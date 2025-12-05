"""Tests for ``python_proptest.core.generator.chain``."""

import unittest

from python_proptest import Gen, PropertyTestError, for_all, run_for_all


def _days_in_month(month: int) -> int:
    """Return the day count for a given month (non-leap year)."""

    return [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]


class TestChainGenerator(unittest.TestCase):
    """Exercise chain in both static and fluent forms."""

    @for_all(
        Gen.chain(
            Gen.int(1, 12),
            lambda month: Gen.int(1, _days_in_month(month)),
        ),
        num_runs=200,
    )
    def test_static_chain_produces_valid_dates(self, pair):
        """Month/day pairs stay within the derived bounds."""

        month, day = pair
        self.assertGreaterEqual(month, 1)
        self.assertLessEqual(month, 12)
        self.assertGreaterEqual(day, 1)
        self.assertLessEqual(day, _days_in_month(month))

    @for_all(
        Gen.int(5, 15).chain(lambda start: Gen.int(start, start + 10)),
        num_runs=200,
    )
    def test_fluent_chain_respects_dependency(self, pair):
        """Fluent ``chain`` ensures upper bound honours the base value."""

        start, end = pair
        self.assertGreaterEqual(start, 5)
        self.assertLessEqual(start, 15)
        self.assertGreaterEqual(end, start)
        self.assertLessEqual(end, start + 10)

    @for_all(
        Gen.int(1, 10).chain(
            lambda base: Gen.int(base, base + 5).chain(
                lambda mid: Gen.int(mid, mid + 5)
            )
        ),
        num_runs=200,
    )
    def test_nested_chain_dependencies(self, value):
        """Multiple chaining stages preserve relational constraints."""

        base, (mid, end) = value
        self.assertGreaterEqual(base, 1)
        self.assertLessEqual(base, 10)
        self.assertGreaterEqual(mid, base)
        self.assertLessEqual(mid, base + 5)
        self.assertGreaterEqual(end, mid)
        self.assertLessEqual(end, mid + 5)

    def test_chain_shrinking_respects_dependency(self):
        """Failing property shrinks to minimal consistent dependency."""

        generator = Gen.chain(Gen.int(1, 12), lambda month: Gen.int(1, month))

        with self.assertRaises(PropertyTestError) as ctx:
            run_for_all(lambda pair: pair[1] > pair[0], generator, num_runs=1)

        minimal_month, minimal_day = ctx.exception.minimal_inputs[0]
        self.assertGreaterEqual(minimal_month, minimal_day)
        self.assertGreaterEqual(minimal_day, 1)

    @for_all(
        Gen.chain(
            Gen.int(1, 5),
            lambda size: Gen.list(
                Gen.int(0, 100),
                min_length=size,
                max_length=size,
            ),
        ),
        num_runs=200,
    )
    def test_chain_combined_with_list(self, value):
        """Chaining over collection sizes adheres to derived bounds."""

        size, values = value
        self.assertEqual(size, len(values))
        self.assertTrue(all(isinstance(elem, int) and 0 <= elem <= 100 for elem in values))


if __name__ == "__main__":
    unittest.main()
