"""Tests for ``python_proptest.core.generator.dict``."""

import unittest

from python_proptest import Gen, PropertyTestError, for_all, run_for_all


class TestDictGenerator(unittest.TestCase):
    """Validate dictionary generator behaviour."""

    @for_all(
        Gen.dict(
            Gen.str(min_length=1, max_length=2),
            Gen.int(min_value=0, max_value=5),
            min_size=0,
            max_size=3,
        ),
        num_runs=200,
    )
    def test_dict_respects_key_value_generators(self, value):
        """Generated dictionaries obey key/value constraints."""

        self.assertIsInstance(value, dict)
        self.assertLessEqual(len(value), 3)
        for key, val in value.items():
            self.assertIsInstance(key, str)
            self.assertGreaterEqual(len(key), 1)
            self.assertLessEqual(len(key), 2)
            self.assertIsInstance(val, int)
            self.assertGreaterEqual(val, 0)
            self.assertLessEqual(val, 5)

    def test_dict_zero_min_size_allows_empty(self):
        """Zero minimum size lets failing property shrink to empty dict."""

        generator = Gen.dict(
            Gen.str(min_length=1, max_length=2),
            Gen.int(min_value=0, max_value=5),
            min_size=0,
            max_size=3,
        )

        with self.assertRaises(PropertyTestError) as ctx:
            run_for_all(lambda value: False, generator, num_runs=1)

        self.assertEqual(ctx.exception.minimal_inputs[0], {})


if __name__ == "__main__":
    unittest.main()
