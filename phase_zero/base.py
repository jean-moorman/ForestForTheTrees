import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

from resources import (
    ResourceType, ResourceEventTypes, EventQueue, StateManager, AgentContextManager, 
    CacheManager, MetricsManager, ErrorHandler, HealthTracker
)
from resources.monitoring import CircuitBreaker, MemoryMonitor, HealthStatus, CircuitOpenError, CircuitBreakerConfig
from interfaces import AgentInterface, AgentState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalysisState(Enum):
    IDLE = "idle"
    ANALYZING = "analyzing"
    ERROR = "error"
    COMPLETE = "complete"

@dataclass
class MetricsSnapshot:
    """System metrics snapshot"""
    error_rate: float
    resource_usage: float
    development_state: str
    component_health: str
    timestamp: datetime = datetime.now()
        
class BaseAnalysisAgent(AgentInterface):
    """Base class for analysis agents with proper resource management."""
    
    def __init__(self, agent_id: str, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        # Ensure memory_monitor is not None for AgentInterface
        if memory_monitor is None:
            memory_monitor = MemoryMonitor(event_queue)
        super().__init__(agent_id, event_queue, state_manager, context_manager, cache_manager, metrics_manager, error_handler, memory_monitor)
        self._analysis_state = AnalysisState.IDLE
        
        # Monitoring components
        self._health_tracker = health_tracker
        self._memory_monitor = memory_monitor
        
        # Circuit breaker registry
        self._circuit_breakers = {}
        
        # Create default processing circuit breaker
        self._create_circuit_breaker("processing")
        
        # Initial health report (deferred to avoid sync/async issues)
        asyncio.create_task(self._report_agent_health())
    
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
            return self._create_circuit_breaker(name)
        return self._circuit_breakers[name]
    
    def _report_agent_health(self, custom_status: str = None, 
                           description: str = None, 
                           metadata: Dict[str, Any] = None):
        """Report agent health status to health tracker."""
        if not self._health_tracker:
            return
            
        # Map analysis state to health status
        state_health_mapping = {
            AnalysisState.IDLE: "HEALTHY",
            AnalysisState.ANALYZING: "HEALTHY",
            AnalysisState.ERROR: "CRITICAL",
            AnalysisState.COMPLETE: "HEALTHY"
        }
        
        status = custom_status or state_health_mapping.get(self._analysis_state, "UNKNOWN")
        desc = description or f"Agent {self.interface_id} in state {self._analysis_state.value}"
        
        # Merge metadata
        meta = {"analysis_state": self._analysis_state.value}
        if metadata:
            meta.update(metadata)
        
        # Create health status object
        health_status = HealthStatus(
            status=status,
            source=f"agent_{self.interface_id}",
            description=desc,
            metadata=meta
        )
        
        # Update health tracker
        return self._health_tracker.update_health(
            f"agent_{self.interface_id}", 
            health_status
        )
    
    async def track_memory_usage(self, resource_id: str, size_mb: float) -> None:
        """Track memory usage of agent resources."""
        if self._memory_monitor:
            await self._memory_monitor.track_resource(
                f"agent:{self.interface_id}:{resource_id}",
                size_mb,
                f"agent_{self.interface_id}"
            )
    
    async def track_dict_memory(self, resource_id: str, dict_value: Dict[str, Any]) -> None:
        """Track memory usage of a dictionary resource."""
        if self._memory_monitor:
            size_mb = len(json.dumps(dict_value)) / (1024 * 1024)  # Rough estimation
            await self.track_memory_usage(resource_id, size_mb)

    @property
    async def analysis_state(self) -> AnalysisState:
        """Get current analysis state with caching."""
        cached_state = await self._cache_manager.get_cache(
            f"agent:{self.interface_id}:analysis_state"
        )
        if cached_state:
            return AnalysisState(cached_state)
        return self._analysis_state
        
    async def set_analysis_state(self, state: AnalysisState) -> None:
        """Set analysis state with proper tracking."""
        if state != self._analysis_state:
            old_state = self._analysis_state
            self._analysis_state = state
            
            # Update state
            await self._state_manager.set_state(
                f"agent:{self.interface_id}:analysis_state",
                {
                    "state": state.name,
                    "previous_state": old_state.name,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Cache state
            await self._cache_manager.set_cache(
                f"agent:{self.interface_id}:analysis_state",
                state.value
            )
            
            # Record metric
            await self._metrics_manager.record_metric(
                f"agent:{self.interface_id}:state_changes",
                1.0,
                metadata={
                    "from_state": old_state.name,
                    "to_state": state.name
                }
            )
            
    async def _process(self, *args, **kwargs) -> Dict[str, Any]:
        """Process analysis with proper resource management."""
        try:
            # Handle both explicit parameters and dictionary input
            if len(args) == 1 and isinstance(args[0], dict) and "garden_planner" in args[0]:
                # Dictionary input case
                inputs = args[0]
                garden_planner_output = inputs.get("garden_planner", {})
                environmental_analysis_output = inputs.get("environmental_analysis", {})
                root_system_output = inputs.get("root_system", {})
                tree_placement_output = inputs.get("tree_placement", {})
            elif len(args) >= 4:
                # Explicit parameters case
                garden_planner_output, environmental_analysis_output, root_system_output, tree_placement_output = args[0:4]
            else:
                # Extract from kwargs if available
                garden_planner_output = kwargs.get("garden_planner_output", {})
                environmental_analysis_output = kwargs.get("environmental_analysis_output", {})
                root_system_output = kwargs.get("root_system_output", {})
                tree_placement_output = kwargs.get("tree_placement_output", {})

            # Track memory usage of inputs
            await self.track_dict_memory("garden_planner_input", garden_planner_output)
            await self.track_dict_memory("environmental_analysis_input", environmental_analysis_output)
            await self.track_dict_memory("root_system_input", root_system_output)
            await self.track_dict_memory("tree_placement_input", tree_placement_output)
            
            # Record start time
            start_time = time.time()
            
            # Update state
            await self.set_analysis_state(AnalysisState.ANALYZING)
            await self._report_agent_health(
                description="Analyzing phase one outputs",
                metadata={"inputs": ["garden_planner", "environmental_analysis", 
                                "root_system", "tree_placement"]}
            )
            
            try:
                # Process with circuit breaker protection
                result = await self.get_circuit_breaker("processing").execute(
                    lambda: self.process_with_validation(
                        conversation=json.dumps({
                            "garden_planner": garden_planner_output,
                            "environmental_analysis": environmental_analysis_output,
                            "root_system": root_system_output,
                            "tree_placement": tree_placement_output
                        }),
                        schema=self.get_output_schema()
                    )
                )
            except CircuitOpenError:
                logger.warning(f"Processing circuit open for agent {self.interface_id}")
                await self.set_analysis_state(AnalysisState.ERROR)
                
                # Report critical health status
                await self._report_agent_health(
                    custom_status="CRITICAL",
                    description=f"Analysis rejected due to circuit breaker open",
                    metadata={"circuit": "open"}
                )
                
                return {
                    "error": "Analysis rejected due to circuit breaker open",
                    "status": "failure",
                    "agent_id": self.interface_id,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Track memory usage of result
            await self.track_dict_memory("analysis_result", result)
            
            # Record performance metric
            processing_time = time.time() - start_time
            await self._metrics_manager.record_metric(
                f"agent:{self.interface_id}:processing_time",
                processing_time,
                metadata={"success": True}
            )
            
            # Update state and report success
            await self.set_analysis_state(AnalysisState.COMPLETE)
            await self._report_agent_health(
                description="Analysis completed successfully",
                metadata={"processing_time": processing_time}
            )
            
            return result
            
        except Exception as e:
            # Update error state
            self._analysis_state = AnalysisState.ERROR
            
            # Report critical health status
            await self._report_agent_health(
                custom_status="CRITICAL",
                description=f"Processing error: {str(e)}",
                metadata={"error": str(e)}
            )
            
            # Record error metric
            await self._metrics_manager.record_metric(
                f"agent:{self.interface_id}:errors",
                1.0,
                metadata={"error": str(e)}
            )
            
            # Emit error event
            await self._event_queue.emit(
                ResourceEventTypes.ERROR_OCCURRED.value,
                {
                    "agent_id": self.interface_id,
                    "error": str(e),
                    "phase": "analysis"
                }
            )
            
            raise
            
    def get_output_schema(self) -> Dict:
        """Get agent-specific output schema."""
        raise NotImplementedError