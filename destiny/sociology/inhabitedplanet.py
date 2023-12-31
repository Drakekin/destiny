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
    founding_year: int
    planet: Planet
    name: str
    discoveries: List[ScienceNode]

    is_earth: bool
    population_by_year: List[int]

    uuid: UUID

    def __init__(self, rng: Random, planet: Planet, name: str, founding_year: int):
        self.settlements = []
        self.rng = rng
        self.planet = planet
        self.planet.inhabited = self
        self.name = name
        self.founding_year = founding_year

        self.uuid = uuid4()

        self.science_level = 0
        self.manufacturing_base = 1

        self.discoveries = [TECH_TREE]

        self.science_surplus = 0
        self.manufacturing_surplus = 0
        self.is_earth = False
        self.population_by_year = []

    def __eq__(self, other):
        return self.uuid == other.uuid

    def __hash__(self):
        return self.uuid.__hash__()

    def science_upgrade(self):
        # TODO: Fix science so Earth doesn't massively race ahead and so that FTL isn't invented on year two
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
        planet_year = year - self.founding_year
        if planet_year == year:
            print(f"Processing year {year+1} for {self.name}")
        else:
            print(f"Processing year {year+1} (MY {planet_year+1}) for {self.name}")
        print(f"Population: {self.population:,} in {sum(len(s.pops) for s in self.settlements)} pops across {len(self.settlements)} states")

        population_birth_rate_modifier = 1/max(self.population / 7_000_000_000, 1)

        unhappy_pops = []
        settlements_by_government = defaultdict(list)
        for settlement in self.settlements:
            (
                new_unhappy_pops,
                manufacturing_output,
                science_output,
                average_happiness
            ) = settlement.process_year(year, population_birth_rate_modifier, self.is_earth)
            unhappy_pops += new_unhappy_pops
            self.science_surplus += science_output * average_happiness
            self.science_upgrade()

            self.manufacturing_surplus += self.manufacturing_base * manufacturing_output

            settlements_by_government[settlement.government.opinion_hash].append(
                settlement
            )

        self.population_by_year.append(self.population)

        print(f"{len(unhappy_pops)} pops want to move")
        leaving_ships, remaining_ships = self.migrate_pops(unhappy_pops, settlements_by_government, year)

        self.planet.ships = []
        for ship in remaining_ships:
            candidates = []
            candidate_weightings = []
            for star, distance in self.planet.star.precomputed_neighbours:
                if distance > ship.range:
                    break
                for planet in star.habitable_planets:
                    if planet.inhabited:
                        candidates.append(planet.inhabited)
                        candidate_weightings.append(planet.inhabited.population / distance)
            if not candidates:
                self.planet.ships.append(ship)
                continue
            destination, = self.rng.choices(candidates, weights=candidate_weightings)
            ship.travel_to(self, inhabited=destination)

        return leaving_ships

    def migrate_pops(self, unhappy_pops, settlements_by_government, year):
        pops_to_move = len(unhappy_pops)
        moved = 0
        emigrated = 0
        stayed = 0
        colonists: List[Tuple[Settlement, "Population"]] = []
        settlers: List[Tuple[Settlement, "Population"]] = []
        offworld_settlers: List[Tuple[Settlement, "Population"]] = []

        while unhappy_pops:
            original_settlement, pop = unhappy_pops.pop()
            if pop.settler_colonial < 0.5:
                colonists.append((original_settlement, pop))
            else:
                settlers.append((original_settlement, pop))

        while settlers:
            original_settlement, pop = settlers.pop()
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
                # TODO: Pick colonisation targets better
                colonisable_planets = sorted(
                    colonisable_planets, key=lambda t: t[0]
                )
                while colonists and random_ships and colonisable_planets:
                    max_ship_range = max(ship.range for ship in random_ships)
                    colonisable_planets = list(filter(lambda p: p[0] <= max_ship_range, colonisable_planets))
                    if not colonisable_planets:
                        break
                    planet_weighting = [(1 / d) ** 5 for d, _ in colonisable_planets]
                    choice, = self.rng.choices(colonisable_planets, weights=planet_weighting)
                    distance, target_planet = choice

                    ship: Optional[Starship] = None
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
                    filter(lambda t: len(settlers_for_planet[t[1]]) > 0, settleable_planets),
                    key=lambda t: len(settlers_for_planet[t[1]])
                )
                candidate_planets = settleable_planets[-3:]
                if not candidate_planets:
                    break
                chosen_planet = self.rng.choice(candidate_planets)
                candidate_planets.remove(chosen_planet)

                distance, target_inhabited_planet = chosen_planet
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

                if len(settlers_for_planet[target_inhabited_planet]) > 0:
                    settleable_planets.append((distance, target_inhabited_planet))

        if offworld_settlers:
            if self.is_earth:
                for original_settlement, pop in offworld_settlers:
                    original_settlement.pops.append(pop)
                    stayed += 1
            else:
                stayed += len(offworld_settlers)
                returners = []
                if len(offworld_settlers) > 10:
                    instigators = [(settlement, pop) for settlement, pop in offworld_settlers if
                                   pop.political_engagement > 0.95]
                    possible_new_settlements = defaultdict(list)
                    for settlement, pop in offworld_settlers:
                        if (settlement, pop) in instigators:
                            continue
                        for _, instigator in instigators:
                            if pop.similarity_to(instigator) < pop.tolerance:
                                possible_new_settlements[instigator].append(pop)
                                break
                        else:
                            returners.append((settlement, pop))
                    if possible_new_settlements:
                        successful_instigator = max(possible_new_settlements.keys(),
                                                    key=lambda s: len(possible_new_settlements[s]))
                        new_population = possible_new_settlements[successful_instigator]
                        new_population.append(successful_instigator)
                        for settlement, failed_instigator in instigators:
                            if failed_instigator == successful_instigator:
                                continue
                            returners.append((settlement, failed_instigator))

                        new_settlement = Settlement.for_pops(self.rng, new_population, founding_year=year)
                        print(
                            f"{len(new_population)} pops have formed a new state of {new_settlement.name} on {self.name}")
                        self.settlements.append(new_settlement)
                    else:
                        returners = offworld_settlers
                else:
                    returners = offworld_settlers

                for settlement, pop in returners:
                    settlement.pops.append(pop)

        print(
            f"Moved {moved}, emigrated {emigrated}, stayed {stayed} of {pops_to_move}"
        )

        return leaving_ships, random_ships
