"""
Comprehensive tests for the Try monad.

This module tests all functionality of the Try, Success, and Failure classes,
including edge cases and error handling.
"""

import unittest
from typing import Any

from python_proptest.core.try_ import Failure, Success, Try, attempt


class TestSuccess(unittest.TestCase):
    """Test the Success class."""

    def test_is_success(self):
        """Test is_success returns True for Success."""
        result = Success(42)
        self.assertTrue(result.is_success())

    def test_is_failure(self):
        """Test is_failure returns False for Success."""
        result = Success(42)
        self.assertFalse(result.is_failure())

    def test_get(self):
        """Test get returns the value."""
        result = Success(42)
        self.assertEqual(result.get(), 42)

    def test_get_or_else(self):
        """Test get_or_else returns the value, not the default."""
        result = Success(42)
        self.assertEqual(result.get_or_else(0), 42)

    def test_get_exception_raises(self):
        """Test get_exception raises ValueError for Success."""
        result = Success(42)
        with self.assertRaises(ValueError) as cm:
            result.get_exception()
        self.assertIn("Cannot get exception from Success", str(cm.exception))

    def test_map_success(self):
        """Test map applies function successfully."""
        result = Success(5)
        mapped = result.map(lambda x: x * 2)
        self.assertIsInstance(mapped, Success)
        self.assertEqual(mapped.get(), 10)

    def test_map_with_exception(self):
        """Test map catches exceptions and returns Failure."""
        result = Success(5)

        def failing_func(x: int) -> int:
            raise ValueError("Test exception")

        mapped = result.map(failing_func)
        self.assertIsInstance(mapped, Failure)
        self.assertIsInstance(mapped.get_exception(), ValueError)
        self.assertIn("Test exception", str(mapped.get_exception()))

    def test_flat_map_success(self):
        """Test flat_map with function returning Success."""
        result = Success(5)
        mapped = result.flat_map(lambda x: Success(x * 2))
        self.assertIsInstance(mapped, Success)
        self.assertEqual(mapped.get(), 10)

    def test_flat_map_failure(self):
        """Test flat_map with function returning Failure."""
        result = Success(5)
        mapped = result.flat_map(lambda x: Failure(ValueError("Test")))
        self.assertIsInstance(mapped, Failure)
        self.assertIsInstance(mapped.get_exception(), ValueError)

    def test_flat_map_with_exception(self):
        """Test flat_map catches exceptions and returns Failure."""
        result = Success(5)

        def failing_func(x: int) -> Try[int]:
            raise ValueError("Test exception")

        mapped = result.flat_map(failing_func)
        self.assertIsInstance(mapped, Failure)
        self.assertIsInstance(mapped.get_exception(), ValueError)

    def test_recover_returns_self(self):
        """Test recover returns self for Success."""
        result = Success(42)
        recovered = result.recover(lambda e: 0)
        self.assertIs(result, recovered)

    def test_filter_success(self):
        """Test filter with predicate that passes."""
        result = Success(5)
        filtered = result.filter(lambda x: x > 0)
        self.assertIsInstance(filtered, Success)
        self.assertEqual(filtered.get(), 5)

    def test_filter_failure(self):
        """Test filter with predicate that fails."""
        result = Success(5)
        filtered = result.filter(lambda x: x < 0)
        self.assertIsInstance(filtered, Failure)
        self.assertIsInstance(filtered.get_exception(), ValueError)
        self.assertIn("Predicate failed", str(filtered.get_exception()))

    def test_filter_with_exception(self):
        """Test filter catches exceptions in predicate."""
        result = Success(5)

        def failing_predicate(x: int) -> bool:
            raise ValueError("Predicate exception")

        filtered = result.filter(failing_predicate)
        self.assertIsInstance(filtered, Failure)
        self.assertIsInstance(filtered.get_exception(), ValueError)
        self.assertIn("Predicate exception", str(filtered.get_exception()))

    def test_eq_success(self):
        """Test equality for Success."""
        self.assertEqual(Success(42), Success(42))
        self.assertNotEqual(Success(42), Success(43))
        self.assertNotEqual(Success(42), Failure(ValueError()))

    def test_repr(self):
        """Test string representation."""
        result = Success(42)
        self.assertEqual(repr(result), "Success(42)")


