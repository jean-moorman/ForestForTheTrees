"""
Integration tests for the complete validation pipeline.

These tests verify that all validation components work together correctly,
testing real workflows without mocking critical functionality.
"""

import asyncio
import json
import pytest
import unittest
from datetime import datetime
from typing import Dict, Any, List

# Import system components
from agent import Agent
from agent_validation import Validator, ValidationErrorAnalyzer, SemanticErrorHandler
from resources import EventQueue, StateManager

# Import test infrastructure
from tests_new.harness.validation_test_harness import ValidationTestHarness, ValidationScenarioResult
from tests_new.doubles.testable_api import TestableAnthropicAPI


class TestValidationPipelineIntegration(unittest.TestCase):
    """Integration tests for the complete validation pipeline."""
    
    def setUp(self):
        """Set up test environment."""
        self.harness = ValidationTestHarness()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        """Clean up test environment."""
        if hasattr(self, 'loop'):
            self.loop.close()
            asyncio.set_event_loop(None)
    
    @pytest.mark.asyncio
    async def test_complete_semantic_error_correction_flow(self):
        """Test the complete semantic error detection and correction flow."""
        # Define schema with multiple constraint types
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "minLength": 2},
                        "email": {"type": "string", "format": "email"},
                        "age": {"type": "integer", "minimum": 0, "maximum": 150}
                    },
                    "required": ["name", "email", "age"]
                },
                "status": {"type": "string", "enum": ["active", "inactive", "pending"]},
                "preferences": {
                    "type": "object",
                    "properties": {
                        "notifications": {"type": "boolean"},
                        "theme": {"type": "string", "enum": ["light", "dark"]}
                    },
                    "required": ["notifications"]
                }
            },
            "required": ["user", "status", "preferences"]
        }
        
        # Create invalid response that will trigger semantic error correction
        invalid_response = {
            "user": {
                "name": "X",  # Too short (minLength: 2)
                "email": "invalid-email",  # Invalid email format
                "age": 200  # Exceeds maximum (150)
            },
            "status": "unknown",  # Invalid enum value
            "preferences": {
                # Missing required "notifications" field
                "theme": "blue"  # Invalid enum value
            }
        }
        
        # Create valid corrected response
        corrected_response = {
            "user": {
                "name": "Test User",
                "email": "test@example.com",
                "age": 25
            },
            "status": "active",
            "preferences": {
                "notifications": True,
                "theme": "light"
            }
        }
        
        # Set up API to return invalid then corrected response
        agent, api_double = await self.harness.create_agent_with_api_behavior(
            api_mode="adaptive"
        )
        
        # Configure staged responses
        call_count = 0
        original_call = api_double.call
        
        async def staged_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return json.dumps(invalid_response)
            else:
                return json.dumps(corrected_response)
        
        api_double.call = staged_call
        
        # Execute the validation scenario
        start_time = datetime.now()
        
        async with agent as active_agent:
            result = await active_agent.get_response(
                conversation="Create a user with semantic validation errors that need correction",
                system_prompt_info=("test", "semantic_correction"),
                schema=schema,
                current_phase="semantic_integration_test",
                operation_id="semantic_correction_integration"
            )
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Verify successful correction
        self.assertNotIn("error", result)
        self.assertIn("user", result)
        self.assertIn("status", result)
        self.assertIn("preferences", result)
        
        # Verify corrected values
        self.assertEqual(result["user"]["name"], "Test User")
        self.assertEqual(result["user"]["email"], "test@example.com")
        self.assertEqual(result["user"]["age"], 25)
        self.assertEqual(result["status"], "active")
        self.assertEqual(result["preferences"]["notifications"], True)
        self.assertEqual(result["preferences"]["theme"], "light")
        
        # Verify multiple API calls were made (indicating correction attempts)
        self.assertGreater(call_count, 1)
        
        # Verify reasonable execution time
        self.assertLess(execution_time, 30.0)  # Should complete within 30 seconds
    
    @pytest.mark.asyncio
    async def test_formatting_error_correction_pipeline(self):
        """Test the formatting error correction pipeline."""
        schema = {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "count": {"type": "integer"},
                "active": {"type": "boolean"}
            },
            "required": ["message", "count", "active"]
        }
        
        # Create response with formatting issues but valid semantics
        formatted_response = {
            "message": "Test message",
            "count": 42,
            "active": True
        }
        
        # Set up API to return response with formatting issues
        agent, api_double = await self.harness.create_agent_with_api_behavior(
            api_mode="adaptive"
        )
        
        # Override to return JSON with formatting problems
        original_call = api_double.call
        async def formatting_issue_call(*args, **kwargs):
            # Simulate response that would have formatting issues
            response = json.dumps(formatted_response, separators=(',', ':'))  # Compact format
            return response
        
        api_double.call = formatting_issue_call
        
        async with agent as active_agent:
            result = await active_agent.get_response(
                conversation="Create a response with potential formatting issues",
                system_prompt_info=("test", "formatting"),
                schema=schema,
                current_phase="formatting_integration_test",
                operation_id="formatting_correction_integration"
            )
        
        # Should succeed after formatting correction
        self.assertNotIn("error", result)
        self.assertEqual(result["message"], "Test message")
        self.assertEqual(result["count"], 42)
        self.assertEqual(result["active"], True)
    
    @pytest.mark.asyncio
    async def test_json_extraction_integration(self):
        """Test JSON extraction within the validation pipeline."""
        schema = {
            "type": "object",
            "properties": {
                "extracted": {"type": "string"},
                "from_text": {"type": "boolean"}
            },
            "required": ["extracted", "from_text"]
        }
        
        # Set up API to return JSON embedded in text
        agent, api_double = await self.harness.create_agent_with_api_behavior(
            api_mode="adaptive"
        )
        
        original_call = api_double.call
        async def text_response_call(*args, **kwargs):
            return '''
            Here's the response you requested:
            
            {"extracted": "Successfully extracted from text", "from_text": true}
            
            I hope this helps with your integration testing!
            '''
        
        api_double.call = text_response_call
        
        async with agent as active_agent:
            result = await active_agent.get_response(
                conversation="Respond with JSON embedded in explanatory text",
                system_prompt_info=("test", "extraction"),
                schema=schema,
                current_phase="extraction_integration_test",
                operation_id="json_extraction_integration"
            )
        
        # Should successfully extract and validate JSON
        self.assertNotIn("error", result)
        self.assertEqual(result["extracted"], "Successfully extracted from text")
        self.assertEqual(result["from_text"], True)
    
    @pytest.mark.asyncio
    async def test_complex_nested_validation_pipeline(self):
        """Test validation pipeline with complex nested schemas."""
        complex_schema = {
            "type": "object",
            "properties": {
                "organization": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "departments": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "employees": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "integer"},
                                                "name": {"type": "string"},
                                                "email": {"type": "string", "format": "email"},
                                                "role": {"type": "string", "enum": ["manager", "developer", "analyst"]}
                                            },
                                            "required": ["id", "name", "email", "role"]
                                        },
                                        "minItems": 1
                                    }
                                },
                                "required": ["name", "employees"]
                            },
                            "minItems": 1
                        }
                    },
                    "required": ["id", "departments"]
                }
            },
            "required": ["organization"]
        }
        
        # Create valid complex response
        complex_response = {
            "organization": {
                "id": 123,
                "departments": [
                    {
                        "name": "Engineering",
                        "employees": [
                            {
                                "id": 1,
                                "name": "Alice Johnson", 
                                "email": "alice@company.com",
                                "role": "manager"
                            },
                            {
                                "id": 2,
                                "name": "Bob Smith",
                                "email": "bob@company.com", 
                                "role": "developer"
                            }
                        ]
                    },
                    {
                        "name": "Analytics",
                        "employees": [
                            {
                                "id": 3,
                                "name": "Carol Wilson",
                                "email": "carol@company.com",
                                "role": "analyst"
                            }
                        ]
                    }
                ]
            }
        }
        
        # Set up API to return complex valid response
        agent, api_double = await self.harness.create_agent_with_api_behavior(
            api_mode="schema_compliant"
        )
        
        # Override to return our specific complex response
        original_call = api_double.call
        async def complex_response_call(*args, **kwargs):
            return json.dumps(complex_response, indent=2)
        
        api_double.call = complex_response_call
        
        async with agent as active_agent:
            result = await active_agent.get_response(
                conversation="Create a complex organizational structure",
                system_prompt_info=("test", "complex"),
                schema=complex_schema,
                current_phase="complex_integration_test",
                operation_id="complex_validation_integration"
            )
        
        # Verify complex validation succeeded
        self.assertNotIn("error", result)
        self.assertIn("organization", result)
        self.assertEqual(result["organization"]["id"], 123)
        self.assertEqual(len(result["organization"]["departments"]), 2)
        
        # Verify nested structure
        engineering_dept = result["organization"]["departments"][0]
        self.assertEqual(engineering_dept["name"], "Engineering")
        self.assertEqual(len(engineering_dept["employees"]), 2)
        
        alice = engineering_dept["employees"][0]
        self.assertEqual(alice["name"], "Alice Johnson")
        self.assertEqual(alice["email"], "alice@company.com")
        self.assertEqual(alice["role"], "manager")
    
    @pytest.mark.asyncio
    async def test_validation_state_management_integration(self):
        """Test that validation state is properly managed throughout the pipeline."""
        schema = {
            "type": "object",
            "properties": {
                "test_id": {"type": "string"},
                "timestamp": {"type": "string"}
            },
            "required": ["test_id", "timestamp"]
        }
        
        operation_id = "state_management_integration_test"
        
        # Set up scenario that requires multiple validation attempts
        agent, api_double = await self.harness.create_agent_with_api_behavior(
            api_mode="adaptive"
        )
        
        call_count = 0
        original_call = api_double.call
        
        async def multi_attempt_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First attempt: missing required field
                return json.dumps({"test_id": "test123"})
            else:
                # Subsequent attempts: complete response
                return json.dumps({
                    "test_id": "test123",
                    "timestamp": "2023-01-01T00:00:00Z"
                })
        
        api_double.call = multi_attempt_call
        
        # Check state before execution
        validation_key = f"validation:agent:{operation_id}"
        initial_state = await self.harness.state_manager.get_state(validation_key)
        self.assertIsNone(initial_state)
        
        # Execute validation
        async with agent as active_agent:
            result = await active_agent.get_response(
                conversation="Create a test response that may require validation retries",
                system_prompt_info=("test", "state"),
                schema=schema,
                current_phase="state_test",
                operation_id=operation_id
            )
        
        # Verify successful result
        self.assertNotIn("error", result)
        self.assertEqual(result["test_id"], "test123")
        self.assertIn("timestamp", result)
        
        # Verify state was created and updated
        final_state = await self.harness.state_manager.get_state(validation_key)
        self.assertIsNotNone(final_state)
        self.assertIn("attempts", final_state.state)
        self.assertIn("history", final_state.state)
        self.assertGreaterEqual(final_state.state["attempts"], 1)
        self.assertGreaterEqual(len(final_state.state["history"]), 1)
    
    @pytest.mark.asyncio
    async def test_metrics_collection_integration(self):
        """Test that metrics are properly collected throughout the validation pipeline."""
        schema = {
            "type": "object",
            "properties": {
                "metric_test": {"type": "boolean"}
            },
            "required": ["metric_test"]
        }
        
        # Clear existing metrics
        self.harness.metrics_collector.reset()
        
        # Set up simple successful scenario
        agent, api_double = await self.harness.create_agent_with_api_behavior(
            api_mode="schema_compliant"
        )
        
        async with agent as active_agent:
            result = await active_agent.get_response(
                conversation="Create a simple response for metrics testing",
                system_prompt_info=("test", "metrics"),
                schema=schema,
                current_phase="metrics_test",
                operation_id="metrics_integration_test"
            )
        
        # Verify successful result
        self.assertNotIn("error", result)
        
        # Verify metrics were collected
        recorded_metrics = self.harness.metrics_collector.get_recorded_metrics()
        self.assertGreater(len(recorded_metrics), 0)
        
        # Check for validation success rate metric
        validation_metrics = [
            metric for metric in recorded_metrics
            if metric["name"] == "agent:validation:success_rate"
        ]
        self.assertGreater(len(validation_metrics), 0)
        
        # Verify metric values
        for metric in validation_metrics:
            self.assertEqual(metric["value"], 1.0)  # Should be successful
            self.assertEqual(metric["metadata"]["phase"], "metrics_test")
            self.assertEqual(metric["metadata"]["operation_id"], "metrics_integration_test")
    
    @pytest.mark.asyncio
    async def test_error_recovery_integration(self):
        """Test error recovery mechanisms in the validation pipeline."""
        schema = {
            "type": "object",
            "properties": {
                "recovery_test": {"type": "string"},
                "attempt_number": {"type": "integer"}
            },
            "required": ["recovery_test", "attempt_number"]
        }
        
        # Set up scenario that fails multiple times before succeeding
        agent, api_double = await self.harness.create_agent_with_api_behavior(
            api_mode="adaptive"
        )
        
        call_count = 0
        original_call = api_double.call
        
        async def recovery_test_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                # First attempt: invalid JSON
                return "This is not JSON at all!"
            elif call_count == 2:
                # Second attempt: invalid schema
                return json.dumps({"wrong_field": "value"})
            else:
                # Final attempt: correct response
                return json.dumps({
                    "recovery_test": "Successfully recovered",
                    "attempt_number": call_count
                })
        
        api_double.call = recovery_test_call
        
        async with agent as active_agent:
            result = await active_agent.get_response(
                conversation="Test error recovery with multiple failure types",
                system_prompt_info=("test", "recovery"),
                schema=schema,
                current_phase="recovery_test", 
                operation_id="error_recovery_integration"
            )
        
        # Should eventually succeed after recovery
        if "error" not in result:
            self.assertEqual(result["recovery_test"], "Successfully recovered")
            self.assertEqual(result["attempt_number"], 3)
        else:
            # If it failed, verify it's a validation exceeded error
            self.assertIn("validation", result["error"]["type"])
    
    @pytest.mark.asyncio
    async def test_concurrent_validation_requests(self):
        """Test handling of concurrent validation requests."""
        schema = {
            "type": "object",
            "properties": {
                "request_id": {"type": "string"},
                "processed": {"type": "boolean"}
            },
            "required": ["request_id", "processed"]
        }
        
        async def run_validation_request(request_id: str):
            agent, api_double = await self.harness.create_agent_with_api_behavior(
                api_mode="schema_compliant"
            )
            
            # Override to return request-specific response
            original_call = api_double.call
            async def request_specific_call(*args, **kwargs):
                return json.dumps({
                    "request_id": request_id,
                    "processed": True
                })
            
            api_double.call = request_specific_call
            
            async with agent as active_agent:
                return await active_agent.get_response(
                    conversation=f"Process request {request_id}",
                    system_prompt_info=("test", "concurrent"),
                    schema=schema,
                    current_phase="concurrent_test",
                    operation_id=f"concurrent_{request_id}"
                )
        
        # Run multiple concurrent requests
        request_ids = ["req_001", "req_002", "req_003", "req_004", "req_005"]
        tasks = [run_validation_request(req_id) for req_id in request_ids]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all requests completed successfully
        self.assertEqual(len(results), 5)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.fail(f"Request {request_ids[i]} failed with exception: {result}")
            else:
                self.assertNotIn("error", result)
                self.assertEqual(result["request_id"], request_ids[i])
                self.assertEqual(result["processed"], True)


if __name__ == "__main__":
    # Run with pytest for better async support
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])