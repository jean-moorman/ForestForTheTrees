"""
Loop Context Validation Utilities

This module provides utilities to validate proper loop context usage in the 
two-loop architecture without mocks. It helps detect and track loop ownership 
violations in real system operation.
"""

import asyncio
import threading
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from resources.events.loop_management import EventLoopManager


@dataclass
class LoopContextViolation:
    """Represents a loop context violation."""
    operation_name: str
    expected_context: str
    actual_loop_id: int
    expected_loop_id: Optional[int]
    thread_id: int
    thread_name: str
    timestamp: datetime
    stack_trace: List[str] = field(default_factory=list)


class LoopContextValidator:
    """
    Utility to validate proper loop context usage in real scenarios.
    
    This validator helps detect when operations are running in the wrong 
    loop context, which can cause the "no running event loop" errors
    and other coordination issues.
    """
    
    def __init__(self):
        self.violations: List[LoopContextViolation] = []
        self._operation_count = 0
        self._validation_enabled = True
    
    def enable_validation(self):
        """Enable context validation."""
        self._validation_enabled = True
    
    def disable_validation(self):
        """Disable context validation."""
        self._validation_enabled = False
    
    def validate_context(self, operation_name: str, expected_context: str) -> bool:
        """
        Validate current operation is in expected loop context.
        
        Args:
            operation_name: Name of the operation being validated
            expected_context: "main", "background", or "any"
            
        Returns:
            True if context is correct, False if violation detected
        """
        if not self._validation_enabled:
            return True
        
        self._operation_count += 1
        
        try:
            current_thread = threading.current_thread()
            thread_id = threading.get_ident()
            
            # Get current running loop
            try:
                current_loop = asyncio.get_running_loop()
                current_loop_id = id(current_loop)
            except RuntimeError:
                # No running loop - this might be a violation depending on context
                if expected_context in ["main", "background"]:
                    self._record_violation(
                        operation_name=operation_name,
                        expected_context=expected_context,
                        actual_loop_id=None,
                        expected_loop_id=None,
                        thread_id=thread_id,
                        thread_name=current_thread.name,
                        error_msg="No running event loop"
                    )
                    return False
                return True
            
            # Determine expected loop based on context
            if expected_context == "main":
                expected_loop = EventLoopManager.get_primary_loop()
                if not expected_loop:
                    # Main loop not registered - might be early in startup
                    return True
                
                expected_loop_id = id(expected_loop)
                
                # Verify we're in main thread
                if current_thread is not threading.main_thread():
                    self._record_violation(
                        operation_name=operation_name,
                        expected_context=expected_context,
                        actual_loop_id=current_loop_id,
                        expected_loop_id=expected_loop_id,
                        thread_id=thread_id,
                        thread_name=current_thread.name,
                        error_msg="Main context operation not in main thread"
                    )
                    return False
                
                # Verify we're in the main/primary loop
                if current_loop_id != expected_loop_id:
                    self._record_violation(
                        operation_name=operation_name,
                        expected_context=expected_context,
                        actual_loop_id=current_loop_id,
                        expected_loop_id=expected_loop_id,
                        thread_id=thread_id,
                        thread_name=current_thread.name,
                        error_msg="Main context operation in wrong loop"
                    )
                    return False
            
            elif expected_context == "background":
                expected_loop = EventLoopManager.get_background_loop()
                if not expected_loop:
                    # Background loop not registered yet
                    return True
                
                expected_loop_id = id(expected_loop)
                
                # Verify we're NOT in main thread
                if current_thread is threading.main_thread():
                    self._record_violation(
                        operation_name=operation_name,
                        expected_context=expected_context,
                        actual_loop_id=current_loop_id,
                        expected_loop_id=expected_loop_id,
                        thread_id=thread_id,
                        thread_name=current_thread.name,
                        error_msg="Background context operation in main thread"
                    )
                    return False
                
                # Verify we're in the background loop
                if current_loop_id != expected_loop_id:
                    self._record_violation(
                        operation_name=operation_name,
                        expected_context=expected_context,
                        actual_loop_id=current_loop_id,
                        expected_loop_id=expected_loop_id,
                        thread_id=thread_id,
                        thread_name=current_thread.name,
                        error_msg="Background context operation in wrong loop"
                    )
                    return False
            
            elif expected_context == "any":
                # Any loop is acceptable
                return True
            
            else:
                raise ValueError(f"Unknown expected_context: {expected_context}")
            
            return True
            
        except Exception as e:
            self._record_violation(
                operation_name=operation_name,
                expected_context=expected_context,
                actual_loop_id=None,
                expected_loop_id=None,
                thread_id=thread_id,
                thread_name=current_thread.name if 'current_thread' in locals() else "unknown",
                error_msg=f"Validation error: {e}"
            )
            return False
    
    def _record_violation(self, operation_name: str, expected_context: str, 
                         actual_loop_id: Optional[int], expected_loop_id: Optional[int],
                         thread_id: int, thread_name: str, error_msg: str):
        """Record a context violation."""
        import traceback
        
        violation = LoopContextViolation(
            operation_name=operation_name,
            expected_context=expected_context,
            actual_loop_id=actual_loop_id or 0,
            expected_loop_id=expected_loop_id,
            thread_id=thread_id,
            thread_name=thread_name,
            timestamp=datetime.now(),
            stack_trace=traceback.format_stack()
        )
        
        self.violations.append(violation)
        
        # Log the violation
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Loop context violation: {error_msg} - {operation_name}")
    
    def assert_no_violations(self):
        """Assert no context violations occurred."""
        if self.violations:
            violation_summary = self._format_violations()
            raise AssertionError(f"Loop context violations detected:\n{violation_summary}")
    
    def get_violations(self) -> List[LoopContextViolation]:
        """Get list of all violations."""
        return self.violations.copy()
    
    def clear_violations(self):
        """Clear all recorded violations."""
        self.violations.clear()
        self._operation_count = 0
    
    def get_violation_summary(self) -> Dict[str, Any]:
        """Get summary of violations."""
        return {
            "total_operations": self._operation_count,
            "violation_count": len(self.violations),
            "violation_rate": len(self.violations) / max(self._operation_count, 1),
            "violations_by_context": self._group_violations_by_context(),
            "violations_by_operation": self._group_violations_by_operation()
        }
    
    def _group_violations_by_context(self) -> Dict[str, int]:
        """Group violations by expected context."""
        context_counts = {}
        for violation in self.violations:
            context = violation.expected_context
            context_counts[context] = context_counts.get(context, 0) + 1
        return context_counts
    
    def _group_violations_by_operation(self) -> Dict[str, int]:
        """Group violations by operation name."""
        operation_counts = {}
        for violation in self.violations:
            operation = violation.operation_name
            operation_counts[operation] = operation_counts.get(operation, 0) + 1
        return operation_counts
    
    def _format_violations(self) -> str:
        """Format violations for display."""
        if not self.violations:
            return "No violations"
        
        lines = [f"Total violations: {len(self.violations)}"]
        for i, violation in enumerate(self.violations, 1):
            lines.append(f"{i}. {violation.operation_name}:")
            lines.append(f"   Expected: {violation.expected_context}")
            lines.append(f"   Thread: {violation.thread_name} ({violation.thread_id})")
            lines.append(f"   Actual loop: {violation.actual_loop_id}")
            lines.append(f"   Expected loop: {violation.expected_loop_id}")
            lines.append(f"   Time: {violation.timestamp}")
            lines.append("")
        
        return "\n".join(lines)


