"""Tests for ``python_proptest.core.generator.list``."""

import unittest

from python_proptest import Gen, PropertyTestError, for_all, run_for_all


class TestListGenerator(unittest.TestCase):
    """Cover list-oriented generators and shrinking behaviour."""

    @for_all(Gen.list(Gen.int(min_value=0, max_value=10), min_length=0, max_length=5), num_runs=200)
    def test_list_respects_length_and_element_type(self, value):
        """Generated lists honour declared bounds and element generators."""

        self.assertIsInstance(value, list)
        self.assertLessEqual(len(value), 5)
        self.assertTrue(all(isinstance(elem, int) and 0 <= elem <= 10 for elem in value))

    @for_all(
        Gen.unique_list(Gen.int(min_value=0, max_value=10), min_length=0, max_length=5),
        num_runs=200,
    )
    def test_unique_list_contains_no_duplicates(self, value):
        """``Gen.unique_list`` produces strictly unique elements."""

        self.assertIsInstance(value, list)
        self.assertEqual(value, sorted(value))
        self.assertEqual(len(value), len(set(value)))

    def test_list_shrinks_to_minimum_length(self):
        """Failing property shrinks towards the declared minimum length."""

        generator = Gen.list(
            Gen.int(min_value=0, max_value=100),
            min_length=2,
            max_length=4,
        )

        with self.assertRaises(PropertyTestError) as ctx:
            run_for_all(lambda value: False, generator, num_runs=1)

        minimal_list = ctx.exception.minimal_inputs[0]
        failing_list = ctx.exception.failing_inputs[0]
        self.assertLessEqual(len(minimal_list), len(failing_list))
        self.assertEqual(minimal_list, [])

    def test_zero_min_length_shrinks_to_empty_list(self):
        """Min length 0 shrinks failing examples down to the empty list."""

        generator = Gen.list(
            Gen.int(min_value=0, max_value=5),
            min_length=0,
            max_length=3,
        )

        with self.assertRaises(PropertyTestError) as ctx:
            run_for_all(lambda value: False, generator, num_runs=1)

        self.assertEqual(ctx.exception.minimal_inputs[0], [])


if __name__ == "__main__":
    unittest.main()
