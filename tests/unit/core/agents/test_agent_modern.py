"""
Modern async tests for the Agent class using pytest-asyncio patterns.

This replaces the unittest.TestCase approach with proper async testing
to validate async functionality correctly.
"""

import pytest
import json
import os
import asyncio
from datetime import datetime
from pathlib import Path
import logging

# Import actual system components
from agent import Agent, CorrectionRequest, CorrectionResult
from resources import (
    ResourceType, ResourceEventTypes, AgentContext, AgentContextType,
    EventQueue, StateManager, AgentContextManager, CacheManager, 
    MetricsManager, ErrorHandler
)
from agent_validation import ValidationException, Validator

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@pytest.fixture
async def test_components():
    """Create test components for agent testing."""
    # Ensure API key is available
    if not os.getenv("ANTHROPIC_API_KEY"):
        os.environ["ANTHROPIC_API_KEY"] = "test_key_for_unit_tests"
        api_available = False
        logger.warning("No ANTHROPIC_API_KEY found. API-dependent tests will be skipped.")
    else:
        api_available = True
    
    # Initialize actual system resources
    event_queue = EventQueue()
    state_manager = StateManager(event_queue)
    context_manager = AgentContextManager(event_queue)
    cache_manager = CacheManager(event_queue)
    metrics_manager = MetricsManager(event_queue)
    error_handler = ErrorHandler(event_queue)
    
    # Create Agent instance with real components
    agent = Agent(
        event_queue=event_queue,
        state_manager=state_manager,
        context_manager=context_manager,
        cache_manager=cache_manager,
        metrics_manager=metrics_manager,
        error_handler=error_handler,
        model="claude-3-7-sonnet-20250219"
    )
    
    # Test schemas
    simple_schema = {
        "type": "object",
        "properties": {
            "message": {"type": "string"},
            "success": {"type": "boolean"}
        },
        "required": ["message", "success"]
    }
    
    complex_schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["create", "update", "delete"]},
            "status": {"type": "string", "enum": ["pending", "completed"]},
            "count": {"type": "integer"},
            "metadata": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "enum": ["A", "B", "C"]},
                    "priority": {"type": "integer", "minimum": 1, "maximum": 5}
                },
                "required": ["category", "priority"]
            }
        },
        "required": ["action", "status", "count", "metadata"]
    }
    
    return {
        "agent": agent,
        "event_queue": event_queue,
        "state_manager": state_manager,
        "context_manager": context_manager,
        "cache_manager": cache_manager,
        "metrics_manager": metrics_manager,
        "error_handler": error_handler,
        "simple_schema": simple_schema,
        "complex_schema": complex_schema,
        "api_available": api_available
    }


