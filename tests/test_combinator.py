"""
Combinator tests ported from Dart.

These tests verify that generator combinators work correctly
for combining and transforming generators.
"""

import random
import unittest

from python_proptest import Gen, PropertyTestError, for_all, integers, run_for_all


class TestCombinators(unittest.TestCase):
    """Test generator combinators."""

    def test_just_produces_constant_values(self):
        """Test that just produces constant values."""
        rng = random.Random(42)
        const_gen = Gen.just(42)

        for _ in range(5):
            result = const_gen.generate(rng)
            assert result.value == 42
            assert result.shrinks().is_empty()  # Just generator has no shrinks

    def test_just_with_various_types(self):
        """Test just with various types."""
        rng = random.Random(42)

        test_cases = [
            (42, int),
            ("hello", str),
            (True, bool),
            (3.14, float),
            ([1, 2, 3], list),
            ({"key": "value"}, dict),
        ]

        for value, expected_type in test_cases:
            gen = Gen.just(value)
            result = gen.generate(rng)
            assert result.value == value
            assert isinstance(result.value, expected_type)

    def test_element_of_selects_from_provided_values(self):
        """Test that elementOf selects from provided values."""
        rng = random.Random(42)
        element_gen = Gen.element_of(1, 2, 3, 4, 5)

        results = []
        for _ in range(20):
            result = element_gen.generate(rng)
            results.append(result.value)

        # All results should be from the provided list
        for result in results:
            assert result in [1, 2, 3, 4, 5]

    def test_element_of_with_mixed_types(self):
        """Test elementOf with mixed types."""
        rng = random.Random(42)
        mixed_gen = Gen.element_of(42, "hello", True, 3.14)

        results = []
        for _ in range(20):
            result = mixed_gen.generate(rng)
            results.append(result.value)

        # Should generate different types
        types = set(type(x) for x in results)
        assert len(types) >= 2

    def test_one_of_selects_from_generators(self):
        """Test that oneOf selects from generators."""
        rng = random.Random(42)
        one_of_gen = Gen.one_of(Gen.just(1), Gen.just(2))

        results = []
        for _ in range(20):
            result = one_of_gen.generate(rng)
            results.append(result.value)

        # All results should be from the provided generators
        for result in results:
            assert result in [1, 2]

    def test_one_of_with_mixed_generator_types(self):
        """Test oneOf with mixed generator types."""
        rng = random.Random(42)
        mixed_gen = Gen.one_of(
            Gen.int(min_value=1, max_value=10),
            Gen.str(min_length=1, max_length=5),
            Gen.bool(),
        )

        results = []
        for _ in range(30):
            result = mixed_gen.generate(rng)
            results.append(result.value)

        # Should generate different types
        types = set(type(x) for x in results)
        assert len(types) >= 2

        # Check that each type is valid
        for value in results:
            assert isinstance(value, (int, str, bool))

    def test_map_transformation(self):
        """Test map transformation."""
        rng = random.Random(42)
        mapped_gen = Gen.int(min_value=1, max_value=10).map(lambda x: x * 2)

        results = []
        for _ in range(10):
            result = mapped_gen.generate(rng)
            results.append(result.value)

        # All results should be even numbers
        for result in results:
            assert result % 2 == 0
            assert 2 <= result <= 20

    def test_map_with_string_transformation(self):
        """Test map with string transformation."""
        rng = random.Random(42)
        string_gen = Gen.int(min_value=1, max_value=10).map(lambda x: f"Number: {x}")

        results = []
        for _ in range(10):
            result = string_gen.generate(rng)
            results.append(result.value)

        # All results should be strings starting with "Number: "
        for result in results:
            assert isinstance(result, str)
            assert result.startswith("Number: ")
            assert result[8:].isdigit()  # The number part should be digits

    def test_filter_works_correctly(self):
        """Test that filter works correctly."""
        rng = random.Random(42)
        even_gen = Gen.int(min_value=1, max_value=20).filter(lambda x: x % 2 == 0)

        results = []
        for _ in range(10):
            result = even_gen.generate(rng)
            results.append(result.value)

        # All results should be even numbers
        for result in results:
            assert result % 2 == 0
            assert 1 <= result <= 20

    def test_filter_with_impossible_condition_raises_error(self):
        """Test that filter raises error when condition is impossible."""
        rng = random.Random(42)
        impossible_gen = Gen.int(min_value=1, max_value=10).filter(lambda x: x > 100)

        with self.assertRaises(ValueError):
            impossible_gen.generate(rng)

    def test_flat_map_works_correctly(self):
        """Test that flatMap works correctly."""
        rng = random.Random(42)
        flat_mapped_gen = Gen.int(min_value=1, max_value=5).flat_map(
            lambda x: Gen.int(min_value=x, max_value=x + 10)
        )

        results = []
        for _ in range(10):
            result = flat_mapped_gen.generate(rng)
            results.append(result.value)

        # All results should be in the expected range
        for result in results:
            assert 1 <= result <= 15  # 1 to 5 + 10

    def test_flat_map_with_string_length(self):
        """Test flatMap with string length generation."""
        rng = random.Random(42)
        string_length_gen = Gen.int(min_value=1, max_value=5).flat_map(
            lambda length: Gen.str(min_length=length, max_length=length)
        )

        results = []
        for _ in range(10):
            result = string_length_gen.generate(rng)
            results.append(result.value)

        # All results should be strings with correct length
        for result in results:
            assert isinstance(result, str)
            assert 1 <= len(result) <= 5

    def test_multiple_transformations_chained(self):
        """Test multiple transformations chained together."""
        rng = random.Random(42)
        chained_gen = (
            Gen.int(min_value=1, max_value=100)
            .map(lambda x: x * 2)
            .filter(lambda x: x > 10)
            .map(lambda x: f"Value: {x}")
        )

        results = []
        for _ in range(10):
            result = chained_gen.generate(rng)
            results.append(result.value)

        # All results should be strings starting with "Value: " and containing even numbers > 10
        for result in results:
            assert isinstance(result, str)
            assert result.startswith("Value: ")
            number = int(result[7:])  # Extract the number part
            assert number > 10
            assert number % 2 == 0

    def test_combinator_with_property_testing(self):
        """Test combinators with property testing."""

        @for_all(integers(min_value=1, max_value=10).map(lambda x: f"Number: {x}"))
        def test_property(self, x: str):
            assert isinstance(x, str) and x.startswith("Number: ")

        test_property(self)

    def test_combinator_with_failing_property(self):
        """Test combinators with failing property."""

        @for_all(integers(min_value=0, max_value=100).map(lambda x: x * 2))
        def test_failing_property(self, x: int):
            assert x < 50  # This will fail for x >= 50

        with self.assertRaises(AssertionError) as exc_info:
            test_failing_property(self)

        # Should have failing input information in the error message
        error_msg = str(exc_info.exception)
        assert "Property failed" in error_msg

    def test_combinator_reproducibility_with_seeds(self):
        """Test combinator reproducibility with seeds."""

        def test_property(x):
            return isinstance(x, str)

        # Test with same seed - keeping run_for_all for seed testing
        result1 = run_for_all(
            test_property,
            Gen.int(min_value=1, max_value=10).map(lambda x: f"Number: {x}"),
            num_runs=10,
            seed=42,
        )

        result2 = run_for_all(
            test_property,
            Gen.int(min_value=1, max_value=10).map(lambda x: f"Number: {x}"),
            num_runs=10,
            seed=42,
        )

        assert result1 is True
        assert result2 is True

    def test_combinator_with_complex_nested_structures(self):
        """Test combinators with complex nested structures."""
        rng = random.Random(42)

        # Generate a list of dictionaries with transformed values
        complex_gen = Gen.list(
            Gen.dict(
                Gen.str(min_length=1, max_length=2).map(lambda s: s.upper()),
                Gen.int(min_value=0, max_value=10).map(lambda x: x * 2),
            ),
            min_length=1,
            max_length=3,
        )

        result = complex_gen.generate(rng)
        assert isinstance(result.value, list)
        assert 1 <= len(result.value) <= 3

        for item in result.value:
            assert isinstance(item, dict)
            for key, value in item.items():
                assert isinstance(key, str)
                assert isinstance(value, int)
                assert key.isupper()  # Should be uppercase
                assert value % 2 == 0  # Should be even (multiplied by 2)

    def test_combinator_performance_with_large_runs(self):
        """Test combinator performance with large number of runs."""

        @for_all(
            integers(min_value=1, max_value=100).map(lambda x: f"Number: {x}"),
            num_runs=1000,
        )
        def test_property(self, x: str):
            assert isinstance(x, str)

        test_property(self)

    def test_combinator_with_edge_cases(self):
        """Test combinators with edge cases."""
        rng = random.Random(42)

        # Test with empty list
        empty_list_gen = Gen.list(Gen.int(), min_length=0, max_length=0)
        result = empty_list_gen.generate(rng)
        assert result.value == []

        # Test with single element list
        single_list_gen = Gen.list(Gen.just(42), min_length=1, max_length=1)
        result = single_list_gen.generate(rng)
        assert result.value == [42]

        # Test with empty dictionary
        empty_dict_gen = Gen.dict(Gen.str(), Gen.int(), min_size=0, max_size=0)
        result = empty_dict_gen.generate(rng)
        assert result.value == {}

    def test_combinator_with_one_of_empty_list_raises_error(self):
        """Test that oneOf with empty list raises error."""
        with self.assertRaises(ValueError):
            Gen.one_of()

    def test_combinator_with_one_of_single_generator(self):
        """Test oneOf with single generator."""
        rng = random.Random(42)
        single_gen = Gen.one_of(Gen.just(42))

        for _ in range(5):
            result = single_gen.generate(rng)
            assert result.value == 42
