"""
Test file for phase three evolutionary selection mechanisms.

This file tests:
1. Feature performance evaluation
2. Natural selection decision-making
3. Feature replacement, improvement, and combination
"""

import asyncio
import json
import pytest
import unittest.mock as mock
from typing import Dict, List, Any, Optional, Set
from datetime import datetime

class ResourceType:
    STATE = "state"
    EVENT = "event"
    METRIC = "metric"

class ResourceState:
    PENDING = "pending"
    ACTIVE = "active"
    FAILED = "failed"
    COMPLETE = "complete"

# Mock classes for dependency injection
class EventQueue:
    async def publish(self, event_type, data): pass
    
class StateManager:
    async def set_state(self, key, value, resource_type): pass
    async def get_state(self, key): pass
    
class CacheManager:
    async def set(self, key, value, ttl=None): pass
    async def get(self, key): return None
    
class AgentContextManager:
    async def get_context(self, agent_id): return {}
    async def set_context(self, agent_id, context): pass
    
class MetricsManager:
    async def record_metric(self, name, value, metadata=None): pass
    
class ErrorHandler:
    async def handle_error(self, error, context=None): pass
# Mock classes for phase_three
from enum import Enum, auto

class FeaturePerformanceMetrics(Enum):
    CODE_QUALITY = auto()
    TEST_COVERAGE = auto()
    BUILD_STABILITY = auto()
    MAINTAINABILITY = auto()
    RUNTIME_EFFICIENCY = auto()
    INTEGRATION_SCORE = auto()

class FeatureDevelopmentState(Enum):
    PLANNING = auto()
    ELABORATION = auto()
    TEST_CREATION = auto()
    IMPLEMENTATION = auto()
    TESTING = auto()
    INTEGRATION = auto()
    COMPLETED = auto()
    FAILED = auto()

class FeatureState(Enum):
    INITIALIZED = auto()
    IMPLEMENTING = auto()
    TESTING = auto()
    ACTIVE = auto()
    DISABLED = auto()
    ERROR = auto()

class FeaturePerformanceScore:
    def __init__(self, feature_id):
        self.feature_id = feature_id
        self.scores = {}
        
    def get_overall_score(self):
        if not self.scores:
            return 0.0
        return sum(self.scores.values()) / len(self.scores)

class Feature:
    def __init__(self, feature_id, description=""):
        self.interface_id = feature_id
        self.description = description

# Mocked versions of the main classes
class NaturalSelectionAgent:
    def __init__(self, event_queue, state_manager, context_manager, cache_manager, metrics_manager, error_handler, memory_monitor=None):
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._context_manager = context_manager
        self._cache_manager = cache_manager
        self._metrics_manager = metrics_manager
        self._error_handler = error_handler
        self._memory_monitor = memory_monitor
        
        # Phase Zero agents
        self._requirements_analysis_agent = mock.MagicMock()
        self._implementation_analysis_agent = mock.MagicMock()
        self._evolution_agent = mock.MagicMock()
        
    async def evaluate_features(self, feature_performances, operation_id):
        # This would be mocked in tests
        pass

class ParallelFeatureDevelopment:
    def __init__(self, event_queue, state_manager, context_manager, cache_manager, metrics_manager, error_handler, phase_four_interface, memory_monitor=None, max_parallel=3):
        pass
    
    async def get_feature_status(self, feature_id):
        pass
    
    async def get_all_feature_statuses(self):
        pass
    
    async def start_feature_development(self, feature_metadata):
        pass

class PhaseThreeInterface:
    def __init__(self, event_queue, state_manager, context_manager, cache_manager, metrics_manager, error_handler, memory_monitor=None, system_monitor=None):
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._context_manager = context_manager
        self._cache_manager = cache_manager
        self._metrics_manager = metrics_manager
        self._error_handler = error_handler
        self._memory_monitor = memory_monitor
        self._system_monitor = system_monitor
        
        # Natural selection agent
        self._natural_selection_agent = mock.MagicMock()
        
        # Feature development
        self._feature_development = mock.MagicMock()
        
        # Phase four interface
        self._phase_four_interface = mock.MagicMock()
        
        # Track growth intervals
        self._last_evaluation_time = 0
        self._evaluation_interval = 3600  # 1 hour between evaluations
    
    async def evaluate_feature_evolution(self, component_id=None):
        pass
    
    async def _apply_evolution_decisions(self, evaluation_result):
        pass
    
    async def _replace_feature(self, feature_id, rationale, evaluation_data):
        pass
    
    async def _improve_feature(self, feature_id, rationale, evaluation_data):
        pass
    
    async def _combine_features(self, combination_candidates, evaluation_data):
        pass

