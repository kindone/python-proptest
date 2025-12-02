"""Tests for ``python_proptest.core.generator.dict``."""

import unittest

from python_proptest import Gen, PropertyTestError, run_for_all


class TestDictGenerator(unittest.TestCase):
    """Validate dictionary generator behaviour."""

    def test_dict_respects_key_value_generators(self):
        """Generated dictionaries obey key/value constraints."""

        generator = Gen.dict(
            Gen.str(min_length=1, max_length=2),
            Gen.int(min_value=0, max_value=5),
            min_size=0,
            max_size=3,
        )

        def predicate(value):
            if not isinstance(value, dict) or not (0 <= len(value) <= 3):
                return False
            return all(
                isinstance(key, str)
                and 1 <= len(key) <= 2
                and isinstance(val, int)
                and 0 <= val <= 5
                for key, val in value.items()
            )

        run_for_all(predicate, generator, num_runs=200)

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
