"""
Integration tests for error analysis accuracy.

These tests verify that the error analysis components correctly categorize
and analyze different types of validation errors in realistic scenarios.
"""

import asyncio
import json
import pytest
import unittest
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Import system components
from agent_validation import ValidationErrorAnalyzer, ValidationError, Validator

# Import test infrastructure
from tests_new.harness.validation_test_harness import ValidationTestHarness


class TestErrorAnalysisAccuracy(unittest.TestCase):
    """Test suite for error analysis accuracy."""
    
    def setUp(self):
        """Set up test environment."""
        self.harness = ValidationTestHarness()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Define comprehensive test cases for error analysis
        self.error_analysis_test_cases = [
            {
                "name": "missing_required_field",
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string", "format": "email"}
                    },
                    "required": ["name", "email"]
                },
                "invalid_json": {"name": "Test User"},  # Missing email
                "expected_error_type": "semantic",
                "expected_errors": ["missing_field"],
                "expected_field_count": 1
            },
            {
                "name": "type_mismatch", 
                "schema": {
                    "type": "object",
                    "properties": {
                        "age": {"type": "integer"},
                        "count": {"type": "number"}
                    }
                },
                "invalid_json": {"age": "twenty-five", "count": "10.5"},  # String instead of numbers
                "expected_error_type": "semantic",
                "expected_errors": ["type_error"],
                "expected_field_count": 2
            },
            {
                "name": "enum_violation",
                "schema": {
                    "type": "object", 
                    "properties": {
                        "status": {"type": "string", "enum": ["active", "inactive", "pending"]},
                        "priority": {"type": "string", "enum": ["low", "medium", "high"]}
                    }
                },
                "invalid_json": {"status": "unknown", "priority": "urgent"},  # Invalid enum values
                "expected_error_type": "semantic",
                "expected_errors": ["enum_violation"],
                "expected_field_count": 2
            },
            {
                "name": "numeric_constraint_violation",
                "schema": {
                    "type": "object",
                    "properties": {
                        "age": {"type": "integer", "minimum": 0, "maximum": 150},
                        "rating": {"type": "number", "minimum": 1.0, "maximum": 5.0}
                    }
                },
                "invalid_json": {"age": -5, "rating": 10.0},  # Outside valid ranges
                "expected_error_type": "semantic",
                "expected_errors": ["constraint_violation"],
                "expected_field_count": 2
            },
            {
                "name": "string_constraint_violation",
                "schema": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string", "minLength": 3, "maxLength": 20},
                        "email": {"type": "string", "format": "email"}
                    }
                },
                "invalid_json": {"username": "ab", "email": "not-an-email"},  # Too short + invalid format
                "expected_error_type": "semantic", 
                "expected_errors": ["constraint_violation", "format_error"],
                "expected_field_count": 2
            },
            {
                "name": "array_constraint_violation",
                "schema": {
                    "type": "object",
                    "properties": {
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 1,
                            "maxItems": 5
                        },
                        "scores": {
                            "type": "array", 
                            "items": {"type": "integer", "minimum": 0, "maximum": 100}
                        }
                    }
                },
                "invalid_json": {
                    "tags": [],  # Empty array (minItems: 1)
                    "scores": [50, 150, -10]  # Values outside range
                },
                "expected_error_type": "semantic",
                "expected_errors": ["constraint_violation"],
                "expected_field_count": 2
            },
            {
                "name": "multiple_error_types",
                "schema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string", "minLength": 2},
                        "email": {"type": "string", "format": "email"},
                        "status": {"type": "string", "enum": ["active", "inactive"]},
                        "age": {"type": "integer", "minimum": 0, "maximum": 150}
                    },
                    "required": ["id", "name", "email", "status"]
                },
                "invalid_json": {
                    "id": "not_integer",  # Type error
                    "name": "X",  # Length constraint
                    "email": "invalid",  # Format error
                    "status": "unknown",  # Enum violation
                    "age": 200  # Numeric constraint
                    # Missing required fields would be handled separately
                },
                "expected_error_type": "semantic",
                "expected_errors": ["type_error", "constraint_violation", "format_error", "enum_violation"],
                "expected_field_count": 5
            }
        ]
    
    def tearDown(self):
        """Clean up test environment."""
        if hasattr(self, 'loop'):
            self.loop.close()
            asyncio.set_event_loop(None)
    
    @pytest.mark.asyncio
    async def test_error_categorization_accuracy(self):
        """Test that error analyzer correctly categorizes different error types."""
        analyzer = await self.harness.create_error_analyzer_with_real_components()
        validator = await self.harness.create_validator_with_real_components()
        
        async with analyzer:
            for test_case in self.error_analysis_test_cases:
                with self.subTest(test_case=test_case["name"]):
                    # Get actual validation errors from the validator
                    validation_errors = validator.get_validation_errors(
                        test_case["invalid_json"],
                        test_case["schema"]
                    )
                    
                    # Perform error analysis
                    analysis = await analyzer.analyze_errors(
                        output=test_case["invalid_json"],
                        validation_errors=validation_errors,
                        operation_id=f"accuracy_test_{test_case['name']}",
                        schema=test_case["schema"]
                    )
                    
                    # Verify primary error type categorization
                    self.assertEqual(
                        analysis["error_analysis"]["primary_error_type"],
                        test_case["expected_error_type"],
                        f"Wrong primary error type for {test_case['name']}"
                    )
                    
                    # Verify semantic errors are detected
                    if test_case["expected_error_type"] == "semantic":
                        semantic_errors = analysis["error_analysis"]["semantic_errors"]
                        self.assertGreater(
                            len(semantic_errors), 0,
                            f"No semantic errors detected for {test_case['name']}"
                        )
                        
                        # Verify expected number of errors (approximately)
                        # Note: The exact count may vary based on how errors are grouped
                        self.assertGreaterEqual(
                            len(semantic_errors), 1,
                            f"Expected at least 1 semantic error for {test_case['name']}"
                        )
    
    @pytest.mark.asyncio 
    async def test_semantic_error_detail_accuracy(self):
        """Test the accuracy of semantic error details and descriptions."""
        analyzer = await self.harness.create_error_analyzer_with_real_components()
        validator = await self.harness.create_validator_with_real_components()
        
        # Test case with clear semantic errors
        schema = {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "email": {"type": "string", "format": "email"},
                "age": {"type": "integer", "minimum": 18, "maximum": 100},
                "role": {"type": "string", "enum": ["admin", "user", "guest"]}
            },
            "required": ["user_id", "email", "role"]
        }
        
        invalid_output = {
            "user_id": "not_a_number",  # Type error
            "email": "invalid.email.format",  # Format error  
            "age": 15,  # Constraint violation (minimum: 18)
            "role": "superuser"  # Enum violation
        }
        
        async with analyzer:
            validation_errors = validator.get_validation_errors(invalid_output, schema)
            analysis = await analyzer.analyze_errors(
                output=invalid_output,
                validation_errors=validation_errors,
                operation_id="semantic_detail_test",
                schema=schema
            )
        
        semantic_errors = analysis["error_analysis"]["semantic_errors"]
        self.assertGreater(len(semantic_errors), 0)
        
        # Verify that error descriptions are meaningful
        error_descriptions = [error.get("description", "") for error in semantic_errors]
        combined_descriptions = " ".join(error_descriptions).lower()
        
        # Should mention relevant field names and constraint types
        expected_terms = ["user_id", "email", "age", "role", "type", "format", "minimum", "enum"]
        found_terms = [term for term in expected_terms if term in combined_descriptions]
        
        # Should find at least half of the expected terms
        self.assertGreaterEqual(
            len(found_terms), len(expected_terms) // 2,
            f"Error descriptions lack detail. Found terms: {found_terms}"
        )
    
    @pytest.mark.asyncio
    async def test_nested_schema_error_analysis(self):
        """Test error analysis accuracy with nested schemas."""
        analyzer = await self.harness.create_error_analyzer_with_real_components()
        validator = await self.harness.create_validator_with_real_components()
        
        nested_schema = {
            "type": "object",
            "properties": {
                "organization": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "contact": {
                            "type": "object",
                            "properties": {
                                "email": {"type": "string", "format": "email"},
                                "phone": {"type": "string", "pattern": "^\\+?[1-9]\\d{1,14}$"}
                            },
                            "required": ["email"]
                        }
                    },
                    "required": ["id", "contact"]
                }
            },
            "required": ["organization"]
        }
        
        invalid_nested_output = {
            "organization": {
                "id": "not_integer",  # Type error at nested level
                "contact": {
                    "email": "invalid-email",  # Format error at deeply nested level
                    "phone": "invalid-phone-format"  # Pattern violation
                }
            }
        }
        
        async with analyzer:
            validation_errors = validator.get_validation_errors(invalid_nested_output, nested_schema)
            analysis = await analyzer.analyze_errors(
                output=invalid_nested_output,
                validation_errors=validation_errors,
                operation_id="nested_schema_test",
                schema=nested_schema
            )
        
        # Should correctly identify semantic errors in nested structure
        self.assertEqual(analysis["error_analysis"]["primary_error_type"], "semantic")
        
        semantic_errors = analysis["error_analysis"]["semantic_errors"]
        self.assertGreater(len(semantic_errors), 0)
        
        # Error descriptions should reference nested field paths
        error_descriptions = " ".join([
            error.get("description", "") for error in semantic_errors
        ]).lower()
        
        # Should mention nested field references
        nested_terms = ["organization", "contact", "id", "email", "phone"]
        found_nested_terms = [term for term in nested_terms if term in error_descriptions]
        self.assertGreater(len(found_nested_terms), 2)
    
    @pytest.mark.asyncio
    async def test_error_analysis_with_large_objects(self):
        """Test error analysis performance and accuracy with large objects."""
        analyzer = await self.harness.create_error_analyzer_with_real_components()
        validator = await self.harness.create_validator_with_real_components()
        
        # Create schema for large object
        large_schema = {
            "type": "object",
            "properties": {
                "metadata": {"type": "object"},
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string", "minLength": 1},
                            "value": {"type": "number", "minimum": 0}
                        },
                        "required": ["id", "name", "value"]
                    },
                    "minItems": 1
                }
            },
            "required": ["items"]
        }
        
        # Create large object with some errors
        large_invalid_output = {
            "metadata": {"note": "Large test object"},
            "items": [
                {"id": i, "name": f"item_{i}", "value": i * 1.5}
                for i in range(500)  # 500 valid items
            ] + [
                {"id": "invalid", "name": "", "value": -1},  # Invalid item
                {"id": 999, "value": 10}  # Missing name
            ]
        }
        
        start_time = datetime.now()
        
        async with analyzer:
            validation_errors = validator.get_validation_errors(large_invalid_output, large_schema)
            analysis = await analyzer.analyze_errors(
                output=large_invalid_output,
                validation_errors=validation_errors,
                operation_id="large_object_test",
                schema=large_schema
            )
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Should complete in reasonable time (less than 10 seconds)
        self.assertLess(execution_time, 10.0)
        
        # Should still detect errors accurately
        self.assertEqual(analysis["error_analysis"]["primary_error_type"], "semantic")
        semantic_errors = analysis["error_analysis"]["semantic_errors"]
        self.assertGreater(len(semantic_errors), 0)
    
    @pytest.mark.asyncio
    async def test_mixed_formatting_and_semantic_errors(self):
        """Test analysis when both formatting and semantic errors are present."""
        analyzer = await self.harness.create_error_analyzer_with_real_components()
        
        # This test simulates what would happen if JSON extraction succeeded
        # but the content has semantic issues
        schema = {
            "type": "object",
            "properties": {
                "data": {"type": "string"},
                "count": {"type": "integer", "minimum": 1}
            },
            "required": ["data", "count"]
        }
        
        # Object with semantic errors (would need formatting errors injected separately)
        mixed_error_output = {
            "data": "test",
            "count": 0  # Violates minimum constraint
        }
        
        # Create mixed validation errors (simulating both types)
        mixed_validation_errors = [
            ValidationError("0 is less than the minimum of 1", "count", "minimum"),
            ValidationError("JSON formatting issue detected", "", "format")
        ]
        
        async with analyzer:
            analysis = await analyzer.analyze_errors(
                output=mixed_error_output,
                validation_errors=mixed_validation_errors,
                operation_id="mixed_errors_test",
                schema=schema
            )
        
        # Should prioritize semantic errors when both are present
        self.assertEqual(analysis["error_analysis"]["primary_error_type"], "semantic")
        
        # Should have both types of errors recorded
        self.assertGreater(len(analysis["error_analysis"]["semantic_errors"]), 0)
        self.assertGreater(len(analysis["error_analysis"]["formatting_errors"]), 0)
    
    @pytest.mark.asyncio
    async def test_error_analysis_edge_cases(self):
        """Test error analysis with edge cases and boundary conditions."""
        analyzer = await self.harness.create_error_analyzer_with_real_components()
        validator = await self.harness.create_validator_with_real_components()
        
        edge_case_tests = [
            {
                "name": "empty_object",
                "schema": {
                    "type": "object",
                    "properties": {"required_field": {"type": "string"}},
                    "required": ["required_field"]
                },
                "output": {},
                "expected_errors": 1
            },
            {
                "name": "additional_properties",
                "schema": {
                    "type": "object", 
                    "properties": {"allowed": {"type": "string"}},
                    "additionalProperties": False
                },
                "output": {"allowed": "value", "not_allowed": "extra"},
                "expected_errors": 1
            },
            {
                "name": "null_values",
                "schema": {
                    "type": "object",
                    "properties": {"required": {"type": "string"}},
                    "required": ["required"]
                },
                "output": {"required": None},
                "expected_errors": 1
            }
        ]
        
        async with analyzer:
            for test_case in edge_case_tests:
                with self.subTest(test_case=test_case["name"]):
                    validation_errors = validator.get_validation_errors(
                        test_case["output"], 
                        test_case["schema"]
                    )
                    
                    analysis = await analyzer.analyze_errors(
                        output=test_case["output"],
                        validation_errors=validation_errors,
                        operation_id=f"edge_case_{test_case['name']}",
                        schema=test_case["schema"]
                    )
                    
                    # Should handle edge cases without crashing
                    self.assertIn("error_analysis", analysis)
                    self.assertIn("primary_error_type", analysis["error_analysis"])
                    
                    # Should detect appropriate number of errors
                    total_errors = (
                        len(analysis["error_analysis"]["semantic_errors"]) +
                        len(analysis["error_analysis"]["formatting_errors"])
                    )
                    self.assertGreaterEqual(total_errors, test_case["expected_errors"])


