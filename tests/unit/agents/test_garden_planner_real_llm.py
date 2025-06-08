"""
Comprehensive test suite for Garden Planner Agent with real LLM calls and actual prompts.

This module tests the Garden Planner agent's core functionality with real API calls
to ensure end-to-end operational readiness for phase one.
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
from phase_one.agents.garden_planner import GardenPlannerAgent
from phase_one.models.enums import DevelopmentState
from FFTT_system_prompts.phase_one.garden_planner_agent import (
    initial_task_elaboration_prompt,
    initial_task_elaboration_schema,
    task_reflection_prompt,
    task_reflection_schema,
    task_revision_prompt,
    task_revision_schema,
    task_elaboration_refinement_prompt,
    task_elaboration_refinement_schema
)

logger = logging.getLogger(__name__)

@pytest.mark.real_api
class TestGardenPlannerRealLLM:
    """Test suite for Garden Planner Agent using real LLM API calls."""

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
    async def garden_planner_agent(self, real_resources):
        """Create a Garden Planner Agent instance with real resources."""
        agent = GardenPlannerAgent(
            agent_id="test_garden_planner",
            **real_resources
        )
        return agent

    @pytest.fixture
    def test_user_requests(self):
        """Provide various test user requests for comprehensive testing."""
        return {
            "simple_web_app": "Create a web application that allows users to track their daily habits and goals.",
            
            "complex_e_commerce": """Create a comprehensive e-commerce platform with the following features:
- User authentication and profile management
- Product catalog with search and filtering
- Shopping cart and checkout system
- Payment processing integration
- Order tracking and history
- Admin dashboard for inventory management
- Mobile-responsive design
- RESTful API for mobile app integration""",
            
            "minimal_task": "Build a simple todo list app",
            
            "ambiguous_request": "I need a system that helps people do things better",
            
            "technical_specific": """Develop a microservices-based inventory management system using:
