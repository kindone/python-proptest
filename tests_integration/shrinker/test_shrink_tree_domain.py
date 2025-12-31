"""
Tests for shrink tree domain/predicate verification.

These tests verify that all values in a shrink tree satisfy domain constraints,
similar to cppproptest's checkShrinkTreeDomain function.

This is useful for ensuring that:
- Float generators only produce finite values (when configured)
- Integer generators respect min/max bounds throughout the tree
- String generators respect length constraints
- List generators respect size constraints
- Filter predicates are preserved throughout the tree
"""

import math
import random
import unittest

from python_proptest import Gen


def check_shrink_tree_domain(shrinkable, predicate, domain_name="domain", max_depth=100):
    """
    Verify all values in a shrink tree satisfy a predicate.

    Similar to cppproptest's checkShrinkTreeDomain.

    Args:
        shrinkable: The Shrinkable to check
        predicate: Function that returns True if value satisfies domain
        domain_name: Name of domain for error messages
        max_depth: Maximum depth to traverse

    Raises:
        AssertionError: If any value in the tree violates the predicate
    """
    def check_recursive(sh, depth=0):
        if depth > max_depth:
            return []
        problems = []
        if not predicate(sh.value):
            problems.append((depth, sh.value, f"violates {domain_name}"))
        for child in sh.shrinks().to_list():
            problems.extend(check_recursive(child, depth + 1))
        return problems

    problems = check_recursive(shrinkable)
    if problems:
        raise AssertionError(
            f"Found {len(problems)} values violating {domain_name}: {problems[:10]}"
        )


class TestFloatShrinkTreeDomain(unittest.TestCase):
    """Test float shrink tree domain preservation."""

    def test_float_finite_only_shrinks_preserve_domain(self):
        """Test that default float generator (finite only) preserves domain."""
        rng = random.Random(42)
        gen = Gen.float()  # Default: finite only

        for _ in range(10):
            shrinkable = gen.generate(rng)
            # Root must be finite
            self.assertTrue(
                math.isfinite(shrinkable.value),
                f"Root {shrinkable.value} should be finite",
            )
            # All shrinks must be finite
            check_shrink_tree_domain(
                shrinkable,
                lambda x: math.isfinite(x),
                "finite",
            )

    def test_float_with_nan_probability_domain(self):
        """Test that float generator with NaN probability preserves domain."""
        rng = random.Random(42)
        gen = Gen.float(nan_prob=0.1)  # 10% NaN, 90% finite

        for _ in range(20):
            shrinkable = gen.generate(rng)
            # Root can be NaN or finite
            self.assertTrue(
                math.isnan(shrinkable.value) or math.isfinite(shrinkable.value),
                f"Root {shrinkable.value} should be NaN or finite",
            )
            # All shrinks must be NaN or finite (not inf)
            check_shrink_tree_domain(
                shrinkable,
                lambda x: math.isnan(x) or math.isfinite(x),
                "NaN or finite",
            )

    def test_float_with_posinf_probability_domain(self):
        """Test that float generator with +inf probability preserves domain."""
        rng = random.Random(42)
        gen = Gen.float(posinf_prob=0.1)  # 10% +inf, 90% finite

        for _ in range(20):
            shrinkable = gen.generate(rng)
            # Root can be +inf or finite
            self.assertTrue(
                math.isinf(shrinkable.value) and shrinkable.value > 0
                or math.isfinite(shrinkable.value),
                f"Root {shrinkable.value} should be +inf or finite",
            )
            # All shrinks must be +inf or finite (not NaN, not -inf)
            check_shrink_tree_domain(
                shrinkable,
                lambda x: (math.isinf(x) and x > 0) or math.isfinite(x),
                "+inf or finite",
            )

    def test_float_with_neginf_probability_domain(self):
        """Test that float generator with -inf probability preserves domain."""
        rng = random.Random(42)
        gen = Gen.float(neginf_prob=0.1)  # 10% -inf, 90% finite

        for _ in range(20):
            shrinkable = gen.generate(rng)
            # Root can be -inf or finite
            self.assertTrue(
                math.isinf(shrinkable.value) and shrinkable.value < 0
                or math.isfinite(shrinkable.value),
                f"Root {shrinkable.value} should be -inf or finite",
            )
            # All shrinks must be -inf or finite (not NaN, not +inf)
            check_shrink_tree_domain(
                shrinkable,
                lambda x: (math.isinf(x) and x < 0) or math.isfinite(x),
                "-inf or finite",
            )

    def test_float_with_all_probabilities_domain(self):
        """Test that float generator with all special value probabilities preserves domain."""
        rng = random.Random(42)
        gen = Gen.float(nan_prob=0.05, posinf_prob=0.05, neginf_prob=0.05)

        for _ in range(30):
            shrinkable = gen.generate(rng)
            root = shrinkable.value
            # Root can be any valid float value
            self.assertTrue(
                math.isnan(root)
                or (math.isinf(root) and root > 0)
                or (math.isinf(root) and root < 0)
                or math.isfinite(root),
                f"Root {root} should be valid float",
            )
            # All shrinks must be valid (NaN, +inf, -inf, or finite)
            check_shrink_tree_domain(
                shrinkable,
                lambda x: (
                    math.isnan(x)
                    or (math.isinf(x) and x > 0)
                    or (math.isinf(x) and x < 0)
                    or math.isfinite(x)
                ),
                "valid float",
            )


