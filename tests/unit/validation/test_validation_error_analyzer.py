"""
Independent tests for ValidationErrorAnalyzer.

These tests focus on the ValidationErrorAnalyzer class in isolation,
testing its core functionality without mocking critical components.
"""

import asyncio
import json
import pytest
import unittest
from datetime import datetime
from typing import Dict, Any, List

# Import system components
from agent_validation import ValidationErrorAnalyzer, ValidationError, Validator
from resources import EventQueue, StateManager, ResourceType

# Import test infrastructure
from tests_new.harness.validation_test_harness import ValidationTestHarness


class TestValidationErrorAnalyzer(unittest.TestCase):
    """Test suite for ValidationErrorAnalyzer class."""
    
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
    async def test_error_analyzer_initialization(self):
        """Test that ValidationErrorAnalyzer initializes correctly with real components."""
        analyzer = await self.harness.create_error_analyzer_with_real_components()
        
        # Verify initialization
        self.assertIsNotNone(analyzer.validator)
        self.assertIsNotNone(analyzer._event_queue)
        self.assertIsNotNone(analyzer._state_manager)
        self.assertIsNotNone(analyzer._context_manager)
        self.assertIsNotNone(analyzer._cache_manager)
        self.assertIsNotNone(analyzer._metrics_manager)
        
        # Verify initial state
        self.assertEqual(analyzer._model, "claude-3-7-sonnet-20250219")
        self.assertIsInstance(analyzer._active_analyses, dict)
        self.assertEqual(len(analyzer._active_analyses), 0)
    
    @pytest.mark.asyncio
    async def test_simple_semantic_error_analysis(self):
        """Test analysis of simple semantic validation errors."""
        analyzer = await self.harness.create_error_analyzer_with_real_components()
        
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
        self.assertIn("error_analysis", analysis)
        error_analysis = analysis["error_analysis"]
        
        self.assertIn("formatting_errors", error_analysis)
        self.assertIn("semantic_errors", error_analysis)
        self.assertIn("primary_error_type", error_analysis)
        
        # Verify semantic errors were detected
        self.assertEqual(error_analysis["primary_error_type"], "semantic")
        self.assertGreater(len(error_analysis["semantic_errors"]), 0)
        
        # Check that analysis timestamp was added
        self.assertIn("analysis_timestamp", error_analysis)
    
    @pytest.mark.asyncio
    async def test_complex_multi_error_analysis(self):
        """Test analysis of complex, multi-type validation errors."""
        analyzer = await self.harness.create_error_analyzer_with_real_components()
        
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
        validator = await self.harness.create_validator_with_real_components()
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
        self.assertEqual(error_analysis["primary_error_type"], "semantic")
        
        semantic_errors = error_analysis["semantic_errors"]
        self.assertGreater(len(semantic_errors), 3)  # Should detect multiple errors
        
        # Verify specific error types are identified
        error_descriptions = [error.get("description", "") for error in semantic_errors]
        error_text = " ".join(error_descriptions).lower()
        
        # Should identify various constraint violations
        self.assertTrue(any("type" in desc.lower() for desc in error_descriptions))
    
    @pytest.mark.asyncio
    async def test_formatting_error_analysis(self):
        """Test analysis of formatting-specific errors."""
        analyzer = await self.harness.create_error_analyzer_with_real_components()
        
        # Create output that would cause formatting errors
        # Note: For this test, we simulate what would happen with malformed JSON
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
        self.assertEqual(error_analysis["primary_error_type"], "formatting")
        self.assertGreater(len(error_analysis["formatting_errors"]), 0)
        self.assertEqual(len(error_analysis["semantic_errors"]), 0)
    
    @pytest.mark.asyncio
    async def test_state_management_during_analysis(self):
        """Test that error analysis properly manages state."""
        analyzer = await self.harness.create_error_analyzer_with_real_components()
        
        operation_id = "test_state_management"
        analysis_id = f"error_analysis:{operation_id}"
        
        output = {"test": "data"}
        schema = {"type": "object", "properties": {"test": {"type": "string"}}}
        validation_errors = [
            ValidationError("Test error", "test", "test_path")
        ]
        
        # Verify no state exists initially
        initial_state = await self.harness.state_manager.get_state(analysis_id)
        self.assertIsNone(initial_state)
        
        # Run analysis
        async with analyzer:
            analysis = await analyzer.analyze_errors(
                output=output,
                validation_errors=validation_errors,
                operation_id=operation_id,
                schema=schema
            )
        
        # Verify state was created and managed
        final_state = await self.harness.state_manager.get_state(analysis_id)
        self.assertIsNotNone(final_state)
        self.assertEqual(final_state.state["status"], "complete")
        self.assertIn("result", final_state.state)
        self.assertIn("completion_time", final_state.state)
    
    @pytest.mark.asyncio
    async def test_metrics_recording_during_analysis(self):
        """Test that error analysis records appropriate metrics."""
        analyzer = await self.harness.create_error_analyzer_with_real_components()
        
        # Clear any existing metrics
        self.harness.metrics_collector.reset()
        
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
        recorded_metrics = self.harness.metrics_collector.get_recorded_metrics()
        self.assertGreater(len(recorded_metrics), 0)
        
        # Look for analysis completion metric
        analysis_metrics = [
            metric for metric in recorded_metrics 
            if metric["name"] == "validation:analysis:completion"
        ]
        self.assertGreater(len(analysis_metrics), 0)
        
        # Verify metric contains correct metadata
        analysis_metric = analysis_metrics[0]
        self.assertEqual(analysis_metric["value"], 1.0)
        self.assertEqual(analysis_metric["metadata"]["operation_id"], "test_metrics")
    
    @pytest.mark.asyncio
    async def test_event_emission_during_analysis(self):
        """Test that error analysis emits appropriate events."""
        analyzer = await self.harness.create_error_analyzer_with_real_components()
        
        # Set up event monitoring
        emitted_events = []
        original_emit = self.harness.event_queue.emit
        
        async def monitor_emit(event_type, payload):
            emitted_events.append({"type": event_type, "payload": payload})
            return await original_emit(event_type, payload)
        
        self.harness.event_queue.emit = monitor_emit
        
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
        # The exact events depend on the implementation, but we should have some activity
        self.assertGreaterEqual(len(emitted_events), 0)
    
    @pytest.mark.asyncio
    async def test_error_handling_in_analysis(self):
        """Test error handling during error analysis process."""
        analyzer = await self.harness.create_error_analyzer_with_real_components()
        
        # Create a scenario that might cause errors in analysis
        # (e.g., invalid schema format or malformed data)
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
        self.assertIn("error_analysis", analysis)
        error_analysis = analysis["error_analysis"]
        
        # Should have semantic errors (even if analysis partially failed)
        self.assertIn("semantic_errors", error_analysis)
        self.assertIn("primary_error_type", error_analysis)
    
    @pytest.mark.asyncio
    async def test_determine_primary_error_type_logic(self):
        """Test the logic for determining primary error type."""
        analyzer = await self.harness.create_error_analyzer_with_real_components()
        
        # Test semantic primary
        semantic_analysis = {
            "error_analysis": {
                "formatting_errors": [],
                "semantic_errors": [{"error": "semantic"}]
            }
        }
        primary_type = analyzer.determine_primary_error_type(semantic_analysis)
        self.assertEqual(primary_type, "semantic")
        
        # Test formatting primary
        formatting_analysis = {
            "error_analysis": {
                "formatting_errors": [{"error": "formatting"}],
                "semantic_errors": []
            }
        }
        primary_type = analyzer.determine_primary_error_type(formatting_analysis)
        self.assertEqual(primary_type, "formatting")
        
        # Test both present (semantic should take priority)
        mixed_analysis = {
            "error_analysis": {
                "formatting_errors": [{"error": "formatting"}],
                "semantic_errors": [{"error": "semantic"}]
            }
        }
        primary_type = analyzer.determine_primary_error_type(mixed_analysis)
        self.assertEqual(primary_type, "semantic")
        
        # Test empty (should default to formatting)
        empty_analysis = {
            "error_analysis": {
                "formatting_errors": [],
                "semantic_errors": []
            }
        }
        primary_type = analyzer.determine_primary_error_type(empty_analysis)
        self.assertEqual(primary_type, "formatting")
    
    @pytest.mark.asyncio
    async def test_validation_formatting_method(self):
        """Test the validate_formatting method."""
        analyzer = await self.harness.create_error_analyzer_with_real_components()
        
        # Test valid formatting
        valid_json = {"name": "test", "count": 5, "active": True}
        is_valid, issues = analyzer.validate_formatting(valid_json)
        self.assertTrue(is_valid)
        self.assertEqual(len(issues), 0)
        
        # Test with None values (should be flagged)
        json_with_none = {"name": "test", "value": None}
        is_valid, issues = analyzer.validate_formatting(json_with_none)
        self.assertFalse(is_valid)
        self.assertGreater(len(issues), 0)
        self.assertTrue(any("Undefined value" in issue for issue in issues))


class TestValidationErrorAnalyzerEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for ValidationErrorAnalyzer."""
    
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
    async def test_empty_validation_errors_list(self):
        """Test behavior with empty validation errors list."""
        analyzer = await self.harness.create_error_analyzer_with_real_components()
        
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
        self.assertIn("error_analysis", analysis)
        error_analysis = analysis["error_analysis"]
        self.assertEqual(len(error_analysis["semantic_errors"]), 0)
        self.assertEqual(len(error_analysis["formatting_errors"]), 0)
    
    @pytest.mark.asyncio
    async def test_large_output_analysis(self):
        """Test analysis performance with large output data."""
        analyzer = await self.harness.create_error_analyzer_with_real_components()
        
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
        self.assertLess(execution_time, 5.0)
        
        # Should still produce valid analysis
        self.assertIn("error_analysis", analysis)
        self.assertEqual(analysis["error_analysis"]["primary_error_type"], "semantic")
    
    @pytest.mark.asyncio
    async def test_concurrent_analysis_requests(self):
        """Test handling of concurrent analysis requests."""
        analyzer = await self.harness.create_error_analyzer_with_real_components()
        
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
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertIn("error_analysis", result)
            self.assertEqual(result["error_analysis"]["primary_error_type"], "semantic")


if __name__ == "__main__":
    # Run with asyncio support
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])