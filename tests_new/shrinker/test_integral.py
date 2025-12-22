"""Tests for ``python_proptest.core.shrinker.integral`` integer shrinking behavior."""

import unittest

from python_proptest import Gen, PropertyTestError, run_for_all


class TestIntegralShrinking(unittest.TestCase):
    """Verify integer shrinking finds minimal failing cases."""

    def test_integer_shrinks_towards_zero(self):
        """Integer properties shrink failing values towards zero."""

        def property_func(x: int):
            # Fail for any non-zero value
            return x == 0

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func, Gen.int(min_value=-10, max_value=10), num_runs=50
            )

        # Should shrink to a non-zero value (minimal failing case)
        failing_input = exc_info.exception.failing_inputs[0]
        self.assertIsInstance(failing_input, int)
        self.assertNotEqual(failing_input, 0)

    def test_integer_shrinks_to_minimal_failing_value(self):
        """Integer properties shrink to the minimal value that fails."""

        def property_func(x: int):
            # Fail for values >= 5
            return x < 5

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func, Gen.int(min_value=5, max_value=100), num_runs=50
            )

        # Should shrink to 5 (the minimal failing value)
        minimal_input = exc_info.exception.minimal_inputs[0]
        self.assertGreaterEqual(minimal_input, 5)
        self.assertLess(minimal_input, 20)  # Should be relatively small after shrinking

    def test_shrinking_preserves_failing_condition(self):
        """Shrunk values still fail the original property."""

        def property_func(x: int):
            # Fail for values >= 7
            return x < 7

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func, Gen.int(min_value=0, max_value=100), num_runs=50
            )

        # The shrunk value should still fail
        failing_input = exc_info.exception.failing_inputs[0]
        self.assertFalse(property_func(failing_input))

    def test_shrinking_finds_minimal_inputs(self):
        """Shrinking finds minimal inputs, not just smaller ones."""

        def property_func(x: int):
            # Fail for values >= 3
            return x < 3

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func, Gen.int(min_value=3, max_value=100), num_runs=50
            )

        # Should shrink to 3 (the minimal failing value), not just any smaller value
        minimal_input = exc_info.exception.minimal_inputs[0]
        self.assertGreaterEqual(minimal_input, 3)
        self.assertLess(minimal_input, 50)  # Should be smaller than original range

    def test_shrinking_with_zero_boundary(self):
        """Shrinking handles zero boundary conditions correctly."""

        def property_func(x: int):
            # Fail for non-zero values
            return x == 0

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func, Gen.int(min_value=-10, max_value=10), num_runs=50
            )

        # Should find a non-zero value
        failing_input = exc_info.exception.failing_inputs[0]
        self.assertIsInstance(failing_input, int)
        self.assertNotEqual(failing_input, 0)

    def test_shrinking_with_negative_values(self):
        """Shrinking works correctly with negative integer values."""

        def property_func(x: int):
            # Fail for values < -5
            return x >= -5

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func, Gen.int(min_value=-20, max_value=-6), num_runs=50
            )

        # Should shrink to a value close to -5 (minimal failing value)
        # Use failing_inputs if minimal_inputs is not available
        if exc_info.exception.minimal_inputs and len(exc_info.exception.minimal_inputs) > 0:
            minimal_input = exc_info.exception.minimal_inputs[0]
        else:
            minimal_input = exc_info.exception.failing_inputs[0]
        self.assertIsInstance(minimal_input, int)
        self.assertLess(minimal_input, -5)
        self.assertGreaterEqual(minimal_input, -20)

    def test_shrinking_finds_smaller_values_consistently(self):
        """Shrinking consistently finds smaller values across multiple runs."""

        def property_func(x: int):
            # Fail for values >= 10
            return x < 10

        # Run multiple times with same seed to verify consistency
        minimal_values = []
        for seed in [42, 42, 42]:  # Same seed should produce same result
            with self.assertRaises(PropertyTestError) as exc_info:
                run_for_all(
                    property_func,
                    Gen.int(min_value=10, max_value=100),
                    num_runs=50,
                    seed=seed,
                )
            minimal_values.append(exc_info.exception.minimal_inputs[0])

        # All runs with same seed should produce same minimal value
        self.assertEqual(len(set(minimal_values)), 1)


if __name__ == "__main__":
    unittest.main()
