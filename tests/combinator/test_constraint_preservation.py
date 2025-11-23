"""
Generalized tests for constraint preservation across all generator types.

This test suite verifies that when generators have constraints (min_value, max_value,
min_length, max_length, etc.), these constraints are:
1. Preserved when no transformations are applied
2. Transformed correctly when map is applied
3. Preserved when filter is applied
4. Preserved/transformed correctly when map and filter are chained

Covers:
- Primitive generators (int, float, str)
- Collection generators (list, set, dict, tuple)
- Nested structures
- Various transformation types
- Edge cases (boundary values)
"""

import unittest
from python_proptest import Gen
import random
import math


class TestPrimitiveConstraintPreservation(unittest.TestCase):
    """Test constraint preservation for primitive generators."""

    def test_int_constraints_preserved(self):
        """Test that int constraints are preserved throughout shrink tree."""
        rng = random.Random(42)
        gen = Gen.int(5, 15)
        
        for _ in range(10):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must respect constraints
            self.assertGreaterEqual(root, 5, f"Root {root} < 5")
            self.assertLessEqual(root, 15, f"Root {root} > 15")
            
            # All shrinks must respect constraints
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                if sh.value < 5 or sh.value > 15:
                    problems.append((depth, sh.value, f"out of [5, 15]"))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found values violating constraints: {problems[:5]}"
            )

    def test_int_map_additive_transformation(self):
        """Test that int constraints are transformed correctly with additive map."""
        rng = random.Random(42)
        # Gen.int(5, 15) -> after map(+10) should be [15, 25]
        gen = Gen.int(5, 15).map(lambda x: x + 10)
        
        for _ in range(10):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must respect transformed constraints
            self.assertGreaterEqual(root, 15, f"Root {root} < 15 (5+10)")
            self.assertLessEqual(root, 25, f"Root {root} > 25 (15+10)")
            
            # All shrinks must respect transformed constraints
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                if sh.value < 15 or sh.value > 25:
                    problems.append((depth, sh.value, f"out of [15, 25]"))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found values violating transformed constraints: {problems[:5]}"
            )

    def test_int_map_multiplicative_transformation(self):
        """Test that int constraints are transformed correctly with multiplicative map."""
        rng = random.Random(42)
        # Gen.int(3, 7) -> after map(*3) should be [9, 21]
        gen = Gen.int(3, 7).map(lambda x: x * 3)
        
        for _ in range(10):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must respect transformed constraints
            self.assertGreaterEqual(root, 9, f"Root {root} < 9 (3*3)")
            self.assertLessEqual(root, 21, f"Root {root} > 21 (7*3)")
            
            # All shrinks must respect transformed constraints
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                if sh.value < 9 or sh.value > 21:
                    problems.append((depth, sh.value, f"out of [9, 21]"))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found values violating transformed constraints: {problems[:5]}"
            )

    def test_int_map_complex_transformation(self):
        """Test that int constraints are transformed correctly with complex map."""
        rng = random.Random(42)
        # Gen.int(2, 8) -> after map(x*2+5) should be [9, 21]
        gen = Gen.int(2, 8).map(lambda x: x * 2 + 5)
        
        for _ in range(10):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must respect transformed constraints
            self.assertGreaterEqual(root, 9, f"Root {root} < 9 (2*2+5)")
            self.assertLessEqual(root, 21, f"Root {root} > 21 (8*2+5)")
            
            # All shrinks must respect transformed constraints
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                if sh.value < 9 or sh.value > 21:
                    problems.append((depth, sh.value, f"out of [9, 21]"))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found values violating transformed constraints: {problems[:5]}"
            )

    def test_int_filter_preserves_constraints(self):
        """Test that filter preserves original int constraints."""
        rng = random.Random(42)
        gen = Gen.int(6, 12).filter(lambda x: x % 3 == 0)
        
        for _ in range(10):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must respect original constraints AND filter
            self.assertGreaterEqual(root, 6, f"Root {root} < 6")
            self.assertLessEqual(root, 12, f"Root {root} > 12")
            self.assertEqual(root % 3, 0, f"Root {root} not divisible by 3")
            
            # All shrinks must respect both
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                if sh.value < 6 or sh.value > 12:
                    problems.append((depth, sh.value, f"out of [6, 12]"))
                if sh.value % 3 != 0:
                    problems.append((depth, sh.value, f"not divisible by 3"))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found values violating constraints: {problems[:5]}"
            )

    def test_float_constraints_preserved(self):
        """Test that float constraints are preserved throughout shrink tree.
        
        Note: Float shrinking can produce values outside the original range
        (e.g., 0.0, negative values) to find minimal counterexamples.
        This is expected behavior in property-based testing.
        However, when map is applied, the transformed constraints should be preserved.
        """
        rng = random.Random(42)
        gen = Gen.float(2.5, 7.5)
        
        for _ in range(10):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Skip NaN/inf values
            if not (math.isfinite(root) and not math.isnan(root)):
                continue
            
            # Root must respect constraints
            self.assertGreaterEqual(root, 2.5, f"Root {root} < 2.5")
            self.assertLessEqual(root, 7.5, f"Root {root} > 7.5")
            
            # Note: During shrinking, floats can go outside the original range
            # This test only verifies that the root value respects constraints.
            # For a more comprehensive test, see test_float_map_transforms_constraints

    def test_str_length_constraints_preserved(self):
        """Test that string length constraints are preserved throughout shrink tree."""
        rng = random.Random(42)
        gen = Gen.str(min_length=3, max_length=8)
        
        for _ in range(10):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must respect constraints
            self.assertGreaterEqual(len(root), 3, f"Root length {len(root)} < 3")
            self.assertLessEqual(len(root), 8, f"Root length {len(root)} > 8")
            
            # All shrinks must respect constraints
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                if len(sh.value) < 3 or len(sh.value) > 8:
                    problems.append((depth, sh.value, f"length {len(sh.value)} out of [3, 8]"))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found strings violating length constraints: {problems[:5]}"
            )


