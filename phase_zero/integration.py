"""
Phase Zero Integration Interfaces

This module provides integration interfaces for Phase Zero with Phase 2 and Phase 3.
It enables the analysis and feedback of component and feature guidelines using
specialized Phase Zero agents.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from resources import (
    EventQueue, 
    StateManager, 
    CacheManager, 
    AgentContextManager, 
    MetricsManager, 
    ErrorHandler, 
    HealthTracker,
    ResourceType,
    HealthStatus,
    ResourceEventTypes
)

from phase_zero.validation.earth import validate_guideline_update
# Water agent propagation functionality has been removed
from dataclasses import asdict

logger = logging.getLogger(__name__)

class PhaseZeroComponentIntegration:
    """Interface for integrating Phase Zero with Phase 2 (component level)"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None):
        """Initialize the component integration interface"""
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._context_manager = context_manager
        self._cache_manager = cache_manager
        self._metrics_manager = metrics_manager
        self._error_handler = error_handler
        self._health_tracker = health_tracker
        
        # Create agent instances - placeholder until agent classes are created
        self._component_agents = {}
        
        logger.info("Phase Zero Component Integration initialized")
    
    async def analyze_component_guidelines(self, 
                                           component_id: str, 
                                           component_guidelines: Dict[str, Any],
                                           operation_id: str) -> Dict[str, Any]:
        """Analyze component guidelines using specialized Phase Zero agents"""
        logger.info(f"Analyzing component guidelines for {component_id}")
        
        try:
            # Record start metric
            await self._metrics_manager.record_metric(
                "phase_zero:component_analysis:start",
                1.0,
                metadata={
                    "component_id": component_id,
                    "operation_id": operation_id
                }
            )
            
            # Store analysis request
            await self._state_manager.set_state(
                f"phase_zero:component_analysis:{component_id}",
                {
                    "component_id": component_id,
                    "timestamp": datetime.now().isoformat(),
                    "operation_id": operation_id,
                    "status": "in_progress"
                },
                ResourceType.STATE
            )
            
            # Process with agents - placeholder until agents are created
            analysis_results = {
                "component_id": component_id,
                "operation_id": operation_id,
                "timestamp": datetime.now().isoformat(),
                "description_analysis": {
                    "issues": [],
                    "gaps": [],
                    "conflicts": []
                },
                "requirements_analysis": {
                    "gaps": [],
                    "conflicts": [],
                    "issues": [],
                    "optimization": []
                },
                "data_flow_analysis": {
                    "gaps": [],
                    "conflicts": [],
                    "issues": []
                },
                "structure_analysis": {
                    "gaps": [],
                    "conflicts": [],
                    "issues": [],
                    "optimization": []
                },
                "evolution_synthesis": {
                    "recommendations": [],
                    "strategies": []
                }
            }
            
            # Store analysis results
            await self._state_manager.set_state(
                f"phase_zero:component_analysis:{component_id}:results",
                analysis_results,
                ResourceType.STATE
            )
            
            # Update status
            await self._state_manager.set_state(
                f"phase_zero:component_analysis:{component_id}",
                {
                    "component_id": component_id,
                    "timestamp": datetime.now().isoformat(),
                    "operation_id": operation_id,
                    "status": "completed"
                },
                ResourceType.STATE
            )
            
            # Record completion metric
            await self._metrics_manager.record_metric(
                "phase_zero:component_analysis:complete",
                1.0,
                metadata={
                    "component_id": component_id,
                    "operation_id": operation_id
                }
            )
            
            return analysis_results
        
        except Exception as e:
            logger.error(f"Error in component guideline analysis: {str(e)}", exc_info=True)
            
            # Record error metric
            await self._metrics_manager.record_metric(
                "phase_zero:component_analysis:error",
                1.0,
                metadata={
                    "component_id": component_id,
                    "operation_id": operation_id,
                    "error": str(e)
                }
            )
            
            # Update status to error
            await self._state_manager.set_state(
                f"phase_zero:component_analysis:{component_id}",
                {
                    "component_id": component_id,
                    "timestamp": datetime.now().isoformat(),
                    "operation_id": operation_id,
                    "status": "error",
                    "error": str(e)
                },
                ResourceType.STATE
            )
            
            return {
                "component_id": component_id,
                "operation_id": operation_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def validate_component_guideline_update(self, 
                                                 component_id: str, 
                                                 current_guideline: Dict[str, Any],
                                                 proposed_update: Dict[str, Any]) -> Dict[str, Any]:
        """Validate component guideline update using Earth mechanism"""
        try:
            # Call Earth validation with component context
            validation_result = await validate_guideline_update(
                agent_id=component_id,
                current_guideline=current_guideline,
                proposed_update=proposed_update,
                health_tracker=self._health_tracker,
                state_manager=self._state_manager
            )
            
            # Emit component-specific validation event
            try:
                from resources.schemas import ValidationEventPayload
                
                # Create specialized component validation payload
                payload = ValidationEventPayload(
                    validation_id=validation_result.get("metadata", {}).get("validation_id", "unknown"),
                    agent_id=component_id,
                    is_valid=validation_result["is_valid"],
                    validation_category="COMPONENT_APPROVED" if validation_result["is_valid"] else "COMPONENT_REJECTED",
                    detected_issues=validation_result.get("detected_issues", []),
                    tier="component",
                    corrected_update=validation_result.get("corrected_update"),
                    source_id="component_earth_validator",
                    context={
                        "reason": validation_result["reason"]
                    }
                )
                
                # Emit with component validation event type
                await self._event_queue.emit(
                    "COMPONENT_VALIDATION_COMPLETE",
                    asdict(payload)
                )
            except Exception as event_error:
                logger.warning(f"Error emitting component validation event: {event_error}")
            
            return validation_result
        
        except Exception as e:
            logger.error(f"Error in component guideline validation: {str(e)}", exc_info=True)
            return {
                "is_valid": False,
                "reason": f"Validation error: {str(e)}",
                "component_id": component_id,
                "timestamp": datetime.now().isoformat()
            }
    
    async def propagate_component_guideline_update(self,
                                                  component_id: str,
                                                  updated_guideline: Dict[str, Any],
                                                  affected_components: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Propagate component guideline update to affected components.
        
        Note: This is a stub implementation as the Water propagation mechanism has been removed.
        It always returns success without actually propagating anything.
        """
        logger.info(f"Component guideline update propagation called for component {component_id} (stubbed)")
        
        if affected_components is None:
            affected_components = []
            
        # Return a successful result without actual propagation
        result = {
            "success": True,
            "affected_agents": affected_components,
            "timestamp": datetime.now().isoformat(),
            "component_id": component_id,
            "metadata": {
                "warning": "Water propagation functionality has been removed. This is a stub implementation."
            }
        }
        
        # Emit component propagation event
        await self._event_queue.emit(
            "COMPONENT_PROPAGATION_COMPLETE",
            {
                "component_id": component_id,
                "affected_components": affected_components,
                "success": True,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return result

class PhaseZeroFeatureIntegration:
    """Interface for integrating Phase Zero with Phase 3 (feature level)"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None):
        """Initialize the feature integration interface"""
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._context_manager = context_manager
        self._cache_manager = cache_manager
        self._metrics_manager = metrics_manager
        self._error_handler = error_handler
        self._health_tracker = health_tracker
        
        # Create agent instances - placeholder until agent classes are created
        self._feature_agents = {}
        
        logger.info("Phase Zero Feature Integration initialized")
    
    async def analyze_feature_guidelines(self, 
                                         feature_id: str, 
                                         feature_guidelines: Dict[str, Any],
                                         operation_id: str) -> Dict[str, Any]:
        """Analyze feature guidelines using specialized Phase Zero agents"""
        logger.info(f"Analyzing feature guidelines for {feature_id}")
        
        try:
            # Record start metric
            await self._metrics_manager.record_metric(
                "phase_zero:feature_analysis:start",
                1.0,
                metadata={
                    "feature_id": feature_id,
                    "operation_id": operation_id
                }
            )
            
            # Store analysis request
            await self._state_manager.set_state(
                f"phase_zero:feature_analysis:{feature_id}",
                {
                    "feature_id": feature_id,
                    "timestamp": datetime.now().isoformat(),
                    "operation_id": operation_id,
                    "status": "in_progress"
                },
                ResourceType.STATE
            )
            
            # Process with agents - placeholder until agents are created
            analysis_results = {
                "feature_id": feature_id,
                "operation_id": operation_id,
                "timestamp": datetime.now().isoformat(),
                "requirements_analysis": {
                    "completion_gaps": [],
                    "consistency_issues": [],
                    "testability_concerns": [],
                    "enhancement_suggestions": []
                },
                "implementation_analysis": {
                    "code_structure_issues": [],
                    "architectural_concerns": [],
                    "optimization_opportunities": [],
                    "quality_metrics": {}
                },
                "evolution_analysis": {
                    "feature_combinations": [],
                    "reuse_patterns": [],
                    "refactoring_suggestions": [],
                    "emerging_abstractions": []
                }
            }
            
            # Store analysis results
            await self._state_manager.set_state(
                f"phase_zero:feature_analysis:{feature_id}:results",
                analysis_results,
                ResourceType.STATE
            )
            
            # Update status
            await self._state_manager.set_state(
                f"phase_zero:feature_analysis:{feature_id}",
                {
                    "feature_id": feature_id,
                    "timestamp": datetime.now().isoformat(),
                    "operation_id": operation_id,
                    "status": "completed"
                },
                ResourceType.STATE
            )
            
            # Record completion metric
            await self._metrics_manager.record_metric(
                "phase_zero:feature_analysis:complete",
                1.0,
                metadata={
                    "feature_id": feature_id,
                    "operation_id": operation_id
                }
            )
            
            return analysis_results
        
        except Exception as e:
            logger.error(f"Error in feature guideline analysis: {str(e)}", exc_info=True)
            
            # Record error metric
            await self._metrics_manager.record_metric(
                "phase_zero:feature_analysis:error",
                1.0,
                metadata={
                    "feature_id": feature_id,
                    "operation_id": operation_id,
                    "error": str(e)
                }
            )
            
            # Update status to error
            await self._state_manager.set_state(
                f"phase_zero:feature_analysis:{feature_id}",
                {
                    "feature_id": feature_id,
                    "timestamp": datetime.now().isoformat(),
                    "operation_id": operation_id,
                    "status": "error",
                    "error": str(e)
                },
                ResourceType.STATE
            )
            
            return {
                "feature_id": feature_id,
                "operation_id": operation_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def validate_feature_guideline_update(self, 
                                              feature_id: str, 
                                              current_guideline: Dict[str, Any],
                                              proposed_update: Dict[str, Any]) -> Dict[str, Any]:
        """Validate feature guideline update using Earth mechanism"""
        try:
            # Call Earth validation with feature context
            validation_result = await validate_guideline_update(
                agent_id=feature_id,
                current_guideline=current_guideline,
                proposed_update=proposed_update,
                health_tracker=self._health_tracker,
                state_manager=self._state_manager
            )
            
            # Emit feature-specific validation event
            try:
                from resources.schemas import ValidationEventPayload
                
                # Create specialized feature validation payload
                payload = ValidationEventPayload(
                    validation_id=validation_result.get("metadata", {}).get("validation_id", "unknown"),
                    agent_id=feature_id,
                    is_valid=validation_result["is_valid"],
                    validation_category="FEATURE_APPROVED" if validation_result["is_valid"] else "FEATURE_REJECTED",
                    detected_issues=validation_result.get("detected_issues", []),
                    tier="feature",
                    corrected_update=validation_result.get("corrected_update"),
                    source_id="feature_earth_validator",
                    context={
                        "reason": validation_result["reason"]
                    }
                )
                
                # Emit with feature validation event type
                await self._event_queue.emit(
                    "FEATURE_VALIDATION_COMPLETE",
                    asdict(payload)
                )
            except Exception as event_error:
                logger.warning(f"Error emitting feature validation event: {event_error}")
            
            return validation_result
        
        except Exception as e:
            logger.error(f"Error in feature guideline validation: {str(e)}", exc_info=True)
            return {
                "is_valid": False,
                "reason": f"Validation error: {str(e)}",
                "feature_id": feature_id,
                "timestamp": datetime.now().isoformat()
            }
    
    async def propagate_feature_guideline_update(self,
                                               feature_id: str,
                                               updated_guideline: Dict[str, Any],
                                               affected_features: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Propagate feature guideline update to affected features.
        
        Note: This is a stub implementation as the Water propagation mechanism has been removed.
        It always returns success without actually propagating anything.
        """
        logger.info(f"Feature guideline update propagation called for feature {feature_id} (stubbed)")
        
        if affected_features is None:
            affected_features = []
            
        # Return a successful result without actual propagation
        result = {
            "success": True,
            "affected_agents": affected_features,
            "timestamp": datetime.now().isoformat(),
            "feature_id": feature_id,
            "metadata": {
                "warning": "Water propagation functionality has been removed. This is a stub implementation."
            }
        }
        
        # Emit feature propagation event
        await self._event_queue.emit(
            "FEATURE_PROPAGATION_COMPLETE",
            {
                "feature_id": feature_id,
                "affected_features": affected_features,
                "success": True,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return result