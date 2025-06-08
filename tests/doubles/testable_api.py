"""
TestableAnthropicAPI - A test double that implements realistic API behavior
without external dependencies.

This replaces mocks with controlled, deterministic responses that still
exercise the actual validation logic paths.
"""

import json
import random
import re
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class APICall:
    """Record of an API call for test verification."""
    conversation: str
    system_prompt_info: Tuple[str, str]
    schema: Dict[str, Any]
    current_phase: Optional[str]
    max_tokens: Optional[int]
    timestamp: datetime


class TestableAnthropicAPI:
    """
    Test double that implements real API interface with controllable responses.
    
    Instead of mocking with predictable strings, this generates realistic
    responses based on conversation patterns and schemas, allowing us to
    test actual validation logic.
    """
    
    def __init__(self, response_mode: str = "adaptive"):
        """
        Initialize the testable API.
        
        Args:
            response_mode: Controls response generation strategy
                - "adaptive": Generate responses based on conversation analysis
                - "schema_compliant": Always generate valid responses
                - "validation_testing": Generate responses with specific error types
        """
        self.response_mode = response_mode
        self.call_history: List[APICall] = []
        self.custom_responses: Dict[str, str] = {}
        self.error_injection_rules: List[Dict[str, Any]] = []
        self.call_count = 0
        
    def set_custom_response(self, conversation_pattern: str, response: str):
        """Set a custom response for conversations matching a pattern."""
        self.custom_responses[conversation_pattern] = response
        
    def add_error_injection_rule(self, rule: Dict[str, Any]):
        """
        Add a rule for injecting specific validation errors.
        
        Rule format:
        {
            "trigger_pattern": "regex pattern to match conversation",
            "error_type": "missing_field|type_error|enum_violation|format_error",
            "target_field": "field_path",
            "probability": 0.8  # Chance of triggering
        }
        """
        self.error_injection_rules.append(rule)
        
    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass
        
    async def call(
        self,
        conversation: str,
        system_prompt_info: Tuple[str, str],
        schema: Dict[str, Any],
        current_phase: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a realistic API response based on the conversation and schema.
        
        This method analyzes the conversation to understand what type of response
        is being requested and generates appropriate JSON that may or may not
        pass validation, depending on the test scenario.
        """
        self.call_count += 1
        
        # Record the API call
        call_record = APICall(
            conversation=conversation,
            system_prompt_info=system_prompt_info,
            schema=schema,
            current_phase=current_phase,
            max_tokens=max_tokens,
            timestamp=datetime.now()
        )
        self.call_history.append(call_record)
        
        # Check for custom responses first
        for pattern, response in self.custom_responses.items():
            if pattern.lower() in conversation.lower():
                return response
        
        # Apply error injection rules
        for rule in self.error_injection_rules:
            if self._should_trigger_error(rule, conversation):
                return self._generate_error_response(rule, schema)
        
        # Generate response based on mode
        if self.response_mode == "adaptive":
            return self._generate_adaptive_response(conversation, schema)
        elif self.response_mode == "schema_compliant":
            return self._generate_schema_compliant_response(schema)
        elif self.response_mode == "validation_testing":
            return self._generate_validation_testing_response(conversation, schema)
        else:
            return self._generate_default_response(schema)
    
    def _should_trigger_error(self, rule: Dict[str, Any], conversation: str) -> bool:
        """Check if an error injection rule should trigger."""
        pattern = rule.get("trigger_pattern", "")
        probability = rule.get("probability", 0.0)
        
        # Check pattern match
        if pattern and not re.search(pattern, conversation, re.IGNORECASE):
            return False
        
        # Check probability
        return random.random() < probability
    
    def _generate_error_response(self, rule: Dict[str, Any], schema: Dict[str, Any]) -> str:
        """Generate a response that will trigger the specified error type."""
        error_type = rule.get("error_type", "missing_field")
        target_field = rule.get("target_field", "")
        
        if error_type == "json_format_error":
            return "{ invalid json response with syntax errors }"
        elif error_type == "missing_field":
            return self._generate_response_missing_field(schema, target_field)
        elif error_type == "type_error":
            return self._generate_response_with_type_error(schema, target_field)
        elif error_type == "enum_violation":
            return self._generate_response_with_enum_violation(schema, target_field)
        elif error_type == "format_error":
            return self._generate_response_with_format_error(schema, target_field)
        else:
            return self._generate_basic_response(schema)
    
    def _generate_adaptive_response(self, conversation: str, schema: Dict[str, Any]) -> str:
        """Generate response adapted to conversation content and schema."""
        # Analyze conversation for key concepts
        conversation_lower = conversation.lower()
        
        # Generate base response from schema
        response = self._generate_basic_response(schema)
        
        # Adapt based on conversation content
        if "user" in conversation_lower and isinstance(response, dict):
            if "user" in response:
                response["user"]["name"] = "John Doe"
                if "email" in response["user"]:
                    response["user"]["email"] = "john.doe@example.com"
        
        if "project" in conversation_lower and isinstance(response, dict):
            if "project" in response:
                response["project"]["name"] = "Sample Project"
                if "id" in response["project"]:
                    response["project"]["id"] = "PROJ-1234"
        
        return json.dumps(response, indent=2)
    
    def _generate_schema_compliant_response(self, schema: Dict[str, Any]) -> str:
        """Generate a response that fully complies with the schema."""
        response = self._generate_basic_response(schema)
        return json.dumps(response, indent=2)
    
    def _generate_validation_testing_response(self, conversation: str, schema: Dict[str, Any]) -> str:
        """Generate responses designed for validation testing scenarios."""
        # On first few calls, generate potentially invalid responses
        # On later calls, generate valid responses to test correction workflows
        
        if self.call_count <= 2:
            # Generate response with potential issues
            if self.call_count == 1:
                return self._generate_response_with_minor_issues(schema)
            else:
                return self._generate_response_with_moderate_issues(schema)
        else:
            # Generate valid response for correction workflow
            return self._generate_schema_compliant_response(schema)
    
    def _generate_basic_response(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a basic response structure from schema."""
        if not schema or "type" not in schema:
            return {"message": "Generated response"}
        
        if schema["type"] == "object":
            return self._generate_object_from_schema(schema)
        elif schema["type"] == "array":
            return [self._generate_item_from_schema(schema.get("items", {}))]
        else:
            return {"value": self._generate_value_from_schema(schema)}
    
    def _generate_object_from_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate object matching schema structure."""
        result = {}
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        # Add required fields
        for field in required:
            if field in properties:
                result[field] = self._generate_value_from_schema(properties[field])
        
        # Add some optional fields
        for field, field_schema in properties.items():
            if field not in result and random.random() < 0.7:
                result[field] = self._generate_value_from_schema(field_schema)
        
        return result
    
    def _generate_value_from_schema(self, schema: Dict[str, Any]) -> Any:
        """Generate a value matching the schema type."""
        schema_type = schema.get("type", "string")
        
        if schema_type == "string":
            if "enum" in schema:
                return random.choice(schema["enum"])
            elif "format" in schema and schema["format"] == "email":
                return "test@example.com"
            else:
                return "test_string"
        elif schema_type == "integer":
            minimum = schema.get("minimum", 0)
            maximum = schema.get("maximum", 100)
            return random.randint(minimum, maximum)
        elif schema_type == "number":
            minimum = schema.get("minimum", 0.0)
            maximum = schema.get("maximum", 100.0)
            return round(random.uniform(minimum, maximum), 2)
        elif schema_type == "boolean":
            return random.choice([True, False])
        elif schema_type == "array":
            items_schema = schema.get("items", {"type": "string"})
            return [self._generate_value_from_schema(items_schema)]
        elif schema_type == "object":
            return self._generate_object_from_schema(schema)
        else:
            return "unknown_type"
    
    def _generate_response_missing_field(self, schema: Dict[str, Any], target_field: str) -> str:
        """Generate response missing a specific field."""
        response = self._generate_basic_response(schema)
        
        # Remove the target field if present
        if isinstance(response, dict) and "." in target_field:
            # Handle nested field paths like "user.email"
            path_parts = target_field.split(".")
            current = response
            for part in path_parts[:-1]:
                if part in current and isinstance(current[part], dict):
                    current = current[part]
                else:
                    break
            else:
                if path_parts[-1] in current:
                    del current[path_parts[-1]]
        elif isinstance(response, dict) and target_field in response:
            del response[target_field]
        
        return json.dumps(response, indent=2)
    
    def _generate_response_with_type_error(self, schema: Dict[str, Any], target_field: str) -> str:
        """Generate response with type error in specific field."""
        response = self._generate_basic_response(schema)
        
        # Introduce type error
        if isinstance(response, dict) and target_field in response:
            if isinstance(response[target_field], int):
                response[target_field] = "not_an_integer"
            elif isinstance(response[target_field], str):
                response[target_field] = 12345
        
        return json.dumps(response, indent=2)
    
    def _generate_response_with_enum_violation(self, schema: Dict[str, Any], target_field: str) -> str:
        """Generate response with enum constraint violation."""
        response = self._generate_basic_response(schema)
        
        # Introduce enum violation
        if isinstance(response, dict) and target_field in response:
            response[target_field] = "invalid_enum_value"
        
        return json.dumps(response, indent=2)
    
    def _generate_response_with_format_error(self, schema: Dict[str, Any], target_field: str) -> str:
        """Generate response with format constraint violation."""
        response = self._generate_basic_response(schema)
        
        # Introduce format error
        if isinstance(response, dict) and "." in target_field:
            path_parts = target_field.split(".")
            current = response
            for part in path_parts[:-1]:
                if part in current and isinstance(current[part], dict):
                    current = current[part]
                else:
                    break
            else:
                if path_parts[-1] in current:
                    current[path_parts[-1]] = "INVALID-FORMAT"
        elif isinstance(response, dict) and target_field in response:
            response[target_field] = "INVALID-FORMAT"
        
        return json.dumps(response, indent=2)
    
    def _generate_response_with_minor_issues(self, schema: Dict[str, Any]) -> str:
        """Generate response with minor validation issues."""
        response = self._generate_basic_response(schema)
        
        # Add minor formatting issues but keep structure valid
        return json.dumps(response, indent=2).replace("    ", "  ")  # Different indentation
    
    def _generate_response_with_moderate_issues(self, schema: Dict[str, Any]) -> str:
        """Generate response with moderate validation issues."""
        response = self._generate_basic_response(schema)
        
        # Introduce moderate issues like missing required fields
        if isinstance(response, dict):
            required = schema.get("required", [])
            if required and len(required) > 1:
                # Remove one required field
                field_to_remove = required[0]
                if field_to_remove in response:
                    del response[field_to_remove]
        
        return json.dumps(response, indent=2)
    
    def _generate_item_from_schema(self, schema: Dict[str, Any]) -> Any:
        """Generate single item from schema."""
        return self._generate_value_from_schema(schema)
    
    def _generate_default_response(self, schema: Dict[str, Any]) -> str:
        """Generate default response when mode is unknown."""
        return json.dumps({"message": "default response", "call_count": self.call_count})


class RealMetricsCollector:
    """Metrics collector that actually records metrics for test verification."""
    
    def __init__(self):
        """Initialize the metrics collector."""
        self.recorded_metrics: List[Dict[str, Any]] = []
    
    def reset(self):
        """Reset recorded metrics."""
        self.recorded_metrics.clear()
    
    async def record_metric(self, name: str, value: float, metadata: Optional[Dict[str, Any]] = None):
        """Record a metric."""
        metric_record = {
            "name": name,
            "value": value,
            "metadata": metadata or {},
            "timestamp": datetime.now()
        }
        self.recorded_metrics.append(metric_record)
    
    def get_recorded_metrics(self) -> List[Dict[str, Any]]:
        """Get all recorded metrics."""
        return self.recorded_metrics.copy()
    
    def get_metrics_by_name(self, name: str) -> List[Dict[str, Any]]:
        """Get metrics by name."""
        return [m for m in self.recorded_metrics if m["name"] == name]