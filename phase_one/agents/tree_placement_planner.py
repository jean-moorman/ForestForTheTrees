"""
Tree Placement Planner Agent for phase one.
"""
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

from resources import EventQueue, StateManager, AgentContextManager, CacheManager, MetricsManager, ErrorHandler
from resources.monitoring import MemoryMonitor, MemoryThresholds, HealthTracker

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

    def _extract_validation_status(self, reflection_result: Dict[str, Any]) -> bool:
        """Extract validation status from reflection result, handling multiple structure formats."""
        try:
            # Check if reflection_results exists
            reflection_results = reflection_result.get("reflection_results", {})
            if not reflection_results:
                logger.warning("No reflection_results found in reflection response")
                return False
            
            # Method 1: Standard validation_status structure (from base class fallbacks)
            validation_status = reflection_results.get("validation_status")
            if validation_status is not None:
                return validation_status.get("passed", False)
            
            # Method 2: Overall assessment structure (from earth agent and others)
            overall_assessment = reflection_results.get("overall_assessment", {})
            if overall_assessment:
                critical_improvements = overall_assessment.get("critical_improvements", [])
                if isinstance(critical_improvements, list):
                    # If there are critical improvements, validation failed
                    critical_count = sum(1 for item in critical_improvements 
                                       if isinstance(item, dict) and 
                                       item.get("importance") == "critical")
                    return critical_count == 0
                return True  # No critical improvements means validation passed
            
            # Method 3: Direct status check
            status = reflection_result.get("status")
            if status:
                return status == "success"
            
            # Method 4: Check for error indicators
            if reflection_result.get("error"):
                return False
            
            # Default: assume validation passed if no negative indicators
            logger.info("No clear validation indicators found, defaulting to passed")
            return True
            
        except Exception as e:
            logger.error(f"Error extracting validation status from reflection result: {str(e)}")
            # Log the structure for debugging
            logger.debug(f"Reflection result structure: {reflection_result}")
            return False

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
                
                # Direct processing - circuit breaker protection now at API level
                initial_design = await self.process_with_validation(
                    conversation=f"""Design component architecture based on:
                    Garden planner: {garden_planner_output}
                    Environment analysis: {environment_analysis_output}
                    Root system: {root_system_output}""",
                    system_prompt_info=(self._prompt_config.system_prompt_base_path, 
                                      self._prompt_config.initial_prompt_name)
                )
            except Exception as e:
                logger.warning(f"Component design processing error for agent {self.interface_id}: {str(e)}")
                self.development_state = DevelopmentState.ERROR
                
                await self._report_agent_health(
                    custom_status="CRITICAL",
                    description=f"Component design processing error: {str(e)}",
                    metadata={
                        "state": "ERROR",
                        "error": str(e)
                    }
                )
                
                return {
                    "error": f"Component design operation failed: {str(e)}",
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
            
            # Check validation status - handle multiple reflection result structures
            validation_passed = self._extract_validation_status(reflection_result)
            
            if not validation_passed:
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