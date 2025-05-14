"""
Forest For The Trees (FFTT) Phase Coordination System - Phase Manager
---------------------------------------------------
Core phase management functionality.
"""
import logging
import asyncio
from typing import Dict, Any, List, Set, Optional, Union
from datetime import datetime

from resources.phase_coordinator.constants import PhaseState, PhaseType, _CUSTOM_PHASE_TYPES
from resources.phase_coordinator.models import PhaseContext
from resources.phase_coordinator.transition_handler import register_transition_handlers
from resources.phase_coordinator.utils import emit_phase_state_change_event, get_phase_type_value
from resources.events import EventQueue, ResourceEventTypes
from resources.state import StateManager, ResourceType
from resources.managers import MetricsManager
from resources.monitoring import CircuitBreaker, CircuitOpenError

logger = logging.getLogger(__name__)

class PhaseManager:
    """Manages phase lifecycle and state transitions"""
    
    def __init__(self, 
                event_queue: EventQueue,
                state_manager: StateManager,
                metrics_manager: MetricsManager):
        """
        Initialize the phase manager
        
        Args:
            event_queue: Event queue for sending events
            state_manager: State manager for persisting phase state
            metrics_manager: Metrics manager for recording phase metrics
        """
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._metrics_manager = metrics_manager
        
        # Phase state tracking
        self._phase_states: Dict[str, PhaseContext] = {}
        self._active_phases: Set[str] = set()
        self._phase_hierarchy: Dict[str, Set[str]] = {}  # parent-child relationships
        self._phase_dependencies: Dict[str, Set[str]] = {}
        self._transition_handlers: Dict[str, List[Any]] = {}
        
        # Create lock for thread safety
        self._state_lock = asyncio.Lock()
    
    async def initialize_phase(self, 
                              phase_id: str, 
                              phase_type: Union[PhaseType, str], 
                              phase_config: Dict[str, Any],
                              parent_phase_id: Optional[str] = None,
                              metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Initialize a phase with configuration and parent-child relationship
        
        Args:
            phase_id: Unique identifier for the phase
            phase_type: Type of phase being initialized (built-in or custom)
            phase_config: Configuration settings for the phase
            parent_phase_id: Optional parent phase identifier
            metadata: Optional additional metadata
            
        Returns:
            bool: True if initialization was successful
        """
        # Track if this is a custom phase type
        is_custom_type = False
        phase_type_value = None
        
        # Validate and convert phase_type
        if isinstance(phase_type, str):
            # Try to convert to built-in PhaseType first
            built_in_type = PhaseType.from_string(phase_type)
            if built_in_type:
                phase_type = built_in_type
                phase_type_value = built_in_type.value
            # If not built-in, check if it's a registered custom type
            elif phase_type in _CUSTOM_PHASE_TYPES:
                # For custom types, store the string value directly
                is_custom_type = True
                phase_type_value = phase_type
                logger.info(f"Using custom phase type: {phase_type}")
            else:
                logger.error(f"Invalid phase type: {phase_type} - not a built-in or registered custom type")
                return False
        else:
            # Using enum value directly
            phase_type_value = phase_type.value
            
        async with self._state_lock:
            # Check if phase already exists
            if phase_id in self._phase_states:
                logger.warning(f"Phase {phase_id} already initialized")
                return False
                
            # Create phase context
            context = PhaseContext(
                phase_id=phase_id,
                phase_type=phase_type,
                parent_phase_id=parent_phase_id,
                config=phase_config,
                metadata=metadata or {},
                is_custom_type=is_custom_type
            )
            
            # Register transition handlers if specified
            handler_names = phase_config.get("handlers", [])
            handlers = register_transition_handlers(handler_names)
            if handlers:
                self._transition_handlers[phase_id] = handlers
            
            # Register parent-child relationship if parent exists
            if parent_phase_id:
                if parent_phase_id not in self._phase_states:
                    logger.warning(f"Parent phase {parent_phase_id} not found when initializing {phase_id}")
                    # Continue anyway, will update when parent is initialized
                
                # Update parent's child phases
                if parent_phase_id not in self._phase_hierarchy:
                    self._phase_hierarchy[parent_phase_id] = set()
                self._phase_hierarchy[parent_phase_id].add(phase_id)
                
                # Get parent context if available
                parent_context = self._phase_states.get(parent_phase_id)
                if parent_context:
                    parent_context.child_phases.add(phase_id)
            
            # Register phase dependencies if specified
            dependencies = phase_config.get("dependencies", [])
            if dependencies:
                self._phase_dependencies[phase_id] = set(dependencies)
                context.dependencies = set(dependencies)
            
            # Store phase context
            self._phase_states[phase_id] = context
            
            # Persist to state manager
            context.state = PhaseState.READY
            await self._update_phase_state(phase_id, PhaseState.READY, {
                **phase_config,
                "initialized_at": datetime.now().isoformat()
            })
            
            # Create log message with phase type (handle both standard and custom types)
            log_phase_type = phase_type_value
            if is_custom_type:
                custom_info = _CUSTOM_PHASE_TYPES.get(phase_type_value, {})
                custom_desc = custom_info.get("description", "")
                log_phase_type = f"{phase_type_value} ({custom_desc})" if custom_desc else phase_type_value
                
            # Log initialization
            logger.info(f"Phase {phase_id} ({log_phase_type}) initialized" + 
                       (f" with parent {parent_phase_id}" if parent_phase_id else ""))
            
            # Emit initialization event
            event_data = {
                "resource_id": f"phase:{phase_id}",
                "state": "initialized",
                "phase_type": phase_type_value,
                "parent_phase_id": parent_phase_id,
                "configuration": phase_config
            }
            
            # Add custom type info if relevant
            if is_custom_type:
                event_data["is_custom_type"] = True
                event_data["custom_type_info"] = {
                    "parent_type": _CUSTOM_PHASE_TYPES.get(phase_type_value, {}).get("parent_type"),
                    "description": _CUSTOM_PHASE_TYPES.get(phase_type_value, {}).get("description")
                }
                
            await self._event_queue.emit(
                ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
                event_data
            )
            
            # Record initialization metric
            await self._metrics_manager.record_metric(
                f"phase_coordinator:initialize:{phase_type_value}",
                1.0,
                metadata={
                    "phase_id": phase_id,
                    "parent_phase_id": parent_phase_id,
                    "is_custom_type": is_custom_type,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            return True
    
    async def start_phase(self, phase_id: str, input_data: Dict[str, Any], circuit_breaker: Optional[CircuitBreaker] = None) -> Dict[str, Any]:
        """
        Start or resume execution of a phase with input data
        
        Args:
            phase_id: The phase identifier
            input_data: Input data for the phase
            circuit_breaker: Optional circuit breaker to protect phase execution
            
        Returns:
            Dict[str, Any]: The phase execution result
        """
        # Ensure phase exists
        context = self._phase_states.get(phase_id)
        if not context:
            logger.error(f"Cannot start unknown phase: {phase_id}")
            return {"error": f"Phase {phase_id} not found", "status": "error"}
            
        # Check dependencies
        dependencies = self._phase_dependencies.get(phase_id, set())
        unfulfilled_deps = []
        
        for dep_id in dependencies:
            dep_context = self._phase_states.get(dep_id)
            if not dep_context or dep_context.state != PhaseState.COMPLETED:
                unfulfilled_deps.append(dep_id)
                
        if unfulfilled_deps:
            logger.warning(f"Phase {phase_id} has unfulfilled dependencies: {unfulfilled_deps}")
            return {
                "error": f"Unfulfilled dependencies: {unfulfilled_deps}",
                "status": "dependency_error"
            }
            
        try:
            # Use circuit breaker to protect phase execution if provided
            if circuit_breaker:
                try:
                    return await circuit_breaker.execute(
                        lambda: self._execute_phase(phase_id, input_data)
                    )
                except CircuitOpenError:
                    phase_type_value = get_phase_type_value(context.phase_type)
                    logger.error(f"Circuit breaker open for {phase_type_value} phase execution")
                    return {
                        "error": f"Circuit breaker open for {phase_type_value} phase execution",
                        "status": "circuit_open",
                        "phase_id": phase_id
                    }
            else:
                # Execute directly without circuit breaker
                return await self._execute_phase(phase_id, input_data)
                
        except Exception as e:
            logger.error(f"Error starting phase {phase_id}: {str(e)}")
            
            # Update phase state to FAILED
            await self._update_phase_state(phase_id, PhaseState.FAILED, {
                "error": str(e),
                "error_type": type(e).__name__
            })
            
            # Remove from active phases
            self._active_phases.discard(phase_id)
            
            # Record end time
            context.end_time = datetime.now()
            
            # Get phase type value for metrics
            phase_type_value = get_phase_type_value(context.phase_type)
            
            # Record error metric
            await self._metrics_manager.record_metric(
                f"phase_coordinator:phase_error:{phase_type_value}",
                1.0,
                metadata={
                    "phase_id": phase_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            
            # Emit failure event
            await self._event_queue.emit(
                ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
                {
                    "resource_id": f"phase:{phase_id}",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "execution_time": (context.end_time - context.start_time).total_seconds() if context.start_time else 0
                }
            )
            
            return {
                "error": str(e),
                "status": "error",
                "phase_id": phase_id
            }
    
    async def _execute_phase(self, phase_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal method to execute a phase with proper tracking
        
        Args:
            phase_id: The phase identifier
            input_data: Input data for the phase
            
        Returns:
            Dict[str, Any]: The phase execution result
        """
        context = self._phase_states.get(phase_id)
        
        # Update phase state to RUNNING
        await self._update_phase_state(phase_id, PhaseState.RUNNING)
        
        # Add to active phases
        self._active_phases.add(phase_id)
        
        # Record start time if not already set
        if not context.start_time:
            context.start_time = datetime.now()
            
        # Get phase type value for metrics
        phase_type_value = get_phase_type_value(context.phase_type)
            
        # Record metric for phase start
        await self._metrics_manager.record_metric(
            f"phase_coordinator:phase_start:{phase_type_value}",
            1.0,
            metadata={
                "phase_id": phase_id,
                "timestamp": context.start_time.isoformat()
            }
        )
        
        # Execute phase implementation (to be implemented in concrete phase classes)
        # This would dispatch to Phase One/Two/Three/Four implementations
        # For now we'll simulate a successful execution
        try:
            logger.info(f"Starting execution of phase {phase_id} ({phase_type_value})")
            
            # Simulate some work
            await asyncio.sleep(0.1)
            
            # Simulate implementation based on phase type
            result = {
                "status": "success",
                "phase_id": phase_id,
                "phase_type": phase_type_value,
                "output": f"Simulated output from {phase_type_value} phase {phase_id}",
                "execution_time": 0.1
            }
            
            # Update phase result
            context.result = result
            
            # Update phase state to COMPLETED
            await self._update_phase_state(phase_id, PhaseState.COMPLETED)
            
            # Remove from active phases
            self._active_phases.discard(phase_id)
            
            # Record end time
            context.end_time = datetime.now()
            
            # Calculate execution time
            execution_time = (context.end_time - context.start_time).total_seconds()
            
            # Record metric for phase completion
            await self._metrics_manager.record_metric(
                f"phase_coordinator:phase_complete:{phase_type_value}",
                1.0,
                metadata={
                    "phase_id": phase_id,
                    "execution_time": execution_time,
                    "timestamp": context.end_time.isoformat()
                }
            )
            
            # Emit completion event
            await self._event_queue.emit(
                ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
                {
                    "resource_id": f"phase:{phase_id}",
                    "state": "completed",
                    "execution_time": execution_time
                }
            )
            
            return result
            
        except Exception as e:
            # Update phase state to FAILED
            await self._update_phase_state(phase_id, PhaseState.FAILED, {
                "error": str(e),
                "error_type": type(e).__name__
            })
            
            # Remove from active phases
            self._active_phases.discard(phase_id)
            
            # Record end time
            context.end_time = datetime.now()
            
            # Emit failure event
            await self._event_queue.emit(
                ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
                {
                    "resource_id": f"phase:{phase_id}",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "execution_time": (context.end_time - context.start_time).total_seconds()
                }
            )
            
            # Re-raise the exception
            raise
    
    async def pause_phase(self, phase_id: str, reason: str) -> bool:
        """
        Pause a running phase
        
        Args:
            phase_id: The phase identifier
            reason: Reason for pausing
            
        Returns:
            bool: True if phase was paused
        """
        context = self._phase_states.get(phase_id)
        if not context:
            logger.error(f"Cannot pause unknown phase: {phase_id}")
            return False
            
        if context.state != PhaseState.RUNNING:
            logger.warning(f"Cannot pause phase {phase_id} in state {context.state.name}")
            return False
            
        # Update phase state to PAUSED
        await self._update_phase_state(phase_id, PhaseState.PAUSED, {
            "pause_reason": reason,
            "pause_time": datetime.now().isoformat()
        })
        
        # Execute pause handlers
        handlers = self._transition_handlers.get(phase_id, [])
        for handler in handlers:
            try:
                if hasattr(handler, 'on_pause') and callable(handler.on_pause):
                    await handler.on_pause(phase_id, reason, context.to_dict())
            except Exception as e:
                logger.error(f"Error executing pause handler for {phase_id}: {str(e)}")
        
        # Get phase type value for metrics
        phase_type_value = get_phase_type_value(context.phase_type)
                
        # Record metric for phase pause
        await self._metrics_manager.record_metric(
            f"phase_coordinator:phase_pause:{phase_type_value}",
            1.0,
            metadata={
                "phase_id": phase_id,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            }
        )
                
        return True
    
    async def resume_phase(self, phase_id: str) -> bool:
        """
        Resume a paused phase
        
        Args:
            phase_id: The phase identifier
            
        Returns:
            bool: True if phase was resumed
        """
        context = self._phase_states.get(phase_id)
        if not context:
            logger.error(f"Cannot resume unknown phase: {phase_id}")
            return False
            
        if context.state != PhaseState.PAUSED:
            logger.warning(f"Cannot resume phase {phase_id} in state {context.state.name}")
            return False
            
        # Update phase state to RUNNING
        await self._update_phase_state(phase_id, PhaseState.RUNNING, {
            "resume_time": datetime.now().isoformat()
        })
        
        # Execute resume handlers
        handlers = self._transition_handlers.get(phase_id, [])
        for handler in handlers:
            try:
                if hasattr(handler, 'on_resume') and callable(handler.on_resume):
                    await handler.on_resume(phase_id, context.to_dict())
            except Exception as e:
                logger.error(f"Error executing resume handler for {phase_id}: {str(e)}")
        
        # Get phase type value for metrics
        phase_type_value = get_phase_type_value(context.phase_type)
                
        # Record metric for phase resume
        await self._metrics_manager.record_metric(
            f"phase_coordinator:phase_resume:{phase_type_value}",
            1.0,
            metadata={
                "phase_id": phase_id,
                "timestamp": datetime.now().isoformat()
            }
        )
                
        return True
    
    async def abort_phase(self, phase_id: str, reason: str) -> bool:
        """
        Abort a running or paused phase
        
        Args:
            phase_id: The phase identifier
            reason: Reason for aborting
            
        Returns:
            bool: True if phase was aborted
        """
        context = self._phase_states.get(phase_id)
        if not context:
            logger.error(f"Cannot abort unknown phase: {phase_id}")
            return False
            
        if context.state not in [PhaseState.RUNNING, PhaseState.PAUSED]:
            logger.warning(f"Cannot abort phase {phase_id} in state {context.state.name}")
            return False
            
        # Update phase state to ABORTED
        await self._update_phase_state(phase_id, PhaseState.ABORTED, {
            "abort_reason": reason,
            "abort_time": datetime.now().isoformat()
        })
        
        # Remove from active phases
        self._active_phases.discard(phase_id)
        
        # Get phase type value for metrics
        phase_type_value = get_phase_type_value(context.phase_type)
        
        # Record metric for phase abort
        await self._metrics_manager.record_metric(
            f"phase_coordinator:phase_abort:{phase_type_value}",
            1.0,
            metadata={
                "phase_id": phase_id,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Emit abort event
        await self._event_queue.emit(
            ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
            {
                "resource_id": f"phase:{phase_id}",
                "state": "aborted",
                "reason": reason
            }
        )
        
        return True
    
    async def get_phase_status(self, phase_id: str) -> Dict[str, Any]:
        """
        Get the current status of a phase
        
        Args:
            phase_id: The phase identifier
            
        Returns:
            Dict[str, Any]: Phase status information
        """
        from resources.phase_coordinator.utils import get_enhanced_status_response
        return get_enhanced_status_response(self._phase_states, phase_id)
    
    async def get_current_phase_info(self) -> Dict[str, Any]:
        """
        Get information about currently active phases
        
        Returns:
            Dict[str, Any]: Information about active phases
        """
        active_phases_info = {}
        
        for phase_id in self._active_phases:
            context = self._phase_states.get(phase_id)
            if context:
                # Get phase type value (handles both built-in enum and custom string)
                phase_type_value = get_phase_type_value(context.phase_type)
                
                active_phases_info[phase_id] = {
                    "phase_type": phase_type_value,
                    "state": context.state.name,
                    "start_time": context.start_time.isoformat() if context.start_time else None,
                    "parent_phase_id": context.parent_phase_id,
                    "child_phases": list(context.child_phases)
                }
                
        # Count phases by type
        phase_type_counts = {}
        for phase_type in PhaseType:
            phase_type_counts[phase_type.value] = sum(
                1 for context in self._phase_states.values() 
                if context.phase_type == phase_type
            )
                
        return {
            "active_phases": active_phases_info,
            "total_active": len(self._active_phases),
            "total_phases": len(self._phase_states),
            "phase_type_counts": phase_type_counts,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _update_phase_state(self, phase_id: str, state: PhaseState, 
                                metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Update phase state in state manager
        
        Args:
            phase_id: The phase identifier
            state: New phase state
            metadata: Optional additional metadata
        """
        context = self._phase_states.get(phase_id)
        if not context:
            raise ValueError(f"Phase {phase_id} not found")
        
        # Store previous state for events
        previous_state = context.state
        
        # Update context
        context.state = state
        if metadata:
            context.config.update(metadata)
        
        # Update timestamp
        if state == PhaseState.RUNNING and not context.start_time:
            context.start_time = datetime.now()
        elif state in (PhaseState.COMPLETED, PhaseState.FAILED, PhaseState.ABORTED):
            context.end_time = datetime.now()
        
        # Get phase type value (handles both built-in enum and custom string)
        phase_type_value = get_phase_type_value(context.phase_type)
        
        # Update in state manager
        state_data = {
            "phase_id": phase_id,
            "phase_type": phase_type_value,
            "is_custom_type": context.is_custom_type,
            "state": state.name,
            "parent_phase_id": context.parent_phase_id,
            "child_phases": list(context.child_phases),
            "dependencies": list(context.dependencies),
            "start_time": context.start_time.isoformat() if context.start_time else None,
            "end_time": context.end_time.isoformat() if context.end_time else None,
            "error_info": context.error_info,
            "timestamp": datetime.now().isoformat(),
            "metadata": context.metadata
        }
        
        # Add custom type info if applicable
        if context.is_custom_type and isinstance(context.phase_type, str) and context.phase_type in _CUSTOM_PHASE_TYPES:
            state_data["custom_type_info"] = {
                "parent_type": _CUSTOM_PHASE_TYPES[context.phase_type].get("parent_type"),
                "description": _CUSTOM_PHASE_TYPES[context.phase_type].get("description")
            }
            
        await self._state_manager.set_state(
            f"phase:{phase_id}:state",
            state_data,
            ResourceType.STATE,
            metadata={
                "update_type": "phase_state_change",
                "previous_state": previous_state.name if previous_state else None
            }
        )
        
        # Emit events for state change
        await emit_phase_state_change_event(
            self._event_queue,
            phase_id,
            previous_state,
            state,
            context.phase_type,
            context.is_custom_type,
            metadata=metadata
        )
    
    def get_active_phases(self) -> Set[str]:
        """Get the set of active phase IDs"""
        return self._active_phases.copy()
    
    def get_phase_states(self) -> Dict[str, PhaseContext]:
        """Get the current phase states"""
        return self._phase_states
    
    def get_phase_hierarchy(self) -> Dict[str, Set[str]]:
        """Get the current phase hierarchy"""
        return self._phase_hierarchy
    
    def get_phase_dependencies(self) -> Dict[str, Set[str]]:
        """Get the current phase dependencies"""
        return self._phase_dependencies
    
    def get_transition_handlers(self) -> Dict[str, List[Any]]:
        """Get the current transition handlers"""
        return self._transition_handlers