"""Tests for CodeGenerationAgent class."""

import unittest
import asyncio
from unittest.mock import MagicMock, patch
import json

from resources import (
    EventQueue, 
    StateManager, 
    AgentContextManager, 
    CacheManager, 
    MetricsManager, 
    ErrorHandler
)
from interface import AgentState
from phase_four.agents.code_generation import CodeGenerationAgent


class TestCodeGenerationAgent(unittest.TestCase):
    """Test cases for CodeGenerationAgent."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mocks for all dependencies
        self.event_queue = MagicMock(spec=EventQueue)
        self.state_manager = MagicMock(spec=StateManager)
        self.context_manager = MagicMock(spec=AgentContextManager)
        self.cache_manager = MagicMock(spec=CacheManager)
        self.metrics_manager = MagicMock(spec=MetricsManager)
        self.error_handler = MagicMock(spec=ErrorHandler)
        
        # Create agent with mocked dependencies
        self.agent = CodeGenerationAgent(
            self.event_queue,
            self.state_manager,
            self.context_manager,
            self.cache_manager,
            self.metrics_manager,
            self.error_handler
        )
        
        # Mock the validation manager's process_with_validation method
        self.agent._validation_manager.validate_llm_response = MagicMock()
        
        # Sample feature requirements
        self.feature_requirements = {
            "id": "test_feature_123",
            "name": "Test Feature",
            "description": "A test feature for unit testing",
            "language": "python"
        }
        
        # Sample LLM response
        self.llm_response = {
            "code": "def test_function():\n    return 'Hello, World!'",
            "explanation": "A simple test function",
            "imports": [],
            "dependencies": []
        }
    
    async def async_setup(self):
        """Async setup for tests."""
        # Mock the process_with_validation coroutine
        self.agent.process_with_validation = MagicMock()
        self.agent.process_with_validation.return_value = self.llm_response
        
        # Mock the set_agent_state coroutine
        self.agent.set_agent_state = MagicMock()
    
    async def test_generate_code_success(self):
        """Test successful code generation."""
        await self.async_setup()
        
        # Set up the coroutine return value
        self.agent.process_with_validation.return_value = self.llm_response
        
        # Call the method under test
        result = await self.agent.generate_code(
            self.feature_requirements,
            "test_operation_123"
        )
        
        # Verify method calls
        self.agent.set_agent_state.assert_any_call(AgentState.PROCESSING)
        self.agent.set_agent_state.assert_any_call(AgentState.COMPLETE)
        
        self.agent.process_with_validation.assert_called_once()
        
        # Verify the schema validation was called with the correct arguments
        call_args = self.agent.process_with_validation.call_args[1]
        self.assertIn("conversation", call_args)
        self.assertIn("schema", call_args)
        self.assertIn("current_phase", call_args)
        self.assertIn("operation_id", call_args)
        self.assertEqual(call_args["operation_id"], "test_operation_123")
        
        # Verify the result
        self.assertEqual(result["feature_id"], "test_feature_123")
        self.assertEqual(result["feature_name"], "Test Feature")
        self.assertEqual(result["operation_id"], "test_operation_123")
        self.assertEqual(result["code"], "def test_function():\n    return 'Hello, World!'")
        self.assertEqual(result["explanation"], "A simple test function")
    
    async def test_generate_code_error(self):
        """Test code generation with an error."""
        await self.async_setup()
        
        # Set up the coroutine to raise an exception
        self.agent.process_with_validation.side_effect = Exception("Test error")
        
        # Call the method under test
        result = await self.agent.generate_code(
            self.feature_requirements,
            "test_operation_123"
        )
        
        # Verify method calls
        self.agent.set_agent_state.assert_any_call(AgentState.PROCESSING)
        self.agent.set_agent_state.assert_any_call(AgentState.ERROR)
        
        # Verify the result
        self.assertIn("error", result)
        self.assertEqual(result["feature_id"], "test_feature_123")
        self.assertEqual(result["feature_name"], "Test Feature")
        self.assertEqual(result["operation_id"], "test_operation_123")
        self.assertIn("Code generation failed", result["error"])


def async_test(coro):
    """Decorator for async test methods."""
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper


# Apply the decorator to the test methods
TestCodeGenerationAgent.test_generate_code_success = async_test(TestCodeGenerationAgent.test_generate_code_success)
TestCodeGenerationAgent.test_generate_code_error = async_test(TestCodeGenerationAgent.test_generate_code_error)


if __name__ == "__main__":
    unittest.main()