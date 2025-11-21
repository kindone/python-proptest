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


class TestComplexCombinatorChains(unittest.TestCase):
    """Test complex chains of multiple combinators to ensure conditions are maintained."""

    def test_filter_map_filter_chain(self):
        """Test filter -> map -> filter chain maintains all conditions."""
        rng = random.Random(42)
        gen = (
            Gen.int(1, 100)
            .filter(lambda x: x % 2 == 0)      # Even numbers
            .map(lambda x: x * 3)              # Multiply by 3
            .filter(lambda x: x % 4 == 0)      # Must be divisible by 4
        )
        
        for _ in range(20):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must satisfy: (even * 3) % 4 == 0
            # This means original must be divisible by 4 (since 3*4=12, 3*8=24, etc.)
            self.assertTrue(
                root % 4 == 0,
                f"Root {root} must be divisible by 4"
            )
            # Root must be divisible by 3 (since it's original * 3)
            self.assertTrue(
                root % 3 == 0,
                f"Root {root} must be divisible by 3"
            )
            
            # All shrinks must satisfy both conditions
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                if not (sh.value % 4 == 0 and sh.value % 3 == 0):
                    problems.append((depth, sh.value))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found values that don't satisfy filter->map->filter conditions: {problems[:10]}"
            )

    def test_map_filter_map_chain(self):
        """Test map -> filter -> map chain maintains all conditions."""
        rng = random.Random(42)
        gen = (
            Gen.int(1, 50)
            .map(lambda x: x * 2)              # Double it
            .filter(lambda x: x % 3 == 0)      # Must be divisible by 3
            .map(lambda x: x + 10)            # Add 10
        )
        
        for _ in range(20):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must satisfy: ((original * 2) % 3 == 0) + 10
            # So (root - 10) must be divisible by 3 and even
            adjusted = root - 10
            self.assertTrue(
                adjusted % 3 == 0,
                f"Root {root} -> adjusted {adjusted} must be divisible by 3"
            )
            self.assertTrue(
                adjusted % 2 == 0,
                f"Root {root} -> adjusted {adjusted} must be even"
            )
            
            # All shrinks must satisfy the chain
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                adj = sh.value - 10
                if not (adj % 3 == 0 and adj % 2 == 0):
                    problems.append((depth, sh.value, adj))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found values that don't satisfy map->filter->map conditions: {problems[:10]}"
            )

    def test_triple_filter_chain(self):
        """Test three filters in sequence maintain all conditions."""
        rng = random.Random(42)
        gen = (
            Gen.int(1, 200)
            .filter(lambda x: x % 2 == 0)      # Even
            .filter(lambda x: x % 5 == 0)      # Divisible by 5
            .filter(lambda x: x % 7 == 0)      # Divisible by 7
        )
        
        for _ in range(20):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must be divisible by 2, 5, and 7 (i.e., by 70)
            self.assertTrue(root % 2 == 0, f"Root {root} must be even")
            self.assertTrue(root % 5 == 0, f"Root {root} must be divisible by 5")
            self.assertTrue(root % 7 == 0, f"Root {root} must be divisible by 7")
            self.assertTrue(root % 70 == 0, f"Root {root} must be divisible by 70")
            
            # All shrinks must satisfy all three filters
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                if not (sh.value % 2 == 0 and sh.value % 5 == 0 and sh.value % 7 == 0):
                    problems.append((depth, sh.value))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found values that don't satisfy all three filters: {problems[:10]}"
            )

    def test_triple_map_chain(self):
        """Test three maps in sequence maintain transformations."""
        rng = random.Random(42)
        gen = (
            Gen.int(1, 20)
            .map(lambda x: x * 2)              # Double
            .map(lambda x: x + 5)              # Add 5
            .map(lambda x: x * 3)              # Triple
        )
        
        for _ in range(20):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must be: ((original * 2) + 5) * 3
            # So (root / 3 - 5) / 2 should be the original integer
            back = (root / 3 - 5) / 2
            self.assertAlmostEqual(
                back, int(back), places=5,
                msg=f"Root {root} should be derivable from integer original"
            )
            
            # All shrinks must maintain the transformation
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                back_val = (sh.value / 3 - 5) / 2
                if abs(back_val - int(back_val)) > 0.001:
                    problems.append((depth, sh.value, back_val))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found values that don't maintain triple map transformation: {problems[:10]}"
            )

    def test_filter_map_filter_map_chain(self):
        """Test alternating filter and map chain maintains all conditions."""
        rng = random.Random(42)
        gen = (
            Gen.int(1, 100)
            .filter(lambda x: x % 2 == 0)      # Even
            .map(lambda x: x * 2)              # Double -> multiple of 4
            .filter(lambda x: x % 3 == 0)      # Divisible by 3
            .map(lambda x: x // 3)             # Divide by 3
        )
        
        for _ in range(20):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must satisfy: ((even * 2) % 3 == 0) // 3
            # So root * 3 must be multiple of 4 and divisible by 3
            back = root * 3
            self.assertTrue(
                back % 4 == 0,
                f"Root {root} -> {back} must be multiple of 4"
            )
            self.assertTrue(
                back % 3 == 0,
                f"Root {root} -> {back} must be divisible by 3"
            )
            
            # All shrinks must maintain the chain
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
                f"Found values that don't maintain filter->map->filter->map chain: {problems[:10]}"
            )

    def test_flatmap_with_filter(self):
        """Test flatmap combined with filter maintains conditions."""
        rng = random.Random(42)
        # Generate a number, then generate a list of that length, filter to keep only lists with sum > 20
        gen = (
            Gen.int(2, 5)
            .flat_map(lambda n: Gen.list(Gen.int(1, 10), min_length=n, max_length=n))
            .filter(lambda lst: sum(lst) > 20)
        )
        
        for _ in range(20):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must be a list with sum > 20
            self.assertIsInstance(root, list, f"Root {root} must be a list")
            self.assertGreater(
                sum(root), 20,
                f"Root {root} sum {sum(root)} must be > 20"
            )
            
            # All shrinks must be lists with sum > 20
            def check_all_shrinks(sh, depth=0, max_depth=3):
                if depth > max_depth:
                    return []
                problems = []
                if not isinstance(sh.value, list):
                    problems.append((depth, sh.value, "not a list"))
                elif sum(sh.value) <= 20:
                    problems.append((depth, sh.value, f"sum={sum(sh.value)}"))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found values that don't satisfy flatmap+filter conditions: {problems[:10]}"
            )

    def test_flatmap_with_map(self):
        """Test flatmap combined with map maintains transformations."""
        rng = random.Random(42)
        # Generate a number, then generate a list, then map to sum
        gen = (
            Gen.int(1, 5)
            .flat_map(lambda n: Gen.list(Gen.int(1, 10), min_length=n, max_length=n))
            .map(lambda lst: sum(lst))
        )
        
        for _ in range(20):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must be an integer (sum of list)
            self.assertIsInstance(root, int, f"Root {root} must be an int")
            # Sum should be at least the length (all elements >= 1)
            self.assertGreaterEqual(root, 1, f"Root {root} must be >= 1")
            
            # All shrinks must be integers
            def check_all_shrinks(sh, depth=0, max_depth=3):
                if depth > max_depth:
                    return []
                problems = []
                if not isinstance(sh.value, int):
                    problems.append((depth, sh.value, type(sh.value)))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found non-integer values in flatmap+map chain: {problems[:10]}"
            )

    def test_flatmap_filter_map_chain(self):
        """Test flatmap -> filter -> map chain maintains all conditions."""
        rng = random.Random(42)
        gen = (
            Gen.int(2, 4)
            .flat_map(lambda n: Gen.list(Gen.int(1, 10), min_length=n, max_length=n))
            .filter(lambda lst: len(lst) >= 3)  # At least 3 elements
            .map(lambda lst: len(lst) * 10)    # Map to length * 10
        )
        
        for _ in range(20):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must be >= 30 (length >= 3, so length * 10 >= 30)
            self.assertGreaterEqual(
                root, 30,
                f"Root {root} must be >= 30 (length * 10, length >= 3)"
            )
            # Root must be divisible by 10
            self.assertTrue(
                root % 10 == 0,
                f"Root {root} must be divisible by 10"
            )
            
            # All shrinks must satisfy conditions
            def check_all_shrinks(sh, depth=0, max_depth=3):
                if depth > max_depth:
                    return []
                problems = []
                if not (sh.value >= 30 and sh.value % 10 == 0):
                    problems.append((depth, sh.value))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found values that don't satisfy flatmap->filter->map chain: {problems[:10]}"
            )

    def test_one_of_with_filter(self):
        """Test one_of combined with filter maintains conditions."""
        rng = random.Random(42)
        gen = (
            Gen.one_of(
                Gen.int(1, 50),
                Gen.int(51, 100),
            )
            .filter(lambda x: x % 2 == 0)  # Even numbers only
        )
        
        for _ in range(20):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must be even and in range [1, 100]
            self.assertTrue(
                root % 2 == 0,
                f"Root {root} must be even"
            )
            self.assertGreaterEqual(root, 1, f"Root {root} must be >= 1")
            self.assertLessEqual(root, 100, f"Root {root} must be <= 100")
            
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
                f"Found odd values in one_of+filter chain: {problems[:10]}"
            )

    def test_one_of_with_map(self):
        """Test one_of combined with map maintains transformations."""
        rng = random.Random(42)
        gen = (
            Gen.one_of(
                Gen.int(1, 10),
                Gen.int(11, 20),
            )
            .map(lambda x: x * 2)  # Double all values
        )
        
        for _ in range(20):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must be even and in range [2, 40]
            self.assertTrue(
                root % 2 == 0,
                f"Root {root} must be even (original * 2)"
            )
            self.assertGreaterEqual(root, 2, f"Root {root} must be >= 2")
            self.assertLessEqual(root, 40, f"Root {root} must be <= 40")
            
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
                f"Found odd values in one_of+map chain: {problems[:10]}"
            )

    def test_one_of_filter_map_chain(self):
        """Test one_of -> filter -> map chain maintains all conditions."""
        rng = random.Random(42)
        gen = (
            Gen.one_of(
                Gen.int(1, 30),
                Gen.int(31, 60),
            )
            .filter(lambda x: x % 3 == 0)  # Divisible by 3
            .map(lambda x: x * 2)          # Double
        )
        
        for _ in range(20):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must be divisible by 6 (divisible by 3 * 2)
            self.assertTrue(
                root % 6 == 0,
                f"Root {root} must be divisible by 6"
            )
            # Root must be in range [6, 120] (original in [1, 60], * 2)
            self.assertGreaterEqual(root, 6, f"Root {root} must be >= 6")
            self.assertLessEqual(root, 120, f"Root {root} must be <= 120")
            
            # All shrinks must be divisible by 6
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                if sh.value % 6 != 0:
                    problems.append((depth, sh.value))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found values not divisible by 6 in one_of->filter->map chain: {problems[:10]}"
            )

    def test_element_of_with_filter(self):
        """Test element_of combined with filter maintains conditions."""
        rng = random.Random(42)
        gen = (
            Gen.element_of(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
            .filter(lambda x: x % 2 == 0)  # Even numbers only
        )
        
        for _ in range(20):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must be even and in the original set
            self.assertTrue(
                root % 2 == 0,
                f"Root {root} must be even"
            )
            self.assertIn(root, [2, 4, 6, 8, 10], f"Root {root} must be in [2, 4, 6, 8, 10]")
            
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
                f"Found odd values in element_of+filter chain: {problems[:10]}"
            )

    def test_element_of_with_map(self):
        """Test element_of combined with map maintains transformations."""
        rng = random.Random(42)
        gen = (
            Gen.element_of(1, 2, 3, 4, 5)
            .map(lambda x: x * 10)  # Multiply by 10
        )
        
        for _ in range(20):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must be in [10, 20, 30, 40, 50]
            self.assertIn(root, [10, 20, 30, 40, 50], f"Root {root} must be in [10, 20, 30, 40, 50]")
            # Root must be divisible by 10
            self.assertTrue(root % 10 == 0, f"Root {root} must be divisible by 10")
            
            # All shrinks must be divisible by 10
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                if sh.value % 10 != 0:
                    problems.append((depth, sh.value))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found values not divisible by 10 in element_of+map chain: {problems[:10]}"
            )

    def test_very_deep_chain(self):
        """Test a very deep chain of filters and maps maintains all conditions."""
        rng = random.Random(42)
        gen = (
            Gen.int(1, 200)
            .filter(lambda x: x % 2 == 0)      # Even
            .map(lambda x: x * 2)              # * 2 -> multiple of 4
            .filter(lambda x: x % 3 == 0)      # Divisible by 3
            .map(lambda x: x // 3)             # // 3
            .filter(lambda x: x > 10)          # > 10
            .map(lambda x: x + 5)              # + 5
        )
        
        for _ in range(20):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Work backwards: root - 5 must be > 10, so root > 15
            self.assertGreater(
                root, 15,
                f"Root {root} must be > 15 (after +5, original > 10)"
            )
            
            # All shrinks must satisfy: (value - 5) > 10, so value > 15
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                if sh.value <= 15:
                    problems.append((depth, sh.value))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found values <= 15 in deep chain: {problems[:10]}"
            )

    def test_list_generator_with_filter_map(self):
        """Test list generator with filter and map maintains conditions."""
        rng = random.Random(42)
        gen = (
            Gen.list(Gen.int(1, 20), min_length=3, max_length=10)
            .filter(lambda lst: len(lst) >= 5)  # At least 5 elements
            .map(lambda lst: [x * 2 for x in lst])  # Double all elements
        )
        
        for _ in range(20):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must be a list with at least 5 elements, all even
            self.assertIsInstance(root, list, f"Root {root} must be a list")
            self.assertGreaterEqual(
                len(root), 5,
                f"Root list {root} must have at least 5 elements"
            )
            for val in root:
                self.assertTrue(
                    val % 2 == 0,
                    f"All elements in {root} must be even"
                )
            
            # All shrinks must be lists with at least 5 even elements
            def check_all_shrinks(sh, depth=0, max_depth=3):
                if depth > max_depth:
                    return []
                problems = []
                if not isinstance(sh.value, list):
                    problems.append((depth, sh.value, "not a list"))
                elif len(sh.value) < 5:
                    problems.append((depth, sh.value, f"length={len(sh.value)}"))
                else:
                    for val in sh.value:
                        if val % 2 != 0:
                            problems.append((depth, sh.value, f"odd value: {val}"))
                            break
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found values that don't satisfy list+filter+map conditions: {problems[:10]}"
            )

    def test_string_generator_with_filter_map(self):
        """Test string generator with filter and map maintains conditions."""
        rng = random.Random(42)
        gen = (
            Gen.str(min_length=5, max_length=15)
            .filter(lambda s: len(s) >= 8)  # At least 8 characters
            .map(lambda s: s.upper())        # Convert to uppercase
        )
        
        for _ in range(20):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must be uppercase string with at least 8 characters
            self.assertIsInstance(root, str, f"Root {root} must be a string")
            self.assertGreaterEqual(
                len(root), 8,
                f"Root string '{root}' must have at least 8 characters"
            )
            self.assertEqual(
                root, root.upper(),
                f"Root string '{root}' must be uppercase"
            )
            
            # All shrinks must be uppercase strings with at least 8 characters
            def check_all_shrinks(sh, depth=0, max_depth=3):
                if depth > max_depth:
                    return []
                problems = []
                if not isinstance(sh.value, str):
                    problems.append((depth, sh.value, "not a string"))
                elif len(sh.value) < 8:
                    problems.append((depth, sh.value, f"length={len(sh.value)}"))
                elif sh.value != sh.value.upper():
                    problems.append((depth, sh.value, "not uppercase"))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found values that don't satisfy string+filter+map conditions: {problems[:10]}"
            )


if __name__ == "__main__":
    unittest.main()