class TestIntShrinkTreeDomain(unittest.TestCase):
    """Test integer shrink tree domain preservation."""

    def test_int_range_domain(self):
        """Test that int generator preserves range constraints throughout tree."""
        rng = random.Random(42)
        gen = Gen.int(min_value=5, max_value=15)

        for _ in range(10):
            shrinkable = gen.generate(rng)
            # Root must respect constraints
            self.assertGreaterEqual(
                shrinkable.value, 5, f"Root {shrinkable.value} < 5"
            )
            self.assertLessEqual(
                shrinkable.value, 15, f"Root {shrinkable.value} > 15"
            )
            # All shrinks must respect constraints
            check_shrink_tree_domain(
                shrinkable,
                lambda x: 5 <= x <= 15,
                "range [5, 15]",
            )

    def test_int_negative_range_domain(self):
        """Test that int generator with negative range preserves domain."""
        rng = random.Random(42)
        gen = Gen.int(min_value=-10, max_value=-1)

        for _ in range(10):
            shrinkable = gen.generate(rng)
            # All values must be in [-10, -1]
            check_shrink_tree_domain(
                shrinkable,
                lambda x: -10 <= x <= -1,
                "range [-10, -1]",
            )


class TestStringShrinkTreeDomain(unittest.TestCase):
    """Test string shrink tree domain preservation."""

    def test_string_length_domain(self):
        """Test that string generator preserves length constraints throughout tree."""
        rng = random.Random(42)
        gen = Gen.str(min_length=2, max_length=10)

        for _ in range(10):
            shrinkable = gen.generate(rng)
            # Root must respect length constraints
            self.assertGreaterEqual(
                len(shrinkable.value), 2, f"Root length {len(shrinkable.value)} < 2"
            )
            self.assertLessEqual(
                len(shrinkable.value), 10, f"Root length {len(shrinkable.value)} > 10"
            )
            # All shrinks must respect length constraints
            check_shrink_tree_domain(
                shrinkable,
                lambda s: 2 <= len(s) <= 10,
                "length [2, 10]",
            )


class TestListShrinkTreeDomain(unittest.TestCase):
    """Test list shrink tree domain preservation."""

    def test_list_size_domain(self):
        """Test that list generator preserves size constraints throughout tree."""
        rng = random.Random(42)
        gen = Gen.list(Gen.int(), min_length=3, max_length=8)

        for _ in range(50):
            shrinkable = gen.generate(rng)
            # Root must respect size constraints
            self.assertGreaterEqual(
                len(shrinkable.value), 3, f"Root size {len(shrinkable.value)} < 3"
            )
            self.assertLessEqual(
                len(shrinkable.value), 8, f"Root size {len(shrinkable.value)} > 8"
            )
            # All shrinks must respect max_length constraint
            # Note: shrinks can be smaller than min_length as part of the shrinking process
            # to find minimal failing cases, but they should not exceed max_length
            check_shrink_tree_domain(
                shrinkable,
                lambda lst: len(lst) >= 3 and len(lst) <= 8,
                "max size 8",
            )

    def test_list_element_domain(self):
        """Test that list generator with element constraints preserves domain."""
        rng = random.Random(42)
        gen = Gen.list(Gen.int(min_value=1, max_value=10), min_length=1, max_length=5)

        for _ in range(10):
            shrinkable = gen.generate(rng)
            # Root elements must respect constraints
            for elem in shrinkable.value:
                self.assertGreaterEqual(elem, 1, f"Element {elem} < 1")
                self.assertLessEqual(elem, 10, f"Element {elem} > 10")

            # All shrinks must have elements in [1, 10]
            def check_list_domain(lst):
                return all(1 <= x <= 10 for x in lst)

            check_shrink_tree_domain(
                shrinkable,
                check_list_domain,
                "elements in [1, 10]",
            )

    def test_list_shrink_uniqueness_with_unique_root(self):
        """Test that shrinking doesn't create duplicates when root has unique values."""
        # Create a shrinkable with unique values: [4, 1, 2, 3] with minSize=2
        # This tests whether the shrinking algorithm itself creates duplicates
        # (not due to duplicates already in the root)
        from python_proptest.core.shrinker.list import shrink_membership_wise
        from python_proptest.core.shrinker import Shrinkable

        # Create base shrinkable with unique values
        base_list = [
            Shrinkable(4),
            Shrinkable(1),
            Shrinkable(2),
            Shrinkable(3),
        ]

        # Shrink with min_size=2
        shrunk = shrink_membership_wise(base_list, min_size=2)

        # Check for duplicates in the shrink tree
        seen_values = set()

        def check_unique(sh: Shrinkable):
            list_tuple = tuple(sh.value)
            assert (
                list_tuple not in seen_values
            ), f"Duplicate list value {list_tuple} found in shrink tree"
            seen_values.add(list_tuple)
            for child in sh.shrinks().to_list():
                check_unique(child)

        check_unique(shrunk)


if __name__ == "__main__":
    unittest.main()
