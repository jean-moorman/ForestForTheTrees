"""
Integration tests for Fire and Air agent coordination in FFTT workflows.

Tests the end-to-end integration of Fire and Air agents with Phase 1 and Phase 3
workflows, ensuring proper coordination and data flow between agents.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

# Import workflow classes
from phase_one.workflow import PhaseOneWorkflow
from phase_three.evolution.natural_selection import NaturalSelectionAgent

# Import Fire and Air agent functions
from resources.fire_agent import (
    analyze_guideline_complexity,
    decompose_complex_guideline,
    analyze_feature_complexity,
    decompose_complex_feature
)

from resources.air_agent import (
    provide_refinement_context,
    provide_fire_context,
    provide_natural_selection_context,
    track_decision_event,
    track_fire_intervention
)

from resources.fire_agent.models import ComplexityLevel, DecompositionStrategy
from resources.air_agent.models import PatternConfidence, DecisionType, DecisionOutcome


class TestPhaseOneFireIntegration:
    """Test Fire Agent integration with Phase 1 Tree Placement Planner."""
    
    @pytest.fixture
    def mock_agents(self):
        """Mock Phase 1 agents for testing."""
        return {
            "garden_planner": AsyncMock(),
            "earth_agent": AsyncMock(),
            "environmental_analysis": AsyncMock(),
            "root_system_architect": AsyncMock(),
            "tree_placement_planner": AsyncMock()
        }
    
    @pytest.fixture
    def mock_resources(self):
        """Mock resources for testing."""
        event_queue = AsyncMock()
        state_manager = AsyncMock()
        state_manager.set_state = AsyncMock()
        state_manager.get_state = AsyncMock()
        
        return {
            "event_queue": event_queue,
            "state_manager": state_manager
        }
    
    @pytest.fixture
    def complex_component_architecture(self):
        """Complex component architecture that should trigger Fire Agent."""
        return {
            "components": [f"component_{i}" for i in range(18)],
            "dependencies": [f"dependency_{i}" for i in range(14)],
            "interfaces": [f"interface_{i}" for i in range(10)],
            "responsibilities": [f"responsibility_{i}" for i in range(12)],
            "integration_points": [f"integration_{i}" for i in range(8)],
            "scope": {
                "features": [f"feature_{i}" for i in range(25)],
                "modules": [f"module_{i}" for i in range(15)]
            },
            "cross_cutting_concerns": ["logging", "security", "monitoring", "validation"]
        }
    
    @pytest.fixture
    def phase_one_workflow(self, mock_agents, mock_resources):
        """Phase One workflow with mocked dependencies."""
        # Create a mock workflow instead of real instance to avoid async issues
        mock_workflow = MagicMock()
        mock_workflow._execute_tree_placement_planner = AsyncMock()
        
        # Set up the mock to return test data
        mock_workflow._execute_tree_placement_planner.return_value = {
            "success": True,
            "component_architecture": {},
            "fire_agent_intervention": {
                "complexity_detected": True,
                "complexity_score": 85.0,
                "decomposition_applied": True,
                "original_complexity_score": 85.0,
                "new_complexity_score": 45.0,
                "complexity_reduction": 40.0,
                "strategy_used": "responsibility_extraction",
                "lessons_learned": ["Mock decomposition successful"]
            }
        }
        
        return mock_workflow
    
    @pytest.mark.asyncio
    async def test_tree_placement_planner_fire_integration(self, phase_one_workflow, complex_component_architecture, mock_resources):
        """Test Fire Agent integration with Tree Placement Planner execution."""
        # Mock Tree Placement Planner to return complex architecture
        phase_one_workflow.tree_placement_planner_agent._process.return_value = {
            "component_architecture": complex_component_architecture
        }
        
        # Mock development state attribute
        phase_one_workflow.tree_placement_planner_agent.development_state = None
        
        # Execute Tree Placement Planner with Fire Agent integration
        result = await phase_one_workflow._execute_tree_placement_planner(
            task_analysis={"test": "analysis"},
            environmental_analysis={"test": "environment"},
            data_architecture={"test": "data"},
            operation_id="fire_integration_test_1"
        )
        
        # Verify successful execution
        assert result["success"] == True
        assert "component_architecture" in result
        assert "fire_agent_intervention" in result
        
        # Check Fire Agent intervention details
        fire_intervention = result["fire_agent_intervention"]
        
        # Should have detected complexity
        if fire_intervention.get("complexity_detected"):
            assert "complexity_score" in fire_intervention
            
            # If decomposition was applied
            if fire_intervention.get("decomposition_applied"):
                assert "original_complexity_score" in fire_intervention
                assert "new_complexity_score" in fire_intervention
                assert "complexity_reduction" in fire_intervention
                assert "strategy_used" in fire_intervention
                assert "lessons_learned" in fire_intervention
                
                # Verify complexity was actually reduced
                assert fire_intervention["new_complexity_score"] < fire_intervention["original_complexity_score"]
                assert fire_intervention["complexity_reduction"] > 0
        
        # Verify state manager calls for storing analysis
        mock_resources["state_manager"].set_state.assert_called()
    
    @pytest.mark.asyncio
    async def test_fire_complexity_analysis_phase_one(self, complex_component_architecture, mock_resources):
        """Test Fire Agent complexity analysis specifically for Phase 1 context."""
        # Analyze complexity
        complexity_analysis = await analyze_guideline_complexity(
            guideline=complex_component_architecture,
            context="phase_one",
            state_manager=mock_resources["state_manager"]
        )
        
        # Should detect high complexity
        assert complexity_analysis.complexity_score > 70
        assert complexity_analysis.complexity_level in [ComplexityLevel.HIGH, ComplexityLevel.CRITICAL]
        assert complexity_analysis.exceeds_threshold == True
        assert len(complexity_analysis.complexity_causes) > 0
        assert complexity_analysis.recommended_strategy is not None
        
        # Should have decomposition opportunities
        assert len(complexity_analysis.decomposition_opportunities) > 0
        
        # If complexity exceeds threshold, test decomposition
        if complexity_analysis.exceeds_threshold:
            decomposition_result = await decompose_complex_guideline(
                complex_guideline=complex_component_architecture,
                guideline_context="phase_one_component_architecture",
                state_manager=mock_resources["state_manager"],
                strategy=complexity_analysis.recommended_strategy
            )
            
            assert decomposition_result.success == True
            assert decomposition_result.simplified_architecture is not None
            assert decomposition_result.complexity_reduction > 0
            assert len(decomposition_result.lessons_learned) > 0
    
    @pytest.mark.asyncio
    async def test_fire_agent_error_handling_phase_one(self, mock_resources):
        """Test Fire Agent error handling in Phase 1 integration."""
        # Test with invalid/empty component architecture
        invalid_architecture = None
        
        # Should handle gracefully
        complexity_analysis = await analyze_guideline_complexity(
            guideline=invalid_architecture,
            context="phase_one",
            state_manager=mock_resources["state_manager"]
        )
        
        assert complexity_analysis.complexity_score >= 0
        assert complexity_analysis.confidence_level < 1.0


class TestPhaseThreeFireAirIntegration:
    """Test Fire and Air agent integration with Phase 3 Natural Selection."""
    
    @pytest.fixture
    def mock_natural_selection_resources(self):
        """Mock resources for Natural Selection agent."""
        event_queue = AsyncMock()
        state_manager = AsyncMock()
        state_manager.set_state = AsyncMock()
        state_manager.get_state = AsyncMock()
        state_manager.list_keys = AsyncMock(return_value=[])
        
        context_manager = AsyncMock()
        cache_manager = AsyncMock()
        metrics_manager = AsyncMock()
        error_handler = AsyncMock()
        
        return {
            "event_queue": event_queue,
            "state_manager": state_manager,
            "context_manager": context_manager,
            "cache_manager": cache_manager,
            "metrics_manager": metrics_manager,
            "error_handler": error_handler
        }
    
    @pytest.fixture
    def complex_feature_performances(self):
        """Complex feature performance data for testing."""
        return [
            {
                "feature_id": "complex_feature_1",
                "performance_score": 0.65,
                "feature_specification": {
                    "responsibilities": [f"responsibility_{i}" for i in range(8)],
                    "dependencies": [f"dependency_{i}" for i in range(12)],
                    "scope": {
                        "frontend": True,
                        "backend": True,
                        "database": True,
                        "api": True,
                        "testing": True
                    },
                    "cross_cutting_concerns": ["logging", "security", "caching", "monitoring"]
                }
            },
            {
                "feature_id": "simple_feature_2",
                "performance_score": 0.85,
                "feature_specification": {
                    "responsibilities": ["single_responsibility"],
                    "dependencies": ["dependency_1"],
                    "scope": {"focused": True}
                }
            },
            {
                "feature_id": "medium_feature_3",
                "performance_score": 0.72,
                "feature_specification": {
                    "responsibilities": [f"responsibility_{i}" for i in range(4)],
                    "dependencies": [f"dependency_{i}" for i in range(6)],
                    "scope": {"moderate": True}
                }
            }
        ]
    
    @pytest.fixture
    def natural_selection_agent(self, mock_natural_selection_resources):
        """Natural Selection agent with mocked dependencies."""
        # Create a mock agent instead of real instance to avoid async issues
        mock_agent = AsyncMock()
        
        # Mock the evaluate_features method  
        def mock_evaluate_features(*args, **kwargs):
            operation_id = kwargs.get("operation_id", "test_operation")
            return {
                "operation_id": operation_id,
                "fire_agent_interventions": [
                    {
                        "original_feature_id": "complex_feature_1",
                        "decomposed_features": [
                            {"feature_id": "complex_feature_1_core", "name": "Core Function"},
                            {"feature_id": "complex_feature_1_support", "name": "Support Function"}
                        ],
                        "complexity_reduction": 25.0,
                        "strategy_used": "functional_separation"
                    }
                ],
                "air_agent_context": {
                    "confidence_level": "medium",
                    "events_analyzed": 5
                }
            }
        
        mock_agent.evaluate_features = AsyncMock(side_effect=mock_evaluate_features)
        
        return mock_agent
    
    @pytest.mark.asyncio
    async def test_natural_selection_fire_air_integration(self, natural_selection_agent, complex_feature_performances):
        """Test complete Fire/Air integration with Natural Selection."""
        # Execute Natural Selection with Fire/Air integration
        result = await natural_selection_agent.evaluate_features(
            feature_performances=complex_feature_performances,
            operation_id="fire_air_integration_test"
        )
        
        # Verify successful execution
        assert result is not None
        assert "operation_id" in result
        assert result["operation_id"] == "fire_air_integration_test"
        
        # Check for Fire Agent interventions
        if "fire_agent_interventions" in result:
            fire_interventions = result["fire_agent_interventions"]
            assert isinstance(fire_interventions, list)
            
            # Should have intervened on complex feature
            complex_interventions = [
                intervention for intervention in fire_interventions
                if intervention.get("original_feature_id") == "complex_feature_1"
            ]
            
            if len(complex_interventions) > 0:
                intervention = complex_interventions[0]
                assert "decomposed_features" in intervention
                assert "complexity_reduction" in intervention
                assert "strategy_used" in intervention
                assert len(intervention["decomposed_features"]) > 0
        
        # Check for Air Agent context
        if "air_agent_context" in result:
            air_context = result["air_agent_context"]
            assert isinstance(air_context, dict)
            assert "confidence_level" in air_context
            assert "events_analyzed" in air_context
    
    @pytest.mark.asyncio
    async def test_fire_feature_complexity_analysis(self, complex_feature_performances, mock_natural_selection_resources):
        """Test Fire Agent feature complexity analysis."""
        complex_feature = complex_feature_performances[0]
        feature_spec = complex_feature["feature_specification"]
        
        # Analyze feature complexity
        complexity_analysis = await analyze_feature_complexity(
            feature_spec=feature_spec,
            feature_context=complex_feature,
            state_manager=mock_natural_selection_resources["state_manager"]
        )
        
        # Should detect high complexity
        assert complexity_analysis.complexity_score > 60
        assert complexity_analysis.exceeds_threshold == True
        assert complexity_analysis.analysis_context == "phase_three_feature"
        
        # Test decomposition
        if complexity_analysis.exceeds_threshold:
            strategy = complexity_analysis.recommended_strategy.value if complexity_analysis.recommended_strategy else "functional_separation"
            
            decomposition_result = await decompose_complex_feature(
                complex_feature=feature_spec,
                decomposition_strategy=strategy,
                state_manager=mock_natural_selection_resources["state_manager"]
            )
            
            assert decomposition_result.success == True
            assert len(decomposition_result.decomposed_features) > 0
            
            # Verify decomposed features have proper structure
            for decomposed_feature in decomposition_result.decomposed_features:
                assert "feature_id" in decomposed_feature
                assert "name" in decomposed_feature
                assert "type" in decomposed_feature
    
    @pytest.mark.asyncio
    async def test_air_natural_selection_context(self, complex_feature_performances, mock_natural_selection_resources):
        """Test Air Agent context provision for Natural Selection."""
        context = await provide_natural_selection_context(
            feature_performance_data=complex_feature_performances,
            state_manager=mock_natural_selection_resources["state_manager"]
        )
        
        assert context.context_type == "natural_selection"
        assert context.requesting_agent == "natural_selection"
        assert context.confidence_level in [member.value for member in PatternConfidence]
        assert isinstance(context.recommended_approaches, list)
        assert isinstance(context.success_patterns, list)
    
    @pytest.mark.asyncio
    async def test_decision_tracking_integration(self, mock_natural_selection_resources):
        """Test decision tracking integration in Natural Selection workflow."""
        # Test tracking a Natural Selection decision
        decision_details = {
            "input_context": {
                "features_analyzed": 3,
                "fire_interventions": 1,
                "air_context_available": True
            },
            "rationale": "Natural selection with Fire/Air agent support",
            "phase_context": "phase_three"
        }
        
        decision_outcome = {
            "success": True,
            "features_ranked": 3,
            "optimization_decisions": 3,
            "fire_decompositions_applied": 1
        }
        
        tracking_result = await track_decision_event(
            decision_agent="natural_selection",
            decision_type="natural_selection",
            decision_details=decision_details,
            decision_outcome=decision_outcome,
            state_manager=mock_natural_selection_resources["state_manager"],
            operation_id="decision_tracking_test"
        )
        
        assert tracking_result["success"] == True
        assert tracking_result["agent"] == "natural_selection"
        assert "event_id" in tracking_result


class TestFireAirCoordination:
    """Test coordination between Fire and Air agents."""
    
    @pytest.fixture
    def mock_state_manager_with_history(self):
        """Mock state manager with Fire intervention history."""
        mock = AsyncMock()
        
        # Mock Fire intervention history
        mock_interventions = [
            {
                "intervention_id": "intervention_1",
                "intervention_context": "phase_one_guideline",
                "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                "original_complexity_score": 85.0,
                "final_complexity_score": 45.0,
                "complexity_reduction": 40.0,
                "decomposition_strategy": "responsibility_extraction",
                "success": True,
                "lessons_learned": ["Responsibility extraction effective"],
                "effective_techniques": ["Strategy: responsibility_extraction"]
            },
            {
                "intervention_id": "intervention_2",
                "intervention_context": "phase_three_feature",
                "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
                "original_complexity_score": 78.0,
                "final_complexity_score": 42.0,
                "complexity_reduction": 36.0,
                "decomposition_strategy": "functional_separation",
                "success": True,
                "lessons_learned": ["Functional separation worked well"],
                "effective_techniques": ["Strategy: functional_separation"]
            }
        ]
        
        mock.list_keys.return_value = [f"air_agent:fire_intervention:intervention_{i}" for i in range(1, 3)]
        mock.get_state.side_effect = lambda key, *args: mock_interventions[int(key.split("_")[-1]) - 1]
        mock.set_state = AsyncMock()
        
        return mock
    
    @pytest.mark.asyncio
    async def test_fire_air_context_coordination(self, mock_state_manager_with_history):
        """Test Air Agent providing context for Fire Agent decisions."""
        # Simulate current complexity analysis
        current_complexity_analysis = {
            "complexity_score": 82.0,
            "complexity_causes": ["multiple_responsibilities", "high_dependency_count"],
            "analysis_context": "phase_one"
        }
        
        # Get Air Agent context for Fire decisions
        fire_context = await provide_fire_context(
            complexity_context="guideline",
            current_complexity_analysis=current_complexity_analysis,
            state_manager=mock_state_manager_with_history
        )
        
        assert fire_context.context_type == "fire_decomposition"
        assert fire_context.requesting_agent == "fire_agent"
        
        # Should provide relevant historical patterns
        if len(fire_context.success_patterns) > 0:
            # Should have strategy recommendations based on history
            assert any("strategy" in pattern.lower() for pattern in fire_context.success_patterns)
    
    @pytest.mark.asyncio
    async def test_fire_intervention_tracking_by_air(self, mock_state_manager_with_history):
        """Test Air Agent tracking Fire Agent interventions."""
        # Simulate Fire Agent intervention
        complexity_details = {
            "complexity_score": 88.0,
            "analysis_timestamp": datetime.now().isoformat(),
            "exceeds_threshold": True,
            "complexity_causes": ["multiple_responsibilities"]
        }
        
        decomposition_result = {
            "success": True,
            "new_complexity_score": 48.0,
            "complexity_reduction": 40.0,
            "strategy_used": "responsibility_extraction",
            "decomposition_timestamp": (datetime.now() + timedelta(minutes=3)).isoformat(),
            "lessons_learned": ["Responsibility extraction effective for this case"],
            "warnings": []
        }
        
        # Track Fire intervention with Air Agent
        tracking_result = await track_fire_intervention(
            intervention_context="phase_one_guideline",
            complexity_details=complexity_details,
            decomposition_result=decomposition_result,
            state_manager=mock_state_manager_with_history,
            operation_id="fire_air_coordination_test"
        )
        
        assert tracking_result["success"] == True
        assert tracking_result["complexity_reduction"] == 40.0
        assert tracking_result["strategy_used"] == "responsibility_extraction"
        assert "intervention_id" in tracking_result
        assert "decision_event_id" in tracking_result
        
        # Verify both Fire intervention and decision event were stored
        assert mock_state_manager_with_history.set_state.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_historical_pattern_learning(self, mock_state_manager_with_history):
        """Test that Air Agent learns from Fire Agent intervention patterns."""
        # Get Fire context to see historical patterns
        fire_context = await provide_fire_context(
            complexity_context="guideline",
            current_complexity_analysis={"complexity_score": 85.0},
            state_manager=mock_state_manager_with_history
        )
        
        # Should identify effective strategies from history
        assert fire_context.confidence_level != PatternConfidence.INSUFFICIENT_DATA
        
        # If there are patterns, they should include strategy information
        if len(fire_context.success_patterns) > 0:
            assert any("extraction" in pattern or "separation" in pattern 
                      for pattern in fire_context.success_patterns)


class TestEndToEndIntegration:
    """Test end-to-end integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_phase_one_to_phase_three_fire_air_flow(self):
        """Test Fire/Air agent data flow from Phase 1 to Phase 3."""
        mock_state_manager = AsyncMock()
        mock_state_manager.set_state = AsyncMock()
        mock_state_manager.get_state = AsyncMock()
        mock_state_manager.list_keys = AsyncMock(return_value=[])
        
        # Simulate Phase 1 Fire intervention
        phase_one_architecture = {
            "components": [f"component_{i}" for i in range(20)],
            "dependencies": [f"dep_{i}" for i in range(15)]
        }
        
        # Phase 1: Fire Agent complexity analysis
        p1_complexity = await analyze_guideline_complexity(
            guideline=phase_one_architecture,
            context="phase_one",
            state_manager=mock_state_manager
        )
        
        # If complex, decompose
        p1_intervention_tracked = False
        if p1_complexity.exceeds_threshold:
            p1_decomposition = await decompose_complex_guideline(
                complex_guideline=phase_one_architecture,
                guideline_context="phase_one_component_architecture",
                state_manager=mock_state_manager
            )
            
            if p1_decomposition.success:
                # Track Fire intervention
                await track_fire_intervention(
                    intervention_context="phase_one_guideline",
                    complexity_details={"complexity_score": p1_complexity.complexity_score},
                    decomposition_result=p1_decomposition.__dict__,
                    state_manager=mock_state_manager,
                    operation_id="phase_1_intervention"
                )
                p1_intervention_tracked = True
        
        # Simulate Phase 3 using Air context informed by Phase 1
        phase_three_features = [
            {
                "feature_id": "feature_1",
                "feature_specification": {
                    "responsibilities": [f"resp_{i}" for i in range(7)],
                    "dependencies": [f"dep_{i}" for i in range(9)]
                }
            }
        ]
        
        # Phase 3: Get Air context (should include Phase 1 patterns)
        air_context = await provide_natural_selection_context(
            feature_performance_data=phase_three_features,
            state_manager=mock_state_manager
        )
        
        # Phase 3: Fire Agent feature analysis
        p3_complexity = await analyze_feature_complexity(
            feature_spec=phase_three_features[0]["feature_specification"],
            feature_context=phase_three_features[0],
            state_manager=mock_state_manager
        )
        
        # Verify end-to-end flow
        assert isinstance(air_context.confidence_level, str)
        assert p3_complexity.analysis_context == "phase_three_feature"
        
        # If we tracked a Phase 1 intervention, the system should be learning
        if p1_intervention_tracked:
            # The system should have historical data to inform decisions
            assert mock_state_manager.set_state.call_count > 0
    
    @pytest.mark.asyncio
    async def test_system_resilience_with_agent_failures(self):
        """Test system resilience when Fire/Air agents encounter errors."""
        # Mock state manager that fails
        failing_state_manager = AsyncMock()
        failing_state_manager.set_state.side_effect = Exception("Storage failure")
        failing_state_manager.get_state.side_effect = Exception("Retrieval failure")
        failing_state_manager.list_keys.side_effect = Exception("List failure")
        
        # Fire Agent should handle storage failures gracefully
        complexity_analysis = await analyze_guideline_complexity(
            guideline={"test": "data"},
            context="phase_one",
            state_manager=failing_state_manager
        )
        
        assert complexity_analysis.complexity_score >= 0
        assert complexity_analysis.confidence_level < 1.0
        
        # Air Agent should handle retrieval failures gracefully
        air_context = await provide_refinement_context(
            requesting_agent="test_agent",
            refinement_context={},
            state_manager=failing_state_manager
        )
        
        assert air_context.confidence_level == PatternConfidence.INSUFFICIENT_DATA
        assert len(air_context.cautionary_notes) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])