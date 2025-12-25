"""Tests for ``python_proptest.core.shrinker.pair`` dict shrinking behavior."""

import unittest

from python_proptest import Gen, PropertyTestError, run_for_all


class TestPairShrinking(unittest.TestCase):
    """Verify dictionary (pair-based) shrinking finds minimal failing cases."""

    def test_dict_shrinks_to_minimal_size(self):
        """Dictionary properties shrink to minimal failing size."""

        def property_func(d: dict):
            # Fail for dicts of size >= 2
            return len(d) < 2

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func,
                Gen.dict(
                    Gen.str(min_length=1, max_length=2),
                    Gen.int(min_value=0, max_value=10),
                    min_size=0,
                    max_size=3,
                ),
                num_runs=50,
            )

        # Should shrink to a dict of size 2 (minimal failing size)
        failing_input = exc_info.exception.failing_inputs[0]
        self.assertIsInstance(failing_input, dict)
        self.assertGreaterEqual(len(failing_input), 2)
        self.assertLess(len(failing_input), 4)  # Should be close to minimal

    def test_shrinking_with_nested_dicts(self):
        """Shrinking works with nested dictionary structures."""

        def property_func(d: dict):
            # Fail when dict has nested dicts with total keys >= 2
            total_keys = len(d)
            for v in d.values():
                if isinstance(v, dict):
                    total_keys += len(v)
            return total_keys < 2

        nested_gen = Gen.dict(
            Gen.str(min_length=1, max_length=2),
            Gen.one_of(
                Gen.int(min_value=0, max_value=10),
                Gen.dict(
                    Gen.str(min_length=1, max_length=1),
                    Gen.int(min_value=0, max_value=5),
                    min_size=0,
                    max_size=2,
                ),
            ),
            min_size=1,
            max_size=3,
        )

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(property_func, nested_gen, num_runs=50)

        # Should have shrunk to a minimal failing structure
        failing_input = exc_info.exception.failing_inputs[0]
        self.assertIsInstance(failing_input, dict)


if __name__ == "__main__":
    unittest.main()

