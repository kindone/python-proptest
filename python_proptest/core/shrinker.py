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
    from .shrinker import Shrinkable
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


def shrink_array_length(
    shrinkable_elems: List[Shrinkable[T]], min_size: int
) -> Shrinkable[List[T]]:
    """
    Shrinks an array by reducing its length from the rear.
    It attempts to produce arrays with lengths ranging from the original size
    down to `minSize`. Uses binary search internally for efficiency, but ensures
    we eventually reach `minSize`.

    Args:
        shrinkable_elems: The array of Shrinkable elements
        min_size: The minimum allowed size for the shrunken array

    Returns:
        A Shrinkable representing arrays of potentially smaller lengths
    """
    size = len(shrinkable_elems)
    if size <= min_size:
        # Already at minimum size, no shrinking possible
        return Shrinkable([shr.value for shr in shrinkable_elems[:size]])

    range_val = size - min_size
    range_shrinkable_original = binary_search_shrinkable(range_val)

    # Check if 0 (which maps to minSize) is already in the shrink tree
    has_zero = False

    def check_for_zero(shr: Shrinkable[int]) -> None:
        nonlocal has_zero
        if shr.value == 0:
            has_zero = True
            return
        for shrink in shr.shrinks().to_list():
            check_for_zero(shrink)

    check_for_zero(range_shrinkable_original)

    # Map range values to actual sizes
    range_shrinkable = range_shrinkable_original.map(lambda s: s + min_size)

    # If 0 is not in the tree, add it as a final shrink (which maps to minSize)
    if not has_zero:
        return range_shrinkable.concat_static(
            lambda: Stream.one(Shrinkable(min_size))
        ).map(
            lambda new_size: (
                []
                if new_size == 0
                else [shr.value for shr in shrinkable_elems[:new_size]]
            )
        )
    else:
        return range_shrinkable.map(
            lambda new_size: (
                []
                if new_size == 0
                else [shr.value for shr in shrinkable_elems[:new_size]]
            )
        )


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
