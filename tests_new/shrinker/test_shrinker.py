"""Tests for general shrinking behavior across multiple types."""

import unittest

from python_proptest import Gen, PropertyTestError, run_for_all


class TestShrinkingBehavior(unittest.TestCase):
    """Verify general shrinking behavior across multiple argument types."""

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
                num_runs=50,
            )

        # Should have shrunk both arguments
        minimal_inputs = exc_info.exception.minimal_inputs
        self.assertEqual(len(minimal_inputs), 2)
        a, b = minimal_inputs
        self.assertGreaterEqual(a + b, 10)
        # Values should be within generator bounds
        self.assertLessEqual(a, 20)
        self.assertLessEqual(b, 20)

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
                num_runs=50,
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

    def test_shrinking_with_mixed_type_arguments(self):
        """Shrinking works correctly with mixed-type arguments."""

        def property_func(x: int, s: str, b: bool):
            # Fail when combined condition is met
            return not (x >= 5 and len(s) >= 2 and b)

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func,
                Gen.int(min_value=5, max_value=20),
                Gen.str(min_length=2, max_length=5),
                Gen.bool(),
                num_runs=50,
            )

        # Should have shrunk all arguments
        minimal_inputs = exc_info.exception.minimal_inputs
        self.assertEqual(len(minimal_inputs), 3)
        x, s, b = minimal_inputs
        self.assertIsInstance(x, int)
        self.assertIsInstance(s, str)
        self.assertIsInstance(b, bool)


if __name__ == "__main__":
    unittest.main()
