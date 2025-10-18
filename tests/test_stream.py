"""
Stream tests ported from TypeScript.

These tests verify that the Stream class works correctly for lazy evaluation.
"""

import unittest

from python_proptest import Stream


class TestStream(unittest.TestCase):
    """Test Stream functionality."""

    def test_empty_stream(self):
        """Test empty stream creation."""
        stream = Stream.empty()
        assert stream.is_empty()
        assert stream.head() is None
        assert stream.tail().is_empty()
        assert str(stream) == "Stream()"

    def test_one_element_stream(self):
        """Test stream with one element."""
        stream = Stream.one(1)
        assert not stream.is_empty()
        assert stream.head() == 1
        assert stream.tail().is_empty()
        assert str(stream) == "Stream(1)"

    def test_two_element_stream(self):
        """Test stream with two elements."""
        stream = Stream.two(1, 2)
        assert not stream.is_empty()
        assert stream.head() == 1
        tail = stream.tail()
        assert not tail.is_empty()
        assert tail.head() == 2
        assert tail.tail().is_empty()
        assert str(stream) == "Stream(1, 2)"

    def test_three_element_stream(self):
        """Test stream with three elements."""
        stream = Stream.three(1, 2, 3)
        assert not stream.is_empty()
        assert stream.head() == 1
        tail1 = stream.tail()
        assert tail1.head() == 2
        tail2 = tail1.tail()
        assert tail2.head() == 3
        assert tail2.tail().is_empty()
        assert str(stream) == "Stream(1, 2, 3)"

    def test_many_element_stream(self):
        """Test stream with many elements."""
        values = list(range(20))
        stream = Stream.many(values)

        # Test first 10 elements
        assert str(stream) == "Stream(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, ...)"
        assert (
            str(stream.toString(20))
            == "Stream(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19)"
        )
        assert str(stream.toString(20)) == str(stream.toString(30))

    def test_stream_filter(self):
        """Test stream filtering."""
        values = list(range(10))
        stream = Stream.many(values)
        filtered = stream.filter(lambda n: n % 2 == 0)
        assert str(filtered) == "Stream(0, 2, 4, 6, 8)"

    def test_stream_concat(self):
        """Test stream concatenation."""
        stream1 = Stream.many([0, 1, 2])
        stream2 = Stream.many([3, 4, 5])
        concatenated = stream1.concat(stream2)
        assert str(concatenated) == "Stream(0, 1, 2, 3, 4, 5)"

    def test_stream_concat_with_empty(self):
        """Test concatenating with empty stream."""
        stream = Stream.many([1, 2, 3])
        empty = Stream.empty()
        result1 = stream.concat(empty)
        result2 = empty.concat(stream)
        assert str(result1) == "Stream(1, 2, 3)"
        assert str(result2) == "Stream(1, 2, 3)"

    def test_stream_map(self):
        """Test stream mapping."""
        stream = Stream.many([1, 2, 3, 4, 5])
        mapped = stream.map(lambda x: x * 2)
        assert str(mapped) == "Stream(2, 4, 6, 8, 10)"

    def test_stream_take(self):
        """Test taking elements from stream."""
        stream = Stream.many([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        taken = stream.take(5)
        assert str(taken) == "Stream(0, 1, 2, 3, 4)"

        # Test taking more than available
        taken_all = stream.take(20)
        assert str(taken_all) == "Stream(0, 1, 2, 3, 4, 5, 6, 7, 8, 9)"

    def test_stream_to_list(self):
        """Test converting stream to list."""
        stream = Stream.many([1, 2, 3, 4, 5])
        result = stream.to_list()
        assert result == [1, 2, 3, 4, 5]

    def test_stream_iteration(self):
        """Test stream iteration."""
        stream = Stream.many([1, 2, 3, 4, 5])
        result = list(stream)
        assert result == [1, 2, 3, 4, 5]

    def test_stream_chaining(self):
        """Test chaining stream operations."""
        stream = Stream.many([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        result = stream.filter(lambda x: x % 2 == 0).map(lambda x: x * 2).take(3)
        assert str(result) == "Stream(0, 4, 8)"

    def test_empty_stream_operations(self):
        """Test operations on empty stream."""
        empty = Stream.empty()
        assert empty.filter(lambda x: True).is_empty()
        assert empty.map(lambda x: x).is_empty()
        assert empty.take(5).is_empty()
        assert empty.to_list() == []
        assert list(empty) == []

    def test_stream_with_complex_operations(self):
        """Test stream with complex operations."""
        # Create a stream, filter, map, and concatenate
        stream1 = Stream.many([1, 2, 3, 4, 5])
        stream2 = Stream.many([6, 7, 8, 9, 10])

        filtered1 = stream1.filter(lambda x: x % 2 == 1)  # [1, 3, 5]
        filtered2 = stream2.filter(lambda x: x % 2 == 0)  # [6, 8, 10]

        mapped1 = filtered1.map(lambda x: x * 2)  # [2, 6, 10]
        mapped2 = filtered2.map(lambda x: x * 3)  # [18, 24, 30]

        result = mapped1.concat(mapped2)
        assert str(result) == "Stream(2, 6, 10, 18, 24, 30)"
