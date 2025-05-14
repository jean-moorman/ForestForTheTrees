"""
Forest For The Trees (FFTT) Phase Coordination System
---------------------------------------------------
Provides centralized phase lifecycle management, transition coordination,
and nested phase execution.

This package coordinates the different phases of the FFTT system,
managing the lifecycle of phases and orchestrating transitions between them.
"""
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, Set, Union

from resources.events import EventQueue, EventLoopManager, ResourceEventTypes
from resources.state import StateManager
from resources.managers import AgentContextManager, CacheManager, MetricsManager, CircuitBreakerRegistry
from resources.monitoring import SystemMonitor, MemoryMonitor, CircuitBreaker, CircuitBreakerConfig
from system_error_recovery import ErrorHandler

from resources.phase_coordinator.constants import PhaseState, PhaseType, _CUSTOM_PHASE_TYPES
from resources.phase_coordinator.models import PhaseContext, NestedPhaseExecution
from resources.phase_coordinator.phase_manager import PhaseManager
from resources.phase_coordinator.circuit_breakers import CircuitBreakerManager
from resources.phase_coordinator.monitoring import PhaseMonitor
from resources.phase_coordinator.checkpoint import CheckpointManager
from resources.phase_coordinator.nested_execution import NestedExecutionManager
from resources.phase_coordinator.transition_handler import PhaseTransitionHandler
from resources.phase_coordinator.utils import is_valid_phase_type, get_phase_type_value

logger = logging.getLogger(__name__)

