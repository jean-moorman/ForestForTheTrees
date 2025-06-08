"""
Comprehensive tests for JSON extraction functionality.

These tests focus on the JSON extraction methods in the Validator class,
testing edge cases and complex scenarios that could occur in real API responses.
"""

import json
import pytest
import unittest
import asyncio
from typing import Dict, Any

# Import system components
from agent_validation import Validator
from resources import EventQueue, StateManager

# Import test infrastructure  
from tests_new.harness.validation_test_harness import ValidationTestHarness


class TestJSONExtraction(unittest.TestCase):
    """Test suite for JSON extraction methods."""
    
    def setUp(self):
        """Set up test environment with real validator."""
        self.harness = ValidationTestHarness()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Create validator for testing JSON extraction
        self.validator = self.loop.run_until_complete(
            self.harness.create_validator_with_real_components()
        )
    
    def tearDown(self):
        """Clean up test environment."""
        if hasattr(self, 'loop'):
            self.loop.close()
            asyncio.set_event_loop(None)
    
    def test_validate_json_with_valid_objects(self):
        """Test validate_json method with valid JSON objects."""
        # Simple object
        simple_json = '{"name": "test", "value": 123}'
        result = self.validator.validate_json(simple_json)
        self.assertEqual(result, simple_json)
        
        # Complex nested object
        complex_json = '''
        {
            "user": {
                "id": 1,
                "profile": {
                    "name": "Test User",
                    "contacts": [
                        {"type": "email", "value": "test@example.com"},
                        {"type": "phone", "value": "+1-555-0123"}
                    ]
                }
            },
            "metadata": {
                "created": "2023-01-01T00:00:00Z",
                "updated": null
            }
        }
        '''
        result = self.validator.validate_json(complex_json)
        self.assertIsNotNone(result)
        
        # Verify it's properly formatted JSON
        parsed = json.loads(result)
        self.assertIn("user", parsed)
        self.assertIn("metadata", parsed)
    
    def test_validate_json_with_invalid_json(self):
        """Test validate_json method with invalid JSON."""
        # Malformed JSON
        invalid_cases = [
            '{"name": "test", "value":}',  # Missing value
            '{"name": "test" "value": 123}',  # Missing comma
            '{"name": "test", "value": 123,}',  # Trailing comma
            '{name: "test"}',  # Unquoted key
            "{'name': 'test'}",  # Single quotes
            '{"name": "test"',  # Missing closing brace
            '',  # Empty string
            'null',  # Not an object
            '["array"]',  # Array instead of object
            '"string"',  # String instead of object
            '123',  # Number instead of object
        ]
        
        for invalid_json in invalid_cases:
            with self.subTest(json_string=invalid_json):
                result = self.validator.validate_json(invalid_json)
                self.assertIsNone(result)
    
    def test_extract_json_from_response_basic_cases(self):
        """Test JSON extraction from responses with basic cases."""
        # JSON with surrounding text
        content1 = '''
        Here's the response you requested:
        {"message": "Hello world", "status": "success"}
        I hope this helps!
        '''
        result1 = self.validator.extract_json_from_response(content1)
        expected1 = '{"message": "Hello world", "status": "success"}'
        self.assertEqual(result1, expected1)
        
        # JSON at the beginning
        content2 = '{"start": true, "value": 42} and some text after'
        result2 = self.validator.extract_json_from_response(content2)
        expected2 = '{"start": true, "value": 42}'
        self.assertEqual(result2, expected2)
        
        # JSON at the end
        content3 = 'Some text before the JSON: {"end": true, "final": "value"}'
        result3 = self.validator.extract_json_from_response(content3)
        expected3 = '{"end": true, "final": "value"}'
        self.assertEqual(result3, expected3)
    
    def test_extract_json_with_nested_braces_in_strings(self):
        """Test JSON extraction with braces inside string values."""
        # Braces in string values
        content1 = '''
        Response: {"message": "The format is {key: value} style", "valid": true}
        '''
        result1 = self.validator.extract_json_from_response(content1)
        expected1 = '{"message": "The format is {key: value} style", "valid": true}'
        self.assertEqual(result1, expected1)
        
        # Multiple braces in strings
        content2 = '''
        {"description": "Use {variable} and {another} in templates", "count": 2}
        '''
        result2 = self.validator.extract_json_from_response(content2)
        expected2 = '{"description": "Use {variable} and {another} in templates", "count": 2}'
        self.assertEqual(result2, expected2)
        
        # Nested object-like strings
        content3 = '''
        {"config": "server: {host: localhost, port: 8080}", "enabled": true}
        '''
        result3 = self.validator.extract_json_from_response(content3)
        expected3 = '{"config": "server: {host: localhost, port: 8080}", "enabled": true}'
        self.assertEqual(result3, expected3)
    
    def test_extract_json_with_escaped_quotes(self):
        """Test handling of escaped quotes in JSON strings."""
        # Simple escaped quotes
        content1 = r'Response: {"quote": "She said \"Hello world\"", "source": "test"}'
        result1 = self.validator.extract_json_from_response(content1)
        
        if result1:
            parsed = json.loads(result1)
            self.assertEqual(parsed["quote"], 'She said "Hello world"')
            self.assertEqual(parsed["source"], "test")
        
        # Multiple escaped quotes
        content2 = r'{"text": "Quote: \"To be or not to be\" - Shakespeare", "nested": "More \"quotes\" here"}'
        result2 = self.validator.extract_json_from_response(content2)
        
        if result2:
            parsed = json.loads(result2)
            self.assertIn('"To be or not to be"', parsed["text"])
            self.assertIn('"quotes"', parsed["nested"])
        
        # Escaped backslashes and quotes
        content3 = r'{"path": "C:\\Users\\\"John Doe\"\\Documents", "valid": true}'
        result3 = self.validator.extract_json_from_response(content3)
        
        if result3:
            parsed = json.loads(result3)
            self.assertIn("C:\\", parsed["path"])
            self.assertIn('"John Doe"', parsed["path"])
    
    def test_extract_json_with_complex_nesting(self):
        """Test JSON extraction with deeply nested structures."""
        complex_json = '''
        {
            "level1": {
                "level2": {
                    "level3": {
                        "array": [
                            {"nested": "object1", "data": {"value": 1}},
                            {"nested": "object2", "data": {"value": 2}}
                        ],
                        "metadata": {
                            "created": "2023-01-01",
                            "config": {
                                "settings": {
                                    "enabled": true,
                                    "options": ["a", "b", "c"]
                                }
                            }
                        }
                    }
                }
            }
        }
        '''
        
        content = f"Here's the complex response: {complex_json} End of response."
        result = self.validator.extract_json_from_response(content)
        
        self.assertIsNotNone(result)
        parsed = json.loads(result)
        
        # Verify deep nesting preserved
        self.assertIn("level1", parsed)
        self.assertIn("level2", parsed["level1"])
        self.assertIn("level3", parsed["level1"]["level2"])
        self.assertIn("array", parsed["level1"]["level2"]["level3"])
        self.assertEqual(len(parsed["level1"]["level2"]["level3"]["array"]), 2)
    
    def test_extract_json_with_unicode_and_special_characters(self):
        """Test JSON extraction with Unicode and special characters."""
        # Unicode characters
        content1 = '''
        {"message": "Hello 世界! 🌍", "emoji": "🚀🎉", "unicode": "café naïve résumé"}
        '''
        result1 = self.validator.extract_json_from_response(content1)
        
        if result1:
            parsed = json.loads(result1)
            self.assertIn("世界", parsed["message"])
            self.assertIn("🌍", parsed["message"])
            self.assertIn("🚀", parsed["emoji"])
            self.assertIn("café", parsed["unicode"])
        
        # Special characters and symbols
        content2 = '''
        {"symbols": "!@#$%^&*()_+-=[]{}|;:,.<>?", "math": "∑∏∂∫√∞", "currency": "€£¥$"}
        '''
        result2 = self.validator.extract_json_from_response(content2)
        
        if result2:
            parsed = json.loads(result2)
            self.assertIn("!@#$%", parsed["symbols"])
            self.assertIn("∑∏∂", parsed["math"])
            self.assertIn("€£¥", parsed["currency"])
    
    def test_extract_json_with_multiple_json_objects(self):
        """Test extraction when multiple JSON objects are present."""
        # Multiple separate JSON objects
        content = '''
        First object: {"first": true, "value": 1}
        Second object: {"second": true, "value": 2}
        Third object: {"third": true, "value": 3}
        '''
        
        # Should extract the first complete JSON object
        result = self.validator.extract_json_from_response(content)
        expected = '{"first": true, "value": 1}'
        self.assertEqual(result, expected)
    
    def test_extract_json_with_markdown_formatting(self):
        """Test JSON extraction from markdown-formatted responses."""
        # JSON in code blocks
        content1 = '''
        Here's the response:
        
        ```json
        {"formatted": true, "language": "json", "block": "code"}
        ```
        
        Additional text here.
        '''
        result1 = self.validator.extract_json_from_response(content1)
        expected1 = '{"formatted": true, "language": "json", "block": "code"}'
        self.assertEqual(result1, expected1)
        
        # JSON with backticks but not in code block
        content2 = '''
        The JSON is: `{"inline": true, "style": "backticks"}` in the text.
        '''
        result2 = self.validator.extract_json_from_response(content2)
        expected2 = '{"inline": true, "style": "backticks"}'
        self.assertEqual(result2, expected2)
    
    def test_extract_json_edge_cases(self):
        """Test edge cases for JSON extraction."""
        # Empty content
        result1 = self.validator.extract_json_from_response("")
        self.assertIsNone(result1)
        
        # None input
        result2 = self.validator.extract_json_from_response(None)
        self.assertIsNone(result2)
        
        # Non-string input
        result3 = self.validator.extract_json_from_response(123)
        self.assertIsNone(result3)
        
        # Only text, no JSON
        result4 = self.validator.extract_json_from_response("This is just text with no JSON")
        self.assertIsNone(result4)
        
        # Partial JSON (incomplete)
        result5 = self.validator.extract_json_from_response('{"incomplete": "json"')
        self.assertIsNone(result5)
        
        # JSON-like but invalid
        result6 = self.validator.extract_json_from_response('{not: "valid", json}')
        self.assertIsNone(result6)
    
    def test_bracket_counting_algorithm(self):
        """Test the bracket counting algorithm specifically."""
        # Test the internal bracket counting method
        
        # Balanced braces
        content1 = '{"a": {"b": {"c": "value"}}}'
        result1 = self.validator._extract_json_with_bracket_counting(content1)
        self.assertEqual(result1, content1)
        
        # Unbalanced braces (extra opening)
        content2 = '{"a": {"b": {"c": "value"}'
        result2 = self.validator._extract_json_with_bracket_counting(content2)
        self.assertIsNone(result2)
        
        # Extra closing brace
        content3 = '{"a": "value"}} extra'
        result3 = self.validator._extract_json_with_bracket_counting(content3)
        expected3 = '{"a": "value"}'
        self.assertEqual(result3, expected3)
        
        # No opening brace
        content4 = 'no json here'
        result4 = self.validator._extract_json_with_bracket_counting(content4)
        self.assertIsNone(result4)
        
        # Braces only in strings (should be ignored for counting)
        content5 = '{"text": "this has {braces} in string", "valid": true}'
        result5 = self.validator._extract_json_with_bracket_counting(content5)
        self.assertEqual(result5, content5)
    
    def test_escaped_characters_in_bracket_counting(self):
        """Test that escaped characters are handled correctly in bracket counting."""
        # Escaped quotes should not affect string boundary detection
        content1 = r'{"text": "She said \"Hello {world}\" to me", "valid": true}'
        result1 = self.validator._extract_json_with_bracket_counting(content1)
        self.assertEqual(result1, content1)
        
        # Escaped backslashes
        content2 = r'{"path": "C:\\Program Files\\{App}", "valid": true}'
        result2 = self.validator._extract_json_with_bracket_counting(content2)
        self.assertEqual(result2, content2)
        
        # Multiple escaped characters
        content3 = r'{"regex": "\\{\\d+\\}", "example": "Match \\\"quoted\\\" text"}'
        result3 = self.validator._extract_json_with_bracket_counting(content3)
        self.assertEqual(result3, content3)
    
    def test_performance_with_large_content(self):
        """Test JSON extraction performance with large content."""
        import time
        
        # Create large content with JSON at the end
        large_text = "This is a lot of text. " * 10000
        json_part = '{"found": true, "position": "end"}'
        large_content = large_text + json_part
        
        start_time = time.time()
        result = self.validator.extract_json_from_response(large_content)
        end_time = time.time()
        
        # Should complete quickly (less than 1 second)
        execution_time = end_time - start_time
        self.assertLess(execution_time, 1.0)
        
        # Should find the JSON
        self.assertEqual(result, json_part)
    
    def test_extract_json_with_string_escaping_patterns(self):
        """Test JSON extraction with various string escaping patterns."""
        # Test string that looks like escaped JSON
        content1 = r'The JSON is: "{\"key\": \"value\", \"number\": 42}"'
        result1 = self.validator.extract_json_from_response(content1)
        
        # The escaped JSON string should be detected and unescaped
        if result1:
            parsed = json.loads(result1)
            self.assertIn("key", parsed)
            self.assertEqual(parsed["key"], "value")
            self.assertEqual(parsed["number"], 42)
    
    def test_malformed_json_recovery(self):
        """Test handling of common JSON malformation patterns."""
        # Common API response issues that might be recoverable
        test_cases = [
            # Extra comma
            ('{"valid": true,}', None),  # Should not extract invalid JSON
            
            # Missing quotes on keys
            ('{valid: true}', None),  # Should not extract invalid JSON
            
            # Single quotes instead of double
            ("{'valid': true}", None),  # Should not extract invalid JSON
            
            # Trailing text that might confuse extraction
            ('{"valid": true} and some trailing text', '{"valid": true}'),
        ]
        
        for content, expected in test_cases:
            with self.subTest(content=content):
                result = self.validator.extract_json_from_response(content)
                self.assertEqual(result, expected)


