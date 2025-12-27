"""
Tests for the new string generators that match the original Dart project.
"""

import random
import unittest

from python_proptest import Gen, run_for_all


class TestNewStringGenerators(unittest.TestCase):
    """Test the new string generators that match the original Dart project."""

    def test_ascii_string_generator(self):
        """Test Gen.ascii_string generates ASCII strings (0-127)."""
        result = run_for_all(
            lambda s: all(0 <= ord(c) <= 127 for c in s),
            Gen.ascii_string(min_length=1, max_length=10),
        )
        assert result is True

    def test_printable_ascii_string_generator(self):
        """Test Gen.printable_ascii_string generates printable ASCII strings (32-126)."""
        result = run_for_all(
            lambda s: all(32 <= ord(c) <= 126 for c in s),
            Gen.printable_ascii_string(min_length=1, max_length=10),
        )
        assert result is True

    def test_ascii_char_generator(self):
        """Test Gen.ascii_char generates ASCII character codes (0-127)."""
        result = run_for_all(lambda c: 0 <= c <= 127, Gen.ascii_char())
        assert result is True

    def test_unicode_char_generator(self):
        """Test Gen.unicode_char generates Unicode character codes (avoiding surrogate pairs)."""
        result = run_for_all(
            lambda c: (1 <= c <= 0xD7FF) or (0xE000 <= c <= 0x10FFFF),
            Gen.unicode_char(),
        )
        assert result is True

    def test_printable_ascii_char_generator(self):
        """Test Gen.printable_ascii_char generates printable ASCII character codes (32-126)."""
        result = run_for_all(lambda c: 32 <= c <= 126, Gen.printable_ascii_char())
        assert result is True

    def test_ascii_string_vs_regular_string(self):
        """Test that ascii_string generates different characters than regular string generator."""
        # Generate some ASCII strings
        ascii_samples = []
        for _ in range(10):
            rng = random.Random(42 + _)
            shrinkable = Gen.ascii_string(min_length=5, max_length=5).generate(rng)
            ascii_samples.append(shrinkable.value)

        # Generate some regular strings
        regular_samples = []
        for _ in range(10):
            rng = random.Random(42 + _)
            shrinkable = Gen.str(min_length=5, max_length=5).generate(rng)
            regular_samples.append(shrinkable.value)

        # ASCII strings should contain characters with codes 0-127
        for sample in ascii_samples:
            for char in sample:
                assert (
                    0 <= ord(char) <= 127
                ), f"Character {char} (ord={ord(char)}) not in ASCII range"

        # Regular strings should only contain lowercase letters
        for sample in regular_samples:
            for char in sample:
                assert char.islower(), f"Character {char} not lowercase"

    def test_printable_ascii_string_content(self):
        """Test that printable_ascii_string generates only printable characters."""
        result = run_for_all(
            lambda s: all(c.isprintable() for c in s),
            Gen.printable_ascii_string(min_length=1, max_length=10),
        )
        assert result is True

    def test_unicode_char_avoids_surrogate_pairs(self):
        """Test that unicode_char avoids surrogate pair range (U+D800 to U+DFFF)."""
        result = run_for_all(lambda c: not (0xD800 <= c <= 0xDFFF), Gen.unicode_char())
        assert result is True

    def test_character_generators_produce_different_ranges(self):
        """Test that different character generators produce different ranges."""
        # Test ascii_char
        ascii_result = run_for_all(lambda c: 0 <= c <= 127, Gen.ascii_char())
        assert ascii_result is True

        # Test printable_ascii_char
        printable_result = run_for_all(
            lambda c: 32 <= c <= 126, Gen.printable_ascii_char()
        )
        assert printable_result is True

        # Test unicode_char
        unicode_result = run_for_all(
            lambda c: (1 <= c <= 0xD7FF) or (0xE000 <= c <= 0x10FFFF),
            Gen.unicode_char(),
        )
        assert unicode_result is True

    def test_in_range_generator(self):
        """Test Gen.in_range generates integers in exclusive range."""
        result = run_for_all(
            lambda x: 0 <= x < 10,  # Should be [0, 10) - exclusive of 10
            Gen.in_range(0, 10),
        )
        assert result is True

    def test_in_range_vs_interval(self):
        """Test that in_range and interval produce different ranges."""
        # in_range(0, 10) should produce [0, 9]
        in_range_result = run_for_all(lambda x: 0 <= x <= 9, Gen.in_range(0, 10))
        assert in_range_result is True

        # interval(0, 10) should produce [0, 10]
        interval_result = run_for_all(lambda x: 0 <= x <= 10, Gen.interval(0, 10))
        assert interval_result is True

    def test_unique_list_generator(self):
        """Test Gen.unique_list generates lists with unique elements."""
        result = run_for_all(
            lambda lst: len(lst) == len(set(lst)),  # All elements should be unique
            Gen.unique_list(
                Gen.int(min_value=1, max_value=5), min_length=1, max_length=3
            ),
        )
        assert result is True

    def test_unique_list_is_sorted(self):
        """Test that unique_list generates sorted lists."""
        result = run_for_all(
            lambda lst: lst == sorted(lst),  # Should be sorted
            Gen.unique_list(
                Gen.int(min_value=1, max_value=10), min_length=2, max_length=5
            ),
        )
        assert result is True


if __name__ == "__main__":
    unittest.main()
