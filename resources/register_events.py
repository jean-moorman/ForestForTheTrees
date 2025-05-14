"""
Event registry population script.

This script populates the EventRegistry with metadata for all event types
in the FFTT system, including publishers, subscribers, schemas, and examples.
"""
import logging
from typing import Dict, List, Any, Optional

from resources.event_registry import EventRegistry, EventTypeMetadata
from resources.events import ResourceEventTypes
from resources.schemas import (
    # Base and Phase 0/1 schemas
    ValidationEventPayload, PropagationEventPayload,
    ValidationStateChangedPayload, RefinementContextPayload,
    RefinementIterationPayload, AgentUpdateRequestPayload,
    # Phase Two schemas
    ComponentEventPayload, TestEventPayload, IntegrationEventPayload,
    # Phase Three schemas
    FeatureEventPayload, OptimizationEventPayload, FeatureIntegrationPayload,
    # Phase Four schemas
    CodeGenerationPayload, CompilationPayload, RefinementIterationPayloadPhase4
)

logger = logging.getLogger(__name__)

def register_all_events():
    """Register all event types in the event registry."""
    # Core resource events
    register_core_events()
    
    # Phase 0 events
    register_phase_zero_events()
    
    # Phase One events
    register_phase_one_events()
    
    # Phase Two events
    register_phase_two_events()
    
    # Phase Three events
    register_phase_three_events()
    
    # Phase Four events
    register_phase_four_events()
    
    # Log summary
    summary = EventRegistry.get_registry_summary()
    logger.info(f"Registered {summary['total_events']} event types in the event registry")
    
def register_core_events():
    """Register core resource events."""
    # Interface and resource state events
    EventRegistry.register_event(
        ResourceEventTypes.INTERFACE_STATE_CHANGED.value,
        EventTypeMetadata(
            name="Interface State Changed",
            description="Emitted when the interface state changes",
            publisher_components=["interface", "phase_coordinator"],
            subscriber_components=["main", "phase_one", "phase_two", "phase_three", "phase_four"],
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
        EventTypeMetadata(
            name="Resource State Changed",
            description="Emitted when a resource state changes",
            publisher_components=["resource_manager", "state_manager", "cache_manager"],
            subscriber_components=["phase_one", "phase_two", "phase_three", "phase_four"],
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.AGENT_CONTEXT_UPDATED.value,
        EventTypeMetadata(
            name="Agent Context Updated",
            description="Emitted when an agent's context is updated",
            publisher_components=["context_manager", "agent"],
            subscriber_components=["phase_zero", "phase_one", "agent_validation"],
            priority="normal"
        )
    )
    
    # Validation and metrics events
    EventRegistry.register_event(
        ResourceEventTypes.VALIDATION_COMPLETED.value,
        EventTypeMetadata(
            name="Validation Completed",
            description="Emitted when a validation process completes",
            publisher_components=["validator", "dependency_validator", "agent_validation"],
            subscriber_components=["phase_one", "phase_two", "phase_three", "phase_four"],
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.METRIC_RECORDED.value,
        EventTypeMetadata(
            name="Metric Recorded",
            description="Emitted when a metric is recorded",
            publisher_components=["metrics_manager", "monitor", "system_monitor"],
            subscriber_components=["main", "interface", "display"],
            priority="low"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.MONITORING_ERROR_OCCURRED.value,
        EventTypeMetadata(
            name="Monitoring Error Occurred",
            description="Emitted when an error occurs in monitoring",
            publisher_components=["monitor", "system_monitor", "memory_monitor"],
            subscriber_components=["system_error_recovery", "error_handler"],
            priority="high"
        )
    )
    
    # Resource events
    EventRegistry.register_event(
        ResourceEventTypes.CACHE_UPDATED.value,
        EventTypeMetadata(
            name="Cache Updated",
            description="Emitted when cache is updated",
            publisher_components=["cache_manager"],
            subscriber_components=["agent", "phase_zero", "phase_one", "phase_two", "phase_three", "phase_four"],
            priority="low"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.ERROR_OCCURRED.value,
        EventTypeMetadata(
            name="Error Occurred",
            description="Emitted when a general error occurs",
            publisher_components=["error_handler", "agent", "phase_one", "phase_two", "phase_three", "phase_four"],
            subscriber_components=["system_error_recovery", "interface", "display"],
            priority="high"
        )
    )
    
    # Health and monitoring events
    EventRegistry.register_event(
        ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value,
        EventTypeMetadata(
            name="System Health Changed",
            description="Emitted when system health status changes",
            publisher_components=["system_monitor", "health_tracker", "circuit_breaker", "memory_monitor"],
            subscriber_components=["interface", "display", "system_error_recovery"],
            priority="high"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.RESOURCE_HEALTH_CHANGED.value,
        EventTypeMetadata(
            name="Resource Health Changed",
            description="Emitted when a resource's health status changes",
            publisher_components=["resource_manager", "state_manager", "cache_manager"],
            subscriber_components=["system_monitor", "interface"],
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.RESOURCE_METRIC_RECORDED.value,
        EventTypeMetadata(
            name="Resource Metric Recorded",
            description="Emitted when a resource-specific metric is recorded",
            publisher_components=["metrics_manager", "resource_manager", "memory_monitor"],
            subscriber_components=["system_monitor", "interface", "display"],
            priority="low"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.RESOURCE_ALERT_CREATED.value,
        EventTypeMetadata(
            name="Resource Alert Created",
            description="Emitted when a resource alert is created",
            publisher_components=["system_monitor", "memory_monitor", "circuit_breaker"],
            subscriber_components=["interface", "display", "system_error_recovery"],
            priority="high"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.RESOURCE_ALERT_UPDATED.value,
        EventTypeMetadata(
            name="Resource Alert Updated",
            description="Emitted when a resource alert is updated",
            publisher_components=["system_monitor", "memory_monitor", "circuit_breaker"],
            subscriber_components=["interface", "display", "system_error_recovery"],
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.SYSTEM_ALERT.value,
        EventTypeMetadata(
            name="System Alert",
            description="Emitted for system-wide critical alerts",
            publisher_components=["system_monitor", "error_handler", "system_error_recovery"],
            subscriber_components=["interface", "display", "main"],
            priority="high"
        )
    )
    
    # Error-specific events
    EventRegistry.register_event(
        ResourceEventTypes.RESOURCE_CLEANUP.value,
        EventTypeMetadata(
            name="Resource Cleanup",
            description="Emitted when resources are being cleaned up",
            publisher_components=["resource_manager", "state_manager", "cache_manager"],
            subscriber_components=["interface", "main"],
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
        EventTypeMetadata(
            name="Resource Error Occurred",
            description="Emitted when a resource-specific error occurs",
            publisher_components=["resource_manager", "state_manager", "cache_manager", "memory_monitor"],
            subscriber_components=["system_error_recovery", "error_handler", "interface"],
            priority="high"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.RESOURCE_ERROR_RESOLVED.value,
        EventTypeMetadata(
            name="Resource Error Resolved",
            description="Emitted when a resource error is resolved",
            publisher_components=["system_error_recovery", "error_handler"],
            subscriber_components=["interface", "display"],
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.RESOURCE_ERROR_RECOVERY_STARTED.value,
        EventTypeMetadata(
            name="Resource Error Recovery Started",
            description="Emitted when error recovery begins for a resource",
            publisher_components=["system_error_recovery", "error_handler"],
            subscriber_components=["interface", "display"],
            priority="high"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.RESOURCE_ERROR_RECOVERY_COMPLETED.value,
        EventTypeMetadata(
            name="Resource Error Recovery Completed",
            description="Emitted when error recovery completes for a resource",
            publisher_components=["system_error_recovery", "error_handler"],
            subscriber_components=["interface", "display"],
            priority="normal"
        )
    )
    
def register_phase_zero_events():
    """Register Phase Zero events."""
    # Earth Agent events
    EventRegistry.register_event(
        ResourceEventTypes.EARTH_VALIDATION_STARTED.value,
        EventTypeMetadata(
            name="Earth Validation Started",
            description="Emitted when Earth agent starts validating a guideline update",
            publisher_components=["earth_agent", "phase_zero"],
            subscriber_components=["phase_one", "water_agent", "interface"],
            schema_class=ValidationEventPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.EARTH_VALIDATION_COMPLETE.value,
        EventTypeMetadata(
            name="Earth Validation Complete",
            description="Emitted when Earth agent completes validation",
            publisher_components=["earth_agent", "phase_zero"],
            subscriber_components=["phase_one", "water_agent", "interface"],
            schema_class=ValidationEventPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.EARTH_VALIDATION_FAILED.value,
        EventTypeMetadata(
            name="Earth Validation Failed",
            description="Emitted when Earth agent encounters validation errors",
            publisher_components=["earth_agent", "phase_zero"],
            subscriber_components=["phase_one", "water_agent", "interface", "system_error_recovery"],
            schema_class=ValidationEventPayload,
            priority="high"
        )
    )
    
    # Water Agent events
    EventRegistry.register_event(
        ResourceEventTypes.WATER_PROPAGATION_STARTED.value,
        EventTypeMetadata(
            name="Water Propagation Started",
            description="Emitted when Water agent starts propagating changes",
            publisher_components=["water_agent", "phase_zero"],
            subscriber_components=["phase_one", "interface"],
            schema_class=PropagationEventPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.WATER_PROPAGATION_COMPLETE.value,
        EventTypeMetadata(
            name="Water Propagation Complete",
            description="Emitted when Water agent completes propagation",
            publisher_components=["water_agent", "phase_zero"],
            subscriber_components=["phase_one", "interface"],
            schema_class=PropagationEventPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.WATER_PROPAGATION_REJECTED.value,
        EventTypeMetadata(
            name="Water Propagation Rejected",
            description="Emitted when Water agent rejects propagation",
            publisher_components=["water_agent", "phase_zero"],
            subscriber_components=["phase_one", "interface"],
            schema_class=PropagationEventPayload,
            priority="high"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.WATER_PROPAGATION_FAILED.value,
        EventTypeMetadata(
            name="Water Propagation Failed",
            description="Emitted when Water agent encounters propagation errors",
            publisher_components=["water_agent", "phase_zero"],
            subscriber_components=["phase_one", "interface", "system_error_recovery"],
            schema_class=PropagationEventPayload,
            priority="high"
        )
    )
    
    # Agent update events
    EventRegistry.register_event(
        ResourceEventTypes.AGENT_UPDATE_REQUEST.value,
        EventTypeMetadata(
            name="Agent Update Request",
            description="Emitted when an agent update is requested",
            publisher_components=["phase_one", "phase_two", "phase_three", "phase_four"],
            subscriber_components=["water_agent", "earth_agent", "phase_zero"],
            schema_class=AgentUpdateRequestPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.AGENT_UPDATE_COMPLETE.value,
        EventTypeMetadata(
            name="Agent Update Complete",
            description="Emitted when an agent update completes",
            publisher_components=["water_agent", "earth_agent", "phase_zero"],
            subscriber_components=["phase_one", "phase_two", "phase_three", "phase_four", "interface"],
            schema_class=AgentUpdateRequestPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.AGENT_UPDATE_FAILED.value,
        EventTypeMetadata(
            name="Agent Update Failed",
            description="Emitted when an agent update fails",
            publisher_components=["water_agent", "earth_agent", "phase_zero"],
            subscriber_components=["phase_one", "phase_two", "phase_three", "phase_four", "interface", "system_error_recovery"],
            schema_class=AgentUpdateRequestPayload,
            priority="high"
        )
    )
    
def register_phase_one_events():
    """Register Phase One events."""
    # Phase One validation events
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_ONE_VALIDATION_STATE_CHANGED.value,
        EventTypeMetadata(
            name="Phase One Validation State Changed",
            description="Emitted when validation state changes",
            publisher_components=["phase_one", "phase_one_validator"],
            subscriber_components=["refinement_manager", "interface", "system_monitor"],
            schema_class=ValidationStateChangedPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_ONE_VALIDATION_COMPLETED.value,
        EventTypeMetadata(
            name="Phase One Validation Completed",
            description="Emitted when validation completes successfully",
            publisher_components=["phase_one", "phase_one_validator"],
            subscriber_components=["phase_two", "interface", "system_monitor"],
            schema_class=ValidationStateChangedPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_ONE_VALIDATION_FAILED.value,
        EventTypeMetadata(
            name="Phase One Validation Failed",
            description="Emitted when validation fails",
            publisher_components=["phase_one", "phase_one_validator"],
            subscriber_components=["system_error_recovery", "interface", "system_monitor"],
            schema_class=ValidationStateChangedPayload,
            priority="high"
        )
    )
    
    # Phase One refinement events
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_ONE_REFINEMENT_CREATED.value,
        EventTypeMetadata(
            name="Phase One Refinement Created",
            description="Emitted when a refinement context is created",
            publisher_components=["refinement_manager"],
            subscriber_components=["phase_one_validator", "system_monitor"],
            schema_class=RefinementContextPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_ONE_REFINEMENT_UPDATED.value,
        EventTypeMetadata(
            name="Phase One Refinement Updated",
            description="Emitted when a refinement context is updated",
            publisher_components=["refinement_manager"],
            subscriber_components=["phase_one_validator", "system_monitor"],
            schema_class=RefinementContextPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_ONE_REFINEMENT_COMPLETED.value,
        EventTypeMetadata(
            name="Phase One Refinement Completed",
            description="Emitted when a refinement process completes",
            publisher_components=["refinement_manager"],
            subscriber_components=["phase_one_validator", "phase_two", "system_monitor"],
            schema_class=RefinementContextPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_ONE_REFINEMENT_ITERATION.value,
        EventTypeMetadata(
            name="Phase One Refinement Iteration",
            description="Emitted for each iteration of refinement",
            publisher_components=["refinement_manager"],
            subscriber_components=["system_monitor", "metrics_manager"],
            schema_class=RefinementIterationPayload,
            priority="normal"
        )
    )
    
def register_phase_two_events():
    """Register Phase Two events."""
    # Phase Two component events
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_TWO_COMPONENT_CREATED.value,
        EventTypeMetadata(
            name="Phase Two Component Created",
            description="Emitted when a component is created",
            publisher_components=["phase_two", "component_development"],
            subscriber_components=["orchestrator", "interface", "test_creation"],
            schema_class=ComponentEventPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_TWO_COMPONENT_UPDATED.value,
        EventTypeMetadata(
            name="Phase Two Component Updated",
            description="Emitted when a component is updated",
            publisher_components=["phase_two", "component_development"],
            subscriber_components=["orchestrator", "interface", "test_creation"],
            schema_class=ComponentEventPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_TWO_COMPONENT_DELETED.value,
        EventTypeMetadata(
            name="Phase Two Component Deleted",
            description="Emitted when a component is deleted",
            publisher_components=["phase_two", "component_development"],
            subscriber_components=["orchestrator", "interface", "test_creation"],
            schema_class=ComponentEventPayload,
            priority="normal"
        )
    )
    
    # Phase Two test events
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_TWO_TEST_CREATED.value,
        EventTypeMetadata(
            name="Phase Two Test Created",
            description="Emitted when a test is created",
            publisher_components=["phase_two", "test_creation"],
            subscriber_components=["orchestrator", "interface", "implementation"],
            schema_class=TestEventPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_TWO_TEST_EXECUTED.value,
        EventTypeMetadata(
            name="Phase Two Test Executed",
            description="Emitted when a test is executed",
            publisher_components=["phase_two", "test_execution"],
            subscriber_components=["orchestrator", "interface", "implementation"],
            schema_class=TestEventPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_TWO_TEST_FAILED.value,
        EventTypeMetadata(
            name="Phase Two Test Failed",
            description="Emitted when a test fails",
            publisher_components=["phase_two", "test_execution"],
            subscriber_components=["orchestrator", "interface", "implementation"],
            schema_class=TestEventPayload,
            priority="high"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_TWO_TEST_PASSED.value,
        EventTypeMetadata(
            name="Phase Two Test Passed",
            description="Emitted when a test passes",
            publisher_components=["phase_two", "test_execution"],
            subscriber_components=["orchestrator", "interface", "implementation"],
            schema_class=TestEventPayload,
            priority="normal"
        )
    )
    
    # Phase Two integration events
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_TWO_INTEGRATION_STARTED.value,
        EventTypeMetadata(
            name="Phase Two Integration Started",
            description="Emitted when integration testing starts",
            publisher_components=["phase_two", "integration_test"],
            subscriber_components=["orchestrator", "interface"],
            schema_class=IntegrationEventPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_TWO_INTEGRATION_COMPLETED.value,
        EventTypeMetadata(
            name="Phase Two Integration Completed",
            description="Emitted when integration testing completes",
            publisher_components=["phase_two", "integration_test"],
            subscriber_components=["orchestrator", "interface"],
            schema_class=IntegrationEventPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_TWO_INTEGRATION_FAILED.value,
        EventTypeMetadata(
            name="Phase Two Integration Failed",
            description="Emitted when integration testing fails",
            publisher_components=["phase_two", "integration_test"],
            subscriber_components=["orchestrator", "interface", "system_error_recovery"],
            schema_class=IntegrationEventPayload,
            priority="high"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_TWO_SYSTEM_TEST_STARTED.value,
        EventTypeMetadata(
            name="Phase Two System Test Started",
            description="Emitted when system testing starts",
            publisher_components=["phase_two", "system_test"],
            subscriber_components=["orchestrator", "interface"],
            schema_class=IntegrationEventPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_TWO_SYSTEM_TEST_COMPLETED.value,
        EventTypeMetadata(
            name="Phase Two System Test Completed",
            description="Emitted when system testing completes",
            publisher_components=["phase_two", "system_test"],
            subscriber_components=["orchestrator", "interface"],
            schema_class=IntegrationEventPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_TWO_DEPLOYMENT_STARTED.value,
        EventTypeMetadata(
            name="Phase Two Deployment Started",
            description="Emitted when deployment starts",
            publisher_components=["phase_two", "deployment_test"],
            subscriber_components=["orchestrator", "interface"],
            schema_class=IntegrationEventPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_TWO_DEPLOYMENT_COMPLETED.value,
        EventTypeMetadata(
            name="Phase Two Deployment Completed",
            description="Emitted when deployment completes",
            publisher_components=["phase_two", "deployment_test"],
            subscriber_components=["orchestrator", "interface"],
            schema_class=IntegrationEventPayload,
            priority="normal"
        )
    )
    
def register_phase_three_events():
    """Register Phase Three events."""
    # Phase Three feature events
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_THREE_FEATURE_REQUESTED.value,
        EventTypeMetadata(
            name="Phase Three Feature Requested",
            description="Emitted when a feature is requested",
            publisher_components=["phase_three", "elaboration"],
            subscriber_components=["integration", "performance", "natural_selection"],
            schema_class=FeatureEventPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_THREE_FEATURE_CREATED.value,
        EventTypeMetadata(
            name="Phase Three Feature Created",
            description="Emitted when a feature is created",
            publisher_components=["phase_three", "elaboration"],
            subscriber_components=["integration", "performance", "natural_selection"],
            schema_class=FeatureEventPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_THREE_FEATURE_EVOLVED.value,
        EventTypeMetadata(
            name="Phase Three Feature Evolved",
            description="Emitted when a feature evolves",
            publisher_components=["phase_three", "natural_selection"],
            subscriber_components=["integration", "performance", "elaboration"],
            schema_class=FeatureEventPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_THREE_FEATURE_INTEGRATED.value,
        EventTypeMetadata(
            name="Phase Three Feature Integrated",
            description="Emitted when a feature is integrated",
            publisher_components=["phase_three", "integration"],
            subscriber_components=["performance", "natural_selection", "elaboration"],
            schema_class=FeatureEventPayload,
            priority="normal"
        )
    )
    
    # Phase Three optimization events
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_THREE_OPTIMIZATION_STARTED.value,
        EventTypeMetadata(
            name="Phase Three Optimization Started",
            description="Emitted when optimization starts",
            publisher_components=["phase_three", "performance"],
            subscriber_components=["natural_selection", "elaboration", "interface"],
            schema_class=OptimizationEventPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_THREE_OPTIMIZATION_ITERATION.value,
        EventTypeMetadata(
            name="Phase Three Optimization Iteration",
            description="Emitted for each optimization iteration",
            publisher_components=["phase_three", "performance"],
            subscriber_components=["natural_selection", "elaboration", "interface"],
            schema_class=OptimizationEventPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_THREE_OPTIMIZATION_COMPLETED.value,
        EventTypeMetadata(
            name="Phase Three Optimization Completed",
            description="Emitted when optimization completes",
            publisher_components=["phase_three", "performance"],
            subscriber_components=["natural_selection", "elaboration", "interface"],
            schema_class=OptimizationEventPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_THREE_NATURAL_SELECTION.value,
        EventTypeMetadata(
            name="Phase Three Natural Selection",
            description="Emitted when natural selection occurs",
            publisher_components=["phase_three", "natural_selection"],
            subscriber_components=["elaboration", "performance", "interface"],
            schema_class=OptimizationEventPayload,
            priority="normal"
        )
    )
    
def register_phase_four_events():
    """Register Phase Four events."""
    # Phase Four code generation events
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_FOUR_CODE_GENERATION_STARTED.value,
        EventTypeMetadata(
            name="Phase Four Code Generation Started",
            description="Emitted when code generation starts",
            publisher_components=["phase_four", "code_generation"],
            subscriber_components=["static_compilation", "refinement", "debug"],
            schema_class=CodeGenerationPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_FOUR_CODE_GENERATION_COMPLETED.value,
        EventTypeMetadata(
            name="Phase Four Code Generation Completed",
            description="Emitted when code generation completes",
            publisher_components=["phase_four", "code_generation"],
            subscriber_components=["static_compilation", "refinement", "debug"],
            schema_class=CodeGenerationPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_FOUR_CODE_GENERATION_FAILED.value,
        EventTypeMetadata(
            name="Phase Four Code Generation Failed",
            description="Emitted when code generation fails",
            publisher_components=["phase_four", "code_generation"],
            subscriber_components=["static_compilation", "refinement", "debug", "system_error_recovery"],
            schema_class=CodeGenerationPayload,
            priority="high"
        )
    )
    
    # Phase Four compilation events
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_FOUR_COMPILATION_STARTED.value,
        EventTypeMetadata(
            name="Phase Four Compilation Started",
            description="Emitted when compilation starts",
            publisher_components=["phase_four", "static_compilation"],
            subscriber_components=["refinement", "debug", "code_generation"],
            schema_class=CompilationPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_FOUR_COMPILATION_PASSED.value,
        EventTypeMetadata(
            name="Phase Four Compilation Passed",
            description="Emitted when compilation passes",
            publisher_components=["phase_four", "static_compilation"],
            subscriber_components=["refinement", "debug", "code_generation"],
            schema_class=CompilationPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_FOUR_COMPILATION_FAILED.value,
        EventTypeMetadata(
            name="Phase Four Compilation Failed",
            description="Emitted when compilation fails",
            publisher_components=["phase_four", "static_compilation"],
            subscriber_components=["refinement", "debug", "code_generation", "system_error_recovery"],
            schema_class=CompilationPayload,
            priority="high"
        )
    )
    
    # Phase Four refinement events
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_FOUR_REFINEMENT_ITERATION.value,
        EventTypeMetadata(
            name="Phase Four Refinement Iteration",
            description="Emitted for each refinement iteration",
            publisher_components=["phase_four", "refinement"],
            subscriber_components=["code_generation", "debug", "static_compilation"],
            schema_class=RefinementIterationPayloadPhase4,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_FOUR_DEBUG_STARTED.value,
        EventTypeMetadata(
            name="Phase Four Debug Started",
            description="Emitted when debugging starts",
            publisher_components=["phase_four", "debug"],
            subscriber_components=["refinement", "code_generation", "static_compilation"],
            schema_class=CodeGenerationPayload,
            priority="normal"
        )
    )
    
    EventRegistry.register_event(
        ResourceEventTypes.PHASE_FOUR_DEBUG_COMPLETED.value,
        EventTypeMetadata(
            name="Phase Four Debug Completed",
            description="Emitted when debugging completes",
            publisher_components=["phase_four", "debug"],
            subscriber_components=["refinement", "code_generation", "static_compilation"],
            schema_class=CodeGenerationPayload,
            priority="normal"
        )
    )

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Register all events
    register_all_events()
    
    # Log summary
    summary = EventRegistry.get_registry_summary()
    print(f"Registered {summary['total_events']} event types")
    print(f"Events by phase: {summary['event_types_by_phase']}")
    print(f"Publisher components: {summary['publishers']}")
    print(f"Subscriber components: {summary['subscribers']}")