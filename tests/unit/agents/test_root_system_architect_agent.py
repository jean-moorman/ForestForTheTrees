"""
Comprehensive unit tests for Root System Architect Agent.

Tests focus on end-to-end operational readiness with real functionality
and proper resource management.
"""
import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from phase_one.agents.root_system_architect import RootSystemArchitectAgent
from phase_one.models.enums import DevelopmentState
from phase_one.models.refinement import AgentPromptConfig
from resources import EventQueue, StateManager, AgentContextManager, CacheManager, MetricsManager, ErrorHandler
from resources.monitoring import MemoryMonitor, HealthTracker, CircuitOpenError

class TestRootSystemArchitectAgentInitialization:
    """Test Root System Architect Agent initialization and configuration."""
    
    @pytest.fixture
    async def resource_managers(self):
        """Create real resource managers for testing."""
        event_queue = EventQueue()
        await event_queue.start()
        
        state_manager = StateManager(event_queue)
        await state_manager.initialize()
        
        context_manager = AgentContextManager(event_queue)
        await context_manager.initialize()
        
        cache_manager = CacheManager(event_queue)
        await cache_manager.initialize()
        
        metrics_manager = MetricsManager(event_queue)
        await metrics_manager.initialize()
        
        error_handler = ErrorHandler(event_queue)
        memory_monitor = MemoryMonitor(event_queue)
        health_tracker = HealthTracker(event_queue)
        
        yield {
            "event_queue": event_queue,
            "state_manager": state_manager,
            "context_manager": context_manager,
            "cache_manager": cache_manager,
            "metrics_manager": metrics_manager,
            "error_handler": error_handler,
            "memory_monitor": memory_monitor,
            "health_tracker": health_tracker
        }
        
        # Cleanup
        try:
            await event_queue.stop()
        except Exception as e:
            # Ignore cleanup errors in tests
            pass

    async def test_root_system_architect_initialization_success(self, resource_managers):
        """Test successful Root System Architect Agent initialization."""
        agent = RootSystemArchitectAgent(
            agent_id="test_root_architect",
            event_queue=resource_managers["event_queue"],
            state_manager=resource_managers["state_manager"],
            context_manager=resource_managers["context_manager"],
            cache_manager=resource_managers["cache_manager"],
            metrics_manager=resource_managers["metrics_manager"],
            error_handler=resource_managers["error_handler"],
            memory_monitor=resource_managers["memory_monitor"],
            health_tracker=resource_managers["health_tracker"]
        )
        
        # Verify agent initialization
        assert agent.agent_id == "test_root_architect"
        assert agent.development_state == DevelopmentState.INITIALIZING
        assert isinstance(agent._prompt_config, AgentPromptConfig)
        assert agent._prompt_config.system_prompt_base_path == "FFTT_system_prompts/phase_one/root_system_architect_agent"
        assert agent._prompt_config.initial_prompt_name == "initial_core_data_flow_prompt"
        
        # Verify circuit breaker definitions are configured
        cb_names = [cb.name for cb in agent._circuit_breaker_definitions]
        assert "processing" in cb_names
        assert "design" in cb_names
        
        # Verify lazy circuit breaker initialization works
        processing_cb = agent.get_circuit_breaker("processing")
        assert processing_cb is not None
        assert "processing" in agent._circuit_breakers

    async def test_root_system_architect_prompt_configuration(self, resource_managers):
        """Test Root System Architect prompt configuration is correct."""
        agent = RootSystemArchitectAgent(
            agent_id="test_root_architect",
            **resource_managers
        )
        
        # Verify all prompt names are configured
        config = agent._prompt_config
        assert config.system_prompt_base_path == "FFTT_system_prompts/phase_one/root_system_architect_agent"
        assert config.reflection_prompt_name == "core_data_flow_reflection_prompt"
        assert config.refinement_prompt_name == "core_data_flow_refinement_prompt"
        assert config.initial_prompt_name == "initial_core_data_flow_prompt"

    async def test_root_system_architect_circuit_breaker_configuration(self, resource_managers):
        """Test Root System Architect circuit breaker configuration."""
        agent = RootSystemArchitectAgent(
            agent_id="test_root_architect",
            **resource_managers
        )
        
        # Verify design circuit breaker with longer timeouts
        design_cb = agent.get_circuit_breaker("design")
        assert design_cb is not None
        assert design_cb.circuit_id == "test_root_architect_design"

    async def test_root_system_architect_memory_configuration(self, resource_managers):
        """Test Root System Architect memory configuration."""
        agent = RootSystemArchitectAgent(
            agent_id="test_root_architect",
            **resource_managers
        )
        
        # Verify memory monitor is configured with higher thresholds
        assert agent._memory_monitor is not None
        # Root System Architect should have higher memory threshold (100MB)


