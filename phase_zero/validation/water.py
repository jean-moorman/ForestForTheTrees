import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from resources import ResourceType, HealthStatus

logger = logging.getLogger(__name__)

async def propagate_guideline_update(
        agent_id: str, 
        updated_guideline: Dict,
        affected_agents: List[str] = None,
        event_queue=None,
        health_tracker=None,
        state_manager=None) -> Dict:
    """Water mechanism: Propagate guideline updates to affected downstream components.
    
    This method implements the Water elemental guideline integration by
    ensuring changes propagate properly through the system.
    
    Args:
        agent_id: The ID of the agent whose guideline was updated
        updated_guideline: The updated guideline content
        affected_agents: List of downstream agents to propagate to (if None, determined automatically)
        
    Returns:
        Dict with propagation results including:
            - success: Whether the propagation was successful
            - affected_agents: List of agents that received updates
            - failures: List of any agents that failed to update
            - metadata: Additional propagation information
    """
    logger.info(f"Propagating guideline update from agent {agent_id}")
    
    propagation_id = f"guideline_propagation_{datetime.now().isoformat()}"
    
    try:
        # Update health status
        if health_tracker:
            await health_tracker.update_health(
                f"water_propagation_{propagation_id}",
                HealthStatus(
                    status="HEALTHY",
                    source="phase_zero_orchestrator",
                    description=f"Propagating update from {agent_id}",
                    metadata={"agent_id": agent_id}
                )
            )
        
        # Store propagation request
        if state_manager:
            await state_manager.set_state(
                f"guideline_propagation:{propagation_id}",
                {
                    "agent_id": agent_id,
                    "timestamp": datetime.now().isoformat(),
                    "updated_guideline": updated_guideline,
                    "status": "propagating"
                },
                resource_type=ResourceType.STATE
            )
        
        # Determine affected downstream agents if not specified
        if affected_agents is None:
            affected_agents = await _determine_downstream_agents(agent_id)
        
        # Track affected agents
        if state_manager:
            await state_manager.set_state(
                f"guideline_propagation:{propagation_id}:affected_agents",
                affected_agents,
                resource_type=ResourceType.STATE
            )
        
        # Initialize propagation results
        propagation_results = {
            "success": True,
            "affected_agents": affected_agents,
            "updates": [],
            "failures": [],
            "metadata": {
                "propagation_id": propagation_id,
                "origin_agent": agent_id,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Propagate to each affected agent
        for downstream_agent in affected_agents:
            try:
                # Generate contextual update for this specific agent
                context = await _generate_propagation_context(
                    agent_id, downstream_agent, updated_guideline
                )
                
                # Apply update to downstream agent's guidelines
                update_result = await _apply_guideline_update(
                    downstream_agent, context, updated_guideline
                )
                
                # Track result
                propagation_results["updates"].append({
                    "agent": downstream_agent,
                    "success": update_result["success"],
                    "context_provided": context is not None,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Track any failures
                if not update_result["success"]:
                    propagation_results["failures"].append({
                        "agent": downstream_agent,
                        "reason": update_result.get("reason", "Unknown failure"),
                        "timestamp": datetime.now().isoformat()
                    })
                    
            except Exception as e:
                logger.error(f"Error propagating to agent {downstream_agent}: {e}")
                
                # Track failure
                propagation_results["failures"].append({
                    "agent": downstream_agent,
                    "reason": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        # Update overall success status
        if propagation_results["failures"]:
            propagation_results["success"] = False
        
        # Store propagation result
        if state_manager:
            await state_manager.set_state(
                f"guideline_propagation:{propagation_id}",
                {
                    **propagation_results,
                    "status": "completed"
                },
                resource_type=ResourceType.STATE
            )
        
        # Update health status
        if health_tracker:
            status = "HEALTHY" if propagation_results["success"] else "WARNING"
            await health_tracker.update_health(
                f"water_propagation_{propagation_id}",
                HealthStatus(
                    status=status,
                    source="phase_zero_orchestrator",
                    description=f"Guideline propagation completed with {len(propagation_results['updates'])} updates and {len(propagation_results['failures'])} failures",
                    metadata={
                        "agent_id": agent_id,
                        "success": propagation_results["success"],
                        "affected_count": len(affected_agents)
                    }
                )
            )
        
        return propagation_results
        
    except Exception as e:
        logger.error(f"Error in guideline propagation: {e}")
        
        # Update error state
        if health_tracker:
            await health_tracker.update_health(
                f"water_propagation_{propagation_id}",
                HealthStatus(
                    status="CRITICAL",
                    source="phase_zero_orchestrator",
                    description=f"Guideline propagation error: {str(e)}",
                    metadata={"error": str(e), "agent_id": agent_id}
                )
            )
        
        # Store error state
        if state_manager:
            await state_manager.set_state(
                f"guideline_propagation:{propagation_id}",
                {
                    "agent_id": agent_id,
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                    "status": "error"
                },
                resource_type=ResourceType.STATE
            )
        
        # Return error result
        return {
            "success": False,
            "affected_agents": affected_agents or [],
            "updates": [],
            "failures": [
                {
                    "agent": "all",
                    "reason": f"Propagation error: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "metadata": {
                "propagation_id": propagation_id,
                "origin_agent": agent_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        }


async def _determine_downstream_agents(agent_id: str) -> List[str]:
    """Determine which downstream agents are affected by changes to a specific agent.
    
    The dependency chain is:
    garden_planner -> environmental_analysis -> root_system -> tree_placement
    """
    dependency_chain = {
        "garden_planner": ["environmental_analysis", "root_system", "tree_placement"],
        "environmental_analysis": ["root_system", "tree_placement"],
        "root_system": ["tree_placement"],
        "tree_placement": []
    }
    
    return dependency_chain.get(agent_id, [])


async def _generate_propagation_context(
                                 origin_agent: str, 
                                 target_agent: str, 
                                 updated_guideline: Dict) -> Optional[Dict]:
    """Generate contextual information for a propagated update.
    
    This provides the downstream agent with context about why/how
    this update affects them.
    """
    # This would be implemented with LLM-based context generation
    # For now, we'll return a simple context
    return {
        "origin_agent": origin_agent,
        "update_summary": f"Update from {origin_agent} that affects {target_agent}",
        "timestamp": datetime.now().isoformat()
    }


async def _apply_guideline_update(
                             agent_id: str, 
                             context: Dict, 
                             updated_upstream_guideline: Dict) -> Dict:
    """Apply a propagated guideline update to a downstream agent.
    
    This would trigger the agent to update its own guidelines based on
    upstream changes.
    """
    # This would be implemented with the actual agent's update mechanism
    # For now, we'll simulate success
    return {
        "success": True,
        "agent_id": agent_id,
        "timestamp": datetime.now().isoformat()
    }