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
        """Evaluate multiple features and make optimization decisions based on phase zero feedback, 
        with Fire Agent complexity analysis and Air Agent historical context."""
        try:
            logger.info(f"Evaluating {len(feature_performances)} features for optimization")
            
            # Set agent state to processing
            await self.set_agent_state(AgentState.PROCESSING)
            
            # Air Agent: Get historical context for Natural Selection decisions
            logger.info("Getting Air Agent historical context for Natural Selection")
            historical_context = None
            try:
                from resources.air_agent import provide_natural_selection_context
                
                historical_context = await provide_natural_selection_context(
                    feature_performance_data=feature_performances,
                    state_manager=self._state_manager,
                    health_tracker=getattr(self, '_memory_monitor', None)
                )
                
                logger.info(f"Air Agent provided context with {historical_context.events_analyzed} events and {historical_context.patterns_identified} patterns")
                
            except Exception as air_error:
                logger.warning(f"Air Agent context provision failed: {str(air_error)}")
                historical_context = None
            
            # Fire Agent: Analyze feature complexity for decomposition opportunities
            logger.info("Fire Agent analyzing feature complexity")
            fire_interventions = []
            
            try:
                from resources.fire_agent import analyze_feature_complexity, decompose_complex_feature
                
                for i, feature_performance in enumerate(feature_performances):
                    feature_spec = feature_performance.get("feature_specification", {})
                    feature_context = feature_performance
                    
                    # Analyze feature complexity
                    complexity_analysis = await analyze_feature_complexity(
                        feature_spec=feature_spec,
                        feature_context=feature_context,
                        state_manager=self._state_manager
                    )
                    
                    # Store complexity analysis
                    await self._state_manager.set_state(
                        f"natural_selection:{operation_id}:feature_{i}_complexity",
                        complexity_analysis.__dict__,
                        "STATE"
                    )
                    
                    # If feature is too complex, decompose it
                    if complexity_analysis.exceeds_threshold:
                        logger.info(f"Feature {feature_performance.get('feature_id', i)} complexity detected (score: {complexity_analysis.complexity_score:.2f}), initiating Fire agent decomposition")
                        
                        # Determine decomposition strategy from complexity analysis
                        strategy = complexity_analysis.recommended_strategy.value if complexity_analysis.recommended_strategy else "functional_separation"
                        
                        decomposition_result = await decompose_complex_feature(
                            complex_feature=feature_spec,
                            decomposition_strategy=strategy,
                            state_manager=self._state_manager
                        )
                        
                        # Store decomposition result
                        await self._state_manager.set_state(
                            f"natural_selection:{operation_id}:feature_{i}_decomposition",
                            decomposition_result.__dict__,
                            "STATE"
                        )
                        
                        if decomposition_result.success:
                            fire_interventions.append({
                                "original_feature_id": feature_performance.get("feature_id", f"feature_{i}"),
                                "decomposed_features": decomposition_result.decomposed_features,
                                "complexity_reduction": decomposition_result.complexity_reduction,
                                "strategy_used": strategy,
                                "lessons_learned": decomposition_result.lessons_learned
                            })
                            
                            logger.info(f"Fire agent successfully decomposed feature {feature_performance.get('feature_id', i)}")
                        else:
                            logger.warning(f"Fire agent decomposition failed for feature {feature_performance.get('feature_id', i)}")
                    
            except Exception as fire_error:
                logger.warning(f"Fire Agent complexity analysis failed: {str(fire_error)}")
            
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
                },
                "fire_agent_interventions": fire_interventions,
                "air_agent_context": {
                    "historical_patterns": historical_context.success_patterns if historical_context else [],
                    "recommendations": historical_context.recommended_approaches if historical_context else [],
                    "cautionary_notes": historical_context.cautionary_notes if historical_context else [],
                    "confidence_level": historical_context.confidence_level.value if historical_context else "insufficient_data",
                    "events_analyzed": historical_context.events_analyzed if historical_context else 0
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
            
            # Generate enhanced system prompt with Fire and Air agent context
            system_prompt = f"""You are an expert software evolution specialist serving as a refinement agent.
Based on the performance data, Phase Zero feedback, Fire Agent complexity analysis, and Air Agent historical context, 
make optimization decisions using natural selection principles.

## Analysis Sources:

**Phase Zero Feedback:**
- Requirements analysis for feature alignment
- Implementation analysis for technical quality
- Evolution opportunities for strategic improvements

**Fire Agent Complexity Analysis:**
- {len(fire_interventions)} features required complexity decomposition
- Decomposed features should be considered as separate optimization candidates
- Complex features may need additional simplification before optimization

**Air Agent Historical Context:**
- {historical_context.events_analyzed if historical_context else 0} historical decisions analyzed
- Confidence level: {historical_context.confidence_level.value if historical_context else 'insufficient_data'}
- Historical success patterns: {', '.join(historical_context.success_patterns[:3]) if historical_context and historical_context.success_patterns else 'None identified'}
- Recommendations from past experience: {', '.join(historical_context.recommended_approaches[:2]) if historical_context and historical_context.recommended_approaches else 'None available'}

## Decision Framework:
1. Objectively ranking features based on performance metrics and all available feedback
2. Identifying features that should be kept, improved, or replaced
3. Incorporating Fire Agent decomposition results into optimization strategy
4. Applying lessons learned from Air Agent historical patterns
5. Finding opportunities for code reuse between features (including decomposed sub-features)
6. Suggesting combinations of features that would work well together
7. Recommending refactoring opportunities informed by complexity analysis

## Special Considerations:
- Features that underwent Fire Agent decomposition may have reduced complexity scores
- Consider decomposed sub-features as independent optimization candidates
- Apply historical success patterns where relevant to current feature set
- Heed cautionary notes from Air Agent: {', '.join(historical_context.cautionary_notes[:2]) if historical_context and historical_context.cautionary_notes else 'None noted'}

Your decisions should integrate insights from all analysis sources for comprehensive optimization strategy.

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
            
            # Track this decision event with Air Agent
            try:
                from resources.air_agent import track_decision_event
                
                await track_decision_event(
                    decision_agent="natural_selection",
                    decision_type="natural_selection",
                    decision_details={
                        "input_context": {
                            "features_analyzed": len(feature_performances),
                            "fire_interventions": len(fire_interventions),
                            "air_context_available": historical_context is not None
                        },
                        "rationale": f"Natural selection optimization of {len(feature_performances)} features with Fire/Air agent support",
                        "phase_context": "phase_three"
                    },
                    decision_outcome={
                        "success": True,
                        "features_ranked": len(response.get("feature_rankings", [])),
                        "optimization_decisions": len(response.get("optimization_decisions", [])),
                        "fire_decompositions_applied": len(fire_interventions)
                    },
                    state_manager=self._state_manager,
                    operation_id=operation_id
                )
                
            except Exception as tracking_error:
                logger.warning(f"Failed to track Natural Selection decision event: {str(tracking_error)}")
            
            # Add operation ID and all feedback to the response
            response["operation_id"] = operation_id
            response["phase_zero_feedback"] = {
                "requirements_analysis": requirements_feedback,
                "implementation_analysis": implementation_feedback,
                "evolution_opportunities": evolution_feedback
            }
            
            # Include Fire and Air agent results
            response["fire_agent_interventions"] = fire_interventions
            response["air_agent_context"] = {
                "patterns_applied": historical_context.success_patterns[:3] if historical_context and historical_context.success_patterns else [],
                "recommendations_considered": historical_context.recommended_approaches[:2] if historical_context and historical_context.recommended_approaches else [],
                "confidence_level": historical_context.confidence_level.value if historical_context else "insufficient_data",
                "events_analyzed": historical_context.events_analyzed if historical_context else 0
            }
            
            logger.info(f"Natural selection refinement completed for {len(feature_performances)} features with Fire/Air agent integration")
            logger.info(f"Fire Agent: {len(fire_interventions)} complexity interventions applied")
            logger.info(f"Air Agent: {historical_context.events_analyzed if historical_context else 0} historical events analyzed")
            
            return response
            
        except Exception as e:
            logger.error(f"Error in natural selection refinement: {str(e)}", exc_info=True)
            await self.set_agent_state(AgentState.ERROR)
            
            return {
                "error": f"Natural selection refinement failed: {str(e)}",
                "operation_id": operation_id
            }