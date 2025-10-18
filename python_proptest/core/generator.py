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
                return shrinkable
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
        """Randomly choose from multiple generators."""
        return OneOfGenerator(list(generators))

    @staticmethod
    def element_of(*values):
        """Randomly choose from multiple values."""
        if not values:
            raise ValueError("At least one value must be provided")
        return ElementOfGenerator(list(values))

    @staticmethod
    def just(value):
        """Always generate the same value."""
        return JustGenerator(value)

    @staticmethod
    def weighted_value(generator: "Generator", weight: float) -> "Generator":
        """Create a weighted generator (for compatibility with stateful tests)."""
        return generator

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
    def interval(min_value: int, max_value: int) -> "IntGenerator":
        """Generate random integers in the specified range (inclusive)."""
        return IntGenerator(min_value, max_value)

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

        # Shrink towards zero
        if value > 0:
            shrinks.append(Shrinkable(0))
            if value > 1:
                shrinks.append(Shrinkable(1))
        elif value < 0:
            shrinks.append(Shrinkable(0))
            if value < -1:
                shrinks.append(Shrinkable(-1))

        # Binary search shrinking
        if abs(value) > 1:
            shrinks.append(Shrinkable(value // 2))
            shrinks.append(Shrinkable(-value // 2))

        return shrinks


class StringGenerator(Generator[str]):
    """Generator for strings."""

    def __init__(self, min_length: int, max_length: int, charset: str):
        self.min_length = min_length
        self.max_length = max_length
        self.charset = charset

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
    """Generator that randomly chooses from multiple generators."""

    def __init__(self, generators: List[Generator[T]]):
        if not generators:
            raise ValueError("At least one generator must be provided")
        self.generators = generators

    def generate(self, rng: Random) -> Shrinkable[T]:
        generator = rng.choice(self.generators)
        return generator.generate(rng)


class ElementOfGenerator(Generator[T]):
    """Generator that randomly chooses from multiple values."""

    def __init__(self, values: List[T]):
        if not values:
            raise ValueError("At least one value must be provided")
        self.values = values

    def generate(self, rng: Random) -> Shrinkable[T]:
        value = rng.choice(self.values)
        # Generate shrinks by trying other values
        shrinks = [Shrinkable(v) for v in self.values if v != value]
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
