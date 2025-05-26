import unittest
import asyncio
import datetime
from enum import Enum, auto
import sys
import os
from unittest.mock import MagicMock, patch

# Adjust Python path to find modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the actual classes
from resources.common import ResourceState, InterfaceState, ResourceType
from resources.state.models import StateEntry, StateSnapshot
from resources.state.validators import StateTransitionValidator

# Mock SystemErrorRecovery to avoid dependency issues
sys.modules['system_error_recovery'] = MagicMock()

def async_test(coro):
    """Decorator for async test methods"""
    def wrapper(*args, **kwargs):
        # Get the current event loop if it exists and is running
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            # No event loop in this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper

class TestBasicStateElements(unittest.TestCase):
    """Test the basic state elements from the state module."""
    
    def test_state_entry_creation(self):
        """Test creating a StateEntry object."""
        entry = StateEntry(
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE,
            metadata={"region": "us-west-2"}
        )
        
        self.assertEqual(entry.state, ResourceState.ACTIVE)
        self.assertEqual(entry.resource_type, ResourceType.COMPUTE)
        self.assertEqual(entry.metadata, {"region": "us-west-2"})
        
    def test_state_snapshot_creation(self):
        """Test creating a StateSnapshot object."""
        snapshot = StateSnapshot(
            state={"state": ResourceState.ACTIVE, "metadata": {"region": "us-west-2"}},
            resource_type=ResourceType.COMPUTE
        )
        
        self.assertEqual(snapshot.state["state"], ResourceState.ACTIVE)
        self.assertEqual(snapshot.state["metadata"]["region"], "us-west-2")
        self.assertEqual(snapshot.resource_type, ResourceType.COMPUTE)
        
    def test_state_transition_validation(self):
        """Test the StateTransitionValidator."""
        validator = StateTransitionValidator()
        
        # Test valid transitions
        self.assertTrue(validator.validate_transition(ResourceState.ACTIVE, ResourceState.PAUSED))
        self.assertTrue(validator.validate_transition(ResourceState.ACTIVE, ResourceState.FAILED))
        self.assertTrue(validator.validate_transition(ResourceState.PAUSED, ResourceState.ACTIVE))
        
        # Test invalid transitions
        self.assertFalse(validator.validate_transition(ResourceState.ACTIVE, ResourceState.RECOVERED))
        self.assertFalse(validator.validate_transition(ResourceState.FAILED, ResourceState.ACTIVE))
        
        # Test self-transitions
        self.assertTrue(validator.validate_transition(ResourceState.ACTIVE, ResourceState.ACTIVE))

if __name__ == "__main__":
    unittest.main()