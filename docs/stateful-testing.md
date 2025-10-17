# Stateful Testing

Stateful testing involves defining a sequence of actions or commands that can be applied to a system under test and verifying properties or invariants about the system's state after executing these sequences.

`PyPropTest` provides utilities for defining state machines and generating sequences of commands to effectively test stateful systems. It allows you to model the state of your system, define actions that change the state, and automatically run sequences of these actions to find bugs.

## Core Concepts

Stateful testing in `PyPropTest` revolves around the `StatefulProperty` class, which orchestrates the test execution. Here are the key components:

1.  **Initial State (`ObjectType`)**: You need a generator (`Generator[ObjectType]`) that produces the initial state of the system under test for each test run.
2.  **Actions (`Action` or `SimpleAction`)**: Actions represent operations that modify the system's state.
    *   `SimpleAction`: Used when you don't need an explicit model. It takes a function `(obj: ObjectType) -> None`.
    *   `Action`: Used when you have a model. It takes a function `(obj: ObjectType, model: ModelType) -> None` and updates both the real object and the model.
3.  **Model (`ModelType`, Optional)**: A simplified representation of the system's state. It's used to verify the correctness of the actual system's state after each action.
4.  **Model Factory (`model_factory`, Optional)**: A function `(obj: ObjectType) -> ModelType` that creates the initial model state based on the initial object state. Required if using a model.
5.  **Action Generation (`action_gen_factory` or `simple_action_gen_factory`)**: A factory function that returns a generator for the *next* action based on the *current* state of the object (and model, if applicable).
    *   `SimpleActionGenFactory`: `(obj: ObjectType) -> Generator[SimpleAction[ObjectType]]`
    *   `ActionGenFactory`: `(obj: ObjectType, model: ModelType) -> Generator[Action[ObjectType, ModelType]]`
    `PyPropTest` provides helpers like `simple_action_gen_of` and `action_gen_of` to combine multiple action generators.

## Creating a Stateful Property

You typically use factory functions to create a `StatefulProperty`:

*   **`simple_stateful_property<ObjectType>(initial_gen, simple_action_gen_factory)`**: Use this when you don't need an explicit model. Checks are usually performed within the `SimpleAction` implementations (e.g., asserting invariants after an operation).

    ```python
    from pyproptest import Gen, simple_stateful_property, SimpleAction

    # Define the system type
    MySystem = list[int]

    # Generator for the initial state (e.g., an empty list)
    initial_gen = Gen.just([])

    # Action: Add an element
    def add_action_gen():
        return Gen.int().map(lambda val:
            SimpleAction(lambda arr: arr.append(val))
        )

    # Action: Clear the list
    def clear_action_gen():
        return Gen.just(
            SimpleAction(lambda arr: arr.clear())
        )

    # Combine action generators
    def action_factory(obj: MySystem):
        return Gen.one_of(add_action_gen(), clear_action_gen())

    # Create the property
    prop = simple_stateful_property(initial_gen, action_factory)

    # Run the test
    prop.go()
    ```

*   **`stateful_property<ObjectType, ModelType>(initial_gen, model_factory, action_gen_factory)`**: Use this when you want to maintain a separate model to verify the system's behavior against.

    ```python
    from pyproptest import Gen, stateful_property, Action

    # Define the system and model types
    MySystem = list[int]
    MyModel = dict[str, int]  # Simplified model: {"count": int}

    # Initial state generator
    initial_gen = Gen.list(Gen.int(), min_length=0, max_length=10)

    # Model factory
    def model_factory(arr: MySystem) -> MyModel:
        return {"count": len(arr)}

    # Action: Add element (updates object and model)
    def add_action_gen():
        return Gen.int().map(lambda val:
            Action(lambda arr, model: (
                arr.append(val),
                model.update({"count": model["count"] + 1})
            ))
        )

    # Action: Remove element (updates object and model)
    def remove_action_gen():
        return Gen.just(
            Action(lambda arr, model: (
                arr.pop() if arr else None,
                model.update({"count": max(0, model["count"] - 1)}) if arr else None
            ))
        )

    # Action generator factory
    def action_factory(obj: MySystem, model: MyModel):
        return Gen.one_of(add_action_gen(), remove_action_gen())

    # Create the property
    prop = stateful_property(initial_gen, model_factory, action_factory)

    # Run the test
    prop.go()
    ```

## Configuration

The `StatefulProperty` instance provides several methods for configuration:

*   `set_seed(seed)`: Sets the initial seed for the random number generator for reproducible tests.
*   `set_num_runs(num_runs)`: Sets the number of test sequences to execute (default: 100).
*   `set_min_actions(min_actions)` / `set_max_actions(max_actions)`: Sets the minimum and maximum number of actions per sequence (default: 1-100).
*   `set_verbosity(verbose)`: Enables/disables verbose logging during execution.
*   `set_on_startup(startup_func)`: Sets a function to run before each test sequence.
*   `set_on_cleanup(cleanup_func)`: Sets a function to run after each successful test sequence.
*   `set_post_check(post_check_func)`: Sets a function to run after all actions in a sequence have completed successfully. Useful for final state validation. You can also use `set_post_check_without_model((obj: ObjectType) -> None)`.

