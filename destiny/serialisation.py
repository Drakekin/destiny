from collections import defaultdict
from typing import List, Tuple, Optional
from uuid import UUID

from pydantic import BaseModel

from destiny.cartography.star import Star as CartographyStar
from destiny.cartography.planet import Planet as CartographyPlanet, LifeLevel
from destiny.sociology.settlement import Settlement as SociologySettlement

class RGB(BaseModel):
    r: float
    g: float
    b: float


class Star(BaseModel):
    spectral_type: str
    spectral_subtype: float
    luminosity: float
    colour: RGB
    mass: float
    radius: float


class NativeLife(BaseModel):
    type: str
    level: int


class Government(BaseModel):
    type: str
    philosophy: str
    support: float


class Country(BaseModel):
    uuid: UUID
    founded: int
    name: str
    population_by_year: List[int]
    ancestries: List[List[str]]
    government: Government

    @classmethod
    def serialise(cls, settlement: SociologySettlement):
        return Country(
            uuid=settlement.uuid,
            founded=settlement.founding_year,
            name=settlement.name,
            population_by_year=settlement.population_by_year,
            ancestries=settlement.ancestries(),
            government=Government(
                type=settlement.government.name,
                philosophy=settlement.government.philosophy,
                support=settlement.government_support(),
            )
        )


class Settlement(BaseModel):
    founded: int
    population_by_year: List[int]
    countries: List[Country]


PLANET_LETTERS = "bcdefghijklmnopqrstuvwxyz"


class Planet(BaseModel):
    uuid: UUID
    mass: float
    name: Optional[str]
    settlement: Optional[Settlement]
    orbital_radius: float
    year_length_hours: float
    day_length_hours: float
    solid: bool
    surface_water: Optional[float]
    moons: int
    greenhouse_factor: int
    surface_temperature: int
    native_life: Optional[NativeLife]

    @classmethod
    def serialise(cls, planet: CartographyPlanet, index: int):
        return Planet(
            uuid=planet.uuid,
            mass=planet.mass,
            name=planet.inhabited.name if planet.inhabited else f"{planet.star.name}-{PLANET_LETTERS[index]}",
            orbital_radius=planet.orbital_radius,
            year_length_hours=planet.orbital_period,
            day_length_hours=planet.day_length_hours,
            solid=planet.solid,
            surface_water=planet.surface_water,
            moons=planet.moons,
            greenhouse_factor=planet.greenhouse_factor,
            surface_temperature=planet.surface_temperature,
            native_life=NativeLife(
                type=planet.native_life.value,
                level=planet.life_level.value,
            ) if planet.life_level != LifeLevel.none else None,
            settlement=Settlement(
                founded=planet.inhabited.founding_year,
                population_by_year=planet.inhabited.population_by_year,
                countries=[Country.serialise(country) for country in planet.inhabited.settlements]
            ) if planet.inhabited else None,
        )


class System(BaseModel):
    name: str
    uuid: UUID
    position: Tuple[float, float, float]
    star: Star
    planets: List[Planet]
    # wormholes: List[UUID]

    @classmethod
    def serialise(cls, star: CartographyStar):
        return System(
            name=star.name,
            uuid=star.uuid,
            position=star.position.to_list(),
            star=Star(
                spectral_type=star.spectral_type,
                spectral_subtype=star.spectral_subtype,
                luminosity=star.luminosity,
                colour=RGB(
                    r=star.colour["r"],
                    g=star.colour["g"],
                    b=star.colour["b"],
                ),
                mass=star.mass,
                radius=star.radius,
            ),
            planets=[Planet.serialise(planet, n) for n, planet in enumerate(star.planets)]
        )


class TradeRoute(BaseModel):
    start: UUID
    end: UUID
    frequency_by_year: List[float]

    @classmethod
    def serialise(cls, transits: List[List[Tuple[CartographyPlanet, CartographyPlanet]]]) -> List["TradeRoute"]:
        routes = []
        by_route = defaultdict(lambda: defaultdict(int))
        transits_per_year = []
        for year, year_transits in enumerate(transits):
            transits_per_year.append(len(year_transits))
            for start, end in year_transits:
                by_route[(start.uuid, end.uuid)][year] += 1

        for route, years in by_route.items():
            start, end = route
            routes.append(TradeRoute(
                start=start,
                end=end,
                frequency_by_year=[years[n]/transits_per_year[n] for n in range(len(transits))]
            ))

        return routes


class Starmap(BaseModel):
    systems: List[System]
    trade_routes: List[TradeRoute]

    @classmethod
    def serialise(cls, starmap: List[CartographyStar], transits: List[List[Tuple[CartographyPlanet, CartographyPlanet]]]):
        return Starmap(
            systems=[System.serialise(star) for star in starmap],
            trade_routes=TradeRoute.serialise(transits)
        )

