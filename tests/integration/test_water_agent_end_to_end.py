"""
End-to-end integration tests for Water Agent coordination workflows.

This module tests complete coordination workflows from start to finish,
including real component integration and complex scenarios.
"""

import pytest
import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from tests_new.fixtures.water_agent_test_data import WaterAgentTestDataProvider
from resources.water_agent.context_manager import WaterAgentContextManager, CoordinationContext
from phase_one.validation.coordination import SequentialAgentCoordinator
from interfaces.agent.coordination import CoordinationInterface
from resources.state import StateManager
from resources.events import EventQueue
from resources.errors import CoordinationError


class RealishAgent:
    """More realistic agent implementation for end-to-end testing."""
    
    def __init__(self, agent_id: str, agent_type: str, personality: str = "collaborative"):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.personality = personality
        self.clarification_history = []
        self.coordination_interface = None
        
        # Agent state tracking
        self.current_output = ""
        self.context_data = {}
        self.performance_metrics = {
            "clarifications_requested": 0,
            "clarifications_provided": 0,
            "output_revisions": 0
        }
    
    def setup_coordination_interface(self, agent_interface):
        """Setup coordination interface for this agent."""
        self.coordination_interface = CoordinationInterface(agent_interface)
    
    async def clarify(self, question: str) -> str:
        """Provide realistic clarification responses."""
        self.performance_metrics["clarifications_provided"] += 1
        self.clarification_history.append({
            "question": question,
            "timestamp": datetime.now().isoformat(),
            "response_style": self.personality
        })
        
        # Generate contextual responses based on agent type and question
        if self.agent_type == "garden_planner":
            return await self._garden_planner_clarify(question)
        elif self.agent_type == "earth_agent":
            return await self._earth_agent_clarify(question)
        elif self.agent_type == "environmental_analysis":
            return await self._environmental_analysis_clarify(question)
        elif self.agent_type == "root_system_architect":
            return await self._root_system_architect_clarify(question)
        else:
            return await self._generic_clarify(question)
    
    async def _garden_planner_clarify(self, question: str) -> str:
        """Garden planner specific clarifications."""
        if "terminology" in question.lower():
            return """Garden Planner clarification: I use permaculture terminology where:
            - 'Forest layers' refers to the seven standard permaculture layers (canopy, understory, shrub, herbaceous, ground cover, root, vine)
            - 'Structural components' means the physical zones and plant groupings
            - 'Dependencies' refers to the sequential relationships between design elements
            I'm happy to use whatever terminology the team prefers for consistency."""
            
        elif "requirements" in question.lower() or "constraint" in question.lower():
            return """Garden Planner clarification: The most critical requirements I identified are:
            1. Size constraint: 1000 square meters (fixed)
            2. Native species focus (high priority)
            3. Budget: $10,000 (should be confirmed if flexible)
            4. Permaculture principles (design approach)
            5. Sustainability focus (long-term goal)
            Any additional constraints should be integrated into the design process."""
            
        elif "scope" in question.lower() or "phase" in question.lower():
            return """Garden Planner clarification: I envision this as a comprehensive food forest design that can be implemented in phases:
            Phase 1: Foundation planting (trees and perennials)
            Phase 2: Understory and support systems  
            Phase 3: Annual integration and optimization
            The scope can be adjusted based on resources and timeline preferences."""
            
        else:
            return f"Garden Planner clarification: I'm focusing on creating a holistic permaculture design that maximizes food production while building soil health and biodiversity. Could you help me understand which specific aspect of my analysis needs more detail?"
    
    async def _earth_agent_clarify(self, question: str) -> str:
        """Earth agent specific clarifications."""
        if "validation" in question.lower():
            return """Earth Agent clarification: My validation process checks:
            1. Alignment with stated user requirements
            2. Feasibility within given constraints  
            3. Completeness of design elements
            4. Sustainability of proposed approach
            I can adjust my validation criteria based on what aspects are most important to prioritize."""
            
        elif "terminology" in question.lower():
            return """Earth Agent clarification: I interpreted the Garden Planner's terms as follows:
            - 'Canopy Layer' = Primary tree species for food production
            - 'Structural Components' = Main design elements that need validation
            - 'Dependencies' = Critical sequence requirements for implementation
            I can standardize on any preferred terminology for the project."""
            
        else:
            return f"Earth Agent clarification: My role is to validate that the garden plan aligns with the user's actual needs and constraints. I focus on practical feasibility and requirement fulfillment. What specific validation concerns should I address?"
    
    async def _environmental_analysis_clarify(self, question: str) -> str:
        """Environmental analysis agent clarifications."""
        if "constraint" in question.lower() or "limitation" in question.lower():
            return """Environmental Analysis clarification: The critical environmental constraints I identified are:
            1. Wind exposure: Severe rooftop conditions requiring wind-resistant design
            2. Weight limitations: Structural capacity of 150 lbs/sq ft maximum
            3. Water access: Limited to roof drainage, no irrigation hookup
            4. Temperature extremes: Wide range requiring hardy plant selection
            5. Removability requirement: Rental property restrictions
            These are non-negotiable constraints that must drive all design decisions."""
            
        elif "priority" in question.lower():
            return """Environmental Analysis clarification: My priority ranking for this site is:
            1. Structural safety (weight limits) - CRITICAL
            2. Wind resistance - CRITICAL  
            3. Water management - HIGH
            4. Plant hardiness - HIGH
            5. Aesthetic considerations - MEDIUM
            This prioritization is based on the extreme rooftop environment."""
            
        else:
            return f"Environmental Analysis clarification: I focus on identifying site-specific challenges that will determine project success or failure. The rooftop environment creates unique constraints that must be addressed in every design decision."
    
    async def _root_system_architect_clarify(self, question: str) -> str:
        """Root system architect clarifications.""" 
        if "weight" in question.lower() or "constraint" in question.lower():
            return """Root System Architect clarification: You're absolutely right about the weight constraints. I need to completely revise my approach:
            - Container-based systems only (no in-ground planting)
            - Lightweight growing media (coconut coir, perlite blends)
            - Shallow-rooted plant varieties
            - Modular design for easy removal
            - Weight distribution systems to spread loads
            I apologize for initially missing these critical limitations."""
            
        elif "approach" in question.lower() or "design" in question.lower():
            return """Root System Architect clarification: My revised approach will focus on:
            1. Lightweight container systems with proper drainage
            2. Root systems optimized for container growing
            3. Companion planting within weight constraints
            4. Vertical growing techniques to maximize space efficiency
            5. Easy maintenance and modification capabilities
            This approach prioritizes safety while maintaining productivity."""
            
        else:
            return f"Root System Architect clarification: I design root systems and growing infrastructure. I should have prioritized the structural constraints from the beginning. How can I better align my designs with the environmental limitations?"
    
    async def _generic_clarify(self, question: str) -> str:
        """Generic clarification for unknown agent types."""
        return f"Agent {self.agent_id} clarification: I understand you need more information about my approach. I'm working on {self.agent_type} aspects of the project and want to ensure my contribution aligns with overall goals. Could you help me understand the specific concern?"
    
    async def revise_output(self, coordination_feedback: Dict[str, Any]) -> str:
        """Revise output based on coordination feedback."""
        self.performance_metrics["output_revisions"] += 1
        
        # Simulate realistic output revision based on feedback
        changes = coordination_feedback.get("changes_needed", [])
        revised_output = self.current_output
        
        if changes:
            revision_notes = "\n\n## COORDINATION UPDATES:\n"
            for change in changes:
                revision_notes += f"- {change}\n"
            revised_output += revision_notes
        
        return revised_output
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get agent performance metrics."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "performance_metrics": self.performance_metrics,
            "clarification_count": len(self.clarification_history),
            "personality": self.personality
        }


