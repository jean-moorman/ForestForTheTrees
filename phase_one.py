"""
Phase One module for Forest For The Trees (FFTT).

This module coordinates the phase one processes, which handle
the initial foundation and structural design of the software project.

Note: This file has been refactored to use the phase_one package.
"""
import logging

# Re-export all components from the phase_one package
from phase_one import (
    # Enums
    DevelopmentState,
    PhaseValidationState,
    
    # Data models
    MonitoringFeedback,
    AnalysisFeedback,
    EvolutionFeedback,
    RefinementContext,
    AgentPromptConfig,
    CircuitBreakerDefinition,
    
    # Agents
    ReflectiveAgent,
    GardenPlannerAgent,
    EarthAgent,
    EnvironmentalAnalysisAgent,
    RootSystemArchitectAgent,
    TreePlacementPlannerAgent,
    
    # Validation
    PhaseOneValidator,
    PhaseZeroInterface,
    GardenPlannerValidator,
    
    # Workflow
    PhaseOneWorkflow
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Improve backward compatibility
__all__ = [
    'DevelopmentState',
    'PhaseValidationState',
    'MonitoringFeedback',
    'AnalysisFeedback',
    'EvolutionFeedback',
    'RefinementContext',
    'AgentPromptConfig',
    'CircuitBreakerDefinition',
    'ReflectiveAgent',
    'GardenPlannerAgent',
    'EarthAgent',
    'EnvironmentalAnalysisAgent',
    'RootSystemArchitectAgent',
    'TreePlacementPlannerAgent',
    'PhaseOneValidator',
    'PhaseZeroInterface',
    'GardenPlannerValidator',
    'PhaseOneWorkflow',
    'SequentialAgentCoordinator',
]