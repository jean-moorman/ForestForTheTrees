import unittest
import asyncio
import os
import shutil
import tempfile
import datetime
from unittest.mock import Mock, patch, AsyncMock
import json
import pickle
import sys
from pathlib import Path
import uuid
import time

# Directly import the classes we need to avoid import issues
from resources.state.models import StateEntry, StateSnapshot
from resources.state.validators import StateTransitionValidator
from resources.common import ResourceState, InterfaceState, ResourceType, HealthStatus

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
        
    def test_state_entry_with_interface_state(self):
        """Test that StateEntry can handle InterfaceState values"""
        entry = StateEntry(
            state=InterfaceState.ACTIVE,
            resource_type=ResourceType.INTERFACE,
            metadata={"connection_count": 5}
        )
        
        self.assertEqual(entry.state, InterfaceState.ACTIVE)
        self.assertEqual(entry.resource_type, ResourceType.INTERFACE)
        self.assertEqual(entry.metadata, {"connection_count": 5})
        
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
        
    def test_state_entry_with_failure_info(self):
        """Test that StateEntry can include failure information"""
        failure_info = {
            "error_type": "ConnectionError",
            "message": "Failed to connect to resource",
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        entry = StateEntry(
            state=ResourceState.FAILED,
            resource_type=ResourceType.COMPUTE,
            metadata={"region": "us-west-2"},
            failure_info=failure_info,
            transition_reason="connection failure"
        )
        
        self.assertEqual(entry.state, ResourceState.FAILED)
        self.assertEqual(entry.failure_info, failure_info)
        self.assertEqual(entry.transition_reason, "connection failure")


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
    
    def test_snapshot_with_custom_timestamp(self):
        """Test that StateSnapshot can be created with a custom timestamp"""
        custom_time = datetime.datetime(2023, 1, 1, 12, 0, 0)
        state_data = {"state": ResourceState.ACTIVE}
        snapshot = StateSnapshot(
            state=state_data,
            timestamp=custom_time,
            resource_type=ResourceType.COMPUTE
        )
        
        self.assertEqual(snapshot.timestamp, custom_time)
    
    def test_snapshot_with_custom_version(self):
        """Test that StateSnapshot can be created with a custom version"""
        state_data = {"state": ResourceState.ACTIVE}
        snapshot = StateSnapshot(
            state=state_data,
            resource_type=ResourceType.COMPUTE,
            version=5
        )
        
        self.assertEqual(snapshot.version, 5)


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
            
    def test_valid_interface_transitions(self):
        """Test valid interface state transitions"""
        valid_transitions = [
            (InterfaceState.INITIALIZED, InterfaceState.ACTIVE),
            (InterfaceState.INITIALIZED, InterfaceState.ERROR),
            (InterfaceState.ACTIVE, InterfaceState.DISABLED),
            (InterfaceState.ACTIVE, InterfaceState.ERROR),
            (InterfaceState.ACTIVE, InterfaceState.VALIDATING),
            (InterfaceState.DISABLED, InterfaceState.ACTIVE),
            (InterfaceState.ERROR, InterfaceState.INITIALIZED),
            (InterfaceState.ERROR, InterfaceState.DISABLED),
            (InterfaceState.VALIDATING, InterfaceState.ACTIVE),
            (InterfaceState.VALIDATING, InterfaceState.ERROR),
            (InterfaceState.VALIDATING, InterfaceState.PROPAGATING),
            (InterfaceState.PROPAGATING, InterfaceState.ACTIVE),
            (InterfaceState.PROPAGATING, InterfaceState.ERROR)
        ]
        
        for current, new in valid_transitions:
            self.assertTrue(
                self.validator.validate_transition(current, new),
                f"Transition from {current} to {new} should be valid"
            )
            
    def test_invalid_interface_transitions(self):
        """Test invalid interface state transitions"""
        invalid_transitions = [
            (InterfaceState.INITIALIZED, InterfaceState.DISABLED),
            (InterfaceState.INITIALIZED, InterfaceState.VALIDATING),
            (InterfaceState.INITIALIZED, InterfaceState.PROPAGATING),
            (InterfaceState.DISABLED, InterfaceState.INITIALIZED),
            (InterfaceState.DISABLED, InterfaceState.ERROR),
            (InterfaceState.DISABLED, InterfaceState.VALIDATING),
            (InterfaceState.DISABLED, InterfaceState.PROPAGATING),
            (InterfaceState.ERROR, InterfaceState.ACTIVE),
            (InterfaceState.ERROR, InterfaceState.VALIDATING),
            (InterfaceState.ERROR, InterfaceState.PROPAGATING),
            (InterfaceState.VALIDATING, InterfaceState.INITIALIZED),
            (InterfaceState.VALIDATING, InterfaceState.DISABLED),
            (InterfaceState.PROPAGATING, InterfaceState.INITIALIZED),
            (InterfaceState.PROPAGATING, InterfaceState.DISABLED),
            (InterfaceState.PROPAGATING, InterfaceState.VALIDATING)
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
        
    def test_get_valid_transitions(self):
        """Test getting valid next states"""
        active_transitions = self.validator.get_valid_transitions(ResourceState.ACTIVE)
        self.assertEqual(
            active_transitions, 
            {ResourceState.PAUSED, ResourceState.FAILED, ResourceState.TERMINATED}
        )
        
        terminated_transitions = self.validator.get_valid_transitions(ResourceState.TERMINATED)
        self.assertEqual(terminated_transitions, set())
        
        dict_transitions = self.validator.get_valid_transitions({"status": "running"})
        self.assertEqual(dict_transitions, set())
        
    def test_self_transitions(self):
        """Test that transitions to the same state are always valid"""
        states = [
            ResourceState.ACTIVE,
            ResourceState.PAUSED,
            ResourceState.FAILED,
            ResourceState.RECOVERED,
            ResourceState.TERMINATED,
            InterfaceState.INITIALIZED,
            InterfaceState.ACTIVE,
            InterfaceState.DISABLED,
            InterfaceState.ERROR,
            InterfaceState.VALIDATING,
            InterfaceState.PROPAGATING,
            {"status": "custom"}
        ]
        
        for state in states:
            self.assertTrue(
                self.validator.validate_transition(state, state),
                f"Self transition for {state} should be valid"
            )


if __name__ == '__main__':
    unittest.main()