"""
Generator module for property-based testing.

This module contains generator implementations for various types,
separated from shrinker logic for better organization.
"""

# Combinator generators
from ..combinator import (
    ConstructGenerator,
    ElementOfGenerator,
    JustGenerator,
    LazyGenerator,
    OneOfGenerator,
)

# Aggregate generators
from .aggregate import AccumulateGenerator, AggregateGenerator

# Base Generator class and common utilities
from .base import (
    Generator,
    Random,
    Weighted,
    WeightedValue,
    is_weighted_generator,
    is_weighted_value,
    normalize_weighted_generators,
    normalize_weighted_values,
)
from .bool import BoolGenerator

# Chain generators
from .chain import ChainGenerator, ChainTupleGenerator
from .dict import DictGenerator
from .floating import FloatGenerator

# Gen class with static methods
from .gen import Gen

# Primitive generators
from .integral import IntGenerator, UnicodeCharGenerator

# Container generators
from .list import ListGenerator, UniqueListGenerator
from .set import SetGenerator
from .string import StringGenerator, UnicodeStringGenerator

# Transform generators
from .transform import FilteredGenerator, FlatMappedGenerator, MappedGenerator

__all__ = [
    # Base
    "Generator",
    "Random",
    "Weighted",
    "WeightedValue",
    "is_weighted_value",
    "is_weighted_generator",
    "normalize_weighted_values",
    "normalize_weighted_generators",
    # Transform
    "MappedGenerator",
    "FilteredGenerator",
    "FlatMappedGenerator",
    # Primitives
    "IntGenerator",
    "UnicodeCharGenerator",
    "BoolGenerator",
    "FloatGenerator",
    "StringGenerator",
    "UnicodeStringGenerator",
    # Containers
    "ListGenerator",
    "UniqueListGenerator",
    "SetGenerator",
    "DictGenerator",
    # Combinators
    "OneOfGenerator",
    "ElementOfGenerator",
    "JustGenerator",
    "LazyGenerator",
    "ConstructGenerator",
    # Chain
    "ChainGenerator",
    "ChainTupleGenerator",
    # Aggregate
    "AggregateGenerator",
    "AccumulateGenerator",
    # Gen
    "Gen",
]
