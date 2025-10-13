"""
PyPropTest - Python Property-Based Testing Library

A clean, Pythonic property-based testing library with seamless pytest integration.
"""

from .core.property import run_for_all, Property, PropertyTestError
from .core.generator import Generator, Gen
from .core.shrinker import Shrinkable
from .core.stream import Stream
from .core.option import Option, Some, None_, none
from .core.either import Either, Left, Right
from .core.try_ import Try, Success, Failure, attempt
from .core.stateful import (
    SimpleAction, Action, StatefulProperty,
    simpleActionGenOf, actionGenOf, statefulProperty, simpleStatefulProperty
)
from .core.decorators import (
    for_all, given, example, settings, assume, note, run_property_test,
    Strategy, integers, floats, text, lists, dictionaries, one_of, just
)

__version__ = "0.1.0"
__author__ = "kindone"
__email__ = "kindone@example.com"

__all__ = [
    "for_all",
    "run_for_all",
    "Property",
    "PropertyTestError",
    "Generator",
    "Gen",
    "Shrinkable",
    "Stream",
    "Option",
    "Some",
    "None_",
    "none",
    "Either",
    "Left",
    "Right",
    "Try",
    "Success",
    "Failure",
    "attempt",
    "SimpleAction",
    "Action",
    "StatefulProperty",
    "simpleActionGenOf",
    "actionGenOf",
    "statefulProperty",
    "simpleStatefulProperty",
    "given",
    "example",
    "settings",
    "assume",
    "note",
    "run_property_test",
    "Strategy",
    "integers",
    "floats",
    "text",
    "lists",
    "dictionaries",
    "one_of",
    "just",
]
