"""Tests for ``python_proptest.core.generator.floating``."""

import unittest

from python_proptest import Gen, for_all


class TestFloatGenerator(unittest.TestCase):
    """Verify floating-point generator behaviour."""

    @for_all(Gen.float(min_value=1.5, max_value=3.5), num_runs=200)
    def test_float_within_bounds(self, value: float):
        """Generated floats stay in the provided interval."""

        self.assertIsInstance(value, float)
        self.assertGreaterEqual(value, 1.5)
        self.assertLessEqual(value, 3.5)

    @for_all(Gen.float(), num_runs=50)
    def test_default_range_allows_broad_values(self, value: float):
        """Default float generator returns floats across large range."""

        self.assertIsInstance(value, float)


if __name__ == "__main__":
    unittest.main()
