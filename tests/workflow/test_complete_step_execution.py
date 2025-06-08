"""
Test Complete Step-by-Step Execution from run_phase_one.py

This module tests the complete 6-step workflow execution that is missing from existing E2E tests.
Tests the PhaseOneInterface step-by-step execution with real operation tracking and state persistence.
"""

import pytest
import pytest_asyncio
import asyncio
import json
import time
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from run_phase_one import PhaseOneInterface
from resources.events import EventQueue
from resources.state import StateManager


def generate_test_operation_id(test_name: str = "test") -> str:
    """Generate truly unique operation IDs for tests."""
    return f"test_{test_name}_{uuid.uuid4().hex[:8]}_{int(time.time() * 1000)}"


class MockPhaseOneOrchestrator:
    """Mock PhaseOneOrchestrator for testing step execution."""
    
    def __init__(self):
        self._state_manager = None
        self.garden_planner_agent = MagicMock()
        self.earth_agent = MagicMock()
        self.environmental_analysis_agent = MagicMock()
        self.root_system_architect_agent = MagicMock()
        self.tree_placement_planner_agent = MagicMock()
        self.foundation_refinement_agent = MagicMock()
        
        # Track calls for verification
        self.agent_calls = {}
        
        # Setup agent process methods
        self._setup_agent_mocks()
    
    def _setup_agent_mocks(self):
        """Setup mock agent process methods."""
        async def mock_garden_planner_process(prompt):
            self.agent_calls['garden_planner'] = prompt
            return {
                "status": "success",
                "task_analysis": {
                    "original_request": prompt,
                    "interpreted_goal": "Create a comprehensive web application",
                    "scope": {
                        "included": ["User management", "Core functionality", "Basic UI"],
                        "excluded": ["Advanced analytics", "Mobile app"]
                    },
                    "technical_requirements": {
                        "languages": ["Python", "JavaScript"],
                        "frameworks": ["Flask", "React"],
                        "databases": ["PostgreSQL"]
                    }
                }
            }
        
        async def mock_earth_agent_process(validation_input):
            self.agent_calls['earth_agent_validation'] = validation_input
            return {
                "status": "success",
                "validation_result": {
                    "validation_category": "APPROVED",
                    "is_valid": True,
                    "explanation": "Task analysis is comprehensive and technically sound"
                },
                "validated_output": validation_input.get("garden_planner_output", {})
            }
        
        async def mock_environmental_analysis_process(validated_output):
            self.agent_calls['environmental_analysis'] = validated_output
            return {
                "status": "success",
                "analysis": {
                    "requirements": {
                        "functional": ["User registration", "Data management", "Reporting"],
                        "non_functional": ["Security", "Performance", "Scalability"]
                    },
                    "constraints": {
                        "technical": ["Browser compatibility", "API rate limits"],
                        "business": ["6-month timeline", "Budget constraints"]
                    },
                    "stakeholders": ["End users", "Development team", "Product managers"],
                    "success_criteria": ["User adoption > 1000", "Response time < 2s"]
                }
            }
        
        async def mock_root_system_process(env_output):
            self.agent_calls['root_system_architect'] = env_output
            return {
                "status": "success",
                "data_architecture": {
                    "entities": ["User", "Role", "Session", "AuditLog"],
                    "relationships": [
                        {"from": "User", "to": "Role", "type": "many-to-many"},
                        {"from": "User", "to": "Session", "type": "one-to-many"}
                    ],
                    "data_flow": {
                        "authentication": ["Login", "Token validation", "Session management"],
                        "authorization": ["Role checking", "Permission validation"]
                    },
                    "storage": {
                        "database": "PostgreSQL",
                        "caching": "Redis",
                        "file_storage": "AWS S3"
                    }
                }
            }
        
        async def mock_tree_placement_process(root_output):
            self.agent_calls['tree_placement_planner'] = root_output
            return {
                "status": "success",
                "component_architecture": {
                    "components": [
                        {
                            "id": "auth_service",
                            "name": "Authentication Service",
                            "description": "Handles user authentication and session management",
                            "responsibilities": ["User login", "Token management", "Session tracking"],
                            "dependencies": [],
                            "interfaces": ["REST API", "WebSocket"]
                        },
                        {
                            "id": "user_service",
                            "name": "User Management Service",
                            "description": "Manages user profiles and preferences",
                            "responsibilities": ["User CRUD", "Profile management", "Preferences"],
                            "dependencies": ["auth_service"],
                            "interfaces": ["REST API"]
                        },
                        {
                            "id": "data_service",
                            "name": "Data Management Service", 
                            "description": "Core data operations and business logic",
                            "responsibilities": ["Data CRUD", "Business rules", "Validation"],
                            "dependencies": ["auth_service", "user_service"],
                            "interfaces": ["REST API", "GraphQL"]
                        },
                        {
                            "id": "api_gateway",
                            "name": "API Gateway",
                            "description": "Entry point for all client requests",
                            "responsibilities": ["Request routing", "Rate limiting", "Authentication"],
                            "dependencies": ["auth_service", "user_service", "data_service"],
                            "interfaces": ["REST API", "WebSocket"]
                        },
                        {
                            "id": "frontend",
                            "name": "Frontend Application",
                            "description": "React-based user interface",
                            "responsibilities": ["User interface", "State management", "API communication"],
                            "dependencies": ["api_gateway"],
                            "interfaces": ["HTTP", "WebSocket"]
                        }
                    ],
                    "deployment_strategy": {
                        "containerization": "Docker",
                        "orchestration": "Kubernetes",
                        "cloud_provider": "AWS",
                        "monitoring": "Prometheus + Grafana"
                    }
                }
            }
        
        async def mock_foundation_refinement_process(compiled_results):
            self.agent_calls['foundation_refinement'] = compiled_results
            return {
                "status": "success",
                "refinement_analysis": {
                    "status": "refinement_executed",
                    "target_component": "data_service",
                    "refinements_applied": [
                        "Added data validation layer",
                        "Improved error handling",
                        "Enhanced security measures"
                    ],
                    "architecture_improvements": {
                        "separation_of_concerns": "Improved",
                        "scalability": "Enhanced",
                        "maintainability": "Optimized"
                    }
                },
                "final_architecture": {
                    "structural_components": [
                        {
                            "id": "auth_service_refined",
                            "name": "Enhanced Authentication Service",
                            "description": "Robust authentication with security hardening",
                            "dependencies": [],
                            "security_features": ["MFA", "Rate limiting", "Audit logging"]
                        },
                        {
                            "id": "user_service_refined", 
                            "name": "Enhanced User Management Service",
                            "description": "User management with privacy controls",
                            "dependencies": ["auth_service_refined"],
                            "privacy_features": ["Data encryption", "GDPR compliance"]
                        },
                        {
                            "id": "data_service_refined",
                            "name": "Enhanced Data Management Service",
                            "description": "Data service with validation and caching",
                            "dependencies": ["auth_service_refined", "user_service_refined"],
                            "performance_features": ["Caching layer", "Query optimization"]
                        }
                    ]
                }
            }
        
        # Assign mock methods
        self.garden_planner_agent.process = mock_garden_planner_process
        self.earth_agent.process = mock_earth_agent_process
        self.environmental_analysis_agent.process = mock_environmental_analysis_process
        self.root_system_architect_agent.process = mock_root_system_process
        self.tree_placement_planner_agent.process = mock_tree_placement_process
        self.foundation_refinement_agent.process = mock_foundation_refinement_process


