# Generators

Generators are the foundation of property-based testing in `python-proptest`. They are responsible for creating the diverse range of random (or sometimes specific) input data that is fed into your properties during testing. By defining how data should be generated – its type, constraints, and structure – generators allow `python-proptest` to explore the input space of your functions effectively, searching for edge cases and potential bugs that manually chosen examples might miss. Generators can range from simple primitives like booleans and numbers to complex, nested data structures built by combining other generators.

## Generator Summary Table

| Generator                 | Description                                                     | Key Parameters                                     | Example Usage                                         |
| :------------------------ | :-------------------------------------------------------------- | :------------------------------------------------- | :---------------------------------------------------- |
| **Primitives**            |                                                                 |                                                    |                                                       |
| `Gen.bool()`             | Generates `True` or `False`.                                    | `true_prob` (def: 0.5)                              | `Gen.bool()`                                       |
| `Gen.float()`             | Generates floating-point numbers (incl. `inf`, `-inf`, `nan`).     | `min_value`, `max_value`                              | `Gen.float(min_value=0.0, max_value=1.0)`                                         |
| `Gen.int()`  | Generates integers in the range `[min_value, max_value]`.                   | `min_value`, `max_value`                                       | `Gen.int(min_value=0, max_value=10)`                                 |
| `Gen.str()`  | Generates strings (defaults to ASCII).                          | `min_length` (def: 0), `max_length` (def: 10)        | `Gen.str(min_length=0, max_length=5)`                                    |
| `Gen.ascii_str(...)`    | Generates strings containing only ASCII chars (0-127).          | `min_length` (def: 0), `max_length` (def: 10)        | `Gen.ascii_str(min_length=1, max_length=8)`                               |
| `Gen.unicode_str(...)`  | Generates strings containing Unicode chars.                     | `min_length` (def: 0), `max_length` (def: 10)        | `Gen.unicode_str(min_length=1, max_length=8)`                             |
| `Gen.printable_ascii_str(...)` | Generates strings containing only printable ASCII chars.  | `min_length` (def: 0), `max_length` (def: 10)        | `Gen.printable_ascii_str(min_length=5, max_length=5)`                      |
| **Containers**            |                                                                 |                                                    |                                                       |
| `Gen.list(elem, min_length, max_length)` | Generates lists with elements from `elem`.                   | `element_gen`, `min_length` (def: 0), `max_length` (def: 10) | `Gen.list(Gen.bool(), min_length=2, max_length=4)`                      |
| `Gen.set(elem, min_size, max_size)`   | Generates `set` objects with elements from `elem`.            | `element_gen`, `min_size` (def: 0), `max_size` (def: 10)   | `Gen.set(Gen.int(min_value=1, max_value=3), min_size=1, max_size=3)`                   |
| `Gen.dict(key_gen, val_gen, min_size, max_size)` | Generates dictionaries with keys from `key_gen` and values from `val_gen`. | `key_gen`, `value_gen`, `min_size` (def: 0), `max_size` (def: 10)   | `Gen.dict(Gen.str(min_length=1, max_length=2), Gen.int(min_value=0, max_value=5), min_size=2, max_size=5)` |
| `Gen.tuple(...gens)`      | Generates fixed-size tuples from `gens`.             | `...element_gens`                                   | `Gen.tuple(Gen.float(), Gen.str())`             |
| **Special**               |                                                                 |                                                    |                                                       |
| `Gen.just(value)`         | Always generates the provided `value`.                          | `value`                                            | `Gen.just(None)`                                      |
| `Gen.lazy(value_factory)`   | Defers execution of a function to produce `value` until needed. | `value_factory: Callable[[], T]`                            | `Gen.lazy(lambda: expensive_calculation())`              |

*(Defaults for length/size are typically 0 and 10, but check implementation for specifics)*

## Examples

Here are some more detailed examples illustrating how to use various generators:

**`Gen.float()`**

Generates standard floating-point numbers, but also includes special values crucial for testing numerical robustness:

```python
# Can produce: 3.14, -0.0, inf, -inf, nan
Gen.float()
```

**`Gen.str()`**

Generates strings. You can control the character set and length.

```python
# Generates ASCII strings of length 5 to 10
Gen.str(min_length=5, max_length=10)  # Default character set is printable ASCII

# Generates Unicode strings of exactly length 3
Gen.unicode_str(min_length=3, max_length=3)

# Generates printable ASCII strings of length 0 to 5
Gen.printable_ascii_str(min_length=0, max_length=5)
```

**`Gen.list()`**

Generates lists where each element is created by the provided element generator.

```python
# Generates lists of 2 to 5 booleans
# e.g., [True, False], [False, False, True, True]
Gen.list(Gen.bool(), min_length=2, max_length=5)

# Generates lists of 0 to 10 strings, each 1-3 chars long
Gen.list(Gen.str(min_length=1, max_length=3), min_length=0, max_length=10)
```

**`Gen.dict()`**

Generates dictionaries with string keys generated by `key_gen` and values generated by the provided `value_gen`.

```python
# Generates dictionaries with 1 to 3 key-value pairs,
# where keys are 1-char strings (a-z) and values are floats.
# e.g., {"a": 1.2, "b": -inf}, {"z": 10.0}
key_gen = Gen.str(min_length=1, max_length=1).map(
    lambda s: chr(97 + (ord(s[0]) % 26))  # Generate a-z keys
)
Gen.dict(key_gen, Gen.float(), min_size=1, max_size=3)
```

**`Gen.tuple()`**

Generates fixed-size tuples with elements of potentially different types, determined by the sequence of generators provided.

```python
# Generates pairs of (bool, float)
# e.g., (True, 15.0), (False, -3.1)
Gen.tuple(Gen.bool(), Gen.float())

# Generates triples of (str, int, str)
# e.g., ("hello", 5, "world"), ("", -100, "test")
Gen.tuple(Gen.str(min_length=0, max_length=5), Gen.int(min_value=-100, max_value=100), Gen.str(min_length=1, max_length=4))
```

**`Gen.just(value)`**

A generator that *always* produces the exact `value` provided. Useful for including specific edge cases or constants in your generated data mix (often used with `Gen.one_of`).

```python
# Always generates the number 42
Gen.just(42)

# Always generates None
Gen.just(None)
```

**`Gen.lazy(value_factory)`**

Defers the execution of a function that produces a value `T`. The function is only called when the generator's `generate` method is invoked. This is useful for delaying expensive computations or breaking simple circular dependencies in definitions.

```python
# Example: Deferring an expensive calculation
def expensive_calculation():
    # ... imagine complex logic here ...
    return result

lazy_result_gen = Gen.lazy(expensive_calculation)
```

Beyond the built-in generators, `python-proptest` provides **combinators**: functions that transform or combine existing generators to create new, more complex ones. This is how you build generators for your specific data types and constraints.

These combinators are essential tools for tailoring data generation precisely to your testing needs. For a comprehensive guide on how to use them, see the [Combinators](./combinators.md) documentation.
