"""Tests for ``python_proptest.core.generator.integral``."""

import unittest

from python_proptest import Gen, PropertyTestError, for_all, run_for_all


class TestIntegralGenerators(unittest.TestCase):
    """Validate integral generator behaviours and shrinking."""

    @for_all(Gen.int(min_value=-50, max_value=50), num_runs=200)
    def test_int_values_within_bounds(self, value):
        """Generated integers should stay within the inclusive range."""

        self.assertIsInstance(value, int)
        self.assertGreaterEqual(value, -50)
        self.assertLessEqual(value, 50)

    def test_int_shrinks_to_minimum_for_positive_range(self):
        """Failing properties shrink towards the configured minimum."""

        generator = Gen.int(min_value=25, max_value=100)

        with self.assertRaises(PropertyTestError) as ctx:
            run_for_all(lambda value: value < 25, generator, num_runs=1)

        error = ctx.exception
        self.assertEqual(error.minimal_inputs[0], 25)
        self.assertGreaterEqual(error.failing_inputs[0], 25)

    @for_all(Gen.in_range(10, 20), num_runs=200)
    def test_in_range_excludes_upper_bound(self, value):
        """``Gen.in_range`` generates values in [min, max)."""

        self.assertIsInstance(value, int)
        self.assertGreaterEqual(value, 10)
        self.assertLess(value, 20)

    def test_in_range_requires_strict_bounds(self):
        """Invalid bounds raise immediately when creating the generator."""

        with self.assertRaises(ValueError):
            Gen.in_range(5, 5)

    @for_all(Gen.ascii_char(), num_runs=200)
    def test_ascii_char_range(self, value):
        """ASCII char generator stays within byte range."""

        self.assertIsInstance(value, int)
        self.assertGreaterEqual(value, 0)
        self.assertLessEqual(value, 127)

    @for_all(Gen.printable_ascii_char(), num_runs=200)
    def test_printable_ascii_char_range(self, value):
        """Printable ASCII char generator avoids control characters."""

        self.assertIsInstance(value, int)
        self.assertGreaterEqual(value, 32)
        self.assertLessEqual(value, 126)

    @for_all(Gen.unicode_char(), num_runs=200)
    def test_unicode_char_skips_surrogate_range(self, value: int):
        """Unicode char generator never yields surrogate code points."""

        self.assertIsInstance(value, int)
        self.assertGreaterEqual(value, 1)
        self.assertLessEqual(value, 0x10FFFF)
        self.assertFalse(0xD800 <= value <= 0xDFFF)


if __name__ == "__main__":
    unittest.main()
