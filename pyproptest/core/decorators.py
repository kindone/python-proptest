"""
Decorator-based API for property-based testing.

This module provides decorators similar to Hypothesis for more ergonomic
property-based testing with complex functions.
"""

import inspect
from typing import Any, Callable, Union

from .generator import Generator
from .property import Property, PropertyTestError


def for_all(
    *generators: Generator[Any], num_runs: int = 100, seed: Union[str, int, None] = None
):
    """
    Decorator for property-based testing with generators.

    This decorator automatically detects whether it's being used in a pytest context
    (class methods with 'self' parameter) or standalone functions and adapts accordingly.

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

    Args:
        *generators: Variable number of generators for function arguments
        num_runs: Number of test runs (default: 100)
        seed: Random seed for reproducibility (default: None)

    Returns:
        Decorated function that runs property-based tests
    """

    def decorator(func: Callable) -> Callable:
        # Get function signature to validate argument count
        sig = inspect.signature(func)
        params = [
            p for p in sig.parameters.values() if p.kind == p.POSITIONAL_OR_KEYWORD
        ]

        # Check if this is a pytest class method (has 'self' as first parameter)
        is_pytest_method = params and params[0].name == "self"

        # For class methods, exclude 'self' from the count
        param_count = len(params)
        if is_pytest_method:
            param_count -= 1

        if param_count != len(generators):
            raise ValueError(
                f"Function {func.__name__} expects {param_count} arguments, "
                f"but {len(generators)} generators were provided"
            )

        # Don't use @functools.wraps to avoid pytest fixture injection issues
        def wrapper(*args, **kwargs):
            # For pytest class methods, we need to handle the 'self' parameter
            if is_pytest_method:
                # In pytest context, args[0] is 'self', and we need to generate values for the rest
                if len(args) > 1:
                    # Function was called with arguments (shouldn't happen in pytest)
                    return func(*args, **kwargs)

                # Check if this is being called by pytest directly (no arguments except self)
                if len(args) == 1:  # Only 'self' parameter
                    # This is pytest calling the method directly - run property-based testing
                    pass  # Continue to property-based testing below
                else:
                    # This shouldn't happen in normal pytest usage
                    return func(*args, **kwargs)

                # Run property-based testing for pytest
                try:
                    # Create a property function that works with pytest
                    def pytest_property(*generated_args):
                        try:
                            # Call the original function with 'self' and generated arguments
                            func(args[0], *generated_args)
                            return True  # No assertion failed
                        except AssertionError:
                            return False  # Assertion failed
                        except Exception as e:
                            # Handle assume() calls by checking for SkipTest
                            if "Assumption failed" in str(e):
                                return True  # Skip this test case
                            raise  # Re-raise other exceptions

                    # Extract generators from Strategy objects if needed
                    actual_generators = []
                    for gen in generators:
                        if hasattr(gen, "generator"):
                            # It's a Strategy object
                            actual_generators.append(gen.generator)
                        else:
                            # It's already a Generator
                            actual_generators.append(gen)

                    property_test = Property(
                        pytest_property, num_runs=num_runs, seed=seed
                    )
                    property_test.for_all(*actual_generators)
                    return None  # Pytest expects test functions to return None
                except PropertyTestError as e:
                    # Re-raise as AssertionError for better pytest integration
                    raise AssertionError(str(e)) from e
            else:
                # Standalone function - original behavior
                if args or kwargs:
                    return func(*args, **kwargs)

                # Run property-based testing
                try:
                    # Create a property function that returns True/False based on assertions
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

                    # Extract generators from Strategy objects if needed
                    actual_generators = []
                    for gen in generators:
                        if hasattr(gen, "generator"):
                            # It's a Strategy object
                            actual_generators.append(gen.generator)
                        else:
                            # It's already a Generator
                            actual_generators.append(gen)

                    property_test = Property(
                        assertion_property, num_runs=num_runs, seed=seed
                    )
                    property_test.for_all(*actual_generators)
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

        # Add metadata for introspection
        wrapper._pyproptest_generators = generators
        wrapper._pyproptest_num_runs = num_runs
        wrapper._pyproptest_seed = seed
        wrapper._pyproptest_is_pytest_method = is_pytest_method

        return wrapper

    return decorator


# Alias for Hypothesis compatibility
given = for_all


def example(*values: Any):
    """
    Decorator to provide example values for a property test.

    Usage:
        @given(Gen.int(), Gen.str())
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
        if not hasattr(func, "_pyproptest_examples"):
            func._pyproptest_examples = []
        func._pyproptest_examples.append(values)
        return func

    return decorator


def settings(**kwargs):
    """
    Decorator to configure property test settings.

    Usage:
        @given(Gen.int())
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
        if not hasattr(func, "_pyproptest_settings"):
            func._pyproptest_settings = {}
        func._pyproptest_settings.update(kwargs)
        return func

    return decorator