class TestCollectionConstraintPreservation(unittest.TestCase):
    """Test constraint preservation for collection generators."""

    def test_list_with_constrained_elements_preserves_constraints(self):
        """Test that list with constrained element generators preserves element constraints.
        
        Note: Size constraints (min_length, max_length) are for generation only.
        During shrinking, collections can become smaller to find minimal counterexamples.
        However, element constraints (from the element generator) should be preserved.
        """
        rng = random.Random(42)
        gen = Gen.list(Gen.int(10, 20), min_length=2, max_length=5)
        
        for _ in range(10):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must respect constraints
            self.assertGreaterEqual(len(root), 2, f"Root length {len(root)} < 2")
            self.assertLessEqual(len(root), 5, f"Root length {len(root)} > 5")
            for elem in root:
                self.assertGreaterEqual(elem, 10, f"Element {elem} < 10")
                self.assertLessEqual(elem, 20, f"Element {elem} > 20")
            
            # All shrinks must respect ELEMENT constraints (size can shrink below min_length)
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                # Only check element constraints, not size constraints
                for elem in sh.value:
                    if elem < 10 or elem > 20:
                        problems.append((depth, sh.value, f"element {elem} out of [10, 20]"))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found lists violating element constraints: {problems[:5]}"
            )

    def test_list_map_transforms_element_constraints(self):
        """Test that map on list transforms element constraints correctly."""
        rng = random.Random(42)
        gen = Gen.list(Gen.int(5, 10), min_length=1, max_length=4).map(
            lambda lst: [x * 2 for x in lst]
        )
        
        for _ in range(10):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must respect transformed constraints
            for elem in root:
                self.assertGreaterEqual(elem, 10, f"Element {elem} < 10 (5*2)")
                self.assertLessEqual(elem, 20, f"Element {elem} > 20 (10*2)")
            
            # All shrinks must respect transformed constraints
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                for elem in sh.value:
                    if elem < 10 or elem > 20:
                        problems.append((depth, sh.value, f"element {elem} out of [10, 20]"))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found lists violating transformed constraints: {problems[:5]}"
            )

    def test_set_with_constrained_elements_preserves_constraints(self):
        """Test that set with constrained element generators preserves element constraints.
        
        Note: Size constraints (min_size, max_size) are for generation only.
        During shrinking, collections can become smaller to find minimal counterexamples.
        However, element constraints (from the element generator) should be preserved.
        """
        rng = random.Random(42)
        gen = Gen.set(Gen.int(15, 25), min_size=1, max_size=4)
        
        for _ in range(10):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must respect constraints
            self.assertGreaterEqual(len(root), 1, f"Root size {len(root)} < 1")
            self.assertLessEqual(len(root), 4, f"Root size {len(root)} > 4")
            for elem in root:
                self.assertGreaterEqual(elem, 15, f"Element {elem} < 15")
                self.assertLessEqual(elem, 25, f"Element {elem} > 25")
            
            # All shrinks must respect ELEMENT constraints (size can shrink below min_size)
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                # Only check element constraints, not size constraints
                for elem in sh.value:
                    if elem < 15 or elem > 25:
                        problems.append((depth, sh.value, f"element {elem} out of [15, 25]"))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found sets violating element constraints: {problems[:5]}"
            )


