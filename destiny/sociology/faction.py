from random import Random
from typing import List

from destiny.sociology.inhabitedplanet import InhabitedPlanet


FACTION_NAME_SUFFIXES = {
    0b0: "empire",
    0b10000: "hegemony",
    0b1000: "dominion",
    0b11000: "congregation",
    0b100: "alliance",
    0b10100: "axis",
    0b1100: "pact",
    0b11100: "crusade",
    0b10: "kingdom",
    0b10010: "bloc",
    0b1010: "coalition",
    0b11010: "league",
    0b110: "concordat",
    0b10110: "combine",
    0b1110: "fraternity",
    0b11110: "sorority",
    0b1: "affiliation",
    0b10001: "federation",
    0b1001: "compact",
    0b11001: "league",
    0b101: "entente",
    0b10101: "guild",
    0b1101: "consortium",
    0b11101: "syndicate",
    0b11: "association",
    0b10011: "confederation",
    0b1011: "treaty",
    0b11011: "mutual",
    0b111: "conjunction",
    0b10111: "accord",
    0b1111: "communion",
    0b11111: "collaboration",
}
PREFIX_LIST = [
    "new ", "old ", "post-", "pre-", "inter-", "extra-"
]
ADJECTIVE_LIST = [
    "ancient", "golden", "democratic", "stellar", "eternal",
    "traditional", "modern", "utopian",
]


class Faction:
    conservative_progressive: float
    pacifist_militaristic: float
    secular_religious: float
    traditionalist_technological: float

    members: List[InhabitedPlanet]
    name: str

    rng: Random

    def generate_name(self):
        noun_options = []
        faction_type_options = []
        for planet in self.members:
            noun_options.append(planet.name)
            for settlement in planet.settlements:
                noun_options.append(settlement.name)
                faction_type_options.append(FACTION_NAME_SUFFIXES[settlement.government.opinion_hash])
                for pop in settlement.pops:
                    noun_options.append(pop.ancestry[0][0])

        noun = self.rng.choice(noun_options)
        type_ = self.rng.choice(faction_type_options)
        prefix = self.rng.choice(PREFIX_LIST)
        adjective = self.rng.choice(ADJECTIVE_LIST)
        return self.rng.choice([
            f"{prefix}{noun} {type_}",
            f"{noun} {adjective} {type_}"
            f"{adjective} {type_} of {noun}",
            f"{prefix}{adjective} {noun} {type_}"
            f"{noun} {type_}"
            f"{adjective} {type_}"
            f"{prefix}{adjective} {type_}"
            f"{prefix}{noun}"
        ])

    def __init__(self, rng: Random, founding_members: List[InhabitedPlanet]):
        self.rng = rng
        self.members = []
        self.members.extend(founding_members)
        self.name = self.generate_name()
