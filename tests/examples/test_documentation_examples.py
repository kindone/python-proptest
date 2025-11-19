"""
Tests for all examples in the documentation.

This file ensures that all code examples in the documentation work correctly
and stay up-to-date with the API changes.
"""

import json
import unittest
from typing import List

from python_proptest import Gen, Property, PropertyTestError, for_all, run_for_all


class TestIndexDocumentationExamples(unittest.TestCase):
    """Test examples from docs/index.md"""

    def test_serialize_parse_roundtrip_example(self):
        """Test the JSON serialization/parsing roundtrip example from index.md"""
        # Generator for keys (non-empty strings without special characters)
        key_gen = Gen.str(min_length=1, max_length=10).filter(
            lambda s: s and "&" not in s and "=" not in s
        )
        # Generator for arbitrary string values
        value_gen = Gen.str(min_length=0, max_length=10)
        # Generator for dictionaries with our specific keys and values
        data_object_gen = Gen.dict(key_gen, value_gen, min_size=0, max_size=10)

        # Simple lambda-based property - perfect for run_for_all
        result = run_for_all(
            lambda original_data: json.loads(json.dumps(original_data))
            == original_data,
            data_object_gen,
        )
        assert result is True

    def test_addition_commutativity_function_based(self):
        """Test the function-based approach example from index.md"""

        def property_func(x: int, y: int):
            return x + y == y + x

        result = run_for_all(property_func, Gen.int(), Gen.int())
        assert result is True

    def test_addition_commutativity_decorator_based(self):
        """Test the decorator-based approach example from index.md"""

        @for_all(Gen.int(), Gen.int())
        def test_addition_commutativity(x: int, y: int):
            assert x + y == y + x

        # Run the test
        test_addition_commutativity()

    def test_pytest_integration_example(self):
        """Test the pytest integration example from index.md"""

        @for_all(Gen.int(), Gen.int())
        def test_addition_commutativity(self, x: int, y: int):
            """Test that addition is commutative - direct decoration!"""
            assert x + y == y + x

        # Run the test
        test_addition_commutativity(self)

    def test_simple_properties_examples(self):
        """Test the simple properties examples from index.md"""
        # Type checks
        result = run_for_all(
            lambda x: isinstance(x, int), Gen.int(min_value=0, max_value=100)
        )
        assert result is True

        # Range validations
        result = run_for_all(
            lambda x: 0 <= x <= 100, Gen.int(min_value=0, max_value=100)
        )
        assert result is True

        # Simple assertions
        result = run_for_all(
            lambda lst: all(isinstance(x, int) for x in lst), Gen.list(Gen.int())
        )
        assert result is True

    def test_complex_math_property_example(self):
        """Test the complex math property example from index.md"""

        @for_all(
            Gen.int(min_value=1, max_value=100), Gen.int(min_value=1, max_value=100)
        )
        def test_complex_math_property(x: int, y: int):
            """Test complex mathematical property with multiple conditions."""
            result = x * y + x + y
            assert result >= x
            assert result >= y
            # Test that result is always positive for positive inputs
            assert result > 0

        test_complex_math_property()

    def test_string_operations_example(self):
        """Test the string operations example from index.md"""

        @for_all(Gen.str(), Gen.str())
        def test_string_operations(s1: str, s2: str):
            """Test string operations with multiple assertions."""
            combined = s1 + s2
            assert len(combined) == len(s1) + len(s2)
            assert combined.startswith(s1)
            assert combined.endswith(s2)

        test_string_operations()


