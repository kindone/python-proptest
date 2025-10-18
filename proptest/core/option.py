"""
Option type for representing optional values.

This module provides the Option, Some, and None classes for handling
optional values in a functional programming style.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")
U = TypeVar("U")


class Option(ABC, Generic[T]):
    """Abstract base class for optional values."""

    @abstractmethod
    def is_some(self) -> bool:
        """Check if this option contains a value."""
        pass

    @abstractmethod
    def is_none(self) -> bool:
        """Check if this option is empty."""
        pass

    @abstractmethod
    def get(self) -> T:
        """Get the value, raising an exception if None."""
        pass

    @abstractmethod
    def get_or_else(self, default: T) -> T:
        """Get the value or return a default."""
        pass

    @abstractmethod
    def map(self, func: Callable[[T], U]) -> "Option[U]":
        """Map a function over the option."""
        pass

    @abstractmethod
    def flat_map(self, func: Callable[[T], "Option[U]"]) -> "Option[U]":
        """Flat map a function over the option."""
        pass

    @abstractmethod
    def filter(self, predicate: Callable[[T], bool]) -> "Option[T]":
        """Filter the option using a predicate."""
        pass


class Some(Option[T]):
    """An option that contains a value."""

    def __init__(self, value: T):
        self._value = value

    def is_some(self) -> bool:
        return True

    def is_none(self) -> bool:
        return False

    def get(self) -> T:
        return self._value

    def get_or_else(self, default: T) -> T:
        return self._value

    def map(self, func: Callable[[T], U]) -> "Option[U]":
        return Some(func(self._value))

    def flat_map(self, func: Callable[[T], "Option[U]"]) -> "Option[U]":
        return func(self._value)

    def filter(self, predicate: Callable[[T], bool]) -> "Option[T]":
        if predicate(self._value):
            return self
        return None_()

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Some):
            return False
        return self._value == other._value

    def __repr__(self) -> str:
        return f"Some({self._value!r})"


class None_(Option[T]):
    """An option that contains no value."""

    def is_some(self) -> bool:
        return False

    def is_none(self) -> bool:
        return True

    def get(self) -> T:
        raise ValueError("Cannot get value from None")

    def get_or_else(self, default: T) -> T:
        return default

    def map(self, func: Callable[[T], U]) -> "Option[U]":
        return None_()

    def flat_map(self, func: Callable[[T], "Option[U]"]) -> "Option[U]":
        return None_()

    def filter(self, predicate: Callable[[T], bool]) -> "Option[T]":
        return self

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, None_)

    def __repr__(self) -> str:
        return "None"


# Convenience function to create None
def none() -> None_[Any]:
    """Create a None option."""
    return None_()
