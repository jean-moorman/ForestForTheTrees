"""
Unit tests for Phase Zero Analysis Agents

Tests the specialized Phase Zero agents responsible for quality assurance analysis:
- SunAgent (task description analysis)
- ShadeAgent (conflict analysis)
- SoilAgent (requirement analysis) 
- MicrobialAgent (issue analysis)
- MycelialAgent (data flow analysis)
- WormAgent (gap analysis)
- BirdAgent (structural analysis)
- TreeAgent (structural gap analysis)
- PollinatorAgent (optimization analysis)

Each agent performs dual-perspective analysis with proper circuit breaker protection,
memory monitoring, and health tracking.
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from phase_zero.agents.description_analysis import SunAgent, ShadeAgent
from phase_zero.agents.requirement_analysis import SoilAgent, MicrobialAgent
from phase_zero.agents.data_flow import MycelialAgent, WormAgent
from phase_zero.agents.structural import BirdAgent, TreeAgent
from phase_zero.agents.optimization import PollinatorAgent
from phase_zero.base import BaseAnalysisAgent, AnalysisState
from phase_zero.prompt_loader import PromptType
from resources.monitoring import CircuitOpenError, MemoryMonitor
from resources import (
    EventQueue, StateManager, AgentContextManager, CacheManager,
    MetricsManager, ErrorHandler, HealthTracker
)


@pytest.fixture
def mock_resources():
    """Create mock resource managers for testing."""
    return {
        'event_queue': AsyncMock(spec=EventQueue),
        'state_manager': AsyncMock(spec=StateManager),
        'context_manager': AsyncMock(spec=AgentContextManager),
        'cache_manager': AsyncMock(spec=CacheManager),
        'metrics_manager': AsyncMock(spec=MetricsManager),
        'error_handler': AsyncMock(spec=ErrorHandler),
        'memory_monitor': AsyncMock(spec=MemoryMonitor),
        'health_tracker': AsyncMock(spec=HealthTracker)
    }


@pytest.fixture
def sample_phase_one_output():
    """Sample Phase One output for analysis."""
    return {
        "task_analysis": {
            "project_title": "E-commerce Platform",
            "primary_objective": "Build scalable online shopping platform",
            "requirements": [
                "User authentication and registration",
                "Product catalog management",
                "Shopping cart functionality",
                "Order processing and payment"
            ]
        },
        "environmental_analysis": {
            "runtime_requirements": {
                "performance_targets": {"concurrent_users": 1000}
            }
        },
        "data_architecture": {
            "data_entities": ["users", "products", "orders"],
            "data_flows": ["user_registration", "product_catalog"]
        },
        "component_architecture": {
            "components": [
                {"id": "auth_service", "name": "Authentication Service"},
                {"id": "catalog_service", "name": "Product Catalog Service"}
            ]
        },
        "status": "completed"
    }


@pytest.fixture
def sample_analysis_input():
    """Sample analysis input for Phase Zero agents."""
    return {
        "guidelines": {
            "task_description": "Build e-commerce platform",
            "requirements": ["authentication", "catalog", "orders"],
            "constraints": ["scalability", "security"]
        },
        "phase_one_output": {
            "task_analysis": {"requirements": ["auth", "catalog"]},
            "technical_specs": {"database": "PostgreSQL"}
        },
        "context": {
            "project_type": "web_application",
            "timeline": "12 weeks",
            "team_size": "5 developers"
        }
    }


class TestBaseAnalysisAgent:
    """Test base analysis agent functionality."""
    
    async def test_base_agent_initialization(self, mock_resources):
        """Test base analysis agent initialization."""
        agent = BaseAnalysisAgent(
            agent_id="test_base_agent",
            event_queue=mock_resources['event_queue'],
            state_manager=mock_resources['state_manager'],
            context_manager=mock_resources['context_manager'],
            cache_manager=mock_resources['cache_manager'],
            metrics_manager=mock_resources['metrics_manager'],
            error_handler=mock_resources['error_handler'],
            health_tracker=mock_resources['health_tracker'],
            memory_monitor=mock_resources['memory_monitor']
        )
        
        # Verify initialization
        assert agent.interface_id == "agent:test_base_agent"
        assert agent._analysis_state == AnalysisState.IDLE
        assert "processing" in agent._circuit_breakers
        
        # Verify health tracking integration
        assert agent._health_tracker == mock_resources['health_tracker']
        assert agent._memory_monitor == mock_resources['memory_monitor']
    
    async def test_circuit_breaker_creation(self, mock_resources):
        """Test circuit breaker creation and retrieval."""
        agent = BaseAnalysisAgent(
            agent_id="test_circuit_agent",
            event_queue=mock_resources['event_queue'],
            state_manager=mock_resources['state_manager'],
            context_manager=mock_resources['context_manager'],
            cache_manager=mock_resources['cache_manager'],
            metrics_manager=mock_resources['metrics_manager'],
            error_handler=mock_resources['error_handler']
        )
        
        # Test getting existing circuit breaker
        processing_cb = agent.get_circuit_breaker("processing")
        assert processing_cb is not None
        
        # Test creating new circuit breaker
        analysis_cb = agent.get_circuit_breaker("analysis")
        assert analysis_cb is not None
        assert "analysis" in agent._circuit_breakers


class TestSunAgent:
    """Test SunAgent (task description analysis)."""
    
    async def test_sun_agent_initialization(self, mock_resources):
        """Test SunAgent initialization."""
        agent = SunAgent(
            event_queue=mock_resources['event_queue'],
            state_manager=mock_resources['state_manager'],
            context_manager=mock_resources['context_manager'],
            cache_manager=mock_resources['cache_manager'],
            metrics_manager=mock_resources['metrics_manager'],
            error_handler=mock_resources['error_handler'],
            health_tracker=mock_resources['health_tracker'],
            memory_monitor=mock_resources['memory_monitor']
        )
        
        # Verify initialization
        assert agent.interface_id == "agent:sun"
        assert agent._current_prompt_type == PromptType.PHASE_ONE_INITIAL
        assert isinstance(agent, BaseAnalysisAgent)
    
    async def test_sun_agent_output_schema(self, mock_resources):
        """Test SunAgent output schema definition."""
        agent = SunAgent(
            event_queue=mock_resources['event_queue'],
            state_manager=mock_resources['state_manager'],
            context_manager=mock_resources['context_manager'],
            cache_manager=mock_resources['cache_manager'],
            metrics_manager=mock_resources['metrics_manager'],
            error_handler=mock_resources['error_handler']
        )
        
        schema = agent.get_output_schema()
        
        # Verify schema structure for dual-perspective analysis
        assert "dual_perspective_analysis" in schema
        assert "issue_analysis" in schema["dual_perspective_analysis"]
        assert "gap_analysis" in schema["dual_perspective_analysis"]
        assert "synthesis" in schema["dual_perspective_analysis"]
        
        # Verify issue analysis categories
        issue_analysis = schema["dual_perspective_analysis"]["issue_analysis"]
        assert "scope_issues" in issue_analysis
        assert "clarity_issues" in issue_analysis
        assert "alignment_issues" in issue_analysis
        assert "feasibility_issues" in issue_analysis
        assert "complexity_issues" in issue_analysis
        
        # Verify gap analysis categories
        gap_analysis = schema["dual_perspective_analysis"]["gap_analysis"]
        assert "scope_gaps" in gap_analysis
        assert "definition_gaps" in gap_analysis
        assert "alignment_gaps" in gap_analysis
        assert "constraint_gaps" in gap_analysis
        assert "complexity_gaps" in gap_analysis
    
    @patch('phase_zero.prompt_loader.prompt_loader.get_prompt')
    async def test_sun_agent_processing_with_system_prompt(self, mock_get_prompt, mock_resources):
        """Test SunAgent processing with system prompt integration."""
        agent = SunAgent(
            event_queue=mock_resources['event_queue'],
            state_manager=mock_resources['state_manager'],
            context_manager=mock_resources['context_manager'],
            cache_manager=mock_resources['cache_manager'],
            metrics_manager=mock_resources['metrics_manager'],
            error_handler=mock_resources['error_handler']
        )
        
        # Mock system prompt
        mock_get_prompt.return_value = "System prompt for SunAgent task description analysis"
        
        # Mock the base process_with_validation
        expected_result = {
            "dual_perspective_analysis": {
                "issue_analysis": {
                    "scope_issues": [{"issue": "Unclear project boundaries"}],
                    "clarity_issues": [{"issue": "Ambiguous requirements"}]
                },
                "gap_analysis": {
                    "scope_gaps": [{"gap": "Missing user story details"}]
                },
                "synthesis": {
                    "key_observations": ["Project scope needs refinement"],
                    "prioritized_recommendations": [{"priority": "high", "action": "clarify scope"}]
                }
            }
        }
        
        with patch.object(BaseAnalysisAgent, 'process_with_validation', new=AsyncMock(return_value=expected_result)):
            result = await agent.process_with_validation(
                "Analyze this task description",
                agent.get_output_schema()
            )
        
        # Verify system prompt was requested
        mock_get_prompt.assert_called_once()
        
        # Verify result structure
        assert result["dual_perspective_analysis"]["issue_analysis"]["scope_issues"][0]["issue"] == "Unclear project boundaries"


class TestShadeAgent:
    """Test ShadeAgent (conflict analysis)."""
    
    async def test_shade_agent_initialization(self, mock_resources):
        """Test ShadeAgent initialization."""
        agent = ShadeAgent(
            event_queue=mock_resources['event_queue'],
            state_manager=mock_resources['state_manager'],
            context_manager=mock_resources['context_manager'],
            cache_manager=mock_resources['cache_manager'],
            metrics_manager=mock_resources['metrics_manager'],
            error_handler=mock_resources['error_handler']
        )
        
        # Verify initialization
        assert agent.interface_id == "agent:shade"
        assert agent._current_prompt_type == PromptType.PHASE_ONE_INITIAL
    
    async def test_shade_agent_output_schema(self, mock_resources):
        """Test ShadeAgent output schema for conflict analysis."""
        agent = ShadeAgent(
            event_queue=mock_resources['event_queue'],
            state_manager=mock_resources['state_manager'],
            context_manager=mock_resources['context_manager'],
            cache_manager=mock_resources['cache_manager'],
            metrics_manager=mock_resources['metrics_manager'],
            error_handler=mock_resources['error_handler']
        )
        
        schema = agent.get_output_schema()
        
        # Verify schema structure for dual-perspective conflicts
        assert "dual_perspective_conflicts" in schema
        assert "task_vs_guidelines" in schema["dual_perspective_conflicts"]
        assert "guidelines_vs_task" in schema["dual_perspective_conflicts"]
        assert "synthesis" in schema["dual_perspective_conflicts"]
        
        # Verify conflict categories in both directions
        task_vs_guidelines = schema["dual_perspective_conflicts"]["task_vs_guidelines"]
        guidelines_vs_task = schema["dual_perspective_conflicts"]["guidelines_vs_task"]
        
        for conflict_direction in [task_vs_guidelines, guidelines_vs_task]:
            assert "scope_conflicts" in conflict_direction
            assert "stakeholder_conflicts" in conflict_direction
            assert "context_conflicts" in conflict_direction
            assert "criteria_conflicts" in conflict_direction


class TestSoilAgent:
    """Test SoilAgent (requirement analysis)."""
    
    async def test_soil_agent_initialization(self, mock_resources):
        """Test SoilAgent initialization."""
        # Import here to avoid circular imports during test collection
        from phase_zero.agents.requirement_analysis import SoilAgent
        
        agent = SoilAgent(
            event_queue=mock_resources['event_queue'],
            state_manager=mock_resources['state_manager'],
            context_manager=mock_resources['context_manager'],
            cache_manager=mock_resources['cache_manager'],
            metrics_manager=mock_resources['metrics_manager'],
            error_handler=mock_resources['error_handler']
        )
        
        # Verify initialization
        assert agent.interface_id == "agent:soil"
        assert isinstance(agent, BaseAnalysisAgent)


class TestMicrobialAgent:
    """Test MicrobialAgent (issue analysis)."""
    
    async def test_microbial_agent_initialization(self, mock_resources):
        """Test MicrobialAgent initialization."""
        from phase_zero.agents.requirement_analysis import MicrobialAgent
        
        agent = MicrobialAgent(
            event_queue=mock_resources['event_queue'],
            state_manager=mock_resources['state_manager'],
            context_manager=mock_resources['context_manager'],
            cache_manager=mock_resources['cache_manager'],
            metrics_manager=mock_resources['metrics_manager'],
            error_handler=mock_resources['error_handler']
        )
        
        # Verify initialization
        assert agent.interface_id == "agent:microbial"
        assert isinstance(agent, BaseAnalysisAgent)


class TestMycelialAgent:
    """Test MycelialAgent (data flow analysis)."""
    
    async def test_mycelial_agent_initialization(self, mock_resources):
        """Test MycelialAgent initialization."""
        from phase_zero.agents.data_flow import MycelialAgent
        
        agent = MycelialAgent(
            event_queue=mock_resources['event_queue'],
            state_manager=mock_resources['state_manager'],
            context_manager=mock_resources['context_manager'],
            cache_manager=mock_resources['cache_manager'],
            metrics_manager=mock_resources['metrics_manager'],
            error_handler=mock_resources['error_handler']
        )
        
        # Verify initialization
        assert agent.interface_id == "agent:mycelial"
        assert isinstance(agent, BaseAnalysisAgent)


class TestWormAgent:
    """Test WormAgent (gap analysis)."""
    
    async def test_worm_agent_initialization(self, mock_resources):
        """Test WormAgent initialization."""
        from phase_zero.agents.data_flow import WormAgent
        
        agent = WormAgent(
            event_queue=mock_resources['event_queue'],
            state_manager=mock_resources['state_manager'],
            context_manager=mock_resources['context_manager'],
            cache_manager=mock_resources['cache_manager'],
            metrics_manager=mock_resources['metrics_manager'],
            error_handler=mock_resources['error_handler']
        )
        
        # Verify initialization
        assert agent.interface_id == "agent:worm"
        assert isinstance(agent, BaseAnalysisAgent)


class TestBirdAgent:
    """Test BirdAgent (structural analysis)."""
    
    async def test_bird_agent_initialization(self, mock_resources):
        """Test BirdAgent initialization."""
        from phase_zero.agents.structural import BirdAgent
        
        agent = BirdAgent(
            event_queue=mock_resources['event_queue'],
            state_manager=mock_resources['state_manager'],
            context_manager=mock_resources['context_manager'],
            cache_manager=mock_resources['cache_manager'],
            metrics_manager=mock_resources['metrics_manager'],
            error_handler=mock_resources['error_handler']
        )
        
        # Verify initialization
        assert agent.interface_id == "agent:bird"
        assert isinstance(agent, BaseAnalysisAgent)


class TestTreeAgent:
    """Test TreeAgent (structural gap analysis)."""
    
    async def test_tree_agent_initialization(self, mock_resources):
        """Test TreeAgent initialization."""
        from phase_zero.agents.structural import TreeAgent
        
        agent = TreeAgent(
            event_queue=mock_resources['event_queue'],
            state_manager=mock_resources['state_manager'],
            context_manager=mock_resources['context_manager'],
            cache_manager=mock_resources['cache_manager'],
            metrics_manager=mock_resources['metrics_manager'],
            error_handler=mock_resources['error_handler']
        )
        
        # Verify initialization
        assert agent.interface_id == "agent:tree"
        assert isinstance(agent, BaseAnalysisAgent)


class TestPollinatorAgent:
    """Test PollinatorAgent (optimization analysis)."""
    
    async def test_pollinator_agent_initialization(self, mock_resources):
        """Test PollinatorAgent initialization."""
        from phase_zero.agents.optimization import PollinatorAgent
        
        agent = PollinatorAgent(
            event_queue=mock_resources['event_queue'],
            state_manager=mock_resources['state_manager'],
            context_manager=mock_resources['context_manager'],
            cache_manager=mock_resources['cache_manager'],
            metrics_manager=mock_resources['metrics_manager'],
            error_handler=mock_resources['error_handler']
        )
        
        # Verify initialization
        assert agent.interface_id == "agent:pollinator"
        assert isinstance(agent, BaseAnalysisAgent)


class TestPhaseZeroAgentIntegration:
    """Test integration scenarios for Phase Zero agents."""
    
    async def test_agent_circuit_breaker_behavior(self, mock_resources):
        """Test circuit breaker behavior across different agents."""
        agent = SunAgent(
            event_queue=mock_resources['event_queue'],
            state_manager=mock_resources['state_manager'],
            context_manager=mock_resources['context_manager'],
            cache_manager=mock_resources['cache_manager'],
            metrics_manager=mock_resources['metrics_manager'],
            error_handler=mock_resources['error_handler']
        )
        
        # Mock circuit breaker to be open
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(side_effect=CircuitOpenError("Circuit open"))
        agent._circuit_breakers["processing"] = mock_circuit
        
        # Test that circuit breaker protection works
        with patch.object(agent, 'get_circuit_breaker', return_value=mock_circuit):
            # The agent should handle circuit breaker failures gracefully
            # This test verifies the infrastructure is in place
            circuit = agent.get_circuit_breaker("processing")
            assert circuit == mock_circuit
    
    async def test_agent_health_reporting(self, mock_resources):
        """Test health reporting across different agent types."""
        agents = [
            SunAgent(**mock_resources),
            ShadeAgent(**mock_resources)
        ]
        
        for agent in agents:
            # Each agent should have health tracking capability
            assert hasattr(agent, '_health_tracker')
            assert hasattr(agent, '_report_agent_health')
            
            # Verify health reporting method exists and is callable
            assert callable(agent._report_agent_health)
    
    async def test_agent_memory_monitoring(self, mock_resources):
        """Test memory monitoring integration across agents."""
        agent = SunAgent(
            event_queue=mock_resources['event_queue'],
            state_manager=mock_resources['state_manager'],
            context_manager=mock_resources['context_manager'],
            cache_manager=mock_resources['cache_manager'],
            metrics_manager=mock_resources['metrics_manager'],
            error_handler=mock_resources['error_handler'],
            memory_monitor=mock_resources['memory_monitor']
        )
        
        # Verify memory monitor integration
        assert agent._memory_monitor == mock_resources['memory_monitor']
        
        # Test that memory monitoring infrastructure is available
        assert hasattr(agent, '_memory_monitor')
    
    async def test_agent_state_transitions(self, mock_resources):
        """Test analysis state transitions."""
        agent = SunAgent(
            event_queue=mock_resources['event_queue'],
            state_manager=mock_resources['state_manager'],
            context_manager=mock_resources['context_manager'],
            cache_manager=mock_resources['cache_manager'],
            metrics_manager=mock_resources['metrics_manager'],
            error_handler=mock_resources['error_handler']
        )
        
        # Initial state should be IDLE
        assert agent._analysis_state == AnalysisState.IDLE
        
        # Test state transition capability
        agent._analysis_state = AnalysisState.ANALYZING
        assert agent._analysis_state == AnalysisState.ANALYZING
        
        agent._analysis_state = AnalysisState.COMPLETE
        assert agent._analysis_state == AnalysisState.COMPLETE


class TestPhaseZeroAnalysisWorkflow:
    """Test realistic Phase Zero analysis workflows."""
    
    @patch('phase_zero.prompt_loader.prompt_loader.get_prompt')
    async def test_dual_perspective_analysis_workflow(self, mock_get_prompt, mock_resources, sample_analysis_input):
        """Test dual-perspective analysis workflow with Sun and Shade agents."""
        # Mock system prompts
        mock_get_prompt.return_value = "System prompt for analysis"
        
        # Create agents
        sun_agent = SunAgent(**mock_resources)
        shade_agent = ShadeAgent(**mock_resources)
        
        # Mock analysis results
        sun_result = {
            "dual_perspective_analysis": {
                "issue_analysis": {
                    "scope_issues": [{"issue": "Scope too broad", "severity": "medium"}],
                    "clarity_issues": [{"issue": "Requirements unclear", "severity": "high"}]
                },
                "gap_analysis": {
                    "scope_gaps": [{"gap": "Missing user stories", "priority": "high"}],
                    "definition_gaps": [{"gap": "Unclear success criteria", "priority": "medium"}]
                },
                "synthesis": {
                    "key_observations": ["Project needs better scoping", "Requirements need clarification"],
                    "prioritized_recommendations": [
                        {"priority": "high", "action": "Define user stories"},
                        {"priority": "medium", "action": "Clarify success criteria"}
                    ]
                }
            }
        }
        
        shade_result = {
            "dual_perspective_conflicts": {
                "task_vs_guidelines": {
                    "scope_conflicts": [{"conflict": "Task scope exceeds timeline", "severity": "high"}],
                    "stakeholder_conflicts": [{"conflict": "User needs vs business goals", "severity": "medium"}]
                },
                "guidelines_vs_task": {
                    "scope_conflicts": [{"conflict": "Guidelines suggest smaller scope", "severity": "medium"}],
                    "context_conflicts": [{"conflict": "Technology constraints", "severity": "low"}]
                },
                "synthesis": {
                    "key_patterns": ["Scope-timeline mismatch", "Stakeholder alignment issues"],
                    "bidirectional_issues": ["Resource allocation conflicts"],
                    "prioritized_resolutions": [
                        {"priority": "high", "resolution": "Adjust scope or timeline"},
                        {"priority": "medium", "resolution": "Align stakeholders"}
                    ]
                }
            }
        }
        
        # Mock the base process_with_validation for each agent
        with patch.object(BaseAnalysisAgent, 'process_with_validation', new=AsyncMock()) as mock_process:
            # Configure different returns for different agents
            mock_process.side_effect = [sun_result, shade_result]
            
            # Execute analysis workflow
            sun_analysis = await sun_agent.process_with_validation(
                json.dumps(sample_analysis_input),
                sun_agent.get_output_schema()
            )
            
            shade_analysis = await shade_agent.process_with_validation(
                json.dumps(sample_analysis_input),
                shade_agent.get_output_schema()
            )
        
        # Verify results
        assert sun_analysis["dual_perspective_analysis"]["issue_analysis"]["scope_issues"][0]["issue"] == "Scope too broad"
        assert shade_analysis["dual_perspective_conflicts"]["task_vs_guidelines"]["scope_conflicts"][0]["conflict"] == "Task scope exceeds timeline"
        
        # Verify both agents were called
        assert mock_process.call_count == 2
    
    async def test_phase_zero_error_handling(self, mock_resources):
        """Test error handling across Phase Zero agents."""
        agent = SunAgent(
            event_queue=mock_resources['event_queue'],
            state_manager=mock_resources['state_manager'],
            context_manager=mock_resources['context_manager'],
            cache_manager=mock_resources['cache_manager'],
            metrics_manager=mock_resources['metrics_manager'],
            error_handler=mock_resources['error_handler']
        )
        
        # Test error state transition
        agent._analysis_state = AnalysisState.ERROR
        assert agent._analysis_state == AnalysisState.ERROR
        
        # Verify error handler integration
        assert agent._error_handler == mock_resources['error_handler']
    
    async def test_phase_zero_resource_management(self, mock_resources):
        """Test resource management integration across agents."""
        agents = [
            SunAgent(**mock_resources),
            ShadeAgent(**mock_resources)
        ]
        
        for agent in agents:
            # Verify all required resource managers are integrated
            assert agent._event_queue == mock_resources['event_queue']
            assert agent._state_manager == mock_resources['state_manager']
            assert agent._context_manager == mock_resources['context_manager']
            assert agent._cache_manager == mock_resources['cache_manager']
            assert agent._metrics_manager == mock_resources['metrics_manager']
            assert agent._error_handler == mock_resources['error_handler']
            
            # Verify optional monitoring components
            if 'health_tracker' in mock_resources:
                assert agent._health_tracker == mock_resources['health_tracker']
            if 'memory_monitor' in mock_resources:
                assert agent._memory_monitor == mock_resources['memory_monitor']