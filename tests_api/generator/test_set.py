"""Tests for ``python_proptest.core.generator.set``."""

import unittest

from python_proptest import Gen, for_all


class TestSetGenerator(unittest.TestCase):
    """Exercise set generator behaviours."""

    @for_all(
        Gen.set(Gen.int(min_value=0, max_value=10), min_size=0, max_size=5),
        num_runs=200,
    )
    def test_set_contains_unique_elements(self, value):
        """Generated sets consist of unique integers within range."""

        self.assertIsInstance(value, set)
        self.assertTrue(
            all(isinstance(elem, int) and 0 <= elem <= 10 for elem in value)
        )

    @for_all(
        Gen.set(Gen.int(min_value=0, max_value=10), min_size=2, max_size=4),
        num_runs=200,
    )
    def test_set_respects_size_constraints(self, value):
        """Set generator honours min/max size parameters."""

        self.assertIsInstance(value, set)
        self.assertGreaterEqual(len(value), 2)
        self.assertLessEqual(len(value), 4)


if __name__ == "__main__":
    unittest.main()
