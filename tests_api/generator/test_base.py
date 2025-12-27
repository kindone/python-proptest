"""Tests for core generator base behaviours."""

import unittest

from python_proptest import Gen, for_all


class TestGeneratorBase(unittest.TestCase):
    """Validate tuple and dict/set generators provided by ``Gen`` namespace."""

    @for_all(
        Gen.tuple(Gen.int(0, 5), Gen.bool(), Gen.str(min_length=1, max_length=3)),
        num_runs=200,
    )
    def test_tuple_generator_preserves_order(self, value):
        """Tuple generator combines elements in declared order."""

        self.assertIsInstance(value, tuple)
        self.assertEqual(len(value), 3)
        first, second, third = value
        self.assertIsInstance(first, int)
        self.assertGreaterEqual(first, 0)
        self.assertLessEqual(first, 5)
        self.assertIsInstance(second, bool)
        self.assertIsInstance(third, str)
        self.assertGreaterEqual(len(third), 1)
        self.assertLessEqual(len(third), 3)

    @for_all(
        Gen.dict(
            Gen.str(min_length=1, max_length=2),
            Gen.int(min_value=0, max_value=5),
            min_size=0,
            max_size=3,
        ),
        num_runs=200,
    )
    def test_dict_generator_constraints(self, value):
        """Dictionary generator adheres to size and value constraints."""

        self.assertIsInstance(value, dict)
        self.assertLessEqual(len(value), 3)
        for key, val in value.items():
            self.assertIsInstance(key, str)
            self.assertGreaterEqual(len(key), 1)
            self.assertLessEqual(len(key), 2)
            self.assertIsInstance(val, int)
            self.assertGreaterEqual(val, 0)
            self.assertLessEqual(val, 5)

    @for_all(
        Gen.set(
            Gen.int(min_value=0, max_value=10),
            min_size=0,
            max_size=5,
        ),
        num_runs=200,
    )
    def test_set_generator_uniqueness(self, value):
        """Set generator returns unique elements within range."""

        self.assertIsInstance(value, set)
        self.assertTrue(all(0 <= elem <= 10 for elem in value))


if __name__ == "__main__":
    unittest.main()
