"""
Air Agent: Historical Context Provider for Decision-Making Agents

The Air Agent serves as a system resource agent that provides historical context
to critical decision-making agents throughout the FFTT system. It tracks decision
events, analyzes patterns, and provides relevant historical insights to support
better decision-making.

Core responsibilities:
1. Track decision events by refinement agents
2. Analyze historical patterns and outcomes
3. Provide relevant context to decision makers
4. Support Fire agent decomposition decisions with historical data

Usage:
    from resources.air_agent import (
        provide_refinement_context,
        provide_fire_context,
        track_decision_event,
        track_fire_intervention
    )
"""

from .history_tracker import (
    track_decision_event,
    track_refinement_cycle,
    track_fire_intervention,
    get_decision_history,
    clear_old_history
)

from .context_provider import (
    provide_refinement_context,
    provide_fire_context,
    provide_evolution_context,
    provide_natural_selection_context,
    analyze_cross_phase_patterns
)

from .models import (
    DecisionEvent,
    FireIntervention,
    HistoricalContext,
    DecisionPattern,
    AirAgentConfig
)

from .pattern_analyzer import (
    analyze_decision_patterns,
    identify_success_patterns,
    identify_failure_patterns,
    calculate_pattern_confidence
)

__all__ = [
    # History tracking functions
    'track_decision_event',
    'track_refinement_cycle',
    'track_fire_intervention',
    'get_decision_history',
    'clear_old_history',
    
    # Context provision functions
    'provide_refinement_context',
    'provide_fire_context',
    'provide_evolution_context',
    'provide_natural_selection_context',
    'analyze_cross_phase_patterns',
    
    # Pattern analysis functions
    'analyze_decision_patterns',
    'identify_success_patterns',
    'identify_failure_patterns',
    'calculate_pattern_confidence',
    
    # Data models
    'DecisionEvent',
    'FireIntervention',
    'HistoricalContext',
    'DecisionPattern',
    'AirAgentConfig'
]