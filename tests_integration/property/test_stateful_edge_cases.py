"""
Tests for edge cases in stateful property testing.

This module tests error handling, callbacks, and edge cases in stateful testing.
"""

import unittest
from typing import List
from unittest.mock import Mock

from python_proptest import Gen, PropertyTestError, SimpleAction
from python_proptest.core.stateful import (
    Action,
    StatefulProperty,
    actionGenOf,
    simpleActionGenOf,
    simpleStatefulProperty,
    statefulProperty,
)


class TestStatefulPropertyEdgeCases(unittest.TestCase):
    """Test edge cases in StatefulProperty."""

    def test_startup_callbacks(self):
        """Test startup callbacks are called."""
        callback = Mock()
        prop = StatefulProperty(
            Gen.just(0),
            Gen.just(SimpleAction(lambda s: None)),
            num_runs=1,
        )
        prop.setOnStartup(callback)
        prop.go()
        callback.assert_called_once()

    def test_cleanup_callbacks(self):
        """Test cleanup callbacks are called."""
        callback = Mock()
        prop = StatefulProperty(
            Gen.just(0),
            Gen.just(SimpleAction(lambda s: None)),
            num_runs=1,
        )
        prop.setOnCleanup(callback)
        prop.go()
        callback.assert_called_once()

    def test_cleanup_callbacks_on_failure(self):
        """Test cleanup callbacks are called even on failure."""
        cleanup_callback = Mock()
        startup_callback = Mock()

        # Create an action that will fail
        failing_action = SimpleAction(
            lambda s: (_ for _ in ()).throw(ValueError("Test error"))
        )

        prop = StatefulProperty(
            Gen.just(0),
            Gen.just(failing_action),
            num_runs=1,
        )
        prop.setOnStartup(startup_callback)
        prop.setOnCleanup(cleanup_callback)

        with self.assertRaises(PropertyTestError):
            prop.go()

        startup_callback.assert_called_once()
        cleanup_callback.assert_called_once()

    def test_cleanup_callback_exception_handling(self):
        """Test that cleanup callback exceptions don't prevent cleanup."""
        cleanup_callback1 = Mock()
        cleanup_callback2 = Mock(side_effect=ValueError("Cleanup error"))
        cleanup_callback3 = Mock()

        prop = StatefulProperty(
            Gen.just(0),
            Gen.just(SimpleAction(lambda s: None)),
            num_runs=1,
        )
        prop.setOnCleanup(cleanup_callback1)
        prop.setOnCleanup(cleanup_callback2)
        prop.setOnCleanup(cleanup_callback3)

        # Should not raise, even though callback2 raises
        prop.go()

        cleanup_callback1.assert_called_once()
        cleanup_callback2.assert_called_once()
        cleanup_callback3.assert_called_once()

    def test_multiple_startup_callbacks(self):
        """Test multiple startup callbacks are called in order."""
        callback1 = Mock()
        callback2 = Mock()
        callback3 = Mock()

        prop = StatefulProperty(
            Gen.just(0),
            Gen.just(SimpleAction(lambda s: None)),
            num_runs=1,
        )
        prop.setOnStartup(callback1)
        prop.setOnStartup(callback2)
        prop.setOnStartup(callback3)
        prop.go()

        # All should be called
        callback1.assert_called_once()
        callback2.assert_called_once()
        callback3.assert_called_once()

    def test_multiple_cleanup_callbacks(self):
        """Test multiple cleanup callbacks are called."""
        callback1 = Mock()
        callback2 = Mock()
        callback3 = Mock()

        prop = StatefulProperty(
            Gen.just(0),
            Gen.just(SimpleAction(lambda s: None)),
            num_runs=1,
        )
        prop.setOnCleanup(callback1)
        prop.setOnCleanup(callback2)
        prop.setOnCleanup(callback3)
        prop.go()

        # All should be called
        callback1.assert_called_once()
        callback2.assert_called_once()
        callback3.assert_called_once()

    def test_action_with_model(self):
        """Test Action with model parameter is called during the run.

        Each run operates on an isolated deepcopy of the initial model so that
        state from one run does not bleed into the next.  The test verifies
        that the action function is actually invoked (via a closure side-effect
        that survives deepcopy) rather than checking that the original dict was
        mutated (which would be an implementation-detail leak).
        """
        calls: List[int] = []  # closure survives deepcopy — function ref is shared

        def action_func(state: int, model: dict) -> None:
            calls.append(1)  # appends to the outer list regardless of model copy

        action = Action(action_func)
        prop = StatefulProperty(
            Gen.just(0),
            Gen.just(action),
            max_actions=1,
            num_runs=1,
            initial_model_gen=Gen.just({"count": 0}),
        )
        prop.go()

        # The action must have been called exactly once (1 run × 1 action)
        self.assertEqual(len(calls), 1)

    def test_action_without_model_raises(self):
        """Test Action without model raises error."""

        def action_func(state: int, model: dict):
            model["count"] += 1

        action = Action(action_func)
        prop = StatefulProperty(
            Gen.just(0),
            Gen.just(action),
            num_runs=1,
            # No initial_model_gen
        )

        # Should raise when action.run is called without model
        with self.assertRaises(PropertyTestError):
            prop.go()

    def test_zero_max_actions(self):
        """Test with max_actions=0 (no actions executed)."""
        callback = Mock()
        prop = StatefulProperty(
            Gen.just(0),
            Gen.just(SimpleAction(lambda s: callback())),
            max_actions=0,
            num_runs=1,
        )
        prop.go()

        # Callback should not be called since no actions run
        callback.assert_not_called()

    def test_custom_seed_string(self):
        """Test StatefulProperty with string seed."""
        prop1 = StatefulProperty(
            Gen.int(),
            Gen.just(SimpleAction(lambda s: None)),
            num_runs=10,
            seed="test_seed",
        )
        prop2 = StatefulProperty(
            Gen.int(),
            Gen.just(SimpleAction(lambda s: None)),
            num_runs=10,
            seed="test_seed",
        )

        # Both should use the same seed
        prop1.go()
        prop2.go()

    def test_custom_seed_int(self):
        """Test StatefulProperty with integer seed."""
        prop = StatefulProperty(
            Gen.int(),
            Gen.just(SimpleAction(lambda s: None)),
            num_runs=1,
            seed=42,
        )
        prop.go()

    def test_custom_seed_none(self):
        """Test StatefulProperty with None seed (random)."""
        prop = StatefulProperty(
            Gen.int(),
            Gen.just(SimpleAction(lambda s: None)),
            num_runs=1,
            seed=None,
        )
        prop.go()

    def test_property_test_error_message(self):
        """Test PropertyTestError includes run number."""
        failing_action = SimpleAction(
            lambda s: (_ for _ in ()).throw(ValueError("Test"))
        )

        prop = StatefulProperty(
            Gen.just(0),
            Gen.just(failing_action),
            num_runs=1,
        )

        with self.assertRaises(PropertyTestError) as cm:
            prop.go()

        self.assertIn("run 1", str(cm.exception).lower())

    def test_chaining_setonstartup(self):
        """Test chaining setOnStartup calls."""
        callback1 = Mock()
        callback2 = Mock()

        prop = StatefulProperty(
            Gen.just(0),
            Gen.just(SimpleAction(lambda s: None)),
            num_runs=1,
        )
        result = prop.setOnStartup(callback1).setOnStartup(callback2)
        self.assertIs(result, prop)  # Should return self for chaining
        prop.go()

        callback1.assert_called_once()
        callback2.assert_called_once()

    def test_chaining_setoncleanup(self):
        """Test chaining setOnCleanup calls."""
        callback1 = Mock()
        callback2 = Mock()

        prop = StatefulProperty(
            Gen.just(0),
            Gen.just(SimpleAction(lambda s: None)),
            num_runs=1,
        )
        result = prop.setOnCleanup(callback1).setOnCleanup(callback2)
        self.assertIs(result, prop)  # Should return self for chaining
        prop.go()

        callback1.assert_called_once()
        callback2.assert_called_once()


