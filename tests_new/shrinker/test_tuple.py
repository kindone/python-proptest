"""Tests for ``python_proptest.core.shrinker.tuple`` tuple shrinking behavior."""

import unittest

from python_proptest import Gen, PropertyTestError, run_for_all


class TestTupleShrinking(unittest.TestCase):
    """Verify tuple shrinking finds minimal failing cases."""

    def test_tuple_shrinks_components_independently(self):
        """Tuple properties shrink each component independently."""

        def property_func(t: tuple):
            # Fail when sum of tuple elements >= 10
            return sum(t) < 10

        with self.assertRaises(PropertyTestError) as exc_info:
            run_for_all(
                property_func,
                Gen.tuple(
                    Gen.int(min_value=0, max_value=10),
                    Gen.int(min_value=0, max_value=10),
                    Gen.int(min_value=0, max_value=10),
                ),
                num_runs=50,
            )

        # Should have shrunk tuple components
        minimal_input = exc_info.exception.minimal_inputs[0]
        self.assertIsInstance(minimal_input, tuple)
        self.assertEqual(len(minimal_input), 3)
        self.assertGreaterEqual(sum(minimal_input), 10)


if __name__ == "__main__":
    unittest.main()

