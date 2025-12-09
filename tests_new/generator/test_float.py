"""Tests for ``python_proptest.core.generator.floating``."""

import math
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

    @for_all(Gen.float(), num_runs=200)
    def test_default_range_produces_finite_values(self, value: float):
        """Default float generator returns finite floats even across broad range."""

        self.assertIsInstance(value, float)
        self.assertTrue(math.isfinite(value))

    @for_all(Gen.float(nan_prob=1.0), num_runs=20)
    def test_float_can_generate_nan(self, value: float):
        """Setting nan_prob=1 forces NaN outputs."""

        self.assertTrue(math.isnan(value))

    @for_all(Gen.float(posinf_prob=1.0), num_runs=20)
    def test_float_can_generate_posinf(self, value: float):
        """Setting posinf_prob=1 forces +inf outputs."""

        self.assertTrue(math.isinf(value))
        self.assertGreater(value, 0.0)

    @for_all(Gen.float(neginf_prob=1.0), num_runs=20)
    def test_float_can_generate_neginf(self, value: float):
        """Setting neginf_prob=1 forces -inf outputs."""

        self.assertTrue(math.isinf(value))
        self.assertLess(value, 0.0)

    @for_all(Gen.float(min_value=-2.5, max_value=2.5, nan_prob=0.1, posinf_prob=0.1, neginf_prob=0.1), num_runs=200)
    def test_float_with_special_probabilities_respects_bounds(self, value: float):
        """Finite draws stay in range even when special probabilities are present."""

        if math.isfinite(value):
            self.assertGreaterEqual(value, -2.5)
            self.assertLessEqual(value, 2.5)
        else:
            self.assertTrue(math.isnan(value) or math.isinf(value))

    def test_float_probability_sum_validation(self):
        """Reject probability totals above 1.0."""

        with self.assertRaises(ValueError):
            Gen.float(nan_prob=0.6, posinf_prob=0.3, neginf_prob=0.2)


if __name__ == "__main__":
    unittest.main()
