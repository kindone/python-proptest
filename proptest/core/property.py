"""
Core property testing functionality.

This module provides the main Property class and for_all function
for running property-based tests.
"""

import random
from typing import Any, Callable, List, Optional, TypeVar, Union

from .generator import Generator, Random

T = TypeVar("T")


class PropertyTestError(Exception):
    """Exception raised when a property test fails."""

    def __init__(
        self,
        message: str,
        failing_inputs: Optional[List[Any]] = None,
        minimal_inputs: Optional[List[Any]] = None,
    ):
        self.failing_inputs = failing_inputs
        self.minimal_inputs = minimal_inputs

        # Create a user-friendly error message
        full_message = message

        if minimal_inputs is not None:
            full_message += f"\n\nMinimal counterexample: {minimal_inputs}"

        if failing_inputs is not None and failing_inputs != minimal_inputs:
            full_message += f"\nOriginal failing inputs: {failing_inputs}"

        super().__init__(full_message)


class Property:
    """Main class for property-based testing."""

    def __init__(
        self,
        property_func: Callable[..., bool],
        num_runs: int = 100,
        seed: Optional[Union[str, int]] = None,
    ):
        self.property_func = property_func
        self.num_runs = num_runs
        self.seed = seed
        self._rng = self._create_rng()

    def _create_rng(self) -> Random:
        """Create a random number generator."""
        if self.seed is not None:
            if isinstance(self.seed, str):
                # Convert string to integer seed
                seed_int = hash(self.seed) % (2**32)
            elif isinstance(self.seed, (list, dict, tuple)):
                # Convert complex types to integer seed using hash
                seed_int = hash(str(self.seed)) % (2**32)
            else:
                seed_int = self.seed
            return random.Random(seed_int)
        return random.Random()

    def for_all(self, *generators: Generator[Any]) -> bool:
        """
        Run property tests with the given generators.

        Args:
            *generators: Variable number of generators for test inputs

        Returns:
            True if all tests pass

        Raises:
            PropertyTestError: If any test fails
        """
        if len(generators) == 0:
            raise ValueError("At least one generator must be provided")

        for run in range(self.num_runs):
            try:
                # Generate test inputs
                inputs = []
                for generator in generators:
                    shrinkable = generator.generate(self._rng)
                    inputs.append(shrinkable.value)

                # Run the property
                result = self.property_func(*inputs)

                if not result:
                    # Property failed, try to shrink
                    minimal_inputs = self._shrink_failing_inputs(
                        inputs, list(generators)
                    )
                    raise PropertyTestError(
                        f"Property failed on run {run + 1}",
                        failing_inputs=inputs,
                        minimal_inputs=minimal_inputs,
                    )

            except Exception as e:
                if isinstance(e, PropertyTestError):
                    raise
                # Other exceptions are treated as property failures
                minimal_inputs = self._shrink_failing_inputs(inputs, list(generators))
                raise PropertyTestError(
                    f"Property failed with exception on run {run + 1}: {e}",
                    failing_inputs=inputs,
                    minimal_inputs=minimal_inputs,
                ) from e

        return True

    def _shrink_failing_inputs(
        self, inputs: List[Any], generators: List[Generator[Any]]
    ) -> List[Any]:
        """Attempt to shrink failing inputs to find minimal counterexamples."""
        if len(inputs) != len(generators):
            return inputs

        # Create a predicate that tests if the property passes with given inputs
        def property_predicate(test_inputs: List[Any]) -> bool:
            try:
                return self.property_func(*test_inputs)
            except Exception:
                return False

        # Shrink each input individually using the shrinkable candidates
        shrunk_inputs: List[Any] = []
        for i, (input_val, generator) in enumerate(zip(inputs, generators)):
            # Generate a shrinkable for this input to get shrinking candidates
            shrinkable = generator.generate(self._rng)
            # Override the value with our failing input
            shrinkable.value = input_val

            # Try to find a smaller failing value using the shrinkable's candidates
            current_val = input_val
            improved = True

            while improved:
                improved = False
                for candidate_shrinkable in shrinkable.shrinks().to_list():
                    candidate_val = candidate_shrinkable.value
                    # Test if this candidate also fails
                    test_inputs = shrunk_inputs[:i] + [candidate_val] + inputs[i + 1 :]
                    if not property_predicate(test_inputs):
                        # This candidate also fails, use it as the new current value
                        current_val = candidate_val
                        shrinkable = candidate_shrinkable
                        improved = True
                        break

            shrunk_inputs.append(current_val)

        return shrunk_inputs


def run_for_all(
    property_func: Callable[..., bool],
    *generators: Generator[Any],
    num_runs: int = 100,
    seed: Optional[Union[str, int]] = None,
) -> bool:
    """
    Run property-based tests with the given function and generators.

    This function executes property-based tests by running the given function
    with randomly generated inputs from the provided generators.

    Args:
        property_func: Function that takes generated inputs and returns a boolean
        *generators: Variable number of generators for test inputs
        num_runs: Number of test runs to perform
        seed: Optional seed for reproducible tests

    Returns:
        True if all tests pass

    Raises:
        PropertyTestError: If any test fails

    Examples:
        >>> def test_addition_commutative(a, b):
        ...     return a + b == b + a
        >>>
        >>> for_all(
        ...     test_addition_commutative,
        ...     Gen.int(min_value=0, max_value=100),
        ...     Gen.int(min_value=0, max_value=100),
        ...     num_runs=100
        ... )
        True

        >>> def test_string_length(s1, s2):
        ...     return len(s1 + s2) == len(s1) + len(s2)
        >>>
        >>> for_all(
        ...     test_string_length,
        ...     Gen.str(min_length=0, max_length=10),
        ...     Gen.str(min_length=0, max_length=10),
        ...     num_runs=50
        ... )
        True
    """
    property_test = Property(property_func, num_runs, seed)
    return property_test.for_all(*generators)


# Convenience function for pytest integration
def property_test(
    *generators: Generator[Any],
    num_runs: int = 100,
    seed: Optional[Union[str, int]] = None,
):
    """
    Decorator for property-based tests that integrates with pytest.

    Args:
        *generators: Variable number of generators for test inputs
        num_runs: Number of test runs to perform
        seed: Optional seed for reproducible tests

    Examples:
        >>> @property_test(
        ...     Gen.int(min_value=0, max_value=100),
        ...     Gen.int(min_value=0, max_value=100),
        ...     num_runs=100
        ... )
        ... def test_addition_commutative(a, b):
        ...     assert a + b == b + a
    """

    def decorator(func: Callable[..., bool]) -> Callable[[], bool]:
        def wrapper() -> bool:
            return run_for_all(func, *generators, num_runs=num_runs, seed=seed)

        return wrapper

    return decorator
