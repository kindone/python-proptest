"""Tests for ``python_proptest.core.shrinker.list`` list shrinking behavior."""

import unittest

from python_proptest import Gen, PropertyTestError, run_for_all


class TestListShrinking(unittest.TestCase):
    """Verify list shrinking finds minimal failing cases."""

    def test_list_shrinks_to_minimal_length(self):
        """List properties shrink to minimal failing length."""

        def property_func(lst: list):
            # Fail for lists of length >= 2
            return len(lst) < 2

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func,
                Gen.list(Gen.int(min_value=0, max_value=10), min_length=2, max_length=5),
                num_runs=50,
            )

        # Should shrink to a list of length 2 (minimal failing length)
        minimal_input = exc_info.exception.minimal_inputs[0]
        self.assertIsInstance(minimal_input, list)
        self.assertGreaterEqual(len(minimal_input), 2)
        self.assertLessEqual(len(minimal_input), 5)  # Should be within generator bounds

    def test_shrinking_with_empty_collections(self):
        """Shrinking handles empty collections correctly."""

        def property_func(lst: list):
            # Fail for non-empty lists
            return len(lst) == 0

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func,
                Gen.list(Gen.int(min_value=0, max_value=10), min_length=1, max_length=3),
                num_runs=50,
            )

        # Should find a non-empty list
        failing_input = exc_info.exception.failing_inputs[0]
        self.assertIsInstance(failing_input, list)
        self.assertGreater(len(failing_input), 0)

    def test_shrinking_with_single_element_collections(self):
        """Shrinking works with single-element collections."""

        def property_func(lst: list):
            # Fail for lists with more than one element
            return len(lst) <= 1

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func,
                Gen.list(Gen.int(min_value=0, max_value=10), min_length=2, max_length=5),
                num_runs=50,
            )

        # Should shrink to a list with exactly 2 elements (minimal failing case)
        minimal_input = exc_info.exception.minimal_inputs[0]
        self.assertIsInstance(minimal_input, list)
        self.assertGreaterEqual(len(minimal_input), 2)
        self.assertLessEqual(len(minimal_input), 5)  # Should be within generator bounds

    def test_shrinking_with_complex_nested_structure(self):
        """Shrinking works with nested composite structures."""

        def property_func(data: list):
            # Fail when list has length >= 2 (guaranteed to fail with min_length=2)
            return len(data) < 2

        nested_gen = Gen.list(
            Gen.list(Gen.int(min_value=0, max_value=5), min_length=0, max_length=3),
            min_length=2,
            max_length=3,
        )

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(property_func, nested_gen, num_runs=50)

        # Should have shrunk to a minimal failing structure
        failing_input = exc_info.exception.failing_inputs[0]
        self.assertIsInstance(failing_input, list)
        self.assertGreaterEqual(len(failing_input), 2)


if __name__ == "__main__":
    unittest.main()

