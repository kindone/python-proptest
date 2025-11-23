"""
Chain generators for dependent value generation.
"""

from typing import Any, Callable, TypeVar

from ..shrinker import Shrinkable
from ..stream import Stream
from .base import Generator, Random

T = TypeVar("T")


class ChainTupleGenerator(Generator[tuple]):
    """Generator that chains tuple generation with dependent value generation."""

    def __init__(
        self,
        tuple_gen: Generator[tuple],
        gen_factory: Callable[[tuple], Generator[Any]],
    ):
        self.tuple_gen = tuple_gen
        self.gen_factory = gen_factory

    def generate(self, rng: Random) -> Shrinkable[tuple]:
        # Generate the initial tuple
        tuple_shrinkable = self.tuple_gen.generate(rng)

        # Generate the dependent value
        dependent_gen = self.gen_factory(tuple_shrinkable.value)
        dependent_shrinkable = dependent_gen.generate(rng)

        # Combine into new tuple
        combined_value = tuple_shrinkable.value + (dependent_shrinkable.value,)

        # Generate shrinks
        shrinks = []

        # Shrinks from tuple generation
        for shrunk_tuple in tuple_shrinkable.shrinks().to_list():
            new_dependent_gen = self.gen_factory(shrunk_tuple.value)
            new_dependent_shrinkable = new_dependent_gen.generate(rng)
            shrinks.append(
                Shrinkable(shrunk_tuple.value + (new_dependent_shrinkable.value,))
            )

        # Shrinks from dependent value generation
        for shrunk_dependent in dependent_shrinkable.shrinks().to_list():
            shrinks.append(
                Shrinkable(tuple_shrinkable.value + (shrunk_dependent.value,))
            )

        return Shrinkable(combined_value, lambda: Stream.many(shrinks))


class ChainGenerator(Generator[tuple]):
    """Generator that chains tuple generation with dependent value generation.

    This generator takes a generator and a function that produces a new generator
    based on the generated value(s). The result is a tuple with the original value(s)
    plus one additional element that depends on the previous elements.
    """

    def __init__(
        self,
        base_gen: Generator,
        gen_factory: Callable[[Any], Generator[Any]],
    ):
        self.base_gen = base_gen
        self.gen_factory = gen_factory

    def generate(self, rng: Random) -> Shrinkable[tuple]:
        # Generate the base value(s)
        base_shrinkable = self.base_gen.generate(rng)
        base_value = base_shrinkable.value

        # Normalize to tuple if it's not already
        if isinstance(base_value, tuple):
            base_tuple = base_value
        else:
            base_tuple = (base_value,)

        # Generate the dependent value
        dependent_gen = self.gen_factory(base_value)
        dependent_shrinkable = dependent_gen.generate(rng)

        # Combine into new tuple
        combined_value = base_tuple + (dependent_shrinkable.value,)

        def create_shrinks():
            shrinks = []

            # Shrinks from base generation (keeping dependent value consistent)
            for shrunk_base in base_shrinkable.shrinks().to_list():
                shrunk_base_value = shrunk_base.value
                # Normalize to tuple
                if isinstance(shrunk_base_value, tuple):
                    shrunk_base_tuple = shrunk_base_value
                else:
                    shrunk_base_tuple = (shrunk_base_value,)

                try:
                    # Generate new dependent value for the shrunk base
                    new_dependent_gen = self.gen_factory(shrunk_base_value)
                    new_dependent_shrinkable = new_dependent_gen.generate(rng)
                    new_combined = shrunk_base_tuple + (new_dependent_shrinkable.value,)

                    # Recursively create shrinkable with proper shrinks
                    shrinks.append(
                        Shrinkable(
                            new_combined,
                            lambda: self._create_dependent_shrinks(
                                shrunk_base, new_dependent_shrinkable, rng
                            ),
                        )
                    )
                except Exception:
                    # Skip if dependent generation fails for shrunk value
                    continue  # nosec B112

            # Shrinks from dependent value generation (keeping base value fixed)
            for shrunk_dependent in dependent_shrinkable.shrinks().to_list():
                new_combined = base_tuple + (shrunk_dependent.value,)
                shrinks.append(
                    Shrinkable(
                        new_combined,
                        lambda: self._create_base_shrinks(
                            base_shrinkable, shrunk_dependent, rng
                        ),
                    )
                )

            return Stream.many(shrinks)

        return Shrinkable(combined_value, create_shrinks)

    def _create_dependent_shrinks(self, base_shrinkable, dependent_shrinkable, rng):
        """Create shrinks for when we've shrunk the base and regenerated dependent."""
        shrinks = []

        base_value = base_shrinkable.value
        base_tuple = base_value if isinstance(base_value, tuple) else (base_value,)

        # Only shrink the dependent part further
        for shrunk_dependent in dependent_shrinkable.shrinks().to_list():
            shrinks.append(Shrinkable(base_tuple + (shrunk_dependent.value,)))

        return Stream.many(shrinks)

    def _create_base_shrinks(self, base_shrinkable, dependent_shrinkable, rng):
        """Create shrinks for when we've kept base and shrunk dependent."""
        return Stream.empty()  # No further shrinks needed for this path
