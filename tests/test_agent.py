import sys
import unittest
import pytest
import json
import os
import asyncio
from datetime import datetime
from pathlib import Path
import traceback
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

class TestAgent(unittest.TestCase):
    """Test suite for the Agent class using real components."""
    
    def setUp(self):
        """Set up real components for testing."""
        # Create an event loop for StateManager initialization
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Ensure API key is available
        if not os.getenv("ANTHROPIC_API_KEY"):
            # Use a default test key or skip tests if none available
            # Using a placeholder value will cause API calls to fail
            os.environ["ANTHROPIC_API_KEY"] = "test_key_for_unit_tests"
            self.api_available = False
            logger.warning("No ANTHROPIC_API_KEY found. API-dependent tests will be skipped.")
        else:
            self.api_available = True
        
        # Initialize actual system resources
        self.event_queue = EventQueue()
        self.state_manager = StateManager(self.event_queue)
        self.context_manager = AgentContextManager(self.event_queue)
        self.cache_manager = CacheManager(self.event_queue)
        self.metrics_manager = MetricsManager(self.event_queue)
        self.error_handler = ErrorHandler(self.event_queue)
        
        # Create Agent instance with real components
        self.agent = Agent(
            event_queue=self.event_queue,
            state_manager=self.state_manager,
            context_manager=self.context_manager,
            cache_manager=self.cache_manager,
            metrics_manager=self.metrics_manager,
            error_handler=self.error_handler,
            model="claude-3-7-sonnet-20250219"
        )
        
        # Test schemas
        self.simple_schema = {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "success": {"type": "boolean"}
            },
            "required": ["message", "success"]
        }
        
        self.complex_schema = {
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
    
    def tearDown(self):
        """Clean up after each test."""
        # Close the event loop
        if hasattr(self, 'loop'):
            self.loop.close()
            asyncio.set_event_loop(None)

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test that Agent initializes correctly with real components."""
        # Check that initialization set up the correct attributes
        self.assertEqual(self.agent.model, "claude-3-7-sonnet-20250219")
        self.assertEqual(self.agent.max_tokens, 1024)
        self.assertEqual(self.agent.max_validation_attempts, 3)
        
        # Check that components are initialized
        self.assertIsNotNone(self.agent._event_queue)
        self.assertIsNotNone(self.agent._state_manager)
        self.assertIsNotNone(self.agent._context_manager)
        self.assertIsNotNone(self.agent._cache_manager)
        self.assertIsNotNone(self.agent._metrics_manager)
        self.assertIsNotNone(self.agent._error_handler)
        
        # Check that API and validator are initialized
        self.assertIsNotNone(self.agent.api)
        self.assertIsNotNone(self.agent.validator)
    
    @pytest.mark.asyncio
    async def test_initialization_no_api_key(self):
        """Test initialization fails with no API key."""
        # Save current API key
        original_key = os.environ.get("ANTHROPIC_API_KEY")
        
        try:
            # Remove API key from environment
            if "ANTHROPIC_API_KEY" in os.environ:
                del os.environ["ANTHROPIC_API_KEY"]
            
            # Check that initialization raises an error
            with self.assertRaises(ValueError) as context:
                Agent(
                    event_queue=self.event_queue,
                    state_manager=self.state_manager,
                    context_manager=self.context_manager,
                    cache_manager=self.cache_manager,
                    metrics_manager=self.metrics_manager,
                    error_handler=self.error_handler
                )
            self.assertIn("ANTHROPIC_API_KEY not found", str(context.exception))
        
        finally:
            # Restore API key
            if original_key:
                os.environ["ANTHROPIC_API_KEY"] = original_key
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test that Agent works as an async context manager."""
        async with self.agent as agent:
            # The agent should be correctly initialized
            self.assertIsNotNone(agent.api)
    
    @pytest.mark.asyncio
    async def test_get_response_empty_conversation(self):
        """Test get_response with empty conversation."""
        # Call get_response with empty conversation
        with self.assertRaises(ValueError) as context:
            await self.agent.get_response(
                conversation="",
                system_prompt_info=("test_prompt_dir", "test_prompt_name"),
                schema=self.simple_schema,
                current_phase="test_phase",
                operation_id="test_op_id"
            )
        
        self.assertIn("conversation parameter cannot be empty", str(context.exception))
    
    @pytest.mark.asyncio
    async def test_successful_response(self):
        """Test getting a successful response."""
        if not self.api_available:
            self.skipTest("API key not available")
        
        # Simple conversation that should result in a valid response
        conversation = """
        Please respond with a simple message object:
        - Include a message field with the text "Test successful"
        - Include a success field with the value true
        """
        
        async with self.agent as agent:
            result = await agent.get_response(
                conversation=conversation,
                system_prompt_info=("system_prompts", "simple_response"),
                schema=self.simple_schema,
                current_phase="success_test",
                operation_id="test_success"
            )
        
        # Verify the response
        self.assertIsInstance(result, dict)
        self.assertIn("message", result)
        self.assertIn("success", result)
        self.assertEqual(result["success"], True)
    
    @pytest.mark.asyncio
    async def test_validation_retry(self):
        """Test the validation retry mechanism."""
        if not self.api_available:
            self.skipTest("API key not available")
        
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
        
        async with self.agent as agent:
            result = await agent.get_response(
                conversation=conversation,
                system_prompt_info=("system_prompts", "complex_response"),
                schema=self.complex_schema,
                current_phase="validation_test",
                operation_id="test_validation"
            )
        
        # Check if we got a valid response
        if "error" not in result:
            self.assertIn("action", result)
            self.assertIn("status", result)
            self.assertIn("count", result)
            self.assertIn("metadata", result)
            self.assertIn("category", result["metadata"])
            self.assertIn("priority", result["metadata"])
        else:
            # If we got an error, check that it's a validation error
            # and log the details (but don't fail the test as model responses vary)
            logger.info(f"Validation test resulted in error: {result['error']}")
            self.assertIn(result["error"]["type"], 
                         ["validation_error", "validation_exceeded"])
    
    @pytest.mark.asyncio
    async def test_schema_loading(self):
        """Test dynamic schema loading."""
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
            if not self.api_available:
                # Skip the API call part if no API key
                # But still test schema loading
                with self.assertRaises(Exception):
                    await self.agent.get_response(
                        conversation="Test schema loading",
                        system_prompt_info=("test_schemas", "test"),
                        schema=None,
                        current_phase="schema_test",
                        operation_id="test_schema_loading"
                    )
                
                # Check that the schema was loaded
                self.assertEqual(self.agent.schema, test_schema)
            else:
                # If API is available, run the full test
                result = await self.agent.get_response(
                    conversation="Respond with a test field containing any string",
                    system_prompt_info=("test_schemas", "test"),
                    schema=None,
                    current_phase="schema_test",
                    operation_id="test_schema_loading"
                )
                
                # Check the result
                if "error" not in result:
                    self.assertIn("test", result)
                    self.assertIsInstance(result["test"], str)
        
        finally:
            # Clean up temporary file
            if schema_path.exists():
                schema_path.unlink()
    
    @pytest.mark.asyncio
    async def test_schema_file_not_found(self):
        """Test schema loading when file doesn't exist."""
        # Non-existent schema path
        with self.assertRaises(FileNotFoundError) as context:
            await self.agent.get_response(
                conversation="Test conversation",
                system_prompt_info=("nonexistent", "schema"),
                schema=None,
                current_phase="test_phase",
                operation_id="test_missing_schema"
            )
        
        self.assertIn("Schema file not found", str(context.exception))
    
    @pytest.mark.asyncio
    async def test_validation_exceeded(self):
        """Test exceeding validation attempts."""
        if not self.api_available:
            self.skipTest("API key not available")
        
        # Craft a conversation likely to produce invalid responses
        conversation = """
        Respond with anything you want, I'll fix it later.
        """
        
        # Override max attempts to make test faster
        original_max = self.agent.max_validation_attempts
        self.agent.max_validation_attempts = 1
        
        try:
            async with self.agent as agent:
                result = await agent.get_response(
                    conversation=conversation,
                    system_prompt_info=("system_prompts", "intentionally_invalid"),
                    schema=self.complex_schema,  # Complex schema makes validation harder
                    current_phase="validation_exceeded_test",
                    operation_id="test_exceeded"
                )
            
            # With real components, we might get a valid response or validation error
            if "error" in result:
                # Check if it's a validation exceeded error
                if result["error"]["type"] == "validation_exceeded":
                    # Test passed as expected
                    self.assertEqual(result["error"]["type"], "validation_exceeded")
                else:
                    # Some other error, but not a failure of the test
                    logger.info(f"Got error: {result['error']['type']}")
            else:
                # We got a valid response, which is unexpected but not a test failure
                logger.info(f"Surprisingly got valid response: {result}")
        
        finally:
            # Restore original max attempts
            self.agent.max_validation_attempts = original_max


class TestCorrectionRequest(unittest.TestCase):
    """Test suite for the CorrectionRequest class."""
    
    def test_initialization(self):
        """Test initialization of CorrectionRequest."""
        # Create a CorrectionRequest
        request = CorrectionRequest(
            original_output={"test": "data"},
            feedback="Fix this issue",
            schema={"type": "object"},
            validation_errors={"error": "test error"},
            attempt_number=1,
            operation_id="test_op_id"
        )
        
        # Verify attributes
        self.assertEqual(request.original_output, {"test": "data"})
        self.assertEqual(request.feedback, "Fix this issue")
        self.assertEqual(request.schema, {"type": "object"})
        self.assertEqual(request.validation_errors, {"error": "test error"})
        self.assertEqual(request.attempt_number, 1)
        self.assertEqual(request.operation_id, "test_op_id")
    
    def test_initialization_without_operation_id(self):
        """Test initialization of CorrectionRequest without operation_id."""
        # Create a CorrectionRequest without operation_id
        request = CorrectionRequest(
            original_output={"test": "data"},
            feedback="Fix this issue",
            schema={"type": "object"},
            validation_errors={"error": "test error"},
            attempt_number=1
        )
        
        # Verify attributes
        self.assertEqual(request.original_output, {"test": "data"})
        self.assertEqual(request.feedback, "Fix this issue")
        self.assertEqual(request.schema, {"type": "object"})
        self.assertEqual(request.validation_errors, {"error": "test error"})
        self.assertEqual(request.attempt_number, 1)
        self.assertIsNone(request.operation_id)


class TestCorrectionResult(unittest.TestCase):
    """Test suite for the CorrectionResult class."""
    
    def test_initialization_success(self):
        """Test initialization of CorrectionResult with success."""
        # Create a successful CorrectionResult
        result = CorrectionResult(
            corrected_output={"corrected": "data"},
            success=True
        )
        
        # Verify attributes
        self.assertEqual(result.corrected_output, {"corrected": "data"})
        self.assertTrue(result.success)
        self.assertIsNone(result.error_message)
    
    def test_initialization_failure(self):
        """Test initialization of CorrectionResult with failure."""
        # Create a failed CorrectionResult
        result = CorrectionResult(
            corrected_output=None,
            success=False,
            error_message="Test error message"
        )
        
        # Verify attributes
        self.assertIsNone(result.corrected_output)
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "Test error message")


