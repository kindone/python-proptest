"""
Tests for the new decorator-based API.

This module demonstrates and tests the Hypothesis-style decorator API
for more ergonomic property-based testing.
"""

import unittest

from python_proptest import (
    Gen,
    assume,
    example,
    for_all,
    note,
    run_property_test,
    settings,
)


class TestDecoratorAPI(unittest.TestCase):
    """Test the decorator-based API."""

    def test_basic_decorator_usage(self):
        """Test basic @for_all decorator usage."""

        @for_all(
            Gen.int(min_value=1, max_value=100), Gen.int(min_value=1, max_value=100)
        )
        def test_addition_commutativity(x: int, y: int):
            """Test that addition is commutative."""
            assert x + y == y + x

        # Run the test
        test_addition_commutativity()

    def test_decorator_with_generators(self):
        """Test @for_all decorator with Generator objects."""

        @for_all(
            Gen.int(min_value=1, max_value=100),
            Gen.int(min_value=1, max_value=100),
            Gen.int(min_value=1, max_value=100),
        )
        def test_multiplication_associativity(x: int, y: int, z: int):
            """Test that multiplication is associative."""
            assert (x * y) * z == x * (y * z)

        # Run the test
        test_multiplication_associativity()

    def test_decorator_with_mixed_types(self):
        """Test @for_all decorator with mixed types."""

        @for_all(Gen.int(), Gen.str(min_length=1, max_length=10))
        def test_string_length_property(x: int, s: str):
            """Test string length property."""
            assert len(s) >= 0
            assert isinstance(s, str)
            assert isinstance(x, int)

        # Run the test
        test_string_length_property()

    def test_decorator_with_lists(self):
        """Test @for_all decorator with list generators."""

        @for_all(Gen.list(Gen.int(), min_length=0, max_length=10))
        def test_list_sorting(lst: list):
            """Test list sorting properties."""
            if len(lst) <= 1:
                return  # Skip trivial cases

            sorted_lst = sorted(lst)
            assert len(sorted_lst) == len(lst)
            assert all(
                sorted_lst[i] <= sorted_lst[i + 1] for i in range(len(sorted_lst) - 1)
            )

        # Run the test
        test_list_sorting()

    def test_decorator_with_dictionaries(self):
        """Test @for_all decorator with dictionary generators."""

        @for_all(
            Gen.dict(
                Gen.str(min_length=1, max_length=5), Gen.int(), min_size=0, max_size=5
            )
        )
        def test_dictionary_properties(d: dict):
            """Test dictionary properties."""
            assert isinstance(d, dict)
            for key, value in d.items():
                assert isinstance(key, str)
                assert isinstance(value, int)
                assert len(key) > 0

        # Run the test
        test_dictionary_properties()

    def test_decorator_with_one_of(self):
        """Test @for_all decorator with one_of generator."""

        @for_all(Gen.one_of(Gen.int(), Gen.float(), Gen.str()))
        def test_mixed_type_property(value):
            """Test property with mixed types."""
            assert value is not None
            assert isinstance(value, (int, float, str))

        # Run the test
        test_mixed_type_property()

    def test_decorator_with_example(self):
        """Test @for_all decorator with @example."""

        @for_all(Gen.int())
        @example(42)
        @example(-1)
        def test_integer_properties(x: int):
            """Test integer properties with specific examples."""
            assert isinstance(x, int)
            assert x * 0 == 0

        # Run the test
        test_integer_properties()

    def test_decorator_with_settings(self):
        """Test @for_all decorator with @settings."""

        @for_all(Gen.int())
        @settings(num_runs=50, seed=42)
        def test_with_custom_settings(x: int):
            """Test with custom settings."""
            assert isinstance(x, int)

        # Run the test
        test_with_custom_settings()

    def test_settings_with_invalid_parameter(self):
        """Test @settings rejects unsupported parameters."""

        with self.assertRaises(ValueError) as context:

            @settings(num_runs=50, max_iterations=1000)  # max_iterations is invalid
            @for_all(Gen.int())
            def test_invalid_setting(x: int):
                assert isinstance(x, int)

        self.assertIn("max_iterations", str(context.exception))
        self.assertIn("Unsupported parameter", str(context.exception))

    def test_settings_with_multiple_invalid_parameters(self):
        """Test @settings rejects multiple unsupported parameters."""

        with self.assertRaises(ValueError) as context:

            @settings(num_runs=50, timeout=30, max_retries=5)  # multiple invalid
            @for_all(Gen.int())
            def test_invalid_settings(x: int):
                assert isinstance(x, int)

        error_msg = str(context.exception)
        self.assertIn("Unsupported parameter", error_msg)
        # Should mention at least one of the invalid params
        self.assertTrue("timeout" in error_msg or "max_retries" in error_msg)

    def test_decorator_with_assume(self):
        """Test @for_all decorator with assume."""

        @for_all(Gen.int(), Gen.int())
        def test_division_property(x: int, y: int):
            """Test division property with assumption."""
            assume(y != 0)  # Skip cases where y is 0
            # Test a simpler property that's always true
            assert isinstance(x, int)
            assert isinstance(y, int)
            assert y != 0  # This should always be true after assume

        # Run the test
        test_division_property()

    def test_decorator_with_note(self):
        """Test @for_all decorator with note."""

        @for_all(Gen.int())
        def test_with_note(x: int):
            """Test with note for debugging."""
            note(f"Testing with x = {x}")
            assert x * 2 == x + x

        # Run the test
        test_with_note()

    def test_decorator_error_handling(self):
        """Test error handling in decorator API."""

        @for_all(Gen.int())
        def test_failing_property(x: int):
            """Test that fails for certain values."""
            assert x < 100  # This will fail for x >= 100

        # This should raise an AssertionError
        with self.assertRaises(AssertionError):
            test_failing_property()

    def test_decorator_argument_count_mismatch(self):
        """Test error when argument count doesn't match."""

        with self.assertRaises(ValueError):

            @for_all(Gen.int(), Gen.int())
            def test_wrong_arg_count(x: int):
                """Function with wrong argument count."""
                assert x > 0

    def test_run_property_test_function(self):
        """Test the run_property_test utility function."""

        @for_all(Gen.int())
        def test_simple_property(x: int):
            """Simple property test."""
            assert x * 0 == 0

        # Run using the utility function
        result = run_property_test(test_simple_property)
        assert result is True  # run_property_test returns True on success

    def test_decorator_with_complex_function(self):
        """Test decorator with a complex function that would be awkward with lambda."""

        @for_all(Gen.list(Gen.int(), min_length=1, max_length=10))
        def test_list_operations(lst: list):
            """Test complex list operations."""
            # This would be very awkward with lambda syntax
            if len(lst) == 0:
                return

            # Test various list properties
            original_length = len(lst)
            lst_copy = lst.copy()

            # Test that sorting doesn't change length
            sorted_lst = sorted(lst_copy)
            assert len(sorted_lst) == original_length

            # Test that sorting is idempotent
            double_sorted = sorted(sorted_lst)
            assert double_sorted == sorted_lst

            # Test that all elements are preserved
            assert set(lst) == set(sorted_lst)

            # Test ordering property
            for i in range(len(sorted_lst) - 1):
                assert sorted_lst[i] <= sorted_lst[i + 1]

        # Run the test
        test_list_operations()

    def test_decorator_with_nested_structures(self):
        """Test decorator with nested data structures."""

        @for_all(
            Gen.list(
                Gen.dict(Gen.str(min_length=1), Gen.int(), min_size=1, max_size=3),
                min_length=0,
                max_length=5,
            )
        )
        def test_nested_structures(data: list):
            """Test properties of nested data structures."""
            assert isinstance(data, list)

            for item in data:
                assert isinstance(item, dict)
                assert len(item) > 0

                for key, value in item.items():
                    assert isinstance(key, str)
                    assert isinstance(value, int)
                    assert len(key) > 0

        # Run the test
        test_nested_structures()

    @for_all(
        Gen.int(min_value=1, max_value=100)
        .filter(lambda x: x % 2 == 0)
        .map(lambda x: x * 2)
    )
    def test_decorator_with_custom_generator_chain(self, x: int):
        """Test decorator with chained generators."""

        """Test custom generator chain."""
        assert x > 0
        assert x % 4 == 0  # Even number * 2 is divisible by 4
        assert isinstance(x, int)

    @for_all(Gen.int(min_value=1, max_value=100))
    def test_for_all_decorator(self, x: int):
        """Test custom generator chain."""
        assert x >= 1
        assert x <= 100
        assert isinstance(x, int)


