"""
Tests for the Water Agent implementation.

These tests verify that the Water Agent correctly coordinates guideline propagation
between agents in the dependency chain, with rich contextual information using LLM.
"""

import asyncio
import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from resources.water_agent import (
    WaterAgent, 
    PropagationContext, 
    PropagationRequest, 
    PropagationResult,
    PropagationPhase
)
from resources import (
    ResourceType, 
    ResourceEventTypes, 
    EventQueue, 
    StateManager, 
    AgentContextManager, 
    CacheManager, 
    MetricsManager,
    ErrorHandler,
    MemoryMonitor
)

@pytest.fixture
def event_queue():
    """Create a mock event queue for testing."""
    eq = MagicMock(spec=EventQueue)
    eq.emit = AsyncMock()
    eq.subscribe = MagicMock()
    eq.start = AsyncMock()
    eq.running = True
    return eq

@pytest.fixture
def state_manager(event_queue):
    """Create a mock state manager for testing."""
    sm = MagicMock(spec=StateManager)
    sm.set_state = AsyncMock()
    sm.get_state = AsyncMock(return_value={})
    return sm

@pytest.fixture
def context_manager(event_queue):
    """Create a mock context manager for testing."""
    cm = MagicMock(spec=AgentContextManager)
    cm.get_context = AsyncMock(return_value={})
    return cm

@pytest.fixture
def cache_manager(event_queue):
    """Create a mock cache manager for testing."""
    cm = MagicMock(spec=CacheManager)
    return cm

@pytest.fixture
def metrics_manager(event_queue):
    """Create a mock metrics manager for testing."""
    mm = MagicMock(spec=MetricsManager)
    mm.record_metric = AsyncMock()
    return mm

@pytest.fixture
def error_handler(event_queue):
    """Create a mock error handler for testing."""
    eh = MagicMock(spec=ErrorHandler)
    return eh

@pytest.fixture
def memory_monitor(event_queue):
    """Create a mock memory monitor for testing."""
    mm = MagicMock(spec=MemoryMonitor)
    return mm

@pytest.fixture
def earth_agent():
    """Create a mock Earth agent for testing."""
    ea = MagicMock()
    ea.validate_guideline_update = AsyncMock()
    return ea

@pytest.fixture
def water_agent(
    event_queue, 
    state_manager, 
    context_manager,
    cache_manager,
    metrics_manager,
    error_handler,
    memory_monitor,
    earth_agent
):
    """Create a Water agent for testing."""
    agent = WaterAgent(
        agent_id="test_water_agent",
        event_queue=event_queue,
        state_manager=state_manager,
        context_manager=context_manager,
        cache_manager=cache_manager,
        metrics_manager=metrics_manager,
        error_handler=error_handler,
        memory_monitor=memory_monitor,
        earth_agent=earth_agent
    )
    
    # Mock core methods to isolate testing
    agent._get_direct_dependencies = AsyncMock(return_value=["agent1", "agent2"])
    agent._get_transitive_dependencies = AsyncMock(return_value=["agent3"])
    agent._filter_affected_by_relevance = AsyncMock(return_value=["agent1", "agent2", "agent3"])
    agent._extract_update_components = AsyncMock(return_value=[{"type": "interface_change"}])
    agent._get_agent_guideline = AsyncMock(return_value={"version": "1.0"})
    agent._analyze_interface_impacts = AsyncMock(return_value=[{"impact": "significant"}])
    agent._analyze_behavioral_impacts = AsyncMock(return_value=[{"impact": "moderate"}])
    agent._determine_required_adaptations = AsyncMock(return_value=[{"action": "update_interface"}])
    agent._request_agent_readiness = AsyncMock(return_value={"ready": True})
    agent._get_agent_interface = AsyncMock()
    agent._apply_update_to_agent = AsyncMock(return_value={"success": True})
    agent._verify_agent_update = AsyncMock(return_value={"verified": True})
    agent._sort_by_dependency_order = AsyncMock(side_effect=lambda x, y=None: x)
    agent.calculate_impact_score = AsyncMock(return_value=2.5)
    
    # Mock LLM methods
    agent.process_with_validation = AsyncMock()
    agent._analyze_propagation = AsyncMock(return_value={
        "propagation_analysis": {
            "affected_agents": [
                {"agent_id": "agent1", "dependency_type": "direct", "impact_level": "HIGH", "propagation_priority": 1},
                {"agent_id": "agent2", "dependency_type": "direct", "impact_level": "MEDIUM", "propagation_priority": 2},
                {"agent_id": "agent3", "dependency_type": "transitive", "impact_level": "LOW", "propagation_priority": 3}
            ],
            "propagation_order": ["agent1", "agent2", "agent3"],
            "update_classification": {
                "primary_change_type": "interface_update",
                "scope": "CROSS_COMPONENT",
                "cascading_likelihood": "MEDIUM",
                "boundary_crossing": True
            },
            "impact_assessment": {
                "overall_score": 3.5,
                "impact_areas": [
                    {"area": "interfaces", "score": 4, "description": "Significant interface changes"}
                ],
                "high_risk_elements": []
            }
        }
    })
    agent._generate_rich_context = AsyncMock(return_value={
        "update_context": {
            "origin_context": {
                "origin_agent": "origin_agent",
                "change_rationale": "Improve API consistency",
                "architectural_principles": ["Consistency", "Separation of concerns"],
                "change_history": "Initial implementation"
            },
            "impact_context": {
                "direct_impacts": [{"area": "API", "description": "Changes to method signatures", "severity": "MEDIUM"}],
                "interface_changes": [],
                "behavioral_changes": [],
                "ripple_effects": []
            }
        }
    })
    agent._generate_adaptation_guidance = AsyncMock(return_value={
        "adaptation_guidance": {
            "integration_overview": {
                "update_summary": "API signature changes",
                "integration_approach": "Incremental",
                "estimated_complexity": "MEDIUM",
                "compatibility_assessment": "Compatible with minor changes"
            }
        }
    })
    agent._reflect_and_revise = AsyncMock(side_effect=lambda x, y, z, w: x)
    
    return agent

