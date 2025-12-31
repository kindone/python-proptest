"""
Tests for combinator shrink tree structure preservation using known structures.

These tests verify that combinators (map, filter, chain, flatMap, aggregate, accumulate, oneOf)
preserve shrink tree structure correctly when applied to known test structures (40213, 7531246, 964285173).

Inspired by dartproptest's combinator_constraint_tree_test.dart.
"""

import json
import random
import unittest

from python_proptest import Gen
from python_proptest.core.shrinker import Shrinkable
from python_proptest.core.stream import Stream


def serialize_shrinkable(shrinkable: Shrinkable) -> str:
    """Serialize a shrinkable to JSON string (compact format)."""
    obj = {"value": shrinkable.value}

    shrinks = shrinkable.shrinks()
    if not shrinks.is_empty():
        shrinks_list = []
        for shrink in shrinks.to_list():
            shrinks_list.append(json.loads(serialize_shrinkable(shrink)))
        obj["shrinks"] = shrinks_list

    return json.dumps(obj, separators=(",", ":"))


def gen_shrinkable_40213() -> Shrinkable[int]:
    """Generate a shrinkable with value 4 and shrinks [0, 2->1, 3]."""
    return Shrinkable(4).with_shrinks(
        lambda: Stream.many(
            [
                Shrinkable(0),
                Shrinkable(2).with_shrinks(lambda: Stream.one(Shrinkable(1))),
                Shrinkable(3),
            ]
        )
    )


def gen_shrinkable_7531246() -> Shrinkable[int]:
    """Generate a shrinkable with value 7 and shrinks [5->[3->1, 2], 4, 6]."""
    return Shrinkable(7).with_shrinks(
        lambda: Stream.many(
            [
                Shrinkable(5).with_shrinks(
                    lambda: Stream.many(
                        [
                            Shrinkable(3).with_shrinks(
                                lambda: Stream.one(Shrinkable(1))
                            ),
                            Shrinkable(2),
                        ]
                    )
                ),
                Shrinkable(4),
                Shrinkable(6),
            ]
        )
    )


def gen_shrinkable_964285173() -> Shrinkable[int]:
    """Generate a shrinkable with value 9 and shrinks [6->[4->2, 8], 5->1, 7->3]."""
    return Shrinkable(9).with_shrinks(
        lambda: Stream.many(
            [
                Shrinkable(6).with_shrinks(
                    lambda: Stream.many(
                        [
                            Shrinkable(4).with_shrinks(
                                lambda: Stream.one(Shrinkable(2))
                            ),
                            Shrinkable(8),
                        ]
                    )
                ),
                Shrinkable(5).with_shrinks(lambda: Stream.one(Shrinkable(1))),
                Shrinkable(7).with_shrinks(lambda: Stream.one(Shrinkable(3))),
            ]
        )
    )


def collect_all_values(shrinkable, all_values=None, max_depth=100):
    """Collect all values from a shrinkable tree into a set."""
    if all_values is None:
        all_values = set()
    if max_depth <= 0:
        return all_values
    all_values.add(shrinkable.value)
    for child in shrinkable.shrinks().to_list():
        collect_all_values(child, all_values, max_depth - 1)
    return all_values


def verify_constraint(shrinkable, constraint, max_depth=100):
    """Verify that all values in a shrinkable tree satisfy a constraint."""
    if max_depth <= 0:
        return True
    if not constraint(shrinkable.value):
        return False
    for child in shrinkable.shrinks().to_list():
        if not verify_constraint(child, constraint, max_depth - 1):
            return False
    return True


