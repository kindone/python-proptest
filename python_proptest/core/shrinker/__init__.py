"""
Shrinker module for property-based testing.

This module contains shrinker implementations for various types,
separated from generator logic for better organization.
"""

from typing import Any, Callable, Generic, List, Optional, TypeVar

from ..stream import Stream

T = TypeVar("T")
U = TypeVar("U")


class Shrinkable(Generic[T]):
    """A value with its shrinking candidates."""

    def __init__(
        self,
        value: T,
        shrinks_gen: Optional[Callable[[], Stream["Shrinkable[T]"]]] = None,
    ):
        self.value = value
        self.shrinks_gen = shrinks_gen or (lambda: Stream.empty())

    def __repr__(self) -> str:
        return f"Shrinkable({self.value!r})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Shrinkable):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)

    def shrinks(self) -> Stream["Shrinkable[T]"]:
        """Get the shrinking candidates as a stream."""
        return self.shrinks_gen()

    def with_shrinks(
        self, shrink_func: Callable[[], Stream["Shrinkable[T]"]]
    ) -> "Shrinkable[T]":
        """Add shrinking candidates using a function that returns a stream."""
        return Shrinkable(self.value, shrink_func)

    def concat_static(
        self, shrink_func: Callable[[], Stream["Shrinkable[T]"]]
    ) -> "Shrinkable[T]":
        """Add static shrinking candidates."""

        def combined_shrinks() -> Stream["Shrinkable[T]"]:
            return self.shrinks().concat(shrink_func())

        return Shrinkable(self.value, combined_shrinks)

    def concat(
        self, shrink_func: Callable[["Shrinkable[T]"], Stream["Shrinkable[T]"]]
    ) -> "Shrinkable[T]":
        """
        Add shrinking candidates that depend on the current value.

        Matches cppproptest's concat behavior:
        - Recursively applies concat to each shrink in the stream
        - Concatenates the result of shrink_func(self) to the stream
        """

        def combined_shrinks() -> Stream["Shrinkable[T]"]:
            # Transform each shrink in the current stream by recursively applying concat
            transformed_shrinks = self.shrinks().map(
                lambda shrink: shrink.concat(shrink_func)
            )
            # Concatenate the result of shrink_func(self) to the transformed stream
            return transformed_shrinks.concat(shrink_func(self))

        return Shrinkable(self.value, combined_shrinks)

    def and_then_static(
        self, shrink_func: Callable[[], Stream["Shrinkable[T]"]]
    ) -> "Shrinkable[T]":
        """Replace shrinking candidates with new ones."""
        return Shrinkable(self.value, shrink_func)

    def and_then(
        self, shrink_func: Callable[["Shrinkable[T]"], Stream["Shrinkable[T]"]]
    ) -> "Shrinkable[T]":
        """
        Replace shrinking candidates with new ones that depend on the current value.

        Matches cppproptest's andThen behavior:
        - If current shrinks are empty, applies shrink_func to self
        - Otherwise, recursively applies and_then to each shrink in the stream
        """
        current_shrinks = self.shrinks()
        if current_shrinks.is_empty():
            return Shrinkable(self.value, lambda: shrink_func(self))
        else:

            def transformed_shrinks() -> Stream["Shrinkable[T]"]:
                return current_shrinks.map(lambda shrink: shrink.and_then(shrink_func))

            return Shrinkable(self.value, transformed_shrinks)

    def map(self, func: Callable[[T], U]) -> "Shrinkable[U]":
        """Transform the value and all shrinking candidates."""

        def mapped_shrinks() -> Stream["Shrinkable[U]"]:
            return self.shrinks().map(lambda shrink: shrink.map(func))

        return Shrinkable(func(self.value), mapped_shrinks)

    def filter(self, predicate: Callable[[T], bool]) -> "Shrinkable[T]":
        """Filter shrinking candidates based on a predicate."""
        if not predicate(self.value):
            raise ValueError("Cannot filter out the root value")

        def filtered_shrinks() -> Stream["Shrinkable[T]"]:
            return (
                self.shrinks()
                .filter(lambda shrink: predicate(shrink.value))
                .map(lambda shrink: shrink.filter(predicate))
            )

        return Shrinkable(self.value, filtered_shrinks)

    def flat_map(self, func: Callable[[T], "Shrinkable[U]"]) -> "Shrinkable[U]":
        """Transform the value and flatten the result."""
        result = func(self.value)

        def flat_mapped_shrinks() -> Stream["Shrinkable[U]"]:
            return (
                self.shrinks()
                .map(lambda shrink: shrink.flat_map(func))
                .concat(result.shrinks())
            )

        return Shrinkable(result.value, flat_mapped_shrinks)

    def get_nth_child(self, index: int) -> "Shrinkable[T]":
        """Get the nth shrinking candidate."""
        if index < 0:
            raise IndexError(f"Index {index} out of range for shrinks")

        shrinks_stream = self.shrinks()
        current = shrinks_stream
        for i in range(index):
            if current.is_empty():
                raise IndexError(f"Index {index} out of range for shrinks")
            current = current.tail()

        if current.is_empty():
            raise IndexError(f"Index {index} out of range for shrinks")

        head_val = current.head()
        if head_val is None:
            raise IndexError(f"Index {index} out of range for shrinks")
        return head_val

    def retrieve(self, path: List[int]) -> "Shrinkable[T]":
        """Retrieve a shrinkable by following a path of indices."""
        if not path:
            return self

        current = self
        for index in path:
            current = current.get_nth_child(index)
        return current

    def take(self, n: int) -> "Shrinkable[T]":
        """Limit the number of shrinking candidates to n."""

        def limited_shrinks() -> Stream["Shrinkable[T]"]:
            return self.shrinks().take(n)

        return Shrinkable(self.value, limited_shrinks)


