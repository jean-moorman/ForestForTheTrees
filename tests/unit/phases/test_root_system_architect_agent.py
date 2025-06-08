"""
Unit tests for Root System Architect Agent

Tests the core Phase One agent responsible for data flow architecture design
with proper circuit breaker protection, memory monitoring, performance metrics,
and health tracking.
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from phase_one.agents.root_system_architect import RootSystemArchitectAgent
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
            "requirements": [
                "User authentication and registration",
                "Product catalog management", 
                "Shopping cart functionality",
                "Order processing and payment"
            ]
        },
        "scope_definition": {
            "core_features": ["catalog", "cart", "orders", "payments"],
            "data_entities": ["users", "products", "orders", "payments"]
        },
        "status": "completed"
    }


@pytest.fixture
def sample_environment_analysis_output():
    """Sample environment analysis output for testing."""
    return {
        "environmental_analysis": {
            "runtime_requirements": {
                "target_platforms": ["web", "mobile"],
                "performance_targets": {
                    "concurrent_users": 1000,
                    "response_time": "< 200ms"
                }
            },
            "deployment_requirements": {
                "hosting_environment": "cloud",
                "database_requirements": ["PostgreSQL", "Redis"],
                "scalability_requirements": ["horizontal_scaling", "load_balancing"]
            },
            "technical_constraints": {
                "framework_preferences": ["React", "Node.js"],
                "security_requirements": ["HTTPS", "authentication", "data_encryption"]
            }
        },
        "status": "success"
    }


@pytest.fixture
def sample_large_inputs():
    """Large input samples for memory testing."""
    return {
        "garden_planner": {
            "task_analysis": {
                "requirements": [f"requirement_{i}" for i in range(100)],
                "detailed_specs": {f"spec_{i}": f"value_{i}" for i in range(50)}
            }
        },
        "environment_analysis": {
            "environmental_analysis": {
                "runtime_requirements": {f"req_{i}": f"value_{i}" for i in range(50)},
                "deployment_requirements": {f"deploy_{i}": f"config_{i}" for i in range(50)}
            }
        }
    }


@pytest.fixture
async def root_system_architect_agent(mock_resources):
    """Create a Root System Architect Agent for testing."""
    agent = RootSystemArchitectAgent(
        agent_id="root_system_test",
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


class TestRootSystemArchitectAgentInitialization:
    """Test Root System Architect Agent initialization."""
    
    async def test_initialization_success(self, mock_resources):
        """Test successful agent initialization."""
        agent = RootSystemArchitectAgent(
            agent_id="test_root_agent",
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
        assert agent.interface_id == "agent:test_root_agent"
        assert agent.development_state == DevelopmentState.INITIALIZING
        assert isinstance(agent._prompt_config, AgentPromptConfig)
        
        # Verify prompt configuration
        assert agent._prompt_config.system_prompt_base_path == "FFTT_system_prompts/phase_one/root_system_architect_agent"
        assert agent._prompt_config.reflection_prompt_name == "core_data_flow_reflection_prompt"
        assert agent._prompt_config.refinement_prompt_name == "core_data_flow_refinement_prompt"
        assert agent._prompt_config.initial_prompt_name == "initial_core_data_flow_prompt"
        
        # Verify circuit breakers
        assert "design" in agent._circuit_breakers
        assert "processing" in agent._circuit_breakers  # Default from base class
        
        # Verify design circuit breaker configuration (longer timeouts for complex design)
        design_cb = agent.get_circuit_breaker("design")
        assert design_cb is not None
    
    async def test_initialization_memory_monitor_registration(self, mock_resources):
        """Test memory monitor registration with higher thresholds for architecture diagrams."""
        agent = RootSystemArchitectAgent(
            agent_id="test_memory_root",
            event_queue=mock_resources['event_queue'],
            state_manager=mock_resources['state_manager'],
            context_manager=mock_resources['context_manager'],
            cache_manager=mock_resources['cache_manager'],
            metrics_manager=mock_resources['metrics_manager'],
            error_handler=mock_resources['error_handler'],
            memory_monitor=mock_resources['memory_monitor'],
            health_tracker=mock_resources['health_tracker']
        )
        
        # Verify memory monitor registration
        mock_resources['memory_monitor'].register_component.assert_called_once()
        
        # Verify registration parameters
        call_args = mock_resources['memory_monitor'].register_component.call_args
        assert call_args[0][0] == "agent_test_memory_root"
        
        # Verify memory thresholds (higher for architecture diagrams)
        thresholds = call_args[0][1]
        assert isinstance(thresholds, MemoryThresholds)
        assert thresholds.per_resource_max_mb == 100  # Higher for architecture data
        assert thresholds.warning_percent == 0.6
        assert thresholds.critical_percent == 0.85


class TestDataArchitectureDesign:
    """Test core data architecture design functionality."""
    
    async def test_successful_architecture_design(
        self, 
        root_system_architect_agent, 
        sample_garden_planner_output, 
        sample_environment_analysis_output
    ):
        """Test successful data architecture design processing."""
        # Mock successful design result
        design_result = {
            "data_architecture": {
                "data_entities": {
                    "users": {
                        "attributes": ["id", "email", "password_hash", "profile"],
                        "relationships": ["orders", "cart_items"],
                        "constraints": ["unique_email", "required_fields"]
                    },
                    "products": {
                        "attributes": ["id", "name", "description", "price", "inventory"],
                        "relationships": ["categories", "order_items"],
                        "constraints": ["positive_price", "non_negative_inventory"]
                    },
                    "orders": {
                        "attributes": ["id", "user_id", "total", "status", "created_at"],
                        "relationships": ["users", "order_items", "payments"],
                        "constraints": ["valid_status", "positive_total"]
                    }
                },
                "data_flows": {
                    "user_registration": {
                        "source": "client",
                        "destination": "user_service",
                        "data": ["email", "password", "profile"],
                        "validation": ["email_format", "password_strength"]
                    },
                    "product_catalog": {
                        "source": "product_service",
                        "destination": "client",
                        "data": ["products", "categories", "inventory"],
                        "caching": ["redis_cache", "cdn"]
                    },
                    "order_processing": {
                        "source": "order_service",
                        "destination": ["payment_service", "inventory_service"],
                        "data": ["order_details", "payment_info"],
                        "transactions": ["atomic_operations", "rollback_capability"]
                    }
                },
                "integration_points": {
                    "payment_gateway": {
                        "provider": "stripe",
                        "data_format": "json",
                        "security": ["ssl", "api_keys"]
                    },
                    "email_service": {
                        "provider": "sendgrid",
                        "triggers": ["registration", "order_confirmation"],
                        "templates": ["welcome", "receipt"]
                    }
                }
            },
            "architecture_metadata": {
                "complexity_assessment": "medium",
                "scalability_factors": ["database_sharding", "service_separation"],
                "performance_considerations": ["indexing", "caching", "query_optimization"]
            },
            "validation_status": {
                "passed": True,
                "data_consistency": "validated",
                "flow_completeness": "comprehensive"
            },
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        
        # Mock the circuit breaker and process_with_validation
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=design_result)
        root_system_architect_agent._circuit_breakers["design"] = mock_circuit
        
        root_system_architect_agent.process_with_validation = AsyncMock(return_value=design_result)
        root_system_architect_agent.standard_reflect = AsyncMock(return_value={
            "reflection_results": {
                "validation_status": {"passed": True}
            }
        })
        
        # Execute processing
        result = await root_system_architect_agent._process(
            sample_garden_planner_output, 
            sample_environment_analysis_output
        )
        
        # Verify result
        assert result is not None
        assert result["data_architecture"]["data_entities"]["users"]["attributes"][0] == "id"
        assert result["validation_status"]["passed"] is True
        assert root_system_architect_agent.development_state == DevelopmentState.COMPLETE
        
        # Verify circuit breaker was called
        mock_circuit.execute.assert_called_once()
        
        # Verify metrics were recorded
        root_system_architect_agent._metrics_manager.record_metric.assert_called()
        
        # Verify design completion metric
        metric_calls = root_system_architect_agent._metrics_manager.record_metric.call_args_list
        design_metrics = [call for call in metric_calls 
                         if "design_completed" in call[0][0]]
        assert len(design_metrics) > 0
    
    async def test_design_validation_failure(
        self, 
        root_system_architect_agent, 
        sample_garden_planner_output, 
        sample_environment_analysis_output
    ):
        """Test handling of validation failure during design."""
        # Mock design result with validation failure
        design_result = {
            "data_architecture": {
                "data_entities": {"incomplete": True}
            },
            "validation_status": {
                "passed": False,
                "issues": ["Missing data relationships", "Incomplete flow definitions"]
            },
            "status": "needs_refinement"
        }
        
        reflection_result = {
            "reflection_results": {
                "validation_status": {"passed": False},
                "issues": ["Architecture incomplete", "Missing critical relationships"]
            },
            "refinement_needed": True
        }
        
        # Mock the circuit breaker and methods
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=design_result)
        root_system_architect_agent._circuit_breakers["design"] = mock_circuit
        
        root_system_architect_agent.process_with_validation = AsyncMock(return_value=design_result)
        root_system_architect_agent.standard_reflect = AsyncMock(return_value=reflection_result)
        
        # Execute processing
        result = await root_system_architect_agent._process(
            sample_garden_planner_output, 
            sample_environment_analysis_output
        )
        
        # Verify result indicates refinement needed
        assert result == reflection_result
        assert root_system_architect_agent.development_state == DevelopmentState.REFINING
        
        # Verify health status was updated to degraded
        health_calls = [call for call in root_system_architect_agent._report_agent_health.call_args_list 
                       if call[1].get('custom_status') == 'DEGRADED']
        assert len(health_calls) > 0
    
    async def test_circuit_breaker_open(
        self, 
        root_system_architect_agent, 
        sample_garden_planner_output, 
        sample_environment_analysis_output
    ):
        """Test handling when design circuit breaker is open."""
        # Mock circuit breaker to raise CircuitOpenError
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(side_effect=CircuitOpenError("Design circuit open"))
        root_system_architect_agent._circuit_breakers["design"] = mock_circuit
        
        # Execute processing
        result = await root_system_architect_agent._process(
            sample_garden_planner_output, 
            sample_environment_analysis_output
        )
        
        # Verify safe failure handling
        assert result is not None
        assert result["error"] == "Design operation rejected due to circuit breaker open"
        assert result["status"] == "failure"
        assert result["agent_id"] == root_system_architect_agent.interface_id
        assert root_system_architect_agent.development_state == DevelopmentState.ERROR
        
        # Verify critical health status was reported
        health_calls = [call for call in root_system_architect_agent._report_agent_health.call_args_list 
                       if call[1].get('custom_status') == 'CRITICAL']
        assert len(health_calls) > 0
    
    async def test_design_exception_handling(
        self, 
        root_system_architect_agent, 
        sample_garden_planner_output, 
        sample_environment_analysis_output
    ):
        """Test handling of unexpected exceptions during design."""
        # Mock circuit breaker to raise unexpected exception
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(side_effect=Exception("Unexpected design error"))
        root_system_architect_agent._circuit_breakers["design"] = mock_circuit
        
        # Should raise the exception
        with pytest.raises(Exception, match="Unexpected design error"):
            await root_system_architect_agent._process(
                sample_garden_planner_output, 
                sample_environment_analysis_output
            )
        
        # Verify state was set to error
        assert root_system_architect_agent.development_state == DevelopmentState.ERROR
        
        # Verify error metric was recorded
        error_metrics = [call for call in root_system_architect_agent._metrics_manager.record_metric.call_args_list 
                        if "design_errors" in call[0][0]]
        assert len(error_metrics) > 0


class TestMemoryTrackingAndManagement:
    """Test memory tracking and management functionality."""
    
    async def test_memory_tracking_multiple_inputs(
        self, 
        root_system_architect_agent, 
        sample_garden_planner_output, 
        sample_environment_analysis_output
    ):
        """Test memory usage tracking for multiple input sources."""
        # Mock successful processing
        design_result = {
            "data_architecture": {"entities": "test"},
            "status": "success"
        }
        
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=design_result)
        root_system_architect_agent._circuit_breakers["design"] = mock_circuit
        
        root_system_architect_agent.process_with_validation = AsyncMock(return_value=design_result)
        root_system_architect_agent.standard_reflect = AsyncMock(return_value={
            "reflection_results": {"validation_status": {"passed": True}}
        })
        
        # Execute processing
        await root_system_architect_agent._process(
            sample_garden_planner_output, 
            sample_environment_analysis_output
        )
        
        # Verify memory tracking calls for all inputs
        track_calls = root_system_architect_agent.track_dict_memory.call_args_list
        tracked_resources = [call[0][0] for call in track_calls]
        
        assert "garden_planner_input" in tracked_resources
        assert "environment_analysis_input" in tracked_resources
        assert "initial_design" in tracked_resources
        
        # Verify total input size tracking
        memory_calls = root_system_architect_agent.track_memory_usage.call_args_list
        total_input_calls = [call for call in memory_calls if call[0][0] == "total_input"]
        assert len(total_input_calls) > 0
    
    async def test_large_input_memory_tracking(self, root_system_architect_agent, sample_large_inputs):
        """Test memory tracking with large input data."""
        # Mock successful processing
        design_result = {"data_architecture": {"processed": True}}
        
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=design_result)
        root_system_architect_agent._circuit_breakers["design"] = mock_circuit
        
        root_system_architect_agent.process_with_validation = AsyncMock(return_value=design_result)
        root_system_architect_agent.standard_reflect = AsyncMock(return_value={
            "reflection_results": {"validation_status": {"passed": True}}
        })
        
        # Execute processing with large inputs
        await root_system_architect_agent._process(
            sample_large_inputs["garden_planner"],
            sample_large_inputs["environment_analysis"]
        )
        
        # Verify memory tracking was called for large inputs
        track_calls = root_system_architect_agent.track_dict_memory.call_args_list
        assert len(track_calls) >= 3  # At least 3 tracking calls (2 inputs + 1 result)
        
        # Verify total input size calculation was performed
        memory_calls = root_system_architect_agent.track_memory_usage.call_args_list
        total_input_calls = [call for call in memory_calls if call[0][0] == "total_input"]
        assert len(total_input_calls) > 0


class TestPerformanceMetrics:
    """Test performance metrics tracking functionality."""
    
    async def test_reflection_performance_tracking(
        self, 
        root_system_architect_agent, 
        sample_garden_planner_output
    ):
        """Test performance tracking during reflection."""
        test_output = {"design": "test"}
        expected_result = {"reflection": "completed"}
        
        root_system_architect_agent.standard_reflect = AsyncMock(return_value=expected_result)
        
        # Execute reflection
        result = await root_system_architect_agent.reflect(test_output)
        
        # Verify result
        assert result == expected_result
        
        # Verify performance metric was recorded
        metric_calls = root_system_architect_agent._metrics_manager.record_metric.call_args_list
        reflection_time_metrics = [call for call in metric_calls 
                                  if "reflection_time" in call[0][0]]
        assert len(reflection_time_metrics) > 0
        
        # Verify metric includes success metadata
        reflection_metric = reflection_time_metrics[0]
        assert reflection_metric[1]["metadata"]["success"] is True
    
    async def test_refinement_performance_tracking(
        self, 
        root_system_architect_agent
    ):
        """Test performance tracking during refinement."""
        test_output = {"design": "test"}
        test_guidance = {"guidance": "improve"}
        expected_result = {"refined": "result"}
        
        root_system_architect_agent.standard_refine = AsyncMock(return_value=expected_result)
        
        # Execute refinement
        result = await root_system_architect_agent.refine(test_output, test_guidance)
        
        # Verify result
        assert result == expected_result
        
        # Verify performance metric was recorded
        metric_calls = root_system_architect_agent._metrics_manager.record_metric.call_args_list
        refinement_time_metrics = [call for call in metric_calls 
                                  if "refinement_time" in call[0][0]]
        assert len(refinement_time_metrics) > 0
        
        # Verify metric includes success metadata
        refinement_metric = refinement_time_metrics[0]
        assert refinement_metric[1]["metadata"]["success"] is True


class TestHealthReporting:
    """Test health reporting functionality with multiple input sources."""
    
    async def test_health_reporting_with_input_sources(
        self, 
        root_system_architect_agent, 
        sample_garden_planner_output, 
        sample_environment_analysis_output
    ):
        """Test health reporting includes input source information."""
        # Mock successful processing
        design_result = {"data_architecture": {"entities": "test"}}
        
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=design_result)
        root_system_architect_agent._circuit_breakers["design"] = mock_circuit
        
        root_system_architect_agent.process_with_validation = AsyncMock(return_value=design_result)
        root_system_architect_agent.standard_reflect = AsyncMock(return_value={
            "reflection_results": {"validation_status": {"passed": True}}
        })
        
        # Execute processing
        await root_system_architect_agent._process(
            sample_garden_planner_output, 
            sample_environment_analysis_output
        )
        
        # Verify health was reported with input source metadata
        health_calls = root_system_architect_agent._report_agent_health.call_args_list
        
        # Check for designing state health report with input sources
        designing_calls = [call for call in health_calls 
                          if call[0][0] == "Designing data architecture"]
        assert len(designing_calls) > 0
        
        designing_call = designing_calls[0]
        metadata = designing_call[1]["metadata"]
        assert "input_sources" in metadata
        assert "garden_planner" in metadata["input_sources"]
        assert "environment_analysis" in metadata["input_sources"]
    
    async def test_circuit_breaker_health_reporting(
        self, 
        root_system_architect_agent, 
        sample_garden_planner_output, 
        sample_environment_analysis_output
    ):
        """Test health reporting when circuit breaker opens."""
        # Mock circuit breaker open
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(side_effect=CircuitOpenError("Design circuit open"))
        root_system_architect_agent._circuit_breakers["design"] = mock_circuit
        
        # Execute processing
        await root_system_architect_agent._process(
            sample_garden_planner_output, 
            sample_environment_analysis_output
        )
        
        # Verify critical health status was reported with circuit breaker details
        health_calls = root_system_architect_agent._report_agent_health.call_args_list
        critical_calls = [call for call in health_calls 
                         if call[1].get('custom_status') == 'CRITICAL']
        assert len(critical_calls) > 0
        
        critical_call = critical_calls[0]
        metadata = critical_call[1]["metadata"]
        assert metadata["circuit"] == "design_circuit"
        assert metadata["circuit_state"] == "OPEN"


class TestDevelopmentStateTransitions:
    """Test development state transitions during architecture design."""
    
    async def test_state_progression_success(
        self, 
        root_system_architect_agent, 
        sample_garden_planner_output, 
        sample_environment_analysis_output
    ):
        """Test state progression during successful design."""
        # Mock successful processing
        design_result = {"data_architecture": {"entities": "test"}}
        
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=design_result)
        root_system_architect_agent._circuit_breakers["design"] = mock_circuit
        
        root_system_architect_agent.process_with_validation = AsyncMock(return_value=design_result)
        root_system_architect_agent.standard_reflect = AsyncMock(return_value={
            "reflection_results": {"validation_status": {"passed": True}}
        })
        
        # Initial state
        assert root_system_architect_agent.development_state == DevelopmentState.INITIALIZING
        
        # Execute processing
        await root_system_architect_agent._process(
            sample_garden_planner_output, 
            sample_environment_analysis_output
        )
        
        # Verify final state
        assert root_system_architect_agent.development_state == DevelopmentState.COMPLETE
    
    async def test_state_progression_with_validation(
        self, 
        root_system_architect_agent, 
        sample_garden_planner_output, 
        sample_environment_analysis_output
    ):
        """Test state progression through validation."""
        # Mock design and validation steps
        design_result = {"data_architecture": {"entities": "test"}}
        
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=design_result)
        root_system_architect_agent._circuit_breakers["design"] = mock_circuit
        
        root_system_architect_agent.process_with_validation = AsyncMock(return_value=design_result)
        
        # Track state transitions during reflection
        def track_reflect_state(*args, **kwargs):
            # Should be in VALIDATING state during reflection
            assert root_system_architect_agent.development_state == DevelopmentState.VALIDATING
            return {"reflection_results": {"validation_status": {"passed": True}}}
        
        root_system_architect_agent.standard_reflect = AsyncMock(side_effect=track_reflect_state)
        
        # Execute processing
        await root_system_architect_agent._process(
            sample_garden_planner_output, 
            sample_environment_analysis_output
        )
        
        # Verify final state
        assert root_system_architect_agent.development_state == DevelopmentState.COMPLETE


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    async def test_empty_input_processing(self, root_system_architect_agent):
        """Test processing with empty input data."""
        empty_garden_planner = {}
        empty_environment_analysis = {}
        
        # Mock processing that handles empty inputs
        design_result = {
            "data_architecture": {"default": "configuration"},
            "status": "success"
        }
        
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=design_result)
        root_system_architect_agent._circuit_breakers["design"] = mock_circuit
        
        root_system_architect_agent.process_with_validation = AsyncMock(return_value=design_result)
        root_system_architect_agent.standard_reflect = AsyncMock(return_value={
            "reflection_results": {"validation_status": {"passed": True}}
        })
        
        # Execute processing
        result = await root_system_architect_agent._process(
            empty_garden_planner, 
            empty_environment_analysis
        )
        
        # Verify processing handles empty inputs gracefully
        assert result is not None
        assert result["data_architecture"]["default"] == "configuration"
    
    async def test_malformed_input_processing(self, root_system_architect_agent):
        """Test processing with malformed input data."""
        malformed_garden_planner = "not_a_dict"
        malformed_environment_analysis = None
        
        # Mock processing that handles malformed inputs
        design_result = {
            "data_architecture": {"error_handled": True},
            "status": "success"
        }
        
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=design_result)
        root_system_architect_agent._circuit_breakers["design"] = mock_circuit
        
        root_system_architect_agent.process_with_validation = AsyncMock(return_value=design_result)
        root_system_architect_agent.standard_reflect = AsyncMock(return_value={
            "reflection_results": {"validation_status": {"passed": True}}
        })
        
        # Execute processing
        result = await root_system_architect_agent._process(
            malformed_garden_planner, 
            malformed_environment_analysis
        )
        
        # Verify processing handles malformed inputs gracefully
        assert result is not None
        assert result["data_architecture"]["error_handled"] is True


class TestIntegrationScenarios:
    """Test integration scenarios and realistic workflows."""
    
    async def test_complete_architecture_design_workflow(
        self, 
        root_system_architect_agent, 
        sample_garden_planner_output, 
        sample_environment_analysis_output
    ):
        """Test complete architecture design workflow from start to finish."""
        # Mock comprehensive architecture design result
        comprehensive_result = {
            "data_architecture": {
                "data_entities": {
                    "users": {
                        "attributes": ["id", "email", "password_hash", "profile", "created_at"],
                        "relationships": ["orders", "cart_items", "reviews"],
                        "constraints": ["unique_email", "required_fields", "valid_email_format"],
                        "indices": ["email_idx", "created_at_idx"]
                    },
                    "products": {
                        "attributes": ["id", "name", "description", "price", "inventory", "category_id"],
                        "relationships": ["categories", "order_items", "reviews", "images"],
                        "constraints": ["positive_price", "non_negative_inventory", "required_name"],
                        "indices": ["category_idx", "price_idx", "name_search_idx"]
                    },
                    "orders": {
                        "attributes": ["id", "user_id", "total", "status", "created_at", "updated_at"],
                        "relationships": ["users", "order_items", "payments", "shipping"],
                        "constraints": ["valid_status", "positive_total", "valid_user"],
                        "indices": ["user_idx", "status_idx", "created_at_idx"]
                    },
                    "payments": {
                        "attributes": ["id", "order_id", "amount", "method", "status", "processed_at"],
                        "relationships": ["orders"],
                        "constraints": ["positive_amount", "valid_method", "valid_status"],
                        "indices": ["order_idx", "status_idx"]
                    }
                },
                "data_flows": {
                    "user_registration_flow": {
                        "source": "client_application",
                        "destination": "user_service",
                        "data": ["email", "password", "profile_data"],
                        "validation": ["email_format", "password_strength", "profile_completeness"],
                        "security": ["input_sanitization", "rate_limiting"],
                        "error_handling": ["duplicate_email", "invalid_format"]
                    },
                    "product_catalog_flow": {
                        "source": "product_service",
                        "destination": "client_application",
                        "data": ["products", "categories", "inventory", "images"],
                        "caching": ["redis_cache", "cdn_cache"],
                        "optimization": ["lazy_loading", "pagination"],
                        "filters": ["category", "price_range", "availability"]
                    },
                    "order_processing_flow": {
                        "source": "order_service",
                        "destination": ["payment_service", "inventory_service", "notification_service"],
                        "data": ["order_details", "payment_info", "shipping_info"],
                        "transactions": ["atomic_operations", "two_phase_commit"],
                        "rollback": ["payment_reversal", "inventory_restoration"],
                        "monitoring": ["processing_time", "failure_rate"]
                    }
                },
                "integration_points": {
                    "payment_gateway": {
                        "provider": "stripe",
                        "data_format": "json",
                        "security": ["ssl", "api_keys", "webhook_verification"],
                        "fallback": ["secondary_provider", "manual_processing"]
                    },
                    "email_service": {
                        "provider": "sendgrid",
                        "triggers": ["registration", "order_confirmation", "shipping_update"],
                        "templates": ["welcome", "receipt", "shipping_notification"],
                        "personalization": ["user_preferences", "order_history"]
                    },
                    "analytics_service": {
                        "provider": "google_analytics",
                        "events": ["page_views", "purchases", "cart_additions"],
                        "privacy": ["gdpr_compliance", "user_consent"]
                    }
                }
            },
            "performance_considerations": {
                "database_optimization": ["indexing_strategy", "query_optimization", "connection_pooling"],
                "caching_strategy": ["redis_cache", "application_cache", "cdn"],
                "scalability_patterns": ["horizontal_scaling", "database_sharding", "microservices"]
            },
            "security_architecture": {
                "authentication": ["jwt_tokens", "oauth2", "multi_factor"],
                "authorization": ["role_based", "resource_based", "policy_engine"],
                "data_protection": ["encryption_at_rest", "encryption_in_transit", "key_management"]
            },
            "validation_status": {
                "passed": True,
                "data_consistency": "validated",
                "flow_completeness": "comprehensive",
                "integration_coverage": "complete"
            },
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        
        # Mock circuit breaker and processing
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=comprehensive_result)
        root_system_architect_agent._circuit_breakers["design"] = mock_circuit
        
        root_system_architect_agent.process_with_validation = AsyncMock(return_value=comprehensive_result)
        root_system_architect_agent.standard_reflect = AsyncMock(return_value={
            "reflection_results": {"validation_status": {"passed": True}}
        })
        
        # Execute full workflow
        result = await root_system_architect_agent._process(
            sample_garden_planner_output, 
            sample_environment_analysis_output
        )
        
        # Verify comprehensive result
        assert result == comprehensive_result
        assert result["validation_status"]["passed"] is True
        assert result["data_architecture"]["data_entities"]["users"]["attributes"][0] == "id"
        assert root_system_architect_agent.development_state == DevelopmentState.COMPLETE
        
        # Verify all expected memory tracking occurred
        track_calls = root_system_architect_agent.track_dict_memory.call_args_list
        tracked_resources = [call[0][0] for call in track_calls]
        assert "garden_planner_input" in tracked_resources
        assert "environment_analysis_input" in tracked_resources
        assert "initial_design" in tracked_resources
        
        # Verify performance metrics were recorded
        metric_calls = root_system_architect_agent._metrics_manager.record_metric.call_args_list
        design_metrics = [call for call in metric_calls if "design_completed" in call[0][0]]
        assert len(design_metrics) > 0
        
        # Verify health reporting occurred throughout
        health_calls = root_system_architect_agent._report_agent_health.call_args_list
        assert len(health_calls) >= 2  # Processing start and completion
    
    async def test_architecture_refinement_cycle(
        self, 
        root_system_architect_agent, 
        sample_garden_planner_output, 
        sample_environment_analysis_output
    ):
        """Test architecture design with refinement cycle."""
        # Initial design with validation failure
        initial_result = {
            "data_architecture": {"incomplete": True},
            "validation_status": {"passed": False}
        }
        
        reflection_failure = {
            "reflection_results": {"validation_status": {"passed": False}}
        }
        
        # Mock circuit breaker and processing
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=initial_result)
        root_system_architect_agent._circuit_breakers["design"] = mock_circuit
        
        root_system_architect_agent.process_with_validation = AsyncMock(return_value=initial_result)
        root_system_architect_agent.standard_reflect = AsyncMock(return_value=reflection_failure)
        
        # Execute processing (should trigger refinement path)
        result = await root_system_architect_agent._process(
            sample_garden_planner_output, 
            sample_environment_analysis_output
        )
        
        # Verify refinement was triggered
        assert result == reflection_failure
        assert root_system_architect_agent.development_state == DevelopmentState.REFINING
        
        # Verify degraded health was reported
        health_calls = root_system_architect_agent._report_agent_health.call_args_list
        degraded_calls = [call for call in health_calls 
                         if call[1].get('custom_status') == 'DEGRADED']
        assert len(degraded_calls) > 0