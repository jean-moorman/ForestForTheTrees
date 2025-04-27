import os
import sys
import asyncio
import unittest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dependency import DependencyValidator, DependencyInterface
from resources import StateManager, EventQueue, ResourceState
from interface import AgentInterface
from phase_one import PhaseOneValidator, PhaseValidationState


class MockAgentInterface(MagicMock):
    """Mock implementation of AgentInterface."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.process_with_validation = AsyncMock()


class TestValidationWorkflow(unittest.TestCase):
    """Test the validation workflow."""
    
    def setUp(self):
        """Set up test resources."""
        self.event_queue = EventQueue()
        self.state_manager = StateManager("test_manager", self.event_queue)
        
        # Create mock agents
        self.root_system_agent = MockAgentInterface()
        self.tree_placement_agent = MockAgentInterface()
        self.foundation_refinement_agent = MockAgentInterface()
        
        # Create validator
        self.phase_validator = PhaseOneValidator(
            self.state_manager,
            self.event_queue,
            self.root_system_agent,
            self.tree_placement_agent,
            self.foundation_refinement_agent
        )
        
        # Sample data for testing
        self.valid_data_flow = {
            "data_architecture": {
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
        }
        
        self.invalid_data_flow = {
            "data_architecture": {
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
        }
        
        self.valid_structure = {
            "component_architecture": {
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
        }
        
        self.inconsistent_structure = {
            "component_architecture": {
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
                            "required": [],  # Missing dependency on componentA from data flow
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
        }
        
    def test_data_flow_registration_valid(self):
        """Test registering valid data flow."""
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self.phase_validator.register_data_flow(self.valid_data_flow["data_architecture"]))
        self.assertTrue(result, "Valid data flow should register successfully")
        
    def test_data_flow_registration_invalid(self):
        """Test registering invalid data flow."""
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self.phase_validator.register_data_flow(self.invalid_data_flow["data_architecture"]))
        self.assertFalse(result, "Invalid data flow should fail registration")
        self.assertEqual(self.phase_validator.validation_state, PhaseValidationState.DATA_FLOW_REVISING)
        
    def test_structural_registration_valid(self):
        """Test registering valid structural breakdown."""
        loop = asyncio.get_event_loop()
        
        # Register valid data flow first
        loop.run_until_complete(self.phase_validator.register_data_flow(self.valid_data_flow["data_architecture"]))
        
        # Then register valid structure
        result = loop.run_until_complete(self.phase_validator.register_structural_breakdown(self.valid_structure["component_architecture"]))
        self.assertTrue(result, "Valid structure should register successfully")
        self.assertEqual(self.phase_validator.validation_state, PhaseValidationState.COMPLETED)
        
    def test_structural_registration_inconsistent(self):
        """Test registering inconsistent structural breakdown."""
        loop = asyncio.get_event_loop()
        
        # Register valid data flow first
        loop.run_until_complete(self.phase_validator.register_data_flow(self.valid_data_flow["data_architecture"]))
        
        # Then register inconsistent structure
        result = loop.run_until_complete(self.phase_validator.register_structural_breakdown(self.inconsistent_structure["component_architecture"]))
        self.assertFalse(result, "Inconsistent structure should fail cross-validation")
        self.assertEqual(self.phase_validator.validation_state, PhaseValidationState.ARBITRATION)
        
    def test_data_flow_revision(self):
        """Test data flow revision process."""
        loop = asyncio.get_event_loop()
        
        # Setup mock response
        self.root_system_agent.process_with_validation.return_value = self.valid_data_flow
        
        # Register invalid data flow to trigger revision
        loop.run_until_complete(self.phase_validator.register_data_flow(self.invalid_data_flow["data_architecture"]))
        
        # Call revise_data_flow
        result = loop.run_until_complete(self.phase_validator.revise_data_flow())
        
        # Verify revision was requested with feedback
        self.root_system_agent.process_with_validation.assert_called_once()
        self.assertIn("validation feedback", self.root_system_agent.process_with_validation.call_args[1]["conversation"])
        
    def test_arbitration_process(self):
        """Test arbitration process."""
        loop = asyncio.get_event_loop()
        
        # Setup mock response
        self.foundation_refinement_agent.process_with_validation.return_value = {
            "refinement_analysis": {
                "root_cause": {
                    "responsible_agent": "root_system_architect"
                }
            }
        }
        
        # Setup validation state
        self.phase_validator.validation_state = PhaseValidationState.ARBITRATION
        self.phase_validator._last_validation_errors = [
            {"error_type": "missing_data_flow", "message": "Missing data flow"}
        ]
        
        # Call perform_arbitration
        responsible_agent = loop.run_until_complete(self.phase_validator.perform_arbitration())
        
        # Verify arbitration was performed
        self.foundation_refinement_agent.process_with_validation.assert_called_once()
        self.assertEqual(responsible_agent, "data_flow_agent")
        self.assertEqual(self.phase_validator.validation_state, PhaseValidationState.DATA_FLOW_REVISING)
        
    def test_full_validation_workflow(self):
        """Test the full validation workflow."""
        loop = asyncio.get_event_loop()
        
        # Setup mock responses
        self.root_system_agent.process_with_validation.return_value = self.valid_data_flow
        self.tree_placement_agent.process_with_validation.return_value = self.valid_structure
        self.foundation_refinement_agent.process_with_validation.return_value = {
            "refinement_analysis": {
                "root_cause": {
                    "responsible_agent": "root_system_architect"
                }
            }
        }
        
        # Register invalid data flow
        loop.run_until_complete(self.phase_validator.register_data_flow(self.invalid_data_flow["data_architecture"]))
        
        # Execute workflow
        result = loop.run_until_complete(self.phase_validator.execute_validation_workflow())
        
        # Verify workflow completed successfully
        self.assertTrue(result, "Validation workflow should complete successfully")
        self.assertEqual(self.phase_validator.validation_state, PhaseValidationState.COMPLETED)
        

if __name__ == '__main__':
    # Ensure event loop is running
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    unittest.main()