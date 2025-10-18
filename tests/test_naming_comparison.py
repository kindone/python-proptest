"""
Comparison of the two property-based testing approaches in python-proptest.

This test demonstrates both the decorator-based @for_all and the
function-based run_for_all approaches.
"""

import unittest

from python_proptest import Gen, for_all, integers, run_for_all


class TestNamingComparison(unittest.TestCase):
    """Compare the two property-based testing approaches."""

    def test_decorator_based_approach(self):
        """Test decorator-based @for_all approach (Recommended)."""

        @for_all(integers(), integers())
        def test_addition_commutativity(x: int, y: int):
            """Test that addition is commutative: x + y = y + x"""
            assert x + y == y + x

        @for_all(integers(), integers(), integers())
        def test_addition_associativity(x: int, y: int, z: int):
            """Test that addition is associative: (x + y) + z = x + (y + z)"""
            assert (x + y) + z == x + (y + z)

        @for_all(integers())
        def test_multiplication_by_zero(x: int):
            """Test that multiplying by zero gives zero: x * 0 = 0"""
            assert x * 0 == 0

        # Run the decorator-based tests
        test_addition_commutativity()
        test_addition_associativity()
        test_multiplication_by_zero()

    def test_function_based_approach(self):
        """Test function-based run_for_all approach (Legacy/Alternative)."""

        # Test addition commutativity
        result1 = run_for_all(lambda x, y: x + y == y + x, Gen.int(), Gen.int())
        assert result1 is True

        # Test addition associativity
        result2 = run_for_all(
            lambda x, y, z: (x + y) + z == x + (y + z), Gen.int(), Gen.int(), Gen.int()
        )
        assert result2 is True

        # Test multiplication by zero
        result3 = run_for_all(lambda x: x * 0 == 0, Gen.int())
        assert result3 is True

    def test_both_approaches_equivalent(self):
        """Test that both approaches produce equivalent results."""

        # Decorator approach
        @for_all(
            integers(min_value=1, max_value=10), integers(min_value=1, max_value=10)
        )
        def decorator_test(x: int, y: int):
            assert x + y > 0
            assert x * y > 0

        # Function approach
        def function_test():
            result = run_for_all(
                lambda x, y: x + y > 0 and x * y > 0,
                Gen.int(min_value=1, max_value=10),
                Gen.int(min_value=1, max_value=10),
            )
            assert result is True

        # Both should pass
        decorator_test()
        function_test()

    def test_approach_guidelines(self):
        """Test examples that demonstrate when to use each approach."""

        # Use @for_all for complex assertions with multiple conditions
        @for_all(integers(), integers())
        def complex_assertion_test(x: int, y: int):
            """Complex test with multiple assertions - perfect for @for_all"""
            # Test multiple properties of addition and multiplication
            assert x + y == y + x  # Commutativity
            assert x * y == y * x  # Commutativity
            assert (x + y) + 0 == x + y  # Identity element
            assert (x * y) * 1 == x * y  # Identity element

        # Use run_for_all for simple lambda-based properties
        def simple_property_test():
            """Simple lambda-based properties - perfect for run_for_all"""
            result = run_for_all(
                lambda x: isinstance(x, int), Gen.int(min_value=0, max_value=100)
            )
            assert result is True

            result = run_for_all(
                lambda x: 0 <= x <= 100, Gen.int(min_value=0, max_value=100)
            )
            assert result is True

        # Run both tests
        complex_assertion_test()
        simple_property_test()


if __name__ == "__main__":
    pytest.main([__file__])