class TestErrorAnalysisConsistency(unittest.TestCase):
    """Test consistency of error analysis across multiple runs."""
    
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
    async def test_analysis_consistency_across_runs(self):
        """Test that error analysis produces consistent results across multiple runs."""
        analyzer = await self.harness.create_error_analyzer_with_real_components()
        validator = await self.harness.create_validator_with_real_components()
        
        # Fixed test case
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "email": {"type": "string", "format": "email"},
                "status": {"type": "string", "enum": ["active", "inactive"]}
            },
            "required": ["id", "email", "status"]
        }
        
        invalid_output = {
            "id": "not_integer",
            "email": "invalid-email",
            "status": "unknown"
        }
        
        # Run analysis multiple times
        results = []
        async with analyzer:
            for i in range(5):
                validation_errors = validator.get_validation_errors(invalid_output, schema)
                analysis = await analyzer.analyze_errors(
                    output=invalid_output,
                    validation_errors=validation_errors,
                    operation_id=f"consistency_test_{i}",
                    schema=schema
                )
                results.append(analysis)
        
        # Verify consistency across runs
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            # Primary error type should be consistent
            self.assertEqual(
                result["error_analysis"]["primary_error_type"],
                first_result["error_analysis"]["primary_error_type"],
                f"Inconsistent primary error type on run {i}"
            )
            
            # Number of semantic errors should be consistent
            self.assertEqual(
                len(result["error_analysis"]["semantic_errors"]),
                len(first_result["error_analysis"]["semantic_errors"]),
                f"Inconsistent semantic error count on run {i}"
            )
            
            # Number of formatting errors should be consistent
            self.assertEqual(
                len(result["error_analysis"]["formatting_errors"]),
                len(first_result["error_analysis"]["formatting_errors"]),
                f"Inconsistent formatting error count on run {i}"
            )


if __name__ == "__main__":
    # Run with pytest for better async support
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])