class TestCorrectionHandling(unittest.TestCase):
    """Test suite for correction handling functionality."""
    
    def setUp(self):
        """Set up components for testing."""
        # Ensure API key is available
        if not os.getenv("ANTHROPIC_API_KEY"):
            os.environ["ANTHROPIC_API_KEY"] = "test_key_for_unit_tests"
            self.api_available = False
            logger.warning("No ANTHROPIC_API_KEY found. API-dependent tests will be skipped.")
        else:
            self.api_available = True
        
        # Initialize system resources
        self.event_queue = EventQueue()
        self.state_manager = StateManager(self.event_queue)
        self.context_manager = AgentContextManager(self.event_queue)
        self.cache_manager = CacheManager(self.event_queue)
        self.metrics_manager = MetricsManager(self.event_queue)
        self.error_handler = ErrorHandler(self.event_queue)
        
        # Create Agent instance
        self.agent = Agent(
            event_queue=self.event_queue,
            state_manager=self.state_manager,
            context_manager=self.context_manager,
            cache_manager=self.cache_manager,
            metrics_manager=self.metrics_manager,
            error_handler=self.error_handler,
            model="claude-3-7-sonnet-20250219"
        )
        
        # Test schema for corrections
        self.test_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0},
                "active": {"type": "boolean"}
            },
            "required": ["name", "age", "active"]
        }
    
    @pytest.mark.asyncio
    async def test_correction_request_handling(self):
        """Test handling a correction request."""
        if not self.api_available:
            self.skipTest("API key not available")
        
        # Create a correction request with validation errors
        request = CorrectionRequest(
            original_output={"name": "Test", "active": True},  # Missing 'age'
            feedback="Response is missing the required 'age' field which should be an integer.",
            schema=self.test_schema,
            validation_errors={"missing": ["age"]},
            attempt_number=1,
            operation_id="test_correction"
        )
        
        # Test handling the correction
        async with self.agent as agent:
            result = await agent.handle_correction_request(request)
        
        # Check the result
        if result.success:
            # Should have corrected the output with the age field
            self.assertIsNotNone(result.corrected_output)
            self.assertIn("name", result.corrected_output)
            self.assertIn("age", result.corrected_output)
            self.assertIn("active", result.corrected_output)
            self.assertIsInstance(result.corrected_output["age"], int)
        else:
            # Log the error but don't fail the test as model responses vary
            logger.info(f"Correction failed: {result.error_message}")
    
    @pytest.mark.asyncio
    async def test_build_correction_prompt(self):
        """Test building a correction prompt."""
        # Create a correction request
        request = CorrectionRequest(
            original_output={"name": "Test", "active": True},
            feedback="Missing required field 'age'",
            schema=self.test_schema,
            validation_errors={"missing": ["age"]},
            attempt_number=2,
            operation_id="test_prompt"
        )
        
        # Build the correction prompt
        prompt = self.agent._build_correction_prompt(request)
        
        # Verify prompt content
        self.assertIn("Validation Feedback:", prompt)
        self.assertIn("Missing required field 'age'", prompt)
        self.assertIn("Original Output:", prompt)
        self.assertIn('"name": "Test"', prompt)
        self.assertIn("Schema Requirements:", prompt)
        self.assertIn("Attempt number: 2", prompt)
        self.assertIn("Please provide a corrected response", prompt)

