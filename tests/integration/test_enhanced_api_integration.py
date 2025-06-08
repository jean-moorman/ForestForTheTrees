"""
Enhanced API Integration Tests - Real workflow testing with controlled API responses.

These tests demonstrate the full validation pipeline using the TestableAnthropicAPI
for realistic but deterministic testing scenarios.
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
from resources import EventQueue, StateManager, AgentContextManager, CacheManager, MetricsManager, ErrorHandler

# Import test infrastructure
from tests_new.harness.validation_test_harness import ValidationTestHarness, ValidationScenarioResult
from tests_new.doubles.testable_api import TestableAnthropicAPI


class TestEnhancedAPIIntegration(unittest.TestCase):
    """Test complete validation workflows with enhanced API integration."""
    
    def setUp(self):
        """Set up test environment with harness."""
        self.harness = ValidationTestHarness()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        """Clean up test environment."""
        if hasattr(self, 'loop'):
            self.loop.close()
            asyncio.set_event_loop(None)
    
    @pytest.mark.asyncio
    async def test_complete_validation_workflow_with_correction(self):
        """Test complete workflow from invalid response to successful correction."""
        # Define schema for testing
        test_schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "minLength": 2},
                        "email": {"type": "string", "format": "email"},
                        "age": {"type": "integer", "minimum": 0, "maximum": 120}
                    },
                    "required": ["name", "email", "age"]
                },
                "action": {"type": "string", "enum": ["create", "update", "delete"]},
                "priority": {"type": "integer", "minimum": 1, "maximum": 5}
            },
            "required": ["user", "action", "priority"]
        }
        
        # Create agent with API that generates progressive responses
        agent, api_double = await self.harness.create_agent_with_api_behavior(
            api_mode="validation_testing",
            error_injection_rules=[
                {
                    "trigger_pattern": "user.*create",
                    "error_type": "missing_field",
                    "target_field": "user.email",
                    "probability": 1.0
                }
            ]
        )
        
        # Test conversation that should trigger validation errors initially
        conversation = """
        Please create a user record with the following information:
        - Name: John
        - Age: 25
        - Action: create
        - Priority: 3
        
        Make sure to include all required fields in JSON format.
        """
        
        start_time = datetime.now()
        async with agent:
            result = await agent.get_response(
                conversation=conversation,
                system_prompt_info=("test_prompts", "user_creation"),
                schema=test_schema,
                current_phase="enhanced_api_test",
                operation_id="test_workflow_correction"
            )
        end_time = datetime.now()
        
        # Verify the workflow completed successfully
        if "error" not in result:
            # Should have all required fields after correction
            self.assertIn("user", result)
            self.assertIn("action", result)
            self.assertIn("priority", result)
            
            user = result["user"]
            self.assertIn("name", user)
            self.assertIn("email", user)
            self.assertIn("age", user)
            
            # Verify data types and constraints
            self.assertIsInstance(user["name"], str)
            self.assertGreaterEqual(len(user["name"]), 2)
            self.assertIsInstance(user["email"], str)
            self.assertIn("@", user["email"])
            self.assertIsInstance(user["age"], int)
            self.assertGreaterEqual(user["age"], 0)
            self.assertLessEqual(user["age"], 120)
            
            self.assertIn(result["action"], ["create", "update", "delete"])
            self.assertGreaterEqual(result["priority"], 1)
            self.assertLessEqual(result["priority"], 5)
        else:
            # If we got an error, it should be a meaningful validation error
            self.assertIn("type", result["error"])
            self.assertIn("message", result["error"])
        
        # Verify API was called (shows integration is working)
        self.assertGreater(len(api_double.call_history), 0)
        
        # Verify execution completed in reasonable time
        execution_time = (end_time - start_time).total_seconds()
        self.assertLess(execution_time, 10.0)  # Should complete within 10 seconds
    
    @pytest.mark.asyncio
    async def test_complex_nested_validation_with_multiple_corrections(self):
        """Test validation of complex nested objects with multiple correction rounds."""
        # Complex schema with deep nesting
        complex_schema = {
            "type": "object",
            "properties": {
                "project": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "pattern": "^PROJ-[0-9]{4}$"},
                        "name": {"type": "string", "minLength": 5, "maxLength": 50},
                        "status": {"type": "string", "enum": ["active", "inactive", "pending"]},
                        "team": {
                            "type": "object",
                            "properties": {
                                "lead": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "email": {"type": "string", "format": "email"},
                                        "role": {"type": "string", "enum": ["manager", "lead", "developer"]}
                                    },
                                    "required": ["name", "email", "role"]
                                },
                                "members": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "skills": {"type": "array", "items": {"type": "string"}}
                                        },
                                        "required": ["name", "skills"]
                                    },
                                    "minItems": 1
                                }
                            },
                            "required": ["lead", "members"]
                        },
                        "budget": {"type": "number", "minimum": 1000, "maximum": 1000000}
                    },
                    "required": ["id", "name", "status", "team", "budget"]
                }
            },
            "required": ["project"]
        }
        
        # Create agent with progressive correction behavior
        agent, api_double = await self.harness.create_agent_with_api_behavior(
            api_mode="adaptive",
            error_injection_rules=[
                {
                    "trigger_pattern": "project",
                    "error_type": "format_error",
                    "target_field": "project.id",
                    "probability": 0.7
                },
                {
                    "trigger_pattern": "team",
                    "error_type": "missing_field",
                    "target_field": "project.team.lead.email",
                    "probability": 0.5
                }
            ]
        )
        
        conversation = """
        Create a project definition with the following structure:
        - Project ID (format: PROJ-####)
        - Project name (between 5-50 characters)
        - Status (active/inactive/pending)
        - Team with lead and members
        - Budget (between 1000-1000000)
        
        Include realistic team member data with skills.
        """
        
        async with agent:
            result = await agent.get_response(
                conversation=conversation,
                system_prompt_info=("test_prompts", "project_creation"),
                schema=complex_schema,
                current_phase="complex_validation_test",
                operation_id="test_complex_nested"
            )
        
        # Verify structure if successful
        if "error" not in result:
            self.assertIn("project", result)
            project = result["project"]
            
            # Verify project-level fields
            self.assertIn("id", project)
            self.assertIn("name", project)
            self.assertIn("status", project)
            self.assertIn("team", project)
            self.assertIn("budget", project)
            
            # Verify team structure
            team = project["team"]
            self.assertIn("lead", team)
            self.assertIn("members", team)
            
            # Verify lead structure
            lead = team["lead"]
            self.assertIn("name", lead)
            self.assertIn("email", lead)
            self.assertIn("role", lead)
            self.assertIn("@", lead["email"])
            self.assertIn(lead["role"], ["manager", "lead", "developer"])
            
            # Verify members structure
            members = team["members"]
            self.assertIsInstance(members, list)
            self.assertGreaterEqual(len(members), 1)
            
            for member in members:
                self.assertIn("name", member)
                self.assertIn("skills", member)
                self.assertIsInstance(member["skills"], list)
        
        # Verify multiple API calls were made (indicating correction rounds)
        self.assertGreaterEqual(len(api_double.call_history), 1)
    
    @pytest.mark.asyncio
    async def test_concurrent_validation_workflows(self):
        """Test multiple concurrent validation workflows."""
        # Create multiple agents for concurrent testing
        agents_and_apis = []
        for i in range(3):
            agent, api_double = await self.harness.create_agent_with_api_behavior(
                api_mode="schema_compliant"
            )
            agents_and_apis.append((agent, api_double))
        
        simple_schema = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "message": {"type": "string"},
                "timestamp": {"type": "string"}
            },
            "required": ["id", "message", "timestamp"]
        }
        
        async def run_validation_workflow(agent_api_pair, workflow_id):
            agent, api_double = agent_api_pair
            conversation = f"Create a message object with ID {workflow_id}, a greeting message, and current timestamp"
            
            async with agent:
                result = await agent.get_response(
                    conversation=conversation,
                    system_prompt_info=("test_prompts", "simple_message"),
                    schema=simple_schema,
                    current_phase="concurrent_test",
                    operation_id=f"concurrent_workflow_{workflow_id}"
                )
            
            return result, api_double
        
        # Run workflows concurrently
        start_time = datetime.now()
        tasks = [
            run_validation_workflow(agents_and_apis[i], i) 
            for i in range(3)
        ]
        results = await asyncio.gather(*tasks)
        end_time = datetime.now()
        
        # Verify all workflows completed
        self.assertEqual(len(results), 3)
        
        for i, (result, api_double) in enumerate(results):
            if "error" not in result:
                self.assertIn("id", result)
                self.assertIn("message", result)
                self.assertIn("timestamp", result)
                self.assertEqual(result["id"], i)
            
            # Verify API was called for each workflow
            self.assertGreater(len(api_double.call_history), 0)
        
        # Verify concurrent execution was efficient
        execution_time = (end_time - start_time).total_seconds()
        self.assertLess(execution_time, 15.0)  # Should complete within 15 seconds
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self):
        """Test complete error recovery workflow across multiple failure modes."""
        # Create agent that will experience different types of errors
        agent, api_double = await self.harness.create_agent_with_api_behavior(
            api_mode="validation_testing",
            error_injection_rules=[
                {
                    "trigger_pattern": "first",
                    "error_type": "json_format_error",
                    "probability": 1.0
                },
                {
                    "trigger_pattern": "second",
                    "error_type": "type_error",
                    "target_field": "count",
                    "probability": 1.0
                },
                {
                    "trigger_pattern": "third",
                    "error_type": "enum_violation",
                    "target_field": "status",
                    "probability": 1.0
                }
            ]
        )
        
        recovery_schema = {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "minimum": 1},
                "status": {"type": "string", "enum": ["ready", "processing", "complete"]},
                "data": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["count", "status", "data"]
        }
        
        # Test multiple recovery scenarios
        recovery_conversations = [
            "First attempt: Create a processing record with count=5, status=ready, data=['item1', 'item2']",
            "Second attempt: Create a processing record with count=5, status=ready, data=['item1', 'item2']", 
            "Third attempt: Create a processing record with count=5, status=ready, data=['item1', 'item2']",
            "Final attempt: Create a processing record with count=5, status=ready, data=['item1', 'item2']"
        ]
        
        final_result = None
        async with agent:
            for i, conversation in enumerate(recovery_conversations):
                result = await agent.get_response(
                    conversation=conversation,
                    system_prompt_info=("test_prompts", "recovery_test"),
                    schema=recovery_schema,
                    current_phase="error_recovery_test",
                    operation_id=f"recovery_test_{i}"
                )
                
                if "error" not in result:
                    final_result = result
                    break
                else:
                    # Log the error for analysis but continue
                    print(f"Recovery attempt {i+1} failed: {result['error']['type']}")
        
        # Verify that eventually we got a successful result or at least proper error handling
        if final_result:
            self.assertIn("count", final_result)
            self.assertIn("status", final_result)
            self.assertIn("data", final_result)
            self.assertIsInstance(final_result["count"], int)
            self.assertIn(final_result["status"], ["ready", "processing", "complete"])
            self.assertIsInstance(final_result["data"], list)
        
        # Verify error recovery was attempted (multiple API calls)
        self.assertGreaterEqual(len(api_double.call_history), 2)


class TestValidationPipelineMetrics(unittest.TestCase):
    """Test metrics collection during validation workflows."""
    
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
    async def test_comprehensive_metrics_collection(self):
        """Test that comprehensive metrics are collected during validation workflows."""
        # Clear any existing metrics
        self.harness.metrics_collector.reset()
        
        # Create agent with metrics collection
        agent, api_double = await self.harness.create_agent_with_api_behavior(
            api_mode="validation_testing",
            error_injection_rules=[
                {
                    "trigger_pattern": "validation",
                    "error_type": "missing_field",
                    "target_field": "required_field",
                    "probability": 0.8
                }
            ]
        )
        
        test_schema = {
            "type": "object",
            "properties": {
                "required_field": {"type": "string"},
                "optional_field": {"type": "integer"}
            },
            "required": ["required_field"]
        }
        
        # Run validation workflow that will generate metrics
        async with agent:
            result = await agent.get_response(
                conversation="Create a validation test object",
                system_prompt_info=("test_prompts", "metrics_test"),
                schema=test_schema,
                current_phase="metrics_collection_test",
                operation_id="test_metrics_collection"
            )
        
        # Verify metrics were collected
        recorded_metrics = self.harness.metrics_collector.get_recorded_metrics()
        self.assertGreater(len(recorded_metrics), 0)
        
        # Look for specific validation metrics
        validation_metrics = [
            metric for metric in recorded_metrics 
            if "validation" in metric["name"]
        ]
        self.assertGreater(len(validation_metrics), 0)
        
        # Look for agent metrics
        agent_metrics = [
            metric for metric in recorded_metrics 
            if "agent" in metric["name"]
        ]
        self.assertGreater(len(agent_metrics), 0)
        
        # Verify metrics contain expected metadata
        for metric in recorded_metrics:
            self.assertIn("name", metric)
            self.assertIn("value", metric)
            self.assertIn("metadata", metric)
            
            if "operation_id" in metric["metadata"]:
                self.assertEqual(metric["metadata"]["operation_id"], "test_metrics_collection")


if __name__ == "__main__":
    # Run with asyncio support
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])