"""
Phase Three Delegation Interface
==============================

This module provides the interface for delegating component implementations
and feature definitions to Phase Three.
"""

import logging
import asyncio
import uuid
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta

from resources import (
    StateManager,
    MetricsManager,
    EventQueue,
    PhaseCoordinationIntegration,
    PhaseType,
    ResourceType,
    ErrorHandler
)

from phase_three import PhaseThreeInterface

from phase_two.delegation.mapper import ComponentToFeatureMapper
from phase_two.delegation.events import (
    DelegationEventHandler,
    DelegationEventType,
    DelegationErrorType
)
from phase_two.delegation.state import (
    DelegationStateTracker,
    DelegationState
)

logger = logging.getLogger(__name__)

class PhaseThreeDelegationInterface:
    """
    Interface for delegating component definitions to Phase Three.
    
    This class is responsible for:
    1. Providing a clean API for delegating component definitions to Phase Three
    2. Managing async methods for status checking
    3. Handling result retrieval
    4. Aggregating feature implementations for component implementation
    """
    
    def __init__(self, 
                event_queue: EventQueue,
                state_manager: StateManager,
                metrics_manager: MetricsManager,
                phase_three: PhaseThreeInterface,
                phase_coordination: PhaseCoordinationIntegration,
                error_handler: ErrorHandler,
                mapper: Optional[ComponentToFeatureMapper] = None,
                event_handler: Optional[DelegationEventHandler] = None,
                state_tracker: Optional[DelegationStateTracker] = None):
        """
        Initialize the PhaseThreeDelegationInterface.
        
        Args:
            event_queue: EventQueue instance for event emission
            state_manager: StateManager instance for state persistence
            metrics_manager: MetricsManager instance for metrics recording
            phase_three: PhaseThreeInterface instance
            phase_coordination: PhaseCoordinationIntegration instance
            error_handler: ErrorHandler instance
            mapper: Optional ComponentToFeatureMapper instance (created if not provided)
            event_handler: Optional DelegationEventHandler instance (created if not provided)
            state_tracker: Optional DelegationStateTracker instance (created if not provided)
        """
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._metrics_manager = metrics_manager
        self._phase_three = phase_three
        self._phase_coordination = phase_coordination
        self._error_handler = error_handler
        
        # Create mapper if not provided
        self._mapper = mapper or ComponentToFeatureMapper(
            state_manager, metrics_manager, event_queue
        )
        
        # Create event handler if not provided
        self._event_handler = event_handler or DelegationEventHandler(
            event_queue, state_manager
        )
        
        # Create state tracker if not provided
        self._state_tracker = state_tracker or DelegationStateTracker(
            state_manager, metrics_manager
        )
        
        # Dictionary to store active delegations with timers
        self._active_delegations: Dict[str, asyncio.Task] = {}
        
        # Maximum wait time for delegation completion in seconds
        self._max_wait_time = 3600  # 1 hour
    
    async def delegate_component(self, 
                               component_id: str,
                               component_definition: Dict[str, Any],
                               operation_id: Optional[str] = None,
                               wait_for_completion: bool = False,
                               timeout_seconds: Optional[int] = None) -> Dict[str, Any]:
        """
        Delegate a component to Phase Three for implementation.
        
        Args:
            component_id: ID of the component
            component_definition: Component definition including requirements and features
            operation_id: Optional operation ID for tracking (generated if not provided)
            wait_for_completion: Whether to wait for delegation completion
            timeout_seconds: Optional timeout in seconds (defaults to 1 hour)
            
        Returns:
            Dictionary with delegation information
        """
        # Generate operation ID if not provided
        if not operation_id:
            operation_id = f"delegation_{component_id}_{uuid.uuid4().hex[:8]}"
            
        # Generate delegation ID
        delegation_id = f"delegation_{component_id}_{int(datetime.now().timestamp())}"
        
        try:
            # Extract features from component definition
            features = await self._mapper.extract_features(component_definition)
            
            # Validate features
            is_valid, validation_errors = await self._mapper.validate_features(features)
            if not is_valid:
                error_msg = f"Feature validation failed: {validation_errors}"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "delegation_id": delegation_id,
                    "operation_id": operation_id,
                    "error": error_msg,
                    "error_type": DelegationErrorType.INVALID_FEATURE.value,
                    "validation_errors": validation_errors
                }
            
            # Establish feature dependencies if component has dependencies
            if "dependencies" in component_definition:
                feature_dependencies = await self._mapper.establish_feature_dependencies(
                    component_id, component_definition.get("dependencies", [])
                )
                # Add dependencies to features
                for feature in features:
                    feature_id = feature["id"]
                    if feature_id in feature_dependencies:
                        feature["dependencies"] = feature_dependencies[feature_id]
            
            # Add component metadata to features
            features = await self._mapper.add_component_metadata(features, component_definition)
            
            # Register delegation with state tracker
            feature_ids = [feature["id"] for feature in features]
            await self._state_tracker.register_delegation(delegation_id, component_id, feature_ids)
            
            # Emit delegation initiated event
            await self._event_handler.emit_delegation_initiated(
                delegation_id, component_id, features, operation_id
            )
            
            # Update delegation state to initiated
            await self._state_tracker.update_delegation_state(
                delegation_id, DelegationState.INITIATED
            )
            
            # Start delegation process
            delegation_task = asyncio.create_task(
                self._process_delegation(delegation_id, component_id, features, operation_id)
            )
            
            # Store active delegation
            self._active_delegations[delegation_id] = delegation_task
            
            # Record metric
            await self._metrics_manager.record_metric(
                "phase_two:delegation:component_delegated",
                1.0,
                metadata={
                    "delegation_id": delegation_id,
                    "component_id": component_id,
                    "operation_id": operation_id,
                    "feature_count": len(features)
                }
            )
            
            # Wait for completion if requested
            if wait_for_completion:
                # Use provided timeout or default
                timeout = timeout_seconds or self._max_wait_time
                try:
                    await asyncio.wait_for(delegation_task, timeout=timeout)
                    
                    # Get final delegation status
                    delegation_status = await self._state_tracker.get_delegation_status(delegation_id)
                    
                    return {
                        "status": "complete",
                        "delegation_id": delegation_id,
                        "operation_id": operation_id,
                        "delegation_status": delegation_status
                    }
                except asyncio.TimeoutError:
                    logger.warning(f"Delegation {delegation_id} timed out after {timeout} seconds")
                    return {
                        "status": "timeout",
                        "delegation_id": delegation_id,
                        "operation_id": operation_id,
                        "message": f"Delegation timed out after {timeout} seconds"
                    }
            
            # Return delegation information
            return {
                "status": "initiated",
                "delegation_id": delegation_id,
                "operation_id": operation_id,
                "feature_count": len(features)
            }
            
        except Exception as e:
            logger.error(f"Error delegating component {component_id}: {str(e)}")
            
            # Record error
            await self._error_handler.record_error(
                error=e,
                source="phase_two_delegation",
                context={
                    "delegation_id": delegation_id,
                    "component_id": component_id,
                    "operation_id": operation_id
                }
            )
            
            # Record metric
            await self._metrics_manager.record_metric(
                "phase_two:delegation:error",
                1.0,
                metadata={
                    "delegation_id": delegation_id,
                    "component_id": component_id,
                    "operation_id": operation_id,
                    "error": str(e)
                }
            )
            
            return {
                "status": "error",
                "delegation_id": delegation_id,
                "operation_id": operation_id,
                "error": str(e),
                "error_type": DelegationErrorType.UNKNOWN_ERROR.value
            }
    
    async def get_delegation_status(self, delegation_id: str) -> Dict[str, Any]:
        """
        Get the status of a delegation operation.
        
        Args:
            delegation_id: ID of the delegation operation
            
        Returns:
            Dictionary with delegation status information
        """
        status = await self._state_tracker.get_delegation_status(delegation_id)
        if not status:
            return {
                "status": "not_found",
                "delegation_id": delegation_id,
                "message": f"Delegation {delegation_id} not found"
            }
            
        return {
            "status": "found",
            "delegation_id": delegation_id,
            "delegation_status": status
        }
    
    async def get_component_status(self, component_id: str) -> Dict[str, Any]:
        """
        Get the delegation status for a component.
        
        Args:
            component_id: ID of the component
            
        Returns:
            Dictionary with delegation status information
        """
        status = await self._state_tracker.get_component_delegation_status(component_id)
        if not status:
            return {
                "status": "not_found",
                "component_id": component_id,
                "message": f"No delegation found for component {component_id}"
            }
            
        return {
            "status": "found",
            "component_id": component_id,
            "delegation_status": status
        }
    
    async def get_delegation_result(self, delegation_id: str) -> Dict[str, Any]:
        """
        Get the result of a delegation operation.
        
        Args:
            delegation_id: ID of the delegation operation
            
        Returns:
            Dictionary with delegation result
        """
        # Get delegation status
        status = await self._state_tracker.get_delegation_status(delegation_id)
        if not status:
            return {
                "status": "not_found",
                "delegation_id": delegation_id,
                "message": f"Delegation {delegation_id} not found"
            }
            
        # Check if delegation is completed
        if status["state"] not in ["COMPLETED", "PARTIAL", "FAILED"]:
            return {
                "status": "in_progress",
                "delegation_id": delegation_id,
                "delegation_status": status,
                "message": f"Delegation {delegation_id} is still in progress"
            }
            
        # Get component ID
        component_id = status["component_id"]
        
        # Get implemented features from Phase Three
        implemented_features = []
        failed_features = []
        for feature_id in status["feature_ids"]:
            try:
                # Check if feature is in completed features
                if feature_id in status["completed_features"]:
                    feature_status = await self._phase_three.get_feature_status(feature_id)
                    if feature_status:
                        implemented_features.append(feature_status)
                elif feature_id in status["failed_features"]:
                    # Get failure info
                    failed_features.append({"feature_id": feature_id, "error": status.get("error_message")})
            except Exception as e:
                logger.error(f"Error getting feature status for {feature_id}: {str(e)}")
                failed_features.append({"feature_id": feature_id, "error": str(e)})
        
        # Construct component implementation from features
        implementation = None
        if implemented_features:
            implementation = self._aggregate_feature_implementations(component_id, implemented_features)
        
        # Return result
        result = {
            "status": status["state"].lower(),
            "delegation_id": delegation_id,
            "component_id": component_id,
            "implemented_features": [f["feature_id"] for f in implemented_features],
            "failed_features": [f["feature_id"] for f in failed_features],
            "feature_details": {
                "implemented": implemented_features,
                "failed": failed_features
            }
        }
        
        if implementation:
            result["implementation"] = implementation
            
        return result
    
    async def cancel_delegation(self, delegation_id: str, reason: str) -> Dict[str, Any]:
        """
        Cancel a delegation operation.
        
        Args:
            delegation_id: ID of the delegation operation
            reason: Reason for cancellation
            
        Returns:
            Dictionary with cancellation result
        """
        # Get delegation status
        status = await self._state_tracker.get_delegation_status(delegation_id)
        if not status:
            return {
                "status": "not_found",
                "delegation_id": delegation_id,
                "message": f"Delegation {delegation_id} not found"
            }
            
        # Check if delegation can be cancelled
        if status["state"] in ["COMPLETED", "FAILED", "CANCELLED"]:
            return {
                "status": "invalid_state",
                "delegation_id": delegation_id,
                "message": f"Delegation {delegation_id} is already in final state: {status['state']}"
            }
            
        # Get component ID and features
        component_id = status["component_id"]
        all_features = status["feature_ids"]
        completed_features = status["completed_features"]
        
        # Cancel active task if exists
        if delegation_id in self._active_delegations:
            self._active_delegations[delegation_id].cancel()
            del self._active_delegations[delegation_id]
        
        # Update state to cancelled
        await self._state_tracker.update_delegation_state(
            delegation_id, DelegationState.CANCELLED
        )
        
        # Get cancelled features (all features that aren't completed)
        cancelled_features = [f for f in all_features if f not in completed_features]
        
        # Emit cancellation event
        await self._event_handler.emit_delegation_cancelled(
            delegation_id, component_id, reason, cancelled_features, completed_features
        )
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:delegation:cancelled",
            1.0,
            metadata={
                "delegation_id": delegation_id,
                "component_id": component_id,
                "reason": reason,
                "completed_count": len(completed_features),
                "cancelled_count": len(cancelled_features)
            }
        )
        
        return {
            "status": "cancelled",
            "delegation_id": delegation_id,
            "component_id": component_id,
            "reason": reason,
            "completed_features": completed_features,
            "cancelled_features": cancelled_features
        }
    
    async def cleanup_completed_delegations(self, max_age_days: int = 7) -> Dict[str, Any]:
        """
        Clean up completed delegation records.
        
        Args:
            max_age_days: Maximum age of completed delegations to keep, in days
            
        Returns:
            Dictionary with cleanup result
        """
        count = await self._state_tracker.cleanup_old_delegations(max_age_days)
        
        return {
            "status": "success",
            "cleaned_up_count": count,
            "max_age_days": max_age_days
        }
    
    async def _process_delegation(self,
                                delegation_id: str,
                                component_id: str,
                                features: List[Dict[str, Any]],
                                operation_id: str) -> None:
        """
        Process a delegation operation.
        
        This method handles the actual delegation to Phase Three, tracking progress,
        and updating delegation state.
        
        Args:
            delegation_id: ID of the delegation operation
            component_id: ID of the component
            features: List of feature definitions
            operation_id: Operation ID for tracking
        """
        logger.info(f"Processing delegation {delegation_id} for component {component_id}")
        
        try:
            # Update delegation state to in progress
            await self._state_tracker.update_delegation_state(
                delegation_id, DelegationState.IN_PROGRESS
            )
            
            # Start feature cultivation in Phase Three
            phase_three_config = {
                "operation_id": operation_id,
                "component_id": component_id,
                "delegation_id": delegation_id,
                "handlers": ["phase_two_to_three", "phase_three_to_four"]
            }
            
            # Start the delegation to Phase Three
            try:
                # Determine if we should use coordination or direct interface
                if self._phase_coordination:
                    # Use coordination for nested phase execution
                    logger.info(f"Using phase coordination for delegation {delegation_id}")
                    
                    # Get phase type (for nested calls from Phase Two to Phase Three)
                    phase_two_id = await self._phase_coordination.get_current_phase_id()
                    
                    # Prepare input data
                    phase_three_input = {
                        "features": features,
                        "component_id": component_id,
                        "delegation_id": delegation_id
                    }
                    
                    # Execute nested phase call
                    result = await self._phase_coordination.coordinate_nested_execution(
                        phase_two_id,  # Parent phase ID
                        PhaseType.THREE,  # Target phase type
                        phase_three_input,  # Input data
                        phase_three_config  # Configuration
                    )
                else:
                    # Use direct Phase Three interface
                    logger.info(f"Using direct Phase Three interface for delegation {delegation_id}")
                    result = await self._phase_three.start_feature_cultivation(
                        features=features,
                        operation_id=operation_id
                    )
            except Exception as e:
                logger.error(f"Error starting feature cultivation for delegation {delegation_id}: {str(e)}")
                # Update state to failed
                await self._state_tracker.update_delegation_state(
                    delegation_id, 
                    DelegationState.FAILED,
                    {"error_message": str(e)}
                )
                
                # Emit failure event
                await self._event_handler.emit_delegation_failed(
                    delegation_id,
                    component_id,
                    DelegationErrorType.PHASE_THREE_UNAVAILABLE,
                    str(e),
                    [],  # failed features (all)
                    [],  # completed features (none)
                    operation_id=operation_id
                )
                
                # Record error
                await self._error_handler.record_error(
                    error=e,
                    source="phase_two_delegation",
                    context={
                        "delegation_id": delegation_id,
                        "component_id": component_id,
                        "operation_id": operation_id
                    }
                )
                
                return
            
            # Get feature IDs
            feature_ids = [feature["id"] for feature in features]
            
            # Check result for immediate errors
            if "error" in result:
                logger.error(f"Error in Phase Three cultivation for delegation {delegation_id}: {result['error']}")
                # Update state to failed
                await self._state_tracker.update_delegation_state(
                    delegation_id, 
                    DelegationState.FAILED,
                    {"error_message": result["error"]}
                )
                
                # Emit failure event
                await self._event_handler.emit_delegation_failed(
                    delegation_id,
                    component_id,
                    DelegationErrorType.FEATURE_CREATION_FAILED,
                    result["error"],
                    feature_ids,  # failed features (all)
                    [],  # completed features (none)
                    operation_id=operation_id
                )
                
                return
            
            # Extract operation ID from result if available
            if "operation_id" in result:
                phase_three_operation_id = result["operation_id"]
            else:
                phase_three_operation_id = operation_id
            
            # Wait for feature cultivation to complete
            # This involves polling Phase Three for status
            completed_features = []
            failed_features = []
            max_wait_time = self._max_wait_time
            poll_interval = 5  # seconds
            total_wait_time = 0
            
            while total_wait_time < max_wait_time:
                # Check if task was cancelled
                if asyncio.current_task().cancelled():
                    logger.info(f"Delegation task {delegation_id} was cancelled")
                    return
                
                # Get cultivation status from Phase Three
                try:
                    if hasattr(self._phase_three, "get_cultivation_status"):
                        # Using direct phase three interface
                        cultivation_status = await self._phase_three.get_cultivation_status(
                            phase_three_operation_id
                        )
                    else:
                        # Using coordination - result already contains the status
                        cultivation_status = result.get("status", {})
                        
                    # Check if cultivation is complete
                    if cultivation_status.get("status") == "completed":
                        logger.info(f"Phase Three cultivation completed for delegation {delegation_id}")
                        
                        # Get completed features
                        completed_features = cultivation_status.get("completed_features", [])
                        failed_features = cultivation_status.get("failed_features", [])
                        
                        # Update feature statuses
                        for feature_id in feature_ids:
                            if feature_id in completed_features:
                                await self._state_tracker.update_feature_status(feature_id, True)
                            elif feature_id in failed_features:
                                await self._state_tracker.update_feature_status(
                                    feature_id, False, 
                                    f"Feature implementation failed in Phase Three"
                                )
                        
                        # Determine final state
                        if len(completed_features) == len(feature_ids):
                            final_state = DelegationState.COMPLETED
                        elif len(completed_features) > 0:
                            final_state = DelegationState.PARTIAL
                        else:
                            final_state = DelegationState.FAILED
                        
                        # Update delegation state
                        await self._state_tracker.update_delegation_state(
                            delegation_id, final_state
                        )
                        
                        # Calculate progress percentage
                        progress_percentage = len(completed_features) / len(feature_ids) * 100 if feature_ids else 0
                        
                        # Emit appropriate event
                        if final_state == DelegationState.COMPLETED:
                            await self._event_handler.emit_delegation_completed(
                                delegation_id,
                                component_id,
                                completed_features,
                                cultivation_status,
                                operation_id
                            )
                        elif final_state == DelegationState.PARTIAL:
                            # First emit progress
                            await self._event_handler.emit_delegation_progress(
                                delegation_id,
                                component_id,
                                progress_percentage,
                                completed_features,
                                failed_features,
                                f"Partial completion with {len(completed_features)} of {len(feature_ids)} features",
                                operation_id
                            )
                            
                            # Then emit completion with partial state
                            await self._event_handler.emit_delegation_completed(
                                delegation_id,
                                component_id,
                                completed_features,
                                cultivation_status,
                                operation_id
                            )
                        else:  # FAILED
                            await self._event_handler.emit_delegation_failed(
                                delegation_id,
                                component_id,
                                DelegationErrorType.FEATURE_IMPLEMENTATION_FAILED,
                                f"All features failed implementation in Phase Three",
                                failed_features,
                                completed_features,
                                operation_id=operation_id
                            )
                        
                        # Break out of the loop
                        break
                    else:
                        # Cultivation still in progress
                        # Calculate progress
                        progress = cultivation_status.get("progress", {})
                        progress_percentage = progress.get("percentage", 0)
                        completed = progress.get("completed_features", [])
                        pending = [f for f in feature_ids if f not in completed]
                        
                        # Update feature statuses
                        for feature_id in completed:
                            await self._state_tracker.update_feature_status(feature_id, True)
                        
                        # Emit progress event
                        await self._event_handler.emit_delegation_progress(
                            delegation_id,
                            component_id,
                            progress_percentage,
                            completed,
                            pending,
                            f"In progress: {len(completed)} of {len(feature_ids)} features completed",
                            operation_id
                        )
                        
                except Exception as e:
                    logger.error(f"Error checking cultivation status for delegation {delegation_id}: {str(e)}")
                    # Don't fail the delegation here, just log the error and continue polling
                
                # Wait for next poll
                await asyncio.sleep(poll_interval)
                total_wait_time += poll_interval
                
                # Increase poll interval gradually (up to 30 seconds)
                poll_interval = min(poll_interval * 1.5, 30)
            
            # If we get here and haven't broken out of the loop, the delegation timed out
            if total_wait_time >= max_wait_time:
                logger.warning(f"Delegation {delegation_id} timed out after {max_wait_time} seconds")
                
                # Update delegation state to failed
                await self._state_tracker.update_delegation_state(
                    delegation_id, 
                    DelegationState.FAILED,
                    {"error_message": f"Delegation timed out after {max_wait_time} seconds"}
                )
                
                # Emit failure event
                await self._event_handler.emit_delegation_failed(
                    delegation_id,
                    component_id,
                    DelegationErrorType.TIMEOUT,
                    f"Delegation timed out after {max_wait_time} seconds",
                    [f for f in feature_ids if f not in completed_features],  # failed features
                    completed_features,  # completed features
                    operation_id=operation_id
                )
                
        except asyncio.CancelledError:
            logger.info(f"Delegation task {delegation_id} was cancelled")
            # Clean up task from active delegations
            if delegation_id in self._active_delegations:
                del self._active_delegations[delegation_id]
            raise
            
        except Exception as e:
            logger.error(f"Error processing delegation {delegation_id}: {str(e)}")
            
            # Update delegation state to failed
            await self._state_tracker.update_delegation_state(
                delegation_id, 
                DelegationState.FAILED,
                {"error_message": str(e)}
            )
            
            # Emit failure event
            await self._event_handler.emit_delegation_failed(
                delegation_id,
                component_id,
                DelegationErrorType.UNKNOWN_ERROR,
                str(e),
                [f["id"] for f in features],  # all features failed
                [],  # no features completed
                operation_id=operation_id
            )
            
            # Record error
            await self._error_handler.record_error(
                error=e,
                source="phase_two_delegation",
                context={
                    "delegation_id": delegation_id,
                    "component_id": component_id,
                    "operation_id": operation_id
                }
            )
            
        finally:
            # Clean up task from active delegations
            if delegation_id in self._active_delegations:
                del self._active_delegations[delegation_id]
    
    def _aggregate_feature_implementations(self, component_id: str, 
                                        features: List[Dict[str, Any]]) -> str:
        """
        Aggregate feature implementations into a component implementation.
        
        Args:
            component_id: ID of the component
            features: List of feature status dictionaries with implementations
            
        Returns:
            Aggregated component implementation
        """
        implementation_parts = [
            f"# Component: {component_id}\n"
            f"# Generated by Phase Two Delegation\n"
            f"# Timestamp: {datetime.now().isoformat()}\n"
            f"# Features: {len(features)}\n\n"
        ]
        
        # Add imports section
        imports = set()
        for feature in features:
            if "implementation" in feature:
                # Extract import lines
                impl = feature.get("implementation", "")
                for line in impl.splitlines():
                    if line.strip().startswith(("import ", "from ")):
                        imports.add(line)
        
        if imports:
            implementation_parts.append("# Imports\n")
            for imp in sorted(imports):
                implementation_parts.append(f"{imp}\n")
            implementation_parts.append("\n")
        
        # Add feature implementations
        for feature in features:
            feature_id = feature.get("feature_id", "unknown")
            feature_name = feature.get("feature_name", feature_id)
            implementation = feature.get("implementation", "")
            
            # Remove import lines to avoid duplicates
            impl_lines = implementation.splitlines()
            filtered_lines = [line for line in impl_lines 
                           if not line.strip().startswith(("import ", "from "))]
            filtered_impl = "\n".join(filtered_lines)
            
            implementation_parts.append(f"# Feature: {feature_name} ({feature_id})\n")
            implementation_parts.append(f"{filtered_impl}\n\n")
        
        return "".join(implementation_parts)