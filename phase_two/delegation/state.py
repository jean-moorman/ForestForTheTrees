"""
Delegation State Tracker
======================

This module provides functionality for tracking the state of delegated
component implementations and feature definitions.
"""

import logging
import json
from enum import Enum, auto
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta

from resources import (
    StateManager,
    MetricsManager,
    ResourceType
)

logger = logging.getLogger(__name__)

class DelegationState(Enum):
    """States for delegation operations."""
    PENDING = auto()         # Delegation not yet initiated
    INITIATED = auto()       # Delegation has been initiated
    IN_PROGRESS = auto()     # Delegation is in progress
    COMPLETED = auto()       # Delegation completed successfully
    FAILED = auto()          # Delegation failed
    CANCELLED = auto()       # Delegation was cancelled
    RETRYING = auto()        # Delegation is being retried
    PARTIAL = auto()         # Delegation partially completed

@dataclass
class DelegationStatus:
    """Status information for a delegation operation."""
    delegation_id: str
    component_id: str
    state: DelegationState
    feature_ids: List[str]
    completed_features: List[str] = field(default_factory=list)
    failed_features: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    last_update_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    error_message: Optional[str] = None
    progress_percentage: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        # Convert enums and datetimes to strings
        result["state"] = self.state.name
        if self.start_time:
            result["start_time"] = self.start_time.isoformat()
        if self.last_update_time:
            result["last_update_time"] = self.last_update_time.isoformat()
        if self.completion_time:
            result["completion_time"] = self.completion_time.isoformat()
        return result