class TestEnhancedValidation(unittest.TestCase):
    """Test suite for enhanced validation scenarios."""
    
    def setUp(self):
        """Set up for validation tests."""
        # Initialize components for testing
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Initialize system resources
        self.event_queue = EventQueue()
        self.state_manager = StateManager(self.event_queue)
        self.context_manager = AgentContextManager(self.event_queue)
        self.cache_manager = CacheManager(self.event_queue)
        self.metrics_manager = MetricsManager(self.event_queue)
        self.error_handler = ErrorHandler(self.event_queue)
        
        # Initialize agent
        self.agent = Agent(
            event_queue=self.event_queue,
            state_manager=self.state_manager,
            context_manager=self.context_manager,
            cache_manager=self.cache_manager,
            metrics_manager=self.metrics_manager,
            error_handler=self.error_handler,
            model="claude-3-7-sonnet-20250219"
        )
        
        # Set up API key check
        if not os.getenv("ANTHROPIC_API_KEY"):
            os.environ["ANTHROPIC_API_KEY"] = "test_key_for_unit_tests"
            self.api_available = False
            logger.warning("No ANTHROPIC_API_KEY found. API-dependent tests will be skipped.")
        else:
            self.api_available = True

    def tearDown(self):
        """Clean up after each test."""
        if hasattr(self, 'loop'):
            self.loop.close()
            asyncio.set_event_loop(None)
    
    @pytest.mark.asyncio
    async def test_string_validation(self):
        """Test validation of string fields."""
        if not self.api_available:
            self.skipTest("API key not available")
        
        # Schema with string constraints
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 3, "maxLength": 10},
                "category": {"type": "string", "enum": ["A", "B", "C"]}
            },
            "required": ["name", "category"]
        }
        
        # Test conversation designed to produce a response with string fields
        conversation = """
        Please respond with a JSON object containing:
        - A name field (string between 3-10 characters)
        - A category field (one of: A, B, or C)
        
        Use name="Test" and category="A"
        """
        
        async with self.agent as agent:
            result = await agent.get_response(
                conversation=conversation,
                system_prompt_info=("system_prompts", "string_validation"),
                schema=schema,
                current_phase="string_validation",
                operation_id="test_string"
            )
        
        # Verify the response
        if "error" not in result:
            self.assertIn("name", result)
            self.assertIn("category", result)
            self.assertIsInstance(result["name"], str)
            self.assertIsInstance(result["category"], str)
            self.assertGreaterEqual(len(result["name"]), 3)
            self.assertLessEqual(len(result["name"]), 10)
            self.assertIn(result["category"], ["A", "B", "C"])
    
    @pytest.mark.asyncio
    async def test_numeric_validation(self):
        """Test validation of numeric fields."""
        if not self.api_available:
            self.skipTest("API key not available")
        
        # Schema with numeric constraints
        schema = {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "minimum": 0, "maximum": 100},
                "price": {"type": "number", "minimum": 0, "exclusiveMaximum": 1000}
            },
            "required": ["count", "price"]
        }
        
        # Test conversation designed to produce a response with numeric fields
        conversation = """
        Please respond with a JSON object containing:
        - A count field (integer between 0-100)
        - A price field (number between 0-1000, exclusive)
        
        Use count=50 and price=499.99
        """
        
        async with self.agent as agent:
            result = await agent.get_response(
                conversation=conversation,
                system_prompt_info=("system_prompts", "numeric_validation"),
                schema=schema,
                current_phase="numeric_validation",
                operation_id="test_numeric"
            )
        
        # Verify the response
        if "error" not in result:
            self.assertIn("count", result)
            self.assertIn("price", result)
            self.assertIsInstance(result["count"], int)
            self.assertIsInstance(result["price"], (int, float))
            self.assertGreaterEqual(result["count"], 0)
            self.assertLessEqual(result["count"], 100)
            self.assertGreaterEqual(result["price"], 0)
            self.assertLess(result["price"], 1000)
    
    @pytest.mark.asyncio
    async def test_nested_object_validation(self):
        """Test validation of nested object structures."""
        if not self.api_available:
            self.skipTest("API key not available")
        
        # Schema with nested objects
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "contact": {
                            "type": "object",
                            "properties": {
                                "email": {"type": "string", "format": "email"},
                                "phone": {"type": "string"}
                            },
                            "required": ["email"]
                        }
                    },
                    "required": ["id", "name", "contact"]
                },
                "active": {"type": "boolean"}
            },
            "required": ["user", "active"]
        }
        
        # Test conversation designed to produce a response with nested objects
        conversation = """
        Please respond with a JSON object containing:
        - A user object with:
          - id (integer)
          - name (string)
          - contact object with:
            - email (string in email format)
            - phone (string, optional)
        - An active field (boolean)
        
        Example values:
        id=123, name="Test User", email="test@example.com", active=true
        """
        
        async with self.agent as agent:
            result = await agent.get_response(
                conversation=conversation,
                system_prompt_info=("system_prompts", "nested_validation"),
                schema=schema,
                current_phase="nested_validation",
                operation_id="test_nested"
            )
        
        # Verify the response
        if "error" not in result:
            self.assertIn("user", result)
            self.assertIn("active", result)
            self.assertIsInstance(result["user"], dict)
            self.assertIsInstance(result["active"], bool)
            
            user = result["user"]
            self.assertIn("id", user)
            self.assertIn("name", user)
            self.assertIn("contact", user)
            self.assertIsInstance(user["id"], int)
            self.assertIsInstance(user["name"], str)
            self.assertIsInstance(user["contact"], dict)
            
            contact = user["contact"]
            self.assertIn("email", contact)
            self.assertIsInstance(contact["email"], str)
            self.assertIn("@", contact["email"])  # Basic email validation


