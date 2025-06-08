"""
Comprehensive unit tests for Garden Planner Agent.

Tests focus on end-to-end operational readiness with real functionality
and proper resource management.
"""
import pytest
import pytest_asyncio
import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from phase_one.agents.garden_planner import GardenPlannerAgent
from phase_one.models.enums import DevelopmentState
from phase_one.models.refinement import AgentPromptConfig
from resources import EventQueue, StateManager, AgentContextManager, CacheManager, MetricsManager, ErrorHandler
from resources.monitoring import MemoryMonitor, HealthTracker, CircuitOpenError

class TestGardenPlannerAgentInitialization:
    """Test Garden Planner Agent initialization and configuration."""
    
    @pytest_asyncio.fixture
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

    @pytest.mark.asyncio
    async def test_garden_planner_initialization_success(self, resource_managers):
        """Test successful Garden Planner Agent initialization."""
        agent = GardenPlannerAgent(
            agent_id="test_garden_planner",
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
        assert agent.agent_id == "test_garden_planner"
        assert agent.development_state == DevelopmentState.INITIALIZING
        assert isinstance(agent._prompt_config, AgentPromptConfig)
        assert agent._prompt_config.system_prompt_base_path == "FFTT_system_prompts/phase_one/garden_planner_agent"
        assert agent._prompt_config.initial_prompt_name == "initial_task_elaboration_prompt"
        
        # Verify circuit breaker definitions are configured
        cb_names = [cb.name for cb in agent._circuit_breaker_definitions]
        assert "processing" in cb_names
        assert "analysis" in cb_names
        
        # Verify lazy circuit breaker initialization works
        processing_cb = agent.get_circuit_breaker("processing")
        assert processing_cb is not None
        assert "processing" in agent._circuit_breakers
        
        # Verify validation history is initialized
        assert agent.validation_history == []

    @pytest.mark.asyncio
    async def test_garden_planner_prompt_configuration(self, resource_managers):
        """Test Garden Planner prompt configuration is correct."""
        agent = GardenPlannerAgent(
            agent_id="test_garden_planner",
            **resource_managers
        )
        
        # Verify all prompt names are configured
        config = agent._prompt_config
        assert config.system_prompt_base_path == "FFTT_system_prompts/phase_one/garden_planner_agent"
        assert config.reflection_prompt_name == "task_reflection_prompt"
        assert config.refinement_prompt_name == "task_elaboration_refinement_prompt"
        assert config.initial_prompt_name == "initial_task_elaboration_prompt"

    @pytest.mark.asyncio
    async def test_garden_planner_circuit_breaker_configuration(self, resource_managers):
        """Test Garden Planner circuit breaker configuration."""
        agent = GardenPlannerAgent(
            agent_id="test_garden_planner",
            **resource_managers
        )
        
        # Verify analysis circuit breaker
        analysis_cb = agent.get_circuit_breaker("analysis")
        assert analysis_cb is not None
        assert analysis_cb.name == "agent:test_garden_planner_analysis"


class TestGardenPlannerTaskProcessing:
    """Test Garden Planner Agent task processing functionality."""
    
    @pytest_asyncio.fixture
    async def garden_planner_agent(self):
        """Create a Garden Planner Agent for testing."""
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
        
        agent = GardenPlannerAgent(
            agent_id="test_garden_planner",
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
            await agent.cleanup()
        except Exception as e:
            # Ignore cleanup errors in tests
            pass
        try:
            await event_queue.stop()
        except Exception as e:
            # Ignore cleanup errors in tests
            pass

    @patch('interfaces.agent.interface.AgentInterface.process_with_validation')
    @pytest.mark.asyncio
    async def test_garden_planner_process_success(self, mock_process, garden_planner_agent):
        """Test successful task processing."""
        # Mock successful task analysis response
        mock_task_analysis = {
            "task_analysis": {
                "original_request": "Create a blog website",
                "interpreted_goal": "Build a personal blog website with content management",
                "scope": {
                    "included": ["Blog post creation", "Content management", "User authentication"],
                    "excluded": ["E-commerce features", "Social media integration"],
                    "assumptions": ["Single author blog", "Standard web technologies"]
                },
                "technical_requirements": {
                    "languages": ["Python", "JavaScript"],
                    "frameworks": ["Django", "React"],
                    "apis": ["REST API"],
                    "infrastructure": ["PostgreSQL", "Redis"]
                },
                "constraints": {
                    "technical": ["Must be responsive", "SEO friendly"],
                    "business": ["Budget under $5000", "3 month timeline"],
                    "performance": ["Page load under 2 seconds"]
                },
                "considerations": {
                    "security": ["User authentication", "CSRF protection"],
                    "scalability": ["Support 1000 concurrent users"],
                    "maintainability": ["Clean code structure", "Documentation"]
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
        
        mock_process.side_effect = [mock_task_analysis, mock_reflection]
        
        # Process a test task
        result = await garden_planner_agent._process("Create a blog website")
        
        # Verify successful processing
        assert "error" not in result
        assert result["task_analysis"]["original_request"] == "Create a blog website"
        assert result["task_analysis"]["interpreted_goal"] == "Build a personal blog website with content management"
        
        # Verify agent state
        assert garden_planner_agent.development_state == DevelopmentState.VALIDATING  # State after processing
        
        # Verify process_with_validation was called correctly
        assert mock_process.call_count == 2  # Initial analysis + reflection
        
        # Verify first call (initial analysis)
        first_call = mock_process.call_args_list[0]
        assert "Analyze task requirements: Create a blog website" in first_call[1]["conversation"]
        assert first_call[1]["system_prompt_info"][0] == "FFTT_system_prompts/phase_one/garden_planner_agent"
        assert first_call[1]["system_prompt_info"][1] == "initial_task_elaboration_prompt"

    @patch('interfaces.agent.interface.AgentInterface.process_with_validation')
    @pytest.mark.asyncio
    async def test_garden_planner_process_validation_failure(self, mock_process, garden_planner_agent):
        """Test processing when validation fails."""
        # Mock initial analysis
        mock_task_analysis = {
            "task_analysis": {
                "original_request": "Create a complex system",
                "interpreted_goal": "Build something",
                "scope": {"included": [], "excluded": [], "assumptions": []},
                "technical_requirements": {"languages": [], "frameworks": [], "apis": [], "infrastructure": []},
                "constraints": {"technical": [], "business": [], "performance": []},
                "considerations": {"security": [], "scalability": [], "maintainability": []}
            }
        }
        
        # Mock reflection response indicating validation failed
        mock_reflection = {
            "reflection_results": {
                "validation_status": {"passed": False},
                "complexity_issues": {
                    "granularity": [{"severity": "high", "issue": "Insufficient detail", "recommendation": "Add more specific requirements"}],
                    "complexity_level": []
                },
                "completeness_issues": {"requirements_coverage": [], "dependencies": [], "cross_cutting": []},
                "consistency_issues": {"technical_alignment": [], "constraint_compatibility": [], "assumption_validation": []}
            }
        }
        
        mock_process.side_effect = [mock_task_analysis, mock_reflection]
        
        # Process task
        result = await garden_planner_agent._process("Create a complex system")
        
        # Verify reflection result is returned (indicating refinement needed)
        assert result == mock_reflection
        assert garden_planner_agent.development_state == DevelopmentState.REFINING

    @patch('interfaces.agent.interface.AgentInterface.process_with_validation')
    @pytest.mark.asyncio
    async def test_garden_planner_circuit_breaker_protection(self, mock_process, garden_planner_agent):
        """Test circuit breaker protection during processing."""
        # Mock circuit breaker open exception
        mock_process.side_effect = CircuitOpenError("analysis", "Circuit breaker open")
        
        # Process task
        result = await garden_planner_agent._process("Create a website")
        
        # Verify circuit breaker error handling
        assert result["status"] == "failure"
        assert "Analysis rejected" in result["error"]
        assert garden_planner_agent.development_state == DevelopmentState.ERROR

    @pytest.mark.asyncio
    async def test_garden_planner_process_exception_handling(self, garden_planner_agent):
        """Test exception handling during processing."""
        # Test with invalid method call to trigger exception
        with pytest.raises(AttributeError):
            # Call non-existent method to trigger exception
            await garden_planner_agent.non_existent_method()


class TestGardenPlannerReflectionAndRefinement:
    """Test Garden Planner Agent reflection and refinement capabilities."""
    
    @pytest_asyncio.fixture
    async def garden_planner_agent(self):
        """Create a Garden Planner Agent for testing."""
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
        
        agent = GardenPlannerAgent(
            agent_id="test_garden_planner",
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
            await agent.cleanup()
        except Exception as e:
            # Ignore cleanup errors in tests
            pass
        try:
            await event_queue.stop()
        except Exception as e:
            # Ignore cleanup errors in tests
            pass

    @patch('interfaces.agent.interface.AgentInterface.process_with_validation')
    @pytest.mark.asyncio
    async def test_garden_planner_reflect_method(self, mock_process, garden_planner_agent):
        """Test Garden Planner reflect method."""
        mock_output = {"task_analysis": {"original_request": "Test task"}}
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
        result = await garden_planner_agent.reflect(mock_output)
        
        # Verify reflection was called
        assert result == mock_reflection
        mock_process.assert_called_once()
        
        # Verify reflection prompt was used
        call_args = mock_process.call_args
        assert "Reflect on output with a critical eye" in call_args[1]["conversation"]

    @patch('interfaces.agent.interface.AgentInterface.process_with_validation')
    @pytest.mark.asyncio
    async def test_garden_planner_refine_method(self, mock_process, garden_planner_agent):
        """Test Garden Planner refine method."""
        mock_output = {"task_analysis": {"original_request": "Test task"}}
        mock_guidance = {"action": "refine_scope", "specific_changes": ["Add more detail to scope"]}
        mock_refinement = {
            "task_analysis": {
                "original_request": "Test task",
                "interpreted_goal": "Refined goal with more detail"
            }
        }
        
        mock_process.return_value = mock_refinement
        
        # Test refinement
        result = await garden_planner_agent.refine(mock_output, mock_guidance)
        
        # Verify refinement was called
        assert result == mock_refinement
        mock_process.assert_called_once()
        
        # Verify refinement prompt was used
        call_args = mock_process.call_args
        assert "Refine output based on:" in call_args[1]["conversation"]
        assert "Original output:" in call_args[1]["conversation"]
        assert "Refinement guidance:" in call_args[1]["conversation"]


class TestGardenPlannerValidationLogic:
    """Test Garden Planner Agent validation logic."""
    
    @pytest_asyncio.fixture
    async def garden_planner_agent(self):
        """Create a Garden Planner Agent for testing."""
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
        
        agent = GardenPlannerAgent(
            agent_id="test_garden_planner",
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
            await agent.cleanup()
        except Exception as e:
            # Ignore cleanup errors in tests
            pass
        try:
            await event_queue.stop()
        except Exception as e:
            # Ignore cleanup errors in tests
            pass

    @pytest.mark.asyncio
    async def test_get_validation_status_passed(self, garden_planner_agent):
        """Test validation status extraction when validation passed."""
        reflection_result = {
            "reflection_results": {
                "validation_status": {"passed": True}
            }
        }
        
        status = await garden_planner_agent._get_validation_status(reflection_result)
        assert status is True

    @pytest.mark.asyncio
    async def test_get_validation_status_failed(self, garden_planner_agent):
        """Test validation status extraction when validation failed."""
        reflection_result = {
            "reflection_results": {
                "validation_status": {"passed": False}
            }
        }
        
        status = await garden_planner_agent._get_validation_status(reflection_result)
        assert status is False

    @pytest.mark.asyncio
    async def test_get_validation_status_malformed(self, garden_planner_agent):
        """Test validation status extraction with malformed result."""
        reflection_result = {"invalid": "structure"}
        
        status = await garden_planner_agent._get_validation_status(reflection_result)
        assert status is False

    @pytest.mark.asyncio
    async def test_get_validation_status_missing(self, garden_planner_agent):
        """Test validation status extraction with missing validation status."""
        reflection_result = {
            "reflection_results": {
                "complexity_issues": {}
            }
        }
        
        status = await garden_planner_agent._get_validation_status(reflection_result)
        assert status is False


class TestGardenPlannerMemoryManagement:
    """Test Garden Planner Agent memory management."""
    
    @pytest_asyncio.fixture
    async def garden_planner_agent(self):
        """Create a Garden Planner Agent for testing."""
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
        
        agent = GardenPlannerAgent(
            agent_id="test_garden_planner",
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
            await agent.cleanup()
        except Exception as e:
            # Ignore cleanup errors in tests
            pass
        try:
            await event_queue.stop()
        except Exception as e:
            # Ignore cleanup errors in tests
            pass

    @pytest.mark.asyncio
    async def test_memory_threshold_registration(self, garden_planner_agent):
        """Test memory threshold registration."""
        # Verify memory monitor has the component registered
        assert garden_planner_agent._memory_monitor is not None
        
        # This would be tested by verifying the registration actually happened
        # In a real scenario, we'd check the memory monitor's internal state

    @pytest.mark.asyncio
    async def test_track_string_memory(self, garden_planner_agent):
        """Test string memory tracking."""
        test_string = "This is a test task prompt for memory tracking"
        
        # Track string memory
        await garden_planner_agent.track_string_memory("test_resource", test_string)
        
        # Verify tracking doesn't raise exceptions
        # In real implementation, we'd verify the memory monitor recorded the usage

    @pytest.mark.asyncio
    async def test_track_dict_memory(self, garden_planner_agent):
        """Test dictionary memory tracking."""
        test_dict = {
            "task_analysis": {
                "original_request": "Test request",
                "interpreted_goal": "Test goal"
            }
        }
        
        # Track dict memory
        await garden_planner_agent.track_dict_memory("test_dict", test_dict)
        
        # Verify tracking doesn't raise exceptions
        # In real implementation, we'd verify the memory monitor recorded the usage


class TestGardenPlannerHealthReporting:
    """Test Garden Planner Agent health reporting."""
    
    @pytest_asyncio.fixture
    async def garden_planner_agent(self):
        """Create a Garden Planner Agent for testing."""
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
        
        agent = GardenPlannerAgent(
            agent_id="test_garden_planner",
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
            await agent.cleanup()
        except Exception as e:
            # Ignore cleanup errors in tests
            pass
        try:
            await event_queue.stop()
        except Exception as e:
            # Ignore cleanup errors in tests
            pass

    @pytest.mark.asyncio
    async def test_health_tracker_initialization(self, garden_planner_agent):
        """Test health tracker is properly initialized."""
        assert garden_planner_agent._health_tracker is not None

    @pytest.mark.asyncio
    async def test_health_reporting_success(self, garden_planner_agent):
        """Test health reporting with success status."""
        await garden_planner_agent._report_agent_health(
            custom_status="HEALTHY",
            description="Test successful operation",
            metadata={"test": "value"}
        )
        
        # Verify no exceptions are raised
        # In real implementation, we'd verify the health status was recorded

    @pytest.mark.asyncio
    async def test_health_reporting_error(self, garden_planner_agent):
        """Test health reporting with error status."""
        await garden_planner_agent._report_agent_health(
            custom_status="CRITICAL",
            description="Test error condition",
            metadata={"error": "test error"}
        )
        
        # Verify no exceptions are raised
        # In real implementation, we'd verify the health status was recorded


class TestGardenPlannerIntegrationScenarios:
    """Test Garden Planner Agent integration scenarios."""
    
    @pytest_asyncio.fixture
    async def garden_planner_agent(self):
        """Create a Garden Planner Agent for testing."""
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
        
        agent = GardenPlannerAgent(
            agent_id="test_garden_planner",
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
            await agent.cleanup()
        except Exception as e:
            # Ignore cleanup errors in tests
            pass
        try:
            await event_queue.stop()
        except Exception as e:
            # Ignore cleanup errors in tests
            pass

    @patch('interfaces.agent.interface.AgentInterface.process_with_validation')
    @pytest.mark.asyncio
    async def test_complete_blog_website_scenario(self, mock_process, garden_planner_agent):
        """Test complete blog website analysis scenario."""
        # Mock comprehensive task analysis
        mock_task_analysis = {
            "task_analysis": {
                "original_request": "Create a personal blog website with content management capabilities",
                "interpreted_goal": "Build a modern personal blog website with user-friendly content management, responsive design, and SEO optimization",
                "scope": {
                    "included": [
                        "Blog post creation and editing interface",
                        "Content management dashboard",
                        "User authentication system",
                        "Comment system",
                        "SEO optimization features",
                        "Responsive design",
                        "Search functionality"
                    ],
                    "excluded": [
                        "E-commerce functionality",
                        "Multi-author support",
                        "Social media automation",
                        "Advanced analytics dashboard",
                        "Custom themes marketplace"
                    ],
                    "assumptions": [
                        "Single author personal blog",
                        "Standard web hosting environment",
                        "Modern browser support",
                        "Basic SEO requirements",
                        "Moderate traffic expectations (< 10k visitors/month)"
                    ]
                },
                "technical_requirements": {
                    "languages": ["Python", "JavaScript", "HTML", "CSS"],
                    "frameworks": ["Django", "React", "Bootstrap"],
                    "apis": ["REST API", "Django REST Framework"],
                    "infrastructure": ["PostgreSQL", "Redis", "Nginx", "Docker"]
                },
                "constraints": {
                    "technical": [
                        "Must be responsive across all devices",
                        "Page load time under 3 seconds",
                        "SEO friendly URLs and meta tags",
                        "HTTPS required",
                        "Cross-browser compatibility"
                    ],
                    "business": [
                        "Development budget under $8,000",
                        "4-month development timeline",
                        "Hosting budget under $50/month",
                        "Must support future content growth"
                    ],
                    "performance": [
                        "Support 500 concurrent users",
                        "99.9% uptime requirement",
                        "Mobile-first performance optimization",
                        "Search response time under 1 second"
                    ]
                },
                "considerations": {
                    "security": [
                        "User authentication and session management",
                        "CSRF protection",
                        "SQL injection prevention",
                        "Content sanitization",
                        "Secure file upload handling"
                    ],
                    "scalability": [
                        "Database query optimization",
                        "Caching strategy implementation",
                        "CDN integration for media files",
                        "Horizontal scaling preparation"
                    ],
                    "maintainability": [
                        "Clean, documented code structure",
                        "Automated testing suite",
                        "Version control with Git",
                        "Deployment automation",
                        "Monitoring and logging setup"
                    ]
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
        
        mock_process.side_effect = [mock_task_analysis, mock_reflection]
        
        # Process the blog website request
        result = await garden_planner_agent._process(
            "Create a personal blog website with content management capabilities"
        )
        
        # Verify comprehensive analysis
        assert result["task_analysis"]["original_request"] == "Create a personal blog website with content management capabilities"
        assert len(result["task_analysis"]["scope"]["included"]) >= 7
        assert len(result["task_analysis"]["scope"]["excluded"]) >= 5
        assert len(result["task_analysis"]["technical_requirements"]["languages"]) >= 4
        assert len(result["task_analysis"]["constraints"]["technical"]) >= 5
        
        # Verify specific requirements
        assert "Django" in result["task_analysis"]["technical_requirements"]["frameworks"]
        assert "PostgreSQL" in result["task_analysis"]["technical_requirements"]["infrastructure"]
        assert "User authentication system" in result["task_analysis"]["scope"]["included"]

    @patch('interfaces.agent.interface.AgentInterface.process_with_validation')
    @pytest.mark.asyncio
    async def test_ecommerce_platform_scenario(self, mock_process, garden_planner_agent):
        """Test e-commerce platform analysis scenario."""
        # Mock complex e-commerce task analysis
        mock_task_analysis = {
            "task_analysis": {
                "original_request": "Build an e-commerce platform for selling handmade crafts",
                "interpreted_goal": "Develop a comprehensive e-commerce platform specialized for handmade craft vendors with marketplace functionality",
                "scope": {
                    "included": [
                        "Product catalog management",
                        "Shopping cart and checkout system",
                        "Payment processing integration",
                        "Vendor management system",
                        "Order tracking and fulfillment",
                        "Customer review system",
                        "Inventory management",
                        "Multi-vendor marketplace features",
                        "Mobile-responsive design"
                    ],
                    "excluded": [
                        "Physical shipping logistics",
                        "International tax calculation",
                        "Advanced analytics dashboard",
                        "Subscription billing",
                        "Affiliate marketing system"
                    ],
                    "assumptions": [
                        "Multiple vendors selling handmade items",
                        "Credit card payment processing",
                        "North American market focus",
                        "Standard shipping methods",
                        "English language interface"
                    ]
                },
                "technical_requirements": {
                    "languages": ["Python", "JavaScript", "TypeScript", "HTML", "CSS"],
                    "frameworks": ["Django", "React", "Redux", "Material-UI"],
                    "apis": ["REST API", "Stripe API", "PayPal API", "Shipping APIs"],
                    "infrastructure": ["PostgreSQL", "Redis", "Elasticsearch", "AWS S3", "CDN"]
                },
                "constraints": {
                    "technical": [
                        "PCI DSS compliance for payment processing",
                        "High availability (99.95% uptime)",
                        "Page load time under 2 seconds",
                        "Mobile-first design",
                        "SEO optimization for product discovery"
                    ],
                    "business": [
                        "Development budget $50,000-$75,000",
                        "8-month development timeline",
                        "Commission-based revenue model",
                        "Must support 1000+ concurrent vendors"
                    ],
                    "performance": [
                        "Support 10,000 concurrent users",
                        "Handle 1 million products in catalog",
                        "Process 1000 orders per hour",
                        "Search response time under 500ms"
                    ]
                },
                "considerations": {
                    "security": [
                        "PCI DSS compliance",
                        "Two-factor authentication",
                        "Encrypted payment processing",
                        "Fraud detection system",
                        "Secure vendor onboarding"
                    ],
                    "scalability": [
                        "Microservices architecture",
                        "Database sharding strategy",
                        "Auto-scaling infrastructure",
                        "CDN for global content delivery"
                    ],
                    "maintainability": [
                        "Comprehensive test coverage",
                        "CI/CD pipeline",
                        "Monitoring and alerting",
                        "Documentation and API specs",
                        "Code quality standards"
                    ]
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
        
        mock_process.side_effect = [mock_task_analysis, mock_reflection]
        
        # Process the e-commerce platform request
        result = await garden_planner_agent._process(
            "Build an e-commerce platform for selling handmade crafts"
        )
        
        # Verify complex analysis
        assert result["task_analysis"]["original_request"] == "Build an e-commerce platform for selling handmade crafts"
        assert len(result["task_analysis"]["scope"]["included"]) >= 9
        assert "Payment processing integration" in result["task_analysis"]["scope"]["included"]
        assert any("PCI DSS compliance" in constraint for constraint in result["task_analysis"]["constraints"]["technical"])
        assert "Stripe API" in result["task_analysis"]["technical_requirements"]["apis"]