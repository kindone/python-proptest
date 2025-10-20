# Generators

Generators are the foundation of property-based testing in `python-proptest`. They are responsible for creating the diverse range of random (or sometimes specific) input data that is fed into your properties during testing. By defining how data should be generated – its type, constraints, and structure – generators allow `python-proptest` to explore the input space of your functions effectively, searching for edge cases and potential bugs that manually chosen examples might miss. Generators can range from simple primitives like booleans and numbers to complex, nested data structures built by combining other generators.

## Generator Summary Table

| Generator                 | Description                                                     | Key Parameters                                     | Example Usage                                         |
| :------------------------ | :-------------------------------------------------------------- | :------------------------------------------------- | :---------------------------------------------------- |
| **Primitives**            |                                                                 |                                                    |                                                       |
| `Gen.bool()`             | Generates `True` or `False` with configurable probability.     | `true_prob` (def: 0.5)                              | `Gen.bool(true_prob=0.8)`                                       |
| `Gen.float()`             | Generates floating-point numbers (incl. `inf`, `-inf`, `nan`).     | `min_value`, `max_value`                              | `Gen.float(min_value=0.0, max_value=1.0)`                                         |
| `Gen.int()`  | Generates integers in the range `[min_value, max_value]`.                   | `min_value`, `max_value`                                       | `Gen.int(min_value=0, max_value=10)`                                 |
| `Gen.str()`  | Generates strings (defaults to ASCII).                          | `min_length` (def: 0), `max_length` (def: 10)        | `Gen.str(min_length=0, max_length=5)`                                    |
| `Gen.ascii_string(...)`    | Generates strings containing only ASCII chars (0-127).          | `min_length` (def: 0), `max_length` (def: 10)        | `Gen.ascii_string(min_length=1, max_length=8)`                               |
| `Gen.unicode_string(...)`  | Generates strings containing Unicode chars.                     | `min_length` (def: 0), `max_length` (def: 10)        | `Gen.unicode_string(min_length=1, max_length=8)`                             |
| `Gen.printable_ascii_string(...)` | Generates strings containing only printable ASCII chars.  | `min_length` (def: 0), `max_length` (def: 10)        | `Gen.printable_ascii_string(min_length=5, max_length=5)`                      |
| `Gen.ascii_char()`        | Generates ASCII character codes (0-127).                  | None                                                | `Gen.ascii_char()`                                                             |
| `Gen.unicode_char()`      | Generates Unicode character codes (avoiding surrogate pairs). | None                                                | `Gen.unicode_char()`                                                           |
| `Gen.printable_ascii_char()` | Generates printable ASCII character codes (32-126).    | None                                                | `Gen.printable_ascii_char()`                                                   |
| `Gen.in_range(min, max)`  | Generates integers in range [min, max) (exclusive).      | `min_value`, `max_value`                            | `Gen.in_range(0, 10)`                                                         |
| `Gen.unique_list(elem, min_length, max_length)` | Generates lists with unique elements, sorted. | `element_gen`, `min_length` (def: 0), `max_length` (def: 10) | `Gen.unique_list(Gen.int(min_value=1, max_value=5), min_length=1, max_length=3)` |
| **Containers**            |                                                                 |                                                    |                                                       |
| `Gen.list(elem, min_length, max_length)` | Generates lists with elements from `elem`.                   | `element_gen`, `min_length` (def: 0), `max_length` (def: 10) | `Gen.list(Gen.bool(), min_length=2, max_length=4)`                      |
| `Gen.set(elem, min_size, max_size)`   | Generates `set` objects with elements from `elem`.            | `element_gen`, `min_size` (def: 0), `max_size` (def: 10)   | `Gen.set(Gen.int(min_value=1, max_value=3), min_size=1, max_size=3)`                   |
| `Gen.dict(key_gen, val_gen, min_size, max_size)` | Generates dictionaries with keys from `key_gen` and values from `val_gen`. | `key_gen`, `value_gen`, `min_size` (def: 0), `max_size` (def: 10)   | `Gen.dict(Gen.str(min_length=1, max_length=2), Gen.int(min_value=0, max_value=5), min_size=2, max_size=5)` |
| `Gen.tuple(...gens)`      | Generates fixed-size tuples from `gens`.             | `...element_gens`                                   | `Gen.tuple(Gen.float(), Gen.str())`             |
| **Special**               |                                                                 |                                                    |                                                       |
| `Gen.just(value)`         | Always generates the provided `value`.                          | `value`                                            | `Gen.just(None)`                                      |
| `Gen.lazy(value_factory)`   | Defers execution of a function to produce `value` until needed. | `value_factory: Callable[[], T]`                            | `Gen.lazy(lambda: expensive_calculation())`              |