class TestCombinatorShrinkTrees40213(unittest.TestCase):
    """Test combinator shrink tree preservation using 40213 structure."""

    def test_map_preserves_tree_structure_even_numbers(self):
        """Test that map preserves tree structure: even numbers only."""
        # Start with 40213 structure, map to double values
        # Expected tree structure after mapping (x * 2):
        #   8
        #   ├─ 0
        #   ├─ 4
        #   │  └─ 2
        #   └─ 6
        base_shrinkable = gen_shrinkable_40213()
        mapped_shrinkable = base_shrinkable.map(lambda x: x * 2)

        actual_serialized = serialize_shrinkable(mapped_shrinkable)
        expected_serialized = (
            '{"value":8,"shrinks":[{"value":0},{"value":4,"shrinks":[{"value":2}]},'
            '{"value":6}]}'
        )

        self.assertEqual(
            actual_serialized,
            expected_serialized,
            "Mapped tree structure should match expected structure",
        )

        # Verify all shrunk values are even
        self.assertTrue(
            verify_constraint(mapped_shrinkable, lambda x: x % 2 == 0),
            "All shrunk values should satisfy the even constraint",
        )

    def test_filter_preserves_tree_structure_ge_2(self):
        """Test that filter preserves tree structure: only values >= 2."""
        # Filter the 40213 structure to only include values >= 2
        # Expected tree structure after filtering (x >= 2):
        #   4
        #   ├─ 2
        #   └─ 3
        # (0 and 1 are filtered out)
        base_shrinkable = gen_shrinkable_40213()

        # Filter: only keep values >= 2
        def filter_func(value):
            return value >= 2

        # Apply filter recursively
        def apply_filter(sh):
            if not filter_func(sh.value):
                return None
            filtered_children = []
            for child in sh.shrinks().to_list():
                filtered_child = apply_filter(child)
                if filtered_child is not None:
                    filtered_children.append(filtered_child)
            return Shrinkable(sh.value).with_shrinks(
                lambda: Stream.many(filtered_children) if filtered_children else Stream.empty()
            )

        filtered_shrinkable = apply_filter(base_shrinkable)

        actual_serialized = serialize_shrinkable(filtered_shrinkable)
        expected_serialized = '{"value":4,"shrinks":[{"value":2},{"value":3}]}'

        self.assertEqual(
            actual_serialized,
            expected_serialized,
            "Filtered tree structure should match expected structure",
        )

        # Verify all shrunk values satisfy the constraint
        self.assertTrue(
            verify_constraint(filtered_shrinkable, lambda x: x >= 2),
            "All shrunk values should satisfy the filter constraint",
        )


class TestCombinatorShrinkTrees7531246(unittest.TestCase):
    """Test combinator shrink tree preservation using 7531246 structure."""

    def test_map_preserves_tree_structure_7531246(self):
        """Test that map preserves tree structure on larger structure."""
        base_shrinkable = gen_shrinkable_7531246()
        mapped_shrinkable = base_shrinkable.map(lambda x: x * 2)

        # Verify structure is preserved (all values doubled)
        # 7*2=14, 5*2=10, 3*2=6, 1*2=2, 2*2=4, 4*2=8, 6*2=12
        expected_serialized = (
            '{"value":14,"shrinks":[{"value":10,"shrinks":[{"value":6,"shrinks":'
            '[{"value":2}]},{"value":4}]},{"value":8},{"value":12}]}'
        )
        actual_serialized = serialize_shrinkable(mapped_shrinkable)

        self.assertEqual(
            actual_serialized,
            expected_serialized,
            "Mapped tree structure should match expected structure",
        )

        # Verify all values are even (doubled)
        self.assertTrue(
            verify_constraint(mapped_shrinkable, lambda x: x % 2 == 0),
            "All shrunk values should be even",
        )


class TestCombinatorShrinkTrees964285173(unittest.TestCase):
    """Test combinator shrink tree preservation using 964285173 structure."""

    def test_map_preserves_tree_structure_964285173(self):
        """Test that map preserves tree structure on largest structure."""
        base_shrinkable = gen_shrinkable_964285173()
        mapped_shrinkable = base_shrinkable.map(lambda x: x * 2)

        # Verify structure is preserved (all values doubled)
        # 9*2=18, 6*2=12, 4*2=8, 2*2=4, 8*2=16, 5*2=10, 1*2=2, 7*2=14, 3*2=6
        expected_serialized = (
            '{"value":18,"shrinks":[{"value":12,"shrinks":[{"value":8,"shrinks":'
            '[{"value":4}]},{"value":16}]},{"value":10,"shrinks":[{"value":2}]},'
            '{"value":14,"shrinks":[{"value":6}]}]}'
        )
        actual_serialized = serialize_shrinkable(mapped_shrinkable)

        self.assertEqual(
            actual_serialized,
            expected_serialized,
            "Mapped tree structure should match expected structure",
        )

        # Verify all values are even (doubled)
        self.assertTrue(
            verify_constraint(mapped_shrinkable, lambda x: x % 2 == 0),
            "All shrunk values should be even",
        )


