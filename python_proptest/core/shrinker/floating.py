"""
Shrinker for floating point values.

Note: This is a simplified implementation. cppproptest uses a more sophisticated
approach with frexp/ldexp to decompose floats into fraction and exponent.
"""

from python_proptest.core.stream import Stream

from . import Shrinkable


def shrink_float(value: float) -> Shrinkable[float]:
    """
    Shrink a float value.

    Args:
        value: The float value to shrink

    Returns:
        A Shrinkable containing the value and its shrinks.
        Shrinks towards zero, and uses binary search for values > 1.0.
    """
    shrinks = []

    # Shrink towards zero
    if value > 0:
        shrinks.append(Shrinkable(0.0))
    elif value < 0:
        shrinks.append(Shrinkable(0.0))

    # Binary search shrinking
    if abs(value) > 1.0:
        shrinks.append(Shrinkable(value / 2))
        shrinks.append(Shrinkable(-value / 2))

    return Shrinkable(
        value, lambda: Stream.many(shrinks) if shrinks else Stream.empty()
    )
