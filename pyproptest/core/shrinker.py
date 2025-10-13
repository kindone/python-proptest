"""
Shrinking functionality for finding minimal failing cases.

This module provides the Shrinkable class and shrinking algorithms
for reducing failing test cases to minimal counterexamples.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, List, Optional, TypeVar

T = TypeVar("T")


class Shrinkable(Generic[T]):
    """A value with its shrinking candidates."""

    def __init__(self, value: T, shrinks: Optional[List["Shrinkable[T]"]] = None):
        self.value = value
        self.shrinks = shrinks or []

    def __repr__(self) -> str:
        return f"Shrinkable({self.value!r})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Shrinkable):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)


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
    """Shrinker for strings."""

    def shrink(self, value: str) -> List[str]:
        """Generate shrinking candidates for a string."""
        candidates = []

        # Empty string
        if len(value) > 0:
            candidates.append("")

        # Shorter strings
        if len(value) > 1:
            candidates.append(value[:-1])  # Remove last character
            candidates.append(value[1:])  # Remove first character

        # Single character strings
        if len(value) > 0:
            candidates.append(value[0])  # First character only
            if len(value) > 1:
                candidates.append(value[-1])  # Last character only

        return candidates


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
