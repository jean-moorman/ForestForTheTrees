"""
Delegation Event Handler
======================

This module provides event handling functionality for the delegation lifecycle,
including event types, payloads, and subscription mechanisms.
"""

import logging
import json
from enum import Enum, auto
from typing import Dict, List, Any, Optional, Callable, Set, Tuple
from dataclasses import dataclass, field, asdict
import asyncio
from datetime import datetime

from resources import (
    EventQueue,
    StateManager,
    ResourceType,
    PhaseType
)

logger = logging.getLogger(__name__)

class DelegationEventType(Enum):
    """Event types for delegation lifecycle."""
    DELEGATION_INITIATED = "delegation_initiated"
    DELEGATION_PROGRESS = "delegation_progress"
    DELEGATION_COMPLETED = "delegation_completed"
    DELEGATION_FAILED = "delegation_failed"
    DELEGATION_CANCELLED = "delegation_cancelled"
    DELEGATION_RETRY = "delegation_retry"

class DelegationErrorType(Enum):
    """Error types for delegation failures."""
    INVALID_COMPONENT = "invalid_component"
    INVALID_FEATURE = "invalid_feature"
    PHASE_THREE_UNAVAILABLE = "phase_three_unavailable"
    FEATURE_CREATION_FAILED = "feature_creation_failed"
    FEATURE_IMPLEMENTATION_FAILED = "feature_implementation_failed"
    FEATURE_TESTING_FAILED = "feature_testing_failed"
    TIMEOUT = "timeout"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    DEPENDENCY_FAILURE = "dependency_failure"
    COMMUNICATION_ERROR = "communication_error"
    UNKNOWN_ERROR = "unknown_error"

