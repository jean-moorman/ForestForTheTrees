"""
Phase One Agent Coordination Module.

Provides coordination mechanisms to prevent resource contention between agents
during peak operations.
"""

from .agent_coordinator import AgentUpdateCoordinator, AgentPriority, get_agent_coordinator

__all__ = ['AgentUpdateCoordinator', 'AgentPriority', 'get_agent_coordinator']