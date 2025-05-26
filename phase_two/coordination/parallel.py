"""
Parallel Feature Coordinator for Phase Two
---------------------------------------
Manages parallel delegation to Phase Three, aggregates results, 
balances workload, and tracks dependencies between features.
"""

import logging
import asyncio
import uuid
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime
import json

from resources import (
    EventQueue,
    StateManager,
    MetricsManager,
    PhaseCoordinationIntegration,
    PhaseType,
    ResourceEventTypes
)

logger = logging.getLogger(__name__)

class ParallelFeatureCoordinator:
    """
    Manages parallel feature development with Phase Three.
    
    This class provides:
    1. Management of parallel delegation to Phase Three
    2. Aggregation of results from parallel feature development
    3. Balancing workload across available resources
    4. Dependency tracking between parallel feature developments
    5. Thread boundary enforcement for parallel execution
    """
    
    def __init__(self,
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 metrics_manager: MetricsManager,
                 phase_coordination: PhaseCoordinationIntegration,
                 max_concurrent_features: int = 5,
                 dependency_resolution_mode: str = "topological"):
        """
        Initialize the ParallelFeatureCoordinator.
        
        Args:
            event_queue: EventQueue for emitting events
            state_manager: StateManager for state persistence
            metrics_manager: MetricsManager for metrics recording
            phase_coordination: PhaseCoordinationIntegration for coordination
            max_concurrent_features: Maximum number of concurrent features to process
            dependency_resolution_mode: Mode for resolving dependencies ("topological" or "level")
        """
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._metrics_manager = metrics_manager
        self._phase_coordination = phase_coordination
        self._max_concurrent_features = max_concurrent_features
        self._dependency_resolution_mode = dependency_resolution_mode
        
        # Store active parallel operations
        self._active_operations: Dict[str, Dict[str, Any]] = {}
        
        # Store feature dependencies
        self._feature_dependencies: Dict[str, Dict[str, Set[str]]] = {}
        
        # Store feature status
        self._feature_statuses: Dict[str, Dict[str, Any]] = {}
        
        # Store workload distribution
        self._workload_distribution: Dict[str, int] = {}  # resource_id -> count
        
        # Store thread affinity for proper thread boundary enforcement
        import threading
        import asyncio
        self._creation_thread_id = threading.get_ident()
        
        # Store the event loop for this component
        from resources.events.loop_management import ThreadLocalEventLoopStorage
        try:
            loop = asyncio.get_event_loop()
            ThreadLocalEventLoopStorage.get_instance().set_loop(loop)
            logger.debug(f"ParallelFeatureCoordinator initialized in thread {self._creation_thread_id} with loop {id(loop)}")
        except Exception as e:
            logger.warning(f"Could not register event loop for ParallelFeatureCoordinator: {e}")
            
        # Keep track of feature semaphores per thread - thread safe dict
        self._feature_semaphores = {}
        self._semaphore_lock = threading.RLock()
        
        logger.info(f"ParallelFeatureCoordinator initialized with max_concurrent_features={max_concurrent_features}")
    
    async def start_parallel_feature_development(self,
                                               parent_phase_id: str,
                                               component_id: str,
                                               features: List[Dict[str, Any]],
                                               config: Dict[str, Any],
                                               operation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Start parallel feature development for a component.
        
        Args:
            parent_phase_id: ID of the parent phase
            component_id: ID of the component
            features: List of feature definitions
            config: Configuration for feature development
            operation_id: Optional operation ID
            
        Returns:
            Dictionary with operation information
        """
        # Generate operation ID if not provided
        if not operation_id:
            operation_id = f"parallel_op_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"
        
        # Analyze feature dependencies
        dependency_graph, execution_order = self._analyze_dependencies(features)
        
        # Store dependency information
        self._feature_dependencies[operation_id] = dependency_graph
        
        # Initialize feature statuses
        for feature in features:
            feature_id = feature["id"]
            self._feature_statuses[feature_id] = {
                "operation_id": operation_id,
                "component_id": component_id,
                "status": "pending",
                "dependencies_met": len(dependency_graph.get(feature_id, set())) == 0,
                "created_at": datetime.now().isoformat()
            }
        
        # Create operation record
        operation = {
            "operation_id": operation_id,
            "parent_phase_id": parent_phase_id,
            "component_id": component_id,
            "start_time": datetime.now().isoformat(),
            "status": "started",
            "config": config,
            "feature_count": len(features),
            "execution_order": execution_order,
            "completed_features": [],
            "in_progress_features": [],
            "pending_features": [f["id"] for f in features],
            "failed_features": []
        }
        
        # Store operation
        self._active_operations[operation_id] = operation
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:parallel_features:started",
            1.0,
            metadata={
                "operation_id": operation_id,
                "component_id": component_id,
                "feature_count": len(features)
            }
        )
        
        # Emit operation started event
        await self._event_queue.emit(
            ResourceEventTypes.PHASE_COORDINATION_EVENT.value,
            {
                "event_type": "parallel_feature_development_started",
                "operation_id": operation_id,
                "component_id": component_id,
                "feature_count": len(features),
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Start processing features asynchronously
        asyncio.create_task(self._process_features(operation_id, parent_phase_id, features, config))
        
        return {
            "operation_id": operation_id,
            "component_id": component_id,
            "status": "started",
            "feature_count": len(features),
            "dependency_layers": self._get_dependency_layers(execution_order, dependency_graph)
        }
    
    async def get_operation_status(self, operation_id: str) -> Dict[str, Any]:
        """
        Get the status of a parallel feature operation.
        
        Args:
            operation_id: ID of the operation
            
        Returns:
            Dictionary with operation status
        """
        # Check if operation exists
        if operation_id not in self._active_operations:
            return {
                "found": False,
                "operation_id": operation_id,
                "message": f"Operation {operation_id} not found"
            }
        
        # Get operation info
        operation = self._active_operations[operation_id]
        
        # Calculate completion percentage
        completed_count = len(operation["completed_features"])
        total_count = operation["feature_count"]
        completion_percentage = (completed_count / total_count) * 100 if total_count > 0 else 0
        
        # Determine overall status
        if completed_count == total_count:
            status = "completed"
        elif len(operation["failed_features"]) > 0:
            if len(operation["pending_features"]) == 0 and len(operation["in_progress_features"]) == 0:
                status = "failed"
            else:
                status = "partial_failure"
        else:
            status = "in_progress"
        
        # Get individual feature statuses
        feature_statuses = {}
        for feature_id in (operation["completed_features"] + 
                          operation["in_progress_features"] + 
                          operation["pending_features"] + 
                          operation["failed_features"]):
            feature_statuses[feature_id] = self._feature_statuses.get(feature_id, {"status": "unknown"})
        
        # Calculate duration if operation has end_time
        duration_ms = None
        if "end_time" in operation:
            duration_ms = (datetime.fromisoformat(operation["end_time"]) - 
                          datetime.fromisoformat(operation["start_time"])).total_seconds() * 1000
        
        # Construct response
        response = {
            "found": True,
            "operation_id": operation_id,
            "component_id": operation["component_id"],
            "status": status,
            "start_time": operation["start_time"],
            "feature_count": operation["feature_count"],
            "completed_count": completed_count,
            "in_progress_count": len(operation["in_progress_features"]),
            "pending_count": len(operation["pending_features"]),
            "failed_count": len(operation["failed_features"]),
            "completion_percentage": completion_percentage,
            "features": {
                "completed": operation["completed_features"],
                "in_progress": operation["in_progress_features"],
                "pending": operation["pending_features"],
                "failed": operation["failed_features"]
            },
            "feature_statuses": feature_statuses
        }
        
        # Add end time and duration if available
        if "end_time" in operation:
            response["end_time"] = operation["end_time"]
            response["duration_ms"] = duration_ms
        
        return response
    
    async def get_feature_status(self, feature_id: str) -> Dict[str, Any]:
        """
        Get the status of a specific feature.
        
        Args:
            feature_id: ID of the feature
            
        Returns:
            Dictionary with feature status
        """
        # Check if feature exists
        if feature_id not in self._feature_statuses:
            return {
                "found": False,
                "feature_id": feature_id,
                "message": f"Feature {feature_id} not found"
            }
        
        # Get feature status
        status = self._feature_statuses[feature_id]
        
        # Get operation info
        operation_id = status["operation_id"]
        operation = self._active_operations.get(operation_id, {})
        
        # Add feature ID and found flag
        result = {
            "found": True,
            "feature_id": feature_id,
            **status
        }
        
        # Add component info if available
        if "component_id" in operation:
            result["component_id"] = operation["component_id"]
        
        return result
    
    async def cancel_operation(self, operation_id: str, reason: str) -> Dict[str, Any]:
        """
        Cancel a parallel feature operation.
        
        Args:
            operation_id: ID of the operation to cancel
            reason: Reason for cancellation
            
        Returns:
            Dictionary with cancellation result
        """
        # Check if operation exists
        if operation_id not in self._active_operations:
            return {
                "success": False,
                "operation_id": operation_id,
                "message": f"Operation {operation_id} not found"
            }
        
        # Get operation
        operation = self._active_operations[operation_id]
        
        # Mark operation as cancelled
        operation["status"] = "cancelled"
        operation["end_time"] = datetime.now().isoformat()
        operation["cancel_reason"] = reason
        
        # Update feature statuses for in-progress and pending features
        for feature_id in operation["in_progress_features"] + operation["pending_features"]:
            self._feature_statuses[feature_id]["status"] = "cancelled"
            self._feature_statuses[feature_id]["cancelled_at"] = datetime.now().isoformat()
            self._feature_statuses[feature_id]["cancel_reason"] = reason
        
        # Move all pending features to cancelled
        operation["cancelled_features"] = operation["in_progress_features"] + operation["pending_features"]
        operation["in_progress_features"] = []
        operation["pending_features"] = []
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:parallel_features:cancelled",
            1.0,
            metadata={
                "operation_id": operation_id,
                "component_id": operation["component_id"],
                "reason": reason,
                "completed_count": len(operation["completed_features"]),
                "cancelled_count": len(operation["cancelled_features"]),
                "failed_count": len(operation["failed_features"])
            }
        )
        
        # Emit operation cancelled event
        await self._event_queue.emit(
            ResourceEventTypes.PHASE_COORDINATION_EVENT.value,
            {
                "event_type": "parallel_feature_development_cancelled",
                "operation_id": operation_id,
                "component_id": operation["component_id"],
                "reason": reason,
                "completed_count": len(operation["completed_features"]),
                "cancelled_count": len(operation["cancelled_features"]),
                "failed_count": len(operation["failed_features"]),
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return {
            "success": True,
            "operation_id": operation_id,
            "component_id": operation["component_id"],
            "message": f"Operation {operation_id} cancelled: {reason}",
            "completed_features": operation["completed_features"],
            "cancelled_features": operation["cancelled_features"],
            "failed_features": operation["failed_features"]
        }
    
    async def aggregate_results(self, operation_id: str) -> Dict[str, Any]:
        """
        Aggregate results from a parallel feature operation.
        
        Args:
            operation_id: ID of the operation
            
        Returns:
            Dictionary with aggregated results
        """
        # Get operation status
        status = await self.get_operation_status(operation_id)
        
        if not status["found"]:
            return {
                "success": False,
                "operation_id": operation_id,
                "message": f"Operation {operation_id} not found"
            }
        
        # Collect feature details
        component_id = status["component_id"]
        features_details = {}
        
        for feature_id, feature_status in status["feature_statuses"].items():
            features_details[feature_id] = feature_status
        
        # Aggregate implementations if operation is completed
        implementations = {}
        if status["status"] in ["completed", "partial_failure"]:
            for feature_id in status["features"]["completed"]:
                # Check if feature has implementation data
                if "result" in features_details.get(feature_id, {}):
                    feature_result = features_details[feature_id]["result"]
                    if "implementation" in feature_result:
                        implementations[feature_id] = feature_result["implementation"]
        
        # Calculate success metrics
        success_rate = status["completed_count"] / status["feature_count"] if status["feature_count"] > 0 else 0
        
        # Calculate average duration
        durations = []
        for feature_id, feature_status in status["feature_statuses"].items():
            if "start_time" in feature_status and "end_time" in feature_status:
                try:
                    start = datetime.fromisoformat(feature_status["start_time"])
                    end = datetime.fromisoformat(feature_status["end_time"])
                    duration_ms = (end - start).total_seconds() * 1000
                    durations.append(duration_ms)
                except (ValueError, TypeError, KeyError):
                    pass
        
        avg_duration_ms = sum(durations) / len(durations) if durations else None
        
        # Construct aggregated result
        result = {
            "success": True,
            "operation_id": operation_id,
            "component_id": component_id,
            "status": status["status"],
            "feature_count": status["feature_count"],
            "completed_count": status["completed_count"],
            "failed_count": status["failed_count"],
            "success_rate": success_rate,
            "avg_duration_ms": avg_duration_ms,
            "features": {
                "completed": status["features"]["completed"],
                "failed": status["features"]["failed"]
            },
            "aggregated_at": datetime.now().isoformat()
        }
        
        # Add implementations if available
        if implementations:
            result["implementations"] = implementations
        
        # Add aggregated implementation if all features are completed
        if status["status"] == "completed":
            result["aggregated_implementation"] = self._aggregate_implementations(
                component_id, implementations)
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:parallel_features:aggregated",
            success_rate,
            metadata={
                "operation_id": operation_id,
                "component_id": component_id,
                "feature_count": status["feature_count"],
                "completed_count": status["completed_count"],
                "failed_count": status["failed_count"]
            }
        )
        
        return result
    
    async def _process_features(self,
                              operation_id: str,
                              parent_phase_id: str,
                              features: List[Dict[str, Any]],
                              config: Dict[str, Any]) -> None:
        """
        Process features for parallel development with thread boundary enforcement.
        
        Args:
            operation_id: ID of the operation
            parent_phase_id: ID of the parent phase
            features: List of feature definitions
            config: Configuration for feature development
        """
        # Enforce thread boundary - check if we're in the same thread as the coordinator was created in
        if hasattr(self, '_creation_thread_id'):
            current_thread_id = threading.get_ident()
            if current_thread_id != self._creation_thread_id:
                logger.warning(f"_process_features called from thread {current_thread_id}, but coordinator created in thread {self._creation_thread_id}")
                
                # Delegate to the correct thread if possible
                from resources.events.loop_management import EventLoopManager
                try:
                    loop = EventLoopManager.get_loop_for_thread(self._creation_thread_id)
                    if loop:
                        logger.info(f"Delegating _process_features to coordinator thread {self._creation_thread_id}")
                        future = EventLoopManager.run_coroutine_threadsafe(
                            self._process_features(
                                operation_id=operation_id,
                                parent_phase_id=parent_phase_id,
                                features=features,
                                config=config
                            ),
                            target_loop=loop
                        )
                        return await asyncio.wrap_future(future)
                except Exception as e:
                    logger.error(f"Error delegating _process_features to coordinator thread: {e}")
                    # Continue with current thread as fallback, but log the issue
        
        # Get operation
        operation = self._active_operations[operation_id]
        
        # Get dependency information
        dependency_graph = self._feature_dependencies.get(operation_id, {})
        execution_order = operation["execution_order"]
        
        # Group features by dependency layer
        layers = self._get_dependency_layers(execution_order, dependency_graph)
        
        try:
            # Process each layer in order
            for layer_idx, layer in enumerate(layers):
                logger.info(f"Processing layer {layer_idx + 1}/{len(layers)} with {len(layer)} features for operation {operation_id}")
                
                # Emit layer start event
                await self._event_queue.emit(
                    ResourceEventTypes.PHASE_COORDINATION_EVENT.value,
                    {
                        "event_type": "parallel_features_layer_started",
                        "operation_id": operation_id,
                        "layer_index": layer_idx,
                        "feature_count": len(layer),
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                # Process features in this layer in parallel with concurrency limit
                layer_tasks = []
                
                # Use a thread-safe dictionary of semaphores to ensure each thread has its own semaphore
                current_thread_id = threading.get_ident()
                with self._semaphore_lock:
                    if current_thread_id not in self._feature_semaphores:
                        self._feature_semaphores[current_thread_id] = asyncio.Semaphore(self._max_concurrent_features)
                    semaphore = self._feature_semaphores[current_thread_id]
                
                for feature_id in layer:
                    # Get feature definition
                    feature = next((f for f in features if f["id"] == feature_id), None)
                    if not feature:
                        logger.warning(f"Feature {feature_id} not found in features list for operation {operation_id}")
                        continue
                    
                    # Create task for this feature
                    task = asyncio.create_task(
                        self._process_feature_with_semaphore(
                            semaphore, operation_id, parent_phase_id, feature, config
                        )
                    )
                    layer_tasks.append(task)
                
                # Wait for all features in this layer to complete
                await asyncio.gather(*layer_tasks)
                
                # Emit layer completion event
                await self._event_queue.emit(
                    ResourceEventTypes.PHASE_COORDINATION_EVENT.value,
                    {
                        "event_type": "parallel_features_layer_completed",
                        "operation_id": operation_id,
                        "layer_index": layer_idx,
                        "feature_count": len(layer),
                        "timestamp": datetime.now().isoformat()
                    }
                )
            
            # Mark operation as completed
            operation["status"] = "completed"
            operation["end_time"] = datetime.now().isoformat()
            
            # Determine final status
            if len(operation["failed_features"]) > 0:
                if len(operation["completed_features"]) > 0:
                    operation["status"] = "partial_failure"
                else:
                    operation["status"] = "failed"
            
            # Calculate completion metrics
            total_count = operation["feature_count"]
            completed_count = len(operation["completed_features"])
            failed_count = len(operation["failed_features"])
            success_rate = completed_count / total_count if total_count > 0 else 0
            
            # Record final metric
            await self._metrics_manager.record_metric(
                "phase_two:parallel_features:completed",
                success_rate,
                metadata={
                    "operation_id": operation_id,
                    "component_id": operation["component_id"],
                    "feature_count": total_count,
                    "completed_count": completed_count,
                    "failed_count": failed_count,
                    "duration_ms": (datetime.fromisoformat(operation["end_time"]) - 
                                    datetime.fromisoformat(operation["start_time"])).total_seconds() * 1000
                }
            )
            
            # Emit operation completion event
            await self._event_queue.emit(
                ResourceEventTypes.PHASE_COORDINATION_EVENT.value,
                {
                    "event_type": "parallel_feature_development_completed",
                    "operation_id": operation_id,
                    "component_id": operation["component_id"],
                    "status": operation["status"],
                    "feature_count": total_count,
                    "completed_count": completed_count,
                    "failed_count": failed_count,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing features for operation {operation_id}: {str(e)}")
            
            # Mark operation as failed
            operation["status"] = "failed"
            operation["end_time"] = datetime.now().isoformat()
            operation["error"] = str(e)
            
            # Update pending features as failed
            for feature_id in operation["pending_features"] + operation["in_progress_features"]:
                self._feature_statuses[feature_id]["status"] = "failed"
                self._feature_statuses[feature_id]["error"] = str(e)
                self._feature_statuses[feature_id]["end_time"] = datetime.now().isoformat()
                
                # Move to failed features
                if feature_id in operation["pending_features"]:
                    operation["pending_features"].remove(feature_id)
                if feature_id in operation["in_progress_features"]:
                    operation["in_progress_features"].remove(feature_id)
                if feature_id not in operation["failed_features"]:
                    operation["failed_features"].append(feature_id)
            
            # Record failure metric
            await self._metrics_manager.record_metric(
                "phase_two:parallel_features:failed",
                1.0,
                metadata={
                    "operation_id": operation_id,
                    "component_id": operation["component_id"],
                    "error": str(e),
                    "feature_count": operation["feature_count"],
                    "completed_count": len(operation["completed_features"]),
                    "failed_count": len(operation["failed_features"])
                }
            )
            
            # Emit operation failed event
            await self._event_queue.emit(
                ResourceEventTypes.PHASE_COORDINATION_EVENT.value,
                {
                    "event_type": "parallel_feature_development_failed",
                    "operation_id": operation_id,
                    "component_id": operation["component_id"],
                    "error": str(e),
                    "feature_count": operation["feature_count"],
                    "completed_count": len(operation["completed_features"]),
                    "failed_count": len(operation["failed_features"]),
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    async def _process_feature_with_semaphore(self,
                                            semaphore: asyncio.Semaphore,
                                            operation_id: str,
                                            parent_phase_id: str,
                                            feature: Dict[str, Any],
                                            config: Dict[str, Any]) -> None:
        """
        Process a feature with a semaphore for concurrency control with thread boundary enforcement.
        
        Args:
            semaphore: Semaphore for concurrency control
            operation_id: ID of the operation
            parent_phase_id: ID of the parent phase
            feature: Feature definition
            config: Configuration for feature development
        """
        # Log thread information for debugging
        current_thread_id = threading.get_ident()
        logger.debug(f"Processing feature {feature['id']} in thread {current_thread_id}")
        
        # Verify thread has the right semaphore
        with self._semaphore_lock:
            if current_thread_id not in self._feature_semaphores:
                logger.warning(f"Thread {current_thread_id} missing semaphore, creating new one")
                self._feature_semaphores[current_thread_id] = asyncio.Semaphore(self._max_concurrent_features)
                semaphore = self._feature_semaphores[current_thread_id]
        
        # Use the semaphore to limit concurrency
        async with semaphore:
            # Process the feature in its own task to ensure thread safety
            await self._process_single_feature(operation_id, parent_phase_id, feature, config)
    
    async def _process_single_feature(self,
                                    operation_id: str,
                                    parent_phase_id: str,
                                    feature: Dict[str, Any],
                                    config: Dict[str, Any]) -> None:
        """
        Process a single feature.
        
        Args:
            operation_id: ID of the operation
            parent_phase_id: ID of the parent phase
            feature: Feature definition
            config: Configuration for feature development
        """
        feature_id = feature["id"]
        operation = self._active_operations[operation_id]
        
        try:
            # Mark feature as in progress
            self._feature_statuses[feature_id]["status"] = "in_progress"
            self._feature_statuses[feature_id]["start_time"] = datetime.now().isoformat()
            
            # Move from pending to in progress
            if feature_id in operation["pending_features"]:
                operation["pending_features"].remove(feature_id)
            operation["in_progress_features"].append(feature_id)
            
            # Emit feature started event
            await self._event_queue.emit(
                ResourceEventTypes.PHASE_COORDINATION_EVENT.value,
                {
                    "event_type": "feature_development_started",
                    "operation_id": operation_id,
                    "feature_id": feature_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Prepare feature-specific config
            feature_config = config.copy()
            feature_config["parent_operation_id"] = operation_id
            feature_config["feature_id"] = feature_id
            
            # Initiate Phase Three for this feature
            result = await self._phase_coordination.coordinate_nested_execution(
                parent_phase_id,
                PhaseType.THREE,
                {"feature": feature},
                feature_config
            )
            
            # Update feature status
            end_time = datetime.now().isoformat()
            
            if "error" in result:
                # Feature failed
                self._feature_statuses[feature_id].update({
                    "status": "failed",
                    "error": result["error"],
                    "end_time": end_time
                })
                
                # Move from in progress to failed
                operation["in_progress_features"].remove(feature_id)
                operation["failed_features"].append(feature_id)
                
                # Record failure metric
                await self._metrics_manager.record_metric(
                    "phase_two:feature_development:failed",
                    0.0,
                    metadata={
                        "operation_id": operation_id,
                        "feature_id": feature_id,
                        "error": result["error"],
                        "duration_ms": (datetime.fromisoformat(end_time) - 
                                       datetime.fromisoformat(self._feature_statuses[feature_id]["start_time"])).total_seconds() * 1000
                    }
                )
                
                # Emit feature failed event
                await self._event_queue.emit(
                    ResourceEventTypes.PHASE_COORDINATION_EVENT.value,
                    {
                        "event_type": "feature_development_failed",
                        "operation_id": operation_id,
                        "feature_id": feature_id,
                        "error": result["error"],
                        "timestamp": end_time
                    }
                )
            else:
                # Feature completed successfully
                self._feature_statuses[feature_id].update({
                    "status": "completed",
                    "result": result,
                    "end_time": end_time
                })
                
                # Move from in progress to completed
                operation["in_progress_features"].remove(feature_id)
                operation["completed_features"].append(feature_id)
                
                # Record success metric
                await self._metrics_manager.record_metric(
                    "phase_two:feature_development:completed",
                    1.0,
                    metadata={
                        "operation_id": operation_id,
                        "feature_id": feature_id,
                        "duration_ms": (datetime.fromisoformat(end_time) - 
                                       datetime.fromisoformat(self._feature_statuses[feature_id]["start_time"])).total_seconds() * 1000
                    }
                )
                
                # Emit feature completed event
                await self._event_queue.emit(
                    ResourceEventTypes.PHASE_COORDINATION_EVENT.value,
                    {
                        "event_type": "feature_development_completed",
                        "operation_id": operation_id,
                        "feature_id": feature_id,
                        "timestamp": end_time
                    }
                )
            
        except Exception as e:
            logger.error(f"Error processing feature {feature_id} for operation {operation_id}: {str(e)}")
            
            # Update feature status
            self._feature_statuses[feature_id].update({
                "status": "failed",
                "error": str(e),
                "end_time": datetime.now().isoformat()
            })
            
            # Move from in progress to failed
            if feature_id in operation["in_progress_features"]:
                operation["in_progress_features"].remove(feature_id)
            operation["failed_features"].append(feature_id)
            
            # Record failure metric
            await self._metrics_manager.record_metric(
                "phase_two:feature_development:failed",
                0.0,
                metadata={
                    "operation_id": operation_id,
                    "feature_id": feature_id,
                    "error": str(e),
                    "duration_ms": (datetime.now() - 
                                   datetime.fromisoformat(self._feature_statuses[feature_id]["start_time"])).total_seconds() * 1000
                }
            )
            
            # Emit feature failed event
            await self._event_queue.emit(
                ResourceEventTypes.PHASE_COORDINATION_EVENT.value,
                {
                    "event_type": "feature_development_failed",
                    "operation_id": operation_id,
                    "feature_id": feature_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    def _analyze_dependencies(self,
                            features: List[Dict[str, Any]]) -> Tuple[Dict[str, Set[str]], List[str]]:
        """
        Analyze dependencies between features.
        
        Args:
            features: List of feature definitions
            
        Returns:
            Tuple containing dependency graph and execution order
        """
        # Create dependency graph
        dependency_graph: Dict[str, Set[str]] = {}
        reverse_graph: Dict[str, Set[str]] = {}
        
        # Initialize graphs
        for feature in features:
            feature_id = feature["id"]
            dependency_graph[feature_id] = set()
            reverse_graph[feature_id] = set()
        
        # Fill dependency graph
        for feature in features:
            feature_id = feature["id"]
            dependencies = feature.get("dependencies", [])
            
            for dep_id in dependencies:
                if dep_id in dependency_graph:
                    dependency_graph[feature_id].add(dep_id)
                    reverse_graph[dep_id].add(feature_id)
                else:
                    logger.warning(f"Feature {feature_id} depends on unknown feature {dep_id}")
        
        # Use topological sort for execution order
        execution_order = self._topological_sort(dependency_graph)
        
        return dependency_graph, execution_order
    
    def _topological_sort(self, graph: Dict[str, Set[str]]) -> List[str]:
        """
        Perform topological sort to determine execution order.
        
        Args:
            graph: Dependency graph
            
        Returns:
            List of nodes in topological order
        """
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(node):
            # Check for cycles
            if node in temp_visited:
                cycle_nodes = list(temp_visited)
                msg = f"Dependency cycle detected: {' -> '.join(cycle_nodes + [node])}"
                logger.error(msg)
                raise ValueError(msg)
            
            # Skip if already visited
            if node in visited:
                return
            
            # Mark as temporarily visited
            temp_visited.add(node)
            
            # Visit dependencies
            for dependency in graph[node]:
                visit(dependency)
            
            # Mark as visited
            temp_visited.remove(node)
            visited.add(node)
            
            # Add to result
            order.append(node)
        
        # Visit all nodes
        for node in graph:
            if node not in visited:
                visit(node)
        
        # Reverse to get execution order
        return list(reversed(order))
    
    def _get_dependency_layers(self,
                             execution_order: List[str],
                             dependency_graph: Dict[str, Set[str]]) -> List[List[str]]:
        """
        Group features into layers for parallel execution.
        
        Args:
            execution_order: Topological sort of features
            dependency_graph: Dependency graph
            
        Returns:
            List of layers (each layer is a list of feature IDs)
        """
        # If we're using level-based resolution
        if self._dependency_resolution_mode == "level":
            # Implementation for level-based resolution
            layers = []
            remaining = set(execution_order)
            
            while remaining:
                # Features with no dependencies or all dependencies processed
                current_layer = []
                
                for feature_id in execution_order:
                    if feature_id not in remaining:
                        # Already processed
                        continue
                    
                    # Check if all dependencies are processed
                    dependencies = dependency_graph.get(feature_id, set())
                    if all(dep not in remaining for dep in dependencies):
                        current_layer.append(feature_id)
                
                # Add layer
                layers.append(current_layer)
                
                # Remove processed features
                for feature_id in current_layer:
                    remaining.remove(feature_id)
                
            return layers
        else:
            # Default to topological grouping
            # Group features with the same predecessors together
            layers = []
            processed = set()
            
            for feature_id in execution_order:
                # Find layer where all dependencies are already processed
                layer_idx = 0
                
                while layer_idx < len(layers):
                    # Check if any dependency is in this layer
                    layer = layers[layer_idx]
                    dependencies = dependency_graph.get(feature_id, set())
                    
                    if any(dep in layer for dep in dependencies):
                        # Can't add to this layer, try next
                        layer_idx += 1
                    else:
                        # Can add to this layer
                        break
                
                # Add to the appropriate layer
                if layer_idx < len(layers):
                    layers[layer_idx].append(feature_id)
                else:
                    # Create a new layer
                    layers.append([feature_id])
                
                # Mark as processed
                processed.add(feature_id)
            
            return layers
    
    def _aggregate_implementations(self, component_id: str, implementations: Dict[str, str]) -> str:
        """
        Aggregate feature implementations into a component implementation.
        
        Args:
            component_id: ID of the component
            implementations: Dictionary of feature implementations
            
        Returns:
            Aggregated implementation
        """
        # Start with a header
        result = [
            f"# Component: {component_id}",
            f"# Generated: {datetime.now().isoformat()}",
            f"# Features: {len(implementations)}",
            ""
        ]
        
        # Collect imports
        imports = set()
        for impl in implementations.values():
            for line in impl.splitlines():
                if line.strip().startswith(("import ", "from ")):
                    imports.add(line)
        
        # Add imports section
        if imports:
            result.append("# Imports")
            for imp in sorted(imports):
                result.append(imp)
            result.append("")
        
        # Add feature implementations
        for feature_id, impl in implementations.items():
            # Add feature header
            result.append(f"# Feature: {feature_id}")
            
            # Add implementation without import lines
            impl_lines = [
                line for line in impl.splitlines()
                if not line.strip().startswith(("import ", "from "))
            ]
            
            result.extend(impl_lines)
            result.append("")  # Empty line between features
        
        return "\n".join(result)