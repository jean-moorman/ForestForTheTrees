"""
ValidationTestHarness - Controlled testing environment for validation workflows.

This harness provides a complete testing environment that uses real components
but with controlled, deterministic behavior for reliable testing.
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

# Import actual system components
from agent import Agent
from agent_validation import Validator, ValidationErrorAnalyzer, SemanticErrorHandler
from resources import (
    EventQueue, StateManager, AgentContextManager, CacheManager, 
    MetricsManager, ErrorHandler, ResourceType
)

# Import our test doubles
from tests_new.doubles.testable_api import TestableAnthropicAPI, RealMetricsCollector


@dataclass
class ValidationScenarioResult:
    """Complete result of a validation scenario test."""
    success: bool
    final_result: Dict[str, Any]
    api_calls: List[Any]
    metrics: List[Dict[str, Any]]
    state_changes: List[Dict[str, Any]]
    validation_attempts: int
    error_analysis: Optional[Dict[str, Any]] = None
    execution_time_ms: float = 0.0


class ValidationTestHarness:
    """
    Harness for testing validation workflows with real components.
    
    This replaces the current mock-heavy approach with a controlled environment
    that uses actual validation logic but with deterministic API responses.
    """
    
    def __init__(self):
        """Initialize the test harness with real components."""
        self.event_queue = EventQueue()
        self.state_manager = StateManager(self.event_queue)
        self.context_manager = AgentContextManager(self.event_queue)
        self.cache_manager = CacheManager(self.event_queue)
        self.metrics_collector = RealMetricsCollector()
        self.error_handler = ErrorHandler(self.event_queue)
        
        # Track state changes for verification
        self.state_changes: List[Dict[str, Any]] = []
        self._setup_state_monitoring()
        
    def _setup_state_monitoring(self):
        """Set up monitoring of state changes for test verification."""
        original_set_state = self.state_manager.set_state
        
        async def monitored_set_state(resource_id: str, state: Dict[str, Any], 
                                     resource_type: ResourceType):
            self.state_changes.append({
                "timestamp": datetime.now(),
                "resource_id": resource_id,
                "state": state.copy(),
                "resource_type": resource_type
            })
            return await original_set_state(resource_id, state, resource_type)
        
        self.state_manager.set_state = monitored_set_state
    
    async def create_agent_with_api_behavior(self, api_mode: str = "adaptive", 
                                           custom_responses: Optional[Dict[str, str]] = None,
                                           error_injection_rules: Optional[List[Dict[str, Any]]] = None) -> Tuple[Agent, TestableAnthropicAPI]:
        """
        Create an agent with testable API but real validation pipeline.
        
        Args:
            api_mode: Response generation mode for the API double
            custom_responses: Custom responses for specific conversation patterns
            error_injection_rules: Rules for injecting specific validation errors
            
        Returns:
            Tuple of (Agent instance, API double for test verification)
        """
        # Create testable API with specified behavior
        api_double = TestableAnthropicAPI(response_mode=api_mode)
        
        if custom_responses:
            for pattern, response in custom_responses.items():
                api_double.set_custom_response(pattern, response)
                
        if error_injection_rules:
            for rule in error_injection_rules:
                api_double.add_error_injection_rule(rule)
        
        # Create agent with real components but testable API
        agent = Agent(
            event_queue=self.event_queue,
            state_manager=self.state_manager,
            context_manager=self.context_manager,
            cache_manager=self.cache_manager,
            metrics_manager=self.metrics_collector,  # Use our real metrics collector
            error_handler=self.error_handler,
            model="claude-3-7-sonnet-20250219"
        )
        
        # Replace only the API client, keep all validation logic
        agent.api = api_double
        
        return agent, api_double
    
    async def run_validation_scenario(self, 
                                    scenario_name: str,
                                    conversation: str, 
                                    schema: Dict[str, Any],
                                    api_mode: str = "adaptive",
                                    custom_responses: Optional[Dict[str, str]] = None,
                                    error_injection_rules: Optional[List[Dict[str, Any]]] = None,
                                    expected_attempts: Optional[int] = None) -> ValidationScenarioResult:
        """
        Run a complete validation scenario and return detailed results.
        
        This method exercises the real validation pipeline with controlled inputs
        and captures comprehensive test data for verification.
        """
        start_time = datetime.now()
        
        # Reset state for clean test
        self.state_changes.clear()
        self.metrics_collector.reset()
        
        # Create agent with specified API behavior
        agent, api_double = await self.create_agent_with_api_behavior(
            api_mode=api_mode,
            custom_responses=custom_responses,
            error_injection_rules=error_injection_rules
        )
        
        # Execute the validation scenario
        try:
            async with agent as active_agent:
                result = await active_agent.get_response(
                    conversation=conversation,
                    system_prompt_info=("test_harness", "scenario"),
                    schema=schema,
                    current_phase=f"test_{scenario_name}",
                    operation_id=f"harness_{scenario_name}_{int(start_time.timestamp())}"
                )
        except Exception as e:
            result = {"error": {"type": "harness_error", "message": str(e)}}
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds() * 1000
        
        # Determine success
        success = "error" not in result
        
        # Extract validation attempts from state changes
        validation_attempts = len([
            change for change in self.state_changes 
            if "validation:agent:" in change["resource_id"] and 
               "attempts" in change.get("state", {})
        ])
        
        # Create comprehensive result
        scenario_result = ValidationScenarioResult(
            success=success,
            final_result=result,
            api_calls=api_double.get_call_history(),
            metrics=self.metrics_collector.get_recorded_metrics(),
            state_changes=self.state_changes.copy(),
            validation_attempts=validation_attempts,
            execution_time_ms=execution_time
        )
        
        # Add error analysis if available
        if not success and "error" in result:
            scenario_result.error_analysis = result["error"]
        
        return scenario_result
    
    async def test_semantic_error_correction_flow(self, 
                                                schema: Dict[str, Any],
                                                invalid_response: Dict[str, Any],
                                                expected_correction: Dict[str, Any]) -> ValidationScenarioResult:
        """
        Test the complete semantic error correction flow.
        
        This creates a scenario where the first API call returns invalid data,
        then subsequent calls return progressively better responses.
        """
        call_count = 0
        
        def staged_response_generator():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return json.dumps(invalid_response)
            else:
                return json.dumps(expected_correction)
        
        # Set up custom responses for correction flow
        custom_responses = {
            ".*": staged_response_generator()  # Will be called for any conversation
        }
        
        # Create API double with staged responses
        api_double = TestableAnthropicAPI(response_mode="adaptive")
        
        # Override the call method to provide staged responses
        original_call = api_double.call
        async def staged_call(*args, **kwargs):
            if call_count == 0:
                call_count += 1
                return json.dumps(invalid_response)
            else:
                return json.dumps(expected_correction)
        
        api_double.call = staged_call
        
        # Create agent with staged API
        agent = Agent(
            event_queue=self.event_queue,
            state_manager=self.state_manager,
            context_manager=self.context_manager,
            cache_manager=self.cache_manager,
            metrics_manager=self.metrics_collector,
            error_handler=self.error_handler
        )
        agent.api = api_double
        
        # Run the scenario
        start_time = datetime.now()
        try:
            async with agent as active_agent:
                result = await active_agent.get_response(
                    conversation="Test semantic error correction",
                    system_prompt_info=("test", "semantic_correction"),
                    schema=schema,
                    operation_id="semantic_correction_test"
                )
        except Exception as e:
            result = {"error": {"type": "test_error", "message": str(e)}}
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds() * 1000
        
        return ValidationScenarioResult(
            success="error" not in result,
            final_result=result,
            api_calls=api_double.get_call_history(),
            metrics=self.metrics_collector.get_recorded_metrics(),
            state_changes=self.state_changes.copy(),
            validation_attempts=call_count,
            execution_time_ms=execution_time
        )
    
    async def create_validator_with_real_components(self) -> Validator:
        """Create a Validator instance with real components for isolated testing."""
        # Create a mock correction handler for validator testing
        class TestCorrectionHandler:
            async def handle_correction_request(self, request):
                from agent import CorrectionResult
                return CorrectionResult(
                    corrected_output={"corrected": True},
                    success=True
                )
        
        correction_handler = TestCorrectionHandler()
        
        validator = Validator(
            event_queue=self.event_queue,
            state_manager=self.state_manager,
            correction_handler=correction_handler
        )
        
        return validator
    
    async def create_error_analyzer_with_real_components(self) -> ValidationErrorAnalyzer:
        """Create a ValidationErrorAnalyzer with real components."""
        validator = await self.create_validator_with_real_components()
        
        analyzer = ValidationErrorAnalyzer(
            validator=validator,
            event_queue=self.event_queue,
            state_manager=self.state_manager
        )
        
        return analyzer
    
    async def create_semantic_handler_with_real_components(self) -> SemanticErrorHandler:
        """Create a SemanticErrorHandler with real components."""
        validator = await self.create_validator_with_real_components()
        
        # Create a test correction handler
        class TestCorrectionHandler:
            def __init__(self):
                self.call_count = 0
                
            async def handle_correction_request(self, request):
                from agent import CorrectionResult
                self.call_count += 1
                
                # Simulate progressive correction
                if self.call_count == 1:
                    # First attempt - partial correction
                    return CorrectionResult(
                        corrected_output={"name": "Test", "email": "invalid-email"},
                        success=True
                    )
                else:
                    # Subsequent attempts - full correction
                    return CorrectionResult(
                        corrected_output={"name": "Test", "email": "test@example.com"},
                        success=True
                    )
        
        correction_handler = TestCorrectionHandler()
        
        semantic_handler = SemanticErrorHandler(
            validator=validator,
            event_queue=self.event_queue,
            state_manager=self.state_manager,
            correction_handler=correction_handler
        )
        
        return semantic_handler
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics collected during tests."""
        return self.metrics_collector.get_all_metric_summaries()
    
    def get_state_change_summary(self) -> Dict[str, Any]:
        """Get a summary of state changes during tests."""
        return {
            "total_changes": len(self.state_changes),
            "resources_modified": len(set(change["resource_id"] for change in self.state_changes)),
            "change_timeline": [
                {
                    "timestamp": change["timestamp"].isoformat(),
                    "resource_id": change["resource_id"],
                    "resource_type": change["resource_type"].value if hasattr(change["resource_type"], 'value') else str(change["resource_type"])
                }
                for change in self.state_changes
            ]
        }
    
    def reset(self):
        """Reset the harness state for a new test."""
        self.state_changes.clear()
        self.metrics_collector.reset()


