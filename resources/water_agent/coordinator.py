"""
Water Agent Coordinator module for facilitating agent coordination.

This module provides the WaterAgentCoordinator class that manages the coordination
process between sequential agents, detecting and resolving misunderstandings.
"""

import logging
import asyncio
import json
import uuid
from typing import Dict, List, Optional, Tuple, Any, Set, Union
from enum import Enum, auto
import os

from resources.base_resource import BaseResource
from resources.errors import CoordinationError, MisunderstandingDetectionError
from resources.events import ResourceEventTypes
from resources.common import ResourceType
from resources.water_agent.reflective import WaterAgentReflective

# Import system prompts
from FFTT_system_prompts.core_agents.water_agent import (
    MISUNDERSTANDING_DETECTION_PROMPT,
    RESOLUTION_ASSESSMENT_PROMPT,
    CONTEXT_REFINEMENT_PROMPT,
    WATER_AGENT_REFLECTION_PROMPT,
    WATER_AGENT_REVISION_PROMPT
)

logger = logging.getLogger(__name__)


class AmbiguitySeverity(Enum):
    """Classification of ambiguity severity levels for agent coordination."""
    CRITICAL = auto()  # Fundamentally blocks progress, must be resolved
    HIGH = auto()      # Significantly impacts output quality, should be resolved
    MEDIUM = auto()    # Affects clarity but may not impact core functionality
    LOW = auto()       # Minor issues that could be improved but are not harmful