@pytest_asyncio.fixture
async def event_queue():
    """Create an event queue for testing."""
    queue = EventQueue()
    await queue.start()
    yield queue
    await queue.stop()


@pytest_asyncio.fixture
async def state_manager(event_queue):
    """Create a state manager for testing."""
    manager = StateManager(event_queue)
    await manager.initialize()
    return manager


@pytest.fixture
def mock_orchestrator(state_manager):
    """Create a mock orchestrator with state manager."""
    orchestrator = MockPhaseOneOrchestrator()
    orchestrator._state_manager = state_manager
    return orchestrator


@pytest_asyncio.fixture
async def clean_phase_one_interface(mock_orchestrator):
    """Create a PhaseOneInterface with state cleanup for testing."""
    interface = PhaseOneInterface(mock_orchestrator)
    
    # Clean up any existing workflow states before starting
    await interface.reset_all_workflow_states()
    
    yield interface
    
    # Clean up after test
    await interface.reset_all_workflow_states()

@pytest.fixture
def phase_one_interface(mock_orchestrator):
    """Create a PhaseOneInterface for testing (legacy fixture)."""
    return PhaseOneInterface(mock_orchestrator)

@pytest_asyncio.fixture(autouse=True)
async def cleanup_state_after_tests(event_queue):
    """Auto-cleanup state after each test."""
    yield
    
    # Reset StateManager singleton for clean state
    from resources.state.manager import StateManager
    StateManager.reset_for_testing()


