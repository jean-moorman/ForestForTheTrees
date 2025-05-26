"""
Agent interface implementation for the FFTT system.
"""

import asyncio
import logging
import random
import time
import weakref
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union

from resources import (
    EventQueue,
    StateManager,
    CacheManager,
    AgentContextManager,
    MetricsManager,
    ErrorHandler,
    MemoryMonitor,
    ResourceState,
    AgentContextType,
    CircuitBreakerConfig
)
from agent import Agent
from ..base import BaseInterface
from ..errors import ValidationError
from .validation import ValidationManager
from .cache import InterfaceCache
from .metrics import InterfaceMetrics
from .guideline import GuidelineManager
from .coordination import CoordinationInterface

# Import AgentState from __init__ without creating a circular import
from enum import Enum, auto
class AgentState(Enum):
    READY = auto()
    PROCESSING = auto()
    VALIDATING = auto()
    FAILED_VALIDATION = auto()
    COMPLETE = auto()
    ERROR = auto()
    COORDINATING = auto()
    CLARIFYING = auto()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Standard cache circuit breaker configuration
CACHE_CIRCUIT_CONFIG = CircuitBreakerConfig(
    failure_threshold=10,
    recovery_timeout=30,
    failure_window=30
)


class AgentInterface(BaseInterface):
    """
    Agent interface using modular resource managers.
    Provides functionality for agent communication, validation, and guideline management.
    """
    def __init__(
            self, 
            agent_id: str, 
            event_queue: EventQueue,
            state_manager: StateManager,
            context_manager: AgentContextManager,
            cache_manager: CacheManager,
            metrics_manager: MetricsManager,
            error_handler: ErrorHandler,
            memory_monitor: MemoryMonitor,
            model: str = "claude-3-7-sonnet-20250219"):
        """
        Initialize the agent interface.
        
        Args:
            agent_id: ID of the agent
            event_queue: Queue for event handling
            state_manager: Manager for state persistence
            context_manager: Manager for agent context
            cache_manager: Manager for caching
            metrics_manager: Manager for metrics collection
            error_handler: Handler for errors
            memory_monitor: Monitor for memory usage
            model: Model name for the agent
        """
        super().__init__(
            f"agent:{agent_id}", 
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor
        )
        self.agent_id = agent_id
        self.agent_state = AgentState.READY
        self.model = model
        
        # Create the agent
        self.agent = Agent(
            event_queue=event_queue,
            state_manager=self._state_manager,
            context_manager=self._context_manager,
            cache_manager=self._cache_manager,
            metrics_manager=self._metrics_manager,
            error_handler=self._error_handler,
            model=model
        )
        
        # Create validation manager
        self._validation_manager = ValidationManager(event_queue, self._state_manager, self._context_manager)
        self._validation_manager._validator.correction_handler = weakref.proxy(self.agent)
        
        # Create metrics manager
        self._metrics = InterfaceMetrics(event_queue, self._state_manager, self.interface_id)
        
        # Create cache manager
        self._cache = InterfaceCache(event_queue, self.interface_id, cache_manager, self._memory_monitor)
        
        # Create guideline manager
        self._guideline_manager = GuidelineManager(event_queue, self._state_manager, self.agent_id)
        
        # Create coordination interface
        self.coordination_interface = CoordinationInterface(self)
        
        # Configure validation settings
        self._max_validation_attempts = 3
    
    async def set_agent_state(self, new_state: AgentState, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Update agent state and synchronize with resource state with initialization safeguard and timeout protection.
        
        Args:
            new_state: New state to set
            metadata: Additional metadata
        """
        resource_states = {
            AgentState.PROCESSING: ResourceState.ACTIVE,
            AgentState.VALIDATING: ResourceState.PAUSED,
            AgentState.FAILED_VALIDATION: ResourceState.FAILED,
            AgentState.ERROR: ResourceState.TERMINATED,
            AgentState.COMPLETE: ResourceState.ACTIVE
        }
        logger.info(f"Setting agent state to {new_state}")
        
        try:
            # Add timeout wrapper to prevent hanging - using wait_for for Python 3.10 compatibility
            try:
                await asyncio.wait_for(self._set_agent_state_impl(new_state, resource_states, metadata), timeout=10.0)
            except asyncio.TimeoutError:
                logger.error(f"Overall timeout setting agent state to {new_state}")
                # Ensure internal state is at least set
                self.agent_state = new_state
                raise
        except Exception as e:
            logger.error(f"Error setting agent state to {new_state}: {str(e)}")
            # Still update internal state even if other operations fail
            self.agent_state = new_state
            raise
    
    async def _set_agent_state_impl(self, new_state: AgentState, resource_states: dict, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Internal implementation of agent state setting with detailed logging.
        
        Args:
            new_state: New state to set
            resource_states: Mapping of agent states to resource states
            metadata: Additional metadata
        """
        logger.debug(f"About to ensure initialized for {new_state}")
        
        # Ensure initialization before using lock
        await self.ensure_initialized()
        logger.debug(f"Initialization complete for {new_state}")
        
        # Update internal state first (this should never hang)
        self.agent_state = new_state
        logger.debug(f"Internal agent state updated to {new_state}")
        
        # Only update resource state if needed
        if new_state in resource_states:
            logger.debug(f"Attempting to set resource state to {resource_states[new_state]}")
            
            # Try state lock with shorter timeout
            try:
                await asyncio.wait_for(self._update_resource_state_with_lock(resource_states[new_state], metadata), timeout=5.0)
                logger.debug(f"Resource state set successfully")
            except asyncio.TimeoutError:
                logger.warning(f"State lock timeout for {new_state}, updating without resource sync")
                # Agent state is already set, continue without resource state sync
            except Exception as lock_error:
                logger.warning(f"State lock error for {new_state}: {str(lock_error)}, continuing without sync")
                # Agent state is already set, continue without resource state sync
        
        logger.info(f"Agent state successfully set to {new_state}")
        
    async def _update_resource_state_with_lock(self, resource_state: 'ResourceState', metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Update resource state with lock protection.
        
        Args:
            resource_state: Resource state to set
            metadata: Additional metadata
        """
        async with self._state_lock:
            logger.debug(f"Acquired state lock, setting resource state")
            await self.set_state(resource_state, metadata=metadata)
    
    # Guideline update methods (delegated to guideline manager)
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
        return await self._guideline_manager.apply_guideline_update(
            origin_agent_id,
            propagation_context,
            update_data
        )
    
    async def verify_guideline_update(self, update_id: str) -> Dict[str, Any]:
        """
        Verify that a guideline update was applied correctly.
        
        Args:
            update_id: ID of the update to verify
            
        Returns:
            Dict with verification status and details
        """
        return await self._guideline_manager.verify_guideline_update(update_id)
    
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
        # First update the guideline manager with the current agent state
        # Replace the stub implementation in the guideline manager
        propagation_context["agent_state"] = self.agent_state
        
        return await self._guideline_manager.check_update_readiness(
            origin_agent_id,
            propagation_context
        )
        
    async def process_with_validation(
            self,
            conversation: str,
            system_prompt_info: Tuple[str],
            schema: Dict[str, Any] = None,
            current_phase: Optional[str] = None,
            operation_id: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None,
            timeout: int = 30
        ) -> Dict[str, Any]:
        """
        Process with validation with improved error handling and metrics.
        
        Args:
            conversation: Conversation to process
            system_prompt_info: System prompt information
            schema: Schema for validation
            current_phase: Current phase of processing
            operation_id: ID of the operation
            metadata: Additional metadata
            timeout: Timeout in seconds
            
        Returns:
            Processing result
        """
        start_time = time.monotonic()
        request_id = operation_id or f"op_{int(time.time())}_{random.randint(1000, 9999)}"
        
        # Enhanced metadata
        if metadata is None:
            metadata = {}
        
        metadata.update({
            "request_id": request_id,
            "phase": current_phase,
            "start_time": datetime.now().isoformat()
        })
        
        # Create a dedicated task to allow for proper cancellation
        processing_task = None
        
        try:
            # Ensure interface is initialized
            if not self._initialized:
                await self.ensure_initialized()
            
            logger.info(f"Processing request {request_id} - Phase: {current_phase}")
            
            # Set processing state
            try:
                await self.set_agent_state(AgentState.PROCESSING, metadata=metadata)
                logger.info("=== AGENT STATE SET TO PROCESSING SUCCESSFULLY ===")
            except Exception as e:
                logger.error(f"Failed to set agent state to PROCESSING: {str(e)}")
                # Continue anyway - we'll try to process even if state setting failed
            
            # Create or get context
            logger.info(f"=== CREATING CONTEXT for {request_id} ===")
            context_key = f"agent_context:{request_id}"
            try:
                context = await self._context_manager.get_context(context_key)
                if not context:
                    logger.info(f"Creating new agent context for operation {request_id}")
                    context = await self._context_manager.create_context(
                        agent_id=f"agent:{self.interface_id}",
                        operation_id=request_id,
                        schema=schema,
                        context_type=AgentContextType.PERSISTENT,
                    )
                    logger.info(f"Created new agent context: {context}")
                logger.info("=== CONTEXT CREATION COMPLETE ===")
            except Exception as e:
                logger.error(f"Error creating/getting context for {request_id}: {str(e)}")
                # Continue anyway - we'll try to process even without proper context
            
            # Start processing timer
            logger.info("=== STARTING PROCESSING TIMER ===")
            try:
                await self._metrics_manager.record_metric(
                    f"agent:{self.interface_id}:processing_start",
                    1.0,
                    metadata=metadata
                )
            except Exception as e:
                logger.warning(f"Failed to record start metric: {str(e)}")
            
            processing_task = asyncio.create_task(
                self.agent.get_response(
                    conversation=conversation,
                    system_prompt_info=system_prompt_info,
                    schema=schema,
                    current_phase=current_phase,
                    operation_id=request_id
                )
            )
            
            # Wait for the response with timeout
            try:
                response = await asyncio.wait_for(processing_task, timeout=timeout)
                logger.info(f"Agent response received for {request_id}")
                
            except asyncio.TimeoutError:
                logger.error(f"Timeout waiting for agent.get_response for {request_id}")
                error_metadata = {**metadata, "error": "processing_timeout", "timeout": timeout}
                
                # Try to cancel the task if it's still running
                if processing_task and not processing_task.done():
                    processing_task.cancel()
                    try:
                        # Allow some time for cancellation to complete
                        await asyncio.wait_for(processing_task, timeout=1.0)
                    except (asyncio.TimeoutError, asyncio.CancelledError, Exception):
                        # Ignore errors during cancellation
                        pass
                        
                # Set error state and return error
                await self.set_agent_state(AgentState.ERROR, metadata=error_metadata)
                await self._metrics_manager.record_metric(
                    f"agent:{self.interface_id}:timeout",
                    1.0,
                    metadata=error_metadata
                )
                
                return {
                    "error": f"Processing timeout after {timeout} seconds",
                    "request_id": request_id,
                    "status": "error"
                }
                
            except Exception as e:
                logger.error(f"Error in agent.get_response for {request_id}: {str(e)}", exc_info=True)
                error_metadata = {**metadata, "error": str(e)}
                
                try:
                    await self.set_agent_state(AgentState.ERROR, metadata=error_metadata)
                except Exception as inner_e:
                    logger.error(f"Failed to set error state: {str(inner_e)}")
                    
                try:
                    await self._metrics_manager.record_metric(
                        f"agent:{self.interface_id}:processing_error",
                        1.0,
                        metadata=error_metadata
                    )
                except Exception as inner_e:
                    logger.warning(f"Failed to record error metric: {str(inner_e)}")
                    
                return {
                    "error": f"Processing error: {str(e)}",
                    "request_id": request_id,
                    "status": "error"
                }
                
            # Record processing duration
            processing_time = time.monotonic() - start_time
            try:
                await self._metrics_manager.record_metric(
                    f"agent:{self.interface_id}:processing_duration",
                    processing_time,
                    metadata={**metadata, "duration_seconds": processing_time}
                )
            except Exception as e:
                logger.warning(f"Failed to record duration metric: {str(e)}")
            
            # Handle errors in response
            if isinstance(response, dict) and "error" in response:
                logger.error(f"Error in response for {request_id}: {response['error']}")
                try:
                    await self.set_agent_state(AgentState.ERROR, metadata={
                        **metadata,
                        "error": response["error"]
                    })
                except Exception as e:
                    logger.error(f"Failed to set agent state to ERROR: {str(e)}")
                    
                try:
                    await self._metrics_manager.record_metric(
                        f"agent:{self.interface_id}:response_error",
                        1.0,
                        metadata={**metadata, "error": response["error"]}
                    )
                except Exception as e:
                    logger.warning(f"Failed to record error metric: {str(e)}")
                    
                # Ensure request_id is in the response
                if isinstance(response, dict):
                    response["request_id"] = request_id
                    
                return response
            
            # Set complete state for successful processing
            try:
                await self.set_agent_state(AgentState.COMPLETE, metadata=metadata)
            except Exception as e:
                logger.error(f"Failed to set agent state to COMPLETE: {str(e)}")
                
            try:
                await self._metrics_manager.record_metric(
                    f"agent:{self.interface_id}:processing_success",
                    1.0,
                    metadata={**metadata, "duration_seconds": processing_time}
                )
            except Exception as e:
                logger.warning(f"Failed to record success metric: {str(e)}")
                
            # Add request_id to response
            if isinstance(response, dict):
                response["request_id"] = request_id
                
            return response
                
        except Exception as e:
            logger.error(f"Unhandled error in process_with_validation for {request_id}: {str(e)}", exc_info=True)
            try:
                await self.set_agent_state(AgentState.ERROR, metadata={
                    **metadata,
                    "error": str(e)
                })
            except Exception as inner_e:
                logger.error(f"Failed to set agent state to ERROR: {str(inner_e)}")
                
            try:
                await self._metrics_manager.record_metric(
                    f"agent:{self.interface_id}:processing_exception",
                    1.0,
                    metadata={**metadata, "error": str(e)}
                )
            except Exception as inner_e:
                logger.warning(f"Failed to record exception metric: {str(inner_e)}")
                
            return {
                "error": f"Processing exception: {str(e)}",
                "request_id": request_id,
                "status": "error"
            }
            
    async def clarify(self, question: str) -> str:
        """
        Respond to a clarification question from the Water Agent.
        
        This method is called during the coordination process when the Water Agent
        detects potential misunderstandings and needs clarification from the agent.
        
        Args:
            question: The clarification question from the Water Agent
            
        Returns:
            The agent's response to the clarification question
        """
        logger.info(f"Agent {self.agent_id} received clarification request")
        
        # Set clarifying state
        previous_state = self.agent_state
        try:
            await self.set_agent_state(AgentState.CLARIFYING, metadata={
                "question": question[:100] + "..." if len(question) > 100 else question
            })
        except Exception as e:
            logger.error(f"Failed to set agent state to CLARIFYING: {str(e)}")
            
        try:
            # Delegate to the coordination interface
            response = await self.coordination_interface.clarify(question)
            
            # Restore previous state
            try:
                await self.set_agent_state(previous_state)
            except Exception as e:
                logger.error(f"Failed to restore previous agent state: {str(e)}")
                
            return response
            
        except Exception as e:
            logger.error(f"Error in clarification: {str(e)}")
            
            # Restore previous state
            try:
                await self.set_agent_state(previous_state)
            except Exception as inner_e:
                logger.error(f"Failed to restore previous agent state: {str(inner_e)}")
                
            return f"Error providing clarification: {str(e)}"
            
    async def coordinate_with_next_agent(
        self, 
        next_agent: Any,
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
        logger.info(f"Agent {self.agent_id} initiating coordination with {next_agent.agent_id}")
        
        # Set coordinating state
        previous_state = self.agent_state
        try:
            await self.set_agent_state(AgentState.COORDINATING, metadata={
                "next_agent": str(next_agent.agent_id)
            })
        except Exception as e:
            logger.error(f"Failed to set agent state to COORDINATING: {str(e)}")
            
        try:
            # Delegate to the coordination interface
            result = await self.coordination_interface.coordinate_with_next_agent(
                next_agent,
                my_output,
                next_agent_output,
                coordination_params
            )
            
            # Restore previous state
            try:
                await self.set_agent_state(previous_state)
            except Exception as e:
                logger.error(f"Failed to restore previous agent state: {str(e)}")
                
            return result
            
        except Exception as e:
            logger.error(f"Error in coordination: {str(e)}")
            
            # Restore previous state
            try:
                await self.set_agent_state(previous_state)
            except Exception as inner_e:
                logger.error(f"Failed to restore previous agent state: {str(inner_e)}")
                
            # Return original outputs with error context
            return my_output, next_agent_output, {"error": str(e), "status": "failed"}