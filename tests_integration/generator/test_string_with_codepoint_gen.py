"""Test string generators with codepoint generators."""

import unittest

from python_proptest import Gen, for_all


class TestUnionOfAlias(unittest.TestCase):
    """Test Gen.union_of() alias matching cppproptest's gen::unionOf."""

    @for_all(Gen.union_of(Gen.just("a"), Gen.just("b"), Gen.just("c")))
    def test_union_of_generates_from_choices(self, value: str):
        """Property: Gen.union_of() generates values from provided generators."""
        assert value in {"a", "b", "c"}


class TestStringWithCodepointGenerator(unittest.TestCase):
    """Test string generator with integer codepoint generators."""

    @for_all(Gen.str(min_length=3, max_length=8, charset=Gen.int(65, 90)))
    def test_string_with_codepoint_generator_uppercase(self, s: str):
        """Test string generator with uppercase letter codepoints (A-Z)."""
        self.assertTrue(3 <= len(s) <= 8)
        # Check that all characters are uppercase letters
        self.assertTrue(all(c.isupper() and c.isalpha() for c in s))
        self.assertTrue(all(65 <= ord(c) <= 90 for c in s))

    @for_all(Gen.string(min_length=2, max_length=5, charset=Gen.int(97, 122)))
    def test_string_alias_works(self, s: str):
        """Test that Gen.string is an alias for Gen.str."""
        self.assertTrue(2 <= len(s) <= 5)
        # Check that all characters are lowercase letters
        self.assertTrue(all(c.islower() and c.isalpha() for c in s))

    @for_all(Gen.str(min_length=3, max_length=6, charset=Gen.integers(48, 10)))
    def test_integers_alias_works(self, s: str):
        """Test that Gen.integers uses start+count semantics (cppproptest style)."""
        self.assertTrue(3 <= len(s) <= 6)
        # Gen.integers(48, 10) generates [48, 58) i.e., codepoints 48-57 (digits '0'-'9')
        self.assertTrue(all(c.isdigit() for c in s))
        self.assertTrue(all(48 <= ord(c) <= 57 for c in s))

    @for_all(Gen.integers(65, 26))
    def test_integers_generates_uppercase_letters(self, codepoint: int):
        """Test Gen.integers(65, 26) generates A-Z codepoints."""
        # Gen.integers(65, 26) should generate [65, 91) which is A-Z
        self.assertTrue(65 <= codepoint <= 90)
        self.assertTrue(chr(codepoint).isupper())
        self.assertTrue(chr(codepoint).isalpha())

    @for_all(Gen.str(min_length=1, max_length=4, charset=Gen.int(48, 122)))
    def test_string_with_mixed_codepoint_range(self, s: str):
        """Test string generator with mixed character ranges."""
        self.assertTrue(1 <= len(s) <= 4)
        # All characters should be in the codepoint range 48-122
        self.assertTrue(all(48 <= ord(c) <= 122 for c in s))

    @for_all(Gen.str(min_length=2, max_length=5, charset="xyz"))
    def test_backward_compatibility_string_charset(self, s: str):
        """Test that string charset still works (backward compatibility)."""
        self.assertTrue(2 <= len(s) <= 5)
        # Check that all characters are in charset
        self.assertTrue(all(c in "xyz" for c in s))

    @for_all(Gen.str(min_length=0, max_length=5, charset=Gen.int(65, 90)))
    def test_all_chars_in_valid_range(self, s: str):
        """Test that all generated characters are in the valid codepoint range."""
        self.assertTrue(0 <= len(s) <= 5)
        # All characters should be uppercase letters
        for c in s:
            self.assertTrue(65 <= ord(c) <= 90)
            self.assertTrue(c.isupper() and c.isalpha())


class TestStringCodepointShrinking(unittest.TestCase):
    """Property-based tests verifying shrinking preserves charset constraints."""

    @for_all(Gen.str(min_length=0, max_length=5, charset=Gen.int(65, 90)))
    def test_shrinking_with_codepoint_generator(self, original_value: str):
        """Property: All generated strings from codepoint generator stay within range (A-Z)."""
        # Verify all characters are uppercase letters A-Z (codepoints 65-90)
        assert all(65 <= ord(c) <= 90 for c in original_value)

    @for_all(Gen.str(min_length=0, max_length=5, charset="xyz"))
    def test_shrinking_with_string_charset(self, original_value: str):
        """Property: All generated strings from string charset stay within charset."""
        # Verify all characters are in the charset
        assert all(c in "xyz" for c in original_value)

    @for_all(Gen.str(min_length=1, max_length=4, charset=Gen.integers(48, 10)))
    def test_shrinking_digits_codepoint_generator(self, original_value: str):
        """Property: All generated strings from digit codepoint generator remain digits."""
        # Verify all characters are digits (codepoints 48-57, i.e., '0'-'9')
        assert all(c.isdigit() for c in original_value)
        assert all(48 <= ord(c) <= 57 for c in original_value)


