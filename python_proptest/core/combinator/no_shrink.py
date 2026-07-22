"""
NoShrink combinator generator.

Wraps a generator to produce the same values but with an empty shrink stream.
Use when shrinking is meaningless or undesirable — e.g. seeds, UUIDs,
timestamps, or when you want to suppress context shrinking in a flat_map chain.
"""

from typing import TypeVar

from ..generator.base import Generator, Random
from ..shrinker import Shrinkable

T = TypeVar("T")


class NoShrinkGenerator(Generator[T]):
    """Generator that strips shrink candidates from the wrapped generator.

    Generated values have identical distribution to the wrapped generator,
    but every Shrinkable produced carries an empty shrink stream.
    """

    def __init__(self, gen: Generator[T]):
        self.gen = gen

    def generate(self, rng: Random) -> Shrinkable[T]:
        return Shrinkable(self.gen.generate(rng).value)