class TestGeneratorsDocumentationExamples(unittest.TestCase):
    """Test examples from docs/generators.md"""

    def test_float_generator_example(self):
        """Test the float generator example from generators.md"""
        # Can produce: 3.14, -0.0, inf, -inf, nan
        result = run_for_all(lambda x: isinstance(x, float), Gen.float())
        assert result is True

    def test_string_generators_examples(self):
        """Test the string generator examples from generators.md"""
        # Generates ASCII strings of length 5 to 10
        result = run_for_all(
            lambda s: isinstance(s, str) and 5 <= len(s) <= 10,
            Gen.str(min_length=5, max_length=10),
        )
        assert result is True

        # Generates Unicode strings of exactly length 3
        result = run_for_all(
            lambda s: isinstance(s, str) and len(s) == 3,
            Gen.unicode_string(min_length=3, max_length=3),
        )
        assert result is True

        # Generates printable ASCII strings of length 0 to 5
        result = run_for_all(
            lambda s: isinstance(s, str) and 0 <= len(s) <= 5,
            Gen.printable_ascii_string(min_length=0, max_length=5),
        )
        assert result is True

        # Generates ASCII strings of length 1 to 3
        result = run_for_all(
            lambda s: isinstance(s, str) and 1 <= len(s) <= 3,
            Gen.ascii_string(min_length=1, max_length=3),
        )
        assert result is True

        # Test character generators
        # Generates ASCII character codes (0-127)
        result = run_for_all(
            lambda c: 0 <= c <= 127,
            Gen.ascii_char(),
        )
        assert result is True

        # Generates Unicode character codes (avoiding surrogate pairs)
        result = run_for_all(
            lambda c: (1 <= c <= 0xD7FF) or (0xE000 <= c <= 0x10FFFF),
            Gen.unicode_char(),
        )
        assert result is True

        # Generates printable ASCII character codes (32-126)
        result = run_for_all(
            lambda c: 32 <= c <= 126,
            Gen.printable_ascii_char(),
        )
        assert result is True

        # Test integer generators
        # Generates integers in range [0, 10) (exclusive of 10)
        result = run_for_all(
            lambda x: 0 <= x < 10,
            Gen.in_range(0, 10),
        )
        assert result is True

        # Generates integers in range [0, 10] (inclusive of 10)
        result = run_for_all(
            lambda x: 0 <= x <= 10,
            Gen.interval(0, 10),
        )
        assert result is True

        # Test unique list generator
        # Generates lists with unique elements, sorted
        result = run_for_all(
            lambda lst: len(lst) == len(set(lst)) and lst == sorted(lst),
            Gen.unique_list(
                Gen.int(min_value=1, max_value=5), min_length=1, max_length=3
            ),
        )
        assert result is True

    def test_list_generator_examples(self):
        """Test the list generator examples from generators.md"""
        # Generates lists of 2 to 5 booleans
        result = run_for_all(
            lambda lst: isinstance(lst, list)
            and 2 <= len(lst) <= 5
            and all(isinstance(x, bool) for x in lst),
            Gen.list(Gen.bool(), min_length=2, max_length=5),
        )
        assert result is True

        # Generates lists of 0 to 10 strings, each 1-3 chars long
        result = run_for_all(
            lambda lst: isinstance(lst, list)
            and 0 <= len(lst) <= 10
            and all(isinstance(x, str) and 1 <= len(x) <= 3 for x in lst),
            Gen.list(Gen.str(min_length=1, max_length=3), min_length=0, max_length=10),
        )
        assert result is True

    def test_dict_generator_example(self):
        """Test the dict generator example from generators.md"""
        # Generates dictionaries with 1 to 3 key-value pairs,
        # where keys are 1-char strings (a-z) and values are floats.
        key_gen = Gen.str(min_length=1, max_length=1).map(
            lambda s: chr(97 + (ord(s[0]) % 26))  # Generate a-z keys
        )

        result = run_for_all(
            lambda d: (
                isinstance(d, dict)
                and 1 <= len(d) <= 3
                and all(
                    isinstance(k, str) and len(k) == 1 and "a" <= k <= "z"
                    for k in d.keys()
                )
                and all(isinstance(v, float) for v in d.values())
            ),
            Gen.dict(key_gen, Gen.float(), min_size=1, max_size=3),
        )
        assert result is True

    def test_tuple_generator_examples(self):
        """Test the tuple generator examples from generators.md"""
        # Generates pairs of (bool, float)
        result = run_for_all(
            lambda t: (
                isinstance(t, tuple)
                and len(t) == 2
                and isinstance(t[0], bool)
                and isinstance(t[1], float)
            ),
            Gen.tuple(Gen.bool(), Gen.float()),
        )
        assert result is True

        # Generates triples of (str, int, str)
        result = run_for_all(
            lambda t: (
                isinstance(t, tuple)
                and len(t) == 3
                and isinstance(t[0], str)
                and isinstance(t[1], int)
                and isinstance(t[2], str)
            ),
            Gen.tuple(
                Gen.str(min_length=0, max_length=5),
                Gen.int(min_value=-100, max_value=100),
                Gen.str(min_length=1, max_length=4),
            ),
        )
        assert result is True

    def test_just_generator_examples(self):
        """Test the just generator examples from generators.md"""
        # Always generates the number 42
        result = run_for_all(lambda x: x == 42, Gen.just(42))
        assert result is True

        # Always generates None
        result = run_for_all(lambda x: x is None, Gen.just(None))
        assert result is True

    def test_lazy_generator_example(self):
        """Test the lazy generator example from generators.md"""

        # Example: Deferring an expensive calculation
        def expensive_calculation():
            # ... imagine complex logic here ...
            return "expensive_result"

        lazy_result_gen = Gen.lazy(expensive_calculation)

        result = run_for_all(lambda x: x == "expensive_result", lazy_result_gen)
        assert result is True


