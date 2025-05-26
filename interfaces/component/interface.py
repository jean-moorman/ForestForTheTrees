"""
Component interface implementation for the FFTT system.
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


class ComponentInterface(BaseInterface):
    """
    Interface for components in the FFTT system.
    Components are high-level structural elements that contain features.
    """
    
    def __init__(
        self, 
        component_id: str, 
        event_queue: EventQueue,
        state_manager: StateManager,
        context_manager=None,
        cache_manager=None,
        metrics_manager=None,
        error_handler=None,
        memory_monitor=None
    ):
        """
        Initialize the component interface.
        
        Args:
            component_id: ID of the component
            event_queue: Queue for event handling
            state_manager: Manager for state persistence
            context_manager: Optional manager for context
            cache_manager: Optional manager for caching
            metrics_manager: Optional manager for metrics
            error_handler: Optional handler for errors
            memory_monitor: Optional monitor for memory usage
        """
        super().__init__(
            f"component:{component_id}", 
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor
        )
        self.component_id = component_id
        self._features: Set[str] = set()
        self._dependencies: Set[str] = set()
        
    async def add_feature(self, feature_id: str) -> None:
        """
        Add a feature to this component.
        
        Args:
            feature_id: ID of the feature to add
        """
        self._features.add(feature_id)
        
        # Store in state manager for persistence
        await self._state_manager.set_state(
            f"component:{self.component_id}:features",
            list(self._features),
            resource_type=ResourceType.STATE
        )
        
        logger.info(f"Added feature {feature_id} to component {self.component_id}")
        
    async def remove_feature(self, feature_id: str) -> bool:
        """
        Remove a feature from this component.
        
        Args:
            feature_id: ID of the feature to remove
            
        Returns:
            True if the feature was removed, False if it wasn't found
        """
        if feature_id in self._features:
            self._features.remove(feature_id)
            
            # Update state manager
            await self._state_manager.set_state(
                f"component:{self.component_id}:features",
                list(self._features),
                resource_type=ResourceType.STATE
            )
            
            logger.info(f"Removed feature {feature_id} from component {self.component_id}")
            return True
        
        logger.warning(f"Feature {feature_id} not found in component {self.component_id}")
        return False
        
    async def get_features(self) -> List[str]:
        """
        Get the list of features in this component.
        
        Returns:
            List of feature IDs
        """
        # If we don't have features loaded, try to get them from state
        if not self._features:
            features = await self._state_manager.get_state(
                f"component:{self.component_id}:features"
            )
            
            if features:
                self._features = set(features)
        
        return list(self._features)
        
    async def add_dependency(self, component_id: str) -> None:
        """
        Add a dependency on another component.
        
        Args:
            component_id: ID of the component this component depends on
        """
        self._dependencies.add(component_id)
        
        # Store in state manager for persistence
        await self._state_manager.set_state(
            f"component:{self.component_id}:dependencies",
            list(self._dependencies),
            resource_type=ResourceType.STATE
        )
        
        logger.info(f"Added dependency on {component_id} to component {self.component_id}")
        
    async def get_dependencies(self) -> List[str]:
        """
        Get the list of dependencies for this component.
        
        Returns:
            List of component IDs this component depends on
        """
        # If we don't have dependencies loaded, try to get them from state
        if not self._dependencies:
            dependencies = await self._state_manager.get_state(
                f"component:{self.component_id}:dependencies"
            )
            
            if dependencies:
                self._dependencies = set(dependencies)
        
        return list(self._dependencies)
        
    async def validate(self) -> Dict[str, Any]:
        """
        Validate this component's structure and dependencies.
        
        Returns:
            Dict with validation results
        """
        # Basic validation, to be enhanced in derived classes
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check for features
        features = await self.get_features()
        if not features:
            validation_result["warnings"].append("Component has no features")
            
        # Check for cyclic dependencies (basic implementation)
        dependencies = await self.get_dependencies()
        if self.component_id in dependencies:
            validation_result["errors"].append("Component depends on itself")
            validation_result["valid"] = False
            
        return validation_result