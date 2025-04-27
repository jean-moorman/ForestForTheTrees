import json
import logging
from typing import Dict, List, Any, Optional

from resources import (
    EventQueue, 
    StateManager, 
    CacheManager, 
    AgentContextManager, 
    MetricsManager, 
    ErrorHandler, 
    MemoryMonitor
)
from interface import AgentInterface, ValidationManager, AgentState

from phase_three.phase_zero import (
    FeatureRequirementsAnalysisAgent,
    FeatureImplementationAnalysisAgent,
    FeatureEvolutionAgent
)

logger = logging.getLogger(__name__)

class NaturalSelectionAgent(AgentInterface):
    """Refinement agent responsible for feature optimization decisions"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "natural_selection_agent", 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler,
            memory_monitor
        )
        self._validation_manager = ValidationManager(event_queue, state_manager, context_manager)
        
        # Initialize Phase Zero feedback agents
        self._requirements_analysis_agent = FeatureRequirementsAnalysisAgent(
            event_queue, state_manager, context_manager, 
            cache_manager, metrics_manager, error_handler
        )
        self._implementation_analysis_agent = FeatureImplementationAnalysisAgent(
            event_queue, state_manager, context_manager, 
            cache_manager, metrics_manager, error_handler
        )
        self._evolution_agent = FeatureEvolutionAgent(
            event_queue, state_manager, context_manager, 
            cache_manager, metrics_manager, error_handler
        )
        
    async def evaluate_features(self,
                              feature_performances: List[Dict[str, Any]],
                              operation_id: str) -> Dict[str, Any]:
        """Evaluate multiple features and make optimization decisions based on phase zero feedback."""
        try:
            logger.info(f"Evaluating {len(feature_performances)} features for optimization")
            
            # Set agent state to processing
            await self.set_agent_state(AgentState.PROCESSING)
            
            # First gather Phase Zero feedback
            logger.info("Gathering Phase Zero feedback for feature optimization")
            
            # 1. Requirements analysis
            requirements_feedback = await self._requirements_analysis_agent.process_with_validation(
                json.dumps({"features": feature_performances}),
                {"type": "requirements_analysis"},
                current_phase="phase_zero_requirements_analysis",
                operation_id=f"{operation_id}_req_analysis"
            )
            
            # 2. Implementation analysis
            implementation_feedback = await self._implementation_analysis_agent.process_with_validation(
                json.dumps({"features": feature_performances}),
                {"type": "implementation_analysis"},
                current_phase="phase_zero_implementation_analysis",
                operation_id=f"{operation_id}_impl_analysis"
            )
            
            # 3. Evolution opportunities
            evolution_feedback = await self._evolution_agent.process_with_validation(
                json.dumps({
                    "features": feature_performances,
                    "requirements_analysis": requirements_feedback,
                    "implementation_analysis": implementation_feedback
                }),
                {"type": "evolution_opportunities"},
                current_phase="phase_zero_evolution_analysis",
                operation_id=f"{operation_id}_evol_analysis"
            )
            
            # Combine all feedback for natural selection decisions
            feedback_data = {
                "features": feature_performances,
                "phase_zero_feedback": {
                    "requirements_analysis": requirements_feedback,
                    "implementation_analysis": implementation_feedback,
                    "evolution_opportunities": evolution_feedback
                }
            }
            
            # Create schema for validation of final decision
            schema = {
                "type": "object",
                "required": ["feature_rankings", "optimization_decisions", "evolution_strategy"],
                "properties": {
                    "feature_rankings": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["feature_id", "feature_name", "rank", "overall_score"],
                            "properties": {
                                "feature_id": {"type": "string"},
                                "feature_name": {"type": "string"},
                                "rank": {"type": "integer"},
                                "overall_score": {"type": "number"},
                                "strengths": {"type": "array", "items": {"type": "string"}},
                                "weaknesses": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    },
                    "optimization_decisions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["feature_id", "decision", "rationale"],
                            "properties": {
                                "feature_id": {"type": "string"},
                                "decision": {"type": "string"},
                                "rationale": {"type": "string"}
                            }
                        }
                    },
                    "evolution_strategy": {
                        "type": "object",
                        "required": ["reuse_opportunities", "refactor_suggestions", "feature_combinations"],
                        "properties": {
                            "reuse_opportunities": {"type": "array", "items": {"type": "object"}},
                            "refactor_suggestions": {"type": "array", "items": {"type": "object"}},
                            "feature_combinations": {"type": "array", "items": {"type": "object"}}
                        }
                    }
                }
            }
            
            # Generate system prompt for natural selection evaluation
            system_prompt = """You are an expert software evolution specialist serving as a refinement agent.
Based on the performance data and Phase Zero feedback, make optimization decisions using natural selection principles.
Focus on:
1. Objectively ranking features based on performance metrics and feedback
2. Identifying features that should be kept, improved, or replaced
3. Finding opportunities for code reuse between features
4. Suggesting combinations of features that would work well together
5. Recommending refactoring opportunities

Your decisions should be driven by the feedback from the specialized analysis agents, with careful consideration
of all aspects of feature quality.

Return your response as a JSON object with these fields:
- feature_rankings: An array of feature rankings, each with:
  - feature_id: The feature identifier
  - feature_name: The feature name
  - rank: Numerical ranking (1 is best)
  - overall_score: Numerical score from performance metrics
  - strengths: Array of feature strengths
  - weaknesses: Array of feature weaknesses
- optimization_decisions: An array of decisions, each with:
  - feature_id: The feature identifier
  - decision: One of "keep", "improve", "replace", "combine"
  - rationale: Explanation for the decision
- evolution_strategy: Object containing:
  - reuse_opportunities: Array of code reuse possibilities
  - refactor_suggestions: Array of refactoring suggestions
  - feature_combinations: Array of features that could be combined
"""
            
            # Call LLM to make final optimization decisions based on all feedback
            response = await self.process_with_validation(
                conversation=json.dumps(feedback_data),
                system_prompt_info=(system_prompt,),
                schema=schema,
                current_phase="natural_selection_refinement",
                operation_id=operation_id
            )
            
            # Update state to complete
            await self.set_agent_state(AgentState.COMPLETE)
            
            # Add operation ID and feedback to the response
            response["operation_id"] = operation_id
            response["phase_zero_feedback"] = {
                "requirements_analysis": requirements_feedback,
                "implementation_analysis": implementation_feedback,
                "evolution_opportunities": evolution_feedback
            }
            
            logger.info(f"Natural selection refinement completed for {len(feature_performances)} features")
            return response
            
        except Exception as e:
            logger.error(f"Error in natural selection refinement: {str(e)}", exc_info=True)
            await self.set_agent_state(AgentState.ERROR)
            
            return {
                "error": f"Natural selection refinement failed: {str(e)}",
                "operation_id": operation_id
            }