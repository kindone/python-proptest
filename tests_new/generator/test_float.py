"""Tests for ``python_proptest.core.generator.floating``."""

import unittest

from python_proptest import Gen, run_for_all


class TestFloatGenerator(unittest.TestCase):
    """Verify floating-point generator behaviour."""

    def test_float_within_bounds(self):
        """Generated floats stay in the provided interval."""

        run_for_all(
            lambda value: isinstance(value, float) and 1.5 <= value <= 3.5,
            Gen.float(min_value=1.5, max_value=3.5),
            num_runs=200,
        )

    def test_default_range_allows_broad_values(self):
        """Default float generator returns floats across large range."""

        run_for_all(lambda value: isinstance(value, float), Gen.float(), num_runs=50)


if __name__ == "__main__":
    unittest.main()
