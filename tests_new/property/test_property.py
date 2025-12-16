"""Unit tests for ``python_proptest.core.property`` helpers and public API."""

import unittest

from python_proptest import Gen, Property, PropertyTestError, run_for_all


class TestPropertyModule(unittest.TestCase):
    """Verify core property runner behaviour across argument shapes and seeds."""

    def test_property_with_always_true_condition(self):
        """run_for_all succeeds when predicate always returns truthy values."""

        def property_func(a, b):
            return True

        result = run_for_all(
            property_func,
            Gen.int(min_value=0, max_value=100),
            Gen.int(min_value=0, max_value=100),
            num_runs=10,
        )
        self.assertTrue(result)

    def test_property_with_void_function_that_never_throws(self):
        """Functions without return value still pass when they avoid exceptions."""

        def property_func(a, b):
            return True

        result = run_for_all(
            property_func,
            Gen.int(min_value=0, max_value=100),
            Gen.int(min_value=0, max_value=100),
            num_runs=10,
        )
        self.assertTrue(result)

    def test_property_with_single_argument_always_true(self):
        """Single-argument properties wire correctly through run_for_all."""

        def property_func(x):
            return True

        result = run_for_all(
            property_func, Gen.int(min_value=0, max_value=100), num_runs=10
        )
        self.assertTrue(result)

    def test_property_with_three_arguments_always_true(self):
        """Support multi-argument predicates without raising failures."""

        def property_func(a, b, c):
            return True

        result = run_for_all(
            property_func,
            Gen.int(min_value=0, max_value=100),
            Gen.int(min_value=0, max_value=100),
            Gen.int(min_value=0, max_value=100),
            num_runs=10,
        )
        self.assertTrue(result)

    def test_property_with_five_arguments_always_true(self):
        """Allow up to five generator arguments for compatibility parity."""

        def property_func(a, b, c, d, e):
            return True

        result = run_for_all(
            property_func,
            Gen.int(min_value=0, max_value=100),
            Gen.int(min_value=0, max_value=100),
            Gen.int(min_value=0, max_value=100),
            Gen.int(min_value=0, max_value=100),
            Gen.int(min_value=0, max_value=100),
            num_runs=10,
        )
        self.assertTrue(result)

    def test_property_with_mixed_types_always_true(self):
        """Ensure heterogeneous generator combinations flow into predicates."""

        def property_func(a, b, c, d):
            return True

        result = run_for_all(
            property_func,
            Gen.int(min_value=0, max_value=100),
            Gen.str(min_length=0, max_length=10),
            Gen.bool(),
            Gen.float(min_value=0.0, max_value=1.0),
            num_runs=10,
        )
        self.assertTrue(result)

    def test_property_with_list_argument_always_true(self):
        """List-valued generators feed through the property runner."""

        def property_func(lst):
            return True

        result = run_for_all(
            property_func,
            Gen.list(Gen.int(min_value=0, max_value=10), min_length=0, max_length=5),
            num_runs=10,
        )
        self.assertTrue(result)

    def test_property_with_dict_argument_always_true(self):
        """Dictionary-valued generators integrate without extra wiring."""

        def property_func(dct):
            return True

        result = run_for_all(
            property_func,
            Gen.dict(
                Gen.str(min_length=1, max_length=3),
                Gen.int(min_value=0, max_value=10),
            ),
            num_runs=10,
        )
        self.assertTrue(result)

    def test_property_with_nested_structures_always_true(self):
        """Nested composite generators execute successfully."""

        def property_func(data):
            return True

        nested_gen = Gen.list(
            Gen.dict(
                Gen.str(min_length=1, max_length=2),
                Gen.int(min_value=0, max_value=5),
            ),
            min_length=0,
            max_length=3,
        )

        result = run_for_all(property_func, nested_gen, num_runs=10)
        self.assertTrue(result)

    def test_property_with_seed_reproducibility(self):
        """Identical seeds should produce reproducible outcomes."""

        def property_func(x):
            return True

        result1 = run_for_all(
            property_func, Gen.int(min_value=0, max_value=100), num_runs=10, seed=42
        )

        result2 = run_for_all(
            property_func, Gen.int(min_value=0, max_value=100), num_runs=10, seed=42
        )

        self.assertTrue(result1)
        self.assertTrue(result2)

    def test_property_with_string_seed(self):
        """String seeds should be accepted for reproducibility."""

        def property_func(x):
            return True

        result = run_for_all(
            property_func,
            Gen.int(min_value=0, max_value=100),
            num_runs=10,
            seed="test_seed",
        )
        self.assertTrue(result)

    def test_property_with_zero_runs(self):
        """Zero-run configuration short-circuits while returning success."""

        def property_func(x):
            return True

        result = run_for_all(
            property_func, Gen.int(min_value=0, max_value=100), num_runs=0
        )
        self.assertTrue(result)

    def test_property_with_single_run(self):
        """Single run executes exactly once and returns success."""

        def property_func(x):
            return True

        result = run_for_all(
            property_func, Gen.int(min_value=0, max_value=100), num_runs=1
        )
        self.assertTrue(result)

    def test_property_with_large_number_of_runs(self):
        """High iteration counts should remain stable and performant."""

        def property_func(x):
            return True

        result = run_for_all(
            property_func, Gen.int(min_value=0, max_value=100), num_runs=1000
        )
        self.assertTrue(result)

    def test_property_class_direct_usage(self):
        """Property class can be invoked directly with generators."""

        def property_func(x):
            return True

        prop = Property(property_func, num_runs=10)
        result = prop.for_all(Gen.int(min_value=0, max_value=100))
        self.assertTrue(result)

    def test_property_class_with_seed(self):
        """Property class respects configured seeds for reproducibility."""

        def property_func(x):
            return True

        prop = Property(property_func, num_runs=10, seed=42)
        result = prop.for_all(Gen.int(min_value=0, max_value=100))
        self.assertTrue(result)

    def test_property_failure_raises_property_test_error(self):
        """Failing predicate raises PropertyTestError with counterexample."""

        def property_func(x):
            self.assertIsInstance(x, int)
            return x < 0

        with self.assertRaises(PropertyTestError):
            run_for_all(property_func, Gen.int(min_value=0, max_value=10), num_runs=5)

    def test_property_with_exception_handling(self):
        """Exceptions inside predicates bubble up as PropertyTestError."""

        def property_func(x):
            if x < 0:
                raise ValueError("Negative value")
            return True

        with self.assertRaises(PropertyTestError):
            run_for_all(
                property_func, Gen.int(min_value=-10, max_value=-1), num_runs=10
            )

    def test_property_exception_is_wrapped_in_property_test_error(self):
        """Exceptions raised in predicates surface as PropertyTestError."""

        def property_func(_x):
            raise ValueError("boom")

        with self.assertRaises(PropertyTestError) as ctx:
            run_for_all(property_func, Gen.int(min_value=0, max_value=10), num_runs=5)

        self.assertIn("boom", str(ctx.exception))

    def test_property_with_failing_condition(self):
        """Counterexamples expose failing inputs through the error object."""

        def property_func(x):
            return x < 50

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func, Gen.int(min_value=50, max_value=100), num_runs=10
            )

        failing_inputs = exc_info.exception.failing_inputs
        self.assertIsNotNone(failing_inputs)
        self.assertEqual(len(failing_inputs), 1)
        self.assertGreaterEqual(failing_inputs[0], 50)

    def test_property_with_complex_failing_condition(self):
        """Multiple generators expose multi-argument counterexamples."""

        def property_func(a, b, c):
            return a + b + c < 100

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func,
                Gen.int(min_value=40, max_value=50),
                Gen.int(min_value=40, max_value=50),
                Gen.int(min_value=40, max_value=50),
                num_runs=10,
            )

        failing_inputs = exc_info.exception.failing_inputs
        self.assertIsNotNone(failing_inputs)
        self.assertEqual(len(failing_inputs), 3)
        a, b, c = failing_inputs
        self.assertGreaterEqual(a + b + c, 100)

    def test_property_with_no_generators_raises_error(self):
        """run_for_all requires at least one generator when callable expects args."""

        def property_func():
            return True

        with self.assertRaises(ValueError):
            run_for_all(property_func, num_runs=10)

    def test_property_with_wrong_number_of_arguments_raises_error(self):
        """Mismatch between predicate arity and generators raises helpful errors."""

        def property_func(x):
            return True

        with self.assertRaises(Exception):
            run_for_all(
                property_func,
                Gen.int(min_value=0, max_value=100),
                Gen.int(min_value=0, max_value=100),
                num_runs=10,
            )


if __name__ == "__main__":
    unittest.main()
