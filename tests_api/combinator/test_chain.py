"""Tests for ``python_proptest.core.generator.chain`` helpers and behaviour."""

import unittest

from python_proptest import Gen, PropertyTestError, for_all, run_for_all


class TestChainCombinator(unittest.TestCase):
    """Validate chain combinator across declarative and fluent APIs."""

    def test_simple_chain_static_api_function_style(self):
        """run_for_all handles chain defined via static API helper."""

        def days_in_month(month: int) -> int:
            return [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]

        date_gen = Gen.chain(
            Gen.int(1, 12),
            lambda month: Gen.int(1, days_in_month(month)),
        )

        @run_for_all(date_gen, num_runs=20)
        def check_valid_date(date_tuple):
            self.assertIsInstance(date_tuple, tuple)
            self.assertEqual(len(date_tuple), 2)
            month, day = date_tuple
            self.assertGreaterEqual(month, 1)
            self.assertLessEqual(month, 12)
            self.assertGreaterEqual(day, 1)
            self.assertLessEqual(day, days_in_month(month))

    @for_all(
        Gen.chain(
            Gen.int(1, 12),
            lambda month: Gen.int(
                1, [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
            ),
        ),
        num_runs=20,
    )
    def test_simple_chain_static_api(self, date_tuple):
        """Decorator form keeps dependencies between chained values."""

        self.assertIsInstance(date_tuple, tuple)
        self.assertEqual(len(date_tuple), 2)
        month, day = date_tuple
        self.assertGreaterEqual(month, 1)
        self.assertLessEqual(month, 12)
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        self.assertGreaterEqual(day, 1)
        self.assertLessEqual(day, days_in_month[month - 1])

    def test_fluent_chain_api(self):
        """Fluent ``Gen.chain`` maintains dependency ordering."""

        chained_gen = Gen.int(1, 10).chain(lambda x: Gen.int(x, x + 10))

        @run_for_all(chained_gen, num_runs=15)
        def check_chain_dependency(pair):
            self.assertIsInstance(pair, tuple)
            base, dependent = pair
            self.assertGreaterEqual(base, 1)
            self.assertLessEqual(base, 10)
            self.assertGreaterEqual(dependent, base)
            self.assertLessEqual(dependent, base + 10)

    def test_multiple_chaining(self):
        """Nested chaining builds larger tuples while preserving constraints."""

        triple_gen = Gen.chain(
            Gen.chain(Gen.int(1, 5), lambda width: Gen.int(width, width + 5)),
            lambda width_height: Gen.int(1, width_height[0] * width_height[1]),
        )

        @run_for_all(triple_gen, num_runs=10)
        def check_triple_dependency(triple):
            width, height, area = triple
            self.assertGreaterEqual(width, 1)
            self.assertLessEqual(width, 5)
            self.assertGreaterEqual(height, width)
            self.assertLessEqual(height, width + 5)
            self.assertGreaterEqual(area, 1)
            self.assertLessEqual(area, width * height)

    def test_chain_with_other_generators(self):
        """Chaining across heterogeneous generator types stays consistent."""

        string_gen = Gen.chain(
            Gen.int(3, 10),
            lambda length: Gen.str(min_length=length, max_length=length),
        )

        @run_for_all(string_gen, num_runs=10)
        def check_string_length(pair):
            length, string_value = pair
            self.assertEqual(len(string_value), length)
            self.assertGreaterEqual(length, 3)
            self.assertLessEqual(length, 10)

    def test_chain_with_complex_dependencies(self):
        """Dependent collection sizes follow upstream values while shrinking."""

        list_gen = Gen.chain(
            Gen.int(2, 5),
            lambda size: Gen.list(Gen.int(0, 100), min_length=size, max_length=size),
        )

        @run_for_all(list_gen, num_runs=10)
        def check_list_size(result):
            size, generated_list = result
            self.assertEqual(len(generated_list), size)
            self.assertGreaterEqual(size, 2)
            self.assertLessEqual(size, 5)
            for element in generated_list:
                self.assertGreaterEqual(element, 0)
                self.assertLessEqual(element, 100)

    def test_shrinking_maintains_dependencies(self):
        """Shrinking candidates stay within derived bounds."""

        def days_in_month(month: int) -> int:
            return [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]

        date_gen = Gen.chain(
            Gen.int(1, 12), lambda month: Gen.int(1, days_in_month(month))
        )

        with self.assertRaises(PropertyTestError) as ctx:
            run_for_all(lambda _: False, date_gen, num_runs=1)

        error = ctx.exception
        self.assertIsNotNone(error.minimal_inputs)
        minimal_month, minimal_day = error.minimal_inputs[0]

        self.assertGreaterEqual(minimal_month, 1)
        self.assertLessEqual(minimal_month, 12)
        self.assertGreaterEqual(minimal_day, 1)
        self.assertLessEqual(minimal_day, days_in_month(minimal_month))

    def test_chain_preserves_single_value_generators(self):
        """Chaining from ``Gen.just`` keeps the anchor value intact."""

        constant_chain = Gen.chain(Gen.just(42), lambda x: Gen.int(x, x + 10))

        run_for_all(
            lambda pair: pair[0] == 42 and 42 <= pair[1] <= 52,
            constant_chain,
            num_runs=30,
        )

    def test_nested_tuple_chaining(self):
        """Chaining on tuple outputs appends trailing dependent value."""

        base_tuple_gen = Gen.tuple(Gen.int(1, 5), Gen.int(1, 5))
        extended_gen = Gen.chain(
            base_tuple_gen,
            lambda pair: Gen.int(pair[0] + pair[1], pair[0] + pair[1] + 10),
        )

        @run_for_all(extended_gen, num_runs=10)
        def check_nested_tuple(triple):
            first, second, third = triple
            expected_min = first + second
            expected_max = first + second + 10
            self.assertGreaterEqual(third, expected_min)
            self.assertLessEqual(third, expected_max)

    def test_property_based_chain_validation(self):
        """run_for_all returns True when predicate holds for all samples."""

        def validate_chain(pair):
            x, y = pair
            return y >= x

        run_for_all(
            validate_chain,
            Gen.chain(Gen.int(1, 50), lambda value: Gen.int(value, value + 20)),
            num_runs=50,
        )

    def test_chain_with_for_all_decorator(self):
        """@for_all decorated helper executes immediately when invoked."""

        @for_all(Gen.chain(Gen.int(1, 10), lambda value: Gen.int(value * 2, value * 3)))
        def property_under_test(self, pair):
            x, y = pair
            self.assertGreaterEqual(y, x * 2)
            self.assertLessEqual(y, x * 3)

        property_under_test(self)

    def test_error_handling(self):
        """Invalid dependent ranges should raise during generation."""

        invalid_gen = Gen.chain(
            Gen.int(1, 10),
            lambda value: Gen.int(value + 100, value),
        )

        with self.assertRaises(PropertyTestError) as ctx:
            run_for_all(lambda value: True, invalid_gen, num_runs=1)

        self.assertIsInstance(ctx.exception.__cause__, ValueError)

    def test_chain_type_consistency(self):
        """Conditional branches maintain declared output types."""

        mixed_chain = Gen.chain(
            Gen.bool(),
            lambda predicate: Gen.int(0, 1) if predicate else Gen.int(10, 20),
        )

        def property_under_test(value):
            boolean, integer = value
            if not isinstance(boolean, bool):
                return False
            if not isinstance(integer, int):
                return False
            if boolean:
                return integer in (0, 1)
            return 10 <= integer <= 20

        run_for_all(property_under_test, mixed_chain, num_runs=60)

    def test_long_chain_sequence(self):
        """Extended fluent chaining maintains monotonic dependencies."""

        def build_long_chain():
            generator = Gen.int(1, 3)
            generator = generator.chain(lambda x: Gen.int(x, x + 2))
            generator = generator.chain(lambda xy: Gen.int(xy[1], xy[1] + 2))
            generator = generator.chain(lambda xyz: Gen.int(xyz[2], xyz[2] + 2))
            generator = generator.chain(lambda xyzw: Gen.int(xyzw[3], xyzw[3] + 2))
            return generator

        long_gen = build_long_chain()

        def property_under_test(value):
            a, b, c, d, e = value
            return (
                len(value) == 5
                and a <= b <= a + 2
                and b <= c <= b + 2
                and c <= d <= c + 2
                and d <= e <= d + 2
            )

        run_for_all(property_under_test, long_gen, num_runs=60)


if __name__ == "__main__":
    unittest.main()
