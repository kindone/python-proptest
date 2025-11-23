"""
Shrinker for boolean values.

Matches cppproptest's shrinkBool implementation.
"""

from python_proptest.core.stream import Stream

from . import Shrinkable


def shrink_bool(value: bool) -> Shrinkable[bool]:
    """
    Shrink a boolean value.

    Args:
        value: The boolean value to shrink

    Returns:
        A Shrinkable containing the value and its shrinks.
        If value is True, shrinks to False. If value is False, no shrinks.
    """
    if value:
        # True can shrink to False
        return Shrinkable(value, lambda: Stream.one(Shrinkable(False)))
    else:
        # False cannot shrink further
        return Shrinkable(value, lambda: Stream.empty())
