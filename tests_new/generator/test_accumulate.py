"""Tests for ``python_proptest.core.generator.aggregate`` accumulate variant."""

import unittest

from python_proptest import Gen, PropertyTestError, for_all, run_for_all


class TestAccumulateGenerator(unittest.TestCase):
    """Validate ``Gen.accumulate`` behaviour and shrinking."""

    @for_all(
        Gen.accumulate(
            Gen.int(0, 10),
            lambda value: Gen.int(value, value + 5),
            min_size=3,
            max_size=5,
        ),
        num_runs=200,
    )
    def test_accumulate_returns_final_value(self, value):
        """Accumulation yields a single value within expected bounds."""

        self.assertIsInstance(value, int)
        self.assertGreaterEqual(value, 0)

    def test_zero_min_steps_allows_initial_value(self):
        """Zero minimum size lets shrinking reach the initial value."""

        generator = Gen.accumulate(
            Gen.int(10, 20),
            lambda value: Gen.int(value, value + 5),
            min_size=0,
            max_size=3,
        )

        with self.assertRaises(PropertyTestError) as ctx:
            run_for_all(lambda value: False, generator, num_runs=1)

        minimal_value = ctx.exception.minimal_inputs[0]
        self.assertGreaterEqual(minimal_value, 10)
        self.assertLessEqual(minimal_value, 20)

    @for_all(
        Gen.accumulate(
            Gen.ascii_string(min_length=1, max_length=2),
            lambda text: Gen.ascii_string(min_length=len(text) + 1, max_length=len(text) + 2),
            min_size=3,
            max_size=5,
        ),
        num_runs=200,
    )
    def test_string_growth_returns_final_string(self, value):
        """String accumulation returns a sufficiently long final string."""

        self.assertIsInstance(value, str)
        self.assertGreaterEqual(len(value), 4)

    def test_shrinking_produces_minimal_value(self):
        """Failing property shrinks towards the minimal accumulated output."""

        generator = Gen.accumulate(
            Gen.int(0, 100),
            lambda value: Gen.int(value, value + 10),
            min_size=3,
            max_size=6,
        )

        with self.assertRaises(PropertyTestError) as ctx:
            run_for_all(lambda value: value < 0, generator, num_runs=1)

        minimal_value = ctx.exception.minimal_inputs[0]
        self.assertGreaterEqual(minimal_value, 0)


if __name__ == "__main__":
    unittest.main()
