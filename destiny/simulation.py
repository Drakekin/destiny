from random import Random

from destiny.cartography.mapping import load_stellar_catalogue
from destiny.sociology.utils import generate_earth_pops


def simulate(years: int = 100):
    rng = Random()
    starmap = load_stellar_catalogue()
    sol = starmap[0]
    inhabited_planets = [generate_earth_pops(rng, earth=sol.planets[2])]

    for n in range(years):
        print(f"Year {n+1}")
        for planet in inhabited_planets:
            planet.process_year(n)
