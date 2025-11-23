"""
Base Generator interface and common utilities.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, List, Optional, Protocol, TypeVar

from ..shrinker import Shrinkable

T = TypeVar("T")
U = TypeVar("U")


class WeightedValue(Generic[T]):
    """Represents a value with an associated weight for weighted selection."""

    def __init__(self, value: T, weight: float):
        self.value = value
        self.weight = weight


class Weighted(Generic[T]):
    """Wraps a Generator with an associated weight for weighted selection."""

    def __init__(self, generator: "Generator[T]", weight: float):
        self.generator = generator
        self.weight = weight

    def generate(self, rng: "Random") -> "Shrinkable[T]":
        """Generate a value using the wrapped generator."""
        return self.generator.generate(rng)

    def map(self, transformer: Callable[[T], U]) -> "Generator[U]":
        """Apply a transformation to the wrapped generator."""
        return self.generator.map(transformer)

    def filter(self, predicate: Callable[[T], bool]) -> "Generator[T]":
        """Filter the wrapped generator."""
        return self.generator.filter(predicate)

    def flat_map(self, gen_factory: Callable[[T], "Generator[U]"]) -> "Generator[U]":
        """Apply flat_map to the wrapped generator."""
        return self.generator.flat_map(gen_factory)


class Random(Protocol):
    """Protocol for random number generators."""

    def random(self) -> float:
        """Generate a random float in [0.0, 1.0)."""
        ...

    def randint(self, a: int, b: int) -> int:
        """Generate a random integer in [a, b]."""
        ...

    def randrange(self, start: int, stop: Optional[int] = None, step: int = 1) -> int:
        """Generate a random integer in the range."""
        ...

    def choice(self, seq: List[T]) -> T:
        """Choose a random element from sequence."""
        ...


def is_weighted_value(element: Any) -> bool:
    """Type check to determine if an element is weighted."""
    return isinstance(element, WeightedValue)


def is_weighted_generator(gen: Any) -> bool:
    """Type check to determine if a generator is weighted."""
    return isinstance(gen, Weighted)


def normalize_weighted_values(values: List[Any]) -> List[WeightedValue]:
    """Normalize weights so they sum to 1.0, handling mixed weighted/unweighted."""
    if not values:
        raise ValueError("At least one value must be provided")

    sum_weight = 0.0
    num_unassigned = 0

    # First pass: collect weighted values and count unweighted ones
    weighted_values = []
    for raw_or_weighted in values:
        if is_weighted_value(raw_or_weighted):
            weighted = raw_or_weighted
            sum_weight += weighted.weight
            weighted_values.append(weighted)
        else:
            num_unassigned += 1
            # Temporarily assign 0 weight to unweighted values
            weighted_values.append(WeightedValue(raw_or_weighted, 0.0))

    # Validate the sum of explicitly assigned weights
    if sum_weight < 0.0 or sum_weight > 1.0:
        raise ValueError(
            "invalid weights: sum must be between 0.0 (exclusive) and 1.0 (inclusive)"
        )

    # Distribute remaining probability mass among unweighted values
    if num_unassigned > 0:
        rest = 1.0 - sum_weight
        if rest <= 0.0:
            raise ValueError(
                "invalid weights: rest of weights must be greater than 0.0"
            )

        per_unassigned = rest / num_unassigned
        weighted_values = [
            WeightedValue(wv.value, per_unassigned) if wv.weight == 0.0 else wv
            for wv in weighted_values
        ]

    return weighted_values


def normalize_weighted_generators(generators: List[Any]) -> List[Weighted]:
    """Normalize weights so they sum to 1.0, handling mixed weighted/unweighted."""
    if not generators:
        raise ValueError("At least one generator must be provided")

    sum_weight = 0.0
    num_unassigned = 0

    # First pass: collect weighted generators and count unweighted ones
    weighted_generators = []
    for raw_or_weighted in generators:
        if is_weighted_generator(raw_or_weighted):
            weighted = raw_or_weighted
            sum_weight += weighted.weight
            weighted_generators.append(weighted)
        else:
            num_unassigned += 1
            # Temporarily assign 0 weight to unweighted generators
            weighted_generators.append(Weighted(raw_or_weighted, 0.0))

    # Validate the sum of explicitly assigned weights
    if sum_weight < 0.0 or sum_weight > 1.0:
        raise ValueError(
            "invalid weights: sum must be between 0.0 (exclusive) and 1.0 (inclusive)"
        )

    # Distribute remaining probability mass among unweighted generators
    if num_unassigned > 0:
        rest = 1.0 - sum_weight
        if rest <= 0.0:
            raise ValueError(
                "invalid weights: rest of weights must be greater than 0.0"
            )

        per_unassigned = rest / num_unassigned
        weighted_generators = [
            Weighted(wg.generator, per_unassigned) if wg.weight == 0.0 else wg
            for wg in weighted_generators
        ]

    return weighted_generators


class Generator(ABC, Generic[T]):
    """Abstract base class for generators."""

    @abstractmethod
    def generate(self, rng: Random) -> Shrinkable[T]:
        """Generate a value and its shrinking candidates."""
        pass

    def map(self, func: Callable[[T], U]) -> "Generator[U]":
        """Transform generated values using a function."""
        from .transform import MappedGenerator

        return MappedGenerator(self, func)

    def filter(self, predicate: Callable[[T], bool]) -> "Generator[T]":
        """Filter generated values using a predicate."""
        from .transform import FilteredGenerator

        return FilteredGenerator(self, predicate)

    def flat_map(self, func: Callable[[T], "Generator[U]"]) -> "Generator[U]":
        """Generate a value, then use it to generate another value."""
        from .transform import FlatMappedGenerator

        return FlatMappedGenerator(self, func)

    def chain(self, gen_factory: Callable[[T], "Generator[U]"]) -> "Generator[tuple]":
        """Chain this generator with a dependent generator to create tuples."""
        from .chain import ChainGenerator

        return ChainGenerator(self, gen_factory)

    def aggregate(
        self,
        gen_factory: Callable[[T], "Generator[T]"],
        min_size: int = 0,
        max_size: int = 10,
    ) -> "Generator[List[T]]":
        """Create a list where each element depends on the previous one."""
        from .aggregate import AggregateGenerator

        return AggregateGenerator(self, gen_factory, min_size, max_size)

    def accumulate(
        self,
        gen_factory: Callable[[T], "Generator[T]"],
        min_size: int = 0,
        max_size: int = 10,
    ) -> "Generator[T]":
        """Generate a final value through successive dependent generations."""
        from .aggregate import AccumulateGenerator

        return AccumulateGenerator(self, gen_factory, min_size, max_size)
