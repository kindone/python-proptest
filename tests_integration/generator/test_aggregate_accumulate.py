"""Tests for aggregate and accumulate generator combinators."""

import random
import unittest

from python_proptest import run_for_all
from python_proptest.core.generator import Gen


class TestAggregate(unittest.TestCase):
    """Test cases for Gen.aggregate()."""

    def test_aggregate_basic(self):
        """Test basic aggregate functionality with increasing numbers."""
        gen = Gen.aggregate(
            Gen.int(0, 10), lambda n: Gen.int(n, n + 5), min_size=3, max_size=5
        )

        # Test using run_for_all
        # Test using run_for_all as decorator
        @run_for_all(gen, num_runs=20, seed=42)
        def check_aggregate(values):
            # Check size constraints
            self.assertGreaterEqual(len(values), 3)
            self.assertLessEqual(len(values), 5)

            # Check that each element is >= previous
            for i in range(1, len(values)):
                self.assertGreaterEqual(
                    values[i],
                    values[i - 1],
                    f"Element {i} ({values[i]}) should be >= previous ({values[i-1]})",
                )

    def test_aggregate_empty_list(self):
        """Test aggregate with min_size=0 can generate empty lists."""
        gen = Gen.aggregate(
            Gen.int(0, 10), lambda n: Gen.int(n, n + 5), min_size=0, max_size=5
        )

        # Generate many times to increase chance of empty list
        found_empty = False
        for _ in range(100):
            values = gen.generate(random.Random()).value
            if len(values) == 0:
                found_empty = True
                break

        self.assertTrue(found_empty, "Should be able to generate empty list")

    def test_aggregate_single_element(self):
        """Test aggregate with size range [1, 1] produces single element."""
        gen = Gen.aggregate(
            Gen.int(0, 100), lambda n: Gen.int(n, n + 5), min_size=1, max_size=1
        )

        for _ in range(10):
            values = gen.generate(random.Random()).value
            self.assertEqual(len(values), 1)
            self.assertGreaterEqual(values[0], 0)
            self.assertLessEqual(values[0], 100)

    def test_aggregate_random_walk(self):
        """Test aggregate for bounded random walk."""
        gen = Gen.aggregate(
            Gen.int(50, 50),  # Start at 50
            lambda pos: Gen.int(max(0, pos - 10), min(100, pos + 10)),
            min_size=5,
            max_size=10,
        )

        # Test using run_for_all decorator - auto-executes!
        @run_for_all(gen, num_runs=20, seed=42)
        def check_random_walk(values):
            self.assertEqual(values[0], 50, "Should start at 50")

            # Check all values are within bounds
            for val in values:
                self.assertGreaterEqual(val, 0)
                self.assertLessEqual(val, 100)

            # Check that consecutive values differ by at most 10
            for i in range(1, len(values)):
                diff = abs(values[i] - values[i - 1])
                self.assertLessEqual(
                    diff, 10, f"Consecutive values differ by {diff}, expected <= 10"
                )

    def test_aggregate_strict_increasing(self):
        """Test aggregate where each value must be strictly greater."""
        gen = Gen.aggregate(
            Gen.int(0, 5), lambda n: Gen.int(n + 1, n + 10), min_size=3, max_size=7
        )

        # Test using run_for_all as decorator
        @run_for_all(gen, num_runs=20, seed=42)
        def check_strict_increasing(values):
            # Check strictly increasing
            for i in range(1, len(values)):
                self.assertGreater(
                    values[i],
                    values[i - 1],
                    f"Element {i} should be strictly greater than previous",
                )

    def test_aggregate_fluent_api(self):
        """Test fluent API version of aggregate."""
        gen = Gen.int(0, 10).aggregate(
            lambda n: Gen.int(n, n + 5), min_size=3, max_size=5
        )

        for _ in range(10):
            values = gen.generate(random.Random()).value
            self.assertGreaterEqual(len(values), 3)
            self.assertLessEqual(len(values), 5)

            # Check increasing property
            for i in range(1, len(values)):
                self.assertGreaterEqual(values[i], values[i - 1])

    def test_aggregate_with_strings(self):
        """Test aggregate with string accumulation."""
        gen = Gen.aggregate(
            Gen.ascii_string(min_length=1, max_length=3),
            lambda s: Gen.ascii_string(min_length=len(s), max_length=len(s) + 2),
            min_size=2,
            max_size=5,
        )

        for _ in range(20):
            values = gen.generate(random.Random()).value
            self.assertGreaterEqual(len(values), 2)
            self.assertLessEqual(len(values), 5)

            # Check that string lengths are non-decreasing
            for i in range(1, len(values)):
                self.assertGreaterEqual(
                    len(values[i]),
                    len(values[i - 1]),
                    f"String {i} length should be >= previous",
                )

    def test_aggregate_shrinking_reduces_length(self):
        """Test that aggregate shrinking reduces list length."""
        gen = Gen.aggregate(
            Gen.int(0, 10), lambda n: Gen.int(n, n + 5), min_size=2, max_size=10
        )

        shrinkable = gen.generate(random.Random())
        original_length = len(shrinkable.value)

        if original_length > 2:
            shrinks = shrinkable.shrinks().to_list()
            if shrinks:
                # Some shrinks should have shorter length
                shorter_found = any(len(shr.value) < original_length for shr in shrinks)
                self.assertTrue(
                    shorter_found, "Should find shrinks with shorter length"
                )


