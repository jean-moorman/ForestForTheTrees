"""
Coordination Checkpoint Manager for Phase Two
------------------------------------------
Implements atomic checkpointing for phase state, restoration from checkpoints,
checkpoint history, and integration with the event system.
"""

import logging
import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from resources import (
    EventQueue,
    StateManager,
    MetricsManager,
    ResourceType,
    ResourceEventTypes
)

logger = logging.getLogger(__name__)

class CoordinationCheckpointManager:
    """
    Manages checkpoint creation, storage, and restoration.
    
    This class provides:
    1. Atomic checkpoints for phase state
    2. Restoration from checkpoints after failures
    3. Checkpoint history tracking
    4. Integration with event system for checkpoint notifications
    """
    
    def __init__(self,
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 metrics_manager: MetricsManager,
                 max_history_per_phase: int = 10):
        """
        Initialize the CoordinationCheckpointManager.
        
        Args:
            event_queue: EventQueue for emitting events
            state_manager: StateManager for state persistence
            metrics_manager: MetricsManager for metrics recording
            max_history_per_phase: Maximum number of checkpoints to keep per phase
        """
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._metrics_manager = metrics_manager
        self._max_history_per_phase = max_history_per_phase
        
        # Store checkpoints in memory for quick access
        # {checkpoint_id: checkpoint_data}
        self._checkpoints: Dict[str, Dict[str, Any]] = {}
        
        # Store checkpoint history by phase
        # {phase_id: [checkpoint_id1, checkpoint_id2, ...]}
        self._checkpoint_history: Dict[str, List[str]] = {}
        
        logger.info("CoordinationCheckpointManager initialized")
    
    async def create_checkpoint(self,
                              phase_id: str,
                              checkpoint_type: str,
                              metadata: Dict[str, Any],
                              state_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Create an atomic checkpoint for a phase.
        
        Args:
            phase_id: ID of the phase
            checkpoint_type: Type of checkpoint (e.g., "pre_execution", "post_execution")
            metadata: Metadata about the checkpoint
            state_data: Optional state data to store in the checkpoint
            
        Returns:
            Checkpoint ID
        """
        # Generate checkpoint ID
        checkpoint_id = f"checkpoint_{phase_id}_{checkpoint_type}_{uuid.uuid4().hex[:8]}"
        
        # Get phase state if not provided
        if state_data is None:
            try:
                # Get current phase state
                phase_state_entry = await self._state_manager.get_state(f"phase:{phase_id}")
                if not phase_state_entry:
                    logger.warning(f"No state found for phase {phase_id}, creating empty checkpoint")
                    state_data = {}
                else:
                    state_data = phase_state_entry.state
            except Exception as e:
                logger.error(f"Error getting phase state for checkpoint: {str(e)}")
                state_data = {}
        
        # Create checkpoint data
        checkpoint_data = {
            "checkpoint_id": checkpoint_id,
            "phase_id": phase_id,
            "type": checkpoint_type,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata,
            "state_data": state_data
        }
        
        # Store checkpoint
        self._checkpoints[checkpoint_id] = checkpoint_data
        
        # Update checkpoint history
        if phase_id not in self._checkpoint_history:
            self._checkpoint_history[phase_id] = []
        
        self._checkpoint_history[phase_id].append(checkpoint_id)
        
        # Trim history if needed
        await self._trim_checkpoint_history(phase_id)
        
        # Persist checkpoint
        try:
            await self._state_manager.set_state(
                f"checkpoint:{checkpoint_id}",
                checkpoint_data,
                ResourceType.STATE
            )
            
            # Update phase's checkpoint list
            await self._update_phase_checkpoint_list(phase_id, checkpoint_id)
            
            logger.info(f"Created checkpoint {checkpoint_id} for phase {phase_id} of type {checkpoint_type}")
        except Exception as e:
            logger.error(f"Error persisting checkpoint {checkpoint_id}: {str(e)}")
            # Keep in-memory copy even if persistence fails
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:checkpoint:created",
            1.0,
            metadata={
                "phase_id": phase_id,
                "checkpoint_id": checkpoint_id,
                "checkpoint_type": checkpoint_type,
                "data_size_bytes": len(json.dumps(checkpoint_data))
            }
        )
        
        # Emit checkpoint created event
        await self._event_queue.emit(
            ResourceEventTypes.PHASE_COORDINATION_EVENT.value,
            {
                "event_type": "checkpoint_created",
                "phase_id": phase_id,
                "checkpoint_id": checkpoint_id,
                "checkpoint_type": checkpoint_type,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return checkpoint_id
    
    async def restore_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """
        Restore state from a checkpoint.
        
        Args:
            checkpoint_id: ID of the checkpoint to restore
            
        Returns:
            Checkpoint data or None if checkpoint not found
        """
        # Check if checkpoint exists in memory
        checkpoint_data = self._checkpoints.get(checkpoint_id)
        
        # If not in memory, try to load from state manager
        if not checkpoint_data:
            try:
                checkpoint_entry = await self._state_manager.get_state(f"checkpoint:{checkpoint_id}")
                if not checkpoint_entry:
                    logger.error(f"Checkpoint {checkpoint_id} not found")
                    return None
                    
                checkpoint_data = checkpoint_entry.state
                # Update in-memory store
                self._checkpoints[checkpoint_id] = checkpoint_data
            except Exception as e:
                logger.error(f"Error loading checkpoint {checkpoint_id}: {str(e)}")
                return None
        
        # Extract phase and state data
        phase_id = checkpoint_data["phase_id"]
        state_data = checkpoint_data["state_data"]
        checkpoint_type = checkpoint_data["type"]
        
        # Restore phase state if it has state data
        if state_data:
            try:
                # Restore phase state
                await self._state_manager.set_state(
                    f"phase:{phase_id}",
                    state_data,
                    ResourceType.STATE
                )
                
                logger.info(f"Restored phase {phase_id} state from checkpoint {checkpoint_id}")
            except Exception as e:
                logger.error(f"Error restoring phase state from checkpoint {checkpoint_id}: {str(e)}")
                # Continue anyway to return the checkpoint data
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:checkpoint:restored",
            1.0,
            metadata={
                "phase_id": phase_id,
                "checkpoint_id": checkpoint_id,
                "checkpoint_type": checkpoint_type
            }
        )
        
        # Emit checkpoint restored event
        await self._event_queue.emit(
            ResourceEventTypes.PHASE_COORDINATION_EVENT.value,
            {
                "event_type": "checkpoint_restored",
                "phase_id": phase_id,
                "checkpoint_id": checkpoint_id,
                "checkpoint_type": checkpoint_type,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Add restoration timestamp
        checkpoint_data["restored_at"] = datetime.now().isoformat()
        
        return checkpoint_data
    
    async def get_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """
        Get checkpoint data without restoring state.
        
        Args:
            checkpoint_id: ID of the checkpoint to get
            
        Returns:
            Checkpoint data or None if checkpoint not found
        """
        # Check if checkpoint exists in memory
        checkpoint_data = self._checkpoints.get(checkpoint_id)
        
        # If not in memory, try to load from state manager
        if not checkpoint_data:
            try:
                checkpoint_entry = await self._state_manager.get_state(f"checkpoint:{checkpoint_id}")
                if not checkpoint_entry:
                    return None
                    
                checkpoint_data = checkpoint_entry.state
                # Update in-memory store
                self._checkpoints[checkpoint_id] = checkpoint_data
            except Exception as e:
                logger.error(f"Error loading checkpoint {checkpoint_id}: {str(e)}")
                return None
        
        return checkpoint_data
    
    async def get_checkpoints_for_phase(self, phase_id: str) -> List[Dict[str, Any]]:
        """
        Get all checkpoints for a phase.
        
        Args:
            phase_id: ID of the phase
            
        Returns:
            List of checkpoint data
        """
        # Get checkpoint IDs for the phase
        checkpoint_ids = self._checkpoint_history.get(phase_id, [])
        
        # Collect checkpoint data
        checkpoints = []
        for checkpoint_id in checkpoint_ids:
            checkpoint_data = await self.get_checkpoint(checkpoint_id)
            if checkpoint_data:
                checkpoints.append(checkpoint_data)
        
        # Sort by creation time (newest first)
        checkpoints.sort(key=lambda x: x["created_at"], reverse=True)
        
        return checkpoints
    
    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Delete a checkpoint.
        
        Args:
            checkpoint_id: ID of the checkpoint to delete
            
        Returns:
            True if checkpoint was deleted, False otherwise
        """
        # Check if checkpoint exists
        checkpoint_data = await self.get_checkpoint(checkpoint_id)
        if not checkpoint_data:
            return False
        
        # Get phase ID
        phase_id = checkpoint_data["phase_id"]
        
        # Delete from state manager
        try:
            await self._state_manager.delete_state(f"checkpoint:{checkpoint_id}")
        except Exception as e:
            logger.error(f"Error deleting checkpoint {checkpoint_id} from state manager: {str(e)}")
            # Continue anyway to remove from in-memory store
        
        # Remove from in-memory store
        if checkpoint_id in self._checkpoints:
            del self._checkpoints[checkpoint_id]
        
        # Remove from checkpoint history
        if phase_id in self._checkpoint_history and checkpoint_id in self._checkpoint_history[phase_id]:
            self._checkpoint_history[phase_id].remove(checkpoint_id)
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:checkpoint:deleted",
            1.0,
            metadata={
                "phase_id": phase_id,
                "checkpoint_id": checkpoint_id
            }
        )
        
        logger.info(f"Deleted checkpoint {checkpoint_id} for phase {phase_id}")
        
        return True
    
    async def get_checkpoint_history(self, phase_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get checkpoint history.
        
        Args:
            phase_id: Optional phase ID to filter history
            
        Returns:
            Dictionary with checkpoint history
        """
        history_data = {}
        
        if phase_id:
            # Get history for specific phase
            checkpoint_ids = self._checkpoint_history.get(phase_id, [])
            history_data[phase_id] = {
                "checkpoint_count": len(checkpoint_ids),
                "checkpoint_ids": checkpoint_ids
            }
        else:
            # Get history for all phases
            for phase_id, checkpoint_ids in self._checkpoint_history.items():
                history_data[phase_id] = {
                    "checkpoint_count": len(checkpoint_ids),
                    "checkpoint_ids": checkpoint_ids
                }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "history": history_data,
            "total_checkpoints": sum(len(ids) for ids in self._checkpoint_history.values())
        }
    
    async def _trim_checkpoint_history(self, phase_id: str) -> None:
        """
        Trim checkpoint history for a phase.
        
        Args:
            phase_id: ID of the phase
        """
        checkpoint_ids = self._checkpoint_history.get(phase_id, [])
        
        # Nothing to trim if under the limit
        if len(checkpoint_ids) <= self._max_history_per_phase:
            return
        
        # Get checkpoints to delete (oldest first)
        to_delete = checkpoint_ids[:-self._max_history_per_phase]
        
        # Delete each checkpoint
        for checkpoint_id in to_delete:
            await self.delete_checkpoint(checkpoint_id)
        
        # Update history (should already be updated by delete_checkpoint)
        self._checkpoint_history[phase_id] = checkpoint_ids[-self._max_history_per_phase:]
    
    async def _update_phase_checkpoint_list(self, phase_id: str, checkpoint_id: str) -> None:
        """
        Update the list of checkpoints for a phase in state manager.
        
        Args:
            phase_id: ID of the phase
            checkpoint_id: ID of the checkpoint to add
        """
        try:
            # Get current list
            checkpoint_list_entry = await self._state_manager.get_state(f"phase_checkpoints:{phase_id}")
            
            if not checkpoint_list_entry:
                # Create new list
                checkpoint_list = {
                    "phase_id": phase_id,
                    "checkpoints": [checkpoint_id],
                    "last_updated": datetime.now().isoformat()
                }
            else:
                # Update existing list
                checkpoint_list = checkpoint_list_entry.state
                if "checkpoints" not in checkpoint_list:
                    checkpoint_list["checkpoints"] = []
                
                # Add checkpoint ID if not already in list
                if checkpoint_id not in checkpoint_list["checkpoints"]:
                    checkpoint_list["checkpoints"].append(checkpoint_id)
                
                checkpoint_list["last_updated"] = datetime.now().isoformat()
            
            # Save updated list
            await self._state_manager.set_state(
                f"phase_checkpoints:{phase_id}",
                checkpoint_list,
                ResourceType.STATE
            )
        except Exception as e:
            logger.error(f"Error updating phase checkpoint list for {phase_id}: {str(e)}")
    
    async def load_checkpoint_history(self) -> None:
        """
        Load checkpoint history from state manager.
        
        This should be called during initialization if needed to restore
        checkpoint history from persistent storage.
        """
        try:
            # Get all checkpoint list entries
            checkpoint_list_prefix = "phase_checkpoints:"
            checkpoint_lists = await self._state_manager.get_states_by_prefix(checkpoint_list_prefix)
            
            # Process each checkpoint list
            for entry in checkpoint_lists:
                # Extract phase ID from key
                phase_id = entry.key[len(checkpoint_list_prefix):]
                
                # Get checkpoint list
                checkpoint_list = entry.state
                
                # Update in-memory history
                self._checkpoint_history[phase_id] = checkpoint_list.get("checkpoints", [])
            
            logger.info(f"Loaded checkpoint history for {len(self._checkpoint_history)} phases")
        except Exception as e:
            logger.error(f"Error loading checkpoint history: {str(e)}")