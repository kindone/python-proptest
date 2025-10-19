# python-proptest

A property-based testing framework for Python, inspired by Haskell's QuickCheck and Python's Hypothesis.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://github.com/kindone/python-proptest/workflows/CI/badge.svg)](https://github.com/kindone/python-proptest/actions)
[![Coverage](https://codecov.io/gh/kindone/python-proptest/branch/main/graph/badge.svg)](https://codecov.io/gh/kindone/python-proptest)
[![PyPI version](https://badge.fury.io/py/python-proptest.svg)](https://badge.fury.io/py/python-proptest)

## What is Property-Based Testing?

Property-based testing shifts the focus from example-based verification to defining universal *properties* or *invariants* that must hold true for an input domain. Instead of manually crafting test cases for specific inputs, you describe the *domain* of inputs your function expects and the *general characteristics* of the output.

python-proptest then generates hundreds or thousands of varied inputs, searching for edge cases or unexpected behaviors that violate your defined properties. This approach significantly increases test coverage and the likelihood of finding subtle bugs.

## Quick Start

### Installation

```bash
pip install python-proptest
```

For development dependencies:

```bash
pip install python-proptest[dev]
```

### Simple Lambda-Based Tests (Recommended for Simple Properties)

```python
from python_proptest import run_for_all, Gen

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

**The easiest way to use python-proptest is with pytest!** Just add the `@for_all` decorator to your test methods, and python-proptest automatically generates hundreds of random test cases:

```python
import pytest
from python_proptest import for_all, Gen

class TestMathProperties:
    @for_all(Gen.int(), Gen.int())
    def test_addition_commutativity(self, x: int, y: int):
        """Test that addition is commutative - automatically runs 100+ random cases!"""
        assert x + y == y + x

    @for_all(Gen.int(), Gen.int())
    def test_multiplication_associativity(self, x: int, y: int, z: int):
        """Test that multiplication is associative."""
        assert (x * y) * z == x * (y * z)

class TestStringProperties:
    @for_all(Gen.str(), Gen.str())
    def test_string_concatenation(self, s1: str, s2: str):
        """Test string concatenation properties."""
        result = s1 + s2
        assert len(result) == len(s1) + len(s2)
        assert result.startswith(s1)
        assert result.endswith(s2)

# Just run: pytest
# Each test method automatically runs with 100+ random inputs!
```

### Unittest Integration

**python-proptest also works with Python's built-in unittest framework!** The `@for_all` decorator automatically detects unittest.TestCase classes and adapts accordingly:

```python
import unittest
from python_proptest import for_all, Gen

class TestMathProperties(unittest.TestCase):
    @for_all(Gen.int(), Gen.int())
    def test_addition_commutativity(self, x: int, y: int):
        """Test that addition is commutative using unittest assertions."""
        self.assertEqual(x + y, y + x)

    @for_all(Gen.int(), Gen.int(), Gen.int())
    def test_multiplication_associativity(self, x: int, y: int, z: int):
        """Test that multiplication is associative."""
        self.assertEqual((x * y) * z, x * (y * z))

class TestStringProperties(unittest.TestCase):
    @for_all(Gen.str(), Gen.str())
    def test_string_concatenation(self, s1: str, s2: str):
        """Test string concatenation properties."""
        result = s1 + s2
        self.assertEqual(len(result), len(s1) + len(s2))
        self.assertTrue(result.startswith(s1))
        self.assertTrue(result.endswith(s2))

# Run with: python -m unittest
# Or with: pytest (both frameworks work!)
```

### Standalone Function-Based Tests

```python
from python_proptest import for_all, Gen

@for_all(Gen.int(), Gen.int())
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

### Use `@for_all` with unittest

**Perfect for teams using Python's built-in unittest framework!** Great for:

- **Standard library integration**: No external dependencies beyond python-proptest
- **Unittest assertions**: Use `self.assertEqual()`, `self.assertTrue()`, etc.
- **Mixed assertion styles**: Combine unittest assertions with regular `assert` statements
- **Legacy codebases**: Easy migration from existing unittest test suites
- **CI/CD compatibility**: Works with any unittest-compatible test runner

### Use `run_for_all` for Simple Lambda-Based Tests

Perfect for simple property checks that can be expressed as lambdas:

- **Type checks**: `lambda x: isinstance(x, int)`
- **Range validations**: `lambda x: 0 <= x <= 100`
- **Simple assertions**: `lambda lst: all(isinstance(x, int) for x in lst)`
- **Seed-based reproducibility testing**
- **Quick prototyping**: When you want to test a property without creating a full test class

## Features

- **🚀 Test Framework Integration**: Drop-in integration with both pytest and unittest - just add `@for_all()` decorator
- **🔧 Automatic Framework Detection**: Automatically detects unittest.TestCase vs pytest vs standalone functions
- **🎲 Automatic Randomization**: Each test method automatically runs with 100+ randomly generated inputs
- **🔍 Automatic Shrinking**: When tests fail, python-proptest finds minimal counterexamples
- **📊 Comprehensive Generators**: Built-in generators for primitives, collections, and complex data structures
- **🔧 Powerful Combinators**: Transform and combine generators to create sophisticated test data
- **🏗️ Stateful Testing**: Test systems with internal state using action sequences
- **🎯 Reproducible Tests**: Support for seeds to make tests deterministic
- **💡 Type Safety**: Full type hints support for better IDE integration

## Examples

### Testing List Operations

```python
from python_proptest import run_for_all, Gen

def test_list_reverse():
    def property_func(lst: list):
        # Reversing twice should return the original list
        return list(reversed(list(reversed(lst)))) == lst

    run_for_all(property_func, Gen.list(Gen.str(), min_length=0, max_length=10))
```

### Testing String Properties

```python
from python_proptest import for_all, Gen

@for_all(Gen.str(), Gen.str())
def test_string_concatenation(s1: str, s2: str):
    result = s1 + s2
    assert len(result) == len(s1) + len(s2)
    assert result.startswith(s1)
    assert result.endswith(s2)
```

### Testing Complex Data Structures

```python
from python_proptest import run_for_all, Gen

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
from python_proptest import simple_stateful_property, Gen, SimpleAction

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

The project includes a comprehensive Makefile with useful development commands:

### Quick Commands

```bash
# Show all available commands
make help

# Quick pre-commit checks (fast)
make quick-check

# Full pre-commit checks
make pre-commit

# Run all CI checks
make all-checks
```

### Individual Development Tasks

```bash
# Install dependencies
make install

# Run all tests (unittest + pytest with coverage)
make test

# Code quality checks
make lint           # Run flake8 linting
make format         # Format code with black and isort
make type-check     # Run mypy type checking
make security       # Run security analysis

# Python version testing
make test-python38  # Test Python 3.8 compatibility
make test-all-python # Test all available Python versions

# PyPI publishing
make build-package  # Build package for PyPI distribution
make test-package   # Test built package locally
make upload-testpypi # Upload to TestPyPI
make upload-pypi    # Upload to production PyPI

# Utilities
make clean          # Clean up generated files
make clean-whitespace # Clean trailing whitespaces from all files
```

### Development Workflow

```bash
# Quick check (fast, for frequent commits)
make quick-check

# Full check (comprehensive, before pushing)
make pre-commit

# All CI checks (before submitting PR)
make all-checks
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## CI/CD and Publishing

### Automated Testing
- **CI Pipeline**: Runs on every push and PR with Python 3.8-3.12
- **Test Frameworks**: Both `unittest` and `pytest` are supported
- **Code Quality**: Automated linting, formatting, type checking, and security analysis

### Publishing to PyPI

#### TestPyPI Uploads
To upload to TestPyPI (for testing), you can:

1. **Manual trigger**: Use GitHub Actions workflow dispatch
2. **Local upload**: Use `make upload-testpypi`

#### Production PyPI Uploads
Production uploads happen automatically when you:
1. Create a version tag: `git tag v1.0.0`
2. Push the tag: `git push origin v1.0.0`

### Version Management
- Use `make bump-version` to bump versions (patch/minor/major)
- Production PyPI uses semantic versioning from git tags

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to get started.

### Quick Start for Contributors

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/python-proptest.git`
3. Create a feature branch: `git checkout -b feature/amazing-feature`
4. Set up development environment: `make install`
5. Make your changes and add tests
6. Run quality checks: `make pre-commit`
7. Ensure all tests pass: `make all-checks`
8. Commit your changes: `git commit -m 'feat: add amazing feature'`
9. Push to your branch: `git push origin feature/amazing-feature`
10. Open a Pull Request

For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/your-username/python-proptest.git
cd python-proptest

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
make install

# Run quick checks
make quick-check

# Run comprehensive checks
make all-checks
```

### Pre-commit Workflow

Before committing, run the pre-commit checks to ensure code quality:

```bash
# Quick check (fast, for frequent commits)
make quick-check

# Full check (comprehensive, before pushing)
make pre-commit

# All CI checks (before submitting PR)
make all-checks
```

## Acknowledgments

- Inspired by [QuickCheck](https://hackage.haskell.org/package/QuickCheck) for Haskell
- Influenced by [Hypothesis](https://hypothesis.readthedocs.io/) for Python
- Based on the original [jsproptest](https://github.com/kindone/jsproptest) TypeScript implementation
