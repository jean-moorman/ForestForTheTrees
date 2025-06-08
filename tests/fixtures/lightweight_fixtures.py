"""
Lightweight test fixtures for Water Agent testing.

This module provides minimal dependency injection patterns that avoid
complex initialization chains while still testing real functionality.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, Optional
import uuid
import json

from resources.water_agent.coordinator import (
    MisunderstandingDetector, 
    QuestionResponseHandler, 
    AmbiguityResolutionTracker
)
from resources.water_agent.context_manager import WaterAgentContextManager


@pytest.fixture
def lightweight_misunderstanding_detector():
    """Create a lightweight misunderstanding detector for testing."""
    detector = MisunderstandingDetector(agent_interface=None)
    
    # Mock the agent interface calls but keep the parsing logic
    async def mock_process_with_validation(conversation, system_prompt_info, **kwargs):
        # Return a realistic detection response
        return {
            "misunderstandings": [
                {
                    "id": "test_misunderstanding_1",
                    "description": "Terminology conflict detected",
                    "severity": "MEDIUM",
                    "affected_elements": ["terminology"]
                }
            ],
            "first_agent_questions": [
                {"question": "Can you clarify the terminology used?"}
            ],
            "second_agent_questions": [
                {"question": "What is your understanding of the terminology?"}
            ]
        }
    
    # Create a mock agent interface with just what we need
    mock_interface = MagicMock()
    mock_interface.process_with_validation = AsyncMock(side_effect=mock_process_with_validation)
    detector.agent_interface = mock_interface
    
    return detector


@pytest.fixture
def lightweight_response_handler():
    """Create a lightweight question response handler."""
    handler = QuestionResponseHandler()
    return handler


@pytest.fixture
def lightweight_resolution_tracker():
    """Create a lightweight resolution tracker for testing."""
    tracker = AmbiguityResolutionTracker(agent_interface=None)
    
    # Mock the agent interface calls
    async def mock_process_with_validation(conversation, system_prompt_info, **kwargs):
        return {
            "resolved_misunderstandings": [
                {
                    "id": "test_misunderstanding_1",
                    "resolution_summary": "Terminology clarified through Q&A"
                }
            ],
            "unresolved_misunderstandings": [],
            "new_first_agent_questions": [],
            "new_second_agent_questions": [],
            "require_further_iteration": False
        }
    
    mock_interface = MagicMock()
    mock_interface.process_with_validation = AsyncMock(side_effect=mock_process_with_validation)
    tracker.agent_interface = mock_interface
    
    return tracker


@pytest.fixture
async def lightweight_water_coordinator(lightweight_misunderstanding_detector, 
                                      lightweight_response_handler, 
                                      lightweight_resolution_tracker):
    """Create a lightweight water coordinator with mocked components."""
    from resources.water_agent.coordinator import WaterAgentCoordinator
    
    # Create minimal infrastructure
    state_manager = AsyncMock()
    state_manager.get_state = AsyncMock(return_value=None)
    state_manager.set_state = AsyncMock(return_value=True)
    
    event_bus = AsyncMock()
    event_bus.emit = AsyncMock()
    
    # Create coordinator without complex initialization
    coordinator = WaterAgentCoordinator(
        resource_id="test_coordinator",
        state_manager=state_manager,
        event_bus=event_bus,
        agent_interface=None
    )
    
    # Replace components with lightweight versions
    coordinator.misunderstanding_detector = lightweight_misunderstanding_detector
    coordinator.response_handler = lightweight_response_handler
    coordinator.resolution_tracker = lightweight_resolution_tracker
    
    # Mock context manager to avoid complex initialization
    coordinator.context_manager = AsyncMock()
    coordinator.context_manager.create_coordination_context = AsyncMock()
    coordinator.context_manager.save_coordination_outputs = AsyncMock()
    coordinator.context_manager.update_coordination_iteration = AsyncMock()
    coordinator.context_manager.complete_coordination = AsyncMock()
    coordinator.context_manager.prune_temporary_data = AsyncMock()
    
    # Mock emit event
    coordinator._emit_event = AsyncMock()
    
    return coordinator


class LightweightTestAgent:
    """Lightweight agent for testing coordination."""
    
    def __init__(self, agent_id: str, agent_type: str = "test"):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.__class__.__name__ = f"Lightweight{agent_type.title()}Agent"
        self.clarification_history = []
        
    async def clarify(self, question: str) -> str:
        """Provide contextual clarification responses."""
        self.clarification_history.append(question)
        
        # Provide realistic responses based on question content
        if "terminology" in question.lower():
            return f"Agent {self.agent_id}: I use standard terminology where 'X' means specific technical concept."
        elif "requirement" in question.lower():
            return f"Agent {self.agent_id}: The key requirements are A, B, and C with priority on B."
        elif "clarify" in question.lower():
            return f"Agent {self.agent_id}: Let me clarify - my understanding is {question[:50]}..."
        else:
            return f"Agent {self.agent_id}: Response to '{question[:30]}...'"


@pytest.fixture
def lightweight_agent_pair():
    """Create a pair of lightweight agents for coordination testing."""
    first_agent = LightweightTestAgent("agent_1", "garden_planner")
    second_agent = LightweightTestAgent("agent_2", "earth_agent")
    return first_agent, second_agent


@pytest.fixture
async def lightweight_coordination_scenario():
    """Create a complete lightweight coordination scenario."""
    scenario = {
        "coordination_id": f"test_coord_{uuid.uuid4().hex[:8]}",
        "first_agent_output": """
        Garden Planning Analysis:
        - Size: 1000 square meters
        - Focus: Permaculture food forest
        - Constraints: Native species, $10k budget
        - Timeline: 2-year implementation
        """,
        "second_agent_output": """
        Earth Agent Validation:
        - Area: 1000 sq meters confirmed
        - Approach: Sustainable forest design  
        - Requirements: Indigenous plants, budget considerations
        - Schedule: Phased development over 24 months
        """,
        "expected_coordination": {
            "misunderstandings_detected": 1,
            "iterations_needed": 1,
            "questions_generated": 2,
            "resolution_achieved": True
        }
    }
    return scenario


@pytest.fixture
def mock_json_responses():
    """Provide mock JSON responses for different scenarios."""
    return {
        "no_misunderstandings": {
            "misunderstandings": [],
            "first_agent_questions": [],
            "second_agent_questions": []
        },
        "single_misunderstanding": {
            "misunderstandings": [
                {
                    "id": "terminology_conflict_1",
                    "description": "Inconsistent terminology usage",
                    "severity": "MEDIUM",
                    "affected_elements": ["forest design", "implementation phases"]
                }
            ],
            "first_agent_questions": [
                {"question": "Should we standardize on 'food forest' or 'forest garden' terminology?"}
            ],
            "second_agent_questions": [
                {"question": "What specific implementation phases do you envision?"}
            ]
        },
        "complex_misunderstandings": {
            "misunderstandings": [
                {
                    "id": "scope_mismatch_1",
                    "description": "Scope interpretation differences",
                    "severity": "HIGH",
                    "affected_elements": ["project scope", "timeline"]
                },
                {
                    "id": "requirement_gap_1", 
                    "description": "Missing technical requirements",
                    "severity": "MEDIUM",
                    "affected_elements": ["soil analysis", "drainage planning"]
                }
            ],
            "first_agent_questions": [
                {"question": "Does the scope include soil preparation and drainage work?"},
                {"question": "Should soil testing be completed before design finalization?"}
            ],
            "second_agent_questions": [
                {"question": "What level of detail is expected for soil and drainage analysis?"},
                {"question": "Are there specific soil testing protocols to follow?"}
            ]
        }
    }


@pytest.fixture
def patch_complex_initialization():
    """Patch complex initialization patterns to simplify testing."""
    patches = []
    
    # Patch AgentInterface creation to avoid complex dependency chains
    patches.append(patch('interfaces.agent.interface.AgentInterface'))
    
    # Patch circuit breaker creation to avoid state manager dependencies
    patches.append(patch('resources.monitoring.circuit_breakers.CircuitBreaker'))
    
    # Patch event queue creation to avoid async startup issues
    patches.append(patch('resources.events.EventQueue'))
    
    # Patch metrics initialization to avoid background tasks
    patches.append(patch('interfaces.agent.metrics.InterfaceMetrics'))
    
    # Start all patches
    for p in patches:
        p.start()
    
    yield
    
    # Stop all patches
    for p in patches:
        p.stop()


@pytest.fixture
async def async_test_isolation():
    """Provide isolated async environment for each test."""
    # Suppress common warnings during testing
    import warnings
    warnings.filterwarnings("ignore", message=".*was never awaited.*")
    warnings.filterwarnings("ignore", message=".*Task was destroyed.*")
    
    # Create clean async context
    try:
        yield
    finally:
        # Cleanup any pending tasks
        tasks = [task for task in asyncio.all_tasks() if not task.done()]
        if tasks:
            for task in tasks:
                task.cancel()
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except Exception:
                pass  # Ignore cleanup errors


class MockPromptResponse:
    """Helper for creating mock prompt responses."""
    
    @staticmethod
    def misunderstanding_detection(misunderstandings=None, first_questions=None, second_questions=None):
        """Create a mock misunderstanding detection response."""
        return {
            "misunderstandings": misunderstandings or [],
            "first_agent_questions": first_questions or [],
            "second_agent_questions": second_questions or []
        }
    
    @staticmethod
    def resolution_assessment(resolved=None, unresolved=None, new_first_questions=None, new_second_questions=None):
        """Create a mock resolution assessment response."""
        return {
            "resolved_misunderstandings": resolved or [],
            "unresolved_misunderstandings": unresolved or [],
            "new_first_agent_questions": new_first_questions or [],
            "new_second_agent_questions": new_second_questions or [],
            "require_further_iteration": bool(new_first_questions or new_second_questions)
        }


@pytest.fixture
def mock_prompt_responses():
    """Provide mock prompt response factory."""
    return MockPromptResponse