def assume(condition: bool):
    """
    Skip the current test case if the condition is False.

    Usage:
        @given(Gen.int(), Gen.int())
        def test_division(x: int, y: int):
            assume(y != 0)  # Skip cases where y is 0
            assert x / y * y == x

    Args:
        condition: Condition that must be True to continue the test

    Raises:
        SkipTest: If condition is False
    """
    if not condition:
        # Import here to avoid circular imports
        try:
            import pytest

            pytest.skip("Assumption failed")
        except ImportError:
            # Fallback for non-pytest environments
            class SkipTest(Exception):
                pass

            raise SkipTest("Assumption failed")


def note(message: str):
    """
    Add a note to the test output (useful for debugging).

    Usage:
        @given(Gen.int())
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
    Run a property test function that has been decorated with @given.

    Usage:
        @given(Gen.int())
        def test_property(x: int):
            assert x * 0 == 0

        if __name__ == "__main__":
            run_property_test(test_property)

    Args:
        func: Decorated function to run

    Returns:
        Result of the property test
    """
    if not hasattr(func, "_pyproptest_generators"):
        raise ValueError(f"Function {func.__name__} is not decorated with @given")

    return func()


# Utility for creating custom strategies
class Strategy:
    """Base class for custom strategies."""

    def __init__(self, generator: Generator[Any]):
        self.generator = generator

    def map(self, func: Callable[[Any], Any]) -> "Strategy":
        """Map a function over this strategy."""
        return Strategy(self.generator.map(func))

    def filter(self, predicate: Callable[[Any], bool]) -> "Strategy":
        """Filter this strategy with a predicate."""
        return Strategy(self.generator.filter(predicate))

    def flatmap(self, func: Callable[[Any], "Strategy"]) -> "Strategy":
        """Flat map a function over this strategy."""

        def generator_func(value):
            strategy = func(value)
            return strategy.generator

        return Strategy(self.generator.flat_map(generator_func))


# Convenience functions for creating strategies
def integers(min_value: int = None, max_value: int = None) -> Strategy:
    """Create an integer strategy."""
    from .generator import Gen

    # Only pass non-None values to avoid overriding defaults
    kwargs = {}
    if min_value is not None:
        kwargs["min_value"] = min_value
    if max_value is not None:
        kwargs["max_value"] = max_value
    return Strategy(Gen.int(**kwargs))


def floats(min_value: float = None, max_value: float = None) -> Strategy:
    """Create a float strategy."""
    from .generator import Gen

    # Only pass non-None values to avoid overriding defaults
    kwargs = {}
    if min_value is not None:
        kwargs["min_value"] = min_value
    if max_value is not None:
        kwargs["max_value"] = max_value
    return Strategy(Gen.float(**kwargs))


def text(min_size: int = 0, max_size: int = None, alphabet: str = None) -> Strategy:
    """Create a text strategy."""
    from .generator import Gen

    # Only pass non-None values to avoid overriding defaults
    kwargs = {}
    if min_size is not None:
        kwargs["min_length"] = min_size
    if max_size is not None:
        kwargs["max_length"] = max_size
    # For now, ignore alphabet parameter
    return Strategy(Gen.str(**kwargs))


def lists(elements: Strategy, min_size: int = 0, max_size: int = None) -> Strategy:
    """Create a list strategy."""
    from .generator import Gen

    # Only pass non-None values to avoid overriding defaults
    kwargs = {}
    if min_size is not None:
        kwargs["min_length"] = min_size
    if max_size is not None:
        kwargs["max_length"] = max_size
    return Strategy(Gen.list(elements.generator, **kwargs))


def dictionaries(
    keys: Strategy, values: Strategy, min_size: int = 0, max_size: int = None
) -> Strategy:
    """Create a dictionary strategy."""
    from .generator import Gen

    # Only pass non-None values to avoid overriding defaults
    kwargs = {}
    if min_size is not None:
        kwargs["min_size"] = min_size
    if max_size is not None:
        kwargs["max_size"] = max_size
    return Strategy(Gen.dict(keys.generator, values.generator, **kwargs))


def one_of(*strategies: Strategy) -> Strategy:
    """Create a strategy that chooses from multiple strategies."""
    from .generator import Gen

    generators = [s.generator for s in strategies]
    return Strategy(Gen.one_of(*generators))


def just(value: Any) -> Strategy:
    """Create a strategy that always returns the same value."""
    from .generator import Gen

    return Strategy(Gen.just(value))