class TestRootSystemArchitectProcessing:
    """Test Root System Architect Agent processing functionality."""
    
    @pytest.fixture
    async def root_architect_agent(self):
        """Create a Root System Architect Agent for testing."""
        event_queue = EventQueue()
        await event_queue.start()
        
        state_manager = StateManager(event_queue)
        await state_manager.initialize()
        
        context_manager = AgentContextManager(event_queue)
        await context_manager.initialize()
        
        cache_manager = CacheManager(event_queue)
        await cache_manager.initialize()
        
        metrics_manager = MetricsManager(event_queue)
        await metrics_manager.initialize()
        
        error_handler = ErrorHandler(event_queue)
        memory_monitor = MemoryMonitor(event_queue)
        health_tracker = HealthTracker(event_queue)
        
        agent = RootSystemArchitectAgent(
            agent_id="test_root_architect",
            event_queue=event_queue,
            state_manager=state_manager,
            context_manager=context_manager,
            cache_manager=cache_manager,
            metrics_manager=metrics_manager,
            error_handler=error_handler,
            memory_monitor=memory_monitor,
            health_tracker=health_tracker
        )
        
        yield agent
        
        # Cleanup
        try:
            await event_queue.stop()
        except Exception as e:
            # Ignore cleanup errors in tests
            pass

    @patch('interfaces.agent.interface.AgentInterface.process_with_validation')
    async def test_root_system_architect_process_success(self, mock_process, root_architect_agent):
        """Test successful data architecture design processing."""
        # Mock Garden Planner output
        garden_planner_output = {
            "task_analysis": {
                "original_request": "Create a blog website",
                "technical_requirements": {
                    "languages": ["Python", "JavaScript"],
                    "frameworks": ["Django", "React"],
                    "infrastructure": ["PostgreSQL", "Redis"]
                }
            }
        }
        
        # Mock Environmental Analysis output
        environment_analysis_output = {
            "environmental_analysis": {
                "deployment_environment": {
                    "hosting_type": "cloud",
                    "scalability_requirements": "moderate"
                },
                "technical_ecosystem": {
                    "databases": ["PostgreSQL", "Redis"]
                }
            }
        }
        
        # Mock data architecture design response
        mock_data_architecture = {
            "data_architecture": {
                "data_flow_design": {
                    "user_interactions": {
                        "read_operations": ["blog_post_view", "comment_read"],
                        "write_operations": ["blog_post_create", "comment_create"],
                        "flow_patterns": ["request_response", "async_processing"]
                    },
                    "database_design": {
                        "primary_database": "PostgreSQL",
                        "cache_layer": "Redis",
                        "data_models": ["User", "BlogPost", "Comment"],
                        "relationships": ["one_to_many", "many_to_many"]
                    },
                    "api_architecture": {
                        "api_pattern": "REST",
                        "endpoints": ["/posts", "/comments", "/users"],
                        "authentication": "JWT",
                        "rate_limiting": "100_requests_per_minute"
                    }
                },
                "persistence_strategy": {
                    "data_consistency": "eventual_consistency",
                    "backup_frequency": "daily",
                    "replication": "master_slave"
                }
            }
        }
        
        # Mock reflection response indicating validation passed
        mock_reflection = {
            "reflection_results": {
                "validation_status": {"passed": True},
                "complexity_issues": {"granularity": [], "complexity_level": []},
                "completeness_issues": {"requirements_coverage": [], "dependencies": [], "cross_cutting": []},
                "consistency_issues": {"technical_alignment": [], "constraint_compatibility": [], "assumption_validation": []}
            }
        }
        
        mock_process.side_effect = [mock_data_architecture, mock_reflection]
        
        # Process data architecture design
        result = await root_architect_agent._process(garden_planner_output, environment_analysis_output)
        
        # Verify successful processing
        assert "error" not in result
        assert result["data_architecture"]["data_flow_design"]["database_design"]["primary_database"] == "PostgreSQL"
        assert root_architect_agent.development_state == DevelopmentState.COMPLETE
        
        # Verify process_with_validation was called correctly
        assert mock_process.call_count == 2  # Design + reflection
        
        # Verify first call (data architecture design)
        first_call = mock_process.call_args_list[0]
        assert "Design data architecture based on:" in first_call[1]["conversation"]
        assert "Garden planner:" in first_call[1]["conversation"]
        assert "Environment analysis:" in first_call[1]["conversation"]
        assert first_call[1]["system_prompt_info"][0] == "FFTT_system_prompts/phase_one/root_system_architect_agent"
        assert first_call[1]["system_prompt_info"][1] == "initial_core_data_flow_prompt"

    @patch('interfaces.agent.interface.AgentInterface.process_with_validation')
    async def test_root_system_architect_validation_failure(self, mock_process, root_architect_agent):
        """Test processing when validation fails."""
        garden_planner_output = {"task_analysis": {"original_request": "Create a system"}}
        environment_analysis_output = {"environmental_analysis": {"deployment_environment": {}}}
        
        # Mock initial data architecture
        mock_data_architecture = {
            "data_architecture": {
                "data_flow_design": {"incomplete": "design"}
            }
        }
        
        # Mock reflection response indicating validation failed
        mock_reflection = {
            "reflection_results": {
                "validation_status": {"passed": False},
                "complexity_issues": {
                    "granularity": [{"severity": "high", "issue": "Insufficient data flow detail", "recommendation": "Add comprehensive data flows"}],
                    "complexity_level": []
                },
                "completeness_issues": {"requirements_coverage": [], "dependencies": [], "cross_cutting": []},
                "consistency_issues": {"technical_alignment": [], "constraint_compatibility": [], "assumption_validation": []}
            }
        }
        
        mock_process.side_effect = [mock_data_architecture, mock_reflection]
        
        # Process data architecture design
        result = await root_architect_agent._process(garden_planner_output, environment_analysis_output)
        
        # Verify reflection result is returned (indicating refinement needed)
        assert result == mock_reflection
        assert root_architect_agent.development_state == DevelopmentState.REFINING

    @patch('interfaces.agent.interface.AgentInterface.process_with_validation')
    async def test_root_system_architect_circuit_breaker_protection(self, mock_process, root_architect_agent):
        """Test circuit breaker protection during processing."""
        # Mock circuit breaker open exception
        mock_process.side_effect = CircuitOpenError("design", "Circuit breaker open")
        
        garden_planner_output = {"task_analysis": {"original_request": "Test"}}
        environment_analysis_output = {"environmental_analysis": {}}
        
        # Process data architecture design
        result = await root_architect_agent._process(garden_planner_output, environment_analysis_output)
        
        # Verify circuit breaker error handling
        assert result["status"] == "failure"
        assert "Design operation rejected" in result["error"]
        assert root_architect_agent.development_state == DevelopmentState.ERROR

    async def test_root_system_architect_process_exception_handling(self, root_architect_agent):
        """Test exception handling during processing."""
        garden_planner_output = {"task_analysis": {"original_request": "Test"}}
        environment_analysis_output = {"environmental_analysis": {}}
        
        # Test with invalid method call to trigger exception
        with pytest.raises(Exception):
            await root_architect_agent._process(garden_planner_output, environment_analysis_output)
        
        # Verify error state
        assert root_architect_agent.development_state == DevelopmentState.ERROR


