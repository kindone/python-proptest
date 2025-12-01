# python-proptest

`python-proptest` is a property-based testing (PBT) framework ported from for `cppproptest`, drawing inspiration from libraries such as Haskell's QuickCheck and Python's Hypothesis. Property-based testing shifts the focus from example-based verification to defining universal *properties* or *invariants* that must hold true for an input domain.

python-proptest provides seamless integration with `unittest` or `pytest` through the convenient decorators like `@for_all`, automatically detecting pytest context and adapting behavior accordingly.

Instead of manually crafting test cases for specific inputs, PBT allows you to describe the *domain* of inputs your function expects and the *general characteristics* of the output (e.g., `add(a, b)` should always be greater than or equal to `a` and `b` if they are non-negative). PBT then generates hundreds or thousands of varied inputs, searching for edge cases or unexpected behaviors that violate your defined properties. This approach significantly increases test coverage and the likelihood of finding subtle bugs.

The core workflow involves:

1.  **Defining a property:** A function that takes generated inputs and asserts an expected invariant. See [Properties](properties.md).
2.  **Specifying generators:** Mechanisms for creating random data conforming to certain types or constraints, often built by composing simpler generators using **combinators**. See [Generators](generators.md) and [Combinators](combinators.md).
3.  **Execution:** `python-proptest` automatically runs the property function against numerous generated inputs (typically 100+).
4.  **Shrinking:** If a test case fails (the property returns `false` or throws), `python-proptest` attempts to find a minimal counterexample by simplifying the failing input. See [Shrinking](shrinking.md).
5.  **Enhanced testing:** Use decorators like `@example`, `@settings`, and `@matrix` for specific test cases, configuration, and exhaustive testing. See [Decorators](decorators.md).

Consider verifying a round-trip property for a custom parser/serializer:

```python
import json
from python_proptest import run_for_all, Gen

"""Test that serializing and parsing preserves data."""
# Generator for keys (non-empty strings without special characters)
key_gen = Gen.str(min_length=1, max_length=10).filter(
    lambda s: s and '&' not in s and '=' not in s
)
# Generator for arbitrary string values
value_gen = Gen.str(min_length=0, max_length=10)
# Generator for dictionaries with our specific keys and values
data_object_gen = Gen.dict(key_gen, value_gen, min_size=0, max_size=10)

# Simple lambda-based property is suitable for run_for_all
result = run_for_all(
    lambda original_data: json.loads(json.dumps(original_data)) == original_data,
    data_object_gen
)
assert result is True
```

This PBT approach facilitates the discovery of edge cases and intricate bugs that might be neglected by traditional, example-driven testing methodologies.

## Getting Started

### Installation

To add `python-proptest` to your project, run the following command:

```bash
pip install python-proptest
```

For development dependencies:

```bash
pip install python-proptest[dev]
```

## Core Concepts and Features

Understanding these key components will help you use `python-proptest` effectively:

*   **[Generators](generators.md)**: Produce random data of various types (primitives, containers) according to specified constraints (e.g., `Gen.int()`, `Gen.list(...)`). Learn how to create the basic building blocks of your test data.

*   **[Combinators](combinators.md)**: Modify or combine existing generators to create new ones. Discover techniques to constraint, combine, and transform generators for complex data structures.

*   **[Properties (`Property`, `run_for_all`)](properties.md)**: Express conditions or invariants that should hold true for generated data. `python-proptest` runs these properties against many generated examples using the `run_for_all` function or `Property` class methods. Understand how to define the invariants your code should satisfy and how to run tests.

*   **[Shrinking](shrinking.md)**: When a property fails, `python-proptest` attempts to find a minimal counterexample by simplifying the failing input using logic associated with the generated value (often via a `Shrinkable` structure). See how `python-proptest` helps pinpoint failures.

*   **[Stateful Testing](stateful-testing.md)**: Go beyond simple input-output functions and test systems with internal state by generating sequences of operations or commands. Learn how to model and verify stateful behaviors.

