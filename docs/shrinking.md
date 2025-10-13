# Shrinking

When `run_for_all` (either standalone or called on a `Property` instance) detects a failing test case, it automatically tries to "shrink" the failing input to a simpler version that still causes the failure. This helps pinpoint the root cause.

*   Shrinking explores smaller integers, shorter strings/lists, subsets of sets, and simpler structures based on how the generators were defined and combined.
*   The error message thrown by `run_for_all` on failure typically includes the original failing input and the final, shrunk failing input.

```python
from pyproptest import run_for_all, Gen, PropertyTestError

# Example where shrinking is useful (using standalone run_for_all)
def test_failing_property():
    # Generator for pairs [a, b] where a <= b
    pair_gen = Gen.int(min_value=0, max_value=1000).flat_map(
        lambda a: Gen.tuple(Gen.just(a), Gen.int(min_value=a, max_value=1000))
    )

    def property_func(tup):
        # This property fails if the difference is large
        return tup[1] - tup[0] <= 5

    try:
        run_for_all(property_func, pair_gen)
    except PropertyTestError as e:
        # The error message will likely show a shrunk example,
        # e.g., "property failed (simplest args found by shrinking): ..."
        print(f"Property failed: {e}")
        # The shrunk example will be much simpler than the original failing input
```

## How Shrinking Works

PyPropTest's shrinking process follows these principles:

1. **Start with the failing input**: When a property fails, the system records the exact input that caused the failure.

2. **Generate shrink candidates**: For each type of input, PyPropTest generates simpler versions:
   - **Integers**: Shrinks towards 0 (e.g., 100 → 50 → 25 → 12 → 6 → 3 → 1 → 0)
   - **Strings**: Shrinks by removing characters (e.g., "hello" → "hell" → "hel" → "he" → "h" → "")
   - **Lists**: Shrinks by removing elements and making elements simpler
   - **Dictionaries**: Shrinks by removing key-value pairs and simplifying values

3. **Test each candidate**: Each shrink candidate is tested against the property to see if it still fails.

4. **Keep the simplest failing case**: The shrinking process continues until no simpler input can be found that still causes the failure.

## Shrinking Examples

### Integer Shrinking

```python
from pyproptest import run_for_all, Gen, PropertyTestError

def test_integer_shrinking():
    def property_func(x: int):
        # This will fail for x >= 100
        return x < 100

    try:
        run_for_all(property_func, Gen.int(min_value=0, max_value=1000))
    except PropertyTestError as e:
        print(f"Failed with input: {e}")
        # The shrunk input will likely be exactly 100, the minimal failing case
```

### String Shrinking

```python
from pyproptest import run_for_all, Gen, PropertyTestError

def test_string_shrinking():
    def property_func(s: str):
        # This will fail for strings containing 'x'
        return 'x' not in s

    try:
        run_for_all(property_func, Gen.str(min_length=0, max_length=10))
    except PropertyTestError as e:
        print(f"Failed with input: {e}")
        # The shrunk input will likely be just "x", the minimal failing case
```

### List Shrinking

```python
from pyproptest import run_for_all, Gen, PropertyTestError

def test_list_shrinking():
    def property_func(lst: list):
        # This will fail for lists with more than 3 elements
        return len(lst) <= 3

    try:
        run_for_all(property_func, Gen.list(Gen.int(), min_length=0, max_length=10))
    except PropertyTestError as e:
        print(f"Failed with input: {e}")
        # The shrunk input will likely be a list with exactly 4 elements
```

### Complex Structure Shrinking

```python
from pyproptest import run_for_all, Gen, PropertyTestError

def test_complex_shrinking():
    def property_func(data):
        # This will fail for dictionaries with 'error' key
        return 'error' not in data

    # Generate complex nested data
    complex_gen = Gen.dict(
        Gen.str(min_length=1, max_length=5),
        Gen.one_of(
            Gen.str(),
            Gen.int(),
            Gen.list(Gen.str(), min_length=0, max_length=3)
        ),
        min_size=1,
        max_size=5
    )

    try:
        run_for_all(property_func, complex_gen)
    except PropertyTestError as e:
        print(f"Failed with input: {e}")
        # The shrunk input will be the simplest dictionary that still contains 'error'
```

## Advanced Shrinking

PyPropTest includes advanced shrinking strategies for more complex scenarios:

### Element-wise Shrinking

For collections, PyPropTest can shrink individual elements while keeping the structure:

```python
from pyproptest import run_for_all, Gen, PropertyTestError

def test_element_wise_shrinking():
    def property_func(numbers: list):
        # This will fail if any number is >= 100
        return all(n < 100 for n in numbers)

    try:
        run_for_all(property_func, Gen.list(Gen.int(min_value=0, max_value=200), min_length=1, max_length=5))
    except PropertyTestError as e:
        print(f"Failed with input: {e}")
        # The shrunk input will have the minimal number that causes failure
```

### Membership-wise Shrinking

For sets and dictionaries, PyPropTest can remove elements to find the minimal failing subset:

```python
from pyproptest import run_for_all, Gen, PropertyTestError

def test_membership_shrinking():
    def property_func(items: set):
        # This will fail if the set contains 42
        return 42 not in items

    try:
        run_for_all(property_func, Gen.set(Gen.int(min_value=0, max_value=100), min_size=1, max_size=10))
    except PropertyTestError as e:
        print(f"Failed with input: {e}")
        # The shrunk input will likely be just {42}
```

## Custom Shrinking

You can influence the shrinking behavior by using specific generators or combinators:

### Using `Gen.just()` for Fixed Values

```python
from pyproptest import run_for_all, Gen

def test_with_fixed_values():
    def property_func(x: int):
        return x != 42  # This will always fail for x=42

    # Using Gen.just() ensures the value 42 is always generated
    run_for_all(property_func, Gen.just(42))
    # The shrunk input will be exactly 42
```

### Using `Gen.element_of()` for Specific Values

```python
from pyproptest import run_for_all, Gen, PropertyTestError

def test_with_specific_values():
    def property_func(x: int):
        return x not in [10, 20, 30]  # This will fail for these values

    try:
        run_for_all(property_func, Gen.element_of(10, 20, 30, 40, 50))
    except PropertyTestError as e:
        print(f"Failed with input: {e}")
        # The shrunk input will be one of the failing values: 10, 20, or 30
```

## Shrinking Configuration

You can control shrinking behavior through the `Property` class:

```python
from pyproptest import Property, Gen

def my_property(x: int):
    return x < 100

# Create a property with custom shrinking settings
prop = Property(my_property)
prop.set_num_runs(100)  # Number of test runs
prop.for_all(Gen.int(min_value=0, max_value=1000))

# The shrinking process is automatic and cannot be disabled,
# but you can influence it by choosing appropriate generators
```

## Best Practices for Shrinking

1. **Use appropriate generators**: Choose generators that produce values close to the boundaries you want to test.

2. **Avoid overly complex predicates**: Simple predicates shrink better than complex ones.

3. **Test edge cases explicitly**: Use `Gen.just()` or `Gen.element_of()` to test specific values.

4. **Consider the shrinking path**: Think about what the minimal failing case should be when designing your properties.

```python
# Good: Simple predicate that shrinks well
def good_property(x: int):
    return x < 100

# Less ideal: Complex predicate that might not shrink as effectively
def complex_property(x: int):
    return x < 100 and x % 2 == 0 and x > 0 and str(x).count('1') < 2
```

The shrinking process is one of the most powerful features of property-based testing, as it helps you understand exactly what conditions cause your code to fail, making debugging much more effective.
