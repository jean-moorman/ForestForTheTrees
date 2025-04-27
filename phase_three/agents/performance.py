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

class FeaturePerformanceAgent(FeatureAgentBase):
    """Agent responsible for evaluating feature performance"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "feature_performance_agent", 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler,
            memory_monitor
        )
        
    async def evaluate_performance(self,
                                feature_implementation: Dict[str, Any],
                                test_results: Dict[str, Any],
                                operation_id: str) -> Dict[str, Any]:
        """Evaluate the performance of a feature."""
        try:
            logger.info(f"Evaluating performance for {feature_implementation.get('feature_name', 'unknown')}")
            
            # Set agent state to processing
            await self.set_agent_state(AgentState.PROCESSING)
            
            # Prepare input data for the prompt
            performance_data = {
                "feature": feature_implementation,
                "test_results": test_results
            }
            performance_str = json.dumps(performance_data)
            
            # Get feature name and id
            feature_name = feature_implementation.get("feature_name", "unnamed_feature")
            feature_id = feature_implementation.get("feature_id", f"feature_{operation_id}")
            
            # Create schema for validation
            schema = {
                "type": "object",
                "required": ["performance_metrics", "overall_score", "improvement_suggestions"],
                "properties": {
                    "performance_metrics": {
                        "type": "object",
                        "required": ["code_quality", "test_coverage", "build_stability", "maintainability", "runtime_efficiency", "integration_score"],
                        "properties": {
                            "code_quality": {"type": "number"},
                            "test_coverage": {"type": "number"},
                            "build_stability": {"type": "number"},
                            "maintainability": {"type": "number"},
                            "runtime_efficiency": {"type": "number"},
                            "integration_score": {"type": "number"}
                        }
                    },
                    "overall_score": {"type": "number"},
                    "improvement_suggestions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["area", "description", "priority"],
                            "properties": {
                                "area": {"type": "string"},
                                "description": {"type": "string"},
                                "priority": {"type": "string"}
                            }
                        }
                    }
                }
            }
            
            # Generate system prompt for performance evaluation
            system_prompt = """You are an expert software quality analyst.
Evaluate the performance of the feature implementation based on test results and code quality.
Focus on:
1. Code quality (structure, patterns, readability)
2. Test coverage (comprehensiveness, edge cases)
3. Build stability (reliability of builds)
4. Maintainability (ease of future modifications)
5. Runtime efficiency (resource usage, speed)
6. Integration quality (how well it works with dependencies)

Return your response as a JSON object with these fields:
- performance_metrics: An object with scores from 0-100 for:
  - code_quality: Code structure and readability
  - test_coverage: Completeness of test coverage
  - build_stability: Reliability of build process
  - maintainability: Ease of future maintenance
  - runtime_efficiency: Resource usage efficiency
  - integration_score: Quality of integration with dependencies
- overall_score: A weighted average of all metrics (0-100)
- improvement_suggestions: An array of suggested improvements, each with:
  - area: The area to improve
  - description: Detailed description of the improvement
  - priority: "low", "medium", or "high"
"""
            
            # Call LLM to evaluate performance
            response = await self.process_with_validation(
                conversation=performance_str,
                system_prompt_info=(system_prompt,),
                schema=schema,
                current_phase="performance_evaluation",
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
            
            logger.info(f"Performance evaluation completed for {feature_name}")
            return response
            
        except Exception as e:
            logger.error(f"Error evaluating performance: {str(e)}", exc_info=True)
            await self.set_agent_state(AgentState.ERROR)
            
            return {
                "error": f"Performance evaluation failed: {str(e)}",
                "feature_name": feature_implementation.get("feature_name", "unnamed_feature"),
                "feature_id": feature_implementation.get("feature_id", f"feature_{operation_id}"),
                "operation_id": operation_id
            }