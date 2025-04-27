import json
import logging
from typing import Dict, Any, Optional

from resources import (
    EventQueue, 
    StateManager, 
    CacheManager, 
    AgentContextManager, 
    MetricsManager, 
    ErrorHandler, 
    MemoryMonitor
)
from interface import AgentState

from phase_three.agents.base import FeatureAgentBase

logger = logging.getLogger(__name__)

class FeatureTestSpecAgent(FeatureAgentBase):
    """Agent responsible for creating feature test specifications"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "feature_test_spec_agent", 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler,
            memory_monitor
        )
        
    async def create_test_specifications(self, 
                                       feature_requirements: Dict[str, Any],
                                       operation_id: str) -> Dict[str, Any]:
        """Create test specifications for a feature based on requirements."""
        try:
            logger.info(f"Creating test specifications for feature {feature_requirements.get('name', 'unknown')}")
            
            # Set agent state to processing
            await self.set_agent_state(AgentState.PROCESSING)
            
            # Prepare requirements for the prompt
            requirements_str = json.dumps(feature_requirements)
            
            # Get feature name and id
            feature_name = feature_requirements.get("name", "unnamed_feature")
            feature_id = feature_requirements.get("feature_id", f"feature_{operation_id}")
            
            # Create schema for validation
            schema = {
                "type": "object",
                "required": ["test_specifications", "test_coverage"],
                "properties": {
                    "test_specifications": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["id", "name", "description", "test_type", "expected_result"],
                            "properties": {
                                "id": {"type": "string"},
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "test_type": {"type": "string"},
                                "expected_result": {"type": "string"},
                                "dependencies": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    },
                    "test_coverage": {
                        "type": "object",
                        "properties": {
                            "requirements_covered": {"type": "array", "items": {"type": "string"}},
                            "coverage_percentage": {"type": "number"}
                        }
                    }
                }
            }
            
            # Generate system prompt for test specification creation
            system_prompt = """You are an expert test engineer specializing in test-driven development.
Create comprehensive test specifications for the provided feature requirements.
Focus on creating:
1. Unit test specifications that verify individual functionalities
2. Integration test specifications for dependencies
3. Edge case test specifications for robustness
4. Performance test specifications for non-functional requirements

Return your response as a JSON object with these fields:
- test_specifications: An array of test specification objects, each with:
  - id: A unique identifier for the test
  - name: The test name
  - description: What the test verifies
  - test_type: The type of test (unit, integration, edge_case, performance)
  - expected_result: The expected outcome of the test
  - dependencies: Any dependencies needed to run the test
- test_coverage: An object showing what requirements are covered and the coverage percentage
"""
            
            # Call LLM to create test specifications
            response = await self.process_with_validation(
                conversation=requirements_str,
                system_prompt_info=(system_prompt,),
                schema=schema,
                current_phase="test_specification",
                operation_id=operation_id,
                metadata={"feature_name": feature_name, "feature_id": feature_id}
            )
            
            # Update state to complete
            await self.set_agent_state(AgentState.COMPLETE)
            
            # Add feature metadata to the response
            response.update({
                "feature_name": feature_name,
                "feature_id": feature_id,
                "operation_id": operation_id
            })
            
            logger.info(f"Test specification creation completed for {feature_name}")
            return response
            
        except Exception as e:
            logger.error(f"Error creating test specifications: {str(e)}", exc_info=True)
            await self.set_agent_state(AgentState.ERROR)
            
            return {
                "error": f"Test specification creation failed: {str(e)}",
                "feature_name": feature_requirements.get("name", "unnamed_feature"),
                "feature_id": feature_requirements.get("feature_id", f"feature_{operation_id}"),
                "operation_id": operation_id
            }