from datetime import datetime
import logging
import os
import re
from typing import Dict, Any, List, Optional, Tuple, Protocol, Callable, Awaitable
import json
import jsonschema
from jsonschema import validate, ValidationError as JsonSchemaValidationError
from pathlib import Path
import asyncio
import math
from api import AnthropicAPI

from resources import EventQueue, StateManager, AgentContextManager, CacheManager, MetricsManager, ResourceEventTypes, ResourceType

class CorrectionRequest:
    """Data class representing a correction request."""
    def __init__(
        self,
        original_output: Dict[str, Any],
        feedback: str,
        schema: Dict[str, Any],
        validation_errors: Dict[str, Any],
        attempt_number: int,
        operation_id: Optional[str] = None
    ):
        self.original_output = original_output
        self.feedback = feedback
        self.schema = schema
        self.validation_errors = validation_errors
        self.attempt_number = attempt_number
        self.operation_id = operation_id

class CorrectionResult:
    """Data class representing the result of a correction attempt."""
    def __init__(
        self,
        corrected_output: Optional[Dict[str, Any]],
        success: bool,
        error_message: Optional[str] = None
    ):
        self.corrected_output = corrected_output
        self.success = success
        self.error_message = error_message


    
class ValidationException(Exception):
    """Custom exception for validation errors."""
    def __init__(self, message: str, details: Any = None):
        super().__init__(message)
        self.details = details

class ValidationError:
    """Class to structure validation error information."""
    def __init__(self, message: str, path: str = "", schema_path: str = ""):
        self.message = message
        self.path = path
        self.schema_path = schema_path

    def __str__(self):
        return f"ValidationError: {self.message} (path: {self.path}, schema_path: {self.schema_path})"
        
    def to_dict(self) -> Dict[str, str]:
        """Convert error to dictionary format."""
        return {
            "message": self.message,
            "path": self.path,
            "schema_path": self.schema_path
        }

ERROR_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "error_analysis": {
            "type": "object",
            "required": ["formatting_errors", "semantic_errors"],
            "properties": {
                "formatting_errors": {"type": "array"},
                "semantic_errors": {"type": "array"}
            }
        }
    }
}