# Utility functions for test data generation
def create_test_schema_with_constraints() -> Dict[str, Any]:
    """Create a test schema with various constraint types for validation testing."""
    return {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "minLength": 2,
                "maxLength": 50
            },
            "email": {
                "type": "string", 
                "format": "email"
            },
            "age": {
                "type": "integer",
                "minimum": 0,
                "maximum": 150
            },
            "status": {
                "type": "string",
                "enum": ["active", "inactive", "pending"]
            },
            "preferences": {
                "type": "object",
                "properties": {
                    "notifications": {"type": "boolean"},
                    "theme": {"type": "string", "enum": ["light", "dark"]}
                },
                "required": ["notifications"]
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "maxItems": 10
            }
        },
        "required": ["name", "email", "status"]
    }


def create_complex_nested_schema() -> Dict[str, Any]:
    """Create a complex nested schema for testing deep validation."""
    return {
        "type": "object",
        "properties": {
            "user": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "profile": {
                        "type": "object",
                        "properties": {
                            "personal": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "contacts": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "type": {"type": "string", "enum": ["email", "phone"]},
                                                "value": {"type": "string"},
                                                "primary": {"type": "boolean"}
                                            },
                                            "required": ["type", "value"]
                                        }
                                    }
                                },
                                "required": ["name", "contacts"]
                            }
                        },
                        "required": ["personal"]
                    }
                },
                "required": ["id", "profile"]
            }
        },
        "required": ["user"]
    }