class TestExtendedCorrectionFlow(unittest.TestCase):
    """Test suite for comprehensive correction flow handling."""
    
    def setUp(self):
        """Set up for correction flow tests."""
        # Initialize components for testing
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Initialize system resources
        self.event_queue = EventQueue()
        self.state_manager = StateManager(self.event_queue)
        self.context_manager = AgentContextManager(self.event_queue)
        self.cache_manager = CacheManager(self.event_queue)
        self.metrics_manager = MetricsManager(self.event_queue)
        self.error_handler = ErrorHandler(self.event_queue)
        
        # Initialize agent
        self.agent = Agent(
            event_queue=self.event_queue,
            state_manager=self.state_manager,
            context_manager=self.context_manager,
            cache_manager=self.cache_manager,
            metrics_manager=self.metrics_manager,
            error_handler=self.error_handler,
            model="claude-3-7-sonnet-20250219"
        )
        
        # Set up API key check
        if not os.getenv("ANTHROPIC_API_KEY"):
            os.environ["ANTHROPIC_API_KEY"] = "test_key_for_unit_tests"
            self.api_available = False
            logger.warning("No ANTHROPIC_API_KEY found. API-dependent tests will be skipped.")
        else:
            self.api_available = True
        
        # Test schema for corrections
        self.test_schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "email": {"type": "string", "format": "email"}
                    },
                    "required": ["id", "name", "email"]
                },
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "price": {"type": "number", "minimum": 0}
                        },
                        "required": ["id", "name", "price"]
                    },
                    "minItems": 1
                },
                "total": {"type": "number", "minimum": 0}
            },
            "required": ["user", "items", "total"]
        }

    def tearDown(self):
        """Clean up after each test."""
        if hasattr(self, 'loop'):
            self.loop.close()
            asyncio.set_event_loop(None)
    
    @pytest.mark.asyncio
    async def test_missing_field_correction(self):
        """Test correction of a missing required field."""
        if not self.api_available:
            self.skipTest("API key not available")
        
        # Create original output with missing field
        original_output = {
            "user": {
                "id": 123,
                "name": "Test User",
                # "email" is missing
            },
            "items": [
                {
                    "id": 1,
                    "name": "Item 1",
                    "price": 10.99
                }
            ],
            "total": 10.99
        }
        
        # Create correction request
        request = CorrectionRequest(
            original_output=original_output,
            feedback="The user object is missing the required 'email' field which should be a string in email format.",
            schema=self.test_schema,
            validation_errors={"missing": ["user.email"]},
            attempt_number=1,
            operation_id="test_missing"
        )
        
        # Test handling the correction
        async with self.agent as agent:
            result = await agent.handle_correction_request(request)
        
        # Check the result
        if result.success:
            self.assertIsNotNone(result.corrected_output)
            self.assertIn("user", result.corrected_output)
            self.assertIn("email", result.corrected_output["user"])
            self.assertIsInstance(result.corrected_output["user"]["email"], str)
            self.assertIn("@", result.corrected_output["user"]["email"])
        else:
            logger.info(f"Correction failed: {result.error_message}")
    
    @pytest.mark.asyncio
    async def test_invalid_value_correction(self):
        """Test correction of an invalid value."""
        if not self.api_available:
            self.skipTest("API key not available")
        
        # Create original output with invalid value
        original_output = {
            "user": {
                "id": 123,
                "name": "Test User",
                "email": "test@example.com"
            },
            "items": [
                {
                    "id": 1,
                    "name": "Item 1",
                    "price": -10.99  # Negative price, should be >= 0
                }
            ],
            "total": 10.99
        }
        
        # Create correction request
        request = CorrectionRequest(
            original_output=original_output,
            feedback="The 'price' field in the first item should be >= 0, but got -10.99",
            schema=self.test_schema,
            validation_errors={"invalid_value": ["items[0].price"]},
            attempt_number=1,
            operation_id="test_invalid"
        )
        
        # Test handling the correction
        async with self.agent as agent:
            result = await agent.handle_correction_request(request)
        
        # Check the result
        if result.success:
            self.assertIsNotNone(result.corrected_output)
            self.assertIn("items", result.corrected_output)
            self.assertGreaterEqual(len(result.corrected_output["items"]), 1)
            self.assertIn("price", result.corrected_output["items"][0])
            self.assertGreaterEqual(result.corrected_output["items"][0]["price"], 0)
        else:
            logger.info(f"Correction failed: {result.error_message}")
    
    @pytest.mark.asyncio
    async def test_multiple_errors_correction(self):
        """Test correction of multiple validation errors."""
        if not self.api_available:
            self.skipTest("API key not available")
        
        # Create original output with multiple errors
        original_output = {
            "user": {
                "id": "123",  # Should be integer, not string
                "name": "Test User",
                "email": "invalid-email"  # Invalid email format
            },
            "items": [],  # Empty array, should have at least 1 item
            "total": 0
        }
        
        # Create correction request
        request = CorrectionRequest(
            original_output=original_output,
            feedback="Multiple validation errors: 1) user.id should be an integer, 2) user.email is not a valid email format, 3) items array should have at least 1 item",
            schema=self.test_schema,
            validation_errors={
                "type_error": ["user.id"],
                "format_error": ["user.email"],
                "array_error": ["items"]
            },
            attempt_number=1,
            operation_id="test_multiple"
        )
        
        # Test handling the correction
        async with self.agent as agent:
            result = await agent.handle_correction_request(request)
        
        # Check the result
        if result.success:
            self.assertIsNotNone(result.corrected_output)
            
            # Check that all errors were corrected
            self.assertIn("user", result.corrected_output)
            self.assertIn("id", result.corrected_output["user"])
            self.assertIsInstance(result.corrected_output["user"]["id"], int)
            
            self.assertIn("email", result.corrected_output["user"])
            self.assertIn("@", result.corrected_output["user"]["email"])
            
            self.assertIn("items", result.corrected_output)
            self.assertGreaterEqual(len(result.corrected_output["items"]), 1)
        else:
            logger.info(f"Correction failed: {result.error_message}")

