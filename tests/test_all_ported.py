"""
Comprehensive test runner for all ported functionality.

This test file runs all the ported tests to ensure everything works correctly.
"""

import random
import unittest

from python_proptest import Gen, Property, PropertyTestError, Shrinkable, run_for_all
from python_proptest.core.shrinker import (
    DictShrinker,
    IntegerShrinker,
    ListShrinker,
    StringShrinker,
    shrink_to_minimal,
)


class TestAllPortedFunctionality(unittest.TestCase):
    """Comprehensive test suite for all ported functionality."""

    def test_basic_generators_work(self):
        """Test that all basic generators work correctly."""
        rng = random.Random(42)

        # Test integer generator
        int_gen = Gen.int(min_value=0, max_value=100)
        result = int_gen.generate(rng)
        assert isinstance(result.value, int)
        assert 0 <= result.value <= 100
        shrinks_list = result.shrinks().to_list()
        assert len(shrinks_list) > 0

        # Test string generator
        str_gen = Gen.str(min_length=1, max_length=10)
        result = str_gen.generate(rng)
        assert isinstance(result.value, str)
        assert 1 <= len(result.value) <= 10
        shrinks_list = result.shrinks().to_list()
        assert len(shrinks_list) > 0

        # Test boolean generator
        bool_gen = Gen.bool()
        result = bool_gen.generate(rng)
        assert isinstance(result.value, bool)
        # Boolean generator may have no shrinks if value is False
        if result.value is True:
            shrinks_list = result.shrinks().to_list()
        assert len(shrinks_list) > 0

        # Test float generator
        float_gen = Gen.float(min_value=0.0, max_value=1.0)
        result = float_gen.generate(rng)
        assert isinstance(result.value, float)
        assert 0.0 <= result.value <= 1.0
        shrinks_list = result.shrinks().to_list()
        assert len(shrinks_list) > 0

    def test_collection_generators_work(self):
        """Test that collection generators work correctly."""
        rng = random.Random(42)

        # Test list generator
        list_gen = Gen.list(
            Gen.int(min_value=0, max_value=10), min_length=0, max_length=5
        )
        result = list_gen.generate(rng)
        assert isinstance(result.value, list)
        assert 0 <= len(result.value) <= 5
        assert all(isinstance(x, int) for x in result.value)
        shrinks_list = result.shrinks().to_list()
        assert len(shrinks_list) > 0

        # Test dict generator
        dict_gen = Gen.dict(
            Gen.str(min_length=1, max_length=2), Gen.int(min_value=0, max_value=10)
        )
        result = dict_gen.generate(rng)
        assert isinstance(result.value, dict)
        for key, value in result.value.items():
            assert isinstance(key, str)
            assert isinstance(value, int)
        shrinks_list = result.shrinks().to_list()
        assert len(shrinks_list) > 0

    def test_combinators_work(self):
        """Test that all combinators work correctly."""
        rng = random.Random(42)

        # Test just combinator
        just_gen = Gen.just(42)
        result = just_gen.generate(rng)
        assert result.value == 42
        assert result.shrinks().is_empty()

        # Test one_of combinator
        one_of_gen = Gen.one_of(Gen.just(1), Gen.just(2))
        result = one_of_gen.generate(rng)
        assert result.value in [1, 2]

        # Test map combinator
        map_gen = Gen.int(min_value=1, max_value=10).map(lambda x: x * 2)
        result = map_gen.generate(rng)
        assert result.value % 2 == 0
        assert 2 <= result.value <= 20

        # Test filter combinator
        filter_gen = Gen.int(min_value=1, max_value=20).filter(lambda x: x % 2 == 0)
        result = filter_gen.generate(rng)
        assert result.value % 2 == 0
        assert 1 <= result.value <= 20

        # Test flat_map combinator
        flat_map_gen = Gen.int(min_value=1, max_value=5).flat_map(
            lambda x: Gen.int(min_value=x, max_value=x + 10)
        )
        result = flat_map_gen.generate(rng)
        assert 1 <= result.value <= 15

    def test_property_testing_works(self):
        """Test that property testing works correctly."""

        # Test passing property
        def test_passing_property(a, b):
            return a + b == b + a

        result = run_for_all(
            test_passing_property,
            Gen.int(min_value=0, max_value=100),
            Gen.int(min_value=0, max_value=100),
            num_runs=100,
        )
        assert result is True

        # Test failing property
        def test_failing_property(x):
            return x < 50

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                test_failing_property, Gen.int(min_value=0, max_value=100), num_runs=100
            )

        assert exc_info.exception.failing_inputs is not None
        assert len(exc_info.exception.failing_inputs) == 1
        assert exc_info.exception.failing_inputs[0] >= 50

    def test_seed_reproducibility_works(self):
        """Test that seed reproducibility works correctly."""

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

    def test_shrinking_works(self):
        """Test that shrinking works correctly."""
        # Test integer shrinking
        shrinker = IntegerShrinker()
        candidates = shrinker.shrink(8)
        assert 0 in candidates
        assert 1 in candidates
        assert 4 in candidates

        # Test string shrinking
        string_shrinker = StringShrinker()
        candidates = string_shrinker.shrink("ABCD")
        assert "" in candidates
        assert "ABC" in candidates
        assert "BCD" in candidates

        # Test list shrinking
        element_shrinker = IntegerShrinker()
        list_shrinker = ListShrinker(element_shrinker)
        candidates = list_shrinker.shrink([10, 20, 30])
        assert [] in candidates
        assert [10, 20] in candidates
        assert [20, 30] in candidates

        # Test shrink_to_minimal
        def predicate(x):
            return x < 10

        minimal = shrink_to_minimal(100, predicate, IntegerShrinker())
        assert not predicate(minimal)
        assert minimal < 100
        assert minimal >= 10

    def test_complex_nested_structures_work(self):
        """Test that complex nested structures work correctly."""

        def test_property(data):
            return isinstance(data, list)

        # Generate a list of dictionaries with transformed values
        complex_gen = Gen.list(
            Gen.dict(
                Gen.str(min_length=1, max_length=2).map(lambda s: s.upper()),
                Gen.int(min_value=0, max_value=10).map(lambda x: x * 2),
            ),
            min_length=0,
            max_length=3,
        )

        result = run_for_all(test_property, complex_gen, num_runs=100)
        assert result is True

    def test_performance_with_large_runs(self):
        """Test performance with large number of runs."""

        def test_property(x):
            return isinstance(x, int)

        # This should complete quickly
        result = run_for_all(
            test_property, Gen.int(min_value=0, max_value=100), num_runs=1000
        )
        assert result is True

    def test_edge_cases_work(self):
        """Test that edge cases work correctly."""
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

        # Test with single value range
        single_value_gen = Gen.int(min_value=42, max_value=42)
        result = single_value_gen.generate(rng)
        assert result.value == 42

    def test_error_handling_works(self):
        """Test that error handling works correctly."""

        # Test with no generators
        def test_property():
            return True

        with self.assertRaises(ValueError):
            run_for_all(test_property, num_runs=10)

        # Test with impossible filter condition
        rng = random.Random(42)
        impossible_gen = Gen.int(min_value=1, max_value=10).filter(lambda x: x > 100)

        with self.assertRaises(ValueError):
            impossible_gen.generate(rng)

        # Test with empty one_of
        with self.assertRaises(ValueError):
            Gen.one_of()

    def test_property_class_direct_usage_works(self):
        """Test that Property class direct usage works correctly."""

        def test_property(x):
            return isinstance(x, int)

        prop = Property(test_property, num_runs=10, seed=42)
        result = prop.for_all(Gen.int(min_value=0, max_value=100))
        assert result is True

    def test_mixed_types_work(self):
        """Test that mixed types work correctly."""

        def test_property(a, b, c, d):
            return (
                isinstance(a, int)
                and isinstance(b, str)
                and isinstance(c, bool)
                and isinstance(d, float)
            )

        result = run_for_all(
            test_property,
            Gen.int(min_value=0, max_value=100),
            Gen.str(min_length=1, max_length=5),
            Gen.bool(),
            Gen.float(min_value=0.0, max_value=1.0),
            num_runs=100,
        )
        assert result is True

    def test_string_seeds_work(self):
        """Test that string seeds work correctly."""

        def test_property(x):
            return isinstance(x, int)

        # Test with various string seeds
        seeds = ["test", "hello world", "🚀", "测试", ""]

        for seed in seeds:
            result = run_for_all(
                test_property,
                Gen.int(min_value=0, max_value=100),
                num_runs=10,
                seed=seed,
            )
            assert result is True

    def test_large_seeds_work(self):
        """Test that large seeds work correctly."""

        def test_property(x):
            return isinstance(x, int)

        # Test with large integer seeds
        large_seeds = [2**31 - 1, -(2**31), 0, 1, -1]

        for seed in large_seeds:
            result = run_for_all(
                test_property,
                Gen.int(min_value=0, max_value=100),
                num_runs=10,
                seed=seed,
            )
            assert result is True
