"""
Standardized schemas for event payloads and other data structures.

This module provides dataclasses for consistent payload structures across
the FFTT system, enabling type checking and validation.
"""
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

# Event Types for Component and Feature analysis
class AnalysisEventTypes:
    """Event types for component and feature analysis"""
    # Component-level events
    COMPONENT_VALIDATION_COMPLETE = "COMPONENT_VALIDATION_COMPLETE"
    COMPONENT_PROPAGATION_COMPLETE = "COMPONENT_PROPAGATION_COMPLETE"
    COMPONENT_ANALYSIS_COMPLETE = "COMPONENT_ANALYSIS_COMPLETE"
    
    # Feature-level events
    FEATURE_VALIDATION_COMPLETE = "FEATURE_VALIDATION_COMPLETE"
    FEATURE_PROPAGATION_COMPLETE = "FEATURE_PROPAGATION_COMPLETE"
    FEATURE_ANALYSIS_COMPLETE = "FEATURE_ANALYSIS_COMPLETE"


@dataclass
class BaseEventPayload:
    """Base class for all event payloads with common fields."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""  # Agent/component that emitted event


@dataclass
class ValidationEventPayload(BaseEventPayload):
    """Payload for Earth agent validation events."""
    validation_id: str = ""
    agent_id: str = ""
    is_valid: bool = False
    validation_category: str = "undefined"
    detected_issues: List[Dict[str, Any]] = field(default_factory=list)
    tier: str = ""  # component, feature, functionality
    corrected_update: Optional[Dict[str, Any]] = None
    context: Dict[str, Any] = field(default_factory=dict)




@dataclass
class ValidationStateChangedPayload(BaseEventPayload):
    """Payload for Phase One validation state change events."""
    old_state: str = ""
    new_state: str = ""
    context_id: Optional[str] = None
    error_count: int = 0
    responsible_agent: Optional[str] = None


@dataclass
class RefinementContextPayload(BaseEventPayload):
    """Payload for refinement context events."""
    context_id: str = ""
    phase_id: str = ""
    validation_state: str = ""
    responsible_agent: Optional[str] = None
    error_count: int = 0
    state: str = ""  # created, updated, cleaned_up
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RefinementIterationPayload(BaseEventPayload):
    """Payload for refinement iteration events."""
    context_id: str = ""
    iteration_number: int = 0
    refinement_type: str = ""  # refinement, reflection, revision
    success: bool = False
    duration_seconds: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentUpdateRequestPayload(BaseEventPayload):
    """Payload for agent update request events."""
    agent_id: str = ""
    update_type: str = ""  # guideline, component, feature, etc.
    content: Dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    priority: int = 0

# Phase Two payload schemas
@dataclass
class ComponentEventPayload(BaseEventPayload):
    """Payload for Phase Two component events."""
    component_id: str = ""
    component_name: str = ""
    dependency_ids: List[str] = field(default_factory=list)
    operation_type: str = ""  # created, updated
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestEventPayload(BaseEventPayload):
    """Payload for Phase Two test events."""
    test_id: str = ""
    component_id: str = ""
    test_type: str = ""  # unit, integration, system
    status: str = ""  # created, passed, failed
    execution_time: float = 0.0
    failure_details: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegrationEventPayload(BaseEventPayload):
    """Payload for Phase Two integration events."""
    integration_id: str = ""
    component_ids: List[str] = field(default_factory=list)
    status: str = ""  # started, completed, failed
    issues: List[Dict[str, Any]] = field(default_factory=list)
    duration_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

# Phase Three payload schemas
@dataclass
class FeatureEventPayload(BaseEventPayload):
    """Payload for Phase Three feature events."""
    feature_id: str = ""
    component_id: str = ""
    feature_name: str = ""
    version: int = 1
    event_type: str = ""  # requested, created, evolved, integrated
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationEventPayload(BaseEventPayload):
    """Payload for Phase Three optimization events."""
    optimization_id: str = ""
    feature_ids: List[str] = field(default_factory=list)
    iteration: int = 0
    metrics: Dict[str, float] = field(default_factory=dict)
    changes: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeatureIntegrationPayload(BaseEventPayload):
    """Payload for Phase Three feature integration events."""
    integration_id: str = ""
    component_id: str = ""
    feature_ids: List[str] = field(default_factory=list)
    status: str = ""  # started, completed, failed
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    resolution_strategy: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

# Component and Feature schema definitions
@dataclass
class ComponentGuidelineSchema:
    """Schema for component guidelines."""
    component_id: str
    component_name: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    features: List[Dict[str, Any]] = field(default_factory=list)
    data_flow: Dict[str, Any] = field(default_factory=dict)
    interfaces: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeatureGuidelineSchema:
    """Schema for feature guidelines."""
    feature_id: str
    feature_name: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    functionality: List[Dict[str, Any]] = field(default_factory=list)
    implementation: Dict[str, Any] = field(default_factory=dict)
    test_criteria: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComponentAnalysisSchema(BaseEventPayload):
    """Schema for component analysis results."""
    component_id: str = ""
    description_analysis: Dict[str, Any] = field(default_factory=dict)
    requirements_analysis: Dict[str, Any] = field(default_factory=dict)
    data_flow_analysis: Dict[str, Any] = field(default_factory=dict)
    structure_analysis: Dict[str, Any] = field(default_factory=dict)
    evolution_synthesis: Dict[str, Any] = field(default_factory=dict)
    operation_id: str = ""


@dataclass
class FeatureAnalysisSchema(BaseEventPayload):
    """Schema for feature analysis results."""
    feature_id: str = ""
    requirements_analysis: Dict[str, Any] = field(default_factory=dict)
    implementation_analysis: Dict[str, Any] = field(default_factory=dict)
    evolution_analysis: Dict[str, Any] = field(default_factory=dict)
    operation_id: str = ""


# Phase Four payload schemas
@dataclass
class CodeGenerationPayload(BaseEventPayload):
    """Payload for Phase Four code generation events."""
    feature_id: str = ""
    functionality_id: str = ""
    generation_status: str = ""  # started, completed, failed
    compiler_status: Dict[str, str] = field(default_factory=dict)
    iteration: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompilationPayload(BaseEventPayload):
    """Payload for Phase Four compilation events."""
    feature_id: str = ""
    functionality_id: str = ""
    compiler_type: str = ""  # formatting, style, logic, type, security
    status: str = ""  # started, passed, failed
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    duration_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RefinementIterationPayloadPhase4(BaseEventPayload):
    """Payload for Phase Four refinement iteration events."""
    feature_id: str = ""
    functionality_id: str = ""
    iteration_number: int = 0
    compiler_results: Dict[str, str] = field(default_factory=dict)
    duration_seconds: float = 0.0
    success: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)