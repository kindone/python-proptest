"""
Comprehensive tests for the Option monad.

This module tests all functionality of the Option, Some, and None classes,
including edge cases and error handling.
"""

import unittest
from typing import Any

from python_proptest.core.option import None_, Option, Some, none


class TestSome(unittest.TestCase):
    """Test the Some class."""

    def test_is_some(self):
        """Test is_some returns True for Some."""
        result = Some(42)
        self.assertTrue(result.is_some())

    def test_is_none(self):
        """Test is_none returns False for Some."""
        result = Some(42)
        self.assertFalse(result.is_none())

    def test_get(self):
        """Test get returns the value."""
        result = Some(42)
        self.assertEqual(result.get(), 42)

    def test_get_or_else(self):
        """Test get_or_else returns the value, not the default."""
        result = Some(42)
        self.assertEqual(result.get_or_else(0), 42)

    def test_map(self):
        """Test map applies function to Some value."""
        result = Some(5)
        mapped = result.map(lambda x: x * 2)
        self.assertIsInstance(mapped, Some)
        self.assertEqual(mapped.get(), 10)

    def test_flat_map(self):
        """Test flat_map with function returning Some."""
        result = Some(5)
        mapped = result.flat_map(lambda x: Some(x * 2))
        self.assertIsInstance(mapped, Some)
        self.assertEqual(mapped.get(), 10)

    def test_flat_map_with_none(self):
        """Test flat_map with function returning None."""
        result = Some(5)
        mapped = result.flat_map(lambda x: None_())
        self.assertIsInstance(mapped, None_)

    def test_filter_success(self):
        """Test filter with predicate that passes."""
        result = Some(5)
        filtered = result.filter(lambda x: x > 0)
        self.assertIsInstance(filtered, Some)
        self.assertEqual(filtered.get(), 5)

    def test_filter_failure(self):
        """Test filter with predicate that fails."""
        result = Some(5)
        filtered = result.filter(lambda x: x < 0)
        self.assertIsInstance(filtered, None_)

    def test_eq_some(self):
        """Test equality for Some."""
        self.assertEqual(Some(42), Some(42))
        self.assertNotEqual(Some(42), Some(43))
        self.assertNotEqual(Some(42), None_())

    def test_repr(self):
        """Test string representation."""
        result = Some(42)
        self.assertEqual(repr(result), "Some(42)")


class TestNone(unittest.TestCase):
    """Test the None_ class."""

    def test_is_some(self):
        """Test is_some returns False for None."""
        result = None_()
        self.assertFalse(result.is_some())

    def test_is_none(self):
        """Test is_none returns True for None."""
        result = None_()
        self.assertTrue(result.is_none())

    def test_get_raises(self):
        """Test get raises ValueError for None."""
        result = None_()
        with self.assertRaises(ValueError) as cm:
            result.get()
        self.assertIn("Cannot get value from None", str(cm.exception))

    def test_get_or_else(self):
        """Test get_or_else returns the default."""
        result = None_()
        self.assertEqual(result.get_or_else(42), 42)

    def test_map_returns_none(self):
        """Test map returns None without applying function."""
        result = None_()
        mapped = result.map(lambda x: x * 2)
        self.assertIsInstance(mapped, None_)

    def test_flat_map_returns_none(self):
        """Test flat_map returns None without applying function."""
        result = None_()
        mapped = result.flat_map(lambda x: Some(x * 2))
        self.assertIsInstance(mapped, None_)

    def test_filter_returns_self(self):
        """Test filter returns self for None."""
        result = None_()
        filtered = result.filter(lambda x: True)
        self.assertIs(result, filtered)

    def test_eq_none(self):
        """Test equality for None."""
        self.assertEqual(None_(), None_())
        self.assertNotEqual(None_(), Some(42))

    def test_repr(self):
        """Test string representation."""
        result = None_()
        self.assertEqual(repr(result), "None")


class TestNoneFunction(unittest.TestCase):
    """Test the none() convenience function."""

    def test_none_returns_none(self):
        """Test none() returns None_ instance."""
        result = none()
        self.assertIsInstance(result, None_)

    def test_none_is_singleton_behavior(self):
        """Test that none() returns equivalent None_ instances."""
        result1 = none()
        result2 = none()
        # They should be equal (though not necessarily the same object)
        self.assertEqual(result1, result2)


class TestOptionChaining(unittest.TestCase):
    """Test chaining Option operations."""

    def test_some_chain(self):
        """Test chaining multiple operations on Some."""
        result = (
            Some(5)
            .map(lambda x: x * 2)
            .flat_map(lambda x: Some(x + 1))
            .filter(lambda x: x > 0)
        )
        self.assertIsInstance(result, Some)
        self.assertEqual(result.get(), 11)

    def test_none_chain(self):
        """Test chaining operations on None."""
        result = (
            None_()
            .map(lambda x: x * 2)
            .flat_map(lambda x: Some(x + 1))
            .filter(lambda x: x > 0)
        )
        self.assertIsInstance(result, None_)

    def test_filter_none_in_chain(self):
        """Test filter causing None in chain."""
        result = Some(5).filter(lambda x: x < 0).map(lambda x: x * 2)
        self.assertIsInstance(result, None_)

    def test_flat_map_none_in_chain(self):
        """Test flat_map returning None in chain."""
        result = Some(5).flat_map(lambda x: None_()).map(lambda x: x * 2)
        self.assertIsInstance(result, None_)


class TestOptionEdgeCases(unittest.TestCase):
    """Test edge cases for Option."""

    def test_some_with_none_value(self):
        """Test Some can contain None as a value."""
        result = Some(None)
        self.assertTrue(result.is_some())
        self.assertIsNone(result.get())

    def test_map_with_none_return(self):
        """Test map can return None as a value."""
        result = Some(5)
        mapped = result.map(lambda x: None)
        self.assertIsInstance(mapped, Some)
        self.assertIsNone(mapped.get())

    def test_filter_with_exception(self):
        """Test filter with predicate that raises exception."""
        result = Some(5)

        def failing_predicate(x: int) -> bool:
            raise ValueError("Predicate exception")

        # Option doesn't catch exceptions in filter
        with self.assertRaises(ValueError):
            result.filter(failing_predicate)
