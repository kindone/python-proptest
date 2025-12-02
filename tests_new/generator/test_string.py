"""Tests for ``python_proptest.core.generator.string``."""

import string
import unittest

from python_proptest import Gen, for_all


class TestStringGenerator(unittest.TestCase):
    """Validate string generator constraints and charsets."""

    @for_all(Gen.str(min_length=0, max_length=5), num_runs=200)
    def test_default_charset_values(self, value: str):
        """Default string generator yields lowercase ASCII letters."""

        alphabet = set("abcdefghijklmnopqrstuvwxyz")
        self.assertIsInstance(value, str)
        self.assertLessEqual(len(value), 5)
        self.assertTrue(all(char in alphabet for char in value))

    @for_all(Gen.str(min_length=1, max_length=5, charset="abc123"), num_runs=200)
    def test_custom_charset_is_respected(self, value: str):
        """Custom charset restricts output to declared characters."""

        allowed = set("abc123")
        self.assertIsInstance(value, str)
        self.assertGreaterEqual(len(value), 1)
        self.assertLessEqual(len(value), 5)
        self.assertTrue(all(char in allowed for char in value))

    def test_empty_charset_is_invalid(self):
        """Constructing a generator with an empty charset should fail."""

        with self.assertRaises(ValueError):
            Gen.str(min_length=0, max_length=1, charset="")

    @for_all(Gen.ascii_string(min_length=0, max_length=5), num_runs=200)
    def test_ascii_string_range(self, value: str):
        """ASCII string generator only emits characters below U+0080."""

        self.assertIsInstance(value, str)
        self.assertTrue(all(ord(char) < 128 for char in value))

    @for_all(Gen.printable_ascii_string(min_length=0, max_length=5), num_runs=200)
    def test_printable_ascii_string_range(self, value: str):
        """Printable ASCII generator excludes control characters."""

        printable = set(string.printable)
        self.assertIsInstance(value, str)
        self.assertTrue(all(char in printable and 32 <= ord(char) <= 126 for char in value))

    @for_all(Gen.unicode_string(min_length=2, max_length=4), num_runs=200)
    def test_unicode_string_length_bounds(self, value: str):
        """Unicode string generator respects declared length bounds."""

        self.assertIsInstance(value, str)
        self.assertGreaterEqual(len(value), 2)
        self.assertLessEqual(len(value), 4)


if __name__ == "__main__":
    unittest.main()
