"""Test named arguments in @example decorator."""

import unittest

from python_proptest import Gen, example, for_all


class TestNamedExamples(unittest.TestCase):
    """Test @example decorator with named arguments."""

    def test_positional_examples_still_work(self):
        """Test that legacy positional examples continue to work."""
        call_count = []

        @for_all(Gen.int(), Gen.str())
        @example(42, "hello")
        @example(0, "")
        def test_property(self, x: int, s: str):
            call_count.append((x, s))
            self.assertIsInstance(x, int)
            self.assertIsInstance(s, str)

        test_property(self)

        # Verify examples were run
        self.assertIn((42, "hello"), call_count)
        self.assertIn((0, ""), call_count)

    def test_named_examples(self):
        """Test that named examples work."""
        call_count = []

        @for_all(Gen.int(), Gen.str())
        @example(x=42, s="hello")
        @example(x=0, s="")
        def test_property(self, x: int, s: str):
            call_count.append((x, s))
            self.assertIsInstance(x, int)
            self.assertIsInstance(s, str)

        test_property(self)

        # Verify examples were run
        self.assertIn((42, "hello"), call_count)
        self.assertIn((0, ""), call_count)

    def test_mixed_positional_and_named(self):
        """Test mixing positional and named arguments."""
        call_count = []

        @for_all(Gen.int(), Gen.str(), Gen.bool())
        @example(42, s="hello", b=True)
        @example(0, s="", b=False)
        def test_property(self, x: int, s: str, b: bool):
            call_count.append((x, s, b))
            self.assertIsInstance(x, int)
            self.assertIsInstance(s, str)
            self.assertIsInstance(b, bool)

        test_property(self)

        # Verify examples were run
        self.assertIn((42, "hello", True), call_count)
        self.assertIn((0, "", False), call_count)

    def test_conflict_raises_error(self):
        """Test that specifying same arg positionally and by name raises error."""

        @for_all(Gen.int(), Gen.str())
        @example(42, x=100)  # x specified both ways
        def test_property(self, x: int, s: str):
            pass

        with self.assertRaises(ValueError) as cm:
            test_property(self)

        self.assertIn("both positionally and by name", str(cm.exception))

    def test_named_with_different_order(self):
        """Test that named args don't depend on position."""
        call_count = []

        @for_all(Gen.int(), Gen.str(), Gen.bool())
        @example(b=True, x=42, s="hello")  # Different order than params
        def test_property(self, x: int, s: str, b: bool):
            call_count.append((x, s, b))
            return True

        test_property(self)

        # Verify example was run with correct mapping
        self.assertIn((42, "hello", True), call_count)

    def test_unknown_parameter_raises_error(self):
        """Test that unknown parameter names raise an error."""

        @for_all(Gen.int(), Gen.str())
        @example(x=42, unknown_param="value")  # unknown_param doesn't exist
        def test_property(self, x: int, s: str):
            pass

        with self.assertRaises(ValueError) as cm:
            test_property(self)

        self.assertIn("Unknown parameter 'unknown_param'", str(cm.exception))
        self.assertIn("Available parameters", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
