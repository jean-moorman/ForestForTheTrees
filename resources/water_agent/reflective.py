"""
Reflective Water Agent implementation.

This module provides a ReflectiveAgent implementation for the Water Agent
to standardize the reflection and refinement process across all agents.
"""

import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from phase_one.agents.base import ReflectiveAgent
from phase_one.models.refinement import AgentPromptConfig
from phase_one.monitoring.circuit_breakers import CircuitBreakerDefinition
from phase_one.models.enums import DevelopmentState

from FFTT_system_prompts.core_agents.water_agent import (
    MISUNDERSTANDING_DETECTION_PROMPT,
    WATER_AGENT_REFLECTION_PROMPT,
    WATER_AGENT_REVISION_PROMPT
)

logger = logging.getLogger(__name__)

class WaterAgentReflective(ReflectiveAgent):
    """
    Reflective Water Agent for misunderstanding detection and coordination.
    
    This class extends the ReflectiveAgent to provide standardized reflection
    capabilities for the Water Agent components, particularly misunderstanding
    detection.
    """
    
    def __init__(
        self,
        agent_id: str,
        event_queue: Any,
        state_manager: Any,
        context_manager: Any,
        cache_manager: Any,
        metrics_manager: Any,
        error_handler: Any,
        memory_monitor: Any,
        health_tracker: Optional[Any] = None,
        max_reflection_cycles: int = 2
    ):
        """
        Initialize the Reflective Water Agent.
        
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
            max_reflection_cycles: Maximum number of reflection cycles
        """
        # Define prompt configuration
        prompt_config = AgentPromptConfig(
            system_prompt_base_path="FFTT_system_prompts/core_agents/water_agent",
            reflection_prompt_name="reflection_prompt",
            refinement_prompt_name="revision_prompt",
            initial_prompt_name="misunderstanding_detection_prompt"
        )
        
        # Define circuit breakers
        circuit_breakers = [
            CircuitBreakerDefinition(
                name="detection",
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
        
        # Tracking for reflection cycles
        self.max_reflection_cycles = max_reflection_cycles
        self.current_reflection_cycle = 0
        
    async def detect_misunderstandings(
        self,
        first_agent_output: str,
        second_agent_output: str,
        use_reflection: bool = True
    ) -> Dict[str, Any]:
        """
        Detect misunderstandings between two agent outputs with reflection capability.
        
        Args:
            first_agent_output: Output from the first agent
            second_agent_output: Output from the second agent
            use_reflection: Whether to use reflection to improve detection results
            
        Returns:
            Dict containing detected misunderstandings and questions
        """
        try:
            # Set to analyzing state
            self.development_state = DevelopmentState.ANALYZING
            
            # Prepare the detection context
            detection_id = f"detection_{datetime.now().isoformat()}_{self.interface_id}"
            
            detection_context = {
                "first_agent_output": first_agent_output,
                "second_agent_output": second_agent_output,
                "detection_id": detection_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Store context in state
            await self._state_manager.set_state(
                f"water_agent:detection_context:{detection_id}",
                detection_context,
                ResourceType="STATE"
            )
            
            # Format the detection prompt
            formatted_prompt = MISUNDERSTANDING_DETECTION_PROMPT.format(
                first_agent_output=first_agent_output,
                second_agent_output=second_agent_output
            )
            
            # Process detection with circuit breaker protection
            try:
                # Perform misunderstanding detection using misunderstanding_detection_prompt
                detection_result = await self.get_circuit_breaker("detection").execute(
                    lambda: self.process_with_validation(
                        conversation=formatted_prompt,
                        system_prompt_info=(self._prompt_config.system_prompt_base_path, 
                                          self._prompt_config.initial_prompt_name)
                    )
                )
                
                # Apply reflection and revision if enabled
                if use_reflection:
                    # Reset reflection cycle counter
                    self.current_reflection_cycle = 0
                    
                    # Apply reflection and revision to improve detection result
                    detection_result = await self._reflect_and_revise_detection(
                        detection_result,
                        detection_context
                    )
                
                # Update state to complete
                self.development_state = DevelopmentState.COMPLETE
                
                return detection_result
                
            except Exception as e:
                logger.error(f"Detection circuit open or error occurred: {str(e)}")
                self.development_state = DevelopmentState.ERROR
                
                return {
                    "error": f"Detection error: {str(e)}",
                    "misunderstandings": [],
                    "first_agent_questions": [],
                    "second_agent_questions": []
                }
                
        except Exception as e:
            logger.error(f"Unexpected error in detect_misunderstandings: {str(e)}")
            self.development_state = DevelopmentState.ERROR
            
            return {
                "error": f"Detection process error: {str(e)}",
                "misunderstandings": [],
                "first_agent_questions": [],
                "second_agent_questions": []
            }
            
    async def _reflect_and_revise_detection(
        self,
        detection_result: Dict[str, Any],
        detection_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply reflection and revision to improve misunderstanding detection results.
        
        Args:
            detection_result: Initial detection result
            detection_context: Original detection context
            
        Returns:
            Improved detection result after reflection and revision
        """
        # Skip reflection if detection was an error response
        if "error" in detection_result:
            return detection_result
        
        # Increment the reflection cycle
        self.current_reflection_cycle += 1
        
        # Check if we've reached the maximum cycles
        if self.current_reflection_cycle > self.max_reflection_cycles:
            logger.info(f"Maximum reflection cycles reached ({self.max_reflection_cycles}), using current result")
            return detection_result
            
        try:
            # Set state to validating for reflection
            self.development_state = DevelopmentState.VALIDATING
            
            # Prepare reflection context
            reflection_context = {
                "detection_context": detection_context,
                "detection_result": detection_result,
                "reflection_cycle": self.current_reflection_cycle,
                "timestamp": datetime.now().isoformat()
            }
            
            # Use standardized reflection method from ReflectiveAgent
            reflection_result = await self.standard_reflect(
                output=reflection_context,
                circuit_name="reflection",
                prompt_path=self._prompt_config.system_prompt_base_path,
                prompt_name="reflection_prompt"
            )
            
            # Check if reflection suggests critical improvements
            critical_improvements = reflection_result.get("reflection_results", {}).get("overall_assessment", {}).get("critical_improvements", [])
            if not any(item.get("importance") == "critical" for item in critical_improvements):
                logger.info("Reflection indicates no critical improvements needed, skipping revision")
                return detection_result
                
            # Set state to refining
            self.development_state = DevelopmentState.REFINING
            
            # Prepare revision context
            revision_context = {
                "detection_context": detection_context,
                "original_detection_results": detection_result,
                "reflection_assessment": reflection_result,
                "reflection_cycle": self.current_reflection_cycle,
                "timestamp": datetime.now().isoformat()
            }
            
            # Use standardized refinement method from ReflectiveAgent
            revision_result = await self.standard_refine(
                output=revision_context,
                refinement_guidance=reflection_result,
                circuit_name="revision",
                prompt_path=self._prompt_config.system_prompt_base_path,
                prompt_name="revision_prompt"
            )
            
            # Store reflection and revision results in state
            await self._state_manager.set_state(
                f"water_agent:reflection:{detection_context.get('detection_id')}_{self.current_reflection_cycle}",
                reflection_result,
                ResourceType="STATE"
            )
            
            await self._state_manager.set_state(
                f"water_agent:revision:{detection_context.get('detection_id')}_{self.current_reflection_cycle}",
                revision_result,
                ResourceType="STATE"
            )
            
            # Check if we should perform another reflection cycle
            # If the revision result suggests further improvement, recurse
            needs_another_cycle = revision_result.get("needs_further_reflection", False)
            if needs_another_cycle and self.current_reflection_cycle < self.max_reflection_cycles:
                logger.info(f"Revision suggests further improvement, starting reflection cycle {self.current_reflection_cycle + 1}")
                # Use the revised detection result for the next cycle
                revised_detection = revision_result.get("revised_detection", detection_result)
                return await self._reflect_and_revise_detection(revised_detection, detection_context)
            
            # Return the revised detection result
            return revision_result.get("revised_detection", detection_result)
                
        except Exception as e:
            logger.error(f"Error in reflection/revision process: {str(e)}")
            # If reflection/revision fails, return original detection result
            return detection_result
            
    # Base class overrides
        
    async def reflect(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to standardized reflection method."""
        return await self.standard_reflect(output, "detection")

    async def refine(self, output: Dict[str, Any], refinement_guidance: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to standardized refinement method."""
        return await self.standard_refine(output, refinement_guidance, "detection")