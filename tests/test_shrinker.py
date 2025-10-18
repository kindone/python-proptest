"""
Shrinker tests ported from Dart.

These tests verify that the shrinking functionality works correctly
for finding minimal failing cases.
"""

import random
import unittest

from python_proptest import Gen, PropertyTestError, Shrinkable, run_for_all
from python_proptest.core.shrinker import (
    DictShrinker,
    IntegerShrinker,
    ListShrinker,
    StringShrinker,
    shrink_to_minimal,
)


class TestShrinker(unittest.TestCase):
    """Test shrinking functionality."""

    def test_integer_shrinker_shrinks_towards_zero(self):
        """Test that integer shrinker shrinks towards zero."""
        shrinker = IntegerShrinker()

        # Test positive number
        candidates = shrinker.shrink(8)
        assert 0 in candidates  # Should shrink towards zero
        assert 1 in candidates  # Should include 1
        assert 4 in candidates  # Should include 8/2

        # Test negative number
        candidates = shrinker.shrink(-8)
        assert 0 in candidates  # Should shrink towards zero
        assert -1 in candidates  # Should include -1
        assert -4 in candidates  # Should include -8/2

    def test_integer_shrinker_with_zero(self):
        """Test integer shrinker with zero."""
        shrinker = IntegerShrinker()
        candidates = shrinker.shrink(0)
        assert len(candidates) == 0  # Zero has no shrinks

    def test_integer_shrinker_with_one(self):
        """Test integer shrinker with one."""
        shrinker = IntegerShrinker()
        candidates = shrinker.shrink(1)
        assert 0 in candidates  # Should shrink to zero
        assert len(candidates) == 1  # Only one shrink candidate

    def test_string_shrinker_shrinks_length(self):
        """Test that string shrinker shrinks length."""
        shrinker = StringShrinker()

        # Test non-empty string
        candidates = shrinker.shrink("ABCD")
        assert "" in candidates  # Should shrink to empty string
        assert "ABC" in candidates  # Should remove last character
        assert "BCD" in candidates  # Should remove first character
        assert "A" in candidates  # Should shrink to first character
        assert "D" in candidates  # Should shrink to last character

    def test_string_shrinker_with_empty_string(self):
        """Test string shrinker with empty string."""
        shrinker = StringShrinker()
        candidates = shrinker.shrink("")
        assert len(candidates) == 0  # Empty string has no shrinks

    def test_string_shrinker_with_single_character(self):
        """Test string shrinker with single character."""
        shrinker = StringShrinker()
        candidates = shrinker.shrink("A")
        assert "" in candidates  # Should shrink to empty string
        # Single character can shrink to empty string and itself
        assert len(candidates) >= 1  # At least one shrink candidate

    def test_list_shrinker_shrinks_length_and_elements(self):
        """Test that list shrinker shrinks length and elements."""
        element_shrinker = IntegerShrinker()
        shrinker = ListShrinker(element_shrinker)

        # Test non-empty list
        candidates = shrinker.shrink([10, 20, 30])
        assert [] in candidates  # Should shrink to empty list
        assert [10, 20] in candidates  # Should remove last element
        assert [20, 30] in candidates  # Should remove first element
        assert [5, 20, 30] in candidates  # Should shrink first element
        assert [10, 10, 30] in candidates  # Should shrink second element
        assert [10, 20, 15] in candidates  # Should shrink third element

    def test_list_shrinker_with_empty_list(self):
        """Test list shrinker with empty list."""
        element_shrinker = IntegerShrinker()
        shrinker = ListShrinker(element_shrinker)
        candidates = shrinker.shrink([])
        assert len(candidates) == 0  # Empty list has no shrinks

    def test_list_shrinker_with_single_element(self):
        """Test list shrinker with single element."""
        element_shrinker = IntegerShrinker()
        shrinker = ListShrinker(element_shrinker)
        candidates = shrinker.shrink([10])
        assert [] in candidates  # Should shrink to empty list
        assert [0] in candidates  # Should shrink element to 0
        assert [5] in candidates  # Should shrink element to 5

    def test_dict_shrinker_shrinks_size_and_values(self):
        """Test that dict shrinker shrinks size and values."""
        key_shrinker = StringShrinker()
        value_shrinker = IntegerShrinker()
        shrinker = DictShrinker(key_shrinker, value_shrinker)

        # Test non-empty dict
        candidates = shrinker.shrink({"a": 10, "b": 20})
        assert {} in candidates  # Should shrink to empty dict
        assert {"a": 10} in candidates  # Should remove last item
        assert {"b": 20} in candidates  # Should remove first item
        assert {"a": 0, "b": 20} in candidates  # Should shrink first value
        assert {"a": 10, "b": 0} in candidates  # Should shrink second value

    def test_dict_shrinker_with_empty_dict(self):
        """Test dict shrinker with empty dict."""
        key_shrinker = StringShrinker()
        value_shrinker = IntegerShrinker()
        shrinker = DictShrinker(key_shrinker, value_shrinker)
        candidates = shrinker.shrink({})
        assert len(candidates) == 0  # Empty dict has no shrinks

    def test_dict_shrinker_with_single_item(self):
        """Test dict shrinker with single item."""
        key_shrinker = StringShrinker()
        value_shrinker = IntegerShrinker()
        shrinker = DictShrinker(key_shrinker, value_shrinker)
        candidates = shrinker.shrink({"a": 10})
        assert {} in candidates  # Should shrink to empty dict
        assert {"a": 0} in candidates  # Should shrink value to 0
        assert {"a": 5} in candidates  # Should shrink value to 5

    def test_shrink_to_minimal_finds_minimal_failing_case(self):
        """Test that shrink_to_minimal finds minimal failing case."""

        def predicate(x):
            return x < 10  # This fails for x >= 10

        # Start with a large failing value
        minimal = shrink_to_minimal(100, predicate, IntegerShrinker())
        assert not predicate(minimal)  # Should still fail
        assert minimal < 100  # Should be smaller than original
        assert minimal >= 10  # Should be minimal failing case

    def test_shrink_to_minimal_with_impossible_condition(self):
        """Test shrink_to_minimal with impossible condition."""

        def predicate(x):
            return x > 1000  # This fails for all x <= 1000

        # Start with a small failing value
        minimal = shrink_to_minimal(5, predicate, IntegerShrinker())
        assert not predicate(minimal)  # Should still fail
        assert minimal <= 5  # Should be smaller or equal to original

    def test_shrink_to_minimal_with_passing_condition(self):
        """Test shrink_to_minimal with passing condition."""

        def predicate(x):
            return x >= 0  # This passes for all x >= 0

        # Start with a passing value, but shrink_to_minimal will find a failing candidate
        # from the shrink candidates (like -5) and return that as the minimal failing case
        minimal = shrink_to_minimal(10, predicate, IntegerShrinker())
        assert not predicate(minimal)  # Should find a failing case
        assert minimal < 10  # Should be smaller than original

    def test_shrinkable_preserves_value_and_shrinks(self):
        """Test that Shrinkable preserves value and shrinks."""
        # Test with integer
        shrinkable = Shrinkable(42)
        assert shrinkable.value == 42
        assert shrinkable.shrinks().is_empty()  # No shrinks by default

        # Test with shrinks
        from python_proptest.core.stream import Stream

        shrinkable_with_shrinks = Shrinkable(
            42, lambda: Stream.many([Shrinkable(21), Shrinkable(0)])
        )
        assert shrinkable_with_shrinks.value == 42
        shrinks_list = shrinkable_with_shrinks.shrinks().to_list()
        assert len(shrinks_list) == 2
        assert shrinks_list[0].value == 21
        assert shrinks_list[1].value == 0

    def test_shrinkable_equality_and_hash(self):
        """Test Shrinkable equality and hash."""
        shrinkable1 = Shrinkable(42)
        shrinkable2 = Shrinkable(42)
        shrinkable3 = Shrinkable(43)

        assert shrinkable1 == shrinkable2
        assert shrinkable1 != shrinkable3
        assert hash(shrinkable1) == hash(shrinkable2)
        assert hash(shrinkable1) != hash(shrinkable3)

    def test_shrinking_with_generator_integration(self):
        """Test shrinking with generator integration."""

        def test_failing_property(x):
            return x < 50  # This will fail for x >= 50

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                test_failing_property, Gen.int(min_value=0, max_value=100), num_runs=100
            )

        # Should have failing input information
        assert exc_info.exception.failing_inputs is not None
        assert len(exc_info.exception.failing_inputs) == 1
        assert exc_info.exception.failing_inputs[0] >= 50

    def test_shrinking_with_string_generator(self):
        """Test shrinking with string generator."""

        def test_failing_property(s):
            return len(s) < 5  # This will fail for strings of length >= 5

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                test_failing_property,
                Gen.str(min_length=0, max_length=10),
                num_runs=100,
            )

        # Should have failing input information
        assert exc_info.exception.failing_inputs is not None
        assert len(exc_info.exception.failing_inputs) == 1
        assert len(exc_info.exception.failing_inputs[0]) >= 5

    def test_shrinking_with_list_generator(self):
        """Test shrinking with list generator."""

        def test_failing_property(lst):
            return len(lst) < 3  # This will fail for lists of length >= 3

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                test_failing_property,
                Gen.list(
                    Gen.int(min_value=0, max_value=10), min_length=0, max_length=5
                ),
                num_runs=100,
            )

        # Should have failing input information
        assert exc_info.exception.failing_inputs is not None
        assert len(exc_info.exception.failing_inputs) == 1
        assert len(exc_info.exception.failing_inputs[0]) >= 3

    def test_shrinking_with_dict_generator(self):
        """Test shrinking with dict generator."""

        def test_failing_property(d):
            return len(d) < 2  # This will fail for dicts of size >= 2

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                test_failing_property,
                Gen.dict(
                    Gen.str(min_length=1, max_length=2),
                    Gen.int(min_value=0, max_value=10),
                    min_size=0,
                    max_size=3,
                ),
                num_runs=100,
            )

        # Should have failing input information
        assert exc_info.exception.failing_inputs is not None
        assert len(exc_info.exception.failing_inputs) == 1
        assert len(exc_info.exception.failing_inputs[0]) >= 2

    def test_shrinking_with_complex_nested_structure(self):
        """Test shrinking with complex nested structure."""

        def test_failing_property(data):
            # This will fail for nested structures with total elements >= 3
            def count_elements(obj):
                if isinstance(obj, list):
                    return sum(count_elements(item) for item in obj)
                elif isinstance(obj, dict):
                    return sum(count_elements(v) for v in obj.values())
                else:
                    return 1

            return count_elements(data) < 3

        # Generate a list of dictionaries
        nested_gen = Gen.list(
            Gen.dict(
                Gen.str(min_length=1, max_length=2), Gen.int(min_value=0, max_value=5)
            ),
            min_length=0,
            max_length=3,
        )

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(test_failing_property, nested_gen, num_runs=100)

        # Should have failing input information
        assert exc_info.exception.failing_inputs is not None
        assert len(exc_info.exception.failing_inputs) == 1

    def test_shrinking_performance_with_large_values(self):
        """Test shrinking performance with large values."""

        def test_failing_property(x):
            return x < 1000  # This will fail for x >= 1000

        # This should complete quickly even with large initial value
        minimal = shrink_to_minimal(10000, test_failing_property, IntegerShrinker())
        assert not test_failing_property(minimal)
        assert minimal < 10000
        assert minimal >= 1000

    def test_shrinking_with_max_attempts_limit(self):
        """Test shrinking with max attempts limit."""

        def predicate(x):
            return x < 10  # This fails for x >= 10

        # Test with very low max attempts
        minimal = shrink_to_minimal(100, predicate, IntegerShrinker(), max_attempts=1)
        assert not predicate(minimal)  # Should still fail
        assert minimal < 100  # Should be smaller than original
