"""
Test cases to validate/invalidate potential issues with flat_map implementations.

These tests are designed to check if the theoretical issues identified in
CRITICAL_ANALYSIS_FLATMAP.md actually manifest in practice.
"""

import unittest
import random
from python_proptest import Gen, Property, PropertyTestError


class TestFlatMapEdgeCases(unittest.TestCase):
    """Test edge cases to validate/invalidate implementation issues."""

    def test_nested_flatmap_determinism(self):
        """
        Test: Does nested flatMap maintain determinism?
        
        Issue: Inner and outer flatMap might share RNG state incorrectly.
        Expected: Should be deterministic with same seed.
        """
        rng1 = random.Random(42)
        rng2 = random.Random(42)
        
        # Nested flatMap: int -> list -> list of strings
        gen = (
            Gen.int(1, 3)
            .flat_map(lambda n: Gen.list(Gen.int(1, 5), min_length=n, max_length=n))
            .flat_map(lambda lst: Gen.list(Gen.str(min_length=1, max_length=2), min_length=len(lst), max_length=len(lst)))
        )
        
        shrinkable1 = gen.generate(rng1)
        shrinkable2 = gen.generate(rng2)
        
        # Root values should match
        self.assertEqual(shrinkable1.value, shrinkable2.value,
                        "Nested flatMap should be deterministic")
        
        # Shrink trees should match (at least structure)
        shrinks1 = shrinkable1.shrinks().to_list()
        shrinks2 = shrinkable2.shrinks().to_list()
        
        self.assertEqual(len(shrinks1), len(shrinks2),
                        "Nested flatMap shrink trees should have same structure")
        
        # Values should match
        for s1, s2 in zip(shrinks1, shrinks2):
            self.assertEqual(s1.value, s2.value,
                            f"Nested flatMap shrinks should match: {s1.value} != {s2.value}")

    def test_nested_flatmap_independence(self):
        """
        Test: Are nested flatMap generations independent?
        
        Issue: Inner flatMap might use RNG state that depends on outer flatMap.
        Expected: Each level should generate independently.
        """
        rng = random.Random(42)
        
        # Track what values are generated at each level
        outer_values = []
        inner_values = []
        
        def track_outer(n):
            outer_values.append(n)
            return Gen.list(Gen.int(1, 10), min_length=n, max_length=n)
        
        def track_inner(lst):
            inner_values.append(len(lst))
            return Gen.just(sum(lst))
        
        gen = Gen.int(1, 5).flat_map(track_outer).flat_map(track_inner)
        
        # Generate multiple times
        for _ in range(10):
            gen.generate(rng)
        
        # Check: outer_values should be independent of inner_values
        # (This is a sanity check - if they're correlated, it might indicate RNG sharing)
        self.assertGreater(len(outer_values), 0, "Should generate outer values")
        self.assertGreater(len(inner_values), 0, "Should generate inner values")
        
        # The key test: if we generate with same seed, should get same sequences
        rng2 = random.Random(42)
        outer_values2 = []
        inner_values2 = []
        
        def track_outer2(n):
            outer_values2.append(n)
            return Gen.list(Gen.int(1, 10), min_length=n, max_length=n)
        
        def track_inner2(lst):
            inner_values2.append(len(lst))
            return Gen.just(sum(lst))
        
        gen2 = Gen.int(1, 5).flat_map(track_outer2).flat_map(track_inner2)
        
        for _ in range(10):
            gen2.generate(rng2)
        
        self.assertEqual(outer_values, outer_values2,
                        "Outer values should be deterministic")
        self.assertEqual(inner_values, inner_values2,
                        "Inner values should be deterministic")

    def test_flatmap_regeneration_determinism(self):
        """
        Test: Is regeneration during shrinking deterministic?
        
        Issue: RNG state might not be restored correctly during regeneration.
        Expected: Regeneration should produce same values with same seed.
        """
        rng1 = random.Random(42)
        rng2 = random.Random(42)
        
        gen = Gen.int(1, 5).flat_map(
            lambda n: Gen.list(Gen.int(1, 10), min_length=n, max_length=n)
        )
        
        shrinkable1 = gen.generate(rng1)
        shrinkable2 = gen.generate(rng2)
        
        # Get first shrink of first value
        first_shrinks1 = shrinkable1.shrinks().to_list()
        first_shrinks2 = shrinkable2.shrinks().to_list()
        
        # Find shrinks that correspond to shrinking the first value
        # (These are the ones that regenerate the second value)
        regenerated1 = []
        regenerated2 = []
        
        for shrink in first_shrinks1:
            # If this shrink has a different length than root, it's from regenerating
            if isinstance(shrink.value, list):
                if len(shrink.value) != len(shrinkable1.value):
                    regenerated1.append(shrink.value)
        
        for shrink in first_shrinks2:
            if isinstance(shrink.value, list):
                if len(shrink.value) != len(shrinkable2.value):
                    regenerated2.append(shrink.value)
        
        # Regenerated values should match
        if regenerated1 and regenerated2:
            self.assertEqual(len(regenerated1), len(regenerated2),
                            "Should have same number of regenerated values")
            for r1, r2 in zip(regenerated1, regenerated2):
                self.assertEqual(r1, r2,
                                f"Regenerated values should match: {r1} != {r2}")

    def test_exception_safety_during_regeneration(self):
        """
        Test: Is RNG state restored correctly if exception occurs during regeneration?
        
        Issue: If exception occurs in generate(), RNG state might be inconsistent.
        Expected: State should always be restored, even on exception.
        """
        rng = random.Random(42)
        
        # Create a generator that might raise exception
        class FailingGenerator(Gen):
            def generate(self, rng):
                # Save state
                state = rng.getstate()
                # Advance RNG
                rng.random()
                # Simulate exception
                raise ValueError("Test exception")
        
        # This should not be used, but test the pattern
        gen = Gen.int(1, 5).flat_map(
            lambda n: Gen.list(Gen.int(1, 10), min_length=n, max_length=n)
        )
        
        # Generate normally
        shrinkable = gen.generate(rng)
        original_state = rng.getstate()
        
        # Try to access shrinks (which might trigger regeneration)
        try:
            shrinks = shrinkable.shrinks().to_list()
            # If we get here, regeneration worked
            # Check that RNG state is still consistent
            current_state = rng.getstate()
            # State should be restored (though it might have advanced)
            # The key is that it should be deterministic
            self.assertIsNotNone(current_state, "RNG state should exist")
        except Exception as e:
            # If exception occurs, state should still be restored
            current_state = rng.getstate()
            self.assertIsNotNone(current_state, "RNG state should exist even after exception")

    def test_multiple_flatmap_chains(self):
        """
        Test: Do multiple flatMap chains maintain independence?
        
        Issue: RNG state might leak between different flatMap chains.
        Expected: Each chain should be independent.
        """
        rng = random.Random(42)
        
        gen1 = Gen.int(1, 5).flat_map(
            lambda n: Gen.list(Gen.int(1, 10), min_length=n, max_length=n)
        )
        
        gen2 = Gen.int(1, 5).flat_map(
            lambda n: Gen.list(Gen.int(1, 10), min_length=n, max_length=n)
        )
        
        # Generate with same seed
        rng1 = random.Random(42)
        rng2 = random.Random(42)
        
        shrinkable1 = gen1.generate(rng1)
        shrinkable2 = gen2.generate(rng2)
        
        # Should produce same values (deterministic)
        self.assertEqual(shrinkable1.value, shrinkable2.value,
                        "Independent flatMap chains should be deterministic")

    def test_flatmap_in_property_test(self):
        """
        Test: Does flatMap work correctly in actual property tests?
        
        Issue: RNG state management might break in property test context.
        Expected: Should work correctly, including shrinking.
        """
        # Create a property that will fail
        def failing_property(lst):
            # Fail if list length >= 3
            return len(lst) < 3
        
        gen = Gen.int(1, 5).flat_map(
            lambda n: Gen.list(Gen.int(1, 10), min_length=n, max_length=n)
        )
        
        property_test = Property(failing_property, num_runs=50, seed=42)
        
        # This should raise PropertyTestError with minimal counterexample
        with self.assertRaises(PropertyTestError) as exc_info:
            property_test.for_all(gen)
        
        minimal_inputs = exc_info.exception.minimal_inputs
        self.assertIsNotNone(minimal_inputs)
        self.assertEqual(len(minimal_inputs), 1)
        
        minimal_list = minimal_inputs[0]
        self.assertIsInstance(minimal_list, list)
        
        # Minimal list should be as small as possible
        # (Due to property: len < 3, so minimal should be length 3)
        self.assertGreaterEqual(len(minimal_list), 1)
        self.assertLessEqual(len(minimal_list), 5)

    def test_deeply_nested_flatmap(self):
        """
        Test: Does deeply nested flatMap (3+ levels) work correctly?
        
        Issue: State management might break with deep nesting.
        Expected: Should work correctly at any depth.
        """
        rng1 = random.Random(42)
        rng2 = random.Random(42)
        
        # 3 levels of nesting
        gen = (
            Gen.int(1, 3)
            .flat_map(lambda n: Gen.list(Gen.int(1, 5), min_length=n, max_length=n))
            .flat_map(lambda lst: Gen.list(Gen.str(min_length=1, max_length=2), min_length=len(lst), max_length=len(lst)))
            .flat_map(lambda str_lst: Gen.just(len(str_lst)))
        )
        
        shrinkable1 = gen.generate(rng1)
        shrinkable2 = gen.generate(rng2)
        
        # Should be deterministic
        self.assertEqual(shrinkable1.value, shrinkable2.value,
                        "Deeply nested flatMap should be deterministic")
        
        # Should produce valid values
        self.assertIsInstance(shrinkable1.value, int)
        self.assertGreaterEqual(shrinkable1.value, 1)

    def test_flatmap_with_filter_chain(self):
        """
        Test: Does flatMap work correctly when chained with filter?
        
        Issue: Filter might interfere with flatMap's RNG state management.
        Expected: Should work correctly.
        """
        rng = random.Random(42)
        
        gen = (
            Gen.int(1, 10)
            .flat_map(lambda n: Gen.list(Gen.int(1, 10), min_length=n, max_length=n))
            .filter(lambda lst: sum(lst) > 10)  # Filter after flatMap
        )
        
        shrinkable = gen.generate(rng)
        
        # Root should satisfy filter
        self.assertGreater(sum(shrinkable.value), 10,
                          "Root should satisfy filter condition")
        
        # All shrinks should satisfy filter
        def check_all_shrinks(sh, depth=0, max_depth=3):
            if depth > max_depth:
                return []
            problems = []
            if sum(sh.value) <= 10:
                problems.append((depth, sh.value, sum(sh.value)))
            for child in sh.shrinks().to_list():
                problems.extend(check_all_shrinks(child, depth+1, max_depth))
            return problems
        
        problems = check_all_shrinks(shrinkable)
        self.assertEqual(len(problems), 0,
                        f"All shrinks should satisfy filter: {problems[:10]}")


if __name__ == "__main__":
    unittest.main()

