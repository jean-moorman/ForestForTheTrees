"""
Forest For The Trees (FFTT) Event System
---------------------------------------
This module is a backward compatibility interface that redirects to the modular implementation
in the events/ directory. For new code, please import directly from resources.events.

Provides a comprehensive event system for communication between components
with prioritization, batching, reliable delivery, and monitoring capabilities.
"""

# Import and re-export all public classes from resources.events
from resources.events import (
    ResourceEventTypes,
    Event,
    EventQueue,
    EventMonitor,
    EventLoopManager,
    ThreadLocalEventLoopStorage,
    get_llm_client
)

# Define exports
__all__ = [
    'ResourceEventTypes',
    'Event',
    'EventQueue',
    'EventMonitor',
    'EventLoopManager',
    'ThreadLocalEventLoopStorage',
    'get_llm_client'
]