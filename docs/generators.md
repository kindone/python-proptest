# Generators

Generators are the foundation of property-based testing in `python-proptest`. They are responsible for creating the diverse range of random (or sometimes specific) input data that is fed into your properties during testing. By defining how data should be generated – its type, constraints, and structure – generators allow `python-proptest` to explore the input space of your functions effectively, searching for edge cases and potential bugs that manually chosen examples might miss. Generators can range from simple primitives like booleans and numbers to complex, nested data structures built by combining other generators.

## Generator Summary Table

| Generator                 | Description                                                     | Key Parameters                                     | Example Usage                                         |
| :------------------------ | :-------------------------------------------------------------- | :------------------------------------------------- | :---------------------------------------------------- |
| **Primitives**            |                                                                 |                                                    |                                                       |
| [`Gen.bool()`](#genbooltrue_prob)             | Generates `True` or `False` with configurable probability.     | `true_prob` (def: 0.5)                              | `Gen.bool(true_prob=0.8)`                                       |
| [`Gen.float()`](#genfloatmin_value-max_value)             | Generates floating-point numbers (incl. `inf`, `-inf`, `nan`).     | `min_value`, `max_value`                              | `Gen.float(min_value=0.0, max_value=1.0)`                                         |
| [`Gen.int()`](#genintmin_value-max_value)  | Generates integers in the range `[min_value, max_value]`.                   | `min_value`, `max_value`                                       | `Gen.int(min_value=0, max_value=10)`                                 |
| [`Gen.str()`](#genstrmin_length-max_length)  | Generates strings (defaults to ASCII).                          | `min_length` (def: 0), `max_length` (def: 10)        | `Gen.str(min_length=0, max_length=5)`                                    |
| [`Gen.ascii_string(...)`](#genascii_stringmin_length-max_length)    | Generates strings containing only ASCII chars (0-127).          | `min_length` (def: 0), `max_length` (def: 10)        | `Gen.ascii_string(min_length=1, max_length=8)`                               |
| [`Gen.unicode_string(...)`](#genunicode_stringmin_length-max_length)  | Generates strings containing Unicode chars.                     | `min_length` (def: 0), `max_length` (def: 10)        | `Gen.unicode_string(min_length=1, max_length=8)`                             |
| [`Gen.printable_ascii_string(...)`](#genprintable_ascii_stringmin_length-max_length) | Generates strings containing only printable ASCII chars.  | `min_length` (def: 0), `max_length` (def: 10)        | `Gen.printable_ascii_string(min_length=5, max_length=5)`                      |
| [`Gen.ascii_char()`](#genascii_char)        | Generates ASCII character codes (0-127).                  | None                                                | `Gen.ascii_char()`                                                             |
| [`Gen.unicode_char()`](#genunicode_char)      | Generates Unicode character codes (avoiding surrogate pairs). | None                                                | `Gen.unicode_char()`                                                           |
| [`Gen.printable_ascii_char()`](#genprintable_ascii_char) | Generates printable ASCII character codes (32-126).    | None                                                | `Gen.printable_ascii_char()`                                                   |
| [`Gen.in_range(min, max)`](#genin_rangemin_value-max_value)  | Generates integers in range [min, max) (exclusive).      | `min_value`, `max_value`                            | `Gen.in_range(0, 10)`                                                         |
| [`Gen.unique_list(elem, ...)`](#genunique_listelement_gen-min_length-max_length) | Generates lists with unique elements, sorted. | `element_gen`, `min_length` (def: 0), `max_length` (def: 10) | `Gen.unique_list(Gen.int(min_value=1, max_value=5), min_length=1, max_length=3)` |
| **Containers**            |                                                                 |                                                    |                                                       |
| [`Gen.list(elem, ...)`](#genlistelement_gen-min_length-max_length) | Generates lists with elements from `elem`.                   | `element_gen`, `min_length` (def: 0), `max_length` (def: 10) | `Gen.list(Gen.bool(), min_length=2, max_length=4)`                      |
| [`Gen.set(elem, ...)`](#gensetelement_gen-min_size-max_size)   | Generates `set` objects with elements from `elem`.            | `element_gen`, `min_size` (def: 0), `max_size` (def: 10)   | `Gen.set(Gen.int(min_value=1, max_value=3), min_size=1, max_size=3)`                   |
| [`Gen.dict(key_gen, val_gen, ...)`](#gendictkey_gen-value_gen-min_size-max_size) | Generates dictionaries with keys from `key_gen` and values from `val_gen`. | `key_gen`, `value_gen`, `min_size` (def: 0), `max_size` (def: 10)   | `Gen.dict(Gen.str(min_length=1, max_length=2), Gen.int(min_value=0, max_value=5), min_size=2, max_size=5)` |
| [`Gen.tuple(...gens)`](#gentuplegenerators)      | Generates fixed-size tuples from `gens`.             | `...element_gens`                                   | `Gen.tuple(Gen.float(), Gen.str())`             |
| **Special**               |                                                                 |                                                    |                                                       |
| [`Gen.just(value)`](#genjustvalue)         | Always generates the provided `value`.                          | `value`                                            | `Gen.just(None)`                                      |
| [`Gen.lazy(value_factory)`](#genlazyfunc)   | Defers execution of a function to produce `value` until needed. | `value_factory: Callable[[], T]`                            | `Gen.lazy(lambda: expensive_calculation())`              |

*(Defaults for length/size are typically 0 and 10, but check implementation for specifics)*

## Primitive Generators

### `Gen.int(min_value, max_value)`

Generates random integers within the specified range (inclusive).

**Parameters:**
- `min_value` (int, optional): Minimum integer value to generate. If not specified, uses `-sys.maxsize - 1` (full integer range)
- `max_value` (int, optional): Maximum integer value to generate. If not specified, uses `sys.maxsize` (full integer range)

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

**See Also:** [`Gen.in_range()`](#genin_rangemin_value-max_value), [`Gen.interval()`](#genintervalmin_value-max_value), [`Gen.float()`](#genfloatmin_value-max_value)

### `Gen.float(min_value, max_value)`

Generates random floating-point numbers within the specified range.

**Parameters:**
- `min_value` (float, optional): Minimum float value to generate. If not specified, uses `-sys.float_info.max` (full float range)
- `max_value` (float, optional): Maximum float value to generate. If not specified, uses `sys.float_info.max` (full float range)

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

**See Also:** [`Gen.int()`](#genintmin_value-max_value), [`Gen.bool()`](#genbooltrue_prob)

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

**See Also:** [`Gen.just()`](#genjustvalue) for constant values, [`Gen.list()`](#genlistelement_gen-min_length-max_length) for lists of booleans

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

**See Also:** [`Gen.ascii_string()`](#genascii_stringmin_length-max_length), [`Gen.unicode_string()`](#genunicode_stringmin_length-max_length), [`Gen.printable_ascii_string()`](#genprintable_ascii_stringmin_length-max_length)

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

**See Also:** [`Gen.str()`](#genstrmin_length-max_length), [`Gen.printable_ascii_string()`](#genprintable_ascii_stringmin_length-max_length), [`Gen.ascii_char()`](#genascii_char)

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

**See Also:** [`Gen.ascii_string()`](#genascii_stringmin_length-max_length), [`Gen.printable_ascii_char()`](#genprintable_ascii_char)

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

**See Also:** [`Gen.str()`](#genstrmin_length-max_length), [`Gen.unicode_char()`](#genunicode_char)

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

**See Also:** [`Gen.ascii_string()`](#genascii_stringmin_length-max_length), [`Gen.unicode_char()`](#genunicode_char), [`Gen.printable_ascii_char()`](#genprintable_ascii_char), [`generator.map()`](combinators.md#generatormapfunc)

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

**See Also:** [`Gen.unicode_string()`](#genunicode_stringmin_length-max_length), [`Gen.ascii_char()`](#genascii_char), [`generator.map()`](combinators.md#generatormapfunc)

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

**See Also:** [`Gen.printable_ascii_string()`](#genprintable_ascii_stringmin_length-max_length), [`Gen.ascii_char()`](#genascii_char), [`generator.map()`](combinators.md#generatormapfunc)

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

**See Also:** [`Gen.int()`](#genintmin_value-max_value), [`Gen.interval()`](#genintervalmin_value-max_value)

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

**See Also:** [`Gen.int()`](#genintmin_value-max_value), [`Gen.in_range()`](#genin_rangemin_value-max_value), [`Gen.integers()`](#genintegersmin_value-max_value)

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

**See Also:** [`Gen.unique_list()`](#genunique_listelement_gen-min_length-max_length), [`Gen.set()`](#gensetelement_gen-min_size-max_size), [`Gen.tuple()`](#gentuplegenerators), [`generator.map()`](combinators.md#generatormapfunc)

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

**See Also:** [`Gen.list()`](#genlistelement_gen-min_length-max_length), [`Gen.set()`](#gensetelement_gen-min_size-max_size)

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

**See Also:** [`Gen.list()`](#genlistelement_gen-min_length-max_length), [`Gen.unique_list()`](#genunique_listelement_gen-min_length-max_length)

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

**See Also:** [`Gen.list()`](#genlistelement_gen-min_length-max_length), [`Gen.set()`](#gensetelement_gen-min_size-max_size), [`Gen.tuple()`](#gentuplegenerators)

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

**See Also:** [`Gen.list()`](#genlistelement_gen-min_length-max_length), [`Gen.construct()`](#genconstructtype-generators), [`Gen.chain()`](combinators.md#genchainbase_gen-gen_factory-generatorchaingen_factory)

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

**See Also:** [`Gen.one_of()`](combinators.md#genone_ofgenerators), [`Gen.element_of()`](combinators.md#genelement_ofvalues)

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

**See Also:** [`Gen.construct()`](#genconstructtype-generators), recursive generation patterns in [Combinators](combinators.md#recursive-generation)

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

**See Also:** [`Gen.tuple()`](#gentuplegenerators), [`Gen.lazy()`](#genlazyfunc), [`Gen.construct()` in Combinators](combinators.md#genconstructtype-generators)

## Dependent Generation

For generators where values depend on each other, `python-proptest` provides powerful combinators like [`chain`](combinators.md#genchainbase_gen-gen_factory-generatorchaingen_factory), [`aggregate`](combinators.md#genaggregateinitial_gen-gen_factory-min_size-max_size-generatoraggregate), and [`accumulate`](combinators.md#genaccumulateinitial_gen-gen_factory-min_size-max_size-generatoraccumulate). These are covered in detail in the [Combinators](./combinators.md) documentation under "Dependent Generation Combinators".

**Quick Examples:**
```python
# Chain: Create dependent tuple (month, day)
Gen.chain(Gen.int(1, 12), lambda month: Gen.int(1, days_in_month(month)))

# Aggregate: Create list where each element depends on previous
Gen.aggregate(Gen.int(0, 10), lambda n: Gen.int(n, n + 5), min_size=3, max_size=10)

# Accumulate: Get final value after dependent steps
Gen.accumulate(Gen.int(50, 50), lambda p: Gen.int(max(0, p-10), min(100, p+10)), min_size=10)
```

**See Also:** [Combinators documentation](combinators.md) for transformation combinators ([`map`](combinators.md#generatormapfunc), [`filter`](combinators.md#generatorfilterpredicate), [`flat_map`](combinators.md#generatorflat_mapfunc)) and [Decorators documentation](decorators.md) for using generators in tests with [`@for_all`](decorators.md#for_all) and [`@run_for_all`](decorators.md#run_for_all).

Beyond the built-in generators, `python-proptest` provides **combinators**: functions that transform or combine existing generators to create new, more complex ones. This is how you build generators for your specific data types and constraints.

These combinators are essential tools for tailoring data generation precisely to your testing needs. For a comprehensive guide on how to use them, see the [Combinators](./combinators.md) documentation.
