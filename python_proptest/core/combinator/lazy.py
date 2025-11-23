"""
Lazy combinator generator.

Delays evaluation until generation.
"""

from typing import Callable, TypeVar

from ..generator.base import Generator, Random
from ..shrinker import Shrinkable
from ..stream import Stream

T = TypeVar("T")


class LazyGenerator(Generator[T]):
    """Generator that delays evaluation until generation."""

    def __init__(self, func: Callable[[], T]):
        self.func = func

    def generate(self, rng: Random) -> Shrinkable[T]:
        value = self.func()
        return Shrinkable(value, lambda: Stream.empty())
