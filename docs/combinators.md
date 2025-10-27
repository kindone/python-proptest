# Combinators

Combinators are higher-order functions that manipulate or combine existing generators (`Gen`) to create new, more sophisticated generators. They are the primary mechanism in `python-proptest` for building generators that produce complex data structures, implement specific constraints, or tailor data generation to the precise needs of your tests. Instead of just using basic generators like `Gen.int()` or `Gen.str()`, combinators allow you to compose these building blocks into generators for custom objects, lists with specific properties, or data distributions that mimic real-world scenarios. Mastering combinators is key to unlocking the full potential of property-based testing.

## Combinator Summary Table

| Combinator                                   | Description                                                              | Key Parameters                       | Example Usage                                                                 |
| :------------------------------------------- | :----------------------------------------------------------------------- | :----------------------------------- | :---------------------------------------------------------------------------- |
| **Selection**                                |                                                                          |                                      |                                                                               |
| [`Gen.one_of(...gens)`](#genone_ofgenerators)                         | Randomly picks one generator from `gens` to produce a value. Use [`weighted_gen`](#genweighted_gengenerator-weight) to adjust probabilities. | `...generators` (can be `Weighted`)  | `Gen.one_of(Gen.int(min_value=0, max_value=10), Gen.int(min_value=20, max_value=30))` (Union of ranges)                           |
| [`Gen.element_of(...values)`](#genelement_ofvalues)                   | Randomly picks one value from the provided `values`. Use [`weighted_value`](#genweighted_valuevalue-weight) to adjust probabilities. | `...values` (can be `Weighted`)      | `Gen.element_of(2, 3, 5, 7)` (Prime numbers < 10)     |
| [`Gen.weighted_gen(gen, weight)`](#genweighted_gengenerator-weight)               | Wraps a generator with a `weight` for [`Gen.one_of`](#genone_ofgenerators).                       | `generator`, `weight`                | `Gen.weighted_gen(Gen.str(), 0.8)` (80% probability)               |
| [`Gen.weighted_value(value, weight)`](#genweighted_valuevalue-weight)           | Wraps a value with a `weight` for [`Gen.element_of`](#genelement_ofvalues).                       | `value`, `weight`                    | `Gen.weighted_value('a', 0.2)` (20% probability)                          |
| **Transformation**                           |                                                                          |                                      |                                                                               |
| [`generator.map(f)`](#generatormapfunc)                           | Applies function `f` to each generated value.                            | `(value: T) -> U`                    | `Gen.int(min_value=1, max_value=100).map(lambda n: str(n))` (Stringified numbers within [1,100])                             |
| [`generator.filter(predicate)`](#generatorfilterpredicate)                | Only keeps values where `predicate(value)` is true.                      | `(value: T) -> bool`              | `Gen.int().filter(lambda n: n % 2 == 0)` (Even numbers)                       |
| [`generator.flat_map(f)`](#generatorflat_mapfunc) / [`generator.chain(f)`](#generatorflat_mapfunc) | Creates a dependent generator using `f(value)` which returns a new Gen. | `(value: T) -> Generator[U]`         | `Gen.int(min_value=1, max_value=5).flat_map(lambda n: Gen.str(min_length=n))` (String of random length within [1,5))   |
| **Dependent Generation**                     |                                                                          |                                      |                                                                               |
| [`Gen.chain(base_gen, gen_factory)`](#genchainbase_gen-gen_factory-generatorchaingen_factory)           | Creates dependent tuple where next value depends on previous.            | `base_gen`, `(value) -> Generator`   | `Gen.chain(Gen.int(1, 12), lambda m: Gen.int(1, days_in_month(m)))` (Valid month/day)         |
| [`Gen.aggregate(initial_gen, gen_factory, ...)`](#genaggregateinitial_gen-gen_factory-min_size-max_size-generatoraggregate) | Generates list where each element depends on previous. | `initial_gen`, `(value) -> Generator`, `min/max_size` | `Gen.aggregate(Gen.int(0, 10), lambda n: Gen.int(n, n+5), min_size=3)` (Increasing list)     |
| [`Gen.accumulate(initial_gen, gen_factory, ...)`](#genaccumulateinitial_gen-gen_factory-min_size-max_size-generatoraccumulate) | Generates final value after N dependent steps. | `initial_gen`, `(value) -> Generator`, `min/max_size` | `Gen.accumulate(Gen.int(50, 50), lambda p: Gen.int(max(0,p-10), min(100,p+10)), min_size=10)` (Random walk endpoint) |
| **Class Construction**                       |                                                                          |                                      |                                                                               |
| [`Gen.construct(Class, ...arg_gens)`](#genconstructtype-generators)           | Creates class instances using `Class(...args)` from `arg_gens`.       | `Constructor`, `...argument_generators` | `Gen.construct(Point, Gen.int(), Gen.int())` (Construct Point object)       |

## Selection Combinators

### `Gen.one_of(*generators)`

Randomly chooses one generator from the provided generators to produce a value. Each generator has an equal probability of being selected unless weights are specified.

**Parameters:**
- `*generators` (Generator or Weighted): Variable number of generators, optionally wrapped with [`Gen.weighted_gen()`](#genweighted_gengenerator-weight)

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

**See Also:** [`Gen.element_of()`](#genelement_ofvalues), [`Gen.weighted_gen()`](#genweighted_gengenerator-weight)

### `Gen.element_of(*values)`

Randomly chooses one value from the provided values. Each value has an equal probability of being selected unless weights are specified.

**Parameters:**
- `*values` (Any or WeightedValue): Variable number of values, optionally wrapped with [`Gen.weighted_value()`](#genweighted_valuevalue-weight)

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

**See Also:** [`Gen.one_of()`](#genone_ofgenerators), [`Gen.weighted_value()`](#genweighted_valuevalue-weight)

### `Gen.weighted_gen(generator, weight)`

Wraps a generator with a weight for use in [`Gen.one_of()`](#genone_ofgenerators). The weight determines the probability of selecting this generator.

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

**See Also:** [`Gen.one_of()`](#genone_ofgenerators), [`Gen.weighted_value()`](#genweighted_valuevalue-weight)

### `Gen.weighted_value(value, weight)`

Wraps a value with a weight for use in [`Gen.element_of()`](#genelement_ofvalues). The weight determines the probability of selecting this value.

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

**See Also:** [`Gen.element_of()`](#genelement_ofvalues), [`Gen.weighted_gen()`](#genweighted_gengenerator-weight)

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

**See Also:** [`generator.filter()`](#generatorfilterpredicate), [`generator.flat_map()`](#generatorflat_mapfunc)

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

**See Also:** [`generator.map()`](#generatormapfunc), [`generator.flat_map()`](#generatorflat_mapfunc)

### `generator.flat_map(func)`

Creates a dependent generator where the function takes a generated value and returns a new generator. This is powerful for creating related test data. For more complex dependent generation, consider using [`Gen.chain()`](#genchainbase_gen-gen_factory-generatorchaingen_factory).

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

**See Also:** [`generator.map()`](#generatormapfunc), [`generator.filter()`](#generatorfilterpredicate), [`Gen.chain()`](#genchainbase_gen-gen_factory-generatorchaingen_factory)

## Dependent Generation Combinators

Dependent generation combinators allow you to create generators where subsequent values depend on previously generated values. These are essential for testing stateful systems, sequences with constraints, or data with complex interdependencies.

For testing with dependent generators, see the [`@run_for_all` decorator](decorators.md#run_for_all) which provides clean syntax for property tests using these combinators.

### `Gen.chain(base_gen, gen_factory)` / `generator.chain(gen_factory)`

Creates a tuple generator where the next value depends on the previously generated value(s). The result is always a tuple containing all generated values.

**Parameters:**
- `base_gen` (Generator): Generator for the initial value(s) - can produce single value or tuple
- `gen_factory` (Callable[[T], Generator[U]]): Function that takes the base value and returns a generator

**Static API Examples:**
```python
# Simple dependency: month -> valid day
def days_in_month(month):
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return days[month - 1]

date_gen = Gen.chain(
    Gen.int(1, 12),  # Generate month
    lambda month: Gen.int(1, days_in_month(month))  # Generate valid day for that month
)
# Result: Generator[Tuple[int, int]] producing (month, day) pairs like (2, 28), (12, 31)

# Multiple chaining: month -> day -> hour
datetime_gen = Gen.chain(
    date_gen,  # Base is already a tuple (month, day)
    lambda date_tuple: Gen.int(0, 23)  # Generate hour
)
# Result: Generator[Tuple[int, int, int]] producing (month, day, hour) like (3, 15, 14)

# Width constrains height
rect_gen = Gen.chain(
    Gen.int(1, 100),  # Generate width
    lambda width: Gen.int(1, 200 // width)  # Height constrained by width
)
# Result: Generator[Tuple[int, int]] ensuring width * height <= 200
```

**Fluent API Examples:**
```python
# Fluent API style (more concise)
date_gen = Gen.int(1, 12).chain(
    lambda month: Gen.int(1, days_in_month(month))
)

# Can chain multiple times
datetime_gen = Gen.int(1, 12)\
    .chain(lambda month: Gen.int(1, days_in_month(month)))\
    .chain(lambda date: Gen.int(0, 23))
```

**Use Cases:**
- Generating valid date combinations (month/day, hour/minute)
- Creating dependent geometric properties (width/height with area constraint)
- Testing APIs with dependent parameters
- Generating valid state transitions
- Creating dependent tuple data

**See Also:** [`Gen.aggregate()`](#genaggregateinitial_gen-gen_factory-min_size-max_size-generatoraggregate), [`Gen.accumulate()`](#genaccumulateinitial_gen-gen_factory-min_size-max_size-generatoraccumulate), [`generator.flat_map()`](#generatorflat_mapfunc), [`@run_for_all` decorator](decorators.md#run_for_all)

### `Gen.aggregate(initial_gen, gen_factory, min_size, max_size)` / `generator.aggregate(...)`

Generates a **list** where each element depends on the previous element. Returns the entire sequence of generated values.

**Parameters:**
- `initial_gen` (Generator[T]): Generator for the first element
- `gen_factory` (Callable[[T], Generator[T]]): Function that takes a value and returns a generator for the next value
- `min_size` (int): Minimum number of elements (default: 0)
- `max_size` (int): Maximum number of elements (default: 10)

**Static API Examples:**
```python
# Increasing sequence: each element >= previous
increasing_gen = Gen.aggregate(
    Gen.int(0, 10),  # Start with 0-10
    lambda n: Gen.int(n, n + 5),  # Each next value is n to n+5
    min_size=3,
    max_size=10
)
# Result: [5, 8, 12, 15, 18] - entire sequence of increasing numbers

# Strictly increasing sequence
strictly_increasing_gen = Gen.aggregate(
    Gen.int(0, 5),
    lambda n: Gen.int(n + 1, n + 10),  # Each next value is > previous
    min_size=4,
    max_size=7
)
# Result: [2, 5, 8, 15] - each element strictly > previous

# Bounded random walk
walk_gen = Gen.aggregate(
    Gen.int(50, 50),  # Start at position 50
    lambda pos: Gen.int(max(0, pos - 10), min(100, pos + 10)),  # Move ±10
    min_size=5,
    max_size=20
)
# Result: [50, 45, 52, 48, 38, ...] - random walk staying in [0, 100]

# Growing strings
string_growth_gen = Gen.aggregate(
    Gen.ascii_string(min_length=1, max_length=3),
    lambda s: Gen.ascii_string(min_length=len(s), max_length=len(s) + 2),
    min_size=3,
    max_size=8
)
# Result: ['ab', 'abc', 'abcde', 'abcdefg'] - strings growing in length
```

**Fluent API Examples:**
```python
# Fluent style
increasing_gen = Gen.int(0, 10).aggregate(
    lambda n: Gen.int(n, n + 5),
    min_size=3,
    max_size=10
)

# Chain with other combinators
filtered_walk = Gen.int(50, 50).aggregate(
    lambda pos: Gen.int(max(0, pos - 10), min(100, pos + 10)),
    min_size=10,
    max_size=20
).filter(lambda path: path[-1] > 30)  # Only paths ending above 30
```

**Use Cases:**
- Simulating sequences with constraints (increasing values, bounded movements)
- Testing stateful systems where each state depends on previous
- Generating time series data
- Creating dependency chains
- Testing algorithms that process sequences
- Simulating random walks or stochastic processes

**See Also:** [`Gen.chain()`](#genchainbase_gen-gen_factory-generatorchaingen_factory), [`Gen.accumulate()`](#genaccumulateinitial_gen-gen_factory-min_size-max_size-generatoraccumulate), [`@run_for_all` decorator](decorators.md#run_for_all)

### `Gen.accumulate(initial_gen, gen_factory, min_size, max_size)` / `generator.accumulate(...)`

Generates a **single final value** after N dependent generation steps. Like [`aggregate`](#genaggregateinitial_gen-gen_factory-min_size-max_size-generatoraggregate), but returns only the end result, not the intermediate values.

**Parameters:**
- `initial_gen` (Generator[T]): Generator for the initial value
- `gen_factory` (Callable[[T], Generator[T]]): Function that takes a value and returns a generator for the next value
- `min_size` (int): Minimum number of accumulation steps (default: 0)
- `max_size` (int): Maximum number of accumulation steps (default: 10)

**Static API Examples:**
```python
# Random walk - final position only
final_position_gen = Gen.accumulate(
    Gen.int(0, 100),  # Start position
    lambda pos: Gen.int(max(0, pos - 5), min(100, pos + 5)),  # Move ±5
    min_size=10,
    max_size=50
)
# Result: 67 - single int (final position after 10-50 steps)

# Compound growth - final amount only
final_amount_gen = Gen.accumulate(
    Gen.float(100.0, 100.0),  # Start with $100
    lambda amount: Gen.float(amount * 1.01, amount * 1.1),  # Grow 1-10%
    min_size=5,
    max_size=20
)
# Result: 156.34 - single float (final amount after compounding)

# Strictly increasing - final value
final_value_gen = Gen.accumulate(
    Gen.int(0, 10),
    lambda n: Gen.int(n + 1, n + 5),
    min_size=10,
    max_size=15
)
# Result: 47 - single int (final value after 10-15 increasing steps)
```

**Fluent API Examples:**
```python
# Fluent style
final_position = Gen.int(50, 50).accumulate(
    lambda pos: Gen.int(max(0, pos - 10), min(100, pos + 10)),
    min_size=20,
    max_size=30
)

# Use with map
final_state = Gen.int(0, 0).accumulate(
    lambda state: Gen.int(state, state + 10),
    min_size=5,
    max_size=10
).map(lambda final: f"Final state: {final}")
```

**Use Cases:**
- Testing end states of stochastic processes
- Simulating compound growth/decay
- Testing final outcomes without intermediate steps
- Generating complex derived values
- Simulating iterative algorithms (final result only)
- Testing convergence properties

**See Also:** [`Gen.chain()`](#genchainbase_gen-gen_factory-generatorchaingen_factory), [`Gen.aggregate()`](#genaggregateinitial_gen-gen_factory-min_size-max_size-generatoraggregate), [`@run_for_all` decorator](decorators.md#run_for_all)

### Comparison: `chain` vs `aggregate` vs `accumulate`

| Feature | [`chain`](#genchainbase_gen-gen_factory-generatorchaingen_factory) | [`aggregate`](#genaggregateinitial_gen-gen_factory-min_size-max_size-generatoraggregate) | [`accumulate`](#genaccumulateinitial_gen-gen_factory-min_size-max_size-generatoraccumulate) |
|---------|---------|-------------|--------------|
| **Returns** | Tuple of all values | List of all values | Single final value |
| **Dependency** | Each depends on all previous | Each depends on immediate previous | Each depends on immediate previous |
| **Result Size** | Fixed (base + 1) | Variable (min_size to max_size) | Single value |
| **Use When** | Need all related values | Need full sequence history | Only care about end result |
| **Example** | (month, day, hour) | [1, 3, 5, 8, 12] | 47 |

**Example Comparison:**
```python
# Chain: Get tuple of related values
date = Gen.chain(Gen.int(1, 12), lambda m: Gen.int(1, days_in_month(m)))
# Result: (3, 15) - tuple of (month, day)

# Aggregate: Get list showing full progression
path = Gen.aggregate(Gen.int(0, 0), lambda n: Gen.int(n, n+5), min_size=5, max_size=5)
# Result: [0, 3, 6, 10, 14] - full path shown

# Accumulate: Get only final position
final = Gen.accumulate(Gen.int(0, 0), lambda n: Gen.int(n, n+5), min_size=5, max_size=5)
# Result: 14 - only final value
```

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

**See Also:** [`generator.map()`](#generatormapfunc), [`generator.filter()`](#generatorfilterpredicate)

## Advanced Combinator Patterns

### Chaining Combinators

Combinators can be chained together to create complex generators. See also the individual combinator documentation: [`map`](#generatormapfunc), [`filter`](#generatorfilterpredicate), [`flat_map`](#generatorflat_mapfunc), [`one_of`](#genone_ofgenerators).

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

Use [`flat_map`](#generatorflat_mapfunc) for conditional generation:

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

Use `Gen.lazy()` for recursive generators. See also [`Gen.one_of()`](#genone_ofgenerators) and [`Gen.construct()`](#genconstructtype-generators):

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

1. **Avoid overly restrictive filters**: Use `Gen.in_range()` instead of [`filter`](#generatorfilterpredicate) for ranges
2. **Use appropriate generators**: Choose the right generator for your needs (see [Generators documentation](generators.md))
3. **Consider weights**: Use [`weighted_gen`](#genweighted_gengenerator-weight)/[`weighted_value`](#genweighted_valuevalue-weight) for realistic distributions
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
4. **Test error conditions**: Use [`Gen.element_of()`](#genelement_ofvalues) for error cases
5. **Test dependent data**: Use [`chain`](#genchainbase_gen-gen_factory-generatorchaingen_factory), [`aggregate`](#genaggregateinitial_gen-gen_factory-min_size-max_size-generatoraggregate), or [`accumulate`](#genaccumulateinitial_gen-gen_factory-min_size-max_size-generatoraccumulate) for dependent generation

Combinators are the key to creating sophisticated test data that matches your specific needs. By combining and transforming basic generators, you can create generators for any data structure or constraint your tests require. For more information, see:

- [Generators documentation](generators.md) - Basic generators
- [Decorators documentation](decorators.md) - Using generators in tests with `@for_all` and `@run_for_all`
- [Properties documentation](properties.md) - Writing property-based tests
