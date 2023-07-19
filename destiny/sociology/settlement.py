from collections import Counter
from random import Random
from typing import List, Type, Tuple, Optional

from destiny.sociology.government import Government
from destiny.sociology.pop import Population
from destiny.sociology.constants import POP_TARGET_SIZE
from destiny.sociology.utils.life import process_births_and_deaths
from destiny.sociology.utils.city_names import get_name


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

    def births_and_deaths(self):
        self.pops = process_births_and_deaths(self.pops, self.rng)

    def process_year(
        self, year: int
    ) -> Tuple[List[Tuple["Settlement", Population]], int, int]:
        """
        :param year: the current year
        :return: A list of unhappy pops, units of manufacturing, units of science
        """
        self.births_and_deaths()
        new_government = self.government.govern(self, year)
        if new_government:
            self.government = new_government

        agricultural_requirement = round(self.population / POP_TARGET_SIZE / 3)

        pops_to_move = []
        pops_to_stay = []
        for pop in self.pops:
            # TODO: incorporate government suitability into happiness
            if not self.government.suitable_for(pop) and pop.wants_to_move():
                pops_to_move.append(pop)
            else:
                pops_to_stay.append(pop)

        if not pops_to_stay:
            remainer = self.rng.choice(pops_to_move)
            pops_to_move.remove(remainer)
            pops_to_stay.append(remainer)

        self.pops = pops_to_stay
        effort = len(self.pops) + (len(pops_to_move) // 2) - agricultural_requirement

        if effort > 0:
            science_output = round(
                self.government.traditionalist_technological * effort
            )
            manufacturing_output = effort - science_output
        else:
            science_output = 0
            manufacturing_output = 0

        return [(self, p) for p in pops_to_move], manufacturing_output, science_output
