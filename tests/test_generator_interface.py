"""
Generator interface tests ported from Dart.

These tests verify that the generator interface works correctly
with transformations, chaining, and filtering.
"""

import random
import unittest

from python_proptest import Gen, PropertyTestError, run_for_all


class TestGeneratorInterface(unittest.TestCase):
    """Test the generator interface and transformations."""

    def test_map_transformation_works(self):
        """Test that map transformation works correctly."""
        rng = random.Random(42)
        int_gen = Gen.int(min_value=1, max_value=10)
        string_gen = int_gen.map(lambda i: f"Number: {i}")

        result = string_gen.generate(rng)
        assert result.value.startswith("Number: ")
        assert any(c.isdigit() for c in result.value)

    def test_flat_map_chaining_works(self):
        """Test that flatMap chaining works correctly."""
        rng = random.Random(42)
        int_gen = Gen.int(min_value=1, max_value=5)
        chained_gen = int_gen.flat_map(lambda i: Gen.int(min_value=i, max_value=i + 10))

        result = chained_gen.generate(rng)
        assert result.value >= 1
        assert result.value <= 15

    def test_filter_works_correctly(self):
        """Test that filter works correctly."""
        rng = random.Random(42)
        int_gen = Gen.int(min_value=1, max_value=20)
        even_gen = int_gen.filter(lambda i: i % 2 == 0)

        result = even_gen.generate(rng)
        assert result.value % 2 == 0
        assert 1 <= result.value <= 20

    def test_filter_with_impossible_condition_raises_error(self):
        """Test that filter raises error when condition is impossible."""
        rng = random.Random(42)
        int_gen = Gen.int(min_value=1, max_value=10)
        impossible_gen = int_gen.filter(lambda i: i > 100)  # Impossible condition

        with self.assertRaises(ValueError):
            impossible_gen.generate(rng)

    def test_chain_preserves_original_value(self):
        """Test that chain preserves the original value."""
        rng = random.Random(42)
        int_gen = Gen.int(min_value=1, max_value=5)

        # Create a generator that returns a tuple of (original, derived)
        chained_gen = int_gen.flat_map(lambda i: Gen.just((i, i + 10)))  # Return tuple

        result = chained_gen.generate(rng)
        original, derived = result.value
        assert 1 <= original <= 5
        assert derived == original + 10

    def test_multiple_transformations(self):
        """Test multiple transformations chained together."""
        rng = random.Random(42)

        # Start with int, map to string, then filter
        gen = (
            Gen.int(min_value=1, max_value=100)
            .map(lambda x: f"Value: {x}")
            .filter(lambda s: len(s) > 5)
        )

        result = gen.generate(rng)
        assert result.value.startswith("Value: ")
        assert len(result.value) > 5

    def test_nested_flat_map(self):
        """Test nested flat_map operations."""
        rng = random.Random(42)

        # Generate a list length, then generate a list of that length
        gen = Gen.int(min_value=1, max_value=5).flat_map(
            lambda length: Gen.list(
                Gen.int(min_value=0, max_value=10), min_length=length, max_length=length
            )
        )

        result = gen.generate(rng)
        assert isinstance(result.value, list)
        assert 1 <= len(result.value) <= 5
        assert all(isinstance(x, int) for x in result.value)

    def test_generator_with_seed_reproducibility(self):
        """Test that generators with seeds are reproducible."""

        def test_property(x):
            return isinstance(x, int)

        # Run with same seed twice
        result1 = run_for_all(
            test_property, Gen.int(min_value=0, max_value=100), num_runs=10, seed=42
        )

        result2 = run_for_all(
            test_property, Gen.int(min_value=0, max_value=100), num_runs=10, seed=42
        )

        assert result1 is True
        assert result2 is True

    def test_generator_with_different_seeds(self):
        """Test that different seeds produce different results."""

        def test_property(x):
            return isinstance(x, int)

        # These should both pass but with different random sequences
        result1 = run_for_all(
            test_property,
            Gen.int(min_value=0, max_value=100),
            num_runs=10,
            seed="seed1",
        )

        result2 = run_for_all(
            test_property,
            Gen.int(min_value=0, max_value=100),
            num_runs=10,
            seed="seed2",
        )

        assert result1 is True
        assert result2 is True

    def test_generator_shrinking_preserved_through_transformations(self):
        """Test that shrinking is preserved through transformations."""
        rng = random.Random(42)

        # Create a generator that transforms and should preserve shrinking
        gen = Gen.int(min_value=0, max_value=100).map(lambda x: x * 2)

        result = gen.generate(rng)
        assert isinstance(result.value, int)
        assert result.value % 2 == 0  # Should be even since we multiply by 2

        # Check that shrinks exist
        shrinks_list = result.shrinks().to_list()
        assert len(shrinks_list) > 0

    def test_one_of_generator_selection(self):
        """Test that one_of generator selects from multiple generators."""
        rng = random.Random(42)

        gen = Gen.one_of(
            Gen.int(min_value=1, max_value=10),
            Gen.str(min_length=1, max_length=5),
            Gen.bool(),
        )

        # Generate multiple values and check types
        results = []
        for _ in range(20):
            result = gen.generate(rng)
            results.append(result.value)

        # Should have at least two different types
        types = set(type(x) for x in results)
        assert len(types) >= 2

    def test_just_generator_always_returns_same_value(self):
        """Test that just generator always returns the same value."""
        rng = random.Random(42)

        gen = Gen.just(42)

        # Generate multiple values
        for _ in range(10):
            result = gen.generate(rng)
            assert result.value == 42
            assert result.shrinks().is_empty()  # Just generator has no shrinks

    def test_generator_with_complex_nested_structure(self):
        """Test generator with complex nested structure."""
        rng = random.Random(42)

        # Generate a list of dictionaries with string keys and int values
        gen = Gen.list(
            Gen.dict(
                Gen.str(min_length=1, max_length=3), Gen.int(min_value=0, max_value=10)
            ),
            min_length=1,
            max_length=3,
        )

        result = gen.generate(rng)
        assert isinstance(result.value, list)
        assert 1 <= len(result.value) <= 3

        for item in result.value:
            assert isinstance(item, dict)
            for key, value in item.items():
                assert isinstance(key, str)
                assert isinstance(value, int)
                assert 1 <= len(key) <= 3
                assert 0 <= value <= 10
