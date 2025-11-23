"""
Generators for string types.
"""

from typing import List

from ..shrinker import Shrinkable
from ..shrinker.integral import binary_search_shrinkable
from ..shrinker.list import shrinkable_array
from .base import Generator, Random


class StringGenerator(Generator[str]):
    """Generator for strings."""

    def __init__(self, min_length: int, max_length: int, charset: str):
        self.min_length = min_length
        self.max_length = max_length
        self.charset = self._get_charset(charset)
        if not self.charset:
            raise ValueError("Charset must contain at least one character")
        # Preserve order but ensure uniqueness for deterministic shrinking
        self._charset_list = list(dict.fromkeys(self.charset))
        self._charset_len = len(self._charset_list)

    def _get_charset(self, charset: str) -> str:
        """Convert charset specification to actual character set."""
        if charset == "ascii":
            # ASCII characters 0-127
            return "".join(chr(i) for i in range(128))
        elif charset == "printable_ascii":
            # Printable ASCII characters 32-126
            return "".join(chr(i) for i in range(32, 127))
        else:
            # Use the provided charset as-is
            return charset

    def _build_indices(self, rng: Random, length: int) -> List[int]:
        return [rng.randrange(self._charset_len) for _ in range(length)]

    def _indices_to_string(self, indices: List[int]) -> str:
        return "".join(self._charset_list[idx] for idx in indices)

    def generate(self, rng: Random) -> Shrinkable[str]:
        length = rng.randint(self.min_length, self.max_length)
        indices = self._build_indices(rng, length)

        char_shrinkables = [binary_search_shrinkable(idx) for idx in indices]
        array_shrinkable = shrinkable_array(
            char_shrinkables,
            min_size=self.min_length,
            membership_wise=True,
            element_wise=True,
        )

        return array_shrinkable.map(self._indices_to_string)


class UnicodeStringGenerator(Generator[str]):
    """Generator for Unicode strings."""

    def __init__(self, min_length: int, max_length: int):
        self.min_length = min_length
        self.max_length = max_length

    def generate(self, rng: Random) -> Shrinkable[str]:
        length = rng.randint(self.min_length, self.max_length)
        codepoints: List[int] = []
        char_shrinkables: List[Shrinkable[int]] = []

        for _ in range(length):
            codepoint = rng.randint(0, 0xFFFF)
            codepoints.append(codepoint)
            char_shrinkables.append(binary_search_shrinkable(codepoint))

        array_shrinkable = shrinkable_array(
            char_shrinkables,
            min_size=self.min_length,
            membership_wise=True,
            element_wise=True,
        )

        def to_string(points: List[int]) -> str:
            result_chars = []
            for point in points:
                try:
                    result_chars.append(chr(point))
                except ValueError:
                    result_chars.append("?")
            return "".join(result_chars)

        return array_shrinkable.map(to_string)
