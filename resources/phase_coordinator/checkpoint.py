"""
Forest For The Trees (FFTT) Phase Coordination System - Checkpoint Management
---------------------------------------------------
Handles creation and restoration of phase checkpoints.
"""
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

from resources.events import EventQueue, ResourceEventTypes
from resources.state import StateManager, ResourceType
from resources.managers import MetricsManager
from resources.phase_coordinator.models import PhaseContext

logger = logging.getLogger(__name__)

class CheckpointManager:
    """Manages checkpoints for phases"""
    
    def __init__(self, 
                event_queue: EventQueue, 
                state_manager: StateManager,
                metrics_manager: MetricsManager):
        """
        Initialize the checkpoint manager
        
        Args:
            event_queue: Event queue for sending events
            state_manager: State manager for persisting checkpoints
            metrics_manager: Metrics manager for recording checkpoint operations
        """
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._metrics_manager = metrics_manager
        self._checkpoint_data: Dict[str, Dict[str, Any]] = {}
    
    async def create_checkpoint(self, phase_id: str, context: PhaseContext) -> str:
        """
        Create a checkpoint for the current phase state
        
        Args:
            phase_id: The phase identifier
            context: The phase context to checkpoint
            
        Returns:
            str: Checkpoint identifier
        """
        if not context:
            logger.error(f"Cannot create checkpoint for unknown phase: {phase_id}")
            raise ValueError(f"Phase {phase_id} not found")
            
        # Generate checkpoint ID
        checkpoint_id = f"checkpoint_{phase_id}_{int(time.time())}"
        
        # Store phase context
        context_dict = context.to_dict()
        self._checkpoint_data[checkpoint_id] = context_dict
        
        # Add checkpoint to phase context
        context.checkpoint_ids.append(checkpoint_id)
        
        # Persist checkpoint
        await self._state_manager.set_state(
            f"phase_checkpoint:{checkpoint_id}",
            context_dict,
            ResourceType.STATE
        )
        
        logger.info(f"Created checkpoint {checkpoint_id} for phase {phase_id}")
        
        # Determine phase type value for metrics
        phase_type_value = context.phase_type.value if hasattr(context.phase_type, 'value') else str(context.phase_type)
        
        # Record metric for checkpoint creation
        await self._metrics_manager.record_metric(
            f"phase_coordinator:checkpoint_create:{phase_type_value}",
            1.0,
            metadata={
                "phase_id": phase_id,
                "checkpoint_id": checkpoint_id,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return checkpoint_id
    
    async def restore_from_checkpoint(self, checkpoint_id: str) -> Optional[PhaseContext]:
        """
        Restore a phase from a checkpoint
        
        Args:
            checkpoint_id: The checkpoint identifier
            
        Returns:
            Optional[PhaseContext]: The restored phase context or None if checkpoint not found
        """
        # Check if checkpoint exists in memory
        checkpoint_data = self._checkpoint_data.get(checkpoint_id)
        
        # If not in memory, try to load from state manager
        if not checkpoint_data:
            checkpoint_entry = await self._state_manager.get_state(f"phase_checkpoint:{checkpoint_id}")
            if not checkpoint_entry:
                logger.error(f"Checkpoint {checkpoint_id} not found")
                return None
                
            checkpoint_data = checkpoint_entry.state
            
        # Restore phase context
        context = PhaseContext.from_dict(checkpoint_data)
        phase_id = context.phase_id
        
        # Determine phase type value for metrics
        phase_type_value = context.phase_type.value if hasattr(context.phase_type, 'value') else str(context.phase_type)
        
        # Record metric for checkpoint restoration
        await self._metrics_manager.record_metric(
            f"phase_coordinator:checkpoint_restore:{phase_type_value}",
            1.0,
            metadata={
                "phase_id": phase_id,
                "checkpoint_id": checkpoint_id,
                "timestamp": datetime.now().isoformat()
            }
        )
            
        # Emit restore event
        await self._event_queue.emit(
            ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
            {
                "resource_id": f"phase:{phase_id}",
                "state": "restored",
                "checkpoint_id": checkpoint_id,
                "restored_state": context.state.name
            }
        )
        
        logger.info(f"Restored phase {phase_id} from checkpoint {checkpoint_id}")
        
        return context
    
    async def rollback_to_checkpoint(self, checkpoint_id: str) -> Optional[PhaseContext]:
        """
        Roll back to a previously created checkpoint
        
        Args:
            checkpoint_id: The checkpoint ID to roll back to
            
        Returns:
            Optional[PhaseContext]: The restored phase context or None if rollback failed
        """
        context = await self.restore_from_checkpoint(checkpoint_id)
        
        if context:
            # Emit rollback event
            await self._event_queue.emit(
                ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
                {
                    "resource_id": "phase_coordinator",
                    "state": "rolled_back",
                    "checkpoint_id": checkpoint_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Record metric
            await self._metrics_manager.record_metric(
                "phase_coordinator:rollback",
                1.0,
                metadata={
                    "checkpoint_id": checkpoint_id,
                    "success": True,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            return context
        
        # Record failed rollback metric
        await self._metrics_manager.record_metric(
            "phase_coordinator:rollback",
            0.0,
            metadata={
                "checkpoint_id": checkpoint_id,
                "success": False,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return None
    
    def get_checkpoint_data(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the raw checkpoint data
        
        Args:
            checkpoint_id: The checkpoint identifier
            
        Returns:
            Optional[Dict[str, Any]]: The checkpoint data or None if not found
        """
        return self._checkpoint_data.get(checkpoint_id)