"""
Core generator interface and basic generators.

This module provides the fundamental Generator interface and basic generators
for common Python types.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Generic, List, Protocol, Set, Tuple, TypeVar

from .shrinker import Shrinkable
from .stream import Stream

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
        return MappedGenerator(self, func)

    def filter(self, predicate: Callable[[T], bool]) -> "Generator[T]":
        """Filter generated values using a predicate."""
        return FilteredGenerator(self, predicate)

    def flat_map(self, func: Callable[[T], "Generator[U]"]) -> "Generator[U]":
        """Generate a value, then use it to generate another value."""
        return FlatMappedGenerator(self, func)


class MappedGenerator(Generator[U]):
    """Generator that transforms values using a function."""

    def __init__(self, generator: Generator[T], func: Callable[[T], U]):
        self.generator = generator
        self.func = func

    def generate(self, rng: Random) -> Shrinkable[U]:
        shrinkable = self.generator.generate(rng)
        transformed_value = self.func(shrinkable.value)

        def shrink_func() -> Stream[Shrinkable[U]]:
            transformed_shrinks = [
                Shrinkable(self.func(s.value), lambda: s.shrinks())  # type: ignore
                for s in shrinkable.shrinks().to_list()
            ]
            return Stream.many(transformed_shrinks)

        return Shrinkable(transformed_value, shrink_func)


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
        for _ in range(self.max_attempts):
            shrinkable = self.generator.generate(rng)
            if self.predicate(shrinkable.value):
                # Create a new Shrinkable with filtered shrinking candidates
                filtered_shrinks = self._filter_shrinks(shrinkable)
                return Shrinkable(shrinkable.value, lambda: filtered_shrinks)
        raise ValueError(
            f"Could not generate value satisfying predicate after "
            f"{self.max_attempts} attempts"
        )

    def _filter_shrinks(self, shrinkable: Shrinkable[T]):
        """Filter shrinking candidates by predicate."""
        from python_proptest.core.stream import Stream

        def filtered_stream():
            original_stream = shrinkable.shrinks()
            filtered_candidates = []

            # Get all candidates from the original stream
            for candidate in original_stream:
                if self.predicate(candidate.value):
                    filtered_candidates.append(candidate)

            return Stream.many(filtered_candidates)

        return filtered_stream()


class FlatMappedGenerator(Generator[U]):
    """Generator that generates a value, then uses it to generate another value."""

    def __init__(self, generator: Generator[T], func: Callable[[T], Generator[U]]):
        self.generator = generator
        self.func = func

    def generate(self, rng: Random) -> Shrinkable[U]:
        shrinkable = self.generator.generate(rng)
        nested_generator = self.func(shrinkable.value)
        return nested_generator.generate(rng)


class Gen:
    """Namespace for built-in generators."""

    @staticmethod
    def int(min_value: int = -1000, max_value: int = 1000):
        """Generate random integers in the specified range."""
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
    def bool() -> "BoolGenerator":
        """Generate random booleans."""
        return BoolGenerator()

    @staticmethod
    def float(
        min_value: float = -1000.0, max_value: float = 1000.0
    ) -> "FloatGenerator":
        """Generate random floats in the specified range."""
        return FloatGenerator(min_value, max_value)

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
        return ConstructGenerator(Type, list(generators))

    @staticmethod
    def chain_tuple(tuple_gen, gen_factory):
        """Chain tuple generation with dependent value generation."""
        return ChainTupleGenerator(tuple_gen, gen_factory)

    @staticmethod
    def tuple(*generators):
        """Create a generator that generates tuples from multiple generators."""
        if not generators:
            raise ValueError("At least one generator must be provided")

        def generate(rng: Random) -> Shrinkable[tuple]:
            values = []
            shrinks = []
            for gen in generators:
                shrinkable = gen.generate(rng)
                values.append(shrinkable.value)
                shrinks.append(shrinkable)

            # Create shrinks for the tuple
            tuple_shrinks = []
            for i, shrink in enumerate(shrinks):
                for shr in shrink.shrinks().to_list():
                    new_values = values.copy()
                    new_values[i] = shr.value
                    tuple_shrinks.append(Shrinkable(tuple(new_values)))

            from python_proptest.core.stream import Stream

            return Shrinkable(tuple(values), lambda: Stream.many(tuple_shrinks))

        class TupleGenerator(Generator[tuple]):
            def generate(self, rng: Random) -> Shrinkable[tuple]:
                return generate(rng)

        return TupleGenerator()


class IntGenerator(Generator[int]):
    """Generator for integers."""

    def __init__(self, min_value: int, max_value: int):
        self.min_value = min_value
        self.max_value = max_value

    def generate(self, rng: Random) -> Shrinkable[int]:
        value = rng.randint(self.min_value, self.max_value)
        shrinks = self._generate_shrinks(value)
        from python_proptest.core.stream import Stream

        return Shrinkable(value, lambda: Stream.many(shrinks))

    def _generate_shrinks(self, value: int) -> List[Shrinkable[int]]:
        """Generate shrinking candidates for an integer."""
        shrinks = []

        # Shrink towards min_value (or zero if min_value <= 0)
        target = max(self.min_value, 0)
        if value > target:
            if target >= self.min_value and target <= self.max_value:
                shrinks.append(Shrinkable(target))
            if (
                value > target + 1
                and target + 1 >= self.min_value
                and target + 1 <= self.max_value
            ):
                shrinks.append(Shrinkable(target + 1))
        elif value < target:
            if target <= self.max_value and target >= self.min_value:
                shrinks.append(Shrinkable(target))
            if (
                value < target - 1
                and target - 1 <= self.max_value
                and target - 1 >= self.min_value
            ):
                shrinks.append(Shrinkable(target - 1))

        # Binary search shrinking towards min_value
        if value != self.min_value:
            # Try shrinking towards min_value
            if value > self.min_value:
                mid = (value + self.min_value) // 2
                if mid >= self.min_value and mid <= self.max_value and mid != value:
                    shrinks.append(Shrinkable(mid))

            # Try shrinking towards max_value (for negative values)
            if value < self.max_value:
                mid = (value + self.max_value) // 2
                if mid >= self.min_value and mid <= self.max_value and mid != value:
                    shrinks.append(Shrinkable(mid))

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

        from python_proptest.core.stream import Stream

        return Shrinkable(unique_list, lambda: Stream.many(shrinks))


class UnicodeCharGenerator(Generator[int]):
    """Generator for Unicode character codes avoiding surrogate pairs."""

    def generate(self, rng: Random) -> Shrinkable[int]:
        """Generate a Unicode character code avoiding surrogate pairs."""
        # Generate a random number in the range [1, 0xD7FF + (0x10FFFF - 0xE000 + 1)]
        # Then map it to avoid surrogate pairs (U+D800 to U+DFFF)
        max_range = 0xD7FF + (0x10FFFF - 0xE000 + 1)
        code = rng.randint(1, max_range)

        # Skip surrogate pair range D800-DFFF
        if code >= 0xD800:
            code += 0xE000 - 0xD800

        shrinks = self._generate_shrinks(code)
        from python_proptest.core.stream import Stream

        return Shrinkable(code, lambda: Stream.many(shrinks))

    def _generate_shrinks(self, value: int) -> List[Shrinkable[int]]:
        """Generate shrinking candidates for a Unicode character code."""
        shrinks = []

        # Shrink towards 1 (minimum valid Unicode)
        if value > 1:
            shrinks.append(Shrinkable(1))
            if value > 2:
                shrinks.append(Shrinkable(2))

        # Binary search shrinking
        if value > 1:
            mid = (value + 1) // 2
            if mid != value:
                shrinks.append(Shrinkable(mid))

        return shrinks


class StringGenerator(Generator[str]):
    """Generator for strings."""

    def __init__(self, min_length: int, max_length: int, charset: str):
        self.min_length = min_length
        self.max_length = max_length
        self.charset = self._get_charset(charset)

    def _get_charset(self, charset: str) -> str:
        """Convert charset specification to actual character set."""
        if charset == "ascii":
            # ASCII characters 0-127
            return "".join(chr(i) for i in range(128))
        elif charset == "printable_ascii":
            # Printable ASCII characters 32-126
            return "".join(chr(i) for i in range(32, 127))
        else:
            # Use the provided charset as-is
            return charset

    def generate(self, rng: Random) -> Shrinkable[str]:
        length = rng.randint(self.min_length, self.max_length)
        chars = [rng.choice(list(self.charset)) for _ in range(length)]
        value = "".join(chars)
        shrinks = self._generate_shrinks(value)
        from python_proptest.core.stream import Stream

        return Shrinkable(value, lambda: Stream.many(shrinks))

    def _generate_shrinks(self, value: str) -> List[Shrinkable[str]]:
        """Generate shrinking candidates for a string."""
        shrinks = []

        # Empty string
        if len(value) > 0:
            shrinks.append(Shrinkable(""))

        # Shorter strings
        if len(value) > 1:
            shrinks.append(Shrinkable(value[:-1]))  # Remove last character
            shrinks.append(Shrinkable(value[1:]))  # Remove first character

        # Single character strings
        if len(value) > 0:
            shrinks.append(Shrinkable(value[0]))  # First character only
            if len(value) > 1:
                shrinks.append(Shrinkable(value[-1]))  # Last character only

        return shrinks


class BoolGenerator(Generator[bool]):
    """Generator for booleans."""

    def generate(self, rng: Random) -> Shrinkable[bool]:
        value = rng.choice([True, False])
        shrinks = self._generate_shrinks(value)
        from python_proptest.core.stream import Stream

        return Shrinkable(value, lambda: Stream.many(shrinks))

    def _generate_shrinks(self, value: bool) -> List[Shrinkable[bool]]:
        """Generate shrinking candidates for a boolean."""
        if value:
            return [Shrinkable(False)]
        return []


class FloatGenerator(Generator[float]):
    """Generator for floats."""

    def __init__(self, min_value: float, max_value: float):
        self.min_value = min_value
        self.max_value = max_value

    def generate(self, rng: Random) -> Shrinkable[float]:
        value = rng.random() * (self.max_value - self.min_value) + self.min_value
        shrinks = self._generate_shrinks(value)
        from python_proptest.core.stream import Stream

        return Shrinkable(value, lambda: Stream.many(shrinks))

    def _generate_shrinks(self, value: float) -> List[Shrinkable[float]]:
        """Generate shrinking candidates for a float."""
        shrinks = []

        # Shrink towards zero
        if value > 0:
            shrinks.append(Shrinkable(0.0))
        elif value < 0:
            shrinks.append(Shrinkable(0.0))

        # Binary search shrinking
        if abs(value) > 1.0:
            shrinks.append(Shrinkable(value / 2))
            shrinks.append(Shrinkable(-value / 2))

        return shrinks


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
        from python_proptest.core.stream import Stream

        return Shrinkable(value, lambda: Stream.many(shrinks))

    def _generate_shrinks(
        self, elements: List[Shrinkable[T]]
    ) -> List[Shrinkable[List[T]]]:
        """Generate shrinking candidates for a list."""
        shrinks: List[Shrinkable[List[T]]] = []

        # Empty list
        if len(elements) > 0:
            shrinks.append(Shrinkable([]))

        # Shorter lists
        if len(elements) > 1:
            shrinks.append(
                Shrinkable([elem.value for elem in elements[:-1]])
            )  # Remove last
            shrinks.append(
                Shrinkable([elem.value for elem in elements[1:]])
            )  # Remove first

        # Lists with shrunk elements
        for i, elem in enumerate(elements):
            for shrunk_elem in elem.shrinks().to_list():
                new_elements = elements.copy()
                new_elements[i] = shrunk_elem
                shrinks.append(Shrinkable([e.value for e in new_elements]))

        return shrinks


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
        from python_proptest.core.stream import Stream

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


class OneOfGenerator(Generator[T]):
    """Generator that randomly chooses from multiple generators with weights."""

    def __init__(self, generators: List[Any]):
        if not generators:
            raise ValueError("At least one generator must be provided")
        self.weighted_generators = normalize_weighted_generators(generators)

    def generate(self, rng: Random) -> Shrinkable[T]:
        # Selection loop: repeatedly pick a generator index and check against its weight
        while True:
            dice = rng.randint(0, len(self.weighted_generators) - 1)
            weighted_gen = self.weighted_generators[dice]
            if rng.random() < weighted_gen.weight:
                return weighted_gen.generate(rng)


class ElementOfGenerator(Generator[T]):
    """Generator that randomly chooses from multiple values with optional weights."""

    def __init__(self, values: List[Any]):
        if not values:
            raise ValueError("At least one value must be provided")
        self.weighted_values = normalize_weighted_values(values)

    def generate(self, rng: Random) -> Shrinkable[T]:
        # Selection loop: repeatedly pick a value index and check against its weight
        while True:
            dice = rng.randint(0, len(self.weighted_values) - 1)
            weighted_value = self.weighted_values[dice]
            if rng.random() < weighted_value.weight:
                value = weighted_value.value
                # Generate shrinks by trying other values
                shrinks = [
                    Shrinkable(wv.value)
                    for wv in self.weighted_values
                    if wv.value != value
                ]
                from python_proptest.core.stream import Stream

                return Shrinkable(value, lambda: Stream.many(shrinks))


class JustGenerator(Generator[T]):
    """Generator that always returns the same value."""

    def __init__(self, value: T):
        self.value = value

    def generate(self, rng: Random) -> Shrinkable[T]:
        from python_proptest.core.stream import Stream

        return Shrinkable(self.value, lambda: Stream.empty())


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
        from python_proptest.core.stream import Stream

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


class UnicodeStringGenerator(Generator[str]):
    """Generator for Unicode strings."""

    def __init__(self, min_length: int, max_length: int):
        self.min_length = min_length
        self.max_length = max_length

    def generate(self, rng: Random) -> Shrinkable[str]:
        length = rng.randint(self.min_length, self.max_length)
        chars = []

        for _ in range(length):
            # Generate random Unicode codepoint (basic multilingual plane)
            codepoint = rng.randint(0, 0xFFFF)
            try:
                chars.append(chr(codepoint))
            except ValueError:
                # Skip invalid codepoints
                chars.append("?")

        value = "".join(chars)
        shrinks = self._generate_shrinks(value)
        from python_proptest.core.stream import Stream

        return Shrinkable(value, lambda: Stream.many(shrinks))

    def _generate_shrinks(self, value: str) -> List[Shrinkable[str]]:
        """Generate shrinking candidates for a Unicode string."""
        shrinks = []

        # Empty string
        if len(value) > 0:
            shrinks.append(Shrinkable(""))

        # Shorter strings
        if len(value) > 1:
            shrinks.append(Shrinkable(value[:-1]))  # Remove last character
            shrinks.append(Shrinkable(value[1:]))  # Remove first character

        # Single character strings
        if len(value) > 0:
            shrinks.append(Shrinkable(value[0]))  # First character only
            if len(value) > 1:
                shrinks.append(Shrinkable(value[-1]))  # Last character only

        return shrinks


class LazyGenerator(Generator[T]):
    """Generator that delays evaluation until generation."""

    def __init__(self, func: Callable[[], T]):
        self.func = func

    def generate(self, rng: Random) -> Shrinkable[T]:
        value = self.func()
        from python_proptest.core.stream import Stream

        return Shrinkable(value, lambda: Stream.empty())


class ConstructGenerator(Generator[Any]):
    """Generator that creates instances of a class."""

    def __init__(self, Type: type, generators: List[Generator[Any]]):
        self.Type = Type
        self.generators = generators

    def generate(self, rng: Random) -> Shrinkable[Any]:
        # Generate arguments
        args = []
        arg_shrinks = []

        for gen in self.generators:
            arg_shrinkable = gen.generate(rng)
            args.append(arg_shrinkable.value)
            arg_shrinks.append(arg_shrinkable)

        # Create instance
        instance = self.Type(*args)

        # Generate shrinks by shrinking arguments
        shrinks = []
        for i, arg_shrink in enumerate(arg_shrinks):
            for shrunk_arg in arg_shrink.shrinks().to_list():
                new_args = args.copy()
                new_args[i] = shrunk_arg.value
                shrinks.append(Shrinkable(self.Type(*new_args)))

        from python_proptest.core.stream import Stream

        return Shrinkable(instance, lambda: Stream.many(shrinks))


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

        from python_proptest.core.stream import Stream

        return Shrinkable(combined_value, lambda: Stream.many(shrinks))
