"""
Agent Update Coordinator for Phase One agents.

Coordinates agent state updates to prevent resource contention during peak operations
like Earth Agent validation + Garden Planner refinement.
"""

import asyncio
import logging
import threading
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Set
from enum import Enum, auto

logger = logging.getLogger(__name__)

class AgentPriority(Enum):
    """Priority levels for agent coordination."""
    LOW = auto()
    NORMAL = auto()
    HIGH = auto()
    CRITICAL = auto()

class AgentUpdateCoordinator:
    """
    Coordinates agent state updates to prevent resource contention.
    
    This class implements a coordination mechanism to stagger agent updates
    and prevent multiple agents from overwhelming shared resources simultaneously.
    """
    _instance = None
    _instance_lock = threading.RLock()
    
    def __new__(cls):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        with self._instance_lock:
            if not self._initialized:
                # Active update tracking
                self._active_updates: Dict[str, Dict[str, Any]] = {}
                self._coordination_lock = asyncio.Lock()
                
                # Configuration
                self._max_concurrent_updates = 3  # Limit concurrent updates
                self._max_high_priority_updates = 2  # Limit high priority updates
                self._update_timeout = 120.0  # Maximum time for an update
                
                # Queue for waiting updates
                self._waiting_updates: Dict[str, asyncio.Event] = {}
                
                # Statistics
                self._coordination_stats = {
                    "total_coordinated": 0,
                    "contention_prevented": 0,
                    "average_wait_time": 0.0,
                    "peak_concurrent": 0
                }
                
                self._initialized = True
                logger.info("AgentUpdateCoordinator initialized")
            else:
                logger.debug("Reusing existing AgentUpdateCoordinator instance")
    
    async def initialize_async(self):
        """Initialize async components."""
        if not hasattr(self, '_coordination_lock') or self._coordination_lock is None:
            self._coordination_lock = asyncio.Lock()
    
    @asynccontextmanager
    async def request_update_slot(
        self, 
        agent_id: str, 
        priority: AgentPriority = AgentPriority.NORMAL,
        estimated_duration: float = 30.0,
        operation_type: str = "state_update"
    ):
        """
        Request a slot for agent state update with backpressure and priority.
        
        Args:
            agent_id: ID of the agent requesting update
            priority: Priority level for the update
            estimated_duration: Estimated duration in seconds
            operation_type: Type of operation being performed
            
        Yields:
            Context manager for the update slot
        """
        await self.initialize_async()
        
        start_wait_time = datetime.now()
        
        # Wait for available slot
        await self._wait_for_slot(agent_id, priority)
        
        wait_time = (datetime.now() - start_wait_time).total_seconds()
        
        # Register the update
        async with self._coordination_lock:
            self._active_updates[agent_id] = {
                'start_time': datetime.now(),
                'estimated_duration': estimated_duration,
                'priority': priority,
                'operation_type': operation_type,
                'actual_wait_time': wait_time
            }
            
            # Update statistics
            self._coordination_stats["total_coordinated"] += 1
            if wait_time > 0.1:  # If we had to wait significantly
                self._coordination_stats["contention_prevented"] += 1
            
            current_concurrent = len(self._active_updates)
            if current_concurrent > self._coordination_stats["peak_concurrent"]:
                self._coordination_stats["peak_concurrent"] = current_concurrent
            
            logger.debug(f"Agent {agent_id} acquired update slot (priority: {priority.name}, "
                        f"wait: {wait_time:.2f}s, concurrent: {current_concurrent})")
        
        try:
            yield
        finally:
            # Cleanup and notify waiting agents
            async with self._coordination_lock:
                if agent_id in self._active_updates:
                    update_info = self._active_updates.pop(agent_id)
                    actual_duration = (datetime.now() - update_info['start_time']).total_seconds()
                    
                    logger.debug(f"Agent {agent_id} released update slot "
                                f"(duration: {actual_duration:.2f}s)")
                
                # Update average wait time
                total_wait = self._coordination_stats.get("total_wait_time", 0.0)
                total_count = self._coordination_stats["total_coordinated"]
                total_wait += wait_time
                self._coordination_stats["average_wait_time"] = total_wait / total_count if total_count > 0 else 0.0
                self._coordination_stats["total_wait_time"] = total_wait
            
            # Notify waiting agents
            await self._notify_waiting_agents()
    
    async def _wait_for_slot(self, agent_id: str, priority: AgentPriority):
        """Wait for an available update slot based on priority and limits."""
        while True:
            async with self._coordination_lock:
                current_count = len(self._active_updates)
                high_priority_count = sum(
                    1 for update in self._active_updates.values()
                    if update['priority'] in [AgentPriority.HIGH, AgentPriority.CRITICAL]
                )
                
                # Check if slot is available
                slot_available = False
                
                if priority == AgentPriority.CRITICAL:
                    # Critical always gets through, but respect absolute max
                    slot_available = current_count < self._max_concurrent_updates
                elif priority == AgentPriority.HIGH:
                    # High priority respects high priority limit
                    slot_available = (current_count < self._max_concurrent_updates and 
                                    high_priority_count < self._max_high_priority_updates)
                else:
                    # Normal/Low priority waits for no high priority and available slots
                    slot_available = (current_count < self._max_concurrent_updates and 
                                    high_priority_count == 0)
                
                if slot_available:
                    return  # Slot is available
                
                # Need to wait - set up wait event
                if agent_id not in self._waiting_updates:
                    self._waiting_updates[agent_id] = asyncio.Event()
                
                wait_event = self._waiting_updates[agent_id]
            
            # Wait for notification (with timeout to prevent infinite waits)
            try:
                await asyncio.wait_for(wait_event.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                # Timeout - try again (prevents deadlocks)
                continue
            
            # Clear the event for next time
            wait_event.clear()
    
    async def _notify_waiting_agents(self):
        """Notify waiting agents that a slot may be available."""
        async with self._coordination_lock:
            # Copy the waiting agents to avoid modification during iteration
            waiting_agents = list(self._waiting_updates.items())
        
        # Notify all waiting agents to check again
        for agent_id, event in waiting_agents:
            try:
                event.set()
            except Exception as e:
                logger.warning(f"Error notifying waiting agent {agent_id}: {e}")
    
    async def force_release_agent(self, agent_id: str):
        """Force release an agent from coordination (for timeout/error recovery)."""
        async with self._coordination_lock:
            if agent_id in self._active_updates:
                self._active_updates.pop(agent_id)
                logger.warning(f"Force released agent {agent_id} from coordination")
            
            if agent_id in self._waiting_updates:
                self._waiting_updates.pop(agent_id)
        
        await self._notify_waiting_agents()
    
    def get_coordination_stats(self) -> Dict[str, Any]:
        """Get coordination statistics."""
        return dict(self._coordination_stats)
    
    def get_active_updates(self) -> Dict[str, Dict[str, Any]]:
        """Get currently active updates."""
        return dict(self._active_updates)
    
    async def cleanup_stale_updates(self):
        """Clean up updates that have been running too long."""
        now = datetime.now()
        stale_agents = []
        
        async with self._coordination_lock:
            for agent_id, update_info in self._active_updates.items():
                duration = (now - update_info['start_time']).total_seconds()
                if duration > self._update_timeout:
                    stale_agents.append(agent_id)
        
        # Force release stale agents
        for agent_id in stale_agents:
            await self.force_release_agent(agent_id)
            logger.warning(f"Cleaned up stale update for agent {agent_id}")

# Singleton instance for global access
_coordinator_instance = None

def get_agent_coordinator() -> AgentUpdateCoordinator:
    """Get the global agent update coordinator instance."""
    global _coordinator_instance
    if _coordinator_instance is None:
        _coordinator_instance = AgentUpdateCoordinator()
    return _coordinator_instance