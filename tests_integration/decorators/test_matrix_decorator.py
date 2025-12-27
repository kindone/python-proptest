"""
Tests for the @matrix decorator and run_matrix function.

This module tests the matrix functionality that provides exhaustive
Cartesian product testing of fixed input combinations.
"""

import unittest
from unittest.mock import Mock

from python_proptest import Gen, for_all, matrix, run_matrix


class TestMatrixDecorator(unittest.TestCase):
    """Test the @matrix decorator functionality."""

    def test_matrix_decorator_stores_spec(self):
        """Test that @matrix decorator stores the matrix specification."""

        @matrix(x=[1, 2], y=["a", "b"])
        def test_func(x, y):
            pass

        # Check that matrix specs are stored as a list
        self.assertTrue(hasattr(test_func, "_proptest_matrices"))
        self.assertEqual(test_func._proptest_matrices, [{"x": [1, 2], "y": ["a", "b"]}])

    def test_matrix_decorator_stores_multiple_specs_separately(self):
        """Test that multiple @matrix decorators store separate specifications."""

        @matrix(x=[1, 2])
        @matrix(y=["a", "b"])
        def test_func(x, y):
            pass

        # Check that each decorator creates a separate matrix spec
        # Decorators are applied bottom-up, so bottom decorator is first in the list
        expected = [{"y": ["a", "b"]}, {"x": [1, 2]}]
        self.assertEqual(test_func._proptest_matrices, expected)

    def test_matrix_decorator_creates_separate_cases_for_overlapping_keys(self):
        """Test that overlapping keys in multiple @matrix decorators create separate cases."""

        @matrix(x=[1, 2], y=["a"])
        @matrix(x=[3, 4], y=["b", "c"])
        def test_func(x, y):
            pass

        # Each decorator creates separate matrix cases (no merging)
        # Decorators are applied bottom-up, so bottom decorator is first in the list
        expected = [{"x": [3, 4], "y": ["b", "c"]}, {"x": [1, 2], "y": ["a"]}]
        self.assertEqual(test_func._proptest_matrices, expected)

    def test_matrix_decorator_allows_partial_keys(self):
        """Test that @matrix decorators can have different keys (no restriction)."""

        @matrix(x=[3, 4])  # Top decorator - only x
        @matrix(x=[1, 2], y=["a"])  # Bottom decorator - has x and y
        def test_func(x, y):
            pass

        # Each decorator creates separate matrix cases, so partial keys are fine
        expected = [{"x": [1, 2], "y": ["a"]}, {"x": [3, 4]}]
        self.assertEqual(test_func._proptest_matrices, expected)

    def test_matrix_decorator_allows_completely_different_keys(self):
        """Test that completely different keys in multiple decorators are allowed."""

        @matrix(x=[1, 2])
        @matrix(y=["a", "b"])
        @matrix(z=[True, False])
        def test_func(x, y, z):
            pass

        # Each decorator creates separate matrix cases
        expected = [{"z": [True, False]}, {"y": ["a", "b"]}, {"x": [1, 2]}]
        self.assertEqual(test_func._proptest_matrices, expected)

    def test_matrix_with_for_all_integration(self):
        """Test that @matrix works with @for_all decorator."""
        call_count = 0
        matrix_calls = []

        @for_all(Gen.int(1, 10), Gen.str(1, 5))
        @matrix(x=[0, 1], s=["test"])
        def test_property(x, s):
            nonlocal call_count
            call_count += 1
            if x in [0, 1] and s == "test":
                matrix_calls.append((x, s))
            # Property should pass for all inputs
            assert isinstance(x, int)
            assert isinstance(s, str)

        # Run the test
        test_property()

        # Should have run matrix cases (2 combinations) plus random cases
        self.assertGreaterEqual(call_count, 2)
        # Matrix cases should have been executed
        self.assertEqual(set(matrix_calls), {(0, "test"), (1, "test")})

    def test_matrix_with_for_all_method(self):
        """Test that @matrix works with @for_all on class methods."""
        call_count = 0
        matrix_calls = []

        class TestClass(unittest.TestCase):
            @for_all(Gen.int(1, 10), Gen.str(1, 5))
            @matrix(x=[0, 1], s=["test"])
            def test_property(self, x, s):
                nonlocal call_count
                call_count += 1
                if x in [0, 1] and s == "test":
                    matrix_calls.append((x, s))
                # Property should pass for all inputs
                self.assertIsInstance(x, int)
                self.assertIsInstance(s, str)

        # Run the test
        test_instance = TestClass()
        test_instance.test_property()

        # Should have run matrix cases (2 combinations) plus random cases
        self.assertGreaterEqual(call_count, 2)
        # Matrix cases should have been executed
        self.assertEqual(set(matrix_calls), {(0, "test"), (1, "test")})

    def test_matrix_cases_dont_count_toward_num_runs(self):
        """Test that matrix cases don't count toward the num_runs setting."""
        call_count = 0

        @for_all(Gen.int(1, 10))
        @matrix(x=[0, 1, 2])
        def test_property(x):
            nonlocal call_count
            call_count += 1
            assert isinstance(x, int)

        # Run with small num_runs
        test_property()

        # Should have 3 matrix cases + at least some random cases
        # Total should be more than just the matrix cases
        self.assertGreater(call_count, 3)

    def test_matrix_with_settings_integration(self):
        """Test that @matrix works with @settings decorator."""
        call_count = 0
        matrix_calls = []

        @for_all(Gen.int(1, 10))
        @matrix(xx=[0, 1])
        def test_property(xx):
            nonlocal call_count
            call_count += 1
            if xx in [0, 1]:
                matrix_calls.append(xx)
            assert isinstance(xx, int)

        # Run the test
        test_property()

        # Matrix cases should be executed
        self.assertEqual(set(matrix_calls), {0, 1})
        # Should have more calls than just matrix cases
        self.assertGreater(call_count, 2)

    def test_matrix_with_example_integration(self):
        """Test that @matrix works with @example decorator."""
        call_count = 0
        matrix_calls = []
        example_calls = []

        @for_all(Gen.int(1, 10))
        @matrix(x=[0, 1])
        def test_property(x):
            nonlocal call_count
            call_count += 1
            if x in [0, 1]:
                matrix_calls.append(x)
            elif x == 42:
                example_calls.append(x)
            assert isinstance(x, int)

        # Add example after the function is defined
        from python_proptest import example

        test_property = example(42)(test_property)

        # Run the test
        test_property()

        # Matrix cases should be executed
        self.assertEqual(set(matrix_calls), {0, 1})
        # Example cases should also be executed
        self.assertIn(42, example_calls)

    def test_matrix_skips_incomplete_combinations(self):
        """Test that matrix skips combinations that don't cover all parameters."""
        call_count = 0
        matrix_calls = []

        @for_all(Gen.int(1, 10), Gen.str(1, 5))
        @matrix(x=[0, 1])  # Only provide x, not y
        def test_property(x, y):
            nonlocal call_count
            call_count += 1
            # Only count as matrix call if both x and y are from matrix spec
            if x in [0, 1] and y in ["matrix_a", "matrix_b"]:
                matrix_calls.append((x, y))
            assert isinstance(x, int)
            assert isinstance(y, str)

        # Run the test
        test_property()

        # Should not have executed matrix cases since y is missing from matrix spec
        self.assertEqual(len(matrix_calls), 0)
        # Should still have random cases
        self.assertGreater(call_count, 0)

    def test_matrix_empty_spec(self):
        """Test that empty matrix specification doesn't cause issues."""
        call_count = 0

        @for_all(Gen.int(1, 10))
        @matrix()  # Empty matrix
        def test_property(x):
            nonlocal call_count
            call_count += 1
            assert isinstance(x, int)

        # Run the test
        test_property()

        # Should only have random cases
        self.assertGreater(call_count, 0)

    def test_matrix_single_value(self):
        """Test matrix with single values."""
        call_count = 0
        matrix_calls = []

        @for_all(Gen.int(1, 10))
        @matrix(x=[42])
        def test_property(x):
            nonlocal call_count
            call_count += 1
            if x == 42:
                matrix_calls.append(x)
            assert isinstance(x, int)

        # Run the test
        test_property()

        # Should have executed the single matrix case
        self.assertEqual(matrix_calls, [42])
        # Should have more calls than just the matrix case
        self.assertGreater(call_count, 1)


