# This file is now a wrapper around the refactored phase_three package
# It maintains backward compatibility with existing code

from phase_three.interface import PhaseThreeInterface
from phase_three.models import (
    FeatureDevelopmentState,
    FeaturePerformanceMetrics,
    FeaturePerformanceScore,
    FeatureDevelopmentContext
)
from phase_three.development import ParallelFeatureDevelopment
from phase_three.agents import (
    FeatureElaborationAgent,
    FeatureTestSpecAgent,
    FeatureIntegrationAgent,
    FeaturePerformanceAgent
)
from phase_three.phase_zero import (
    FeatureRequirementsAnalysisAgent,
    FeatureImplementationAnalysisAgent,
    FeatureEvolutionAgent
)
from phase_three.evolution import NaturalSelectionAgent

# Re-export all the original classes for backward compatibility
__all__ = [
    'PhaseThreeInterface',
    'FeatureDevelopmentState',
    'FeaturePerformanceMetrics',
    'FeaturePerformanceScore',
    'FeatureDevelopmentContext',
    'ParallelFeatureDevelopment',
    'FeatureElaborationAgent',
    'FeatureTestSpecAgent',
    'FeatureIntegrationAgent',
    'FeaturePerformanceAgent',
    'FeatureRequirementsAnalysisAgent',
    'FeatureImplementationAnalysisAgent',
    'FeatureEvolutionAgent',
    'NaturalSelectionAgent'
]