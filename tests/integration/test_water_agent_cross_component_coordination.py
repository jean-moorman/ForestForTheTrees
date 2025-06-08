"""
Integration tests for Water Agent cross-component coordination scenarios.

This module tests the Water Agent's integration with various FFTT system components
including Phase One agents, Phase Zero feedback integration, and multi-agent
coordination workflows.
"""

import pytest
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from resources import (
    EventQueue,
    StateManager,
    AgentContextManager,
    CacheManager,
    MetricsManager,
    ResourceType
)
from resources.monitoring import HealthTracker, MemoryMonitor
from resources.errors import ErrorHandler, CoordinationError
from resources.water_agent import WaterAgentCoordinator
from resources.water_agent.reflective import WaterAgentReflective
from resources.water_agent.context_manager import WaterAgentContextManager, CoordinationContext

from phase_one.validation.coordination import SequentialAgentCoordinator
from phase_one.agents.garden_planner import GardenPlannerAgent
from phase_one.agents.earth_agent import EarthAgent
from phase_one.agents.environmental_analysis import EnvironmentalAnalysisAgent
from phase_one.agents.root_system_architect import RootSystemArchitectAgent
from phase_one.agents.tree_placement_planner import TreePlacementPlannerAgent
from phase_one.models.enums import DevelopmentState
from interfaces.agent.coordination import CoordinationInterface


@pytest.fixture
def mock_event_queue():
    """Create a mock event queue for testing."""
    queue = AsyncMock(spec=EventQueue)
    queue.emit = AsyncMock()
    queue.subscribe = AsyncMock()
    return queue


@pytest.fixture
def mock_state_manager():
    """Create a mock state manager for testing."""
    state_manager = AsyncMock(spec=StateManager)
    state_manager.get_state = AsyncMock(return_value=None)
    state_manager.set_state = AsyncMock(return_value=True)
    state_manager.find_keys = AsyncMock(return_value=[])
    state_manager.delete_state = AsyncMock(return_value=True)
    return state_manager


@pytest.fixture
def mock_context_manager():
    """Create a mock context manager for testing."""
    context_manager = AsyncMock(spec=AgentContextManager)
    context_manager.get_context = AsyncMock(return_value={})
    context_manager.set_context = AsyncMock(return_value=True)
    context_manager.update_context = AsyncMock(return_value=True)
    context_manager.create_context = AsyncMock(return_value={})
    return context_manager


@pytest.fixture
def mock_cache_manager():
    """Create a mock cache manager for testing."""
    cache_manager = AsyncMock(spec=CacheManager)
    cache_manager.get = AsyncMock(return_value=None)
    cache_manager.set = AsyncMock(return_value=True)
    cache_manager.invalidate = AsyncMock(return_value=True)
    return cache_manager


@pytest.fixture
def mock_metrics_manager():
    """Create a mock metrics manager for testing."""
    metrics_manager = AsyncMock(spec=MetricsManager)
    metrics_manager.record_metric = AsyncMock()
    metrics_manager.get_metric = AsyncMock(return_value=0)
    return metrics_manager


@pytest.fixture
def mock_error_handler():
    """Create a mock error handler for testing."""
    error_handler = AsyncMock(spec=ErrorHandler)
    error_handler.handle_error = AsyncMock()
    error_handler.is_recoverable = AsyncMock(return_value=True)
    return error_handler


@pytest.fixture
def mock_memory_monitor():
    """Create a mock memory monitor for testing."""
    memory_monitor = AsyncMock(spec=MemoryMonitor)
    memory_monitor.check_memory = AsyncMock(return_value={"status": "ok"})
    memory_monitor.get_usage = AsyncMock(return_value={"memory": 0.5})
    return memory_monitor


@pytest.fixture
def mock_health_tracker():
    """Create a mock health tracker for testing."""
    health_tracker = AsyncMock(spec=HealthTracker)
    health_tracker.track_metric = AsyncMock()
    health_tracker.get_health_status = AsyncMock(return_value={"status": "healthy"})
    return health_tracker


