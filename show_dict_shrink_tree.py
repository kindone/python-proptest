#!/usr/bin/env python3
"""Visualize dictionary shrink tree structure."""

import random

from python_proptest import Gen


def visualize_shrink_tree(
    shrinkable, max_depth=3, indent=0, prefix="", max_children=10
):
    """Visualize shrink tree in a readable format."""
    value_str = str(shrinkable.value)
    if len(value_str) > 80:
        value_str = value_str[:77] + "..."
    print(f"{' ' * indent}{prefix}{value_str}")

    if indent // 2 >= max_depth:
        return

    children = shrinkable.shrinks().to_list()[:max_children]
    for i, child in enumerate(children):
        is_last = i == len(children) - 1
        child_prefix = "└─ " if is_last else "├─ "
        visualize_shrink_tree(child, max_depth, indent + 2, child_prefix, max_children)


def main():
    # Generate a dictionary with a fixed seed
    rng = random.Random(42)
    dict_gen = Gen.dict(
        Gen.str(min_length=1, max_length=3),
        Gen.int(min_value=1, max_value=10),
        min_size=2,
        max_size=3,
    )

    shrinkable = dict_gen.generate(rng)

    print("Dictionary Shrink Tree (from Gen.dict):")
    print("=" * 80)
    visualize_shrink_tree(shrinkable, max_depth=3, max_children=8)
    print("=" * 80)
    print(f"\nRoot value: {shrinkable.value}")
    print(f"Type: {type(shrinkable.value)}")
    print(
        f"Number of immediate shrink candidates: {len(shrinkable.shrinks().to_list())}"
    )

    # Show what types of shrinks are available
    children = shrinkable.shrinks().to_list()
    if children:
        print("\nFirst 10 shrink candidates:")
        for i, child in enumerate(children[:10]):
            print(f"  {i+1}. {child.value}")

    # Now show the shrink_dict function directly
    print("\n" + "=" * 80)
    print("Dictionary Shrink Tree (using shrink_dict directly):")
    print("=" * 80)

    from python_proptest.core.shrinker.integral import shrink_integral
    from python_proptest.core.shrinker.list import shrink_dict

    # Create a dict with known key-value pairs
    key_shrinkables = [
        shrink_integral(10, min_value=0, max_value=20),
        shrink_integral(30, min_value=20, max_value=40),
    ]
    value_shrinkables = [
        shrink_integral(5, min_value=0, max_value=10),
        shrink_integral(8, min_value=0, max_value=10),
    ]

    shrinkable2 = shrink_dict(key_shrinkables, value_shrinkables, min_size=0)

    visualize_shrink_tree(shrinkable2, max_depth=2, max_children=8)
    print("=" * 80)
    print(f"\nRoot value: {shrinkable2.value}")
    print(
        f"Number of immediate shrink candidates: {len(shrinkable2.shrinks().to_list())}"
    )

    children2 = shrinkable2.shrinks().to_list()
    if children2:
        print("\nAll immediate shrink candidates:")
        for i, child in enumerate(children2):
            print(f"  {i+1}. {child.value}")


if __name__ == "__main__":
    main()
