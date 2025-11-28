"""
Stateful testing functionality.

This module provides classes and functions for testing stateful systems
using property-based testing.
"""

import random
from typing import Callable, Generic, List, Optional, TypeVar, Union

from .generator import Gen, Generator
from .property import PropertyTestError

S = TypeVar("S")  # State type
A = TypeVar("A")  # Action type


class SimpleAction(Generic[S]):
    """A simple action that operates on state without a model."""

    def __init__(self, action_func: Callable[[S], None]):
        self.action_func = action_func

    def run(self, state: S) -> None:
        """Run the action on the given state."""
        self.action_func(state)


class Action(Generic[S, A]):
    """An action that operates on both state and model."""

    def __init__(self, action_func: Callable[[S, A], None]):
        self.action_func = action_func

    def run(self, state: S, model: A) -> None:
        """Run the action on the given state and model."""
        self.action_func(state, model)


class StatefulProperty(Generic[S, A]):
    """A property for testing stateful systems."""

    def __init__(
        self,
        initial_state_gen: Generator[S],
        action_gen: Generator[Union[SimpleAction[S], Action[S, A]]],
        max_actions: int = 100,
        num_runs: int = 100,
        seed: Optional[Union[str, int]] = None,
        initial_model_gen: Optional[Generator[A]] = None,
    ):
        self.initial_state_gen = initial_state_gen
        self.action_gen = action_gen
        self.initial_model_gen = initial_model_gen
        self.max_actions = max_actions
        self.num_runs = num_runs
        self.seed = seed
        self._rng = self._create_rng()
        self._startup_callbacks: List[Callable[[], None]] = []
        self._cleanup_callbacks: List[Callable[[], None]] = []

    def _create_rng(self) -> random.Random:
        """Create a random number generator."""
        if self.seed is not None:
            if isinstance(self.seed, str):
                seed_int = hash(self.seed) % (2**32)
            elif isinstance(self.seed, (list, dict, tuple)):
                seed_int = hash(str(self.seed)) % (2**32)
            else:
                seed_int = self.seed
            return random.Random(seed_int)
        return random.Random()

    def setOnStartup(self, callback: Callable[[], None]) -> "StatefulProperty[S, A]":
        """Set a startup callback."""
        self._startup_callbacks.append(callback)
        return self

    def setOnCleanup(self, callback: Callable[[], None]) -> "StatefulProperty[S, A]":
        """Set a cleanup callback."""
        self._cleanup_callbacks.append(callback)
        return self

    def go(self) -> None:
        """Run the stateful property test."""
        for run in range(self.num_runs):
            try:
                # Run startup callbacks
                for callback in self._startup_callbacks:
                    callback()

                # Generate initial state
                initial_state_shrinkable = self.initial_state_gen.generate(self._rng)
                state = initial_state_shrinkable.value

                # Generate initial model if needed
                model = None
                if self.initial_model_gen is not None:
                    model_shrinkable = self.initial_model_gen.generate(self._rng)
                    model = model_shrinkable.value

                # Generate and run actions
                if self.max_actions > 0:
                    num_actions = self._rng.randint(1, self.max_actions)
                    for _ in range(num_actions):
                        action_shrinkable = self.action_gen.generate(self._rng)
                        action = action_shrinkable.value
                        if isinstance(action, Action) and model is not None:
                            action.run(state, model)
                        else:
                            action.run(state)  # type: ignore

                # Run cleanup callbacks
                cleanup_exception = None
                for callback in self._cleanup_callbacks:
                    try:
                        callback()
                    except Exception as cleanup_err:
                        # Store cleanup exception but don't raise it yet
                        cleanup_exception = cleanup_err

            except Exception as e:
                # Run cleanup callbacks even on failure
                cleanup_exception = None
                for callback in self._cleanup_callbacks:
                    try:
                        callback()
                    except Exception as cleanup_err:
                        # Store cleanup exception but don't raise it
                        cleanup_exception = cleanup_err
                # Only raise the original exception, not cleanup exceptions
                raise PropertyTestError(
                    f"Stateful property failed on run {run + 1}: {e}"
                )
            else:
                # If no exception occurred, but cleanup raised, log it but don't fail
                if cleanup_exception is not None:
                    # Cleanup exceptions are ignored - they shouldn't fail the test
                    pass


def simpleActionGenOf(
    state_type: type, *action_gens: Generator[SimpleAction[S]]
) -> Generator[SimpleAction[S]]:
    """Create a generator that randomly selects from multiple action generators."""
    if not action_gens:
        raise ValueError("At least one action generator must be provided")

    return Gen.one_of(*action_gens)


def actionGenOf(
    state_type: type, model_type: type, *action_gens: Generator[Action[S, A]]
) -> Generator[Action[S, A]]:
    """Create a generator that randomly selects from multiple action generators."""
    if not action_gens:
        raise ValueError("At least one action generator must be provided")

    return Gen.one_of(*action_gens)


def statefulProperty(
    initial_state_gen: Generator[S],
    action_gen: Generator[Action[S, A]],
    max_actions: int = 100,
    num_runs: int = 100,
    seed: Optional[Union[str, int]] = None,
    initial_model_gen: Optional[Generator[A]] = None,
) -> StatefulProperty[S, A]:
    """Create a stateful property for testing."""
    return StatefulProperty(
        initial_state_gen,
        action_gen,  # type: ignore
        max_actions,
        num_runs,
        seed,
        initial_model_gen,  # type: ignore
    )


def simpleStatefulProperty(
    initial_state_gen: Generator[S],
    action_gen: Generator[SimpleAction[S]],
    max_actions: int = 100,
    num_runs: int = 100,
    seed: Optional[Union[str, int]] = None,
) -> StatefulProperty[S, A]:
    """Create a simple stateful property for testing without a model."""
    return StatefulProperty(
        initial_state_gen, action_gen, max_actions, num_runs, seed  # type: ignore
    )