@pytest.fixture
def resource_managers(
    mock_event_queue,
    mock_state_manager,
    mock_context_manager,
    mock_cache_manager,
    mock_metrics_manager,
    mock_error_handler,
    mock_memory_monitor,
    mock_health_tracker
):
    """Create a set of resource managers for testing."""
    return {
        "event_queue": mock_event_queue,
        "state_manager": mock_state_manager,
        "context_manager": mock_context_manager,
        "cache_manager": mock_cache_manager,
        "metrics_manager": mock_metrics_manager,
        "error_handler": mock_error_handler,
        "memory_monitor": mock_memory_monitor,
        "health_tracker": mock_health_tracker
    }


@pytest.fixture
def water_agent_coordinator(resource_managers):
    """Create a WaterAgentCoordinator for testing."""
    with patch('resources.water_agent.context_manager.WaterAgentContextManager'), \
         patch('interfaces.agent.interface.AgentInterface'):
        coordinator = WaterAgentCoordinator(
            resource_id="test_water_coordinator",
            state_manager=resource_managers["state_manager"],
            event_bus=resource_managers["event_queue"]
        )
        
        # Mock the agent interface and internal components
        coordinator.agent_interface = MagicMock()
        coordinator.agent_interface.get_response = AsyncMock(return_value="Mock LLM response")
        coordinator._emit_event = AsyncMock()
        
        # Mock the detector and tracker components
        coordinator.misunderstanding_detector = MagicMock()
        coordinator.misunderstanding_detector.detect_misunderstandings = AsyncMock()
        coordinator.response_handler = MagicMock()
        coordinator.response_handler.get_agent_responses = AsyncMock()
        coordinator.resolution_tracker = MagicMock()
        coordinator.resolution_tracker.assess_resolution = AsyncMock()
        
        # Mock the main coordination method
        coordinator.coordinate_agents = AsyncMock(return_value=(
            "Updated first output", "Updated second output", {"status": "completed"}
        ))
        
        return coordinator


@pytest.fixture
def sequential_agent_coordinator(resource_managers, water_agent_coordinator):
    """Create a SequentialAgentCoordinator for testing."""
    with patch('phase_one.validation.coordination.WaterAgentCoordinator', return_value=water_agent_coordinator):
        coordinator = SequentialAgentCoordinator(
            event_queue=resource_managers["event_queue"],
            state_manager=resource_managers["state_manager"],
            max_coordination_attempts=3,
            coordination_timeout=10.0
        )
        return coordinator


@pytest.fixture
def mock_garden_planner():
    """Create a mock Garden Planner agent."""
    agent = MagicMock()
    agent.agent_id = "garden_planner_agent"
    agent.interface_id = "garden_planner_interface"
    agent.__class__.__name__ = "GardenPlannerAgent"
    agent.development_state = DevelopmentState.COMPLETE
    agent.clarify = AsyncMock(return_value="Garden planner clarification response")
    agent.get_response = AsyncMock(return_value={
        "structural_components": [
            {"name": "UserInterface", "description": "Web interface for users"},
            {"name": "DataLayer", "description": "Database management component"}
        ],
        "dependencies": [
            {"from": "UserInterface", "to": "DataLayer", "type": "uses"}
        ]
    })
    agent.coordination_interface = MagicMock()
    agent.coordination_interface.update_output = AsyncMock(return_value=True)
    return agent


@pytest.fixture
def mock_earth_agent():
    """Create a mock Earth agent."""
    agent = MagicMock()
    agent.agent_id = "earth_agent"
    agent.interface_id = "earth_agent_interface"
    agent.__class__.__name__ = "EarthAgent"
    agent.development_state = DevelopmentState.COMPLETE
    agent.clarify = AsyncMock(return_value="Earth agent validation response")
    agent.validate_garden_plan = AsyncMock(return_value={
        "validation_result": "approved",
        "issues": [],
        "recommendations": ["Consider adding error handling component"]
    })
    agent.coordination_interface = MagicMock()
    agent.coordination_interface.update_output = AsyncMock(return_value=True)
    return agent


