import math
from collections import defaultdict, Counter
from typing import List, Optional, TYPE_CHECKING

from destiny.sociology.constants import POP_TARGET_SIZE

if TYPE_CHECKING:
    from destiny.sociology.pop import Population
    from destiny.sociology.settlement import Settlement


class Government:
    autocratic_democratic: float
    conservative_progressive: float
    pacifist_militaristic: float
    secular_religious: float
    traditionalist_technological: float

    def __init__(self, settlement: "Settlement"):
        pass

    def govern(self, settlement: "Settlement", year: int) -> Optional["Government"]:
        pass

    @staticmethod
    def council_size(settlement: "Settlement"):
        size = math.sqrt(settlement.population / POP_TARGET_SIZE / 50)
        return math.ceil(size)

    # TODO: Reduce hash size
    @property
    def opinion_hash(self) -> int:
        return (
            (round(self.autocratic_democratic))
            + (round(self.conservative_progressive) << 1)
            + (round(self.pacifist_militaristic) << 2)
            + (round(self.secular_religious) << 3)
            + (round(self.traditionalist_technological) << 4)
        )

    def suitable_for(self, pop: "Population") -> bool:
        boundary = pop.tolerance / 2
        return (
            abs(self.autocratic_democratic - pop.autocratic_democratic) < boundary
            and abs(self.conservative_progressive - pop.conservative_progressive)
            < boundary
            and abs(self.pacifist_militaristic - pop.pacifist_militaristic) < boundary
            and abs(self.secular_religious - pop.secular_religious) < boundary
            and abs(
                self.traditionalist_technological - pop.traditionalist_technological
            )
            < boundary
        )

    def suitability_for(self, pop: "Population") -> float:
        return (
            abs(self.autocratic_democratic - pop.autocratic_democratic)
            + abs(self.conservative_progressive - pop.conservative_progressive)
            + abs(self.pacifist_militaristic - pop.pacifist_militaristic)
            + abs(self.secular_religious - pop.secular_religious)
            + abs(self.traditionalist_technological - pop.traditionalist_technological)
        ) / 5


class Dictatorship(Government):
    dictator: "Population"

    def infer_opinion(self):
        self.autocratic_democratic = self.dictator.autocratic_democratic
        self.conservative_progressive = self.dictator.conservative_progressive
        self.pacifist_militaristic = self.dictator.pacifist_militaristic
        self.secular_religious = self.dictator.secular_religious
        self.traditionalist_technological = self.dictator.traditionalist_technological

    def __init__(self, settlement: "Settlement"):
        super(Dictatorship, self).__init__(settlement)
        self.dictator = settlement.rng.choice(settlement.pops)
        self.dictator.mergeable = False
        self.infer_opinion()

    def choose_new_dictator(self, settlement: "Settlement"):
        candidates = [pop for pop in settlement.pops if self.suitable_for(pop)]
        if not candidates:
            candidates = settlement.pops
        self.dictator = settlement.rng.choice(candidates)
        self.infer_opinion()

    def govern(self, settlement: "Settlement", year: int) -> Optional["Government"]:
        if self.dictator.is_dead:
            self.choose_new_dictator(settlement)
            self.infer_opinion()
        return None


class HereditaryDictatorship(Dictatorship):
    def choose_new_dictator(self, settlement: "Settlement"):
        candidates = self.dictator.descendent_pops
        if not candidates:
            candidates = [pop for pop in settlement.pops if self.suitable_for(pop)]
        if not candidates:
            candidates = settlement.pops
        self.dictator = settlement.rng.choice(candidates)
        self.infer_opinion()


def average_opinion(government: Government, pops: List["Population"]):
    government.autocratic_democratic = sum(
        (p.autocratic_democratic for p in pops)
    ) / len(pops)
    government.conservative_progressive = sum(
        (p.conservative_progressive for p in pops)
    ) / len(pops)
    government.pacifist_militaristic = sum(
        (p.pacifist_militaristic for p in pops)
    ) / len(pops)
    government.secular_religious = sum((p.secular_religious for p in pops)) / len(pops)
    government.traditionalist_technological = sum(
        (p.traditionalist_technological for p in pops)
    ) / len(pops)


class Autocracy(Government):
    council: List["Population"]

    def infer_opinion(self):
        average_opinion(self, self.council)

    def __init__(self, settlement: "Settlement"):
        super(Autocracy, self).__init__(settlement)
        self.council = []
        self.elect_council_members(settlement)

    def elect_council_members(self, settlement: "Settlement"):
        self.housekeeping(settlement)

        council_size = self.council_size(settlement)
        new_councilors = self.select_council_members(settlement, council_size)

        self.appoint_councilors(new_councilors)

        self.infer_opinion()

    def select_council_members(self, settlement: "Settlement", council_size: int):
        candidates = [pop for pop in settlement.pops if self.suitable_for(pop)]
        required = council_size - len(self.council)
        if required <= 0:
            new_councilors = []
        elif required > len(candidates):
            new_councilors = candidates
        else:
            new_councilors = settlement.rng.sample(candidates, required)
        return new_councilors

    def appoint_councilors(self, new_councilors: List["Population"]):
        for councilor in new_councilors:
            councilor.mergeable = False
            self.council.append(councilor)

    def housekeeping(self, settlement: "Settlement"):
        self.council = [
            councilor for councilor in self.council if not councilor.is_dead
        ]
        if not self.council:
            self.elect_initital_councilor(settlement)

    def elect_initital_councilor(self, settlement: "Settlement"):
        candidates = [pop for pop in settlement.pops if pop.autocratic_democratic < 0.5]
        if not candidates:
            candidates = settlement.pops
        seed_councilor = settlement.rng.choice(candidates)
        seed_councilor.mergeable = False
        self.council.append(seed_councilor)
        self.infer_opinion()

    def govern(self, settlement: "Settlement", year: int) -> Optional["Government"]:
        self.elect_council_members(settlement)
        return None