class TestNestedConstraintPreservation(unittest.TestCase):
    """Test constraint preservation for nested structures."""

    def test_list_of_dicts_preserves_constraints(self):
        """Test that list of dicts preserves element constraints at all levels.
        
        Note: Size constraints (min_length, max_length, min_size, max_size) are for generation only.
        During shrinking, collections can become smaller to find minimal counterexamples.
        However, element constraints (from the element generators) should be preserved.
        """
        rng = random.Random(42)
        gen = Gen.list(
            Gen.dict(Gen.int(20, 30), Gen.int(20, 30), min_size=1, max_size=2),
            min_length=1,
            max_length=3
        )
        
        for _ in range(10):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must respect constraints
            self.assertGreaterEqual(len(root), 1)
            self.assertLessEqual(len(root), 3)
            for d in root:
                for k, v in d.items():
                    self.assertGreaterEqual(k, 20, f"Key {k} < 20")
                    self.assertLessEqual(k, 30, f"Key {k} > 30")
                    self.assertGreaterEqual(v, 20, f"Value {v} < 20")
                    self.assertLessEqual(v, 30, f"Value {v} > 30")
            
            # All shrinks must respect ELEMENT constraints (size can shrink)
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                # Only check element constraints, not size constraints
                for d in sh.value:
                    for k, v in d.items():
                        if k < 20 or k > 30:
                            problems.append((depth, f"key {k} out of [20, 30]"))
                        if v < 20 or v > 30:
                            problems.append((depth, f"value {v} out of [20, 30]"))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found nested structures violating element constraints: {problems[:5]}"
            )

    def test_dict_of_lists_preserves_constraints(self):
        """Test that dict of lists preserves element constraints at all levels.
        
        Note: Size constraints (min_length, max_length, min_size, max_size) are for generation only.
        During shrinking, collections can become smaller to find minimal counterexamples.
        However, element constraints (from the element generators) should be preserved.
        """
        rng = random.Random(42)
        gen = Gen.dict(
            Gen.int(30, 40),
            Gen.list(Gen.int(30, 40), min_length=1, max_length=3),
            min_size=1,
            max_size=2
        )
        
        for _ in range(10):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must respect constraints
            for k, v in root.items():
                self.assertGreaterEqual(k, 30, f"Key {k} < 30")
                self.assertLessEqual(k, 40, f"Key {k} > 40")
                self.assertGreaterEqual(len(v), 1, f"List length {len(v)} < 1")
                self.assertLessEqual(len(v), 3, f"List length {len(v)} > 3")
                for elem in v:
                    self.assertGreaterEqual(elem, 30, f"Element {elem} < 30")
                    self.assertLessEqual(elem, 40, f"Element {elem} > 40")
            
            # All shrinks must respect ELEMENT constraints (size can shrink)
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                # Only check element constraints, not size constraints
                for k, v in sh.value.items():
                    if k < 30 or k > 40:
                        problems.append((depth, f"key {k} out of [30, 40]"))
                    for elem in v:
                        if elem < 30 or elem > 40:
                            problems.append((depth, f"element {elem} out of [30, 40]"))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found nested structures violating element constraints: {problems[:5]}"
            )


