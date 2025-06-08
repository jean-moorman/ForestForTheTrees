from datetime import datetime
from pathlib import Path
import json
import logging
import traceback
from typing import Dict, List, Optional, Tuple, Any
import asyncio
import os
import importlib
from dotenv import load_dotenv
from typing import Dict, Any, Protocol, Optional

from resources import ResourceType, ResourceEventTypes, AgentContext, AgentContextType, EventQueue, StateManager, AgentContextManager, CacheManager, MetricsManager, ErrorHandler
from agent_validation import Validator, ValidationException
from api import AnthropicAPI

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
    
class Agent:
    def __init__(
        self,
        event_queue: EventQueue,
        state_manager: StateManager,
        context_manager: AgentContextManager,
        cache_manager: CacheManager,
        metrics_manager: MetricsManager,
        error_handler: ErrorHandler,
        model: str = "claude-3-7-sonnet-20250219"
    ):
        load_dotenv()
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        logging.debug(f"Initializing Agent with model: {model}")

        try:
            self._event_queue = event_queue
            self._state_manager = state_manager
            self._context_manager = context_manager
            self._cache_manager = cache_manager
            self._metrics_manager = metrics_manager
            self._error_handler = error_handler
            
            self.model = model
            self.max_tokens = 1024
            self.max_validation_attempts = 3
            
            # Initialize API client
            anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
            if not anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
            self.api = AnthropicAPI(
                model="claude-3-7-sonnet-20250219",
                key=anthropic_api_key
            )
            if not self.api:
                raise ValueError("failed to initialize AnthropicAPI")
            
            self.validator = Validator(
                self._event_queue,
                self._state_manager,
                correction_handler=self
            )
            if not self.validator:
                raise ValueError("Failed to initialize Validator")
            
            # Initialize validation history
            self.validation_history = []

        except Exception as e:
            self.logger.error(f"Failed to initialize Agent: {str(e)}\n{traceback.format_exc()}")
            raise

    async def __aenter__(self):
        """Async enter implementation for context manager."""
        self.api = await self.api.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async exit implementation for context manager."""
        await self.api.__aexit__(exc_type, exc_val, exc_tb)

    async def get_response(
        self,
        conversation: str,
        system_prompt_info: Tuple[str],
        schema: Dict[str, Any] = None,
        current_phase: Optional[str] = None,
        operation_id: Optional[str] = None,
        context_type: Optional[AgentContextType] = None,
        window_size: Optional[int] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get a validated response using modular resource managers."""
        if not operation_id:
            operation_id = f"agent_op_{datetime.now().isoformat()}"
            
        validation_key = f"validation:agent:{operation_id}"
        
        try:
            self.logger.info(f"=== STARTING get_response with operation_id: {operation_id} ===")
            self.logger.info(f"Conversation length: {len(conversation) if conversation else 0}")
            
            # Validate inputs
            if not conversation:
                raise ValueError("conversation parameter cannot be empty")
            if schema is None: #setting default schema
                self.logger.info("Schema parameter is none, setting default schema")
                self.logger.info(f"system_prompt_info: {system_prompt_info}")
                prompt_name = system_prompt_info[1]
                self.logger.info(f"prompt_name: {prompt_name}")
                schema_name = prompt_name[:-6] + "schema"
                self.logger.info(f"schema_name: {schema_name}")
                schema_dir = system_prompt_info[0]
                # Check if the schema_dir is a file path without extension
                if not schema_dir.endswith('.py'):
                    schema_path = schema_dir + ".py"
                else:
                    schema_path = schema_dir
                self.logger.info(f"Schema path: {schema_path}")
                self.logger.info(f"Schema dir: {schema_dir}")
                self.logger.info(f"Working directory: {os.getcwd()}")
                if not os.path.exists(schema_path):
                    self.logger.error(f"Schema file not found: {schema_path}")
                    raise FileNotFoundError(f"Schema file not found: {schema_path}")
                
                # Load the schema module dynamically
                spec = importlib.util.spec_from_file_location(schema_name, schema_path)
                if spec is None or spec.loader is None:
                    self.logger.debug(f"Could not load schema spec from {schema_path}")
                    raise ImportError(f"Could not load schema spec from {schema_path}")
                    
                schema_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(schema_module)
                
                # Get the schema from the module
                self.schema = getattr(schema_module, schema_name, None)
                if self.schema is None:
                    raise AttributeError(f"No schema found in {schema_path}")
                
                self.logger.debug(f"Schema loaded successfully: {schema_name}")
            # Get validation state entry
            state_entry = await self._state_manager.get_state(validation_key)
            
            if not state_entry:
                # Initialize validation state
                await self._state_manager.set_state(
                    resource_id=validation_key,
                    state={
                        "attempts": 0,
                        "history": []
                    },
                    resource_type=ResourceType.AGENT
                )
                # Get the newly created state entry
                state_entry = await self._state_manager.get_state(validation_key)
            
            # Access state data properly through the StateEntry object
            validation_data = state_entry.state
            if validation_data["attempts"] >= self.max_validation_attempts:
                self.logger.warning("Maximum validation attempts exceeded")
                error_details = {
                    "type": "validation_exceeded", 
                    "message": "Maximum validation attempts exceeded",
                    "attempts": validation_data["attempts"],
                    "history": validation_data["history"]
                }
                await self._handle_error(error_details, operation_id, current_phase)
                return {"error": error_details}
            
            self.logger.debug(f"Getting agent context for operation {operation_id}")
            # Get agent context
            context = await self._context_manager.get_context(f"agent_context:{operation_id}")
            if not context:
                self.logger.debug("No agent context found, creating new context")
                context = await self._context_manager.create_context(
                    agent_id=f"agent_context:{operation_id}",
                    operation_id=operation_id,
                    schema=self.schema,
                    context_type=AgentContextType.PERSISTENT,
                )
                self.logger.debug("Agent context created successfully")

            # Get raw response
            content = await self.api.call(
                conversation=conversation,
                system_prompt_info=system_prompt_info,
                schema=self.schema,
                current_phase=current_phase,
                max_tokens=max_tokens or self.max_tokens
            )
            if content is None:
                raise ValueError("API call returned None response")
            
            try:
                # Log content only in debug mode to avoid massive output
                self.logger.debug(f"API response length: {len(content)} characters")
                self.logger.debug(f"Schema validation using: {type(self.schema)}")
                
                # Pass content directly to validator - it will handle string extraction or object validation
                try:
                    success, result, analysis = await self.validator.validate_output(content, self.schema)
                except Exception as e:
                    self.logger.debug("validation failed with error: ", str(e))

                # Update validation state
                validation_data = state_entry.state
                validation_data["attempts"] += 1
                validation_data["history"].append({
                    "timestamp": datetime.now().isoformat(),
                    "success": success,
                    "error_analysis": None if success else analysis
                })

                await self._state_manager.set_state(
                    resource_id=validation_key,
                    state=validation_data,
                    resource_type=ResourceType.AGENT
                )

                # Record metrics
                await self._metrics_manager.record_metric(
                    "agent:validation:success_rate",
                    1.0 if success else 0.0,
                    metadata={
                        "operation_id": operation_id,
                        "phase": current_phase
                    }
                )
                
                if success:
                    self.logger.debug(f"Validation succeeded after {validation_data['attempts']} attempts")
                    return result
                
                #Handle multiple validation attempts
                self.logger.debug(f"Starting validation loop - attempts: {validation_data['attempts']}, max: {self.max_validation_attempts}")
                while not success and validation_data["attempts"] < self.max_validation_attempts - 1:
                    self.logger.debug(f"Validation attempt {validation_data['attempts'] + 1} - validation failed, retrying...")
                    val_errors = f"Validation failed with errors: {analysis}"
                    
                    # Get new content with validation feedback
                    new_content = await self.api.call(
                        conversation=conversation + "\n\n" + val_errors,
                        system_prompt_info=system_prompt_info,
                        schema=self.schema,
                        current_phase=current_phase,
                        max_tokens=max_tokens or self.max_tokens
                    )
                    
                    # Pass new content directly to validator
                    success, result, analysis = await self.validator.validate_output(new_content, self.schema)

                    validation_data["attempts"] += 1
                    self.logger.debug(f"Validation attempt {validation_data['attempts']} completed. Success: {success}")
                    
                    # Safety check to prevent infinite loops
                    if validation_data["attempts"] >= self.max_validation_attempts:
                        self.logger.warning(f"Maximum validation attempts ({self.max_validation_attempts}) reached, breaking loop")
                        break
                    validation_data["history"].append({
                        "timestamp": datetime.now().isoformat(),
                        "success": success,
                        "error_analysis": None if success else analysis
                    })

                    await self._state_manager.set_state(
                        resource_id=validation_key,
                        state=validation_data,
                        resource_type=ResourceType.AGENT
                    )

                    # Record metrics
                    await self._metrics_manager.record_metric(
                        "agent:validation:success_rate",
                        1.0 if success else 0.0,
                        metadata={
                            "operation_id": operation_id,
                            "phase": current_phase
                        }
                    )

                    if success:
                        self.logger.debug(f"Validation succeeded on retry attempt {validation_data['attempts']}")
                        return result
    
                         
                return {
                    "error": {
                        "type": "validation_error",
                        "message": "Response validation failed",
                        "analysis": analysis,
                        "attempts": validation_data["attempts"]
                    }
                }
                    
            except json.JSONDecodeError as je:
                error_details = {
                    "type": "json_decode_error",
                    "message": f"Failed to parse JSON: {str(je)}",
                    "details": f"Error at position {je.pos}: {je.msg}",
                    "content_sample": content[:200]
                }
                await self._handle_error(error_details, operation_id, current_phase)
                return {"error": error_details}
                
        except Exception as e:
            error_details = self._create_error_details(e)
            await self._handle_error(error_details, operation_id, current_phase)
            return {"error": error_details}
        
        finally:
            try:
                await self._event_queue.stop()
            except Exception as e:
                self.logger.error(f"Error stopping event queue: {str(e)}")
    
    def _create_error_details(self, error: Exception) -> Dict[str, Any]:
        """Create detailed error information."""
        return {
            "type": "system_error",
            "message": str(error),
            "details": type(error).__name__,
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_error(
        self,
        error_details: Dict[str, Any],
        operation_id: str,
        current_phase: Optional[str] = None
    ) -> None:
        """Handle errors using resource managers."""
        await self._error_handler.handle_error(
            Exception(error_details["message"]),
            f"agent:{operation_id}",
            "agent_processing_error",
            context={
                "phase": current_phase,
                "error_type": error_details["type"],
                "operation_id": operation_id
            }
        )
        
        await self._event_queue.emit(
            ResourceEventTypes.ERROR_OCCURRED.value,
            {
                "agent_id": operation_id,
                **error_details
            }
        )

    async def handle_correction_request(
        self,
        request: CorrectionRequest
    ) -> CorrectionResult:
        """
        Handle a correction request by generating a new response that addresses validation errors.
        
        Args:
            request: CorrectionRequest containing the original output, feedback, and schema
            
        Returns:
            CorrectionResult containing the corrected output or error information
        """
        try:
            # Build correction prompt
            correction_prompt = self._build_correction_prompt(request)
            
            # Get corrected response using API
            corrected_content = await self.api.call(
                conversation=correction_prompt,
                system_prompt_info=("FFTT_system_prompts/validation/semantic_correction_agent", "semantic_correction_prompt"),
                schema=request.schema,
                current_phase="semantic_correction",
                max_tokens=self.max_tokens
            )
            
            if not corrected_content:
                return CorrectionResult(
                    corrected_output=None,
                    success=False,
                    error_message="Empty response from API"
                )

            # Parse the corrected content
            try:
                corrected_output = json.loads(corrected_content)
                return CorrectionResult(
                    corrected_output=corrected_output,
                    success=True
                )
            except json.JSONDecodeError as e:
                return CorrectionResult(
                    corrected_output=None,
                    success=False,
                    error_message=f"Failed to parse corrected output: {str(e)}"
                )

        except Exception as e:
            self.logger.error(f"Error handling correction request: {str(e)}")
            return CorrectionResult(
                corrected_output=None,
                success=False,
                error_message=f"Correction handling error: {str(e)}"
            )

    def _build_correction_prompt(self, request: CorrectionRequest) -> str:
        """
        Build a prompt for correcting validation errors.
        
        Args:
            request: CorrectionRequest containing correction details
            
        Returns:
            str: Formatted prompt for the API
        """
        prompt_parts = [
            "Your previous response had validation errors that need to be corrected.",
            "",
            f"Attempt number: {request.attempt_number}",
            "",
            "Validation Feedback:",
            request.feedback,
            "",
            "Original Output:",
            json.dumps(request.original_output),
            "",
            "Schema Requirements:",
            json.dumps(request.schema),
            "",
            "Please provide a corrected response that meets all requirements.",
            "Only provide the corrected JSON output with no additional explanation or text."
        ]
        
        return "\n".join(prompt_parts)
    
async def main():
    """Test the Agent get_response functionality."""
    # Initialize test agent with system prompt path
    mock_q = EventQueue()
    mock_state_manager = StateManager(mock_q)
    mock_context_manager = AgentContextManager(mock_q)
    mock_cache_manager = CacheManager(mock_q)
    mock_metrics_manager = MetricsManager(mock_q)
    mock_error_handler = ErrorHandler(mock_q)

    test_agent = Agent(mock_q, mock_state_manager, mock_context_manager, mock_cache_manager, mock_metrics_manager, mock_error_handler, model="claude-3-7-sonnet-20250219")
    
    initial_task_elaboration_schema = {
            "type": "object",
            "properties": {
                "task_analysis": {
                    "type": "object",
                    "properties": {
                        "original_request": {"type": "string"},
                        "interpreted_goal": {"type": "string"},
                        "scope": {
                            "type": "object",
                            "properties": {
                                "included": {"type": "array", "items": {"type": "string"}},
                                "excluded": {"type": "array", "items": {"type": "string"}},
                                "assumptions": {"type": "array", "items": {"type": "string"}}
                            },
                            "required": ["included", "excluded", "assumptions"]
                        },
                        "technical_requirements": {
                            "type": "object",
                            "properties": {
                                "languages": {"type": "array", "items": {"type": "string"}},
                                "frameworks": {"type": "array", "items": {"type": "string"}},
                                "apis": {"type": "array", "items": {"type": "string"}},
                                "infrastructure": {"type": "array", "items": {"type": "string"}}
                            },
                            "required": ["languages", "frameworks", "apis", "infrastructure"]
                        },
                        "constraints": {
                            "type": "object",
                            "properties": {
                                "technical": {"type": "array", "items": {"type": "string"}},
                                "business": {"type": "array", "items": {"type": "string"}},
                                "performance": {"type": "array", "items": {"type": "string"}}
                            },
                            "required": ["technical", "business", "performance"]
                        },
                        "considerations": {
                            "type": "object",
                            "properties": {
                                "security": {"type": "array", "items": {"type": "string"}},
                                "scalability": {"type": "array", "items": {"type": "string"}},
                                "maintainability": {"type": "array", "items": {"type": "string"}}
                            },
                            "required": ["security", "scalability", "maintainability"]
                        }
                    },
                    "required": ["original_request", "interpreted_goal", "scope", 
                            "technical_requirements", "constraints", "considerations"]
                }
            },
            "required": ["task_analysis"]
        }


    
    # test_api = AnthropicAPI(model="claude-3-5-sonnet-20241022")
    validator = Validator(event_queue=EventQueue(), state_manager=mock_state_manager, correction_handler=test_agent)

    # Test schema with opportunities for both semantic and formatting errors
    test_schema = {
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
    validator.current_schema = test_schema

    try:
        print("Starting Agent get_response tests...\n")
        
        # Test 1: Valid Response
        print("Test 1: Valid Response")
        result = await test_agent.get_response(
            conversation="Test valid response",
            system_prompt_info = ("FFTT_system_prompts/phase_one/environmental_analysis_agent","initial_core_requirements_prompt"),
            schema=None,
            current_phase="testing"
        )
        print(f"Result: {json.dumps(result, indent=2)}")
        # raise Exception
        # Test 2: Invalid JSON
        print("\nTest 2: Invalid JSON")
        result = await test_agent.get_response(
            conversation="Test invalid_json response",
            system_prompt_info= ("FFTT_system_prompts/phase_one/environmental_analysis_agent","initial_core_requirements_prompt"),
            schema=None,
            current_phase="testing"
        )
        print(f"Result: {json.dumps(result, indent=2)}")
        raise Exception
        # Test 3: Invalid Schema
        print("\nTest 3: Invalid Schema")
        result = await test_agent.get_response(
            conversation="Test invalid_schema response",
            system_prompt_info = ("FFTT_system_prompts/phase_one/environmental_analysis_agent","initial_core_requirements_prompt"),
            schema=initial_task_elaboration_schema,
            current_phase="testing"
        )
        print(f"Result: {json.dumps(result, indent=2)}")
        
        # Test 4: Multiple Validation Attempts
        print("\nTest 4: Multiple Validation Attempts")
        for i in range(test_agent.max_validation_attempts + 1):
            print(f"\nAttempt {i + 1}:")
            result = await test_agent.get_response(
                conversation="Test invalid_schema response",
                system_prompt_info =("FFTT_system_prompts/phase_one/environmental_analysis_agent","initial_core_requirements_prompt"),
                schema=initial_task_elaboration_schema,
                current_phase="testing"
            )
            print(f"Result: {json.dumps(result, indent=2)}")
            if "error" in result and result["error"].get("type") == "validation_exceeded":
                print("Maximum validation attempts exceeded as expected")
                break
        
        # Test 5: Resource Manager Integration
        print("\nTest 5: Resource Manager Integration")
        result = await test_agent.get_response(
            conversation="Test valid response",
            system_prompt_info = ("FFTT_system_prompts/phase_one/environmental_analysis_agent","initial_core_requirements_prompt"),
            schema=None,
            current_phase="resource_test"
        )
        print(f"Result: {json.dumps(result, indent=2)}")
        print("Resource manager state:", 
              (await test_agent._state_manager.get_state("agent:validation:resource_test")).state)
        
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        raise

if __name__ == "__main__":
    # Run the test
    asyncio.run(main())