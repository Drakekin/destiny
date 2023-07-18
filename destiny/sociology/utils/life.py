from destiny.sociology.constants import POP_TARGET_SIZE
from destiny.sociology.pop import Population


def process_births_and_deaths(pops, rng):
    for n, pop in enumerate(pops):
        pop.births_and_deaths(rng.randint(10, 80), rng.randint(1, 10))
    pops_with_descendents = [p for p in pops if p.descendents > 0]
    pops_with_descendents = rng.sample(
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
            pops.append(Population.form_next_generation(parent_pops))
    pops_with_no_starting_population = []
    pops_with_few_starting_population = []
    new_pops = []
    for pop in pops:
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
    return new_pops
