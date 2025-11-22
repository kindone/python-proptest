"""
Tests for membership-wise shrinking to verify it matches cppproptest behavior.
"""

import unittest
from python_proptest.core.shrinker.list import shrink_membership_wise
from python_proptest.core.shrinker import Shrinkable


class TestMembershipWiseShrinking(unittest.TestCase):
    """Test membership-wise shrinking matches cppproptest's shrinkFrontAndThenMid."""

    def test_list_size_3_generates_all_subsets(self):
        """Test that [1, 2, 3] generates all 2^3 = 8 subsets."""
        elems = [Shrinkable(1), Shrinkable(2), Shrinkable(3)]
        result = shrink_membership_wise(elems, min_size=0)

        # Collect all unique subsets
        all_values = set()

        def collect_values(shrinkable):
            values = tuple(s.value for s in shrinkable.value)
            all_values.add(values)
            for shrink in shrinkable.shrinks().to_list():
                collect_values(shrink)

        collect_values(result)

        # Should generate all 2^3 = 8 subsets
        expected_subsets = {
            (),
            (1,),
            (2,),
            (3,),
            (1, 2),
            (1, 3),
            (2, 3),
            (1, 2, 3),
        }

        self.assertEqual(len(all_values), 8, f"Expected 8 subsets, got {len(all_values)}")
        self.assertEqual(all_values, expected_subsets)

    def test_list_size_3_structure_matches_cppproptest(self):
        """Test that the shrink tree structure matches cppproptest's expected output."""
        elems = [Shrinkable(1), Shrinkable(2), Shrinkable(3)]
        result = shrink_membership_wise(elems, min_size=0)

        # Expected direct shrinks from cppproptest test:
        # {value: [ 1, 2, 3 ], shrinks: [
        #   {value: [  ]},
        #   {value: [ 1 ]},
        #   {value: [ 1, 2 ], shrinks: [{value: [ 2 ]}]},
        #   {value: [ 3 ]},
        #   {value: [ 1, 3 ]},
        #   {value: [ 2, 3 ]}
        # ]}

        shrinks = result.shrinks().to_list()
        self.assertEqual(len(shrinks), 6, "Should have 6 direct shrinks")

        # Check that [1, 2] has [2] as a recursive shrink
        found_1_2 = False
        for shrink in shrinks:
            values = tuple(s.value for s in shrink.value)
            if values == (1, 2):
                found_1_2 = True
                recursive = list(shrink.shrinks().to_list())
                self.assertEqual(len(recursive), 1, "[1, 2] should have 1 recursive shrink")
                self.assertEqual(
                    tuple(s.value for s in recursive[0].value),
                    (2,),
                    "[1, 2] should shrink to [2]",
                )
                break

        self.assertTrue(found_1_2, "Should find [1, 2] in direct shrinks")

    def test_list_size_2_generates_all_subsets(self):
        """Test that [1, 2] generates all 2^2 = 4 subsets."""
        elems = [Shrinkable(1), Shrinkable(2)]
        result = shrink_membership_wise(elems, min_size=0)

        all_values = set()

        def collect_values(shrinkable):
            values = tuple(s.value for s in shrinkable.value)
            all_values.add(values)
            for shrink in shrinkable.shrinks().to_list():
                collect_values(shrink)

        collect_values(result)

        expected_subsets = {(), (1,), (2,), (1, 2)}
        self.assertEqual(len(all_values), 4, f"Expected 4 subsets, got {len(all_values)}")
        self.assertEqual(all_values, expected_subsets)

    def test_list_size_1_generates_all_subsets(self):
        """Test that [1] generates all 2^1 = 2 subsets."""
        elems = [Shrinkable(1)]
        result = shrink_membership_wise(elems, min_size=0)

        all_values = set()

        def collect_values(shrinkable):
            values = tuple(s.value for s in shrinkable.value)
            all_values.add(values)
            for shrink in shrinkable.shrinks().to_list():
                collect_values(shrink)

        collect_values(result)

        expected_subsets = {(), (1,)}
        self.assertEqual(len(all_values), 2, f"Expected 2 subsets, got {len(all_values)}")
        self.assertEqual(all_values, expected_subsets)

    def test_respects_min_size(self):
        """Test that min_size is respected."""
        elems = [Shrinkable(1), Shrinkable(2), Shrinkable(3)]
        result = shrink_membership_wise(elems, min_size=2)

        all_values = set()

        def collect_values(shrinkable):
            values = tuple(s.value for s in shrinkable.value)
            all_values.add(values)
            for shrink in shrinkable.shrinks().to_list():
                collect_values(shrink)

        collect_values(result)

        # All subsets should have size >= 2
        for values in all_values:
            self.assertGreaterEqual(
                len(values), 2, f"Subset {values} should have size >= 2"
            )


if __name__ == "__main__":
    unittest.main()