class PhaseCoordinator:
    """
    Manages phase transitions and nested phase execution
    
    The PhaseCoordinator is the main facade class that orchestrates the different
    components of the phase coordination system. It manages the lifecycle of phases,
    coordinates transitions between phases, and handles nested phase execution.
    """
    
    def __init__(self, 
                event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                memory_monitor: Optional[MemoryMonitor] = None,
                system_monitor: Optional[SystemMonitor] = None,
                circuit_breaker_registry: Optional[CircuitBreakerRegistry] = None,
                custom_circuit_breaker_configs: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Initialize the phase coordinator
        
        Args:
            event_queue: Event queue for sending events
            state_manager: State manager for persisting phase state
            context_manager: Agent context manager for agent contexts
            cache_manager: Cache manager for caching
            metrics_manager: Metrics manager for recording metrics
            error_handler: Error handler for handling errors
            memory_monitor: Optional memory monitor
            system_monitor: Optional system monitor
            circuit_breaker_registry: Optional circuit breaker registry
            custom_circuit_breaker_configs: Optional custom circuit breaker configurations
        """
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._context_manager = context_manager
        self._cache_manager = cache_manager
        self._metrics_manager = metrics_manager
        self._error_handler = error_handler
        self._memory_monitor = memory_monitor
        self._system_monitor = system_monitor
        
        # Initialize component managers
        self._circuit_breaker_manager = CircuitBreakerManager(
            event_queue, 
            state_manager, 
            circuit_breaker_registry,
            custom_circuit_breaker_configs
        )
        
        self._phase_manager = PhaseManager(
            event_queue,
            state_manager,
            metrics_manager
        )
        
        self._checkpoint_manager = CheckpointManager(
            event_queue,
            state_manager,
            metrics_manager
        )
        
        self._nested_execution_manager = NestedExecutionManager(
            event_queue,
            metrics_manager
        )
        
        self._phase_monitor = PhaseMonitor(
            event_queue,
            metrics_manager
        )
        
        # Service state
        self._running = False
        
        # Register with event loop manager
        EventLoopManager.register_resource(f"phase_coordinator_{id(self)}", self)
        
        # Load circuit breaker configurations
        asyncio.create_task(self._circuit_breaker_manager.load_circuit_breaker_configs())
    
    async def start(self):
        """Start the phase coordinator service."""
        if self._running:
            return
            
        self._running = True
        
        # Start phase monitoring
        await self._phase_monitor.start_monitoring(
            self._phase_manager.get_phase_states(),
            self._phase_manager.get_active_phases(),
            self._nested_execution_manager.get_nested_executions()
        )
        
        logger.info("Phase coordinator service started")
    
    async def stop(self):
        """Stop the phase coordinator service."""
        if not self._running:
            return
            
        self._running = False
        
        # Stop phase monitoring
        await self._phase_monitor.stop_monitoring()
                
        logger.info("Phase coordinator service stopped")
    
    # Phase management methods
    
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
        return await self._phase_manager.initialize_phase(
            phase_id, 
            phase_type, 
            phase_config,
            parent_phase_id,
            metadata
        )
    
    async def start_phase(self, phase_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start or resume execution of a phase with input data
        
        Args:
            phase_id: The phase identifier
            input_data: Input data for the phase
            
        Returns:
            Dict[str, Any]: The phase execution result
        """
        # Get the phase context to determine its type
        context = self._phase_manager.get_phase_states().get(phase_id)
        if not context:
            return {"error": f"Phase {phase_id} not found", "status": "error"}
        
        # Get the appropriate circuit breaker based on phase type
        phase_type_value = get_phase_type_value(context.phase_type)
        circuit_breaker = self._circuit_breaker_manager.get_phase_circuit_breaker(phase_type_value)
        
        return await self._phase_manager.start_phase(phase_id, input_data, circuit_breaker)
    
    async def pause_phase(self, phase_id: str, reason: str) -> bool:
        """
        Pause a running phase
        
        Args:
            phase_id: The phase identifier
            reason: Reason for pausing
            
        Returns:
            bool: True if phase was paused
        """
        return await self._phase_manager.pause_phase(phase_id, reason)
    
    async def resume_phase(self, phase_id: str) -> bool:
        """
        Resume a paused phase
        
        Args:
            phase_id: The phase identifier
            
        Returns:
            bool: True if phase was resumed
        """
        return await self._phase_manager.resume_phase(phase_id)
    
    async def abort_phase(self, phase_id: str, reason: str) -> bool:
        """
        Abort a running or paused phase
        
        Args:
            phase_id: The phase identifier
            reason: Reason for aborting
            
        Returns:
            bool: True if phase was aborted
        """
        return await self._phase_manager.abort_phase(phase_id, reason)
    
    async def get_phase_status(self, phase_id: str) -> Dict[str, Any]:
        """
        Get the current status of a phase
        
        Args:
            phase_id: The phase identifier
            
        Returns:
            Dict[str, Any]: Phase status information
        """
        return await self._phase_manager.get_phase_status(phase_id)
    
    async def get_current_phase_info(self) -> Dict[str, Any]:
        """
        Get information about currently active phases
        
        Returns:
            Dict[str, Any]: Information about active phases
        """
        phase_info = await self._phase_manager.get_current_phase_info()
        
        # Add nested execution info
        nested_executions = self._nested_execution_manager.get_nested_executions()
        phase_info["nested_executions"] = {
            "total": len(nested_executions),
            "pending": sum(1 for exec in nested_executions.values() if exec.status == "pending"),
            "completed": sum(1 for exec in nested_executions.values() if exec.status == "completed"),
            "failed": sum(1 for exec in nested_executions.values() if exec.status == "failed")
        }
        
        return phase_info
    
    # Checkpoint methods
    
    async def create_checkpoint(self, phase_id: str) -> str:
        """
        Create a checkpoint for the current phase state
        
        Args:
            phase_id: The phase identifier
            
        Returns:
            str: Checkpoint identifier
        """
        context = self._phase_manager.get_phase_states().get(phase_id)
        if not context:
            logger.error(f"Cannot create checkpoint for unknown phase: {phase_id}")
            raise ValueError(f"Phase {phase_id} not found")
        
        return await self._checkpoint_manager.create_checkpoint(phase_id, context)
    
    async def restore_from_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Restore a phase from a checkpoint
        
        Args:
            checkpoint_id: The checkpoint identifier
            
        Returns:
            bool: True if restored successfully
        """
        context = await self._checkpoint_manager.restore_from_checkpoint(checkpoint_id)
        if not context:
            return False
        
        # Update phase state tracking
        phase_id = context.phase_id
        self._phase_manager.get_phase_states()[phase_id] = context
        
        # Update other state tracking
        if context.parent_phase_id:
            phase_hierarchy = self._phase_manager.get_phase_hierarchy()
            if context.parent_phase_id not in phase_hierarchy:
                phase_hierarchy[context.parent_phase_id] = set()
            phase_hierarchy[context.parent_phase_id].add(phase_id)
            
        if context.dependencies:
            self._phase_manager.get_phase_dependencies()[phase_id] = context.dependencies
        
        return True
    
    async def rollback_to_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Roll back to a previously created checkpoint
        
        Args:
            checkpoint_id: The checkpoint ID to roll back to
            
        Returns:
            bool: True if rollback was successful
        """
        context = await self._checkpoint_manager.rollback_to_checkpoint(checkpoint_id)
        return context is not None
    
    # Nested execution methods
    
    async def coordinate_nested_execution(self, 
                                         parent_phase_id: str, 
                                         child_phase_id: str, 
                                         input_data: Dict[str, Any],
                                         timeout_seconds: Optional[int] = None,
                                         priority: str = "normal",
                                         execution_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Coordinate execution of a child phase from a parent phase with configurable execution parameters
        
        Args:
            parent_phase_id: Parent phase identifier
            child_phase_id: Child phase identifier
            input_data: Input data for the child phase
            timeout_seconds: Optional timeout in seconds for this execution (overrides default)
            priority: Execution priority ("high", "normal", "low")
            execution_metadata: Optional additional metadata for the execution
            
        Returns:
            Dict[str, Any]: Result of child phase execution
        """
        return await self._nested_execution_manager.coordinate_nested_execution(
            parent_phase_id, 
            child_phase_id, 
            input_data,
            self._circuit_breaker_manager.get_transition_circuit_breaker(),
            self._phase_manager,
            self._phase_manager.get_transition_handlers(),
            self._phase_manager.get_phase_states(),
            timeout_seconds,
            priority,
            execution_metadata
        )
    
    # Custom phase type management methods
    
    async def register_custom_phase_type(self, 
                                  phase_type: str, 
                                  description: str,
                                  parent_phase_type: Optional[str] = None,
                                  config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Register a custom phase type for dynamic extensibility
        
        Args:
            phase_type: The unique identifier for the phase type (e.g., "phase_custom")
            description: Human-readable description of the phase type
            parent_phase_type: Optional parent phase type for inheritance
            config: Optional configuration for the phase type
            
        Returns:
            bool: True if registration was successful
        """
        # Validate phase type ID
        if not phase_type or not isinstance(phase_type, str) or not phase_type.startswith("phase_"):
            logger.error(f"Invalid phase type ID: {phase_type}. Must start with 'phase_'")
            return False
            
        # Check if phase type already exists in built-in types
        for existing_type in PhaseType:
            if existing_type.value == phase_type:
                logger.error(f"Cannot register custom phase type: {phase_type} already exists as built-in type")
                return False
                
        # Check if phase type is already registered
        if phase_type in _CUSTOM_PHASE_TYPES:
            logger.warning(f"Phase type {phase_type} already registered, updating")
            
        # Register circuit breaker for the new phase type
        self._circuit_breaker_manager.register_custom_phase_circuit_breaker(phase_type)
            
        # Register the custom phase type
        _CUSTOM_PHASE_TYPES[phase_type] = {
            "description": description,
            "parent_type": parent_phase_type,
            "config": config or {},
            "registered_at": datetime.now().isoformat(),
            "registered_by": "phase_coordinator"
        }
        
        # Log registration
        logger.info(f"Registered custom phase type: {phase_type} ({description})")
        
        # Emit event
        await self._event_queue.emit(
            ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
            {
                "resource_id": f"phase_type:{phase_type}",
                "state": "registered",
                "description": description,
                "parent_type": parent_phase_type,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return True
        
    async def unregister_custom_phase_type(self, phase_type: str) -> bool:
        """
        Unregister a previously registered custom phase type
        
        Args:
            phase_type: The phase type to unregister
            
        Returns:
            bool: True if unregistration was successful
        """
        if phase_type not in _CUSTOM_PHASE_TYPES:
            logger.warning(f"Cannot unregister: Phase type {phase_type} not found in custom registry")
            return False
            
        # Check if any active phases use this type
        for phase_id, context in self._phase_manager.get_phase_states().items():
            if context.phase_type.value == phase_type:
                logger.error(f"Cannot unregister phase type {phase_type} - in use by phase {phase_id}")
                return False
                
        # Remove from registry
        phase_info = _CUSTOM_PHASE_TYPES.pop(phase_type)
        
        # Emit event
        await self._event_queue.emit(
            ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
            {
                "resource_id": f"phase_type:{phase_type}",
                "state": "unregistered",
                "description": phase_info.get("description", ""),
                "timestamp": datetime.now().isoformat()
            }
        )
        
        logger.info(f"Unregistered custom phase type: {phase_type}")
        return True
    
    async def get_registered_phase_types(self) -> Dict[str, Any]:
        """
        Get information about all registered phase types (built-in and custom)
        
        Returns:
            Dict[str, Any]: Information about registered phase types
        """
        # Combine built-in and custom types
        phase_types = {}
        
        # Add built-in types
        for phase_type in PhaseType:
            # Get circuit breaker configuration if available
            circuit_breaker = self._circuit_breaker_manager.get_phase_circuit_breaker(phase_type.value)
            circuit_breaker_config = self._circuit_breaker_manager._circuit_breaker_configs.get(phase_type.value)
            cb_config_dict = None
            if circuit_breaker_config:
                cb_config_dict = {
                    "failure_threshold": circuit_breaker_config.failure_threshold,
                    "recovery_timeout": circuit_breaker_config.recovery_timeout,
                    "failure_window": circuit_breaker_config.failure_window
                }
                
            # Count active phases of this type
            active_count = sum(
                1 for ctx in self._phase_manager.get_phase_states().values()
                if isinstance(ctx.phase_type, PhaseType) and ctx.phase_type == phase_type
            )
            
            phase_types[phase_type.value] = {
                "name": phase_type.name,
                "value": phase_type.value,
                "type": "built-in",
                "description": f"Built-in {phase_type.name.lower()} phase type",
                "circuit_breaker_config": cb_config_dict,
                "active_phases": active_count,
                "circuit_open": circuit_breaker.is_open() if circuit_breaker else False
            }
            
        # Add custom types with extended information
        for phase_type, info in _CUSTOM_PHASE_TYPES.items():
            # Get circuit breaker configuration
            circuit_breaker = self._circuit_breaker_manager.get_phase_circuit_breaker(phase_type)
            circuit_breaker_config = self._circuit_breaker_manager._circuit_breaker_configs.get(phase_type)
            cb_config_dict = None
            if circuit_breaker_config:
                cb_config_dict = {
                    "failure_threshold": circuit_breaker_config.failure_threshold,
                    "recovery_timeout": circuit_breaker_config.recovery_timeout,
                    "failure_window": circuit_breaker_config.failure_window
                }
                
            # Count active phases of this type
            active_count = sum(
                1 for ctx in self._phase_manager.get_phase_states().values()
                if ctx.is_custom_type and 
                (isinstance(ctx.phase_type, str) and ctx.phase_type == phase_type)
            )
            
            # Build inheritance chain if available
            parent_chain = []
            current_parent = info.get("parent_type")
            while current_parent:
                parent_chain.append(current_parent)
                # Check if parent is a custom type too
                if current_parent in _CUSTOM_PHASE_TYPES:
                    current_parent = _CUSTOM_PHASE_TYPES[current_parent].get("parent_type")
                else:
                    # Built-in parent type
                    break
                    
            phase_types[phase_type] = {
                "name": phase_type.replace("phase_", "").upper(),
                "value": phase_type,
                "type": "custom",
                "description": info.get("description", ""),
                "parent_type": info.get("parent_type"),
                "registered_at": info.get("registered_at"),
                "circuit_breaker_config": cb_config_dict,
                "active_phases": active_count,
                "circuit_open": circuit_breaker.is_open() if circuit_breaker else False,
                "custom_config": info.get("config", {}),
                "parent_chain": parent_chain if parent_chain else None
            }
            
        # Get hierarchical relationships (which phase types inherit from others)
        inheritance_map = {}
        for phase_type, info in _CUSTOM_PHASE_TYPES.items():
            parent = info.get("parent_type")
            if parent:
                if parent not in inheritance_map:
                    inheritance_map[parent] = []
                inheritance_map[parent].append(phase_type)
            
        return {
            "phase_types": phase_types,
            "inheritance_map": inheritance_map,
            "count": {
                "built-in": len(PhaseType),
                "custom": len(_CUSTOM_PHASE_TYPES),
                "total": len(phase_types)
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def update_circuit_breaker_config(self, phase_type: str, config: CircuitBreakerConfig) -> bool:
        """
        Update circuit breaker configuration for a specific phase type
        
        Args:
            phase_type: The phase type to update configuration for
            config: The new circuit breaker configuration
            
        Returns:
            bool: True if update was successful
        """
        return await self._circuit_breaker_manager.update_circuit_breaker_config(phase_type, config)
    
    async def get_phase_health(self) -> Dict[str, Any]:
        """
        Get health status of all phases
        
        Returns:
            Dict[str, Any]: Health status information
        """
        # Get phase circuit breakers
        phase_circuit_breakers = {
            phase_type.value: self._circuit_breaker_manager.get_phase_circuit_breaker(phase_type.value)
            for phase_type in PhaseType
        }
        
        # Add custom phase circuit breakers
        for phase_type in _CUSTOM_PHASE_TYPES:
            phase_circuit_breakers[phase_type] = self._circuit_breaker_manager.get_phase_circuit_breaker(phase_type)
        
        return await self._phase_monitor.get_phase_health(
            self._phase_manager.get_phase_states(),
            self._phase_manager.get_active_phases(),
            phase_circuit_breakers,
            self._circuit_breaker_manager.get_transition_circuit_breaker()
        )
    
    def is_valid_phase_type(self, phase_type: Union[str, PhaseType]) -> bool:
        """
        Check if a given phase type is valid (built-in or custom)
        
        Args:
            phase_type: The phase type to check (string or enum)
            
        Returns:
            bool: True if valid phase type
        """
        return is_valid_phase_type(phase_type)

# Export key classes and types
__all__ = [
    'PhaseCoordinator',
    'PhaseState',
    'PhaseType',
    'PhaseContext',
    'NestedPhaseExecution',
    'PhaseTransitionHandler'
]