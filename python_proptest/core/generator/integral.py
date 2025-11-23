"""
Generators for integral types (integers, Unicode character codes).
"""

from typing import List

from ..shrinker import Shrinkable
from ..shrinker.integral import shrink_integral
from ..stream import Stream
from .base import Generator, Random


class IntGenerator(Generator[int]):
    """Generator for integers."""

    def __init__(self, min_value: int, max_value: int):
        self.min_value = min_value
        self.max_value = max_value

    def generate(self, rng: Random) -> Shrinkable[int]:
        value = rng.randint(self.min_value, self.max_value)
        return shrink_integral(value, self.min_value, self.max_value)


class UnicodeCharGenerator(Generator[int]):
    """Generator for Unicode character codes avoiding surrogate pairs."""

    def generate(self, rng: Random) -> Shrinkable[int]:
        """Generate a Unicode character code avoiding surrogate pairs."""
        # Generate a random number in the range [1, 0xD7FF + (0x10FFFF - 0xE000 + 1)]
        # Then map it to avoid surrogate pairs (U+D800 to U+DFFF)
        max_range = 0xD7FF + (0x10FFFF - 0xE000 + 1)
        code = rng.randint(1, max_range)

        # Skip surrogate pair range D800-DFFF
        if code >= 0xD800:
            code += 0xE000 - 0xD800

        shrinks = self._generate_shrinks(code)
        return Shrinkable(code, lambda: Stream.many(shrinks))

    def _generate_shrinks(self, value: int) -> List[Shrinkable[int]]:
        """Generate shrinking candidates for a Unicode character code."""
        shrinks = []

        # Shrink towards 1 (minimum valid Unicode)
        if value > 1:
            shrinks.append(Shrinkable(1))
            if value > 2:
                shrinks.append(Shrinkable(2))

        # Binary search shrinking
        if value > 1:
            mid = (value + 1) // 2
            if mid != value:
                shrinks.append(Shrinkable(mid))

        return shrinks
