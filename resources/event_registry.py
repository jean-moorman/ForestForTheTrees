"""
Central registry for system-wide event documentation.

This module provides a central registry for documenting and validating
event types throughout the FFTT system, enabling consistent communication
between components across different phases.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Type, Any

@dataclass
class EventTypeMetadata:
    """Metadata for event types in the central event registry."""
    name: str
    description: str
    publisher_components: List[str]
    subscriber_components: List[str]
    example_payload: Optional[Dict] = None
    schema_class: Optional[Type] = None
    priority: str = "normal"  # "high", "normal", "low"

class EventRegistry:
    """Central registry for system-wide event documentation."""
    _registry: Dict[str, EventTypeMetadata] = {}
    
    @classmethod
    def register_event(cls, event_type: str, metadata: EventTypeMetadata) -> None:
        """Register an event type with metadata."""
        cls._registry[event_type] = metadata
        
    @classmethod
    def get_event_metadata(cls, event_type: str) -> Optional[EventTypeMetadata]:
        """Get metadata for an event type."""
        return cls._registry.get(event_type)
        
    @classmethod
    def get_events_by_publisher(cls, publisher: str) -> List[str]:
        """Get event types published by a specific component."""
        return [
            event_type for event_type, metadata in cls._registry.items()
            if publisher in metadata.publisher_components
        ]
        
    @classmethod
    def get_events_by_subscriber(cls, subscriber: str) -> List[str]:
        """Get event types subscribed to by a specific component."""
        return [
            event_type for event_type, metadata in cls._registry.items()
            if subscriber in metadata.subscriber_components
        ]
    
    @classmethod
    def get_all_event_types(cls) -> List[str]:
        """Get all registered event types."""
        return list(cls._registry.keys())
    
    @classmethod
    def get_registry_summary(cls) -> Dict[str, Any]:
        """Get a summary of the registry for documentation."""
        return {
            "total_events": len(cls._registry),
            "event_types_by_phase": cls._count_events_by_phase(),
            "publishers": cls._get_unique_publishers(),
            "subscribers": cls._get_unique_subscribers(),
        }
    
    @classmethod
    def _count_events_by_phase(cls) -> Dict[str, int]:
        """Count events by phase prefix."""
        phase_counts = {
            "phase_zero": 0,
            "phase_one": 0,
            "phase_two": 0,
            "phase_three": 0,
            "phase_four": 0,
            "earth_agent": 0,
            "water_agent": 0,
            "system": 0,
            "resource": 0,
            "agent": 0,
            "other": 0
        }
        
        for event_type in cls._registry.keys():
            if event_type.startswith("phase_zero"):
                phase_counts["phase_zero"] += 1
            elif event_type.startswith("phase_one"):
                phase_counts["phase_one"] += 1
            elif event_type.startswith("phase_two"):
                phase_counts["phase_two"] += 1
            elif event_type.startswith("phase_three"):
                phase_counts["phase_three"] += 1
            elif event_type.startswith("phase_four"):
                phase_counts["phase_four"] += 1
            elif event_type.startswith("earth_agent"):
                phase_counts["earth_agent"] += 1
            elif event_type.startswith("water_agent"):
                phase_counts["water_agent"] += 1
            elif event_type.startswith("system"):
                phase_counts["system"] += 1
            elif event_type.startswith("resource"):
                phase_counts["resource"] += 1
            elif event_type.startswith("agent"):
                phase_counts["agent"] += 1
            else:
                phase_counts["other"] += 1
                
        return phase_counts
    
    @classmethod
    def _get_unique_publishers(cls) -> List[str]:
        """Get unique publisher components across all events."""
        publishers = set()
        for metadata in cls._registry.values():
            publishers.update(metadata.publisher_components)
        return sorted(list(publishers))
    
    @classmethod
    def _get_unique_subscribers(cls) -> List[str]:
        """Get unique subscriber components across all events."""
        subscribers = set()
        for metadata in cls._registry.values():
            subscribers.update(metadata.subscriber_components)
        return sorted(list(subscribers))