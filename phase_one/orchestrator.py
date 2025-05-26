"""
Phase One Orchestrator for Forest For The Trees (FFTT)

This module implements the PhaseOneOrchestrator class, which coordinates
the Phase One workflow including Earth Agent validation and Water Agent
coordination for sequential agent handoff.
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from resources import (
    EventQueue, StateManager, AgentContextManager,
    CacheManager, MetricsManager, ErrorHandler, HealthTracker, 
    SystemMonitor, MemoryMonitor
)
from system_error_recovery import SystemErrorRecovery
from resources.common import ResourceType, HealthStatus
from resources.events import ResourceEventTypes
from resources.monitoring import CircuitBreaker, CircuitOpenError
from phase_zero import PhaseZeroOrchestrator

from interface import AgentInterface

from phase_one.workflow import PhaseOneWorkflow
from phase_one.agents.garden_planner import GardenPlannerAgent
from phase_one.agents.earth_agent import EarthAgent
from phase_one.agents.environmental_analysis import EnvironmentalAnalysisAgent
from phase_one.agents.root_system_architect import RootSystemArchitectAgent
from phase_one.agents.tree_placement_planner import TreePlacementPlannerAgent
from phase_one.validation.garden_planner_validator import GardenPlannerValidator
from phase_one.validation.coordination import SequentialAgentCoordinator

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from phase_one.workflow import PhaseOneWorkflow

logger = logging.getLogger(__name__)

class PhaseOneOrchestrator:
    """
    Orchestrates Phase One operations with Earth Agent validation and Water Agent coordination.
    
    This class is responsible for:
    1. Initializing and managing all Phase One agents
    2. Coordinating the workflow execution with proper resource management
    3. Handling monitoring, circuit breakers, and error recovery
    4. Processing user tasks through the Phase One workflow
    5. Interfacing with Phase Zero for refinement analysis
    """
    
    def __init__(
        self,
        event_queue: EventQueue,
        state_manager: StateManager,
        context_manager: AgentContextManager,
        cache_manager: CacheManager,
        metrics_manager: MetricsManager,
        error_handler: ErrorHandler,
        error_recovery: Optional[SystemErrorRecovery] = None,
        phase_zero: Optional[PhaseZeroOrchestrator] = None,
        health_tracker: Optional[HealthTracker] = None,
        memory_monitor: Optional[MemoryMonitor] = None,
        system_monitor: Optional[SystemMonitor] = None,
        max_earth_validation_cycles: int = 3,
        validation_timeout: float = 120.0,
        # Optional pre-initialized agents and workflow
        garden_planner_agent: Optional[AgentInterface] = None,
        earth_agent: Optional[AgentInterface] = None,
        environmental_analysis_agent: Optional[AgentInterface] = None,
        root_system_architect_agent: Optional[AgentInterface] = None,
        tree_placement_planner_agent: Optional[AgentInterface] = None,
        workflow: Optional[PhaseOneWorkflow] = None
    ):
        """
        Initialize the Phase One orchestrator.
        
        Args:
            event_queue: Event queue for publishing/subscribing to events
            state_manager: State manager for persistent state
            context_manager: Context manager for agent contexts
            cache_manager: Cache manager for caching results
            metrics_manager: Metrics manager for recording metrics
            error_handler: Error handler for processing errors
            error_recovery: Optional error recovery system
            phase_zero: Optional phase zero orchestrator for refinement
            health_tracker: Optional health tracker for monitoring
            memory_monitor: Optional memory monitor for tracking memory usage
            system_monitor: Optional system monitor for circuit breakers
            max_earth_validation_cycles: Maximum number of Earth validation cycles
            validation_timeout: Timeout for validation processes in seconds
        """
        # Resource managers
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._context_manager = context_manager
        self._cache_manager = cache_manager
        self._metrics_manager = metrics_manager
        self._error_handler = error_handler
        self._error_recovery = error_recovery
        
        # Monitoring components
        self._health_tracker = health_tracker
        self._memory_monitor = memory_monitor
        self._system_monitor = system_monitor
        
        # Phase Zero for refinement
        self._phase_zero = phase_zero
        
        # Configuration
        self._max_validation_cycles = max_earth_validation_cycles
        self._validation_timeout = validation_timeout
        
        # Initialize circuit breaker for orchestration
        self._orchestration_circuit = CircuitBreaker(
            "phase_one_orchestration", 
            event_queue
        )
        
        # Register with system monitor if available
        if self._system_monitor and self._orchestration_circuit:
            asyncio.create_task(
                self._system_monitor.register_circuit_breaker(
                    "phase_one_orchestration", 
                    self._orchestration_circuit
                )
            )
        
        # Store pre-initialized agents if provided
        self.garden_planner_agent = garden_planner_agent
        self.earth_agent = earth_agent
        self.environmental_analysis_agent = environmental_analysis_agent
        self.root_system_architect_agent = root_system_architect_agent
        self.tree_placement_planner_agent = tree_placement_planner_agent
        self.phase_one_workflow = workflow
        
        # Initialize agents and workflow if not provided
        if (
            not self.garden_planner_agent or
            not self.earth_agent or
            not self.environmental_analysis_agent or
            not self.root_system_architect_agent or
            not self.tree_placement_planner_agent or
            not self.phase_one_workflow
        ):
            self._initialize_agents_and_workflow()
        
        # Store initial state
        asyncio.create_task(self._store_initial_state())

        # Report initial health status
        if self._health_tracker:
            asyncio.create_task(
                self._health_tracker.update_health(
                    "phase_one_orchestrator",
                    HealthStatus(
                        status="HEALTHY",
                        source="phase_one_orchestrator",
                        description="Phase one orchestrator initialized",
                        metadata={}
                    )
                )
            )
    
    def _initialize_agents_and_workflow(self) -> None:
        """Initialize all Phase One agents and workflow."""
        # Only initialize agents that weren't provided
        
        # Garden Planner Agent
        if not self.garden_planner_agent:
            self.garden_planner_agent = GardenPlannerAgent(
                "garden_planner",
                self._event_queue,
                self._state_manager,
                self._context_manager,
                self._cache_manager,
                self._metrics_manager,
                self._error_handler,
                self._memory_monitor,
                health_tracker=self._health_tracker
            )
        
        # Earth Agent for validation
        if not self.earth_agent:
            self.earth_agent = EarthAgent(
                "earth_agent",
                self._event_queue,
                self._state_manager,
                self._context_manager,
                self._cache_manager,
                self._metrics_manager,
                self._error_handler,
                self._memory_monitor,
                health_tracker=self._health_tracker
            )
        
        # Environmental Analysis Agent
        if not self.environmental_analysis_agent:
            self.environmental_analysis_agent = EnvironmentalAnalysisAgent(
                "environmental_analysis",
                self._event_queue,
                self._state_manager,
                self._context_manager,
                self._cache_manager,
                self._metrics_manager,
                self._error_handler,
                self._memory_monitor,
                health_tracker=self._health_tracker
            )
        
        # Root System Architect Agent
        if not self.root_system_architect_agent:
            self.root_system_architect_agent = RootSystemArchitectAgent(
                "root_system_architect",
                self._event_queue,
                self._state_manager,
                self._context_manager,
                self._cache_manager,
                self._metrics_manager,
                self._error_handler,
                self._memory_monitor,
                health_tracker=self._health_tracker
            )
        
        # Tree Placement Planner Agent
        if not self.tree_placement_planner_agent:
            self.tree_placement_planner_agent = TreePlacementPlannerAgent(
                "tree_placement_planner",
                self._event_queue,
                self._state_manager,
                self._context_manager,
                self._cache_manager,
                self._metrics_manager,
                self._error_handler,
                self._memory_monitor,
                health_tracker=self._health_tracker
            )
        
        # Initialize Phase One Workflow if not provided
        if not self.phase_one_workflow:
            self.phase_one_workflow = PhaseOneWorkflow(
                self.garden_planner_agent,
                self.earth_agent,
                self.environmental_analysis_agent,
                self.root_system_architect_agent,
                self.tree_placement_planner_agent,
                self._event_queue,
                self._state_manager,
                max_earth_validation_cycles=self._max_validation_cycles,
                validation_timeout=self._validation_timeout
            )
        
        # Register agent circuit breakers with system monitor
        if self._system_monitor:
            for agent in [
                self.garden_planner_agent, 
                self.earth_agent,
                self.environmental_analysis_agent,
                self.root_system_architect_agent,
                self.tree_placement_planner_agent
            ]:
                # Register all circuit breakers for each agent
                for cb_name, cb in agent._circuit_breakers.items() if hasattr(agent, '_circuit_breakers') else []:
                    asyncio.create_task(
                        self._system_monitor.register_circuit_breaker(
                            f"{agent.agent_id or agent.interface_id}_{cb_name}", 
                            cb
                        )
                    )
    
    async def _store_initial_state(self) -> None:
        """Store orchestrator state."""
        await self._state_manager.set_state(
            "phase_one:orchestrator",
            {
                "status": "initialized",
                "timestamp": datetime.now().isoformat(),
                "agents": [
                    "garden_planner",
                    "earth_agent",
                    "environmental_analysis",
                    "root_system_architect",
                    "tree_placement_planner"
                ]
            },
            resource_type=ResourceType.STATE
        )
    
    async def process_task(self, user_request: str, operation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process user task through Phase One workflow.
        
        Args:
            user_request: User request to process
            operation_id: Optional identifier for this operation
            
        Returns:
            Result of Phase One processing
        """
        if not operation_id:
            operation_id = f"phase_one_{datetime.now().isoformat()}"
        
        process_start_time = datetime.now()
        
        try:
            # Update health status to processing
            if self._health_tracker:
                await self._health_tracker.update_health(
                    "phase_one_orchestrator",
                    HealthStatus(
                        status="HEALTHY",
                        source="phase_one_orchestrator",
                        description="Processing user task",
                        metadata={"operation_id": operation_id}
                    )
                )
            
            # Store process start
            await self._state_manager.set_state(
                f"phase_one:process:{operation_id}",
                {
                    "status": "started",
                    "timestamp": datetime.now().isoformat(),
                    "user_request": user_request[:200] + "..." if len(user_request) > 200 else user_request
                },
                resource_type=ResourceType.MONITOR
            )
            
            # Use circuit breaker to protect the entire processing pipeline
            try:
                result = await self._orchestration_circuit.execute(
                    lambda: self._process_task_internal(user_request, operation_id)
                )
            except CircuitOpenError:
                logger.error("Phase one orchestration circuit open, processing rejected")
                
                # Update health status to critical
                if self._health_tracker:
                    await self._health_tracker.update_health(
                        "phase_one_orchestrator",
                        HealthStatus(
                            status="CRITICAL",
                            source="phase_one_orchestrator",
                            description="Task processing rejected due to circuit breaker open",
                            metadata={"circuit": "phase_one_orchestration"}
                        )
                    )
                
                return {
                    "status": "error",
                    "message": "Phase one processing rejected due to circuit breaker open",
                    "operation_id": operation_id
                }
            
            # Calculate execution time
            execution_time = (datetime.now() - process_start_time).total_seconds()
            
            # Record execution time metric
            await self._metrics_manager.record_metric(
                "phase_one:execution_time",
                execution_time,
                metadata={"success": True, "operation_id": operation_id}
            )
            
            # Update health status to completed
            if self._health_tracker:
                await self._health_tracker.update_health(
                    "phase_one_orchestrator",
                    HealthStatus(
                        status="HEALTHY",
                        source="phase_one_orchestrator",
                        description="Task processing completed",
                        metadata={
                            "execution_time": execution_time,
                            "operation_id": operation_id
                        }
                    )
                )
            
            # Return the result with execution time
            return {
                **result,
                "execution_time": execution_time
            }
            
        except Exception as e:
            logger.error(f"Task processing error: {e}")
            
            # Calculate execution time before failure
            execution_time = (datetime.now() - process_start_time).total_seconds()
            
            # Record execution time metric for failed execution
            await self._metrics_manager.record_metric(
                "phase_one:execution_time",
                execution_time,
                metadata={"success": False, "error": str(e), "operation_id": operation_id}
            )
            
            # Update health status to critical
            if self._health_tracker:
                await self._health_tracker.update_health(
                    "phase_one_orchestrator",
                    HealthStatus(
                        status="CRITICAL",
                        source="phase_one_orchestrator",
                        description=f"Task processing failed: {str(e)}",
                        metadata={"error": str(e), "operation_id": operation_id}
                    )
                )
            
            # Store error state
            await self._state_manager.set_state(
                f"phase_one:process:{operation_id}",
                {
                    "status": "error",
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                    "execution_time": execution_time
                },
                resource_type=ResourceType.STATE
            )
            
            # Emit error event
            await self._event_queue.emit(
                ResourceEventTypes.ERROR_OCCURRED.value,
                {
                    "operation_id": operation_id,
                    "error": str(e),
                    "phase": "phase_one"
                }
            )
            
            # Return error result
            return {
                "status": "error",
                "message": str(e),
                "operation_id": operation_id,
                "execution_time": execution_time
            }
    
    async def _process_task_internal(self, user_request: str, operation_id: str) -> Dict[str, Any]:
        """
        Internal method for processing tasks with monitoring.
        
        Args:
            user_request: User request to process
            operation_id: Identifier for this operation
            
        Returns:
            Phase One processed result
        """
        try:
            # Execute Phase One workflow
            logger.info(f"Executing Phase One workflow for operation {operation_id}")
            
            workflow_result = await self.phase_one_workflow.execute_phase_one(
                user_request,
                operation_id
            )
            
            # Store workflow result
            await self._state_manager.set_state(
                f"phase_one:process:{operation_id}:workflow_result",
                workflow_result,
                resource_type=ResourceType.STATE
            )
            
            # Check if workflow was successful
            if workflow_result.get("status") == "completed":
                logger.info(f"Phase One workflow completed successfully for operation {operation_id}")
                
                # Emit success event
                await self._event_queue.emit(
                    "phase_one_task_processed",
                    {
                        "operation_id": operation_id,
                        "status": "success",
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                # Extract components for phase two
                final_output = workflow_result.get("final_output", {})
                component_architecture = final_output.get("component_architecture", {})
                
                # Format result for phase two
                result = {
                    "status": "success",
                    "message": "Phase One completed successfully",
                    "operation_id": operation_id,
                    "structural_components": component_architecture.get("components", []),
                    "system_requirements": {
                        "task_analysis": final_output.get("task_analysis", {}),
                        "environmental_analysis": final_output.get("environmental_analysis", {}),
                        "data_architecture": final_output.get("data_architecture", {})
                    },
                    "workflow_result": workflow_result
                }
                
                # Store final result for phase two
                await self._state_manager.set_state(
                    f"phase_one:process:{operation_id}:final_result",
                    result,
                    resource_type=ResourceType.STATE
                )
                
                return result
            else:
                # Workflow encountered an error or failed stage
                logger.error(f"Phase One workflow failed for operation {operation_id}: {workflow_result.get('status')}")
                
                # Emit failure event
                await self._event_queue.emit(
                    "phase_one_task_failed",
                    {
                        "operation_id": operation_id,
                        "status": "failure",
                        "failure_stage": workflow_result.get("failure_stage"),
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                # Return failure result
                return {
                    "status": "failed",
                    "message": f"Phase One failed at stage: {workflow_result.get('failure_stage', 'unknown')}",
                    "operation_id": operation_id,
                    "failure_stage": workflow_result.get("failure_stage"),
                    "error": workflow_result.get("error"),
                    "workflow_result": workflow_result
                }
        except Exception as e:
            logger.error(f"Error in Phase One internal processing: {str(e)}")
            raise
    
    async def get_agent_metrics(self, agent_id: str) -> Dict[str, Any]:
        """
        Get metrics for a specific agent.
        
        Args:
            agent_id: ID of the agent to get metrics for
            
        Returns:
            Agent metrics
        """
        try:
            # Get agent metrics from metrics manager
            agent_metrics = await self._metrics_manager.get_agent_metrics(agent_id)
            
            # Get agent state from state manager
            agent_state = await self._state_manager.get_state(f"agent:{agent_id}:state", "STATE")
            
            # Get agent workflow contributions
            agent_workflows = await self._state_manager.get_states_by_pattern(
                f"phase_one_workflow:*:*:{agent_id}",
                "STATE"
            )
            
            # Return combined metrics
            return {
                "status": "success",
                "agent_id": agent_id,
                "metrics": agent_metrics,
                "state": agent_state,
                "workflows": len(agent_workflows),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting agent metrics for {agent_id}: {str(e)}")
            return {
                "status": "error",
                "agent_id": agent_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_workflow_status(self, operation_id: str) -> Dict[str, Any]:
        """
        Get current workflow status for an operation.
        
        Args:
            operation_id: Identifier for the workflow
            
        Returns:
            Workflow status information
        """
        return await self.phase_one_workflow.get_workflow_status(operation_id)
    
    async def shutdown(self) -> None:
        """Shut down the orchestrator and release resources."""
        logger.info("Shutting down Phase One orchestrator")
        
        try:
            # Emit shutdown event
            await self._event_queue.emit(
                "phase_one_orchestrator_shutdown",
                {
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Update health status to shutting down
            if self._health_tracker:
                await self._health_tracker.update_health(
                    "phase_one_orchestrator",
                    HealthStatus(
                        status="WARNING",
                        source="phase_one_orchestrator",
                        description="Orchestrator shutting down",
                        metadata={}
                    )
                )
            
            # Store shutdown state
            await self._state_manager.set_state(
                "phase_one:orchestrator",
                {
                    "status": "shutdown",
                    "timestamp": datetime.now().isoformat()
                },
                resource_type=ResourceType.STATE
            )
            
            logger.info("Phase One orchestrator shutdown complete")
        except Exception as e:
            logger.error(f"Error during Phase One orchestrator shutdown: {str(e)}")