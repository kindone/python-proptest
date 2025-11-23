"""
Construct combinator generator.

Constructs objects from generators.
"""

from typing import Any, Callable

from ..generator.base import Generator, Random
from ..shrinker import Shrinkable
from ..stream import Stream


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
