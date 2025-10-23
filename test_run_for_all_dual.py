"""Test that run_for_all works both as function and decorator."""

import unittest

from python_proptest import Gen, run_for_all


class TestRunForAllDual(unittest.TestCase):
    """Test dual-mode run_for_all."""

    def test_function_mode(self):
        """Test run_for_all as a function."""

        def check(x, y):
            return x + y == y + x

        result = run_for_all(
            check, Gen.int(0, 100), Gen.int(0, 100), num_runs=10, seed=42
        )
        self.assertTrue(result)

    def test_decorator_mode_simple(self):
        """Test run_for_all as a simple decorator."""

        @run_for_all(Gen.int(0, 100), Gen.int(0, 100), num_runs=10, seed=42)
        def check_addition(x, y):
            self.assertEqual(x + y, y + x)

        @run_for_all(
            Gen.int(1, 10).chain(lambda x: Gen.int(x, x + 10)), num_runs=20, seed=42
        )
        def check_decorator_mode_chain(pair):
            """Test run_for_all as a decorator with chain."""
            base, dependent = pair
            self.assertGreaterEqual(dependent, base)
            self.assertLessEqual(dependent, base + 10)

        @run_for_all(
            Gen.aggregate(
                Gen.int(0, 10), lambda n: Gen.int(n, n + 5), min_size=3, max_size=5
            ),
            num_runs=15,
            seed=42,
        )
        def check_decorator_mode_aggregate(values):
            """Test run_for_all as a decorator with aggregate."""
            self.assertGreaterEqual(len(values), 3)
            self.assertLessEqual(len(values), 5)

            # Check each value is >= previous
            for i in range(1, len(values)):
                self.assertGreaterEqual(values[i], values[i - 1])

        @run_for_all(
            Gen.list(Gen.int(0, 100), min_length=0, max_length=10), num_runs=10, seed=42
        )
        def check_decorator_mode_list(lst):
            """Test run_for_all as a decorator with list."""
            self.assertGreaterEqual(len(lst), 0)
            self.assertLessEqual(len(lst), 10)
            for x in lst:
                self.assertGreaterEqual(x, 0)
                self.assertLessEqual(x, 100)

    def test_nested_function_decorator_mode(self):
        """Test run_for_all as decorator on nested function - auto-executes."""
        gen = Gen.chain(Gen.int(1, 10), lambda x: Gen.int(x, x + 10))

        # Track that the property test actually runs
        execution_count = {"count": 0}

        # This decorator should execute immediately when check_property is defined
        @run_for_all(gen, num_runs=15, seed=42)
        def check_property(pair):
            execution_count["count"] += 1
            base, dependent = pair
            self.assertIsInstance(pair, tuple)
            self.assertGreaterEqual(base, 1)
            self.assertLessEqual(base, 10)
            self.assertGreaterEqual(dependent, base)
            self.assertLessEqual(dependent, base + 10)

        # No explicit call needed - the decorator already executed the property test!
        # Verify it actually ran
        self.assertEqual(
            execution_count["count"], 15, "Property test should have run 15 times"
        )

    def test_nested_function_with_aggregate(self):
        """Test nested function decorator with aggregate generator."""
        gen = Gen.aggregate(
            Gen.int(0, 5), lambda n: Gen.int(n, n + 3), min_size=3, max_size=6
        )

        execution_count = {"count": 0}

        @run_for_all(gen, num_runs=20, seed=42)
        def check_aggregate(values):
            execution_count["count"] += 1
            self.assertGreaterEqual(len(values), 3)
            self.assertLessEqual(len(values), 6)

            # Check non-decreasing
            for i in range(1, len(values)):
                self.assertGreaterEqual(values[i], values[i - 1])

        # Verify execution
        self.assertEqual(
            execution_count["count"], 20, "Property test should have run 20 times"
        )

    def test_nested_function_with_accumulate(self):
        """Test nested function decorator with accumulate generator."""
        gen = Gen.accumulate(
            Gen.int(10, 20), lambda n: Gen.int(n + 1, n + 5), min_size=5, max_size=5
        )

        execution_count = {"count": 0}

        @run_for_all(gen, num_runs=10, seed=42)
        def check_accumulate(final_value):
            execution_count["count"] += 1
            # After 5 steps of increasing by at least 1 each
            # Starting from 10-20, final should be >= initial + 5
            self.assertGreaterEqual(final_value, 15)

        # Verify execution
        self.assertEqual(
            execution_count["count"], 10, "Property test should have run 10 times"
        )


if __name__ == "__main__":
    unittest.main()