- Node.js with Express for API services
- PostgreSQL for data persistence
- Redis for caching
- Docker for containerization
- Kubernetes for orchestration
- GraphQL for client queries
- JWT for authentication""",
            
            "non_technical": "Create something that helps small businesses manage their customers and sales"
        }

    @pytest.mark.asyncio
    async def test_garden_planner_initial_task_elaboration_simple(self, garden_planner_agent, test_user_requests):
        """Test Garden Planner's initial task elaboration with a simple request."""
        user_request = test_user_requests["simple_web_app"]
        operation_id = f"test_simple_{datetime.now().isoformat()}"
        
        logger.info(f"Testing Garden Planner with simple request: {user_request}")
        
        # Test initial task elaboration
        result = await garden_planner_agent.process_with_validation(
            conversation=user_request,
            system_prompt_info=("FFTT_system_prompts/phase_one", "garden_planner_agent"),
            operation_id=operation_id
        )
        
        # Verify the result structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "task_analysis" in result, "Result should contain task_analysis"
        
        task_analysis = result["task_analysis"]
        
        # Verify required fields are present
        required_fields = [
            "original_request", "interpreted_goal", "scope", 
            "technical_requirements", "constraints", "considerations"
        ]
        for field in required_fields:
            assert field in task_analysis, f"Task analysis should contain {field}"
        
        # Verify nested structure
        assert "included" in task_analysis["scope"], "Scope should have included items"
        assert "excluded" in task_analysis["scope"], "Scope should have excluded items"
        assert "assumptions" in task_analysis["scope"], "Scope should have assumptions"
        
        assert "languages" in task_analysis["technical_requirements"], "Should specify languages"
        assert "frameworks" in task_analysis["technical_requirements"], "Should specify frameworks"
        
        # Verify content quality
        assert task_analysis["original_request"] == user_request, "Should preserve original request"
        assert len(task_analysis["interpreted_goal"]) > 50, "Should provide detailed goal interpretation"
        assert len(task_analysis["scope"]["included"]) > 0, "Should include specific features"
        
        logger.info("Garden Planner simple request test passed")

    @pytest.mark.asyncio
    async def test_garden_planner_complex_elaboration(self, garden_planner_agent, test_user_requests):
        """Test Garden Planner with a complex e-commerce request."""
        user_request = test_user_requests["complex_e_commerce"]
        operation_id = f"test_complex_{datetime.now().isoformat()}"
        
        logger.info(f"Testing Garden Planner with complex request")
        
        result = await garden_planner_agent.process_with_validation(
            conversation=user_request,
            system_prompt_info=("FFTT_system_prompts/phase_one", "garden_planner_agent"),
            operation_id=operation_id
        )
        
        assert "task_analysis" in result
        task_analysis = result["task_analysis"]
        
        # For complex requests, should identify multiple components
        assert len(task_analysis["scope"]["included"]) >= 5, "Complex request should include multiple features"
        assert len(task_analysis["technical_requirements"]["frameworks"]) >= 2, "Should identify multiple frameworks"
        assert len(task_analysis["considerations"]["security"]) >= 2, "Should identify security considerations"
        
        # Should identify e-commerce specific requirements
        included_text = " ".join(task_analysis["scope"]["included"]).lower()
        assert any(term in included_text for term in ["payment", "checkout", "cart", "product"]), \
            "Should identify e-commerce specific features"
        
        logger.info("Garden Planner complex request test passed")

    @pytest.mark.asyncio
    async def test_garden_planner_ambiguous_request_handling(self, garden_planner_agent, test_user_requests):
        """Test how Garden Planner handles ambiguous requests."""
        user_request = test_user_requests["ambiguous_request"]
        operation_id = f"test_ambiguous_{datetime.now().isoformat()}"
        
        logger.info(f"Testing Garden Planner with ambiguous request")
        
        result = await garden_planner_agent.process_with_validation(
            conversation=user_request,
            system_prompt_info=("FFTT_system_prompts/phase_one", "garden_planner_agent"),
            operation_id=operation_id
        )
        
        assert "task_analysis" in result
        task_analysis = result["task_analysis"]
        
        # Should make reasonable assumptions and clarify scope
        assert len(task_analysis["scope"]["assumptions"]) >= 3, "Should make explicit assumptions for ambiguous requests"
        assert len(task_analysis["interpreted_goal"]) > 100, "Should provide detailed interpretation"
        
        # Should identify the need for clarification
        assumptions_text = " ".join(task_analysis["scope"]["assumptions"]).lower()
        assert any(term in assumptions_text for term in ["assume", "unclear", "clarify", "interpret"]), \
            "Should acknowledge ambiguity in assumptions"
        
        logger.info("Garden Planner ambiguous request test passed")

    @pytest.mark.asyncio
    async def test_garden_planner_reflection_process(self, garden_planner_agent, test_user_requests):
        """Test Garden Planner's reflection capabilities with actual prompts."""
        user_request = test_user_requests["simple_web_app"]
        operation_id = f"test_reflection_{datetime.now().isoformat()}"
        
        logger.info("Testing Garden Planner reflection process")
        
        # First get initial analysis
        initial_result = await garden_planner_agent.process_with_validation(
            conversation=user_request,
            system_prompt_info=("FFTT_system_prompts/phase_one", "garden_planner_agent"),
            operation_id=operation_id
        )
        
        # Test reflection process
        reflection_result = await garden_planner_agent.standard_reflect(
            output=initial_result,
            prompt_path="FFTT_system_prompts/phase_one",
            prompt_name="task_reflection_prompt"
        )
        
        # Verify reflection structure
        assert "reflection_results" in reflection_result, "Should contain reflection results"
        
        reflection_data = reflection_result["reflection_results"]
        
        # Verify reflection categories
        required_categories = ["complexity_issues", "completeness_issues", "consistency_issues"]
        for category in required_categories:
            assert category in reflection_data, f"Reflection should include {category}"
        
        # Verify subcategories
        assert "granularity" in reflection_data["complexity_issues"]
        assert "complexity_level" in reflection_data["complexity_issues"]
        assert "requirements_coverage" in reflection_data["completeness_issues"]
        assert "dependencies" in reflection_data["completeness_issues"]
        assert "cross_cutting" in reflection_data["completeness_issues"]
        
        logger.info("Garden Planner reflection test passed")

    @pytest.mark.asyncio
    async def test_garden_planner_revision_process(self, garden_planner_agent, test_user_requests):
        """Test Garden Planner's revision capabilities."""
        user_request = test_user_requests["technical_specific"]
        operation_id = f"test_revision_{datetime.now().isoformat()}"
        
        logger.info("Testing Garden Planner revision process")
        
        # Get initial analysis
        initial_result = await garden_planner_agent.process_with_validation(
            conversation=user_request,
            system_prompt_info=("FFTT_system_prompts/phase_one", "garden_planner_agent"),
            operation_id=operation_id
        )
        
        # Create mock reflection feedback to trigger revision
        mock_reflection = {
            "reflection_results": {
                "complexity_issues": {
                    "granularity": [{
                        "severity": "high",
                        "issue": "Task scope too broad",
                        "recommendation": "Break down into smaller components"
                    }],
                    "complexity_level": []
                },
                "completeness_issues": {
                    "requirements_coverage": [{
                        "severity": "medium",
                        "missing_component": "Error handling strategy",
                        "impact": "System reliability",
                        "recommendation": "Add comprehensive error handling requirements"
                    }],
                    "dependencies": [],
                    "cross_cutting": []
                },
                "consistency_issues": {
                    "technical_alignment": [],
                    "constraint_compatibility": [],
                    "assumption_validation": []
                }
            }
        }
        
        # Test revision process
        revision_input = f"""
        Original output: {initial_result}
        Reflection results: {mock_reflection}
        """
        
        revision_result = await garden_planner_agent.standard_refine(
            output=initial_result,
            refinement_guidance=mock_reflection,
            prompt_path="FFTT_system_prompts/phase_one",
            prompt_name="task_revision_prompt"
        )
        
        # Verify revision structure
        assert "revision_metadata" in revision_result, "Should contain revision metadata"
        assert "task_analysis" in revision_result, "Should contain revised task analysis"
        
        revision_metadata = revision_result["revision_metadata"]
        assert "processed_issues" in revision_metadata
        assert "revision_summary" in revision_metadata
        assert "validation_steps" in revision_metadata
        
        logger.info("Garden Planner revision test passed")

    @pytest.mark.asyncio
    async def test_garden_planner_schema_compliance(self, garden_planner_agent, test_user_requests):
        """Test that Garden Planner outputs comply with expected schemas."""
        user_request = test_user_requests["minimal_task"]
        operation_id = f"test_schema_{datetime.now().isoformat()}"
        
        logger.info("Testing Garden Planner schema compliance")
        
        result = await garden_planner_agent.process_with_validation(
            conversation=user_request,
            system_prompt_info=("FFTT_system_prompts/phase_one", "garden_planner_agent"),
            operation_id=operation_id
        )
        
        # Validate against the actual schema
        import jsonschema
        
        try:
            jsonschema.validate(instance=result, schema=initial_task_elaboration_schema)
            logger.info("Garden Planner output complies with schema")
        except jsonschema.ValidationError as e:
            pytest.fail(f"Garden Planner output does not comply with schema: {e.message}")

    @pytest.mark.asyncio
    async def test_garden_planner_technical_requirement_extraction(self, garden_planner_agent, test_user_requests):
        """Test Garden Planner's ability to extract technical requirements."""
        user_request = test_user_requests["technical_specific"]
        operation_id = f"test_tech_req_{datetime.now().isoformat()}"
        
        logger.info("Testing Garden Planner technical requirement extraction")
        
        result = await garden_planner_agent.process_with_validation(
            conversation=user_request,
            system_prompt_info=("FFTT_system_prompts/phase_one", "garden_planner_agent"),
            operation_id=operation_id
        )
        
        tech_req = result["task_analysis"]["technical_requirements"]
        
        # Should identify specific technologies mentioned in request
        languages = [lang.lower() for lang in tech_req["languages"]]
        frameworks = [fw.lower() for fw in tech_req["frameworks"]]
        infrastructure = [inf.lower() for inf in tech_req["infrastructure"]]
        
        # Check for specific technologies mentioned in the request
        assert any("node" in lang or "javascript" in lang for lang in languages), "Should identify Node.js/JavaScript"
        assert any("express" in fw for fw in frameworks), "Should identify Express framework"
        assert any("postgresql" in inf or "postgres" in inf for inf in infrastructure), "Should identify PostgreSQL"
        assert any("redis" in inf for inf in infrastructure), "Should identify Redis"
        assert any("docker" in inf for inf in infrastructure), "Should identify Docker"
        
        logger.info("Garden Planner technical requirement extraction test passed")

    @pytest.mark.asyncio
    async def test_garden_planner_constraint_identification(self, garden_planner_agent, test_user_requests):
        """Test Garden Planner's constraint identification capabilities."""
        user_request = test_user_requests["non_technical"]
        operation_id = f"test_constraints_{datetime.now().isoformat()}"
        
        logger.info("Testing Garden Planner constraint identification")
        
        result = await garden_planner_agent.process_with_validation(
            conversation=user_request,
            system_prompt_info=("FFTT_system_prompts/phase_one", "garden_planner_agent"),
            operation_id=operation_id
        )
        
        constraints = result["task_analysis"]["constraints"]
        
        # Should identify typical small business constraints
        business_constraints = [c.lower() for c in constraints["business"]]
        technical_constraints = [c.lower() for c in constraints["technical"]]
        
        # Should consider small business context
        assert any("budget" in c or "cost" in c for c in business_constraints), "Should consider budget constraints"
        assert any("ease" in c or "simple" in c or "user-friendly" in c for c in technical_constraints), \
            "Should consider usability for non-technical users"
        
        logger.info("Garden Planner constraint identification test passed")

    @pytest.mark.asyncio
    async def test_garden_planner_error_handling(self, garden_planner_agent):
        """Test Garden Planner's error handling with malformed inputs."""
        operation_id = f"test_error_{datetime.now().isoformat()}"
        
        logger.info("Testing Garden Planner error handling")
        
        # Test with empty request
        result = await garden_planner_agent.process_with_validation(
            conversation="",
            system_prompt_info=("FFTT_system_prompts/phase_one", "garden_planner_agent"),
            operation_id=operation_id
        )
        
        # Should handle gracefully and still produce valid structure
        assert isinstance(result, dict), "Should return dictionary even for empty input"
        
        # If error occurred, should be properly formatted
        if "error" in result:
            assert isinstance(result["error"], str), "Error should be a string"
        else:
            # If processed successfully, should have basic structure
            assert "task_analysis" in result, "Should still produce task analysis structure"
        
        logger.info("Garden Planner error handling test passed")

    @pytest.mark.asyncio
    async def test_garden_planner_state_transitions(self, garden_planner_agent, test_user_requests):
        """Test Garden Planner's development state transitions."""
        user_request = test_user_requests["simple_web_app"]
        operation_id = f"test_states_{datetime.now().isoformat()}"
        
        logger.info("Testing Garden Planner state transitions")
        
        # Check initial state
        assert garden_planner_agent.development_state == DevelopmentState.INITIALIZING
        
        # Process request and monitor state changes
        result = await garden_planner_agent.process_with_validation(
            conversation=user_request,
            system_prompt_info=("FFTT_system_prompts/phase_one", "garden_planner_agent"),
            operation_id=operation_id
        )
        
        # Should transition to appropriate final state
        assert garden_planner_agent.development_state in [
            DevelopmentState.COMPLETE, 
            DevelopmentState.ANALYZING, 
            DevelopmentState.ERROR
        ], f"Should be in valid final state, got {garden_planner_agent.development_state}"
        
        logger.info("Garden Planner state transitions test passed")

    @pytest.mark.asyncio 
    async def test_garden_planner_memory_tracking(self, garden_planner_agent, test_user_requests):
        """Test Garden Planner's memory tracking capabilities."""
        user_request = test_user_requests["complex_e_commerce"]
        operation_id = f"test_memory_{datetime.now().isoformat()}"
        
        logger.info("Testing Garden Planner memory tracking")
        
        # Process a large request
        result = await garden_planner_agent.process_with_validation(
            conversation=user_request,
            system_prompt_info=("FFTT_system_prompts/phase_one", "garden_planner_agent"),
            operation_id=operation_id
        )
        
        # Memory tracking should be working (no exceptions)
        assert isinstance(result, dict), "Should complete processing without memory issues"
        
        # Check that memory monitor was used
        memory_monitor = garden_planner_agent._memory_monitor
        assert memory_monitor is not None, "Should have memory monitor"
        
        logger.info("Garden Planner memory tracking test passed")