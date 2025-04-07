"""
Forest For The Trees (FFTT) Phase Coordination System
---------------------------------------------------
Provides centralized phase lifecycle management, transition coordination,
and nested phase execution.
"""
import asyncio
import logging
import time
import json
from datetime import datetime
from enum import Enum, auto
from typing import Dict, Any, Optional, List, Set, Callable, Awaitable, Protocol, Tuple, Union, Type
from dataclasses import dataclass, field

from resources.common import ResourceType, HealthStatus
from resources.errors import ResourceError, ErrorSeverity
from resources.events import ResourceEventTypes, EventQueue, EventLoopManager
from resources.state import StateManager
from resources.managers import AgentContextManager, CacheManager, MetricsManager, CircuitBreakerRegistry
from resources.monitoring import SystemMonitor, MemoryMonitor, CircuitBreaker, CircuitBreakerConfig, CircuitOpenError
from system_error_recovery import ErrorHandler

logger = logging.getLogger(__name__)

class PhaseState(Enum):
    """States for phase lifecycle"""
    INITIALIZING = auto()
    READY = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()
    ABORTED = auto()

class PhaseType(Enum):
    """Base types of phases in the system"""
    ZERO = "phase_zero"
    ONE = "phase_one"
    TWO = "phase_two"
    THREE = "phase_three"
    FOUR = "phase_four"
    
    @classmethod
    def get_all_values(cls) -> List[str]:
        """Get all phase type values"""
        return [member.value for member in cls]
    
    @classmethod
    def from_string(cls, value: str) -> Optional['PhaseType']:
        """Convert string to PhaseType if valid"""
        for member in cls:
            if member.value == value:
                return member
        return None

# Global registry for custom phase types
_CUSTOM_PHASE_TYPES: Dict[str, Dict[str, Any]] = {}

