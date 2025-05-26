"""
Functionality interface implementation for the FFTT system.
"""

import logging
from typing import Dict, List, Any, Optional, Set

from resources import (
    EventQueue,
    StateManager,
    ResourceType
)
from ..base import BaseInterface

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FunctionalityInterface(BaseInterface):
    """
    Interface for functionalities in the FFTT system.
    Functionalities are the smallest units of implementation within features.
    """
    
    def __init__(
        self, 
        functionality_id: str, 
        event_queue: EventQueue = None,
        state_manager: StateManager = None,
        context_manager=None,
        cache_manager=None,
        metrics_manager=None,
        error_handler=None,
        memory_monitor=None
    ):
        """
        Initialize the functionality interface.
        
        Args:
            functionality_id: ID of the functionality
            event_queue: Queue for event handling
            state_manager: Manager for state persistence
            context_manager: Optional manager for context
            cache_manager: Optional manager for caching
            metrics_manager: Optional manager for metrics
            error_handler: Optional handler for errors
            memory_monitor: Optional monitor for memory usage
        """
        super().__init__(
            f"functionality:{functionality_id}", 
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor
        )
        self.functionality_id = functionality_id
        self._functionality_state: Dict[str, Any] = {}
        self._dependencies: Set[str] = set()
        
    async def set_functionality_state(self, key: str, value: Any) -> None:
        """
        Set a state value for this functionality.
        
        Args:
            key: State key
            value: State value
        """
        self._functionality_state[key] = value
        
        # Store in state manager if available
        if self._state_manager:
            await self._state_manager.set_state(
                f"functionality:{self.functionality_id}:state:{key}",
                value,
                resource_type=ResourceType.STATE
            )
        
    async def get_functionality_state(self, key: str) -> Optional[Any]:
        """
        Get a state value for this functionality.
        
        Args:
            key: State key
            
        Returns:
            State value or None if not found
        """
        # Try to get from local state first
        if key in self._functionality_state:
            return self._functionality_state.get(key)
            
        # Try to get from state manager if available
        if self._state_manager:
            state = await self._state_manager.get_state(
                f"functionality:{self.functionality_id}:state:{key}"
            )
            
            if state is not None:
                # Update local cache
                self._functionality_state[key] = state
                return state
                
        return None
        
    async def add_dependency(self, functionality_id: str) -> None:
        """
        Add a dependency on another functionality.
        
        Args:
            functionality_id: ID of the functionality this functionality depends on
        """
        self._dependencies.add(functionality_id)
        
        # Store in state manager if available
        if self._state_manager:
            await self._state_manager.set_state(
                f"functionality:{self.functionality_id}:dependencies",
                list(self._dependencies),
                resource_type=ResourceType.STATE
            )
            
        logger.info(f"Added dependency on {functionality_id} to functionality {self.functionality_id}")
        
    async def get_dependencies(self) -> List[str]:
        """
        Get the list of dependencies for this functionality.
        
        Returns:
            List of functionality IDs this functionality depends on
        """
        # If we don't have dependencies loaded, try to get them from state
        if not self._dependencies and self._state_manager:
            dependencies = await self._state_manager.get_state(
                f"functionality:{self.functionality_id}:dependencies"
            )
            
            if dependencies:
                self._dependencies = set(dependencies)
        
        return list(self._dependencies)
        
    async def validate(self) -> Dict[str, Any]:
        """
        Validate this functionality's structure and dependencies.
        
        Returns:
            Dict with validation results
        """
        # Basic validation, to be enhanced in derived classes
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
            
        # Check for cyclic dependencies
        dependencies = await self.get_dependencies()
        if self.functionality_id in dependencies:
            validation_result["errors"].append("Functionality depends on itself")
            validation_result["valid"] = False
            
        return validation_result