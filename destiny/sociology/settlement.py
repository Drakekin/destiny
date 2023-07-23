from collections import Counter
from random import Random
from typing import List, Type, Tuple, Optional
from uuid import UUID, uuid4

from destiny.sociology.government import Government
from destiny.sociology.pop import Population
from destiny.sociology.constants import POP_TARGET_SIZE
from destiny.sociology.utils.life import process_births_and_deaths
from destiny.sociology.utils.city_names import get_name


class Settlement:
    uuid: UUID
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
        self.uuid = uuid4()
        self.rng = rng
        self.pops = pops
        self.government = government_type(self)
        self.name = name

    @classmethod
    def for_pops(cls, rng: Random, pops: List[Population], name: Optional[str] = None):
        government_types = Counter()
        countries = Counter()
        for pop in pops:
            government_types[pop.preferred_government] += 1
            for ancestry, amount in pop.ancestry:
                countries[ancestry] += amount

        if name is None:
            origin_country = countries.most_common(1)[0][0]
            name = get_name(origin_country, rng)

        return Settlement(rng, name, pops, government_types.most_common(1)[0][0])

    @property
    def population(self):
        return sum(p.population for p in self.pops)

    def births_and_deaths(self, birth_rate_modifier: float):
        self.pops = process_births_and_deaths(self.pops, self.rng, birth_rate_modifier)

    def process_year(
        self, year: int, birth_rate_modifier: float
    ) -> Tuple[List[Tuple["Settlement", Population]], int, int]:
        """
        :param year: the current year
        :return: A list of unhappy pops, units of manufacturing, units of science
        """
        self.births_and_deaths(birth_rate_modifier)
        new_government = self.government.govern(self, year)
        if new_government:
            self.government = new_government
            for pop in self.pops:
                pop.happiness += 0.5

        agricultural_requirement = round(self.population / POP_TARGET_SIZE / 3)

        pops_to_move = []
        pops_to_stay = []
        average_stay_happiness = 0
        average_move_happiness = 0
        for pop in self.pops:
            if pop.wants_to_move():
                pops_to_move.append(pop)
                average_move_happiness += pop.happiness
            else:
                pops_to_stay.append(pop)
                average_stay_happiness += pop.happiness

        if not pops_to_stay:
            remainer = self.rng.choice(pops_to_move)
            pops_to_move.remove(remainer)
            pops_to_stay.append(remainer)

        if pops_to_move:
            average_move_happiness /= len(pops_to_move)
        average_stay_happiness /= len(pops_to_stay)

        effort = len(pops_to_stay) + (len(pops_to_move) // 4)

        if effort < agricultural_requirement:
            print(f"{self.name} cannot grow enough food! Their population has starved!")
            for pop in self.pops:
                pop.starve()
            effort = 0
        else:
            effort -= agricultural_requirement

        self.pops = pops_to_stay

        if effort > 0:
            science_output = round(
                self.government.traditionalist_technological * effort
            )
            manufacturing_output = effort - science_output
        else:
            science_output = 0
            manufacturing_output = 0

        return [(self, p) for p in pops_to_move], manufacturing_output, science_output
