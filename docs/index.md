# PyPropTest

`PyPropTest` is a property-based testing (PBT) framework for Python, drawing inspiration from libraries such as Haskell's QuickCheck and Python's Hypothesis. Property-based testing shifts the focus from example-based verification to defining universal *properties* or *invariants* that must hold true for an input domain.

PyPropTest provides seamless integration with pytest through the `@for_all` decorator, automatically detecting pytest context and adapting behavior accordingly.

Instead of manually crafting test cases for specific inputs, PBT allows you to describe the *domain* of inputs your function expects and the *general characteristics* of the output (e.g., `add(a, b)` should always be greater than or equal to `a` and `b` if they are non-negative). PBT then generates hundreds or thousands of varied inputs, searching for edge cases or unexpected behaviors that violate your defined properties. This approach significantly increases test coverage and the likelihood of finding subtle bugs.

The core workflow involves:

1.  **Defining a property:** A function that takes generated inputs and asserts an expected invariant. See [Properties](properties.md).
2.  **Specifying generators:** Mechanisms for creating random data conforming to certain types or constraints, often built by composing simpler generators using **combinators**. See [Generators](generators.md) and [Combinators](combinators.md).
3.  **Execution:** `PyPropTest` automatically runs the property function against numerous generated inputs (typically 100+).
4.  **Shrinking:** If a test case fails (the property returns `false` or throws), `PyPropTest` attempts to find a minimal counterexample by simplifying the failing input. See [Shrinking](shrinking.md).

Consider verifying a round-trip property for a custom parser/serializer:

```python
import json
from pyproptest import run_for_all, Gen

def test_serialize_parse_roundtrip():
    """Test that serializing and parsing preserves data."""
    # Generator for keys (non-empty strings without special characters)
    key_gen = Gen.str(min_length=1, max_length=10).filter(
        lambda s: s and '&' not in s and '=' not in s
    )
    # Generator for arbitrary string values
    value_gen = Gen.str(min_length=0, max_length=10)
    # Generator for dictionaries with our specific keys and values
    data_object_gen = Gen.dict(key_gen, value_gen, min_size=0, max_size=10)

    # Simple lambda-based property - perfect for run_for_all
    result = run_for_all(
        lambda original_data: json.loads(json.dumps(original_data)) == original_data,
        data_object_gen
    )
    assert result is True
```

This PBT approach facilitates the discovery of edge cases and intricate bugs that might be neglected by traditional, example-driven testing methodologies.

## Getting Started

### Installation

To add `PyPropTest` to your project, run the following command:

```bash
pip install pyproptest
```

For development dependencies:

```bash
pip install pyproptest[dev]
```

## Core Concepts and Features

Understanding these key components will help you use `PyPropTest` effectively:

*   **[Generators](generators.md)**: Produce random data of various types (primitives, containers) according to specified constraints (e.g., `Gen.int()`, `Gen.list(...)`). Learn how to create the basic building blocks of your test data.

*   **[Combinators](combinators.md)**: Modify or combine existing generators to create new ones. Discover techniques to constraint, combine, and transform generators for complex data structures.

*   **[Properties (`Property`, `run_for_all`)](properties.md)**: Express conditions or invariants that should hold true for generated data. `PyPropTest` runs these properties against many generated examples using the `run_for_all` function or `Property` class methods. Understand how to define the invariants your code should satisfy and how to run tests.

*   **[Shrinking](shrinking.md)**: When a property fails, `PyPropTest` attempts to find a minimal counterexample by simplifying the failing input using logic associated with the generated value (often via a `Shrinkable` structure). See how `PyPropTest` helps pinpoint failures.

*   **[Stateful Testing](stateful-testing.md)**: Go beyond simple input-output functions and test systems with internal state by generating sequences of operations or commands. Learn how to model and verify stateful behaviors.

## API Overview

PyPropTest provides two main approaches for property-based testing:

### 1. Function-based Approach (Recommended for pytest)

```python
from pyproptest import run_for_all, Gen

def test_addition_commutativity():
    def property_func(x: int, y: int):
        return x + y == y + x
    
    run_for_all(property_func, Gen.int(), Gen.int())
```

### 2. Decorator-based Approach

```python
from pyproptest import for_all, integers

@for_all(integers(), integers())
def test_addition_commutativity(x: int, y: int):
    assert x + y == y + x

# Run the test
test_addition_commutativity()
```

### 3. Pytest Integration (Automatic Randomization)

The `@for_all` decorator provides seamless pytest integration with **automatic test randomization**. Simply add the decorator to your test methods, and PyPropTest will automatically generate hundreds of random test cases for each test run:

```python
import pytest
from pyproptest import for_all, integers, text

class TestMathProperties:
    @for_all(integers(), integers())
    def test_addition_commutativity(self, x: int, y: int):
        """Test that addition is commutative - automatically runs 100+ random cases!"""
        assert x + y == y + x
    
    @for_all(integers(), integers())
    def test_multiplication_associativity(self, x: int, y: int, z: int):
        """Test that multiplication is associative."""
        assert (x * y) * z == x * (y * z)

class TestStringProperties:
    @for_all(text(), text())
    def test_string_concatenation(self, s1: str, s2: str):
        """Test string concatenation properties."""
        result = s1 + s2
        assert len(result) == len(s1) + len(s2)
        assert result.startswith(s1)
        assert result.endswith(s2)
```