@dataclass
class PhaseContext:
    """Context information for a phase"""
    phase_id: str
    phase_type: Union[PhaseType, str]  # Can be built-in enum or custom string type
    state: PhaseState = PhaseState.INITIALIZING
    parent_phase_id: Optional[str] = None
    child_phases: Set[str] = field(default_factory=set)
    dependencies: Set[str] = field(default_factory=set)
    config: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    checkpoint_ids: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_info: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_custom_type: bool = False  # Flag to indicate if using a custom phase type
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for storage"""
        # For phase_type, handle both enum and string cases
        phase_type_value = self.phase_type.value if isinstance(self.phase_type, PhaseType) else self.phase_type
        
        return {
            "phase_id": self.phase_id,
            "phase_type": phase_type_value,
            "is_custom_type": self.is_custom_type,
            "state": self.state.name,
            "parent_phase_id": self.parent_phase_id,
            "child_phases": list(self.child_phases),
            "dependencies": list(self.dependencies),
            "config": self.config,
            "metrics": self.metrics,
            "checkpoint_ids": self.checkpoint_ids,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "error_info": self.error_info,
            "result": self.result,
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PhaseContext':
        """Create context from dictionary"""
        # Handle both custom and built-in phase types
        is_custom_type = data.get("is_custom_type", False)
        phase_type_value = data["phase_type"]
        
        if is_custom_type:
            # Custom phase type is stored as a string
            phase_type = phase_type_value
        else:
            # Built-in phase type
            try:
                phase_type = PhaseType(phase_type_value)
            except ValueError:
                # Fallback: if value doesn't match built-in but exists as custom
                if phase_type_value in _CUSTOM_PHASE_TYPES:
                    phase_type = phase_type_value
                    is_custom_type = True
                else:
                    # Default to phase one for backward compatibility
                    logger.warning(f"Unknown phase type: {phase_type_value}, defaulting to phase_one")
                    phase_type = PhaseType.ONE
        
        context = cls(
            phase_id=data["phase_id"],
            phase_type=phase_type,
            is_custom_type=is_custom_type
        )
        context.state = PhaseState[data["state"]]
        context.parent_phase_id = data.get("parent_phase_id")
        context.child_phases = set(data.get("child_phases", []))
        context.dependencies = set(data.get("dependencies", []))
        context.config = data.get("config", {})
        context.metrics = data.get("metrics", {})
        context.checkpoint_ids = data.get("checkpoint_ids", [])
        context.metadata = data.get("metadata", {})
        
        if data.get("start_time"):
            context.start_time = datetime.fromisoformat(data["start_time"])
        if data.get("end_time"):
            context.end_time = datetime.fromisoformat(data["end_time"])
            
        context.error_info = data.get("error_info")
        context.result = data.get("result")
        
        return context

@dataclass
class NestedPhaseExecution:
    """Tracks a nested phase execution"""
    parent_id: str
    child_id: str
    execution_id: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    status: str = "pending"
    result: Any = None
    error: Optional[str] = None
    timeout_seconds: int = 7200  # Default timeout of 2 hours
    priority: str = "normal"  # Priority: high, normal, low
    health_checks: List[datetime] = field(default_factory=list)  # Timestamps of health checks
    progress_updates: Dict[str, Any] = field(default_factory=dict)  # Progress information
    last_activity: Optional[datetime] = None  # Last recorded activity timestamp

class PhaseTransitionHandler(Protocol):
    """Protocol for handlers that manage transitions between phases"""
    
    async def before_start(self, phase_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Called before a phase starts, can modify input data"""
        ...
        
    async def after_completion(self, phase_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Called after a phase completes, can modify result data"""
        ...
        
    async def on_failure(self, phase_id: str, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Called when a phase fails, can implement recovery or clean-up"""
        ...
        
    async def on_pause(self, phase_id: str, reason: str, context: Dict[str, Any]) -> None:
        """Called when a phase is paused"""
        ...
        
    async def on_resume(self, phase_id: str, context: Dict[str, Any]) -> None:
        """Called when a phase is resumed"""
        ...

class PhaseCoordinator:
    """Manages phase transitions and nested phase execution"""
    
    # Default circuit breaker configs for different phase types
    DEFAULT_CIRCUIT_BREAKER_CONFIGS = {
        "phase_zero": CircuitBreakerConfig(failure_threshold=3, recovery_timeout=60, failure_window=300),
        "phase_one": CircuitBreakerConfig(failure_threshold=3, recovery_timeout=60, failure_window=300),
        "phase_two": CircuitBreakerConfig(failure_threshold=5, recovery_timeout=120, failure_window=600),
        "phase_three": CircuitBreakerConfig(failure_threshold=4, recovery_timeout=90, failure_window=450),
        "phase_four": CircuitBreakerConfig(failure_threshold=3, recovery_timeout=60, failure_window=300),
        "transition": CircuitBreakerConfig(failure_threshold=3, recovery_timeout=60, failure_window=300),
    }
    
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
                 custom_circuit_breaker_configs: Optional[Dict[str, CircuitBreakerConfig]] = None):
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._context_manager = context_manager
        self._cache_manager = cache_manager
        self._metrics_manager = metrics_manager
        self._error_handler = error_handler
        self._memory_monitor = memory_monitor
        self._system_monitor = system_monitor
        self._circuit_breaker_registry = circuit_breaker_registry
        
        # Phase state tracking
        self._phase_states: Dict[str, PhaseContext] = {}
        self._active_phases: Set[str] = set()
        self._phase_hierarchy: Dict[str, Set[str]] = {}  # parent-child relationships
        self._phase_dependencies: Dict[str, Set[str]] = {}
        self._checkpoint_data: Dict[str, Dict[str, Any]] = {}
        self._transition_handlers: Dict[str, List[PhaseTransitionHandler]] = {}
        
        # Nested executions tracking
        self._nested_executions: Dict[str, NestedPhaseExecution] = {}
        
        # Create lock for thread safety
        self._state_lock = asyncio.Lock()
        
        # Load custom circuit breaker configurations if provided
        self._circuit_breaker_configs = dict(self.DEFAULT_CIRCUIT_BREAKER_CONFIGS)
        if custom_circuit_breaker_configs:
            for phase_type, config in custom_circuit_breaker_configs.items():
                if isinstance(config, CircuitBreakerConfig):
                    self._circuit_breaker_configs[phase_type] = config
                    logger.info(f"Using custom circuit breaker config for {phase_type}")
                else:
                    logger.warning(f"Invalid circuit breaker config for {phase_type}")
        
        # Try to load config from state manager if available
        asyncio.create_task(self._load_circuit_breaker_configs())
        
        # Initialize circuit breakers
        self._phase_circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Use circuit breaker registry if provided, otherwise create directly
        if self._circuit_breaker_registry:
            for phase_type in PhaseType:
                cb_id = f"phase_coordinator_{phase_type.value}"
                config = self._circuit_breaker_configs.get(phase_type.value, self._circuit_breaker_configs["phase_one"])
                self._phase_circuit_breakers[phase_type.value] = self._circuit_breaker_registry.get_or_create_circuit_breaker(
                    cb_id, config
                )
                logger.debug(f"Registered circuit breaker {cb_id} with registry")
            
            # Transition circuit breaker
            self._transition_circuit_breaker = self._circuit_breaker_registry.get_or_create_circuit_breaker(
                "phase_transition", 
                self._circuit_breaker_configs["transition"]
            )
        else:
            # Create circuit breakers directly
            for phase_type in PhaseType:
                config = self._circuit_breaker_configs.get(phase_type.value, self._circuit_breaker_configs["phase_one"])
                self._phase_circuit_breakers[phase_type.value] = CircuitBreaker(
                    f"phase_coordinator_{phase_type.value}",
                    event_queue,
                    config
                )
                
            # Transition circuit breaker
            self._transition_circuit_breaker = CircuitBreaker(
                "phase_transition",
                event_queue,
                self._circuit_breaker_configs["transition"]
            )
        
        # Status tracking
        self._running = False
        self._monitoring_task = None
        
        # Register with event loop manager
        EventLoopManager.register_resource(f"phase_coordinator_{id(self)}", self)
        
    async def _load_circuit_breaker_configs(self) -> None:
        """Load circuit breaker configurations from state manager if available"""
        if not self._state_manager:
            return
            
        try:
            # Try to load saved configurations
            config_entry = await self._state_manager.get_state("phase_coordinator:circuit_breaker_configs")
            if config_entry and hasattr(config_entry, 'state') and isinstance(config_entry.state, dict):
                # Parse saved configs back into CircuitBreakerConfig objects
                loaded_configs = {}
                for phase_type, config_dict in config_entry.state.items():
                    try:
                        loaded_configs[phase_type] = CircuitBreakerConfig(
                            failure_threshold=config_dict.get("failure_threshold", 3),
                            recovery_timeout=config_dict.get("recovery_timeout", 60),
                            failure_window=config_dict.get("failure_window", 300)
                        )
                        logger.debug(f"Loaded circuit breaker config for {phase_type} from state manager")
                    except (KeyError, TypeError) as e:
                        logger.warning(f"Error loading circuit breaker config for {phase_type}: {e}")
                
                # Update configs
                if loaded_configs:
                    self._circuit_breaker_configs.update(loaded_configs)
                    logger.info(f"Loaded {len(loaded_configs)} circuit breaker configurations from state manager")
        except Exception as e:
            logger.warning(f"Error loading circuit breaker configurations: {e}")
    
    async def _save_circuit_breaker_configs(self) -> None:
        """Save current circuit breaker configurations to state manager"""
        if not self._state_manager:
            return
            
        try:
            # Convert CircuitBreakerConfig objects to dictionaries
            config_dict = {}
            for phase_type, config in self._circuit_breaker_configs.items():
                if isinstance(config, CircuitBreakerConfig):
                    config_dict[phase_type] = {
                        "failure_threshold": config.failure_threshold,
                        "recovery_timeout": config.recovery_timeout,
                        "failure_window": config.failure_window
                    }
            
            # Save to state manager
            await self._state_manager.set_state(
                "phase_coordinator:circuit_breaker_configs",
                config_dict,
                ResourceType.CONFIGURATION,
                metadata={
                    "updated_at": datetime.now().isoformat(),
                    "component": "phase_coordinator"
                }
            )
            logger.debug("Saved circuit breaker configurations to state manager")
        except Exception as e:
            logger.warning(f"Error saving circuit breaker configurations: {e}")
    
    async def update_circuit_breaker_config(self, phase_type: str, config: CircuitBreakerConfig) -> bool:
        """
        Update circuit breaker configuration for a specific phase type
        
        Args:
            phase_type: The phase type to update configuration for
            config: The new circuit breaker configuration
            
        Returns:
            bool: True if update was successful
        """
        try:
            # Validate phase type
            is_valid = False
            if phase_type == "transition":
                is_valid = True
            else:
                for pt in PhaseType:
                    if pt.value == phase_type:
                        is_valid = True
                        break
            
            if not is_valid:
                logger.warning(f"Invalid phase type for circuit breaker config: {phase_type}")
                return False
            
            # Update config
            self._circuit_breaker_configs[phase_type] = config
            
            # Update actual circuit breaker if it exists
            if phase_type == "transition" and self._transition_circuit_breaker:
                if hasattr(self._transition_circuit_breaker, 'update_config'):
                    self._transition_circuit_breaker.update_config(config)
            elif phase_type in self._phase_circuit_breakers:
                circuit_breaker = self._phase_circuit_breakers[phase_type]
                if hasattr(circuit_breaker, 'update_config'):
                    circuit_breaker.update_config(config)
            
            # Save updated configurations
            await self._save_circuit_breaker_configs()
            
            logger.info(f"Updated circuit breaker configuration for {phase_type}")
            return True
        except Exception as e:
            logger.error(f"Error updating circuit breaker config for {phase_type}: {e}")
            return False
            
    async def start(self):
        """Start the phase coordinator service."""
        if self._running:
            return
            
        self._running = True
        
        # Start monitoring task if needed
        loop = asyncio.get_event_loop()
        self._monitoring_task = loop.create_task(self._monitor_phases())
        
        logger.info("Phase coordinator service started")
    
    async def stop(self):
        """Stop the phase coordinator service."""
        if not self._running:
            return
            
        self._running = False
        
        # Stop monitoring task if it exists
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass
                
        logger.info("Phase coordinator service stopped")
    
    async def _monitor_phases(self):
        """Monitor active phases and handle timeouts or stalls."""
        while self._running:
            try:
                # Check for stalled phases
                stalled_phases = await self._check_for_stalled_phases()
                
                if stalled_phases:
                    for phase_id in stalled_phases:
                        logger.warning(f"Phase {phase_id} appears to be stalled")
                        
                        # Record metric for stalled phase
                        await self._metrics_manager.record_metric(
                            "phase_coordinator:stalled_phase",
                            1.0,
                            metadata={
                                "phase_id": phase_id,
                                "stalled_since": datetime.now().isoformat(),
                                "phase_type": self._phase_states[phase_id].phase_type.value
                                if phase_id in self._phase_states else "unknown"
                            }
                        )
                        
                        # Emit event for monitoring
                        await self._event_queue.emit(
                            ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
                            {
                                "resource_id": f"phase:{phase_id}",
                                "state": "stalled",
                                "timestamp": datetime.now().isoformat()
                            }
                        )
                
                # Record metrics on current phase statistics
                await self._record_phase_metrics()
                
                # Check for orphaned nested executions
                await self._check_orphaned_executions()
                
                # Sleep before next check
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in phase monitoring: {str(e)}")
                await asyncio.sleep(10)  # Shorter sleep on error
                
    async def _record_phase_metrics(self):
        """Record metrics about current phase status for monitoring"""
        try:
            # Count phases by state
            state_counts = {}
            for state in PhaseState:
                state_counts[state.name] = 0
                
            for context in self._phase_states.values():
                state_counts[context.state.name] += 1
                
            # Count phases by type
            type_counts = {}
            for phase_type in PhaseType:
                type_counts[phase_type.value] = 0
                
            for context in self._phase_states.values():
                if isinstance(context.phase_type, PhaseType):
                    type_counts[context.phase_type.value] += 1
                
            # Record metrics for state counts
            for state, count in state_counts.items():
                await self._metrics_manager.record_metric(
                    f"phase_coordinator:phases_by_state:{state}",
                    count,
                    metadata={
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
            # Record metrics for type counts
            for phase_type, count in type_counts.items():
                await self._metrics_manager.record_metric(
                    f"phase_coordinator:phases_by_type:{phase_type}",
                    count,
                    metadata={
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
            # Record active phases count
            await self._metrics_manager.record_metric(
                "phase_coordinator:active_phases",
                len(self._active_phases),
                metadata={
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Record nested executions metrics
            pending_executions = sum(1 for exec in self._nested_executions.values() 
                                   if exec.status == "pending")
            
            await self._metrics_manager.record_metric(
                "phase_coordinator:pending_executions",
                pending_executions,
                metadata={
                    "total_executions": len(self._nested_executions),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error recording phase metrics: {e}")
            # Log but don't re-raise to maintain stability
                
    async def _check_orphaned_executions(self):
        """Check for and clean up orphaned nested executions with progressive monitoring."""
        now = datetime.now()
        orphaned_executions = []
        warning_executions = []
        
        for exec_id, execution in self._nested_executions.items():
            if execution.status != "pending":
                continue
                
            # Record this health check
            execution.health_checks.append(now)
            
            # Calculate the execution time
            execution_time = (now - execution.start_time).total_seconds()
            
            # Get the effective timeout (use default if not set)
            timeout = execution.timeout_seconds if hasattr(execution, 'timeout_seconds') else 7200
            
            # Check if we need to time out this execution
            if execution_time > timeout:
                orphaned_executions.append(exec_id)
                continue
            
            # Progressive monitoring - increase frequency based on elapsed time percentage
            elapsed_percent = (execution_time / timeout) * 100
            
            # Define warning thresholds based on percentage of timeout
            if elapsed_percent > 75:  # >75% of timeout - critical warning
                # Check if there's been activity in the last 15 minutes
                if (not execution.last_activity or 
                    (now - execution.last_activity).total_seconds() > 900):  # 15 minutes
                    warning_executions.append((exec_id, "critical", elapsed_percent))
            elif elapsed_percent > 50:  # >50% of timeout - warning
                # Check if there's been activity in the last 30 minutes
                if (not execution.last_activity or 
                    (now - execution.last_activity).total_seconds() > 1800):  # 30 minutes
                    warning_executions.append((exec_id, "warning", elapsed_percent))
        
        # Handle warnings first
        for exec_id, level, percent in warning_executions:
            execution = self._nested_executions[exec_id]
            
            # Log warning
            if level == "critical":
                logger.warning(f"Execution nearing timeout ({percent:.1f}%): {exec_id} (parent: {execution.parent_id}, child: {execution.child_id})")
            else:
                logger.info(f"Long-running execution ({percent:.1f}%): {exec_id} (parent: {execution.parent_id}, child: {execution.child_id})")
            
            # Emit warning event
            await self._event_queue.emit(
                ResourceEventTypes.RESOURCE_ALERT_CREATED.value,
                {
                    "resource_id": f"nested_execution:{exec_id}",
                    "alert_type": "execution_warning",
                    "severity": level.upper(),
                    "message": f"Execution has been running for {percent:.1f}% of timeout",
                    "parent_phase": execution.parent_id,
                    "child_phase": execution.child_id,
                    "execution_time_seconds": (now - execution.start_time).total_seconds(),
                    "timeout_seconds": execution.timeout_seconds,
                    "timestamp": now.isoformat()
                }
            )
        
        # Clean up orphaned executions
        for exec_id in orphaned_executions:
            execution = self._nested_executions[exec_id]
            logger.warning(f"Cleaning up orphaned nested execution: {exec_id} (parent: {execution.parent_id}, child: {execution.child_id})")
            
            # Generate detailed timeout message with execution history
            timeout_message = (
                f"Execution orphaned - timed out after {execution.timeout_seconds//60} minutes. "
                f"Health checks: {len(execution.health_checks)}, "
                f"Progress updates: {len(execution.progress_updates)}"
            )
            
            # Mark as failed
            execution.status = "failed"
            execution.end_time = now
            execution.error = timeout_message
            
            # Emit detailed error event
            await self._event_queue.emit(
                ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
                {
                    "resource_id": f"nested_execution:{exec_id}",
                    "error": timeout_message,
                    "error_type": "orphaned_execution",
                    "parent_phase": execution.parent_id,
                    "child_phase": execution.child_id,
                    "execution_details": {
                        "start_time": execution.start_time.isoformat(),
                        "end_time": now.isoformat(),
                        "duration_seconds": (now - execution.start_time).total_seconds(),
                        "health_checks": len(execution.health_checks),
                        "progress_updates": execution.progress_updates
                    },
                    "timestamp": now.isoformat()
                },
                priority="high"  # Use high priority for timeout errors
            )
                
    async def _check_for_stalled_phases(self) -> List[str]:
        """Check for phases that appear to be stalled.
        
        Returns:
            List[str]: List of stalled phase IDs
        """
        stalled_phases = []
        now = datetime.now()
        
        for phase_id in self._active_phases:
            context = self._phase_states.get(phase_id)
            if not context or not context.start_time:
                continue
                
            # If phase has been running for more than 1 hour, consider it stalled
            running_time = (now - context.start_time).total_seconds()
            if running_time > 3600:  # 1 hour
                stalled_phases.append(phase_id)
                
        return stalled_phases
    
    async def get_current_phase_info(self) -> Dict[str, Any]:
        """Get information about currently active phases.
        
        Returns:
            Dict[str, Any]: Information about active phases
        """
        active_phases_info = {}
        
        for phase_id in self._active_phases:
            context = self._phase_states.get(phase_id)
            if context:
                active_phases_info[phase_id] = {
                    "phase_type": context.phase_type.value,
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
        
        # Get nested execution stats
        nested_executions = {
            "total": len(self._nested_executions),
            "pending": sum(1 for exec in self._nested_executions.values() if exec.status == "pending"),
            "completed": sum(1 for exec in self._nested_executions.values() if exec.status == "completed"),
            "failed": sum(1 for exec in self._nested_executions.values() if exec.status == "failed")
        }
                
        return {
            "active_phases": active_phases_info,
            "total_active": len(self._active_phases),
            "total_phases": len(self._phase_states),
            "phase_type_counts": phase_type_counts,
            "nested_executions": nested_executions,
            "timestamp": datetime.now().isoformat()
        }
    
    async def rollback_to_checkpoint(self, checkpoint_id: str) -> bool:
        """Roll back to a previously created checkpoint.
        
        Args:
            checkpoint_id: The checkpoint ID to roll back to
            
        Returns:
            bool: True if rollback was successful
        """
        success = await self.restore_from_checkpoint(checkpoint_id)
        
        if success:
            # Emit rollback event
            await self._event_queue.emit(
                ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
                {
                    "resource_id": "phase_coordinator",
                    "state": "rolled_back",
                    "checkpoint_id": checkpoint_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Record metric
            await self._metrics_manager.record_metric(
                "phase_coordinator:rollback",
                1.0,
                metadata={
                    "checkpoint_id": checkpoint_id,
                    "success": True,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        return success
        
    async def initialize_phase(self, phase_id: str, phase_type: Union[PhaseType, str], 
                              phase_config: Dict[str, Any],
                              parent_phase_id: Optional[str] = None,
                              metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize a phase with configuration and parent-child relationship
        
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
            self._register_transition_handlers(phase_id, handler_names)
            
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
            
    def _register_transition_handlers(self, phase_id: str, handler_names: List[str]) -> None:
        """Register transition handlers for a phase
        
        Args:
            phase_id: The phase identifier
            handler_names: List of handler names to register
        """
        if not handler_names:
            return
            
        if phase_id not in self._transition_handlers:
            self._transition_handlers[phase_id] = []
            
        # Dynamically import and register handlers
        from importlib import import_module
        from resources.phase_coordination_integration import PhaseTransitionHandler
        
        for handler_name in handler_names:
            try:
                # Parse module and class name (expected format: module_path.ClassName)
                if '.' in handler_name:
                    module_path, class_name = handler_name.rsplit('.', 1)
                    # Import the module
                    module = import_module(module_path)
                    # Get the handler class
                    handler_class = getattr(module, class_name)
                    # Check if it's a valid transition handler
                    if hasattr(handler_class, '__mro__') and PhaseTransitionHandler in handler_class.__mro__:
                        # Create instance and register
                        handler_instance = handler_class()
                        self._transition_handlers[phase_id].append(handler_instance)
                        logger.info(f"Registered handler {handler_name} for phase {phase_id}")
                    else:
                        logger.warning(f"Handler {handler_name} is not a valid PhaseTransitionHandler")
                else:
                    logger.warning(f"Invalid handler format: {handler_name}, expected module.ClassName")
            except (ImportError, AttributeError, ValueError) as e:
                logger.error(f"Failed to register handler {handler_name}: {str(e)}")
        
    def _get_transition_handlers(self, source_phase: str, target_phase: str) -> List[PhaseTransitionHandler]:
        """Get transition handlers for a phase transition
        
        Args:
            source_phase: Source phase ID
            target_phase: Target phase ID
            
        Returns:
            List of transition handlers
        """
        # Combine source and target phase handlers
        handlers = []
        
        # First source phase handlers
        if source_phase in self._transition_handlers:
            handlers.extend(self._transition_handlers[source_phase])
            
        # Then target phase handlers
        if target_phase in self._transition_handlers and target_phase != source_phase:
            handlers.extend(self._transition_handlers[target_phase])
            
        return handlers
            
    async def start_phase(self, phase_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Start or resume execution of a phase with input data
        
        Args:
            phase_id: The phase identifier
            input_data: Input data for the phase
            
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
            # Get the appropriate circuit breaker
            circuit_breaker = self._phase_circuit_breakers.get(
                context.phase_type.value, 
                self._phase_circuit_breakers[PhaseType.ONE.value]  # Default fallback
            )
            
            # Use circuit breaker to protect phase execution
            try:
                return await circuit_breaker.execute(
                    lambda: self._execute_phase(phase_id, input_data)
                )
            except CircuitOpenError:
                logger.error(f"Circuit breaker open for {context.phase_type.value} phase execution")
                return {
                    "error": f"Circuit breaker open for {context.phase_type.value} phase execution",
                    "status": "circuit_open",
                    "phase_id": phase_id
                }
                
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
            
            # Record error metric
            await self._metrics_manager.record_metric(
                f"phase_coordinator:phase_error:{context.phase_type.value}",
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
        """Internal method to execute a phase with proper tracking."""
        context = self._phase_states.get(phase_id)
        
        # Update phase state to RUNNING
        await self._update_phase_state(phase_id, PhaseState.RUNNING)
        
        # Add to active phases
        self._active_phases.add(phase_id)
        
        # Record start time if not already set
        if not context.start_time:
            context.start_time = datetime.now()
            
        # Record metric for phase start
        await self._metrics_manager.record_metric(
            f"phase_coordinator:phase_start:{context.phase_type.value}",
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
            logger.info(f"Starting execution of phase {phase_id} ({context.phase_type.value})")
            
            # Simulate some work
            await asyncio.sleep(0.1)
            
            # Simulate implementation based on phase type
            result = {
                "status": "success",
                "phase_id": phase_id,
                "phase_type": context.phase_type.value,
                "output": f"Simulated output from {context.phase_type.value} phase {phase_id}",
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
                f"phase_coordinator:phase_complete:{context.phase_type.value}",
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
        """Pause a running phase
        
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
                
        # Record metric for phase pause
        await self._metrics_manager.record_metric(
            f"phase_coordinator:phase_pause:{context.phase_type.value}",
            1.0,
            metadata={
                "phase_id": phase_id,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            }
        )
                
        return True
        
    async def resume_phase(self, phase_id: str) -> bool:
        """Resume a paused phase
        
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
                
        # Record metric for phase resume
        await self._metrics_manager.record_metric(
            f"phase_coordinator:phase_resume:{context.phase_type.value}",
            1.0,
            metadata={
                "phase_id": phase_id,
                "timestamp": datetime.now().isoformat()
            }
        )
                
        return True
        
    async def abort_phase(self, phase_id: str, reason: str) -> bool:
        """Abort a running or paused phase
        
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
        
        # Record metric for phase abort
        await self._metrics_manager.record_metric(
            f"phase_coordinator:phase_abort:{context.phase_type.value}",
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
        """Get the current status of a phase
        
        Args:
            phase_id: The phase identifier
            
        Returns:
            Dict[str, Any]: Phase status information
        """
        context = self._phase_states.get(phase_id)
        if not context:
            return {"error": f"Phase {phase_id} not found", "status": "unknown"}
            
        # Get phase type value (handles both built-in enum and custom string)
        phase_type_value = context.phase_type.value if isinstance(context.phase_type, PhaseType) else context.phase_type
            
        # Get child phase statuses if any
        child_statuses = {}
        for child_id in context.child_phases:
            child_context = self._phase_states.get(child_id)
            if child_context:
                # Handle phase type value for child (either enum or string)
                child_type_value = (child_context.phase_type.value 
                                   if isinstance(child_context.phase_type, PhaseType) 
                                   else child_context.phase_type)
                
                child_statuses[child_id] = {
                    "state": child_context.state.name,
                    "phase_type": child_type_value,
                    "is_custom_type": child_context.is_custom_type,
                    "start_time": child_context.start_time.isoformat() if child_context.start_time else None,
                    "end_time": child_context.end_time.isoformat() if child_context.end_time else None
                }
                
                # Add custom type info if relevant
                if child_context.is_custom_type and isinstance(child_context.phase_type, str):
                    custom_info = _CUSTOM_PHASE_TYPES.get(child_context.phase_type, {})
                    if custom_info:
                        child_statuses[child_id]["custom_type_info"] = {
                            "parent_type": custom_info.get("parent_type"),
                            "description": custom_info.get("description")
                        }
                
        # Calculate progression metrics
        progress_metrics = {}
        if context.start_time:
            # Calculate time running
            if context.state in [PhaseState.RUNNING, PhaseState.PAUSED]:
                time_running = (datetime.now() - context.start_time).total_seconds()
                progress_metrics["time_running_seconds"] = time_running
                
            # For completed phases, calculate execution metrics
            if context.state == PhaseState.COMPLETED and context.end_time:
                execution_time = (context.end_time - context.start_time).total_seconds()
                progress_metrics["execution_time_seconds"] = execution_time
                
                # If checkpoints were created, calculate time between checkpoints
                if context.checkpoint_ids:
                    progress_metrics["checkpoints_count"] = len(context.checkpoint_ids)
                
        # Get nested execution details if any
        nested_executions = {}
        for exec_id, execution in self._nested_executions.items():
            if execution.parent_id == phase_id or execution.child_id == phase_id:
                nested_executions[exec_id] = {
                    "status": execution.status,
                    "parent_id": execution.parent_id,
                    "child_id": execution.child_id,
                    "start_time": execution.start_time.isoformat(),
                    "end_time": execution.end_time.isoformat() if execution.end_time else None,
                    "execution_time": (datetime.now() - execution.start_time).total_seconds()
                }
                
        # Build the base status response
        status_response = {
            "phase_id": phase_id,
            "phase_type": phase_type_value,
            "is_custom_type": context.is_custom_type,
            "state": context.state.name,
            "parent_phase_id": context.parent_phase_id,
            "child_phases": list(context.child_phases),
            "child_statuses": child_statuses,
            "dependencies": list(context.dependencies),
            "start_time": context.start_time.isoformat() if context.start_time else None,
            "end_time": context.end_time.isoformat() if context.end_time else None,
            "execution_time": (context.end_time - context.start_time).total_seconds() if context.start_time and context.end_time else None,
            "error_info": context.error_info,
            "checkpoint_ids": context.checkpoint_ids,
            "metadata": context.metadata,
            "progress_metrics": progress_metrics,
            "nested_executions": nested_executions
        }
        
        # Add custom type info if this is a custom phase type
        if context.is_custom_type and phase_type_value in _CUSTOM_PHASE_TYPES:
            custom_info = _CUSTOM_PHASE_TYPES[phase_type_value]
            status_response["custom_type_info"] = {
                "parent_type": custom_info.get("parent_type"),
                "description": custom_info.get("description"),
                "registered_at": custom_info.get("registered_at"),
                "config": custom_info.get("config", {})
            }
            
            # Add inheritance chain if available
            parent_chain = []
            current_parent = custom_info.get("parent_type")
            while current_parent:
                parent_chain.append(current_parent)
                # Check if parent is a custom type too
                if current_parent in _CUSTOM_PHASE_TYPES:
                    current_parent = _CUSTOM_PHASE_TYPES[current_parent].get("parent_type")
                else:
                    # Built-in parent type
                    break
                    
            if parent_chain:
                status_response["custom_type_info"]["inheritance_chain"] = parent_chain
                
        return status_response
        
    async def create_checkpoint(self, phase_id: str) -> str:
        """Create a checkpoint for the current phase state
        
        Args:
            phase_id: The phase identifier
            
        Returns:
            str: Checkpoint identifier
        """
        context = self._phase_states.get(phase_id)
        if not context:
            logger.error(f"Cannot create checkpoint for unknown phase: {phase_id}")
            raise ValueError(f"Phase {phase_id} not found")
            
        # Generate checkpoint ID
        checkpoint_id = f"checkpoint_{phase_id}_{int(time.time())}"
        
        # Store phase context
        self._checkpoint_data[checkpoint_id] = context.to_dict()
        
        # Add checkpoint to phase context
        context.checkpoint_ids.append(checkpoint_id)
        
        # Persist checkpoint
        await self._state_manager.set_state(
            f"phase_checkpoint:{checkpoint_id}",
            self._checkpoint_data[checkpoint_id],
            ResourceType.STATE
        )
        
        logger.info(f"Created checkpoint {checkpoint_id} for phase {phase_id}")
        
        # Record metric for checkpoint creation
        await self._metrics_manager.record_metric(
            f"phase_coordinator:checkpoint_create:{context.phase_type.value}",
            1.0,
            metadata={
                "phase_id": phase_id,
                "checkpoint_id": checkpoint_id,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return checkpoint_id
        
    async def restore_from_checkpoint(self, checkpoint_id: str) -> bool:
        """Restore a phase from a checkpoint
        
        Args:
            checkpoint_id: The checkpoint identifier
            
        Returns:
            bool: True if restored successfully
        """
        # Check if checkpoint exists in memory
        checkpoint_data = self._checkpoint_data.get(checkpoint_id)
        
        # If not in memory, try to load from state manager
        if not checkpoint_data:
            checkpoint_entry = await self._state_manager.get_state(f"phase_checkpoint:{checkpoint_id}")
            if not checkpoint_entry:
                logger.error(f"Checkpoint {checkpoint_id} not found")
                return False
                
            checkpoint_data = checkpoint_entry.state
            
        # Restore phase context
        phase_id = checkpoint_data["phase_id"]
        context = PhaseContext.from_dict(checkpoint_data)
        
        # Update phase state
        self._phase_states[phase_id] = context
        
        # Update other state tracking
        if context.parent_phase_id:
            if context.parent_phase_id not in self._phase_hierarchy:
                self._phase_hierarchy[context.parent_phase_id] = set()
            self._phase_hierarchy[context.parent_phase_id].add(phase_id)
            
        if context.dependencies:
            self._phase_dependencies[phase_id] = context.dependencies
            
        # Record metric for checkpoint restoration
        await self._metrics_manager.record_metric(
            f"phase_coordinator:checkpoint_restore:{context.phase_type.value}",
            1.0,
            metadata={
                "phase_id": phase_id,
                "checkpoint_id": checkpoint_id,
                "timestamp": datetime.now().isoformat()
            }
        )
            
        # Emit restore event
        await self._event_queue.emit(
            ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
            {
                "resource_id": f"phase:{phase_id}",
                "state": "restored",
                "checkpoint_id": checkpoint_id,
                "restored_state": context.state.name
            }
        )
        
        logger.info(f"Restored phase {phase_id} from checkpoint {checkpoint_id}")
        
        return True
        
    async def coordinate_nested_execution(self, parent_phase_id: str, 
                                         child_phase_id: str, 
                                         input_data: Dict[str, Any],
                                         timeout_seconds: Optional[int] = None,
                                         priority: str = "normal",
                                         execution_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Coordinate execution of a child phase from a parent phase with configurable execution parameters
        
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
        # Validate and normalize priority
        if priority not in ["high", "normal", "low"]:
            priority = "normal"
            logger.warning(f"Invalid priority '{priority}' specified, using 'normal'")
        
        # Use circuit breaker to protect the transition process
        try:
            return await self._transition_circuit_breaker.execute(
                lambda: self._coordinate_nested_execution_internal(
                    parent_phase_id, 
                    child_phase_id, 
                    input_data,
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
                                                  timeout_seconds: Optional[int] = None,
                                                  priority: str = "normal",
                                                  execution_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Internal implementation of nested execution coordination with enhanced execution tracking."""
        # Validate parent-child relationship
        if child_phase_id not in self._phase_hierarchy.get(parent_phase_id, set()):
            raise ValueError(f"Phase {child_phase_id} is not a child of {parent_phase_id}")
        
        # Create execution context
        execution_id = f"{parent_phase_id}_to_{child_phase_id}_{int(time.time())}"
        
        # Determine timeout based on phase type
        if timeout_seconds is None:
            # Set default timeout based on phase type
            child_context = self._phase_states.get(child_phase_id)
            if child_context:
                phase_type = child_context.phase_type.value
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
        
        # Get parent and child phase contexts
        parent_context = self._phase_states.get(parent_phase_id)
        child_context = self._phase_states.get(child_phase_id)
        
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
        
        # Prepare input data with parent context
        enhanced_input = {
            **input_data,
            "parent_context": {
                "phase_id": parent_phase_id,
                "phase_type": parent_context.phase_type.value,
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
                "parent_phase_type": parent_context.phase_type.value,
                "child_phase_id": child_phase_id,
                "child_phase_type": child_context.phase_type.value,
                "execution_id": execution_id,
                "priority": priority,
                "timeout_seconds": timeout_seconds,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Execute handlers for transition
        handlers = self._get_transition_handlers(parent_phase_id, child_phase_id)
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
            child_result = await self.start_phase(child_phase_id, enhanced_input)
            
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
            
    async def _update_phase_state(self, phase_id: str, state: PhaseState, 
                                 metadata: Optional[Dict[str, Any]] = None) -> None:
        """Update phase state in state manager
        
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
        phase_type_value = context.phase_type.value if isinstance(context.phase_type, PhaseType) else context.phase_type
        
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
        if context.is_custom_type and phase_type_value in _CUSTOM_PHASE_TYPES:
            state_data["custom_type_info"] = {
                "parent_type": _CUSTOM_PHASE_TYPES[phase_type_value].get("parent_type"),
                "description": _CUSTOM_PHASE_TYPES[phase_type_value].get("description")
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
        
        # Emit event for monitoring
        health_event_data = {
            "component": f"phase_{phase_id}",
            "status": "HEALTHY" if state in (PhaseState.RUNNING, PhaseState.COMPLETED) else "DEGRADED",
            "description": f"Phase {phase_id} state changed to {state.name}",
            "metadata": {
                "phase_id": phase_id,
                "phase_type": phase_type_value,
                "state": state.name,
                "parent_phase_id": context.parent_phase_id,
                "is_custom_type": context.is_custom_type,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Add custom type details if relevant
        if context.is_custom_type and isinstance(context.phase_type, str):
            custom_info = _CUSTOM_PHASE_TYPES.get(context.phase_type, {})
            if custom_info:
                health_event_data["metadata"]["custom_type_info"] = {
                    "parent_type": custom_info.get("parent_type"),
                    "description": custom_info.get("description")
                }
                
        await self._event_queue.emit(
            ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value,
            health_event_data
        )
        
        # Also emit specific state change event
        state_change_event = {
            "resource_id": f"phase:{phase_id}",
            "old_state": previous_state.name if previous_state else None,
            "new_state": state.name,
            "phase_id": phase_id,
            "phase_type": phase_type_value,
            "is_custom_type": context.is_custom_type,
            "timestamp": datetime.now().isoformat()
        }
        
        await self._event_queue.emit(
            ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
            state_change_event
        )
        
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
            
        # Create circuit breaker for the new phase type
        if not self._circuit_breaker_registry:
            # Create directly
            self._phase_circuit_breakers[phase_type] = CircuitBreaker(
                f"phase_coordinator_{phase_type}",
                self._event_queue,
                self._circuit_breaker_configs.get(phase_type, self._circuit_breaker_configs["phase_one"])
            )
        else:
            # Use registry
            cb_id = f"phase_coordinator_{phase_type}"
            config = self._circuit_breaker_configs.get(phase_type, self._circuit_breaker_configs["phase_one"])
            self._phase_circuit_breakers[phase_type] = self._circuit_breaker_registry.get_or_create_circuit_breaker(
                cb_id, config
            )
            
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
        for phase_id, context in self._phase_states.items():
            if context.phase_type.value == phase_type:
                logger.error(f"Cannot unregister phase type {phase_type} - in use by phase {phase_id}")
                return False
                
        # Remove from registry
        phase_info = _CUSTOM_PHASE_TYPES.pop(phase_type)
        
        # Clean up circuit breaker if it exists
        if phase_type in self._phase_circuit_breakers:
            # Just remove reference, actual cleanup handled by the registry
            del self._phase_circuit_breakers[phase_type]
            
        # Log unregistration
        logger.info(f"Unregistered custom phase type: {phase_type}")
        
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
        
        return True
    
    async def get_registered_phase_types(self) -> Dict[str, Any]:
        """Get information about all registered phase types (built-in and custom)"""
        # Combine built-in and custom types
        phase_types = {}
        
        # Add built-in types
        for phase_type in PhaseType:
            # Get circuit breaker configuration if available
            circuit_breaker_config = self._circuit_breaker_configs.get(phase_type.value)
            cb_config_dict = None
            if circuit_breaker_config:
                cb_config_dict = {
                    "failure_threshold": circuit_breaker_config.failure_threshold,
                    "recovery_timeout": circuit_breaker_config.recovery_timeout,
                    "failure_window": circuit_breaker_config.failure_window
                }
                
            # Count active phases of this type
            active_count = sum(
                1 for ctx in self._phase_states.values()
                if isinstance(ctx.phase_type, PhaseType) and ctx.phase_type == phase_type
            )
            
            phase_types[phase_type.value] = {
                "name": phase_type.name,
                "value": phase_type.value,
                "type": "built-in",
                "description": f"Built-in {phase_type.name.lower()} phase type",
                "circuit_breaker_config": cb_config_dict,
                "active_phases": active_count,
                "circuit_open": (
                    self._phase_circuit_breakers.get(phase_type.value) and 
                    self._phase_circuit_breakers[phase_type.value].is_open()
                )
            }
            
        # Add custom types with extended information
        for phase_type, info in _CUSTOM_PHASE_TYPES.items():
            # Get circuit breaker configuration
            circuit_breaker_config = self._circuit_breaker_configs.get(phase_type)
            cb_config_dict = None
            if circuit_breaker_config:
                cb_config_dict = {
                    "failure_threshold": circuit_breaker_config.failure_threshold,
                    "recovery_timeout": circuit_breaker_config.recovery_timeout,
                    "failure_window": circuit_breaker_config.failure_window
                }
                
            # Count active phases of this type
            active_count = sum(
                1 for ctx in self._phase_states.values()
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
                "circuit_open": (
                    self._phase_circuit_breakers.get(phase_type) and 
                    self._phase_circuit_breakers[phase_type].is_open()
                ),
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
        
    def is_valid_phase_type(self, phase_type: Union[str, PhaseType]) -> bool:
        """
        Check if a given phase type is valid (built-in or custom)
        
        Args:
            phase_type: The phase type to check (string or enum)
            
        Returns:
            bool: True if valid phase type
        """
        if isinstance(phase_type, PhaseType):
            return True
            
        if isinstance(phase_type, str):
            # Check built-in types
            if PhaseType.from_string(phase_type) is not None:
                return True
                
            # Check custom types
            if phase_type in _CUSTOM_PHASE_TYPES:
                return True
                
        return False
    
    async def get_phase_health(self) -> Dict[str, Any]:
        """Get health status of all phases.
        
        Returns:
            Dict[str, Any]: Health status information
        """
        # Count phases by state
        state_counts = {}
        for state in PhaseState:
            state_counts[state.name] = 0
            
        for context in self._phase_states.values():
            state_counts[context.state.name] += 1
            
        # Count phases by type
        type_counts = {}
        for phase_type in PhaseType:
            type_counts[phase_type.value] = 0
            
        for context in self._phase_states.values():
            type_counts[context.phase_type.value] += 1
            
        # Calculate health status
        health_status = "HEALTHY"
        health_details = []
        
        # Check for failed phases
        if state_counts[PhaseState.FAILED.name] > 0:
            health_status = "CRITICAL"
            health_details.append(f"{state_counts[PhaseState.FAILED.name]} phases in FAILED state")
            
        # Check for aborted phases
        if state_counts[PhaseState.ABORTED.name] > 0:
            if health_status != "CRITICAL":
                health_status = "DEGRADED"
            health_details.append(f"{state_counts[PhaseState.ABORTED.name]} phases in ABORTED state")
            
        # Check for stalled phases
        stalled_phases = await self._check_for_stalled_phases()
        if stalled_phases:
            if health_status == "HEALTHY":
                health_status = "WARNING"
            health_details.append(f"{len(stalled_phases)} phases appear to be stalled")
        
        # Check circuit breakers
        open_circuits = []
        for phase_type, circuit in self._phase_circuit_breakers.items():
            if circuit.is_open():
                open_circuits.append(phase_type)
                
        if open_circuits:
            if health_status == "HEALTHY":
                health_status = "WARNING"
            health_details.append(f"Circuit breakers open for phases: {', '.join(open_circuits)}")
            
        # Check transition circuit breaker
        if self._transition_circuit_breaker.is_open():
            if health_status == "HEALTHY":
                health_status = "WARNING"
            health_details.append("Transition circuit breaker is open")
            
        return {
            "status": health_status,
            "description": "; ".join(health_details) if health_details else "All phases healthy",
            "state_counts": state_counts,
            "type_counts": type_counts,
            "active_phases": len(self._active_phases),
            "stalled_phases": len(stalled_phases),
            "open_circuits": open_circuits,
            "transition_circuit_open": self._transition_circuit_breaker.is_open(),
            "timestamp": datetime.now().isoformat()
        }