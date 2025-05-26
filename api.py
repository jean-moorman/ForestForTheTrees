import traceback
import anthropic
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import asyncio
from dataclasses import dataclass

class AnthropicAPI:
    def __init__(self, model: str = "claude-3-5-sonnet-20241022", key: str="", system_prompt_path: Optional[Tuple[str, Path]] = None):
        self.system_prompt_path = system_prompt_path
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,  # Change from DEBUG to INFO
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Suppress noisy libraries
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        self.client = anthropic.Anthropic(api_key=key)
        self.model = model
        self._executor = ThreadPoolExecutor(max_workers=1)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=True)

    def _sync_api_call(
        self,
        model: str,
        max_tokens: int,
        system: List[Dict[str, Any]],
        messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Synchronous API call with detailed logging"""
        try:
            logging.debug("Making API call with:")
            logging.debug(f"Model: {model}")
            logging.debug(f"Max tokens: {max_tokens}")
            logging.debug(f"System: {json.dumps(system, indent=2)}")
            logging.debug(f"Messages: {json.dumps(messages, indent=2)}")
            
            # Try standard API call first
            # try:
            #     logging.debug("Attempting standard API call...")
            #     system_message = system[0]["text"] if system else ""
            #     response = self.client.messages.create(
            #         model=model,
            #         max_tokens=max_tokens,
            #         system=system_message,
            #         messages=messages
            #     )
            #     logging.debug("Standard API call successful")
            #     return response
            # except Exception as e:
            #     logging.debug(f"Standard API call failed: {str(e)}")
            try:

                logging.debug("Attempting API call...")
                response = self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    system=system,
                    messages=messages
                )
                logging.debug("Beta API call successful")
                return response
            except Exception as e:
                logging.debug(f"Beta API call failed: {str(e)}")
                
        except Exception as e:
            logging.error(f"API call failed with error: {str(e)}")
            logging.error(f"Error type: {type(e).__name__}")
            raise
    
    async def call(
        self,
        conversation: str,
        system_prompt_info: Tuple[str, str],
        schema: Dict[str, Any],
        current_phase: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Make the API call with properly formatted system messages"""
        logging.debug("Making API call with:")
        logging.debug(f"Model: {self.model}")
        logging.debug(f"Max tokens: {max_tokens}")
        logging.debug(f"System prompt directory: {self.system_prompt_path}")

        messages = [
            {"role": "user", "content": conversation}
        ]
        system = []
        system_prompt = self.get_prompt_from_dir(system_prompt_info[0], system_prompt_info[1])
        if system_prompt:
            system.append({
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"}
            })
            
            # Add schema as a separate system message
            system.append({
                "type": "text",
                "text": json.dumps(schema),
                "cache_control": {"type": "ephemeral"}
            })
        
        # Run the synchronous API call in a thread to avoid blocking the event loop
        response = await asyncio.to_thread(
            self.client.messages.create,
            model=self.model,
            max_tokens=max_tokens,
            messages=messages,
            system=system
        )
        
        if not response.content:
            raise ValueError("Empty response from API")
            
        logging.debug("API call successful")
        return response.content[0].text
    
    def get_prompt_from_dir(self, system_prompt_dir: str, prompt_name: str = "system_prompt") -> Optional[str]:
        """
        Load system prompt from a directory by importing the specified prompt variable.
        
        Args:
            system_prompt_dir: Path to the directory containing the prompt file
            prompt_name: Name of the prompt variable to import (default: "system_prompt")
            
        Returns:
            Optional[str]: The system prompt string if found, None otherwise
        """
        try:
            logging.debug(f"System prompt directory: {system_prompt_dir}")
            
            # Remove .py extension if present
            if system_prompt_dir.endswith('.py'):
                system_prompt_dir = system_prompt_dir[:-3]
                
            # Convert directory path to module path format
            module_path = system_prompt_dir.replace("/", ".")
            
            # Remove any leading dots
            module_path = module_path.lstrip('.')
            
            logging.debug(f"Attempting to import module: {module_path}")
            
            # Import the module dynamically
            import importlib
            import sys
            
            # Add the current directory to sys.path if not already there
            current_dir = str(Path.cwd())
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
                
            module = importlib.import_module(module_path)
            
            # Get the specified prompt from the module
            prompt = getattr(module, prompt_name)
            
            if not isinstance(prompt, str):
                logging.error(f"Prompt '{prompt_name}' is not a string")
                return None
                
            return prompt
                
        except ImportError as e:
            logging.error(f"Could not import prompt module: {str(e)}")
            logging.debug(f"sys.path: {sys.path}")
            return None
        except AttributeError as e:
            logging.error(f"Prompt '{prompt_name}' not found in module: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Error loading prompt: {str(e)}")
            logging.debug(f"Exception details: {traceback.format_exc()}")
            return None

async def test_error_analysis_api(api: AnthropicAPI) -> None:
    """Test error analysis functionality of the API"""
    # Test data similar to what ValidationErrorAnalyzer would use
    test_output = {
        "response": {
            "task_analysis": "incomplete format",
            "requirements": ["req1", "req2"],
            "status": None
        }
    }
    
    test_schema = {
        "type": "object",
        "properties": {
            "error_analysis": {
                "type": "object",
                "properties": {
                    "formatting_errors": {"type": "array"},
                    "semantic_errors": {"type": "array"},
                    "primary_error_type": {"type": "string", "enum": ["formatting", "semantic"]}
                },
                "required": ["formatting_errors", "semantic_errors", "primary_error_type"]
            }
        },
        "required": ["error_analysis"]
    }

    conversation = f"""Please analyze these validation errors:
    Original Output: {json.dumps(test_output, indent=2)}
    
    Determine if these are formatting errors that can be automatically fixed,
    or semantic errors that require re-prompting the original agent.
    """

    try:
        response = await api.call(
            conversation=conversation,
            schema=test_schema,
            current_phase="error_analysis",
            max_tokens=1024
        )
        logging.info(f"Error analysis test response: {response}")
    except Exception as e:
        logging.error(f"Error analysis test failed: {str(e)}")
        raise

async def test_formatting_correction_api(api: AnthropicAPI) -> None:
    """Test formatting correction functionality of the API"""
    test_output = {
        "response": {
            "data": "misformatted example",
            "status": "incomplete"
        }
    }

    test_schema = {
        "type": "object",
        "properties": {
            "response": {
                "type": "object",
                "properties": {
                    "data": {"type": "string"},
                    "status": {"type": "string"}
                },
                "required": ["data", "status"]
            }
        },
        "required": ["response"]
    }

    conversation = f"""The following JSON output has formatting errors. 
    Please correct the format while preserving the semantic meaning:
    
    {json.dumps(test_output, indent=2)}
    """

    try:
        response = await api.call(
            conversation=conversation,
            schema=test_schema,
            current_phase="formatting_correction",
            max_tokens=1024
        )
        logging.info(f"Formatting correction test response: {response}")
    except Exception as e:
        logging.error(f"Formatting correction test failed: {str(e)}")
        raise

async def test_environmental_analysis_api(api: AnthropicAPI) -> None:
    """Test environmental analysis functionality using the default prompt"""
    
    # Test data simulating a Garden Planner's task overview
    test_task = {
        "project": {
            "name": "Web Dashboard",
            "type": "frontend",
            "features": [
                "Real-time data visualization",
                "User authentication",
                "REST API integration"
            ]
        }
    }

    # Schema matching the environment analysis agent's output format
    test_schema = {
        "type": "object",
        "properties": {
            "environment_analysis": {
                "type": "object",
                "properties": {
                    "core_requirements": {
                        "type": "object",
                        "properties": {
                            "runtime": {
                                "type": "object",
                                "properties": {
                                    "language_version": {"type": "string"},
                                    "platform_dependencies": {"type": "array"}
                                }
                            },
                            "deployment": {
                                "type": "object",
                                "properties": {
                                    "target_environment": {"type": "string"},
                                    "required_services": {"type": "array"},
                                    "minimum_specs": {"type": "object"}
                                }
                            }
                        }
                    },
                    "dependencies": {"type": "object"},
                    "integration_points": {"type": "object"},
                    "compatibility_requirements": {"type": "object"},
                    "technical_constraints": {"type": "object"}
                },
                "required": ["core_requirements", "dependencies", "integration_points", 
                           "compatibility_requirements", "technical_constraints"]
            }
        },
        "required": ["environment_analysis"]
    }

    # Initial analysis test
    conversation = f"""Please analyze this Garden Planner task and determine the environment requirements:
    Task Overview: {json.dumps(test_task, indent=2)}
    
    Provide a comprehensive environment analysis following the specified format.
    """

    try:
        response = await api.call(
            conversation=conversation,
            system_prompt_info=("FFTT_system_prompts/phase_one/environmental_analysis_agent", "initial_core_requirements_prompt"),
            schema=test_schema,
            current_phase="initial_analysis",
            max_tokens=2048
        )
        logging.info("Initial environment analysis response:")
        logging.info(response)

        # Simulate a refinement scenario
        refinement_feedback = {
            "refinement_analysis": {
                "critical_failure": {
                    "category": "deployment_specification",
                    "description": "Incomplete deployment requirements for cloud services",
                    "evidence": ["Missing container orchestration specifications"]
                },
                "root_cause": {
                    "failure_point": "deployment.required_services",
                    "causal_chain": ["Insufficient cloud platform details"]
                }
            }
        }

        refinement_conversation = f"""Please refine the environment analysis based on this feedback:
        Original Analysis: {response}
        Refinement Feedback: {json.dumps(refinement_feedback, indent=2)}
        """

        refinement_response = await api.call(
            conversation=refinement_conversation,
            system_prompt_info=("FFTT_system_prompts/phase_one/environmental_analysis_agent", "core_requirements_refinement_prompt"),
            schema=test_schema,
            current_phase="refinement",
            max_tokens=2048
        )
        logging.info("Refinement analysis response:")
        logging.info(refinement_response)

    except Exception as e:
        logging.error(f"Environmental analysis test failed: {str(e)}")
        raise

async def main():
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize the Anthropic client
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        # Initialize API client for environmental analysis
        env_analysis_api = AnthropicAPI(
            model="claude-3-5-sonnet-20241022",
            key=anthropic_api_key
        )
        
        # Run test
        async with env_analysis_api as api:
            await test_environmental_analysis_api(api)
            
    except Exception as e:
        logging.error(f"Main execution failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())

# async def main():
#     import os
#     from dotenv import load_dotenv
#     load_dotenv()
#     # Configure logging
#     logging.basicConfig(
#         level=logging.DEBUG,
#         format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
#     )
    
#     try:
#         # Initialize the Anthropic client
#         anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
#         if not anthropic_api_key:
#             raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
#         # client = Anthropic(api_key=anthropic_api_key)

#         # Initialize API clients for different purposes
#         error_analysis_api = AnthropicAPI(
#             model="claude-3-5-sonnet-20241022",
#             key=anthropic_api_key
#         )
        
#         formatting_correction_api = AnthropicAPI(
#             model="claude-3-5-sonnet-20241022",
#             key=anthropic_api_key
#         )
        
#         # Run tests
#         async with error_analysis_api as api1, formatting_correction_api as api2:
#             await test_error_analysis_api(api1)
#             await test_formatting_correction_api(api2)
            
#     except Exception as e:
#         logging.error(f"Main execution failed: {str(e)}")
#         raise

# if __name__ == "__main__":
#     asyncio.run(main())