class TestLLMWaterAgent:
    """Tests for the LLM-powered Water Agent implementation."""
    
    @pytest.mark.asyncio
    async def test_llm_analyze_propagation(self, water_agent):
        """Test LLM-based propagation analysis."""
        # Reset to use the real method instead of the mock
        water_agent._analyze_propagation = AsyncMock(wraps=WaterAgent._analyze_propagation.__get__(water_agent, WaterAgent))
        
        # Set up the process_with_validation mock with the desired response
        water_agent.process_with_validation.return_value = {
            "propagation_analysis": {
                "affected_agents": [
                    {"agent_id": "agent1", "dependency_type": "direct", "impact_level": "HIGH", "propagation_priority": 1}
                ],
                "propagation_order": ["agent1"],
                "update_classification": {
                    "primary_change_type": "interface_update",
                    "scope": "LOCAL",
                    "cascading_likelihood": "LOW",
                    "boundary_crossing": False
                },
                "impact_assessment": {
                    "overall_score": 2.0,
                    "impact_areas": [],
                    "high_risk_elements": []
                }
            }
        }
        
        # Test analysis
        result = await water_agent._analyze_propagation(
            "origin_agent",
            ["agent1"],
            {"update": "test"},
            "test_operation"
        )
        
        # Verify LLM was called with proper arguments
        water_agent.process_with_validation.assert_called_once()
        args, kwargs = water_agent.process_with_validation.call_args
        
        # Check that the conversation contains the key elements
        conversation = kwargs.get("conversation", "")
        analysis_context = json.loads(conversation)
        assert analysis_context["origin_agent_id"] == "origin_agent"
        assert analysis_context["potentially_affected_agents"] == ["agent1"]
        assert analysis_context["validated_update"] == {"update": "test"}
        
        # Check system prompt used
        assert kwargs.get("system_prompt_info") == ("FFTT_system_prompts/core_agents/water_agent/propagation_analysis_prompt", "propagation_analysis_prompt")
        
        # Check result
        assert "propagation_analysis" in result
        assert result["propagation_analysis"]["affected_agents"][0]["agent_id"] == "agent1"
    
    @pytest.mark.asyncio
    async def test_generate_agent_specific_context(self, water_agent):
        """Test rich context generation for specific agents."""
        # Reset to use the real method for context generation
        water_agent._generate_rich_context = AsyncMock(wraps=WaterAgent._generate_rich_context.__get__(water_agent, WaterAgent))
        
        # Set up the process_with_validation mock with the desired response
        water_agent.process_with_validation.return_value = {
            "update_context": {
                "origin_context": {
                    "origin_agent": "origin_agent",
                    "change_rationale": "Improve component structure",
                    "architectural_principles": ["Modularity"],
                    "change_history": "Initial implementation"
                },
                "impact_context": {
                    "direct_impacts": [
                        {"area": "Interfaces", "description": "API changes", "severity": "MEDIUM"}
                    ],
                    "interface_changes": [],
                    "behavioral_changes": [],
                    "ripple_effects": []
                }
            },
            "target_specific_guidance": {
                "agent_role": "Testing agent",
                "agent_responsibilities": ["Testing interfaces"],
                "tailored_recommendations": ["Update test cases"],
                "priority_adaptation_areas": ["API tests"]
            }
        }
        
        # Test function
        context = await water_agent.generate_agent_specific_context(
            "origin_agent",
            "target_agent",
            {"test": "update"},
            {"validation_result": "approved"},
            "test_operation"
        )
        
        # Assertions
        assert isinstance(context, PropagationContext)
        assert context.origin_agent_id == "origin_agent"
        assert context.target_agent_id == "target_agent"
        assert context.rich_context is not None
        assert "update_context" in context.rich_context
        assert context.rich_context["update_context"]["origin_context"]["change_rationale"] == "Improve component structure"
        
        # Check LLM method calls
        water_agent.process_with_validation.assert_called_once()
        args, kwargs = water_agent.process_with_validation.call_args
        assert kwargs.get("system_prompt_info") == ("FFTT_system_prompts/core_agents/water_agent/context_generation_prompt", "context_generation_prompt")
    
    @pytest.mark.asyncio
    async def test_generate_adaptation_guidance(self, water_agent):
        """Test adaptation guidance generation."""
        # Reset to use the real method
        water_agent._generate_adaptation_guidance = AsyncMock(wraps=WaterAgent._generate_adaptation_guidance.__get__(water_agent, WaterAgent))
        
        # Set up the process_with_validation mock with the desired response
        water_agent.process_with_validation.return_value = {
            "adaptation_guidance": {
                "integration_overview": {
                    "update_summary": "API changes",
                    "integration_approach": "Incremental",
                    "estimated_complexity": "MEDIUM",
                    "compatibility_assessment": "Compatible with minor changes"
                },
                "implementation_plan": {
                    "phases": [
                        {
                            "phase_name": "Update interfaces",
                            "description": "Update interface definitions",
                            "tasks": [],
                            "success_criteria": []
                        }
                    ],
                    "critical_path": [],
                    "recommended_sequence": "Sequential"
                }
            }
        }
        
        # Create test context
        prop_context = PropagationContext(
            origin_agent_id="origin_agent",
            target_agent_id="target_agent",
            update_id="test_update",
            validation_result={},
            specific_changes=[],
            interface_impacts=[],
            behavioral_impacts=[],
            required_adaptations=[]
        )
        
        # Test function
        guidance = await water_agent._generate_adaptation_guidance(
            "origin_agent",
            "target_agent",
            prop_context,
            {"target": "guideline"},
            "test_operation"
        )
        
        # Assertions
        assert "adaptation_guidance" in guidance
        assert guidance["adaptation_guidance"]["integration_overview"]["update_summary"] == "API changes"
        
        # Check LLM method calls
        water_agent.process_with_validation.assert_called_once()
        args, kwargs = water_agent.process_with_validation.call_args
        assert kwargs.get("system_prompt_info") == ("FFTT_system_prompts/core_agents/water_agent/adaptation_guidance_prompt", "adaptation_guidance_prompt")
    
    @pytest.mark.asyncio
    async def test_reflection_and_revision(self, water_agent):
        """Test the reflection and revision process."""
        # Reset to use the real method
        water_agent._reflect_and_revise = AsyncMock(wraps=WaterAgent._reflect_and_revise.__get__(water_agent, WaterAgent))
        
        # Set up sequential mock responses for process_with_validation
        # First for reflection, then for revision
        water_agent.process_with_validation.side_effect = [
            # Reflection result
            {
                "reflection_results": {
                    "overall_assessment": {
                        "decision_quality_score": 6,  # Lower score to trigger revision
                        "critical_improvements": [
                            {
                                "priority": 8,
                                "target_area": "impact_assessment",
                                "issue_description": "Missing details about API changes",
                                "improvement_recommendation": "Add specific API changes",
                                "expected_impact": "Better understanding of changes"
                            }
                        ]
                    }
                }
            },
            # Revision result
            {
                "revision_results": {
                    "revised_validation": {
                        "propagation_analysis": {
                            "affected_agents": [{"agent_id": "agent1"}],
                            "impact_assessment": {"overall_score": 3.5, "impact_areas": [{"area": "API", "description": "Updated API impact description"}]}
                        }
                    },
                    "revision_summary": {
                        "confidence": {"score": 9},
                        "decision_changes": {"significant_content_changes": True}
                    }
                }
            }
        ]
        
        # Initial result to improve
        initial_result = {
            "propagation_analysis": {
                "affected_agents": [{"agent_id": "agent1"}],
                "impact_assessment": {"overall_score": 3.0}
            }
        }
        
        # Test reflection and revision
        revised_result = await water_agent._reflect_and_revise(
            initial_result,
            PropagationPhase.ANALYSIS,
            {"test": "context"},
            "test_operation"
        )
        
        # Verify process_with_validation was called twice with correct prompts
        assert water_agent.process_with_validation.call_count == 2
        
        # Get args from first call (reflection)
        reflect_args = water_agent.process_with_validation.call_args_list[0][1]
        assert reflect_args["system_prompt_info"] == ("FFTT_system_prompts/core_agents/water_agent/reflection_prompt", "reflection_prompt")
        assert reflect_args["current_phase"] == "analysis_reflection"
        
        # Get args from second call (revision)
        revise_args = water_agent.process_with_validation.call_args_list[1][1]
        assert revise_args["system_prompt_info"] == ("FFTT_system_prompts/core_agents/water_agent/revision_prompt", "revision_prompt")
        assert revise_args["current_phase"] == "analysis_revision"
        
        # Check the revision counts were tracked
        assert water_agent.revision_attempts["test_operation"] == 1
        
        # Verify we got the revised result
        assert revised_result["propagation_analysis"]["impact_assessment"]["overall_score"] == 3.5
        assert revised_result["propagation_analysis"]["impact_assessment"]["impact_areas"][0]["area"] == "API"
    
    @pytest.mark.asyncio
    async def test_coordinate_propagation_with_llm(self, water_agent):
        """Test the end-to-end propagation coordination with LLM components."""
        # Mock the response data
        water_agent.map_affected_agents.return_value = ["agent1", "agent2"]
        
        # Define a more complex sample update
        sample_update = {
            "ordered_components": [
                {
                    "name": "api",
                    "description": "API component"
                },
                {
                    "name": "core",
                    "dependencies": {
                        "required": ["api"]
                    }
                }
            ]
        }
        
        # Test function
        result = await water_agent.coordinate_propagation(
            "origin_agent",
            sample_update,
            {"validation_category": "APPROVED"}
        )
        
        # Assertions
        assert isinstance(result, PropagationResult)
        assert result.success is True  # Assuming no failures in the mocked setup
        assert "agent1" in result.propagation_map
        assert "agent2" in result.propagation_map
        assert result.metrics["affected_count"] == 2
        
        # Verify all LLM methods were called
        assert water_agent._analyze_propagation.call_count == 1
        assert water_agent._generate_rich_context.call_count >= 1
        assert water_agent._generate_adaptation_guidance.call_count >= 1
        
        # Verify the apply_update and verification was called for each agent
        assert water_agent._apply_update_to_agent.call_count == 2
        
    @pytest.mark.asyncio
    async def test_validation_event_handling(self, water_agent):
        """Test handling of Earth validation events."""
        # Prepare a mock event
        event_data = {
            "validation_result": {"validation_category": "APPROVED"},
            "operation_id": "test_op",
            "agent_id": "test_agent",
            "updated_guideline": {"test": "guideline"},
            "auto_propagate": True
        }
        
        # Patch coordinate_propagation to track call
        water_agent.coordinate_propagation = AsyncMock()
        
        # Trigger event handler
        await water_agent._handle_validation_complete(event_data)
        
        # Verify propagation was triggered with correct parameters
        water_agent.coordinate_propagation.assert_called_once_with(
            origin_agent_id="test_agent",
            validated_update={"test": "guideline"},
            validation_result={"validation_category": "APPROVED"}
        )
        
    @pytest.mark.asyncio
    async def test_calculate_impact_score_with_llm(self, water_agent):
        """Test impact score calculation using LLM analysis."""
        # Reset to use the real method
        water_agent.calculate_impact_score = AsyncMock(wraps=WaterAgent.calculate_impact_score.__get__(water_agent, WaterAgent))
        
        # Create propagation analysis with impact score
        prop_analysis = {
            "propagation_analysis": {
                "impact_assessment": {
                    "overall_score": 4.5,
                    "impact_areas": []
                }
            }
        }
        
        # Test function using the LLM-provided score
        score = await water_agent.calculate_impact_score(
            {"test": "update"},
            ["agent1", "agent2"],
            prop_analysis
        )
        
        # Verify we got the LLM score
        assert score == 4.5
        
        # Test fallback to heuristic calculation when no LLM analysis
        score = await water_agent.calculate_impact_score(
            {"test": "update"},
            ["agent1", "agent2"],
            None
        )
        
        # Verify we got a score from the heuristic calculation
        assert score > 0