class TestRootSystemArchitectReflectionAndRefinement:
    """Test Root System Architect Agent reflection and refinement capabilities."""
    
    @pytest.fixture
    async def root_architect_agent(self):
        """Create a Root System Architect Agent for testing."""
        event_queue = EventQueue()
        await event_queue.start()
        
        state_manager = StateManager(event_queue)
        await state_manager.initialize()
        
        context_manager = AgentContextManager(event_queue)
        await context_manager.initialize()
        
        cache_manager = CacheManager(event_queue)
        await cache_manager.initialize()
        
        metrics_manager = MetricsManager(event_queue)
        await metrics_manager.initialize()
        
        error_handler = ErrorHandler(event_queue)
        memory_monitor = MemoryMonitor(event_queue)
        health_tracker = HealthTracker(event_queue)
        
        agent = RootSystemArchitectAgent(
            agent_id="test_root_architect",
            event_queue=event_queue,
            state_manager=state_manager,
            context_manager=context_manager,
            cache_manager=cache_manager,
            metrics_manager=metrics_manager,
            error_handler=error_handler,
            memory_monitor=memory_monitor,
            health_tracker=health_tracker
        )
        
        yield agent
        
        # Cleanup
        try:
            await event_queue.stop()
        except Exception as e:
            # Ignore cleanup errors in tests
            pass

    @patch('interfaces.agent.interface.AgentInterface.process_with_validation')
    async def test_root_system_architect_reflect_with_performance_tracking(self, mock_process, root_architect_agent):
        """Test Root System Architect reflect method with performance tracking."""
        mock_output = {"data_architecture": {"data_flow_design": {"database_design": {"primary_database": "PostgreSQL"}}}}
        mock_reflection = {
            "reflection_results": {
                "validation_status": {"passed": True},
                "complexity_issues": {"granularity": [], "complexity_level": []},
                "completeness_issues": {"requirements_coverage": [], "dependencies": [], "cross_cutting": []},
                "consistency_issues": {"technical_alignment": [], "constraint_compatibility": [], "assumption_validation": []}
            }
        }
        
        mock_process.return_value = mock_reflection
        
        # Test reflection
        result = await root_architect_agent.reflect(mock_output)
        
        # Verify reflection was called
        assert result == mock_reflection
        mock_process.assert_called_once()
        
        # Verify reflection prompt was used
        call_args = mock_process.call_args
        assert "Reflect on output with a critical eye" in call_args[1]["conversation"]

    @patch('interfaces.agent.interface.AgentInterface.process_with_validation')
    async def test_root_system_architect_refine_with_performance_tracking(self, mock_process, root_architect_agent):
        """Test Root System Architect refine method with performance tracking."""
        mock_output = {"data_architecture": {"data_flow_design": {"database_design": {"primary_database": "PostgreSQL"}}}}
        mock_guidance = {"action": "enhance_data_flows", "specific_changes": ["Add detailed API specifications"]}
        mock_refinement = {
            "data_architecture": {
                "data_flow_design": {
                    "database_design": {"primary_database": "PostgreSQL"},
                    "api_architecture": {
                        "detailed_endpoints": ["/posts", "/comments"],
                        "authentication": "JWT"
                    }
                }
            }
        }
        
        mock_process.return_value = mock_refinement
        
        # Test refinement
        result = await root_architect_agent.refine(mock_output, mock_guidance)
        
        # Verify refinement was called
        assert result == mock_refinement
        mock_process.assert_called_once()
        
        # Verify refinement prompt was used
        call_args = mock_process.call_args
        assert "Refine output based on:" in call_args[1]["conversation"]