class TestStringCodepointShrinkingManual(unittest.TestCase):
    """Manual tests verifying shrunk values maintain charset constraints."""

    def test_shrinking_preserves_codepoint_constraints(self):
        """Test that shrinking preserves codepoint generator constraints (A-Z)."""
        import random

        rng = random.Random(42)
        string_gen = Gen.str(min_length=0, max_length=5, charset=Gen.int(65, 90))

        # Generate several strings and verify all shrinks stay in range
        for _ in range(10):
            shrinkable = string_gen.generate(rng)
            original_value = shrinkable.value

            # Verify original is valid
            self.assertTrue(all(65 <= ord(c) <= 90 for c in original_value))

            # Check all shrinks maintain constraints
            shrinks_stream = shrinkable.shrinks()
            shrink_count = 0
            while not shrinks_stream.is_empty() and shrink_count < 20:
                shrunk = shrinks_stream.head()
                shrunk_value = shrunk.value

                # Shrunk value should be shorter or same length
                self.assertTrue(len(shrunk_value) <= len(original_value))
                # All characters should still be in valid range
                for c in shrunk_value:
                    self.assertTrue(
                        65 <= ord(c) <= 90,
                        f"Shrunk char '{c}' (codepoint {ord(c)}) not in range 65-90",
                    )

                shrinks_stream = shrinks_stream.tail()
                shrink_count += 1

    def test_shrinking_preserves_string_charset(self):
        """Test that shrinking preserves string charset constraints."""
        import random

        rng = random.Random(100)
        string_gen = Gen.str(min_length=0, max_length=5, charset="xyz")

        # Generate several strings and verify all shrinks stay in charset
        for _ in range(10):
            shrinkable = string_gen.generate(rng)
            original_value = shrinkable.value

            # Verify original is valid
            self.assertTrue(all(c in "xyz" for c in original_value))

            # Check all shrinks maintain charset
            shrinks_stream = shrinkable.shrinks()
            shrink_count = 0
            while not shrinks_stream.is_empty() and shrink_count < 20:
                shrunk = shrinks_stream.head()
                shrunk_value = shrunk.value

                # Shrunk value should be shorter or same length
                self.assertTrue(len(shrunk_value) <= len(original_value))
                # All characters should still be in charset
                for c in shrunk_value:
                    self.assertIn(c, "xyz", f"Shrunk char '{c}' not in charset 'xyz'")

                shrinks_stream = shrinks_stream.tail()
                shrink_count += 1

    def test_shrinking_preserves_digit_constraints(self):
        """Test that shrinking preserves digit codepoint constraints."""
        import random

        rng = random.Random(200)
        # Gen.integers(48, 10) generates [48, 58) i.e., codepoints 48-57 (digits '0'-'9')
        string_gen = Gen.str(min_length=1, max_length=4, charset=Gen.integers(48, 10))

        # Generate several strings and verify all shrinks stay in digit range
        for _ in range(10):
            shrinkable = string_gen.generate(rng)
            original_value = shrinkable.value

            # Verify original is valid
            self.assertTrue(all(c.isdigit() for c in original_value))

            # Check all shrinks maintain digit constraint
            shrinks_stream = shrinkable.shrinks()
            shrink_count = 0
            while not shrinks_stream.is_empty() and shrink_count < 20:
                shrunk = shrinks_stream.head()
                shrunk_value = shrunk.value

                # All characters should still be digits
                for c in shrunk_value:
                    self.assertTrue(c.isdigit(), f"Shrunk char '{c}' is not a digit")
                    self.assertTrue(
                        48 <= ord(c) <= 57,
                        f"Shrunk char '{c}' (codepoint {ord(c)}) not in range 48-57",
                    )

                shrinks_stream = shrinks_stream.tail()
                shrink_count += 1


if __name__ == "__main__":
    unittest.main()
