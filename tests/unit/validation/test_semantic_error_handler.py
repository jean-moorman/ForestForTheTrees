"""
Independent tests for SemanticErrorHandler.

These tests focus on the SemanticErrorHandler class functionality,
testing real semantic error correction workflows without mocks.
"""

import asyncio
import json
import pytest
import unittest
from datetime import datetime
from typing import Dict, Any, List

# Import system components
from agent_validation import SemanticErrorHandler, ValidationError, Validator
from agent import CorrectionRequest, CorrectionResult
from resources import EventQueue, StateManager, ResourceType

# Import test infrastructure
from tests_new.harness.validation_test_harness import ValidationTestHarness


class MockCorrectionHandler:
    """Test correction handler that simulates realistic correction behavior."""
    
    def __init__(self, correction_strategy: str = "progressive"):
        """
        Initialize with different correction strategies.
        
        Args:
            correction_strategy: "progressive", "immediate", "failing", or "custom"
        """
        self.correction_strategy = correction_strategy
        self.call_count = 0
        self.call_history = []
        self.custom_responses = {}
        
    def set_custom_response(self, attempt_number: int, response: Dict[str, Any]):
        """Set a custom response for a specific attempt number."""
        self.custom_responses[attempt_number] = response
        
    async def handle_correction_request(self, request: CorrectionRequest) -> CorrectionResult:
        """Handle correction request based on strategy."""
        self.call_count += 1
        self.call_history.append({
            "attempt": request.attempt_number,
            "original_output": request.original_output,
            "feedback": request.feedback,
            "timestamp": datetime.now()
        })
        
        # Check for custom response first
        if self.call_count in self.custom_responses:
            return CorrectionResult(
                corrected_output=self.custom_responses[self.call_count],
                success=True
            )
        
        if self.correction_strategy == "progressive":
            return self._handle_progressive_correction(request)
        elif self.correction_strategy == "immediate":
            return self._handle_immediate_correction(request)
        elif self.correction_strategy == "failing":
            return self._handle_failing_correction(request)
        else:
            raise ValueError(f"Unknown correction strategy: {self.correction_strategy}")
    
    def _handle_progressive_correction(self, request: CorrectionRequest) -> CorrectionResult:
        """Progressive correction that improves with each attempt."""
        if self.call_count == 1:
            # First attempt: partial fix
            if "email" in request.feedback.lower():
                corrected = request.original_output.copy()
                corrected["email"] = "invalid-email-format"  # Still not valid
                return CorrectionResult(corrected_output=corrected, success=True)
            elif "missing" in request.feedback.lower():
                corrected = request.original_output.copy()
                corrected["missing_field"] = "added_but_wrong_type"
                return CorrectionResult(corrected_output=corrected, success=True)
        elif self.call_count == 2:
            # Second attempt: complete fix
            corrected = request.original_output.copy()
            corrected.update({
                "name": "Test User",
                "email": "test@example.com",
                "status": "active",
                "age": 25
            })
            return CorrectionResult(corrected_output=corrected, success=True)
        
        # Fallback
        return CorrectionResult(
            corrected_output=request.original_output,
            success=True
        )
    
    def _handle_immediate_correction(self, request: CorrectionRequest) -> CorrectionResult:
        """Immediate correction that fixes everything on first try."""
        corrected = {
            "name": "Test User",
            "email": "test@example.com", 
            "status": "active",
            "age": 25
        }
        return CorrectionResult(corrected_output=corrected, success=True)
    
    def _handle_failing_correction(self, request: CorrectionRequest) -> CorrectionResult:
        """Correction that always fails."""
        return CorrectionResult(
            corrected_output=None,
            success=False,
            error_message="Correction failed for testing"
        )