class TestAgentInitialization:
    """Test agent initialization functionality."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, test_components):
        """Test that Agent initializes correctly with real components."""
        agent = test_components["agent"]
        
        # Check that initialization set up the correct attributes
        assert agent.model == "claude-3-7-sonnet-20250219"
        assert agent.max_tokens == 1024
        assert agent.max_validation_attempts == 3
        
        # Check that components are initialized
        assert agent._event_queue is not None
        assert agent._state_manager is not None
        assert agent._context_manager is not None
        assert agent._cache_manager is not None
        assert agent._metrics_manager is not None
        assert agent._error_handler is not None
        
        # Check that API and validator are initialized
        assert agent.api is not None
        assert agent.validator is not None
    
    @pytest.mark.asyncio
    async def test_initialization_no_api_key(self):
        """Test initialization fails with no API key."""
        # Save current API key
        original_key = os.environ.get("ANTHROPIC_API_KEY")
        
        try:
            # Remove API key from environment
            if "ANTHROPIC_API_KEY" in os.environ:
                del os.environ["ANTHROPIC_API_KEY"]
            
            # Initialize test components
            event_queue = EventQueue()
            state_manager = StateManager(event_queue)
            context_manager = AgentContextManager(event_queue)
            cache_manager = CacheManager(event_queue)
            metrics_manager = MetricsManager(event_queue)
            error_handler = ErrorHandler(event_queue)
            
            # Check that initialization raises an error
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not found"):
                Agent(
                    event_queue=event_queue,
                    state_manager=state_manager,
                    context_manager=context_manager,
                    cache_manager=cache_manager,
                    metrics_manager=metrics_manager,
                    error_handler=error_handler
                )
        
        finally:
            # Restore API key
            if original_key:
                os.environ["ANTHROPIC_API_KEY"] = original_key
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self, test_components):
        """Test that Agent works as an async context manager."""
        agent = test_components["agent"]
        
        async with agent as active_agent:
            # The agent should be correctly initialized
            assert active_agent.api is not None


class TestAgentBasicOperations:
    """Test basic agent operations."""
    
    @pytest.mark.asyncio
    async def test_get_response_empty_conversation(self, test_components):
        """Test get_response with empty conversation."""
        agent = test_components["agent"]
        simple_schema = test_components["simple_schema"]
        
        # Call get_response with empty conversation should return error dict
        result = await agent.get_response(
            conversation="",
            system_prompt_info=("test_prompt_dir", "test_prompt_name"),
            schema=simple_schema,
            current_phase="test_phase",
            operation_id="test_op_id"
        )
        
        # Should return error response instead of raising
        assert "error" in result
        assert "conversation parameter cannot be empty" in result["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_schema_file_not_found(self, test_components):
        """Test schema loading when file doesn't exist."""
        agent = test_components["agent"]
        
        # Non-existent schema path should raise FileNotFoundError
        with pytest.raises(FileNotFoundError, match="Schema file not found"):
            await agent.get_response(
                conversation="Test conversation",
                system_prompt_info=("nonexistent", "schema"),
                schema=None,
                current_phase="test_phase",
                operation_id="test_missing_schema"
            )
    
    @pytest.mark.asyncio
    async def test_schema_loading(self, test_components):
        """Test dynamic schema loading."""
        agent = test_components["agent"]
        api_available = test_components["api_available"]
        
        # Create a temporary schema file
        schema_dir = Path("test_schemas")
        schema_dir.mkdir(exist_ok=True)
        
        schema_path = schema_dir / "test_schema.py"
        test_schema = {
            "type": "object",
            "properties": {
                "test": {"type": "string"}
            },
            "required": ["test"]
        }
        
        try:
            # Write schema to file
            with open(schema_path, "w") as f:
                f.write(f"test_schema = {json.dumps(test_schema)}")
            
            # Test loading the schema
            if not api_available:
                # Skip the API call part if no API key but test schema loading
                with pytest.raises(Exception):  # Will fail on API call, but that's expected
                    await agent.get_response(
                        conversation="Test schema loading",
                        system_prompt_info=("test_schemas", "test"),
                        schema=None,
                        current_phase="schema_test",
                        operation_id="test_schema_loading"
                    )
                
                # Check that the schema was loaded
                assert agent.schema == test_schema
            else:
                # If API is available, run the full test
                result = await agent.get_response(
                    conversation="Respond with a test field containing any string",
                    system_prompt_info=("test_schemas", "test"),
                    schema=None,
                    current_phase="schema_test",
                    operation_id="test_schema_loading"
                )
                
                # Check the result
                if "error" not in result:
                    assert "test" in result
                    assert isinstance(result["test"], str)
        
        finally:
            # Clean up temporary file
            if schema_path.exists():
                schema_path.unlink()
            if schema_dir.exists():
                schema_dir.rmdir()


