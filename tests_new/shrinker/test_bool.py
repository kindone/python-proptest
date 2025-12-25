"""Tests for ``python_proptest.core.shrinker.bool`` boolean shrinking behavior."""

import unittest

from python_proptest import Gen, PropertyTestError, run_for_all


class TestBoolShrinking(unittest.TestCase):
    """Verify boolean shrinking finds minimal failing cases."""

    def test_boolean_shrinks_to_false(self):
        """Boolean properties shrink True to False when possible."""

        def property_func(b: bool):
            # Fail for True values
            return not b

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(property_func, Gen.bool(), num_runs=50)

        # Should find True as failing value
        failing_input = exc_info.exception.failing_inputs[0]
        self.assertIsInstance(failing_input, bool)
        self.assertTrue(failing_input)  # Should be True


if __name__ == "__main__":
    unittest.main()

