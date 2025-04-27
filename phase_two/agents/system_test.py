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

class SystemTestAgent(PhaseTwoAgentBase):
    """Agent responsible for creating system tests"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "system_test_agent", 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler,
            memory_monitor
        )
        
    async def create_system_tests(self,
                              components: List[Dict[str, Any]],
                              system_requirements: Dict[str, Any],
                              operation_id: str) -> Dict[str, Any]:
        """Create system-level tests for the complete application."""
        try:
            logger.info(f"Creating system tests for {len(components)} components")
            
            # Set agent state to processing
            await self.set_agent_state(AgentState.PROCESSING)
            
            # Prepare input data for the prompt
            system_data = {
                "components": components,
                "requirements": system_requirements
            }
            system_str = json.dumps(system_data)
            
            # Create schema for validation
            schema = {
                "type": "object",
                "required": ["system_tests", "coverage_analysis"],
                "properties": {
                    "system_tests": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["id", "name", "description", "test_code", "components_involved"],
                            "properties": {
                                "id": {"type": "string"},
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "test_code": {"type": "string"},
                                "components_involved": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    },
                    "coverage_analysis": {
                        "type": "object",
                        "required": ["requirements_covered", "components_covered", "coverage_percentage"],
                        "properties": {
                            "requirements_covered": {"type": "array", "items": {"type": "string"}},
                            "components_covered": {"type": "array", "items": {"type": "string"}},
                            "coverage_percentage": {"type": "number"}
                        }
                    }
                }
            }
            
            # Generate system prompt for system test creation
            system_prompt = """You are an expert system test engineer.
Create comprehensive system tests for the complete application based on the components and requirements.
Focus on:
1. End-to-end functionality testing
2. System-level integration testing
3. Performance and reliability testing at the system level
4. Comprehensive coverage of system requirements

Return your response as a JSON object with these fields:
- system_tests: An array of test case objects, each with:
  - id: A unique identifier for the test
  - name: The test name
  - description: What the system test verifies
  - test_code: Python code implementing the system test
  - components_involved: Array of component IDs involved in the test
- coverage_analysis: An object with:
  - requirements_covered: Array of requirement IDs covered by the tests
  - components_covered: Array of component IDs covered by the tests
  - coverage_percentage: Percentage of system requirements covered
"""
            
            # Call LLM to create system tests
            response = await self.process_with_validation(
                conversation=system_str,
                system_prompt_info=(system_prompt,),
                schema=schema,
                current_phase="system_test_creation",
                operation_id=operation_id
            )
            
            # Update state to complete
            await self.set_agent_state(AgentState.COMPLETE)
            
            # Add operation ID to the response
            response["operation_id"] = operation_id
            
            logger.info(f"System test creation completed for {len(components)} components")
            return response
            
        except Exception as e:
            logger.error(f"Error creating system tests: {str(e)}", exc_info=True)
            await self.set_agent_state(AgentState.ERROR)
            
            return {
                "error": f"System test creation failed: {str(e)}",
                "operation_id": operation_id
            }