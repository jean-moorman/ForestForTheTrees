"""
Refinement manager for handling the refinement lifecycle in Phase Two.

This module implements specialized functionality for managing the refinement process
for component guidelines, including context cleanup after backtracking, refinement
iteration tracking, system monitoring integration, and enhanced timeout handling.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from resources import (
    EventQueue, StateManager, MetricsManager, ResourceType, ResourceEventTypes
)
from resources.monitoring import MemoryMonitor, SystemMonitor, HealthStatus
from resources.base import AsyncTimeoutManager
from interface import AgentInterface
from phase_two.validation.validator import ComponentValidationState

logger = logging.getLogger(__name__)

@dataclass
class ComponentRefinementContext:
    """Context information for a component guideline refinement."""
    context_id: str
    component_id: str
    validation_state: ComponentValidationState
    responsible_agent: Optional[str]
    validation_errors: List[Dict[str, Any]]
    created_at: datetime
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "context_id": self.context_id,
            "component_id": self.component_id,
            "validation_state": self.validation_state.value,
            "responsible_agent": self.responsible_agent,
            "validation_errors": self.validation_errors,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }

@dataclass
class RefinementIteration:
    """Tracking information for a refinement iteration."""
    context_id: str
    iteration_number: int
    refinement_type: str
    timestamp: datetime
    success: bool
    duration_seconds: float
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "context_id": self.context_id,
            "iteration_number": self.iteration_number,
            "refinement_type": self.refinement_type,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "duration_seconds": self.duration_seconds,
            "metadata": self.metadata
        }

class ComponentRefinementManager:
    """
    Manages the refinement lifecycle for phase two component validation process.
    
    This class handles:
    1. Context cleanup after backtracking
    2. Refinement iteration progress tracking
    3. System monitoring integration
    4. Enhanced timeout handling
    """
    
    def __init__(
        self,
        event_queue: EventQueue,
        state_manager: StateManager,
        metrics_manager: MetricsManager,
        memory_monitor: Optional[MemoryMonitor] = None,
        system_monitor: Optional[SystemMonitor] = None,
        timeout_manager: Optional[AsyncTimeoutManager] = None
    ):
        self.event_queue = event_queue
        self.state_manager = state_manager
        self.metrics_manager = metrics_manager
        self.memory_monitor = memory_monitor
        self.system_monitor = system_monitor
        self.timeout_manager = timeout_manager or AsyncTimeoutManager()
        
        # Refinement tracking
        self._current_refinement: Optional[ComponentRefinementContext] = None
        self._refinement_lock = asyncio.Lock()
        self._refinement_iterations: Dict[str, List[RefinementIteration]] = {}
        
        # Default timeout values
        self.DEFAULT_REFINEMENT_TIMEOUT = 120.0  # 2 minutes
        self.DEFAULT_REFLECTION_TIMEOUT = 60.0   # 1 minute
        self.DEFAULT_REVISION_TIMEOUT = 90.0     # 1.5 minutes
        
    async def create_refinement_context(
        self,
        component_id: str,
        validation_state: ComponentValidationState,
        responsible_agent: Optional[str] = None,
        validation_errors: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ComponentRefinementContext:
        """
        Create a new refinement context.
        
        Args:
            component_id: Identifier for the component undergoing refinement
            validation_state: Current validation state
            responsible_agent: Agent responsible for refinement (if known)
            validation_errors: List of validation errors that triggered refinement
            metadata: Additional contextual metadata
            
        Returns:
            ComponentRefinementContext: The created refinement context
        """
        context_id = f"component_refinement:{component_id}:{datetime.now().isoformat()}"
        
        refinement_context = ComponentRefinementContext(
            context_id=context_id,
            component_id=component_id,
            validation_state=validation_state,
            responsible_agent=responsible_agent,
            validation_errors=validation_errors or [],
            created_at=datetime.now(),
            metadata=metadata or {}
        )
        
        # Store in state manager
        await self.state_manager.set_state(
            f"component_refinement_context:{context_id}",
            refinement_context.to_dict(),
            ResourceType.STATE
        )
        
        # Set as current refinement
        async with self._refinement_lock:
            self._current_refinement = refinement_context
            
        # Emit event using standardized event type and payload
        from resources.schemas import RefinementContextPayload
        from dataclasses import asdict
        
        # Create standardized payload
        payload = RefinementContextPayload(
            context_id=context_id,
            phase_id=f"component_{component_id}",
            validation_state=validation_state.value,
            responsible_agent=responsible_agent,
            error_count=len(validation_errors or []),
            state="created",
            source_id="component_refinement_manager",
            metadata={
                "refinement_type": "created"
            }
        )
        
        # Emit with standardized event type
        await self.event_queue.emit(
            ResourceEventTypes.COMPONENT_REFINEMENT_CREATED.value,
            asdict(payload)
        )
        
        # Track memory usage
        if self.memory_monitor:
            context_size_mb = len(str(refinement_context.to_dict())) / (1024 * 1024)
            await self.memory_monitor.track_resource(
                f"component_refinement_context:{context_id}",
                context_size_mb,
                f"component_refinement_context_{component_id}"
            )
            
        # Record metric
        await self.metrics_manager.record_metric(
            "component_guideline:refinement:context_created",
            1.0,
            metadata={
                "context_id": context_id,
                "component_id": component_id,
                "validation_state": validation_state.value,
                "error_count": len(validation_errors or []),
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return refinement_context
        
    async def track_refinement_iteration(
        self,
        context_id: str,
        iteration_number: int,
        refinement_type: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        success: bool,
        duration_seconds: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> RefinementIteration:
        """
        Track a refinement iteration.
        
        Args:
            context_id: Refinement context identifier
            iteration_number: Current iteration number
            refinement_type: Type of refinement (initial, reflection, revision)
            input_data: Input data for the refinement
            output_data: Output data from the refinement
            success: Whether the refinement was successful
            duration_seconds: Duration of the refinement in seconds
            metadata: Additional contextual metadata
            
        Returns:
            RefinementIteration: The created iteration tracking object
        """
        iteration = RefinementIteration(
            context_id=context_id,
            iteration_number=iteration_number,
            refinement_type=refinement_type,
            timestamp=datetime.now(),
            success=success,
            duration_seconds=duration_seconds,
            metadata=metadata or {}
        )
        
        # Store iteration in memory
        if context_id not in self._refinement_iterations:
            self._refinement_iterations[context_id] = []
            
        self._refinement_iterations[context_id].append(iteration)
        
        # Store in state manager for persistence
        await self.state_manager.set_state(
            f"component_refinement_iteration:{context_id}:{iteration_number}:{refinement_type}",
            iteration.to_dict(),
            ResourceType.METRIC
        )
        
        # Record metrics
        await self.metrics_manager.record_metric(
            f"component_guideline:refinement:{refinement_type}",
            duration_seconds,
            metadata={
                "context_id": context_id,
                "iteration": iteration_number,
                "success": success,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Emit event using standardized event type and payload
        from resources.schemas import RefinementIterationPayload
        from dataclasses import asdict
        
        # Create standardized payload
        payload = RefinementIterationPayload(
            context_id=context_id,
            iteration_number=iteration_number,
            refinement_type=refinement_type,
            success=success,
            duration_seconds=duration_seconds,
            source_id="component_refinement_manager",
            metadata={
                "state": "completed"
            }
        )
        
        # Emit with standardized event type
        await self.event_queue.emit(
            ResourceEventTypes.COMPONENT_REFINEMENT_ITERATION.value,
            asdict(payload)
        )
        
        return iteration
        
    async def cleanup_obsolete_contexts(
        self,
        new_validation_state: ComponentValidationState,
        agent_id: Optional[str] = None
    ) -> None:
        """
        Clean up obsolete contexts after backtracking.
        
        This method removes refinement contexts and iterations that are no longer
        relevant after backtracking to an earlier validation state.
        
        Args:
            new_validation_state: The new validation state after backtracking
            agent_id: Optional agent ID to only clean up contexts for a specific agent
        """
        if not self._current_refinement:
            return
            
        removed_contexts = 0
        removed_iterations = 0
        
        # Get all refinement contexts
        try:
            contexts = await self.state_manager.get_states_by_prefix("component_refinement_context:")
            
            for context_id, context_state in contexts.items():
                if not hasattr(context_state, 'state') or not isinstance(context_state.state, dict):
                    continue
                    
                # Parse context data
                context_data = context_state.state
                context_component_id = context_data.get("component_id", "")
                context_agent = context_data.get("responsible_agent", "")
                
                # Skip if filtering by agent and not matching
                if agent_id and context_agent != agent_id:
                    continue
                    
                # Remove this context if it's obsolete based on state transition
                if self._is_context_obsolete(context_data.get("validation_state", ""), new_validation_state.value):
                    # Clean up iterations for this context
                    iterations_removed = await self._cleanup_iterations_for_context(context_id)
                    removed_iterations += iterations_removed
                    
                    # Remove the context itself
                    await self.state_manager.delete_state(context_id)
                    
                    # Clean up from memory
                    if context_id in self._refinement_iterations:
                        del self._refinement_iterations[context_id]
                        
                    # Clean up memory tracking
                    if self.memory_monitor:
                        await self.memory_monitor.remove_resource(f"component_refinement_context:{context_id}")
                        
                    removed_contexts += 1
                    
                    # Emit cleanup event using standardized event type and payload
                    from resources.schemas import RefinementContextPayload
                    from dataclasses import asdict
                    
                    # Create standardized payload
                    payload = RefinementContextPayload(
                        context_id=context_id,
                        phase_id=context_data.get("component_id", "unknown"),
                        validation_state=context_data.get("validation_state", "unknown"),
                        responsible_agent=context_data.get("responsible_agent"),
                        error_count=len(context_data.get("validation_errors", [])),
                        state="cleaned_up",
                        source_id="component_refinement_manager",
                        metadata={
                            "reason": "backtracking",
                            "new_validation_state": new_validation_state.value
                        }
                    )
                    
                    # Emit with standardized event type
                    await self.event_queue.emit(
                        ResourceEventTypes.COMPONENT_REFINEMENT_UPDATED.value,
                        asdict(payload)
                    )
        except Exception as e:
            logger.error(f"Error cleaning up obsolete contexts: {str(e)}")
            
        # Record cleanup metrics
        await self.metrics_manager.record_metric(
            "component_guideline:refinement:contexts_cleaned",
            removed_contexts,
            metadata={
                "iterations_cleaned": removed_iterations,
                "new_validation_state": new_validation_state.value,
                "agent_filter": agent_id or "none",
                "timestamp": datetime.now().isoformat()
            }
        )
        
    def _is_context_obsolete(self, context_state: str, new_state: str) -> bool:
        """
        Determine if a context is obsolete based on state transition.
        
        Args:
            context_state: The validation state of the context
            new_state: The new validation state after backtracking
            
        Returns:
            bool: True if the context is obsolete, False otherwise
        """
        # State precedence order
        state_order = {
            ComponentValidationState.NOT_STARTED.value: 0,
            ComponentValidationState.DESCRIPTION_VALIDATING.value: 1,
            ComponentValidationState.DESCRIPTION_REVISING.value: 2,
            ComponentValidationState.REQUIREMENTS_VALIDATING.value: 3,
            ComponentValidationState.REQUIREMENTS_REVISING.value: 4,
            ComponentValidationState.DATA_FLOW_VALIDATING.value: 5,
            ComponentValidationState.DATA_FLOW_REVISING.value: 6,
            ComponentValidationState.FEATURES_VALIDATING.value: 7,
            ComponentValidationState.FEATURES_REVISING.value: 8,
            ComponentValidationState.ARBITRATION.value: 9,
            ComponentValidationState.COMPLETED.value: 10
        }
        
        # Get numeric precedence
        context_precedence = state_order.get(context_state, 0)
        new_precedence = state_order.get(new_state, 0)
        
        # A context is obsolete if we're backtracking to an earlier state
        # or if we're moving to a different branch at the same level
        if new_precedence < context_precedence:
            return True
            
        # Special case: if we're moving from arbitration to a specific revision state,
        # only clean up contexts that aren't for the responsible agent
        if context_state == ComponentValidationState.ARBITRATION.value and (
            new_state == ComponentValidationState.DESCRIPTION_REVISING.value or
            new_state == ComponentValidationState.REQUIREMENTS_REVISING.value or
            new_state == ComponentValidationState.DATA_FLOW_REVISING.value or
            new_state == ComponentValidationState.FEATURES_REVISING.value
        ):
            # We'll keep all arbitration contexts - they might be useful
            # The context for the specific agent will be cleaned separately
            return False
            
        return False
        
    async def _cleanup_iterations_for_context(self, context_id: str) -> int:
        """
        Clean up iterations for a specific context.
        
        Args:
            context_id: The context ID to clean up iterations for
            
        Returns:
            int: Number of iterations cleaned up
        """
        removed_count = 0
        
        try:
            # Find all iterations for this context
            iterations = await self.state_manager.get_states_by_prefix(f"component_refinement_iteration:{context_id}:")
            
            for iteration_id in iterations:
                await self.state_manager.delete_state(iteration_id)
                removed_count += 1
                
                # Emit cleanup event using standardized event type and payload
                from resources.schemas import RefinementIterationPayload
                from dataclasses import asdict
                
                # Parse iteration ID to extract iteration number
                try:
                    parts = iteration_id.split(":")
                    iteration_number = int(parts[-2]) if len(parts) >= 3 else 0
                    refinement_type = parts[-1] if len(parts) >= 3 else "unknown"
                except (ValueError, IndexError):
                    iteration_number = 0
                    refinement_type = "unknown"
                
                # Create standardized payload
                payload = RefinementIterationPayload(
                    context_id=context_id,
                    iteration_number=iteration_number,
                    refinement_type=refinement_type,
                    success=False,  # Cleaned up before completion
                    duration_seconds=0.0,
                    source_id="component_refinement_manager",
                    metadata={
                        "state": "cleaned_up",
                        "reason": "context_obsolete"
                    }
                )
                
                # Emit with standardized event type
                await self.event_queue.emit(
                    ResourceEventTypes.COMPONENT_REFINEMENT_ITERATION.value,
                    asdict(payload)
                )
        except Exception as e:
            logger.error(f"Error cleaning up iterations for context {context_id}: {str(e)}")
            
        return removed_count
        
    async def run_with_timeout(
        self,
        coro,
        timeout_seconds: float,
        context_id: str,
        operation_type: str
    ) -> Tuple[Any, float, bool]:
        """
        Run a coroutine with timeout tracking.
        
        Args:
            coro: Coroutine to run
            timeout_seconds: Timeout in seconds
            context_id: Context ID for tracking
            operation_type: Type of operation (refinement, reflection, revision)
            
        Returns:
            Tuple[Any, float, bool]: (result, duration_seconds, success)
        """
        start_time = datetime.now()
        
        try:
            # Register operation start for monitoring
            if self.system_monitor:
                await self.system_monitor.register_operation(
                    f"component_refinement_{operation_type}_{context_id}",
                    {
                        "operation_type": operation_type,
                        "context_id": context_id,
                        "start_time": start_time.isoformat(),
                        "timeout_seconds": timeout_seconds
                    }
                )
                
            # Run with timeout
            result = await self.timeout_manager.run_with_timeout(
                coro, 
                timeout_seconds
            )
            
            end_time = datetime.now()
            duration_seconds = (end_time - start_time).total_seconds()
            
            # Register operation completion
            if self.system_monitor:
                await self.system_monitor.update_operation(
                    f"component_refinement_{operation_type}_{context_id}",
                    {
                        "status": "completed",
                        "duration_seconds": duration_seconds,
                        "end_time": end_time.isoformat()
                    }
                )
                
            return result, duration_seconds, True
            
        except asyncio.TimeoutError:
            end_time = datetime.now()
            duration_seconds = (end_time - start_time).total_seconds()
            
            # Register timeout
            if self.system_monitor:
                await self.system_monitor.update_operation(
                    f"component_refinement_{operation_type}_{context_id}",
                    {
                        "status": "timeout",
                        "duration_seconds": duration_seconds,
                        "end_time": end_time.isoformat()
                    }
                )
                
            # Record timeout metric
            await self.metrics_manager.record_metric(
                f"component_guideline:refinement:{operation_type}_timeout",
                1.0,
                metadata={
                    "context_id": context_id,
                    "duration_seconds": duration_seconds,
                    "timeout_seconds": timeout_seconds,
                    "timestamp": end_time.isoformat()
                }
            )
                
            logger.warning(f"Timeout in {operation_type} operation for context {context_id} after {duration_seconds}s")
            
            # Return default timeout result
            return {"error": f"Operation timed out after {timeout_seconds} seconds"}, duration_seconds, False
            
        except Exception as e:
            end_time = datetime.now()
            duration_seconds = (end_time - start_time).total_seconds()
            
            # Register error
            if self.system_monitor:
                await self.system_monitor.update_operation(
                    f"component_refinement_{operation_type}_{context_id}",
                    {
                        "status": "error",
                        "error": str(e),
                        "duration_seconds": duration_seconds,
                        "end_time": end_time.isoformat()
                    }
                )
                
            logger.error(f"Error in {operation_type} operation for context {context_id}: {str(e)}")
            
            # Return error result
            return {"error": f"Operation failed: {str(e)}"}, duration_seconds, False
            
    async def three_stage_refinement(
        self,
        context_id: str,
        agent: AgentInterface,
        initial_input: Dict[str, Any],
        refinement_timeout: Optional[float] = None,
        reflection_timeout: Optional[float] = None,
        revision_timeout: Optional[float] = None,
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Execute the three-stage refinement process (refinement, reflection, revision).
        
        Args:
            context_id: Refinement context ID
            agent: Agent to use for refinement
            initial_input: Initial input for refinement
            refinement_timeout: Timeout for refinement stage (seconds)
            reflection_timeout: Timeout for reflection stage (seconds)
            revision_timeout: Timeout for revision stage (seconds)
            max_iterations: Maximum number of iterations
            
        Returns:
            Dict[str, Any]: Final refinement result
        """
        # Use default timeouts if not specified
        refinement_timeout = refinement_timeout or self.DEFAULT_REFINEMENT_TIMEOUT
        reflection_timeout = reflection_timeout or self.DEFAULT_REFLECTION_TIMEOUT
        revision_timeout = revision_timeout or self.DEFAULT_REVISION_TIMEOUT
        
        # Initialize tracking
        iteration = 1
        current_input = initial_input
        best_result = None
        best_score = 0.0
        
        while iteration <= max_iterations:
            # 1. Initial refinement
            refinement_result, refinement_duration, refinement_success = await self.run_with_timeout(
                agent.process_with_validation(
                    conversation=f"Perform refinement analysis: {current_input}",
                    system_prompt_info=("FFTT_system_prompts/phase_two", "component_guideline_refinement_prompt")
                ),
                refinement_timeout,
                context_id,
                "refinement"
            )
            
            # Track refinement iteration
            await self.track_refinement_iteration(
                context_id=context_id,
                iteration_number=iteration,
                refinement_type="refinement",
                input_data=current_input,
                output_data=refinement_result,
                success=refinement_success,
                duration_seconds=refinement_duration,
                metadata={"stage": 1}
            )
            
            if not refinement_success:
                logger.warning(f"Refinement failed on iteration {iteration}, stopping refinement process")
                return refinement_result  # Return error result
            
            # 2. Reflection
            reflection_result, reflection_duration, reflection_success = await self.run_with_timeout(
                agent.process_with_validation(
                    conversation=f"Reflect on refinement analysis: {refinement_result}",
                    system_prompt_info=("FFTT_system_prompts/phase_two", "component_guideline_reflection_prompt")
                ),
                reflection_timeout,
                context_id,
                "reflection"
            )
            
            # Track reflection iteration
            await self.track_refinement_iteration(
                context_id=context_id,
                iteration_number=iteration,
                refinement_type="reflection",
                input_data=refinement_result,
                output_data=reflection_result,
                success=reflection_success,
                duration_seconds=reflection_duration,
                metadata={"stage": 2}
            )
            
            if not reflection_success:
                logger.warning(f"Reflection failed on iteration {iteration}, using refinement result")
                return refinement_result  # Fallback to refinement result
            
            # 3. Revision
            revision_input = {
                "refinement_analysis": refinement_result.get("refinement_analysis", {}),
                "reflection_results": reflection_result.get("reflection_results", {})
            }
            
            revision_result, revision_duration, revision_success = await self.run_with_timeout(
                agent.process_with_validation(
                    conversation=f"Revise refinement based on reflection: {revision_input}",
                    system_prompt_info=("FFTT_system_prompts/phase_two", "component_guideline_revision_prompt")
                ),
                revision_timeout,
                context_id,
                "revision"
            )
            
            # Track revision iteration
            await self.track_refinement_iteration(
                context_id=context_id,
                iteration_number=iteration,
                refinement_type="revision",
                input_data=revision_input,
                output_data=revision_result,
                success=revision_success,
                duration_seconds=revision_duration,
                metadata={"stage": 3}
            )
            
            if not revision_success:
                logger.warning(f"Revision failed on iteration {iteration}, using refinement result")
                return refinement_result  # Fallback to refinement result
            
            # Calculate quality score from revision confidence
            current_score = self._calculate_quality_score(revision_result)
            
            # Update best result if this is better
            if current_score > best_score:
                best_result = revision_result
                best_score = current_score
            
            # Check if result meets quality threshold
            if self._meets_quality_threshold(revision_result):
                logger.info(f"Refinement meets quality threshold on iteration {iteration}, stopping early")
                return revision_result
            
            # Prepare for next iteration
            iteration += 1
            current_input = revision_result
        
        # Return best result or final revision result
        return best_result or revision_result
    
    def _calculate_quality_score(self, revision_result: Dict[str, Any]) -> float:
        """
        Calculate quality score from revision result.
        
        Args:
            revision_result: Revision result data
            
        Returns:
            float: Quality score (0.0-1.0)
        """
        # Extract confidence assessment
        try:
            confidence = revision_result.get("revision_results", {}).get("revision_summary", {}).get("confidence_assessment", "medium")
            
            # Convert to numeric score
            if confidence == "high":
                return 1.0
            elif confidence == "medium":
                return 0.7
            else:  # low
                return 0.4
        except (KeyError, AttributeError):
            return 0.0
    
    def _meets_quality_threshold(self, revision_result: Dict[str, Any]) -> bool:
        """
        Check if revision result meets quality threshold.
        
        Args:
            revision_result: Revision result data
            
        Returns:
            bool: True if meets threshold, False otherwise
        """
        # Check for high confidence and no remaining uncertainties
        try:
            revision_summary = revision_result.get("revision_results", {}).get("revision_summary", {})
            confidence = revision_summary.get("confidence_assessment", "low")
            uncertainties = revision_summary.get("remaining_uncertainties", [])
            
            # High confidence with few or no uncertainties
            return confidence == "high" and len(uncertainties) <= 1
        except (KeyError, AttributeError, TypeError):
            return False
            
    async def get_health_status(self) -> HealthStatus:
        """
        Get health status of the refinement manager.
        
        Returns:
            HealthStatus: Current health status
        """
        # Count active refinement contexts
        active_count = len(self._refinement_iterations)
        
        # Count total iterations
        iteration_count = sum(len(iterations) for iterations in self._refinement_iterations.values())
        
        # Calculate average iterations per context
        avg_iterations = iteration_count / max(active_count, 1)
        
        # Determine status based on metrics
        status = "HEALTHY"
        description = "Component refinement manager operating normally"
        
        if avg_iterations > 2.5:
            status = "DEGRADED"
            description = "High average iteration count, refinement may be struggling"
            
        if active_count > 10:
            status = "DEGRADED"
            description = "High number of active refinement contexts"
        
        return HealthStatus(
            status=status,
            source="component_refinement_manager",
            description=description,
            metadata={
                "active_contexts": active_count,
                "total_iterations": iteration_count,
                "avg_iterations": round(avg_iterations, 2)
            }
        )