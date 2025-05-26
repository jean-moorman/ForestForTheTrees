import unittest
import sys
import os
from unittest.mock import patch

# Add the parent directory to sys.path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# The problem is the import in resources/__init__.py that tries to load ErrorHandler
# We'll patch this module to avoid the import error
import importlib.util
spec = importlib.util.spec_from_file_location(
    "state_models", 
    os.path.join(os.path.dirname(__file__), "..", "resources", "state", "models.py")
)
state_models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(state_models)

spec = importlib.util.spec_from_file_location(
    "state_validators", 
    os.path.join(os.path.dirname(__file__), "..", "resources", "state", "validators.py")
)
state_validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(state_validators)

# Now we can access these directly
StateEntry = state_models.StateEntry
StateSnapshot = state_models.StateSnapshot
StateTransitionValidator = state_validators.StateTransitionValidator

# Import common resources
import importlib.util
spec = importlib.util.spec_from_file_location(
    "common", 
    os.path.join(os.path.dirname(__file__), "..", "resources", "common.py")
)
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)

ResourceState = common.ResourceState
InterfaceState = common.InterfaceState
ResourceType = common.ResourceType

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
        self.assertEqual(snapshot.resource_type, ResourceType.STATE)
        self.assertEqual(snapshot.metadata, {})
        self.assertEqual(snapshot.version, 1)


class TestStateTransitionValidatorBasic(unittest.TestCase):
    """Test basic StateTransitionValidator functionality"""
    
    def setUp(self):
        self.validator = StateTransitionValidator()
        
    def test_valid_resource_transitions(self):
        """Test valid resource state transitions"""
        # Test all valid transitions defined in _RESOURCE_TRANSITIONS
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


if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTest(unittest.makeSuite(TestStateEntryBasic))
    suite.addTest(unittest.makeSuite(TestStateSnapshotBasic))
    suite.addTest(unittest.makeSuite(TestStateTransitionValidatorBasic))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return proper exit code
    sys.exit(not result.wasSuccessful())