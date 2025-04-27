"""
Environmental Analysis Agent for phase one.
"""
import logging
from typing import Dict, Any
from datetime import datetime

from resources import EventQueue, StateManager, AgentContextManager, CacheManager, MetricsManager, ErrorHandler
from resources.monitoring import MemoryMonitor, MemoryThresholds, HealthTracker, CircuitOpenError

from phase_one.agents.base import ReflectiveAgent
from phase_one.models.enums import DevelopmentState
from phase_one.models.refinement import AgentPromptConfig
from phase_one.monitoring.circuit_breakers import CircuitBreakerDefinition

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnvironmentalAnalysisAgent(ReflectiveAgent):
    """
    Environmental Analysis Agent - Responsible for analyzing requirements.
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
            system_prompt_base_path="FFTT_system_prompts/phase_one/garden_environmental_analysis_agent",
            reflection_prompt_name="core_requirements_reflection_prompt",
            refinement_prompt_name="core_requirements_refinement_prompt",
            initial_prompt_name="initial_core_requirements_prompt"
        )
        
        # Define circuit breakers
        circuit_breakers = [
            CircuitBreakerDefinition(
                name="analysis",
                failure_threshold=3,
                recovery_timeout=30,
                failure_window=120
            )
        ]
        
        # Initialize base class with configuration
        super().__init__(
            agent_id, 
            event_queue, state_manager, context_manager, cache_manager, metrics_manager, error_handler, 
            memory_monitor,
            prompt_config,
            circuit_breakers,
            health_tracker
        )
        
        # Set initial state
        self.development_state = DevelopmentState.INITIALIZING
        
        # Register with memory monitor if available
        if self._memory_monitor:
            self._memory_monitor.register_component(
                f"agent_{agent_id}",
                MemoryThresholds(
                    per_resource_max_mb=70,  # Environment data could be larger
                    warning_percent=0.5,
                    critical_percent=0.8
                )
            )

    async def _process(self, garden_planner_output: Dict[str, Any]) -> Dict[str, Any]:
        """Process garden planner output with monitoring."""
        try:
            # Track memory usage of input data
            await self.track_dict_memory("garden_planner_input", garden_planner_output)
            
            # Update health status to processing
            await self._report_agent_health(
                description="Processing environment analysis",
                metadata={"state": "ANALYZING"}
            )
            
            # Process analysis with circuit breaker protection
            try:
                self.development_state = DevelopmentState.ANALYZING
                
                initial_analysis = await self.get_circuit_breaker("analysis").execute(
                    lambda: self.process_with_validation(
                        conversation=f"Analyze environment based on: {garden_planner_output}",
                        system_prompt_info=(self._prompt_config.system_prompt_base_path, 
                                          self._prompt_config.initial_prompt_name)
                    )
                )
            except CircuitOpenError:
                logger.warning(f"Analysis circuit open for agent {self.interface_id}, processing rejected")
                self.development_state = DevelopmentState.ERROR
                return {
                    "error": "Analysis rejected due to circuit breaker open",
                    "status": "failure",
                    "agent_id": self.interface_id,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Track memory usage of analysis result
            await self.track_dict_memory("analysis_result", initial_analysis)
            
            # Use standardized reflection method
            reflection_result = await self.standard_reflect(
                initial_analysis,
                circuit_name="analysis"
            )
            
            # Check validation status
            if not reflection_result["reflection_results"]["validation_status"]["passed"]:
                self.development_state = DevelopmentState.REFINING
                
                # Report degraded health
                await self._report_agent_health(
                    custom_status="DEGRADED",
                    description="Validation failed, entering refinement",
                    metadata={
                        "state": "REFINING",
                        "validation": "failed"
                    }
                )
                
                return reflection_result
            
            # Set state to complete and report success
            self.development_state = DevelopmentState.COMPLETE
            
            await self._report_agent_health(
                description="Environment analysis completed successfully",
                metadata={"state": "COMPLETE"}
            )
            
            return initial_analysis
            
        except Exception as e:
            self.development_state = DevelopmentState.ERROR
            
            await self._report_agent_health(
                custom_status="CRITICAL",
                description=f"Processing error: {str(e)}",
                metadata={
                    "state": "ERROR",
                    "error": str(e)
                }
            )
            
            raise

    async def reflect(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to standardized reflection method."""
        return await self.standard_reflect(output, "analysis")

    async def refine(self, output: Dict[str, Any], refinement_guidance: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to standardized refinement method."""
        return await self.standard_refine(output, refinement_guidance, "analysis")