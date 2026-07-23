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

        # Save RNG state after base generation for deterministic dependent
        # regeneration during shrinking.
        rng_state_after_base = rng.getstate()  # type: ignore[attr-defined]

        def make_combined(base_val: Any) -> Shrinkable[tuple]:
            """Regenerate the combined tuple from a (possibly shrunk) base value."""
            bt = base_val if isinstance(base_val, tuple) else (base_val,)
            rng.setstate(rng_state_after_base)  # type: ignore[attr-defined]
            dep_gen = self.gen_factory(base_val)
            dep_shrinkable = dep_gen.generate(rng)
            # Map the dependent shrinkable into a combined-tuple shrinkable so that
            # U-axis shrinks (dep value) are preserved in the result.
            return dep_shrinkable.map(lambda dep_val: bt + (dep_val,))

        # Delegate to Shrinkable.flat_map which correctly implements:
        # - Base (T) axis shrinks first, each carrying recursive flat_map shrinks
        # - Dependent (U) axis shrinks appended via concat (fires at every node)
        return base_shrinkable.flat_map(make_combined)
