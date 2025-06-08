"""
Unit tests for Tree Placement Planner Agent

Tests the core Phase One agent responsible for structural component architecture
with proper circuit breaker protection, memory monitoring, performance metrics,
component estimation, and health tracking.
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from phase_one.agents.tree_placement_planner import TreePlacementPlannerAgent
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
                "Order processing and payment",
                "Inventory management",
                "Admin dashboard",
                "Email notifications",
                "Search functionality"
            ]
        },
        "scope_definition": {
            "core_features": ["catalog", "cart", "orders", "payments", "inventory", "admin"],
            "optional_features": ["reviews", "recommendations", "analytics"],
            "technical_constraints": ["RESTful API", "PostgreSQL database", "React frontend"]
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
            }
        },
        "status": "success"
    }


@pytest.fixture
def sample_root_system_output():
    """Sample root system architect output for testing."""
    return {
        "data_architecture": {
            "data_entities": {
                "users": {"attributes": ["id", "email"], "relationships": ["orders"]},
                "products": {"attributes": ["id", "name", "price"], "relationships": ["categories"]},
                "orders": {"attributes": ["id", "user_id", "total"], "relationships": ["users", "products"]}
            },
            "data_flows": {
                "user_registration": {"source": "client", "destination": "user_service"},
                "product_catalog": {"source": "product_service", "destination": "client"}
            }
        },
        "status": "success"
    }


@pytest.fixture
def sample_minimal_inputs():
    """Minimal input samples for edge case testing."""
    return {
        "garden_planner": {
            "task_analysis": {
                "requirements": ["Basic functionality", "Simple UI"]
            }
        },
        "environment_analysis": {
            "environmental_analysis": {"runtime_requirements": {"basic": True}}
        },
        "root_system": {
            "data_architecture": {"data_entities": {"simple": {}}}
        }
    }


@pytest.fixture
def sample_large_inputs():
    """Large input samples for memory and performance testing."""
    return {
        "garden_planner": {
            "task_analysis": {
                "requirements": [f"requirement_{i}" for i in range(50)],
                "detailed_specs": {f"spec_{i}": f"value_{i}" for i in range(25)}
            }
        },
        "environment_analysis": {
            "environmental_analysis": {
                "runtime_requirements": {f"req_{i}": f"value_{i}" for i in range(30)},
                "deployment_requirements": {f"deploy_{i}": f"config_{i}" for i in range(30)}
            }
        },
        "root_system": {
            "data_architecture": {
                "data_entities": {f"entity_{i}": {"attributes": [f"attr_{j}" for j in range(5)]} for i in range(20)}
            }
        }
    }


@pytest.fixture
async def tree_placement_planner_agent(mock_resources):
    """Create a Tree Placement Planner Agent for testing."""
    agent = TreePlacementPlannerAgent(
        agent_id="tree_placement_test",
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


class TestTreePlacementPlannerAgentInitialization:
    """Test Tree Placement Planner Agent initialization."""
    
    async def test_initialization_success(self, mock_resources):
        """Test successful agent initialization."""
        agent = TreePlacementPlannerAgent(
            agent_id="test_tree_agent",
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
        assert agent.interface_id == "agent:test_tree_agent"
        assert agent.development_state == DevelopmentState.INITIALIZING
        assert isinstance(agent._prompt_config, AgentPromptConfig)
        
        # Verify prompt configuration
        assert agent._prompt_config.system_prompt_base_path == "FFTT_system_prompts/phase_one/tree_placement_planner_agent"
        assert agent._prompt_config.reflection_prompt_name == "structural_component_reflection_prompt"
        assert agent._prompt_config.refinement_prompt_name == "structural_component_refinement_prompt"
        assert agent._prompt_config.initial_prompt_name == "initial_structural_components_prompt"
        
        # Verify circuit breakers
        assert "component_design" in agent._circuit_breakers
        assert "processing" in agent._circuit_breakers  # Default from base class
        
        # Verify component design circuit breaker configuration (higher failure threshold)
        design_cb = agent.get_circuit_breaker("component_design")
        assert design_cb is not None
        
        # Verify performance tracking initialization
        assert agent._processing_times == []
        assert agent._component_counts == []
    
    async def test_initialization_memory_monitor_registration(self, mock_resources):
        """Test memory monitor registration with highest thresholds for component diagrams."""
        agent = TreePlacementPlannerAgent(
            agent_id="test_memory_tree",
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
        assert call_args[0][0] == "agent_test_memory_tree"
        
        # Verify memory thresholds (highest for component diagrams)
        thresholds = call_args[0][1]
        assert isinstance(thresholds, MemoryThresholds)
        assert thresholds.per_resource_max_mb == 120  # Highest threshold for component diagrams
        assert thresholds.warning_percent == 0.6
        assert thresholds.critical_percent == 0.85


class TestComponentEstimation:
    """Test component count estimation functionality."""
    
    async def test_component_estimation_from_requirements(self, tree_placement_planner_agent):
        """Test component count estimation based on requirements."""
        garden_planner_output = {
            "requirements": [
                "User authentication",
                "Product catalog", 
                "Shopping cart",
                "Order processing",
                "Payment handling",
                "Inventory management"
            ]
        }
        
        environment_analysis_output = {
            "runtime_requirements": {"performance": "high"}
        }
        
        # Test estimation method
        estimated_count = tree_placement_planner_agent._estimate_component_count(
            garden_planner_output, 
            environment_analysis_output
        )
        
        # Should estimate roughly 1 component per 2-3 requirements (6 requirements = ~3 components)
        assert estimated_count >= 3
        assert estimated_count <= 6
    
    async def test_component_estimation_minimal_requirements(self, tree_placement_planner_agent):
        """Test component estimation with minimal requirements."""
        garden_planner_output = {
            "requirements": ["Basic functionality"]
        }
        
        environment_analysis_output = {}
        
        estimated_count = tree_placement_planner_agent._estimate_component_count(
            garden_planner_output, 
            environment_analysis_output
        )
        
        # Should default to minimum of 3-5 components
        assert estimated_count >= 3
        assert estimated_count <= 5
    
    async def test_component_estimation_no_requirements(self, tree_placement_planner_agent):
        """Test component estimation with no requirements list."""
        garden_planner_output = {"other_data": "value"}
        environment_analysis_output = {}
        
        estimated_count = tree_placement_planner_agent._estimate_component_count(
            garden_planner_output, 
            environment_analysis_output
        )
        
        # Should fallback to safe default
        assert estimated_count == 5
    
    async def test_component_estimation_exception_handling(self, tree_placement_planner_agent):
        """Test component estimation exception handling."""
        malformed_garden_planner = None
        environment_analysis_output = {}
        
        estimated_count = tree_placement_planner_agent._estimate_component_count(
            malformed_garden_planner, 
            environment_analysis_output
        )
        
        # Should handle exceptions and return safe default
        assert estimated_count == 5


class TestComponentArchitectureDesign:
    """Test core component architecture design functionality."""
    
    async def test_successful_component_design(
        self, 
        tree_placement_planner_agent, 
        sample_garden_planner_output, 
        sample_environment_analysis_output,
        sample_root_system_output
    ):
        """Test successful component architecture design processing."""
        # Mock successful design result
        design_result = {
            "component_architecture": {
                "components": [
                    {
                        "id": "user_management",
                        "name": "User Management Component",
                        "description": "Handles user authentication, registration, and profile management",
                        "responsibilities": ["authentication", "registration", "profile_management"],
                        "interfaces": ["UserService", "AuthService"],
                        "dependencies": [],
                        "data_entities": ["users", "sessions"],
                        "estimated_complexity": "medium"
                    },
                    {
                        "id": "product_catalog",
                        "name": "Product Catalog Component",
                        "description": "Manages product information, categories, and search",
                        "responsibilities": ["product_management", "categorization", "search"],
                        "interfaces": ["ProductService", "SearchService"],
                        "dependencies": [],
                        "data_entities": ["products", "categories"],
                        "estimated_complexity": "medium"
                    },
                    {
                        "id": "order_processing",
                        "name": "Order Processing Component",
                        "description": "Handles order creation, processing, and fulfillment",
                        "responsibilities": ["order_creation", "order_processing", "fulfillment"],
                        "interfaces": ["OrderService", "PaymentService"],
                        "dependencies": ["user_management", "product_catalog"],
                        "data_entities": ["orders", "order_items"],
                        "estimated_complexity": "high"
                    }
                ],
                "component_relationships": {
                    "order_processing": {
                        "depends_on": ["user_management", "product_catalog"],
                        "interaction_patterns": ["api_calls", "event_messaging"]
                    }
                },
                "deployment_order": ["user_management", "product_catalog", "order_processing"],
                "integration_points": ["payment_gateway", "email_service"]
            },
            "architecture_metadata": {
                "total_components": 3,
                "complexity_distribution": {"low": 0, "medium": 2, "high": 1},
                "dependency_depth": 2,
                "estimated_development_time": "12 weeks"
            },
            "validation_status": {
                "passed": True,
                "component_coverage": "complete",
                "dependency_validation": "consistent"
            },
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        
        # Mock the circuit breaker and process_with_validation
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=design_result)
        tree_placement_planner_agent._circuit_breakers["component_design"] = mock_circuit
        
        tree_placement_planner_agent.process_with_validation = AsyncMock(return_value=design_result)
        tree_placement_planner_agent.standard_reflect = AsyncMock(return_value={
            "reflection_results": {
                "validation_status": {"passed": True}
            }
        })
        
        # Execute processing
        result = await tree_placement_planner_agent._process(
            sample_garden_planner_output, 
            sample_environment_analysis_output,
            sample_root_system_output
        )
        
        # Verify result
        assert result is not None
        assert result["component_architecture"]["components"][0]["id"] == "user_management"
        assert result["architecture_metadata"]["total_components"] == 3
        assert result["validation_status"]["passed"] is True
        assert tree_placement_planner_agent.development_state == DevelopmentState.COMPLETE
        
        # Verify circuit breaker was called
        mock_circuit.execute.assert_called_once()
        
        # Verify metrics were recorded
        tree_placement_planner_agent._metrics_manager.record_metric.assert_called()
        
        # Verify component count was tracked
        assert len(tree_placement_planner_agent._component_counts) == 1
        assert tree_placement_planner_agent._component_counts[0] == 3
        
        # Verify processing time was tracked
        assert len(tree_placement_planner_agent._processing_times) == 1
        assert tree_placement_planner_agent._processing_times[0] > 0
    
    async def test_component_design_validation_failure(
        self, 
        tree_placement_planner_agent, 
        sample_garden_planner_output, 
        sample_environment_analysis_output,
        sample_root_system_output
    ):
        """Test handling of validation failure during component design."""
        # Mock design result with validation failure
        design_result = {
            "component_architecture": {
                "components": [{"incomplete": True}]
            },
            "validation_status": {
                "passed": False,
                "issues": ["Missing component dependencies", "Incomplete component definitions"]
            },
            "status": "needs_refinement"
        }
        
        reflection_result = {
            "reflection_results": {
                "validation_status": {"passed": False},
                "issues": ["Component architecture incomplete", "Missing critical integrations"]
            },
            "refinement_needed": True
        }
        
        # Mock the circuit breaker and methods
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=design_result)
        tree_placement_planner_agent._circuit_breakers["component_design"] = mock_circuit
        
        tree_placement_planner_agent.process_with_validation = AsyncMock(return_value=design_result)
        tree_placement_planner_agent.standard_reflect = AsyncMock(return_value=reflection_result)
        
        # Execute processing
        result = await tree_placement_planner_agent._process(
            sample_garden_planner_output, 
            sample_environment_analysis_output,
            sample_root_system_output
        )
        
        # Verify result indicates refinement needed
        assert result == reflection_result
        assert tree_placement_planner_agent.development_state == DevelopmentState.REFINING
        
        # Verify health status was updated to degraded
        health_calls = [call for call in tree_placement_planner_agent._report_agent_health.call_args_list 
                       if call[1].get('custom_status') == 'DEGRADED']
        assert len(health_calls) > 0
    
    async def test_circuit_breaker_open(
        self, 
        tree_placement_planner_agent, 
        sample_garden_planner_output, 
        sample_environment_analysis_output,
        sample_root_system_output
    ):
        """Test handling when component design circuit breaker is open."""
        # Mock circuit breaker to raise CircuitOpenError
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(side_effect=CircuitOpenError("Component design circuit open"))
        tree_placement_planner_agent._circuit_breakers["component_design"] = mock_circuit
        
        # Execute processing
        result = await tree_placement_planner_agent._process(
            sample_garden_planner_output, 
            sample_environment_analysis_output,
            sample_root_system_output
        )
        
        # Verify safe failure handling
        assert result is not None
        assert result["error"] == "Component design rejected due to circuit breaker open"
        assert result["status"] == "failure"
        assert result["agent_id"] == tree_placement_planner_agent.interface_id
        assert tree_placement_planner_agent.development_state == DevelopmentState.ERROR
        
        # Verify critical health status was reported with circuit details
        health_calls = [call for call in tree_placement_planner_agent._report_agent_health.call_args_list 
                       if call[1].get('custom_status') == 'CRITICAL']
        assert len(health_calls) > 0
        
        critical_call = health_calls[0]
        metadata = critical_call[1]["metadata"]
        assert metadata["circuit"] == "component_design_circuit"
        assert metadata["circuit_state"] == "OPEN"


class TestMemoryTrackingAndManagement:
    """Test memory tracking and management with three input sources."""
    
    async def test_memory_tracking_three_inputs(
        self, 
        tree_placement_planner_agent, 
        sample_garden_planner_output, 
        sample_environment_analysis_output,
        sample_root_system_output
    ):
        """Test memory usage tracking for three input sources."""
        # Mock successful processing
        design_result = {
            "component_architecture": {"components": [{"test": True}]},
            "status": "success"
        }
        
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=design_result)
        tree_placement_planner_agent._circuit_breakers["component_design"] = mock_circuit
        
        tree_placement_planner_agent.process_with_validation = AsyncMock(return_value=design_result)
        tree_placement_planner_agent.standard_reflect = AsyncMock(return_value={
            "reflection_results": {"validation_status": {"passed": True}}
        })
        
        # Execute processing
        await tree_placement_planner_agent._process(
            sample_garden_planner_output, 
            sample_environment_analysis_output,
            sample_root_system_output
        )
        
        # Verify memory tracking calls for all three inputs
        track_calls = tree_placement_planner_agent.track_dict_memory.call_args_list
        tracked_resources = [call[0][0] for call in track_calls]
        
        assert "garden_planner_input" in tracked_resources
        assert "environment_analysis_input" in tracked_resources
        assert "root_system_input" in tracked_resources
        assert "initial_design" in tracked_resources
        
        # Verify total input size tracking (combining all three inputs)
        memory_calls = tree_placement_planner_agent.track_memory_usage.call_args_list
        total_input_calls = [call for call in memory_calls if call[0][0] == "total_input"]
        assert len(total_input_calls) > 0
    
    async def test_large_input_memory_tracking(self, tree_placement_planner_agent, sample_large_inputs):
        """Test memory tracking with large input data from all three sources."""
        # Mock successful processing
        design_result = {"component_architecture": {"processed": True}}
        
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=design_result)
        tree_placement_planner_agent._circuit_breakers["component_design"] = mock_circuit
        
        tree_placement_planner_agent.process_with_validation = AsyncMock(return_value=design_result)
        tree_placement_planner_agent.standard_reflect = AsyncMock(return_value={
            "reflection_results": {"validation_status": {"passed": True}}
        })
        
        # Execute processing with large inputs
        await tree_placement_planner_agent._process(
            sample_large_inputs["garden_planner"],
            sample_large_inputs["environment_analysis"],
            sample_large_inputs["root_system"]
        )
        
        # Verify memory tracking was called for large inputs
        track_calls = tree_placement_planner_agent.track_dict_memory.call_args_list
        assert len(track_calls) >= 4  # At least 4 tracking calls (3 inputs + 1 result)
        
        # Verify total input size calculation includes all three sources
        memory_calls = tree_placement_planner_agent.track_memory_usage.call_args_list
        total_input_calls = [call for call in memory_calls if call[0][0] == "total_input"]
        assert len(total_input_calls) > 0


class TestPerformanceMetrics:
    """Test performance metrics and component tracking functionality."""
    
    async def test_component_count_tracking(
        self, 
        tree_placement_planner_agent, 
        sample_garden_planner_output, 
        sample_environment_analysis_output,
        sample_root_system_output
    ):
        """Test component count tracking during processing."""
        # Mock design result with known component count
        design_result = {
            "component_architecture": {
                "components": [
                    {"id": "comp1", "name": "Component 1"},
                    {"id": "comp2", "name": "Component 2"},
                    {"id": "comp3", "name": "Component 3"},
                    {"id": "comp4", "name": "Component 4"}
                ]
            },
            "status": "success"
        }
        
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=design_result)
        tree_placement_planner_agent._circuit_breakers["component_design"] = mock_circuit
        
        tree_placement_planner_agent.process_with_validation = AsyncMock(return_value=design_result)
        tree_placement_planner_agent.standard_reflect = AsyncMock(return_value={
            "reflection_results": {"validation_status": {"passed": True}}
        })
        
        # Execute processing
        await tree_placement_planner_agent._process(
            sample_garden_planner_output, 
            sample_environment_analysis_output,
            sample_root_system_output
        )
        
        # Verify component count was tracked
        assert len(tree_placement_planner_agent._component_counts) == 1
        assert tree_placement_planner_agent._component_counts[0] == 4
        
        # Verify component creation metric was recorded
        metric_calls = tree_placement_planner_agent._metrics_manager.record_metric.call_args_list
        component_metrics = [call for call in metric_calls 
                            if "components_created" in call[0][0]]
        assert len(component_metrics) > 0
        
        # Verify metric value matches actual component count
        component_metric = component_metrics[0]
        assert component_metric[0][1] == 4  # Second argument is the value
    
    async def test_processing_time_tracking(
        self, 
        tree_placement_planner_agent, 
        sample_garden_planner_output, 
        sample_environment_analysis_output,
        sample_root_system_output
    ):
        """Test processing time tracking during component design."""
        # Mock successful processing
        design_result = {
            "component_architecture": {"components": [{"id": "test"}]},
            "status": "success"
        }
        
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=design_result)
        tree_placement_planner_agent._circuit_breakers["component_design"] = mock_circuit
        
        tree_placement_planner_agent.process_with_validation = AsyncMock(return_value=design_result)
        tree_placement_planner_agent.standard_reflect = AsyncMock(return_value={
            "reflection_results": {"validation_status": {"passed": True}}
        })
        
        # Execute processing
        await tree_placement_planner_agent._process(
            sample_garden_planner_output, 
            sample_environment_analysis_output,
            sample_root_system_output
        )
        
        # Verify processing time was tracked
        assert len(tree_placement_planner_agent._processing_times) == 1
        assert tree_placement_planner_agent._processing_times[0] > 0
        
        # Verify health report includes processing time
        health_calls = tree_placement_planner_agent._report_agent_health.call_args_list
        completion_calls = [call for call in health_calls 
                           if call[0][0] == "Component architecture design completed successfully"]
        assert len(completion_calls) > 0
        
        completion_call = completion_calls[0]
        metadata = completion_call[1]["metadata"]
        assert "processing_time" in metadata
        assert metadata["processing_time"] > 0
    
    async def test_get_performance_metrics(self, tree_placement_planner_agent):
        """Test getting performance metrics from the agent."""
        # Simulate some processing history
        tree_placement_planner_agent._processing_times = [1.5, 2.0, 1.8]
        tree_placement_planner_agent._component_counts = [3, 5, 4]
        
        # Get performance metrics
        metrics = await tree_placement_planner_agent.get_performance_metrics()
        
        # Verify metrics structure and calculations
        assert metrics["agent_id"] == tree_placement_planner_agent.interface_id
        assert metrics["avg_processing_time"] == 1.7666666666666666  # Average of [1.5, 2.0, 1.8]
        assert metrics["avg_component_count"] == 4.0  # Average of [3, 5, 4]
        assert metrics["total_designs"] == 3
        assert "timestamp" in metrics
    
    async def test_get_performance_metrics_empty_history(self, tree_placement_planner_agent):
        """Test getting performance metrics with no processing history."""
        # Ensure no processing history
        tree_placement_planner_agent._processing_times = []
        tree_placement_planner_agent._component_counts = []
        
        # Get performance metrics
        metrics = await tree_placement_planner_agent.get_performance_metrics()
        
        # Verify empty metrics
        assert metrics["agent_id"] == tree_placement_planner_agent.interface_id
        assert metrics["avg_processing_time"] == 0
        assert metrics["avg_component_count"] == 0
        assert metrics["total_designs"] == 0


class TestHealthReporting:
    """Test health reporting functionality with component estimation."""
    
    async def test_health_reporting_with_component_estimation(
        self, 
        tree_placement_planner_agent, 
        sample_garden_planner_output, 
        sample_environment_analysis_output,
        sample_root_system_output
    ):
        """Test health reporting includes component estimation."""
        # Mock successful processing
        design_result = {
            "component_architecture": {"components": [{"id": "test1"}, {"id": "test2"}]},
            "status": "success"
        }
        
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=design_result)
        tree_placement_planner_agent._circuit_breakers["component_design"] = mock_circuit
        
        tree_placement_planner_agent.process_with_validation = AsyncMock(return_value=design_result)
        tree_placement_planner_agent.standard_reflect = AsyncMock(return_value={
            "reflection_results": {"validation_status": {"passed": True}}
        })
        
        # Execute processing
        await tree_placement_planner_agent._process(
            sample_garden_planner_output, 
            sample_environment_analysis_output,
            sample_root_system_output
        )
        
        # Verify health was reported with component estimation
        health_calls = tree_placement_planner_agent._report_agent_health.call_args_list
        
        # Check for designing state health report with component estimation
        designing_calls = [call for call in health_calls 
                          if call[0][0] == "Designing component architecture"]
        assert len(designing_calls) > 0
        
        designing_call = designing_calls[0]
        metadata = designing_call[1]["metadata"]
        assert "estimated_components" in metadata
        assert metadata["estimated_components"] > 0
        
        # Check for completion state health report with actual component count
        completion_calls = [call for call in health_calls 
                           if call[0][0] == "Component architecture design completed successfully"]
        assert len(completion_calls) > 0
        
        completion_call = completion_calls[0]
        metadata = completion_call[1]["metadata"]
        assert "components" in metadata
        assert metadata["components"] == 2  # Actual component count


class TestReflectionAndRefinement:
    """Test reflection and refinement functionality."""
    
    async def test_reflection_delegation(self, tree_placement_planner_agent):
        """Test that reflection is delegated to standard method."""
        test_output = {"architecture": "test"}
        expected_result = {"reflection": "completed"}
        
        tree_placement_planner_agent.standard_reflect = AsyncMock(return_value=expected_result)
        
        result = await tree_placement_planner_agent.reflect(test_output)
        
        assert result == expected_result
        tree_placement_planner_agent.standard_reflect.assert_called_once_with(test_output, "component_design")
    
    async def test_refinement_delegation(self, tree_placement_planner_agent):
        """Test that refinement is delegated to standard method."""
        test_output = {"architecture": "test"}
        test_guidance = {"guidance": "improve"}
        expected_result = {"refined": "result"}
        
        tree_placement_planner_agent.standard_refine = AsyncMock(return_value=expected_result)
        
        result = await tree_placement_planner_agent.refine(test_output, test_guidance)
        
        assert result == expected_result
        tree_placement_planner_agent.standard_refine.assert_called_once_with(
            test_output, test_guidance, "component_design"
        )


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    async def test_minimal_input_processing(self, tree_placement_planner_agent, sample_minimal_inputs):
        """Test processing with minimal input data."""
        # Mock successful processing with minimal data
        design_result = {
            "component_architecture": {
                "components": [{"id": "basic_component", "name": "Basic Component"}],
                "metadata": {"minimal": True}
            },
            "status": "success"
        }
        
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=design_result)
        tree_placement_planner_agent._circuit_breakers["component_design"] = mock_circuit
        
        tree_placement_planner_agent.process_with_validation = AsyncMock(return_value=design_result)
        tree_placement_planner_agent.standard_reflect = AsyncMock(return_value={
            "reflection_results": {"validation_status": {"passed": True}}
        })
        
        # Execute processing
        result = await tree_placement_planner_agent._process(
            sample_minimal_inputs["garden_planner"],
            sample_minimal_inputs["environment_analysis"],
            sample_minimal_inputs["root_system"]
        )
        
        # Verify processing succeeds with minimal input
        assert result is not None
        assert result["component_architecture"]["components"][0]["id"] == "basic_component"
        
        # Verify component count tracking worked with minimal data
        assert len(tree_placement_planner_agent._component_counts) == 1
        assert tree_placement_planner_agent._component_counts[0] == 1
    
    async def test_empty_component_architecture_result(
        self, 
        tree_placement_planner_agent, 
        sample_garden_planner_output, 
        sample_environment_analysis_output,
        sample_root_system_output
    ):
        """Test handling when component architecture result has no components."""
        # Mock result with empty components list
        design_result = {
            "component_architecture": {
                "components": []  # Empty components list
            },
            "status": "success"
        }
        
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=design_result)
        tree_placement_planner_agent._circuit_breakers["component_design"] = mock_circuit
        
        tree_placement_planner_agent.process_with_validation = AsyncMock(return_value=design_result)
        tree_placement_planner_agent.standard_reflect = AsyncMock(return_value={
            "reflection_results": {"validation_status": {"passed": True}}
        })
        
        # Execute processing
        result = await tree_placement_planner_agent._process(
            sample_garden_planner_output, 
            sample_environment_analysis_output,
            sample_root_system_output
        )
        
        # Verify processing handles empty component list
        assert result is not None
        assert result["component_architecture"]["components"] == []
        
        # Verify component count tracking handled empty list
        assert len(tree_placement_planner_agent._component_counts) == 1
        assert tree_placement_planner_agent._component_counts[0] == 0
    
    async def test_malformed_component_architecture_result(
        self, 
        tree_placement_planner_agent, 
        sample_garden_planner_output, 
        sample_environment_analysis_output,
        sample_root_system_output
    ):
        """Test handling when component architecture result is malformed."""
        # Mock result without component_architecture key
        design_result = {
            "other_data": "value",
            "status": "success"
        }
        
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=design_result)
        tree_placement_planner_agent._circuit_breakers["component_design"] = mock_circuit
        
        tree_placement_planner_agent.process_with_validation = AsyncMock(return_value=design_result)
        tree_placement_planner_agent.standard_reflect = AsyncMock(return_value={
            "reflection_results": {"validation_status": {"passed": True}}
        })
        
        # Execute processing
        result = await tree_placement_planner_agent._process(
            sample_garden_planner_output, 
            sample_environment_analysis_output,
            sample_root_system_output
        )
        
        # Verify processing handles malformed result gracefully
        assert result is not None
        
        # Verify component count defaulted to 0 for malformed result
        assert len(tree_placement_planner_agent._component_counts) == 1
        assert tree_placement_planner_agent._component_counts[0] == 0


class TestIntegrationScenarios:
    """Test integration scenarios and realistic workflows."""
    
    async def test_complete_component_architecture_workflow(
        self, 
        tree_placement_planner_agent, 
        sample_garden_planner_output, 
        sample_environment_analysis_output,
        sample_root_system_output
    ):
        """Test complete component architecture workflow from start to finish."""
        # Mock comprehensive component architecture result
        comprehensive_result = {
            "component_architecture": {
                "components": [
                    {
                        "id": "authentication_service",
                        "name": "Authentication Service",
                        "description": "Handles user authentication, authorization, and session management",
                        "responsibilities": [
                            "user_login", "user_registration", "password_management", 
                            "session_handling", "token_generation", "permission_checking"
                        ],
                        "interfaces": ["AuthAPI", "UserAPI", "SessionAPI"],
                        "dependencies": [],
                        "data_entities": ["users", "sessions", "permissions"],
                        "technology_stack": ["Node.js", "JWT", "bcrypt"],
                        "estimated_complexity": "medium",
                        "estimated_development_time": "3 weeks"
                    },
                    {
                        "id": "product_catalog_service",
                        "name": "Product Catalog Service",
                        "description": "Manages product information, categories, inventory, and search functionality",
                        "responsibilities": [
                            "product_management", "category_management", "inventory_tracking",
                            "product_search", "price_management", "product_recommendations"
                        ],
                        "interfaces": ["ProductAPI", "SearchAPI", "InventoryAPI"],
                        "dependencies": [],
                        "data_entities": ["products", "categories", "inventory", "product_images"],
                        "technology_stack": ["Node.js", "Elasticsearch", "PostgreSQL"],
                        "estimated_complexity": "high",
                        "estimated_development_time": "4 weeks"
                    },
                    {
                        "id": "order_management_service",
                        "name": "Order Management Service",
                        "description": "Handles order processing, payment integration, and fulfillment",
                        "responsibilities": [
                            "order_creation", "order_processing", "payment_handling",
                            "order_tracking", "fulfillment_coordination", "refund_processing"
                        ],
                        "interfaces": ["OrderAPI", "PaymentAPI", "FulfillmentAPI"],
                        "dependencies": ["authentication_service", "product_catalog_service"],
                        "data_entities": ["orders", "order_items", "payments", "shipments"],
                        "technology_stack": ["Node.js", "Stripe", "PostgreSQL"],
                        "estimated_complexity": "high",
                        "estimated_development_time": "5 weeks"
                    },
                    {
                        "id": "admin_dashboard_service",
                        "name": "Admin Dashboard Service",
                        "description": "Provides administrative interface and management capabilities",
                        "responsibilities": [
                            "user_management", "product_administration", "order_monitoring",
                            "analytics_dashboard", "system_configuration", "reporting"
                        ],
                        "interfaces": ["AdminAPI", "AnalyticsAPI", "ReportingAPI"],
                        "dependencies": ["authentication_service", "product_catalog_service", "order_management_service"],
                        "data_entities": ["admin_users", "system_configs", "audit_logs"],
                        "technology_stack": ["React", "Node.js", "Chart.js"],
                        "estimated_complexity": "medium",
                        "estimated_development_time": "3 weeks"
                    }
                ],
                "component_relationships": {
                    "order_management_service": {
                        "depends_on": ["authentication_service", "product_catalog_service"],
                        "interaction_patterns": ["REST_API", "event_messaging"],
                        "data_flow": ["user_verification", "product_validation", "inventory_check"]
                    },
                    "admin_dashboard_service": {
                        "depends_on": ["authentication_service", "product_catalog_service", "order_management_service"],
                        "interaction_patterns": ["REST_API", "WebSocket"],
                        "data_flow": ["admin_authentication", "data_aggregation", "real_time_updates"]
                    }
                },
                "deployment_order": [
                    "authentication_service",
                    "product_catalog_service", 
                    "order_management_service",
                    "admin_dashboard_service"
                ],
                "integration_points": {
                    "external_services": ["stripe_payment", "sendgrid_email", "cloudinary_images"],
                    "databases": ["postgresql_primary", "redis_cache", "elasticsearch_search"],
                    "monitoring": ["prometheus", "grafana", "elk_stack"]
                }
            },
            "architecture_metadata": {
                "total_components": 4,
                "complexity_distribution": {"low": 0, "medium": 2, "high": 2},
                "dependency_depth": 3,
                "estimated_total_development_time": "15 weeks",
                "technology_stack": ["Node.js", "React", "PostgreSQL", "Redis", "Elasticsearch"],
                "deployment_complexity": "medium",
                "scalability_considerations": ["microservices", "load_balancing", "database_sharding"]
            },
            "quality_assurance": {
                "testing_strategy": ["unit_tests", "integration_tests", "end_to_end_tests"],
                "code_quality": ["linting", "code_review", "static_analysis"],
                "monitoring": ["health_checks", "performance_metrics", "error_tracking"]
            },
            "validation_status": {
                "passed": True,
                "component_coverage": "complete",
                "dependency_validation": "consistent",
                "interface_completeness": "verified"
            },
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        
        # Mock circuit breaker and processing
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value=comprehensive_result)
        tree_placement_planner_agent._circuit_breakers["component_design"] = mock_circuit
        
        tree_placement_planner_agent.process_with_validation = AsyncMock(return_value=comprehensive_result)
        tree_placement_planner_agent.standard_reflect = AsyncMock(return_value={
            "reflection_results": {"validation_status": {"passed": True}}
        })
        
        # Execute full workflow
        result = await tree_placement_planner_agent._process(
            sample_garden_planner_output, 
            sample_environment_analysis_output,
            sample_root_system_output
        )
        
        # Verify comprehensive result
        assert result == comprehensive_result
        assert result["validation_status"]["passed"] is True
        assert result["architecture_metadata"]["total_components"] == 4
        assert tree_placement_planner_agent.development_state == DevelopmentState.COMPLETE
        
        # Verify all expected memory tracking occurred
        track_calls = tree_placement_planner_agent.track_dict_memory.call_args_list
        tracked_resources = [call[0][0] for call in track_calls]
        assert "garden_planner_input" in tracked_resources
        assert "environment_analysis_input" in tracked_resources
        assert "root_system_input" in tracked_resources
        assert "initial_design" in tracked_resources
        
        # Verify component count tracking
        assert len(tree_placement_planner_agent._component_counts) == 1
        assert tree_placement_planner_agent._component_counts[0] == 4
        
        # Verify performance metrics were recorded
        metric_calls = tree_placement_planner_agent._metrics_manager.record_metric.call_args_list
        component_metrics = [call for call in metric_calls if "components_created" in call[0][0]]
        assert len(component_metrics) > 0
        
        # Verify performance metrics can be retrieved
        performance_metrics = await tree_placement_planner_agent.get_performance_metrics()
        assert performance_metrics["total_designs"] == 1
        assert performance_metrics["avg_component_count"] == 4.0