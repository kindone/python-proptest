"""Unit tests for tag() / classify() / stat() and Property.assert_stat_*()."""

import io
import unittest

from python_proptest import Gen, Property, classify, stat, tag
from python_proptest.core.property import PropertyTestError


def _stream():
    """Return a StringIO-based write stream and accessor."""
    buf = io.StringIO()
    return buf, buf


class TestTagCollectionBasics(unittest.TestCase):

    def test_tag_records_key_value_in_summary(self):
        buf, stream = _stream()
        Property(
            lambda n: (tag("bucket", "high" if n > 50 else "low"), True)[-1]
        ).set_num_runs(100).set_seed("tag-basic").set_output_stream(stream).for_all(
            Gen.int(0, 100)
        )

        summary = buf.getvalue()
        self.assertIn("bucket:", summary)
        self.assertRegex(summary, r"high|low")

    def test_tag_is_noop_outside_property_run(self):
        # Must not crash when called outside an active context
        tag("k", "v")

    def test_classify_records_only_when_condition_true(self):
        buf, stream = _stream()
        Property(
            lambda n: (
                classify(n < 0, "sign", "negative"),
                classify(n >= 0, "sign", "non-negative"),
                True,
            )[-1]
        ).set_num_runs(200).set_seed("classify-test").set_output_stream(stream).for_all(
            Gen.int(-100, 100)
        )

        summary = buf.getvalue()
        self.assertIn("sign:", summary)
        self.assertIn("negative", summary)
        self.assertIn("non-negative", summary)

    def test_stat_records_bool_as_true_false(self):
        buf, stream = _stream()
        Property(lambda n: (stat("is_pos", n > 0), True)[-1]).set_num_runs(
            100
        ).set_seed("stat-basic").set_output_stream(stream).for_all(Gen.int(-10, 10))

        summary = buf.getvalue()
        self.assertIn("is_pos:", summary)
        self.assertRegex(summary, r"True|False")

    def test_no_summary_without_output_stream(self):
        # Should not raise even without output_stream
        Property(lambda n: (tag("x", n), True)[-1]).set_num_runs(20).for_all(
            Gen.int(0, 10)
        )

    def test_summary_not_printed_on_failure(self):
        buf, stream = _stream()
        with self.assertRaises(PropertyTestError):
            Property(lambda n: (tag("v", n), n < 5)[-1]).set_num_runs(
                100
            ).set_output_stream(stream).for_all(Gen.int(0, 10))
        # No summary should be printed on failure
        self.assertNotIn("v:", buf.getvalue())

    def test_multiple_tag_keys_in_summary(self):
        buf, stream = _stream()
        Property(
            lambda n: (
                tag("parity", "even" if n % 2 == 0 else "odd"),
                tag("sign", "pos" if n >= 0 else "neg"),
                True,
            )[-1]
        ).set_num_runs(50).set_seed("multi-tag").set_output_stream(stream).for_all(
            Gen.int(-10, 10)
        )

        summary = buf.getvalue()
        self.assertIn("parity:", summary)
        self.assertIn("sign:", summary)


class TestStatAssertions(unittest.TestCase):

    def test_assert_stat_ge_passes(self):
        # interval(-10, 10) → ~50% positive; bound 0.2 is safe
        Property(lambda n: (stat("pos", n > 0), True)[-1]).set_num_runs(200).set_seed(
            "ge-pass"
        ).assert_stat_ge("pos", 0.2).for_all(Gen.int(-10, 10))

    def test_assert_stat_ge_fails(self):
        # All negative → "pos" ratio = 0 < 0.5
        with self.assertRaises(PropertyTestError) as cm:
            Property(lambda n: (stat("pos", n > 0), True)[-1]).set_num_runs(
                100
            ).set_seed("ge-fail").assert_stat_ge("pos", 0.5).for_all(Gen.int(-100, -1))
        self.assertIn("assert_stat_ge", str(cm.exception))

    def test_assert_stat_le_passes(self):
        # All negative → "pos" ratio = 0 ≤ 0.1
        Property(lambda n: (stat("pos", n > 0), True)[-1]).set_num_runs(100).set_seed(
            "le-pass"
        ).assert_stat_le("pos", 0.1).for_all(Gen.int(-100, -1))

    def test_assert_stat_le_fails(self):
        # All positive → ratio = 1.0 > 0.5
        with self.assertRaises(PropertyTestError) as cm:
            Property(lambda n: (stat("pos", n > 0), True)[-1]).set_num_runs(
                100
            ).set_seed("le-fail").assert_stat_le("pos", 0.5).for_all(Gen.int(1, 100))
        self.assertIn("assert_stat_le", str(cm.exception))

    def test_assert_stat_in_range_passes(self):
        # interval(-10, 10) → ~50% positive; [0.2, 0.8] easily contains it
        Property(lambda n: (stat("pos", n > 0), True)[-1]).set_num_runs(300).set_seed(
            "range-pass"
        ).assert_stat_in_range("pos", 0.2, 0.8).for_all(Gen.int(-10, 10))

    def test_assert_stat_in_range_fails(self):
        # All positive → ratio = 1.0, range [0.1, 0.5] fails
        with self.assertRaises(PropertyTestError) as cm:
            Property(lambda n: (stat("pos", n > 0), True)[-1]).set_num_runs(
                100
            ).set_seed("range-fail").assert_stat_in_range("pos", 0.1, 0.5).for_all(
                Gen.int(1, 100)
            )
        self.assertIn("assert_stat_in_range", str(cm.exception))

    def test_failure_message_contains_key_and_bound(self):
        with self.assertRaises(PropertyTestError) as cm:
            Property(lambda n: (stat("is_big", n > 1000), True)[-1]).set_num_runs(
                100
            ).set_seed("msg-test").assert_stat_ge("is_big", 0.9).for_all(Gen.int(0, 10))
        msg = str(cm.exception)
        self.assertIn("is_big", msg)
        self.assertIn("0.9", msg)

    def test_multiple_assertions_all_reported(self):
        with self.assertRaises(PropertyTestError) as cm:
            Property(
                lambda n: (stat("big", n > 1000), stat("huge", n > 9000), True)[-1]
            ).set_num_runs(100).set_seed("multi-assert").assert_stat_ge(
                "big", 0.9
            ).assert_stat_ge(
                "huge", 0.5
            ).for_all(
                Gen.int(0, 10)
            )
        msg = str(cm.exception)
        self.assertIn("big", msg)
        self.assertIn("huge", msg)

    def test_stat_assertion_prints_summary_before_raising(self):
        buf, stream = _stream()
        try:
            Property(lambda n: (stat("pos", n > 0), True)[-1]).set_num_runs(
                100
            ).set_seed("summary-on-assert").set_output_stream(stream).assert_stat_ge(
                "pos", 0.9
            ).for_all(
                Gen.int(-100, -1)
            )
        except PropertyTestError:
            pass
        self.assertIn("pos:", buf.getvalue())

    def test_contexts_isolated_between_runs(self):
        buf1, stream1 = _stream()
        buf2, stream2 = _stream()

        Property(lambda n: (tag("run1", n > 5), True)[-1]).set_num_runs(50).set_seed(
            "iso1"
        ).set_output_stream(stream1).for_all(Gen.int(0, 10))

        Property(lambda _: True).set_num_runs(50).set_seed("iso2").set_output_stream(
            stream2
        ).for_all(Gen.int(0, 10))

        self.assertIn("run1:", buf1.getvalue())
        self.assertNotIn("run1:", buf2.getvalue())


if __name__ == "__main__":
    unittest.main()
