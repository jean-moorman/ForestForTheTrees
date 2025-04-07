import json
import asyncio
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
from enum import Enum

from resources import ResourceType, ResourceEventTypes, EventQueue, StateManager, AgentContextManager, CacheManager, MetricsManager, SystemMonitor, SystemMonitorConfig, HealthTracker, ErrorHandler
from resources.monitoring import CircuitBreaker, MemoryMonitor, HealthStatus, CircuitOpenError, CircuitBreakerConfig
from interface import AgentInterface, AgentState
from phase_one import PhaseZeroInterface

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
        super().__init__(agent_id, event_queue, state_manager, context_manager, cache_manager, metrics_manager, error_handler)
        self._analysis_state = AnalysisState.IDLE
        
        # Monitoring components
        self._health_tracker = health_tracker
        self._memory_monitor = memory_monitor
        
        # Circuit breaker registry
        self._circuit_breakers = {}
        
        # Create default processing circuit breaker
        self._create_circuit_breaker("processing")
        
        # Initial health report
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

class MonitoringAgent(BaseAnalysisAgent):
    def __init__(self, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__("system_monitoring", event_queue, state_manager, context_manager, cache_manager, metrics_manager, error_handler, health_tracker, memory_monitor)
        self.metrics_schema = {
            "type": "object",
            "required": ["resource", "error", "development"],
            "properties": {
                "resource": {
                    "type": "object",
                    "additionalProperties": {"type": "number"}
                },
                "error": {
                    "type": "object",
                    "additionalProperties": {"type": "number"}
                },
                "development": {
                    "type": "object",
                    "additionalProperties": {"type": "number"}
                }
            }
        }

    async def analyze_metrics(self, metrics: Dict[str, Any], system_state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze metrics with validation."""
        metrics_json = json.dumps(metrics)
        return await self.process_with_validation(
            metrics_json,
            self.metrics_schema,
            current_phase="metric_analysis",
            metadata={"system_state": system_state}
        )

    async def _process(self, metrics_json: str,
                      schema: Dict[str, Any],
                      current_phase: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process validated metrics data."""
        try:
            metrics_data = json.loads(metrics_json)
            analysis = {
                "flag_raised": False,
                "flag_type": None,
                "recommendations": []
            }

            # Analysis logic for resource metrics
            if any(value > 80 for value in metrics_data["resource"].values()):
                analysis.update({
                    "flag_raised": True,
                    "flag_type": "high_resource_usage"
                })

            # Analysis logic for error metrics  
            if any(value > 0.05 for value in metrics_data["error"].values()):
                analysis.update({
                    "flag_raised": True,
                    "flag_type": "high_error_rate"
                })

            return analysis

        except json.JSONDecodeError:
            raise ValueError("Invalid metrics data format")
            
    def get_output_schema(self) -> Dict:
        """Get agent-specific output schema."""
        return self.metrics_schema
    
class SoilAgent(BaseAnalysisAgent):
    def __init__(self, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__("soil", event_queue, state_manager, context_manager, cache_manager, metrics_manager, error_handler, health_tracker, memory_monitor)
        
    def get_output_schema(self) -> Dict:
        return {
            "critical_requirement_gaps": {
                "runtime_gaps": List[Dict],
                "deployment_gaps": List[Dict],
                "dependency_gaps": List[Dict],
                "integration_gaps": List[Dict]
            }
        }

class MicrobialAgent(BaseAnalysisAgent):
    def __init__(self, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__("microbial", event_queue, state_manager, context_manager, cache_manager, metrics_manager, error_handler, health_tracker, memory_monitor)
        
    def get_output_schema(self) -> Dict:
        return {
            "critical_guideline_conflicts": {
                "task_assumption_conflicts": List[Dict],
                "data_pattern_conflicts": List[Dict],
                "component_structure_conflicts": List[Dict],
                "technical_decision_conflicts": List[Dict]
            }
        }

class RootSystemAgent(BaseAnalysisAgent):
    def __init__(self, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__("root_system", event_queue, state_manager, context_manager, cache_manager, metrics_manager, error_handler, health_tracker, memory_monitor)
        
    def get_output_schema(self) -> Dict:
        return {
            "critical_data_flow_gaps": {
                "entity_gaps": List[Dict],
                "flow_pattern_gaps": List[Dict],
                "persistence_gaps": List[Dict],
                "contract_gaps": List[Dict]
            }
        }

class MycelialAgent(BaseAnalysisAgent):
    def __init__(self, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__("mycelial", event_queue, state_manager, context_manager, cache_manager, metrics_manager, error_handler, health_tracker, memory_monitor)
        
    def get_output_schema(self) -> Dict:
        return {
            "critical_guideline_conflicts": {
                "task_scope_conflicts": List[Dict],
                "environment_conflicts": List[Dict],
                "component_conflicts": List[Dict],
                "constraint_conflicts": List[Dict]
            }
        }

class InsectAgent(BaseAnalysisAgent):
    def __init__(self, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__("insect", event_queue, state_manager, context_manager, cache_manager, metrics_manager, error_handler, health_tracker, memory_monitor)
        
    def get_output_schema(self) -> Dict:
        return {
            "critical_structure_gaps": {
                "boundary_gaps": List[Dict],
                "sequence_gaps": List[Dict],
                "interface_gaps": List[Dict],
                "dependency_gaps": List[Dict]
            }
        }

class BirdAgent(BaseAnalysisAgent):
    def __init__(self, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__("bird", event_queue, state_manager, context_manager, cache_manager, metrics_manager, error_handler, health_tracker, memory_monitor)
        
    def get_output_schema(self) -> Dict:
        return {
            "critical_guideline_conflicts": {
                "scope_boundary_conflicts": List[Dict],
                "data_sequence_conflicts": List[Dict],
                "environment_requirement_conflicts": List[Dict],
                "dependency_chain_conflicts": List[Dict]
            }
        }

class PollinatorAgent(BaseAnalysisAgent):
    def __init__(self, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__("pollinator", event_queue, state_manager, context_manager, cache_manager, metrics_manager, error_handler, health_tracker, memory_monitor)
        
    def get_output_schema(self) -> Dict:
        return {
            "component_optimization_opportunities": {
                "redundant_implementations": List[Dict],
                "reuse_opportunities": List[Dict],
                "service_consolidation": List[Dict],
                "abstraction_opportunities": List[Dict]
            }
        }

class EvolutionAgent(AgentInterface):
    """Synthesizes system adaptations based on analysis results"""
    
    def __init__(self, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__("evolution_agent", event_queue, state_manager, context_manager, cache_manager, metrics_manager, error_handler)
        self._health_tracker = health_tracker
        self._memory_monitor = memory_monitor
        
    async def _process(self, conversation: str, schema: Dict, current_phase: Optional[str] = None,
                      metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Process synthesis data with validation"""
        try:
            analysis_inputs = {
                "conversation": conversation,
                "phase": current_phase or "synthesis",
                "metadata": metadata or {}
            }
            
            return await super().process_with_validation(
                json.dumps(analysis_inputs),
                {
                    "strategic_adaptations": {
                        "key_patterns": List[Dict],
                        "adaptations": List[Dict],
                        "priorities": Dict
                    }
                },
                current_phase=current_phase,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Processing error in evolution synthesis: {e}")
            raise

class PhaseZeroOrchestrator(PhaseZeroInterface):
    """Orchestrates phase zero monitoring and analysis with proper resource management."""
    
    def __init__(self, event_queue: EventQueue,
            state_manager: StateManager,
            context_manager: AgentContextManager,
            cache_manager: CacheManager,
            metrics_manager: MetricsManager,
            error_handler: ErrorHandler,
             health_tracker: Optional[HealthTracker] = None,
             memory_monitor: Optional[MemoryMonitor] = None,
             system_monitor: Optional[SystemMonitor] = None):
        # Initialize resource managers
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._context_manager = context_manager
        self._cache_manager = cache_manager
        self._metrics_manager = metrics_manager
        self._error_handler = error_handler
        
        # Monitoring components
        self._health_tracker = health_tracker
        self._memory_monitor = memory_monitor
        self._system_monitor = system_monitor
        
        # Initialize circuit breaker for orchestration
        self._orchestration_circuit = CircuitBreaker(
            "phase_zero_orchestration", 
            event_queue
        )
        
        # Register with system monitor if available
        if self._system_monitor and self._orchestration_circuit:
            asyncio.create_task(
                self._system_monitor.register_circuit_breaker(
                    "phase_zero_orchestration", 
                    self._orchestration_circuit
                )
            )
        
        # Initialize agents with shared event queue
        self._initialize_agents()
        
        # Store initial state
        asyncio.create_task(self._store_initial_state())

        # Report initial health status
        if self._health_tracker:
            asyncio.create_task(
                self._health_tracker.update_health(
                    "phase_zero_orchestrator",
                    HealthStatus(
                        status="HEALTHY",
                        source="phase_zero_orchestrator",
                        description="Phase zero orchestrator initialized",
                        metadata={}
                    )
                )
            )
    
    def _initialize_agents(self) -> None:
        """Initialize all analysis agents with shared event queue and monitoring."""
        self.monitoring_agent = MonitoringAgent(
            self._event_queue,
            self._state_manager,
            self._context_manager,
            self._cache_manager,
            self._metrics_manager,
            self._error_handler,
            health_tracker=self._health_tracker,
            memory_monitor=self._memory_monitor
        )
        
        self.soil_agent = SoilAgent(
            self._event_queue,
            self._state_manager,
            self._context_manager,
            self._cache_manager,
            self._metrics_manager,
            self._error_handler,
            health_tracker=self._health_tracker,
            memory_monitor=self._memory_monitor
        )
        
        self.microbial_agent = MicrobialAgent(
            self._event_queue,
            self._state_manager,
            self._context_manager,
            self._cache_manager,
            self._metrics_manager,
            self._error_handler,
            health_tracker=self._health_tracker,
            memory_monitor=self._memory_monitor
        )

        self.root_system_agent = RootSystemAgent(
            self._event_queue,
            self._state_manager,
            self._context_manager,
            self._cache_manager,
            self._metrics_manager,
            self._error_handler,
            health_tracker=self._health_tracker,
            memory_monitor=self._memory_monitor
        )
        
        self.mycelial_agent = MycelialAgent(
            self._event_queue,
            self._state_manager,
            self._context_manager,
            self._cache_manager,
            self._metrics_manager,
            self._error_handler,
            health_tracker=self._health_tracker,
            memory_monitor=self._memory_monitor
        )
        
        self.insect_agent = InsectAgent(
            self._event_queue,
            self._state_manager,
            self._context_manager,
            self._cache_manager,
            self._metrics_manager,
            self._error_handler,
            health_tracker=self._health_tracker,
            memory_monitor=self._memory_monitor
        )
        
        self.bird_agent = BirdAgent(
            self._event_queue,
            self._state_manager,
            self._context_manager,
            self._cache_manager,
            self._metrics_manager,
            self._error_handler,
            health_tracker=self._health_tracker,
            memory_monitor=self._memory_monitor
        )
        
        self.pollinator_agent = PollinatorAgent(
            self._event_queue,
            self._state_manager,
            self._context_manager,
            self._cache_manager,
            self._metrics_manager,
            self._error_handler,
            health_tracker=self._health_tracker,
            memory_monitor=self._memory_monitor
        )
        
        self.evolution_agent = EvolutionAgent(
            self._event_queue,
            self._state_manager,
            self._context_manager,
            self._cache_manager,
            self._metrics_manager,
            self._error_handler,
            health_tracker=self._health_tracker,
            memory_monitor=self._memory_monitor
        )
        
        # Register agent circuit breakers with system monitor
        if self._system_monitor:
            for agent in [self.monitoring_agent, self.soil_agent, 
                        self.microbial_agent, self.root_system_agent, 
                        self.mycelial_agent, self.insect_agent, 
                        self.bird_agent, self.pollinator_agent, 
                        self.evolution_agent]:
                # Register all circuit breakers for each agent
                for cb_name, cb in agent._circuit_breakers.items():
                    asyncio.create_task(
                        self._system_monitor.register_circuit_breaker(
                            f"{agent.interface_id}_{cb_name}", 
                            cb
                        )
                    )
        
    async def _store_initial_state(self) -> None:
        """Store orchestrator state."""
        await self._state_manager.set_state(
            "phase_zero:orchestrator",
            {
                "status": "initialized",
                "timestamp": datetime.now().isoformat(),
                "agents": [
                    "monitoring", "soil", "microbial", "root_system",
                    "mycelial", "insect", "bird", "pollinator", "evolution"
                ]
            },
            resource_type=ResourceType.STATE
        )

    async def process_system_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Process metrics with proper resource coordination."""
        process_id = f"process_{datetime.now().isoformat()}"
        
        try:
            # Track memory usage for metrics
            if self._memory_monitor:
                metrics_size_mb = len(json.dumps(metrics)) / (1024 * 1024)
                await self._memory_monitor.track_resource(
                    "phase_zero:metrics",
                    metrics_size_mb,
                    "phase_zero_orchestrator"
                )
            
            # Update health status to processing
            if self._health_tracker:
                await self._health_tracker.update_health(
                    "phase_zero_orchestrator",
                    HealthStatus(
                        status="HEALTHY",
                        source="phase_zero_orchestrator",
                        description="Processing system metrics",
                        metadata={"metrics_size": len(json.dumps(metrics))}
                    )
                )
            
            try:
                # Use circuit breaker to protect the entire processing pipeline
                return await self._orchestration_circuit.execute(
                    lambda: self._process_metrics_internal(metrics, process_id)
                )
            except CircuitOpenError:
                logger.error("Phase zero orchestration circuit open, processing rejected")
                
                # Update health status to critical
                if self._health_tracker:
                    await self._health_tracker.update_health(
                        "phase_zero_orchestrator",
                        HealthStatus(
                            status="CRITICAL",
                            source="phase_zero_orchestrator",
                            description="Metrics processing rejected due to circuit breaker open",
                            metadata={"circuit": "phase_zero_orchestration"}
                        )
                    )
                
                return {
                    "status": "error",
                    "error": "Phase zero processing rejected due to circuit breaker open",
                    "phase": "phase_zero_orchestration"
                }
                
        except Exception as e:
            logger.error(f"Phase zero processing failed: {e}")
            
            # Update health status to critical
            if self._health_tracker:
                await self._health_tracker.update_health(
                    "phase_zero_orchestrator",
                    HealthStatus(
                        status="CRITICAL",
                        source="phase_zero_orchestrator",
                        description=f"Processing failed: {str(e)}",
                        metadata={"error": str(e)}
                    )
                )
            
            # Emit error event
            await self._event_queue.emit(
                ResourceEventTypes.ERROR_OCCURRED.value,
                {
                    "process_id": process_id,
                    "error": str(e),
                    "phase": "phase_zero"
                }
            )
            
            return {
                "status": "error",
                "error": str(e),
                "phase": "phase_zero_orchestration"
            }      

    async def _process_metrics_internal(self, metrics: Dict[str, Any], process_id: str) -> Dict[str, Any]:
        """Internal method for processing metrics with monitoring."""
        execution_start_time = datetime.now()
        
        try:
            # Store process start
            await self._state_manager.set_state(
                f"phase_zero:process:{process_id}",
                {
                    "status": "started",
                    "timestamp": datetime.now().isoformat(),
                    "metrics": metrics
                },
                resource_type=ResourceType.MONITOR
            )
            
            # Get phase one outputs with standardized interface
            try:
                phase_one_outputs = await self._data_interface.retrieve_phase_one_outputs()
                logger.info(f"Retrieved Phase One outputs for analysis")
            except ValueError as e:
                logger.error(f"Failed to retrieve Phase One outputs: {e}")
                raise e
            
            # Track memory usage of outputs
            if self._memory_monitor:
                outputs_size_mb = len(json.dumps(phase_one_outputs)) / (1024 * 1024)
                await self._memory_monitor.track_resource(
                    "phase_zero:phase_one_outputs",
                    outputs_size_mb,
                    "phase_zero_orchestrator"
                )
            
            # Update system metrics if monitor available
            if self._system_monitor:
                await self._system_monitor._check_memory_status()
                await self._system_monitor._check_circuit_breakers()
                await self._system_monitor._update_system_health()
            
            # Process all agents with monitoring and timeout protection
            analysis_results = {}
            
            # Run monitoring analysis with circuit breaker protection
            try:
                monitoring_result = await self._execute_agent_with_monitoring(
                    self.monitoring_agent, 
                    metrics, 
                    await self._get_system_state()
                )
            except Exception as e:
                logger.error(f"Monitoring analysis failed: {e}")
                monitoring_result = {
                    "flag_raised": True,
                    "flag_type": "monitoring_error",
                    "error": str(e)
                }
            
            # Run parallel agent analysis
            agents_to_execute = {
                "soil": self.soil_agent,
                "microbial": self.microbial_agent,
                "root_system": self.root_system_agent,
                "mycelial": self.mycelial_agent,
                "insect": self.insect_agent,
                "bird": self.bird_agent,
                "pollinator": self.pollinator_agent
            }
            
            for agent_id, agent in agents_to_execute.items():
                try:
                    analysis_results[agent_id] = await self._execute_agent_with_monitoring(
                        agent, 
                        phase_one_outputs
                    )
                except Exception as e:
                    logger.error(f"Agent {agent_id} analysis failed: {e}")
                    analysis_results[agent_id] = {
                        "error": str(e),
                        "status": "failure",
                        "agent_id": agent_id,
                        "timestamp": datetime.now().isoformat()
                    }
            
            # Run evolution synthesis
            try:
                evolution_result = await self._execute_agent_with_monitoring(
                    self.evolution_agent,
                    {
                        "monitoring": monitoring_result,
                        "analysis": analysis_results,
                        "phase_one": phase_one_outputs
                    }
                )
            except Exception as e:
                logger.error(f"Evolution synthesis failed: {e}")
                evolution_result = {
                    "error": str(e),
                    "status": "failure",
                    "agent_id": "evolution",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Prepare final result
            result = {
                "monitoring_analysis": monitoring_result,
                "deep_analysis": analysis_results,
                "evolution_synthesis": evolution_result,
                "timestamp": datetime.now().isoformat()
            }
            
            # Store result using data interface
            if hasattr(self, '_data_interface') and self._data_interface is not None:
                try:
                    # Get latest phase one version
                    phase_one_version = await self._state_manager.get_state("phase_data:one:latest_version")
                    if phase_one_version:
                        feedback_version = await self._data_interface.store_phase_zero_feedback(
                            result, phase_one_version
                        )
                        logger.info(f"Stored analysis results with version {feedback_version}")
                except Exception as e:
                    logger.error(f"Error storing analysis results via data interface: {e}")

            # Calculate execution time
            execution_time = (datetime.now() - execution_start_time).total_seconds()
            
            # Record execution time metric
            await self._metrics_manager.record_metric(
                "phase_zero:execution_time",
                execution_time,
                metadata={"success": True}
            )
            
            # Store final result
            await self._state_manager.set_state(
                f"phase_zero:process:{process_id}",
                {
                    "status": "completed",
                    "timestamp": datetime.now().isoformat(),
                    "execution_time": execution_time,
                    "result": result
                },
                resource_type=ResourceType.STATE
            )
            
            # Update health status to completed
            if self._health_tracker:
                await self._health_tracker.update_health(
                    "phase_zero_orchestrator",
                    HealthStatus(
                        status="HEALTHY",
                        source="phase_zero_orchestrator",
                        description="Phase zero processing completed successfully",
                        metadata={
                            "execution_time": execution_time,
                            "agent_count": len(agents_to_execute) + 2  # +2 for monitoring and evolution
                        }
                    )
                )
            
            return result
            
        except Exception as e:
            # Record execution time before failure
            execution_time = (datetime.now() - execution_start_time).total_seconds()
            
            # Record execution time metric for failed execution
            await self._metrics_manager.record_metric(
                "phase_zero:execution_time",
                execution_time,
                metadata={"success": False, "error": str(e)}
            )
            
            # Store error state
            await self._state_manager.set_state(
                f"phase_zero:process:{process_id}",
                {
                    "status": "error",
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                    "execution_time": execution_time
                },
                resource_type=ResourceType.STATE
            )
            
            # Re-raise for outer handler
            raise
    
    async def _execute_agent_with_monitoring(self, agent, *args):
        """Execute an agent with monitoring and timeout protection."""
        agent_id = agent.interface_id
        execution_start_time = datetime.now()
        
        # Update health status for agent execution
        if self._health_tracker:
            await self._health_tracker.update_health(
                f"execution_{agent_id}",
                HealthStatus(
                    status="HEALTHY",
                    source="phase_zero_orchestrator",
                    description=f"Starting execution of agent {agent_id}"
                )
            )
        
        try:
            # Execute with timeout - ensure args are passed correctly
            if hasattr(agent, 'process') and callable(agent.process):
                # If agent has a public process method
                result = await self.with_timeout(
                    agent.process(*args),
                    60,  # 60 seconds timeout
                    f"agent_execution_{agent_id}"
                )
            else:
                # Fall back to _process
                result = await self.with_timeout(
                    agent._process(*args),
                    60,
                    f"agent_execution_{agent_id}"
                )
            
            # Record successful execution time
            execution_time = (datetime.now() - execution_start_time).total_seconds()
            await self._metrics_manager.record_metric(
                f"agent:{agent_id}:execution_time",
                execution_time,
                metadata={"success": True}
            )
            
            # Update health status for successful execution
            if self._health_tracker:
                await self._health_tracker.update_health(
                    f"execution_{agent_id}",
                    HealthStatus(
                        status="HEALTHY",
                        source="phase_zero_orchestrator",
                        description=f"Agent {agent_id} executed successfully",
                        metadata={"execution_time": execution_time}
                    )
                )
            
            return result
            
        except asyncio.TimeoutError:
            logger.warning(f"Agent {agent_id} timed out")
            
            # Record timeout metric
            await self._metrics_manager.record_metric(
                f"agent:{agent_id}:timeouts",
                1.0
            )
            
            # Update health status for timeout
            if self._health_tracker:
                await self._health_tracker.update_health(
                    f"execution_{agent_id}",
                    HealthStatus(
                        status="CRITICAL",
                        source="phase_zero_orchestrator",
                        description=f"Agent {agent_id} timed out",
                        metadata={"timeout": 60}
                    )
                )
            
            raise
            
        except Exception as e:
            logger.error(f"Agent {agent_id} error: {str(e)}")
            
            # Record error metric
            await self._metrics_manager.record_metric(
                f"agent:{agent_id}:errors",
                1.0,
                metadata={"error": str(e)}
            )
            
            # Update health status for error
            if self._health_tracker:
                await self._health_tracker.update_health(
                    f"execution_{agent_id}",
                    HealthStatus(
                        status="CRITICAL",
                        source="phase_zero_orchestrator",
                        description=f"Agent {agent_id} error: {str(e)}",
                        metadata={"error": str(e)}
                    )
                )
            
            raise

    async def with_timeout(self, coro, timeout_seconds: float, operation_name: str):
        """Execute a coroutine with a timeout and monitoring."""
        try:
            # Update health status for operation start
            if self._health_tracker:
                await self._health_tracker.update_health(
                    f"operation_{operation_name}",
                    HealthStatus(
                        status="HEALTHY",
                        source="phase_zero_orchestrator",
                        description=f"Starting operation {operation_name}",
                        metadata={"timeout": timeout_seconds}
                    )
                )
            
            # Start timer
            start_time = datetime.now()
            
            # Execute with timeout
            result = await asyncio.wait_for(coro, timeout=timeout_seconds)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Record execution time metric
            await self._metrics_manager.record_metric(
                f"operation:{operation_name}:execution_time",
                execution_time,
                metadata={"success": True}
            )
            
            # Update health status for operation completion
            if self._health_tracker:
                await self._health_tracker.update_health(
                    f"operation_{operation_name}",
                    HealthStatus(
                        status="HEALTHY",
                        source="phase_zero_orchestrator",
                        description=f"Operation {operation_name} completed",
                        metadata={"execution_time": execution_time}
                    )
                )
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Operation {operation_name} timed out after {timeout_seconds}s")
            
            # Record timeout metric
            await self._metrics_manager.record_metric(
                "operation_timeouts",
                1.0,
                metadata={"operation": operation_name}
            )
            
            # Update health status for operation timeout
            if self._health_tracker:
                await self._health_tracker.update_health(
                    f"operation_{operation_name}",
                    HealthStatus(
                        status="CRITICAL",
                        source="phase_zero_orchestrator",
                        description=f"Operation {operation_name} timed out after {timeout_seconds}s",
                        metadata={"timeout": timeout_seconds}
                    )
                )
            
            # Emit timeout event
            await self._event_queue.emit(
                ResourceEventTypes.TIMEOUT_OCCURRED.value,
                {
                    "operation": operation_name,
                    "timeout": timeout_seconds,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            raise

    async def _get_phase_one_outputs(self) -> Dict[str, Dict]:
        """Get phase one outputs with caching."""
        cache_key = "phase_one_outputs"
        
        # Try cache first
        cached = await self._cache_manager.get_cache(cache_key)
        if cached:
            return cached
            
        # Get from state manager
        outputs = {}
        for output_type in ["garden_planner", "environmental_analysis", "root_system", "tree_placement"]:
            state = await self._state_manager.get_state(f"{output_type}_output")
            if not state:
                raise ValueError(f"Required Phase 1 output missing: {output_type}")
            outputs[f"{output_type}_output"] = state
            
        # Cache results
        await self._cache_manager.set_cache(
            cache_key,
            outputs,
            metadata={"timestamp": datetime.now().isoformat()}
        )
        
        return outputs
        
    async def _get_system_state(self) -> Dict[str, Any]:
        """Get current system state."""
        return {
            "phase_zero": await self._state_manager.get_state("phase_zero:orchestrator"),
            "system_monitor": await self._state_manager.get_state("system_monitor:state"),
            "timestamp": datetime.now().isoformat()
        }
        

