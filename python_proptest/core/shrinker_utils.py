"""
Utility functions for working with shrink trees.

This module provides helper functions for visualizing and analyzing shrink trees.
"""

import json
from typing import Any, Dict, List, TypeVar

from .shrinker import Shrinkable

T = TypeVar("T")


def collect_tree_compact(
    node: Shrinkable[T],
    depth: int = 0,
    max_depth: int = 10,
    breadth: int = 50,
) -> List[Any]:
    """
    Collect a shrink tree into a compact nested array format.

    The format is [value, [children]], where children is always a list
    (empty [] if no children). This ensures:
    - Each value appears exactly once in the tree
    - The structure is hierarchical and easy to parse
    - No duplicates are implied

    Args:
        node: The root Shrinkable node
        depth: Current depth in the tree (used internally)
        max_depth: Maximum depth to traverse
        breadth: Maximum number of children to explore at each level

    Returns:
        A nested list structure: [value, [child1, child2, ...]]
        where each child is also [value, [children]]

    Example:
        For Gen.int(0, 8) with value 8:
        [8, [
          [0, []],
          [4, [
            [2, [[1, []]]],
            [3, []]
          ]],
          [6, [[5, []]]],
          [7, []]
        ]]
    """
    children = []
    if depth < max_depth:
        current = node.shrinks()
        count = 0
        while count < breadth and not current.is_empty():
            head = current.head()
            if head is None:
                break
            children.append(collect_tree_compact(head, depth + 1, max_depth, breadth))
            current = current.tail()
            count += 1

    return [node.value, children]


def collect_tree_structured(
    node: Shrinkable[T],
    depth: int = 0,
    max_depth: int = 10,
    breadth: int = 50,
) -> Dict[str, Any]:
    """
    Collect a shrink tree into a structured dictionary format.

    The format is {"value": v, "shrinks": [children]}, where shrinks
    is only included if there are children. This provides:
    - Clear labeling of values and shrinks
    - Self-documenting structure
    - Easy to parse and understand

    Args:
        node: The root Shrinkable node
        depth: Current depth in the tree (used internally)
        max_depth: Maximum depth to traverse
        breadth: Maximum number of children to explore at each level

    Returns:
        A dictionary structure: {"value": v, "shrinks": [child1, child2, ...]}
        where each child is also {"value": v, "shrinks": [...]}

    Example:
        For Gen.int(0, 8) with value 8:
        {
          "value": 8,
          "shrinks": [
            {"value": 0},
            {
              "value": 4,
              "shrinks": [
                {"value": 2, "shrinks": [{"value": 1}]},
                {"value": 3}
              ]
            },
            {"value": 6, "shrinks": [{"value": 5}]},
            {"value": 7}
          ]
        }
    """
    result: dict[str, Any] = {"value": node.value}

    if depth < max_depth:
        children = []
        current = node.shrinks()
        count = 0
        while count < breadth and not current.is_empty():
            head = current.head()
            if head is None:
                break
            children.append(
                collect_tree_structured(head, depth + 1, max_depth, breadth)
            )
            current = current.tail()
            count += 1

        if children:
            result["shrinks"] = children

    return result


def tree_to_json(
    node: Shrinkable[T],
    max_depth: int = 10,
    breadth: int = 50,
    indent: int = 2,
) -> str:
    """
    Convert a shrink tree to a JSON string representation (compact format).

    Args:
        node: The root Shrinkable node
        max_depth: Maximum depth to traverse
        breadth: Maximum number of children to explore at each level
        indent: JSON indentation level

    Returns:
        A JSON string representing the shrink tree in compact format
    """
    tree = collect_tree_compact(node, max_depth=max_depth, breadth=breadth)
    return json.dumps(tree, indent=indent)


def tree_to_json_structured(
    node: Shrinkable[T],
    max_depth: int = 10,
    breadth: int = 50,
    indent: int = 2,
) -> str:
    """
    Convert a shrink tree to a JSON string representation (structured format).

    Uses {"value": v, "shrinks": [...]} format for better readability.

    Args:
        node: The root Shrinkable node
        max_depth: Maximum depth to traverse
        breadth: Maximum number of children to explore at each level
        indent: JSON indentation level

    Returns:
        A JSON string representing the shrink tree in structured format
    """
    tree = collect_tree_structured(node, max_depth=max_depth, breadth=breadth)
    return json.dumps(tree, indent=indent)


def check_duplicates(
    node: Shrinkable[T],
    max_depth: int = 10,
    breadth: int = 50,
) -> Dict[str, List[int]]:
    """
    Check for duplicate values in a shrink tree.

    Returns a dictionary mapping value strings to lists of depths
    where they appear. If a value appears multiple times, it will
    be in the result with multiple depth entries.

    Args:
        node: The root Shrinkable node
        max_depth: Maximum depth to traverse
        breadth: Maximum number of children to explore at each level

    Returns:
        Dictionary mapping value strings to lists of depths
    """
    seen: dict[str, List[int]] = {}

    def traverse(n: Shrinkable[T], d: int = 0):
        value_key = json.dumps(n.value, sort_keys=True)
        if value_key not in seen:
            seen[value_key] = []
        seen[value_key].append(d)

        if d < max_depth:
            current = n.shrinks()
            count = 0
            while count < breadth and not current.is_empty():
                head = current.head()
                if head is None:
                    break
                traverse(head, d + 1)
                current = current.tail()
                count += 1

    traverse(node)
    return {k: v for k, v in seen.items() if len(v) > 1}
