import json
from collections import Counter
from random import Random

from destiny.cartography.planet import Planet
from destiny.sociology.government import GOVERNMENTS
from destiny.sociology.pop import Population
from destiny.sociology.constants import POP_TARGET_SIZE
from destiny.sociology.settlement import InhabitedPlanet, Settlement


def generate_earth_pops(
    rng: Random, population_multiplier: float = 10.0 / 8, earth: Planet = None
) -> InhabitedPlanet:
    with open("data/earth_pop.json") as earth_pop_text:
        earth_pop_json = json.load(earth_pop_text)

    planet = InhabitedPlanet(rng, earth)
    print("Loading earth data")
    for country in earth_pop_json:
        print(f"Loading {country['country']}")
        pops = []
        adjusted_population = country["population"] * population_multiplier
        government_types = Counter()
        for _ in range(int(adjusted_population // POP_TARGET_SIZE)):
            population = Population(
                rng,
                POP_TARGET_SIZE,
                [(country["country"], 100)],
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
            government_types[population.preferred_government] += 1
        if len(pops) == 0:
            continue
        settlement = Settlement(
            rng, country["country"], pops, government_types.most_common(1)[0][0]
        )
        planet.settlements.append(settlement)

    return planet
