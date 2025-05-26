"""
Feature interface implementation for the FFTT system.
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


class FeatureInterface(BaseInterface):
    """
    Interface for features in the FFTT system.
    Features are functional units that make up components and contain functionalities.
    """
    
    def __init__(
        self, 
        feature_id: str, 
        event_queue: EventQueue = None,
        state_manager: StateManager = None,
        context_manager=None,
        cache_manager=None,
        metrics_manager=None,
        error_handler=None,
        memory_monitor=None
    ):
        """
        Initialize the feature interface.
        
        Args:
            feature_id: ID of the feature
            event_queue: Queue for event handling
            state_manager: Manager for state persistence
            context_manager: Optional manager for context
            cache_manager: Optional manager for caching
            metrics_manager: Optional manager for metrics
            error_handler: Optional handler for errors
            memory_monitor: Optional monitor for memory usage
        """
        super().__init__(
            f"feature:{feature_id}", 
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor
        )
        self.feature_id = feature_id
        self._feature_state: Dict[str, Any] = {}
        self._functionalities: Set[str] = set()
        self._dependencies: Set[str] = set()
        
    async def set_feature_state(self, key: str, value: Any) -> None:
        """
        Set a state value for this feature.
        
        Args:
            key: State key
            value: State value
        """
        self._feature_state[key] = value
        
        # Store in state manager if available
        if self._state_manager:
            await self._state_manager.set_state(
                f"feature:{self.feature_id}:state:{key}",
                value,
                resource_type=ResourceType.STATE
            )
        
    async def get_feature_state(self, key: str) -> Optional[Any]:
        """
        Get a state value for this feature.
        
        Args:
            key: State key
            
        Returns:
            State value or None if not found
        """
        # Try to get from local state first
        if key in self._feature_state:
            return self._feature_state.get(key)
            
        # Try to get from state manager if available
        if self._state_manager:
            state = await self._state_manager.get_state(
                f"feature:{self.feature_id}:state:{key}"
            )
            
            if state is not None:
                # Update local cache
                self._feature_state[key] = state
                return state
                
        return None
        
    async def add_functionality(self, functionality_id: str) -> None:
        """
        Add a functionality to this feature.
        
        Args:
            functionality_id: ID of the functionality to add
        """
        self._functionalities.add(functionality_id)
        
        # Store in state manager if available
        if self._state_manager:
            await self._state_manager.set_state(
                f"feature:{self.feature_id}:functionalities",
                list(self._functionalities),
                resource_type=ResourceType.STATE
            )
            
        logger.info(f"Added functionality {functionality_id} to feature {self.feature_id}")
        
    async def get_functionalities(self) -> List[str]:
        """
        Get the list of functionalities in this feature.
        
        Returns:
            List of functionality IDs
        """
        # If we don't have functionalities loaded, try to get them from state
        if not self._functionalities and self._state_manager:
            functionalities = await self._state_manager.get_state(
                f"feature:{self.feature_id}:functionalities"
            )
            
            if functionalities:
                self._functionalities = set(functionalities)
        
        return list(self._functionalities)
        
    async def add_dependency(self, feature_id: str) -> None:
        """
        Add a dependency on another feature.
        
        Args:
            feature_id: ID of the feature this feature depends on
        """
        self._dependencies.add(feature_id)
        
        # Store in state manager if available
        if self._state_manager:
            await self._state_manager.set_state(
                f"feature:{self.feature_id}:dependencies",
                list(self._dependencies),
                resource_type=ResourceType.STATE
            )
            
        logger.info(f"Added dependency on {feature_id} to feature {self.feature_id}")
        
    async def get_dependencies(self) -> List[str]:
        """
        Get the list of dependencies for this feature.
        
        Returns:
            List of feature IDs this feature depends on
        """
        # If we don't have dependencies loaded, try to get them from state
        if not self._dependencies and self._state_manager:
            dependencies = await self._state_manager.get_state(
                f"feature:{self.feature_id}:dependencies"
            )
            
            if dependencies:
                self._dependencies = set(dependencies)
        
        return list(self._dependencies)
        
    async def validate(self) -> Dict[str, Any]:
        """
        Validate this feature's structure and dependencies.
        
        Returns:
            Dict with validation results
        """
        # Basic validation, to be enhanced in derived classes
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check for functionalities
        functionalities = await self.get_functionalities()
        if not functionalities:
            validation_result["warnings"].append("Feature has no functionalities")
            
        # Check for cyclic dependencies
        dependencies = await self.get_dependencies()
        if self.feature_id in dependencies:
            validation_result["errors"].append("Feature depends on itself")
            validation_result["valid"] = False
            
        return validation_result