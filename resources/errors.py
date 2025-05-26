from dataclasses import dataclass, field
from resources.common import ErrorSeverity, ResourceType
from datetime import datetime
import logging
import traceback
import threading
from typing import Dict, Any, Optional, Counter
from collections import Counter

@dataclass
class ErrorContext:
    """Enhanced error context with correlation tracking"""
    resource_id: str
    operation: str
    attempt: int = 1
    recovery_attempts: int = 0
    details: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    parent_error_id: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)


@dataclass
class ErrorClassification:
    """Detailed error classification information"""
    severity: ErrorSeverity
    error_type: str
    source: str
    impact_score: float  # 0-1 score of operational impact
    requires_intervention: bool
    recovery_strategy: Optional[str]
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)

class ResourceError(Exception):
    """Enhanced base exception for resource errors with correlation"""
    def __init__(self, 
                 message: str,
                 resource_id: str,
                 severity: ErrorSeverity,
                 recovery_strategy: Optional[str] = None,
                 impact_score: float = 0.5,
                 requires_intervention: bool = False,
                 details: Optional[Dict[str, Any]] = None,
                 correlation_id: Optional[str] = None):
        self.message = message
        self.resource_id = resource_id
        self.severity = severity
        self.recovery_strategy = recovery_strategy
        self.impact_score = impact_score
        self.requires_intervention = requires_intervention
        self.details = details or {}
        self.timestamp = datetime.now()
        self.error_id = f"{resource_id}:{datetime.now().timestamp()}"
        self.correlation_id = correlation_id or self.error_id

        # Create full context
        self.context = ErrorContext(
            resource_id=resource_id,
            operation="unknown",  # Will be set by specific error types
            details=self.details,
            correlation_id=self.correlation_id
        )
        
        super().__init__(self.message)

class ResourceExhaustionError(ResourceError):
    """Raised when a resource exceeds its limits"""
    def __init__(self, 
                 resource_id: str,
                 operation: str,
                 current_usage: float,
                 limit: float,
                 resource_type: str,
                 details: Optional[Dict[str, Any]] = None,
                 correlation_id: Optional[str] = None):
        message = f"Resource {resource_id} exceeded {resource_type} limit: {current_usage}/{limit}"
        
        # Prepare details with usage information
        combined_details = {
            "current_usage": current_usage,
            "limit": limit,
            "resource_type": resource_type,
            "usage_percentage": current_usage / limit if limit > 0 else float('inf'),
            **(details or {})
        }
        
        is_critical = current_usage > limit * 1.5
        
        super().__init__(
            message=message,
            resource_id=resource_id,
            severity=ErrorSeverity.FATAL if is_critical else ErrorSeverity.DEGRADED,
            recovery_strategy="reduce_load" if not is_critical else "force_cleanup",
            impact_score=min(1.0, current_usage / limit) if limit > 0 else 1.0,
            requires_intervention=is_critical,
            details=combined_details,
            correlation_id=correlation_id
        )
        self.operation = operation
        self.current_usage = current_usage
        self.limit = limit
        self.resource_type = resource_type
        
        # Set operation in context
        self.context.operation = operation

class ResourceTimeoutError(ResourceError):
    """Raised when a resource operation times out"""
    def __init__(self,
                 resource_id: str, 
                 operation: str,
                 timeout_seconds: float,
                 details: Optional[Dict[str, Any]] = None,
                 correlation_id: Optional[str] = None):
        message = f"Operation {operation} on resource {resource_id} timed out after {timeout_seconds}s"
        super().__init__(
            message=message,
            resource_id=resource_id,
            severity=ErrorSeverity.TRANSIENT,
            recovery_strategy="retry_with_backoff",
            impact_score=0.3,
            requires_intervention=False,
            details=details,
            correlation_id=correlation_id
        )
        self.operation = operation
        self.timeout = timeout_seconds
        self.timeout_seconds = timeout_seconds  # Added for compatibility with tests
        # Set operation in context
        self.context.operation = operation

class ResourceOperationError(ResourceError):
    """Error during resource operations with recovery tracking"""
    def __init__(self,
                 message: str,
                 resource_id: str,
                 severity: ErrorSeverity,
                 operation: str,
                 recovery_strategy: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None,
                 correlation_id: Optional[str] = None,
                 parent_error_id: Optional[str] = None):
        super().__init__(
            message=message,
            resource_id=resource_id,
            severity=severity,
            recovery_strategy=recovery_strategy,
            details=details or {},
            correlation_id=correlation_id
        )
        self.operation = operation
        
        # Set operation in context
        self.context.operation = operation
        
        # Set parent error ID for tracking chains of errors
        if parent_error_id:
            self.context.parent_error_id = parent_error_id