# Test data
@pytest.fixture
def feature_performance_data():
    """Sample feature performance data for testing."""
    return [
        {
            "feature_id": "feature_1", 
            "feature_name": "High Performance Feature",
            "state": FeatureDevelopmentState.COMPLETED.name,
            "performance": {
                "overall_score": 85.0,
                "metrics": {
                    "code_quality": 90.0,
                    "test_coverage": 85.0,
                    "build_stability": 95.0,
                    "maintainability": 80.0,
                    "runtime_efficiency": 85.0,
                    "integration_score": 75.0
                }
            }
        },
        {
            "feature_id": "feature_2", 
            "feature_name": "Low Performance Feature",
            "state": FeatureDevelopmentState.COMPLETED.name,
            "performance": {
                "overall_score": 45.0,
                "metrics": {
                    "code_quality": 40.0,
                    "test_coverage": 35.0,
                    "build_stability": 65.0,
                    "maintainability": 40.0,
                    "runtime_efficiency": 50.0,
                    "integration_score": 40.0
                }
            }
        },
        {
            "feature_id": "feature_3", 
            "feature_name": "Medium Performance Feature",
            "state": FeatureDevelopmentState.COMPLETED.name,
            "performance": {
                "overall_score": 65.0,
                "metrics": {
                    "code_quality": 60.0,
                    "test_coverage": 70.0,
                    "build_stability": 65.0,
                    "maintainability": 60.0,
                    "runtime_efficiency": 65.0,
                    "integration_score": 70.0
                }
            }
        }
    ]

@pytest.fixture
def mock_evaluation_result():
    """Mock evaluation result from NaturalSelectionAgent."""
    return {
        "feature_rankings": [
            {
                "feature_id": "feature_1",
                "feature_name": "High Performance Feature",
                "rank": 1,
                "overall_score": 85.0,
                "strengths": ["High code quality", "Strong build stability"],
                "weaknesses": ["Integration could be improved"]
            },
            {
                "feature_id": "feature_3",
                "feature_name": "Medium Performance Feature",
                "rank": 2,
                "overall_score": 65.0,
                "strengths": ["Good test coverage", "Decent integration"],
                "weaknesses": ["Average code quality", "Could be more maintainable"]
            },
            {
                "feature_id": "feature_2",
                "feature_name": "Low Performance Feature",
                "rank": 3,
                "overall_score": 45.0,
                "strengths": ["Reasonable build stability"],
                "weaknesses": ["Poor code quality", "Low test coverage", "Difficult to maintain"]
            }
        ],
        "optimization_decisions": [
            {
                "feature_id": "feature_1",
                "decision": "keep",
                "rationale": "High-performing feature with good metrics across the board"
            },
            {
                "feature_id": "feature_2",
                "decision": "replace",
                "rationale": "Low-performing feature with multiple critical weaknesses"
            },
            {
                "feature_id": "feature_3",
                "decision": "improve",
                "rationale": "Medium-performing feature that could benefit from targeted improvements"
            }
        ],
        "evolution_strategy": {
            "reuse_opportunities": [
                {
                    "source_feature_id": "feature_1",
                    "target_feature_id": "feature_2",
                    "adaptations": ["Adapt high-quality code structure to feature_2's purpose"]
                }
            ],
            "refactor_suggestions": [
                {
                    "feature_id": "feature_3",
                    "suggestions": ["Improve documentation", "Extract common patterns into helpers"]
                }
            ],
            "feature_combinations": []
        },
        "phase_zero_feedback": {
            "requirements_analysis": {
                "completion_gaps": [],
                "consistency_issues": []
            },
            "implementation_analysis": {
                "code_structure_issues": [],
                "quality_metrics": {}
            },
            "evolution_opportunities": {
                "reuse_patterns": [
                    {
                        "source_feature_id": "feature_1",
                        "target_feature_id": "feature_2",
                        "adaptations": ["Use similar code structure", "Adapt core functionality"]
                    }
                ],
                "feature_combinations": []
            }
        }
    }

