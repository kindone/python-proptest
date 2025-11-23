"""
Aggregate and accumulate generators for dependent sequences.
"""

from typing import Callable, List, TypeVar

from ..shrinker import Shrinkable
from ..stream import Stream
from .base import Generator, Random

T = TypeVar("T")


class AggregateGenerator(Generator[List[T]]):
    """Generator that creates a list where each element depends on the previous one.

    This generator takes an initial generator and a function that produces a new
    generator based on the previously generated value. The result is a list where
    each element depends on its predecessor.
    """

    def __init__(
        self,
        initial_gen: Generator[T],
        gen_factory: Callable[[T], Generator[T]],
        min_size: int,
        max_size: int,
    ):
        self.initial_gen = initial_gen
        self.gen_factory = gen_factory
        self.min_size = min_size
        self.max_size = max_size

    def generate(self, rng: Random) -> Shrinkable[List[T]]:
        # Generate the size
        size = rng.randint(self.min_size, self.max_size)

        if size == 0:
            return Shrinkable([], lambda: Stream.empty())

        # Generate the sequence
        shrinkables = []
        current_shrinkable = self.initial_gen.generate(rng)
        shrinkables.append(current_shrinkable)

        for _ in range(1, size):
            next_gen = self.gen_factory(current_shrinkable.value)
            current_shrinkable = next_gen.generate(rng)
            shrinkables.append(current_shrinkable)

        values = [shr.value for shr in shrinkables]

        def create_shrinks():
            shrinks = []

            # Shrink length towards min_size
            if len(shrinkables) > self.min_size:
                for new_size in range(self.min_size, len(shrinkables)):
                    shrunk_shrinkables = shrinkables[:new_size]
                    shrunk_values = [shr.value for shr in shrunk_shrinkables]
                    shrinks.append(Shrinkable(shrunk_values))

            # Shrink individual elements while maintaining dependencies
            for i in range(len(shrinkables)):
                for shrunk_elem in shrinkables[i].shrinks().to_list():
                    try:
                        # Regenerate subsequent elements based on shrunk value
                        new_shrinkables = shrinkables[:i] + [shrunk_elem]
                        current_value = shrunk_elem.value

                        for j in range(i + 1, len(shrinkables)):
                            next_gen = self.gen_factory(current_value)
                            next_shrinkable = next_gen.generate(rng)
                            new_shrinkables.append(next_shrinkable)
                            current_value = next_shrinkable.value

                        new_values = [shr.value for shr in new_shrinkables]
                        shrinks.append(Shrinkable(new_values))
                    except Exception:
                        # Skip if regeneration fails
                        continue  # nosec B112

            return Stream.many(shrinks)

        return Shrinkable(values, create_shrinks)


class AccumulateGenerator(Generator[T]):
    """Generator that produces a final value through successive dependent generations.

    This generator starts with an initial value and repeatedly applies a generator
    function that depends on the previous value. Only the final value after all
    steps is returned.
    """

    def __init__(
        self,
        initial_gen: Generator[T],
        gen_factory: Callable[[T], Generator[T]],
        min_size: int,
        max_size: int,
    ):
        self.initial_gen = initial_gen
        self.gen_factory = gen_factory
        self.min_size = min_size
        self.max_size = max_size

    def generate(self, rng: Random) -> Shrinkable[T]:
        # Generate the number of accumulation steps
        size = rng.randint(self.min_size, self.max_size)

        # Generate initial value
        current_shrinkable = self.initial_gen.generate(rng)

        # Accumulate through the steps
        for _ in range(size):
            next_gen = self.gen_factory(current_shrinkable.value)
            current_shrinkable = next_gen.generate(rng)

        final_value = current_shrinkable.value

        def create_shrinks():
            shrinks = []

            # Shrink by reducing number of steps
            if size > self.min_size:
                for new_size in range(self.min_size, size):
                    try:
                        # Regenerate with fewer steps
                        temp_shrinkable = self.initial_gen.generate(rng)
                        for _ in range(new_size):
                            temp_gen = self.gen_factory(temp_shrinkable.value)
                            temp_shrinkable = temp_gen.generate(rng)
                        shrinks.append(Shrinkable(temp_shrinkable.value))
                    except Exception:
                        continue  # nosec B112

            # Shrink the final value itself
            for shrunk in current_shrinkable.shrinks().to_list():
                shrinks.append(Shrinkable(shrunk.value))

            return Stream.many(shrinks)

        return Shrinkable(final_value, create_shrinks)
