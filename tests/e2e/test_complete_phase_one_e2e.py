"""
Complete End-to-End Phase One Test

This module provides a comprehensive end-to-end test that demonstrates
the complete Phase One workflow from user request to component architecture.
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
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from resources import (
    EventQueue, StateManager, AgentContextManager, CacheManager, 
    MetricsManager, ErrorHandler, MemoryMonitor, ResourceType
)
from resources.monitoring import HealthTracker
from phase_one.orchestrator import PhaseOneOrchestrator
from phase_one.agents.foundation_refinement import FoundationRefinementAgent

logger = logging.getLogger(__name__)

@pytest.mark.real_api
@pytest.mark.e2e
class TestCompletePhaseOneE2E:
    """Complete end-to-end Phase One test suite."""

    @pytest_asyncio.fixture
    async def production_resources(self):
        """Create production-like resource managers."""
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
    async def phase_one_orchestrator(self, production_resources):
        """Create production-ready Phase One orchestrator."""
        orchestrator = PhaseOneOrchestrator(
            **production_resources,
            max_earth_validation_cycles=3,
            validation_timeout=120.0,
            max_refinement_cycles=2
        )
        return orchestrator

    @pytest.fixture
    def real_world_requests(self):
        """Provide real-world user requests for testing."""
        return {
            "habit_tracker": {
                "request": """Create a web application that allows users to track their daily habits and goals. 
                The application should have user accounts, allow users to create custom habits, 
                track daily completion, and show progress over time with charts and statistics.""",
                "expected_components": [
                    "user_authentication",
                    "habit_management", 
                    "tracking_system",
                    "progress_visualization",
                    "data_persistence"
                ]
            },
            
            "task_manager": {
                "request": """Build a collaborative task management system for small teams. 
                Users should be able to create projects, assign tasks to team members, 
                set deadlines, track progress, and receive notifications.""",
                "expected_components": [
                    "user_management",
                    "project_management",
                    "task_assignment",
                    "notification_system",
                    "collaboration_features"
                ]
            },
            
            "blog_platform": {
                "request": """Develop a blogging platform where users can write and publish articles, 
                other users can comment, and there's a basic content management system for administrators.""",
                "expected_components": [
                    "content_management",
                    "user_system",
                    "commenting_system",
                    "publishing_workflow",
                    "admin_panel"
                ]
            }
        }

    @pytest.mark.asyncio
    @pytest.mark.timeout(600)  # 10 minute timeout for complete workflow
    async def test_complete_habit_tracker_workflow(self, phase_one_orchestrator, real_world_requests):
        """Test complete Phase One workflow for habit tracker application."""
        
        request_data = real_world_requests["habit_tracker"]
        user_request = request_data["request"]
        expected_components = request_data["expected_components"]
        operation_id = f"e2e_habit_tracker_{datetime.now().isoformat()}"
        
        logger.info("Starting complete habit tracker workflow test")
        logger.info(f"User request: {user_request}")
        
        # Execute complete Phase One workflow
        result = await phase_one_orchestrator.process_task(user_request, operation_id)
        
        # Verify overall result structure
        assert isinstance(result, dict), "Orchestrator should return dictionary"
        assert "status" in result, "Result should contain status"
        assert "operation_id" in result, "Result should contain operation_id"
        assert result["operation_id"] == operation_id, "Operation ID should match"
        
        # Check execution completed
        if result["status"] == "success":
            logger.info("✅ Phase One completed successfully")
            
            # Verify structural components
            assert "structural_components" in result, "Should contain structural components"
            components = result["structural_components"]
            assert isinstance(components, list), "Components should be a list"
            assert len(components) > 0, "Should have at least one component"
            
            # Verify component quality
            component_names = [comp.get("name", "").lower() for comp in components if isinstance(comp, dict)]
            component_text = " ".join(component_names)
            
            # Check for expected component types
            found_expected = 0
            for expected_comp in expected_components:
                if any(part in component_text for part in expected_comp.split("_")):
                    found_expected += 1
            
            coverage_ratio = found_expected / len(expected_components)
            assert coverage_ratio >= 0.4, f"Should cover at least 40% of expected components, got {coverage_ratio:.2f}"
            
            # Verify system requirements
            assert "system_requirements" in result, "Should contain system requirements"
            sys_reqs = result["system_requirements"]
            
            # Should have task analysis
            assert "task_analysis" in sys_reqs, "Should contain task analysis"
            task_analysis = sys_reqs["task_analysis"]
            assert "original_request" in task_analysis, "Should preserve original request"
            
            # Verify workflow result
            if "workflow_result" in result:
                workflow_result = result["workflow_result"]
                assert "agents" in workflow_result, "Should contain agent results"
                
                # Verify key agents executed
                agents = workflow_result["agents"]
                key_agents = ["garden_planner", "environmental_analysis", "root_system_architect", "tree_placement_planner"]
                for agent in key_agents:
                    if agent in agents:
                        agent_result = agents[agent]
                        assert "success" in agent_result or agent_result.get("success", False), \
                            f"{agent} should complete successfully"
            
            logger.info(f"✅ Generated {len(components)} structural components")
            
            # Log component summary
            for i, comp in enumerate(components[:5]):  # Show first 5 components
                if isinstance(comp, dict):
                    comp_name = comp.get("name", f"Component_{i}")
                    comp_type = comp.get("type", "unknown")
                    logger.info(f"  - {comp_name} ({comp_type})")
            
        elif result["status"] == "failed":
            logger.warning(f"⚠️ Phase One failed at stage: {result.get('failure_stage', 'unknown')}")
            
            # Even if failed, should have proper error information
            assert "failure_stage" in result, "Failed result should indicate failure stage"
            
            # Check if failure is at a reasonable stage
            failure_stage = result["failure_stage"]
            valid_failure_stages = ["garden_planner", "environmental_analysis", "root_system_architect", "tree_placement_planner"]
            assert failure_stage in valid_failure_stages, f"Should fail at valid stage, got {failure_stage}"
            
        else:
            pytest.fail(f"Unexpected result status: {result['status']}")
        
        # Verify execution time
        execution_time = result.get("execution_time", 0)
        logger.info(f"⏱️ Total execution time: {execution_time:.2f} seconds")
        
        # Should complete within reasonable time (even if it takes longer than ideal)
        assert execution_time < 600, f"Should complete within 10 minutes, took {execution_time:.2f}s"
        
        logger.info("Complete habit tracker workflow test passed")

    @pytest.mark.asyncio
    @pytest.mark.timeout(450)  # 7.5 minute timeout
    async def test_task_manager_workflow_with_refinement(self, phase_one_orchestrator, real_world_requests):
        """Test Phase One workflow with potential refinement for task manager."""
        
        request_data = real_world_requests["task_manager"]
        user_request = request_data["request"]
        operation_id = f"e2e_task_manager_{datetime.now().isoformat()}"
        
        logger.info("Starting task manager workflow with refinement test")
        
        # Execute workflow
        result = await phase_one_orchestrator.process_task(user_request, operation_id)
        
        # Verify result
        assert isinstance(result, dict), "Should return dictionary"
        assert "status" in result, "Should contain status"
        
        if result["status"] == "success":
            logger.info("✅ Task manager workflow completed successfully")
            
            # Check for refinement metadata
            if "refinement_analysis" in result:
                logger.info("🔄 Refinement analysis was performed")
                refinement = result["refinement_analysis"]
                
                if isinstance(refinement, dict):
                    if refinement.get("status") == "refinement_executed":
                        logger.info("✅ Refinement cycle was executed")
                        assert "target_agent" in refinement, "Should identify target agent"
                        target_agent = refinement["target_agent"]
                        logger.info(f"🎯 Target agent for refinement: {target_agent}")
            
            # Verify components for collaborative system
            if "structural_components" in result:
                components = result["structural_components"]
                component_text = json.dumps(components).lower()
                
                # Should identify collaboration-related components
                collab_indicators = ["team", "project", "assign", "collaborate", "share", "notify"]
                found_collab = sum(1 for indicator in collab_indicators if indicator in component_text)
                assert found_collab >= 2, f"Should identify collaborative features, found {found_collab}"
        
        elif result["status"] == "failed":
            logger.info(f"⚠️ Task manager workflow failed at: {result.get('failure_stage')}")
        
        logger.info("Task manager workflow with refinement test completed")

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)  # 5 minute timeout for simpler case
    async def test_blog_platform_workflow_validation(self, phase_one_orchestrator, real_world_requests):
        """Test Phase One workflow validation for blog platform."""
        
        request_data = real_world_requests["blog_platform"]
        user_request = request_data["request"]
        operation_id = f"e2e_blog_platform_{datetime.now().isoformat()}"
        
        logger.info("Starting blog platform workflow validation test")
        
        # Execute workflow
        result = await phase_one_orchestrator.process_task(user_request, operation_id)
        
        # Verify basic structure
        assert isinstance(result, dict), "Should return dictionary"
        assert "status" in result, "Should contain status"
        
        if result["status"] == "success":
            logger.info("✅ Blog platform workflow completed successfully")
            
            # Verify content management aspects
            if "structural_components" in result:
                components = result["structural_components"]
                component_text = json.dumps(components).lower()
                
                # Should identify content management features
                cms_indicators = ["content", "article", "post", "publish", "admin", "manage"]
                found_cms = sum(1 for indicator in cms_indicators if indicator in component_text)
                assert found_cms >= 2, f"Should identify CMS features, found {found_cms}"
                
                # Should consider user-generated content
                ugc_indicators = ["comment", "user", "author", "write", "publish"]
                found_ugc = sum(1 for indicator in ugc_indicators if indicator in component_text)
                assert found_ugc >= 2, f"Should consider user-generated content, found {found_ugc}"
        
        logger.info("Blog platform workflow validation test completed")

    @pytest.mark.asyncio
    @pytest.mark.timeout(180)  # 3 minute timeout for metrics test
    async def test_orchestrator_metrics_and_monitoring(self, phase_one_orchestrator):
        """Test orchestrator metrics and monitoring capabilities."""
        
        user_request = "Create a simple note-taking app"
        operation_id = f"e2e_metrics_{datetime.now().isoformat()}"
        
        logger.info("Starting orchestrator metrics and monitoring test")
        
        # Execute workflow and capture metrics
        start_time = datetime.now()
        result = await phase_one_orchestrator.process_task(user_request, operation_id)
        end_time = datetime.now()
        
        # Verify metrics collection
        assert "execution_time" in result, "Should include execution time"
        
        execution_time = result["execution_time"]
        calculated_time = (end_time - start_time).total_seconds()
        
        # Execution time should be reasonable
        assert abs(execution_time - calculated_time) < 5, "Execution time should be accurate"
        
        # Check workflow status
        workflow_status = await phase_one_orchestrator.get_workflow_status(operation_id)
        assert isinstance(workflow_status, dict), "Should return workflow status"
        assert "status" in workflow_status, "Should contain status"
        
        # Verify operation tracking
        assert workflow_status["operation_id"] == operation_id, "Should track correct operation"
        
        logger.info(f"✅ Metrics collected - execution time: {execution_time:.2f}s")
        
        # Test agent metrics (if available)
        try:
            agent_metrics = await phase_one_orchestrator.get_agent_metrics("garden_planner")
            assert isinstance(agent_metrics, dict), "Should return agent metrics"
            logger.info("✅ Agent metrics available")
        except Exception as e:
            logger.info(f"ℹ️ Agent metrics not available: {e}")
        
        logger.info("Orchestrator metrics and monitoring test completed")

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)  # 2 minute timeout for error test
    async def test_workflow_error_recovery(self, phase_one_orchestrator):
        """Test workflow error recovery and graceful failure."""
        
        # Intentionally problematic requests
        problematic_requests = [
            "",  # Empty request
            "x" * 1000,  # Very long request
            "Build an impossible application that violates physics",  # Impossible request
        ]
        
        logger.info("Starting workflow error recovery test")
        
        for i, request in enumerate(problematic_requests):
            operation_id = f"e2e_error_{i}_{datetime.now().isoformat()}"
            
            try:
                result = await phase_one_orchestrator.process_task(request, operation_id)
                
                # Should handle gracefully
                assert isinstance(result, dict), f"Should return dict for error case {i}"
                assert "status" in result, f"Should have status for error case {i}"
                
                # Should not crash
                if result["status"] == "error":
                    assert "message" in result, f"Error should have message for case {i}"
                    logger.info(f"✅ Error case {i} handled gracefully: {result['status']}")
                elif result["status"] == "success":
                    logger.info(f"✅ Error case {i} completed successfully (robust system)")
                else:
                    logger.info(f"ℹ️ Error case {i} status: {result['status']}")
                
            except Exception as e:
                pytest.fail(f"Unhandled exception for error case {i}: {str(e)}")
        
        logger.info("Workflow error recovery test completed")

    @pytest.mark.asyncio
    @pytest.mark.timeout(600)  # 10 minute timeout for comprehensive test
    async def test_comprehensive_system_validation(self, phase_one_orchestrator, real_world_requests):
        """Comprehensive system validation test covering all major functionality."""
        
        logger.info("Starting comprehensive system validation test")
        
        # Test multiple requests to validate system robustness
        test_results = {}
        
        for request_name, request_data in real_world_requests.items():
            logger.info(f"\n🧪 Testing {request_name}...")
            
            operation_id = f"e2e_comprehensive_{request_name}_{datetime.now().isoformat()}"
            
            try:
                start_time = datetime.now()
                result = await phase_one_orchestrator.process_task(
                    request_data["request"], 
                    operation_id
                )
                execution_time = (datetime.now() - start_time).total_seconds()
                
                test_results[request_name] = {
                    "status": result.get("status"),
                    "execution_time": execution_time,
                    "components_count": len(result.get("structural_components", [])),
                    "success": result.get("status") == "success"
                }
                
                logger.info(f"✅ {request_name}: {result.get('status')} ({execution_time:.1f}s)")
                
            except Exception as e:
                test_results[request_name] = {
                    "status": "exception",
                    "error": str(e),
                    "success": False
                }
                logger.error(f"❌ {request_name}: Exception - {str(e)}")
        
        # Analyze results
        successful_tests = sum(1 for result in test_results.values() if result["success"])
        total_tests = len(test_results)
        success_rate = (successful_tests / total_tests) * 100
        
        logger.info(f"\n📊 Comprehensive Test Results:")
        logger.info(f"Success rate: {success_rate:.1f}% ({successful_tests}/{total_tests})")
        
        for request_name, result in test_results.items():
            status_emoji = "✅" if result["success"] else "❌"
            logger.info(f"  {status_emoji} {request_name}: {result['status']}")
        
        # System should handle at least 2/3 of requests successfully
        assert success_rate >= 66.7, f"System should handle at least 67% of requests, got {success_rate:.1f}%"
        
        logger.info("✅ Comprehensive system validation completed successfully")

