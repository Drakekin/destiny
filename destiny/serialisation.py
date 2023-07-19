from typing import List, Tuple, Optional
from uuid import UUID

from pydantic import BaseModel


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


class City(BaseModel):
    uuid: UUID
    founded: int
    population_by_year: List[int]
    ancestries: List[List[str]]
    government: Government


class Settlement(BaseModel):
    founded: int
    population_by_year: List[int]
    cities: List[City]


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


class System(BaseModel):
    name: str
    uuid: UUID
    position: Tuple[float]
    star: Star
    planets: List[Planet]
    wormholes: List[UUID]


class Starmap(BaseModel):
    systems: List[System]
