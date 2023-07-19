from random import Random
from typing import List

from destiny.cartography.mapping import load_stellar_catalogue
from destiny.sociology.starships import Starship
from destiny.sociology.utils.loading import generate_earth_pops


def simulate(years: int = 100):
    rng = Random()
    starmap = load_stellar_catalogue()
    sol = starmap[0]
    inhabited_planets = [generate_earth_pops(rng, earth=sol.planets[2])]
    ships_in_flight: List[Starship] = []

    for n in range(years):
        print(f"Year {n+1}")
        ships_still_in_flight = []
        ships_arrived = []
        for ship in ships_in_flight:
            if ship.transit():
                ships_arrived.append(ship)
            else:
                ships_still_in_flight.append(ship)
        ships_in_flight = ships_still_in_flight

        for ship in ships_arrived:
            maybe_new_planet = ship.offload()
            if maybe_new_planet:
                inhabited_planets.append(maybe_new_planet)

        for planet in inhabited_planets:
            ships_in_flight += planet.process_year(n)
