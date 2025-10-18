"""
Library utility tests ported from TypeScript.

These tests verify that utility classes (Option, Either, Try) work correctly.
"""

import random
import unittest

from python_proptest import (
    Either,
    Failure,
    Left,
    None_,
    Option,
    Right,
    Some,
    Success,
    Try,
    attempt,
    none,
)


class TestOption(unittest.TestCase):
    """Test Option functionality."""

    def test_some_creation(self):
        """Test Some creation and basic operations."""
        some = Some(42)
        assert some.is_some()
        assert not some.is_none()
        assert some.get() == 42
        assert some.get_or_else(0) == 42
        assert str(some) == "Some(42)"

    def test_none_creation(self):
        """Test None creation and basic operations."""
        none_val = None_()
        assert not none_val.is_some()
        assert none_val.is_none()

        with self.assertRaises(ValueError):
            none_val.get()

        assert none_val.get_or_else(42) == 42
        assert str(none_val) == "None"

    def test_option_map(self):
        """Test Option mapping."""
        some = Some(5)
        mapped = some.map(lambda x: x * 2)
        assert isinstance(mapped, Some)
        assert mapped.get() == 10

        none_val = None_()
        mapped_none = none_val.map(lambda x: x * 2)
        assert isinstance(mapped_none, None_)

    def test_option_flat_map(self):
        """Test Option flat mapping."""
        some = Some(5)
        flat_mapped = some.flat_map(lambda x: Some(x * 2))
        assert isinstance(flat_mapped, Some)
        assert flat_mapped.get() == 10

        flat_mapped_none = some.flat_map(lambda x: None_())
        assert isinstance(flat_mapped_none, None_)

        none_val = None_()
        flat_mapped_from_none = none_val.flat_map(lambda x: Some(x * 2))
        assert isinstance(flat_mapped_from_none, None_)

    def test_option_filter(self):
        """Test Option filtering."""
        some = Some(5)
        filtered = some.filter(lambda x: x > 3)
        assert isinstance(filtered, Some)
        assert filtered.get() == 5

        filtered_false = some.filter(lambda x: x < 3)
        assert isinstance(filtered_false, None_)

        none_val = None_()
        filtered_none = none_val.filter(lambda x: x > 3)
        assert isinstance(filtered_none, None_)

    def test_option_equality(self):
        """Test Option equality."""
        some1 = Some(42)
        some2 = Some(42)
        some3 = Some(43)
        none_val = None_()

        assert some1 == some2
        assert some1 != some3
        assert some1 != none_val
        assert none_val == None_()


class TestEither(unittest.TestCase):
    """Test Either functionality."""

    def test_left_creation(self):
        """Test Left creation and basic operations."""
        left = Left("error")
        assert left.is_left()
        assert not left.is_right()
        assert left.get_left() == "error"
        assert left.get_or_else("default") == "default"

        with self.assertRaises(ValueError):
            left.get_right()

        assert str(left) == "Left('error')"

    def test_right_creation(self):
        """Test Right creation and basic operations."""
        right = Right(42)
        assert not right.is_left()
        assert right.is_right()
        assert right.get_right() == 42
        assert right.get_or_else(0) == 42

        with self.assertRaises(ValueError):
            right.get_left()

        assert str(right) == "Right(42)"

    def test_either_map(self):
        """Test Either mapping."""
        right = Right(5)
        mapped = right.map(lambda x: x * 2)
        assert isinstance(mapped, Right)
        assert mapped.get_right() == 10

        left = Left("error")
        mapped_left = left.map(lambda x: x * 2)
        assert isinstance(mapped_left, Left)
        assert mapped_left.get_left() == "error"

    def test_either_map_left(self):
        """Test Either left mapping."""
        left = Left("error")
        mapped = left.map_left(lambda x: x.upper())
        assert isinstance(mapped, Left)
        assert mapped.get_left() == "ERROR"

        right = Right(42)
        mapped_right = right.map_left(lambda x: x.upper())
        assert isinstance(mapped_right, Right)
        assert mapped_right.get_right() == 42

    def test_either_flat_map(self):
        """Test Either flat mapping."""
        right = Right(5)
        flat_mapped = right.flat_map(lambda x: Right(x * 2))
        assert isinstance(flat_mapped, Right)
        assert flat_mapped.get_right() == 10

        flat_mapped_left = right.flat_map(lambda x: Left("error"))
        assert isinstance(flat_mapped_left, Left)
        assert flat_mapped_left.get_left() == "error"

        left = Left("error")
        flat_mapped_from_left = left.flat_map(lambda x: Right(x * 2))
        assert isinstance(flat_mapped_from_left, Left)
        assert flat_mapped_from_left.get_left() == "error"

    def test_either_equality(self):
        """Test Either equality."""
        left1 = Left("error")
        left2 = Left("error")
        left3 = Left("different")
        right = Right(42)

        assert left1 == left2
        assert left1 != left3
        assert left1 != right
        assert right == Right(42)