@pytest.fixture
def mock_environmental_analysis_agent():
    """Create a mock Environmental Analysis agent."""
    agent = MagicMock()
    agent.agent_id = "environmental_analysis_agent"
    agent.interface_id = "environmental_analysis_interface"
    agent.__class__.__name__ = "EnvironmentalAnalysisAgent"
    agent.development_state = DevelopmentState.COMPLETE
    agent.clarify = AsyncMock(return_value="Environmental analysis clarification")
    agent.analyze_environment = AsyncMock(return_value={
        "environmental_factors": {
            "complexity": "medium",
            "scalability_requirements": "high",
            "integration_constraints": ["database_compatibility", "api_versioning"]
        },
        "recommendations": ["Use microservices architecture", "Implement caching layer"]
    })
    agent.coordination_interface = MagicMock()
    agent.coordination_interface.update_output = AsyncMock(return_value=True)
    return agent


@pytest.fixture
def mock_root_system_architect():
    """Create a mock Root System Architect agent."""
    agent = MagicMock()
    agent.agent_id = "root_system_architect_agent"
    agent.interface_id = "root_system_architect_interface"
    agent.__class__.__name__ = "RootSystemArchitectAgent"
    agent.development_state = DevelopmentState.COMPLETE
    agent.clarify = AsyncMock(return_value="Root system architect clarification")
    agent.design_root_system = AsyncMock(return_value={
        "root_architecture": {
            "foundation_patterns": ["singleton_database_connection", "factory_pattern_ui"],
            "dependency_management": "dependency_injection",
            "communication_protocols": ["REST_API", "message_queues"]
        },
        "integration_points": ["database_layer", "authentication_service"]
    })
    agent.coordination_interface = MagicMock()
    agent.coordination_interface.update_output = AsyncMock(return_value=True)
    return agent


