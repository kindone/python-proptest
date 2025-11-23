"""
OneOf combinator generator.

Randomly chooses from multiple generators with optional weights.
"""

from typing import List, TypeVar

from ..generator.base import Generator, Random, normalize_weighted_generators
from ..shrinker import Shrinkable

T = TypeVar("T")


class OneOfGenerator(Generator[T]):
    """Generator that randomly chooses from multiple generators with weights."""

    def __init__(self, generators: List):
        if not generators:
            raise ValueError("At least one generator must be provided")
        self.weighted_generators = normalize_weighted_generators(generators)

    def generate(self, rng: Random) -> Shrinkable[T]:
        # Selection loop: repeatedly pick a generator index and check against its weight
        while True:
            dice = rng.randint(0, len(self.weighted_generators) - 1)
            weighted_gen = self.weighted_generators[dice]
            if rng.random() < weighted_gen.weight:
                return weighted_gen.generate(rng)