*(Defaults for length/size are typically 0 and 10, but check implementation for specifics)*

## Primitive Generators

### `Gen.int(min_value, max_value)`

Generates random integers within the specified range (inclusive).

**Parameters:**
- `min_value` (int, default: -1000): Minimum integer value to generate
- `max_value` (int, default: 1000): Maximum integer value to generate

**Examples:**
```python
# Generate integers from 0 to 100
Gen.int(min_value=0, max_value=100)

# Generate negative integers
Gen.int(min_value=-50, max_value=-1)

# Generate single value (when min_value == max_value)
Gen.int(min_value=42, max_value=42)
```

**Use Cases:**
- Testing mathematical operations
- Generating array indices
- Creating test IDs or counts

### `Gen.float(min_value, max_value)`

Generates random floating-point numbers within the specified range.

**Parameters:**
- `min_value` (float, default: -1000.0): Minimum float value to generate
- `max_value` (float, default: 1000.0): Maximum float value to generate

**Examples:**
```python
# Generate floats from 0.0 to 1.0
Gen.float(min_value=0.0, max_value=1.0)

# Generate negative floats
Gen.float(min_value=-10.0, max_value=-0.1)

# Generate very small floats
Gen.float(min_value=0.0, max_value=0.001)
```

**Use Cases:**
- Testing floating-point arithmetic
- Generating probabilities or percentages
- Creating test measurements or coordinates

### `Gen.bool(true_prob)`

Generates random boolean values (`True` or `False`) with configurable probability.

**Parameters:**
- `true_prob` (float, default: 0.5): Probability of generating `True` (0.0 to 1.0)

**Examples:**
```python
# Generate random booleans (50% True, 50% False)
Gen.bool()

# Generate mostly True values (80% True, 20% False)
Gen.bool(true_prob=0.8)

# Generate mostly False values (10% True, 90% False)
Gen.bool(true_prob=0.1)

# Always generate True
Gen.bool(true_prob=1.0)

# Always generate False
Gen.bool(true_prob=0.0)

# Use with other generators
Gen.tuple(Gen.bool(true_prob=0.7), Gen.int())

# Generate lists of biased booleans
Gen.list(Gen.bool(true_prob=0.3), min_length=1, max_length=5)
```

**Use Cases:**
- Testing conditional logic with biased inputs
- Generating feature flags with realistic distributions
- Creating binary choices with weighted probabilities
- Testing boolean operations with edge cases
- Simulating real-world boolean distributions

### `Gen.str(min_length, max_length)`

Generates random strings with ASCII characters.

**Parameters:**
- `min_length` (int, default: 0): Minimum string length
- `max_length` (int, default: 20): Maximum string length

**Examples:**
```python
# Generate strings of length 5 to 10
Gen.str(min_length=5, max_length=10)

# Generate single character strings
Gen.str(min_length=1, max_length=1)

# Generate empty strings (min_length=0)
Gen.str(min_length=0, max_length=0)
```

**Use Cases:**
- Testing string operations
- Generating usernames or identifiers
- Creating test data for text processing

### `Gen.ascii_string(min_length, max_length)`

Generates random strings containing only ASCII characters (0-127).

**Parameters:**
- `min_length` (int, default: 0): Minimum string length
- `max_length` (int, default: 20): Maximum string length

**Examples:**
```python
# Generate ASCII strings of length 1 to 8
Gen.ascii_string(min_length=1, max_length=8)

# Generate fixed-length ASCII strings
Gen.ascii_string(min_length=5, max_length=5)
```

**Use Cases:**
- Testing ASCII-only systems
- Generating legacy-compatible strings
- Creating test data for systems with ASCII restrictions

### `Gen.printable_ascii_string(min_length, max_length)`

Generates random strings containing only printable ASCII characters (32-126).

**Parameters:**
- `min_length` (int, default: 0): Minimum string length
- `max_length` (int, default: 20): Maximum string length

**Examples:**
```python
# Generate printable ASCII strings
Gen.printable_ascii_string(min_length=1, max_length=10)

# Generate fixed-length printable strings
Gen.printable_ascii_string(min_length=5, max_length=5)
```

**Use Cases:**
- Testing user input validation
- Generating displayable text
- Creating test data for human-readable strings

### `Gen.unicode_string(min_length, max_length)`