class TestCombinatorsDocumentationExamples(unittest.TestCase):
    """Test examples from docs/combinators.md"""

    def test_map_combinator_examples(self):
        """Test the map combinator examples from combinators.md"""
        # Generate positive integers and map them to their string representation
        positive_int_gen = Gen.int(min_value=1, max_value=1000)
        positive_int_string_gen = positive_int_gen.map(lambda num: str(num))

        result = run_for_all(
            lambda s: isinstance(s, str) and s.isdigit() and 1 <= int(s) <= 1000,
            positive_int_string_gen,
        )
        assert result is True

        # Generate user objects with an ID and a derived email
        user_id_gen = Gen.int(min_value=1, max_value=100)
        user_object_gen = user_id_gen.map(
            lambda id: {"id": id, "email": f"user{id}@example.com"}
        )

        result = run_for_all(
            lambda obj: (
                isinstance(obj, dict)
                and "id" in obj
                and "email" in obj
                and isinstance(obj["id"], int)
                and 1 <= obj["id"] <= 100
                and obj["email"] == f"user{obj['id']}@example.com"
            ),
            user_object_gen,
        )
        assert result is True

    def test_filter_combinator_examples(self):
        """Test the filter combinator examples from combinators.md"""
        # Even numbers
        even_gen = Gen.int().filter(lambda n: n % 2 == 0)

        result = run_for_all(lambda x: isinstance(x, int) and x % 2 == 0, even_gen)
        assert result is True

        # Non-empty strings
        non_empty_string_gen = Gen.str().filter(lambda s: len(s) > 0)

        result = run_for_all(
            lambda s: isinstance(s, str) and len(s) > 0, non_empty_string_gen
        )
        assert result is True

    def test_flat_map_combinator_examples(self):
        """Test the flat_map combinator examples from combinators.md"""
        # String of random length within [1,5)
        string_gen = Gen.int(min_value=1, max_value=5).flat_map(
            lambda n: Gen.str(min_length=n, max_length=n)
        )

        result = run_for_all(
            lambda s: isinstance(s, str) and 1 <= len(s) <= 5, string_gen
        )
        assert result is True

    def test_one_of_combinator_examples(self):
        """Test the one_of combinator examples from combinators.md"""
        # Union of ranges
        union_gen = Gen.one_of(
            Gen.int(min_value=0, max_value=10), Gen.int(min_value=20, max_value=30)
        )

        result = run_for_all(
            lambda x: isinstance(x, int) and ((0 <= x <= 10) or (20 <= x <= 30)),
            union_gen,
        )
        assert result is True

    def test_element_of_combinator_examples(self):
        """Test the element_of combinator examples from combinators.md"""
        # Prime numbers < 10
        prime_gen = Gen.element_of(2, 3, 5, 7)

        result = run_for_all(lambda x: x in [2, 3, 5, 7], prime_gen)
        assert result is True

    def test_weighted_combinator_examples(self):
        """Test the weighted combinator examples from combinators.md"""
        # Note: The current API doesn't support weighted generators
        # This test demonstrates the basic one_of functionality instead
        mixed_gen = Gen.one_of(Gen.str(), Gen.int())

        result = run_for_all(lambda x: isinstance(x, (str, int)), mixed_gen)
        assert result is True

        # Test element_of with multiple values
        value_gen = Gen.element_of("a", "b", "c")

        result = run_for_all(lambda x: x in ["a", "b", "c"], value_gen)
        assert result is True

    def test_weighted_element_of_example(self):
        """Test the weighted element_of example from combinators.md"""
        # Test the documented weighted element_of functionality
        weighted_char_gen = Gen.element_of(
            Gen.weighted_value("a", 0.8),  # 80%
            Gen.weighted_value("b", 0.1),  # 10%
            Gen.weighted_value("c", 0.1),  # 10%
        )

        result = run_for_all(lambda x: x in ["a", "b", "c"], weighted_char_gen)
        assert result is True

        # Test that weighted_value works correctly
        weighted_a = Gen.weighted_value("a", 0.8)
        assert weighted_a.value == "a"
        assert weighted_a.weight == 0.8

        # Test mixed weighted/unweighted values
        mixed_gen = Gen.element_of(
            Gen.weighted_value("x", 0.5),  # 50%
            "y",  # 25% (remaining weight split equally)
            "z",  # 25% (remaining weight split equally)
        )

        result = run_for_all(lambda x: x in ["x", "y", "z"], mixed_gen)
        assert result is True

    def test_weighted_one_of_example(self):
        """Test the weighted one_of example from combinators.md"""
        # Test the documented weighted one_of functionality
        weighted_gen = Gen.one_of(
            Gen.weighted_gen(Gen.just(0), 0.8),  # 80% chance of getting 0
            Gen.weighted_gen(
                Gen.int(min_value=1, max_value=100), 0.2
            ),  # 20% chance of getting 1-100
        )

        result = run_for_all(
            lambda x: isinstance(x, int) and 0 <= x <= 100, weighted_gen
        )
        assert result is True

        # Test that weighted_gen works correctly
        weighted_zero = Gen.weighted_gen(Gen.just(0), 0.8)
        assert weighted_zero.weight == 0.8

        # Test mixed weighted/unweighted generators
        mixed_gen = Gen.one_of(
            Gen.weighted_gen(Gen.just("a"), 0.6),  # 60%
            Gen.just("b"),  # 20% (remaining weight split equally)
            Gen.just("c"),  # 20% (remaining weight split equally)
        )

        result = run_for_all(lambda x: x in ["a", "b", "c"], mixed_gen)
        assert result is True

    def test_construct_combinator_examples(self):
        """Test the construct combinator examples from combinators.md"""

        # Simple Point class for testing
        class Point:
            def __init__(self, x: int, y: int):
                self.x = x
                self.y = y

            def __eq__(self, other):
                return (
                    isinstance(other, Point) and self.x == other.x and self.y == other.y
                )

        # Construct Point object
        point_gen = Gen.construct(Point, Gen.int(), Gen.int())

        result = run_for_all(
            lambda p: isinstance(p, Point)
            and isinstance(p.x, int)
            and isinstance(p.y, int),
            point_gen,
        )
        assert result is True


