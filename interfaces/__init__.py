"""
Interfaces package for FFTT system.
Provides interface classes for agents, components, features, and functionalities.
"""

# Errors
from .errors import (
    InterfaceError, 
    InitializationError, 
    StateTransitionError, 
    ResourceError, 
    ValidationError,
    TimeoutError
)

# Base interface
from .base import BaseInterface

# Agent interfaces
from .agent import AgentInterface, AgentState

# Component, feature and functionality interfaces
from .component import ComponentInterface
from .feature import FeatureInterface, FunctionalityInterface

# Testing tools
from .testing import TestAgent

# Agent coordination
from .agent.coordination import CoordinationInterface

# Phase interfaces
from .phase_interfaces import PhaseZeroInterface

__all__ = [
    # Errors
    'InterfaceError', 'InitializationError', 'StateTransitionError', 
    'ResourceError', 'ValidationError', 'TimeoutError',
    
    # Interfaces
    'BaseInterface', 'AgentInterface', 'AgentState',
    'ComponentInterface', 'FeatureInterface', 'FunctionalityInterface',
    
    # Coordination
    'CoordinationInterface',
    
    # Phase interfaces
    'PhaseZeroInterface',
    
    # Testing
    'TestAgent'
]

__version__ = '0.1.0'