class TestRunMatrixFunction(unittest.TestCase):
    """Test the run_matrix function functionality."""

    def test_run_matrix_basic(self):
        """Test basic run_matrix functionality."""
        calls = []

        def test_func(x, y):
            calls.append((x, y))

        matrix_spec = {"x": [1, 2], "y": ["a", "b"]}
        run_matrix(test_func, matrix_spec)

        # Should have called with all combinations
        expected = [(1, "a"), (1, "b"), (2, "a"), (2, "b")]
        self.assertEqual(calls, expected)

    def test_run_matrix_with_self_obj(self):
        """Test run_matrix with self_obj parameter."""
        calls = []

        def test_method(self, x, y):
            calls.append((x, y))

        matrix_spec = {"x": [1, 2], "y": ["a"]}
        mock_self = Mock()
        run_matrix(test_method, matrix_spec, self_obj=mock_self)

        # Should have called with all combinations
        expected = [(1, "a"), (2, "a")]
        self.assertEqual(calls, expected)

    def test_run_matrix_skips_incomplete_combinations(self):
        """Test that run_matrix skips combinations that don't cover all parameters."""
        calls = []

        def test_func(x, y, z):
            calls.append((x, y, z))

        matrix_spec = {"x": [1, 2], "y": ["a"]}  # Missing z
        run_matrix(test_func, matrix_spec)

        # Should not have called since z is missing
        self.assertEqual(len(calls), 0)

    def test_run_matrix_single_parameter(self):
        """Test run_matrix with single parameter."""
        calls = []

        def test_func(x):
            calls.append(x)

        matrix_spec = {"x": [1, 2, 3]}
        run_matrix(test_func, matrix_spec)

        # Should have called with all values
        self.assertEqual(calls, [1, 2, 3])

    def test_run_matrix_empty_spec(self):
        """Test run_matrix with empty specification."""
        calls = []

        def test_func(x):
            calls.append(x)

        matrix_spec = {}
        run_matrix(test_func, matrix_spec)

        # Should not have called since no parameters provided
        self.assertEqual(len(calls), 0)

    def test_run_matrix_parameter_order(self):
        """Test that run_matrix respects function parameter order."""
        calls = []

        def test_func(b, a, c):
            calls.append((b, a, c))

        matrix_spec = {"a": [1, 2], "b": ["x", "y"], "c": [True, False]}
        run_matrix(test_func, matrix_spec)

        # Should call in function parameter order: b, a, c
        # Cartesian product order: (a=1,b=x,c=True), (a=1,b=x,c=False), (a=1,b=y,c=True), etc.
        expected = [
            ("x", 1, True),
            ("x", 1, False),
            ("y", 1, True),
            ("y", 1, False),
            ("x", 2, True),
            ("x", 2, False),
            ("y", 2, True),
            ("y", 2, False),
        ]
        self.assertEqual(calls, expected)

    def test_run_matrix_with_method_but_no_self_obj(self):
        """Test run_matrix with method signature but no self_obj raises error."""

        def test_method(self, x):
            pass

        matrix_spec = {"x": [1, 2]}

        with self.assertRaises(ValueError) as cm:
            run_matrix(test_method, matrix_spec)

        self.assertIn("self_obj must be provided", str(cm.exception))

    def test_run_matrix_ignores_extra_parameters(self):
        """Test that run_matrix ignores extra parameters in matrix spec."""
        calls = []

        def test_func(x):
            calls.append(x)

        matrix_spec = {"x": [1, 2], "y": ["a", "b"]}  # y is extra
        run_matrix(test_func, matrix_spec)

        # Should only call with x values
        self.assertEqual(calls, [1, 2])


