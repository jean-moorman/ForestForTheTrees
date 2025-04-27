import json
import logging
from typing import Dict, List, Any, Optional

from resources import (
    EventQueue, 
    StateManager, 
    AgentContextManager, 
    CacheManager, 
    MetricsManager, 
    ErrorHandler, 
    MemoryMonitor
)
from interface import AgentState

from phase_two.agents.agent_base import PhaseTwoAgentBase

logger = logging.getLogger(__name__)

class IntegrationTestAgent(PhaseTwoAgentBase):
    """Agent responsible for creating integration tests between components"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "integration_test_agent", 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler,
            memory_monitor
        )
        
    async def create_integration_tests(self,
                                   component_implementation: Dict[str, Any],
                                   dependencies: List[Dict[str, Any]],
                                   operation_id: str) -> Dict[str, Any]:
        """Create integration tests between a component and its dependencies."""
        try:
            logger.info(f"Creating integration tests for {component_implementation.get('component_name', 'unknown')}")
            
            # Set agent state to processing
            await self.set_agent_state(AgentState.PROCESSING)
            
            # Prepare input data for the prompt
            integration_data = {
                "component": component_implementation,
                "dependencies": dependencies
            }
            integration_str = json.dumps(integration_data)
            
            # Get component name and id
            component_name = component_implementation.get("component_name", "unnamed_component")
            component_id = component_implementation.get("component_id", f"component_{operation_id}")
            
            # Create schema for validation
            schema = {
                "type": "object",
                "required": ["integration_tests", "integration_score"],
                "properties": {
                    "integration_tests": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["id", "name", "description", "test_code", "components_tested"],
                            "properties": {
                                "id": {"type": "string"},
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "test_code": {"type": "string"},
                                "components_tested": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    },
                    "integration_score": {"type": "number"},
                    "integration_issues": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["issue_type", "description", "severity"],
                            "properties": {
                                "issue_type": {"type": "string"},
                                "description": {"type": "string"},
                                "severity": {"type": "string"},
                                "fix_suggestion": {"type": "string"}
                            }
                        }
                    }
                }
            }
            
            # Generate system prompt for integration test creation
            system_prompt = """You are an expert integration test engineer.
Analyze the component implementation and its dependencies to create comprehensive integration tests.
Focus on:
1. Testing the interactions between the component and its dependencies
2. Identifying potential integration issues
3. Ensuring all communication paths are tested
4. Validating data flows between components

Return your response as a JSON object with these fields:
- integration_tests: An array of test case objects, each with:
  - id: A unique identifier for the test
  - name: The test name
  - description: What the integration test verifies
  - test_code: Python code implementing the integration test
  - components_tested: Array of component IDs being tested together
- integration_score: A score from 0-100 indicating integration quality
- integration_issues: An array of potential issues found, each with:
  - issue_type: Type of integration issue
  - description: Detailed description of the issue
  - severity: "low", "medium", or "high"
  - fix_suggestion: Suggested fix for the issue
"""
            
            # Call LLM to create integration tests
            response = await self.process_with_validation(
                conversation=integration_str,
                system_prompt_info=(system_prompt,),
                schema=schema,
                current_phase="integration_test_creation",
                operation_id=operation_id,
                metadata={"component_name": component_name, "component_id": component_id}
            )
            
            # Update state to complete
            await self.set_agent_state(AgentState.COMPLETE)
            
            # Add component metadata to the response
            response.update({
                "component_name": component_name,
                "component_id": component_id,
                "operation_id": operation_id
            })
            
            logger.info(f"Integration test creation completed for {component_name}")
            return response
            
        except Exception as e:
            logger.error(f"Error creating integration tests: {str(e)}", exc_info=True)
            await self.set_agent_state(AgentState.ERROR)
            
            return {
                "error": f"Integration test creation failed: {str(e)}",
                "component_name": component_implementation.get("component_name", "unnamed_component"),
                "component_id": component_implementation.get("component_id", f"component_{operation_id}"),
                "operation_id": operation_id
            }