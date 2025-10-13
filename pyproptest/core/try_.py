"""
Try type for representing computations that may fail.

This module provides the Try, Success, and Failure classes for handling
computations that may throw exceptions in a functional programming style.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")
U = TypeVar("U")


class Try(ABC, Generic[T]):
    """Abstract base class for try values."""

    @abstractmethod
    def is_success(self) -> bool:
        """Check if this try is a Success."""
        pass

    @abstractmethod
    def is_failure(self) -> bool:
        """Check if this try is a Failure."""
        pass

    @abstractmethod
    def get(self) -> T:
        """Get the value, raising an exception if Failure."""
        pass

    @abstractmethod
    def get_or_else(self, default: T) -> T:
        """Get the value or return a default."""
        pass

    @abstractmethod
    def get_exception(self) -> Exception:
        """Get the exception, raising an exception if Success."""
        pass

    @abstractmethod
    def map(self, func: Callable[[T], U]) -> "Try[U]":
        """Map a function over the try value."""
        pass

    @abstractmethod
    def flat_map(self, func: Callable[[T], "Try[U]"]) -> "Try[U]":
        """Flat map a function over the try value."""
        pass

    @abstractmethod
    def recover(self, func: Callable[[Exception], T]) -> "Try[T]":
        """Recover from a failure using a function."""
        pass

    @abstractmethod
    def filter(self, predicate: Callable[[T], bool]) -> "Try[T]":
        """Filter the try using a predicate."""
        pass


class Success(Try[T]):
    """A try that contains a successful value."""

    def __init__(self, value: T):
        self._value = value

    def is_success(self) -> bool:
        return True

    def is_failure(self) -> bool:
        return False

    def get(self) -> T:
        return self._value

    def get_or_else(self, default: T) -> T:
        return self._value

    def get_exception(self) -> Exception:
        raise ValueError("Cannot get exception from Success")

    def map(self, func: Callable[[T], U]) -> "Try[U]":
        try:
            return Success(func(self._value))
        except Exception as e:
            return Failure(e)

    def flat_map(self, func: Callable[[T], "Try[U]"]) -> "Try[U]":
        try:
            return func(self._value)
        except Exception as e:
            return Failure(e)

    def recover(self, func: Callable[[Exception], T]) -> "Try[T]":
        return self

    def filter(self, predicate: Callable[[T], bool]) -> "Try[T]":
        try:
            if predicate(self._value):
                return self
            else:
                return Failure(ValueError("Predicate failed"))
        except Exception as e:
            return Failure(e)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Success):
            return False
        return self._value == other._value

    def __repr__(self) -> str:
        return f"Success({self._value!r})"


class Failure(Try[T]):
    """A try that contains a failure."""

    def __init__(self, exception: Exception):
        self._exception = exception

    def is_success(self) -> bool:
        return False

    def is_failure(self) -> bool:
        return True

    def get(self) -> T:
        raise self._exception

    def get_or_else(self, default: T) -> T:
        return default

    def get_exception(self) -> Exception:
        return self._exception

    def map(self, func: Callable[[T], U]) -> "Try[U]":
        return Failure(self._exception)

    def flat_map(self, func: Callable[[T], "Try[U]"]) -> "Try[U]":
        return Failure(self._exception)

    def recover(self, func: Callable[[Exception], T]) -> "Try[T]":
        try:
            return Success(func(self._exception))
        except Exception as e:
            return Failure(e)

    def filter(self, predicate: Callable[[T], bool]) -> "Try[T]":
        return self

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Failure):
            return False
        return isinstance(self._exception, type(other._exception)) and str(
            self._exception
        ) == str(other._exception)

    def __repr__(self) -> str:
        return f"Failure({self._exception!r})"


def attempt(func: Callable[[], T]) -> Try[T]:
    """Attempt to execute a function, returning Success or Failure."""
    try:
        return Success(func())
    except Exception as e:
        return Failure(e)
