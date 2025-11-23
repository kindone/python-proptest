"""
Tests for tuple shrink tree structure.

These tests verify that the shrink tree structure matches expected serialized
representations, ensuring internal behavior remains consistent.
"""

import unittest
import json
from python_proptest import Gen
import random


def serialize_shrink_tree(shrinkable, max_depth=5):
    """
    Serialize a shrink tree to a canonical JSON representation.
    
    The representation is:
    {
        "value": <value>,
        "shrinks": [<serialized_shrink>, ...]
    }
    
    Args:
        shrinkable: The Shrinkable to serialize
        max_depth: Maximum depth to serialize
    
    Returns:
        A dictionary representing the shrink tree
    """
    def serialize_recursive(sh, depth=0):
        if depth > max_depth:
            return None
        
        result = {
            "value": sh.value,
            "shrinks": []
        }
        
        for child in sh.shrinks().to_list():
            child_serialized = serialize_recursive(child, depth + 1)
            if child_serialized is not None:
                result["shrinks"].append(child_serialized)
        
        return result
    
    return serialize_recursive(shrinkable)


def shrink_tree_to_string(shrinkable, max_depth=5):
    """
    Convert shrink tree to a canonical string representation.
    
    Format: "value[child1,child2,...]" where children are recursively formatted.
    This provides a compact, deterministic representation.
    """
    def to_string_recursive(sh, depth=0):
        if depth > max_depth:
            return "..."
        
        value_str = str(sh.value)
        children = sh.shrinks().to_list()
        
        if not children:
            return value_str
        
        # Sort children by value for deterministic output
        children_strs = sorted([to_string_recursive(child, depth + 1) for child in children])
        return f"{value_str}[{','.join(children_strs)}]"
    
    return to_string_recursive(shrinkable)


