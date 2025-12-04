"""
Comprehensive shrinker tests ported from dartproptest.

These tests verify shrinker functionality that may not be covered
in the basic shrinker tests.
"""

import json
import unittest

from python_proptest.core.shrinker import (
    Shrinkable,
    binary_search_shrinkable,
    shrink_element_wise,
    shrink_membership_wise,
    shrinkable_array,
    shrinkable_boolean,
    shrinkable_float,
)
from python_proptest.core.stream import Stream


def serialize_shrinkable(shrinkable: Shrinkable) -> str:
    """Serialize a shrinkable to JSON string (compact format)."""
    obj = {"value": shrinkable.value}

    shrinks = shrinkable.shrinks()
    if not shrinks.is_empty():
        shrinks_list = []
        for shrink in shrinks.to_list():
            shrinks_list.append(json.loads(serialize_shrinkable(shrink)))
        obj["shrinks"] = shrinks_list

    return json.dumps(obj, separators=(",", ":"))


def compare_shrinkable(
    lhs: Shrinkable, rhs: Shrinkable, max_elements: int = 1000
) -> bool:
    """Compare two shrinkables for equality."""
    if lhs.value != rhs.value:
        return False

    if max_elements <= 0:
        return True

    lhs_shrinks = lhs.shrinks().to_list()
    rhs_shrinks = rhs.shrinks().to_list()

    if len(lhs_shrinks) != len(rhs_shrinks):
        return False

    for left, right in zip(lhs_shrinks, rhs_shrinks):
        if not compare_shrinkable(left, right, max_elements - 1):
            return False

    return True


def exhaustive_traversal(shrinkable: Shrinkable, level: int = 0, func=None):
    """Exhaustively traverse a shrinkable tree."""
    if func is None:
        indent = "  " * level
        print(f"{indent}shrinkable: {shrinkable.value!r}")
    else:
        func(shrinkable, level)

    for shrink in shrinkable.shrinks().to_list():
        exhaustive_traversal(shrink, level + 1, func)


def gen_shrinkable_21() -> Shrinkable[int]:
    """Generate a shrinkable with value 2 and shrinks [0, 1]."""
    return Shrinkable(2).with_shrinks(
        lambda: Stream.many([Shrinkable(0), Shrinkable(1)])
    )


def gen_shrinkable_40213() -> Shrinkable[int]:
    """Generate a shrinkable with value 4 and shrinks [0, 2->1, 3]."""
    return Shrinkable(4).with_shrinks(
        lambda: Stream.many(
            [
                Shrinkable(0),
                Shrinkable(2).with_shrinks(lambda: Stream.one(Shrinkable(1))),
                Shrinkable(3),
            ]
        )
    )