class TestGeneratorAPI(unittest.TestCase):
    """Test the Generator API with map/filter/flat_map."""

    def test_generator_map(self):
        """Test Generator.map method."""
        generator = Gen.int(min_value=1, max_value=10)
        doubled = generator.map(lambda x: x * 2)

        @for_all(doubled)
        def test_doubled_integers(x: int):
            assert x % 2 == 0
            assert x >= 2
            assert x <= 20

        test_doubled_integers()

    def test_generator_filter(self):
        """Test Generator.filter method."""
        generator = Gen.int(min_value=1, max_value=20)
        even_only = generator.filter(lambda x: x % 2 == 0)

        @for_all(even_only)
        def test_even_integers(x: int):
            assert x % 2 == 0
            assert x >= 2
            assert x <= 20

        test_even_integers()

    def test_generator_flat_map(self):
        """Test Generator.flat_map method."""
        generator = Gen.int(min_value=1, max_value=5)

        def create_list_generator(n: int):
            return Gen.list(Gen.just(n), min_length=n, max_length=n)

        list_generator = generator.flat_map(create_list_generator)

        @for_all(list_generator)
        def test_flatmap_result(lst: list):
            assert len(lst) > 0
            assert all(isinstance(x, int) for x in lst)
            assert all(x == lst[0] for x in lst)  # All elements should be the same

        test_flatmap_result()


if __name__ == "__main__":
    # Run some examples
    print("Running decorator API examples...")

    @for_all(Gen.int(), Gen.int())
    def example_commutativity(x: int, y: int):
        assert x + y == y + x

    @for_all(Gen.list(Gen.int(), min_length=0, max_length=10))
    def example_list_sorting(lst: list):
        if len(lst) <= 1:
            return
        sorted_lst = sorted(lst)
        assert len(sorted_lst) == len(lst)
        assert all(
            sorted_lst[i] <= sorted_lst[i + 1] for i in range(len(sorted_lst) - 1)
        )

    example_commutativity()
    example_list_sorting()

    print("✅ All examples passed!")
