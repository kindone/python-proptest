# Properties

Properties define the expected behavior of your code over a range of inputs.

## Defining Properties with `Property(...)`

*   **`Property(predicate: Callable[..., bool | None])`**: Creates a property object explicitly. The `predicate` function receives arguments generated according to the generators passed to `for_all`.
    *   If the predicate returns `False` or throws an error, the property fails.
    *   If the predicate returns `True` or `None` (implicitly returns `None`), the property passes for that input.

    ```python
    from pyproptest import Property, Gen

    # Property: The sum of two non-negative numbers is non-negative
    def sum_property(a: float, b: float):
        assert a + b >= 0  # Using assertions
        # Or: return a + b >= 0

    # Running the property
    prop = Property(sum_property)
    prop.set_num_runs(200).for_all(Gen.int(min_value=0, max_value=100), Gen.int(min_value=0, max_value=100))
    ```

*   **`property.set_num_runs(n: int)`**: Configures the number of random test cases to execute when `for_all` is called on a `Property` instance. Returns the `Property` instance for chaining.

*   **`property.example(...args: Any)`**: Runs the property's predicate *once* with the explicitly provided `args`. Useful for debugging specific edge cases.

    ```python
    def prop_func(a: int, b: int):
        return a > b

    prop = Property(prop_func)
    prop.example(5, 3)  # Runs the predicate with a=5, b=3
    prop.example(3, 5)  # returns False
    ```

## Defining and Running Properties with `run_for_all(...)` (Lambda-Based)

*   **`run_for_all(predicate: Callable[..., bool | None], *generators: Generator[Any])`**: Perfect for simple property checks that can be expressed as lambdas. This is the most concise way to define and immediately check a property. It implicitly creates and runs the property. You don't need to manually create a `Property` object.

    ```python
    from pyproptest import run_for_all, Gen

    # Property: Reversing a list twice yields the original list
    def test_double_reverse():
        def property_func(arr: list):
            # Predicate using assertions
            assert list(reversed(list(reversed(arr)))) == arr
            return True

        run_for_all(property_func, Gen.list(Gen.str(min_length=0, max_length=5), min_length=0, max_length=10))

    # Property: String concatenation length
    def test_string_concatenation_length():
        def property_func(s1: str, s2: str):
            # Predicate returning a boolean
            return len(s1 + s2) == len(s1) + len(s2)

        run_for_all(property_func, Gen.str(min_length=0, max_length=20), Gen.str(min_length=0, max_length=20))

    # Property: Absolute value is non-negative
    def test_absolute_value_non_negative():
        def property_func(num: float):
            assert abs(num) >= 0
            return True

        run_for_all(property_func, Gen.float())  # Use float generator

    # Property: Tuple elements follow constraints
    def test_tuple_constraints():
        def property_func(tup: tuple):
            num, bool_val = tup
            assert num >= 0
            assert num <= 10
            assert isinstance(bool_val, bool)
            return True

        run_for_all(property_func, Gen.tuple(Gen.int(min_value=0, max_value=10), Gen.bool()))
    ```

## Decorator-based Properties

PyPropTest also supports a decorator-based approach for defining properties, similar to Hypothesis. This is perfect for complex assertions that benefit from explicit parameter signatures:

```python
from pyproptest import for_all, integers, text

@for_all(integers(), integers())
def test_addition_commutativity(x: int, y: int):
    """Test that addition is commutative."""
    assert x + y == y + x

@for_all(text(), text())
def test_string_concatenation(s1: str, s2: str):
    """Test string concatenation properties."""
    result = s1 + s2
    assert len(result) == len(s1) + len(s2)
    assert result.startswith(s1)
    assert result.endswith(s2)

# Run the tests
test_addition_commutativity()
test_string_concatenation()
```

## Choosing the Right Approach

PyPropTest provides multiple ways to define property tests. Choose based on your needs:

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

    assert result is True
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

## Configuration Options

### Number of Runs

```python
from pyproptest import Property, Gen

def my_property(x: int):
    return x >= 0

# Using Property class
prop = Property(my_property)
prop.set_num_runs(500).for_all(Gen.int())

# Using run_for_all with num_runs parameter
run_for_all(my_property, Gen.int(), num_runs=500)
```

### Seed for Reproducibility

```python
from pyproptest import run_for_all, Gen

def my_property(x: int):
    return x >= 0

# Using a fixed seed for reproducible tests
run_for_all(my_property, Gen.int(), seed=42)

# Using a string seed
run_for_all(my_property, Gen.int(), seed="my_test_seed")
```

## Error Handling

When a property fails, PyPropTest will:

1. **Report the failure** with the original failing input
2. **Attempt shrinking** to find a minimal counterexample
3. **Raise an exception** with details about the failure

```python
from pyproptest import run_for_all, Gen, PropertyTestError

def failing_property(x: int):
    return x < 100  # This will fail for x >= 100

try:
    run_for_all(failing_property, Gen.int())
except PropertyTestError as e:
    print(f"Property failed: {e}")
    # The error will include the minimal counterexample found through shrinking
```

## Best Practices

1. **Keep properties simple**: Each property should test one specific invariant
2. **Use meaningful names**: Name your properties clearly to understand what they test
3. **Handle edge cases**: Consider what happens with empty lists, zero values, etc.
4. **Use appropriate generators**: Choose generators that match your function's expected input domain
5. **Test both positive and negative cases**: Verify that your function behaves correctly in both success and failure scenarios

```python
# Good: Simple, focused property
def test_list_length_after_append():
    def property_func(lst: list, item: str):
        original_length = len(lst)
        lst.append(item)
        return len(lst) == original_length + 1

    run_for_all(property_func, Gen.list(Gen.str()), Gen.str())

# Good: Testing edge cases
def test_division_by_zero():
    def property_func(a: float, b: float):
        if b == 0:
            # Test that division by zero raises an exception
            try:
                result = a / b
                return False  # Should not reach here
            except ZeroDivisionError:
                return True  # Expected behavior
        else:
            # Test normal division
            result = a / b
            return isinstance(result, float)

    run_for_all(property_func, Gen.float(), Gen.float())
```
