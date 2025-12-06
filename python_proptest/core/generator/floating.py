"""
Generator for floating point values.

Python's float is 64-bit (IEEE 754 double precision), equivalent to C++ double.

By default, generates only finite values. Can optionally generate inf and NaN
with specified probabilities.
"""

import math
import struct
import sys
from typing import TYPE_CHECKING, Optional, Union

from ..shrinker import Shrinkable
from ..shrinker.floating import shrink_float
from .base import Generator, Random

if TYPE_CHECKING:
    from ..combinator.one_of import OneOfGenerator


class FiniteFloatGenerator(Generator[float]):
    """
    Generator for finite float values only.

    Uses bit interpretation with rejection loop to ensure finite values.
    Covers the full finite float space including denormals.
    """

    def __init__(self, min_value: float, max_value: float):
        self.min_value = min_value
        self.max_value = max_value
        # Check if we're using the default full range (bit interpretation mode)
        self._use_bit_interpretation = (
            min_value == -sys.float_info.max and max_value == sys.float_info.max
        )

    def generate(self, rng: Random) -> Shrinkable[float]:
        """
        Generate a finite float.

        If using default range (full float range), uses bit interpretation
        with rejection loop to ensure finite values.

        If explicit min/max are provided, generates finite values in that range.
        """
        if self._use_bit_interpretation:
            # Generate using bit interpretation with rejection loop
            # Reject inf/NaN until we get a finite value
            while True:
                # Generate random 64-bit unsigned integer
                raw_bits = rng.randint(0, 2**64 - 1)

                # Interpret bits as double (like C++ reinterpret_cast<double*>(&raw))
                value = struct.unpack("d", struct.pack("Q", raw_bits))[0]

                # Reject inf/NaN and retry
                if math.isfinite(value):
                    break
        else:
            # Generate finite value in specified range
            value = rng.random() * (self.max_value - self.min_value) + self.min_value
            # Ensure it's finite (clamp if needed)
            if not math.isfinite(value):
                # Fallback to midpoint if range calculation overflowed
                value = (self.min_value + self.max_value) / 2.0

        return shrink_float(value)


class FloatGenerator(Generator[float]):
    """
    Generator for floats with optional inf/NaN probabilities.

    Python's float is 64-bit (IEEE 754 double precision), equivalent to C++ double.

    By default (all probabilities = 0), generates only finite values.
    Can optionally generate +inf, -inf, and NaN with specified probabilities.
    """

    def __init__(
        self,
        min_value: float,
        max_value: float,
        nan_prob: float = 0.0,
        posinf_prob: float = 0.0,
        neginf_prob: float = 0.0,
    ):
        # Validate probabilities
        if not (0.0 <= nan_prob <= 1.0):
            raise ValueError(f"nan_prob must be between 0.0 and 1.0, got {nan_prob}")
        if not (0.0 <= posinf_prob <= 1.0):
            raise ValueError(
                f"posinf_prob must be between 0.0 and 1.0, got {posinf_prob}"
            )
        if not (0.0 <= neginf_prob <= 1.0):
            raise ValueError(
                f"neginf_prob must be between 0.0 and 1.0, got {neginf_prob}"
            )

        total_prob = nan_prob + posinf_prob + neginf_prob
        if total_prob > 1.0:
            raise ValueError(
                f"Sum of probabilities (nan_prob + posinf_prob + neginf_prob) must be <= 1.0, got {total_prob}"
            )

        self.min_value = min_value
        self.max_value = max_value
        self.nan_prob = nan_prob
        self.posinf_prob = posinf_prob
        self.neginf_prob = neginf_prob

        # If all probabilities are 0, use finite-only generator directly
        if nan_prob == 0.0 and posinf_prob == 0.0 and neginf_prob == 0.0:
            self._finite_gen: FiniteFloatGenerator = FiniteFloatGenerator(
                min_value, max_value
            )
            self._one_of_gen: Optional["OneOfGenerator[float]"] = None
            self._use_one_of = False
        else:
            # Use one_of internally with weighted generators
            from ..combinator.just import JustGenerator
            from ..combinator.one_of import OneOfGenerator
            from .base import Weighted

            generators = []
            finite_prob = 1.0 - total_prob

            # Add special value generators with their probabilities
            if nan_prob > 0.0:
                generators.append(Weighted(JustGenerator(float("nan")), nan_prob))
            if posinf_prob > 0.0:
                generators.append(Weighted(JustGenerator(float("inf")), posinf_prob))
            if neginf_prob > 0.0:
                generators.append(Weighted(JustGenerator(float("-inf")), neginf_prob))

            # Add finite generator with remaining probability
            if finite_prob > 0.0:
                generators.append(
                    Weighted(FiniteFloatGenerator(min_value, max_value), finite_prob)
                )

            self._one_of_gen = OneOfGenerator(generators)
            self._finite_gen = None  # type: ignore[assignment]
            self._use_one_of = True

    def generate(self, rng: Random) -> Shrinkable[float]:
        """
        Generate a float.

        If all probabilities are 0, generates only finite values.
        Otherwise, uses one_of internally to select between finite values
        and special values (inf, -inf, NaN) based on probabilities.
        """
        if self._use_one_of:
            if self._one_of_gen is None:
                raise RuntimeError(
                    "Internal error: one_of_gen is None when _use_one_of is True"
                )
            return self._one_of_gen.generate(rng)
        else:
            if self._finite_gen is None:
                raise RuntimeError(
                    "Internal error: finite_gen is None when _use_one_of is False"
                )
            return self._finite_gen.generate(rng)
