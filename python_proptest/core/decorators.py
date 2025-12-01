"""
Decorator-based API for property-based testing.

This module provides decorators similar to Hypothesis for more ergonomic
property-based testing with complex functions.
"""

import inspect
import itertools
from typing import Any, Callable, Dict, Iterable, List, Union

from .generator import Generator
from .property import Property, PropertyTestError


def for_all(
    *generators: Generator[Any], num_runs: int = 100, seed: Union[str, int, None] = None
):
    """
    Decorator for property-based testing with generators.

    This decorator automatically detects whether it's being used in a unittest context
    (unittest.TestCase methods), pytest context (class methods with 'self' parameter),
    or standalone functions and adapts accordingly.

    Usage:
        # Standalone function
        @for_all(Gen.int(), Gen.str())
        def test_property(x: int, s: str):
            assert len(s) >= 0
            assert x * 2 == x + x

        # Pytest class method
        class TestMyProperties:
            @for_all(Gen.int(), Gen.str())
            def test_property(self, x: int, s: str):
                assert len(s) >= 0
                assert x * 2 == x + x

        # Unittest class method
        import unittest
        class TestMyUnittestProperties(unittest.TestCase):
            @for_all(Gen.int(), Gen.str())
            def test_property(self, x: int, s: str):
                self.assertGreaterEqual(len(s), 0)
                self.assertEqual(x * 2, x + x)

    Args:
        *generators: Variable number of generators for function arguments
        num_runs: Number of test runs (default: 100)
        seed: Random seed for reproducibility (default: None)

    Returns:
        Decorated function that runs property-based tests
    """

    def decorator(func: Callable) -> Callable:
        # Preserve any existing _proptest_examples / _proptest_settings /
        # _proptest_matrices / _proptest_for_all_configs
        existing_examples = getattr(func, "_proptest_examples", [])
        existing_settings = getattr(func, "_proptest_settings", {})
        existing_matrices = getattr(func, "_proptest_matrices", [])
        existing_for_all_configs = getattr(func, "_proptest_for_all_configs", [])

        # Get function signature to validate argument count
        # If function is already wrapped by @for_all, use the original signature
        if hasattr(func, "_proptest_original_sig"):
            sig = func._proptest_original_sig  # type: ignore
        else:
            sig = inspect.signature(func)
        params = [
            p for p in sig.parameters.values() if p.kind == p.POSITIONAL_OR_KEYWORD
        ]

        # Check if this is a test class method (has 'self' as first parameter)
        is_test_method = params and params[0].name == "self"

        # Determine if it's unittest or pytest by checking the class hierarchy
        is_unittest_method = False
        is_pytest_method = False

        if is_test_method:
            # Get the class that contains this method
            if hasattr(func, "__self__"):
                # Method is bound to an instance
                test_class = func.__self__.__class__
            elif hasattr(func, "__qualname__") and "." in func.__qualname__:
                # Method is unbound, try to get class from qualname
                class_name = func.__qualname__.split(".")[0]
                # Try to find the class in the module
                module = inspect.getmodule(func)
                if module and hasattr(module, class_name):
                    test_class = getattr(module, class_name)
                else:
                    test_class = None
            else:
                test_class = None

            if test_class:
                # Check if it inherits from unittest.TestCase
                try:
                    import unittest  # noqa: F401

                    is_unittest_method = issubclass(test_class, unittest.TestCase)
                except ImportError:
                    is_unittest_method = False

                # If not unittest, assume it's pytest
                if not is_unittest_method:
                    is_pytest_method = True

        # For class methods, exclude 'self' from the count
        param_count = len(params)
        if is_test_method:  # Both unittest and pytest methods have 'self'
            param_count -= 1

        if param_count != len(generators):
            raise ValueError(
                f"Function {func.__name__} expects {param_count} arguments, "
                f"but {len(generators)} generators were provided"
            )

        # Don't use @functools.wraps to avoid pytest fixture injection issues
        def wrapper(*args, **kwargs):
            # For test class methods (both unittest and pytest), we need to handle
            # the 'self' parameter
            if is_test_method:
                # In test context, args[0] is 'self', and we need to generate
                # values for the rest
                if len(args) > 1:
                    # Function was called with arguments (shouldn't happen in test
                    # frameworks)
                    return func(*args, **kwargs)

                # Check if this is being called by test framework directly (no
                # arguments except self)
                if len(args) == 1:  # Only 'self' parameter
                    # This is test framework calling the method directly - run
                    # property-based testing
                    pass  # Continue to property-based testing below
                else:
                    # This shouldn't happen in normal test framework usage
                    return func(*args, **kwargs)

                # Run property-based testing for test frameworks
                try:
                    # Create a property function that works with both unittest and
                    # pytest
                    def test_property(*generated_args):
                        try:
                            # Call the original function with 'self' and generated
                            # arguments
                            func(args[0], *generated_args)
                            return True  # No assertion failed
                        except AssertionError:
                            return False  # Assertion failed
                        except Exception as e:
                            # Handle assume() calls by checking for SkipTest
                            if "Assumption failed" in str(e):
                                return True  # Skip this test case
                            raise  # Re-raise other exceptions

                    # Apply settings overrides if provided
                    override_num_runs = existing_settings.get("num_runs", num_runs)
                    override_seed = existing_settings.get("seed", seed)

                    # Execute matrix cases first (do not count toward num_runs)
                    # Run each matrix spec independently
                    for matrix_spec in existing_matrices:
                        _run_matrix_cases(func, args[0], matrix_spec)

                    # Run all @for_all configurations (append behavior)
                    # Examples are shared across all configs
                    for config in existing_for_all_configs:
                        config_generators = config["generators"]
                        config_num_runs = config.get("num_runs", override_num_runs)
                        config_seed = config.get("seed", override_seed)

                        property_test = Property(
                            test_property,
                            num_runs=config_num_runs,
                            seed=config_seed,
                            examples=existing_examples,  # Examples shared across all configs
                        )
                        property_test.for_all(*config_generators)

                    # Run the current @for_all configuration
                    property_test = Property(
                        test_property,
                        num_runs=override_num_runs,
                        seed=override_seed,
                        examples=existing_examples,
                    )
                    property_test.for_all(*generators)
                    return None  # Test frameworks expect test functions to return
                    # None
                except PropertyTestError as e:
                    # Re-raise as appropriate exception for the test framework
                    if is_unittest_method:
                        # For unittest, we need to raise the test case's failure
                        # exception
                        try:
                            import unittest  # noqa: F401

                            # Get the test case instance and raise its failure exception
                            test_case = args[0]  # 'self' is the test case instance
                            raise test_case.failureException(str(e)) from e
                        except (ImportError, AttributeError):
                            # Fallback to AssertionError if unittest not available
                            raise AssertionError(str(e)) from e
                    else:
                        # For pytest, raise AssertionError
                        raise AssertionError(str(e)) from e
            else:
                # Standalone function - original behavior
                if args or kwargs:
                    return func(*args, **kwargs)

                # Run property-based testing
                try:
                    # Create a property function that returns True/False based on
                    # assertions
                    def assertion_property(*args):
                        try:
                            func(*args)
                            return True  # No assertion failed
                        except AssertionError:
                            return False  # Assertion failed
                        except Exception as e:
                            # Handle assume() calls by checking for SkipTest
                            if "Assumption failed" in str(e):
                                return True  # Skip this test case
                            raise  # Re-raise other exceptions

                    # Apply settings overrides if provided
                    override_num_runs = existing_settings.get("num_runs", num_runs)
                    override_seed = existing_settings.get("seed", seed)

                    # Execute matrix cases first (do not count toward num_runs)
                    # Run each matrix spec independently
                    for matrix_spec in existing_matrices:
                        _run_matrix_cases(func, None, matrix_spec)

                    # Run all @for_all configurations (append behavior)
                    # Examples are shared across all configs
                    for config in existing_for_all_configs:
                        config_generators = config["generators"]
                        config_num_runs = config.get("num_runs", override_num_runs)
                        config_seed = config.get("seed", override_seed)

                        property_test = Property(
                            assertion_property,
                            num_runs=config_num_runs,
                            seed=config_seed,
                            examples=existing_examples,  # Examples shared across all configs
                        )
                        property_test.for_all(*config_generators)

                    # Run the current @for_all configuration
                    property_test = Property(
                        assertion_property,
                        num_runs=override_num_runs,
                        seed=override_seed,
                        examples=existing_examples,
                    )
                    property_test.for_all(*generators)
                    return None  # Pytest expects test functions to return None
                except PropertyTestError as e:
                    # Re-raise as AssertionError for better test framework integration
                    raise AssertionError(str(e)) from e

        # Manually set function metadata (normally done by @functools.wraps)
        wrapper.__name__ = func.__name__
        wrapper.__qualname__ = func.__qualname__
        wrapper.__doc__ = func.__doc__
        wrapper.__module__ = func.__module__
        wrapper.__annotations__ = func.__annotations__

        # Store original signature for validation when stacking decorators
        # If func is already wrapped, preserve its original signature
        if hasattr(func, "_proptest_original_sig"):
            wrapper._proptest_original_sig = func._proptest_original_sig  # type: ignore
        else:
            # Store the original function's signature (before wrapping)
            wrapper._proptest_original_sig = sig  # type: ignore

        # Add metadata for introspection
        wrapper._proptest_generators = generators  # type: ignore
        wrapper._proptest_num_runs = num_runs  # type: ignore
        wrapper._proptest_seed = seed  # type: ignore
        wrapper._proptest_is_pytest_method = is_pytest_method  # type: ignore
        wrapper._proptest_is_unittest_method = is_unittest_method  # type: ignore
        wrapper._proptest_is_test_method = is_test_method  # type: ignore

        # Preserve examples, settings, and matrices from other decorators
        wrapper._proptest_examples = existing_examples  # type: ignore
        wrapper._proptest_settings = existing_settings  # type: ignore
        wrapper._proptest_matrices = existing_matrices  # type: ignore

        # Append this @for_all configuration to the list (append behavior)
        # Store the configuration for this decorator
        new_config = {
            "generators": generators,
            "num_runs": num_runs,
            "seed": seed,
        }
        wrapper._proptest_for_all_configs = existing_for_all_configs + [new_config]  # type: ignore

        return wrapper

    return decorator


