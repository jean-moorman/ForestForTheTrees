"""
Event system monitoring and tracing for debugging and analysis.

This module provides tools for monitoring event system health metrics
and tracing event flows for debugging purposes.
"""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Callable, Awaitable

from resources.events import EventQueue, ResourceEventTypes

logger = logging.getLogger(__name__)

@dataclass
class EventSystemHealth:
    """Health metrics for the event system."""
    event_counts: Dict[str, int]  # Counts by event type
    emission_rates: Dict[str, float]  # Events per second by type
    queue_sizes: Dict[str, int]  # Queue sizes by priority
    delivery_times: Dict[str, float]  # Average delivery time by type
    error_rates: Dict[str, float]  # Error rates by type
    current_subscribers: Dict[str, int]  # Subscriber counts by type
    
    def summary(self) -> Dict[str, Any]:
        """Get a summary of the health metrics."""
        return {
            "total_events_processed": sum(self.event_counts.values()),
            "event_types": len(self.event_counts),
            "max_emission_rate": max(self.emission_rates.values()) if self.emission_rates else 0,
            "queue_status": {
                "high": self.queue_sizes.get("high", 0),
                "normal": self.queue_sizes.get("normal", 0),
                "low": self.queue_sizes.get("low", 0)
            },
            "avg_delivery_time": sum(self.delivery_times.values()) / len(self.delivery_times) if self.delivery_times else 0,
            "total_subscribers": sum(self.current_subscribers.values()),
            "busy_event_types": sorted(self.event_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        }

class EventSystemMonitor:
    """Monitor for the event system health and metrics."""
    
    def __init__(self, event_queue: EventQueue):
        self.event_queue = event_queue
        self._event_counts = {}
        self._emission_timestamps = {}
        self._delivery_times = {}
        self._error_counts = {}
        self._active = False
        self._monitoring_task = None
        self._sample_window = 100  # Number of events to keep for rate calculation
        self._last_health_check = datetime.now()
        self._health_check_interval = 60  # seconds
        
    async def start_monitoring(self):
        """Start monitoring the event system."""
        if self._active:
            return
            
        self._active = True
        
        # Subscribe to all events (using wildcard)
        await self.event_queue.subscribe("*", self._handle_any_event)
        
        # Subscribe to specific error events for error tracking
        await self.event_queue.subscribe(
            ResourceEventTypes.ERROR_OCCURRED.value, 
            self._handle_error_event
        )
        await self.event_queue.subscribe(
            ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value, 
            self._handle_error_event
        )
        
        # Start background health check task
        self._monitoring_task = asyncio.create_task(self._periodic_health_check())
        logger.info("Event system monitoring started")
        
    async def stop_monitoring(self):
        """Stop monitoring the event system."""
        if not self._active:
            return
            
        self._active = False
        
        # Unsubscribe from events
        await self.event_queue.unsubscribe("*", self._handle_any_event)
        await self.event_queue.unsubscribe(
            ResourceEventTypes.ERROR_OCCURRED.value, 
            self._handle_error_event
        )
        await self.event_queue.unsubscribe(
            ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value, 
            self._handle_error_event
        )
        
        # Cancel monitoring task
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
                
        logger.info("Event system monitoring stopped")
            
    async def _periodic_health_check(self):
        """Periodically check and record event system health."""
        while self._active:
            try:
                # Get current health metrics
                health_metrics = self.get_health_metrics()
                
                # Emit health event
                await self.event_queue.emit(
                    ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value,
                    {
                        "component": "event_system",
                        "status": "HEALTHY",  # Default to healthy
                        "description": "Event system health check",
                        "metrics": health_metrics.summary()
                    }
                )
                
                # Check for warning conditions
                high_queue_size = health_metrics.queue_sizes.get("high", 0)
                normal_queue_size = health_metrics.queue_sizes.get("normal", 0)
                
                if high_queue_size > 100 or normal_queue_size > 500:
                    logger.warning(f"Event queue saturation: high={high_queue_size}, normal={normal_queue_size}")
                    
                    # Emit warning event
                    await self.event_queue.emit(
                        ResourceEventTypes.RESOURCE_ALERT_CREATED.value,
                        {
                            "alert_type": "event_queue_saturation",
                            "level": "WARNING",
                            "description": f"Event queue saturation detected: high={high_queue_size}, normal={normal_queue_size}",
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                    
            except Exception as e:
                logger.error(f"Error in event system health check: {e}")
                
            # Wait for next check interval
            self._last_health_check = datetime.now()
            await asyncio.sleep(self._health_check_interval)
            
    async def _handle_any_event(self, event_type: str, data: Dict[str, Any]):
        """Record metrics for any event."""
        if not self._active:
            return
            
        # Skip monitoring events to avoid recursion
        if event_type == ResourceEventTypes.SYSTEM_HEALTH_CHANGED.value:
            return
            
        # Update counts
        self._event_counts[event_type] = self._event_counts.get(event_type, 0) + 1
        
        # Record timestamp for rate calculation
        if event_type not in self._emission_timestamps:
            self._emission_timestamps[event_type] = []
            
        self._emission_timestamps[event_type].append(datetime.now())
        
        # Limit history size
        if len(self._emission_timestamps[event_type]) > self._sample_window:
            self._emission_timestamps[event_type] = self._emission_timestamps[event_type][-self._sample_window:]
            
        # Record delivery time if available
        if "delivery_time" in data:
            if event_type not in self._delivery_times:
                self._delivery_times[event_type] = []
                
            self._delivery_times[event_type].append(data["delivery_time"])
            
            # Limit history size
            if len(self._delivery_times[event_type]) > self._sample_window:
                self._delivery_times[event_type] = self._delivery_times[event_type][-self._sample_window:]
        
    async def _handle_error_event(self, event_type: str, data: Dict[str, Any]):
        """Record error metrics."""
        if not self._active:
            return
            
        # Extract the source event type if available
        source_event = data.get("event_type", "unknown")
        
        # Update error counts
        self._error_counts[source_event] = self._error_counts.get(source_event, 0) + 1
        
    def get_health_metrics(self) -> EventSystemHealth:
        """Get current health metrics."""
        # Calculate emission rates
        emission_rates = {}
        for event_type, timestamps in self._emission_timestamps.items():
            if len(timestamps) >= 2:
                # Calculate events per second over the sample window
                time_span = (timestamps[-1] - timestamps[0]).total_seconds()
                if time_span > 0:
                    emission_rates[event_type] = len(timestamps) / time_span
        
        # Get queue sizes
        queue_sizes = {
            "high": self.event_queue.high_priority_queue.qsize() if hasattr(self.event_queue, 'high_priority_queue') else 0,
            "normal": self.event_queue.normal_priority_queue.qsize() if hasattr(self.event_queue, 'normal_priority_queue') else 0,
            "low": self.event_queue.low_priority_queue.qsize() if hasattr(self.event_queue, 'low_priority_queue') else 0
        }
        
        # Get subscriber counts
        subscriber_counts = {}
        for event_type in self._event_counts.keys():
            subscriber_counts[event_type] = len(self.event_queue._subscribers.get(event_type, set()))
        
        # Calculate average delivery times
        avg_delivery_times = {}
        for event_type, times in self._delivery_times.items():
            if times:
                avg_delivery_times[event_type] = sum(times) / len(times)
        
        # Calculate error rates
        error_rates = {}
        for event_type, error_count in self._error_counts.items():
            event_count = self._event_counts.get(event_type, 0)
            if event_count > 0:
                error_rates[event_type] = error_count / event_count
            
        return EventSystemHealth(
            event_counts=dict(self._event_counts),
            emission_rates=emission_rates,
            queue_sizes=queue_sizes,
            delivery_times=avg_delivery_times,
            error_rates=error_rates,
            current_subscribers=subscriber_counts
        )
    
    def reset_metrics(self):
        """Reset all metrics."""
        self._event_counts = {}
        self._emission_timestamps = {}
        self._delivery_times = {}
        self._error_counts = {}


class EventTracer:
    """Event tracing system for debugging and analysis."""
    
    def __init__(self, event_queue: EventQueue):
        self.event_queue = event_queue
        self._traces = {}  # correlation_id -> list of events
        self._active = False
        self._tracked_event_types = set()  # Event types being traced
        self._trace_handlers = {}  # correlation_id -> callback
        self._max_trace_size = 1000  # Maximum events per trace
        self._max_traces = 100  # Maximum number of traces to keep
        
    async def start_tracing(self, event_types: List[str] = None, max_trace_size: int = None):
        """Start tracing events.
        
        Args:
            event_types: Optional list of event types to trace, or None for all
            max_trace_size: Optional maximum number of events per trace
        """
        self._active = True
        
        if max_trace_size is not None:
            self._max_trace_size = max_trace_size
        
        # Subscribe to specific events or all events
        if event_types:
            self._tracked_event_types = set(event_types)
            for event_type in event_types:
                await self.event_queue.subscribe(event_type, self._handle_traced_event)
        else:
            # Use wildcard to trace all events
            await self.event_queue.subscribe("*", self._handle_traced_event)
            
        logger.info(f"Event tracing started for {len(event_types) if event_types else 'all'} event types")
            
    async def stop_tracing(self):
        """Stop tracing events."""
        if not self._active:
            return
            
        self._active = False
        
        # Unsubscribe from all tracked events
        if self._tracked_event_types:
            for event_type in self._tracked_event_types:
                await self.event_queue.unsubscribe(event_type, self._handle_traced_event)
        else:
            # Unsubscribe from wildcard
            await self.event_queue.unsubscribe("*", self._handle_traced_event)
            
        logger.info("Event tracing stopped")
        
    async def _handle_traced_event(self, event_type: str, data: Dict[str, Any]):
        """Record traced event."""
        if not self._active:
            return
            
        # Get correlation ID
        correlation_id = data.get("correlation_id", "untracked")
        
        # Initialize trace if needed
        if correlation_id not in self._traces:
            # Limit number of traces
            if len(self._traces) >= self._max_traces:
                # Remove oldest trace
                oldest_id = next(iter(self._traces))
                del self._traces[oldest_id]
                
            self._traces[correlation_id] = []
            
        # Add event to trace
        self._traces[correlation_id].append({
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        })
        
        # Limit trace size
        if len(self._traces[correlation_id]) > self._max_trace_size:
            self._traces[correlation_id] = self._traces[correlation_id][-self._max_trace_size:]
            
        # Call any registered handlers for this correlation ID
        if correlation_id in self._trace_handlers:
            try:
                await self._trace_handlers[correlation_id](event_type, data)
            except Exception as e:
                logger.error(f"Error in trace handler for {correlation_id}: {e}")
        
    def get_trace(self, correlation_id: str) -> List[Dict[str, Any]]:
        """Get trace for a specific correlation ID."""
        return self._traces.get(correlation_id, [])
        
    def get_traces(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all traces."""
        return dict(self._traces)
        
    def clear_traces(self):
        """Clear all traces."""
        self._traces = {}
        
    async def register_trace_handler(
        self, 
        correlation_id: str, 
        handler: Callable[[str, Dict[str, Any]], Awaitable[None]]
    ):
        """Register a handler for a specific trace.
        
        This allows for real-time handling of events in a specific trace.
        
        Args:
            correlation_id: The correlation ID to handle
            handler: Async callback that takes (event_type, data)
        """
        self._trace_handlers[correlation_id] = handler
        
    async def unregister_trace_handler(self, correlation_id: str):
        """Unregister a trace handler."""
        if correlation_id in self._trace_handlers:
            del self._trace_handlers[correlation_id]


class EventProtocolValidator:
    """Tool for validating event protocol compliance."""
    
    def __init__(self):
        self._validation_results = {}
        
    @staticmethod
    async def validate_component_protocol(
        component_name: str, 
        event_registry: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate a component's protocol compliance.
        
        Args:
            component_name: The name of the component to validate
            event_registry: The event registry
            
        Returns:
            Dict with validation results including any issues
        """
        from resources.event_registry import EventRegistry
        
        # Get events published by this component
        published_events = EventRegistry.get_events_by_publisher(component_name)
        
        # Get events subscribed to by this component
        subscribed_events = EventRegistry.get_events_by_subscriber(component_name)
        
        # Look for code references to validate implementation
        import os
        import glob
        
        component_files = []
        for pattern in [f"{component_name}/*.py", f"{component_name}/**/*.py"]:
            component_files.extend(glob.glob(pattern, recursive=True))
        
        # Check for event emission
        emission_implementations = {}
        for event_type in published_events:
            implemented = False
            for file_path in component_files:
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        if f'"{event_type}"' in content or f"'{event_type}'" in content:
                            implemented = True
                            emission_implementations[event_type] = file_path
                            break
                except (IOError, UnicodeDecodeError):
                    # Skip binary or inaccessible files
                    continue
            
            if not implemented:
                emission_implementations[event_type] = None
        
        # Check for event subscription
        subscription_implementations = {}
        for event_type in subscribed_events:
            implemented = False
            for file_path in component_files:
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        subscription_pattern = f'subscribe.*"{event_type}"'
                        if subscription_pattern in content or f"subscribe.*'{event_type}'" in content:
                            implemented = True
                            subscription_implementations[event_type] = file_path
                            break
                except (IOError, UnicodeDecodeError):
                    # Skip binary or inaccessible files
                    continue
            
            if not implemented:
                subscription_implementations[event_type] = None
        
        return {
            "component": component_name,
            "published_events": published_events,
            "subscribed_events": subscribed_events,
            "emission_implementations": emission_implementations,
            "subscription_implementations": subscription_implementations,
            "issues": {
                "missing_emission_implementations": [
                    event_type for event_type, file_path in emission_implementations.items()
                    if file_path is None
                ],
                "missing_subscription_implementations": [
                    event_type for event_type, file_path in subscription_implementations.items()
                    if file_path is None
                ]
            }
        }
        
    @staticmethod
    async def validate_event_schemas():
        """Validate all event schemas against the event registry.
        
        Returns:
            Dict with validation results
        """
        from resources.event_registry import EventRegistry
        from resources.events import ResourceEventTypes
        
        # Get all event types
        all_event_types = [event_type.value for event_type in ResourceEventTypes]
        
        # Get registered event types
        registered_event_types = EventRegistry.get_all_event_types()
        
        # Find unregistered events
        unregistered_events = [
            event_type for event_type in all_event_types
            if event_type not in registered_event_types
        ]
        
        # Check for schema coverage
        schema_coverage = {}
        for event_type in registered_event_types:
            metadata = EventRegistry.get_event_metadata(event_type)
            schema_coverage[event_type] = metadata.schema_class is not None if metadata else False
        
        # Find events without schemas
        events_without_schemas = [
            event_type for event_type, has_schema in schema_coverage.items()
            if not has_schema
        ]
        
        return {
            "total_event_types": len(all_event_types),
            "registered_events": len(registered_event_types),
            "unregistered_events": unregistered_events,
            "schema_coverage": sum(1 for has_schema in schema_coverage.values() if has_schema) / len(schema_coverage) if schema_coverage else 0,
            "events_without_schemas": events_without_schemas
        }