class TestSimpleActionGenOf(unittest.TestCase):
    """Test simpleActionGenOf function."""

    def test_simple_action_gen_of(self):
        """Test simpleActionGenOf creates generator."""
        action1 = Gen.just(SimpleAction(lambda s: None))
        action2 = Gen.just(SimpleAction(lambda s: None))
        gen = simpleActionGenOf(int, action1, action2)
        self.assertIsNotNone(gen)

    def test_simple_action_gen_of_empty(self):
        """Test simpleActionGenOf with no actions raises ValueError."""
        with self.assertRaises(ValueError):
            simpleActionGenOf(int)


class TestActionGenOf(unittest.TestCase):
    """Test actionGenOf function."""

    def test_action_gen_of(self):
        """Test actionGenOf creates generator."""
        action1 = Gen.just(Action(lambda s, m: None))
        action2 = Gen.just(Action(lambda s, m: None))
        gen = actionGenOf(int, dict, action1, action2)
        self.assertIsNotNone(gen)

    def test_action_gen_of_empty(self):
        """Test actionGenOf with no actions raises ValueError."""
        with self.assertRaises(ValueError):
            actionGenOf(int, dict)


class TestStatefulPropertyFactory(unittest.TestCase):
    """Test stateful property factory functions."""

    def test_stateful_property_factory(self):
        """Test statefulProperty factory function."""
        prop = statefulProperty(
            Gen.just(0),
            Gen.just(Action(lambda s, m: None)),
            num_runs=1,
            initial_model_gen=Gen.just({}),
        )
        self.assertIsInstance(prop, StatefulProperty)
        prop.go()

    def test_simple_stateful_property_factory(self):
        """Test simpleStatefulProperty factory function."""
        prop = simpleStatefulProperty(
            Gen.just(0),
            Gen.just(SimpleAction(lambda s: None)),
            num_runs=1,
        )
        self.assertIsInstance(prop, StatefulProperty)
        prop.go()


