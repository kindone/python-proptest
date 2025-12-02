"""Tests for ``python_proptest.core.combinator.element_of``."""

import unittest

from python_proptest import Gen, run_for_all


class TestElementOf(unittest.TestCase):
    """Check selection semantics for ``Gen.element_of``."""

    def test_selects_from_provided_values(self):
        """Every generated value must belong to the given pool."""

        pool = [1, 2, 3, 4, 5]
        generator = Gen.element_of(*pool)

        run_for_all(
            lambda value: value in pool,
            generator,
            num_runs=50,
        )

    def test_supports_mixed_types(self):
        """Selection can span heterogeneous value types."""

        pool = [42, "hello", True, 3.14]
        generator = Gen.element_of(*pool)

        observed_types = set()

        def property_under_test(value):
            observed_types.add(type(value))
            return value in pool

        run_for_all(property_under_test, generator, num_runs=80)

        self.assertGreaterEqual(len(observed_types), 2)


if __name__ == "__main__":
    unittest.main()
