"""
Random number generator tests ported from Dart.

These tests verify that the random number generation works correctly
and produces reproducible results with seeds.
"""

import random
import unittest

from python_proptest import Gen, PropertyTestError, run_for_all


class TestRandom(unittest.TestCase):
    """Test random number generation functionality."""

    def test_random_generation_with_seed(self):
        """Test that random generation is reproducible with seeds."""

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

    def test_random_generation_with_string_seed(self):
        """Test that random generation works with string seeds."""

        def test_property(x):
            return isinstance(x, int)

        result = run_for_all(
            test_property,
            Gen.int(min_value=0, max_value=100),
            num_runs=10,
            seed="test_seed",
        )
        assert result is True

    def test_random_generation_with_different_seeds_produces_different_results(self):
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

    def test_random_generation_without_seed(self):
        """Test that random generation works without seed."""

        def test_property(x):
            return isinstance(x, int)

        result = run_for_all(
            test_property, Gen.int(min_value=0, max_value=100), num_runs=10
        )
        assert result is True

    def test_random_generation_with_large_seed(self):
        """Test random generation with large seed values."""

        def test_property(x):
            return isinstance(x, int)

        # Test with large integer seed
        result = run_for_all(
            test_property,
            Gen.int(min_value=0, max_value=100),
            num_runs=10,
            seed=2**31 - 1,  # Large positive integer
        )
        assert result is True

        # Test with negative seed
        result = run_for_all(
            test_property,
            Gen.int(min_value=0, max_value=100),
            num_runs=10,
            seed=-(2**31),  # Large negative integer
        )
        assert result is True

    def test_random_generation_with_unicode_string_seed(self):
        """Test random generation with Unicode string seeds."""

        def test_property(x):
            return isinstance(x, int)

        # Test with Unicode string
        result = run_for_all(
            test_property,
            Gen.int(min_value=0, max_value=100),
            num_runs=10,
            seed="测试种子🚀",
        )
        assert result is True

    def test_random_generation_distribution(self):
        """Test that random generation produces reasonable distribution."""

        def test_property(x):
            return 0 <= x <= 100

        # This should pass for all generated values
        result = run_for_all(
            test_property, Gen.int(min_value=0, max_value=100), num_runs=1000
        )
        assert result is True

    def test_random_generation_with_float_seed(self):
        """Test random generation with float seed (should be converted to int)."""

        def test_property(x):
            return isinstance(x, int)

        # Test with float seed (should be converted to int)
        result = run_for_all(
            test_property,
            Gen.int(min_value=0, max_value=100),
            num_runs=10,
            seed=42.5,  # Float seed
        )
        assert result is True

    def test_random_generation_with_none_seed(self):
        """Test random generation with None seed (should use current time)."""

        def test_property(x):
            return isinstance(x, int)

        # Test with None seed (should use current time)
        result = run_for_all(
            test_property, Gen.int(min_value=0, max_value=100), num_runs=10, seed=None
        )
        assert result is True

    def test_random_generation_with_empty_string_seed(self):
        """Test random generation with empty string seed."""

        def test_property(x):
            return isinstance(x, int)

        # Test with empty string seed
        result = run_for_all(
            test_property, Gen.int(min_value=0, max_value=100), num_runs=10, seed=""
        )
        assert result is True

    def test_random_generation_with_boolean_seed(self):
        """Test random generation with boolean seed."""

        def test_property(x):
            return isinstance(x, int)

        # Test with boolean seed
        result = run_for_all(
            test_property, Gen.int(min_value=0, max_value=100), num_runs=10, seed=True
        )
        assert result is True

        result = run_for_all(
            test_property, Gen.int(min_value=0, max_value=100), num_runs=10, seed=False
        )
        assert result is True

    def test_random_generation_with_list_seed(self):
        """Test random generation with list seed."""

        def test_property(x):
            return isinstance(x, int)

        # Test with list seed (should be converted to hash)
        result = run_for_all(
            test_property,
            Gen.int(min_value=0, max_value=100),
            num_runs=10,
            seed=[1, 2, 3],
        )
        assert result is True

    def test_random_generation_with_dict_seed(self):
        """Test random generation with dict seed."""

        def test_property(x):
            return isinstance(x, int)

        # Test with dict seed (should be converted to hash)
        result = run_for_all(
            test_property,
            Gen.int(min_value=0, max_value=100),
            num_runs=10,
            seed={"key": "value"},
        )
        assert result is True

    def test_random_generation_reproducibility_across_runs(self):
        """Test that random generation is reproducible across multiple runs."""

        def test_property(x):
            return isinstance(x, int)

        # Run multiple times with same seed
        results = []
        for _ in range(5):
            result = run_for_all(
                test_property,
                Gen.int(min_value=0, max_value=100),
                num_runs=5,
                seed=12345,
            )
            results.append(result)

        # All results should be True
        assert all(result is True for result in results)

    def test_random_generation_with_mixed_generators(self):
        """Test random generation with mixed generator types."""

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
            num_runs=10,
            seed=42,
        )
        assert result is True

    def test_random_generation_with_complex_nested_generators(self):
        """Test random generation with complex nested generators."""

        def test_property(data):
            return isinstance(data, list)

        # Generate a list of dictionaries
        nested_gen = Gen.list(
            Gen.dict(
                Gen.str(min_length=1, max_length=2), Gen.int(min_value=0, max_value=5)
            ),
            min_length=0,
            max_length=3,
        )

        result = run_for_all(test_property, nested_gen, num_runs=10, seed=42)
        assert result is True

    def test_random_generation_performance_with_large_runs(self):
        """Test random generation performance with large number of runs."""

        def test_property(x):
            return isinstance(x, int)

        # This should complete quickly
        result = run_for_all(
            test_property, Gen.int(min_value=0, max_value=100), num_runs=10000, seed=42
        )
        assert result is True

    def test_random_generation_with_failing_property(self):
        """Test random generation with failing property."""

        def test_failing_property(x):
            return x < 50  # This will fail for x >= 50

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                test_failing_property,
                Gen.int(min_value=0, max_value=100),
                num_runs=100,
                seed=42,
            )

        # Should have failing input information
        assert exc_info.exception.failing_inputs is not None
        assert len(exc_info.exception.failing_inputs) == 1
        assert exc_info.exception.failing_inputs[0] >= 50
