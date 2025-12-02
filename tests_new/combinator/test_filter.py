"""Tests for ``python_proptest.core.generator.transform.filter``."""

import unittest

from python_proptest import Gen, PropertyTestError, run_for_all


class TestFilterCombinator(unittest.TestCase):
    """Validate behaviour of ``Gen.filter``."""

    def test_filter_keeps_valid_values(self):
        """Filtering for even numbers only yields even outputs."""

        filtered = Gen.int(min_value=1, max_value=20).filter(lambda x: x % 2 == 0)

        run_for_all(
            lambda value: value % 2 == 0 and 2 <= value <= 20,
            filtered,
            num_runs=60,
        )

    def test_filter_impossible_predicate_raises(self):
        """Impossible predicates raise ValueError during generation."""

        filtered = Gen.int(min_value=1, max_value=10).filter(lambda x: x > 100)

        with self.assertRaises(PropertyTestError) as ctx:
            run_for_all(lambda value: True, filtered, num_runs=1)

        self.assertIsInstance(ctx.exception.__cause__, ValueError)

    def test_filter_interacts_with_run_for_all(self):
        """Property runners respect filtered constraints."""

        def predicate(x):
            self.assertEqual(x % 2, 0)
            return True

        run_for_all(
            predicate,
            Gen.int(min_value=1, max_value=20).filter(lambda x: x % 2 == 0),
            num_runs=50,
        )


if __name__ == "__main__":
    unittest.main()