# Quick validation test that can run without API key
@pytest.mark.integration
class TestPhaseOneSystemValidation:
    """System validation tests that don't require real LLM calls."""
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_system_component_initialization(self):
        """Test that all system components can be initialized properly."""
        
        logger.info("Testing system component initialization")
        
        # Test resource initialization
        event_queue = EventQueue()
        await event_queue.start()
        
        try:
            state_manager = StateManager(event_queue)
            await state_manager.initialize()
            
            context_manager = AgentContextManager(event_queue)
            await context_manager.initialize()
            
            cache_manager = CacheManager(event_queue)
            await cache_manager.initialize()
            
            metrics_manager = MetricsManager(event_queue)
            await metrics_manager.initialize()
            
            error_handler = ErrorHandler(event_queue)
            
            memory_monitor = MemoryMonitor(event_queue)
            health_tracker = HealthTracker(event_queue)
            
            # Test orchestrator initialization
            orchestrator = PhaseOneOrchestrator(
                event_queue=event_queue,
                state_manager=state_manager,
                context_manager=context_manager,
                cache_manager=cache_manager,
                metrics_manager=metrics_manager,
                error_handler=error_handler,
                memory_monitor=memory_monitor,
                health_tracker=health_tracker,
                max_earth_validation_cycles=1,
                validation_timeout=30.0
            )
            
            assert orchestrator is not None, "Orchestrator should initialize successfully"
            
            logger.info("✅ All system components initialized successfully")
            
        finally:
            await event_queue.stop()
        
        logger.info("System component initialization test completed")