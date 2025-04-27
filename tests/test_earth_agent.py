import asyncio
import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock, AsyncMock

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from resources.earth_agent import EarthAgent, AbstractionTier
from interface import AgentInterface

class TestEarthAgent(unittest.TestCase):
    """Test the EarthAgent functionality."""

    def setUp(self):
        """Set up the test environment."""
        # Create mock resources
        self.mock_event_queue = MagicMock()
        self.mock_event_queue.start = AsyncMock()
        self.mock_event_queue.emit = AsyncMock()
        
        self.mock_state_manager = MagicMock()
        self.mock_state_manager.set_state = AsyncMock()
        self.mock_state_manager.get_state = AsyncMock()
        
        self.mock_context_manager = MagicMock()
        self.mock_cache_manager = MagicMock()
        self.mock_metrics_manager = MagicMock()
        self.mock_metrics_manager.record_metric = AsyncMock()
        
        self.mock_error_handler = MagicMock()
        self.mock_memory_monitor = MagicMock()
        
        # Create dependency validator mock
        self.mock_dependency_validator = MagicMock()
        self.mock_dependency_validator.validate_structural_breakdown = AsyncMock(return_value=(True, []))
        
        # Create Earth agent with mocks
        self.earth_agent = EarthAgent(
            agent_id="test_earth_agent",
            event_queue=self.mock_event_queue,
            state_manager=self.mock_state_manager,
            context_manager=self.mock_context_manager,
            cache_manager=self.mock_cache_manager,
            metrics_manager=self.mock_metrics_manager,
            error_handler=self.mock_error_handler,
            memory_monitor=self.mock_memory_monitor,
            max_iterations=3
        )
        
        # Mock the dependency validator
        self.earth_agent.dependency_validator = self.mock_dependency_validator
        
        # Mock the process_with_validation method
        self.earth_agent.process_with_validation = AsyncMock()
        
        # Mock dependency analysis methods
        self.earth_agent._prepare_validation_context = AsyncMock()
        self.earth_agent._reflect_and_revise_validation = AsyncMock()

    @patch.object(EarthAgent, 'process_with_validation')
    @patch.object(EarthAgent, '_prepare_validation_context')
    @patch.object(EarthAgent, '_reflect_and_revise_validation')
    async def test_validate_guideline_update_component_tier(self, mock_reflect, mock_prepare, mock_process):
        """Test that the Earth agent properly validates component tier guidelines."""
        # Mock response data
        mock_response = {
            "validation_result": {
                "is_valid": True,
                "validation_category": "APPROVED",
                "explanation": "The update maintains architectural integrity."
            },
            "architectural_issues": [],
            "corrected_update": None,
            "metadata": {
                "validation_timestamp": "2025-04-24T10:00:00",
                "original_agent": "component_architect",
                "affected_downstream_components": []
            }
        }
        
        # Setup mocks
        mock_process.return_value = mock_response
        mock_reflect.return_value = mock_response  # Reflection returns same response
        mock_prepare.return_value = {
            "agent_id": "component_architect",
            "current_guideline": {},
            "proposed_update": {},
            "dependency_context": {
                "affected_downstream_components": [],
                "potential_dependency_impacts": []
            }
        }
        
        # Sample input data
        current_guideline = {
            "components": [
                {"id": "auth", "name": "Authentication", "dependencies": []}
            ]
        }
        
        proposed_update = {
            "components": [
                {"id": "auth", "name": "Authentication", "dependencies": []},
                {"id": "user", "name": "User Management", "dependencies": ["auth"]}
            ]
        }
        
        # Call the validation method
        result = await self.earth_agent.validate_guideline_update(
            abstraction_tier="COMPONENT",
            agent_id="component_architect",
            current_guideline=current_guideline,
            proposed_update=proposed_update,
            operation_id="test_op_1"
        )
        
        # Check that process_with_validation was called with the right prompt path
        mock_process.assert_called_once()
        args, kwargs = mock_process.call_args
        self.assertEqual(kwargs['system_prompt_info'], 
                         ("FFTT_system_prompts/core_agents/earth_agent/component_tier_prompt", 
                          "component_tier_prompt"))
        
        # Verify prepare validation context was called
        mock_prepare.assert_called_once_with(
            "COMPONENT", 
            "component_architect", 
            current_guideline, 
            proposed_update
        )
        
        # Verify reflect and revise was called
        mock_reflect.assert_called_once()
        
        # Verify state was updated
        self.mock_state_manager.set_state.assert_called()
        
        # Verify metrics were recorded
        self.mock_metrics_manager.record_metric.assert_called_with(
            "earth_agent:validation_count",
            1.0,
            metadata={
                "agent_id": "component_architect",
                "tier": "COMPONENT",
                "is_valid": True
            }
        )
        
        # Check that validation history was updated
        self.assertEqual(len(self.earth_agent.validation_history["component_architect"]), 1)
        self.assertEqual(self.earth_agent.validation_history["component_architect"][0]["is_valid"], True)
        
        # Verify the result matches the mock response
        self.assertEqual(result, mock_response)
        
    @patch.object(EarthAgent, 'validate_guideline_update')
    async def test_process_guideline_update(self, mock_validate):
        """Test the process_guideline_update method for different validation categories."""
        # Test case 1: APPROVED validation - should return the proposed update
        mock_validate.return_value = {
            "validation_result": {
                "is_valid": True,
                "validation_category": "APPROVED",
                "explanation": "Valid update"
            }
        }
        
        current = {"id": "auth"}
        proposed = {"id": "auth", "description": "Authentication service"}
        
        accepted, result, details = await self.earth_agent.process_guideline_update(
            "COMPONENT", "test_agent", current, proposed
        )
        
        self.assertTrue(accepted)
        self.assertEqual(result, proposed)
        
        # Test case 2: CORRECTED validation - should return the corrected update
        corrected = {"id": "auth", "description": "Authentication and authorization service"}
        mock_validate.return_value = {
            "validation_result": {
                "is_valid": True,
                "validation_category": "CORRECTED",
                "explanation": "Minor corrections applied"
            },
            "corrected_update": corrected
        }
        
        accepted, result, details = await self.earth_agent.process_guideline_update(
            "COMPONENT", "test_agent", current, proposed
        )
        
        self.assertTrue(accepted)
        self.assertEqual(result, corrected)
        
        # Test case 3: REJECTED validation - should return the current guideline
        mock_validate.return_value = {
            "validation_result": {
                "is_valid": False,
                "validation_category": "REJECTED",
                "explanation": "Invalid update"
            }
        }
        
        accepted, result, details = await self.earth_agent.process_guideline_update(
            "COMPONENT", "test_agent", current, proposed
        )
        
        self.assertFalse(accepted)
        self.assertEqual(result, current)

    @patch.object(EarthAgent, 'process_with_validation')
    async def test_reflection_and_revision(self, mock_process):
        """Test the reflection and revision process."""
        # Mock initial validation result
        initial_result = {
            "validation_result": {
                "is_valid": True,
                "validation_category": "APPROVED",
                "explanation": "Initial validation"
            },
            "architectural_issues": [],
            "corrected_update": None,
            "metadata": {}
        }
        
        # Mock reflection result with quality score and critical improvements
        reflection_result = {
            "reflection_results": {
                "overall_assessment": {
                    "decision_quality_score": 6,  # Lower score to trigger revision
                    "critical_improvements": [
                        {"priority": 8, "area": "dependency_analysis", "recommendation": "Consider deeper impact"}
                    ]
                }
            }
        }
        
        # Mock revision result
        revised_validation = {
            "validation_result": {
                "is_valid": True,
                "validation_category": "APPROVED",
                "explanation": "Revised explanation with deeper dependency analysis"
            },
            "architectural_issues": [],
            "corrected_update": None,
            "metadata": {"improved": True}
        }
        
        revision_result = {
            "revision_results": {
                "revised_validation": revised_validation,
                "revision_summary": {
                    "decision_changes": {"category_changed": False},
                    "confidence": {"score": 9}
                }
            }
        }
        
        # Configure mock to return different results on different calls
        mock_process.side_effect = [
            initial_result,          # Initial validation 
            reflection_result,       # First reflection
            revision_result,         # First revision
        ]
        
        # Test data
        validation_context = {
            "agent_id": "test_agent",
            "current_guideline": {},
            "proposed_update": {},
            "dependency_context": {}
        }
        
        # Call reflection and revision
        result = await self.earth_agent._reflect_and_revise_validation(
            initial_result,
            "COMPONENT",
            validation_context,
            "test_op_1"
        )
        
        # Check it made correct number of calls
        self.assertEqual(mock_process.call_count, 2)  # 1 reflection + 1 revision
        
        # Verify the result is the revised validation
        self.assertEqual(result, revised_validation)
        
        # Verify revision attempt counter incremented
        self.assertEqual(self.earth_agent.revision_attempts["test_op_1"], 1)

    @patch.object(EarthAgent, 'process_with_validation')
    async def test_reflection_max_iterations(self, mock_process):
        """Test that reflection/revision respects max iterations."""
        # Set max_iterations to a small number for testing
        self.earth_agent.max_iterations = 2
        
        # Mock results
        initial_result = {"validation_result": {"is_valid": True, "validation_category": "APPROVED"}}
        
        # First iteration
        reflection1 = {
            "reflection_results": {
                "overall_assessment": {
                    "decision_quality_score": 5,
                    "critical_improvements": [{"priority": 8, "area": "test", "recommendation": "Improve"}]
                }
            }
        }
        
        revision1 = {
            "revision_results": {
                "revised_validation": {"validation_result": {"is_valid": True, "validation_category": "APPROVED", "version": 1}},
                "revision_summary": {
                    "decision_changes": {"category_changed": False},
                    "confidence": {"score": 6}
                }
            }
        }
        
        # Second iteration - would stop after this due to max iterations
        reflection2 = {
            "reflection_results": {
                "overall_assessment": {
                    "decision_quality_score": 6,
                    "critical_improvements": [{"priority": 7, "area": "test", "recommendation": "Further improve"}]
                }
            }
        }
        
        revision2 = {
            "revision_results": {
                "revised_validation": {"validation_result": {"is_valid": True, "validation_category": "APPROVED", "version": 2}},
                "revision_summary": {
                    "decision_changes": {"category_changed": False},
                    "confidence": {"score": 7}
                }
            }
        }
        
        # Configure mock
        mock_process.side_effect = [
            reflection1, revision1,   # First iteration
            reflection2, revision2    # Second iteration
        ]
        
        # Set up test
        validation_context = {"agent_id": "test", "current_guideline": {}, "proposed_update": {}}
        
        # Call reflection and revision
        result = await self.earth_agent._reflect_and_revise_validation(
            initial_result,
            "COMPONENT",
            validation_context,
            "test_max"
        )
        
        # Verify it stopped after max iterations
        self.assertEqual(self.earth_agent.revision_attempts["test_max"], 2)
        self.assertEqual(mock_process.call_count, 4)  # 2 iterations * (1 reflection + 1 revision)
        
        # Verify final result
        self.assertEqual(result["validation_result"]["version"], 2)

    async def test_prepare_validation_context(self):
        """Test preparation of validation context with dependency information."""
        # Mock agent's dependency methods
        self.earth_agent._get_affected_downstream_components = AsyncMock(return_value=set(["api", "database"]))
        self.earth_agent._analyze_component_dependencies = AsyncMock(return_value=[
            {"impact_type": "dependency_cycle", "source": "a", "target": "b"}
        ])
        
        # Test data
        current_guideline = {"components": [{"name": "auth"}]}
        proposed_update = {"ordered_components": [{"name": "auth"}, {"name": "user"}]}
        
        # Call the method
        context = await self.earth_agent._prepare_validation_context(
            "COMPONENT", 
            "test_agent", 
            current_guideline, 
            proposed_update
        )
        
        # Verify basic context
        self.assertEqual(context["agent_id"], "test_agent")
        self.assertEqual(context["current_guideline"], current_guideline)
        self.assertEqual(context["proposed_update"], proposed_update)
        
        # Verify dependency context for component tier
        self.assertIn("dependency_context", context)
        self.assertIn("affected_downstream_components", context["dependency_context"])
        self.assertIn("potential_dependency_impacts", context["dependency_context"])
        self.assertEqual(set(context["dependency_context"]["affected_downstream_components"]), set(["api", "database"]))
        self.assertEqual(len(context["dependency_context"]["potential_dependency_impacts"]), 1)
        
        # Test feature tier context
        self.earth_agent._get_affected_features = AsyncMock(return_value=set(["login", "profile"]))
        self.earth_agent._analyze_feature_dependencies = AsyncMock(return_value=[
            {"impact_type": "missing_feature_dependency", "feature": "a", "missing_dependency": "b"}
        ])
        
        feature_context = await self.earth_agent._prepare_validation_context(
            "FEATURE",
            "test_agent",
            {},
            {"component_id": "auth", "features": []}
        )
        
        # Verify feature tier context
        self.assertIn("dependency_context", feature_context)
        self.assertEqual(feature_context["dependency_context"]["component_id"], "auth")
        self.assertEqual(set(feature_context["dependency_context"]["affected_features"]), set(["login", "profile"]))

    async def test_get_validation_stats(self):
        """Test that validation statistics are correctly calculated."""
        # Set up test data
        self.earth_agent.validation_history = {
            "agent1": [
                {"tier": "COMPONENT", "is_valid": True, "timestamp": "2025-04-24T10:00:00"},
                {"tier": "COMPONENT", "is_valid": False, "timestamp": "2025-04-24T11:00:00"}
            ],
            "agent2": [
                {"tier": "FEATURE", "is_valid": True, "timestamp": "2025-04-24T10:30:00"},
                {"tier": "FUNCTIONALITY", "is_valid": False, "timestamp": "2025-04-24T11:30:00"}
            ]
        }
        
        # Get stats
        stats = await self.earth_agent.get_validation_stats()
        
        # Verify stats
        self.assertEqual(stats["total_validations"], 4)
        self.assertEqual(stats["validations_by_agent"], {"agent1": 2, "agent2": 2})
        self.assertEqual(stats["validations_by_tier"]["COMPONENT"], 2)
        self.assertEqual(stats["validations_by_tier"]["FEATURE"], 1)
        self.assertEqual(stats["validations_by_tier"]["FUNCTIONALITY"], 1)
        self.assertEqual(stats["approval_rate"], 0.5)  # 2 approved out of 4 total

def run_async_test(test_case):
    """Helper function to run async test cases."""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_case)

if __name__ == '__main__':
    unittest.main()