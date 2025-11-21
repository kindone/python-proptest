"""
Just combinator generator.

Always returns the same value.
"""

from typing import TypeVar

from ..shrinker import Shrinkable
from ..stream import Stream
from ..generator.base import Generator, Random

T = TypeVar("T")


class JustGenerator(Generator[T]):
    """Generator that always returns the same value."""

    def __init__(self, value: T):
        self.value = value

    def generate(self, rng: Random) -> Shrinkable[T]:
        return Shrinkable(self.value, lambda: Stream.empty())