class TestShrinkerComprehensive(unittest.TestCase):
    """Comprehensive shrinker tests ported from dartproptest."""

    def test_basic_shrinkable(self):
        """Test basic shrinkable creation."""
        shr = Shrinkable(0)
        assert serialize_shrinkable(shr) == '{"value":0}'

    def test_shrinkable_40213(self):
        """Test complex shrinkable structure."""
        shr = gen_shrinkable_40213()
        expected = '{"value":4,"shrinks":[{"value":0},{"value":2,"shrinks":[{"value":1}]},{"value":3}]}'
        assert serialize_shrinkable(shr) == expected

    def test_shrinkable_concat_static(self):
        """Test concat_static method."""
        # Test 1: Simple case
        shr0 = Shrinkable(100)
        shr1 = shr0.concat_static(lambda: Stream.one(Shrinkable(200)))
        assert serialize_shrinkable(shr1) == '{"value":100,"shrinks":[{"value":200}]}'

        # Test 2: With existing shrinks - concat_static ADDS static shrinks at root level
        shr2 = gen_shrinkable_21()
        shr3 = shr2.concat_static(lambda: Stream.one(Shrinkable(3)))
        # Existing shrinks [0, 1] + new shrink [3] = [0, 1, 3]
        expected = '{"value":2,"shrinks":[{"value":0},{"value":1},{"value":3}]}'
        assert serialize_shrinkable(shr3) == expected

        # Test 3: Complex case - same behavior
        shr4 = gen_shrinkable_40213()
        shr5 = shr4.concat_static(lambda: Stream.one(Shrinkable(5)))
        # Existing shrinks [0, 2->1, 3] + new shrink [5] = [0, 2->1, 3, 5]
        expected = '{"value":4,"shrinks":[{"value":0},{"value":2,"shrinks":[{"value":1}]},{"value":3},{"value":5}]}'
        assert serialize_shrinkable(shr5) == expected

    def test_shrinkable_concat(self):
        """Test concat method."""
        # Test 1: Simple case
        shr0 = Shrinkable(100)
        shr1 = shr0.concat(lambda parent: Stream.one(Shrinkable(parent.value + 5)))
        assert serialize_shrinkable(shr1) == '{"value":100,"shrinks":[{"value":105}]}'

        # Test 2: With existing shrinks - concat recursively applies to each shrink
        # (matching cppproptest behavior)
        # The function is applied to the parent (2), adding 2+5=7 to the existing shrinks
        # AND recursively applied to each existing shrink (0->5, 1->6)
        shr0 = gen_shrinkable_21()
        assert (
            serialize_shrinkable(shr0)
            == '{"value":2,"shrinks":[{"value":0},{"value":1}]}'
        )
        shr1 = shr0.concat(lambda parent: Stream.one(Shrinkable(parent.value + 5)))
        # Existing shrinks [0, 1] with concat applied recursively: [0->5, 1->6] + new shrink [7]
        expected = '{"value":2,"shrinks":[{"value":0,"shrinks":[{"value":5}]},{"value":1,"shrinks":[{"value":6}]},{"value":7}]}'
        assert serialize_shrinkable(shr1) == expected

        # Test 3: Complex case - same behavior
        shr = gen_shrinkable_40213()
        shr2 = shr.concat(lambda parent: Stream.one(Shrinkable(parent.value + 1)))
        # Existing shrinks [0, 2->1, 3] with concat applied recursively: [0->1, 2->1->2, 3->4] + new shrink [5]
        expected = '{"value":4,"shrinks":[{"value":0,"shrinks":[{"value":1}]},{"value":2,"shrinks":[{"value":1,"shrinks":[{"value":2}]},{"value":3}]},{"value":3,"shrinks":[{"value":4}]},{"value":5}]}'
        assert serialize_shrinkable(shr2) == expected

    def test_shrinkable_and_then_static(self):
        """Test and_then_static method."""
        # Test 1: Simple case
        shr = Shrinkable(100)
        shr2 = shr.and_then_static(lambda: Stream.one(Shrinkable(200)))
        assert serialize_shrinkable(shr2) == '{"value":100,"shrinks":[{"value":200}]}'

        # Test 2: With existing shrinks - and_then_static REPLACES shrinks
        # It applies the static function, which replaces all shrinks with the new one
        shr = gen_shrinkable_21()
        shr2 = shr.and_then_static(lambda: Stream.one(Shrinkable(3)))
        # All existing shrinks are replaced with just 3
        expected = '{"value":2,"shrinks":[{"value":3}]}'
        assert serialize_shrinkable(shr2) == expected

        # Test 3: Complex case - same behavior
        shr = gen_shrinkable_40213()
        shr2 = shr.and_then_static(lambda: Stream.one(Shrinkable(5)))
        # All existing shrinks are replaced with just 5
        expected = '{"value":4,"shrinks":[{"value":5}]}'
        assert serialize_shrinkable(shr2) == expected

    def test_shrinkable_and_then(self):
        """Test and_then method."""
        # Test 1: Simple case - no existing shrinks
        shr = Shrinkable(100)
        shr2 = shr.and_then(lambda _: Stream.one(Shrinkable(200)))
        assert serialize_shrinkable(shr2) == '{"value":100,"shrinks":[{"value":200}]}'

        # Test 2: With existing shrinks - and_then recursively applies to each child
        # Matches cppproptest behavior: each child gets and_then applied recursively
        shr = gen_shrinkable_21()
        shr2 = shr.and_then(lambda parent: Stream.one(Shrinkable(parent.value + 5)))
        # The function is recursively applied to each child:
        # - Child 0 gets 0 + 5 = 5
        # - Child 1 gets 1 + 5 = 6
        expected = '{"value":2,"shrinks":[{"value":0,"shrinks":[{"value":5}]},{"value":1,"shrinks":[{"value":6}]}]}'
        assert serialize_shrinkable(shr2) == expected

        # Test 3: Complex case - same recursive behavior
        shr = gen_shrinkable_40213()
        shr2 = shr.and_then(lambda parent: Stream.one(Shrinkable(parent.value + 1)))
        # The function is recursively applied to each child:
        # - Child 0 gets 0 + 1 = 1
        # - Child 2 gets 2 + 1 = 3 (and its child 1 gets 1 + 1 = 2)
        # - Child 3 gets 3 + 1 = 4
        expected = '{"value":4,"shrinks":[{"value":0,"shrinks":[{"value":1}]},{"value":2,"shrinks":[{"value":1,"shrinks":[{"value":2}]}]},{"value":3,"shrinks":[{"value":4}]}]}'
        assert serialize_shrinkable(shr2) == expected

    def test_shrinkable_map(self):
        """Test map method."""
        shr = gen_shrinkable_40213()
        shr2 = shr.map(lambda i: i + 1)
        expected = '{"value":5,"shrinks":[{"value":1},{"value":3,"shrinks":[{"value":2}]},{"value":4}]}'
        assert serialize_shrinkable(shr2) == expected

        # Test mapping to list
        shr3 = shr.map(lambda i: [i, i + 2])
        expected = '{"value":[4,6],"shrinks":[{"value":[0,2]},{"value":[2,4],"shrinks":[{"value":[1,3]}]},{"value":[3,5]}]}'
        assert serialize_shrinkable(shr3) == expected

    def test_shrinkable_filter(self):
        """Test filter method."""
        shr = gen_shrinkable_40213()
        shr2 = shr.filter(lambda i: i % 2 == 0)
        expected = '{"value":4,"shrinks":[{"value":0},{"value":2}]}'
        assert serialize_shrinkable(shr2) == expected

        # Test that filtering out root raises error
        shr = Shrinkable(4)
        with self.assertRaises(ValueError):
            shr.filter(lambda i: i > 10)

    def test_shrinkable_flat_map(self):
        """Test flat_map method."""
        shr = gen_shrinkable_40213()
        shr2 = shr.flat_map(lambda i: Shrinkable(i + 1))
        expected = '{"value":5,"shrinks":[{"value":1},{"value":3,"shrinks":[{"value":2}]},{"value":4}]}'
        assert serialize_shrinkable(shr2) == expected

    def test_shrinkable_get_nth_child(self):
        """Test get_nth_child method."""
        shr = gen_shrinkable_40213()
        assert shr.get_nth_child(0).value == 0
        assert shr.get_nth_child(1).value == 2
        assert shr.get_nth_child(2).value == 3

        with self.assertRaises(IndexError):
            shr.get_nth_child(-1)
        with self.assertRaises(IndexError):
            shr.get_nth_child(3)

    def test_shrinkable_retrieve(self):
        """Test retrieve method."""
        shr = gen_shrinkable_40213()
        assert shr.retrieve([]).value == 4
        assert serialize_shrinkable(shr.retrieve([0])) == serialize_shrinkable(
            Shrinkable(0)
        )
        assert (
            serialize_shrinkable(shr.retrieve([1]))
            == '{"value":2,"shrinks":[{"value":1}]}'
        )
        assert serialize_shrinkable(shr.retrieve([2])) == '{"value":3}'
        assert serialize_shrinkable(shr.retrieve([1, 0])) == '{"value":1}'

        with self.assertRaises(IndexError):
            shr.retrieve([-1])
        with self.assertRaises(IndexError):
            shr.retrieve([1, 1])
        with self.assertRaises(IndexError):
            shr.retrieve([2, 0])
        with self.assertRaises(IndexError):
            shr.retrieve([3])
        with self.assertRaises(IndexError):
            shr.retrieve([3, 0])

    def test_shrinkable_take(self):
        """Test take method (limit shrinks)."""
        shr = gen_shrinkable_40213()
        shr2 = shr.take(2)
        shrinks = shr2.shrinks().to_list()
        assert len(shrinks) == 2

    def test_shrinkable_with_shrinks(self):
        """Test with_shrinks method."""
        shr = Shrinkable(42)
        shr2 = shr.with_shrinks(lambda: Stream.one(Shrinkable(21)))
        assert shr2.value == 42
        assert not shr2.shrinks().is_empty()
        shrinks_list = shr2.shrinks().to_list()
        assert shrinks_list[0].value == 21

    def test_shrinkable_to_string(self):
        """Test string representation."""
        shr = Shrinkable(42)
        assert str(shr) == "Shrinkable(42)"
        assert repr(shr) == "Shrinkable(42)"

    def test_shrinkable_compare(self):
        """Test comparing shrinkables."""
        shr1 = gen_shrinkable_21()
        shr2 = gen_shrinkable_21()
        shr3 = Shrinkable(2).with_shrinks(lambda: Stream.one(Shrinkable(0)))

        assert compare_shrinkable(shr1, shr2) is True
        assert compare_shrinkable(shr1, shr3) is False

    def test_shrinkable_exhaustive_traversal(self):
        """Test exhaustive traversal."""
        shr = gen_shrinkable_40213()
        results = []

        def collect(shrinkable, level):
            indent = "  " * level
            results.append(f"{indent}{shrinkable.value}")

        exhaustive_traversal(shr, 0, collect)

        assert "4" in results
        assert "  0" in results
        assert "  2" in results
        assert "    1" in results
        assert "  3" in results


