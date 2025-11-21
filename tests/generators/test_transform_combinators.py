"""
Tests for transform combinators (filter, map, flat_map) to ensure
conditions are maintained throughout the shrink tree.
"""

import unittest
from python_proptest import Gen
import random


class TestTransformCombinators(unittest.TestCase):
    """Test that filter/map/flatmap maintain conditions in shrink trees."""

    def test_filter_maintains_predicate(self):
        """Test that filter maintains predicate throughout shrink tree."""
        rng = random.Random(42)
        gen = Gen.int(1, 100).filter(lambda x: x % 2 == 0)
        
        # Generate multiple times to test different values
        for _ in range(20):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must satisfy predicate
            self.assertTrue(
                root % 2 == 0,
                f"Root value {root} does not satisfy filter predicate (should be even)"
            )
            
            # All shrinks must satisfy predicate
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                if sh.value % 2 != 0:
                    problems.append((depth, sh.value))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found values in shrink tree that don't satisfy filter: {problems[:10]}"
            )

    def test_map_maintains_transformation(self):
        """Test that map correctly transforms values throughout shrink tree."""
        rng = random.Random(42)
        gen = Gen.int(1, 50).map(lambda x: x * 2)
        
        for _ in range(20):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must be even (original * 2)
            self.assertTrue(
                root % 2 == 0,
                f"Root value {root} is not even (should be original * 2)"
            )
            
            # All shrinks must be even
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                if sh.value % 2 != 0:
                    problems.append((depth, sh.value))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found odd values in mapped shrink tree: {problems[:10]}"
            )

    def test_filter_then_map_maintains_conditions(self):
        """Test that filter then map maintains both conditions."""
        rng = random.Random(42)
        gen = Gen.int(1, 100).filter(lambda x: x % 2 == 0).map(lambda x: x * 2)
        
        for _ in range(20):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must be multiple of 4 (even * 2)
            self.assertTrue(
                root % 4 == 0,
                f"Root value {root} is not a multiple of 4 (should be even * 2)"
            )
            
            # All shrinks must be multiples of 4
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                if sh.value % 4 != 0:
                    orig = sh.value // 2
                    problems.append((depth, sh.value, orig, orig % 2 == 0))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            if problems:
                self.fail(
                    f"Found values in shrink tree that are not multiples of 4: "
                    f"{problems[:10]}. Each value should be (even number) * 2."
                )

    def test_map_then_filter_maintains_conditions(self):
        """Test that map then filter maintains conditions."""
        rng = random.Random(42)
        # Map to squares, then filter to keep only values > 100
        gen = Gen.int(1, 20).map(lambda x: x * x).filter(lambda x: x > 100)
        
        for _ in range(20):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must be > 100 and a perfect square
            self.assertGreater(
                root, 100,
                f"Root value {root} is not > 100"
            )
            
            # All shrinks must be > 100
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                if sh.value <= 100:
                    problems.append((depth, sh.value))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found values in shrink tree that are not > 100: {problems[:10]}"
            )

    def test_multiple_filters_maintain_conditions(self):
        """Test that multiple filters maintain all conditions."""
        rng = random.Random(42)
        gen = (
            Gen.int(1, 100)
            .filter(lambda x: x % 2 == 0)  # Even
            .filter(lambda x: x % 3 == 0)  # Divisible by 3
            .filter(lambda x: x > 10)      # Greater than 10
        )
        
        for _ in range(20):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must satisfy all conditions
            self.assertTrue(root % 2 == 0, f"Root {root} is not even")
            self.assertTrue(root % 3 == 0, f"Root {root} is not divisible by 3")
            self.assertGreater(root, 10, f"Root {root} is not > 10")
            
            # All shrinks must satisfy all conditions
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                if not (sh.value % 2 == 0 and sh.value % 3 == 0 and sh.value > 10):
                    problems.append((depth, sh.value))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found values in shrink tree that don't satisfy all filters: {problems[:10]}"
            )

    def test_multiple_maps_maintain_transformations(self):
        """Test that multiple maps maintain transformations."""
        rng = random.Random(42)
        gen = Gen.int(1, 10).map(lambda x: x * 2).map(lambda x: x + 1)
        
        for _ in range(20):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must be odd (original * 2 + 1)
            self.assertTrue(
                root % 2 == 1,
                f"Root value {root} is not odd (should be (original * 2) + 1)"
            )
            
            # All shrinks must be odd
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                if sh.value % 2 == 0:
                    problems.append((depth, sh.value))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found even values in shrink tree: {problems[:10]}"
            )

    def test_flatmap_maintains_conditions(self):
        """Test that flatmap maintains conditions."""
        rng = random.Random(42)
        # Generate a number, then generate a list of that length
        gen = Gen.int(1, 5).flat_map(lambda n: Gen.list(Gen.int(1, 10), min_length=n, max_length=n))
        
        for _ in range(20):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must be a list
            self.assertIsInstance(root, list, f"Root {root} is not a list")
            
            # Root length should match the original number
            # (we can't directly check this, but we can check it's a valid list)
            self.assertGreater(len(root), 0, f"Root list {root} is empty")
            self.assertLessEqual(len(root), 5, f"Root list {root} is too long")
            
            # All shrinks must be lists
            def check_all_shrinks(sh, depth=0, max_depth=3):
                if depth > max_depth:
                    return []
                problems = []
                if not isinstance(sh.value, list):
                    problems.append((depth, sh.value, type(sh.value)))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found non-list values in shrink tree: {problems[:10]}"
            )

    def test_complex_chain_maintains_conditions(self):
        """Test that complex filter/map chains maintain all conditions."""
        rng = random.Random(42)
        gen = (
            Gen.int(1, 100)
            .filter(lambda x: x % 2 == 0)      # Even
            .map(lambda x: x * 2)              # Multiply by 2 -> multiple of 4
            .filter(lambda x: x % 3 == 0)      # Divisible by 3
            .map(lambda x: x // 3)             # Divide by 3
        )
        
        for _ in range(20):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must satisfy: (even * 2) % 3 == 0, then // 3
            # So root should be an integer
            self.assertIsInstance(root, int, f"Root {root} is not an int")
            
            # Work backwards: root * 3 should be multiple of 4 and divisible by 3
            back = root * 3
            self.assertTrue(
                back % 4 == 0,
                f"Root {root} -> {back} should be multiple of 4"
            )
            self.assertTrue(
                back % 3 == 0,
                f"Root {root} -> {back} should be divisible by 3"
            )
            
            # Check shrinks maintain the transformation chain
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                back_val = sh.value * 3
                if not (back_val % 4 == 0 and back_val % 3 == 0):
                    problems.append((depth, sh.value, back_val))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found values in shrink tree that don't maintain chain conditions: {problems[:10]}"
            )

    def test_regeneration_maintains_conditions(self):
        """Test that regenerating with same RNG state maintains conditions."""
        rng1 = random.Random(42)
        rng2 = random.Random(42)
        
        gen = Gen.int(1, 100).filter(lambda x: x % 2 == 0).map(lambda x: x * 2)
        
        shrinkable1 = gen.generate(rng1)
        shrinkable2 = gen.generate(rng2)
        
        # Roots should match
        self.assertEqual(shrinkable1.value, shrinkable2.value)
        
        # Both should be multiples of 4
        self.assertTrue(shrinkable1.value % 4 == 0)
        self.assertTrue(shrinkable2.value % 4 == 0)
        
        # Check that both shrink trees maintain conditions
        def check_shrinks(shrinkable):
            problems = []
            for sh in shrinkable.shrinks().to_list():
                if sh.value % 4 != 0:
                    problems.append(sh.value)
            return problems
        
        problems1 = check_shrinks(shrinkable1)
        problems2 = check_shrinks(shrinkable2)
        
        self.assertEqual(len(problems1), 0, f"First shrinkable has problems: {problems1}")
        self.assertEqual(len(problems2), 0, f"Second shrinkable has problems: {problems2}")


if __name__ == "__main__":
    unittest.main()

