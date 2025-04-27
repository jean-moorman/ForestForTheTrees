import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from resources import (
    ResourceType, ResourceEventTypes, EventQueue, StateManager, AgentContextManager, 
    CacheManager, MetricsManager, ErrorHandler, HealthTracker, SystemMonitor, 
    SystemMonitorConfig, HealthStatus
)
from resources.monitoring import CircuitBreaker, MemoryMonitor, CircuitOpenError
from phase_one import PhaseZeroInterface

from phase_zero.agents.monitoring import MonitoringAgent
from phase_zero.agents.description_analysis import SunAgent, ShadeAgent, WindAgent
from phase_zero.agents.requirement_analysis import SoilAgent, MicrobialAgent, RainAgent
from phase_zero.agents.data_flow import RootSystemAgent, MycelialAgent, WormAgent
from phase_zero.agents.structural import InsectAgent, BirdAgent, TreeAgent
from phase_zero.agents.optimization import PollinatorAgent
from phase_zero.agents.synthesis import EvolutionAgent
from phase_zero.utils import with_timeout, get_system_state, execute_agent_with_monitoring
from phase_zero.validation.earth import validate_guideline_update
from phase_zero.validation.water import propagate_guideline_update

logger = logging.getLogger(__name__)

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
        
        # Track revision attempts by agent
        self.revision_attempts = {}
        
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
        
        # Initial description analysis agents
        self.sun_agent = SunAgent(
            self._event_queue,
            self._state_manager,
            self._context_manager,
            self._cache_manager,
            self._metrics_manager,
            self._error_handler,
            health_tracker=self._health_tracker,
            memory_monitor=self._memory_monitor
        )
        
        self.shade_agent = ShadeAgent(
            self._event_queue,
            self._state_manager,
            self._context_manager,
            self._cache_manager,
            self._metrics_manager,
            self._error_handler,
            health_tracker=self._health_tracker,
            memory_monitor=self._memory_monitor
        )
        
        self.wind_agent = WindAgent(
            self._event_queue,
            self._state_manager,
            self._context_manager,
            self._cache_manager,
            self._metrics_manager,
            self._error_handler,
            health_tracker=self._health_tracker,
            memory_monitor=self._memory_monitor
        )
        
        # Requirement analysis agents
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
        
        self.rain_agent = RainAgent(
            self._event_queue,
            self._state_manager,
            self._context_manager,
            self._cache_manager,
            self._metrics_manager,
            self._error_handler,
            health_tracker=self._health_tracker,
            memory_monitor=self._memory_monitor
        )

        # Data flow analysis agents
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
        
        self.worm_agent = WormAgent(
            self._event_queue,
            self._state_manager,
            self._context_manager,
            self._cache_manager,
            self._metrics_manager,
            self._error_handler,
            health_tracker=self._health_tracker,
            memory_monitor=self._memory_monitor
        )
        
        # Structural component analysis agents
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
        
        self.tree_agent = TreeAgent(
            self._event_queue,
            self._state_manager,
            self._context_manager,
            self._cache_manager,
            self._metrics_manager,
            self._error_handler,
            health_tracker=self._health_tracker,
            memory_monitor=self._memory_monitor
        )
        
        # Optimization analysis agent
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
        
        # Synthesis agent
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
            for agent in [self.monitoring_agent, 
                        self.sun_agent, self.shade_agent, self.wind_agent,
                        self.soil_agent, self.microbial_agent, self.rain_agent,
                        self.root_system_agent, self.mycelial_agent, self.worm_agent,
                        self.insect_agent, self.bird_agent, self.tree_agent,
                        self.pollinator_agent, self.evolution_agent]:
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
                    "monitoring", 
                    "sun", "shade", "wind",  # Initial description analysis
                    "soil", "microbial", "rain",  # Requirement analysis
                    "root_system", "mycelial", "worm",  # Data flow analysis
                    "insect", "bird", "tree",  # Structural component analysis
                    "pollinator",  # Optimization analysis
                    "evolution"  # Synthesis
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
                monitoring_result = await execute_agent_with_monitoring(
                    self.monitoring_agent, 
                    metrics, 
                    await get_system_state(self._state_manager),
                    health_tracker=self._health_tracker,
                    metrics_manager=self._metrics_manager,
                    event_queue=self._event_queue,
                    state_manager=self._state_manager,
                    revision_attempts=self.revision_attempts
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
                "sun": self.sun_agent,
                "shade": self.shade_agent,
                "wind": self.wind_agent,
                "soil": self.soil_agent,
                "microbial": self.microbial_agent,
                "rain": self.rain_agent,
                "root_system": self.root_system_agent,
                "mycelial": self.mycelial_agent,
                "worm": self.worm_agent,
                "insect": self.insect_agent,
                "bird": self.bird_agent,
                "tree": self.tree_agent,
                "pollinator": self.pollinator_agent
            }
            
            for agent_id, agent in agents_to_execute.items():
                try:
                    analysis_results[agent_id] = await execute_agent_with_monitoring(
                        agent, 
                        phase_one_outputs,
                        health_tracker=self._health_tracker,
                        metrics_manager=self._metrics_manager,
                        event_queue=self._event_queue,
                        state_manager=self._state_manager,
                        revision_attempts=self.revision_attempts
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
                evolution_result = await execute_agent_with_monitoring(
                    self.evolution_agent,
                    {
                        "monitoring": monitoring_result,
                        "analysis": analysis_results,
                        "phase_one": phase_one_outputs
                    },
                    health_tracker=self._health_tracker,
                    metrics_manager=self._metrics_manager,
                    event_queue=self._event_queue,
                    state_manager=self._state_manager,
                    revision_attempts=self.revision_attempts
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

    async def validate_guideline_update(self, agent_id: str, current_guideline: Dict, proposed_update: Dict) -> Dict:
        """Earth mechanism: Validate a proposed guideline update and provide feedback."""
        return await validate_guideline_update(
            agent_id, 
            current_guideline, 
            proposed_update, 
            health_tracker=self._health_tracker, 
            state_manager=self._state_manager
        )

    async def propagate_guideline_update(self, agent_id: str, updated_guideline: Dict, affected_agents: List[str] = None) -> Dict:
        """Water mechanism: Propagate guideline updates to affected downstream components."""
        return await propagate_guideline_update(
            agent_id, 
            updated_guideline, 
            affected_agents, 
            event_queue=self._event_queue,
            health_tracker=self._health_tracker, 
            state_manager=self._state_manager
        )