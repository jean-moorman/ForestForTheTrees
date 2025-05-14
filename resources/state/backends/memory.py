from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

from resources.state.backends.base import StateStorageBackend
from resources.state.models import StateEntry, StateSnapshot


class MemoryStateBackend(StateStorageBackend):
    """In-memory storage backend (default, no persistence)"""
    
    def __init__(self):
        """Initialize an empty in-memory store"""
        self._states: Dict[str, StateEntry] = {}
        self._history: Dict[str, List[StateEntry]] = defaultdict(list)
        self._snapshots: Dict[str, List[StateSnapshot]] = defaultdict(list)
        
    async def save_state(self, resource_id: str, state_entry: StateEntry) -> bool:
        """Save a state entry to memory"""
        self._states[resource_id] = state_entry
        self._history[resource_id].append(state_entry)
        return True
        
    async def save_snapshot(self, resource_id: str, snapshot: StateSnapshot) -> bool:
        """Save a state snapshot to memory"""
        self._snapshots[resource_id].append(snapshot)
        return True
        
    async def load_state(self, resource_id: str) -> Optional[StateEntry]:
        """Load the latest state for a resource from memory"""
        return self._states.get(resource_id)
        
    async def load_history(self, resource_id: str, limit: Optional[int] = None) -> List[StateEntry]:
        """Load state history for a resource from memory"""
        history = self._history.get(resource_id, [])
        if limit:
            return history[-limit:]
        return history
        
    async def load_snapshots(self, resource_id: str, limit: Optional[int] = None) -> List[StateSnapshot]:
        """Load snapshots for a resource from memory"""
        snapshots = self._snapshots.get(resource_id, [])
        if limit:
            return snapshots[-limit:]
        return snapshots
        
    async def get_all_resource_ids(self) -> List[str]:
        """Get all resource IDs in memory"""
        return list(self._states.keys())
        
    async def cleanup(self, older_than: Optional[datetime] = None) -> int:
        """Clean up old entries, returns count of removed items"""
        # Memory backend doesn't need special cleanup
        return 0