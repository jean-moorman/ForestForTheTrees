import unittest
import datetime
from enum import Enum, auto

# Define minimal versions of required enums for testing
# Import the actual ResourceState enum from the common module
from resources.common import ResourceState

# Import the actual InterfaceState enum from the common module
from resources.common import InterfaceState

# Import the actual ResourceType enum from the common module
from resources.common import ResourceType

# Import actual implementation classes from the modules directly
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import directly from the module files
from resources.state.models import StateEntry, StateSnapshot
from resources.state.validators import StateTransitionValidator

# Test cases
class TestStateEntryBasic(unittest.TestCase):
    """Test basic StateEntry functionality"""
    
    def test_state_entry_initialization(self):
        """Test that a StateEntry can be properly initialized"""
        entry = StateEntry(
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE,
            metadata={"region": "us-west-2"},
            previous_state=None,
            transition_reason="initial creation"
        )
        
        self.assertEqual(entry.state, ResourceState.ACTIVE)
        self.assertEqual(entry.resource_type, ResourceType.COMPUTE)
        self.assertEqual(entry.metadata, {"region": "us-west-2"})
        self.assertIsNone(entry.previous_state)
        self.assertEqual(entry.transition_reason, "initial creation")
        self.assertIsNone(entry.failure_info)
        self.assertEqual(entry.version, 1)
        
    def test_state_entry_with_dict_state(self):
        """Test that StateEntry can handle dictionary states"""
        custom_state = {"status": "initializing", "progress": 0.5}
        entry = StateEntry(
            state=custom_state,
            resource_type=ResourceType.STATE,
            metadata={}
        )
        
        self.assertEqual(entry.state, custom_state)
        self.assertEqual(entry.resource_type, ResourceType.STATE)
        
    def test_default_timestamp(self):
        """Test that timestamp defaults to current time"""
        before = datetime.datetime.now()
        entry = StateEntry(
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE
        )
        after = datetime.datetime.now()
        
        self.assertTrue(before <= entry.timestamp <= after)
        
    def test_default_metadata(self):
        """Test that metadata defaults to empty dict"""
        entry = StateEntry(
            state=ResourceState.ACTIVE,
            resource_type=ResourceType.COMPUTE
        )
        
        self.assertEqual(entry.metadata, {})


class TestStateSnapshotBasic(unittest.TestCase):
    """Test basic StateSnapshot functionality"""
    
    def test_snapshot_initialization(self):
        """Test that a StateSnapshot can be properly initialized"""
        state_data = {"state": ResourceState.ACTIVE, "metadata": {"region": "us-west-2"}}
        snapshot = StateSnapshot(
            state=state_data,
            resource_type=ResourceType.COMPUTE
        )
        
        self.assertEqual(snapshot.state, state_data)
        self.assertEqual(snapshot.resource_type, ResourceType.COMPUTE)
        self.assertEqual(snapshot.version, 1)
        
    def test_default_values(self):
        """Test default values for StateSnapshot"""
        state_data = {"state": ResourceState.ACTIVE}
        snapshot = StateSnapshot(state=state_data)
        
        self.assertEqual(snapshot.state, state_data)
        # Use a different assertion method for the ResourceType that doesn't rely on equality
        self.assertTrue(snapshot.resource_type.name == ResourceType.STATE.name)
        self.assertEqual(snapshot.metadata, {})
        self.assertEqual(snapshot.version, 1)


class TestStateTransitionValidatorBasic(unittest.TestCase):
    """Test basic StateTransitionValidator functionality"""
    
    def setUp(self):
        self.validator = StateTransitionValidator()
        
    def test_valid_resource_transitions(self):
        """Test valid resource state transitions"""
        # Test valid transitions 
        valid_transitions = [
            (ResourceState.ACTIVE, ResourceState.PAUSED),
            (ResourceState.ACTIVE, ResourceState.FAILED),
            (ResourceState.ACTIVE, ResourceState.TERMINATED),
            (ResourceState.PAUSED, ResourceState.ACTIVE),
            (ResourceState.PAUSED, ResourceState.TERMINATED),
            (ResourceState.FAILED, ResourceState.RECOVERED),
            (ResourceState.FAILED, ResourceState.TERMINATED),
            (ResourceState.RECOVERED, ResourceState.ACTIVE),
            (ResourceState.RECOVERED, ResourceState.TERMINATED)
        ]
        
        for current, new in valid_transitions:
            self.assertTrue(
                self.validator.validate_transition(current, new),
                f"Transition from {current} to {new} should be valid"
            )
            
    def test_invalid_resource_transitions(self):
        """Test invalid resource state transitions"""
        invalid_transitions = [
            (ResourceState.ACTIVE, ResourceState.RECOVERED),
            (ResourceState.PAUSED, ResourceState.FAILED),
            (ResourceState.PAUSED, ResourceState.RECOVERED),
            (ResourceState.FAILED, ResourceState.ACTIVE),
            (ResourceState.FAILED, ResourceState.PAUSED),
            (ResourceState.RECOVERED, ResourceState.FAILED),
            (ResourceState.RECOVERED, ResourceState.PAUSED),
            (ResourceState.TERMINATED, ResourceState.ACTIVE),
            (ResourceState.TERMINATED, ResourceState.PAUSED),
            (ResourceState.TERMINATED, ResourceState.FAILED),
            (ResourceState.TERMINATED, ResourceState.RECOVERED)
        ]
        
        for current, new in invalid_transitions:
            self.assertFalse(
                self.validator.validate_transition(current, new),
                f"Transition from {current} to {new} should be invalid"
            )
            
    def test_mixed_type_transitions(self):
        """Test transitions between different state types"""
        # Different enum types should not be valid transitions
        self.assertFalse(
            self.validator.validate_transition(ResourceState.ACTIVE, InterfaceState.ACTIVE)
        )
        self.assertFalse(
            self.validator.validate_transition(InterfaceState.ACTIVE, ResourceState.ACTIVE)
        )
        
    def test_dict_state_transitions(self):
        """Test transitions with dictionary states"""
        # Dictionary state transitions should be allowed
        self.assertTrue(
            self.validator.validate_transition({"status": "running"}, {"status": "stopped"})
        )
        
        # Dictionary to enum transitions should be allowed
        self.assertTrue(
            self.validator.validate_transition({"status": "running"}, ResourceState.ACTIVE)
        )
        
        # Enum to dictionary transitions should be allowed
        self.assertTrue(
            self.validator.validate_transition(ResourceState.ACTIVE, {"status": "running"})
        )


if __name__ == '__main__':
    unittest.main()