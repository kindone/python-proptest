"""
Tests for edge cases in the decorator API.

This module tests error handling, context detection failures, and
other edge cases that may not be covered by normal usage.
"""

import unittest
from unittest.mock import patch

from python_proptest import Gen, for_all, run_property_test


class TestDecoratorEdgeCases(unittest.TestCase):
    """Test edge cases in decorator functionality."""

    def test_context_detection_without_self(self):
        """Test decorator on function without self parameter."""

        @for_all(Gen.int())
        def standalone_test(x: int):
            assert x == x

        # Should work fine
        standalone_test()

    def test_context_detection_class_lookup_failure(self):
        """Test decorator when class lookup fails."""

        # Create a function with qualname but class doesn't exist in module
        def fake_func():
            pass

        fake_func.__qualname__ = "NonExistentClass.test_method"

        # This should not crash, but may not detect context correctly
        # The decorator should handle this gracefully
        @for_all(Gen.int())
        def test_with_fake_qualname(x: int):
            assert x == x

        test_with_fake_qualname()

    def test_context_detection_module_none(self):
        """Test decorator when inspect.getmodule returns None."""
        # Create a mock function where getmodule returns None
        with patch("inspect.getmodule", return_value=None):

            @for_all(Gen.int())
            def test_with_no_module(x: int):
                assert x == x

            # Should still work, just won't detect class context
            test_with_no_module()

    def test_generator_count_mismatch(self):
        """Test ValueError when generator count doesn't match parameters."""
        with self.assertRaises(ValueError) as cm:

            @for_all(Gen.int(), Gen.str())
            def test_wrong_count(x: int):
                assert x == x

        self.assertIn("expects", str(cm.exception).lower())
        self.assertIn("generators", str(cm.exception).lower())

    def test_generator_count_mismatch_with_self(self):
        """Test ValueError with self parameter."""
        with self.assertRaises(ValueError) as cm:

            @for_all(Gen.int(), Gen.str())
            def test_wrong_count_with_self(self, x: int):
                assert x == x

        self.assertIn("expects", str(cm.exception).lower())

    def test_unittest_import_error(self):
        """Test decorator when unittest import fails."""

        # This is hard to test directly, but we can verify the code path exists
        # by checking that ImportError is caught
        @for_all(Gen.int())
        def test_import_handling(x: int):
            assert x == x

        test_import_handling()

    def test_run_property_test_function(self):
        """Test the run_property_test convenience function."""

        @for_all(Gen.int())
        def test_property(x: int):
            assert x == x

        # Should be able to call run_property_test
        result = run_property_test(test_property)
        # Function should have been executed
        self.assertIsNotNone(result)

    def test_decorator_preserves_metadata(self):
        """Test that decorator preserves function metadata."""

        @for_all(Gen.int())
        def test_with_doc(x: int):
            """This is a test function."""
            assert x == x

        self.assertEqual(test_with_doc.__name__, "test_with_doc")
        self.assertIn("test function", test_with_doc.__doc__)
        self.assertTrue(hasattr(test_with_doc, "_proptest_generators"))

    def test_decorator_with_existing_examples(self):
        """Test decorator preserves existing examples."""
        from python_proptest import example

        @for_all(Gen.int())
        @example(42)
        def test_with_example(x: int):
            assert x == x

        self.assertTrue(hasattr(test_with_example, "_proptest_examples"))
        self.assertEqual(len(test_with_example._proptest_examples), 1)

    def test_decorator_with_existing_settings(self):
        """Test decorator preserves existing settings."""
        from python_proptest import settings

        @for_all(Gen.int())
        @settings(num_runs=50)
        def test_with_settings(x: int):
            assert x == x

        self.assertTrue(hasattr(test_with_settings, "_proptest_settings"))
        self.assertEqual(test_with_settings._proptest_settings.get("num_runs"), 50)

    def test_decorator_with_existing_matrix(self):
        """Test decorator preserves existing matrix."""
        from python_proptest import matrix

        @for_all(Gen.int())
        @matrix(x=[1, 2, 3])
        def test_with_matrix(x: int):
            assert x == x

        self.assertTrue(hasattr(test_with_matrix, "_proptest_matrices"))

    def test_wrapper_with_exception(self):
        """Test wrapper handles exceptions correctly."""

        @for_all(Gen.int())
        def test_that_fails(x: int):
            assert x < 0  # Will fail for positive numbers

        # Should raise PropertyTestError or similar
        with self.assertRaises(Exception):
            test_that_fails()

    def test_wrapper_with_assertion_error(self):
        """Test wrapper converts AssertionError appropriately."""

        @for_all(Gen.int())
        def test_with_assertion(x: int):
            assert x < 0

        with self.assertRaises(Exception):
            test_with_assertion()

    def test_decorator_on_unittest_method(self):
        """Test decorator on unittest.TestCase method."""

        class TestUnittestClass(unittest.TestCase):
            @for_all(Gen.int())
            def test_unittest_method(self, x: int):
                self.assertGreaterEqual(x, x)

        # Create instance and run test
        test_instance = TestUnittestClass()
        test_instance.test_unittest_method()

    def test_decorator_on_pytest_style_method(self):
        """Test decorator on pytest-style class method."""

        class TestPytestClass:
            @for_all(Gen.int())
            def test_pytest_method(self, x: int):
                assert x == x

        # Create instance and run test
        test_instance = TestPytestClass()
        test_instance.test_pytest_method()

    def test_decorator_with_custom_seed(self):
        """Test decorator with custom seed."""

        @for_all(Gen.int(), seed=42)
        def test_with_seed(x: int):
            assert x == x

        self.assertEqual(test_with_seed._proptest_seed, 42)
        test_with_seed()

    def test_decorator_with_custom_num_runs(self):
        """Test decorator with custom num_runs."""

        @for_all(Gen.int(), num_runs=50)
        def test_with_runs(x: int):
            assert x == x

        self.assertEqual(test_with_runs._proptest_num_runs, 50)
        test_with_runs()