# Mocks and helpers
class MockStateManager:
    """Mock StateManager for testing."""
    
    def __init__(self):
        self.states = {}
        
    async def set_state(self, key, value, resource_type=ResourceType.STATE):
        self.states[key] = value
        
    async def get_state(self, key):
        return self.states.get(key)

class MockFeatureDevelopment:
    """Mock ParallelFeatureDevelopment for testing."""
    
    def __init__(self):
        self.features = {}
        self.started_features = []
        
    async def get_feature_status(self, feature_id):
        return self.features.get(feature_id, {"feature_id": feature_id, "error": "Feature not found"})
        
    async def start_feature_development(self, feature_metadata):
        feature_id = feature_metadata.get("id")
        self.started_features.append(feature_id)
        self.features[feature_id] = feature_metadata
        return feature_id
        
    async def get_all_feature_statuses(self):
        return self.features

# Tests
@pytest.mark.asyncio
async def test_natural_selection_agent_evaluate_features(mock_evaluation_result):
    """Test the NaturalSelectionAgent evaluate_features method."""
    # Create mocks with all necessary async methods
    event_queue = mock.MagicMock()
    state_manager = MockStateManager()
    context_manager = mock.MagicMock()
    cache_manager = mock.MagicMock()
    metrics_manager = mock.MagicMock()
    metrics_manager.record_metric = mock.AsyncMock()
    error_handler = mock.MagicMock()
    
    # Mock the air_agent and fire_agent imports to prevent import errors
    with mock.patch('resources.air_agent.provide_natural_selection_context', return_value=None), \
         mock.patch('resources.fire_agent.analyze_feature_complexity', return_value=mock.MagicMock(exceeds_threshold=False)), \
         mock.patch('resources.fire_agent.decompose_complex_feature'), \
         mock.patch('resources.air_agent.track_decision_event'):
        
        # Create agent with mocked process_with_validation
        agent = NaturalSelectionAgent(
            event_queue, state_manager, context_manager,
            cache_manager, metrics_manager, error_handler
        )
        
        # Mock the agent's set_agent_state method to prevent state-related issues
        agent.set_agent_state = mock.AsyncMock()
        
        # Mock the process_with_validation method
        agent.process_with_validation = mock.AsyncMock(return_value=mock_evaluation_result)
        
        # Set up requirements analysis agent mock
        agent._requirements_analysis_agent.process_with_validation = mock.AsyncMock(
            return_value={"completion_gaps": [], "consistency_issues": []}
        )
        
        # Set up implementation analysis agent mock
        agent._implementation_analysis_agent.process_with_validation = mock.AsyncMock(
            return_value={"code_structure_issues": [], "quality_metrics": {}}
        )
        
        # Set up evolution agent mock
        agent._evolution_agent.process_with_validation = mock.AsyncMock(
            return_value={"feature_combinations": [], "reuse_patterns": []}
        )
        
        # Test the evaluate_features method
        feature_performances = [
            {"feature_id": "feature_1", "feature_name": "Feature 1", "state": "COMPLETED"},
            {"feature_id": "feature_2", "feature_name": "Feature 2", "state": "COMPLETED"}
        ]
        
        try:
            result = await agent.evaluate_features(feature_performances, "test_op_id")
            
            # Print the result to debug what happened
            print(f"Result: {result}")
            
            # If there's an error in the result, the method failed
            if result and "error" in result:
                print(f"Method failed with error: {result['error']}")
            elif result is None:
                print("Method returned None - likely an unhandled exception occurred")
                
        except Exception as e:
            print(f"Exception raised during evaluate_features: {e}")
            print(f"Exception type: {type(e)}")
            raise
            
        # Verify the calls to phase zero agents
        agent._requirements_analysis_agent.process_with_validation.assert_called_once()
        agent._implementation_analysis_agent.process_with_validation.assert_called_once()
        agent._evolution_agent.process_with_validation.assert_called_once()
        
        # Verify the call to process_with_validation
        agent.process_with_validation.assert_called_once()
    
    # Verify the result contains optimization decisions
    assert "optimization_decisions" in result
    assert isinstance(result["optimization_decisions"], list)
    
    # Verify decisions for each feature
    feature_decisions = {d["feature_id"]: d["decision"] for d in result["optimization_decisions"]}
    assert feature_decisions["feature_1"] == "keep"
    assert feature_decisions["feature_2"] == "replace"
    assert feature_decisions["feature_3"] == "improve"