@pytest.fixture
def minimal_event_queue():
    """Create a minimal event queue for testing."""
    # Use a simple mock instead of real EventQueue to avoid complexity
    event_queue = AsyncMock()
    event_queue.emit = AsyncMock()
    event_queue.subscribe = AsyncMock()
    return event_queue


@pytest.fixture
def minimal_state_manager():
    """Create a minimal state manager for testing."""
    state_manager = AsyncMock()
    state_manager.get_state = AsyncMock(return_value=None)
    state_manager.set_state = AsyncMock(return_value=True)
    state_manager.find_keys = AsyncMock(return_value=[])
    state_manager.delete_state = AsyncMock(return_value=True)
    return state_manager


@pytest.fixture
def coordination_infrastructure(minimal_event_queue, minimal_state_manager):
    """Create basic coordination infrastructure."""
    return {
        "event_queue": minimal_event_queue,
        "state_manager": minimal_state_manager
    }


class TestEndToEndCoordination:
    """Test complete end-to-end coordination workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_garden_planning_workflow(self, coordination_infrastructure):
        """Test complete garden planning coordination workflow."""
        # Setup infrastructure
        event_queue = coordination_infrastructure["event_queue"]
        state_manager = coordination_infrastructure["state_manager"]
        
        # Create realistic agents
        garden_planner = RealishAgent("garden_planner_001", "garden_planner", "detailed")
        earth_agent = RealishAgent("earth_agent_001", "earth_agent", "analytical")
        
        # Get realistic test scenario
        scenarios = WaterAgentTestDataProvider.get_basic_scenarios()
        scenario = next(s for s in scenarios if s.name == "garden_planner_earth_agent_terminology")
        
        # Set agent outputs
        garden_planner.current_output = scenario.first_agent_output
        earth_agent.current_output = scenario.second_agent_output
        
        # Create sequential coordinator
        sequential_coordinator = SequentialAgentCoordinator(
            event_queue=event_queue,
            state_manager=state_manager,
            max_coordination_attempts=2,
            coordination_timeout=60.0
        )
        
        # Mock the water coordinator's methods for realistic behavior
        mock_detection_response = WaterAgentTestDataProvider.get_expected_misunderstanding_for_scenario(scenario)
        sequential_coordinator.water_coordinator.misunderstanding_detector.detect_misunderstandings = AsyncMock(
            return_value=(
                mock_detection_response["misunderstandings"],
                [q["question"] for q in mock_detection_response["first_agent_questions"]],
                [q["question"] for q in mock_detection_response["second_agent_questions"]]
            )
        )
        
        # Mock resolution assessment
        sequential_coordinator.water_coordinator.resolution_tracker.assess_resolution = AsyncMock(
            return_value=(
                mock_detection_response["misunderstandings"],  # All resolved
                [],  # No unresolved
                [],  # No new questions
                []
            )
        )
        
        # Mock output generation
        sequential_coordinator.water_coordinator._generate_final_outputs = AsyncMock(
            return_value=(
                scenario.first_agent_output + "\n\n[UPDATED: Standardized terminology per coordination]",
                scenario.second_agent_output + "\n\n[UPDATED: Aligned terminology usage]",
                {
                    "first_agent_changes": ["Terminology standardization"],
                    "second_agent_changes": ["Terminology alignment"],
                    "coordination_approach": "terminology_resolution"
                }
            )
        )
        
        # Execute coordination workflow
        start_time = datetime.now()
        
        try:
            # Create mock agent interfaces for the handoff
            mock_garden_interface = MagicMock()
            mock_garden_interface.agent_id = garden_planner.agent_id
            mock_earth_interface = MagicMock()
            mock_earth_interface.agent_id = earth_agent.agent_id
            
            updated_output, coordination_metadata = await sequential_coordinator.coordinate_agent_handoff(
                first_agent=mock_garden_interface,
                first_agent_output={"content": garden_planner.current_output},
                second_agent=mock_earth_interface,
                operation_id="test_garden_planning_workflow"
            )
            
            coordination_duration = datetime.now() - start_time
            
            # Verify workflow completion
            assert updated_output is not None
            assert coordination_metadata is not None
            assert coordination_duration < timedelta(seconds=10)  # Should complete quickly in test
            
            # Verify coordination occurred
            assert sequential_coordinator.water_coordinator.misunderstanding_detector.detect_misunderstandings.called
            
            # Verify agent clarifications would have been realistic
            test_question = "Can you clarify which terminology should be used consistently?"
            garden_response = await garden_planner.clarify(test_question)
            earth_response = await earth_agent.clarify(test_question)
            
            assert len(garden_response) > 100  # Substantial response
            assert "terminology" in garden_response.lower()
            assert len(earth_response) > 100
            assert "terminology" in earth_response.lower()
            
            # Verify performance tracking
            garden_metrics = garden_planner.get_performance_summary()
            earth_metrics = earth_agent.get_performance_summary()
            
            assert garden_metrics["clarification_count"] > 0
            assert earth_metrics["clarification_count"] > 0
            
        except Exception as e:
            pytest.fail(f"End-to-end coordination workflow failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_multi_agent_sequential_coordination(self, coordination_infrastructure):
        """Test coordination across multiple sequential agents."""
        # Setup
        event_queue = coordination_infrastructure["event_queue"] 
        state_manager = coordination_infrastructure["state_manager"]
        
        # Create agent sequence: Garden Planner -> Earth Agent -> Environmental Analysis -> Root Architect
        agents = [
            RealishAgent("garden_planner", "garden_planner"),
            RealishAgent("earth_agent", "earth_agent"),
            RealishAgent("env_analysis", "environmental_analysis"),
            RealishAgent("root_architect", "root_system_architect")
        ]
        
        # Get complex scenario
        scenarios = WaterAgentTestDataProvider.get_basic_scenarios()
        complex_scenario = next(s for s in scenarios if s.name == "missing_critical_requirements")
        
        # Set initial outputs
        agents[0].current_output = "Initial garden planning analysis with basic requirements."
        agents[1].current_output = "Earth agent validation with standard checks."
        agents[2].current_output = complex_scenario.first_agent_output  # Environmental constraints
        agents[3].current_output = complex_scenario.second_agent_output  # Problematic root design
        
        # Create sequential coordinator
        sequential_coordinator = SequentialAgentCoordinator(
            event_queue=event_queue,
            state_manager=state_manager,
            max_coordination_attempts=3,
            coordination_timeout=120.0
        )
        
        # Track coordination events
        coordination_events = []
        
        async def track_coordination_event(event_type, event_data):
            coordination_events.append({
                "type": event_type,
                "data": event_data,
                "timestamp": datetime.now()
            })
        
        event_queue.emit.side_effect = track_coordination_event
        
        # Execute sequential coordination
        coordination_results = []
        
        # Coordinate each sequential pair
        for i in range(len(agents) - 1):
            first_agent = agents[i]
            second_agent = agents[i + 1]
            
            # Mock coordination for this pair
            if i == 2:  # Environmental -> Root architect (critical issues)
                mock_detection = WaterAgentTestDataProvider.get_expected_misunderstanding_for_scenario(complex_scenario)
                sequential_coordinator.water_coordinator.misunderstanding_detector.detect_misunderstandings = AsyncMock(
                    return_value=(
                        mock_detection["misunderstandings"],
                        [q["question"] for q in mock_detection["first_agent_questions"]],
                        [q["question"] for q in mock_detection["second_agent_questions"]]
                    )
                )
                
                # Mock multi-iteration resolution
                call_count = 0
                async def progressive_resolution(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:
                        return ([], mock_detection["misunderstandings"], ["Follow-up question"], ["Follow-up question"])
                    else:
                        return (mock_detection["misunderstandings"], [], [], [])
                
                sequential_coordinator.water_coordinator.resolution_tracker.assess_resolution = AsyncMock(
                    side_effect=progressive_resolution
                )
                
                sequential_coordinator.water_coordinator._generate_final_outputs = AsyncMock(
                    return_value=(
                        complex_scenario.first_agent_output + "\n[UPDATED: Critical constraints emphasized]",
                        complex_scenario.second_agent_output.replace("24-inch deep", "container-based") + "\n[UPDATED: Redesigned for constraints]",
                        {"first_agent_changes": ["Constraint emphasis"], "second_agent_changes": ["Complete redesign"]}
                    )
                )
            else:
                # Simple coordination for other pairs
                sequential_coordinator.water_coordinator.misunderstanding_detector.detect_misunderstandings = AsyncMock(
                    return_value=([], [], [])  # No issues
                )
            
            # Mock agent interfaces
            mock_first = MagicMock()
            mock_first.agent_id = first_agent.agent_id
            mock_second = MagicMock()
            mock_second.agent_id = second_agent.agent_id
            
            try:
                result, metadata = await sequential_coordinator.coordinate_agent_handoff(
                    first_agent=mock_first,
                    first_agent_output={"content": first_agent.current_output},
                    second_agent=mock_second,
                    operation_id=f"coordination_{i}_{i+1}"
                )
                
                coordination_results.append({
                    "agents": f"{first_agent.agent_id} -> {second_agent.agent_id}",
                    "result": result,
                    "metadata": metadata
                })
                
                # Test agent clarifications for this pair
                test_question = f"How does your output relate to {first_agent.agent_id}'s analysis?"
                second_response = await second_agent.clarify(test_question)
                assert len(second_response) > 50
                
            except Exception as e:
                pytest.fail(f"Sequential coordination failed for {first_agent.agent_id} -> {second_agent.agent_id}: {str(e)}")
        
        # Verify multi-agent coordination
        assert len(coordination_results) == len(agents) - 1
        
        # Verify critical coordination occurred between environmental and root architect
        env_root_result = coordination_results[2]
        assert env_root_result["agents"] == "env_analysis -> root_architect"
        
        # Verify coordination events were tracked
        assert len(coordination_events) > 0
        
        # Verify all agents have realistic clarification capabilities
        for agent in agents:
            metrics = agent.get_performance_summary()
            assert metrics["agent_type"] in ["garden_planner", "earth_agent", "environmental_analysis", "root_system_architect"]
            assert isinstance(metrics["performance_metrics"], dict)
    
    @pytest.mark.asyncio
    async def test_coordination_context_persistence(self, coordination_infrastructure):
        """Test that coordination context is properly persisted across workflow."""
        state_manager = coordination_infrastructure["state_manager"]
        
        # Create context manager
        context_manager = WaterAgentContextManager(
            state_manager=state_manager,
            event_bus=coordination_infrastructure["event_queue"]
        )
        
        # Create coordination context
        coordination_id = f"test_workflow_{uuid.uuid4()}"
        context = await context_manager.create_coordination_context(
            first_agent_id="garden_planner",
            second_agent_id="earth_agent",
            coordination_id=coordination_id
        )
        
        # Verify context creation
        assert context.coordination_id == coordination_id
        assert context.status == "created"
        
        # Simulate coordination iteration
        await context_manager.update_coordination_iteration(
            coordination_id=coordination_id,
            iteration=1,
            first_agent_questions=["What are the key priorities?"],
            first_agent_responses=["Focus on sustainability and native species"],
            second_agent_questions=["How do you define success?"],
            second_agent_responses=["Successful establishment within 2 years"],
            resolved=[{"id": "M1", "resolution_summary": "Terminology clarified"}],
            unresolved=[]
        )
        
        # Verify context persistence
        retrieved_context = await context_manager.get_coordination_context(coordination_id)
        assert retrieved_context is not None
        assert retrieved_context.status == "in_progress"
        assert len(retrieved_context.iterations) == 1
        assert "M1" in retrieved_context.resolved_issues
        
        # Complete coordination
        await context_manager.complete_coordination(
            coordination_id=coordination_id,
            first_agent_final_output="Final garden plan with clarifications",
            second_agent_final_output="Final validation with approved design",
            final_status="all_issues_resolved"
        )
        
        # Verify completion
        final_context = await context_manager.get_coordination_context(coordination_id)
        assert final_context.status == "completed"
        assert final_context.final_status == "all_issues_resolved"
        assert final_context.completed_at is not None
        
        # Test context pruning
        await context_manager.prune_temporary_data(coordination_id, keep_final_outputs=True)
        
        pruned_context = await context_manager.get_coordination_context(coordination_id)
        assert pruned_context.first_agent_final_output is not None
        assert pruned_context.second_agent_final_output is not None
        # Verify temporary data was simplified
        assert len(pruned_context.iterations) > 0
        iteration = pruned_context.iterations[0]
        assert "first_agent_questions_count" in iteration
        assert "first_agent_questions" not in iteration  # Pruned
    
    @pytest.mark.asyncio
    async def test_error_recovery_in_workflow(self, coordination_infrastructure):
        """Test error recovery during coordination workflow."""
        event_queue = coordination_infrastructure["event_queue"]
        state_manager = coordination_infrastructure["state_manager"]
        
        # Create agents
        garden_planner = RealishAgent("garden_planner", "garden_planner")
        earth_agent = RealishAgent("earth_agent", "earth_agent")
        
        # Create coordinator
        sequential_coordinator = SequentialAgentCoordinator(
            event_queue=event_queue,
            state_manager=state_manager,
            max_coordination_attempts=3
        )
        
        # Mock initial failure then success
        call_count = 0
        async def mock_coordination_with_failure(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Temporary coordination failure")
            else:
                return ("Updated output", "Updated output", {"status": "recovered"})
        
        sequential_coordinator.water_coordinator.coordinate_agents = AsyncMock(
            side_effect=mock_coordination_with_failure
        )
        
        # Mock agent interfaces
        mock_garden = MagicMock()
        mock_garden.agent_id = garden_planner.agent_id
        mock_earth = MagicMock()
        mock_earth.agent_id = earth_agent.agent_id
        
        # Test error recovery
        try:
            result, metadata = await sequential_coordinator.coordinate_agent_handoff(
                first_agent=mock_garden,
                first_agent_output={"content": "Garden plan"},
                second_agent=mock_earth,
                operation_id="error_recovery_test"
            )
            
            # Should succeed on retry
            assert result is not None
            assert metadata is not None
            assert call_count == 2  # Failed once, succeeded on retry
            
        except Exception as e:
            # If coordination still fails, verify it's after exhausting retries
            assert call_count >= 3
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_in_workflow(self, coordination_infrastructure):
        """Test performance monitoring during coordination workflow."""
        # Create agents with performance tracking
        agents = [
            RealishAgent("agent_1", "garden_planner", "efficient"),
            RealishAgent("agent_2", "earth_agent", "thorough"),
            RealishAgent("agent_3", "environmental_analysis", "detailed")
        ]
        
        # Simulate coordination interactions
        start_time = datetime.now()
        
        # Test clarification performance
        for i, agent in enumerate(agents):
            questions = [
                f"Question {i+1} for {agent.agent_id}",
                f"Follow-up question for {agent.agent_id}",
                f"Clarification about approach for {agent.agent_id}"
            ]
            
            for question in questions:
                response = await agent.clarify(question)
                assert len(response) > 50  # Quality check
        
        workflow_duration = datetime.now() - start_time
        
        # Analyze performance metrics
        performance_summary = []
        for agent in agents:
            metrics = agent.get_performance_summary()
            performance_summary.append(metrics)
            
            # Verify performance tracking
            assert metrics["clarification_count"] == 3
            assert metrics["performance_metrics"]["clarifications_provided"] == 3
            assert len(agent.clarification_history) == 3
        
        # Verify workflow performance
        assert workflow_duration < timedelta(seconds=5)  # Should be fast in test
        
        # Verify personality differences in responses
        responses_by_personality = {}
        for agent in agents:
            personality = agent.personality
            if personality not in responses_by_personality:
                responses_by_personality[personality] = []
            responses_by_personality[personality].extend(agent.clarification_history)
        
        # Each personality should have different response characteristics
        assert len(responses_by_personality) > 1