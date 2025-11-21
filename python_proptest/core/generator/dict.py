"""
Generator for dictionary types.
"""

from typing import Dict, List, Tuple, TypeVar

from ..shrinker import Shrinkable
from ..stream import Stream
from .base import Generator, Random

T = TypeVar("T")
U = TypeVar("U")


class DictGenerator(Generator[Dict[T, U]]):
    """Generator for dictionaries."""

    def __init__(
        self,
        key_generator: Generator[T],
        value_generator: Generator[U],
        min_size: int,
        max_size: int,
    ):
        self.key_generator = key_generator
        self.value_generator = value_generator
        self.min_size = min_size
        self.max_size = max_size

    def generate(self, rng: Random) -> Shrinkable[Dict[T, U]]:
        size = rng.randint(self.min_size, self.max_size)
        items = []
        for _ in range(size):
            key_shrinkable = self.key_generator.generate(rng)
            value_shrinkable = self.value_generator.generate(rng)
            items.append((key_shrinkable, value_shrinkable))

        value = {key.value: value.value for key, value in items}
        shrinks = self._generate_shrinks(items)
        return Shrinkable(value, lambda: Stream.many(shrinks))

    def _generate_shrinks(
        self, items: List[Tuple[Shrinkable[T], Shrinkable[U]]]
    ) -> List[Shrinkable[Dict[T, U]]]:
        """Generate shrinking candidates for a dictionary."""
        shrinks: List[Shrinkable[Dict[T, U]]] = []

        # Empty dictionary
        if len(items) > 0:
            shrinks.append(Shrinkable({}))

        # Dictionaries with fewer items
        if len(items) > 1:
            shrinks.append(
                Shrinkable({key.value: value.value for key, value in items[:-1]})
            )
            shrinks.append(
                Shrinkable({key.value: value.value for key, value in items[1:]})
            )

        # Dictionaries with shrunk values
        for i, (key_shrinkable, value_shrinkable) in enumerate(items):
            for shrunk_value in value_shrinkable.shrinks().to_list():
                new_items = items.copy()
                new_items[i] = (key_shrinkable, shrunk_value)
                shrinks.append(
                    Shrinkable({key.value: value.value for key, value in new_items})
                )

        return shrinks

