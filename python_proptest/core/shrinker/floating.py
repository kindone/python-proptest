"""
Shrinker for floating point values.

Matches cppproptest's shrinkFloat implementation using frexp/ldexp
to decompose floats into fraction and exponent.
"""

import math
import sys
from typing import Tuple, TypeVar

from python_proptest.core.stream import Stream

from . import Shrinkable
from .integral import shrink_integral

FLOATTYPE = TypeVar("FLOATTYPE", float, float)


def _decompose_float(value: float) -> Tuple[float, int]:
    """
    Decompose a float into fraction and exponent using frexp.

    Returns:
        Tuple of (fraction, exponent) where value = fraction * 2^exponent
        and 0.5 <= abs(fraction) < 1.0 (or fraction == 0.0)
    """
    return math.frexp(value)


def _compose_float(fraction: float, exp: int) -> float:
    """
    Compose a float from fraction and exponent using ldexp.

    Returns:
        fraction * 2^exp
    """
    return math.ldexp(fraction, exp)


def _float_shrinks_impl(value: float) -> Stream[Shrinkable[float]]:
    """
    Generate shrinks for a float value.

    Matches cppproptest's floatShrinksImpl implementation:
    1. Handles special cases (0.0, NaN, infinity)
    2. Decomposes float into fraction and exponent
    3. Shrinks the exponent using shrinkIntegral
    4. Prepends 0.0
    5. Shrinks fraction to 0.5/-0.5
    6. "Integerfies" by converting to int if closer to zero
    """
    if value == 0.0:
        return Stream.empty()
    elif math.isnan(value):
        return Stream.one(Shrinkable(0.0))
    else:
        # Handle infinity
        if math.isinf(value):
            if value > 0:
                max_val = sys.float_info.max
                fraction, exp = _decompose_float(max_val)
            else:
                min_val = sys.float_info.min
                fraction, exp = _decompose_float(min_val)
        else:
            fraction, exp = _decompose_float(value)

        # Shrink exponent using shrinkIntegral
        exp_shrinkable = shrink_integral(exp)

        # Map exponent shrinks to float values
        def compose_from_exp(exp_val: int) -> float:
            return _compose_float(fraction, exp_val)

        float_shrinkable = exp_shrinkable.map(compose_from_exp)

        # Prepend 0.0 (capture original shrinks before modifying)
        original_shrinks = float_shrinkable.shrinks()
        zero_shrinkable = Shrinkable(0.0)
        float_shrinkable = float_shrinkable.with_shrinks(
            lambda: Stream.one(zero_shrinkable).concat(original_shrinks)
        )

        # Shrink fraction to 0.5/-0.5
        def shrink_fraction(shr: Shrinkable[float]) -> Stream[Shrinkable[float]]:
            val = shr.value
            if val == 0.0:
                return Stream.empty()
            _, exp = _decompose_float(val)
            if val > 0:
                return Stream.one(Shrinkable(_compose_float(0.5, exp)))
            else:
                return Stream.one(Shrinkable(_compose_float(-0.5, exp)))

        float_shrinkable = float_shrinkable.and_then(shrink_fraction)

        # "Integerfy" - convert to int if closer to zero
        def integerfy(shr: Shrinkable[float]) -> Stream[Shrinkable[float]]:
            val = shr.value
            int_val = int(val)
            if int_val != 0 and abs(int_val) < abs(val):
                return Stream.one(Shrinkable(float(int_val)))
            else:
                return Stream.empty()

        float_shrinkable = float_shrinkable.and_then(integerfy)

        return float_shrinkable.shrinks()


def shrink_float(value: float) -> Shrinkable[float]:
    """
    Shrink a float value.

    Args:
        value: The float value to shrink

    Returns:
        A Shrinkable containing the value and its shrinks.
        Matches cppproptest's shrinkFloat implementation.
    """
    return Shrinkable(value, lambda: _float_shrinks_impl(value))
