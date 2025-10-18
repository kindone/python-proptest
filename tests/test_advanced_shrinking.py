"""
Tests for advanced shrinking functionality.
"""

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


class TestShrinkable(unittest.TestCase):
    """Test the enhanced Shrinkable class."""

    def test_basic_shrinkable(self):
        """Test basic Shrinkable creation."""
        shr = Shrinkable(0)
        assert shr.value == 0
        assert shr.shrinks().is_empty()

    def test_with_shrinks(self):
        """Test adding shrinking candidates."""
        from python_proptest.core.stream import Stream

        shr = Shrinkable(2).with_shrinks(
            lambda: Stream.many([Shrinkable(0), Shrinkable(1)])
        )
        assert shr.value == 2
        shrinks_list = shr.shrinks().to_list()
        assert len(shrinks_list) == 2
        assert shrinks_list[0].value == 0
        assert shrinks_list[1].value == 1

    def test_concat_static(self):
        """Test concatenating static shrinking candidates."""
        from python_proptest.core.stream import Stream

        shr = Shrinkable(100)
        shr2 = shr.concat_static(lambda: Stream.one(Shrinkable(200)))
        assert shr2.value == 100
        shrinks_list = shr2.shrinks().to_list()
        assert len(shrinks_list) == 1
        assert shrinks_list[0].value == 200

    def test_concat(self):
        """Test concatenating dependent shrinking candidates."""
        from python_proptest.core.stream import Stream

        shr = Shrinkable(100)
        shr2 = shr.concat(lambda parent: Stream.one(Shrinkable(parent.value + 5)))
        assert shr2.value == 100
        shrinks_list = shr2.shrinks().to_list()
        assert len(shrinks_list) == 1
        assert shrinks_list[0].value == 105

    def test_and_then_static(self):
        """Test replacing shrinking candidates with static ones."""
        from python_proptest.core.stream import Stream

        shr = Shrinkable(100)
        shr2 = shr.and_then_static(lambda: Stream.one(Shrinkable(200)))
        assert shr2.value == 100
        shrinks_list = shr2.shrinks().to_list()
        assert len(shrinks_list) == 1
        assert shrinks_list[0].value == 200

    def test_and_then(self):
        """Test replacing shrinking candidates with dependent ones."""
        from python_proptest.core.stream import Stream

        shr = Shrinkable(100)
        shr2 = shr.and_then(lambda parent: Stream.one(Shrinkable(parent.value + 1)))
        assert shr2.value == 100
        shrinks_list = shr2.shrinks().to_list()
        assert len(shrinks_list) == 1
        assert shrinks_list[0].value == 101

    def test_map(self):
        """Test mapping over shrinkable values."""
        from python_proptest.core.stream import Stream

        shr = Shrinkable(4).with_shrinks(
            lambda: Stream.many([Shrinkable(0), Shrinkable(2), Shrinkable(3)])
        )
        shr2 = shr.map(lambda x: x + 1)
        assert shr2.value == 5
        shrinks_list = shr2.shrinks().to_list()
        assert len(shrinks_list) == 3
        assert shrinks_list[0].value == 1
        assert shrinks_list[1].value == 3
        assert shrinks_list[2].value == 4

    def test_filter(self):
        """Test filtering shrinking candidates."""
        from python_proptest.core.stream import Stream

        shr = Shrinkable(4).with_shrinks(
            lambda: Stream.many([Shrinkable(0), Shrinkable(2), Shrinkable(3)])
        )
        shr2 = shr.filter(lambda x: x % 2 == 0)
        assert shr2.value == 4
        shrinks_list = shr2.shrinks().to_list()
        assert len(shrinks_list) == 2
        assert shrinks_list[0].value == 0
        assert shrinks_list[1].value == 2

    def test_filter_raises_on_root(self):
        """Test that filtering out the root value raises an error."""
        shr = Shrinkable(4)
        with self.assertRaises(ValueError):
            shr.filter(lambda x: x > 10)

    def test_flat_map(self):
        """Test flat mapping over shrinkable values."""
        from python_proptest.core.stream import Stream

        shr = Shrinkable(4).with_shrinks(
            lambda: Stream.many([Shrinkable(0), Shrinkable(2), Shrinkable(3)])
        )
        shr2 = shr.flat_map(lambda x: Shrinkable(x + 1))
        assert shr2.value == 5
        # The flat_map should include shrinks from the original shrinkable
        shrinks_list = shr2.shrinks().to_list()
        assert len(shrinks_list) >= 3
        # Check that the shrinks are transformed
        shrink_values = [s.value for s in shrinks_list]
        assert 1 in shrink_values  # 0 + 1
        assert 3 in shrink_values  # 2 + 1
        assert 4 in shrink_values  # 3 + 1

    def test_get_nth_child(self):
        """Test getting nth child shrinkable."""
        from python_proptest.core.stream import Stream

        shr = Shrinkable(4).with_shrinks(
            lambda: Stream.many([Shrinkable(0), Shrinkable(2), Shrinkable(3)])
        )
        assert shr.get_nth_child(0).value == 0
        assert shr.get_nth_child(1).value == 2
        assert shr.get_nth_child(2).value == 3

        with self.assertRaises(IndexError):
            shr.get_nth_child(-1)
        with self.assertRaises(IndexError):
            shr.get_nth_child(3)

    def test_retrieve(self):
        """Test retrieving shrinkable by path."""
        from python_proptest.core.stream import Stream

        shr = Shrinkable(4).with_shrinks(
            lambda: Stream.many(
                [
                    Shrinkable(0),
                    Shrinkable(2).with_shrinks(lambda: Stream.one(Shrinkable(1))),
                    Shrinkable(3),
                ]
            )
        )

        assert shr.retrieve([]).value == 4
        assert shr.retrieve([0]).value == 0
        assert shr.retrieve([1]).value == 2
        assert shr.retrieve([2]).value == 3
        assert shr.retrieve([1, 0]).value == 1


