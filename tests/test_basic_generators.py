"""
Tests for basic generators.
"""

import unittest

from python_proptest import (
    Gen,
    dictionaries,
    floats,
    for_all,
    integers,
    just,
    lists,
    one_of,
    run_for_all,
    text,
)


class TestIntGenerator(unittest.TestCase):
    """Test integer generator."""

    def test_int_generator_basic(self):
        """Test basic integer generation."""
        result = run_for_all(
            lambda x: isinstance(x, int),
            Gen.int(min_value=0, max_value=100),
            num_runs=50,
        )
        assert result is True

    def test_int_generator_range(self):
        """Test integer generator respects range constraints."""
        result = run_for_all(
            lambda x: 0 <= x <= 100, Gen.int(min_value=0, max_value=100), num_runs=50
        )
        assert result is True

    def test_int_generator_negative_range(self):
        """Test integer generator with negative range."""
        result = run_for_all(
            lambda x: -50 <= x <= 50, Gen.int(min_value=-50, max_value=50), num_runs=50
        )
        assert result is True


class TestStringGenerator(unittest.TestCase):
    """Test string generator."""

    def test_string_generator_basic(self):
        """Test basic string generation."""
        result = run_for_all(
            lambda s: isinstance(s, str),
            Gen.str(min_length=0, max_length=10),
            num_runs=50,
        )
        assert result is True

    def test_string_generator_length(self):
        """Test string generator respects length constraints."""
        result = run_for_all(
            lambda s: 0 <= len(s) <= 10,
            Gen.str(min_length=0, max_length=10),
            num_runs=50,
        )
        assert result is True

    def test_string_generator_charset(self):
        """Test string generator with custom charset."""

        @for_all(Gen.str(min_length=0, max_length=5, charset="abc"))
        def test_charset(self, s: str):
            assert all(c in "abc" for c in s)

        test_charset(self)


class TestBoolGenerator(unittest.TestCase):
    """Test boolean generator."""

    def test_bool_generator_basic(self):
        """Test basic boolean generation."""
        result = run_for_all(lambda b: isinstance(b, bool), Gen.bool(), num_runs=50)
        assert result is True


class TestFloatGenerator(unittest.TestCase):
    """Test float generator."""

    def test_float_generator_basic(self):
        """Test basic float generation."""
        result = run_for_all(
            lambda f: isinstance(f, float),
            Gen.float(min_value=0.0, max_value=100.0),
            num_runs=50,
        )
        assert result is True

    def test_float_generator_range(self):
        """Test float generator respects range constraints."""
        result = run_for_all(
            lambda f: 0.0 <= f <= 100.0,
            Gen.float(min_value=0.0, max_value=100.0),
            num_runs=50,
        )
        assert result is True


class TestListGenerator(unittest.TestCase):
    """Test list generator."""

    def test_list_generator_basic(self):
        """Test basic list generation."""
        result = run_for_all(
            lambda lst: isinstance(lst, list),
            Gen.list(Gen.int(min_value=0, max_value=10)),
            num_runs=50,
        )
        assert result is True

    def test_list_generator_length(self):
        """Test list generator respects length constraints."""
        result = run_for_all(
            lambda lst: 0 <= len(lst) <= 5,
            Gen.list(Gen.int(min_value=0, max_value=10), min_length=0, max_length=5),
            num_runs=50,
        )
        assert result is True

    def test_list_generator_elements(self):
        """Test list generator element types."""
        result = run_for_all(
            lambda lst: all(isinstance(x, int) for x in lst),
            Gen.list(Gen.int(min_value=0, max_value=10)),
            num_runs=50,
        )
        assert result is True


class TestDictGenerator(unittest.TestCase):
    """Test dictionary generator."""

    def test_dict_generator_basic(self):
        """Test basic dictionary generation."""
        result = run_for_all(
            lambda d: isinstance(d, dict),
            Gen.dict(
                Gen.str(min_length=1, max_length=3), Gen.int(min_value=0, max_value=10)
            ),
            num_runs=50,
        )
        assert result is True

    def test_dict_generator_size(self):
        """Test dictionary generator respects size constraints."""
        result = run_for_all(
            lambda d: 0 <= len(d) <= 3,
            Gen.dict(
                Gen.str(min_length=1, max_length=2),
                Gen.int(min_value=0, max_value=5),
                min_size=0,
                max_size=3,
            ),
            num_runs=50,
        )
        assert result is True


class TestCombinators(unittest.TestCase):
    """Test generator combinators."""

    @for_all(
        Gen.one_of(
            Gen.int(min_value=0, max_value=10), Gen.str(min_length=1, max_length=3)
        )
    )
    def test_one_of_generator(self, x):
        """Test one_of combinator."""
        assert isinstance(x, (int, str))

    @for_all(Gen.just(42))
    def test_just_generator(self, x: int):
        """Test just combinator."""
        assert x == 42

    @for_all(Gen.int(min_value=1, max_value=10).map(lambda n: f"Number: {n}"))
    def test_map_generator(self, x: str):
        """Test map combinator."""
        assert isinstance(x, str) and x.startswith("Number: ")

    @for_all(Gen.int(min_value=0, max_value=100).filter(lambda x: x % 2 == 0))
    def test_filter_generator(self, x: int):
        """Test filter combinator."""
        assert x % 2 == 0
