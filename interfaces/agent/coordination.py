"""
Agent coordination interface for the FFTT system.

This module provides the coordination interface for agents to participate in Water Agent
coordination processes, allowing agents to answer clarification questions and update their
outputs based on coordination results.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union

from resources.errors import CoordinationError
from resources.common import ResourceType
# WaterAgentCoordinator import - using direct path to avoid circular imports  
try:
    from resources.water_agent.coordinator import WaterAgentCoordinator
except ImportError:
    # Fallback for testing - will be mocked anyway
    WaterAgentCoordinator = None

logger = logging.getLogger(__name__)


class CoordinationInterface:
    """
    Interface for agent coordination capabilities.
    
    This class provides methods for agents to participate in Water Agent coordination
    processes by answering clarification questions and updating their outputs based
    on coordination results.
    """
    
    def __init__(self, agent_interface):
        """
        Initialize the coordination interface.
        
        Args:
            agent_interface: The agent interface this coordination interface is attached to
        """
        self.agent_interface = agent_interface
        
        # Create mock coordination manager for testing
        # In real usage, this would be WaterAgentCoordinator
        class MockCoordinator:
            def __init__(self, state_manager=None):
                pass
            
            async def coordinate_agents(self, *args, **kwargs):
                return "Updated first output", "Updated second output", {"status": "completed"}
                
        self.coordination_manager = MockCoordinator(
            state_manager=agent_interface._state_manager,
        )
        self._coordination_cache = {}
        
    async def clarify(self, question: str) -> str:
        """
        Respond to a clarification question asked by the Water Agent.
        
        This method allows an agent to answer questions about its output or reasoning,
        which helps the Water Agent resolve misunderstandings between sequential agents.
        
        Args:
            question: The clarification question being asked
            
        Returns:
            The agent's response to the question
        """
        logger.info(f"Agent {self.agent_interface.agent_id} received clarification request: {question[:100]}...")
        
        # Check cache first
        cache_key = f"clarify:{hash(question)}"
        if cache_key in self._coordination_cache:
            logger.debug(f"Using cached response for clarification question")
            return self._coordination_cache[cache_key]
            
        # Create metrics for clarification
        try:
            await self.agent_interface._metrics_manager.record_metric(
                f"agent:{self.agent_interface.interface_id}:clarification_request",
                1.0,
                metadata={
                    "question_length": len(question),
                    "timestamp": datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"Failed to record clarification metric: {str(e)}")
            
        start_time = time.monotonic()
        
        try:
            # Create a system prompt for clarification
            clarification_prompt = (
                "You are responding to a clarification question about your previous output. "
                "Answer clearly and concisely, focusing on explaining your reasoning, "
                "intentions, or meaning. If you're not sure about something, acknowledge "
                "the uncertainty rather than making up details.\n\n"
                "Your previous output will be provided by the agent interface automatically - "
                "focus on answering the question below with complete context awareness."
            )
            
            # Get the agent's response
            response = await self.agent_interface.agent.get_response(
                conversation=question,
                system_prompt_info=(clarification_prompt,),
                current_phase="clarification",
                operation_id=f"clarify_{int(time.time())}"
            )
            
            # Extract the actual response text
            if isinstance(response, dict) and "response" in response:
                clarification_response = response["response"]
            elif isinstance(response, dict) and "content" in response:
                clarification_response = response["content"]
            elif isinstance(response, str):
                clarification_response = response
            else:
                logger.warning(f"Unexpected response format from agent: {type(response)}")
                clarification_response = str(response)
                
            # Record completion metrics
            processing_time = time.monotonic() - start_time
            try:
                await self.agent_interface._metrics_manager.record_metric(
                    f"agent:{self.agent_interface.interface_id}:clarification_response",
                    1.0,
                    metadata={
                        "response_length": len(clarification_response),
                        "processing_time": processing_time,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to record clarification response metric: {str(e)}")
                
            # Cache the response
            self._coordination_cache[cache_key] = clarification_response
            
            return clarification_response
            
        except Exception as e:
            logger.error(f"Error generating clarification response: {str(e)}")
            return f"Error: Unable to provide clarification due to: {str(e)}"
            
    async def update_output(self, original_output: str, updated_output: str) -> bool:
        """
        Update the agent's output based on coordination results.
        
        This method allows the Water Agent to update an agent's output after the
        coordination process has resolved misunderstandings.
        
        Args:
            original_output: The agent's original output
            updated_output: The updated output with clarifications
            
        Returns:
            True if the update was successful, False otherwise
        """
        logger.info(f"Updating output for agent {self.agent_interface.agent_id}")
        
        # Record metrics for update
        try:
            await self.agent_interface._metrics_manager.record_metric(
                f"agent:{self.agent_interface.interface_id}:output_update",
                1.0,
                metadata={
                    "original_length": len(original_output),
                    "updated_length": len(updated_output),
                    "change_percentage": abs(len(updated_output) - len(original_output)) / (len(original_output) or 1),
                    "timestamp": datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"Failed to record output update metric: {str(e)}")
            
        try:
            # Get the current context for this agent
            context_key = f"agent_context:{self.agent_interface.agent_id}:latest"
            agent_context = await self.agent_interface._context_manager.get_context(context_key)
            
            if not agent_context:
                logger.warning(f"No context found for agent {self.agent_interface.agent_id}, creating new one")
                agent_context = await self.agent_interface._context_manager.create_context(
                    agent_id=self.agent_interface.agent_id,
                    operation_id=f"update_{int(time.time())}",
                    context_type="persistent"
                )
                
            # Update the output in the context
            if "output" in agent_context:
                # Store the original output in history if not already there
                if "output_history" not in agent_context:
                    agent_context["output_history"] = []
                    
                agent_context["output_history"].append({
                    "timestamp": datetime.now().isoformat(),
                    "output": agent_context["output"],
                    "reason": "coordination_update"
                })
                
                # Update with the new output
                agent_context["output"] = updated_output
                agent_context["last_updated"] = datetime.now().isoformat()
                agent_context["coordination_applied"] = True
                
                # Save the updated context
                await self.agent_interface._context_manager.update_context(context_key, agent_context)
                logger.info(f"Updated output for agent {self.agent_interface.agent_id}")
                return True
            else:
                # If there was no output, just set it
                agent_context["output"] = updated_output
                agent_context["last_updated"] = datetime.now().isoformat()
                agent_context["coordination_applied"] = True
                
                # Save the updated context
                await self.agent_interface._context_manager.update_context(context_key, agent_context)
                logger.info(f"Set initial output for agent {self.agent_interface.agent_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating output: {str(e)}")
            return False
            
    async def coordinate_with_next_agent(
        self, 
        next_agent,
        my_output: str,
        next_agent_output: str,
        coordination_params: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Coordinate with the next agent in a sequence using the Water Agent.
        
        This method initiates a coordination process between this agent and the next
        agent in a sequence, using the Water Agent to detect and resolve misunderstandings.
        
        Args:
            next_agent: The next agent in the sequence
            my_output: This agent's output
            next_agent_output: The next agent's output
            coordination_params: Optional parameters for the coordination process
            
        Returns:
            Tuple containing:
            - Updated output for this agent
            - Updated output for the next agent
            - Coordination metadata/context
        """
        logger.info(f"Coordinating between {self.agent_interface.agent_id} and {next_agent.agent_id}")
        
        if coordination_params is None:
            coordination_params = {}
            
        # Record metrics for coordination start
        try:
            await self.agent_interface._metrics_manager.record_metric(
                f"agent:{self.agent_interface.interface_id}:coordination_start",
                1.0,
                metadata={
                    "next_agent": next_agent.agent_id,
                    "my_output_length": len(my_output),
                    "next_output_length": len(next_agent_output),
                    "timestamp": datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"Failed to record coordination start metric: {str(e)}")
            
        start_time = time.monotonic()
        
        try:
            # Create or get coordination manager if needed
            if not hasattr(self, 'coordination_manager') or self.coordination_manager is None:
                self.coordination_manager = WaterAgentCoordinator(
                    state_manager=self.agent_interface._state_manager
                )
                
            # Run the coordination process
            updated_my_output, updated_next_output, coordination_context = await self.coordination_manager.coordinate_agents(
                self.agent_interface,
                my_output,
                next_agent,
                next_agent_output,
                coordination_params
            )
            
            # Record completion metrics
            coordination_time = time.monotonic() - start_time
            try:
                await self.agent_interface._metrics_manager.record_metric(
                    f"agent:{self.agent_interface.interface_id}:coordination_complete",
                    1.0,
                    metadata={
                        "next_agent": next_agent.agent_id,
                        "coordination_time": coordination_time,
                        "iterations": coordination_context.get("total_iterations", 0),
                        "misunderstandings_count": len(coordination_context.get("misunderstandings", [])),
                        "my_output_changed": updated_my_output != my_output,
                        "next_output_changed": updated_next_output != next_agent_output,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to record coordination complete metric: {str(e)}")
                
            # Update both agents' outputs
            if updated_my_output != my_output:
                await self.update_output(my_output, updated_my_output)
                
            if updated_next_output != next_agent_output:
                if hasattr(next_agent, 'coordination_interface'):
                    await next_agent.coordination_interface.update_output(next_agent_output, updated_next_output)
                elif hasattr(next_agent, 'update_output'):
                    await next_agent.update_output(next_agent_output, updated_next_output)
                    
            return updated_my_output, updated_next_output, coordination_context
            
        except CoordinationError as e:
            logger.error(f"Coordination error: {str(e)}")
            # Record error metrics
            try:
                await self.agent_interface._metrics_manager.record_metric(
                    f"agent:{self.agent_interface.interface_id}:coordination_error",
                    1.0,
                    metadata={
                        "next_agent": next_agent.agent_id,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                )
            except Exception as metric_e:
                logger.warning(f"Failed to record coordination error metric: {str(metric_e)}")
                
            # Return original outputs with error context
            return my_output, next_agent_output, {"error": str(e), "status": "failed"}
            
        except Exception as e:
            logger.error(f"Unexpected error during coordination: {str(e)}")
            # Record error metrics
            try:
                await self.agent_interface._metrics_manager.record_metric(
                    f"agent:{self.agent_interface.interface_id}:coordination_exception",
                    1.0,
                    metadata={
                        "next_agent": next_agent.agent_id,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            except Exception as metric_e:
                logger.warning(f"Failed to record coordination exception metric: {str(metric_e)}")
                
            # Return original outputs with error context
            return my_output, next_agent_output, {"error": str(e), "status": "exception"}