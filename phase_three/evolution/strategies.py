import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Set

from resources import (
    ResourceType, 
    StateManager, 
    MetricsManager, 
    EventQueue
)

logger = logging.getLogger(__name__)

class FeatureEvolutionStrategy:
    """Base class for feature evolution strategies"""
    
    def __init__(self, 
                state_manager: StateManager,
                metrics_manager: MetricsManager,
                event_queue: EventQueue):
        self._state_manager = state_manager
        self._metrics_manager = metrics_manager
        self._event_queue = event_queue
    
    async def apply(self, feature_id: str, rationale: str, 
                  evaluation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply the evolution strategy to a feature.
        
        Args:
            feature_id: ID of the feature to evolve
            rationale: Reason for evolution
            evaluation_data: Data from natural selection evaluation
            
        Returns:
            Dict containing evolution results
        """
        raise NotImplementedError("Subclasses must implement the apply method")
    
    async def _disable_feature(self, feature_id: str) -> None:
        """Disable a feature by toggling it off.
        
        Args:
            feature_id: ID of the feature to disable
        """
        try:
            logger.info(f"Disabling feature {feature_id} as part of evolution")
            
            # Get feature from state manager
            feature_state = await self._state_manager.get_state(f"feature:development:{feature_id}")
            if not feature_state:
                logger.warning(f"Feature state not found for {feature_id}")
                return
            
            # Update feature state to disabled
            await self._state_manager.set_state(
                f"feature:development:{feature_id}",
                {
                    **feature_state,
                    "state": "DISABLED",
                    "disabled_at": datetime.now().isoformat(),
                    "is_enabled": False
                },
                ResourceType.STATE
            )
            
            # Emit feature disabled event
            self._event_queue.publish(
                "feature_disabled",
                {
                    "feature_id": feature_id,
                    "reason": "evolutionary_replacement",
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Record metric
            await self._metrics_manager.record_metric(
                "feature:disabled",
                1.0,
                metadata={"feature_id": feature_id, "reason": "evolutionary_replacement"}
            )
            
        except Exception as e:
            logger.error(f"Error disabling feature {feature_id}: {str(e)}")

class FeatureReplacementStrategy(FeatureEvolutionStrategy):
    """Strategy for replacing a feature with a new implementation"""
    
    async def apply(self, feature_id: str, rationale: str, 
                   evaluation_data: Dict[str, Any],
                   feature_development_manager: Any) -> Dict[str, Any]:
        """Replace a low-performing feature with a new implementation.
        
        Args:
            feature_id: The ID of the feature to replace
            rationale: The reason for replacement
            evaluation_data: The full evaluation data with patterns and suggestions
            feature_development_manager: Manager for starting feature development
            
        Returns:
            Dict containing replacement results
        """
        logger.info(f"Replacing feature {feature_id} based on evolutionary selection")
        
        try:
            # Get current feature status
            feature_status = await feature_development_manager.get_feature_status(feature_id)
            if not feature_status or "error" in feature_status:
                return {
                    "status": "error",
                    "error": f"Could not retrieve feature status: {feature_status.get('error', 'Unknown error')}",
                    "feature_id": feature_id
                }
            
            # Record replacement decision
            await self._metrics_manager.record_metric(
                "feature:evolution:replacement_decision",
                1.0,
                metadata={
                    "feature_id": feature_id,
                    "feature_name": feature_status.get("feature_name", "unknown"),
                    "rationale": rationale
                }
            )
            
            # Determine replacement method based on evolution data
            evolution_opportunities = evaluation_data.get("phase_zero_feedback", {}).get(
                "evolution_opportunities", {}
            )
            reuse_opportunities = evolution_opportunities.get("reuse_patterns", [])
            
            # Check if we can reuse code from another feature
            replacement_method = "recreation"  # Default method
            reuse_candidate = None
            
            for reuse in reuse_opportunities:
                if reuse.get("target_feature_id") == feature_id:
                    reuse_candidate = reuse
                    replacement_method = "reuse"
                    break
            
            # First, toggle the original feature to off (disable it)
            await self._disable_feature(feature_id)
            
            # Create replacement feature ID
            replacement_id = f"{feature_id}_v{int(datetime.now().timestamp())}"
            
            # Prepare requirements for the new feature
            if replacement_method == "reuse":
                # Use requirements from the reuse candidate
                source_feature_id = reuse_candidate.get("source_feature_id")
                source_feature = await feature_development_manager.get_feature_status(source_feature_id)
                
                if not source_feature or "error" in source_feature:
                    # Fallback to recreation if source feature not found
                    replacement_method = "recreation"
                    requirements = self._prepare_recreation_requirements(feature_status, evaluation_data)
                else:
                    # Adapt the source feature with the original feature's requirements
                    requirements = self._prepare_reuse_requirements(
                        feature_status, 
                        source_feature, 
                        reuse_candidate
                    )
            else:
                # Prepare requirements for recreation
                requirements = self._prepare_recreation_requirements(feature_status, evaluation_data)
            
            # Start development of the replacement feature
            replacement_result = await feature_development_manager.start_feature_development({
                "id": replacement_id,
                "name": f"{feature_status.get('feature_name', 'Unknown')}_Replacement",
                "description": f"Replacement for {feature_id}: {rationale}",
                "requirements": requirements,
                "dependencies": feature_status.get("dependencies", []),
                "replacement_for": feature_id,
                "replacement_method": replacement_method
            })
            
            # Store the replacement relationship in state manager
            await self._state_manager.set_state(
                f"feature:replacement:{feature_id}",
                {
                    "original_id": feature_id,
                    "replacement_id": replacement_id,
                    "method": replacement_method,
                    "timestamp": datetime.now().isoformat(),
                    "rationale": rationale
                },
                ResourceType.STATE
            )
            
            # Record the replacement metric
            await self._metrics_manager.record_metric(
                "feature:evolution:replacement_created",
                1.0,
                metadata={
                    "original_id": feature_id,
                    "replacement_id": replacement_id,
                    "method": replacement_method
                }
            )
            
            return {
                "status": "success",
                "original_id": feature_id,
                "replacement_id": replacement_id,
                "method": replacement_method,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error replacing feature {feature_id}: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "feature_id": feature_id
            }
    
    def _prepare_recreation_requirements(self, 
                                      feature_status: Dict[str, Any],
                                      evaluation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare requirements for feature recreation based on evolutionary feedback.
        
        Args:
            feature_status: Current status of the feature
            evaluation_data: Evaluation data with improvement suggestions
            
        Returns:
            Dict of updated requirements for recreation
        """
        # Start with original requirements
        original_requirements = feature_status.get("requirements", {})
        
        # Extract improvement suggestions from evaluation
        improvements = []
        for pattern in evaluation_data.get("key_patterns", []):
            if pattern.get("issue") and "low quality" in pattern.get("issue", "").lower():
                improvements.extend([evidence for signal in pattern.get("signals", []) 
                                   for evidence in signal.get("key_evidence", [])])
        
        # Add evolutionary improvements to requirements
        if not original_requirements:
            original_requirements = {}
        
        updated_requirements = dict(original_requirements)
        
        # Add evolution-guided improvements
        if "improvements" not in updated_requirements:
            updated_requirements["improvements"] = []
        
        updated_requirements["improvements"].extend(improvements)
        updated_requirements["recreation_from"] = feature_status.get("feature_id")
        
        return updated_requirements
    
    def _prepare_reuse_requirements(self, 
                                 original_feature: Dict[str, Any],
                                 source_feature: Dict[str, Any],
                                 reuse_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare requirements for feature reuse from another feature.
        
        Args:
            original_feature: Feature being replaced
            source_feature: Feature being reused
            reuse_data: Reuse pattern data from evolution agent
            
        Returns:
            Dict of requirements for the new feature
        """
        # Start with source feature requirements
        source_requirements = source_feature.get("requirements", {})
        
        # Adapt them to the original feature's purpose
        adapted_requirements = dict(source_requirements)
        
        # Keep original feature's name and description
        adapted_requirements["original_name"] = original_feature.get("feature_name")
        adapted_requirements["original_description"] = original_feature.get("description")
        
        # Add adaptation guidance from reuse data
        adapted_requirements["reuse_adaptations"] = reuse_data.get("adaptations", [])
        adapted_requirements["reuse_from"] = source_feature.get("feature_id")
        adapted_requirements["reuse_for"] = original_feature.get("feature_id")
        
        # Keep original dependencies
        if "dependencies" not in adapted_requirements:
            adapted_requirements["dependencies"] = []
        
        original_dependencies = original_feature.get("dependencies", [])
        if original_dependencies:
            adapted_requirements["dependencies"].extend(
                [dep for dep in original_dependencies 
                 if dep not in adapted_requirements["dependencies"]]
            )
        
        return adapted_requirements

class FeatureImprovementStrategy(FeatureEvolutionStrategy):
    """Strategy for improving an existing feature"""
    
    async def apply(self, feature_id: str, rationale: str, 
                   evaluation_data: Dict[str, Any],
                   phase_four_interface: Any) -> Dict[str, Any]:
        """Improve an existing feature based on evolutionary feedback.
        
        Args:
            feature_id: ID of the feature to improve
            rationale: Reason for improvement
            evaluation_data: Evaluation data with improvement suggestions
            phase_four_interface: Interface to Phase Four for code improvement
            
        Returns:
            Dict containing improvement results
        """
        logger.info(f"Improving feature {feature_id} based on evolutionary selection")
        
        try:
            # Get current feature status from state manager
            feature_status = await self._state_manager.get_state(f"feature:development:{feature_id}")
            if not feature_status:
                return {
                    "status": "error",
                    "error": f"Could not retrieve feature status",
                    "feature_id": feature_id
                }
            
            # Extract improvement suggestions from evaluation
            improvements = []
            for pattern in evaluation_data.get("key_patterns", []):
                if any(area in pattern.get("affected_areas", []) for area in ["code_quality", "performance", "architecture"]):
                    improvements.extend([evidence for signal in pattern.get("signals", []) 
                                       for evidence in signal.get("key_evidence", [])])
            
            # Extract specific improvement suggestions from adaptations
            for adaptation in evaluation_data.get("adaptations", []):
                if feature_id in adaptation.get("addresses", []):
                    improvements.append(adaptation.get("implementation", ""))
            
            # If no specific improvements found, use general ones
            if not improvements:
                improvements = [
                    "Improve code readability and documentation",
                    "Optimize performance-critical sections",
                    "Enhance error handling and recovery mechanisms",
                    "Improve test coverage for edge cases"
                ]
            
            # Create improvement task
            improvement_id = f"improve_{feature_id}_{int(datetime.now().timestamp())}"
            
            # Store improvement task in state manager
            await self._state_manager.set_state(
                f"feature:improvement:{improvement_id}",
                {
                    "feature_id": feature_id,
                    "improvements": improvements,
                    "status": "pending",
                    "created_at": datetime.now().isoformat(),
                    "rationale": rationale
                },
                ResourceType.STATE
            )
            
            # Get feature implementation
            feature_implementation = await self._state_manager.get_state(f"feature:implementation:{feature_id}")
            
            if not feature_implementation:
                return {
                    "status": "pending",
                    "message": "Feature scheduled for improvement, but implementation not found",
                    "improvements": improvements,
                    "improvement_id": improvement_id
                }
            
            # Prepare input for phase four
            improvement_input = {
                "id": feature_id,
                "name": feature_status.get("feature_name", "Unknown"),
                "original_implementation": feature_implementation.get("implementation", ""),
                "improvements": improvements,
                "rationale": rationale
            }
            
            # Use phase four to improve the implementation
            try:
                improvement_result = await phase_four_interface.process_feature_improvement(
                    improvement_input
                )
                
                if improvement_result.get("success", False):
                    # Update feature implementation
                    await self._state_manager.set_state(
                        f"feature:implementation:{feature_id}",
                        {
                            **feature_implementation,
                            "implementation": improvement_result.get("improved_code", 
                                                                  feature_implementation.get("implementation", "")),
                            "improved_at": datetime.now().isoformat(),
                            "improvements": improvements
                        },
                        ResourceType.STATE
                    )
                    
                    # Update improvement task status
                    await self._state_manager.set_state(
                        f"feature:improvement:{improvement_id}",
                        {
                            "feature_id": feature_id,
                            "improvements": improvements,
                            "status": "completed",
                            "created_at": datetime.now().isoformat(),
                            "completed_at": datetime.now().isoformat(),
                            "rationale": rationale
                        },
                        ResourceType.STATE
                    )
                    
                    # Record metric
                    await self._metrics_manager.record_metric(
                        "feature:evolution:improved",
                        1.0,
                        metadata={
                            "feature_id": feature_id,
                            "improvement_count": len(improvements)
                        }
                    )
                    
                    return {
                        "status": "success",
                        "feature_id": feature_id,
                        "improvements": improvements,
                        "improvement_id": improvement_id
                    }
                else:
                    # Update improvement task status to failed
                    await self._state_manager.set_state(
                        f"feature:improvement:{improvement_id}",
                        {
                            "feature_id": feature_id,
                            "improvements": improvements,
                            "status": "failed",
                            "created_at": datetime.now().isoformat(),
                            "failed_at": datetime.now().isoformat(),
                            "rationale": rationale,
                            "error": improvement_result.get("error", "Unknown error")
                        },
                        ResourceType.STATE
                    )
                    
                    return {
                        "status": "failed",
                        "feature_id": feature_id,
                        "improvements": improvements,
                        "improvement_id": improvement_id,
                        "error": improvement_result.get("error", "Unknown error")
                    }
            
            except Exception as e:
                logger.error(f"Error improving feature with phase four: {str(e)}")
                # Update improvement task status to error
                await self._state_manager.set_state(
                    f"feature:improvement:{improvement_id}",
                    {
                        "feature_id": feature_id,
                        "improvements": improvements,
                        "status": "error",
                        "created_at": datetime.now().isoformat(),
                        "error_at": datetime.now().isoformat(),
                        "rationale": rationale,
                        "error": str(e)
                    },
                    ResourceType.STATE
                )
                
                return {
                    "status": "error",
                    "feature_id": feature_id,
                    "improvements": improvements,
                    "improvement_id": improvement_id,
                    "error": str(e)
                }
                
        except Exception as e:
            logger.error(f"Error improving feature {feature_id}: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "feature_id": feature_id
            }