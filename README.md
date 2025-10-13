# PyPropTest

A property-based testing framework for Python, inspired by Haskell's QuickCheck and Python's Hypothesis.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-BSD--3--Clause-green.svg)](LICENSE)
[![Tests](https://github.com/kindone/pyproptest/workflows/CI/badge.svg)](https://github.com/kindone/pyproptest/actions)
[![Coverage](https://codecov.io/gh/kindone/pyproptest/branch/main/graph/badge.svg)](https://codecov.io/gh/kindone/pyproptest)
[![PyPI version](https://badge.fury.io/py/pyproptest.svg)](https://badge.fury.io/py/pyproptest)

## What is Property-Based Testing?

Property-based testing shifts the focus from example-based verification to defining universal *properties* or *invariants* that must hold true for an input domain. Instead of manually crafting test cases for specific inputs, you describe the *domain* of inputs your function expects and the *general characteristics* of the output.

PyPropTest then generates hundreds or thousands of varied inputs, searching for edge cases or unexpected behaviors that violate your defined properties. This approach significantly increases test coverage and the likelihood of finding subtle bugs.

## Quick Start

### Installation

```bash
pip install pyproptest
```

For development dependencies:

```bash
pip install pyproptest[dev]
```

### Simple Lambda-Based Tests (Recommended for Simple Properties)

```python
from pyproptest import run_for_all, Gen

def test_simple_properties():
    # Perfect for simple lambda-based properties
    result = run_for_all(
        lambda x, y: x + y == y + x,  # Addition is commutative
        Gen.int(), Gen.int()
    )
    
    result = run_for_all(
        lambda x: isinstance(x, int),  # Type check
        Gen.int(min_value=0, max_value=100)
    )
    
    assert result is True
```

### Pytest Integration (Recommended for Most Use Cases)

**The easiest way to use PyPropTest is with pytest!** Just add the `@for_all` decorator to your test methods, and PyPropTest automatically generates hundreds of random test cases:

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

# Just run: pytest
# Each test method automatically runs with 100+ random inputs!
```

### Standalone Function-Based Tests

```python
from pyproptest import for_all, integers

@for_all(integers(), integers())
def test_complex_math_property(x: int, y: int):
    """Test complex mathematical property with multiple conditions."""
    result = x * y + x + y
    assert result >= x
    assert result >= y
    assert result % 2 == (x + y) % 2

# Run the test
test_complex_math_property()
```

## When to Use Each Approach

### Use `@for_all` with pytest (Recommended)

**This is the recommended approach for most users!** Perfect for:

- **Pytest integration**: Works seamlessly with your existing test suite
- **Automatic test discovery**: pytest finds and runs your property-based tests
- **IDE support**: Full debugging, breakpoints, and parameter inspection
- **Complex assertions**: Multiple conditions and complex generator transformations
- **Team collaboration**: Standard pytest workflow everyone understands

### Use `run_for_all` for Simple Lambda-Based Tests

Perfect for simple property checks that can be expressed as lambdas:

- **Type checks**: `lambda x: isinstance(x, int)`
- **Range validations**: `lambda x: 0 <= x <= 100`
- **Simple assertions**: `lambda lst: all(isinstance(x, int) for x in lst)`
- **Seed-based reproducibility testing**
- **Quick prototyping**: When you want to test a property without creating a full test class

## Features

- **🚀 Pytest Integration**: Drop-in integration with pytest - just add `@for_all()` decorator and run `pytest`
- **🎲 Automatic Randomization**: Each test method automatically runs with 100+ randomly generated inputs
- **🔍 Automatic Shrinking**: When tests fail, PyPropTest finds minimal counterexamples
- **📊 Comprehensive Generators**: Built-in generators for primitives, collections, and complex data structures
- **🔧 Powerful Combinators**: Transform and combine generators to create sophisticated test data
- **🏗️ Stateful Testing**: Test systems with internal state using action sequences
- **🎯 Reproducible Tests**: Support for seeds to make tests deterministic
- **💡 Type Safety**: Full type hints support for better IDE integration

## Examples

### Testing List Operations

```python
from pyproptest import run_for_all, Gen

def test_list_reverse():
    def property_func(lst: list):
        # Reversing twice should return the original list
        return list(reversed(list(reversed(lst)))) == lst
    
    run_for_all(property_func, Gen.list(Gen.str(), min_length=0, max_length=10))
```

### Testing String Properties

```python
from pyproptest import for_all, text

@for_all(text(), text())
def test_string_concatenation(s1: str, s2: str):
    result = s1 + s2
    assert len(result) == len(s1) + len(s2)
    assert result.startswith(s1)
    assert result.endswith(s2)
```

### Testing Complex Data Structures

```python
from pyproptest import run_for_all, Gen

def test_json_roundtrip():
    def property_func(data: dict):
        import json
        serialized = json.dumps(data)
        parsed = json.loads(serialized)
        return parsed == data
    
    # Generate dictionaries with string keys and various values
    data_gen = Gen.dict(
        Gen.str(min_length=1, max_length=10),
        Gen.one_of(
            Gen.str(),
            Gen.int(),
            Gen.bool(),
            Gen.list(Gen.str(), min_length=0, max_length=5)
        ),
        min_size=0,
        max_size=5
    )
    
    run_for_all(property_func, data_gen)
```

### Stateful Testing

```python
from pyproptest import simple_stateful_property, Gen, SimpleAction

def test_stack_operations():
    # Define a stack as a list
    Stack = list
    
    # Start with an empty stack
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
    
    # Action factory
    def action_factory(stack: Stack):
        if not stack:
            return push_action()  # Can only push when empty
        else:
            return Gen.one_of(push_action(), pop_action())
    
    # Create and run the property
    prop = simple_stateful_property(initial_gen, action_factory)
    prop.go()
```

## API Overview

### Generators

- **Primitives**: `Gen.int()`, `Gen.float()`, `Gen.str()`, `Gen.bool()`
- **Collections**: `Gen.list()`, `Gen.dict()`, `Gen.set()`, `Gen.tuple()`
- **Special**: `Gen.just()`, `Gen.lazy()`, `Gen.one_of()`, `Gen.element_of()`

### Combinators

- **Transformation**: `generator.map()`, `generator.filter()`, `generator.flat_map()`
- **Selection**: `Gen.one_of()`, `Gen.element_of()`, `Gen.weighted_gen()`
- **Construction**: `Gen.construct()`

### Properties

- **Function-based**: `run_for_all(property_func, *generators)`
- **Decorator-based**: `@for_all(*generators)`
- **Class-based**: `Property(property_func).for_all(*generators)`

## Documentation

- [Getting Started](docs/index.md)
- [Generators](docs/generators.md)
- [Combinators](docs/combinators.md)
- [Properties](docs/properties.md)
- [Shrinking](docs/shrinking.md)
- [Stateful Testing](docs/stateful-testing.md)

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pyproptest

# Run specific test file
pytest tests/test_generators.py
```

### Type Checking

```bash
mypy pyproptest/
```

### Code Formatting

```bash
black pyproptest/ tests/
isort pyproptest/ tests/
```

## License

This project is licensed under the BSD-3-Clause License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to get started.

### Quick Start for Contributors

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Install in development mode: `pip install -e ".[dev,docs]"`
4. Make your changes and add tests
5. Run the test suite: `pytest`
6. Commit your changes: `git commit -m 'Add amazing feature'`
7. Push to your branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/your-username/pyproptest.git
cd pyproptest

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev,docs]"

# Run tests
pytest

# Run linting
black pyproptest/ tests/
isort pyproptest/ tests/
flake8 pyproptest/ tests/
mypy pyproptest/
```

## Acknowledgments

- Inspired by [QuickCheck](https://hackage.haskell.org/package/QuickCheck) for Haskell
- Influenced by [Hypothesis](https://hypothesis.readthedocs.io/) for Python
- Based on the original [jsproptest](https://github.com/kindone/jsproptest) TypeScript implementation