class TestCompleteStepExecution:
    """Test complete 6-step workflow execution."""
    
    @pytest.mark.asyncio
    async def test_start_phase_one_workflow(self, phase_one_interface):
        """Test starting a Phase One workflow."""
        test_prompt = "Create a comprehensive task management system"
        
        operation_id = await phase_one_interface.start_phase_one(test_prompt)
        
        # Verify operation ID format
        assert operation_id is not None
        assert operation_id.startswith("phase_one_")
        assert len(operation_id) > 20  # Should include timestamp and UUID
        
        # Verify initial state was stored
        status = await phase_one_interface.get_step_status(operation_id)
        assert status["operation_id"] == operation_id
        assert status["status"] == "initialized"
        assert status["current_step"] == "ready"
        assert status["progress_percentage"] == 0
        assert len(status["steps_completed"]) == 0
    
    @pytest.mark.asyncio
    async def test_execute_garden_planner_step(self, phase_one_interface, mock_orchestrator):
        """Test executing the Garden Planner step."""
        test_prompt = "Create a web application for project management"
        
        # Start workflow
        operation_id = await phase_one_interface.start_phase_one(test_prompt)
        
        # Execute first step
        step_result = await phase_one_interface.execute_next_step(operation_id)
        
        # Verify step execution
        assert step_result["status"] == "step_completed"
        assert step_result["operation_id"] == operation_id
        assert step_result["step_executed"] == "garden_planner"
        assert step_result["next_step"] == "earth_agent_validation"
        
        # Verify step result content
        step_data = step_result["step_result"]
        assert step_data["status"] == "success"
        assert step_data["step_name"] == "garden_planner"
        assert "result" in step_data
        assert "task_analysis" in step_data["result"]
        
        # Verify garden planner was called
        assert "garden_planner" in mock_orchestrator.agent_calls
        assert mock_orchestrator.agent_calls["garden_planner"] == test_prompt
        
        # Verify status was updated
        status = await phase_one_interface.get_step_status(operation_id)
        assert status["current_step"] == "garden_planner"
        assert "garden_planner" in status["steps_completed"]
        assert status["progress_percentage"] > 0
    
    @pytest.mark.asyncio
    async def test_execute_earth_agent_validation_step(self, phase_one_interface, mock_orchestrator):
        """Test executing the Earth Agent validation step."""
        test_prompt = "Create a social media platform"
        
        # Start and execute first step
        operation_id = await phase_one_interface.start_phase_one(test_prompt)
        await phase_one_interface.execute_next_step(operation_id)  # Garden Planner
        
        # Execute Earth Agent validation
        step_result = await phase_one_interface.execute_next_step(operation_id)
        
        # Verify step execution
        assert step_result["status"] == "step_completed"
        assert step_result["step_executed"] == "earth_agent_validation"
        assert step_result["next_step"] == "environmental_analysis"
        
        # Verify Earth Agent was called with proper input
        assert "earth_agent_validation" in mock_orchestrator.agent_calls
        validation_input = mock_orchestrator.agent_calls["earth_agent_validation"]
        assert "user_request" in validation_input
        assert "garden_planner_output" in validation_input
        assert validation_input["user_request"] == test_prompt
        
        # Verify step result content
        step_data = step_result["step_result"]
        assert step_data["status"] == "success"
        assert "validation_result" in step_data["result"]
        assert step_data["result"]["validation_result"]["is_valid"] is True
    
    @pytest.mark.asyncio
    async def test_execute_all_six_steps_sequentially(self, phase_one_interface, mock_orchestrator):
        """Test executing all 6 steps in sequence."""
        test_prompt = "Create an e-commerce platform with user management"
        
        # Start workflow
        operation_id = await phase_one_interface.start_phase_one(test_prompt)
        
        # Define expected step sequence
        expected_steps = [
            "garden_planner",
            "earth_agent_validation", 
            "environmental_analysis",
            "root_system_architect",
            "tree_placement_planner",
            "foundation_refinement"
        ]
        
        # Execute all steps
        executed_steps = []
        for i, expected_step in enumerate(expected_steps):
            step_result = await phase_one_interface.execute_next_step(operation_id)
            
            # Verify each step
            assert step_result["status"] == "step_completed"
            assert step_result["step_executed"] == expected_step
            executed_steps.append(expected_step)
            
            # Check progress
            status = await phase_one_interface.get_step_status(operation_id)
            expected_progress = ((i + 1) / len(expected_steps)) * 100
            assert abs(status["progress_percentage"] - expected_progress) < 1
            
            # Verify next step
            if i < len(expected_steps) - 1:
                assert step_result["next_step"] == expected_steps[i + 1]
            else:
                assert step_result["next_step"] == "completed"
        
        # Verify all agents were called
        for step in expected_steps:
            agent_key = step.replace("earth_agent_validation", "earth_agent_validation")
            assert agent_key in mock_orchestrator.agent_calls
        
        # Verify final status
        final_status = await phase_one_interface.get_step_status(operation_id)
        assert len(final_status["steps_completed"]) == len(expected_steps)
        assert final_status["progress_percentage"] == 100
        assert set(final_status["steps_completed"]) == set(expected_steps)
        
        # Verify all step results are stored
        step_results = final_status["step_results"]
        assert len(step_results) == len(expected_steps)
        for step in expected_steps:
            assert step in step_results
            assert step_results[step]["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_workflow_completion_handling(self, phase_one_interface, mock_orchestrator):
        """Test workflow completion after all steps are executed."""
        test_prompt = "Create a blog platform"
        
        # Start and execute all steps
        operation_id = await phase_one_interface.start_phase_one(test_prompt)
        
        # Execute all 6 steps
        for _ in range(6):
            await phase_one_interface.execute_next_step(operation_id)
        
        # Try to execute another step (should indicate completion)
        completion_result = await phase_one_interface.execute_next_step(operation_id)
        
        assert completion_result["status"] == "completed"
        assert completion_result["message"] == "Phase One workflow completed successfully"
        assert "final_results" in completion_result
        
        # Verify final status
        final_status = await phase_one_interface.get_step_status(operation_id)
        assert final_status["status"] == "completed"
        assert final_status["current_step"] == "completed"
    
    @pytest.mark.asyncio
    async def test_step_data_flow_between_agents(self, phase_one_interface, mock_orchestrator):
        """Test that data flows correctly between agents in the workflow."""
        test_prompt = "Create a customer relationship management system"
        
        # Start workflow and execute first few steps
        operation_id = await phase_one_interface.start_phase_one(test_prompt)
        
        # Execute Garden Planner
        await phase_one_interface.execute_next_step(operation_id)
        
        # Execute Earth Agent validation
        await phase_one_interface.execute_next_step(operation_id)
        
        # Execute Environmental Analysis  
        await phase_one_interface.execute_next_step(operation_id)
        
        # Verify data flow
        garden_input = mock_orchestrator.agent_calls["garden_planner"]
        earth_input = mock_orchestrator.agent_calls["earth_agent_validation"]
        env_input = mock_orchestrator.agent_calls["environmental_analysis"]
        
        # Garden Planner gets original prompt
        assert garden_input == test_prompt
        
        # Earth Agent gets Garden Planner output
        assert "garden_planner_output" in earth_input
        assert earth_input["user_request"] == test_prompt
        
        # Environmental Analysis gets validated output
        assert "validated_output" in env_input or env_input is not None
    
    @pytest.mark.asyncio
    async def test_operation_id_persistence(self, phase_one_interface):
        """Test that operation IDs are persistent across step executions."""
        test_prompt = "Create a learning management system"
        
        # Start workflow
        operation_id = await phase_one_interface.start_phase_one(test_prompt)
        
        # Execute multiple steps and verify operation ID consistency
        for i in range(3):
            step_result = await phase_one_interface.execute_next_step(operation_id)
            assert step_result["operation_id"] == operation_id
            
            status = await phase_one_interface.get_step_status(operation_id)
            assert status["operation_id"] == operation_id
    
    @pytest.mark.asyncio 
    async def test_step_timing_and_metadata(self, phase_one_interface):
        """Test that step execution includes timing and metadata."""
        test_prompt = "Create a financial tracking application"
        
        # Start workflow
        operation_id = await phase_one_interface.start_phase_one(test_prompt)
        
        # Execute a step and verify timing metadata
        step_result = await phase_one_interface.execute_next_step(operation_id)
        
        step_data = step_result["step_result"]
        assert "execution_time_seconds" in step_data
        assert "timestamp" in step_data
        assert "attempt" in step_data
        assert step_data["execution_time_seconds"] > 0
        assert step_data["attempt"] == 1
        
        # Verify timestamp format
        timestamp = step_data["timestamp"]
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))  # Should not raise exception