class DelegationStateTracker:
    """
    Tracks the state of delegated component implementations and feature definitions.
    
    This class is responsible for:
    1. Tracking delegation state per component
    2. Storing mappings between component IDs and delegated feature IDs
    3. Interfacing with StateManager for persistence
    4. Providing query methods for delegation status reporting
    """
    
    def __init__(self, state_manager: StateManager, metrics_manager: MetricsManager):
        """
        Initialize the DelegationStateTracker.
        
        Args:
            state_manager: StateManager instance for state persistence
            metrics_manager: MetricsManager instance for metrics recording
        """
        self._state_manager = state_manager
        self._metrics_manager = metrics_manager
        
        # In-memory state tracking
        self._delegation_statuses: Dict[str, DelegationStatus] = {}
        self._component_to_delegation: Dict[str, str] = {}
        self._feature_to_delegation: Dict[str, str] = {}
        self._feature_to_component: Dict[str, str] = {}
    
    async def register_delegation(self, delegation_id: str, component_id: str, feature_ids: List[str]) -> None:
        """
        Register a new delegation operation.
        
        Args:
            delegation_id: Unique ID for this delegation operation
            component_id: ID of the component being delegated
            feature_ids: List of feature IDs being delegated
        """
        # Create status object
        status = DelegationStatus(
            delegation_id=delegation_id,
            component_id=component_id,
            state=DelegationState.PENDING,
            feature_ids=feature_ids,
            start_time=datetime.now(),
            last_update_time=datetime.now()
        )
        
        # Store in memory
        self._delegation_statuses[delegation_id] = status
        self._component_to_delegation[component_id] = delegation_id
        
        # Store feature to delegation and component mappings
        for feature_id in feature_ids:
            self._feature_to_delegation[feature_id] = delegation_id
            self._feature_to_component[feature_id] = component_id
        
        # Store in state manager
        await self._persist_delegation_status(status)
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:delegation:registered",
            1.0,
            metadata={
                "delegation_id": delegation_id,
                "component_id": component_id,
                "feature_count": len(feature_ids)
            }
        )
        
        logger.info(f"Registered delegation {delegation_id} for component {component_id} with {len(feature_ids)} features")
    
    async def update_delegation_state(self, delegation_id: str, state: DelegationState, 
                                    metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Update the state of a delegation operation.
        
        Args:
            delegation_id: ID of the delegation operation
            state: New state
            metadata: Optional additional metadata
        """
        if delegation_id not in self._delegation_statuses:
            logger.warning(f"Attempted to update unknown delegation: {delegation_id}")
            return
            
        status = self._delegation_statuses[delegation_id]
        old_state = status.state
        status.state = state
        status.last_update_time = datetime.now()
        
        # Update specific fields based on metadata
        if metadata:
            if "progress_percentage" in metadata:
                status.progress_percentage = metadata["progress_percentage"]
            if "completed_features" in metadata:
                status.completed_features = metadata["completed_features"]
            if "failed_features" in metadata:
                status.failed_features = metadata["failed_features"]
            if "error_message" in metadata:
                status.error_message = metadata["error_message"]
        
        # Set completion time if the state is final
        if state in (DelegationState.COMPLETED, DelegationState.FAILED, DelegationState.CANCELLED):
            status.completion_time = datetime.now()
        
        # Persist updated status
        await self._persist_delegation_status(status)
        
        # Record state change metric
        await self._metrics_manager.record_metric(
            "phase_two:delegation:state_change",
            1.0,
            metadata={
                "delegation_id": delegation_id,
                "component_id": status.component_id,
                "old_state": old_state.name,
                "new_state": state.name
            }
        )
        
        logger.info(f"Updated delegation {delegation_id} state from {old_state.name} to {state.name}")
    
    async def update_feature_status(self, feature_id: str, completed: bool, 
                                  error_message: Optional[str] = None) -> None:
        """
        Update the status of a delegated feature.
        
        Args:
            feature_id: ID of the feature
            completed: Whether the feature implementation completed
            error_message: Optional error message if the feature failed
        """
        if feature_id not in self._feature_to_delegation:
            logger.warning(f"Attempted to update unknown feature: {feature_id}")
            return
            
        delegation_id = self._feature_to_delegation[feature_id]
        status = self._delegation_statuses[delegation_id]
        
        # Update feature lists
        if completed:
            if feature_id not in status.completed_features:
                status.completed_features.append(feature_id)
            if feature_id in status.failed_features:
                status.failed_features.remove(feature_id)
        else:
            if feature_id not in status.failed_features:
                status.failed_features.append(feature_id)
            if feature_id in status.completed_features:
                status.completed_features.remove(feature_id)
        
        # Update progress percentage
        total_features = len(status.feature_ids)
        completed_count = len(status.completed_features)
        status.progress_percentage = (completed_count / total_features) * 100 if total_features > 0 else 0
        
        # Update error message if provided
        if error_message and not completed:
            status.error_message = error_message
        
        # Update last update time
        status.last_update_time = datetime.now()
        
        # Determine new state based on feature status
        if completed_count == total_features:
            await self.update_delegation_state(delegation_id, DelegationState.COMPLETED)
        elif len(status.failed_features) > 0:
            if completed_count > 0:
                await self.update_delegation_state(delegation_id, DelegationState.PARTIAL)
            else:
                await self.update_delegation_state(delegation_id, DelegationState.FAILED)
        else:
            await self.update_delegation_state(delegation_id, DelegationState.IN_PROGRESS)
        
        # Record feature status metric
        await self._metrics_manager.record_metric(
            "phase_two:delegation:feature_status",
            1.0,
            metadata={
                "delegation_id": delegation_id,
                "component_id": status.component_id,
                "feature_id": feature_id,
                "completed": completed,
                "has_error": error_message is not None
            }
        )
        
        logger.debug(f"Updated feature {feature_id} status: completed={completed}")
    
    async def get_delegation_status(self, delegation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a delegation operation.
        
        Args:
            delegation_id: ID of the delegation operation
            
        Returns:
            Dictionary representation of delegation status or None if not found
        """
        if delegation_id not in self._delegation_statuses:
            logger.warning(f"Attempted to get unknown delegation: {delegation_id}")
            return None
            
        status = self._delegation_statuses[delegation_id]
        return status.to_dict()
    
    async def get_component_delegation_status(self, component_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the delegation status for a component.
        
        Args:
            component_id: ID of the component
            
        Returns:
            Dictionary representation of delegation status or None if not found
        """
        if component_id not in self._component_to_delegation:
            logger.warning(f"No delegation found for component: {component_id}")
            return None
            
        delegation_id = self._component_to_delegation[component_id]
        return await self.get_delegation_status(delegation_id)
    
    async def get_feature_delegation_status(self, feature_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the delegation status for a feature.
        
        Args:
            feature_id: ID of the feature
            
        Returns:
            Dictionary representation of delegation status or None if not found
        """
        if feature_id not in self._feature_to_delegation:
            logger.warning(f"No delegation found for feature: {feature_id}")
            return None
            
        delegation_id = self._feature_to_delegation[feature_id]
        return await self.get_delegation_status(delegation_id)
    
    async def get_component_features(self, component_id: str) -> List[str]:
        """
        Get the feature IDs for a component.
        
        Args:
            component_id: ID of the component
            
        Returns:
            List of feature IDs for the component
        """
        if component_id not in self._component_to_delegation:
            logger.warning(f"No delegation found for component: {component_id}")
            return []
            
        delegation_id = self._component_to_delegation[component_id]
        status = self._delegation_statuses[delegation_id]
        return status.feature_ids
    
    async def get_feature_component(self, feature_id: str) -> Optional[str]:
        """
        Get the component ID for a feature.
        
        Args:
            feature_id: ID of the feature
            
        Returns:
            Component ID or None if not found
        """
        return self._feature_to_component.get(feature_id)
    
    async def get_all_delegations(self) -> List[Dict[str, Any]]:
        """
        Get all delegation statuses.
        
        Returns:
            List of delegation status dictionaries
        """
        return [status.to_dict() for status in self._delegation_statuses.values()]
    
    async def get_delegations_by_state(self, state: DelegationState) -> List[Dict[str, Any]]:
        """
        Get delegations by state.
        
        Args:
            state: State to filter by
            
        Returns:
            List of delegation status dictionaries matching the state
        """
        return [status.to_dict() for status in self._delegation_statuses.values() 
                if status.state == state]
    
    async def load_delegation_states(self) -> None:
        """Load delegation states from state manager."""
        # Get all delegation keys
        delegation_keys = await self._state_manager.get_keys_by_prefix("delegation:")
        
        for key in delegation_keys:
            if key.endswith(":status"):
                delegation_id = key.split(":")[1]
                status_dict = await self._state_manager.get_state(key)
                if not status_dict:
                    continue
                    
                # Create status object
                try:
                    # Convert string dates to datetime objects
                    for date_field in ["start_time", "last_update_time", "completion_time"]:
                        if date_field in status_dict and status_dict[date_field]:
                            status_dict[date_field] = datetime.fromisoformat(status_dict[date_field])
                    
                    # Convert state string to enum
                    if "state" in status_dict:
                        status_dict["state"] = DelegationState[status_dict["state"]]
                    
                    # Create status object
                    status = DelegationStatus(**status_dict)
                    
                    # Store in memory
                    self._delegation_statuses[delegation_id] = status
                    self._component_to_delegation[status.component_id] = delegation_id
                    
                    # Store feature mappings
                    for feature_id in status.feature_ids:
                        self._feature_to_delegation[feature_id] = delegation_id
                        self._feature_to_component[feature_id] = status.component_id
                        
                except Exception as e:
                    logger.error(f"Error loading delegation status for {delegation_id}: {str(e)}")
        
        logger.info(f"Loaded {len(self._delegation_statuses)} delegation states from state manager")
    
    async def cleanup_old_delegations(self, max_age_days: int = 7) -> int:
        """
        Clean up old delegation records.
        
        Args:
            max_age_days: Maximum age of delegations to keep, in days
            
        Returns:
            Number of delegations cleaned up
        """
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        delegations_to_remove = []
        
        # Find delegations to remove
        for delegation_id, status in self._delegation_statuses.items():
            # Skip delegations that are still active
            if status.state in (DelegationState.PENDING, DelegationState.INITIATED, 
                             DelegationState.IN_PROGRESS, DelegationState.RETRYING):
                continue
                
            # Check completion time
            if status.completion_time and status.completion_time < cutoff_time:
                delegations_to_remove.append(delegation_id)
        
        # Remove delegations
        for delegation_id in delegations_to_remove:
            status = self._delegation_statuses[delegation_id]
            
            # Remove from state manager
            await self._state_manager.delete_state(f"delegation:{delegation_id}:status")
            
            # Remove from memory
            del self._delegation_statuses[delegation_id]
            del self._component_to_delegation[status.component_id]
            
            # Remove feature mappings
            for feature_id in status.feature_ids:
                if feature_id in self._feature_to_delegation:
                    del self._feature_to_delegation[feature_id]
                if feature_id in self._feature_to_component:
                    del self._feature_to_component[feature_id]
        
        logger.info(f"Cleaned up {len(delegations_to_remove)} old delegations")
        return len(delegations_to_remove)
    
    async def _persist_delegation_status(self, status: DelegationStatus) -> None:
        """
        Persist delegation status to state manager.
        
        Args:
            status: Delegation status to persist
        """
        await self._state_manager.set_state(
            f"delegation:{status.delegation_id}:status",
            status.to_dict(),
            ResourceType.STATE
        )