"""
Unit tests for Evolution Agent

Tests the Phase Zero Evolution Agent responsible for synthesis of all Phase Zero
analysis feedback into strategic adaptations and coordinated improvement strategies.
This agent performs the critical synthesis function that consolidates dual-perspective
analyses from all specialized Phase Zero agents.
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from phase_zero.agents.synthesis import EvolutionAgent
from phase_zero.prompt_loader import AgentType, PromptType
from interface import AgentInterface
from resources.monitoring import MemoryMonitor
from resources import (
    EventQueue, StateManager, AgentContextManager, CacheManager,
    MetricsManager, ErrorHandler, HealthTracker
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
def sample_phase_zero_analysis():
    """Sample Phase Zero analysis results for synthesis."""
    return {
        "sun_agent_analysis": {
            "dual_perspective_analysis": {
                "issue_analysis": {
                    "scope_issues": [
                        {"issue": "Project scope too broad", "severity": "high", "impact": "timeline"},
                        {"issue": "Unclear deliverables", "severity": "medium", "impact": "quality"}
                    ],
                    "clarity_issues": [
                        {"issue": "Requirements ambiguous", "severity": "high", "impact": "development"}
                    ]
                },
                "gap_analysis": {
                    "scope_gaps": [
                        {"gap": "Missing user stories", "priority": "high", "area": "requirements"},
                        {"gap": "No acceptance criteria", "priority": "medium", "area": "testing"}
                    ]
                },
                "synthesis": {
                    "key_observations": ["Scope needs refinement", "Requirements clarity critical"],
                    "prioritized_recommendations": [
                        {"priority": "high", "action": "Define clear user stories"},
                        {"priority": "medium", "action": "Establish acceptance criteria"}
                    ]
                }
            }
        },
        "shade_agent_analysis": {
            "dual_perspective_conflicts": {
                "task_vs_guidelines": {
                    "scope_conflicts": [
                        {"conflict": "Timeline vs scope mismatch", "severity": "high", "area": "planning"}
                    ],
                    "stakeholder_conflicts": [
                        {"conflict": "User needs vs business goals", "severity": "medium", "area": "alignment"}
                    ]
                },
                "synthesis": {
                    "key_patterns": ["Resource allocation conflicts", "Timeline pressures"],
                    "prioritized_resolutions": [
                        {"priority": "high", "resolution": "Adjust scope or extend timeline"}
                    ]
                }
            }
        },
        "soil_agent_analysis": {
            "requirement_assessment": {
                "completeness_analysis": {
                    "missing_requirements": ["Security requirements", "Performance benchmarks"],
                    "incomplete_requirements": ["User authentication details"]
                },
                "quality_analysis": {
                    "clarity_issues": ["Vague performance targets"],
                    "consistency_issues": ["Conflicting user interface requirements"]
                }
            }
        },
        "microbial_agent_analysis": {
            "issue_detection": {
                "critical_issues": [
                    {"issue": "No security framework defined", "severity": "critical", "area": "security"}
                ],
                "warning_issues": [
                    {"issue": "Performance targets unrealistic", "severity": "warning", "area": "performance"}
                ]
            }
        },
        "mycelial_agent_analysis": {
            "data_flow_assessment": {
                "flow_gaps": ["Missing error handling flows", "Incomplete data validation"],
                "consistency_issues": ["Data format mismatches between services"]
            }
        },
        "worm_agent_analysis": {
            "gap_identification": {
                "architectural_gaps": ["No monitoring strategy", "Missing backup procedures"],
                "process_gaps": ["No deployment pipeline", "Missing rollback procedures"]
            }
        },
        "bird_agent_analysis": {
            "structural_analysis": {
                "component_issues": ["Tight coupling between services"],
                "dependency_issues": ["Circular dependencies in modules"]
            }
        },
        "tree_agent_analysis": {
            "structural_gaps": {
                "missing_components": ["Logging service", "Configuration management"],
                "incomplete_interfaces": ["API versioning strategy"]
            }
        },
        "pollinator_agent_analysis": {
            "optimization_opportunities": {
                "performance_optimizations": ["Database indexing strategy", "Caching layer"],
                "architectural_improvements": ["Microservices decomposition", "Event-driven architecture"]
            }
        }
    }


@pytest.fixture
def sample_comprehensive_synthesis_result():
    """Sample comprehensive synthesis result from Evolution Agent."""
    return {
        "strategic_adaptations": {
            "common_patterns": [
                {
                    "pattern": "scope_clarity_issues",
                    "frequency": 8,
                    "agents_reporting": ["sun", "shade", "soil"],
                    "severity": "high",
                    "impact_areas": ["timeline", "quality", "development"]
                },
                {
                    "pattern": "architectural_gaps", 
                    "frequency": 5,
                    "agents_reporting": ["worm", "tree", "bird"],
                    "severity": "medium",
                    "impact_areas": ["maintainability", "scalability"]
                }
            ],
            "reinforcing_signals": [
                {
                    "signal": "requirements_clarity_critical",
                    "supporting_agents": ["sun", "soil", "microbial"],
                    "convergence_strength": "strong",
                    "recommended_action": "immediate_requirements_workshop"
                },
                {
                    "signal": "architectural_foundation_weak",
                    "supporting_agents": ["bird", "tree", "worm"],
                    "convergence_strength": "moderate", 
                    "recommended_action": "architectural_review_session"
                }
            ],
            "strategic_adjustments": [
                {
                    "adjustment": "scope_refinement_mandatory",
                    "rationale": "Multiple agents identify scope issues as critical",
                    "expected_impact": "reduced_timeline_risk",
                    "implementation_priority": "immediate"
                },
                {
                    "adjustment": "architecture_foundation_strengthening",
                    "rationale": "Structural gaps threaten long-term maintainability",
                    "expected_impact": "improved_scalability",
                    "implementation_priority": "high"
                }
            ],
            "high_impact_opportunities": [
                {
                    "opportunity": "requirements_driven_development",
                    "potential_benefit": "25% reduction in rework",
                    "implementation_effort": "medium",
                    "success_likelihood": "high"
                },
                {
                    "opportunity": "modular_architecture_adoption",
                    "potential_benefit": "40% improvement in maintainability",
                    "implementation_effort": "high", 
                    "success_likelihood": "medium"
                }
            ],
            "integration_strategies": [
                {
                    "strategy": "phased_scope_clarification",
                    "phases": ["requirements_workshop", "stakeholder_alignment", "scope_validation"],
                    "coordination_requirements": ["product_owner", "development_team", "stakeholders"],
                    "success_metrics": ["requirements_completeness", "stakeholder_agreement"]
                },
                {
                    "strategy": "incremental_architecture_improvement",
                    "phases": ["current_state_assessment", "target_architecture_design", "migration_planning"],
                    "coordination_requirements": ["architects", "developers", "operations"],
                    "success_metrics": ["code_quality", "system_reliability"]
                }
            ],
            "synthesis": {
                "priority_adaptations": [
                    {
                        "adaptation": "immediate_scope_clarification",
                        "justification": "Critical path blocker affecting all development phases",
                        "timeline": "1-2 weeks",
                        "success_criteria": ["documented_requirements", "stakeholder_signoff"]
                    },
                    {
                        "adaptation": "architectural_foundation_establishment",
                        "justification": "Prevents technical debt accumulation",
                        "timeline": "3-4 weeks",
                        "success_criteria": ["architectural_documentation", "design_patterns_established"]
                    }
                ],
                "implementation_strategy": {
                    "approach": "parallel_workstreams",
                    "workstream_1": "requirements_clarification",
                    "workstream_2": "architectural_planning",
                    "synchronization_points": ["weekly_alignment_meetings", "milestone_reviews"],
                    "risk_mitigation": ["regular_stakeholder_communication", "incremental_validation"]
                },
                "success_metrics": [
                    {
                        "metric": "requirements_clarity_score",
                        "target": "95%",
                        "measurement_method": "stakeholder_survey"
                    },
                    {
                        "metric": "architectural_completeness_score", 
                        "target": "90%",
                        "measurement_method": "architecture_review_checklist"
                    }
                ]
            }
        }
    }


@pytest.fixture
async def evolution_agent(mock_resources):
    """Create an Evolution Agent for testing."""
    agent = EvolutionAgent(
        event_queue=mock_resources['event_queue'],
        state_manager=mock_resources['state_manager'],
        context_manager=mock_resources['context_manager'],
        cache_manager=mock_resources['cache_manager'],
        metrics_manager=mock_resources['metrics_manager'],
        error_handler=mock_resources['error_handler'],
        health_tracker=mock_resources['health_tracker'],
        memory_monitor=mock_resources['memory_monitor']
    )
    
    return agent


class TestEvolutionAgentInitialization:
    """Test Evolution Agent initialization."""
    
    async def test_initialization_success(self, mock_resources):
        """Test successful Evolution Agent initialization."""
        agent = EvolutionAgent(
            event_queue=mock_resources['event_queue'],
            state_manager=mock_resources['state_manager'],
            context_manager=mock_resources['context_manager'],
            cache_manager=mock_resources['cache_manager'],
            metrics_manager=mock_resources['metrics_manager'],
            error_handler=mock_resources['error_handler'],
            health_tracker=mock_resources['health_tracker'],
            memory_monitor=mock_resources['memory_monitor']
        )
        
        # Verify initialization
        assert agent.interface_id == "agent:evolution_agent"
        assert agent._current_prompt_type == PromptType.PHASE_ONE_INITIAL
        assert isinstance(agent, AgentInterface)
        
        # Verify monitoring integration
        assert agent._health_tracker == mock_resources['health_tracker']
        assert agent._memory_monitor == mock_resources['memory_monitor']
    
    async def test_initialization_without_optional_components(self, mock_resources):
        """Test initialization without optional monitoring components."""
        agent = EvolutionAgent(
            event_queue=mock_resources['event_queue'],
            state_manager=mock_resources['state_manager'],
            context_manager=mock_resources['context_manager'],
            cache_manager=mock_resources['cache_manager'],
            metrics_manager=mock_resources['metrics_manager'],
            error_handler=mock_resources['error_handler']
        )
        
        # Should initialize successfully without optional components
        assert agent.interface_id == "agent:evolution_agent"
        assert agent._health_tracker is None
        assert agent._memory_monitor is None


class TestEvolutionAgentSynthesis:
    """Test Evolution Agent synthesis functionality."""
    
    @patch('phase_zero.prompt_loader.prompt_loader.get_prompt')
    async def test_successful_synthesis_processing(
        self, 
        mock_get_prompt, 
        evolution_agent, 
        sample_phase_zero_analysis,
        sample_comprehensive_synthesis_result
    ):
        """Test successful synthesis processing with comprehensive output."""
        # Mock system prompt
        mock_get_prompt.return_value = "System prompt for Evolution Agent synthesis"
        
        # Mock the parent process_with_validation method
        with patch.object(AgentInterface, 'process_with_validation', new=AsyncMock(return_value=sample_comprehensive_synthesis_result)):
            result = await evolution_agent._process(
                json.dumps(sample_phase_zero_analysis),
                evolution_agent._get_synthesis_schema(),
                current_phase="phase_one",
                metadata={"synthesis_type": "comprehensive"}
            )
        
        # Verify result structure
        assert result is not None
        assert "strategic_adaptations" in result
        
        # Verify common patterns identification
        common_patterns = result["strategic_adaptations"]["common_patterns"]
        assert len(common_patterns) >= 2
        assert common_patterns[0]["pattern"] == "scope_clarity_issues"
        assert common_patterns[0]["frequency"] == 8
        
        # Verify reinforcing signals
        reinforcing_signals = result["strategic_adaptations"]["reinforcing_signals"]
        assert len(reinforcing_signals) >= 2
        assert reinforcing_signals[0]["signal"] == "requirements_clarity_critical"
        assert reinforcing_signals[0]["convergence_strength"] == "strong"
        
        # Verify strategic adjustments
        strategic_adjustments = result["strategic_adaptations"]["strategic_adjustments"]
        assert len(strategic_adjustments) >= 2
        assert strategic_adjustments[0]["adjustment"] == "scope_refinement_mandatory"
        assert strategic_adjustments[0]["implementation_priority"] == "immediate"
        
        # Verify synthesis section
        synthesis = result["strategic_adaptations"]["synthesis"]
        assert "priority_adaptations" in synthesis
        assert "implementation_strategy" in synthesis
        assert "success_metrics" in synthesis
        
        # Verify system prompt was requested
        mock_get_prompt.assert_called_once_with(AgentType.EVOLUTION, PromptType.PHASE_ONE_INITIAL)
    
    async def test_synthesis_schema_structure(self, evolution_agent):
        """Test synthesis schema structure."""
        schema = evolution_agent._get_synthesis_schema()
        
        # Verify top-level structure
        assert "strategic_adaptations" in schema
        strategic_adaptations = schema["strategic_adaptations"]
        
        # Verify all required sections
        assert "common_patterns" in strategic_adaptations
        assert "reinforcing_signals" in strategic_adaptations
        assert "strategic_adjustments" in strategic_adaptations
        assert "high_impact_opportunities" in strategic_adaptations
        assert "integration_strategies" in strategic_adaptations
        assert "synthesis" in strategic_adaptations
        
        # Verify synthesis subsections
        synthesis = strategic_adaptations["synthesis"]
        assert "priority_adaptations" in synthesis
        assert "implementation_strategy" in synthesis
        assert "success_metrics" in synthesis
    
    async def test_synthesis_with_minimal_input(self, evolution_agent):
        """Test synthesis processing with minimal Phase Zero input."""
        minimal_input = {
            "sun_agent_analysis": {
                "dual_perspective_analysis": {
                    "issue_analysis": {"scope_issues": [{"issue": "Minor scope concern"}]},
                    "synthesis": {"key_observations": ["Small improvement needed"]}
                }
            }
        }
        
        minimal_result = {
            "strategic_adaptations": {
                "common_patterns": [
                    {"pattern": "minor_adjustments", "frequency": 1, "severity": "low"}
                ],
                "synthesis": {
                    "priority_adaptations": [
                        {"adaptation": "minor_scope_adjustment", "timeline": "1 week"}
                    ],
                    "implementation_strategy": {"approach": "incremental"},
                    "success_metrics": [{"metric": "completion_rate", "target": "100%"}]
                }
            }
        }
        
        with patch.object(AgentInterface, 'process_with_validation', new=AsyncMock(return_value=minimal_result)):
            result = await evolution_agent._process(
                json.dumps(minimal_input),
                evolution_agent._get_synthesis_schema()
            )
        
        # Verify minimal synthesis works
        assert result is not None
        assert result["strategic_adaptations"]["common_patterns"][0]["pattern"] == "minor_adjustments"
    
    async def test_synthesis_error_handling(self, evolution_agent, sample_phase_zero_analysis):
        """Test synthesis error handling."""
        # Mock processing error
        with patch.object(AgentInterface, 'process_with_validation', new=AsyncMock(side_effect=Exception("Synthesis error"))):
            with pytest.raises(Exception, match="Synthesis error"):
                await evolution_agent._process(
                    json.dumps(sample_phase_zero_analysis),
                    evolution_agent._get_synthesis_schema()
                )


class TestEvolutionAgentHelperMethods:
    """Test Evolution Agent helper methods."""
    
    async def test_get_synthesis_schema_method(self, evolution_agent):
        """Test _get_synthesis_schema helper method."""
        schema = evolution_agent._get_synthesis_schema()
        
        # Verify it returns the expected schema structure
        assert isinstance(schema, dict)
        assert "strategic_adaptations" in schema
        
        # Verify schema types are properly defined
        strategic_adaptations = schema["strategic_adaptations"]
        assert "common_patterns" in strategic_adaptations
        assert "reinforcing_signals" in strategic_adaptations
        assert "strategic_adjustments" in strategic_adaptations
        
        # Verify List[Dict] type hints are preserved in the schema
        from typing import get_origin, get_args
        # The schema should maintain proper typing structure
        assert isinstance(strategic_adaptations["common_patterns"], type)
    
    async def test_conversation_enhancement(self, evolution_agent, sample_phase_zero_analysis):
        """Test conversation enhancement with system prompt."""
        with patch('phase_zero.prompt_loader.prompt_loader.get_prompt') as mock_get_prompt:
            mock_get_prompt.return_value = "Enhanced system prompt"
            
            # Mock successful processing
            with patch.object(AgentInterface, 'process_with_validation', new=AsyncMock(return_value={})) as mock_process:
                await evolution_agent._process(
                    json.dumps(sample_phase_zero_analysis),
                    evolution_agent._get_synthesis_schema(),
                    current_phase="phase_one"
                )
                
                # Verify enhanced conversation was passed to parent
                call_args = mock_process.call_args[0]
                enhanced_conversation = call_args[0]
                
                # Should contain system prompt and analysis input
                assert "Enhanced system prompt" in enhanced_conversation
                assert "## Analysis Input" in enhanced_conversation
                assert json.dumps(sample_phase_zero_analysis) in enhanced_conversation
    
    async def test_fallback_without_system_prompt(self, evolution_agent, sample_phase_zero_analysis):
        """Test fallback behavior when system prompt is not available."""
        with patch('phase_zero.prompt_loader.prompt_loader.get_prompt') as mock_get_prompt:
            mock_get_prompt.return_value = None  # No system prompt available
            
            # Mock successful processing
            with patch.object(AgentInterface, 'process_with_validation', new=AsyncMock(return_value={})) as mock_process:
                await evolution_agent._process(
                    json.dumps(sample_phase_zero_analysis),
                    evolution_agent._get_synthesis_schema()
                )
                
                # Verify fallback conversation format
                call_args = mock_process.call_args[0]
                conversation = call_args[0]
                
                # Should be valid JSON without system prompt
                analysis_data = json.loads(conversation)
                assert "conversation" in analysis_data
                assert "phase" in analysis_data
                assert "metadata" in analysis_data


class TestEvolutionAgentIntegration:
    """Test Evolution Agent integration scenarios."""
    
    @patch('phase_zero.prompt_loader.prompt_loader.get_prompt')
    async def test_phase_specific_prompt_selection(self, mock_get_prompt, evolution_agent):
        """Test that appropriate prompts are selected for different phases."""
        mock_get_prompt.return_value = "Phase-specific prompt"
        
        # Test with different phases
        test_phases = ["phase_one", "phase_two", "phase_three"]
        
        for phase in test_phases:
            with patch.object(AgentInterface, 'process_with_validation', new=AsyncMock(return_value={})):
                await evolution_agent._process(
                    "test input",
                    evolution_agent._get_synthesis_schema(),
                    current_phase=phase
                )
        
        # Verify prompt loader was called for each phase
        assert mock_get_prompt.call_count == len(test_phases)
        
        # Verify correct agent type was always used
        for call in mock_get_prompt.call_args_list:
            assert call[0][0] == AgentType.EVOLUTION
    
    async def test_metadata_propagation(self, evolution_agent, sample_phase_zero_analysis):
        """Test metadata propagation through synthesis process."""
        test_metadata = {
            "synthesis_type": "comprehensive",
            "analysis_timestamp": datetime.now().isoformat(),
            "agent_count": 9,
            "priority_level": "high"
        }
        
        with patch.object(AgentInterface, 'process_with_validation', new=AsyncMock(return_value={})) as mock_process:
            await evolution_agent._process(
                json.dumps(sample_phase_zero_analysis),
                evolution_agent._get_synthesis_schema(),
                current_phase="phase_one",
                metadata=test_metadata
            )
            
            # Verify metadata was passed to parent process
            call_kwargs = mock_process.call_args[1]
            assert call_kwargs["metadata"] == test_metadata
            assert call_kwargs["current_phase"] == "phase_one"
    
    async def test_comprehensive_synthesis_workflow(
        self, 
        evolution_agent, 
        sample_phase_zero_analysis, 
        sample_comprehensive_synthesis_result
    ):
        """Test complete synthesis workflow from Phase Zero input to strategic output."""
        with patch('phase_zero.prompt_loader.prompt_loader.get_prompt') as mock_get_prompt:
            mock_get_prompt.return_value = "Comprehensive synthesis prompt"
            
            with patch.object(AgentInterface, 'process_with_validation', new=AsyncMock(return_value=sample_comprehensive_synthesis_result)):
                # Execute complete synthesis workflow
                result = await evolution_agent._process(
                    json.dumps(sample_phase_zero_analysis),
                    evolution_agent._get_synthesis_schema(),
                    current_phase="phase_one",
                    metadata={"synthesis_type": "comprehensive"}
                )
        
        # Verify comprehensive synthesis result
        assert result == sample_comprehensive_synthesis_result
        
        # Verify strategic adaptations are properly structured
        strategic_adaptations = result["strategic_adaptations"]
        
        # Verify pattern analysis
        common_patterns = strategic_adaptations["common_patterns"]
        assert all("pattern" in pattern for pattern in common_patterns)
        assert all("frequency" in pattern for pattern in common_patterns)
        assert all("agents_reporting" in pattern for pattern in common_patterns)
        
        # Verify reinforcing signals
        reinforcing_signals = strategic_adaptations["reinforcing_signals"] 
        assert all("signal" in signal for signal in reinforcing_signals)
        assert all("supporting_agents" in signal for signal in reinforcing_signals)
        assert all("convergence_strength" in signal for signal in reinforcing_signals)
        
        # Verify strategic adjustments
        strategic_adjustments = strategic_adaptations["strategic_adjustments"]
        assert all("adjustment" in adj for adj in strategic_adjustments)
        assert all("rationale" in adj for adj in strategic_adjustments)
        assert all("implementation_priority" in adj for adj in strategic_adjustments)
        
        # Verify synthesis quality
        synthesis = strategic_adaptations["synthesis"]
        assert "priority_adaptations" in synthesis
        assert "implementation_strategy" in synthesis
        assert "success_metrics" in synthesis
        
        # Verify priority adaptations have required fields
        priority_adaptations = synthesis["priority_adaptations"]
        assert all("adaptation" in adapt for adapt in priority_adaptations)
        assert all("justification" in adapt for adapt in priority_adaptations)
        assert all("timeline" in adapt for adapt in priority_adaptations)
        assert all("success_criteria" in adapt for adapt in priority_adaptations)


class TestEvolutionAgentErrorScenarios:
    """Test Evolution Agent error handling scenarios."""
    
    async def test_malformed_phase_zero_input(self, evolution_agent):
        """Test handling of malformed Phase Zero input."""
        malformed_input = "not_valid_json"
        
        # Should handle malformed input gracefully
        with patch.object(AgentInterface, 'process_with_validation', new=AsyncMock(return_value={})):
            result = await evolution_agent._process(
                malformed_input,
                evolution_agent._get_synthesis_schema()
            )
        
        # Verify processing continues with fallback
        assert result == {}
    
    async def test_empty_phase_zero_analysis(self, evolution_agent):
        """Test handling of empty Phase Zero analysis."""
        empty_analysis = {}
        
        empty_result = {
            "strategic_adaptations": {
                "common_patterns": [],
                "reinforcing_signals": [],
                "strategic_adjustments": [],
                "high_impact_opportunities": [],
                "integration_strategies": [],
                "synthesis": {
                    "priority_adaptations": [],
                    "implementation_strategy": {"approach": "minimal"},
                    "success_metrics": []
                }
            }
        }
        
        with patch.object(AgentInterface, 'process_with_validation', new=AsyncMock(return_value=empty_result)):
            result = await evolution_agent._process(
                json.dumps(empty_analysis),
                evolution_agent._get_synthesis_schema()
            )
        
        # Verify empty input produces empty but valid synthesis
        assert result["strategic_adaptations"]["common_patterns"] == []
        assert result["strategic_adaptations"]["synthesis"]["priority_adaptations"] == []
    
    async def test_synthesis_processing_exception(self, evolution_agent, sample_phase_zero_analysis):
        """Test exception handling during synthesis processing."""
        with patch.object(AgentInterface, 'process_with_validation', new=AsyncMock(side_effect=ValueError("Processing failed"))):
            with pytest.raises(ValueError, match="Processing failed"):
                await evolution_agent._process(
                    json.dumps(sample_phase_zero_analysis),
                    evolution_agent._get_synthesis_schema()
                )
    
    async def test_prompt_loader_failure(self, evolution_agent, sample_phase_zero_analysis):
        """Test handling when prompt loader fails."""
        with patch('phase_zero.prompt_loader.prompt_loader.get_prompt') as mock_get_prompt:
            mock_get_prompt.side_effect = Exception("Prompt loading failed")
            
            # Should continue processing even if prompt loading fails
            with patch.object(AgentInterface, 'process_with_validation', new=AsyncMock(return_value={})):
                result = await evolution_agent._process(
                    json.dumps(sample_phase_zero_analysis),
                    evolution_agent._get_synthesis_schema()
                )
            
            # Should complete successfully with fallback
            assert result == {}