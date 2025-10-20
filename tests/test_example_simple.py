"""Simple tests to verify that @example decorator actually executes examples."""

import unittest
from python_proptest import Gen, for_all, example, Property


class TestExampleSimple(unittest.TestCase):
    """Simple tests to verify example execution."""

    def test_example_execution_direct_property(self):
        """Test examples directly with Property class."""

        # Track executions
        executions = []

        def property_func(x: int, s: str):
            executions.append((x, s))
            return True  # Always pass

        # Create property with examples
        prop = Property(property_func, examples=[(42, "hello"), (100, "world")])

        # Run with generators
        prop.for_all(Gen.int(), Gen.str())

        # Check that examples were executed
        self.assertIn((42, "hello"), executions)
        self.assertIn((100, "world"), executions)

        # Check that we have more than just examples (random tests too)
        self.assertGreater(len(executions), 2)

    def test_example_failure_direct_property(self):
        """Test that failing examples are detected with Property class."""

        # Track executions
        executions = []

        def property_func(x: int, s: str):
            executions.append((x, s))
            return x > 0  # Fail for x <= 0

        # Create property with failing example
        prop = Property(property_func, examples=[(0, "hello")])

        # This should fail immediately
        with self.assertRaises(Exception) as cm:
            prop.for_all(Gen.int(), Gen.str())

        # Check that the error mentions the example
        self.assertIn("Property failed on example", str(cm.exception))
        self.assertIn("(0, 'hello')", str(cm.exception))

        # Check that only the failing example was executed
        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0], (0, "hello"))

    def test_example_execution_with_decorator(self):
        """Test examples with @for_all decorator using simple property."""

        # Track executions
        executions = []

        @for_all(Gen.int(), Gen.str())
        @example(42, "hello")
        @example(100, "world")
        def test_property(x: int, s: str):
            executions.append((x, s))
            # Simple property that always passes
            return isinstance(x, int) and isinstance(s, str)

        # Run the test
        test_property()

        # Check that examples were executed
        self.assertIn((42, "hello"), executions)
        self.assertIn((100, "world"), executions)

        # Check that we have more than just examples (random tests too)
        self.assertGreater(len(executions), 2)

    def test_example_failure_with_decorator(self):
        """Test that failing examples are detected with @for_all decorator."""

        # Track executions
        executions = []

        @for_all(Gen.int(), Gen.str())
        @example(0, "hello")  # This will fail
        def test_property(x: int, s: str):
            executions.append((x, s))
            assert x > 0  # Fail for x <= 0

        # This should fail immediately
        with self.assertRaises(AssertionError) as cm:
            test_property()

        # Check that the error mentions the example
        self.assertIn("Property failed on example", str(cm.exception))
        self.assertIn("(0, 'hello')", str(cm.exception))

        # Check that only the failing example was executed
        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0], (0, "hello"))


if __name__ == "__main__":
    unittest.main()