def example(*values: Any):
    """
    Decorator to provide example values for a property test.

    Usage:
        @for_all(Gen.int(), Gen.str())
        @example(42, "hello")
        def test_property(x: int, s: str):
            assert x > 0 or len(s) > 0

    Args:
        *values: Example values to test in addition to generated ones

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        # Store examples for later use
        if not hasattr(func, "_proptest_examples"):
            func._proptest_examples = []  # type: ignore
        func._proptest_examples.append(values)  # type: ignore
        return func

    return decorator


def matrix(**kwargs: Iterable[Any]):
    """
    Decorator to provide an exhaustive matrix (Cartesian product) of example values.

    Usage:
        @for_all(Gen.int(), Gen.str())
        @matrix(x=[0, 1], s=["a", "b"])
        def test_property(x: int, s: str):
            ...

    Notes:
        - Matrix cases are executed once per combination, before examples/random runs.
        - Matrix cases do not count toward settings(num_runs).
        - Multiple @matrix decorators can be stacked. Each decorator creates separate
          matrix cases that run independently. If you want to merge values, combine
          them in a single @matrix decorator.
    """

    def decorator(func: Callable) -> Callable:
        # Store matrix specs as a list (each decorator adds its own spec)
        if not hasattr(func, "_proptest_matrices"):
            func._proptest_matrices = []  # type: ignore
        # Append this matrix spec to the list
        func._proptest_matrices.append(dict(kwargs))  # type: ignore
        return func

    return decorator


def _run_matrix_cases(
    func: Callable, self_obj: Any, matrix_spec: Dict[str, Iterable[Any]]
):
    # Build argument order from function signature (skip self when present)
    sig = inspect.signature(func)
    params: List[str] = [
        p.name for p in sig.parameters.values() if p.kind == p.POSITIONAL_OR_KEYWORD
    ]
    is_method = bool(params and params[0] == "self")
    call_params = params[1:] if is_method else params

    # Only run matrix cases if all call parameters are covered by matrix spec
    if not all(name in matrix_spec for name in call_params):
        return

    # Only include parameters that are actually needed by the function
    needed_keys = [k for k in matrix_spec.keys() if k in call_params]
    if not needed_keys:
        return

    # Construct cartesian product in key order
    values_product = itertools.product(*[list(matrix_spec[k]) for k in needed_keys])

    for combo in values_product:
        # Map provided keys to their values
        arg_map: Dict[str, Any] = dict(zip(needed_keys, combo))
        # Build positional args in function param order
        args_in_order: List[Any] = [arg_map[name] for name in call_params]
        try:
            if is_method:
                func(self_obj, *args_in_order)
            else:
                func(*args_in_order)
        except Exception as e:
            # Handle assume() calls by checking for "Assumption failed"
            if "Assumption failed" in str(e):
                continue  # Skip this matrix case
            raise  # Re-raise other exceptions


def settings(**kwargs):
    """
    Decorator to configure property test settings.

    Usage:
        @for_all(Gen.int())
        @settings(num_runs=1000, seed=42)
        def test_property(x: int):
            assert x * 0 == 0

    Args:
        **kwargs: Settings to override (num_runs, seed, etc.)

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        # Store settings for later use
        if not hasattr(func, "_proptest_settings"):
            func._proptest_settings = {}  # type: ignore
        func._proptest_settings.update(kwargs)  # type: ignore
        return func

    return decorator


