"""
Either type for representing values of one of two possible types.

This module provides the Either, Left, and Right classes for handling
values that can be one of two types in a functional programming style.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, TypeVar

L = TypeVar("L")
R = TypeVar("R")
U = TypeVar("U")


class Either(ABC, Generic[L, R]):
    """Abstract base class for either values."""

    @abstractmethod
    def is_left(self) -> bool:
        """Check if this either is a Left."""
        pass

    @abstractmethod
    def is_right(self) -> bool:
        """Check if this either is a Right."""
        pass

    @abstractmethod
    def get_left(self) -> L:
        """Get the left value, raising an exception if Right."""
        pass

    @abstractmethod
    def get_right(self) -> R:
        """Get the right value, raising an exception if Left."""
        pass

    @abstractmethod
    def get_or_else(self, default: R) -> R:
        """Get the right value or return a default."""
        pass

    @abstractmethod
    def map(self, func: Callable[[R], U]) -> "Either[L, U]":
        """Map a function over the right value."""
        pass

    @abstractmethod
    def map_left(self, func: Callable[[L], U]) -> "Either[U, R]":
        """Map a function over the left value."""
        pass

    @abstractmethod
    def flat_map(self, func: Callable[[R], "Either[L, U]"]) -> "Either[L, U]":
        """Flat map a function over the right value."""
        pass


class Left(Either[L, R]):
    """An either that contains a left value."""

    def __init__(self, value: L):
        self._value = value

    def is_left(self) -> bool:
        return True

    def is_right(self) -> bool:
        return False

    def get_left(self) -> L:
        return self._value

    def get_right(self) -> R:
        raise ValueError("Cannot get right value from Left")

    def get_or_else(self, default: R) -> R:
        return default

    def map(self, func: Callable[[R], U]) -> "Either[L, U]":
        return Left(self._value)

    def map_left(self, func: Callable[[L], U]) -> "Either[U, R]":
        return Left(func(self._value))

    def flat_map(self, func: Callable[[R], "Either[L, U]"]) -> "Either[L, U]":
        return Left(self._value)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Left):
            return False
        return self._value == other._value

    def __repr__(self) -> str:
        return f"Left({self._value!r})"


class Right(Either[L, R]):
    """An either that contains a right value."""

    def __init__(self, value: R):
        self._value = value

    def is_left(self) -> bool:
        return False

    def is_right(self) -> bool:
        return True

    def get_left(self) -> L:
        raise ValueError("Cannot get left value from Right")

    def get_right(self) -> R:
        return self._value

    def get_or_else(self, default: R) -> R:
        return self._value

    def map(self, func: Callable[[R], U]) -> "Either[L, U]":
        return Right(func(self._value))

    def map_left(self, func: Callable[[L], U]) -> "Either[U, R]":
        return Right(self._value)

    def flat_map(self, func: Callable[[R], "Either[L, U]"]) -> "Either[L, U]":
        return func(self._value)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Right):
            return False
        return self._value == other._value

    def __repr__(self) -> str:
        return f"Right({self._value!r})"
