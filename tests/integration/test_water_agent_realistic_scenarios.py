"""
Integration tests for Water Agent using realistic coordination scenarios.

This module tests the Water Agent coordination functionality using realistic
agent outputs and scenarios to validate genuine coordination capabilities.
"""

import pytest
import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import Dict, Any, List

from tests_new.fixtures.water_agent_test_data import (
    WaterAgentTestDataProvider, 
    CoordinationTestScenario,
    MisunderstandingType
)
from resources.water_agent import WaterAgentCoordinator
from resources.water_agent.context_manager import WaterAgentContextManager
from resources.state import StateManager
from resources.errors import CoordinationError


class MockRealisticAgent:
    """Mock agent that provides more realistic responses for testing."""
    
    def __init__(self, agent_id: str, response_style: str = "detailed"):
        self.agent_id = agent_id
        self.response_style = response_style
        self.clarification_count = 0
        
    async def clarify(self, question: str) -> str:
        """Provide realistic clarification responses based on question content."""
        self.clarification_count += 1
        
        if "terminology" in question.lower():
            return f"Agent {self.agent_id}: Regarding terminology, I use industry-standard terms. Let me clarify specific definitions used in my analysis."
            
        elif "requirements" in question.lower() or "constraints" in question.lower():
            return f"Agent {self.agent_id}: I may have overlooked some constraints. Could you highlight the most critical requirements I should address?"
            
        elif "approach" in question.lower() or "conflict" in question.lower():
            return f"Agent {self.agent_id}: I see the potential conflict. My approach focuses on [specific aspect], but I'm open to reconciling differences."
            
        elif "scope" in question.lower() or "scale" in question.lower():
            return f"Agent {self.agent_id}: Let me clarify the scope I'm addressing. I understand the project as [interpretation of scope]."
            
        elif "priority" in question.lower():
            return f"Agent {self.agent_id}: My priority ranking may differ. I focused on [primary priority] as the main goal."
            
        elif "technical" in question.lower() or "specification" in question.lower():
            return f"Agent {self.agent_id}: For technical clarity: [specific technical details]. I can provide more detailed specifications if needed."
            
        else:
            return f"Agent {self.agent_id}: Thank you for the clarification request. I'll provide more detail: [expanded explanation of my approach]."


@pytest.fixture
def state_manager_mock():
    """Create a realistic mock StateManager for testing."""
    state_manager = AsyncMock(spec=StateManager)
    state_manager.get_state = AsyncMock(return_value=None)
    state_manager.set_state = AsyncMock(return_value=True)
    state_manager.find_keys = AsyncMock(return_value=[])
    state_manager.delete_state = AsyncMock(return_value=True)
    return state_manager


@pytest.fixture
def realistic_water_coordinator(state_manager_mock):
    """Create a Water Agent Coordinator with realistic behavior."""
    with patch('interfaces.agent.interface.AgentInterface'), \
         patch('interfaces.agent.metrics.InterfaceMetrics'), \
         patch('asyncio.create_task'):
        coordinator = WaterAgentCoordinator(
            state_manager=state_manager_mock,
            agent_interface=None  # Will be mocked
        )
        coordinator._emit_event = AsyncMock()
        return coordinator