class WaterAgentCoordinator(BaseResource):
    """
    Coordinates communication between sequential agents to resolve misunderstandings.
    
    This class manages the entire coordination process between two sequential agents,
    detecting misunderstandings, generating questions, collecting responses, and
    determining when sufficient clarity has been achieved.
    """
    
    def __init__(self, state_manager=None, event_bus=None, agent_interface=None):
        """
        Initialize the WaterAgentCoordinator.
        
        The WaterAgentCoordinator manages the coordination process between sequential agents,
        detecting and resolving misunderstandings. It now includes self-reflection capabilities
        to improve the accuracy and quality of misunderstanding detection and resolution through
        the standardized ReflectiveAgent pattern.
        
        Args:
            state_manager: Optional state manager for persisting coordination state
            event_bus: Optional event bus for emitting events
            agent_interface: Optional agent interface to use for LLM calls
        """
        super().__init__(state_manager=state_manager, event_bus=event_bus)
        
        # Create or use the provided agent interface
        self.agent_interface = agent_interface
        
        # Initialize detector and trackers with agent interface
        self.misunderstanding_detector = MisunderstandingDetector(agent_interface=agent_interface)
        self.response_handler = QuestionResponseHandler()
        self.resolution_tracker = AmbiguityResolutionTracker(agent_interface=agent_interface)
        
        # Create reflective agent for context refinement
        self._reflective_agent = None
        self._initialize_reflective_agent_async = None
        
        # Import context manager here to avoid circular imports
        try:
            from resources.water_agent.context_manager import WaterAgentContextManager
            self.context_manager = WaterAgentContextManager(state_manager=state_manager, event_bus=event_bus)
        except ImportError:
            logger.warning("Could not import WaterAgentContextManager, using placeholder")
            self.context_manager = None
        
        # Create agent interface if none provided
        if self.agent_interface is None:
            try:
                from resources import (
                    EventQueue, 
                    StateManager, 
                    AgentContextManager, 
                    CacheManager, 
                    MetricsManager, 
                    ErrorHandler,
                    MemoryMonitor
                )
                
                # Initialize required resources for agent interface
                event_queue = EventQueue() if event_bus is None else event_bus
                state_mgr = StateManager(event_queue) if state_manager is None else state_manager
                context_manager = AgentContextManager(event_queue)
                cache_manager = CacheManager(event_queue)
                metrics_manager = MetricsManager(event_queue)
                error_handler = ErrorHandler(event_queue)
                memory_monitor = MemoryMonitor()
                
                # Create the agent interface (delayed import to avoid circular dependency)
                from interfaces.agent.interface import AgentInterface
                self.agent_interface = AgentInterface(
                    agent_id="water_agent_coordinator",
                    event_queue=event_queue,
                    state_manager=state_mgr,
                    context_manager=context_manager,
                    cache_manager=cache_manager,
                    metrics_manager=metrics_manager,
                    error_handler=error_handler,
                    memory_monitor=memory_monitor
                )
                
                # Start event queue if created here
                if event_bus is None:
                    asyncio.create_task(event_queue.start())
                
                # Initialize reflective agent lazily (will be done when needed)
                    
            except (ImportError, AttributeError) as e:
                logger.warning(f"Could not create agent interface, will use placeholder responses: {e}")
                self.agent_interface = None
                
    async def ensure_reflective_agent_initialized(self):
        """Ensure the reflective agent is initialized."""
        if self._reflective_agent is not None:
            return
            
        # If initialization is already in progress, wait for it
        if self._initialize_reflective_agent_async is not None:
            await self._initialize_reflective_agent_async
            return
            
        # Start the initialization
        try:
            self._initialize_reflective_agent_async = asyncio.create_task(self._initialize_reflective_agent())
            await self._initialize_reflective_agent_async
        finally:
            self._initialize_reflective_agent_async = None
            
    async def _initialize_reflective_agent(self):
        """Initialize the reflective agent with necessary dependencies."""
        if self.agent_interface is None:
            logger.warning("Cannot initialize reflective agent without an agent interface")
            return
            
        try:
            # Extract required resources from agent_interface
            event_queue = self.agent_interface._event_queue
            state_manager = self.agent_interface._state_manager
            context_manager = self.agent_interface._context_manager
            cache_manager = self.agent_interface._cache_manager
            metrics_manager = self.agent_interface._metrics_manager
            error_handler = self.agent_interface._error_handler
            memory_monitor = self.agent_interface._memory_monitor
            health_tracker = None  # Optional, can be None
            
            # Create the reflective agent
            self._reflective_agent = WaterAgentReflective(
                agent_id="water_coordinator",
                event_queue=event_queue,
                state_manager=state_manager,
                context_manager=context_manager,
                cache_manager=cache_manager,
                metrics_manager=metrics_manager,
                error_handler=error_handler,
                memory_monitor=memory_monitor,
                health_tracker=health_tracker,
                max_reflection_cycles=1
            )
            
            logger.info("Coordinator reflective agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize reflective agent for coordinator: {str(e)}")
            self._reflective_agent = None
            
    async def coordinate_agents(
        self, 
        first_agent: Any, 
        first_agent_output: str,
        second_agent: Any, 
        second_agent_output: str,
        coordination_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Coordinate communication between two sequential agents to resolve misunderstandings.
        
        Args:
            first_agent: The first agent in the sequence
            first_agent_output: Output from the first agent
            second_agent: The second agent in the sequence
            second_agent_output: Output from the second agent
            coordination_context: Optional context for the coordination process
            
        Returns:
            Tuple containing:
            - Updated first agent output
            - Updated second agent output
            - Coordination metadata/context
        """
        # Initialize coordination context if not provided
        if not coordination_context:
            coordination_context = {
                "coordination_id": str(uuid.uuid4()),
                "start_time": asyncio.get_event_loop().time(),
                "max_iterations": 3,  # Default max iterations
                "severity_threshold": "LOW"  # Default threshold for considering issues resolved
            }
            
        # Create coordination context in the context manager
        coordination_id = coordination_context.get("coordination_id", str(uuid.uuid4()))
        first_agent_id = getattr(first_agent, 'agent_id', str(first_agent))
        second_agent_id = getattr(second_agent, 'agent_id', str(second_agent))
        mode = coordination_context.get("mode", "standard")
        max_iterations = coordination_context.get("max_iterations", 3)
        severity_threshold = coordination_context.get("severity_threshold", "LOW")
        
        # Create the persistent coordination context if context manager is available
        persistent_context = None
        if self.context_manager:
            persistent_context = await self.context_manager.create_coordination_context(
                first_agent_id=first_agent_id,
                second_agent_id=second_agent_id,
                mode=mode,
                max_iterations=max_iterations,
                severity_threshold=severity_threshold,
                coordination_id=coordination_id
            )
            
            # Save the original outputs if context manager is available
            await self.context_manager.save_coordination_outputs(
                coordination_id=coordination_id,
                first_agent_output=first_agent_output,
                second_agent_output=second_agent_output
            )
            
        try:
            # Log and emit event for coordination start
            logger.info(f"Starting coordination between sequential agents: " +
                       f"{first_agent.__class__.__name__} → {second_agent.__class__.__name__}")
            
            await self._emit_event(ResourceEventTypes.RESOURCE_STATE_CHANGED, {
                "coordination_id": coordination_context["coordination_id"],
                "first_agent": getattr(first_agent, 'name', first_agent.__class__.__name__),
                "second_agent": getattr(second_agent, 'name', second_agent.__class__.__name__),
                "first_agent_output_length": len(first_agent_output),
                "second_agent_output_length": len(second_agent_output)
            })
            
            # Store original outputs
            coordination_context["original_first_agent_output"] = first_agent_output
            coordination_context["original_second_agent_output"] = second_agent_output
            
            # Detect initial misunderstandings (with reflection by default)
            misunderstandings, first_agent_questions, second_agent_questions = (
                await self.misunderstanding_detector.detect_misunderstandings(
                    first_agent_output, 
                    second_agent_output,
                    use_reflection=coordination_context.get("use_reflection", True)
                )
            )
            
            # Check if any misunderstandings were detected
            if not misunderstandings:
                logger.info("No misunderstandings detected, coordination not needed")
                
                await self._emit_event(ResourceEventTypes.RESOURCE_STATE_CHANGED, {
                    "coordination_id": coordination_context["coordination_id"],
                    "iterations": 0,
                    "misunderstandings_detected": 0,
                    "misunderstandings_resolved": 0,
                    "duration": asyncio.get_event_loop().time() - coordination_context["start_time"],
                    "status": "no_misunderstandings_detected"
                })
                
                return first_agent_output, second_agent_output, coordination_context
            
            # Log detected misunderstandings
            logger.info(f"Detected {len(misunderstandings)} potential misunderstandings")
            
            # Count misunderstandings by severity
            severity_counts = {}
            for m in misunderstandings:
                severity = m.get("severity", "MEDIUM")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
            await self._emit_event(ResourceEventTypes.RESOURCE_STATE_CHANGED, {
                "coordination_id": coordination_context["coordination_id"],
                "misunderstandings_count": len(misunderstandings),
                "severity_counts": severity_counts,
                "first_agent_questions_count": len(first_agent_questions),
                "second_agent_questions_count": len(second_agent_questions)
            })
                
            # Initialize resolution tracking
            self.resolution_tracker.initialize_tracking(misunderstandings)
            coordination_context["misunderstandings"] = misunderstandings
            
            # Begin coordination iterations
            iteration = 0
            max_iterations = coordination_context.get("max_iterations", 3)
            
            # Begin iterative resolution process
            while not self.resolution_tracker.all_resolved() and iteration < max_iterations:
                iteration += 1
                logger.info(f"Starting coordination iteration {iteration} of {max_iterations}")
                
                # Emit event for iteration start
                await self._emit_event(ResourceEventTypes.RESOURCE_STATE_CHANGED, {
                    "coordination_id": coordination_context["coordination_id"],
                    "iteration": iteration,
                    "max_iterations": max_iterations,
                    "first_agent_questions_count": len(first_agent_questions),
                    "second_agent_questions_count": len(second_agent_questions),
                    "unresolved_issues_count": len(self.resolution_tracker.unresolved_issues)
                })
                
                # Get responses from agents
                first_agent_responses = await self.response_handler.get_agent_responses(
                    first_agent, first_agent_questions
                )
                
                second_agent_responses = await self.response_handler.get_agent_responses(
                    second_agent, second_agent_questions
                )
                
                # Track responses in context
                coordination_context[f"iteration_{iteration}"] = {
                    "first_agent_questions": first_agent_questions,
                    "first_agent_responses": first_agent_responses,
                    "second_agent_questions": second_agent_questions,
                    "second_agent_responses": second_agent_responses,
                    "timestamp": asyncio.get_event_loop().time()
                }
                
                # Assess resolution progress
                resolved_issues, unresolved_issues, new_first_questions, new_second_questions = (
                    await self.resolution_tracker.assess_resolution(
                        misunderstandings,
                        first_agent_questions,
                        first_agent_responses,
                        second_agent_questions,
                        second_agent_responses
                    )
                )
                
                # Track resolution progress in context
                coordination_context[f"resolution_{iteration}"] = {
                    "resolved_issues_count": len(resolved_issues),
                    "unresolved_issues_count": len(unresolved_issues),
                    "resolved_issues": resolved_issues,
                    "unresolved_issues": unresolved_issues
                }
                
                # Update persistent context if available
                if self.context_manager:
                    await self.context_manager.update_coordination_iteration(
                        coordination_id=coordination_id,
                        iteration=iteration,
                        first_agent_questions=first_agent_questions,
                        first_agent_responses=first_agent_responses,
                        second_agent_questions=second_agent_questions,
                        second_agent_responses=second_agent_responses,
                        resolved=resolved_issues,
                        unresolved=unresolved_issues
                    )
                
                # Emit events for resolved misunderstandings
                for resolved in resolved_issues:
                    await self._emit_event(ResourceEventTypes.RESOURCE_STATE_CHANGED, {
                        "coordination_id": coordination_context["coordination_id"],
                        "misunderstanding_id": resolved.get("id", "unknown"),
                        "resolution_summary": resolved.get("resolution_summary", ""),
                        "iteration": iteration
                    })
                
                # Update questions for next iteration
                first_agent_questions = new_first_questions
                second_agent_questions = new_second_questions
                
                # Check if we need to continue
                if not first_agent_questions and not second_agent_questions:
                    logger.info("No further questions needed, ending coordination")
                    break
            
            # Generate final outputs with resolved understanding
            updated_first_output, updated_second_output, refinement_summary = await self._generate_final_outputs(
                first_agent, first_agent_output,
                second_agent, second_agent_output,
                coordination_context
            )
            
            # Store final outputs and summary in context
            coordination_context["final_first_agent_output"] = updated_first_output
            coordination_context["final_second_agent_output"] = updated_second_output
            coordination_context["refinement_summary"] = refinement_summary
            coordination_context["total_iterations"] = iteration
            coordination_context["end_time"] = asyncio.get_event_loop().time()
            coordination_context["duration"] = coordination_context["end_time"] - coordination_context["start_time"]
            
            # Determine coordination status
            if self.resolution_tracker.all_resolved():
                status = "all_issues_resolved"
            elif iteration >= max_iterations:
                status = "max_iterations_reached"
            else:
                status = "partially_resolved"
                
            # Update persistent context with final outputs if context manager available
            if self.context_manager:
                await self.context_manager.complete_coordination(
                    coordination_id=coordination_id,
                    first_agent_final_output=updated_first_output,
                    second_agent_final_output=updated_second_output,
                    final_status=status
                )
                
                # Prune temporary data if configured to do so
                if coordination_context.get("prune_temp_data", True):
                    await self.context_manager.prune_temporary_data(
                        coordination_id=coordination_id,
                        keep_final_outputs=True
                    )
                
            # Emit completion event
            await self._emit_event(ResourceEventTypes.RESOURCE_STATE_CHANGED, {
                "coordination_id": coordination_context["coordination_id"],
                "iterations": iteration,
                "duration": coordination_context["duration"],
                "resolved_misunderstandings": len(self.resolution_tracker.resolved_issues),
                "unresolved_misunderstandings": len(self.resolution_tracker.unresolved_issues),
                "status": status,
                "first_agent_output_changed": updated_first_output != first_agent_output,
                "second_agent_output_changed": updated_second_output != second_agent_output
            })
            
            # Return the updated outputs and context
            return updated_first_output, updated_second_output, coordination_context
            
        except Exception as e:
            # Log the error and emit event
            logger.error(f"Error during agent coordination: {str(e)}")
            
            await self._emit_event(ResourceEventTypes.RESOURCE_STATE_CHANGED, {
                "coordination_id": coordination_context.get("coordination_id", "unknown"),
                "error": str(e),
                "error_type": type(e).__name__,
                "trace": getattr(e, "__traceback__", "No traceback available")
            })
            
            # Add error info to context before raising
            coordination_context["error"] = str(e)
            coordination_context["error_type"] = type(e).__name__
            coordination_context["error_time"] = asyncio.get_event_loop().time()
            
            # Raise a coordination error
            raise CoordinationError(f"Failed to coordinate agents: {str(e)}")
    
    async def _generate_final_outputs(
        self,
        first_agent: Any,
        first_agent_output: str,
        second_agent: Any,
        second_agent_output: str,
        coordination_context: Dict[str, Any]
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Generate final outputs for both agents with resolved misunderstandings.
        
        This function consolidates the understanding gained through the coordination
        process to update the outputs of both agents. It can use a reflective agent
        for enhanced context refinement when available.
        
        Args:
            first_agent: The first agent in the sequence
            first_agent_output: Original output from the first agent
            second_agent: The second agent in the sequence
            second_agent_output: Original output from the second agent
            coordination_context: The context from the coordination process
            
        Returns:
            Tuple containing:
            - Updated first agent output
            - Updated second agent output
            - Refinement summary dictionary
        """
        # If no misunderstandings were found or all were unresolvable,
        # return original outputs
        if not coordination_context.get("misunderstandings"):
            return first_agent_output, second_agent_output, {
                "first_agent_changes": [],
                "second_agent_changes": []
            }
            
        # If no iterations occurred, return original outputs
        if "iteration_1" not in coordination_context:
            return first_agent_output, second_agent_output, {
                "first_agent_changes": [],
                "second_agent_changes": []
            }
        
        # Build a record of the coordination process for the prompt
        coordination_record = []
        
        # Get total iterations
        total_iterations = coordination_context.get("total_iterations", 0)
        
        # Build the record of each iteration
        for i in range(1, total_iterations + 1):
            iteration_key = f"iteration_{i}"
            if iteration_key not in coordination_context:
                continue
                
            # Get the questions and responses for this iteration
            iteration_data = coordination_context[iteration_key]
            
            # Format first agent Q&A
            first_agent_qa = []
            for q, a in zip(iteration_data.get("first_agent_questions", []), 
                           iteration_data.get("first_agent_responses", [])):
                first_agent_qa.append(f"Q: {q}\nA: {a}")
                
            # Format second agent Q&A
            second_agent_qa = []
            for q, a in zip(iteration_data.get("second_agent_questions", []), 
                           iteration_data.get("second_agent_responses", [])):
                second_agent_qa.append(f"Q: {q}\nA: {a}")
                
            # Add to coordination record
            coordination_record.append(f"--- Iteration {i} ---\n")
            
            if first_agent_qa:
                coordination_record.append(f"First Agent ({first_agent.__class__.__name__}) Q&A:\n")
                coordination_record.append("\n\n".join(first_agent_qa))
                coordination_record.append("\n")
                
            if second_agent_qa:
                coordination_record.append(f"Second Agent ({second_agent.__class__.__name__}) Q&A:\n")
                coordination_record.append("\n\n".join(second_agent_qa))
                coordination_record.append("\n")
        
        # Format misunderstanding resolution information
        misunderstanding_resolution = []
        
        # Add resolved issues
        misunderstanding_resolution.append("--- Resolved Misunderstandings ---\n")
        for issue_id in self.resolution_tracker.resolved_issues:
            # Find the resolution summary from the context
            resolution_summary = "No details available"
            for i in range(1, total_iterations + 1):
                resolution_key = f"resolution_{i}"
                if resolution_key in coordination_context:
                    for resolved in coordination_context[resolution_key].get("resolved_issues", []):
                        if resolved.get("id") == issue_id:
                            resolution_summary = resolved.get("resolution_summary", "No details available")
                            break
            
            misunderstanding_resolution.append(f"ID: {issue_id}\nResolution: {resolution_summary}\n")
        
        # Add unresolved issues
        misunderstanding_resolution.append("--- Unresolved Misunderstandings ---\n")
        for issue_id, issue in self.resolution_tracker.unresolved_issues.items():
            severity = issue.get("severity", "UNKNOWN")
            description = issue.get("description", "No description available")
            misunderstanding_resolution.append(f"ID: {issue_id}\nSeverity: {severity}\nDescription: {description}\n")
        
        # Combine all parts into a single string
        coordination_record_str = "\n".join(coordination_record)
        misunderstanding_resolution_str = "\n".join(misunderstanding_resolution)
        
        # Try to use reflective agent if available
        use_reflective = coordination_context.get("use_reflection", True)
        
        if use_reflective and self.agent_interface is not None:
            try:
                # Initialize reflective agent if not already done
                await self.ensure_reflective_agent_initialized()
                
                if self._reflective_agent is not None:
                    logger.info("Using reflective agent for context refinement")
                    
                    # Prepare the refinement context
                    refinement_context = {
                        "first_agent_output": first_agent_output,
                        "second_agent_output": second_agent_output,
                        "coordination_record": coordination_record_str,
                        "misunderstanding_resolution": misunderstanding_resolution_str,
                        "refinement_id": f"refine_{uuid.uuid4()}"
                    }
                    
                    # Use the reflective agent to process the context refinement
                    # Format the context refinement prompt - this is needed because the
                    # reflective agent doesn't have access to CONTEXT_REFINEMENT_PROMPT directly
                    formatted_prompt = CONTEXT_REFINEMENT_PROMPT.format(
                        first_agent_output=first_agent_output,
                        second_agent_output=second_agent_output,
                        coordination_record=coordination_record_str,
                        misunderstanding_resolution=misunderstanding_resolution_str
                    )
                    
                    # Set up the reflective agent processing context
                    processing_context = {
                        "refinement_context": refinement_context,
                        "prompt": formatted_prompt
                    }
                    
                    # Use the reflective agent to process with built-in reflection
                    refinement_result = await self._reflective_agent.process_with_validation(
                        conversation=formatted_prompt,
                        system_prompt_info=("FFTT_system_prompts/core_agents/water_agent", "context_refinement_prompt"),
                        current_phase="context_refinement",
                        operation_id=refinement_context["refinement_id"]
                    )
                    
                    # Extract the refined outputs and summary
                    # refinement_result is the raw response, which should be a parsed JSON object already
                    refined_first_output = refinement_result.get("refined_first_agent_output", first_agent_output)
                    refined_second_output = refinement_result.get("refined_second_agent_output", second_agent_output)
                    refinement_summary = refinement_result.get("refinement_summary", {
                        "first_agent_changes": [],
                        "second_agent_changes": []
                    })
                    
                    logger.info("Successfully used reflective agent for context refinement")
                    
                    # Log refinement results
                    logger.info(f"Generated refined outputs: " +
                              f"First agent changes: {len(refinement_summary.get('first_agent_changes', []))}, " +
                              f"Second agent changes: {len(refinement_summary.get('second_agent_changes', []))}")
                    
                    return refined_first_output, refined_second_output, refinement_summary
            except Exception as reflective_e:
                logger.warning(f"Error using reflective agent for context refinement, falling back to direct approach: {str(reflective_e)}")
                # Fall through to direct approach if reflective agent fails
        
        # Direct approach without reflective agent
        try:
            # Create the prompt for the context refinement
            formatted_prompt = CONTEXT_REFINEMENT_PROMPT.format(
                first_agent_output=first_agent_output,
                second_agent_output=second_agent_output,
                coordination_record=coordination_record_str,
                misunderstanding_resolution=misunderstanding_resolution_str
            )
            
            # Use the agent interface if available, otherwise fall back to placeholder
            if self.agent_interface is not None:
                # Call the LLM to generate refined outputs using agent interface
                refinement_response = await self.agent_interface.process_with_validation(
                    conversation=formatted_prompt,
                    system_prompt_info=("FFTT_system_prompts/core_agents/water_agent", "context_refinement_prompt"),
                    current_phase="context_refinement",
                    operation_id=f"context_refine_{uuid.uuid4()}"
                )
                
                # Extract response content if needed
                if isinstance(refinement_response, dict):
                    if "content" in refinement_response:
                        refinement_response = refinement_response["content"]
                    elif "response" in refinement_response:
                        refinement_response = refinement_response["response"]
            else:
                # Use the internal _call_llm method as fallback
                refinement_response = await self._call_llm(formatted_prompt, "context_refinement")
            
            # Parse the response
            parsed_response = self._parse_json_response(refinement_response)
            
            # Extract the refined outputs and summary
            refined_first_output = parsed_response.get("refined_first_agent_output", first_agent_output)
            refined_second_output = parsed_response.get("refined_second_agent_output", second_agent_output)
            refinement_summary = parsed_response.get("refinement_summary", {
                "first_agent_changes": [],
                "second_agent_changes": []
            })
            
            # Log refinement results
            logger.info(f"Generated refined outputs: " +
                      f"First agent changes: {len(refinement_summary.get('first_agent_changes', []))}, " +
                      f"Second agent changes: {len(refinement_summary.get('second_agent_changes', []))}")
            
            return refined_first_output, refined_second_output, refinement_summary
            
        except Exception as e:
            logger.error(f"Error generating refined outputs: {str(e)}")
            
            # In case of error, return original outputs
            return first_agent_output, second_agent_output, {
                "first_agent_changes": [],
                "second_agent_changes": [],
                "error": str(e)
            }
    
    async def _call_llm(self, prompt: str, prompt_type: str = "context_refinement") -> str:
        """
        Make a call to the LLM with the given prompt using the agent interface.
        
        Args:
            prompt: The prompt to send to the LLM
            prompt_type: Type of prompt (context_refinement, misunderstanding_detection, or resolution_assessment)
            
        Returns:
            The LLM's response as a string
        """
        # If agent interface is available, use it
        if self.agent_interface is not None:
            try:
                # Map prompt type to system prompt info
                system_prompt_map = {
                    "context_refinement": ("FFTT_system_prompts/core_agents/water_agent", "context_refinement_prompt"),
                    "misunderstanding_detection": ("FFTT_system_prompts/core_agents/water_agent", "misunderstanding_detection_prompt"),
                    "resolution_assessment": ("FFTT_system_prompts/core_agents/water_agent", "resolution_assessment_prompt")
                }
                
                # Get the appropriate system prompt info
                system_prompt_info = system_prompt_map.get(
                    prompt_type, 
                    ("FFTT_system_prompts/core_agents/water_agent", "context_refinement_prompt")
                )
                
                # Process with validation
                response = await self.agent_interface.process_with_validation(
                    conversation=prompt,
                    system_prompt_info=system_prompt_info,
                    current_phase=f"water_agent_{prompt_type}",
                    operation_id=f"water_{uuid.uuid4()}"
                )
                
                # Extract response content - different formats possible
                if isinstance(response, dict):
                    if "content" in response:
                        return response["content"]
                    elif "response" in response:
                        return response["response"]
                    else:
                        # Return the whole response as JSON string
                        return json.dumps(response)
                elif isinstance(response, str):
                    return response
                else:
                    logger.warning(f"Unexpected response type from agent: {type(response)}")
                    return json.dumps({})
                    
            except Exception as e:
                logger.error(f"Error using agent interface for LLM call: {str(e)}")
                # Fall through to placeholder implementation
        
        # Placeholder implementation if agent interface is not available
        logger.warning("Using placeholder LLM implementation - replace with actual implementation")
        await asyncio.sleep(0.1)  # Simulate API call latency
        
        # For the context refinement prompt, return a sample response
        if prompt_type == "context_refinement" or "Context Refinement System" in prompt:
            return json.dumps({
                "refined_first_agent_output": "Refined first agent output with clarifications.",
                "refined_second_agent_output": "Refined second agent output with better understanding of the first agent's intent.",
                "refinement_summary": {
                    "first_agent_changes": [
                        "Clarified terminology used in section X",
                        "Added more explicit instructions in section Y"
                    ],
                    "second_agent_changes": [
                        "Updated understanding of requirement Z",
                        "Corrected misinterpretation of first agent's instructions"
                    ]
                }
            })
        elif prompt_type == "misunderstanding_detection" or "Misunderstanding Detection System" in prompt:
            return json.dumps({
                "misunderstandings": [],
                "first_agent_questions": [],
                "second_agent_questions": []
            })
        elif prompt_type == "resolution_assessment" or "Resolution Assessment System" in prompt:
            return json.dumps({
                "resolved_misunderstandings": [],
                "unresolved_misunderstandings": [],
                "new_first_agent_questions": [],
                "new_second_agent_questions": [],
                "require_further_iteration": False,
                "iteration_recommendation": "All issues resolved."
            })
        
        # Default empty response
        return "{}"
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse a JSON response from the LLM.
        
        Args:
            response: The LLM's response as a string
            
        Returns:
            The parsed JSON as a dictionary
        """
        try:
            # Extract JSON from the response
            json_start = response.find('{')
            json_end = response.rfind('}')
            
            if json_start == -1 or json_end == -1:
                logger.warning("Could not find JSON in LLM response")
                return {}
                
            json_str = response[json_start:json_end+1]
            return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from LLM response: {str(e)}")
            logger.debug(f"Raw response: {response}")
            return {}


class MisunderstandingDetector:
    """
    Detects potential misunderstandings between sequential agent outputs.
    
    This class analyzes the outputs of two sequential agents to identify potential
    misunderstandings, ambiguities, or inconsistencies that might affect system operation.
    It leverages the ReflectiveAgent pattern to provide standardized self-reflection and
    revision capabilities through the WaterAgentReflective class.
    
    The self-reflection process improves detection accuracy by:
    
    1. Reflecting on the initial misunderstanding detection output
    2. Identifying potential false positives and false negatives
    3. Assessing the severity classifications and question quality
    4. Revising the detection results based on reflection insights
    
    This self-reflection loop helps ensure that misunderstandings are accurately detected
    and appropriately classified, which is crucial for effective agent coordination.
    """
    
    def __init__(self, agent_interface=None):
        """
        Initialize the MisunderstandingDetector.
        
        Args:
            agent_interface: Agent interface for making LLM API calls. If None, WaterAgentCoordinator will handle it.
        """
        self.agent_interface = agent_interface
        self._reflective_agent = None
        self._initialize_reflective_agent_async = None
        
    async def ensure_reflective_agent_initialized(self):
        """Ensure the reflective agent is initialized."""
        if self._reflective_agent is not None:
            return
            
        # If initialization is already in progress, wait for it
        if self._initialize_reflective_agent_async is not None:
            await self._initialize_reflective_agent_async
            return
            
        # Start the initialization
        try:
            self._initialize_reflective_agent_async = asyncio.create_task(self._initialize_reflective_agent())
            await self._initialize_reflective_agent_async
        finally:
            self._initialize_reflective_agent_async = None
            
    async def _initialize_reflective_agent(self):
        """Initialize the reflective agent with necessary dependencies."""
        if self.agent_interface is None:
            logger.warning("Cannot initialize reflective agent without an agent interface")
            return
            
        try:
            # Extract required resources from agent_interface
            event_queue = self.agent_interface._event_queue
            state_manager = self.agent_interface._state_manager
            context_manager = self.agent_interface._context_manager
            cache_manager = self.agent_interface._cache_manager
            metrics_manager = self.agent_interface._metrics_manager
            error_handler = self.agent_interface._error_handler
            memory_monitor = self.agent_interface._memory_monitor
            health_tracker = None  # Optional, can be None
            
            # Create the reflective agent
            self._reflective_agent = WaterAgentReflective(
                agent_id="water_misunderstanding_detector",
                event_queue=event_queue,
                state_manager=state_manager,
                context_manager=context_manager,
                cache_manager=cache_manager,
                metrics_manager=metrics_manager,
                error_handler=error_handler,
                memory_monitor=memory_monitor,
                health_tracker=health_tracker,
                max_reflection_cycles=2
            )
            
            logger.info("Reflective agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize reflective agent: {str(e)}")
            self._reflective_agent = None
    
    async def detect_misunderstandings(
        self, 
        first_agent_output: str,
        second_agent_output: str,
        use_reflection: bool = True
    ) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
        """
        Detect misunderstandings between the outputs of two sequential agents.
        
        Args:
            first_agent_output: Output from the first agent
            second_agent_output: Output from the second agent
            use_reflection: Whether to use reflection and revision to improve the detection output
            
        Returns:
            Tuple containing:
            - List of detected misunderstandings with metadata
            - List of questions for the first agent
            - List of questions for the second agent
        """
        try:
            # Use reflective agent if available and reflection is enabled
            if use_reflection and self.agent_interface is not None:
                try:
                    # Ensure reflective agent is initialized
                    await self.ensure_reflective_agent_initialized()
                    
                    if self._reflective_agent is not None:
                        # Use reflective agent for detection with self-reflection
                        logger.info("Using reflective agent for misunderstanding detection")
                        detection_result = await self._reflective_agent.detect_misunderstandings(
                            first_agent_output,
                            second_agent_output,
                            use_reflection=True
                        )
                        
                        # Extract the results
                        misunderstandings = detection_result.get("misunderstandings", [])
                        first_agent_questions = [
                            q["question"] for q in detection_result.get("first_agent_questions", [])
                        ]
                        second_agent_questions = [
                            q["question"] for q in detection_result.get("second_agent_questions", [])
                        ]
                        
                        logger.info(f"Reflective agent detected {len(misunderstandings)} potential misunderstandings")
                        return misunderstandings, first_agent_questions, second_agent_questions
                except Exception as reflective_e:
                    logger.warning(f"Error using reflective agent, falling back to direct approach: {str(reflective_e)}")
                    # Fall through to direct approach if reflective agent fails
            
            # Direct approach without reflective agent
            # Prepare prompt with agent outputs
            formatted_prompt = MISUNDERSTANDING_DETECTION_PROMPT.format(
                first_agent_output=first_agent_output,
                second_agent_output=second_agent_output
            )
            
            # Make LLM API call - either through our own interface or via parent coordinator
            if self.agent_interface is not None:
                # Use agent interface directly
                detection_response = await self.agent_interface.process_with_validation(
                    conversation=formatted_prompt,
                    system_prompt_info=("FFTT_system_prompts/core_agents/water_agent", "misunderstanding_detection_prompt"),
                    current_phase="misunderstanding_detection",
                    operation_id=f"misunderstand_detect_{uuid.uuid4()}"
                )
                
                # Extract response content if needed
                if isinstance(detection_response, dict):
                    if "content" in detection_response:
                        detection_response = detection_response["content"]
                    elif "response" in detection_response:
                        detection_response = detection_response["response"]
            else:
                # Parent coordinator will handle the call with a placeholder
                # This should be replaced with a proper call to the parent's _call_llm method
                detection_response = json.dumps({
                    "misunderstandings": [],
                    "first_agent_questions": [],
                    "second_agent_questions": []
                })
            
            # Parse the response
            parsed_response = self._parse_json_response(detection_response)
            
            # Extract the misunderstandings and questions
            misunderstandings = parsed_response.get("misunderstandings", [])
            first_agent_questions = [
                q["question"] for q in parsed_response.get("first_agent_questions", [])
            ]
            second_agent_questions = [
                q["question"] for q in parsed_response.get("second_agent_questions", [])
            ]
            
            logger.info(f"Detected {len(misunderstandings)} potential misunderstandings")
            
            return misunderstandings, first_agent_questions, second_agent_questions
            
        except Exception as e:
            logger.error(f"Error detecting misunderstandings: {str(e)}")
            raise MisunderstandingDetectionError(f"Failed to detect misunderstandings: {str(e)}")
    
    # _call_llm method removed as it's handled by agent_interface or parent coordinator
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse a JSON response from the LLM.
        
        Args:
            response: The LLM's response as a string
            
        Returns:
            The parsed JSON as a dictionary
        """
        try:
            # Extract JSON from the response
            # This handles cases where the LLM might include explanation text before/after the JSON
            json_start = response.find('{')
            json_end = response.rfind('}')
            
            if json_start == -1 or json_end == -1:
                logger.warning("Could not find JSON in LLM response")
                return {
                    "misunderstandings": [],
                    "first_agent_questions": [],
                    "second_agent_questions": []
                }
                
            json_str = response[json_start:json_end+1]
            return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from LLM response: {str(e)}")
            logger.debug(f"Raw response: {response}")
            return {
                "misunderstandings": [],
                "first_agent_questions": [],
                "second_agent_questions": []
            }


class QuestionResponseHandler:
    """
    Handles the question generation and response collection during coordination.
    
    This class is responsible for delivering questions to agents and collecting
    their responses during the coordination process.
    """
    
    def __init__(self):
        """Initialize the QuestionResponseHandler."""
        self.response_cache = {}
    
    async def get_agent_responses(
        self,
        agent: Any,
        questions: List[str]
    ) -> List[str]:
        """
        Get responses from an agent for a list of questions.
        
        Args:
            agent: The agent to question
            questions: List of questions to ask
            
        Returns:
            List of responses from the agent
        """
        if not questions:
            return []
        
        responses = []
        
        # Generate a unique identifier for the agent
        agent_id = self._get_agent_identifier(agent)
        
        # Process each question
        for question in questions:
            # Check if we already have a response for this question from this agent
            cache_key = f"{agent_id}:{question}"
            if cache_key in self.response_cache:
                logger.debug(f"Using cached response for question: {question[:50]}...")
                responses.append(self.response_cache[cache_key])
                continue
            
            # Get the response from the agent
            try:
                response = await self._ask_agent(agent, question)
                self.response_cache[cache_key] = response
                responses.append(response)
            except Exception as e:
                logger.error(f"Error getting response from agent: {str(e)}")
                responses.append(f"ERROR: Failed to get response: {str(e)}")
        
        return responses
    
    def _get_agent_identifier(self, agent: Any) -> str:
        """
        Generate a unique identifier for an agent.
        
        Args:
            agent: The agent to identify
            
        Returns:
            A string identifier for the agent
        """
        # In a real implementation, this would use a more robust method to identify agents
        return f"{agent.__class__.__name__}:{id(agent)}"
    
    async def _ask_agent(self, agent: Any, question: str) -> str:
        """
        Ask a question to an agent and get its response.
        
        Args:
            agent: The agent to question
            question: The question to ask
            
        Returns:
            The agent's response as a string
        """
        # Check if the agent has a clarify method
        if hasattr(agent, 'clarify') and callable(getattr(agent, 'clarify')):
            return await agent.clarify(question)
        
        # Fallback: If agent doesn't have a clarify method, check for ask_question
        if hasattr(agent, 'ask_question') and callable(getattr(agent, 'ask_question')):
            return await agent.ask_question(question)
        
        # Fallback: If agent doesn't have either method, use a generic approach
        # This would be replaced with actual implementation in a real system
        logger.warning(f"Agent {agent.__class__.__name__} doesn't have clarify or ask_question methods")
        return f"Agent does not support answering clarification questions: {question}"


class AmbiguityResolutionTracker:
    """
    Tracks the resolution status of identified ambiguities during coordination.
    
    This class maintains state about which misunderstandings have been resolved
    and which still require attention. It can leverage a reflective agent for
    enhanced resolution assessment when available.
    """
    
    def __init__(self, agent_interface=None):
        """
        Initialize the resolution tracker.
        
        Args:
            agent_interface: Agent interface for making LLM API calls. If None, will use parent coordinator.
        """
        self.resolved_issues: Set[str] = set()
        self.unresolved_issues: Dict[str, Dict[str, Any]] = {}
        self.agent_interface = agent_interface
        self.iteration = 0
        self._reflective_agent = None
        self._initialize_reflective_agent_async = None
        
    async def ensure_reflective_agent_initialized(self):
        """Ensure the reflective agent is initialized."""
        if self._reflective_agent is not None:
            return
            
        # If initialization is already in progress, wait for it
        if self._initialize_reflective_agent_async is not None:
            await self._initialize_reflective_agent_async
            return
            
        # Start the initialization
        try:
            self._initialize_reflective_agent_async = asyncio.create_task(self._initialize_reflective_agent())
            await self._initialize_reflective_agent_async
        finally:
            self._initialize_reflective_agent_async = None
            
    async def _initialize_reflective_agent(self):
        """Initialize the reflective agent with necessary dependencies."""
        if self.agent_interface is None:
            logger.warning("Cannot initialize reflective agent without an agent interface")
            return
            
        try:
            # Extract required resources from agent_interface
            event_queue = self.agent_interface._event_queue
            state_manager = self.agent_interface._state_manager
            context_manager = self.agent_interface._context_manager
            cache_manager = self.agent_interface._cache_manager
            metrics_manager = self.agent_interface._metrics_manager
            error_handler = self.agent_interface._error_handler
            memory_monitor = self.agent_interface._memory_monitor
            health_tracker = None  # Optional, can be None
            
            # Create the reflective agent
            self._reflective_agent = WaterAgentReflective(
                agent_id="water_resolution_tracker",
                event_queue=event_queue,
                state_manager=state_manager,
                context_manager=context_manager,
                cache_manager=cache_manager,
                metrics_manager=metrics_manager,
                error_handler=error_handler,
                memory_monitor=memory_monitor,
                health_tracker=health_tracker,
                max_reflection_cycles=1  # Less reflection needed for resolution assessment
            )
            
            logger.info("Resolution tracker reflective agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize reflective agent for resolution tracker: {str(e)}")
            self._reflective_agent = None
        
    def initialize_tracking(self, misunderstandings: List[Dict[str, Any]]) -> None:
        """
        Initialize tracking for a list of misunderstandings.
        
        Args:
            misunderstandings: List of misunderstandings to track
        """
        self.resolved_issues = set()
        self.unresolved_issues = {
            m.get("id", f"issue_{i}"): m 
            for i, m in enumerate(misunderstandings)
        }
        self.iteration = 0
        logger.info(f"Initialized tracking for {len(misunderstandings)} misunderstandings")
    
    def all_resolved(self) -> bool:
        """
        Check if all identified issues have been resolved.
        
        Returns:
            True if all issues are resolved, False otherwise
        """
        # Check if there are any unresolved issues
        if len(self.unresolved_issues) == 0:
            return True
            
        # Check if there are only LOW severity issues remaining
        for issue_id, issue in self.unresolved_issues.items():
            severity = issue.get("severity", "MEDIUM")
            if severity in ["CRITICAL", "HIGH", "MEDIUM"]:
                return False
                
        # If we only have LOW severity issues, consider them resolved
        logger.info("Only LOW severity issues remain, considering all resolved")
        return True
        
    async def assess_resolution(
        self,
        misunderstandings: List[Dict[str, Any]],
        first_agent_questions: List[str],
        first_agent_responses: List[str],
        second_agent_questions: List[str],
        second_agent_responses: List[str]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str], List[str]]:
        """
        Assess which misunderstandings have been resolved based on agent responses.
        
        Args:
            misunderstandings: Original list of misunderstandings
            first_agent_questions: Questions asked to the first agent
            first_agent_responses: Responses from the first agent
            second_agent_questions: Questions asked to the second agent
            second_agent_responses: Responses from the second agent
            
        Returns:
            Tuple containing:
            - List of resolved issues
            - List of unresolved issues
            - New questions for the first agent
            - New questions for the second agent
        """
        # Check if we have any questions and responses
        if not first_agent_questions and not second_agent_questions:
            logger.warning("No questions were asked to either agent, can't assess resolution")
            return [], list(self.unresolved_issues.values()), [], []

        # Format the questions and responses for the prompt
        first_agent_qa = []
        for i, (q, a) in enumerate(zip(first_agent_questions, first_agent_responses)):
            first_agent_qa.append(f"Q{i+1}: {q}\nA{i+1}: {a}")
        
        second_agent_qa = []
        for i, (q, a) in enumerate(zip(second_agent_questions, second_agent_responses)):
            second_agent_qa.append(f"Q{i+1}: {q}\nA{i+1}: {a}")

        # Prepare the formatted Q&A for the prompt
        first_agent_qa_str = "\n\n".join(first_agent_qa)
        second_agent_qa_str = "\n\n".join(second_agent_qa)
        
        # Format the misunderstandings for the prompt
        misunderstandings_str = json.dumps(misunderstandings, indent=2)
        
        # Calculate the current iteration number based on the state
        self.iteration += 1
            
        # Prepare prompt with the formatted inputs
        formatted_prompt = RESOLUTION_ASSESSMENT_PROMPT.format(
            misunderstandings=misunderstandings_str,
            first_agent_questions_and_responses=first_agent_qa_str,
            second_agent_questions_and_responses=second_agent_qa_str,
            current_iteration=self.iteration
        )
        
        try:
            # Make LLM API call using agent interface if available
            if self.agent_interface is not None:
                # Use agent interface directly
                assessment_response = await self.agent_interface.process_with_validation(
                    conversation=formatted_prompt,
                    system_prompt_info=("FFTT_system_prompts/core_agents/water_agent", "resolution_assessment_prompt"),
                    current_phase="resolution_assessment",
                    operation_id=f"resolution_assess_{uuid.uuid4()}"
                )
                
                # Extract response content if needed
                if isinstance(assessment_response, dict):
                    if "content" in assessment_response:
                        assessment_response = assessment_response["content"]
                    elif "response" in assessment_response:
                        assessment_response = assessment_response["response"]
            else:
                # Parent coordinator will handle the call with a placeholder
                # This should be replaced with a proper call to the parent's _call_llm method
                assessment_response = json.dumps({
                    "resolved_misunderstandings": [],
                    "unresolved_misunderstandings": list(self.unresolved_issues.values()),
                    "new_first_agent_questions": [],
                    "new_second_agent_questions": [],
                    "require_further_iteration": False
                })
            
            # Parse the response
            parsed_response = self._parse_json_response(assessment_response)
            
            # Extract the assessment results
            resolved_misunderstandings = parsed_response.get("resolved_misunderstandings", [])
            unresolved_misunderstandings = parsed_response.get("unresolved_misunderstandings", [])
            new_first_agent_questions = [
                q["question"] for q in parsed_response.get("new_first_agent_questions", [])
            ]
            new_second_agent_questions = [
                q["question"] for q in parsed_response.get("new_second_agent_questions", [])
            ]
            require_further_iteration = parsed_response.get("require_further_iteration", False)
            
            # Update internal tracking state
            for resolved in resolved_misunderstandings:
                issue_id = resolved.get("id")
                if issue_id and issue_id in self.unresolved_issues:
                    self.resolved_issues.add(issue_id)
                    del self.unresolved_issues[issue_id]
            
            # Update any severity changes to remaining unresolved issues
            for unresolved in unresolved_misunderstandings:
                issue_id = unresolved.get("id")
                if issue_id and issue_id in self.unresolved_issues:
                    # Update the severity if it has changed
                    if "severity" in unresolved:
                        self.unresolved_issues[issue_id]["severity"] = unresolved["severity"]
            
            # Log resolution progress
            logger.info(f"Resolution assessment complete. Resolved: {len(resolved_misunderstandings)}, " +
                       f"Unresolved: {len(unresolved_misunderstandings)}, " +
                       f"Needs more iterations: {require_further_iteration}")
            
            return (
                resolved_misunderstandings, 
                unresolved_misunderstandings, 
                new_first_agent_questions, 
                new_second_agent_questions
            )
            
        except Exception as e:
            logger.error(f"Error assessing resolution: {str(e)}")
            
            # In case of error, return conservative result (nothing resolved)
            return [], list(self.unresolved_issues.values()), [], []
    
    # _call_llm method removed as it's handled by agent_interface or parent coordinator
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse a JSON response from the LLM.
        
        Args:
            response: The LLM's response as a string
            
        Returns:
            The parsed JSON as a dictionary
        """
        try:
            # Extract JSON from the response
            json_start = response.find('{')
            json_end = response.rfind('}')
            
            if json_start == -1 or json_end == -1:
                logger.warning("Could not find JSON in LLM response")
                return {
                    "resolved_misunderstandings": [],
                    "unresolved_misunderstandings": list(self.unresolved_issues.values()),
                    "new_first_agent_questions": [],
                    "new_second_agent_questions": [],
                    "require_further_iteration": False
                }
                
            json_str = response[json_start:json_end+1]
            return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from LLM response: {str(e)}")
            logger.debug(f"Raw response: {response}")
            
            # Return a safe fallback
            return {
                "resolved_misunderstandings": [],
                "unresolved_misunderstandings": list(self.unresolved_issues.values()),
                "new_first_agent_questions": [],
                "new_second_agent_questions": [],
                "require_further_iteration": False
            }