import asyncio
import contextlib
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union

from resources.base import BaseManager, CleanupPolicy
from resources.common import ResourceState, InterfaceState, ResourceType, HealthStatus
from resources.events import EventQueue, ResourceEventTypes
from resources.state.backends.base import StateStorageBackend
from resources.state.backends.file import FileStateBackend
from resources.state.backends.memory import MemoryStateBackend
from resources.state.backends.sqlite import SQLiteStateBackend
from resources.state.models import StateEntry, StateSnapshot, StateManagerConfig
from resources.state.validators import StateTransitionValidator

logger = logging.getLogger(__name__)


class StateManager(BaseManager):
    """Manages state transitions and persistence with pluggable backends"""
    
    _instance = None
    _init_count = 0

    def __new__(cls, 
                event_queue: EventQueue,
                config: Optional[StateManagerConfig] = None):
        """Implement singleton pattern to prevent multiple instances"""
        if cls._instance is None:
            cls._instance = super(StateManager, cls).__new__(cls)
            cls._instance._is_initialized = False
        return cls._instance

    def __init__(self, 
                 event_queue: EventQueue,
                 config: Optional[StateManagerConfig] = None):
        """Initialize the state manager with the given configuration"""
        # Increment initialization counter for debugging
        StateManager._init_count += 1
        init_count = StateManager._init_count
        
        # Only initialize once
        if hasattr(self, '_is_initialized') and self._is_initialized:
            logger.warning(f"StateManager already initialized, skipping (init attempt #{init_count})")
            return
            
        logger.info(f"Initializing StateManager (attempt #{init_count})")
        self._is_initialized = True
        
        config = config or StateManagerConfig()
        
        super().__init__(
            event_queue=event_queue,
            cleanup_config=config.cleanup_config,
        )
        
        self._config = config
        
        # Initialize the appropriate storage backend based on configuration
        if config.persistence_type == "file" and config.storage_dir:
            self._backend = FileStateBackend(config.storage_dir)
            logger.info(f"Using file-based persistence at {config.storage_dir}")
            
        elif config.persistence_type == "sqlite" and config.db_path:
            self._backend = SQLiteStateBackend(config.db_path)
            logger.info(f"Using SQLite persistence at {config.db_path}")
            
        elif config.persistence_type == "custom" and config.custom_backend:
            self._backend = config.custom_backend
            logger.info(f"Using custom persistence backend: {type(config.custom_backend).__name__}")
            
        else:
            self._backend = MemoryStateBackend()
            logger.info("Using in-memory persistence (no persistence between restarts)")
        
        # LRU cache for frequently accessed state to reduce backend access
        self._states_cache: Dict[str, StateEntry] = {}
        self._cache_keys: List[str] = []  # For LRU tracking
        
        # State validator
        self._validator = StateTransitionValidator()
        
        # Resource-level locks for concurrency control
        self._resource_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._global_lock: asyncio.Lock = asyncio.Lock()
        
        # Metrics if enabled
        if config.enable_metrics:
            self._metrics = {
                "set_state_count": 0,
                "get_state_count": 0,
                "get_history_count": 0,
                "cache_hits": 0,
                "cache_misses": 0,
                "transition_failures": 0,
                "backend_errors": 0,
                "resource_count": 0
            }
        else:
            self._metrics = None
            
        # Initialize but don't start cleanup task yet
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_running = False
        
        # Start the cleanup task if cleanup config is provided
        if config.cleanup_config:
            self._start_cleanup_task()
        
        # Flag to track initialization status
        self._initialization_complete = False
        self._init_lock = asyncio.Lock()
        
        # We no longer create a task here:
        # asyncio.create_task(self._initialize())
        # Instead, we'll initialize on first use
    
    async def ensure_initialized(self):
        """Ensure the state manager is fully initialized before use."""
        if self._initialization_complete:
            return
            
        async with self._init_lock:
            if not self._initialization_complete:
                await self._initialize()
                self._initialization_complete = True
                
    async def _initialize(self):
        """Initialize the state manager by loading state from storage"""
        try:
            resource_ids = await self._backend.get_all_resource_ids()
            logger.info(f"Loading {len(resource_ids)} resources from persistence")
            
            # Limit to cache size
            to_load = resource_ids[:self._config.cache_size]
            
            for resource_id in to_load:
                state_entry = await self._backend.load_state(resource_id)
                if state_entry:
                    self._update_cache(resource_id, state_entry)
            
            if self._metrics:
                self._metrics["resource_count"] = len(resource_ids)
                
            logger.info(f"State manager initialized with {len(self._states_cache)} resources in cache")
            
            # Attempt repair if configured
            if self._config.auto_repair and hasattr(self._backend, 'repair_corrupt_files'):
                try:
                    repair_results = await self._backend.repair_corrupt_files()
                    logger.info(f"Auto-repair completed: {repair_results}")
                except Exception as e:
                    logger.error(f"Auto-repair failed: {e}")
                    
        except Exception as e:
            logger.error(f"Error initializing state manager: {e}")
    
    @classmethod
    async def create(cls, event_queue, config=None):
        """Factory method for creating and initializing a StateManager."""
        instance = cls(event_queue, config)
        await instance.ensure_initialized()
        return instance
    
    @contextlib.asynccontextmanager
    async def _resource_lock(self, resource_id: str):
        """Acquire a resource-specific lock to prevent race conditions."""
        async with self._global_lock:
            # Ensure the lock exists under global lock
            if resource_id not in self._resource_locks:
                self._resource_locks[resource_id] = asyncio.Lock()
        
        # Then acquire the resource-specific lock
        lock = self._resource_locks[resource_id]
        try:
            async with lock:
                yield
        except Exception as e:
            logger.error(f"Error while holding resource lock for {resource_id}: {e}")
            raise
    
    def _update_cache(self, resource_id: str, state_entry: StateEntry):
        """Update the LRU cache with a state entry"""
        # Remove existing key if present
        if resource_id in self._cache_keys:
            self._cache_keys.remove(resource_id)
            
        # Add to cache
        self._states_cache[resource_id] = state_entry
        self._cache_keys.append(resource_id)
        
        # Enforce cache size limit
        while len(self._cache_keys) > self._config.cache_size:
            oldest_key = self._cache_keys.pop(0)
            if oldest_key in self._states_cache:
                del self._states_cache[oldest_key]
    
    async def set_state(self,
                        resource_id: str,
                        state: Union[ResourceState, InterfaceState, Dict[str, Any]],
                        resource_type: ResourceType,
                        metadata: Optional[Dict[str, Any]] = None,
                        transition_reason: Optional[str] = None,
                        failure_info: Optional[Dict[str, Any]] = None) -> StateEntry:
        """Set state with validation and persistence"""
        if self._metrics:
            self._metrics["set_state_count"] += 1
            
        async with self._resource_lock(resource_id):
            # Get current state (trying cache first)
            current = self._states_cache.get(resource_id)
            if not current:
                try:
                    current = await self._backend.load_state(resource_id)
                except Exception as e:
                    logger.error(f"Error loading state from backend for {resource_id}: {e}")
                    if self._metrics:
                        self._metrics["backend_errors"] += 1
            
            # Check if state is actually changing
            is_new_resource = current is None
            state_changed = is_new_resource or (current and current.state != state)

            # Validate transition if applicable
            if (current and isinstance(state, (ResourceState, InterfaceState)) and 
                isinstance(current.state, (ResourceState, InterfaceState))):
                if not self._validator.validate_transition(current.state, state):
                    error_msg = f"Invalid state transition: {current.state} -> {state}"
                    logger.warning(f"{error_msg} for resource {resource_id}")
                    if self._metrics:
                        self._metrics["transition_failures"] += 1
                    raise ValueError(error_msg)
            
            # Create new state entry
            entry = StateEntry(
                state=state,
                resource_type=resource_type,
                metadata=metadata or {},
                previous_state=str(current.state) if current else None,
                transition_reason=transition_reason,
                failure_info=failure_info
            )
            
            # Update cache
            self._update_cache(resource_id, entry)
            
            # Persist state to backend
            try:
                success = await self._backend.save_state(resource_id, entry)
                if not success:
                    logger.error(f"Failed to persist state for {resource_id}")
                    if self._metrics:
                        self._metrics["backend_errors"] += 1
            except Exception as e:
                logger.error(f"Error persisting state for {resource_id}: {e}")
                if self._metrics:
                    self._metrics["backend_errors"] += 1
            
            # Create periodic snapshot if needed
            try:
                history = await self._backend.load_history(resource_id)
                if len(history) % 10 == 0:  # Every 10 transitions
                    await self._create_snapshot(resource_id, entry)
            except Exception as e:
                logger.error(f"Error creating snapshot for {resource_id}: {e}")
            
            # Only emit event if state actually changed
            if state_changed:
                try:
                    # Emit state change event
                    await self._event_queue.emit(
                        "resource_state_changed",
                        {
                            "resource_id": resource_id,
                            "state": str(state),
                            "resource_type": resource_type.name,
                            "metadata": metadata,
                            "transition_reason": transition_reason,
                            "failure_info": failure_info
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to emit state change event: {e}")
            
            return entry

    async def get_state(self, 
                        resource_id: str,
                        version: Optional[int] = None,
                        use_cache: bool = True) -> Optional[StateEntry]:
        """
        Get current state or specific version.
        
        Args:
            resource_id: The ID of the resource
            version: If provided, get a specific version from history
            use_cache: Whether to use the cache (set to False to force backend lookup)
        """
        if self._metrics:
            self._metrics["get_state_count"] += 1
            
        if version is not None:
            # Need to load history for specific version (never cached)
            try:
                history = await self._backend.load_history(resource_id)
                return next((entry for entry in history if entry.version == version), None)
            except Exception as e:
                logger.error(f"Error loading history for {resource_id}: {e}")
                if self._metrics:
                    self._metrics["backend_errors"] += 1
                return None
        
        # Try cache first if enabled
        if use_cache and resource_id in self._states_cache:
            if self._metrics:
                self._metrics["cache_hits"] += 1
            return self._states_cache[resource_id]
        
        # Load from backend
        try:
            if self._metrics:
                self._metrics["cache_misses"] += 1
                
            state = await self._backend.load_state(resource_id)
            if state and use_cache:
                self._update_cache(resource_id, state)
            return state
        except Exception as e:
            logger.error(f"Error loading state for {resource_id} from backend: {e}")
            if self._metrics:
                self._metrics["backend_errors"] += 1
            return None

    async def get_history(self,
                         resource_id: str,
                         limit: Optional[int] = None) -> List[StateEntry]:
        """Get state transition history"""
        if self._metrics:
            self._metrics["get_history_count"] += 1
            
        try:
            return await self._backend.load_history(resource_id, limit)
        except Exception as e:
            logger.error(f"Error loading history for {resource_id}: {e}")
            if self._metrics:
                self._metrics["backend_errors"] += 1
            return []

    async def _create_snapshot(self, resource_id: str, state_entry: Optional[StateEntry] = None) -> None:
        """Create a point-in-time snapshot of state"""
        if not state_entry:
            state_entry = await self.get_state(resource_id)
            
        if not state_entry:
            return
            
        snapshot = StateSnapshot(
            state={"state": state_entry.state, "metadata": state_entry.metadata},
            resource_type=state_entry.resource_type,
            metadata={"snapshot_reason": "periodic"}
        )
        
        try:
            await self._backend.save_snapshot(resource_id, snapshot)
            logger.debug(f"Created snapshot for {resource_id}")
        except Exception as e:
            logger.error(f"Error creating snapshot for {resource_id}: {e}")
            if self._metrics:
                self._metrics["backend_errors"] += 1

    async def recover_from_snapshot(self, 
                                   resource_id: str,
                                   snapshot_index: int = -1) -> Optional[StateEntry]:
        """Recover state from a snapshot"""
        try:
            snapshots = await self._backend.load_snapshots(resource_id)
            if not snapshots:
                logger.warning(f"No snapshots found for {resource_id}")
                return None
                
            try:
                snapshot = snapshots[snapshot_index]
                state_data = snapshot.state.get("state")
                metadata = snapshot.state.get("metadata", {})
                
                return await self.set_state(
                    resource_id=resource_id,
                    state=state_data,
                    resource_type=snapshot.resource_type,
                    metadata=metadata,
                    transition_reason="recovered_from_snapshot"
                )
            except IndexError:
                logger.error(f"Snapshot index {snapshot_index} out of range for {resource_id}")
                return None
        except Exception as e:
            logger.error(f"Error recovering from snapshot: {e}")
            if self._metrics:
                self._metrics["backend_errors"] += 1
            return None
    
    def _start_cleanup_task(self, immediate_for_testing=False):
        """Start the background cleanup task based on cleanup configuration."""
        if self._cleanup_task is not None:
            logger.warning("Cleanup task already running, not starting another one")
            return
            
        if not self._cleanup_config:
            logger.warning("No cleanup configuration provided, cleanup task not started")
            return
            
        self._cleanup_running = True
        
        asyncio.create_task(self.start_cleanup_task_safe(immediate_for_testing))
        
    async def start_cleanup_task_safe(self, immediate_for_testing=False):
        """Safely start the cleanup task, handling the case where no event loop is running."""
        if not self._cleanup_running or self._cleanup_task is not None:
            return
            
        try:
            # Check if there's a running event loop
            loop = asyncio.get_running_loop()
            
            async def _cleanup_loop():
                try:
                    # If immediate_for_testing is True, run cleanup once and exit
                    if immediate_for_testing:
                        try:
                            cleanup_results = await self.cleanup()
                            logger.info(f"Immediate cleanup completed: {cleanup_results}")
                        except Exception as e:
                            logger.error(f"Error during immediate cleanup: {e}")
                        return  # Exit after immediate cleanup
                    
                    # Regular cleanup loop
                    while self._cleanup_running:
                        try:
                            cleanup_results = await self.cleanup()
                            logger.info(f"Cleanup completed: {cleanup_results}")
                        except Exception as e:
                            logger.error(f"Error during cleanup: {e}")
                        
                        # Sleep interval based on cleanup policy
                        if self._cleanup_config.policy == CleanupPolicy.AGGRESSIVE:
                            await asyncio.sleep(60)  # Every minute
                        elif self._cleanup_config.policy == CleanupPolicy.TTL:
                            await asyncio.sleep(300)  # Every 5 minutes
                        else:
                            await asyncio.sleep(3600)  # Default: every hour
                except asyncio.CancelledError:
                    logger.info("Cleanup task was cancelled")
                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")
                    
            # Create task only when we have a running loop
            self._cleanup_task = asyncio.create_task(_cleanup_loop())
            logger.info(f"Started state cleanup task with policy: {self._cleanup_config.policy.name}")
        except RuntimeError:
            # No running event loop, log a message but don't fail
            logger.info("No running event loop available, cleanup task will start when event loop is available")

    async def stop_cleanup_task(self):
        """Stop the background cleanup task."""
        self._cleanup_running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Stopped state cleanup task")
    
    async def _cleanup_resources(self, force: bool = False) -> None:
        """
        Implement specific state manager cleanup logic.
        
        Args:
            force: If True, perform aggressive cleanup regardless of interval/policy
        """
        if not self._cleanup_config:
            logger.debug("No cleanup config, skipping cleanup")
            return
            
        try:
            # Determine cutoff time - more aggressive if force=True
            if force:
                # Use half the normal TTL for forced cleanup
                cutoff_seconds = self._cleanup_config.ttl_seconds // 2 if self._cleanup_config.ttl_seconds else 86400
            else:
                cutoff_seconds = self._cleanup_config.ttl_seconds if self._cleanup_config.ttl_seconds else 86400
                
            older_than = datetime.now() - timedelta(seconds=cutoff_seconds)
            
            # Use backend's cleanup method
            items_removed = await self._backend.cleanup(older_than)
            
            # Update resource count metric
            if self._metrics:
                resource_ids = await self._backend.get_all_resource_ids()
                self._metrics["resource_count"] = len(resource_ids)
            
            # Log cleanup results
            logger.info(f"State manager cleanup: removed {items_removed} items, force={force}")
            
            # Emit cleanup metrics
            await self._event_queue.emit(
                ResourceEventTypes.METRIC_RECORDED.value,
                {
                    "metric": "state_cleanup",
                    "value": float(items_removed),
                    "forced": force,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error during state manager cleanup: {e}")
            
            # Emit error event for monitoring
            await self._event_queue.emit(
                ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
                {
                    "component_id": "state_manager",
                    "operation": "cleanup",
                    "error_type": "cleanup_error",
                    "severity": "DEGRADED",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                },
                priority="high"
            )
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get metrics about state manager operations"""
        if not self._metrics:
            return {"metrics_disabled": True}
            
        # Add backend-specific metrics if available
        metrics = dict(self._metrics)
        
        try:
            if hasattr(self._backend, 'get_database_stats'):
                db_stats = await self._backend.get_database_stats()
                metrics.update(db_stats)
        except Exception as e:
            logger.error(f"Error getting backend stats: {e}")
            
        # Add cache stats
        metrics["cache_size"] = len(self._states_cache)
        metrics["cache_capacity"] = self._config.cache_size
        
        return metrics
    
    async def compact_storage(self) -> Dict[str, Any]:
        """
        Perform storage compaction operations specific to the backend.
        This can be an expensive operation and should be run during maintenance windows.
        """
        results = {}
        
        try:
            # File backend specific compaction
            if isinstance(self._backend, FileStateBackend):
                # Compact history files
                resource_ids = await self._backend.get_all_resource_ids()
                for resource_id in resource_ids:
                    if hasattr(self._backend, 'compact_history'):
                        success = await self._backend.compact_history(resource_id)
                        if success:
                            results[f"compacted_{resource_id}"] = True
            
            # SQLite backend optimization
            elif isinstance(self._backend, SQLiteStateBackend):
                if hasattr(self._backend, 'optimize_database'):
                    success = await self._backend.optimize_database()
                    results["database_optimized"] = success
        except Exception as e:
            logger.error(f"Error during storage compaction: {e}")
            results["error"] = str(e)
            
        return results
    
    async def mark_as_failed(self, 
                           resource_id: str, 
                           reason: str, 
                           error_info: Optional[Dict[str, Any]] = None) -> Optional[StateEntry]:
        """
        Utility method to mark a resource as failed with proper error handling.
        """
        try:
            # Get current state
            current = await self.get_state(resource_id)
            if not current:
                logger.warning(f"Cannot mark non-existent resource {resource_id} as failed")
                return None
            
            # Only resources can be marked as failed
            if not isinstance(current.state, ResourceState):
                logger.warning(f"Cannot mark non-resource state {resource_id} as failed")
                return None
                
            # Check if transition is valid
            if not self._validator.validate_transition(current.state, ResourceState.FAILED):
                logger.warning(f"Cannot transition {resource_id} from {current.state} to FAILED")
                return None
                
            # Create error info
            failure_info = {
                "timestamp": datetime.now().isoformat(),
                "reason": reason,
                **(error_info or {})
            }
            
            # Set failed state
            return await self.set_state(
                resource_id=resource_id,
                state=ResourceState.FAILED,
                resource_type=current.resource_type,
                metadata=current.metadata,
                transition_reason=reason,
                failure_info=failure_info
            )
        except Exception as e:
            logger.error(f"Error marking resource {resource_id} as failed: {e}")
            return None

    async def mark_as_recovered(self, 
                              resource_id: str, 
                              reason: str) -> Optional[StateEntry]:
        """
        Utility method to mark a failed resource as recovered.
        """
        try:
            # Get current state
            current = await self.get_state(resource_id)
            if not current:
                logger.warning(f"Cannot mark non-existent resource {resource_id} as recovered")
                return None
            
            # Only resources can be recovered
            if not isinstance(current.state, ResourceState):
                logger.warning(f"Cannot mark non-resource state {resource_id} as recovered")
                return None
                
            # Check if transition is valid
            if current.state != ResourceState.FAILED:
                logger.warning(f"Cannot recover resource {resource_id} that is not in FAILED state")
                return None
                
            # Set recovered state
            return await self.set_state(
                resource_id=resource_id,
                state=ResourceState.RECOVERED,
                resource_type=current.resource_type,
                metadata=current.metadata,
                transition_reason=reason
            )
        except Exception as e:
            logger.error(f"Error marking resource {resource_id} as recovered: {e}")
            return None

    async def count_resources_by_state(self) -> Dict[str, int]:
        """
        Count resources by their current state.
        Returns a dictionary mapping state names to counts.
        """
        result = defaultdict(int)
        
        try:
            # Get all resource IDs
            resource_ids = await self._backend.get_all_resource_ids()
            
            # Count by state
            for resource_id in resource_ids:
                state_entry = await self.get_state(resource_id)
                if state_entry:
                    state_name = str(state_entry.state)
                    result[state_name] += 1
                    
            return dict(result)
        except Exception as e:
            logger.error(f"Error counting resources by state: {e}")
            return dict(result)

    async def get_resources_by_state(self, 
                                   state: Union[ResourceState, InterfaceState, str]) -> List[str]:
        """
        Get IDs of all resources in the specified state.
        """
        result = []
        state_str = str(state)
        
        try:
            # Get all resource IDs
            resource_ids = await self._backend.get_all_resource_ids()
            
            # Filter by state
            for resource_id in resource_ids:
                state_entry = await self.get_state(resource_id)
                if state_entry and str(state_entry.state) == state_str:
                    result.append(resource_id)
                    
            return result
        except Exception as e:
            logger.error(f"Error getting resources by state {state}: {e}")
            return result

    async def terminate_resource(self, 
                               resource_id: str, 
                               reason: str) -> Optional[StateEntry]:
        """
        Utility method to terminate a resource with proper cleanup.
        """
        try:
            # Get current state
            current = await self.get_state(resource_id)
            if not current:
                logger.warning(f"Cannot terminate non-existent resource {resource_id}")
                return None
            
            # Only resources can be terminated
            if not isinstance(current.state, ResourceState):
                logger.warning(f"Cannot terminate non-resource state {resource_id}")
                return None
                
            # If already terminated, just return current state
            if current.state == ResourceState.TERMINATED:
                return current
                
            # Set terminated state
            entry = await self.set_state(
                resource_id=resource_id,
                state=ResourceState.TERMINATED,
                resource_type=current.resource_type,
                metadata=current.metadata,
                transition_reason=reason
            )
            
            # Create a final snapshot
            await self._create_snapshot(resource_id, entry)
            
            return entry
        except Exception as e:
            logger.error(f"Error terminating resource {resource_id}: {e}")
            return None
            
    async def get_health_status(self) -> HealthStatus:
        """Get health status of state management"""
        try:
            status = "HEALTHY"
            description = "State manager operating normally"
            metadata = {}
            
            # Get metrics if available
            if self._metrics:
                resource_count = self._metrics.get("resource_count", 0)
                backend_errors = self._metrics.get("backend_errors", 0)
                metadata.update(self._metrics)
            else:
                # Count resources directly
                resource_ids = await self._backend.get_all_resource_ids()
                resource_count = len(resource_ids)
                backend_errors = 0
                metadata["resource_count"] = resource_count
            
            # Check for degraded conditions
            if resource_count > 10000:
                status = "DEGRADED"
                description = "High resource count, performance may be affected"
            
            if backend_errors > 100:
                status = "DEGRADED"
                description = "Multiple backend errors detected"
                
            # Check for backend-specific health
            if hasattr(self._backend, 'get_database_stats'):
                try:
                    db_stats = await self._backend.get_database_stats()
                    if db_stats.get("database_size_bytes", 0) > 1024 * 1024 * 100:  # 100MB
                        status = "DEGRADED"
                        description = "Database size is large, consider optimization"
                    metadata.update(db_stats)
                except Exception as e:
                    logger.error(f"Error getting backend health: {e}")
            
            return HealthStatus(
                status=status,
                source="state_manager",
                description=description,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return HealthStatus(
                status="ERROR",
                source="state_manager",
                description=f"Error getting health status: {e}",
                metadata={}
            )
    
    async def get_keys_by_prefix(self, prefix: str) -> List[str]:
        """Get all keys that start with the given prefix."""
        try:
            resource_ids = await self._backend.get_all_resource_ids()
            return [rid for rid in resource_ids if rid.startswith(prefix)]
        except Exception as e:
            logger.error(f"Error getting keys by prefix: {e}")
            return []