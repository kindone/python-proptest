"""Tests for ``python_proptest.core.generator.chain``."""

import unittest

from python_proptest import Gen, PropertyTestError, run_for_all


class TestChainGenerator(unittest.TestCase):
    """Exercise chain in both static and fluent forms."""

    def test_static_chain_produces_valid_dates(self):
        """Month/day pairs stay within the derived bounds."""

        def days_in_month(month: int) -> int:
            return [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]

        generator = Gen.chain(
            Gen.int(1, 12),
            lambda month: Gen.int(1, days_in_month(month)),
        )

        def predicate(pair):
            month, day = pair
            return 1 <= month <= 12 and 1 <= day <= days_in_month(month)

        run_for_all(predicate, generator, num_runs=200)

    def test_fluent_chain_respects_dependency(self):
        """Fluent ``chain`` ensures upper bound honours the base value."""

        generator = Gen.int(5, 15).chain(lambda start: Gen.int(start, start + 10))

        run_for_all(
            lambda pair: 5 <= pair[0] <= 15 and pair[0] <= pair[1] <= pair[0] + 10,
            generator,
            num_runs=200,
        )

    def test_nested_chain_dependencies(self):
        """Multiple chaining stages preserve relational constraints."""

        generator = Gen.int(1, 10).chain(
            lambda base: Gen.int(base, base + 5).chain(
                lambda mid: Gen.int(mid, mid + 5)
            )
        )

        def predicate(value):
            base, (mid, end) = value
            return base <= mid <= base + 5 and mid <= end <= mid + 5

        run_for_all(predicate, generator, num_runs=200)

    def test_chain_shrinking_respects_dependency(self):
        """Failing property shrinks to minimal consistent dependency."""

        generator = Gen.chain(Gen.int(1, 12), lambda month: Gen.int(1, month))

        with self.assertRaises(PropertyTestError) as ctx:
            run_for_all(lambda pair: pair[1] > pair[0], generator, num_runs=1)

        minimal_month, minimal_day = ctx.exception.minimal_inputs[0]
        self.assertGreaterEqual(minimal_month, minimal_day)
        self.assertGreaterEqual(minimal_day, 1)

    def test_chain_combined_with_list(self):
        """Chaining over collection sizes adheres to derived bounds."""

        generator = Gen.chain(
            Gen.int(1, 5),
            lambda size: Gen.list(
                Gen.int(0, 100),
                min_length=size,
                max_length=size,
            ),
        )

        def predicate(value):
            size, values = value
            return (
                size == len(values)
                and all(isinstance(elem, int) and 0 <= elem <= 100 for elem in values)
            )

        run_for_all(predicate, generator, num_runs=200)


if __name__ == "__main__":
    unittest.main()
