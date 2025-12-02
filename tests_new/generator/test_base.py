"""Tests for core generator base behaviours."""

import unittest

from python_proptest import Gen, run_for_all


class TestGeneratorBase(unittest.TestCase):
    """Validate tuple and dict/set generators provided by ``Gen`` namespace."""

    def test_tuple_generator_preserves_order(self):
        """Tuple generator combines elements in declared order."""

        generator = Gen.tuple(Gen.int(0, 5), Gen.bool(), Gen.str(min_length=1, max_length=3))

        def predicate(value):
            if not isinstance(value, tuple) or len(value) != 3:
                return False
            first, second, third = value
            return (
                isinstance(first, int)
                and 0 <= first <= 5
                and isinstance(second, bool)
                and isinstance(third, str)
                and 1 <= len(third) <= 3
            )

        run_for_all(predicate, generator, num_runs=200)

    def test_dict_generator_constraints(self):
        """Dictionary generator adheres to size and value constraints."""

        generator = Gen.dict(
            Gen.str(min_length=1, max_length=2),
            Gen.int(min_value=0, max_value=5),
            min_size=0,
            max_size=3,
        )

        def predicate(value):
            if not isinstance(value, dict) or not (0 <= len(value) <= 3):
                return False
            for key, val in value.items():
                if not (isinstance(key, str) and 1 <= len(key) <= 2):
                    return False
                if not (isinstance(val, int) and 0 <= val <= 5):
                    return False
            return True

        run_for_all(predicate, generator, num_runs=200)

    def test_set_generator_uniqueness(self):
        """Set generator returns unique elements within range."""

        generator = Gen.set(
            Gen.int(min_value=0, max_value=10),
            min_size=0,
            max_size=5,
        )

        run_for_all(
            lambda value: isinstance(value, set) and all(0 <= elem <= 10 for elem in value),
            generator,
            num_runs=200,
        )


if __name__ == "__main__":
    unittest.main()
