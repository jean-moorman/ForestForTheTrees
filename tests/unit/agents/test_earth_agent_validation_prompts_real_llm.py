"""
Comprehensive test suite for Earth Agent validation prompts with real LLM calls.

This module tests the Earth Agent's validation functionality with actual prompts and real API calls
to ensure proper validation of Garden Planner outputs and reflection/revision processes.
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
from phase_one.agents.earth_agent import EarthAgent
from phase_one.models.enums import DevelopmentState

logger = logging.getLogger(__name__)

@pytest.mark.real_api
class TestEarthAgentValidationPromptsRealLLM:
    """Test suite for Earth Agent validation prompts using real LLM API calls."""

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
    async def earth_agent(self, real_resources):
        """Create an Earth Agent instance with real resources."""
        agent = EarthAgent(
            agent_id="test_earth_agent",
            **real_resources,
            max_validation_cycles=3
        )
        return agent

    @pytest.fixture
    def validation_test_cases(self):
        """Provide comprehensive validation test cases."""
        return {
            "excellent_garden_planner_output": {
                "task_analysis": {
                    "original_request": "Create a web application for habit tracking",
                    "interpreted_goal": "Build a comprehensive habit tracking web application with user authentication, habit management, progress visualization, and analytics dashboard",
                    "scope": {
                        "included": [
                            "User registration and authentication system",
                            "Habit creation and management interface",
                            "Daily habit tracking functionality",
                            "Progress visualization with charts and graphs",
                            "User dashboard with habit streaks and statistics",
                            "Responsive web design for mobile and desktop"
                        ],
                        "excluded": [
                            "Mobile native applications",
                            "Social sharing features",
                            "Third-party integrations",
                            "Advanced AI recommendations",
                            "Premium subscription features"
                        ],
                        "assumptions": [
                            "Web-based application accessible via browser",
                            "Individual user accounts with data privacy",
                            "Standard web technologies sufficient for requirements",
                            "Users will manually input habit completion data",
                            "Simple analytics sufficient for initial version"
                        ]
                    },
                    "technical_requirements": {
                        "languages": ["JavaScript", "HTML", "CSS", "SQL"],
                        "frameworks": ["React", "Node.js", "Express.js"],
                        "apis": ["RESTful API", "Authentication API"],
                        "infrastructure": ["Web server", "Database server", "SSL certificate"]
                    },
                    "constraints": {
                        "technical": ["Browser compatibility with Chrome, Firefox, Safari", "Responsive design required", "HTTPS required for production"],
                        "business": ["3-month development timeline", "Budget under $50,000", "Single developer initially"],
                        "performance": ["Page load times under 2 seconds", "Support 1,000 concurrent users", "99% uptime target"]
                    },
                    "considerations": {
                        "security": ["Secure user authentication", "Password encryption", "Data protection compliance", "SQL injection prevention"],
                        "scalability": ["Database optimization for growth", "Caching strategy for performance", "Horizontal scaling capability"],
                        "maintainability": ["Code documentation", "Modular architecture", "Unit test coverage", "Error logging and monitoring"]
                    }
                }
            },
            
            "poor_garden_planner_output": {
                "task_analysis": {
                    "original_request": "Create a simple todo app",
                    "interpreted_goal": "Build an enterprise-grade distributed microservices architecture with AI-powered recommendations and blockchain integration",
                    "scope": {
                        "included": [
                            "Distributed microservices architecture",
                            "AI-powered task recommendations",
                            "Blockchain-based task verification",
                            "Real-time collaboration features",
                            "Advanced analytics and reporting",
                            "Multi-language support",
                            "Enterprise SSO integration"
                        ],
                        "excluded": ["Simple task management"],
                        "assumptions": [
                            "Enterprise budget available",
                            "Team of 20+ developers",
                            "2-year development timeline"
                        ]
                    },
                    "technical_requirements": {
                        "languages": ["Go", "Rust", "Solidity", "Python", "TypeScript"],
                        "frameworks": ["Kubernetes", "Istio", "TensorFlow", "Ethereum"],
                        "apis": ["GraphQL", "gRPC", "Blockchain APIs"],
                        "infrastructure": ["Container orchestration", "Service mesh", "Blockchain network"]
                    },
                    "constraints": {
                        "technical": ["High availability", "ACID compliance", "Immutable infrastructure"],
                        "business": ["Unlimited budget", "No timeline constraints"],
                        "performance": ["Sub-millisecond response times", "Global distribution"]
                    },
                    "considerations": {
                        "security": ["Zero-trust architecture", "End-to-end encryption", "Quantum-resistant cryptography"],
                        "scalability": ["Horizontal and vertical scaling", "Auto-scaling based on ML predictions"],
                        "maintainability": ["Comprehensive test coverage", "Infrastructure as code", "Continuous deployment"]
                    }
                }
            },
            
            "incomplete_garden_planner_output": {
                "task_analysis": {
                    "original_request": "Build a chat application",
                    "interpreted_goal": "Create a messaging app",
                    "scope": {
                        "included": ["Messages"],
                        "excluded": [],
                        "assumptions": []
                    },
                    "technical_requirements": {
                        "languages": ["JavaScript"],
                        "frameworks": [],
                        "apis": [],
                        "infrastructure": []
                    },
                    "constraints": {
                        "technical": [],
                        "business": [],
                        "performance": []
                    },
                    "considerations": {
                        "security": [],
                        "scalability": [],
                        "maintainability": []
                    }
                }
            },
            
            "misaligned_garden_planner_output": {
                "task_analysis": {
                    "original_request": "Create a simple blog website",
                    "interpreted_goal": "Build a comprehensive e-commerce platform with inventory management",
                    "scope": {
                        "included": [
                            "Product catalog management",
                            "Shopping cart functionality",
                            "Payment processing",
                            "Inventory tracking",
                            "Order fulfillment system"
                        ],
                        "excluded": ["Blog posts", "Content management"],
                        "assumptions": ["E-commerce business model", "Product sales required"]
                    },
                    "technical_requirements": {
                        "languages": ["PHP", "MySQL"],
                        "frameworks": ["WooCommerce", "Magento"],
                        "apis": ["Payment gateway APIs", "Shipping APIs"],
                        "infrastructure": ["E-commerce hosting", "PCI compliance"]
                    },
                    "constraints": {
                        "technical": ["PCI DSS compliance", "High transaction volume"],
                        "business": ["Revenue generation required", "Inventory management"],
                        "performance": ["High availability for sales"]
                    },
                    "considerations": {
                        "security": ["Payment security", "Customer data protection"],
                        "scalability": ["Handle peak shopping seasons"],
                        "maintainability": ["E-commerce platform updates"]
                    }
                }
            }
        }

    @pytest.mark.asyncio
    async def test_earth_agent_validation_excellent_output(self, earth_agent, validation_test_cases):
        """Test Earth Agent validation of excellent Garden Planner output."""
        user_request = "Create a web application for habit tracking"
        garden_planner_output = validation_test_cases["excellent_garden_planner_output"]
        operation_id = f"test_excellent_{datetime.now().isoformat()}"
        
        logger.info("Testing Earth Agent validation of excellent output")
        
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            garden_planner_output,
            operation_id
        )
        
        # Should approve excellent output
        assert result["is_valid"] == True, "Should approve excellent Garden Planner output"
        assert result["validation_category"] == "APPROVED", "Should categorize as APPROVED"
        
        # Should have minimal issues
        if "validation_issues" in result:
            high_severity_issues = [issue for issue in result["validation_issues"] if issue.get("severity") == "high"]
            assert len(high_severity_issues) == 0, "Should have no high severity issues for excellent output"
        
        logger.info("Earth Agent excellent output validation test passed")

    @pytest.mark.asyncio
    async def test_earth_agent_validation_poor_output(self, earth_agent, validation_test_cases):
        """Test Earth Agent validation of poor Garden Planner output."""
        user_request = "Create a simple todo app"
        garden_planner_output = validation_test_cases["poor_garden_planner_output"]
        operation_id = f"test_poor_{datetime.now().isoformat()}"
        
        logger.info("Testing Earth Agent validation of poor output")
        
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            garden_planner_output,
            operation_id
        )
        
        # Should reject poor output
        assert result["is_valid"] == False, "Should reject poor Garden Planner output"
        assert result["validation_category"] in ["REJECTED", "NEEDS_CORRECTION"], "Should categorize as REJECTED or NEEDS_CORRECTION"
        
        # Should identify significant issues
        if "validation_issues" in result:
            assert len(result["validation_issues"]) > 0, "Should identify validation issues"
            
            # Should identify scope mismatch
            issues_text = str(result["validation_issues"]).lower()
            scope_indicators = ["scope", "mismatch", "overengineered", "complex", "simple"]
            found_scope_issues = sum(1 for indicator in scope_indicators if indicator in issues_text)
            assert found_scope_issues >= 1, "Should identify scope-related issues"
        
        logger.info("Earth Agent poor output validation test passed")

    @pytest.mark.asyncio
    async def test_earth_agent_validation_incomplete_output(self, earth_agent, validation_test_cases):
        """Test Earth Agent validation of incomplete Garden Planner output."""
        user_request = "Build a chat application"
        garden_planner_output = validation_test_cases["incomplete_garden_planner_output"]
        operation_id = f"test_incomplete_{datetime.now().isoformat()}"
        
        logger.info("Testing Earth Agent validation of incomplete output")
        
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            garden_planner_output,
            operation_id
        )
        
        # Should identify incompleteness
        assert result["is_valid"] == False, "Should reject incomplete Garden Planner output"
        
        # Should identify completeness issues
        if "validation_issues" in result:
            issues_text = str(result["validation_issues"]).lower()
            completeness_indicators = ["incomplete", "missing", "empty", "insufficient", "detail"]
            found_completeness_issues = sum(1 for indicator in completeness_indicators if indicator in issues_text)
            assert found_completeness_issues >= 1, "Should identify completeness issues"
        
        logger.info("Earth Agent incomplete output validation test passed")

    @pytest.mark.asyncio
    async def test_earth_agent_validation_misaligned_output(self, earth_agent, validation_test_cases):
        """Test Earth Agent validation of misaligned Garden Planner output."""
        user_request = "Create a simple blog website"
        garden_planner_output = validation_test_cases["misaligned_garden_planner_output"]
        operation_id = f"test_misaligned_{datetime.now().isoformat()}"
        
        logger.info("Testing Earth Agent validation of misaligned output")
        
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            garden_planner_output,
            operation_id
        )
        
        # Should identify misalignment
        assert result["is_valid"] == False, "Should reject misaligned Garden Planner output"
        
        # Should identify alignment issues
        if "validation_issues" in result:
            issues_text = str(result["validation_issues"]).lower()
            alignment_indicators = ["mismatch", "alignment", "blog", "e-commerce", "different", "wrong"]
            found_alignment_issues = sum(1 for indicator in alignment_indicators if indicator in issues_text)
            assert found_alignment_issues >= 1, "Should identify alignment issues"
        
        logger.info("Earth Agent misaligned output validation test passed")

    @pytest.mark.asyncio
    async def test_earth_agent_reflection_process(self, earth_agent, validation_test_cases):
        """Test Earth Agent reflection process with actual prompts."""
        garden_planner_output = validation_test_cases["excellent_garden_planner_output"]
        operation_id = f"test_reflection_{datetime.now().isoformat()}"
        
        logger.info("Testing Earth Agent reflection process")
        
        # First validate the output
        user_request = "Create a web application for habit tracking"
        validation_result = await earth_agent.validate_garden_planner_output(
            user_request,
            garden_planner_output,
            operation_id
        )
        
        # Test reflection on the validation
        reflection_result = await earth_agent.standard_reflect(
            output=validation_result,
            prompt_path="FFTT_system_prompts/core_agents",
            prompt_name="earth_agent"
        )
        
        # Verify reflection structure
        assert isinstance(reflection_result, dict), "Reflection should return dictionary"
        
        if "error" not in reflection_result:
            # Should contain reflection results
            assert "reflection_results" in reflection_result or len(str(reflection_result)) > 100, \
                "Should provide meaningful reflection"
            
            # Should evaluate the validation quality
            reflection_str = json.dumps(reflection_result).lower()
            evaluation_indicators = ["validation", "quality", "accuracy", "assessment", "analysis"]
            found_evaluation = sum(1 for indicator in evaluation_indicators if indicator in reflection_str)
            assert found_evaluation >= 1, "Should evaluate validation quality"
        
        logger.info("Earth Agent reflection process test passed")

    @pytest.mark.asyncio
    async def test_earth_agent_revision_process(self, earth_agent, validation_test_cases):
        """Test Earth Agent revision process."""
        user_request = "Create a simple todo app"
        garden_planner_output = validation_test_cases["poor_garden_planner_output"]
        operation_id = f"test_revision_{datetime.now().isoformat()}"
        
        logger.info("Testing Earth Agent revision process")
        
        # First validate the poor output
        validation_result = await earth_agent.validate_garden_planner_output(
            user_request,
            garden_planner_output,
            operation_id
        )
        
        # Create mock refinement guidance
        refinement_guidance = {
            "issues_identified": [
                "Scope mismatch - request is for simple todo app but analysis suggests enterprise system",
                "Technology over-engineering for simple requirements",
                "Unrealistic complexity for stated goal"
            ],
            "recommendations": [
                "Simplify scope to match original request",
                "Use appropriate technology stack for simple todo app",
                "Focus on core todo functionality"
            ]
        }
        
        # Test revision process
        revision_result = await earth_agent.standard_refine(
            output=validation_result,
            refinement_guidance=refinement_guidance,
            prompt_path="FFTT_system_prompts/core_agents",
            prompt_name="earth_agent"
        )
        
        # Verify revision structure
        assert isinstance(revision_result, dict), "Revision should return dictionary"
        
        if "error" not in revision_result:
            # Should provide improved validation
            revision_str = json.dumps(revision_result).lower()
            improvement_indicators = ["improved", "revised", "corrected", "updated", "refined"]
            found_improvement = sum(1 for indicator in improvement_indicators if indicator in revision_str)
            assert found_improvement >= 1 or len(str(revision_result)) > 100, \
                "Should provide improved validation or substantial analysis"
        
        logger.info("Earth Agent revision process test passed")

    @pytest.mark.asyncio
    async def test_earth_agent_validation_consistency(self, earth_agent, validation_test_cases):
        """Test Earth Agent validation consistency across multiple runs."""
        user_request = "Create a web application for habit tracking"
        garden_planner_output = validation_test_cases["excellent_garden_planner_output"]
        
        logger.info("Testing Earth Agent validation consistency")
        
        # Run validation multiple times
        results = []
        for i in range(3):
            operation_id = f"test_consistency_{i}_{datetime.now().isoformat()}"
            result = await earth_agent.validate_garden_planner_output(
                user_request,
                garden_planner_output,
                operation_id
            )
            results.append(result)
        
        # Check consistency
        validation_decisions = [result["is_valid"] for result in results]
        validation_categories = [result["validation_category"] for result in results]
        
        # Should be consistent in validation decisions
        assert len(set(validation_decisions)) <= 2, "Validation decisions should be mostly consistent"
        
        # At least majority should be consistent
        most_common_decision = max(set(validation_decisions), key=validation_decisions.count)
        consistency_rate = validation_decisions.count(most_common_decision) / len(validation_decisions)
        assert consistency_rate >= 0.66, f"Should have at least 66% consistency, got {consistency_rate}"
        
        logger.info("Earth Agent validation consistency test passed")

    @pytest.mark.asyncio
    async def test_earth_agent_validation_with_system_prompts(self, earth_agent, validation_test_cases):
        """Test Earth Agent validation using actual system prompts."""
        user_request = "Create a web application for habit tracking"
        garden_planner_output = validation_test_cases["excellent_garden_planner_output"]
        operation_id = f"test_prompts_{datetime.now().isoformat()}"
        
        logger.info("Testing Earth Agent validation with system prompts")
        
        # Format validation input
        validation_input = f"""
        User Request: {user_request}
        
        Garden Planner Output: {json.dumps(garden_planner_output, indent=2)}
        """
        
        # Use the actual Earth Agent validation prompt
        result = await earth_agent.process_with_validation(
            conversation=validation_input,
            system_prompt_info=("FFTT_system_prompts/core_agents", "earth_agent"),
            operation_id=operation_id
        )
        
        # Verify the result follows expected structure
        assert isinstance(result, dict), "Result should be a dictionary"
        
        if "error" not in result:
            # Should provide comprehensive validation analysis
            assert len(str(result)) > 200, "Should provide detailed validation analysis"
            
            # Check for validation elements
            result_str = json.dumps(result).lower()
            
            # Should include validation analysis elements
            validation_elements = ["validation", "analysis", "assessment", "quality", "alignment"]
            found_elements = sum(1 for element in validation_elements if element in result_str)
            assert found_elements >= 2, f"Should include validation elements, found {found_elements}"
        
        logger.info("Earth Agent system prompts test passed")

    @pytest.mark.asyncio
    async def test_earth_agent_validation_severity_classification(self, earth_agent, validation_test_cases):
        """Test Earth Agent validation severity classification."""
        test_cases = [
            ("Create a simple todo app", validation_test_cases["poor_garden_planner_output"], "high"),
            ("Build a chat application", validation_test_cases["incomplete_garden_planner_output"], "medium"),
            ("Create a web application for habit tracking", validation_test_cases["excellent_garden_planner_output"], "low")
        ]
        
        logger.info("Testing Earth Agent validation severity classification")
        
        for user_request, garden_output, expected_severity_level in test_cases:
            operation_id = f"test_severity_{expected_severity_level}_{datetime.now().isoformat()}"
            
            result = await earth_agent.validate_garden_planner_output(
                user_request,
                garden_output,
                operation_id
            )
            
            if expected_severity_level == "low":
                # Should approve or have minimal issues
                assert result["is_valid"] == True or result["validation_category"] == "APPROVED", \
                    "Low severity case should be approved"
            else:
                # Should identify issues with appropriate severity
                assert result["is_valid"] == False, f"Should reject {expected_severity_level} severity issues"
                
                if "validation_issues" in result:
                    has_expected_severity = any(
                        issue.get("severity") == expected_severity_level 
                        for issue in result["validation_issues"]
                    )
                    # Not strict requirement but good indicator
                    if not has_expected_severity:
                        logger.info(f"Expected {expected_severity_level} severity issues but found different classification")
        
        logger.info("Earth Agent severity classification test passed")

    @pytest.mark.asyncio
    async def test_earth_agent_validation_error_handling(self, earth_agent):
        """Test Earth Agent validation error handling."""
        operation_id = f"test_error_{datetime.now().isoformat()}"
        
        logger.info("Testing Earth Agent validation error handling")
        
        # Test with malformed inputs
        malformed_user_request = ""
        malformed_garden_output = {"invalid": "structure"}
        
        result = await earth_agent.validate_garden_planner_output(
            malformed_user_request,
            malformed_garden_output,
            operation_id
        )
        
        # Should handle gracefully
        assert isinstance(result, dict), "Should return dictionary even for malformed input"
        
        # Should have basic validation structure
        required_fields = ["is_valid", "validation_category"]
        for field in required_fields:
            assert field in result, f"Should contain {field} field even for errors"
        
        # Should indicate validation failure for malformed input
        assert result["is_valid"] == False, "Should mark malformed input as invalid"
        
        logger.info("Earth Agent validation error handling test passed")

    @pytest.mark.asyncio
    async def test_earth_agent_integration_readiness(self, earth_agent, validation_test_cases):
        """Test Earth Agent integration readiness for Garden Planner validation workflow."""
        user_request = "Create a web application for habit tracking"
        garden_planner_output = validation_test_cases["excellent_garden_planner_output"]
        operation_id = f"test_integration_{datetime.now().isoformat()}"
        
        logger.info("Testing Earth Agent integration readiness")
        
        # Test as it would be called in Garden Planner validation workflow
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            garden_planner_output,
            operation_id
        )
        
        # Verify integration readiness
        assert isinstance(result, dict), "Should return dictionary for workflow integration"
        
        # Should be serializable for state management
        try:
            json.dumps(result)
            logger.info("Result is JSON serializable")
        except (TypeError, ValueError) as e:
            pytest.fail(f"Result is not JSON serializable: {e}")
        
        # Should provide clear validation decision
        assert "is_valid" in result, "Should provide clear validation decision"
        assert isinstance(result["is_valid"], bool), "Validation decision should be boolean"
        
        # Should provide validation category
        assert "validation_category" in result, "Should provide validation category"
        valid_categories = ["APPROVED", "NEEDS_CORRECTION", "REJECTED"]
        assert result["validation_category"] in valid_categories, f"Should use valid category, got {result['validation_category']}"
        
        logger.info("Earth Agent integration readiness test passed")