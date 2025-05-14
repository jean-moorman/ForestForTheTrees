"""
Component Processing Orchestrator
==============================

This module provides an enhanced orchestrator for component processing with
pipeline stages, dependency enforcement, progress tracking, and circuit breakers.
"""

import logging
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from enum import Enum, auto
from dataclasses import dataclass, field

from resources import (
    ResourceType,
    EventQueue,
    StateManager,
    MetricsManager,
    ErrorHandler
)

from phase_two.models import ComponentDevelopmentContext, ComponentDevelopmentState
from phase_two.orchestration.dependencies import DependencyResolver
from phase_two.orchestration.features import FeatureDefinitionGenerator
from phase_two.orchestration.tracking import ComponentBuildTracker
from phase_two.orchestration.resources import PhaseResourceManager
from phase_two.delegation.interface import PhaseThreeDelegationInterface

logger = logging.getLogger(__name__)

class ProcessingStage(Enum):
    """Component processing pipeline stages."""
    VALIDATION = auto()       # Validate component definition
    PREPARATION = auto()      # Prepare component for processing
    FEATURE_EXTRACTION = auto()  # Extract features from component
    DELEGATION = auto()       # Delegate to Phase Three
    RESULT_COLLECTION = auto()  # Collect and process results
    INTEGRATION = auto()      # Integrate with other components
    COMPLETION = auto()       # Mark component as completed
    FAILED = auto()           # Component processing failed