class TestWaterAgentPhaseOneIntegration:
    """Test Water Agent integration with Phase One workflow components."""

    @pytest.mark.asyncio
    async def test_garden_planner_earth_agent_coordination(
        self,
        water_agent_coordinator,
        sequential_agent_coordinator,
        mock_garden_planner,
        mock_earth_agent
    ):
        """Test coordination between Garden Planner and Earth Agent."""
        # Setup garden planner output
        garden_plan = {
            "structural_components": [
                {"name": "UserInterface", "description": "Web interface"},
                {"name": "DataLayer", "description": "Database management"}
            ],
            "dependencies": [{"from": "UserInterface", "to": "DataLayer", "type": "uses"}]
        }
        
        # Setup earth agent validation
        earth_validation = {
            "validation_result": "approved_with_recommendations",
            "issues": [
                {
                    "severity": "medium",
                    "description": "Missing error handling in UserInterface",
                    "recommendation": "Add comprehensive error handling"
                }
            ],
            "recommendations": ["Consider adding logging component"]
        }
        
        # Mock coordination detecting misunderstanding about error handling
        water_agent_coordinator.misunderstanding_detector.detect_misunderstandings.return_value = (
            [
                {
                    "id": "error_handling_misunderstanding",
                    "description": "Garden planner didn't include error handling, Earth agent flagged it",
                    "severity": "MEDIUM",
                    "affected_elements": ["UserInterface"]
                }
            ],
            ["Can you clarify the error handling requirements for the UserInterface?"],
            ["What specific error handling patterns should be implemented?"]
        )
        
        # Mock agent responses
        water_agent_coordinator.response_handler.get_agent_responses.side_effect = [
            ["Error handling should include try-catch blocks and user-friendly error messages"],
            ["Implement global error handler with logging and user notification"]
        ]
        
        # Mock resolution tracking
        water_agent_coordinator.resolution_tracker.assess_resolution.return_value = (
            [
                {
                    "id": "error_handling_misunderstanding",
                    "resolution_summary": "Error handling requirements clarified and agreed upon"
                }
            ],
            [],  # No unresolved issues
            [],  # No additional questions for first agent
            []   # No additional questions for second agent
        )
        
        # Execute coordination
        updated_garden_plan, updated_earth_validation, metadata = await sequential_agent_coordinator.coordinate_interactive_handoff(
            mock_garden_planner,
            garden_plan,
            mock_earth_agent,
            earth_validation,
            "garden_plan_validation"
        )
        
        # Verify coordination occurred
        assert metadata["status"] == "completed"
        assert metadata["result"] in ["no_misunderstandings", "coordination_applied"]
        
        # Verify coordination was attempted (regardless of outcome)
        assert water_agent_coordinator.coordinate_agents.called
        
        # Verify state tracking
        sequential_agent_coordinator.state_manager.set_state.assert_called()

    @pytest.mark.asyncio
    async def test_sequential_phase_one_agent_coordination(
        self,
        water_agent_coordinator,
        sequential_agent_coordinator,
        mock_garden_planner,
        mock_environmental_analysis_agent,
        mock_root_system_architect
    ):
        """Test sequential coordination through multiple Phase One agents."""
        # Initial garden plan
        initial_plan = {
            "structural_components": [
                {"name": "WebApp", "description": "Main web application"}
            ]
        }
        
        # Environmental analysis output
        environmental_analysis = {
            "environmental_factors": {
                "complexity": "high",
                "scalability_requirements": "very_high"
            },
            "recommendations": ["Use microservices", "Implement caching"]
        }
        
        # Root system architecture
        root_architecture = {
            "foundation_patterns": ["microservice_pattern"],
            "dependency_management": "service_mesh"
        }
        
        # Mock no misunderstandings for first coordination
        water_agent_coordinator.misunderstanding_detector.detect_misunderstandings.return_value = ([], [], [])
        
        # First coordination: Garden Planner -> Environmental Analysis
        plan_after_env, env_after_coord, metadata1 = await sequential_agent_coordinator.coordinate_interactive_handoff(
            mock_garden_planner,
            initial_plan,
            mock_environmental_analysis_agent,
            environmental_analysis,
            "plan_environmental_analysis"
        )
        
        # Mock misunderstanding for second coordination
        water_agent_coordinator.misunderstanding_detector.detect_misunderstandings.return_value = (
            [
                {
                    "id": "architecture_pattern_misunderstanding",
                    "description": "Mismatch between recommended microservices and proposed monolith",
                    "severity": "HIGH"
                }
            ],
            ["Should the WebApp be split into microservices based on environmental analysis?"],
            ["How should the service mesh integrate with the proposed architecture?"]
        )
        
        water_agent_coordinator.response_handler.get_agent_responses.side_effect = [
            ["Yes, WebApp should be split into UserService and DataService"],
            ["Service mesh should handle inter-service communication and load balancing"]
        ]
        
        water_agent_coordinator.resolution_tracker.assess_resolution.return_value = (
            [{"id": "architecture_pattern_misunderstanding", "resolution_summary": "Architecture aligned with microservices pattern"}],
            [], [], []
        )
        
        # Second coordination: Environmental Analysis -> Root System Architect
        env_after_root, root_after_coord, metadata2 = await sequential_agent_coordinator.coordinate_interactive_handoff(
            mock_environmental_analysis_agent,
            environmental_analysis,
            mock_root_system_architect,
            root_architecture,
            "env_root_architecture"
        )
        
        # Verify both coordinations completed
        assert metadata1["status"] == "completed"
        assert metadata2["status"] == "completed"
        assert metadata2["result"] == "coordination_applied"
        
        # Verify sequential state tracking
        assert sequential_agent_coordinator.state_manager.set_state.call_count >= 4  # 2 coordinations × 2+ state updates each

    @pytest.mark.asyncio
    async def test_phase_zero_feedback_integration(
        self,
        water_agent_coordinator,
        mock_garden_planner,
        mock_earth_agent
    ):
        """Test Water Agent coordination with Phase Zero feedback integration."""
        # Simulate garden plan with Phase Zero feedback
        garden_plan_with_feedback = {
            "structural_components": [
                {"name": "UserInterface", "description": "Web interface"},
                {"name": "DataLayer", "description": "Database management"}
            ],
            "phase_zero_feedback": {
                "structural_breakdown_feedback": {
                    "issues": ["Missing authentication component"],
                    "recommendations": ["Add AuthenticationService component"]
                },
                "requirements_analysis_feedback": {
                    "missing_requirements": ["user_session_management"],
                    "conflicting_requirements": []
                }
            }
        }
        
        # Earth agent validation considering Phase Zero feedback
        earth_validation_with_feedback = {
            "validation_result": "requires_revision",
            "issues": [
                {
                    "severity": "high",
                    "description": "Phase Zero feedback indicates missing authentication",
                    "source": "phase_zero_structural_breakdown"
                }
            ],
            "phase_zero_alignment": {
                "structural_alignment": "partial",
                "missing_elements": ["AuthenticationService"]
            }
        }
        
        # Mock misunderstanding about Phase Zero feedback integration
        water_agent_coordinator.misunderstanding_detector.detect_misunderstandings.return_value = (
            [
                {
                    "id": "phase_zero_feedback_integration",
                    "description": "Garden planner may not have fully integrated Phase Zero feedback",
                    "severity": "HIGH",
                    "affected_elements": ["authentication", "structural_components"],
                    "phase_zero_context": True
                }
            ],
            ["How should the Phase Zero feedback about missing authentication be integrated?"],
            ["Should the AuthenticationService be a separate component or integrated into existing ones?"]
        )
        
        # Mock responses considering Phase Zero feedback
        water_agent_coordinator.response_handler.get_agent_responses.side_effect = [
            ["AuthenticationService should be a separate component with clear interfaces to UserInterface and DataLayer"],
            ["Separate component is preferred for security isolation and maintainability"]
        ]
        
        water_agent_coordinator.resolution_tracker.assess_resolution.return_value = (
            [
                {
                    "id": "phase_zero_feedback_integration",
                    "resolution_summary": "Phase Zero feedback integrated with AuthenticationService as separate component"
                }
            ],
            [], [], []
        )
        
        # Execute coordination with Phase Zero context
        updated_plan, updated_validation, metadata = await water_agent_coordinator.coordinate_agents(
            mock_garden_planner,
            garden_plan_with_feedback,
            mock_earth_agent,
            earth_validation_with_feedback
        )
        
        # Verify Phase Zero feedback was considered in coordination
        assert "phase_zero_context" in str(water_agent_coordinator.misunderstanding_detector.detect_misunderstandings.call_args)
        
        # Verify coordination completed successfully
        assert len(updated_plan) > 0  # Should have updated plan
        assert len(updated_validation) > 0  # Should have updated validation


