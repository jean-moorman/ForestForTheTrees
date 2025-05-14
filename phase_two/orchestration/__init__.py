"""
Phase Two Orchestration Package
============================

This package provides enhanced orchestration capabilities for Phase Two,
extending the core functionality in the main orchestrator.py file.

Key components:
- ComponentProcessingOrchestrator: Manages component processing pipeline
- DependencyResolver: Enhanced dependency resolution and management
- FeatureDefinitionGenerator: Generates feature definitions from components
- ComponentBuildTracker: Tracks build progress and component state
- PhaseResourceManager: Manages resources for phase execution
"""

from phase_two.orchestration.processor import ComponentProcessingOrchestrator
from phase_two.orchestration.dependencies import DependencyResolver
from phase_two.orchestration.features import FeatureDefinitionGenerator
from phase_two.orchestration.tracking import ComponentBuildTracker
from phase_two.orchestration.resources import PhaseResourceManager

__all__ = [
    'ComponentProcessingOrchestrator',
    'DependencyResolver',
    'FeatureDefinitionGenerator',
    'ComponentBuildTracker',
    'PhaseResourceManager'
]