```python
from pyproptest import simple_stateful_property, Gen, SimpleAction

def test_configured_stateful_property():
    # Define a simple counter system
    Counter = int

    # Initial state
    initial_gen = Gen.just(0)

    # Actions
    def increment_action():
        return Gen.just(SimpleAction(lambda counter: counter + 1))

    def decrement_action():
        return Gen.just(SimpleAction(lambda counter: max(0, counter - 1)))

    def action_factory(counter: Counter):
        return Gen.one_of(increment_action(), decrement_action())

    # Create and configure the property
    prop = simple_stateful_property(initial_gen, action_factory)
    prop.set_seed(42)  # Reproducible tests
    prop.set_num_runs(50)  # Fewer runs for faster testing
    prop.set_min_actions(5)  # At least 5 actions per sequence
    prop.set_max_actions(20)  # At most 20 actions per sequence
    prop.set_verbosity(True)  # Enable verbose output

    # Add startup and cleanup functions
    prop.set_on_startup(lambda: print("Starting test sequence"))
    prop.set_on_cleanup(lambda: print("Test sequence completed"))

    # Add post-check to verify final state
    prop.set_post_check_without_model(lambda counter: counter >= 0)

    # Run the test
    prop.go()
```

## Advanced Stateful Testing Examples

### Testing a Stack Data Structure

```python
from pyproptest import simple_stateful_property, Gen, SimpleAction
from typing import List

def test_stack_implementation():
    # Define the stack system
    Stack = List[int]

    # Initial state: empty stack
    initial_gen = Gen.just([])

    # Action: Push an element
    def push_action():
        return Gen.int().map(lambda val:
            SimpleAction(lambda stack: stack.append(val))
        )

    # Action: Pop an element
    def pop_action():
        return Gen.just(
            SimpleAction(lambda stack: stack.pop() if stack else None)
        )

    # Action: Peek at the top element
    def peek_action():
        return Gen.just(
            SimpleAction(lambda stack: stack[-1] if stack else None)
        )

    # Action generator factory
    def action_factory(stack: Stack):
        # Only allow pop/peek if stack is not empty
        if not stack:
            return push_action()
        else:
            return Gen.one_of(push_action(), pop_action(), peek_action())

    # Create the property
    prop = simple_stateful_property(initial_gen, action_factory)
    prop.set_post_check_without_model(lambda stack: len(stack) >= 0)

    # Run the test
    prop.go()
```

### Testing a Bank Account with Model

```python
from pyproptest import stateful_property, Gen, Action
from typing import Dict, Any

def test_bank_account():
    # Define the system and model types
    BankAccount = Dict[str, Any]  # {"balance": float, "transactions": List[float]}
    AccountModel = Dict[str, Any]  # {"balance": float, "transaction_count": int}

    # Initial state generator
    initial_gen = Gen.dict(
        Gen.just("balance"),
        Gen.float(min_value=0.0, max_value=1000.0),
        min_size=1,
        max_size=1
    ).map(lambda d: {**d, "transactions": []})

    # Model factory
    def model_factory(account: BankAccount) -> AccountModel:
        return {
            "balance": account["balance"],
            "transaction_count": len(account["transactions"])
        }

    # Action: Deposit money
    def deposit_action():
        return Gen.float(min_value=0.01, max_value=100.0).map(lambda amount:
            Action(lambda account, model: (
                account.update({
                    "balance": account["balance"] + amount,
                    "transactions": account["transactions"] + [amount]
                }),
                model.update({
                    "balance": model["balance"] + amount,
                    "transaction_count": model["transaction_count"] + 1
                })
            ))
        )

    # Action: Withdraw money
    def withdraw_action():
        return Gen.float(min_value=0.01, max_value=100.0).map(lambda amount:
            Action(lambda account, model: (
                account.update({
                    "balance": max(0, account["balance"] - amount),
                    "transactions": account["transactions"] + [-amount]
                }),
                model.update({
                    "balance": max(0, model["balance"] - amount),
                    "transaction_count": model["transaction_count"] + 1
                })
            ))
        )

    # Action generator factory
    def action_factory(account: BankAccount, model: AccountModel):
        return Gen.one_of(deposit_action(), withdraw_action())

    # Create the property
    prop = stateful_property(initial_gen, model_factory, action_factory)

    # Add post-check to verify model consistency
    def post_check(account: BankAccount, model: AccountModel):
        assert account["balance"] == model["balance"]
        assert len(account["transactions"]) == model["transaction_count"]
        assert account["balance"] >= 0

    prop.set_post_check(post_check)
    prop.go()
```

## Shrinking in Stateful Testing

If a test sequence fails (an action throws an error or the `post_check` fails), `PyPropTest` automatically tries to **shrink** the test case to find a minimal reproduction. It does this by:

1.  **Shrinking the Action Sequence**: Trying shorter sequences or simpler actions.
2.  **Shrinking the Initial State**: Trying simpler versions of the initial state generated by `initial_gen`.

The goal is to present the simplest possible initial state and sequence of actions that trigger the failure, making debugging easier. The error message will report the shrunk arguments if successful.

```python
from pyproptest import simple_stateful_property, Gen, SimpleAction

def test_failing_stateful_property():
    # This will demonstrate shrinking in action
    Counter = int

    initial_gen = Gen.just(0)

    def increment_action():
        return Gen.just(SimpleAction(lambda counter: counter + 1))

    def decrement_action():
        return Gen.just(SimpleAction(lambda counter: counter - 1))

    def action_factory(counter: Counter):
        return Gen.one_of(increment_action(), decrement_action())

    prop = simple_stateful_property(initial_gen, action_factory)

    # This will fail and show shrinking in action
    prop.set_post_check_without_model(lambda counter: counter >= 0)
    prop.go()
```

Stateful testing is particularly powerful for testing systems with complex state transitions, concurrent operations, or systems where the order of operations matters. It helps uncover race conditions, state inconsistencies, and other subtle bugs that are difficult to find with traditional unit tests.
