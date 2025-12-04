"""
Shrinker for list-like containers (lists, sets, dicts).

Matches cppproptest's listlike, set, and map shrinker implementations.
"""

from typing import Dict, List, Set, Tuple, TypeVar

from python_proptest.core.stream import Stream

from . import Shrinkable
from .integral import binary_search_shrinkable, shrink_integral

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


def _shrink_front_and_then_mid(
    shrinkable_elems: List[Shrinkable[T]], min_size: int, rear_size: int
) -> Shrinkable[List[Shrinkable[T]]]:
    """
    Shrinks an array using the shrinkFrontAndThenMid strategy from cppproptest.

    This strategy:
    1. Shrinks the front size (number of elements to keep from front) using binary search
    2. Keeps rear_size elements at the end intact
    3. Recursively shrinks by incrementing rear_size

    This generates all 2^N subsets for a list of size N.

    Args:
        shrinkable_elems: The array of Shrinkable elements
        min_size: The minimum allowed size for the shrunken array
        rear_size: Number of elements to keep at the rear (fixed)

    Returns:
        A Shrinkable representing arrays with potentially fewer elements
    """
    shrinkable_cont = shrinkable_elems
    min_front_size = min_size - rear_size if min_size >= rear_size else 0
    max_front_size = len(shrinkable_cont) - rear_size

    # If no valid front size range, return empty shrinks
    if max_front_size < min_front_size:
        return Shrinkable(shrinkable_elems)

    # Shrink the front size using binary search (shrinkIntegral for size_t)
    # Range is [min_front_size, max_front_size] (inclusive)
    # We shrink (max_front_size - min_front_size) to get values in [0, max_front_size - min_front_size]
    # Then map to [min_front_size, max_front_size]
    range_size = max_front_size - min_front_size
    if range_size < 0:
        return Shrinkable(shrinkable_elems)

    # Use shrink_integral to shrink the range size, then map to actual front sizes
    range_shrinkable = shrink_integral(range_size, min_value=0, max_value=range_size)

    # Map the shrunk range size back to front size
    def map_to_front_size(range_val: int) -> int:
        return range_val + min_front_size

    front_size_shrinkable = range_shrinkable.map(map_to_front_size)

    # For each front size, create a list with front_size elements from front + rear elements
    def create_list_with_front_size(front_size: int) -> List[Shrinkable[T]]:
        # Take front_size elements from the front
        front_part = shrinkable_cont[:front_size]
        # Take rear_size elements from the end (starting at max_front_size)
        rear_part = shrinkable_cont[max_front_size:]
        # Concatenate front and rear
        return front_part + rear_part

    # Flat map: for each front size, create the corresponding list
    # Each shrinkable created here will have recursive shrinks added via concat
    def create_shrinkable_with_front_size(
        front_size: int,
    ) -> Shrinkable[List[Shrinkable[T]]]:
        new_list = create_list_with_front_size(front_size)
        return Shrinkable(new_list)

    result_shrinkable = front_size_shrinkable.flat_map(
        create_shrinkable_with_front_size
    )

    # Recursively shrink by incrementing rear_size
    # This adds recursive shrinks to each parent shrinkable
    def recursive_shrinks(
        parent: Shrinkable[List[Shrinkable[T]]],
    ) -> Stream[Shrinkable[List[Shrinkable[T]]]]:
        parent_size = len(parent.value)
        # No further shrinking possible
        if parent_size <= min_size or parent_size <= rear_size:
            return Stream.empty()
        # Shrink front further by fixing one more element to rear
        # This returns a Shrinkable, and we want its shrinks
        recursive_result = _shrink_front_and_then_mid(
            parent.value, min_size, rear_size + 1
        )
        return recursive_result.shrinks()

    # Concatenate recursive shrinks to the result
    # This adds recursive shrinks to each shrinkable in the result
    return result_shrinkable.concat(recursive_shrinks)


def shrink_membership_wise(
    shrinkable_elems: List[Shrinkable[T]], min_size: int
) -> Shrinkable[List[Shrinkable[T]]]:
    """
    Shrinks an array by removing elements (membership).

    Uses shrinkFrontAndThenMid strategy from cppproptest, which generates
    all 2^N subsets for a list of size N.

    Args:
        shrinkable_elems: The array of Shrinkable elements
        min_size: The minimum allowed size for the shrunken array

    Returns:
        A Shrinkable representing arrays with potentially fewer elements
    """
    return _shrink_front_and_then_mid(shrinkable_elems, min_size, 0)


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
    # Matches cppproptest: element-wise shrinking applies recursively to membership shrinks
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
    Shrink a dictionary value using pair shrinking.

    Matches cppproptest's shrinkMap implementation:
    - Creates pairs from (key, value) shrinkables
    - Uses shrinkable_array with both membership-wise and element-wise shrinking
    - Element-wise shrinking uses pair shrinking, allowing both keys and values to shrink

    Args:
        key_shrinkables: List of Shrinkable keys
        value_shrinkables: List of Shrinkable values
        min_size: Minimum allowed size

    Returns:
        A Shrinkable containing the dict and its shrinks.
        Shrinks both membership-wise (removing pairs) and element-wise (shrinking pairs).
    """
    from .pair import shrink_pair

    # Create pairs of (key, value) shrinkables
    # Each pair is a Shrinkable<(key, value)>
    pair_shrinkables: List[Shrinkable[Tuple[T, U]]] = []
    for key_shr, value_shr in zip(key_shrinkables, value_shrinkables):
        pair_shr = shrink_pair(key_shr, value_shr)
        pair_shrinkables.append(pair_shr)

    # Use shrinkable_array with both membership-wise and element-wise shrinking
    # Element-wise shrinking will recursively shrink each pair (both key and value)
    array_shrinkable = shrinkable_array(
        pair_shrinkables, min_size, membership_wise=True, element_wise=True
    )

    # Convert list of pairs to dictionary
    def pairs_to_dict(pairs: List[Tuple[T, U]]) -> Dict[T, U]:
        result = {}
        for key, value in pairs:
            result[key] = value
        return result

    return array_shrinkable.map(pairs_to_dict)
