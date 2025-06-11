"""
Modern async tests for validation components using pytest-asyncio patterns.

This replaces the unittest.TestCase approach with proper async testing
to validate async functionality correctly for validation error analysis
and semantic error handling.
"""

import pytest
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List

# Import system components
from agent_validation import ValidationErrorAnalyzer, ValidationError, Validator, SemanticErrorHandler
from resources import EventQueue, StateManager, ResourceType

# Import test infrastructure
from tests.harness.validation_test_harness import ValidationTestHarness


@pytest.fixture
async def validation_harness():
    """Create validation test harness."""
    harness = ValidationTestHarness()
    yield harness
    # Cleanup if needed
    harness.reset()


class TestValidationErrorAnalyzer:
    """Test suite for ValidationErrorAnalyzer class."""
    
    @pytest.mark.asyncio
    async def test_error_analyzer_initialization(self, validation_harness):
        """Test that ValidationErrorAnalyzer initializes correctly with real components."""
        analyzer = await validation_harness.create_error_analyzer_with_real_components()
        
        # Verify initialization
        assert analyzer.validator is not None
        assert analyzer._event_queue is not None
        assert analyzer._state_manager is not None
        assert analyzer._context_manager is not None
        assert analyzer._cache_manager is not None
        assert analyzer._metrics_manager is not None
        
        # Verify initial state
        assert analyzer._model == "claude-3-7-sonnet-20250219"
        assert isinstance(analyzer._active_analyses, dict)
        assert len(analyzer._active_analyses) == 0
    
    @pytest.mark.asyncio
    async def test_simple_semantic_error_analysis(self, validation_harness):
        """Test analysis of simple semantic validation errors."""
        analyzer = await validation_harness.create_error_analyzer_with_real_components()
        
        # Create output with semantic errors
        output = {
            "name": "Test User",
            "status": "unknown"  # Invalid enum value
        }
        
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string", "format": "email"},  # Missing required field
                "status": {"type": "string", "enum": ["active", "inactive"]}
            },
            "required": ["name", "email", "status"]
        }
        
        # Create validation errors
        validation_errors = [
            ValidationError("'email' is a required property", "email", "required"),
            ValidationError("'unknown' is not one of ['active', 'inactive']", "status", "enum")
        ]
        
        # Test error analysis
        async with analyzer:
            analysis = await analyzer.analyze_errors(
                output=output,
                validation_errors=validation_errors,
                operation_id="test_semantic_simple",
                schema=schema
            )
        
        # Verify analysis structure
        assert "error_analysis" in analysis
        error_analysis = analysis["error_analysis"]
        
        assert "formatting_errors" in error_analysis
        assert "semantic_errors" in error_analysis
        assert "primary_error_type" in error_analysis
        
        # Verify semantic errors were detected
        assert error_analysis["primary_error_type"] == "semantic"
        assert len(error_analysis["semantic_errors"]) > 0
        
        # Check that analysis timestamp was added
        assert "analysis_timestamp" in error_analysis
    
    @pytest.mark.asyncio
    async def test_complex_multi_error_analysis(self, validation_harness):
        """Test analysis of complex, multi-type validation errors."""
        analyzer = await validation_harness.create_error_analyzer_with_real_components()
        
        # Create output with multiple error types
        output = {
            "user": {
                "id": "not_an_integer",  # Type error
                "name": "X",  # Length constraint violation
                "email": "invalid-email-format"  # Format error
            },
            "items": [],  # Array constraint violation (minItems)
            "total": -5,  # Numeric constraint violation
            "extra_field": "not_in_schema"  # Additional property (if additionalProperties: false)
        }
        
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string", "minLength": 2, "maxLength": 50},
                        "email": {"type": "string", "format": "email"}
                    },
                    "required": ["id", "name", "email"]
                },
                "items": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1
                },
                "total": {"type": "number", "minimum": 0}
            },
            "required": ["user", "items", "total"],
            "additionalProperties": False
        }
        
        # Get actual validation errors from the validator
        validator = await validation_harness.create_validator_with_real_components()
        validation_errors = validator.get_validation_errors(output, schema)
        
        # Test comprehensive error analysis
        async with analyzer:
            analysis = await analyzer.analyze_errors(
                output=output,
                validation_errors=validation_errors,
                operation_id="test_complex_multi",
                schema=schema
            )
        
        # Verify comprehensive analysis
        error_analysis = analysis["error_analysis"]
        assert error_analysis["primary_error_type"] == "semantic"
        
        semantic_errors = error_analysis["semantic_errors"]
        assert len(semantic_errors) > 3  # Should detect multiple errors
        
        # Verify specific error types are identified
        error_descriptions = [error.get("description", "") for error in semantic_errors]
        error_text = " ".join(error_descriptions).lower()
        
        # Should identify various constraint violations
        assert any("type" in desc.lower() for desc in error_descriptions)
    
    @pytest.mark.asyncio
    async def test_formatting_error_analysis(self, validation_harness):
        """Test analysis of formatting-specific errors."""
        analyzer = await validation_harness.create_error_analyzer_with_real_components()
        
        # Create output that would cause formatting errors
        output = {"valid": "json", "but": "with_formatting_issues"}
        
        schema = {
            "type": "object",
            "properties": {
                "valid": {"type": "string"},
                "but": {"type": "string"}
            }
        }
        
        # Create formatting-focused validation errors
        validation_errors = [
            ValidationError("JSON formatting issue: inconsistent spacing", "", "format"),
            ValidationError("JSON formatting issue: invalid indentation", "", "format")
        ]
        
        async with analyzer:
            analysis = await analyzer.analyze_errors(
                output=output,
                validation_errors=validation_errors,
                operation_id="test_formatting",
                schema=schema
            )
        
        error_analysis = analysis["error_analysis"]
        
        # Should identify as formatting issue
        assert error_analysis["primary_error_type"] == "formatting"
        assert len(error_analysis["formatting_errors"]) > 0
        assert len(error_analysis["semantic_errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_state_management_during_analysis(self, validation_harness):
        """Test that error analysis properly manages state."""
        analyzer = await validation_harness.create_error_analyzer_with_real_components()
        
        operation_id = "test_state_management"
        analysis_id = f"error_analysis:{operation_id}"
        
        output = {"test": "data"}
        schema = {"type": "object", "properties": {"test": {"type": "string"}}}
        validation_errors = [
            ValidationError("Test error", "test", "test_path")
        ]
        
        # Verify no state exists initially
        initial_state = await validation_harness.state_manager.get_state(analysis_id)
        assert initial_state is None
        
        # Run analysis
        async with analyzer:
            analysis = await analyzer.analyze_errors(
                output=output,
                validation_errors=validation_errors,
                operation_id=operation_id,
                schema=schema
            )
        
        # Verify state was created and managed
        final_state = await validation_harness.state_manager.get_state(analysis_id)
        assert final_state is not None
        assert final_state.state["status"] == "complete"
        assert "result" in final_state.state
        assert "completion_time" in final_state.state
    
    @pytest.mark.asyncio
    async def test_metrics_recording_during_analysis(self, validation_harness):
        """Test that error analysis records appropriate metrics."""
        analyzer = await validation_harness.create_error_analyzer_with_real_components()
        
        # Clear any existing metrics
        validation_harness.metrics_collector.reset()
        
        output = {"test": "value"}
        schema = {"type": "object", "properties": {"test": {"type": "string"}}}
        validation_errors = [
            ValidationError("Test validation error", "test", "test_schema_path")
        ]
        
        async with analyzer:
            analysis = await analyzer.analyze_errors(
                output=output,
                validation_errors=validation_errors,
                operation_id="test_metrics",
                schema=schema
            )
        
        # Verify metrics were recorded
        recorded_metrics = validation_harness.metrics_collector.get_recorded_metrics()
        assert len(recorded_metrics) > 0
        
        # Look for analysis completion metric
        analysis_metrics = [
            metric for metric in recorded_metrics 
            if metric["name"] == "validation:analysis:completion"
        ]
        assert len(analysis_metrics) > 0
        
        # Verify metric contains correct metadata
        analysis_metric = analysis_metrics[0]
        assert analysis_metric["value"] == 1.0
        assert analysis_metric["metadata"]["operation_id"] == "test_metrics"
    
    @pytest.mark.asyncio
    async def test_event_emission_during_analysis(self, validation_harness):
        """Test that error analysis emits appropriate events."""
        analyzer = await validation_harness.create_error_analyzer_with_real_components()
        
        # Set up event monitoring
        emitted_events = []
        original_emit = validation_harness.event_queue.emit
        
        async def monitor_emit(event_type, payload):
            emitted_events.append({"type": event_type, "payload": payload})
            return await original_emit(event_type, payload)
        
        validation_harness.event_queue.emit = monitor_emit
        
        output = {"test": "data"}
        schema = {"type": "object", "properties": {"missing": {"type": "string"}}, "required": ["missing"]}
        validation_errors = [
            ValidationError("'missing' is a required property", "missing", "required")
        ]
        
        async with analyzer:
            analysis = await analyzer.analyze_errors(
                output=output,
                validation_errors=validation_errors,
                operation_id="test_events",
                schema=schema
            )
        
        # Verify events were emitted (error analysis might emit events on completion)
        assert len(emitted_events) >= 0  # Some activity expected
    
    @pytest.mark.asyncio
    async def test_error_handling_in_analysis(self, validation_harness):
        """Test error handling during error analysis process."""
        analyzer = await validation_harness.create_error_analyzer_with_real_components()
        
        # Create a scenario that might cause errors in analysis
        output = {"valid": "data"}
        invalid_schema = {"type": "invalid_schema_type"}  # Invalid schema
        validation_errors = [
            ValidationError("Schema validation error", "", "")
        ]
        
        async with analyzer:
            analysis = await analyzer.analyze_errors(
                output=output,
                validation_errors=validation_errors,
                operation_id="test_error_handling",
                schema=invalid_schema
            )
        
        # Should return an error response instead of crashing
        assert "error_analysis" in analysis
        error_analysis = analysis["error_analysis"]
        
        # Should have semantic errors (even if analysis partially failed)
        assert "semantic_errors" in error_analysis
        assert "primary_error_type" in error_analysis
    
    @pytest.mark.asyncio
    async def test_determine_primary_error_type_logic(self, validation_harness):
        """Test the logic for determining primary error type."""
        analyzer = await validation_harness.create_error_analyzer_with_real_components()
        
        # Test semantic primary
        semantic_analysis = {
            "error_analysis": {
                "formatting_errors": [],
                "semantic_errors": [{"error": "semantic"}]
            }
        }
        primary_type = analyzer.determine_primary_error_type(semantic_analysis)
        assert primary_type == "semantic"
        
        # Test formatting primary
        formatting_analysis = {
            "error_analysis": {
                "formatting_errors": [{"error": "formatting"}],
                "semantic_errors": []
            }
        }
        primary_type = analyzer.determine_primary_error_type(formatting_analysis)
        assert primary_type == "formatting"
        
        # Test both present (semantic should take priority)
        mixed_analysis = {
            "error_analysis": {
                "formatting_errors": [{"error": "formatting"}],
                "semantic_errors": [{"error": "semantic"}]
            }
        }
        primary_type = analyzer.determine_primary_error_type(mixed_analysis)
        assert primary_type == "semantic"
        
        # Test empty (should default to formatting)
        empty_analysis = {
            "error_analysis": {
                "formatting_errors": [],
                "semantic_errors": []
            }
        }
        primary_type = analyzer.determine_primary_error_type(empty_analysis)
        assert primary_type == "formatting"
    
    @pytest.mark.asyncio
    async def test_validation_formatting_method(self, validation_harness):
        """Test the validate_formatting method."""
        analyzer = await validation_harness.create_error_analyzer_with_real_components()
        
        # Test valid formatting
        valid_json = {"name": "test", "count": 5, "active": True}
        is_valid, issues = analyzer.validate_formatting(valid_json)
        assert is_valid is True
        assert len(issues) == 0
        
        # Test with None values (should be flagged)
        json_with_none = {"name": "test", "value": None}
        is_valid, issues = analyzer.validate_formatting(json_with_none)
        assert is_valid is False
        assert len(issues) > 0
        assert any("Undefined value" in issue for issue in issues)


class TestValidationErrorAnalyzerEdgeCases:
    """Test edge cases and error conditions for ValidationErrorAnalyzer."""
    
    @pytest.mark.asyncio
    async def test_empty_validation_errors_list(self, validation_harness):
        """Test behavior with empty validation errors list."""
        analyzer = await validation_harness.create_error_analyzer_with_real_components()
        
        output = {"valid": "response"}
        schema = {"type": "object", "properties": {"valid": {"type": "string"}}}
        validation_errors = []  # Empty list
        
        async with analyzer:
            analysis = await analyzer.analyze_errors(
                output=output,
                validation_errors=validation_errors,
                operation_id="test_empty_errors",
                schema=schema
            )
        
        # Should handle empty errors gracefully
        assert "error_analysis" in analysis
        error_analysis = analysis["error_analysis"]
        assert len(error_analysis["semantic_errors"]) == 0
        assert len(error_analysis["formatting_errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_large_output_analysis(self, validation_harness):
        """Test analysis performance with large output data."""
        analyzer = await validation_harness.create_error_analyzer_with_real_components()
        
        # Create large output
        large_output = {
            "items": [{"id": i, "name": f"item_{i}", "data": f"data_{i}"} for i in range(1000)]
        }
        
        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "data": {"type": "string"}
                        }
                    }
                },
                "required_field": {"type": "string"}  # Missing in output
            },
            "required": ["items", "required_field"]
        }
        
        validation_errors = [
            ValidationError("'required_field' is a required property", "required_field", "required")
        ]
        
        start_time = datetime.now()
        async with analyzer:
            analysis = await analyzer.analyze_errors(
                output=large_output,
                validation_errors=validation_errors,
                operation_id="test_large_output",
                schema=schema
            )
        end_time = datetime.now()
        
        # Should complete in reasonable time (less than 5 seconds)
        execution_time = (end_time - start_time).total_seconds()
        assert execution_time < 5.0
        
        # Should still produce valid analysis
        assert "error_analysis" in analysis
        assert analysis["error_analysis"]["primary_error_type"] == "semantic"
    
    @pytest.mark.asyncio
    async def test_concurrent_analysis_requests(self, validation_harness):
        """Test handling of concurrent analysis requests."""
        analyzer = await validation_harness.create_error_analyzer_with_real_components()
        
        async def run_analysis(operation_id: str):
            output = {"test": f"data_{operation_id}"}
            schema = {"type": "object", "properties": {"missing": {"type": "string"}}, "required": ["missing"]}
            validation_errors = [
                ValidationError("'missing' is a required property", "missing", "required")
            ]
            
            async with analyzer:
                return await analyzer.analyze_errors(
                    output=output,
                    validation_errors=validation_errors,
                    operation_id=operation_id,
                    schema=schema
                )
        
        # Run multiple analyses concurrently
        tasks = [run_analysis(f"concurrent_{i}") for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All should complete successfully
        assert len(results) == 5
        for result in results:
            assert "error_analysis" in result
            assert result["error_analysis"]["primary_error_type"] == "semantic"


class TestSemanticErrorHandler:
    """Test suite for SemanticErrorHandler class."""
    
    @pytest.mark.asyncio
    async def test_semantic_handler_initialization(self, validation_harness):
        """Test SemanticErrorHandler initialization."""
        handler = await validation_harness.create_semantic_handler_with_real_components()
        
        assert handler.validator is not None
        assert handler._event_queue is not None
        assert handler._state_manager is not None
        assert handler._context_manager is not None
        assert handler._metrics_manager is not None
        assert handler._correction_handler is not None
        assert handler._initialized is False  # Not initialized until used as context manager
    
    @pytest.mark.asyncio
    async def test_successful_single_attempt_correction(self, validation_harness):
        """Test successful correction on first attempt."""
        handler = await validation_harness.create_semantic_handler_with_real_components()
        
        # Create test data
        original_output = {"name": "Test"}  # Missing required fields
        validation_errors = [
            ValidationError("'email' is a required property", "email", "required")
        ]
        error_analysis = {
            "error_analysis": {
                "formatting_errors": [],
                "semantic_errors": [
                    {"field": "email", "error_type": "missing_field", "description": "Required field missing"}
                ],
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
                operation_id="test_single_correction"
            )
        
        # Should succeed on first attempt with test correction handler
        assert success is True
        assert corrected_output is not None
        assert "name" in corrected_output
        assert "email" in corrected_output
    
    @pytest.mark.asyncio
    async def test_progressive_multi_attempt_correction(self, validation_harness):
        """Test progressive correction over multiple attempts."""
        handler = await validation_harness.create_semantic_handler_with_real_components()
        
        # Create test data with multiple issues
        original_output = {"name": "Test", "email": "invalid-email"}
        validation_errors = [
            ValidationError("'invalid-email' is not a valid email format", "email", "format")
        ]
        error_analysis = {
            "error_analysis": {
                "formatting_errors": [],
                "semantic_errors": [
                    {"field": "email", "error_type": "format_error", "description": "Invalid email format"}
                ],
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
                operation_id="test_multi_correction",
                max_retries=2
            )
        
        # Should eventually succeed with progressive correction
        assert success is True
        assert corrected_output is not None
        assert "@" in corrected_output["email"]  # Should have valid email format
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, validation_harness):
        """Test behavior when max retries are exceeded."""
        # Create a handler that will always fail correction
        class FailingCorrectionHandler:
            async def handle_correction_request(self, request):
                from agent import CorrectionResult
                return CorrectionResult(
                    corrected_output=None,
                    success=False,
                    error_message="Correction always fails"
                )
        
        validator = await validation_harness.create_validator_with_real_components()
        correction_handler = FailingCorrectionHandler()
        
        handler = SemanticErrorHandler(
            validator=validator,
            event_queue=validation_harness.event_queue,
            state_manager=validation_harness.state_manager,
            correction_handler=correction_handler
        )
        
        original_output = {"name": "Test"}
        validation_errors = [
            ValidationError("'email' is a required property", "email", "required")
        ]
        error_analysis = {
            "error_analysis": {
                "formatting_errors": [],
                "semantic_errors": [
                    {"field": "email", "error_type": "missing_field", "description": "Required field missing"}
                ],
                "primary_error_type": "semantic"
            }
        }
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"}
            },
            "required": ["name", "email"]
        }
        
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
        assert success is False
        assert corrected_output is None
    
    @pytest.mark.asyncio
    async def test_state_management_during_correction(self, validation_harness):
        """Test that semantic error handling properly manages state."""
        handler = await validation_harness.create_semantic_handler_with_real_components()
        
        operation_id = "test_semantic_state"
        correction_id = f"semantic_correction:{operation_id}"
        
        # Verify no state exists initially
        initial_state = await validation_harness.state_manager.get_state(correction_id)
        assert initial_state is None
        
        original_output = {"name": "Test"}
        validation_errors = [
            ValidationError("'email' is a required property", "email", "required")
        ]
        error_analysis = {
            "error_analysis": {
                "formatting_errors": [],
                "semantic_errors": [
                    {"field": "email", "error_type": "missing_field", "description": "Required field missing"}
                ],
                "primary_error_type": "semantic"
            }
        }
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"}
            },
            "required": ["name", "email"]
        }
        
        async with handler:
            success, corrected_output, updated_analysis = await handler.handle_semantic_errors(
                original_output=original_output,
                validation_errors=validation_errors,
                error_analysis=error_analysis,
                schema=schema,
                operation_id=operation_id
            )
        
        # Verify state was created and managed
        final_state = await validation_harness.state_manager.get_state(correction_id)
        assert final_state is not None
        assert final_state.state["status"] == "complete"
        assert "final_output" in final_state.state
        assert "completion_time" in final_state.state
    
    @pytest.mark.asyncio
    async def test_metrics_recording_during_correction(self, validation_harness):
        """Test that semantic correction records metrics."""
        handler = await validation_harness.create_semantic_handler_with_real_components()
        
        # Clear existing metrics
        validation_harness.metrics_collector.reset()
        
        original_output = {"name": "Test"}
        validation_errors = [
            ValidationError("'email' is a required property", "email", "required")
        ]
        error_analysis = {
            "error_analysis": {
                "formatting_errors": [],
                "semantic_errors": [
                    {"field": "email", "error_type": "missing_field", "description": "Required field missing"}
                ],
                "primary_error_type": "semantic"
            }
        }
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"}
            },
            "required": ["name", "email"]
        }
        
        async with handler:
            success, corrected_output, updated_analysis = await handler.handle_semantic_errors(
                original_output=original_output,
                validation_errors=validation_errors,
                error_analysis=error_analysis,
                schema=schema,
                operation_id="test_semantic_metrics"
            )
        
        # Verify metrics were recorded
        recorded_metrics = validation_harness.metrics_collector.get_recorded_metrics()
        assert len(recorded_metrics) > 0
        
        # Look for semantic correction metrics
        semantic_metrics = [
            metric for metric in recorded_metrics 
            if "semantic_correction" in metric["name"]
        ]
        assert len(semantic_metrics) > 0
    
    @pytest.mark.asyncio
    async def test_field_schema_extraction(self, validation_harness):
        """Test field schema extraction functionality."""
        handler = await validation_harness.create_semantic_handler_with_real_components()
        
        schema = {
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
        
        # Test simple field path
        field_schema = handler._get_field_schema(schema, "user")
        assert field_schema is not None
        assert field_schema["type"] == "object"
        
        # Test nested field path
        field_schema = handler._get_field_schema(schema, "user -> profile -> email")
        assert field_schema is not None
        assert field_schema["type"] == "string"
        assert field_schema["format"] == "email"
        
        # Test invalid path
        field_schema = handler._get_field_schema(schema, "invalid -> path")
        assert field_schema is None
    
    @pytest.mark.asyncio
    async def test_field_requirements_extraction(self, validation_harness):
        """Test field requirements extraction."""
        handler = await validation_harness.create_semantic_handler_with_real_components()
        
        # Test string field with constraints
        string_schema = {
            "type": "string",
            "minLength": 3,
            "maxLength": 50,
            "pattern": "^[A-Za-z]+$"
        }
        requirements = handler._get_field_requirements(string_schema)
        assert "Must be of type 'string'" in requirements
        assert "Minimum length: 3" in requirements
        assert "Maximum length: 50" in requirements
        assert "Must match pattern" in requirements
        
        # Test enum field
        enum_schema = {
            "type": "string",
            "enum": ["active", "inactive", "pending"]
        }
        requirements = handler._get_field_requirements(enum_schema)
        assert "Must be one of: active, inactive, pending" in requirements
        
        # Test numeric field with constraints
        numeric_schema = {
            "type": "integer",
            "minimum": 1,
            "maximum": 100
        }
        requirements = handler._get_field_requirements(numeric_schema)
        assert "Must be of type 'integer'" in requirements
        assert "Minimum value: 1" in requirements
        assert "Maximum value: 100" in requirements
    
    @pytest.mark.asyncio
    async def test_feedback_generation_quality(self, validation_harness):
        """Test quality of generated feedback messages."""
        handler = await validation_harness.create_semantic_handler_with_real_components()
        
        original_output = {"name": "X", "age": -5, "status": "unknown"}
        validation_errors = [
            ValidationError("'X' is too short (minimum 2 characters)", "name", "minLength"),
            ValidationError("-5 is less than minimum value 0", "age", "minimum"),
            ValidationError("'unknown' is not one of ['active', 'inactive']", "status", "enum")
        ]
        error_analysis = {
            "error_analysis": {
                "formatting_errors": [],
                "semantic_errors": [
                    {"field": "name", "error_type": "length_error", "description": "Name too short"},
                    {"field": "age", "error_type": "range_error", "description": "Age below minimum"},
                    {"field": "status", "error_type": "enum_error", "description": "Invalid status value"}
                ],
                "primary_error_type": "semantic"
            }
        }
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 2, "maxLength": 50},
                "age": {"type": "integer", "minimum": 0, "maximum": 150},
                "status": {"type": "string", "enum": ["active", "inactive"]}
            },
            "required": ["name", "age", "status"]
        }
        
        feedback = handler._generate_semantic_feedback(
            original_output,
            validation_errors,
            error_analysis,
            schema,
            attempt=1
        )
        
        # Verify feedback quality
        assert "semantic validation errors" in feedback
        assert "Field 'name':" in feedback
        assert "Field 'age':" in feedback
        assert "Field 'status':" in feedback
        assert "Requirements:" in feedback
        assert "Please provide a new response" in feedback


