"""
Transform generators (map, filter, flat_map).
"""

from typing import Callable, TypeVar

from ..shrinker import Shrinkable
from ..stream import Stream
from .base import Generator, Random

T = TypeVar("T")
U = TypeVar("U")


class MappedGenerator(Generator[U]):
    """Generator that transforms values using a function."""

    def __init__(self, generator: Generator[T], func: Callable[[T], U]):
        self.generator = generator
        self.func = func

    def generate(self, rng: Random) -> Shrinkable[U]:
        shrinkable = self.generator.generate(rng)
        return shrinkable.map(self.func)


class FilteredGenerator(Generator[T]):
    """Generator that filters values using a predicate."""

    def __init__(
        self,
        generator: Generator[T],
        predicate: Callable[[T], bool],
        max_attempts: int = 100,
    ):
        self.generator = generator
        self.predicate = predicate
        self.max_attempts = max_attempts

    def generate(self, rng: Random) -> Shrinkable[T]:
        for attempt in range(self.max_attempts):
            shrinkable = self.generator.generate(rng)
            value = shrinkable.value
            predicate_result = self.predicate(value)
            if predicate_result:
                filtered = shrinkable.filter(self.predicate)
                return filtered
        raise ValueError(
            f"Could not generate value satisfying predicate after "
            f"{self.max_attempts} attempts"
        )


class FlatMappedGenerator(Generator[U]):
    """Generator that generates a value, then uses it to generate another value."""

    def __init__(self, generator: Generator[T], func: Callable[[T], Generator[U]]):
        self.generator = generator
        self.func = func

    def generate(self, rng: Random) -> Shrinkable[U]:
        # Generate first value
        first_shrinkable = self.generator.generate(rng)

        # Save RNG state after first generation for deterministic regeneration
        rng_state_after_first = rng.getstate()  # type: ignore[attr-defined]

        # Generate second value
        second_generator = self.func(first_shrinkable.value)
        second_shrinkable = second_generator.generate(rng)

        def shrink_func() -> Stream[Shrinkable[U]]:
            # Shrink the second value first (keeping first fixed)
            second_shrinks = [
                Shrinkable(s.value, lambda: s.shrinks())
                for s in second_shrinkable.shrinks().to_list()
            ]

            # Then shrink the first value and regenerate the second
            # IMPORTANT: Restore RNG state to ensure deterministic regeneration
            original_rng_state = rng.getstate()  # type: ignore[attr-defined]
            first_shrinks = []
            try:
                for first_shrink in first_shrinkable.shrinks().to_list():
                    # Restore RNG state to what it was after first generation
                    rng.setstate(rng_state_after_first)  # type: ignore[attr-defined]
                    new_second_gen = self.func(first_shrink.value)
                    new_second_shrink = new_second_gen.generate(rng)
                    first_shrinks.append(new_second_shrink)
            finally:
                # Restore original RNG state
                rng.setstate(original_rng_state)  # type: ignore[attr-defined]

            return Stream.many(second_shrinks + first_shrinks)

        return Shrinkable(second_shrinkable.value, shrink_func)