class TestBinarySearchShrinking(unittest.TestCase):
    """Test binary search shrinking algorithm."""

    def test_binary_search_zero(self):
        """Test that 0 cannot shrink further."""
        shr = binary_search_shrinkable(0)
        assert shr.value == 0
        assert shr.shrinks().is_empty()

    def test_binary_search_positive(self):
        """Test binary search shrinking for positive numbers."""
        shr = binary_search_shrinkable(4)
        assert shr.value == 4
        shrinks_list = shr.shrinks().to_list()
        assert len(shrinks_list) > 0
        # Should include 0 as first shrink
        assert shrinks_list[0].value == 0

    def test_binary_search_negative(self):
        """Test binary search shrinking for negative numbers."""
        shr = binary_search_shrinkable(-4)
        assert shr.value == -4
        shrinks_list = shr.shrinks().to_list()
        assert len(shrinks_list) > 0
        # Should include 0 as first shrink
        assert shrinks_list[0].value == 0

    def test_binary_search_small_positive(self):
        """Test binary search shrinking for small positive numbers."""
        shr = binary_search_shrinkable(2)
        assert shr.value == 2
        shrinks_list = shr.shrinks().to_list()
        assert len(shrinks_list) > 0
        assert shrinks_list[0].value == 0

    def test_binary_search_small_negative(self):
        """Test binary search shrinking for small negative numbers."""
        shr = binary_search_shrinkable(-2)
        assert shr.value == -2
        shrinks_list = shr.shrinks().to_list()
        assert len(shrinks_list) > 0
        assert shrinks_list[0].value == 0


class TestElementWiseShrinking(unittest.TestCase):
    """Test element-wise shrinking algorithm."""

    def test_shrink_element_wise_empty(self):
        """Test element-wise shrinking with empty array."""
        shr = Shrinkable([])
        result = shrink_element_wise(shr, 0, 0)
        assert result.is_empty()

    def test_shrink_element_wise_single_element(self):
        """Test element-wise shrinking with single element."""
        from python_proptest.core.stream import Stream

        elem = Shrinkable(5).with_shrinks(
            lambda: Stream.many([Shrinkable(3), Shrinkable(4)])
        )
        shr = Shrinkable([elem])
        result = shrink_element_wise(shr, 0, 0)
        result_list = result.to_list()
        assert len(result_list) == 2
        assert result_list[0].value[0].value == 3
        assert result_list[1].value[0].value == 4

    def test_shrink_element_wise_multiple_elements(self):
        """Test element-wise shrinking with multiple elements."""
        from python_proptest.core.stream import Stream

        elem1 = Shrinkable(5).with_shrinks(lambda: Stream.one(Shrinkable(3)))
        elem2 = Shrinkable(7).with_shrinks(lambda: Stream.one(Shrinkable(6)))
        shr = Shrinkable([elem1, elem2])
        result = shrink_element_wise(shr, 0, 0)
        result_list = result.to_list()
        assert len(result_list) == 2
        assert result_list[0].value[0].value == 3
        assert result_list[0].value[1].value == 7
        assert result_list[1].value[0].value == 5
        assert result_list[1].value[1].value == 6


class TestMembershipWiseShrinking(unittest.TestCase):
    """Test membership-wise shrinking algorithm."""

    def test_shrink_membership_wise_empty(self):
        """Test membership-wise shrinking with empty array."""
        result = shrink_membership_wise([], 0)
        assert result.value == []
        assert result.shrinks().is_empty()

    def test_shrink_membership_wise_single_element(self):
        """Test membership-wise shrinking with single element."""
        elem = Shrinkable(5)
        result = shrink_membership_wise([elem], 0)
        assert len(result.value) == 1
        assert result.value[0].value == 5
        # Should have empty array as shrink
        shrinks_list = result.shrinks().to_list()
        assert len(shrinks_list) > 0
        assert shrinks_list[0].value == []

    def test_shrink_membership_wise_multiple_elements(self):
        """Test membership-wise shrinking with multiple elements."""
        elem1 = Shrinkable(5)
        elem2 = Shrinkable(7)
        elem3 = Shrinkable(9)
        result = shrink_membership_wise([elem1, elem2, elem3], 1)
        assert len(result.value) == 3
        # Should have shrinks with fewer elements
        shrinks_list = result.shrinks().to_list()
        assert len(shrinks_list) > 0
        # Check that shrinks respect minimum size
        for shrink in shrinks_list:
            assert len(shrink.value) >= 1


