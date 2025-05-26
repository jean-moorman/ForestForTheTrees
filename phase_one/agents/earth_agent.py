"""
Earth Agent for Phase One validation of Garden Planner output.

This agent validates the Garden Planner output against the original user request,
providing feedback for refinement.
"""
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from resources import (
    EventQueue, 
    StateManager, 
    AgentContextManager, 
    CacheManager, 
    MetricsManager, 
    ErrorHandler,
    MemoryMonitor
)
from resources.monitoring import HealthTracker, MemoryThresholds

from phase_one.agents.base import ReflectiveAgent
from phase_one.models.enums import DevelopmentState
from phase_one.models.refinement import AgentPromptConfig, RefinementContext
from phase_one.monitoring.circuit_breakers import CircuitBreakerDefinition

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EarthAgent(ReflectiveAgent):
    """
    Earth Agent for Phase One - Validates Garden Planner output against the original user request.
    
    This agent maintains persistent context across validation iterations to better
    understand the Garden Planner agent's responses and provide consistent feedback.
    """
    def __init__(
        self, 
        agent_id: str,
        event_queue: EventQueue,
        state_manager: StateManager,
        context_manager: AgentContextManager,
        cache_manager: CacheManager,
        metrics_manager: MetricsManager,
        error_handler: ErrorHandler,
        memory_monitor: MemoryMonitor,
        health_tracker: HealthTracker = None,
        max_validation_cycles: int = 3
    ):
        """
        Initialize the Earth Agent for Phase One.
        
        Args:
            agent_id: Unique identifier for this agent
            event_queue: Event queue for publishing/subscribing to events
            state_manager: State manager for persistent state
            context_manager: Context manager for agent context
            cache_manager: Cache manager for temporary data
            metrics_manager: Metrics manager for tracking metrics
            error_handler: Error handler for error management
            memory_monitor: Memory monitor for resource tracking
            health_tracker: Health tracker for reporting agent health
            max_validation_cycles: Maximum number of validation cycles
        """
        # Define prompt configuration
        prompt_config = AgentPromptConfig(
            system_prompt_base_path="FFTT_system_prompts/core_agents/earth_agent",
            reflection_prompt_name="reflection_prompt",
            refinement_prompt_name="revision_prompt",
            initial_prompt_name="garden_planner_validation_prompt"
        )
        
        # Define circuit breakers
        circuit_breakers = [
            CircuitBreakerDefinition(
                name="validation",
                failure_threshold=3,
                recovery_timeout=30,
                failure_window=120
            ),
            CircuitBreakerDefinition(
                name="reflection",
                failure_threshold=2,
                recovery_timeout=45,
                failure_window=180
            ),
            CircuitBreakerDefinition(
                name="revision",
                failure_threshold=2,
                recovery_timeout=45,
                failure_window=180
            )
        ]
        
        # Initialize base class
        super().__init__(
            agent_id,
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor,
            prompt_config,
            circuit_breakers,
            health_tracker
        )
        
        # Set initial state
        self.development_state = DevelopmentState.INITIALIZING
        
        # Tracking for validation cycles
        self.max_validation_cycles = max_validation_cycles
        self.current_validation_cycle = 0
        self.validation_history = []
        
        # Register with memory monitor
        if self._memory_monitor:
            self._memory_monitor.register_component(
                f"agent_{agent_id}",
                MemoryThresholds(
                    per_resource_max_mb=75,  # Earth agent needs more memory for context
                    warning_percent=0.6,     # 60% warning threshold
                    critical_percent=0.85    # 85% critical threshold
                )
            )
    
    async def validate_garden_planner_output(
        self, 
        user_request: str, 
        garden_planner_output: Dict[str, Any],
        validation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate Garden Planner output against the user's original request.
        
        Args:
            user_request: The original user request
            garden_planner_output: The Garden Planner's task analysis output
            validation_id: Optional identifier for this validation
            
        Returns:
            Validation result with feedback and category (APPROVED/CORRECTED/REJECTED)
        """
        try:
            # Initialize validation tracking
            self.development_state = DevelopmentState.VALIDATING
            
            # Generate validation ID if not provided
            if not validation_id:
                validation_id = f"validation_{datetime.now().isoformat()}_{self.interface_id}"
            
            # Check if input has valid structure
            if not self._validate_input_structure(garden_planner_output):
                error_message = "Invalid Garden Planner output structure"
                logger.error(f"{error_message}: {garden_planner_output}")
                await self._report_agent_health(
                    custom_status="CRITICAL",
                    description=error_message,
                    metadata={
                        "development_state": "VALIDATING",
                        "error": error_message
                    }
                )
                return self._create_error_validation_response(error_message)
            
            # Prepare validation context
            validation_context = {
                "user_request": user_request,
                "garden_planner_output": garden_planner_output,
                "validation_id": validation_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Track memory usage of validation context
            await self.track_dict_memory("validation_context", validation_context)
            
            # Store validation context in state
            await self._state_manager.set_state(
                f"earth_agent:validation_context:{validation_id}",
                validation_context,
                ResourceType="STATE"
            )
            
            # Add validation history to context if available
            if self.validation_history:
                validation_context["validation_history"] = self.validation_history
            
            # Process validation with circuit breaker protection
            try:
                # Convert context to conversation string
                conversation = json.dumps(validation_context, indent=2)
                
                # Perform validation using garden_planner_validation_prompt
                validation_result = await self.get_circuit_breaker("validation").execute(
                    lambda: self.process_with_validation(
                        conversation=f"Validate Garden Planner output against user request: {conversation}",
                        system_prompt_info=(self._prompt_config.system_prompt_base_path, 
                                          self._prompt_config.initial_prompt_name)
                    )
                )
                
                # Apply reflection and revision to improve validation
                validation_result = await self._reflect_and_revise_validation(
                    validation_result, 
                    validation_context
                )
                
                # Update validation history
                self._update_validation_history(validation_result, validation_id)
                
                # Record validation metrics
                await self._record_validation_metrics(validation_result)
                
                # Set appropriate development state based on validation result
                await self._update_state_from_validation(validation_result)
                
                return validation_result
                
            except Exception as e:
                logger.error(f"Validation circuit open or error occurred: {str(e)}")
                self.development_state = DevelopmentState.ERROR
                
                await self._report_agent_health(
                    custom_status="CRITICAL",
                    description=f"Validation error: {str(e)}",
                    metadata={
                        "development_state": "ERROR",
                        "error": str(e)
                    }
                )
                
                return self._create_error_validation_response(str(e))
                
        except Exception as e:
            logger.error(f"Unexpected error in validate_garden_planner_output: {str(e)}")
            self.development_state = DevelopmentState.ERROR
            
            await self._report_agent_health(
                custom_status="CRITICAL",
                description=f"Validation process error: {str(e)}",
                metadata={
                    "development_state": "ERROR",
                    "error": str(e)
                }
            )
            
            return self._create_error_validation_response(str(e))
    
    async def _reflect_and_revise_validation(
        self, 
        validation_result: Dict[str, Any],
        validation_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply reflection and revision to improve validation.
        
        Args:
            validation_result: Initial validation result
            validation_context: Original validation context
            
        Returns:
            Improved validation result after reflection and revision
        """
        # Skip reflection if validation was an error response
        if "error" in validation_result:
            return validation_result
            
        try:
            # Prepare reflection context
            reflection_context = {
                "validation_context": validation_context,
                "validation_result": validation_result,
                "timestamp": datetime.now().isoformat()
            }
            
            # Process reflection with circuit breaker
            reflection_result = await self.get_circuit_breaker("reflection").execute(
                lambda: self.process_with_validation(
                    conversation=json.dumps(reflection_context, indent=2),
                    system_prompt_info=(self._prompt_config.system_prompt_base_path, 
                                      "reflection_prompt")
                )
            )
            
            # Skip revision if reflection suggests no critical improvements
            critical_improvements = reflection_result.get("reflection_results", {}).get("overall_assessment", {}).get("critical_improvements", [])
            if not any(item.get("importance") == "critical" for item in critical_improvements):
                logger.info("Reflection indicates no critical improvements needed, skipping revision")
                return validation_result
                
            # Prepare revision context
            revision_context = {
                "validation_context": validation_context,
                "validation_result": validation_result,
                "reflection_result": reflection_result,
                "timestamp": datetime.now().isoformat()
            }
            
            # Process revision with circuit breaker
            revision_result = await self.get_circuit_breaker("revision").execute(
                lambda: self.process_with_validation(
                    conversation=json.dumps(revision_context, indent=2),
                    system_prompt_info=(self._prompt_config.system_prompt_base_path, 
                                      "revision_prompt")
                )
            )
            
            # Extract revised validation
            if "revision_results" in revision_result and "revised_validation" in revision_result["revision_results"]:
                revised_validation = revision_result["revision_results"]["revised_validation"]
                
                # Add revision metadata
                if "metadata" not in revised_validation:
                    revised_validation["metadata"] = {}
                    
                revised_validation["metadata"]["revision_applied"] = True
                revised_validation["metadata"]["revision_timestamp"] = datetime.now().isoformat()
                
                # Store reflection and revision results in state
                await self._state_manager.set_state(
                    f"earth_agent:reflection:{validation_context.get('validation_id')}",
                    reflection_result,
                    ResourceType="STATE"
                )
                
                await self._state_manager.set_state(
                    f"earth_agent:revision:{validation_context.get('validation_id')}",
                    revision_result,
                    ResourceType="STATE"
                )
                
                return revised_validation
            else:
                logger.warning("Revision process did not produce revised validation")
                return validation_result
                
        except Exception as e:
            logger.error(f"Error in reflection/revision process: {str(e)}")
            # If reflection/revision fails, return original validation
            return validation_result
    
    def _update_validation_history(self, validation_result: Dict[str, Any], validation_id: str):
        """Update validation history with current result."""
        history_entry = {
            "validation_id": validation_id,
            "timestamp": datetime.now().isoformat(),
            "validation_category": validation_result.get("validation_result", {}).get("validation_category", "UNKNOWN"),
            "issue_count": len(validation_result.get("architectural_issues", [])),
            "issues_by_severity": self._count_issues_by_severity(validation_result.get("architectural_issues", []))
        }
        
        self.validation_history.append(history_entry)
        
        # Keep validation history to a reasonable size
        if len(self.validation_history) > 10:
            self.validation_history = self.validation_history[-10:]
    
    def _count_issues_by_severity(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count issues by severity level."""
        counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        
        for issue in issues:
            severity = issue.get("severity", "UNKNOWN")
            if severity in counts:
                counts[severity] += 1
                
        return counts
        
    async def _record_validation_metrics(self, validation_result: Dict[str, Any]):
        """Record metrics for the validation process."""
        if not self._metrics_manager:
            return
            
        validation_category = validation_result.get("validation_result", {}).get("validation_category", "UNKNOWN")
        issues = validation_result.get("architectural_issues", [])
        
        # Record validation result
        await self._metrics_manager.record_metric(
            "earth_agent:validation",
            1.0,
            metadata={
                "category": validation_category,
                "issue_count": len(issues),
                "revision_applied": validation_result.get("metadata", {}).get("revision_applied", False)
            }
        )
        
        # Record issue counts by severity
        issue_counts = self._count_issues_by_severity(issues)
        for severity, count in issue_counts.items():
            await self._metrics_manager.record_metric(
                f"earth_agent:issues:{severity.lower()}",
                count
            )
    
    async def _update_state_from_validation(self, validation_result: Dict[str, Any]):
        """Update development state based on validation result."""
        validation_category = validation_result.get("validation_result", {}).get("validation_category", "UNKNOWN")
        
        if validation_category == "APPROVED":
            self.development_state = DevelopmentState.COMPLETE
            await self._report_agent_health(
                custom_status="HEALTHY",
                description="Validation approved",
                metadata={
                    "development_state": "COMPLETE",
                    "validation_category": validation_category
                }
            )
        elif validation_category == "CORRECTED":
            self.development_state = DevelopmentState.COMPLETE
            await self._report_agent_health(
                custom_status="HEALTHY",
                description="Validation completed with corrections",
                metadata={
                    "development_state": "COMPLETE", 
                    "validation_category": validation_category
                }
            )
        elif validation_category == "REJECTED":
            self.development_state = DevelopmentState.REFINING
            await self._report_agent_health(
                custom_status="DEGRADED",
                description="Validation rejected, refinement needed",
                metadata={
                    "development_state": "REFINING",
                    "validation_category": validation_category
                }
            )
        else:
            # Unknown validation category
            self.development_state = DevelopmentState.ERROR
            await self._report_agent_health(
                custom_status="CRITICAL",
                description=f"Unknown validation category: {validation_category}",
                metadata={
                    "development_state": "ERROR",
                    "validation_category": validation_category
                }
            )
    
    def _validate_input_structure(self, garden_planner_output: Dict[str, Any]) -> bool:
        """Validate that the Garden Planner output has the expected structure."""
        try:
            # Check for task_analysis key
            if "task_analysis" not in garden_planner_output:
                return False
                
            task_analysis = garden_planner_output["task_analysis"]
            
            # Check for required top-level keys
            required_keys = ["original_request", "interpreted_goal", "scope", 
                            "technical_requirements", "constraints", "considerations"]
                            
            if not all(key in task_analysis for key in required_keys):
                return False
                
            # Check for required sub-structure
            if not all(key in task_analysis["scope"] for key in ["included", "excluded", "assumptions"]):
                return False
                
            if not all(key in task_analysis["technical_requirements"] for key in 
                      ["languages", "frameworks", "apis", "infrastructure"]):
                return False
                
            if not all(key in task_analysis["constraints"] for key in 
                      ["technical", "business", "performance"]):
                return False
                
            if not all(key in task_analysis["considerations"] for key in 
                      ["security", "scalability", "maintainability"]):
                return False
                
            return True
            
        except (TypeError, KeyError):
            return False
    
    def _create_error_validation_response(self, error_message: str) -> Dict[str, Any]:
        """Create a validation response for error conditions."""
        return {
            "error": error_message,
            "validation_result": {
                "validation_category": "REJECTED",
                "is_valid": False,
                "explanation": f"Validation error: {error_message}"
            },
            "architectural_issues": [{
                "issue_id": "system_error",
                "severity": "CRITICAL",
                "issue_type": "technical_misalignment",
                "description": f"System error during validation: {error_message}",
                "affected_areas": ["validation_process"],
                "suggested_resolution": "Check system logs and retry validation",
                "alignment_with_user_request": "Cannot be determined due to error"
            }],
            "metadata": {
                "validation_timestamp": datetime.now().isoformat(),
                "validation_version": "1.0",
                "original_agent": "garden_planner",
                "key_decision_factors": ["system_error"]
            }
        }
    
    async def get_validation_history(self) -> List[Dict[str, Any]]:
        """Get the validation history for this agent."""
        return self.validation_history
        
    async def reset_validation_cycle_counter(self):
        """Reset the validation cycle counter to start a new validation sequence."""
        self.current_validation_cycle = 0
        
    async def increment_validation_cycle(self):
        """Increment the validation cycle counter."""
        self.current_validation_cycle += 1
        
    async def get_current_validation_cycle(self) -> int:
        """Get the current validation cycle number."""
        return self.current_validation_cycle
        
    async def has_reached_max_cycles(self) -> bool:
        """Check if the maximum validation cycles have been reached."""
        return self.current_validation_cycle >= self.max_validation_cycles
    
    # Base class overrides
        
    async def reflect(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to standardized reflection method."""
        return await self.standard_reflect(output, "validation")

    async def refine(self, output: Dict[str, Any], refinement_guidance: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to standardized refinement method."""
        return await self.standard_refine(output, refinement_guidance, "validation")