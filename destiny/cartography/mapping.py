import json
from typing import List, Dict, Tuple, Iterable

from destiny.cartography.planet import Planet, LifeLevel
from destiny.cartography.star import Star
from destiny.maths import Vec3

import numpy as np
from scipy.spatial import Delaunay


def generate_sol():
    sol = Star("Sol", Vec3(0, 0, 0), "G", "2", {"r": 1, "g": 1, "b": 1}, 1)
    sol.planets = [
        Planet(sol, 0.055, 88 * 24, 0.4, True),
        Planet(sol, 0.815, 243 * 24, 0.72, True),
        Planet(sol, 1, 24, 1, True, greenhouse_factor=32),
        Planet(sol, 0.107, 24.5, 1.45, True),
        Planet(sol, 317, 10, 5.2, False),
        Planet(sol, 95, 10.5, 9.5, False),
        Planet(sol, 14.5, 17.4, 19.1, False),
        Planet(sol, 17, 16, 30, False),
    ]
    return sol


def load_stellar_catalogue() -> List[Star]:
    stars = [generate_sol()]

    with open("data/bsc5p_3d.json") as catalogue_3d_file:
        catalogue_3d = json.load(catalogue_3d_file)
    with open("data/bsc5p_names.json") as catalogue_name_file:
        catalogue_name_unsorted = json.load(catalogue_name_file)
    with open("data/bsc5p_spectral_extra.json") as catalogue_spectral_file:
        catalogue_spectral_unsorted = json.load(catalogue_spectral_file)

    catalogue_name = {d["i"]: d for d in catalogue_name_unsorted}
    catalogue_spectral = {d["i"]: d for d in catalogue_spectral_unsorted}

    print("Loading stellar data")
    for data in catalogue_3d:
        star_id = data["i"]
        pos = Vec3(data["x"], data["y"], data["z"])
        colour = data.get("K", {"r": 1, "g": 1, "b": 1})

        maybe_names = [
            n[5:] for n in catalogue_name[star_id]["n"] if n.startswith("NAME ")
        ]
        if maybe_names:
            name = min(maybe_names, key=lambda n: len(n))
        else:
            name = data["n"]
        luminosity = data["N"]
        spectral_data = catalogue_spectral[star_id]

        spectral_class = spectral_data["C"]
        if "/" in spectral_class:
            spectral_class = spectral_class.split("/")[-1]

        if spectral_class not in ("O", "B", "A", "F", "G", "K", "M"):
            continue

        spectral_subclass = spectral_data.get("S")
        if not spectral_subclass:
            spectral_subclass = "5"
        if "/" in spectral_subclass:
            spectral_subclass = spectral_subclass.split("/")[0]
        if "-" in spectral_subclass:
            spectral_subclass = spectral_subclass.split("-")[0]

        try:
            subclass = float(spectral_subclass)
        except ValueError:
            continue

        star = Star(name, pos, spectral_class, spectral_subclass, colour, luminosity)
        stars.append(star)

    habitable_stars = [s for s in stars if s.habitable]

    print(f"Calculating neighbours for {len(habitable_stars)} habitable stars")
    points_for_scipy = np.array([s.position.to_list() for s in habitable_stars])
    tris = Delaunay(points_for_scipy, qhull_options="Qbb Qc Qz Q12 QJ")

    star_distance_cache = {}

    print(f"Precomputing distances between {len(habitable_stars)} habitable stars")
    for n, star in enumerate(habitable_stars):
        neighbour_indexes = find_delaunay_neighbors(n, tris)
        for index in neighbour_indexes:
            if index == len(habitable_stars):
                continue  # where index 1094 is coming from, I don't know
            key = frozenset((n, index))
            other = habitable_stars[index]
            if key in star_distance_cache:
                distance = star_distance_cache[key]
            else:
                distance = other.position.distance(star.position)
                star_distance_cache[key] = distance

            star.precomputed_neighbours.append((other, distance))
        star.precomputed_neighbours = sorted(star.precomputed_neighbours, key=lambda t: t[1])

    # for star in habitable_stars:
    #     star.precomputed_neighbours = compute_neighbours(
    #         star_distance_cache, habitable_stars, star
    #     )

    return stars


def find_delaunay_neighbors(pindex, triang):
    neighbors = list()
    for simplex in triang.simplices:
        if pindex in simplex:
            neighbors.extend([simplex[i] for i in range(len(simplex)) if simplex[i] != pindex])
            '''
            this is a one liner for if a simplex contains the point we`re interested in,
            extend the neighbors list by appending all the *other* point indices in the simplex
            '''
    #now we just have to strip out all the dulicate indices and return the neighbors list:
    return list(set(neighbors))

def store_neighbours(star: Star, stars: List[Star], neighbour_indexes: Iterable[int]):
    neighbours = []
    for index in neighbour_indexes:
        if index == -1:
            continue
        other = stars[index]
        neighbours.append((other, other.position.distance(star.position)))
    star.precomputed_neighbours = sorted(neighbours, key=lambda tuple_: tuple_[1])


def compute_neighbours(
    cache: Dict[Tuple[Star, Star], float], stars: List[Star], star: Star
):
    neighbours = []
    for other in stars:
        if other == star:
            continue
        if (other, star) in cache:
            neighbours.append((other, cache[(other, star)]))
            continue
        distance = star.position.distance(other.position)
        cache[(star, other)] = distance
        neighbours.append((other, distance))
    return sorted(neighbours, key=lambda tuple_: tuple_[1])


if __name__ == "__main__":
    starmap = load_stellar_catalogue()
    print(
        f"{len([s for s in starmap if any(p.life_level == LifeLevel.intelligent_life for p in s.planets)])} with intelligent life"
    )
    print(
        f"{len([s for s in starmap if any(p.life_level != LifeLevel.precursor and p.life_level != LifeLevel.none and p.life_level != LifeLevel.intelligent_life for p in s.planets)])} with life"
    )
    print(
        f"{len([s for s in starmap if any(p.life_level == LifeLevel.precursor for p in s.planets)])} with life precursors"
    )
    print(f"{len([s for s in starmap if s.habitable])} habitable")
    print(f"{len(starmap)} total")
