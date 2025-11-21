"""
Shrinker for pairs (tuples of 2 elements).

Matches cppproptest's shrinkPair implementation.
"""

from typing import Tuple, TypeVar
from . import Shrinkable
from ..stream import Stream

T = TypeVar("T")
U = TypeVar("U")


def shrink_pair(
    first_shrinkable: Shrinkable[T], second_shrinkable: Shrinkable[U]
) -> Shrinkable[Tuple[T, U]]:
    """
    Shrink a pair (tuple of 2 elements).

    Args:
        first_shrinkable: Shrinkable for the first element
        second_shrinkable: Shrinkable for the second element

    Returns:
        A Shrinkable containing the pair and its shrinks.
        Shrinks by shrinking the first element, then the second element.
    """
    value = (first_shrinkable.value, second_shrinkable.value)

    def make_shrinks() -> Stream[Shrinkable[Tuple[T, U]]]:
        shrinks = []

        # Shrink first element
        for first_shrink in first_shrinkable.shrinks().to_list():
            shrinks.append(
                Shrinkable((first_shrink.value, second_shrinkable.value))
            )

        # Shrink second element
        for second_shrink in second_shrinkable.shrinks().to_list():
            shrinks.append(
                Shrinkable((first_shrinkable.value, second_shrink.value))
            )

        return Stream.many(shrinks)

    return Shrinkable(value, make_shrinks)

