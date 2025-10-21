#!/usr/bin/env python
"""Demo of aggregate and accumulate generator combinators.

This script demonstrates the new aggregate and accumulate features
ported from cppproptest2.
"""

import random
from python_proptest import Gen


def demo_aggregate():
    """Demonstrate Gen.aggregate() - returns list of dependent values."""
    print("=" * 70)
    print("AGGREGATE DEMO: Generate lists with dependent elements")
    print("=" * 70)

    # Example 1: Increasing sequence
    print("\n1. Increasing sequence (each >= previous):")
    gen = Gen.aggregate(
        Gen.int(0, 10), lambda n: Gen.int(n, n + 5), min_size=5, max_size=8
    )
    for i in range(3):
        result = gen.generate(random.Random()).value
        print(f"   Sample {i+1}: {result}")

    # Example 2: Random walk
    print("\n2. Bounded random walk (±10 steps):")
    gen = Gen.aggregate(
        Gen.int(50, 50),  # Start at 50
        lambda pos: Gen.int(max(0, pos - 10), min(100, pos + 10)),
        min_size=10,
        max_size=15,
    )
    for i in range(3):
        result = gen.generate(random.Random()).value
        print(f"   Sample {i+1}: {result}")

    # Example 3: Fluent API
    print("\n3. Strictly increasing (fluent API):")
    gen = Gen.int(0, 5).aggregate(
        lambda n: Gen.int(n + 1, n + 10), min_size=4, max_size=7
    )
    for i in range(3):
        result = gen.generate(random.Random()).value
        print(f"   Sample {i+1}: {result}")


def demo_accumulate():
    """Demonstrate Gen.accumulate() - returns only final value."""
    print("\n" + "=" * 70)
    print("ACCUMULATE DEMO: Generate final value after N steps")
    print("=" * 70)

    # Example 1: Random walk - final position
    print("\n1. Random walk final position (10-20 steps):")
    gen = Gen.accumulate(
        Gen.int(50, 50),
        lambda pos: Gen.int(max(0, pos - 5), min(100, pos + 5)),
        min_size=10,
        max_size=20,
    )
    for i in range(5):
        result = gen.generate(random.Random()).value
        print(f"   Sample {i+1}: Final position = {result}")

    # Example 2: Compound growth
    print("\n2. Compound growth (5-10 steps, 1-10% each):")
    gen = Gen.accumulate(
        Gen.float(100.0, 100.0),
        lambda amount: Gen.float(amount * 1.01, amount * 1.1),
        min_size=5,
        max_size=10,
    )
    for i in range(5):
        result = gen.generate(random.Random()).value
        print(f"   Sample {i+1}: Final amount = ${result:.2f}")

    # Example 3: Fluent API
    print("\n3. Strictly increasing (fluent API):")
    gen = Gen.int(0, 10).accumulate(
        lambda n: Gen.int(n + 1, n + 5), min_size=10, max_size=15
    )
    for i in range(5):
        result = gen.generate(random.Random()).value
        print(f"   Sample {i+1}: Final value = {result}")


def demo_comparison():
    """Compare aggregate vs accumulate with same configuration."""
    print("\n" + "=" * 70)
    print("COMPARISON: aggregate vs accumulate")
    print("=" * 70)

    print("\nSame generator factory, different results:\n")

    # Aggregate: returns all intermediate values
    print("Aggregate (returns all steps):")
    agg_gen = Gen.aggregate(
        Gen.int(0, 5), lambda n: Gen.int(n, n + 3), min_size=5, max_size=5
    )
    result = agg_gen.generate(random.Random()).value
    print(f"   Result (list): {result}")
    print(f"   Length: {len(result)}")

    # Accumulate: returns only final value
    print("\nAccumulate (returns final only):")
    acc_gen = Gen.accumulate(
        Gen.int(0, 5), lambda n: Gen.int(n, n + 3), min_size=5, max_size=5
    )
    result = acc_gen.generate(random.Random()).value
    print(f"   Result (single): {result}")
    print(f"   Type: {type(result).__name__}")


def demo_integration():
    """Demonstrate integration with other generators."""
    print("\n" + "=" * 70)
    print("INTEGRATION: Combining with chain and other generators")
    print("=" * 70)

    # Chain with aggregate
    print("\n1. Chain: base value -> aggregate from it:")
    gen = Gen.int(1, 5).chain(
        lambda n: Gen.aggregate(
            Gen.int(n, n), lambda x: Gen.int(x, x + 5), min_size=3, max_size=5
        )
    )
    for i in range(3):
        base, sequence = gen.generate(random.Random()).value
        print(f"   Sample {i+1}: base={base}, sequence={sequence}")

    # List of accumulated values
    print("\n2. List of accumulate results:")
    gen = Gen.list(
        Gen.accumulate(
            Gen.int(0, 10), lambda n: Gen.int(n, n + 5), min_size=3, max_size=5
        ),
        min_length=3,
        max_length=5,
    )
    for i in range(3):
        result = gen.generate(random.Random()).value
        print(f"   Sample {i+1}: {result}")


if __name__ == "__main__":
    demo_aggregate()
    demo_accumulate()
    demo_comparison()
    demo_integration()

    print("\n" + "=" * 70)
    print("✨ Demo complete! ✨")
    print("=" * 70)
