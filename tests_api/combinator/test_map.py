"""Tests for ``python_proptest.core.generator.transform.map``."""

import unittest

from python_proptest import Gen, run_for_all


class TestMapCombinator(unittest.TestCase):
    """Validate transformations applied through ``Gen.map``."""

    def test_numeric_transformation(self):
        """Mapping over integers should apply provided function."""

        mapped = Gen.int(min_value=1, max_value=10).map(lambda x: x * 2)

        run_for_all(
            lambda value: value % 2 == 0 and 2 <= value <= 20,
            mapped,
            num_runs=40,
        )

    def test_string_transformation(self):
        """Mapping into strings using f-strings preserves formatting."""

        mapped = Gen.int(min_value=1, max_value=10).map(lambda x: f"Number: {x}")

        def property_under_test(value: str) -> bool:
            return value.startswith("Number: ") and value[8:].isdigit()

        run_for_all(property_under_test, mapped, num_runs=40)

    def test_chained_transformations(self):
        """Multiple map calls execute sequentially."""

        mapped = (
            Gen.int(min_value=1, max_value=100)
            .map(lambda x: x * 2)
            .map(lambda x: x + 1)
        )

        run_for_all(
            lambda value: value % 2 == 1 and 3 <= value <= 201,
            mapped,
            num_runs=40,
        )


if __name__ == "__main__":
    unittest.main()
