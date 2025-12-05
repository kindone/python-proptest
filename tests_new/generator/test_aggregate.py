"""Tests for ``python_proptest.core.generator.aggregate``."""

import unittest

from python_proptest import Gen, PropertyTestError, for_all, run_for_all


class TestAggregateGenerator(unittest.TestCase):
    """Exercise ``Gen.aggregate`` behaviour across scenarios."""

    @for_all(
        Gen.aggregate(
            Gen.int(0, 10),
            lambda value: Gen.int(value, value + 5),
            min_size=3,
            max_size=5,
        ),
        num_runs=200,
    )
    def test_increasing_sequence_respects_bounds(self, values):
        """Aggregate sequences stay non-decreasing within declared length bounds."""

        self.assertIsInstance(values, list)
        self.assertGreaterEqual(len(values), 3)
        self.assertLessEqual(len(values), 5)
        self.assertTrue(all(values[i] <= values[i + 1] for i in range(len(values) - 1)))

    def test_zero_min_size_allows_empty_list(self):
        """Aggregate with min size 0 can shrink to empty list on failure."""

        generator = Gen.aggregate(
            Gen.int(0, 10),
            lambda value: Gen.int(value, value + 5),
            min_size=0,
            max_size=5,
        )

        with self.assertRaises(PropertyTestError) as ctx:
            run_for_all(lambda values: False, generator, num_runs=1)

        self.assertEqual(ctx.exception.minimal_inputs[0], [])

    @for_all(
        Gen.aggregate(
            Gen.ascii_string(min_length=1, max_length=3),
            lambda text: Gen.ascii_string(min_length=len(text), max_length=len(text) + 2),
            min_size=2,
            max_size=5,
        ),
        num_runs=200,
    )
    def test_string_sequence_has_non_decreasing_length(self, values):
        """String-based aggregation maintains monotonic lengths."""

        self.assertIsInstance(values, list)
        self.assertGreaterEqual(len(values), 2)
        self.assertLessEqual(len(values), 5)
        self.assertTrue(all(len(values[i]) <= len(values[i + 1]) for i in range(len(values) - 1)))

    def test_shrinks_reduce_length(self):
        """Shrinking a failing property drives towards the minimum size."""

        generator = Gen.aggregate(
            Gen.int(0, 10),
            lambda value: Gen.int(value, value + 5),
            min_size=2,
            max_size=6,
        )

        with self.assertRaises(PropertyTestError) as ctx:
            run_for_all(lambda values: False, generator, num_runs=1)

        minimal_values = ctx.exception.minimal_inputs[0]
        failing_values = ctx.exception.failing_inputs[0]
        self.assertGreaterEqual(len(minimal_values), 2)
        self.assertLessEqual(len(minimal_values), len(failing_values))


if __name__ == "__main__":
    unittest.main()
