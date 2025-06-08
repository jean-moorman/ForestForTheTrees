"""
Comprehensive test suite for Foundation Refinement Agent with real LLM calls.

This module tests the Foundation Refinement agent's core functionality with real API calls
to ensure proper phase one analysis and refinement decision-making.
"""

import asyncio
import json
import pytest
import pytest_asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from resources import (
    EventQueue, StateManager, AgentContextManager, CacheManager, 
    MetricsManager, ErrorHandler, MemoryMonitor, ResourceType
)
from resources.monitoring import HealthTracker
from phase_one.agents.foundation_refinement import FoundationRefinementAgent
from phase_one.models.enums import DevelopmentState

logger = logging.getLogger(__name__)

@pytest.mark.real_api
class TestFoundationRefinementRealLLM:
    """Test suite for Foundation Refinement Agent using real LLM API calls."""

    @pytest_asyncio.fixture
    async def real_resources(self):
        """Create real resource managers for testing."""
        event_queue = EventQueue()
        await event_queue.start()
        
        state_manager = StateManager(event_queue)
        await state_manager.initialize()
        
        context_manager = AgentContextManager(event_queue)
        await context_manager.initialize()
        
        cache_manager = CacheManager(event_queue)
        await cache_manager.initialize()
        
        metrics_manager = MetricsManager(event_queue)
        await metrics_manager.initialize()
        
        error_handler = ErrorHandler(event_queue)
        await error_handler.initialize()
        
        memory_monitor = MemoryMonitor(event_queue)
        health_tracker = HealthTracker(event_queue)

        yield {
            'event_queue': event_queue,
            'state_manager': state_manager,
            'context_manager': context_manager,
            'cache_manager': cache_manager,
            'metrics_manager': metrics_manager,
            'error_handler': error_handler,
            'memory_monitor': memory_monitor,
            'health_tracker': health_tracker
        }
        
        # Cleanup
        await event_queue.stop()

    @pytest_asyncio.fixture
    async def foundation_refinement_agent(self, real_resources):
        """Create a Foundation Refinement Agent instance with real resources."""
        agent = FoundationRefinementAgent(
            **real_resources,
            max_refinement_cycles=3
        )
        return agent

    @pytest.fixture
    def sample_phase_one_results(self):
        """Provide sample phase one results for testing."""
        return {
            "successful_result": {
                "status": "success",
                "operation_id": "test_operation_001",
                "structural_components": [
                    {
                        "sequence_number": 1,
                        "name": "UserAuthComponent",
                        "type": "foundation",
                        "purpose": "Handle user authentication and session management",
                        "dependencies": {"required": [], "optional": []},
                        "completion_criteria": ["Authentication flow implemented", "Session management working"]
                    },
                    {
                        "sequence_number": 2,
                        "name": "HabitManagementComponent", 
                        "type": "core",
                        "purpose": "Manage habit creation, editing, and tracking",
                        "dependencies": {"required": ["UserAuthComponent"], "optional": []},
                        "completion_criteria": ["CRUD operations for habits", "Habit validation implemented"]
                    }
                ],
                "system_requirements": {
                    "task_analysis": {
                        "original_request": "Create a habit tracking web application",
                        "interpreted_goal": "Build a comprehensive habit tracking application"
                    },
                    "environmental_analysis": {
                        "core_requirements": {
                            "runtime": {"language_version": "Node.js 18.x"},
                            "deployment": {"target_environment": "Cloud hosting"}
                        }
                    },
                    "data_architecture": {
                        "core_entities": [
                            {"name": "User", "description": "Application user"},
                            {"name": "Habit", "description": "User-defined habit"}
                        ]
                    }
                }
            },
            
            "problematic_result": {
                "status": "success",
                "operation_id": "test_operation_002", 
                "structural_components": [
                    {
                        "sequence_number": 1,
                        "name": "OverlyComplexComponent",
                        "type": "core",
                        "purpose": "Handle everything related to the application",
                        "dependencies": {"required": ["NonExistentComponent"], "optional": []},
                        "completion_criteria": ["Everything works"]
                    }
                ],
                "system_requirements": {
                    "task_analysis": {
                        "original_request": "Build a simple todo app",
                        "interpreted_goal": "Create an enterprise-grade distributed system"
                    }
                }
            }
        }

    @pytest.fixture
    def sample_phase_zero_feedback(self):
        """Provide sample phase zero feedback for testing."""
        return {
            "good_feedback": {
                "status": "completed",
                "monitoring_analysis": {"system_health": "good"},
                "deep_analysis": {
                    "structural_agent": {"status": "success", "flag_raised": False},
                    "requirement_agent": {"status": "success", "flag_raised": False}
                },
                "evolution_synthesis": {"recommendations": ["proceed"]}
            },
            
            "concerning_feedback": {
                "status": "completed",
                "monitoring_analysis": {"system_health": "degraded"},
                "deep_analysis": {
                    "structural_agent": {"status": "warning", "flag_raised": True, "issues": ["Overly complex structure"]},
                    "requirement_agent": {"status": "warning", "flag_raised": True, "issues": ["Scope mismatch"]}
                },
                "evolution_synthesis": {"recommendations": ["review_architecture", "simplify_components"]}
            }
        }

    @pytest.mark.asyncio
    async def test_foundation_refinement_basic_analysis(self, foundation_refinement_agent, sample_phase_one_results, sample_phase_zero_feedback):
        """Test basic foundation refinement analysis."""
        phase_one_result = sample_phase_one_results["successful_result"]
        phase_zero_feedback = sample_phase_zero_feedback["good_feedback"]
        operation_id = f"test_basic_{datetime.now().isoformat()}"
        
        logger.info("Testing Foundation Refinement basic analysis")
        
        result = await foundation_refinement_agent.analyze_phase_one_outputs(
            phase_one_result,
            phase_zero_feedback,
            operation_id
        )
        
        # Verify result structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "refinement_analysis" in result, "Should contain refinement analysis"
        
        refinement_analysis = result["refinement_analysis"]
        
        # Should contain required analysis sections
        required_sections = ["critical_failure", "root_cause", "refinement_action"]
        for section in required_sections:
            assert section in refinement_analysis, f"Should contain {section} section"
        
        logger.info("Foundation Refinement basic analysis test passed")

    @pytest.mark.asyncio
    async def test_foundation_refinement_good_result_approval(self, foundation_refinement_agent, sample_phase_one_results, sample_phase_zero_feedback):
        """Test Foundation Refinement approval of good results."""
        phase_one_result = sample_phase_one_results["successful_result"]
        phase_zero_feedback = sample_phase_zero_feedback["good_feedback"]
        operation_id = f"test_approval_{datetime.now().isoformat()}"
        
        logger.info("Testing Foundation Refinement approval of good results")
        
        result = await foundation_refinement_agent.analyze_phase_one_outputs(
            phase_one_result,
            phase_zero_feedback,
            operation_id
        )
        
        # Should approve good results
        refinement_action = result["refinement_analysis"]["refinement_action"]
        assert refinement_action["action"] == "proceed_to_phase_two", "Should approve good results"
        
        # Should indicate no critical failures
        critical_failure = result["refinement_analysis"]["critical_failure"]
        assert not critical_failure.get("category") or critical_failure["category"] == "none", "Should indicate no critical failures"
        
        # Decision method should also approve
        should_proceed = foundation_refinement_agent.should_proceed_to_phase_two(result)
        assert should_proceed, "Should decide to proceed to phase two"
        
        logger.info("Foundation Refinement approval test passed")

    @pytest.mark.asyncio
    async def test_foundation_refinement_problematic_result_rejection(self, foundation_refinement_agent, sample_phase_one_results, sample_phase_zero_feedback):
        """Test Foundation Refinement rejection of problematic results."""
        phase_one_result = sample_phase_one_results["problematic_result"]
        phase_zero_feedback = sample_phase_zero_feedback["concerning_feedback"]
        operation_id = f"test_rejection_{datetime.now().isoformat()}"
        
        logger.info("Testing Foundation Refinement rejection of problematic results")
        
        result = await foundation_refinement_agent.analyze_phase_one_outputs(
            phase_one_result,
            phase_zero_feedback,
            operation_id
        )
        
        # Should identify issues with problematic results
        critical_failure = result["refinement_analysis"]["critical_failure"]
        assert critical_failure["category"] != "none", "Should identify critical issues"
        
        refinement_action = result["refinement_analysis"]["refinement_action"]
        
        # Should either request refinement or identify specific issues
        assert refinement_action["action"] in [
            "refine_garden_planner",
            "refine_environmental_analysis", 
            "refine_root_system_architect",
            "refine_tree_placement_planner",
            "proceed_to_phase_two"  # May still proceed with warnings
        ], "Should provide valid refinement action"
        
        logger.info("Foundation Refinement rejection test passed")

    @pytest.mark.asyncio
    async def test_foundation_refinement_target_agent_identification(self, foundation_refinement_agent, sample_phase_one_results, sample_phase_zero_feedback):
        """Test Foundation Refinement target agent identification."""
        phase_one_result = sample_phase_one_results["problematic_result"]
        phase_zero_feedback = sample_phase_zero_feedback["concerning_feedback"]
        operation_id = f"test_target_{datetime.now().isoformat()}"
        
        logger.info("Testing Foundation Refinement target agent identification")
        
        result = await foundation_refinement_agent.analyze_phase_one_outputs(
            phase_one_result,
            phase_zero_feedback,
            operation_id
        )
        
        # Test target agent identification
        target_agent = foundation_refinement_agent.get_refinement_target_agent(result)
        
        if target_agent:
            # Should identify a valid target agent
            valid_targets = ["garden_planner", "environmental_analysis", "root_system_architect", "tree_placement_planner"]
            assert target_agent in valid_targets, f"Should identify valid target agent, got {target_agent}"
            
            # Root cause should identify the responsible agent
            root_cause = result["refinement_analysis"]["root_cause"]
            assert "responsible_agent" in root_cause, "Should identify responsible agent"
            
        logger.info("Foundation Refinement target agent identification test passed")

    @pytest.mark.asyncio
    async def test_foundation_refinement_guidance_generation(self, foundation_refinement_agent, sample_phase_one_results, sample_phase_zero_feedback):
        """Test Foundation Refinement guidance generation."""
        phase_one_result = sample_phase_one_results["problematic_result"]
        phase_zero_feedback = sample_phase_zero_feedback["concerning_feedback"]
        operation_id = f"test_guidance_{datetime.now().isoformat()}"
        
        logger.info("Testing Foundation Refinement guidance generation")
        
        result = await foundation_refinement_agent.analyze_phase_one_outputs(
            phase_one_result,
            phase_zero_feedback,
            operation_id
        )
        
        # Test guidance generation
        guidance = foundation_refinement_agent.get_refinement_guidance(result)
        
        assert isinstance(guidance, dict), "Should return guidance dictionary"
        
        # Should contain action guidance
        assert "action" in guidance, "Should contain action guidance"
        
        # Should contain specific guidance
        if "specific_guidance" in guidance:
            specific = guidance["specific_guidance"]
            assert "current_state" in specific or "required_state" in specific, "Should provide specific guidance"
        
        logger.info("Foundation Refinement guidance generation test passed")

    @pytest.mark.asyncio
    async def test_foundation_refinement_cycle_management(self, foundation_refinement_agent, sample_phase_one_results, sample_phase_zero_feedback):
        """Test Foundation Refinement cycle management."""
        operation_id = f"test_cycles_{datetime.now().isoformat()}"
        
        logger.info("Testing Foundation Refinement cycle management")
        
        # Check initial cycle count
        initial_cycle = foundation_refinement_agent.get_current_cycle()
        assert initial_cycle == 0, "Should start at cycle 0"
        
        # Increment cycle
        foundation_refinement_agent.increment_cycle()
        assert foundation_refinement_agent.get_current_cycle() == 1, "Should increment cycle"
        
        # Test max cycle limit
        for _ in range(10):  # Exceed max cycles
            foundation_refinement_agent.increment_cycle()
        
        # Should not exceed max cycles
        assert foundation_refinement_agent.get_current_cycle() <= foundation_refinement_agent._max_refinement_cycles, \
            "Should not exceed max cycles"
        
        logger.info("Foundation Refinement cycle management test passed")

    @pytest.mark.asyncio
    async def test_foundation_refinement_with_system_prompt(self, foundation_refinement_agent, sample_phase_one_results, sample_phase_zero_feedback):
        """Test Foundation Refinement using actual system prompt."""
        phase_one_result = sample_phase_one_results["successful_result"]
        phase_zero_feedback = sample_phase_zero_feedback["good_feedback"]
        operation_id = f"test_prompt_{datetime.now().isoformat()}"
        
        logger.info("Testing Foundation Refinement with system prompt")
        
        # Format input for the agent
        analysis_input = f"""
        Phase One Result: {json.dumps(phase_one_result, indent=2)}
        
        Phase Zero Feedback: {json.dumps(phase_zero_feedback, indent=2)}
        """
        
        # Use the actual system prompt
        result = await foundation_refinement_agent.process_with_validation(
            conversation=analysis_input,
            system_prompt_info=("FFTT_system_prompts/phase_one/garden_foundation_refinement_agent", "task_foundation_refinement_prompt"),
            operation_id=operation_id
        )
        
        # Verify the result follows expected structure
        assert isinstance(result, dict), "Result should be a dictionary"
        
        if "error" not in result:
            # Should provide comprehensive refinement analysis
            assert len(str(result)) > 200, "Should provide detailed refinement analysis"
            
            # Check for refinement analysis structure
            result_str = json.dumps(result).lower()
            
            # Should include refinement analysis elements
            analysis_elements = ["refinement", "analysis", "critical", "failure", "action"]
            found_elements = sum(1 for element in analysis_elements if element in result_str)
            assert found_elements >= 2, f"Should include refinement elements, found {found_elements}"
        
        logger.info("Foundation Refinement system prompt test passed")

    @pytest.mark.asyncio
    async def test_foundation_refinement_phase_zero_integration(self, foundation_refinement_agent, sample_phase_one_results, sample_phase_zero_feedback):
        """Test Foundation Refinement integration with Phase Zero feedback."""
        phase_one_result = sample_phase_one_results["successful_result"]
        phase_zero_feedback = sample_phase_zero_feedback["concerning_feedback"]
        operation_id = f"test_integration_{datetime.now().isoformat()}"
        
        logger.info("Testing Foundation Refinement Phase Zero integration")
        
        result = await foundation_refinement_agent.analyze_phase_one_outputs(
            phase_one_result,
            phase_zero_feedback,
            operation_id
        )
        
        # Should incorporate Phase Zero feedback in analysis
        refinement_analysis = result["refinement_analysis"]
        
        # Should reference Phase Zero signals
        if "phase_zero_signals" in refinement_analysis.get("critical_failure", {}):
            signals = refinement_analysis["critical_failure"]["phase_zero_signals"]
            assert isinstance(signals, list), "Phase Zero signals should be a list"
        
        # Should consider Phase Zero recommendations
        result_str = json.dumps(result).lower()
        phase_zero_indicators = ["phase_zero", "monitoring", "evolution", "structural", "requirement"]
        found_indicators = sum(1 for indicator in phase_zero_indicators if indicator in result_str)
        assert found_indicators >= 1, "Should incorporate Phase Zero feedback"
        
        logger.info("Foundation Refinement Phase Zero integration test passed")

    @pytest.mark.asyncio
    async def test_foundation_refinement_error_handling(self, foundation_refinement_agent):
        """Test Foundation Refinement error handling."""
        operation_id = f"test_error_{datetime.now().isoformat()}"
        
        logger.info("Testing Foundation Refinement error handling")
        
        # Test with malformed inputs
        malformed_phase_one = {"invalid": "structure"}
        malformed_phase_zero = {"broken": "feedback"}
        
        result = await foundation_refinement_agent.analyze_phase_one_outputs(
            malformed_phase_one,
            malformed_phase_zero,
            operation_id
        )
        
        # Should handle gracefully
        assert isinstance(result, dict), "Should return dictionary even for malformed input"
        
        # Should contain refinement analysis structure
        assert "refinement_analysis" in result, "Should contain refinement analysis even for errors"
        
        # Should have fallback behavior
        refinement_analysis = result["refinement_analysis"]
        assert "refinement_action" in refinement_analysis, "Should have refinement action even for errors"
        
        logger.info("Foundation Refinement error handling test passed")

    @pytest.mark.asyncio
    async def test_foundation_refinement_state_transitions(self, foundation_refinement_agent, sample_phase_one_results, sample_phase_zero_feedback):
        """Test Foundation Refinement state transitions."""
        phase_one_result = sample_phase_one_results["successful_result"]
        phase_zero_feedback = sample_phase_zero_feedback["good_feedback"]
        operation_id = f"test_states_{datetime.now().isoformat()}"
        
        logger.info("Testing Foundation Refinement state transitions")
        
        # Check initial state
        initial_state = foundation_refinement_agent.development_state
        assert initial_state == DevelopmentState.INITIALIZING
        
        # Process and monitor state changes
        result = await foundation_refinement_agent.analyze_phase_one_outputs(
            phase_one_result,
            phase_zero_feedback,
            operation_id
        )
        
        # Should transition to appropriate final state
        final_state = foundation_refinement_agent.development_state
        assert final_state in [
            DevelopmentState.COMPLETE,
            DevelopmentState.ANALYZING,
            DevelopmentState.ERROR
        ], f"Should be in valid final state, got {final_state}"
        
        logger.info("Foundation Refinement state transitions test passed")

    @pytest.mark.asyncio
    async def test_foundation_refinement_integration_readiness(self, foundation_refinement_agent, sample_phase_one_results, sample_phase_zero_feedback):
        """Test Foundation Refinement integration readiness for orchestrator."""
        phase_one_result = sample_phase_one_results["successful_result"]
        phase_zero_feedback = sample_phase_zero_feedback["good_feedback"]
        operation_id = f"test_integration_{datetime.now().isoformat()}"
        
        logger.info("Testing Foundation Refinement integration readiness")
        
        # Test as it would be called by orchestrator
        result = await foundation_refinement_agent.analyze_phase_one_outputs(
            phase_one_result,
            phase_zero_feedback,
            operation_id
        )
        
        # Verify integration readiness
        assert isinstance(result, dict), "Should return dictionary for orchestrator integration"
        
        # Should be serializable for state management
        try:
            json.dumps(result)
            logger.info("Result is JSON serializable")
        except (TypeError, ValueError) as e:
            pytest.fail(f"Result is not JSON serializable: {e}")
        
        # Should provide decision-making information for orchestrator
        assert "refinement_analysis" in result, "Should provide refinement analysis for orchestrator"
        
        # Should enable orchestrator decision-making
        should_proceed = foundation_refinement_agent.should_proceed_to_phase_two(result)
        assert isinstance(should_proceed, bool), "Should provide clear boolean decision"
        
        if not should_proceed:
            # Should provide target agent if refinement needed
            target_agent = foundation_refinement_agent.get_refinement_target_agent(result)
            # Target agent can be None if no specific agent identified
            if target_agent:
                assert isinstance(target_agent, str), "Target agent should be string"
        
        logger.info("Foundation Refinement integration readiness test passed")