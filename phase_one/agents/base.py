"""
Base reflective agent with proper resource management.
"""
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

from resources import (
    ResourceType, ResourceEventTypes, EventQueue, StateManager, 
    AgentContextManager, CacheManager, MetricsManager, ErrorHandler
)
from resources.monitoring import (
    MemoryThresholds, MemoryMonitor, HealthStatus, HealthTracker
)
from interfaces import AgentInterface, AgentState

from phase_one.models.enums import DevelopmentState
from phase_one.models.refinement import RefinementContext, AgentPromptConfig
# Circuit breaker definitions no longer needed - protection at API level
from phase_one.coordination import get_agent_coordinator, AgentPriority

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReflectiveAgent(AgentInterface):
    """Enhanced base class for reflective agents with proper resource management."""
    
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
        prompt_config: AgentPromptConfig,
        health_tracker: HealthTracker = None
    ):
        super().__init__(agent_id, event_queue, state_manager, context_manager, cache_manager, metrics_manager, error_handler, memory_monitor)
        self._development_state = DevelopmentState.INITIALIZING
        self._prompt_config = prompt_config
        
        # Monitoring integrations
        self._health_tracker = health_tracker
        self._memory_monitor = memory_monitor
        
        # Agent coordination
        self._agent_coordinator = get_agent_coordinator()
        self._priority_level = self._calculate_priority_level()
        
        # Circuit breakers removed - LLM protection now handled at API level
        # Individual agents don't need their own circuit breakers since they just do internal processing
        # The actual LLM calls are protected by the centralized circuit breaker in AnthropicAPI
        
        # Mapping between development states and agent states
        self._state_mapping = {
            DevelopmentState.INITIALIZING: AgentState.READY,
            DevelopmentState.ANALYZING: AgentState.PROCESSING,
            DevelopmentState.DESIGNING: AgentState.PROCESSING,
            DevelopmentState.VALIDATING: AgentState.VALIDATING,
            DevelopmentState.REFINING: AgentState.PROCESSING,
            DevelopmentState.ERROR: AgentState.ERROR,
            DevelopmentState.COMPLETE: AgentState.COMPLETE
        }

        # Track background tasks for proper cleanup
        self._background_tasks = set()
        
        # Initial health report (deferred to async initialization)
        task = asyncio.create_task(self._ensure_initialized_and_report_health())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
    
    async def _ensure_initialized_and_report_health(self):
        """Ensure initialization and report health"""
        await self.ensure_initialized()
        await self._report_agent_health()
    
    def _calculate_priority_level(self) -> AgentPriority:
        """Calculate the priority level for this agent based on its type and role."""
        agent_type = self.__class__.__name__.lower()
        
        # Earth Agent and Garden Planner get high priority due to their coordination complexity
        if 'earth' in agent_type or 'garden' in agent_type:
            return AgentPriority.HIGH
        # Validation agents get normal priority
        elif 'validation' in agent_type or 'validator' in agent_type:
            return AgentPriority.NORMAL
        # Other agents get low priority
        else:
            return AgentPriority.LOW
    
    def _estimate_update_duration(self, new_state: AgentState) -> float:
        """Estimate how long a state update will take based on the state type."""
        # LLM-intensive operations take longer
        llm_states = {AgentState.PROCESSING, AgentState.VALIDATING}
        
        if new_state in llm_states:
            return 45.0  # 45 seconds for LLM operations
        elif new_state == AgentState.COORDINATING:
            return 30.0  # 30 seconds for coordination
        else:
            return 10.0  # 10 seconds for simple state changes
    
    async def set_agent_state(self, new_state: AgentState, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Coordinated agent state update to prevent resource contention.
        
        Args:
            new_state: New state to set
            metadata: Additional metadata
        """
        # Skip coordination if we're already in the target state
        if hasattr(self, 'agent_state') and self.agent_state == new_state:
            logger.debug(f"Agent {self.agent_id} already in state {new_state.name}, skipping update")
            return
            
        # Use coordination for state updates to prevent contention
        estimated_duration = self._estimate_update_duration(new_state)
        operation_type = f"state_update_{new_state.name}"
        
        try:
            async with self._agent_coordinator.request_update_slot(
                self.agent_id,
                self._priority_level,
                estimated_duration,
                operation_type
            ):
                # Call the parent implementation within the coordination context
                await super().set_agent_state(new_state, metadata)
        except Exception as e:
            logger.error(f"Coordination failed for agent {self.agent_id} state transition to {new_state.name}: {str(e)}")
            # Fall back to direct state update if coordination fails
            try:
                await super().set_agent_state(new_state, metadata)
                logger.info(f"Fallback state update successful for agent {self.agent_id} to {new_state.name}")
            except Exception as fallback_error:
                logger.error(f"Both coordinated and fallback state updates failed for agent {self.agent_id}: {str(fallback_error)}")
                # Still update the internal state to prevent getting stuck
                if hasattr(self, 'agent_state'):
                    self.agent_state = new_state
                raise

    # Circuit breaker methods removed - protection now at API level
    
    # Compatibility method for step-by-step interface
    
    async def process(self, input_data: Any) -> Dict[str, Any]:
        """
        Compatibility method for step-by-step interface.
        
        This method provides a simplified interface that wraps the more complex
        process_with_validation method with sensible defaults.
        
        Args:
            input_data: Input data for processing (string or dict)
            
        Returns:
            Processing result dictionary
        """
        await self.ensure_initialized()
        
        # Convert input to conversation string
        if isinstance(input_data, str):
            conversation = input_data
        elif isinstance(input_data, dict):
            conversation = json.dumps(input_data, indent=2)
        else:
            conversation = str(input_data)
        
        # Use the configured prompt paths
        prompt_path = self._prompt_config.system_prompt_base_path
        prompt_name = self._prompt_config.initial_prompt_name
        
        # Set processing state
        self.development_state = DevelopmentState.ANALYZING
        
        try:
            # Direct processing - circuit breaker protection now at API level
            result = await self.process_with_validation(
                conversation=conversation,
                system_prompt_info=(prompt_path, prompt_name),
                timeout=180  # 3 minute timeout for LLM calls
            )
            
            # Mark as complete if successful
            if result.get("status") == "success":
                self.development_state = DevelopmentState.COMPLETE
            else:
                self.development_state = DevelopmentState.ERROR
            
            return result
            
        except Exception as e:
            self.development_state = DevelopmentState.ERROR
            error_msg = f"Processing failed for agent {self.interface_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return {
                "status": "error", 
                "error": error_msg,
                "agent_id": self.interface_id,
                "timestamp": datetime.now().isoformat()
            }
    
    # Health reporting methods
    
    async def _report_agent_health(self, custom_status: str = None, description: str = None, metadata: Dict[str, Any] = None):
        """Report agent health status to health tracker."""
        if not self._health_tracker:
            return
            
        # Map development state to health status if not provided
        state_health_mapping = {
            DevelopmentState.INITIALIZING: "HEALTHY",
            DevelopmentState.ANALYZING: "HEALTHY",
            DevelopmentState.DESIGNING: "HEALTHY",
            DevelopmentState.VALIDATING: "HEALTHY",
            DevelopmentState.REFINING: "DEGRADED",
            DevelopmentState.ERROR: "CRITICAL",
            DevelopmentState.COMPLETE: "HEALTHY"
        }
        
        status = custom_status or state_health_mapping.get(self._development_state, "UNKNOWN")
        desc = description or f"Agent {self.interface_id} in state {self._development_state.value}"
        
        # Merge metadata
        meta = {"development_state": self._development_state.value}
        if metadata:
            meta.update(metadata)
        
        # Create health status object
        health_status = HealthStatus(
            status=status,
            source=f"agent_{self.interface_id}",
            description=desc,
            metadata=meta
        )
        
        # Update health tracker asynchronously - now correctly awaited
        await self._health_tracker.update_health(
            f"agent_{self.interface_id}", 
            health_status
        )
    
    # Memory tracking methods
    
    async def track_string_memory(self, resource_id: str, string_value: str) -> None:
        """Track memory usage of a string resource."""
        if self._memory_monitor:
            size_mb = len(string_value) / (1024 * 1024)  # Rough estimation
            await self.track_memory_usage(resource_id, size_mb)
    
    async def track_dict_memory(self, resource_id: str, dict_value: Dict[str, Any]) -> None:
        """Track memory usage of a dictionary resource."""
        if self._memory_monitor:
            size_mb = len(json.dumps(dict_value)) / (1024 * 1024)  # Rough estimation
            await self.track_memory_usage(resource_id, size_mb)
    
    # Reflection and validation methods
    
    async def standard_reflect(
        self, 
        output: Dict[str, Any],
        circuit_name: str = None,  # Ignored - kept for compatibility
        prompt_path: str = None,
        prompt_name: str = None
    ) -> Dict[str, Any]:
        """Standardized reflection with monitoring."""
        # Ensure initialization
        await self.ensure_initialized()
        
        # Set state and report health
        self.development_state = DevelopmentState.VALIDATING
        
        # Track memory usage of the output
        await self.track_dict_memory("reflection_input", output)
        
        # Use configured paths or overrides
        _prompt_path = prompt_path or self._prompt_config.system_prompt_base_path
        _prompt_name = prompt_name or self._prompt_config.reflection_prompt_name
        
        try:
            # Direct reflection - circuit breaker protection now at API level
            return await self.process_with_validation(
                conversation=f"Reflect on output with a critical eye for fundamental errors and / or faulty assumptions: {output}",
                system_prompt_info=(_prompt_path, _prompt_name)
            )
        except Exception as e:
            logger.error(f"Reflection failed for {self.interface_id}: {str(e)}")
            
            # Report critical health status with error
            try:
                await self._report_agent_health(
                    custom_status="CRITICAL",
                    description=f"Reflection failed: {str(e)}",
                    metadata={
                        "state": "VALIDATING",
                        "error": str(e)
                    }
                )
            except Exception as health_error:
                logger.error(f"Failed to report health status: {str(health_error)}")
            
            # Return a minimal failure structure that won't break downstream processing
            return {
                "error": f"Reflection error: {str(e)}",
                "status": "failure",
                "agent_id": self.interface_id,
                "timestamp": datetime.now().isoformat(),
                "reflection_results": {
                    "validation_status": {
                        "passed": False
                    },
                    "error": str(e)
                }
            }
    
    async def standard_refine(
        self, 
        output: Dict[str, Any], 
        refinement_guidance: Dict[str, Any],
        circuit_name: str = None,  # Ignored - kept for compatibility
        prompt_path: str = None,
        prompt_name: str = None
    ) -> Dict[str, Any]:
        """Standardized refinement with monitoring."""
        # Ensure initialization
        await self.ensure_initialized()

        # Set state and report health
        self.development_state = DevelopmentState.REFINING
        
        # Track memory usage
        combined_size_mb = (len(json.dumps(output)) + len(json.dumps(refinement_guidance))) / (1024 * 1024)
        await self.track_memory_usage("refinement_data", combined_size_mb)
        
        # Use configured paths or overrides
        _prompt_path = prompt_path or self._prompt_config.system_prompt_base_path
        _prompt_name = prompt_name or self._prompt_config.refinement_prompt_name
        
        try:
            # Direct refinement - circuit breaker protection now at API level
            refinement_result = await self.process_with_validation(
                conversation=f"""Refine output based on:
                Original output: {output}
                Refinement guidance: {refinement_guidance}""",
                system_prompt_info=(_prompt_path, _prompt_name)
            )
            
            # Update health status based on refinement result
            if self._health_tracker:
                status = "HEALTHY" if refinement_result.get("status") == "success" else "DEGRADED"
                await self._report_agent_health(
                    custom_status=status,
                    description="Refinement completed",
                    metadata={
                        "state": "COMPLETE" if status == "HEALTHY" else "REFINING",
                        "refinement_status": refinement_result.get("status", "unknown")
                    }
                )
            
            return refinement_result
            
        except Exception as e:
            logger.error(f"Refinement failed for {self.interface_id}: {str(e)}")
            
            # Report critical health status
            await self._report_agent_health(
                custom_status="CRITICAL", 
                description=f"Refinement failed: {str(e)}",
                metadata={
                    "state": "REFINING",
                    "error": str(e)
                }
            )
            
            return {
                "error": f"Refinement failed: {str(e)}",
                "status": "failure",
                "agent_id": self.interface_id,
                "timestamp": datetime.now().isoformat()
            }
    
    async def track_memory_usage(self, resource_id: str, size_mb: float) -> None:
        """Track memory usage of agent resources."""
        if self._memory_monitor:
            await self._memory_monitor.track_resource(
                f"agent:{self.interface_id}:{resource_id}",
                size_mb,
                f"agent_{self.interface_id}"
            )
            
    async def add_refinement_iteration(
        self,
        context: RefinementContext
    ) -> None:
        """Record refinement iteration with proper persistence."""
        # Store in state manager
        await self._state_manager.set_state(
            f"agent:{self.interface_id}:refinement:{context.iteration}",
            context.to_dict(),
            ResourceType.STATE
        )
        
        # Update refinement history in context
        agent_context = await self._context_manager.get_context(
            f"agent_context:{self.interface_id}"
        )
        if agent_context:
            refinement_history = agent_context.refinement_history or []
            refinement_history.append(context.to_dict())
            await self._context_manager.store_context(
                f"agent_context:{self.interface_id}",
                agent_context
            )
            
    async def get_refinement_history(self) -> List[Dict[str, Any]]:
        """Get refinement history from context manager."""
        agent_context = await self._context_manager.get_context(
            f"agent_context:{self.interface_id}"
        )
        if agent_context:
            return agent_context.refinement_history or []
        return []
        
    @property
    def development_state(self) -> DevelopmentState:
        """Get the current development state."""
        return self._development_state
    
    @development_state.setter
    def development_state(self, state: DevelopmentState) -> None:
        """Set the development state and update agent state."""
        self._development_state = state
        # Update the agent state based on the development state
        self.agent_state = self._state_mapping.get(state, AgentState.READY)
    
    async def cleanup(self) -> None:
        """Clean up background tasks and resources."""
        # Cancel any remaining background tasks
        for task in self._background_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        self._background_tasks.clear()
        
        # Call parent cleanup if available
        if hasattr(super(), 'cleanup'):
            await super().cleanup()