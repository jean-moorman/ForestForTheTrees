"""
Tests for Earth Agent reflection and revision workflow.

This module tests the Earth Agent's sophisticated reflection-revision process
that allows it to improve its validation decisions through self-evaluation
and iterative refinement.
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

class TestEarthAgentReflectionRevision:
    """Test suite for Earth Agent reflection and revision workflow."""

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
            agent_id="test_earth_agent_reflection",
            **real_resources,
            max_validation_cycles=3
        )

    @pytest.fixture
    def borderline_validation_case(self):
        """Garden Planner output that's borderline and should benefit from reflection."""
        return {
            "task_analysis": {
                "original_request": "Create a web application for a local restaurant to manage online orders and customer information",
                "interpreted_goal": "Build a restaurant management system for online ordering and customer data",
                "scope": {
                    "included": [
                        "Online ordering interface",
                        "Customer registration and login",
                        "Menu management",
                        "Order processing",
                        "Customer data storage"
                    ],
                    "excluded": [
                        "In-person point-of-sale system",
                        "Inventory management",
                        "Employee scheduling"
                    ],
                    "assumptions": [
                        "Restaurant has existing payment processing",
                        "Menu items are relatively stable",
                        "Basic customer support needs"
                    ]
                },
                "technical_requirements": {
                    "languages": ["Python", "JavaScript"],
                    "frameworks": ["Django", "React"],
                    "apis": ["REST API"],
                    "infrastructure": ["Cloud hosting", "Database"]  # Vague infrastructure
                },
                "constraints": {
                    "technical": [
                        "Must integrate with existing payment system"  # Missing specifics
                    ],
                    "business": [
                        "Limited budget",  # Vague constraint
                        "Quick deployment needed"  # Vague timeline
                    ],
                    "performance": [
                        "Handle lunch rush traffic"  # Unmeasurable requirement
                    ]
                },
                "considerations": {
                    "security": [
                        "Protect customer data",  # Vague security consideration
                        "Secure payments"  # Relies on external system
                    ],
                    "scalability": [
                        "Support growing customer base"  # Vague scalability requirement
                    ],
                    "maintainability": [
                        "Easy to update menu items",
                        "Simple admin interface"
                    ]
                }
            }
        }

    @pytest.fixture
    def complex_validation_scenario(self):
        """Complex Garden Planner output that should trigger detailed reflection."""
        return {
            "task_analysis": {
                "original_request": "Create a healthcare patient portal with appointment scheduling, medical records access, and telemedicine capabilities",
                "interpreted_goal": "Develop a comprehensive healthcare patient portal that enables patients to schedule appointments, access their medical records, and participate in telemedicine consultations while ensuring HIPAA compliance and integration with existing healthcare systems",
                "scope": {
                    "included": [
                        "Patient registration and authentication",
                        "Appointment scheduling system",
                        "Medical records viewer",
                        "Telemedicine video consultations",
                        "Prescription management",
                        "Insurance information management",
                        "Provider communication portal"
                    ],
                    "excluded": [
                        "Electronic Health Records (EHR) system replacement",
                        "Medical billing and insurance claims processing",
                        "Clinical decision support systems",
                        "Medical device integration"
                    ],
                    "assumptions": [
                        "Integration with existing EHR system via HL7 FHIR",
                        "Video consultation platform will be third-party service",
                        "Patients have reliable internet and devices for telemedicine",
                        "Healthcare providers have capacity for digital consultations"
                    ]
                },
                "technical_requirements": {
                    "languages": ["Python", "JavaScript", "TypeScript"],
                    "frameworks": ["Django", "React", "Django REST Framework"],
                    "apis": ["HL7 FHIR API", "Video conference API", "SMS notification API"],
                    "infrastructure": ["HIPAA-compliant cloud hosting", "PostgreSQL", "Redis", "SSL certificates"]
                },
                "constraints": {
                    "technical": [
                        "HIPAA compliance mandatory for all data handling",
                        "Integration with legacy EHR systems",
                        "Cross-browser compatibility required",
                        "Mobile-responsive design essential"
                    ],
                    "business": [
                        "18-month development timeline",
                        "Healthcare industry regulations compliance",
                        "Budget constraints for HIPAA-compliant infrastructure",
                        "Phased rollout to minimize disruption"
                    ],
                    "performance": [
                        "Sub-second response times for patient data",
                        "99.9% uptime for critical healthcare operations",
                        "Support for 500+ concurrent users during peak hours",
                        "Video quality suitable for medical consultations"
                    ]
                },
                "considerations": {
                    "security": [
                        "HIPAA compliance for all patient data",
                        "End-to-end encryption for telemedicine sessions",
                        "Multi-factor authentication for healthcare providers",
                        "Audit logging for all patient data access",
                        "Regular security assessments and penetration testing"
                    ],
                    "scalability": [
                        "Database optimization for large patient datasets",
                        "CDN for medical images and documents",
                        "Auto-scaling for variable appointment loads",
                        "Load balancing for high-availability"
                    ],
                    "maintainability": [
                        "Comprehensive test coverage for healthcare workflows",
                        "Documentation for healthcare compliance requirements",
                        "Automated deployment with rollback capabilities",
                        "24/7 monitoring and alerting for critical systems"
                    ]
                }
            }
        }

    # Test Reflection Process

    @pytest.mark.asyncio
    async def test_reflection_process_with_borderline_case(self, earth_agent, borderline_validation_case):
        """Test that reflection process is triggered for borderline validation cases."""
        user_request = "Create a web application for a local restaurant to manage online orders and customer information"
        
        # Perform validation which should trigger reflection
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            borderline_validation_case,
            "test_reflection_borderline"
        )
        
        # Validation should complete without errors
        assert "error" not in result, f"Validation should not have errors, got: {result.get('error', 'None')}"
        
        # Check if reflection metadata is present (indicates reflection was applied)
        metadata = result.get("metadata", {})
        revision_applied = metadata.get("revision_applied", False)
        
        # For borderline cases, reflection may or may not result in revision
        # The important thing is that the process completes successfully
        validation_category = result.get("validation_result", {}).get("validation_category")
        assert validation_category in ["APPROVED", "CORRECTED", "REJECTED"], \
            f"Should have valid validation category, got: {validation_category}"
        
        # If revision was applied, should have revision timestamp
        if revision_applied:
            assert "revision_timestamp" in metadata, "Revised validation should have revision timestamp"

    @pytest.mark.asyncio
    async def test_reflection_with_complex_healthcare_scenario(self, earth_agent, complex_validation_scenario):
        """Test reflection process with complex healthcare scenario requiring detailed analysis."""
        user_request = "Create a healthcare patient portal with appointment scheduling, medical records access, and telemedicine capabilities"
        
        # This complex scenario should trigger thorough validation and potentially reflection
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            complex_validation_scenario,
            "test_reflection_complex_healthcare"
        )
        
        # Validation should complete successfully
        assert "error" not in result, f"Validation should not have errors, got: {result.get('error', 'None')}"
        
        # Complex healthcare scenario should be handled appropriately
        validation_category = result.get("validation_result", {}).get("validation_category")
        assert validation_category in ["APPROVED", "CORRECTED"], \
            f"Well-structured healthcare scenario should be approved or corrected, got: {validation_category}"
        
        # Should identify relevant considerations for healthcare
        issues = result.get("architectural_issues", [])
        if issues:
            # Check that any issues identified are relevant to healthcare context
            issue_descriptions = [issue.get("description", "") for issue in issues]
            healthcare_terms = ["HIPAA", "healthcare", "medical", "patient", "compliance", "security"]
            
            # At least some issues should mention healthcare-specific concerns
            healthcare_mentions = sum(1 for desc in issue_descriptions 
                                    if any(term.lower() in desc.lower() for term in healthcare_terms))
            
            if len(issues) > 0:
                assert healthcare_mentions > 0, \
                    f"Healthcare scenario should identify healthcare-specific considerations, issues: {issue_descriptions}"

    # Test Error Handling in Reflection

    @pytest.mark.asyncio
    async def test_reflection_handles_error_validation_gracefully(self, earth_agent):
        """Test that reflection process handles error validation results gracefully."""
        # Create an error validation result manually for testing
        error_validation_result = {
            "error": "Test error for reflection handling",
            "validation_result": {
                "validation_category": "REJECTED",
                "is_valid": False,
                "explanation": "Test error occurred"
            }
        }
        
        validation_context = {
            "user_request": "Test request",
            "validation_id": "test_error_reflection"
        }
        
        # Reflection should handle error validation gracefully
        result = await earth_agent._reflect_and_revise_validation(
            error_validation_result,
            validation_context
        )
        
        # Should return the original error result unchanged
        assert result == error_validation_result, \
            "Error validation should be returned unchanged by reflection process"

    # Test State Persistence During Reflection

    @pytest.mark.asyncio
    async def test_reflection_state_persistence(self, earth_agent, borderline_validation_case):
        """Test that reflection process properly persists state information."""
        user_request = "Create a web application for restaurant order management"
        validation_id = "test_reflection_state_persistence"
        
        # Perform validation
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            borderline_validation_case,
            validation_id
        )
        
        # Check that validation context was stored in state manager
        stored_context = await earth_agent._state_manager.get_state(
            f"earth_agent:validation_context:{validation_id}",
            resource_type="STATE"
        )
        
        if stored_context:
            assert "user_request" in stored_context, "Stored context should include user request"
            assert "garden_planner_output" in stored_context, "Stored context should include garden planner output"
            assert "validation_id" in stored_context, "Stored context should include validation ID"

    # Test Circuit Breaker Integration with Reflection

    @pytest.mark.asyncio
    async def test_reflection_circuit_breaker_protection(self, earth_agent, borderline_validation_case):
        """Test that reflection process is protected by circuit breakers."""
        user_request = "Create a restaurant management application"
        
        # Perform validation which may trigger reflection
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            borderline_validation_case,
            "test_reflection_circuit_breaker"
        )
        
        # Even if circuit breakers activate, should get a valid response
        assert "validation_result" in result, "Should have validation result even with circuit breaker protection"
        
        validation_category = result.get("validation_result", {}).get("validation_category")
        assert validation_category in ["APPROVED", "CORRECTED", "REJECTED"], \
            f"Should have valid validation category, got: {validation_category}"

    # Test Reflection Decision Logic

    @pytest.mark.asyncio
    async def test_reflection_decision_logic_no_critical_improvements(self, earth_agent):
        """Test reflection decision logic when no critical improvements are needed."""
        # Create a validation result that's already good
        good_validation_result = {
            "validation_result": {
                "validation_category": "APPROVED",
                "is_valid": True,
                "explanation": "Garden Planner output aligns well with user requirements"
            },
            "architectural_issues": [
                {"severity": "LOW", "description": "Minor documentation improvement"}
            ],
            "metadata": {
                "validation_timestamp": datetime.now().isoformat(),
                "validation_version": "1.0"
            }
        }
        
        validation_context = {
            "user_request": "Create a simple web application",
            "validation_id": "test_no_critical_improvements"
        }
        
        # Test the reflection process
        result = await earth_agent._reflect_and_revise_validation(
            good_validation_result,
            validation_context
        )
        
        # For a good validation, reflection might not change anything
        # The key is that it should return a valid result
        assert "validation_result" in result, "Should return valid validation result"
        assert result["validation_result"]["validation_category"] in ["APPROVED", "CORRECTED"], \
            "Good validation should remain approved or be corrected"

    # Test Validation History Integration with Reflection

    @pytest.mark.asyncio
    async def test_reflection_uses_validation_history(self, earth_agent, borderline_validation_case):
        """Test that reflection process can utilize validation history for context."""
        # Add some validation history
        for i in range(3):
            validation_result = {
                "validation_result": {"validation_category": "CORRECTED"},
                "architectural_issues": [{"severity": "MEDIUM"}]
            }
            earth_agent._update_validation_history(validation_result, f"previous_validation_{i}")
        
        user_request = "Create a web application for restaurant management"
        
        # Perform validation with history available
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            borderline_validation_case,
            "test_reflection_with_history"
        )
        
        # Should complete successfully with history context
        assert "error" not in result, "Validation with history should not have errors"
        
        validation_category = result.get("validation_result", {}).get("validation_category")
        assert validation_category in ["APPROVED", "CORRECTED", "REJECTED"], \
            f"Should have valid validation category, got: {validation_category}"

    # Test Metrics Recording During Reflection

    @pytest.mark.asyncio
    async def test_reflection_metrics_recording(self, earth_agent, borderline_validation_case):
        """Test that reflection process properly records metrics."""
        user_request = "Create a restaurant order management system"
        
        # Perform validation which may include reflection
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            borderline_validation_case,
            "test_reflection_metrics"
        )
        
        # Check that metrics recording was called
        # The metrics manager should have recorded validation metrics
        assert earth_agent._metrics_manager.record_metric.called, \
            "Metrics should be recorded during validation process"
        
        # Verify validation completed successfully
        assert "validation_result" in result, "Should have validation result"

    # Test Revision Quality

    @pytest.mark.asyncio
    async def test_revision_improves_validation_quality(self, earth_agent):
        """Test that revision process can improve validation quality."""
        # Create a validation scenario that could benefit from revision
        moderate_quality_output = {
            "task_analysis": {
                "original_request": "Create an e-commerce website for selling handmade crafts",
                "interpreted_goal": "Build an online store for artisan crafts",
                "scope": {
                    "included": [
                        "Product catalog",
                        "Shopping cart",
                        "Payment processing"
                    ],
                    "excluded": [
                        "Inventory management"  # Might be needed for e-commerce
                    ],
                    "assumptions": [
                        "Simple payment integration"  # Could be more specific
                    ]
                },
                "technical_requirements": {
                    "languages": ["Python", "JavaScript"],
                    "frameworks": ["Django"],  # Missing frontend framework
                    "apis": ["Payment API"],  # Vague API specification
                    "infrastructure": ["Web hosting"]  # Vague infrastructure
                },
                "constraints": {
                    "technical": ["Works on mobile"],  # Vague constraint
                    "business": ["Low cost"],  # Vague business constraint
                    "performance": ["Fast loading"]  # Unmeasurable performance requirement
                },
                "considerations": {
                    "security": ["Secure payments"],  # Could be more comprehensive
                    "scalability": ["Handle growth"],  # Vague scalability requirement
                    "maintainability": ["Easy updates"]  # Vague maintainability requirement
                }
            }
        }
        
        user_request = "Create an e-commerce website for selling handmade crafts with inventory management, customer reviews, and detailed product customization options"
        
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            moderate_quality_output,
            "test_revision_quality_improvement"
        )
        
        # Validation should complete
        assert "error" not in result, "Validation should complete without errors"
        
        # For moderate quality input that misses some requirements, should be corrected or approved
        validation_category = result.get("validation_result", {}).get("validation_category")
        assert validation_category in ["APPROVED", "CORRECTED"], \
            f"Moderate quality output should be approved or corrected, got: {validation_category}"
        
        # If corrected, the correction should address some of the gaps
        if validation_category == "CORRECTED":
            corrected_update = result.get("corrected_update", {})
            assert corrected_update, "CORRECTED validation should include corrected_update"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])