class TestShrinkableArray(unittest.TestCase):
    """Test the shrinkable array function."""

    def test_shrinkable_array_basic(self):
        """Test basic shrinkable array creation."""
        elem1 = Shrinkable(5)
        elem2 = Shrinkable(7)
        result = shrinkable_array([elem1, elem2], 0)
        assert result.value == [5, 7]
        shrinks_list = result.shrinks().to_list()
        assert len(shrinks_list) > 0

    def test_shrinkable_array_membership_only(self):
        """Test shrinkable array with membership shrinking only."""
        elem1 = Shrinkable(5)
        elem2 = Shrinkable(7)
        result = shrinkable_array(
            [elem1, elem2], 0, membership_wise=True, element_wise=False
        )
        assert result.value == [5, 7]
        # Should have shrinks with fewer elements
        shrinks_list = result.shrinks().to_list()
        assert len(shrinks_list) > 0

    def test_shrinkable_array_element_wise_only(self):
        """Test shrinkable array with element-wise shrinking only."""
        from python_proptest.core.stream import Stream

        elem1 = Shrinkable(5).with_shrinks(lambda: Stream.one(Shrinkable(3)))
        elem2 = Shrinkable(7).with_shrinks(lambda: Stream.one(Shrinkable(6)))
        result = shrinkable_array(
            [elem1, elem2], 2, membership_wise=False, element_wise=True
        )
        assert result.value == [5, 7]
        # Should have shrinks with shrunk elements
        shrinks_list = result.shrinks().to_list()
        assert len(shrinks_list) > 0

    def test_shrinkable_array_both(self):
        """Test shrinkable array with both membership and element-wise shrinking."""
        from python_proptest.core.stream import Stream

        elem1 = Shrinkable(5).with_shrinks(lambda: Stream.one(Shrinkable(3)))
        elem2 = Shrinkable(7).with_shrinks(lambda: Stream.one(Shrinkable(6)))
        result = shrinkable_array(
            [elem1, elem2], 0, membership_wise=True, element_wise=True
        )
        assert result.value == [5, 7]
        # Should have shrinks from both strategies
        shrinks_list = result.shrinks().to_list()
        assert len(shrinks_list) > 0


class TestShrinkableBoolean(unittest.TestCase):
    """Test boolean shrinking."""

    def test_shrinkable_boolean_true(self):
        """Test shrinking true to false."""
        shr = shrinkable_boolean(True)
        assert shr.value is True
        shrinks_list = shr.shrinks().to_list()
        assert len(shrinks_list) == 1
        assert shrinks_list[0].value is False

    def test_shrinkable_boolean_false(self):
        """Test that false cannot shrink further."""
        shr = shrinkable_boolean(False)
        assert shr.value is False
        assert shr.shrinks().is_empty()


class TestShrinkableFloat(unittest.TestCase):
    """Test float shrinking."""

    def test_shrinkable_float_zero(self):
        """Test that 0.0 cannot shrink further."""
        shr = shrinkable_float(0.0)
        assert shr.value == 0.0
        assert shr.shrinks().is_empty()

    def test_shrinkable_float_positive(self):
        """Test shrinking positive floats."""
        shr = shrinkable_float(4.0)
        assert shr.value == 4.0
        shrinks_list = shr.shrinks().to_list()
        assert len(shrinks_list) > 0
        # Should include 0.0 as first shrink
        assert shrinks_list[0].value == 0.0

    def test_shrinkable_float_negative(self):
        """Test shrinking negative floats."""
        shr = shrinkable_float(-4.0)
        assert shr.value == -4.0
        shrinks_list = shr.shrinks().to_list()
        assert len(shrinks_list) > 0
        # Should include 0.0 as first shrink
        assert shrinks_list[0].value == 0.0

    def test_shrinkable_float_nan(self):
        """Test shrinking NaN to 0.0."""
        shr = shrinkable_float(float("nan"))
        assert shr.value != shr.value  # NaN != NaN
        shrinks_list = shr.shrinks().to_list()
        assert len(shrinks_list) == 1
        assert shrinks_list[0].value == 0.0

    def test_shrinkable_float_infinity(self):
        """Test shrinking infinity."""
        shr = shrinkable_float(float("inf"))
        assert shr.value == float("inf")
        shrinks_list = shr.shrinks().to_list()
        assert len(shrinks_list) > 0

    def test_shrinkable_float_negative_infinity(self):
        """Test shrinking negative infinity."""
        shr = shrinkable_float(float("-inf"))
        assert shr.value == float("-inf")
        shrinks_list = shr.shrinks().to_list()
        assert len(shrinks_list) > 0
