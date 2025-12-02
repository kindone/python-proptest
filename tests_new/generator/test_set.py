"""Tests for ``python_proptest.core.generator.set``."""

import unittest

from python_proptest import Gen, run_for_all


class TestSetGenerator(unittest.TestCase):
    """Exercise set generator behaviours."""

    def test_set_contains_unique_elements(self):
        """Generated sets consist of unique integers within range."""

        def predicate(value):
            if not isinstance(value, set):
                return False
            return all(isinstance(elem, int) and 0 <= elem <= 10 for elem in value)

        run_for_all(
            predicate,
            Gen.set(Gen.int(min_value=0, max_value=10), min_size=0, max_size=5),
            num_runs=200,
        )

    def test_set_respects_size_constraints(self):
        """Set generator honours min/max size parameters."""

        run_for_all(
            lambda value: isinstance(value, set) and 2 <= len(value) <= 4,
            Gen.set(Gen.int(min_value=0, max_value=10), min_size=2, max_size=4),
            num_runs=200,
        )


if __name__ == "__main__":
    unittest.main()
