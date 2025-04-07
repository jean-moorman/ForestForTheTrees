import unittest
import asyncio
import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

# Import the module to test
from phase_two import (
    ComponentDevelopmentState,
    ComponentDevelopmentContext,
    ComponentTestCreationAgent,
    ComponentImplementationAgent,
    IntegrationTestAgent,
    SystemTestAgent,
    DeploymentTestAgent,
    PhaseTwo
)

class TestComponentDevelopmentContext:
    """Test the ComponentDevelopmentContext class"""
    
    def test_init(self):
        """Test initialization of ComponentDevelopmentContext"""
        context = ComponentDevelopmentContext(
            component_id="test_component",
            component_name="Test Component",
            description="A test component",
            requirements={"key": "value"}
        )
        
        assert context.component_id == "test_component"
        assert context.component_name == "Test Component"
        assert context.description == "A test component"
        assert context.requirements == {"key": "value"}
        assert context.dependencies == set()
        assert context.features == []
        assert context.state == ComponentDevelopmentState.PLANNING
        assert context.tests == []
        assert context.implementation is None
        assert context.iteration_history == []
    
    def test_record_iteration(self):
        """Test recording an iteration"""
        context = ComponentDevelopmentContext(
            component_id="test_component",
            component_name="Test Component",
            description="A test component",
            requirements={"key": "value"}
        )
        
        context.record_iteration(
            ComponentDevelopmentState.TEST_CREATION,
            {"test_result": "success"}
        )
        
        assert len(context.iteration_history) == 1
        assert context.state == ComponentDevelopmentState.TEST_CREATION
        assert context.iteration_history[0]["state"] == "TEST_CREATION"
        assert context.iteration_history[0]["details"] == {"test_result": "success"}
        assert "timestamp" in context.iteration_history[0]

@pytest.mark.asyncio
class TestComponentTestCreationAgent:
    """Test the ComponentTestCreationAgent class"""
    
    async def test_create_test_specifications(self):
        """Test creating test specifications"""
        # Create mock dependencies
        event_queue = AsyncMock()
        state_manager = AsyncMock()
        context_manager = AsyncMock()
        cache_manager = AsyncMock()
        metrics_manager = AsyncMock()
        error_handler = AsyncMock()
        
        # Create the agent
        agent = ComponentTestCreationAgent(
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler
        )
        
        # Mock the process_with_validation method
        mock_validation_result = {
            "test_specifications": [
                {
                    "id": "test_1",
                    "name": "Test 1",
                    "description": "Test description",
                    "test_type": "unit",
                    "expected_result": "Success"
                }
            ],
            "test_coverage": {
                "requirements_covered": ["req1", "req2"],
                "coverage_percentage": 80.0
            }
        }
        
        agent.process_with_validation = AsyncMock(return_value=mock_validation_result)
        agent.set_agent_state = AsyncMock()
        
        # Test input
        component_requirements = {
            "name": "Test Component",
            "component_id": "test_component",
            "description": "A test component"
        }
        
        # Call the method
        result = await agent.create_test_specifications(component_requirements, "test_op")
        
        # Verify result
        assert "test_specifications" in result
        assert "test_coverage" in result
        assert "component_name" in result
        assert "component_id" in result
        assert "operation_id" in result
        assert result["component_name"] == "Test Component"
        assert result["component_id"] == "test_component"
        assert result["operation_id"] == "test_op"
        
        # Verify the agent state was updated
        agent.set_agent_state.assert_called()
        
        # Verify process_with_validation was called correctly
        agent.process_with_validation.assert_called_once()

@pytest.mark.asyncio
class TestPhaseTwo:
    """Test the PhaseTwo class"""
    
    async def test_sort_components_by_dependencies(self):
        """Test sorting components by dependencies"""
        # Create mock dependencies
        event_queue = AsyncMock()
        state_manager = AsyncMock()
        context_manager = AsyncMock()
        cache_manager = AsyncMock()
        metrics_manager = AsyncMock()
        error_handler = AsyncMock()
        phase_zero = AsyncMock()
        phase_three = AsyncMock()
        
        # Create PhaseTwo instance
        phase_two = PhaseTwo(
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            phase_zero,
            phase_three
        )
        
        # Test components with dependencies
        components = [
            {
                "id": "comp3",
                "name": "Component 3",
                "dependencies": ["comp1", "comp2"]
            },
            {
                "id": "comp2",
                "name": "Component 2",
                "dependencies": ["comp1"]
            },
            {
                "id": "comp1",
                "name": "Component 1",
                "dependencies": []
            }
        ]
        
        sorted_components = phase_two._sort_components_by_dependencies(components)
        
        # Verify sorting
        assert sorted_components[0]["id"] == "comp1"  # No dependencies
        assert sorted_components[1]["id"] == "comp2"  # Depends on comp1
        assert sorted_components[2]["id"] == "comp3"  # Depends on comp1 and comp2
    
    @patch('phase_two.Component')
    async def test_run_component_tests(self, mock_component):
        """Test running component tests"""
        # Create mock dependencies
        event_queue = AsyncMock()
        state_manager = AsyncMock()
        context_manager = AsyncMock()
        cache_manager = AsyncMock()
        metrics_manager = AsyncMock()
        error_handler = AsyncMock()
        phase_zero = AsyncMock()
        phase_three = AsyncMock()
        
        # Create PhaseTwo instance
        phase_two = PhaseTwo(
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            phase_zero,
            phase_three
        )
        
        # Create a mock component
        component = mock_component.return_value
        component.create_test_execution = MagicMock()
        component.update_test_state = MagicMock()
        
        # Create test context with tests
        context = ComponentDevelopmentContext(
            component_id="test_component",
            component_name="Test Component",
            description="A test component",
            requirements={}
        )
        context.tests = [
            {
                "id": "test_1",
                "name": "Test 1",
                "description": "Test 1 description",
                "test_type": "unit",
                "expected_result": "Success"
            },
            {
                "id": "test_2",
                "name": "Test 2",
                "description": "Test 2 description",
                "test_type": "integration",
                "expected_result": "Success"
            }
        ]
        
        # Run the tests
        with patch('random.random', return_value=0.99):  # Ensure all tests pass
            result = await phase_two._run_component_tests(component, context)
        
        # Verify result
        assert result["total_tests"] == 2
        assert result["passed_tests"] == 2
        assert result["failed_tests"] == 0
        assert result["status"] == "passed"
        assert len(result["test_details"]) == 2
        
        # Verify component methods were called
        component.create_test_execution.assert_called_once()
        component.update_test_state.assert_called_once()

if __name__ == '__main__':
    pytest.main(['-xvs', 'test_phase_two.py'])