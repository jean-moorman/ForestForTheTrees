import json
import logging
from typing import Dict, Any, Optional

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

class ComponentImplementationAgent(PhaseTwoAgentBase):
    """Agent responsible for implementing components"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "component_implementation_agent", 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler,
            memory_monitor
        )
        
    async def implement_component(self, 
                                component_requirements: Dict[str, Any],
                                test_specifications: Dict[str, Any],
                                operation_id: str) -> Dict[str, Any]:
        """Implement a component based on requirements and test specifications."""
        try:
            logger.info(f"Implementing component {component_requirements.get('name', 'unknown')}")
            
            # Set agent state to processing
            await self.set_agent_state(AgentState.PROCESSING)
            
            # Prepare input data for the prompt
            implementation_data = {
                "requirements": component_requirements,
                "test_specifications": test_specifications
            }
            implementation_str = json.dumps(implementation_data)
            
            # Get component name and id
            component_name = component_requirements.get("name", "unnamed_component")
            component_id = component_requirements.get("component_id", f"component_{operation_id}")
            
            # Create schema for validation
            schema = {
                "type": "object",
                "required": ["implementation", "implementation_metadata"],
                "properties": {
                    "implementation": {"type": "string"},
                    "implementation_metadata": {
                        "type": "object",
                        "required": ["features", "dependencies", "interfaces"],
                        "properties": {
                            "features": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["id", "name", "description"],
                                    "properties": {
                                        "id": {"type": "string"},
                                        "name": {"type": "string"},
                                        "description": {"type": "string"}
                                    }
                                }
                            },
                            "dependencies": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "interfaces": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["name", "description", "methods"],
                                    "properties": {
                                        "name": {"type": "string"},
                                        "description": {"type": "string"},
                                        "methods": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            # Generate system prompt for implementation
            system_prompt = """You are an expert software developer specializing in test-driven development.
Implement the provided component based on the requirements and test specifications.
Focus on creating:
1. Clean, modular code that satisfies all requirements
2. Code that will pass the provided test specifications
3. Well-defined interfaces for other components to interact with
4. Proper handling of dependencies

Return your response as a JSON object with these fields:
- implementation: A string containing the Python code for the component
- implementation_metadata: An object with:
  - features: An array of feature objects, each with:
    - id: A unique identifier for the feature
    - name: The feature name
    - description: A description of the feature
  - dependencies: An array of component dependencies
  - interfaces: An array of interface objects, each with:
    - name: The interface name
    - description: A description of the interface
    - methods: An array of method signatures
"""
            
            # Call LLM to implement component
            response = await self.process_with_validation(
                conversation=implementation_str,
                system_prompt_info=(system_prompt,),
                schema=schema,
                current_phase="component_implementation",
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
            
            logger.info(f"Component implementation completed for {component_name}")
            return response
            
        except Exception as e:
            logger.error(f"Error implementing component: {str(e)}", exc_info=True)
            await self.set_agent_state(AgentState.ERROR)
            
            return {
                "error": f"Component implementation failed: {str(e)}",
                "component_name": component_requirements.get("name", "unnamed_component"),
                "component_id": component_requirements.get("component_id", f"component_{operation_id}"),
                "operation_id": operation_id
            }