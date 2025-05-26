import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Set

from resources import (
    ResourceType, 
    EventQueue, 
    StateManager, 
    AgentContextManager, 
    CacheManager, 
    MetricsManager, 
    MemoryMonitor, 
    SystemMonitor,
    PhaseCoordinationIntegration,
    PhaseType
)
# Import ErrorHandler directly from resources.__init__
from resources import ErrorHandler
from phase_zero import PhaseZeroOrchestrator
from phase_three import PhaseThreeInterface
from component import Component

from phase_two.models import ComponentDevelopmentContext, ComponentDevelopmentState
from phase_two.agents.test_creation import ComponentTestCreationAgent
from phase_two.agents.implementation import ComponentImplementationAgent
from phase_two.agents.integration_test import IntegrationTestAgent
from phase_two.agents.system_test import SystemTestAgent
from phase_two.agents.deployment_test import DeploymentTestAgent
from phase_two.test_execution import TestExecutor
from phase_two.component_development import ComponentDeveloper
# Import the PhaseTwoCoordinator from the coordination.py file 
# (not the coordination/ package directory)
import importlib.util
import sys
import os

# Get the path to the coordination.py file specifically
coordination_file_path = os.path.join(os.path.dirname(__file__), 'coordination.py')
spec = importlib.util.spec_from_file_location("phase_two_coordination", coordination_file_path)
coordination_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coordination_module)
PhaseTwoCoordinator = coordination_module.PhaseTwoCoordinator
from phase_two.utils import sort_components_by_dependencies

logger = logging.getLogger(__name__)