Generates random strings containing Unicode characters.

**Parameters:**
- `min_length` (int, default: 0): Minimum string length
- `max_length` (int, default: 20): Maximum string length

**Examples:**
```python
# Generate Unicode strings
Gen.unicode_string(min_length=1, max_length=10)

# Generate short Unicode strings
Gen.unicode_string(min_length=1, max_length=3)
```

**Use Cases:**
- Testing internationalization
- Generating multi-language text
- Creating test data for Unicode-aware systems

### `Gen.ascii_char()`

Generates single ASCII character codes (0-127).

**Parameters:**
- None

**Examples:**
```python
# Generate ASCII character codes
Gen.ascii_char()

# Use with map to get actual characters
Gen.ascii_char().map(chr)
```

**Use Cases:**
- Testing character processing
- Generating single character inputs
- Creating test data for character-based operations

### `Gen.unicode_char()`

Generates single Unicode character codes (avoiding surrogate pairs).

**Parameters:**
- None

**Examples:**
```python
# Generate Unicode character codes
Gen.unicode_char()

# Use with map to get actual characters
Gen.unicode_char().map(chr)
```

**Use Cases:**
- Testing Unicode character handling
- Generating international characters
- Creating test data for Unicode-aware systems

### `Gen.printable_ascii_char()`

Generates single printable ASCII character codes (32-126).

**Parameters:**
- None

**Examples:**
```python
# Generate printable ASCII character codes
Gen.printable_ascii_char()

# Use with map to get actual characters
Gen.printable_ascii_char().map(chr)
```

**Use Cases:**
- Testing printable character processing
- Generating displayable characters
- Creating test data for user-visible text

### `Gen.in_range(min_value, max_value)`

Generates random integers in range [min_value, max_value) (exclusive of max_value).

**Parameters:**
- `min_value` (int): Minimum integer value (inclusive)
- `max_value` (int): Maximum integer value (exclusive)

**Examples:**
```python
# Generate integers from 0 to 9 (exclusive of 10)
Gen.in_range(0, 10)

# Generate array indices
Gen.in_range(0, len(my_array))
```

**Use Cases:**
- Generating array indices
- Creating ranges for iteration
- Testing boundary conditions

### `Gen.interval(min_value, max_value)`

Generates random integers in range [min_value, max_value] (inclusive of both bounds).

**Parameters:**
- `min_value` (int): Minimum integer value (inclusive)
- `max_value` (int): Maximum integer value (inclusive)

**Examples:**
```python
# Generate integers from 0 to 10 (inclusive)
Gen.interval(0, 10)

# Generate dice rolls (1 to 6)
Gen.interval(1, 6)
```

**Use Cases:**
- Testing inclusive ranges
- Generating dice rolls or random selections
- Creating bounded integer values

### `Gen.integers(min_value, max_value)`

Alias for `Gen.interval()` for compatibility.

**Parameters:**
- `min_value` (int): Minimum integer value (inclusive)
- `max_value` (int): Maximum integer value (inclusive)

**Examples:**
```python
# Same as Gen.interval(0, 10)
Gen.integers(0, 10)
```

## Container Generators

### `Gen.list(element_gen, min_length, max_length)`

Generates random lists with elements from the specified generator.

**Parameters:**
- `element_gen` (Generator): Generator for list elements
- `min_length` (int, default: 0): Minimum list length
- `max_length` (int, default: 10): Maximum list length

**Examples:**
```python
# Generate lists of 2 to 5 booleans
Gen.list(Gen.bool(), min_length=2, max_length=5)

# Generate lists of integers
Gen.list(Gen.int(min_value=1, max_value=100), min_length=0, max_length=10)

# Generate lists of strings
Gen.list(Gen.str(min_length=1, max_length=5), min_length=1, max_length=3)
```

**Use Cases:**
- Testing list operations
- Generating test data collections
- Creating sequences for processing

### `Gen.unique_list(element_gen, min_length, max_length)`

Generates random lists with unique elements, sorted.

**Parameters:**
- `element_gen` (Generator): Generator for list elements
- `min_length` (int, default: 0): Minimum list length
- `max_length` (int, default: 10): Maximum list length

**Examples:**
```python
# Generate unique integer lists
Gen.unique_list(Gen.int(min_value=1, max_value=10), min_length=1, max_length=5)

# Generate unique string lists
Gen.unique_list(Gen.str(min_length=1, max_length=3), min_length=2, max_length=4)
```

**Use Cases:**
- Testing unique value processing
- Generating sorted test data
- Creating sets represented as lists