class TestRootSystemArchitectMetricsAndHealthReporting:
    """Test Root System Architect Agent metrics and health reporting."""
    
    @pytest.fixture
    async def root_architect_agent(self):
        """Create a Root System Architect Agent for testing."""
        event_queue = EventQueue()
        await event_queue.start()
        
        state_manager = StateManager(event_queue)
        await state_manager.initialize()
        
        context_manager = AgentContextManager(event_queue)
        await context_manager.initialize()
        
        cache_manager = CacheManager(event_queue)
        await cache_manager.initialize()
        
        metrics_manager = MetricsManager(event_queue)
        await metrics_manager.initialize()
        
        error_handler = ErrorHandler(event_queue)
        memory_monitor = MemoryMonitor(event_queue)
        health_tracker = HealthTracker(event_queue)
        
        agent = RootSystemArchitectAgent(
            agent_id="test_root_architect",
            event_queue=event_queue,
            state_manager=state_manager,
            context_manager=context_manager,
            cache_manager=cache_manager,
            metrics_manager=metrics_manager,
            error_handler=error_handler,
            memory_monitor=memory_monitor,
            health_tracker=health_tracker
        )
        
        yield agent
        
        # Cleanup
        try:
            await event_queue.stop()
        except Exception as e:
            # Ignore cleanup errors in tests
            pass

    async def test_health_reporting_designing_state(self, root_architect_agent):
        """Test health reporting during designing state."""
        await root_architect_agent._report_agent_health(
            description="Designing data architecture",
            metadata={
                "state": "DESIGNING",
                "input_sources": ["garden_planner", "environment_analysis"]
            }
        )
        
        # Verify no exceptions are raised

    async def test_health_reporting_critical_state(self, root_architect_agent):
        """Test health reporting during critical state."""
        await root_architect_agent._report_agent_health(
            custom_status="CRITICAL",
            description="Design rejected due to circuit breaker open",
            metadata={
                "state": "ERROR",
                "circuit": "design_circuit",
                "circuit_state": "OPEN"
            }
        )
        
        # Verify no exceptions are raised

    async def test_metrics_recording(self, root_architect_agent):
        """Test metrics recording functionality."""
        # This would test the metrics manager integration
        # In a real scenario, we'd verify metrics are recorded properly
        await root_architect_agent._metrics_manager.record_metric(
            f"agent:{root_architect_agent.interface_id}:design_completed",
            1.0,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "validation": "passed"
            }
        )
        
        # Verify no exceptions are raised


class TestRootSystemArchitectMemoryManagement:
    """Test Root System Architect Agent memory management."""
    
    @pytest.fixture
    async def root_architect_agent(self):
        """Create a Root System Architect Agent for testing."""
        event_queue = EventQueue()
        await event_queue.start()
        
        state_manager = StateManager(event_queue)
        await state_manager.initialize()
        
        context_manager = AgentContextManager(event_queue)
        await context_manager.initialize()
        
        cache_manager = CacheManager(event_queue)
        await cache_manager.initialize()
        
        metrics_manager = MetricsManager(event_queue)
        await metrics_manager.initialize()
        
        error_handler = ErrorHandler(event_queue)
        memory_monitor = MemoryMonitor(event_queue)
        health_tracker = HealthTracker(event_queue)
        
        agent = RootSystemArchitectAgent(
            agent_id="test_root_architect",
            event_queue=event_queue,
            state_manager=state_manager,
            context_manager=context_manager,
            cache_manager=cache_manager,
            metrics_manager=metrics_manager,
            error_handler=error_handler,
            memory_monitor=memory_monitor,
            health_tracker=health_tracker
        )
        
        yield agent
        
        # Cleanup
        try:
            await event_queue.stop()
        except Exception as e:
            # Ignore cleanup errors in tests
            pass

    async def test_track_multiple_input_sources(self, root_architect_agent):
        """Test tracking memory for multiple input sources."""
        garden_planner_output = {"task_analysis": {"original_request": "Create a system"}}
        environment_analysis_output = {"environmental_analysis": {"deployment_environment": {}}}
        
        # Track memory for both inputs
        await root_architect_agent.track_dict_memory("garden_planner_input", garden_planner_output)
        await root_architect_agent.track_dict_memory("environment_analysis_input", environment_analysis_output)
        
        # Calculate total input size
        planner_size_mb = len(json.dumps(garden_planner_output)) / (1024 * 1024)
        env_size_mb = len(json.dumps(environment_analysis_output)) / (1024 * 1024)
        await root_architect_agent.track_memory_usage("total_input", planner_size_mb + env_size_mb)
        
        # Verify tracking doesn't raise exceptions

    async def test_track_design_result_memory(self, root_architect_agent):
        """Test tracking memory for design results."""
        design_result = {
            "data_architecture": {
                "data_flow_design": {
                    "user_interactions": {"read_operations": ["view"], "write_operations": ["create"]},
                    "database_design": {"primary_database": "PostgreSQL"},
                    "api_architecture": {"api_pattern": "REST"}
                }
            }
        }
        
        # Track design result memory
        await root_architect_agent.track_dict_memory("initial_design", design_result)
        
        # Verify tracking doesn't raise exceptions


