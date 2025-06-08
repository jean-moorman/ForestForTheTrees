"""
Comprehensive unit tests for Earth Agent core validation logic.

This module tests the Earth Agent's core validation functionality with real
system components and data flows, avoiding mocks that would hide actual issues.
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
from phase_one.agents.earth_agent import EarthAgent
from phase_one.models.enums import DevelopmentState

logger = logging.getLogger(__name__)

class TestEarthAgentValidationCore:
    """Test suite for Earth Agent core validation logic using real components."""

    @pytest_asyncio.fixture
    async def real_resources(self):
        """Create real resource managers for testing."""
        event_queue = EventQueue()
        await event_queue.start()
        
        state_manager = StateManager(event_queue)
        context_manager = AgentContextManager(event_queue)
        cache_manager = CacheManager(event_queue)
        metrics_manager = MetricsManager(event_queue)
        error_handler = ErrorHandler(event_queue)
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
    async def earth_agent(self, real_resources):
        """Create an Earth Agent instance with real resources."""
        agent = EarthAgent(
            agent_id="test_earth_agent",
            **real_resources,
            max_validation_cycles=3
        )
        return agent

    @pytest.fixture
    def valid_garden_planner_output(self):
        """Well-structured Garden Planner output that should pass validation."""
        return {
            "task_analysis": {
                "original_request": "Create a web application that allows users to track their daily habits and goals",
                "interpreted_goal": "Build a comprehensive habit tracking web application with user authentication, habit management, and progress visualization",
                "scope": {
                    "included": [
                        "User registration and authentication system",
                        "Habit creation and management interface",
                        "Daily habit check-in functionality", 
                        "Progress tracking and visualization",
                        "Goal setting and milestone tracking",
                        "Basic reporting and analytics"
                    ],
                    "excluded": [
                        "Mobile application development",
                        "Social sharing features",
                        "Premium subscription tiers",
                        "Third-party integrations"
                    ],
                    "assumptions": [
                        "Web-based deployment on modern browsers",
                        "PostgreSQL database for data persistence",
                        "RESTful API architecture",
                        "Responsive design for mobile browsers"
                    ]
                },
                "technical_requirements": {
                    "languages": ["Python", "JavaScript", "HTML", "CSS"],
                    "frameworks": ["Django", "React", "Bootstrap"],
                    "apis": ["REST API", "JSON API"],
                    "infrastructure": ["AWS EC2", "PostgreSQL", "Redis", "Docker"]
                },
                "constraints": {
                    "technical": [
                        "Must support modern browsers (Chrome, Firefox, Safari, Edge)",
                        "Mobile-responsive design required",
                        "Offline functionality not required initially"
                    ],
                    "business": [
                        "6-month development timeline",
                        "Single developer team initially",
                        "Budget constraints limit third-party services"
                    ],
                    "performance": [
                        "Page load times under 2 seconds",
                        "API response times under 200ms",
                        "Support for 1000 concurrent users"
                    ]
                },
                "considerations": {
                    "security": [
                        "HTTPS encryption required",
                        "JWT token-based authentication",
                        "Input validation and sanitization",
                        "SQL injection prevention"
                    ],
                    "scalability": [
                        "Database optimization for growth",
                        "Caching strategy for frequent queries",
                        "Load balancing for multiple instances"
                    ],
                    "maintainability": [
                        "Comprehensive code documentation",
                        "Automated testing suite",
                        "Version control and deployment pipeline",
                        "Error logging and monitoring"
                    ]
                }
            }
        }

    @pytest.fixture
    def problematic_garden_planner_output(self):
        """Garden Planner output with issues that should be caught by validation."""
        return {
            "task_analysis": {
                "original_request": "Create a web application for tracking habits",
                "interpreted_goal": "Build a habit tracker",  # Too vague
                "scope": {
                    "included": ["stuff", "things"],  # Extremely vague
                    "excluded": [],  # Missing important exclusions
                    "assumptions": ["it will work"]  # Vague assumption
                },
                "technical_requirements": {
                    "languages": ["Python"],
                    "frameworks": [],  # Missing frameworks
                    "apis": ["API"],  # Vague API specification
                    "infrastructure": ["computer"]  # Vague infrastructure
                },
                "constraints": {
                    "technical": ["must be good"],  # Vague constraint
                    "business": [],  # Missing business constraints
                    "performance": ["fast"]  # Vague performance requirement
                },
                "considerations": {
                    "security": ["secure"],  # Vague security consideration
                    "scalability": [],  # Missing scalability considerations
                    "maintainability": ["easy to maintain"]  # Vague maintainability
                }
            }
        }

    @pytest.fixture
    def invalid_structure_output(self):
        """Garden Planner output with structural issues."""
        return {
            "task_analysis": {
                "original_request": "Create a web app",
                "interpreted_goal": "Build an app",
                "scope": {
                    "included": ["features"],
                    # Missing excluded and assumptions
                },
                "technical_requirements": {
                    "languages": ["Python"],
                    # Missing frameworks, apis, infrastructure
                },
                # Missing constraints and considerations entirely
            }
        }

    # Test Input Structure Validation

    @pytest.mark.asyncio
    async def test_input_structure_validation_valid_output(self, earth_agent, valid_garden_planner_output):
        """Test input structure validation with properly structured output."""
        result = earth_agent._validate_input_structure(valid_garden_planner_output)
        assert result is True, "Valid Garden Planner output should pass structure validation"

    @pytest.mark.asyncio
    async def test_input_structure_validation_missing_task_analysis(self, earth_agent):
        """Test input structure validation when task_analysis is missing."""
        invalid_output = {"some_other_field": "value"}
        result = earth_agent._validate_input_structure(invalid_output)
        assert result is False, "Output missing task_analysis should fail validation"

    @pytest.mark.asyncio
    async def test_input_structure_validation_incomplete_structure(self, earth_agent, invalid_structure_output):
        """Test input structure validation with incomplete required fields."""
        result = earth_agent._validate_input_structure(invalid_structure_output)
        assert result is False, "Output with incomplete structure should fail validation"

    @pytest.mark.asyncio
    async def test_input_structure_validation_type_errors(self, earth_agent):
        """Test input structure validation with type errors."""
        # Test with string instead of dict
        result = earth_agent._validate_input_structure("not a dictionary")
        assert result is False, "String input should fail validation"
        
        # Test with None
        result = earth_agent._validate_input_structure(None)
        assert result is False, "None input should fail validation"
        
        # Test with list
        result = earth_agent._validate_input_structure(["not", "a", "dict"])
        assert result is False, "List input should fail validation"

    # Test Validation History Management

    @pytest.mark.asyncio
    async def test_validation_history_tracking(self, earth_agent):
        """Test that validation history is properly tracked."""
        # Start with empty history
        assert len(earth_agent.validation_history) == 0
        
        # Create validation results with different categories and issues
        validation_results = [
            {
                "validation_result": {"validation_category": "APPROVED"},
                "architectural_issues": []
            },
            {
                "validation_result": {"validation_category": "REJECTED"},
                "architectural_issues": [
                    {"severity": "CRITICAL"},
                    {"severity": "HIGH"}
                ]
            },
            {
                "validation_result": {"validation_category": "CORRECTED"},
                "architectural_issues": [
                    {"severity": "MEDIUM"},
                    {"severity": "LOW"},
                    {"severity": "LOW"}
                ]
            }
        ]
        
        # Update history with each result
        for i, result in enumerate(validation_results):
            earth_agent._update_validation_history(result, f"validation_{i}")
        
        # Verify history is tracked correctly
        assert len(earth_agent.validation_history) == 3
        
        # Check first entry (APPROVED)
        entry0 = earth_agent.validation_history[0]
        assert entry0["validation_category"] == "APPROVED"
        assert entry0["issue_count"] == 0
        assert entry0["validation_id"] == "validation_0"
        
        # Check second entry (REJECTED)
        entry1 = earth_agent.validation_history[1]
        assert entry1["validation_category"] == "REJECTED"
        assert entry1["issue_count"] == 2
        assert entry1["issues_by_severity"]["CRITICAL"] == 1
        assert entry1["issues_by_severity"]["HIGH"] == 1
        
        # Check third entry (CORRECTED)
        entry2 = earth_agent.validation_history[2]
        assert entry2["validation_category"] == "CORRECTED"
        assert entry2["issue_count"] == 3
        assert entry2["issues_by_severity"]["MEDIUM"] == 1
        assert entry2["issues_by_severity"]["LOW"] == 2

    @pytest.mark.asyncio
    async def test_validation_history_size_limit(self, earth_agent):
        """Test that validation history maintains size limit of 10 entries."""
        # Add 15 validation results to test the limit
        for i in range(15):
            validation_result = {
                "validation_result": {"validation_category": "APPROVED"},
                "architectural_issues": []
            }
            earth_agent._update_validation_history(validation_result, f"validation_{i}")
        
        # Should only keep the last 10 entries
        assert len(earth_agent.validation_history) == 10
        
        # Verify it kept the most recent entries (5-14)
        assert earth_agent.validation_history[0]["validation_id"] == "validation_5"
        assert earth_agent.validation_history[-1]["validation_id"] == "validation_14"

    # Test Issue Severity Counting

    @pytest.mark.asyncio
    async def test_count_issues_by_severity(self, earth_agent):
        """Test counting of issues by severity level."""
        issues = [
            {"severity": "CRITICAL"},
            {"severity": "CRITICAL"},
            {"severity": "HIGH"},
            {"severity": "HIGH"},
            {"severity": "HIGH"},
            {"severity": "MEDIUM"},
            {"severity": "LOW"},
            {"severity": "UNKNOWN"}  # Should not be counted in standard categories
        ]
        
        counts = earth_agent._count_issues_by_severity(issues)
        
        assert counts["CRITICAL"] == 2
        assert counts["HIGH"] == 3
        assert counts["MEDIUM"] == 1
        assert counts["LOW"] == 1
        # UNKNOWN severity is not counted in our categories

    # Test Validation Cycle Management

    @pytest.mark.asyncio
    async def test_validation_cycle_counter_operations(self, earth_agent):
        """Test validation cycle counter operations."""
        # Initial state should be 0
        initial_cycle = await earth_agent.get_current_validation_cycle()
        assert initial_cycle == 0
        
        # Should not have reached max cycles initially
        has_reached_max = await earth_agent.has_reached_max_cycles()
        assert has_reached_max is False
        
        # Increment cycle and verify
        await earth_agent.increment_validation_cycle()
        cycle1 = await earth_agent.get_current_validation_cycle()
        assert cycle1 == 1
        
        # Increment to max cycles (3)
        await earth_agent.increment_validation_cycle()
        await earth_agent.increment_validation_cycle()
        cycle3 = await earth_agent.get_current_validation_cycle()
        assert cycle3 == 3
        
        # Should now have reached max cycles
        has_reached_max = await earth_agent.has_reached_max_cycles()
        assert has_reached_max is True
        
        # Reset and verify
        await earth_agent.reset_validation_cycle_counter()
        reset_cycle = await earth_agent.get_current_validation_cycle()
        assert reset_cycle == 0
        
        has_reached_max_after_reset = await earth_agent.has_reached_max_cycles()
        assert has_reached_max_after_reset is False

    # Test State Updates Based on Validation Results

    @pytest.mark.asyncio
    async def test_state_update_for_approved_validation(self, earth_agent):
        """Test state update when validation is approved."""
        validation_result = {
            "validation_result": {"validation_category": "APPROVED"}
        }
        
        await earth_agent._update_state_from_validation(validation_result)
        assert earth_agent.development_state == DevelopmentState.COMPLETE

    @pytest.mark.asyncio
    async def test_state_update_for_corrected_validation(self, earth_agent):
        """Test state update when validation is corrected."""
        validation_result = {
            "validation_result": {"validation_category": "CORRECTED"}
        }
        
        await earth_agent._update_state_from_validation(validation_result)
        assert earth_agent.development_state == DevelopmentState.COMPLETE

    @pytest.mark.asyncio
    async def test_state_update_for_rejected_validation(self, earth_agent):
        """Test state update when validation is rejected."""
        validation_result = {
            "validation_result": {"validation_category": "REJECTED"}
        }
        
        await earth_agent._update_state_from_validation(validation_result)
        assert earth_agent.development_state == DevelopmentState.REFINING

    @pytest.mark.asyncio
    async def test_state_update_for_unknown_validation(self, earth_agent):
        """Test state update when validation category is unknown."""
        validation_result = {
            "validation_result": {"validation_category": "UNKNOWN_CATEGORY"}
        }
        
        await earth_agent._update_state_from_validation(validation_result)
        assert earth_agent.development_state == DevelopmentState.ERROR

    # Test Error Response Creation

    @pytest.mark.asyncio
    async def test_error_validation_response_creation(self, earth_agent):
        """Test creation of error validation responses."""
        error_message = "Test validation error"
        
        response = earth_agent._create_error_validation_response(error_message)
        
        # Verify error is included
        assert "error" in response
        assert response["error"] == error_message
        
        # Verify validation result structure
        validation_result = response["validation_result"]
        assert validation_result["validation_category"] == "REJECTED"
        assert validation_result["is_valid"] is False
        assert error_message in validation_result["explanation"]
        
        # Verify architectural issues
        assert len(response["architectural_issues"]) == 1
        issue = response["architectural_issues"][0]
        assert issue["issue_id"] == "system_error"
        assert issue["severity"] == "CRITICAL"
        assert issue["issue_type"] == "technical_misalignment"
        assert error_message in issue["description"]
        
        # Verify metadata structure
        metadata = response["metadata"]
        assert "validation_timestamp" in metadata
        assert metadata["validation_version"] == "1.0"
        assert metadata["original_agent"] == "garden_planner"
        assert "system_error" in metadata["key_decision_factors"]

    # Test Real Validation with Invalid Outputs

    @pytest.mark.asyncio
    async def test_validation_with_invalid_structure_returns_error(self, earth_agent, invalid_structure_output):
        """Test that validation with invalid structure returns proper error."""
        user_request = "Create a web application for habit tracking"
        
        result = await earth_agent.validate_garden_planner_output(
            user_request, 
            invalid_structure_output,
            "test_invalid_structure"
        )
        
        # Should return error response
        assert "error" in result
        assert result["validation_result"]["validation_category"] == "REJECTED"
        assert result["validation_result"]["is_valid"] is False
        assert "Invalid Garden Planner output structure" in result["error"]
        
        # Agent should be in error state
        assert earth_agent.development_state == DevelopmentState.ERROR

    @pytest.mark.asyncio
    async def test_validation_with_malformed_output(self, earth_agent):
        """Test validation with completely malformed output."""
        user_request = "Create a web application"
        malformed_output = {"completely": "wrong", "structure": ["invalid"]}
        
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            malformed_output,
            "test_malformed"
        )
        
        # Should return error response
        assert "error" in result
        assert result["validation_result"]["validation_category"] == "REJECTED"
        assert "Invalid Garden Planner output structure" in result["error"]

    # Test Validation History Retrieval

    @pytest.mark.asyncio
    async def test_get_validation_history(self, earth_agent):
        """Test retrieval of validation history."""
        # Initially empty
        history = await earth_agent.get_validation_history()
        assert history == []
        
        # Add some validation results
        for i in range(3):
            validation_result = {
                "validation_result": {"validation_category": "APPROVED"},
                "architectural_issues": []
            }
            earth_agent._update_validation_history(validation_result, f"validation_{i}")
        
        # Retrieve and verify
        history = await earth_agent.get_validation_history()
        assert len(history) == 3
        assert all("validation_id" in entry for entry in history)
        assert all("timestamp" in entry for entry in history)
        assert all("validation_category" in entry for entry in history)

if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])