@pytest.mark.asyncio
async def test_apply_evolution_decisions(mock_evaluation_result):
    """Test the _apply_evolution_decisions method."""
    # Create mocks
    event_queue = mock.MagicMock()
    state_manager = MockStateManager()
    context_manager = mock.MagicMock()
    cache_manager = mock.MagicMock()
    metrics_manager = mock.MagicMock()
    metrics_manager.record_metric = mock.AsyncMock()
    error_handler = mock.MagicMock()
    
    # Create PhaseThreeInterface with mocked dependencies
    phase_four_interface = mock.MagicMock()
    phase_four_interface.process_feature_improvement = mock.AsyncMock(
        return_value={"success": True, "improved_code": "# Improved code"}
    )
    
    # Create feature development mock
    feature_development = MockFeatureDevelopment()
    
    # Create PhaseThreeInterface
    interface = PhaseThreeInterface(
        event_queue, state_manager, context_manager,
        cache_manager, metrics_manager, error_handler
    )
    
    # Set mocked dependencies
    interface._feature_development = feature_development
    interface._phase_four_interface = phase_four_interface
    
    # Mock methods
    interface._replace_feature = mock.AsyncMock(
        return_value={"status": "success", "replacement_id": "feature_2_replacement"}
    )
    interface._improve_feature = mock.AsyncMock(
        return_value={"status": "success", "improvements": ["Better error handling"]}
    )
    interface._combine_features = mock.AsyncMock(
        return_value={"status": "success", "combined_id": "combined_feature"}
    )
    
    # Test apply_evolution_decisions
    result = await interface._apply_evolution_decisions(mock_evaluation_result)
    
    # Verify decisions were applied
    assert result["total_decisions"] == 3
    assert result["applied_decisions"] == 2  # replace and improve (keep doesn't need action)
    
    # Verify specific method calls
    interface._replace_feature.assert_called_once_with(
        "feature_2", 
        "Low-performing feature with multiple critical weaknesses",
        mock_evaluation_result
    )
    
    interface._improve_feature.assert_called_once_with(
        "feature_3", 
        "Medium-performing feature that could benefit from targeted improvements",
        mock_evaluation_result
    )
    
    # Verify no combination was attempted (none in the test data)
    interface._combine_features.assert_not_called()

