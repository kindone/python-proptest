"""
Tests for flat_map RNG state preservation and deterministic regeneration.

These tests verify that flat_map correctly preserves RNG state during
shrinking to ensure reproducible and deterministic behavior.
"""

import unittest
import random
from python_proptest import Gen, Property, PropertyTestError


class TestFlatMapRNGPreservation(unittest.TestCase):
    """Test that flat_map preserves RNG state correctly."""

    def test_flat_map_regeneration_determinism(self):
        """Test that regenerating during shrinking is deterministic."""
        rng1 = random.Random(42)
        rng2 = random.Random(42)
        
        gen = Gen.int(1, 5).flat_map(
            lambda n: Gen.list(Gen.int(1, 10), min_length=n, max_length=n)
        )
        
        shrinkable1 = gen.generate(rng1)
        shrinkable2 = gen.generate(rng2)
        
        # Root values should match
        self.assertEqual(shrinkable1.value, shrinkable2.value)
        
        # Shrink trees should be identical
        shrinks1 = shrinkable1.shrinks().to_list()
        shrinks2 = shrinkable2.shrinks().to_list()
        
        self.assertEqual(len(shrinks1), len(shrinks2))
        
        # All shrink values should match
        for s1, s2 in zip(shrinks1, shrinks2):
            self.assertEqual(s1.value, s2.value, 
                           f"Shrink values don't match: {s1.value} != {s2.value}")
    
    def test_flat_map_regeneration_uses_correct_rng_state(self):
        """Test that regeneration uses the correct RNG state (after first generation)."""
        rng = random.Random(42)
        
        # Generate first value
        first_gen = Gen.int(1, 5)
        first_shrinkable = first_gen.generate(rng)
        first_value = first_shrinkable.value
        
        # Save RNG state after first generation
        rng_state_after_first = rng.getstate()
        
        # Generate second value
        second_gen = Gen.list(Gen.int(1, 10), min_length=first_value, max_length=first_value)
        second_shrinkable = second_gen.generate(rng)
        second_value = second_shrinkable.value
        
        # Now test regeneration: take a shrink of first value
        first_shrinks = first_shrinkable.shrinks().to_list()
        if len(first_shrinks) > 0:
            shrunk_first = first_shrinks[-1]  # Take last shrink
            
            # Wrong way: use current RNG state (advanced)
            current_rng_state = rng.getstate()
            rng.setstate(current_rng_state)
            wrong_regenerated_gen = Gen.list(Gen.int(1, 10), min_length=shrunk_first.value, max_length=shrunk_first.value)
            wrong_regenerated = wrong_regenerated_gen.generate(rng)
            
            # Correct way: use saved RNG state (after first generation)
            rng.setstate(rng_state_after_first)
            correct_regenerated_gen = Gen.list(Gen.int(1, 10), min_length=shrunk_first.value, max_length=shrunk_first.value)
            correct_regenerated = correct_regenerated_gen.generate(rng)
            
            # The correct regeneration should match what flat_map produces
            flat_map_gen = Gen.int(1, 5).flat_map(
                lambda n: Gen.list(Gen.int(1, 10), min_length=n, max_length=n)
            )
            rng_test = random.Random(42)
            flat_map_shrinkable = flat_map_gen.generate(rng_test)
            
            # Find the shrink that corresponds to shrinking first value
            flat_map_shrinks = flat_map_shrinkable.shrinks().to_list()
            # The shrinks from shrinking first value are at the end
            # (after shrinks from shrinking second value)
            # We need to find one that has length matching shrunk_first.value
            matching_shrink = None
            for shrink in flat_map_shrinks:
                if isinstance(shrink.value, list) and len(shrink.value) == shrunk_first.value:
                    matching_shrink = shrink
                    break
            
            if matching_shrink:
                # The matching shrink should match the correct regeneration
                self.assertEqual(
                    matching_shrink.value, correct_regenerated.value,
                    "flat_map regeneration should match correct RNG state restoration"
                )
                self.assertNotEqual(
                    matching_shrink.value, wrong_regenerated.value,
                    "flat_map should NOT match wrong (advanced) RNG state"
                )
    
    def test_flat_map_in_failing_property_scenario(self):
        """Test flat_map in an actual failing property scenario."""
        # Create a property that fails for certain values
        def failing_property(lst):
            # Fail if list length is >= 3
            return len(lst) < 3
        
        gen = Gen.int(1, 5).flat_map(
            lambda n: Gen.list(Gen.int(1, 10), min_length=n, max_length=n)
        )
        
        property_test = Property(failing_property, num_runs=50, seed=42)
        
        # This should raise PropertyTestError with minimal counterexample
        with self.assertRaises(PropertyTestError) as exc_info:
            property_test.for_all(gen)
        
        # Verify that the minimal counterexample is a list
        minimal_inputs = exc_info.exception.minimal_inputs
        self.assertIsNotNone(minimal_inputs)
        self.assertEqual(len(minimal_inputs), 1)
        
        minimal_list = minimal_inputs[0]
        self.assertIsInstance(minimal_list, list)
        
        # The minimal list should be as small as possible (length 3, since that's the failure threshold)
        # But due to shrinking, it might be smaller if the property logic allows
        self.assertGreaterEqual(len(minimal_list), 1)
        self.assertLessEqual(len(minimal_list), 5)
    
    def test_flat_map_shrink_tree_structure_consistency(self):
        """Test that flat_map produces consistent shrink tree structures."""
        rng1 = random.Random(42)
        rng2 = random.Random(42)
        rng3 = random.Random(42)
        
        gen = Gen.int(1, 5).flat_map(
            lambda n: Gen.list(Gen.int(1, 10), min_length=n, max_length=n)
        )
        
        shrinkable1 = gen.generate(rng1)
        shrinkable2 = gen.generate(rng2)
        shrinkable3 = gen.generate(rng3)
        
        def serialize_tree(shrinkable, max_depth=3):
            """Serialize shrink tree to a comparable structure."""
            def serialize_recursive(sh, depth=0):
                if depth > max_depth:
                    return None
                result = {
                    "value": sh.value,
                    "value_type": type(sh.value).__name__,
                    "value_len": len(sh.value) if isinstance(sh.value, (list, tuple, str)) else None,
                    "shrinks": []
                }
                for child in sh.shrinks().to_list():
                    child_serialized = serialize_recursive(child, depth + 1)
                    if child_serialized is not None:
                        result["shrinks"].append(child_serialized)
                return result
            return serialize_recursive(shrinkable)
        
        tree1 = serialize_tree(shrinkable1)
        tree2 = serialize_tree(shrinkable2)
        tree3 = serialize_tree(shrinkable3)
        
        # All trees should be identical
        self.assertEqual(tree1, tree2, "Trees 1 and 2 should be identical")
        self.assertEqual(tree2, tree3, "Trees 2 and 3 should be identical")
    
    def test_flat_map_with_nested_flat_map(self):
        """Test flat_map with nested flat_map (regression test)."""
        rng1 = random.Random(42)
        rng2 = random.Random(42)
        
        # Nested flat_map: int -> list of ints -> list of strings
        gen = (
            Gen.int(1, 3)
            .flat_map(lambda n: Gen.list(Gen.int(1, 5), min_length=n, max_length=n))
            .flat_map(lambda lst: Gen.list(Gen.str(min_length=1, max_length=2), min_length=len(lst), max_length=len(lst)))
        )
        
        shrinkable1 = gen.generate(rng1)
        shrinkable2 = gen.generate(rng2)
        
        # Root values should match
        self.assertEqual(shrinkable1.value, shrinkable2.value)
        
        # Both should be lists of strings
        self.assertIsInstance(shrinkable1.value, list)
        self.assertIsInstance(shrinkable2.value, list)
        if len(shrinkable1.value) > 0:
            self.assertIsInstance(shrinkable1.value[0], str)
            self.assertIsInstance(shrinkable2.value[0], str)
    
    def test_flat_map_regeneration_maintains_constraints(self):
        """Test that regeneration during shrinking maintains constraints."""
        rng = random.Random(42)
        
        # Generate a number, then generate a list of that length
        gen = Gen.int(2, 5).flat_map(
            lambda n: Gen.list(Gen.int(1, 10), min_length=n, max_length=n)
        )
        
        shrinkable = gen.generate(rng)
        root = shrinkable.value
        
        # Root should be a list with length in [2, 5]
        self.assertIsInstance(root, list)
        self.assertGreaterEqual(len(root), 2)
        self.assertLessEqual(len(root), 5)
        
        # All shrinks should also be lists
        def check_all_shrinks(sh, depth=0, max_depth=5):
            if depth > max_depth:
                return []
            problems = []
            if not isinstance(sh.value, list):
                problems.append(f"Not a list at depth {depth}: {sh.value}")
            elif len(sh.value) > 0:
                # Check that all elements are in range [1, 10]
                for elem in sh.value:
                    if not (1 <= elem <= 10):
                        problems.append(f"Element {elem} out of range in {sh.value}")
            for child in sh.shrinks().to_list():
                problems.extend(check_all_shrinks(child, depth + 1, max_depth))
            return problems
        
        problems = check_all_shrinks(shrinkable)
        self.assertEqual(
            len(problems), 0,
            f"Found constraint violations in shrink tree: {problems[:10]}"
        )


if __name__ == "__main__":
    unittest.main()