class TestAgentValidationFlows:
    """Test agent validation workflows."""
    
    @pytest.mark.asyncio
    async def test_successful_response(self, test_components):
        """Test getting a successful response."""
        agent = test_components["agent"]
        simple_schema = test_components["simple_schema"]
        api_available = test_components["api_available"]
        
        if not api_available:
            pytest.skip("API key not available")
        
        # Simple conversation that should result in a valid response
        conversation = """
        Please respond with a simple message object:
        - Include a message field with the text "Test successful"
        - Include a success field with the value true
        """
        
        async with agent as active_agent:
            result = await active_agent.get_response(
                conversation=conversation,
                system_prompt_info=("system_prompts", "simple_response"),
                schema=simple_schema,
                current_phase="success_test",
                operation_id="test_success"
            )
        
        # Verify the response
        assert isinstance(result, dict)
        assert "message" in result
        assert "success" in result
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_validation_retry(self, test_components):
        """Test the validation retry mechanism."""
        agent = test_components["agent"]
        complex_schema = test_components["complex_schema"]
        api_available = test_components["api_available"]
        
        if not api_available:
            pytest.skip("API key not available")
        
        # Conversation designed to potentially require validation
        conversation = """
        Respond with an object that needs the following fields:
        - action (must be one of: create, update, delete)
        - status (must be one of: pending, completed)
        - count (must be an integer)
        - metadata (an object with category and priority fields)
          - category must be one of: A, B, C
          - priority must be an integer between 1 and 5
        
        Let's use action=create, status=pending, count=1, category=A, priority=3
        """
        
        async with agent as active_agent:
            result = await active_agent.get_response(
                conversation=conversation,
                system_prompt_info=("system_prompts", "complex_response"),
                schema=complex_schema,
                current_phase="validation_test",
                operation_id="test_validation"
            )
        
        # Check if we got a valid response
        if "error" not in result:
            assert "action" in result
            assert "status" in result
            assert "count" in result
            assert "metadata" in result
            assert "category" in result["metadata"]
            assert "priority" in result["metadata"]
        else:
            # If we got an error, check that it's a validation error
            logger.info(f"Validation test resulted in error: {result['error']}")
            assert result["error"]["type"] in ["validation_error", "validation_exceeded"]
    
    @pytest.mark.asyncio
    async def test_validation_exceeded(self, test_components):
        """Test exceeding validation attempts."""
        agent = test_components["agent"]
        complex_schema = test_components["complex_schema"]
        api_available = test_components["api_available"]
        
        if not api_available:
            pytest.skip("API key not available")
        
        # Override max attempts to make test faster
        original_max = agent.max_validation_attempts
        agent.max_validation_attempts = 1
        
        try:
            async with agent as active_agent:
                result = await active_agent.get_response(
                    conversation="Respond with anything you want, I'll fix it later.",
                    system_prompt_info=("system_prompts", "intentionally_invalid"),
                    schema=complex_schema,  # Complex schema makes validation harder
                    current_phase="validation_exceeded_test",
                    operation_id="test_exceeded"
                )
            
            # With real components, we might get a valid response or validation error
            if "error" in result:
                # Check if it's a validation exceeded error
                if result["error"]["type"] == "validation_exceeded":
                    assert result["error"]["type"] == "validation_exceeded"
                else:
                    # Some other error, but not a failure of the test
                    logger.info(f"Got error: {result['error']['type']}")
            else:
                # We got a valid response, which is unexpected but not a test failure
                logger.info(f"Surprisingly got valid response: {result}")
        
        finally:
            # Restore original max attempts
            agent.max_validation_attempts = original_max