# Import legacy classes and functions from shrinker.py for backward compatibility
# We use importlib to load shrinker.py directly since there's a naming conflict
# (both shrinker.py file and shrinker/ package exist)
import importlib.util
import os

from .bool import shrink_bool  # noqa: E402
from .floating import shrink_float  # noqa: E402

# Import shrinker functions (must be after Shrinkable definition to avoid circular imports)
from .integral import binary_search_shrinkable, shrink_integral  # noqa: E402
from .list import (  # noqa: E402
    shrink_array_length,
    shrink_dict,
    shrink_element_wise,
    shrink_list,
    shrink_membership_wise,
    shrink_set,
    shrinkable_array,
)
from .pair import shrink_pair  # noqa: E402
from .string import shrink_string, shrink_unicode_string  # noqa: E402
from .tuple import shrink_tuple  # noqa: E402

_shrinker_file_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "shrinker.py"
)
if os.path.exists(_shrinker_file_path):
    import sys

    _spec = importlib.util.spec_from_file_location(
        "python_proptest.core.shrinker_file", _shrinker_file_path
    )
    if _spec is None or _spec.loader is None:
        raise ImportError(f"Could not load spec from {_shrinker_file_path}")
    _shrinker_file_module = importlib.util.module_from_spec(_spec)
    # Set up the module's package and name for proper imports
    _shrinker_file_module.__package__ = "python_proptest.core"
    _shrinker_file_module.__name__ = "python_proptest.core.shrinker_file"

    # The shrinker.py file tries to do "from .shrinker import Shrinkable"
    # We need to make sure this import works. Since we're in the shrinker package's __init__.py,
    # we can create a temporary module object that the relative import will find.
    # Actually, the relative import ".shrinker" will resolve to this package (python_proptest.core.shrinker)
    # So we need to make sure this package is in sys.modules and has Shrinkable

    # Save current state
    _old_shrinker_in_sys = "python_proptest.core.shrinker" in sys.modules

    # Make sure this package is in sys.modules (it should be, since we're executing it)
    # and that it has Shrinkable available
    # The shrinker.py file will import from this package, so Shrinkable should already be available

    # Also set Shrinkable and Stream directly in the module namespace as a fallback
    _shrinker_file_module.Shrinkable = Shrinkable  # type: ignore[attr-defined]
    from ..stream import Stream as StreamClass

    _shrinker_file_module.Stream = StreamClass  # type: ignore[attr-defined]

    # Now execute the module - the "from .shrinker import Shrinkable" should work
    # because this package (python_proptest.core.shrinker) is in sys.modules
    if _spec.loader is not None:
        _spec.loader.exec_module(_shrinker_file_module)

    # Export the classes and functions
    Shrinker = _shrinker_file_module.Shrinker
    IntegerShrinker = _shrinker_file_module.IntegerShrinker
    StringShrinker = _shrinker_file_module.StringShrinker
    ListShrinker = _shrinker_file_module.ListShrinker
    DictShrinker = _shrinker_file_module.DictShrinker
    shrink_to_minimal = _shrinker_file_module.shrink_to_minimal
    shrinkable_boolean = _shrinker_file_module.shrinkable_boolean
    shrinkable_float = _shrinker_file_module.shrinkable_float
else:
    # Fallback: define as None if file doesn't exist
    Shrinker = None
    IntegerShrinker = None
    StringShrinker = None
    ListShrinker = None
    DictShrinker = None
    shrink_to_minimal = None
    shrinkable_boolean = None
    shrinkable_float = None

__all__ = [
    "Shrinkable",
    "shrink_integral",
    "binary_search_shrinkable",
    "shrink_float",
    "shrink_bool",
    "shrink_string",
    "shrink_unicode_string",
    "shrink_list",
    "shrink_set",
    "shrink_dict",
    "shrink_pair",
    "shrink_tuple",
    "shrinkable_array",
    "shrink_membership_wise",
    "shrink_element_wise",
    "shrink_array_length",
    # Legacy exports
    "Shrinker",
    "IntegerShrinker",
    "StringShrinker",
    "ListShrinker",
    "DictShrinker",
    "shrink_to_minimal",
    "shrinkable_boolean",
    "shrinkable_float",
]
