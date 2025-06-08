"""
Tests for Earth Agent validation accuracy and decision-making logic.

This module tests the Earth Agent's ability to make accurate validation decisions
with real Garden Planner outputs, testing the actual validation prompts and
decision logic without mocking the core validation process.
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
from phase_one.models.enums import DevelopmentState

logger = logging.getLogger(__name__)

class TestEarthAgentValidationAccuracy:
    """Test suite for Earth Agent validation accuracy with real scenarios."""

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
            agent_id="test_earth_agent_accuracy",
            **real_resources,
            max_validation_cycles=2  # Limit cycles for faster testing
        )

    @pytest.fixture
    def excellent_garden_planner_output(self):
        """High-quality Garden Planner output that should be APPROVED."""
        return {
            "task_analysis": {
                "original_request": "Create a comprehensive project management web application for small teams with task tracking, time management, and collaboration features",
                "interpreted_goal": "Develop a full-featured project management platform that enables small teams (3-10 people) to efficiently organize tasks, track time, collaborate on projects, and monitor progress through an intuitive web interface",
                "scope": {
                    "included": [
                        "User authentication and role-based access control",
                        "Project creation and management interface",
                        "Task assignment and tracking system",
                        "Time tracking and reporting functionality",
                        "Team collaboration tools (comments, file sharing)",
                        "Dashboard with project overview and analytics",
                        "Notification system for deadlines and updates",
                        "Data export capabilities (CSV, PDF reports)",
                        "Mobile-responsive web interface"
                    ],
                    "excluded": [
                        "Native mobile applications (iOS/Android)",
                        "Advanced enterprise features (SSO, LDAP integration)",
                        "Video conferencing integration",
                        "Advanced project portfolio management",
                        "Third-party calendar integrations initially",
                        "Multi-language support in initial version"
                    ],
                    "assumptions": [
                        "Target users have reliable internet connectivity",
                        "Teams primarily use desktop/laptop computers for work",
                        "PostgreSQL database provides sufficient performance",
                        "AWS cloud infrastructure for hosting and scaling",
                        "Modern web browsers (Chrome, Firefox, Safari, Edge) support",
                        "GDPR compliance required for European users",
                        "Standard working hours timezone support initially"
                    ]
                },
                "technical_requirements": {
                    "languages": ["Python", "JavaScript", "TypeScript", "HTML5", "CSS3", "SQL"],
                    "frameworks": ["Django", "Django REST Framework", "React", "Redux", "Bootstrap", "Celery"],
                    "apis": ["REST API", "WebSocket API for real-time updates", "File upload API"],
                    "infrastructure": ["AWS EC2", "AWS RDS (PostgreSQL)", "AWS S3", "Redis", "Docker", "Nginx", "Let's Encrypt SSL"]
                },
                "constraints": {
                    "technical": [
                        "Must support modern browsers released within last 2 years",
                        "Mobile-responsive design required for tablet/phone access",
                        "Real-time updates required for collaborative features",
                        "File upload size limit of 100MB per file",
                        "Database must support ACID transactions for data integrity"
                    ],
                    "business": [
                        "12-month development timeline with 3 major milestones",
                        "Development team of 2-3 full-stack developers",
                        "Budget allocation for cloud infrastructure and tools",
                        "Beta testing period with 5-10 pilot teams",
                        "Compliance with data protection regulations"
                    ],
                    "performance": [
                        "Page load times under 1.5 seconds on standard broadband",
                        "API response times under 100ms for most operations",
                        "Support for 100 concurrent users per team",
                        "99.5% uptime SLA target",
                        "Database queries optimized for <50ms response time"
                    ]
                },
                "considerations": {
                    "security": [
                        "HTTPS encryption for all communications",
                        "JWT token-based authentication with refresh tokens",
                        "Password policies and secure password storage (bcrypt)",
                        "Input validation and sanitization against XSS/CSRF",
                        "SQL injection prevention with parameterized queries",
                        "Rate limiting to prevent abuse",
                        "Audit logging for sensitive operations",
                        "Data encryption at rest for sensitive information"
                    ],
                    "scalability": [
                        "Database indexing strategy for efficient queries",
                        "Redis caching for frequently accessed data",
                        "CDN integration for static assets",
                        "Horizontal scaling capability with load balancing",
                        "Database connection pooling",
                        "Asynchronous task processing with Celery",
                        "Auto-scaling policies for cloud infrastructure"
                    ],
                    "maintainability": [
                        "Comprehensive unit and integration test coverage (>90%)",
                        "Detailed API documentation with OpenAPI/Swagger",
                        "Code style enforcement with linting tools",
                        "Version control workflow with feature branches",
                        "Automated CI/CD pipeline with deployment automation",
                        "Error monitoring and logging with structured logging",
                        "Performance monitoring and alerting",
                        "Regular security updates and dependency management"
                    ]
                }
            }
        }

    @pytest.fixture
    def poor_garden_planner_output(self):
        """Low-quality Garden Planner output that should be REJECTED."""
        return {
            "task_analysis": {
                "original_request": "Create a project management app",
                "interpreted_goal": "Make an app for projects",  # Extremely vague
                "scope": {
                    "included": ["tasks", "users", "stuff"],  # Vague and uninformative
                    "excluded": [],  # Missing exclusions
                    "assumptions": ["it works", "people use it"]  # Vague assumptions
                },
                "technical_requirements": {
                    "languages": ["code"],  # Not a real programming language
                    "frameworks": ["web framework"],  # Vague framework
                    "apis": ["internet"],  # Not a real API specification
                    "infrastructure": ["computer", "internet"]  # Vague infrastructure
                },
                "constraints": {
                    "technical": ["works on computers"],  # Vague constraint
                    "business": ["cheap", "fast"],  # Vague business constraints
                    "performance": ["good", "not slow"]  # Unmeasurable performance requirements
                },
                "considerations": {
                    "security": ["safe"],  # Vague security consideration
                    "scalability": ["big"],  # Vague scalability consideration
                    "maintainability": ["easy"]  # Vague maintainability consideration
                }
            }
        }

    @pytest.fixture
    def needs_correction_output(self):
        """Garden Planner output with some issues that should be CORRECTED."""
        return {
            "task_analysis": {
                "original_request": "Create a simple task management web application for personal use",
                "interpreted_goal": "Build a personal task management web application for individual users to organize and track their daily tasks and projects",
                "scope": {
                    "included": [
                        "User registration and login",
                        "Task creation and editing",
                        "Task categorization and tagging",
                        "Due date tracking",
                        "Task completion status"
                    ],
                    "excluded": [
                        "Multi-user collaboration",
                        "Team management features",
                        "Advanced reporting"
                    ],
                    "assumptions": [
                        "Single-user focused application",
                        "Web-based interface",
                        "Basic database storage"
                    ]
                },
                "technical_requirements": {
                    "languages": ["Python", "JavaScript"],
                    "frameworks": ["Django"],  # Missing frontend framework
                    "apis": ["REST"],  # Could be more specific
                    "infrastructure": ["server", "database"]  # Vague infrastructure specification
                },
                "constraints": {
                    "technical": [
                        "Must work in web browsers"  # Could be more specific about browser support
                    ],
                    "business": [
                        "Low cost solution"  # Vague business constraint
                    ],
                    "performance": [
                        "Should be fast"  # Unmeasurable performance requirement
                    ]
                },
                "considerations": {
                    "security": [
                        "User authentication required",
                        "Secure data storage"  # Could be more specific
                    ],
                    "scalability": [
                        "Handle growing number of tasks"  # Vague scalability requirement
                    ],
                    "maintainability": [
                        "Clean code",  # Vague maintainability requirement
                        "Documentation"
                    ]
                }
            }
        }

    @pytest.fixture
    def misaligned_output(self):
        """Garden Planner output that misunderstands the user request."""
        return {
            "task_analysis": {
                "original_request": "Create a simple personal todo list web application",
                "interpreted_goal": "Build an enterprise-grade project management platform with advanced team collaboration and portfolio management capabilities",  # Massive scope creep
                "scope": {
                    "included": [
                        "Multi-tenant architecture for enterprise deployment",
                        "Advanced project portfolio management",
                        "Resource allocation and capacity planning",
                        "Time tracking with billing integration",
                        "Advanced reporting and analytics dashboards",
                        "Integration with CRM and ERP systems",
                        "Custom workflow automation engine",
                        "Multi-language support for global teams"
                    ],
                    "excluded": [
                        "Simple task lists",  # This contradicts the user request
                        "Personal use features"
                    ],
                    "assumptions": [
                        "Enterprise customer base with complex needs",
                        "Large development team and extended timeline",
                        "Significant budget for enterprise features"
                    ]
                },
                "technical_requirements": {
                    "languages": ["Java", "Scala", "Go"],  # Overly complex for simple todo list
                    "frameworks": ["Spring Boot", "Microservices", "Kubernetes"],
                    "apis": ["GraphQL", "gRPC", "Enterprise Service Bus"],
                    "infrastructure": ["Kubernetes cluster", "Elasticsearch", "Apache Kafka", "Redis Cluster"]
                },
                "constraints": {
                    "technical": [
                        "Must support 10,000+ concurrent users",
                        "Multi-region deployment required",
                        "Enterprise security compliance (SOX, HIPAA)"
                    ],
                    "business": [
                        "18-month development timeline",
                        "Team of 15+ developers",
                        "Enterprise sales and support model"
                    ],
                    "performance": [
                        "Sub-10ms API response times",
                        "Support for millions of tasks",
                        "Real-time analytics processing"
                    ]
                },
                "considerations": {
                    "security": [
                        "Enterprise SSO integration (SAML, LDAP)",
                        "Advanced audit logging and compliance",
                        "Zero-trust security architecture"
                    ],
                    "scalability": [
                        "Auto-scaling microservices architecture",
                        "Global content delivery network",
                        "Multi-region data replication"
                    ],
                    "maintainability": [
                        "Enterprise monitoring and observability platform",
                        "Automated deployment pipelines",
                        "Comprehensive enterprise documentation"
                    ]
                }
            }
        }

    # Test Validation Decision Accuracy

    @pytest.mark.asyncio
    async def test_excellent_output_gets_approved(self, earth_agent, excellent_garden_planner_output):
        """Test that high-quality Garden Planner output gets APPROVED."""
        user_request = "Create a comprehensive project management web application for small teams with task tracking, time management, and collaboration features"
        
        # This test may take longer due to actual LLM processing
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            excellent_garden_planner_output,
            "test_excellent_approval"
        )
        
        # Check that validation succeeded without errors
        assert "error" not in result, f"Validation should not have errors, got: {result.get('error', 'None')}"
        
        # High-quality output should be approved or corrected, not rejected
        validation_category = result.get("validation_result", {}).get("validation_category")
        assert validation_category in ["APPROVED", "CORRECTED"], f"Expected APPROVED or CORRECTED, got {validation_category}"
        
        # Should have minimal or no high/critical issues
        issues = result.get("architectural_issues", [])
        critical_issues = [issue for issue in issues if issue.get("severity") == "CRITICAL"]
        high_issues = [issue for issue in issues if issue.get("severity") == "HIGH"]
        
        assert len(critical_issues) == 0, f"High-quality output should not have critical issues, found: {critical_issues}"
        assert len(high_issues) <= 1, f"High-quality output should have minimal high issues, found: {high_issues}"

    @pytest.mark.asyncio 
    async def test_poor_output_gets_rejected(self, earth_agent, poor_garden_planner_output):
        """Test that low-quality Garden Planner output gets REJECTED."""
        user_request = "Create a project management app"
        
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            poor_garden_planner_output,
            "test_poor_rejection"
        )
        
        # Check that validation succeeded without errors
        assert "error" not in result, f"Validation should not have errors, got: {result.get('error', 'None')}"
        
        # Poor quality output should be rejected
        validation_category = result.get("validation_result", {}).get("validation_category")
        assert validation_category == "REJECTED", f"Expected REJECTED, got {validation_category}"
        
        # Should have multiple critical or high severity issues
        issues = result.get("architectural_issues", [])
        critical_issues = [issue for issue in issues if issue.get("severity") == "CRITICAL"]
        high_issues = [issue for issue in issues if issue.get("severity") == "HIGH"]
        
        # Poor output should have significant issues
        total_critical_high = len(critical_issues) + len(high_issues)
        assert total_critical_high >= 2, f"Poor output should have multiple critical/high issues, found {total_critical_high}"

    @pytest.mark.asyncio
    async def test_needs_correction_output_gets_corrected(self, earth_agent, needs_correction_output):
        """Test that output with moderate issues gets CORRECTED."""
        user_request = "Create a simple task management web application for personal use"
        
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            needs_correction_output,
            "test_correction_needed"
        )
        
        # Check that validation succeeded without errors
        assert "error" not in result, f"Validation should not have errors, got: {result.get('error', 'None')}"
        
        # Should be corrected or approved (Earth Agent might provide corrections)
        validation_category = result.get("validation_result", {}).get("validation_category")
        assert validation_category in ["CORRECTED", "APPROVED"], f"Expected CORRECTED or APPROVED, got {validation_category}"
        
        # If corrected, should have corrected_update field
        if validation_category == "CORRECTED":
            assert "corrected_update" in result, "CORRECTED validation should include corrected_update"
            corrected_analysis = result["corrected_update"].get("task_analysis", {})
            assert corrected_analysis, "Corrected update should contain task_analysis"

    @pytest.mark.asyncio
    async def test_misaligned_output_gets_rejected(self, earth_agent, misaligned_output):
        """Test that output misaligned with user request gets REJECTED."""
        user_request = "Create a simple personal todo list web application"
        
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            misaligned_output,
            "test_misalignment_rejection"
        )
        
        # Check that validation succeeded without errors
        assert "error" not in result, f"Validation should not have errors, got: {result.get('error', 'None')}"
        
        # Misaligned output should be rejected
        validation_category = result.get("validation_result", {}).get("validation_category")
        assert validation_category == "REJECTED", f"Expected REJECTED for misaligned output, got {validation_category}"
        
        # Should identify requirement gaps or technical misalignments
        issues = result.get("architectural_issues", [])
        issue_types = [issue.get("issue_type") for issue in issues]
        assert "requirement_gap" in issue_types or "technical_misalignment" in issue_types, \
            f"Should identify requirement/alignment issues, found types: {issue_types}"

    # Test Issue Classification Accuracy

    @pytest.mark.asyncio
    async def test_issue_type_classification(self, earth_agent, poor_garden_planner_output):
        """Test that issues are classified with appropriate types."""
        user_request = "Create a detailed project management application"
        
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            poor_garden_planner_output,
            "test_issue_classification"
        )
        
        issues = result.get("architectural_issues", [])
        assert len(issues) > 0, "Poor output should generate issues"
        
        # Check that all issues have valid types
        valid_issue_types = [
            "requirement_gap", 
            "technical_misalignment", 
            "invalid_assumption", 
            "constraint_incompatibility", 
            "insufficient_consideration"
        ]
        
        for issue in issues:
            issue_type = issue.get("issue_type")
            assert issue_type in valid_issue_types, f"Invalid issue type: {issue_type}"
            
            # Verify required fields are present
            assert "issue_id" in issue, "Issue should have issue_id"
            assert "severity" in issue, "Issue should have severity"
            assert "description" in issue, "Issue should have description"
            assert "affected_areas" in issue, "Issue should have affected_areas"
            assert "suggested_resolution" in issue, "Issue should have suggested_resolution"

    @pytest.mark.asyncio
    async def test_severity_classification_accuracy(self, earth_agent, poor_garden_planner_output):
        """Test that severity levels are appropriately assigned."""
        user_request = "Create a project management system with specific requirements"
        
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            poor_garden_planner_output,
            "test_severity_classification"
        )
        
        issues = result.get("architectural_issues", [])
        assert len(issues) > 0, "Should generate issues for poor output"
        
        # Check severity distribution
        severity_counts = {}
        valid_severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        
        for issue in issues:
            severity = issue.get("severity")
            assert severity in valid_severities, f"Invalid severity: {severity}"
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Poor output should have some high-severity issues
        high_severity_count = severity_counts.get("CRITICAL", 0) + severity_counts.get("HIGH", 0)
        assert high_severity_count > 0, "Poor output should have at least some high-severity issues"

    # Test Validation Consistency

    @pytest.mark.asyncio
    async def test_validation_consistency_across_runs(self, earth_agent, needs_correction_output):
        """Test that validation results are reasonably consistent across multiple runs."""
        user_request = "Create a simple task management web application for personal use"
        
        # Run validation multiple times
        results = []
        for i in range(3):
            result = await earth_agent.validate_garden_planner_output(
                user_request,
                needs_correction_output,
                f"test_consistency_{i}"
            )
            results.append(result)
            
            # Reset agent state for next run
            await earth_agent.reset_validation_cycle_counter()
            earth_agent.development_state = DevelopmentState.INITIALIZING
        
        # Check that all runs succeeded
        for i, result in enumerate(results):
            assert "error" not in result, f"Run {i} should not have errors"
        
        # Extract validation categories
        categories = [r.get("validation_result", {}).get("validation_category") for r in results]
        
        # Should not have any rejected results for moderate-quality input
        assert "REJECTED" not in categories, f"Moderate-quality input should not be rejected, got categories: {categories}"
        
        # Should be consistent in general assessment (all approved or all corrected)
        unique_categories = set(categories)
        assert len(unique_categories) <= 2, f"Results should be reasonably consistent, got: {categories}"

    # Test Validation Decision Rules

    @pytest.mark.asyncio
    async def test_validation_decision_rules_adherence(self, earth_agent):
        """Test that validation follows the decision rules specified in the prompts."""
        # Test with output that should clearly violate decision rules
        
        # Create output that should be rejected due to multiple critical issues
        critical_issues_output = {
            "task_analysis": {
                "original_request": "Create a secure banking application",
                "interpreted_goal": "Build a basic website",  # Completely misunderstands security needs
                "scope": {
                    "included": ["login page"],  # Severely inadequate for banking
                    "excluded": ["security", "encryption"],  # Excludes critical requirements
                    "assumptions": ["security not important"]  # Invalid assumption for banking
                },
                "technical_requirements": {
                    "languages": ["HTML"],  # Inadequate for banking app
                    "frameworks": [],  # No frameworks specified
                    "apis": [],  # No APIs specified
                    "infrastructure": ["shared hosting"]  # Inappropriate for banking
                },
                "constraints": {
                    "technical": ["works on old browsers"],  # Inappropriate constraint
                    "business": ["free to build"],  # Unrealistic for banking
                    "performance": ["doesn't matter"]  # Inappropriate for banking
                },
                "considerations": {
                    "security": [],  # No security considerations for banking app!
                    "scalability": [],  # No scalability considerations
                    "maintainability": []  # No maintainability considerations
                }
            }
        }
        
        user_request = "Create a secure online banking application with transaction processing, account management, and regulatory compliance"
        
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            critical_issues_output,
            "test_decision_rules"
        )
        
        # Should be rejected due to critical security and requirement issues
        validation_category = result.get("validation_result", {}).get("validation_category")
        assert validation_category == "REJECTED", f"Output with critical security gaps should be REJECTED, got {validation_category}"
        
        # Should identify critical issues
        issues = result.get("architectural_issues", [])
        critical_issues = [issue for issue in issues if issue.get("severity") == "CRITICAL"]
        assert len(critical_issues) > 0, "Should identify critical issues for banking app without security considerations"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])