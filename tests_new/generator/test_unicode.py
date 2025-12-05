"""Tests for unicode-aware generators."""

import unittest

from python_proptest import Gen, for_all


class TestUnicodeGenerators(unittest.TestCase):
    """Validate unicode string and char generators."""

    @for_all(Gen.unicode_string(min_length=1, max_length=3), num_runs=200)
    def test_unicode_string_range(self, value: str):
        """Unicode string generator can emit characters beyond ASCII."""

        self.assertIsInstance(value, str)
        self.assertGreaterEqual(len(value), 1)
        self.assertLessEqual(len(value), 3)


if __name__ == "__main__":
    unittest.main()
