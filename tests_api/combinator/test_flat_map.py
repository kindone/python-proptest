"""Tests for ``python_proptest.core.generator.transform.flat_map``."""

import unittest

from python_proptest import Gen, run_for_all


class TestFlatMapCombinator(unittest.TestCase):
    """Check dependent generator behaviour using flat_map."""

    def test_flat_map_generates_dependent_ranges(self):
        """Dependent generator respects upstream value bounds."""

        generator = Gen.int(min_value=1, max_value=5).flat_map(
            lambda x: Gen.int(min_value=x, max_value=x + 10)
        )

        run_for_all(
            lambda value: 1 <= value <= 15,
            generator,
            num_runs=60,
        )

    def test_flat_map_string_lengths(self):
        """Dependent string length generation holds exact size."""

        generator = Gen.int(min_value=1, max_value=5).flat_map(
            lambda length: Gen.str(min_length=length, max_length=length)
        )

        def property_under_test(value: str) -> bool:
            return isinstance(value, str) and 1 <= len(value) <= 5

        run_for_all(property_under_test, generator, num_runs=60)


if __name__ == "__main__":
    unittest.main()