class CoordinationError(ResourceError):
    """Raised when there's an error during agent coordination"""
    def __init__(self,
                 message: str,
                 resource_id: str = "water_agent",
                 severity: ErrorSeverity = ErrorSeverity.DEGRADED,
                 details: Optional[Dict[str, Any]] = None,
                 correlation_id: Optional[str] = None):
        super().__init__(
            message=message,
            resource_id=resource_id,
            severity=severity,
            recovery_strategy="retry_coordination",
            impact_score=0.6,
            requires_intervention=False,
            details=details or {},
            correlation_id=correlation_id
        )
        self.operation = "agent_coordination"
        self.context.operation = "agent_coordination"


class MisunderstandingDetectionError(CoordinationError):
    """Raised when there's an error detecting misunderstandings between agents"""
    def __init__(self,
                 message: str,
                 resource_id: str = "water_agent",
                 details: Optional[Dict[str, Any]] = None,
                 correlation_id: Optional[str] = None):
        super().__init__(
            message=message,
            resource_id=resource_id,
            severity=ErrorSeverity.TRANSIENT,
            details=details or {},
            correlation_id=correlation_id
        )
        self.operation = "misunderstanding_detection"
        self.context.operation = "misunderstanding_detection"


logger = logging.getLogger(__name__)

class ErrorHandler:
    """Centralized error handling system with thread safety"""
    def __init__(self, event_queue):
        self._event_queue = event_queue
        self._error_counts: Counter = Counter()
        self._last_errors: Dict[str, datetime] = {}
        # Add thread-safe lock for shared state access
        self._lock = threading.RLock()
        
    async def handle_error(self,
                          error: Exception,
                          component_id: str,
                          operation: str,
                          context: Optional[Dict[str, Any]] = None) -> ErrorClassification:
        """Unified error handling with classification and improved reporting"""
        error_id = f"{component_id}:{operation}"
        classification = self._classify_error(error, context)
        
        # Thread-safely update error tracking with lock
        with self._lock:
            self._error_counts[error_id] += 1
            self._last_errors[error_id] = datetime.now()
            # Create a snapshot of the current error count for event emission
            current_count = self._error_counts[error_id]
        
        # Enhanced error context for better tracking
        error_context = {
            "error_id": error_id,
            "timestamp": datetime.now().isoformat(),
            "error_message": str(error),
            "error_type": type(error).__name__,
            "stacktrace": self._get_error_traceback(error),
            "frequency": current_count,  # Use the snapshot value
            **(context or {})
        }
        
        # Emit error events
        try:
            # Emit to ERROR_OCCURRED
            await self._event_queue.emit(
                "error_occurred",  # Use string instead of enum
                {
                    "component_id": component_id,
                    "operation": operation,
                    "error_type": classification.error_type,
                    "severity": classification.severity,
                    "requires_intervention": classification.requires_intervention,
                    "context": error_context
                }
            )
            
            # Also emit to RESOURCE_ERROR_OCCURRED for existing subscribers
            await self._event_queue.emit(
                "resource_error_occurred",  # Use string instead of enum
                {
                    "component_id": component_id,
                    "operation": operation,
                    "error_type": classification.error_type,
                    "severity": classification.severity,
                    "requires_intervention": classification.requires_intervention,
                    "context": error_context
                }
            )
        except Exception as e:
            # Log but don't fail the error handling if event emission fails
            logger.error(f"Failed to emit error events: {str(e)}")
        
        return classification
        
    def _get_error_traceback(self, error: Exception) -> str:
        """Get formatted traceback for an error if available"""
        try:
            tb = getattr(error, '__traceback__', None)
            if tb:
                return ''.join(traceback.format_tb(tb))
            return "No traceback available"
        except Exception:
            return "Error getting traceback"
        
    def _classify_error(self, 
                       error: Exception, 
                       context: Optional[Dict[str, Any]] = None) -> ErrorClassification:
        """Classify error type and severity with enhanced patterns"""
        # Check if the error is a ResourceExhaustionError by checking for required attributes
        is_exhaustion_error = (
            hasattr(error, 'current_usage') and
            hasattr(error, 'limit') and
            hasattr(error, 'resource_id') and
            hasattr(error, 'impact_score')
        )
        
        if is_exhaustion_error:
            # Enhanced classification for extreme memory pressure
            if error.current_usage > 2 * error.limit:
                return ErrorClassification(
                    severity=ErrorSeverity.FATAL,
                    error_type="extreme_memory_pressure",
                    source=error.resource_id,
                    impact_score=0.9,
                    requires_intervention=True,
                    recovery_strategy="emergency_cleanup"
                )
            # Standard classification
            return ErrorClassification(
                severity=ErrorSeverity.FATAL if error.impact_score > 0.8 else ErrorSeverity.DEGRADED,
                error_type="resource_exhaustion",
                source=error.resource_id,
                impact_score=error.impact_score,
                requires_intervention=getattr(error, 'requires_intervention', False),
                recovery_strategy=getattr(error, 'recovery_strategy', None)
            )
        
        # Check if the error is a ResourceTimeoutError by checking for required attributes
        is_timeout_error = (
            hasattr(error, 'operation') and
            hasattr(error, 'resource_id') and
            hasattr(error, 'timeout_seconds')
        )
        
        if is_timeout_error:
            # Special handling for lock timeouts
            if "lock_acquisition" in error.operation:
                # Check if context and details are available
                lock_type = "unknown"
                if hasattr(error, 'context') and hasattr(error.context, 'details'):
                    lock_type = getattr(error.context.details, "lock_type", "unknown")
                
                if lock_type == "write":
                    # Writing locks are more critical
                    return ErrorClassification(
                        severity=ErrorSeverity.DEGRADED,
                        error_type="lock_timeout",
                        source=error.resource_id,
                        impact_score=0.7,  # Higher impact
                        requires_intervention=False,
                        recovery_strategy="restart_component"
                    )
                else:
                    # Read locks less critical
                    return ErrorClassification(
                        severity=ErrorSeverity.TRANSIENT,
                        error_type="lock_timeout",
                        source=error.resource_id,
                        impact_score=0.4,
                        requires_intervention=False,
                        recovery_strategy="retry_with_backoff"
                    )
            
            # Standard timeout classification
            return ErrorClassification(
                severity=ErrorSeverity.TRANSIENT,
                error_type="timeout",
                source=error.resource_id,
                impact_score=0.5,
                requires_intervention=False,
                recovery_strategy="retry_with_backoff"
            )
            
        # Default classification for unknown errors
        return ErrorClassification(
            severity=ErrorSeverity.DEGRADED,
            error_type="unknown",
            source=context.get("source", "unknown") if context else "unknown",
            impact_score=0.7,
            requires_intervention=True,
            recovery_strategy="manual_intervention_required"
        )

    async def track_recovery(self,
                           error_id: str,
                           success: bool,
                           recovery_info: Optional[Dict[str, Any]] = None) -> None:
        """Track recovery attempt results with enhanced reporting and thread safety"""
        # Ensure recovery_info is a dictionary
        if recovery_info is None:
            recovery_info = {}
            
        # Add timestamp for event correlation
        recovery_info["timestamp"] = datetime.now().isoformat()
        
        # Thread-safe error count access and updates
        if success:
            # Reset error count on successful recovery and get previous count
            with self._lock:
                previous_attempts = self._error_counts.get(error_id, 0)
                self._error_counts[error_id] = 0
            
            # Prepare event data with detailed information
            event_data = {
                "error_id": error_id,
                "status": "recovered",
                "recovery_info": recovery_info,
                "previous_attempts": previous_attempts
            }
            
            # Emit recovery events
            try:
                await self._event_queue.emit(
                    "error_occurred",  # Use string instead of enum
                    event_data
                )
                
                await self._event_queue.emit(
                    "resource_error_resolved",  # Use string instead of enum
                    event_data
                )
                
                # For successful recoveries, also emit to RESOURCE_ERROR_RECOVERY_COMPLETED
                await self._event_queue.emit(
                    "resource_error_recovery_completed",  # Use string instead of enum
                    event_data
                )
                
            except Exception as e:
                logger.error(f"Failed to emit recovery events: {str(e)}")
                
        else:
            # Thread-safe access to current attempts count
            with self._lock:
                current_attempts = self._error_counts.get(error_id, 0)
            
            # Prepare event data with detailed information
            event_data = {
                "error_id": error_id,
                "status": "recovery_failed",
                "attempt": current_attempts,
                "recovery_info": recovery_info,
                "recovery_strategy": recovery_info.get("strategy", "unknown")
            }
            
            # Emit to both event types for compatibility
            try:
                await self._event_queue.emit(
                    "error_occurred",  # Use string instead of enum
                    event_data
                )
                
                await self._event_queue.emit(
                    "resource_error_recovery_started",  # Use string instead of enum
                    event_data
                )
                
                # For failed recoveries, we'll emit a different event 
                # if we've reached max retries
                if current_attempts >= 3:  # Consider making this configurable
                    await self._event_queue.emit(
                        "resource_alert_created",  # Use string instead of enum
                        {
                            **event_data,
                            "alert_type": "max_recovery_attempts_reached",
                            "severity": "CRITICAL",
                            "message": f"Max recovery attempts reached for error {error_id}"
                        }
                    )
                    
            except Exception as e:
                logger.error(f"Failed to emit failed recovery events: {str(e)}")

    def requires_forced_cleanup(self, error_id: str, threshold: int = 3) -> bool:
        """Check if error frequency requires forced cleanup with thread safety"""
        with self._lock:
            return self._error_counts.get(error_id, 0) >= threshold