class TestMatrixIntegration(unittest.TestCase):
    """Test matrix integration with other decorators and features."""

    def test_matrix_with_assume(self):
        """Test that matrix works with assume() calls."""
        call_count = 0
        matrix_calls = []

        @for_all(Gen.int(1, 10))
        @matrix(x=[0, 1, 2])
        def test_property(x):
            nonlocal call_count
            call_count += 1

            # Assume x is even
            from python_proptest import assume

            assume(x % 2 == 0)

            # Only count as matrix call if we get past the assume()
            if x in [0, 1, 2]:
                matrix_calls.append(x)
            assert isinstance(x, int)

        # Run the test
        test_property()

        # Should have executed matrix cases (0, 2 are even, 1 is odd so skipped)
        self.assertIn(0, matrix_calls)
        self.assertIn(2, matrix_calls)
        # 1 should be skipped due to assume()
        self.assertNotIn(1, matrix_calls)

    def test_matrix_failure_propagation(self):
        """Test that matrix case failures are properly propagated."""

        @for_all(Gen.int(1, 10))
        @matrix(x=[0, 1])
        def test_property(x):
            if x == 0:
                assert False, "Matrix case failure"
            assert isinstance(x, int)

        # Should raise AssertionError due to matrix case failure
        with self.assertRaises(AssertionError) as cm:
            test_property()

        self.assertIn("Matrix case failure", str(cm.exception))

    def test_matrix_with_complex_types(self):
        """Test matrix with complex data types."""
        call_count = 0
        matrix_calls = []

        @for_all(Gen.int(1, 5), Gen.dict(Gen.str(1, 3), Gen.int(1, 5), 1, 2))
        @matrix(x=[1, 2], y=[{"a": 1}, {"b": 2}])
        def test_property(x, y):
            nonlocal call_count
            call_count += 1
            # Only count as matrix call if both x and y match matrix spec exactly
            if x in [1, 2] and y in [{"a": 1}, {"b": 2}]:
                matrix_calls.append((x, y))
            assert isinstance(x, int)
            assert isinstance(y, dict)

        # Run the test with a fixed seed to avoid flakiness
        from python_proptest import settings

        test_property = settings(seed=42)(test_property)
        test_property()

        # Should have executed matrix cases
        self.assertEqual(len(matrix_calls), 4)  # 2 x values * 2 y values
        expected_calls = [(1, {"a": 1}), (1, {"b": 2}), (2, {"a": 1}), (2, {"b": 2})]
        # Sort both lists for comparison since dicts are unhashable
        matrix_calls_sorted = sorted(matrix_calls, key=lambda x: (x[0], str(x[1])))
        expected_calls_sorted = sorted(expected_calls, key=lambda x: (x[0], str(x[1])))
        self.assertEqual(matrix_calls_sorted, expected_calls_sorted)


if __name__ == "__main__":
    unittest.main()
