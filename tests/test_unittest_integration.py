"""
Tests for unittest integration with python-proptest.

This module verifies that the @for_all decorator works correctly with
unittest.TestCase classes.
"""

import unittest

from python_proptest import Gen, for_all, integers, text


class TestUnittestIntegration(unittest.TestCase):
    """Test unittest integration with python-proptest."""

    @for_all(integers(), integers())
    def test_addition_commutativity(self, x: int, y: int):
        """Test that addition is commutative using unittest assertions."""
        result1 = x + y
        result2 = y + x
        self.assertEqual(
            result1,
            result2,
            f"Addition not commutative: {x} + {y} = {result1}, {y} + {x} = {result2}",
        )

    @for_all(integers(), integers(), integers())
    def test_multiplication_associativity(self, x: int, y: int, z: int):
        """Test that multiplication is associative using unittest assertions."""
        result1 = (x * y) * z
        result2 = x * (y * z)
        self.assertEqual(
            result1,
            result2,
            f"Multiplication not associative: ({x} * {y}) * {z} = {result1}, {x} * ({y} * {z}) = {result2}",
        )

    @for_all(text(), text())
    def test_string_concatenation(self, s1: str, s2: str):
        """Test string concatenation properties using unittest assertions."""
        result = s1 + s2
        self.assertEqual(
            len(result),
            len(s1) + len(s2),
            f"String length mismatch: len('{s1}' + '{s2}') = {len(result)}, expected {len(s1) + len(s2)}",
        )
        self.assertTrue(
            result.startswith(s1), f"Result '{result}' does not start with '{s1}'"
        )
        self.assertTrue(
            result.endswith(s2), f"Result '{result}' does not end with '{s2}'"
        )

    @for_all(integers(min_value=1, max_value=100), integers(min_value=1, max_value=100))
    def test_division_properties(self, x: int, y: int):
        """Test division properties using unittest assertions."""
        # Test that x / y * y equals x (for integer division)
        quotient = x // y
        remainder = x % y
        self.assertEqual(
            quotient * y + remainder,
            x,
            f"Division property failed: {x} // {y} * {y} + {x} % {y} = {quotient * y + remainder}, expected {x}",
        )

    @for_all(integers(), integers())
    def test_mixed_assertions(self, x: int, y: int):
        """Test mixing unittest assertions with regular assertions."""
        # Use unittest assertions
        self.assertIsInstance(x, int)
        self.assertIsInstance(y, int)

        # Use regular assertions
        assert x + y == y + x
        assert x * 0 == 0
        assert x * 1 == x


class TestUnittestWithGen(unittest.TestCase):
    """Test unittest integration using Gen class directly."""

    @for_all(Gen.int(), Gen.str())
    def test_int_string_properties(self, x: int, s: str):
        """Test properties with int and string generators."""
        self.assertIsInstance(x, int)
        self.assertIsInstance(s, str)
        self.assertGreaterEqual(len(s), 0)

    @for_all(Gen.int(min_value=0, max_value=100), Gen.int(min_value=0, max_value=100))
    def test_positive_int_properties(self, x: int, y: int):
        """Test properties with positive integers."""
        self.assertGreaterEqual(x, 0)
        self.assertGreaterEqual(y, 0)
        self.assertGreaterEqual(x + y, x)
        self.assertGreaterEqual(x + y, y)


if __name__ == "__main__":
    unittest.main()
