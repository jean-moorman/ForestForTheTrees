"""
Tree Placement Planner Agent for phase one.
"""
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

from resources import EventQueue, StateManager, AgentContextManager, CacheManager, MetricsManager, ErrorHandler
from resources.monitoring import MemoryMonitor, MemoryThresholds, HealthTracker, CircuitOpenError

from phase_one.agents.base import ReflectiveAgent
from phase_one.models.enums import DevelopmentState
from phase_one.models.refinement import AgentPromptConfig
from phase_one.monitoring.circuit_breakers import CircuitBreakerDefinition

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TreePlacementPlannerAgent(ReflectiveAgent):
    """
    Tree Placement Planner Agent - Responsible for structural component architecture.
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
            system_prompt_base_path="FFTT_system_prompts/phase_one/tree_placement_planner_agent",
            reflection_prompt_name="structural_component_reflection_prompt",
            refinement_prompt_name="structural_component_refinement_prompt",
            initial_prompt_name="initial_structural_components_prompt"
        )
        
        # Define circuit breakers
        circuit_breakers = [
            CircuitBreakerDefinition(
                name="component_design",
                failure_threshold=4,      # More failures allowed for complex component design
                recovery_timeout=40,
                failure_window=180
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
                    per_resource_max_mb=120,  # Component diagrams can be larger
                    warning_percent=0.6,
                    critical_percent=0.85
                )
            )
            
        # Initialize performance tracking
        self._processing_times = []
        self._component_counts = []

    def _estimate_component_count(self, garden_planner_output: Dict[str, Any], 
                               environment_analysis_output: Dict[str, Any]) -> int:
        """Estimate the number of components based on requirements."""
        # Simple estimation logic - in a real scenario, this would be more sophisticated
        try:
            # Check for requirements list in garden planner output
            requirements = garden_planner_output.get("requirements", [])
            if isinstance(requirements, list):
                # Roughly estimate 1 component per 2-3 requirements
                return max(3, len(requirements) // 2)
            
            # Fallback to a reasonable minimum
            return 5
        except Exception:
            # Safe fallback
            return 5

    async def _process(self, garden_planner_output: Dict[str, Any],
                      environment_analysis_output: Dict[str, Any],
                      root_system_output: Dict[str, Any]) -> Dict[str, Any]:
        """Process component architecture design with monitoring."""
        processing_start = datetime.now()
        
        try:
            # Track memory usage of input data
            await self.track_dict_memory("garden_planner_input", garden_planner_output)
            await self.track_dict_memory("environment_analysis_input", environment_analysis_output)
            await self.track_dict_memory("root_system_input", root_system_output)
            
            # Calculate total input size for monitoring
            planner_size_mb = len(json.dumps(garden_planner_output)) / (1024 * 1024)
            env_size_mb = len(json.dumps(environment_analysis_output)) / (1024 * 1024)
            root_size_mb = len(json.dumps(root_system_output)) / (1024 * 1024)
            await self.track_memory_usage("total_input", planner_size_mb + env_size_mb + root_size_mb)
            
            # Count expected components from requirements (estimated)
            estimated_components = self._estimate_component_count(
                garden_planner_output, 
                environment_analysis_output
            )
            
            # Update health status to designing
            await self._report_agent_health(
                description="Designing component architecture",
                metadata={
                    "state": "DESIGNING",
                    "input_sources": ["garden_planner", "environment_analysis", "root_system"],
                    "estimated_components": estimated_components
                }
            )
            
            # Design components with circuit breaker protection
            try:
                self.development_state = DevelopmentState.DESIGNING
                
                initial_design = await self.get_circuit_breaker("component_design").execute(
                    lambda: self.process_with_validation(
                        conversation=f"""Design component architecture based on:
                        Garden planner: {garden_planner_output}
                        Environment analysis: {environment_analysis_output}
                        Root system: {root_system_output}""",
                        system_prompt_info=(self._prompt_config.system_prompt_base_path, 
                                          self._prompt_config.initial_prompt_name)
                    )
                )
            except CircuitOpenError:
                logger.warning(f"Component design circuit open for agent {self.interface_id}, processing rejected")
                self.development_state = DevelopmentState.ERROR
                
                await self._report_agent_health(
                    custom_status="CRITICAL",
                    description="Component design rejected due to circuit breaker open",
                    metadata={
                        "state": "ERROR",
                        "circuit": "component_design_circuit",
                        "circuit_state": "OPEN"
                    }
                )
                
                return {
                    "error": "Component design rejected due to circuit breaker open",
                    "status": "failure",
                    "agent_id": self.interface_id,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Track memory usage of design result
            await self.track_dict_memory("initial_design", initial_design)
            
            # Calculate actual component count
            actual_components = 0
            if isinstance(initial_design, dict) and "component_architecture" in initial_design:
                components = initial_design["component_architecture"].get("components", [])
                actual_components = len(components)
                
                # Log the component count for monitoring
                self._component_counts.append(actual_components)
                logger.info(f"Designed {actual_components} components (estimated: {estimated_components})")
            
            # Use standardized reflection method
            self.development_state = DevelopmentState.VALIDATING
            reflection_result = await self.standard_reflect(
                initial_design,
                circuit_name="component_design"
            )
            
            # Check validation status
            if not reflection_result["reflection_results"]["validation_status"]["passed"]:
                self.development_state = DevelopmentState.REFINING
                
                await self._report_agent_health(
                    custom_status="DEGRADED",
                    description="Validation failed, component design requires refinement",
                    metadata={
                        "state": "REFINING",
                        "validation": "failed",
                        "actual_components": actual_components
                    }
                )
                
                return reflection_result
            
            # Track processing time
            processing_time = (datetime.now() - processing_start).total_seconds()
            self._processing_times.append(processing_time)
            
            # Set state to complete
            self.development_state = DevelopmentState.COMPLETE
            
            # Report success metrics
            await self._metrics_manager.record_metric(
                f"agent:{self.interface_id}:components_created",
                actual_components,
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "processing_time": processing_time
                }
            )
            
            await self._report_agent_health(
                description="Component architecture design completed successfully",
                metadata={
                    "state": "COMPLETE",
                    "processing_time": processing_time,
                    "components": actual_components
                }
            )
            
            return initial_design
            
        except Exception as e:
            self.development_state = DevelopmentState.ERROR
            
            processing_time = (datetime.now() - processing_start).total_seconds()
            
            await self._report_agent_health(
                custom_status="CRITICAL",
                description=f"Component design error: {str(e)}",
                metadata={
                    "state": "ERROR",
                    "error": str(e),
                    "processing_time": processing_time
                }
            )
            
            # Record error metric
            await self._metrics_manager.record_metric(
                f"agent:{self.interface_id}:design_errors",
                1.0,
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                    "processing_time": processing_time
                }
            )
            
            raise

    async def reflect(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to standardized reflection method."""
        return await self.standard_reflect(output, "component_design")

    async def refine(self, output: Dict[str, Any], refinement_guidance: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to standardized refinement method."""
        return await self.standard_refine(output, refinement_guidance, "component_design")
        
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics."""
        avg_processing_time = 0
        if self._processing_times:
            avg_processing_time = sum(self._processing_times) / len(self._processing_times)
            
        avg_component_count = 0
        if self._component_counts:
            avg_component_count = sum(self._component_counts) / len(self._component_counts)
            
        return {
            "agent_id": self.interface_id,
            "avg_processing_time": avg_processing_time,
            "avg_component_count": avg_component_count,
            "total_designs": len(self._processing_times),
            "timestamp": datetime.now().isoformat()
        }