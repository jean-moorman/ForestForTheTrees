"""
Simplified System Error Recovery for FFTT.

This is a simplified version of the SystemErrorRecovery class that avoids circular dependencies
by not importing from resources/ modules that depend on it.
"""

import logging
import json
import traceback
import threading
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Awaitable
from contextlib import asynccontextmanager

# Define error severity enum directly instead of importing
class ErrorSeverity:
    TRANSIENT = "TRANSIENT"
    DEGRADED = "DEGRADED" 
    FATAL = "FATAL"

# Local HealthStatus class to avoid import
class HealthStatus:
    def __init__(self, status, source, description="", metadata=None):
        self.status = status
        self.source = source
        self.description = description
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

# Local ErrorClassification to avoid import
class ErrorClassification:
    """Detailed error classification information"""
    def __init__(self, severity, error_type, source, impact_score, requires_intervention, 
                 recovery_strategy=None, context=None):
        self.severity = severity
        self.error_type = error_type
        self.source = source
        self.impact_score = impact_score  # 0-1 score of operational impact
        self.requires_intervention = requires_intervention
        self.recovery_strategy = recovery_strategy
        self.timestamp = datetime.now()
        self.context = context or {}

logger = logging.getLogger(__name__)

class SimpleErrorHandler:
    """Simple error handler that can be used without circular dependencies."""
    
    def __init__(self, event_queue=None):
        """Initialize the error handler with optional event queue."""
        self._event_queue = event_queue
        self._error_counts = {}
        
    async def handle_error(self, error, component_id, operation, context=None):
        """Handle an error and classify it."""
        # Track error counts
        error_key = f"{component_id}:{operation}"
        self._error_counts[error_key] = self._error_counts.get(error_key, 0) + 1
        
        # Simple severity classification based on error type and count
        if self._error_counts[error_key] > 5:
            severity = ErrorSeverity.FATAL
            impact_score = 0.9
            requires_intervention = True
        elif self._error_counts[error_key] > 2:
            severity = ErrorSeverity.DEGRADED
            impact_score = 0.5
            requires_intervention = False
        else:
            severity = ErrorSeverity.TRANSIENT
            impact_score = 0.2
            requires_intervention = False
            
        # Get recovery strategy if any
        recovery_strategy = getattr(error, 'recovery_strategy', None)
        
        # Classify the error
        classification = ErrorClassification(
            severity=severity,
            error_type=type(error).__name__,
            source=component_id,
            impact_score=impact_score,
            requires_intervention=requires_intervention,
            recovery_strategy=recovery_strategy,
            context=context
        )
        
        # Emit event if queue is available
        if self._event_queue:
            try:
                await self._event_queue.emit(
                    "error_occurred",
                    {
                        "component_id": component_id,
                        "operation": operation,
                        "error_type": type(error).__name__,
                        "severity": severity,
                        "message": str(error),
                        "timestamp": datetime.now().isoformat(),
                        "requires_intervention": requires_intervention,
                        "recovery_strategy": recovery_strategy
                    }
                )
            except Exception as e:
                logger.error(f"Failed to emit error event: {str(e)}")
                
        return classification
        
    def requires_forced_cleanup(self, error_key):
        """Check if forced cleanup is required based on error history."""
        return self._error_counts.get(error_key, 0) > 3