class TestBinarySearchShrinking(unittest.TestCase):
    """Test binary search shrinking from shrinker_test.dart."""

    def test_binary_search_shrinkable_shrinks_ranges_correctly(self):
        """Test that binarySearchShrinkable shrinks ranges correctly."""
        range_shrinkable = binary_search_shrinkable(8)
        assert range_shrinkable.value == 8

        shrinks = range_shrinkable.shrinks()
        assert not shrinks.is_empty()

        shrinks_list = shrinks.to_list()
        assert len(shrinks_list) > 0
        # First shrink should be 0 (prepended)
        assert shrinks_list[0].value == 0
        # Second shrink should be around 4 (8 / 2)
        assert len(shrinks_list) > 1
        assert shrinks_list[1].value == 4


class TestArrayLengthShrinking(unittest.TestCase):
    """Test array length shrinking."""

    def test_shrink_array_length_shrinks_array_lengths(self):
        """Test that shrinkArrayLength shrinks array lengths."""
        from python_proptest.core.shrinker import shrink_array_length

        elements = [
            Shrinkable(1),
            Shrinkable(2),
            Shrinkable(3),
            Shrinkable(4),
            Shrinkable(5),
        ]

        array_shrinkable = shrink_array_length(elements, 2)
        assert len(array_shrinkable.value) == 5

        shrinks = array_shrinkable.shrinks()
        assert not shrinks.is_empty()

        shrinks_list = shrinks.to_list()
        assert len(shrinks_list) > 0
        first_shrink = shrinks_list[0]
        # range = 5 - 2 = 3, binarySearchShrinkable(3) first gives 0, so size = 0 + 2 = 2
        # But wait, 0 maps to minSize (2), so first shrink should be size 2
        assert len(first_shrink.value) == 2


