"""Tests for ``python_proptest.core.shrinker.floating`` float shrinking behavior."""

import unittest

from python_proptest import Gen, PropertyTestError, run_for_all
from python_proptest.core.shrinker.floating import shrink_float


class TestFloatingShrinking(unittest.TestCase):
    """Verify floating-point shrinking finds minimal failing cases."""

    def test_shrinking_with_float_values(self):
        """Shrinking works with floating-point values."""

        def property_func(x: float):
            # Fail for values >= 2.5
            return x < 2.5

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func,
                Gen.float(min_value=2.5, max_value=10.0),
                num_runs=50,
            )

        # Should shrink to a value close to 2.5
        minimal_input = exc_info.exception.minimal_inputs[0]
        self.assertIsInstance(minimal_input, float)
        self.assertGreaterEqual(minimal_input, 2.5)
        self.assertLess(minimal_input, 10.0)  # Should be within generator bounds

    def test_negative_infinity_shrinks_through_negative_finite_values(self):
        """-Infinity should shrink toward negative finite values, not positive ones."""

        shrinkable = shrink_float(float("-inf"))
        shrinks = shrinkable.shrinks().to_list()

        self.assertGreater(len(shrinks), 0)
        self.assertEqual(shrinks[0].value, 0.0)
        self.assertTrue(any(candidate.value < 0.0 for candidate in shrinks))


if __name__ == "__main__":
    unittest.main()
