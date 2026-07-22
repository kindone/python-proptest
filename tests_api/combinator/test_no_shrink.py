"""Unit tests for ``python_proptest.core.combinator.no_shrink``."""

import random
import unittest

from python_proptest import Gen
from python_proptest.core.shrinker import Shrinkable


def _make_rng(seed: int = 42):
    """Return a seeded stdlib Random instance usable as a generator RNG."""
    return random.Random(seed)


class TestNoShrink(unittest.TestCase):
    """Verify behaviour of Gen.no_shrink() and .no_shrink()."""

    # ------------------------------------------------------------------
    # Standalone form: Gen.no_shrink(gen)
    # ------------------------------------------------------------------

    def test_standalone_produces_values_in_range(self):
        """Gen.no_shrink(Gen.int(...)) still generates values in range."""
        rng = _make_rng()
        gen = Gen.no_shrink(Gen.int(5, 100))
        for _ in range(50):
            shr = gen.generate(rng)
            self.assertGreaterEqual(shr.value, 5)
            self.assertLessEqual(shr.value, 100)

    def test_standalone_produces_empty_shrinks(self):
        """Gen.no_shrink() strips the shrink stream — shrinks() is empty."""
        rng = _make_rng()
        gen = Gen.no_shrink(Gen.int(5, 100))
        for _ in range(50):
            shr = gen.generate(rng)
            self.assertTrue(shr.shrinks().is_empty())

    # ------------------------------------------------------------------
    # Method form: gen.no_shrink()
    # ------------------------------------------------------------------

    def test_method_produces_values_in_range(self):
        """gen.no_shrink() still generates values in the correct range."""
        rng = _make_rng()
        gen = Gen.int(5, 100).no_shrink()
        for _ in range(50):
            shr = gen.generate(rng)
            self.assertGreaterEqual(shr.value, 5)
            self.assertLessEqual(shr.value, 100)

    def test_method_produces_empty_shrinks(self):
        """.no_shrink() strips the shrink stream — shrinks() is empty."""
        rng = _make_rng()
        gen = Gen.int(5, 100).no_shrink()
        for _ in range(50):
            shr = gen.generate(rng)
            self.assertTrue(shr.shrinks().is_empty())

    # ------------------------------------------------------------------
    # Works on generators that normally have shrinks
    # ------------------------------------------------------------------

    def test_int_normally_has_shrinks(self):
        """Sanity check: without no_shrink, Gen.int does produce shrink candidates."""
        rng = _make_rng()
        gen = Gen.int(5, 100)
        found_shrinks = False
        for _ in range(50):
            shr = gen.generate(rng)
            if not shr.shrinks().is_empty():
                found_shrinks = True
                break
        self.assertTrue(found_shrinks, "Expected Gen.int to produce at least some shrink candidates")

    def test_list_gen_no_shrink(self):
        """no_shrink works on non-integer generators too."""
        rng = _make_rng()
        gen = Gen.no_shrink(Gen.list(Gen.int(0, 10), min_length=2, max_length=5))
        for _ in range(30):
            shr = gen.generate(rng)
            self.assertIsInstance(shr.value, list)
            self.assertTrue(shr.shrinks().is_empty())

    def test_str_gen_no_shrink(self):
        """no_shrink works on string generators."""
        rng = _make_rng()
        gen = Gen.no_shrink(Gen.str(2, 10))
        for _ in range(30):
            shr = gen.generate(rng)
            self.assertIsInstance(shr.value, str)
            self.assertTrue(shr.shrinks().is_empty())

    # ------------------------------------------------------------------
    # Composition: no_shrink + flat_map => only U-axis shrinks
    # ------------------------------------------------------------------

    def test_no_shrink_flat_map_only_u_axis_shrinks(self):
        """When T has no shrinks, flat_map produces only U-axis shrink candidates.

        All direct children of root must have value <= root.value (U-axis), and
        no child should re-generate a different T (since T is suppressed).
        """
        rng = _make_rng()
        gen = Gen.no_shrink(Gen.int(2, 10)).flat_map(lambda n: Gen.int(0, n))

        for _ in range(50):
            root = gen.generate(rng)
            # Every direct shrink candidate must be <= root (pure U-axis shrink)
            stream = root.shrinks()
            while not stream.is_empty():
                child = stream.head()
                self.assertLessEqual(child.value, root.value)
                stream = stream.tail()

    # ------------------------------------------------------------------
    # Chaining: double no_shrink is a no-op (still no shrinks)
    # ------------------------------------------------------------------

    def test_double_no_shrink_is_idempotent(self):
        """Applying no_shrink twice still yields an empty shrink stream."""
        rng = _make_rng()
        gen = Gen.int(0, 50).no_shrink().no_shrink()
        for _ in range(20):
            shr = gen.generate(rng)
            self.assertTrue(shr.shrinks().is_empty())


if __name__ == "__main__":
    unittest.main()
