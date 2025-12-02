"""Tests for ``python_proptest.core.combinator.construct``."""

import unittest
from dataclasses import dataclass

from python_proptest import Gen, PropertyTestError, run_for_all


@dataclass
class Point:
    x: int
    y: int


class TestConstructCombinator(unittest.TestCase):
    """Ensure ``Gen.construct`` builds objects and propagates shrinks."""

    def test_construct_creates_instances(self):
        """Generated values should be constructed using provided class."""

        point_gen = Gen.construct(
            Point,
            Gen.int(min_value=-5, max_value=5),
            Gen.int(min_value=-5, max_value=5),
        )

        def property_under_test(point: Point) -> bool:
            return (
                isinstance(point, Point)
                and -5 <= point.x <= 5
                and -5 <= point.y <= 5
            )

        run_for_all(property_under_test, point_gen, num_runs=100)

    def test_construct_propagates_shrinks(self):
        """Shrinking underlying generators should construct new instances."""

        point_gen = Gen.construct(
            Point,
            Gen.int(min_value=1, max_value=10),
            Gen.int(min_value=1, max_value=10),
        )

        with self.assertRaises(PropertyTestError) as ctx:
            run_for_all(lambda _: False, point_gen, num_runs=1)

        error = ctx.exception
        self.assertIsNotNone(error.minimal_inputs)
        self.assertIsNotNone(error.failing_inputs)

        minimal_point = error.minimal_inputs[0]
        failing_point = error.failing_inputs[0]

        self.assertIsInstance(minimal_point, Point)
        self.assertIsInstance(failing_point, Point)

        self.assertLessEqual(minimal_point.x, failing_point.x)
        self.assertLessEqual(minimal_point.y, failing_point.y)
        self.assertGreaterEqual(minimal_point.x, 1)
        self.assertLessEqual(minimal_point.x, 10)
        self.assertGreaterEqual(minimal_point.y, 1)
        self.assertLessEqual(minimal_point.y, 10)
        self.assertNotEqual(minimal_point, failing_point)


if __name__ == "__main__":
    unittest.main()
