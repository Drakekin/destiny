from collections import defaultdict, Counter
from random import Random
from typing import List, Optional, Tuple, TYPE_CHECKING
from uuid import uuid4, UUID

from destiny.cartography.planet import Planet
from destiny.sociology.science import ScienceNode, TECH_TREE
from destiny.sociology.settlement import Settlement
from destiny.sociology.starships import Starship
from destiny.sociology.utils.shipnames import SHIP_NAMES

if TYPE_CHECKING:
    from destiny.sociology.pop import Population


class InhabitedPlanet:
    settlements: List[Settlement]
    rng: Random
    science_level: int
    science_surplus: int
    manufacturing_base: int
    manufacturing_surplus: int
    planet: Planet
    name: str
    discoveries: List[ScienceNode]

    is_earth: bool

    uuid: UUID

    def __init__(self, rng: Random, planet: Planet, name: str):
        self.settlements = []
        self.rng = rng
        self.planet = planet
        self.planet.inhabited = self
        self.name = name

        self.uuid = uuid4()

        self.science_level = 0
        self.manufacturing_base = 1

        self.discoveries = [TECH_TREE]

        self.science_surplus = 0
        self.manufacturing_surplus = 0
        self.is_earth = False

    def __eq__(self, other):
        return self.uuid == other.uuid

    def __hash__(self):
        return self.uuid.__hash__()

    def science_upgrade(self):
        surplus_needed = (self.science_level * 10) ** 3
        if self.science_surplus >= surplus_needed:
            self.science_surplus -= surplus_needed
            self.science_level += 1

            options = []
            for discovery in self.discoveries:
                for option in discovery.options:
                    if option not in self.discoveries and option not in options:
                        options.append(option)

            choice = self.rng.choice(options)
            self.discoveries.append(choice)
            print(
                f"{self.name} has upgraded to science level {self.science_level} and unlocked {choice}"
            )

    def build_ships(self, year: int, capacity_needed: int):
        capacity_purchased = 0
        while capacity_purchased < capacity_needed:
            ship_name = self.rng.choice(SHIP_NAMES)
            ship_template, cost = Starship.construct_from_available_technologies(
                self.rng, self.science_level, self.discoveries, ship_name, year
            )
            if self.manufacturing_surplus < cost:
                return

            capacity_purchased += ship_template.capacity
            self.manufacturing_surplus -= cost
            self.planet.ships.append(ship_template)
            SHIP_NAMES.remove(ship_name)
            original, *numbers = ship_name.split("—")
            if numbers:
                (number_str,) = numbers
                number = int(number_str) + 1
            else:
                number = 2
            SHIP_NAMES.append(f"{original}—{number}")

    @property
    def population(self):
        return sum([s.population for s in self.settlements])

    def process_year(self, year: int) -> List[Starship]:
        print(f"Processing year {year} for {self.name}")

        unhappy_pops = []
        settlements_by_government = defaultdict(list)
        for settlement in self.settlements:
            (
                new_unhappy_pops,
                manufacturing_output,
                science_output,
            ) = settlement.process_year(year)
            unhappy_pops += new_unhappy_pops
            self.science_surplus += science_output
            self.science_upgrade()

            self.manufacturing_surplus += self.manufacturing_base * manufacturing_output

            settlements_by_government[settlement.government.opinion_hash].append(
                settlement
            )

        print(f"{len(unhappy_pops)} pops want to move")
        moved = 0
        emigrated = 0
        stayed = 0
        colonists: List[Tuple[Settlement, "Population"]] = []
        settlers: List[Tuple[Settlement, "Population"]] = []
        offworld_settlers: List[Tuple[Settlement, "Population"]] = []

        for original_settlement, pop in unhappy_pops:
            if pop.settler_colonial < 0.5:
                colonists.append((original_settlement, pop))
            else:
                settlers.append((original_settlement, pop))

        for original_settlement, pop in settlers:
            opinion = pop.opinion_hash
            for candidate in settlements_by_government[opinion]:
                if candidate.government.suitable_for(pop):
                    candidate.pops.append(pop)
                    moved += 1
                    break
            else:
                offworld_settlers.append((original_settlement, pop))

        total_capacity_available = sum([ship.capacity for ship in self.planet.ships])
        if total_capacity_available < (len(offworld_settlers) + len(colonists)):
            self.build_ships(
                year, len(offworld_settlers) + len(colonists) - total_capacity_available
            )

        random_ships = sorted(self.planet.ships, key=lambda _: self.rng.random())

        leaving_ships = []

        if random_ships and colonists:
            max_range = max(ship.range for ship in random_ships)
            possible_destination_stars = []
            for star, distance in self.planet.star.precomputed_neighbours:
                if distance <= max_range:
                    possible_destination_stars.append((distance, star))
                else:
                    break

            colonisable_planets = []
            for distance, star in possible_destination_stars:
                for planet in star.habitable_planets:
                    if planet.inhabited is None:
                        colonisable_planets.append((distance, planet))

            if colonisable_planets:
                colonisable_planets = sorted(
                    colonisable_planets, key=lambda t: t[0], reverse=True
                )
                while colonists and random_ships and colonisable_planets:
                    distance, target_planet = colonisable_planets.pop()
                    ship: Optional[Starship] = None
                    if all(ship.range < distance for ship in random_ships):
                        continue
                    while ship is None or ship.range < distance:
                        ship = self.rng.choice(random_ships)
                    random_ships.remove(ship)
                    original_settlement, exemplar_colonist = self.rng.choice(colonists)
                    colonists.remove((original_settlement, exemplar_colonist))
                    cargo = [exemplar_colonist]
                    colonists = sorted(
                        colonists,
                        key=lambda c: c[1].similarity_to(exemplar_colonist),
                        reverse=True,
                    )
                    while colonists and len(cargo) < ship.capacity:
                        _, new_colonist = colonists.pop()
                        cargo.append(new_colonist)
                        emigrated += 1
                    leaving_ships.append(ship)
                    ship.travel_to(self, cargo, planet=target_planet)
                    print(
                        f"The {ship.name} is heading to {target_planet.star.name} with {len(cargo)} colonists on a journey taking {ship.objective_time_remaining} years"
                    )

                if colonists:
                    offworld_settlers += colonists

        if random_ships and offworld_settlers:
            new_max_range = max(ship.range for ship in random_ships)

            settleable_planets = []
            settlers_for_planet = defaultdict(list)
            planet_for_settlers = defaultdict(list)
            for star, distance in self.planet.star.precomputed_neighbours:
                if distance > new_max_range:
                    break
                for planet in star.habitable_planets:
                    if planet.inhabited:
                        chosen = False
                        for original_settlement, settler in offworld_settlers:
                            if any(
                                settlement.government.suitable_for(settler)
                                for settlement in planet.inhabited.settlements
                            ):
                                settlers_for_planet[planet.inhabited].append(
                                    (original_settlement, settler)
                                )
                                planet_for_settlers[
                                    (original_settlement, settler)
                                ].append(planet.inhabited)
                                chosen = True
                        if chosen:
                            settleable_planets.append((distance, planet.inhabited))

            while offworld_settlers and random_ships and settleable_planets:
                settleable_planets = sorted(
                    settleable_planets, key=lambda t: len(settlers_for_planet[t[1]])
                )
                distance, target_inhabited_planet = settleable_planets.pop()
                settlers = settlers_for_planet[target_inhabited_planet]

                ship: Optional[Starship] = None
                if all(ship.range < distance for ship in random_ships):
                    break
                while ship is None or ship.range < distance:
                    ship = self.rng.choice(random_ships)
                random_ships.remove(ship)

                cargo = []
                while settlers and len(cargo) < ship.capacity:
                    settlement_settler = settlers.pop()
                    original_settlement, settler = settlement_settler
                    offworld_settlers.remove(settlement_settler)
                    for candidate in planet_for_settlers[settlement_settler]:
                        if candidate == target_inhabited_planet:
                            continue
                        settlers_for_planet[candidate].remove(settlement_settler)
                    cargo.append(settler)
                    emigrated += 1

                leaving_ships.append(ship)
                ship.travel_to(self, cargo, inhabited=target_inhabited_planet)
                print(
                    f"The {ship.name} is heading to {target_inhabited_planet.name} with {len(cargo)} colonists on a journey taking {ship.objective_time_remaining} years"
                )

                if settlers_for_planet[target_inhabited_planet]:
                    settleable_planets.append((distance, target_inhabited_planet))

            if self.is_earth:
                for original_settlement, pop in offworld_settlers:
                    original_settlement.pops.append(pop)
                    stayed += 1
            else:
                # TODO: form multiple settlements if the number of remaining pops is big
                self.settlements.append(
                    Settlement.for_pops(self.rng, [pop for _, pop in offworld_settlers], "City McCityface"))

        self.planet.ships = random_ships

        print(
            f"Moved {moved}, emigrated {emigrated}, stayed {stayed} of {len(unhappy_pops)}"
        )

        return leaving_ships
