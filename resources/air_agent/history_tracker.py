"""
Air Agent history tracking functionality.

This module handles tracking of decision events, Fire agent interventions,
and other system events to build a historical knowledge base for context provision.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json

from .models import (
    DecisionEvent,
    FireIntervention,
    DecisionType,
    DecisionOutcome,
    AirAgentConfig,
    EffectivenessTracking
)

logger = logging.getLogger(__name__)


async def track_decision_event(
    decision_agent: str,  # "garden_foundation_refinement", "natural_selection", "evolution"
    decision_type: str,
    decision_details: Dict[str, Any],
    decision_outcome: Dict[str, Any],
    state_manager=None,
    health_tracker=None,
    operation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Track major decision events by refinement agents.
    
    This is the primary entry point for tracking decisions made by
    Garden Foundation Refinement Agent, Natural Selection Agent, and Evolution Agent.
    
    Args:
        decision_agent: Name of the agent making the decision
        decision_type: Type of decision (as string, converted to enum)
        decision_details: Details about the decision made
        decision_outcome: Outcome of the decision
        state_manager: Optional state manager for persistence
        health_tracker: Optional health tracker for monitoring
        operation_id: Optional operation identifier
        
    Returns:
        Tracking result with event ID and metadata
    """
    try:
        logger.info(f"Tracking decision event: {decision_agent} - {decision_type}")
        
        # Convert string decision type to enum
        decision_type_enum = _convert_decision_type(decision_type)
        
        # Generate unique event ID
        event_id = f"decision_{decision_agent}_{datetime.now().isoformat()}_{id(decision_details)}"
        
        # Extract decision context
        input_context = decision_details.get("input_context", {})
        decision_rationale = decision_details.get("rationale", "No rationale provided")
        phase_context = decision_details.get("phase_context", _infer_phase_context(decision_agent))
        
        # Determine initial outcome
        initial_outcome = _determine_initial_outcome(decision_outcome)
        
        # Create decision event
        decision_event = DecisionEvent(
            event_id=event_id,
            decision_agent=decision_agent,
            decision_type=decision_type_enum,
            timestamp=datetime.now(),
            input_context=input_context,
            decision_rationale=decision_rationale,
            decision_details=decision_details,
            decision_outcome=initial_outcome,
            operation_id=operation_id,
            phase_context=phase_context
        )
        
        # Store decision event if state manager available
        if state_manager:
            await _store_decision_event(state_manager, decision_event)
        
        # Track decision metrics if health tracker available
        if health_tracker:
            await _track_decision_health(health_tracker, decision_event)
        
        # Schedule effectiveness tracking
        await _schedule_effectiveness_tracking(decision_event, state_manager)
        
        logger.info(f"Decision event tracked successfully: {event_id}")
        
        return {
            "success": True,
            "event_id": event_id,
            "tracking_timestamp": datetime.now().isoformat(),
            "agent": decision_agent,
            "decision_type": decision_type,
            "phase_context": phase_context
        }
        
    except Exception as e:
        logger.error(f"Error tracking decision event: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


async def track_refinement_cycle(
    refinement_agent: str,
    cycle_details: Dict[str, Any],
    cycle_outcome: Dict[str, Any],
    state_manager=None,
    health_tracker=None,
    operation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Track complete refinement cycles for pattern analysis.
    
    Args:
        refinement_agent: Name of the refinement agent
        cycle_details: Details about the refinement cycle
        cycle_outcome: Outcome of the refinement cycle
        state_manager: Optional state manager for persistence
        health_tracker: Optional health tracker for monitoring
        operation_id: Optional operation identifier
        
    Returns:
        Tracking result with cycle metadata
    """
    try:
        logger.info(f"Tracking refinement cycle: {refinement_agent}")
        
        # Track refinement decision events
        decision_events = []
        
        # Track necessity decision
        necessity_result = await track_decision_event(
            decision_agent=refinement_agent,
            decision_type="refinement_necessity",
            decision_details={
                "input_context": cycle_details.get("initial_analysis", {}),
                "rationale": cycle_details.get("necessity_rationale", ""),
                "phase_context": cycle_details.get("phase_context", "")
            },
            decision_outcome=cycle_outcome.get("necessity_outcome", {}),
            state_manager=state_manager,
            health_tracker=health_tracker,
            operation_id=operation_id
        )
        decision_events.append(necessity_result["event_id"])
        
        # Track strategy decision if refinement was necessary
        if cycle_outcome.get("refinement_necessary", False):
            strategy_result = await track_decision_event(
                decision_agent=refinement_agent,
                decision_type="refinement_strategy",
                decision_details={
                    "input_context": cycle_details.get("strategy_analysis", {}),
                    "rationale": cycle_details.get("strategy_rationale", ""),
                    "phase_context": cycle_details.get("phase_context", "")
                },
                decision_outcome=cycle_outcome.get("strategy_outcome", {}),
                state_manager=state_manager,
                health_tracker=health_tracker,
                operation_id=operation_id
            )
            decision_events.append(strategy_result["event_id"])
        
        # Create cycle summary
        cycle_summary = {
            "cycle_id": f"cycle_{refinement_agent}_{datetime.now().isoformat()}",
            "refinement_agent": refinement_agent,
            "operation_id": operation_id,
            "decision_events": decision_events,
            "cycle_start": cycle_details.get("start_time", datetime.now().isoformat()),
            "cycle_end": datetime.now().isoformat(),
            "refinement_necessary": cycle_outcome.get("refinement_necessary", False),
            "refinement_successful": cycle_outcome.get("refinement_successful", False),
            "iterations_required": cycle_outcome.get("iterations", 1),
            "lessons_learned": cycle_outcome.get("lessons_learned", [])
        }
        
        # Store cycle summary
        if state_manager:
            await _store_refinement_cycle(state_manager, cycle_summary)
        
        return {
            "success": True,
            "cycle_id": cycle_summary["cycle_id"],
            "decision_events": decision_events,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error tracking refinement cycle: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


async def track_fire_intervention(
    intervention_context: str,  # "phase_one_guideline", "phase_three_feature"
    complexity_details: Dict[str, Any],
    decomposition_result: Dict[str, Any],
    state_manager=None,
    health_tracker=None,
    operation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Track Fire agent complexity reduction interventions.
    
    This function tracks when Fire agent performs complexity decomposition
    to build knowledge about effective decomposition strategies.
    
    Args:
        intervention_context: Context of the intervention
        complexity_details: Details about the complexity that triggered intervention
        decomposition_result: Result of the Fire agent decomposition
        state_manager: Optional state manager for persistence
        health_tracker: Optional health tracker for monitoring
        operation_id: Optional operation identifier
        
    Returns:
        Tracking result with intervention metadata
    """
    try:
        logger.info(f"Tracking Fire agent intervention: {intervention_context}")
        
        # Generate unique intervention ID
        intervention_id = f"fire_{intervention_context}_{datetime.now().isoformat()}"
        
        # Extract intervention details
        original_score = complexity_details.get("complexity_score", 0.0)
        final_score = decomposition_result.get("new_complexity_score", None)
        complexity_reduction = decomposition_result.get("complexity_reduction", None)
        strategy = decomposition_result.get("strategy_used", "unknown")
        success = decomposition_result.get("success", False)
        
        # Calculate intervention duration
        start_time = complexity_details.get("analysis_timestamp")
        end_time = decomposition_result.get("decomposition_timestamp")
        intervention_duration = None
        
        if start_time and end_time:
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time)
            intervention_duration = end_time - start_time
        
        # Extract learning data
        lessons_learned = decomposition_result.get("lessons_learned", [])
        effective_techniques = _extract_effective_techniques(decomposition_result)
        challenges = decomposition_result.get("warnings", [])
        
        # Create Fire intervention record
        fire_intervention = FireIntervention(
            intervention_id=intervention_id,
            intervention_context=intervention_context,
            timestamp=datetime.now(),
            original_complexity_score=original_score,
            final_complexity_score=final_score,
            complexity_reduction=complexity_reduction,
            decomposition_strategy=str(strategy),
            success=success,
            intervention_duration=intervention_duration,
            lessons_learned=lessons_learned,
            effective_techniques=effective_techniques,
            challenges_encountered=challenges,
            operation_id=operation_id
        )
        
        # Store Fire intervention if state manager available
        if state_manager:
            await _store_fire_intervention(state_manager, fire_intervention)
        
        # Track Fire metrics if health tracker available
        if health_tracker:
            await _track_fire_health(health_tracker, fire_intervention)
        
        # Also track as a decision event for cross-referencing
        decision_result = await track_decision_event(
            decision_agent="fire_agent",
            decision_type="complexity_intervention",
            decision_details={
                "input_context": complexity_details,
                "rationale": f"Complexity score {original_score} exceeded threshold",
                "phase_context": intervention_context
            },
            decision_outcome={
                "intervention_success": success,
                "complexity_reduction": complexity_reduction,
                "strategy_used": str(strategy)
            },
            state_manager=state_manager,
            health_tracker=health_tracker,
            operation_id=operation_id
        )
        
        # Link decision event to Fire intervention
        fire_intervention.triggering_decision = decision_result.get("event_id")
        
        logger.info(f"Fire intervention tracked successfully: {intervention_id}")
        
        return {
            "success": True,
            "intervention_id": intervention_id,
            "decision_event_id": decision_result.get("event_id"),
            "complexity_reduction": complexity_reduction,
            "strategy_used": str(strategy),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error tracking Fire intervention: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


async def get_decision_history(
    agent_filter: Optional[str] = None,
    decision_type_filter: Optional[str] = None,
    phase_filter: Optional[str] = None,
    lookback_period: Optional[timedelta] = None,
    max_events: int = 100,
    state_manager=None
) -> List[DecisionEvent]:
    """
    Retrieve decision history with optional filtering.
    
    Args:
        agent_filter: Filter by specific agent name
        decision_type_filter: Filter by decision type
        phase_filter: Filter by phase context
        lookback_period: Time period to look back
        max_events: Maximum number of events to return
        state_manager: State manager for data retrieval
        
    Returns:
        List of decision events matching criteria
    """
    try:
        if not state_manager:
            logger.warning("No state manager provided for decision history retrieval")
            return []
        
        # Get all decision event keys
        decision_keys = await _get_decision_event_keys(state_manager, lookback_period)
        
        # Retrieve and filter decision events
        decision_events = []
        for key in decision_keys[:max_events * 2]:  # Get extra in case of filtering
            try:
                event_data = await state_manager.get_state(key, "STATE")
                if event_data:
                    decision_event = _deserialize_decision_event(event_data)
                    
                    # Apply filters
                    if agent_filter and decision_event.decision_agent != agent_filter:
                        continue
                    if decision_type_filter and decision_event.decision_type.value != decision_type_filter:
                        continue
                    if phase_filter and decision_event.phase_context != phase_filter:
                        continue
                    
                    decision_events.append(decision_event)
                    
                    if len(decision_events) >= max_events:
                        break
                        
            except Exception as e:
                logger.warning(f"Error retrieving decision event {key}: {e}")
                continue
        
        # Sort by timestamp (most recent first)
        decision_events.sort(key=lambda x: x.timestamp, reverse=True)
        
        return decision_events[:max_events]
        
    except Exception as e:
        logger.error(f"Error retrieving decision history: {str(e)}")
        return []


async def clear_old_history(
    retention_days: int = 90,
    state_manager=None,
    health_tracker=None
) -> Dict[str, Any]:
    """
    Clear old decision history and Fire interventions to manage storage.
    
    Args:
        retention_days: Number of days to retain history
        state_manager: State manager for data cleanup
        health_tracker: Optional health tracker for monitoring
        
    Returns:
        Cleanup result with statistics
    """
    try:
        if not state_manager:
            return {"success": False, "error": "No state manager provided"}
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        # Clean up decision events
        decision_keys = await _get_decision_event_keys(state_manager, None)
        decisions_cleaned = 0
        
        for key in decision_keys:
            try:
                event_data = await state_manager.get_state(key, "STATE")
                if event_data:
                    event_timestamp = datetime.fromisoformat(event_data.get("timestamp", ""))
                    if event_timestamp < cutoff_date:
                        await state_manager.delete_state(key, "STATE")
                        decisions_cleaned += 1
            except Exception as e:
                logger.warning(f"Error cleaning decision event {key}: {e}")
        
        # Clean up Fire interventions
        fire_keys = await _get_fire_intervention_keys(state_manager, None)
        interventions_cleaned = 0
        
        for key in fire_keys:
            try:
                intervention_data = await state_manager.get_state(key, "STATE")
                if intervention_data:
                    intervention_timestamp = datetime.fromisoformat(intervention_data.get("timestamp", ""))
                    if intervention_timestamp < cutoff_date:
                        await state_manager.delete_state(key, "STATE")
                        interventions_cleaned += 1
            except Exception as e:
                logger.warning(f"Error cleaning Fire intervention {key}: {e}")
        
        # Track cleanup metrics
        if health_tracker:
            health_tracker.track_metric("air_agent_decisions_cleaned", decisions_cleaned)
            health_tracker.track_metric("air_agent_interventions_cleaned", interventions_cleaned)
        
        cleanup_result = {
            "success": True,
            "decisions_cleaned": decisions_cleaned,
            "interventions_cleaned": interventions_cleaned,
            "cutoff_date": cutoff_date.isoformat(),
            "cleanup_timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"History cleanup complete: {decisions_cleaned} decisions, {interventions_cleaned} interventions removed")
        
        return cleanup_result
        
    except Exception as e:
        logger.error(f"Error clearing old history: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# Helper functions for decision tracking

def _convert_decision_type(decision_type_str: str) -> DecisionType:
    """Convert string decision type to enum."""
    type_mapping = {
        "refinement_necessity": DecisionType.REFINEMENT_NECESSITY,
        "refinement_strategy": DecisionType.REFINEMENT_STRATEGY,
        "complexity_intervention": DecisionType.COMPLEXITY_INTERVENTION,
        "feature_evolution": DecisionType.FEATURE_EVOLUTION,
        "natural_selection": DecisionType.NATURAL_SELECTION,
        "architectural_change": DecisionType.ARCHITECTURAL_CHANGE,
        "decomposition_strategy": DecisionType.DECOMPOSITION_STRATEGY
    }
    
    return type_mapping.get(decision_type_str, DecisionType.ARCHITECTURAL_CHANGE)


def _infer_phase_context(decision_agent: str) -> str:
    """Infer phase context from decision agent name."""
    agent_phase_map = {
        "garden_foundation_refinement": "phase_one",
        "natural_selection": "phase_three",
        "evolution": "phase_zero",
        "fire_agent": "system_wide"
    }
    
    return agent_phase_map.get(decision_agent, "unknown")


def _determine_initial_outcome(decision_outcome: Dict[str, Any]) -> DecisionOutcome:
    """Determine initial decision outcome from result data."""
    if decision_outcome.get("success", False):
        return DecisionOutcome.SUCCESS
    elif decision_outcome.get("partial_success", False):
        return DecisionOutcome.PARTIAL_SUCCESS
    elif decision_outcome.get("deferred", False):
        return DecisionOutcome.DEFERRED
    elif "error" in decision_outcome:
        return DecisionOutcome.FAILURE
    else:
        return DecisionOutcome.UNKNOWN


def _extract_effective_techniques(decomposition_result: Dict[str, Any]) -> List[str]:
    """Extract effective techniques from decomposition result."""
    techniques = []
    
    if decomposition_result.get("success", False):
        strategy = decomposition_result.get("strategy_used", "")
        if strategy:
            techniques.append(f"Strategy: {strategy}")
        
        if decomposition_result.get("complexity_reduction", 0) > 20:
            techniques.append("High complexity reduction achieved")
        
        success_metrics = decomposition_result.get("success_metrics", {})
        if success_metrics.get("strategy_effectiveness") == "high":
            techniques.append("Strategy highly effective")
    
    return techniques


# Storage and retrieval helpers

async def _store_decision_event(state_manager, decision_event: DecisionEvent):
    """Store decision event in state manager."""
    try:
        key = f"air_agent:decision_event:{decision_event.event_id}"
        await state_manager.set_state(key, decision_event.__dict__, "STATE")
    except Exception as e:
        logger.warning(f"Failed to store decision event: {e}")


async def _store_refinement_cycle(state_manager, cycle_summary: Dict[str, Any]):
    """Store refinement cycle summary."""
    try:
        key = f"air_agent:refinement_cycle:{cycle_summary['cycle_id']}"
        await state_manager.set_state(key, cycle_summary, "STATE")
    except Exception as e:
        logger.warning(f"Failed to store refinement cycle: {e}")


async def _store_fire_intervention(state_manager, fire_intervention: FireIntervention):
    """Store Fire intervention in state manager."""
    try:
        key = f"air_agent:fire_intervention:{fire_intervention.intervention_id}"
        await state_manager.set_state(key, fire_intervention.__dict__, "STATE")
    except Exception as e:
        logger.warning(f"Failed to store Fire intervention: {e}")


async def _get_decision_event_keys(state_manager, lookback_period: Optional[timedelta]) -> List[str]:
    """Get decision event keys from state manager."""
    try:
        # This is a simplified implementation - in practice would use state manager's query capabilities
        all_keys = await state_manager.list_keys("air_agent:decision_event:")
        
        if lookback_period:
            cutoff_time = datetime.now() - lookback_period
            filtered_keys = []
            
            for key in all_keys:
                try:
                    event_data = await state_manager.get_state(key, "STATE")
                    if event_data:
                        event_timestamp = datetime.fromisoformat(event_data.get("timestamp", ""))
                        if event_timestamp >= cutoff_time:
                            filtered_keys.append(key)
                except Exception:
                    continue
            
            return filtered_keys
        
        return all_keys
        
    except Exception as e:
        logger.warning(f"Error getting decision event keys: {e}")
        return []


async def _get_fire_intervention_keys(state_manager, lookback_period: Optional[timedelta]) -> List[str]:
    """Get Fire intervention keys from state manager."""
    try:
        all_keys = await state_manager.list_keys("air_agent:fire_intervention:")
        
        if lookback_period:
            cutoff_time = datetime.now() - lookback_period
            filtered_keys = []
            
            for key in all_keys:
                try:
                    intervention_data = await state_manager.get_state(key, "STATE")
                    if intervention_data:
                        intervention_timestamp = datetime.fromisoformat(intervention_data.get("timestamp", ""))
                        if intervention_timestamp >= cutoff_time:
                            filtered_keys.append(key)
                except Exception:
                    continue
            
            return filtered_keys
        
        return all_keys
        
    except Exception as e:
        logger.warning(f"Error getting Fire intervention keys: {e}")
        return []


def _deserialize_decision_event(event_data: Dict[str, Any]) -> DecisionEvent:
    """Deserialize decision event from stored data."""
    # Convert string timestamp back to datetime
    timestamp = datetime.fromisoformat(event_data["timestamp"])
    outcome_timestamp = None
    if event_data.get("outcome_timestamp"):
        outcome_timestamp = datetime.fromisoformat(event_data["outcome_timestamp"])
    
    # Convert string decision type back to enum
    decision_type = DecisionType(event_data["decision_type"])
    decision_outcome = DecisionOutcome(event_data["decision_outcome"])
    
    return DecisionEvent(
        event_id=event_data["event_id"],
        decision_agent=event_data["decision_agent"],
        decision_type=decision_type,
        timestamp=timestamp,
        input_context=event_data["input_context"],
        decision_rationale=event_data["decision_rationale"],
        decision_details=event_data["decision_details"],
        decision_outcome=decision_outcome,
        effectiveness_score=event_data.get("effectiveness_score"),
        outcome_timestamp=outcome_timestamp,
        operation_id=event_data.get("operation_id"),
        phase_context=event_data.get("phase_context"),
        related_events=event_data.get("related_events", []),
        lessons_learned=event_data.get("lessons_learned", []),
        success_factors=event_data.get("success_factors", []),
        failure_factors=event_data.get("failure_factors", [])
    )


# Health tracking helpers

async def _track_decision_health(health_tracker, decision_event: DecisionEvent):
    """Track decision event metrics in health tracker."""
    try:
        health_tracker.track_metric("air_agent_decision_events", 1)
        health_tracker.track_metric(f"air_agent_decisions_{decision_event.decision_agent}", 1)
        health_tracker.track_metric(f"air_agent_decision_type_{decision_event.decision_type.value}", 1)
    except Exception as e:
        logger.warning(f"Failed to track decision health: {e}")


async def _track_fire_health(health_tracker, fire_intervention: FireIntervention):
    """Track Fire intervention metrics in health tracker."""
    try:
        health_tracker.track_metric("air_agent_fire_interventions", 1)
        health_tracker.track_metric("air_agent_fire_success", 1 if fire_intervention.success else 0)
        if fire_intervention.complexity_reduction:
            health_tracker.track_metric("air_agent_complexity_reduction_total", fire_intervention.complexity_reduction)
    except Exception as e:
        logger.warning(f"Failed to track Fire health: {e}")


# Effectiveness tracking

async def _schedule_effectiveness_tracking(decision_event: DecisionEvent, state_manager=None):
    """Schedule follow-up effectiveness tracking for a decision event."""
    try:
        if not state_manager:
            return
        
        # Create effectiveness tracking record
        tracking_record = EffectivenessTracking(
            tracking_id=f"effectiveness_{decision_event.event_id}",
            context_response_id=decision_event.event_id,
            decision_event_id=decision_event.event_id
        )
        
        # Store for later evaluation
        key = f"air_agent:effectiveness_tracking:{tracking_record.tracking_id}"
        await state_manager.set_state(key, tracking_record.__dict__, "STATE")
        
    except Exception as e:
        logger.warning(f"Failed to schedule effectiveness tracking: {e}")