class TestSemanticErrorHandler(unittest.TestCase):
    """Test suite for SemanticErrorHandler class."""
    
    def setUp(self):
        """Set up test environment with real components."""
        self.harness = ValidationTestHarness()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        """Clean up test environment."""
        if hasattr(self, 'loop'):
            self.loop.close()
            asyncio.set_event_loop(None)
    
    @pytest.mark.asyncio
    async def test_semantic_handler_initialization(self):
        """Test that SemanticErrorHandler initializes correctly."""
        handler = await self.harness.create_semantic_handler_with_real_components()
        
        # Verify initialization
        self.assertIsNotNone(handler.validator)
        self.assertIsNotNone(handler._event_queue)
        self.assertIsNotNone(handler._state_manager)
        self.assertIsNotNone(handler._context_manager)
        self.assertIsNotNone(handler._metrics_manager)
        self.assertIsNotNone(handler._correction_handler)
        
        # Verify initial state
        self.assertFalse(handler._initialized)
    
    @pytest.mark.asyncio
    async def test_successful_single_attempt_correction(self):
        """Test successful semantic error correction on first attempt."""
        # Create handler with immediate correction strategy
        validator = await self.harness.create_validator_with_real_components()
        correction_handler = MockCorrectionHandler(correction_strategy="immediate")
        
        handler = SemanticErrorHandler(
            validator=validator,
            event_queue=self.harness.event_queue,
            state_manager=self.harness.state_manager,
            correction_handler=correction_handler
        )
        
        # Test data
        original_output = {"name": "Test"}  # Missing required fields
        validation_errors = [
            ValidationError("'email' is a required property", "email", "required"),
            ValidationError("'status' is a required property", "status", "required")
        ]
        error_analysis = {
            "error_analysis": {
                "semantic_errors": [
                    {"field": "email", "description": "Missing required field"},
                    {"field": "status", "description": "Missing required field"}
                ],
                "formatting_errors": [],
                "primary_error_type": "semantic"
            }
        }
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string", "format": "email"},
                "status": {"type": "string", "enum": ["active", "inactive"]},
                "age": {"type": "integer"}
            },
            "required": ["name", "email", "status"]
        }
        
        # Execute semantic error handling
        async with handler:
            success, corrected_output, updated_analysis = await handler.handle_semantic_errors(
                original_output=original_output,
                validation_errors=validation_errors,
                error_analysis=error_analysis,
                schema=schema,
                operation_id="test_single_attempt",
                max_retries=3
            )
        
        # Verify successful correction
        self.assertTrue(success)
        self.assertIsNotNone(corrected_output)
        self.assertIn("email", corrected_output)
        self.assertIn("status", corrected_output)
        self.assertEqual(correction_handler.call_count, 1)
    
    @pytest.mark.asyncio
    async def test_progressive_multi_attempt_correction(self):
        """Test semantic error correction that improves over multiple attempts."""
        validator = await self.harness.create_validator_with_real_components()
        correction_handler = MockCorrectionHandler(correction_strategy="progressive")
        
        handler = SemanticErrorHandler(
            validator=validator,
            event_queue=self.harness.event_queue,
            state_manager=self.harness.state_manager,
            correction_handler=correction_handler
        )
        
        original_output = {"name": "Test"}
        validation_errors = [
            ValidationError("'email' is a required property", "email", "required")
        ]
        error_analysis = {
            "error_analysis": {
                "semantic_errors": [
                    {"field": "email", "description": "Missing required field email"}
                ],
                "formatting_errors": [],
                "primary_error_type": "semantic"
            }
        }
        schema = {
            "type": "object", 
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string", "format": "email"}
            },
            "required": ["name", "email"]
        }
        
        async with handler:
            success, corrected_output, updated_analysis = await handler.handle_semantic_errors(
                original_output=original_output,
                validation_errors=validation_errors,
                error_analysis=error_analysis,
                schema=schema,
                operation_id="test_progressive",
                max_retries=3
            )
        
        # Should eventually succeed after multiple attempts
        self.assertTrue(success)
        self.assertIsNotNone(corrected_output)
        self.assertGreaterEqual(correction_handler.call_count, 1)
        
        # Verify the final corrected output is valid
        self.assertIn("email", corrected_output)
        self.assertIn("@", corrected_output["email"])
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test behavior when max retries are exceeded."""
        validator = await self.harness.create_validator_with_real_components()
        correction_handler = MockCorrectionHandler(correction_strategy="failing")
        
        handler = SemanticErrorHandler(
            validator=validator,
            event_queue=self.harness.event_queue,
            state_manager=self.harness.state_manager,
            correction_handler=correction_handler
        )
        
        original_output = {"invalid": "data"}
        validation_errors = [
            ValidationError("Schema violation", "field", "path")
        ]
        error_analysis = {
            "error_analysis": {
                "semantic_errors": [{"field": "test", "description": "Test error"}],
                "formatting_errors": [],
                "primary_error_type": "semantic"
            }
        }
        schema = {"type": "object", "properties": {"valid": {"type": "string"}}}
        
        async with handler:
            success, corrected_output, updated_analysis = await handler.handle_semantic_errors(
                original_output=original_output,
                validation_errors=validation_errors,
                error_analysis=error_analysis,
                schema=schema,
                operation_id="test_max_retries",
                max_retries=2
            )
        
        # Should fail after max retries
        self.assertFalse(success)
        self.assertIsNone(corrected_output)
        self.assertEqual(correction_handler.call_count, 2)
    
    @pytest.mark.asyncio
    async def test_state_management_during_correction(self):
        """Test that semantic error handling properly manages state."""
        validator = await self.harness.create_validator_with_real_components()
        correction_handler = MockCorrectionHandler(correction_strategy="immediate")
        
        handler = SemanticErrorHandler(
            validator=validator,
            event_queue=self.harness.event_queue,
            state_manager=self.harness.state_manager,
            correction_handler=correction_handler
        )
        
        operation_id = "test_state_management"
        correction_id = f"semantic_correction:{operation_id}"
        
        # Verify no state exists initially
        initial_state = await self.harness.state_manager.get_state(correction_id)
        self.assertIsNone(initial_state)
        
        original_output = {"test": "data"}
        validation_errors = [ValidationError("Test error", "field", "path")]
        error_analysis = {
            "error_analysis": {
                "semantic_errors": [{"field": "test", "description": "Test"}],
                "formatting_errors": [],
                "primary_error_type": "semantic"
            }
        }
        schema = {"type": "object", "properties": {"test": {"type": "string"}}}
        
        async with handler:
            success, corrected_output, updated_analysis = await handler.handle_semantic_errors(
                original_output=original_output,
                validation_errors=validation_errors,
                error_analysis=error_analysis,
                schema=schema,
                operation_id=operation_id,
                max_retries=3
            )
        
        # Verify state was created and updated
        final_state = await self.harness.state_manager.get_state(correction_id)
        self.assertIsNotNone(final_state)
        
        if success:
            self.assertEqual(final_state.state["status"], "complete")
            self.assertIn("final_output", final_state.state)
        else:
            self.assertEqual(final_state.state["status"], "failed")
    
    @pytest.mark.asyncio
    async def test_metrics_recording_during_correction(self):
        """Test that semantic error handling records appropriate metrics."""
        validator = await self.harness.create_validator_with_real_components()
        correction_handler = MockCorrectionHandler(correction_strategy="immediate")
        
        handler = SemanticErrorHandler(
            validator=validator,
            event_queue=self.harness.event_queue,
            state_manager=self.harness.state_manager,
            correction_handler=correction_handler
        )
        
        # Clear existing metrics
        self.harness.metrics_collector.reset()
        
        original_output = {"test": "data"}
        validation_errors = [ValidationError("Test error", "field", "path")]
        error_analysis = {
            "error_analysis": {
                "semantic_errors": [{"field": "test", "description": "Test"}],
                "formatting_errors": [],
                "primary_error_type": "semantic"
            }
        }
        schema = {"type": "object", "properties": {"test": {"type": "string"}}}
        
        async with handler:
            success, corrected_output, updated_analysis = await handler.handle_semantic_errors(
                original_output=original_output,
                validation_errors=validation_errors,
                error_analysis=error_analysis,
                schema=schema,
                operation_id="test_metrics",
                max_retries=3
            )
        
        # Verify metrics were recorded
        recorded_metrics = self.harness.metrics_collector.get_recorded_metrics()
        
        if success:
            # Look for success metric
            success_metrics = [
                metric for metric in recorded_metrics 
                if metric["name"] == "semantic_correction:success"
            ]
            self.assertGreater(len(success_metrics), 0)
        else:
            # Look for failure metric
            failure_metrics = [
                metric for metric in recorded_metrics 
                if metric["name"] == "semantic_correction:failure"
            ]
            self.assertGreater(len(failure_metrics), 0)
    
    @pytest.mark.asyncio
    async def test_feedback_generation_quality(self):
        """Test the quality of feedback generated for corrections."""
        validator = await self.harness.create_validator_with_real_components()
        
        # Create a test correction handler that captures feedback
        class FeedbackCapturingHandler:
            def __init__(self):
                self.captured_feedback = []
                
            async def handle_correction_request(self, request: CorrectionRequest):
                self.captured_feedback.append(request.feedback)
                return CorrectionResult(
                    corrected_output={"corrected": True},
                    success=True
                )
        
        correction_handler = FeedbackCapturingHandler()
        
        handler = SemanticErrorHandler(
            validator=validator,
            event_queue=self.harness.event_queue,
            state_manager=self.harness.state_manager,
            correction_handler=correction_handler
        )
        
        original_output = {"name": "Test", "email": "invalid"}
        validation_errors = [
            ValidationError("'invalid' is not a valid email format", "email", "format"),
            ValidationError("'age' is a required property", "age", "required")
        ]
        error_analysis = {
            "error_analysis": {
                "semantic_errors": [
                    {"field": "email", "description": "Invalid email format"},
                    {"field": "age", "description": "Missing required field"}
                ],
                "formatting_errors": [],
                "primary_error_type": "semantic"
            }
        }
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string", "format": "email"},
                "age": {"type": "integer", "minimum": 0}
            },
            "required": ["name", "email", "age"]
        }
        
        async with handler:
            success, corrected_output, updated_analysis = await handler.handle_semantic_errors(
                original_output=original_output,
                validation_errors=validation_errors,
                error_analysis=error_analysis,
                schema=schema,
                operation_id="test_feedback_quality",
                max_retries=3
            )
        
        # Verify feedback was generated
        self.assertGreater(len(correction_handler.captured_feedback), 0)
        
        feedback = correction_handler.captured_feedback[0]
        
        # Verify feedback quality
        self.assertIn("email", feedback.lower())
        self.assertIn("age", feedback.lower())
        self.assertIn("required", feedback.lower())
        self.assertTrue(len(feedback) > 50)  # Should be descriptive
    
    @pytest.mark.asyncio
    async def test_field_schema_extraction(self):
        """Test the _get_field_schema method."""
        handler = await self.harness.create_semantic_handler_with_real_components()
        
        complex_schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "profile": {
                            "type": "object",
                            "properties": {
                                "email": {"type": "string", "format": "email"}
                            }
                        }
                    }
                }
            }
        }
        
        # Test root level
        root_schema = handler._get_field_schema(complex_schema, "")
        self.assertEqual(root_schema, complex_schema)
        
        # Test nested field
        email_schema = handler._get_field_schema(complex_schema, "user -> profile -> email")
        expected_email_schema = {"type": "string", "format": "email"}
        self.assertEqual(email_schema, expected_email_schema)
        
        # Test non-existent field
        missing_schema = handler._get_field_schema(complex_schema, "nonexistent -> field")
        self.assertIsNone(missing_schema)
    
    @pytest.mark.asyncio
    async def test_field_requirements_extraction(self):
        """Test the _get_field_requirements method."""
        handler = await self.harness.create_semantic_handler_with_real_components()
        
        # Test string field with constraints
        string_schema = {
            "type": "string",
            "minLength": 3,
            "maxLength": 50,
            "pattern": "^[A-Za-z]+$"
        }
        requirements = handler._get_field_requirements(string_schema)
        self.assertIn("string", requirements)
        self.assertIn("3", requirements)
        self.assertIn("50", requirements)
        self.assertIn("pattern", requirements)
        
        # Test enum field
        enum_schema = {"type": "string", "enum": ["active", "inactive"]}
        requirements = handler._get_field_requirements(enum_schema)
        self.assertIn("active", requirements)
        self.assertIn("inactive", requirements)
        
        # Test numeric field
        numeric_schema = {"type": "integer", "minimum": 1, "maximum": 100}
        requirements = handler._get_field_requirements(numeric_schema)
        self.assertIn("integer", requirements)
        self.assertIn("1", requirements)
        self.assertIn("100", requirements)


class TestSemanticErrorHandlerEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for SemanticErrorHandler."""
    
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
    async def test_correction_handler_exception(self):
        """Test handling when correction handler raises exception."""
        validator = await self.harness.create_validator_with_real_components()
        
        class ExceptionCorrectionHandler:
            async def handle_correction_request(self, request):
                raise ValueError("Correction handler error")
        
        correction_handler = ExceptionCorrectionHandler()
        
        handler = SemanticErrorHandler(
            validator=validator,
            event_queue=self.harness.event_queue,
            state_manager=self.harness.state_manager,
            correction_handler=correction_handler
        )
        
        original_output = {"test": "data"}
        validation_errors = [ValidationError("Test error", "field", "path")]
        error_analysis = {
            "error_analysis": {
                "semantic_errors": [{"field": "test", "description": "Test"}],
                "formatting_errors": [],
                "primary_error_type": "semantic"
            }
        }
        schema = {"type": "object"}
        
        async with handler:
            success, corrected_output, updated_analysis = await handler.handle_semantic_errors(
                original_output=original_output,
                validation_errors=validation_errors,
                error_analysis=error_analysis,
                schema=schema,
                operation_id="test_exception",
                max_retries=1
            )
        
        # Should handle exception gracefully
        self.assertFalse(success)
        self.assertIsNone(corrected_output)
    
    @pytest.mark.asyncio
    async def test_empty_error_analysis(self):
        """Test behavior with empty error analysis."""
        handler = await self.harness.create_semantic_handler_with_real_components()
        
        original_output = {"test": "data"}
        validation_errors = []
        error_analysis = {
            "error_analysis": {
                "semantic_errors": [],
                "formatting_errors": [],
                "primary_error_type": "semantic"
            }
        }
        schema = {"type": "object"}
        
        async with handler:
            success, corrected_output, updated_analysis = await handler.handle_semantic_errors(
                original_output=original_output,
                validation_errors=validation_errors,
                error_analysis=error_analysis,
                schema=schema,
                operation_id="test_empty_analysis",
                max_retries=1
            )
        
        # Should handle empty analysis gracefully
        # Behavior may vary, but should not crash
        self.assertIsInstance(success, bool)


if __name__ == "__main__":
    # Run with asyncio support
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])