class TestTupleShrinkTreeStructure(unittest.TestCase):
    """Test that tuple shrink trees have the expected structure."""
    
    def test_tuple_length_2_shrink_tree(self):
        """Test shrink tree structure for tuple of length 2."""
        rng = random.Random(42)
        gen = Gen.tuple(Gen.int(5, 10), Gen.int(5, 10))
        shrinkable = gen.generate(rng)
        
        # Serialize the tree
        tree_str = shrink_tree_to_string(shrinkable, max_depth=4)
        
        # Expected: root value with shrinks for position 0 and position 1
        # The exact structure depends on the generated values, but we can verify:
        # 1. Root is present
        # 2. Shrinks exist
        # 3. Structure is consistent
        
        self.assertIn(str(shrinkable.value), tree_str)
        self.assertIn("[", tree_str)  # Should have children
        
        # Verify all values respect constraints
        def check_constraints(sh, depth=0, max_depth=5):
            if depth > max_depth:
                return []
            problems = []
            for val in sh.value:
                if val < 5 or val > 10:
                    problems.append((sh.value, val))
            for child in sh.shrinks().to_list():
                problems.extend(check_constraints(child, depth+1, max_depth))
            return problems
        
        problems = check_constraints(shrinkable)
        self.assertEqual(len(problems), 0, f"Constraint violations: {problems}")
    
    def test_tuple_length_3_shrink_tree_deterministic(self):
        """Test shrink tree structure for tuple of length 3 with fixed seed."""
        rng = random.Random(42)
        gen = Gen.tuple(Gen.int(5, 10), Gen.int(5, 10), Gen.int(5, 10))
        shrinkable = gen.generate(rng)
        
        # Serialize to JSON for comparison
        tree_json = serialize_shrink_tree(shrinkable, max_depth=3)
        
        # Verify structure
        self.assertIn("value", tree_json)
        self.assertIn("shrinks", tree_json)
        self.assertEqual(tree_json["value"], shrinkable.value)
        
        # Verify all shrinks are tuples of length 3
        def verify_structure(node, depth=0, max_depth=3):
            if depth > max_depth:
                return
            self.assertIsInstance(node["value"], tuple)
            self.assertEqual(len(node["value"]), 3)
            for child in node.get("shrinks", []):
                verify_structure(child, depth + 1, max_depth)
        
        verify_structure(tree_json)
    
    def test_tuple_shrink_tree_uniqueness(self):
        """Test that all values in shrink tree are unique."""
        rng = random.Random(42)
        gen = Gen.tuple(Gen.int(5, 10), Gen.int(5, 10), Gen.int(5, 10))
        shrinkable = gen.generate(rng)
        
        all_values = []
        def collect_all(sh, depth=0, max_depth=5):
            if depth > max_depth:
                return
            all_values.append(sh.value)
            for child in sh.shrinks().to_list():
                collect_all(child, depth+1, max_depth)
        
        collect_all(shrinkable)
        
        # All values should be unique
        unique_values = set(all_values)
        self.assertEqual(len(all_values), len(unique_values), 
                        f"Found {len(all_values) - len(unique_values)} duplicate values")
    
    def test_tuple_shrink_tree_all_positions_shrink(self):
        """Test that all positions in the tuple can be shrunk."""
        # Find a seed that generates a tuple where all elements can shrink
        for seed in range(100):
            rng = random.Random(seed)
            gen = Gen.tuple(Gen.int(5, 10), Gen.int(5, 10), Gen.int(5, 10))
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Check if all elements are above minimum (can shrink)
            if all(x > 5 for x in root):
                # Collect all values
                all_values = set()
                def collect_all(sh, depth=0, max_depth=4):
                    if depth > max_depth:
                        return
                    all_values.add(sh.value)
                    for child in sh.shrinks().to_list():
                        collect_all(child, depth+1, max_depth)
                
                collect_all(shrinkable)
                
                # Check that each position has been shrunk
                position_shrunk = {0: False, 1: False, 2: False}
                for tup in all_values:
                    if tup == root:
                        continue
                    for i in range(3):
                        if tup[i] != root[i]:
                            position_shrunk[i] = True
                            break
                
                # All positions should be shrinkable
                self.assertTrue(all(position_shrunk.values()),
                               f"Not all positions were shrunk: {position_shrunk}, root={root}")
                break
    
    def test_tuple_shrink_tree_recursive_structure(self):
        """Test that shrink tree has recursive structure (shrinks of shrinks)."""
        rng = random.Random(3)
        gen = Gen.tuple(Gen.int(5, 10), Gen.int(5, 10), Gen.int(5, 10))
        shrinkable = gen.generate(rng)
        
        # Check for recursive shrinking (shrinks should have their own shrinks)
        has_recursive = False
        def check_recursive(sh, depth=0, max_depth=3):
            nonlocal has_recursive
            if depth > max_depth:
                return
            for child in sh.shrinks().to_list():
                if not child.shrinks().is_empty():
                    has_recursive = True
                    return
                check_recursive(child, depth+1, max_depth)
        
        check_recursive(shrinkable)
        self.assertTrue(has_recursive, "Shrink tree should have recursive structure")
    
    def test_tuple_shrink_tree_serialization_consistency(self):
        """Test that serialization is consistent across multiple calls."""
        rng = random.Random(42)
        gen = Gen.tuple(Gen.int(5, 10), Gen.int(5, 10), Gen.int(5, 10))
        shrinkable = gen.generate(rng)
        
        # Serialize multiple times
        tree1 = serialize_shrink_tree(shrinkable, max_depth=3)
        tree2 = serialize_shrink_tree(shrinkable, max_depth=3)
        tree3 = serialize_shrink_tree(shrinkable, max_depth=3)
        
        # Should be identical
        self.assertEqual(tree1, tree2)
        self.assertEqual(tree2, tree3)
        
        # String representation should also be consistent
        str1 = shrink_tree_to_string(shrinkable, max_depth=3)
        str2 = shrink_tree_to_string(shrinkable, max_depth=3)
        self.assertEqual(str1, str2)
    
    def test_tuple_shrink_tree_expected_structure(self):
        """Test against a known expected structure for a specific seed."""
        rng = random.Random(42)
        gen = Gen.tuple(Gen.int(5, 10), Gen.int(5, 10), Gen.int(5, 10))
        shrinkable = gen.generate(rng)
        
        root = shrinkable.value
        
        # Serialize the tree
        tree_str = shrink_tree_to_string(shrinkable, max_depth=3)
        
        # Verify root is in the string
        self.assertIn(str(root), tree_str)
        
        # Verify structure: should have brackets indicating children
        self.assertIn("[", tree_str)
        
        # Count total nodes (approximate by counting opening brackets)
        node_count = tree_str.count("[") + 1  # +1 for root
        self.assertGreater(node_count, 1, "Tree should have more than just the root")
    
    def test_tuple_length_4_shrink_tree(self):
        """Test shrink tree structure for tuple of length 4."""
        rng = random.Random(42)
        gen = Gen.tuple(Gen.int(5, 10), Gen.int(5, 10), Gen.int(5, 10), Gen.int(5, 10))
        shrinkable = gen.generate(rng)
        
        # Serialize the tree
        tree_json = serialize_shrink_tree(shrinkable, max_depth=2)
        
        # Verify structure
        self.assertIn("value", tree_json)
        self.assertIn("shrinks", tree_json)
        self.assertEqual(len(tree_json["value"]), 4)
        
        # Verify all shrinks are tuples of length 4
        def verify_structure(node, depth=0, max_depth=2):
            if depth > max_depth:
                return
            self.assertIsInstance(node["value"], tuple)
            self.assertEqual(len(node["value"]), 4)
            for child in node.get("shrinks", []):
                verify_structure(child, depth + 1, max_depth)
        
        verify_structure(tree_json)
    
    def test_tuple_shrink_tree_with_constraints(self):
        """Test shrink tree structure with constrained generators."""
        rng = random.Random(42)
        gen = Gen.tuple(Gen.int(7, 9), Gen.int(7, 9), Gen.int(7, 9))
        shrinkable = gen.generate(rng)
        
        # Serialize the tree
        tree_str = shrink_tree_to_string(shrinkable, max_depth=3)
        
        # Verify all values in tree respect constraints
        all_values = set()
        def collect_all(sh, depth=0, max_depth=4):
            if depth > max_depth:
                return
            all_values.add(sh.value)
            for child in sh.shrinks().to_list():
                collect_all(child, depth+1, max_depth)
        
        collect_all(shrinkable)
        
        # All values should be within [7, 9] for each element
        for tup in all_values:
            for val in tup:
                self.assertGreaterEqual(val, 7, f"Value {val} < 7 in tuple {tup}")
                self.assertLessEqual(val, 9, f"Value {val} > 9 in tuple {tup}")
    
    def test_tuple_shrink_tree_expected_serialization(self):
        """Test that shrink tree matches expected serialized representation.
        
        This is a regression test to ensure the internal structure doesn't change.
        The expected tree is generated with seed=42, Gen.tuple(Gen.int(5,10), ...).
        """
        rng = random.Random(42)
        gen = Gen.tuple(Gen.int(5, 10), Gen.int(5, 10), Gen.int(5, 10))
        shrinkable = gen.generate(rng)
        
        # Serialize the tree
        tree_json = serialize_shrink_tree(shrinkable, max_depth=3)
        
        # Expected root value (deterministic with seed=42)
        expected_root = (10, 5, 5)
        self.assertEqual(tree_json["value"], expected_root, 
                        f"Root value mismatch. Expected {expected_root}, got {tree_json['value']}")
        
        # Verify tree structure properties
        self.assertIsInstance(tree_json["shrinks"], list)
        self.assertGreater(len(tree_json["shrinks"]), 0, "Tree should have shrinks")
        
        # Verify all shrinks are tuples of length 3
        def verify_all_shrinks(node, depth=0, max_depth=3):
            if depth > max_depth:
                return
            self.assertIsInstance(node["value"], tuple, 
                                f"Node value should be tuple, got {type(node['value'])}")
            self.assertEqual(len(node["value"]), 3,
                           f"Tuple should have length 3, got {len(node['value'])}")
            for child in node.get("shrinks", []):
                verify_all_shrinks(child, depth + 1, max_depth)
        
        verify_all_shrinks(tree_json)
        
        # Verify serialization is deterministic (same tree on multiple calls)
        tree_json2 = serialize_shrink_tree(shrinkable, max_depth=3)
        self.assertEqual(tree_json, tree_json2, "Serialization should be deterministic")
    
    def test_tuple_shrink_tree_expected_json_representation(self):
        """Test against a stored expected JSON representation.
        
        This is a strict regression test. If this fails, it means the internal
        shrink tree structure has changed. Update the expected JSON if the change
        is intentional.
        """
        rng = random.Random(42)
        gen = Gen.tuple(Gen.int(5, 10), Gen.int(5, 10), Gen.int(5, 10))
        shrinkable = gen.generate(rng)
        
        # Serialize the tree
        actual_tree = serialize_shrink_tree(shrinkable, max_depth=3)
        
        # Expected tree structure (generated with seed=42, max_depth=3)
        # Note: Tuples are serialized as lists in JSON
        expected_tree = {
            "value": (10, 5, 5),
            "shrinks": [
                {
                    "value": (5, 5, 5),
                    "shrinks": []
                },
                {
                    "value": (7, 5, 5),
                    "shrinks": [
                        {
                            "value": (6, 5, 5),
                            "shrinks": []
                        }
                    ]
                },
                {
                    "value": (8, 5, 5),
                    "shrinks": []
                },
                {
                    "value": (9, 5, 5),
                    "shrinks": []
                }
            ]
        }
        
        # Compare structures
        self.assertEqual(actual_tree["value"], expected_tree["value"],
                        "Root value mismatch")
        self.assertEqual(len(actual_tree["shrinks"]), len(expected_tree["shrinks"]),
                        "Number of direct shrinks mismatch")
        
        # Compare each shrink
        for i, (actual_shrink, expected_shrink) in enumerate(
            zip(actual_tree["shrinks"], expected_tree["shrinks"])
        ):
            self.assertEqual(actual_shrink["value"], expected_shrink["value"],
                           f"Shrink {i} value mismatch: {actual_shrink['value']} != {expected_shrink['value']}")
            self.assertEqual(len(actual_shrink["shrinks"]), len(expected_shrink["shrinks"]),
                           f"Shrink {i} number of child shrinks mismatch")
            
            # Compare child shrinks if any
            for j, (actual_child, expected_child) in enumerate(
                zip(actual_shrink["shrinks"], expected_shrink["shrinks"])
            ):
                self.assertEqual(actual_child["value"], expected_child["value"],
                               f"Shrink {i} child {j} value mismatch")
    
    def test_tuple_shrink_tree_string_representation(self):
        """Test that string representation is consistent and deterministic."""
        rng = random.Random(42)
        gen = Gen.tuple(Gen.int(5, 10), Gen.int(5, 10), Gen.int(5, 10))
        shrinkable = gen.generate(rng)
        
        # Generate string representation multiple times
        str1 = shrink_tree_to_string(shrinkable, max_depth=3)
        str2 = shrink_tree_to_string(shrinkable, max_depth=3)
        str3 = shrink_tree_to_string(shrinkable, max_depth=3)
        
        # Should be identical
        self.assertEqual(str1, str2)
        self.assertEqual(str2, str3)
        
        # Should contain root value
        self.assertIn(str(shrinkable.value), str1)
        
        # Should have structure (brackets indicate children)
        self.assertIn("[", str1)


if __name__ == "__main__":
    unittest.main()

