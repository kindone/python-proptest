"""Tests for ``python_proptest.core.combinator.one_of``."""

import unittest

from python_proptest import Gen, run_for_all


class TestOneOf(unittest.TestCase):
    """Validate generator selection combinator ``Gen.one_of``."""

    def test_selects_from_generators(self):
        """Values originate from one of the supplied generators."""

        generator = Gen.one_of(Gen.just(1), Gen.just(2))

        run_for_all(lambda value: value in [1, 2], generator, num_runs=60)

    def test_supports_mixed_generator_types(self):
        """Different generator types may be combined in one_of."""

        generator = Gen.one_of(
            Gen.int(min_value=1, max_value=10),
            Gen.str(min_length=1, max_length=5),
            Gen.bool(),
        )

        observed_types = set()

        def property_under_test(value):
            observed_types.add(type(value))
            return isinstance(value, (int, str, bool))

        run_for_all(property_under_test, generator, num_runs=120)

        self.assertGreaterEqual(len(observed_types), 2)

    def test_empty_input_raises_value_error(self):
        """one_of must receive at least one generator."""

        with self.assertRaises(ValueError):
            Gen.one_of()

    def test_single_generator_is_valid(self):
        """A single generator acts as a pass-through."""

        run_for_all(lambda value: value == 42, Gen.one_of(Gen.just(42)), num_runs=20)


if __name__ == "__main__":
    unittest.main()