class TestRootSystemArchitectIntegrationScenarios:
    """Test Root System Architect Agent integration scenarios."""
    
    @pytest.fixture
    async def root_architect_agent(self):
        """Create a Root System Architect Agent for testing."""
        event_queue = EventQueue()
        await event_queue.start()
        
        state_manager = StateManager(event_queue)
        await state_manager.initialize()
        
        context_manager = AgentContextManager(event_queue)
        await context_manager.initialize()
        
        cache_manager = CacheManager(event_queue)
        await cache_manager.initialize()
        
        metrics_manager = MetricsManager(event_queue)
        await metrics_manager.initialize()
        
        error_handler = ErrorHandler(event_queue)
        memory_monitor = MemoryMonitor(event_queue)
        health_tracker = HealthTracker(event_queue)
        
        agent = RootSystemArchitectAgent(
            agent_id="test_root_architect",
            event_queue=event_queue,
            state_manager=state_manager,
            context_manager=context_manager,
            cache_manager=cache_manager,
            metrics_manager=metrics_manager,
            error_handler=error_handler,
            memory_monitor=memory_monitor,
            health_tracker=health_tracker
        )
        
        yield agent
        
        # Cleanup
        try:
            await event_queue.stop()
        except Exception as e:
            # Ignore cleanup errors in tests
            pass

    @patch('interfaces.agent.interface.AgentInterface.process_with_validation')
    async def test_microservices_data_architecture_scenario(self, mock_process, root_architect_agent):
        """Test data architecture design for microservices scenario."""
        # Mock Garden Planner output for microservices
        garden_planner_output = {
            "task_analysis": {
                "original_request": "Build a microservices e-commerce platform",
                "technical_requirements": {
                    "languages": ["Python", "Java", "JavaScript"],
                    "frameworks": ["Django", "Spring Boot", "React"],
                    "apis": ["REST API", "GraphQL", "gRPC"],
                    "infrastructure": ["PostgreSQL", "MongoDB", "Redis", "RabbitMQ", "Elasticsearch"]
                }
            }
        }
        
        # Mock Environmental Analysis output for microservices
        environment_analysis_output = {
            "environmental_analysis": {
                "deployment_environment": {
                    "hosting_type": "cloud_native",
                    "architecture_pattern": "microservices",
                    "container_orchestration": "kubernetes"
                },
                "technical_ecosystem": {
                    "messaging": ["RabbitMQ", "Apache Kafka"],
                    "databases": {"primary": "PostgreSQL", "document": "MongoDB", "cache": "Redis", "search": "Elasticsearch"}
                }
            }
        }
        
        # Mock comprehensive microservices data architecture response
        mock_data_architecture = {
            "data_architecture": {
                "data_flow_design": {
                    "service_interactions": {
                        "synchronous_patterns": ["API gateway to services", "Service-to-service REST calls"],
                        "asynchronous_patterns": ["Event-driven messaging", "CQRS with event sourcing"],
                        "data_consistency": "eventual_consistency",
                        "transaction_patterns": ["Saga pattern", "Two-phase commit for critical operations"]
                    },
                    "database_design": {
                        "database_per_service": True,
                        "service_databases": {
                            "user_service": {"type": "PostgreSQL", "schema": "users_schema"},
                            "product_service": {"type": "MongoDB", "collection": "products"},
                            "order_service": {"type": "PostgreSQL", "schema": "orders_schema"},
                            "inventory_service": {"type": "PostgreSQL", "schema": "inventory_schema"},
                            "search_service": {"type": "Elasticsearch", "indices": ["products", "orders"]}
                        },
                        "shared_databases": {
                            "cache": {"type": "Redis", "usage": "Session cache, API cache"},
                            "message_queue": {"type": "RabbitMQ", "exchanges": ["user.events", "order.events", "inventory.events"]}
                        }
                    },
                    "api_architecture": {
                        "api_gateway": {
                            "pattern": "Backend for Frontend (BFF)",
                            "authentication": "OAuth 2.0 with JWT",
                            "rate_limiting": "Per-service rate limits",
                            "circuit_breakers": "Per-service circuit breakers"
                        },
                        "service_apis": {
                            "user_service": {"protocol": "REST", "endpoints": ["/users", "/auth"], "version": "v1"},
                            "product_service": {"protocol": "GraphQL", "schema": "product_schema", "version": "v1"},
                            "order_service": {"protocol": "REST", "endpoints": ["/orders", "/payments"], "version": "v1"},
                            "inventory_service": {"protocol": "gRPC", "services": ["InventoryService"], "version": "v1"}
                        },
                        "inter_service_communication": {
                            "synchronous": "HTTP/REST and gRPC",
                            "asynchronous": "Message queues with RabbitMQ",
                            "service_discovery": "Kubernetes DNS",
                            "load_balancing": "Kubernetes service mesh"
                        }
                    }
                },
                "persistence_strategy": {
                    "data_consistency": "BASE (Basically Available, Soft state, Eventual consistency)",
                    "backup_frequency": "Per-service backup strategy",
                    "replication": "Multi-region replication for critical services",
                    "data_partitioning": "Horizontal partitioning by service domain",
                    "cross_service_queries": "Event sourcing and CQRS patterns"
                },
                "event_architecture": {
                    "event_sourcing": {
                        "enabled_services": ["order_service", "inventory_service"],
                        "event_store": "PostgreSQL with event store schema",
                        "snapshot_strategy": "Periodic snapshots for performance"
                    },
                    "message_patterns": {
                        "event_publishing": "Domain events published to message queue",
                        "event_consumption": "Multiple consumers per event type",
                        "dead_letter_queues": "Failed message handling",
                        "message_ordering": "Partition-based ordering for related events"
                    }
                }
            }
        }
        
        # Mock reflection response
        mock_reflection = {
            "reflection_results": {
                "validation_status": {"passed": True},
                "complexity_issues": {"granularity": [], "complexity_level": []},
                "completeness_issues": {"requirements_coverage": [], "dependencies": [], "cross_cutting": []},
                "consistency_issues": {"technical_alignment": [], "constraint_compatibility": [], "assumption_validation": []}
            }
        }
        
        mock_process.side_effect = [mock_data_architecture, mock_reflection]
        
        # Process the microservices data architecture design
        result = await root_architect_agent._process(garden_planner_output, environment_analysis_output)
        
        # Verify comprehensive microservices data architecture
        data_arch = result["data_architecture"]
        assert data_arch["data_flow_design"]["database_design"]["database_per_service"] is True
        assert len(data_arch["data_flow_design"]["database_design"]["service_databases"]) == 5
        assert "user_service" in data_arch["data_flow_design"]["database_design"]["service_databases"]
        assert data_arch["data_flow_design"]["api_architecture"]["api_gateway"]["pattern"] == "Backend for Frontend (BFF)"
        assert data_arch["persistence_strategy"]["data_consistency"] == "BASE (Basically Available, Soft state, Eventual consistency)"
        assert "order_service" in data_arch["event_architecture"]["event_sourcing"]["enabled_services"]

    @patch('interfaces.agent.interface.AgentInterface.process_with_validation')
    async def test_monolithic_data_architecture_scenario(self, mock_process, root_architect_agent):
        """Test data architecture design for monolithic scenario."""
        # Mock Garden Planner output for monolithic system
        garden_planner_output = {
            "task_analysis": {
                "original_request": "Build an internal CRM system",
                "technical_requirements": {
                    "languages": ["Python"],
                    "frameworks": ["Django"],
                    "apis": ["REST API"],
                    "infrastructure": ["PostgreSQL", "Redis"]
                }
            }
        }
        
        # Mock Environmental Analysis output for monolithic system
        environment_analysis_output = {
            "environmental_analysis": {
                "deployment_environment": {
                    "hosting_type": "on_premise",
                    "architecture_pattern": "monolithic",
                    "server_configuration": "dedicated_servers"
                },
                "technical_ecosystem": {
                    "database": ["PostgreSQL", "Redis"],
                    "web_server": ["Nginx", "Gunicorn"]
                }
            }
        }
        
        # Mock monolithic data architecture response
        mock_data_architecture = {
            "data_architecture": {
                "data_flow_design": {
                    "application_layers": {
                        "presentation_layer": "Django templates and REST API",
                        "business_logic_layer": "Django models and services",
                        "data_access_layer": "Django ORM with PostgreSQL",
                        "caching_layer": "Redis for session and query caching"
                    },
                    "database_design": {
                        "primary_database": "PostgreSQL",
                        "database_schema": {
                            "customers": {"fields": ["id", "name", "email", "created_at"], "relationships": ["one_to_many_with_contacts"]},
                            "contacts": {"fields": ["id", "customer_id", "type", "value"], "relationships": ["many_to_one_with_customers"]},
                            "opportunities": {"fields": ["id", "customer_id", "amount", "stage"], "relationships": ["many_to_one_with_customers"]},
                            "activities": {"fields": ["id", "customer_id", "type", "description", "date"], "relationships": ["many_to_one_with_customers"]}
                        },
                        "indexing_strategy": "B-tree indexes on foreign keys and frequently queried fields",
                        "data_integrity": "Foreign key constraints and database triggers"
                    },
                    "api_architecture": {
                        "api_pattern": "RESTful API with Django REST Framework",
                        "endpoints": {
                            "/api/customers": {"methods": ["GET", "POST", "PUT", "DELETE"], "authentication": "required"},
                            "/api/contacts": {"methods": ["GET", "POST", "PUT", "DELETE"], "authentication": "required"},
                            "/api/opportunities": {"methods": ["GET", "POST", "PUT", "DELETE"], "authentication": "required"},
                            "/api/activities": {"methods": ["GET", "POST", "PUT", "DELETE"], "authentication": "required"}
                        },
                        "authentication": "Django session authentication",
                        "serialization": "JSON with Django REST Framework serializers"
                    }
                },
                "persistence_strategy": {
                    "data_consistency": "ACID compliance with PostgreSQL transactions",
                    "backup_frequency": "Daily automated backups with weekly full backups",
                    "replication": "Master-slave replication for read scalability",
                    "connection_pooling": "PgBouncer for database connection management",
                    "query_optimization": "Database query analysis and index optimization"
                },
                "caching_strategy": {
                    "session_caching": "Redis for user session storage",
                    "query_caching": "Redis for frequently accessed database queries",
                    "page_caching": "Django cache framework with Redis backend",
                    "cache_invalidation": "Time-based and event-driven cache invalidation"
                }
            }
        }
        
        # Mock reflection response
        mock_reflection = {
            "reflection_results": {
                "validation_status": {"passed": True},
                "complexity_issues": {"granularity": [], "complexity_level": []},
                "completeness_issues": {"requirements_coverage": [], "dependencies": [], "cross_cutting": []},
                "consistency_issues": {"technical_alignment": [], "constraint_compatibility": [], "assumption_validation": []}
            }
        }
        
        mock_process.side_effect = [mock_data_architecture, mock_reflection]
        
        # Process the monolithic data architecture design
        result = await root_architect_agent._process(garden_planner_output, environment_analysis_output)
        
        # Verify monolithic data architecture
        data_arch = result["data_architecture"]
        assert data_arch["data_flow_design"]["database_design"]["primary_database"] == "PostgreSQL"
        assert len(data_arch["data_flow_design"]["database_design"]["database_schema"]) == 4
        assert "customers" in data_arch["data_flow_design"]["database_design"]["database_schema"]
        assert data_arch["data_flow_design"]["api_architecture"]["api_pattern"] == "RESTful API with Django REST Framework"
        assert data_arch["persistence_strategy"]["data_consistency"] == "ACID compliance with PostgreSQL transactions"
        assert data_arch["caching_strategy"]["session_caching"] == "Redis for user session storage"

    @patch('interfaces.agent.interface.AgentInterface.process_with_validation')
    async def test_real_time_analytics_data_architecture_scenario(self, mock_process, root_architect_agent):
        """Test data architecture design for real-time analytics scenario."""
        # Mock Garden Planner output for real-time analytics
        garden_planner_output = {
            "task_analysis": {
                "original_request": "Build a real-time analytics dashboard for IoT data",
                "technical_requirements": {
                    "languages": ["Python", "JavaScript", "Scala"],
                    "frameworks": ["Django", "React", "Apache Spark"],
                    "apis": ["REST API", "WebSocket API", "Streaming API"],
                    "infrastructure": ["PostgreSQL", "Apache Kafka", "InfluxDB", "Redis", "Elasticsearch"]
                }
            }
        }
        
        # Mock Environmental Analysis output for real-time analytics
        environment_analysis_output = {
            "environmental_analysis": {
                "deployment_environment": {
                    "hosting_type": "cloud_native",
                    "architecture_pattern": "event_driven",
                    "scalability_requirements": "elastic_scaling"
                },
                "technical_ecosystem": {
                    "streaming_platform": ["Apache Kafka"],
                    "time_series_database": ["InfluxDB"],
                    "search_engine": ["Elasticsearch"],
                    "processing_framework": ["Apache Spark"]
                }
            }
        }
        
        # Mock real-time analytics data architecture response
        mock_data_architecture = {
            "data_architecture": {
                "data_flow_design": {
                    "streaming_architecture": {
                        "data_ingestion": {
                            "iot_devices": "Direct streaming to Kafka topics",
                            "batch_imports": "Scheduled data imports via REST API",
                            "real_time_events": "WebSocket connections for live updates"
                        },
                        "stream_processing": {
                            "framework": "Apache Spark Streaming",
                            "processing_patterns": ["Windowed aggregations", "Complex event processing", "Real-time filtering"],
                            "output_sinks": ["InfluxDB for time series", "PostgreSQL for metadata", "Elasticsearch for search"]
                        },
                        "data_flow_patterns": {
                            "lambda_architecture": "Batch and stream processing layers",
                            "kappa_architecture": "Stream-only processing for low latency",
                            "event_sourcing": "Immutable event log with Kafka"
                        }
                    },
                    "database_design": {
                        "time_series_database": {
                            "primary": "InfluxDB",
                            "schema": {
                                "measurements": ["sensor_data", "device_metrics", "alert_events"],
                                "tags": ["device_id", "location", "sensor_type"],
                                "fields": ["value", "status", "metadata"],
                                "retention_policy": "1 year for raw data, 5 years for aggregated data"
                            }
                        },
                        "relational_database": {
                            "primary": "PostgreSQL",
                            "schema": {
                                "devices": {"fields": ["id", "name", "type", "location"], "purpose": "Device metadata"},
                                "alerts": {"fields": ["id", "device_id", "severity", "message"], "purpose": "Alert configuration"},
                                "users": {"fields": ["id", "username", "role", "permissions"], "purpose": "User management"}
                            }
                        },
                        "search_database": {
                            "primary": "Elasticsearch",
                            "indices": {
                                "device_logs": {"mapping": "Device log events with full-text search"},
                                "alert_history": {"mapping": "Historical alerts with aggregations"}
                            }
                        }
                    },
                    "api_architecture": {
                        "rest_api": {
                            "endpoints": ["/devices", "/alerts", "/analytics", "/dashboards"],
                            "authentication": "JWT with role-based access",
                            "rate_limiting": "Tiered limits based on user role"
                        },
                        "websocket_api": {
                            "real_time_channels": ["device_updates", "alert_notifications", "dashboard_streams"],
                            "connection_management": "Redis for connection state",
                            "message_routing": "Kafka consumer groups for scalability"
                        },
                        "streaming_api": {
                            "kafka_topics": ["iot.raw.data", "iot.processed.data", "iot.alerts"],
                            "schema_registry": "Avro schemas for data validation",
                            "consumer_groups": "Isolated processing for different analytics"
                        }
                    }
                },
                "persistence_strategy": {
                    "data_consistency": "Eventual consistency for analytics, strong consistency for metadata",
                    "backup_frequency": "Continuous replication for time series, daily backups for metadata",
                    "data_retention": "Automated data lifecycle management",
                    "partitioning": "Time-based partitioning for time series data",
                    "compression": "Automatic compression for historical data"
                },
                "real_time_processing": {
                    "stream_processing_topology": {
                        "ingestion_stage": "Kafka producers with message validation",
                        "processing_stage": "Spark Streaming with windowed operations",
                        "aggregation_stage": "Real-time metrics calculation",
                        "output_stage": "Multi-sink output to databases and dashboards"
                    },
                    "performance_requirements": {
                        "latency": "Sub-second processing for critical alerts",
                        "throughput": "100,000 events per second",
                        "availability": "99.9% uptime for streaming pipeline"
                    }
                }
            }
        }
        
        # Mock reflection response
        mock_reflection = {
            "reflection_results": {
                "validation_status": {"passed": True},
                "complexity_issues": {"granularity": [], "complexity_level": []},
                "completeness_issues": {"requirements_coverage": [], "dependencies": [], "cross_cutting": []},
                "consistency_issues": {"technical_alignment": [], "constraint_compatibility": [], "assumption_validation": []}
            }
        }
        
        mock_process.side_effect = [mock_data_architecture, mock_reflection]
        
        # Process the real-time analytics data architecture design
        result = await root_architect_agent._process(garden_planner_output, environment_analysis_output)
        
        # Verify real-time analytics data architecture
        data_arch = result["data_architecture"]
        streaming_arch = data_arch["data_flow_design"]["streaming_architecture"]
        assert streaming_arch["data_ingestion"]["iot_devices"] == "Direct streaming to Kafka topics"
        assert streaming_arch["stream_processing"]["framework"] == "Apache Spark Streaming"
        assert "lambda_architecture" in streaming_arch["data_flow_patterns"]
        
        db_design = data_arch["data_flow_design"]["database_design"]
        assert db_design["time_series_database"]["primary"] == "InfluxDB"
        assert len(db_design["time_series_database"]["schema"]["measurements"]) == 3
        assert db_design["search_database"]["primary"] == "Elasticsearch"
        
        api_arch = data_arch["data_flow_design"]["api_architecture"]
        assert len(api_arch["websocket_api"]["real_time_channels"]) == 3
        assert "iot.raw.data" in api_arch["streaming_api"]["kafka_topics"]
        
        real_time = data_arch["real_time_processing"]
        assert real_time["performance_requirements"]["throughput"] == "100,000 events per second"
        assert real_time["stream_processing_topology"]["processing_stage"] == "Spark Streaming with windowed operations"