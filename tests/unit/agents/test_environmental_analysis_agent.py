"""
Comprehensive unit tests for Environmental Analysis Agent.

Tests focus on end-to-end operational readiness with real functionality
and proper resource management.
"""
import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from phase_one.agents.environmental_analysis import EnvironmentalAnalysisAgent
from phase_one.models.enums import DevelopmentState
from phase_one.models.refinement import AgentPromptConfig
from resources import EventQueue, StateManager, AgentContextManager, CacheManager, MetricsManager, ErrorHandler
from resources.monitoring import MemoryMonitor, HealthTracker, CircuitOpenError

class TestEnvironmentalAnalysisAgentInitialization:
    """Test Environmental Analysis Agent initialization and configuration."""
    
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

    async def test_environmental_analysis_initialization_success(self, resource_managers):
        """Test successful Environmental Analysis Agent initialization."""
        agent = EnvironmentalAnalysisAgent(
            agent_id="test_env_analysis",
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
        assert agent.agent_id == "test_env_analysis"
        assert agent.development_state == DevelopmentState.INITIALIZING
        assert isinstance(agent._prompt_config, AgentPromptConfig)
        assert agent._prompt_config.system_prompt_base_path == "FFTT_system_prompts/phase_one/garden_environmental_analysis_agent"
        assert agent._prompt_config.initial_prompt_name == "initial_core_requirements_prompt"
        
        # Verify circuit breaker definitions are configured
        cb_names = [cb.name for cb in agent._circuit_breaker_definitions]
        assert "processing" in cb_names
        assert "analysis" in cb_names
        
        # Verify lazy circuit breaker initialization works
        processing_cb = agent.get_circuit_breaker("processing")
        assert processing_cb is not None
        assert "processing" in agent._circuit_breakers

    async def test_environmental_analysis_prompt_configuration(self, resource_managers):
        """Test Environmental Analysis prompt configuration is correct."""
        agent = EnvironmentalAnalysisAgent(
            agent_id="test_env_analysis",
            **resource_managers
        )
        
        # Verify all prompt names are configured
        config = agent._prompt_config
        assert config.system_prompt_base_path == "FFTT_system_prompts/phase_one/garden_environmental_analysis_agent"
        assert config.reflection_prompt_name == "core_requirements_reflection_prompt"
        assert config.refinement_prompt_name == "core_requirements_refinement_prompt"
        assert config.initial_prompt_name == "initial_core_requirements_prompt"

    async def test_environmental_analysis_memory_configuration(self, resource_managers):
        """Test Environmental Analysis memory configuration."""
        agent = EnvironmentalAnalysisAgent(
            agent_id="test_env_analysis",
            **resource_managers
        )
        
        # Verify memory monitor is configured
        assert agent._memory_monitor is not None
        # Environmental analysis should have higher memory threshold (70MB vs 50MB)


class TestEnvironmentalAnalysisProcessing:
    """Test Environmental Analysis Agent processing functionality."""
    
    @pytest.fixture
    async def env_analysis_agent(self):
        """Create an Environmental Analysis Agent for testing."""
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
        
        agent = EnvironmentalAnalysisAgent(
            agent_id="test_env_analysis",
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
    async def test_environmental_analysis_process_success(self, mock_process, env_analysis_agent):
        """Test successful environmental analysis processing."""
        # Mock Garden Planner output
        garden_planner_output = {
            "task_analysis": {
                "original_request": "Create a blog website",
                "interpreted_goal": "Build a personal blog website with content management",
                "technical_requirements": {
                    "languages": ["Python", "JavaScript"],
                    "frameworks": ["Django", "React"],
                    "infrastructure": ["PostgreSQL", "Redis"]
                },
                "constraints": {
                    "performance": ["Page load under 2 seconds"],
                    "business": ["Budget under $5000"]
                }
            }
        }
        
        # Mock environmental analysis response
        mock_env_analysis = {
            "environmental_analysis": {
                "deployment_environment": {
                    "hosting_type": "cloud",
                    "scalability_requirements": "moderate",
                    "availability_needs": "99.9%"
                },
                "technical_ecosystem": {
                    "development_stack": ["Python", "JavaScript", "PostgreSQL"],
                    "deployment_tools": ["Docker", "Nginx"],
                    "monitoring_requirements": ["Application monitoring", "Database monitoring"]
                },
                "operational_requirements": {
                    "backup_strategy": "Daily automated backups",
                    "security_compliance": ["HTTPS", "Data encryption"],
                    "maintenance_windows": "Weekly maintenance allowed"
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
        
        mock_process.side_effect = [mock_env_analysis, mock_reflection]
        
        # Process environmental analysis
        result = await env_analysis_agent._process(garden_planner_output)
        
        # Verify successful processing
        assert "error" not in result
        assert result["environmental_analysis"]["deployment_environment"]["hosting_type"] == "cloud"
        assert env_analysis_agent.development_state == DevelopmentState.COMPLETE
        
        # Verify process_with_validation was called correctly
        assert mock_process.call_count == 2  # Analysis + reflection
        
        # Verify first call (environmental analysis)
        first_call = mock_process.call_args_list[0]
        assert "Analyze environment based on:" in first_call[1]["conversation"]
        assert first_call[1]["system_prompt_info"][0] == "FFTT_system_prompts/phase_one/garden_environmental_analysis_agent"
        assert first_call[1]["system_prompt_info"][1] == "initial_core_requirements_prompt"

    @patch('interfaces.agent.interface.AgentInterface.process_with_validation')
    async def test_environmental_analysis_validation_failure(self, mock_process, env_analysis_agent):
        """Test processing when validation fails."""
        # Mock Garden Planner output
        garden_planner_output = {
            "task_analysis": {
                "original_request": "Create a complex system",
                "technical_requirements": {"languages": ["Python"]}
            }
        }
        
        # Mock initial environmental analysis
        mock_env_analysis = {
            "environmental_analysis": {
                "deployment_environment": {"hosting_type": "unknown"}
            }
        }
        
        # Mock reflection response indicating validation failed
        mock_reflection = {
            "reflection_results": {
                "validation_status": {"passed": False},
                "complexity_issues": {
                    "granularity": [{"severity": "high", "issue": "Insufficient environment detail", "recommendation": "Specify hosting requirements"}],
                    "complexity_level": []
                },
                "completeness_issues": {"requirements_coverage": [], "dependencies": [], "cross_cutting": []},
                "consistency_issues": {"technical_alignment": [], "constraint_compatibility": [], "assumption_validation": []}
            }
        }
        
        mock_process.side_effect = [mock_env_analysis, mock_reflection]
        
        # Process environmental analysis
        result = await env_analysis_agent._process(garden_planner_output)
        
        # Verify reflection result is returned (indicating refinement needed)
        assert result == mock_reflection
        assert env_analysis_agent.development_state == DevelopmentState.REFINING

    @patch('interfaces.agent.interface.AgentInterface.process_with_validation')
    async def test_environmental_analysis_circuit_breaker_protection(self, mock_process, env_analysis_agent):
        """Test circuit breaker protection during processing."""
        # Mock circuit breaker open exception
        mock_process.side_effect = CircuitOpenError("analysis", "Circuit breaker open")
        
        garden_planner_output = {"task_analysis": {"original_request": "Test"}}
        
        # Process environmental analysis
        result = await env_analysis_agent._process(garden_planner_output)
        
        # Verify circuit breaker error handling
        assert result["status"] == "failure"
        assert "Analysis rejected" in result["error"]
        assert env_analysis_agent.development_state == DevelopmentState.ERROR

    async def test_environmental_analysis_process_exception_handling(self, env_analysis_agent):
        """Test exception handling during processing."""
        garden_planner_output = {"task_analysis": {"original_request": "Test"}}
        
        # Test with invalid method call to trigger exception
        with pytest.raises(Exception):
            await env_analysis_agent._process(garden_planner_output)
        
        # Verify error state
        assert env_analysis_agent.development_state == DevelopmentState.ERROR


class TestEnvironmentalAnalysisReflectionAndRefinement:
    """Test Environmental Analysis Agent reflection and refinement capabilities."""
    
    @pytest.fixture
    async def env_analysis_agent(self):
        """Create an Environmental Analysis Agent for testing."""
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
        
        agent = EnvironmentalAnalysisAgent(
            agent_id="test_env_analysis",
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
    async def test_environmental_analysis_reflect_method(self, mock_process, env_analysis_agent):
        """Test Environmental Analysis reflect method."""
        mock_output = {"environmental_analysis": {"deployment_environment": {"hosting_type": "cloud"}}}
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
        result = await env_analysis_agent.reflect(mock_output)
        
        # Verify reflection was called
        assert result == mock_reflection
        mock_process.assert_called_once()
        
        # Verify reflection prompt was used
        call_args = mock_process.call_args
        assert "Reflect on output with a critical eye" in call_args[1]["conversation"]

    @patch('interfaces.agent.interface.AgentInterface.process_with_validation')
    async def test_environmental_analysis_refine_method(self, mock_process, env_analysis_agent):
        """Test Environmental Analysis refine method."""
        mock_output = {"environmental_analysis": {"deployment_environment": {"hosting_type": "cloud"}}}
        mock_guidance = {"action": "enhance_environment", "specific_changes": ["Add more deployment details"]}
        mock_refinement = {
            "environmental_analysis": {
                "deployment_environment": {
                    "hosting_type": "cloud",
                    "provider": "AWS",
                    "region": "us-east-1"
                }
            }
        }
        
        mock_process.return_value = mock_refinement
        
        # Test refinement
        result = await env_analysis_agent.refine(mock_output, mock_guidance)
        
        # Verify refinement was called
        assert result == mock_refinement
        mock_process.assert_called_once()
        
        # Verify refinement prompt was used
        call_args = mock_process.call_args
        assert "Refine output based on:" in call_args[1]["conversation"]


class TestEnvironmentalAnalysisHealthReporting:
    """Test Environmental Analysis Agent health reporting."""
    
    @pytest.fixture
    async def env_analysis_agent(self):
        """Create an Environmental Analysis Agent for testing."""
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
        
        agent = EnvironmentalAnalysisAgent(
            agent_id="test_env_analysis",
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

    async def test_health_reporting_processing_state(self, env_analysis_agent):
        """Test health reporting during processing state."""
        await env_analysis_agent._report_agent_health(
            description="Processing environment analysis",
            metadata={"state": "ANALYZING"}
        )
        
        # Verify no exceptions are raised

    async def test_health_reporting_degraded_state(self, env_analysis_agent):
        """Test health reporting during degraded state."""
        await env_analysis_agent._report_agent_health(
            custom_status="DEGRADED",
            description="Validation failed, entering refinement",
            metadata={
                "state": "REFINING",
                "validation": "failed"
            }
        )
        
        # Verify no exceptions are raised

    async def test_health_reporting_complete_state(self, env_analysis_agent):
        """Test health reporting during complete state."""
        await env_analysis_agent._report_agent_health(
            description="Environment analysis completed successfully",
            metadata={"state": "COMPLETE"}
        )
        
        # Verify no exceptions are raised


class TestEnvironmentalAnalysisIntegrationScenarios:
    """Test Environmental Analysis Agent integration scenarios."""
    
    @pytest.fixture
    async def env_analysis_agent(self):
        """Create an Environmental Analysis Agent for testing."""
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
        
        agent = EnvironmentalAnalysisAgent(
            agent_id="test_env_analysis",
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
    async def test_cloud_microservices_environment_scenario(self, mock_process, env_analysis_agent):
        """Test environmental analysis for cloud microservices scenario."""
        # Mock Garden Planner output for microservices architecture
        garden_planner_output = {
            "task_analysis": {
                "original_request": "Build a microservices-based e-commerce platform",
                "interpreted_goal": "Develop scalable microservices architecture for e-commerce",
                "technical_requirements": {
                    "languages": ["Python", "JavaScript", "Java"],
                    "frameworks": ["Django", "Spring Boot", "React"],
                    "apis": ["REST API", "GraphQL", "gRPC"],
                    "infrastructure": ["PostgreSQL", "MongoDB", "Redis", "RabbitMQ", "Elasticsearch"]
                },
                "constraints": {
                    "technical": ["Microservices architecture", "Container-based deployment", "API gateway required"],
                    "business": ["High availability required", "Global deployment"],
                    "performance": ["Support 100,000 concurrent users", "Sub-second response times"]
                }
            }
        }
        
        # Mock comprehensive environmental analysis response
        mock_env_analysis = {
            "environmental_analysis": {
                "deployment_environment": {
                    "hosting_type": "cloud_native",
                    "architecture_pattern": "microservices",
                    "container_orchestration": "kubernetes",
                    "cloud_provider": "AWS",
                    "regions": ["us-east-1", "eu-west-1", "ap-southeast-1"],
                    "scalability_requirements": "auto_scaling",
                    "availability_needs": "99.99%"
                },
                "technical_ecosystem": {
                    "development_stack": ["Python", "JavaScript", "Java"],
                    "containerization": ["Docker", "Kubernetes"],
                    "service_mesh": ["Istio"],
                    "api_gateway": ["Kong", "AWS API Gateway"],
                    "messaging": ["RabbitMQ", "Apache Kafka"],
                    "databases": {
                        "primary": "PostgreSQL",
                        "document": "MongoDB", 
                        "cache": "Redis",
                        "search": "Elasticsearch"
                    },
                    "monitoring_requirements": [
                        "Distributed tracing",
                        "Application performance monitoring",
                        "Infrastructure monitoring",
                        "Log aggregation"
                    ]
                },
                "operational_requirements": {
                    "backup_strategy": "Cross-region automated backups",
                    "disaster_recovery": "Multi-region failover",
                    "security_compliance": ["SOC 2", "PCI DSS", "GDPR"],
                    "maintenance_windows": "Rolling updates with zero downtime",
                    "load_balancing": "Application load balancer with health checks",
                    "auto_scaling": "Horizontal pod autoscaling based on CPU and memory"
                },
                "development_environment": {
                    "ci_cd": "GitLab CI/CD with automated testing",
                    "environment_parity": "Development, staging, production",
                    "infrastructure_as_code": "Terraform",
                    "configuration_management": "Kubernetes ConfigMaps and Secrets"
                },
                "performance_requirements": {
                    "latency_targets": {
                        "api_response": "< 200ms",
                        "page_load": "< 1.5s",
                        "search": "< 500ms"
                    },
                    "throughput_targets": {
                        "requests_per_second": "50,000",
                        "concurrent_users": "100,000",
                        "database_tps": "10,000"
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
        
        mock_process.side_effect = [mock_env_analysis, mock_reflection]
        
        # Process the microservices environment analysis
        result = await env_analysis_agent._process(garden_planner_output)
        
        # Verify comprehensive environmental analysis
        env_analysis = result["environmental_analysis"]
        assert env_analysis["deployment_environment"]["architecture_pattern"] == "microservices"
        assert env_analysis["deployment_environment"]["container_orchestration"] == "kubernetes"
        assert len(env_analysis["deployment_environment"]["regions"]) == 3
        assert env_analysis["technical_ecosystem"]["service_mesh"][0] == "Istio"
        assert "Distributed tracing" in env_analysis["technical_ecosystem"]["monitoring_requirements"]
        assert env_analysis["operational_requirements"]["security_compliance"] == ["SOC 2", "PCI DSS", "GDPR"]
        assert env_analysis["performance_requirements"]["latency_targets"]["api_response"] == "< 200ms"

    @patch('interfaces.agent.interface.AgentInterface.process_with_validation')
    async def test_on_premise_monolith_environment_scenario(self, mock_process, env_analysis_agent):
        """Test environmental analysis for on-premise monolithic scenario."""
        # Mock Garden Planner output for monolithic architecture
        garden_planner_output = {
            "task_analysis": {
                "original_request": "Build an internal CRM system for company use",
                "interpreted_goal": "Develop monolithic CRM system for internal company operations",
                "technical_requirements": {
                    "languages": ["Python"],
                    "frameworks": ["Django"],
                    "apis": ["REST API"],
                    "infrastructure": ["PostgreSQL", "Redis"]
                },
                "constraints": {
                    "technical": ["Must run on company servers", "No cloud services"],
                    "business": ["Internal use only", "Company security policies"],
                    "performance": ["Support 500 concurrent users", "Response time under 3 seconds"]
                }
            }
        }
        
        # Mock on-premise environmental analysis response
        mock_env_analysis = {
            "environmental_analysis": {
                "deployment_environment": {
                    "hosting_type": "on_premise",
                    "architecture_pattern": "monolithic",
                    "server_configuration": "dedicated_servers",
                    "datacenter_location": "company_facility",
                    "scalability_requirements": "vertical_scaling",
                    "availability_needs": "99.5%"
                },
                "technical_ecosystem": {
                    "development_stack": ["Python", "Django"],
                    "web_server": ["Nginx", "Gunicorn"],
                    "database": ["PostgreSQL", "Redis"],
                    "operating_system": "Ubuntu 20.04 LTS",
                    "monitoring_requirements": [
                        "Server monitoring",
                        "Application logs",
                        "Database performance"
                    ]
                },
                "operational_requirements": {
                    "backup_strategy": "Daily local backups with weekly off-site",
                    "security_compliance": ["Company security policies", "Data encryption at rest"],
                    "maintenance_windows": "Weekend maintenance allowed",
                    "hardware_requirements": {
                        "cpu": "16 cores",
                        "memory": "64GB RAM",
                        "storage": "2TB SSD"
                    }
                },
                "development_environment": {
                    "version_control": "GitLab self-hosted",
                    "ci_cd": "Jenkins",
                    "environment_setup": "Development, staging, production on separate servers",
                    "deployment_method": "Blue-green deployment"
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
        
        mock_process.side_effect = [mock_env_analysis, mock_reflection]
        
        # Process the on-premise environment analysis
        result = await env_analysis_agent._process(garden_planner_output)
        
        # Verify on-premise environmental analysis
        env_analysis = result["environmental_analysis"]
        assert env_analysis["deployment_environment"]["hosting_type"] == "on_premise"
        assert env_analysis["deployment_environment"]["architecture_pattern"] == "monolithic"
        assert env_analysis["deployment_environment"]["scalability_requirements"] == "vertical_scaling"
        assert env_analysis["technical_ecosystem"]["operating_system"] == "Ubuntu 20.04 LTS"
        assert env_analysis["operational_requirements"]["hardware_requirements"]["memory"] == "64GB RAM"
        assert env_analysis["development_environment"]["version_control"] == "GitLab self-hosted"

    @patch('interfaces.agent.interface.AgentInterface.process_with_validation')
    async def test_hybrid_cloud_environment_scenario(self, mock_process, env_analysis_agent):
        """Test environmental analysis for hybrid cloud scenario."""
        # Mock Garden Planner output for hybrid architecture
        garden_planner_output = {
            "task_analysis": {
                "original_request": "Build a healthcare management system with HIPAA compliance",
                "interpreted_goal": "Develop HIPAA-compliant healthcare system with hybrid cloud architecture",
                "technical_requirements": {
                    "languages": ["Python", "JavaScript"],
                    "frameworks": ["Django", "React"],
                    "apis": ["REST API", "HL7 FHIR"],
                    "infrastructure": ["PostgreSQL", "Redis", "MinIO"]
                },
                "constraints": {
                    "technical": ["HIPAA compliance", "PHI data protection", "Audit logging"],
                    "business": ["Healthcare regulations", "Patient data privacy"],
                    "performance": ["24/7 availability", "Secure data transmission"]
                }
            }
        }
        
        # Mock hybrid cloud environmental analysis response
        mock_env_analysis = {
            "environmental_analysis": {
                "deployment_environment": {
                    "hosting_type": "hybrid_cloud",
                    "architecture_pattern": "distributed",
                    "cloud_components": ["Application layer", "API gateway"],
                    "on_premise_components": ["Database", "PHI storage"],
                    "cloud_provider": "Azure",
                    "compliance_zones": "HIPAA-compliant regions",
                    "scalability_requirements": "elastic_scaling",
                    "availability_needs": "99.99%"
                },
                "technical_ecosystem": {
                    "development_stack": ["Python", "JavaScript"],
                    "cloud_services": ["Azure App Service", "Azure API Management"],
                    "on_premise_infrastructure": ["PostgreSQL", "MinIO object storage"],
                    "security_layer": ["VPN connection", "Private endpoints"],
                    "compliance_tools": ["Azure Security Center", "Audit logging"],
                    "monitoring_requirements": [
                        "Compliance monitoring",
                        "Security event monitoring",
                        "Performance monitoring",
                        "Audit trail tracking"
                    ]
                },
                "operational_requirements": {
                    "backup_strategy": "Encrypted cross-site backups",
                    "disaster_recovery": "Hot standby with 15-minute RTO",
                    "security_compliance": ["HIPAA", "SOC 2 Type II", "ISO 27001"],
                    "data_encryption": "End-to-end encryption for PHI",
                    "access_controls": "Role-based access with MFA",
                    "audit_requirements": "Complete audit trail for all PHI access"
                },
                "compliance_requirements": {
                    "data_residency": "US-based data centers only",
                    "retention_policies": "7-year data retention",
                    "privacy_controls": "Patient consent management",
                    "security_assessments": "Annual penetration testing"
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
        
        mock_process.side_effect = [mock_env_analysis, mock_reflection]
        
        # Process the hybrid cloud environment analysis
        result = await env_analysis_agent._process(garden_planner_output)
        
        # Verify hybrid cloud environmental analysis
        env_analysis = result["environmental_analysis"]
        assert env_analysis["deployment_environment"]["hosting_type"] == "hybrid_cloud"
        assert "PHI storage" in env_analysis["deployment_environment"]["on_premise_components"]
        assert "Azure App Service" in env_analysis["technical_ecosystem"]["cloud_services"]
        assert "HIPAA" in env_analysis["operational_requirements"]["security_compliance"]
        assert env_analysis["compliance_requirements"]["data_residency"] == "US-based data centers only"
        assert env_analysis["compliance_requirements"]["retention_policies"] == "7-year data retention"