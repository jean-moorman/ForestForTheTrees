"""
Unit tests for Environmental Analysis Agent

Tests the core Phase One agent responsible for analyzing requirements
and environmental constraints with proper circuit breaker protection,
memory monitoring, and health tracking.
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from phase_one.agents.environmental_analysis import EnvironmentalAnalysisAgent
from phase_one.models.enums import DevelopmentState
from phase_one.models.refinement import AgentPromptConfig
from phase_one.monitoring.circuit_breakers import CircuitBreakerDefinition
from resources.monitoring import CircuitOpenError, MemoryThresholds
from resources import (
    EventQueue, StateManager, AgentContextManager, CacheManager,
    MetricsManager, ErrorHandler, MemoryMonitor, HealthTracker
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
def sample_garden_planner_output():
    """Sample garden planner output for testing."""
    return {
        "task_analysis": {
            "project_title": "E-commerce Platform",
            "primary_objective": "Build scalable online shopping platform",
            "target_users": ["customers", "administrators", "vendors"],
            "requirements": [
                "User authentication and registration",
                "Product catalog management",
                "Shopping cart functionality",
                "Order processing and payment",
                "Inventory management",
                "Admin dashboard"
            ]
        },
        "scope_definition": {
            "core_features": ["catalog", "cart", "orders", "payments"],
            "optional_features": ["reviews", "recommendations"],
            "technical_constraints": ["RESTful API", "PostgreSQL database"],
            "performance_requirements": ["1000 concurrent users", "< 200ms response time"]
        },
        "status": "completed",
        "timestamp": datetime.now().isoformat()
    }


@pytest.fixture
def sample_minimal_garden_planner_output():
    """Minimal garden planner output for edge case testing."""
    return {
        "task_analysis": {
            "project_title": "Simple App",
            "requirements": ["Basic functionality"]
        },
        "status": "completed"
    }


@pytest.fixture
async def environmental_analysis_agent(mock_resources):
    """Create an Environmental Analysis Agent for testing."""
    agent = EnvironmentalAnalysisAgent(
        agent_id="env_analysis_test",
        event_queue=mock_resources['event_queue'],
        state_manager=mock_resources['state_manager'],
        context_manager=mock_resources['context_manager'],
        cache_manager=mock_resources['cache_manager'],
        metrics_manager=mock_resources['metrics_manager'],
        error_handler=mock_resources['error_handler'],
        memory_monitor=mock_resources['memory_monitor'],
        health_tracker=mock_resources['health_tracker']
    )
    
    # Mock the initialization
    agent._initialized = True
    
    return agent


class TestEnvironmentalAnalysisAgentInitialization:
    """Test Environmental Analysis Agent initialization."""
    
    @pytest.mark.asyncio
    async def test_initialization_success(self, mock_resources):
        """Test successful agent initialization."""
        agent = EnvironmentalAnalysisAgent(
            agent_id="test_env_agent",
            event_queue=mock_resources['event_queue'],
            state_manager=mock_resources['state_manager'],
            context_manager=mock_resources['context_manager'],
            cache_manager=mock_resources['cache_manager'],
            metrics_manager=mock_resources['metrics_manager'],
            error_handler=mock_resources['error_handler'],
            memory_monitor=mock_resources['memory_monitor'],
            health_tracker=mock_resources['health_tracker']
        )
        
        # Verify initialization
        assert agent.interface_id == "agent:test_env_agent"
        assert agent.development_state == DevelopmentState.INITIALIZING
        assert isinstance(agent._prompt_config, AgentPromptConfig)
        
        # Verify prompt configuration
        assert agent._prompt_config.system_prompt_base_path == "FFTT_system_prompts/phase_one/garden_environmental_analysis_agent"
        assert agent._prompt_config.reflection_prompt_name == "core_requirements_reflection_prompt"
        assert agent._prompt_config.refinement_prompt_name == "core_requirements_refinement_prompt"
        assert agent._prompt_config.initial_prompt_name == "initial_core_requirements_prompt"
        
        # Verify circuit breakers
        assert "analysis" in agent._circuit_breakers
        assert "processing" in agent._circuit_breakers  # Default from base class
        
        # Verify circuit breaker configuration
        analysis_cb = agent.get_circuit_breaker("analysis")
        assert analysis_cb is not None
    
    async def test_initialization_memory_monitor_registration(self, mock_resources):
        """Test memory monitor registration during initialization."""
        agent = EnvironmentalAnalysisAgent(
            agent_id="test_memory_agent",
            event_queue=mock_resources['event_queue'],
            state_manager=mock_resources['state_manager'],
            context_manager=mock_resources['context_manager'],
            cache_manager=mock_resources['cache_manager'],
            metrics_manager=mock_resources['metrics_manager'],
            error_handler=mock_resources['error_handler'],
            memory_monitor=mock_resources['memory_monitor'],
            health_tracker=mock_resources['health_tracker']
        )
        
        # Verify memory monitor registration was called
        mock_resources['memory_monitor'].register_component.assert_called_once()
        
        # Verify registration parameters
        call_args = mock_resources['memory_monitor'].register_component.call_args
        assert call_args[0][0] == "agent_test_memory_agent"
        
        # Verify memory thresholds
        thresholds = call_args[0][1]
        assert isinstance(thresholds, MemoryThresholds)
        assert thresholds.per_resource_max_mb == 70  # Environment data threshold
        assert thresholds.warning_percent == 0.5
        assert thresholds.critical_percent == 0.8
    
    async def test_initialization_without_health_tracker(self, mock_resources):
        """Test initialization when health tracker is not provided."""
        mock_resources['health_tracker'] = None
        
        agent = EnvironmentalAnalysisAgent(
            agent_id="test_no_health",
            event_queue=mock_resources['event_queue'],
            state_manager=mock_resources['state_manager'],
            context_manager=mock_resources['context_manager'],
            cache_manager=mock_resources['cache_manager'],
            metrics_manager=mock_resources['metrics_manager'],
            error_handler=mock_resources['error_handler'],
            memory_monitor=mock_resources['memory_monitor'],
            health_tracker=mock_resources['health_tracker']
        )
        
        # Should initialize successfully without health tracker
        assert agent._health_tracker is None
        assert agent.interface_id == "agent:test_no_health"


class TestEnvironmentalAnalysisProcessing:
    """Test core environmental analysis processing functionality."""
    
    async def test_successful_analysis(self, environmental_analysis_agent, sample_garden_planner_output):
        """Test successful environmental analysis processing."""
        # Mock successful analysis result
        analysis_result = {
            "environmental_analysis": {
                "runtime_requirements": {
                    "target_platforms": ["web", "mobile"],
                    "browser_support": ["Chrome", "Firefox", "Safari"],
                    "performance_targets": {
                        "page_load_time": "< 2 seconds",
                        "api_response_time": "< 200ms",
                        "concurrent_users": 1000
                    }
                },
                "deployment_requirements": {
                    "hosting_environment": "cloud",
                    "database_requirements": ["PostgreSQL", "Redis"],
                    "third_party_services": ["payment_gateway", "email_service"],
                    "scalability_requirements": ["horizontal_scaling", "load_balancing"]
                },
                "technical_constraints": {
                    "framework_preferences": ["React", "Node.js"],
                    "security_requirements": ["HTTPS", "authentication", "data_encryption"],
                    "compliance_requirements": ["GDPR", "PCI_DSS"]
                }
            },
            "validation_status": {
                "passed": True,
                "requirements_coverage": "complete",
                "constraint_analysis": "comprehensive"
            },
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        
        # Mock the circuit breaker and process_with_validation
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=analysis_result)
        environmental_analysis_agent._circuit_breakers["analysis"] = mock_circuit
        
        environmental_analysis_agent.process_with_validation = AsyncMock(return_value=analysis_result)
        environmental_analysis_agent.standard_reflect = AsyncMock(return_value={
            "reflection_results": {
                "validation_status": {"passed": True}
            }
        })
        
        # Execute processing
        result = await environmental_analysis_agent._process(sample_garden_planner_output)
        
        # Verify result
        assert result is not None
        assert result["environmental_analysis"]["runtime_requirements"]["concurrent_users"] == 1000
        assert result["validation_status"]["passed"] is True
        assert environmental_analysis_agent.development_state == DevelopmentState.COMPLETE
        
        # Verify circuit breaker was called
        mock_circuit.execute.assert_called_once()
        
        # Verify health tracking
        environmental_analysis_agent._report_agent_health.assert_called()
    
    async def test_analysis_validation_failure(self, environmental_analysis_agent, sample_garden_planner_output):
        """Test handling of validation failure during analysis."""
        # Mock analysis result with validation failure
        analysis_result = {
            "environmental_analysis": {
                "runtime_requirements": {"incomplete": True}
            },
            "validation_status": {
                "passed": False,
                "issues": ["Missing performance requirements"]
            },
            "status": "needs_refinement"
        }
        
        reflection_result = {
            "reflection_results": {
                "validation_status": {"passed": False},
                "issues": ["Analysis incomplete", "Missing critical requirements"]
            },
            "refinement_needed": True
        }
        
        # Mock the circuit breaker and methods
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=analysis_result)
        environmental_analysis_agent._circuit_breakers["analysis"] = mock_circuit
        
        environmental_analysis_agent.process_with_validation = AsyncMock(return_value=analysis_result)
        environmental_analysis_agent.standard_reflect = AsyncMock(return_value=reflection_result)
        
        # Execute processing
        result = await environmental_analysis_agent._process(sample_garden_planner_output)
        
        # Verify result indicates refinement needed
        assert result == reflection_result
        assert environmental_analysis_agent.development_state == DevelopmentState.REFINING
        
        # Verify health status was updated to degraded
        health_calls = [call for call in environmental_analysis_agent._report_agent_health.call_args_list 
                       if call[1].get('custom_status') == 'DEGRADED']
        assert len(health_calls) > 0
    
    async def test_circuit_breaker_open(self, environmental_analysis_agent, sample_garden_planner_output):
        """Test handling when circuit breaker is open."""
        # Mock circuit breaker to raise CircuitOpenError
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(side_effect=CircuitOpenError("Circuit open"))
        environmental_analysis_agent._circuit_breakers["analysis"] = mock_circuit
        
        # Execute processing
        result = await environmental_analysis_agent._process(sample_garden_planner_output)
        
        # Verify safe failure handling
        assert result is not None
        assert result["error"] == "Analysis rejected due to circuit breaker open"
        assert result["status"] == "failure"
        assert result["agent_id"] == environmental_analysis_agent.interface_id
        assert environmental_analysis_agent.development_state == DevelopmentState.ERROR
        
        # Verify timestamp is present
        assert "timestamp" in result
    
    async def test_processing_exception_handling(self, environmental_analysis_agent, sample_garden_planner_output):
        """Test handling of unexpected exceptions during processing."""
        # Mock circuit breaker to raise unexpected exception
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(side_effect=Exception("Unexpected processing error"))
        environmental_analysis_agent._circuit_breakers["analysis"] = mock_circuit
        
        # Should raise the exception
        with pytest.raises(Exception, match="Unexpected processing error"):
            await environmental_analysis_agent._process(sample_garden_planner_output)
        
        # Verify state was set to error
        assert environmental_analysis_agent.development_state == DevelopmentState.ERROR
        
        # Verify critical health status was reported
        health_calls = [call for call in environmental_analysis_agent._report_agent_health.call_args_list 
                       if call[1].get('custom_status') == 'CRITICAL']
        assert len(health_calls) > 0


class TestMemoryTracking:
    """Test memory tracking and monitoring functionality."""
    
    async def test_memory_tracking_during_processing(self, environmental_analysis_agent, sample_garden_planner_output):
        """Test memory usage tracking during processing."""
        # Mock successful processing
        analysis_result = {
            "environmental_analysis": {"requirements": "test"},
            "status": "success"
        }
        
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=analysis_result)
        environmental_analysis_agent._circuit_breakers["analysis"] = mock_circuit
        
        environmental_analysis_agent.process_with_validation = AsyncMock(return_value=analysis_result)
        environmental_analysis_agent.standard_reflect = AsyncMock(return_value={
            "reflection_results": {"validation_status": {"passed": True}}
        })
        
        # Execute processing
        await environmental_analysis_agent._process(sample_garden_planner_output)
        
        # Verify memory tracking calls
        track_calls = environmental_analysis_agent.track_dict_memory.call_args_list
        
        # Should track garden planner input and analysis result
        tracked_resources = [call[0][0] for call in track_calls]
        assert "garden_planner_input" in tracked_resources
        assert "analysis_result" in tracked_resources
    
    async def test_memory_tracking_methods(self, environmental_analysis_agent):
        """Test individual memory tracking methods."""
        test_data = {"key": "value", "data": [1, 2, 3]}
        
        # Test track_dict_memory
        await environmental_analysis_agent.track_dict_memory("test_dict", test_data)
        
        # Verify track_memory_usage was called
        environmental_analysis_agent.track_memory_usage.assert_called()
        
        # Verify the resource ID and approximate size calculation
        call_args = environmental_analysis_agent.track_memory_usage.call_args
        assert call_args[0][0] == "test_dict"
        assert call_args[0][1] > 0  # Size should be positive


class TestReflectionAndRefinement:
    """Test reflection and refinement functionality."""
    
    async def test_reflection_delegation(self, environmental_analysis_agent):
        """Test that reflection is delegated to standard method."""
        test_output = {"analysis": "test"}
        expected_result = {"reflection": "completed"}
        
        environmental_analysis_agent.standard_reflect = AsyncMock(return_value=expected_result)
        
        result = await environmental_analysis_agent.reflect(test_output)
        
        assert result == expected_result
        environmental_analysis_agent.standard_reflect.assert_called_once_with(test_output, "analysis")
    
    async def test_refinement_delegation(self, environmental_analysis_agent):
        """Test that refinement is delegated to standard method."""
        test_output = {"analysis": "test"}
        test_guidance = {"guidance": "improve"}
        expected_result = {"refined": "result"}
        
        environmental_analysis_agent.standard_refine = AsyncMock(return_value=expected_result)
        
        result = await environmental_analysis_agent.refine(test_output, test_guidance)
        
        assert result == expected_result
        environmental_analysis_agent.standard_refine.assert_called_once_with(
            test_output, test_guidance, "analysis"
        )


class TestHealthReporting:
    """Test health reporting functionality."""
    
    async def test_health_reporting_during_states(self, environmental_analysis_agent, sample_garden_planner_output):
        """Test health reporting during different processing states."""
        # Mock successful processing
        analysis_result = {"environmental_analysis": {"requirements": "test"}}
        
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=analysis_result)
        environmental_analysis_agent._circuit_breakers["analysis"] = mock_circuit
        
        environmental_analysis_agent.process_with_validation = AsyncMock(return_value=analysis_result)
        environmental_analysis_agent.standard_reflect = AsyncMock(return_value={
            "reflection_results": {"validation_status": {"passed": True}}
        })
        
        # Execute processing
        await environmental_analysis_agent._process(sample_garden_planner_output)
        
        # Verify health was reported multiple times during processing
        health_calls = environmental_analysis_agent._report_agent_health.call_args_list
        assert len(health_calls) >= 2
        
        # Check for processing state health report
        processing_calls = [call for call in health_calls 
                          if call[0][0] == "Processing environment analysis"]
        assert len(processing_calls) > 0
        
        # Check for completion state health report
        completion_calls = [call for call in health_calls 
                          if call[0][0] == "Environment analysis completed successfully"]
        assert len(completion_calls) > 0


class TestDevelopmentStateTransitions:
    """Test development state transitions during processing."""
    
    async def test_state_progression_success(self, environmental_analysis_agent, sample_garden_planner_output):
        """Test state progression during successful processing."""
        # Track state changes
        states = []
        
        def track_state_change():
            states.append(environmental_analysis_agent.development_state)
        
        # Mock successful processing with state tracking
        analysis_result = {"environmental_analysis": {"requirements": "test"}}
        
        async def mock_execute(func):
            track_state_change()  # Before analysis
            return analysis_result
        
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(side_effect=mock_execute)
        environmental_analysis_agent._circuit_breakers["analysis"] = mock_circuit
        
        environmental_analysis_agent.process_with_validation = AsyncMock(return_value=analysis_result)
        environmental_analysis_agent.standard_reflect = AsyncMock(return_value={
            "reflection_results": {"validation_status": {"passed": True}}
        })
        
        # Initial state
        assert environmental_analysis_agent.development_state == DevelopmentState.INITIALIZING
        
        # Execute processing
        await environmental_analysis_agent._process(sample_garden_planner_output)
        
        # Verify final state
        assert environmental_analysis_agent.development_state == DevelopmentState.COMPLETE
    
    async def test_state_error_handling(self, environmental_analysis_agent, sample_garden_planner_output):
        """Test state transitions during error conditions."""
        # Mock circuit breaker open
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(side_effect=CircuitOpenError("Circuit open"))
        environmental_analysis_agent._circuit_breakers["analysis"] = mock_circuit
        
        # Execute processing
        await environmental_analysis_agent._process(sample_garden_planner_output)
        
        # Verify error state
        assert environmental_analysis_agent.development_state == DevelopmentState.ERROR


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    async def test_minimal_input_processing(self, environmental_analysis_agent, sample_minimal_garden_planner_output):
        """Test processing with minimal input data."""
        # Mock successful processing with minimal data
        analysis_result = {
            "environmental_analysis": {
                "runtime_requirements": {"basic": True},
                "deployment_requirements": {"simple": True}
            },
            "status": "success"
        }
        
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=analysis_result)
        environmental_analysis_agent._circuit_breakers["analysis"] = mock_circuit
        
        environmental_analysis_agent.process_with_validation = AsyncMock(return_value=analysis_result)
        environmental_analysis_agent.standard_reflect = AsyncMock(return_value={
            "reflection_results": {"validation_status": {"passed": True}}
        })
        
        # Execute processing
        result = await environmental_analysis_agent._process(sample_minimal_garden_planner_output)
        
        # Verify processing succeeds with minimal input
        assert result is not None
        assert result["environmental_analysis"]["runtime_requirements"]["basic"] is True
    
    async def test_empty_input_processing(self, environmental_analysis_agent):
        """Test processing with empty input data."""
        empty_input = {}
        
        # Mock processing that handles empty input
        analysis_result = {
            "environmental_analysis": {"default": "configuration"},
            "status": "success"
        }
        
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=analysis_result)
        environmental_analysis_agent._circuit_breakers["analysis"] = mock_circuit
        
        environmental_analysis_agent.process_with_validation = AsyncMock(return_value=analysis_result)
        environmental_analysis_agent.standard_reflect = AsyncMock(return_value={
            "reflection_results": {"validation_status": {"passed": True}}
        })
        
        # Execute processing
        result = await environmental_analysis_agent._process(empty_input)
        
        # Verify processing handles empty input gracefully
        assert result is not None
        assert result["environmental_analysis"]["default"] == "configuration"
    
    async def test_large_input_memory_tracking(self, environmental_analysis_agent):
        """Test memory tracking with large input data."""
        # Create large input data
        large_input = {
            "task_analysis": {
                "requirements": [f"requirement_{i}" for i in range(1000)],
                "detailed_specs": {f"spec_{i}": f"value_{i}" for i in range(500)}
            }
        }
        
        # Mock successful processing
        analysis_result = {"environmental_analysis": {"processed": True}}
        
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=analysis_result)
        environmental_analysis_agent._circuit_breakers["analysis"] = mock_circuit
        
        environmental_analysis_agent.process_with_validation = AsyncMock(return_value=analysis_result)
        environmental_analysis_agent.standard_reflect = AsyncMock(return_value={
            "reflection_results": {"validation_status": {"passed": True}}
        })
        
        # Execute processing
        await environmental_analysis_agent._process(large_input)
        
        # Verify memory tracking was called for large input
        track_calls = environmental_analysis_agent.track_dict_memory.call_args_list
        garden_input_calls = [call for call in track_calls if call[0][0] == "garden_planner_input"]
        assert len(garden_input_calls) > 0


class TestIntegrationScenarios:
    """Test integration scenarios and realistic workflows."""
    
    async def test_full_analysis_workflow(self, environmental_analysis_agent, sample_garden_planner_output):
        """Test complete analysis workflow from start to finish."""
        # Mock comprehensive analysis result
        comprehensive_result = {
            "environmental_analysis": {
                "runtime_requirements": {
                    "target_platforms": ["web", "mobile"],
                    "performance_targets": {
                        "concurrent_users": 1000,
                        "response_time": "< 200ms"
                    },
                    "availability_requirements": "99.9%"
                },
                "deployment_requirements": {
                    "hosting_environment": "cloud",
                    "database_requirements": ["PostgreSQL", "Redis"],
                    "monitoring_requirements": ["metrics", "logging", "alerting"]
                },
                "technical_constraints": {
                    "security_requirements": ["HTTPS", "authentication"],
                    "compliance_requirements": ["GDPR"],
                    "integration_requirements": ["payment_gateway", "email_service"]
                },
                "resource_estimates": {
                    "cpu_requirements": "4 cores minimum",
                    "memory_requirements": "8GB minimum",
                    "storage_requirements": "100GB initial"
                }
            },
            "analysis_metadata": {
                "coverage_assessment": "comprehensive",
                "risk_factors": ["third_party_dependencies", "scalability_challenges"],
                "recommendations": ["implement_caching", "use_cdn", "monitor_performance"]
            },
            "validation_status": {
                "passed": True,
                "completeness_score": 0.95,
                "requirements_coverage": "complete"
            },
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        
        # Mock circuit breaker and processing
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=comprehensive_result)
        environmental_analysis_agent._circuit_breakers["analysis"] = mock_circuit
        
        environmental_analysis_agent.process_with_validation = AsyncMock(return_value=comprehensive_result)
        environmental_analysis_agent.standard_reflect = AsyncMock(return_value={
            "reflection_results": {"validation_status": {"passed": True}}
        })
        
        # Execute full workflow
        result = await environmental_analysis_agent._process(sample_garden_planner_output)
        
        # Verify comprehensive result
        assert result == comprehensive_result
        assert result["validation_status"]["passed"] is True
        assert result["analysis_metadata"]["coverage_assessment"] == "comprehensive"
        assert environmental_analysis_agent.development_state == DevelopmentState.COMPLETE
        
        # Verify all expected memory tracking occurred
        track_calls = environmental_analysis_agent.track_dict_memory.call_args_list
        tracked_resources = [call[0][0] for call in track_calls]
        assert "garden_planner_input" in tracked_resources
        assert "analysis_result" in tracked_resources
        
        # Verify health reporting occurred
        health_calls = environmental_analysis_agent._report_agent_health.call_args_list
        assert len(health_calls) >= 2  # Processing start and completion
    
    async def test_analysis_refinement_cycle(self, environmental_analysis_agent, sample_garden_planner_output):
        """Test analysis with refinement cycle."""
        # Initial analysis with validation failure
        initial_result = {
            "environmental_analysis": {"incomplete": True},
            "validation_status": {"passed": False}
        }
        
        # Refined analysis with validation success
        refined_result = {
            "environmental_analysis": {"complete": True},
            "validation_status": {"passed": True}
        }
        
        reflection_failure = {
            "reflection_results": {"validation_status": {"passed": False}}
        }
        
        # Mock circuit breaker and processing
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=initial_result)
        environmental_analysis_agent._circuit_breakers["analysis"] = mock_circuit
        
        environmental_analysis_agent.process_with_validation = AsyncMock(return_value=initial_result)
        environmental_analysis_agent.standard_reflect = AsyncMock(return_value=reflection_failure)
        
        # Execute processing (should trigger refinement path)
        result = await environmental_analysis_agent._process(sample_garden_planner_output)
        
        # Verify refinement was triggered
        assert result == reflection_failure
        assert environmental_analysis_agent.development_state == DevelopmentState.REFINING
        
        # Verify degraded health was reported
        health_calls = environmental_analysis_agent._report_agent_health.call_args_list
        degraded_calls = [call for call in health_calls 
                         if call[1].get('custom_status') == 'DEGRADED']
        assert len(degraded_calls) > 0