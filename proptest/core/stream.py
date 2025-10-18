"""
Stream/LazyStream functionality for lazy evaluation.

This module provides the Stream class for representing lazy sequences,
which is used for efficient shrinking candidate generation.
"""

from typing import Any, Callable, Generic, Iterator, List, Optional, TypeVar

T = TypeVar("T")


class Stream(Generic[T]):
    """A lazy stream of values."""

    def __init__(
        self, head: Optional[T] = None, tail: Optional[Callable[[], "Stream[T]"]] = None
    ):
        self._head = head
        self._tail = tail
        self._evaluated = head is not None

    @classmethod
    def empty(cls) -> "Stream[T]":
        """Create an empty stream."""
        return cls()

    @classmethod
    def one(cls, value: T) -> "Stream[T]":
        """Create a stream with a single value."""
        return cls(head=value)

    @classmethod
    def two(cls, value1: T, value2: T) -> "Stream[T]":
        """Create a stream with two values."""
        return cls(head=value1, tail=lambda: cls(head=value2))

    @classmethod
    def three(cls, value1: T, value2: T, value3: T) -> "Stream[T]":
        """Create a stream with three values."""
        return cls(
            head=value1, tail=lambda: cls(head=value2, tail=lambda: cls(head=value3))
        )

    @classmethod
    def many(cls, values: List[T]) -> "Stream[T]":
        """Create a stream from a list of values."""
        if not values:
            return cls.empty()

        def make_stream(index: int = 0) -> "Stream[T]":
            if index >= len(values):
                return cls.empty()
            return cls(head=values[index], tail=lambda: make_stream(index + 1))

        return make_stream()

    def is_empty(self) -> bool:
        """Check if the stream is empty."""
        return self._head is None and self._tail is None

    def head(self) -> Optional[T]:
        """Get the first element of the stream."""
        return self._head

    def tail(self) -> "Stream[T]":
        """Get the rest of the stream."""
        if self._tail is None:
            return Stream.empty()
        return self._tail()

    def concat(self, other: "Stream[T]") -> "Stream[T]":
        """Concatenate this stream with another stream."""
        if self.is_empty():
            return other

        def concat_tail() -> "Stream[T]":
            return self.tail().concat(other)

        return Stream(self._head, concat_tail)

    def filter(self, predicate: Callable[[T], bool]) -> "Stream[T]":
        """Filter the stream using a predicate."""
        if self.is_empty():
            return Stream.empty()

        def filter_tail() -> "Stream[T]":
            return self.tail().filter(predicate)

        if self._head is not None and predicate(self._head):
            return Stream(self._head, filter_tail)
        else:
            return filter_tail()

    def map(self, func: Callable[[T], Any]) -> "Stream[Any]":
        """Map a function over the stream."""
        if self.is_empty():
            return Stream.empty()

        def map_tail() -> "Stream[Any]":
            return self.tail().map(func)

        if self._head is not None:
            return Stream(func(self._head), map_tail)
        else:
            return Stream.empty()

    def take(self, n: int) -> "Stream[T]":
        """Take the first n elements from the stream."""
        if n <= 0 or self.is_empty():
            return Stream.empty()

        def take_tail() -> "Stream[T]":
            return self.tail().take(n - 1)

        return Stream(self._head, take_tail)

    def to_list(self) -> List[T]:
        """Convert the stream to a list."""
        result = []
        current = self
        while not current.is_empty():
            head_val = current.head()
            if head_val is not None:
                result.append(head_val)
            current = current.tail()
        return result

    def __iter__(self) -> Iterator[T]:
        """Make the stream iterable."""
        current = self
        while not current.is_empty():
            head_val = current.head()
            if head_val is not None:
                yield head_val
            current = current.tail()

    def __repr__(self) -> str:
        """String representation of the stream."""
        if self.is_empty():
            return "Stream()"

        # Take first 10 elements for display
        elements = list(self.take(10))
        total_elements = len(self.to_list())

        if total_elements > 10:
            return f"Stream({', '.join(map(str, elements))}, ...)"
        else:
            return f"Stream({', '.join(map(str, elements))})"

    def __str__(self) -> str:
        """String representation of the stream."""
        return self.__repr__()

    def toString(self, max_elements: int = 10) -> str:
        """Get string representation with specified max elements."""
        if self.is_empty():
            return "Stream()"

        elements = list(self.take(max_elements))
        total_elements = len(self.to_list())

        if total_elements > max_elements:
            return f"Stream({', '.join(map(str, elements))}, ...)"
        else:
            return f"Stream({', '.join(map(str, elements))})"
