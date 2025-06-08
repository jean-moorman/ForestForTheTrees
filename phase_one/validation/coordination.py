"""
Sequential Agent Coordination module for Phase One.

This module provides a coordinator for sequential agent handoffs using the Water Agent
to detect and resolve misunderstandings between agents in a sequence.
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from unittest.mock import MagicMock

from resources import EventQueue, StateManager, ResourceType
from interfaces.agent.interface import AgentInterface

# Setup logging before using it
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lazy import to avoid circular dependency issues
_WaterAgentCoordinator = None

def get_water_agent_coordinator():
    """Lazy loader for WaterAgentCoordinator to avoid circular imports."""
    global _WaterAgentCoordinator
    if _WaterAgentCoordinator is None:
        try:
            from resources.water_agent.coordinator import WaterAgentCoordinator
            _WaterAgentCoordinator = WaterAgentCoordinator
        except ImportError as e:
            logger.warning(f"Using fallback WaterAgentCoordinator due to import failure: {e}")
            # Mock WaterAgentCoordinator for testing if the real one is not available
            class MockWaterAgentCoordinator:
                """Mock WaterAgentCoordinator for testing"""
                def __init__(self, resource_id="water_agent_coordinator", state_manager=None, event_bus=None, agent_interface=None):
                    self.resource_id = resource_id
                    self.state_manager = state_manager
                    self.event_bus = event_bus
                    self.agent_interface = agent_interface
                    
                    # Mock the required attributes
                    self.misunderstanding_detector = MagicMock()
                    self.resolution_tracker = MagicMock()
                    self.response_handler = MagicMock()
                    self.context_manager = MagicMock()
                    
                async def coordinate_agents(self, *args, **kwargs):
                    return "Updated first output", "Updated second output", {
                        "status": "completed",
                        "coordination_id": "test_coordination_id"
                    }
            _WaterAgentCoordinator = MockWaterAgentCoordinator
    return _WaterAgentCoordinator

class SequentialAgentCoordinator:
    """
    Coordinates sequential agent interactions using the Water Agent.
    
    This class manages the handoff between sequential agents, using the Water Agent
    to detect and resolve misunderstandings before proceeding to the next agent.
    """
    
    def __init__(
        self,
        event_queue: EventQueue,
        state_manager: StateManager,
        max_coordination_attempts: int = 2,
        coordination_timeout: float = 120.0
    ):
        """
        Initialize the sequential agent coordinator.
        
        Args:
            event_queue: Event queue for publishing/subscribing to events
            state_manager: State manager for persistent state
            max_coordination_attempts: Maximum number of coordination attempts
            coordination_timeout: Timeout for coordination process in seconds
        """
        self.event_queue = event_queue
        self.state_manager = state_manager
        self.max_coordination_attempts = max_coordination_attempts
        self.coordination_timeout = coordination_timeout
        
        # Create Water Agent coordinator using lazy loader
        WaterAgentCoordinatorClass = get_water_agent_coordinator()
        self.water_coordinator = WaterAgentCoordinatorClass(
            resource_id="water_agent_coordinator",
            state_manager=state_manager,
            event_bus=event_queue
        )
        
        # Tracking for coordination attempts
        self.current_attempt = 0
        self.coordination_history = []
        
    async def coordinate_agent_handoff(
        self,
        first_agent: AgentInterface,
        first_agent_output: Dict[str, Any],
        second_agent: AgentInterface,
        operation_id: Optional[str] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Coordinate the handoff between two sequential agents.
        
        This method manages the coordination process between two sequential agents
        using the Water Agent to detect and resolve misunderstandings.
        
        Args:
            first_agent: The first agent in the sequence
            first_agent_output: Output from the first agent
            second_agent: The second agent that will receive the output
            operation_id: Optional identifier for this coordination
            
        Returns:
            Tuple containing:
            - Updated first agent output after coordination
            - Coordination metadata
        """
        # Reset coordination tracking
        self.current_attempt = 0
        self.coordination_history = []
        
        # Generate operation ID if not provided
        if not operation_id:
            operation_id = f"phase_one_coordination_{datetime.now().isoformat()}"
            
        # Convert the first agent output to string if it's a dict
        first_agent_output_str = str(first_agent_output)
        
        # Placeholder for second agent output (not yet generated)
        # We'll use a mock output initially to give the Water Agent something to analyze
        mock_second_agent_output = (
            f"This is a placeholder for {second_agent.agent_id}'s output. "
            f"The agent will respond to the following input: "
            f"{first_agent_output_str[:200]}..."
        )
        
        # Initialize coordination tracking in state
        await self.state_manager.set_state(
            f"sequential_coordination:{operation_id}",
            {
                "status": "in_progress",
                "current_attempt": 0,
                "start_time": datetime.now().isoformat(),
                "first_agent": first_agent.agent_id,
                "second_agent": second_agent.agent_id
            },
            resource_type=ResourceType.STATE
        )
        
        # Emit coordination start event
        await self.event_queue.emit(
            "sequential_coordination_started",
            {
                "operation_id": operation_id,
                "first_agent": first_agent.agent_id,
                "second_agent": second_agent.agent_id,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        logger.info(f"Starting sequential coordination between {first_agent.agent_id} and {second_agent.agent_id}")
        
        # Process coordination with timeout
        try:
            # First, have the Water Agent analyze the first agent's output for potential issues
            updated_first_output, _, coordination_context = await asyncio.wait_for(
                self.water_coordinator.coordinate_agents(
                    first_agent,
                    first_agent_output_str,
                    second_agent,
                    mock_second_agent_output,
                    {"operation_id": operation_id, "mode": "preventive"}
                ), 
                timeout=self.coordination_timeout
            )
            
            # Check if any misunderstandings were detected and resolved
            misunderstandings = coordination_context.get("misunderstandings", [])
            if not misunderstandings:
                logger.info(f"No potential misunderstandings detected during preventive coordination")
                
                # Update coordination state
                await self.state_manager.set_state(
                    f"sequential_coordination:{operation_id}",
                    {
                        "status": "completed",
                        "result": "no_misunderstandings",
                        "end_time": datetime.now().isoformat()
                    },
                    resource_type=ResourceType.STATE
                )
                
                # Emit coordination complete event
                await self.event_queue.emit(
                    "sequential_coordination_completed",
                    {
                        "operation_id": operation_id,
                        "result": "no_misunderstandings",
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                # Return the original (or slightly updated) output
                return first_agent_output, {"status": "completed", "result": "no_misunderstandings"}
            
            # Misunderstandings were detected, update first agent output if necessary
            if updated_first_output != first_agent_output_str:
                logger.info(f"Updated first agent output based on preventive coordination")
                
                # Try to convert the string output back to dict if the original was a dict
                if isinstance(first_agent_output, dict):
                    try:
                        import json
                        # If the updated output is a JSON string, parse it
                        if updated_first_output.strip().startswith('{') and updated_first_output.strip().endswith('}'):
                            updated_first_output_dict = json.loads(updated_first_output)
                        else:
                            # Otherwise, keep the original structure but update the content
                            # This is a simplified approach - in a real implementation, you would
                            # use a more sophisticated method to update specific parts of the dict
                            updated_first_output_dict = first_agent_output.copy()
                            # Update the main content field if it exists
                            for key in ["content", "output", "result", "response"]:
                                if key in updated_first_output_dict:
                                    updated_first_output_dict[key] = updated_first_output
                                    break
                    except Exception as e:
                        logger.warning(f"Failed to parse updated output as dict: {str(e)}")
                        # Fallback: create a new dict with the updated output
                        updated_first_output_dict = {
                            "content": updated_first_output,
                            "coordination_applied": True,
                            "timestamp": datetime.now().isoformat()
                        }
                else:
                    # If the original was not a dict, keep the updated string
                    updated_first_output_dict = updated_first_output
                
                # Update first agent output
                first_agent_output = updated_first_output_dict
            
            # Update coordination history and state
            self.coordination_history.append({
                "attempt": 1,
                "timestamp": datetime.now().isoformat(),
                "misunderstandings_count": len(misunderstandings),
                "updated_output": updated_first_output != first_agent_output_str
            })
            
            await self.state_manager.set_state(
                f"sequential_coordination:{operation_id}:attempt:1",
                {
                    "misunderstandings": misunderstandings,
                    "updated_output": updated_first_output != first_agent_output_str,
                    "timestamp": datetime.now().isoformat()
                },
                resource_type=ResourceType.STATE
            )
            
            # Final coordination state update
            await self.state_manager.set_state(
                f"sequential_coordination:{operation_id}",
                {
                    "status": "completed",
                    "result": "coordination_applied",
                    "misunderstandings_count": len(misunderstandings),
                    "end_time": datetime.now().isoformat()
                },
                resource_type=ResourceType.STATE
            )
            
            # Emit coordination complete event
            await self.event_queue.emit(
                "sequential_coordination_completed",
                {
                    "operation_id": operation_id,
                    "result": "coordination_applied",
                    "misunderstandings_count": len(misunderstandings),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Return the updated output and coordination metadata
            return first_agent_output, {
                "status": "completed", 
                "result": "coordination_applied",
                "misunderstandings_count": len(misunderstandings),
                "coordination_id": coordination_context.get("coordination_id", "unknown"),
                "context": coordination_context
            }
            
        except asyncio.TimeoutError:
            logger.error(f"Coordination timeout exceeded for operation {operation_id}")
            
            # Update coordination state
            await self.state_manager.set_state(
                f"sequential_coordination:{operation_id}",
                {
                    "status": "timeout",
                    "current_attempt": self.current_attempt,
                    "end_time": datetime.now().isoformat(),
                    "error": "Coordination timeout exceeded"
                },
                resource_type=ResourceType.STATE
            )
            
            # Emit coordination timeout event
            await self.event_queue.emit(
                "sequential_coordination_timeout",
                {
                    "operation_id": operation_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Return the original output with timeout status
            return first_agent_output, {"status": "timeout", "error": "Coordination timeout exceeded"}
            
        except Exception as e:
            logger.error(f"Coordination error for operation {operation_id}: {str(e)}")
            
            # Update coordination state
            await self.state_manager.set_state(
                f"sequential_coordination:{operation_id}",
                {
                    "status": "error",
                    "current_attempt": self.current_attempt,
                    "end_time": datetime.now().isoformat(),
                    "error": str(e)
                },
                resource_type=ResourceType.STATE
            )
            
            # Emit coordination error event
            await self.event_queue.emit(
                "sequential_coordination_error",
                {
                    "operation_id": operation_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Return the original output with error status
            return first_agent_output, {"status": "error", "error": str(e)}
    
    async def coordinate_interactive_handoff(
        self,
        first_agent: AgentInterface,
        first_agent_output: Dict[str, Any],
        second_agent: AgentInterface,
        second_agent_output: Dict[str, Any],
        operation_id: Optional[str] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """
        Coordinate the interactive handoff between two sequential agents after second agent has processed.
        
        This method manages the coordination process between two sequential agents after the second
        agent has already processed the output from the first agent, using the Water Agent to detect
        and resolve misunderstandings.
        
        Args:
            first_agent: The first agent in the sequence
            first_agent_output: Output from the first agent
            second_agent: The second agent that received the output
            second_agent_output: Output from the second agent
            operation_id: Optional identifier for this coordination
            
        Returns:
            Tuple containing:
            - Updated first agent output after coordination
            - Updated second agent output after coordination
            - Coordination metadata
        """
        # Reset coordination tracking
        self.current_attempt = 0
        self.coordination_history = []
        
        # Generate operation ID if not provided
        if not operation_id:
            operation_id = f"phase_one_interactive_coordination_{datetime.now().isoformat()}"
            
        # Convert outputs to strings if they're dicts
        first_agent_output_str = str(first_agent_output)
        second_agent_output_str = str(second_agent_output)
        
        # Initialize coordination tracking in state
        await self.state_manager.set_state(
            f"interactive_coordination:{operation_id}",
            {
                "status": "in_progress",
                "current_attempt": 0,
                "start_time": datetime.now().isoformat(),
                "first_agent": first_agent.agent_id,
                "second_agent": second_agent.agent_id
            },
            resource_type=ResourceType.STATE
        )
        
        # Emit coordination start event
        await self.event_queue.emit(
            "interactive_coordination_started",
            {
                "operation_id": operation_id,
                "first_agent": first_agent.agent_id,
                "second_agent": second_agent.agent_id,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        logger.info(f"Starting interactive coordination between {first_agent.agent_id} and {second_agent.agent_id}")
        
        # Process coordination with timeout
        try:
            # Run the interactive coordination process
            updated_first_output, updated_second_output, coordination_context = await asyncio.wait_for(
                self.water_coordinator.coordinate_agents(
                    first_agent,
                    first_agent_output_str,
                    second_agent,
                    second_agent_output_str,
                    {"operation_id": operation_id, "mode": "interactive"}
                ),
                timeout=self.coordination_timeout
            )
            
            # Check if any misunderstandings were detected and resolved
            misunderstandings = coordination_context.get("misunderstandings", [])
            if not misunderstandings:
                logger.info(f"No misunderstandings detected during interactive coordination")
                
                # Update coordination state
                await self.state_manager.set_state(
                    f"interactive_coordination:{operation_id}",
                    {
                        "status": "completed",
                        "result": "no_misunderstandings",
                        "end_time": datetime.now().isoformat()
                    },
                    resource_type=ResourceType.STATE
                )
                
                # Emit coordination complete event
                await self.event_queue.emit(
                    "interactive_coordination_completed",
                    {
                        "operation_id": operation_id,
                        "result": "no_misunderstandings",
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                # Return the original outputs
                return first_agent_output, second_agent_output, {
                    "status": "completed", 
                    "result": "no_misunderstandings"
                }
            
            # Misunderstandings were detected and potentially resolved
            
            # Convert updated outputs back to dicts if the originals were dicts
            if isinstance(first_agent_output, dict) and updated_first_output != first_agent_output_str:
                try:
                    import json
                    # If the updated output is a JSON string, parse it
                    if updated_first_output.strip().startswith('{') and updated_first_output.strip().endswith('}'):
                        updated_first_output_dict = json.loads(updated_first_output)
                    else:
                        # Otherwise, keep the original structure but update the content
                        updated_first_output_dict = first_agent_output.copy()
                        # Update the main content field if it exists
                        for key in ["content", "output", "result", "response"]:
                            if key in updated_first_output_dict:
                                updated_first_output_dict[key] = updated_first_output
                                break
                except Exception as e:
                    logger.warning(f"Failed to parse updated first output as dict: {str(e)}")
                    # Fallback: create a new dict with the updated output
                    updated_first_output_dict = {
                        "content": updated_first_output,
                        "coordination_applied": True,
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                updated_first_output_dict = updated_first_output
                
            if isinstance(second_agent_output, dict) and updated_second_output != second_agent_output_str:
                try:
                    import json
                    # If the updated output is a JSON string, parse it
                    if updated_second_output.strip().startswith('{') and updated_second_output.strip().endswith('}'):
                        updated_second_output_dict = json.loads(updated_second_output)
                    else:
                        # Otherwise, keep the original structure but update the content
                        updated_second_output_dict = second_agent_output.copy()
                        # Update the main content field if it exists
                        for key in ["content", "output", "result", "response"]:
                            if key in updated_second_output_dict:
                                updated_second_output_dict[key] = updated_second_output
                                break
                except Exception as e:
                    logger.warning(f"Failed to parse updated second output as dict: {str(e)}")
                    # Fallback: create a new dict with the updated output
                    updated_second_output_dict = {
                        "content": updated_second_output,
                        "coordination_applied": True,
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                updated_second_output_dict = updated_second_output
            
            # Update coordination history and state
            self.coordination_history.append({
                "attempt": 1,
                "timestamp": datetime.now().isoformat(),
                "misunderstandings_count": len(misunderstandings),
                "first_output_updated": updated_first_output != first_agent_output_str,
                "second_output_updated": updated_second_output != second_agent_output_str
            })
            
            await self.state_manager.set_state(
                f"interactive_coordination:{operation_id}:attempt:1",
                {
                    "misunderstandings": misunderstandings,
                    "first_output_updated": updated_first_output != first_agent_output_str,
                    "second_output_updated": updated_second_output != second_agent_output_str,
                    "timestamp": datetime.now().isoformat()
                },
                resource_type=ResourceType.STATE
            )
            
            # Final coordination state update
            await self.state_manager.set_state(
                f"interactive_coordination:{operation_id}",
                {
                    "status": "completed",
                    "result": "coordination_applied",
                    "misunderstandings_count": len(misunderstandings),
                    "first_output_updated": updated_first_output != first_agent_output_str,
                    "second_output_updated": updated_second_output != second_agent_output_str,
                    "end_time": datetime.now().isoformat()
                },
                resource_type=ResourceType.STATE
            )
            
            # Emit coordination complete event
            await self.event_queue.emit(
                "interactive_coordination_completed",
                {
                    "operation_id": operation_id,
                    "result": "coordination_applied",
                    "misunderstandings_count": len(misunderstandings),
                    "first_output_updated": updated_first_output != first_agent_output_str,
                    "second_output_updated": updated_second_output != second_agent_output_str,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Return the updated outputs and coordination metadata
            return updated_first_output_dict, updated_second_output_dict, {
                "status": "completed", 
                "result": "coordination_applied",
                "misunderstandings_count": len(misunderstandings),
                "coordination_id": coordination_context.get("coordination_id", "unknown"),
                "context": coordination_context
            }
            
        except asyncio.TimeoutError:
            logger.error(f"Interactive coordination timeout exceeded for operation {operation_id}")
            
            # Update coordination state
            await self.state_manager.set_state(
                f"interactive_coordination:{operation_id}",
                {
                    "status": "timeout",
                    "current_attempt": self.current_attempt,
                    "end_time": datetime.now().isoformat(),
                    "error": "Coordination timeout exceeded"
                },
                resource_type=ResourceType.STATE
            )
            
            # Emit coordination timeout event
            await self.event_queue.emit(
                "interactive_coordination_timeout",
                {
                    "operation_id": operation_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Return the original outputs with timeout status
            return first_agent_output, second_agent_output, {
                "status": "timeout", 
                "error": "Coordination timeout exceeded"
            }
            
        except Exception as e:
            logger.error(f"Interactive coordination error for operation {operation_id}: {str(e)}")
            
            # Update coordination state
            await self.state_manager.set_state(
                f"interactive_coordination:{operation_id}",
                {
                    "status": "error",
                    "current_attempt": self.current_attempt,
                    "end_time": datetime.now().isoformat(),
                    "error": str(e)
                },
                resource_type=ResourceType.STATE
            )
            
            # Emit coordination error event
            await self.event_queue.emit(
                "interactive_coordination_error",
                {
                    "operation_id": operation_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Return the original outputs with error status
            return first_agent_output, second_agent_output, {
                "status": "error", 
                "error": str(e)
            }
            
    async def get_coordination_status(self, operation_id: str, interactive: bool = False) -> Dict[str, Any]:
        """
        Get current coordination status for an operation.
        
        Args:
            operation_id: Identifier for the coordination
            interactive: Whether this is an interactive coordination
            
        Returns:
            Coordination status information
        """
        # Get coordination state
        prefix = "interactive_coordination" if interactive else "sequential_coordination"
        coordination_state = await self.state_manager.get_state(
            f"{prefix}:{operation_id}",
            resource_type=ResourceType.STATE
        )
        
        # If no state found, return unknown status
        if not coordination_state:
            return {
                "status": "unknown",
                "operation_id": operation_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # Get coordination history
        history = []
        for attempt in range(1, coordination_state.get("current_attempt", 0) + 1):
            attempt_state = await self.state_manager.get_state(
                f"{prefix}:{operation_id}:attempt:{attempt}",
                resource_type=ResourceType.STATE
            )
            
            if attempt_state:
                history.append({
                    "attempt": attempt,
                    "timestamp": attempt_state.get("timestamp", ""),
                    "misunderstandings_count": len(attempt_state.get("misunderstandings", [])),
                    "first_output_updated": attempt_state.get("first_output_updated", False),
                    "second_output_updated": attempt_state.get("second_output_updated", False) if interactive else False
                })
        
        # Return comprehensive status
        return {
            "status": coordination_state.get("status", "unknown"),
            "result": coordination_state.get("result", "unknown"),
            "misunderstandings_count": coordination_state.get("misunderstandings_count", 0),
            "first_output_updated": coordination_state.get("first_output_updated", False),
            "second_output_updated": coordination_state.get("second_output_updated", False) if interactive else False,
            "start_time": coordination_state.get("start_time", ""),
            "end_time": coordination_state.get("end_time", ""),
            "error": coordination_state.get("error", None),
            "history": history,
            "operation_id": operation_id,
            "timestamp": datetime.now().isoformat()
        }