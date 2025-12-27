#!/usr/bin/env python3
"""
Simple test to verify chain combinator works correctly.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import random

from python_proptest.core.generator import Gen


def test_simple_chain():
    """Test basic chain functionality."""
    print("Testing simple chain combinator...")

    # Create a simple chain: generate month, then valid day for that month
    def days_in_month(month):
        days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        return days[month - 1]

    # Chain month generator with day generator
    date_gen = Gen.chain(
        Gen.int(1, 12),  # month
        lambda month: Gen.int(1, days_in_month(month)),  # valid day for month
    )

    # Test generation
    rng = random.Random(42)  # Fixed seed for reproducible test

    for i in range(10):
        shrinkable = date_gen.generate(rng)
        month, day = shrinkable.value

        print(f"Generated: month={month}, day={day}")

        # Verify the relationship is maintained
        assert 1 <= month <= 12, f"Invalid month: {month}"
        assert 1 <= day <= days_in_month(month), f"Invalid day {day} for month {month}"

    print("✓ Simple chain test passed!")


def test_fluent_chain():
    """Test fluent API chain functionality."""
    print("Testing fluent chain API...")

    # Test fluent chaining
    base_gen = Gen.int(1, 10)
    chained_gen = base_gen.chain(lambda x: Gen.int(x, x + 10))

    rng = random.Random(123)

    for i in range(5):
        shrinkable = chained_gen.generate(rng)
        base_val, dependent_val = shrinkable.value

        print(f"Generated: base={base_val}, dependent={dependent_val}")

        # Verify dependency
        assert (
            base_val <= dependent_val <= base_val + 10
        ), f"Dependency violated: {base_val} -> {dependent_val}"

    print("✓ Fluent chain test passed!")


def test_multiple_chains():
    """Test chaining multiple times."""
    print("Testing multiple chains...")

    # Chain multiple times to create a 3-tuple
    datetime_gen = Gen.chain(
        Gen.chain(
            Gen.int(1, 12),  # month
            lambda month: Gen.int(1, 28),  # day (simplified to 28 max)
        ),
        lambda date_tuple: Gen.int(0, 23),  # hour
    )

    rng = random.Random(456)

    for i in range(3):
        shrinkable = datetime_gen.generate(rng)
        month, day, hour = shrinkable.value

        print(f"Generated: month={month}, day={day}, hour={hour}")

        # Verify all components
        assert 1 <= month <= 12, f"Invalid month: {month}"
        assert 1 <= day <= 28, f"Invalid day: {day}"
        assert 0 <= hour <= 23, f"Invalid hour: {hour}"

    print("✓ Multiple chains test passed!")


if __name__ == "__main__":
    try:
        test_simple_chain()
        test_fluent_chain()
        test_multiple_chains()
        print("\n🎉 All chain tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
