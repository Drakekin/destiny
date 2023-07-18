import math
from random import Random
from typing import Optional, TYPE_CHECKING, List, Tuple
from uuid import UUID, uuid4

from destiny.sociology.constants import SPEED_OF_LIGHT, SECONDS_PER_YEAR
from destiny.sociology.science import (
    Technology,
    SuperheavySpacecraft,
    Spacefolding,
    Sublight,
)
from destiny.sociology.utils.life import process_births_and_deaths
from destiny.sociology.utils.shipnames import SHIP_NAMES

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
    technologies: List["Technology"]
    name: str
    founded: int
    lifespan: int
    decommissioned: bool

    destination: Optional["Planet"]
    destination_settlement: Optional["InhabitedPlanet"]
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
        technologies: List["Technology"],
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
        self.technologies = technologies

        self.destination = None
        self.destination_settlement = None
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
        cargo: List["Population"],
        *,
        inhabited: Optional["InhabitedPlanet"] = None,
        planet: Optional["Planet"] = None
    ):
        if inhabited:
            self.destination = inhabited.planet
            self.destination_settlement = inhabited
        else:
            self.destination = planet
            self.destination_settlement = None
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
            return round(distance / self.ftl_speed)

        if distance > self.sublight_range:
            return None

        seconds_to_destination = math.sqrt(
            ((distance / SPEED_OF_LIGHT) ** 2)
            + (4 * distance / self.sublight_acceleration)
        )
        return round(seconds_to_destination / SECONDS_PER_YEAR)

    def subjective_time_between(self, start: "Planet", end: "Planet") -> Optional[int]:
        # TODO: can you get close via wormholes?

        distance = start.star.position.distance(end.star.position)
        if self.ftl_range and self.ftl_range >= distance:
            return round(distance / self.ftl_speed)

        if distance > self.sublight_range:
            return None

        seconds_to_destination = (
            SPEED_OF_LIGHT / self.sublight_acceleration
        ) * math.acosh(
            (self.sublight_acceleration * distance / (SPEED_OF_LIGHT**2) + 1)
        )
        return round(seconds_to_destination / SECONDS_PER_YEAR)

    @classmethod
    def construct_from_available_technologies(
        cls,
        rng: Random,
        science_level: int,
        techs: List[Technology],
        name: str,
        year: int,
    ) -> Tuple["Starship", int]:
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
            techs,
            ftl_speed,
            ftl_range,
        )
        cost = chassis.capacity * chassis.cost * ftl_cost_multiplier

        return ship, cost
