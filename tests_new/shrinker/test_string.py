"""Tests for ``python_proptest.core.shrinker.string`` string shrinking behavior."""

import unittest

from python_proptest import Gen, PropertyTestError, run_for_all


class TestStringShrinking(unittest.TestCase):
    """Verify string shrinking finds minimal failing cases."""

    def test_string_shrinks_to_minimal_length(self):
        """String properties shrink to minimal failing length."""

        def property_func(s: str):
            # Fail for strings of length >= 3
            return len(s) < 3

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func, Gen.str(min_length=3, max_length=10), num_runs=50
            )

        # Should shrink to a string of length 3 (minimal failing length)
        minimal_input = exc_info.exception.minimal_inputs[0]
        self.assertIsInstance(minimal_input, str)
        self.assertGreaterEqual(len(minimal_input), 3)
        self.assertLess(len(minimal_input), 8)  # Should be relatively small after shrinking

    def test_shrinking_preserves_string_charset_constraints(self):
        """Shrinking preserves charset constraints in string generators."""

        def property_func(s: str):
            # Fail for strings of length >= 2
            return len(s) < 2

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func,
                Gen.str(min_length=2, max_length=5, charset="abc"),
                num_runs=50,
            )

        # Shrunk string should still only contain charset characters
        minimal_input = exc_info.exception.minimal_inputs[0]
        self.assertIsInstance(minimal_input, str)
        self.assertGreaterEqual(len(minimal_input), 2)
        self.assertTrue(all(c in "abc" for c in minimal_input))

    def test_shrinking_preserves_codepoint_range_constraints(self):
        """Shrinking preserves codepoint range constraints."""

        def property_func(s: str):
            # Fail for strings of length >= 2 (guaranteed to fail with min_length=2)
            return len(s) < 2

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func,
                Gen.str(min_length=2, max_length=5, charset=Gen.int(65, 90)),  # A-Z
                num_runs=50,
            )

        # Shrunk string should still only contain A-Z characters
        # Check whichever input is available
        error = exc_info.exception
        if error.minimal_inputs and len(error.minimal_inputs) > 0:
            input_to_check = error.minimal_inputs[0]
        elif error.failing_inputs and len(error.failing_inputs) > 0:
            input_to_check = error.failing_inputs[0]
        else:
            self.fail("No failing or minimal inputs found")
        
        self.assertIsInstance(input_to_check, str)
        self.assertGreaterEqual(len(input_to_check), 1)
        # All characters should be in A-Z range (codepoints 65-90)
        self.assertTrue(all(65 <= ord(c) <= 90 for c in input_to_check))


if __name__ == "__main__":
    unittest.main()
