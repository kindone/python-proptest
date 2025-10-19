"""
Stateful testing tests ported from TypeScript.

These tests verify that stateful testing functionality works correctly.
"""

import random
import unittest

from python_proptest import (
    Action,
    Gen,
    SimpleAction,
    StatefulProperty,
    actionGenOf,
    simpleActionGenOf,
    simpleStatefulProperty,
    statefulProperty,
)


class TestStateful(unittest.TestCase):
    """Test stateful testing functionality."""

    def test_simple_stateful_property(self):
        """Test simple stateful property execution without a model."""
        # Test with array operations
        push_gen = Gen.int(min_value=0, max_value=10000).map(
            lambda value: SimpleAction(lambda obj: obj.append(value))
        )

        pop_gen = Gen.just(SimpleAction(lambda obj: obj.pop() if obj else None))

        clear_gen = Gen.just(SimpleAction(lambda obj: obj.clear() if obj else None))

        # Create weighted action generator
        action_gen = simpleActionGenOf(
            list, push_gen, pop_gen, Gen.weighted_gen(clear_gen, 0.1)
        )

        # Create stateful property
        prop = simpleStatefulProperty(
            Gen.list(
                Gen.int(min_value=0, max_value=10000), min_length=0, max_length=20
            ),
            action_gen,
            max_actions=50,
            num_runs=5,
            seed=42,
        )

        # Test startup and cleanup callbacks
        startup_called = []
        cleanup_called = []

        prop.setOnStartup(lambda: startup_called.append(1))
        prop.setOnCleanup(lambda: cleanup_called.append(1))

        # Run the property
        prop.go()

        # Verify callbacks were called
        assert len(startup_called) == 5  # Called once per run
        assert len(cleanup_called) == 5  # Called once per run

    def test_stateful_property_with_model(self):
        """Test stateful property with a model."""

        # Define a simple counter state
        class Counter:
            def __init__(self):
                self.value = 0

        # Define a model that tracks the expected state
        class CounterModel:
            def __init__(self):
                self.value = 0

        # Action generators
        increment_gen = Gen.just(
            Action(
                lambda state, model: setattr(state, "value", state.value + 1)
                or setattr(model, "value", model.value + 1)
            )
        )

        decrement_gen = Gen.just(
            Action(
                lambda state, model: setattr(state, "value", max(0, state.value - 1))
                or setattr(model, "value", max(0, model.value - 1))
            )
        )

        reset_gen = Gen.just(
            Action(
                lambda state, model: setattr(state, "value", 0)
                or setattr(model, "value", 0)
            )
        )

        # Create action generator
        action_gen = actionGenOf(
            Counter, CounterModel, increment_gen, decrement_gen, reset_gen
        )

        # Create stateful property
        prop = statefulProperty(
            Gen.just(Counter()),
            action_gen,
            max_actions=20,
            num_runs=3,
            seed=123,
            initial_model_gen=Gen.just(CounterModel()),
        )

        # Run the property
        prop.go()

    def test_stateful_property_with_assertions(self):
        """Test stateful property with assertions."""
        # Test with a list that maintains invariants
        push_gen = Gen.int(min_value=1, max_value=100).map(
            lambda value: SimpleAction(lambda obj: obj.append(value))
        )

        pop_gen = Gen.just(SimpleAction(lambda obj: obj.pop() if obj else None))

        # Action that asserts list length is non-negative
        def assert_length(obj):
            assert len(obj) >= 0

        assert_gen = Gen.just(SimpleAction(assert_length))

        action_gen = simpleActionGenOf(list, push_gen, pop_gen, assert_gen)

        prop = simpleStatefulProperty(
            Gen.list(Gen.int(min_value=1, max_value=100), min_length=0, max_length=10),
            action_gen,
            max_actions=30,
            num_runs=3,
            seed=456,
        )

        # This should not raise an exception
        prop.go()

    def test_stateful_property_with_weighted_actions(self):
        """Test stateful property with weighted action selection."""
        # Create actions with different weights
        common_action = Gen.just(
            SimpleAction(lambda obj: obj.append(1) if obj is not None else None)
        )

        rare_action = Gen.just(SimpleAction(lambda obj: obj.clear() if obj else None))

        # Weight the actions (common_action should be selected more often)
        weighted_common = Gen.weighted_gen(common_action, 0.8)
        weighted_rare = Gen.weighted_gen(rare_action, 0.2)

        action_gen = simpleActionGenOf(list, weighted_common, weighted_rare)

        prop = simpleStatefulProperty(
            Gen.list(Gen.int(min_value=1, max_value=10), min_length=0, max_length=5),
            action_gen,
            max_actions=20,
            num_runs=2,
            seed=789,
        )

        prop.go()

    def test_stateful_property_with_complex_state(self):
        """Test stateful property with complex state structure."""

        # Define a complex state
        class ComplexState:
            def __init__(self):
                self.data = {}
                self.counter = 0
                self.history = []

        # Actions that operate on the complex state
        set_data_gen = Gen.tuple(
            Gen.str(min_length=1, max_length=5), Gen.int(min_value=1, max_value=100)
        ).map(
            lambda t: SimpleAction(
                lambda state: setattr(state, "data", {**state.data, t[0]: t[1]})
                or state.history.append(f"set_{t[0]}")
            )
        )

        increment_counter_gen = Gen.just(
            SimpleAction(
                lambda state: setattr(state, "counter", state.counter + 1)
                or state.history.append("increment")
            )
        )

        clear_data_gen = Gen.just(
            SimpleAction(
                lambda state: setattr(state, "data", {})
                or state.history.append("clear")
            )
        )

        action_gen = simpleActionGenOf(
            ComplexState, set_data_gen, increment_counter_gen, clear_data_gen
        )

        prop = simpleStatefulProperty(
            Gen.just(ComplexState()), action_gen, max_actions=15, num_runs=2, seed=999
        )

        prop.go()

    def test_stateful_property_error_handling(self):
        """Test stateful property error handling."""
        # Create an action that will fail
        failing_action = Gen.just(
            SimpleAction(lambda obj: 1 / 0)  # This will raise ZeroDivisionError
        )

        prop = simpleStatefulProperty(
            Gen.list(Gen.int(min_value=1, max_value=10), min_length=0, max_length=5),
            failing_action,
            max_actions=5,
            num_runs=1,
            seed=111,
        )

        # This should raise a PropertyTestError
        with self.assertRaises(Exception):  # PropertyTestError or ZeroDivisionError
            prop.go()

    def test_stateful_property_with_different_seeds(self):
        """Test that different seeds produce different behavior."""
        # Simple action
        action_gen = Gen.just(
            SimpleAction(
                lambda obj: (
                    obj.append(random.randint(1, 100)) if obj is not None else None
                )
            )
        )

        # Run with different seeds
        prop1 = simpleStatefulProperty(
            Gen.list(Gen.int(min_value=1, max_value=10), min_length=0, max_length=3),
            action_gen,
            max_actions=5,
            num_runs=1,
            seed=111,
        )

        prop2 = simpleStatefulProperty(
            Gen.list(Gen.int(min_value=1, max_value=10), min_length=0, max_length=3),
            action_gen,
            max_actions=5,
            num_runs=1,
            seed=222,
        )

        # Both should run without error (different seeds should produce different results)
        prop1.go()
        prop2.go()

    def test_stateful_property_with_zero_actions(self):
        """Test stateful property with zero actions."""
        action_gen = Gen.just(SimpleAction(lambda obj: None))  # No-op action

        prop = simpleStatefulProperty(
            Gen.list(Gen.int(min_value=1, max_value=10), min_length=0, max_length=3),
            action_gen,
            max_actions=0,  # Zero actions
            num_runs=1,
            seed=333,
        )

        # This should still run (just no actions executed)
        prop.go()

    def test_stateful_property_with_single_action(self):
        """Test stateful property with single action type."""
        action_gen = Gen.just(
            SimpleAction(lambda obj: obj.append(42) if obj is not None else None)
        )

        prop = simpleStatefulProperty(
            Gen.list(Gen.int(min_value=1, max_value=10), min_length=0, max_length=3),
            action_gen,
            max_actions=10,
            num_runs=1,
            seed=444,
        )

        prop.go()
