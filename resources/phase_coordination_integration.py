"""
Forest For The Trees (FFTT) Phase Coordination Integration
----------------------------------------------------------
Provides the integration layer between the enhanced PhaseCoordinator and the phase implementation classes.
Implements transition handlers, coordinates nested phase execution, and manages phase lifecycle events.
"""
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Set, Callable, Awaitable, Tuple, Union

from resources.phase_coordinator import (
    PhaseCoordinator, 
    PhaseContext, 
    PhaseState, 
    PhaseType, 
    PhaseTransitionHandler, 
    NestedPhaseExecution
)
from resources import (
    StateManager,
    CacheManager,
    MetricsManager,
    EventQueue,
    ResourceEventTypes,
    AgentContextManager,
    SystemMonitor,
    MemoryMonitor
)
from resources.errors import ErrorHandler
from resources.monitoring import HealthStatus

logger = logging.getLogger(__name__)

class PhaseOneToTwoTransitionHandler(PhaseTransitionHandler):
    """Manages transitions from Phase One to Phase Two"""
    
    async def before_start(self, phase_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Called before Phase Two starts, can modify input data"""
        logger.info(f"Preparing transition from Phase One to Phase Two ({phase_id})")
        
        # Enhance input data with additional context from Phase One
        if "structural_components" in input_data:
            # Analyze dependencies to determine execution order
            components = input_data["structural_components"]
            dependency_analysis = self._analyze_component_dependencies(components)
            
            # Add dependency analysis to input data
            input_data["dependency_analysis"] = dependency_analysis
            
            # Add execution strategy based on dependency analysis
            input_data["execution_strategy"] = {
                "execution_order": dependency_analysis["execution_order"],
                "parallel_opportunities": dependency_analysis["parallel_groups"],
                "transition_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Enhanced Phase Two input with dependency analysis and execution strategy")
            
        return input_data
    
    async def after_completion(self, phase_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Called after Phase Two completes, can modify result data"""
        logger.info(f"Processing completion of Phase Two ({phase_id})")
        
        # Add metadata about the transition back to phase one
        result["transition_metadata"] = {
            "components_processed": result.get("components_processed", 0),
            "components_completed": result.get("components_completed", 0),
            "transition_completed_timestamp": datetime.now().isoformat()
        }
        
        return result
    
    async def on_failure(self, phase_id: str, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Called when Phase Two fails, can implement recovery or clean-up"""
        logger.error(f"Handling failure in Phase Two ({phase_id}): {str(error)}")
        
        # Create recovery data
        recovery_data = {
            "error": str(error),
            "error_type": type(error).__name__,
            "recovery_strategy": "fallback_to_phase_one",
            "recovery_timestamp": datetime.now().isoformat(),
            "context": {k: v for k, v in context.items() if k != "input_data"}  # Avoid large input data
        }
        
        return recovery_data
    
    def _analyze_component_dependencies(self, components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze component dependencies to determine execution order"""
        # Create dependency graph
        dependency_graph = {}
        for component in components:
            component_id = component.get("id", "")
            dependencies = component.get("dependencies", [])
            
            if component_id:
                dependency_graph[component_id] = dependencies
        
        # Determine execution order using topological sort
        execution_order = self._topological_sort(dependency_graph)
        
        # Identify groups that can be executed in parallel
        parallel_groups = []
        current_group = []
        
        for component_id in execution_order:
            # Check if component depends on anything in the current group
            dependencies = dependency_graph.get(component_id, [])
            if not any(dep in current_group for dep in dependencies):
                current_group.append(component_id)
            else:
                if current_group:
                    parallel_groups.append(current_group)
                current_group = [component_id]
        
        if current_group:
            parallel_groups.append(current_group)
        
        return {
            "execution_order": execution_order,
            "parallel_groups": parallel_groups
        }
    
    def _topological_sort(self, graph: Dict[str, List[str]]) -> List[str]:
        """Perform topological sort to determine execution order"""
        visited = set()
        result = []
        
        def dfs(node):
            visited.add(node)
            
            # Visit all dependencies first
            for dependency in graph.get(node, []):
                if dependency not in visited:
                    dfs(dependency)
            
            # After visiting all dependencies, add this node to result
            result.append(node)
        
        # Visit all nodes
        for node in graph:
            if node not in visited:
                dfs(node)
        
        # Reverse to get correct execution order (least dependent first)
        return list(reversed(result))

class PhaseTwoToThreeTransitionHandler(PhaseTransitionHandler):
    """Manages transitions from Phase Two to Phase Three"""
    
    async def before_start(self, phase_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Called before Phase Three starts, prepare feature data"""
        logger.info(f"Preparing transition from Phase Two to Phase Three ({phase_id})")
        
        # Enhance feature data for phase three
        if "features" in input_data:
            features = input_data["features"]
            
            # Add execution context for phase three
            input_data["execution_context"] = {
                "parent_phase_id": input_data.get("parent_phase_id", ""),
                "component_id": input_data.get("component_id", ""),
                "execution_id": input_data.get("execution_id", ""),
                "feature_count": len(features),
                "transition_timestamp": datetime.now().isoformat()
            }
            
            # Group features by dependencies for parallel execution
            feature_groups = self._group_features_by_dependencies(features)
            input_data["feature_groups"] = feature_groups
            
            logger.info(f"Enhanced Phase Three input with {len(feature_groups)} feature groups")
        
        return input_data
    
    async def after_completion(self, phase_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Called after Phase Three completes, process cultivation results"""
        logger.info(f"Processing completion of Phase Three ({phase_id})")
        
        # Add transition metadata to the result
        result["transition_metadata"] = {
            "features_processed": result.get("total_features", 0),
            "features_completed": len(result.get("feature_statuses", {})),
            "transition_completed_timestamp": datetime.now().isoformat()
        }
        
        return result
    
    async def on_failure(self, phase_id: str, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Called when Phase Three fails, implement recovery"""
        logger.error(f"Handling failure in Phase Three ({phase_id}): {str(error)}")
        
        # Get partial results if available
        partial_results = context.get("partial_results", {})
        
        # Create recovery data
        recovery_data = {
            "error": str(error),
            "error_type": type(error).__name__,
            "recovery_strategy": "use_partial_results",
            "partial_results": partial_results,
            "recovery_timestamp": datetime.now().isoformat()
        }
        
        return recovery_data
    
    def _group_features_by_dependencies(self, features: List[Dict[str, Any]]) -> List[List[str]]:
        """Group features by dependencies for parallel execution"""
        # Create dependency graph
        dependency_graph = {}
        for feature in features:
            feature_id = feature.get("id", "")
            dependencies = feature.get("dependencies", [])
            
            if feature_id:
                dependency_graph[feature_id] = dependencies
        
        # Identify groups that can be executed in parallel
        visited = set()
        groups = []
        
        # Start with features that have no dependencies
        no_dependencies = [f for f, deps in dependency_graph.items() if not deps]
        if no_dependencies:
            groups.append(no_dependencies)
            visited.update(no_dependencies)
        
        # Keep processing until all features are assigned to groups
        while len(visited) < len(dependency_graph):
            # Find features whose dependencies are all visited
            next_group = []
            for feature_id, dependencies in dependency_graph.items():
                if feature_id not in visited and all(dep in visited for dep in dependencies):
                    next_group.append(feature_id)
            
            # Add to groups and mark as visited
            if next_group:
                groups.append(next_group)
                visited.update(next_group)
            else:
                # Break if no progress can be made (circular dependencies)
                break
        
        return groups

class PhaseThreeToFourTransitionHandler(PhaseTransitionHandler):
    """Manages transitions from Phase Three to Phase Four"""
    
    async def before_start(self, phase_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Called before Phase Four starts, prepare feature code requirements"""
        logger.info(f"Preparing transition from Phase Three to Phase Four ({phase_id})")
        
        # Add compiler configuration
        input_data["compiler_config"] = {
            "max_iterations": input_data.get("max_iterations", 5),
            "timeout_seconds": 300,  # 5 minutes per compilation phase
            "strict_mode": input_data.get("strict_mode", False)
        }
        
        # Add execution context
        input_data["execution_context"] = {
            "parent_phase_id": input_data.get("parent_phase_id", ""),
            "feature_id": input_data.get("feature_id", ""),
            "transition_timestamp": datetime.now().isoformat()
        }
        
        return input_data
    
    async def after_completion(self, phase_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Called after Phase Four completes, process compilation results"""
        logger.info(f"Processing completion of Phase Four ({phase_id})")
        
        # Add transition metadata to the result
        result["transition_metadata"] = {
            "iterations_required": result.get("iterations", 0),
            "code_quality_score": result.get("analysis", {}).get("code_quality_score", 0),
            "transition_completed_timestamp": datetime.now().isoformat()
        }
        
        return result
    
    async def on_failure(self, phase_id: str, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Called when Phase Four fails, implement recovery"""
        logger.error(f"Handling failure in Phase Four ({phase_id}): {str(error)}")
        
        # Get the latest code if available
        latest_code = context.get("latest_code", "")
        
        # Create recovery data
        recovery_data = {
            "error": str(error),
            "error_type": type(error).__name__,
            "recovery_strategy": "fallback_to_initial_code" if not latest_code else "use_latest_code",
            "latest_code": latest_code,
            "recovery_timestamp": datetime.now().isoformat()
        }
        
        return recovery_data
    
    async def on_pause(self, phase_id: str, reason: str, context: Dict[str, Any]) -> None:
        """Called when Phase Four is paused"""
        logger.info(f"Phase Four paused ({phase_id}): {reason}")
        
        # Could implement checkpoint saving here

class PhaseCoordinationIntegration:
    """
    Integration layer between the PhaseCoordinator and phase implementation classes.
    Provides specific handlers for each phase transition.
    """
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None,
                 system_monitor: Optional[SystemMonitor] = None):
        """Initialize the phase coordination integration."""
        # Store resource manager references
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._context_manager = context_manager
        self._cache_manager = cache_manager
        self._metrics_manager = metrics_manager
        self._error_handler = error_handler
        self._memory_monitor = memory_monitor
        self._system_monitor = system_monitor
        
        # Create the phase coordinator
        self._phase_coordinator = PhaseCoordinator(
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor,
            system_monitor
        )
        
        # Register transition handlers
        self._register_transition_handlers()
        
        # Track integration state
        self._initialized = False
        logger.info("Phase coordination integration created")
    
    async def initialize(self) -> None:
        """Initialize the integration layer."""
        if self._initialized:
            return
            
        # Start the phase coordinator
        await self._phase_coordinator.start()
        
        # Register with system monitor if available
        if self._system_monitor:
            await self._system_monitor.register_component(
                "phase_coordination_integration",
                {
                    "type": "integration",
                    "description": "Phase coordination integration layer",
                    "initialized_at": datetime.now().isoformat()
                }
            )
        
        self._initialized = True
        logger.info("Phase coordination integration initialized")
    
    def _register_transition_handlers(self) -> None:
        """Register transition handlers for phase transitions."""
        # Create handler instances
        phase_one_to_two_handler = PhaseOneToTwoTransitionHandler()
        phase_two_to_three_handler = PhaseTwoToThreeTransitionHandler()
        phase_three_to_four_handler = PhaseThreeToFourTransitionHandler()
        
        # Create transition handler mapping
        self._transition_handlers = {
            (PhaseType.ONE, PhaseType.TWO): phase_one_to_two_handler,
            (PhaseType.TWO, PhaseType.THREE): phase_two_to_three_handler,
            (PhaseType.THREE, PhaseType.FOUR): phase_three_to_four_handler
        }
        
        logger.info("Registered phase transition handlers")
    
    async def get_handler_for_transition(self, 
                                       source_phase_type: PhaseType, 
                                       target_phase_type: PhaseType) -> Optional[PhaseTransitionHandler]:
        """Get the appropriate handler for a phase transition."""
        return self._transition_handlers.get((source_phase_type, target_phase_type))
    
    async def initialize_phase_one(self, config: Dict[str, Any]) -> str:
        """Initialize Phase One with the coordinator."""
        phase_id = f"phase_one_{int(datetime.now().timestamp())}"
        
        # Initialize Phase One in the coordinator
        await self._phase_coordinator.initialize_phase(
            phase_id,
            PhaseType.ONE,
            config
        )
        
        logger.info(f"Initialized Phase One with ID: {phase_id}")
        return phase_id
    
    async def initialize_phase_two(self, config: Dict[str, Any], parent_phase_id: Optional[str] = None) -> str:
        """Initialize Phase Two with the coordinator."""
        phase_id = f"phase_two_{int(datetime.now().timestamp())}"
        
        # Initialize Phase Two in the coordinator
        await self._phase_coordinator.initialize_phase(
            phase_id,
            PhaseType.TWO,
            config,
            parent_phase_id
        )
        
        logger.info(f"Initialized Phase Two with ID: {phase_id}, parent: {parent_phase_id or 'none'}")
        return phase_id
    
    async def initialize_phase_three(self, config: Dict[str, Any], parent_phase_id: str) -> str:
        """Initialize Phase Three with the coordinator."""
        phase_id = f"phase_three_{int(datetime.now().timestamp())}"
        
        # Initialize Phase Three in the coordinator
        await self._phase_coordinator.initialize_phase(
            phase_id,
            PhaseType.THREE,
            config,
            parent_phase_id
        )
        
        logger.info(f"Initialized Phase Three with ID: {phase_id}, parent: {parent_phase_id}")
        return phase_id
    
    async def initialize_phase_four(self, config: Dict[str, Any], parent_phase_id: str) -> str:
        """Initialize Phase Four with the coordinator."""
        phase_id = f"phase_four_{int(datetime.now().timestamp())}"
        
        # Initialize Phase Four in the coordinator
        await self._phase_coordinator.initialize_phase(
            phase_id,
            PhaseType.FOUR,
            config,
            parent_phase_id
        )
        
        logger.info(f"Initialized Phase Four with ID: {phase_id}, parent: {parent_phase_id}")
        return phase_id
    
    async def initialize_phase_zero(self, config: Dict[str, Any]) -> str:
        """Initialize Phase Zero with the coordinator."""
        phase_id = f"phase_zero_{int(datetime.now().timestamp())}"
        
        # Initialize Phase Zero in the coordinator
        await self._phase_coordinator.initialize_phase(
            phase_id,
            PhaseType.ZERO,
            config
        )
        
        logger.info(f"Initialized Phase Zero with ID: {phase_id}")
        return phase_id
    
    async def start_phase(self, phase_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Start execution of a phase."""
        # Get phase context
        phase_status = await self._phase_coordinator.get_phase_status(phase_id)
        if "error" in phase_status:
            logger.error(f"Cannot start unknown phase: {phase_id}")
            return {"error": f"Phase {phase_id} not found", "status": "error"}
        
        # Start the phase
        result = await self._phase_coordinator.start_phase(phase_id, input_data)
        
        return result
    
    async def coordinate_nested_execution(self, 
                                        parent_phase_id: str, 
                                        child_phase_type: PhaseType, 
                                        input_data: Dict[str, Any],
                                        config: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate nested phase execution."""
        try:
            # Get parent phase context
            parent_status = await self._phase_coordinator.get_phase_status(parent_phase_id)
            if "error" in parent_status:
                logger.error(f"Cannot start nested execution: parent phase {parent_phase_id} not found")
                return {"error": f"Parent phase {parent_phase_id} not found", "status": "error"}
            
            # Determine initialization method based on child phase type
            if child_phase_type == PhaseType.TWO:
                child_phase_id = await self.initialize_phase_two(config, parent_phase_id)
            elif child_phase_type == PhaseType.THREE:
                child_phase_id = await self.initialize_phase_three(config, parent_phase_id)
            elif child_phase_type == PhaseType.FOUR:
                child_phase_id = await self.initialize_phase_four(config, parent_phase_id)
            elif child_phase_type == PhaseType.ZERO:
                child_phase_id = await self.initialize_phase_zero(config)
            else:
                logger.error(f"Unsupported child phase type: {child_phase_type}")
                return {"error": f"Unsupported child phase type: {child_phase_type}", "status": "error"}
            
            # Add execution context to input data
            enhanced_input = {
                **input_data,
                "parent_phase_id": parent_phase_id,
                "execution_id": f"{parent_phase_id}_to_{child_phase_id}_{int(datetime.now().timestamp())}"
            }
            
            # Use the coordinator to manage the nested execution
            result = await self._phase_coordinator.coordinate_nested_execution(
                parent_phase_id,
                child_phase_id,
                enhanced_input
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error coordinating nested execution: {str(e)}")
            return {
                "error": f"Nested execution failed: {str(e)}",
                "status": "error",
                "parent_phase_id": parent_phase_id,
                "child_phase_type": child_phase_type.value
            }
    
    async def get_phase_status(self, phase_id: str) -> Dict[str, Any]:
        """Get the status of a phase."""
        return await self._phase_coordinator.get_phase_status(phase_id)
    
    async def get_phase_health(self) -> Dict[str, Any]:
        """Get health status of all phases."""
        return await self._phase_coordinator.get_phase_health()
    
    async def create_checkpoint(self, phase_id: str) -> str:
        """Create a checkpoint for a phase."""
        return await self._phase_coordinator.create_checkpoint(phase_id)
    
    async def rollback_to_checkpoint(self, checkpoint_id: str) -> bool:
        """Roll back to a checkpoint."""
        return await self._phase_coordinator.rollback_to_checkpoint(checkpoint_id)
    
    async def pause_phase(self, phase_id: str, reason: str) -> bool:
        """Pause a phase execution."""
        return await self._phase_coordinator.pause_phase(phase_id, reason)
    
    async def resume_phase(self, phase_id: str) -> bool:
        """Resume a paused phase."""
        return await self._phase_coordinator.resume_phase(phase_id)
    
    async def abort_phase(self, phase_id: str, reason: str) -> bool:
        """Abort a running phase."""
        return await self._phase_coordinator.abort_phase(phase_id, reason)
    
    async def shutdown(self) -> None:
        """Shutdown the integration layer."""
        if not self._initialized:
            return
            
        # Stop the phase coordinator
        await self._phase_coordinator.stop()
        
        self._initialized = False
        logger.info("Phase coordination integration shutdown")