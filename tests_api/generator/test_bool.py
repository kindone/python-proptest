"""Tests for ``python_proptest.core.generator.bool``."""

import unittest

from python_proptest import Gen, for_all


class TestBoolGenerator(unittest.TestCase):
    """Ensure boolean generator honours its probability contract."""

    @for_all(Gen.bool(), num_runs=200)
    def test_bool_outputs_are_boolean(self, value):
        """Generated values should always be ``bool`` instances."""

        self.assertIsInstance(value, bool)

    @for_all(Gen.bool(true_prob=1.0), num_runs=50)
    def test_true_probability_one(self, value):
        """Probability of 1.0 yields only ``True`` values."""

        self.assertIs(value, True)

    @for_all(Gen.bool(true_prob=0.0), num_runs=50)
    def test_true_probability_zero(self, value):
        """Probability of 0.0 yields only ``False`` values."""

        self.assertIs(value, False)

    def test_invalid_probability_raises(self):
        """Values outside the [0, 1] interval raise ``ValueError``."""

        with self.assertRaises(ValueError):
            Gen.bool(true_prob=-0.1)

        with self.assertRaises(ValueError):
            Gen.bool(true_prob=1.1)


if __name__ == "__main__":
    unittest.main()
