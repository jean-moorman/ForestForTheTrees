"""Agent that performs deep analysis of compilation results."""

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
from interface import AgentInterface, AgentState

logger = logging.getLogger(__name__)


class CompilationAnalysisAgent(AgentInterface):
    """Agent that performs deep analysis of compilation results"""
    
    def __init__(self, 
                event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "compilation_analysis_agent", 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler,
            memory_monitor
        )
    
    async def analyze_compilation(self, 
                              code: str,
                              compilation_results: Dict[str, Any],
                              operation_id: str) -> Dict[str, Any]:
        """Analyze compilation results and provide insights."""
        try:
            logger.info(f"Performing compilation analysis for operation {operation_id}")
            
            # Set agent state to processing
            await self.set_agent_state(AgentState.PROCESSING)
            
            # Format the results for the prompt
            results_str = json.dumps(compilation_results, indent=2)
            
            # Create schema for validation
            schema = {
                "type": "object",
                "required": ["summary", "insights", "metrics", "improvements"],
                "properties": {
                    "summary": {"type": "string"},
                    "insights": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "metrics": {
                        "type": "object",
                        "properties": {
                            "code_quality_score": {"type": "number"},
                            "robustness_score": {"type": "number"},
                            "maintainability_score": {"type": "number"},
                            "security_score": {"type": "number"}
                        }
                    },
                    "improvements": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["category", "suggestion"],
                            "properties": {
                                "category": {"type": "string"},
                                "suggestion": {"type": "string"},
                                "priority": {"type": "string"}
                            }
                        }
                    }
                }
            }
            
            # Generate system prompt for analysis
            system_prompt = """You are an expert code quality analyst who evaluates compilation results.
Analyze the provided code and compilation results to offer insights into code quality.
Focus on providing value through:
1. Objective analysis of compilation metrics
2. Specific insights about code structure and quality
3. Numerical scores for different aspects of the code
4. Actionable suggestions for improvements
5. Identification of patterns that might cause future issues

Return your response as JSON with these fields:
- summary: A concise summary of the overall code quality
- insights: An array of specific insights drawn from the compilation results
- metrics: An object with numerical scores (0-100) for code_quality_score, robustness_score, maintainability_score, and security_score
- improvements: An array of objects with 'category', 'suggestion', and 'priority' fields
"""
            
            # Call LLM to analyze compilation results
            conversation = {
                "code": code,
                "compilation_results": results_str
            }
            
            response = await self.process_with_validation(
                conversation=json.dumps(conversation),
                system_prompt_info=(system_prompt,),
                schema=schema,
                current_phase="compilation_analysis",
                operation_id=operation_id
            )
            
            # Update state to complete
            await self.set_agent_state(AgentState.COMPLETE)
            
            # Add operation id to the response
            response["operation_id"] = operation_id
            response["success"] = True
            
            logger.info(f"Compilation analysis completed for {operation_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error in compilation analysis: {str(e)}", exc_info=True)
            await self.set_agent_state(AgentState.ERROR)
            
            return {
                "operation_id": operation_id,
                "success": False,
                "error": f"Compilation analysis failed: {str(e)}"
            }