class TestPropertiesDocumentationExamples(unittest.TestCase):
    """Test examples from docs/properties.md"""

    def test_property_class_example(self):
        """Test the Property class example from properties.md"""

        # Property: The sum of two positive numbers is positive
        def sum_property(a: int, b: int):
            return a + b > 0  # Return boolean

        # Running the property
        prop = Property(sum_property, num_runs=200)
        prop.for_all(
            Gen.int(min_value=1, max_value=100), Gen.int(min_value=1, max_value=100)
        )

    def test_property_example_method(self):
        """Test the property example method from properties.md"""

        def prop_func(a: int, b: int):
            return a > b

        prop = Property(prop_func)
        # Note: The current API doesn't have an example method
        # This test demonstrates the property works correctly
        assert prop_func(5, 3) is True  # 5 > 3
        assert prop_func(3, 5) is False  # 3 > 5 is False

    def test_run_for_all_example(self):
        """Test the run_for_all example from properties.md"""

        # Property: Reversing a list twice yields the original list
        def property_func(arr: list):
            # Predicate using assertions
            assert list(reversed(list(reversed(arr)))) == arr
            return True

        result = run_for_all(property_func, Gen.list(Gen.int()))
        assert result is True

    def test_for_all_decorator_example(self):
        """Test the @for_all decorator example from properties.md"""

        @for_all(Gen.int(), Gen.int())
        def test_addition_commutativity(x: int, y: int):
            """Test that addition is commutative."""
            assert x + y == y + x

        test_addition_commutativity()

    def test_property_with_seed_example(self):
        """Test the property with seed example from properties.md"""

        @for_all(Gen.int(), Gen.int(), seed=42)
        def test_reproducible_property(x: int, y: int):
            """Test that the same seed produces the same sequence."""
            assert isinstance(x, int)
            assert isinstance(y, int)

        test_reproducible_property()

    def test_property_with_settings_example(self):
        """Test the property with settings example from properties.md"""
        from python_proptest import settings

        @for_all(Gen.int(), Gen.int())
        @settings(num_runs=50)
        def test_property_with_custom_runs(x: int, y: int):
            """Test with custom number of runs."""
            assert x + y == y + x

        test_property_with_custom_runs()


