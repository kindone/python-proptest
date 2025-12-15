"""
Example demonstrating standalone @matrix and @example decorators.

These decorators can now be used without @for_all for simple test cases
where you just want to test specific values or combinations.
"""
import unittest
from python_proptest import matrix, example


class TestStandaloneDecorators(unittest.TestCase):
    """Examples of using @matrix and @example without @for_all."""

    @example(0, 0)
    @example(1, 1)
    @example(100, 100)
    def test_equality_reflexive(self, x: int, y: int):
        """Test that equal values remain equal."""
        if x == y:
            self.assertEqual(x, y)

    @matrix(x=[0, 1, -1], y=[0, 1, -1])
    def test_addition_commutative(self, x: int, y: int):
        """Test that x + y == y + x for specific values."""
        self.assertEqual(x + y, y + x)

    @example("", 0)
    @example("hello", 5)
    @example("world", 5)
    @matrix(s=["test"], expected=[4])
    @matrix(s=["python"], expected=[6])
    def test_string_length(self, s: str, expected: int):
        """Test string length calculation with both examples and matrix."""
        self.assertEqual(len(s), expected)


def standalone_function_example():
    """Example of standalone decorators on non-method functions."""
    results = []

    @matrix(x=[1, 2, 3], y=[10, 20])
    def collect_combinations(x, y):
        results.append((x, y))

    # Call with no arguments - runs all matrix combinations
    collect_combinations()

    print(f"Matrix generated {len(results)} combinations:")
    for x, y in results:
        print(f"  x={x}, y={y}")


if __name__ == "__main__":
    print("Running standalone function example...")
    standalone_function_example()
    print("\nRunning unittest examples...")
    unittest.main()
