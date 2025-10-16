"""
Shrinking functionality for finding minimal failing cases.

This module provides the Shrinkable class and shrinking algorithms
for reducing failing test cases to minimal counterexamples.
"""

import math
import sys
from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, List, Optional, TypeVar

from .stream import Stream

T = TypeVar("T")
U = TypeVar("U")


class Shrinkable(Generic[T]):
    """A value with its shrinking candidates."""

    def __init__(
        self,
        value: T,
        shrinks_gen: Optional[Callable[[], Stream["Shrinkable[T]"]]] = None,
    ):
        self.value = value
        self.shrinks_gen = shrinks_gen or (lambda: Stream.empty())

    def __repr__(self) -> str:
        return f"Shrinkable({self.value!r})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Shrinkable):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)

    def shrinks(self) -> Stream["Shrinkable[T]"]:
        """Get the shrinking candidates as a stream."""
        return self.shrinks_gen()

    def with_shrinks(
        self, shrink_func: Callable[[], Stream["Shrinkable[T]"]]
    ) -> "Shrinkable[T]":
        """Add shrinking candidates using a function that returns a stream."""
        return Shrinkable(self.value, shrink_func)

    def concat_static(
        self, shrink_func: Callable[[], Stream["Shrinkable[T]"]]
    ) -> "Shrinkable[T]":
        """Add static shrinking candidates."""

        def combined_shrinks() -> Stream["Shrinkable[T]"]:
            return self.shrinks().concat(shrink_func())

        return Shrinkable(self.value, combined_shrinks)

    def concat(
        self, shrink_func: Callable[["Shrinkable[T]"], Stream["Shrinkable[T]"]]
    ) -> "Shrinkable[T]":
        """Add shrinking candidates that depend on the current value."""

        def combined_shrinks() -> Stream["Shrinkable[T]"]:
            return self.shrinks().concat(shrink_func(self))

        return Shrinkable(self.value, combined_shrinks)

    def and_then_static(
        self, shrink_func: Callable[[], Stream["Shrinkable[T]"]]
    ) -> "Shrinkable[T]":
        """Replace shrinking candidates with new ones."""
        return Shrinkable(self.value, shrink_func)

    def and_then(
        self, shrink_func: Callable[["Shrinkable[T]"], Stream["Shrinkable[T]"]]
    ) -> "Shrinkable[T]":
        """Replace shrinking candidates with new ones that depend on the current
        value."""
        return Shrinkable(self.value, lambda: shrink_func(self))

    def map(self, func: Callable[[T], U]) -> "Shrinkable[U]":
        """Transform the value and all shrinking candidates."""

        def mapped_shrinks() -> Stream["Shrinkable[U]"]:
            return self.shrinks().map(lambda shrink: shrink.map(func))

        return Shrinkable(func(self.value), mapped_shrinks)

    def filter(self, predicate: Callable[[T], bool]) -> "Shrinkable[T]":
        """Filter shrinking candidates based on a predicate."""
        if not predicate(self.value):
            raise ValueError("Cannot filter out the root value")

        def filtered_shrinks() -> Stream["Shrinkable[T]"]:
            return (
                self.shrinks()
                .filter(lambda shrink: predicate(shrink.value))
                .map(lambda shrink: shrink.filter(predicate))
            )

        return Shrinkable(self.value, filtered_shrinks)

    def flat_map(self, func: Callable[[T], "Shrinkable[U]"]) -> "Shrinkable[U]":
        """Transform the value and flatten the result."""
        result = func(self.value)

        def flat_mapped_shrinks() -> Stream["Shrinkable[U]"]:
            return (
                self.shrinks()
                .map(lambda shrink: shrink.flat_map(func))
                .concat(result.shrinks())
            )

        return Shrinkable(result.value, flat_mapped_shrinks)

    def get_nth_child(self, index: int) -> "Shrinkable[T]":
        """Get the nth shrinking candidate."""
        if index < 0:
            raise IndexError(f"Index {index} out of range for shrinks")

        shrinks_stream = self.shrinks()
        current = shrinks_stream
        for i in range(index):
            if current.is_empty():
                raise IndexError(f"Index {index} out of range for shrinks")
            current = current.tail()

        if current.is_empty():
            raise IndexError(f"Index {index} out of range for shrinks")

        head_val = current.head()
        if head_val is None:
            raise IndexError(f"Index {index} out of range for shrinks")
        return head_val

    def retrieve(self, path: List[int]) -> "Shrinkable[T]":
        """Retrieve a shrinkable by following a path of indices."""
        if not path:
            return self

        current = self
        for index in path:
            current = current.get_nth_child(index)
        return current


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


