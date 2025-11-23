"""
Shrinker for integral types (integers).

Matches cppproptest's shrinkIntegral implementation.
"""

import math
import sys
from typing import List

from ..stream import Stream
from . import Shrinkable


def cpp_div(a: int, b: int) -> int:
    """Simulate C++ integer division (truncates towards 0)."""
    result = a / b
    return int(result) if result >= 0 else int(math.ceil(result))


def _gen_pos(
    min_val: int,
    max_val: int,
    offset: int,
    min_bound: int = -sys.maxsize - 1,
    max_bound: int = sys.maxsize,
) -> List[Shrinkable[int]]:
    """
    Generate shrinks for a positive integer range using binary search.
    Works on half-open range [min_val, max_val) to avoid duplicates.
    """
    # Range is [min_val, max_val) - half-open, max_val is exclusive
    if min_val + 1 >= max_val:
        return []  # No more shrinking possible

    # Calculate midpoint, ensuring it rounds towards min correctly
    mid = (
        ((min_val - 1) // 2 if min_val < 0 else min_val // 2)
        + ((max_val - 1) // 2 if max_val < 0 else max_val // 2)
        + (1 if min_val % 2 != 0 and max_val % 2 != 0 else 0)
    )

    # Ensure mid is strictly between min_val and max_val
    if mid <= min_val:
        mid = min_val + 1
    if mid >= max_val:
        mid = max_val - 1
    if mid <= min_val:  # Range too small
        return []

    if min_val + 2 >= max_val:
        # Only midpoint left in range [min_val, max_val)
        # Since max_val is exclusive, we only have min_val and mid (if mid != min_val)
        if mid != min_val:
            final_value = mid + offset
            if min_bound <= final_value <= max_bound:
                return [Shrinkable(final_value)]
        return []

    # Recursively generate shrinks: prioritize midpoint, then lower half, then upper half
    # Ranges are disjoint: [min_val, mid) and [mid, max_val)
    mid_value = mid + offset
    shrinks = []
    if min_bound <= mid_value <= max_bound:
        # Create recursive shrinkable for midpoint
        # Range [min_val, mid) is disjoint from [mid, max_val), so no duplicates
        # Only recurse if the range will actually shrink (mid > min_val + 1)
        if min_val < mid < max_val and (mid - min_val) > 1:

            def make_mid_shrinks():
                mid_shrinks = _gen_pos(min_val, mid, offset, min_bound, max_bound)
                return Stream.many(mid_shrinks) if mid_shrinks else Stream.empty()

            shrinks.append(Shrinkable(mid_value, make_mid_shrinks))
        elif min_val < mid < max_val:
            # Mid is min_val + 1, just add it without recursion
            shrinks.append(Shrinkable(mid_value))

    # Add shrinks from upper half [mid, max_val) - disjoint from [min_val, mid)
    # Only recurse if the range will actually shrink (max_val > mid + 1)
    if mid < max_val:
        if (max_val - mid) > 1:
            upper_shrinks = _gen_pos(mid, max_val, offset, min_bound, max_bound)
            shrinks.extend(upper_shrinks)
        # If max_val == mid + 1, the range [mid, max_val) is empty, so nothing to add

    return shrinks


def _gen_neg(
    min_val: int,
    max_val: int,
    offset: int,
    min_bound: int = -sys.maxsize - 1,
    max_bound: int = sys.maxsize,
) -> List[Shrinkable[int]]:
    """
    Generate shrinks for a negative integer range using binary search.
    Matches cppproptest's genneg implementation.
    Works on half-open range (min_val, max_val] to avoid duplicates.
    Note: Uses _gen_neg recursively for both halves (as per cppproptest implementation).
    """
    # Range is (min_val, max_val] - half-open on left, min_val is exclusive
    if min_val + 1 >= max_val:
        return []  # No more shrinking possible

    # Calculate midpoint, matching cppproptest's formula:
    # mid = min/2 + max/2 + ((min % 2 != 0 && max % 2 != 0) ? -1 : 0)
    mid = (
        cpp_div(min_val, 2)
        + cpp_div(max_val, 2)
        + (-1 if min_val % 2 != 0 and max_val % 2 != 0 else 0)
    )

    # Ensure mid is strictly between min_val and max_val
    if mid <= min_val:
        mid = min_val + 1
    if mid >= max_val:
        mid = max_val - 1
    if mid <= min_val:  # Range too small
        return []

    if min_val + 2 >= max_val:
        # Only midpoint left in range (min_val, max_val]
        # Since min_val is exclusive, we only have mid and max_val (if mid != max_val)
        if mid != max_val:
            final_value = mid + offset
            if min_bound <= final_value <= max_bound:
                return [Shrinkable(final_value)]
        return []

    # cppproptest structure: midpoint with child from genneg(mid, max), then genneg(min, mid)
    # This gives: midpoint, then its recursive children (from upper half), then lower half
    mid_value = mid + offset
    shrinks = []

    # First: midpoint with recursive shrinks from upper half genneg(mid, max)
    if min_bound <= mid_value <= max_bound:
        # Create recursive shrinkable for midpoint
        # The child comes from genneg(mid, max) - the upper half
        # Only recurse if the range will actually shrink (max_val > mid + 1)
        if mid < max_val and (max_val - mid) > 1:

            def make_mid_shrinks():
                # Child comes from genneg(mid, max) - upper half
                mid_shrinks = _gen_neg(mid, max_val, offset, min_bound, max_bound)
                return Stream.many(mid_shrinks) if mid_shrinks else Stream.empty()

            shrinks.append(Shrinkable(mid_value, make_mid_shrinks))
        elif mid < max_val:
            # Mid is max_val - 1, just add it without recursion
            shrinks.append(Shrinkable(mid_value))

    # Then: lower half genneg(min, mid)
    # Only recurse if the range will actually shrink (mid > min_val + 1)
    if min_val < mid and (mid - min_val) > 1:
        lower_shrinks = _gen_neg(min_val, mid, offset, min_bound, max_bound)
        shrinks.extend(lower_shrinks)

    return shrinks


def _binary_search_towards_zero(
    value: int,
    min_bound: int = -sys.maxsize - 1,
    max_bound: int = sys.maxsize,
) -> List[Shrinkable[int]]:
    """Generate shrinks for an integer using binary search towards 0."""
    if value == 0:
        return []

    if value > 0:
        # For positive numbers, prioritize 0, then use binary search for (0, value)
        shrinks = [Shrinkable(0)]
        # Only recurse if value > 1 (so range [0, value) has room to shrink)
        if value > 1:
            shrinks.extend(_gen_pos(0, value, 0, min_bound, max_bound))
        return shrinks
    else:
        # For negative numbers, prioritize 0, then use binary search for (value, 0)
        shrinks = [Shrinkable(0)]
        # Only recurse if value < -1 (so range (value, 0] has room to shrink)
        if value < -1:
            shrinks.extend(_gen_neg(value, 0, 0, min_bound, max_bound))
        return shrinks


def _binary_search_towards_min(
    value: int,
    offset: int,
    min_bound: int = -sys.maxsize - 1,
    max_bound: int = sys.maxsize,
) -> List[Shrinkable[int]]:
    """Generate shrinks for an integer using binary search towards min_value."""
    if value == 0:
        return []

    if value > 0:
        # For positive values, shrink towards 0, then add offset
        # We need to exclude the original value, so end at value (exclusive)
        shrinks = [Shrinkable(min_bound)]
        # _gen_pos(0, value, offset) generates range [0, value) with offset
        # This excludes value itself, which is correct
        if value > 0:
            shrinks.extend(_gen_pos(0, value, min_bound, min_bound, max_bound))
        return shrinks
    else:
        shrinks = [Shrinkable(min_bound)]
        # For negative values, shrink from value+1 to 0 (exclusive of value)
        # Only recurse if value+1 < 0 and there's room to shrink
        if value + 1 < 0 and (0 - (value + 1)) > 1:
            shrinks.extend(_gen_neg(value + 1, 0, min_bound, min_bound, max_bound))
        return shrinks


def _binary_search_towards_max(
    value: int,
    offset: int,
    min_bound: int = -sys.maxsize - 1,
    max_bound: int = sys.maxsize,
) -> List[Shrinkable[int]]:
    """Generate shrinks for an integer using binary search towards max_value."""
    if value == 0:
        return []

    if value < 0:
        # For negative values, shrink towards 0, then add offset
        # We need to exclude the original value, so start from value+1
        shrinks = [Shrinkable(max_bound)]
        # _gen_neg(value+1, 0, offset) generates range (value+1, 0] with offset
        # This excludes value itself (which maps to the original value)
        # Only recurse if value+1 < 0 and there's room to shrink
        if value + 1 < 0 and (0 - (value + 1)) > 1:
            shrinks.extend(_gen_neg(value + 1, 0, max_bound, min_bound, max_bound))
        return shrinks
    else:
        shrinks = [Shrinkable(max_bound)]
        # For positive values, shrink from 0 to value (exclusive of value)
        if value > 0:
            shrinks.extend(_gen_pos(0, value, max_bound, min_bound, max_bound))
        return shrinks


def shrink_integral(
    value: int,
    min_value: int = -sys.maxsize - 1,
    max_value: int = sys.maxsize,
) -> Shrinkable[int]:
    """
    Shrink an integer value.

    Args:
        value: The integer value to shrink
        min_value: Minimum allowed value (for range validation)
        max_value: Maximum allowed value (for range validation)

    Returns:
        A Shrinkable containing the value and its shrinks
    """
    # Use binary search approach similar to cppproptest
    if min_value >= 0:
        # Range is entirely non-negative: shrink towards min_value
        if value == min_value:
            shrinks = []  # Already at minimum, can't shrink further
        else:
            shrinks = _binary_search_towards_min(
                value - min_value, min_value, min_value, max_value
            )
    elif max_value <= 0:
        # Range is entirely non-positive: shrink towards max_value
        if value == max_value:
            shrinks = []  # Already at maximum (least negative), can't shrink further
        else:
            shrinks = _binary_search_towards_max(
                value - max_value, max_value, min_value, max_value
            )
    else:
        # Range crosses zero: shrink towards 0
        # For negative numbers, smaller negatives are more complex, so we should
        # shrink towards 0 even if at min_value boundary
        # For positive numbers, larger positives are more complex, so we should
        # shrink towards 0 even if at max_value boundary
        # Only 0 itself cannot shrink further
        if value == 0:
            shrinks = []  # Already at 0, can't shrink further
        else:
            shrinks = _binary_search_towards_zero(value, min_value, max_value)

    def make_shrinks():
        return Stream.many(shrinks) if shrinks else Stream.empty()

    return Shrinkable(value, make_shrinks)


def binary_search_shrinkable(value: int) -> Shrinkable[int]:
    """
    Create a shrinkable for an integer using binary search towards 0.
    This is the core function used when the range crosses zero.
    """
    shrinks = _binary_search_towards_zero(value)
    return Shrinkable(
        value, lambda: Stream.many(shrinks) if shrinks else Stream.empty()
    )
