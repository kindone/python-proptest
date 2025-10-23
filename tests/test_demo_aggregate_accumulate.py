"""Test/demo of aggregate and accumulate generator combinators.

This demonstrates the aggregate and accumulate features with executable tests.
"""

import random
import unittest

from python_proptest import Gen


class TestAggregateDemo(unittest.TestCase):
    """Demonstrate Gen.aggregate() - returns list of dependent values."""

    def test_aggregate_increasing_sequence(self):
        """Test aggregate with increasing sequence."""
        gen = Gen.aggregate(
            Gen.int(0, 10), lambda n: Gen.int(n, n + 5), min_size=5, max_size=8
        )

        for _ in range(10):
            result = gen.generate(random.Random()).value
            self.assertGreaterEqual(len(result), 5)
            self.assertLessEqual(len(result), 8)
            # Verify increasing property
            for i in range(len(result) - 1):
                self.assertLessEqual(result[i], result[i + 1])

    def test_aggregate_random_walk(self):
        """Test aggregate with bounded random walk."""
        gen = Gen.aggregate(
            Gen.int(50, 50),  # Start at 50
            lambda pos: Gen.int(max(0, pos - 10), min(100, pos + 10)),
            min_size=10,
            max_size=15,
        )

        for _ in range(10):
            result = gen.generate(random.Random()).value
            self.assertEqual(result[0], 50)  # Always starts at 50
            self.assertGreaterEqual(len(result), 10)
            self.assertLessEqual(len(result), 15)
            # All values should be in valid range
            for val in result:
                self.assertGreaterEqual(val, 0)
                self.assertLessEqual(val, 100)

    def test_aggregate_fluent_api(self):
        """Test aggregate using fluent API."""
        gen = Gen.int(0, 5).aggregate(
            lambda n: Gen.int(n + 1, n + 10), min_size=4, max_size=7
        )

        for _ in range(10):
            result = gen.generate(random.Random()).value
            self.assertGreaterEqual(len(result), 4)
            self.assertLessEqual(len(result), 7)
            # Verify strictly increasing
            for i in range(len(result) - 1):
                self.assertLess(result[i], result[i + 1])


class TestAccumulateDemo(unittest.TestCase):
    """Demonstrate Gen.accumulate() - returns only final value."""

    def test_accumulate_random_walk_final_position(self):
        """Test accumulate with random walk - returns final position only."""
        gen = Gen.accumulate(
            Gen.int(50, 50),
            lambda pos: Gen.int(max(0, pos - 5), min(100, pos + 5)),
            min_size=10,
            max_size=20,
        )

        for _ in range(10):
            result = gen.generate(random.Random()).value
            # Result is a single integer, not a list
            self.assertIsInstance(result, int)
            self.assertGreaterEqual(result, 0)
            self.assertLessEqual(result, 100)

    def test_accumulate_compound_growth(self):
        """Test accumulate with compound growth."""
        gen = Gen.accumulate(
            Gen.float(100.0, 100.0),
            lambda amount: Gen.float(amount * 1.01, amount * 1.1),
            min_size=5,
            max_size=10,
        )

        for _ in range(10):
            result = gen.generate(random.Random()).value
            # Result should be a float > 100 (growth)
            self.assertIsInstance(result, float)
            self.assertGreater(result, 100.0)

    def test_accumulate_fluent_api(self):
        """Test accumulate using fluent API."""
        gen = Gen.int(0, 10).accumulate(
            lambda n: Gen.int(n + 1, n + 5), min_size=10, max_size=15
        )

        for _ in range(10):
            result = gen.generate(random.Random()).value
            self.assertIsInstance(result, int)
            # After 10-15 steps of +1 to +5, should be significantly larger
            self.assertGreater(result, 10)


class TestAggregateVsAccumulate(unittest.TestCase):
    """Compare aggregate vs accumulate with same configuration."""

    def test_aggregate_returns_list(self):
        """Test that aggregate returns a list of all steps."""
        gen = Gen.aggregate(
            Gen.int(0, 5), lambda n: Gen.int(n, n + 3), min_size=5, max_size=5
        )
        result = gen.generate(random.Random()).value

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 5)

    def test_accumulate_returns_single_value(self):
        """Test that accumulate returns only the final value."""
        gen = Gen.accumulate(
            Gen.int(0, 5), lambda n: Gen.int(n, n + 3), min_size=5, max_size=5
        )
        result = gen.generate(random.Random()).value

        # Returns single int, not list
        self.assertIsInstance(result, int)
        self.assertNotIsInstance(result, list)


class TestIntegration(unittest.TestCase):
    """Demonstrate integration with other generators."""

    def test_chain_with_aggregate(self):
        """Test combining chain with aggregate."""
        gen = Gen.int(1, 5).chain(
            lambda n: Gen.aggregate(
                Gen.int(n, n), lambda x: Gen.int(x, x + 5), min_size=3, max_size=5
            )
        )

        for _ in range(10):
            base, sequence = gen.generate(random.Random()).value
            self.assertIsInstance(sequence, list)
            self.assertGreaterEqual(len(sequence), 3)
            self.assertLessEqual(len(sequence), 5)
            # First element should equal base
            self.assertEqual(sequence[0], base)

    def test_list_of_accumulate_results(self):
        """Test list of accumulate results."""
        gen = Gen.list(
            Gen.accumulate(
                Gen.int(0, 10), lambda n: Gen.int(n, n + 5), min_size=3, max_size=5
            ),
            min_length=3,
            max_length=5,
        )

        for _ in range(10):
            result = gen.generate(random.Random()).value
            self.assertIsInstance(result, list)
            self.assertGreaterEqual(len(result), 3)
            self.assertLessEqual(len(result), 5)
            # Each element should be an int (not a list)
            for elem in result:
                self.assertIsInstance(elem, int)


if __name__ == "__main__":
    unittest.main()
