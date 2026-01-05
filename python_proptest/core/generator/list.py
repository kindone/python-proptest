"""
Generators for list types.
"""

from typing import List, TypeVar

from ..shrinker import Shrinkable, shrink_list  # type: ignore[attr-defined]
from ..stream import Stream
from .base import Generator, Random

T = TypeVar("T")


class ListGenerator(Generator[List[T]]):
    """Generator for lists."""

    def __init__(
        self, element_generator: Generator[T], min_length: int, max_length: int
    ):
        self.element_generator = element_generator
        self.min_length = min_length
        self.max_length = max_length

    def generate(self, rng: Random) -> Shrinkable[List[T]]:
        length = rng.randint(self.min_length, self.max_length)
        elements = [self.element_generator.generate(rng) for _ in range(length)]
        # Use shrink_list which respects min_size constraint
        return shrink_list(elements, min_size=self.min_length)


class UniqueListGenerator(Generator[List[T]]):
    """Generator for lists with unique elements."""

    def __init__(
        self, element_generator: "Generator[T]", min_length: int, max_length: int
    ):
        self.element_generator = element_generator
        self.min_length = min_length
        self.max_length = max_length

    def generate(self, rng: Random) -> Shrinkable[List[T]]:
        """Generate a list with unique elements."""
        # Use set generator and convert to list
        from .set import SetGenerator

        set_gen = SetGenerator(self.element_generator, self.min_length, self.max_length)
        set_shrinkable = set_gen.generate(rng)

        # Convert set to sorted list
        unique_list = list(set_shrinkable.value)
        unique_list.sort()

        # Generate shrinks by converting set shrinks to list shrinks
        shrinks = []
        for set_shrink in set_shrinkable.shrinks():
            shrink_list = list(set_shrink.value)
            shrink_list.sort()
            shrinks.append(Shrinkable(shrink_list))

        return Shrinkable(unique_list, lambda: Stream.many(shrinks))