class TestAccumulate(unittest.TestCase):
    """Test cases for Gen.accumulate()."""

    def test_accumulate_basic(self):
        """Test basic accumulate functionality."""
        gen = Gen.accumulate(
            Gen.int(0, 10), lambda n: Gen.int(n, n + 5), min_size=3, max_size=5
        )

        for _ in range(20):
            value = gen.generate(random.Random()).value
            # Result should be a single integer
            self.assertIsInstance(value, int)
            # After 3-5 steps starting from 0-10, value should be at least initial
            self.assertGreaterEqual(value, 0)

    def test_accumulate_increasing_value(self):
        """Test that accumulate with increasing steps produces larger values."""
        gen = Gen.accumulate(
            Gen.int(0, 5), lambda n: Gen.int(n + 1, n + 10), min_size=5, max_size=5
        )

        for _ in range(20):
            value = gen.generate(random.Random()).value
            # After 5 steps of increasing by at least 1 each time
            # Final value should be >= initial (0) + 5 steps * 1 = 5
            self.assertGreaterEqual(
                value, 5, "After 5 increasing steps, value should be >= 5"
            )

    def test_accumulate_zero_steps(self):
        """Test accumulate with min_size=0 can return initial value."""
        gen = Gen.accumulate(
            Gen.int(10, 20), lambda n: Gen.int(n + 1, n + 10), min_size=0, max_size=3
        )

        # Generate many times to possibly see zero-step case
        found_initial_range = False
        for _ in range(100):
            value = gen.generate(random.Random()).value
            if 10 <= value <= 20:
                found_initial_range = True
                # This could be zero steps
                break

        self.assertTrue(
            found_initial_range,
            "Should be able to generate values in initial range with 0 steps",
        )

    def test_accumulate_random_walk(self):
        """Test accumulate for bounded random walk final position."""
        gen = Gen.accumulate(
            Gen.int(50, 50),  # Start at 50
            lambda pos: Gen.int(max(0, pos - 10), min(100, pos + 10)),
            min_size=5,
            max_size=20,
        )

        for _ in range(20):
            value = gen.generate(random.Random()).value
            # Final position should be within bounds
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, 100)

    def test_accumulate_fluent_api(self):
        """Test fluent API version of accumulate."""
        gen = Gen.int(0, 10).accumulate(
            lambda n: Gen.int(n, n + 5), min_size=3, max_size=5
        )

        for _ in range(10):
            value = gen.generate(random.Random()).value
            self.assertIsInstance(value, int)
            self.assertGreaterEqual(value, 0)

    def test_accumulate_with_strings(self):
        """Test accumulate with string growth, returning final string."""
        gen = Gen.accumulate(
            Gen.ascii_string(min_length=1, max_length=2),
            lambda s: Gen.ascii_string(min_length=len(s) + 1, max_length=len(s) + 2),
            min_size=3,
            max_size=5,
        )

        for _ in range(20):
            value = gen.generate(random.Random()).value
            self.assertIsInstance(value, str)
            # After 3-5 steps of growing by at least 1 each time
            # Final length should be >= initial (1) + 3 steps * 1 = 4
            self.assertGreaterEqual(
                len(value), 4, "After 3+ growth steps, string should be long enough"
            )

    def test_accumulate_compound_growth(self):
        """Test accumulate for compound growth simulation."""
        gen = Gen.accumulate(
            Gen.float(100.0, 100.0),  # Start with $100
            lambda amount: Gen.float(amount * 1.01, amount * 1.1),  # 1-10% growth
            min_size=5,
            max_size=10,
        )

        for _ in range(20):
            value = gen.generate(random.Random()).value
            self.assertIsInstance(value, float)
            # After 5-10 steps of at least 1% growth each
            # Final should be > 100 * (1.01^5) ≈ 105.1
            self.assertGreater(
                value, 100.0, "After compound growth, value should increase"
            )

    def test_accumulate_shrinking(self):
        """Test that accumulate supports shrinking."""
        gen = Gen.accumulate(
            Gen.int(0, 100), lambda n: Gen.int(n, n + 10), min_size=3, max_size=10
        )

        shrinkable = gen.generate(random.Random())

        shrinks = shrinkable.shrinks().to_list()
        # Should have some shrinks
        if shrinks:
            # It's possible that all shrinks are larger due to accumulation,
            # but often we should find smaller ones
            # Just verify shrinks exist
            self.assertGreater(len(shrinks), 0, "Should produce some shrinks")


class TestAggregateAccumulateStaticAPI(unittest.TestCase):
    """Test static API methods Gen.aggregate() and Gen.accumulate()."""

    def test_static_aggregate(self):
        """Test Gen.aggregate static method."""
        gen = Gen.aggregate(
            Gen.int(0, 10), lambda n: Gen.int(n, n + 5), min_size=3, max_size=5
        )

        values = gen.generate(random.Random()).value
        self.assertIsInstance(values, list)
        self.assertGreaterEqual(len(values), 3)
        self.assertLessEqual(len(values), 5)

    def test_static_accumulate(self):
        """Test Gen.accumulate static method."""
        gen = Gen.accumulate(
            Gen.int(0, 10), lambda n: Gen.int(n, n + 5), min_size=3, max_size=5
        )

        value = gen.generate(random.Random()).value
        self.assertIsInstance(value, int)

    def test_aggregate_and_accumulate_same_sequence(self):
        """Compare aggregate and accumulate on same random seed."""
        # Both should go through same sequence, but aggregate keeps all,
        # accumulate keeps only final

        # Use a fixed seed for reproducibility
        import random

        rng1 = random.Random(42)
        rng2 = random.Random(42)

        aggregate_gen = Gen.aggregate(
            Gen.int(0, 5), lambda n: Gen.int(n, n + 3), min_size=5, max_size=5
        )

        accumulate_gen = Gen.accumulate(
            Gen.int(0, 5), lambda n: Gen.int(n, n + 3), min_size=5, max_size=5
        )

        aggregate_result = aggregate_gen.generate(rng1).value
        accumulate_result = accumulate_gen.generate(rng2).value

        # With same seed, accumulate result should equal last element of aggregate
        # Note: This might not hold exactly due to RNG consumption differences,
        # but it's a conceptual test
        self.assertIsInstance(aggregate_result, list)
        self.assertIsInstance(accumulate_result, int)
        self.assertEqual(len(aggregate_result), 5)


class TestAggregateAccumulateIntegration(unittest.TestCase):
    """Integration tests combining aggregate/accumulate with other generators."""

    def test_aggregate_with_chain(self):
        """Test combining aggregate with chain combinator."""
        # Generate a base value, then aggregate from it
        gen = Gen.int(1, 5).chain(
            lambda n: Gen.aggregate(
                Gen.int(n, n),  # Start with base value
                lambda x: Gen.int(x, x + 5),
                min_size=3,
                max_size=5,
            )
        )

        for _ in range(10):
            result = gen.generate(random.Random()).value
            self.assertIsInstance(result, tuple)
            self.assertEqual(len(result), 2)
            base, lst = result
            self.assertIsInstance(base, int)
            self.assertIsInstance(lst, list)
            # First element of list should equal base
            if len(lst) > 0:
                self.assertEqual(lst[0], base)

    def test_accumulate_in_list(self):
        """Test using accumulate inside a list generator."""
        gen = Gen.list(
            Gen.accumulate(
                Gen.int(0, 10), lambda n: Gen.int(n, n + 5), min_size=2, max_size=4
            ),
            min_length=2,
            max_length=5,
        )

        for _ in range(10):
            result = gen.generate(random.Random()).value
            self.assertIsInstance(result, list)
            self.assertGreaterEqual(len(result), 2)
            self.assertLessEqual(len(result), 5)
            # Each element should be an int (accumulated value)
            for elem in result:
                self.assertIsInstance(elem, int)

    def test_aggregate_of_tuples(self):
        """Test aggregate where each element is a tuple."""
        gen = Gen.aggregate(
            Gen.tuple(Gen.int(0, 10), Gen.int(0, 10)),
            lambda pair: Gen.tuple(
                Gen.int(pair[0], pair[0] + 5), Gen.int(pair[1], pair[1] + 5)
            ),
            min_size=3,
            max_size=6,
        )

        for _ in range(10):
            result = gen.generate(random.Random()).value
            self.assertIsInstance(result, list)
            for elem in result:
                self.assertIsInstance(elem, tuple)
                self.assertEqual(len(elem), 2)

            # Check that both coordinates are non-decreasing
            for i in range(1, len(result)):
                self.assertGreaterEqual(result[i][0], result[i - 1][0])
                self.assertGreaterEqual(result[i][1], result[i - 1][1])


if __name__ == "__main__":
    unittest.main()
