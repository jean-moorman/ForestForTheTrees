"""
Guideline management utilities for agent interfaces in the FFTT system.
"""

from datetime import datetime
import logging
from typing import Dict, List, Any, Optional, Tuple

from resources import (
    EventQueue,
    StateManager,
    ResourceType
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GuidelineManager:
    """
    Manages guideline updates and propagation between agents.
    """
    
    def __init__(self, event_queue: EventQueue, state_manager: StateManager, agent_id: str):
        """
        Initialize guideline manager.
        
        Args:
            event_queue: Queue for event handling
            state_manager: Manager for state persistence
            agent_id: ID of the agent
        """
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._agent_id = agent_id
        self._guideline_updates = {}
        
    async def apply_guideline_update(
        self,
        origin_agent_id: str,
        propagation_context: Dict[str, Any],
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply a guideline update propagated from an upstream agent.
        
        Args:
            origin_agent_id: ID of the agent that originated the update
            propagation_context: Detailed context about the update's impact
            update_data: The actual update data to apply
            
        Returns:
            Dict with success status and details
        """
        logger.info(f"Applying guideline update from {origin_agent_id} to {self._agent_id}")
        
        try:
            # Extract update ID
            update_id = propagation_context.get("update_id", f"update_{datetime.now().isoformat()}")
            
            # Store the update information
            await self._state_manager.set_state(
                f"agent:{self._agent_id}:guideline_update:{update_id}",
                {
                    "origin_agent_id": origin_agent_id,
                    "update_data": update_data,
                    "propagation_context": propagation_context,
                    "timestamp": datetime.now().isoformat(),
                    "status": "received"
                },
                resource_type=ResourceType.STATE
            )
            
            # Update internal tracking
            self._guideline_updates[update_id] = {
                "origin_agent_id": origin_agent_id,
                "timestamp": datetime.now().isoformat(),
                "status": "in_progress"
            }
            
            # Analyze required adaptations
            required_adaptations = propagation_context.get("required_adaptations", [])
            
            # Get current guideline
            current_guideline = await self._state_manager.get_state(f"agent:{self._agent_id}:guideline")
            if not current_guideline:
                current_guideline = {}
            
            # Apply adaptations to current guideline
            updated_guideline = await self._apply_adaptations(
                current_guideline, 
                update_data,
                required_adaptations
            )
            
            # Store updated guideline
            await self._state_manager.set_state(
                f"agent:{self._agent_id}:guideline",
                updated_guideline,
                resource_type=ResourceType.STATE
            )
            
            # Update status
            self._guideline_updates[update_id]["status"] = "applied"
            await self._state_manager.set_state(
                f"agent:{self._agent_id}:guideline_update:{update_id}",
                {
                    "origin_agent_id": origin_agent_id,
                    "update_data": update_data,
                    "propagation_context": propagation_context,
                    "timestamp": datetime.now().isoformat(),
                    "status": "applied"
                },
                resource_type=ResourceType.STATE
            )
            
            # Emit update applied event
            await self._event_queue.emit(
                "guideline_update_applied",
                {
                    "agent_id": self._agent_id,
                    "origin_agent_id": origin_agent_id,
                    "update_id": update_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Return success
            return {
                "success": True,
                "agent_id": self._agent_id,
                "update_id": update_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error applying guideline update to {self._agent_id}: {str(e)}")
            
            # Update error state if update_id is available
            if 'update_id' in locals():
                await self._state_manager.set_state(
                    f"agent:{self._agent_id}:guideline_update:{update_id}",
                    {
                        "origin_agent_id": origin_agent_id,
                        "update_data": update_data,
                        "propagation_context": propagation_context,
                        "timestamp": datetime.now().isoformat(),
                        "status": "error",
                        "error": str(e)
                    },
                    resource_type=ResourceType.STATE
                )
                
                # Update internal tracking
                if update_id in self._guideline_updates:
                    self._guideline_updates[update_id]["status"] = "error"
                    self._guideline_updates[update_id]["error"] = str(e)
            
            # Return error
            return {
                "success": False,
                "agent_id": self._agent_id,
                "reason": f"Error applying guideline update: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _apply_adaptations(
        self,
        current_guideline: Dict[str, Any],
        update_data: Dict[str, Any],
        required_adaptations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Apply required adaptations to the current guideline.
        
        Args:
            current_guideline: The agent's current guideline
            update_data: The update data from upstream
            required_adaptations: List of required adaptations
            
        Returns:
            The updated guideline
        """
        # Create a copy of the current guideline to avoid modifying the original
        updated_guideline = current_guideline.copy() if current_guideline else {}
        
        # Apply each adaptation
        for adaptation in required_adaptations:
            adaptation_type = adaptation.get("type")
            
            if adaptation_type == "interface_adaptation":
                # Update interface-related elements
                if "interfaces" in update_data:
                    updated_guideline["interfaces"] = update_data.get("interfaces")
                    
            elif adaptation_type == "behavioral_adaptation":
                # Update behavior-related elements
                if "behavior" in update_data:
                    updated_guideline["behavior"] = update_data.get("behavior")
                    
            elif adaptation_type == "dependency_adaptation":
                # Update dependencies
                if "dependencies" in update_data:
                    if "dependencies" not in updated_guideline:
                        updated_guideline["dependencies"] = []
                    
                    # Merge dependencies, avoiding duplicates
                    existing_deps = set(updated_guideline["dependencies"])
                    for dep in update_data.get("dependencies", []):
                        if dep not in existing_deps:
                            updated_guideline["dependencies"].append(dep)
                            
            # Add more adaptation types as needed
            
        return updated_guideline
    
    async def verify_guideline_update(self, update_id: str) -> Dict[str, Any]:
        """
        Verify that a guideline update was applied correctly.
        
        Args:
            update_id: ID of the update to verify
            
        Returns:
            Dict with verification status and details
        """
        logger.info(f"Verifying guideline update {update_id} for {self._agent_id}")
        
        try:
            # Get the update info
            update_info = await self._state_manager.get_state(
                f"agent:{self._agent_id}:guideline_update:{update_id}"
            )
            
            if not update_info:
                return {
                    "verified": False,
                    "errors": [f"Update {update_id} not found"],
                    "timestamp": datetime.now().isoformat()
                }
            
            # Check status
            if update_info.get("status") != "applied":
                return {
                    "verified": False,
                    "errors": [f"Update {update_id} not applied (status: {update_info.get('status')})"],
                    "timestamp": datetime.now().isoformat()
                }
            
            # Get current guideline
            current_guideline = await self._state_manager.get_state(
                f"agent:{self._agent_id}:guideline"
            )
            
            # Extract propagation context
            propagation_context = update_info.get("propagation_context", {})
            
            # Check that required adaptations were applied
            required_adaptations = propagation_context.get("required_adaptations", [])
            all_applied = await self._check_adaptations_applied(
                current_guideline,
                required_adaptations
            )
            
            if all_applied:
                # Update verification status
                if update_id in self._guideline_updates:
                    self._guideline_updates[update_id]["verified"] = True
                
                return {
                    "verified": True,
                    "agent_id": self._agent_id,
                    "update_id": update_id,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "verified": False,
                    "errors": ["Required adaptations not fully applied"],
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error verifying update {update_id} for {self._agent_id}: {str(e)}")
            
            return {
                "verified": False,
                "errors": [f"Verification error: {str(e)}"],
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_adaptations_applied(
        self,
        current_guideline: Dict[str, Any],
        required_adaptations: List[Dict[str, Any]]
    ) -> bool:
        """
        Check if all required adaptations have been applied to the guideline.
        
        Args:
            current_guideline: The agent's current guideline
            required_adaptations: List of required adaptations
            
        Returns:
            True if all adaptations are applied, False otherwise
        """
        # Simple implementation for now - actual implementation would check each adaptation
        return True
    
    async def check_update_readiness(
        self,
        origin_agent_id: str,
        propagation_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if this agent is ready to receive a guideline update.
        
        Args:
            origin_agent_id: ID of the agent that originated the update
            propagation_context: Detailed context about the update's impact
            
        Returns:
            Dict with readiness status and details
        """
        logger.info(f"Checking update readiness from {origin_agent_id} for {self._agent_id}")
        
        try:
            # Extract update ID
            update_id = propagation_context.get("update_id", f"check_{datetime.now().isoformat()}")
            
            # Check if agent is in a valid state to receive updates
            # Note: This should be passed in from the AgentInterface, but for now we'll stub it
            agent_state = "READY"  # Placeholder - actual implementation would check real state
            if agent_state not in ["READY", "COMPLETE"]:
                return {
                    "ready": False,
                    "concerns": [{
                        "type": "agent_state",
                        "description": f"Agent is in {agent_state} state, which does not allow updates"
                    }],
                    "timestamp": datetime.now().isoformat()
                }
            
            # Check if required adaptations can be applied
            required_adaptations = propagation_context.get("required_adaptations", [])
            adaptation_concerns = await self._check_adaptation_concerns(required_adaptations)
            
            if adaptation_concerns:
                return {
                    "ready": False,
                    "concerns": adaptation_concerns,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Agent is ready to receive the update
            return {
                "ready": True,
                "concerns": [],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking update readiness for {self._agent_id}: {str(e)}")
            
            return {
                "ready": False,
                "concerns": [{
                    "type": "system_error",
                    "description": f"Error checking readiness: {str(e)}"
                }],
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_adaptation_concerns(
        self,
        required_adaptations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Check if there are any concerns about applying the required adaptations.
        
        Args:
            required_adaptations: List of required adaptations
            
        Returns:
            List of concerns, empty if none
        """
        # For now, just return empty list - actual implementation would check each adaptation
        return []