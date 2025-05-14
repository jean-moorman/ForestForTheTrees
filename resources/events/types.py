"""
Event type definitions and core event data structures for the FFTT system.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional

class ResourceEventTypes(Enum):
    """Unified event types for resource management"""
    # Core state events
    INTERFACE_STATE_CHANGED = "interface_state_changed"
    RESOURCE_STATE_CHANGED = "resource_state_changed"
    AGENT_CONTEXT_UPDATED = "agent_context_updated"
    
    # Validation and metrics
    VALIDATION_COMPLETED = "validation_completed"
    METRIC_RECORDED = "metric_recorded"
    MONITORING_ERROR_OCCURRED = "monitoring_error_occurred"
    
    # Resource events
    CACHE_UPDATED = "cache_updated"
    ERROR_OCCURRED = "error_occurred"
    
    # Health and monitoring
    SYSTEM_HEALTH_CHANGED = "system_health_changed"
    RESOURCE_HEALTH_CHANGED = "resource_health_changed"
    RESOURCE_METRIC_RECORDED = "resource_metric_recorded"
    RESOURCE_ALERT_CREATED = "resource_alert_created"
    RESOURCE_ALERT_UPDATED = "resource_alert_updated"
    SYSTEM_ALERT = "system_alert"

    # Error-specific events
    RESOURCE_CLEANUP = "resource_cleanup"
    RESOURCE_ERROR_OCCURRED = "resource_error_occurred"
    RESOURCE_ERROR_RESOLVED = "resource_error_resolved"
    RESOURCE_ERROR_RECOVERY_STARTED = "resource_error_recovery_started"
    RESOURCE_ERROR_RECOVERY_COMPLETED = "resource_error_recovery_completed"
    
    # Phase 0 Earth Agent events
    EARTH_VALIDATION_STARTED = "earth_agent:validation_started"
    EARTH_VALIDATION_COMPLETE = "earth_agent:validation_complete"
    EARTH_VALIDATION_FAILED = "earth_agent:validation_failed"
    
    # Phase 0 Water Agent events
    WATER_PROPAGATION_STARTED = "water_agent:propagation_started"
    WATER_PROPAGATION_COMPLETE = "water_agent:propagation_complete"
    WATER_PROPAGATION_REJECTED = "water_agent:propagation_rejected"
    WATER_PROPAGATION_FAILED = "water_agent:propagation_failed"
    
    # Component Phase 0 Analysis events
    COMPONENT_VALIDATION_STARTED = "component:validation_started"
    COMPONENT_VALIDATION_COMPLETE = "component:validation_complete"
    COMPONENT_PROPAGATION_STARTED = "component:propagation_started"
    COMPONENT_PROPAGATION_COMPLETE = "component:propagation_complete"
    COMPONENT_ANALYSIS_STARTED = "component:analysis_started"
    COMPONENT_ANALYSIS_COMPLETE = "component:analysis_complete"
    
    # Component Phase Two events
    COMPONENT_GUIDELINE_PROPAGATION_COMPLETE = "component:guideline_propagation_complete"
    COMPONENT_GUIDELINE_ESTABLISHED = "component:guideline_established"
    COMPONENT_DEVELOPMENT_STARTED = "component:development_started"
    COMPONENT_DEVELOPMENT_COMPLETED = "component:development_completed"
    COMPONENT_DEVELOPMENT_FAILED = "component:development_failed"
    COMPONENT_DEPENDENCY_CYCLE_DETECTED = "component:dependency_cycle_detected"
    COMPONENT_DEPENDENCY_CYCLES_RESOLVED = "component:dependency_cycles_resolved"
    COMPONENT_FEATURES_READY = "component:features_ready"
    
    # Feature Phase 0 Analysis events
    FEATURE_VALIDATION_STARTED = "feature:validation_started"
    FEATURE_VALIDATION_COMPLETE = "feature:validation_complete"
    FEATURE_PROPAGATION_STARTED = "feature:propagation_started"
    FEATURE_PROPAGATION_COMPLETE = "feature:propagation_complete"
    FEATURE_ANALYSIS_STARTED = "feature:analysis_started"
    FEATURE_ANALYSIS_COMPLETE = "feature:analysis_complete"
    
    # Agent update events
    AGENT_UPDATE_REQUEST = "agent:update_request"
    AGENT_UPDATE_COMPLETE = "agent:update_complete"
    AGENT_UPDATE_FAILED = "agent:update_failed"
    
    # Phase 1 validation events
    PHASE_ONE_VALIDATION_STATE_CHANGED = "phase_one_validation_state_changed"
    PHASE_ONE_VALIDATION_COMPLETED = "phase_one_validation_completed"
    PHASE_ONE_VALIDATION_FAILED = "phase_one_validation_failed"
    
    # Phase 1 refinement events
    PHASE_ONE_REFINEMENT_CREATED = "phase_one_refinement_created"
    PHASE_ONE_REFINEMENT_UPDATED = "phase_one_refinement_updated"
    PHASE_ONE_REFINEMENT_COMPLETED = "phase_one_refinement_completed"
    PHASE_ONE_REFINEMENT_ITERATION = "phase_one_refinement_iteration"
    
    # Phase 1 guideline update events
    PHASE_ONE_GUIDELINE_UPDATE_REQUESTED = "phase_one_guideline_update_requested"
    PHASE_ONE_GUIDELINE_UPDATE_VALIDATED = "phase_one_guideline_update_validated"
    PHASE_ONE_GUIDELINE_UPDATE_PROPAGATING = "phase_one_guideline_update_propagating"
    PHASE_ONE_GUIDELINE_UPDATE_PROPAGATED = "phase_one_guideline_update_propagated"

    # Subphase 2a component guideline update events
    SUBPHASE_2A_GUIDELINE_UPDATE_REQUESTED = "subphase_2a_guideline_update_requested"
    SUBPHASE_2A_GUIDELINE_UPDATE_VALIDATED = "subphase_2a_guideline_update_validated"
    SUBPHASE_2A_GUIDELINE_UPDATE_PROPAGATING = "subphase_2a_guideline_update_propagating"
    SUBPHASE_2A_GUIDELINE_UPDATE_PROPAGATED = "subphase_2a_guideline_update_propagated"

    # Subphase 3a feature guideline update events
    SUBPHASE_3A_GUIDELINE_UPDATE_REQUESTED = "subphase_3a_guideline_update_requested"
    SUBPHASE_3A_GUIDELINE_UPDATE_VALIDATED = "subphase_3a_guideline_update_validated"
    SUBPHASE_3A_GUIDELINE_UPDATE_PROPAGATING = "subphase_3a_guideline_update_propagating"
    SUBPHASE_3A_GUIDELINE_UPDATE_PROPAGATED = "subphase_3a_guideline_update_propagated"

    # Phase Two component events
    PHASE_TWO_COMPONENT_CREATED = "phase_two:component_created"
    PHASE_TWO_COMPONENT_UPDATED = "phase_two:component_updated"
    PHASE_TWO_COMPONENT_DELETED = "phase_two:component_deleted"
    
    # Component validation events
    COMPONENT_VALIDATION_STATE_CHANGED = "component:validation_state_changed"
    COMPONENT_REFINEMENT_CREATED = "component:refinement_created"
    COMPONENT_REFINEMENT_UPDATED = "component:refinement_updated"
    COMPONENT_REFINEMENT_COMPLETED = "component:refinement_completed"
    COMPONENT_REFINEMENT_ITERATION = "component:refinement_iteration"
    
    # Phase Two test events
    PHASE_TWO_TEST_CREATED = "phase_two:test_created"
    PHASE_TWO_TEST_EXECUTED = "phase_two:test_executed"
    PHASE_TWO_TEST_FAILED = "phase_two:test_failed"
    PHASE_TWO_TEST_PASSED = "phase_two:test_passed"
    
    # Phase Two integration events
    PHASE_TWO_INTEGRATION_STARTED = "phase_two:integration_started"
    PHASE_TWO_INTEGRATION_COMPLETED = "phase_two:integration_completed"
    PHASE_TWO_INTEGRATION_FAILED = "phase_two:integration_failed"
    PHASE_TWO_SYSTEM_TEST_STARTED = "phase_two:system_test_started"
    PHASE_TWO_SYSTEM_TEST_COMPLETED = "phase_two:system_test_completed"
    PHASE_TWO_DEPLOYMENT_STARTED = "phase_two:deployment_started"
    PHASE_TWO_DEPLOYMENT_COMPLETED = "phase_two:deployment_completed"
    
    # System testing events
    SYSTEM_TESTING_STARTED = "system_testing:started"
    SYSTEM_TESTING_COMPLETED = "system_testing:completed"
    SYSTEM_TESTING_ERROR = "system_testing:error"
    SYSTEM_TEST_EXECUTION_COMPLETED = "system_testing:execution_completed"
    SYSTEM_TEST_ANALYSIS_COMPLETED = "system_testing:analysis_completed"
    SYSTEM_TEST_REVIEW_COMPLETED = "system_testing:review_completed"
    SYSTEM_TEST_DEBUG_COMPLETED = "system_testing:debug_completed"
    SYSTEM_VALIDATION_COMPLETED = "system_testing:validation_completed"
    
    # Phase Three feature events
    PHASE_THREE_FEATURE_REQUESTED = "phase_three:feature_requested"
    PHASE_THREE_FEATURE_CREATED = "phase_three:feature_created"
    PHASE_THREE_FEATURE_EVOLVED = "phase_three:feature_evolved"
    PHASE_THREE_FEATURE_INTEGRATED = "phase_three:feature_integrated"
    
    # Phase Three optimization events
    PHASE_THREE_OPTIMIZATION_STARTED = "phase_three:optimization_started"
    PHASE_THREE_OPTIMIZATION_ITERATION = "phase_three:optimization_iteration"
    PHASE_THREE_OPTIMIZATION_COMPLETED = "phase_three:optimization_completed"
    PHASE_THREE_NATURAL_SELECTION = "phase_three:natural_selection"
    
    # Phase Four code generation events
    PHASE_FOUR_CODE_GENERATION_STARTED = "phase_four:code_generation_started"
    PHASE_FOUR_CODE_GENERATION_COMPLETED = "phase_four:code_generation_completed"
    PHASE_FOUR_CODE_GENERATION_FAILED = "phase_four:code_generation_failed"
    
    # Phase Four compilation events
    PHASE_FOUR_COMPILATION_STARTED = "phase_four:compilation_started"
    PHASE_FOUR_COMPILATION_PASSED = "phase_four:compilation_passed"
    PHASE_FOUR_COMPILATION_FAILED = "phase_four:compilation_failed"
    
    # Phase Four refinement events
    PHASE_FOUR_REFINEMENT_ITERATION = "phase_four:refinement_iteration"
    PHASE_FOUR_DEBUG_STARTED = "phase_four:debug_started"
    PHASE_FOUR_DEBUG_COMPLETED = "phase_four:debug_completed"


@dataclass
class Event:
    """Represents a single event in the system"""
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    resource_type: Optional[str] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: str = "normal"  # One of "high", "normal", "low"