@dataclass
class DelegationEventPayload:
    """Base class for delegation event payloads."""
    delegation_id: str
    component_id: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    operation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert payload to dictionary."""
        return asdict(self)

@dataclass
class DelegationInitiatedPayload(DelegationEventPayload):
    """Payload for delegation initiated events."""
    feature_count: int
    features: List[str]
    delegated_to: str = "phase_three"
    expected_completion_time: Optional[str] = None

@dataclass
class DelegationProgressPayload(DelegationEventPayload):
    """Payload for delegation progress events."""
    progress_percentage: float
    completed_features: List[str]
    pending_features: List[str]
    status_message: str

@dataclass
class DelegationCompletedPayload(DelegationEventPayload):
    """Payload for delegation completed events."""
    completed_features: List[str]
    execution_time_seconds: float
    result_summary: Dict[str, Any]

@dataclass
class DelegationFailedPayload(DelegationEventPayload):
    """Payload for delegation failed events."""
    error_type: str
    error_message: str
    failed_features: List[str]
    completed_features: List[str]
    execution_time_seconds: float
    recovery_attempted: bool = False
    recovery_succeeded: bool = False

@dataclass
class DelegationCancelledPayload(DelegationEventPayload):
    """Payload for delegation cancelled events."""
    reason: str
    cancelled_features: List[str]
    completed_features: List[str]
    execution_time_seconds: float

@dataclass
class DelegationRetryPayload(DelegationEventPayload):
    """Payload for delegation retry events."""
    retry_count: int
    error_type: str
    error_message: str
    retry_features: List[str]
    retry_strategy: str
    next_retry_time: str

class DelegationEventHandler:
    """
    Handles events for the delegation lifecycle.
    
    This class is responsible for:
    1. Registering event types for delegation lifecycle
    2. Creating and emitting standardized event payloads
    3. Providing a taxonomy of delegation errors
    4. Managing event subscriptions for tracking delegated tasks
    """
    
    def __init__(self, event_queue: EventQueue, state_manager: StateManager):
        """
        Initialize the DelegationEventHandler.
        
        Args:
            event_queue: EventQueue instance for event emission
            state_manager: StateManager instance for state persistence
        """
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._subscriptions: Dict[str, Set[Callable]] = {}
        self._event_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # Register with event queue
        self._register_event_handlers()
    
    async def _register_event_handlers(self):
        """Register event handlers with event queue."""
        # Register handlers for delegation events
        for event_type in DelegationEventType:
            await self._event_queue.register_handler(
                event_type.value, 
                self._handle_delegation_event
            )
        
        logger.info("Registered delegation event handlers")
    
    async def _handle_delegation_event(self, event_type: str, payload: Dict[str, Any]):
        """
        Handle delegation event.
        
        Args:
            event_type: Type of event
            payload: Event payload
        """
        # Get delegation ID from payload
        delegation_id = payload.get("delegation_id", "unknown")
        
        # Store event in history
        if delegation_id not in self._event_history:
            self._event_history[delegation_id] = []
            
        self._event_history[delegation_id].append({
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "payload": payload
        })
        
        # Get component ID from payload
        component_id = payload.get("component_id", "unknown")
        
        # Store latest event in state manager
        await self._state_manager.set_state(
            f"delegation:{delegation_id}:latest_event",
            {
                "event_type": event_type,
                "timestamp": datetime.now().isoformat(),
                "payload": payload
            },
            ResourceType.STATE
        )
        
        # Update component delegation state
        await self._state_manager.set_state(
            f"component:{component_id}:delegation:status",
            {
                "delegation_id": delegation_id,
                "last_event_type": event_type,
                "last_update": datetime.now().isoformat()
            },
            ResourceType.STATE
        )
        
        # Call subscribers
        await self._notify_subscribers(event_type, payload)
        
        logger.debug(f"Handled delegation event: {event_type} for {delegation_id}")
    
    async def emit_delegation_initiated(self, 
                                       delegation_id: str, 
                                       component_id: str,
                                       features: List[Dict[str, Any]],
                                       operation_id: Optional[str] = None,
                                       expected_completion_time: Optional[str] = None) -> None:
        """
        Emit delegation initiated event.
        
        Args:
            delegation_id: Unique ID for this delegation operation
            component_id: ID of the component being delegated
            features: List of feature definitions being delegated
            operation_id: Optional operation ID for tracking
            expected_completion_time: Optional expected completion time
        """
        feature_ids = [f.get("id", "") for f in features]
        
        payload = DelegationInitiatedPayload(
            delegation_id=delegation_id,
            component_id=component_id,
            feature_count=len(features),
            features=feature_ids,
            operation_id=operation_id,
            expected_completion_time=expected_completion_time
        )
        
        # Record start time
        await self._state_manager.set_state(
            f"delegation:{delegation_id}:start_time",
            datetime.now().isoformat(),
            ResourceType.STATE
        )
        
        # Store feature IDs for this delegation
        await self._state_manager.set_state(
            f"delegation:{delegation_id}:features",
            feature_ids,
            ResourceType.STATE
        )
        
        # Emit event
        await self._event_queue.emit(
            DelegationEventType.DELEGATION_INITIATED.value,
            payload.to_dict()
        )
        
        logger.info(f"Delegation initiated for component {component_id} with {len(features)} features")
    
    async def emit_delegation_progress(self,
                                     delegation_id: str,
                                     component_id: str,
                                     progress_percentage: float,
                                     completed_features: List[str],
                                     pending_features: List[str],
                                     status_message: str,
                                     operation_id: Optional[str] = None) -> None:
        """
        Emit delegation progress event.
        
        Args:
            delegation_id: Unique ID for this delegation operation
            component_id: ID of the component being delegated
            progress_percentage: Percentage of completion (0-100)
            completed_features: List of completed feature IDs
            pending_features: List of pending feature IDs
            status_message: Status message
            operation_id: Optional operation ID for tracking
        """
        payload = DelegationProgressPayload(
            delegation_id=delegation_id,
            component_id=component_id,
            progress_percentage=progress_percentage,
            completed_features=completed_features,
            pending_features=pending_features,
            status_message=status_message,
            operation_id=operation_id
        )
        
        # Store progress
        await self._state_manager.set_state(
            f"delegation:{delegation_id}:progress",
            {
                "percentage": progress_percentage,
                "completed_features": completed_features,
                "pending_features": pending_features,
                "timestamp": datetime.now().isoformat()
            },
            ResourceType.STATE
        )
        
        # Emit event
        await self._event_queue.emit(
            DelegationEventType.DELEGATION_PROGRESS.value,
            payload.to_dict()
        )
        
        logger.info(f"Delegation progress for {component_id}: {progress_percentage:.2f}% complete")
    
    async def emit_delegation_completed(self,
                                      delegation_id: str,
                                      component_id: str,
                                      completed_features: List[str],
                                      result_summary: Dict[str, Any],
                                      operation_id: Optional[str] = None) -> None:
        """
        Emit delegation completed event.
        
        Args:
            delegation_id: Unique ID for this delegation operation
            component_id: ID of the component being delegated
            completed_features: List of completed feature IDs
            result_summary: Summary of delegation results
            operation_id: Optional operation ID for tracking
        """
        # Calculate execution time
        start_time_str = await self._state_manager.get_state(f"delegation:{delegation_id}:start_time")
        if start_time_str:
            start_time = datetime.fromisoformat(start_time_str)
            execution_time = (datetime.now() - start_time).total_seconds()
        else:
            execution_time = 0.0
        
        payload = DelegationCompletedPayload(
            delegation_id=delegation_id,
            component_id=component_id,
            completed_features=completed_features,
            execution_time_seconds=execution_time,
            result_summary=result_summary,
            operation_id=operation_id
        )
        
        # Store completion
        await self._state_manager.set_state(
            f"delegation:{delegation_id}:completion",
            {
                "completed_features": completed_features,
                "execution_time_seconds": execution_time,
                "result_summary": result_summary,
                "timestamp": datetime.now().isoformat()
            },
            ResourceType.STATE
        )
        
        # Emit event
        await self._event_queue.emit(
            DelegationEventType.DELEGATION_COMPLETED.value,
            payload.to_dict()
        )
        
        logger.info(f"Delegation completed for {component_id} after {execution_time:.2f} seconds")
    
    async def emit_delegation_failed(self,
                                   delegation_id: str,
                                   component_id: str,
                                   error_type: DelegationErrorType,
                                   error_message: str,
                                   failed_features: List[str],
                                   completed_features: List[str],
                                   recovery_attempted: bool = False,
                                   recovery_succeeded: bool = False,
                                   operation_id: Optional[str] = None) -> None:
        """
        Emit delegation failed event.
        
        Args:
            delegation_id: Unique ID for this delegation operation
            component_id: ID of the component being delegated
            error_type: Type of error
            error_message: Error message
            failed_features: List of failed feature IDs
            completed_features: List of completed feature IDs
            recovery_attempted: Whether recovery was attempted
            recovery_succeeded: Whether recovery succeeded
            operation_id: Optional operation ID for tracking
        """
        # Calculate execution time
        start_time_str = await self._state_manager.get_state(f"delegation:{delegation_id}:start_time")
        if start_time_str:
            start_time = datetime.fromisoformat(start_time_str)
            execution_time = (datetime.now() - start_time).total_seconds()
        else:
            execution_time = 0.0
        
        payload = DelegationFailedPayload(
            delegation_id=delegation_id,
            component_id=component_id,
            error_type=error_type.value,
            error_message=error_message,
            failed_features=failed_features,
            completed_features=completed_features,
            execution_time_seconds=execution_time,
            recovery_attempted=recovery_attempted,
            recovery_succeeded=recovery_succeeded,
            operation_id=operation_id
        )
        
        # Store failure
        await self._state_manager.set_state(
            f"delegation:{delegation_id}:failure",
            {
                "error_type": error_type.value,
                "error_message": error_message,
                "failed_features": failed_features,
                "completed_features": completed_features,
                "execution_time_seconds": execution_time,
                "recovery_attempted": recovery_attempted,
                "recovery_succeeded": recovery_succeeded,
                "timestamp": datetime.now().isoformat()
            },
            ResourceType.STATE
        )
        
        # Emit event
        await self._event_queue.emit(
            DelegationEventType.DELEGATION_FAILED.value,
            payload.to_dict()
        )
        
        logger.error(f"Delegation failed for {component_id}: {error_type.value} - {error_message}")
    
    async def emit_delegation_cancelled(self,
                                      delegation_id: str,
                                      component_id: str,
                                      reason: str,
                                      cancelled_features: List[str],
                                      completed_features: List[str],
                                      operation_id: Optional[str] = None) -> None:
        """
        Emit delegation cancelled event.
        
        Args:
            delegation_id: Unique ID for this delegation operation
            component_id: ID of the component being delegated
            reason: Reason for cancellation
            cancelled_features: List of cancelled feature IDs
            completed_features: List of completed feature IDs
            operation_id: Optional operation ID for tracking
        """
        # Calculate execution time
        start_time_str = await self._state_manager.get_state(f"delegation:{delegation_id}:start_time")
        if start_time_str:
            start_time = datetime.fromisoformat(start_time_str)
            execution_time = (datetime.now() - start_time).total_seconds()
        else:
            execution_time = 0.0
        
        payload = DelegationCancelledPayload(
            delegation_id=delegation_id,
            component_id=component_id,
            reason=reason,
            cancelled_features=cancelled_features,
            completed_features=completed_features,
            execution_time_seconds=execution_time,
            operation_id=operation_id
        )
        
        # Store cancellation
        await self._state_manager.set_state(
            f"delegation:{delegation_id}:cancellation",
            {
                "reason": reason,
                "cancelled_features": cancelled_features,
                "completed_features": completed_features,
                "execution_time_seconds": execution_time,
                "timestamp": datetime.now().isoformat()
            },
            ResourceType.STATE
        )
        
        # Emit event
        await self._event_queue.emit(
            DelegationEventType.DELEGATION_CANCELLED.value,
            payload.to_dict()
        )
        
        logger.warning(f"Delegation cancelled for {component_id}: {reason}")
    
    async def emit_delegation_retry(self,
                                  delegation_id: str,
                                  component_id: str,
                                  retry_count: int,
                                  error_type: DelegationErrorType,
                                  error_message: str,
                                  retry_features: List[str],
                                  retry_strategy: str,
                                  next_retry_time: datetime,
                                  operation_id: Optional[str] = None) -> None:
        """
        Emit delegation retry event.
        
        Args:
            delegation_id: Unique ID for this delegation operation
            component_id: ID of the component being delegated
            retry_count: Number of retries attempted so far
            error_type: Type of error that triggered the retry
            error_message: Error message
            retry_features: List of features to retry
            retry_strategy: Strategy used for retry
            next_retry_time: Next retry time
            operation_id: Optional operation ID for tracking
        """
        payload = DelegationRetryPayload(
            delegation_id=delegation_id,
            component_id=component_id,
            retry_count=retry_count,
            error_type=error_type.value,
            error_message=error_message,
            retry_features=retry_features,
            retry_strategy=retry_strategy,
            next_retry_time=next_retry_time.isoformat(),
            operation_id=operation_id
        )
        
        # Store retry info
        await self._state_manager.set_state(
            f"delegation:{delegation_id}:retry:{retry_count}",
            {
                "error_type": error_type.value,
                "error_message": error_message,
                "retry_features": retry_features,
                "retry_strategy": retry_strategy,
                "next_retry_time": next_retry_time.isoformat(),
                "timestamp": datetime.now().isoformat()
            },
            ResourceType.STATE
        )
        
        # Emit event
        await self._event_queue.emit(
            DelegationEventType.DELEGATION_RETRY.value,
            payload.to_dict()
        )
        
        logger.info(f"Delegation retry #{retry_count} for {component_id} scheduled at {next_retry_time.isoformat()}")
    
    async def subscribe(self, event_type: DelegationEventType, callback: Callable) -> None:
        """
        Subscribe to delegation events.
        
        Args:
            event_type: Type of event to subscribe to
            callback: Callback function to call when event occurs
        """
        if event_type.value not in self._subscriptions:
            self._subscriptions[event_type.value] = set()
            
        self._subscriptions[event_type.value].add(callback)
        logger.debug(f"Subscribed to delegation event: {event_type.value}")
    
    async def unsubscribe(self, event_type: DelegationEventType, callback: Callable) -> None:
        """
        Unsubscribe from delegation events.
        
        Args:
            event_type: Type of event to unsubscribe from
            callback: Callback function to unsubscribe
        """
        if event_type.value in self._subscriptions:
            self._subscriptions[event_type.value].discard(callback)
            logger.debug(f"Unsubscribed from delegation event: {event_type.value}")
    
    async def _notify_subscribers(self, event_type: str, payload: Dict[str, Any]) -> None:
        """
        Notify subscribers of delegation event.
        
        Args:
            event_type: Type of event
            payload: Event payload
        """
        if event_type in self._subscriptions:
            for callback in self._subscriptions[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event_type, payload)
                    else:
                        callback(event_type, payload)
                except Exception as e:
                    logger.error(f"Error in delegation event subscriber: {str(e)}")
    
    async def get_event_history(self, delegation_id: str) -> List[Dict[str, Any]]:
        """
        Get event history for a delegation.
        
        Args:
            delegation_id: ID of the delegation
            
        Returns:
            List of events for the delegation
        """
        return self._event_history.get(delegation_id, [])