class TestTry(unittest.TestCase):
    """Test Try functionality."""

    def test_success_creation(self):
        """Test Success creation and basic operations."""
        success = Success(42)
        assert success.is_success()
        assert not success.is_failure()
        assert success.get() == 42
        assert success.get_or_else(0) == 42

        with self.assertRaises(ValueError):
            success.get_exception()

        assert str(success) == "Success(42)"

    def test_failure_creation(self):
        """Test Failure creation and basic operations."""
        exception = ValueError("test error")
        failure = Failure(exception)
        assert not failure.is_success()
        assert failure.is_failure()
        assert failure.get_exception() == exception
        assert failure.get_or_else(42) == 42

        with self.assertRaises(ValueError):
            failure.get()

        assert str(failure) == "Failure(ValueError('test error'))"

    def test_try_map(self):
        """Test Try mapping."""
        success = Success(5)
        mapped = success.map(lambda x: x * 2)
        assert isinstance(mapped, Success)
        assert mapped.get() == 10

        # Test mapping that throws
        mapped_error = success.map(lambda x: 1 / 0)
        assert isinstance(mapped_error, Failure)

        failure = Failure(ValueError("error"))
        mapped_failure = failure.map(lambda x: x * 2)
        assert isinstance(mapped_failure, Failure)

    def test_try_flat_map(self):
        """Test Try flat mapping."""
        success = Success(5)
        flat_mapped = success.flat_map(lambda x: Success(x * 2))
        assert isinstance(flat_mapped, Success)
        assert flat_mapped.get() == 10

        flat_mapped_failure = success.flat_map(lambda x: Failure(ValueError("error")))
        assert isinstance(flat_mapped_failure, Failure)

        failure = Failure(ValueError("error"))
        flat_mapped_from_failure = failure.flat_map(lambda x: Success(x * 2))
        assert isinstance(flat_mapped_from_failure, Failure)

    def test_try_recover(self):
        """Test Try recovery."""
        failure = Failure(ValueError("error"))
        recovered = failure.recover(lambda e: 42)
        assert isinstance(recovered, Success)
        assert recovered.get() == 42

        success = Success(5)
        recovered_success = success.recover(lambda e: 42)
        assert isinstance(recovered_success, Success)
        assert recovered_success.get() == 5

    def test_try_filter(self):
        """Test Try filtering."""
        success = Success(5)
        filtered = success.filter(lambda x: x > 3)
        assert isinstance(filtered, Success)
        assert filtered.get() == 5

        filtered_false = success.filter(lambda x: x < 3)
        assert isinstance(filtered_false, Failure)

        failure = Failure(ValueError("error"))
        filtered_failure = failure.filter(lambda x: x > 3)
        assert isinstance(filtered_failure, Failure)

    def test_attempt_function(self):
        """Test the attempt function."""
        # Test successful function
        result = attempt(lambda: 42)
        assert isinstance(result, Success)
        assert result.get() == 42

        # Test failing function
        result = attempt(lambda: 1 / 0)
        assert isinstance(result, Failure)
        assert isinstance(result.get_exception(), ZeroDivisionError)

    def test_try_equality(self):
        """Test Try equality."""
        success1 = Success(42)
        success2 = Success(42)
        success3 = Success(43)
        failure = Failure(ValueError("error"))

        assert success1 == success2
        assert success1 != success3
        assert success1 != failure
        assert failure == Failure(ValueError("error"))


class TestRandom(unittest.TestCase):
    """Test random number generation."""

    def test_random_next(self):
        """Test random number generation."""
        rng = random.Random()
        value = rng.random()
        assert isinstance(value, float)
        assert 0 <= value < 1


class TestJest(unittest.TestCase):
    """Test assertion functionality."""

    def test_expect(self):
        """Test assertion behavior."""
        a = 6
        try:
            assert 5 == a
        except AssertionError:
            # This is expected to fail
            pass
        else:
            pytest.fail("Expected assertion to fail")


class Error1(Exception):
    """Custom error class 1."""

    def __init__(self, name: str):
        super().__init__(name)
        self.name = name
        self.message = "Error1"


class Error2(Error1):
    """Custom error class 2."""

    def __init__(self, name: str):
        super().__init__(name)
        self.message = "Error2"


class TestError(unittest.TestCase):
    """Test error handling."""

    def test_error_type(self):
        """Test error type checking."""
        try:
            raise Error1("hello")
        except Error1 as e:
            assert isinstance(e, Error1)
            assert e.name == "hello"
            assert e.message == "Error1"

    def test_error_inheritance(self):
        """Test error inheritance."""
        try:
            raise Error2("world")
        except Error2 as e:
            assert isinstance(e, Error2)
            assert isinstance(e, Error1)  # Should be instance of parent too
            assert e.name == "world"
            assert e.message == "Error2"
