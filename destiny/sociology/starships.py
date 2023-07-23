import math
from collections import Counter
from random import Random
from typing import Optional, TYPE_CHECKING, List, Tuple, Type
from uuid import UUID, uuid4

from destiny.sociology.constants import SPEED_OF_LIGHT, SECONDS_PER_YEAR, LIGHTYEAR_METRES
from destiny.sociology.science import (
    Technology,
    SuperheavySpacecraft,
    Spacefolding,
    Sublight, ScienceNode,
)
from destiny.sociology.settlement import Settlement
from destiny.sociology.utils.life import process_births_and_deaths
from destiny.sociology.utils.city_names import get_name

if TYPE_CHECKING:
    from destiny.sociology.inhabitedplanet import InhabitedPlanet
    from destiny.cartography.planet import Planet
    from destiny.sociology.pop import Population


class Starship:
    sublight_acceleration: float
    sublight_range: float
    ftl_speed: Optional[float]
    ftl_range: Optional[float]

    capacity: int
    science_level: int
    discoveries: List["ScienceNode"]
    name: str
    founded: int
    lifespan: int
    decommissioned: bool

    origin: Optional["InhabitedPlanet"]
    destination: Optional["Planet"]
    destination_inhabited_planet: Optional["InhabitedPlanet"]
    subjective_time_remaining: Optional[int]
    objective_time_remaining: Optional[int]
    cargo: List["Population"]

    rng: Random
    uuid: UUID

    def __init__(
        self,
        rng: Random,
        name: str,
        capacity: int,
        founded: int,
        lifespan: int,
        sublight_acceleration: float,
        sublight_range: float,
        science_level: int,
        discoveries: List["ScienceNode"],
        ftl_speed: Optional[float] = None,
        ftl_range: Optional[float] = None,
    ):
        self.uuid = uuid4()

        self.sublight_acceleration = sublight_acceleration
        self.sublight_range = sublight_range
        self.ftl_speed = ftl_speed
        self.ftl_range = ftl_range
        self.name = name
        self.capacity = capacity
        self.founded = founded
        self.lifespan = lifespan
        self.decommissioned = False
        self.science_level = science_level
        self.discoveries = discoveries

        self.origin = None
        self.destination = None
        self.destination_inhabited_planet = None
        self.subjective_time_remaining = None
        self.objective_time_remaining = None

        self.rng = rng

    def __eq__(self, other):
        return self.uuid == other.uuid

    @property
    def range(self):
        if self.ftl_range:
            return self.ftl_range
        return self.sublight_range

    def travel_to(
        self,
        current_location: "InhabitedPlanet",
        cargo: Optional[List["Population"]] = None,
        *,
        inhabited: Optional["InhabitedPlanet"] = None,
        planet: Optional["Planet"] = None
    ):
        if cargo is None:
            cargo = []

        self.origin = current_location
        if inhabited:
            self.destination = inhabited.planet
            self.destination_inhabited_planet = inhabited
        else:
            self.destination = planet
            self.destination_inhabited_planet = None
        if len(cargo) > self.capacity:
            raise ValueError("Cannot carry that many people")
        self.cargo = cargo
        self.objective_time_remaining = self.objective_time_between(
            current_location.planet, self.destination
        )
        self.subjective_time_remaining = self.subjective_time_between(
            current_location.planet, self.destination
        )

    def transit(self) -> bool:
        """
        :return: True if the ship has reached its destination
        """
        if self.objective_time_remaining == 0:
            return True

        if self.subjective_time_remaining:
            self.cargo = process_births_and_deaths(self.cargo, self.rng)
            self.subjective_time_remaining -= 1
        self.objective_time_remaining -= 1
        return self.objective_time_remaining == 0

    def objective_time_between(self, start: "Planet", end: "Planet") -> Optional[int]:
        # TODO: can you get close via wormholes?

        distance = start.star.position.distance(end.star.position)
        if self.ftl_range and self.ftl_range >= distance:
            return math.ceil(distance / self.ftl_speed)

        if distance > self.sublight_range:
            return None

        distance *= LIGHTYEAR_METRES

        seconds_to_destination = math.sqrt(
            ((distance / SPEED_OF_LIGHT) ** 2)
            + (4 * distance / self.sublight_acceleration)
        )
        return math.ceil(seconds_to_destination / SECONDS_PER_YEAR)

    def subjective_time_between(self, start: "Planet", end: "Planet") -> Optional[int]:
        # TODO: can you get close via wormholes?

        distance = start.star.position.distance(end.star.position)
        if self.ftl_range and self.ftl_range >= distance:
            return math.ceil(distance / self.ftl_speed)

        if distance > self.sublight_range:
            return None

        distance *= LIGHTYEAR_METRES

        seconds_to_destination = (
            SPEED_OF_LIGHT / self.sublight_acceleration
        ) * math.acosh(
            (self.sublight_acceleration * distance / (SPEED_OF_LIGHT**2) + 1)
        )
        return math.ceil(seconds_to_destination / SECONDS_PER_YEAR)

    @classmethod
    def construct_from_available_technologies(
        cls,
        rng: Random,
        science_level: int,
        discoveries: List[ScienceNode],
        name: str,
        year: int,
    ) -> Tuple["Starship", int]:
        techs = []
        for node in discoveries:
            for tech in node.provides:
                if tech in techs:
                    continue
                techs.append(tech)

        superheavies: List[SuperheavySpacecraft] = [
            t for t in techs if isinstance(t, SuperheavySpacecraft)
        ]
        sublight: List[Sublight] = [t for t in techs if isinstance(t, Sublight)]
        spacefolding: List[Spacefolding] = [
            t for t in techs if isinstance(t, Spacefolding)
        ]

        chassis = max(superheavies, key=lambda t: (t.capacity, -t.cost))
        engine = max(sublight, key=lambda t: (t.acceleration, t.maximum_range))

        if spacefolding:
            ftl = max(spacefolding, key=lambda t: (t.ftl_speed, t.maximum_range))
            ftl_speed = ftl.ftl_speed
            ftl_range = ftl.maximum_range
            ftl_cost_multiplier = 2
        else:
            ftl_speed = None
            ftl_range = None
            ftl_cost_multiplier = 1

        ship = Starship(
            rng,
            name,
            chassis.capacity,
            year,
            rng.randint(25, 100),
            engine.acceleration,
            engine.maximum_range,
            science_level,
            discoveries,
            ftl_speed,
            ftl_range,
        )
        cost = chassis.capacity * chassis.cost * ftl_cost_multiplier

        return ship, cost

    def offload(self, year: int) -> Optional["InhabitedPlanet"]:
        new_planet = None
        if self.destination_inhabited_planet is None and self.destination.inhabited:
            self.destination_inhabited_planet = self.destination.inhabited
        if self.destination_inhabited_planet:
            self.offload_to_settlement()
        else:
            new_planet = self.settle_planet()
        if self.founded + self.lifespan > year:
            self.destination.ships.append(self)
        else:
            print(f"{self.name} has reached the end of its service life")
        self.reset()
        return new_planet

    def settle_planet(self) -> "InhabitedPlanet":
        InhabitedPlanetConstructor: Type[InhabitedPlanet] = type(self.origin)

        countries = Counter()
        for pop in self.cargo:
            for ancestry, amount in pop.ancestry:
                countries[ancestry] += amount

        origin_country = countries.most_common(1)[0][0]
        name = get_name(origin_country, self.rng)

        planet = InhabitedPlanetConstructor(
            self.rng, self.destination, name
        )
        planet.science_level = self.science_level
        planet.discoveries = list(self.discoveries)
        for pop in self.cargo:
            pop.happiness = 1
            pop.reset_wonderlust()
        settlement = Settlement.for_pops(self.rng, self.cargo, name)
        planet.settlements.append(settlement)
        return planet

    def reset(self):
        self.destination = None
        self.destination_inhabited_planet = None
        self.cargo = []

    def offload_to_settlement(self):
        for pop in self.cargo:
            for settlement in self.destination_inhabited_planet.settlements:
                if settlement.government.suitable_for(pop):
                    settlement.pops.append(pop)
                    pop.happiness = 1
                    break
            else:
                pop.happiness = 0.75
                self.rng.choice(self.destination_inhabited_planet.settlements).pops.append(pop)
            pop.reset_wonderlust()