class TestJSONExtractionIntegration(unittest.TestCase):
    """Integration tests for JSON extraction within the validation pipeline."""
    
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
    async def test_json_extraction_in_validation_pipeline(self):
        """Test JSON extraction as part of the complete validation pipeline."""
        validator = await self.harness.create_validator_with_real_components()
        
        # Test with string output that contains JSON
        string_output = '''
        Here's the response:
        {"name": "Test User", "email": "test@example.com", "status": "active"}
        That should work!
        '''
        
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string", "format": "email"},
                "status": {"type": "string", "enum": ["active", "inactive"]}
            },
            "required": ["name", "email", "status"]
        }
        
        async with validator:
            success, result, analysis = await validator.validate_output(
                output=string_output,
                schema=schema,
                operation_id="test_extraction_integration"
            )
        
        # Should successfully extract and validate JSON
        self.assertTrue(success)
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "Test User")
        self.assertEqual(result["email"], "test@example.com")
        self.assertEqual(result["status"], "active")
    
    @pytest.mark.asyncio
    async def test_failed_json_extraction_handling(self):
        """Test handling when JSON extraction fails."""
        validator = await self.harness.create_validator_with_real_components()
        
        # Content with no valid JSON
        invalid_output = "This is just text with no JSON at all!"
        
        schema = {
            "type": "object",
            "properties": {"test": {"type": "string"}},
            "required": ["test"]
        }
        
        async with validator:
            success, result, analysis = await validator.validate_output(
                output=invalid_output,
                schema=schema,
                operation_id="test_failed_extraction"
            )
        
        # Should fail with appropriate error
        self.assertFalse(success)
        self.assertIsNone(result)
        self.assertIn("error_analysis", analysis)
        self.assertEqual(analysis["error_analysis"]["primary_error_type"], "formatting")
        
        # Should have formatting error about JSON extraction
        formatting_errors = analysis["error_analysis"]["formatting_errors"]
        self.assertGreater(len(formatting_errors), 0)
        
        error_descriptions = [error.get("description", "") for error in formatting_errors]
        error_text = " ".join(error_descriptions).lower()
        self.assertIn("json", error_text)


if __name__ == "__main__":
    # Run with pytest for better async support
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])