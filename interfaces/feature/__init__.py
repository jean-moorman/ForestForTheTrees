"""
Feature interface module for the FFTT system.
Provides interfaces for feature and functionality management.
"""

from .interface import FeatureInterface
from .functionality import FunctionalityInterface

__all__ = [
    'FeatureInterface',
    'FunctionalityInterface'
]