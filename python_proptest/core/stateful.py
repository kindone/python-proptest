"""
Stateful testing functionality.

This module provides classes and functions for testing stateful systems
using property-based testing.
"""

import random
import time
from copy import deepcopy
from typing import Any, Callable, Generic, List, Optional, TypeVar, Union, cast

from .generator import Gen, Generator
from .property import PropertyTestError, ReproductionStats, WriteStream
from .shrinker import Shrinkable
from .shrinker.list import shrinkable_array

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
        shrink_max_retries: int = 0,
        shrink_timeout_ms: Optional[int] = None,
        shrink_retry_timeout_ms: Optional[int] = None,
        output_stream: Optional[WriteStream] = None,
        error_stream: Optional[WriteStream] = None,
        on_reproduction_stats: Optional[Callable[[ReproductionStats], None]] = None,
    ):
        self.initial_state_gen = initial_state_gen
        self.action_gen = action_gen
        self.initial_model_gen = initial_model_gen
        self.max_actions = max_actions
        self.num_runs = num_runs
        self.seed = seed
        self.shrink_max_retries = self._validate_non_negative_int(
            shrink_max_retries, "shrink_max_retries"
        )
        self.shrink_timeout_ms = self._validate_timeout_ms(shrink_timeout_ms)
        self.shrink_retry_timeout_ms = self._validate_timeout_ms(
            shrink_retry_timeout_ms
        )
        self.output_stream = self._validate_stream(output_stream, "output_stream")
        self.error_stream = self._validate_stream(error_stream, "error_stream")
        self.on_reproduction_stats = on_reproduction_stats
        self.last_reproduction_stats: Optional[ReproductionStats] = None
        self._rng = self._create_rng()
        self._startup_callbacks: List[Callable[[], None]] = []
        self._cleanup_callbacks: List[Callable[[], None]] = []

    @staticmethod
    def _validate_non_negative_int(value: int, name: str) -> int:
        if not isinstance(value, int):
            raise TypeError(f"{name} must be an integer")
        if value < 0:
            raise ValueError(f"{name} must be non-negative")
        return value

    @staticmethod
    def _validate_timeout_ms(timeout_ms: Optional[int]) -> Optional[int]:
        if timeout_ms is None:
            return None
        if not isinstance(timeout_ms, (int, float)):
            raise TypeError("timeout_ms must be a number or None")
        if timeout_ms != timeout_ms or timeout_ms in (float("inf"), float("-inf")):
            raise ValueError("timeout_ms must be finite")
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be non-negative")
        return int(timeout_ms)

    @staticmethod
    def _validate_stream(
        stream: Optional[WriteStream], name: str
    ) -> Optional[WriteStream]:
        if stream is not None and not callable(getattr(stream, "write", None)):
            raise TypeError(f"{name} must have a write(str) method")
        return stream

    @staticmethod
    def _has_exceeded_timeout(started_at: float, timeout_ms: Optional[int]) -> bool:
        if timeout_ms is None:
            return False
        return (time.monotonic() - started_at) * 1000 >= timeout_ms

    def _write_output(self, message: str) -> None:
        if self.output_stream is not None:
            self.output_stream.write(message)

    def _write_error(self, message: str) -> None:
        if self.error_stream is not None:
            self.error_stream.write(message)

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

    def set_shrink_max_retries(
        self, shrink_max_retries: int
    ) -> "StatefulProperty[S, A]":
        """Set extra retry attempts for each stateful shrink candidate."""
        self.shrink_max_retries = self._validate_non_negative_int(
            shrink_max_retries, "shrink_max_retries"
        )
        return self

    def set_shrink_timeout_ms(
        self, shrink_timeout_ms: Optional[int]
    ) -> "StatefulProperty[S, A]":
        """Set the total stateful shrink phase time budget."""
        self.shrink_timeout_ms = self._validate_timeout_ms(shrink_timeout_ms)
        return self

    def set_shrink_retry_timeout_ms(
        self, shrink_retry_timeout_ms: Optional[int]
    ) -> "StatefulProperty[S, A]":
        """Set the per-candidate stateful shrink retry time budget."""
        self.shrink_retry_timeout_ms = self._validate_timeout_ms(
            shrink_retry_timeout_ms
        )
        return self

    def set_output_stream(
        self, output_stream: Optional[WriteStream]
    ) -> "StatefulProperty[S, A]":
        """Set the stream used for informational stateful shrink output."""
        self.output_stream = self._validate_stream(output_stream, "output_stream")
        return self

    def set_error_stream(
        self, error_stream: Optional[WriteStream]
    ) -> "StatefulProperty[S, A]":
        """Set the stream used for stateful runner error output."""
        self.error_stream = self._validate_stream(error_stream, "error_stream")
        return self

    def set_on_reproduction_stats(
        self, callback: Optional[Callable[[ReproductionStats], None]]
    ) -> "StatefulProperty[S, A]":
        """Set the callback invoked after stateful shrink retry assessment."""
        self.on_reproduction_stats = callback
        return self

    def get_last_reproduction_stats(self) -> Optional[ReproductionStats]:
        """Return the most recent stateful shrink reproduction stats."""
        return self.last_reproduction_stats

    def go(self) -> None:
        """Run the stateful property test."""
        for run in range(self.num_runs):
            initial_state_shrinkable: Optional[Shrinkable[S]] = None
            model_shrinkable: Optional[Shrinkable[A]] = None
            action_shrinkables: List[Shrinkable[Any]] = []
            state: Any = None
            model: Any = None
            try:
                # Run startup callbacks
                for callback in self._startup_callbacks:
                    callback()

                # Generate initial state
                initial_state_shrinkable = self.initial_state_gen.generate(self._rng)
                state = initial_state_shrinkable.value

                # Generate initial model if needed
                if self.initial_model_gen is not None:
                    model_shrinkable = self.initial_model_gen.generate(self._rng)
                    model = model_shrinkable.value

                # Generate and run actions
                if self.max_actions > 0:
                    num_actions = self._rng.randint(1, self.max_actions)
                    for _ in range(num_actions):
                        action_shrinkable = self.action_gen.generate(self._rng)
                        action_shrinkables.append(action_shrinkable)

                self._run_actions(
                    state,
                    model,
                    [
                        action_shrinkable.value
                        for action_shrinkable in action_shrinkables
                    ],
                )

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
                minimal_inputs: Optional[List[Any]] = None
                if initial_state_shrinkable is not None:
                    minimal_inputs = self._shrink_failure(
                        initial_state_shrinkable,
                        model_shrinkable,
                        action_shrinkables,
                    )
                raise PropertyTestError(
                    f"Stateful property failed on run {run + 1}: {e}",
                    failing_inputs=[state, [shr.value for shr in action_shrinkables]],
                    minimal_inputs=minimal_inputs,
                )
            else:
                # If no exception occurred, but cleanup raised, log it but don't fail
                if cleanup_exception is not None:
                    # Cleanup exceptions are ignored - they shouldn't fail the test
                    pass

    def _run_actions(
        self,
        state: S,
        model: Optional[A],
        actions: List[Union[SimpleAction[S], Action[S, A]]],
    ) -> None:
        for action in actions:
            if isinstance(action, Action):
                action.run(state, cast(A, model))
            else:
                action.run(state)

    def _candidate_fails(
        self, state: S, model: Optional[A], actions: List[Any]
    ) -> bool:
        try:
            self._run_actions(deepcopy(state), deepcopy(model), deepcopy(actions))
        except Exception:
            return True
        return False

    def _test_shrink_candidate_with_retries(
        self,
        args_as_string: str,
        run_candidate: Callable[[], bool],
        shrink_started_at: float,
    ) -> bool:
        candidate_started_at = time.monotonic()
        attempts = 0
        num_reproduced = 0
        max_attempts = self.shrink_max_retries + 1

        while attempts < max_attempts:
            if self._has_exceeded_timeout(shrink_started_at, self.shrink_timeout_ms):
                break
            if attempts > 0 and self._has_exceeded_timeout(
                candidate_started_at, self.shrink_retry_timeout_ms
            ):
                break

            attempts += 1
            if run_candidate():
                num_reproduced += 1

        stats: ReproductionStats = {
            "num_reproduced": num_reproduced,
            "total_runs": attempts,
            "elapsed_sec": time.monotonic() - candidate_started_at,
            "args_as_string": args_as_string,
        }
        self.last_reproduction_stats = stats
        if self.on_reproduction_stats is not None:
            self.on_reproduction_stats(stats)

        return num_reproduced > 0

    def _shrink_failure(
        self,
        initial_state_shrinkable: Shrinkable[S],
        model_shrinkable: Optional[Shrinkable[A]],
        action_shrinkables: List[Shrinkable[Any]],
    ) -> List[Any]:
        shrink_started_at = time.monotonic()
        current_state: Any = initial_state_shrinkable.value
        current_model: Any = (
            model_shrinkable.value if model_shrinkable is not None else None
        )
        current_actions: List[Any] = [shr.value for shr in action_shrinkables]

        action_list_shrinkable = shrinkable_array(action_shrinkables, min_size=0)
        action_stream = action_list_shrinkable.shrinks()
        while not action_stream.is_empty():
            if self._has_exceeded_timeout(shrink_started_at, self.shrink_timeout_ms):
                break

            action_candidate = action_stream.head()
            if action_candidate is None:
                break
            candidate_actions = action_candidate.value

            def run_action_candidate(
                actions: List[Any] = candidate_actions,
            ) -> bool:
                return self._candidate_fails(current_state, current_model, actions)

            reproduced = self._test_shrink_candidate_with_retries(
                f"actions={candidate_actions!r}",
                run_action_candidate,
                shrink_started_at,
            )
            if reproduced:
                current_actions = candidate_actions
                action_stream = action_candidate.shrinks()
                self._write_output(
                    "  stateful shrinking found simpler failing action sequence: "
                    f"{len(current_actions)} actions\n"
                )
                continue

            action_stream = action_stream.tail()

        state_stream = initial_state_shrinkable.shrinks()
        while not state_stream.is_empty():
            if self._has_exceeded_timeout(shrink_started_at, self.shrink_timeout_ms):
                break

            state_candidate = state_stream.head()
            if state_candidate is None:
                break
            candidate_state = state_candidate.value

            def run_state_candidate(state: Any = candidate_state) -> bool:
                return self._candidate_fails(state, current_model, current_actions)

            reproduced = self._test_shrink_candidate_with_retries(
                f"initial_state={candidate_state!r}",
                run_state_candidate,
                shrink_started_at,
            )
            if reproduced:
                current_state = candidate_state
                state_stream = state_candidate.shrinks()
                self._write_output(
                    "  stateful shrinking found simpler initial state: "
                    f"{current_state!r}\n"
                )
                continue

            state_stream = state_stream.tail()

        return [current_state, current_actions]


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
    shrink_max_retries: int = 0,
    shrink_timeout_ms: Optional[int] = None,
    shrink_retry_timeout_ms: Optional[int] = None,
    output_stream: Optional[WriteStream] = None,
    error_stream: Optional[WriteStream] = None,
    on_reproduction_stats: Optional[Callable[[ReproductionStats], None]] = None,
) -> StatefulProperty[S, A]:
    """Create a stateful property for testing."""
    return StatefulProperty(
        initial_state_gen,
        action_gen,  # type: ignore
        max_actions,
        num_runs,
        seed,
        initial_model_gen,  # type: ignore
        shrink_max_retries,
        shrink_timeout_ms,
        shrink_retry_timeout_ms,
        output_stream,
        error_stream,
        on_reproduction_stats,
    )


def simpleStatefulProperty(
    initial_state_gen: Generator[S],
    action_gen: Generator[SimpleAction[S]],
    max_actions: int = 100,
    num_runs: int = 100,
    seed: Optional[Union[str, int]] = None,
    shrink_max_retries: int = 0,
    shrink_timeout_ms: Optional[int] = None,
    shrink_retry_timeout_ms: Optional[int] = None,
    output_stream: Optional[WriteStream] = None,
    error_stream: Optional[WriteStream] = None,
    on_reproduction_stats: Optional[Callable[[ReproductionStats], None]] = None,
) -> StatefulProperty[S, A]:
    """Create a simple stateful property for testing without a model."""
    return StatefulProperty(
        initial_state_gen,
        cast(Generator[Union[SimpleAction[S], Action[S, A]]], action_gen),
        max_actions,
        num_runs,
        seed,  # type: ignore
        None,
        shrink_max_retries,
        shrink_timeout_ms,
        shrink_retry_timeout_ms,
        output_stream,
        error_stream,
        on_reproduction_stats,
    )