class SystemErrorRecoverySimple:
    """Simple system error recovery implementation to avoid circular dependencies."""
    
    def __init__(self, event_queue=None, health_tracker=None, system_monitor=None, state_manager=None):
        """Initialize with minimal dependencies to avoid circular imports."""
        self._event_queue = event_queue
        self._health_tracker = health_tracker
        self._system_monitor = system_monitor
        self._state_manager = state_manager
        
        # Create a simple error handler instead of importing the full one
        self._error_handler = SimpleErrorHandler(event_queue)
        
        # No other complex components to avoid circular dependencies
        self._running = False
        
    async def start(self):
        """Start the system error recovery service."""
        if self._running:
            return
            
        self._running = True
        logger.info("Simple system error recovery service started")
        
    async def stop(self):
        """Stop the system error recovery service."""
        self._running = False
        logger.info("Simple system error recovery service stopped")
        
    @asynccontextmanager
    async def start_session(self):
        """Context manager for a system error recovery session.
        
        Usage:
            async with system_error_recovery.start_session():
                # Recovery service is active
                # Do work here
            # Recovery service is stopped
        """
        try:
            await self.start()
            yield self
        finally:
            await self.stop()
        
    async def handle_operation_error(self, 
                                   error, 
                                   operation, 
                                   component_id, 
                                   cleanup_callback=None):
        """Handle an operation error with minimal dependencies."""
        try:
            # Generate correlation ID for tracking related errors
            import uuid
            correlation_id = str(uuid.uuid4())
            
            # Use error handler to classify the error
            classification = await self._error_handler.handle_error(
                error=error,
                component_id=component_id,
                operation=operation,
                context={
                    "component_type": component_id,
                    "correlation_id": correlation_id,
                    "thread_id": threading.get_ident(),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Update health status if available
            if self._health_tracker:
                await self._health_tracker.update_health(
                    component_id,
                    HealthStatus(
                        status="CRITICAL" if classification.severity == ErrorSeverity.FATAL else "DEGRADED",
                        source=component_id,
                        description=f"Error in operation {operation}: {str(error)}",
                        metadata={
                            "error_type": classification.error_type,
                            "severity": classification.severity,
                            "operation": operation,
                            "correlation_id": correlation_id
                        }
                    )
                )
                
            # Emit error event in a standardized format
            if self._event_queue:
                try:
                    error_data = {
                        "component_id": component_id,
                        "operation": operation,
                        "error_type": classification.error_type,
                        "severity": classification.severity,
                        "message": str(error),
                        "timestamp": datetime.now().isoformat(),
                        "correlation_id": correlation_id,
                        "thread_id": threading.get_ident(),
                        "context": {
                            "component_type": component_id,
                            "stacktrace": self._get_error_traceback(error)
                        }
                    }
                    
                    await self._event_queue.emit(
                        "resource_error_occurred",
                        error_data,
                        priority="high"
                    )
                except Exception as e:
                    logger.error(f"Failed to emit error event: {str(e)}")
                    
            # Implement recovery strategy if specified
            if hasattr(error, 'recovery_strategy') and error.recovery_strategy:
                await self.implement_recovery_strategy(error, component_id, cleanup_callback)
                
            # Check if cleanup needed based on severity
            if (classification.severity == ErrorSeverity.FATAL or 
                self._error_handler.requires_forced_cleanup(f"{component_id}:{operation}")):
                
                # Call cleanup callback if provided
                if cleanup_callback:
                    await cleanup_callback(True)  # True indicates forced cleanup
                    
            return classification
            
        except Exception as e:
            # Ensure errors in error handling don't propagate
            logger.error(f"Error handling failed: {str(e)}")
            if hasattr(e, "__traceback__"):
                logger.error(traceback.format_exc())
            return ErrorClassification(
                severity=ErrorSeverity.FATAL,
                error_type=type(error).__name__,
                source=component_id,
                impact_score=1.0,
                requires_intervention=True,
                recovery_strategy=None,
                context={"error_in_error_handling": True}
            )
    
    def _get_error_traceback(self, error):
        """Get formatted traceback for an error if available."""
        try:
            tb = getattr(error, '__traceback__', None)
            if tb:
                return ''.join(traceback.format_tb(tb))
            return "No traceback available"
        except Exception:
            return "Error getting traceback"
            
    async def implement_recovery_strategy(self, error, component_id, cleanup_callback=None):
        """Implement basic recovery strategies."""
        if not hasattr(error, 'recovery_strategy') or not error.recovery_strategy:
            return False
            
        # Get error identifier
        error_id = f"{component_id}:{getattr(error, 'operation', 'unknown')}"
        
        strategy = error.recovery_strategy
        logger.info(f"Implementing recovery strategy '{strategy}' for error: {error}")
        
        try:
            # Handle basic strategies
            if strategy == "force_cleanup":
                # Execute the force cleanup
                if cleanup_callback:
                    await cleanup_callback(True)  # True indicates forced cleanup
                return True
                
            elif strategy == "retry_with_backoff":
                # Just acknowledge the strategy - actual retry happens elsewhere
                return True
                
            elif strategy == "reduce_load":
                # Basic load reduction - just cleaning up non-essential resources
                if cleanup_callback:
                    await cleanup_callback(False)  # False for non-forced cleanup
                return True
                
            elif strategy == "restart_component":
                # Aggressive cleanup and inform monitoring system
                if cleanup_callback:
                    await cleanup_callback(True)  # True for forced cleanup
                
                # Emit restart event
                if self._event_queue:
                    try:
                        await self._event_queue.emit(
                            "component_restart_requested",
                            {
                                "component_id": component_id,
                                "reason": str(error),
                                "timestamp": datetime.now().isoformat()
                            }
                        )
                    except Exception:
                        pass
                        
                return True
                
            elif strategy == "manual_intervention_required":
                # Emit alert event
                if self._event_queue:
                    try:
                        await self._event_queue.emit(
                            "manual_intervention_required",
                            {
                                "component_id": component_id,
                                "error": str(error),
                                "timestamp": datetime.now().isoformat()
                            }
                        )
                    except Exception:
                        pass
                        
                # This strategy always returns False as it requires human action
                return False
                
            else:
                logger.warning(f"Unknown recovery strategy: {strategy}")
                return False
                
        except Exception as e:
            logger.error(f"Error implementing recovery strategy: {str(e)}")
            return False
            
    async def get_recovery_recommendation(self, error_context):
        """Provide a basic recovery recommendation."""
        # This is a very simple implementation without LLM integration
        error_type = error_context.get("error_type", "unknown")
        component_id = error_context.get("component_id", "unknown")
        
        # Simple decision tree based on error type
        if "MemoryError" in error_type or "OutOfMemory" in error_type:
            strategy = "force_cleanup"
        elif "Timeout" in error_type:
            strategy = "retry_with_backoff"
        elif "ConnectionError" in error_type or "NetworkError" in error_type:
            strategy = "retry_with_backoff"
        elif "State" in error_type or "Corruption" in error_type:
            strategy = "restart_component"
        elif "Fatal" in error_type or "Critical" in error_type:
            strategy = "manual_intervention_required"
        else:
            # Default strategy
            strategy = "reduce_load"
            
        return {
            "recommended_action": strategy,
            "required_components": [component_id],
            "fallback_action": "manual_intervention_required",
            "decision_context": {
                "primary_trigger": f"{error_type} in component {component_id}",
                "contributing_factors": [],
                "risk_assessment": "Medium risk",
                "success_likelihood": 0.7
            }
        }

# Ensure this module can be imported without circular dependencies  
__all__ = ['SystemErrorRecoverySimple', 'ErrorSeverity', 'HealthStatus', 'ErrorClassification']