@pytest.mark.asyncio
async def test_feature_replacement():
    """Test the feature replacement functionality."""
    # Create mocks
    event_queue = mock.MagicMock()
    event_queue.publish = mock.AsyncMock()
    state_manager = MockStateManager()
    context_manager = mock.MagicMock()
    cache_manager = mock.MagicMock()
    metrics_manager = mock.MagicMock()
    metrics_manager.record_metric = mock.AsyncMock()
    error_handler = mock.MagicMock()
    
    # Create feature development mock
    feature_development = MockFeatureDevelopment()
    feature_development.features["feature_to_replace"] = {
        "feature_id": "feature_to_replace",
        "feature_name": "Feature To Replace",
        "state": "COMPLETED",
        "dependencies": ["dep1", "dep2"],
        "requirements": {"functional": ["req1", "req2"]}
    }
    
    # Create PhaseThreeInterface
    interface = PhaseThreeInterface(
        event_queue, state_manager, context_manager,
        cache_manager, metrics_manager, error_handler
    )
    
    # Set mocked dependencies
    interface._feature_development = feature_development
    interface._event_queue = event_queue
    
    # Set up evaluation data
    evaluation_data = {
        "phase_zero_feedback": {
            "evolution_opportunities": {
                "reuse_patterns": [
                    {
                        "source_feature_id": "good_feature",
                        "target_feature_id": "feature_to_replace",
                        "adaptations": ["Use similar structure"]
                    }
                ]
            }
        }
    }
    
    # Test feature replacement
    replacement_result = await interface._replace_feature(
        "feature_to_replace", 
        "Low performance", 
        evaluation_data
    )
    
    # Verify replacement was successful
    assert replacement_result["status"] == "success"
    assert "replacement_id" in replacement_result
    assert replacement_result["original_id"] == "feature_to_replace"
    
    # Verify feature was disabled
    assert "feature:development:feature_to_replace" in state_manager.states
    assert state_manager.states["feature:development:feature_to_replace"]["state"] == "DISABLED"
    
    # Verify replacement relationship was recorded
    assert f"feature:replacement:feature_to_replace" in state_manager.states
    
    # Verify new feature was started
    assert replacement_result["replacement_id"] in feature_development.started_features
    
    # Verify we detected the reuse pattern from evaluation data
    assert replacement_result["method"] == "reuse"
    
    # Verify event was published
    event_queue.publish.assert_called_once()
    
    # Verify metrics were recorded
    assert metrics_manager.record_metric.call_count >= 2

@pytest.mark.asyncio
async def test_feature_improvement():
    """Test the feature improvement functionality."""
    # Create mocks
    event_queue = mock.MagicMock()
    state_manager = MockStateManager()
    context_manager = mock.MagicMock()
    cache_manager = mock.MagicMock()
    metrics_manager = mock.MagicMock()
    metrics_manager.record_metric = mock.AsyncMock()
    error_handler = mock.MagicMock()
    
    # Create feature development mock
    feature_development = MockFeatureDevelopment()
    feature_development.features["feature_to_improve"] = {
        "feature_id": "feature_to_improve",
        "feature_name": "Feature To Improve",
        "state": "COMPLETED"
    }
    
    # Set up state for feature implementation
    state_manager.states["feature:implementation:feature_to_improve"] = {
        "implementation": "# Original implementation code"
    }
    
    # Create phase four interface mock
    phase_four_interface = mock.MagicMock()
    phase_four_interface.process_feature_improvement = mock.AsyncMock(
        return_value={
            "success": True,
            "improved_code": "# Improved implementation code",
            "improvements_applied": [
                {"description": "Better error handling", "changes": "Added try/except"}
            ]
        }
    )
    
    # Create PhaseThreeInterface
    interface = PhaseThreeInterface(
        event_queue, state_manager, context_manager,
        cache_manager, metrics_manager, error_handler
    )
    
    # Set mocked dependencies
    interface._feature_development = feature_development
    interface._phase_four_interface = phase_four_interface
    
    # Set up evaluation data
    evaluation_data = {
        "key_patterns": [
            {
                "issue": "Poor error handling",
                "affected_areas": ["code_quality"],
                "signals": [
                    {
                        "primary_agent": "implementation_analysis",
                        "key_evidence": ["Error handling is insufficient"]
                    }
                ]
            }
        ],
        "adaptations": [
            {
                "strategy": "Improve error handling",
                "addresses": ["feature_to_improve"],
                "implementation": "Add try/except blocks and proper error logging"
            }
        ]
    }
    
    # Test feature improvement
    improvement_result = await interface._improve_feature(
        "feature_to_improve", 
        "Needs better error handling", 
        evaluation_data
    )
    
    # Verify improvement was successful
    assert improvement_result["status"] == "success"
    assert "improvements" in improvement_result
    
    # Verify phase four was called correctly
    phase_four_interface.process_feature_improvement.assert_called_once()
    call_args = phase_four_interface.process_feature_improvement.call_args[0][0]
    assert call_args["id"] == "feature_to_improve"
    assert call_args["original_implementation"] == "# Original implementation code"
    assert "improvements" in call_args
    
    # Verify improvement task was stored
    improvement_id = None
    for key in state_manager.states.keys():
        if key.startswith("feature:improvement:improve_feature_to_improve"):
            improvement_id = key
            break
    assert improvement_id is not None
    assert state_manager.states[improvement_id]["status"] == "completed"
    
    # Verify implementation was updated
    assert "feature:implementation:feature_to_improve" in state_manager.states
    assert state_manager.states["feature:implementation:feature_to_improve"]["implementation"] == "# Improved implementation code"
    
    # Verify metrics were recorded
    assert metrics_manager.record_metric.call_count >= 2

