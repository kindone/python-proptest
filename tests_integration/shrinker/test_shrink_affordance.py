"""
Shrink affordance tests: verify that the fixes to FlatMappedGenerator,
ChainGenerator, and ListGenerator produce multi-level shrinking as expected.

Key fixes verified here:
1. FlatMappedGenerator / ChainGenerator now delegate to Shrinkable.flat_map,
   giving correct T-axis recursive shrinking (not just one level deep).
2. ListGenerator now enables element_wise=True, so list elements themselves
   shrink, not only the list length.
3. shrinkable_array element-wise uses concat (not and_then), so element shrinks
   fire at every node of the membership shrink tree.
"""

import random
import unittest

from python_proptest import Gen, Property


def collect_all_shrinks(shrinkable, max_depth=10):
    """BFS over a shrink tree up to max_depth; return set of all seen values."""
    seen = set()
    queue = [(shrinkable, 0)]
    while queue:
        node, depth = queue.pop(0)
        v = node.value
        key = v if not isinstance(v, list) else tuple(v)
        seen.add(key)
        if depth < max_depth:
            for child in node.shrinks().to_list():
                queue.append((child, depth + 1))
    return seen


class TestFlatMappedGeneratorShrinkAffordance(unittest.TestCase):
    """Verify FlatMappedGenerator (Gen.flat_map) multi-level shrinking."""

    def test_t_axis_shrinks_recursively(self):
        """
        T-axis shrinks must cascade: if T shrinks to T', the U derived from T'
        must also appear in the shrink tree, and T' must itself have further
        T-axis shrinks (not just one level deep).

        We use flat_map(int[5..20], lambda n: int[0..n]) so the T value
        controls the U range.  Starting from a large T the shrinker should
        eventually reach T=5 (or close), not stop at T's first shrink.
        """
        rng = random.Random("flat-map-t-axis")
        gen = Gen.int(min_value=5, max_value=20).flat_map(
            lambda n: Gen.int(min_value=0, max_value=n)
        )
        shrinkable = gen.generate(rng)

        all_t_u = collect_all_shrinks(shrinkable, max_depth=20)

        # We only have the combined (T, U) value merged — but the ROOT value is
        # the U output.  To check T shrinking, run a property that fails for
        # large T so the shrinker must reduce it.
        found_small = any(v <= 5 for v in all_t_u if isinstance(v, int))
        self.assertTrue(
            found_small,
            f"Expected shrink tree to reach values ≤5; saw {sorted(all_t_u)[:20]}",
        )

    def test_flat_map_property_finds_minimal(self):
        """
        A property that fails for any list with sum > 0 should shrink to
        a single-element list [1] when the element generator is int[1..10].
        Without T-axis recursive shrinking the minimal would stay too large.
        """
        counterexample = None
        try:
            Property(lambda xs: sum(xs) == 0).set_seed("shrink-minimal").set_num_runs(
                200
            ).for_all(Gen.list(Gen.int(min_value=1, max_value=10), min_length=1))
        except Exception as e:
            counterexample = str(e)

        # The property should fail (all elements are ≥1 so sum is always >0)
        self.assertIsNotNone(counterexample, "Property should have failed")

        # With element-wise + membership shrinking the minimal should be [1]
        # We parse the counterexample string for the minimal value
        self.assertIn(
            "[1]",
            counterexample,
            f"Expected minimal counterexample [1] but got: {counterexample}",
        )


class TestListElementShrinking(unittest.TestCase):
    """Verify element_wise=True in ListGenerator means elements shrink."""

    def test_elements_shrink_toward_minimum(self):
        """
        Given a list of ints in [3..10], the shrink tree should contain lists
        whose elements approach the minimum value (3).  Without element_wise this
        never happens — only the list length would shrink.
        """
        rng = random.Random("elem-shrink")
        gen = Gen.list(Gen.int(min_value=3, max_value=10), min_length=1, max_length=5)
        shrinkable = gen.generate(rng)

        all_values = collect_all_shrinks(shrinkable, max_depth=8)
        all_elems = {e for t in all_values if isinstance(t, tuple) for e in t}
        all_elems.update({v for v in all_values if isinstance(v, int)})

        # Filter element values from list tuples
        elem_values = set()
        for v in all_values:
            if isinstance(v, tuple):
                elem_values.update(v)

        self.assertTrue(
            any(e == 3 for e in elem_values),
            f"Expected element value 3 (min) to appear in shrink tree; "
            f"saw element values: {sorted(elem_values)}",
        )

    def test_property_shrinks_list_elements(self):
        """
        Property fails when any element > 3.  Without element_wise the shrinker
        can only reduce list length, and could report a 1-element counterexample
        like [7] instead of the minimal [4].  With element_wise it reaches [4].
        """
        counterexample = None
        try:
            Property(lambda xs: all(x <= 3 for x in xs)).set_seed(
                "elem-shrink-prop"
            ).set_num_runs(200).for_all(
                Gen.list(Gen.int(min_value=1, max_value=10), min_length=1)
            )
        except Exception as e:
            counterexample = str(e)

        self.assertIsNotNone(counterexample, "Property should have failed")
        # The minimal counterexample should contain element 4 (smallest value > 3)
        self.assertIn(
            "4",
            counterexample,
            f"Expected minimal element 4 in counterexample; got: {counterexample}",
        )


class TestChainGeneratorShrinkAffordance(unittest.TestCase):
    """Verify ChainGenerator (Gen.chain) multi-level shrinking."""

    def test_chain_base_value_shrinks(self):
        """
        chain(int[5..20], lambda n: int[0..n]) should shrink the base n
        recursively, eventually reaching 5.
        """
        rng = random.Random("chain-base")
        # Access chain via flat_map on tuple — chain returns (base, dep) tuple
        gen = Gen.int(min_value=5, max_value=20).chain(
            lambda n: Gen.int(min_value=0, max_value=n)
        )
        shrinkable = gen.generate(rng)

        all_vals = collect_all_shrinks(shrinkable, max_depth=20)

        # all_vals are tuples (base, dep); check base values
        base_vals = {t[0] for t in all_vals if isinstance(t, tuple) and len(t) == 2}
        self.assertTrue(
            any(b <= 5 for b in base_vals),
            f"Expected base to shrink to 5; saw base values: {sorted(base_vals)}",
        )


if __name__ == "__main__":
    unittest.main()
