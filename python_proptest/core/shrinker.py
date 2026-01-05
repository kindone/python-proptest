"""
Shrinking functionality for finding minimal failing cases.

This module provides backward compatibility by re-exporting Shrinkable
and other utilities from the shrinker package.
"""

import math
import sys
from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, List, TypeVar

# Import Shrinkable and Stream
# Note: When loaded via importlib, these may already be set in the module namespace
# Check if they're already set (by importlib), otherwise import normally
try:
    from .shrinker import Shrinkable  # type: ignore[attr-defined]
except (ImportError, ValueError):
    # If that fails, it should have been set by importlib
    Shrinkable = None  # type: ignore[assignment, misc]

try:
    from .stream import Stream
except (ImportError, ValueError):
    # If that fails, it should have been set by importlib
    Stream = None  # type: ignore[assignment, misc]

T = TypeVar("T")
U = TypeVar("U")


class Shrinker(ABC, Generic[T]):
    """Abstract base class for shrinking algorithms."""

    @abstractmethod
    def shrink(self, value: T) -> List[T]:
        """Generate shrinking candidates for a value."""
        pass


class IntegerShrinker(Shrinker[int]):
    """Shrinker for integers."""

    def shrink(self, value: int) -> List[int]:
        """Generate shrinking candidates for an integer."""
        candidates = []

        # Shrink towards zero
        if value > 0:
            candidates.append(0)
            if value > 1:
                candidates.append(1)
        elif value < 0:
            candidates.append(0)
            if value < -1:
                candidates.append(-1)

        # Binary search shrinking
        if abs(value) > 1:
            candidates.append(value // 2)
            candidates.append(-value // 2)

        return candidates


class StringShrinker(Shrinker[str]):
    """Shrinker for strings that mirrors dartproptest behavior."""

    def shrink(self, value: str) -> List[str]:
        """Generate shrinking candidates for a string."""
        if not value:
            return []

        # Import from the shrinker package to avoid circular imports
        from .shrinker.integral import binary_search_shrinkable
        from .shrinker.list import shrinkable_array

        char_shrinkables = [binary_search_shrinkable(ord(ch)) for ch in value]

        shrinkable = shrinkable_array(
            char_shrinkables,
            min_size=0,
            membership_wise=True,
            element_wise=True,
        )

        return [
            "".join(chr(code) for code in child.value)
            for child in shrinkable.shrinks().to_list()
        ]


class ListShrinker(Shrinker[List[T]]):
    """Shrinker for lists."""

    def __init__(self, element_shrinker: Shrinker[T]):
        self.element_shrinker = element_shrinker

    def shrink(self, value: List[T]) -> List[List[T]]:
        """Generate shrinking candidates for a list."""
        candidates: List[List[T]] = []

        # Empty list
        if len(value) > 0:
            candidates.append([])

        # Shorter lists
        if len(value) > 1:
            candidates.append(value[:-1])  # Remove last element
            candidates.append(value[1:])  # Remove first element

        # Lists with shrunk elements
        for i, element in enumerate(value):
            for shrunk_element in self.element_shrinker.shrink(element):
                new_list = value.copy()
                new_list[i] = shrunk_element
                candidates.append(new_list)

        return candidates


class DictShrinker(Shrinker[dict]):
    """Shrinker for dictionaries."""

    def __init__(self, key_shrinker: Shrinker[Any], value_shrinker: Shrinker[Any]):
        self.key_shrinker = key_shrinker
        self.value_shrinker = value_shrinker

    def shrink(self, value: dict) -> List[dict]:
        """Generate shrinking candidates for a dictionary."""
        candidates: List[dict] = []

        # Empty dictionary
        if len(value) > 0:
            candidates.append({})

        # Dictionaries with fewer items
        if len(value) > 1:
            items = list(value.items())
            candidates.append(dict(items[:-1]))  # Remove last item
            candidates.append(dict(items[1:]))  # Remove first item

        # Dictionaries with shrunk values
        for key, val in value.items():
            for shrunk_value in self.value_shrinker.shrink(val):
                new_dict = value.copy()
                new_dict[key] = shrunk_value
                candidates.append(new_dict)

        return candidates


def shrinkable_boolean(value: bool) -> Shrinkable[bool]:
    """
    Creates a Shrinkable instance for a boolean value.

    Args:
        value: The boolean value to make shrinkable

    Returns:
        A Shrinkable instance representing the boolean value
    """
    if value:
        # If the value is true, it can shrink to false
        return Shrinkable(value, lambda: Stream.one(Shrinkable(False)))
    else:
        # If the value is false, it cannot shrink further
        return Shrinkable(value)


def shrinkable_float(value: float) -> Shrinkable[float]:
    """
    Creates a Shrinkable instance for a float value with sophisticated shrinking.

    Args:
        value: The float value to make shrinkable

    Returns:
        A Shrinkable instance representing the float value
    """

    def shrinkable_float_stream(val: float) -> Stream[Shrinkable[float]]:
        """Generate shrinking candidates for a float value."""
        if val == 0.0:
            return Stream.empty()
        elif math.isnan(val):
            return Stream.one(Shrinkable(0.0))
        else:
            shrinks = []

            # Always shrink towards 0.0
            shrinks.append(Shrinkable(0.0))

            # For infinity, shrink to max/min values
            if val == float("inf"):
                shrinks.append(Shrinkable(sys.float_info.max))
            elif val == float("-inf"):
                shrinks.append(Shrinkable(sys.float_info.min))
            else:
                # For regular floats, add some basic shrinks
                if abs(val) > 1.0:
                    shrinks.append(Shrinkable(val / 2))
                    shrinks.append(Shrinkable(-val / 2))

                # Add integer shrinking
                int_val = math.floor(val) if val > 0 else math.floor(val) + 1
                if int_val != 0 and abs(int_val) < abs(val):
                    shrinks.append(Shrinkable(float(int_val)))

            return Stream.many(shrinks)

    return Shrinkable(value, lambda: shrinkable_float_stream(value))


def shrink_to_minimal(
    initial_value: T,
    predicate: Callable[[T], bool],
    shrinker: Shrinker[T],
    max_attempts: int = 1000,
) -> T:
    """
    Shrink a value to find a minimal failing case.

    Args:
        initial_value: The initial failing value
        predicate: Function that returns True if the value should pass
        shrinker: Shrinker to generate candidates
        max_attempts: Maximum number of shrinking attempts

    Returns:
        A minimal failing value
    """
    current_value = initial_value
    attempts = 0

    while attempts < max_attempts:
        candidates = shrinker.shrink(current_value)

        # Find a smaller failing candidate
        found_smaller = False
        for candidate in candidates:
            if not predicate(candidate):
                current_value = candidate
                found_smaller = True
                break

        if not found_smaller:
            break

        attempts += 1

    return current_value
