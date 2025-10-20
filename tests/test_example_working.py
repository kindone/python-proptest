"""Simple tests to verify that @example decorator is working correctly."""

import unittest
from python_proptest import Gen, for_all, example


class TestExampleWorking(unittest.TestCase):
    """Test that @example decorator is working correctly."""

    def test_example_failure_detection(self):
        """Test that failing examples are detected."""

        # This should fail because the example (0, "hello") violates the property
        with self.assertRaises(AssertionError):

            @for_all(Gen.int(), Gen.str())
            @example(0, "hello")  # This will fail: 0 > 0 is False
            def test_property(x: int, s: str):
                assert x > 0  # This will fail for x=0
                assert len(s) > 0

            test_property()

    def test_example_success_with_restrictive_generators(self):
        """Test that passing examples work even with restrictive generators."""

        # Use generators that only produce positive values
        @for_all(Gen.int(min_value=1), Gen.str(min_length=1))
        @example(1, "hello")  # This will pass: 1 > 0 is True
        def test_property(x: int, s: str):
            assert x > 0
            assert len(s) > 0

        # Should not raise any exception
        test_property()

    def test_example_with_simple_property(self):
        """Test examples with a simple property that always passes."""

        # This should pass because the property is always true
        @for_all(Gen.int(), Gen.str())
        @example(42, "hello")
        def test_property(x: int, s: str):
            assert isinstance(x, int)
            assert isinstance(s, str)

        # Should not raise any exception
        test_property()

    def test_example_with_bool_generator(self):
        """Test examples with boolean generator."""

        # This should pass because the property is always true
        @for_all(Gen.bool())
        @example(True)
        def test_property(b: bool):
            assert isinstance(b, bool)

        # Should not raise any exception
        test_property()

    def test_example_with_float_generator(self):
        """Test examples with float generator."""

        # This should pass because the property is always true
        @for_all(Gen.float())
        @example(3.14)
        def test_property(f: float):
            assert isinstance(f, float)

        # Should not raise any exception
        test_property()


if __name__ == "__main__":
    unittest.main()
