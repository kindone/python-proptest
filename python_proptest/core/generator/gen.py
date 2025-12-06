"""
Gen class with static factory methods for creating generators.
"""

import sys
from typing import Any, Callable, List, Optional, TypeVar

from ..combinator import (
    ConstructGenerator,
    ElementOfGenerator,
    JustGenerator,
    LazyGenerator,
    OneOfGenerator,
)
from ..shrinker import Shrinkable
from .base import Generator, Random, Weighted, WeightedValue
from .bool import BoolGenerator
from .chain import ChainGenerator
from .dict import DictGenerator
from .floating import FloatGenerator
from .integral import IntGenerator, UnicodeCharGenerator
from .list import ListGenerator, UniqueListGenerator
from .set import SetGenerator
from .string import StringGenerator, UnicodeStringGenerator

T = TypeVar("T")


class Gen:
    """Namespace for built-in generators."""

    @staticmethod
    def int(min_value: Optional[int] = None, max_value: Optional[int] = None):
        """Generate random integers in the specified range.

        If min_value or max_value are not specified, uses the full integer range
        (from -sys.maxsize - 1 to sys.maxsize).
        """
        if min_value is None:
            min_value = -sys.maxsize - 1
        if max_value is None:
            max_value = sys.maxsize
        return IntGenerator(min_value, max_value)

    @staticmethod
    def str(
        min_length: int = 0,
        max_length: int = 20,
        charset: str = "abcdefghijklmnopqrstuvwxyz",
    ) -> "StringGenerator":
        """Generate random strings with the specified constraints."""
        return StringGenerator(min_length, max_length, charset)

    @staticmethod
    def bool(true_prob: float = 0.5) -> "BoolGenerator":
        """Generate random booleans with specified probability of True.

        Args:
            true_prob: Probability of generating True (0.0 to 1.0, default: 0.5)
        """
        if not 0.0 <= true_prob <= 1.0:
            raise ValueError("true_prob must be between 0.0 and 1.0")
        return BoolGenerator(true_prob)

    @staticmethod
    def float(
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        nan_prob: float = 0.0,
        posinf_prob: float = 0.0,
        neginf_prob: float = 0.0,
    ) -> "FloatGenerator":
        """Generate random floats in the specified range.

        By default, generates only finite values. Can optionally generate
        special values (NaN, +inf, -inf) with specified probabilities.

        Args:
            min_value: Minimum float value to generate. If not specified, uses
                -sys.float_info.max (full finite float range).
            max_value: Maximum float value to generate. If not specified, uses
                sys.float_info.max (full finite float range).
            nan_prob: Probability of generating NaN (0.0 to 1.0, default: 0.0).
            posinf_prob: Probability of generating +inf (0.0 to 1.0, default: 0.0).
            neginf_prob: Probability of generating -inf (0.0 to 1.0, default: 0.0).

        The sum of nan_prob, posinf_prob, and neginf_prob must be <= 1.0.
        The remaining probability (1.0 - sum) is used for finite values.

        Examples:
            # Finite values only (default)
            Gen.float()

            # 1% NaN, 99% finite
            Gen.float(nan_prob=0.01)

            # 1% each inf, 98% finite
            Gen.float(posinf_prob=0.01, neginf_prob=0.01)

            # Custom mix
            Gen.float(nan_prob=0.1, posinf_prob=0.05, neginf_prob=0.05)
        """
        if min_value is None:
            min_value = -sys.float_info.max
        if max_value is None:
            max_value = sys.float_info.max
        return FloatGenerator(min_value, max_value, nan_prob, posinf_prob, neginf_prob)

    @staticmethod
    def list(
        element_generator: "Generator", min_length: int = 0, max_length: int = 10
    ) -> "ListGenerator":
        """Generate random lists of elements from the given generator."""
        return ListGenerator(element_generator, min_length, max_length)

    @staticmethod
    def unique_list(
        element_generator: "Generator", min_length: int = 0, max_length: int = 10
    ) -> "UniqueListGenerator":
        """Generate random lists with unique elements from the given generator."""
        return UniqueListGenerator(element_generator, min_length, max_length)

    @staticmethod
    def dict(
        key_generator: "Generator",
        value_generator: "Generator",
        min_size: int = 0,
        max_size: int = 10,
    ) -> "DictGenerator":
        """Generate random dictionaries."""
        return DictGenerator(key_generator, value_generator, min_size, max_size)

    @staticmethod
    def one_of(*generators):
        """Randomly choose from multiple generators with optional weights."""
        return OneOfGenerator(list(generators))

    @staticmethod
    def element_of(*values):
        """Randomly choose from multiple values with optional weights."""
        if not values:
            raise ValueError("At least one value must be provided")
        return ElementOfGenerator(list(values))

    @staticmethod
    def just(value):
        """Always generate the same value."""
        return JustGenerator(value)

    @staticmethod
    def weighted_gen(generator: "Generator", weight: float) -> "Weighted":
        """Wraps a generator with a weight for Gen.one_of."""
        return Weighted(generator, weight)

    @staticmethod
    def weighted_value(value: T, weight: float) -> "WeightedValue":
        """Wraps a value with a weight for Gen.element_of."""
        return WeightedValue(value, weight)

    @staticmethod
    def set(
        element_generator: "Generator", min_size: int = 0, max_size: int = 10
    ) -> "SetGenerator":
        """Generate random sets of elements from the given generator."""
        return SetGenerator(element_generator, min_size, max_size)

    @staticmethod
    def unicode_string(
        min_length: int = 0, max_length: int = 20
    ) -> "UnicodeStringGenerator":
        """Generate random Unicode strings with the specified constraints."""
        return UnicodeStringGenerator(min_length, max_length)

    @staticmethod
    def ascii_string(min_length: int = 0, max_length: int = 20) -> "StringGenerator":
        """Generate random ASCII strings (characters 0-127)."""
        return StringGenerator(min_length, max_length, "ascii")

    @staticmethod
    def printable_ascii_string(
        min_length: int = 0, max_length: int = 20
    ) -> "StringGenerator":
        """Generate random printable ASCII strings (characters 32-126)."""
        return StringGenerator(min_length, max_length, "printable_ascii")

    @staticmethod
    def ascii_char() -> "IntGenerator":
        """Generate single ASCII character codes (0-127)."""
        return IntGenerator(0, 127)

    @staticmethod
    def unicode_char() -> "UnicodeCharGenerator":
        """Generate single Unicode character codes (avoiding surrogate pairs)."""
        return UnicodeCharGenerator()

    @staticmethod
    def printable_ascii_char() -> "IntGenerator":
        """Generate single printable ASCII character codes (32-126)."""
        return IntGenerator(32, 126)

    @staticmethod
    def interval(min_value: int, max_value: int) -> "IntGenerator":
        """Generate random integers in the specified range (inclusive)."""
        return IntGenerator(min_value, max_value)

    @staticmethod
    def in_range(min_value: int, max_value: int) -> "IntGenerator":
        """Generate random integers in range [min_value, max_value) (exclusive)."""
        min_val: int = min_value
        max_val: int = max_value
        if min_val >= max_val:
            raise ValueError(f"invalid range: min ({min_val}) >= max ({max_val})")
        return IntGenerator(min_val, max_val - 1)

    @staticmethod
    def integers(min_value: int, max_value: int) -> "IntGenerator":
        """Alias for interval for compatibility."""
        return IntGenerator(min_value, max_value)

    @staticmethod
    def lazy(func):
        """Create a generator that delays evaluation until generation."""
        return LazyGenerator(func)

    @staticmethod
    def construct(Type: type, *generators):
        """Create a generator for instances of a class."""
        return ConstructGenerator(Type, *generators)

    @staticmethod
    def chain(
        base_gen: "Generator", gen_factory: Callable[[Any], "Generator[Any]"]
    ) -> "ChainGenerator":
        """Chain generators to create dependent tuple generation.

        Takes a generator and a function that produces a new generator based on the
        generated value. The result is a tuple with the original value(s) plus
        the dependent value.

        Args:
            base_gen: Generator for the base value(s) - can be single value or tuple
            gen_factory: Function that takes the base value and returns a Generator

        Returns:
            Generator that produces tuples with dependent values

        Examples:
            # Simple dependency: month -> valid day
            date_gen = Gen.chain(
                Gen.int(1, 12),  # month
                lambda month: Gen.int(1, days_in_month(month))  # valid day for month
            )
            # Result: Generator[Tuple[int, int]] for (month, day)

            # Chain multiple dependencies
            datetime_gen = Gen.chain(
                date_gen,
                lambda date_tuple: Gen.int(0, 23)  # hour
            )
            # Result: Generator[Tuple[int, int, int]] for (month, day, hour)

            # Complex dependency with validation
            rect_gen = Gen.chain(
                Gen.int(1, 100),  # width
                lambda width: Gen.int(1, 200 // width)  # height constrained by width
            )
        """
        return ChainGenerator(base_gen, gen_factory)

    @staticmethod
    def chain_tuple(tuple_gen, gen_factory):
        """Chain tuple generation with dependent value generation.

        Deprecated: Use Gen.chain() instead for unified API.
        """
        return ChainGenerator(tuple_gen, gen_factory)

    @staticmethod
    def aggregate(
        initial_gen: "Generator[T]",
        gen_factory: Callable[[T], "Generator[T]"],
        min_size: int = 0,
        max_size: int = 10,
    ) -> "Generator[List[T]]":
        """Generate a list where each element depends on the previous one.

        Creates a list of dependent values starting with a value from initial_gen,
        then repeatedly applying gen_factory to generate the next value based on
        the previous one. The entire list is returned.

        Args:
            initial_gen: Generator for the first element
            gen_factory: Function that takes a value and returns a Generator
                        for the next value
            min_size: Minimum number of elements (default: 0)
            max_size: Maximum number of elements (default: 10)

        Returns:
            Generator that produces List[T] with dependent elements

        Examples:
            # Generate increasing sequence
            increasing_gen = Gen.aggregate(
                Gen.int(0, 10),
                lambda n: Gen.int(n, n + 5),
                min_size=3, max_size=10
            )
            # Result: [5, 8, 12, 15, ...] - each element >= previous

            # Random walk with boundaries
            walk_gen = Gen.aggregate(
                Gen.int(50, 50),  # Start at 50
                lambda pos: Gen.int(max(0, pos - 10), min(100, pos + 10)),
                min_size=5, max_size=20
            )
            # Result: [50, 45, 52, 48, ...] - bounded random walk
        """
        from .aggregate import AggregateGenerator

        return AggregateGenerator(initial_gen, gen_factory, min_size, max_size)

    @staticmethod
    def accumulate(
        initial_gen: "Generator[T]",
        gen_factory: Callable[[T], "Generator[T]"],
        min_size: int = 0,
        max_size: int = 10,
    ) -> "Generator[T]":
        """Generate a final value through successive dependent generations.

        Like aggregate, but returns only the final value after all accumulation
        steps instead of the entire list. Useful for simulating processes where
        only the end result matters.

        Args:
            initial_gen: Generator for the initial value
            gen_factory: Function that takes a value and returns a Generator
                        for the next value
            min_size: Minimum number of accumulation steps (default: 0)
            max_size: Maximum number of accumulation steps (default: 10)

        Returns:
            Generator that produces a single T (final accumulated value)

        Examples:
            # Random walk - final position only
            final_pos_gen = Gen.accumulate(
                Gen.int(0, 100),
                lambda pos: Gen.int(max(0, pos - 5), min(100, pos + 5)),
                min_size=10, max_size=50
            )
            # Result: Single int (position after N steps)

            # Compound growth - final amount only
            final_amount_gen = Gen.accumulate(
                Gen.float(100.0, 1000.0),
                lambda amount: Gen.float(amount * 1.01, amount * 1.1),
                min_size=5, max_size=20
            )
            # Result: Single float (final amount after compounding)
        """
        from .aggregate import AccumulateGenerator

        return AccumulateGenerator(initial_gen, gen_factory, min_size, max_size)

    @staticmethod
    def tuple(*generators):
        """Create a generator that generates tuples from multiple generators.

        Uses shrink_tuple for recursive shrinking of all elements, matching cppproptest.
        """
        if not generators:
            raise ValueError("At least one generator must be provided")

        from ..shrinker.tuple import shrink_tuple

        class TupleGenerator(Generator[tuple]):
            def generate(self, rng: Random) -> Shrinkable[tuple]:
                # Generate shrinkables for each element
                shrinkables = []
                for gen in generators:
                    shrinkable = gen.generate(rng)
                    shrinkables.append(shrinkable)

                # Use shrink_tuple to create a shrinkable tuple with recursive shrinking
                return shrink_tuple(shrinkables)

        return TupleGenerator()
