from dataclasses import dataclass, field
from resources.common import ErrorSeverity, ResourceType
from datetime import datetime
from typing import Dict, Any, Optional

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