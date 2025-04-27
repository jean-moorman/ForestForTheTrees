import os
import sys
import asyncio
import unittest
import json
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dependency import DependencyValidator, DependencyInterface
from resources import StateManager, EventQueue, ResourceState


class TestDependencyValidation(unittest.TestCase):
    """Test the dependency validation functionality."""
    
    def setUp(self):
        """Set up test resources."""
        self.event_queue = EventQueue()
        self.state_manager = StateManager("test_manager", self.event_queue)
        self.validator = DependencyValidator(self.state_manager)
        
        # Sample data for testing
        self.valid_data_flow = {
            "data_flows": [
                {
                    "flow_id": "flow1",
                    "source": "componentA",
                    "destination": "componentB",
                    "data_type": "string",
                    "transformation": "none",
                    "trigger": "event"
                },
                {
                    "flow_id": "flow2",
                    "source": "componentB",
                    "destination": "componentC",
                    "data_type": "string",
                    "transformation": "none",
                    "trigger": "event"
                }
            ]
        }
        
        self.invalid_data_flow = {
            "data_flows": [
                {
                    "flow_id": "flow1",
                    "source": "componentA",
                    "destination": "componentB",
                    "data_type": "string",
                    "transformation": "none",
                    "trigger": "event"
                },
                {
                    "flow_id": "flow2",
                    "source": "componentB",
                    "destination": "componentA",  # Creates a cycle
                    "data_type": "string",
                    "transformation": "none",
                    "trigger": "event"
                }
            ]
        }
        
        self.valid_structure = {
            "ordered_components": [
                {
                    "name": "componentA",
                    "sequence_number": 1,
                    "dependencies": {
                        "required": [],
                        "optional": []
                    }
                },
                {
                    "name": "componentB",
                    "sequence_number": 2,
                    "dependencies": {
                        "required": ["componentA"],
                        "optional": []
                    }
                },
                {
                    "name": "componentC",
                    "sequence_number": 3,
                    "dependencies": {
                        "required": ["componentB"],
                        "optional": []
                    }
                }
            ]
        }
        
        self.invalid_structure = {
            "ordered_components": [
                {
                    "name": "componentA",
                    "sequence_number": 1,
                    "dependencies": {
                        "required": ["componentC"],  # Forward reference not allowed
                        "optional": []
                    }
                },
                {
                    "name": "componentB",
                    "sequence_number": 2,
                    "dependencies": {
                        "required": ["componentA"],
                        "optional": []
                    }
                },
                {
                    "name": "componentC",
                    "sequence_number": 3,
                    "dependencies": {
                        "required": ["componentB"],
                        "optional": []
                    }
                }
            ]
        }
        
        self.inconsistent_structure = {
            "ordered_components": [
                {
                    "name": "componentA",
                    "sequence_number": 1,
                    "dependencies": {
                        "required": [],
                        "optional": []
                    }
                },
                {
                    "name": "componentB",
                    "sequence_number": 2,
                    "dependencies": {
                        "required": [],  # Missing dependency on componentA that exists in data flow
                        "optional": []
                    }
                },
                {
                    "name": "componentC",
                    "sequence_number": 3,
                    "dependencies": {
                        "required": ["componentB"],
                        "optional": []
                    }
                }
            ]
        }
        
    def tearDown(self):
        """Clean up resources."""
        pass
        
    def test_data_flow_validation(self):
        """Test data flow validation."""
        # Valid data flow
        is_valid, errors = self.validator.dependency_interface.validate_data_flow(self.valid_data_flow)
        self.assertTrue(is_valid, "Valid data flow should validate successfully")
        self.assertEqual(len(errors), 0, "Should have no errors for valid data flow")
        
        # Invalid data flow
        is_valid, errors = self.validator.dependency_interface.validate_data_flow(self.invalid_data_flow)
        self.assertFalse(is_valid, "Invalid data flow should fail validation")
        self.assertGreater(len(errors), 0, "Should have errors for invalid data flow")
        
    def test_structural_breakdown_validation(self):
        """Test structural breakdown validation."""
        # Valid structure
        is_valid, errors = self.validator.dependency_interface.validate_structural_breakdown(self.valid_structure)
        self.assertTrue(is_valid, "Valid structure should validate successfully")
        self.assertEqual(len(errors), 0, "Should have no errors for valid structure")
        
        # Invalid structure
        is_valid, errors = self.validator.dependency_interface.validate_structural_breakdown(self.invalid_structure)
        self.assertFalse(is_valid, "Invalid structure should fail validation")
        self.assertGreater(len(errors), 0, "Should have errors for invalid structure")
        
    def test_cross_consistency_validation(self):
        """Test cross-consistency validation."""
        # Setup data
        self.validator._data_flow = self.valid_data_flow
        self.validator._structural_breakdown = self.valid_structure
        
        # Test consistent data
        is_valid, errors = self.validator.dependency_interface.validate_cross_consistency(
            self.valid_data_flow, 
            self.valid_structure
        )
        self.assertTrue(is_valid, "Cross-consistency should validate with consistent data")
        
        # Test inconsistent data
        is_valid, errors = self.validator.dependency_interface.validate_cross_consistency(
            self.valid_data_flow, 
            self.inconsistent_structure
        )
        self.assertFalse(is_valid, "Cross-consistency should fail with inconsistent data")
        self.assertGreater(len(errors), 0, "Should have errors for inconsistent data")
        
    def test_determine_responsible_agent(self):
        """Test determination of responsible agent for errors."""
        # Create some test errors
        data_flow_errors = [
            {"error_type": "data_flow_cycle", "message": "Cycle in data flow"}
        ]
        
        structural_errors = [
            {"error_type": "duplicate_component_name", "message": "Duplicate component name"}
        ]
        
        mixed_errors = [
            {"error_type": "data_flow_cycle", "message": "Cycle in data flow"},
            {"error_type": "duplicate_component_name", "message": "Duplicate component name"},
            {"error_type": "missing_structural_dependency", "message": "Missing structural dependency"}
        ]
        
        # Run event loop to get results
        loop = asyncio.get_event_loop()
        
        # Test data flow errors
        result = loop.run_until_complete(self.validator.determine_responsible_agent(data_flow_errors))
        self.assertEqual(result, "data_flow_agent", "Should identify data_flow_agent for data flow errors")
        
        # Test structural errors
        result = loop.run_until_complete(self.validator.determine_responsible_agent(structural_errors))
        self.assertEqual(result, "structural_agent", "Should identify structural_agent for structural errors")
        
        # Test mixed errors with more structural errors
        result = loop.run_until_complete(self.validator.determine_responsible_agent(mixed_errors))
        self.assertEqual(result, "structural_agent", "Should identify structural_agent for mixed errors with more structural")


if __name__ == '__main__':
    # Ensure event loop is running
    loop = asyncio.get_event_loop()
    if not loop.is_running():
        unittest.main()
    else:
        print("Test requires a running event loop")
        sys.exit(1)