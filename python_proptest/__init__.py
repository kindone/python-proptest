"""
python-proptest - Python Property-Based Testing Library

A clean, Pythonic property-based testing library with seamless pytest integration.
"""

from .core.decorators import (
    assume,
    example,
    for_all,
    matrix,
    note,
    run_property_test,
    settings,
)
from .core.either import Either, Left, Right
from .core.generator import Gen, Generator
from .core.option import None_, Option, Some, none
from .core.property import Property, PropertyTestError, run_for_all, run_matrix
from .core.shrinker import Shrinkable
from .core.stateful import (
    Action,
    SimpleAction,
    StatefulProperty,
    actionGenOf,
    simpleActionGenOf,
    simpleStatefulProperty,
    statefulProperty,
)
from .core.stream import Stream
from .core.try_ import Failure, Success, Try, attempt

__version__ = "0.1.4"
__author__ = "kindone"
__email__ = "jradoo@gmail.com"

__all__ = [
    "for_all",
    "run_for_all",
    "run_matrix",
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
    "example",
    "matrix",
    "settings",
    "assume",
    "note",
    "run_property_test",
]
