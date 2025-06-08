from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List

from resources.state.models import StateEntry, StateSnapshot


class StateStorageBackend(ABC):
    """Abstract interface for state storage backends"""
    
    @abstractmethod
    async def save_state(self, resource_id: str, state_entry: StateEntry) -> bool:
        """Save a state entry to storage"""
        pass
        
    @abstractmethod
    async def save_snapshot(self, resource_id: str, snapshot: StateSnapshot) -> bool:
        """Save a state snapshot to storage"""
        pass
        
    @abstractmethod
    async def load_state(self, resource_id: str) -> Optional[StateEntry]:
        """Load the latest state for a resource"""
        pass
        
    @abstractmethod
    async def load_history(self, resource_id: str, limit: Optional[int] = None) -> List[StateEntry]:
        """Load state history for a resource"""
        pass
        
    @abstractmethod
    async def load_snapshots(self, resource_id: str, limit: Optional[int] = None) -> List[StateSnapshot]:
        """Load snapshots for a resource"""
        pass
        
    @abstractmethod
    async def get_all_resource_ids(self) -> List[str]:
        """Get all resource IDs in storage"""
        pass
        
    @abstractmethod
    async def cleanup(self, older_than: Optional[datetime] = None) -> int:
        """Clean up old entries, returns count of removed items"""
        pass
        
    @abstractmethod
    async def delete_state(self, resource_id: str) -> bool:
        """Delete a state entry from storage"""
        pass
        
    @abstractmethod
    async def clear_all_states(self) -> int:
        """Clear all states from storage, returns count of removed items"""
        pass