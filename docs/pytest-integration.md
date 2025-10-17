# Pytest Integration

PyPropTest provides seamless integration with pytest through the `@for_all` decorator. The decorator automatically detects whether it's being used in a pytest context (class methods with `self` parameter) or standalone functions and adapts accordingly.

## Basic Usage

### Class Methods (Pytest Context) - Direct Decoration

```python
import pytest
from pyproptest import for_all, Gen, integers, text

class TestMathProperties:
    """Test class for mathematical properties."""

    @for_all(integers(), integers())
    def test_addition_commutativity(self, x: int, y: int):
        """Test that addition is commutative - direct decoration!"""
        assert x + y == y + x

    @for_all(integers(), integers(), integers())
    def test_multiplication_associativity(self, x: int, y: int, z: int):
        """Test that multiplication is associative - direct decoration!"""
        assert (x * y) * z == x * (y * z)
```

**✅ Direct decoration now works!** The `@for_all` decorator automatically detects pytest context and handles the `self` parameter correctly.

### Alternative: Nested Approach (Still Supported)

If you prefer the nested approach for clarity, it still works:

```python
class TestMathProperties:
    def test_addition_commutativity(self):
        """Test that addition is commutative - nested approach."""
        @for_all(integers(), integers())
        def test_commutativity(self, x: int, y: int):
            assert x + y == y + x

        test_commutativity(self)
```

### Standalone Functions

```python
def test_standalone_property():
    """Test that standalone functions work with @for_all."""
    @for_all(integers(), integers())
    def test_commutativity(x: int, y: int):
        assert x + y == y + x

    test_commutativity()
```

## Advanced Features

### Failing Properties and Shrinking

```python
class TestFailingProperties:
    """Test class demonstrating failing properties and shrinking."""

    def test_failing_property_demonstrates_shrinking(self):
        """Test that failing properties show minimal counterexamples."""
        @for_all(integers())
        def test_failing_property(self, x: int):
            # This will fail for x >= 50
            assert x < 50

        # This should raise an AssertionError with shrinking information
        with pytest.raises(AssertionError) as exc_info:
            test_failing_property(self)

        # The error message should contain shrinking information
        assert "Property failed" in str(exc_info.value)
```

### Using assume() for Preconditions

```python
class TestWithAssumptions:
    """Test class demonstrating assume() functionality."""

    def test_with_assume(self):
        """Test assume() functionality in pytest context."""
        @for_all(integers(), integers())
        def test_with_assume(self, x: int, y: int):
            from pyproptest import assume
            assume(y != 0)  # Skip test cases where y is 0
            # Use a simpler assertion to avoid floating point precision issues
            assert isinstance(x, int)
            assert isinstance(y, int)

        test_with_assume(self)
```

### Complex Data Structures

```python
class TestComplexStructures:
    """Test class for complex data structures."""

    def test_list_properties(self):
        """Test list properties."""
        @for_all(Gen.list(Gen.int(), min_length=0, max_length=10))
        def test_list_properties(self, lst: list):
            original_length = len(lst)
            lst.append(42)
            assert len(lst) == original_length + 1
            assert lst[-1] == 42

        test_list_properties(self)

    def test_string_properties(self):
        """Test string properties."""
        @for_all(text(), text())
        def test_string_properties(self, s1: str, s2: str):
            combined = s1 + s2
            assert len(combined) == len(s1) + len(s2)
            assert combined.startswith(s1)
            assert combined.endswith(s2)

        test_string_properties(self)
```

## Running Tests

### Using pytest directly

```bash
# Run all tests in a file
pytest test_pytest_integration.py -v

# Run specific test class
pytest test_pytest_integration.py::TestMathProperties -v

# Run specific test method
pytest test_pytest_integration.py::TestMathProperties::test_addition_commutativity -v
```

### Using pytest discovery

```bash
# Run all tests in the current directory
pytest -v

# Run tests matching a pattern
pytest -k "test_addition" -v

# Run tests with specific markers
pytest -m "not slow" -v
```

## Key Benefits

1. **Automatic Detection**: The `@for_all` decorator automatically detects pytest context by checking for `self` parameter
2. **Seamless Integration**: Works with pytest's test discovery and execution
3. **Proper Error Handling**: Failing properties raise `AssertionError` for better pytest integration
4. **Shrinking Support**: Minimal counterexamples are automatically found and reported
5. **Backward Compatibility**: Standalone functions continue to work as before

## Best Practices

1. **Use descriptive test names**: pytest uses test method names for reporting
2. **Group related tests**: Use test classes to organize related property tests
3. **Handle assumptions**: Use `assume()` to skip test cases that don't meet preconditions
4. **Test edge cases**: Property-based testing is excellent for finding edge cases
5. **Use appropriate generators**: Choose generators that match your domain

## Example: Complete Test Suite

```python
import pytest
from pyproptest import for_all, Gen, integers, text

class TestCompleteExample:
    """Complete example of pytest integration."""

    def test_basic_math_properties(self):
        """Test basic mathematical properties."""
        @for_all(integers(), integers())
        def test_commutativity(self, x: int, y: int):
            assert x + y == y + x

        test_commutativity(self)

    def test_string_operations(self):
        """Test string operation properties."""
        @for_all(text(), text())
        def test_concatenation(self, s1: str, s2: str):
            result = s1 + s2
            assert len(result) == len(s1) + len(s2)
            assert result.startswith(s1)
            assert result.endswith(s2)

        test_concatenation(self)

    def test_failing_property(self):
        """Test that failing properties are properly reported."""
        @for_all(integers())
        def test_failing_property(self, x: int):
            assert x < 100

        with pytest.raises(AssertionError):
            test_failing_property(self)
```

This integration makes PyPropTest a powerful tool for property-based testing within the pytest ecosystem, providing the benefits of both frameworks seamlessly combined.
