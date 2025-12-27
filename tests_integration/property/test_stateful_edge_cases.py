"""
Tests for edge cases in stateful property testing.

This module tests error handling, callbacks, and edge cases in stateful testing.
"""

import unittest
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
        """Test Action with model parameter."""
        model_state = {"count": 0}

        def action_func(state: int, model: dict):
            model["count"] += 1

        action = Action(action_func)
        prop = StatefulProperty(
            Gen.just(0),
            Gen.just(action),
            max_actions=1,
            num_runs=1,
            initial_model_gen=Gen.just(model_state),
        )
        prop.go()

        # Model should have been modified
        self.assertEqual(model_state["count"], 1)

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
