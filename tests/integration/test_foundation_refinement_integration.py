"""
Integration tests for Foundation Refinement workflow

Tests the complete Phase Zero → Foundation Refinement → Recursion flow
with real component integration and end-to-end scenarios.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from phase_one.orchestrator import PhaseOneOrchestrator
from phase_one.agents.foundation_refinement import FoundationRefinementAgent
from phase_zero import PhaseZeroOrchestrator
from resources import (
    EventQueue, StateManager, AgentContextManager, CacheManager,
    MetricsManager, ErrorHandler, MemoryMonitor, HealthTracker,
    SystemMonitor
)


@pytest.fixture
def mock_resources():
    """Create mock resource managers for integration testing."""
    resources = {
        'event_queue': AsyncMock(spec=EventQueue),
        'state_manager': AsyncMock(spec=StateManager),
        'context_manager': AsyncMock(spec=AgentContextManager),
        'cache_manager': AsyncMock(spec=CacheManager),
        'metrics_manager': AsyncMock(spec=MetricsManager),
        'error_handler': AsyncMock(spec=ErrorHandler),
        'memory_monitor': AsyncMock(spec=MemoryMonitor),
        'health_tracker': AsyncMock(spec=HealthTracker),
        'system_monitor': AsyncMock(spec=SystemMonitor)
    }
    
    # Configure state manager to return None for missing states
    resources['state_manager'].get_state.return_value = None
    # Configure additional methods that may be called
    resources['state_manager'].get_states_by_pattern = AsyncMock(return_value=[])
    
    return resources


@pytest.fixture
def integration_test_scenario():
    """Create a comprehensive test scenario with realistic data."""
    return {
        "user_request": "Create a comprehensive task management system with user authentication, project tracking, and real-time collaboration features",
        "operation_id": "integration_test_001",
        "phase_one_result": {
            "status": "completed",
            "agents": {
                "garden_planner": {
                    "success": True,
                    "output": {
                        "task_analysis": {
                            "primary_requirements": [
                                "User authentication system",
                                "Project management capabilities", 
                                "Real-time collaboration",
                                "Data persistence"
                            ],
                            "complexity_assessment": "high",
                            "estimated_components": 8
                        }
                    }
                },
                "environmental_analysis": {
                    "success": True,
                    "output": {
                        "environmental_constraints": [
                            "Must support 1000+ concurrent users",
                            "Real-time updates required",
                            "Multi-platform compatibility"
                        ],
                        "performance_requirements": {
                            "response_time": "< 200ms",
                            "availability": "99.9%"
                        }
                    }
                },
                "root_system_architect": {
                    "success": True,
                    "output": {
                        "data_architecture": {
                            "primary_flows": [
                                "Authentication flow",
                                "Project data flow", 
                                "Real-time notification flow",
                                "Collaboration event flow"
                            ],
                            "data_stores": ["User DB", "Project DB", "Event Store"],
                            "apis": ["Auth API", "Project API", "Collaboration API"]
                        }
                    }
                },
                "tree_placement_planner": {
                    "success": True,
                    "output": {
                        "component_architecture": {
                            "components": [
                                {
                                    "name": "AuthenticationService",
                                    "type": "core",
                                    "dependencies": ["UserDatabase"],
                                    "responsibilities": ["User login", "Token management"]
                                },
                                {
                                    "name": "ProjectManager",
                                    "type": "core", 
                                    "dependencies": ["ProjectDatabase", "AuthenticationService"],
                                    "responsibilities": ["Project CRUD", "Permission management"]
                                },
                                {
                                    "name": "CollaborationEngine",
                                    "type": "feature",
                                    "dependencies": ["EventStore", "ProjectManager"],
                                    "responsibilities": ["Real-time updates", "Conflict resolution"]
                                },
                                {
                                    "name": "NotificationService",
                                    "type": "utility",
                                    "dependencies": ["EventStore"],
                                    "responsibilities": ["Push notifications", "Email alerts"]
                                }
                            ]
                        }
                    }
                }
            },
            "final_output": {
                "task_analysis": {
                    "primary_requirements": [
                        "User authentication system",
                        "Project management capabilities", 
                        "Real-time collaboration",
                        "Data persistence"
                    ],
                    "complexity_assessment": "high",
                    "estimated_components": 8
                },
                "environmental_analysis": {
                    "environmental_constraints": [
                        "Must support 1000+ concurrent users",
                        "Real-time updates required",
                        "Multi-platform compatibility"
                    ],
                    "performance_requirements": {
                        "response_time": "< 200ms",
                        "availability": "99.9%"
                    }
                },
                "data_architecture": {
                    "primary_flows": [
                        "Authentication flow",
                        "Project data flow", 
                        "Real-time notification flow",
                        "Collaboration event flow"
                    ],
                    "data_stores": ["User DB", "Project DB", "Event Store"],
                    "apis": ["Auth API", "Project API", "Collaboration API"]
                },
                "component_architecture": {
                    "components": [
                        {
                            "name": "AuthenticationService",
                            "type": "core",
                            "dependencies": ["UserDatabase"],
                            "responsibilities": ["User login", "Token management"]
                        },
                        {
                            "name": "ProjectManager",
                            "type": "core", 
                            "dependencies": ["ProjectDatabase", "AuthenticationService"],
                            "responsibilities": ["Project CRUD", "Permission management"]
                        },
                        {
                            "name": "CollaborationEngine",
                            "type": "feature",
                            "dependencies": ["EventStore", "ProjectManager"],
                            "responsibilities": ["Real-time updates", "Conflict resolution"]
                        },
                        {
                            "name": "NotificationService",
                            "type": "utility",
                            "dependencies": ["EventStore"],
                            "responsibilities": ["Push notifications", "Email alerts"]
                        }
                    ]
                }
            }
        }
    }


@pytest.fixture
def phase_zero_scenarios():
    """Create different Phase Zero feedback scenarios."""
    return {
        "no_issues": {
            "status": "completed",
            "monitoring_analysis": {
                "system_health": "excellent",
                "resource_utilization": "normal",
                "performance_metrics": "within_bounds"
            },
            "deep_analysis": {
                "structural_agent": {
                    "status": "success",
                    "flag_raised": False,
                    "analysis": "Component structure is well-designed"
                },
                "requirement_agent": {
                    "status": "success", 
                    "flag_raised": False,
                    "analysis": "Requirements are comprehensive and clear"
                },
                "data_flow_agent": {
                    "status": "success",
                    "flag_raised": False,
                    "analysis": "Data flows are properly defined"
                },
                "optimization_agent": {
                    "status": "success",
                    "flag_raised": False,
                    "analysis": "Architecture is optimized for requirements"
                }
            },
            "evolution_synthesis": {
                "overall_assessment": "excellent",
                "recommendations": ["Proceed to Phase Two"],
                "optimization_suggestions": []
            }
        },
        
        "critical_dependency_issue": {
            "status": "completed",
            "monitoring_analysis": {
                "system_health": "degraded",
                "resource_utilization": "high",
                "performance_metrics": "concerning"
            },
            "deep_analysis": {
                "structural_agent": {
                    "status": "success",
                    "flag_raised": True,
                    "flag_type": "critical",
                    "flag_description": "Circular dependency detected between ProjectManager and CollaborationEngine",
                    "severity": "high",
                    "analysis": "Critical architectural flaw that will prevent proper implementation"
                },
                "requirement_agent": {
                    "status": "success",
                    "flag_raised": False,
                    "analysis": "Requirements are adequate"
                },
                "data_flow_agent": {
                    "status": "success",
                    "flag_raised": True,
                    "flag_type": "warning",
                    "flag_description": "Missing error handling in collaboration flow",
                    "severity": "medium",
                    "analysis": "Data flow lacks proper error handling mechanisms"
                },
                "optimization_agent": {
                    "status": "success",
                    "flag_raised": False,
                    "analysis": "Performance optimization opportunities exist"
                }
            },
            "evolution_synthesis": {
                "overall_assessment": "critical_issues_detected",
                "recommendations": [
                    "Restructure component dependencies",
                    "Add error handling to data flows",
                    "Review architectural patterns"
                ],
                "optimization_suggestions": [
                    "Consider event-driven architecture for collaboration",
                    "Implement dependency injection for better decoupling"
                ]
            }
        },
        
        "requirements_gap": {
            "status": "completed",
            "monitoring_analysis": {
                "system_health": "good",
                "resource_utilization": "normal",
                "performance_metrics": "acceptable"
            },
            "deep_analysis": {
                "structural_agent": {
                    "status": "success",
                    "flag_raised": False,
                    "analysis": "Component structure is reasonable"
                },
                "requirement_agent": {
                    "status": "success",
                    "flag_raised": True,
                    "flag_type": "critical",
                    "flag_description": "Missing security requirements and audit trail specifications",
                    "severity": "high",
                    "analysis": "Critical business requirements are missing from the analysis"
                },
                "data_flow_agent": {
                    "status": "success",
                    "flag_raised": False,
                    "analysis": "Data flows are adequately defined"
                },
                "optimization_agent": {
                    "status": "success",
                    "flag_raised": True,
                    "flag_type": "warning", 
                    "flag_description": "Performance concerns with real-time collaboration scale",
                    "severity": "medium",
                    "analysis": "Current architecture may not scale to 1000+ concurrent users"
                }
            },
            "evolution_synthesis": {
                "overall_assessment": "requirements_incomplete",
                "recommendations": [
                    "Re-analyze task with security focus",
                    "Add audit trail requirements",
                    "Consider scalability implications"
                ],
                "optimization_suggestions": [
                    "Implement microservices architecture",
                    "Add caching layers",
                    "Consider event sourcing for audit trails"
                ]
            }
        }
    }


async def create_integrated_orchestrator(mock_resources, phase_zero_scenario=None):
    """Create a real orchestrator with mocked dependencies for integration testing."""
    
    # Create real Foundation Refinement Agent
    foundation_refinement_agent = FoundationRefinementAgent(
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
    
    # Mock the LLM processing for deterministic testing
    foundation_refinement_agent.process_with_validation = AsyncMock()
    foundation_refinement_agent._initialized = True
    
    # Create mock Phase Zero if scenario provided
    phase_zero = None
    if phase_zero_scenario:
        phase_zero = AsyncMock(spec=PhaseZeroOrchestrator)
        phase_zero.process_system_metrics = AsyncMock(return_value=phase_zero_scenario)
    
    # Create orchestrator with real and mock components
    orchestrator = PhaseOneOrchestrator(
        event_queue=mock_resources['event_queue'],
        state_manager=mock_resources['state_manager'],
        context_manager=mock_resources['context_manager'],
        cache_manager=mock_resources['cache_manager'],
        metrics_manager=mock_resources['metrics_manager'],
        error_handler=mock_resources['error_handler'],
        health_tracker=mock_resources['health_tracker'],
        memory_monitor=mock_resources['memory_monitor'],
        system_monitor=mock_resources['system_monitor'],
        phase_zero=phase_zero,
        foundation_refinement_agent=foundation_refinement_agent,
        max_refinement_cycles=3
    )
    
    # Mock the workflow execution
    orchestrator.phase_one_workflow = AsyncMock()
    
    return orchestrator, foundation_refinement_agent


class TestEndToEndRefinementWorkflow:
    """Test complete end-to-end refinement workflows."""
    
    @pytest.mark.asyncio
    @patch('phase_one.agents.foundation_refinement.provide_refinement_context')
    async def test_successful_workflow_no_refinement_needed(
        self,
        mock_air_context,
        mock_resources,
        integration_test_scenario,
        phase_zero_scenarios
    ):
        """Test complete workflow when no refinement is needed."""
        
        # Setup Air Agent context
        mock_air_context.return_value = {
            "historical_patterns": [],
            "success_strategies": ["dependency_validation"],
            "failure_patterns": [],
            "recommendations": ["Architecture looks solid"]
        }
        
        # Create orchestrator with clean Phase Zero feedback
        orchestrator, foundation_agent = await create_integrated_orchestrator(
            mock_resources,
            phase_zero_scenarios["no_issues"]
        )
        
        # Setup workflow to return test scenario
        orchestrator.phase_one_workflow.execute_phase_one.return_value = integration_test_scenario["phase_one_result"]
        
        # Configure Foundation Refinement Agent to proceed
        foundation_agent.process_with_validation.return_value = {
            "refinement_analysis": {
                "critical_failure": {
                    "category": "none_detected",
                    "description": "No critical failures detected - architecture is sound",
                    "evidence": [],
                    "phase_zero_signals": []
                },
                "root_cause": {
                    "responsible_agent": "none",
                    "failure_point": "no_failure_detected",
                    "causal_chain": [],
                    "verification_steps": []
                },
                "refinement_action": {
                    "action": "proceed_to_phase_two",
                    "justification": "All Phase Zero agents report success, architecture is well-designed",
                    "specific_guidance": {
                        "current_state": "Phase One completed successfully",
                        "required_state": "Ready for Phase Two implementation",
                        "adaptation_path": ["Begin component implementation"]
                    }
                }
            },
            "confidence_assessment": "high"
        }
        
        # Execute process task
        result = await orchestrator._process_task_internal(
            integration_test_scenario["user_request"],
            integration_test_scenario["operation_id"]
        )
        
        # Verify successful completion
        assert result["status"] == "success"
        assert "refinement_analysis" in result
        assert result["refinement_analysis"]["refinement_analysis"]["refinement_action"]["action"] == "proceed_to_phase_two"
        assert result["refinement_analysis"]["confidence_assessment"] == "high"
        
        # Verify Phase Zero was called
        orchestrator._phase_zero.process_system_metrics.assert_called_once()
        
        # Verify Foundation Refinement Agent processed correctly
        foundation_agent.process_with_validation.assert_called_once()
        
        # Verify Air Agent context was requested
        mock_air_context.assert_called_once()
    
    @patch('phase_one.agents.foundation_refinement.provide_refinement_context')
    @patch('phase_one.orchestrator.track_decision_event')
    async def test_critical_dependency_issue_refinement_cycle(
        self,
        mock_track_decision,
        mock_air_context,
        mock_resources,
        integration_test_scenario,
        phase_zero_scenarios
    ):
        """Test workflow when critical dependency issues are detected."""
        
        # Setup Air Agent context with relevant historical data
        mock_air_context.return_value = {
            "historical_patterns": [
                {"pattern": "circular_dependency", "frequency": 2, "success_rate": 0.3}
            ],
            "success_strategies": [
                {"strategy": "dependency_injection", "success_rate": 0.9},
                {"strategy": "event_driven_architecture", "success_rate": 0.85}
            ],
            "failure_patterns": [
                {"pattern": "tight_coupling", "frequency": 3}
            ],
            "recommendations": [
                "Consider implementing dependency injection",
                "Review component boundaries for better separation"
            ]
        }
        
        # Create orchestrator with critical Phase Zero feedback
        orchestrator, foundation_agent = await create_integrated_orchestrator(
            mock_resources,
            phase_zero_scenarios["critical_dependency_issue"]
        )
        
        # Setup workflow to return test scenario
        orchestrator.phase_one_workflow.execute_phase_one.return_value = integration_test_scenario["phase_one_result"]
        
        # Configure Foundation Refinement Agent to detect critical failure
        foundation_agent.process_with_validation.return_value = {
            "refinement_analysis": {
                "critical_failure": {
                    "category": "architectural_dependency_failure",
                    "description": "Critical circular dependency detected that will prevent proper implementation",
                    "evidence": [
                        "Phase Zero structural agent flagged circular dependency",
                        "ProjectManager and CollaborationEngine have mutual dependencies",
                        "Data flow agent identified missing error handling"
                    ],
                    "phase_zero_signals": [
                        {
                            "agent": "structural_agent",
                            "signal_type": "critical",
                            "severity": "high",
                            "description": "Circular dependency detected"
                        },
                        {
                            "agent": "data_flow_agent", 
                            "signal_type": "warning",
                            "severity": "medium",
                            "description": "Missing error handling"
                        }
                    ]
                },
                "root_cause": {
                    "responsible_agent": "tree_placement_planner",
                    "failure_point": "component_dependency_mapping",
                    "causal_chain": [
                        "Tree placement planner created mutual dependencies",
                        "Failed to consider dependency direction during component design",
                        "Missing dependency validation during architecture phase"
                    ],
                    "verification_steps": [
                        "Review component dependency graph",
                        "Implement dependency injection pattern",
                        "Add architectural validation rules"
                    ]
                },
                "refinement_action": {
                    "action": "reorganize_components",
                    "justification": "Critical architectural flaws require component restructuring to ensure successful implementation",
                    "specific_guidance": {
                        "current_state": "Components have circular dependencies that will prevent implementation",
                        "required_state": "Clean component architecture with unidirectional dependencies",
                        "adaptation_path": [
                            "Break circular dependency between ProjectManager and CollaborationEngine",
                            "Implement event-driven communication pattern",
                            "Add dependency injection for loose coupling",
                            "Validate architectural constraints"
                        ]
                    }
                }
            },
            "confidence_assessment": "high"
        }
        
        # Execute process task
        result = await orchestrator._process_task_internal(
            integration_test_scenario["user_request"],
            integration_test_scenario["operation_id"]
        )
        
        # Verify refinement cycle was initiated
        assert result["status"] == "success"
        assert "refinement_analysis" in result
        assert result["refinement_analysis"]["status"] == "refinement_attempted"
        assert result["refinement_analysis"]["target_agent"] == "tree_placement_planner"
        assert result["refinement_analysis"]["guidance"]["action"] == "reorganize_components"
        
        # Verify Air Agent decision tracking
        mock_track_decision.assert_called_once()
        
        # Verify proper guidance was provided
        guidance = result["refinement_analysis"]["guidance"]
        assert "adaptation_path" in guidance
        assert "Break circular dependency" in guidance["adaptation_path"][0]
        
        # Verify cycle was incremented
        assert foundation_agent._current_cycle == 1
    
    @patch('phase_one.agents.foundation_refinement.provide_refinement_context')
    async def test_requirements_gap_refinement_cycle(
        self,
        mock_air_context,
        mock_resources,
        integration_test_scenario,
        phase_zero_scenarios
    ):
        """Test workflow when requirements gaps are detected."""
        
        # Setup Air Agent context
        mock_air_context.return_value = {
            "historical_patterns": [
                {"pattern": "missing_security_requirements", "frequency": 4, "success_rate": 0.2}
            ],
            "success_strategies": [
                {"strategy": "comprehensive_requirements_analysis", "success_rate": 0.95},
                {"strategy": "security_first_design", "success_rate": 0.88}
            ],
            "failure_patterns": [
                {"pattern": "incomplete_requirements", "frequency": 5}
            ],
            "recommendations": [
                "Conduct thorough security requirements analysis",
                "Consider compliance and audit requirements early"
            ]
        }
        
        # Create orchestrator with requirements gap feedback
        orchestrator, foundation_agent = await create_integrated_orchestrator(
            mock_resources,
            phase_zero_scenarios["requirements_gap"]
        )
        
        # Setup workflow to return test scenario
        orchestrator.phase_one_workflow.execute_phase_one.return_value = integration_test_scenario["phase_one_result"]
        
        # Configure Foundation Refinement Agent to detect requirements gap
        foundation_agent.process_with_validation.return_value = {
            "refinement_analysis": {
                "critical_failure": {
                    "category": "requirements_completeness_failure",
                    "description": "Critical business and security requirements missing from analysis",
                    "evidence": [
                        "Phase Zero requirement agent flagged missing security requirements",
                        "No audit trail specifications identified",
                        "Scalability concerns not addressed in requirements"
                    ],
                    "phase_zero_signals": [
                        {
                            "agent": "requirement_agent",
                            "signal_type": "critical",
                            "severity": "high",
                            "description": "Missing security requirements and audit trail specifications"
                        },
                        {
                            "agent": "optimization_agent",
                            "signal_type": "warning",
                            "severity": "medium", 
                            "description": "Performance concerns with real-time collaboration scale"
                        }
                    ]
                },
                "root_cause": {
                    "responsible_agent": "garden_planner",
                    "failure_point": "requirements_analysis",
                    "causal_chain": [
                        "Garden planner focused on functional requirements only",
                        "Failed to identify security and compliance requirements",
                        "Did not consider audit trail and governance needs",
                        "Incomplete stakeholder analysis"
                    ],
                    "verification_steps": [
                        "Conduct comprehensive requirements gathering",
                        "Include security and compliance stakeholders",
                        "Define audit trail requirements",
                        "Validate scalability requirements"
                    ]
                },
                "refinement_action": {
                    "action": "reanalyze_task",
                    "justification": "Critical requirements gaps will lead to implementation failures and compliance issues",
                    "specific_guidance": {
                        "current_state": "Requirements analysis incomplete, missing critical business requirements",
                        "required_state": "Comprehensive requirements including security, audit, and scalability specifications",
                        "adaptation_path": [
                            "Re-analyze task with security and compliance focus",
                            "Identify all stakeholders including security team",
                            "Define audit trail and logging requirements",
                            "Specify performance and scalability requirements",
                            "Validate requirements completeness"
                        ]
                    }
                }
            },
            "confidence_assessment": "high"
        }
        
        # Execute process task
        result = await orchestrator._process_task_internal(
            integration_test_scenario["user_request"],
            integration_test_scenario["operation_id"]
        )
        
        # Verify refinement cycle was initiated for garden planner
        assert result["status"] == "success"
        assert result["refinement_analysis"]["status"] == "refinement_attempted"
        assert result["refinement_analysis"]["target_agent"] == "garden_planner"
        assert result["refinement_analysis"]["guidance"]["action"] == "reanalyze_task"
        
        # Verify comprehensive guidance provided
        guidance = result["refinement_analysis"]["guidance"]
        adaptation_path = guidance["adaptation_path"]
        assert any("security and compliance" in step for step in adaptation_path)
        assert any("audit trail" in step for step in adaptation_path)
    
    async def test_maximum_refinement_cycles_reached(
        self,
        mock_resources,
        integration_test_scenario,
        phase_zero_scenarios
    ):
        """Test workflow when maximum refinement cycles are reached."""
        
        # Create orchestrator with critical feedback
        orchestrator, foundation_agent = await create_integrated_orchestrator(
            mock_resources,
            phase_zero_scenarios["critical_dependency_issue"]
        )
        
        # Setup workflow to return test scenario
        orchestrator.phase_one_workflow.execute_phase_one.return_value = integration_test_scenario["phase_one_result"]
        
        # Set agent to maximum cycles
        foundation_agent._current_cycle = foundation_agent._max_refinement_cycles
        
        # Configure agent to normally require refinement
        foundation_agent.process_with_validation.return_value = {
            "refinement_analysis": {
                "critical_failure": {"category": "dependency_failure"},
                "root_cause": {"responsible_agent": "tree_placement_planner"},
                "refinement_action": {"action": "reorganize_components"}
            },
            "confidence_assessment": "high"
        }
        
        # Execute process task
        result = await orchestrator._process_task_internal(
            integration_test_scenario["user_request"],
            integration_test_scenario["operation_id"]
        )
        
        # Verify system proceeds despite needing refinement
        assert result["status"] == "success"
        # Should have refinement analysis but not attempt another cycle
        assert "refinement_analysis" in result
        # The should_proceed_to_phase_two logic should return True due to max cycles
        assert foundation_agent.should_proceed_to_phase_two(result["refinement_analysis"]) is True


class TestErrorRecoveryAndRobustness:
    """Test error recovery scenarios in integrated workflows."""
    
    @patch('phase_one.agents.foundation_refinement.provide_refinement_context')
    async def test_phase_zero_failure_graceful_recovery(
        self,
        mock_air_context,
        mock_resources,
        integration_test_scenario
    ):
        """Test graceful recovery when Phase Zero fails completely."""
        
        # Setup Air Agent context
        mock_air_context.return_value = {
            "historical_patterns": [],
            "success_strategies": [],
            "failure_patterns": [],
            "recommendations": ["No historical context available"]
        }
        
        # Create orchestrator with failing Phase Zero
        phase_zero_mock = AsyncMock(spec=PhaseZeroOrchestrator)
        phase_zero_mock.process_system_metrics.side_effect = Exception("Phase Zero system failure")
        
        orchestrator, foundation_agent = await create_integrated_orchestrator(mock_resources)
        orchestrator._phase_zero = phase_zero_mock
        
        # Setup workflow to return test scenario
        orchestrator.phase_one_workflow.execute_phase_one.return_value = integration_test_scenario["phase_one_result"]
        
        # Configure Foundation Refinement Agent to handle missing Phase Zero feedback
        foundation_agent.process_with_validation.return_value = {
            "refinement_analysis": {
                "critical_failure": {"category": "none_detected"},
                "root_cause": {"responsible_agent": "none"},
                "refinement_action": {"action": "proceed_to_phase_two"}
            },
            "confidence_assessment": "medium"
        }
        
        # Execute process task
        result = await orchestrator._process_task_internal(
            integration_test_scenario["user_request"],
            integration_test_scenario["operation_id"]
        )
        
        # Verify graceful recovery
        assert result["status"] == "success"
        assert "refinement_analysis" in result
        
        # Verify Foundation Refinement Agent was called with error feedback
        foundation_agent.process_with_validation.assert_called_once()
    
    @patch('phase_one.agents.foundation_refinement.provide_refinement_context')
    async def test_air_agent_failure_workflow_continuation(
        self,
        mock_air_context,
        mock_resources,
        integration_test_scenario,
        phase_zero_scenarios
    ):
        """Test workflow continuation when Air Agent fails."""
        
        # Make Air Agent fail
        mock_air_context.side_effect = Exception("Air Agent connection error")
        
        # Create orchestrator with good Phase Zero feedback
        orchestrator, foundation_agent = await create_integrated_orchestrator(
            mock_resources,
            phase_zero_scenarios["no_issues"]
        )
        
        # Setup workflow to return test scenario
        orchestrator.phase_one_workflow.execute_phase_one.return_value = integration_test_scenario["phase_one_result"]
        
        # Configure Foundation Refinement Agent to proceed
        foundation_agent.process_with_validation.return_value = {
            "refinement_analysis": {
                "critical_failure": {"category": "none_detected"},
                "root_cause": {"responsible_agent": "none"},
                "refinement_action": {"action": "proceed_to_phase_two"}
            },
            "confidence_assessment": "medium"
        }
        
        # Execute process task
        result = await orchestrator._process_task_internal(
            integration_test_scenario["user_request"],
            integration_test_scenario["operation_id"]
        )
        
        # Verify workflow continues despite Air Agent failure
        assert result["status"] == "success"
        assert "refinement_analysis" in result
        
        # Verify Air Agent failure was handled gracefully
        mock_air_context.assert_called_once()


class TestStateManagementAndPersistence:
    """Test state management during integrated workflows."""
    
    @patch('phase_one.agents.foundation_refinement.provide_refinement_context')
    async def test_comprehensive_state_storage(
        self,
        mock_air_context,
        mock_resources,
        integration_test_scenario,
        phase_zero_scenarios
    ):
        """Test that all workflow state is properly stored."""
        
        # Setup mocks
        mock_air_context.return_value = {"recommendations": ["test"]}
        
        # Create orchestrator
        orchestrator, foundation_agent = await create_integrated_orchestrator(
            mock_resources,
            phase_zero_scenarios["critical_dependency_issue"]
        )
        
        # Setup workflow
        orchestrator.phase_one_workflow.execute_phase_one.return_value = integration_test_scenario["phase_one_result"]
        
        # Configure Foundation Refinement Agent
        foundation_agent.process_with_validation.return_value = {
            "refinement_analysis": {
                "critical_failure": {"category": "dependency_failure"},
                "root_cause": {"responsible_agent": "tree_placement_planner"},
                "refinement_action": {"action": "reorganize_components"}
            },
            "confidence_assessment": "high"
        }
        
        # Execute process task
        await orchestrator._process_task_internal(
            integration_test_scenario["user_request"],
            integration_test_scenario["operation_id"]
        )
        
        # Verify comprehensive state storage
        state_calls = mock_resources['state_manager'].set_state.call_args_list
        stored_keys = [call[0][0] for call in state_calls]
        
        # Should store Phase Zero feedback, refinement analysis, and workflow results
        assert any("phase_zero_feedback" in key for key in stored_keys)
        assert any("refinement_analysis" in key for key in stored_keys)
        assert any("refinement_workflow" in key for key in stored_keys)
        
        # Verify operation tracking
        assert any(integration_test_scenario["operation_id"] in key for key in stored_keys)
    
    async def test_metrics_and_monitoring_integration(
        self,
        mock_resources,
        integration_test_scenario,
        phase_zero_scenarios
    ):
        """Test metrics collection and monitoring during workflow."""
        
        # Create orchestrator
        orchestrator, foundation_agent = await create_integrated_orchestrator(
            mock_resources,
            phase_zero_scenarios["no_issues"]
        )
        
        # Setup workflow
        orchestrator.phase_one_workflow.execute_phase_one.return_value = integration_test_scenario["phase_one_result"]
        
        # Configure Foundation Refinement Agent
        foundation_agent.process_with_validation.return_value = {
            "refinement_analysis": {
                "critical_failure": {"category": "none_detected"},
                "root_cause": {"responsible_agent": "none"},
                "refinement_action": {"action": "proceed_to_phase_two"}
            },
            "confidence_assessment": "high"
        }
        
        # Execute process task
        await orchestrator.process_task(
            integration_test_scenario["user_request"],
            integration_test_scenario["operation_id"]
        )
        
        # Verify metrics were recorded
        mock_resources['metrics_manager'].record_metric.assert_called()
        
        # Verify health tracking
        mock_resources['health_tracker'].update_health.assert_called()
        
        # Verify event emission
        mock_resources['event_queue'].emit.assert_called()