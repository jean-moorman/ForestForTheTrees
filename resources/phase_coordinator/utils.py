"""
Forest For The Trees (FFTT) Phase Coordination System - Utilities
---------------------------------------------------
Utility functions for the phase coordinator.
"""
import logging
from typing import Dict, Any, Union, Optional
from datetime import datetime

from resources.events import EventQueue, ResourceEventTypes
from resources.phase_coordinator.constants import PhaseState, PhaseType, _CUSTOM_PHASE_TYPES

logger = logging.getLogger(__name__)

async def emit_phase_state_change_event(
    event_queue: EventQueue,
    phase_id: str,
    previous_state: Optional[PhaseState],
    new_state: PhaseState,
    phase_type: Union[PhaseType, str],
    is_custom_type: bool = False,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Emit events for phase state changes
    
    Args:
        event_queue: Event queue for sending events
        phase_id: The phase identifier
        previous_state: Previous phase state (if any)
        new_state: New phase state
        phase_type: Phase type
        is_custom_type: Whether this is a custom phase type
        metadata: Optional additional metadata
    """
    # Get phase type value (handles both built-in enum and custom string)
    phase_type_value = phase_type.value if isinstance(phase_type, PhaseType) else phase_type
    
    # Emit health event
    health_event_data = {
        "component": f"phase_{phase_id}",
        "status": "HEALTHY" if new_state in (PhaseState.RUNNING, PhaseState.COMPLETED) else "DEGRADED",
        "description": f"Phase {phase_id} state changed to {new_state.name}",
        "metadata": {
            "phase_id": phase_id,
            "phase_type": phase_type_value,
            "state": new_state.name,
            "is_custom_type": is_custom_type,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    # Add custom type details if relevant
    if is_custom_type and isinstance(phase_type, str):
        custom_info = _CUSTOM_PHASE_TYPES.get(phase_type, {})
        if custom_info:
            health_event_data["metadata"]["custom_type_info"] = {
                "parent_type": custom_info.get("parent_type"),
                "description": custom_info.get("description")
            }
    
    # Add additional metadata if provided
    if metadata:
        health_event_data["metadata"].update(metadata)
            
    await event_queue.emit(
        ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value,
        health_event_data
    )
    
    # Also emit specific state change event
    state_change_event = {
        "resource_id": f"phase:{phase_id}",
        "old_state": previous_state.name if previous_state else None,
        "new_state": new_state.name,
        "phase_id": phase_id,
        "phase_type": phase_type_value,
        "is_custom_type": is_custom_type,
        "timestamp": datetime.now().isoformat()
    }
    
    await event_queue.emit(
        ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
        state_change_event
    )

def get_phase_type_value(phase_type: Union[PhaseType, str]) -> str:
    """
    Get the string value of a phase type (enum or string)
    
    Args:
        phase_type: The phase type (enum or string)
        
    Returns:
        str: The phase type value
    """
    return phase_type.value if isinstance(phase_type, PhaseType) else phase_type

def is_valid_phase_type(phase_type: Union[str, PhaseType]) -> bool:
    """
    Check if a given phase type is valid (built-in or custom)
    
    Args:
        phase_type: The phase type to check (string or enum)
        
    Returns:
        bool: True if valid phase type
    """
    if isinstance(phase_type, PhaseType):
        return True
        
    if isinstance(phase_type, str):
        # Check built-in types
        if PhaseType.from_string(phase_type) is not None:
            return True
            
        # Check custom types
        if phase_type in _CUSTOM_PHASE_TYPES:
            return True
            
    return False

def get_enhanced_status_response(phase_states: Dict[str, Any], phase_id: str) -> Dict[str, Any]:
    """
    Build enhanced status response for a phase
    
    Args:
        phase_states: Dictionary of phase states
        phase_id: The phase ID to get status for
        
    Returns:
        Dict[str, Any]: Enhanced status response
    """
    context = phase_states.get(phase_id)
    if not context:
        return {"error": f"Phase {phase_id} not found", "status": "unknown"}
        
    # Get phase type value (handles both built-in enum and custom string)
    phase_type_value = context.phase_type.value if isinstance(context.phase_type, PhaseType) else context.phase_type
        
    # Get child phase statuses if any
    child_statuses = {}
    for child_id in context.child_phases:
        child_context = phase_states.get(child_id)
        if child_context:
            # Handle phase type value for child (either enum or string)
            child_type_value = (child_context.phase_type.value 
                               if isinstance(child_context.phase_type, PhaseType) 
                               else child_context.phase_type)
            
            child_statuses[child_id] = {
                "state": child_context.state.name,
                "phase_type": child_type_value,
                "is_custom_type": child_context.is_custom_type,
                "start_time": child_context.start_time.isoformat() if child_context.start_time else None,
                "end_time": child_context.end_time.isoformat() if child_context.end_time else None
            }
            
            # Add custom type info if relevant
            if child_context.is_custom_type and isinstance(child_context.phase_type, str):
                custom_info = _CUSTOM_PHASE_TYPES.get(child_context.phase_type, {})
                if custom_info:
                    child_statuses[child_id]["custom_type_info"] = {
                        "parent_type": custom_info.get("parent_type"),
                        "description": custom_info.get("description")
                    }
    
    # Build the base status response
    status_response = {
        "phase_id": phase_id,
        "phase_type": phase_type_value,
        "is_custom_type": context.is_custom_type,
        "state": context.state.name,
        "parent_phase_id": context.parent_phase_id,
        "child_phases": list(context.child_phases),
        "child_statuses": child_statuses,
        "dependencies": list(context.dependencies),
        "start_time": context.start_time.isoformat() if context.start_time else None,
        "end_time": context.end_time.isoformat() if context.end_time else None,
        "execution_time": (context.end_time - context.start_time).total_seconds() if context.start_time and context.end_time else None,
        "error_info": context.error_info,
        "checkpoint_ids": context.checkpoint_ids,
        "metadata": context.metadata
    }
    
    # Add custom type info if this is a custom phase type
    if context.is_custom_type and phase_type_value in _CUSTOM_PHASE_TYPES:
        custom_info = _CUSTOM_PHASE_TYPES[phase_type_value]
        status_response["custom_type_info"] = {
            "parent_type": custom_info.get("parent_type"),
            "description": custom_info.get("description"),
            "registered_at": custom_info.get("registered_at"),
            "config": custom_info.get("config", {})
        }
        
        # Add inheritance chain if available
        parent_chain = []
        current_parent = custom_info.get("parent_type")
        while current_parent:
            parent_chain.append(current_parent)
            # Check if parent is a custom type too
            if current_parent in _CUSTOM_PHASE_TYPES:
                current_parent = _CUSTOM_PHASE_TYPES[current_parent].get("parent_type")
            else:
                # Built-in parent type
                break
                
        if parent_chain:
            status_response["custom_type_info"]["inheritance_chain"] = parent_chain
    
    return status_response