"""
Water agent coordination module for Phase Zero.

This module provides a simplified interface for the Water agent's coordination functionality. 
The previous guideline propagation functionality has been removed as part of the system refactoring.
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from resources import ResourceType, HealthStatus

logger = logging.getLogger(__name__)

async def coordinate_agents(
    first_agent: Any, 
    first_agent_output: str,
    second_agent: Any, 
    second_agent_output: str,
    coordination_context: Optional[Dict[str, Any]] = None,
    agent_interface=None,
    state_manager=None,
    event_queue=None
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Coordinate communication between two sequential agents to resolve misunderstandings.
    
    This function serves as a wrapper around the WaterAgentCoordinator from resources.water_agent.coordinator.
    
    Args:
        first_agent: The first agent in the sequence
        first_agent_output: Output from the first agent
        second_agent: The second agent in the sequence
        second_agent_output: Output from the second agent
        coordination_context: Optional context for the coordination process
        agent_interface: Optional agent interface for LLM access
        state_manager: Optional state manager for persisting state
        event_queue: Optional event queue for event emission
        
    Returns:
        Tuple containing:
        - Updated first agent output
        - Updated second agent output
        - Coordination metadata/context
    """
    try:
        # Import the coordinator here to avoid circular imports
        from resources.water_agent.coordinator import WaterAgentCoordinator
        
        # Create a coordinator instance or use a cached one
        coordinator = WaterAgentCoordinator(
            state_manager=state_manager,
            event_bus=event_queue,
            agent_interface=agent_interface
        )
        
        # Use the coordinator to handle the coordination process
        return await coordinator.coordinate_agents(
            first_agent=first_agent,
            first_agent_output=first_agent_output,
            second_agent=second_agent,
            second_agent_output=second_agent_output,
            coordination_context=coordination_context
        )
    
    except Exception as e:
        logger.error(f"Error in agent coordination: {e}")
        
        # In case of error, return the original outputs with error context
        return first_agent_output, second_agent_output, {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }