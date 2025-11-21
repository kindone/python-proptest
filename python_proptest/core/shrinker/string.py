"""
Shrinker for string types.

Matches cppproptest's shrinkString implementation.
"""

from typing import List
from . import Shrinkable
from .integral import binary_search_shrinkable
from .list import shrinkable_array
from python_proptest.core.stream import Stream


def shrink_string(
    value: str, min_length: int = 0, char_shrinkables: List[Shrinkable[int]] = None
) -> Shrinkable[str]:
    """
    Shrink a string value.

    Args:
        value: The string value to shrink
        min_length: Minimum allowed length
        char_shrinkables: Optional list of Shrinkable[int] for each character code.
            If not provided, will be generated from the string.

    Returns:
        A Shrinkable containing the value and its shrinks.
        Shrinks by length (membership-wise) and by character codes (element-wise).
    """
    if char_shrinkables is None:
        # Generate char shrinkables from string
        char_shrinkables = [binary_search_shrinkable(ord(c)) for c in value]

    # Use shrinkable_array for both membership-wise and element-wise shrinking
    array_shrinkable = shrinkable_array(
        char_shrinkables,
        min_size=min_length,
        membership_wise=True,
        element_wise=True,
    )

    # Map back to string
    return array_shrinkable.map(lambda points: "".join(chr(p) for p in points))


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

