"""Agent that analyzes compiler failures and suggests fixes."""

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


class CompilationDebugAgent(AgentInterface):
    """Agent that analyzes compiler failures and suggests fixes"""
    
    def __init__(self, 
                event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "compilation_debug_agent", 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler,
            memory_monitor
        )
    
    async def analyze_failures(self, 
                            code: str,
                            compilation_results: Dict[str, Any],
                            operation_id: str) -> Dict[str, Any]:
        """Analyze compilation failures and suggest fixes."""
        try:
            logger.info(f"Analyzing compilation failures for operation {operation_id}")
            
            # Set agent state to processing
            await self.set_agent_state(AgentState.PROCESSING)
            
            # Identify failed compiler steps
            failed_steps = []
            results = compilation_results.get("results", {})
            
            for compiler, result in results.items():
                if not result.get("success", False):
                    failed_steps.append({
                        "compiler": compiler,
                        "issues": result.get("issues", []),
                        "state": result.get("state", "UNKNOWN")
                    })
            
            # Skip if no failures found
            if not failed_steps:
                logger.info("No compilation failures to analyze")
                await self.set_agent_state(AgentState.COMPLETE)
                return {
                    "operation_id": operation_id,
                    "success": True,
                    "analysis": "No compilation failures to analyze",
                    "suggestions": []
                }
            
            # Format the issues for the prompt
            issues_str = json.dumps(failed_steps, indent=2)
            
            # Create schema for validation
            schema = {
                "type": "object",
                "required": ["analysis", "suggestions", "fixed_code"],
                "properties": {
                    "analysis": {"type": "string"},
                    "suggestions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["issue", "fix"],
                            "properties": {
                                "issue": {"type": "string"},
                                "fix": {"type": "string"},
                                "line_numbers": {"type": "array", "items": {"type": "integer"}}
                            }
                        }
                    },
                    "fixed_code": {"type": "string"}
                }
            }
            
            # Generate system prompt for analysis
            system_prompt = """You are an expert programming compiler specialist who diagnoses and fixes code issues.
Analyze the provided code and compilation issues, then suggest specific fixes to resolve each issue.
Focus on being precise and practical:
1. Identify the root cause of each compilation failure
2. Suggest specific code changes to fix each issue
3. Provide a fully corrected version of the code
4. Prioritize fixes for the most critical issues first

Return your response as JSON with these fields:
- analysis: A detailed analysis of the compilation failures
- suggestions: An array of objects, each with 'issue' (description of the problem) and 'fix' (how to fix it) fields
- fixed_code: The complete fixed version of the code
"""
            
            # Call LLM to analyze failures
            conversation = {
                "code": code,
                "compilation_failures": issues_str
            }
            
            response = await self.process_with_validation(
                conversation=json.dumps(conversation),
                system_prompt_info=(system_prompt,),
                schema=schema,
                current_phase="compilation_debug",
                operation_id=operation_id
            )
            
            # Update state to complete
            await self.set_agent_state(AgentState.COMPLETE)
            
            # Add operation id to the response
            response["operation_id"] = operation_id
            response["success"] = True
            
            logger.info(f"Compilation failure analysis completed for {operation_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error analyzing compilation failures: {str(e)}", exc_info=True)
            await self.set_agent_state(AgentState.ERROR)
            
            return {
                "operation_id": operation_id,
                "success": False,
                "error": f"Compilation failure analysis failed: {str(e)}"
            }