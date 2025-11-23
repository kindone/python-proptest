"""
ElementOf combinator generator.

Randomly chooses from multiple values with optional weights.
"""

from typing import Any, List, TypeVar

from ..generator.base import Generator, Random, normalize_weighted_values
from ..shrinker import Shrinkable
from ..stream import Stream

T = TypeVar("T")


class ElementOfGenerator(Generator[T]):
    """Generator that randomly chooses from multiple values with optional weights."""

    def __init__(self, values: List[Any]):
        if not values:
            raise ValueError("At least one value must be provided")
        self.weighted_values = normalize_weighted_values(values)

    def generate(self, rng: Random) -> Shrinkable[T]:
        # Selection loop: repeatedly pick a value index and check against its weight
        while True:
            dice = rng.randint(0, len(self.weighted_values) - 1)
            weighted_value = self.weighted_values[dice]
            if rng.random() < weighted_value.weight:
                value = weighted_value.value
                # Generate shrinks by trying other values
                shrinks = [
                    Shrinkable(wv.value)
                    for wv in self.weighted_values
                    if wv.value != value
                ]
                return Shrinkable(value, lambda: Stream.many(shrinks))