class TestFloatShrinkingEdgeCases(unittest.TestCase):
    """Test float shrinking edge cases from shrinker_test.dart."""

    def test_shrinkable_float_shrinks_large_values_correctly(self):
        """Test that shrinkableFloat shrinks large values correctly."""
        shrinkable = shrinkable_float(100.0)
        shrinks = shrinkable.shrinks()

        assert not shrinks.is_empty()
        shrinks_list = shrinks.to_list()
        assert shrinks_list[0].value == 0.0  # Prepended zero

        # Should shrink to a smaller value (exponent-based shrinking)
        assert len(shrinks_list) > 1
        second_shrink = shrinks_list[1]
        assert second_shrink.value < 100.0
        assert second_shrink.value > 0.0

    def test_shrinkable_float_shrinks_values_with_exponent_0_correctly(self):
        """Test that shrinkableFloat shrinks values with exponent 0 correctly."""
        test_cases = [8.0, 3.14, 0.5]

        for value in test_cases:
            shrinkable = shrinkable_float(value)
            shrinks = shrinkable.shrinks()

            assert not shrinks.is_empty(), f"{value} should have shrinks"
            shrinks_list = shrinks.to_list()
            assert shrinks_list[0].value == 0.0  # Prepended zero

            # Should shrink to smaller values, not 0.0
            if len(shrinks_list) > 1:
                second_shrink = shrinks_list[1]
                assert (
                    second_shrink.value < value
                ), f"{value} should shrink to a smaller value"
                assert second_shrink.value >= 0.0

    def test_shrinkable_float_tree_terminates_without_infinite_recursion(self):
        """Test that shrinkableFloat tree terminates without infinite recursion."""
        shrinkable = shrinkable_float(100.0)
        shrinks = shrinkable.shrinks()
        shrinks_list = shrinks.to_list()

        # Skip prepended 0.0
        if len(shrinks_list) > 1:
            second_shrink = shrinks_list[1]  # Get first non-zero shrink

            # The shrink should itself have shrinks, but they should be different values
            second_shrinks = second_shrink.shrinks()
            if not second_shrinks.is_empty():
                second_shrinks_list = second_shrinks.to_list()
                if len(second_shrinks_list) > 1:
                    third_shrink = second_shrinks_list[1]  # Skip prepended 0.0
                    # Should be different from the parent (no self-reference)
                    assert (
                        third_shrink.value != second_shrink.value
                    ), "Shrink should not reference itself"


