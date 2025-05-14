"""
Delegation Recovery Handler
========================

This module provides functionality for recovering from delegation failures,
including retry mechanisms, circuit breakers, and transaction semantics.
"""

import logging
import asyncio
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
import random

from resources import (
    StateManager,
    MetricsManager,
    EventQueue,
    ResourceType,
    ErrorHandler
)

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

class RecoveryStrategy(Enum):
    """Strategies for delegation recovery."""
    RETRY_ALL = "retry_all"                  # Retry all failed features
    RETRY_INDIVIDUAL = "retry_individual"    # Retry specific failed features
    PARTIAL_COMPLETION = "partial_completion"  # Accept partial completion
    CIRCUIT_BREAKER = "circuit_breaker"      # Prevent further delegations for some time
    FALLBACK = "fallback"                    # Use a fallback implementation

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation (allowing calls)
    OPEN = "open"           # Prevention of calls
    HALF_OPEN = "half_open"  # Testing if system has recovered

class DelegationRecoveryHandler:
    """
    Handles recovery strategies for failed delegations.
    
    This class is responsible for:
    1. Implementing strategies for handling failed delegations
    2. Providing retry mechanisms with exponential backoff
    3. Implementing circuit breakers to prevent cascading failures
    4. Providing transaction-like semantics for delegation consistency
    """
    
    def __init__(self,
                event_queue: EventQueue,
                state_manager: StateManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                event_handler: DelegationEventHandler,
                state_tracker: DelegationStateTracker):
        """
        Initialize the DelegationRecoveryHandler.
        
        Args:
            event_queue: EventQueue instance for event emission
            state_manager: StateManager instance for state persistence
            metrics_manager: MetricsManager instance for metrics recording
            error_handler: ErrorHandler instance for error handling
            event_handler: DelegationEventHandler instance for event handling
            state_tracker: DelegationStateTracker instance for state tracking
        """
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._metrics_manager = metrics_manager
        self._error_handler = error_handler
        self._event_handler = event_handler
        self._state_tracker = state_tracker
        
        # Circuit breaker state
        self._circuit_state = CircuitState.CLOSED
        self._circuit_failure_count = 0
        self._circuit_failure_threshold = 5
        self._circuit_reset_time: Optional[datetime] = None
        self._circuit_reset_delay = 60  # seconds
        
        # Retry limits
        self._max_retry_attempts = 3
        self._base_retry_delay = 5  # seconds
        
        # Recovery strategies per error type
        self._strategies_by_error = {
            DelegationErrorType.INVALID_COMPONENT: RecoveryStrategy.CIRCUIT_BREAKER,
            DelegationErrorType.INVALID_FEATURE: RecoveryStrategy.CIRCUIT_BREAKER,
            DelegationErrorType.PHASE_THREE_UNAVAILABLE: RecoveryStrategy.RETRY_ALL,
            DelegationErrorType.FEATURE_CREATION_FAILED: RecoveryStrategy.RETRY_ALL,
            DelegationErrorType.FEATURE_IMPLEMENTATION_FAILED: RecoveryStrategy.RETRY_INDIVIDUAL,
            DelegationErrorType.FEATURE_TESTING_FAILED: RecoveryStrategy.RETRY_INDIVIDUAL,
            DelegationErrorType.TIMEOUT: RecoveryStrategy.RETRY_ALL,
            DelegationErrorType.RESOURCE_EXHAUSTION: RecoveryStrategy.CIRCUIT_BREAKER,
            DelegationErrorType.DEPENDENCY_FAILURE: RecoveryStrategy.PARTIAL_COMPLETION,
            DelegationErrorType.COMMUNICATION_ERROR: RecoveryStrategy.RETRY_ALL,
            DelegationErrorType.UNKNOWN_ERROR: RecoveryStrategy.CIRCUIT_BREAKER
        }
        
        # Retry tracking
        self._retry_counts: Dict[str, int] = {}  # delegation_id -> retry count
        
        # Active recovery tasks
        self._active_recoveries: Dict[str, asyncio.Task] = {}
        
        # Register for failure events
        asyncio.create_task(self._register_for_failures())
    
    async def _register_for_failures(self) -> None:
        """Register for delegation failure events."""
        await self._event_handler.subscribe(
            DelegationEventType.DELEGATION_FAILED,
            self._handle_delegation_failure
        )
        logger.info("Registered for delegation failure events")
    
    async def _handle_delegation_failure(self, event_type: str, payload: Dict[str, Any]) -> None:
        """
        Handle delegation failure event.
        
        Args:
            event_type: Type of event
            payload: Event payload
        """
        # Extract information from payload
        delegation_id = payload.get("delegation_id", "")
        component_id = payload.get("component_id", "")
        error_type_str = payload.get("error_type", "")
        error_message = payload.get("error_message", "")
        failed_features = payload.get("failed_features", [])
        completed_features = payload.get("completed_features", [])
        
        logger.info(f"Handling delegation failure for {delegation_id}: {error_type_str}")
        
        # Convert error type string to enum
        try:
            error_type = DelegationErrorType(error_type_str)
        except (ValueError, KeyError):
            error_type = DelegationErrorType.UNKNOWN_ERROR
        
        # Get recovery strategy for this error type
        strategy = self._strategies_by_error.get(error_type, RecoveryStrategy.CIRCUIT_BREAKER)
        
        # Check if circuit breaker is open
        if self._circuit_state == CircuitState.OPEN:
            logger.warning(f"Circuit breaker is open, no recovery attempted for {delegation_id}")
            
            # Record metric
            await self._metrics_manager.record_metric(
                "phase_two:delegation:recovery:circuit_breaker_blocked",
                1.0,
                metadata={
                    "delegation_id": delegation_id,
                    "component_id": component_id,
                    "error_type": error_type.value
                }
            )
            
            return
        
        # Check retry count
        retry_count = self._retry_counts.get(delegation_id, 0)
        if retry_count >= self._max_retry_attempts:
            logger.warning(f"Max retry attempts ({self._max_retry_attempts}) reached for {delegation_id}")
            
            # Record metric
            await self._metrics_manager.record_metric(
                "phase_two:delegation:recovery:max_retries_reached",
                1.0,
                metadata={
                    "delegation_id": delegation_id,
                    "component_id": component_id,
                    "retry_count": retry_count
                }
            )
            
            # Update circuit breaker
            await self._update_circuit_breaker(True)
            
            return
        
        # Increment retry count
        self._retry_counts[delegation_id] = retry_count + 1
        
        # Start recovery based on strategy
        if strategy == RecoveryStrategy.RETRY_ALL:
            # Start recovery task
            recovery_task = asyncio.create_task(
                self._retry_delegation(
                    delegation_id, component_id, failed_features + completed_features,
                    error_type, error_message, retry_count + 1
                )
            )
            self._active_recoveries[delegation_id] = recovery_task
            
        elif strategy == RecoveryStrategy.RETRY_INDIVIDUAL:
            # Start recovery task for individual features
            recovery_task = asyncio.create_task(
                self._retry_individual_features(
                    delegation_id, component_id, failed_features,
                    error_type, error_message, retry_count + 1
                )
            )
            self._active_recoveries[delegation_id] = recovery_task
            
        elif strategy == RecoveryStrategy.PARTIAL_COMPLETION:
            # Accept partial completion
            await self._handle_partial_completion(
                delegation_id, component_id, failed_features, completed_features,
                error_type, error_message
            )
            
        elif strategy == RecoveryStrategy.CIRCUIT_BREAKER:
            # Activate circuit breaker
            await self._update_circuit_breaker(True)
            
            # Record metric
            await self._metrics_manager.record_metric(
                "phase_two:delegation:recovery:circuit_breaker_activated",
                1.0,
                metadata={
                    "delegation_id": delegation_id,
                    "component_id": component_id,
                    "error_type": error_type.value
                }
            )
            
        elif strategy == RecoveryStrategy.FALLBACK:
            # Use fallback implementation
            await self._use_fallback_implementation(
                delegation_id, component_id, failed_features,
                error_type, error_message
            )
    
    async def _retry_delegation(self,
                             delegation_id: str,
                             component_id: str,
                             features: List[str],
                             error_type: DelegationErrorType,
                             error_message: str,
                             retry_count: int) -> None:
        """
        Retry a delegation operation.
        
        Args:
            delegation_id: ID of the delegation operation
            component_id: ID of the component
            features: List of feature IDs to retry
            error_type: Type of error that caused the failure
            error_message: Error message
            retry_count: Number of retries attempted so far
        """
        try:
            logger.info(f"Retrying delegation {delegation_id} (attempt {retry_count})")
            
            # Calculate retry delay with exponential backoff and jitter
            delay = self._calculate_retry_delay(retry_count)
            next_retry_time = datetime.now() + timedelta(seconds=delay)
            
            # Emit retry event
            await self._event_handler.emit_delegation_retry(
                delegation_id,
                component_id,
                retry_count,
                error_type,
                error_message,
                features,
                RecoveryStrategy.RETRY_ALL.value,
                next_retry_time
            )
            
            # Update delegation state to retrying
            await self._state_tracker.update_delegation_state(
                delegation_id, DelegationState.RETRYING
            )
            
            # Wait for retry delay
            await asyncio.sleep(delay)
            
            # Get delegation status
            status = await self._state_tracker.get_delegation_status(delegation_id)
            if not status:
                logger.error(f"Delegation {delegation_id} not found for retry")
                return
            
            # Check if the delegation should still be retried
            if status["state"] in ["COMPLETED", "CANCELLED"]:
                logger.info(f"Delegation {delegation_id} is already in final state: {status['state']}, skipping retry")
                return
            
            # Get original component definition
            component_def = await self._state_manager.get_state(f"component:{component_id}:definition")
            if not component_def:
                logger.error(f"Component definition not found for {component_id}, cannot retry")
                return
            
            # Get required interfaces
            phase_three = await self._get_phase_three_interface()
            delegation_interface = await self._get_delegation_interface()
            
            if not phase_three or not delegation_interface:
                logger.error("Could not get required interfaces for retry")
                return
            
            # Create new delegation operation
            new_delegation_id = f"{delegation_id}_retry_{retry_count}"
            
            # Update state tracker with new delegation
            feature_ids = features
            await self._state_tracker.register_delegation(new_delegation_id, component_id, feature_ids)
            
            # Update delegation state to initiated
            await self._state_tracker.update_delegation_state(
                new_delegation_id, DelegationState.INITIATED
            )
            
            # Emit delegation initiated event
            await self._event_handler.emit_delegation_initiated(
                new_delegation_id, component_id, [{
                    "id": feature_id
                } for feature_id in feature_ids]
            )
            
            # Delegate component to Phase Three
            result = await delegation_interface.delegate_component(
                component_id,
                component_def,
                wait_for_completion=True,
                timeout_seconds=3600  # 1 hour
            )
            
            # Handle retry result
            if result["status"] in ["complete", "partial"]:
                logger.info(f"Delegation retry {new_delegation_id} completed successfully")
                
                # Update original delegation state
                if "delegation_status" in result:
                    # Copy status from new delegation to original
                    status = result["delegation_status"]
                    await self._state_tracker.update_delegation_state(
                        delegation_id, 
                        DelegationState[status["state"]],
                        {
                            "completed_features": status.get("completed_features", []),
                            "failed_features": status.get("failed_features", []),
                            "progress_percentage": status.get("progress_percentage", 0)
                        }
                    )
                
                # Update circuit breaker
                await self._update_circuit_breaker(False)
                
                # Record metric
                await self._metrics_manager.record_metric(
                    "phase_two:delegation:recovery:retry_succeeded",
                    1.0,
                    metadata={
                        "delegation_id": delegation_id,
                        "component_id": component_id,
                        "retry_count": retry_count
                    }
                )
                
            else:
                logger.warning(f"Delegation retry {new_delegation_id} failed: {result.get('error', 'Unknown error')}")
                
                # Record metric
                await self._metrics_manager.record_metric(
                    "phase_two:delegation:recovery:retry_failed",
                    1.0,
                    metadata={
                        "delegation_id": delegation_id,
                        "component_id": component_id,
                        "retry_count": retry_count,
                        "error": result.get("error", "Unknown error")
                    }
                )
            
        except Exception as e:
            logger.error(f"Error in delegation retry for {delegation_id}: {str(e)}")
            
            # Record error
            await self._error_handler.record_error(
                error=e,
                source="phase_two_delegation_recovery",
                context={
                    "delegation_id": delegation_id,
                    "component_id": component_id,
                    "retry_count": retry_count
                }
            )
            
        finally:
            # Remove from active recoveries
            if delegation_id in self._active_recoveries:
                del self._active_recoveries[delegation_id]
    
    async def _retry_individual_features(self,
                                      delegation_id: str,
                                      component_id: str,
                                      failed_features: List[str],
                                      error_type: DelegationErrorType,
                                      error_message: str,
                                      retry_count: int) -> None:
        """
        Retry individual failed features.
        
        Args:
            delegation_id: ID of the delegation operation
            component_id: ID of the component
            failed_features: List of failed feature IDs
            error_type: Type of error that caused the failure
            error_message: Error message
            retry_count: Number of retries attempted so far
        """
        try:
            logger.info(f"Retrying {len(failed_features)} individual features for delegation {delegation_id} (attempt {retry_count})")
            
            # Calculate retry delay with exponential backoff and jitter
            delay = self._calculate_retry_delay(retry_count)
            next_retry_time = datetime.now() + timedelta(seconds=delay)
            
            # Emit retry event
            await self._event_handler.emit_delegation_retry(
                delegation_id,
                component_id,
                retry_count,
                error_type,
                error_message,
                failed_features,
                RecoveryStrategy.RETRY_INDIVIDUAL.value,
                next_retry_time
            )
            
            # Update delegation state to retrying
            await self._state_tracker.update_delegation_state(
                delegation_id, DelegationState.RETRYING
            )
            
            # Wait for retry delay
            await asyncio.sleep(delay)
            
            # Get delegation status
            status = await self._state_tracker.get_delegation_status(delegation_id)
            if not status:
                logger.error(f"Delegation {delegation_id} not found for retry")
                return
            
            # Check if the delegation should still be retried
            if status["state"] in ["COMPLETED", "CANCELLED"]:
                logger.info(f"Delegation {delegation_id} is already in final state: {status['state']}, skipping retry")
                return
            
            # Get required interfaces
            phase_three = await self._get_phase_three_interface()
            
            if not phase_three:
                logger.error("Could not get required interface for retry")
                return
            
            # Process each failed feature individually
            retry_success_count = 0
            for feature_id in failed_features:
                try:
                    # Get feature definition
                    feature_def = await self._state_manager.get_state(f"feature:{feature_id}:definition")
                    if not feature_def:
                        logger.error(f"Feature definition not found for {feature_id}, skipping retry")
                        continue
                    
                    # Retry feature in Phase Three
                    retry_result = await phase_three.retry_feature(
                        feature_id,
                        feature_def,
                        component_id
                    )
                    
                    # Check result
                    if retry_result.get("status") == "success":
                        logger.info(f"Feature retry succeeded for {feature_id}")
                        await self._state_tracker.update_feature_status(feature_id, True)
                        retry_success_count += 1
                    else:
                        logger.warning(f"Feature retry failed for {feature_id}: {retry_result.get('error', 'Unknown error')}")
                        await self._state_tracker.update_feature_status(
                            feature_id, False, 
                            retry_result.get("error", "Retry failed")
                        )
                        
                except Exception as e:
                    logger.error(f"Error retrying feature {feature_id}: {str(e)}")
                    await self._state_tracker.update_feature_status(
                        feature_id, False, 
                        f"Retry error: {str(e)}"
                    )
            
            # Update circuit breaker based on overall success rate
            if retry_success_count > 0:
                success_rate = retry_success_count / len(failed_features)
                await self._update_circuit_breaker(success_rate < 0.5)
            else:
                await self._update_circuit_breaker(True)
            
            # Record metric
            await self._metrics_manager.record_metric(
                "phase_two:delegation:recovery:individual_retry",
                retry_success_count,
                metadata={
                    "delegation_id": delegation_id,
                    "component_id": component_id,
                    "retry_count": retry_count,
                    "total_features": len(failed_features),
                    "success_count": retry_success_count
                }
            )
            
        except Exception as e:
            logger.error(f"Error in individual feature retry for {delegation_id}: {str(e)}")
            
            # Record error
            await self._error_handler.record_error(
                error=e,
                source="phase_two_delegation_recovery",
                context={
                    "delegation_id": delegation_id,
                    "component_id": component_id,
                    "retry_count": retry_count,
                    "feature_count": len(failed_features)
                }
            )
            
        finally:
            # Remove from active recoveries
            if delegation_id in self._active_recoveries:
                del self._active_recoveries[delegation_id]
    
    async def _handle_partial_completion(self,
                                       delegation_id: str,
                                       component_id: str,
                                       failed_features: List[str],
                                       completed_features: List[str],
                                       error_type: DelegationErrorType,
                                       error_message: str) -> None:
        """
        Handle partial completion of a delegation.
        
        Args:
            delegation_id: ID of the delegation operation
            component_id: ID of the component
            failed_features: List of failed feature IDs
            completed_features: List of completed feature IDs
            error_type: Type of error that caused the failure
            error_message: Error message
        """
        logger.info(f"Handling partial completion for delegation {delegation_id}: {len(completed_features)} completed, {len(failed_features)} failed")
        
        # Update delegation state to partial
        await self._state_tracker.update_delegation_state(
            delegation_id, DelegationState.PARTIAL,
            {
                "completed_features": completed_features,
                "failed_features": failed_features,
                "error_message": error_message
            }
        )
        
        # Calculate completion percentage
        total_features = len(completed_features) + len(failed_features)
        completion_percentage = len(completed_features) / total_features * 100 if total_features > 0 else 0
        
        # Emit partial completion event
        await self._event_handler.emit_delegation_completed(
            delegation_id,
            component_id,
            completed_features,
            {
                "result_summary": {
                    "completed_features": completed_features,
                    "failed_features": failed_features,
                    "completion_percentage": completion_percentage,
                    "error_message": error_message
                }
            }
        )
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:delegation:recovery:partial_completion",
            completion_percentage,
            metadata={
                "delegation_id": delegation_id,
                "component_id": component_id,
                "completed_count": len(completed_features),
                "failed_count": len(failed_features)
            }
        )
    
    async def _use_fallback_implementation(self,
                                        delegation_id: str,
                                        component_id: str,
                                        failed_features: List[str],
                                        error_type: DelegationErrorType,
                                        error_message: str) -> None:
        """
        Use fallback implementation for failed features.
        
        Args:
            delegation_id: ID of the delegation operation
            component_id: ID of the component
            failed_features: List of failed feature IDs
            error_type: Type of error that caused the failure
            error_message: Error message
        """
        logger.info(f"Using fallback implementation for delegation {delegation_id}: {len(failed_features)} failed features")
        
        # Create fallback implementations for failed features
        for feature_id in failed_features:
            # Get feature definition
            feature_def = await self._state_manager.get_state(f"feature:{feature_id}:definition")
            if not feature_def:
                logger.error(f"Feature definition not found for {feature_id}, cannot create fallback")
                continue
            
            # Create fallback implementation
            fallback = self._generate_fallback_implementation(feature_id, feature_def)
            
            # Store fallback implementation
            await self._state_manager.set_state(
                f"feature:{feature_id}:implementation",
                fallback,
                ResourceType.IMPLEMENTATION
            )
            
            # Update feature status
            await self._state_tracker.update_feature_status(feature_id, True)
        
        # Update delegation state
        await self._state_tracker.update_delegation_state(
            delegation_id, DelegationState.COMPLETED
        )
        
        # Get all features for this delegation
        status = await self._state_tracker.get_delegation_status(delegation_id)
        all_features = status.get("feature_ids", []) if status else []
        
        # Emit completion event
        await self._event_handler.emit_delegation_completed(
            delegation_id,
            component_id,
            all_features,  # now all features are considered completed
            {
                "result_summary": {
                    "message": "Completed with fallback implementations",
                    "fallback_count": len(failed_features)
                }
            }
        )
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:delegation:recovery:fallback_used",
            len(failed_features),
            metadata={
                "delegation_id": delegation_id,
                "component_id": component_id,
                "fallback_count": len(failed_features)
            }
        )
    
    async def _update_circuit_breaker(self, failure: bool) -> None:
        """
        Update circuit breaker state based on success or failure.
        
        Args:
            failure: Whether the operation failed
        """
        if failure:
            # Increment failure count
            self._circuit_failure_count += 1
            
            # Check if threshold exceeded
            if self._circuit_failure_count >= self._circuit_failure_threshold:
                # Open circuit
                self._circuit_state = CircuitState.OPEN
                self._circuit_reset_time = datetime.now() + timedelta(seconds=self._circuit_reset_delay)
                
                logger.warning(f"Circuit breaker opened after {self._circuit_failure_count} failures. Reset scheduled for {self._circuit_reset_time.isoformat()}")
                
                # Schedule reset task
                asyncio.create_task(self._reset_circuit_breaker())
                
                # Record metric
                await self._metrics_manager.record_metric(
                    "phase_two:delegation:circuit_breaker:opened",
                    1.0,
                    metadata={
                        "failure_count": self._circuit_failure_count,
                        "threshold": self._circuit_failure_threshold,
                        "reset_delay": self._circuit_reset_delay
                    }
                )
        else:
            # Success, reset failure count
            self._circuit_failure_count = 0
            
            # If circuit is half-open, close it
            if self._circuit_state == CircuitState.HALF_OPEN:
                self._circuit_state = CircuitState.CLOSED
                logger.info("Circuit breaker closed after successful operation")
                
                # Record metric
                await self._metrics_manager.record_metric(
                    "phase_two:delegation:circuit_breaker:closed",
                    1.0
                )
    
    async def _reset_circuit_breaker(self) -> None:
        """Reset circuit breaker after delay."""
        if not self._circuit_reset_time:
            return
            
        # Calculate delay until reset time
        now = datetime.now()
        if now < self._circuit_reset_time:
            delay = (self._circuit_reset_time - now).total_seconds()
            await asyncio.sleep(delay)
        
        # Set to half-open state
        self._circuit_state = CircuitState.HALF_OPEN
        logger.info("Circuit breaker reset to half-open state")
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:delegation:circuit_breaker:half_open",
            1.0
        )
    
    def _calculate_retry_delay(self, retry_count: int) -> float:
        """
        Calculate retry delay with exponential backoff and jitter.
        
        Args:
            retry_count: Number of retries attempted so far
            
        Returns:
            Delay in seconds
        """
        # Calculate exponential backoff
        delay = self._base_retry_delay * (2 ** (retry_count - 1))
        
        # Add jitter (±25%)
        jitter = delay * 0.25
        delay = delay + random.uniform(-jitter, jitter)
        
        # Ensure positive delay
        return max(1.0, delay)
    
    def _generate_fallback_implementation(self, feature_id: str, feature_def: Dict[str, Any]) -> str:
        """
        Generate fallback implementation for a feature.
        
        Args:
            feature_id: ID of the feature
            feature_def: Feature definition
            
        Returns:
            Fallback implementation
        """
        feature_name = feature_def.get("name", feature_id)
        description = feature_def.get("description", "")
        
        # Create a stub implementation
        return f"""# Fallback implementation for {feature_name} ({feature_id})
# Generated at {datetime.now().isoformat()}
# This is a stub implementation created by the recovery system.
# Description: {description}

# pylint: disable=unused-argument,missing-function-docstring

class {feature_name.replace(' ', '')}Fallback:
    \"\"\"
    Fallback implementation for {feature_name}.
    
    This is a stub implementation created by the recovery system.
    Description: {description}
    \"\"\"
    
    def __init__(self):
        self.feature_id = "{feature_id}"
        self.is_fallback = True
        
    def execute(self, *args, **kwargs):
        # This is a stub implementation
        return {{
            "status": "fallback",
            "feature_id": "{feature_id}",
            "message": "This is a fallback implementation"
        }}
        
# Create instance        
fallback = {feature_name.replace(' ', '')}Fallback()
"""
    
    async def _get_phase_three_interface(self) -> Any:
        """Get Phase Three interface from state manager."""
        return await self._state_manager.get_state("phase_three:interface")
    
    async def _get_delegation_interface(self) -> Any:
        """Get delegation interface from state manager."""
        return await self._state_manager.get_state("phase_two:delegation:interface")
    
    async def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """
        Get circuit breaker status.
        
        Returns:
            Dictionary with circuit breaker status
        """
        return {
            "state": self._circuit_state.value,
            "failure_count": self._circuit_failure_count,
            "threshold": self._circuit_failure_threshold,
            "reset_time": self._circuit_reset_time.isoformat() if self._circuit_reset_time else None,
            "reset_delay": self._circuit_reset_delay
        }
    
    async def reset_circuit_breaker(self) -> Dict[str, Any]:
        """
        Manually reset circuit breaker.
        
        Returns:
            Dictionary with circuit breaker status
        """
        self._circuit_state = CircuitState.CLOSED
        self._circuit_failure_count = 0
        self._circuit_reset_time = None
        
        logger.info("Circuit breaker manually reset to closed state")
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:delegation:circuit_breaker:manual_reset",
            1.0
        )
        
        return await self.get_circuit_breaker_status()
    
    async def get_recovery_statistics(self) -> Dict[str, Any]:
        """
        Get recovery statistics.
        
        Returns:
            Dictionary with recovery statistics
        """
        # Count retries
        retries = sum(self._retry_counts.values())
        
        # Count active recoveries
        active_recoveries = len(self._active_recoveries)
        
        return {
            "total_retries": retries,
            "active_recoveries": active_recoveries,
            "circuit_breaker": await self.get_circuit_breaker_status(),
            "retry_counts": dict(self._retry_counts)
        }