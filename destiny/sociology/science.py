from typing import List, Tuple, Optional


class Technology:
    pass


class SuperheavySpacecraft(Technology):
    capacity: int
    cost: int

    def __init__(self, capacity: int, cost: int):
        self.capacity = capacity
        self.cost = cost

    def __str__(self):
        return f"spacecraft carrying {self.capacity} pops costing {self.cost}/pop"


class Sublight(Technology):
    acceleration: float
    maximum_range: float

    def __init__(self, acceleration: float, range: float):
        self.acceleration = acceleration
        self.maximum_range = range

    def __str__(self):
        return f"sublight engines that can accelerate at {self.acceleration}g up to {self.maximum_range}ly"


class Spacefolding(Technology):
    ftl_speed: float
    maximum_range: float

    def __init__(self, speed: float, range: float):
        self.ftl_speed = speed
        self.maximum_range = range

    def __str__(self):
        return f"space folding engines that can travel at {self.ftl_speed}c up to {self.maximum_range}ly"


class Wormholes(Technology):
    cost: int
    range: float
    capacity: int

    def __init__(self, cost: int, range: float):
        self.cost = cost
        self.range = range

    def __str__(self):
        return f"a stable artificial wormhole that can span {self.range}ly and costs {self.cost}"


class ScienceNode:
    options: List["ScienceNode"]
    provides: Tuple[Technology]

    def __init__(self, *techs: Technology):
        self.provides = techs
        self.options = []

    def leads_to(
        self, *techs: Technology, node: Optional["ScienceNode"] = None
    ) -> "ScienceNode":
        if not node:
            node = ScienceNode(*techs)
        self.options.append(node)
        return node

    def __str__(self):
        s = " and ".join(str(t) for t in self.provides)
        return s[0].upper() + s[1:]


sublight_I = Sublight(0.2, 10)
sublight_II = Sublight(0.4, 12)
sublight_III = Sublight(0.6, 15)
sublight_IV = Sublight(0.8, 19)
sublight_V = Sublight(1, 24)

superheavy_I = SuperheavySpacecraft(2, 5)
superheavy_II = SuperheavySpacecraft(3, 10)
superheavy_III = SuperheavySpacecraft(4, 17)
superheavy_IV = SuperheavySpacecraft(5, 26)
superheavy_V = SuperheavySpacecraft(6, 20)
superheavy_VI = SuperheavySpacecraft(7, 15)
superheavy_VII = SuperheavySpacecraft(8, 10)
superheavy_VIII = SuperheavySpacecraft(9, 5)

foldspace_I = Spacefolding(2.5, 25)
foldspace_II = Spacefolding(5, 50)
foldspace_III = Spacefolding(10, 75)
foldspace_IV = Spacefolding(20, 100)
foldspace_V = Spacefolding(40, 125)
foldspace_VI = Spacefolding(80, 150)
foldspace_VII = Spacefolding(160, 175)
foldspace_VIII = Spacefolding(320, 200)

wormhole_I = Wormholes(1000, 10)
wormhole_II = Wormholes(900, 12)
wormhole_III = Wormholes(800, 15)
wormhole_IV = Wormholes(700, 19)
wormhole_V = Wormholes(600, 24)
wormhole_VI = Wormholes(500, 30)
wormhole_VII = Wormholes(400, 37)
wormhole_VIII = Wormholes(300, 45)

TECH_TREE = constant_thrust = ScienceNode(sublight_I, superheavy_I)
sublight_tree = (
    constant_thrust.leads_to(sublight_II)
    .leads_to(sublight_III, superheavy_II)
    .leads_to(sublight_IV)
    .leads_to(sublight_V, superheavy_III)
    .leads_to(foldspace_I)
)

foldspace_tree = (
    sublight_tree.leads_to(foldspace_II, superheavy_IV)
    .leads_to(foldspace_III)
    .leads_to(foldspace_IV, superheavy_V)
    .leads_to(foldspace_V)
    .leads_to(foldspace_VI, superheavy_VI)
    .leads_to(foldspace_VII)
    .leads_to(foldspace_VIII, superheavy_VII)
)

wormhole_tree = (
    sublight_tree.leads_to(wormhole_I, superheavy_IV)
    .leads_to(wormhole_II)
    .leads_to(wormhole_III, superheavy_V)
    .leads_to(wormhole_IV)
    .leads_to(wormhole_V, superheavy_VI)
    .leads_to(wormhole_VI)
    .leads_to(wormhole_VII, superheavy_VII)
    .leads_to(wormhole_VIII)
)
