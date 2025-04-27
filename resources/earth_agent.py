from datetime import datetime
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Literal, Set

from resources import (
    ResourceType, 
    ResourceEventTypes, 
    EventQueue, 
    StateManager, 
    AgentContextManager, 
    CacheManager, 
    MetricsManager,
    ErrorHandler,
    MemoryMonitor
)
from agent import Agent
from interface import AgentInterface, AgentState
from dependency import DependencyValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define abstraction tiers for the Earth agent
AbstractionTier = Literal["COMPONENT", "FEATURE", "FUNCTIONALITY"]

class EarthAgent(AgentInterface):
    """
    Earth Agent for validating potential updates to foundational guidelines.
    
    This agent is responsible for validating guideline updates across all abstraction 
    tiers (component, feature, functionality) and determining if they are valid,
    need correction, or should be rejected.
    """
    def __init__(
        self,
        agent_id: str = "earth_agent",
        event_queue: Optional[EventQueue] = None,
        state_manager: Optional[StateManager] = None,
        context_manager: Optional[AgentContextManager] = None,
        cache_manager: Optional[CacheManager] = None,
        metrics_manager: Optional[MetricsManager] = None,
        error_handler: Optional[ErrorHandler] = None,
        memory_monitor: Optional[MemoryMonitor] = None,
        model: str = "claude-3-7-sonnet-20250219",
        max_iterations: int = 3
    ):
        # Initialize base resources if not provided
        if not event_queue:
            event_queue = EventQueue()
            asyncio.create_task(event_queue.start())
        
        if not state_manager:
            state_manager = StateManager(event_queue)
        
        if not context_manager:
            context_manager = AgentContextManager(event_queue)
            
        if not cache_manager:
            cache_manager = CacheManager(event_queue)
            
        if not metrics_manager:
            metrics_manager = MetricsManager(event_queue)
            
        if not error_handler:
            error_handler = ErrorHandler(event_queue)
            
        if not memory_monitor:
            memory_monitor = MemoryMonitor(event_queue)
        
        super().__init__(
            agent_id,
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor,
            model=model
        )
        self.validation_history = {}
        # Maximum number of reflection/revision iterations
        self.max_iterations = max_iterations
        # Initialize dependency validator for dependency context
        self.dependency_validator = DependencyValidator(state_manager)
        # Track current revision attempts
        self.revision_attempts = {}
        
    async def validate_guideline_update(
        self,
        abstraction_tier: AbstractionTier,
        agent_id: str,
        current_guideline: Dict[str, Any],
        proposed_update: Dict[str, Any],
        operation_id: Optional[str] = None,
        with_reflection: bool = True
    ) -> Dict[str, Any]:
        """
        Validate a proposed guideline update for the specified abstraction tier.
        
        Args:
            abstraction_tier: The tier (COMPONENT, FEATURE, FUNCTIONALITY) being validated
            agent_id: The ID of the agent proposing the update
            current_guideline: The current state of the guideline
            proposed_update: The proposed update to the guideline
            operation_id: Optional operation identifier for tracking
            with_reflection: Whether to use reflection and revision process
            
        Returns:
            Dict containing validation results with appropriate structure for the abstraction tier
        """
        logger.info(f"Validating {abstraction_tier} guideline update from agent {agent_id}")
        
        # Generate operation ID if not provided
        if not operation_id:
            operation_id = f"validation_{datetime.now().isoformat()}_{agent_id}"
        
        validation_id = f"earth_validation:{operation_id}"
        
        # Track this validation operation
        await self._state_manager.set_state(
            validation_id,
            {
                "status": "in_progress",
                "tier": abstraction_tier,
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat()
            },
            resource_type=ResourceType.STATE
        )
        
        # Map abstraction tier to appropriate system prompt and schema
        tier_prompts = {
            "COMPONENT": ("FFTT_system_prompts/core_agents/earth_agent/component_tier_prompt", "component_tier_prompt"),
            "FEATURE": ("FFTT_system_prompts/core_agents/earth_agent/feature_tier_prompt", "feature_tier_prompt"),
            "FUNCTIONALITY": ("FFTT_system_prompts/core_agents/earth_agent/functionality_tier_prompt", "functionality_tier_prompt")
        }
        
        system_prompt_info = tier_prompts.get(abstraction_tier)
        if not system_prompt_info:
            logger.error(f"Invalid abstraction tier: {abstraction_tier}")
            return {
                "validation_result": {
                    "is_valid": False,
                    "validation_category": "REJECTED",
                    "explanation": f"Invalid abstraction tier: {abstraction_tier}"
                },
                "detected_issues": [{
                    "issue_type": "system_error",
                    "severity": "CRITICAL",
                    "description": f"Invalid abstraction tier: {abstraction_tier}",
                    "affected_elements": [agent_id],
                    "suggested_resolution": "Use a valid abstraction tier: COMPONENT, FEATURE, or FUNCTIONALITY"
                }],
                "corrected_update": None,
                "metadata": {
                    "validation_timestamp": datetime.now().isoformat(),
                    "original_agent": agent_id,
                    "error": "invalid_abstraction_tier"
                }
            }
        
        try:
            # Prepare the validation conversation with dependency context
            validation_context = await self._prepare_validation_context(
                abstraction_tier, 
                agent_id, 
                current_guideline, 
                proposed_update
            )
            
            conversation = json.dumps(validation_context, indent=2)
            
            # Get validation response from agent with tier-specific prompt
            result = await self.process_with_validation(
                conversation=conversation,
                system_prompt_info=system_prompt_info,
                current_phase=f"{abstraction_tier.lower()}_validation",
                operation_id=operation_id
            )
            
            # Apply reflection and revision process if enabled
            if with_reflection:
                result = await self._reflect_and_revise_validation(
                    result, 
                    abstraction_tier, 
                    validation_context, 
                    operation_id
                )
            
            # Track the validation result
            await self._state_manager.set_state(
                validation_id,
                {
                    "status": "completed",
                    "tier": abstraction_tier,
                    "agent_id": agent_id,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                },
                resource_type=ResourceType.STATE
            )
            
            # Store validation in history
            if agent_id not in self.validation_history:
                self.validation_history[agent_id] = []
            
            self.validation_history[agent_id].append({
                "operation_id": operation_id,
                "tier": abstraction_tier,
                "timestamp": datetime.now().isoformat(),
                "is_valid": result.get("validation_result", {}).get("is_valid", False)
            })
            
            # Record metrics
            await self._metrics_manager.record_metric(
                "earth_agent:validation_count",
                1.0,
                metadata={
                    "agent_id": agent_id,
                    "tier": abstraction_tier,
                    "is_valid": result.get("validation_result", {}).get("is_valid", False)
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating guideline update: {str(e)}")
            
            # Update error state
            await self._state_manager.set_state(
                validation_id,
                {
                    "status": "error",
                    "tier": abstraction_tier,
                    "agent_id": agent_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                },
                resource_type=ResourceType.STATE
            )
            
            # Return error result
            return {
                "validation_result": {
                    "is_valid": False,
                    "validation_category": "REJECTED",
                    "explanation": f"Validation error: {str(e)}"
                },
                "detected_issues": [{
                    "issue_type": "system_error",
                    "severity": "CRITICAL",
                    "description": f"System error during validation: {str(e)}",
                    "affected_elements": [agent_id],
                    "suggested_resolution": "Retry validation or contact system administrator"
                }],
                "corrected_update": None,
                "metadata": {
                    "validation_timestamp": datetime.now().isoformat(),
                    "original_agent": agent_id,
                    "error": str(e)
                }
            }

    async def _prepare_validation_context(
        self,
        abstraction_tier: AbstractionTier,
        agent_id: str,
        current_guideline: Dict[str, Any],
        proposed_update: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare enhanced validation context with dependency information.
        
        This enriches the basic validation input with dependency context
        for more informed validation decisions.
        """
        # Start with basic context
        context = {
            "agent_id": agent_id,
            "current_guideline": current_guideline,
            "proposed_update": proposed_update,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add dependency context based on tier
        if abstraction_tier == "COMPONENT":
            # For component tier, find affected downstream components
            affected_downstream = await self._get_affected_downstream_components(proposed_update)
            context["dependency_context"] = {
                "affected_downstream_components": list(affected_downstream),
                "potential_dependency_impacts": await self._analyze_component_dependencies(proposed_update)
            }
        
        elif abstraction_tier == "FEATURE":
            # For feature tier, find affected features in the same component
            component_id = proposed_update.get("component_id", "unknown")
            affected_features = await self._get_affected_features(component_id, proposed_update)
            context["dependency_context"] = {
                "component_id": component_id,
                "affected_features": list(affected_features),
                "potential_dependency_impacts": await self._analyze_feature_dependencies(component_id, proposed_update)
            }
            
        elif abstraction_tier == "FUNCTIONALITY":
            # For functionality tier, find affected functionalities in the same feature
            feature_id = proposed_update.get("feature_id", "unknown")
            affected_functionalities = await self._get_affected_functionalities(feature_id, proposed_update)
            context["dependency_context"] = {
                "feature_id": feature_id,
                "affected_functionalities": list(affected_functionalities),
                "potential_dependency_impacts": await self._analyze_functionality_dependencies(feature_id, proposed_update)
            }
        
        return context
        
    async def _get_affected_downstream_components(self, proposed_update: Dict[str, Any]) -> Set[str]:
        """
        Identify components affected by changes to the proposed components.
        Uses dependency.py to analyze component relationships.
        """
        affected = set()
        
        # Extract components from structural breakdown
        if "ordered_components" in proposed_update:
            for component in proposed_update["ordered_components"]:
                # Add components that depend on this one
                component_name = component.get("name", "")
                if component_name:
                    # Find dependent components (those that depend on this one)
                    for other_component in proposed_update["ordered_components"]:
                        other_name = other_component.get("name", "")
                        if other_name and other_name != component_name:
                            if "dependencies" in other_component and "required" in other_component["dependencies"]:
                                if component_name in other_component["dependencies"]["required"]:
                                    affected.add(other_name)
        
        return affected
        
    async def _analyze_component_dependencies(self, proposed_update: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze component dependencies for potential impacts.
        """
        impacts = []
        
        # Extract components from structural breakdown
        if "ordered_components" in proposed_update:
            # Check if there are dependency cycles
            is_valid, errors = await self.dependency_validator.validate_structural_breakdown(proposed_update)
            
            if not is_valid:
                for error in errors:
                    if error.get("error_type") == "dependency_cycle":
                        impacts.append({
                            "impact_type": "dependency_cycle",
                            "source": error.get("cycle_node"),
                            "target": error.get("cycle_next"),
                            "description": error.get("message", "Dependency cycle detected")
                        })
            
            # Check for undefined dependencies
            for error in errors:
                if error.get("error_type") == "undefined_dependency":
                    impacts.append({
                        "impact_type": "undefined_dependency",
                        "component": error.get("component_name"),
                        "missing_dependency": error.get("dependency"),
                        "description": error.get("message", "Undefined dependency")
                    })
        
        return impacts
        
    async def _get_affected_features(self, component_id: str, proposed_update: Dict[str, Any]) -> Set[str]:
        """
        Identify features affected by changes to the proposed features.
        """
        affected = set()
        
        # Extract features for this component
        if "features" in proposed_update:
            for feature in proposed_update["features"]:
                # Add features that depend on this one
                feature_id = feature.get("id", "")
                if feature_id:
                    # Find dependent features (those that depend on this one)
                    for other_feature in proposed_update["features"]:
                        other_id = other_feature.get("id", "")
                        if other_id and other_id != feature_id:
                            if "dependencies" in other_feature and feature_id in other_feature["dependencies"]:
                                affected.add(other_id)
        
        return affected
        
    async def _analyze_feature_dependencies(self, component_id: str, proposed_update: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze feature dependencies for potential impacts.
        """
        impacts = []
        
        # Extract features from update
        if "features" in proposed_update:
            feature_ids = set()
            feature_deps = {}
            
            # Collect all feature IDs and their dependencies
            for feature in proposed_update["features"]:
                feature_id = feature.get("id", "")
                if feature_id:
                    feature_ids.add(feature_id)
                    if "dependencies" in feature:
                        feature_deps[feature_id] = feature["dependencies"]
            
            # Check for missing dependencies
            for feature_id, deps in feature_deps.items():
                for dep in deps:
                    if dep not in feature_ids:
                        impacts.append({
                            "impact_type": "missing_feature_dependency",
                            "feature": feature_id,
                            "missing_dependency": dep,
                            "description": f"Feature {feature_id} depends on undefined feature {dep}"
                        })
            
            # Check for cycles using simple cycle detection
            visited = set()
            path = set()
            
            def detect_cycle(node):
                visited.add(node)
                path.add(node)
                
                for neighbor in feature_deps.get(node, []):
                    if neighbor not in visited:
                        if detect_cycle(neighbor):
                            return True
                    elif neighbor in path:
                        impacts.append({
                            "impact_type": "feature_dependency_cycle",
                            "source": node,
                            "target": neighbor,
                            "description": f"Feature dependency cycle detected: {node} -> {neighbor}"
                        })
                        return True
                
                path.remove(node)
                return False
            
            for node in feature_deps:
                if node not in visited:
                    detect_cycle(node)
        
        return impacts
        
    async def _get_affected_functionalities(self, feature_id: str, proposed_update: Dict[str, Any]) -> Set[str]:
        """
        Identify functionalities affected by changes to the proposed functionalities.
        """
        affected = set()
        
        # Extract functionalities for this feature
        if "functionalities" in proposed_update:
            for functionality in proposed_update["functionalities"]:
                # Add functionalities that depend on this one
                functionality_id = functionality.get("id", "")
                if functionality_id:
                    # Find dependent functionalities
                    for other_func in proposed_update["functionalities"]:
                        other_id = other_func.get("id", "")
                        if other_id and other_id != functionality_id:
                            if "dependencies" in other_func and functionality_id in other_func["dependencies"]:
                                affected.add(other_id)
        
        return affected
        
    async def _analyze_functionality_dependencies(self, feature_id: str, proposed_update: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze functionality dependencies for potential impacts.
        """
        impacts = []
        
        # Similar cycle detection as features but for functionalities
        if "functionalities" in proposed_update:
            func_ids = set()
            func_deps = {}
            
            # Collect all functionality IDs and their dependencies
            for func in proposed_update["functionalities"]:
                func_id = func.get("id", "")
                if func_id:
                    func_ids.add(func_id)
                    if "dependencies" in func:
                        func_deps[func_id] = func["dependencies"]
            
            # Check for missing dependencies
            for func_id, deps in func_deps.items():
                for dep in deps:
                    if dep not in func_ids:
                        impacts.append({
                            "impact_type": "missing_functionality_dependency",
                            "functionality": func_id,
                            "missing_dependency": dep,
                            "description": f"Functionality {func_id} depends on undefined functionality {dep}"
                        })
            
            # Check for cycles
            visited = set()
            path = set()
            
            def detect_cycle(node):
                visited.add(node)
                path.add(node)
                
                for neighbor in func_deps.get(node, []):
                    if neighbor not in visited:
                        if detect_cycle(neighbor):
                            return True
                    elif neighbor in path:
                        impacts.append({
                            "impact_type": "functionality_dependency_cycle",
                            "source": node,
                            "target": neighbor,
                            "description": f"Functionality dependency cycle detected: {node} -> {neighbor}"
                        })
                        return True
                
                path.remove(node)
                return False
            
            for node in func_deps:
                if node not in visited:
                    detect_cycle(node)
        
        return impacts
            
    async def _reflect_and_revise_validation(
        self,
        validation_result: Dict[str, Any],
        abstraction_tier: AbstractionTier,
        validation_context: Dict[str, Any],
        operation_id: str
    ) -> Dict[str, Any]:
        """
        Apply reflection and revision process to improve validation result.
        
        Implements a feedback loop where:
        1. Initial validation is reflected upon
        2. Reflection feedback is used to revise the validation
        3. Process repeats up to max_iterations times
        """
        # Initialize tracking for this operation
        if operation_id not in self.revision_attempts:
            self.revision_attempts[operation_id] = 0
            
        current_result = validation_result
        reflection_prompt_info = ("FFTT_system_prompts/core_agents/earth_agent/reflection_prompt", "reflection_prompt")
        revision_prompt_info = ("FFTT_system_prompts/core_agents/earth_agent/revision_prompt", "revision_prompt")
        
        # Continue reflection/revision until max iterations reached
        while self.revision_attempts[operation_id] < self.max_iterations:
            try:
                # Increment revision attempt counter
                self.revision_attempts[operation_id] += 1
                current_attempt = self.revision_attempts[operation_id]
                
                logger.info(f"Starting reflection/revision iteration {current_attempt}/{self.max_iterations} for {operation_id}")
                
                # Prepare reflection context
                reflection_context = {
                    "validation_context": validation_context,
                    "validation_result": current_result,
                    "abstraction_tier": abstraction_tier,
                    "iteration": current_attempt,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Process reflection
                reflection_result = await self.process_with_validation(
                    conversation=json.dumps(reflection_context, indent=2),
                    system_prompt_info=reflection_prompt_info,
                    current_phase=f"{abstraction_tier.lower()}_reflection",
                    operation_id=f"{operation_id}_reflection_{current_attempt}"
                )
                
                # Check if reflection indicates no significant issues
                critical_improvements = reflection_result.get("reflection_results", {}).get("overall_assessment", {}).get("critical_improvements", [])
                decision_quality = reflection_result.get("reflection_results", {}).get("overall_assessment", {}).get("decision_quality_score", 0)
                
                # If decision quality is high (>7) and no critical improvements, stop revision
                if decision_quality >= 7 and len(critical_improvements) == 0:
                    logger.info(f"Reflection indicates high quality decision ({decision_quality}/10) with no critical improvements needed. Stopping revision.")
                    break
                
                # Prepare revision context
                revision_context = {
                    "validation_context": validation_context,
                    "validation_result": current_result,
                    "reflection_result": reflection_result,
                    "abstraction_tier": abstraction_tier,
                    "iteration": current_attempt,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Process revision
                revision_result = await self.process_with_validation(
                    conversation=json.dumps(revision_context, indent=2),
                    system_prompt_info=revision_prompt_info,
                    current_phase=f"{abstraction_tier.lower()}_revision",
                    operation_id=f"{operation_id}_revision_{current_attempt}"
                )
                
                # Update current result from revised validation
                if "revision_results" in revision_result and "revised_validation" in revision_result["revision_results"]:
                    current_result = revision_result["revision_results"]["revised_validation"]
                    
                    # Log revision outcome
                    decision_changes = revision_result.get("revision_results", {}).get("revision_summary", {}).get("decision_changes", {})
                    confidence = revision_result.get("revision_results", {}).get("revision_summary", {}).get("confidence", {})
                    
                    logger.info(f"Completed revision {current_attempt} with confidence score {confidence.get('score', 0)}/10")
                    
                    # If confidence is high (>8) and minimal changes, stop revision
                    if confidence.get("score", 0) >= 8 and not decision_changes.get("category_changed", False):
                        logger.info(f"Revision indicates high confidence ({confidence.get('score', 0)}/10) with minimal changes. Stopping revision.")
                        break
                else:
                    # If revision fails to produce a revised validation, stop the process
                    logger.warning(f"Revision process failed to produce a revised validation in iteration {current_attempt}")
                    break
                
                # Track revision in state
                await self._state_manager.set_state(
                    f"earth_validation:{operation_id}:revision:{current_attempt}",
                    {
                        "reflection": reflection_result,
                        "revision": revision_result,
                        "timestamp": datetime.now().isoformat()
                    },
                    resource_type=ResourceType.STATE
                )
                
                # Record metrics
                await self._metrics_manager.record_metric(
                    "earth_agent:revision_completed",
                    1.0,
                    metadata={
                        "operation_id": operation_id,
                        "attempt": current_attempt,
                        "decision_quality": decision_quality,
                        "confidence": confidence.get("score", 0) if confidence else 0
                    }
                )
                
            except Exception as e:
                logger.error(f"Error in reflection/revision iteration {current_attempt}: {str(e)}")
                # Continue with current result despite error
                break
        
        # Return the final result after all iterations
        return current_result
        
    async def get_agent_validation_history(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get validation history for a specific agent."""
        return self.validation_history.get(agent_id, [])
            
    async def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics across all agents."""
        stats = {
            "total_validations": sum(len(history) for history in self.validation_history.values()),
            "validations_by_agent": {agent_id: len(history) for agent_id, history in self.validation_history.items()},
            "validations_by_tier": {
                "COMPONENT": 0,
                "FEATURE": 0,
                "FUNCTIONALITY": 0
            },
            "approval_rate": 0
        }
        
        # Count by tier and calculate approval rate
        total_approved = 0
        for agent_histories in self.validation_history.values():
            for validation in agent_histories:
                tier = validation.get("tier")
                if tier in stats["validations_by_tier"]:
                    stats["validations_by_tier"][tier] += 1
                
                if validation.get("is_valid", False):
                    total_approved += 1
        
        if stats["total_validations"] > 0:
            stats["approval_rate"] = total_approved / stats["total_validations"]
            
        return stats

    async def process_guideline_update(
        self,
        abstraction_tier: AbstractionTier,
        agent_id: str,
        current_guideline: Dict[str, Any],
        proposed_update: Dict[str, Any],
        operation_id: Optional[str] = None,
        with_reflection: bool = True,
        auto_propagate: bool = False
    ) -> Tuple[bool, Dict[str, Any], Dict[str, Any]]:
        """
        Process a guideline update by validating and returning relevant information.
        
        Args:
            abstraction_tier: The tier (COMPONENT, FEATURE, FUNCTIONALITY) being validated
            agent_id: The ID of the agent proposing the update
            current_guideline: The current state of the guideline
            proposed_update: The proposed update to the guideline
            operation_id: Optional operation identifier for tracking
            with_reflection: Whether to use reflection and revision process
            auto_propagate: Whether to automatically propagate approved updates
            
        Returns:
            Tuple containing:
            - Boolean indicating if the update was accepted (with or without corrections)
            - The final guideline (either the corrected update or the original update if valid)
            - The full validation result dict
        """
        # Validate the guideline update
        validation_result = await self.validate_guideline_update(
            abstraction_tier,
            agent_id,
            current_guideline,
            proposed_update,
            operation_id,
            with_reflection
        )
        
        # Extract validation status
        validation_category = validation_result.get("validation_result", {}).get("validation_category", "REJECTED")
        is_valid = validation_result.get("validation_result", {}).get("is_valid", False)
        
        # For accepted updates (with or without corrections), propagate if requested
        if validation_category in ["APPROVED", "CORRECTED"] and auto_propagate:
            # Determine the update to propagate
            update_to_propagate = validation_result.get("corrected_update") if validation_category == "CORRECTED" else proposed_update
            
            # Emit event for Water agent to pick up
            await self._event_queue.emit_event(
                "earth_agent:validation_complete",
                {
                    "operation_id": operation_id or f"op_{datetime.now().isoformat()}",
                    "agent_id": agent_id,
                    "abstraction_tier": abstraction_tier,
                    "validation_result": validation_result.get("validation_result", {}),
                    "updated_guideline": update_to_propagate,
                    "auto_propagate": True
                }
            )
            
            logger.info(f"Emitted validation complete event for auto-propagation from {agent_id}")
        
        # Determine final guideline to use
        if validation_category == "APPROVED":
            # Update is valid without changes
            return True, proposed_update, validation_result
        elif validation_category == "CORRECTED":
            # Update needed corrections, which were applied
            corrected_update = validation_result.get("corrected_update")
            if corrected_update:
                return True, corrected_update, validation_result
            else:
                # Corrected category but missing corrected update - fallback to rejection
                logger.warning(f"Validation reported CORRECTED but no corrected_update provided for {agent_id}")
                return False, current_guideline, validation_result
        else:
            # Update was rejected
            return False, current_guideline, validation_result