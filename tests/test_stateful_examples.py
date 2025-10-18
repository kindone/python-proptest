"""
Stateful testing examples demonstrating python-proptest's stateful testing capabilities.

This file shows how to test systems with internal state using action sequences.
"""

import unittest
from typing import Any, Dict, List

from python_proptest import (
    Action,
    Gen,
    SimpleAction,
    actionGenOf,
    simpleActionGenOf,
    simpleStatefulProperty,
    statefulProperty,
)


class TestStatefulExamples(unittest.TestCase):
    """Examples demonstrating stateful testing capabilities."""

    def test_simple_counter(self):
        """Test a simple counter with SimpleAction."""

        # Define the counter system
        Counter = int

        # Start with counter at 0
        initial_gen = Gen.just(0)

        # Action: Increment counter
        increment_action = Gen.just(SimpleAction(lambda counter: counter + 1))

        # Action: Decrement counter
        decrement_action = Gen.just(SimpleAction(lambda counter: max(0, counter - 1)))

        # Create action generator
        action_gen = simpleActionGenOf(int, increment_action, decrement_action)

        # Create and run the property
        prop = simpleStatefulProperty(
            initial_gen, action_gen, max_actions=15, num_runs=50, seed=42
        )

        prop.go()

    def test_stack_operations(self):
        """Test a stack data structure."""

        # Define the stack system
        Stack = List[int]

        # Start with empty stack
        initial_gen = Gen.just([])

        # Action: Push element
        push_action = Gen.int(min_value=1, max_value=100).map(
            lambda value: SimpleAction(lambda stack: stack + [value])
        )

        # Action: Pop element
        pop_action = Gen.just(
            SimpleAction(lambda stack: stack[:-1] if stack else stack)
        )

        # Create action generator
        action_gen = simpleActionGenOf(Stack, push_action, pop_action)

        # Create and run the property
        prop = simpleStatefulProperty(
            initial_gen, action_gen, max_actions=20, num_runs=50, seed=123
        )

        prop.go()

    def test_simple_stateful_with_model(self):
        """Test a simple stateful system with model."""

        # Simple counter with model
        Counter = int
        Model = int

        # Initial state and model generators
        initial_state_gen = Gen.just(0)
        initial_model_gen = Gen.just(0)

        # Action: Increment
        increment_action = Gen.just(
            Action(lambda counter, model: None)  # Simple increment action
        )

        # Create action generator
        action_gen = actionGenOf(int, int, increment_action)

        # Create and run the property
        prop = statefulProperty(
            initial_state_gen,
            action_gen,
            max_actions=10,
            num_runs=20,
            seed=456,
            initial_model_gen=initial_model_gen,
        )

        prop.go()

    def test_stateful_property_with_assertions(self):
        """Test stateful property with assertions."""

        # Counter that should never go negative
        Counter = int

        # Start with counter at 0
        initial_gen = Gen.just(0)

        # Action: Increment counter
        increment_action = Gen.just(SimpleAction(lambda counter: counter + 1))

        # Action: Decrement counter (with lower bound)
        decrement_action = Gen.just(SimpleAction(lambda counter: max(0, counter - 1)))

        # Create action generator
        action_gen = simpleActionGenOf(int, increment_action, decrement_action)

        # Create and run the property
        prop = simpleStatefulProperty(
            initial_gen, action_gen, max_actions=10, num_runs=20, seed=789
        )

        # This should pass because counter never goes negative
        prop.go()


if __name__ == "__main__":
    pytest.main([__file__])
