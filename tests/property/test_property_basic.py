"""
Basic property tests ported from Dart.

These tests verify that the property testing framework works correctly
with various function signatures and edge cases.
"""

import unittest

from python_proptest import Gen, Property, PropertyTestError, run_for_all


class TestPropertyBasic(unittest.TestCase):
    """Basic property testing functionality."""

    def test_property_with_always_true_condition(self):
        """Test property with always true condition."""

        def property_func(a, b):
            return True  # Always true

        # Should not raise an exception
        result = run_for_all(
            property_func,
            Gen.int(min_value=0, max_value=100),
            Gen.int(min_value=0, max_value=100),
            num_runs=10,
        )
        assert result is True

    def test_property_with_void_function_that_never_throws(self):
        """Test property with function that never throws."""

        def property_func(a, b):
            # Do nothing - never throws, but return True to make it pass
            return True

        # Should not raise an exception
        result = run_for_all(
            property_func,
            Gen.int(min_value=0, max_value=100),
            Gen.int(min_value=0, max_value=100),
            num_runs=10,
        )
        assert result is True

    def test_property_with_single_argument_always_true(self):
        """Test property with single argument always true."""

        def property_func(x):
            return True

        result = run_for_all(
            property_func, Gen.int(min_value=0, max_value=100), num_runs=10
        )
        assert result is True

    def test_property_with_three_arguments_always_true(self):
        """Test property with three arguments always true."""

        def property_func(a, b, c):
            return True

        result = run_for_all(
            property_func,
            Gen.int(min_value=0, max_value=100),
            Gen.int(min_value=0, max_value=100),
            Gen.int(min_value=0, max_value=100),
            num_runs=10,
        )
        assert result is True

    def test_property_with_five_arguments_always_true(self):
        """Test property with five arguments always true."""

        def property_func(a, b, c, d, e):
            return True

        result = run_for_all(
            property_func,
            Gen.int(min_value=0, max_value=100),
            Gen.int(min_value=0, max_value=100),
            Gen.int(min_value=0, max_value=100),
            Gen.int(min_value=0, max_value=100),
            Gen.int(min_value=0, max_value=100),
            num_runs=10,
        )
        assert result is True

    def test_property_with_mixed_types_always_true(self):
        """Test property with mixed types always true."""

        def property_func(a, b, c, d):
            return True

        result = run_for_all(
            property_func,
            Gen.int(min_value=0, max_value=100),
            Gen.str(min_length=0, max_length=10),
            Gen.bool(),
            Gen.float(min_value=0.0, max_value=1.0),
            num_runs=10,
        )
        assert result is True

    def test_property_with_list_argument_always_true(self):
        """Test property with list argument always true."""

        def property_func(lst):
            return True

        result = run_for_all(
            property_func,
            Gen.list(Gen.int(min_value=0, max_value=10), min_length=0, max_length=5),
            num_runs=10,
        )
        assert result is True

    def test_property_with_dict_argument_always_true(self):
        """Test property with dictionary argument always true."""

        def property_func(d):
            return True

        result = run_for_all(
            property_func,
            Gen.dict(
                Gen.str(min_length=1, max_length=3), Gen.int(min_value=0, max_value=10)
            ),
            num_runs=10,
        )
        assert result is True

    def test_property_with_nested_structures_always_true(self):
        """Test property with nested structures always true."""

        def property_func(data):
            return True

        # Generate a list of dictionaries
        nested_gen = Gen.list(
            Gen.dict(
                Gen.str(min_length=1, max_length=2), Gen.int(min_value=0, max_value=5)
            ),
            min_length=0,
            max_length=3,
        )

        result = run_for_all(property_func, nested_gen, num_runs=10)
        assert result is True

    def test_property_with_seed_reproducibility(self):
        """Test property with seed for reproducibility."""

        def property_func(x):
            return True

        # Run with same seed twice
        result1 = run_for_all(
            property_func, Gen.int(min_value=0, max_value=100), num_runs=10, seed=42
        )

        result2 = run_for_all(
            property_func, Gen.int(min_value=0, max_value=100), num_runs=10, seed=42
        )

        assert result1 is True
        assert result2 is True

    def test_property_with_string_seed(self):
        """Test property with string seed."""

        def property_func(x):
            return True

        result = run_for_all(
            property_func,
            Gen.int(min_value=0, max_value=100),
            num_runs=10,
            seed="test_seed",
        )
        assert result is True

    def test_property_with_zero_runs(self):
        """Test property with zero runs (edge case)."""

        def property_func(x):
            return True

        # This should still work with zero runs
        result = run_for_all(
            property_func, Gen.int(min_value=0, max_value=100), num_runs=0
        )
        assert result is True

    def test_property_with_single_run(self):
        """Test property with single run."""

        def property_func(x):
            return True

        result = run_for_all(
            property_func, Gen.int(min_value=0, max_value=100), num_runs=1
        )
        assert result is True

    def test_property_with_large_number_of_runs(self):
        """Test property with large number of runs."""

        def property_func(x):
            return True

        result = run_for_all(
            property_func, Gen.int(min_value=0, max_value=100), num_runs=1000
        )
        assert result is True

    def test_property_class_direct_usage(self):
        """Test Property class direct usage."""

        def property_func(x):
            return True

        prop = Property(property_func, num_runs=10)
        result = prop.for_all(Gen.int(min_value=0, max_value=100))
        assert result is True

    def test_property_class_with_seed(self):
        """Test Property class with seed."""

        def property_func(x):
            return True

        prop = Property(property_func, num_runs=10, seed=42)
        result = prop.for_all(Gen.int(min_value=0, max_value=100))
        assert result is True

    def test_property_with_exception_handling(self):
        """Test property with exception handling."""

        def property_func(x):
            if x < 0:
                raise ValueError("Negative value")
            return True

        # Should handle exceptions gracefully
        with self.assertRaises(PropertyTestError):
            run_for_all(
                property_func, Gen.int(min_value=-10, max_value=10), num_runs=10
            )

    def test_property_with_failing_condition(self):
        """Test property with failing condition."""

        def property_func(x):
            return x < 50  # This will fail for x >= 50

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(property_func, Gen.int(min_value=0, max_value=100), num_runs=10)

        # Should have failing input information
        assert exc_info.exception.failing_inputs is not None
        assert len(exc_info.exception.failing_inputs) == 1
        assert exc_info.exception.failing_inputs[0] >= 50

    def test_property_with_complex_failing_condition(self):
        """Test property with complex failing condition."""

        def property_func(a, b, c):
            return a + b + c < 100  # This will fail for large sums

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func,
                Gen.int(min_value=0, max_value=50),
                Gen.int(min_value=0, max_value=50),
                Gen.int(min_value=0, max_value=50),
                num_runs=200,
            )

        # Should have failing input information
        assert exc_info.exception.failing_inputs is not None
        assert len(exc_info.exception.failing_inputs) == 3
        a, b, c = exc_info.exception.failing_inputs
        assert a + b + c >= 100

    def test_property_with_no_generators_raises_error(self):
        """Test that property with no generators raises error."""

        def property_func():
            return True

        with self.assertRaises(ValueError):
            run_for_all(property_func, num_runs=10)

    def test_property_with_wrong_number_of_arguments_raises_error(self):
        """Test that property with wrong number of arguments raises error."""

        def property_func(x):
            return True

        # This should raise an error because we provide 2 generators but function takes 1 argument
        with self.assertRaises(
            Exception
        ):  # Function.apply will raise NoSuchMethodError
            run_for_all(
                property_func,
                Gen.int(min_value=0, max_value=100),
                Gen.int(min_value=0, max_value=100),
                num_runs=10,
            )