class TestFailure(unittest.TestCase):
    """Test the Failure class."""

    def test_is_success(self):
        """Test is_success returns False for Failure."""
        result = Failure(ValueError("Test"))
        self.assertFalse(result.is_success())

    def test_is_failure(self):
        """Test is_failure returns True for Failure."""
        result = Failure(ValueError("Test"))
        self.assertTrue(result.is_failure())

    def test_get_raises(self):
        """Test get raises the exception."""
        exception = ValueError("Test exception")
        result = Failure(exception)
        with self.assertRaises(ValueError) as cm:
            result.get()
        self.assertIs(cm.exception, exception)

    def test_get_or_else(self):
        """Test get_or_else returns the default."""
        result = Failure(ValueError("Test"))
        self.assertEqual(result.get_or_else(42), 42)

    def test_get_exception(self):
        """Test get_exception returns the exception."""
        exception = ValueError("Test exception")
        result = Failure(exception)
        self.assertIs(result.get_exception(), exception)

    def test_map_returns_failure(self):
        """Test map returns Failure without applying function."""
        result = Failure(ValueError("Test"))
        mapped = result.map(lambda x: x * 2)
        self.assertIsInstance(mapped, Failure)
        self.assertIsInstance(mapped.get_exception(), ValueError)

    def test_flat_map_returns_failure(self):
        """Test flat_map returns Failure without applying function."""
        result = Failure(ValueError("Test"))
        mapped = result.flat_map(lambda x: Success(x * 2))
        self.assertIsInstance(mapped, Failure)
        self.assertIsInstance(mapped.get_exception(), ValueError)

    def test_recover_success(self):
        """Test recover with function that succeeds."""
        result = Failure(ValueError("Test"))
        recovered = result.recover(lambda e: 42)
        self.assertIsInstance(recovered, Success)
        self.assertEqual(recovered.get(), 42)

    def test_recover_with_exception(self):
        """Test recover catches exceptions in recovery function."""
        result = Failure(ValueError("Original"))

        def failing_recover(e: Exception) -> int:
            raise RuntimeError("Recovery failed")

        recovered = result.recover(failing_recover)
        self.assertIsInstance(recovered, Failure)
        self.assertIsInstance(recovered.get_exception(), RuntimeError)
        self.assertIn("Recovery failed", str(recovered.get_exception()))

    def test_filter_returns_self(self):
        """Test filter returns self for Failure."""
        result = Failure(ValueError("Test"))
        filtered = result.filter(lambda x: True)
        self.assertIs(result, filtered)

    def test_eq_failure(self):
        """Test equality for Failure."""
        exc1 = ValueError("Test")
        exc2 = ValueError("Test")
        exc3 = ValueError("Different")
        self.assertEqual(Failure(exc1), Failure(exc2))
        self.assertNotEqual(Failure(exc1), Failure(exc3))
        self.assertNotEqual(Failure(exc1), Success(42))

    def test_repr(self):
        """Test string representation."""
        result = Failure(ValueError("Test"))
        self.assertIn("Failure", repr(result))
        self.assertIn("Test", repr(result))


class TestAttempt(unittest.TestCase):
    """Test the attempt function."""

    def test_attempt_success(self):
        """Test attempt with successful function."""
        def successful_func() -> int:
            return 42

        result = attempt(successful_func)
        self.assertIsInstance(result, Success)
        self.assertEqual(result.get(), 42)

    def test_attempt_failure(self):
        """Test attempt with failing function."""
        def failing_func() -> int:
            raise ValueError("Test exception")

        result = attempt(failing_func)
        self.assertIsInstance(result, Failure)
        self.assertIsInstance(result.get_exception(), ValueError)
        self.assertIn("Test exception", str(result.get_exception()))

    def test_attempt_with_different_exceptions(self):
        """Test attempt catches different exception types."""
        def raise_key_error() -> Any:
            raise KeyError("Missing key")

        result = attempt(raise_key_error)
        self.assertIsInstance(result, Failure)
        self.assertIsInstance(result.get_exception(), KeyError)

    def test_attempt_with_no_return(self):
        """Test attempt with function that returns None."""
        def no_return_func() -> None:
            pass

        result = attempt(no_return_func)
        self.assertIsInstance(result, Success)
        self.assertIsNone(result.get())


class TestTryChaining(unittest.TestCase):
    """Test chaining Try operations."""

    def test_success_chain(self):
        """Test chaining multiple operations on Success."""
        result = (
            Success(5)
            .map(lambda x: x * 2)
            .flat_map(lambda x: Success(x + 1))
            .filter(lambda x: x > 0)
        )
        self.assertIsInstance(result, Success)
        self.assertEqual(result.get(), 11)

    def test_failure_chain(self):
        """Test chaining operations on Failure."""
        result = (
            Failure(ValueError("Original"))
            .map(lambda x: x * 2)
            .flat_map(lambda x: Success(x + 1))
            .filter(lambda x: x > 0)
        )
        self.assertIsInstance(result, Failure)
        self.assertIsInstance(result.get_exception(), ValueError)

    def test_recover_in_chain(self):
        """Test recover in a chain."""
        result = (
            Failure(ValueError("Error"))
            .recover(lambda e: 42)
            .map(lambda x: x * 2)
        )
        self.assertIsInstance(result, Success)
        self.assertEqual(result.get(), 84)

    def test_filter_failure_in_chain(self):
        """Test filter causing failure in chain."""
        result = (
            Success(5)
            .filter(lambda x: x < 0)
            .map(lambda x: x * 2)
        )
        self.assertIsInstance(result, Failure)
        self.assertIsInstance(result.get_exception(), ValueError)


