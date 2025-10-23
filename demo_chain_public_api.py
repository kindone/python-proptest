#!/usr/bin/env python3
"""
Demo showing the chain combinator in the public API.

This demonstrates that Gen.chain() is available through the public API
and works as expected for creating dependent tuple generation.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import random

# Import from public API
from python_proptest import Gen, for_all, run_for_all


def demo_public_api_access():
    """Demonstrate that chain is available through public API."""
    print("🔗 Chain Combinator Public API Demo")
    print("=" * 40)

    # 1. Static API - Gen.chain()
    print("\n1. Static API Usage:")
    print("   Gen.chain(base_gen, lambda x: dependent_gen)")

    def days_in_month(month):
        days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        return days[month - 1]

    date_gen = Gen.chain(
        Gen.int(1, 12),  # month
        lambda month: Gen.int(1, days_in_month(month)),  # valid day
    )

    rng = random.Random(42)
    for i in range(5):
        month, day = date_gen.generate(rng).value
        print(
            f"   Generated date: {month:2d}/{day:2d} (month {month} has {days_in_month(month)} days)"
        )

    # 2. Fluent API - gen.chain()
    print("\n2. Fluent API Usage:")
    print("   base_gen.chain(lambda x: dependent_gen)")

    range_gen = Gen.int(5, 15).chain(lambda start: Gen.int(start, start + 10))

    for i in range(5):
        start, end = range_gen.generate(rng).value
        print(f"   Generated range: [{start:2d}, {end:2d}] (span: {end - start})")

    # 3. Multiple chaining
    print("\n3. Multiple Chaining:")
    print("   Chain multiple dependencies to create longer tuples")

    coord_gen = Gen.chain(
        Gen.chain(Gen.int(0, 10), lambda x: Gen.int(x, x + 5)),  # x  # y >= x
        lambda xy: Gen.int(0, xy[0] + xy[1]),  # z <= x + y
    )

    for i in range(5):
        x, y, z = coord_gen.generate(rng).value
        print(f"   Generated coords: ({x}, {y}, {z}) where y >= x and z <= x+y")

    # 4. Integration with property-based testing
    print("\n4. Property-Based Testing Integration:")

    def test_rectangle_area_property(rect_tuple):
        width, height = rect_tuple
        area = width * height
        return area >= width and area >= height

    rect_gen = Gen.chain(
        Gen.int(1, 20), lambda w: Gen.int(w, w + 10)  # width  # height >= width
    )

    result = run_for_all(test_rectangle_area_property, rect_gen, num_runs=20)

    print(f"   Rectangle area property test: {'✅ PASSED' if result else '❌ FAILED'}")

    # 5. Using with @for_all decorator
    print("\n5. Decorator Integration:")

    @for_all(Gen.chain(Gen.int(1, 10), lambda x: Gen.int(x * 2, x * 3)))
    def test_scaling_property(pair):
        """Test that the second value is between 2x and 3x the first."""
        x, y = pair
        return 2 * x <= y <= 3 * x

    print("   @for_all with chain combinator:")
    try:
        test_scaling_property()
        print("   ✅ Scaling property test PASSED")
    except Exception as e:
        print(f"   ❌ Scaling property test FAILED: {e}")

    print("\n🎉 Chain combinator is fully integrated into the public API!")


if __name__ == "__main__":
    demo_public_api_access()
