import json
from typing import List

from destiny.cartography.planet import Planet, LifeLevel
from destiny.cartography.star import Star
from destiny.maths import Vec3


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

    return stars


if __name__ == "__main__":
    from random import choice

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
