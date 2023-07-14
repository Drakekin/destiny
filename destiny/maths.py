import math


class Vec3:
    x: float
    y: float
    z: float

    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    def distance(self, other: "Vec3"):
        return math.sqrt(
            ((self.x - other.x) ** 2)
            + ((self.y - other.y) ** 2)
            + ((self.z - other.z) ** 2)
        )
