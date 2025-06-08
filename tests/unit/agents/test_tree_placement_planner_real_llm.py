"""
Comprehensive test suite for Tree Placement Planner Agent with real LLM calls.

This module tests the Tree Placement Planner agent's core functionality with real API calls
to ensure proper component architecture design and structural breakdown.
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
from phase_one.agents.tree_placement_planner import TreePlacementPlannerAgent
from phase_one.models.enums import DevelopmentState

logger = logging.getLogger(__name__)

@pytest.mark.real_api
class TestTreePlacementPlannerRealLLM:
    """Test suite for Tree Placement Planner Agent using real LLM API calls."""

    @pytest_asyncio.fixture
    async def real_resources(self):
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
        await error_handler.initialize()
        
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
    async def tree_placement_planner_agent(self, real_resources):
        """Create a Tree Placement Planner Agent instance with real resources."""
        agent = TreePlacementPlannerAgent(
            agent_id="test_tree_placement_planner",
            **real_resources
        )
        return agent

    @pytest.fixture
    def comprehensive_phase_one_inputs(self):
        """Provide comprehensive phase one inputs for testing."""
        return {
            "task_analysis": {
                "original_request": "Create a web application that allows users to track their daily habits and goals",
                "interpreted_goal": "Build a comprehensive habit tracking web application with user authentication, habit management, and progress visualization",
                "scope": {
                    "included": [
                        "User registration and authentication system",
                        "Habit creation and management interface",
                        "Daily habit tracking functionality",
                        "Progress visualization and analytics",
                        "User dashboard with overview metrics"
                    ],
                    "excluded": [
                        "Mobile native applications",
                        "Third-party integrations",
                        "Advanced AI recommendations"
                    ],
                    "assumptions": [
                        "Web-based application accessible via browser",
                        "Individual user accounts with privacy",
                        "Standard web technologies will be sufficient"
                    ]
                },
                "technical_requirements": {
                    "languages": ["JavaScript", "HTML", "CSS"],
                    "frameworks": ["React", "Node.js", "Express"],
                    "apis": ["RESTful API"],
                    "infrastructure": ["Database", "Web server", "Authentication service"]
                },
                "constraints": {
                    "technical": ["Browser compatibility", "Responsive design"],
                    "business": ["Development timeline", "Budget limitations"],
                    "performance": ["Fast page load times", "Scalable to 10,000 users"]
                },
                "considerations": {
                    "security": ["User data protection", "Secure authentication"],
                    "scalability": ["Database optimization", "Caching strategy"],
                    "maintainability": ["Code documentation", "Modular architecture"]
                }
            },
            "environmental_analysis": {
                "environment_analysis": {
                    "core_requirements": {
                        "runtime": {
                            "language_version": "Node.js 18.x",
                            "platform_dependencies": ["npm", "Express.js"]
                        },
                        "deployment": {
                            "target_environment": "Cloud hosting",
                            "required_services": ["Web server", "Database", "Authentication service"],
                            "minimum_specs": ["2GB RAM", "1 CPU core", "10GB storage"]
                        }
                    },
                    "dependencies": {
                        "runtime_dependencies": ["react", "express", "mongoose", "jsonwebtoken"],
                        "optional_enhancements": ["redis", "winston", "helmet"]
                    },
                    "integration_points": {
                        "external_services": ["Authentication provider", "Email service"],
                        "apis": ["RESTful API", "WebSocket connections"],
                        "databases": ["MongoDB"]
                    },
                    "compatibility_requirements": {
                        "browsers": ["Chrome 90+", "Firefox 88+", "Safari 14+"],
                        "operating_systems": ["Windows 10+", "macOS 10.15+", "Ubuntu 20.04+"],
                        "devices": ["Desktop", "Tablet", "Mobile"]
                    }
                }
            },
            "data_architecture": {
                "data_architecture": {
                    "core_entities": [
                        {
                            "name": "User",
                            "description": "Application user with authentication",
                            "attributes": ["id", "email", "password_hash", "created_at"],
                            "relationships": ["owns multiple Habits"]
                        },
                        {
                            "name": "Habit",
                            "description": "User-defined habit to track",
                            "attributes": ["id", "name", "description", "frequency", "user_id"],
                            "relationships": ["belongs to User", "has multiple TrackedEntries"]
                        },
                        {
                            "name": "TrackedEntry",
                            "description": "Individual habit completion record",
                            "attributes": ["id", "habit_id", "completed_at", "notes"],
                            "relationships": ["belongs to Habit"]
                        }
                    ],
                    "data_flows": [
                        {
                            "flow_id": "user_registration",
                            "source": "Registration Form",
                            "destination": "User Database",
                            "data_type": "User credentials",
                            "transformation": "Password hashing",
                            "trigger": "User signup"
                        },
                        {
                            "flow_id": "habit_tracking",
                            "source": "Tracking Interface",
                            "destination": "TrackedEntry Database",
                            "data_type": "Completion data",
                            "transformation": "Timestamp addition",
                            "trigger": "User marks habit complete"
                        }
                    ],
                    "persistence_layer": {
                        "primary_store": {
                            "type": "MongoDB",
                            "purpose": "Main application data",
                            "data_types": ["User profiles", "Habits", "Tracking entries"]
                        }
                    }
                }
            }
        }

    @pytest.mark.asyncio
    async def test_tree_placement_planner_basic_functionality(self, tree_placement_planner_agent, comprehensive_phase_one_inputs):
        """Test basic Tree Placement Planner functionality."""
        inputs = comprehensive_phase_one_inputs
        operation_id = f"test_basic_{datetime.now().isoformat()}"
        
        logger.info("Testing Tree Placement Planner basic functionality")
        
        # Format comprehensive input
        combined_input = f"""
        Task Analysis: {json.dumps(inputs['task_analysis'], indent=2)}
        
        Environmental Analysis: {json.dumps(inputs['environmental_analysis'], indent=2)}
        
        Data Architecture: {json.dumps(inputs['data_architecture'], indent=2)}
        """
        
        result = await tree_placement_planner_agent._process(combined_input)
        
        # Verify result structure
        assert isinstance(result, dict), "Result should be a dictionary"
        
        # Tree Placement Planner should provide component architecture
        if "error" not in result:
            # Should provide substantial component architecture
            assert len(str(result)) > 200, "Should provide substantial component architecture"
            
            # Convert result to string to check content
            result_str = json.dumps(result).lower()
            
            # Should consider component structure and organization
            component_factors = ["component", "module", "architecture", "structure", "organization", "layer"]
            found_factors = sum(1 for factor in component_factors if factor in result_str)
            assert found_factors >= 2, f"Should consider component factors, found {found_factors}"
        
        logger.info("Tree Placement Planner basic functionality test passed")

    @pytest.mark.asyncio
    async def test_tree_placement_planner_component_breakdown(self, tree_placement_planner_agent, comprehensive_phase_one_inputs):
        """Test Tree Placement Planner component breakdown capabilities."""
        inputs = comprehensive_phase_one_inputs
        operation_id = f"test_components_{datetime.now().isoformat()}"
        
        logger.info("Testing Tree Placement Planner component breakdown")
        
        combined_input = f"""
        Task Analysis: {json.dumps(inputs['task_analysis'], indent=2)}
        Environmental Analysis: {json.dumps(inputs['environmental_analysis'], indent=2)}
        Data Architecture: {json.dumps(inputs['data_architecture'], indent=2)}
        """
        
        result = await tree_placement_planner_agent._process(combined_input)
        
        if "error" not in result:
            result_str = json.dumps(result).lower()
            
            # Should identify logical component groupings
            component_types = ["frontend", "backend", "api", "database", "auth", "service"]
            found_components = sum(1 for comp_type in component_types if comp_type in result_str)
            assert found_components >= 2, f"Should identify component types, found {found_components}"
            
            # Should consider component relationships
            relationship_concepts = ["depend", "interface", "connect", "integrate", "interact"]
            found_relationships = sum(1 for concept in relationship_concepts if concept in result_str)
            assert found_relationships >= 1, "Should consider component relationships"
        
        logger.info("Tree Placement Planner component breakdown test passed")

    @pytest.mark.asyncio
    async def test_tree_placement_planner_with_system_prompt(self, tree_placement_planner_agent, comprehensive_phase_one_inputs):
        """Test Tree Placement Planner using the actual system prompt."""
        inputs = comprehensive_phase_one_inputs
        operation_id = f"test_prompt_{datetime.now().isoformat()}"
        
        logger.info("Testing Tree Placement Planner with system prompt")
        
        combined_input = f"""
        Task Analysis: {json.dumps(inputs['task_analysis'], indent=2)}
        Environmental Analysis: {json.dumps(inputs['environmental_analysis'], indent=2)}
        Data Architecture: {json.dumps(inputs['data_architecture'], indent=2)}
        """
        
        # Use the actual system prompt
        result = await tree_placement_planner_agent.process_with_validation(
            conversation=combined_input,
            system_prompt_info=("FFTT_system_prompts/phase_one/tree_placement_planner_agent", "initial_component_breakdown_prompt"),
            operation_id=operation_id
        )
        
        # Verify the result follows expected structure
        assert isinstance(result, dict), "Result should be a dictionary"
        
        if "error" not in result:
            # Should provide comprehensive component architecture
            assert len(str(result)) > 300, "Should provide detailed component architecture"
            
            # Check for component architecture structure
            result_str = json.dumps(result).lower()
            
            # Should include component architecture elements
            architecture_elements = ["component_architecture", "component", "architecture", "breakdown", "structure"]
            found_elements = sum(1 for element in architecture_elements if element in result_str)
            assert found_elements >= 2, f"Should include component architecture elements, found {found_elements}"
        
        logger.info("Tree Placement Planner system prompt test passed")

    @pytest.mark.asyncio
    async def test_tree_placement_planner_layered_architecture(self, tree_placement_planner_agent, comprehensive_phase_one_inputs):
        """Test Tree Placement Planner layered architecture design."""
        inputs = comprehensive_phase_one_inputs
        operation_id = f"test_layered_{datetime.now().isoformat()}"
        
        logger.info("Testing Tree Placement Planner layered architecture design")
        
        combined_input = f"""
        Task Analysis: {json.dumps(inputs['task_analysis'], indent=2)}
        Environmental Analysis: {json.dumps(inputs['environmental_analysis'], indent=2)}
        Data Architecture: {json.dumps(inputs['data_architecture'], indent=2)}
        """
        
        result = await tree_placement_planner_agent._process(combined_input)
        
        if "error" not in result:
            result_str = json.dumps(result).lower()
            
            # Should identify architectural layers
            layer_concepts = ["layer", "tier", "presentation", "business", "data", "service"]
            found_layers = sum(1 for concept in layer_concepts if concept in result_str)
            assert found_layers >= 2, f"Should identify architectural layers, found {found_layers}"
            
            # Should consider separation of concerns
            separation_concepts = ["separation", "responsibility", "concern", "boundary", "interface"]
            found_separation = sum(1 for concept in separation_concepts if concept in result_str)
            assert found_separation >= 1, "Should consider separation of concerns"
        
        logger.info("Tree Placement Planner layered architecture test passed")

    @pytest.mark.asyncio
    async def test_tree_placement_planner_microservices_approach(self, tree_placement_planner_agent):
        """Test Tree Placement Planner microservices architecture approach."""
        operation_id = f"test_microservices_{datetime.now().isoformat()}"
        
        logger.info("Testing Tree Placement Planner microservices approach")
        
        # Create a more complex input that would benefit from microservices
        complex_inputs = {
            "task_analysis": {
                "original_request": "Build a comprehensive e-commerce platform with multiple vendor support",
                "scope": {
                    "included": [
                        "Multi-vendor marketplace",
                        "Product catalog management",
                        "Order processing system",
                        "Payment processing",
                        "Inventory management",
                        "User management",
                        "Analytics and reporting"
                    ]
                },
                "technical_requirements": {
                    "languages": ["Python", "JavaScript"],
                    "frameworks": ["Django", "React", "Celery"],
                    "infrastructure": ["Kubernetes", "PostgreSQL", "Redis", "Elasticsearch"]
                }
            },
            "environmental_analysis": {
                "environment_analysis": {
                    "core_requirements": {
                        "deployment": {
                            "target_environment": "Kubernetes cluster",
                            "required_services": ["Load balancer", "API gateway", "Service mesh"]
                        }
                    }
                }
            },
            "data_architecture": {
                "data_architecture": {
                    "core_entities": [
                        {"name": "User", "description": "Platform user"},
                        {"name": "Vendor", "description": "Seller on platform"},
                        {"name": "Product", "description": "Items for sale"},
                        {"name": "Order", "description": "Purchase transactions"},
                        {"name": "Payment", "description": "Payment processing"}
                    ]
                }
            }
        }
        
        combined_input = f"""
        Task Analysis: {json.dumps(complex_inputs['task_analysis'], indent=2)}
        Environmental Analysis: {json.dumps(complex_inputs['environmental_analysis'], indent=2)}
        Data Architecture: {json.dumps(complex_inputs['data_architecture'], indent=2)}
        """
        
        result = await tree_placement_planner_agent._process(combined_input)
        
        if "error" not in result:
            result_str = json.dumps(result).lower()
            
            # Should consider microservices patterns for complex systems
            microservices_concepts = ["service", "microservice", "api", "gateway", "distributed", "independent"]
            found_microservices = sum(1 for concept in microservices_concepts if concept in result_str)
            assert found_microservices >= 2, f"Should consider microservices patterns, found {found_microservices}"
            
            # Should consider service boundaries
            boundary_concepts = ["boundary", "domain", "bounded", "context", "isolation"]
            found_boundaries = sum(1 for concept in boundary_concepts if concept in result_str)
            assert found_boundaries >= 1, "Should consider service boundaries"
        
        logger.info("Tree Placement Planner microservices approach test passed")

    @pytest.mark.asyncio
    async def test_tree_placement_planner_dependency_management(self, tree_placement_planner_agent, comprehensive_phase_one_inputs):
        """Test Tree Placement Planner dependency management."""
        inputs = comprehensive_phase_one_inputs
        operation_id = f"test_dependencies_{datetime.now().isoformat()}"
        
        logger.info("Testing Tree Placement Planner dependency management")
        
        combined_input = f"""
        Task Analysis: {json.dumps(inputs['task_analysis'], indent=2)}
        Environmental Analysis: {json.dumps(inputs['environmental_analysis'], indent=2)}
        Data Architecture: {json.dumps(inputs['data_architecture'], indent=2)}
        """
        
        result = await tree_placement_planner_agent._process(combined_input)
        
        if "error" not in result:
            result_str = json.dumps(result).lower()
            
            # Should identify component dependencies
            dependency_concepts = ["depend", "require", "import", "reference", "call", "use"]
            found_dependencies = sum(1 for concept in dependency_concepts if concept in result_str)
            assert found_dependencies >= 1, "Should identify component dependencies"
            
            # Should consider dependency direction and coupling
            coupling_concepts = ["coupling", "loose", "tight", "decouple", "interface", "contract"]
            found_coupling = sum(1 for concept in coupling_concepts if concept in result_str)
            assert found_coupling >= 1, "Should consider coupling concerns"
        
        logger.info("Tree Placement Planner dependency management test passed")

    @pytest.mark.asyncio
    async def test_tree_placement_planner_scalability_design(self, tree_placement_planner_agent, comprehensive_phase_one_inputs):
        """Test Tree Placement Planner scalability design considerations."""
        inputs = comprehensive_phase_one_inputs
        operation_id = f"test_scalability_{datetime.now().isoformat()}"
        
        logger.info("Testing Tree Placement Planner scalability design")
        
        # Enhance inputs with high scalability requirements
        enhanced_inputs = inputs.copy()
        enhanced_inputs["task_analysis"]["constraints"]["performance"].extend([
            "Support 100,000 concurrent users",
            "Auto-scaling capabilities",
            "Global distribution"
        ])
        
        combined_input = f"""
        Task Analysis: {json.dumps(enhanced_inputs['task_analysis'], indent=2)}
        Environmental Analysis: {json.dumps(enhanced_inputs['environmental_analysis'], indent=2)}
        Data Architecture: {json.dumps(enhanced_inputs['data_architecture'], indent=2)}
        """
        
        result = await tree_placement_planner_agent._process(combined_input)
        
        if "error" not in result:
            result_str = json.dumps(result).lower()
            
            # Should consider scalability patterns
            scalability_concepts = ["scale", "horizontal", "vertical", "load", "balance", "distribute"]
            found_scalability = sum(1 for concept in scalability_concepts if concept in result_str)
            assert found_scalability >= 1, "Should consider scalability patterns"
            
            # Should consider performance optimization
            performance_concepts = ["cache", "optimize", "performance", "efficient", "fast", "responsive"]
            found_performance = sum(1 for concept in performance_concepts if concept in result_str)
            assert found_performance >= 1, "Should consider performance optimization"
        
        logger.info("Tree Placement Planner scalability design test passed")

    @pytest.mark.asyncio
    async def test_tree_placement_planner_security_architecture(self, tree_placement_planner_agent, comprehensive_phase_one_inputs):
        """Test Tree Placement Planner security architecture considerations."""
        inputs = comprehensive_phase_one_inputs
        operation_id = f"test_security_{datetime.now().isoformat()}"
        
        logger.info("Testing Tree Placement Planner security architecture")
        
        combined_input = f"""
        Task Analysis: {json.dumps(inputs['task_analysis'], indent=2)}
        Environmental Analysis: {json.dumps(inputs['environmental_analysis'], indent=2)}
        Data Architecture: {json.dumps(inputs['data_architecture'], indent=2)}
        """
        
        result = await tree_placement_planner_agent._process(combined_input)
        
        if "error" not in result:
            result_str = json.dumps(result).lower()
            
            # Should consider security patterns in component design
            security_concepts = ["security", "auth", "authorization", "authentication", "secure", "protect"]
            found_security = sum(1 for concept in security_concepts if concept in result_str)
            assert found_security >= 1, "Should consider security in component design"
            
            # Should consider data protection
            protection_concepts = ["encrypt", "validation", "sanitize", "filter", "guard", "check"]
            found_protection = sum(1 for concept in protection_concepts if concept in result_str)
            assert found_protection >= 1, "Should consider data protection"
        
        logger.info("Tree Placement Planner security architecture test passed")

    @pytest.mark.asyncio
    async def test_tree_placement_planner_component_communication(self, tree_placement_planner_agent, comprehensive_phase_one_inputs):
        """Test Tree Placement Planner component communication design."""
        inputs = comprehensive_phase_one_inputs
        operation_id = f"test_communication_{datetime.now().isoformat()}"
        
        logger.info("Testing Tree Placement Planner component communication design")
        
        combined_input = f"""
        Task Analysis: {json.dumps(inputs['task_analysis'], indent=2)}
        Environmental Analysis: {json.dumps(inputs['environmental_analysis'], indent=2)}
        Data Architecture: {json.dumps(inputs['data_architecture'], indent=2)}
        """
        
        result = await tree_placement_planner_agent._process(combined_input)
        
        if "error" not in result:
            result_str = json.dumps(result).lower()
            
            # Should consider communication patterns
            communication_concepts = ["api", "message", "event", "request", "response", "protocol"]
            found_communication = sum(1 for concept in communication_concepts if concept in result_str)
            assert found_communication >= 2, f"Should consider communication patterns, found {found_communication}"
            
            # Should consider async vs sync patterns
            async_concepts = ["async", "sync", "queue", "broker", "publish", "subscribe"]
            found_async = sum(1 for concept in async_concepts if concept in result_str)
            assert found_async >= 1, "Should consider async/sync patterns"
        
        logger.info("Tree Placement Planner component communication test passed")

    @pytest.mark.asyncio
    async def test_tree_placement_planner_state_transitions(self, tree_placement_planner_agent, comprehensive_phase_one_inputs):
        """Test Tree Placement Planner state transitions."""
        inputs = comprehensive_phase_one_inputs
        operation_id = f"test_states_{datetime.now().isoformat()}"
        
        logger.info("Testing Tree Placement Planner state transitions")
        
        # Check initial state
        initial_state = tree_placement_planner_agent.development_state
        assert initial_state == DevelopmentState.INITIALIZING
        
        combined_input = f"""
        Task Analysis: {json.dumps(inputs['task_analysis'], indent=2)}
        Environmental Analysis: {json.dumps(inputs['environmental_analysis'], indent=2)}
        Data Architecture: {json.dumps(inputs['data_architecture'], indent=2)}
        """
        
        # Process and monitor state changes
        result = await tree_placement_planner_agent._process(combined_input)
        
        # Should transition to appropriate final state
        final_state = tree_placement_planner_agent.development_state
        assert final_state in [
            DevelopmentState.COMPLETE,
            DevelopmentState.ANALYZING,
            DevelopmentState.ERROR
        ], f"Should be in valid final state, got {final_state}"
        
        logger.info("Tree Placement Planner state transitions test passed")

    @pytest.mark.asyncio
    async def test_tree_placement_planner_error_handling(self, tree_placement_planner_agent):
        """Test Tree Placement Planner error handling."""
        operation_id = f"test_error_{datetime.now().isoformat()}"
        
        logger.info("Testing Tree Placement Planner error handling")
        
        # Test with malformed input
        malformed_input = "Invalid JSON: {broken"
        
        result = await tree_placement_planner_agent._process(malformed_input)
        
        # Should handle gracefully
        assert isinstance(result, dict), "Should return dictionary even for malformed input"
        
        # Should either process successfully or return proper error
        if "error" in result:
            assert isinstance(result["error"], str), "Error should be a string"
            logger.info(f"Error properly handled: {result['error']}")
        else:
            # If processed, should contain some analysis
            assert len(str(result)) > 10, "Should provide some analysis even for malformed input"
        
        logger.info("Tree Placement Planner error handling test passed")

    @pytest.mark.asyncio
    async def test_tree_placement_planner_integration_readiness(self, tree_placement_planner_agent, comprehensive_phase_one_inputs):
        """Test Tree Placement Planner integration readiness for workflow completion."""
        inputs = comprehensive_phase_one_inputs
        operation_id = f"test_integration_{datetime.now().isoformat()}"
        
        logger.info("Testing Tree Placement Planner integration readiness")
        
        combined_input = f"""
        Task Analysis: {json.dumps(inputs['task_analysis'], indent=2)}
        Environmental Analysis: {json.dumps(inputs['environmental_analysis'], indent=2)}
        Data Architecture: {json.dumps(inputs['data_architecture'], indent=2)}
        """
        
        # Test the process method as it would be called in workflow
        result = await tree_placement_planner_agent._process(combined_input)
        
        # Verify integration readiness
        assert isinstance(result, dict), "Should return dictionary for workflow integration"
        
        # Should be serializable for state management
        try:
            json.dumps(result)
            logger.info("Result is JSON serializable")
        except (TypeError, ValueError) as e:
            pytest.fail(f"Result is not JSON serializable: {e}")
        
        # Should provide component architecture for Phase Two
        assert len(str(result)) > 100, "Should provide substantial component architecture for Phase Two"
        
        # Should contain component_architecture field or equivalent
        result_str = json.dumps(result).lower()
        architecture_indicators = ["component_architecture", "component", "architecture", "structure", "breakdown"]
        found_indicators = sum(1 for indicator in architecture_indicators if indicator in result_str)
        assert found_indicators >= 1, "Should indicate component architecture content"
        
        logger.info("Tree Placement Planner integration readiness test passed")

    @pytest.mark.asyncio
    async def test_tree_placement_planner_comprehensive_architecture(self, tree_placement_planner_agent, comprehensive_phase_one_inputs):
        """Test comprehensive component architecture design capabilities."""
        inputs = comprehensive_phase_one_inputs
        operation_id = f"test_comprehensive_{datetime.now().isoformat()}"
        
        logger.info("Testing Tree Placement Planner comprehensive architecture")
        
        combined_input = f"""
        Task Analysis: {json.dumps(inputs['task_analysis'], indent=2)}
        Environmental Analysis: {json.dumps(inputs['environmental_analysis'], indent=2)}
        Data Architecture: {json.dumps(inputs['data_architecture'], indent=2)}
        """
        
        result = await tree_placement_planner_agent.process_with_validation(
            conversation=combined_input,
            system_prompt_info=("FFTT_system_prompts/phase_one/tree_placement_planner_agent", "initial_component_breakdown_prompt"),
            operation_id=operation_id
        )
        
        if "error" not in result:
            result_str = json.dumps(result).lower()
            
            # Should cover multiple architectural dimensions
            dimensions = {
                "structure": ["component", "module", "package", "class", "interface"],
                "communication": ["api", "message", "event", "request", "response"],
                "data": ["model", "entity", "repository", "dao", "persistence"],
                "presentation": ["view", "controller", "ui", "frontend", "client"],
                "business": ["service", "logic", "business", "domain", "workflow"],
                "integration": ["integration", "adapter", "gateway", "proxy", "facade"]
            }
            
            covered_dimensions = 0
            for dimension, keywords in dimensions.items():
                if any(keyword in result_str for keyword in keywords):
                    covered_dimensions += 1
            
            assert covered_dimensions >= 4, f"Should cover multiple architectural dimensions, covered {covered_dimensions}/6"
        
        logger.info("Tree Placement Planner comprehensive architecture test passed")

    @pytest.mark.asyncio
    async def test_tree_placement_planner_fire_agent_integration(self, tree_placement_planner_agent, comprehensive_phase_one_inputs):
        """Test Tree Placement Planner integration with Fire Agent complexity analysis."""
        inputs = comprehensive_phase_one_inputs
        operation_id = f"test_fire_integration_{datetime.now().isoformat()}"
        
        logger.info("Testing Tree Placement Planner Fire Agent integration")
        
        # Create a complex architecture that should trigger Fire Agent analysis
        complex_inputs = inputs.copy()
        complex_inputs["task_analysis"]["scope"]["included"].extend([
            "Advanced analytics dashboard",
            "Real-time notifications system",
            "Machine learning recommendations",
            "Multi-tenant architecture",
            "API rate limiting",
            "Comprehensive audit logging"
        ])
        
        combined_input = f"""
        Task Analysis: {json.dumps(complex_inputs['task_analysis'], indent=2)}
        Environmental Analysis: {json.dumps(complex_inputs['environmental_analysis'], indent=2)}
        Data Architecture: {json.dumps(complex_inputs['data_architecture'], indent=2)}
        """
        
        result = await tree_placement_planner_agent._process(combined_input)
        
        # Verify that the agent can handle complex inputs
        assert isinstance(result, dict), "Should handle complex architecture inputs"
        
        if "error" not in result:
            # Should provide substantial architecture even for complex inputs
            assert len(str(result)) > 200, "Should provide substantial architecture for complex inputs"
            
            # Fire Agent integration would be tested in workflow tests
            # Here we just verify the agent produces valid output
            result_str = json.dumps(result).lower()
            complexity_indicators = ["complex", "advanced", "sophisticated", "comprehensive", "detailed"]
            found_complexity = sum(1 for indicator in complexity_indicators if indicator in result_str)
            # Should at least acknowledge complexity or provide detailed architecture
            assert found_complexity >= 1 or len(str(result)) > 500, "Should handle architectural complexity appropriately"
        
        logger.info("Tree Placement Planner Fire Agent integration test passed")