"""
Tests for transform combinators (filter, map) applied to generators with constraints
to ensure constraints are preserved (or transformed accordingly) throughout the shrink tree.

This specifically tests the case where dictionary/tuple generators are created from
constrained generators (e.g., Gen.int(4, 10) with min_value=4), and then map/filter
are applied.
"""

import random
import unittest

from python_proptest import Gen


class TestConstrainedPairTransform(unittest.TestCase):
    """Test that map/filter preserve or transform constraints correctly."""

    def test_dict_with_constrained_generators_preserves_constraints(self):
        """Test that dict with Gen.int(4, 10) preserves min_value=4 constraint."""
        rng = random.Random(42)
        gen = Gen.dict(Gen.int(4, 10), Gen.int(4, 10), min_size=1, max_size=3)

        for _ in range(10):
            shrinkable = gen.generate(rng)
            root = shrinkable.value

            # Root must respect constraints
            for k, v in root.items():
                self.assertGreaterEqual(k, 4, f"Key {k} < 4 in root")
                self.assertLessEqual(k, 10, f"Key {k} > 10 in root")
                self.assertGreaterEqual(v, 4, f"Value {v} < 4 in root")
                self.assertLessEqual(v, 10, f"Value {v} > 10 in root")

            # All shrinks must respect constraints
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                for k, v in sh.value.items():
                    if k < 4 or k > 10:
                        problems.append((depth, sh.value, f"key {k} out of [4, 10]"))
                    if v < 4 or v > 10:
                        problems.append((depth, sh.value, f"value {v} out of [4, 10]"))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth + 1, max_depth))
                return problems

            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems),
                0,
                f"Found dicts in shrink tree that violate constraints: {problems[:5]}",
            )

    def test_dict_map_transforms_constraints_correctly(self):
        """Test that map on constrained dict transforms constraints correctly."""
        rng = random.Random(42)
        # Gen.int(4, 10) -> after map(*2) should be [8, 20]
        gen = Gen.dict(Gen.int(4, 10), Gen.int(4, 10), min_size=1, max_size=3).map(
            lambda d: {k * 2: v * 2 for k, v in d.items()}
        )

        for _ in range(10):
            shrinkable = gen.generate(rng)
            root = shrinkable.value

            # Root must respect transformed constraints (min_value=8, max_value=20)
            for k, v in root.items():
                self.assertGreaterEqual(k, 8, f"Key {k} < 8 (4*2) in root")
                self.assertLessEqual(k, 20, f"Key {k} > 20 (10*2) in root")
                self.assertGreaterEqual(v, 8, f"Value {v} < 8 (4*2) in root")
                self.assertLessEqual(v, 20, f"Value {v} > 20 (10*2) in root")

            # All shrinks must respect transformed constraints
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                for k, v in sh.value.items():
                    if k < 8 or k > 20:
                        problems.append((depth, sh.value, f"key {k} out of [8, 20]"))
                    if v < 8 or v > 20:
                        problems.append((depth, sh.value, f"value {v} out of [8, 20]"))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth + 1, max_depth))
                return problems

            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems),
                0,
                f"Found dicts in shrink tree that violate transformed constraints: {problems[:5]}",
            )

    def test_dict_filter_preserves_original_constraints(self):
        """Test that filter on constrained dict preserves original constraints."""
        rng = random.Random(42)
        # Filter should preserve the original constraints from Gen.int(4, 10)
        gen = Gen.dict(Gen.int(4, 10), Gen.int(4, 10), min_size=1, max_size=3).filter(
            lambda d: sum(d.keys()) + sum(d.values()) > 20
        )

        for _ in range(10):
            shrinkable = gen.generate(rng)
            root = shrinkable.value

            # Root must respect original constraints AND filter predicate
            for k, v in root.items():
                self.assertGreaterEqual(k, 4, f"Key {k} < 4 in root")
                self.assertLessEqual(k, 10, f"Key {k} > 10 in root")
                self.assertGreaterEqual(v, 4, f"Value {v} < 4 in root")
                self.assertLessEqual(v, 10, f"Value {v} > 10 in root")
            total = sum(root.keys()) + sum(root.values())
            self.assertGreater(total, 20, f"Sum {total} <= 20 in root")

            # All shrinks must respect both original constraints AND filter predicate
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                for k, v in sh.value.items():
                    if k < 4 or k > 10:
                        problems.append((depth, sh.value, f"key {k} out of [4, 10]"))
                    if v < 4 or v > 10:
                        problems.append((depth, sh.value, f"value {v} out of [4, 10]"))
                total = sum(sh.value.keys()) + sum(sh.value.values())
                if total <= 20:
                    problems.append((depth, sh.value, f"sum {total} <= 20"))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth + 1, max_depth))
                return problems

            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems),
                0,
                f"Found dicts in shrink tree that violate constraints: {problems[:5]}",
            )

    def test_dict_map_then_filter_preserves_both(self):
        """Test that map then filter preserves transformed constraints and filter."""
        rng = random.Random(42)
        gen = (
            Gen.dict(Gen.int(4, 10), Gen.int(4, 10), min_size=1, max_size=3)
            .map(lambda d: {k * 2: v * 2 for k, v in d.items()})
            .filter(lambda d: sum(d.keys()) + sum(d.values()) > 40)
        )

        for _ in range(10):
            shrinkable = gen.generate(rng)
            root = shrinkable.value

            # Root must respect transformed constraints [8, 20] AND filter
            for k, v in root.items():
                self.assertGreaterEqual(k, 8)
                self.assertLessEqual(k, 20)
                self.assertGreaterEqual(v, 8)
                self.assertLessEqual(v, 20)
            total = sum(root.keys()) + sum(root.values())
            self.assertGreater(total, 40)

            # All shrinks must respect both
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                for k, v in sh.value.items():
                    if k < 8 or k > 20:
                        problems.append((depth, sh.value, f"key {k} out of [8, 20]"))
                    if v < 8 or v > 20:
                        problems.append((depth, sh.value, f"value {v} out of [8, 20]"))
                total = sum(sh.value.keys()) + sum(sh.value.values())
                if total <= 40:
                    problems.append((depth, sh.value, f"sum {total} <= 40"))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth + 1, max_depth))
                return problems

            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems),
                0,
                f"Found dicts in shrink tree that violate constraints: {problems[:5]}",
            )

    def test_tuple_with_constrained_generators_preserves_constraints(self):
        """Test that tuple with Gen.int(4, 10) preserves min_value=4 constraint."""
        rng = random.Random(42)
        gen = Gen.tuple(Gen.int(4, 10), Gen.int(4, 10))

        for _ in range(10):
            shrinkable = gen.generate(rng)
            root = shrinkable.value

            # Root must respect constraints
            self.assertGreaterEqual(root[0], 4)
            self.assertLessEqual(root[0], 10)
            self.assertGreaterEqual(root[1], 4)
            self.assertLessEqual(root[1], 10)

            # All shrinks must respect constraints
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                if sh.value[0] < 4 or sh.value[0] > 10:
                    problems.append(
                        (depth, sh.value, f"first {sh.value[0]} out of [4, 10]")
                    )
                if sh.value[1] < 4 or sh.value[1] > 10:
                    problems.append(
                        (depth, sh.value, f"second {sh.value[1]} out of [4, 10]")
                    )
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth + 1, max_depth))
                return problems

            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems),
                0,
                f"Found tuples in shrink tree that violate constraints: {problems[:5]}",
            )

    def test_tuple_map_transforms_constraints_correctly(self):
        """Test that map on constrained tuple transforms constraints correctly."""
        rng = random.Random(42)
        gen = Gen.tuple(Gen.int(4, 10), Gen.int(4, 10)).map(
            lambda t: (t[0] * 2, t[1] * 2)
        )

        for _ in range(10):
            shrinkable = gen.generate(rng)
            root = shrinkable.value

            # Root must respect transformed constraints [8, 20]
            self.assertGreaterEqual(root[0], 8)
            self.assertLessEqual(root[0], 20)
            self.assertGreaterEqual(root[1], 8)
            self.assertLessEqual(root[1], 20)

            # All shrinks must respect transformed constraints
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                if sh.value[0] < 8 or sh.value[0] > 20:
                    problems.append(
                        (depth, sh.value, f"first {sh.value[0]} out of [8, 20]")
                    )
                if sh.value[1] < 8 or sh.value[1] > 20:
                    problems.append(
                        (depth, sh.value, f"second {sh.value[1]} out of [8, 20]")
                    )
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth + 1, max_depth))
                return problems

            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems),
                0,
                f"Found tuples in shrink tree that violate transformed constraints: {problems[:5]}",
            )


if __name__ == "__main__":
    unittest.main()