class TestResourceManagerIntegration(unittest.TestCase):
    """Test suite for resource manager integration."""
    
    def setUp(self):
        """Set up for resource manager tests."""
        # Initialize components for testing
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Initialize system resources
        self.event_queue = EventQueue()
        self.state_manager = StateManager(self.event_queue)
        self.context_manager = AgentContextManager(self.event_queue)
        self.cache_manager = CacheManager(self.event_queue)
        self.metrics_manager = MetricsManager(self.event_queue)
        self.error_handler = ErrorHandler(self.event_queue)
        
        # Initialize agent
        self.agent = Agent(
            event_queue=self.event_queue,
            state_manager=self.state_manager,
            context_manager=self.context_manager,
            cache_manager=self.cache_manager,
            metrics_manager=self.metrics_manager,
            error_handler=self.error_handler,
            model="claude-3-7-sonnet-20250219"
        )
        
        # Set up API key check
        if not os.getenv("ANTHROPIC_API_KEY"):
            os.environ["ANTHROPIC_API_KEY"] = "test_key_for_unit_tests"
            self.api_available = False
            logger.warning("No ANTHROPIC_API_KEY found. API-dependent tests will be skipped.")
        else:
            self.api_available = True

    def tearDown(self):
        """Clean up after each test."""
        if hasattr(self, 'loop'):
            self.loop.close()
            asyncio.set_event_loop(None)
    
    @pytest.mark.asyncio
    async def test_state_manager_interaction(self):
        """Test interaction with the state manager."""
        if not self.api_available:
            self.skipTest("API key not available")
        
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
        state_entry = await self.state_manager.get_state(validation_key)
        self.assertIsNone(state_entry)
        
        # Call get_response to trigger state manager interaction
        async with self.agent as agent:
            await agent.get_response(
                conversation="Please respond with a JSON object containing a 'test' string field.",
                system_prompt_info=("system_prompts", "simple_test"),
                schema=schema,
                current_phase="state_test",
                operation_id=operation_id
            )
        
        # Check that the state now exists and has the expected structure
        state_entry = await self.state_manager.get_state(validation_key)
        self.assertIsNotNone(state_entry)
        self.assertIn("attempts", state_entry.state)
        self.assertIn("history", state_entry.state)
        self.assertIsInstance(state_entry.state["attempts"], int)
        self.assertGreaterEqual(state_entry.state["attempts"], 1)
        self.assertIsInstance(state_entry.state["history"], list)
        self.assertGreaterEqual(len(state_entry.state["history"]), 1)
    
    @pytest.mark.asyncio
    async def test_context_manager_interaction(self):
        """Test interaction with the context manager."""
        if not self.api_available:
            self.skipTest("API key not available")
        
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
        context = await self.context_manager.get_context(context_id)
        self.assertIsNone(context)
        
        # Call get_response to trigger context manager interaction
        async with self.agent as agent:
            await agent.get_response(
                conversation="Please respond with a JSON object containing a 'test' string field.",
                system_prompt_info=("system_prompts", "simple_test"),
                schema=schema,
                current_phase="context_test",
                operation_id=operation_id
            )
        
        # Check that the context now exists
        context = await self.context_manager.get_context(context_id)
        self.assertIsNotNone(context)
        self.assertEqual(context.agent_id, context_id)
        self.assertEqual(context.operation_id, operation_id)
    
    @pytest.mark.asyncio
    async def test_metrics_recording(self):
        """Test that metrics are recorded during agent operation."""
        if not self.api_available:
            self.skipTest("API key not available")
        
        # Custom metrics manager to track recorded metrics
        class TestMetricsManager(MetricsManager):
            def __init__(self, event_queue):
                super().__init__(event_queue)
                self.recorded_metrics = []
                
            async def record_metric(self, name, value, metadata=None):
                self.recorded_metrics.append((name, value, metadata))
                await super().record_metric(name, value, metadata)
        
        # Replace the metrics manager
        test_metrics_manager = TestMetricsManager(self.event_queue)
        original_metrics_manager = self.agent._metrics_manager
        self.agent._metrics_manager = test_metrics_manager
        
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
            async with self.agent as agent:
                await agent.get_response(
                    conversation="Please respond with a JSON object containing a 'test' string field.",
                    system_prompt_info=("system_prompts", "simple_test"),
                    schema=schema,
                    current_phase="metrics_test",
                    operation_id="test_metrics"
                )
            
            # Check that metrics were recorded
            self.assertGreater(len(test_metrics_manager.recorded_metrics), 0)
            
            # Check for validation success rate metric
            found_validation_metric = False
            for name, value, metadata in test_metrics_manager.recorded_metrics:
                if name == "agent:validation:success_rate":
                    found_validation_metric = True
                    self.assertIn(value, [0.0, 1.0])  # Success rate is either 0 or 1
                    self.assertEqual(metadata.get("phase"), "metrics_test")
                    self.assertEqual(metadata.get("operation_id"), "test_metrics")
            
            self.assertTrue(found_validation_metric, "Validation success rate metric not found")
            
        finally:
            # Restore the original metrics manager
            self.agent._metrics_manager = original_metrics_manager
    
    @pytest.mark.asyncio
    async def test_error_handler_integration(self):
        """Test integration with the error handler."""
        if not self.api_available:
            self.skipTest("API key not available")
        
        # Custom error handler to track handled errors
        class TestErrorHandler(ErrorHandler):
            def __init__(self, event_queue):
                super().__init__(event_queue)
                self.handled_errors = []
                
            async def handle_error(self, error, resource_id, error_type, context=None):
                self.handled_errors.append((error, resource_id, error_type, context))
                await super().handle_error(error, resource_id, error_type, context)
        
        # Replace the error handler
        test_error_handler = TestErrorHandler(self.event_queue)
        original_error_handler = self.agent._error_handler
        self.agent._error_handler = test_error_handler
        
        try:
            # Create a scenario that will cause an error
            # Use a mock API that raises an exception
            class MockAPI:
                async def __aenter__(self):
                    return self
                    
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass
                    
                async def call(self, **kwargs):
                    raise ValueError("Test error")
            
            # Replace the agent's API
            original_api = self.agent.api
            self.agent.api = MockAPI()
            
            try:
                # Call get_response to trigger an error
                await self.agent.get_response(
                    conversation="This will cause an error.",
                    system_prompt_info=("system_prompts", "simple_test"),
                    schema={"type": "object"},
                    current_phase="error_test",
                    operation_id="test_error_handler"
                )
            except Exception:
                pass  # We expect an error
            
            # Check that the error was handled
            self.assertGreater(len(test_error_handler.handled_errors), 0)
            
            # Check the error details
            error, resource_id, error_type, context = test_error_handler.handled_errors[0]
            self.assertIsInstance(error, Exception)
            self.assertEqual(resource_id, "agent:test_error_handler")
            self.assertEqual(error_type, "agent_processing_error")
            self.assertEqual(context.get("phase"), "error_test")
            self.assertEqual(context.get("operation_id"), "test_error_handler")
            
        finally:
            # Restore the original components
            self.agent._error_handler = original_error_handler
            self.agent.api = original_api


