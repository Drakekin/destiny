from collections import defaultdict, Counter
from random import Random
from typing import List, Type

from destiny.cartography.planet import Planet
from destiny.sociology.government import Government
from destiny.sociology.pop import Population
from destiny.sociology.constants import POP_TARGET_SIZE


class Settlement:
    rng: Random
    pops: List[Population]
    government: Government
    name: str

    def __init__(
        self,
        rng: Random,
        name: str,
        pops: List[Population],
        government_type: Type[Government],
    ):
        self.rng = rng
        self.pops = pops
        self.government = government_type(self)
        self.name = name

    @property
    def population(self):
        return sum(p.population for p in self.pops)

    def births_and_deaths(self):
        for n, pop in enumerate(self.pops):
            pop.births_and_deaths(self.rng.randint(10, 80), self.rng.randint(1, 10))

        pops_with_descendents = [p for p in self.pops if p.descendents > 0]
        pops_with_descendents = self.rng.sample(
            pops_with_descendents, len(pops_with_descendents)
        )
        while pops_with_descendents:
            parent_pops = []
            while (
                sum(p.descendents for p in parent_pops) < POP_TARGET_SIZE
                and pops_with_descendents
            ):
                parent_pops.append(pops_with_descendents.pop())

            if sum(p.descendents for p in parent_pops) >= POP_TARGET_SIZE:
                self.pops.append(Population.form_next_generation(parent_pops))

        pops_with_no_starting_population = []
        pops_with_few_starting_population = []
        new_pops = []
        for pop in self.pops:
            if pop.population > 0:
                if pop.starting_population < POP_TARGET_SIZE / 20:
                    pops_with_few_starting_population.append(pop)
                elif pop.starting_population <= 0:
                    pops_with_no_starting_population.append(pop)
                else:
                    new_pops.append(pop)
        if pops_with_no_starting_population:
            new_pops.append(
                Population.form_next_generation(pops_with_no_starting_population)
            )
        if pops_with_few_starting_population:
            new_pops += Population.merge_small_pops(pops_with_few_starting_population)
        self.pops = new_pops

    def process_year(self, year: int) -> List[Population]:
        self.births_and_deaths()
        new_government = self.government.govern(self, year)
        if new_government:
            self.government = new_government

        pops_to_move = []
        pops_to_stay = []
        for pop in self.pops:
            if not self.government.suitable_for(pop) and pop.wants_to_move():
                pops_to_move.append(pop)
            else:
                pops_to_stay.append(pop)

        self.pops = pops_to_stay
        return pops_to_move


class InhabitedPlanet:
    settlements: List[Settlement]
    rng: Random

    def __init__(self, rng: Random, planet: Planet):
        self.settlements = []
        self.rng = rng
        self.planet = planet

    @property
    def population(self):
        return sum([s.population for s in self.settlements])

    def process_year(self, year: int):
        unhappy_pops = []
        settlements_by_government = defaultdict(list)
        for settlement in self.settlements:
            unhappy_pops += [(settlement, pop) for pop in settlement.process_year(year)]
            settlements_by_government[settlement.government.opinion_hash].append(
                settlement
            )

        print(f"{len(unhappy_pops)} pops want to move")
        moved = 0
        stayed = 0

        moves = Counter()
        for n, (original_settlement, pop) in enumerate(unhappy_pops):
            opinion = pop.opinion_hash
            for candidate in settlements_by_government[opinion]:
            # for candidate in self.rng.sample(
            #     settlements_by_government[opinion],
            #     min(len(settlements_by_government[opinion]), 10),
            # ):
                if candidate.government.suitable_for(pop):
                    candidate.pops.append(pop)
                    moved += 1
                    moves[original_settlement.name, candidate.name] += pop.population
                    break
            else:
                original_settlement.pops.append(pop)
                stayed += 1

        print(f"Moved {moved}/{len(unhappy_pops)}, stayed {stayed}/{len(unhappy_pops)}")
