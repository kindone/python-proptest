"""
Tests for standalone @matrix and @example decorators without @for_all.
"""

import unittest

from python_proptest import example, matrix


class TestStandaloneMatrix(unittest.TestCase):
    """Test @matrix decorator used standalone (without @for_all)."""

    def test_matrix_standalone_basic(self):
        """Test that @matrix works standalone with simple values."""
        results = []

        @matrix(x=[1, 2], y=[10, 20])
        def collect_results(self, x, y):
            results.append((x, y))

        # Call with only self - should execute all matrix combinations
        collect_results(self)

        # Should have 2 * 2 = 4 combinations
        self.assertEqual(len(results), 4)
        self.assertIn((1, 10), results)
        self.assertIn((1, 20), results)
        self.assertIn((2, 10), results)
        self.assertIn((2, 20), results)

    def test_matrix_standalone_with_assertions(self):
        """Test that @matrix standalone properly propagates test assertions."""

        @matrix(x=[1, 2, 3], y=[0, 1])
        def test_property(self, x, y):
            # This should work for all combinations
            self.assertGreaterEqual(x, 1)
            self.assertGreaterEqual(y, 0)
            self.assertLessEqual(x, 3)

        # Should not raise - all assertions pass
        test_property(self)

    def test_matrix_standalone_failure_propagates(self):
        """Test that failures in matrix cases propagate correctly."""

        @matrix(x=[1, 2, 3], y=[0, 1])
        def test_property(self, x, y):
            # This will fail for x=1, y=0
            self.assertGreater(x + y, 1)

        # Should raise AssertionError on first failing case
        with self.assertRaises(AssertionError):
            test_property(self)

    def test_matrix_multiple_decorators_standalone(self):
        """Test that multiple @matrix decorators work standalone."""
        results = []

        @matrix(x=[1, 2], y=[100])  # Complete spec 1
        @matrix(x=[3], y=[10, 20])  # Complete spec 2
        def collect_results(self, x, y):
            results.append((x, y))

        collect_results(self)

        # First matrix: x=[1,2], y=[100] → 2 cases: (1,100), (2,100)
        # Second matrix: x=[3], y=[10,20] → 2 cases: (3,10), (3,20)
        # Total: 4 cases
        self.assertEqual(len(results), 4)
        self.assertIn((1, 100), results)
        self.assertIn((2, 100), results)
        self.assertIn((3, 10), results)
        self.assertIn((3, 20), results)

    def test_matrix_single_parameter(self):
        """Test @matrix with single parameter."""
        results = []

        @matrix(value=[1, 2, 3, 4, 5])
        def collect_value(self, value):
            results.append(value)

        collect_value(self)

        self.assertEqual(results, [1, 2, 3, 4, 5])


class TestStandaloneExample(unittest.TestCase):
    """Test @example decorator used standalone (without @for_all)."""

    def test_example_standalone_positional(self):
        """Test that @example works standalone with positional arguments."""
        results = []

        @example(1, 10)
        @example(2, 20)
        def collect_results(self, x, y):
            results.append((x, y))

        collect_results(self)

        self.assertEqual(len(results), 2)
        self.assertIn((1, 10), results)
        self.assertIn((2, 20), results)

    def test_example_standalone_named(self):
        """Test that @example works standalone with named arguments."""
        results = []

        @example(x=5, y=50)
        @example(x=6, y=60)
        def collect_results(self, x, y):
            results.append((x, y))

        collect_results(self)

        self.assertEqual(len(results), 2)
        self.assertIn((5, 50), results)
        self.assertIn((6, 60), results)

    def test_example_standalone_mixed(self):
        """Test that @example works standalone with mixed arguments."""
        results = []

        @example(7, y=70)
        @example(8, y=80)
        def collect_results(self, x, y):
            results.append((x, y))

        collect_results(self)

        self.assertEqual(len(results), 2)
        self.assertIn((7, 70), results)
        self.assertIn((8, 80), results)

    def test_example_standalone_with_assertions(self):
        """Test that @example standalone properly propagates test assertions."""

        @example(10, 5)
        @example(20, 10)
        @example(30, 15)
        def test_property(self, x, y):
            self.assertGreater(x, y)
            self.assertEqual(x, y * 2)

        # Should not raise - all assertions pass
        test_property(self)

    def test_example_standalone_failure_propagates(self):
        """Test that failures in example cases propagate correctly."""

        @example(10, 5)
        @example(20, 10)
        @example(30, 20)  # This will fail: 30 != 20 * 2
        def test_property(self, x, y):
            self.assertEqual(x, y * 2)

        # Should raise AssertionError on failing example
        with self.assertRaises(AssertionError):
            test_property(self)

    def test_example_edge_cases(self):
        """Test @example with edge case values."""
        results = []

        @example(0, "")
        @example(-1, "negative")
        @example(None, None)
        def collect_results(self, x, y):
            results.append((x, y))

        collect_results(self)

        self.assertEqual(len(results), 3)
        self.assertIn((0, ""), results)
        self.assertIn((-1, "negative"), results)
        self.assertIn((None, None), results)


class TestMatrixAndExampleCombined(unittest.TestCase):
    """Test combining @matrix and @example decorators standalone."""

    def test_matrix_and_example_both_standalone(self):
        """Test that @matrix and @example can both be used standalone together."""
        results = []

        @example(0, 0)  # Example case
        @matrix(x=[1, 2], y=[10, 20])  # Matrix cases
        def collect_results(self, x, y):
            results.append((x, y))

        collect_results(self)

        # Should have 1 example + 4 matrix cases = 5 total
        self.assertEqual(len(results), 5)
        self.assertIn((0, 0), results)  # Example
        self.assertIn((1, 10), results)  # Matrix
        self.assertIn((1, 20), results)
        self.assertIn((2, 10), results)
        self.assertIn((2, 20), results)


class TestStandaloneDecoratorsNonMethod(unittest.TestCase):
    """Test standalone decorators on non-method functions."""

    def test_matrix_standalone_function(self):
        """Test @matrix on a standalone function (not a method)."""
        results = []

        @matrix(x=[1, 2], y=[10, 20])
        def collect_results(x, y):
            results.append((x, y))

        # Call with no arguments - should execute all matrix combinations
        collect_results()

        self.assertEqual(len(results), 4)
        self.assertIn((1, 10), results)
        self.assertIn((1, 20), results)
        self.assertIn((2, 10), results)
        self.assertIn((2, 20), results)

    def test_example_standalone_function(self):
        """Test @example on a standalone function (not a method)."""
        results = []

        @example(5, 50)
        @example(6, 60)
        def collect_results(x, y):
            results.append((x, y))

        # Call with no arguments
        collect_results()

        self.assertEqual(len(results), 2)
        self.assertIn((5, 50), results)
        self.assertIn((6, 60), results)


if __name__ == "__main__":
    unittest.main()
