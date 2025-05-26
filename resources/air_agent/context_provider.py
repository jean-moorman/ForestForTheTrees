"""
Air Agent context provision functionality.

This module provides historical context to decision-making agents by analyzing
past decision events, Fire interventions, and identified patterns to generate
relevant insights and recommendations.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .models import (
    HistoricalContext,
    DecisionEvent,
    FireIntervention,
    DecisionPattern,
    PatternConfidence,
    CrossPhasePattern,
    ContextRequest,
    ContextResponse
)
from .history_tracker import get_decision_history
from .pattern_analyzer import (
    analyze_decision_patterns,
    identify_success_patterns,
    identify_failure_patterns
)

logger = logging.getLogger(__name__)


async def provide_refinement_context(
    requesting_agent: str,  # "garden_foundation_refinement"
    refinement_context: Dict[str, Any],
    lookback_period: Optional[timedelta] = None,
    state_manager=None,
    health_tracker=None
) -> HistoricalContext:
    """
    Provide historical context for Garden Foundation Refinement Agent decisions.
    
    This is the primary context provision function for the Garden Foundation
    Refinement Agent to help it make better decisions about when and how to
    perform refinements.
    
    Args:
        requesting_agent: Name of the requesting agent
        refinement_context: Current refinement context and analysis
        lookback_period: Time period for historical analysis
        state_manager: State manager for data retrieval
        health_tracker: Optional health tracker for monitoring
        
    Returns:
        HistoricalContext with relevant refinement patterns and recommendations
    """
    try:
        logger.info(f"Providing refinement context for {requesting_agent}")
        
        # Set default lookback period
        if lookback_period is None:
            lookback_period = timedelta(days=30)
        
        # Get relevant historical decision events
        refinement_decisions = await get_decision_history(
            agent_filter=requesting_agent,
            decision_type_filter="refinement_necessity",
            phase_filter="phase_one",
            lookback_period=lookback_period,
            max_events=50,
            state_manager=state_manager
        )
        
        strategy_decisions = await get_decision_history(
            agent_filter=requesting_agent,
            decision_type_filter="refinement_strategy",
            phase_filter="phase_one",
            lookback_period=lookback_period,
            max_events=30,
            state_manager=state_manager
        )
        
        # Combine all relevant events
        relevant_events = refinement_decisions + strategy_decisions
        
        # Analyze decision patterns
        decision_patterns = await analyze_decision_patterns(
            relevant_events,
            pattern_types=["refinement_necessity", "refinement_strategy"],
            min_frequency=2
        )
        
        # Identify success and failure patterns
        success_patterns = await identify_success_patterns(
            relevant_events,
            success_threshold=0.7
        )
        
        failure_patterns = await identify_failure_patterns(
            relevant_events,
            failure_threshold=0.3
        )
        
        # Generate specific recommendations based on current context
        recommendations = await _generate_refinement_recommendations(
            refinement_context,
            success_patterns,
            failure_patterns,
            relevant_events
        )
        
        # Generate cautionary notes
        cautionary_notes = await _generate_refinement_cautions(
            refinement_context,
            failure_patterns,
            relevant_events
        )
        
        # Assess confidence level
        confidence_level = _assess_context_confidence(
            relevant_events,
            decision_patterns,
            lookback_period
        )
        
        # Create historical context
        historical_context = HistoricalContext(
            context_type="refinement",
            requesting_agent=requesting_agent,
            context_timestamp=datetime.now(),
            relevant_events=relevant_events,
            identified_patterns=decision_patterns,
            success_patterns=[p.pattern_name for p in success_patterns],
            failure_patterns=[p.pattern_name for p in failure_patterns],
            recommended_approaches=recommendations,
            cautionary_notes=cautionary_notes,
            confidence_level=confidence_level,
            lookback_period=lookback_period,
            events_analyzed=len(relevant_events),
            patterns_identified=len(decision_patterns)
        )
        
        # Track context provision metrics
        if health_tracker:
            await _track_context_provision(health_tracker, historical_context)
        
        logger.info(f"Refinement context provided: {len(relevant_events)} events, {len(decision_patterns)} patterns")
        
        return historical_context
        
    except Exception as e:
        logger.error(f"Error providing refinement context: {str(e)}")
        
        # Return minimal context on error
        return HistoricalContext(
            context_type="refinement",
            requesting_agent=requesting_agent,
            context_timestamp=datetime.now(),
            confidence_level=PatternConfidence.INSUFFICIENT_DATA,
            cautionary_notes=[f"Context generation failed: {str(e)}"]
        )


async def provide_fire_context(
    complexity_context: str,  # "guideline", "feature", "component"
    current_complexity_analysis: Dict[str, Any],
    state_manager=None,
    health_tracker=None
) -> HistoricalContext:
    """
    Provide historical context for Fire agent decomposition decisions.
    
    This function provides the Fire agent with historical data about
    past complexity interventions to improve decomposition strategy selection.
    
    Args:
        complexity_context: Type of complexity being analyzed
        current_complexity_analysis: Current complexity analysis results
        state_manager: State manager for data retrieval
        health_tracker: Optional health tracker for monitoring
        
    Returns:
        HistoricalContext with Fire agent intervention patterns and recommendations
    """
    try:
        logger.info(f"Providing Fire context for {complexity_context} complexity")
        
        # Get Fire intervention history
        fire_interventions = await _get_fire_intervention_history(
            context_filter=complexity_context,
            lookback_period=timedelta(days=60),
            state_manager=state_manager
        )
        
        # Get related complexity intervention decisions
        complexity_decisions = await get_decision_history(
            decision_type_filter="complexity_intervention",
            lookback_period=timedelta(days=60),
            max_events=30,
            state_manager=state_manager
        )
        
        # Analyze Fire intervention patterns
        intervention_patterns = await _analyze_fire_patterns(
            fire_interventions,
            current_complexity_analysis
        )
        
        # Find most effective strategies for similar cases
        effective_strategies = await _identify_effective_strategies(
            fire_interventions,
            current_complexity_analysis
        )
        
        # Generate Fire-specific recommendations
        fire_recommendations = await _generate_fire_recommendations(
            current_complexity_analysis,
            effective_strategies,
            intervention_patterns
        )
        
        # Generate cautionary notes based on past failures
        fire_cautions = await _generate_fire_cautions(
            fire_interventions,
            current_complexity_analysis
        )
        
        # Calculate confidence based on historical data similarity
        confidence_level = _assess_fire_context_confidence(
            fire_interventions,
            current_complexity_analysis
        )
        
        # Create Fire-specific historical context
        historical_context = HistoricalContext(
            context_type="fire_decomposition",
            requesting_agent="fire_agent",
            context_timestamp=datetime.now(),
            relevant_events=complexity_decisions,
            relevant_interventions=fire_interventions,
            success_patterns=effective_strategies,
            recommended_approaches=fire_recommendations,
            cautionary_notes=fire_cautions,
            confidence_level=confidence_level,
            events_analyzed=len(complexity_decisions),
            patterns_identified=len(intervention_patterns)
        )
        
        # Track Fire context provision
        if health_tracker:
            await _track_context_provision(health_tracker, historical_context)
        
        logger.info(f"Fire context provided: {len(fire_interventions)} interventions analyzed")
        
        return historical_context
        
    except Exception as e:
        logger.error(f"Error providing Fire context: {str(e)}")
        
        return HistoricalContext(
            context_type="fire_decomposition",
            requesting_agent="fire_agent",
            context_timestamp=datetime.now(),
            confidence_level=PatternConfidence.INSUFFICIENT_DATA,
            cautionary_notes=[f"Fire context generation failed: {str(e)}"]
        )


async def provide_natural_selection_context(
    feature_performance_data: List[Dict[str, Any]],
    state_manager=None,
    health_tracker=None
) -> HistoricalContext:
    """
    Provide historical context for Natural Selection Agent decisions.
    
    This function helps the Natural Selection Agent make better decisions
    about feature evolution and optimization strategies.
    
    Args:
        feature_performance_data: Current feature performance data
        state_manager: State manager for data retrieval
        health_tracker: Optional health tracker for monitoring
        
    Returns:
        HistoricalContext with Natural Selection patterns and recommendations
    """
    try:
        logger.info("Providing Natural Selection context")
        
        # Get Natural Selection decision history
        selection_decisions = await get_decision_history(
            agent_filter="natural_selection",
            decision_type_filter="natural_selection",
            phase_filter="phase_three",
            lookback_period=timedelta(days=45),
            max_events=40,
            state_manager=state_manager
        )
        
        # Get feature evolution decisions
        evolution_decisions = await get_decision_history(
            decision_type_filter="feature_evolution",
            phase_filter="phase_three",
            lookback_period=timedelta(days=45),
            max_events=30,
            state_manager=state_manager
        )
        
        # Analyze Natural Selection patterns
        selection_patterns = await _analyze_selection_patterns(
            selection_decisions,
            feature_performance_data
        )
        
        # Identify successful optimization strategies
        optimization_strategies = await _identify_optimization_strategies(
            selection_decisions + evolution_decisions,
            feature_performance_data
        )
        
        # Generate Natural Selection recommendations
        selection_recommendations = await _generate_selection_recommendations(
            feature_performance_data,
            optimization_strategies,
            selection_patterns
        )
        
        # Create Natural Selection context
        historical_context = HistoricalContext(
            context_type="natural_selection",
            requesting_agent="natural_selection",
            context_timestamp=datetime.now(),
            relevant_events=selection_decisions + evolution_decisions,
            success_patterns=optimization_strategies,
            recommended_approaches=selection_recommendations,
            confidence_level=_assess_selection_context_confidence(selection_decisions),
            events_analyzed=len(selection_decisions) + len(evolution_decisions),
            patterns_identified=len(selection_patterns)
        )
        
        # Track context provision
        if health_tracker:
            await _track_context_provision(health_tracker, historical_context)
        
        return historical_context
        
    except Exception as e:
        logger.error(f"Error providing Natural Selection context: {str(e)}")
        
        return HistoricalContext(
            context_type="natural_selection",
            requesting_agent="natural_selection",
            context_timestamp=datetime.now(),
            confidence_level=PatternConfidence.INSUFFICIENT_DATA
        )


async def provide_evolution_context(
    evolution_context: Dict[str, Any],
    state_manager=None,
    health_tracker=None
) -> HistoricalContext:
    """
    Provide historical context for Evolution Agent strategic adaptations.
    
    Args:
        evolution_context: Current evolution context and system state
        state_manager: State manager for data retrieval
        health_tracker: Optional health tracker for monitoring
        
    Returns:
        HistoricalContext with Evolution Agent patterns and strategic insights
    """
    try:
        logger.info("Providing Evolution Agent context")
        
        # Get Evolution Agent decision history
        evolution_decisions = await get_decision_history(
            agent_filter="evolution",
            lookback_period=timedelta(days=90),
            max_events=50,
            state_manager=state_manager
        )
        
        # Analyze cross-phase evolution patterns
        evolution_patterns = await _analyze_evolution_patterns(
            evolution_decisions,
            evolution_context
        )
        
        # Generate strategic recommendations
        strategic_recommendations = await _generate_evolution_recommendations(
            evolution_context,
            evolution_patterns,
            evolution_decisions
        )
        
        # Create Evolution context
        historical_context = HistoricalContext(
            context_type="evolution",
            requesting_agent="evolution",
            context_timestamp=datetime.now(),
            relevant_events=evolution_decisions,
            recommended_approaches=strategic_recommendations,
            confidence_level=_assess_evolution_context_confidence(evolution_decisions),
            events_analyzed=len(evolution_decisions),
            patterns_identified=len(evolution_patterns)
        )
        
        return historical_context
        
    except Exception as e:
        logger.error(f"Error providing Evolution context: {str(e)}")
        
        return HistoricalContext(
            context_type="evolution",
            requesting_agent="evolution",
            context_timestamp=datetime.now(),
            confidence_level=PatternConfidence.INSUFFICIENT_DATA
        )


async def analyze_cross_phase_patterns(
    current_phase: str,
    state_manager=None
) -> List[CrossPhasePattern]:
    """
    Analyze patterns that span multiple phases for system-wide insights.
    
    Args:
        current_phase: Current phase context
        state_manager: State manager for data retrieval
        
    Returns:
        List of identified cross-phase patterns
    """
    try:
        logger.info(f"Analyzing cross-phase patterns from {current_phase}")
        
        # Get decision events from all phases
        all_decisions = await get_decision_history(
            lookback_period=timedelta(days=60),
            max_events=200,
            state_manager=state_manager
        )
        
        # Group decisions by phase
        phase_decisions = _group_decisions_by_phase(all_decisions)
        
        # Identify cross-phase patterns
        cross_phase_patterns = []
        
        # Pattern 1: Complexity escalation across phases
        escalation_pattern = await _identify_complexity_escalation_pattern(phase_decisions)
        if escalation_pattern:
            cross_phase_patterns.append(escalation_pattern)
        
        # Pattern 2: Refinement cascade effects
        cascade_pattern = await _identify_refinement_cascade_pattern(phase_decisions)
        if cascade_pattern:
            cross_phase_patterns.append(cascade_pattern)
        
        # Pattern 3: Feature evolution feedback loops
        feedback_pattern = await _identify_evolution_feedback_pattern(phase_decisions)
        if feedback_pattern:
            cross_phase_patterns.append(feedback_pattern)
        
        return cross_phase_patterns
        
    except Exception as e:
        logger.error(f"Error analyzing cross-phase patterns: {str(e)}")
        return []


# Helper functions for context generation

async def _generate_refinement_recommendations(
    refinement_context: Dict[str, Any],
    success_patterns: List[DecisionPattern],
    failure_patterns: List[DecisionPattern],
    relevant_events: List[DecisionEvent]
) -> List[str]:
    """Generate specific recommendations for refinement decisions."""
    recommendations = []
    
    # Analyze current context against historical patterns
    current_complexity = refinement_context.get("complexity_indicators", {})
    current_issues = refinement_context.get("identified_issues", [])
    
    # Recommendations based on success patterns
    for pattern in success_patterns:
        if any(cond in str(current_issues) for cond in pattern.preconditions):
            recommendations.extend(pattern.recommendations)
    
    # General recommendations based on historical data
    if len(relevant_events) > 10:
        success_rate = len([e for e in relevant_events if e.decision_outcome.value == "success"]) / len(relevant_events)
        
        if success_rate > 0.8:
            recommendations.append("Historical success rate is high - proceed with confidence")
        elif success_rate < 0.4:
            recommendations.append("Historical success rate is low - consider more conservative approach")
    
    # Context-specific recommendations
    if current_complexity.get("score", 0) > 80:
        recommendations.append("High complexity detected - prioritize decomposition before refinement")
    
    return recommendations[:5]  # Limit to top 5 recommendations


async def _generate_refinement_cautions(
    refinement_context: Dict[str, Any],
    failure_patterns: List[DecisionPattern],
    relevant_events: List[DecisionEvent]
) -> List[str]:
    """Generate cautionary notes for refinement decisions."""
    cautions = []
    
    # Cautions based on failure patterns
    for pattern in failure_patterns:
        if pattern.confidence_level in [PatternConfidence.HIGH, PatternConfidence.MEDIUM]:
            cautions.append(f"Avoid: {pattern.pattern_description}")
    
    # Recent failure analysis
    recent_failures = [e for e in relevant_events[-10:] if e.decision_outcome.value == "failure"]
    if len(recent_failures) > 3:
        cautions.append("Multiple recent refinement failures detected - review approach")
    
    return cautions


def _assess_context_confidence(
    relevant_events: List[DecisionEvent],
    decision_patterns: List[DecisionPattern],
    lookback_period: timedelta
) -> PatternConfidence:
    """Assess confidence level in the provided context."""
    if len(relevant_events) < 3:
        return PatternConfidence.INSUFFICIENT_DATA
    elif len(relevant_events) >= 10 and len(decision_patterns) >= 2:
        return PatternConfidence.HIGH
    elif len(relevant_events) >= 5:
        return PatternConfidence.MEDIUM
    else:
        return PatternConfidence.LOW


async def _get_fire_intervention_history(
    context_filter: str,
    lookback_period: timedelta,
    state_manager
) -> List[FireIntervention]:
    """Get Fire intervention history with filtering."""
    interventions = []
    
    if not state_manager:
        return interventions
    
    try:
        # Get Fire intervention keys (simplified implementation)
        intervention_keys = await state_manager.list_keys("air_agent:fire_intervention:")
        
        cutoff_time = datetime.now() - lookback_period
        
        for key in intervention_keys:
            try:
                intervention_data = await state_manager.get_state(key, "STATE")
                if intervention_data:
                    timestamp = datetime.fromisoformat(intervention_data["timestamp"])
                    if timestamp >= cutoff_time:
                        # Filter by context if specified
                        if context_filter in intervention_data.get("intervention_context", ""):
                            intervention = _deserialize_fire_intervention(intervention_data)
                            interventions.append(intervention)
            except Exception as e:
                logger.warning(f"Error retrieving Fire intervention {key}: {e}")
                continue
        
        return interventions[:50]  # Limit results
        
    except Exception as e:
        logger.error(f"Error getting Fire intervention history: {e}")
        return []


def _deserialize_fire_intervention(intervention_data: Dict[str, Any]) -> FireIntervention:
    """Deserialize Fire intervention from stored data."""
    timestamp = datetime.fromisoformat(intervention_data["timestamp"])
    
    intervention_duration = None
    if intervention_data.get("intervention_duration"):
        # Handle timedelta deserialization
        duration_seconds = intervention_data["intervention_duration"]
        intervention_duration = timedelta(seconds=duration_seconds)
    
    return FireIntervention(
        intervention_id=intervention_data["intervention_id"],
        intervention_context=intervention_data["intervention_context"],
        timestamp=timestamp,
        original_complexity_score=intervention_data["original_complexity_score"],
        final_complexity_score=intervention_data.get("final_complexity_score"),
        complexity_reduction=intervention_data.get("complexity_reduction"),
        decomposition_strategy=intervention_data["decomposition_strategy"],
        success=intervention_data["success"],
        intervention_duration=intervention_duration,
        lessons_learned=intervention_data.get("lessons_learned", []),
        effective_techniques=intervention_data.get("effective_techniques", []),
        challenges_encountered=intervention_data.get("challenges_encountered", []),
        operation_id=intervention_data.get("operation_id"),
        triggering_decision=intervention_data.get("triggering_decision")
    )


async def _analyze_fire_patterns(
    fire_interventions: List[FireIntervention],
    current_analysis: Dict[str, Any]
) -> List[DecisionPattern]:
    """Analyze patterns in Fire interventions."""
    patterns = []
    
    if len(fire_interventions) < 3:
        return patterns
    
    # Pattern: Successful decomposition strategies
    successful_interventions = [i for i in fire_interventions if i.success]
    if len(successful_interventions) >= 3:
        strategy_counts = {}
        for intervention in successful_interventions:
            strategy = intervention.decomposition_strategy
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        most_successful_strategy = max(strategy_counts, key=strategy_counts.get)
        success_rate = strategy_counts[most_successful_strategy] / len(successful_interventions)
        
        if success_rate >= 0.6:
            pattern = DecisionPattern(
                pattern_id=f"fire_success_{most_successful_strategy}",
                pattern_type="success_pattern",
                pattern_name=f"Successful {most_successful_strategy}",
                pattern_description=f"{most_successful_strategy} strategy shows {success_rate:.0%} success rate",
                decision_types=[],
                contexts=["fire_decomposition"],
                frequency=strategy_counts[most_successful_strategy],
                success_rate=success_rate,
                preconditions=[f"Strategy: {most_successful_strategy}"],
                outcomes=["Complexity reduction achieved"],
                confidence_level=PatternConfidence.HIGH if success_rate > 0.8 else PatternConfidence.MEDIUM,
                first_observed=min(i.timestamp for i in successful_interventions),
                last_observed=max(i.timestamp for i in successful_interventions),
                recommendations=[f"Consider using {most_successful_strategy} strategy"]
            )
            patterns.append(pattern)
    
    return patterns


async def _identify_effective_strategies(
    fire_interventions: List[FireIntervention],
    current_analysis: Dict[str, Any]
) -> List[str]:
    """Identify most effective strategies for similar complexity situations."""
    strategies = []
    
    current_score = current_analysis.get("complexity_score", 0)
    current_causes = current_analysis.get("complexity_causes", [])
    
    # Find interventions with similar complexity scores
    similar_interventions = [
        i for i in fire_interventions
        if abs(i.original_complexity_score - current_score) <= 20 and i.success
    ]
    
    if similar_interventions:
        # Count strategy effectiveness
        strategy_effectiveness = {}
        for intervention in similar_interventions:
            strategy = intervention.decomposition_strategy
            reduction = intervention.complexity_reduction or 0
            
            if strategy not in strategy_effectiveness:
                strategy_effectiveness[strategy] = []
            strategy_effectiveness[strategy].append(reduction)
        
        # Calculate average effectiveness per strategy
        for strategy, reductions in strategy_effectiveness.items():
            avg_reduction = sum(reductions) / len(reductions)
            if avg_reduction > 15:  # Minimum 15-point reduction
                strategies.append(f"{strategy} (avg reduction: {avg_reduction:.1f})")
    
    return strategies[:3]  # Top 3 strategies


async def _generate_fire_recommendations(
    current_analysis: Dict[str, Any],
    effective_strategies: List[str],
    intervention_patterns: List[DecisionPattern]
) -> List[str]:
    """Generate Fire-specific recommendations."""
    recommendations = []
    
    # Strategy recommendations
    if effective_strategies:
        recommendations.append(f"Most effective strategies: {', '.join(effective_strategies[:2])}")
    
    # Complexity-specific recommendations
    current_score = current_analysis.get("complexity_score", 0)
    if current_score > 90:
        recommendations.append("Critical complexity level - immediate decomposition recommended")
    elif current_score > 75:
        recommendations.append("High complexity level - decomposition strongly recommended")
    
    # Pattern-based recommendations
    for pattern in intervention_patterns:
        recommendations.extend(pattern.recommendations[:2])
    
    return recommendations[:4]


async def _generate_fire_cautions(
    fire_interventions: List[FireIntervention],
    current_analysis: Dict[str, Any]
) -> List[str]:
    """Generate Fire-specific cautionary notes."""
    cautions = []
    
    # Analyze recent failures
    recent_failures = [i for i in fire_interventions[-10:] if not i.success]
    if len(recent_failures) > 2:
        common_challenges = {}
        for failure in recent_failures:
            for challenge in failure.challenges_encountered:
                common_challenges[challenge] = common_challenges.get(challenge, 0) + 1
        
        if common_challenges:
            most_common = max(common_challenges, key=common_challenges.get)
            cautions.append(f"Common failure: {most_common}")
    
    # Context-specific cautions
    current_context = current_analysis.get("analysis_context", "")
    if current_context == "phase_one":
        cautions.append("Phase 1 decomposition affects all subsequent phases - proceed carefully")
    
    return cautions


def _assess_fire_context_confidence(
    fire_interventions: List[FireIntervention],
    current_analysis: Dict[str, Any]
) -> PatternConfidence:
    """Assess confidence in Fire context based on historical data similarity."""
    if len(fire_interventions) < 2:
        return PatternConfidence.INSUFFICIENT_DATA
    
    current_score = current_analysis.get("complexity_score", 0)
    
    # Find similar interventions
    similar_count = 0
    for intervention in fire_interventions:
        if abs(intervention.original_complexity_score - current_score) <= 25:
            similar_count += 1
    
    if similar_count >= 5:
        return PatternConfidence.HIGH
    elif similar_count >= 3:
        return PatternConfidence.MEDIUM
    else:
        return PatternConfidence.LOW


# Natural Selection context helpers

async def _analyze_selection_patterns(
    selection_decisions: List[DecisionEvent],
    feature_performance_data: List[Dict[str, Any]]
) -> List[DecisionPattern]:
    """Analyze Natural Selection decision patterns."""
    # Simplified implementation
    return []


async def _identify_optimization_strategies(
    decisions: List[DecisionEvent],
    feature_performance_data: List[Dict[str, Any]]
) -> List[str]:
    """Identify successful optimization strategies."""
    strategies = []
    
    successful_decisions = [d for d in decisions if d.decision_outcome.value == "success"]
    
    for decision in successful_decisions:
        if "optimization_strategy" in decision.decision_details:
            strategy = decision.decision_details["optimization_strategy"]
            if strategy not in strategies:
                strategies.append(strategy)
    
    return strategies[:3]


async def _generate_selection_recommendations(
    feature_performance_data: List[Dict[str, Any]],
    optimization_strategies: List[str],
    selection_patterns: List[DecisionPattern]
) -> List[str]:
    """Generate Natural Selection recommendations."""
    recommendations = []
    
    if optimization_strategies:
        recommendations.append(f"Proven strategies: {', '.join(optimization_strategies)}")
    
    # Performance-based recommendations
    if feature_performance_data:
        avg_performance = sum(f.get("performance_score", 0) for f in feature_performance_data) / len(feature_performance_data)
        if avg_performance < 0.6:
            recommendations.append("Low average performance - consider aggressive optimization")
        else:
            recommendations.append("Good performance baseline - focus on incremental improvements")
    
    return recommendations


def _assess_selection_context_confidence(selection_decisions: List[DecisionEvent]) -> PatternConfidence:
    """Assess confidence in Natural Selection context."""
    if len(selection_decisions) < 3:
        return PatternConfidence.INSUFFICIENT_DATA
    elif len(selection_decisions) >= 10:
        return PatternConfidence.HIGH
    else:
        return PatternConfidence.MEDIUM


# Evolution context helpers

async def _analyze_evolution_patterns(
    evolution_decisions: List[DecisionEvent],
    evolution_context: Dict[str, Any]
) -> List[DecisionPattern]:
    """Analyze Evolution Agent decision patterns."""
    # Simplified implementation
    return []


async def _generate_evolution_recommendations(
    evolution_context: Dict[str, Any],
    evolution_patterns: List[DecisionPattern],
    evolution_decisions: List[DecisionEvent]
) -> List[str]:
    """Generate Evolution Agent recommendations."""
    recommendations = []
    
    if evolution_decisions:
        success_rate = len([d for d in evolution_decisions if d.decision_outcome.value == "success"]) / len(evolution_decisions)
        if success_rate > 0.7:
            recommendations.append("Historical evolution strategies show good success rate")
        else:
            recommendations.append("Consider refining evolution approach based on historical data")
    
    return recommendations


def _assess_evolution_context_confidence(evolution_decisions: List[DecisionEvent]) -> PatternConfidence:
    """Assess confidence in Evolution context."""
    if len(evolution_decisions) < 5:
        return PatternConfidence.INSUFFICIENT_DATA
    else:
        return PatternConfidence.MEDIUM


# Cross-phase pattern analysis helpers

def _group_decisions_by_phase(all_decisions: List[DecisionEvent]) -> Dict[str, List[DecisionEvent]]:
    """Group decisions by phase context."""
    phase_decisions = {
        "phase_one": [],
        "phase_two": [],
        "phase_three": [],
        "system_wide": []
    }
    
    for decision in all_decisions:
        phase = decision.phase_context or "system_wide"
        if phase in phase_decisions:
            phase_decisions[phase].append(decision)
        else:
            phase_decisions["system_wide"].append(decision)
    
    return phase_decisions


async def _identify_complexity_escalation_pattern(phase_decisions: Dict[str, List[DecisionEvent]]) -> Optional[CrossPhasePattern]:
    """Identify complexity escalation patterns across phases."""
    # Simplified pattern detection
    phase_one_complexity = len([d for d in phase_decisions.get("phase_one", []) if "complexity" in d.decision_rationale.lower()])
    phase_three_complexity = len([d for d in phase_decisions.get("phase_three", []) if "complexity" in d.decision_rationale.lower()])
    
    if phase_one_complexity > 0 and phase_three_complexity > phase_one_complexity:
        return CrossPhasePattern(
            pattern_id="complexity_escalation",
            pattern_name="Complexity Escalation",
            phases_involved=["phase_one", "phase_three"],
            pattern_type="escalation",
            description="Complexity issues in Phase 1 lead to increased complexity in Phase 3",
            trigger_conditions=["Phase 1 complexity decisions"],
            propagation_path=["phase_one -> phase_three"],
            system_impact="negative",
            mitigation_strategies=["Increase Phase 1 complexity monitoring"],
            early_warning_signs=["Multiple Phase 1 refinements"]
        )
    
    return None


async def _identify_refinement_cascade_pattern(phase_decisions: Dict[str, List[DecisionEvent]]) -> Optional[CrossPhasePattern]:
    """Identify refinement cascade patterns."""
    # Simplified implementation
    return None


async def _identify_evolution_feedback_pattern(phase_decisions: Dict[str, List[DecisionEvent]]) -> Optional[CrossPhasePattern]:
    """Identify evolution feedback patterns."""
    # Simplified implementation
    return None


# Health tracking

async def _track_context_provision(health_tracker, historical_context: HistoricalContext):
    """Track context provision metrics."""
    try:
        health_tracker.track_metric("air_agent_context_provided", 1)
        health_tracker.track_metric(f"air_agent_context_{historical_context.context_type}", 1)
        health_tracker.track_metric("air_agent_events_analyzed", historical_context.events_analyzed)
        health_tracker.track_metric("air_agent_patterns_identified", historical_context.patterns_identified)
    except Exception as e:
        logger.warning(f"Failed to track context provision: {e}")