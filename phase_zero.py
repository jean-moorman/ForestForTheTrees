"""
Phase Zero - Feedback and Analysis for Phase One

This module has been refactored into a package structure for better maintainability.
All components are re-exported here for backward compatibility.
"""

from phase_zero.orchestrator import PhaseZeroOrchestrator
from phase_zero.base import BaseAnalysisAgent, AnalysisState, MetricsSnapshot

from phase_zero.agents.monitoring import MonitoringAgent
from phase_zero.agents.description_analysis import SunAgent, ShadeAgent, WindAgent
from phase_zero.agents.requirement_analysis import SoilAgent, MicrobialAgent, RainAgent
from phase_zero.agents.data_flow import RootSystemAgent, MycelialAgent, WormAgent
from phase_zero.agents.structural import InsectAgent, BirdAgent, TreeAgent
from phase_zero.agents.optimization import PollinatorAgent
from phase_zero.agents.synthesis import EvolutionAgent

from phase_zero.validation.earth import validate_guideline_update
from phase_zero.validation.water import coordinate_agents

__all__ = [
    # Core orchestrator
    'PhaseZeroOrchestrator',
    
    # Base classes and utilities
    'BaseAnalysisAgent',
    'AnalysisState',
    'MetricsSnapshot',
    
    # Agents
    'MonitoringAgent',
    'SunAgent',
    'ShadeAgent',
    'WindAgent',
    'SoilAgent',
    'MicrobialAgent',
    'RainAgent',
    'RootSystemAgent',
    'MycelialAgent',
    'WormAgent',
    'InsectAgent',
    'BirdAgent',
    'TreeAgent',
    'PollinatorAgent',
    'EvolutionAgent',
    
    # Validation mechanisms
    'validate_guideline_update',
    'coordinate_agents'
]