class TestShrinkingDocumentationExamples(unittest.TestCase):
    """Test examples from docs/shrinking.md"""

    def test_shrinking_example(self):
        """Test the shrinking example from shrinking.md"""

        # Generator for pairs [a, b] where a <= b
        pair_gen = Gen.int(min_value=0, max_value=1000).flat_map(
            lambda a: Gen.tuple(Gen.just(a), Gen.int(min_value=a, max_value=1000))
        )

        def property_func(tup):
            # This property fails if the difference is large
            return tup[1] - tup[0] <= 5

        try:
            run_for_all(property_func, pair_gen)
            # If we get here, the property passed (unlikely with this generator)
            self.fail("Expected PropertyTestError to be raised")
        except PropertyTestError as e:
            # The error message will likely show a shrunk example
            self.assertIn("Property failed", str(e))
            # The shrunk example should be much simpler than the original failing input
            self.assertIsNotNone(e.minimal_inputs)

    def test_integer_shrinking_example(self):
        """Test integer shrinking example from shrinking.md"""

        def property_func(x):
            # This property fails for large numbers
            return x <= 10

        try:
            run_for_all(property_func, Gen.int(min_value=0, max_value=1000))
            self.fail("Expected PropertyTestError to be raised")
        except PropertyTestError as e:
            # The shrunk value should be close to the boundary (10 or 11)
            self.assertIsNotNone(e.minimal_inputs)
            minimal_value = e.minimal_inputs[0]
            self.assertGreater(
                minimal_value, 10
            )  # Should be the smallest failing value

    def test_string_shrinking_example(self):
        """Test string shrinking example from shrinking.md"""

        def property_func(s):
            # This property fails for long strings
            return len(s) <= 3

        try:
            run_for_all(property_func, Gen.str(min_length=0, max_length=20))
            self.fail("Expected PropertyTestError to be raised")
        except PropertyTestError as e:
            # The shrunk string should be short but still fail
            self.assertIsNotNone(e.minimal_inputs)
            minimal_string = e.minimal_inputs[0]
            self.assertGreater(
                len(minimal_string), 3
            )  # Should be the shortest failing string


