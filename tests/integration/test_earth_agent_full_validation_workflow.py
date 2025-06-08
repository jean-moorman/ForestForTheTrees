"""
Comprehensive integration tests for Earth Agent full validation workflow.

This module tests the complete Earth Agent validation workflow including
integration with Garden Planner, real validation scenarios, and end-to-end
validation cycles with reflection and revision.
"""

import asyncio
import json
import pytest
import pytest_asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from resources import (
    EventQueue, StateManager, AgentContextManager, CacheManager, 
    MetricsManager, ErrorHandler, MemoryMonitor
)
from resources.monitoring import HealthTracker
from phase_one.agents.earth_agent import EarthAgent
from phase_one.agents.garden_planner import GardenPlannerAgent
from phase_one.validation.garden_planner_validator import GardenPlannerValidator
from phase_one.models.enums import DevelopmentState

logger = logging.getLogger(__name__)

class TestEarthAgentFullValidationWorkflow:
    """Integration tests for complete Earth Agent validation workflow."""

    @pytest_asyncio.fixture
    async def real_resources(self):
        """Create real resource managers for testing."""
        event_queue = EventQueue()
        await event_queue.start()
        
        state_manager = StateManager(event_queue)
        context_manager = AgentContextManager(event_queue)
        cache_manager = CacheManager(event_queue)
        metrics_manager = MetricsManager(event_queue)
        error_handler = ErrorHandler(event_queue)
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
        
        await event_queue.stop()

    @pytest_asyncio.fixture
    async def earth_agent(self, real_resources):
        """Create Earth Agent with real resources."""
        return EarthAgent(
            agent_id="integration_test_earth_agent",
            **real_resources,
            max_validation_cycles=3
        )

    @pytest_asyncio.fixture
    async def garden_planner_agent(self, real_resources):
        """Create Garden Planner Agent with real resources."""
        return GardenPlannerAgent(
            agent_id="integration_test_garden_planner",
            **real_resources
        )

    @pytest_asyncio.fixture
    async def garden_planner_validator(self, garden_planner_agent, earth_agent, real_resources):
        """Create Garden Planner Validator with real agents."""
        return GardenPlannerValidator(
            garden_planner_agent=garden_planner_agent,
            earth_agent=earth_agent,
            event_queue=real_resources['event_queue'],
            state_manager=real_resources['state_manager'],
            max_refinement_cycles=2,  # Limit for faster testing
            validation_timeout=300.0  # 5 minutes timeout
        )

    # Test Complete End-to-End Validation Scenarios

    @pytest.mark.asyncio
    async def test_complete_validation_workflow_simple_request(self, earth_agent):
        """Test complete validation workflow with a simple, clear user request."""
        user_request = """
        Create a personal blog website where users can:
        - Write and publish blog posts
        - Add comments to posts
        - Categorize posts with tags
        - Search through posts
        - Have a simple admin interface for managing content
        
        The website should be built with Python and be deployed on a standard web hosting service.
        """
        
        # Simulate a well-structured Garden Planner output for this request
        garden_planner_output = {
            "task_analysis": {
                "original_request": user_request.strip(),
                "interpreted_goal": "Build a personal blog website with content management, commenting, categorization, search functionality, and admin interface using Python for standard web hosting deployment",
                "scope": {
                    "included": [
                        "Blog post creation and editing interface",
                        "Blog post publishing and display system",
                        "Comment system for reader engagement",
                        "Tag-based categorization system",
                        "Search functionality across posts and tags",
                        "Admin interface for content management",
                        "User authentication for admin access",
                        "Responsive design for mobile and desktop"
                    ],
                    "excluded": [
                        "Multi-user blogging platform features",
                        "Advanced analytics and metrics",
                        "Email newsletter integration",
                        "Social media integration",
                        "E-commerce or monetization features",
                        "Advanced SEO optimization tools"
                    ],
                    "assumptions": [
                        "Single-author blog (personal use)",
                        "Standard web hosting with Python support",
                        "Modern web browsers for admin interface",
                        "Basic technical maintenance capability",
                        "Content will be primarily text with some images"
                    ]
                },
                "technical_requirements": {
                    "languages": ["Python", "HTML", "CSS", "JavaScript"],
                    "frameworks": ["Django", "Bootstrap"],
                    "apis": ["Django REST API for admin functions"],
                    "infrastructure": ["Standard web hosting with Python support", "SQLite or PostgreSQL", "Static file serving"]
                },
                "constraints": {
                    "technical": [
                        "Compatible with standard shared hosting",
                        "Minimal server resource requirements",
                        "Standard Python web hosting compatibility"
                    ],
                    "business": [
                        "Cost-effective hosting solution",
                        "Easy maintenance and updates",
                        "Quick deployment and setup"
                    ],
                    "performance": [
                        "Fast page load times for blog readers",
                        "Efficient search functionality",
                        "Responsive admin interface"
                    ]
                },
                "considerations": {
                    "security": [
                        "Secure admin authentication",
                        "Input validation for comments and posts",
                        "Protection against spam comments",
                        "Basic XSS and CSRF protection"
                    ],
                    "scalability": [
                        "Database optimization for growing content",
                        "Efficient handling of increased readership",
                        "Content caching for performance"
                    ],
                    "maintainability": [
                        "Clear code organization and documentation",
                        "Simple backup and restore procedures",
                        "Easy content migration capabilities",
                        "Straightforward updates and maintenance"
                    ]
                }
            }
        }
        
        # Perform validation
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            garden_planner_output,
            "integration_test_simple_blog"
        )
        
        # Verify validation completed successfully
        assert "error" not in result, f"Validation should complete without errors, got: {result.get('error', 'None')}"
        assert "validation_result" in result, "Should have validation result"
        
        validation_category = result["validation_result"]["validation_category"]
        assert validation_category in ["APPROVED", "CORRECTED"], \
            f"Well-structured blog request should be approved or corrected, got: {validation_category}"
        
        # Verify Earth Agent state is appropriate
        assert earth_agent.development_state in [DevelopmentState.COMPLETE], \
            f"Earth Agent should be in COMPLETE state, got: {earth_agent.development_state}"

    @pytest.mark.asyncio
    async def test_complete_validation_workflow_complex_request(self, earth_agent):
        """Test complete validation workflow with a complex, detailed user request."""
        user_request = """
        Create a comprehensive project management system for a software development team that includes:
        
        1. Project Planning:
           - Epic and story management
           - Sprint planning and management
           - Task breakdown and assignment
           - Timeline and milestone tracking
        
        2. Team Collaboration:
           - Team member profiles and roles
           - Real-time commenting and discussions
           - File sharing and version control integration
           - Notification system for updates
        
        3. Progress Tracking:
           - Kanban boards with customizable workflows
           - Burndown charts and velocity tracking
           - Time tracking and reporting
           - Custom dashboard with key metrics
        
        4. Integration Requirements:
           - Git repository integration
           - Slack/Teams notifications
           - Calendar synchronization
           - API for third-party integrations
        
        The system should support teams of 10-50 people, be scalable, secure, and have excellent performance.
        It should be built with modern web technologies and be cloud-deployable.
        """
        
        # Simulate Garden Planner output for this complex request
        garden_planner_output = {
            "task_analysis": {
                "original_request": user_request.strip(),
                "interpreted_goal": "Develop a comprehensive project management platform specifically designed for software development teams (10-50 people) with advanced planning, collaboration, tracking, and integration capabilities, built with modern web technologies for cloud deployment",
                "scope": {
                    "included": [
                        "Epic and user story management system",
                        "Sprint planning and management interface",
                        "Task breakdown structure and assignment workflow",
                        "Timeline visualization and milestone tracking",
                        "Team member profile and role management",
                        "Real-time commenting and discussion threads",
                        "File sharing with version control integration",
                        "Comprehensive notification system",
                        "Customizable Kanban boards with workflow states",
                        "Burndown charts and velocity metrics",
                        "Time tracking with detailed reporting",
                        "Custom dashboard with configurable widgets",
                        "Git repository integration and commit tracking",
                        "Slack/Teams notification integration",
                        "Calendar synchronization for deadlines",
                        "REST API for third-party integrations"
                    ],
                    "excluded": [
                        "Financial management and budgeting tools",
                        "HR management features",
                        "Client billing and invoicing",
                        "Advanced business intelligence tools",
                        "Mobile native applications (initial version)",
                        "Video conferencing integration"
                    ],
                    "assumptions": [
                        "Software development team workflow focus",
                        "Agile/Scrum methodology primary use case",
                        "Cloud infrastructure deployment",
                        "Modern browser support (last 2 versions)",
                        "Team size range of 10-50 active users",
                        "English language interface initially",
                        "Standard development tools integration (Git, Slack, etc.)"
                    ]
                },
                "technical_requirements": {
                    "languages": ["Python", "TypeScript", "JavaScript", "HTML5", "CSS3", "SQL"],
                    "frameworks": ["Django", "Django REST Framework", "React", "Redux Toolkit", "WebSocket", "Celery"],
                    "apis": ["REST API", "WebSocket API", "Git API", "Slack API", "Calendar API", "OAuth 2.0"],
                    "infrastructure": ["AWS/GCP/Azure", "PostgreSQL", "Redis", "Docker", "Kubernetes", "CDN", "Load Balancer"]
                },
                "constraints": {
                    "technical": [
                        "Support for 10-50 concurrent users per team",
                        "Real-time updates with WebSocket connections",
                        "Cross-browser compatibility (Chrome, Firefox, Safari, Edge)",
                        "Mobile-responsive design for tablet access",
                        "API rate limiting and security measures"
                    ],
                    "business": [
                        "18-month development timeline with quarterly releases",
                        "Development team of 4-6 full-stack developers",
                        "Budget for cloud infrastructure and third-party APIs",
                        "Phased rollout starting with core features",
                        "Compliance with data protection regulations"
                    ],
                    "performance": [
                        "Page load times under 1 second for dashboard",
                        "API response times under 100ms for most operations",
                        "Real-time updates delivered within 50ms",
                        "Database queries optimized for <25ms response",
                        "99.9% uptime SLA target"
                    ]
                },
                "considerations": {
                    "security": [
                        "OAuth 2.0 authentication with role-based access control",
                        "HTTPS encryption for all communications",
                        "Input validation and sanitization across all interfaces",
                        "API security with rate limiting and authentication",
                        "Data encryption at rest for sensitive information",
                        "Regular security audits and vulnerability assessments",
                        "Secure integration with third-party services"
                    ],
                    "scalability": [
                        "Microservices architecture for independent scaling",
                        "Database sharding strategy for large datasets",
                        "Redis caching for frequently accessed data",
                        "CDN integration for static assets and file sharing",
                        "Auto-scaling policies for variable load",
                        "Queue-based processing for background tasks",
                        "Load balancing across multiple application instances"
                    ],
                    "maintainability": [
                        "Comprehensive unit and integration test coverage (>95%)",
                        "Detailed API documentation with interactive examples",
                        "Code quality enforcement with automated linting",
                        "Feature flag system for gradual rollouts",
                        "Automated CI/CD pipeline with testing gates",
                        "Structured logging and monitoring with alerts",
                        "Performance monitoring and optimization tracking",
                        "Regular dependency updates and security patches"
                    ]
                }
            }
        }
        
        # Perform validation
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            garden_planner_output,
            "integration_test_complex_project_mgmt"
        )
        
        # Verify validation completed successfully
        assert "error" not in result, f"Validation should complete without errors, got: {result.get('error', 'None')}"
        assert "validation_result" in result, "Should have validation result"
        
        validation_category = result["validation_result"]["validation_category"]
        assert validation_category in ["APPROVED", "CORRECTED"], \
            f"Well-structured complex request should be approved or corrected, got: {validation_category}"
        
        # Complex requests should have minimal high-severity issues
        issues = result.get("architectural_issues", [])
        critical_issues = [issue for issue in issues if issue.get("severity") == "CRITICAL"]
        assert len(critical_issues) == 0, f"Well-structured complex request should not have critical issues, found: {critical_issues}"

    @pytest.mark.asyncio
    async def test_validation_workflow_with_multiple_cycles(self, earth_agent):
        """Test validation workflow that requires multiple refinement cycles."""
        user_request = "Create a secure online banking application with transaction processing, account management, and regulatory compliance"
        
        # Simulate Garden Planner output with some issues that should trigger refinement
        problematic_output = {
            "task_analysis": {
                "original_request": user_request,
                "interpreted_goal": "Build a banking application with basic features",  # Too vague for banking
                "scope": {
                    "included": [
                        "Login system",
                        "Account viewing",
                        "Money transfers"
                    ],
                    "excluded": [
                        "Advanced security"  # Problematic exclusion for banking
                    ],
                    "assumptions": [
                        "Basic security is sufficient"  # Inappropriate for banking
                    ]
                },
                "technical_requirements": {
                    "languages": ["Python"],
                    "frameworks": ["Django"],
                    "apis": ["REST API"],
                    "infrastructure": ["Cloud hosting"]  # Too vague for banking
                },
                "constraints": {
                    "technical": ["Works on computers"],  # Too vague
                    "business": ["Quick to build"],  # Inappropriate for banking
                    "performance": ["Fast enough"]  # Unmeasurable
                },
                "considerations": {
                    "security": ["Password protection"],  # Insufficient for banking
                    "scalability": ["Can handle users"],  # Vague
                    "maintainability": ["Easy to update"]  # Vague
                }
            }
        }
        
        # Perform validation which should identify multiple issues
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            problematic_output,
            "integration_test_banking_refinement"
        )
        
        # Validation should complete
        assert "validation_result" in result, "Should have validation result"
        
        # Banking application with insufficient security should be rejected
        validation_category = result["validation_result"]["validation_category"]
        assert validation_category == "REJECTED", \
            f"Banking app with insufficient security should be rejected, got: {validation_category}"
        
        # Should identify critical security issues
        issues = result.get("architectural_issues", [])
        critical_issues = [issue for issue in issues if issue.get("severity") == "CRITICAL"]
        assert len(critical_issues) > 0, "Banking app with poor security should have critical issues"
        
        # Should identify security-related issue types
        issue_types = [issue.get("issue_type") for issue in issues]
        assert "insufficient_consideration" in issue_types or "requirement_gap" in issue_types, \
            "Should identify security insufficiencies"

    # Test Garden Planner Validator Integration

    @pytest.mark.asyncio
    async def test_garden_planner_validator_integration(self, garden_planner_validator):
        """Test integration with Garden Planner Validator for complete workflow."""
        user_request = """
        Create a simple task management application for personal use with:
        - Task creation and editing
        - Due date tracking
        - Task categorization
        - Basic search functionality
        - Simple web interface
        """
        
        # Create a moderate-quality Garden Planner output
        garden_planner_output = {
            "task_analysis": {
                "original_request": user_request.strip(),
                "interpreted_goal": "Build a personal task management web application",
                "scope": {
                    "included": [
                        "Task creation and editing interface",
                        "Due date assignment and tracking",
                        "Category-based task organization",
                        "Basic search across tasks",
                        "Web-based user interface"
                    ],
                    "excluded": [
                        "Multi-user collaboration",
                        "Advanced reporting",
                        "Mobile applications"
                    ],
                    "assumptions": [
                        "Personal use by single user",
                        "Web browser access",
                        "Local or simple cloud deployment"
                    ]
                },
                "technical_requirements": {
                    "languages": ["Python", "JavaScript", "HTML", "CSS"],
                    "frameworks": ["Django", "Bootstrap"],
                    "apis": ["Django REST API"],
                    "infrastructure": ["Simple web hosting", "SQLite database"]
                },
                "constraints": {
                    "technical": [
                        "Modern web browser compatibility",
                        "Responsive design for different screen sizes"
                    ],
                    "business": [
                        "Low-cost hosting solution",
                        "Quick development timeline"
                    ],
                    "performance": [
                        "Fast task loading and search",
                        "Responsive user interface"
                    ]
                },
                "considerations": {
                    "security": [
                        "Basic user authentication",
                        "Input validation for task data"
                    ],
                    "scalability": [
                        "Handle growing number of tasks",
                        "Efficient search as task list grows"
                    ],
                    "maintainability": [
                        "Clean code structure",
                        "Easy to add new features",
                        "Simple backup procedures"
                    ]
                }
            }
        }
        
        # Test validation through Garden Planner Validator
        is_valid, validated_analysis, validation_history = await garden_planner_validator.validate_initial_task_analysis(
            user_request,
            garden_planner_output,
            "integration_test_validator"
        )
        
        # Validation should complete successfully
        assert isinstance(is_valid, bool), "Should return boolean validation result"
        assert validated_analysis is not None, "Should return validated analysis"
        assert isinstance(validation_history, list), "Should return validation history"
        
        # For moderate-quality task management app, should be valid or corrected
        assert is_valid is True, "Moderate-quality task management app should be validated"
        
        # Validation history should contain at least one entry
        assert len(validation_history) > 0, "Should have validation history entries"
        
        # Verify validation history structure
        for entry in validation_history:
            assert "cycle" in entry, "History entry should have cycle number"
            assert "validation_category" in entry, "History entry should have validation category"
            assert "timestamp" in entry, "History entry should have timestamp"

    # Test Metrics and State Tracking

    @pytest.mark.asyncio
    async def test_validation_metrics_and_state_tracking(self, earth_agent):
        """Test that validation properly tracks metrics and state throughout the process."""
        user_request = "Create a simple website with contact form"
        
        simple_output = {
            "task_analysis": {
                "original_request": user_request,
                "interpreted_goal": "Build a basic website with contact functionality",
                "scope": {
                    "included": ["Home page", "Contact form", "Form submission"],
                    "excluded": ["E-commerce", "User accounts"],
                    "assumptions": ["Static hosting", "Email integration"]
                },
                "technical_requirements": {
                    "languages": ["HTML", "CSS", "JavaScript", "Python"],
                    "frameworks": ["Django"],
                    "apis": ["Email API"],
                    "infrastructure": ["Web hosting", "Email service"]
                },
                "constraints": {
                    "technical": ["Modern browsers"],
                    "business": ["Low cost"],
                    "performance": ["Fast loading"]
                },
                "considerations": {
                    "security": ["Form validation", "Spam protection"],
                    "scalability": ["Handle form submissions"],
                    "maintainability": ["Easy updates"]
                }
            }
        }
        
        # Check initial state
        initial_cycle = await earth_agent.get_current_validation_cycle()
        assert initial_cycle == 0, "Should start with cycle 0"
        
        initial_history = await earth_agent.get_validation_history()
        assert len(initial_history) == 0, "Should start with empty history"
        
        # Perform validation
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            simple_output,
            "integration_test_metrics_tracking"
        )
        
        # Verify validation completed
        assert "validation_result" in result, "Should have validation result"
        
        # Check that validation history was updated
        final_history = await earth_agent.get_validation_history()
        assert len(final_history) > len(initial_history), "History should be updated after validation"
        
        # Verify validation cycle was incremented
        final_cycle = await earth_agent.get_current_validation_cycle()
        assert final_cycle > initial_cycle, "Validation cycle should be incremented"
        
        # Verify state is appropriate
        assert earth_agent.development_state in [DevelopmentState.COMPLETE, DevelopmentState.REFINING], \
            "Earth Agent should be in appropriate final state"

    # Test Error Recovery in Integration

    @pytest.mark.asyncio
    async def test_integration_error_recovery(self, earth_agent):
        """Test error recovery in full integration workflow."""
        user_request = "Create a web application"
        
        # Test with completely malformed input
        malformed_output = {
            "wrong_structure": "invalid data",
            "not_task_analysis": ["wrong", "format"]
        }
        
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            malformed_output,
            "integration_test_error_recovery"
        )
        
        # Should handle malformed input gracefully
        assert "error" in result, "Should detect error in malformed input"
        assert result["validation_result"]["validation_category"] == "REJECTED"
        assert earth_agent.development_state == DevelopmentState.ERROR
        
        # Reset agent for next test
        await earth_agent.reset_validation_cycle_counter()
        earth_agent.development_state = DevelopmentState.INITIALIZING
        
        # Test with valid input after error recovery
        valid_output = {
            "task_analysis": {
                "original_request": user_request,
                "interpreted_goal": "Build a web application",
                "scope": {
                    "included": ["Basic features"],
                    "excluded": ["Advanced features"],
                    "assumptions": ["Web deployment"]
                },
                "technical_requirements": {
                    "languages": ["Python"],
                    "frameworks": ["Django"],
                    "apis": ["REST"],
                    "infrastructure": ["Cloud"]
                },
                "constraints": {
                    "technical": ["Modern browsers"],
                    "business": ["Budget constraints"],
                    "performance": ["Good performance"]
                },
                "considerations": {
                    "security": ["Basic security"],
                    "scalability": ["Scalable design"],
                    "maintainability": ["Maintainable code"]
                }
            }
        }
        
        result2 = await earth_agent.validate_garden_planner_output(
            user_request,
            valid_output,
            "integration_test_recovery_success"
        )
        
        # Should recover and process valid input successfully
        assert "error" not in result2, "Should recover from previous error"
        assert "validation_result" in result2
        assert earth_agent.development_state in [DevelopmentState.COMPLETE, DevelopmentState.REFINING]

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])