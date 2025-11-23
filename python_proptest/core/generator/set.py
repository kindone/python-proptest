"""
Generator for set types.
"""

from typing import List, Set, TypeVar

from ..shrinker import Shrinkable
from ..stream import Stream
from .base import Generator, Random

T = TypeVar("T")


class SetGenerator(Generator[Set[T]]):
    """Generator for sets."""

    def __init__(self, element_generator: Generator[T], min_size: int, max_size: int):
        self.element_generator = element_generator
        self.min_size = min_size
        self.max_size = max_size

    def generate(self, rng: Random) -> Shrinkable[Set[T]]:
        size = rng.randint(self.min_size, self.max_size)
        elements: List[Shrinkable[T]] = []
        seen = set()

        # Generate unique elements
        attempts = 0
        while len(elements) < size and attempts < size * 10:  # Prevent infinite loops
            elem_shrinkable = self.element_generator.generate(rng)
            if elem_shrinkable.value not in seen:
                elements.append(elem_shrinkable)
                seen.add(elem_shrinkable.value)
            attempts += 1

        value = {elem.value for elem in elements}
        shrinks = self._generate_shrinks(elements)
        return Shrinkable(value, lambda: Stream.many(shrinks))

    def _generate_shrinks(
        self, elements: List[Shrinkable[T]]
    ) -> List[Shrinkable[Set[T]]]:
        """Generate shrinking candidates for a set."""
        shrinks: List[Shrinkable[Set[T]]] = []

        # Empty set
        if len(elements) > 0:
            shrinks.append(Shrinkable(set()))

        # Sets with fewer elements
        if len(elements) > 1:
            # Remove last element
            shrinks.append(Shrinkable({elem.value for elem in elements[:-1]}))
            # Remove first element
            shrinks.append(Shrinkable({elem.value for elem in elements[1:]}))

        # Sets with shrunk elements
        for i, elem in enumerate(elements):
            for shrunk_elem in elem.shrinks().to_list():
                new_elements = elements.copy()
                new_elements[i] = shrunk_elem
                shrinks.append(Shrinkable({e.value for e in new_elements}))

        return shrinks
