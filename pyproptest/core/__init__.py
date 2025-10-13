"""Core components of PyPropTest."""

from .generator import Generator, Gen
from .property import Property, run_for_all
from .shrinker import Shrinkable

__all__ = ["Generator", "Gen", "Property", "run_for_all", "Shrinkable"]
