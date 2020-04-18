"""A class containing useful utility classes."""

from __future__ import annotations
from typing import *
from math import sqrt, sin, cos
from dataclasses import *

Number = Union[int, float, complex]


class Vector:
    """A Python implementation of a vector class and some of its operations."""

    values: List[Number] = None

    def __init__(self, *args):
        self.values = list(args)

    def __str__(self):
        """String representation of a vector is its components surrounded by < and >."""
        return f"<{str(self.values)[1:-1]}>"

    __repr__ = __str__

    def __len__(self):
        """Defines the length of the vector as the number of its components."""
        return len(self.values)

    def __hash__(self):
        """Defines the hash of the vector as a hash of a tuple with its components."""
        return hash(tuple(self))

    def __eq__(self, other: Vector):
        """Defines vector equality as the equality of all of its components."""
        return self.values == other.values

    def __setitem__(self, i: int, value: Number):
        """Sets the i-th vector component to the specified value."""
        self.values[i] = value

    def __getitem__(self, i: int):
        """Either returns a new vector when sliced, or the i-th vector component."""
        if type(i) == slice:
            return Vector(*self.values[i])
        else:
            return self.values[i]

    def __delitem__(self, i: int):
        """Deletes the i-th component of the vector."""
        del self.values[i]

    def __neg__(self):
        """Defines vector negation as the negation of all of its components."""
        return Vector(*iter(-component for component in self))

    def __add__(self, other: Vector):
        """Defines vector addition as the addition of each of their components."""
        return Vector(*iter(u + v for u, v in zip(self, other)))

    __iadd__ = __add__

    def __sub__(self, other: Vector):
        """Defines vector subtraction as the subtraction of each of its components."""
        return Vector(*iter(u - v for u, v in zip(self, other)))

    __isub__ = __sub__

    def __mul__(self, other: Vector):
        """Defines scalar and dot multiplication of a vector."""
        if type(other) in get_args(Number):
            return Vector(*iter(component * other for component in self))
        else:
            return sum(u * v for u, v in zip(self, other))

    __rmul__ = __imul__ = __mul__

    def __truediv__(self, other: Number):
        """Defines vector division by a scalar."""
        return Vector(*iter(component / other for component in self))

    def __floordiv__(self, other: Number):
        """Defines floor vector division by a scalar."""
        return Vector(*iter(component // other for component in self))

    def __matmul__(self, other: Vector):
        """Defines cross multiplication of a vector."""
        return Vector(
            self[1] * other[2] - self[2] * other[1],
            self[2] * other[0] - self[0] * other[2],
            self[0] * other[1] - self[1] * other[0],
        )

    __imatmul__ = __matmul__

    def __mod__(self, other: Number):
        """Defines vector mod as the mod of its components."""
        return Vector(*iter(component % other for component in self))

    def magnitude(self):
        """Returns the magnitude of the vector."""
        return sqrt(sum(component ** 2 for component in self))

    def rotated(self, angle: float, point: Vector = None):
        """Returns this vector rotated by an angle (in radians) around a certain point."""
        if point is None:
            point = Vector(0, 0)

        return self.__rotated(angle, self - point) + point

    def __rotated(self, angle: float, vector: Vector):
        """Returns a vector rotated by an angle (in radians)."""
        return Vector(
            vector[0] * cos(angle) - vector[1] * sin(angle),
            vector[0] * sin(angle) + vector[1] * cos(angle),
        )

    def unit(self):
        """Returns a unit vector with the same direction as this vector."""
        return self / self.magnitude()

    def abs(self):
        """Returns a vector with absolute values of the components of this vector."""
        return Vector(*iter(abs(component) for component in self))

    def distance(self, other: Vector):
        """Returns the distance of two Vectors in space."""
        return sqrt(sum(map(lambda x: sum(x) ** 2, zip(self, -other))))

    def repeat(self, n: int):
        """Performs sequence repetition on the vector (n times)."""
        return Vector(*self.values * n)

    def project(self, p: Number, q: Number) -> Vector:
        """Project this vector (point) onto a line, given its slope and intercept.
        Return the vector from the point to the line."""
        v = Vector(self[0], self[1] - q)
        s = Vector(1, p)

        return (v * s) / (s * s) * s - v

    @classmethod
    def sum(cls, l: List[Vector]):
        """Return the sum of the given vectors."""
        return sum(l[1:], l[0])

    @classmethod
    def average(cls, l: List[Vector]):
        """Return the average of the given vectors."""
        return Vector.sum(l) / len(l)

    @classmethod
    def fit_line(cls, points: List[Vector]) -> Tuple[Vector, Vector]:
        """Fit a line through a sequence of points, returning its slope and intercept."""
        n = len(points)

        sums = Vector(0, 0, 0, 0)
        for x, y in points:
            sums += Vector(x, y, x ** 2, x * y)

        p = (n * sums[3] - sums[0] * sums[1]) / (n * sums[2] - sums[0] ** 2)
        q = (sums[1] - p * sums[0]) / n

        return p, q


@dataclass
class Transformation:
    """A class for working with the current transformation of the canvas."""

    canvas: QWidget  # get the widget so we can calculate the current width and height

    # initial scale and transformation
    scale: float = 20
    translation: float = Vector(0, 0)

    def transform_painter(self, painter: QPainter):
        """Translate the painter according to the current canvas state."""
        painter.translate(*self.translation)
        painter.scale(self.scale, self.scale)

    def apply(self, point: Vector):
        """Apply the current canvas transformation on the point."""
        return (point - self.translation) / self.scale

    def inverse(self, point: Vector):
        """The inverse of apply."""
        return point * self.scale + self.translation

    def center(self, point: Vector, center_smoothness=0.3):
        """Center the transformation on the given point."""
        middle = self.apply(Vector(self.canvas.width(), self.canvas.height()) / 2)
        self.translation = self.inverse((middle - point) * center_smoothness)

    def translate(self, delta: Vector):
        """Translate the transformation by the vector delta delta."""
        self.translation += delta * self.scale

    def zoom(self, position: Vector, delta: float):
        """Zoom in/out."""
        # adjust the scale
        previous_scale = self.scale
        self.scale *= 2 ** delta  # scale smoothly

        # adjust translation so the x and y of the mouse stay in the same spot
        self.translation -= position * (self.scale - previous_scale)