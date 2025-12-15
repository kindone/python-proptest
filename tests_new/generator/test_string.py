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

    @for_all(Gen.str(min_length=3, max_length=8, charset=Gen.int(65, 90)), num_runs=200)
    def test_string_with_codepoint_generator_uppercase(self, s: str):
        """String generator with codepoint generator produces valid characters."""

        self.assertIsInstance(s, str)
        self.assertGreaterEqual(len(s), 3)
        self.assertLessEqual(len(s), 8)
        # All characters should be uppercase letters (codepoints 65-90)
        self.assertTrue(all(c.isupper() and c.isalpha() for c in s))
        self.assertTrue(all(65 <= ord(c) <= 90 for c in s))

    @for_all(Gen.string(min_length=2, max_length=5, charset=Gen.int(97, 122)), num_runs=200)
    def test_string_alias_works(self, s: str):
        """Gen.string is an alias for Gen.str."""

        self.assertIsInstance(s, str)
        self.assertGreaterEqual(len(s), 2)
        self.assertLessEqual(len(s), 5)
        # All characters should be lowercase letters (codepoints 97-122)
        self.assertTrue(all(c.islower() and c.isalpha() for c in s))

    @for_all(Gen.str(min_length=3, max_length=6, charset=Gen.integers(48, 10)), num_runs=200)
    def test_integers_alias_with_codepoint_range(self, s: str):
        """Gen.integers uses start+count semantics for codepoint ranges."""

        self.assertIsInstance(s, str)
        self.assertGreaterEqual(len(s), 3)
        self.assertLessEqual(len(s), 6)
        # Gen.integers(48, 10) generates [48, 58) i.e., codepoints 48-57 (digits '0'-'9')
        self.assertTrue(all(c.isdigit() for c in s))
        self.assertTrue(all(48 <= ord(c) <= 57 for c in s))

    @for_all(Gen.integers(65, 26), num_runs=200)
    def test_integers_generates_codepoint_range(self, codepoint: int):
        """Gen.integers generates integer values in start+count range."""

        # Gen.integers(65, 26) should generate [65, 91) which is A-Z codepoints
        self.assertIsInstance(codepoint, int)
        self.assertGreaterEqual(codepoint, 65)
        self.assertLess(codepoint, 91)
        self.assertTrue(chr(codepoint).isupper())
        self.assertTrue(chr(codepoint).isalpha())

    @for_all(Gen.str(min_length=1, max_length=4, charset=Gen.int(48, 122)), num_runs=200)
    def test_string_with_mixed_codepoint_range(self, s: str):
        """String generator with mixed codepoint range produces valid characters."""

        self.assertIsInstance(s, str)
        self.assertGreaterEqual(len(s), 1)
        self.assertLessEqual(len(s), 4)
        # All characters should be in the codepoint range 48-122
        self.assertTrue(all(48 <= ord(c) <= 122 for c in s))

    @for_all(Gen.union_of(Gen.just("a"), Gen.just("b"), Gen.just("c")), num_runs=200)
    def test_union_of_generates_from_choices(self, value: str):
        """Gen.union_of generates values from provided generators."""

        self.assertIn(value, {"a", "b", "c"})


if __name__ == "__main__":
    unittest.main()