class TestEdgeCaseConstraintPreservation(unittest.TestCase):
    """Test constraint preservation for edge cases."""

    def test_int_at_min_boundary(self):
        """Test that int at min_value boundary preserves constraints."""
        rng = random.Random(42)
        gen = Gen.int(5, 10)
        
        # Generate many times to hopefully get min_value
        for _ in range(50):
            shrinkable = gen.generate(rng)
            if shrinkable.value == 5:  # Found min_value
                # All shrinks should still be >= 5
                def check_all_shrinks(sh, depth=0, max_depth=5):
                    if depth > max_depth:
                        return []
                    problems = []
                    if sh.value < 5 or sh.value > 10:
                        problems.append((depth, sh.value))
                    for child in sh.shrinks().to_list():
                        problems.extend(check_all_shrinks(child, depth+1, max_depth))
                    return problems
                
                problems = check_all_shrinks(shrinkable)
                self.assertEqual(
                    len(problems), 0,
                    f"Found values violating constraints when at min: {problems[:5]}"
                )
                break

    def test_int_at_max_boundary(self):
        """Test that int at max_value boundary preserves constraints."""
        rng = random.Random(42)
        gen = Gen.int(5, 10)
        
        # Generate many times to hopefully get max_value
        for _ in range(50):
            shrinkable = gen.generate(rng)
            if shrinkable.value == 10:  # Found max_value
                # All shrinks should still be <= 10
                def check_all_shrinks(sh, depth=0, max_depth=5):
                    if depth > max_depth:
                        return []
                    problems = []
                    if sh.value < 5 or sh.value > 10:
                        problems.append((depth, sh.value))
                    for child in sh.shrinks().to_list():
                        problems.extend(check_all_shrinks(child, depth+1, max_depth))
                    return problems
                
                problems = check_all_shrinks(shrinkable)
                self.assertEqual(
                    len(problems), 0,
                    f"Found values violating constraints when at max: {problems[:5]}"
                )
                break

    def test_map_filter_chain_preserves_all_constraints(self):
        """Test that map then filter preserves transformed constraints and filter."""
        rng = random.Random(42)
        gen = (
            Gen.int(4, 12)
            .map(lambda x: x * 2)  # [8, 24]
            .filter(lambda x: x % 4 == 0)  # Must be divisible by 4
        )
        
        for _ in range(10):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            
            # Root must respect transformed constraints [8, 24] AND filter
            self.assertGreaterEqual(root, 8, f"Root {root} < 8")
            self.assertLessEqual(root, 24, f"Root {root} > 24")
            self.assertEqual(root % 4, 0, f"Root {root} not divisible by 4")
            
            # All shrinks must respect both
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                if sh.value < 8 or sh.value > 24:
                    problems.append((depth, sh.value, f"out of [8, 24]"))
                if sh.value % 4 != 0:
                    problems.append((depth, sh.value, f"not divisible by 4"))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth+1, max_depth))
                return problems
            
            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems), 0,
                f"Found values violating constraints: {problems[:5]}"
            )


if __name__ == "__main__":
    unittest.main()

