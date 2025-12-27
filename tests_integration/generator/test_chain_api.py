"""Test/demo of the chain combinator in the public API.

This demonstrates that Gen.chain() is available through the public API
and works as expected for creating dependent tuple generation.
"""

import random
import unittest

from python_proptest import Gen, run_for_all


class TestChainPublicAPI(unittest.TestCase):
    """Demonstrate that chain is available through public API."""

    def test_static_api_chain(self):
        """Test chain using static API: Gen.chain()."""

        def days_in_month(month):
            days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            return days[month - 1]

        date_gen = Gen.chain(
            Gen.int(1, 12),  # month
            lambda month: Gen.int(1, days_in_month(month)),  # valid day
        )

        # Verify generated dates are valid
        for _ in range(20):
            month, day = date_gen.generate(random.Random()).value
            self.assertGreaterEqual(month, 1)
            self.assertLessEqual(month, 12)
            self.assertGreaterEqual(day, 1)
            self.assertLessEqual(day, days_in_month(month))

    def test_fluent_api_chain(self):
        """Test chain using fluent API: gen.chain()."""
        range_gen = Gen.int(5, 15).chain(lambda start: Gen.int(start, start + 10))

        # Verify end >= start and within expected range
        for _ in range(20):
            start, end = range_gen.generate(random.Random()).value
            self.assertGreaterEqual(start, 5)
            self.assertLessEqual(start, 15)
            self.assertGreaterEqual(end, start)
            self.assertLessEqual(end, start + 10)

    def test_nested_chain_dependency(self):
        """Test multiple levels of chaining."""
        # Generate: base -> dependent1 -> dependent2
        gen = Gen.int(1, 10).chain(
            lambda base: Gen.int(base, base + 5).chain(
                lambda mid: Gen.int(mid, mid + 5)
            )
        )

        for _ in range(20):
            (base, (mid, end)) = gen.generate(random.Random()).value
            self.assertGreaterEqual(mid, base)
            self.assertLessEqual(mid, base + 5)
            self.assertGreaterEqual(end, mid)
            self.assertLessEqual(end, mid + 5)

    def test_chain_with_property_testing(self):
        """Test chain combinator with property-based testing."""

        @run_for_all(
            Gen.chain(Gen.int(1, 100), lambda x: Gen.int(x, x + 50)), num_runs=50
        )
        def test_range_property(pair):
            start, end = pair
            self.assertGreaterEqual(end, start)
            self.assertLessEqual(end, start + 50)

    def test_chain_preserves_types(self):
        """Test that chain works with different types."""
        # List chain - depends on list length
        list_gen = Gen.list(Gen.int(0, 10), min_length=1, max_length=5).chain(
            lambda lst: Gen.list(
                Gen.int(0, 10), min_length=len(lst), max_length=len(lst) + 3
            )
        )

        for _ in range(10):
            first, second = list_gen.generate(random.Random()).value
            self.assertGreaterEqual(len(second), len(first))
            self.assertLessEqual(len(second), len(first) + 3)

    def test_chain_complex_dependency(self):
        """Test chain with complex dependency logic."""

        def next_level_generator(level):
            if level < 5:
                return Gen.int(level + 1, level + 3)
            else:
                return Gen.int(level + 1, level + 1)

        gen = Gen.int(1, 10).chain(next_level_generator)

        for _ in range(20):
            base, next_val = gen.generate(random.Random()).value
            if base < 5:
                self.assertGreaterEqual(next_val, base + 1)
                self.assertLessEqual(next_val, base + 3)
            else:
                self.assertEqual(next_val, base + 1)


if __name__ == "__main__":
    unittest.main()
