"""
Async diagnostics and monitoring for FFTT.

This module provides tools for monitoring and diagnosing async-related
issues, particularly event loop problems and qasync integration issues.
"""

import asyncio
import functools
import logging
import threading
import time
import traceback
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

from resources.events.loop_management import EventLoopManager
from resources.events.qasync_utils import get_qasync_compatible_loop

logger = logging.getLogger(__name__)


@dataclass
class AsyncEvent:
    """Record of an async-related event for diagnostics."""
    timestamp: datetime
    event_type: str
    thread_id: int
    loop_id: Optional[int]
    operation: str
    success: bool
    duration: Optional[float] = None
    error: Optional[str] = None
    stack_trace: Optional[str] = None


@dataclass
class LoopHealthMetrics:
    """Health metrics for an event loop."""
    loop_id: int
    thread_id: int
    loop_type: str  # 'main', 'background', 'unknown'
    is_running: bool
    is_closed: bool
    task_count: int
    last_activity: datetime
    error_count: int = 0
    total_operations: int = 0
    avg_operation_time: float = 0.0


class AsyncDiagnostics:
    """
    Diagnostics and monitoring for async operations.
    
    This class tracks async operations, event loop health, and can
    diagnose common issues like event loop mismatches.
    """
    
    def __init__(self, max_events: int = 1000):
        self.max_events = max_events
        self.events: deque[AsyncEvent] = deque(maxlen=max_events)
        self.loop_metrics: Dict[int, LoopHealthMetrics] = {}
        self.operation_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'success_count': 0,
            'total_time': 0.0,
            'errors': []
        })
        self._lock = threading.RLock()
        
    def record_event(
        self,
        event_type: str,
        operation: str,
        success: bool,
        duration: Optional[float] = None,
        error: Optional[Exception] = None
    ) -> None:
        """Record an async event for diagnostics."""
        with self._lock:
            # Get current context
            thread_id = threading.get_ident()
            loop_id = None
            stack_trace = None
            
            try:
                loop = asyncio.get_running_loop()
                loop_id = id(loop)
            except RuntimeError:
                pass
                
            if error:
                stack_trace = traceback.format_exc()
                
            event = AsyncEvent(
                timestamp=datetime.now(),
                event_type=event_type,
                thread_id=thread_id,
                loop_id=loop_id,
                operation=operation,
                success=success,
                duration=duration,
                error=str(error) if error else None,
                stack_trace=stack_trace
            )
            
            self.events.append(event)
            
            # Update operation stats
            stats = self.operation_stats[operation]
            stats['count'] += 1
            if success:
                stats['success_count'] += 1
            if duration:
                stats['total_time'] += duration
            if error:
                stats['errors'].append(str(error))
                # Keep only last 10 errors to prevent memory growth
                stats['errors'] = stats['errors'][-10:]
                
    def update_loop_metrics(self) -> None:
        """Update health metrics for all known event loops."""
        with self._lock:
            current_time = datetime.now()
            
            # Check main loop
            main_loop = EventLoopManager.get_primary_loop()
            if main_loop:
                self._update_single_loop_metrics(main_loop, "main", current_time)
                
            # Check background loop
            bg_loop = EventLoopManager.get_background_loop()
            if bg_loop:
                self._update_single_loop_metrics(bg_loop, "background", current_time)
                
    def _update_single_loop_metrics(
        self, 
        loop: asyncio.AbstractEventLoop, 
        loop_type: str,
        timestamp: datetime
    ) -> None:
        """Update metrics for a single event loop."""
        loop_id = id(loop)
        
        # Get or create metrics
        if loop_id not in self.loop_metrics:
            self.loop_metrics[loop_id] = LoopHealthMetrics(
                loop_id=loop_id,
                thread_id=0,  # Will update below
                loop_type=loop_type,
                is_running=False,
                is_closed=False,
                task_count=0,
                last_activity=timestamp
            )
            
        metrics = self.loop_metrics[loop_id]
        
        # Update basic status
        metrics.is_closed = loop.is_closed()
        metrics.is_running = loop.is_running()
        
        # Get task count
        try:
            all_tasks = asyncio.all_tasks(loop)
            metrics.task_count = len(all_tasks)
        except Exception:
            metrics.task_count = -1  # Unknown
            
        metrics.last_activity = timestamp
        
    def diagnose_event_loop_issues(self) -> List[str]:
        """
        Diagnose potential event loop issues based on recorded events.
        
        Returns:
            List of diagnostic messages describing potential issues
        """
        issues = []
        
        with self._lock:
            self.update_loop_metrics()
            
            # Check for "no running event loop" errors
            loop_errors = [e for e in self.events if e.error and "no running event loop" in e.error]
            if loop_errors:
                issues.append(f"Found {len(loop_errors)} 'no running event loop' errors")
                
                # Analyze patterns
                error_threads = set(e.thread_id for e in loop_errors)
                issues.append(f"Loop errors occurred in {len(error_threads)} different threads")
                
            # Check for closed/missing loops
            for loop_id, metrics in self.loop_metrics.items():
                if metrics.is_closed:
                    issues.append(f"Loop {loop_id} ({metrics.loop_type}) is closed but still referenced")
                    
                if not metrics.is_running and metrics.loop_type == "main":
                    issues.append(f"Main loop {loop_id} is not running")
                    
            # Check for timeout patterns
            timeout_events = [e for e in self.events if e.error and "timeout" in e.error.lower()]
            if len(timeout_events) > 5:
                issues.append(f"High number of timeout events: {len(timeout_events)}")
                
            # Check for qasync compatibility issues
            main_loop = EventLoopManager.get_primary_loop()
            if main_loop:
                try:
                    compatible_loop = get_qasync_compatible_loop()
                    if compatible_loop != main_loop:
                        issues.append("qasync compatibility loop differs from registered main loop")
                except Exception as e:
                    issues.append(f"qasync compatibility check failed: {e}")
                    
        return issues
        
    def get_operation_summary(self) -> Dict[str, Any]:
        """Get summary of operation statistics."""
        with self._lock:
            summary = {}
            
            for operation, stats in self.operation_stats.items():
                count = stats['count']
                success_count = stats['success_count']
                total_time = stats['total_time']
                
                summary[operation] = {
                    'total_operations': count,
                    'success_rate': success_count / count if count > 0 else 0.0,
                    'avg_time': total_time / count if count > 0 else 0.0,
                    'error_count': count - success_count,
                    'recent_errors': stats['errors'][-3:]  # Last 3 errors
                }
                
            return summary
            
    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report."""
        self.update_loop_metrics()
        
        with self._lock:
            return {
                'timestamp': datetime.now().isoformat(),
                'total_events': len(self.events),
                'loop_metrics': {
                    loop_id: {
                        'loop_type': metrics.loop_type,
                        'is_running': metrics.is_running,
                        'is_closed': metrics.is_closed,
                        'task_count': metrics.task_count,
                        'last_activity': metrics.last_activity.isoformat()
                    }
                    for loop_id, metrics in self.loop_metrics.items()
                },
                'operation_summary': self.get_operation_summary(),
                'issues': self.diagnose_event_loop_issues(),
                'recent_events': [
                    {
                        'timestamp': event.timestamp.isoformat(),
                        'type': event.event_type,
                        'operation': event.operation,
                        'success': event.success,
                        'error': event.error
                    }
                    for event in list(self.events)[-10:]  # Last 10 events
                ]
            }


def async_monitor(operation_name: str):
    """
    Decorator to monitor async operations for diagnostics.
    
    Usage:
        @async_monitor("agent_processing")
        async def process_agent_request():
            # ... operation code ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            error = None
            
            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                error = e
                raise
            finally:
                duration = time.time() - start_time
                diagnostics.record_event(
                    event_type="operation",
                    operation=operation_name,
                    success=success,
                    duration=duration,
                    error=error
                )
                
        return wrapper
    return decorator


# Global diagnostics instance
diagnostics = AsyncDiagnostics()


def log_async_health_report():
    """Log a comprehensive async health report."""
    report = diagnostics.get_health_report()
    
    logger.info("=== Async Health Report ===")
    logger.info(f"Total events recorded: {report['total_events']}")
    
    for loop_id, metrics in report['loop_metrics'].items():
        logger.info(f"Loop {loop_id} ({metrics['loop_type']}): "
                   f"running={metrics['is_running']}, "
                   f"closed={metrics['is_closed']}, "
                   f"tasks={metrics['task_count']}")
                   
    if report['issues']:
        logger.warning("Issues detected:")
        for issue in report['issues']:
            logger.warning(f"  - {issue}")
    else:
        logger.info("No issues detected")
        
    # Log operation summary
    for operation, stats in report['operation_summary'].items():
        logger.info(f"Operation {operation}: "
                   f"{stats['total_operations']} ops, "
                   f"{stats['success_rate']:.1%} success rate, "
                   f"{stats['avg_time']:.3f}s avg time")


__all__ = [
    'AsyncEvent',
    'LoopHealthMetrics', 
    'AsyncDiagnostics',
    'async_monitor',
    'diagnostics',
    'log_async_health_report'
]