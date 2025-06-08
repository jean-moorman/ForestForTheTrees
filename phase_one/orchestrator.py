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
# Circuit breaker imports removed - protection now at API level
from phase_zero import PhaseZeroOrchestrator

from interfaces import AgentInterface

from phase_one.workflow import PhaseOneWorkflow
from phase_one.agents.garden_planner import GardenPlannerAgent
from phase_one.agents.earth_agent import EarthAgent
from phase_one.agents.environmental_analysis import EnvironmentalAnalysisAgent
from phase_one.agents.root_system_architect import RootSystemArchitectAgent
from phase_one.agents.tree_placement_planner import TreePlacementPlannerAgent
from phase_one.agents.foundation_refinement import FoundationRefinementAgent
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
        foundation_refinement_agent: Optional[FoundationRefinementAgent] = None,
        workflow: Optional[PhaseOneWorkflow] = None,
        max_refinement_cycles: int = 5
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
        self._max_refinement_cycles = max_refinement_cycles
        
        # Circuit breaker removed - orchestration is internal coordination, 
        # not external API calls that need protection
        
        # Store pre-initialized agents if provided
        self.garden_planner_agent = garden_planner_agent
        self.earth_agent = earth_agent
        self.environmental_analysis_agent = environmental_analysis_agent
        self.root_system_architect_agent = root_system_architect_agent
        self.tree_placement_planner_agent = tree_placement_planner_agent
        self.foundation_refinement_agent = foundation_refinement_agent
        self.phase_one_workflow = workflow
        
        # Initialize agents and workflow if not provided
        if (
            not self.garden_planner_agent or
            not self.earth_agent or
            not self.environmental_analysis_agent or
            not self.root_system_architect_agent or
            not self.tree_placement_planner_agent or
            not self.foundation_refinement_agent or
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
        
        # Foundation Refinement Agent
        if not self.foundation_refinement_agent:
            self.foundation_refinement_agent = FoundationRefinementAgent(
                self._event_queue,
                self._state_manager,
                self._context_manager,
                self._cache_manager,
                self._metrics_manager,
                self._error_handler,
                self._memory_monitor,
                health_tracker=self._health_tracker,
                max_refinement_cycles=self._max_refinement_cycles
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
            
            # Direct processing - LLM protection handled at API level
            try:
                result = await self._process_task_internal(user_request, operation_id)
            except Exception as e:
                logger.error(f"Phase one processing failed: {str(e)}")
                
                # Update health status to critical
                if self._health_tracker:
                    await self._health_tracker.update_health(
                        "phase_one_orchestrator",
                        HealthStatus(
                            status="CRITICAL", 
                            source="phase_one_orchestrator",
                            description=f"Task processing failed: {str(e)}",
                            metadata={"error": str(e)}
                        )
                    )
                
                return {
                    "status": "error",
                    "message": f"Phase one processing failed: {str(e)}",
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
                
                # Execute Foundation Refinement workflow with Phase Zero feedback
                refinement_result = await self._execute_foundation_refinement_workflow(
                    result, workflow_result, operation_id
                )
                
                # Check refinement decision
                if not self.foundation_refinement_agent.should_proceed_to_phase_two(refinement_result):
                    # Refinement is needed - execute refinement cycle
                    logger.info(f"Foundation refinement required for operation {operation_id}")
                    return await self._execute_refinement_cycle(result, refinement_result, operation_id)
                else:
                    # No refinement needed - add refinement feedback and proceed
                    # Handle potential double-nesting from refinement result
                    if isinstance(refinement_result, dict) and "refinement_analysis" in refinement_result:
                        result["refinement_analysis"] = refinement_result["refinement_analysis"]
                    else:
                        result["refinement_analysis"] = refinement_result
                    logger.info(f"No refinement required - proceeding to Phase Two for operation {operation_id}")
                
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
    
    async def _execute_foundation_refinement_workflow(
        self,
        phase_one_result: Dict[str, Any],
        workflow_result: Dict[str, Any],
        operation_id: str
    ) -> Dict[str, Any]:
        """
        Execute the complete Foundation Refinement workflow with Phase Zero feedback.
        
        Args:
            phase_one_result: Phase One workflow result
            workflow_result: Raw workflow result
            operation_id: Operation identifier
            
        Returns:
            Foundation refinement analysis result
        """
        try:
            logger.info(f"Starting Foundation Refinement workflow for operation {operation_id}")
            
            # Step 1: Get Phase Zero quality assurance feedback if available
            phase_zero_feedback = {}
            if self._phase_zero:
                try:
                    logger.info(f"Initiating Phase Zero quality assurance for operation {operation_id}")
                    
                    # Prepare metrics for Phase Zero analysis
                    phase_zero_metrics = {
                        "operation_id": operation_id,
                        "phase_one_result": phase_one_result,
                        "workflow_metrics": workflow_result.get("metrics", {}),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Call Phase Zero process_system_metrics
                    phase_zero_feedback = await self._phase_zero.process_system_metrics(phase_zero_metrics)
                    
                    # Store Phase Zero feedback
                    await self._state_manager.set_state(
                        f"phase_one:process:{operation_id}:phase_zero_feedback",
                        phase_zero_feedback,
                        resource_type=ResourceType.STATE
                    )
                    
                    logger.info(f"Phase Zero quality assurance completed for operation {operation_id}")
                    
                except Exception as e:
                    logger.warning(f"Phase Zero quality assurance failed for operation {operation_id}: {e}")
                    phase_zero_feedback = {
                        "status": "error",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                logger.info(f"No Phase Zero orchestrator available for operation {operation_id}")
                phase_zero_feedback = {
                    "status": "not_available",
                    "message": "Phase Zero orchestrator not configured",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Step 2: Execute Foundation Refinement Analysis
            logger.info(f"Executing Foundation Refinement analysis for operation {operation_id}")
            
            refinement_result = await self.foundation_refinement_agent.analyze_phase_one_outputs(
                phase_one_result,
                phase_zero_feedback,
                operation_id
            )
            
            # Store complete refinement workflow result
            await self._state_manager.set_state(
                f"phase_one:process:{operation_id}:refinement_workflow",
                {
                    "phase_zero_feedback": phase_zero_feedback,
                    "refinement_analysis": refinement_result,
                    "timestamp": datetime.now().isoformat()
                },
                resource_type=ResourceType.STATE
            )
            
            logger.info(f"Foundation Refinement workflow completed for operation {operation_id}")
            return refinement_result
            
        except Exception as e:
            logger.error(f"Foundation Refinement workflow failed for operation {operation_id}: {e}")
            
            # Return safe default to avoid blocking the system
            return {
                "refinement_analysis": {
                    "critical_failure": {
                        "category": "refinement_workflow_error",
                        "description": f"Refinement workflow failed: {str(e)}",
                        "evidence": [],
                        "phase_zero_signals": []
                    },
                    "root_cause": {
                        "responsible_agent": "none",
                        "failure_point": "refinement_workflow",
                        "causal_chain": [f"Refinement workflow error: {str(e)}"],
                        "verification_steps": []
                    },
                    "refinement_action": {
                        "action": "proceed_to_phase_two",
                        "justification": "Refinement workflow failed - proceeding to avoid system blockage",
                        "specific_guidance": {
                            "current_state": "Refinement workflow error",
                            "required_state": "Proceed with current outputs",
                            "adaptation_path": ["Use current Phase One outputs", "Monitor for issues in Phase Two"]
                        }
                    }
                },
                "workflow_error": True,
                "error": str(e)
            }
    
    async def _execute_refinement_cycle(
        self,
        phase_one_result: Dict[str, Any],
        refinement_result: Dict[str, Any],
        operation_id: str
    ) -> Dict[str, Any]:
        """
        Execute a refinement cycle by routing system back to the appropriate agent.
        
        Args:
            phase_one_result: Current Phase One result
            refinement_result: Foundation refinement analysis
            operation_id: Operation identifier
            
        Returns:
            Updated Phase One result after refinement
        """
        try:
            logger.info(f"Starting refinement cycle for operation {operation_id}")
            
            # Get refinement target and guidance
            target_agent = self.foundation_refinement_agent.get_refinement_target_agent(refinement_result)
            refinement_guidance = self.foundation_refinement_agent.get_refinement_guidance(refinement_result)
            
            if not target_agent:
                logger.warning(f"No target agent identified for refinement in operation {operation_id}")
                # Add refinement result and proceed
                phase_one_result["refinement_analysis"] = refinement_result
                return phase_one_result
            
            logger.info(f"Refinement target: {target_agent} for operation {operation_id}")
            
            # Increment refinement cycle
            self.foundation_refinement_agent.increment_cycle()
            
            # Track refinement decision with Air Agent
            try:
                from resources.air_agent import track_decision_event
                await track_decision_event(
                    decision_agent="foundation_refinement_agent",
                    decision_type="refinement_cycle",
                    decision_details={
                        "operation_id": operation_id,
                        "target_agent": target_agent,
                        "refinement_action": refinement_guidance.get("action"),
                        "cycle": self.foundation_refinement_agent._current_cycle
                    },
                    decision_outcome={"outcome": "refinement_initiated"}
                )
            except Exception as e:
                logger.warning(f"Failed to track refinement decision with Air Agent: {e}")
            
            # Execute actual agent recursion
            logger.info(f"Executing recursion for {target_agent} (cycle {self.foundation_refinement_agent._current_cycle})")
            
            # Re-execute workflow starting from the target agent
            updated_result = await self._execute_agent_recursion(
                target_agent, 
                phase_one_result, 
                refinement_guidance, 
                operation_id
            )
            
            # Add refinement metadata to result
            updated_result["refinement_analysis"] = {
                "status": "refinement_executed",
                "target_agent": target_agent,
                "guidance": refinement_guidance,
                "cycle": self.foundation_refinement_agent._current_cycle,
                "message": f"Successfully re-executed workflow starting from {target_agent}"
            }
            
            return updated_result
                
        except Exception as e:
            logger.error(f"Refinement cycle failed for operation {operation_id}: {e}")
            
            # Add error information and proceed to avoid blocking system
            phase_one_result["refinement_analysis"] = refinement_result
            phase_one_result["refinement_error"] = {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            return phase_one_result

    async def _execute_agent_recursion(
        self,
        target_agent: str,
        current_result: Dict[str, Any],
        refinement_guidance: Dict[str, Any],
        operation_id: str
    ) -> Dict[str, Any]:
        """
        Execute agent recursion by re-running the workflow from the target agent.
        
        This method implements the core recursion logic where the system returns
        to the specified agent and resumes normal Phase One execution from that point.
        
        Args:
            target_agent: The agent to restart from
            current_result: Current Phase One result
            refinement_guidance: Specific guidance for refinement
            operation_id: Operation identifier
            
        Returns:
            Updated Phase One result after re-execution
        """
        try:
            logger.info(f"Starting agent recursion from {target_agent} for operation {operation_id}")
            
            # Get original user request from current result
            user_request = current_result.get("workflow_result", {}).get("user_request", "")
            if not user_request:
                # Fallback to extracting from stored workflow state
                workflow_state = await self._state_manager.get_state(
                    f"phase_one_workflow:{operation_id}",
                    default={},
                    resource_type=ResourceType.STATE
                )
                user_request = workflow_state.get("user_request", "No request found")
            
            # Create a new workflow instance for recursion
            recursion_workflow = PhaseOneWorkflow(
                garden_planner_agent=self.garden_planner_agent,
                earth_agent=self.earth_agent,
                environmental_analysis_agent=self.environmental_analysis_agent,
                root_system_architect_agent=self.root_system_architect_agent,
                tree_placement_planner_agent=self.tree_placement_planner_agent,
                event_queue=self._event_queue,
                state_manager=self._state_manager,
                max_earth_validation_cycles=3,
                validation_timeout=120.0
            )
            
            # Execute partial workflow based on target agent
            if target_agent == "garden_planner":
                # Re-execute entire workflow from beginning
                logger.info(f"Re-executing complete workflow from Garden Planner for operation {operation_id}")
                workflow_result = await recursion_workflow.execute(user_request, f"{operation_id}_recursion_{self.foundation_refinement_agent._current_cycle}")
                
            elif target_agent == "environmental_analysis":
                # Re-execute from Environmental Analysis onward
                logger.info(f"Re-executing workflow from Environmental Analysis for operation {operation_id}")
                workflow_result = await self._execute_from_environmental_analysis(
                    recursion_workflow, user_request, current_result, operation_id
                )
                
            elif target_agent == "root_system_architect":
                # Re-execute from Root System Architect onward  
                logger.info(f"Re-executing workflow from Root System Architect for operation {operation_id}")
                workflow_result = await self._execute_from_root_system_architect(
                    recursion_workflow, user_request, current_result, operation_id
                )
                
            elif target_agent == "tree_placement_planner":
                # Re-execute from Tree Placement Planner onward
                logger.info(f"Re-executing workflow from Tree Placement Planner for operation {operation_id}")
                workflow_result = await self._execute_from_tree_placement_planner(
                    recursion_workflow, user_request, current_result, operation_id
                )
                
            else:
                logger.warning(f"Unknown target agent {target_agent}, executing full workflow")
                workflow_result = await recursion_workflow.execute(user_request, f"{operation_id}_recursion_{self.foundation_refinement_agent._current_cycle}")
            
            # Process workflow result into Phase One format
            if workflow_result.get("status") == "success":
                final_output = workflow_result.get("final_output", {})
                component_architecture = final_output.get("component_architecture", {})
                
                # Format result for phase two
                updated_result = {
                    "status": "success",
                    "message": "Phase One completed successfully after refinement",
                    "operation_id": operation_id,
                    "structural_components": component_architecture.get("components", []),
                    "system_requirements": {
                        "task_analysis": final_output.get("task_analysis", {}),
                        "environmental_analysis": final_output.get("environmental_analysis", {}),
                        "data_architecture": final_output.get("data_architecture", {})
                    },
                    "workflow_result": workflow_result,
                    "recursion_metadata": {
                        "target_agent": target_agent,
                        "cycle": self.foundation_refinement_agent._current_cycle,
                        "guidance_applied": refinement_guidance
                    }
                }
                
                # Store updated final result
                await self._state_manager.set_state(
                    f"phase_one:process:{operation_id}:final_result",
                    updated_result,
                    resource_type=ResourceType.STATE
                )
                
                return updated_result
            else:
                # Workflow failed during recursion
                logger.error(f"Agent recursion workflow failed for operation {operation_id}")
                current_result["recursion_error"] = {
                    "target_agent": target_agent,
                    "error": "Workflow failed during recursion",
                    "workflow_result": workflow_result
                }
                return current_result
                
        except Exception as e:
            logger.error(f"Agent recursion failed for operation {operation_id}: {e}")
            current_result["recursion_error"] = {
                "target_agent": target_agent,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            return current_result

    async def _execute_from_environmental_analysis(
        self, 
        workflow: "PhaseOneWorkflow", 
        user_request: str,
        current_result: Dict[str, Any],
        operation_id: str
    ) -> Dict[str, Any]:
        """Execute workflow starting from Environmental Analysis agent."""
        try:
            # Get existing Garden Planner result (must exist since we're in refinement stage)
            garden_planner_result = current_result.get("workflow_result", {}).get("agents", {}).get("garden_planner")
            assert garden_planner_result, "Garden Planner result missing during refinement - this should never happen"
            
            # Execute from Environmental Analysis onward
            task_analysis = garden_planner_result.get("task_analysis", {})
            env_result = await workflow._execute_environmental_analysis(task_analysis, f"{operation_id}_env_recursion")
            
            if not env_result.get("success", False):
                return {"status": "failed", "failure_stage": "environmental_analysis", "agents": {"environmental_analysis": env_result}}
            
            # Continue with Root System Architect
            environmental_analysis = env_result.get("analysis", {})
            root_result = await workflow._execute_root_system_architect(environmental_analysis, f"{operation_id}_env_recursion")
            
            if not root_result.get("success", False):
                return {"status": "failed", "failure_stage": "root_system_architect", "agents": {"environmental_analysis": env_result, "root_system_architect": root_result}}
            
            # Continue with Tree Placement Planner
            data_architecture = root_result.get("data_architecture", {})
            tree_result = await workflow._execute_tree_placement_planner(
                task_analysis, environmental_analysis, data_architecture, f"{operation_id}_env_recursion"
            )
            
            # Build final result
            final_output = {
                "task_analysis": task_analysis,
                "environmental_analysis": environmental_analysis,
                "data_architecture": data_architecture,
                "component_architecture": tree_result.get("component_architecture", {})
            }
            
            return {
                "status": "success",
                "user_request": user_request,
                "final_output": final_output,
                "agents": {
                    "garden_planner": garden_planner_result,
                    "environmental_analysis": env_result,
                    "root_system_architect": root_result,
                    "tree_placement_planner": tree_result
                }
            }
            
        except Exception as e:
            logger.error(f"Environmental Analysis recursion failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def _execute_from_root_system_architect(
        self, 
        workflow: "PhaseOneWorkflow", 
        user_request: str,
        current_result: Dict[str, Any],
        operation_id: str
    ) -> Dict[str, Any]:
        """Execute workflow starting from Root System Architect agent."""
        try:
            # Get existing results (must exist since we're in refinement stage)
            agents = current_result.get("workflow_result", {}).get("agents", {})
            
            garden_planner_result = agents.get("garden_planner")
            assert garden_planner_result, "Garden Planner result missing during refinement - this should never happen"
            
            env_result = agents.get("environmental_analysis")
            assert env_result, "Environmental Analysis result missing during refinement - this should never happen"
            
            # Execute from Root System Architect onward
            environmental_analysis = env_result.get("analysis", {})
            root_result = await workflow._execute_root_system_architect(environmental_analysis, f"{operation_id}_root_recursion")
            
            if not root_result.get("success", False):
                return {"status": "failed", "failure_stage": "root_system_architect", "agents": {"root_system_architect": root_result}}
            
            # Continue with Tree Placement Planner
            task_analysis = garden_planner_result.get("task_analysis", {})
            data_architecture = root_result.get("data_architecture", {})
            tree_result = await workflow._execute_tree_placement_planner(
                task_analysis, environmental_analysis, data_architecture, f"{operation_id}_root_recursion"
            )
            
            # Build final result
            final_output = {
                "task_analysis": task_analysis,
                "environmental_analysis": environmental_analysis,
                "data_architecture": data_architecture,
                "component_architecture": tree_result.get("component_architecture", {})
            }
            
            return {
                "status": "success",
                "user_request": user_request,
                "final_output": final_output,
                "agents": {
                    "garden_planner": garden_planner_result,
                    "environmental_analysis": env_result,
                    "root_system_architect": root_result,
                    "tree_placement_planner": tree_result
                }
            }
            
        except Exception as e:
            logger.error(f"Root System Architect recursion failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def _execute_from_tree_placement_planner(
        self, 
        workflow: "PhaseOneWorkflow", 
        user_request: str,
        current_result: Dict[str, Any],
        operation_id: str
    ) -> Dict[str, Any]:
        """Execute workflow starting from Tree Placement Planner agent."""
        try:
            # Get existing results (must exist since we're in refinement stage)
            agents = current_result.get("workflow_result", {}).get("agents", {})
            
            garden_planner_result = agents.get("garden_planner")
            assert garden_planner_result, "Garden Planner result missing during refinement - this should never happen"
            
            env_result = agents.get("environmental_analysis")
            assert env_result, "Environmental Analysis result missing during refinement - this should never happen"
            
            root_result = agents.get("root_system_architect")
            assert root_result, "Root System Architect result missing during refinement - this should never happen"
            
            # Execute Tree Placement Planner
            task_analysis = garden_planner_result.get("task_analysis", {})
            environmental_analysis = env_result.get("analysis", {})
            data_architecture = root_result.get("data_architecture", {})
            
            tree_result = await workflow._execute_tree_placement_planner(
                task_analysis, environmental_analysis, data_architecture, f"{operation_id}_tree_recursion"
            )
            
            # Build final result
            final_output = {
                "task_analysis": task_analysis,
                "environmental_analysis": environmental_analysis,
                "data_architecture": data_architecture,
                "component_architecture": tree_result.get("component_architecture", {})
            }
            
            return {
                "status": "success",
                "user_request": user_request,
                "final_output": final_output,
                "agents": {
                    "garden_planner": garden_planner_result,
                    "environmental_analysis": env_result,
                    "root_system_architect": root_result,
                    "tree_placement_planner": tree_result
                }
            }
            
        except Exception as e:
            logger.error(f"Tree Placement Planner recursion failed: {e}")
            return {"status": "failed", "error": str(e)}

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