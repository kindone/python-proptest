# Decorators

python-proptest provides several decorators to enhance property-based testing with additional features like examples, settings, and matrix testing.

## Overview

The decorators work together to provide a flexible and powerful testing experience:

- `@for_all` - Core property-based testing decorator
- `@example` - Provides specific example values to test
- `@settings` - Configures test parameters like number of runs and seed
- `@matrix` - Provides exhaustive Cartesian product testing of fixed inputs

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

- `*generators`: Variable number of generators for function arguments
- `num_runs`: Number of test runs (default: 100)
- `seed`: Random seed for reproducibility (default: None)

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

```python
@for_all(Gen.int())
@example(0)      # Edge case: zero
@example(1)      # Edge case: one
@example(-1)     # Edge case: negative
def test_property(x: int):
    assert isinstance(x, int)
```

### 2. Use Matrix for Exhaustive Testing

```python
@for_all(Gen.int(), Gen.int())
@matrix(x=[0, 1, -1], y=[0, 1, -1])  # Test all combinations of edge cases
def test_property(x: int, y: int):
    assert isinstance(x, int)
    assert isinstance(y, int)
```

### 3. Use Settings for Reproducibility

```python
@for_all(Gen.int(), Gen.str())
@settings(seed=42)  # Reproducible tests
def test_property(x: int, s: str):
    assert isinstance(x, int)
    assert isinstance(s, str)
```

### 4. Combine Decorators Strategically

```python
@for_all(Gen.int(), Gen.str())
@matrix(x=[0, 1], s=["a", "b"])  # Exhaustive edge cases
@example(42, "special")          # Known good value
@settings(num_runs=100, seed=42) # Reproducible random testing
def test_property(x: int, s: str):
    assert isinstance(x, int)
    assert isinstance(s, str)
```

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
