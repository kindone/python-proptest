import unittest

from python_proptest import Gen, example, for_all, settings


class TestDecoratorCombinations(unittest.TestCase):
    def test_order_example_settings_for_all(self):
        counter = {"n": 0}

        @example(5)
        @settings(num_runs=10, seed=123)
        @for_all(Gen.int())
        def prop(x: int):
            counter["n"] += 1
            assert isinstance(x, int)

        prop()
        # examples run in addition to num_runs
        assert counter["n"] == 11

    def test_order_settings_example_for_all(self):
        seen = []

        @settings(num_runs=5, seed=456)
        @example(1)
        @for_all(Gen.int())
        def prop(x: int):
            seen.append(x)
            assert isinstance(x, int)

        prop()
        # examples run in addition to num_runs
        assert len(seen) == 6
        assert 1 in seen  # example ran

    def test_for_all_with_example_and_settings(self):
        hits = []

        @for_all(Gen.int())
        @example(7)
        @settings(num_runs=8, seed=789)
        def prop(x: int):
            hits.append(x)
            assert isinstance(x, int)

        prop()
        # examples run in addition to num_runs
        assert len(hits) == 9
        assert 7 in hits

    def test_multiple_settings_last_wins(self):
        count = {"n": 0}

        @for_all(Gen.int())
        @settings(num_runs=3)
        @settings(num_runs=6)
        def prop(x: int):
            count["n"] += 1
            assert isinstance(x, int)

        prop()
        # When stacking @settings above @for_all, the one closest to @for_all applies
        assert count["n"] == 3

    def test_unittest_method_with_example_and_settings(self):
        class C(unittest.TestCase):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.seen = []

            @for_all(Gen.int())
            @example(11)
            @settings(num_runs=4, seed=321)
            def test_m(self, x: int):
                self.seen.append(x)
                self.assertIsInstance(x, int)

        c = C()
        c.test_m()
        # examples run in addition to num_runs
        assert len(c.seen) == 5
        assert 11 in c.seen

    def test_pytest_style_method_with_example_and_settings(self):
        class C:
            def __init__(self):
                self.seen = []

            @for_all(Gen.int())
            @example(13)
            @settings(num_runs=5, seed=654)
            def test_m(self, x: int):
                self.seen.append(x)
                assert isinstance(x, int)

        c = C()
        c.test_m()
        # examples run in addition to num_runs
        assert len(c.seen) == 6
        assert 13 in c.seen

    def test_generator_mix(self):
        # Using generators with filters
        ints = Gen.int().filter(lambda x: True)
        strs = Gen.str(min_length=0, max_length=3)
        seen = []

        @for_all(ints, strs)
        @settings(num_runs=7, seed=111)
        @example(0, "")
        def prop(x: int, s: str):
            seen.append((x, s))
            assert isinstance(x, int) and isinstance(s, str)

        prop()
        # examples run in addition to num_runs
        assert len(seen) == 8
        assert (0, "") in seen

    def test_example_failure_preempts_random_runs_in_methods(self):
        class C(unittest.TestCase):
            @for_all(Gen.int())
            @example(0)
            @settings(num_runs=50)
            def test_m(self, x: int):
                assert x > 0

        c = C()
        with self.assertRaises(AssertionError) as _:
            c.test_m()


if __name__ == "__main__":
    unittest.main()
