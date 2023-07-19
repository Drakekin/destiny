from random import Random

from destiny.cartography.planet import Planet
from destiny.sociology.constants import POP_TARGET_SIZE
from destiny.sociology.inhabitedplanet import InhabitedPlanet
from destiny.sociology.pop import Population
from destiny.sociology.settlement import Settlement


def generate_earth_pops(
    rng: Random, population_multiplier: float = 10.0 / 8, earth: Planet = None
) -> InhabitedPlanet:
    earth_pop_countries = []
    with open("data/worldpop.csv", encoding='utf-8-sig') as earth_pop_text:
        for line in earth_pop_text:
            country, pop_str = line.split(",")
            earth_pop_countries.append((country, int(pop_str)))

    planet = InhabitedPlanet(rng, earth, "Earth")
    print("Loading earth data")
    for country, population in earth_pop_countries:
        print(f"Loading {country}")
        pops = []
        adjusted_population = population * population_multiplier
        for _ in range(int(adjusted_population // POP_TARGET_SIZE)):
            population = Population(
                rng,
                POP_TARGET_SIZE,
                [(country, 100)],
                randomise_statistics=True,
            )
            population.children = [
                rng.randint(
                    int(50 / 10_000 * POP_TARGET_SIZE),
                    int(300 / 10_000 * POP_TARGET_SIZE),
                )
                for _ in range(20)
            ]
            pops.append(population)
        if len(pops) == 0:
            continue
        settlement = Settlement.for_pops(rng, pops, country)
        planet.settlements.append(settlement)

    planet.is_earth = True
    return planet