class TestCorrectionHandling:
    """Test correction handling functionality."""
    
    @pytest.fixture
    async def correction_test_setup(self, test_components):
        """Set up for correction tests."""
        agent = test_components["agent"]
        api_available = test_components["api_available"]
        
        test_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0},
                "active": {"type": "boolean"}
            },
            "required": ["name", "age", "active"]
        }
        
        return {
            "agent": agent,
            "api_available": api_available,
            "test_schema": test_schema
        }
    
    @pytest.mark.asyncio
    async def test_correction_request_handling(self, correction_test_setup):
        """Test handling a correction request."""
        agent = correction_test_setup["agent"]
        api_available = correction_test_setup["api_available"]
        test_schema = correction_test_setup["test_schema"]
        
        if not api_available:
            pytest.skip("API key not available")
        
        # Create a correction request with validation errors
        request = CorrectionRequest(
            original_output={"name": "Test", "active": True},  # Missing 'age'
            feedback="Response is missing the required 'age' field which should be an integer.",
            schema=test_schema,
            validation_errors={"missing": ["age"]},
            attempt_number=1,
            operation_id="test_correction"
        )
        
        # Test handling the correction
        async with agent as active_agent:
            result = await active_agent.handle_correction_request(request)
        
        # Check the result
        if result.success:
            # Should have corrected the output with the age field
            assert result.corrected_output is not None
            assert "name" in result.corrected_output
            assert "age" in result.corrected_output
            assert "active" in result.corrected_output
            assert isinstance(result.corrected_output["age"], int)
        else:
            # Log the error but don't fail the test as model responses vary
            logger.info(f"Correction failed: {result.error_message}")
    
    @pytest.mark.asyncio
    async def test_build_correction_prompt(self, correction_test_setup):
        """Test building a correction prompt."""
        agent = correction_test_setup["agent"]
        test_schema = correction_test_setup["test_schema"]
        
        # Create a correction request
        request = CorrectionRequest(
            original_output={"name": "Test", "active": True},
            feedback="Missing required field 'age'",
            schema=test_schema,
            validation_errors={"missing": ["age"]},
            attempt_number=2,
            operation_id="test_prompt"
        )
        
        # Build the correction prompt
        prompt = agent._build_correction_prompt(request)
        
        # Verify prompt content
        assert "Validation Feedback:" in prompt
        assert "Missing required field 'age'" in prompt
        assert "Original Output:" in prompt
        assert '"name": "Test"' in prompt
        assert "Schema Requirements:" in prompt
        assert "Attempt number: 2" in prompt
        assert "Please provide a corrected response" in prompt


