# Combinators

Combinators are higher-order functions that manipulate or combine existing generators (`Gen`) to create new, more sophisticated generators. They are the primary mechanism in `python-proptest` for building generators that produce complex data structures, implement specific constraints, or tailor data generation to the precise needs of your tests. Instead of just using basic generators like `Gen.int()` or `Gen.str()`, combinators allow you to compose these building blocks into generators for custom objects, lists with specific properties, or data distributions that mimic real-world scenarios. Mastering combinators is key to unlocking the full potential of property-based testing.

## Combinator Summary Table

| Combinator                                   | Description                                                              | Key Parameters                       | Example Usage                                                                 |
| :------------------------------------------- | :----------------------------------------------------------------------- | :----------------------------------- | :---------------------------------------------------------------------------- |
| **Selection**                                |                                                                          |                                      |                                                                               |
| `Gen.one_of(...gens)`                         | Randomly picks one generator from `gens` to produce a value. Use `weighted_gen` to adjust probabilities. | `...generators` (can be `Weighted`)  | `Gen.one_of(Gen.int(min_value=0, max_value=10), Gen.int(min_value=20, max_value=30))` (Union of ranges)                           |
| `Gen.element_of(...values)`                   | Randomly picks one value from the provided `values`. Use `weighted_value` to adjust probabilities. | `...values` (can be `Weighted`)      | `Gen.element_of(2, 3, 5, 7)` (Prime numbers < 10)     |
| `Gen.weighted_gen(gen, weight)`               | Wraps a generator with a `weight` for `Gen.one_of`.                       | `generator`, `weight`                | `Gen.weighted_gen(Gen.str(), 0.8)` (80% probability)               |
| `Gen.weighted_value(value, weight)`           | Wraps a value with a `weight` for `Gen.element_of`.                       | `value`, `weight`                    | `Gen.weighted_value('a', 0.2)` (20% probability)                          |
| **Transformation**                           |                                                                          |                                      |                                                                               |
| `generator.map(f)`                           | Applies function `f` to each generated value.                            | `(value: T) -> U`                    | `Gen.int(min_value=1, max_value=100).map(lambda n: str(n))` (Stringified numbers within [1,100])                             |
| `generator.filter(predicate)`                | Only keeps values where `predicate(value)` is true.                      | `(value: T) -> bool`              | `Gen.int().filter(lambda n: n % 2 == 0)` (Even numbers)                       |
| `generator.flat_map(f)` / `generator.chain(f)` | Creates a dependent generator using `f(value)` which returns a new Gen. | `(value: T) -> Generator[U]`         | `Gen.int(min_value=1, max_value=5).flat_map(lambda n: Gen.str(min_length=n))` (String of random length within [1,5))   |
| **Class Construction**                       |                                                                          |                                      |                                                                               |
| `Gen.construct(Class, ...arg_gens)`           | Creates class instances using `Class(...args)` from `arg_gens`.       | `Constructor`, `...argument_generators` | `Gen.construct(Point, Gen.int(), Gen.int())` (Construct Point object)       |

## Selection Combinators

### `Gen.one_of(*generators)`

Randomly chooses one generator from the provided generators to produce a value. Each generator has an equal probability of being selected unless weights are specified.

**Parameters:**
- `*generators` (Generator or Weighted): Variable number of generators, optionally wrapped with `Gen.weighted_gen()`

**Examples:**
```python
# Equal probability selection
Gen.one_of(
    Gen.int(min_value=0, max_value=10),
    Gen.int(min_value=20, max_value=30),
    Gen.str(min_length=1, max_length=5)
)

# Weighted selection
Gen.one_of(
    Gen.weighted_gen(Gen.str(), 0.8),  # 80% probability
    Gen.weighted_gen(Gen.int(), 0.2)   # 20% probability
)

# Mixed weighted and unweighted
Gen.one_of(
    Gen.weighted_gen(Gen.str(), 0.5),  # 50% probability
    Gen.int(),                         # 25% probability (remaining split)
    Gen.bool()                         # 25% probability (remaining split)
)
```

**Use Cases:**
- Creating union types
- Testing multiple data types
- Implementing weighted random selection
- Creating complex data distributions

### `Gen.element_of(*values)`

Randomly chooses one value from the provided values. Each value has an equal probability of being selected unless weights are specified.

**Parameters:**
- `*values` (Any or WeightedValue): Variable number of values, optionally wrapped with `Gen.weighted_value()`

