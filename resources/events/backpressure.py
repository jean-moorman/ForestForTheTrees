"""
Event system backpressure and rate limiting.

This module provides classes and utilities for implementing backpressure and rate
limiting in the event system to handle load spikes and prevent resource exhaustion.
"""
import logging
import time
from typing import Dict, Any, List, Set, Optional

from .utils import RateLimiter

logger = logging.getLogger(__name__)

class EventBackpressureManager:
    """Manages backpressure for event queues to prevent resource exhaustion.
    
    This class tracks queue saturation and provides strategies for handling
    overload situations through rate limiting, prioritization, and rejection.
    """
    
    def __init__(self):
        """Initialize backpressure manager."""
        # Queue saturation tracking
        self.queue_saturation = {
            'high': 0.0,
            'normal': 0.0,
            'low': 0.0,
            'last_saturation_check': 0,
            'saturation_window': [],  # Track saturation over time for adaptive throttling
            'rejected_events': {},  # Track rejected events by type
        }
        
        # Events that should maintain their priority regardless of load
        self.prioritized_events = set([
            "system_health_changed",
            "resource_error_occurred", 
            "system_alert",
            "resource_error_recovery_started",
            "resource_error_recovery_completed",
            "resource_error_resolved"
        ])
        
        # Rate limiters for event types
        self.rate_limiters: Dict[str, RateLimiter] = {}
        
    def update_saturation(self, high_size: int, high_capacity: int,
                         normal_size: int, normal_capacity: int,
                         low_size: int, low_capacity: int):
        """Update queue saturation metrics.
        
        Args:
            high_size: Current size of high priority queue
            high_capacity: Maximum capacity of high priority queue
            normal_size: Current size of normal priority queue
            normal_capacity: Maximum capacity of normal priority queue
            low_size: Current size of low priority queue
            low_capacity: Maximum capacity of low priority queue
        """
        # Calculate saturation percentages
        high_saturation = high_size / high_capacity if high_capacity > 0 else 0
        normal_saturation = normal_size / normal_capacity if normal_capacity > 0 else 0
        low_saturation = low_size / low_capacity if low_capacity > 0 else 0
        
        # Update metrics
        self.queue_saturation['high'] = high_saturation
        self.queue_saturation['normal'] = normal_saturation
        self.queue_saturation['low'] = low_saturation
        self.queue_saturation['last_saturation_check'] = time.time()
        
        # Track saturation window for trending
        saturation_entry = (time.time(), high_saturation, normal_saturation, low_saturation)
        self.queue_saturation['saturation_window'].append(saturation_entry)
        
        # Limit window size
        if len(self.queue_saturation['saturation_window']) > 10:
            self.queue_saturation['saturation_window'] = self.queue_saturation['saturation_window'][-10:]
        
        # Log warning level on high saturation
        if high_saturation >= 0.9:
            logger.warning(f"High priority queue saturation critical at {high_saturation:.1%}")
        if normal_saturation >= 0.9:
            logger.warning(f"Normal priority queue saturation critical at {normal_saturation:.1%}")
    
    def check_rate_limit(self, event_type: str, priority: str = "normal") -> bool:
        """Check if an event should be rate limited.
        
        Args:
            event_type: The type of event to check
            priority: Event priority - "high", "normal", or "low"
            
        Returns:
            True if event is allowed, False if it should be rejected
        """
        # Prioritized events bypass rate limiting
        if event_type in self.prioritized_events:
            return True
            
        # Initialize rate limiter if needed
        if event_type not in self.rate_limiters:
            self.rate_limiters[event_type] = RateLimiter(
                rate=10.0,      # Default to 10 events per second
                max_tokens=10.0  # Allow burst of 10 events
            )
        
        # Adjust tokens needed based on priority
        tokens_needed = 1.0
        if priority == "high":
            tokens_needed = 0.5  # High priority uses fewer tokens
        elif priority == "low":
            tokens_needed = 1.5  # Low priority uses more tokens
        
        # Apply rate limiting
        if not self.rate_limiters[event_type].consume(tokens_needed):
            # Not enough tokens, reject event
            # Track rejection for metrics
            self.queue_saturation['rejected_events'][event_type] = \
                self.queue_saturation['rejected_events'].get(event_type, 0) + 1
            
            logger.debug(f"Rate limiting rejected {event_type} event")
            return False
            
        return True
    
    def get_adjusted_priority(self, event_type: str, original_priority: str) -> str:
        """Adjust event priority based on system saturation.
        
        Args:
            event_type: The type of event to adjust
            original_priority: Original event priority - "high", "normal", or "low"
            
        Returns:
            Adjusted priority - "high", "normal", or "low"
        """
        # Get current saturation metrics
        high_saturation = self.queue_saturation['high']
        normal_saturation = self.queue_saturation['normal']
        low_saturation = self.queue_saturation['low']
        
        # Determine overall system saturation level
        system_saturation = max(high_saturation, normal_saturation)
        
        # Check if we're trending up in saturation
        trending_up = False
        if len(self.queue_saturation['saturation_window']) >= 2:
            prev_normal_saturation = self.queue_saturation['saturation_window'][-2][2]
            if normal_saturation > prev_normal_saturation + 0.05:  # 5% increase
                trending_up = True
        
        # Critical saturation - system-wide issue
        if system_saturation >= 0.95:
            # For non-priority events, downgrade
            if original_priority != "high" and event_type not in self.prioritized_events:
                return "low"
            # Prioritized events get upgraded during critical saturation
            elif original_priority == "normal" and event_type in self.prioritized_events:
                return "high"
                
        # Severe saturation
        elif system_saturation >= 0.85:
            # Low priority events remain low
            if original_priority == "low":
                return "low"
            
            # Normal priority events get downgraded if not critical
            elif original_priority == "normal":
                if event_type not in self.prioritized_events and normal_saturation >= 0.9:
                    return "low"
                else:
                    return "normal"
            
            # High priority remains high
            return original_priority
                
        # Warning saturation level
        elif system_saturation >= 0.75:
            # Mild back-pressure strategies
            if original_priority == "normal" and event_type not in self.prioritized_events:
                # Apply back-pressure if saturation is trending up
                if trending_up and low_saturation < 0.8:
                    # Only downgrade if low priority queue has capacity
                    return "low"
        
        # Otherwise keep original priority
        return original_priority
    
    def should_reject_event(self, event_type: str, priority: str) -> bool:
        """Determine if an event should be rejected based on system load.
        
        Args:
            event_type: The type of event to check
            priority: Event priority after adjustment
            
        Returns:
            True if event should be rejected, False otherwise
        """
        # Critical events never get rejected
        if event_type in self.prioritized_events:
            return False
            
        # Get saturation for the target queue
        target_saturation = 0.0
        if priority == "high":
            target_saturation = self.queue_saturation['high']
        elif priority == "normal":
            target_saturation = self.queue_saturation['normal']
        else:
            target_saturation = self.queue_saturation['low']
        
        # Determine overall system saturation level
        system_saturation = max(self.queue_saturation['high'], self.queue_saturation['normal'])
        
        # Reject on critical saturation for non-priority events
        if system_saturation >= 0.95 and event_type not in self.prioritized_events:
            if priority != "high":
                # Track rejection for metrics
                self.queue_saturation['rejected_events'][event_type] = \
                    self.queue_saturation['rejected_events'].get(event_type, 0) + 1
                logger.warning(f"System critical saturation ({system_saturation:.1%}), rejecting {event_type} event")
                return True
                
        # Reject on target queue saturation
        if target_saturation >= 0.99 and event_type not in self.prioritized_events:
            # Track rejection for metrics
            self.queue_saturation['rejected_events'][event_type] = \
                self.queue_saturation['rejected_events'].get(event_type, 0) + 1
            logger.warning(f"Target queue completely saturated ({target_saturation:.1%}), rejecting {event_type}")
            return True
            
        return False
        
    def get_stats(self) -> Dict[str, Any]:
        """Get backpressure statistics.
        
        Returns:
            Dictionary of statistics
        """
        # Count total rejections
        total_rejections = sum(self.queue_saturation['rejected_events'].values())
        
        # Get all rate limiters stats
        rate_limiter_stats = {}
        for event_type, limiter in self.rate_limiters.items():
            rate_limiter_stats[event_type] = limiter.get_stats()
            
        return {
            "saturation": {
                "high": self.queue_saturation['high'],
                "normal": self.queue_saturation['normal'],
                "low": self.queue_saturation['low']
            },
            "rejections": {
                "total": total_rejections,
                "by_type": dict(self.queue_saturation['rejected_events'])
            },
            "rate_limiters": rate_limiter_stats
        }