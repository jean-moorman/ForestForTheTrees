"""
Root System Architect Agent for phase one.
"""
import json
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

class RootSystemArchitectAgent(ReflectiveAgent):
    """
    Root System Architect Agent - Responsible for data flow architecture.
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
            system_prompt_base_path="FFTT_system_prompts/phase_one/garden_root_system_agent",
            reflection_prompt_name="core_data_flow_reflection_prompt",
            refinement_prompt_name="core_data_flow_refinement_prompt",
            initial_prompt_name="initial_core_data_flow_prompt"
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
        
        # Register with memory monitor if available
        if self._memory_monitor:
            self._memory_monitor.register_component(
                f"agent_{agent_id}",
                MemoryThresholds(
                    per_resource_max_mb=100,  # Architecture diagrams can be larger
                    warning_percent=0.6,
                    critical_percent=0.85
                )
            )

    async def _process(self, garden_planner_output: Dict[str, Any],
                     environment_analysis_output: Dict[str, Any]) -> Dict[str, Any]:
        """Process architecture design with monitoring."""
        try:
            # Track memory usage of input data
            await self.track_dict_memory("garden_planner_input", garden_planner_output)
            await self.track_dict_memory("environment_analysis_input", environment_analysis_output)
            
            # Calculate total input size for monitoring
            planner_size_mb = len(json.dumps(garden_planner_output)) / (1024 * 1024)
            env_size_mb = len(json.dumps(environment_analysis_output)) / (1024 * 1024)
            await self.track_memory_usage("total_input", planner_size_mb + env_size_mb)
            
            # Update health status to designing
            await self._report_agent_health(
                description="Designing data architecture",
                metadata={
                    "state": "DESIGNING",
                    "input_sources": ["garden_planner", "environment_analysis"]
                }
            )
            
            # Design architecture with circuit breaker protection
            try:
                self.development_state = DevelopmentState.DESIGNING
                
                # Direct processing - circuit breaker protection now at API level
                initial_design = await self.process_with_validation(
                    conversation=f"""Design data architecture based on:
                    Garden planner: {garden_planner_output}
                    Environment analysis: {environment_analysis_output}""",
                    system_prompt_info=(self._prompt_config.system_prompt_base_path, 
                                      self._prompt_config.initial_prompt_name)
                )
            except Exception as e:
                logger.warning(f"Design processing error for agent {self.interface_id}: {str(e)}")
                self.development_state = DevelopmentState.ERROR
                
                await self._report_agent_health(
                    custom_status="CRITICAL",
                    description=f"Design processing error: {str(e)}",
                    metadata={
                        "state": "ERROR",
                        "error": str(e)
                    }
                )
                
                return {
                    "error": f"Design operation failed: {str(e)}",
                    "status": "failure",
                    "agent_id": self.interface_id,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Track memory usage of design result
            await self.track_dict_memory("initial_design", initial_design)
            
            # Use standardized reflection method
            self.development_state = DevelopmentState.VALIDATING
            reflection_result = await self.standard_reflect(
                initial_design,
                circuit_name="design"
            )
            
            # Check validation status (handle both error and success cases)
            reflection_data = reflection_result.get("reflection_results", {})
            validation_status = reflection_data.get("validation_status", {})
            
            # If there's an explicit validation failure or error status
            if (validation_status.get("passed") is False or 
                reflection_result.get("status") == "failure" or
                "error" in reflection_result):
                self.development_state = DevelopmentState.REFINING
                
                await self._report_agent_health(
                    custom_status="DEGRADED",
                    description="Validation failed, design requires refinement",
                    metadata={
                        "state": "REFINING",
                        "validation": "failed"
                    }
                )
                
                return reflection_result
            
            # Set state to complete
            self.development_state = DevelopmentState.COMPLETE
            
            # Record metrics for successful design
            await self._metrics_manager.record_metric(
                f"agent:{self.interface_id}:design_completed",
                1.0,
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "validation": "passed"
                }
            )
            
            await self._report_agent_health(
                description="Data architecture design completed successfully",
                metadata={"state": "COMPLETE"}
            )
            
            return initial_design
            
        except Exception as e:
            self.development_state = DevelopmentState.ERROR
            
            await self._report_agent_health(
                custom_status="CRITICAL",
                description=f"Design error: {str(e)}",
                metadata={
                    "state": "ERROR",
                    "error": str(e)
                }
            )
            
            # Record error metric
            await self._metrics_manager.record_metric(
                f"agent:{self.interface_id}:design_errors",
                1.0,
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e)
                }
            )
            
            raise

    async def reflect(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Specialized reflection method that measures performance."""
        reflection_start = datetime.now()
        
        result = await self.standard_reflect(output, "design")
        
        # Track reflection time
        reflection_time = (datetime.now() - reflection_start).total_seconds()
        await self._metrics_manager.record_metric(
            f"agent:{self.interface_id}:reflection_time",
            reflection_time,
            metadata={"success": True}
        )
        
        return result

    async def refine(self, output: Dict[str, Any], refinement_guidance: Dict[str, Any]) -> Dict[str, Any]:
        """Specialized refinement method that measures performance."""
        refinement_start = datetime.now()
        
        result = await self.standard_refine(output, refinement_guidance, "design")
        
        # Track refinement time
        refinement_time = (datetime.now() - refinement_start).total_seconds()
        await self._metrics_manager.record_metric(
            f"agent:{self.interface_id}:refinement_time",
            refinement_time,
            metadata={"success": True}
        )
        
        return result