class HereditaryAutocracy(Autocracy):
    def elect_council_members(self, settlement: "Settlement"):
        council_size = self.council_size(settlement)

        pre_housekeeping_council_size = len(self.council)
        replacement_candidates = list(
            set(sum((p.descendent_pops for p in self.council), start=[]))
        )

        self.housekeeping(settlement)

        replacement_councilors = max(
            0, pre_housekeeping_council_size - len(self.council)
        )
        if replacement_councilors == 0:
            new_councilors = []
        elif replacement_councilors > len(replacement_candidates):
            new_councilors = replacement_candidates
        else:
            new_councilors = settlement.rng.sample(
                replacement_candidates, replacement_councilors
            )

        self.appoint_councilors(new_councilors)

        new_councilors = self.select_council_members(settlement, council_size)
        self.appoint_councilors(new_councilors)

        self.infer_opinion()


class RepresentativeDemocracy(Government):
    council: List["Population"]
    founding_year: int

    def __init__(self, settlement: "Settlement"):
        super().__init__(settlement)
        self.council = []
        self.elect_council_members(settlement)
        self.founding_year = -1
        self.term = settlement.rng.randint(2, 10)

    def govern(self, settlement: "Settlement", year: int) -> Optional["Government"]:
        if self.founding_year == -1:
            self.founding_year = year
        elif (self.founding_year - year) % self.term == 0:
            self.elect_council_members(settlement)

        return None

    def infer_opinions(self):
        councilors_by_opinion = defaultdict(list)
        for councilor in self.council:
            councilors_by_opinion[councilor.opinion_hash].append(councilor)

        winning_hash = max(
            councilors_by_opinion, key=lambda h: len(councilors_by_opinion[h])
        )
        average_opinion(self, councilors_by_opinion[winning_hash])

    def elect_council_members(self, settlement: "Settlement"):
        if self.council:
            for councilor in self.council:
                councilor.mergeable = True
            self.council = []

        if len(settlement.pops) == 1:
            councilor = settlement.pops[0]
            councilor.mergeable = False
            self.council.append(councilor)
            self.infer_opinions()
            return

        council_size = self.council_size(settlement)

        candidate_candidates = [
            p for p in settlement.pops if p.political_engagement > 0.5
        ]
        if not candidate_candidates:
            candidate_candidates = settlement.pops

        num_candidates = min(len(candidate_candidates), council_size * 3)
        candidates = settlement.rng.sample(candidate_candidates, num_candidates)

        candidates_by_opinion = defaultdict(list)
        for candidate in candidates:
            candidates_by_opinion[candidate.opinion_hash].append(candidate)

        votes = Counter()

        voting_threshold = settlement.rng.random() * 0.5
        voters = (
            pop
            for pop in settlement.pops
            if pop not in candidates and pop.political_engagement >= voting_threshold
        )
        for voter in voters:
            voter_opinion = voter.opinion_hash
            choices = candidates_by_opinion[voter_opinion]
            if len(choices) < council_size:
                # presort somehow?
                choices = candidates
            ranked_choices = sorted(choices, key=lambda pop: pop.similarity_to(voter))
            for candidate in ranked_choices[:council_size]:
                votes[candidate] += 1

        winners = votes.most_common(council_size)

        if winners:
            for winner, _ in winners:
                winner.mergable = False
                self.council.append(winner)
        else:
            self.council = settlement.rng.sample(candidates, council_size)

        self.infer_opinions()


class RepresentativeCoalition(RepresentativeDemocracy):
    def infer_opinion(self):
        average_opinion(self, self.council)


class DirectDemocracy(Government):
    def __init__(self, settlement: "Settlement"):
        super().__init__(settlement)
        self.infer_opinions(settlement)

    def govern(self, settlement: "Settlement", year: int) -> Optional["Government"]:
        self.infer_opinions(settlement)
        return None

    def infer_opinions(self, settlement: "Settlement"):
        population_by_opinion = defaultdict(list)
        for pop in settlement.pops:
            population_by_opinion[pop.opinion_hash].append(pop)

        winning_hash = max(
            population_by_opinion, key=lambda h: len(population_by_opinion[h])
        )
        average_opinion(self, population_by_opinion[winning_hash])


class DirectConsensus(DirectDemocracy):
    def infer_opinion(self, settlement: "Settlement"):
        average_opinion(self, settlement.pops)


GOVERNMENTS = (
    Dictatorship,
    HereditaryDictatorship,
    Autocracy,
    HereditaryAutocracy,
    RepresentativeDemocracy,
    RepresentativeCoalition,
    DirectDemocracy,
    DirectConsensus,
)