class TestWaterAgentReflectiveIntegration:
    """Test integration of WaterAgentReflective with other system components."""

    @pytest.fixture
    def water_agent_reflective(self, resource_managers):
        """Create a WaterAgentReflective for integration testing."""
        agent = WaterAgentReflective(
            agent_id="test_water_reflective",
            event_queue=resource_managers["event_queue"],
            state_manager=resource_managers["state_manager"],
            context_manager=resource_managers["context_manager"],
            cache_manager=resource_managers["cache_manager"],
            metrics_manager=resource_managers["metrics_manager"],
            error_handler=resource_managers["error_handler"],
            memory_monitor=resource_managers["memory_monitor"],
            health_tracker=resource_managers["health_tracker"],
            max_reflection_cycles=3
        )
        
        # Mock the circuit breaker and processing methods
        agent.get_circuit_breaker = MagicMock()
        mock_circuit_breaker = AsyncMock()
        mock_circuit_breaker.execute = AsyncMock()
        agent.get_circuit_breaker.return_value = mock_circuit_breaker
        
        agent.process_with_validation = AsyncMock()
        agent.standard_reflect = AsyncMock()
        agent.standard_refine = AsyncMock()
        
        return agent

    @pytest.mark.asyncio
    async def test_reflective_misunderstanding_detection_with_phase_one_agents(
        self,
        water_agent_reflective,
        mock_garden_planner,
        mock_earth_agent
    ):
        """Test reflective misunderstanding detection between Phase One agents."""
        # Mock garden planner output
        garden_output = json.dumps({
            "structural_components": [
                {"name": "UserInterface", "description": "Basic web interface"}
            ]
        })
        
        # Mock earth agent output
        earth_output = json.dumps({
            "validation_result": "needs_improvement",
            "issues": ["Interface lacks accessibility features"]
        })
        
        # Mock initial detection result
        initial_detection = {
            "misunderstandings": [
                {
                    "id": "accessibility_gap",
                    "description": "Interface design doesn't address accessibility",
                    "severity": "MEDIUM"
                }
            ],
            "first_agent_questions": ["What accessibility features should be included?"],
            "second_agent_questions": ["Are there specific accessibility standards to follow?"]
        }
        
        # Mock reflection suggesting critical improvement
        reflection_result = {
            "reflection_results": {
                "overall_assessment": {
                    "critical_improvements": [
                        {
                            "importance": "critical",
                            "description": "Severity should be HIGH for accessibility issues",
                            "area": "severity_assessment"
                        }
                    ]
                },
                "detection_quality": {
                    "accuracy": "good",
                    "completeness": "partial",
                    "suggestions": ["Consider legal compliance aspects"]
                }
            }
        }
        
        # Mock revision result
        revision_result = {
            "revised_detection": {
                "misunderstandings": [
                    {
                        "id": "accessibility_gap",
                        "description": "Interface design doesn't address accessibility requirements (legal compliance issue)",
                        "severity": "HIGH",
                        "compliance_aspects": ["WCAG_2.1", "ADA_compliance"]
                    }
                ],
                "first_agent_questions": [
                    "What accessibility features should be included for WCAG 2.1 compliance?",
                    "How should keyboard navigation be implemented?"
                ],
                "second_agent_questions": [
                    "Are there specific accessibility standards to follow for legal compliance?",
                    "What testing procedures should be used for accessibility validation?"
                ]
            },
            "needs_further_reflection": False,
            "improvement_summary": {
                "severity_upgraded": True,
                "questions_expanded": True,
                "compliance_context_added": True
            }
        }
        
        # Setup mocks
        water_agent_reflective.get_circuit_breaker().execute.return_value = initial_detection
        water_agent_reflective.standard_reflect.return_value = reflection_result
        water_agent_reflective.standard_refine.return_value = revision_result
        
        # Execute reflective detection
        result = await water_agent_reflective.detect_misunderstandings(
            garden_output,
            earth_output,
            use_reflection=True
        )
        
        # Verify reflection improved the detection
        assert result == revision_result["revised_detection"]
        assert result["misunderstandings"][0]["severity"] == "HIGH"
        assert "compliance_aspects" in result["misunderstandings"][0]
        assert len(result["first_agent_questions"]) == 2
        assert len(result["second_agent_questions"]) == 2
        
        # Verify reflection and refinement were called
        water_agent_reflective.standard_reflect.assert_called_once()
        water_agent_reflective.standard_refine.assert_called_once()
        
        # Verify state persistence
        assert water_agent_reflective._state_manager.set_state.call_count >= 3  # context + reflection + revision

    @pytest.mark.asyncio
    async def test_reflective_coordination_with_circuit_breaker_failures(
        self,
        water_agent_reflective,
        mock_garden_planner,
        mock_environmental_analysis_agent
    ):
        """Test reflective coordination with circuit breaker failures and recovery."""
        garden_output = "Garden planner structural analysis output"
        env_output = "Environmental analysis output"
        
        # Simulate circuit breaker opening during initial detection
        water_agent_reflective.get_circuit_breaker().execute.side_effect = [
            Exception("Circuit breaker open"),  # First attempt fails
            {  # Second attempt succeeds
                "misunderstandings": [],
                "first_agent_questions": [],
                "second_agent_questions": []
            }
        ]
        
        # First call should fail and return error result
        result1 = await water_agent_reflective.detect_misunderstandings(
            garden_output,
            env_output,
            use_reflection=True
        )
        
        assert "error" in result1
        assert water_agent_reflective.development_state == DevelopmentState.ERROR
        
        # Reset state for second attempt
        water_agent_reflective.development_state = DevelopmentState.INITIALIZING
        
        # Second call should succeed
        result2 = await water_agent_reflective.detect_misunderstandings(
            garden_output,
            env_output,
            use_reflection=False
        )
        
        assert "error" not in result2
        assert water_agent_reflective.development_state == DevelopmentState.COMPLETE


