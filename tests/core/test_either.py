"""
Comprehensive tests for the Either monad.

This module tests all functionality of the Either, Left, and Right classes,
including edge cases and error handling.
"""

import unittest
from typing import Any

from python_proptest.core.either import Either, Left, Right


class TestLeft(unittest.TestCase):
    """Test the Left class."""

    def test_is_left(self):
        """Test is_left returns True for Left."""
        result = Left("error")
        self.assertTrue(result.is_left())

    def test_is_right(self):
        """Test is_right returns False for Left."""
        result = Left("error")
        self.assertFalse(result.is_right())

    def test_get_left(self):
        """Test get_left returns the value."""
        result = Left("error")
        self.assertEqual(result.get_left(), "error")

    def test_get_right_raises(self):
        """Test get_right raises ValueError for Left."""
        result = Left("error")
        with self.assertRaises(ValueError) as cm:
            result.get_right()
        self.assertIn("Cannot get right value from Left", str(cm.exception))

    def test_get_or_else(self):
        """Test get_or_else returns the default."""
        result = Left("error")
        self.assertEqual(result.get_or_else(42), 42)

    def test_map_returns_left(self):
        """Test map returns Left without applying function."""
        result = Left("error")
        mapped = result.map(lambda x: x * 2)
        self.assertIsInstance(mapped, Left)
        self.assertEqual(mapped.get_left(), "error")

    def test_map_left(self):
        """Test map_left applies function to Left value."""
        result = Left(5)
        mapped = result.map_left(lambda x: x * 2)
        self.assertIsInstance(mapped, Left)
        self.assertEqual(mapped.get_left(), 10)

    def test_flat_map_returns_left(self):
        """Test flat_map returns Left without applying function."""
        result = Left("error")
        mapped = result.flat_map(lambda x: Right(x * 2))
        self.assertIsInstance(mapped, Left)
        self.assertEqual(mapped.get_left(), "error")

    def test_eq_left(self):
        """Test equality for Left."""
        self.assertEqual(Left("error"), Left("error"))
        self.assertNotEqual(Left("error"), Left("different"))
        self.assertNotEqual(Left("error"), Right("error"))

    def test_repr(self):
        """Test string representation."""
        result = Left("error")
        self.assertEqual(repr(result), "Left('error')")


class TestRight(unittest.TestCase):
    """Test the Right class."""

    def test_is_left(self):
        """Test is_left returns False for Right."""
        result = Right(42)
        self.assertFalse(result.is_left())

    def test_is_right(self):
        """Test is_right returns True for Right."""
        result = Right(42)
        self.assertTrue(result.is_right())

    def test_get_left_raises(self):
        """Test get_left raises ValueError for Right."""
        result = Right(42)
        with self.assertRaises(ValueError) as cm:
            result.get_left()
        self.assertIn("Cannot get left value from Right", str(cm.exception))

    def test_get_right(self):
        """Test get_right returns the value."""
        result = Right(42)
        self.assertEqual(result.get_right(), 42)

    def test_get_or_else(self):
        """Test get_or_else returns the value, not the default."""
        result = Right(42)
        self.assertEqual(result.get_or_else(0), 42)

    def test_map(self):
        """Test map applies function to Right value."""
        result = Right(5)
        mapped = result.map(lambda x: x * 2)
        self.assertIsInstance(mapped, Right)
        self.assertEqual(mapped.get_right(), 10)

    def test_map_left_returns_right(self):
        """Test map_left returns Right without applying function."""
        result = Right(42)
        mapped = result.map_left(lambda x: x * 2)
        self.assertIsInstance(mapped, Right)
        self.assertEqual(mapped.get_right(), 42)

    def test_flat_map(self):
        """Test flat_map with function returning Right."""
        result = Right(5)
        mapped = result.flat_map(lambda x: Right(x * 2))
        self.assertIsInstance(mapped, Right)
        self.assertEqual(mapped.get_right(), 10)

    def test_flat_map_with_left(self):
        """Test flat_map with function returning Left."""
        result = Right(5)
        mapped = result.flat_map(lambda x: Left("error"))
        self.assertIsInstance(mapped, Left)
        self.assertEqual(mapped.get_left(), "error")

    def test_eq_right(self):
        """Test equality for Right."""
        self.assertEqual(Right(42), Right(42))
        self.assertNotEqual(Right(42), Right(43))
        self.assertNotEqual(Right(42), Left(42))

    def test_repr(self):
        """Test string representation."""
        result = Right(42)
        self.assertEqual(repr(result), "Right(42)")


class TestEitherChaining(unittest.TestCase):
    """Test chaining Either operations."""

    def test_right_chain(self):
        """Test chaining multiple operations on Right."""
        result = Right(5).map(lambda x: x * 2).flat_map(lambda x: Right(x + 1))
        self.assertIsInstance(result, Right)
        self.assertEqual(result.get_right(), 11)

    def test_left_chain(self):
        """Test chaining operations on Left."""
        result = Left("error").map(lambda x: x * 2).flat_map(lambda x: Right(x + 1))
        self.assertIsInstance(result, Left)
        self.assertEqual(result.get_left(), "error")

    def test_map_left_in_chain(self):
        """Test map_left in a chain."""
        result = Left(5).map_left(lambda x: x * 2).map(lambda x: x + 1)
        self.assertIsInstance(result, Left)
        self.assertEqual(result.get_left(), 10)

    def test_flat_map_left_in_chain(self):
        """Test flat_map with Left in chain."""
        result = Right(5).flat_map(lambda x: Left("error")).map(lambda x: x * 2)
        self.assertIsInstance(result, Left)
        self.assertEqual(result.get_left(), "error")


class TestEitherErrorHandling(unittest.TestCase):
    """Test error handling in Either operations."""

    def test_map_with_exception(self):
        """Test map raises exception (not caught by Either)."""
        result = Right(5)

        def failing_func(x: int) -> int:
            raise ValueError("Test exception")

        with self.assertRaises(ValueError):
            result.map(failing_func)

    def test_map_left_with_exception(self):
        """Test map_left raises exception (not caught by Either)."""
        result = Left(5)

        def failing_func(x: int) -> int:
            raise ValueError("Test exception")

        with self.assertRaises(ValueError):
            result.map_left(failing_func)

    def test_flat_map_with_exception(self):
        """Test flat_map raises exception (not caught by Either)."""
        result = Right(5)

        def failing_func(x: int) -> Either[str, int]:
            raise ValueError("Test exception")

        with self.assertRaises(ValueError):
            result.flat_map(failing_func)