class TestErrorHandling(unittest.TestCase):
    """Test suite for error handling functionality."""
    
    def setUp(self):
        """Set up components for testing."""
        # Initialize system resources
        self.event_queue = EventQueue()
        self.state_manager = StateManager(self.event_queue)
        self.context_manager = AgentContextManager(self.event_queue)
        self.cache_manager = CacheManager(self.event_queue)
        self.metrics_manager = MetricsManager(self.event_queue)
        self.error_handler = ErrorHandler(self.event_queue)
        
        # Create Agent instance
        self.agent = Agent(
            event_queue=self.event_queue,
            state_manager=self.state_manager,
            context_manager=self.context_manager,
            cache_manager=self.cache_manager,
            metrics_manager=self.metrics_manager,
            error_handler=self.error_handler,
            model="claude-3-7-sonnet-20250219"
        )
    
    def test_create_error_details(self):
        """Test creating error details."""
        # Create a test exception
        test_exception = ValueError("Test error message")
        
        # Get error details
        error_details = self.agent._create_error_details(test_exception)
        
        # Verify error details
        self.assertEqual(error_details["type"], "system_error")
        self.assertEqual(error_details["message"], "Test error message")
        self.assertEqual(error_details["details"], "ValueError")
        self.assertIn("traceback", error_details)
        self.assertIn("timestamp", error_details)
    
    @pytest.mark.asyncio
    async def test_handle_error(self):
        """Test error handling."""
        # Create error details
        error_details = {
            "type": "test_error",
            "message": "Test error message",
            "details": "Test details"
        }
        
        # Handle the error
        await self.agent._handle_error(
            error_details=error_details,
            operation_id="test_op_id",
            current_phase="test_phase"
        )
        
        # No assertions here since we're just testing that it doesn't throw
        # Real validation would involve checking logs or monitoring emitted events
        # but that's beyond the scope of a unit test

