# Shrinking Requirements

This document outlines the core requirements and design principles for shrinking in python-proptest.

## Core Principles

### 1. No Duplicates in Shrink Tree

**Requirement**: Each value must appear exactly once in the shrink tree, even if it could be reached via multiple paths.

**Rationale**:
- Prevents redundant exploration of the same values
- Enables efficient cut-off strategies
- Simplifies tree structure and analysis

**Example**:
For a list `[1, 2]`, the empty list `[]` should appear only once:
- ✅ Correct: `[]` appears once as a direct child of `[1, 2]`
- ❌ Incorrect: `[]` appearing both directly and via `[1] → []` and `[2] → []`

**Implementation**: Shorter lists/structures created during membership-wise shrinking are created as leaf nodes (without recursive shrink functions) to prevent duplicate paths.

### 2. Simplest First Ordering

**Requirement**: Shrink candidates must be ordered from simplest to more complex, following a "try the simplest one first, then logarithmically grow the value" strategy.

**Rationale**:
- Most direct shrinks are tried first (highest probability of finding minimal counterexample)
- Logarithmic growth ensures we explore meaningful candidates early
- Enables effective early cut-off when shrinking steps become too many

**Example**:
For `Gen.int(0, 8)` with value `8`, the shrink order should be:
1. `0` (simplest - direct shrink to minimum)
2. `4` (midpoint - logarithmic step)
3. `6` (between 4 and 8)
4. `7` (between 6 and 8)
5. Then recursive subtrees for intermediate values

### 3. Logarithmic Growth Pattern

**Requirement**: After the simplest shrink, subsequent shrinks should follow a logarithmic growth pattern.

**Rationale**:
- Binary search approach provides efficient exploration
- Logarithmic steps ensure we cover the space meaningfully
- Matches the "try simplest, then grow logarithmically" principle

**Implementation**:
- Integers use binary search shrinking (midpoint, then recursive halves)
- Arrays use binary search for length reduction
- Element-wise shrinking uses chunked approaches

### 4. Early Cut-off Support

**Requirement**: The shrink tree structure must support efficient early cut-off when shrinking steps become too many.

**Rationale**:
- Prevents unresponsiveness during shrinking
- Allows trying the most meaningful candidates in early stages
- Enables graceful degradation when full shrinking is too expensive

**Implementation**:
- Simplest shrinks appear first in the stream
- Tree structure allows limiting depth/breadth exploration
- `Shrinkable.take(n)` method limits number of candidates

## Tree Structure Requirements

### Compact Representation

Shrink trees should be representable in a compact nested array format:

```python
[value, [children]]
```

Where:
- `value` is the actual value at this node
- `children` is always a list (empty `[]` if no children)
- Each child follows the same `[value, [children]]` format

**Example** for `Gen.int(0, 8)` with value `8`:
```json
[8, [
  [0, []],
  [4, [
    [2, [[1, []]]],
    [3, []]
  ]],
  [6, [[5, []]]],
  [7, []]
]]
```

### Uniqueness Guarantee

The compact representation makes it clear that:
- Each value appears exactly once
- The structure is hierarchical
- No duplicates are implied

## Implementation Guidelines

### Membership-wise Shrinking

For collections (lists, sets, dicts):
- Shorter structures should be created as leaf nodes to prevent duplicate paths
- Direct shrinks (e.g., empty list) should appear before intermediate structures
- Intermediate structures don't recursively shrink to avoid creating duplicate paths

### Element-wise Shrinking

For collections with shrinkable elements:
- Element shrinking should occur after membership shrinking
- Each element's shrink tree is explored independently
- Combined with membership shrinking to find minimal failing cases

### Binary Search Shrinking

For ordered values (integers, array lengths):
- Use binary search to find midpoint
- Recursively shrink each half
- Ensure ranges are half-open to prevent duplicates
- Shrink towards a target (typically 0 for integers, min_size for arrays)

## Verification

To verify shrinking requirements are met:

1. **Uniqueness Check**: Use `check_duplicates()` to ensure no value appears multiple times
2. **Ordering Check**: Verify simplest shrinks appear first in the stream
3. **Structure Check**: Use `collect_tree_compact()` to verify tree structure
4. **Cut-off Test**: Verify `take(n)` provides meaningful shrinks even with small n

## References

- `python_proptest.core.shrinker_utils`: Utility functions for tree analysis
- `python_proptest.core.shrinker`: Core shrinking implementation
- `python_proptest.core.generator`: Generator-specific shrinking logic

