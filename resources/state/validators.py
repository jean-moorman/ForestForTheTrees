from typing import Dict, Any, Union, Set

from resources.common import ResourceState, InterfaceState


class StateTransitionValidator:
    """Validates state transitions based on resource type"""
    
    # Define valid state transitions
    _RESOURCE_TRANSITIONS = {
        ResourceState.ACTIVE: {ResourceState.PAUSED, ResourceState.FAILED, ResourceState.TERMINATED},
        ResourceState.PAUSED: {ResourceState.ACTIVE, ResourceState.TERMINATED},
        ResourceState.FAILED: {ResourceState.RECOVERED, ResourceState.TERMINATED},
        ResourceState.RECOVERED: {ResourceState.ACTIVE, ResourceState.TERMINATED},
        ResourceState.TERMINATED: set()  # Terminal state
    }

    _INTERFACE_TRANSITIONS = {
        InterfaceState.INITIALIZED: {InterfaceState.ACTIVE, InterfaceState.ERROR},
        InterfaceState.ACTIVE: {InterfaceState.DISABLED, InterfaceState.ERROR, InterfaceState.VALIDATING},
        InterfaceState.DISABLED: {InterfaceState.ACTIVE},
        InterfaceState.ERROR: {InterfaceState.INITIALIZED, InterfaceState.DISABLED},
        InterfaceState.VALIDATING: {InterfaceState.ACTIVE, InterfaceState.ERROR, InterfaceState.PROPAGATING},
        InterfaceState.PROPAGATING: {InterfaceState.ACTIVE, InterfaceState.ERROR}
    }

    @classmethod
    def validate_transition(cls, 
                          current_state: Union[ResourceState, InterfaceState, Dict[str, Any]],
                          new_state: Union[ResourceState, InterfaceState, Dict[str, Any]]) -> bool:
        """
        Validate if a state transition is allowed
        
        For dictionary states, we allow any transition.
        For enum states, we enforce the defined transition rules.
        """
        # Allow self-transitions (same state to same state)
        if current_state == new_state:
            return True
    
        # If either state is a dict, allow the transition (custom states)
        if isinstance(current_state, dict) or isinstance(new_state, dict):
            return True
            
        # Type mismatch - don't allow transitions between different state types
        if type(current_state) != type(new_state):
            return False
            
        # Handle ResourceState transitions
        if isinstance(current_state, ResourceState) and isinstance(new_state, ResourceState):
            return new_state in cls._RESOURCE_TRANSITIONS.get(current_state, set())
            
        # Handle InterfaceState transitions
        elif isinstance(current_state, InterfaceState) and isinstance(new_state, InterfaceState):
            return new_state in cls._INTERFACE_TRANSITIONS.get(current_state, set())
            
        # Unknown state types
        return False

    @classmethod
    def get_valid_transitions(cls, 
                            current_state: Union[ResourceState, InterfaceState, Dict[str, Any]]) -> Set:
        """Get valid next states for current state"""
        
        # For dictionary states, we can't predict valid transitions
        if isinstance(current_state, dict):
            return set()
            
        # Handle ResourceState transitions
        if isinstance(current_state, ResourceState):
            return cls._RESOURCE_TRANSITIONS.get(current_state, set()).copy()
            
        # Handle InterfaceState transitions
        elif isinstance(current_state, InterfaceState):
            return cls._INTERFACE_TRANSITIONS.get(current_state, set()).copy()
            
        # Unknown state type
        return set()