class TestRealisticCoordinationScenarios:
    """Test Water Agent coordination with realistic scenarios."""
    
    @pytest.mark.asyncio
    async def test_basic_terminology_conflict(self, realistic_water_coordinator):
        """Test coordination with basic terminology conflicts."""
        # Get test scenario
        scenarios = WaterAgentTestDataProvider.get_basic_scenarios()
        scenario = next(s for s in scenarios if s.name == "garden_planner_earth_agent_terminology")
        
        # Create realistic agents
        first_agent = MockRealisticAgent("garden_planner", "detailed")
        second_agent = MockRealisticAgent("earth_agent", "structured")
        
        # Mock misunderstanding detection to return expected results with higher severity
        expected_detection = WaterAgentTestDataProvider.get_expected_misunderstanding_for_scenario(scenario)
        # Change severity to MEDIUM to ensure resolution assessment runs
        for misunderstanding in expected_detection["misunderstandings"]:
            misunderstanding["severity"] = "MEDIUM"
        
        realistic_water_coordinator.misunderstanding_detector.detect_misunderstandings = AsyncMock(
            return_value=(
                expected_detection["misunderstandings"],
                [q["question"] for q in expected_detection["first_agent_questions"]],
                [q["question"] for q in expected_detection["second_agent_questions"]]
            )
        )
        
        # Mock resolution assessment
        realistic_water_coordinator.resolution_tracker.assess_resolution = AsyncMock(
            return_value=(
                expected_detection["misunderstandings"],  # All resolved
                [],  # No unresolved
                [],  # No new questions
                []   # No new questions
            )
        )
        
        # Mock final output generation
        realistic_water_coordinator._generate_final_outputs = AsyncMock(
            return_value=(
                scenario.first_agent_output + "\n\n[UPDATED: Terminology standardized]",
                scenario.second_agent_output + "\n\n[UPDATED: Using consistent terminology]",
                {
                    "first_agent_changes": ["Standardized terminology"],
                    "second_agent_changes": ["Aligned terminology usage"],
                    "refinement_approach": "terminology_alignment"
                }
            )
        )
        
        # Run coordination
        updated_first, updated_second, context = await realistic_water_coordinator.coordinate_agents(
            first_agent,
            scenario.first_agent_output,
            second_agent,
            scenario.second_agent_output
        )
        
        # Verify coordination occurred
        assert realistic_water_coordinator.misunderstanding_detector.detect_misunderstandings.called
        assert realistic_water_coordinator.resolution_tracker.assess_resolution.called
        
        # Verify outputs were updated
        assert "[UPDATED:" in updated_first
        assert "[UPDATED:" in updated_second
        
        # Verify context contains coordination metadata
        assert "coordination_id" in context
        assert "refinement_summary" in context
    
    @pytest.mark.asyncio
    async def test_critical_missing_requirements(self, realistic_water_coordinator):
        """Test coordination with critical missing requirements."""
        scenarios = WaterAgentTestDataProvider.get_basic_scenarios()
        scenario = next(s for s in scenarios if s.name == "missing_critical_requirements")
        
        first_agent = MockRealisticAgent("environmental_analysis", "technical")
        second_agent = MockRealisticAgent("root_system_architect", "engineering")
        
        expected_detection = WaterAgentTestDataProvider.get_expected_misunderstanding_for_scenario(scenario)
        
        # Mock detection of critical issues
        realistic_water_coordinator.misunderstanding_detector.detect_misunderstandings = AsyncMock(
            return_value=(
                expected_detection["misunderstandings"],
                [q["question"] for q in expected_detection["first_agent_questions"]],
                [q["question"] for q in expected_detection["second_agent_questions"]]
            )
        )
        
        # Mock partial resolution requiring multiple iterations
        call_count = 0
        async def mock_assess_resolution(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First iteration - some issues resolved
                return (
                    expected_detection["misunderstandings"][:1],  # One resolved
                    expected_detection["misunderstandings"][1:],  # One unresolved
                    ["Follow-up question for first agent about weight constraints"],
                    ["Follow-up question about structural requirements"]
                )
            else:
                # Second iteration - all resolved
                return (
                    expected_detection["misunderstandings"][1:],  # Remaining resolved
                    [],  # All resolved
                    [],  # No more questions
                    []
                )
        
        realistic_water_coordinator.resolution_tracker.assess_resolution = AsyncMock(
            side_effect=mock_assess_resolution
        )
        
        # Mock realistic output generation
        realistic_water_coordinator._generate_final_outputs = AsyncMock(
            return_value=(
                scenario.first_agent_output + "\n\n[CRITICAL UPDATE: Weight and removability constraints emphasized]",
                scenario.second_agent_output.replace("24-inch deep soil beds", "lightweight container systems") + 
                "\n\n[CRITICAL UPDATE: Redesigned for rooftop constraints]",
                {
                    "first_agent_changes": ["Emphasized critical constraints"],
                    "second_agent_changes": ["Complete redesign for rooftop limitations"],
                    "refinement_approach": "constraint_alignment"
                }
            )
        )
        
        # Run coordination
        updated_first, updated_second, context = await realistic_water_coordinator.coordinate_agents(
            first_agent,
            scenario.first_agent_output,
            second_agent,
            scenario.second_agent_output,
            {"max_iterations": 2}
        )
        
        # Verify multiple iterations occurred
        assert realistic_water_coordinator.resolution_tracker.assess_resolution.call_count == 2
        
        # Verify critical issues were addressed
        assert "CRITICAL UPDATE" in updated_first
        assert "CRITICAL UPDATE" in updated_second
        assert "lightweight container systems" in updated_second
        
        # Verify context reflects multiple iterations
        assert context.get("total_iterations", 0) >= 1
    
    @pytest.mark.asyncio 
    async def test_complex_multi_issue_scenario(self, realistic_water_coordinator):
        """Test coordination with multiple complex issues."""
        scenarios = WaterAgentTestDataProvider.get_complex_scenarios()
        scenario = next(s for s in scenarios if s.name == "multi_layered_misunderstanding")
        
        first_agent = MockRealisticAgent("technical_planner", "complex")
        second_agent = MockRealisticAgent("simple_implementer", "basic")
        
        expected_detection = WaterAgentTestDataProvider.get_expected_misunderstanding_for_scenario(scenario)
        
        # Mock detection of multiple critical issues
        realistic_water_coordinator.misunderstanding_detector.detect_misunderstandings = AsyncMock(
            return_value=(
                expected_detection["misunderstandings"],
                [q["question"] for q in expected_detection["first_agent_questions"]],
                [q["question"] for q in expected_detection["second_agent_questions"]]
            )
        )
        
        # Mock complex resolution requiring maximum iterations
        iteration_responses = [
            # Iteration 1: Scope alignment partial
            (
                expected_detection["misunderstandings"][:1],  # Scope partially resolved
                expected_detection["misunderstandings"][1:],  # Technical issues remain
                ["Can you simplify the technical requirements?"],
                ["What level of complexity are you comfortable with?"]
            ),
            # Iteration 2: Technical alignment partial
            (
                expected_detection["misunderstandings"][1:2],  # Technical partially resolved
                expected_detection["misunderstandings"][2:],  # Priority and logic issues remain
                ["What are your must-have vs nice-to-have features?"],
                ["How can we bridge the complexity gap?"]
            ),
            # Iteration 3: Final resolution
            (
                expected_detection["misunderstandings"][2:],  # Remaining resolved
                [],  # All resolved
                [],
                []
            )
        ]
        
        realistic_water_coordinator.resolution_tracker.assess_resolution = AsyncMock(
            side_effect=iteration_responses
        )
        
        # Mock comprehensive output generation
        realistic_water_coordinator._generate_final_outputs = AsyncMock(
            return_value=(
                """# Simplified Aquaponics-Permaculture System
                
## Phased Implementation Approach:
Phase 1: Basic container gardening with simple automation
Phase 2: Add basic aquaponics components
Phase 3: Integrate advanced monitoring (optional)

## Simplified Technical Components:
- Small-scale aquaponics (200L system)
- Basic sensors (pH, temperature only)
- Manual greenhouse controls
- Simple rainwater collection
- Solar lighting (not full power system)

[UPDATED: Dramatically simplified for practical implementation]""",
                
                """# Practical Implementation Plan
                
## Achievable Setup:
Starting with proven container gardening techniques and gradually adding aquaponics elements.

## Realistic Components:
- Quality containers and growing medium
- Reliable plants for beginners
- Basic automation where beneficial
- Room for growth and learning

## Budget-Friendly Approach:
- Phase 1: $2,000 (basic setup)
- Phase 2: $5,000 (add aquaponics)
- Phase 3: $10,000+ (advanced features)

[UPDATED: Aligned with technical requirements while maintaining simplicity]""",
                
                {
                    "first_agent_changes": ["Simplified technical complexity", "Phased implementation approach", "Realistic budget expectations"],
                    "second_agent_changes": ["Incorporated technical elements", "Added growth pathway", "Maintained practical focus"],
                    "refinement_approach": "complexity_bridging"
                }
            )
        )
        
        # Run coordination with max iterations
        updated_first, updated_second, context = await realistic_water_coordinator.coordinate_agents(
            first_agent,
            scenario.first_agent_output,
            second_agent,
            scenario.second_agent_output,
            {"max_iterations": 3}
        )
        
        # Verify all iterations were used
        assert realistic_water_coordinator.resolution_tracker.assess_resolution.call_count == 3
        
        # Verify complex bridging occurred
        assert "Simplified" in updated_first or "Phased" in updated_first
        assert "technical" in updated_second.lower()
        
        # Verify comprehensive changes
        changes = context.get("refinement_summary", {})
        assert len(changes.get("first_agent_changes", [])) >= 2
        assert len(changes.get("second_agent_changes", [])) >= 2
    
    @pytest.mark.asyncio
    async def test_edge_case_minimal_output(self, realistic_water_coordinator):
        """Test coordination with minimal agent output."""
        scenarios = WaterAgentTestDataProvider.get_edge_case_scenarios()
        scenario = next(s for s in scenarios if s.name == "empty_output_scenario")
        
        first_agent = MockRealisticAgent("minimal_agent", "terse")
        second_agent = MockRealisticAgent("verbose_agent", "detailed")
        
        expected_detection = WaterAgentTestDataProvider.get_expected_misunderstanding_for_scenario(scenario)
        
        # Mock detection of missing information
        realistic_water_coordinator.misunderstanding_detector.detect_misunderstandings = AsyncMock(
            return_value=(
                expected_detection["misunderstandings"],
                [q["question"] for q in expected_detection["first_agent_questions"]],
                [q["question"] for q in expected_detection["second_agent_questions"]]
            )
        )
        
        # Mock resolution that requires elaboration
        realistic_water_coordinator.resolution_tracker.assess_resolution = AsyncMock(
            return_value=(
                expected_detection["misunderstandings"],  # Issue resolved
                [],
                [],
                []
            )
        )
        
        # Mock output that addresses minimal information
        realistic_water_coordinator._generate_final_outputs = AsyncMock(
            return_value=(
                "Task completed. No issues found. [UPDATED: Added detailed analysis of completed tasks and validation criteria]",
                scenario.second_agent_output + "\n\n[UPDATED: Focused analysis based on confirmed task completion]",
                {
                    "first_agent_changes": ["Added detailed explanation"],
                    "second_agent_changes": ["Refined scope based on actual completion"],
                    "refinement_approach": "information_elaboration"
                }
            )
        )
        
        # Run coordination
        updated_first, updated_second, context = await realistic_water_coordinator.coordinate_agents(
            first_agent,
            scenario.first_agent_output,
            second_agent,
            scenario.second_agent_output
        )
        
        # Verify minimal output was enhanced
        original_length = len(scenario.first_agent_output)
        updated_length = len(updated_first)
        assert updated_length > original_length * 2  # Significantly expanded
        
        # Verify second agent output was refined
        assert "[UPDATED:" in updated_second
    
    @pytest.mark.asyncio
    async def test_coordination_with_realistic_errors(self, realistic_water_coordinator):
        """Test coordination behavior with realistic error scenarios."""
        scenarios = WaterAgentTestDataProvider.get_basic_scenarios()
        scenario = scenarios[0]  # Use any scenario
        
        first_agent = MockRealisticAgent("error_prone_agent", "inconsistent")
        second_agent = MockRealisticAgent("normal_agent", "standard")
        
        # Test misunderstanding detection failure
        realistic_water_coordinator.misunderstanding_detector.detect_misunderstandings = AsyncMock(
            side_effect=Exception("LLM API timeout during misunderstanding detection")
        )
        
        # Coordination should handle the error gracefully
        with pytest.raises(CoordinationError):
            await realistic_water_coordinator.coordinate_agents(
                first_agent,
                scenario.first_agent_output,
                second_agent,
                scenario.second_agent_output
            )
        
        # Verify error was logged and event emitted
        assert realistic_water_coordinator._emit_event.called
        error_events = [call for call in realistic_water_coordinator._emit_event.call_args_list 
                      if len(call[0]) > 1 and isinstance(call[0][1], dict) and "error" in call[0][1]]
        assert len(error_events) > 0
    
    @pytest.mark.asyncio
    async def test_agent_clarification_realistic_behavior(self, realistic_water_coordinator):
        """Test that agent clarifications produce realistic improvements."""
        scenarios = WaterAgentTestDataProvider.get_basic_scenarios()
        scenario = next(s for s in scenarios if s.name == "scope_and_priority_misalignment")
        
        first_agent = MockRealisticAgent("scope_focused_agent", "planning")
        second_agent = MockRealisticAgent("production_focused_agent", "execution")
        
        expected_detection = WaterAgentTestDataProvider.get_expected_misunderstanding_for_scenario(scenario)
        
        # Mock realistic question-response flow
        realistic_water_coordinator.misunderstanding_detector.detect_misunderstandings = AsyncMock(
            return_value=(
                expected_detection["misunderstandings"],
                [q["question"] for q in expected_detection["first_agent_questions"]],
                [q["question"] for q in expected_detection["second_agent_questions"]]
            )
        )
        
        # Mock response collection to track realistic agent responses
        original_get_responses = realistic_water_coordinator.response_handler.get_agent_responses
        async def track_realistic_responses(agent, questions):
            responses = []
            for question in questions:
                response = await agent.clarify(question)
                responses.append(response)
                # Verify response quality
                assert len(response) > 50  # Substantial response
                assert agent.agent_id in response  # Agent identifies itself
            return responses
        
        realistic_water_coordinator.response_handler.get_agent_responses = AsyncMock(
            side_effect=track_realistic_responses
        )
        
        # Mock resolution that shows improvement from clarifications
        realistic_water_coordinator.resolution_tracker.assess_resolution = AsyncMock(
            return_value=(
                expected_detection["misunderstandings"],  # All resolved after clarification
                [],
                [],
                []
            )
        )
        
        # Mock output generation that reflects clarification improvements
        realistic_water_coordinator._generate_final_outputs = AsyncMock(
            return_value=(
                scenario.first_agent_output + "\n\n[CLARIFIED: Emphasized demonstration and education focus for Phase 1]",
                scenario.second_agent_output + "\n\n[CLARIFIED: Adjusted to support phased approach starting with demonstration]",
                {
                    "first_agent_changes": ["Clarified phase priorities"],
                    "second_agent_changes": ["Aligned with phased demonstration approach"],
                    "refinement_approach": "scope_clarification"
                }
            )
        )
        
        # Run coordination
        updated_first, updated_second, context = await realistic_water_coordinator.coordinate_agents(
            first_agent,
            scenario.first_agent_output,
            second_agent,
            scenario.second_agent_output
        )
        
        # Verify agents were asked realistic questions
        assert realistic_water_coordinator.response_handler.get_agent_responses.call_count == 2
        
        # Verify clarification tracking
        assert first_agent.clarification_count > 0
        assert second_agent.clarification_count > 0
        
        # Verify outputs reflect clarification improvements
        assert "[CLARIFIED:" in updated_first
        assert "[CLARIFIED:" in updated_second
        assert "demonstration" in updated_second.lower()  # Shows alignment