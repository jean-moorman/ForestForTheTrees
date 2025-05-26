"""
Integration module for FFTT system.

Provides interfaces and states for managing component and feature integration.
This module defines the integration points and validation mechanisms used
throughout the system to ensure proper component connectivity.
"""

from enum import Enum, auto
from typing import Dict, Any, Set, Optional, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class IntegrationState(Enum):
    """States for integration processes."""
    PENDING = auto()
    IN_PROGRESS = auto()
    VALIDATING = auto()
    COMPLETED = auto()
    FAILED = auto()
    ROLLBACK = auto()


class IntegrationType(Enum):
    """Types of integration."""
    COMPONENT = auto()
    FEATURE = auto()
    FUNCTIONALITY = auto()
    SYSTEM = auto()


class IntegrationInterface:
    """Interface for managing integration points and validation."""
    
    def __init__(self, interface_id: str):
        """Initialize the integration interface.
        
        Args:
            interface_id: The ID of the interface creating integration points
        """
        self.interface_id = interface_id
        self.integration_points: Dict[str, Dict[str, Any]] = {}
        self.integration_states: Dict[str, IntegrationState] = {}
        self._logger = logging.getLogger(f"{__name__}.{interface_id}")
        
    def create_integration_point(self, integration_id: str, 
                               integration_type: str, 
                               components: Set[str],
                               metadata: Optional[Dict[str, Any]] = None) -> None:
        """Create an integration point between components.
        
        Args:
            integration_id: Unique identifier for this integration
            integration_type: Type of integration (COMPONENT, FEATURE, etc.)
            components: Set of component IDs involved in integration
            metadata: Optional metadata for the integration
        """
        if metadata is None:
            metadata = {}
            
        self.integration_points[integration_id] = {
            'type': integration_type,
            'components': components,
            'created_by': self.interface_id,
            'created_at': datetime.now(),
            'metadata': metadata
        }
        
        self.integration_states[integration_id] = IntegrationState.PENDING
        
        self._logger.info(f"Created integration point {integration_id} of type {integration_type} "
                         f"between components: {components}")
    
    def validate_integration(self, integration_id: str) -> bool:
        """Validate an integration point.
        
        Args:
            integration_id: ID of the integration to validate
            
        Returns:
            True if integration is valid, False otherwise
        """
        if integration_id not in self.integration_points:
            self._logger.error(f"Integration {integration_id} not found")
            return False
            
        integration_point = self.integration_points[integration_id]
        components = integration_point['components']
        
        # Basic validation - ensure all components exist
        if len(components) < 2:
            self._logger.error(f"Integration {integration_id} requires at least 2 components")
            self.integration_states[integration_id] = IntegrationState.FAILED
            return False
            
        self.integration_states[integration_id] = IntegrationState.VALIDATING
        
        # For now, assume validation passes
        # In a real implementation, this would check component compatibility,
        # interface contracts, dependency constraints, etc.
        
        self.integration_states[integration_id] = IntegrationState.COMPLETED
        self._logger.info(f"Integration {integration_id} validated successfully")
        return True
    
    def get_integration_state(self, integration_id: str) -> Optional[IntegrationState]:
        """Get the current state of an integration.
        
        Args:
            integration_id: ID of the integration
            
        Returns:
            Current integration state or None if not found
        """
        return self.integration_states.get(integration_id)
    
    def set_integration_state(self, integration_id: str, state: IntegrationState) -> None:
        """Set the state of an integration.
        
        Args:
            integration_id: ID of the integration
            state: New state to set
        """
        if integration_id in self.integration_points:
            self.integration_states[integration_id] = state
            self._logger.info(f"Integration {integration_id} state set to {state}")
        else:
            self._logger.error(f"Cannot set state for unknown integration {integration_id}")
    
    def get_integration_points(self) -> Dict[str, Dict[str, Any]]:
        """Get all integration points managed by this interface.
        
        Returns:
            Dictionary of integration points
        """
        return self.integration_points.copy()
    
    def remove_integration_point(self, integration_id: str) -> bool:
        """Remove an integration point.
        
        Args:
            integration_id: ID of the integration to remove
            
        Returns:
            True if removed successfully, False if not found
        """
        if integration_id in self.integration_points:
            del self.integration_points[integration_id]
            del self.integration_states[integration_id]
            self._logger.info(f"Removed integration point {integration_id}")
            return True
        else:
            self._logger.warning(f"Integration point {integration_id} not found for removal")
            return False