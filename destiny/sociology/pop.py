import math
from collections import Counter
from random import Random
from typing import List, Tuple, Type
from uuid import uuid4

from destiny.sociology.government import (
    Government,
    HereditaryDictatorship,
    Dictatorship,
    HereditaryAutocracy,
    Autocracy,
    RepresentativeDemocracy,
    RepresentativeCoalition,
    DirectDemocracy,
    DirectConsensus,
)


class Population:
    rng: Random

    starting_population: int
    average_age: float
    descendents: int
    average_descendent_age: float
    generation: int
    ancestry: List[Tuple[str, int]]
    children: List[int]
    _happiness: float
    preferred_population_size: int
    mergeable: bool

    # statistics from 0-1
    stationary_migrant: float
    autocratic_democratic: float
    conservative_progressive: float
    pacifist_militaristic: float
    secular_religious: float
    settler_colonial: float
    traditionalist_technological: float
    tolerance: float

    descendent_pops: List["Population"]

    @property
    def political_engagement(self):
        return abs(self.autocratic_democratic - 0.5) * 2

    @property
    def preferred_government(self) -> Type[Government]:
        if self.autocratic_democratic > 0.5:
            if self.conservative_progressive < 0.5:
                if self.traditionalist_technological < 0.5:
                    return RepresentativeDemocracy
                else:
                    return RepresentativeCoalition
            else:
                if self.traditionalist_technological < 0.5:
                    return DirectDemocracy
                else:
                    return DirectConsensus
        else:
            if self.conservative_progressive < 0.5:
                if self.traditionalist_technological < 0.5:
                    return HereditaryDictatorship
                else:
                    return Dictatorship
            else:
                if self.traditionalist_technological < 0.5:
                    return HereditaryAutocracy
                else:
                    return Autocracy

    @property
    def happiness(self):
        return self._happiness

    @happiness.setter
    def happiness(self, value: float):
        self._happiness = max(0.0, min(1.0, value))

    def __init__(
        self,
        rng: Random,
        population: int,
        ancestry: List[Tuple[str, int]],
        randomise_statistics: bool = False,
    ):
        self.rng = rng
        self.uuid = uuid4()
        self.generation = 0
        self._happiness = 1.0
        self.mergeable = True
        self.preferred_population_size = self.rng.randint(10, 1_000)

        self.starting_population = population
        self.average_age = 20
        self.descendents = 0
        self.average_descendent_age = 0

        self.ancestry = ancestry
        self.children = [0] * 20

        self.descendent_pops = []

        if randomise_statistics:
            self.stationary_migrant = self.rng.random()
            self.autocratic_democratic = self.rng.random()
            self.conservative_progressive = self.rng.random()
            self.pacifist_militaristic = self.rng.random()
            self.secular_religious = self.rng.random()
            self.settler_colonial = self.rng.random()
            self.traditionalist_technological = self.rng.random()
            self.tolerance = self.rng.random()

    def births_and_deaths(
        self, birth_rate_per_thousand: int, accidental_death_rate_per_thousand: int
    ) -> int:
        """
        Called once per year, adjusts population for births and deaths

        :param birth_rate_per_thousand: number of children born per 1000 adults under 50, varies from 50 to 100
        :param accidental_death_rate_per_thousand: varies from 1 to 10
        :returns number of excess adults in pop
        """

        accidental_deaths = math.floor(
            self.population / 1000 * accidental_death_rate_per_thousand
        )

        death_ratio = self.descendents / (self.descendents + self.starting_population)
        self.descendents -= math.floor(accidental_deaths * death_ratio)
        self.starting_population -= math.ceil(accidental_deaths * (1 - death_ratio))

        starting_population_old_age_likelihood = (
            max(min((self.average_age - 25) / 100 + self.rng.uniform(-0.1, 0.1), 1), 0)
            ** 3
        )
        descendent_old_age_likelihood = (
            max(
                min(
                    (self.average_descendent_age - 25) / 100
                    + self.rng.uniform(-0.1, 0.1),
                    1,
                ),
                0,
            )
            ** 3
        )
        self.starting_population = math.floor(
            self.starting_population * (1 - starting_population_old_age_likelihood)
        )
        self.descendents = math.floor(
            self.descendents * (1 - descendent_old_age_likelihood)
        )

        new_adults = 0
        if len(self.children) >= 20:
            while len(self.children) >= 20:
                new_adults += self.children.pop()
        if self.descendents + new_adults > 0:
            self.average_descendent_age = (
                self.descendents * self.average_descendent_age + new_adults * 20
            ) / (self.descendents + new_adults)
        else:
            self.average_descendent_age = 0
        self.descendents += new_adults

        self.average_age += 1

        childbearing_population = (
            self.starting_population if self.average_age < 50 else 0
        ) + (self.descendents if self.average_descendent_age < 50 else 0)
        births = math.floor(childbearing_population / 1000 * birth_rate_per_thousand)

        self.children = [births] + self.children

        return self.descendents

    @property
    def population(self):
        return self.starting_population + self.descendents

    def inherit_statistics(self, pops: List["Population"], deviation: float = 0.125):
        self.stationary_migrant = max(
            0.0,
            min(
                1.0,
                sum((p.stationary_migrant for p in pops)) / len(pops)
                + self.rng.uniform(-deviation, deviation),
            ),
        )
        self.autocratic_democratic = max(
            0.0,
            min(
                1.0,
                sum((p.autocratic_democratic for p in pops)) / len(pops)
                + self.rng.uniform(-deviation, deviation),
            ),
        )
        self.conservative_progressive = max(
            0.0,
            min(
                1.0,
                sum((p.conservative_progressive for p in pops)) / len(pops)
                + self.rng.uniform(-deviation, deviation),
            ),
        )
        self.pacifist_militaristic = max(
            0.0,
            min(
                1.0,
                sum((p.pacifist_militaristic for p in pops)) / len(pops)
                + self.rng.uniform(-deviation, deviation),
            ),
        )
        self.secular_religious = max(
            0.0,
            min(
                1.0,
                sum((p.secular_religious for p in pops)) / len(pops)
                + self.rng.uniform(-deviation, deviation),
            ),
        )
        self.settler_colonial = max(
            0.0,
            min(
                1.0,
                sum((p.settler_colonial for p in pops)) / len(pops)
                + self.rng.uniform(-deviation, deviation),
            ),
        )
        self.traditionalist_technological = max(
            0.0,
            min(
                1.0,
                sum((p.traditionalist_technological for p in pops)) / len(pops)
                + self.rng.uniform(-deviation, deviation),
            ),
        )
        self.tolerance = max(
            0.0,
            min(
                1.0,
                sum((p.tolerance for p in pops)) / len(pops)
                + self.rng.uniform(-deviation, deviation),
            ),
        )
        self.preferred_population_size = min(max((round(sum(p.preferred_population_size for p in pops)/len(pops))) + self.rng.randint(-1000, 1000), 10), 1000)

    @classmethod
    def merge_small_pops(cls, pops: List["Population"]) -> List["Population"]:
        new_pops = []
        remaining_pops = pops

        while remaining_pops:
            candidate = remaining_pops.pop()
            if not candidate.mergeable:
                new_pops.append(candidate)
                continue
            mergeable = []
            for pop in remaining_pops:
                if pop.ancestry[0][0] == candidate.ancestry[0][0]:
                    mergeable.append(pop)
            if not mergeable:
                new_pops.append(candidate)
                continue

            for pop in mergeable:
                remaining_pops.remove(pop)

            mergeable.append(candidate)
            merged_pop = Population(
                candidate.rng,
                sum(p.starting_population for p in mergeable),
                [(candidate.ancestry[0][0], 100)],
            )
            if merged_pop.population == 0:
                continue
            merged_pop.average_age = (
                sum(p.starting_population * p.average_age for p in mergeable)
                / merged_pop.population
            )
            merged_pop.descendents = sum(p.descendents for p in mergeable)
            if merged_pop.descendents > 0:
                merged_pop.average_descendent_age = (
                    sum(p.descendents * p.average_descendent_age for p in mergeable)
                    / merged_pop.descendents
                )
            merged_pop.children = [
                sum(c) for c in zip(*[p.children for p in mergeable])
            ]
            merged_pop.inherit_statistics(mergeable, 0)
            merged_pop.descendent_pops = list(
                set(sum((p.descendent_pops for p in mergeable), start=[]))
            )

            new_pops.append(merged_pop)

        return new_pops

    @classmethod
    def form_next_generation(cls, pops: List["Population"]) -> "Population":
        new_population = 0
        people_years = 0
        new_children = [0] * 20
        ancestries = Counter()
        for pop in pops:
            percent = pop.descendents / pop.population
            new_population += pop.descendents
            people_years += pop.descendents * pop.average_descendent_age
            pop.descendents -= pop.descendents
            for n in range(len(pop.children)):
                children_to_move = math.floor(percent * pop.children[n])
                new_children[n] += children_to_move
                pop.children[n] -= children_to_move
            for ancestry, weighting in pop.ancestry:
                ancestries[ancestry] += weighting
        unnormalised_ancestries = ancestries.most_common(3)
        total_ancestry = sum(n for _, n in unnormalised_ancestries)
        new_pop = Population(
            pops[0].rng,
            new_population,
            [
                (a, int(round(n / total_ancestry * 100)))
                for a, n in unnormalised_ancestries
            ],
        )
        new_pop.children = new_children
        new_pop.average_age = people_years / new_population
        new_pop.inherit_statistics(pops)
        new_pop.generation = max(p.generation for p in pops) + 1
        for pop in pops:
            pop.descendent_pops.append(new_pop)
        return new_pop

    @property
    def opinion_hash(self) -> int:
        return (
            (round(self.autocratic_democratic))
            + (round(self.conservative_progressive) << 1)
            + (round(self.pacifist_militaristic) << 2)
            + (round(self.secular_religious) << 3)
            + (round(self.traditionalist_technological) << 4)
        )

    def __hash__(self):
        return self.uuid.__hash__()

    def __eq__(self, other):
        return self.uuid == other.uuid

    def wants_to_move(self) -> bool:
        if not self.mergeable:
            return False
        return self.rng.random() - self.happiness > self.stationary_migrant

    @property
    def is_dead(self):
        return self.starting_population <= 0

    def similarity_to(self, pop: "Population") -> float:
        return (
            abs(self.autocratic_democratic - pop.autocratic_democratic)
            + abs(self.conservative_progressive - pop.conservative_progressive)
            + abs(self.pacifist_militaristic - pop.pacifist_militaristic)
            + abs(self.secular_religious - pop.secular_religious)
            + abs(self.traditionalist_technological - pop.traditionalist_technological)
        ) / 5

    def starve(self):
        self.happiness -= 0.25
        if self.happiness == 0:
            self.starting_population *= 0.9
