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
    CircuitBreaker, CircuitState, CircuitOpenError, CircuitBreakerConfig, 
    MemoryThresholds, MemoryMonitor, HealthStatus, HealthTracker
)
from interface import AgentInterface, AgentState

from phase_one.models.enums import DevelopmentState
from phase_one.models.refinement import RefinementContext, AgentPromptConfig
from phase_one.monitoring.circuit_breakers import CircuitBreakerDefinition

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
        circuit_breakers: List[CircuitBreakerDefinition] = None,
        health_tracker: HealthTracker = None
    ):
        super().__init__(agent_id, event_queue, state_manager, context_manager, cache_manager, metrics_manager, error_handler, memory_monitor)
        self._development_state = DevelopmentState.INITIALIZING
        self._prompt_config = prompt_config
        
        # Monitoring integrations
        self._health_tracker = health_tracker
        self._memory_monitor = memory_monitor
        
        # Circuit breaker registry
        self._circuit_breakers = {}
        
        # Always create a processing circuit breaker
        self._create_circuit_breaker("processing")
        
        # Create additional circuit breakers if provided
        if circuit_breakers:
            for cb_def in circuit_breakers:
                self._create_circuit_breaker(
                    cb_def.name, 
                    failure_threshold=cb_def.failure_threshold,
                    recovery_timeout=cb_def.recovery_timeout,
                    failure_window=cb_def.failure_window
                )
        
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

        # Initial health report (deferred to async initialization)
        asyncio.create_task(self._ensure_initialized_and_report_health())
    
    async def _ensure_initialized_and_report_health(self):
        """Ensure initialization and report health"""
        await self.ensure_initialized()
        self._report_agent_health()

    def _create_circuit_breaker(
        self, 
        name: str, 
        failure_threshold: int = 3,
        recovery_timeout: int = 30,
        failure_window: int = 120
    ) -> CircuitBreaker:
        """Create and register a circuit breaker."""
        circuit_id = f"{self.interface_id}_{name}"
        
        self._circuit_breakers[name] = CircuitBreaker(
            circuit_id,
            self._event_queue,
            config=CircuitBreakerConfig(
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                failure_window=failure_window
            )
        )
        
        return self._circuit_breakers[name]
    
    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """Get a circuit breaker by name."""
        if name not in self._circuit_breakers:
            # Create default if doesn't exist
            return self._create_circuit_breaker(name)
        return self._circuit_breakers[name]
    
    # Health reporting methods
    
    def _report_agent_health(self, custom_status: str = None, description: str = None, metadata: Dict[str, Any] = None):
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
        
        # Update health tracker asynchronously
        return self._health_tracker.update_health(
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
        circuit_name: str = "processing",
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
            # Use circuit breaker for reflection
            return await self.get_circuit_breaker(circuit_name).execute(
                lambda: self.process_with_validation(
                    conversation=f"Reflect on output with a critical eye for fundamental errors and / or faulty assumptions: {output}",
                    system_prompt_info=(_prompt_path, _prompt_name)
                )
            )
        except CircuitOpenError:
            logger.warning(f"Reflection circuit open for agent {self.interface_id}, reflection rejected")
            
            # Report critical health status
            await self._report_agent_health(
                custom_status="CRITICAL",
                description=f"Reflection rejected due to circuit breaker open",
                metadata={
                    "state": "VALIDATING",
                    "circuit": "open"
                }
            )
            
            return {
                "error": "Reflection rejected due to circuit breaker open",
                "status": "failure",
                "agent_id": self.interface_id,
                "timestamp": datetime.now().isoformat(),
                "reflection_results": {
                    "validation_status": {
                        "passed": False
                    }
                }
            }
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
        circuit_name: str = "processing",
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
            # Use circuit breaker for refinement
            refinement_result = await self.get_circuit_breaker(circuit_name).execute(
                lambda: self.process_with_validation(
                    conversation=f"""Refine output based on:
                    Original output: {output}
                    Refinement guidance: {refinement_guidance}""",
                    system_prompt_info=(_prompt_path, _prompt_name)
                )
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
            
        except CircuitOpenError:
            logger.warning(f"Refinement circuit open for agent {self.interface_id}, refinement rejected")
            
            # Report critical health status
            await self._report_agent_health(
                custom_status="CRITICAL",
                description=f"Refinement rejected due to circuit breaker open",
                metadata={
                    "state": "REFINING",
                    "circuit": "open"
                }
            )
            
            return {
                "error": "Refinement rejected due to circuit breaker open",
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