class ValidationErrorAnalyzer:
    def __init__(
        self,
        validator: 'Validator',
        event_queue: EventQueue,
        state_manager: StateManager,
    ):
        self.validator = validator
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._context_manager = AgentContextManager(event_queue)
        self._cache_manager = CacheManager(event_queue)
        self._metrics_manager = MetricsManager(event_queue)
        self._error_analysis_api = None
        self._formatting_correction_api = None
        self._semantic_handler = None
        self._active_analyses: Dict[str, Dict[str, Any]] = {}
        self._model: str = "claude-3-7-sonnet-20250219"

    async def analyze_errors(
        self,
        output: Dict[str, Any],
        validation_errors: List[ValidationError],
        operation_id: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        analysis_id = f"error_analysis:{operation_id or datetime.now().isoformat()}"
        
        try:
            # Record analysis start in state manager
            await self._state_manager.set_state(
                analysis_id,
                {
                    "status": "in_progress",
                    "start_time": datetime.now().isoformat(),
                    "output": output,
                    "errors": [e.to_dict() for e in validation_errors]
                },
                resource_type=ResourceType.AGENT
            )
            
            analysis_result = await self._perform_error_analysis(output, validation_errors)
            
            # Enhanced semantic error detection
            if analysis_result["error_analysis"]["primary_error_type"] == "semantic" and schema:
                semantic_details = await self._analyze_semantic_errors(
                    output,
                    validation_errors,
                    schema
                )
                analysis_result["error_analysis"]["semantic_details"] = semantic_details

            # Update context if available
            if operation_id:
                context = await self._context_manager.get_context(f"agent_context:{operation_id}")
                if context:
                    validation_history = context.validation_history or []
                    validation_history.append({
                        "timestamp": datetime.now().isoformat(),
                        "analysis": analysis_result
                    })
                    await self._context_manager.store_context(
                        f"agent_context:{operation_id}",
                        context
                    )
            
            # Record analysis completion
            await self._state_manager.set_state(
                analysis_id,
                {
                    "status": "complete",
                    "result": analysis_result,
                    "completion_time": datetime.now().isoformat()
                },
                resource_type=ResourceType.AGENT
            )
            
            # Record metrics
            await self._metrics_manager.record_metric(
                "validation:analysis:completion",
                1.0,
                metadata={
                    "analysis_id": analysis_id,
                    "operation_id": operation_id,
                    "error_types": analysis_result["error_analysis"]["primary_error_type"]
                }
            )
            
            return analysis_result
            
        except Exception as e:
            error_data = {
                "error": str(e),
                "analysis_id": analysis_id,
                "operation_id": operation_id
            }
            
            await self._event_queue.emit(
                ResourceEventTypes.ERROR_OCCURRED.value,
                error_data
            )
            
            await self._state_manager.set_state(
                analysis_id,
                {
                    "status": "error",
                    "error": str(e),
                    "completion_time": datetime.now().isoformat()
                },
                resource_type=ResourceType.AGENT
            )
            
            return self._create_error_response("analysis_error", str(e))
    
    async def _analyze_semantic_errors(
        self,
        output: Dict[str, Any],
        validation_errors: List[ValidationError],
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform detailed analysis of semantic errors."""
        semantic_details = {
            "constraints_violated": [],
            "suggested_fixes": [],
            "field_requirements": {}
        }
        
        for error in validation_errors:
            # Extract field schema
            field_schema = self._semantic_handler._get_field_schema(schema, error.path)
            if not field_schema:
                continue
                
            # Analyze constraint violations
            constraints = self.validator._analyze_constraints(field_schema, error)
            if constraints:
                semantic_details["constraints_violated"].append(constraints)
                
            # Get field requirements
            requirements = self._semantic_handler._get_field_requirements(field_schema)
            if requirements:
                semantic_details["field_requirements"][error.path] = requirements
                
            # Generate suggested fix
            fix = self.validator._generate_fix_suggestion(error, field_schema)
            if fix:
                semantic_details["suggested_fixes"].append(fix)
        
        return semantic_details

    async def _perform_error_analysis(self, output: Dict[str, Any],
                                    validation_errors: List[ValidationError]) -> Dict[str, Any]:
        """Core error analysis logic."""
        try:
            conversation = self._build_analysis_prompt(output, validation_errors)
            
            # Use already initialized API
            if not self._error_analysis_api:
                raise ValueError("API not initialized. Did you use 'async with'?")
            logging.info("Calling error analysis api")
            response = await self._error_analysis_api.call(
                conversation=conversation,
                system_prompt_info=("FFTT_system_prompts/validation/error_analysis_agent", "error_analysis_prompt"),
                schema=ERROR_ANALYSIS_SCHEMA,
                current_phase="error_analysis",
                max_tokens=8000
            )
            logging.info(f"Error Analysis Agent response: {response}")
            parsed = json.loads(response)
            
            # Validate structure
            jsonschema.validate(instance=parsed, schema=ERROR_ANALYSIS_SCHEMA)
            
            # Add metadata
            parsed["error_analysis"]["analysis_timestamp"] = datetime.now().isoformat()
            
            return parsed
    
        except json.JSONDecodeError as e:
            return self._create_error_response("json_parse_error", str(e))
        except JsonSchemaValidationError as e:
            return self._create_error_response("schema_validation_error", str(e))
        except ValueError as e:
            return self._create_error_response("initialization_error", str(e))
        except Exception as e:
            return self._create_error_response("unknown_error during error_analysis_response_processing", str(e))

    def _build_analysis_prompt(
        self,
        output: Dict[str, Any],
        validation_errors: List[ValidationError]
    ) -> Dict[str, Any]:
        """Use error analysis API to categorize errors and determine correction strategy."""
        try:
            
            conversation = f"""Analyze the following validation errors and categorize them as either formatting or semantic errors.

Input Context:
Original Output: {json.dumps(output, indent=2)}
Validation Errors: {json.dumps([error.to_dict() for error in validation_errors], indent=2)}

IMPORTANT: Your response MUST be a JSON object with EXACTLY this structure:
{{
    "error_analysis": {{
        "formatting_errors": [...],
        "semantic_errors": [...],
        "primary_error_type": "formatting|semantic"
    }}
}}

The primary_error_type field is REQUIRED and MUST be either "formatting" or "semantic".
Do not include any explanation or additional text - only return the JSON object."""
            return conversation

        except Exception as e:
            print(f"Unexpected error in error analysis prompt construction: {str(e)}")
            return self._create_error_response("error analysis prompt construction error", str(e))

    def _create_error_response(self, error_type: str, description: str) -> Dict[str, Any]:
        """Helper method to create consistent error responses."""
        error_response = {
            "error_analysis": {
                "formatting_errors": [],
                "semantic_errors": [{
                    "field": "response",
                    "error_type": error_type,
                    "description": description,
                    "required_clarification": "Need valid JSON response"
                }]
            }
        }
        # Add primary_error_type systematically
        error_response["error_analysis"]["primary_error_type"] = self.determine_primary_error_type(error_response)
        return error_response
    
    def determine_primary_error_type(self, error_analysis: Dict[str, Any]) -> str:
        """Determine primary error type based on presence of errors."""
        if error_analysis["error_analysis"]["semantic_errors"]:
            return "semantic"
        elif error_analysis["error_analysis"]["formatting_errors"]:
            return "formatting"
        return "formatting"  # Default case when both lists are empty

    def validate_formatting(self, formatted_json: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate that JSON meets formatting requirements."""
        issues = []
        
        # Check for undefined or NaN values
        def check_values(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if v is None:
                        issues.append(f"Undefined value found for key {k}")
                    if isinstance(v, float) and math.isnan(v):
                        issues.append(f"NaN value found for key {k}")
                    check_values(v)
            elif isinstance(obj, list):
                for item in obj:
                    check_values(item)
        
        check_values(formatted_json)
        return len(issues) == 0, issues

    async def attempt_formatting_correction(
        self,
        output: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Attempt to correct formatting issues using the formatting correction API."""
        try:
            conversation = f"""Following the strict formatting rules:
    - Use 2 spaces for indentation
    - Use double quotes for strings
    - No undefined or NaN values allowed
    - Arrays and objects with multiple items must be on multiple lines
    - Never encode JSON as a string within JSON
    
    Please correct the following JSON while preserving ALL semantic meaning and data types:
    
    {json.dumps(output, indent=2)}
    
    Return ONLY the corrected JSON object with NO additional text or markup."""

            print("Calling formatting correction API...")
            response = await self._formatting_correction_api.call(
                conversation=conversation,
                system_prompt_info=("FFTT_system_prompts/validation/formatting_correction_agent", "formatting_correction_prompt"),
                schema=self.validator.current_schema,
                current_phase="formatting_correction",
                max_tokens=8000
            )
            print(f"Formatting API Response received: {response}")

            if not response:
                print("Error: Formatting API response is empty")
                return None

            try:
                corrected = json.loads(response)
                
                # Validate formatting requirements
                is_valid, issues = self.validate_formatting(corrected)
                if not is_valid:
                    print(f"Formatting validation failed: {issues}")
                    return None
                    
                return corrected
                
            except json.JSONDecodeError as e:
                print(f"Invalid JSON in formatting correction response: {str(e)}")
                return None
                
        except Exception as e:
            print(f"Formatting correction error: {str(e)}")
            return None

    async def __aenter__(self):
        """Async context manager entry."""
        # Initialize API client
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        # Initialize APIs using their own context managers
        self._error_analysis_api = await AnthropicAPI(model=self._model, key=anthropic_api_key).__aenter__()
        self._formatting_correction_api = await AnthropicAPI(model=self._model, key=anthropic_api_key).__aenter__()
        self._semantic_handler = await SemanticErrorHandler(self.validator, self._event_queue, self._state_manager, self.validator._correction_handler).__aenter__()

        if not self._error_analysis_api or not self._formatting_correction_api:
            raise ValueError("failed to initialize validation apis")
        if not self._semantic_handler:
            raise ValueError("failed to initialize semantic error handler")
        
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup API instances."""
        if self._error_analysis_api:
            await self._error_analysis_api.__aexit__(exc_type, exc_val, exc_tb)
        if self._formatting_correction_api:
            await self._formatting_correction_api.__aexit__(exc_type, exc_val, exc_tb)
        if self._semantic_handler:
            await self._semantic_handler.__aexit__(exc_type, exc_val, exc_tb)
  
class SemanticErrorHandler:
    """Handles semantic validation errors by working with the original agent to get valid output."""
    
    def __init__(
        self,
        validator: 'Validator',
        event_queue: EventQueue,
        state_manager: StateManager,
        correction_handler, #this will be an Agent but avoiding type reference for dependency reasons
    ):
        self.validator = validator
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._context_manager = AgentContextManager(event_queue)
        self._metrics_manager = MetricsManager(event_queue)
        self._correction_handler = correction_handler
        self._initialized = False

    async def handle_semantic_errors(
        self,
        original_output: Dict[str, Any],
        validation_errors: List[ValidationError],
        error_analysis: Dict[str, Any],
        schema: Dict[str, Any],
        operation_id: Optional[str] = None,
        max_retries: int = 3
    ) -> Tuple[bool, Optional[Dict[str, Any]], Dict[str, Any]]:
        """
        Handle semantic validation errors by providing feedback to the original agent.
        
        Args:
            original_output: The output that failed validation
            validation_errors: List of validation errors
            error_analysis: Analysis of the errors
            schema: The validation schema
            operation_id: Optional operation identifier
            max_retries: Maximum number of retry attempts
            
        Returns:
            Tuple of (success boolean, corrected output if successful, error analysis)
        """
        correction_id = f"semantic_correction:{operation_id or datetime.now().isoformat()}"
        
        try:
            # Record correction attempt start
            await self._state_manager.set_state(
                correction_id,
                {
                    "status": "in_progress",
                    "start_time": datetime.now().isoformat(),
                    "original_output": original_output,
                    "errors": [e.to_dict() for e in validation_errors],
                    "attempt": 1,
                    "max_retries": max_retries
                },
                resource_type=ResourceType.AGENT
            )

            logging.info("Starting semantic error correction process")
            for attempt in range(max_retries):
                logging.info(f"Semantic correction attempt {attempt + 1}/{max_retries}")
                # Generate feedback for the agent
                feedback = self._generate_semantic_feedback(
                    original_output,
                    validation_errors,
                    error_analysis,
                    schema,
                    attempt + 1
                )
                logging.debug(f"Generated semantic feedback: {feedback}")
                # Create correction request
                correction_request = CorrectionRequest(
                    original_output=original_output,
                    feedback=feedback,
                    schema=schema,
                    validation_errors=error_analysis,
                    attempt_number=attempt + 1,
                    operation_id=operation_id
                )
                
                logging.info("Calling semantic correction handler")
                # Get corrected response using correction handler
                result = await self._correction_handler.handle_correction_request(correction_request)
                logging.info(f"Semantic correction handler returned: {result}")
                if not result.success or not result.corrected_output:
                    logging.warning(f"Semantic correction attempt {attempt + 1} failed: {result.error_message}")
                    continue
                    
                # Validate the corrected output
                success, validated_output, new_analysis = await self.validator.validate_output(
                    result.corrected_output,
                    schema,
                    operation_id
                )
                
                if success:
                    logging.info("Semantic correction successful!")
                    # Record successful correction
                    await self._state_manager.set_state(
                        correction_id,
                        {
                            "status": "complete",
                            "attempts": attempt + 1,
                            "final_output": validated_output,
                            "completion_time": datetime.now().isoformat()
                        },
                        resource_type=ResourceType.AGENT
                    )
                    
                    # Record metrics
                    await self._metrics_manager.record_metric(
                        "semantic_correction:success",
                        1.0,
                        metadata={
                            "operation_id": operation_id,
                            "attempts": attempt + 1
                        }
                    )
                    
                    return True, validated_output, new_analysis
                
                logging.warning(f"Validation of corrected output failed on attempt {attempt + 1}")
                # Update state for retry
                await self._state_manager.set_state(
                    correction_id,
                    {
                        "status": "retrying",
                        "attempt": attempt + 2,
                        "last_attempt_time": datetime.now().isoformat()
                    },
                    resource_type=ResourceType.AGENT
                )

            # If we get here, we've exhausted retries
            logging.error("Semantic correction failed: max retries exceeded")
            await self._state_manager.set_state(
                correction_id,
                {
                    "status": "failed",
                    "reason": "max_retries_exceeded",
                    "completion_time": datetime.now().isoformat()
                },
                resource_type=ResourceType.AGENT
            )
            
            await self._metrics_manager.record_metric(
                "semantic_correction:failure",
                1.0,
                metadata={
                    "operation_id": operation_id,
                    "reason": "max_retries_exceeded"
                }
            )
            
            return False, None, error_analysis
            
        except Exception as e:
            error_details = {
                "error": str(e),
                "correction_id": correction_id,
                "operation_id": operation_id
            }
            
            await self._event_queue.emit(
                ResourceEventTypes.ERROR_OCCURRED.value,
                error_details
            )
            
            await self._state_manager.set_state(
                correction_id,
                {
                    "status": "error",
                    "error": str(e),
                    "completion_time": datetime.now().isoformat()
                },
                resource_type=ResourceType.AGENT
            )
            
            return False, None, error_analysis

    def _generate_semantic_feedback(
        self,
        original_output: Dict[str, Any],
        validation_errors: List[ValidationError],
        error_analysis: Dict[str, Any],
        schema: Dict[str, Any],
        attempt: int
    ) -> str:
        """Generate clear feedback about semantic errors for the agent."""
        semantic_errors = error_analysis["error_analysis"]["semantic_errors"]
        
        feedback_parts = [
            "Your previous response contained semantic validation errors that need to be corrected:"
        ]
        
        for error in semantic_errors:
            field = error.get("field", "unknown")
            description = error.get("description", "unknown error")
            
            # Get schema requirements for this field
            field_schema = self._get_field_schema(schema, field)
            requirements = self._get_field_requirements(field_schema)
            
            feedback_parts.append(f"\nField '{field}':")
            feedback_parts.append(f"- Error: {description}")
            feedback_parts.append(f"- Requirements: {requirements}")
            
        if attempt > 1:
            feedback_parts.append(f"\nThis is attempt {attempt}. Please carefully review all requirements.")
            
        feedback_parts.append("\nPlease provide a new response that meets all requirements.")
        
        return "\n".join(feedback_parts)

    def _get_field_schema(self, schema: Dict[str, Any], field_path: str) -> Optional[Dict[str, Any]]:
        """Get the schema for a specific field using its path."""
        if not field_path or field_path == "root":
            return schema
            
        parts = field_path.split(" -> ")
        current = schema
        
        for part in parts:
            if "properties" in current and part in current["properties"]:
                current = current["properties"][part]
            elif "items" in current:
                current = current["items"]
            else:
                return None
                
        return current

    def _get_field_requirements(self, field_schema: Optional[Dict[str, Any]]) -> str:
        """Extract human-readable requirements from a field's schema."""
        if not field_schema:
            return "Schema requirements not found"
            
        requirements = []
        
        if "type" in field_schema:
            requirements.append(f"Must be of type '{field_schema['type']}'")
            
        if "enum" in field_schema:
            requirements.append(f"Must be one of: {', '.join(str(v) for v in field_schema['enum'])}")
            
        if "minimum" in field_schema:
            requirements.append(f"Minimum value: {field_schema['minimum']}")
            
        if "maximum" in field_schema:
            requirements.append(f"Maximum value: {field_schema['maximum']}")
            
        if "minLength" in field_schema:
            requirements.append(f"Minimum length: {field_schema['minLength']}")
            
        if "maxLength" in field_schema:
            requirements.append(f"Maximum length: {field_schema['maxLength']}")
            
        if "pattern" in field_schema:
            requirements.append(f"Must match pattern: {field_schema['pattern']}")
            
        return "; ".join(requirements) if requirements else "No specific requirements found"

    async def __aenter__(self):
        """Async context manager entry."""
        if not self._initialized:
            # Any necessary async initialization can go here
            self._initialized = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Any cleanup if needed
        self._initialized = False

class Validator:
    def __init__(
        self,
        event_queue: EventQueue,
        state_manager: StateManager,
        correction_handler
    ):
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._context_manager = AgentContextManager(event_queue)
        self._cache_manager = CacheManager(event_queue)
        self._metrics_manager = MetricsManager(event_queue)
        self._correction_handler = correction_handler
        self._schema_cache: Dict[str, Dict[str, Any]] = {}
        self.current_schema = None
        self.error_analyzer = ValidationErrorAnalyzer(self, event_queue, self._state_manager)

    async def __aenter__(self):
        """Initialize validator and analyzer APIs."""
        await self.error_analyzer.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup validator and analyzer resources."""
        await self.error_analyzer.__aexit__(exc_type, exc_val, exc_tb)
        
    async def _handle_validation_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Handle validation events using state manager."""
        try:
            if event_type == ResourceEventTypes.VALIDATION_COMPLETED.value:
                await self._state_manager.set_state(
                    f"validation:status:{data.get('resource_id', 'unknown')}",
                    {
                        "success": data.get("success", False),
                        "timestamp": datetime.now().isoformat(),
                        "details": data
                    },
                resource_type=ResourceType.AGENT
                )
                
                # Record validation metric
                await self._metrics_manager.record_metric(
                    "validation:completion",
                    1.0 if data.get("success", False) else 0.0,
                    metadata={
                        "resource_id": data.get("resource_id", "unknown"),
                        "details": data
                    }
                )
                
        except Exception as e:
            await self._event_queue.emit(
                ResourceEventTypes.ERROR_OCCURRED.value,
                {
                    "source": "validation_event_handler",
                    "error": str(e),
                    "event_type": event_type
                }
            )

    def validate_json(self, text: str) -> Optional[str]:
        """Helper to validate JSON objects and return them if valid."""
        try:
            parsed = json.loads(text)
            # Check if the parsed JSON is an object (dict in Python)
            if not isinstance(parsed, dict):
                return None
            return json.dumps(parsed)
        except json.JSONDecodeError:
            return None
    
    def extract_json_from_response(self, content: str) -> Optional[str]:
        """
        Extract and fix JSON from a text response after direct parsing has failed.
        Handles common cases like trailing text, markdown wrapping, and string escaping.
        
        Args:
            content: String that contains JSON somewhere within it
            
        Returns:
            Extracted and fixed JSON string if successful, None otherwise
        """
        # Quick return if empty or not string
        if not isinstance(content, str) or not content.strip():
            return None
                
        # Step 1: Extract JSON object pattern, handling both trailing text and markdown
        # Look for {...} with optional markdown wrapping
        # Find outermost {...} patterns - handles nesting by taking the longest valid match
        json_matches = list(re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL))
        for match in json_matches:
            if validated := self.validate_json(match.group(0)):
                return validated
                
        # Step 2: If no valid JSON found, check for string escaping
        # Common in API responses or logged outputs
        escaped_match = re.search(r'"(\{(?:\\.|[^"\\])*\})"', content)
        if escaped_match:
            try:
                # First unescape the string
                unescaped = json.loads(f'"{escaped_match.group(1)}"')
                # Then validate it's proper JSON
                if validated := self.validate_json(unescaped):
                    return validated
            except json.JSONDecodeError:
                pass
                
        # No valid JSON found
        return None
    
    async def validate_output(
        self,
        output: Dict[str, Any],
        schema: Dict[str, Any],
        operation_id: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Validate output with enhanced error handling."""
        validation_key = f"validation:{operation_id}" if operation_id else f"validation:{datetime.now().isoformat()}"
        
        try:
            # Check cache first
            if operation_id:
                cached_result = await self._cache_manager.get_cache(validation_key)
                if cached_result:
                    return cached_result["success"], cached_result["output"], cached_result["analysis"]
            
            # Perform validation
            self.current_schema = schema

            # First, ensure we're working with proper JSON
            json_obj = None
            
            # If output is a string, try to extract JSON from it
            if isinstance(output, str):
                logging.info(f"Received string output, extracting JSON")
                # First try direct parsing in case it's already a valid JSON string
                try:
                    json_obj = json.loads(output)
                    logging.info("Successfully parsed output as JSON")
                except json.JSONDecodeError:
                    # If direct parsing fails, try extraction
                    logging.info("Direct parsing failed, trying JSON extraction")
                    extracted_json = self.extract_json_from_response(output)
                    if extracted_json:
                        try:
                            json_obj = json.loads(extracted_json)
                            logging.info("Successfully extracted and parsed JSON")
                        except json.JSONDecodeError:
                            logging.warning("Failed to parse extracted JSON")
                            json_obj = None
            else:
                # Output is already a dict or other object
                logging.info("Received non-string output, using as-is")
                json_obj = output
            
            # If we couldn't get valid JSON, return validation error
            if json_obj is None:
                logging.error("Could not extract valid JSON from output")
                error_analysis = {
                    "error_analysis": {
                        "formatting_errors": [{
                            "field": "root",
                            "error_type": "json_format_error",
                            "description": "Could not extract valid JSON from output"
                        }],
                        "semantic_errors": [],
                        "primary_error_type": "formatting"
                    }
                }
                await self._handle_validation_failure(
                    validation_key,
                    "Failed to extract valid JSON",
                    error_analysis,
                    operation_id
                )
                return False, None, error_analysis

            # Now validate the JSON against the schema
            try:
                validate(instance=json_obj, schema=schema)
                
                # Success case
                success_analysis = {
                    "error_analysis": {
                        "formatting_errors": [],
                        "semantic_errors": [],
                        "primary_error_type": "none"
                    }
                }
                
                # Store result and emit event
                await self._handle_success(validation_key, json_obj, success_analysis, operation_id)
                return True, json_obj, success_analysis
                
            except JsonSchemaValidationError as e:
                # Get validation errors
                validation_errors = self.get_validation_errors(json_obj, schema)
                logging.info(f"Schema validation failed with errors: {validation_errors}")
                
                async with self.error_analyzer as analyzer:
                    # Get error analysis with schema context
                    error_analysis = await analyzer.analyze_errors(
                        json_obj,
                        validation_errors,
                        operation_id,
                        schema
                    )
                
                # Handle based on error type
                if error_analysis["error_analysis"]["primary_error_type"] == "formatting":
                    return await self._handle_formatting_errors(
                        json_obj,
                        error_analysis,
                        schema,
                        validation_key,
                        operation_id
                    )
                elif error_analysis["error_analysis"]["primary_error_type"] == "semantic":
                    return await self._handle_semantic_errors(
                        json_obj,
                        validation_errors,
                        error_analysis,
                        schema,
                        validation_key,
                        operation_id
                    )
                else:
                    # Unknown error type
                    await self._handle_validation_failure(
                        validation_key,
                        str(e),
                        error_analysis,
                        operation_id
                    )
                    return False, None, error_analysis
                    
        except Exception as e:
            return await self._handle_system_error(e, validation_key, operation_id)

    async def _handle_formatting_errors(
        self,
        output: Dict[str, Any],
        error_analysis: Dict[str, Any],
        schema: Dict[str, Any],
        validation_key: str,
        operation_id: Optional[str]
    ) -> Tuple[bool, Optional[Dict[str, Any]], Dict[str, Any]]:
        """Handle formatting errors using the formatting correction API."""
        async with self.error_analyzer as corrector:
            corrected_output = await corrector.attempt_formatting_correction(output)
            if corrected_output:
                try:
                    validate(instance=corrected_output, schema=schema)
                    await self._handle_success(validation_key, corrected_output, error_analysis, operation_id)
                    return True, corrected_output, error_analysis
                except JsonSchemaValidationError:
                    pass
                    
        await self._handle_validation_failure(
            validation_key,
            "Formatting correction failed",
            error_analysis,
            operation_id
        )
        return False, None, error_analysis

    async def _handle_semantic_errors(
        self,
        output: Dict[str, Any],
        validation_errors: List[ValidationError],
        error_analysis: Dict[str, Any],
        schema: Dict[str, Any],
        validation_key: str,
        operation_id: Optional[str]
    ) -> Tuple[bool, Optional[Dict[str, Any]], Dict[str, Any]]:
        """Handle semantic errors using the semantic error handler."""
        async with self.error_analyzer as analyzer:
            success, corrected_output, updated_analysis = await analyzer._semantic_handler.handle_semantic_errors(
                output,
                validation_errors,
                error_analysis,
                schema,
                operation_id
            )
            
            if success:
                await self._handle_success(validation_key, corrected_output, updated_analysis, operation_id)
                return True, corrected_output, updated_analysis
                
        await self._handle_validation_failure(
            validation_key,
            "Semantic correction failed",
            error_analysis,
            operation_id
        )
        return False, None, error_analysis

    async def _handle_success(
        self,
        validation_key: str,
        output: Dict[str, Any],
        analysis: Dict[str, Any],
        operation_id: Optional[str]
    ):
        """Handle successful validation result."""
        await self._state_manager.set_state(
            validation_key,
            {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "output": output,
                "analysis": analysis
            },
            resource_type=ResourceType.AGENT
        )
        
        if operation_id:
            await self._cache_manager.set_cache(
                validation_key,
                {
                    "success": True,
                    "output": output,
                    "analysis": analysis
                }
            )
        
        await self._metrics_manager.record_metric(
            "validation:success",
            1.0,
            metadata={"operation_id": operation_id}
        )
        
        await self._event_queue.emit(
            ResourceEventTypes.VALIDATION_COMPLETED.value,
            {
                "success": True,
                "operation_id": operation_id,
                "analysis": analysis
            }
        )

    async def _handle_validation_failure(
        self,
        validation_key: str,
        error_message: str,
        error_analysis: Dict[str, Any],
        operation_id: Optional[str]
    ):
        """Handle validation failure."""
        await self._state_manager.set_state(
            validation_key,
            {
                "status": "failed",
                "timestamp": datetime.now().isoformat(),
                "error": error_message,
                "analysis": error_analysis
            },
            resource_type=ResourceType.AGENT
        )
        
        await self._metrics_manager.record_metric(
            "validation:failure",
            1.0,
            metadata={
                "operation_id": operation_id,
                "error_type": error_analysis["error_analysis"]["primary_error_type"]
            }
        )

    async def _handle_system_error(
        self,
        error: Exception,
        validation_key: str,
        operation_id: Optional[str]
    ) -> Tuple[bool, None, Dict[str, Any]]:
        """Handle system-level errors."""
        error_analysis = {
            "error_analysis": {
                "formatting_errors": [{
                    "field": "root",
                    "error_type": "system_error",
                    "description": str(error)
                }],
                "semantic_errors": [],
                "primary_error_type": "system"
                }
            }
        
        await self._event_queue.emit(
            ResourceEventTypes.ERROR_OCCURRED.value,
            {
                "error": str(error),
                "operation_id": operation_id,
                "analysis": error_analysis
            }
        )
        
        await self._state_manager.set_state(
            validation_key,
            {
                "status": "error",
                "error": str(error),
                "analysis": error_analysis,
                "timestamp": datetime.now().isoformat()
            },
            resource_type=ResourceType.AGENT
        )
        
        await self._metrics_manager.record_metric(
            "validation:system_error",
            1.0,
            metadata={
                "operation_id": operation_id,
                "error": str(error)
            }
        )
        
        return False, None, error_analysis

    def _get_field_schema(self, schema: Dict[str, Any], field_path: str) -> Optional[Dict[str, Any]]:
        """Extract schema for a specific field using its path."""
        if not field_path:
            return schema
            
        parts = field_path.split(" -> ")
        current = schema
        
        for part in parts:
            if "properties" in current and part in current["properties"]:
                current = current["properties"][part]
            elif "items" in current:
                current = current["items"]
            else:
                return None
                
        return current

    def _analyze_constraints(self, field_schema: Dict[str, Any], error: ValidationError) -> Optional[Dict[str, Any]]:
        """Analyze constraint violations for a field."""
        constraints = {
            "field": error.path,
            "constraint_type": None,
            "details": {}
        }
        
        # Type constraints
        if "type" in field_schema:
            constraints["constraint_type"] = "type"
            constraints["details"]["expected_type"] = field_schema["type"]
            
        # Enum constraints
        if "enum" in field_schema:
            constraints["constraint_type"] = "enum"
            constraints["details"]["allowed_values"] = field_schema["enum"]
            
        # Numeric constraints
        for key in ["minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum"]:
            if key in field_schema:
                constraints["constraint_type"] = "numeric"
                constraints["details"][key] = field_schema[key]
                
        # String constraints
        for key in ["minLength", "maxLength", "pattern"]:
            if key in field_schema:
                constraints["constraint_type"] = "string"
                constraints["details"][key] = field_schema[key]
                
        # Array constraints
        for key in ["minItems", "maxItems", "uniqueItems"]:
            if key in field_schema:
                constraints["constraint_type"] = "array"
                constraints["details"][key] = field_schema[key]
                
        return constraints if constraints["constraint_type"] else None

    def _generate_fix_suggestion(self, error: ValidationError, field_schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate fix suggestions for semantic errors."""
        suggestion = {
            "field": error.path,
            "current_value": None,  # Will be filled by the semantic handler
            "suggested_value": None,
            "reason": error.message
        }
        
        if "enum" in field_schema:
            suggestion["suggested_value"] = field_schema["enum"][0]  # Suggest first valid enum value
            suggestion["options"] = field_schema["enum"]
            
        elif "type" in field_schema:
            if field_schema["type"] == "number":
                if "minimum" in field_schema:
                    suggestion["suggested_value"] = max(0, field_schema["minimum"])
            elif field_schema["type"] == "string":
                suggestion["suggested_value"] = ""  # Empty string as default
            elif field_schema["type"] == "boolean":
                suggestion["suggested_value"] = False  # False as default
            elif field_schema["type"] == "array":
                suggestion["suggested_value"] = []  # Empty array as default
            elif field_schema["type"] == "object":
                suggestion["suggested_value"] = {}  # Empty object as default
                
        return suggestion if suggestion["suggested_value"] is not None else None

    def get_validation_errors(
        self,
        output: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> List[ValidationError]:
        """Get all validation errors for an output against a schema."""
        errors = []
        validator = jsonschema.Draft7Validator(schema)
        
        for error in validator.iter_errors(output):
            validation_error = ValidationError(
                message=error.message,
                path=" -> ".join(str(p) for p in error.path),
                schema_path=" -> ".join(str(p) for p in error.schema_path)
            )
            errors.append(validation_error)
            
        return errors

    def generate_schema_template(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a template showing the required structure of a schema."""
        if "type" not in schema:
            return {}
            
        if schema["type"] == "object":
            template = {}
            properties = schema.get("properties", {})
            for prop_name, prop_schema in properties.items():
                template[prop_name] = self.generate_schema_template(prop_schema)
            return template
            
        elif schema["type"] == "array":
            items_schema = schema.get("items", {})
            return [self.generate_schema_template(items_schema)]
            
        elif schema["type"] == "string":
            if "enum" in schema:
                return f"<one of: {', '.join(schema['enum'])}>"
            return "<string>"
            
        return f"<{schema['type']}>"

async def main():
    pass

if __name__ == "__main__":
    asyncio.run(main())