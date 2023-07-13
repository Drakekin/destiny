import math
from enum import Enum, auto
from random import Random
from typing import Optional, List, TYPE_CHECKING

from destiny.maths import Vec3
if TYPE_CHECKING:
    from destiny.cartography.star import Star


class LifeType(Enum):
    human_compatible = "human compatible"
    human_neutral = "neutral"
    human_hostile = "human hostile"
    exotic = "exotic"


class LifeLevel(Enum):
    none = 0
    precursor = 1
    unicellular = 2
    photosynthesis = 3
    eukaryote = 4
    multicellular = 5
    plants = 6
    molluscs = 7
    land_animals = 8
    complex_life = 9
    intelligent_life = 10


LIFE_LEVEL_NAMES = [
    "none",
    "life precursor",
    "unicellular life",
    "photosynthetic life",
    "eukaryotic life",
    "multicellular life",
    "plants",
    "molluscs",
    "land animals",
    "complex life",
    "intelligent life",
]


class Planet:
    star: "Star"
    mass: float
    day_length_hours: float
    orbital_radius: float
    solid: bool
    surface_water: Optional[float]
    greenhouse_factor: int
    moons: int
    position: Vec3
    native_life: Optional[LifeType]
    life_level: LifeLevel

    def __init__(self, star: "Star", mass: float, day_length: float, orbital_radius: float, solid: bool,
                 surface_water: Optional[float] = None, greenhouse_factor: int = 0, moons: int = 0):
        self.star = star
        self.mass = mass
        self.day_length_hours = day_length
        self.orbital_radius = orbital_radius
        self.solid = solid
        self.surface_water = surface_water
        self.greenhouse_factor = greenhouse_factor if not solid else 0
        self.moons = moons
        self.native_life = None
        self.life_level = LifeLevel.none

    def generate_life(self, rng: Random):
        options: List[Optional[LifeType]] = []
        if self.surface_temperature > 100:
            options = [None] * 39 + [LifeType.exotic]
        elif self.surface_temperature < -10:
            options = [None] * 35 + [LifeType.exotic] * 3 + [LifeType.human_neutral, LifeType.human_hostile]
        elif not self.solid:
            options = [None] * 10 + [LifeType.exotic] * 5 + [LifeType.human_neutral] * 2 + [LifeType.human_hostile]
        elif not self.habitable:
            options = [None] * 5 + [LifeType.human_hostile] * 7 + [LifeType.human_neutral] * 2 + [LifeType.human_compatible, LifeType.exotic]
        elif self.habitable:
            options = [None] * 5 + [LifeType.human_hostile, LifeType.human_neutral] * 5 + [LifeType.human_compatible] * 4 + [LifeType.exotic]

        self.native_life = rng.choice(options)
        if self.native_life:
            chance = rng.random()
            raw_level = round((chance ** (10 if chance <= 0.9 else 30)) * 9 + 1)
            self.life_level = LifeLevel(raw_level)

    @property
    def habitable(self):
        if not self.solid:
            return False
        days_per_year = self.orbital_period / self.day_length_hours
        return days_per_year > 100 and 0.75 < self.gravity < 1.25 and 0 <= self.surface_temperature <= 25

    @property
    def radius(self):
        kg_mass = self.mass * 5.972 * (10 ** 24)
        volume = kg_mass / 5515
        return math.pow((3 * volume)/(4 * math.pi), 1/3)

    @property
    def gravity(self):
        kg_mass = self.mass * 5.972 * (10 ** 24)
        gravitational_constant = (6.6743 * (10 ** -11))
        return (kg_mass * gravitational_constant) / (self.radius ** 2) / 9.81

    @property
    def orbital_period(self):
        orbit_metres = self.orbital_radius * (149 * (10 ** 9))
        star_mass_kg = self.star.mass * (1.989 * (10 ** 30))
        gravitational_constant = (6.6743 * (10 ** -11))
        period_seconds = 2 * math.pi * math.sqrt((orbit_metres ** 3) / (gravitational_constant * star_mass_kg))
        return period_seconds / (60 * 60)

    @property
    def unmodified_surface_temp(self):
        bond_albedo = 0.3
        boltzman_constant = (5.670373 * (10 ** -8))
        orbit_metres = self.orbital_radius * (149 * (10 ** 9))
        denominator = 16 * math.pi * boltzman_constant * (orbit_metres ** 2)
        luminosity_watts = (3.846 * (10 ** 26))
        received_power = self.star.luminosity * luminosity_watts * (1 - bond_albedo)
        temperature_fourth = received_power / denominator
        temperature = math.pow(temperature_fourth, 1/4)
        return int(temperature - 273)  # kelvin - 273 = celsius

    @property
    def surface_temperature(self):
        return self.unmodified_surface_temp + self.greenhouse_factor

    def __repr__(self):
        type_ = "Rocky planet" if self.solid else "Gas giant"
        mass = f"{round(self.mass, 2)}M⊕"
        day = f"{round(self.day_length_hours, 1)} hours"
        days_per_year = self.orbital_period / self.day_length_hours
        year = f"{round(days_per_year, 1)} local days"
        standard_year = f"{round(self.orbital_period / 24, 1)} standard days"
        if self.solid:
            effective_temp = self.unmodified_surface_temp + self.greenhouse_factor
            life_str = f"{self.native_life.value} {LIFE_LEVEL_NAMES[self.life_level.value]}, " if self.native_life else "probably "
            habitable_str = f"{life_str}habitable" if self.habitable else f"{life_str}uninhabitable"
            extras = f"gravity: {round(self.gravity, 2)}g, mean surface temperature: {int(round(effective_temp))}°C, rotational period: {day}, year: {year}/{standard_year}, {habitable_str}"
        else:
            life_str = f", {self.native_life.value} {LIFE_LEVEL_NAMES[self.life_level.value]}" if self.native_life else ""
            extras = f"rotational period: {day}, year: {year}/{standard_year}, mean surface temperature: {round(self.unmodified_surface_temp)}°C{life_str}"

        return f"<Planet [{type_}, {round(self.orbital_radius, 2)}au, {mass}, {self.moons} moon{'' if self.moons == 1 else 's'}, {extras}]>"
