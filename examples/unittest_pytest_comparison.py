"""
Comparison of unittest and pytest integration with python-proptest.

This example shows how the same property-based tests can be written
using both unittest and pytest frameworks.
"""

import unittest
import pytest
from python_proptest import for_all, Gen


# =============================================================================
# UNITTEST INTEGRATION
# =============================================================================

class TestMathPropertiesUnittest(unittest.TestCase):
    """Mathematical properties using unittest framework."""

    @for_all(Gen.int(), Gen.int())
    def test_addition_commutativity(self, x: int, y: int):
        """Test that addition is commutative."""
        result1 = x + y
        result2 = y + x
        self.assertEqual(result1, result2)

    @for_all(Gen.int(), Gen.int(), Gen.int())
    def test_multiplication_associativity(self, x: int, y: int, z: int):
        """Test that multiplication is associative."""
        result1 = (x * y) * z
        result2 = x * (y * z)
        self.assertEqual(result1, result2)

    @for_all(Gen.int(), Gen.int(), Gen.int())
    def test_distributive_property(self, x: int, y: int, z: int):
        """Test distributive property: x * (y + z) = x * y + x * z."""
        left = x * (y + z)
        right = x * y + x * z
        self.assertEqual(left, right)

    @for_all(Gen.str(), Gen.str())
    def test_string_concatenation(self, s1: str, s2: str):
        """Test string concatenation properties."""
        result = s1 + s2
        self.assertEqual(len(result), len(s1) + len(s2))
        self.assertTrue(result.startswith(s1))
        self.assertTrue(result.endswith(s2))

    @for_all(Gen.int(min_value=1, max_value=100))
    def test_positive_multiplication(self, x: int):
        """Test properties of positive number multiplication."""
        self.assertGreater(x * 2, x)
        self.assertEqual(x * 1, x)
        self.assertEqual(x * 0, 0)


# =============================================================================
# PYTEST INTEGRATION
# =============================================================================

class TestMathPropertiesPytest:
    """Mathematical properties using pytest framework."""

    @for_all(Gen.int(), Gen.int())
    def test_addition_commutativity(self, x: int, y: int):
        """Test that addition is commutative."""
        assert x + y == y + x

    @for_all(Gen.int(), Gen.int(), Gen.int())
    def test_multiplication_associativity(self, x: int, y: int, z: int):
        """Test that multiplication is associative."""
        assert (x * y) * z == x * (y * z)

    @for_all(Gen.int(), Gen.int(), Gen.int())
    def test_distributive_property(self, x: int, y: int, z: int):
        """Test distributive property: x * (y + z) = x * y + x * z."""
        assert x * (y + z) == x * y + x * z

    @for_all(Gen.str(), Gen.str())
    def test_string_concatenation(self, s1: str, s2: str):
        """Test string concatenation properties."""
        result = s1 + s2
        assert len(result) == len(s1) + len(s2)
        assert result.startswith(s1)
        assert result.endswith(s2)

    @for_all(Gen.int(min_value=1, max_value=100))
    def test_positive_multiplication(self, x: int):
        """Test properties of positive number multiplication."""
        assert x * 2 > x
        assert x * 1 == x
        assert x * 0 == 0


# =============================================================================
# MIXED ASSERTION STYLE (WORKS IN BOTH FRAMEWORKS)
# =============================================================================

class TestMixedAssertions(unittest.TestCase):
    """Test mixing unittest assertions with regular assertions."""

    @for_all(Gen.int(), Gen.int())
    def test_mixed_assertions(self, x: int, y: int):
        """Test mixing different assertion styles."""
        # Unittest assertions
        self.assertIsInstance(x, int)
        self.assertIsInstance(y, int)

        # Regular assertions (work in both frameworks)
        assert x + y == y + x
        assert x * 0 == 0
        assert x * 1 == x

        # More unittest assertions - basic properties that are always true
        self.assertEqual(x + y, y + x)  # Commutativity
        self.assertEqual(x * 0, 0)      # Zero property
        self.assertEqual(x * 1, x)      # Identity property


# =============================================================================
# ADVANCED EXAMPLES
# =============================================================================

class TestAdvancedUnittest(unittest.TestCase):
    """Advanced unittest examples with complex properties."""

    @for_all(Gen.int(), Gen.int())
    def test_absolute_value_properties(self, x: int, y: int):
        """Test properties of absolute value."""
        abs_x = abs(x)
        abs_y = abs(y)

        self.assertGreaterEqual(abs_x, 0)
        self.assertGreaterEqual(abs_y, 0)
        self.assertEqual(abs_x, abs(-x))
        self.assertEqual(abs_y, abs(-y))

    @for_all(Gen.str(), Gen.int(min_value=0, max_value=10))
    def test_string_repetition(self, s: str, n: int):
        """Test string repetition properties."""
        repeated = s * n
        self.assertEqual(len(repeated), len(s) * n)

        if n > 0:
            self.assertTrue(repeated.startswith(s))
            self.assertTrue(repeated.endswith(s))

    @for_all(Gen.int(min_value=0, max_value=100), Gen.int(min_value=1, max_value=100))
    def test_modulo_properties(self, x: int, y: int):
        """Test modulo operation properties."""
        remainder = x % y
        quotient = x // y

        self.assertGreaterEqual(remainder, 0)
        self.assertLess(remainder, y)
        self.assertEqual(quotient * y + remainder, x)


# =============================================================================
# RUNNING THE TESTS
# =============================================================================

def run_unittest_examples():
    """Run the unittest examples."""
    print("Running unittest examples...")
    unittest.main(module=__name__, exit=False, verbosity=2)


def run_pytest_examples():
    """Run the pytest examples."""
    print("Running pytest examples...")
    import subprocess
    import sys
    subprocess.run([sys.executable, "-m", "pytest", __file__, "-v"])


if __name__ == "__main__":
    print("python-proptest unittest and pytest integration examples")
    print("=" * 60)

    # Run unittest examples
    run_unittest_examples()

    print("\n" + "=" * 60)
    print("To run with pytest, use:")
    print("python -m pytest examples/unittest_pytest_comparison.py -v")
    print("=" * 60)
