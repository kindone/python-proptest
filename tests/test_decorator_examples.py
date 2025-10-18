"""
Tests demonstrating the decorator-based API.

This file shows how to use the Hypothesis-style decorator API for
more ergonomic property-based testing.
"""

import pytest

from python_proptest import (
    Gen,
    assume,
    dictionaries,
    example,
    floats,
    for_all,
    given,
    integers,
    just,
    lists,
    note,
    one_of,
    settings,
    text,
)


class TestDecoratorAPIExamples:
    """Examples demonstrating the decorator-based API."""

    def test_basic_arithmetic_properties(self):
        """Test basic arithmetic properties using decorators."""

        @for_all(integers(), integers())
        def test_addition_commutativity(x: int, y: int):
            """Addition is commutative: x + y = y + x"""
            assert x + y == y + x

        @for_all(integers(), integers(), integers())
        def test_addition_associativity(x: int, y: int, z: int):
            """Addition is associative: (x + y) + z = x + (y + z)"""
            assert (x + y) + z == x + (y + z)

        @for_all(integers())
        def test_multiplication_by_zero(x: int):
            """Multiplying by zero gives zero: x * 0 = 0"""
            assert x * 0 == 0

        # Run the tests
        test_addition_commutativity()
        test_addition_associativity()
        test_multiplication_by_zero()

    def test_string_properties(self):
        """Test string properties using decorators."""

        @given(text(min_size=1, max_size=20))
        def test_string_length(s: str):
            """String length is non-negative"""
            assert len(s) >= 0
            assert isinstance(s, str)

        @for_all(text(), text())
        def test_string_concatenation(s1: str, s2: str):
            """String concatenation properties"""
            result = s1 + s2
            assert len(result) == len(s1) + len(s2)
            assert result.startswith(s1)
            assert result.endswith(s2)

        # Run the tests
        test_string_length()
        test_string_concatenation()

    def test_list_properties(self):
        """Test list properties using decorators."""

        @for_all(lists(integers(min_value=0, max_value=100)))
        def test_list_sorting(lst: list):
            """List sorting properties"""
            if len(lst) <= 1:
                return  # Skip empty or single-element lists

            sorted_lst = sorted(lst)
            assert len(sorted_lst) == len(lst)
            assert all(
                sorted_lst[i] <= sorted_lst[i + 1] for i in range(len(sorted_lst) - 1)
            )
            assert set(sorted_lst) == set(lst)  # Same elements

        @for_all(lists(integers()))
        def test_list_reversal(lst: list):
            """List reversal properties"""
            reversed_lst = list(reversed(lst))
            assert len(reversed_lst) == len(lst)
            assert list(reversed(reversed_lst)) == lst  # Double reverse gives original

        # Run the tests
        test_list_sorting()
        test_list_reversal()

    def test_dictionary_properties(self):
        """Test dictionary properties using decorators."""

        @for_all(
            dictionaries(
                text(min_size=1, max_size=5), integers(min_value=0, max_value=100)
            )
        )
        def test_dictionary_keys_values(d: dict):
            """Dictionary key-value properties"""
            for key, value in d.items():
                assert isinstance(key, str)
                assert isinstance(value, int)
                assert len(key) > 0
                assert value >= 0

        @for_all(
            dictionaries(
                text(min_size=1, max_size=3), integers(), min_size=0, max_size=10
            )
        )
        def test_dictionary_size(d: dict):
            """Dictionary size properties"""
            assert 0 <= len(d) <= 10
            assert len(d.keys()) == len(d.values())
            assert len(d.keys()) == len(d.items())

        # Run the tests
        test_dictionary_keys_values()
        test_dictionary_size()

    def test_mixed_type_properties(self):
        """Test mixed type properties using decorators."""

        @for_all(one_of(integers(), floats(), text()))
        def test_mixed_type_property(value):
            """Test properties that work with multiple types"""
            if isinstance(value, (int, float)):
                assert value == value  # Reflexivity
            elif isinstance(value, str):
                assert len(value) >= 0
                assert isinstance(value, str)

        # Run the test
        test_mixed_type_property()

    def test_example_decorator(self):
        """Test the @example decorator for specific test cases."""

        @for_all(integers())
        @example(42)
        @example(-1)
        @example(0)
        def test_integer_examples(x: int):
            """Test specific integer examples"""
            assert isinstance(x, int)

        # Run the test
        test_integer_examples()

    def test_settings_decorator(self):
        """Test the @settings decorator for configuration."""

        @for_all(integers())
        @settings(num_runs=50)
        def test_with_custom_settings(x: int):
            """Test with custom settings"""
            assert isinstance(x, int)

        # Run the test
        test_with_custom_settings()

    def test_assume_function(self):
        """Test the assume() function for conditional testing."""

        @for_all(integers(), integers())
        def test_division_property(x: int, y: int):
            """Test division property with assumption"""
            assume(y != 0)  # Skip test cases where y is 0
            result = x / y
            assert isinstance(result, float)
            # Use approximate equality for floating-point arithmetic
            assert (
                abs(result * y - x) < 1e-10
            )  # Division is approximately inverse of multiplication

        # Run the test
        test_division_property()

    def test_note_function(self):
        """Test the note() function for debugging."""

        @for_all(lists(integers(min_value=1, max_value=10)))
        def test_nested_structures(data: list):
            """Test nested data structures with note()"""
            if len(data) > 0:
                note(f"Testing with list of length {len(data)}")
                note(f"First element: {data[0]}")
                assert all(x >= 1 for x in data)
                assert all(x <= 10 for x in data)

        # Run the test
        test_nested_structures()

    def test_strategy_chaining(self):
        """Test chaining strategies with map and filter."""

        @for_all(
            integers(min_value=1, max_value=100)
            .filter(lambda x: x % 2 == 0)  # Only even numbers
            .map(lambda x: x * 2)
        )  # Double them
        def test_custom_strategy_chain(x: int):
            """Test custom strategy chain"""
            assert x > 0
            assert x % 4 == 0  # Even number * 2 is divisible by 4
            assert isinstance(x, int)

        # Run the test
        test_custom_strategy_chain()

    def test_failing_property_demonstration(self):
        """Demonstrate a failing property (this should fail)."""

        @for_all(integers())
        def test_failing_property(x: int):
            """This property will fail for negative numbers"""
            assert x >= 0  # This will fail for negative integers

        # This test should fail, demonstrating shrinking
        with pytest.raises(AssertionError):
            test_failing_property()


if __name__ == "__main__":
    pytest.main([__file__])