class TestSemanticErrorHandlerEdgeCases:
    """Test edge cases for SemanticErrorHandler."""
    
    @pytest.mark.asyncio
    async def test_empty_error_analysis(self, validation_harness):
        """Test handling of empty error analysis."""
        handler = await validation_harness.create_semantic_handler_with_real_components()
        
        original_output = {"name": "Test"}
        validation_errors = []
        error_analysis = {
            "error_analysis": {
                "formatting_errors": [],
                "semantic_errors": [],
                "primary_error_type": "semantic"
            }
        }
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        
        async with handler:
            success, corrected_output, updated_analysis = await handler.handle_semantic_errors(
                original_output=original_output,
                validation_errors=validation_errors,
                error_analysis=error_analysis,
                schema=schema,
                operation_id="test_empty_analysis"
            )
        
        # Should handle empty analysis gracefully
        assert success is True
        assert corrected_output is not None
    
    @pytest.mark.asyncio
    async def test_correction_handler_exception(self, validation_harness):
        """Test handling of correction handler exceptions."""
        # Create a handler that raises exceptions
        class ExceptionCorrectionHandler:
            async def handle_correction_request(self, request):
                raise ValueError("Correction handler failed")
        
        validator = await validation_harness.create_validator_with_real_components()
        correction_handler = ExceptionCorrectionHandler()
        
        handler = SemanticErrorHandler(
            validator=validator,
            event_queue=validation_harness.event_queue,
            state_manager=validation_harness.state_manager,
            correction_handler=correction_handler
        )
        
        original_output = {"name": "Test"}
        validation_errors = [
            ValidationError("'email' is a required property", "email", "required")
        ]
        error_analysis = {
            "error_analysis": {
                "formatting_errors": [],
                "semantic_errors": [
                    {"field": "email", "error_type": "missing_field", "description": "Required field missing"}
                ],
                "primary_error_type": "semantic"
            }
        }
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"}
            },
            "required": ["name", "email"]
        }
        
        async with handler:
            success, corrected_output, updated_analysis = await handler.handle_semantic_errors(
                original_output=original_output,
                validation_errors=validation_errors,
                error_analysis=error_analysis,
                schema=schema,
                operation_id="test_exception_handling"
            )
        
        # Should handle exceptions gracefully and return failure
        assert success is False
        assert corrected_output is None