"""Tests for @example decorator and its interaction with @for_all."""

import unittest

from python_proptest import Gen, Property, example, for_all, settings


class TestExampleDecorator(unittest.TestCase):
    """Test @example decorator functionality."""

    def test_example_decorator_stores_examples(self):
        """Test that @example decorator stores examples on the function."""

        @example(42, "hello")
        def test_func(x: int, s: str):
            pass

        # Check that examples are stored
        self.assertTrue(hasattr(test_func, "_proptest_examples"))
        self.assertEqual(test_func._proptest_examples, [(42, "hello")])

        # Test multiple examples
        @example(1, "a")
        @example(2, "b")
        def test_func_multiple(x: int, s: str):
            pass

        self.assertEqual(len(test_func_multiple._proptest_examples), 2)
        self.assertIn((1, "a"), test_func_multiple._proptest_examples)
        self.assertIn((2, "b"), test_func_multiple._proptest_examples)

    def test_example_with_for_all_standalone(self):
        """Test @example with @for_all on standalone functions."""

        # This should work but examples might not be used yet
        @for_all(Gen.int(), Gen.str())
        @example(42, "hello")
        def test_property(x: int, s: str):
            # This should always pass for the example values
            assert isinstance(x, int)
            assert isinstance(s, str)

        # The function should be callable
        test_property()

        # Check that examples are stored
        self.assertTrue(hasattr(test_property, "_proptest_examples"))
        self.assertEqual(test_property._proptest_examples, [(42, "hello")])

    def test_example_with_for_all_pytest_method(self):
        """Test @example with @for_all on pytest class methods."""

        class TestExamplePytest:
            @for_all(Gen.int(), Gen.str())
            @example(42, "hello")
            def test_property(self, x: int, s: str):
                assert isinstance(x, int)
                assert isinstance(s, str)

        # Create instance and test
        test_instance = TestExamplePytest()
        test_instance.test_property()

        # Check that examples are stored
        self.assertTrue(hasattr(test_instance.test_property, "_proptest_examples"))
        self.assertEqual(
            test_instance.test_property._proptest_examples, [(42, "hello")]
        )

    def test_example_with_for_all_unittest_method(self):
        """Test @example with @for_all on unittest class methods."""

        class TestExampleUnittest(unittest.TestCase):
            @for_all(Gen.int(), Gen.str())
            @example(42, "hello")
            def test_property(self, x: int, s: str):
                self.assertIsInstance(x, int)
                self.assertIsInstance(s, str)

        # Create instance and test
        test_instance = TestExampleUnittest()
        test_instance.test_property()

        # Check that examples are stored
        self.assertTrue(hasattr(test_instance.test_property, "_proptest_examples"))
        self.assertEqual(
            test_instance.test_property._proptest_examples, [(42, "hello")]
        )

    def test_multiple_examples(self):
        """Test multiple @example decorators."""

        @for_all(Gen.int(), Gen.str())
        @example(1, "a")
        @example(2, "b")
        @example(3, "c")
        def test_property(x: int, s: str):
            assert isinstance(x, int)
            assert isinstance(s, str)

        test_property()

        # Check that all examples are stored
        self.assertEqual(len(test_property._proptest_examples), 3)
        self.assertIn((1, "a"), test_property._proptest_examples)
        self.assertIn((2, "b"), test_property._proptest_examples)
        self.assertIn((3, "c"), test_property._proptest_examples)

    def test_example_with_settings(self):
        """Test @example with @settings decorator."""

        @for_all(Gen.int(), Gen.str())
        @example(42, "hello")
        @settings(num_runs=50)
        def test_property(x: int, s: str):
            assert isinstance(x, int)
            assert isinstance(s, str)

        test_property()

        # Check that both examples and settings are stored
        self.assertTrue(hasattr(test_property, "_proptest_examples"))
        self.assertTrue(hasattr(test_property, "_proptest_settings"))
        self.assertEqual(test_property._proptest_examples, [(42, "hello")])
        self.assertEqual(test_property._proptest_settings, {"num_runs": 50})

    def test_example_decorator_order(self):
        """Test that decorator order doesn't matter for @example."""

        # @example first, then @for_all
        @example(42, "hello")
        @for_all(Gen.int(), Gen.str())
        def test_property1(x: int, s: str):
            assert isinstance(x, int)
            assert isinstance(s, str)

        # @for_all first, then @example
        @for_all(Gen.int(), Gen.str())
        @example(42, "hello")
        def test_property2(x: int, s: str):
            assert isinstance(x, int)
            assert isinstance(s, str)

        # Both should work
        test_property1()
        test_property2()

        # Both should have examples stored
        self.assertTrue(hasattr(test_property1, "_proptest_examples"))
        self.assertTrue(hasattr(test_property2, "_proptest_examples"))
        self.assertEqual(test_property1._proptest_examples, [(42, "hello")])
        self.assertEqual(test_property2._proptest_examples, [(42, "hello")])

    def test_example_with_different_types(self):
        """Test @example with different data types."""

        @for_all(Gen.int(), Gen.str(), Gen.bool(), Gen.float())
        @example(42, "hello", True, 3.14)
        def test_property(x: int, s: str, b: bool, f: float):
            assert isinstance(x, int)
            assert isinstance(s, str)
            assert isinstance(b, bool)
            assert isinstance(f, float)

        test_property()

        # Check that examples are stored
        self.assertTrue(hasattr(test_property, "_proptest_examples"))
        self.assertEqual(test_property._proptest_examples, [(42, "hello", True, 3.14)])

    def test_example_with_edge_cases(self):
        """Test @example with edge case values."""

        @for_all(Gen.int(), Gen.str())
        @example(0, "")
        @example(-1, " ")
        @example(1, "a")
        def test_property(x: int, s: str):
            assert isinstance(x, int)
            assert isinstance(s, str)

        test_property()

        # Check that all examples are stored
        self.assertEqual(len(test_property._proptest_examples), 3)
        self.assertIn((0, ""), test_property._proptest_examples)
        self.assertIn((-1, " "), test_property._proptest_examples)
        self.assertIn((1, "a"), test_property._proptest_examples)

    # ------------------------------------------------------------------
    # Tests merged from test_example_simple.py
    # ------------------------------------------------------------------
    def test_example_execution_direct_property(self):
        """Examples should execute when using Property directly."""

        executions = []

        def property_func(x: int, s: str):
            executions.append((x, s))
            return True

        prop = Property(property_func, examples=[(42, "hello"), (100, "world")])
        prop.for_all(Gen.int(), Gen.str())

        self.assertIn((42, "hello"), executions)
        self.assertIn((100, "world"), executions)
        self.assertGreater(len(executions), 2)

    def test_example_failure_direct_property(self):
        """Failing examples should surface immediately with Property."""

        executions = []

        def property_func(x: int, s: str):
            executions.append((x, s))
            return x > 0

        prop = Property(property_func, examples=[(0, "hello")])

        with self.assertRaises(Exception) as cm:
            prop.for_all(Gen.int(), Gen.str())

        self.assertIn("Property failed on example", str(cm.exception))
        self.assertIn("(0, 'hello')", str(cm.exception))
        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0], (0, "hello"))

    def test_example_execution_with_decorator(self):
        """Examples should execute when using @for_all decorator."""

        executions = []

        @for_all(Gen.int(), Gen.str())
        @example(42, "hello")
        @example(100, "world")
        def test_property(x: int, s: str):
            executions.append((x, s))
            return isinstance(x, int) and isinstance(s, str)

        test_property()

        self.assertIn((42, "hello"), executions)
        self.assertIn((100, "world"), executions)
        self.assertGreater(len(executions), 2)

    def test_example_failure_with_decorator(self):
        """Failing examples with decorators should halt immediately."""

        executions = []

        @for_all(Gen.int(), Gen.str())
        @example(0, "hello")
        def test_property(x: int, s: str):
            executions.append((x, s))
            assert x > 0

        with self.assertRaises(AssertionError) as cm:
            test_property()

        self.assertIn("Property failed on example", str(cm.exception))
        self.assertIn("(0, 'hello')", str(cm.exception))
        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0], (0, "hello"))

    # ------------------------------------------------------------------
    # Tests merged from test_example_working.py
    # ------------------------------------------------------------------
    def test_example_success_with_restrictive_generators(self):
        """Examples should work with restrictive generators."""

        @for_all(Gen.int(min_value=1), Gen.str(min_length=1))
        @example(1, "hello")
        def test_property(x: int, s: str):
            assert x > 0
            assert len(s) > 0

        test_property()

    def test_example_with_bool_generator(self):
        """Examples should work with boolean generators."""

        @for_all(Gen.bool())
        @example(True)
        def test_property(b: bool):
            assert isinstance(b, bool)

        test_property()

    def test_example_with_float_generator(self):
        """Examples should work with float generators."""

        @for_all(Gen.float())
        @example(3.14)
        def test_property(f: float):
            assert isinstance(f, float)

        test_property()


if __name__ == "__main__":
    unittest.main()
