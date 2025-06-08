"""
Tests for Earth Agent error handling and edge cases.

This module tests the Earth Agent's robustness in handling various error
conditions, edge cases, and failure scenarios that might occur during
validation processes.
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
from unittest.mock import patch, AsyncMock

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

class TestEarthAgentErrorHandling:
    """Test suite for Earth Agent error handling and edge cases."""

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
            agent_id="test_earth_agent_error_handling",
            **real_resources,
            max_validation_cycles=2  # Limit cycles for faster error testing
        )

    # Test Input Validation Errors

    @pytest.mark.asyncio
    async def test_none_garden_planner_output(self, earth_agent):
        """Test validation with None as Garden Planner output."""
        user_request = "Create a web application"
        
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            None,  # None input
            "test_none_output"
        )
        
        # Should handle None gracefully and return error response
        assert "error" in result
        assert result["validation_result"]["validation_category"] == "REJECTED"
        assert "Invalid Garden Planner output structure" in result["error"]

    @pytest.mark.asyncio
    async def test_empty_dictionary_output(self, earth_agent):
        """Test validation with empty dictionary as Garden Planner output."""
        user_request = "Create a web application"
        
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            {},  # Empty dictionary
            "test_empty_dict"
        )
        
        # Should handle empty dictionary and return error response
        assert "error" in result
        assert result["validation_result"]["validation_category"] == "REJECTED"
        assert "Invalid Garden Planner output structure" in result["error"]

    @pytest.mark.asyncio
    async def test_non_dictionary_output(self, earth_agent):
        """Test validation with non-dictionary Garden Planner output."""
        user_request = "Create a web application"
        
        # Test with string
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            "not a dictionary",
            "test_string_output"
        )
        
        assert "error" in result
        assert result["validation_result"]["validation_category"] == "REJECTED"
        
        # Test with list
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            ["not", "a", "dictionary"],
            "test_list_output"
        )
        
        assert "error" in result
        assert result["validation_result"]["validation_category"] == "REJECTED"

    @pytest.mark.asyncio
    async def test_missing_required_top_level_fields(self, earth_agent):
        """Test validation with missing required top-level fields."""
        user_request = "Create a web application"
        
        # Missing task_analysis entirely
        invalid_output = {
            "some_other_field": "value",
            "another_field": {"nested": "data"}
        }
        
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            invalid_output,
            "test_missing_task_analysis"
        )
        
        assert "error" in result
        assert result["validation_result"]["validation_category"] == "REJECTED"
        assert "Invalid Garden Planner output structure" in result["error"]

    @pytest.mark.asyncio
    async def test_malformed_task_analysis_structure(self, earth_agent):
        """Test validation with malformed task_analysis structure."""
        user_request = "Create a web application"
        
        # task_analysis is not a dictionary
        invalid_output = {
            "task_analysis": "should be a dictionary"
        }
        
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            invalid_output,
            "test_malformed_task_analysis"
        )
        
        assert "error" in result
        assert result["validation_result"]["validation_category"] == "REJECTED"

    # Test User Request Validation

    @pytest.mark.asyncio
    async def test_empty_user_request(self, earth_agent):
        """Test validation with empty user request."""
        valid_garden_planner_output = {
            "task_analysis": {
                "original_request": "Create a web app",
                "interpreted_goal": "Build a web application",
                "scope": {
                    "included": ["basic features"],
                    "excluded": ["advanced features"],
                    "assumptions": ["web deployment"]
                },
                "technical_requirements": {
                    "languages": ["Python"],
                    "frameworks": ["Django"],
                    "apis": ["REST"],
                    "infrastructure": ["cloud"]
                },
                "constraints": {
                    "technical": ["modern browsers"],
                    "business": ["6 months"],
                    "performance": ["fast response"]
                },
                "considerations": {
                    "security": ["HTTPS"],
                    "scalability": ["cloud scaling"],
                    "maintainability": ["documentation"]
                }
            }
        }
        
        # Test with empty string
        result = await earth_agent.validate_garden_planner_output(
            "",  # Empty user request
            valid_garden_planner_output,
            "test_empty_user_request"
        )
        
        # Should still attempt validation but may identify issues
        assert "validation_result" in result

    @pytest.mark.asyncio
    async def test_none_user_request(self, earth_agent):
        """Test validation with None user request."""
        valid_garden_planner_output = {
            "task_analysis": {
                "original_request": "Create a web app",
                "interpreted_goal": "Build a web application",
                "scope": {
                    "included": ["features"],
                    "excluded": ["other features"],
                    "assumptions": ["assumptions"]
                },
                "technical_requirements": {
                    "languages": ["Python"],
                    "frameworks": ["Django"],
                    "apis": ["REST"],
                    "infrastructure": ["cloud"]
                },
                "constraints": {
                    "technical": ["constraints"],
                    "business": ["business"],
                    "performance": ["performance"]
                },
                "considerations": {
                    "security": ["security"],
                    "scalability": ["scalability"],
                    "maintainability": ["maintainability"]
                }
            }
        }
        
        # Earth Agent should handle None user request gracefully
        result = await earth_agent.validate_garden_planner_output(
            None,  # None user request
            valid_garden_planner_output,
            "test_none_user_request"
        )
        
        # Should complete validation but may identify issues with None request
        assert "validation_result" in result

    # Test Validation ID Edge Cases

    @pytest.mark.asyncio
    async def test_none_validation_id(self, earth_agent):
        """Test validation with None validation ID (should auto-generate)."""
        user_request = "Create a simple web application"
        valid_output = {
            "task_analysis": {
                "original_request": user_request,
                "interpreted_goal": "Build a web application",
                "scope": {
                    "included": ["features"],
                    "excluded": ["other"],
                    "assumptions": ["web"]
                },
                "technical_requirements": {
                    "languages": ["Python"],
                    "frameworks": ["Django"],
                    "apis": ["REST"],
                    "infrastructure": ["cloud"]
                },
                "constraints": {
                    "technical": ["modern"],
                    "business": ["budget"],
                    "performance": ["fast"]
                },
                "considerations": {
                    "security": ["secure"],
                    "scalability": ["scalable"],
                    "maintainability": ["maintainable"]
                }
            }
        }
        
        # Should auto-generate validation ID when None is provided
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            valid_output,
            None  # None validation ID
        )
        
        assert "validation_result" in result

    @pytest.mark.asyncio
    async def test_empty_validation_id(self, earth_agent):
        """Test validation with empty string validation ID."""
        user_request = "Create a web application"
        valid_output = {
            "task_analysis": {
                "original_request": user_request,
                "interpreted_goal": "Build a web application",
                "scope": {
                    "included": ["features"],
                    "excluded": ["other"],
                    "assumptions": ["web"]
                },
                "technical_requirements": {
                    "languages": ["Python"],
                    "frameworks": ["Django"],
                    "apis": ["REST"],
                    "infrastructure": ["cloud"]
                },
                "constraints": {
                    "technical": ["modern"],
                    "business": ["budget"],
                    "performance": ["fast"]
                },
                "considerations": {
                    "security": ["secure"],
                    "scalability": ["scalable"],
                    "maintainability": ["maintainable"]
                }
            }
        }
        
        # Should handle empty validation ID gracefully
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            valid_output,
            ""  # Empty validation ID
        )
        
        assert "validation_result" in result

    # Test Circuit Breaker Error Scenarios

    @pytest.mark.asyncio
    async def test_circuit_breaker_failure_handling(self, earth_agent):
        """Test handling when circuit breaker fails."""
        user_request = "Create a web application"
        valid_output = {
            "task_analysis": {
                "original_request": user_request,
                "interpreted_goal": "Build a web application",
                "scope": {
                    "included": ["features"],
                    "excluded": ["other"],
                    "assumptions": ["web"]
                },
                "technical_requirements": {
                    "languages": ["Python"],
                    "frameworks": ["Django"],
                    "apis": ["REST"],
                    "infrastructure": ["cloud"]
                },
                "constraints": {
                    "technical": ["modern"],
                    "business": ["budget"],
                    "performance": ["fast"]
                },
                "considerations": {
                    "security": ["secure"],
                    "scalability": ["scalable"],
                    "maintainability": ["maintainable"]
                }
            }
        }
        
        # Mock circuit breaker to simulate failure
        with patch.object(earth_agent, 'get_circuit_breaker') as mock_get_cb:
            mock_circuit_breaker = AsyncMock()
            mock_circuit_breaker.execute = AsyncMock(side_effect=Exception("Circuit breaker failure"))
            mock_get_cb.return_value = mock_circuit_breaker
            
            result = await earth_agent.validate_garden_planner_output(
                user_request,
                valid_output,
                "test_circuit_breaker_failure"
            )
            
            # Should handle circuit breaker failure gracefully
            assert "error" in result
            assert result["validation_result"]["validation_category"] == "REJECTED"
            assert earth_agent.development_state == DevelopmentState.ERROR

    # Test State Management Error Scenarios

    @pytest.mark.asyncio
    async def test_state_manager_failure_handling(self, earth_agent):
        """Test handling when state manager operations fail."""
        user_request = "Create a web application"
        valid_output = {
            "task_analysis": {
                "original_request": user_request,
                "interpreted_goal": "Build a web application",
                "scope": {
                    "included": ["features"],
                    "excluded": ["other"],
                    "assumptions": ["web"]
                },
                "technical_requirements": {
                    "languages": ["Python"],
                    "frameworks": ["Django"],
                    "apis": ["REST"],
                    "infrastructure": ["cloud"]
                },
                "constraints": {
                    "technical": ["modern"],
                    "business": ["budget"],
                    "performance": ["fast"]
                },
                "considerations": {
                    "security": ["secure"],
                    "scalability": ["scalable"],
                    "maintainability": ["maintainable"]
                }
            }
        }
        
        # Mock state manager to simulate failure
        with patch.object(earth_agent._state_manager, 'set_state', side_effect=Exception("State manager failure")):
            result = await earth_agent.validate_garden_planner_output(
                user_request,
                valid_output,
                "test_state_manager_failure"
            )
            
            # Should handle state manager failure gracefully
            # May still complete validation but log errors
            assert "validation_result" in result

    # Test Memory Monitoring Edge Cases

    @pytest.mark.asyncio
    async def test_memory_tracking_failure_handling(self, earth_agent):
        """Test handling when memory tracking fails."""
        user_request = "Create a web application"
        valid_output = {
            "task_analysis": {
                "original_request": user_request,
                "interpreted_goal": "Build a web application",
                "scope": {
                    "included": ["features"],
                    "excluded": ["other"],
                    "assumptions": ["web"]
                },
                "technical_requirements": {
                    "languages": ["Python"],
                    "frameworks": ["Django"],
                    "apis": ["REST"],
                    "infrastructure": ["cloud"]
                },
                "constraints": {
                    "technical": ["modern"],
                    "business": ["budget"],
                    "performance": ["fast"]
                },
                "considerations": {
                    "security": ["secure"],
                    "scalability": ["scalable"],
                    "maintainability": ["maintainable"]
                }
            }
        }
        
        # Mock memory tracking to simulate failure
        with patch.object(earth_agent, 'track_dict_memory', side_effect=Exception("Memory tracking failure")):
            result = await earth_agent.validate_garden_planner_output(
                user_request,
                valid_output,
                "test_memory_tracking_failure"
            )
            
            # Should handle memory tracking failure gracefully
            assert "validation_result" in result

    # Test Large Input Handling

    @pytest.mark.asyncio
    async def test_very_large_garden_planner_output(self, earth_agent):
        """Test handling of very large Garden Planner output."""
        user_request = "Create a complex enterprise application"
        
        # Create a very large output with many items
        large_output = {
            "task_analysis": {
                "original_request": user_request,
                "interpreted_goal": "Build a comprehensive enterprise application with extensive features",
                "scope": {
                    "included": [f"Feature {i}" for i in range(100)],  # 100 features
                    "excluded": [f"Excluded feature {i}" for i in range(50)],  # 50 exclusions
                    "assumptions": [f"Assumption {i}" for i in range(30)]  # 30 assumptions
                },
                "technical_requirements": {
                    "languages": [f"Language {i}" for i in range(20)],
                    "frameworks": [f"Framework {i}" for i in range(15)],
                    "apis": [f"API {i}" for i in range(25)],
                    "infrastructure": [f"Infrastructure component {i}" for i in range(10)]
                },
                "constraints": {
                    "technical": [f"Technical constraint {i}" for i in range(20)],
                    "business": [f"Business constraint {i}" for i in range(15)],
                    "performance": [f"Performance requirement {i}" for i in range(10)]
                },
                "considerations": {
                    "security": [f"Security consideration {i}" for i in range(25)],
                    "scalability": [f"Scalability consideration {i}" for i in range(15)],
                    "maintainability": [f"Maintainability consideration {i}" for i in range(20)]
                }
            }
        }
        
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            large_output,
            "test_large_output"
        )
        
        # Should handle large input without crashing
        assert "validation_result" in result

    # Test Unicode and Special Characters

    @pytest.mark.asyncio
    async def test_unicode_and_special_characters(self, earth_agent):
        """Test handling of Unicode and special characters in input."""
        user_request = "Créer une application web avec des caractères spéciaux: 中文, العربية, 🚀"
        
        unicode_output = {
            "task_analysis": {
                "original_request": user_request,
                "interpreted_goal": "Construire une application web avec support Unicode complet",
                "scope": {
                    "included": ["Interface multilingue 🌍", "Support UTF-8", "Caractères chinois: 中文"],
                    "excluded": ["Anciennes encodages", "ASCII seulement"],
                    "assumptions": ["Navigateurs modernes", "UTF-8 par défaut"]
                },
                "technical_requirements": {
                    "languages": ["Python 🐍", "JavaScript"],
                    "frameworks": ["Django avec i18n", "React"],
                    "apis": ["REST API Unicode"],
                    "infrastructure": ["UTF-8 database"]
                },
                "constraints": {
                    "technical": ["Support complet Unicode"],
                    "business": ["Multi-langue requis"],
                    "performance": ["Gestion efficace UTF-8"]
                },
                "considerations": {
                    "security": ["Validation Unicode", "XSS prevention"],
                    "scalability": ["Multi-région"],
                    "maintainability": ["Documentation multilingue"]
                }
            }
        }
        
        result = await earth_agent.validate_garden_planner_output(
            user_request,
            unicode_output,
            "test_unicode_characters"
        )
        
        # Should handle Unicode characters without issues
        assert "validation_result" in result

    # Test Concurrent Validation Handling

    @pytest.mark.asyncio
    async def test_validation_cycle_counter_edge_cases(self, earth_agent):
        """Test edge cases with validation cycle counter."""
        # Test maximum cycles reached
        earth_agent.current_validation_cycle = earth_agent.max_validation_cycles
        
        assert await earth_agent.has_reached_max_cycles() is True
        
        # Test beyond maximum
        earth_agent.current_validation_cycle = earth_agent.max_validation_cycles + 1
        assert await earth_agent.has_reached_max_cycles() is True
        
        # Test negative cycles (shouldn't happen but test robustness)
        earth_agent.current_validation_cycle = -1
        assert await earth_agent.has_reached_max_cycles() is False
        
        await earth_agent.reset_validation_cycle_counter()
        assert await earth_agent.get_current_validation_cycle() == 0

    # Test Health Reporting Edge Cases

    @pytest.mark.asyncio
    async def test_health_reporting_failure_handling(self, earth_agent):
        """Test handling when health reporting fails."""
        # Mock health reporting to simulate failure
        with patch.object(earth_agent, '_report_agent_health', side_effect=Exception("Health reporting failure")):
            validation_result = {
                "validation_result": {"validation_category": "APPROVED"}
            }
            
            # Should handle health reporting failure gracefully
            await earth_agent._update_state_from_validation(validation_result)
            
            # State should still be updated despite health reporting failure
            assert earth_agent.development_state == DevelopmentState.COMPLETE

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])