### `Gen.set(element_gen, min_size, max_size)`

Generates random sets with elements from the specified generator.

**Parameters:**
- `element_gen` (Generator): Generator for set elements
- `min_size` (int, default: 0): Minimum set size
- `max_size` (int, default: 10): Maximum set size

**Examples:**
```python
# Generate sets of integers
Gen.set(Gen.int(min_value=1, max_value=10), min_size=1, max_size=5)

# Generate sets of strings
Gen.set(Gen.str(min_length=1, max_length=3), min_size=2, max_size=4)
```

**Use Cases:**
- Testing set operations
- Generating unique collections
- Creating test data for set-based algorithms

### `Gen.dict(key_gen, value_gen, min_size, max_size)`

Generates random dictionaries with keys and values from specified generators.

**Parameters:**
- `key_gen` (Generator): Generator for dictionary keys
- `value_gen` (Generator): Generator for dictionary values
- `min_size` (int, default: 0): Minimum dictionary size
- `max_size` (int, default: 10): Maximum dictionary size

**Examples:**
```python
# Generate string-to-int dictionaries
Gen.dict(Gen.str(min_length=1, max_length=3), Gen.int(), min_size=1, max_size=5)

# Generate int-to-string dictionaries
Gen.dict(Gen.int(min_value=1, max_value=10), Gen.str(min_length=1, max_length=5))
```

**Use Cases:**
- Testing dictionary operations
- Generating configuration data
- Creating test data for key-value processing

### `Gen.tuple(*generators)`

Generates fixed-size tuples with elements from the specified generators.

**Parameters:**
- `*generators` (Generator): Variable number of generators for tuple elements

**Examples:**
```python
# Generate pairs of (bool, int)
Gen.tuple(Gen.bool(), Gen.int())

# Generate triples of (str, int, float)
Gen.tuple(Gen.str(), Gen.int(), Gen.float())

# Generate single-element tuples
Gen.tuple(Gen.str())
```

**Use Cases:**
- Testing tuple operations
- Generating coordinate pairs
- Creating structured test data

## Special Generators

### `Gen.just(value)`

Always generates the exact value provided.

**Parameters:**
- `value` (Any): The value to always generate

**Examples:**
```python
# Always generate 42
Gen.just(42)

# Always generate None
Gen.just(None)

# Always generate a specific string
Gen.just("hello")
```

**Use Cases:**
- Including specific edge cases
- Creating constants in test data
- Combining with `Gen.one_of()` for mixed generation

### `Gen.lazy(func)`

Defers execution of a function until generation time.

**Parameters:**
- `func` (Callable[[], T]): Function that returns a value when called

**Examples:**
```python
# Defer expensive calculation
def expensive_calculation():
    return complex_computation()

Gen.lazy(expensive_calculation)

# Defer current time
Gen.lazy(lambda: datetime.now())
```

**Use Cases:**
- Delaying expensive computations
- Breaking circular dependencies
- Generating time-sensitive values

### `Gen.construct(Type, *generators)`

Creates instances of a class using the specified generators for constructor arguments.

**Parameters:**
- `Type` (type): Class to instantiate
- `*generators` (Generator): Generators for constructor arguments

**Examples:**
```python
class Point:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

# Generate Point instances
Gen.construct(Point, Gen.int(), Gen.int())

class Person:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

# Generate Person instances
Gen.construct(Person, Gen.str(min_length=1, max_length=10), Gen.int(min_value=0, max_value=120))
```

**Use Cases:**
- Testing custom classes
- Generating domain objects
- Creating structured test data

### `Gen.chain_tuple(tuple_gen, gen_factory)`

Chains tuple generation with dependent value generation.

**Parameters:**
- `tuple_gen` (Generator): Generator that produces tuples
- `gen_factory` (Callable): Function that takes tuple values and returns a generator

**Examples:**
```python
# Generate (x, y) pairs, then generate z based on x and y
def create_z_gen(x, y):
    return Gen.int(min_value=x, max_value=y)

Gen.chain_tuple(Gen.tuple(Gen.int(), Gen.int()), create_z_gen)
```

**Use Cases:**
- Creating dependent test data
- Generating related values
- Building complex data structures

Beyond the built-in generators, `python-proptest` provides **combinators**: functions that transform or combine existing generators to create new, more complex ones. This is how you build generators for your specific data types and constraints.

These combinators are essential tools for tailoring data generation precisely to your testing needs. For a comprehensive guide on how to use them, see the [Combinators](./combinators.md) documentation.