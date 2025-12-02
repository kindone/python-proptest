"""Tests for generator transformations (.map, .filter, .flat_map)."""

import unittest

from python_proptest import Gen, PropertyTestError, run_for_all


class TestGeneratorTransformations(unittest.TestCase):
    """Cover transformation APIs on generators."""

    def test_map_transformation_preserves_structure(self):
        """Mapping integers to strings keeps formatting contract."""

        generator = Gen.int(min_value=1, max_value=50).map(lambda value: f"Value: {value}")

        def predicate(value: str) -> bool:
            return value.startswith("Value: ") and value[7:].isdigit()

        run_for_all(predicate, generator, num_runs=200)

    def test_filter_removes_odd_numbers(self):
        """Filtering even values ensures modulus predicate holds."""

        generator = Gen.int(min_value=0, max_value=100).filter(lambda value: value % 2 == 0)

        run_for_all(lambda value: value % 2 == 0, generator, num_runs=200)

    def test_filter_impossible_predicate_raises(self):
        """Impossible filter must surface ``ValueError`` via ``PropertyTestError``."""

        generator = Gen.int(min_value=0, max_value=10).filter(lambda value: value > 100)

        with self.assertRaises(PropertyTestError) as ctx:
            run_for_all(lambda value: True, generator, num_runs=1)

        self.assertIsInstance(ctx.exception.__cause__, ValueError)

    def test_flat_map_generates_nested_constraints(self):
        """Flat map allows dependent ranges to stay consistent."""

        generator = Gen.int(min_value=1, max_value=5).flat_map(
            lambda length: Gen.list(
                Gen.int(0, 10),
                min_length=length,
                max_length=length,
            ).map(lambda items: (length, items))
        )

        def predicate(value):
            length, items = value
            return (
                isinstance(length, int)
                and length == len(items)
                and all(isinstance(elem, int) and 0 <= elem <= 10 for elem in items)
            )

        run_for_all(predicate, generator, num_runs=200)

    def test_flat_map_shrinks_maintain_dependency(self):
        """Shrinking keeps dependent values aligned with the base value."""

        generator = Gen.int(min_value=1, max_value=5).flat_map(
            lambda start: Gen.int(min_value=start, max_value=start + 10)
        )

        with self.assertRaises(PropertyTestError) as ctx:
            run_for_all(lambda value: value < 0, generator, num_runs=1)

        minimal_value = ctx.exception.minimal_inputs[0]
        self.assertGreaterEqual(minimal_value, 1)
        self.assertLessEqual(minimal_value, 5)


if __name__ == "__main__":
    unittest.main()
