from asyncio import Lock
import asyncio
from collections import Counter, defaultdict
from contextlib import contextmanager
import json
import random
import sys
import time
from typing import Dict, List, Any, Optional, Set, Tuple, Type, TypeVar, Union
from dataclasses import dataclass, field
from enum import Enum, auto
from abc import ABC, abstractmethod
import weakref
import logging
from datetime import datetime, timedelta

from resources import (
    ResourceType, 
    ResourceState, 
    CircuitBreakerConfig, 
    ErrorClassification, 
    ErrorSeverity, 
    ErrorHandler, 
    EventQueue, 
    ResourceEventTypes, 
    StateManager, 
    CacheManager, 
    AgentContextManager, 
    MetricsManager, 
    AgentContext, 
    AgentContextType, 
    MemoryMonitor, 
    MemoryThresholds
)

from agent import Agent
from agent_validation import Validator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InterfaceError(Exception):
    """Base class for interface errors."""
    pass

class InitializationError(InterfaceError):
    """Error during interface initialization."""
    pass

class StateTransitionError(InterfaceError):
    """Error during state transition."""
    pass

class ResourceError(InterfaceError):
    """Error related to resource management."""
    pass

class ValidationError(InterfaceError):
    """Error during validation."""
    pass

class TimeoutError(InterfaceError):
    """Error when an operation times out."""
    pass

T = TypeVar('T', bound='BaseInterface')

class AgentState(Enum):
    READY = auto()
    PROCESSING = auto()
    VALIDATING = auto()
    FAILED_VALIDATION = auto()
    COMPLETE = auto()
    ERROR = auto()

CACHE_CIRCUIT_CONFIG = CircuitBreakerConfig(
    failure_threshold=10,
    recovery_timeout=30,
    failure_window=30
)

class ValidationManager:
    def __init__(self, event_queue: EventQueue, state_manager: StateManager, context_manager: AgentContextManager, correction_handler=None):
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
        """Validate agent output with improved error handling and timeout protection."""
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

