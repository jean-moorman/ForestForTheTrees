"""
Forest For The Trees (FFTT) Event System
---------------------------------------
Provides a comprehensive event system for communication between components
with prioritization, batching, reliable delivery, and monitoring capabilities.
"""
# Re-export all public symbols for backward compatibility
from .types import ResourceEventTypes, Event
from .queue import EventQueue
from .monitoring import EventMonitor
from .loop_management import EventLoopManager, ThreadLocalEventLoopStorage
from .utils import get_llm_client

# Public API
__all__ = [
    'ResourceEventTypes',
    'Event',
    'EventQueue',
    'EventMonitor',
    'EventLoopManager',
    'ThreadLocalEventLoopStorage',
    'get_llm_client',
]