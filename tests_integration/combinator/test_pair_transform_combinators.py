"""
Tests for transform combinators (filter, map, flat_map) applied to generators
that use pair shrinking (dictionaries, tuples) to ensure conditions are
maintained throughout the shrink tree.
"""

import random
import unittest

from python_proptest import Gen


class TestPairTransformCombinators(unittest.TestCase):
    """Test that filter/map/flatmap maintain conditions when applied to pair-based generators."""

    def test_dict_map_maintains_transformation(self):
        """Test that map on dict generator maintains transformation throughout shrink tree."""
        rng = random.Random(42)
        gen = Gen.dict(Gen.int(0, 100), Gen.int(0, 100), min_size=1, max_size=3).map(
            lambda d: {k * 2: v * 2 for k, v in d.items()}
        )

        for _ in range(10):
            shrinkable = gen.generate(rng)
            root = shrinkable.value

            # Root must have even keys and values
            for k, v in root.items():
                self.assertTrue(
                    k % 2 == 0 and v % 2 == 0,
                    f"Root value has non-even key/value: {root}",
                )

            # All shrinks must have even keys and values
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                for k, v in sh.value.items():
                    if k % 2 != 0 or v % 2 != 0:
                        problems.append((depth, sh.value, k, v))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth + 1, max_depth))
                return problems

            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems),
                0,
                f"Found dicts in shrink tree with non-even keys/values: {problems[:5]}",
            )

    def test_dict_filter_maintains_predicate(self):
        """Test that filter on dict generator maintains predicate throughout shrink tree."""
        rng = random.Random(42)
        gen = Gen.dict(Gen.int(0, 100), Gen.int(0, 100), min_size=1, max_size=3).filter(
            lambda d: sum(d.keys()) + sum(d.values()) > 50
        )

        for _ in range(10):
            shrinkable = gen.generate(rng)
            root = shrinkable.value

            # Root must satisfy predicate
            total = sum(root.keys()) + sum(root.values())
            self.assertTrue(
                total > 50,
                f"Root value {root} does not satisfy filter predicate (sum={total})",
            )

            # All shrinks must satisfy predicate
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                total = sum(sh.value.keys()) + sum(sh.value.values())
                if total <= 50:
                    problems.append((depth, sh.value, total))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth + 1, max_depth))
                return problems

            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems),
                0,
                f"Found dicts in shrink tree that don't satisfy filter: {problems[:5]}",
            )

    def test_dict_map_then_filter_maintains_conditions(self):
        """Test that map then filter on dict generator maintains both conditions."""
        rng = random.Random(42)
        gen = (
            Gen.dict(Gen.int(0, 100), Gen.int(0, 100), min_size=1, max_size=3)
            .map(lambda d: {k * 2: v * 2 for k, v in d.items()})
            .filter(lambda d: sum(d.keys()) + sum(d.values()) > 100)
        )

        for _ in range(10):
            shrinkable = gen.generate(rng)
            root = shrinkable.value

            # Root must have even keys/values AND sum > 100
            for k, v in root.items():
                self.assertTrue(k % 2 == 0 and v % 2 == 0)
            total = sum(root.keys()) + sum(root.values())
            self.assertTrue(total > 100)

            # All shrinks must satisfy both conditions
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                for k, v in sh.value.items():
                    if k % 2 != 0 or v % 2 != 0:
                        problems.append((depth, sh.value, "non-even", k, v))
                total = sum(sh.value.keys()) + sum(sh.value.values())
                if total <= 100:
                    problems.append((depth, sh.value, "sum <= 100", total))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth + 1, max_depth))
                return problems

            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems),
                0,
                f"Found dicts in shrink tree that don't satisfy conditions: {problems[:5]}",
            )

    def test_dict_filter_then_map_maintains_conditions(self):
        """Test that filter then map on dict generator maintains both conditions."""
        rng = random.Random(42)
        gen = (
            Gen.dict(Gen.int(0, 100), Gen.int(0, 100), min_size=1, max_size=3)
            .filter(lambda d: sum(d.keys()) + sum(d.values()) > 30)
            .map(lambda d: {k * 2: v * 2 for k, v in d.items()})
        )

        for _ in range(10):
            shrinkable = gen.generate(rng)
            root = shrinkable.value

            # Root must have even keys/values (from map)
            for k, v in root.items():
                self.assertTrue(k % 2 == 0 and v % 2 == 0)

            # All shrinks must have even keys/values
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                for k, v in sh.value.items():
                    if k % 2 != 0 or v % 2 != 0:
                        problems.append((depth, sh.value, k, v))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth + 1, max_depth))
                return problems

            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems),
                0,
                f"Found dicts in shrink tree with non-even keys/values: {problems[:5]}",
            )

    def test_tuple_map_maintains_transformation(self):
        """Test that map on tuple generator maintains transformation throughout shrink tree."""
        rng = random.Random(42)
        gen = Gen.tuple(Gen.int(0, 100), Gen.int(0, 100)).map(
            lambda t: (t[0] * 2, t[1] * 2)
        )

        for _ in range(10):
            shrinkable = gen.generate(rng)
            root = shrinkable.value

            # Root must have even elements
            self.assertTrue(
                root[0] % 2 == 0 and root[1] % 2 == 0,
                f"Root value {root} has non-even elements",
            )

            # All shrinks must have even elements
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                if sh.value[0] % 2 != 0 or sh.value[1] % 2 != 0:
                    problems.append((depth, sh.value))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth + 1, max_depth))
                return problems

            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems),
                0,
                f"Found tuples in shrink tree with non-even elements: {problems[:5]}",
            )

    def test_tuple_filter_maintains_predicate(self):
        """Test that filter on tuple generator maintains predicate throughout shrink tree."""
        rng = random.Random(42)
        gen = Gen.tuple(Gen.int(0, 100), Gen.int(0, 100)).filter(
            lambda t: t[0] + t[1] > 50
        )

        for _ in range(10):
            shrinkable = gen.generate(rng)
            root = shrinkable.value

            # Root must satisfy predicate
            self.assertTrue(
                root[0] + root[1] > 50,
                f"Root value {root} does not satisfy filter predicate (sum={root[0] + root[1]})",
            )

            # All shrinks must satisfy predicate
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                if sh.value[0] + sh.value[1] <= 50:
                    problems.append((depth, sh.value, sh.value[0] + sh.value[1]))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth + 1, max_depth))
                return problems

            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems),
                0,
                f"Found tuples in shrink tree that don't satisfy filter: {problems[:5]}",
            )

    def test_tuple_map_then_filter_maintains_conditions(self):
        """Test that map then filter on tuple generator maintains both conditions."""
        rng = random.Random(42)
        gen = (
            Gen.tuple(Gen.int(0, 100), Gen.int(0, 100))
            .map(lambda t: (t[0] * 2, t[1] * 2))
            .filter(lambda t: t[0] + t[1] > 100)
        )

        for _ in range(10):
            shrinkable = gen.generate(rng)
            root = shrinkable.value

            # Root must have even elements AND sum > 100
            self.assertTrue(root[0] % 2 == 0 and root[1] % 2 == 0)
            self.assertTrue(root[0] + root[1] > 100)

            # All shrinks must satisfy both conditions
            def check_all_shrinks(sh, depth=0, max_depth=5):
                if depth > max_depth:
                    return []
                problems = []
                if sh.value[0] % 2 != 0 or sh.value[1] % 2 != 0:
                    problems.append((depth, sh.value, "non-even"))
                if sh.value[0] + sh.value[1] <= 100:
                    problems.append((depth, sh.value, "sum <= 100"))
                for child in sh.shrinks().to_list():
                    problems.extend(check_all_shrinks(child, depth + 1, max_depth))
                return problems

            problems = check_all_shrinks(shrinkable)
            self.assertEqual(
                len(problems),
                0,
                f"Found tuples in shrink tree that don't satisfy conditions: {problems[:5]}",
            )


if __name__ == "__main__":
    unittest.main()
