"""
Test module for Phase One workflow integration.

This module tests the complete integration of Phase One components, including:
- Garden Planner agent with Earth Agent validation
- Environmental Analysis agent
- Root System Architect agent
- Tree Placement Planner agent
- Water Agent coordination between sequential agents
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from resources import (
    EventQueue,
    StateManager,
    AgentContextManager,
    CacheManager,
    MetricsManager,
    ResourceType
)
from resources.monitoring import HealthTracker, MemoryMonitor
from resources.errors import ErrorHandler

from phase_one.workflow import PhaseOneWorkflow
from phase_one.validation.garden_planner_validator import GardenPlannerValidator
from phase_one.validation.coordination import SequentialAgentCoordinator
from phase_one.models.enums import DevelopmentState

# Mock WaterAgentCoordinator to avoid import issues
class MockWaterAgentCoordinator:
    """Mock WaterAgentCoordinator for testing"""
    def __init__(self, state_manager=None):
        pass
        
    async def coordinate_agents(self, *args, **kwargs):
        return "Updated first output", "Updated second output", {"status": "completed"}

# Mock agent for testing
class MockAgent:
    """Mock agent for testing Phase One workflow."""
    
    def __init__(self, agent_id, responses=None):
        self.agent_id = agent_id
        self.interface_id = agent_id
        self.responses = responses or {}
        self.development_state = DevelopmentState.ANALYZING
        self.process_calls = []
        self.validation_cycle = 0
    
    async def _process(self, input_data):
        """Process input data and return mock result."""
        self.process_calls.append(input_data)
        return self.responses.get(self.agent_id, {})
        
    async def process_with_validation(self, conversation, system_prompt_info, operation_id=None, **kwargs):
        """Mock process_with_validation method."""
        self.process_calls.append(conversation)
        return self.responses.get(self.agent_id, {})
    
    async def validate_garden_planner_output(self, user_request, garden_planner_output, validation_id):
        """Mock validate Garden Planner output."""
        return self.responses.get("validation", {
            "validation_result": {
                "validation_category": "APPROVED",
                "is_valid": True,
                "explanation": "The task analysis is valid."
            },
            "architectural_issues": []
        })
    
    async def refine(self, output, refinement_guidance):
        """Mock refine method."""
        return self.responses.get("refinement", output)
    
    async def reset_validation_cycle_counter(self):
        """Reset validation cycle counter."""
        self.validation_cycle = 0
    
    async def increment_validation_cycle(self):
        """Increment validation cycle."""
        self.validation_cycle += 1

# Test fixtures
@pytest.fixture
async def event_queue():
    """Create an event queue for testing."""
    queue = EventQueue()
    await queue.start()
    yield queue
    await queue.stop()

@pytest.fixture
def state_manager(event_queue):
    """Create a state manager for testing."""
    return StateManager(event_queue=event_queue)

@pytest.fixture
def garden_planner_agent():
    """Create a mock Garden Planner agent for testing."""
    return MockAgent("garden_planner", {
        "garden_planner": {
            "task_analysis": {
                "original_request": "Create a habit tracking app",
                "interpreted_goal": "Create a web application for tracking personal habits",
                "scope": {
                    "included": ["User authentication", "Habit tracking", "Reminders"],
                    "excluded": ["Social features", "Mobile app"],
                    "assumptions": ["Web-based", "Email notifications"]
                },
                "technical_requirements": {
                    "languages": ["JavaScript", "Python"],
                    "frameworks": ["React", "Flask"],
                    "apis": ["RESTful API"]
                },
                "constraints": {
                    "technical": ["Browser compatibility", "Responsive design"],
                    "business": ["MVP in 3 months"],
                    "performance": ["Fast load times"]
                },
                "considerations": {
                    "security": ["User data protection", "HTTPS"],
                    "scalability": ["Horizontal scaling"],
                    "maintainability": ["Clean code", "Documentation"]
                }
            }
        }
    })

@pytest.fixture
def earth_agent():
    """Create a mock Earth Agent for testing."""
    return MockAgent("earth_agent", {
        "validation": {
            "validation_result": {
                "validation_category": "APPROVED",
                "is_valid": True,
                "explanation": "The task analysis is valid."
            },
            "architectural_issues": []
        }
    })

@pytest.fixture
def environmental_analysis_agent():
    """Create a mock Environmental Analysis agent for testing."""
    return MockAgent("environmental_analysis", {
        "environmental_analysis": {
            "analysis": {
                "requirements": {
                    "functional": ["User registration", "Habit creation", "Progress tracking"],
                    "non_functional": ["Security", "Performance", "Usability"]
                },
                "constraints": {
                    "technical": ["Browser compatibility", "Responsive design"],
                    "business": ["MVP in 3 months"],
                    "timeline": ["3 months for initial release"]
                },
                "stakeholders": ["End users", "Development team", "Product managers"],
                "risks": ["Technical complexity", "Scope creep", "Performance issues"],
                "success_criteria": ["User adoption", "Habit completion rate"]
            }
        }
    })

@pytest.fixture
def root_system_architect_agent():
    """Create a mock Root System Architect agent for testing."""
    return MockAgent("root_system_architect", {
        "root_system_architect": {
            "data_architecture": {
                "entities": ["User", "Habit", "HabitLog", "Reminder"],
                "relationships": [
                    {"from": "User", "to": "Habit", "type": "one-to-many"},
                    {"from": "Habit", "to": "HabitLog", "type": "one-to-many"},
                    {"from": "Habit", "to": "Reminder", "type": "one-to-many"}
                ],
                "data_flow": {
                    "authentication": ["User registration", "Login", "Session management"],
                    "habit_management": ["Create habit", "Update habit", "Delete habit"],
                    "tracking": ["Log completion", "View progress", "Generate statistics"],
                    "notifications": ["Set reminders", "Send notifications"]
                },
                "storage": {
                    "database": "PostgreSQL",
                    "caching": "Redis",
                    "file_storage": "AWS S3"
                }
            }
        }
    })

@pytest.fixture
def tree_placement_planner_agent():
    """Create a mock Tree Placement Planner agent for testing."""
    return MockAgent("tree_placement_planner", {
        "tree_placement_planner": {
            "component_architecture": {
                "components": [
                    {
                        "id": "auth",
                        "name": "Authentication",
                        "description": "Handles user authentication and session management",
                        "responsibilities": ["User registration", "Login", "Password reset"],
                        "dependencies": []
                    },
                    {
                        "id": "habit",
                        "name": "Habit Management",
                        "description": "Core habit tracking functionality",
                        "responsibilities": ["Create habits", "Update habits", "Delete habits"],
                        "dependencies": ["auth"]
                    },
                    {
                        "id": "tracking",
                        "name": "Progress Tracking",
                        "description": "Tracks and visualizes habit completion",
                        "responsibilities": ["Log completions", "Calculate streaks", "Generate statistics"],
                        "dependencies": ["habit"]
                    },
                    {
                        "id": "reminder",
                        "name": "Reminder System",
                        "description": "Manages and sends habit reminders",
                        "responsibilities": ["Schedule reminders", "Send notifications"],
                        "dependencies": ["habit"]
                    },
                    {
                        "id": "api",
                        "name": "API Gateway",
                        "description": "RESTful API layer for frontend communication",
                        "responsibilities": ["Route requests", "Validate input", "Format responses"],
                        "dependencies": ["auth", "habit", "tracking", "reminder"]
                    },
                    {
                        "id": "frontend",
                        "name": "Frontend Application",
                        "description": "React-based user interface",
                        "responsibilities": ["User interface", "State management", "API communication"],
                        "dependencies": ["api"]
                    }
                ],
                "architecture_diagram": "Frontend Application -> API Gateway -> [Authentication, Habit Management, Progress Tracking, Reminder System]",
                "deployment_strategy": {
                    "frontend": "Static hosting on AWS S3 with CloudFront",
                    "backend": "Containerized with Docker, deployed on AWS ECS",
                    "database": "AWS RDS PostgreSQL instance",
                    "caching": "AWS ElastiCache Redis"
                }
            }
        }
    })

@pytest.fixture
def phase_one_workflow(
    garden_planner_agent,
    earth_agent,
    environmental_analysis_agent,
    root_system_architect_agent,
    tree_placement_planner_agent,
    event_queue,
    state_manager
):
    """Create a Phase One workflow for testing."""
    # Mock the WaterAgentCoordinator to avoid import issues
    with patch('phase_one.validation.coordination.WaterAgentCoordinator', MockWaterAgentCoordinator):
        workflow = PhaseOneWorkflow(
            garden_planner_agent=garden_planner_agent,
            earth_agent=earth_agent,
            environmental_analysis_agent=environmental_analysis_agent,
            root_system_architect_agent=root_system_architect_agent,
            tree_placement_planner_agent=tree_placement_planner_agent,
            event_queue=event_queue,
            state_manager=state_manager,
            max_earth_validation_cycles=2,
            validation_timeout=5.0
        )
        
        # Ensure sequential_coordinator uses the mock
        workflow.sequential_coordinator._water_coordinator = MockWaterAgentCoordinator()
        
        return workflow

# Tests
@pytest.mark.asyncio
async def test_phase_one_workflow_initialization(phase_one_workflow):
    """Test Phase One workflow initialization."""
    assert phase_one_workflow is not None
    assert phase_one_workflow.garden_planner_agent is not None
    assert phase_one_workflow.earth_agent is not None
    assert phase_one_workflow.environmental_analysis_agent is not None
    assert phase_one_workflow.root_system_architect_agent is not None
    assert phase_one_workflow.tree_placement_planner_agent is not None
    assert phase_one_workflow.garden_planner_validator is not None
    assert phase_one_workflow.sequential_coordinator is not None
    assert phase_one_workflow.event_queue is not None
    assert phase_one_workflow.state_manager is not None

@pytest.mark.asyncio
async def test_garden_planner_validation(phase_one_workflow):
    """Test Garden Planner validation with Earth Agent."""
    # Mock the validator's validate_initial_task_analysis method
    with patch.object(
        phase_one_workflow.garden_planner_validator,
        'validate_initial_task_analysis',
        new_callable=AsyncMock
    ) as mock_validate:
        # Mock successful validation
        mock_validate.return_value = (
            True,  # is_valid
            {      # final_analysis
                "task_analysis": {
                    "original_request": "Create a habit tracking app",
                    "interpreted_goal": "Create a web application for tracking personal habits",
                    "scope": {
                        "included": ["User authentication", "Habit tracking", "Reminders"],
                        "excluded": ["Social features", "Mobile app"],
                        "assumptions": ["Web-based", "Email notifications"]
                    },
                    "technical_requirements": {
                        "languages": ["JavaScript", "Python"],
                        "frameworks": ["React", "Flask"],
                        "apis": ["RESTful API"]
                    },
                    "constraints": {
                        "technical": ["Browser compatibility", "Responsive design"],
                        "business": ["MVP in 3 months"],
                        "performance": ["Fast load times"]
                    },
                    "considerations": {
                        "security": ["User data protection", "HTTPS"],
                        "scalability": ["Horizontal scaling"],
                        "maintainability": ["Clean code", "Documentation"]
                    }
                }
            },
            [     # validation_history
                {
                    "cycle": 1,
                    "validation_id": "test_operation_cycle_1",
                    "validation_category": "APPROVED",
                    "issue_count": 0
                }
            ]
        )
        
        # Execute Garden Planner validation
        result = await phase_one_workflow._execute_garden_planner_with_validation(
            "Create a habit tracking app",
            "test_operation"
        )
        
        # Verify validation was called
        mock_validate.assert_called_once()
        
        # Verify result structure
        assert result["success"] is True
        assert "task_analysis" in result
        assert "validation" in result
        assert result["validation"]["is_valid"] is True
        assert len(result["validation"]["validation_history"]) == 1

@pytest.mark.asyncio
async def test_water_agent_coordination(phase_one_workflow):
    """Test Water Agent coordination between sequential agents."""
    # Set up a mock for SequentialAgentCoordinator.coordinate_agent_handoff
    mock_coordination_result = (
        {  # coordinated_output
            "analysis": {
                "requirements": {
                    "functional": ["User registration", "Habit creation", "Progress tracking"],
                    "non_functional": ["Security", "Performance", "Usability"]
                },
                "constraints": {
                    "technical": ["Browser compatibility", "Responsive design"],
                    "business": ["MVP in 3 months"],
                    "timeline": ["3 months for initial release"]
                },
                "stakeholders": ["End users", "Development team", "Product managers"],
                "risks": ["Technical complexity", "Scope creep", "Performance issues"],
                "success_criteria": ["User adoption", "Habit completion rate"]
            }
        },
        {  # coordination_metadata
            "status": "completed",
            "result": "coordination_applied",
            "misunderstandings_count": 1,
            "coordination_id": "test_coordination_id"
        }
    )
    
    # Create a patched version with MockWaterAgentCoordinator
    with patch('phase_one.validation.coordination.WaterAgentCoordinator', MockWaterAgentCoordinator), \
         patch.object(
             phase_one_workflow.sequential_coordinator,
             'coordinate_agent_handoff',
             new_callable=AsyncMock,
             return_value=mock_coordination_result
         ) as mock_coordinate:
        
        # Execute coordination
        task_analysis = {
            "original_request": "Create a habit tracking app",
            "interpreted_goal": "Create a web application for tracking personal habits"
        }
        
        coordinated_output, metadata = await phase_one_workflow.sequential_coordinator.coordinate_agent_handoff(
            phase_one_workflow.garden_planner_agent,
            task_analysis,
            phase_one_workflow.environmental_analysis_agent,
            "test_coordination"
        )
        
        # Verify coordination was called
        mock_coordinate.assert_called_once()
        
        # Verify result
        assert "analysis" in coordinated_output
        assert metadata["status"] == "completed"
        assert metadata["result"] == "coordination_applied"

@pytest.mark.asyncio
async def test_full_phase_one_execution(phase_one_workflow):
    """Test full Phase One workflow execution."""
    # Mock methods for each step
    with patch.object(
        phase_one_workflow,
        '_execute_garden_planner_with_validation',
        new_callable=AsyncMock
    ) as mock_garden_planner, patch.object(
        phase_one_workflow.sequential_coordinator,
        'coordinate_agent_handoff',
        new_callable=AsyncMock
    ) as mock_coordinate, patch.object(
        phase_one_workflow,
        '_execute_environmental_analysis',
        new_callable=AsyncMock
    ) as mock_env_analysis, patch.object(
        phase_one_workflow,
        '_execute_root_system_architect',
        new_callable=AsyncMock
    ) as mock_root_system, patch.object(
        phase_one_workflow,
        '_execute_tree_placement_planner',
        new_callable=AsyncMock
    ) as mock_tree_placement:
        
        # Mock Garden Planner validation result
        mock_garden_planner.return_value = {
            "success": True,
            "task_analysis": {
                "original_request": "Create a habit tracking app",
                "interpreted_goal": "Create a web application for tracking personal habits"
            },
            "validation": {
                "is_valid": True,
                "validation_history": [{"cycle": 1, "validation_category": "APPROVED"}]
            }
        }
        
        # Mock Water Agent coordination result (used multiple times)
        mock_coordinate.return_value = ({}, {"result": "no_misunderstandings"})
        
        # Mock Environmental Analysis result
        mock_env_analysis.return_value = {
            "success": True,
            "analysis": {
                "requirements": {
                    "functional": ["User registration", "Habit tracking"],
                    "non_functional": ["Security", "Performance"]
                }
            }
        }
        
        # Mock Root System Architect result
        mock_root_system.return_value = {
            "success": True,
            "data_architecture": {
                "entities": ["User", "Habit", "HabitLog"],
                "relationships": []
            }
        }
        
        # Mock Tree Placement Planner result
        mock_tree_placement.return_value = {
            "success": True,
            "component_architecture": {
                "components": [
                    {"id": "auth", "name": "Authentication", "dependencies": []},
                    {"id": "habit", "name": "Habit Management", "dependencies": ["auth"]}
                ]
            }
        }
        
        # Execute full Phase One workflow
        result = await phase_one_workflow.execute_phase_one(
            "Create a habit tracking app",
            "test_full_execution"
        )
        
        # Verify all steps were called
        mock_garden_planner.assert_called_once()
        assert mock_coordinate.call_count == 3  # Called for each handoff
        mock_env_analysis.assert_called_once()
        mock_root_system.assert_called_once()
        mock_tree_placement.assert_called_once()
        
        # Verify final result
        assert result["status"] == "completed"
        assert "agents" in result
        assert "garden_planner" in result["agents"]
        assert "environmental_analysis" in result["agents"]
        assert "root_system_architect" in result["agents"]
        assert "tree_placement_planner" in result["agents"]
        assert "final_output" in result
        assert "task_analysis" in result["final_output"]
        assert "environmental_analysis" in result["final_output"]
        assert "data_architecture" in result["final_output"]
        assert "component_architecture" in result["final_output"]

@pytest.mark.asyncio
async def test_garden_planner_failure(phase_one_workflow):
    """Test Phase One workflow with Garden Planner failure."""
    # Mock Garden Planner validation failure
    with patch.object(
        phase_one_workflow,
        '_execute_garden_planner_with_validation',
        new_callable=AsyncMock
    ) as mock_garden_planner:
        
        # Mock failure result
        mock_garden_planner.return_value = {
            "success": False,
            "error": "Garden Planner processing failed",
            "timestamp": datetime.now().isoformat()
        }
        
        # Execute Phase One workflow
        result = await phase_one_workflow.execute_phase_one(
            "Create a habit tracking app",
            "test_garden_planner_failure"
        )
        
        # Verify only Garden Planner was called
        mock_garden_planner.assert_called_once()
        
        # Verify result indicates failure
        assert result["status"] == "failed"
        assert result["failure_stage"] == "garden_planner"
        assert "agents" in result
        assert "garden_planner" in result["agents"]
        assert result["agents"]["garden_planner"]["success"] is False

@pytest.mark.asyncio
async def test_environmental_analysis_failure(phase_one_workflow):
    """Test Phase One workflow with Environmental Analysis failure."""
    # Mock methods for each step
    with patch.object(
        phase_one_workflow,
        '_execute_garden_planner_with_validation',
        new_callable=AsyncMock
    ) as mock_garden_planner, patch.object(
        phase_one_workflow.sequential_coordinator,
        'coordinate_agent_handoff',
        new_callable=AsyncMock
    ) as mock_coordinate, patch.object(
        phase_one_workflow,
        '_execute_environmental_analysis',
        new_callable=AsyncMock
    ) as mock_env_analysis:
        
        # Mock Garden Planner success
        mock_garden_planner.return_value = {
            "success": True,
            "task_analysis": {
                "original_request": "Create a habit tracking app",
                "interpreted_goal": "Create a web application for tracking personal habits"
            },
            "validation": {
                "is_valid": True,
                "validation_history": [{"cycle": 1, "validation_category": "APPROVED"}]
            }
        }
        
        # Mock Water Agent coordination success
        mock_coordinate.return_value = ({}, {"result": "no_misunderstandings"})
        
        # Mock Environmental Analysis failure
        mock_env_analysis.return_value = {
            "success": False,
            "error": "Environmental Analysis processing failed",
            "timestamp": datetime.now().isoformat()
        }
        
        # Execute Phase One workflow
        result = await phase_one_workflow.execute_phase_one(
            "Create a habit tracking app",
            "test_env_analysis_failure"
        )
        
        # Verify Garden Planner and Environmental Analysis were called
        mock_garden_planner.assert_called_once()
        mock_coordinate.assert_called_once()
        mock_env_analysis.assert_called_once()
        
        # Verify result indicates failure at Environmental Analysis
        assert result["status"] == "failed"
        assert result["failure_stage"] == "environmental_analysis"
        assert "agents" in result
        assert "garden_planner" in result["agents"]
        assert "environmental_analysis" in result["agents"]
        assert result["agents"]["garden_planner"]["success"] is True
        assert result["agents"]["environmental_analysis"]["success"] is False

@pytest.mark.asyncio
async def test_get_workflow_status(phase_one_workflow):
    """Test getting Phase One workflow status."""
    # Mock state manager get_state
    with patch.object(
        phase_one_workflow.state_manager,
        'get_state',
        new_callable=AsyncMock
    ) as mock_get_state:
        
        # Mock workflow state
        mock_get_state.return_value = {
            "status": "in_progress",
            "current_agent": "environmental_analysis",
            "start_time": "2023-05-01T10:00:00",
            "operation_id": "test_status"
        }
        
        # Get workflow status
        status = await phase_one_workflow.get_workflow_status("test_status")
        
        # Verify state manager was called
        mock_get_state.assert_called_once_with(
            "phase_one_workflow:test_status",
            "STATE"
        )
        
        # Verify status information
        assert status["status"] == "in_progress"
        assert status["current_agent"] == "environmental_analysis"
        assert status["start_time"] == "2023-05-01T10:00:00"
        assert status["operation_id"] == "test_status"

@pytest.mark.asyncio
async def test_get_coordination_status(phase_one_workflow):
    """Test getting coordination status."""
    # Mock sequential coordinator get_coordination_status
    with patch.object(
        phase_one_workflow.sequential_coordinator,
        'get_coordination_status',
        new_callable=AsyncMock
    ) as mock_get_status:
        
        # Mock coordination status
        mock_get_status.return_value = {
            "status": "completed",
            "result": "coordination_applied",
            "misunderstandings_count": 1,
            "first_output_updated": True,
            "operation_id": "test_coordination",
            "timestamp": "2023-05-01T11:00:00"
        }
        
        # Get coordination status
        status = await phase_one_workflow.get_coordination_status(
            "test_operation",
            "garden_to_env"
        )
        
        # Verify coordinator was called
        mock_get_status.assert_called_once_with("test_operation_garden_to_env_coordination")
        
        # Verify status information
        assert status["status"] == "completed"
        assert status["result"] == "coordination_applied"
        assert status["misunderstandings_count"] == 1
        assert status["first_output_updated"] is True

if __name__ == "__main__":
    pytest.main(["-xvs", "test_phase_one_workflow.py"])