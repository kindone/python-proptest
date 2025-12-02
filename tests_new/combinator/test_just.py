"""Unit tests for ``python_proptest.core.combinator.just``."""

import unittest

from python_proptest import Gen, run_for_all


class TestJust(unittest.TestCase):
    """Verify behaviour of the ``Gen.just`` combinator."""

    def test_produces_constant_values(self):
        """Generated values always equal the provided constant."""

        const_gen = Gen.just(42)

        run_for_all(lambda x: x == 42, const_gen, num_runs=50)

    def test_supports_various_types(self):
        """Values keep identity and type across common Python structures."""

        test_cases = [
            42,
            "hello",
            True,
            3.14,
            [1, 2, 3],
            {"key": "value"},
        ]

        for value in test_cases:
            generator = Gen.just(value)

            def property_under_test(sample):
                return sample == value and type(sample) is type(value)

            run_for_all(property_under_test, generator, num_runs=20)


if __name__ == "__main__":
    unittest.main()
