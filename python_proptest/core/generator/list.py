"""
Generators for list types.
"""

from typing import List, TypeVar

from ..shrinker import Shrinkable
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
        value = [elem.value for elem in elements]
        shrinks = self._generate_shrinks(elements)
        return Shrinkable(value, lambda: Stream.many(shrinks))

    def _generate_shrinks(
        self, elements: List[Shrinkable[T]]
    ) -> List[Shrinkable[List[T]]]:
        """Generate shrinking candidates for a list without duplicates."""
        shrinks: List[Shrinkable[List[T]]] = []
        seen = set()

        def make_hashable(x):  # recursive helper
            if isinstance(x, dict):
                return tuple(sorted((k, make_hashable(v)) for k, v in x.items()))
            if isinstance(x, list):
                return tuple(make_hashable(v) for v in x)
            if isinstance(x, set):
                return tuple(sorted(make_hashable(v) for v in x))
            return x

        def add_candidate(vals: List[T]):
            key = make_hashable(vals)
            if key in seen:
                return
            seen.add(key)
            shrinks.append(Shrinkable(list(vals)))

        # Empty list
        if len(elements) > 0:
            add_candidate([])

        # Shorter lists (remove last / first)
        if len(elements) > 1:
            add_candidate([elem.value for elem in elements[:-1]])
            add_candidate([elem.value for elem in elements[1:]])

        # Lists with individual element shrinks
        for i, elem in enumerate(elements):
            for shrunk_elem in elem.shrinks().to_list():
                new_elements = elements.copy()
                new_elements[i] = shrunk_elem
                add_candidate([e.value for e in new_elements])

        return shrinks


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