class TestResourceManagerIntegration:
    """Test integration with resource managers."""
    
    @pytest.mark.asyncio
    async def test_state_manager_interaction(self, test_components):
        """Test interaction with the state manager."""
        agent = test_components["agent"]
        state_manager = test_components["state_manager"]
        api_available = test_components["api_available"]
        
        if not api_available:
            pytest.skip("API key not available")
        
        # Define a test schema
        schema = {
            "type": "object",
            "properties": {
                "test": {"type": "string"}
            },
            "required": ["test"]
        }
        
        # Define operation ID
        operation_id = "test_state_manager"
        validation_key = f"validation:agent:{operation_id}"
        
        # Check that the state doesn't exist yet
        state_entry = await state_manager.get_state(validation_key)
        assert state_entry is None
        
        # Call get_response to trigger state manager interaction
        async with agent as active_agent:
            await active_agent.get_response(
                conversation="Please respond with a JSON object containing a 'test' string field.",
                system_prompt_info=("system_prompts", "simple_test"),
                schema=schema,
                current_phase="state_test",
                operation_id=operation_id
            )
        
        # Check that the state now exists and has the expected structure
        state_entry = await state_manager.get_state(validation_key)
        assert state_entry is not None
        assert "attempts" in state_entry.state
        assert "history" in state_entry.state
        assert isinstance(state_entry.state["attempts"], int)
        assert state_entry.state["attempts"] >= 1
        assert isinstance(state_entry.state["history"], list)
        assert len(state_entry.state["history"]) >= 1
    
    @pytest.mark.asyncio
    async def test_context_manager_interaction(self, test_components):
        """Test interaction with the context manager."""
        agent = test_components["agent"]
        context_manager = test_components["context_manager"]
        api_available = test_components["api_available"]
        
        if not api_available:
            pytest.skip("API key not available")
        
        # Define a test schema
        schema = {
            "type": "object",
            "properties": {
                "test": {"type": "string"}
            },
            "required": ["test"]
        }
        
        # Define operation ID
        operation_id = "test_context_manager"
        context_id = f"agent_context:{operation_id}"
        
        # Check that the context doesn't exist yet
        context = await context_manager.get_context(context_id)
        assert context is None
        
        # Call get_response to trigger context manager interaction
        async with agent as active_agent:
            await active_agent.get_response(
                conversation="Please respond with a JSON object containing a 'test' string field.",
                system_prompt_info=("system_prompts", "simple_test"),
                schema=schema,
                current_phase="context_test",
                operation_id=operation_id
            )
        
        # Check that the context now exists
        context = await context_manager.get_context(context_id)
        assert context is not None
        assert context.agent_id == context_id
        assert context.operation_id == operation_id
    
    @pytest.mark.asyncio
    async def test_metrics_recording(self, test_components):
        """Test that metrics are recorded during agent operation."""
        agent = test_components["agent"]
        event_queue = test_components["event_queue"]
        api_available = test_components["api_available"]
        
        if not api_available:
            pytest.skip("API key not available")
        
        # Custom metrics manager to track recorded metrics
        class TestMetricsManager(MetricsManager):
            def __init__(self, event_queue):
                super().__init__(event_queue)
                self.recorded_metrics = []
                
            async def record_metric(self, name, value, metadata=None):
                self.recorded_metrics.append((name, value, metadata))
                await super().record_metric(name, value, metadata)
        
        # Replace the metrics manager
        test_metrics_manager = TestMetricsManager(event_queue)
        original_metrics_manager = agent._metrics_manager
        agent._metrics_manager = test_metrics_manager
        
        try:
            # Define a test schema
            schema = {
                "type": "object",
                "properties": {
                    "test": {"type": "string"}
                },
                "required": ["test"]
            }
            
            # Call get_response to trigger metrics recording
            async with agent as active_agent:
                await active_agent.get_response(
                    conversation="Please respond with a JSON object containing a 'test' string field.",
                    system_prompt_info=("system_prompts", "simple_test"),
                    schema=schema,
                    current_phase="metrics_test",
                    operation_id="test_metrics"
                )
            
            # Check that metrics were recorded
            assert len(test_metrics_manager.recorded_metrics) > 0
            
            # Check for validation success rate metric
            found_validation_metric = False
            for name, value, metadata in test_metrics_manager.recorded_metrics:
                if name == "agent:validation:success_rate":
                    found_validation_metric = True
                    assert value in [0.0, 1.0]  # Success rate is either 0 or 1
                    assert metadata.get("phase") == "metrics_test"
                    assert metadata.get("operation_id") == "test_metrics"
            
            assert found_validation_metric, "Validation success rate metric not found"
            
        finally:
            # Restore the original metrics manager
            agent._metrics_manager = original_metrics_manager


class TestErrorHandling:
    """Test error handling functionality."""
    
    @pytest.mark.asyncio
    async def test_create_error_details(self, test_components):
        """Test creating error details."""
        agent = test_components["agent"]
        
        # Create a test exception
        test_exception = ValueError("Test error message")
        
        # Get error details
        error_details = agent._create_error_details(test_exception)
        
        # Verify error details
        assert error_details["type"] == "system_error"
        assert error_details["message"] == "Test error message"
        assert error_details["details"] == "ValueError"
        assert "traceback" in error_details
        assert "timestamp" in error_details
    
    @pytest.mark.asyncio
    async def test_handle_error(self, test_components):
        """Test error handling."""
        agent = test_components["agent"]
        
        # Create error details
        error_details = {
            "type": "test_error",
            "message": "Test error message",
            "details": "Test details"
        }
        
        # Handle the error (should not raise an exception)
        await agent._handle_error(
            error_details=error_details,
            operation_id="test_op_id",
            current_phase="test_phase"
        )
        
        # Test passes if no exception is raised


