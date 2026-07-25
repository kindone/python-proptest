"""
Transform generators (map, filter, flat_map).
"""

from typing import Callable, TypeVar

from ..shrinker import Shrinkable
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
        # Generate first value (T-axis)
        first_shrinkable = self.generator.generate(rng)

        # Save RNG state after first generation for deterministic U regeneration
        # during shrinking — each T-shrink candidate regenerates U from this state.
        rng_state_after_first = rng.getstate()  # type: ignore[attr-defined]

        def make_second(first_val) -> Shrinkable[U]:  # T inferred from flat_map context
            """Regenerate U from T, restoring RNG to the post-T state."""
            rng.setstate(rng_state_after_first)  # type: ignore[attr-defined]
            return self.func(first_val).generate(rng)

        # Delegate to Shrinkable.flat_map which correctly implements:
        # - T-axis shrinks first (each carrying recursive flat_map shrinks via concat)
        # - U-axis shrinks appended after (concat, not and_then — fires at every node)
        # This also avoids the Python late-binding closure bug present in the old
        # hand-rolled approach.
        return first_shrinkable.flat_map(make_second)