**Examples:**
```python
# Equal probability selection
Gen.element_of("red", "green", "blue", "yellow")

# Prime numbers
Gen.element_of(2, 3, 5, 7, 11, 13, 17, 19)

# Weighted selection
Gen.element_of(
    Gen.weighted_value("common", 0.7),    # 70% probability
    Gen.weighted_value("rare", 0.3)       # 30% probability
)

# Mixed weighted and unweighted
Gen.element_of(
    Gen.weighted_value("frequent", 0.6),  # 60% probability
    "normal",                             # 20% probability
    "rare"                                # 20% probability
)
```

**Use Cases:**
- Testing enum-like values
- Creating categorical data
- Implementing weighted choices
- Testing specific edge cases

### `Gen.weighted_gen(generator, weight)`

Wraps a generator with a weight for use in `Gen.one_of()`. The weight determines the probability of selecting this generator.

**Parameters:**
- `generator` (Generator): The generator to wrap
- `weight` (float): Probability weight (0.0 to 1.0)

**Examples:**
```python
# Create weighted generators
common_gen = Gen.weighted_gen(Gen.str(), 0.8)
rare_gen = Gen.weighted_gen(Gen.int(), 0.2)

# Use in one_of
Gen.one_of(common_gen, rare_gen)

# Multiple weighted generators
Gen.one_of(
    Gen.weighted_gen(Gen.str(min_length=1, max_length=3), 0.5),
    Gen.weighted_gen(Gen.int(min_value=1, max_value=10), 0.3),
    Gen.weighted_gen(Gen.bool(), 0.2)
)
```

**Use Cases:**
- Creating realistic data distributions
- Testing with biased inputs
- Implementing weighted random selection
- Simulating real-world scenarios

### `Gen.weighted_value(value, weight)`

Wraps a value with a weight for use in `Gen.element_of()`. The weight determines the probability of selecting this value.

**Parameters:**
- `value` (Any): The value to wrap
- `weight` (float): Probability weight (0.0 to 1.0)

**Examples:**
```python
# Create weighted values
common_value = Gen.weighted_value("success", 0.9)
rare_value = Gen.weighted_value("error", 0.1)

# Use in element_of
Gen.element_of(common_value, rare_value)

# Multiple weighted values
Gen.element_of(
    Gen.weighted_value("low", 0.5),
    Gen.weighted_value("medium", 0.3),
    Gen.weighted_value("high", 0.2)
)
```

**Use Cases:**
- Creating realistic categorical distributions
- Testing with biased inputs
- Implementing weighted choices
- Simulating real-world scenarios

## Transformation Combinators

### `generator.map(func)`

Transforms each generated value using the provided function. This is one of the most commonly used combinators.

**Parameters:**
- `func` (Callable[[T], U]): Function that transforms a value of type T to type U

**Examples:**
```python
# Transform integers to strings
Gen.int(min_value=1, max_value=100).map(lambda n: str(n))

# Transform to custom objects
def create_user(id_num):
    return {"id": id_num, "email": f"user{id_num}@example.com"}

Gen.int(min_value=1, max_value=1000).map(create_user)

# Transform to tuples
Gen.int().map(lambda x: (x, x * 2, x * 3))

# Transform strings
Gen.str().map(lambda s: s.upper())

# Transform lists
Gen.list(Gen.int()).map(lambda lst: sorted(lst))
```

**Use Cases:**
- Converting between data types
- Creating custom objects
- Applying transformations to generated data
- Building complex data structures

### `generator.filter(predicate)`

Only keeps values that satisfy the given predicate function. Be cautious with restrictive predicates as they can slow down generation.

**Parameters:**
- `predicate` (Callable[[T], bool]): Function that returns True for values to keep

**Examples:**
```python
# Filter even numbers
Gen.int().filter(lambda n: n % 2 == 0)

# Filter non-empty strings
Gen.str().filter(lambda s: len(s) > 0)

# Filter positive numbers
Gen.float().filter(lambda x: x > 0)

# Filter lists with specific properties
Gen.list(Gen.int()).filter(lambda lst: len(lst) > 2 and all(x > 0 for x in lst))

# Filter based on multiple conditions
Gen.int().filter(lambda n: n > 0 and n < 100 and n % 3 == 0)
```

**Use Cases:**
- Restricting value ranges
- Testing specific conditions
- Creating constrained test data
- Implementing business rules

**Performance Considerations:**
- Avoid overly restrictive predicates
- Consider using `Gen.in_range()` instead of filtering ranges
- Use `Gen.one_of()` for categorical filtering

### `generator.flat_map(func)`

Creates a dependent generator where the function takes a generated value and returns a new generator. This is powerful for creating related test data.

**Parameters:**
- `func` (Callable[[T], Generator[U]]): Function that takes a value and returns a generator

