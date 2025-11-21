"""
Shrinker for list-like containers (lists, sets, dicts).

Matches cppproptest's listlike, set, and map shrinker implementations.
"""

from typing import List, Set, Dict, TypeVar, Generic
from . import Shrinkable
from .integral import binary_search_shrinkable
from python_proptest.core.stream import Stream

T = TypeVar("T")
U = TypeVar("U")


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
    It attempts to produce arrays with lengths ranging from the original size down to `minSize`.
    Uses binary search internally for efficiency, but ensures we eventually reach `minSize`.

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


def shrink_list(
    shrinkable_elems: List[Shrinkable[T]],
    min_size: int = 0,
    membership_wise: bool = True,
    element_wise: bool = False,
) -> Shrinkable[List[T]]:
    """
    Shrink a list value.

    Args:
        shrinkable_elems: List of Shrinkable elements
        min_size: Minimum allowed size
        membership_wise: If true, allows shrinking by removing elements
        element_wise: If true, applies element-wise shrinking

    Returns:
        A Shrinkable containing the list and its shrinks
    """
    return shrinkable_array(shrinkable_elems, min_size, membership_wise, element_wise)


def shrink_set(
    shrinkable_elems: List[Shrinkable[T]],
    min_size: int = 0,
) -> Shrinkable[Set[T]]:
    """
    Shrink a set value.

    Args:
        shrinkable_elems: List of Shrinkable elements (will be converted to set)
        min_size: Minimum allowed size

    Returns:
        A Shrinkable containing the set and its shrinks.
        Note: Element-wise shrinking is disabled for sets to avoid duplicates.
    """
    # Use shrinkable_array with membership_wise only (no element_wise to avoid duplicates)
    array_shrinkable = shrinkable_array(
        shrinkable_elems, min_size, membership_wise=True, element_wise=False
    )
    # Convert to set
    return array_shrinkable.map(lambda arr: set(arr))


def shrink_dict(
    key_shrinkables: List[Shrinkable[T]],
    value_shrinkables: List[Shrinkable[U]],
    min_size: int = 0,
) -> Shrinkable[Dict[T, U]]:
    """
    Shrink a dictionary value.

    Args:
        key_shrinkables: List of Shrinkable keys
        value_shrinkables: List of Shrinkable values
        min_size: Minimum allowed size

    Returns:
        A Shrinkable containing the dict and its shrinks.
        Shrinks both membership-wise and element-wise (values only).
    """
    # Create pairs of (key, value) shrinkables
    # For dict shrinking, we shrink values but not keys (to maintain dict structure)
    # We'll create a list of value shrinkables and shrink them element-wise
    # while keeping keys fixed
    
    # Create initial dict
    initial_dict = {
        key_shr.value: value_shr.value
        for key_shr, value_shr in zip(key_shrinkables, value_shrinkables)
    }
    
    # Shrink by membership (removing key-value pairs)
    # and by element-wise (shrinking values)
    # We'll use shrinkable_array on the values, then reconstruct the dict
    
    # For membership-wise: remove pairs
    # For element-wise: shrink values
    # This is a simplified version - a full implementation would use pair shrinking
    value_list_shrinkable = shrinkable_array(
        value_shrinkables, min_size, membership_wise=True, element_wise=True
    )
    
    # Reconstruct dict by pairing with keys
    def reconstruct_dict(values: List[U]) -> Dict[T, U]:
        result = {}
        for i, value in enumerate(values):
            if i < len(key_shrinkables):
                result[key_shrinkables[i].value] = value
        return result
    
    return value_list_shrinkable.map(reconstruct_dict)