class TestStatefulTestingDocumentationExamples(unittest.TestCase):
    """Test examples from docs/stateful-testing.md"""

    def test_simple_stateful_property_example(self):
        """Test the simple stateful property example from stateful-testing.md"""
        from python_proptest import (
            SimpleAction,
            simpleActionGenOf,
            simpleStatefulProperty,
        )

        # Define the system type
        MySystem = List[int]

        # Generator for the initial state (e.g., an empty list)
        initial_gen = Gen.just([])

        # Action: Add an element
        add_action_gen = Gen.int().map(
            lambda val: SimpleAction(lambda arr: arr.append(val))
        )

        # Action: Clear the list
        clear_action_gen = Gen.just(SimpleAction(lambda arr: arr.clear()))

        # Combine action generators
        action_gen = simpleActionGenOf(add_action_gen, clear_action_gen)

        # Create the stateful property
        prop = simpleStatefulProperty(initial_gen, action_gen)

        # Run the property test
        prop.go()

    def test_stateful_property_with_model_example(self):
        """Test the stateful property with model example from stateful-testing.md"""
        from python_proptest import Action, actionGenOf, statefulProperty

        # Define the system type
        MySystem = List[int]
        ModelType = int  # Model is just the sum of elements

        # Generator for the initial state
        initial_gen = Gen.just([])

        # Generator for the initial model
        initial_model_gen = Gen.just(0)

        # Action: Add an element
        add_action_gen = Gen.int().map(
            lambda val: Action(lambda arr, model: arr.append(val))
        )

        # Action: Clear the list
        clear_action_gen = Gen.just(Action(lambda arr, model: arr.clear()))

        # Combine action generators
        action_gen = actionGenOf(MySystem, ModelType, add_action_gen, clear_action_gen)

        # Create the stateful property
        prop = statefulProperty(
            initial_gen, action_gen, initial_model_gen=initial_model_gen
        )

        # Run the property test
        prop.go()


class TestPytestIntegrationDocumentationExamples(unittest.TestCase):
    """Test examples from docs/pytest-integration.md"""

    def test_direct_decoration_example(self):
        """Test the direct decoration example from pytest-integration.md"""

        @for_all(Gen.int(), Gen.int())
        def test_addition_commutativity(self, x: int, y: int):
            """Test that addition is commutative - direct decoration!"""
            assert x + y == y + x

        test_addition_commutativity(self)

    def test_multiplication_associativity_example(self):
        """Test the multiplication associativity example from pytest-integration.md"""

        @for_all(Gen.int(), Gen.int(), Gen.int())
        def test_multiplication_associativity(self, x: int, y: int, z: int):
            """Test that multiplication is associative - direct decoration!"""
            assert (x * y) * z == x * (y * z)

        test_multiplication_associativity(self)


class TestUnittestIntegrationDocumentationExamples(unittest.TestCase):
    """Test examples from docs/unittest-integration.md"""

    def test_unittest_addition_commutativity(self):
        """Test the unittest addition commutativity example from unittest-integration.md"""

        @for_all(Gen.int(), Gen.int())
        def test_addition_commutativity(self, x: int, y: int):
            """Test that addition is commutative."""
            result1 = x + y
            result2 = y + x
            self.assertEqual(result1, result2)

        test_addition_commutativity(self)

    def test_unittest_multiplication_associativity(self):
        """Test the unittest multiplication associativity example from unittest-integration.md"""

        @for_all(Gen.int(), Gen.int(), Gen.int())
        def test_multiplication_associativity(self, x: int, y: int, z: int):
            """Test that multiplication is associative."""
            result1 = (x * y) * z
            result2 = x * (y * z)
            self.assertEqual(result1, result2)

        test_multiplication_associativity(self)

    def test_unittest_string_concatenation(self):
        """Test the unittest string concatenation example from unittest-integration.md"""

        @for_all(Gen.str(), Gen.str())
        def test_string_concatenation(self, s1: str, s2: str):
            """Test string concatenation properties."""
            combined = s1 + s2
            self.assertEqual(len(combined), len(s1) + len(s2))
            self.assertTrue(combined.startswith(s1))
            self.assertTrue(combined.endswith(s2))

        test_string_concatenation(self)


class TestPytestBestPracticesDocumentationExamples(unittest.TestCase):
    """Test examples from docs/pytest-best-practices.md"""

    def test_nested_property_test_example(self):
        """Test the nested property test example from pytest-best-practices.md"""

        @for_all(Gen.int(), Gen.int())
        def test_commutativity(self, x: int, y: int):
            assert x + y == y + x

        test_commutativity(self)

    def test_nested_multiplication_associativity(self):
        """Test the nested multiplication associativity example from pytest-best-practices.md"""

        @for_all(Gen.int(), Gen.int(), Gen.int())
        def test_associativity(self, x: int, y: int, z: int):
            assert (x * y) * z == x * (y * z)

        test_associativity(self)


if __name__ == "__main__":
    unittest.main()
