import math
from random import Random
from typing import List

from destiny.cartography.planet import Planet
from destiny.maths import Vec3


class Star:
    name: str
    spectral_type: str
    spectral_subtype: float
    colour: dict
    luminosity: float
    position: Vec3
    planets: List[Planet]

    def __init__(
        self,
        name: str,
        position: Vec3,
        spectral_type: str,
        spectral_subtype_str: str,
        colour: dict,
        luminosity: float,
    ):
        rng = Random(name)

        self.position = position
        self.name = name
        self.spectral_type = spectral_type
        self.spectral_subtype = float(spectral_subtype_str)
        self.colour = colour
        self.luminosity = luminosity

        self.planets = []
        self._generate_planets(rng)

    def surface_temperature(self, orbital_radius: float, bond_albedo: float = 0.3):
        boltzman_constant = 5.670373 * (10**-8)
        orbit_metres = (orbital_radius * (149 * (10**9))) ** 2
        denominator = 16 * math.pi * boltzman_constant * orbit_metres
        luminosity_watts = 3.846 * (10**26)
        received_power = self.luminosity * luminosity_watts * (1 - bond_albedo)
        temperature_fourth = received_power / denominator
        temperature = math.pow(temperature_fourth, 1 / 4)
        return int(temperature - 273)  # kelvin - 273 = celsius

    def _generate_planets(self, rng: Random):
        num_planets = rng.randint(3, 10)
        hot_jupiter = rng.randint(0, 1)
        rocky = num_planets // 2
        gaseous = num_planets - rocky - hot_jupiter
        guaranteed_habitability_chance = 0.05 if self.spectral_type == "G" else 0.5
        guaranteed_habitable = 1 if rng.random() > guaranteed_habitability_chance else 0
        uninhabitable = rocky - guaranteed_habitable

        if hot_jupiter:
            radius = (
                self.inner_habitable_zone / 3 * rng.random()
                + self.inner_habitable_zone / 10
            )
            self.planets.append(
                self.generate_random_gas_giant(radius, rng, moons=False)
            )
            if uninhabitable:
                uncertainty = self.inner_habitable_zone / 3
                radius = uncertainty * rng.random() + radius
                self.planets.append(
                    self.generate_random_uninhabitable_planet(radius, rng)
                )
                uninhabitable -= 1

            habitable_radius = (
                self.inner_habitable_zone
                + (self.outer_habitable_zone - self.inner_habitable_zone) * rng.random()
            )
            self.planets.append(
                self.generate_random_possibly_habitable_planet(habitable_radius, rng)
            )

            if uninhabitable:
                last_radius = (
                    self.outer_habitable_zone
                    + (self.frost_line - self.outer_habitable_zone) * rng.random()
                )
                self.planets.append(
                    self.generate_random_uninhabitable_planet(last_radius, rng)
                )
        elif guaranteed_habitable:
            if uninhabitable:
                uncertainty = self.inner_habitable_zone / 3
                radius = uncertainty * 2 * rng.random() + uncertainty
                self.planets.append(
                    self.generate_random_uninhabitable_planet(radius, rng)
                )
                uninhabitable -= 1

            habitable_radius = (
                self.inner_habitable_zone
                + (self.outer_habitable_zone - self.inner_habitable_zone) * rng.random()
            )
            self.planets.append(
                self.generate_random_possibly_habitable_planet(habitable_radius, rng)
            )

            if uninhabitable:
                last_radius = (
                    self.outer_habitable_zone
                    + (self.frost_line - self.outer_habitable_zone) * rng.random()
                )
                self.planets.append(
                    self.generate_random_uninhabitable_planet(last_radius, rng)
                )
        else:
            min_distance = self.inner_habitable_zone / 3
            max_distance = self.frost_line / 3
            radius = self.inner_habitable_zone / 3
            for _ in range(uninhabitable):
                radius += rng.uniform(min_distance, max_distance)
                self.planets.append(
                    self.generate_random_uninhabitable_planet(radius, rng)
                )

        radius = self.frost_line
        for _ in range(gaseous):
            radius += rng.uniform(3, 10)
            self.planets.append(self.generate_random_gas_giant(radius, rng))

        for planet in self.planets:
            planet.generate_life(rng)

    def generate_random_gas_giant(
        self, radius: float, rng: Random, moons: bool = True
    ) -> Planet:
        planet = Planet(
            star=self,
            mass=rng.uniform(14, 400),
            day_length=rng.uniform(0.25, 50) * 24,
            orbital_radius=radius,
            solid=False,
            moons=rng.randint(0, 30) if moons else 0,
        )
        lock_chance = 0.5 if radius < (0.5 * math.sqrt(self.mass)) else 0.99
        psuedo_locked = rng.random() > lock_chance
        if psuedo_locked:
            planet.day_length_hours = planet.orbital_period * rng.uniform(0.3, 1.1)
        return planet

    def generate_random_uninhabitable_planet(self, radius, rng) -> Planet:
        planet = Planet(
            star=self,
            mass=rng.uniform(0.03, 1.5),
            day_length=rng.uniform(0.3, 10) * 24,
            orbital_radius=radius,
            solid=True,
            greenhouse_factor=rng.randint(0, 100),
            surface_water=rng.random(),
            moons=rng.randint(0, 3),
        )
        lock_chance = 0.5 if radius < (0.5 * math.sqrt(self.mass)) else 0.95
        psuedo_locked = rng.random() > lock_chance
        if psuedo_locked:
            planet.day_length_hours = planet.orbital_period * rng.uniform(0.3, 1.1)
        return planet

    def generate_random_possibly_habitable_planet(
        self, radius: float, rng: Random
    ) -> Planet:
        initial_surface_temperature = self.surface_temperature(radius)
        max_greenhouse_fudge_factor = int(max(24 - initial_surface_temperature, 0))
        min_greenhouse_fudge_factor = int(max(0 - initial_surface_temperature, 0))
        return Planet(
            star=self,
            mass=rng.uniform(0.95, 1.05),
            day_length=rng.uniform(0.75, 2) * 24,
            orbital_radius=radius,
            solid=True,
            greenhouse_factor=rng.randint(
                min_greenhouse_fudge_factor, max_greenhouse_fudge_factor
            ),
            surface_water=rng.uniform(0.5, 0.8),
            moons=1,
        )

    @property
    def mass(self):
        masses = {
            "O": (16, 120),
            "B": (2.1, 16),
            "A": (1.4, 2.1),
            "F": (1.04, 1.4),
            "G": (0.8, 1.04),
            "K": (0.45, 0.8),
            "M": (0.08, 0.45),
        }

        letter, number = self.spectral_type, self.spectral_subtype
        min_t, max_t = masses[letter]
        mod = number / 9
        return min_t + (max_t - min_t) * mod

    @property
    def radius(self):
        radius = {
            "O": (6.6, 50),
            "B": (1.8, 6.6),
            "A": (1.4, 1.8),
            "F": (1.15, 1.4),
            "G": (0.96, 1.15),
            "K": (0.7, 0.96),
            "M": (0.1, 0.7),
        }

        letter, number = self.spectral_type, self.spectral_subtype
        min_t, max_t = radius[letter]
        mod = number / 9
        return min_t + (max_t - min_t) * mod

    @property
    def inner_habitable_zone(self):
        return math.sqrt(self.luminosity * 0.9025)

    @property
    def outer_habitable_zone(self):
        return math.sqrt(self.luminosity * 6.25)

    @property
    def frost_line(self):
        return math.sqrt(self.luminosity * 16)

    @property
    def habitable(self):
        return any(p.habitable for p in self.planets)

    def __repr__(self):
        return f"<Star({self.name}, {self.spectral_type}{int(self.spectral_subtype)}) [{len(self.planets)} planet{'' if len(self.planets) == 0 else 's'}{', habitable' if self.habitable else ''}]>"