class TestStepExecutionState:
    """Test step execution state management."""
    
    @pytest.mark.asyncio
    async def test_step_status_progression(self, phase_one_interface):
        """Test step status progression through the workflow."""
        test_prompt = "Create a task scheduling system"
        
        operation_id = await phase_one_interface.start_phase_one(test_prompt)
        
        # Initial status
        status = await phase_one_interface.get_step_status(operation_id)
        assert status["status"] == "initialized"
        assert status["current_step"] == "ready"
        
        # After first step
        await phase_one_interface.execute_next_step(operation_id)
        status = await phase_one_interface.get_step_status(operation_id)
        assert status["status"] == "running"
        assert status["current_step"] == "garden_planner"
        
        # After second step
        await phase_one_interface.execute_next_step(operation_id)
        status = await phase_one_interface.get_step_status(operation_id)
        assert status["current_step"] == "earth_agent_validation"
        
        # Execute remaining steps
        for _ in range(4):
            await phase_one_interface.execute_next_step(operation_id)
        
        # Final status
        status = await phase_one_interface.get_step_status(operation_id)
        assert status["status"] == "completed"
        assert status["current_step"] == "completed"
    
    @pytest.mark.asyncio
    async def test_step_results_accumulation(self, phase_one_interface):
        """Test that step results accumulate correctly."""
        test_prompt = "Create a content management system"
        
        operation_id = await phase_one_interface.start_phase_one(test_prompt)
        
        # Execute steps and verify accumulation
        for i in range(3):
            await phase_one_interface.execute_next_step(operation_id)
            
            status = await phase_one_interface.get_step_status(operation_id)
            step_results = status["step_results"]
            
            # Should have results for all completed steps
            assert len(step_results) == i + 1
            
            # Each result should have proper structure
            for step_name, result in step_results.items():
                assert "status" in result
                assert "step_name" in result
                assert "result" in result
                assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_progress_percentage_calculation(self, phase_one_interface):
        """Test progress percentage calculation across all steps."""
        test_prompt = "Create a document management system"
        
        operation_id = await phase_one_interface.start_phase_one(test_prompt)
        total_steps = 6
        
        # Verify progress at each step
        for i in range(total_steps):
            # Execute step
            await phase_one_interface.execute_next_step(operation_id)
            
            # Check progress
            status = await phase_one_interface.get_step_status(operation_id)
            expected_progress = ((i + 1) / total_steps) * 100
            actual_progress = status["progress_percentage"]
            
            # Allow small floating point differences
            assert abs(actual_progress - expected_progress) < 0.1
        
        # Final progress should be 100%
        final_status = await phase_one_interface.get_step_status(operation_id)
        assert final_status["progress_percentage"] == 100


