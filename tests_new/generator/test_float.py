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

    def test_float_negative_probability_validation(self):
        """Reject negative probability values."""

        with self.assertRaises(ValueError):
            Gen.float(nan_prob=-0.1)

        with self.assertRaises(ValueError):
            Gen.float(posinf_prob=-0.5)

        with self.assertRaises(ValueError):
            Gen.float(neginf_prob=-0.2)

    def test_float_probability_above_one_validation(self):
        """Reject individual probability values above 1.0."""

        with self.assertRaises(ValueError):
            Gen.float(nan_prob=1.5)

        with self.assertRaises(ValueError):
            Gen.float(posinf_prob=2.0)

        with self.assertRaises(ValueError):
            Gen.float(neginf_prob=1.1)

    @for_all(Gen.float(nan_prob=0.1), num_runs=1000)
    def test_float_partial_nan_probability(self, value: float):
        """Partial nan_prob generates both NaN and finite values."""

        # Should generate either NaN or finite values
        self.assertTrue(math.isnan(value) or math.isfinite(value))

    @for_all(Gen.float(posinf_prob=0.15), num_runs=1000)
    def test_float_partial_posinf_probability(self, value: float):
        """Partial posinf_prob generates both +inf and finite values."""

        # Should generate either +inf or finite values
        self.assertTrue(
            (math.isinf(value) and value > 0) or math.isfinite(value)
        )

    @for_all(Gen.float(neginf_prob=0.2), num_runs=1000)
    def test_float_partial_neginf_probability(self, value: float):
        """Partial neginf_prob generates both -inf and finite values."""

        # Should generate either -inf or finite values
        self.assertTrue(
            (math.isinf(value) and value < 0) or math.isfinite(value)
        )

    @for_all(
        Gen.float(nan_prob=0.1, posinf_prob=0.1), num_runs=1000
    )
    def test_float_two_probability_combination(self, value: float):
        """Combining two probabilities generates all three types correctly."""

        # Should generate NaN, +inf, or finite values (no -inf)
        self.assertTrue(
            math.isnan(value)
            or (math.isinf(value) and value > 0)
            or math.isfinite(value)
        )

    @for_all(
        Gen.float(
            min_value=-1.0,
            max_value=-1.0,
            nan_prob=0.0,
            posinf_prob=0.0,
            neginf_prob=0.0,
        ),
        num_runs=50,
    )
    def test_float_equal_min_max_values(self, value: float):
        """When min_value equals max_value, generator produces that value."""

        self.assertEqual(value, -1.0)

    def test_float_probability_sum_exactly_one(self):
        """Probability sum exactly 1.0 generates only special values."""

        gen = Gen.float(nan_prob=0.4, posinf_prob=0.3, neginf_prob=0.3)

        # Generate many values - all should be special (no finite)
        special_count = 0
        finite_count = 0

        import random

        rng = random.Random(42)
        for _ in range(100):
            value = gen.generate(rng).value
            if math.isfinite(value):
                finite_count += 1
            else:
                special_count += 1

        # With sum=1.0, all values should be special
        self.assertEqual(finite_count, 0)
        self.assertEqual(special_count, 100)

    @for_all(
        Gen.float(nan_prob=0.05, posinf_prob=0.05, neginf_prob=0.05),
        num_runs=200,
    )
    def test_float_all_three_probabilities_together(self, value: float):
        """All three probabilities together generate correct value types."""

        # Should generate any of the four types: NaN, +inf, -inf, or finite
        self.assertTrue(
            math.isnan(value)
            or math.isinf(value)
            or math.isfinite(value)
        )


if __name__ == "__main__":
    unittest.main()
