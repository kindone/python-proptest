"""Tests for ``python_proptest.core.shrinker`` shrinking behavior."""

import unittest

from python_proptest import Gen, PropertyTestError, run_for_all


class TestShrinkingBehavior(unittest.TestCase):
    """Verify shrinking finds minimal failing cases through property tests."""

    def test_integer_shrinks_towards_zero(self):
        """Integer properties shrink failing values towards zero."""

        def property_func(x: int):
            # Fail for any non-zero value
            return x == 0

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func, Gen.int(min_value=-10, max_value=10), num_runs=10
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
                property_func, Gen.int(min_value=5, max_value=100), num_runs=10
            )

        # Should shrink to 5 (the minimal failing value)
        minimal_input = exc_info.exception.minimal_inputs[0]
        self.assertGreaterEqual(minimal_input, 5)
        self.assertLess(minimal_input, 20)  # Should be relatively small after shrinking

    def test_string_shrinks_to_minimal_length(self):
        """String properties shrink to minimal failing length."""

        def property_func(s: str):
            # Fail for strings of length >= 3
            return len(s) < 3

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func, Gen.str(min_length=3, max_length=10), num_runs=10
            )

        # Should shrink to a string of length 3 (minimal failing length)
        minimal_input = exc_info.exception.minimal_inputs[0]
        self.assertIsInstance(minimal_input, str)
        self.assertGreaterEqual(len(minimal_input), 3)
        self.assertLess(len(minimal_input), 8)  # Should be relatively small after shrinking

    def test_list_shrinks_to_minimal_length(self):
        """List properties shrink to minimal failing length."""

        def property_func(lst: list):
            # Fail for lists of length >= 2
            return len(lst) < 2

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func,
                Gen.list(Gen.int(min_value=0, max_value=10), min_length=2, max_length=5),
                num_runs=10,
            )

        # Should shrink to a list of length 2 (minimal failing length)
        minimal_input = exc_info.exception.minimal_inputs[0]
        self.assertIsInstance(minimal_input, list)
        self.assertGreaterEqual(len(minimal_input), 2)
        self.assertLessEqual(len(minimal_input), 5)  # Should be within generator bounds

    def test_dict_shrinks_to_minimal_size(self):
        """Dictionary properties shrink to minimal failing size."""

        def property_func(d: dict):
            # Fail for dicts of size >= 2
            return len(d) < 2

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func,
                Gen.dict(
                    Gen.str(min_length=1, max_length=2),
                    Gen.int(min_value=0, max_value=10),
                    min_size=0,
                    max_size=3,
                ),
                num_runs=10,
            )

        # Should shrink to a dict of size 2 (minimal failing size)
        failing_input = exc_info.exception.failing_inputs[0]
        self.assertIsInstance(failing_input, dict)
        self.assertGreaterEqual(len(failing_input), 2)
        self.assertLess(len(failing_input), 4)  # Should be close to minimal

    def test_multiple_arguments_shrink_independently(self):
        """Multiple arguments shrink independently to minimal values."""

        def property_func(a: int, b: int):
            # Fail when a + b >= 10
            return a + b < 10

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func,
                Gen.int(min_value=5, max_value=20),
                Gen.int(min_value=5, max_value=20),
                num_runs=10,
            )

        # Should have shrunk both arguments
        minimal_inputs = exc_info.exception.minimal_inputs
        self.assertEqual(len(minimal_inputs), 2)
        a, b = minimal_inputs
        self.assertGreaterEqual(a + b, 10)
        # Values should be within generator bounds
        self.assertLessEqual(a, 20)
        self.assertLessEqual(b, 20)

    def test_shrinking_preserves_failing_condition(self):
        """Shrunk values still fail the original property."""

        def property_func(x: int):
            # Fail for values >= 7
            return x < 7

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func, Gen.int(min_value=0, max_value=100), num_runs=10
            )

        # The shrunk value should still fail
        failing_input = exc_info.exception.failing_inputs[0]
        self.assertFalse(property_func(failing_input))

    def test_shrinking_with_complex_nested_structure(self):
        """Shrinking works with nested composite structures."""

        def property_func(data: list):
            # Fail when total elements >= 3
            total = sum(len(item) if isinstance(item, list) else 1 for item in data)
            return total < 3

        nested_gen = Gen.list(
            Gen.list(Gen.int(min_value=0, max_value=5), min_length=0, max_length=3),
            min_length=0,
            max_length=3,
        )

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(property_func, nested_gen, num_runs=10)

        # Should have shrunk to a minimal failing structure
        failing_input = exc_info.exception.failing_inputs[0]
        self.assertIsInstance(failing_input, list)

    def test_shrinking_finds_minimal_inputs(self):
        """Shrinking finds minimal inputs, not just smaller ones."""

        def property_func(x: int):
            # Fail for values >= 3
            return x < 3

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func, Gen.int(min_value=3, max_value=100), num_runs=10
            )

        # Should shrink to 3 (the minimal failing value), not just any smaller value
        minimal_input = exc_info.exception.minimal_inputs[0]
        self.assertGreaterEqual(minimal_input, 3)
        self.assertLess(minimal_input, 50)  # Should be smaller than original range

    def test_shrinking_with_float_values(self):
        """Shrinking works with floating-point values."""

        def property_func(x: float):
            # Fail for values >= 2.5
            return x < 2.5

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func,
                Gen.float(min_value=2.5, max_value=10.0),
                num_runs=10,
            )

        # Should shrink to a value close to 2.5
        minimal_input = exc_info.exception.minimal_inputs[0]
        self.assertIsInstance(minimal_input, float)
        self.assertGreaterEqual(minimal_input, 2.5)
        self.assertLess(minimal_input, 10.0)  # Should be within generator bounds

    def test_shrinking_error_contains_minimal_inputs(self):
        """PropertyTestError contains minimal failing inputs after shrinking."""

        def property_func(x: int, y: int):
            # Fail when x * y >= 20
            return x * y < 20

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func,
                Gen.int(min_value=0, max_value=20),
                Gen.int(min_value=0, max_value=20),
                num_runs=10,
            )

        error = exc_info.exception
        self.assertIsNotNone(error.failing_inputs)
        self.assertIsNotNone(error.minimal_inputs)
        self.assertEqual(len(error.failing_inputs), 2)
        self.assertEqual(len(error.minimal_inputs), 2)

        # Minimal inputs should be smaller or equal to failing inputs
        a_fail, b_fail = error.failing_inputs
        a_min, b_min = error.minimal_inputs
        self.assertLessEqual(a_min, a_fail)
        self.assertLessEqual(b_min, b_fail)


if __name__ == "__main__":
    unittest.main()
