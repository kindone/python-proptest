# Pytest Integration Best Practices

PyPropTest provides seamless integration with pytest through the `@for_all` decorator. This document explains the recommended approaches and why certain patterns work better than others.

## ✅ Recommended Approach: Nested Property Tests

The most reliable and pytest-friendly approach is to nest the property test inside the pytest method:

```python
import pytest
from pyproptest import for_all, Gen, integers, text

class TestMathProperties:
    """Recommended approach: nested property tests."""

    def test_addition_commutativity(self):
        """Test that addition is commutative."""
        @for_all(integers(), integers())
        def test_commutativity(self, x: int, y: int):
            assert x + y == y + x

        test_commutativity(self)

    def test_multiplication_associativity(self):
        """Test that multiplication is associative."""
        @for_all(integers(), integers(), integers())
        def test_associativity(self, x: int, y: int, z: int):
            assert (x * y) * z == x * (y * z)

        test_associativity(self)

    def test_string_properties(self):
        """Test string concatenation properties."""
        @for_all(text(), text())
        def test_concatenation(self, s1: str, s2: str):
            combined = s1 + s2
            assert len(combined) == len(s1) + len(s2)
            assert combined.startswith(s1)
            assert combined.endswith(s2)

        test_concatenation(self)
```

### Why This Approach Works Best

1. **No Fixture Conflicts**: Pytest doesn't try to inject parameters as fixtures
2. **Clear Test Structure**: Each pytest method is a clear test case
3. **Proper Error Reporting**: Failures are reported with clear test method names
4. **Pytest Discovery**: Works perfectly with pytest's test discovery
5. **IDE Support**: IDEs can properly identify and run individual tests

## ❌ Problematic Approach: Direct Method Decoration

**This approach does NOT work** due to pytest's fixture injection system:

```python
# ❌ DON'T DO THIS - Will cause "fixture not found" errors
class TestMathProperties:
    @for_all(integers(), integers())
    def test_addition_commutativity(self, x: int, y: int):
        assert x + y == y + x
```

**Why it fails**: Pytest tries to inject `x` and `y` as fixtures, which don't exist.

## ✅ Alternative: Standalone Functions

For non-class-based tests, you can use standalone functions:

```python
from pyproptest import for_all, integers

@for_all(integers(), integers())
def test_addition_commutativity(x: int, y: int):
    """Standalone property test."""
    assert x + y == y + x

# Run with: python -m pytest test_file.py::test_addition_commutativity
```

## 🎯 Advanced Patterns

### Multiple Property Tests in One Method

```python
class TestAdvancedPatterns:
    def test_multiple_math_properties(self):
        """Test multiple mathematical properties."""

        @for_all(integers(), integers())
        def test_commutativity(self, x: int, y: int):
            assert x + y == y + x

        @for_all(integers(), integers(), integers())
        def test_associativity(self, x: int, y: int, z: int):
            assert (x + y) + z == x + (y + z)

        # Run both property tests
        test_commutativity(self)
        test_associativity(self)
```

### Conditional Property Tests

```python
class TestConditionalProperties:
    def test_division_properties(self):
        """Test division properties with assumptions."""

        @for_all(integers(), integers())
        def test_division_property(self, x: int, y: int):
            from pyproptest import assume
            assume(y != 0)  # Skip test cases where y is 0
            assert (x // y) * y + (x % y) == x

        test_division_property(self)
```

### Failing Properties with Shrinking

```python
class TestFailingProperties:
    def test_failing_property_demonstrates_shrinking(self):
        """Test that failing properties show minimal counterexamples."""

        @for_all(integers())
        def test_failing_property(self, x: int):
            # This will fail for x >= 50
            assert x < 50

        # This should raise an AssertionError with shrinking information
        with pytest.raises(AssertionError) as exc_info:
            test_failing_property(self)

        # The error message should contain failure information
        error_msg = str(exc_info.value)
        assert "Property failed" in error_msg
        assert "run" in error_msg.lower()
```

## 🚀 Running Tests

### Using pytest directly

```bash
# Run all tests in a file
pytest test_file.py -v

# Run specific test class
pytest test_file.py::TestMathProperties -v

# Run specific test method
pytest test_file.py::TestMathProperties::test_addition_commutativity -v

# Run tests matching a pattern
pytest -k "test_addition" -v
```

### Using pytest discovery

```bash
# Run all tests in the current directory
pytest -v

# Run tests with specific markers
pytest -m "not slow" -v
```

## 📝 Best Practices Summary

1. **Use nested property tests** inside pytest methods for class-based tests
2. **Use standalone functions** for simple property tests
3. **Keep property tests focused** - one property per nested test
4. **Use descriptive names** for both pytest methods and property functions
5. **Handle assumptions** with `assume()` for preconditions
6. **Test failing properties** to verify shrinking works
7. **Use pytest's filtering** to run specific tests during development

## 🔧 Migration Guide

If you have existing property tests using other approaches:

### From Direct Decoration (Broken)
```python
# ❌ Old broken approach
@for_all(integers(), integers())
def test_commutativity(self, x: int, y: int):
    assert x + y == y + x
```

### To Nested Approach (Recommended)
```python
# ✅ New working approach
def test_commutativity(self):
    @for_all(integers(), integers())
    def test_commutativity(self, x: int, y: int):
        assert x + y == y + x
    test_commutativity(self)
```

This approach provides the best balance of pytest integration, clarity, and functionality.