@dataclass
class PipelineContext:
    """Context for component processing pipeline."""
    component_id: str
    component_name: str
    stage: ProcessingStage = ProcessingStage.VALIDATION
    component_definition: Dict[str, Any] = field(default_factory=dict)
    features: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: Set[str] = field(default_factory=set)
    delegation_id: Optional[str] = None
    development_context: Optional[ComponentDevelopmentContext] = None
    start_time: float = field(default_factory=time.time)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_error(self, stage: ProcessingStage, error_message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Add an error to the context."""
        self.errors.append({
            "stage": stage.name,
            "timestamp": datetime.now().isoformat(),
            "error": error_message,
            "details": details or {}
        })
    
    def get_duration(self) -> float:
        """Get the duration of processing in seconds."""
        return time.time() - self.start_time

class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = auto()      # Normal operation
    OPEN = auto()        # Preventing operation due to failures
    HALF_OPEN = auto()   # Testing if system has recovered

class ComponentProcessingOrchestrator:
    """
    Orchestrates the processing of components through a pipeline.
    
    Key responsibilities:
    1. Pipeline stages for component processing
    2. Sequential processing with dependency order enforcement
    3. Progress tracking mechanisms
    4. Error handling with circuit breakers
    """
    
    def __init__(self,
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 dependency_resolver: DependencyResolver,
                 feature_generator: FeatureDefinitionGenerator,
                 build_tracker: ComponentBuildTracker,
                 resource_manager: PhaseResourceManager,
                 delegation_interface: PhaseThreeDelegationInterface):
        """
        Initialize the ComponentProcessingOrchestrator.
        
        Args:
            event_queue: EventQueue for event emission
            state_manager: StateManager for state persistence
            metrics_manager: MetricsManager for metrics recording
            error_handler: ErrorHandler for error handling
            dependency_resolver: DependencyResolver for component dependency management
            feature_generator: FeatureDefinitionGenerator for feature extraction
            build_tracker: ComponentBuildTracker for build progress tracking
            resource_manager: PhaseResourceManager for resource management
            delegation_interface: PhaseThreeDelegationInterface for delegation to Phase Three
        """
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._metrics_manager = metrics_manager
        self._error_handler = error_handler
        self._dependency_resolver = dependency_resolver
        self._feature_generator = feature_generator
        self._build_tracker = build_tracker
        self._resource_manager = resource_manager
        self._delegation_interface = delegation_interface
        
        # Pipeline context tracking
        self._active_pipelines: Dict[str, PipelineContext] = {}
        self._completed_components: Dict[str, Dict[str, Any]] = {}
        self._failed_components: Dict[str, Dict[str, Any]] = {}
        
        # Circuit breaker state
        self._circuit_state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._failure_threshold = 3
        self._circuit_reset_time: Optional[float] = None
        
        # Pipeline stage handlers
        self._stage_handlers: Dict[ProcessingStage, Callable] = {
            ProcessingStage.VALIDATION: self._handle_validation_stage,
            ProcessingStage.PREPARATION: self._handle_preparation_stage,
            ProcessingStage.FEATURE_EXTRACTION: self._handle_feature_extraction_stage,
            ProcessingStage.DELEGATION: self._handle_delegation_stage,
            ProcessingStage.RESULT_COLLECTION: self._handle_result_collection_stage,
            ProcessingStage.INTEGRATION: self._handle_integration_stage,
            ProcessingStage.COMPLETION: self._handle_completion_stage,
            ProcessingStage.FAILED: self._handle_failure_stage
        }
        
        # Configuration
        self._max_concurrent_components = 5
        self._result_collection_interval = 10  # seconds
        
        # Processing queue and semaphore for limiting concurrency
        self._processing_queue: asyncio.Queue = asyncio.Queue()
        self._processing_semaphore = asyncio.Semaphore(self._max_concurrent_components)
        
        # Track ongoing tasks
        self._ongoing_tasks: Set[asyncio.Task] = set()
        
    async def initialize(self) -> None:
        """Initialize the orchestrator."""
        # Start resource manager
        await self._resource_manager.initialize()
        
        # Start build tracker
        await self._build_tracker.initialize()
        
        # Start worker pool for processing components
        self._start_worker_pool()
        
        logger.info(f"ComponentProcessingOrchestrator initialized with {self._max_concurrent_components} workers")
    
    def _start_worker_pool(self) -> None:
        """Start worker pool for processing components."""
        for _ in range(self._max_concurrent_components):
            task = asyncio.create_task(self._worker_loop())
            self._ongoing_tasks.add(task)
            task.add_done_callback(self._ongoing_tasks.discard)
    
    async def _worker_loop(self) -> None:
        """Worker loop for processing components from the queue."""
        while True:
            try:
                # Get next component from queue
                component_id = await self._processing_queue.get()
                
                # Check circuit breaker
                if self._circuit_state == CircuitBreakerState.OPEN:
                    logger.warning(f"Circuit breaker is open, skipping component {component_id}")
                    self._processing_queue.task_done()
                    continue
                
                # Check resource limitations
                if not await self._resource_manager.can_process_component():
                    logger.warning(f"Resource limitations prevent processing component {component_id}")
                    # Put back in queue with delay
                    asyncio.create_task(self._requeue_with_delay(component_id, 30))
                    self._processing_queue.task_done()
                    continue
                
                # Acquire semaphore to limit concurrency
                async with self._processing_semaphore:
                    # Process component through pipeline
                    await self._process_component_pipeline(component_id)
                
                # Mark task as done
                self._processing_queue.task_done()
                
            except asyncio.CancelledError:
                logger.info("Worker task cancelled")
                break
                
            except Exception as e:
                logger.error(f"Error in worker loop: {str(e)}", exc_info=True)
                # Continue with next component
                continue
    
    async def _requeue_with_delay(self, component_id: str, delay_seconds: float) -> None:
        """Requeue a component with a delay."""
        await asyncio.sleep(delay_seconds)
        await self._processing_queue.put(component_id)
    
    async def process_components(self, 
                              components: List[Dict[str, Any]], 
                              operation_id: str,
                              wait_for_completion: bool = True) -> Dict[str, Any]:
        """
        Process a list of components through the pipeline.
        
        Args:
            components: List of component definitions
            operation_id: Operation ID for tracking
            wait_for_completion: Whether to wait for all components to complete
            
        Returns:
            Dictionary with processing results
        """
        # Check circuit breaker
        if self._circuit_state == CircuitBreakerState.OPEN:
            logger.warning("Circuit breaker is open, rejecting component processing request")
            return {
                "status": "rejected",
                "reason": "circuit_breaker_open",
                "operation_id": operation_id,
                "message": "Too many failures have occurred, circuit breaker is open"
            }
        
        # Record start of processing
        start_time = time.time()
        total_components = len(components)
        
        logger.info(f"Starting processing of {total_components} components for operation {operation_id}")
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:processing:start",
            total_components,
            metadata={
                "operation_id": operation_id,
                "component_count": total_components
            }
        )
        
        try:
            # Sort components by dependencies
            sorted_components = await self._dependency_resolver.sort_components(components)
            
            # Check for cycles
            cycles = await self._dependency_resolver.detect_cycles(components)
            if cycles:
                logger.error(f"Dependency cycles detected: {cycles}")
                return {
                    "status": "error",
                    "reason": "dependency_cycles",
                    "operation_id": operation_id,
                    "cycles": cycles,
                    "message": "Dependency cycles detected in components"
                }
            
            # Create pipeline contexts
            for component in sorted_components:
                component_id = component.get("id", f"component_{int(time.time())}")
                component_name = component.get("name", "Unnamed Component")
                
                # Create pipeline context
                context = PipelineContext(
                    component_id=component_id,
                    component_name=component_name,
                    component_definition=component,
                    dependencies=set(component.get("dependencies", []))
                )
                
                # Store in active pipelines
                self._active_pipelines[component_id] = context
                
                # Add to processing queue
                await self._processing_queue.put(component_id)
            
            # If wait for completion, wait for all components to be processed
            if wait_for_completion:
                await self._processing_queue.join()
                
                # Calculate results
                completed_count = len(self._completed_components)
                failed_count = len(self._failed_components)
                execution_time = time.time() - start_time
                
                # Prepare result
                result = {
                    "status": "completed",
                    "operation_id": operation_id,
                    "total_components": total_components,
                    "completed_components": completed_count,
                    "failed_components": failed_count,
                    "execution_time_seconds": execution_time,
                    "components": {
                        "completed": self._completed_components,
                        "failed": self._failed_components
                    }
                }
                
                # Record completion metric
                await self._metrics_manager.record_metric(
                    "phase_two:processing:complete",
                    1.0,
                    metadata={
                        "operation_id": operation_id,
                        "total_components": total_components,
                        "completed_components": completed_count,
                        "failed_components": failed_count,
                        "execution_time": execution_time
                    }
                )
                
                logger.info(f"Completed processing of {total_components} components in {execution_time:.2f} seconds")
                
                return result
            else:
                # Return immediately with status
                return {
                    "status": "processing",
                    "operation_id": operation_id,
                    "total_components": total_components,
                    "message": f"Processing {total_components} components in background"
                }
        
        except Exception as e:
            logger.error(f"Error in component processing: {str(e)}", exc_info=True)
            
            # Record error metric
            await self._metrics_manager.record_metric(
                "phase_two:processing:error",
                1.0,
                metadata={
                    "operation_id": operation_id,
                    "error": str(e)
                }
            )
            
            # Record error with error handler
            await self._error_handler.record_error(
                error=e,
                source="phase_two_orchestration",
                context={
                    "operation_id": operation_id,
                    "component_count": total_components
                }
            )
            
            # Update circuit breaker
            await self._update_circuit_breaker(True)
            
            return {
                "status": "error",
                "operation_id": operation_id,
                "error": str(e),
                "message": "Error occurred during component processing"
            }
    
    async def _process_component_pipeline(self, component_id: str) -> None:
        """
        Process a component through the pipeline stages.
        
        Args:
            component_id: ID of the component to process
        """
        if component_id not in self._active_pipelines:
            logger.error(f"Component {component_id} not found in active pipelines")
            return
        
        context = self._active_pipelines[component_id]
        
        # Track processing with build tracker
        await self._build_tracker.start_component_processing(
            component_id, 
            context.component_name,
            context.dependencies
        )
        
        # Loop through pipeline stages
        while context.stage != ProcessingStage.COMPLETION and context.stage != ProcessingStage.FAILED:
            try:
                # Record the current stage
                current_stage = context.stage
                
                # Update build tracker with current stage
                await self._build_tracker.update_component_stage(
                    component_id, 
                    current_stage.name
                )
                
                # Get handler for current stage
                handler = self._stage_handlers.get(current_stage)
                if not handler:
                    logger.error(f"No handler found for stage {current_stage.name}")
                    context.add_error(
                        current_stage, 
                        f"No handler found for stage {current_stage.name}"
                    )
                    context.stage = ProcessingStage.FAILED
                    continue
                
                # Handle stage
                next_stage = await handler(context)
                
                # Update stage
                context.stage = next_stage
                
                # Record metric for stage transition
                await self._metrics_manager.record_metric(
                    "phase_two:processing:stage_transition",
                    1.0,
                    metadata={
                        "component_id": context.component_id,
                        "component_name": context.component_name,
                        "from_stage": current_stage.name,
                        "to_stage": next_stage.name
                    }
                )
                
            except Exception as e:
                logger.error(f"Error in pipeline stage {context.stage.name} for component {component_id}: {str(e)}", exc_info=True)
                
                # Record error
                context.add_error(
                    context.stage, 
                    str(e),
                    {"traceback": str(e.__traceback__)}
                )
                
                # Record error with error handler
                await self._error_handler.record_error(
                    error=e,
                    source="phase_two_orchestration_pipeline",
                    context={
                        "component_id": component_id,
                        "stage": context.stage.name
                    }
                )
                
                # Move to failed stage
                context.stage = ProcessingStage.FAILED
                
                # Update circuit breaker
                await self._update_circuit_breaker(True)
        
        # Finalize processing
        if context.stage == ProcessingStage.COMPLETION:
            # Store in completed components
            self._completed_components[component_id] = {
                "component_id": component_id,
                "component_name": context.component_name,
                "features": context.features,
                "results": context.results,
                "duration": context.get_duration(),
                "completed_at": datetime.now().isoformat()
            }
            
            # Finalize in build tracker
            await self._build_tracker.complete_component_processing(
                component_id,
                success=True,
                results=context.results
            )
            
            # Update circuit breaker with success
            await self._update_circuit_breaker(False)
            
        elif context.stage == ProcessingStage.FAILED:
            # Store in failed components
            self._failed_components[component_id] = {
                "component_id": component_id,
                "component_name": context.component_name,
                "errors": context.errors,
                "duration": context.get_duration(),
                "failed_at": datetime.now().isoformat()
            }
            
            # Finalize in build tracker
            await self._build_tracker.complete_component_processing(
                component_id,
                success=False,
                errors=context.errors
            )
            
            # Update circuit breaker with failure
            await self._update_circuit_breaker(True)
        
        # Remove from active pipelines
        if component_id in self._active_pipelines:
            del self._active_pipelines[component_id]
        
        logger.info(f"Component {component_id} processing completed with status: {context.stage.name}")
    
    async def _handle_validation_stage(self, context: PipelineContext) -> ProcessingStage:
        """
        Handle the validation stage.
        
        Args:
            context: Pipeline context
            
        Returns:
            Next processing stage
        """
        logger.info(f"Validating component {context.component_id}")
        
        # Validate component definition
        validation_result = await self._dependency_resolver.validate_component(
            context.component_definition
        )
        
        if not validation_result["is_valid"]:
            # Record validation errors
            for error in validation_result["errors"]:
                context.add_error(
                    ProcessingStage.VALIDATION, 
                    error["message"],
                    error
                )
            
            logger.error(f"Component {context.component_id} validation failed: {validation_result['errors']}")
            return ProcessingStage.FAILED
        
        # Check dependencies
        for dependency_id in context.dependencies:
            # Check if dependency is already completed
            if dependency_id not in self._completed_components:
                # Dependency not yet completed
                logger.warning(f"Component {context.component_id} depends on uncompleted component {dependency_id}")
                context.add_error(
                    ProcessingStage.VALIDATION,
                    f"Dependency {dependency_id} not yet completed",
                    {"dependency_id": dependency_id}
                )
                return ProcessingStage.FAILED
        
        # Move to preparation stage
        return ProcessingStage.PREPARATION
    
    async def _handle_preparation_stage(self, context: PipelineContext) -> ProcessingStage:
        """
        Handle the preparation stage.
        
        Args:
            context: Pipeline context
            
        Returns:
            Next processing stage
        """
        logger.info(f"Preparing component {context.component_id}")
        
        # Create development context
        development_context = ComponentDevelopmentContext(
            component_id=context.component_id,
            component_name=context.component_name,
            description=context.component_definition.get("description", ""),
            requirements=context.component_definition,
            dependencies=context.dependencies
        )
        
        # Store development context
        context.development_context = development_context
        
        # Store in state manager
        await self._state_manager.set_state(
            f"component:development:{context.component_id}",
            {
                "component_id": context.component_id,
                "component_name": context.component_name,
                "state": development_context.state.name,
                "timestamp": datetime.now().isoformat()
            },
            ResourceType.STATE
        )
        
        # Move to feature extraction stage
        return ProcessingStage.FEATURE_EXTRACTION
    
    async def _handle_feature_extraction_stage(self, context: PipelineContext) -> ProcessingStage:
        """
        Handle the feature extraction stage.
        
        Args:
            context: Pipeline context
            
        Returns:
            Next processing stage
        """
        logger.info(f"Extracting features for component {context.component_id}")
        
        # Extract features from component definition
        features_result = await self._feature_generator.extract_features(
            context.component_definition,
            context.dependencies
        )
        
        if "error" in features_result:
            context.add_error(
                ProcessingStage.FEATURE_EXTRACTION,
                features_result["error"]
            )
            logger.error(f"Feature extraction failed for component {context.component_id}: {features_result['error']}")
            return ProcessingStage.FAILED
        
        # Store features in context
        context.features = features_result["features"]
        
        # Store in development context
        if context.development_context:
            context.development_context.features = context.features
            # Update development context state
            context.development_context.state = ComponentDevelopmentState.PLANNING
            
            # Record iteration in development context
            context.development_context.record_iteration(
                ComponentDevelopmentState.PLANNING,
                {"features": context.features}
            )
        
        # Move to delegation stage
        return ProcessingStage.DELEGATION
    
    async def _handle_delegation_stage(self, context: PipelineContext) -> ProcessingStage:
        """
        Handle the delegation stage.
        
        Args:
            context: Pipeline context
            
        Returns:
            Next processing stage
        """
        logger.info(f"Delegating component {context.component_id} to Phase Three")
        
        # Update development context state
        if context.development_context:
            context.development_context.state = ComponentDevelopmentState.IMPLEMENTATION
            await self._update_development_context(context.component_id, context.development_context)
        
        # Delegate to Phase Three
        delegation_result = await self._delegation_interface.delegate_component(
            context.component_id,
            context.component_definition,
            wait_for_completion=False  # Don't wait, we'll poll for results
        )
        
        if delegation_result["status"] == "error":
            context.add_error(
                ProcessingStage.DELEGATION,
                delegation_result["error"],
                delegation_result
            )
            logger.error(f"Delegation failed for component {context.component_id}: {delegation_result['error']}")
            return ProcessingStage.FAILED
        
        # Store delegation ID
        context.delegation_id = delegation_result["delegation_id"]
        
        # Store metadata
        context.metadata["delegation"] = delegation_result
        
        # Move to result collection stage
        return ProcessingStage.RESULT_COLLECTION
    
    async def _handle_result_collection_stage(self, context: PipelineContext) -> ProcessingStage:
        """
        Handle the result collection stage.
        
        Args:
            context: Pipeline context
            
        Returns:
            Next processing stage
        """
        logger.info(f"Collecting results for component {context.component_id}")
        
        if not context.delegation_id:
            context.add_error(
                ProcessingStage.RESULT_COLLECTION,
                "No delegation ID found"
            )
            logger.error(f"No delegation ID found for component {context.component_id}")
            return ProcessingStage.FAILED
        
        # Get delegation result
        delegation_result = await self._delegation_interface.get_delegation_result(
            context.delegation_id
        )
        
        if delegation_result["status"] == "not_found":
            context.add_error(
                ProcessingStage.RESULT_COLLECTION,
                f"Delegation {context.delegation_id} not found",
                delegation_result
            )
            logger.error(f"Delegation {context.delegation_id} not found for component {context.component_id}")
            return ProcessingStage.FAILED
        
        if delegation_result["status"] == "in_progress":
            # Still in progress, wait and retry
            logger.info(f"Delegation {context.delegation_id} for component {context.component_id} still in progress")
            
            # Wait for a while before retrying
            await asyncio.sleep(self._result_collection_interval)
            
            # Stay in the same stage
            return ProcessingStage.RESULT_COLLECTION
        
        if delegation_result["status"] == "failed":
            context.add_error(
                ProcessingStage.RESULT_COLLECTION,
                "Delegation failed",
                delegation_result
            )
            logger.error(f"Delegation failed for component {context.component_id}: {delegation_result}")
            return ProcessingStage.FAILED
        
        # Store results
        context.results = delegation_result
        
        # Update development context
        if context.development_context:
            context.development_context.implementation = delegation_result.get("implementation", "")
            
            # Record iteration in development context
            context.development_context.record_iteration(
                ComponentDevelopmentState.IMPLEMENTATION,
                {"implementation_result": delegation_result}
            )
            
            # Update development context state
            context.development_context.state = ComponentDevelopmentState.TESTING
            await self._update_development_context(context.component_id, context.development_context)
        
        # Move to integration stage
        return ProcessingStage.INTEGRATION
    
    async def _handle_integration_stage(self, context: PipelineContext) -> ProcessingStage:
        """
        Handle the integration stage.
        
        Args:
            context: Pipeline context
            
        Returns:
            Next processing stage
        """
        logger.info(f"Integrating component {context.component_id}")
        
        # Check if component has dependencies
        if not context.dependencies:
            logger.info(f"Component {context.component_id} has no dependencies, skipping integration")
            return ProcessingStage.COMPLETION
        
        # Update development context state
        if context.development_context:
            context.development_context.state = ComponentDevelopmentState.INTEGRATION
            await self._update_development_context(context.component_id, context.development_context)
        
        # Get dependency implementations
        dependency_implementations = []
        for dep_id in context.dependencies:
            if dep_id in self._completed_components:
                dep_result = self._completed_components[dep_id]
                if "implementation" in dep_result.get("results", {}):
                    dependency_implementations.append({
                        "component_id": dep_id,
                        "component_name": dep_result.get("component_name", ""),
                        "implementation": dep_result["results"]["implementation"]
                    })
        
        # Check if we have implementations for all dependencies
        if len(dependency_implementations) != len(context.dependencies):
            missing_deps = context.dependencies - {dep["component_id"] for dep in dependency_implementations}
            logger.warning(f"Missing implementations for dependencies: {missing_deps}")
            
            # We can continue anyway, but record the issue
            context.metadata["integration_warnings"] = {
                "missing_dependencies": list(missing_deps)
            }
        
        # Store integration details in results
        context.results["integration"] = {
            "dependencies": list(context.dependencies),
            "integrated_with": [dep["component_id"] for dep in dependency_implementations]
        }
        
        # Record integration in development context
        if context.development_context:
            context.development_context.record_iteration(
                ComponentDevelopmentState.INTEGRATION,
                {
                    "dependencies": list(context.dependencies),
                    "integrated_with": [dep["component_id"] for dep in dependency_implementations]
                }
            )
        
        # Move to completion stage
        return ProcessingStage.COMPLETION
    
    async def _handle_completion_stage(self, context: PipelineContext) -> ProcessingStage:
        """
        Handle the completion stage.
        
        Args:
            context: Pipeline context
            
        Returns:
            Next processing stage
        """
        logger.info(f"Completing component {context.component_id}")
        
        # Update development context state
        if context.development_context:
            context.development_context.state = ComponentDevelopmentState.COMPLETED
            await self._update_development_context(context.component_id, context.development_context)
        
        # Record completion in context
        context.results["completion"] = {
            "timestamp": datetime.now().isoformat(),
            "duration": context.get_duration()
        }
        
        # Stay in completion stage
        return ProcessingStage.COMPLETION
    
    async def _handle_failure_stage(self, context: PipelineContext) -> ProcessingStage:
        """
        Handle the failure stage.
        
        Args:
            context: Pipeline context
            
        Returns:
            Next processing stage
        """
        logger.error(f"Component {context.component_id} processing failed")
        
        # Update development context state
        if context.development_context:
            context.development_context.state = ComponentDevelopmentState.FAILED
            await self._update_development_context(context.component_id, context.development_context)
        
        # Record failure in context
        context.results["failure"] = {
            "timestamp": datetime.now().isoformat(),
            "duration": context.get_duration(),
            "errors": context.errors
        }
        
        # Stay in failure stage
        return ProcessingStage.FAILED
    
    async def _update_development_context(self, component_id: str, context: ComponentDevelopmentContext) -> None:
        """
        Update development context in state manager.
        
        Args:
            component_id: Component ID
            context: Development context
        """
        try:
            await self._state_manager.set_state(
                f"component:development:{component_id}",
                {
                    "component_id": component_id,
                    "component_name": context.component_name,
                    "state": context.state.name,
                    "timestamp": datetime.now().isoformat()
                },
                ResourceType.STATE
            )
            
            # Record state change metric
            await self._metrics_manager.record_metric(
                "component:development:state_change",
                1.0,
                metadata={
                    "component_id": component_id,
                    "component_name": context.component_name,
                    "state": context.state.name
                }
            )
        except Exception as e:
            logger.error(f"Error updating development context for {component_id}: {str(e)}")
    
    async def _update_circuit_breaker(self, failure: bool) -> None:
        """
        Update circuit breaker state based on success or failure.
        
        Args:
            failure: Whether the operation failed
        """
        if failure:
            # Increment failure count
            self._failure_count += 1
            
            # Check if threshold exceeded
            if self._failure_count >= self._failure_threshold:
                self._circuit_state = CircuitBreakerState.OPEN
                self._circuit_reset_time = time.time() + 300  # Reset after 5 minutes
                
                logger.warning(f"Circuit breaker opened due to {self._failure_count} failures")
                
                # Record circuit breaker state change
                await self._metrics_manager.record_metric(
                    "phase_two:orchestration:circuit_breaker_open",
                    1.0,
                    metadata={
                        "failure_count": self._failure_count,
                        "threshold": self._failure_threshold,
                        "reset_time": datetime.fromtimestamp(self._circuit_reset_time).isoformat()
                    }
                )
                
                # Schedule reset task
                asyncio.create_task(self._reset_circuit_breaker())
        else:
            # Success, reduce failure count
            self._failure_count = max(0, self._failure_count - 1)
            
            # If circuit is half-open, close it on success
            if self._circuit_state == CircuitBreakerState.HALF_OPEN:
                self._circuit_state = CircuitBreakerState.CLOSED
                self._circuit_reset_time = None
                
                logger.info("Circuit breaker closed after successful operation")
                
                # Record circuit breaker state change
                await self._metrics_manager.record_metric(
                    "phase_two:orchestration:circuit_breaker_closed",
                    1.0
                )
    
    async def _reset_circuit_breaker(self) -> None:
        """Reset circuit breaker after delay."""
        if not self._circuit_reset_time:
            return
            
        # Calculate delay until reset time
        now = time.time()
        if now < self._circuit_reset_time:
            delay = self._circuit_reset_time - now
            await asyncio.sleep(delay)
        
        # Check if circuit still open
        if self._circuit_state == CircuitBreakerState.OPEN:
            # Set to half-open
            self._circuit_state = CircuitBreakerState.HALF_OPEN
            self._failure_count = self._failure_threshold - 1  # One more failure will re-open
            
            logger.info("Circuit breaker reset to half-open state")
            
            # Record circuit breaker state change
            await self._metrics_manager.record_metric(
                "phase_two:orchestration:circuit_breaker_half_open",
                1.0
            )
    
    async def get_component_status(self, component_id: str) -> Dict[str, Any]:
        """
        Get the status of a component.
        
        Args:
            component_id: ID of the component
            
        Returns:
            Dictionary with component status
        """
        # Check if component is in active pipelines
        if component_id in self._active_pipelines:
            context = self._active_pipelines[component_id]
            return {
                "status": "processing",
                "component_id": component_id,
                "component_name": context.component_name,
                "stage": context.stage.name,
                "started_at": datetime.fromtimestamp(context.start_time).isoformat(),
                "duration": context.get_duration(),
                "errors": context.errors,
                "features": len(context.features)
            }
        
        # Check if component is completed
        if component_id in self._completed_components:
            return {
                "status": "completed",
                "component_id": component_id,
                **self._completed_components[component_id]
            }
        
        # Check if component failed
        if component_id in self._failed_components:
            return {
                "status": "failed",
                "component_id": component_id,
                **self._failed_components[component_id]
            }
        
        # Component not found
        return {
            "status": "not_found",
            "component_id": component_id,
            "message": f"Component {component_id} not found"
        }
    
    async def get_processing_status(self) -> Dict[str, Any]:
        """
        Get the overall processing status.
        
        Returns:
            Dictionary with processing status
        """
        # Count components in each stage
        stage_counts = {stage.name: 0 for stage in ProcessingStage}
        for context in self._active_pipelines.values():
            stage_counts[context.stage.name] += 1
        
        # Get queue size
        queue_size = self._processing_queue.qsize()
        
        # Calculate counts
        active_count = len(self._active_pipelines)
        completed_count = len(self._completed_components)
        failed_count = len(self._failed_components)
        total_count = active_count + completed_count + failed_count
        
        # Calculate completion percentage
        completion_percentage = (completed_count / total_count) * 100 if total_count > 0 else 0
        
        return {
            "active_components": active_count,
            "completed_components": completed_count,
            "failed_components": failed_count,
            "total_components": total_count,
            "queue_size": queue_size,
            "completion_percentage": completion_percentage,
            "stage_counts": stage_counts,
            "circuit_breaker_state": self._circuit_state.name,
            "failure_count": self._failure_count,
            "timestamp": datetime.now().isoformat()
        }
    
    async def shutdown(self) -> None:
        """Shutdown the orchestrator."""
        # Cancel all worker tasks
        for task in self._ongoing_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._ongoing_tasks:
            await asyncio.gather(*self._ongoing_tasks, return_exceptions=True)
        
        # Shutdown build tracker
        await self._build_tracker.shutdown()
        
        # Shutdown resource manager
        await self._resource_manager.shutdown()
        
        logger.info("ComponentProcessingOrchestrator shutdown complete")