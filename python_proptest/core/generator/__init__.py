"""
Generator module for property-based testing.

This module contains generator implementations for various types,
separated from shrinker logic for better organization.
"""

# Base Generator class and common utilities
from .base import (
    Generator,
    Random,
    Weighted,
    WeightedValue,
    is_weighted_value,
    is_weighted_generator,
    normalize_weighted_values,
    normalize_weighted_generators,
)

# Transform generators
from .transform import (
    MappedGenerator,
    FilteredGenerator,
    FlatMappedGenerator,
)

# Primitive generators
from .integral import IntGenerator, UnicodeCharGenerator
from .bool import BoolGenerator
from .floating import FloatGenerator
from .string import StringGenerator, UnicodeStringGenerator

# Container generators
from .list import ListGenerator, UniqueListGenerator
from .set import SetGenerator
from .dict import DictGenerator

# Combinator generators
from .combinators import (
    OneOfGenerator,
    ElementOfGenerator,
    JustGenerator,
    LazyGenerator,
    ConstructGenerator,
)

# Chain generators
from .chain import ChainGenerator, ChainTupleGenerator

# Aggregate generators
from .aggregate import (
    AggregateGenerator,
    AccumulateGenerator,
)

# Gen class with static methods
from .gen import Gen

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

