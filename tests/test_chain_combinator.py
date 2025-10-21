"""
Comprehensive tests for the chain combinator.

Tests cover basic usage, shrinking behavior, edge cases, and integration
with other combinators.
"""

import random
import unittest

from python_proptest import Gen, for_all, run_for_all


class TestChainCombinator(unittest.TestCase):
    """Test suite for chain combinator functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.rng = random.Random(42)  # Fixed seed for reproducible tests

    def test_simple_chain_static_api(self):
        """Test basic chain functionality with static API."""

        # Chain month -> valid day
        def days_in_month(month):
            days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            return days[month - 1]

        date_gen = Gen.chain(
            Gen.int(1, 12),  # month
            lambda month: Gen.int(1, days_in_month(month)),  # valid day
        )

        # Test multiple generations
        for _ in range(20):
            shrinkable = date_gen.generate(self.rng)
            month, day = shrinkable.value

            self.assertIsInstance(shrinkable.value, tuple)
            self.assertEqual(len(shrinkable.value), 2)
            self.assertGreaterEqual(month, 1)
            self.assertLessEqual(month, 12)
            self.assertGreaterEqual(day, 1)
            self.assertLessEqual(day, days_in_month(month))

    def test_fluent_chain_api(self):
        """Test chain functionality with fluent API."""
        # Chain base value -> dependent value
        chained_gen = Gen.int(1, 10).chain(lambda x: Gen.int(x, x + 10))

        for _ in range(15):
            shrinkable = chained_gen.generate(self.rng)
            base, dependent = shrinkable.value

            self.assertIsInstance(shrinkable.value, tuple)
            self.assertGreaterEqual(base, 1)
            self.assertLessEqual(base, 10)
            self.assertGreaterEqual(dependent, base)
            self.assertLessEqual(dependent, base + 10)

    def test_multiple_chaining(self):
        """Test chaining multiple times to create longer tuples."""
        # Create a 3-tuple with dependencies
        triple_gen = Gen.chain(
            Gen.chain(
                Gen.int(1, 5), lambda w: Gen.int(w, w + 5)  # width  # height >= width
            ),
            lambda wh: Gen.int(1, wh[0] * wh[1]),  # area <= width * height
        )

        for _ in range(10):
            shrinkable = triple_gen.generate(self.rng)
            width, height, area = shrinkable.value

            self.assertIsInstance(shrinkable.value, tuple)
            self.assertEqual(len(shrinkable.value), 3)

            # Test dependencies
            self.assertGreaterEqual(width, 1)
            self.assertLessEqual(width, 5)
            self.assertGreaterEqual(height, width)
            self.assertLessEqual(height, width + 5)
            self.assertGreaterEqual(area, 1)
            self.assertLessEqual(area, width * height)

    def test_chain_with_other_generators(self):
        """Test chaining with different generator types."""
        # Chain string length -> string of that length
        string_gen = Gen.chain(
            Gen.int(3, 10),  # length
            lambda length: Gen.str(min_length=length, max_length=length),
        )

        for _ in range(10):
            shrinkable = string_gen.generate(self.rng)
            length, string = shrinkable.value

            self.assertIsInstance(shrinkable.value, tuple)
            self.assertEqual(len(string), length)
            self.assertGreaterEqual(length, 3)
            self.assertLessEqual(length, 10)

    def test_chain_with_complex_dependencies(self):
        """Test chain with complex dependency logic."""
        # Generate a list size, then a list of that exact size
        list_gen = Gen.chain(
            Gen.int(2, 5),  # size
            lambda size: Gen.list(Gen.int(0, 100), min_length=size, max_length=size),
        )

        for _ in range(10):
            shrinkable = list_gen.generate(self.rng)
            size, lst = shrinkable.value

            self.assertIsInstance(shrinkable.value, tuple)
            self.assertEqual(len(lst), size)
            self.assertGreaterEqual(size, 2)
            self.assertLessEqual(size, 5)

            # Verify all elements are in range
            for element in lst:
                self.assertGreaterEqual(element, 0)
                self.assertLessEqual(element, 100)

    def test_shrinking_maintains_dependencies(self):
        """Test that shrinking preserves dependency relationships."""

        def days_in_month(month):
            days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            return days[month - 1]

        date_gen = Gen.chain(
            Gen.int(1, 12), lambda month: Gen.int(1, days_in_month(month))
        )

        # Generate and check shrinks
        shrinkable = date_gen.generate(self.rng)
        original_month, original_day = shrinkable.value

        # Test shrinking candidates
        shrink_count = 0
        for shrunk in shrinkable.shrinks().to_list()[:10]:  # Check first 10 shrinks
            shrunk_month, shrunk_day = shrunk.value

            # Verify dependency is maintained in shrinks
            self.assertGreaterEqual(shrunk_month, 1)
            self.assertLessEqual(shrunk_month, 12)
            self.assertGreaterEqual(shrunk_day, 1)
            self.assertLessEqual(shrunk_day, days_in_month(shrunk_month))
            shrink_count += 1

        # Should have some shrinking candidates
        self.assertGreater(shrink_count, 0)

    def test_chain_preserves_single_value_generators(self):
        """Test that single value generators work correctly in chains."""
        # Chain with a constant generator
        constant_chain = Gen.chain(Gen.just(42), lambda x: Gen.int(x, x + 10))

        for _ in range(5):
            shrinkable = constant_chain.generate(self.rng)
            constant, dependent = shrinkable.value

            self.assertEqual(constant, 42)
            self.assertGreaterEqual(dependent, 42)
            self.assertLessEqual(dependent, 52)

    def test_nested_tuple_chaining(self):
        """Test chaining when base generator already produces tuples."""
        # Start with a tuple generator, then chain more
        base_tuple_gen = Gen.tuple(Gen.int(1, 5), Gen.int(1, 5))
        extended_gen = Gen.chain(
            base_tuple_gen,
            lambda pair: Gen.int(pair[0] + pair[1], pair[0] + pair[1] + 10),
        )

        for _ in range(10):
            shrinkable = extended_gen.generate(self.rng)
            first, second, third = shrinkable.value

            self.assertIsInstance(shrinkable.value, tuple)
            self.assertEqual(len(shrinkable.value), 3)

            # Check the dependency
            expected_min = first + second
            expected_max = first + second + 10
            self.assertGreaterEqual(third, expected_min)
            self.assertLessEqual(third, expected_max)

    def test_property_based_chain_validation(self):
        """Use run_for_all to validate chain properties."""

        def validate_chain_dependency(pair):
            x, y = pair
            # y should always be >= x (our dependency)
            return y >= x

        # Test with run_for_all
        result = run_for_all(
            validate_chain_dependency,
            Gen.chain(Gen.int(1, 50), lambda x: Gen.int(x, x + 20)),
            num_runs=50,
        )
        self.assertTrue(result)

    def test_chain_with_for_all_decorator(self):
        """Test chain combinator with @for_all decorator."""

        @for_all(Gen.chain(Gen.int(1, 10), lambda x: Gen.int(x * 2, x * 3)))
        def test_multiplication_dependency(self, pair):
            x, y = pair
            # y should be between 2x and 3x
            self.assertGreaterEqual(y, x * 2)
            self.assertLessEqual(y, x * 3)

        # Run the decorated test
        test_multiplication_dependency(self)

    def test_error_handling(self):
        """Test error handling in chain generation."""
        # Test with invalid dependency function
        with self.assertRaises(Exception):
            invalid_gen = Gen.chain(
                Gen.int(1, 10),
                lambda x: Gen.int(x + 100, x),  # Invalid range: min > max
            )
            invalid_gen.generate(self.rng)

    def test_chain_type_consistency(self):
        """Test that chained generators maintain type consistency."""
        # Chain different types
        mixed_chain = Gen.chain(
            Gen.bool(), lambda b: Gen.int(0, 1) if b else Gen.int(10, 20)
        )

        for _ in range(10):
            shrinkable = mixed_chain.generate(self.rng)
            boolean, integer = shrinkable.value

            self.assertIsInstance(boolean, bool)
            self.assertIsInstance(integer, int)

            if boolean:
                self.assertIn(integer, [0, 1])
            else:
                self.assertGreaterEqual(integer, 10)
                self.assertLessEqual(integer, 20)

    def test_long_chain_sequence(self):
        """Test chaining many generators in sequence."""

        # Create a 5-element tuple through repeated chaining
        def build_long_chain():
            gen = Gen.int(1, 3)  # Start with single value

            # Chain 4 more times
            gen = gen.chain(lambda x: Gen.int(x, x + 2))  # (a, b)
            gen = gen.chain(lambda xy: Gen.int(xy[1], xy[1] + 2))  # (a, b, c)
            gen = gen.chain(lambda xyz: Gen.int(xyz[2], xyz[2] + 2))  # (a, b, c, d)
            gen = gen.chain(
                lambda xyzw: Gen.int(xyzw[3], xyzw[3] + 2)
            )  # (a, b, c, d, e)

            return gen

        long_gen = build_long_chain()

        for _ in range(5):
            shrinkable = long_gen.generate(self.rng)
            a, b, c, d, e = shrinkable.value

            self.assertEqual(len(shrinkable.value), 5)

            # Check dependency chain
            self.assertGreaterEqual(b, a)
            self.assertLessEqual(b, a + 2)
            self.assertGreaterEqual(c, b)
            self.assertLessEqual(c, b + 2)
            self.assertGreaterEqual(d, c)
            self.assertLessEqual(d, c + 2)
            self.assertGreaterEqual(e, d)
            self.assertLessEqual(e, d + 2)


if __name__ == "__main__":
    unittest.main()