def assume(condition: bool):
    """
    Skip the current test case if the condition is False.

    Usage:
        @for_all(Gen.int(), Gen.int())
        def test_division(x: int, y: int):
            assume(y != 0)  # Skip cases where y is 0
            assert x / y * y == x

    Args:
        condition: Condition that must be True to continue the test

    Raises:
        Exception: If condition is False (with message 'Assumption failed')
    """
    if not condition:
        # Raise a regular exception that the property testing framework can catch
        raise Exception("Assumption failed")


def note(message: str):
    """
    Add a note to the test output (useful for debugging).

    Usage:
        @for_all(Gen.int())
        def test_property(x: int):
            note(f"Testing with x = {x}")
            assert x * 2 == x + x

    Args:
        message: Message to include in test output
    """
    # For now, just print the message
    # In a more sophisticated implementation, this could be integrated
    # with test reporting frameworks
    print(f"Note: {message}")


# Convenience function for running decorated tests
def run_property_test(func: Callable) -> Any:
    """
    Run a property test function that has been decorated with @for_all.

    Usage:
        @for_all(Gen.int())
        def test_property(x: int):
            assert x * 0 == 0

        if __name__ == "__main__":
            run_property_test(test_property)

    Args:
        func: Decorated function to run

    Returns:
        Result of the property test
    """
    if not hasattr(func, "_proptest_generators"):
        raise ValueError(f"Function {func.__name__} is not decorated with @for_all")

    # Run the property test
    func()
    # Return True to indicate successful execution
    return True
