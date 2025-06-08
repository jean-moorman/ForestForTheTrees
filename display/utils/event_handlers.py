"""
Event handling utilities for the display system.
"""
import asyncio
import logging
import weakref
from typing import Dict, Any, Callable, List, Tuple

from resources import ResourceEventTypes

logger = logging.getLogger(__name__)


class EventHandlerMixin:
    """Mixin class providing safe event handling functionality."""
    
    def __init__(self):
        self._handlers_active = True
        self._weak_self = weakref.ref(self)
        self._registered_handlers: List[Tuple[str, Callable]] = []
    
    def _create_safe_handler(self, method):
        """Create a safe handler that won't fail if the object is being destroyed."""
        async def safe_wrapper(*args, **kwargs):
            # Check if handlers are still active
            if not self._handlers_active:
                logger.debug(f"Handler {method.__name__} called after cleanup, ignoring")
                return
                
            # Check if the weak reference is still valid
            self_ref = self._weak_self()
            if self_ref is None:
                logger.debug(f"Handler {method.__name__} called after object destruction, ignoring")
                return
                
            try:
                # Call the actual handler method
                if asyncio.iscoroutinefunction(method):
                    return await method(*args, **kwargs)
                else:
                    return method(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in safe handler {method.__name__}: {e}")
                return
        
        return safe_wrapper
    
    async def setup_event_subscriptions(self, event_queue) -> None:
        """Set up event subscriptions with safe handler wrappers."""
        subscriptions = [
            (ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value, self._handle_health_change),
            (ResourceEventTypes.RESOURCE_ALERT_CREATED.value, self._handle_resource_alert),
            (ResourceEventTypes.METRIC_RECORDED.value, self._handle_monitoring_status),
            (ResourceEventTypes.ERROR_OCCURRED.value, self._handle_system_error)
        ]
        
        # Subscribe to each event type with safe handler wrappers
        for event_type, handler in subscriptions:
            if hasattr(self, handler.__name__):
                safe_handler = self._create_safe_handler(handler)
                await event_queue.subscribe(event_type, safe_handler)
                # Track the original handler for cleanup
                self._registered_handlers.append((event_type, safe_handler))
    
    async def cleanup_event_subscriptions(self, event_queue) -> None:
        """Clean up event subscriptions."""
        self._handlers_active = False
        
        # Unsubscribe from each event type
        for event_type, handler in self._registered_handlers:
            try:
                await event_queue.unsubscribe(event_type, handler)
            except Exception as e:
                logger.error(f"Error unsubscribing from {event_type}: {e}")
        
        self._registered_handlers.clear()
    
    # Default handlers - to be overridden by implementing classes
    def _handle_health_change(self, event_type: str, data: Dict[str, Any]) -> None:
        """Handle system health change events."""
        pass
    
    def _handle_resource_alert(self, event_type: str, data: Dict[str, Any]) -> None:
        """Handle resource alert events."""
        pass
    
    def _handle_monitoring_status(self, event_type: str, data: Dict[str, Any]) -> None:
        """Handle periodic monitoring status updates."""
        pass
    
    def _handle_system_error(self, event_type: str, data: Dict[str, Any]) -> None:
        """Handle system-level errors."""
        pass