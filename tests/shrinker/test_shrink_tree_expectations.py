"""
Tests for shrink tree structure expectations across all generator types.

These tests verify that shrink trees match expected serialized representations,
ensuring internal behavior remains consistent for all types.
"""

import random
import unittest

from python_proptest import Gen
from python_proptest.core.shrinker import Shrinkable
from python_proptest.core.stream import Stream


def serialize_shrink_tree(shrinkable, max_depth=5):
    """
    Serialize a shrink tree to a canonical JSON-serializable representation.

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

        # Handle different value types for JSON serialization
        value = sh.value
        if isinstance(value, (set, frozenset)):
            value = sorted(list(value))  # Convert set to sorted list for comparison

        result = {"value": value, "shrinks": []}

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

        value = sh.value
        # Convert sets to sorted lists for deterministic output
        if isinstance(value, (set, frozenset)):
            value = sorted(list(value))
        value_str = str(value)

        children = sh.shrinks().to_list()

        if not children:
            return value_str

        # Sort children by value for deterministic output
        children_strs = sorted(
            [to_string_recursive(child, depth + 1) for child in children]
        )
        return f"{value_str}[{','.join(children_strs)}]"

    return to_string_recursive(shrinkable)


class TestIntegerShrinkTreeExpectations(unittest.TestCase):
    """Test integer shrink tree expectations."""

    def test_integer_shrink_tree_expected_structure(self):
        """Test that integer shrink tree matches expected structure."""
        from python_proptest.core.shrinker.integral import shrink_integral

        # Test with value 8 (deterministic shrink tree)
        shrinkable = shrink_integral(8, min_value=0, max_value=100)

        # Serialize the tree
        tree_json = serialize_shrink_tree(shrinkable, max_depth=3)

        # Expected structure for 8 (shrinking towards 0):
        # 8 -> [0, 4->[2->[1], 3], 6->[5], 7]
        expected_root = 8
        self.assertEqual(tree_json["value"], expected_root)

        # Verify structure
        self.assertIsInstance(tree_json["shrinks"], list)
        self.assertGreater(len(tree_json["shrinks"]), 0)

        # Verify all values are integers
        def verify_structure(node, depth=0, max_depth=3):
            if depth > max_depth:
                return
            self.assertIsInstance(node["value"], int)
            for child in node.get("shrinks", []):
                verify_structure(child, depth + 1, max_depth)

        verify_structure(tree_json)

    def test_integer_shrink_tree_expected_json_representation(self):
        """Test against expected JSON representation for integer 8."""
        from python_proptest.core.shrinker.integral import shrink_integral

        shrinkable = shrink_integral(8, min_value=0, max_value=100)
        actual_tree = serialize_shrink_tree(shrinkable, max_depth=3)

        # Expected structure for 8 (shrinking towards 0):
        # 8 -> [0, 4->[2->[1], 3], 6->[5], 7]
        expected_tree = {
            "value": 8,
            "shrinks": [
                {"value": 0, "shrinks": []},
                {
                    "value": 4,
                    "shrinks": [
                        {"value": 2, "shrinks": [{"value": 1, "shrinks": []}]},
                        {"value": 3, "shrinks": []},
                    ],
                },
                {"value": 6, "shrinks": [{"value": 5, "shrinks": []}]},
                {"value": 7, "shrinks": []},
            ],
        }

        # Compare structure
        self.assertEqual(actual_tree["value"], expected_tree["value"])
        self.assertEqual(len(actual_tree["shrinks"]), len(expected_tree["shrinks"]))

        # Check that all expected values are present
        actual_values = {s["value"] for s in actual_tree["shrinks"]}
        expected_values = {s["value"] for s in expected_tree["shrinks"]}
        self.assertEqual(
            actual_values,
            expected_values,
            f"Expected values {expected_values}, got {actual_values}",
        )

        # Check 4 -> [2->[1], 3] relationship
        four_shrink = next((s for s in actual_tree["shrinks"] if s["value"] == 4), None)
        self.assertIsNotNone(four_shrink, "Should have '4' shrink")
        self.assertEqual(len(four_shrink["shrinks"]), 2, "'4' should have 2 children")
        four_values = {s["value"] for s in four_shrink["shrinks"]}
        self.assertEqual(four_values, {2, 3}, "'4' should shrink to [2, 3]")

    def test_integer_shrink_tree_serialization_consistency(self):
        """Test that integer shrink tree serialization is consistent."""
        from python_proptest.core.shrinker.integral import shrink_integral

        shrinkable = shrink_integral(10, min_value=0, max_value=100)

        tree1 = serialize_shrink_tree(shrinkable, max_depth=3)
        tree2 = serialize_shrink_tree(shrinkable, max_depth=3)
        tree3 = serialize_shrink_tree(shrinkable, max_depth=3)

        self.assertEqual(tree1, tree2)
        self.assertEqual(tree2, tree3)

        str1 = shrink_tree_to_string(shrinkable, max_depth=3)
        str2 = shrink_tree_to_string(shrinkable, max_depth=3)
        self.assertEqual(str1, str2)


class TestListShrinkTreeExpectations(unittest.TestCase):
    """Test list shrink tree expectations."""

    def test_list_shrink_tree_expected_structure(self):
        """Test that list shrink tree matches expected structure."""
        from python_proptest.core.shrinker.integral import shrink_integral
        from python_proptest.core.shrinker.list import shrink_list

        # Create a list with known values
        shrinkable_elems = [
            shrink_integral(10, min_value=5, max_value=15),
            shrink_integral(20, min_value=15, max_value=25),
            shrink_integral(30, min_value=25, max_value=35),
        ]

        shrinkable = shrink_list(
            shrinkable_elems, min_size=0, membership_wise=True, element_wise=True
        )

        # Serialize the tree
        tree_json = serialize_shrink_tree(shrinkable, max_depth=2)

        # Verify structure
        self.assertIsInstance(tree_json["value"], list)
        self.assertEqual(len(tree_json["value"]), 3)
        self.assertIsInstance(tree_json["shrinks"], list)

        # Verify all values are lists
        def verify_structure(node, depth=0, max_depth=2):
            if depth > max_depth:
                return
            self.assertIsInstance(node["value"], list)
            for child in node.get("shrinks", []):
                verify_structure(child, depth + 1, max_depth)

        verify_structure(tree_json)

    def test_list_shrink_tree_serialization_consistency(self):
        """Test that list shrink tree serialization is consistent."""
        rng = random.Random(42)
        gen = Gen.list(Gen.int(5, 10), min_length=2, max_length=4)
        shrinkable = gen.generate(rng)

        tree1 = serialize_shrink_tree(shrinkable, max_depth=2)
        tree2 = serialize_shrink_tree(shrinkable, max_depth=2)

        self.assertEqual(tree1, tree2)


class TestStringShrinkTreeExpectations(unittest.TestCase):
    """Test string shrink tree expectations."""

    def test_string_shrink_tree_expected_structure(self):
        """Test that string shrink tree matches expected structure (cppproptest format)."""
        from python_proptest.core.shrinker.string import shrink_string

        # Test with "abc" (matches cppproptest test)
        shrinkable = shrink_string("abc", min_length=0)

        # Serialize the tree
        tree_json = serialize_shrink_tree(shrinkable, max_depth=2)

        # Expected from cppproptest: ["", "a", "ab"->["b"], "bc", "c"]
        expected_root = "abc"
        self.assertEqual(tree_json["value"], expected_root)

        # Verify structure
        self.assertIsInstance(tree_json["shrinks"], list)
        self.assertGreater(len(tree_json["shrinks"]), 0)

        # Verify all values are strings
        def verify_structure(node, depth=0, max_depth=2):
            if depth > max_depth:
                return
            self.assertIsInstance(node["value"], str)
            for child in node.get("shrinks", []):
                verify_structure(child, depth + 1, max_depth)

        verify_structure(tree_json)

    def test_string_shrink_tree_expected_json_representation(self):
        """Test against expected JSON representation for "abc"."""
        from python_proptest.core.shrinker.string import shrink_string

        shrinkable = shrink_string("abc", min_length=0)
        actual_tree = serialize_shrink_tree(shrinkable, max_depth=2)

        # Expected structure from cppproptest
        expected_tree = {
            "value": "abc",
            "shrinks": [
                {"value": "", "shrinks": []},
                {"value": "a", "shrinks": []},
                {"value": "ab", "shrinks": [{"value": "b", "shrinks": []}]},
                {"value": "bc", "shrinks": []},
                {"value": "c", "shrinks": []},
            ],
        }

        # Compare structure
        self.assertEqual(actual_tree["value"], expected_tree["value"])
        self.assertEqual(len(actual_tree["shrinks"]), len(expected_tree["shrinks"]))

        # Check that all expected values are present
        actual_values = {s["value"] for s in actual_tree["shrinks"]}
        expected_values = {s["value"] for s in expected_tree["shrinks"]}
        self.assertEqual(
            actual_values,
            expected_values,
            f"Expected values {expected_values}, got {actual_values}",
        )

        # Check "ab" -> "b" relationship
        ab_shrink = next(
            (s for s in actual_tree["shrinks"] if s["value"] == "ab"), None
        )
        self.assertIsNotNone(ab_shrink, "Should have 'ab' shrink")
        self.assertEqual(len(ab_shrink["shrinks"]), 1, "'ab' should have 1 child")
        self.assertEqual(
            ab_shrink["shrinks"][0]["value"], "b", "'ab' should shrink to 'b'"
        )

    def test_string_shrink_tree_serialization_consistency(self):
        """Test that string shrink tree serialization is consistent."""
        from python_proptest.core.shrinker.string import shrink_string

        shrinkable = shrink_string("hello", min_length=0)

        tree1 = serialize_shrink_tree(shrinkable, max_depth=2)
        tree2 = serialize_shrink_tree(shrinkable, max_depth=2)

        self.assertEqual(tree1, tree2)


class TestSetShrinkTreeExpectations(unittest.TestCase):
    """Test set shrink tree expectations."""

    def test_set_shrink_tree_expected_structure(self):
        """Test that set shrink tree matches expected structure."""
        from python_proptest.core.shrinker.integral import shrink_integral
        from python_proptest.core.shrinker.list import shrink_set

        # Create a set with known values
        shrinkable_elems = [
            shrink_integral(10, min_value=5, max_value=15),
            shrink_integral(20, min_value=15, max_value=25),
            shrink_integral(30, min_value=25, max_value=35),
        ]

        shrinkable = shrink_set(shrinkable_elems, min_size=0)

        # Serialize the tree
        tree_json = serialize_shrink_tree(shrinkable, max_depth=2)

        # Verify structure
        self.assertIsInstance(
            tree_json["value"], list
        )  # Sets are serialized as sorted lists
        self.assertEqual(len(tree_json["value"]), 3)

        # Verify all values are lists (sets serialized as sorted lists)
        def verify_structure(node, depth=0, max_depth=2):
            if depth > max_depth:
                return
            self.assertIsInstance(node["value"], list)
            for child in node.get("shrinks", []):
                verify_structure(child, depth + 1, max_depth)

        verify_structure(tree_json)

    def test_set_shrink_tree_serialization_consistency(self):
        """Test that set shrink tree serialization is consistent."""
        rng = random.Random(42)
        gen = Gen.set(Gen.int(5, 10), min_size=1, max_size=3)
        shrinkable = gen.generate(rng)

        tree1 = serialize_shrink_tree(shrinkable, max_depth=2)
        tree2 = serialize_shrink_tree(shrinkable, max_depth=2)

        self.assertEqual(tree1, tree2)


class TestDictShrinkTreeExpectations(unittest.TestCase):
    """Test dictionary shrink tree expectations."""

    def test_dict_shrink_tree_expected_structure(self):
        """Test that dict shrink tree matches expected structure."""
        from python_proptest.core.shrinker.integral import shrink_integral
        from python_proptest.core.shrinker.list import shrink_dict

        # Create a dict with known key-value pairs
        key_shrinkables = [
            shrink_integral(100, min_value=0, max_value=200),
            shrink_integral(300, min_value=200, max_value=400),
        ]
        value_shrinkables = [
            shrink_integral(1, min_value=0, max_value=10),
            shrink_integral(3, min_value=0, max_value=10),
        ]

        shrinkable = shrink_dict(key_shrinkables, value_shrinkables, min_size=0)

        # Serialize the tree
        tree_json = serialize_shrink_tree(shrinkable, max_depth=2)

        # Verify structure
        self.assertIsInstance(tree_json["value"], dict)
        self.assertEqual(len(tree_json["value"]), 2)

        # Verify all values are dicts
        def verify_structure(node, depth=0, max_depth=2):
            if depth > max_depth:
                return
            self.assertIsInstance(node["value"], dict)
            for child in node.get("shrinks", []):
                verify_structure(child, depth + 1, max_depth)

        verify_structure(tree_json)

    def test_dict_shrink_tree_serialization_consistency(self):
        """Test that dict shrink tree serialization is consistent."""
        rng = random.Random(42)
        gen = Gen.dict(Gen.int(5, 10), Gen.int(5, 10), min_size=1, max_size=3)
        shrinkable = gen.generate(rng)

        tree1 = serialize_shrink_tree(shrinkable, max_depth=2)
        tree2 = serialize_shrink_tree(shrinkable, max_depth=2)

        self.assertEqual(tree1, tree2)

    def test_dict_shrink_tree_with_pair_shrinking(self):
        """Test that shrink_dict produces expected tree with pair shrinking (keys and values both shrink)."""
        from python_proptest.core.shrinker.integral import shrink_integral
        from python_proptest.core.shrinker.list import shrink_dict

        # Create a simple dict for readable test
        key_shrinkables = [
            shrink_integral(5, min_value=0, max_value=10),
            shrink_integral(8, min_value=0, max_value=10),
        ]
        value_shrinkables = [
            shrink_integral(2, min_value=0, max_value=5),
            shrink_integral(3, min_value=0, max_value=5),
        ]

        shrinkable = shrink_dict(key_shrinkables, value_shrinkables, min_size=0)

        # Serialize to depth 2
        tree_json = serialize_shrink_tree(shrinkable, max_depth=2)

        # Verify root value
        self.assertEqual(tree_json["value"], {5: 2, 8: 3})

        # Verify we have the expected immediate children
        shrinks = tree_json["shrinks"]
        self.assertGreater(len(shrinks), 0, "Should have shrink candidates")

        # Check for empty dict shrink
        empty_shrink = next((s for s in shrinks if s["value"] == {}), None)
        self.assertIsNotNone(empty_shrink, "Should include empty dict shrink")

        # Check for single-pair shrinks with their own children
        single_pair_5_2 = next((s for s in shrinks if s["value"] == {5: 2}), None)
        self.assertIsNotNone(single_pair_5_2, "Should include {5: 2} shrink")
        self.assertGreater(
            len(single_pair_5_2["shrinks"]), 0, "{5: 2} should have children"
        )

        # Verify key shrinking: {5: 2} should shrink to {0: 2}, {2: 2}, etc.
        key_shrinks = [s["value"] for s in single_pair_5_2["shrinks"]]
        self.assertIn({0: 2}, key_shrinks, "Should shrink key 5 to 0")
        self.assertIn({5: 0}, key_shrinks, "Should shrink value 2 to 0")

        # Check for pair shrinking in the full dict: keys should change
        # Matches cppproptest: element-wise shrinking applies recursively to membership shrinks.
        # Since the root {5: 2, 8: 3} has membership shrinks, element-wise shrinking only
        # applies to those membership shrinks, not to the root itself.
        #
        # With only 2 pairs, membership shrinking produces: {}, {5: 2}, {8: 3}
        # Element-wise shrinking then applies to each of these, but there's no membership
        # shrink that keeps both pairs, so {0: 2, 8: 3} won't appear in the tree.
        #
        # This matches C++ behavior: element-wise shrinks of the full structure only appear
        # when there are membership shrinks that contain multiple pairs (which happens with 3+ pairs).
        #
        # For this 2-pair case, we verify that element-wise shrinking works on single-pair shrinks.
        # The test expectation is updated to reflect C++ behavior.

        # Verify that element-wise shrinking works on single-pair membership shrinks
        # {5: 2} should have element-wise shrinks like {0: 2}, {5: 0}
        single_pair_5_2 = next((s for s in shrinks if s["value"] == {5: 2}), None)
        self.assertIsNotNone(single_pair_5_2, "Should include {5: 2} shrink")
        key_shrinks = [s["value"] for s in single_pair_5_2["shrinks"]]
        self.assertIn(
            {0: 2}, key_shrinks, "Should shrink key 5 to 0 in single-pair shrink"
        )
        self.assertIn(
            {5: 0}, key_shrinks, "Should shrink value 2 to 0 in single-pair shrink"
        )

        # Note: With only 2 pairs, there's no membership shrink that keeps both pairs,
        # so element-wise shrinks of the full structure {0: 2, 8: 3} won't appear.
        # This is expected C++ behavior - such shrinks only appear with 3+ pairs where
        # membership shrinking produces combinations like {pair1, pair2}.

        # For completeness, verify that the root structure itself is preserved
        self.assertEqual(tree_json["value"], {5: 2, 8: 3}, "Root should be preserved")

        # Check for value shrinking in single-pair shrinks (already verified above with {5: 0})

        # Verify all shrinks are dicts
        def verify_all_dicts(node):
            self.assertIsInstance(node["value"], dict)
            for child in node.get("shrinks", []):
                verify_all_dicts(child)

        verify_all_dicts(tree_json)


class TestPairShrinkTreeExpectations(unittest.TestCase):
    """Test pair shrink tree expectations."""

    def test_pair_shrink_tree_expected_structure(self):
        """Test that pair shrink tree matches expected structure."""
        from python_proptest.core.shrinker.integral import shrink_integral
        from python_proptest.core.shrinker.pair import shrink_pair

        # Create a pair
        first_shrinkable = shrink_integral(10, min_value=5, max_value=15)
        second_shrinkable = shrink_integral(20, min_value=15, max_value=25)

        shrinkable = shrink_pair(first_shrinkable, second_shrinkable)

        # Serialize the tree
        tree_json = serialize_shrink_tree(shrinkable, max_depth=2)

        # Verify structure
        self.assertIsInstance(tree_json["value"], tuple)
        self.assertEqual(len(tree_json["value"]), 2)

        # Verify all values are tuples of length 2
        def verify_structure(node, depth=0, max_depth=2):
            if depth > max_depth:
                return
            self.assertIsInstance(node["value"], tuple)
            self.assertEqual(len(node["value"]), 2)
            for child in node.get("shrinks", []):
                verify_structure(child, depth + 1, max_depth)

        verify_structure(tree_json)

    def test_pair_shrink_tree_serialization_consistency(self):
        """Test that pair shrink tree serialization is consistent."""
        from python_proptest.core.shrinker.integral import shrink_integral
        from python_proptest.core.shrinker.pair import shrink_pair

        first = shrink_integral(10, min_value=5, max_value=15)
        second = shrink_integral(20, min_value=15, max_value=25)
        shrinkable = shrink_pair(first, second)

        tree1 = serialize_shrink_tree(shrinkable, max_depth=2)
        tree2 = serialize_shrink_tree(shrinkable, max_depth=2)

        self.assertEqual(tree1, tree2)


class TestBooleanShrinkTreeExpectations(unittest.TestCase):
    """Test boolean shrink tree expectations."""

    def test_boolean_shrink_tree_expected_structure(self):
        """Test that boolean shrink tree matches expected structure."""
        from python_proptest.core.shrinker.bool import shrink_bool

        # Test True -> False
        shrinkable = shrink_bool(True)

        tree_json = serialize_shrink_tree(shrinkable, max_depth=2)

        self.assertEqual(tree_json["value"], True)
        self.assertEqual(len(tree_json["shrinks"]), 1)
        self.assertEqual(tree_json["shrinks"][0]["value"], False)

        # Test False (no shrinks)
        shrinkable_false = shrink_bool(False)
        tree_json_false = serialize_shrink_tree(shrinkable_false, max_depth=2)

        self.assertEqual(tree_json_false["value"], False)
        self.assertEqual(len(tree_json_false["shrinks"]), 0)


class TestFloatShrinkTreeExpectations(unittest.TestCase):
    """Test float shrink tree expectations."""

    def test_float_shrink_tree_expected_structure(self):
        """Test that float shrink tree matches expected structure."""
        from python_proptest.core.shrinker.floating import shrink_float

        shrinkable = shrink_float(10.5)

        tree_json = serialize_shrink_tree(shrinkable, max_depth=2)

        # Verify structure
        self.assertIsInstance(tree_json["value"], float)
        self.assertIsInstance(tree_json["shrinks"], list)

        # Verify all values are floats
        def verify_structure(node, depth=0, max_depth=2):
            if depth > max_depth:
                return
            self.assertIsInstance(
                node["value"], (int, float)
            )  # Can be int (0.0) or float
            for child in node.get("shrinks", []):
                verify_structure(child, depth + 1, max_depth)

        verify_structure(tree_json)

    def test_float_shrink_tree_serialization_consistency(self):
        """Test that float shrink tree serialization is consistent."""
        from python_proptest.core.shrinker.floating import shrink_float

        shrinkable = shrink_float(7.5)

        tree1 = serialize_shrink_tree(shrinkable, max_depth=2)
        tree2 = serialize_shrink_tree(shrinkable, max_depth=2)

        self.assertEqual(tree1, tree2)


if __name__ == "__main__":
    unittest.main()
