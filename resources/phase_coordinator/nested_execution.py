"""
Forest For The Trees (FFTT) Phase Coordination System - Nested Execution
---------------------------------------------------
Manages execution of nested phases.
"""
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from resources.events import EventQueue, ResourceEventTypes
from resources.managers import MetricsManager
from resources.phase_coordinator.models import NestedPhaseExecution, PhaseContext
from resources.phase_coordinator.transition_handler import get_transition_handlers
from resources.monitoring import CircuitBreaker, CircuitOpenError

logger = logging.getLogger(__name__)

class NestedExecutionManager:
    """Manages nested phase executions"""
    
    def __init__(self, 
                event_queue: EventQueue,
                metrics_manager: MetricsManager):
        """
        Initialize the nested execution manager
        
        Args:
            event_queue: Event queue for sending events
            metrics_manager: Metrics manager for recording metrics
        """
        self._event_queue = event_queue
        self._metrics_manager = metrics_manager
        self._nested_executions: Dict[str, NestedPhaseExecution] = {}
    
    async def coordinate_nested_execution(self,
                                         parent_phase_id: str, 
                                         child_phase_id: str, 
                                         input_data: Dict[str, Any],
                                         transition_circuit_breaker: CircuitBreaker,
                                         phase_manager: Any,  # Forward reference
                                         handlers_map: Dict[str, List[Any]],
                                         phase_states: Dict[str, PhaseContext],
                                         timeout_seconds: Optional[int] = None,
                                         priority: str = "normal",
                                         execution_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Coordinate execution of a child phase from a parent phase with configurable execution parameters
        
        Args:
            parent_phase_id: Parent phase identifier
            child_phase_id: Child phase identifier
            input_data: Input data for the child phase
            transition_circuit_breaker: Circuit breaker for transitions
            phase_manager: Phase manager for starting phases
            handlers_map: Map of phase IDs to transition handlers
            phase_states: Dictionary of phase contexts
            timeout_seconds: Optional timeout in seconds for this execution (overrides default)
            priority: Execution priority ("high", "normal", "low")
            execution_metadata: Optional additional metadata for the execution
            
        Returns:
            Dict[str, Any]: Result of child phase execution
        """
        # Validate and normalize priority
        if priority not in ["high", "normal", "low"]:
            priority = "normal"
            logger.warning(f"Invalid priority '{priority}' specified, using 'normal'")
        
        # Use circuit breaker to protect the transition process
        try:
            return await transition_circuit_breaker.execute(
                lambda: self._coordinate_nested_execution_internal(
                    parent_phase_id, 
                    child_phase_id, 
                    input_data,
                    phase_manager,
                    handlers_map,
                    phase_states,
                    timeout_seconds,
                    priority,
                    execution_metadata
                )
            )
        except CircuitOpenError:
            logger.error(f"Transition circuit breaker open for {parent_phase_id} to {child_phase_id}")
            return {
                "error": f"Transition circuit breaker open",
                "status": "circuit_open",
                "parent_phase_id": parent_phase_id,
                "child_phase_id": child_phase_id
            }
    
    async def _coordinate_nested_execution_internal(self, 
                                                  parent_phase_id: str, 
                                                  child_phase_id: str, 
                                                  input_data: Dict[str, Any],
                                                  phase_manager: Any,
                                                  handlers_map: Dict[str, List[Any]],
                                                  phase_states: Dict[str, PhaseContext],
                                                  timeout_seconds: Optional[int] = None,
                                                  priority: str = "normal",
                                                  execution_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Internal implementation of nested execution coordination with enhanced execution tracking
        
        Args:
            parent_phase_id: Parent phase identifier
            child_phase_id: Child phase identifier
            input_data: Input data for the child phase
            phase_manager: Phase manager for starting phases
            handlers_map: Map of phase IDs to transition handlers
            phase_states: Dictionary of phase contexts
            timeout_seconds: Optional timeout in seconds (default based on phase type)
            priority: Execution priority ("high", "normal", "low")
            execution_metadata: Optional additional metadata for the execution
            
        Returns:
            Dict[str, Any]: Result of child phase execution
        """
        # Validate parent-child relationship
        parent_context = phase_states.get(parent_phase_id)
        if not parent_context:
            raise ValueError(f"Parent phase {parent_phase_id} not found")
        
        if child_phase_id not in parent_context.child_phases:
            raise ValueError(f"Phase {child_phase_id} is not a child of {parent_phase_id}")
        
        # Create execution context
        execution_id = f"{parent_phase_id}_to_{child_phase_id}_{int(time.time())}"
        
        # Determine timeout based on phase type
        if timeout_seconds is None:
            # Set default timeout based on phase type
            child_context = phase_states.get(child_phase_id)
            if child_context:
                phase_type = child_context.phase_type.value if hasattr(child_context.phase_type, 'value') else str(child_context.phase_type)
                # Different defaults based on phase complexity
                if phase_type == "phase_four":
                    timeout_seconds = 7200  # 2 hours for phase four (complex compilation)
                elif phase_type == "phase_three":
                    timeout_seconds = 5400  # 1.5 hours for phase three
                elif phase_type == "phase_two":
                    timeout_seconds = 3600  # 1 hour for phase two
                else:
                    timeout_seconds = 1800  # 30 minutes for other phases
            else:
                timeout_seconds = 3600  # 1 hour default if phase type unknown
        
        now = datetime.now()
        
        # Create nested execution record with enhanced tracking
        nested_execution = NestedPhaseExecution(
            parent_id=parent_phase_id,
            child_id=child_phase_id,
            execution_id=execution_id,
            start_time=now,
            timeout_seconds=timeout_seconds,
            priority=priority,
            last_activity=now,
            progress_updates={"initialization": {
                "timestamp": now.isoformat(),
                "status": "started"
            }}
        )
        
        # Add metadata if provided
        if execution_metadata:
            nested_execution.progress_updates["metadata"] = execution_metadata
            
        self._nested_executions[execution_id] = nested_execution
        
        # Get parent and child phase contexts
        child_context = phase_states.get(child_phase_id)
        
        if not parent_context:
            nested_execution.status = "failed"
            nested_execution.error = f"Parent phase {parent_phase_id} not found"
            nested_execution.end_time = datetime.now()
            nested_execution.progress_updates["validation_error"] = {
                "timestamp": datetime.now().isoformat(),
                "error": f"Parent phase {parent_phase_id} not found"
            }
            raise ValueError(f"Parent phase {parent_phase_id} not found")
            
        if not child_context:
            nested_execution.status = "failed"
            nested_execution.error = f"Child phase {child_phase_id} not found"
            nested_execution.end_time = datetime.now()
            nested_execution.progress_updates["validation_error"] = {
                "timestamp": datetime.now().isoformat(),
                "error": f"Child phase {child_phase_id} not found"
            }
            raise ValueError(f"Child phase {child_phase_id} not found")
        
        # Get phase type values for metrics
        parent_phase_type = parent_context.phase_type.value if hasattr(parent_context.phase_type, 'value') else str(parent_context.phase_type)
        child_phase_type = child_context.phase_type.value if hasattr(child_context.phase_type, 'value') else str(child_context.phase_type)
        
        # Record the nesting relationship with extended metadata
        await self._metrics_manager.record_metric(
            "phase_transition",
            1.0,
            metadata={
                "parent_phase": parent_phase_id,
                "child_phase": child_phase_id,
                "execution_id": execution_id,
                "priority": priority,
                "timeout_seconds": timeout_seconds
            }
        )
        
        # Prepare input data with parent context
        enhanced_input = {
            **input_data,
            "parent_context": {
                "phase_id": parent_phase_id,
                "phase_type": parent_phase_type,
                "execution_context": parent_context.config.get("execution_context", {})
            },
            "execution_id": execution_id,
            "timeout_seconds": timeout_seconds  # Pass timeout to child phase
        }
        
        # Update progress tracking
        nested_execution.last_activity = datetime.now()
        nested_execution.progress_updates["context_prepared"] = {
            "timestamp": datetime.now().isoformat(),
            "status": "in_progress"
        }
        
        # Record metric for enhanced context
        await self._metrics_manager.record_metric(
            f"phase_coordinator:nested_execution_start",
            1.0,
            metadata={
                "parent_phase_id": parent_phase_id,
                "parent_phase_type": parent_phase_type,
                "child_phase_id": child_phase_id,
                "child_phase_type": child_phase_type,
                "execution_id": execution_id,
                "priority": priority,
                "timeout_seconds": timeout_seconds,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Execute handlers for transition
        handlers = get_transition_handlers(handlers_map, parent_phase_id, child_phase_id)
        nested_execution.progress_updates["handlers"] = {
            "timestamp": datetime.now().isoformat(),
            "count": len(handlers),
            "status": "executing"
        }
        
        for i, handler in enumerate(handlers):
            nested_execution.last_activity = datetime.now()
            try:
                if hasattr(handler, 'before_start') and callable(handler.before_start):
                    enhanced_input = await handler.before_start(child_phase_id, enhanced_input)
                    nested_execution.progress_updates[f"handler_{i+1}"] = {
                        "timestamp": datetime.now().isoformat(),
                        "handler_type": handler.__class__.__name__,
                        "status": "completed"
                    }
            except Exception as e:
                logger.error(f"Error in transition handler for {parent_phase_id} to {child_phase_id}: {str(e)}")
                nested_execution.progress_updates[f"handler_{i+1}_error"] = {
                    "timestamp": datetime.now().isoformat(),
                    "handler_type": handler.__class__.__name__,
                    "error": str(e),
                    "status": "failed"
                }
        
        try:
            # Update progress before starting child phase
            nested_execution.last_activity = datetime.now()
            nested_execution.progress_updates["child_phase_starting"] = {
                "timestamp": datetime.now().isoformat(),
                "status": "starting"
            }
            
            # Start child phase with timeout tracking
            start_time = time.time()
            
            # Start child phase
            child_result = await phase_manager.start_phase(child_phase_id, enhanced_input)
            
            # Update progress after child phase completes
            execution_time = time.time() - start_time
            nested_execution.last_activity = datetime.now()
            nested_execution.progress_updates["child_phase_completed"] = {
                "timestamp": datetime.now().isoformat(),
                "execution_time_seconds": execution_time,
                "status": "completed"
            }
            
            # Execute post-completion handlers
            nested_execution.progress_updates["post_handlers"] = {
                "timestamp": datetime.now().isoformat(),
                "count": len(handlers),
                "status": "executing"
            }
            
            for i, handler in enumerate(reversed(handlers)):
                nested_execution.last_activity = datetime.now()
                try:
                    if hasattr(handler, 'after_completion') and callable(handler.after_completion):
                        child_result = await handler.after_completion(child_phase_id, child_result)
                        nested_execution.progress_updates[f"post_handler_{i+1}"] = {
                            "timestamp": datetime.now().isoformat(),
                            "handler_type": handler.__class__.__name__,
                            "status": "completed"
                        }
                except Exception as e:
                    logger.error(f"Error in completion handler for {child_phase_id}: {str(e)}")
                    nested_execution.progress_updates[f"post_handler_{i+1}_error"] = {
                        "timestamp": datetime.now().isoformat(),
                        "handler_type": handler.__class__.__name__,
                        "error": str(e),
                        "status": "failed"
                    }
            
            # Record completion in parent context
            parent_context.metrics[f"child_phase_{child_phase_id}"] = {
                "status": "completed",
                "execution_id": execution_id,
                "execution_time_seconds": execution_time,
                "timestamp": datetime.now().isoformat()
            }
            
            # Update nested execution record
            nested_execution.status = "completed"
            nested_execution.end_time = datetime.now()
            nested_execution.result = child_result
            nested_execution.progress_updates["completion"] = {
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "execution_time_seconds": execution_time
            }
            
            # Record metric for successful execution with detailed metadata
            await self._metrics_manager.record_metric(
                f"phase_coordinator:nested_execution_complete",
                1.0,
                metadata={
                    "parent_phase_id": parent_phase_id,
                    "child_phase_id": child_phase_id,
                    "execution_id": execution_id,
                    "execution_time": (nested_execution.end_time - nested_execution.start_time).total_seconds(),
                    "priority": priority,
                    "progress_steps_count": len(nested_execution.progress_updates),
                    "timestamp": nested_execution.end_time.isoformat()
                }
            )
            
            return child_result
            
        except Exception as e:
            # Update progress tracking with error
            nested_execution.last_activity = datetime.now()
            nested_execution.progress_updates["execution_error"] = {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "error_type": type(e).__name__,
                "status": "failed"
            }
            
            # Handle failures with recovery
            error_context = {
                "parent_phase": parent_phase_id,
                "child_phase": child_phase_id,
                "execution_id": execution_id,
                "input_data": enhanced_input,
                "error": str(e),
                "error_type": type(e).__name__,
                "progress_history": nested_execution.progress_updates
            }
            
            # Update nested execution record
            nested_execution.status = "failed"
            nested_execution.end_time = datetime.now()
            nested_execution.error = str(e)
            
            # Record metric for failed execution with detailed diagnostics
            await self._metrics_manager.record_metric(
                f"phase_coordinator:nested_execution_failed",
                1.0,
                metadata={
                    "parent_phase_id": parent_phase_id,
                    "child_phase_id": child_phase_id,
                    "execution_id": execution_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "execution_time": (nested_execution.end_time - nested_execution.start_time).total_seconds(),
                    "priority": priority,
                    "progress_steps_count": len(nested_execution.progress_updates),
                    "last_progress_step": list(nested_execution.progress_updates.keys())[-1],
                    "timestamp": nested_execution.end_time.isoformat()
                }
            )
            
            # Try recovery handlers with progress tracking
            nested_execution.progress_updates["recovery_attempt"] = {
                "timestamp": datetime.now().isoformat(),
                "status": "attempting"
            }
            
            recovery_result = None
            for i, handler in enumerate(handlers):
                nested_execution.last_activity = datetime.now()
                try:
                    if hasattr(handler, 'on_failure') and callable(handler.on_failure):
                        nested_execution.progress_updates[f"recovery_handler_{i+1}"] = {
                            "timestamp": datetime.now().isoformat(),
                            "handler_type": handler.__class__.__name__,
                            "status": "attempting"
                        }
                        
                        recovery_result = await handler.on_failure(child_phase_id, e, error_context)
                        
                        if recovery_result:
                            # Handler successfully recovered
                            nested_execution.progress_updates[f"recovery_handler_{i+1}"].update({
                                "timestamp": datetime.now().isoformat(),
                                "status": "succeeded",
                                "strategy": recovery_result.get("strategy", "unknown")
                            })
                            break
                        else:
                            nested_execution.progress_updates[f"recovery_handler_{i+1}"].update({
                                "timestamp": datetime.now().isoformat(),
                                "status": "no_recovery"
                            })
                except Exception as recovery_error:
                    # Log recovery failure but continue with other handlers
                    logger.error(f"Recovery handler for {child_phase_id} failed: {recovery_error}")
                    nested_execution.progress_updates[f"recovery_handler_{i+1}_error"] = {
                        "timestamp": datetime.now().isoformat(),
                        "handler_type": handler.__class__.__name__,
                        "error": str(recovery_error),
                        "status": "failed"
                    }
            
            if recovery_result:
                # Record recovery in metrics with enhanced diagnostics
                await self._metrics_manager.record_metric(
                    "phase_recovery",
                    1.0,
                    metadata={
                        "parent_phase": parent_phase_id,
                        "child_phase": child_phase_id,
                        "execution_id": execution_id,
                        "recovery_strategy": recovery_result.get("strategy", "unknown"),
                        "original_error": str(e),
                        "recovery_steps": len([k for k in nested_execution.progress_updates.keys() if k.startswith("recovery")]),
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                # Update nested execution record
                nested_execution.status = "recovered"
                nested_execution.result = recovery_result
                nested_execution.progress_updates["recovery_succeeded"] = {
                    "timestamp": datetime.now().isoformat(),
                    "strategy": recovery_result.get("strategy", "unknown"),
                    "status": "success"
                }
                
                return recovery_result
            
            # If no handler recovered, record the failure and propagate the error
            nested_execution.progress_updates["recovery_failed"] = {
                "timestamp": datetime.now().isoformat(),
                "status": "failed",
                "message": "All recovery handlers failed or no suitable handler found"
            }
            
            # Emit a final failure event with complete execution history
            await self._event_queue.emit(
                ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
                {
                    "resource_id": f"nested_execution:{execution_id}",
                    "error": str(e),
                    "error_type": "unrecoverable_execution_failure",
                    "parent_phase": parent_phase_id,
                    "child_phase": child_phase_id,
                    "execution_history": nested_execution.progress_updates,
                    "execution_time": (nested_execution.end_time - nested_execution.start_time).total_seconds(),
                    "timestamp": datetime.now().isoformat()
                },
                priority="high"
            )
            
            # Propagate the error
            raise
    
    def get_nested_execution(self, execution_id: str) -> Optional[NestedPhaseExecution]:
        """
        Get a nested execution by ID
        
        Args:
            execution_id: The execution ID
            
        Returns:
            Optional[NestedPhaseExecution]: The nested execution or None if not found
        """
        return self._nested_executions.get(execution_id)
    
    def get_nested_executions(self) -> Dict[str, NestedPhaseExecution]:
        """
        Get all nested executions
        
        Returns:
            Dict[str, NestedPhaseExecution]: Dictionary of all nested executions
        """
        return self._nested_executions