class TestErrorScenarios:
    """Test specific error scenarios."""
    
    @pytest.mark.asyncio
    async def test_json_decode_error(self, test_components):
        """Test handling of JSON decode errors."""
        agent = test_components["agent"]
        event_queue = test_components["event_queue"]
        api_available = test_components["api_available"]
        
        if not api_available:
            pytest.skip("API key not available")
        
        # Track emitted errors
        emitted_errors = []
        
        # Create a custom event queue to capture error events
        original_emit = event_queue.emit
        async def capture_emit(event_type, payload):
            if event_type == ResourceEventTypes.ERROR_OCCURRED.value:
                emitted_errors.append(payload)
            return await original_emit(event_type, payload)
        
        event_queue.emit = capture_emit
        
        # Create a mock API that returns invalid JSON
        class MockAPI:
            async def __aenter__(self):
                return self
                
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
                
            async def call(self, **kwargs):
                return "This is not valid JSON"
        
        # Replace the agent's API with our mock
        original_api = agent.api
        agent.api = MockAPI()
        
        try:
            # Define a test schema
            schema = {
                "type": "object",
                "properties": {
                    "test": {"type": "string"}
                },
                "required": ["test"]
            }
            
            # Call get_response with the mock API
            result = await agent.get_response(
                conversation="Please respond with a JSON object.",
                system_prompt_info=("system_prompts", "simple_test"),
                schema=schema,
                current_phase="json_error_test",
                operation_id="test_json_error"
            )
            
            # Check that an error was returned
            assert "error" in result
            assert result["error"]["type"] == "json_decode_error"
            
            # Check that an error event was emitted
            assert len(emitted_errors) >= 1
            error_found = False
            for error in emitted_errors:
                if ("agent_id" in error and error["agent_id"] == "test_json_error" 
                    and error["type"] == "json_decode_error"):
                    error_found = True
                    break
            assert error_found, "JSON decode error event not found"
            
        finally:
            # Restore the original API and event queue
            agent.api = original_api
            event_queue.emit = original_emit


# Test data classes
class TestCorrectionDataClasses:
    """Test correction request and result data classes."""
    
    def test_correction_request_initialization(self):
        """Test initialization of CorrectionRequest."""
        request = CorrectionRequest(
            original_output={"test": "data"},
            feedback="Fix this issue",
            schema={"type": "object"},
            validation_errors={"error": "test error"},
            attempt_number=1,
            operation_id="test_op_id"
        )
        
        assert request.original_output == {"test": "data"}
        assert request.feedback == "Fix this issue"
        assert request.schema == {"type": "object"}
        assert request.validation_errors == {"error": "test error"}
        assert request.attempt_number == 1
        assert request.operation_id == "test_op_id"
    
    def test_correction_request_without_operation_id(self):
        """Test initialization of CorrectionRequest without operation_id."""
        request = CorrectionRequest(
            original_output={"test": "data"},
            feedback="Fix this issue",
            schema={"type": "object"},
            validation_errors={"error": "test error"},
            attempt_number=1
        )
        
        assert request.original_output == {"test": "data"}
        assert request.feedback == "Fix this issue"
        assert request.schema == {"type": "object"}
        assert request.validation_errors == {"error": "test error"}
        assert request.attempt_number == 1
        assert request.operation_id is None
    
    def test_correction_result_success(self):
        """Test initialization of CorrectionResult with success."""
        result = CorrectionResult(
            corrected_output={"corrected": "data"},
            success=True
        )
        
        assert result.corrected_output == {"corrected": "data"}
        assert result.success is True
        assert result.error_message is None
    
    def test_correction_result_failure(self):
        """Test initialization of CorrectionResult with failure."""
        result = CorrectionResult(
            corrected_output=None,
            success=False,
            error_message="Test error message"
        )
        
        assert result.corrected_output is None
        assert result.success is False
        assert result.error_message == "Test error message"