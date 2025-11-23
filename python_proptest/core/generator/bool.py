"""
Generator for boolean values.
"""

from ..shrinker import Shrinkable
from ..shrinker.bool import shrink_bool
from .base import Generator, Random


class BoolGenerator(Generator[bool]):
    """Generator for booleans with configurable probability."""

    def __init__(self, true_prob: float = 0.5):
        self.true_prob = true_prob

    def generate(self, rng: Random) -> Shrinkable[bool]:
        value = rng.random() < self.true_prob
        return shrink_bool(value)