class InterfaceCache:
    """Interface cache using dedicated CacheManager with improved error handling and metrics"""
    def __init__(self, event_queue: EventQueue, interface_id: str, cache_manager: CacheManager, memory_monitor: MemoryMonitor):
        self._cache_manager = cache_manager
        self._interface_id = interface_id
        self._cache_prefix = f"interface_cache:{interface_id}:"
        self._metrics_manager = MetricsManager(event_queue)
        self._memory_monitor = memory_monitor
        self._event_queue = event_queue
        
        # Ensure component is registered with memory monitor
        asyncio.create_task(self._ensure_registered())
        
    async def _ensure_registered(self) -> None:
        """Ensure the component is registered with memory monitor."""
        if not self._memory_monitor:
            logger.warning("Memory monitor is None, cannot register cache")
            return
            
        try:
            # Check if memory_monitor has register_component and call it appropriately
            if hasattr(self._memory_monitor, 'register_component'):
                if asyncio.iscoroutinefunction(self._memory_monitor.register_component):
                    await self._memory_monitor.register_component(self._interface_id)
                else:
                    self._memory_monitor.register_component(self._interface_id)
            else:
                logger.warning("Memory monitor does not have register_component method")
        except Exception as e:
            logger.warning(f"Failed to register cache with memory monitor: {str(e)}")
            
    async def set_cache(self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Enhanced cache setting with better error handling, retries and memory monitoring."""
        start_time = time.monotonic()
        cache_key = f"{self._interface_id}:{key}"
        
        # Enhanced metadata
        if metadata is None:
            metadata = {}
            
        metadata.update({
            "key": key,
            "interface_id": self._interface_id,
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            # Enhanced memory monitoring with prevention
            size_bytes = sys.getsizeof(value)
            size_mb = size_bytes / (1024 * 1024)
            
            # Define memory thresholds
            warning_threshold_mb = 10  # 10MB
            critical_threshold_mb = 50  # 50MB
            max_allowed_mb = 100       # 100MB
            
            # Check against maximum allowed size to prevent memory issues
            if size_mb > max_allowed_mb:
                logger.error(f"Cache value for {cache_key} exceeds maximum allowed size: {size_mb:.2f}MB > {max_allowed_mb}MB")
                try:
                    await self._event_queue.emit(
                        ResourceEventTypes.ERROR_OCCURRED.value,
                        {
                            "interface_id": self._interface_id,
                            "error": f"Cache value exceeds maximum allowed size: {size_mb:.2f}MB > {max_allowed_mb}MB",
                            "error_type": "MemoryLimitExceeded",
                            "key": key,
                            "size_mb": size_mb,
                            "max_allowed_mb": max_allowed_mb,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to emit error event: {str(e)}")
                    
                # Return early without setting cache to prevent memory issues
                raise ResourceError(f"Cache value exceeds maximum allowed size: {size_mb:.2f}MB > {max_allowed_mb}MB")
            
            # Warning for large values
            if size_mb > warning_threshold_mb:
                alert_type = "warning" if size_mb <= critical_threshold_mb else "critical"
                logger.warning(f"Cache value for {cache_key} is large: {size_mb:.2f}MB ({alert_type})")
                
                try:
                    await self._event_queue.emit(
                        ResourceEventTypes.RESOURCE_ALERT_CREATED.value,
                        {
                            "interface_id": self._interface_id,
                            "alert_type": f"large_cache_value_{alert_type}",
                            "severity": alert_type.upper(),
                            "message": f"Large cache value detected: {size_mb:.2f}MB",
                            "size_mb": size_mb,
                            "key": key,
                            "warning_threshold_mb": warning_threshold_mb,
                            "critical_threshold_mb": critical_threshold_mb,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to emit alert event: {str(e)}")
            
            # Track memory with enhanced error recovery
            try:
                # Get current memory usage before adding new resource
                total_memory_mb = 0
                try:
                    import psutil
                    process = psutil.Process()
                    total_memory_mb = process.memory_info().rss / (1024 * 1024)
                except ImportError:
                    # Fallback if psutil not available
                    pass
                
                # Track the resource
                await self._memory_monitor.track_resource(
                    f"cache:{key}", 
                    size_mb,
                    self._interface_id
                )
                
                # If total memory is high, trigger cleanup proactively
                if total_memory_mb > 0 and total_memory_mb > 500:  # 500MB threshold
                    logger.warning(f"High memory usage detected: {total_memory_mb:.2f}MB. Triggering proactive cleanup.")
                    
                    # Emit memory pressure event
                    try:
                        await self._event_queue.emit(
                            ResourceEventTypes.RESOURCE_ALERT_CREATED.value,
                            {
                                "interface_id": self._interface_id,
                                "alert_type": "memory_pressure",
                                "severity": "WARNING",
                                "message": f"High memory usage: {total_memory_mb:.2f}MB",
                                "total_memory_mb": total_memory_mb,
                                "timestamp": datetime.now().isoformat()
                            }
                        )
                    except Exception:
                        pass  # Ignore event emission failures
                    
                    # Trigger cache cleanup (asynchronously so it doesn't block)
                    asyncio.create_task(self._trigger_memory_cleanup())
                
            except Exception as e:
                logger.warning(f"Failed to track memory for cache {key}: {str(e)}")
                
            # Call set_cache_with_retries to handle actual cache setting with retries
            await self.set_cache_with_retries(cache_key, value, metadata, size_mb, start_time)
                
        except Exception as e:
            # Record failure metrics
            if metadata is None:
                metadata = {}
            await self._metrics_manager.record_metric(
                f"cache:{self._interface_id}:set_failures",
                1.0,
                metadata={**metadata, "error": str(e)}
            )
            raise
    
    async def _trigger_memory_cleanup(self) -> None:
        """Trigger memory cleanup when memory pressure is detected."""
        try:
            # Use cache manager's cleanup if available
            if hasattr(self._cache_manager, 'cleanup') and callable(self._cache_manager.cleanup):
                if asyncio.iscoroutinefunction(self._cache_manager.cleanup):
                    await self._cache_manager.cleanup(force=True)
                else:
                    self._cache_manager.cleanup(force=True)
                    
            # Log cleanup success
            logger.info(f"Completed proactive memory cleanup for {self._interface_id}")
            
        except Exception as e:
            logger.error(f"Failed to perform memory cleanup: {str(e)}")
            
    async def set_cache_with_retries(self, cache_key, value, metadata, size_mb, start_time):
        """Set cache with retries."""
        max_retries = 3
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                # Set cache with circuit breaker protection
                await self._cache_manager.set_cache(cache_key, value, metadata)
                
                # Record success metrics
                duration = time.monotonic() - start_time
                await self._metrics_manager.record_metric(
                    f"cache:{self._interface_id}:set_duration",
                    duration,
                    metadata={**metadata, "size_mb": size_mb, "duration_seconds": duration}
                )
                
                await self._metrics_manager.record_metric(
                    f"cache:{self._interface_id}:set_success",
                    1.0,
                    metadata={**metadata, "size_mb": size_mb}
                )
                
                return  # Success
            except Exception as e:
                retry_count += 1
                last_error = e
                logger.warning(f"Cache set retry {retry_count}/{max_retries} for {cache_key}: {str(e)}")
                
                if retry_count >= max_retries:
                    break
                
                # Exponential backoff
                await asyncio.sleep(0.1 * (2 ** retry_count))
        
        # If we get here, all retries failed
        logger.error(f"Cache set failed after {max_retries} retries for {cache_key}: {str(last_error)}")
        await self._metrics_manager.record_metric(
            f"cache:{self._interface_id}:set_failures",
            1.0,
            metadata={**metadata, "error": str(last_error), "retries": max_retries}
        )
        
        raise ResourceError(f"Failed to set cache after {max_retries} retries: {str(last_error)}")
        
# This is a duplicate method that has been consolidated into the previous implementation

    async def get_cache(self, key: str) -> Optional[Any]:
        """Get cache with enhanced error handling, retries and metrics."""
        start_time = time.monotonic()
        hit = False
        cache_key = f"{self._interface_id}:{key}"
        
        try:
            # Get with retries
            max_retries = 3
            retry_count = 0
            last_error = None
            
            while retry_count < max_retries:
                try:
                    # Get with circuit breaker protection
                    value = await self._cache_manager.get_cache(cache_key)
                    
                    hit = value is not None
                    
                    # Record metrics
                    duration = time.monotonic() - start_time
                    await self._metrics_manager.record_metric(
                        f"cache:{self._interface_id}:get_duration",
                        duration,
                        metadata={"key": key, "hit": hit, "duration_seconds": duration}
                    )
                    
                    # Record cache hit/miss
                    await self._metrics_manager.record_metric(
                        f"cache:{self._interface_id}:hits",
                        1.0 if hit else 0.0,
                        metadata={"key": key}
                    )
                    
                    return value
                    
                except Exception as e:
                    retry_count += 1
                    last_error = e
                    logger.warning(f"Cache get retry {retry_count}/{max_retries} for {cache_key}: {str(e)}")
                    
                    if retry_count >= max_retries:
                        break
                        
                    # Exponential backoff
                    await asyncio.sleep(0.1 * (2 ** retry_count))
            
            # If we get here, all retries failed
            logger.error(f"Cache get failed after {max_retries} retries for {cache_key}: {str(last_error)}")
            await self._metrics_manager.record_metric(
                f"cache:{self._interface_id}:get_failures",
                1.0,
                metadata={"key": key, "error": str(last_error), "retries": max_retries}
            )
            
            raise ResourceError(f"Failed to get cache after {max_retries} retries: {str(last_error)}")
            
        except Exception as e:
            await self._metrics_manager.record_metric(
                f"cache:{self._interface_id}:get_failures",
                1.0,
                metadata={"key": key, "error": str(e)}
            )
            raise
        
    async def invalidate(self, key: str) -> None:
        """Invalidate cache entry with enhanced error handling."""
        cache_key = f"{self._interface_id}:{key}"
        
        try:
            await self._cache_manager.invalidate(cache_key)
            
            # Record successful invalidation
            await self._metrics_manager.record_metric(
                f"cache:{self._interface_id}:invalidations",
                1.0,
                metadata={"key": key}
            )
            
            # Clean up memory tracking
            try:
                await self._memory_monitor.untrack_resource(f"cache:{key}", self._interface_id)
            except Exception as e:
                logger.warning(f"Failed to untrack memory for invalidated cache {key}: {str(e)}")
                
        except Exception as e:
            logger.error(f"Failed to invalidate cache for {key}: {str(e)}")
            
            # Record failed invalidation
            await self._metrics_manager.record_metric(
                f"cache:{self._interface_id}:invalidation_failures",
                1.0,
                metadata={"key": key, "error": str(e)}
            )
            
            raise ResourceError(f"Failed to invalidate cache: {str(e)}")

class InterfaceMetrics:
    """Handles interface metrics with enhanced error handling and comprehensive metrics collection"""
    def __init__(self, event_queue: EventQueue, state_manager: StateManager, interface_id: str):
        self._metrics_manager = MetricsManager(event_queue)
        self._state_manager = state_manager
        self._interface_id = interface_id
        self._event_queue = event_queue
        
        # Initialize metrics collection in background
        asyncio.create_task(self._initialize_metrics())
        
    async def _initialize_metrics(self) -> None:
        """Initialize basic metrics for the interface."""
        try:
            # Register basic interface existence metric
            await self._metrics_manager.record_metric(
                f"interface:{self._interface_id}:initialized",
                1.0,
                metadata={"timestamp": datetime.now().isoformat()}
            )
        except Exception as e:
            logger.warning(f"Failed to initialize metrics for {self._interface_id}: {str(e)}")
        
    async def register_core_metrics(self, interface_state: ResourceState) -> None:
        """Register core interface metrics with improved error handling."""
        try:
            # Record health metric
            await self._metrics_manager.record_metric(
                f"interface:{self._interface_id}:health",
                1.0 if interface_state == ResourceState.ACTIVE else 0.0,
                metadata={"state": interface_state.name, "timestamp": datetime.now().isoformat()}
            )
            
            # Record state transition count
            try:
                state_history = await self._state_manager.get_state_history(
                    f"interface:{self._interface_id}:state"
                )
                
                await self._metrics_manager.record_metric(
                    f"interface:{self._interface_id}:state_changes",
                    len(state_history),
                    metadata={"last_state": interface_state.name}
                )
                
                # Record state duration if applicable
                if state_history and len(state_history) >= 2:
                    # Calculate time in current state
                    current_state_start = state_history[-1].get("timestamp")
                    if current_state_start:
                        try:
                            start_time = datetime.fromisoformat(current_state_start)
                            duration = (datetime.now() - start_time).total_seconds()
                            
                            await self._metrics_manager.record_metric(
                                f"interface:{self._interface_id}:state_duration",
                                duration,
                                metadata={"state": interface_state.name}
                            )
                        except Exception as e:
                            logger.warning(f"Failed to calculate state duration: {str(e)}")
                
            except Exception as e:
                logger.warning(f"Failed to record state history metrics: {str(e)}")
                
        except Exception as e:
            logger.error(f"Failed to register core metrics for {self._interface_id}: {str(e)}")
            
            # Try to emit an error event
            try:
                await self._event_queue.emit(
                    ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
                    {
                        "interface_id": self._interface_id,
                        "error": str(e),
                        "error_type": "metrics_failure",
                        "component": "core_metrics"
                    }
                )
            except Exception:
                pass  # Ignore event emission failures
            
    async def register_validation_metrics(self, validation_history: List[Dict[str, Any]]) -> None:
        """Register validation-related metrics with improved error handling and more detailed metrics."""
        if not validation_history:
            return
            
        try:
            # Calculate success rate
            success_count = sum(1 for v in validation_history if v.get("success", False))
            total_count = len(validation_history)
            success_rate = success_count / total_count if total_count > 0 else 0
            
            # Record success rate
            await self._metrics_manager.record_metric(
                f"interface:{self._interface_id}:validation:success_rate",
                success_rate,
                metadata={
                    "success_count": success_count,
                    "total_count": total_count,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Record attempts count
            await self._metrics_manager.record_metric(
                f"interface:{self._interface_id}:validation:attempts",
                total_count
            )
            
            # Record average attempts needed for success if applicable
            if success_count > 0:
                # Group validation history by operation
                validation_by_operation = defaultdict(list)
                for validation in validation_history:
                    operation = validation.get("operation_id", "unknown")
                    validation_by_operation[operation].append(validation)
                
                # Calculate attempts needed for successful operations
                attempts_until_success = []
                for operation, validations in validation_by_operation.items():
                    # Sort by timestamp if available
                    if all("timestamp" in v for v in validations):
                        validations.sort(key=lambda v: v.get("timestamp", ""))
                    
                    # Count attempts until first success
                    for i, validation in enumerate(validations, 1):
                        if validation.get("success", False):
                            attempts_until_success.append(i)
                            break
                
                if attempts_until_success:
                    avg_attempts = sum(attempts_until_success) / len(attempts_until_success)
                    await self._metrics_manager.record_metric(
                        f"interface:{self._interface_id}:validation:avg_attempts_to_success",
                        avg_attempts
                    )
            
            # Record common error types if failures exist
            if success_count < total_count:
                error_counts = Counter()
                for validation in validation_history:
                    if not validation.get("success", False) and "error_analysis" in validation:
                        error_analysis = validation["error_analysis"]
                        error_type = error_analysis.get("error_type", "unknown")
                        error_counts[error_type] += 1
                
                # Record top errors
                for error_type, count in error_counts.most_common(5):
                    await self._metrics_manager.record_metric(
                        f"interface:{self._interface_id}:validation:error:{error_type}",
                        count,
                        metadata={"error_type": error_type}
                    )
                
        except Exception as e:
            logger.error(f"Failed to register validation metrics for {self._interface_id}: {str(e)}")
            
            # Try to emit an error event
            try:
                await self._event_queue.emit(
                    ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
                    {
                        "interface_id": self._interface_id,
                        "error": str(e),
                        "error_type": "metrics_failure",
                        "component": "validation_metrics"
                    }
                )
            except Exception:
                pass  # Ignore event emission failures
    
    async def register_performance_metrics(self, 
                                          response_time: float,
                                          processing_result: Dict[str, Any]) -> None:
        """Register performance metrics for the interface."""
        try:
            # Record response time
            await self._metrics_manager.record_metric(
                f"interface:{self._interface_id}:response_time",
                response_time,
                metadata={"timestamp": datetime.now().isoformat()}
            )
            
            # Record success/failure
            is_success = "error" not in processing_result
            await self._metrics_manager.record_metric(
                f"interface:{self._interface_id}:success",
                1.0 if is_success else 0.0
            )
            
            # Record specific metrics based on result
            if not is_success:
                error_type = "unknown"
                if isinstance(processing_result.get("error"), str):
                    # Extract general error category
                    error_text = processing_result["error"].lower()
                    if "timeout" in error_text:
                        error_type = "timeout"
                    elif "validation" in error_text:
                        error_type = "validation"
                    elif "memory" in error_text:
                        error_type = "memory"
                    elif "permission" in error_text:
                        error_type = "permission"
                    
                await self._metrics_manager.record_metric(
                    f"interface:{self._interface_id}:error:{error_type}",
                    1.0,
                    metadata={"error_message": str(processing_result.get("error", ""))}
                )
                
        except Exception as e:
            logger.warning(f"Failed to register performance metrics: {str(e)}")
            # Continue execution - metrics failures shouldn't block the main process

class BaseInterface(ABC):
    def __init__(
        self, 
        interface_id: str, 
        event_queue: EventQueue,
        state_manager: StateManager,
        context_manager: AgentContextManager,
        cache_manager: CacheManager,
        metrics_manager: MetricsManager,
        error_handler: ErrorHandler,
        memory_monitor: MemoryMonitor
    ):
        self.interface_id = interface_id
        self._event_queue = event_queue
        
        # Store manager references directly
        self._state_manager = state_manager
        self._context_manager = context_manager
        self._cache_manager = cache_manager
        self._metrics_manager = metrics_manager
        self._error_handler = error_handler

        self._memory_monitor = memory_monitor
        
        # Defer lock creation to async initialization
        self._state_lock = None
        self._initialized = False

        self._cache = InterfaceCache(event_queue, interface_id, cache_manager, self._memory_monitor)
        self._validation_rules: Dict[str, callable] = {}
    
    async def ensure_initialized(self) -> None:
        """Ensure the interface is properly initialized with running event loop with race condition protection."""
        # No early check here to avoid race conditions
        
        # Lazy initialize init_lock if needed
        if not hasattr(self, '_init_lock') or self._init_lock is None:
            self._init_lock = asyncio.Lock()
        
        async with self._init_lock:
            if not self._initialized:  # Check inside the lock
                logger.debug(f"Initializing interface {self.interface_id}")
                
                # Ensure event queue is running
                await self._ensure_event_queue_running()
                        
                # Create state lock now that event queue is started
                self._state_lock = asyncio.Lock()
                self._initialized = True
                
                # Register with memory monitor if not already registered
                if hasattr(self, '_memory_monitor') and self._memory_monitor:
                    try:
                        # Check if register_component is a coroutine function
                        if hasattr(self._memory_monitor, 'register_component'):
                            if asyncio.iscoroutinefunction(self._memory_monitor.register_component):
                                await self._memory_monitor.register_component(self.interface_id)
                            else:
                                self._memory_monitor.register_component(self.interface_id)
                    except Exception as e:
                        logger.warning(f"Failed to register with memory monitor: {str(e)}")

                logger.debug(f"Interface {self.interface_id} initialized successfully")

    @contextmanager
    def ensure_event_loop(self):
        """Context manager to ensure a running event loop using EventLoopManager."""
        from resources.events import EventLoopManager
        
        created_new_loop = False
        loop = None
        
        try:
            try:
                # Use EventLoopManager to get a consistent loop
                loop = EventLoopManager.get_event_loop()
                logger.debug(f"Using existing event loop for {self.interface_id}")
            except RuntimeError:
                logger.debug(f"Creating new event loop for {self.interface_id}")
                
                # Let EventLoopManager create a new loop
                loop = EventLoopManager.get_event_loop()
                created_new_loop = True
                
            yield loop
            
        finally:
            # Only stop the loop if we created it and it's still running
            if created_new_loop and loop and loop.is_running():
                logger.debug(f"Stopping event loop created for {self.interface_id}")
                loop.stop()

    async def _ensure_event_queue_running(self) -> None:
        """Ensure event queue is running, with improved error handling and using EventLoopManager."""
        from resources.events import EventLoopManager
        
        max_retries = 3
        retry_count = 0
        
        # Get the queue ID for better logging
        queue_id = getattr(self._event_queue, '_id', 'unknown')
        
        while retry_count < max_retries:
            try:
                # Ensure we're in the correct event loop context
                loop = EventLoopManager.get_event_loop()
                
                # Check if EventQueue has running state
                if hasattr(self._event_queue, '_running'):
                    if not self._event_queue._running:
                        logger.debug(f"Starting event queue {queue_id} for interface {self.interface_id}")
                        
                        # Start the event queue
                        await self._event_queue.start()
                        
                        # Verify it's now running with explicit check
                        if not self._event_queue._running:
                            raise InitializationError(f"Failed to start event queue {queue_id} for {self.interface_id}")
                
                # Queue is running
                logger.debug(f"Event queue {queue_id} running for {self.interface_id}")
                
                # Add a small delay to allow for queue task to initialize
                await asyncio.sleep(0.05)
                
                return
                
            except Exception as e:
                retry_count += 1
                logger.warning(f"Event queue start attempt {retry_count}/{max_retries} for {queue_id} failed: {str(e)}")
                
                if retry_count >= max_retries:
                    logger.error(f"Failed to start event queue {queue_id} after {max_retries} attempts")
                    if isinstance(e, InitializationError):
                        raise
                    raise InitializationError(f"Failed to initialize event queue {queue_id}: {str(e)}")
                
                # Wait before retrying with exponential backoff
                await asyncio.sleep(0.1 * (2 ** retry_count))

    @classmethod
    async def create(cls: Type[T], interface_id: str) -> T:
        """Factory method to create interface with proper event queue setup using EventLoopManager."""
        from resources.events import EventLoopManager
        
        # Use EventLoopManager to get a consistent event loop
        loop = EventLoopManager.get_event_loop()
        
        # Create event queue with an ID for better tracking
        event_queue = EventQueue(queue_id=f"interface_{interface_id}_queue")
        
        # Start event queue in the managed loop
        await event_queue.start()
        
        # Create and return the interface instance
        return cls(interface_id, event_queue)

    async def cleanup(self) -> bool:
        """
        Coordinated cleanup with retries and detailed error reporting.
        Returns True if successful.
        """
        cleanup_successful = True
        cleanup_errors = []
        
        try:
            # Clean up memory monitor
            if hasattr(self, '_memory_monitor') and self._memory_monitor:
                try:
                    # Check if unregister_component exists
                    if hasattr(self._memory_monitor, 'unregister_component'):
                        if asyncio.iscoroutinefunction(self._memory_monitor.unregister_component):
                            await self._memory_monitor.unregister_component(self.interface_id)
                        else:
                            self._memory_monitor.unregister_component(self.interface_id)
                        logger.debug(f"Successfully unregistered {self.interface_id} from memory monitor")
                    else:
                        logger.debug(f"MemoryMonitor does not have unregister_component method - skipping")
                except Exception as e:
                    cleanup_errors.append(f"Memory monitor cleanup error: {str(e)}")
                    cleanup_successful = False
                    logger.warning(f"Failed to unregister from memory monitor: {str(e)}")

            # Clean up state if state manager exists
            if hasattr(self, '_state_manager') and self._state_manager:
                try:
                    # Set terminal state
                    await self._state_manager.set_state(
                        f"cleanup:{self.interface_id}",
                        {"status": "completed", "timestamp": datetime.now().isoformat()},
                        ResourceType.STATE
                    )
                    logger.debug(f"Successfully set terminal state for {self.interface_id}")
                except Exception as e:
                    cleanup_errors.append(f"State cleanup error: {str(e)}")
                    cleanup_successful = False
                    logger.warning(f"Failed to set terminal state: {str(e)}")
            
            # Emit cleanup event if event queue exists
            if hasattr(self, '_event_queue') and self._event_queue:
                try:
                    if hasattr(self._event_queue, 'stop') and self._event_queue._running:
                        if asyncio.iscoroutinefunction(self._event_queue.stop):
                            await self._event_queue.stop()
                        else:
                            self._event_queue.stop()
                        logger.debug(f"Successfully stopped event queue for {self.interface_id}")
                except Exception as e:
                    cleanup_errors.append(f"Event queue cleanup error: {str(e)}")
                    cleanup_successful = False
                    logger.warning(f"Failed to stop event queue: {str(e)}")
                
                try:
                    await self._event_queue.emit(
                        ResourceEventTypes.RESOURCE_CLEANUP.value,
                        {
                            "interface_id": self.interface_id,
                            "status": "success" if cleanup_successful else "partial_failure",
                            "errors": cleanup_errors,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to emit cleanup event: {str(e)}")
                    # Don't fail the cleanup just because we couldn't emit an event
                
            # Log cleanup status
            if cleanup_errors:
                logger.warning(f"Cleanup completed with errors for {self.interface_id}: {'; '.join(cleanup_errors)}")
            else:
                logger.info(f"Cleanup completed successfully for {self.interface_id}")
                
            return cleanup_successful
        except Exception as e:
            logger.error(f"Critical error during interface cleanup: {str(e)}")
            # Try to emit critical failure event
            if hasattr(self, '_event_queue') and self._event_queue:
                try:
                    await self._event_queue.emit(
                        ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
                        {
                            "interface_id": self.interface_id,
                            "error": str(e),
                            "error_type": "cleanup_failure",
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                except Exception:
                    pass  # Ignore failures here
            return False

    async def get_state(self) -> ResourceState:
        """Get current interface state asynchronously."""
        state_entry = await self._state_manager.get_state(f"interface:{self.interface_id}")
        
        # If state_entry has a 'state' attribute (i.e., it's a StateEntry object), extract and return the state
        if hasattr(state_entry, 'state'):
            return state_entry.state
            
        # Otherwise, assume it's already a ResourceState enum or None
        return state_entry
        
    async def set_state(self, new_state: ResourceState, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Set interface state with improved error handling and retries."""
        if not isinstance(new_state, ResourceState):
            raise ValueError(f"Invalid state type: {type(new_state)}")
        
        # Ensure initialization
        await self.ensure_initialized()
        
        # Enhanced metadata
        if metadata is None:
            metadata = {}
        
        metadata.update({
            "timestamp": datetime.now().isoformat(),
            "interface_id": self.interface_id
        })
        
        # Check if state lock exists
        if self._state_lock is None:
            logger.warning(f"State lock is None for {self.interface_id}, creating new lock")
            self._state_lock = asyncio.Lock()
        
        # Try with lock first (happy path)
        try:
            async with self._state_lock:
                # Double-check current state within lock
                try:
                    current_state = await self.get_state()
                    if current_state == new_state:
                        return
                except Exception:
                    # Continue with state update even if we can't get current state
                    pass
                    
                # Update state
                await self._state_manager.set_state(
                    f"interface:{self.interface_id}",
                    new_state,
                    ResourceType.STATE,
                    metadata=metadata
                )
                
                # Emit state change event
                try:
                    await self._event_queue.emit(
                        ResourceEventTypes.INTERFACE_STATE_CHANGED.value,
                        {
                            "interface_id": self.interface_id,
                            "old_state": current_state.name if current_state else "UNKNOWN",
                            "new_state": new_state.name,
                            "metadata": metadata
                        }
                    )
                except Exception as event_error:
                    logger.warning(f"Failed to emit state change event: {str(event_error)}")
                
                logger.debug(f"State for {self.interface_id} updated to {new_state}")
                return
        except Exception as e:
            logger.error(f"Error setting state for {self.interface_id}: {str(e)}")
        
        # Fall back to direct state setting without lock
        logger.warning(f"Falling back to lockless state update for {self.interface_id}")
        try:
            err_metadata = {**metadata, "error": "State lock acquisition failed"}
            await self._state_manager.set_state(
                f"interface:{self.interface_id}",
                new_state,
                ResourceType.STATE,
                metadata=err_metadata
            )
            
            # Still try to emit the event
            try:
                await self._event_queue.emit(
                    ResourceEventTypes.INTERFACE_STATE_CHANGED.value,
                    {
                        "interface_id": self.interface_id,
                        "old_state": "UNKNOWN",  # We couldn't check within lock
                        "new_state": new_state.name,
                        "metadata": err_metadata
                    }
                )
            except Exception:
                pass  # Ignore event emission errors in fallback path
                
            logger.debug(f"State for {self.interface_id} updated to {new_state} (without lock)")
        except Exception as inner_e:
            logger.error(f"Failed direct state setting for {self.interface_id}: {str(inner_e)}")
            raise StateTransitionError(f"Failed to set state to {new_state.name}: {str(inner_e)}")


class AgentInterface(BaseInterface):
    """Agent interface using modular resource managers"""
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
        self.agent_state = AgentState.READY
        self.model = model
        self.agent = Agent(
            event_queue=event_queue,
            state_manager=self._state_manager,
            context_manager=self._context_manager,
            cache_manager=self._cache_manager,
            metrics_manager=self._metrics_manager,
            error_handler=self._error_handler,
            model=model
        )
        self._validation_manager = ValidationManager(event_queue, self._state_manager, self._context_manager)
        self._validation_manager._validator.correction_handler = weakref.proxy(self.agent)
        
        self._metrics = InterfaceMetrics(event_queue, self._state_manager, self.interface_id)
        self._max_validation_attempts = 3
        self._event_queue = event_queue
    
    async def set_agent_state(self, new_state: AgentState, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Update agent state and synchronize with resource state with initialization safeguard"""
        resource_states = {
            AgentState.PROCESSING: ResourceState.ACTIVE,
            AgentState.VALIDATING: ResourceState.PAUSED,
            AgentState.FAILED_VALIDATION: ResourceState.FAILED,
            AgentState.ERROR: ResourceState.TERMINATED,
            AgentState.COMPLETE: ResourceState.ACTIVE
        }
        logger.info(f"Setting agent state to {new_state}")
        
        # Ensure initialization before using lock
        await self.ensure_initialized()
        
        try:
            async with self._state_lock:
                self.agent_state = new_state
                if new_state in resource_states:
                    await self.set_state(resource_states[new_state], metadata=metadata)
        except Exception as e:
            logger.error(f"Error setting agent state to {new_state}: {str(e)}")
            # Still update internal state even if lock fails
            self.agent_state = new_state
            # Try to update resource state directly without lock
            if new_state in resource_states:
                try:
                    await self._state_manager.set_state(
                        f"interface:{self.interface_id}",
                        resource_states[new_state],
                        ResourceType.STATE,
                        metadata={"error": str(e), **metadata} if metadata else {"error": str(e)}
                    )
                except Exception as inner_e:
                    logger.error(f"Failed fallback setting state: {str(inner_e)}")
                    
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
        """Process with validation with improved error handling and metrics."""
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
            except Exception as e:
                logger.error(f"Failed to set agent state to PROCESSING: {str(e)}")
                # Continue anyway - we'll try to process even if state setting failed
            
            # Create or get context
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
            except Exception as e:
                logger.error(f"Error creating/getting context for {request_id}: {str(e)}")
                # Continue anyway - we'll try to process even without proper context
            
            # Start processing timer
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

class FeatureInterface(BaseInterface):
    def __init__(self, feature_id: str):
        super().__init__(f"feature:{feature_id}")
        self._feature_state: Dict[str, Any] = {}
        
    def set_feature_state(self, key: str, value: Any) -> None:
        self._feature_state[key] = value
        # self._state_manager.set_state(
        #     f"feature:{self.interface_id}:state:{key}",
        #     value,
        #     resource_type=ResourceType.STATE
        # )
        
    def get_feature_state(self, key: str) -> Optional[Any]:
        return self._feature_state.get(key)

class ComponentInterface(BaseInterface):
    def __init__(self, component_id: str, event_queue: EventQueue):
        super().__init__(f"component:{component_id}", event_queue)
        self._features: Set[str] = set()
        
                

class TestAgent(AgentInterface):
    async def initialize(self):
        """Properly initialize the event queue with retry and verification"""
        if hasattr(self._event_queue, '_running') and not self._event_queue._running:
            try:
                # Start with retry
                max_retries = 3
                retry_count = 0
                while retry_count < max_retries:
                    try:
                        await self._event_queue.start()
                        
                        # Verify it started
                        if not self._event_queue._running:
                            raise InitializationError("Failed to start event queue")
                        
                        # Success
                        break
                    except Exception as e:
                        retry_count += 1
                        logger.warning(f"Event queue start retry {retry_count}/{max_retries}: {str(e)}")
                        if retry_count >= max_retries:
                            logger.error("Failed to start event queue after max retries")
                            return False
                        await asyncio.sleep(0.1 * (2 ** retry_count))
            except Exception as e:
                logger.error(f"Error starting event queue: {str(e)}")
                return False
        
        # Allow a short time for event queue to start processing
        await asyncio.sleep(0.1)
        
        # Ensure base interface is initialized
        try:
            await self.ensure_initialized()
        except Exception as e:
            logger.error(f"Error initializing base interface: {str(e)}")
            return False
        
        logger.info("TestAgent initialized successfully")
        return True
        
    def __init__(self):
        # Create a proper event queue with start() already called
        event_queue = EventQueue()
        
        # Create all required resource managers using the same event queue
        state_manager = StateManager(event_queue)
        context_manager = AgentContextManager(event_queue)
        cache_manager = CacheManager(event_queue)
        metrics_manager = MetricsManager(event_queue)
        error_handler = ErrorHandler(event_queue)

        memory_monitor = MemoryMonitor(event_queue)
        
        super().__init__(
            "test_agent", 
            event_queue=event_queue,
            state_manager=state_manager,
            context_manager=context_manager,
            cache_manager=cache_manager,
            metrics_manager=metrics_manager,
            error_handler=error_handler,
            memory_monitor=memory_monitor
        )
        self._initialized = False
        
        # Create a proper test agent that can process requests
        self.agent = Agent(
            event_queue=event_queue,
            state_manager=state_manager,
            context_manager=context_manager,
            cache_manager=cache_manager,
            metrics_manager=metrics_manager,
            error_handler=error_handler,
            model="test-model"  # Use a test model identifier
        )
        
    async def get_response(self, conversation: str,
                    schema: Dict[str, Any],
                    current_phase: Optional[str] = None,
                    operation_id: Optional[str] = None,
                    system_prompt_info: Optional[Tuple[str]] = None) -> Dict[str, Any]:
        """Implement the abstract get_response method with proper logging"""
        logger.info(f"Processing request - Phase: {current_phase}, Operation: {operation_id}")
        try:
            if not self._initialized:
                await self.initialize()
                # Ensure base interface is initialized too
                await self.ensure_initialized()
                self._initialized = True
                
            return {
                "message": "Test response",
                "status": "success",
                "data": {
                    "conversation": conversation,
                    "phase": current_phase or "default"
                }
            }
        except Exception as e:
            logger.error(f"Error in get_response: {str(e)}", exc_info=True)
            raise

async def main():
    """Test the AgentInterface process_with_validation functionality."""
    logger.info("Initializing test agent")
    print("initializing test agent")
    test_agent = None
    
    try:
        # Initialize test agent with proper resource managers
        test_agent = TestAgent()
        
        # Ensure the agent is initialized - with a timeout
        try:
            init_success = await asyncio.wait_for(test_agent.initialize(), timeout=5.0)
            if not init_success:
                logger.error("Failed to initialize test agent")
                return
        except asyncio.TimeoutError:
            logger.error("Timeout waiting for agent initialization")
            return
        
        # Define test schema
        test_schema = {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "status": {"type": "string"},
                "data": {
                    "type": "object",
                    "properties": {
                        "conversation": {"type": "string"},
                        "phase": {"type": "string"}
                    },
                    "required": ["conversation", "phase"]
                }
            },
            "required": ["message", "status", "data"]
        }
        
        logger.info("Starting process_with_validation test...")
        
        # Test basic processing with proper system_prompt_info
        logger.info("Test 1: Basic Processing")
        result = await test_agent.process_with_validation(
            conversation="Test conversation",
            system_prompt_info=("test_dir", "test_prompt"),  # Add required parameter
            schema=test_schema,
            operation_id="test_op_1"
        )
        logger.info(f"Result: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
        raise
    finally:
        if test_agent:
            try:
                # Use proper cleanup
                await test_agent.cleanup()
                # Explicitly cancel any remaining tasks
                tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
                for task in tasks:
                    task.cancel()
                logger.info("Test agent cleaned up successfully")
            except Exception as e:
                logger.error(f"Error cleaning up test agent: {str(e)}", exc_info=True)

if __name__ == "__main__":
    # Set up logging with more detailed format
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the test
    asyncio.run(main())