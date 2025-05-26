"""
Validation manager for agent outputs in the FFTT system.
"""

import asyncio
from datetime import datetime
import logging
from typing import Dict, Any, Optional, Tuple

from resources import (
    EventQueue,
    StateManager,
    AgentContextManager,
    ResourceType
)
from agent_validation import Validator
from ..errors import ValidationError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationManager:
    """
    Manages validation of agent outputs with error handling and timeout protection.
    """
    
    def __init__(self, event_queue: EventQueue, state_manager: StateManager, context_manager: AgentContextManager, correction_handler=None):
        """
        Initialize the validation manager.
        
        Args:
            event_queue: Queue for event handling
            state_manager: Manager for state persistence
            context_manager: Manager for agent context
            correction_handler: Optional handler for corrections
        """
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._context_manager = context_manager
        self._validator = Validator(self._event_queue, self._state_manager, correction_handler=correction_handler)
        self._active_validations: Dict[str, Dict[str, Any]] = {}
        
    async def validate_agent_output(self, interface_id: str,
                              output: Dict[str, Any],
                              schema: Dict[str, Any],
                              operation_id: str,
                              timeout: float = 30.0) -> Tuple[bool, Optional[Dict[str, Any]], Dict[str, Any]]:
        """
        Validate agent output with improved error handling and timeout protection.
        
        Args:
            interface_id: ID of the interface
            output: Output to validate
            schema: Schema to validate against
            operation_id: ID of the operation
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (success, validated_output, error_analysis)
            
        Raises:
            ValidationError: If validation fails with an error
        """
        from resources.events import ResourceEventTypes
        
        validation_id = f"validation:{interface_id}:{operation_id}"
        start_time = datetime.now()
        
        # Ensure schema parameter validation
        if not schema:
            logger.error(f"Missing schema for validation operation {validation_id}")
            await self._event_queue.emit(
                ResourceEventTypes.ERROR_OCCURRED.value,
                {
                    "validation_id": validation_id,
                    "error": "Missing schema for validation",
                    "error_type": "ValidationParameterError",
                    "timestamp": datetime.now().isoformat()
                }
            )
            raise ValueError(f"Schema is required for validation {validation_id}")
            
        # Validate output is a dictionary
        if not isinstance(output, dict):
            logger.error(f"Invalid output type for validation {validation_id}: {type(output)}")
            await self._event_queue.emit(
                ResourceEventTypes.ERROR_OCCURRED.value,
                {
                    "validation_id": validation_id,
                    "error": f"Invalid output type: {type(output)}",
                    "error_type": "ValidationParameterError",
                    "timestamp": datetime.now().isoformat()
                }
            )
            raise TypeError(f"Output must be a dictionary, got {type(output)}")
        
        try:
            # Use asyncio.wait_for to add timeout protection
            try:
                validation_task = self._validator.validate_output(output, schema)
                success, validated_output, error_analysis = await asyncio.wait_for(
                    validation_task, 
                    timeout=timeout
                )
                
                # Record validation duration for monitoring
                validation_duration = (datetime.now() - start_time).total_seconds()
                logger.debug(f"Validation {validation_id} completed in {validation_duration:.2f}s")
                
            except asyncio.TimeoutError:
                # Handle timeout gracefully
                logger.error(f"Validation {validation_id} timed out after {timeout}s")
                
                # Create error analysis for timeout
                error_analysis = {
                    "error_type": "timeout",
                    "message": f"Validation timed out after {timeout} seconds",
                    "timestamp": datetime.now().isoformat(),
                    "validation_id": validation_id
                }
                
                # Emit timeout error event
                await self._event_queue.emit(
                    ResourceEventTypes.ERROR_OCCURRED.value,
                    {
                        "validation_id": validation_id,
                        "error": f"Validation timed out after {timeout}s",
                        "error_type": "ValidationTimeoutError",
                        "schema": str(schema)[:100] + "..." if len(str(schema)) > 100 else str(schema),
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                # Return failure with error analysis
                return False, None, error_analysis
            
            # Log validation result
            if success:
                logger.info(f"Validation {validation_id} succeeded")
            else:
                logger.warning(f"Validation {validation_id} failed: {error_analysis.get('message', 'No error message')}")
            
            # Update validation state
            try:
                await self._state_manager.set_state(
                    validation_id,
                    {
                        "status": "complete" if success else "failed_validation",
                        "success": success,
                        "error_analysis": error_analysis,
                        "completion_time": datetime.now().isoformat(),
                        "duration_seconds": (datetime.now() - start_time).total_seconds()
                    },
                    resource_type=ResourceType.STATE
                )
            except Exception as state_err:
                logger.error(f"Failed to update validation state: {str(state_err)}")
            
            # Update context
            try:
                context = await self._context_manager.get_context(f"agent_context:{operation_id}")
                if context:
                    context.validation_attempts += 1
                    context.validation_history.append({
                        "timestamp": datetime.now().isoformat(),
                        "success": success,
                        "error_analysis": error_analysis,
                        "duration_seconds": (datetime.now() - start_time).total_seconds()
                    })
                    await self._context_manager.store_context(f"agent_context:{operation_id}", context)
            except Exception as ctx_err:
                logger.error(f"Failed to update validation context: {str(ctx_err)}")

            # Emit validation completed event with detailed info
            try:
                await self._event_queue.emit(
                    ResourceEventTypes.VALIDATION_COMPLETED.value,
                    {
                        "validation_id": validation_id,
                        "interface_id": interface_id,
                        "operation_id": operation_id,
                        "success": success,
                        "duration_seconds": (datetime.now() - start_time).total_seconds(),
                        "error_analysis": error_analysis if not success else None,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            except Exception as event_err:
                logger.error(f"Failed to emit validation completed event: {str(event_err)}")

            return success, validated_output, error_analysis
            
        except Exception as e:
            # Enhanced error handling with proper error events
            logger.error(f"Validation error for {validation_id}: {str(e)}")
            
            # Create detailed error information
            error_info = {
                "validation_id": validation_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": (datetime.now() - start_time).total_seconds(),
                "schema_provided": bool(schema)
            }
            
            # Emit both event types for compatibility during transition
            try:
                await self._event_queue.emit(
                    ResourceEventTypes.ERROR_OCCURRED.value,
                    error_info
                )
                
                await self._event_queue.emit(
                    ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
                    error_info
                )
            except Exception as event_err:
                logger.error(f"Failed to emit validation error event: {str(event_err)}")
                
            # Create error analysis for the exception
            error_analysis = {
                "error_type": "exception",
                "message": str(e),
                "exception_type": type(e).__name__,
                "timestamp": datetime.now().isoformat()
            }
            
            # Try to update the validation state even in error cases
            try:
                await self._state_manager.set_state(
                    validation_id,
                    {
                        "status": "failed_validation",
                        "success": False,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "error_analysis": error_analysis,
                        "completion_time": datetime.now().isoformat()
                    },
                    resource_type=ResourceType.STATE
                )
            except Exception:
                pass  # Ignore failures in error handling
                
            # Re-raise with more context
            raise ValidationError(f"Validation failed: {str(e)}") from e