class TestWaterAgentMultiAgentCoordination:
    """Test Water Agent coordination with multiple agents in complex scenarios."""

    @pytest.mark.asyncio
    async def test_three_agent_sequential_coordination(
        self,
        water_agent_coordinator,
        sequential_agent_coordinator,
        mock_garden_planner,
        mock_environmental_analysis_agent,
        mock_root_system_architect
    ):
        """Test coordination between three agents in sequence."""
        # Initial outputs
        garden_plan = {"components": ["WebApp"]}
        env_analysis = {"complexity": "high", "patterns": ["microservices"]}
        root_design = {"architecture": "service_mesh"}
        
        # Mock coordination 1: Garden -> Environmental (no issues)
        water_agent_coordinator.misunderstanding_detector.detect_misunderstandings.return_value = ([], [], [])
        
        result1, metadata1 = await sequential_agent_coordinator.coordinate_agent_handoff(
            mock_garden_planner,
            garden_plan,
            mock_environmental_analysis_agent,
            "garden_to_env"
        )
        
        # Mock coordination 2: Environmental -> Root (with issues)
        water_agent_coordinator.misunderstanding_detector.detect_misunderstandings.return_value = (
            [{"id": "pattern_mismatch", "description": "Architecture pattern mismatch", "severity": "HIGH"}],
            ["Should microservices pattern influence the root architecture design?"],
            ["How should service mesh accommodate the microservices recommendation?"]
        )
        
        water_agent_coordinator.response_handler.get_agent_responses.side_effect = [
            ["Yes, root architecture should support microservices deployment"],
            ["Service mesh will provide inter-service communication infrastructure"]
        ]
        
        water_agent_coordinator.resolution_tracker.assess_resolution.return_value = (
            [{"id": "pattern_mismatch", "resolution_summary": "Architecture patterns aligned"}],
            [], [], []
        )
        
        result2, metadata2 = await sequential_agent_coordinator.coordinate_agent_handoff(
            mock_environmental_analysis_agent,
            env_analysis,
            mock_root_system_architect,
            "env_to_root"
        )
        
        # Verify both coordinations completed
        assert metadata1["status"] == "completed"
        assert metadata2["status"] == "completed"
        assert metadata2["result"] == "coordination_applied"
        
        # Verify sequence of state updates
        state_calls = sequential_agent_coordinator.state_manager.set_state.call_args_list
        assert len(state_calls) >= 4  # Multiple state updates across coordinations

    @pytest.mark.asyncio
    async def test_parallel_coordination_conflict_resolution(
        self,
        water_agent_coordinator,
        mock_garden_planner,
        mock_earth_agent,
        mock_environmental_analysis_agent
    ):
        """Test resolution of conflicts when multiple coordinations happen in parallel."""
        # Simulate parallel coordination requests
        garden_plan = {"components": ["WebApp", "DatabaseService"]}
        earth_validation = {"validation": "conditional_approval"}
        env_analysis = {"recommendations": ["split_database", "add_caching"]}
        
        # Mock different misunderstandings for each coordination
        misunderstanding_results = [
            # Garden -> Earth coordination
            (
                [{"id": "db_design_issue", "description": "Database design concerns", "severity": "MEDIUM"}],
                ["Should DatabaseService be monolithic or split?"],
                ["What are the specific database design concerns?"]
            ),
            # Garden -> Environmental coordination  
            (
                [{"id": "scalability_issue", "description": "Scalability requirements unclear", "severity": "HIGH"}],
                ["What are the expected scalability requirements?"],
                ["How should caching be integrated with the current design?"]
            )
        ]
        
        water_agent_coordinator.misunderstanding_detector.detect_misunderstandings.side_effect = misunderstanding_results
        
        # Mock responses for both coordinations
        response_sequences = [
            [["DatabaseService should remain unified for consistency"], ["Unified database is acceptable for current scale"]],
            [["Expect 10x growth within 2 years"], ["Implement Redis caching layer between WebApp and DatabaseService"]]
        ]
        water_agent_coordinator.response_handler.get_agent_responses.side_effect = response_sequences
        
        # Mock resolutions
        resolution_results = [
            ([{"id": "db_design_issue", "resolution_summary": "Database design approach agreed"}], [], [], []),
            ([{"id": "scalability_issue", "resolution_summary": "Scalability approach with caching agreed"}], [], [], [])
        ]
        water_agent_coordinator.resolution_tracker.assess_resolution.side_effect = resolution_results
        
        # Execute parallel coordinations
        coordination_tasks = [
            water_agent_coordinator.coordinate_agents(
                mock_garden_planner, garden_plan, mock_earth_agent, earth_validation
            ),
            water_agent_coordinator.coordinate_agents(
                mock_garden_planner, garden_plan, mock_environmental_analysis_agent, env_analysis
            )
        ]
        
        results = await asyncio.gather(*coordination_tasks, return_exceptions=True)
        
        # Verify both coordinations completed (or handled gracefully)
        for result in results:
            if isinstance(result, Exception):
                pytest.fail(f"Coordination failed with exception: {result}")
            else:
                assert len(result) == 3  # (updated_first_output, updated_second_output, metadata)

    @pytest.mark.asyncio
    async def test_coordination_context_persistence_across_sessions(
        self,
        resource_managers,
        mock_garden_planner,
        mock_earth_agent
    ):
        """Test that coordination context persists across multiple coordination sessions."""
        # Create context manager
        context_manager = WaterAgentContextManager(
            state_manager=resource_managers["state_manager"],
            event_bus=resource_managers["event_queue"]
        )
        
        # Create initial coordination context
        coordination_id = "persistent_coordination_test"
        context = await context_manager.create_coordination_context(
            first_agent_id=mock_garden_planner.agent_id,
            second_agent_id=mock_earth_agent.agent_id,
            coordination_id=coordination_id
        )
        
        # Simulate multiple iterations
        for iteration in range(3):
            context.update_iteration(
                iteration=iteration + 1,
                first_agent_questions=[f"Question {iteration + 1} for garden planner"],
                first_agent_responses=[f"Response {iteration + 1} from garden planner"],
                second_agent_questions=[f"Question {iteration + 1} for earth agent"],
                second_agent_responses=[f"Response {iteration + 1} from earth agent"],
                resolved=[],
                unresolved=[{"id": f"issue_{iteration + 1}", "severity": "LOW"}] if iteration < 2 else []
            )
        
        # Complete the coordination
        context.complete(
            first_agent_final_output="Final garden plan with all feedback integrated",
            second_agent_final_output="Final earth validation with all concerns addressed",
            final_status="all_issues_resolved"
        )
        
        # Update context in state manager
        await context_manager.update_coordination_context(context)
        
        # Verify context persistence
        assert context.status == "completed"
        assert len(context.iterations) == 3
        assert context.final_status == "all_issues_resolved"
        
        # Test context retrieval
        resource_managers["state_manager"].get_state.return_value = context.to_dict()
        retrieved_context = await context_manager.get_coordination_context(coordination_id)
        
        assert retrieved_context is not None
        assert retrieved_context.coordination_id == coordination_id
        assert retrieved_context.status == "completed"
        assert len(retrieved_context.iterations) == 3

    @pytest.mark.asyncio
    async def test_coordination_performance_under_load(
        self,
        water_agent_coordinator,
        sequential_agent_coordinator,
        mock_garden_planner,
        mock_earth_agent
    ):
        """Test coordination performance under high load scenarios."""
        # Setup for load testing
        num_concurrent_coordinations = 10
        coordination_results = []
        
        # Mock fast responses for load testing
        water_agent_coordinator.misunderstanding_detector.detect_misunderstandings.return_value = ([], [], [])
        
        # Create multiple concurrent coordination tasks
        tasks = []
        for i in range(num_concurrent_coordinations):
            task = sequential_agent_coordinator.coordinate_agent_handoff(
                mock_garden_planner,
                {"plan_id": f"plan_{i}", "components": [f"Component_{i}"]},
                mock_earth_agent,
                f"load_test_operation_{i}"
            )
            tasks.append(task)
        
        # Execute all coordinations concurrently
        start_time = datetime.now()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = datetime.now()
        
        # Verify all coordinations completed successfully
        successful_coordinations = 0
        for result in results:
            if isinstance(result, Exception):
                print(f"Coordination failed: {result}")
            else:
                successful_coordinations += 1
                result_data, metadata = result
                assert metadata["status"] in ["completed", "timeout", "error"]
        
        # Verify performance metrics
        total_time = (end_time - start_time).total_seconds()
        assert successful_coordinations > 0, "At least some coordinations should succeed"
        
        # Log performance results
        print(f"Completed {successful_coordinations}/{num_concurrent_coordinations} coordinations in {total_time:.2f} seconds")
        
        # Verify resource usage was tracked
        assert sequential_agent_coordinator.state_manager.set_state.call_count >= successful_coordinations


if __name__ == "__main__":
    pytest.main([__file__, "-v"])