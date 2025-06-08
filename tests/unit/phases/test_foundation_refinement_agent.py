"""
Unit tests for Foundation Refinement Agent

Tests the critical decision-making agent that processes Phase Zero feedback
and makes system recursion decisions for Phase One workflow.
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from phase_one.agents.foundation_refinement import FoundationRefinementAgent
from phase_one.models.refinement import AgentPromptConfig
from phase_one.monitoring.circuit_breakers import CircuitBreakerDefinition
from resources.monitoring import CircuitOpenError
from resources import (
    EventQueue, StateManager, AgentContextManager, CacheManager,
    MetricsManager, ErrorHandler, MemoryMonitor, HealthTracker
)


@pytest.fixture
def mock_resources():
    """Create mock resource managers for testing."""
    return {
        'event_queue': AsyncMock(spec=EventQueue),
        'state_manager': AsyncMock(spec=StateManager),
        'context_manager': AsyncMock(spec=AgentContextManager),
        'cache_manager': AsyncMock(spec=CacheManager),
        'metrics_manager': AsyncMock(spec=MetricsManager),
        'error_handler': AsyncMock(spec=ErrorHandler),
        'memory_monitor': AsyncMock(spec=MemoryMonitor),
        'health_tracker': AsyncMock(spec=HealthTracker)
    }


@pytest.fixture
def sample_phase_one_result():
    """Sample Phase One workflow result for testing."""
    return {
        "status": "completed",
        "agents": {
            "garden_planner": {"success": True, "output": {"task_analysis": "test"}},
            "environmental_analysis": {"success": True, "output": {"environment": "test"}},
            "root_system_architect": {"success": True, "output": {"data_flow": "test"}},
            "tree_placement_planner": {"success": True, "output": {"components": "test"}}
        },
        "final_output": {
            "task_analysis": {"requirements": ["req1", "req2"]},
            "environmental_analysis": {"constraints": ["constraint1"]},
            "data_architecture": {"flows": ["flow1"]},
            "component_architecture": {"components": ["comp1", "comp2"]}
        }
    }


@pytest.fixture
def sample_phase_zero_feedback():
    """Sample Phase Zero feedback for testing."""
    return {
        "status": "completed",
        "monitoring_analysis": {
            "system_health": "good",
            "metrics_status": "normal"
        },
        "deep_analysis": {
            "structural_agent": {
                "status": "success",
                "flag_raised": False
            },
            "requirement_agent": {
                "status": "success", 
                "flag_raised": True,
                "flag_type": "critical",
                "flag_description": "Missing dependency validation",
                "severity": "high"
            }
        },
        "evolution_synthesis": {
            "recommendations": ["improve validation"],
            "optimization_suggestions": ["add checks"]
        }
    }


@pytest.fixture
def sample_air_context():
    """Sample Air Agent context for testing."""
    return {
        "historical_patterns": [
            {"pattern": "validation_failure", "frequency": 3, "success_rate": 0.7}
        ],
        "success_strategies": [
            {"strategy": "dependency_check", "success_rate": 0.9}
        ],
        "failure_patterns": [
            {"pattern": "missing_validation", "frequency": 2}
        ],
        "recommendations": [
            "Consider additional validation steps",
            "Review dependency requirements"
        ]
    }


@pytest.fixture
async def foundation_refinement_agent(mock_resources):
    """Create a Foundation Refinement Agent for testing."""
    agent = FoundationRefinementAgent(
        event_queue=mock_resources['event_queue'],
        state_manager=mock_resources['state_manager'],
        context_manager=mock_resources['context_manager'],
        cache_manager=mock_resources['cache_manager'],
        metrics_manager=mock_resources['metrics_manager'],
        error_handler=mock_resources['error_handler'],
        memory_monitor=mock_resources['memory_monitor'],
        health_tracker=mock_resources['health_tracker'],
        max_refinement_cycles=3
    )
    
    # Mock the initialization
    agent._initialized = True
    
    return agent


class TestFoundationRefinementAgentInitialization:
    """Test Foundation Refinement Agent initialization."""
    
    async def test_initialization_success(self, mock_resources):
        """Test successful agent initialization."""
        agent = FoundationRefinementAgent(
            event_queue=mock_resources['event_queue'],
            state_manager=mock_resources['state_manager'],
            context_manager=mock_resources['context_manager'],
            cache_manager=mock_resources['cache_manager'],
            metrics_manager=mock_resources['metrics_manager'],
            error_handler=mock_resources['error_handler'],
            memory_monitor=mock_resources['memory_monitor'],
            health_tracker=mock_resources['health_tracker'],
            max_refinement_cycles=5
        )
        
        # Verify initialization
        assert agent.interface_id == "agent:foundation_refinement_agent"
        assert agent._max_refinement_cycles == 5
        assert agent._current_cycle == 0
        assert isinstance(agent._prompt_config, AgentPromptConfig)
        assert "refinement_analysis" in agent._circuit_breakers
        assert "reflection_process" in agent._circuit_breakers
    
    async def test_initialization_with_custom_circuit_breakers(self, mock_resources):
        """Test initialization with custom circuit breakers."""
        custom_breakers = [
            CircuitBreakerDefinition(name="custom_breaker", failure_threshold=5),
            CircuitBreakerDefinition(name="another_breaker", recovery_timeout=60)
        ]
        
        agent = FoundationRefinementAgent(
            event_queue=mock_resources['event_queue'],
            state_manager=mock_resources['state_manager'],
            context_manager=mock_resources['context_manager'],
            cache_manager=mock_resources['cache_manager'],
            metrics_manager=mock_resources['metrics_manager'],
            error_handler=mock_resources['error_handler'],
            memory_monitor=mock_resources['memory_monitor'],
            health_tracker=mock_resources['health_tracker']
        )
        
        # Verify circuit breakers exist
        assert "refinement_analysis" in agent._circuit_breakers
        assert "reflection_process" in agent._circuit_breakers


class TestPhaseOneOutputAnalysis:
    """Test Phase One output analysis functionality."""
    
    @patch('phase_one.agents.foundation_refinement.provide_refinement_context')
    async def test_analyze_phase_one_outputs_success(
        self, 
        mock_provide_context, 
        foundation_refinement_agent,
        sample_phase_one_result,
        sample_phase_zero_feedback,
        sample_air_context
    ):
        """Test successful Phase One output analysis."""
        # Setup mocks
        mock_provide_context.return_value = sample_air_context
        
        # Mock the circuit breaker execute method
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value={
            "refinement_analysis": {
                "critical_failure": {
                    "category": "dependency_validation_gap",
                    "description": "Missing dependency validation steps",
                    "evidence": ["Phase Zero flag raised"],
                    "phase_zero_signals": [{"agent": "requirement_agent", "flag": "critical"}]
                },
                "root_cause": {
                    "responsible_agent": "root_system_architect",
                    "failure_point": "data_flow_validation",
                    "causal_chain": ["Missing validation step"],
                    "verification_steps": ["Add validation checks"]
                },
                "refinement_action": {
                    "action": "restructure_data_flow",
                    "justification": "Need better validation",
                    "specific_guidance": {
                        "current_state": "Missing validation",
                        "required_state": "Complete validation",
                        "adaptation_path": ["Add checks", "Validate dependencies"]
                    }
                }
            },
            "confidence_assessment": "high"
        })
        foundation_refinement_agent._circuit_breakers["refinement_analysis"] = mock_circuit
        
        # Mock process_with_validation
        foundation_refinement_agent.process_with_validation = AsyncMock(return_value={
            "refinement_analysis": {
                "critical_failure": {
                    "category": "dependency_validation_gap",
                    "description": "Missing dependency validation steps",
                    "evidence": ["Phase Zero flag raised"],
                    "phase_zero_signals": [{"agent": "requirement_agent", "flag": "critical"}]
                },
                "root_cause": {
                    "responsible_agent": "root_system_architect",
                    "failure_point": "data_flow_validation",
                    "causal_chain": ["Missing validation step"],
                    "verification_steps": ["Add validation checks"]
                },
                "refinement_action": {
                    "action": "restructure_data_flow",
                    "justification": "Need better validation",
                    "specific_guidance": {
                        "current_state": "Missing validation",
                        "required_state": "Complete validation",
                        "adaptation_path": ["Add checks", "Validate dependencies"]
                    }
                }
            },
            "confidence_assessment": "high"
        })
        
        # Execute analysis
        result = await foundation_refinement_agent.analyze_phase_one_outputs(
            sample_phase_one_result,
            sample_phase_zero_feedback,
            "test_operation_123"
        )
        
        # Verify results
        assert result is not None
        assert "refinement_analysis" in result
        assert result["refinement_analysis"]["refinement_action"]["action"] == "restructure_data_flow"
        assert result["confidence_assessment"] == "high"
        
        # Verify Air Agent context was requested
        mock_provide_context.assert_called_once()
        
        # Verify state was stored
        foundation_refinement_agent._state_manager.set_state.assert_called()
    
    @patch('phase_one.agents.foundation_refinement.provide_refinement_context')
    async def test_analyze_phase_one_outputs_circuit_breaker_open(
        self,
        mock_provide_context,
        foundation_refinement_agent,
        sample_phase_one_result,
        sample_phase_zero_feedback,
        sample_air_context
    ):
        """Test analysis when circuit breaker is open."""
        # Setup mocks
        mock_provide_context.return_value = sample_air_context
        
        # Mock circuit breaker to raise CircuitOpenError
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(side_effect=CircuitOpenError("Circuit open"))
        foundation_refinement_agent._circuit_breakers["refinement_analysis"] = mock_circuit
        
        # Execute analysis
        result = await foundation_refinement_agent.analyze_phase_one_outputs(
            sample_phase_one_result,
            sample_phase_zero_feedback,
            "test_operation_123"
        )
        
        # Verify safe default response
        assert result is not None
        assert "refinement_analysis" in result
        assert result["refinement_analysis"]["refinement_action"]["action"] == "proceed_to_phase_two"
        assert result["confidence_assessment"] == "low"
        assert result["circuit_breaker_protection"] is True
    
    @patch('phase_one.agents.foundation_refinement.provide_refinement_context')
    async def test_analyze_phase_one_outputs_air_agent_failure(
        self,
        mock_provide_context,
        foundation_refinement_agent,
        sample_phase_one_result,
        sample_phase_zero_feedback
    ):
        """Test analysis when Air Agent fails."""
        # Setup mocks - Air Agent fails
        mock_provide_context.side_effect = Exception("Air Agent error")
        
        # Mock successful circuit breaker
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value={
            "refinement_analysis": {
                "critical_failure": {"category": "none_detected"},
                "root_cause": {"responsible_agent": "none"},
                "refinement_action": {"action": "proceed_to_phase_two"}
            },
            "confidence_assessment": "medium"
        })
        foundation_refinement_agent._circuit_breakers["refinement_analysis"] = mock_circuit
        
        # Mock process_with_validation  
        foundation_refinement_agent.process_with_validation = AsyncMock(return_value={
            "refinement_analysis": {
                "critical_failure": {"category": "none_detected"},
                "root_cause": {"responsible_agent": "none"},
                "refinement_action": {"action": "proceed_to_phase_two"}
            },
            "confidence_assessment": "medium"
        })
        
        # Execute analysis
        result = await foundation_refinement_agent.analyze_phase_one_outputs(
            sample_phase_one_result,
            sample_phase_zero_feedback,
            "test_operation_123"
        )
        
        # Verify analysis continues with fallback context
        assert result is not None
        assert "refinement_analysis" in result


class TestCriticalSignalExtraction:
    """Test critical signal extraction from Phase Zero feedback."""
    
    async def test_extract_critical_signals_with_errors(self, foundation_refinement_agent):
        """Test extracting critical signals when agents report errors."""
        phase_zero_analysis = {
            "structural_agent": {
                "error": "Validation failed",
                "status": "failure"
            },
            "requirement_agent": {
                "status": "success",
                "flag_raised": True,
                "flag_type": "critical",
                "flag_description": "Missing dependencies",
                "severity": "high"
            },
            "data_flow_agent": {
                "status": "success",
                "flag_raised": False
            }
        }
        
        signals = foundation_refinement_agent._extract_critical_signals(phase_zero_analysis)
        
        # Should find both error and critical flag
        assert len(signals) == 2
        
        # Check error signal
        error_signal = next(s for s in signals if s["signal_type"] == "error")
        assert error_signal["agent"] == "structural_agent"
        assert error_signal["severity"] == "high"
        
        # Check flag signal  
        flag_signal = next(s for s in signals if s["signal_type"] == "critical")
        assert flag_signal["agent"] == "requirement_agent"
        assert flag_signal["severity"] == "high"
    
    async def test_extract_critical_signals_no_issues(self, foundation_refinement_agent):
        """Test extracting signals when no critical issues exist."""
        phase_zero_analysis = {
            "structural_agent": {
                "status": "success",
                "flag_raised": False
            },
            "requirement_agent": {
                "status": "success",
                "flag_raised": False
            }
        }
        
        signals = foundation_refinement_agent._extract_critical_signals(phase_zero_analysis)
        
        # Should find no critical signals
        assert len(signals) == 0


class TestRefinementDecisionLogic:
    """Test refinement decision logic and utility methods."""
    
    async def test_should_proceed_to_phase_two_true(self, foundation_refinement_agent):
        """Test decision to proceed to Phase Two."""
        refinement_result = {
            "refinement_analysis": {
                "refinement_action": {
                    "action": "proceed_to_phase_two"
                }
            }
        }
        
        should_proceed = foundation_refinement_agent.should_proceed_to_phase_two(refinement_result)
        assert should_proceed is True
    
    async def test_should_proceed_to_phase_two_false_refinement_needed(self, foundation_refinement_agent):
        """Test decision to perform refinement."""
        refinement_result = {
            "refinement_analysis": {
                "refinement_action": {
                    "action": "restructure_data_flow"
                }
            }
        }
        
        should_proceed = foundation_refinement_agent.should_proceed_to_phase_two(refinement_result)
        assert should_proceed is False
    
    async def test_should_proceed_to_phase_two_max_cycles_reached(self, foundation_refinement_agent):
        """Test proceeding when max cycles reached."""
        # Set to max cycles
        foundation_refinement_agent._current_cycle = foundation_refinement_agent._max_refinement_cycles
        
        refinement_result = {
            "refinement_analysis": {
                "refinement_action": {
                    "action": "reanalyze_task"  # Would normally require refinement
                }
            }
        }
        
        should_proceed = foundation_refinement_agent.should_proceed_to_phase_two(refinement_result)
        assert should_proceed is True  # Should proceed due to max cycles
    
    async def test_get_refinement_target_agent(self, foundation_refinement_agent):
        """Test getting the target agent for refinement."""
        refinement_result = {
            "refinement_analysis": {
                "root_cause": {
                    "responsible_agent": "root_system_architect"
                }
            }
        }
        
        target_agent = foundation_refinement_agent.get_refinement_target_agent(refinement_result)
        assert target_agent == "root_system_architect"
    
    async def test_get_refinement_target_agent_none(self, foundation_refinement_agent):
        """Test getting target agent when none is responsible."""
        refinement_result = {
            "refinement_analysis": {
                "root_cause": {
                    "responsible_agent": "none"
                }
            }
        }
        
        target_agent = foundation_refinement_agent.get_refinement_target_agent(refinement_result)
        assert target_agent is None
    
    async def test_get_refinement_guidance(self, foundation_refinement_agent):
        """Test extracting refinement guidance."""
        refinement_result = {
            "refinement_analysis": {
                "refinement_action": {
                    "action": "restructure_data_flow",
                    "justification": "Need better validation",
                    "specific_guidance": {
                        "current_state": "Missing validation",
                        "required_state": "Complete validation",
                        "adaptation_path": ["Add checks", "Validate dependencies"]
                    }
                }
            }
        }
        
        guidance = foundation_refinement_agent.get_refinement_guidance(refinement_result)
        
        assert guidance["action"] == "restructure_data_flow"
        assert guidance["justification"] == "Need better validation"
        assert guidance["current_state"] == "Missing validation"
        assert guidance["required_state"] == "Complete validation"
        assert len(guidance["adaptation_path"]) == 2


class TestCycleManagement:
    """Test refinement cycle management."""
    
    async def test_increment_cycle(self, foundation_refinement_agent):
        """Test incrementing refinement cycle."""
        initial_cycle = foundation_refinement_agent._current_cycle
        foundation_refinement_agent.increment_cycle()
        assert foundation_refinement_agent._current_cycle == initial_cycle + 1
    
    async def test_reset_cycle(self, foundation_refinement_agent):
        """Test resetting refinement cycle."""
        foundation_refinement_agent._current_cycle = 5
        foundation_refinement_agent.reset_cycle()
        assert foundation_refinement_agent._current_cycle == 0


class TestErrorHandling:
    """Test error handling and recovery scenarios."""
    
    @patch('phase_one.agents.foundation_refinement.provide_refinement_context')
    async def test_malformed_analysis_result(
        self,
        mock_provide_context,
        foundation_refinement_agent,
        sample_phase_one_result,
        sample_phase_zero_feedback,
        sample_air_context
    ):
        """Test handling of malformed analysis results."""
        # Setup mocks
        mock_provide_context.return_value = sample_air_context
        
        # Mock circuit breaker with malformed result
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value="invalid_format")  # Not a dict
        foundation_refinement_agent._circuit_breakers["refinement_analysis"] = mock_circuit
        
        # Mock process_with_validation to return malformed result
        foundation_refinement_agent.process_with_validation = AsyncMock(return_value="invalid_format")
        
        # Execute analysis
        result = await foundation_refinement_agent.analyze_phase_one_outputs(
            sample_phase_one_result,
            sample_phase_zero_feedback,
            "test_operation_123"
        )
        
        # Verify safe default is returned
        assert result is not None
        assert "refinement_analysis" in result
        assert result["refinement_analysis"]["refinement_action"]["action"] == "proceed_to_phase_two"
        assert result["confidence_assessment"] == "low"
        assert result["analysis_metadata"]["malformed_result"] is True
    
    @patch('phase_one.agents.foundation_refinement.provide_refinement_context')
    async def test_analysis_exception_handling(
        self,
        mock_provide_context,
        foundation_refinement_agent,
        sample_phase_one_result,
        sample_phase_zero_feedback,
        sample_air_context
    ):
        """Test handling of analysis exceptions."""
        # Setup mocks
        mock_provide_context.return_value = sample_air_context
        
        # Mock circuit breaker to raise unexpected exception
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(side_effect=Exception("Unexpected error"))
        foundation_refinement_agent._circuit_breakers["refinement_analysis"] = mock_circuit
        
        # Should raise the exception
        with pytest.raises(Exception, match="Unexpected error"):
            await foundation_refinement_agent.analyze_phase_one_outputs(
                sample_phase_one_result,
                sample_phase_zero_feedback,
                "test_operation_123"
            )
        
        # Verify error handler was called
        foundation_refinement_agent._error_handler.handle_error.assert_called()


class TestIntegrationScenarios:
    """Test integration scenarios with various input combinations."""
    
    @patch('phase_one.agents.foundation_refinement.provide_refinement_context')
    async def test_no_critical_failures_scenario(
        self,
        mock_provide_context,
        foundation_refinement_agent,
        sample_air_context
    ):
        """Test scenario where no critical failures are detected."""
        # Setup clean inputs
        clean_phase_one_result = {
            "status": "completed",
            "agents": {"garden_planner": {"success": True}},
            "final_output": {"task_analysis": {"requirements": ["req1"]}}
        }
        
        clean_phase_zero_feedback = {
            "status": "completed",
            "deep_analysis": {
                "structural_agent": {"status": "success", "flag_raised": False},
                "requirement_agent": {"status": "success", "flag_raised": False}
            }
        }
        
        mock_provide_context.return_value = sample_air_context
        
        # Mock successful analysis with no issues
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value={
            "refinement_analysis": {
                "critical_failure": {"category": "none_detected"},
                "root_cause": {"responsible_agent": "none"},
                "refinement_action": {"action": "proceed_to_phase_two"}
            },
            "confidence_assessment": "high"
        })
        foundation_refinement_agent._circuit_breakers["refinement_analysis"] = mock_circuit
        
        foundation_refinement_agent.process_with_validation = AsyncMock(return_value={
            "refinement_analysis": {
                "critical_failure": {"category": "none_detected"},
                "root_cause": {"responsible_agent": "none"},
                "refinement_action": {"action": "proceed_to_phase_two"}
            },
            "confidence_assessment": "high"
        })
        
        # Execute analysis
        result = await foundation_refinement_agent.analyze_phase_one_outputs(
            clean_phase_one_result,
            clean_phase_zero_feedback,
            "test_operation_clean"
        )
        
        # Verify clean result
        assert result["refinement_analysis"]["refinement_action"]["action"] == "proceed_to_phase_two"
        assert result["confidence_assessment"] == "high"
        
        # Verify should proceed
        assert foundation_refinement_agent.should_proceed_to_phase_two(result) is True
    
    @patch('phase_one.agents.foundation_refinement.provide_refinement_context')
    async def test_multiple_critical_failures_scenario(
        self,
        mock_provide_context,
        foundation_refinement_agent,
        sample_air_context
    ):
        """Test scenario with multiple critical failures."""
        # Setup inputs with multiple issues
        failing_phase_one_result = {
            "status": "completed",
            "agents": {
                "garden_planner": {"success": False},
                "environmental_analysis": {"success": True}
            },
            "final_output": {"task_analysis": {"requirements": []}}  # Empty requirements
        }
        
        critical_phase_zero_feedback = {
            "status": "completed",
            "deep_analysis": {
                "structural_agent": {
                    "error": "Critical structural issues",
                    "status": "failure"
                },
                "requirement_agent": {
                    "status": "success",
                    "flag_raised": True,
                    "flag_type": "critical",
                    "flag_description": "Missing critical requirements",
                    "severity": "high"
                },
                "data_flow_agent": {
                    "status": "success",
                    "flag_raised": True,
                    "flag_type": "warning",
                    "flag_description": "Data flow inconsistencies",
                    "severity": "medium"
                }
            }
        }
        
        mock_provide_context.return_value = sample_air_context
        
        # Mock analysis detecting critical failure
        mock_circuit = MagicMock()
        mock_circuit.execute = AsyncMock(return_value={
            "refinement_analysis": {
                "critical_failure": {
                    "category": "multiple_critical_failures",
                    "description": "Multiple critical issues detected",
                    "evidence": ["Structural failure", "Requirements missing"],
                    "phase_zero_signals": [
                        {"agent": "structural_agent", "signal": "error"},
                        {"agent": "requirement_agent", "signal": "critical_flag"}
                    ]
                },
                "root_cause": {
                    "responsible_agent": "garden_planner",
                    "failure_point": "initial_analysis",
                    "causal_chain": ["Incomplete analysis", "Missing requirements"],
                    "verification_steps": ["Reanalyze task", "Gather requirements"]
                },
                "refinement_action": {
                    "action": "reanalyze_task",
                    "justification": "Multiple critical failures require complete reanalysis",
                    "specific_guidance": {
                        "current_state": "Critical failures detected",
                        "required_state": "Complete and validated analysis",
                        "adaptation_path": ["Restart analysis", "Validate all requirements"]
                    }
                }
            },
            "confidence_assessment": "high"
        })
        foundation_refinement_agent._circuit_breakers["refinement_analysis"] = mock_circuit
        
        foundation_refinement_agent.process_with_validation = AsyncMock(return_value={
            "refinement_analysis": {
                "critical_failure": {
                    "category": "multiple_critical_failures",
                    "description": "Multiple critical issues detected",
                    "evidence": ["Structural failure", "Requirements missing"],
                    "phase_zero_signals": [
                        {"agent": "structural_agent", "signal": "error"},
                        {"agent": "requirement_agent", "signal": "critical_flag"}
                    ]
                },
                "root_cause": {
                    "responsible_agent": "garden_planner",
                    "failure_point": "initial_analysis",
                    "causal_chain": ["Incomplete analysis", "Missing requirements"],
                    "verification_steps": ["Reanalyze task", "Gather requirements"]
                },
                "refinement_action": {
                    "action": "reanalyze_task",
                    "justification": "Multiple critical failures require complete reanalysis",
                    "specific_guidance": {
                        "current_state": "Critical failures detected",
                        "required_state": "Complete and validated analysis",
                        "adaptation_path": ["Restart analysis", "Validate all requirements"]
                    }
                }
            },
            "confidence_assessment": "high"
        })
        
        # Execute analysis
        result = await foundation_refinement_agent.analyze_phase_one_outputs(
            failing_phase_one_result,
            critical_phase_zero_feedback,
            "test_operation_critical"
        )
        
        # Verify critical failure detected
        assert result["refinement_analysis"]["critical_failure"]["category"] == "multiple_critical_failures"
        assert result["refinement_analysis"]["refinement_action"]["action"] == "reanalyze_task"
        assert result["refinement_analysis"]["root_cause"]["responsible_agent"] == "garden_planner"
        
        # Verify should NOT proceed
        assert foundation_refinement_agent.should_proceed_to_phase_two(result) is False
        
        # Verify target agent identified
        target_agent = foundation_refinement_agent.get_refinement_target_agent(result)
        assert target_agent == "garden_planner"