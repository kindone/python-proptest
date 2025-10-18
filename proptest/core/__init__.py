"""Core components of python-proptest."""

from .generator import Gen, Generator
from .property import Property, run_for_all
from .shrinker import Shrinkable

__all__ = ["Generator", "Gen", "Property", "run_for_all", "Shrinkable"]
