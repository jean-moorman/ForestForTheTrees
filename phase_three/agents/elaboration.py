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

class FeatureElaborationAgent(FeatureAgentBase):
    """Agent responsible for elaborating feature requirements"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "feature_elaboration_agent", 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler,
            memory_monitor
        )
        
    async def elaborate_feature(self, 
                              feature_metadata: Dict[str, Any],
                              operation_id: str) -> Dict[str, Any]:
        """Elaborate feature requirements from initial metadata."""
        try:
            logger.info(f"Starting feature elaboration for {feature_metadata.get('name', 'unknown')}")
            
            # Set agent state to processing
            await self.set_agent_state(AgentState.PROCESSING)
            
            # Prepare feature metadata for the prompt
            metadata_str = json.dumps(feature_metadata)
            
            # Create schema for validation
            schema = {
                "type": "object",
                "required": ["feature_id", "name", "description", "requirements", "dependencies", "test_scenarios"],
                "properties": {
                    "feature_id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "requirements": {
                        "type": "object",
                        "properties": {
                            "functional": {"type": "array", "items": {"type": "string"}},
                            "non_functional": {"type": "array", "items": {"type": "string"}}
                        }
                    },
                    "dependencies": {"type": "array", "items": {"type": "string"}},
                    "test_scenarios": {"type": "array", "items": {"type": "string"}}
                }
            }
            
            # Generate system prompt for elaboration
            system_prompt = """You are an expert software requirements engineer.
Elaborate the provided feature metadata into a comprehensive set of requirements.
Focus on creating:
1. Clear functional requirements that specify what the feature should do
2. Non-functional requirements addressing performance, scalability, etc.
3. Dependencies on other features or components
4. Test scenarios to verify the feature works correctly

Return your response as a JSON object with these fields:
- feature_id: A unique identifier for the feature
- name: The feature name
- description: A detailed description of the feature
- requirements: An object with 'functional' and 'non_functional' arrays
- dependencies: An array of dependency identifiers
- test_scenarios: An array of test scenarios for the feature
"""
            
            # Call LLM to elaborate requirements
            response = await self.process_with_validation(
                conversation=metadata_str,
                system_prompt_info=(system_prompt,),
                schema=schema,
                current_phase="feature_elaboration",
                operation_id=operation_id,
                metadata={"feature_name": feature_metadata.get("name", "unknown")}
            )
            
            # Update state to complete
            await self.set_agent_state(AgentState.COMPLETE)
            
            # Add operation ID to the response
            response["operation_id"] = operation_id
            
            logger.info(f"Feature elaboration completed for {response.get('name', 'unknown')}")
            return response
            
        except Exception as e:
            logger.error(f"Error elaborating feature: {str(e)}", exc_info=True)
            await self.set_agent_state(AgentState.ERROR)
            
            return {
                "error": f"Feature elaboration failed: {str(e)}",
                "feature_name": feature_metadata.get("name", "unknown"),
                "operation_id": operation_id
            }