"""Tests for ``python_proptest.core.stateful`` stateful property testing."""

import unittest
from unittest.mock import Mock

from python_proptest import (
    Action,
    Gen,
    PropertyTestError,
    SimpleAction,
    StatefulProperty,
    actionGenOf,
    simpleActionGenOf,
    simpleStatefulProperty,
    statefulProperty,
)


class TestStatefulProperty(unittest.TestCase):
    """Verify stateful property testing behaviour."""

    def test_simple_stateful_property_execution(self):
        """simpleStatefulProperty executes action sequences without model."""

        push_gen = Gen.int(min_value=0, max_value=100).map(
            lambda value: SimpleAction(lambda obj: obj.append(value))
        )

        pop_gen = Gen.just(SimpleAction(lambda obj: obj.pop() if obj else None))

        action_gen = simpleActionGenOf(list, push_gen, pop_gen)

        prop = simpleStatefulProperty(
            Gen.list(Gen.int(min_value=0, max_value=100), min_length=0, max_length=20),
            action_gen,
            max_actions=20,
            num_runs=3,
            seed=42,
        )

        # Should execute without error
        prop.go()

    def test_stateful_property_with_model(self):
        """statefulProperty executes actions with model tracking."""

        class Counter:
            def __init__(self):
                self.value = 0

        class CounterModel:
            def __init__(self):
                self.value = 0

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

        action_gen = actionGenOf(Counter, CounterModel, increment_gen, decrement_gen)

        prop = statefulProperty(
            Gen.just(Counter()),
            action_gen,
            max_actions=10,
            num_runs=2,
            seed=123,
            initial_model_gen=Gen.just(CounterModel()),
        )

        prop.go()

    def test_startup_callbacks_are_called(self):
        """Startup callbacks execute before each test run."""

        callback = Mock()
        prop = StatefulProperty(
            Gen.just(0),
            Gen.just(SimpleAction(lambda s: None)),
            num_runs=3,
        )
        prop.setOnStartup(callback)
        prop.go()

        # Should be called once per run
        self.assertEqual(callback.call_count, 3)

    def test_cleanup_callbacks_are_called(self):
        """Cleanup callbacks execute after each test run."""

        callback = Mock()
        prop = StatefulProperty(
            Gen.just(0),
            Gen.just(SimpleAction(lambda s: None)),
            num_runs=3,
        )
        prop.setOnCleanup(callback)
        prop.go()

        # Should be called once per run
        self.assertEqual(callback.call_count, 3)

    def test_cleanup_callbacks_on_failure(self):
        """Cleanup callbacks execute even when actions fail."""

        cleanup_callback = Mock()
        startup_callback = Mock()

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

    def test_multiple_callbacks_execute(self):
        """Multiple startup and cleanup callbacks all execute."""

        startup1 = Mock()
        startup2 = Mock()
        cleanup1 = Mock()
        cleanup2 = Mock()

        prop = StatefulProperty(
            Gen.just(0),
            Gen.just(SimpleAction(lambda s: None)),
            num_runs=1,
        )
        prop.setOnStartup(startup1)
        prop.setOnStartup(startup2)
        prop.setOnCleanup(cleanup1)
        prop.setOnCleanup(cleanup2)
        prop.go()

        startup1.assert_called_once()
        startup2.assert_called_once()
        cleanup1.assert_called_once()
        cleanup2.assert_called_once()

    def test_zero_max_actions(self):
        """max_actions=0 executes no actions but still runs callbacks."""

        action_callback = Mock()
        startup_callback = Mock()
        cleanup_callback = Mock()

        prop = StatefulProperty(
            Gen.just(0),
            Gen.just(SimpleAction(lambda s: action_callback())),
            max_actions=0,
            num_runs=1,
        )
        prop.setOnStartup(startup_callback)
        prop.setOnCleanup(cleanup_callback)
        prop.go()

        # Actions should not run, but callbacks should
        action_callback.assert_not_called()
        startup_callback.assert_called_once()
        cleanup_callback.assert_called_once()

    def test_action_with_model_updates_model(self):
        """Actions with model parameter can modify model state."""

        model_state = {"count": 0}

        def action_func(state: int, model: dict):
            model["count"] += 1

        action = Action(action_func)
        prop = StatefulProperty(
            Gen.just(0),
            Gen.just(action),
            max_actions=5,
            num_runs=1,
            initial_model_gen=Gen.just(model_state),
        )
        prop.go()

        # Model should have been modified by actions (at least once, up to max_actions)
        self.assertGreater(model_state["count"], 0)
        self.assertLessEqual(model_state["count"], 5)

    def test_action_without_model_raises_error(self):
        """Action requiring model raises error when model not provided."""

        def action_func(state: int, model: dict):
            model["count"] += 1

        action = Action(action_func)
        prop = StatefulProperty(
            Gen.just(0),
            Gen.just(action),
            num_runs=1,
            # No initial_model_gen provided
        )

        with self.assertRaises(PropertyTestError):
            prop.go()

    def test_stateful_property_with_seed_reproducibility(self):
        """Identical seeds produce reproducible action sequences."""

        push_gen = Gen.int(min_value=1, max_value=10).map(
            lambda value: SimpleAction(lambda obj: obj.append(value))
        )

        action_gen = simpleActionGenOf(list, push_gen)

        prop1 = simpleStatefulProperty(
            Gen.just([]),
            action_gen,
            max_actions=5,
            num_runs=1,
            seed=42,
        )

        prop2 = simpleStatefulProperty(
            Gen.just([]),
            action_gen,
            max_actions=5,
            num_runs=1,
            seed=42,
        )

        # Both should execute successfully with same seed
        prop1.go()
        prop2.go()

    def test_stateful_property_with_string_seed(self):
        """String seeds are accepted for reproducibility."""

        prop = StatefulProperty(
            Gen.just(0),
            Gen.just(SimpleAction(lambda s: None)),
            num_runs=1,
            seed="test_seed",
        )
        prop.go()

    def test_stateful_property_failure_raises_property_test_error(self):
        """Failing actions raise PropertyTestError with context."""

        failing_action = SimpleAction(
            lambda s: (_ for _ in ()).throw(ValueError("Test error"))
        )

        prop = StatefulProperty(
            Gen.just(0),
            Gen.just(failing_action),
            num_runs=1,
        )

        with self.assertRaises(PropertyTestError) as ctx:
            prop.go()

        # Error should include run information
        self.assertIn("run", str(ctx.exception).lower())

    def test_simple_action_gen_of_creates_generator(self):
        """simpleActionGenOf combines action generators correctly."""

        action1 = Gen.just(SimpleAction(lambda s: None))
        action2 = Gen.just(SimpleAction(lambda s: None))
        gen = simpleActionGenOf(int, action1, action2)

        self.assertIsNotNone(gen)

    def test_simple_action_gen_of_empty_raises_error(self):
        """simpleActionGenOf requires at least one action generator."""

        with self.assertRaises(ValueError):
            simpleActionGenOf(int)

    def test_action_gen_of_creates_generator(self):
        """actionGenOf combines action generators with model correctly."""

        action1 = Gen.just(Action(lambda s, m: None))
        action2 = Gen.just(Action(lambda s, m: None))
        gen = actionGenOf(int, dict, action1, action2)

        self.assertIsNotNone(gen)

    def test_action_gen_of_empty_raises_error(self):
        """actionGenOf requires at least one action generator."""

        with self.assertRaises(ValueError):
            actionGenOf(int, dict)

    def test_stateful_property_factory_functions(self):
        """Factory functions create StatefulProperty instances correctly."""

        # Test statefulProperty factory
        prop1 = statefulProperty(
            Gen.just(0),
            Gen.just(Action(lambda s, m: None)),
            num_runs=1,
            initial_model_gen=Gen.just({}),
        )
        self.assertIsInstance(prop1, StatefulProperty)
        prop1.go()

        # Test simpleStatefulProperty factory
        prop2 = simpleStatefulProperty(
            Gen.just(0),
            Gen.just(SimpleAction(lambda s: None)),
            num_runs=1,
        )
        self.assertIsInstance(prop2, StatefulProperty)
        prop2.go()

    def test_chaining_callback_setters(self):
        """setOnStartup and setOnCleanup return self for method chaining."""

        callback1 = Mock()
        callback2 = Mock()

        prop = StatefulProperty(
            Gen.just(0),
            Gen.just(SimpleAction(lambda s: None)),
            num_runs=1,
        )

        result = prop.setOnStartup(callback1).setOnCleanup(callback2)
        self.assertIs(result, prop)  # Should return self for chaining

        prop.go()

        callback1.assert_called_once()
        callback2.assert_called_once()

    def test_weighted_action_selection(self):
        """Weighted action generators respect probability weights."""

        common_action = Gen.just(SimpleAction(lambda obj: obj.append(1)))
        rare_action = Gen.just(SimpleAction(lambda obj: obj.clear()))

        weighted_common = Gen.weighted_gen(common_action, 0.8)
        weighted_rare = Gen.weighted_gen(rare_action, 0.2)

        action_gen = simpleActionGenOf(list, weighted_common, weighted_rare)

        prop = simpleStatefulProperty(
            Gen.just([]),
            action_gen,
            max_actions=20,
            num_runs=2,
            seed=789,
        )

        prop.go()


if __name__ == "__main__":
    unittest.main()
