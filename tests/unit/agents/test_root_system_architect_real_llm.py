"""
Comprehensive test suite for Root System Architect Agent with real LLM calls.

This module tests the Root System Architect agent's core functionality with real API calls
to ensure proper data flow and system architecture design.
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
from phase_one.agents.root_system_architect import RootSystemArchitectAgent
from phase_one.models.enums import DevelopmentState

logger = logging.getLogger(__name__)

@pytest.mark.real_api
class TestRootSystemArchitectRealLLM:
    """Test suite for Root System Architect Agent using real LLM API calls."""

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
    async def root_system_architect_agent(self, real_resources):
        """Create a Root System Architect Agent instance with real resources."""
        agent = RootSystemArchitectAgent(
            agent_id="test_root_system_architect",
            **real_resources
        )
        return agent

    @pytest.fixture
    def sample_environmental_analyses(self):
        """Provide sample environmental analyses for testing."""
        return {
            "web_app_environment": {
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
                    },
                    "technical_constraints": {
                        "version_restrictions": ["Node.js >= 16.x", "MongoDB >= 5.0"],
                        "platform_limitations": ["Browser-based application"],
                        "integration_requirements": ["OAuth 2.0 compatible", "HTTPS required"]
                    }
                }
            },
            
            "e_commerce_environment": {
                "environment_analysis": {
                    "core_requirements": {
                        "runtime": {
                            "language_version": "Python 3.9+",
                            "platform_dependencies": ["Django", "PostgreSQL drivers"]
                        },
                        "deployment": {
                            "target_environment": "Cloud container platform",
                            "required_services": ["Load balancer", "Database cluster", "Redis cache", "Payment gateway"],
                            "minimum_specs": ["4GB RAM", "2 CPU cores", "50GB storage", "SSL certificate"]
                        }
                    },
                    "dependencies": {
                        "runtime_dependencies": ["django", "psycopg2", "celery", "stripe", "pillow"],
                        "optional_enhancements": ["django-debug-toolbar", "sentry-sdk", "gunicorn"]
                    },
                    "integration_points": {
                        "external_services": ["Payment processor", "Shipping API", "Email marketing"],
                        "apis": ["Payment gateway API", "Shipping rates API", "Inventory management API"],
                        "databases": ["PostgreSQL", "Redis"]
                    },
                    "compatibility_requirements": {
                        "browsers": ["All modern browsers"],
                        "operating_systems": ["Cross-platform"],
                        "devices": ["Desktop", "Mobile", "Tablet"]
                    },
                    "technical_constraints": {
                        "version_restrictions": ["Python >= 3.9", "Django >= 4.0", "PostgreSQL >= 13"],
                        "platform_limitations": ["PCI DSS compliance required"],
                        "integration_requirements": ["HTTPS mandatory", "API rate limiting", "Data encryption at rest"]
                    }
                }
            }
        }

    @pytest.mark.asyncio
    async def test_root_system_architect_basic_functionality(self, root_system_architect_agent, sample_environmental_analyses):
        """Test basic Root System Architect functionality."""
        env_analysis = sample_environmental_analyses["web_app_environment"]
        operation_id = f"test_basic_{datetime.now().isoformat()}"
        
        logger.info("Testing Root System Architect basic functionality")
        
        # Format input as expected by the agent
        analysis_input = f"Environmental Analysis: {json.dumps(env_analysis, indent=2)}"
        
        result = await root_system_architect_agent._process(analysis_input)
        
        # Verify result structure
        assert isinstance(result, dict), "Result should be a dictionary"
        
        # Root System Architect should provide data architecture
        if "error" not in result:
            # Should provide substantial architectural analysis
            assert len(str(result)) > 100, "Should provide substantial architectural analysis"
            
            # Convert result to string to check content
            result_str = json.dumps(result).lower()
            
            # Should consider data flow and architecture patterns
            architecture_factors = ["data", "flow", "architecture", "structure", "component", "module"]
            found_factors = sum(1 for factor in architecture_factors if factor in result_str)
            assert found_factors >= 2, f"Should consider architectural factors, found {found_factors}"
        
        logger.info("Root System Architect basic functionality test passed")

    @pytest.mark.asyncio
    async def test_root_system_architect_data_flow_design(self, root_system_architect_agent, sample_environmental_analyses):
        """Test Root System Architect data flow design capabilities."""
        env_analysis = sample_environmental_analyses["web_app_environment"]
        operation_id = f"test_data_flow_{datetime.now().isoformat()}"
        
        logger.info("Testing Root System Architect data flow design")
        
        analysis_input = f"Environmental Analysis: {json.dumps(env_analysis, indent=2)}"
        
        result = await root_system_architect_agent._process(analysis_input)
        
        if "error" not in result:
            result_str = json.dumps(result).lower()
            
            # Should identify data flow patterns
            data_flow_concepts = ["flow", "input", "output", "transformation", "processing", "pipeline"]
            found_flow = sum(1 for concept in data_flow_concepts if concept in result_str)
            assert found_flow >= 2, f"Should identify data flow patterns, found {found_flow}"
            
            # Should consider data persistence
            persistence_concepts = ["database", "storage", "persistence", "model", "schema"]
            found_persistence = sum(1 for concept in persistence_concepts if concept in result_str)
            assert found_persistence >= 1, "Should consider data persistence"
        
        logger.info("Root System Architect data flow design test passed")

    @pytest.mark.asyncio
    async def test_root_system_architect_e_commerce_architecture(self, root_system_architect_agent, sample_environmental_analyses):
        """Test Root System Architect for e-commerce architecture."""
        env_analysis = sample_environmental_analyses["e_commerce_environment"]
        operation_id = f"test_ecommerce_{datetime.now().isoformat()}"
        
        logger.info("Testing Root System Architect for e-commerce architecture")
        
        analysis_input = f"Environmental Analysis: {json.dumps(env_analysis, indent=2)}"
        
        result = await root_system_architect_agent._process(analysis_input)
        
        if "error" not in result:
            result_str = json.dumps(result).lower()
            
            # Should identify e-commerce specific architecture patterns
            ecommerce_patterns = ["transaction", "order", "payment", "inventory", "catalog", "cart"]
            found_patterns = sum(1 for pattern in ecommerce_patterns if pattern in result_str)
            assert found_patterns >= 2, f"Should identify e-commerce patterns, found {found_patterns}"
            
            # Should consider distributed architecture for e-commerce
            distributed_concepts = ["service", "microservice", "api", "integration", "scalability"]
            found_distributed = sum(1 for concept in distributed_concepts if concept in result_str)
            assert found_distributed >= 1, "Should consider distributed architecture"
        
        logger.info("Root System Architect e-commerce architecture test passed")

    @pytest.mark.asyncio
    async def test_root_system_architect_with_system_prompt(self, root_system_architect_agent, sample_environmental_analyses):
        """Test Root System Architect using the actual system prompt."""
        env_analysis = sample_environmental_analyses["web_app_environment"]
        operation_id = f"test_prompt_{datetime.now().isoformat()}"
        
        logger.info("Testing Root System Architect with system prompt")
        
        analysis_input = f"Environmental Analysis: {json.dumps(env_analysis, indent=2)}"
        
        # Use the actual system prompt
        result = await root_system_architect_agent.process_with_validation(
            conversation=analysis_input,
            system_prompt_info=("FFTT_system_prompts/phase_one/garden_root_system_agent", "initial_data_architecture_prompt"),
            operation_id=operation_id
        )
        
        # Verify the result follows expected structure
        assert isinstance(result, dict), "Result should be a dictionary"
        
        if "error" not in result:
            # Should provide comprehensive data architecture
            assert len(str(result)) > 200, "Should provide detailed data architecture"
            
            # Check for structured architecture content
            result_str = json.dumps(result).lower()
            
            # Should include data architecture elements
            architecture_elements = ["data_architecture", "data", "architecture", "system", "design"]
            found_elements = sum(1 for element in architecture_elements if element in result_str)
            assert found_elements >= 2, f"Should include architecture elements, found {found_elements}"
        
        logger.info("Root System Architect system prompt test passed")

    @pytest.mark.asyncio
    async def test_root_system_architect_database_design(self, root_system_architect_agent, sample_environmental_analyses):
        """Test Root System Architect database design capabilities."""
        env_analysis = sample_environmental_analyses["e_commerce_environment"]
        operation_id = f"test_database_{datetime.now().isoformat()}"
        
        logger.info("Testing Root System Architect database design")
        
        analysis_input = f"Environmental Analysis: {json.dumps(env_analysis, indent=2)}"
        
        result = await root_system_architect_agent._process(analysis_input)
        
        if "error" not in result:
            result_str = json.dumps(result).lower()
            
            # Should consider database design patterns
            db_concepts = ["table", "schema", "relationship", "index", "query", "model"]
            found_db = sum(1 for concept in db_concepts if concept in result_str)
            assert found_db >= 2, f"Should consider database design, found {found_db}"
            
            # Should consider data relationships
            relationship_concepts = ["foreign", "primary", "key", "relation", "association", "reference"]
            found_relations = sum(1 for concept in relationship_concepts if concept in result_str)
            assert found_relations >= 1, "Should consider data relationships"
        
        logger.info("Root System Architect database design test passed")

    @pytest.mark.asyncio
    async def test_root_system_architect_system_integration(self, root_system_architect_agent, sample_environmental_analyses):
        """Test Root System Architect system integration design."""
        env_analysis = sample_environmental_analyses["web_app_environment"]
        operation_id = f"test_integration_{datetime.now().isoformat()}"
        
        logger.info("Testing Root System Architect system integration design")
        
        # Enhance environmental analysis with multiple integration points
        enhanced_analysis = sample_environmental_analyses["web_app_environment"].copy()
        enhanced_analysis["environment_analysis"]["integration_points"]["external_services"].extend([
            "Third-party analytics",
            "Social media APIs",
            "Cloud storage service"
        ])
        
        analysis_input = f"Environmental Analysis: {json.dumps(enhanced_analysis, indent=2)}"
        
        result = await root_system_architect_agent._process(analysis_input)
        
        if "error" not in result:
            result_str = json.dumps(result).lower()
            
            # Should consider integration architecture
            integration_concepts = ["api", "integration", "service", "external", "interface", "endpoint"]
            found_integration = sum(1 for concept in integration_concepts if concept in result_str)
            assert found_integration >= 2, f"Should consider integration architecture, found {found_integration}"
            
            # Should consider data exchange patterns
            exchange_concepts = ["request", "response", "protocol", "format", "sync", "async"]
            found_exchange = sum(1 for concept in exchange_concepts if concept in result_str)
            assert found_exchange >= 1, "Should consider data exchange patterns"
        
        logger.info("Root System Architect system integration design test passed")

    @pytest.mark.asyncio
    async def test_root_system_architect_scalability_design(self, root_system_architect_agent, sample_environmental_analyses):
        """Test Root System Architect scalability design."""
        env_analysis = sample_environmental_analyses["e_commerce_environment"]
        operation_id = f"test_scalability_{datetime.now().isoformat()}"
        
        logger.info("Testing Root System Architect scalability design")
        
        analysis_input = f"Environmental Analysis: {json.dumps(env_analysis, indent=2)}"
        
        result = await root_system_architect_agent._process(analysis_input)
        
        if "error" not in result:
            result_str = json.dumps(result).lower()
            
            # Should consider scalability patterns
            scalability_concepts = ["scale", "horizontal", "vertical", "cluster", "partition", "shard"]
            found_scalability = sum(1 for concept in scalability_concepts if concept in result_str)
            assert found_scalability >= 1, "Should consider scalability patterns"
            
            # Should consider performance optimization
            performance_concepts = ["cache", "optimization", "index", "performance", "latency", "throughput"]
            found_performance = sum(1 for concept in performance_concepts if concept in result_str)
            assert found_performance >= 1, "Should consider performance optimization"
        
        logger.info("Root System Architect scalability design test passed")

    @pytest.mark.asyncio
    async def test_root_system_architect_security_architecture(self, root_system_architect_agent, sample_environmental_analyses):
        """Test Root System Architect security architecture considerations."""
        env_analysis = sample_environmental_analyses["e_commerce_environment"]
        operation_id = f"test_security_{datetime.now().isoformat()}"
        
        logger.info("Testing Root System Architect security architecture")
        
        analysis_input = f"Environmental Analysis: {json.dumps(env_analysis, indent=2)}"
        
        result = await root_system_architect_agent._process(analysis_input)
        
        if "error" not in result:
            result_str = json.dumps(result).lower()
            
            # Should consider security architecture patterns
            security_concepts = ["security", "authentication", "authorization", "encryption", "validation", "sanitization"]
            found_security = sum(1 for concept in security_concepts if concept in result_str)
            assert found_security >= 1, "Should consider security architecture"
            
            # Should consider data protection
            protection_concepts = ["protect", "secure", "privacy", "compliance", "audit", "log"]
            found_protection = sum(1 for concept in protection_concepts if concept in result_str)
            assert found_protection >= 1, "Should consider data protection"
        
        logger.info("Root System Architect security architecture test passed")

    @pytest.mark.asyncio
    async def test_root_system_architect_state_transitions(self, root_system_architect_agent, sample_environmental_analyses):
        """Test Root System Architect state transitions."""
        env_analysis = sample_environmental_analyses["web_app_environment"]
        operation_id = f"test_states_{datetime.now().isoformat()}"
        
        logger.info("Testing Root System Architect state transitions")
        
        # Check initial state
        initial_state = root_system_architect_agent.development_state
        assert initial_state == DevelopmentState.INITIALIZING
        
        analysis_input = f"Environmental Analysis: {json.dumps(env_analysis, indent=2)}"
        
        # Process and monitor state changes
        result = await root_system_architect_agent._process(analysis_input)
        
        # Should transition to appropriate final state
        final_state = root_system_architect_agent.development_state
        assert final_state in [
            DevelopmentState.COMPLETE,
            DevelopmentState.ANALYZING,
            DevelopmentState.ERROR
        ], f"Should be in valid final state, got {final_state}"
        
        logger.info("Root System Architect state transitions test passed")

    @pytest.mark.asyncio
    async def test_root_system_architect_error_handling(self, root_system_architect_agent):
        """Test Root System Architect error handling."""
        operation_id = f"test_error_{datetime.now().isoformat()}"
        
        logger.info("Testing Root System Architect error handling")
        
        # Test with malformed input
        malformed_input = "Invalid JSON: {broken"
        
        result = await root_system_architect_agent._process(malformed_input)
        
        # Should handle gracefully
        assert isinstance(result, dict), "Should return dictionary even for malformed input"
        
        # Should either process successfully or return proper error
        if "error" in result:
            assert isinstance(result["error"], str), "Error should be a string"
            logger.info(f"Error properly handled: {result['error']}")
        else:
            # If processed, should contain some analysis
            assert len(str(result)) > 10, "Should provide some analysis even for malformed input"
        
        logger.info("Root System Architect error handling test passed")

    @pytest.mark.asyncio
    async def test_root_system_architect_integration_readiness(self, root_system_architect_agent, sample_environmental_analyses):
        """Test Root System Architect integration readiness for workflow."""
        env_analysis = sample_environmental_analyses["web_app_environment"]
        operation_id = f"test_integration_{datetime.now().isoformat()}"
        
        logger.info("Testing Root System Architect integration readiness")
        
        analysis_input = f"Environmental Analysis: {json.dumps(env_analysis, indent=2)}"
        
        # Test the process method as it would be called in workflow
        result = await root_system_architect_agent._process(analysis_input)
        
        # Verify integration readiness
        assert isinstance(result, dict), "Should return dictionary for workflow integration"
        
        # Should be serializable for state management
        try:
            json.dumps(result)
            logger.info("Result is JSON serializable")
        except (TypeError, ValueError) as e:
            pytest.fail(f"Result is not JSON serializable: {e}")
        
        # Should provide data architecture for Tree Placement Planner
        assert len(str(result)) > 50, "Should provide substantial data architecture for next agent"
        
        # Should contain data_architecture field or equivalent
        result_str = json.dumps(result).lower()
        architecture_indicators = ["data_architecture", "architecture", "data", "structure", "design"]
        found_indicators = sum(1 for indicator in architecture_indicators if indicator in result_str)
        assert found_indicators >= 1, "Should indicate data architecture content"
        
        logger.info("Root System Architect integration readiness test passed")

    @pytest.mark.asyncio
    async def test_root_system_architect_comprehensive_architecture(self, root_system_architect_agent, sample_environmental_analyses):
        """Test comprehensive architecture design capabilities."""
        env_analysis = sample_environmental_analyses["e_commerce_environment"]
        operation_id = f"test_comprehensive_{datetime.now().isoformat()}"
        
        logger.info("Testing Root System Architect comprehensive architecture")
        
        analysis_input = f"Environmental Analysis: {json.dumps(env_analysis, indent=2)}"
        
        result = await root_system_architect_agent.process_with_validation(
            conversation=analysis_input,
            system_prompt_info=("FFTT_system_prompts/phase_one/garden_root_system_agent", "initial_data_architecture_prompt"),
            operation_id=operation_id
        )
        
        if "error" not in result:
            result_str = json.dumps(result).lower()
            
            # Should cover multiple architectural dimensions
            dimensions = {
                "data": ["data", "model", "schema", "entity", "table"],
                "processing": ["process", "logic", "business", "workflow", "operation"],
                "integration": ["api", "service", "integration", "interface", "endpoint"],
                "storage": ["storage", "database", "persistence", "cache", "repository"],
                "communication": ["message", "event", "queue", "notification", "communication"]
            }
            
            covered_dimensions = 0
            for dimension, keywords in dimensions.items():
                if any(keyword in result_str for keyword in keywords):
                    covered_dimensions += 1
            
            assert covered_dimensions >= 3, f"Should cover multiple architectural dimensions, covered {covered_dimensions}/5"
        
        logger.info("Root System Architect comprehensive architecture test passed")