# Decorators

python-proptest provides several decorators to enhance property-based testing with additional features like examples, settings, and matrix testing.

## Overview

The decorators work together to provide a flexible and powerful testing experience:

- [`@for_all`](#for_all) - Core property-based testing decorator
- [`@run_for_all`](#run_for_all) - Versatile decorator for dependent generators
- [`@example`](#example) - Provides specific example values to test
- [`@settings`](#settings) - Configures test parameters like number of runs and seed
- [`@matrix`](#matrix) - Provides exhaustive Cartesian product testing of fixed inputs

For information on generators to use with these decorators, see the [Generators](generators.md) documentation.

## @for_all

The core decorator for property-based testing. It automatically detects the testing framework (pytest, unittest, or standalone) and adapts accordingly.

### Basic Usage

```python
from python_proptest import for_all, Gen

@for_all(Gen.int(), Gen.str())
def test_property(x: int, s: str):
    assert isinstance(x, int)
    assert isinstance(s, str)
    assert len(s) >= 0

# Run the test
test_property()
```

### With pytest

```python
import pytest
from python_proptest import for_all, Gen

class TestMathProperties:
    @for_all(Gen.int(), Gen.int())
    def test_addition_commutativity(self, x: int, y: int):
        assert x + y == y + x
```

### With unittest

```python
import unittest
from python_proptest import for_all, Gen

class TestMathProperties(unittest.TestCase):
    @for_all(Gen.int(), Gen.int())
    def test_addition_commutativity(self, x: int, y: int):
        self.assertEqual(x + y, y + x)
```

### Parameters

- `*generators`: Variable number of [generators](generators.md) for function arguments
- `num_runs`: Number of test runs (default: 100)
- `seed`: Random seed for reproducibility (default: None)

**See Also:** [`@run_for_all`](#run_for_all) for dependent generators, [`@example`](#example) for specific test cases, [`@settings`](#settings) for configuration

## @run_for_all

A versatile decorator that works in three different modes, combining the power of property-based testing with flexible syntax. Unlike `@for_all`, it doesn't unpack generator values, making it ideal for working with complex generators like `chain`, `aggregate`, and `accumulate`.

### Mode 1: Function Call (Traditional)

Use `run_for_all` as a function to explicitly run property tests:

```python
from python_proptest import run_for_all, Gen

def test_addition():
    def check(x, y):
        return x + y == y + x

    result = run_for_all(check, Gen.int(0, 100), Gen.int(0, 100), num_runs=100)
    assert result is True
```

### Mode 2: Test Method Decorator

Decorate test methods to have property tests executed by the test framework:

```python
import unittest
from python_proptest import run_for_all, Gen

class TestProperties(unittest.TestCase):
    @run_for_all(Gen.int(0, 100), Gen.int(0, 100), num_runs=50)
    def test_addition_commutative(self, x, y):
        self.assertEqual(x + y, y + x)
```

### Mode 3: Nested Function Decorator (Auto-Execute)

The most powerful mode - decorate nested functions inside test methods and they **execute immediately**:

```python
import unittest
from python_proptest import run_for_all, Gen

class TestChain(unittest.TestCase):
    def test_chain_dependency(self):
        gen = Gen.chain(Gen.int(1, 10), lambda x: Gen.int(x, x + 10))

        @run_for_all(gen, num_runs=20, seed=42)
        def check_dependency(pair):
            base, dependent = pair
            self.assertGreaterEqual(dependent, base)
            self.assertLessEqual(dependent, base + 10)

        # No explicit call needed - the property test already ran!
```

### Working with Complex Generators

`@run_for_all` is perfect for generators that return tuples or complex structures. For detailed documentation on these combinators, see [Dependent Generation Combinators](combinators.md#dependent-generation-combinators).

#### With chain

[`Gen.chain()`](combinators.md#genchainbase_gen-gen_factory-generatorchaingen_factory) creates dependent tuples where each value depends on the previous:

```python
def test_dependent_generation(self):
    # chain returns (base_value, dependent_value) tuple
    gen = Gen.chain(
        Gen.int(1, 100),
        lambda x: Gen.int(x, x + 50)
    )

    @run_for_all(gen, num_runs=50)
    def check_range(pair):
        start, end = pair
        self.assertGreaterEqual(end, start)
        self.assertLessEqual(end, start + 50)
```

#### With aggregate

[`Gen.aggregate()`](combinators.md#genaggregateinitial_gen-gen_factory-min_size-max_size-generatoraggregate) generates sequences where each element depends on the previous:

```python
def test_increasing_sequence(self):
    # aggregate returns a list of dependent values
    gen = Gen.aggregate(
        Gen.int(0, 10),
        lambda n: Gen.int(n, n + 5),
        min_size=5,
        max_size=10
    )

    @run_for_all(gen, num_runs=30)
    def check_sequence(values):
        self.assertGreaterEqual(len(values), 5)
        # Check each value >= previous
        for i in range(1, len(values)):
            self.assertGreaterEqual(values[i], values[i - 1])
```

#### With accumulate

[`Gen.accumulate()`](combinators.md#genaccumulateinitial_gen-gen_factory-min_size-max_size-generatoraccumulate) generates the final value after N dependent steps:

```python
def test_final_value(self):
    # accumulate returns only the final value after N steps
    gen = Gen.accumulate(
        Gen.int(10, 20),
        lambda n: Gen.int(n + 1, n + 5),
        min_size=10,
        max_size=10
    )

    @run_for_all(gen, num_runs=25)
    def check_final(final_value):
        # After 10 steps of +1 to +5, should be >= initial + 10
        self.assertGreaterEqual(final_value, 20)
```

### Comparison: @for_all vs @run_for_all

```python
# @for_all unpacks the tuple arguments
@for_all(Gen.int(1, 10), Gen.int(1, 10))
def test_with_for_all(self, x, y):
    # Gets two separate arguments: x and y
    assert x <= y

# @run_for_all with chain - receives tuple as-is
@run_for_all(Gen.chain(Gen.int(1, 10), lambda x: Gen.int(x, x + 10)))
def test_with_run_for_all(self, pair):
    # Gets tuple: (base, dependent)
    base, dependent = pair
    assert base <= dependent
```

### Parameters

- `*generators`: One or more [generators](generators.md) (when used as decorator, generators come first)
- `num_runs`: Number of test runs (default: 100)
- `seed`: Random seed for reproducibility (default: None)

### When to Use @run_for_all

Use `@run_for_all` when:
- Working with [`chain`](combinators.md#genchainbase_gen-gen_factory-generatorchaingen_factory), [`aggregate`](combinators.md#genaggregateinitial_gen-gen_factory-min_size-max_size-generatoraggregate), or [`accumulate`](combinators.md#genaccumulateinitial_gen-gen_factory-min_size-max_size-generatoraccumulate) combinators
- You want auto-execution in nested function contexts
- You prefer explicit control over value unpacking
- Testing properties that operate on tuples or complex structures

Use [`@for_all`](#for_all) when:
- You want automatic argument unpacking
- Working with simple, independent generators
- Following traditional property testing patterns

**See Also:** [`@for_all`](#for_all), [Dependent Generation Combinators](combinators.md#dependent-generation-combinators), [`@settings`](#settings)

## @example

Provides specific example values that are tested before random generation. Examples are useful for testing edge cases, known good values, or debugging specific scenarios.

### Basic Usage

```python
from python_proptest import for_all, Gen, example

@for_all(Gen.int(), Gen.str())
@example(0, "")
@example(42, "hello")
def test_property(x: int, s: str):
    assert isinstance(x, int)
    assert isinstance(s, str)
```

### Multiple Examples

```python
@for_all(Gen.int(), Gen.str())
@example(0, "")
@example(1, "a")
@example(-1, "negative")
def test_property(x: int, s: str):
    assert isinstance(x, int)
    assert isinstance(s, str)
```

### Examples with Different Types

```python
@for_all(Gen.int(), Gen.list(Gen.int()))
@example(0, [])
@example(1, [1])
@example(2, [1, 2])
def test_list_property(x: int, lst: list):
    assert isinstance(x, int)
    assert isinstance(lst, list)
```

### Parameters

- `*values`: Variable number of values matching the function parameters

**See Also:** [`@for_all`](#for_all), [`@matrix`](#matrix), [Best Practices](#1-use-examples-for-edge-cases)

## @settings

Configures test parameters like number of runs and random seed. Settings override the defaults provided to `@for_all`.

### Basic Usage

```python
from python_proptest import for_all, Gen, settings

@for_all(Gen.int(), Gen.str())
@settings(num_runs=50, seed=42)
def test_property(x: int, s: str):
    assert isinstance(x, int)
    assert isinstance(s, str)
```

### Seed for Reproducibility

```python
@for_all(Gen.int(), Gen.str())
@settings(seed="deterministic")
def test_property(x: int, s: str):
    assert isinstance(x, int)
    assert isinstance(s, str)
```

### Multiple Settings (Last Wins)

```python
@for_all(Gen.int(), Gen.str())
@settings(num_runs=100)
@settings(seed=42)  # This overrides the previous settings
def test_property(x: int, s: str):
    assert isinstance(x, int)
    assert isinstance(s, str)
```

### Parameters

- `num_runs`: Number of test runs (overrides @for_all default)
- `seed`: Random seed for reproducibility (overrides @for_all default)

**See Also:** [`@for_all`](#for_all), [`@run_for_all`](#run_for_all), [Best Practices](#3-use-settings-for-reproducibility)

## @matrix

Provides exhaustive Cartesian product testing of fixed input combinations. Matrix cases are executed once per combination, before examples and random runs, and do not count toward `num_runs`.

### Basic Usage

```python
from python_proptest import for_all, Gen, matrix

@for_all(Gen.int(), Gen.str())
@matrix(x=[0, 1], s=["a", "b"])
def test_property(x: int, s: str):
    assert isinstance(x, int)
    assert isinstance(s, str)
```

This will test all combinations:
- `(0, "a")`
- `(0, "b")`
- `(1, "a")`
- `(1, "b")`

### Multiple Matrix Decorators

```python
@for_all(Gen.int(), Gen.str())
@matrix(x=[0, 1])
@matrix(s=["a", "b"])
def test_property(x: int, s: str):
    assert isinstance(x, int)
    assert isinstance(s, str)
```

### Matrix with Different Types

```python
@for_all(Gen.int(), Gen.list(Gen.int()))
@matrix(x=[0, 1, 2], lst=[[], [1], [1, 2]])
def test_property(x: int, lst: list):
    assert isinstance(x, int)
    assert isinstance(lst, list)
```

### Matrix with Complex Types

```python
@for_all(Gen.int(), Gen.dict(Gen.str(), Gen.int()))
@matrix(x=[1, 2], d=[{"a": 1}, {"b": 2}])
def test_property(x: int, d: dict):
    assert isinstance(x, int)
    assert isinstance(d, dict)
```

### Parameters

- `**kwargs`: Named parameters with lists of values to test

**See Also:** [`@for_all`](#for_all), [`@example`](#example), [Best Practices](#2-use-matrix-for-exhaustive-testing), [Error Handling](#matrix-parameter-coverage)

## Decorator Composition

All decorators can be combined in various ways. The execution order is:

1. **Matrix cases** (exhaustive combinations)
2. **Example cases** (specific values)
3. **Random cases** (property-based generation)

### Complete Example

```python
from python_proptest import for_all, Gen, example, settings, matrix

@for_all(Gen.int(), Gen.str())
@matrix(x=[0, 1], s=["a", "b"])  # 4 matrix cases
@example(42, "special")           # 1 example case
@settings(num_runs=10, seed=42)   # 10 random cases
def test_property(x: int, s: str):
    assert isinstance(x, int)
    assert isinstance(s, str)
    # Total: 4 + 1 + 10 = 15 test cases
```

### Decorator Order

The order of decorators matters for merging behavior:

```python
@for_all(Gen.int(), Gen.str())
@matrix(x=[1, 2])      # First matrix decorator
@matrix(x=[3, 4])      # Second matrix decorator (overwrites first)
@settings(num_runs=50) # First settings decorator
@settings(seed=42)     # Second settings decorator (overwrites first)
def test_property(x: int, s: str):
    assert isinstance(x, int)
    assert isinstance(s, str)
    # Matrix will use x=[3, 4], settings will use seed=42
```

## Integration with Testing Frameworks

All decorators work seamlessly with both pytest and unittest:

### Pytest Integration

```python
import pytest
from python_proptest import for_all, Gen, example, settings, matrix

class TestMathProperties:
    @for_all(Gen.int(), Gen.int())
    @matrix(x=[0, 1], y=[0, 1])
    @example(42, 24)
    @settings(num_runs=50, seed=42)
    def test_addition_commutativity(self, x: int, y: int):
        assert x + y == y + x
```

### Unittest Integration

```python
import unittest
from python_proptest import for_all, Gen, example, settings, matrix

class TestMathProperties(unittest.TestCase):
    @for_all(Gen.int(), Gen.int())
    @matrix(x=[0, 1], y=[0, 1])
    @example(42, 24)
    @settings(num_runs=50, seed=42)
    def test_addition_commutativity(self, x: int, y: int):
        self.assertEqual(x + y, y + x)
```

## Programmatic Usage

For programmatic testing, you can use the `run_matrix` function:

```python
from python_proptest import run_matrix

def test_func(x: int, y: str):
    assert isinstance(x, int)
    assert isinstance(y, str)

# Run matrix cases programmatically
matrix_spec = {"x": [0, 1], "y": ["a", "b"]}
run_matrix(test_func, matrix_spec)
```

### Parameters

- `test_func`: Function to test
- `matrix_spec`: Dictionary mapping parameter names to lists of values
- `self_obj`: Optional self object for class methods

## Best Practices

### 1. Use Examples for Edge Cases

Combine [`@example`](#example) with [`@for_all`](#for_all) to test specific edge cases before random generation:

```python
@for_all(Gen.int())
@example(0)      # Edge case: zero
@example(1)      # Edge case: one
@example(-1)     # Edge case: negative
def test_property(x: int):
    assert isinstance(x, int)
```

### 2. Use Matrix for Exhaustive Testing

Use [`@matrix`](#matrix) to test all combinations of important values:

```python
@for_all(Gen.int(), Gen.int())
@matrix(x=[0, 1, -1], y=[0, 1, -1])  # Test all combinations of edge cases
def test_property(x: int, y: int):
    assert isinstance(x, int)
    assert isinstance(y, int)
```

### 3. Use Settings for Reproducibility

Use [`@settings`](#settings) to ensure tests are reproducible:

```python
@for_all(Gen.int(), Gen.str())
@settings(seed=42)  # Reproducible tests
def test_property(x: int, s: str):
    assert isinstance(x, int)
    assert isinstance(s, str)
```

### 4. Combine Decorators Strategically

Combine [`@for_all`](#for_all), [`@matrix`](#matrix), [`@example`](#example), and [`@settings`](#settings) for comprehensive testing. See also [Decorator Composition](#decorator-composition).

```python
@for_all(Gen.int(), Gen.str())
@matrix(x=[0, 1], s=["a", "b"])  # Exhaustive edge cases
@example(42, "special")          # Known good value
@settings(num_runs=100, seed=42) # Reproducible random testing
def test_property(x: int, s: str):
    assert isinstance(x, int)
    assert isinstance(s, str)
```

**See Also:** [Decorator Composition](#decorator-composition), [Decorator Order](#decorator-order)

## Error Handling

### Matrix Parameter Coverage

Matrix decorators require all function parameters to be covered:

```python
@for_all(Gen.int(), Gen.str())
@matrix(x=[0, 1])  # Missing 's' parameter - matrix cases will be skipped
def test_property(x: int, s: str):
    assert isinstance(x, int)
    assert isinstance(s, str)
```

### Example Parameter Count

Example decorators must provide the correct number of arguments:

```python
@for_all(Gen.int(), Gen.str())
@example(42)  # Missing second argument - example will be skipped
def test_property(x: int, s: str):
    assert isinstance(x, int)
    assert isinstance(s, str)
```

### Settings Override

Later settings decorators override earlier ones:

```python
@for_all(Gen.int(), Gen.str())
@settings(num_runs=100, seed=1)
@settings(num_runs=50, seed=2)  # Only seed=2 will be used
def test_property(x: int, s: str):
    assert isinstance(x, int)
    assert isinstance(s, str)
```

## Related Documentation

- [Generators](generators.md) - Available generators for creating test data
- [Combinators](combinators.md) - Combining and transforming generators
- [Properties](properties.md) - Alternative approaches to property testing
- [Pytest Integration](pytest-integration.md) - Using decorators with pytest
- [Unittest Integration](unittest-integration.md) - Using decorators with unittest