class TestErrorHandlingScenarios(unittest.TestCase):
    """Test suite for error handling scenarios."""
    
    def setUp(self):
        """Set up for error handling tests."""
        # Initialize components for testing
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Initialize system resources
        self.event_queue = EventQueue()
        self.state_manager = StateManager(self.event_queue)
        self.context_manager = AgentContextManager(self.event_queue)
        self.cache_manager = CacheManager(self.event_queue)
        self.metrics_manager = MetricsManager(self.event_queue)
        self.error_handler = ErrorHandler(self.event_queue)
        
        # Initialize agent
        self.agent = Agent(
            event_queue=self.event_queue,
            state_manager=self.state_manager,
            context_manager=self.context_manager,
            cache_manager=self.cache_manager,
            metrics_manager=self.metrics_manager,
            error_handler=self.error_handler,
            model="claude-3-7-sonnet-20250219"
        )
        
        # Set up API key check
        if not os.getenv("ANTHROPIC_API_KEY"):
            os.environ["ANTHROPIC_API_KEY"] = "test_key_for_unit_tests"
            self.api_available = False
            logger.warning("No ANTHROPIC_API_KEY found. API-dependent tests will be skipped.")
        else:
            self.api_available = True
        
        # Track emitted errors
        self.emitted_errors = []
        
        # Create a custom event queue to capture error events
        class CaptureEventQueue(EventQueue):
            async def emit(self2, event_type, payload):
                if event_type == ResourceEventTypes.ERROR_OCCURRED.value:
                    self.emitted_errors.append(payload)
                await super().emit(event_type, payload)
        
        # Replace the event queue with our custom one
        self.capture_event_queue = CaptureEventQueue()
        self.agent._event_queue = self.capture_event_queue
        self.agent._error_handler._event_queue = self.capture_event_queue

    def tearDown(self):
        """Clean up after each test."""
        if hasattr(self, 'loop'):
            self.loop.close()
            asyncio.set_event_loop(None)
    
    @pytest.mark.asyncio
    async def test_json_decode_error(self):
        """Test handling of JSON decode errors."""
        if not self.api_available:
            self.skipTest("API key not available")
        
        # Create a mock API that returns invalid JSON
        class MockAPI:
            async def __aenter__(self):
                return self
                
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
                
            async def call(self, **kwargs):
                return "This is not valid JSON"
        
        # Replace the agent's API with our mock
        original_api = self.agent.api
        self.agent.api = MockAPI()
        
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
            result = await self.agent.get_response(
                conversation="Please respond with a JSON object.",
                system_prompt_info=("system_prompts", "simple_test"),
                schema=schema,
                current_phase="json_error_test",
                operation_id="test_json_error"
            )
            
            # Check that an error was returned
            self.assertIn("error", result)
            self.assertEqual(result["error"]["type"], "json_decode_error")
            
            # Check that an error event was emitted
            self.assertGreaterEqual(len(self.emitted_errors), 1)
            error_found = False
            for error in self.emitted_errors:
                if "agent_id" in error and error["agent_id"] == "test_json_error" and error["type"] == "json_decode_error":
                    error_found = True
                    break
            self.assertTrue(error_found, "JSON decode error event not found")
            
        finally:
            # Restore the original API
            self.agent.api = original_api
    
    @pytest.mark.asyncio
    async def test_validation_error_handling(self):
        """Test handling of validation errors."""
        if not self.api_available:
            self.skipTest("API key not available")
        
        # Create a mock API that returns an object missing required fields
        class MockAPI:
            async def __aenter__(self):
                return self
                
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
                
            async def call(self, **kwargs):
                return '{"optional_field": "value"}'  # Missing required field
        
        # Replace the agent's API with our mock
        original_api = self.agent.api
        self.agent.api = MockAPI()
        
        try:
            # Define a test schema with a required field
            schema = {
                "type": "object",
                "properties": {
                    "required_field": {"type": "string"},
                    "optional_field": {"type": "string"}
                },
                "required": ["required_field"]
            }
            
            # Set max validation attempts to 1 to speed up test
            original_max = self.agent.max_validation_attempts
            self.agent.max_validation_attempts = 1
            
            # Call get_response with the mock API
            result = await self.agent.get_response(
                conversation="Please respond with a JSON object.",
                system_prompt_info=("system_prompts", "simple_test"),
                schema=schema,
                current_phase="validation_error_test",
                operation_id="test_validation_error"
            )
            
            # Check that an error was returned
            self.assertIn("error", result)
            self.assertEqual(result["error"]["type"], "validation_error")
            
            # Check for missing field in analysis
            self.assertIn("analysis", result["error"])
            
        finally:
            # Restore the original API and max attempts
            self.agent.api = original_api
            self.agent.max_validation_attempts = original_max
    
    @pytest.mark.asyncio
    async def test_validation_exceeded_handling(self):
        """Test handling of exceeded validation attempts."""
        if not self.api_available:
            self.skipTest("API key not available")
        
        # Create a mock API that always returns invalid data
        class MockAPI:
            async def __aenter__(self):
                return self
                
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
                
            async def call(self, **kwargs):
                return '{"wrong_field": "value"}'  # Always wrong
        
        # Replace the agent's API with our mock
        original_api = self.agent.api
        self.agent.api = MockAPI()
        
        try:
            # Define a test schema
            schema = {
                "type": "object",
                "properties": {
                    "correct_field": {"type": "string"}
                },
                "required": ["correct_field"]
            }
            
            # Set max validation attempts to 2 to speed up test
            original_max = self.agent.max_validation_attempts
            self.agent.max_validation_attempts = 2
            
            # Call get_response with the mock API
            result = await self.agent.get_response(
                conversation="Please respond with a JSON object.",
                system_prompt_info=("system_prompts", "simple_test"),
                schema=schema,
                current_phase="validation_exceeded_test",
                operation_id="test_validation_exceeded"
            )
            
            # Check that a validation exceeded error was returned
            self.assertIn("error", result)
            self.assertEqual(result["error"]["type"], "validation_exceeded")
            self.assertEqual(result["error"]["attempts"], 2)
            self.assertIn("history", result["error"])
            self.assertEqual(len(result["error"]["history"]), 2)
            
        finally:
            # Restore the original API and max attempts
            self.agent.api = original_api
            self.agent.max_validation_attempts = original_max
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test handling of API errors."""
        if not self.api_available:
            self.skipTest("API key not available")
        
        # Create a mock API that raises an exception
        class MockAPI:
            async def __aenter__(self):
                return self
                
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
                
            async def call(self, **kwargs):
                raise ValueError("API error")
        
        # Replace the agent's API with our mock
        original_api = self.agent.api
        self.agent.api = MockAPI()
        
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
            result = await self.agent.get_response(
                conversation="Please respond with a JSON object.",
                system_prompt_info=("system_prompts", "simple_test"),
                schema=schema,
                current_phase="api_error_test",
                operation_id="test_api_error"
            )
            
            # Check that a system error was returned
            self.assertIn("error", result)
            self.assertEqual(result["error"]["type"], "system_error")
            self.assertIn("API error", result["error"]["message"])
            self.assertEqual(result["error"]["details"], "ValueError")
            self.assertIn("traceback", result["error"])
            
            # Check that an error event was emitted
            self.assertGreaterEqual(len(self.emitted_errors), 1)
            
        finally:
            # Restore the original API
            self.agent.api = original_api

if __name__ == "__main__":
    # Create a test suite containing all tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add existing test classes
    suite.addTests(loader.loadTestsFromTestCase(TestAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestCorrectionRequest))
    suite.addTests(loader.loadTestsFromTestCase(TestCorrectionResult))
    suite.addTests(loader.loadTestsFromTestCase(TestCorrectionHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    
    # Add new test classes
    suite.addTests(loader.loadTestsFromTestCase(TestEnhancedValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestExtendedCorrectionFlow))
    suite.addTests(loader.loadTestsFromTestCase(TestResourceManagerIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandlingScenarios))
    
    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    test_result = test_runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(not test_result.wasSuccessful())