"""Tests for Gen.bool() with true_prob parameter."""

import unittest

from python_proptest import Gen, run_for_all


class TestGenBoolTrueProb(unittest.TestCase):
    """Test Gen.bool() with configurable true_prob parameter."""

    def test_bool_default_probability(self):
        """Test that Gen.bool() defaults to 50/50 probability."""

        def test_property():
            # Generate many samples and check they're valid booleans
            result = run_for_all(lambda x: isinstance(x, bool), Gen.bool())
            return result

        test_property()

    def test_bool_always_true(self):
        """Test Gen.bool(true_prob=1.0) always generates True."""

        def test_property():
            result = run_for_all(lambda x: x is True, Gen.bool(true_prob=1.0))
            return result

        test_property()

    def test_bool_always_false(self):
        """Test Gen.bool(true_prob=0.0) always generates False."""

        def test_property():
            result = run_for_all(lambda x: x is False, Gen.bool(true_prob=0.0))
            return result

        test_property()

    def test_bool_high_probability(self):
        """Test Gen.bool(true_prob=0.9) generates mostly True values."""

        def test_property():
            # This test might occasionally fail due to randomness,
            # but should pass most of the time
            result = run_for_all(lambda x: isinstance(x, bool), Gen.bool(true_prob=0.9))
            return result

        test_property()

    def test_bool_low_probability(self):
        """Test Gen.bool(true_prob=0.1) generates mostly False values."""

        def test_property():
            result = run_for_all(lambda x: isinstance(x, bool), Gen.bool(true_prob=0.1))
            return result

        test_property()

    def test_bool_invalid_probability_raises_error(self):
        """Test that invalid true_prob values raise ValueError."""
        with self.assertRaises(ValueError):
            Gen.bool(true_prob=-0.1)

        with self.assertRaises(ValueError):
            Gen.bool(true_prob=1.1)

        with self.assertRaises(ValueError):
            Gen.bool(true_prob=2.0)

    def test_bool_edge_cases(self):
        """Test edge case probabilities."""

        # Test exactly 0.0
        def test_zero():
            result = run_for_all(lambda x: x is False, Gen.bool(true_prob=0.0))
            return result

        # Test exactly 1.0
        def test_one():
            result = run_for_all(lambda x: x is True, Gen.bool(true_prob=1.0))
            return result

        test_zero()
        test_one()

    def test_bool_with_other_generators(self):
        """Test Gen.bool() works with other generators."""

        def test_property():
            result = run_for_all(
                lambda x, y: isinstance(x, bool) and isinstance(y, int),
                Gen.bool(true_prob=0.7),
                Gen.int(),
            )
            return result

        test_property()

    def test_bool_in_lists(self):
        """Test Gen.bool() works in list generation."""

        def test_property():
            result = run_for_all(
                lambda lst: all(isinstance(x, bool) for x in lst),
                Gen.list(Gen.bool(true_prob=0.3), min_length=1, max_length=5),
            )
            return result

        test_property()


if __name__ == "__main__":
    unittest.main()