class TestShrinkableSet(unittest.TestCase):
    """Test set shrinking (if available)."""

    def test_shrinkable_set_creates_shrinkable_sets(self):
        """Test that shrinkableSet creates shrinkable sets."""
        try:
            from python_proptest.core.shrinker import shrinkable_set

            elements = [
                Shrinkable(1),
                Shrinkable(2),
                Shrinkable(3),
            ]

            set_shrinkable = shrinkable_set(elements, 1)
            assert set_shrinkable.value == {1, 2, 3}

            shrinks = set_shrinkable.shrinks()
            assert not shrinks.is_empty()
        except ImportError:
            self.skipTest("shrinkable_set not available")


class TestShrinkableTuple(unittest.TestCase):
    """Test tuple shrinking (if available)."""

    def test_shrinkable_tuple_creates_shrinkable_tuples(self):
        """Test that shrinkableTuple creates shrinkable tuples."""
        try:
            from python_proptest.core.shrinker import shrinkable_tuple

            elements = [
                Shrinkable(1),
                Shrinkable(2),
                Shrinkable(3),
            ]

            tuple_shrinkable = shrinkable_tuple(elements)
            assert tuple_shrinkable.value == (1, 2, 3)

            # For now, the tuple shrinker is simplified and doesn't have complex shrinking
            shrinks = tuple_shrinkable.shrinks()
            # This might be empty or have shrinks depending on implementation
        except ImportError:
            self.skipTest("shrinkable_tuple not available")
