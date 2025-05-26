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
from interfaces.agent.interface import AgentInterface
from interfaces.agent.validation import ValidationManager
from interfaces.agent.interface import AgentState

logger = logging.getLogger(__name__)


class CodeGenerationAgent(AgentInterface):
    """Agent responsible for generating feature code from requirements"""
    
    def __init__(self, 
                event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "code_generation_agent", 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler,
            memory_monitor
        )
        self._validation_manager = ValidationManager(event_queue, state_manager, context_manager)
        
    async def generate_code(self, 
                          feature_requirements: Dict[str, Any],
                          operation_id: str) -> Dict[str, Any]:
        """Generate code based on feature requirements."""
        try:
            logger.info(f"Starting code generation for operation {operation_id}")
            
            # Set agent state to processing
            await self.set_agent_state(AgentState.PROCESSING)
            
            # Prepare feature requirements for the prompt
            requirements_str = json.dumps(feature_requirements)
            
            # Get feature name and id
            feature_name = feature_requirements.get("name", "unnamed_feature")
            feature_id = feature_requirements.get("id", f"feature_{operation_id}")
            
            # Create schema for validation
            schema = {
                "type": "object",
                "required": ["code", "explanation"],
                "properties": {
                    "code": {"type": "string"},
                    "explanation": {"type": "string"},
                    "imports": {"type": "array", "items": {"type": "string"}},
                    "dependencies": {"type": "array", "items": {"type": "string"}}
                }
            }
            
            # Determine language, default to Python
            language = feature_requirements.get("language", "python")
            
            # Generate system prompt for code generation
            system_prompt = f"""You are an expert {language} developer. 
Generate clean, well-structured, type-annotated code for a feature based on the requirements.
Focus on creating code that is:
1. Correct - implements all requirements accurately
2. Well-structured - follows good design patterns
3. Maintainable - clear, commented, and easy to understand
4. Type-annotated - uses proper type hints
5. Robust - includes appropriate error handling

Return your response as JSON with these fields:
- code: The implementation code as a string
- explanation: Brief explanation of the code structure
- imports: List of imports needed
- dependencies: List of other features or components this depends on
"""
            
            # Call LLM to generate code
            response = await self.process_with_validation(
                conversation=requirements_str,
                system_prompt_info=(system_prompt,),
                schema=schema,
                current_phase="code_generation",
                operation_id=operation_id,
                metadata={
                    "feature_name": feature_name,
                    "feature_id": feature_id
                }
            )
            
            # Update state to complete
            await self.set_agent_state(AgentState.COMPLETE)
            
            # Add feature metadata to the response
            response.update({
                "feature_name": feature_name,
                "feature_id": feature_id,
                "operation_id": operation_id
            })
            
            logger.info(f"Code generation completed for {feature_name}")
            return response
            
        except Exception as e:
            logger.error(f"Error generating code: {str(e)}", exc_info=True)
            await self.set_agent_state(AgentState.ERROR)
            
            return {
                "error": f"Code generation failed: {str(e)}",
                "feature_name": feature_requirements.get("name", "unnamed_feature"),
                "feature_id": feature_requirements.get("id", f"feature_{operation_id}"),
                "operation_id": operation_id
            }