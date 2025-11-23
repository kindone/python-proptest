"""
Shrinker for string types.

Matches cppproptest's shrinkString implementation.
Only shrinks by length (prefixes and suffixes), NOT by character codes.
"""

from typing import List

from python_proptest.core.stream import Stream

from . import Shrinkable
from .integral import binary_search_shrinkable, shrink_integral
from .list import shrinkable_array


def shrink_string(
    value: str, min_length: int = 0, char_shrinkables: List[Shrinkable[int]] = None
) -> Shrinkable[str]:
    """
    Shrink a string value by length only (prefixes and suffixes).

    Matches cppproptest's shrinkString implementation:
    - Shrinks rear (prefixes): "", "a", "ab", ...
    - Shrinks front (suffixes): for each prefix, generates suffixes by removing from front
    - Does NOT shrink character codes (element-wise shrinking is not used)

    Args:
        value: The string value to shrink
        min_length: Minimum allowed length
        char_shrinkables: Ignored (kept for backward compatibility, but not used)

    Returns:
        A Shrinkable containing the value and its shrinks.
        Only shrinks by length, not by character codes.
    """
    size = len(value)

    # Step 1: Shrink rear (prefixes)
    # shrinkIntegral(size - min_length) -> map to substr(0, size + min_length)
    size_shrinkable = shrink_integral(
        size - min_length, min_value=0, max_value=size - min_length
    )

    def create_prefix(the_size: int) -> str:
        return value[: the_size + min_length]

    shrink_rear = size_shrinkable.map(create_prefix)

    # Step 2: Shrink front (for each rear shrink, remove from front)
    # This generates suffixes by removing characters from the beginning
    def shrink_front(parent: Shrinkable[str]) -> Stream[Shrinkable[str]]:
        str_val = parent.value
        str_size = len(str_val)
        if str_size <= min_length + 1:
            return Stream.empty()

        # shrinkIntegral(str_size - (min_length + 1))
        front_size_shrinkable = shrink_integral(
            str_size - (min_length + 1),
            min_value=0,
            max_value=str_size - (min_length + 1),
        )

        def create_suffix(front_offset: int) -> str:
            start = min_length + 1 + front_offset
            end = str_size
            return str_val[start:end]

        return front_size_shrinkable.map(create_suffix).shrinks()

    return shrink_rear.concat(shrink_front)


def shrink_unicode_string(
    value: str, min_length: int = 0, char_shrinkables: List[Shrinkable[int]] = None
) -> Shrinkable[str]:
    """
    Shrink a Unicode string value.

    Args:
        value: The Unicode string value to shrink
        min_length: Minimum allowed length
        char_shrinkables: Optional list of Shrinkable[int] for each Unicode codepoint.
            If not provided, will be generated from the string.

    Returns:
        A Shrinkable containing the value and its shrinks.
        Shrinks by length (membership-wise) and by codepoints (element-wise).
    """
    if char_shrinkables is None:
        # Generate codepoint shrinkables from string
        char_shrinkables = []
        for c in value:
            codepoint = ord(c)
            # Handle surrogate pairs
            if codepoint >= 0xD800 and codepoint < 0xE000:
                codepoint += 0xE000 - 0xD800
            char_shrinkables.append(binary_search_shrinkable(codepoint))

    # Use shrinkable_array for both membership-wise and element-wise shrinking
    array_shrinkable = shrinkable_array(
        char_shrinkables,
        min_size=min_length,
        membership_wise=True,
        element_wise=True,
    )

    # Map back to string, handling invalid codepoints
    def to_string(points: List[int]) -> str:
        result_chars = []
        for point in points:
            try:
                result_chars.append(chr(point))
            except ValueError:
                result_chars.append("?")
        return "".join(result_chars)

    return array_shrinkable.map(to_string)
