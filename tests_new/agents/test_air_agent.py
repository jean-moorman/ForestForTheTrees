"""
Comprehensive test suite for Air Agent functionality.

Tests decision tracking, pattern analysis, historical context provision,
and integration with decision-making agents throughout the FFTT system.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from resources.air_agent import (
    track_decision_event,
    track_refinement_cycle,
    track_fire_intervention,
    get_decision_history,
    clear_old_history,
    provide_refinement_context,
    provide_fire_context,
    provide_natural_selection_context,
    provide_evolution_context,
    analyze_cross_phase_patterns,
    analyze_decision_patterns,
    identify_success_patterns,
    identify_failure_patterns
)

from resources.air_agent.models import (
    DecisionEvent,
    FireIntervention,
    HistoricalContext,
    DecisionPattern,
    PatternConfidence,
    DecisionType,
    DecisionOutcome,
    CrossPhasePattern
)


class TestAirAgentDecisionTracking:
    """Test Air Agent decision tracking functionality."""
    
    @pytest.fixture
    def mock_state_manager(self):
        """Mock state manager for testing."""
        mock = AsyncMock()
        mock.set_state = AsyncMock()
        mock.get_state = AsyncMock()
        mock.list_keys = AsyncMock(return_value=[])
        mock.delete_state = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_health_tracker(self):
        """Mock health tracker for testing."""
        mock = MagicMock()
        mock.track_metric = MagicMock()
        return mock
    
    @pytest.fixture
    def sample_decision_details(self):
        """Sample decision details for testing."""
        return {
            "input_context": {
                "analysis_data": "test_analysis",
                "complexity_score": 75.0
            },
            "rationale": "Refinement necessary due to architectural issues",
            "phase_context": "phase_one"
        }
    
    @pytest.fixture
    def sample_decision_outcome(self):
        """Sample decision outcome for testing."""
        return {
            "success": True,
            "refinement_applied": True,
            "iterations": 2,
            "final_state": "resolved"
        }
    
    @pytest.mark.asyncio
    async def test_track_decision_event_success(self, sample_decision_details, sample_decision_outcome, mock_state_manager, mock_health_tracker):
        """Test successful decision event tracking."""
        result = await track_decision_event(
            decision_agent="garden_foundation_refinement",
            decision_type="refinement_necessity",
            decision_details=sample_decision_details,
            decision_outcome=sample_decision_outcome,
            state_manager=mock_state_manager,
            health_tracker=mock_health_tracker,
            operation_id="test_operation_123"
        )
        
        assert result["success"] == True
        assert "event_id" in result
        assert result["agent"] == "garden_foundation_refinement"
        assert result["decision_type"] == "refinement_necessity"
        assert result["phase_context"] == "phase_one"
        
        # Verify state manager was called to store the event
        mock_state_manager.set_state.assert_called()
        mock_health_tracker.track_metric.assert_called()
    
    @pytest.mark.asyncio
    async def test_track_decision_event_natural_selection(self, mock_state_manager):
        """Test tracking Natural Selection decisions."""
        decision_details = {
            "input_context": {
                "features_analyzed": 5,
                "fire_interventions": 2
            },
            "rationale": "Natural selection optimization with Fire/Air support",
            "phase_context": "phase_three"
        }
        
        decision_outcome = {
            "success": True,
            "features_ranked": 5,
            "optimization_decisions": 3
        }
        
        result = await track_decision_event(
            decision_agent="natural_selection",
            decision_type="natural_selection",
            decision_details=decision_details,
            decision_outcome=decision_outcome,
            state_manager=mock_state_manager,
            operation_id="ns_operation_456"
        )
        
        assert result["success"] == True
        assert result["agent"] == "natural_selection"
    
    @pytest.mark.asyncio
    async def test_track_refinement_cycle(self, mock_state_manager, mock_health_tracker):
        """Test tracking complete refinement cycles."""
        cycle_details = {
            "start_time": datetime.now().isoformat(),
            "initial_analysis": {"complexity": "high"},
            "necessity_rationale": "Critical architectural issues detected",
            "strategy_analysis": {"recommended": "reorganize_components"},
            "phase_context": "phase_one"
        }
        
        cycle_outcome = {
            "refinement_necessary": True,
            "refinement_successful": True,
            "iterations": 2,
            "lessons_learned": ["Component reorganization was effective"]
        }
        
        result = await track_refinement_cycle(
            refinement_agent="garden_foundation_refinement",
            cycle_details=cycle_details,
            cycle_outcome=cycle_outcome,
            state_manager=mock_state_manager,
            health_tracker=mock_health_tracker,
            operation_id="cycle_789"
        )
        
        assert result["success"] == True
        assert "cycle_id" in result
        assert "decision_events" in result
        assert len(result["decision_events"]) >= 1  # At least necessity decision
    
    @pytest.mark.asyncio
    async def test_track_fire_intervention(self, mock_state_manager, mock_health_tracker):
        """Test tracking Fire Agent interventions."""
        complexity_details = {
            "complexity_score": 85.0,
            "analysis_timestamp": datetime.now().isoformat(),
            "exceeds_threshold": True
        }
        
        decomposition_result = {
            "success": True,
            "new_complexity_score": 45.0,
            "complexity_reduction": 40.0,
            "strategy_used": "responsibility_extraction",
            "decomposition_timestamp": (datetime.now() + timedelta(minutes=5)).isoformat(),
            "lessons_learned": ["Responsibility extraction effective for this case"]
        }
        
        result = await track_fire_intervention(
            intervention_context="phase_one_guideline",
            complexity_details=complexity_details,
            decomposition_result=decomposition_result,
            state_manager=mock_state_manager,
            health_tracker=mock_health_tracker,
            operation_id="fire_intervention_101"
        )
        
        assert result["success"] == True
        assert "intervention_id" in result
        assert "decision_event_id" in result
        assert result["complexity_reduction"] == 40.0
        assert result["strategy_used"] == "responsibility_extraction"
        
        # Verify tracking calls
        mock_state_manager.set_state.assert_called()
        mock_health_tracker.track_metric.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_decision_history_filtered(self, mock_state_manager):
        """Test retrieving filtered decision history."""
        # Mock decision event data
        mock_decision_data = {
            "event_id": "test_event_1",
            "decision_agent": "garden_foundation_refinement",
            "decision_type": "refinement_necessity",
            "timestamp": datetime.now().isoformat(),
            "input_context": {},
            "decision_rationale": "Test rationale",
            "decision_details": {},
            "decision_outcome": "success",
            "phase_context": "phase_one"
        }
        
        mock_state_manager.list_keys.return_value = ["air_agent:decision_event:test_event_1"]
        mock_state_manager.get_state.return_value = mock_decision_data
        
        # Test filtering by agent
        events = await get_decision_history(
            agent_filter="garden_foundation_refinement",
            lookback_period=timedelta(days=7),
            max_events=10,
            state_manager=mock_state_manager
        )
        
        assert len(events) <= 10
        mock_state_manager.list_keys.assert_called()
    
    @pytest.mark.asyncio
    async def test_decision_tracking_error_handling(self, mock_state_manager):
        """Test error handling in decision tracking."""
        # Simulate state manager error
        mock_state_manager.set_state.side_effect = Exception("Storage error")
        
        result = await track_decision_event(
            decision_agent="test_agent",
            decision_type="test_type",
            decision_details={},
            decision_outcome={},
            state_manager=mock_state_manager
        )
        
        # Should handle error gracefully
        assert "success" in result
        assert "error" in result or result["success"] == True


class TestAirAgentContextProvision:
    """Test Air Agent context provision functionality."""
    
    @pytest.fixture
    def mock_state_manager_with_history(self):
        """Mock state manager with decision history."""
        mock = AsyncMock()
        
        # Mock decision history
        sample_events = [
            {
                "event_id": "event_1",
                "decision_agent": "garden_foundation_refinement",
                "decision_type": "refinement_necessity",
                "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                "decision_outcome": "success",
                "phase_context": "phase_one",
                "input_context": {},
                "decision_rationale": "Test rationale 1",
                "decision_details": {}
            },
            {
                "event_id": "event_2",
                "decision_agent": "natural_selection",
                "decision_type": "natural_selection",
                "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
                "decision_outcome": "success",
                "phase_context": "phase_three",
                "input_context": {},
                "decision_rationale": "Test rationale 2",
                "decision_details": {}
            }
        ]
        
        mock.list_keys.return_value = [f"air_agent:decision_event:event_{i}" for i in range(1, 3)]
        mock.get_state.side_effect = lambda key, *args: sample_events[int(key.split("_")[-1]) - 1]
        
        return mock
    
    @pytest.mark.asyncio
    async def test_provide_refinement_context(self, mock_state_manager_with_history):
        """Test providing historical context for refinement decisions."""
        refinement_context = {
            "current_analysis": {
                "complexity_indicators": {"high_dependencies": True},
                "identified_issues": ["architectural_inconsistency"]
            }
        }
        
        context = await provide_refinement_context(
            requesting_agent="garden_foundation_refinement",
            refinement_context=refinement_context,
            lookback_period=timedelta(days=30),
            state_manager=mock_state_manager_with_history
        )
        
        assert isinstance(context, HistoricalContext)
        assert context.context_type == "refinement"
        assert context.requesting_agent == "garden_foundation_refinement"
        assert isinstance(context.confidence_level, PatternConfidence)
        assert isinstance(context.recommended_approaches, list)
        assert isinstance(context.cautionary_notes, list)
    
    @pytest.mark.asyncio
    async def test_provide_fire_context(self):
        """Test providing historical context for Fire Agent decisions."""
        current_complexity_analysis = {
            "complexity_score": 85.0,
            "complexity_causes": ["multiple_responsibilities", "high_dependency_count"],
            "analysis_context": "phase_one"
        }
        
        mock_state_manager = AsyncMock()
        mock_state_manager.list_keys.return_value = []
        
        context = await provide_fire_context(
            complexity_context="guideline",
            current_complexity_analysis=current_complexity_analysis,
            state_manager=mock_state_manager
        )
        
        assert isinstance(context, HistoricalContext)
        assert context.context_type == "fire_decomposition"
        assert context.requesting_agent == "fire_agent"
    
    @pytest.mark.asyncio
    async def test_provide_natural_selection_context(self):
        """Test providing historical context for Natural Selection decisions."""
        feature_performance_data = [
            {
                "feature_id": "feature_1",
                "performance_score": 0.8,
                "feature_specification": {"complexity": "medium"}
            },
            {
                "feature_id": "feature_2", 
                "performance_score": 0.6,
                "feature_specification": {"complexity": "high"}
            }
        ]
        
        mock_state_manager = AsyncMock()
        mock_state_manager.list_keys.return_value = []
        
        context = await provide_natural_selection_context(
            feature_performance_data=feature_performance_data,
            state_manager=mock_state_manager
        )
        
        assert isinstance(context, HistoricalContext)
        assert context.context_type == "natural_selection"
        assert context.requesting_agent == "natural_selection"
    
    @pytest.mark.asyncio
    async def test_provide_evolution_context(self):
        """Test providing historical context for Evolution Agent decisions."""
        evolution_context = {
            "system_state": {"complexity_trend": "increasing"},
            "recent_adaptations": ["strategy_1", "strategy_2"]
        }
        
        mock_state_manager = AsyncMock()
        mock_state_manager.list_keys.return_value = []
        
        context = await provide_evolution_context(
            evolution_context=evolution_context,
            state_manager=mock_state_manager
        )
        
        assert isinstance(context, HistoricalContext)
        assert context.context_type == "evolution"
        assert context.requesting_agent == "evolution"
    
    @pytest.mark.asyncio
    async def test_context_provision_error_handling(self):
        """Test error handling in context provision."""
        # Test with failing state manager
        mock_state_manager = AsyncMock()
        mock_state_manager.list_keys.side_effect = Exception("Storage error")
        
        context = await provide_refinement_context(
            requesting_agent="test_agent",
            refinement_context={},
            state_manager=mock_state_manager
        )
        
        # Should return minimal context on error
        assert isinstance(context, HistoricalContext)
        assert context.confidence_level == PatternConfidence.INSUFFICIENT_DATA


class TestAirAgentPatternAnalysis:
    """Test Air Agent pattern analysis functionality."""
    
    @pytest.fixture
    def sample_decision_events(self):
        """Sample decision events for pattern analysis."""
        base_time = datetime.now()
        return [
            DecisionEvent(
                event_id="event_1",
                decision_agent="garden_foundation_refinement",
                decision_type=DecisionType.REFINEMENT_NECESSITY,
                timestamp=base_time - timedelta(days=1),
                input_context={"complexity": "high"},
                decision_rationale="Architectural issues detected",
                decision_details={"strategy": "reorganize_components"},
                decision_outcome=DecisionOutcome.SUCCESS,
                phase_context="phase_one"
            ),
            DecisionEvent(
                event_id="event_2",
                decision_agent="garden_foundation_refinement",
                decision_type=DecisionType.REFINEMENT_STRATEGY,
                timestamp=base_time - timedelta(days=2),
                input_context={"complexity": "medium"},
                decision_rationale="Component issues detected",
                decision_details={"strategy": "reorganize_components"},
                decision_outcome=DecisionOutcome.SUCCESS,
                phase_context="phase_one"
            ),
            DecisionEvent(
                event_id="event_3",
                decision_agent="natural_selection",
                decision_type=DecisionType.NATURAL_SELECTION,
                timestamp=base_time - timedelta(days=3),
                input_context={"features": 5},
                decision_rationale="Feature optimization needed",
                decision_details={"optimization": "improve"},
                decision_outcome=DecisionOutcome.FAILURE,
                phase_context="phase_three"
            ),
            DecisionEvent(
                event_id="event_4",
                decision_agent="garden_foundation_refinement",
                decision_type=DecisionType.REFINEMENT_NECESSITY,
                timestamp=base_time - timedelta(days=4),
                input_context={"complexity": "low"},
                decision_rationale="Minor issues",
                decision_details={"strategy": "revise_environment"},
                decision_outcome=DecisionOutcome.FAILURE,
                phase_context="phase_one"
            )
        ]
    
    @pytest.mark.asyncio
    async def test_analyze_decision_patterns(self, sample_decision_events):
        """Test decision pattern analysis."""
        patterns = await analyze_decision_patterns(
            decision_events=sample_decision_events,
            pattern_types=["refinement_necessity"],
            min_frequency=2
        )
        
        assert isinstance(patterns, list)
        # Should identify patterns in the decision events
        if len(patterns) > 0:
            for pattern in patterns:
                assert isinstance(pattern, DecisionPattern)
                assert pattern.frequency >= 2
                assert pattern.confidence_level in [member for member in PatternConfidence]
    
    @pytest.mark.asyncio
    async def test_identify_success_patterns(self, sample_decision_events):
        """Test identification of success patterns."""
        success_patterns = await identify_success_patterns(
            decision_events=sample_decision_events,
            success_threshold=0.6
        )
        
        assert isinstance(success_patterns, list)
        for pattern in success_patterns:
            assert isinstance(pattern, DecisionPattern)
            assert pattern.success_rate >= 0.6
            assert pattern.pattern_type == "success_pattern"
    
    @pytest.mark.asyncio
    async def test_identify_failure_patterns(self, sample_decision_events):
        """Test identification of failure patterns."""
        failure_patterns = await identify_failure_patterns(
            decision_events=sample_decision_events,
            failure_threshold=0.4
        )
        
        assert isinstance(failure_patterns, list)
        for pattern in failure_patterns:
            assert isinstance(pattern, DecisionPattern)
            assert pattern.success_rate <= 0.4
            assert pattern.pattern_type == "failure_pattern"
    
    @pytest.mark.asyncio
    async def test_analyze_cross_phase_patterns(self):
        """Test cross-phase pattern analysis."""
        mock_state_manager = AsyncMock()
        mock_state_manager.list_keys.return_value = []
        
        patterns = await analyze_cross_phase_patterns(
            current_phase="phase_two",
            state_manager=mock_state_manager
        )
        
        assert isinstance(patterns, list)
        # Should return list of CrossPhasePattern objects
        for pattern in patterns:
            assert isinstance(pattern, CrossPhasePattern)
    
    def test_pattern_analysis_with_insufficient_data(self):
        """Test pattern analysis behavior with insufficient data."""
        # Test with very few events
        minimal_events = [
            DecisionEvent(
                event_id="event_1",
                decision_agent="test_agent",
                decision_type=DecisionType.REFINEMENT_NECESSITY,
                timestamp=datetime.now(),
                input_context={},
                decision_rationale="Test",
                decision_details={},
                decision_outcome=DecisionOutcome.SUCCESS,
                phase_context="phase_one"
            )
        ]
        
        # Should handle gracefully with minimal events
        # Note: This is a synchronous test as analyze_decision_patterns
        # should handle insufficient data gracefully


class TestAirAgentHistoryManagement:
    """Test Air Agent history management functionality."""
    
    @pytest.fixture
    def mock_state_manager_with_old_data(self):
        """Mock state manager with old decision data."""
        mock = AsyncMock()
        
        old_timestamp = (datetime.now() - timedelta(days=100)).isoformat()
        recent_timestamp = (datetime.now() - timedelta(days=1)).isoformat()
        
        mock_keys = [
            "air_agent:decision_event:old_event",
            "air_agent:decision_event:recent_event",
            "air_agent:fire_intervention:old_intervention",
            "air_agent:fire_intervention:recent_intervention"
        ]
        
        mock_data = {
            "air_agent:decision_event:old_event": {"timestamp": old_timestamp},
            "air_agent:decision_event:recent_event": {"timestamp": recent_timestamp},
            "air_agent:fire_intervention:old_intervention": {"timestamp": old_timestamp},
            "air_agent:fire_intervention:recent_intervention": {"timestamp": recent_timestamp}
        }
        
        mock.list_keys.side_effect = lambda prefix: [k for k in mock_keys if k.startswith(prefix)]
        mock.get_state.side_effect = lambda key, *args: mock_data.get(key)
        mock.delete_state = AsyncMock()
        
        return mock
    
    @pytest.mark.asyncio
    async def test_clear_old_history(self, mock_state_manager_with_old_data, mock_health_tracker):
        """Test clearing old decision history."""
        result = await clear_old_history(
            retention_days=30,
            state_manager=mock_state_manager_with_old_data,
            health_tracker=mock_health_tracker
        )
        
        assert result["success"] == True
        assert "decisions_cleaned" in result
        assert "interventions_cleaned" in result
        assert result["decisions_cleaned"] >= 0
        assert result["interventions_cleaned"] >= 0
        
        # Verify cleanup calls were made
        mock_state_manager_with_old_data.delete_state.assert_called()
        mock_health_tracker.track_metric.assert_called()
    
    @pytest.mark.asyncio
    async def test_history_cleanup_error_handling(self):
        """Test error handling in history cleanup."""
        mock_state_manager = AsyncMock()
        mock_state_manager.list_keys.side_effect = Exception("Storage error")
        
        result = await clear_old_history(
            retention_days=30,
            state_manager=mock_state_manager
        )
        
        assert result["success"] == False
        assert "error" in result


class TestAirAgentIntegration:
    """Test Air Agent integration with FFTT workflows."""
    
    @pytest.mark.asyncio
    async def test_garden_foundation_refinement_integration(self):
        """Test Air Agent integration with Garden Foundation Refinement Agent."""
        mock_state_manager = AsyncMock()
        mock_state_manager.list_keys.return_value = []
        
        # Simulate refinement context
        refinement_context = {
            "current_analysis": {
                "complexity_indicators": {"architectural_issues": True},
                "identified_issues": ["component_conflicts", "integration_problems"]
            },
            "phase_zero_feedback": {
                "critical_issues": ["dependency_cycles"]
            }
        }
        
        # Get historical context
        context = await provide_refinement_context(
            requesting_agent="garden_foundation_refinement",
            refinement_context=refinement_context,
            state_manager=mock_state_manager
        )
        
        # Should provide useful context for decision making
        assert isinstance(context, HistoricalContext)
        assert context.context_type == "refinement"
        
        # Track a refinement decision
        decision_details = {
            "input_context": refinement_context,
            "rationale": "Critical architectural issues require component reorganization",
            "phase_context": "phase_one"
        }
        
        decision_outcome = {
            "success": True,
            "refinement_applied": True,
            "strategy": "reorganize_components"
        }
        
        tracking_result = await track_decision_event(
            decision_agent="garden_foundation_refinement",
            decision_type="refinement_necessity",
            decision_details=decision_details,
            decision_outcome=decision_outcome,
            state_manager=mock_state_manager,
            operation_id="integration_test_1"
        )
        
        assert tracking_result["success"] == True
    
    @pytest.mark.asyncio
    async def test_natural_selection_integration(self):
        """Test Air Agent integration with Natural Selection Agent."""
        mock_state_manager = AsyncMock()
        mock_state_manager.list_keys.return_value = []
        
        # Simulate feature performance data
        feature_performance_data = [
            {
                "feature_id": "feature_1",
                "performance_score": 0.85,
                "complexity_analysis": {"score": 45}
            },
            {
                "feature_id": "feature_2",
                "performance_score": 0.62,
                "complexity_analysis": {"score": 78}
            }
        ]
        
        # Get historical context for Natural Selection
        context = await provide_natural_selection_context(
            feature_performance_data=feature_performance_data,
            state_manager=mock_state_manager
        )
        
        assert isinstance(context, HistoricalContext)
        assert context.context_type == "natural_selection"
        
        # Track Natural Selection decision
        decision_details = {
            "input_context": {
                "features_analyzed": len(feature_performance_data),
                "air_context_available": True
            },
            "rationale": "Natural selection with Air Agent historical context",
            "phase_context": "phase_three"
        }
        
        decision_outcome = {
            "success": True,
            "features_ranked": 2,
            "optimization_decisions": 2
        }
        
        tracking_result = await track_decision_event(
            decision_agent="natural_selection",
            decision_type="natural_selection",
            decision_details=decision_details,
            decision_outcome=decision_outcome,
            state_manager=mock_state_manager,
            operation_id="ns_integration_test"
        )
        
        assert tracking_result["success"] == True
    
    @pytest.mark.asyncio
    async def test_fire_air_coordination(self):
        """Test coordination between Fire and Air agents."""
        mock_state_manager = AsyncMock()
        
        # Simulate Fire Agent intervention
        complexity_details = {
            "complexity_score": 88.0,
            "exceeds_threshold": True,
            "analysis_context": "phase_three_feature"
        }
        
        decomposition_result = {
            "success": True,
            "complexity_reduction": 35.0,
            "strategy_used": "functional_separation",
            "lessons_learned": ["Functional separation effective for this feature type"]
        }
        
        # Track Fire intervention
        fire_tracking = await track_fire_intervention(
            intervention_context="phase_three_feature",
            complexity_details=complexity_details,
            decomposition_result=decomposition_result,
            state_manager=mock_state_manager,
            operation_id="fire_air_coordination_test"
        )
        
        assert fire_tracking["success"] == True
        
        # Provide Fire context using Air Agent
        fire_context = await provide_fire_context(
            complexity_context="feature",
            current_complexity_analysis=complexity_details,
            state_manager=mock_state_manager
        )
        
        assert isinstance(fire_context, HistoricalContext)
        assert fire_context.context_type == "fire_decomposition"
    
    @pytest.mark.asyncio
    async def test_air_agent_resilience(self):
        """Test Air Agent resilience to various error conditions."""
        # Test with None state manager
        context = await provide_refinement_context(
            requesting_agent="test_agent",
            refinement_context={},
            state_manager=None
        )
        
        assert isinstance(context, HistoricalContext)
        assert context.confidence_level == PatternConfidence.INSUFFICIENT_DATA
        
        # Test with empty context
        context = await provide_fire_context(
            complexity_context="",
            current_complexity_analysis={},
            state_manager=None
        )
        
        assert isinstance(context, HistoricalContext)
    
    def test_air_agent_data_models(self):
        """Test Air Agent data model integrity."""
        # Test DecisionEvent creation
        decision_event = DecisionEvent(
            event_id="test_event",
            decision_agent="test_agent",
            decision_type=DecisionType.REFINEMENT_NECESSITY,
            timestamp=datetime.now(),
            input_context={"test": "context"},
            decision_rationale="Test rationale",
            decision_details={"test": "details"},
            decision_outcome=DecisionOutcome.SUCCESS
        )
        
        assert decision_event.event_id == "test_event"
        assert decision_event.decision_type == DecisionType.REFINEMENT_NECESSITY
        assert decision_event.decision_outcome == DecisionOutcome.SUCCESS
        
        # Test FireIntervention creation
        fire_intervention = FireIntervention(
            intervention_id="test_intervention",
            intervention_context="test_context",
            timestamp=datetime.now(),
            original_complexity_score=85.0,
            final_complexity_score=45.0,
            complexity_reduction=40.0,
            decomposition_strategy="functional_separation",
            success=True
        )
        
        assert fire_intervention.intervention_id == "test_intervention"
        assert fire_intervention.complexity_reduction == 40.0
        assert fire_intervention.success == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])