class LoopContextMonitor:
    """
    Monitor for continuous loop context validation during test execution.
    
    This can be used to monitor an entire test suite or application lifecycle
    to detect context violations in real-time.
    """
    
    def __init__(self, validator: Optional[LoopContextValidator] = None):
        self.validator = validator or LoopContextValidator()
        self._monitoring = False
        self._monitor_task = None
        self._operation_log = []
    
    async def start_monitoring(self, check_interval: float = 0.1):
        """Start continuous context monitoring."""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop(check_interval))
    
    async def stop_monitoring(self):
        """Stop continuous context monitoring."""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
    
    async def _monitoring_loop(self, check_interval: float):
        """Continuous monitoring loop."""
        try:
            while self._monitoring:
                # Check current context health
                self._check_current_context()
                await asyncio.sleep(check_interval)
        except asyncio.CancelledError:
            pass
    
    def _check_current_context(self):
        """Check current loop context health."""
        try:
            current_thread = threading.current_thread()
            
            # Check if we're in a running loop
            try:
                current_loop = asyncio.get_running_loop()
                loop_id = id(current_loop)
            except RuntimeError:
                # No running loop in this context
                return
            
            # Determine expected context based on thread
            if current_thread is threading.main_thread():
                expected_context = "main"
            else:
                expected_context = "background"
            
            # Validate context
            operation_name = f"monitor_check_{current_thread.name}"
            self.validator.validate_context(operation_name, expected_context)
            
            # Log operation for analysis
            self._operation_log.append({
                "timestamp": time.time(),
                "thread": current_thread.name,
                "loop_id": loop_id,
                "expected_context": expected_context
            })
            
        except Exception as e:
            # Don't let monitoring errors break the system
            pass
    
    def get_operation_log(self) -> List[Dict[str, Any]]:
        """Get log of monitored operations."""
        return self._operation_log.copy()
    
    def clear_operation_log(self):
        """Clear the operation log."""
        self._operation_log.clear()


# Global validator instance for easy access
_global_validator = LoopContextValidator()

def validate_main_context(operation_name: str) -> bool:
    """Convenience function to validate main context."""
    return _global_validator.validate_context(operation_name, "main")

def validate_background_context(operation_name: str) -> bool:
    """Convenience function to validate background context."""
    return _global_validator.validate_context(operation_name, "background")

def get_global_validator() -> LoopContextValidator:
    """Get the global validator instance."""
    return _global_validator

def reset_global_validator():
    """Reset the global validator."""
    _global_validator.clear_violations()