class PhaseTwo:
    """Manages the systematic development process from components to deployment"""
    
    def __init__(self, 
                event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                phase_zero: PhaseZeroOrchestrator,
                phase_three: PhaseThreeInterface,
                memory_monitor: Optional[MemoryMonitor] = None,
                system_monitor: Optional[SystemMonitor] = None,
                phase_coordination: Optional[PhaseCoordinationIntegration] = None):
        # Initialize resource managers
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._context_manager = context_manager
        self._cache_manager = cache_manager
        self._metrics_manager = metrics_manager
        self._error_handler = error_handler
        
        # References to other phases
        self._phase_zero = phase_zero
        self._phase_three = phase_three
        
        # Monitoring components
        self._memory_monitor = memory_monitor
        self._system_monitor = system_monitor
        
        # Phase coordination
        if phase_coordination:
            self._phase_coordination = phase_coordination
        else:
            # Create phase coordination if not provided
            self._coordinator = PhaseTwoCoordinator(
                event_queue,
                state_manager,
                context_manager,
                cache_manager,
                metrics_manager,
                error_handler,
                memory_monitor,
                system_monitor
            )
            self._phase_coordination = self._coordinator.get_coordinator()
        
        # Initialize agents
        self._test_agent = ComponentTestCreationAgent(
            event_queue, state_manager, context_manager, 
            cache_manager, metrics_manager, error_handler, memory_monitor
        )
        self._implementation_agent = ComponentImplementationAgent(
            event_queue, state_manager, context_manager, 
            cache_manager, metrics_manager, error_handler, memory_monitor
        )
        self._integration_agent = IntegrationTestAgent(
            event_queue, state_manager, context_manager, 
            cache_manager, metrics_manager, error_handler, memory_monitor
        )
        self._system_test_agent = SystemTestAgent(
            event_queue, state_manager, context_manager, 
            cache_manager, metrics_manager, error_handler, memory_monitor
        )
        self._deployment_agent = DeploymentTestAgent(
            event_queue, state_manager, context_manager, 
            cache_manager, metrics_manager, error_handler, memory_monitor
        )
        
        # Initialize test executor
        self._test_executor = TestExecutor(metrics_manager)
        
        # Create component developer
        self._component_developer = ComponentDeveloper(
            state_manager,
            metrics_manager,
            self._test_agent,
            self._implementation_agent,
            self._integration_agent,
            self._test_executor,
            phase_three
        )
        
        # Track development contexts
        self._development_contexts: Dict[str, ComponentDevelopmentContext] = {}
        self._completed_components: List[Dict[str, Any]] = []
        
        # Track processing state
        self._is_processing = False
        self._start_time = None
        self._phase_id = None
        
        # Register with system monitor if available
        if self._system_monitor:
            asyncio.create_task(
                self._system_monitor.register_component("phase_two", {
                    "type": "phase",
                    "description": "Phase Two - Systematic Development",
                    "depends_on": ["phase_one", "phase_three"]
                })
            )
            
        logger.info("Phase Two initialized")
    
    async def process_structural_components(self, 
                                        structural_components: List[Dict[str, Any]],
                                        system_requirements: Dict[str, Any],
                                        operation_id: str,
                                        parent_phase_id: Optional[str] = None) -> Dict[str, Any]:
        """Process the structural components from Phase One and develop the system."""
        if self._is_processing:
            logger.warning("Phase Two is already processing components")
            return {
                "status": "already_processing",
                "message": "Phase Two is already processing components",
                "operation_id": operation_id
            }
            
        self._is_processing = True
        self._start_time = time.time()
        
        try:
            # Initialize phase with the coordinator if we don't have a phase ID yet
            if not self._phase_id:
                config = {
                    "operation_id": operation_id,
                    "component_count": len(structural_components),
                    "handlers": ["phase_one_to_two", "phase_two_to_three"]
                }
                
                if hasattr(self, '_coordinator'):
                    self._phase_id = await self._coordinator.initialize_phase(config, parent_phase_id)
                else:
                    self._phase_id = await self._phase_coordination.initialize_phase_two(config, parent_phase_id)
                
                logger.info(f"Phase Two initialized with coordination ID: {self._phase_id}")
            
            # Record start of phase two
            await self._metrics_manager.record_metric(
                "phase_two:start",
                1.0,
                metadata={
                    "operation_id": operation_id,
                    "component_count": len(structural_components),
                    "phase_id": self._phase_id
                }
            )
            
            # Sort components by dependencies to determine processing order
            sorted_components = sort_components_by_dependencies(structural_components)
            
            logger.info(f"Starting component development process for {len(sorted_components)} components")
            
            # Process components in series, from most fundamental to least
            for component_data in sorted_components:
                component_id = component_data.get("id", f"component_{int(time.time())}")
                component_name = component_data.get("name", "unnamed_component")
                
                logger.info(f"Starting development for component {component_name} ({component_id})")
                
                # Create development context
                context = ComponentDevelopmentContext(
                    component_id=component_id,
                    component_name=component_name,
                    description=component_data.get("description", ""),
                    requirements=component_data,
                    dependencies=set(component_data.get("dependencies", []))
                )
                self._development_contexts[component_id] = context
                
                # Store context in state manager
                await self._state_manager.set_state(
                    f"component:development:{component_id}",
                    {
                        "component_id": component_id,
                        "component_name": component_name,
                        "state": context.state.name,
                        "timestamp": datetime.now().isoformat()
                    },
                    ResourceType.STATE
                )
                
                # Configure component developer with coordination info
                self._component_developer._phase_coordination = self._phase_coordination
                self._component_developer._phase_id = self._phase_id
                
                # Develop the component
                component_result = await self._component_developer.develop_component(
                    component_id, 
                    context, 
                    self._development_contexts
                )
                
                # Handle development result
                if "error" in component_result:
                    logger.error(f"Component development failed for {component_id}: {component_result['error']}")
                else:
                    logger.info(f"Component development completed for {component_name}")
                    self._completed_components.append(component_result)
            
            # Create system tests once all components are implemented
            if self._completed_components:
                system_test_result = await self._system_test_agent.create_system_tests(
                    self._completed_components,
                    system_requirements,
                    f"system_tests_{operation_id}"
                )
                
                # Run system tests (simulated)
                system_test_execution = await self._test_executor.run_system_tests(system_test_result)
                
                # Create deployment tests
                deployment_test_result = await self._deployment_agent.create_deployment_tests(
                    self._completed_components,
                    system_requirements,
                    f"deployment_tests_{operation_id}"
                )
                
                # Run deployment tests (simulated)
                deployment_execution = await self._test_executor.run_deployment_tests(deployment_test_result)
            else:
                system_test_execution = {"status": "skipped", "reason": "No components completed"}
                deployment_execution = {"status": "skipped", "reason": "No components completed"}
            
            # Prepare final result
            execution_time = time.time() - self._start_time
            result = {
                "status": "completed",
                "operation_id": operation_id,
                "components_processed": len(structural_components),
                "components_completed": len(self._completed_components),
                "execution_time_seconds": execution_time,
                "system_test_results": system_test_execution,
                "deployment_results": deployment_execution,
                "timestamp": datetime.now().isoformat()
            }
            
            # Record completion metric
            await self._metrics_manager.record_metric(
                "phase_two:complete",
                1.0,
                metadata={
                    "operation_id": operation_id,
                    "components_completed": len(self._completed_components),
                    "execution_time": execution_time
                }
            )
            
            logger.info(f"Phase Two completed processing {len(structural_components)} components in {execution_time:.2f} seconds")
            
            # If we have a phase ID and the coordinator is available, update phase state
            if self._phase_id:
                try:
                    if hasattr(self, '_coordinator'):
                        # Create checkpoint for completion state
                        checkpoint_id = await self._coordinator.create_checkpoint(self._phase_id)
                    else:
                        # Create checkpoint for completion state
                        checkpoint_id = await self._phase_coordination.create_checkpoint(self._phase_id)
                    
                    logger.info(f"Created completion checkpoint {checkpoint_id} for phase {self._phase_id}")
                except Exception as coord_error:
                    logger.warning(f"Failed to create checkpoint: {str(coord_error)}")
            
            self._is_processing = False
            return result
            
        except Exception as e:
            # Record error metric
            await self._metrics_manager.record_metric(
                "phase_two:error",
                1.0,
                metadata={
                    "operation_id": operation_id,
                    "error": str(e),
                    "phase_id": self._phase_id if hasattr(self, '_phase_id') else None
                }
            )
            
            # Try to report error to coordinator if we have a phase ID
            if hasattr(self, '_phase_id') and self._phase_id:
                try:
                    if hasattr(self, '_coordinator'):
                        # Attempt to abort the phase with the coordinator
                        await self._coordinator.abort_phase(
                            self._phase_id, 
                            f"Error in Phase Two: {str(e)}"
                        )
                    else:
                        # Attempt to abort the phase with the coordinator
                        await self._phase_coordination.abort_phase(
                            self._phase_id, 
                            f"Error in Phase Two: {str(e)}"
                        )
                except Exception as coord_error:
                    logger.error(f"Failed to report error to coordinator: {str(coord_error)}")
            
            logger.error(f"Error in Phase Two: {str(e)}", exc_info=True)
            self._is_processing = False
            return {
                "status": "error",
                "error": str(e),
                "operation_id": operation_id
            }
            
    async def get_component_status(self, component_id: str) -> Dict[str, Any]:
        """Get the status of a component."""
        context = self._development_contexts.get(component_id)
        if not context:
            # Try to get from state manager
            state = await self._state_manager.get_state(f"component:development:{component_id}")
            if not state:
                return {"error": f"Component {component_id} not found"}
            return state
        
        # Build status from context
        return {
            "component_id": component_id,
            "component_name": context.component_name,
            "description": context.description,
            "state": context.state.name,
            "dependencies": list(context.dependencies),
            "features": context.features,
            "has_tests": len(context.tests) > 0,
            "has_implementation": bool(context.implementation),
            "iterations": len(context.iteration_history),
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_development_progress(self) -> Dict[str, Any]:
        """Get overall progress of the development process."""
        total_components = len(self._development_contexts)
        if total_components == 0:
            return {
                "status": "no_components",
                "message": "No components are being developed"
            }
        
        # Count components in each state
        state_counts = {state.name: 0 for state in ComponentDevelopmentState}
        for context in self._development_contexts.values():
            state_counts[context.state.name] += 1
        
        # Calculate completion percentage
        completed = state_counts[ComponentDevelopmentState.COMPLETED.name]
        completion_percentage = (completed / total_components) * 100 if total_components > 0 else 0
        
        return {
            "total_components": total_components,
            "completed_components": completed,
            "completion_percentage": completion_percentage,
            "state_counts": state_counts,
            "is_processing": self._is_processing,
            "timestamp": datetime.now().isoformat()
        }