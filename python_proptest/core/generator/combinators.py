"""
Combinator generators (one_of, element_of, just, lazy, construct).
"""

from typing import Any, Callable, List, TypeVar

from ..shrinker import Shrinkable
from ..stream import Stream
from .base import (
    Generator,
    Random,
    normalize_weighted_generators,
    normalize_weighted_values,
)

T = TypeVar("T")


class OneOfGenerator(Generator[T]):
    """Generator that randomly chooses from multiple generators with weights."""

    def __init__(self, generators: List[Any]):
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


class JustGenerator(Generator[T]):
    """Generator that always returns the same value."""

    def __init__(self, value: T):
        self.value = value

    def generate(self, rng: Random) -> Shrinkable[T]:
        return Shrinkable(self.value, lambda: Stream.empty())


class LazyGenerator(Generator[T]):
    """Generator that delays evaluation until generation."""

    def __init__(self, func: Callable[[], T]):
        self.func = func

    def generate(self, rng: Random) -> Shrinkable[T]:
        value = self.func()
        return Shrinkable(value, lambda: Stream.empty())


class ConstructGenerator(Generator[Any]):
    """Generator that constructs objects from generators."""

    def __init__(self, constructor: Callable, *generators: Generator):
        self.constructor = constructor
        self.generators = generators

    def generate(self, rng: Random) -> Shrinkable[Any]:
        shrinkables = [gen.generate(rng) for gen in self.generators]
        value = self.constructor(*[s.value for s in shrinkables])

        def shrink_func() -> Stream[Shrinkable[Any]]:
            # Generate shrinks by shrinking each argument
            shrinks = []
            for i, shrinkable in enumerate(shrinkables):
                for shrunk in shrinkable.shrinks().to_list():
                    new_shrinkables = shrinkables.copy()
                    new_shrinkables[i] = shrunk
                    new_value = self.constructor(*[s.value for s in new_shrinkables])
                    shrinks.append(Shrinkable(new_value))
            return Stream.many(shrinks)

        return Shrinkable(value, shrink_func)

