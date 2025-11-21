"""
Generator for floating point values.
"""

from ..shrinker import Shrinkable
from ..shrinker.floating import shrink_float
from .base import Generator, Random


class FloatGenerator(Generator[float]):
    """Generator for floats."""

    def __init__(self, min_value: float, max_value: float):
        self.min_value = min_value
        self.max_value = max_value

    def generate(self, rng: Random) -> Shrinkable[float]:
        value = rng.random() * (self.max_value - self.min_value) + self.min_value
        return shrink_float(value)

