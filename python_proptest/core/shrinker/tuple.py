"""
Shrinker for tuples of N elements.

Matches cppproptest's shrinkTuple implementation.
"""

from typing import List, Tuple, TypeVar

from ..stream import Stream
from . import Shrinkable

T = TypeVar("T")


def shrink_tuple(shrinkables: List[Shrinkable[T]]) -> Shrinkable[Tuple[T, ...]]:
    """
    Shrink a tuple of N elements.

    Matches cppproptest's shrinkTupleUsingVector implementation:
    - For each position N in the tuple (0 to Size-1):
      - Shrinks the element at position N (keeping all other elements fixed)
      - Uses concat to combine shrinking strategies for all positions
    - Recursively applies shrinking to each element

    Args:
        shrinkables: List of Shrinkable elements for the tuple

    Returns:
        A Shrinkable containing the tuple and its shrinks.
    """
    if not shrinkables:
        raise ValueError("shrinkables must not be empty")

    # Create initial shrinkable tuple from the list of shrinkables
    # Internal representation: Shrinkable<List[Shrinkable<T>>>
    tuple_shrinkable = Shrinkable(shrinkables)

    # For each position in the tuple, add shrinking strategy
    for position in range(len(shrinkables)):

        def make_shrink_at_position(pos: int):
            """Create a shrinking function for position pos."""

            def shrink_at_position(
                parent: Shrinkable[List[Shrinkable[T]]],
            ) -> Stream[Shrinkable[List[Shrinkable[T]]]]:
                """
                Shrink the element at position pos.

                For each shrink of the element at position pos, create a new tuple
                with that element replaced, keeping all other elements fixed.
                """
                parent_list = parent.value
                if pos >= len(parent_list):
                    return Stream.empty()

                elem_shrinkable = parent_list[pos]

                # Map the element shrinkable to create a new tuple shrinkable
                # For each value in the element's shrink tree, create a new tuple with that element replaced
                def create_tuple_with_shrunk_element(
                    shrunken_elem_val: T,
                ) -> List[Shrinkable[T]]:
                    # Create a copy of the parent list
                    new_list = []
                    for i, shr in enumerate(parent_list):
                        if i == pos:
                            # Replace element at position pos with a new shrinkable containing the shrunk value
                            # Note: We create a simple Shrinkable here, but the recursive shrinking
                            # will come from the concat operation on the parent
                            new_list.append(Shrinkable(shrunken_elem_val))
                        else:
                            # Keep other elements as-is (they're already Shrinkable)
                            new_list.append(shr)
                    return new_list

                # Use map to transform the element shrinkable into a tuple shrinkable
                # This creates a Shrinkable<List[Shrinkable<T>>> where the element at pos is shrunk
                tuple_with_shrunk_elem = elem_shrinkable.map(
                    create_tuple_with_shrunk_element
                )
                # Return the shrinks of this mapped shrinkable
                return tuple_with_shrunk_elem.shrinks()

            return shrink_at_position

        # Apply shrinking strategy for this position using concat
        tuple_shrinkable = tuple_shrinkable.concat(make_shrink_at_position(position))

    # Map from Shrinkable<List[Shrinkable<T>>> to Shrinkable<Tuple<T, ...>>
    # by extracting the actual values from the nested Shrinkables
    return tuple_shrinkable.map(
        lambda shrinkable_list: tuple(shr.value for shr in shrinkable_list)
    )