class TestActionGenFactory(unittest.TestCase):
    """Tests for state-dependent action_gen_factory and PrefixParams shrinking.

    ``action_gen_factory`` is a callable ``(state, model) → Generator[Action]``
    that enables state-dependent action generation and Phase 2b (PrefixParams)
    shrinking: after sequence pruning, non-last-slot actions are re-generated
    from their stored Random bookmark with the live reconstructed state, giving
    a fresh shrink tree that may contain better candidates than the stored tree.
    """

    # ── Validation ────────────────────────────────────────────────────────────

    def test_neither_action_gen_nor_factory_raises(self):
        """Supply neither action_gen nor action_gen_factory → ValueError."""
        with self.assertRaises(ValueError, msg="Supply either action_gen or action_gen_factory"):
            StatefulProperty(Gen.just(0))  # neither supplied

    def test_both_action_gen_and_factory_raises(self):
        """Supply both action_gen and action_gen_factory → ValueError."""
        noop_action_gen = Gen.just(Action(lambda s, m: None))
        noop_factory = lambda s, m: Gen.just(Action(lambda s, m: None))
        with self.assertRaises(ValueError, msg="Supply action_gen OR action_gen_factory, not both"):
            StatefulProperty(
                Gen.just(0),
                noop_action_gen,
                action_gen_factory=noop_factory,
            )

    def test_stateful_property_factory_validates_neither(self):
        """Convenience function statefulProperty also validates missing gen."""
        with self.assertRaises(ValueError):
            statefulProperty(Gen.just(0))  # no action_gen, no action_gen_factory

    def test_stateful_property_factory_validates_both(self):
        """Convenience function statefulProperty also validates both supplied."""
        with self.assertRaises(ValueError):
            statefulProperty(
                Gen.just(0),
                Gen.just(Action(lambda s, m: None)),
                action_gen_factory=lambda s, m: Gen.just(Action(lambda s, m: None)),
            )

    # ── Named Action repr ────────────────────────────────────────────────────

    def test_action_name_appears_in_repr(self):
        """Action(name='add(3)') should display as 'add(3)' in repr."""
        a = Action(lambda s, m: None, name="add(3)")
        self.assertEqual(repr(a), "add(3)")

    def test_simple_action_name_appears_in_repr(self):
        """SimpleAction(name='push(42)') should display as 'push(42)' in repr."""
        sa = SimpleAction(lambda s: None, name="push(42)")
        self.assertEqual(repr(sa), "push(42)")

    def test_action_default_repr_without_name(self):
        """Action without a name should still produce a non-empty repr."""
        a = Action(lambda s, m: None)
        self.assertIn("Action", repr(a))

    # ── Basic factory mode: failure detection ────────────────────────────────

    def test_action_gen_factory_detects_failure(self):
        """action_gen_factory can produce an action that always fails.

        This verifies the factory path through go() works end-to-end:
        the factory is called with the current state, the generated action
        is executed, and the resulting exception is caught and re-raised as
        PropertyTestError.
        """

        class State:
            def __init__(self):
                self.value = 0

        def factory(state: State, model):
            # Returns an action that always fails regardless of state
            def run(s, _m):
                raise ValueError("factory action failed")

            return Gen.just(Action(run, name="always_fail"))

        with self.assertRaises(PropertyTestError) as ctx:
            statefulProperty(
                Gen.int(min_value=0, max_value=0).map(lambda _: State()),
                action_gen_factory=factory,
                max_actions=1,
                num_runs=1,
                seed=1,
            ).go()

        self.assertIn("factory action failed", str(ctx.exception))

    def test_action_gen_factory_basic_accumulator(self):
        """Factory-based accumulator runs without error when limit is not exceeded."""

        class State:
            def __init__(self):
                self.total = 0

        LIMIT = 1000  # effectively never fails

        def factory(state: State, model):
            return Gen.int(min_value=1, max_value=5).map(
                lambda v: Action(
                    lambda s, _m, val=v: setattr(s, "total", s.total + val),
                    name=f"add({v})",
                )
            )

        # Should not raise
        statefulProperty(
            Gen.int(min_value=0, max_value=0).map(lambda _: State()),
            action_gen_factory=factory,
            max_actions=10,
            num_runs=5,
            seed=99,
        ).go()

    # ── State isolation: initial state must not be mutated by actions ────────

    def test_initial_state_not_mutated_by_actions(self):
        """go() must deepcopy initial state before running actions.

        Without the deepcopy, the shrinkable's value is mutated and shrink
        candidates start from an already-accumulated total, making every
        single-action candidate appear to fail.  This verifies the fix by
        checking that the reported minimal CE starts from State(total=0).
        """

        class State:
            def __init__(self, total: int = 0):
                self.total = total

            def __repr__(self) -> str:
                return f"State(total={self.total})"

        LIMIT = 10  # Single add(v) with v in [1,7] ≤ 7 ≤ 10: always passes

        def make_add(v: int) -> Action:
            def run(s: State, _m) -> None:
                s.total += v
                if s.total > LIMIT:
                    raise Exception(f"total {s.total} > {LIMIT}")

            return Action(run, name=f"add({v})")

        def factory(state: State, model):
            return Gen.int(min_value=1, max_value=7).map(make_add)

        with self.assertRaises(PropertyTestError) as ctx:
            statefulProperty(
                Gen.int(min_value=0, max_value=0).map(lambda _: State()),
                action_gen_factory=factory,
                max_actions=4,
                num_runs=300,
                seed=2,
            ).go()

        err = str(ctx.exception)
        # Minimal CE must start from the clean initial state (total=0),
        # proving the deepcopy fix works: shrink candidates are not polluted
        # by mutations from the run that triggered the failure.
        self.assertIn("State(total=0)", err)
        # The minimal CE must have at least 2 actions (1-action sum ≤ 7 ≤ 10 passes)
        self.assertIn("Minimal counterexample:", err)

    # ── Phase 2b (PrefixParams) shrinking ────────────────────────────────────

    def test_action_gen_factory_prefix_params_fires(self):
        """Phase 2b (PrefixParams) fires and improves a non-last-slot action.

        Scenario: accumulator State(total=0).  Each Add(v) adds v and throws
        if total > LIMIT=10.  A single Add(v) with v in [1,7] cannot exceed
        LIMIT alone (max=7 ≤ 10), so Phase 1 cannot prune to 1 action.

        Phase 2b runs at slot 0 (a non-last slot):
          - Replays the empty prefix to reconstruct live State(0)
          - Calls factory(State(0), model) to get a fresh generator
          - Seeds it from the stored bookmark, gets a fresh shrink tree
          - Finds a smaller still-failing action for slot 0

        With seed=2 the original CE is [add(6), add(7)] (sum=13).
        After Phase 2b, slot 0 shrinks to add(4) → CE [add(4), add(7)] (sum=11).

        Asserted invariants:
          - PropertyTestError is raised (failure detected)
          - output_stream captures 'prefix params' (Phase 2b ran)
          - 'Original failing inputs' appears (shrinking improved the CE)
          - Minimal CE starts from clean State(total=0)
          - CE actions are named (contains 'add(')
        """

        class State:
            def __init__(self, total: int = 0):
                self.total = total

            def __repr__(self) -> str:
                return f"State(total={self.total})"

        LIMIT = 10

        def make_add(v: int) -> Action:
            def run(s: State, _m) -> None:
                s.total += v
                if s.total > LIMIT:
                    raise Exception(f"total {s.total} > {LIMIT}")

            return Action(run, name=f"add({v})")

        def factory(state: State, model):
            return Gen.int(min_value=1, max_value=7).map(make_add)

        class Capture:
            def __init__(self):
                self.msgs: List[str] = []

            def write(self, m: str) -> None:
                self.msgs.append(m)

        capture = Capture()

        with self.assertRaises(PropertyTestError) as ctx:
            statefulProperty(
                Gen.int(min_value=0, max_value=0).map(lambda _: State()),
                action_gen_factory=factory,
                max_actions=4,
                num_runs=300,
                seed=2,
                output_stream=capture,
            ).go()

        err = str(ctx.exception)

        # Phase 2b must have fired at least once
        pfx_msgs = [m for m in capture.msgs if "prefix params" in m]
        self.assertGreater(
            len(pfx_msgs), 0,
            "Expected at least one 'prefix params' shrink message in output_stream",
        )

        # Shrinking must have found a better CE than the original run
        self.assertIn(
            "Original failing inputs",
            err,
            "Expected 'Original failing inputs' to appear when shrinking improves the CE",
        )

        # Minimal CE starts from clean State(total=0)
        self.assertIn("State(total=0)", err)

        # Actions are named (PrefixParams regenerates from the factory → named actions)
        self.assertIn("add(", err)