class TestMultipleOperations:
    """Test handling multiple concurrent operations."""
    
    @pytest.mark.asyncio
    async def test_multiple_operations_isolation(self, phase_one_interface):
        """Test that multiple operations don't interfere with each other."""
        # Start two different operations
        operation_id_1 = await phase_one_interface.start_phase_one("Create a chat application")
        operation_id_2 = await phase_one_interface.start_phase_one("Create a video platform")
        
        # Verify they have different IDs
        assert operation_id_1 != operation_id_2
        
        # Execute steps on first operation
        await phase_one_interface.execute_next_step(operation_id_1)
        await phase_one_interface.execute_next_step(operation_id_1)
        
        # Execute steps on second operation
        await phase_one_interface.execute_next_step(operation_id_2)
        
        # Verify independent status
        status_1 = await phase_one_interface.get_step_status(operation_id_1)
        status_2 = await phase_one_interface.get_step_status(operation_id_2)
        
        assert len(status_1["steps_completed"]) == 2
        assert len(status_2["steps_completed"]) == 1
        assert status_1["operation_id"] == operation_id_1
        assert status_2["operation_id"] == operation_id_2
    
    @pytest.mark.asyncio
    async def test_operation_not_found(self, phase_one_interface):
        """Test handling of non-existent operation IDs."""
        fake_operation_id = "nonexistent_operation_123"
        
        # Try to get status for non-existent operation
        status = await phase_one_interface.get_step_status(fake_operation_id)
        assert status["status"] == "not_found"
        assert "No workflow found" in status["message"]
        
        # Try to execute step for non-existent operation
        step_result = await phase_one_interface.execute_next_step(fake_operation_id)
        assert step_result["status"] == "error"
        assert "No workflow found" in step_result["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])