**Examples:**
```python
# Generate string length based on integer
Gen.int(min_value=1, max_value=10).flat_map(
    lambda length: Gen.str(min_length=length, max_length=length)
)

# Generate list size based on integer
Gen.int(min_value=1, max_value=5).flat_map(
    lambda size: Gen.list(Gen.int(), min_length=size, max_length=size)
)

# Generate dependent values
def create_dependent_data(x):
    if x > 0:
        return Gen.int(min_value=1, max_value=x)
    else:
        return Gen.int(min_value=x, max_value=-1)

Gen.int().flat_map(create_dependent_data)

# Generate nested structures
Gen.int(min_value=1, max_value=3).flat_map(
    lambda depth: Gen.list(
        Gen.str(min_length=depth, max_length=depth),
        min_length=depth,
        max_length=depth
    )
)
```

**Use Cases:**
- Creating dependent test data
- Generating related values
- Building complex nested structures
- Implementing conditional generation

## Class Construction Combinators

### `Gen.construct(Type, *generators)`

Creates instances of a class using the specified generators for constructor arguments.

**Parameters:**
- `Type` (type): Class to instantiate
- `*generators` (Generator): Generators for constructor arguments

**Examples:**
```python
# Simple class construction
class Point:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

Gen.construct(Point, Gen.int(), Gen.int())

# Complex class construction
class Person:
    def __init__(self, name: str, age: int, email: str):
        self.name = name
        self.age = age
        self.email = email

Gen.construct(
    Person,
    Gen.str(min_length=1, max_length=20),
    Gen.int(min_value=0, max_value=120),
    Gen.str(min_length=5, max_length=50)
)

# Using with other combinators
class Rectangle:
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height

Gen.construct(
    Rectangle,
    Gen.float(min_value=0.1, max_value=100.0),
    Gen.float(min_value=0.1, max_value=100.0)
).filter(lambda rect: rect.width > rect.height)  # Only tall rectangles
```

**Use Cases:**
- Testing custom classes
- Generating domain objects
- Creating structured test data
- Testing object-oriented code

## Advanced Combinator Patterns

### Chaining Combinators

Combinators can be chained together to create complex generators:

```python
# Chain multiple transformations
Gen.int(min_value=1, max_value=100)\
    .filter(lambda x: x % 2 == 0)\
    .map(lambda x: x * 2)\
    .map(str)

# Chain with selection
Gen.one_of(
    Gen.int().filter(lambda x: x > 0),
    Gen.str().filter(lambda s: len(s) > 0)
).map(lambda x: f"Value: {x}")

# Chain with construction
Gen.construct(
    Point,
    Gen.int().filter(lambda x: x > 0),
    Gen.int().filter(lambda y: y > 0)
).filter(lambda p: p.x + p.y > 10)
```

### Conditional Generation

Use `flat_map` for conditional generation:

```python
# Conditional based on value
Gen.int().flat_map(
    lambda x: Gen.str(min_length=1, max_length=5) if x > 0 
              else Gen.just("negative")
)

# Conditional based on type
Gen.one_of(Gen.int(), Gen.str()).flat_map(
    lambda x: Gen.list(Gen.int(), min_length=1, max_length=3) if isinstance(x, int)
              else Gen.list(Gen.str(), min_length=1, max_length=3)
)
```

### Recursive Generation

Use `Gen.lazy()` for recursive generators:

```python
# Recursive tree structure
def tree_gen():
    return Gen.one_of(
        Gen.just(None),  # Leaf node
        Gen.construct(
            TreeNode,
            Gen.int(),
            Gen.lazy(tree_gen),  # Left subtree
            Gen.lazy(tree_gen)   # Right subtree
        )
    )

class TreeNode:
    def __init__(self, value, left, right):
        self.value = value
        self.left = left
        self.right = right
```

## Best Practices

### Performance Considerations

1. **Avoid overly restrictive filters**: Use `Gen.in_range()` instead of filtering ranges
2. **Use appropriate generators**: Choose the right generator for your needs
3. **Consider weights**: Use weighted selection for realistic distributions
4. **Chain efficiently**: Order transformations to minimize rejected values

### Readability Tips

1. **Use descriptive names**: Name your generators clearly
2. **Break down complex generators**: Split complex logic into smaller parts
3. **Add comments**: Explain complex generation logic
4. **Use type hints**: Help with IDE support and documentation

### Testing Strategies

1. **Test edge cases**: Use `Gen.just()` for specific values
2. **Test realistic data**: Use weighted selection for realistic distributions
3. **Test boundary conditions**: Use `Gen.in_range()` for boundary testing
4. **Test error conditions**: Use `Gen.element_of()` for error cases

Combinators are the key to creating sophisticated test data that matches your specific needs. By combining and transforming basic generators, you can create generators for any data structure or constraint your tests require.