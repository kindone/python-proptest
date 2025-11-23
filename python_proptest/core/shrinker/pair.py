"""
Shrinker for pairs (tuples of 2 elements).

Matches cppproptest's shrinkPair implementation.
"""

from typing import Tuple, TypeVar

from ..stream import Stream
from . import Shrinkable

T = TypeVar("T")
U = TypeVar("U")


def shrink_pair(
    first_shrinkable: Shrinkable[T], second_shrinkable: Shrinkable[U]
) -> Shrinkable[Tuple[T, U]]:
    """
    Shrink a pair (tuple of 2 elements).

    Matches cppproptest's shrinkPair implementation:
    - First shrinks the first element (keeping second fixed)
    - Then shrinks the second element (keeping first fixed)
    - Uses concat to combine both shrinking strategies

    Args:
        first_shrinkable: Shrinkable for the first element
        second_shrinkable: Shrinkable for the second element

    Returns:
        A Shrinkable containing the pair and its shrinks.
    """
    # Create a shrinkable pair from the two shrinkables
    # Internal representation: Shrinkable<(Shrinkable<T>, Shrinkable<U>)>
    pair_shrinkable = Shrinkable((first_shrinkable, second_shrinkable))

    # Shrink first element: for each shrink of first, create a new pair
    def shrink_first(
        parent: Shrinkable[Tuple[Shrinkable[T], Shrinkable[U]]],
    ) -> Stream[Shrinkable[Tuple[Shrinkable[T], Shrinkable[U]]]]:
        first_shr, second_shr = parent.value

        # Use flatMap on first_shr: for each shrink of first_shr, create a new pair
        def create_pair_with_shrunk_first(
            shrunken_first_val: T,
        ) -> Shrinkable[Tuple[Shrinkable[T], Shrinkable[U]]]:
            # Create a new shrinkable for the shrunk first value
            # We need to find the shrinkable that produced this value
            # Actually, flat_map gives us the value, not the shrinkable
            # So we create a simple shrinkable with just the value
            return Shrinkable((Shrinkable(shrunken_first_val), second_shr))

        # flat_map on first_shr will iterate through its shrinks and extract their values
        pair_with_elems = first_shr.flat_map(create_pair_with_shrunk_first)
        return pair_with_elems.shrinks()

    # Shrink second element: for each shrink of second, create a new pair
    def shrink_second(
        parent: Shrinkable[Tuple[Shrinkable[T], Shrinkable[U]]],
    ) -> Stream[Shrinkable[Tuple[Shrinkable[T], Shrinkable[U]]]]:
        first_shr, second_shr = parent.value

        # Use flatMap on second_shr: for each shrink of second_shr, create a new pair
        def create_pair_with_shrunk_second(
            shrunken_second_val: U,
        ) -> Shrinkable[Tuple[Shrinkable[T], Shrinkable[U]]]:
            # Create a new shrinkable for the shrunk second value
            return Shrinkable((first_shr, Shrinkable(shrunken_second_val)))

        # flat_map on second_shr will iterate through its shrinks and extract their values
        pair_with_elems = second_shr.flat_map(create_pair_with_shrunk_second)
        return pair_with_elems.shrinks()

    # Apply both shrinking strategies using concat
    result = pair_shrinkable.concat(shrink_first).concat(shrink_second)

    # Map from Shrinkable<(Shrinkable<T>, Shrinkable<U>)> to Shrinkable<Tuple<T, U>>
    return result.map(lambda pair_shr: (pair_shr[0].value, pair_shr[1].value))