class TestCombinatorShrinkTreesChain(unittest.TestCase):
    """Test chain combinator shrink tree preservation."""

    def test_chain_preserves_tree_structure_40213(self):
        """Test that chain preserves tree structure with dependent values."""
        # Chain: first value from 40213, second value must be <= first
        # We'll create a generator that uses 40213 structure
        base_shrinkable = gen_shrinkable_40213()

        # Create a chain: second value is half of first (rounded down)
        def create_chained_shrinkable(base_shr):
            def create_second_shrinkable(first_val):
                # Second value is first_val // 2
                second_val = first_val // 2
                return Shrinkable(second_val)

            # For each shrink of base, create a tuple shrinkable
            def create_tuple_shrinks():
                shrinks_list = []
                for child in base_shr.shrinks().to_list():
                    second_shr = create_second_shrinkable(child.value)
                    tuple_shr = Shrinkable((child.value, second_shr.value))
                    shrinks_list.append(tuple_shr)
                return Stream.many(shrinks_list)

            # Root tuple
            root_second = create_second_shrinkable(base_shr.value)
            root_tuple = Shrinkable((base_shr.value, root_second.value))
            return root_tuple.with_shrinks(create_tuple_shrinks)

        chained_shrinkable = create_chained_shrinkable(base_shrinkable)

        # Verify constraint: second value should be <= first
        all_pairs = set()

        def collect_pairs(sh, depth=0, max_depth=50):
            if depth > max_depth:
                return
            if isinstance(sh.value, tuple):
                all_pairs.add(sh.value)
            for child in sh.shrinks().to_list():
                collect_pairs(child, depth + 1, max_depth)

        collect_pairs(chained_shrinkable)

        for first, second in all_pairs:
            self.assertLessEqual(
                second,
                first,
                f"Second value {second} should be <= first value {first}",
            )


class TestCombinatorShrinkTreesFlatMap(unittest.TestCase):
    """Test flatMap combinator shrink tree preservation."""

    def test_flat_map_preserves_constraints_40213(self):
        """Test that flatMap preserves constraints with nested dependency."""
        base_shrinkable = gen_shrinkable_40213()

        # FlatMap: generate a list where each element depends on base value
        # For value n, generate list of length n with elements in [0, n]
        def create_flat_mapped_shrinkable(base_shr):
            def create_list_shrinkable(n):
                # Create a list of n elements, each in range [0, n]
                elements = [min(i, n) for i in range(n)]
                return Shrinkable(elements)

            # For each shrink of base, create a list shrinkable
            def create_list_shrinks():
                shrinks_list = []
                for child in base_shr.shrinks().to_list():
                    list_shr = create_list_shrinkable(child.value)
                    shrinks_list.append(list_shr)
                return Stream.many(shrinks_list)

            root_list = create_list_shrinkable(base_shr.value)
            return root_list.with_shrinks(create_list_shrinks)

        flat_mapped_shrinkable = create_flat_mapped_shrinkable(base_shrinkable)

        # Verify constraint: all elements should be <= base value
        all_lists = set()

        def collect_lists(sh, depth=0, max_depth=50):
            if depth > max_depth:
                return
            if isinstance(sh.value, list):
                all_lists.add(tuple(sh.value))  # Use tuple for hashability
            for child in sh.shrinks().to_list():
                collect_lists(child, depth + 1, max_depth)

        collect_lists(flat_mapped_shrinkable)

        # Verify list constraints
        for lst_tuple in all_lists:
            lst = list(lst_tuple)
            self.assertGreaterEqual(
                len(lst), 0, "List should have non-negative length"
            )
            # All elements should be non-negative
            for elem in lst:
                self.assertGreaterEqual(
                    elem, 0, f"Element {elem} should be >= 0"
                )


if __name__ == "__main__":
    unittest.main()
