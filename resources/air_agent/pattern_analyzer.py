"""
Air Agent pattern analysis functionality.

This module analyzes historical decision data to identify patterns, trends,
and insights that can inform future decision-making.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter

from .models import (
    DecisionEvent,
    FireIntervention,
    DecisionPattern,
    PatternConfidence,
    DecisionType,
    DecisionOutcome
)

logger = logging.getLogger(__name__)


async def analyze_decision_patterns(
    decision_events: List[DecisionEvent],
    pattern_types: Optional[List[str]] = None,
    min_frequency: int = 3
) -> List[DecisionPattern]:
    """
    Analyze decision events to identify recurring patterns.
    
    Args:
        decision_events: List of decision events to analyze
        pattern_types: Optional filter for specific pattern types
        min_frequency: Minimum frequency for a pattern to be considered
        
    Returns:
        List of identified decision patterns
    """
    try:
        logger.info(f"Analyzing patterns in {len(decision_events)} decision events")
        
        if len(decision_events) < min_frequency:
            logger.info("Insufficient events for pattern analysis")
            return []
        
        patterns = []
        
        # Analyze success/failure patterns by decision type
        type_patterns = await _analyze_decision_type_patterns(decision_events, min_frequency)
        patterns.extend(type_patterns)
        
        # Analyze temporal patterns
        temporal_patterns = await _analyze_temporal_patterns(decision_events, min_frequency)
        patterns.extend(temporal_patterns)
        
        # Analyze contextual patterns
        contextual_patterns = await _analyze_contextual_patterns(decision_events, min_frequency)
        patterns.extend(contextual_patterns)
        
        # Analyze agent-specific patterns
        agent_patterns = await _analyze_agent_patterns(decision_events, min_frequency)
        patterns.extend(agent_patterns)
        
        # Filter by pattern types if specified
        if pattern_types:
            patterns = [p for p in patterns if any(pt in p.pattern_type for pt in pattern_types)]
        
        # Sort patterns by confidence and frequency
        patterns.sort(key=lambda p: (p.confidence_level.value, p.frequency), reverse=True)
        
        logger.info(f"Identified {len(patterns)} decision patterns")
        
        return patterns
        
    except Exception as e:
        logger.error(f"Error analyzing decision patterns: {str(e)}")
        return []


async def identify_success_patterns(
    decision_events: List[DecisionEvent],
    success_threshold: float = 0.7
) -> List[DecisionPattern]:
    """
    Identify patterns associated with successful decisions.
    
    Args:
        decision_events: List of decision events to analyze
        success_threshold: Minimum success rate to consider a pattern
        
    Returns:
        List of success patterns
    """
    try:
        logger.info(f"Identifying success patterns from {len(decision_events)} events")
        
        success_patterns = []
        
        # Filter successful decisions
        successful_decisions = [
            d for d in decision_events 
            if d.decision_outcome == DecisionOutcome.SUCCESS
        ]
        
        if len(successful_decisions) < 3:
            return success_patterns
        
        # Group successful decisions by various attributes
        success_groups = {
            "by_agent": defaultdict(list),
            "by_type": defaultdict(list),
            "by_phase": defaultdict(list),
            "by_rationale_keywords": defaultdict(list)
        }
        
        # Populate success groups
        for decision in successful_decisions:
            success_groups["by_agent"][decision.decision_agent].append(decision)
            success_groups["by_type"][decision.decision_type.value].append(decision)
            success_groups["by_phase"][decision.phase_context or "unknown"].append(decision)
            
            # Extract keywords from rationale
            keywords = _extract_keywords_from_rationale(decision.decision_rationale)
            for keyword in keywords:
                success_groups["by_rationale_keywords"][keyword].append(decision)
        
        # Analyze each group for patterns
        for group_type, groups in success_groups.items():
            for group_key, group_decisions in groups.items():
                if len(group_decisions) >= 3:  # Minimum for pattern
                    # Calculate success rate for this group
                    total_decisions_in_group = len([
                        d for d in decision_events
                        if _decision_matches_group(d, group_type, group_key)
                    ])
                    
                    if total_decisions_in_group > 0:
                        success_rate = len(group_decisions) / total_decisions_in_group
                        
                        if success_rate >= success_threshold:
                            pattern = _create_success_pattern(
                                group_type, group_key, group_decisions, success_rate
                            )
                            success_patterns.append(pattern)
        
        # Sort by success rate and frequency
        success_patterns.sort(key=lambda p: (p.success_rate, p.frequency), reverse=True)
        
        logger.info(f"Identified {len(success_patterns)} success patterns")
        
        return success_patterns[:10]  # Top 10 patterns
        
    except Exception as e:
        logger.error(f"Error identifying success patterns: {str(e)}")
        return []


async def identify_failure_patterns(
    decision_events: List[DecisionEvent],
    failure_threshold: float = 0.3
) -> List[DecisionPattern]:
    """
    Identify patterns associated with failed decisions.
    
    Args:
        decision_events: List of decision events to analyze
        failure_threshold: Maximum success rate to consider a failure pattern
        
    Returns:
        List of failure patterns
    """
    try:
        logger.info(f"Identifying failure patterns from {len(decision_events)} events")
        
        failure_patterns = []
        
        # Filter failed decisions
        failed_decisions = [
            d for d in decision_events 
            if d.decision_outcome == DecisionOutcome.FAILURE
        ]
        
        if len(failed_decisions) < 2:
            return failure_patterns
        
        # Group failed decisions by various attributes
        failure_groups = {
            "by_agent": defaultdict(list),
            "by_type": defaultdict(list),
            "by_phase": defaultdict(list),
            "by_error_keywords": defaultdict(list)
        }
        
        # Populate failure groups
        for decision in failed_decisions:
            failure_groups["by_agent"][decision.decision_agent].append(decision)
            failure_groups["by_type"][decision.decision_type.value].append(decision)
            failure_groups["by_phase"][decision.phase_context or "unknown"].append(decision)
            
            # Extract error keywords from failure factors
            error_keywords = _extract_error_keywords(decision)
            for keyword in error_keywords:
                failure_groups["by_error_keywords"][keyword].append(decision)
        
        # Analyze each group for failure patterns
        for group_type, groups in failure_groups.items():
            for group_key, group_decisions in groups.items():
                if len(group_decisions) >= 2:  # Minimum for failure pattern
                    # Calculate failure rate for this group
                    total_decisions_in_group = len([
                        d for d in decision_events
                        if _decision_matches_group(d, group_type, group_key)
                    ])
                    
                    if total_decisions_in_group > 0:
                        failure_rate = len(group_decisions) / total_decisions_in_group
                        success_rate = 1.0 - failure_rate
                        
                        if success_rate <= failure_threshold:
                            pattern = _create_failure_pattern(
                                group_type, group_key, group_decisions, success_rate
                            )
                            failure_patterns.append(pattern)
        
        # Sort by failure frequency and failure rate
        failure_patterns.sort(key=lambda p: (p.frequency, 1.0 - p.success_rate), reverse=True)
        
        logger.info(f"Identified {len(failure_patterns)} failure patterns")
        
        return failure_patterns[:5]  # Top 5 failure patterns
        
    except Exception as e:
        logger.error(f"Error identifying failure patterns: {str(e)}")
        return []


def calculate_pattern_confidence(
    pattern: DecisionPattern,
    total_events: int,
    time_span: timedelta
) -> PatternConfidence:
    """
    Calculate confidence level for a decision pattern.
    
    Args:
        pattern: Decision pattern to evaluate
        total_events: Total number of events in the dataset
        time_span: Time span of the data
        
    Returns:
        Pattern confidence level
    """
    try:
        # Factors affecting confidence
        frequency_score = min(pattern.frequency / 10, 1.0)  # Normalize to 10 events
        success_rate_score = pattern.success_rate
        data_size_score = min(total_events / 50, 1.0)  # Normalize to 50 events
        time_span_score = min(time_span.days / 30, 1.0)  # Normalize to 30 days
        
        # Combined confidence score
        confidence_score = (
            frequency_score * 0.3 +
            success_rate_score * 0.3 +
            data_size_score * 0.2 +
            time_span_score * 0.2
        )
        
        # Convert to confidence level
        if confidence_score >= 0.8:
            return PatternConfidence.HIGH
        elif confidence_score >= 0.6:
            return PatternConfidence.MEDIUM
        elif confidence_score >= 0.3:
            return PatternConfidence.LOW
        else:
            return PatternConfidence.INSUFFICIENT_DATA
            
    except Exception as e:
        logger.error(f"Error calculating pattern confidence: {str(e)}")
        return PatternConfidence.LOW


# Helper functions for pattern analysis

async def _analyze_decision_type_patterns(
    decision_events: List[DecisionEvent],
    min_frequency: int
) -> List[DecisionPattern]:
    """Analyze patterns by decision type."""
    patterns = []
    
    # Group by decision type
    type_groups = defaultdict(list)
    for decision in decision_events:
        type_groups[decision.decision_type].append(decision)
    
    # Analyze each type
    for decision_type, decisions in type_groups.items():
        if len(decisions) >= min_frequency:
            # Calculate success rate
            successes = len([d for d in decisions if d.decision_outcome == DecisionOutcome.SUCCESS])
            success_rate = successes / len(decisions)
            
            # Determine pattern type
            if success_rate >= 0.7:
                pattern_type = "success_pattern"
                pattern_name = f"Successful {decision_type.value}"
            elif success_rate <= 0.3:
                pattern_type = "failure_pattern"
                pattern_name = f"Problematic {decision_type.value}"
            else:
                pattern_type = "neutral_pattern"
                pattern_name = f"Mixed {decision_type.value}"
            
            # Create pattern
            pattern = DecisionPattern(
                pattern_id=f"type_{decision_type.value}",
                pattern_type=pattern_type,
                pattern_name=pattern_name,
                pattern_description=f"{decision_type.value} decisions show {success_rate:.0%} success rate",
                decision_types=[decision_type],
                contexts=list(set(d.phase_context for d in decisions if d.phase_context)),
                frequency=len(decisions),
                success_rate=success_rate,
                preconditions=[f"Decision type: {decision_type.value}"],
                outcomes=_analyze_common_outcomes(decisions),
                confidence_level=PatternConfidence.MEDIUM,
                first_observed=min(d.timestamp for d in decisions),
                last_observed=max(d.timestamp for d in decisions),
                recommendations=_generate_type_recommendations(decision_type, success_rate),
                supporting_events=[d.event_id for d in decisions]
            )
            
            patterns.append(pattern)
    
    return patterns


async def _analyze_temporal_patterns(
    decision_events: List[DecisionEvent],
    min_frequency: int
) -> List[DecisionPattern]:
    """Analyze temporal patterns in decisions."""
    patterns = []
    
    if len(decision_events) < min_frequency:
        return patterns
    
    # Sort by timestamp
    sorted_events = sorted(decision_events, key=lambda x: x.timestamp)
    
    # Analyze time-of-day patterns
    hour_success_rates = _analyze_hour_patterns(sorted_events)
    for hour, (count, success_rate) in hour_success_rates.items():
        if count >= min_frequency and (success_rate >= 0.8 or success_rate <= 0.2):
            pattern_type = "success_pattern" if success_rate >= 0.8 else "failure_pattern"
            pattern = DecisionPattern(
                pattern_id=f"temporal_hour_{hour}",
                pattern_type=pattern_type,
                pattern_name=f"Hour {hour} Pattern",
                pattern_description=f"Decisions at hour {hour} show {success_rate:.0%} success rate",
                decision_types=[],
                contexts=["temporal"],
                frequency=count,
                success_rate=success_rate,
                preconditions=[f"Decision time: hour {hour}"],
                outcomes=[f"{success_rate:.0%} success rate"],
                confidence_level=PatternConfidence.LOW,
                first_observed=min(d.timestamp for d in sorted_events),
                last_observed=max(d.timestamp for d in sorted_events),
                recommendations=[f"{'Favor' if success_rate >= 0.8 else 'Avoid'} decisions around hour {hour}"]
            )
            patterns.append(pattern)
    
    return patterns


async def _analyze_contextual_patterns(
    decision_events: List[DecisionEvent],
    min_frequency: int
) -> List[DecisionPattern]:
    """Analyze patterns based on decision context."""
    patterns = []
    
    # Group by phase context
    phase_groups = defaultdict(list)
    for decision in decision_events:
        phase = decision.phase_context or "unknown"
        phase_groups[phase].append(decision)
    
    # Analyze each phase
    for phase, decisions in phase_groups.items():
        if len(decisions) >= min_frequency:
            successes = len([d for d in decisions if d.decision_outcome == DecisionOutcome.SUCCESS])
            success_rate = successes / len(decisions)
            
            pattern = DecisionPattern(
                pattern_id=f"context_{phase}",
                pattern_type="context_pattern",
                pattern_name=f"{phase} Context Pattern",
                pattern_description=f"{phase} decisions show {success_rate:.0%} success rate",
                decision_types=list(set(d.decision_type for d in decisions)),
                contexts=[phase],
                frequency=len(decisions),
                success_rate=success_rate,
                preconditions=[f"Phase context: {phase}"],
                outcomes=_analyze_common_outcomes(decisions),
                confidence_level=PatternConfidence.MEDIUM,
                first_observed=min(d.timestamp for d in decisions),
                last_observed=max(d.timestamp for d in decisions),
                recommendations=_generate_context_recommendations(phase, success_rate)
            )
            
            patterns.append(pattern)
    
    return patterns


async def _analyze_agent_patterns(
    decision_events: List[DecisionEvent],
    min_frequency: int
) -> List[DecisionPattern]:
    """Analyze patterns specific to decision agents."""
    patterns = []
    
    # Group by agent
    agent_groups = defaultdict(list)
    for decision in decision_events:
        agent_groups[decision.decision_agent].append(decision)
    
    # Analyze each agent
    for agent, decisions in agent_groups.items():
        if len(decisions) >= min_frequency:
            successes = len([d for d in decisions if d.decision_outcome == DecisionOutcome.SUCCESS])
            success_rate = successes / len(decisions)
            
            # Analyze agent-specific characteristics
            common_rationales = _find_common_rationales(decisions)
            
            pattern = DecisionPattern(
                pattern_id=f"agent_{agent}",
                pattern_type="agent_pattern",
                pattern_name=f"{agent} Agent Pattern",
                pattern_description=f"{agent} decisions show {success_rate:.0%} success rate",
                decision_types=list(set(d.decision_type for d in decisions)),
                contexts=list(set(d.phase_context for d in decisions if d.phase_context)),
                frequency=len(decisions),
                success_rate=success_rate,
                preconditions=[f"Decision agent: {agent}"],
                outcomes=_analyze_common_outcomes(decisions),
                confidence_level=PatternConfidence.MEDIUM,
                first_observed=min(d.timestamp for d in decisions),
                last_observed=max(d.timestamp for d in decisions),
                recommendations=_generate_agent_recommendations(agent, success_rate, common_rationales)
            )
            
            patterns.append(pattern)
    
    return patterns


def _extract_keywords_from_rationale(rationale: str) -> List[str]:
    """Extract key terms from decision rationale."""
    keywords = []
    
    # Common decision-related keywords
    keyword_patterns = [
        "complexity", "performance", "optimization", "refinement",
        "decomposition", "strategy", "validation", "improvement",
        "critical", "urgent", "necessary", "optional"
    ]
    
    rationale_lower = rationale.lower()
    for keyword in keyword_patterns:
        if keyword in rationale_lower:
            keywords.append(keyword)
    
    return keywords


def _extract_error_keywords(decision: DecisionEvent) -> List[str]:
    """Extract error-related keywords from decision."""
    keywords = []
    
    # Check failure factors
    for factor in decision.failure_factors:
        factor_lower = factor.lower()
        if "timeout" in factor_lower:
            keywords.append("timeout")
        elif "complexity" in factor_lower:
            keywords.append("complexity_error")
        elif "validation" in factor_lower:
            keywords.append("validation_error")
        elif "resource" in factor_lower:
            keywords.append("resource_error")
    
    # Check decision details for error indicators
    details_str = str(decision.decision_details).lower()
    if "error" in details_str:
        keywords.append("general_error")
    if "failed" in details_str:
        keywords.append("failure")
    
    return keywords


def _decision_matches_group(decision: DecisionEvent, group_type: str, group_key: str) -> bool:
    """Check if a decision matches a specific group criteria."""
    if group_type == "by_agent":
        return decision.decision_agent == group_key
    elif group_type == "by_type":
        return decision.decision_type.value == group_key
    elif group_type == "by_phase":
        return (decision.phase_context or "unknown") == group_key
    elif group_type == "by_rationale_keywords":
        return group_key in decision.decision_rationale.lower()
    elif group_type == "by_error_keywords":
        error_keywords = _extract_error_keywords(decision)
        return group_key in error_keywords
    
    return False


def _create_success_pattern(
    group_type: str,
    group_key: str,
    decisions: List[DecisionEvent],
    success_rate: float
) -> DecisionPattern:
    """Create a success pattern from grouped decisions."""
    pattern_name = f"Successful {group_key}"
    pattern_description = f"{group_key} shows {success_rate:.0%} success rate"
    
    return DecisionPattern(
        pattern_id=f"success_{group_type}_{group_key}",
        pattern_type="success_pattern",
        pattern_name=pattern_name,
        pattern_description=pattern_description,
        decision_types=list(set(d.decision_type for d in decisions)),
        contexts=list(set(d.phase_context for d in decisions if d.phase_context)),
        frequency=len(decisions),
        success_rate=success_rate,
        preconditions=[f"{group_type}: {group_key}"],
        outcomes=_analyze_common_outcomes(decisions),
        confidence_level=PatternConfidence.MEDIUM,
        first_observed=min(d.timestamp for d in decisions),
        last_observed=max(d.timestamp for d in decisions),
        recommendations=[f"Continue using {group_key} approach"],
        supporting_events=[d.event_id for d in decisions]
    )


def _create_failure_pattern(
    group_type: str,
    group_key: str,
    decisions: List[DecisionEvent],
    success_rate: float
) -> DecisionPattern:
    """Create a failure pattern from grouped decisions."""
    pattern_name = f"Problematic {group_key}"
    pattern_description = f"{group_key} shows only {success_rate:.0%} success rate"
    
    return DecisionPattern(
        pattern_id=f"failure_{group_type}_{group_key}",
        pattern_type="failure_pattern",
        pattern_name=pattern_name,
        pattern_description=pattern_description,
        decision_types=list(set(d.decision_type for d in decisions)),
        contexts=list(set(d.phase_context for d in decisions if d.phase_context)),
        frequency=len(decisions),
        success_rate=success_rate,
        preconditions=[f"{group_type}: {group_key}"],
        outcomes=_analyze_common_outcomes(decisions),
        confidence_level=PatternConfidence.MEDIUM,
        first_observed=min(d.timestamp for d in decisions),
        last_observed=max(d.timestamp for d in decisions),
        recommendations=[f"Avoid or revise {group_key} approach"],
        anti_patterns=[f"Avoid {group_key} in similar contexts"],
        supporting_events=[d.event_id for d in decisions]
    )


def _analyze_common_outcomes(decisions: List[DecisionEvent]) -> List[str]:
    """Analyze common outcomes across decisions."""
    outcomes = []
    
    # Count outcome types
    outcome_counts = Counter(d.decision_outcome for d in decisions)
    total = len(decisions)
    
    for outcome, count in outcome_counts.items():
        percentage = (count / total) * 100
        outcomes.append(f"{outcome.value}: {percentage:.0f}%")
    
    return outcomes


def _analyze_hour_patterns(events: List[DecisionEvent]) -> Dict[int, Tuple[int, float]]:
    """Analyze success patterns by hour of day."""
    hour_data = defaultdict(lambda: {"total": 0, "success": 0})
    
    for event in events:
        hour = event.timestamp.hour
        hour_data[hour]["total"] += 1
        if event.decision_outcome == DecisionOutcome.SUCCESS:
            hour_data[hour]["success"] += 1
    
    # Calculate success rates
    hour_success_rates = {}
    for hour, data in hour_data.items():
        if data["total"] > 0:
            success_rate = data["success"] / data["total"]
            hour_success_rates[hour] = (data["total"], success_rate)
    
    return hour_success_rates


def _find_common_rationales(decisions: List[DecisionEvent]) -> List[str]:
    """Find common rationale patterns across decisions."""
    rationale_keywords = []
    
    for decision in decisions:
        keywords = _extract_keywords_from_rationale(decision.decision_rationale)
        rationale_keywords.extend(keywords)
    
    # Find most common keywords
    keyword_counts = Counter(rationale_keywords)
    common_keywords = [kw for kw, count in keyword_counts.most_common(3)]
    
    return common_keywords


def _generate_type_recommendations(decision_type: DecisionType, success_rate: float) -> List[str]:
    """Generate recommendations based on decision type patterns."""
    recommendations = []
    
    if success_rate >= 0.8:
        recommendations.append(f"Continue current approach for {decision_type.value} decisions")
    elif success_rate <= 0.3:
        recommendations.append(f"Review and revise {decision_type.value} decision process")
        recommendations.append(f"Consider additional validation for {decision_type.value}")
    else:
        recommendations.append(f"Monitor {decision_type.value} decisions more closely")
    
    return recommendations


def _generate_context_recommendations(phase: str, success_rate: float) -> List[str]:
    """Generate recommendations based on phase context patterns."""
    recommendations = []
    
    if success_rate >= 0.8:
        recommendations.append(f"{phase} context shows strong performance")
    elif success_rate <= 0.3:
        recommendations.append(f"Review {phase} decision-making process")
        recommendations.append(f"Consider additional {phase} validation steps")
    
    return recommendations


def _generate_agent_recommendations(agent: str, success_rate: float, common_rationales: List[str]) -> List[str]:
    """Generate recommendations based on agent patterns."""
    recommendations = []
    
    if success_rate >= 0.8:
        recommendations.append(f"{agent} shows excellent decision performance")
        if common_rationales:
            recommendations.append(f"Continue leveraging {', '.join(common_rationales[:2])} approaches")
    elif success_rate <= 0.3:
        recommendations.append(f"Review {agent} decision-making algorithms")
        if common_rationales:
            recommendations.append(f"Examine {', '.join(common_rationales[:2])} decision factors")
    
    return recommendations