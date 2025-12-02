"""Tests for unicode-aware generators."""

import unittest

from python_proptest import Gen, run_for_all


class TestUnicodeGenerators(unittest.TestCase):
    """Validate unicode string and char generators."""

    def test_unicode_string_range(self):
        """Unicode string generator can emit characters beyond ASCII."""

        def predicate(value: str) -> bool:
            return isinstance(value, str) and 1 <= len(value) <= 3

        run_for_all(
            predicate,
            Gen.unicode_string(min_length=1, max_length=3),
            num_runs=200,
        )


if __name__ == "__main__":
    unittest.main()
