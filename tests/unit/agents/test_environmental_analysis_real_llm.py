"""
Comprehensive test suite for Environmental Analysis Agent with real LLM calls.

This module tests the Environmental Analysis agent's core functionality with real API calls
to ensure proper analysis of environmental factors and system constraints.
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
from phase_one.agents.environmental_analysis import EnvironmentalAnalysisAgent
from phase_one.models.enums import DevelopmentState

logger = logging.getLogger(__name__)

@pytest.mark.real_api
class TestEnvironmentalAnalysisRealLLM:
    """Test suite for Environmental Analysis Agent using real LLM API calls."""

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
    async def environmental_analysis_agent(self, real_resources):
        """Create an Environmental Analysis Agent instance with real resources."""
        agent = EnvironmentalAnalysisAgent(
            agent_id="test_environmental_analysis",
            **real_resources
        )
        return agent

    @pytest.fixture
    def sample_task_analyses(self):
        """Provide sample task analyses from Garden Planner for testing."""
        return {
            "web_app_analysis": {
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
            
            "e_commerce_analysis": {
                "original_request": "Build an e-commerce platform for selling handmade crafts",
                "interpreted_goal": "Create a specialized e-commerce platform for artisans to sell handmade crafts with inventory management and payment processing",
                "scope": {
                    "included": [
                        "Product catalog with categories",
                        "Shopping cart and checkout",
                        "Payment processing integration",
                        "Vendor management system",
                        "Order tracking and fulfillment"
                    ],
                    "excluded": [
                        "Marketplace features",
                        "Advanced analytics",
                        "Multi-language support"
                    ],
                    "assumptions": [
                        "Single-vendor initially",
                        "Credit card payments primary",
                        "US market focus"
                    ]
                },
                "technical_requirements": {
                    "languages": ["Python", "JavaScript"],
                    "frameworks": ["Django", "React"],
                    "apis": ["Payment gateway API", "Shipping API"],
                    "infrastructure": ["PostgreSQL", "Redis", "Cloud storage"]
                },
                "constraints": {
                    "technical": ["PCI compliance", "Mobile responsiveness"],
                    "business": ["Transaction fees", "Compliance requirements"],
                    "performance": ["Sub-2 second page loads", "High availability"]
                },
                "considerations": {
                    "security": ["Payment security", "Data encryption"],
                    "scalability": ["Multi-vendor support", "International expansion"],
                    "maintainability": ["API documentation", "Testing coverage"]
                }
            }
        }

    @pytest.mark.asyncio
    async def test_environmental_analysis_basic_functionality(self, environmental_analysis_agent, sample_task_analyses):
        """Test basic environmental analysis functionality."""
        task_analysis = sample_task_analyses["web_app_analysis"]
        operation_id = f"test_basic_{datetime.now().isoformat()}"
        
        logger.info("Testing Environmental Analysis basic functionality")
        
        # Format input as expected by the agent
        analysis_input = f"Task Analysis: {json.dumps(task_analysis, indent=2)}"
        
        result = await environmental_analysis_agent._process(analysis_input)
        
        # Verify result structure
        assert isinstance(result, dict), "Result should be a dictionary"
        
        # Environmental analysis should provide comprehensive environmental factors
        if "error" not in result:
            # Check for environmental analysis structure
            assert len(str(result)) > 100, "Should provide substantial environmental analysis"
            
            # Convert result to string to check content
            result_str = json.dumps(result).lower()
            
            # Should consider deployment and operational factors
            expected_factors = ["deployment", "environment", "infrastructure", "performance", "security"]
            found_factors = sum(1 for factor in expected_factors if factor in result_str)
            assert found_factors >= 2, f"Should consider environmental factors, found {found_factors}"
        
        logger.info("Environmental Analysis basic functionality test passed")

    @pytest.mark.asyncio
    async def test_environmental_analysis_web_app_context(self, environmental_analysis_agent, sample_task_analyses):
        """Test environmental analysis for web application context."""
        task_analysis = sample_task_analyses["web_app_analysis"]
        operation_id = f"test_web_context_{datetime.now().isoformat()}"
        
        logger.info("Testing Environmental Analysis for web application context")
        
        analysis_input = f"Task Analysis: {json.dumps(task_analysis, indent=2)}"
        
        result = await environmental_analysis_agent._process(analysis_input)
        
        if "error" not in result:
            result_str = json.dumps(result).lower()
            
            # Should identify web-specific environmental factors
            web_factors = ["browser", "http", "server", "client", "responsive", "accessibility"]
            found_web_factors = sum(1 for factor in web_factors if factor in result_str)
            assert found_web_factors >= 2, f"Should identify web-specific factors, found {found_web_factors}"
            
            # Should consider scalability for web applications
            scalability_factors = ["scale", "performance", "load", "cache", "database"]
            found_scalability = sum(1 for factor in scalability_factors if factor in result_str)
            assert found_scalability >= 1, "Should consider scalability factors"
        
        logger.info("Environmental Analysis web application context test passed")

    @pytest.mark.asyncio
    async def test_environmental_analysis_e_commerce_context(self, environmental_analysis_agent, sample_task_analyses):
        """Test environmental analysis for e-commerce context."""
        task_analysis = sample_task_analyses["e_commerce_analysis"]
        operation_id = f"test_ecommerce_{datetime.now().isoformat()}"
        
        logger.info("Testing Environmental Analysis for e-commerce context")
        
        analysis_input = f"Task Analysis: {json.dumps(task_analysis, indent=2)}"
        
        result = await environmental_analysis_agent._process(analysis_input)
        
        if "error" not in result:
            result_str = json.dumps(result).lower()
            
            # Should identify e-commerce specific environmental factors
            ecommerce_factors = ["payment", "transaction", "inventory", "security", "compliance", "pci"]
            found_ecommerce = sum(1 for factor in ecommerce_factors if factor in result_str)
            assert found_ecommerce >= 2, f"Should identify e-commerce factors, found {found_ecommerce}"
            
            # Should consider high availability and security
            reliability_factors = ["availability", "redundancy", "backup", "encryption", "secure"]
            found_reliability = sum(1 for factor in reliability_factors if factor in result_str)
            assert found_reliability >= 1, "Should consider reliability factors"
        
        logger.info("Environmental Analysis e-commerce context test passed")

    @pytest.mark.asyncio
    async def test_environmental_analysis_with_system_prompt(self, environmental_analysis_agent, sample_task_analyses):
        """Test environmental analysis using the actual system prompt."""
        task_analysis = sample_task_analyses["web_app_analysis"]
        operation_id = f"test_prompt_{datetime.now().isoformat()}"
        
        logger.info("Testing Environmental Analysis with system prompt")
        
        analysis_input = f"Task Analysis: {json.dumps(task_analysis, indent=2)}"
        
        # Use the actual system prompt
        result = await environmental_analysis_agent.process_with_validation(
            conversation=analysis_input,
            system_prompt_info=("FFTT_system_prompts/phase_one/garden_environmental_analysis_agent", "initial_core_requirements_prompt"),
            operation_id=operation_id
        )
        
        # Verify the result follows expected structure
        assert isinstance(result, dict), "Result should be a dictionary"
        
        if "error" not in result:
            # Should provide comprehensive environmental analysis
            assert len(str(result)) > 200, "Should provide detailed environmental analysis"
            
            # Check for structured analysis content
            result_str = json.dumps(result).lower()
            analysis_areas = ["technical", "operational", "business", "user", "system"]
            found_areas = sum(1 for area in analysis_areas if area in result_str)
            assert found_areas >= 2, f"Should cover multiple analysis areas, found {found_areas}"
        
        logger.info("Environmental Analysis system prompt test passed")

    @pytest.mark.asyncio
    async def test_environmental_analysis_constraint_identification(self, environmental_analysis_agent, sample_task_analyses):
        """Test environmental constraint identification."""
        task_analysis = sample_task_analyses["e_commerce_analysis"]
        operation_id = f"test_constraints_{datetime.now().isoformat()}"
        
        logger.info("Testing Environmental Analysis constraint identification")
        
        analysis_input = f"Task Analysis: {json.dumps(task_analysis, indent=2)}"
        
        result = await environmental_analysis_agent._process(analysis_input)
        
        if "error" not in result:
            result_str = json.dumps(result).lower()
            
            # Should identify environmental constraints
            constraint_types = ["compliance", "regulation", "standard", "requirement", "limitation"]
            found_constraints = sum(1 for constraint in constraint_types if constraint in result_str)
            assert found_constraints >= 1, "Should identify environmental constraints"
            
            # Should consider operational constraints
            operational_factors = ["deployment", "maintenance", "monitoring", "backup", "disaster"]
            found_operational = sum(1 for factor in operational_factors if factor in result_str)
            assert found_operational >= 1, "Should consider operational factors"
        
        logger.info("Environmental Analysis constraint identification test passed")

    @pytest.mark.asyncio
    async def test_environmental_analysis_performance_considerations(self, environmental_analysis_agent, sample_task_analyses):
        """Test environmental performance analysis."""
        task_analysis = sample_task_analyses["web_app_analysis"]
        operation_id = f"test_performance_{datetime.now().isoformat()}"
        
        logger.info("Testing Environmental Analysis performance considerations")
        
        # Modify task analysis to emphasize performance requirements
        enhanced_analysis = task_analysis.copy()
        enhanced_analysis["constraints"]["performance"].extend([
            "Support 50,000 concurrent users",
            "Sub-100ms API response times",
            "99.9% uptime requirement"
        ])
        
        analysis_input = f"Task Analysis: {json.dumps(enhanced_analysis, indent=2)}"
        
        result = await environmental_analysis_agent._process(analysis_input)
        
        if "error" not in result:
            result_str = json.dumps(result).lower()
            
            # Should identify performance-related environmental factors
            performance_factors = ["latency", "throughput", "scalability", "optimization", "cache", "cdn"]
            found_performance = sum(1 for factor in performance_factors if factor in result_str)
            assert found_performance >= 2, f"Should identify performance factors, found {found_performance}"
            
            # Should consider infrastructure scaling
            scaling_factors = ["load", "balance", "cluster", "horizontal", "vertical"]
            found_scaling = sum(1 for factor in scaling_factors if factor in result_str)
            assert found_scaling >= 1, "Should consider scaling factors"
        
        logger.info("Environmental Analysis performance considerations test passed")

    @pytest.mark.asyncio
    async def test_environmental_analysis_security_assessment(self, environmental_analysis_agent, sample_task_analyses):
        """Test environmental security assessment."""
        task_analysis = sample_task_analyses["e_commerce_analysis"]
        operation_id = f"test_security_{datetime.now().isoformat()}"
        
        logger.info("Testing Environmental Analysis security assessment")
        
        analysis_input = f"Task Analysis: {json.dumps(task_analysis, indent=2)}"
        
        result = await environmental_analysis_agent._process(analysis_input)
        
        if "error" not in result:
            result_str = json.dumps(result).lower()
            
            # Should identify security environmental factors
            security_factors = ["authentication", "authorization", "encryption", "ssl", "firewall", "vulnerability"]
            found_security = sum(1 for factor in security_factors if factor in result_str)
            assert found_security >= 2, f"Should identify security factors, found {found_security}"
            
            # Should consider compliance requirements
            compliance_factors = ["gdpr", "pci", "compliance", "regulation", "audit", "privacy"]
            found_compliance = sum(1 for factor in compliance_factors if factor in result_str)
            assert found_compliance >= 1, "Should consider compliance factors"
        
        logger.info("Environmental Analysis security assessment test passed")

    @pytest.mark.asyncio
    async def test_environmental_analysis_state_transitions(self, environmental_analysis_agent, sample_task_analyses):
        """Test Environmental Analysis Agent state transitions."""
        task_analysis = sample_task_analyses["web_app_analysis"]
        operation_id = f"test_states_{datetime.now().isoformat()}"
        
        logger.info("Testing Environmental Analysis state transitions")
        
        # Check initial state
        initial_state = environmental_analysis_agent.development_state
        assert initial_state == DevelopmentState.INITIALIZING
        
        analysis_input = f"Task Analysis: {json.dumps(task_analysis, indent=2)}"
        
        # Process and monitor state changes
        result = await environmental_analysis_agent._process(analysis_input)
        
        # Should transition to appropriate final state
        final_state = environmental_analysis_agent.development_state
        assert final_state in [
            DevelopmentState.COMPLETE,
            DevelopmentState.ANALYZING,
            DevelopmentState.ERROR
        ], f"Should be in valid final state, got {final_state}"
        
        logger.info("Environmental Analysis state transitions test passed")

    @pytest.mark.asyncio
    async def test_environmental_analysis_error_handling(self, environmental_analysis_agent):
        """Test Environmental Analysis Agent error handling."""
        operation_id = f"test_error_{datetime.now().isoformat()}"
        
        logger.info("Testing Environmental Analysis error handling")
        
        # Test with malformed input
        malformed_input = "Invalid JSON: {broken"
        
        result = await environmental_analysis_agent._process(malformed_input)
        
        # Should handle gracefully
        assert isinstance(result, dict), "Should return dictionary even for malformed input"
        
        # Should either process successfully or return proper error
        if "error" in result:
            assert isinstance(result["error"], str), "Error should be a string"
            logger.info(f"Error properly handled: {result['error']}")
        else:
            # If processed, should contain some analysis
            assert len(str(result)) > 10, "Should provide some analysis even for malformed input"
        
        logger.info("Environmental Analysis error handling test passed")

    @pytest.mark.asyncio
    async def test_environmental_analysis_comprehensive_coverage(self, environmental_analysis_agent, sample_task_analyses):
        """Test comprehensive environmental analysis coverage."""
        task_analysis = sample_task_analyses["e_commerce_analysis"]
        operation_id = f"test_comprehensive_{datetime.now().isoformat()}"
        
        logger.info("Testing Environmental Analysis comprehensive coverage")
        
        analysis_input = f"Task Analysis: {json.dumps(task_analysis, indent=2)}"
        
        result = await environmental_analysis_agent.process_with_validation(
            conversation=analysis_input,
            system_prompt_info=("FFTT_system_prompts/phase_one/garden_environmental_analysis_agent", "initial_core_requirements_prompt"),
            operation_id=operation_id
        )
        
        if "error" not in result:
            result_str = json.dumps(result).lower()
            
            # Should cover multiple environmental dimensions
            dimensions = {
                "technical": ["architecture", "technology", "infrastructure", "platform"],
                "operational": ["deployment", "monitoring", "maintenance", "support"],
                "business": ["cost", "timeline", "resource", "budget"],
                "user": ["experience", "usability", "accessibility", "interface"],
                "security": ["security", "privacy", "compliance", "protection"],
                "performance": ["performance", "scalability", "availability", "reliability"]
            }
            
            covered_dimensions = 0
            for dimension, keywords in dimensions.items():
                if any(keyword in result_str for keyword in keywords):
                    covered_dimensions += 1
            
            assert covered_dimensions >= 4, f"Should cover multiple environmental dimensions, covered {covered_dimensions}/6"
        
        logger.info("Environmental Analysis comprehensive coverage test passed")

    @pytest.mark.asyncio
    async def test_environmental_analysis_integration_readiness(self, environmental_analysis_agent, sample_task_analyses):
        """Test Environmental Analysis integration readiness for workflow."""
        task_analysis = sample_task_analyses["web_app_analysis"]
        operation_id = f"test_integration_{datetime.now().isoformat()}"
        
        logger.info("Testing Environmental Analysis integration readiness")
        
        analysis_input = f"Task Analysis: {json.dumps(task_analysis, indent=2)}"
        
        # Test the process method as it would be called in workflow
        result = await environmental_analysis_agent._process(analysis_input)
        
        # Verify integration readiness
        assert isinstance(result, dict), "Should return dictionary for workflow integration"
        
        # Should be serializable for state management
        try:
            json.dumps(result)
            logger.info("Result is JSON serializable")
        except (TypeError, ValueError) as e:
            pytest.fail(f"Result is not JSON serializable: {e}")
        
        # Should handle the expected input format from Garden Planner
        assert len(str(result)) > 50, "Should provide substantial analysis for next agent"
        
        logger.info("Environmental Analysis integration readiness test passed")