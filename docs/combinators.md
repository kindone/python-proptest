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

## Detailed Combinator Examples

While the table above provides a quick overview, let's explore some common combinators with more illustrative examples.

### `generator.map(f)`

Transforms the output of a generator using a provided function `f`.

```python
from python_proptest import Gen

# Generate positive integers and map them to their string representation
positive_int_gen = Gen.int(min_value=1, max_value=1000)
positive_int_string_gen = positive_int_gen.map(lambda num: str(num))
# Generates strings like "1", "5", "999"

# Generate user objects with an ID and a derived email
user_id_gen = Gen.int(min_value=1, max_value=100)
user_object_gen = user_id_gen.map(lambda id: {
    "id": id,
    "email": f"user{id}@example.com"
})
# Generates objects like {"id": 42, "email": "user42@example.com"}
```

### `generator.filter(predicate)`

Selects only the values from a generator that satisfy a given `predicate` function. Be cautious: if the predicate is too restrictive, generation might become very slow or fail if it cannot find enough valid values within a reasonable number of attempts.

```python
from python_proptest import Gen

# Generate only even numbers between 0 and 20
interval_gen = Gen.int(min_value=0, max_value=20)
even_number_gen = interval_gen.filter(lambda n: n % 2 == 0)
# Generates 0, 2, 4, ..., 20

# Generate non-empty strings
possibly_empty_string_gen = Gen.str(min_length=0, max_length=5)
non_empty_string_gen = possibly_empty_string_gen.filter(lambda s: len(s) > 0)
# Generates strings like "a", "hello", but never ""
```

### `generator.flat_map(f)` / `generator.chain(f)`

Creates a *dependent* generator. The function `f` takes a value produced by the initial generator and returns a *new generator*. This is powerful for scenarios where the generation of one value depends on another.

```python
from python_proptest import Gen

# Generate a list whose length is also randomly generated
length_gen = Gen.int(min_value=1, max_value=5)  # Generate a length first
array_with_random_length_gen = length_gen.flat_map(lambda length:
    Gen.list(Gen.bool(), min_length=length, max_length=length)  # Use the generated length
)
# Generates lists like [True], [False, True, False], [True, True, True, True] etc.

# Generate a pair [x, y] where y > x
x_gen = Gen.int(min_value=0, max_value=10)
pair_gen = x_gen.flat_map(lambda x:
    Gen.int(min_value=x + 1, max_value=20).map(lambda y: [x, y])  # Generate y based on x, then map to pair
)
# Generates pairs like [0, 1], [5, 15], [10, 11], etc.
```

### `Gen.one_of(...gens)`

Randomly selects one of the provided generators to produce a value for each test case. To control the selection probability, you can wrap generators using `Gen.weighted_gen` (see the dedicated section below).

```python
from python_proptest import Gen

# Generate either a number or a boolean
num_or_bool_gen = Gen.one_of(
    Gen.int(min_value=-10, max_value=10),
    Gen.bool()
)
# Generates values like 5, True, -2, False, 0

# Generate specific string constants or a generic short string
specific_or_general_string_gen = Gen.one_of(
    Gen.just(""),        # Empty string
    Gen.just("error"),   # Specific keyword
    Gen.str(min_length=1, max_length=5)     # A short random string
)
# Generates "", "error", "abc", "test", etc.
```

### `Gen.element_of(...values)`

Randomly selects one value from the provided list of literal values. To control the selection probability, you can wrap values using `Gen.weighted_value` (see the dedicated section below).

```python
from python_proptest import Gen

# Pick a specific HTTP status code
status_gen = Gen.element_of(200, 201, 400, 404, 500)
# Generates 200, 404, 500, etc.

# Pick a predefined configuration option
option_gen = Gen.element_of('read', 'write', 'admin')
# Generates 'read', 'write', or 'admin'
```

### `Gen.weighted_gen(gen, weight)` and `Gen.weighted_value(value, weight)`

Used within `Gen.one_of` and `Gen.element_of` respectively to influence the probability of selecting certain generators or values. The `weight` is a positive number between 0.0 and 1.0.

```python
from python_proptest import Gen

# Generate numbers, but make 0 appear much more often
weighted_number_gen = Gen.one_of(
    Gen.weighted_gen(Gen.just(0), 0.8),          # 80% chance of getting 0
    Gen.weighted_gen(Gen.int(min_value=1, max_value=100), 0.2)  # 20% chance of getting 1-100
)
# Generates 0, 0, 5, 0, 42, 0, 0, ...

# Pick a character, biasing heavily towards 'a'
weighted_char_gen = Gen.element_of(
    Gen.weighted_value('a', 0.8),  # 80%
    Gen.weighted_value('b', 0.1),  # 10%
    Gen.weighted_value('c', 0.1)   # 10%
)
# Generates 'a' roughly 9 out of 11 times
```

### `Gen.construct(Class, ...arg_gens)`

Constructs instances of a `Class` by generating arguments for its constructor using the provided `arg_gens`.

```python
from python_proptest import Gen

class Point:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

# Generate Point objects with coordinates between -10 and 10
point_gen = Gen.construct(
    Point,
    Gen.int(min_value=-10, max_value=10),  # Generator for the 'x' argument
    Gen.int(min_value=-10, max_value=10)   # Generator for the 'y' argument
)
# Generates Point instances like Point(3, -5), Point(0, 0)
```

## Advanced Combinator Patterns

### Building Complex Data Structures

```python
from python_proptest import Gen

# Generate a user profile with nested data
user_profile_gen = Gen.construct(
    UserProfile,
    Gen.str(min_length=1, max_length=20),  # name
    Gen.int(min_value=18, max_value=100),  # age
    Gen.list(Gen.str(min_length=1, max_length=10), min_length=0, max_length=5),  # hobbies
    Gen.dict(Gen.str(min_length=1, max_length=10), Gen.str(), min_size=0, max_size=3)  # metadata
)

# Generate a tree-like structure
def tree_gen(depth: int = 0):
    if depth > 3:
        return Gen.just(None)  # Leaf node

    return Gen.one_of(
        Gen.just(None),  # Leaf
        Gen.construct(
            TreeNode,
            Gen.str(),  # value
            Gen.lazy(lambda: tree_gen(depth + 1)),  # left child
            Gen.lazy(lambda: tree_gen(depth + 1))   # right child
        )
    )
```

### Conditional Generation

```python
from python_proptest import Gen

# Generate different types based on a condition
def conditional_gen():
    type_gen = Gen.element_of('string', 'number', 'boolean')

    return type_gen.flat_map(lambda t:
        Gen.str() if t == 'string' else
        Gen.int() if t == 'number' else
        Gen.bool()
    )

# Generate a list where each element depends on the previous
def dependent_list_gen():
    return Gen.int(min_value=1, max_value=5).flat_map(lambda length:
        Gen.list(
            Gen.int(min_value=0, max_value=10).filter(lambda x: x > 0),
            min_length=length,
            max_length=length
        )
    )
```

These combinators provide the building blocks for creating sophisticated generators that can model complex real-world data structures and scenarios. By combining them effectively, you can create property-based tests that thoroughly exercise your code with realistic and diverse inputs.
