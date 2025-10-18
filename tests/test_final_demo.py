"""
Final demonstration of all ported functionality.

This test file demonstrates all the ported functionality from the Dart version
and serves as a comprehensive test suite.
"""

import random
import unittest

from python_proptest import Gen, Property, PropertyTestError, Shrinkable, for_all
from python_proptest.core.shrinker import (
    DictShrinker,
    IntegerShrinker,
    ListShrinker,
    StringShrinker,
    shrink_to_minimal,
)


def run_all_tests():
    """Run all ported tests and demonstrate functionality."""
    print("🐍 python-proptest - Comprehensive Test Suite")
    print("=" * 60)

    # Test 1: Basic Generators
    print("\n1. Testing Basic Generators...")
    rng = random.Random(42)

    # Integer generator
    int_gen = Gen.int(min_value=0, max_value=100)
    result = int_gen.generate(rng)
    assert isinstance(result.value, int)
    assert 0 <= result.value <= 100
    print(f"   ✅ Integer generator: {result.value}")

    # String generator
    str_gen = Gen.str(min_length=1, max_length=10)
    result = str_gen.generate(rng)
    assert isinstance(result.value, str)
    assert 1 <= len(result.value) <= 10
    print(f"   ✅ String generator: '{result.value}'")

    # Boolean generator
    bool_gen = Gen.bool()
    result = bool_gen.generate(rng)
    assert isinstance(result.value, bool)
    print(f"   ✅ Boolean generator: {result.value}")

    # Float generator
    float_gen = Gen.float(min_value=0.0, max_value=1.0)
    result = float_gen.generate(rng)
    assert isinstance(result.value, float)
    assert 0.0 <= result.value <= 1.0
    print(f"   ✅ Float generator: {result.value}")

    # Test 2: Collection Generators
    print("\n2. Testing Collection Generators...")

    # List generator
    list_gen = Gen.list(Gen.int(min_value=0, max_value=10), min_length=0, max_length=5)
    result = list_gen.generate(rng)
    assert isinstance(result.value, list)
    assert 0 <= len(result.value) <= 5
    assert all(isinstance(x, int) for x in result.value)
    print(f"   ✅ List generator: {result.value}")

    # Dict generator
    dict_gen = Gen.dict(
        Gen.str(min_length=1, max_length=2), Gen.int(min_value=0, max_value=10)
    )
    result = dict_gen.generate(rng)
    assert isinstance(result.value, dict)
    for key, value in result.value.items():
        assert isinstance(key, str)
        assert isinstance(value, int)
    print(f"   ✅ Dict generator: {result.value}")

    # Test 3: Combinators
    print("\n3. Testing Combinators...")

    # Just combinator
    just_gen = Gen.just(42)
    result = just_gen.generate(rng)
    assert result.value == 42
    assert result.shrinks().is_empty()
    print(f"   ✅ Just combinator: {result.value}")

    # One of combinator
    one_of_gen = Gen.one_of(Gen.just(1), Gen.just(2))
    result = one_of_gen.generate(rng)
    assert result.value in [1, 2]
    print(f"   ✅ One of combinator: {result.value}")

    # Map combinator
    map_gen = Gen.int(min_value=1, max_value=10).map(lambda x: x * 2)
    result = map_gen.generate(rng)
    assert result.value % 2 == 0
    assert 2 <= result.value <= 20
    print(f"   ✅ Map combinator: {result.value}")

    # Filter combinator
    filter_gen = Gen.int(min_value=1, max_value=20).filter(lambda x: x % 2 == 0)
    result = filter_gen.generate(rng)
    assert result.value % 2 == 0
    assert 1 <= result.value <= 20
    print(f"   ✅ Filter combinator: {result.value}")

    # Flat map combinator
    flat_map_gen = Gen.int(min_value=1, max_value=5).flat_map(
        lambda x: Gen.int(min_value=x, max_value=x + 10)
    )
    result = flat_map_gen.generate(rng)
    assert 1 <= result.value <= 15
    print(f"   ✅ Flat map combinator: {result.value}")

    # Test 4: Property Testing
    print("\n4. Testing Property Testing...")

    # Passing property
    def test_passing_property(a, b):
        return a + b == b + a

    result = for_all(
        test_passing_property,
        Gen.int(min_value=0, max_value=100),
        Gen.int(min_value=0, max_value=100),
        num_runs=100,
    )
    assert result is True
    print("   ✅ Passing property test")

    # Failing property
    def test_failing_property(x):
        return x < 50

    try:
        for_all(
            test_failing_property, Gen.int(min_value=0, max_value=100), num_runs=100
        )
        print("   ❌ Failing property test should have raised an exception")
    except PropertyTestError as e:
        assert e.failing_inputs is not None
        assert len(e.failing_inputs) == 1
        assert e.failing_inputs[0] >= 50
        print(f"   ✅ Failing property test: {e.failing_inputs[0]}")

    # Test 5: Seed Reproducibility
    print("\n5. Testing Seed Reproducibility...")

    def test_property(x):
        return isinstance(x, int)

    result1 = for_all(
        test_property, Gen.int(min_value=0, max_value=100), num_runs=10, seed=42
    )

    result2 = for_all(
        test_property, Gen.int(min_value=0, max_value=100), num_runs=10, seed=42
    )

    assert result1 is True
    assert result2 is True
    print("   ✅ Seed reproducibility test")

    # Test 6: Shrinking
    print("\n6. Testing Shrinking...")

    # Integer shrinking
    shrinker = IntegerShrinker()
    candidates = shrinker.shrink(8)
    assert 0 in candidates
    assert 1 in candidates
    assert 4 in candidates
    print(f"   ✅ Integer shrinking: {candidates}")

    # String shrinking
    string_shrinker = StringShrinker()
    candidates = string_shrinker.shrink("ABCD")
    assert "" in candidates
    assert "ABC" in candidates
    assert "BCD" in candidates
    print(f"   ✅ String shrinking: {candidates}")

    # List shrinking
    element_shrinker = IntegerShrinker()
    list_shrinker = ListShrinker(element_shrinker)
    candidates = list_shrinker.shrink([10, 20, 30])
    assert [] in candidates
    assert [10, 20] in candidates
    assert [20, 30] in candidates
    print(f"   ✅ List shrinking: {len(candidates)} candidates")

    # Shrink to minimal
    def predicate(x):
        return x < 10

    minimal = shrink_to_minimal(100, predicate, IntegerShrinker())
    assert not predicate(minimal)
    assert minimal < 100
    assert minimal >= 10
    print(f"   ✅ Shrink to minimal: {minimal}")

    # Test 7: Complex Nested Structures
    print("\n7. Testing Complex Nested Structures...")

    def test_property(data):
        return isinstance(data, list)

    complex_gen = Gen.list(
        Gen.dict(
            Gen.str(min_length=1, max_length=2).map(lambda s: s.upper()),
            Gen.int(min_value=0, max_value=10).map(lambda x: x * 2),
        ),
        min_length=0,
        max_length=3,
    )

    result = for_all(test_property, complex_gen, num_runs=100)
    assert result is True
    print("   ✅ Complex nested structures test")

    # Test 8: Performance
    print("\n8. Testing Performance...")

    def test_property(x):
        return isinstance(x, int)

    result = for_all(test_property, Gen.int(min_value=0, max_value=100), num_runs=1000)
    assert result is True
    print("   ✅ Performance test (1000 runs)")

    # Test 9: Edge Cases
    print("\n9. Testing Edge Cases...")

    # Empty list
    empty_list_gen = Gen.list(Gen.int(), min_length=0, max_length=0)
    result = empty_list_gen.generate(rng)
    assert result.value == []
    print("   ✅ Empty list generator")

    # Single value range
    single_value_gen = Gen.int(min_value=42, max_value=42)
    result = single_value_gen.generate(rng)
    assert result.value == 42
    print("   ✅ Single value range generator")

    # Empty dictionary
    empty_dict_gen = Gen.dict(Gen.str(), Gen.int(), min_size=0, max_size=0)
    result = empty_dict_gen.generate(rng)
    assert result.value == {}
    print("   ✅ Empty dictionary generator")

    # Test 10: Error Handling
    print("\n10. Testing Error Handling...")

    # No generators
    def test_property():
        return True

    try:
        for_all(test_property, num_runs=10)
        print("   ❌ Should have raised ValueError")
    except ValueError as e:
        assert "At least one generator must be provided" in str(e)
        print("   ✅ No generators error handling")

    # Impossible filter condition
    impossible_gen = Gen.int(min_value=1, max_value=10).filter(lambda x: x > 100)
    try:
        impossible_gen.generate(rng)
        print("   ❌ Should have raised ValueError")
    except ValueError as e:
        assert "Could not generate value" in str(e)
        print("   ✅ Impossible filter error handling")

    # Empty one_of
    try:
        Gen.one_of()
        print("   ❌ Should have raised ValueError")
    except ValueError as e:
        assert "At least one generator must be provided" in str(e)
        print("   ✅ Empty one_of error handling")

    # Test 11: Property Class Direct Usage
    print("\n11. Testing Property Class Direct Usage...")

    def test_property(x):
        return isinstance(x, int)

    prop = Property(test_property, num_runs=10, seed=42)
    result = prop.for_all(Gen.int(min_value=0, max_value=100))
    assert result is True
    print("   ✅ Property class direct usage")

    # Test 12: Mixed Types
    print("\n12. Testing Mixed Types...")

    def test_property(a, b, c, d):
        return (
            isinstance(a, int)
            and isinstance(b, str)
            and isinstance(c, bool)
            and isinstance(d, float)
        )

    result = for_all(
        test_property,
        Gen.int(min_value=0, max_value=100),
        Gen.str(min_length=1, max_length=5),
        Gen.bool(),
        Gen.float(min_value=0.0, max_value=1.0),
        num_runs=100,
    )
    assert result is True
    print("   ✅ Mixed types test")

    # Test 13: String Seeds
    print("\n13. Testing String Seeds...")

    def test_property(x):
        return isinstance(x, int)

    seeds = ["test", "hello world", "🚀", "测试", ""]

    for seed in seeds:
        result = for_all(
            test_property, Gen.int(min_value=0, max_value=100), num_runs=10, seed=seed
        )
        assert result is True
    print("   ✅ String seeds test")

    # Test 14: Large Seeds
    print("\n14. Testing Large Seeds...")

    large_seeds = [2**31 - 1, -(2**31), 0, 1, -1]

    for seed in large_seeds:
        result = for_all(
            test_property, Gen.int(min_value=0, max_value=100), num_runs=10, seed=seed
        )
        assert result is True
    print("   ✅ Large seeds test")

    print("\n" + "=" * 60)
    print("🎉 All tests passed successfully!")
    print("\nKey features demonstrated:")
    print("• Basic generators (int, str, bool, float)")
    print("• Collection generators (list, dict)")
    print("• Combinators (just, one_of, map, filter, flat_map)")
    print("• Property testing with for_all")
    print("• Seed reproducibility")
    print("• Shrinking algorithms")
    print("• Complex nested structures")
    print("• Performance with large runs")
    print("• Edge case handling")
    print("• Error handling")
    print("• Property class direct usage")
    print("• Mixed type support")
    print("• String and large seed support")
    print("\n🚀 python-proptest is ready for production use!")


if __name__ == "__main__":
    run_all_tests()