**Key Benefits of Pytest Integration:**
- **Zero Configuration**: Just add `@for_all()` decorator and run `pytest` as usual
- **Automatic Randomization**: Each test method runs with 100+ randomly generated inputs
- **Pytest Discovery**: Tests are automatically discovered by pytest
- **Standard Output**: Failures appear as normal pytest failures with minimal counterexamples
- **IDE Support**: Full type hints and parameter completion in your IDE

**Running with pytest:**
```bash
# Run all property-based tests
pytest

# Run specific test class
pytest tests/test_math_properties.py::TestMathProperties

# Run with verbose output to see generated test cases
pytest -v

# Run with coverage
pytest --cov=pyproptest
```


## Choosing the Right Approach

PyPropTest provides two main approaches for defining property tests. Choose based on your needs:

### Use `run_for_all` for Simple Lambda-Based Tests

Perfect for simple property checks that can be expressed as lambdas:

```python
from pyproptest import run_for_all, Gen

def test_simple_properties():
    # Type checks
    result = run_for_all(
        lambda x: isinstance(x, int),
        Gen.int(min_value=0, max_value=100)
    )
    
    # Range validations
    result = run_for_all(
        lambda x: 0 <= x <= 100,
        Gen.int(min_value=0, max_value=100)
    )
    
    # Simple assertions
    result = run_for_all(
        lambda lst: all(isinstance(x, int) for x in lst),
        Gen.list(Gen.int())
    )
```

### Use `@for_all` for Complex Function-Based Tests

Perfect for complex assertions that benefit from explicit parameter signatures:

```python
from pyproptest import for_all, integers, text

@for_all(integers(), integers())
def test_complex_math_property(x: int, y: int):
    """Test complex mathematical property with multiple conditions."""
    result = x * y + x + y
    assert result >= x
    assert result >= y
    assert result % 2 == (x + y) % 2

@for_all(text(), text())
def test_string_operations(s1: str, s2: str):
    """Test string operations with multiple assertions."""
    combined = s1 + s2
    assert len(combined) == len(s1) + len(s2)
    assert combined.startswith(s1)
    assert combined.endswith(s2)
```

### Guidelines

- **Use `run_for_all`** for simple property checks that can be expressed as lambdas
- **Use `@for_all`** for complex assertions that benefit from explicit function signatures
- **Use `run_for_all`** for seed-based reproducibility testing
- **Use `@for_all`** for tests with complex generator transformations

All approaches provide the same functionality - choose based on your testing framework and preferences.

## Pytest Integration: The Easiest Way to Get Started

If you're using pytest (which most Python projects do), the `@for_all` decorator is the **recommended approach** for property-based testing. It provides the smoothest integration with your existing test suite:

### Why Use the Pytest Decorator API?

1. **Drop-in Integration**: Works with your existing pytest setup without any configuration
2. **Automatic Test Discovery**: pytest automatically finds and runs your property-based tests
3. **Familiar Workflow**: Use the same `pytest` commands you're already using
4. **IDE Integration**: Full support for debugging, breakpoints, and parameter inspection
5. **Standard Output**: Test failures appear as normal pytest failures with clear error messages

### Complete Example: Testing a Custom Function

```python
import pytest
from pyproptest import for_all, integers, text, lists

def my_sort_function(items):
    """A custom sorting function we want to test."""
    return sorted(items)

class TestMySortFunction:
    @for_all(lists(integers()))
    def test_sort_preserves_length(self, items):
        """Sorting should preserve the number of elements."""
        sorted_items = my_sort_function(items)
        assert len(sorted_items) == len(items)
    
    @for_all(lists(integers()))
    def test_sort_is_sorted(self, items):
        """Sorted result should be in ascending order."""
        sorted_items = my_sort_function(items)
        for i in range(len(sorted_items) - 1):
            assert sorted_items[i] <= sorted_items[i + 1]
    
    @for_all(lists(integers()))
    def test_sort_preserves_elements(self, items):
        """Sorting should preserve all original elements."""
        sorted_items = my_sort_function(items)
        assert set(sorted_items) == set(items)

# Just run: pytest tests/test_my_sort_function.py
# Each test method will automatically run with 100+ random inputs!
```

### Advanced Pytest Features

You can combine PyPropTest with other pytest features:

```python
import pytest
from pyproptest import for_all, integers

class TestAdvancedFeatures:
    @for_all(integers(), integers())
    @pytest.mark.slow  # Mark as slow test
    def test_expensive_operation(self, x, y):
        """This test might take longer due to complexity."""
        result = expensive_operation(x, y)
        assert result is not None
    
    @for_all(integers())
    @pytest.mark.parametrize("multiplier", [2, 3, 5])  # Combine with parametrize
    def test_with_parametrize(self, x, multiplier):
        """Combine property-based testing with parametrized tests."""
        result = x * multiplier
        assert result % multiplier == 0
```

For more details on pytest integration, see [Pytest Integration](pytest-integration.md) and [Pytest Best Practices](pytest-best-practices.md).