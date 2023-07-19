from collections import defaultdict
from random import Random
from typing import Dict, List

country_translations = {
    "Congo (Brazzaville)": "Republic of the Congo",
    "Congo (Kinshasa)": "Democratic Republic of the Congo",
    "Gaza Strip": "Palestine",
    "West Bank": "Palestine",
    "U.S. Virgin Islands": "United States Virgin Islands",
    "Bonaire": "Netherlands",
    "Christmas Island": "Australia",
    "Kosovo": "Serbia",
    "Swaziland": "Eswatini",
    "The Gambia": "Gambia",
    "The Bahamas": "Bahamas",
    "Svalbard": "Norway",
}


def load_city_list() -> Dict[str, List[str]]:
    cities = defaultdict(list)
    with open("data/worldcities.csv", encoding='utf-8-sig') as cities_csv:
        for line in cities_csv:
            country: str
            _, city, _, _, country, *_ = line.split(",")
            city = city.replace('"', "").replace("\\", "")
            country = country.replace('"', "").replace("\\", "")
            country = country_translations.get(country, country)
            cities[country].append(city)
    return cities


CITY_LIST = load_city_list()


def get_name(origin_country: str, rng: Random) -> str:
    candidates = CITY_LIST[origin_country]

    if not candidates:
        candidates = CITY_LIST[rng.choice([key for key in CITY_LIST if len(CITY_LIST[key]) > 0])]

    name = rng.choice(candidates)
    candidates.remove(name)
    return name