@pytest.mark.asyncio
async def test_feature_evolutionary_selection(feature_performance_data, mock_evaluation_result):
    """Test the complete feature evolutionary selection process."""
    # Create mocks
    event_queue = mock.MagicMock()
    state_manager = MockStateManager()
    context_manager = mock.MagicMock()
    cache_manager = mock.MagicMock()
    metrics_manager = mock.MagicMock()
    metrics_manager.record_metric = mock.AsyncMock()
    error_handler = mock.MagicMock()
    
    # Create feature development mock
    feature_development = MockFeatureDevelopment()
    for feature in feature_performance_data:
        feature_id = feature["feature_id"]
        feature_development.features[feature_id] = feature
    
    # Create phase four interface mock
    phase_four_interface = mock.MagicMock()
    phase_four_interface.process_feature_improvement = mock.AsyncMock(
        return_value={"success": True, "improved_code": "# Improved code"}
    )
    
    # Create PhaseThreeInterface
    interface = PhaseThreeInterface(
        event_queue, state_manager, context_manager,
        cache_manager, metrics_manager, error_handler
    )
    
    # Set mocked dependencies
    interface._feature_development = feature_development
    interface._phase_four_interface = phase_four_interface
    
    # Create natural selection agent with mocked process_with_validation
    natural_selection_agent = NaturalSelectionAgent(
        event_queue, state_manager, context_manager,
        cache_manager, metrics_manager, error_handler
    )
    
    # Mock the process_with_validation method
    natural_selection_agent.process_with_validation = mock.AsyncMock(return_value=mock_evaluation_result)
    
    # Set up requirements analysis agent mock
    natural_selection_agent._requirements_analysis_agent.process_with_validation = mock.AsyncMock(
        return_value={"completion_gaps": [], "consistency_issues": []}
    )
    
    # Set up implementation analysis agent mock
    natural_selection_agent._implementation_analysis_agent.process_with_validation = mock.AsyncMock(
        return_value={"code_structure_issues": [], "quality_metrics": {}}
    )
    
    # Set up evolution agent mock
    natural_selection_agent._evolution_agent.process_with_validation = mock.AsyncMock(
        return_value={"feature_combinations": [], "reuse_patterns": []}
    )
    
    # Replace interface's natural selection agent
    interface._natural_selection_agent = natural_selection_agent
    
    # Mock the apply evolution decisions method
    original_apply_evolution_decisions = interface._apply_evolution_decisions
    interface._apply_evolution_decisions = mock.AsyncMock(side_effect=original_apply_evolution_decisions)
    
    # Set last evaluation time to make sure evaluation runs
    interface._last_evaluation_time = 0
    
    # Test the evaluate_feature_evolution method
    result = await interface.evaluate_feature_evolution()
    
    # Verify evaluation was successful
    assert result["status"] == "completed"
    assert "evaluation_result" in result
    assert "applied_decisions" in result
    
    # Verify natural selection agent was called
    natural_selection_agent.evaluate_features.assert_called_once()
    
    # Verify apply_evolution_decisions was called
    interface._apply_evolution_decisions.assert_called_once()
    
    # Check that decisions were applied correctly
    applied_decisions = result["applied_decisions"]
    assert applied_decisions["total_decisions"] == 3
    
    # Verify metrics were recorded
    assert metrics_manager.record_metric.call_count >= 2
    
    # Verify evaluation state was stored
    assert any(key.startswith("phase_three:evolution:") for key in state_manager.states.keys())