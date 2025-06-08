"""
Garden Planner Agent for phase one.
"""
import logging
from typing import Dict, Any
from datetime import datetime

from resources import EventQueue, StateManager, AgentContextManager, CacheManager, MetricsManager, ErrorHandler
from resources.monitoring import MemoryMonitor, MemoryThresholds, HealthTracker

from phase_one.agents.base import ReflectiveAgent
from phase_one.models.enums import DevelopmentState
from phase_one.models.refinement import AgentPromptConfig
from phase_one.monitoring.circuit_breakers import CircuitBreakerDefinition

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GardenPlannerAgent(ReflectiveAgent):
    """
    Garden Planner Agent - Responsible for initial task elaboration.
    """
    def __init__(self, agent_id: str, event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                memory_monitor: MemoryMonitor,
                 health_tracker: HealthTracker = None):
        
        # Define prompt configuration
        prompt_config = AgentPromptConfig(
            system_prompt_base_path="FFTT_system_prompts/phase_one/garden_planner_agent",
            reflection_prompt_name="task_reflection_prompt",
            refinement_prompt_name="task_elaboration_refinement_prompt",
            initial_prompt_name="initial_task_elaboration_prompt"
        )
        
        # Circuit breaker definitions removed - protection now at API level
        
        # Initialize base class with configuration
        super().__init__(
            agent_id, 
            event_queue, state_manager, context_manager, cache_manager, metrics_manager, error_handler, 
            memory_monitor,
            prompt_config,
            health_tracker
        )
        
        # Set initial state
        self.development_state = DevelopmentState.INITIALIZING
        self.validation_history = []
        
        # Register with memory monitor if available
        if self._memory_monitor:
            # Register specific thresholds for this agent
            self._memory_monitor.register_component(
                f"agent_{agent_id}",
                MemoryThresholds(
                    per_resource_max_mb=50,  # Max size of any resource
                    warning_percent=0.5,     # 50% warning threshold
                    critical_percent=0.8     # 80% critical threshold
                )
            )

    async def _process(self, task_prompt: str) -> Dict[str, Any]:
        """Process the task prompt with proper async handling and monitoring."""
        try:
            # Track memory usage of the task prompt
            await self.track_string_memory("task_prompt", task_prompt)
            
            # Process initial analysis with circuit breaker protection
            try:
                logger.info(f"Garden planner system_prompt_base_path: {self._prompt_config.system_prompt_base_path}")
                logger.info(f"Garden planner initial_prompt_name: {self._prompt_config.initial_prompt_name}")
                # Direct processing - circuit breaker protection now at API level
                initial_analysis = await self.process_with_validation(
                    conversation=f"Analyze task requirements: {task_prompt}",
                    system_prompt_info=(self._prompt_config.system_prompt_base_path, 
                                      self._prompt_config.initial_prompt_name)
                )
            except Exception as e:
                logger.warning(f"Analysis circuit open for agent {self.interface_id}, processing rejected")
                self.development_state = DevelopmentState.ERROR
                return {
                    "error": f"Analysis rejected: {str(e)}",
                    "status": "failure",
                    "agent_id": self.interface_id,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Use standardized reflection method
            reflection_result = await self.standard_reflect(
                initial_analysis,
                circuit_name="analysis"
            )
            
            # Check validation status from reflection
            if not (await self._get_validation_status(reflection_result)):
                self.development_state = DevelopmentState.REFINING
                return reflection_result
            
            # Report healthy status after successful processing
            await self._report_agent_health(
                custom_status="HEALTHY",
                description="Successfully processed task",
                metadata={
                    "development_state": "COMPLETE",
                    "validation_status": "passed"
                }
            )
            
            return initial_analysis
            
        except Exception as e:
            self.development_state = DevelopmentState.ERROR
            await self._report_agent_health(
                custom_status="CRITICAL",
                description=f"Processing error: {str(e)}",
                metadata={
                    "development_state": "ERROR",
                    "error": str(e)
                }
            )
            raise

    # Now only the specialized methods or overrides remain
    async def reflect(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to standardized reflection method."""
        return await self.standard_reflect(output, "analysis")

    async def refine(self, output: Dict[str, Any], refinement_guidance: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to standardized refinement method."""
        return await self.standard_refine(output, refinement_guidance, "analysis")

    async def _get_validation_status(self, reflection_result: Dict[str, Any]) -> bool:
        """Extract validation status from reflection result."""
        try:
            return reflection_result.get("reflection_results", {}).get("validation_status", {}).get("passed", False)
        except Exception:
            return False