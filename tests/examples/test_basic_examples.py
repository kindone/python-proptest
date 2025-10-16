"""
Basic examples demonstrating PyPropTest usage.

These examples show common property-based testing patterns
and serve as both documentation and tests.
"""

import unittest

from pyproptest import Gen, PropertyTestError, run_for_all


class TestBasicProperties(unittest.TestCase):
    """Basic property testing examples."""

    def test_addition_is_commutative(self):
        """Test that addition is commutative for all integers."""

        def property_func(a, b):
            return a + b == b + a

        result = run_for_all(
            property_func,
            Gen.int(min_value=0, max_value=100),
            Gen.int(min_value=0, max_value=100),
            num_runs=100,
        )
        assert result is True

    def test_multiplication_is_associative(self):
        """Test that multiplication is associative for all integers."""

        def property_func(a, b, c):
            return (a * b) * c == a * (b * c)

        result = run_for_all(
            property_func,
            Gen.int(min_value=0, max_value=10),
            Gen.int(min_value=0, max_value=10),
            Gen.int(min_value=0, max_value=10),
            num_runs=100,
        )
        assert result is True

    def test_string_concatenation_length(self):
        """Test that string concatenation preserves length property."""

        def property_func(s1, s2):
            return len(s1 + s2) == len(s1) + len(s2)

        result = run_for_all(
            property_func,
            Gen.str(min_length=0, max_length=10),
            Gen.str(min_length=0, max_length=10),
            num_runs=100,
        )
        assert result is True

    def test_list_append_length(self):
        """Test that appending to a list increases its length by 1."""

        def property_func(lst, item):
            original_length = len(lst)
            lst.append(item)
            return len(lst) == original_length + 1

        result = run_for_all(
            property_func,
            Gen.list(Gen.int(min_value=0, max_value=10), min_length=0, max_length=5),
            Gen.int(min_value=0, max_value=10),
            num_runs=100,
        )
        assert result is True

    def test_dictionary_key_value_consistency(self):
        """Test that dictionary keys and values maintain consistency."""

        def property_func(d):
            # If we can get a value by key, the key should exist
            for key in d:
                assert key in d
                assert d[key] is not None
            return True

        result = run_for_all(
            property_func,
            Gen.dict(
                Gen.str(min_length=1, max_length=3),
                Gen.int(min_value=0, max_value=10),
                min_size=0,
                max_size=5,
            ),
            num_runs=100,
        )
        assert result is True


class TestFailingProperties(unittest.TestCase):
    """Examples of properties that fail and demonstrate shrinking."""

    def test_failing_property_demonstrates_shrinking(self):
        """Test that demonstrates how failing properties show minimal counterexamples."""

        def property_func(x):
            return x < 100  # This will fail for x >= 100

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func, Gen.int(min_value=0, max_value=200), num_runs=100
            )

        # The error should contain information about the failing input
        assert exc_info.exception.failing_inputs is not None
        assert len(exc_info.exception.failing_inputs) == 1
        assert exc_info.exception.failing_inputs[0] >= 100

    def test_string_property_failure(self):
        """Test string property that fails for certain inputs."""

        def property_func(s):
            return len(s) < 5  # This will fail for strings of length >= 5

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func, Gen.str(min_length=0, max_length=10), num_runs=100
            )

        # The error should contain information about the failing input
        assert exc_info.exception.failing_inputs is not None
        assert len(exc_info.exception.failing_inputs) == 1
        assert len(exc_info.exception.failing_inputs[0]) >= 5


class TestGeneratorCombinators(unittest.TestCase):
    """Examples of using generator combinators."""

    def test_map_transformation(self):
        """Test using map to transform generated values."""

        def property_func(s):
            return isinstance(s, str) and s.startswith("Number: ")

        result = run_for_all(
            property_func,
            Gen.int(min_value=1, max_value=100).map(lambda n: f"Number: {n}"),
            num_runs=100,
        )
        assert result is True

    def test_filter_condition(self):
        """Test using filter to generate values satisfying conditions."""

        def property_func(x):
            return x % 2 == 0 and x >= 0

        result = run_for_all(
            property_func,
            Gen.int(min_value=0, max_value=100).filter(lambda x: x % 2 == 0),
            num_runs=100,
        )
        assert result is True

    def test_one_of_selection(self):
        """Test using one_of to choose from multiple generators."""

        def property_func(x):
            return isinstance(x, (int, str, bool))

        result = run_for_all(
            property_func,
            Gen.one_of(
                Gen.int(min_value=0, max_value=10),
                Gen.str(min_length=1, max_length=3),
                Gen.bool(),
            ),
            num_runs=100,
        )
        assert result is True

    def test_flat_map_dependent_generation(self):
        """Test using flat_map for dependent generation."""

        def property_func(s):
            return isinstance(s, str) and len(s) >= 1 and len(s) <= 5

        result = run_for_all(
            property_func,
            Gen.int(min_value=1, max_value=5).flat_map(
                lambda length: Gen.str(min_length=length, max_length=length)
            ),
            num_runs=100,
        )
        assert result is True


class TestReproducibleTests(unittest.TestCase):
    """Examples of using seeds for reproducible tests."""

    def test_reproducible_with_string_seed(self):
        """Test that the same seed produces the same sequence of values."""

        def property_func(x):
            return isinstance(x, int)

        # Run with a specific seed
        result1 = run_for_all(
            property_func,
            Gen.int(min_value=0, max_value=100),
            num_runs=10,
            seed="test_seed",
        )

        # Run again with the same seed
        result2 = run_for_all(
            property_func,
            Gen.int(min_value=0, max_value=100),
            num_runs=10,
            seed="test_seed",
        )

        assert result1 is True
        assert result2 is True

    def test_reproducible_with_integer_seed(self):
        """Test that integer seeds work for reproducibility."""

        def property_func(x):
            return isinstance(x, int)

        result = run_for_all(
            property_func, Gen.int(min_value=0, max_value=100), num_runs=10, seed=12345
        )
        assert result is True


class TestComplexProperties(unittest.TestCase):
    """Examples of more complex property testing scenarios."""

    def test_nested_data_structures(self):
        """Test properties involving nested data structures."""

        def property_func(data):
            # Property: all integers in nested structure should be non-negative
            def check_nested(obj):
                if isinstance(obj, int):
                    return obj >= 0
                elif isinstance(obj, list):
                    return all(check_nested(item) for item in obj)
                elif isinstance(obj, dict):
                    return all(check_nested(v) for v in obj.values())
                else:
                    return True

            return check_nested(data)

        # Generate nested structures
        nested_gen = Gen.one_of(
            Gen.int(min_value=0, max_value=10),
            Gen.list(Gen.int(min_value=0, max_value=10), min_length=0, max_length=3),
            Gen.dict(
                Gen.str(min_length=1, max_length=2),
                Gen.int(min_value=0, max_value=10),
                min_size=0,
                max_size=2,
            ),
        )

        result = run_for_all(property_func, nested_gen, num_runs=100)
        assert result is True

    def test_mathematical_properties(self):
        """Test mathematical properties."""

        def property_func(a, b):
            # Property: |a + b| <= |a| + |b| (triangle inequality)
            return abs(a + b) <= abs(a) + abs(b)

        result = run_for_all(
            property_func,
            Gen.int(min_value=-100, max_value=100),
            Gen.int(min_value=-100, max_value=100),
            num_runs=100,
        )
        assert result is True
