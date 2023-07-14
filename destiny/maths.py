import math


class Vec3:
    x: float
    y: float
    z: float

    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    def __hash__(self):
        return (self.x, self.y, self.z).__hash__()

    def distance(self, other: "Vec3"):
        return math.sqrt(
            ((self.x - other.x) ** 2)
            + ((self.y - other.y) ** 2)
            + ((self.z - other.z) ** 2)
        )

    def __str__(self):
        return f"({round(self.x, 2)}, {round(self.y, 2)}, {round(self.z, 2)})"