# Advanced shrinking algorithms from TypeScript implementation


def binary_search_shrinkable(value: int) -> Shrinkable[int]:
    """
    Creates a Shrinkable<number> that shrinks towards 0 using a binary search approach.

    Args:
        value: The initial integer value.

    Returns:
        A Shrinkable number that shrinks towards 0.
    """

    def gen_pos(min_val: int, max_val: int) -> Stream[Shrinkable[int]]:
        """Generate shrinking candidates for a positive integer range using
        binary search."""
        mid = (
            (min_val // 2)
            + (max_val // 2)
            + (1 if min_val % 2 != 0 and max_val % 2 != 0 else 0)
        )
        if min_val + 1 >= max_val:
            return Stream.empty()  # Base case: No more shrinking possible
        elif min_val + 2 >= max_val:
            return Stream.one(Shrinkable(mid))  # Base case: Only midpoint left
        else:
            # Recursively generate shrinks: prioritize midpoint, then lower half,
            # then upper half
            mid_shrinkable = Shrinkable(mid, lambda: gen_pos(min_val, mid))
            return Stream(mid_shrinkable, lambda: gen_pos(mid, max_val))

    def gen_neg(min_val: int, max_val: int) -> Stream[Shrinkable[int]]:
        """Generate shrinking candidates for a negative integer range using
        binary search."""
        mid = (
            (min_val // 2)
            + (max_val // 2)
            + (-1 if min_val % 2 != 0 and max_val % 2 != 0 else 0)
        )
        if min_val + 1 >= max_val:
            return Stream.empty()  # Base case: No more shrinking possible
        elif min_val + 2 >= max_val:
            return Stream.one(Shrinkable(mid))  # Base case: Only midpoint left
        else:
            # Recursively generate shrinks: prioritize midpoint, then lower half,
            # then upper half
            mid_shrinkable = Shrinkable(mid, lambda: gen_neg(min_val, mid))
            return Stream(mid_shrinkable, lambda: gen_neg(mid, max_val))

    if value == 0:
        return Shrinkable(value)  # 0 cannot shrink further
    elif value > 0:
        # For positive numbers, shrink towards 0: prioritize 0, then use gen_pos
        # for the range (0, value)
        def shrinks() -> Stream[Shrinkable[int]]:
            return Stream.one(Shrinkable(0)).concat(gen_pos(0, value))

        return Shrinkable(value, shrinks)
    else:
        # For negative numbers, shrink towards 0: prioritize 0, then use gen_neg
        # for the range (value, 0)
        def shrinks() -> Stream[Shrinkable[int]]:
            return Stream.one(Shrinkable(0)).concat(gen_neg(value, 0))

        return Shrinkable(value, shrinks)


def shrink_element_wise(
    shrinkable_elems_shr: Shrinkable[List[Shrinkable[T]]], power: int, offset: int
) -> Stream[Shrinkable[List[Shrinkable[T]]]]:
    """
    Shrinks an array by shrinking its individual elements.
    This strategy divides the array into chunks (controlled by `power` and `offset`)
    and shrinks elements within the targeted chunk.

    Args:
        shrinkable_elems_shr: The Shrinkable containing the array of Shrinkable
            elements
        power: Determines the number of chunks (2^power) the array is divided
            into for shrinking
        offset: Specifies which chunk (0 <= offset < 2^power) of elements to
            shrink in this step

    Returns:
        A list of Shrinkable arrays, where elements in the specified chunk have
        been shrunk
    """
    if not shrinkable_elems_shr.value:
        return Stream.empty()

    shrinkable_elems = shrinkable_elems_shr.value
    length = len(shrinkable_elems)
    num_splits = 2**power

    if length / num_splits < 1 or offset >= num_splits:
        return Stream.empty()

    def shrink_bulk(
        ancestor: Shrinkable[List[Shrinkable[T]]], power: int, offset: int
    ) -> List[Shrinkable[List[Shrinkable[T]]]]:
        """Helper function to shrink elements within a specific chunk of the array."""
        parent_size = len(ancestor.value)
        num_splits = 2**power

        if parent_size / num_splits < 1:
            return []

        if offset >= num_splits:
            raise ValueError("offset should not reach num_splits")

        from_pos = (parent_size * offset) // num_splits
        to_pos = (parent_size * (offset + 1)) // num_splits

        if to_pos < parent_size:
            raise ValueError(f"topos error: {to_pos} != {parent_size}")

        parent_arr = ancestor.value
        elem_streams = []
        nothing_to_do = True

        for i in range(from_pos, to_pos):
            shrinks = parent_arr[i].shrinks()
            elem_streams.append(shrinks)
            if not shrinks.is_empty():
                nothing_to_do = False

        if nothing_to_do:
            return []

        # Generate shrinks by combining element shrinks
        results = []
        for i, elem_stream in enumerate(elem_streams):
            for shrink in elem_stream.to_list():
                new_array = parent_arr.copy()
                new_array[from_pos + i] = shrink
                results.append(Shrinkable(new_array))

        return results

    new_shrinkable_elems_shr = shrinkable_elems_shr.concat(
        lambda parent: Stream.many(shrink_bulk(parent, power, offset))
    )
    return new_shrinkable_elems_shr.shrinks()


def shrink_membership_wise(
    shrinkable_elems: List[Shrinkable[T]], min_size: int
) -> Shrinkable[List[Shrinkable[T]]]:
    """
    Shrinks an array by removing elements (membership).
    Simplified version that generates shrinking candidates by removing elements.

    Args:
        shrinkable_elems: The array of Shrinkable elements
        min_size: The minimum allowed size for the shrunken array

    Returns:
        A Shrinkable representing arrays with potentially fewer elements
    """

    def generate_shrinks(
        elems: List[Shrinkable[T]],
    ) -> List[Shrinkable[List[Shrinkable[T]]]]:
        """Generate shrinking candidates by removing elements."""
        shrinks: List[Shrinkable[List[Shrinkable[T]]]] = []

        # Empty array (if min_size allows)
        if min_size == 0 and len(elems) > 0:
            shrinks.append(Shrinkable([]))

        # Remove elements from the end
        for i in range(len(elems) - 1, min_size - 1, -1):
            if i >= min_size:
                shrinks.append(Shrinkable(elems[:i]))

        # Remove elements from the beginning
        for i in range(1, len(elems) - min_size + 1):
            if len(elems) - i >= min_size:
                shrinks.append(Shrinkable(elems[i:]))

        return shrinks

    return Shrinkable(
        shrinkable_elems, lambda: Stream.many(generate_shrinks(shrinkable_elems))
    )


def shrinkable_array(
    shrinkable_elems: List[Shrinkable[T]],
    min_size: int,
    membership_wise: bool = True,
    element_wise: bool = False,
) -> Shrinkable[List[T]]:
    """
    Creates a Shrinkable for an array, allowing shrinking by removing elements
    and optionally by shrinking the elements themselves.

    Args:
        shrinkable_elems: The initial array of Shrinkable elements
        min_size: The minimum allowed length of the array after shrinking element
            membership
        membership_wise: If true, allows shrinking by removing elements
            (membership). Defaults to true
        element_wise: If true, applies element-wise shrinking *after* membership
            shrinking. Defaults to false

    Returns:
        A Shrinkable<Array<T>> that represents the original array and its
        potential shrunken versions
    """
    # Base Shrinkable containing the initial structure Shrinkable<T>[]
    current_shrinkable = Shrinkable(shrinkable_elems)

    # Chain membership shrinking if enabled
    if membership_wise:
        current_shrinkable = current_shrinkable.and_then(
            lambda parent: shrink_membership_wise(parent.value, min_size).shrinks()
        )

    # Chain element-wise shrinking if enabled
    if element_wise:
        current_shrinkable = current_shrinkable.and_then(
            lambda parent: shrink_element_wise(parent, 0, 0)
        )

    # Map the final Shrinkable<Shrinkable<T>[]> to Shrinkable<Array<T>> by
    # extracting the values
    return current_shrinkable.map(lambda the_arr: [shr.value for shr in the_arr])


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
