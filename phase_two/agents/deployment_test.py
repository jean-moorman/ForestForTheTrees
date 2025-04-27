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

class DeploymentTestAgent(PhaseTwoAgentBase):
    """Agent responsible for creating deployment tests"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "deployment_test_agent", 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler,
            memory_monitor
        )
        
    async def create_deployment_tests(self,
                                  components: List[Dict[str, Any]],
                                  system_requirements: Dict[str, Any],
                                  operation_id: str) -> Dict[str, Any]:
        """Create deployment tests for the application."""
        try:
            logger.info(f"Creating deployment tests for {len(components)} components")
            
            # Set agent state to processing
            await self.set_agent_state(AgentState.PROCESSING)
            
            # Prepare input data for the prompt
            deployment_data = {
                "components": components,
                "requirements": system_requirements
            }
            deployment_str = json.dumps(deployment_data)
            
            # Create schema for validation
            schema = {
                "type": "object",
                "required": ["deployment_tests", "deployment_checks"],
                "properties": {
                    "deployment_tests": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["id", "name", "description", "test_code"],
                            "properties": {
                                "id": {"type": "string"},
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "test_code": {"type": "string"}
                            }
                        }
                    },
                    "deployment_checks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["check_type", "description", "verification_method"],
                            "properties": {
                                "check_type": {"type": "string"},
                                "description": {"type": "string"},
                                "verification_method": {"type": "string"}
                            }
                        }
                    }
                }
            }
            
            # Generate system prompt for deployment test creation
            system_prompt = """You are an expert deployment engineer.
Create comprehensive deployment tests for the application based on the components and requirements.
Focus on:
1. Environment validation tests
2. Dependency availability checks
3. Installation verification tests
4. Post-deployment health checks

Return your response as a JSON object with these fields:
- deployment_tests: An array of test case objects, each with:
  - id: A unique identifier for the test
  - name: The test name
  - description: What the deployment test verifies
  - test_code: Python code implementing the deployment test
- deployment_checks: An array of manual check objects, each with:
  - check_type: Type of deployment check
  - description: Detailed description of the check
  - verification_method: Method to verify the check
"""
            
            # Call LLM to create deployment tests
            response = await self.process_with_validation(
                conversation=deployment_str,
                system_prompt_info=(system_prompt,),
                schema=schema,
                current_phase="deployment_test_creation",
                operation_id=operation_id
            )
            
            # Update state to complete
            await self.set_agent_state(AgentState.COMPLETE)
            
            # Add operation ID to the response
            response["operation_id"] = operation_id
            
            logger.info(f"Deployment test creation completed for {len(components)} components")
            return response
            
        except Exception as e:
            logger.error(f"Error creating deployment tests: {str(e)}", exc_info=True)
            await self.set_agent_state(AgentState.ERROR)
            
            return {
                "error": f"Deployment test creation failed: {str(e)}",
                "operation_id": operation_id
            }