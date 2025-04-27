"""Tests for PhaseFourInterface class."""

import unittest
import asyncio
from unittest.mock import MagicMock, patch
import json

from resources import (
    ResourceType,
    EventQueue, 
    StateManager, 
    AgentContextManager, 
    CacheManager, 
    MetricsManager, 
    ErrorHandler
)
from phase_four.interface import PhaseFourInterface


class TestPhaseFourInterface(unittest.TestCase):
    """Test cases for PhaseFourInterface."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mocks for all dependencies
        self.event_queue = MagicMock(spec=EventQueue)
        self.state_manager = MagicMock(spec=StateManager)
        self.context_manager = MagicMock(spec=AgentContextManager)
        self.cache_manager = MagicMock(spec=CacheManager)
        self.metrics_manager = MagicMock(spec=MetricsManager)
        self.error_handler = MagicMock(spec=ErrorHandler)
        
        # Create interface with mocked dependencies
        self.interface = PhaseFourInterface(
            self.event_queue,
            self.state_manager,
            self.context_manager,
            self.cache_manager,
            self.metrics_manager,
            self.error_handler
        )
        
        # Sample feature requirements
        self.feature_requirements = {
            "id": "test_feature_123",
            "name": "Test Feature",
            "description": "A test feature for unit testing",
            "language": "python"
        }
        
        # Sample improvement request
        self.improvement_request = {
            "id": "test_feature_123",
            "name": "Test Feature",
            "original_implementation": "def test_function():\n    return 'Hello, World!'",
            "improvements": ["Add type hints", "Add docstring"],
            "rationale": "Improve code quality"
        }
        
        # Sample refinement agent response
        self.refinement_response = {
            "feature_id": "test_feature_123",
            "feature_name": "Test Feature",
            "operation_id": "test_operation_123",
            "success": True,
            "iterations": 2,
            "code": "def test_function() -> str:\n    \"\"\"Return a greeting.\"\"\"\n    return 'Hello, World!'",
            "refinement_history": [],
            "analysis": {"code_quality_score": 85},
            "improvement_suggestions": []
        }
    
    async def async_setup(self):
        """Async setup for tests."""
        # Mock the refinement agent methods
        self.interface.refinement_agent.refine_code = MagicMock()
        self.interface.refinement_agent.refine_code.return_value = self.refinement_response
        
        # Mock state manager set_state
        self.state_manager.set_state = MagicMock()
        
        # Mock metrics manager
        self.metrics_manager.record_metric = MagicMock()
        
    async def test_process_feature_code_success(self):
        """Test successful feature code processing."""
        await self.async_setup()
        
        # Call the method under test
        result = await self.interface.process_feature_code(
            self.feature_requirements,
            initial_code=None,
            max_iterations=5
        )
        
        # Verify method calls
        self.interface.refinement_agent.refine_code.assert_called_once()
        self.metrics_manager.record_metric.assert_called()
        self.state_manager.set_state.assert_called_once()
        
        # Verify state_manager.set_state call
        state_call_args = self.state_manager.set_state.call_args[0]
        self.assertIn("phase_four:result:", state_call_args[0])
        self.assertEqual(state_call_args[1], self.refinement_response)
        self.assertEqual(state_call_args[2], ResourceType.STATE)
        
        # Verify the result
        self.assertEqual(result, self.refinement_response)
    
    async def test_process_feature_code_error(self):
        """Test feature code processing with an error."""
        await self.async_setup()
        
        # Set up the refinement agent to raise an exception
        self.interface.refinement_agent.refine_code.side_effect = Exception("Test error")
        
        # Call the method under test
        result = await self.interface.process_feature_code(
            self.feature_requirements,
            initial_code=None,
            max_iterations=5
        )
        
        # Verify method calls
        self.interface.refinement_agent.refine_code.assert_called_once()
        self.metrics_manager.record_metric.assert_called()
        
        # Verify the result
        self.assertFalse(result["success"])
        self.assertEqual(result["feature_id"], "test_feature_123")
        self.assertEqual(result["feature_name"], "Test Feature")
        self.assertIn("Phase Four processing failed", result["error"])
    
    async def test_process_feature_improvement_success(self):
        """Test successful feature improvement processing."""
        await self.async_setup()
        
        # Mock validation manager and compilation agent
        improve_response = {
            "improved_code": "def test_function() -> str:\n    \"\"\"Return a greeting.\"\"\"\n    return 'Hello, World!'",
            "explanation": "Added type hints and docstring",
            "improvements_applied": [
                {"description": "Added type hints", "changes": "Added return type -> str"},
                {"description": "Added docstring", "changes": "Added function docstring"}
            ]
        }
        
        compilation_result = {
            "success": True,
            "results": {
                "format": {"success": True, "state": "SUCCEEDED", "issues": [], "execution_time": 0.1}
            }
        }
        
        self.interface.refinement_agent._validation_manager.validate_llm_response = MagicMock()
        self.interface.refinement_agent._validation_manager.validate_llm_response.return_value = improve_response
        
        self.interface.refinement_agent.static_compilation_agent.run_compilation = MagicMock()
        self.interface.refinement_agent.static_compilation_agent.run_compilation.return_value = compilation_result
        
        # Call the method under test
        result = await self.interface.process_feature_improvement(self.improvement_request)
        
        # Verify method calls
        self.interface.refinement_agent._validation_manager.validate_llm_response.assert_called_once()
        self.interface.refinement_agent.static_compilation_agent.run_compilation.assert_called_once()
        self.metrics_manager.record_metric.assert_called()
        self.state_manager.set_state.assert_called()
        
        # Verify the result
        self.assertTrue(result["success"])
        self.assertEqual(result["feature_id"], "test_feature_123")
        self.assertEqual(result["feature_name"], "Test Feature")
        self.assertEqual(result["improved_code"], improve_response["improved_code"])
    
    async def test_process_feature_improvement_missing_original_code(self):
        """Test feature improvement with missing original code."""
        await self.async_setup()
        
        # Create a request with missing original implementation
        bad_request = {
            "id": "test_feature_123",
            "name": "Test Feature",
            "improvements": ["Add type hints"],
            "rationale": "Improve code quality"
        }
        
        # Call the method under test
        result = await self.interface.process_feature_improvement(bad_request)
        
        # Verify the result
        self.assertFalse(result["success"])
        self.assertEqual(result["feature_id"], "test_feature_123")
        self.assertEqual(result["feature_name"], "Test Feature")
        self.assertIn("Original implementation is required", result["error"])
    
    async def test_process_feature_improvement_missing_improvements(self):
        """Test feature improvement with missing improvements."""
        await self.async_setup()
        
        # Create a request with missing improvements
        bad_request = {
            "id": "test_feature_123",
            "name": "Test Feature",
            "original_implementation": "def test_function():\n    return 'Hello, World!'",
            "rationale": "Improve code quality"
        }
        
        # Call the method under test
        result = await self.interface.process_feature_improvement(bad_request)
        
        # Verify the result
        self.assertFalse(result["success"])
        self.assertEqual(result["feature_id"], "test_feature_123")
        self.assertEqual(result["feature_name"], "Test Feature")
        self.assertIn("No improvement suggestions provided", result["error"])


def async_test(coro):
    """Decorator for async test methods."""
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper


# Apply the decorator to the test methods
TestPhaseFourInterface.test_process_feature_code_success = async_test(TestPhaseFourInterface.test_process_feature_code_success)
TestPhaseFourInterface.test_process_feature_code_error = async_test(TestPhaseFourInterface.test_process_feature_code_error)
TestPhaseFourInterface.test_process_feature_improvement_success = async_test(TestPhaseFourInterface.test_process_feature_improvement_success)
TestPhaseFourInterface.test_process_feature_improvement_missing_original_code = async_test(TestPhaseFourInterface.test_process_feature_improvement_missing_original_code)
TestPhaseFourInterface.test_process_feature_improvement_missing_improvements = async_test(TestPhaseFourInterface.test_process_feature_improvement_missing_improvements)


if __name__ == "__main__":
    unittest.main()