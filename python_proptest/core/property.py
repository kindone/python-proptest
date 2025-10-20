"""
Core property testing functionality.

This module provides the main Property class and for_all function
for running property-based tests.
"""

import random
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, TypeVar, Union

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
        examples: Optional[List[Tuple[Any, ...]]] = None,
    ):
        self.property_func = property_func
        self.num_runs = num_runs
        self.seed = seed
        self.examples = examples or []
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

        # Test examples first
        for example_inputs in self.examples:
            if len(example_inputs) != len(generators):
                continue  # Skip examples with wrong number of arguments

            try:
                result = self.property_func(*example_inputs)
                if not result:
                    # Example failed, create error
                    raise PropertyTestError(
                        f"Property failed on example: {example_inputs}",
                        failing_inputs=list(example_inputs),
                        minimal_inputs=list(example_inputs),
                    )
            except Exception as e:
                if "Assumption failed" in str(e):
                    continue  # Skip examples that fail assumptions
                raise PropertyTestError(
                    f"Property failed on example: {example_inputs}",
                    failing_inputs=list(example_inputs),
                    minimal_inputs=list(example_inputs),
                ) from e

        # Then run random tests
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


def run_matrix(
    test_func: Callable[..., Any],
    matrix_spec: Dict[str, Iterable[Any]],
    *,
    self_obj: Optional[Any] = None,
) -> None:
    """
    Execute an exhaustive matrix (Cartesian product) of inputs for a test function.

    Matrix cases are executed once each, without shrinking and without counting
    toward property num_runs.
    """
    # Resolve parameter order
    import inspect
    import itertools

    sig = inspect.signature(test_func)
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

    values_product = itertools.product(*[list(matrix_spec[k]) for k in needed_keys])

    for combo in values_product:
        arg_map: Dict[str, Any] = dict(zip(needed_keys, combo))
        args_in_order: List[Any] = [arg_map[name] for name in call_params]
        if is_method or self_obj is not None:
            target = self_obj
            if target is None:
                raise ValueError("self_obj must be provided for bound methods")
            test_func(target, *args_in_order)
        else:
            test_func(*args_in_order)


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
