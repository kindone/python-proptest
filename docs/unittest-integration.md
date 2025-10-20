# Unittest Integration

python-proptest provides seamless integration with Python's built-in `unittest` framework through the `@for_all` decorator. The decorator automatically detects whether it's being used in a unittest context (unittest.TestCase methods), pytest context, or standalone functions and adapts accordingly.

> **Note**: If you're using pytest, see [Pytest Integration](pytest-integration.md) and [Pytest Best Practices](pytest-best-practices.md) for framework-specific guidance. Both pytest and unittest are fully supported with identical functionality.

## Basic Usage

### Unittest TestCase Methods

```python
import unittest
from python_proptest import for_all, Gen

class TestMathProperties(unittest.TestCase):
    """Test class for mathematical properties using unittest."""

    @for_all(Gen.int(), Gen.int())
    def test_addition_commutativity(self, x: int, y: int):
        """Test that addition is commutative."""
        result1 = x + y
        result2 = y + x
        self.assertEqual(result1, result2)

    @for_all(Gen.int(), Gen.int(), Gen.int())
    def test_multiplication_associativity(self, x: int, y: int, z: int):
        """Test that multiplication is associative."""
        result1 = (x * y) * z
        result2 = x * (y * z)
        self.assertEqual(result1, result2)

    @for_all(Gen.str(), Gen.str())
    def test_string_concatenation(self, s1: str, s2: str):
        """Test string concatenation properties."""
        result = s1 + s2
        self.assertEqual(len(result), len(s1) + len(s2))
        self.assertTrue(result.startswith(s1))
        self.assertTrue(result.endswith(s2))
```

**✅ Direct decoration works.** The `@for_all` decorator automatically detects unittest context and handles the `self` parameter correctly.

### Running Unittest Tests

```bash
# Run with unittest
python -m unittest tests.test_unittest_integration -v

# Run with pytest (also works)
python -m pytest tests/test_unittest_integration.py -v
```

## Advanced Features

### Mixed Assertion Styles

You can mix unittest assertions with regular assertions in the same test:

```python
class TestMixedAssertions(unittest.TestCase):
    @for_all(Gen.int(), Gen.int())
    def test_mixed_assertions(self, x: int, y: int):
        """Test mixing different assertion styles."""
        # Unittest assertions
        self.assertIsInstance(x, int)
        self.assertIsInstance(y, int)

        # Regular assertions (work in both frameworks)
        assert x + y == y + x
        assert x * 0 == 0
        assert x * 1 == x

        # More unittest assertions
        self.assertGreaterEqual(x + y, x)
        self.assertGreaterEqual(x + y, y)
```

### Using Gen Class Directly

```python
from python_proptest import for_all, Gen

class TestWithGen(unittest.TestCase):
    @for_all(Gen.int(), Gen.str())
    def test_int_string_properties(self, x: int, s: str):
        """Test properties with int and string generators."""
        self.assertIsInstance(x, int)
        self.assertIsInstance(s, str)
        self.assertGreaterEqual(len(s), 0)

    @for_all(Gen.int(min_value=0, max_value=100), Gen.int(min_value=0, max_value=100))
    def test_positive_int_properties(self, x: int, y: int):
        """Test properties with positive integers."""
        self.assertGreaterEqual(x, 0)
        self.assertGreaterEqual(y, 0)
        self.assertGreaterEqual(x + y, x)
        self.assertGreaterEqual(x + y, y)
```

## Error Handling

### Unittest-Specific Error Handling

When a property test fails in a unittest context, python-proptest automatically raises the appropriate unittest failure exception:

```python
class TestFailingProperties(unittest.TestCase):
    @for_all(Gen.int(), Gen.int())
    def test_failing_property(self, x: int, y: int):
        """This test will fail and show proper unittest error reporting."""
        # This will fail for some inputs
        self.assertLess(x + y, 100)  # Fails when x + y >= 100
```

The error will be reported using unittest's standard failure mechanism, making it compatible with unittest's test runners and reporting tools.

## Framework Detection

python-proptest automatically detects the test framework by checking the class hierarchy:

1. **Unittest Detection**: Checks if the class inherits from `unittest.TestCase`
2. **Pytest Detection**: If not unittest, assumes pytest for class methods with `self` parameter
3. **Standalone Functions**: Functions without `self` parameter are treated as standalone

### Detection Logic

```python
# The decorator automatically detects:
class TestUnittest(unittest.TestCase):  # ← Detected as unittest
    @for_all(Gen.int())
    def test_method(self, x: int):
        self.assertEqual(x, x)

class TestPytest:  # ← Detected as pytest
    @for_all(Gen.int())
    def test_method(self, x: int):
        assert x == x

@for_all(Gen.int())  # ← Detected as standalone
def test_standalone(x: int):
    assert x == x
```

## Best Practices

### 1. Use Descriptive Test Names

```python
class TestStringProperties(unittest.TestCase):
    @for_all(Gen.str(), Gen.str())
    def test_string_concatenation_length_property(self, s1: str, s2: str):
        """Test that concatenated string length equals sum of individual lengths."""
        result = s1 + s2
        self.assertEqual(len(result), len(s1) + len(s2))
```

### 2. Use Appropriate Assertions

```python
class TestNumberProperties(unittest.TestCase):
    @for_all(integers(min_value=1, max_value=100))
    def test_positive_number_properties(self, x: int):
        """Test properties of positive numbers."""
        self.assertGreater(x, 0)  # Use unittest assertions
        self.assertIsInstance(x, int)  # Type checking
        assert x * 2 > x  # Mix with regular assertions
```

### 3. Handle Edge Cases

```python
class TestDivisionProperties(unittest.TestCase):
    @for_all(Gen.int(), integers(min_value=1, max_value=100))
    def test_division_properties(self, x: int, y: int):
        """Test division properties with non-zero divisor."""
        quotient = x // y
        remainder = x % y
        self.assertEqual(quotient * y + remainder, x)
        self.assertGreaterEqual(remainder, 0)
        self.assertLess(remainder, y)
```

## Comparison with Pytest

| Feature | Unittest | Pytest |
|---------|----------|--------|
| **Assertions** | `self.assertEqual()`, `self.assertTrue()` | `assert` statements |
| **Error Reporting** | Unittest failure exceptions | Pytest assertion rewriting |
| **Test Discovery** | `python -m unittest` | `pytest` |
| **Class Inheritance** | Must inherit from `unittest.TestCase` | No inheritance required |
| **Method Naming** | Must start with `test_` | Must start with `test_` |

## Migration from Pytest to Unittest

If you have existing pytest tests and want to migrate to unittest:

```python
# Before (pytest)
class TestMathProperties:
    @for_all(Gen.int(), Gen.int())
    def test_addition(self, x: int, y: int):
        assert x + y == y + x

# After (unittest)
import unittest

class TestMathProperties(unittest.TestCase):
    @for_all(Gen.int(), Gen.int())
    def test_addition(self, x: int, y: int):
        self.assertEqual(x + y, y + x)
```

The `@for_all` decorator works identically in both frameworks - only the assertion style changes.

## Examples

See the complete examples in:
- `examples/unittest_pytest_comparison.py` - Side-by-side comparison
- `tests/test_unittest_integration.py` - Comprehensive test suite