## API Overview

python-proptest provides two main approaches for property-based testing:


### Available Generators

**Primitive Generators:**

- `Gen.int(min_value, max_value)` - Random integers
- `Gen.float(min_value, max_value)` - Random floats
- `Gen.bool(true_prob)` - Random booleans with configurable probability
- `Gen.str(min_length, max_length)` - Random strings (ASCII)
- `Gen.ascii_string(min_length, max_length)` - ASCII strings (0-127)
- `Gen.printable_ascii_string(min_length, max_length)` - Printable ASCII strings (32-126)
- `Gen.unicode_string(min_length, max_length)` - Unicode strings
- `Gen.ascii_char()` - ASCII character codes (0-127)
- `Gen.unicode_char()` - Unicode character codes (avoiding surrogate pairs)
- `Gen.printable_ascii_char()` - Printable ASCII character codes (32-126)
- `Gen.in_range(min_value, max_value)` - Integers in range [min, max) (exclusive)
- `Gen.interval(min_value, max_value)` - Integers in range [min, max] (inclusive)
- `Gen.integers(min_value, max_value)` - Alias for interval

**Container Generators:**

- `Gen.list(element_gen, min_length, max_length)` - Lists
- `Gen.unique_list(element_gen, min_length, max_length)` - Lists with unique elements (sorted)
- `Gen.set(element_gen, min_size, max_size)` - Sets
- `Gen.dict(key_gen, value_gen, min_size, max_size)` - Dictionaries
- `Gen.tuple(*generators)` - Fixed-size tuples

**Special Generators:**

- `Gen.just(value)` - Always generates the same value
- `Gen.lazy(func)` - Defers evaluation until generation
- `Gen.construct(Type, *generators)` - Creates class instances

**Dependent Generation Combinators:**

- `Gen.chain(base_gen, gen_factory)` / `generator.chain(gen_factory)` - Creates dependent tuples
- `Gen.aggregate(initial_gen, gen_factory, min_size, max_size)` / `generator.aggregate(...)` - Generates list with dependent elements
- `Gen.accumulate(initial_gen, gen_factory, min_size, max_size)` / `generator.accumulate(...)` - Generates final value after dependent steps

**Selection Combinators:**

- `Gen.one_of(*generators)` - Randomly chooses from multiple generators
- `Gen.element_of(*values)` - Randomly chooses from multiple values
- `Gen.weighted_gen(generator, weight)` - Wraps generator with weight for one_of
- `Gen.weighted_value(value, weight)` - Wraps value with weight for element_of

**Transformation Combinators:**

- `generator.map(func)` - Transforms generated values
- `generator.filter(predicate)` - Filters values by predicate
- `generator.flat_map(func)` - Creates dependent generators

**Decorators:**

- `@for_all(*generators, num_runs, seed)` - Core property-based testing decorator
- `@example(*values)` - Provides specific example values to test
- `@settings(num_runs, seed)` - Configures test parameters
- `@matrix(**kwargs)` - Provides exhaustive Cartesian product testing

### 1. Function-based Approach (Works with both pytest and unittest)

```python
from python_proptest import run_for_all, Gen

def test_addition_commutativity():
    def property_func(x: int, y: int):
        return x + y == y + x

    run_for_all(property_func, Gen.int(), Gen.int())
```

### 2. Decorator-based Approach

```python
from python_proptest import for_all, Gen, example, settings, matrix

@for_all(Gen.int(), Gen.int())   # Test domain with random generated values
@matrix(x=[0, 1], y=[0, 1])      # Test combination of edge cases exhaustively
@example(42, 24)                 # Test specific known values
@settings(num_runs=50, seed=42)  # Configure test parameters
def test_addition_commutativity(x: int, y: int):
    assert x + y == y + x

# Run the test
test_addition_commutativity()
```

### 3. Framework Integration

The `@for_all` decorator integrates with both `unittest` and `pytest` using direct decoration:

**Unittest Integration:**
```python
import unittest
from python_proptest import for_all, Gen

class TestMathProperties(unittest.TestCase):
    @for_all(Gen.int(), Gen.int())
    def test_addition_commutativity(self, x: int, y: int):
        """Test that addition is commutative - direct decoration."""
        self.assertEqual(x + y, y + x)
```

**Pytest Integration:**
```python
import pytest
from python_proptest import for_all, Gen

class TestMathProperties:
    @for_all(Gen.int(), Gen.int())
    def test_addition_commutativity(self, x: int, y: int):
        """Test that addition is commutative - direct decoration."""
        assert x + y == y + x
```

## Choosing the Right Approach

python-proptest provides multiple approaches for defining property tests. Choose based on your needs:

### Use `run_for_all` Function for Simple Lambda-Based Tests

Suitable for simple property checks that can be expressed as lambdas:

```python
from python_proptest import run_for_all, Gen

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

### Use `@run_for_all` Decorator for Named Functions

While standalone `run_for_all` function can only work on lambdas,
`@run_for_all` decorator can work on a named function.

```python
from python_proptest import run_for_all, Gen

gen = Gen.chain(Gen.int(1, 10), lambda x: Gen.int(x, x + 10))

@run_for_all(gen, num_runs=50)
def check_dependency(pair):
    base, dependent = pair
    self.assertGreaterEqual(dependent, base)
    self.assertLessEqual(dependent, base + 10)
# Auto-executes when decorated!


gen = Gen.aggregate(
    Gen.int(0, 10),
    lambda n: Gen.int(n, n + 5),
    min_size=5, max_size=10
)

@run_for_all(gen, num_runs=30)
def check_increasing(values):
    for i in range(1, len(values)):
        self.assertGreaterEqual(values[i], values[i - 1])
```

### Use `@for_all` for Test Frameworks

`@for_all` decorator can be used to create a property-based test in a test frameworks like `unittest` or `pytest`.
Method parameters are randomized according to the specified generators and the method body is wrapped within a property-based test loop.
As a result, the method becomes a conforming test case of the test framework.

```python
import unittest
from python_proptest import for_all, Gen

class TestStringProperties(unittest.TestCase):
    @for_all(Gen.str(), Gen.str())
    def test_string_concatenation(self, s1: str, s2: str):
        """Test string concatenation properties."""
        result = s1 + s2
        self.assertEqual(len(result), len(s1) + len(s2))
        self.assertTrue(result.startswith(s1))
        self.assertTrue(result.endswith(s2))
```

Note that `@for_all` decorator does not itself executes the test and let it execute by the containing framework whereas `@run_for_all` does the execution as well.

```python
from python_proptest import for_all, Gen

@for_all(Gen.int(), Gen.int())
def test_complex_math_property(x: int, y: int):
    """Test complex mathematical property with multiple conditions."""
    result = x * y + x + y
    assert result >= x
    assert result >= y
    assert result % 2 == (x + y) % 2

# need to call the function explicitly to execute the property test
test_complex_math_property()

# this one does not need explicit call
@run_for_all(Gen.str(), Gen.str())
def test_string_operations(s1: str, s2: str):
    """Test string operations with multiple assertions."""
    combined = s1 + s2
    assert len(combined) == len(s1) + len(s2)
    assert combined.startswith(s1)
    assert combined.endswith(s2)

```

### Guidelines

- **Use `run_for_all` function** for immediately testing a property with a lambda with single statement
- **Use `@run_for_all` decorator** for immediately testing a property with a named functions with longer body
- **Use `@for_all`** for use in test frameworks like `unittest` or `pytest`.

All approaches reach the same goal - choose based on your testing framework and preferences. For more details on decorators, see [Decorators](decorators.md). For framework integration, see [Pytest Integration](pytest-integration.md), [Unittest Integration](unittest-integration.md), and [Pytest Best Practices](pytest-best-practices.md).
