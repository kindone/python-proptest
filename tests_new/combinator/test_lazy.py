"""Tests for ``python_proptest.core.combinator.lazy``."""

import unittest

from python_proptest import Gen, PropertyTestError, run_for_all


class TestLazyCombinator(unittest.TestCase):
    """Validate lazy generator creation via ``Gen.lazy``."""

    def test_lazy_defers_evaluation_until_generation(self):
        """The factory function should not run until generate() is invoked."""

        calls = {"count": 0}

        def factory():
            calls["count"] += 1
            return calls["count"]

        lazy_gen = Gen.lazy(factory)

        self.assertEqual(calls["count"], 0)

        observed = []

        def property_under_test(value: int) -> bool:
            observed.append(value)
            return value == len(observed)

        run_for_all(property_under_test, lazy_gen, num_runs=5)

        self.assertEqual(calls["count"], len(observed))

    def test_lazy_generators_have_no_shrinks(self):
        """Lazy generators produce shrinkables without candidates."""

        lazy_gen = Gen.lazy(lambda: 123)

        with self.assertRaises(PropertyTestError) as ctx:
            run_for_all(lambda value: value != 123, lazy_gen, num_runs=1)

        error = ctx.exception
        self.assertEqual(error.minimal_inputs, error.failing_inputs)
        self.assertEqual(error.minimal_inputs[0], 123)


if __name__ == "__main__":
    unittest.main()
