"""
Test fixtures and mock data for Fire and Air agent testing.

Provides reusable fixtures, mock data, and helper functions for testing
Fire and Air agent functionality across different test modules.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any, List

from resources.fire_agent.models import (
    ComplexityAnalysis,
    DecompositionResult,
    ComplexityCause,
    ComplexityLevel,
    ComplexityThreshold,
    DecompositionStrategy
)

from resources.air_agent.models import (
    DecisionEvent,
    FireIntervention,
    HistoricalContext,
    DecisionPattern,
    PatternConfidence,
    DecisionType,
    DecisionOutcome,
    CrossPhasePattern
)


class FireAgentFixtures:
    """Fixtures for Fire Agent testing."""
    
    @staticmethod
    @pytest.fixture
    def simple_guideline():
        """Simple guideline that should not trigger decomposition."""
        return {
            "components": ["component1", "component2", "component3"],
            "dependencies": ["dependency1", "dependency2"],
            "interfaces": ["interface1"],
            "scope": {
                "features": ["feature1", "feature2"],
                "limited": True
            },
            "responsibilities": ["primary_function", "secondary_function"]
        }
    
    @staticmethod
    @pytest.fixture
    def moderately_complex_guideline():
        """Moderately complex guideline for testing threshold behavior."""
        return {
            "components": [f"component_{i}" for i in range(8)],
            "dependencies": [f"dependency_{i}" for i in range(6)],
            "interfaces": [f"interface_{i}" for i in range(4)],
            "scope": {
                "features": [f"feature_{i}" for i in range(10)],
                "modules": [f"module_{i}" for i in range(5)]
            },
            "responsibilities": [f"responsibility_{i}" for i in range(6)]
        }
    
    @staticmethod
    @pytest.fixture
    def highly_complex_guideline():
        """Highly complex guideline that should definitely trigger decomposition."""
        return {
            "components": [f"component_{i}" for i in range(25)],
            "dependencies": [f"dependency_{i}" for i in range(20)],
            "interfaces": [f"interface_{i}" for i in range(15)],
            "scope": {
                "features": [f"feature_{i}" for i in range(30)],
                "modules": [f"module_{i}" for i in range(20)],
                "services": [f"service_{i}" for i in range(15)],
                "subsystems": [f"subsystem_{i}" for i in range(10)]
            },
            "responsibilities": [f"responsibility_{i}" for i in range(15)],
            "integration": {
                "apis": [f"api_{i}" for i in range(12)],
                "protocols": [f"protocol_{i}" for i in range(8)],
                "channels": [f"channel_{i}" for i in range(6)]
            },
            "cross_cutting_concerns": [
                "logging", "security", "caching", "monitoring", 
                "validation", "error_handling", "performance", "scalability"
            ]
        }
    
    @staticmethod
    @pytest.fixture
    def simple_feature():
        """Simple feature specification."""
        return {
            "feature_id": "simple_feature",
            "name": "Simple Feature",
            "responsibilities": ["core_function"],
            "dependencies": ["dependency1"],
            "scope": {
                "limited": True,
                "focused": True
            },
            "implementation": {
                "complexity": "low"
            }
        }
    
    @staticmethod
    @pytest.fixture
    def complex_feature():
        """Complex feature that should trigger decomposition."""
        return {
            "feature_id": "complex_feature",
            "name": "Complex Multi-Purpose Feature",
            "responsibilities": [
                "user_authentication", "data_validation", "report_generation",
                "notification_sending", "audit_logging", "cache_management",
                "error_handling", "performance_monitoring"
            ],
            "dependencies": [
                "auth_service", "database", "email_service", "cache_redis",
                "logging_service", "metrics_collector", "notification_queue",
                "file_storage", "external_api_1", "external_api_2",
                "validation_engine", "report_engine"
            ],
            "scope": {
                "frontend": True,
                "backend": True,
                "database": True,
                "api": True,
                "testing": True,
                "deployment": True,
                "monitoring": True
            },
            "cross_cutting_concerns": [
                "logging", "security", "caching", "monitoring",
                "validation", "error_handling", "performance",
                "authentication", "authorization", "auditing"
            ],
            "implementation": {
                "complexity": "very_high",
                "layers": ["presentation", "business", "data", "integration"],
                "patterns": ["mvc", "repository", "factory", "observer", "strategy"]
            }
        }
    
    @staticmethod
    @pytest.fixture
    def sample_complexity_analysis():
        """Sample complexity analysis result."""
        return ComplexityAnalysis(
            complexity_score=85.0,
            complexity_level=ComplexityLevel.HIGH,
            exceeds_threshold=True,
            complexity_causes=[
                ComplexityCause.MULTIPLE_RESPONSIBILITIES,
                ComplexityCause.HIGH_DEPENDENCY_COUNT,
                ComplexityCause.CROSS_CUTTING_CONCERNS
            ],
            analysis_context="phase_one",
            recommended_strategy=DecompositionStrategy.RESPONSIBILITY_EXTRACTION,
            decomposition_opportunities=[
                "Extract authentication responsibilities",
                "Separate data access concerns",
                "Isolate cross-cutting concerns"
            ],
            confidence_level=0.85,
            intervention_urgency="high",
            risk_assessment="High complexity poses risks to maintainability"
        )
    
    @staticmethod
    @pytest.fixture
    def sample_decomposition_result():
        """Sample successful decomposition result."""
        return DecompositionResult(
            success=True,
            original_complexity_score=85.0,
            new_complexity_score=45.0,
            complexity_reduction=40.0,
            strategy_used=DecompositionStrategy.RESPONSIBILITY_EXTRACTION,
            decomposed_elements=[
                {
                    "element_id": "auth_component",
                    "type": "responsibility",
                    "description": "Authentication and authorization",
                    "scope": ["user_login", "token_validation", "permissions"]
                },
                {
                    "element_id": "data_component",
                    "type": "responsibility", 
                    "description": "Data access and persistence",
                    "scope": ["database_operations", "data_validation", "caching"]
                },
                {
                    "element_id": "reporting_component",
                    "type": "responsibility",
                    "description": "Report generation and export",
                    "scope": ["report_creation", "data_aggregation", "export_formats"]
                }
            ],
            simplified_architecture={
                "core_component": {
                    "name": "Authentication Service",
                    "responsibilities": ["authentication", "authorization"],
                    "dependencies": ["user_database", "token_service"]
                },
                "supporting_components": [
                    {
                        "name": "Data Service",
                        "responsibilities": ["data_access", "validation"],
                        "dependencies": ["database", "cache"]
                    },
                    {
                        "name": "Reporting Service", 
                        "responsibilities": ["report_generation"],
                        "dependencies": ["data_service", "template_engine"]
                    }
                ]
            },
            lessons_learned=[
                "Responsibility extraction highly effective for multi-purpose components",
                "Authentication concerns should be separated early",
                "Data access patterns benefit from isolation"
            ],
            success_metrics={
                "complexity_reduction_percentage": 47.1,
                "elements_decomposed": 3,
                "strategy_effectiveness": "high"
            }
        )
    
    @staticmethod
    @pytest.fixture
    def custom_complexity_thresholds():
        """Custom complexity thresholds for testing."""
        return ComplexityThreshold(
            low_threshold=25.0,
            medium_threshold=55.0,
            high_threshold=80.0,
            critical_threshold=95.0
        )


class AirAgentFixtures:
    """Fixtures for Air Agent testing."""
    
    @staticmethod
    @pytest.fixture
    def sample_decision_events():
        """Sample decision events for pattern analysis."""
        base_time = datetime.now()
        return [
            DecisionEvent(
                event_id="decision_1",
                decision_agent="garden_foundation_refinement",
                decision_type=DecisionType.REFINEMENT_NECESSITY,
                timestamp=base_time - timedelta(days=1),
                input_context={
                    "complexity_score": 85.0,
                    "architectural_issues": ["dependency_cycles", "unclear_boundaries"]
                },
                decision_rationale="Critical architectural issues detected requiring component reorganization",
                decision_details={
                    "analysis_type": "architectural_review",
                    "recommended_action": "reorganize_components",
                    "urgency": "high"
                },
                decision_outcome=DecisionOutcome.SUCCESS,
                effectiveness_score=0.85,
                phase_context="phase_one",
                operation_id="operation_001",
                lessons_learned=["Component reorganization resolved dependency cycles"],
                success_factors=["Clear architectural analysis", "Targeted intervention"]
            ),
            DecisionEvent(
                event_id="decision_2",
                decision_agent="natural_selection",
                decision_type=DecisionType.NATURAL_SELECTION,
                timestamp=base_time - timedelta(days=2),
                input_context={
                    "features_analyzed": 5,
                    "average_performance": 0.72
                },
                decision_rationale="Feature optimization based on performance metrics and complexity analysis",
                decision_details={
                    "optimization_strategy": "selective_improvement",
                    "features_improved": 3,
                    "features_replaced": 1
                },
                decision_outcome=DecisionOutcome.SUCCESS,
                effectiveness_score=0.78,
                phase_context="phase_three",
                operation_id="operation_002",
                lessons_learned=["Selective improvement more effective than wholesale replacement"],
                success_factors=["Performance-based selection", "Complexity-aware decisions"]
            ),
            DecisionEvent(
                event_id="decision_3",
                decision_agent="garden_foundation_refinement",
                decision_type=DecisionType.REFINEMENT_STRATEGY,
                timestamp=base_time - timedelta(days=3),
                input_context={
                    "complexity_score": 65.0,
                    "identified_issues": ["interface_inconsistencies"]
                },
                decision_rationale="Interface standardization needed for better integration",
                decision_details={
                    "strategy": "revise_environment",
                    "focus_area": "interface_design"
                },
                decision_outcome=DecisionOutcome.FAILURE,
                effectiveness_score=0.25,
                phase_context="phase_one",
                operation_id="operation_003",
                failure_factors=["Insufficient analysis", "Wrong strategy choice"],
                lessons_learned=["Interface issues require more comprehensive analysis"]
            )
        ]
    
    @staticmethod
    @pytest.fixture
    def sample_fire_interventions():
        """Sample Fire Agent interventions for context provision."""
        base_time = datetime.now()
        return [
            FireIntervention(
                intervention_id="fire_1",
                intervention_context="phase_one_guideline",
                timestamp=base_time - timedelta(days=1),
                original_complexity_score=88.0,
                final_complexity_score=42.0,
                complexity_reduction=46.0,
                decomposition_strategy="responsibility_extraction",
                success=True,
                intervention_duration=timedelta(minutes=15),
                lessons_learned=[
                    "Responsibility extraction highly effective for guidelines",
                    "Component boundaries became much clearer after decomposition"
                ],
                effective_techniques=[
                    "Strategy: responsibility_extraction",
                    "High complexity reduction achieved"
                ],
                operation_id="fire_operation_001"
            ),
            FireIntervention(
                intervention_id="fire_2",
                intervention_context="phase_three_feature",
                timestamp=base_time - timedelta(days=2),
                original_complexity_score=76.0,
                final_complexity_score=38.0,
                complexity_reduction=38.0,
                decomposition_strategy="functional_separation",
                success=True,
                intervention_duration=timedelta(minutes=12),
                lessons_learned=[
                    "Functional separation worked well for feature complexity",
                    "Decomposed sub-features easier to optimize individually"
                ],
                effective_techniques=[
                    "Strategy: functional_separation",
                    "Strategy highly effective"
                ],
                operation_id="fire_operation_002"
            ),
            FireIntervention(
                intervention_id="fire_3",
                intervention_context="phase_two_component",
                timestamp=base_time - timedelta(days=5),
                original_complexity_score=82.0,
                final_complexity_score=None,
                complexity_reduction=None,
                decomposition_strategy="layer_separation",
                success=False,
                intervention_duration=timedelta(minutes=25),
                lessons_learned=[
                    "Layer separation not suitable for this component type"
                ],
                challenges_encountered=[
                    "Component did not have clear layering opportunities",
                    "Strategy selection needs improvement"
                ],
                operation_id="fire_operation_003"
            )
        ]
    
    @staticmethod
    @pytest.fixture
    def sample_decision_patterns():
        """Sample decision patterns for testing."""
        return [
            DecisionPattern(
                pattern_id="pattern_success_refinement",
                pattern_type="success_pattern",
                pattern_name="Successful Component Reorganization",
                pattern_description="Component reorganization shows 85% success rate",
                decision_types=[DecisionType.REFINEMENT_NECESSITY, DecisionType.REFINEMENT_STRATEGY],
                contexts=["phase_one"],
                frequency=8,
                success_rate=0.85,
                preconditions=["High complexity architectural issues", "Clear dependency analysis"],
                outcomes=["Resolved architectural issues", "Improved component clarity"],
                confidence_level=PatternConfidence.HIGH,
                first_observed=datetime.now() - timedelta(days=30),
                last_observed=datetime.now() - timedelta(days=1),
                recommendations=[
                    "Continue using component reorganization for architectural issues",
                    "Ensure thorough dependency analysis before applying"
                ],
                supporting_events=["decision_1", "decision_4", "decision_7"]
            ),
            DecisionPattern(
                pattern_id="pattern_failure_interface",
                pattern_type="failure_pattern",
                pattern_name="Interface Revision Failures",
                pattern_description="Interface revision strategy shows only 30% success rate",
                decision_types=[DecisionType.REFINEMENT_STRATEGY],
                contexts=["phase_one"],
                frequency=5,
                success_rate=0.30,
                preconditions=["Interface inconsistencies", "Integration problems"],
                outcomes=["Failed to resolve interface issues", "Required additional analysis"],
                confidence_level=PatternConfidence.MEDIUM,
                first_observed=datetime.now() - timedelta(days=25),
                last_observed=datetime.now() - timedelta(days=3),
                recommendations=[
                    "Avoid interface revision for complex integration issues",
                    "Consider more comprehensive architectural analysis"
                ],
                anti_patterns=["Quick interface fixes", "Insufficient analysis before action"],
                supporting_events=["decision_3", "decision_8"]
            )
        ]
    
    @staticmethod
    @pytest.fixture
    def sample_historical_context():
        """Sample historical context for testing."""
        return HistoricalContext(
            context_type="refinement",
            requesting_agent="garden_foundation_refinement",
            context_timestamp=datetime.now(),
            relevant_events=[],  # Would be populated with sample_decision_events
            success_patterns=[
                "Successful Component Reorganization",
                "Effective Dependency Reduction",
                "Architectural Issue Resolution"
            ],
            failure_patterns=[
                "Interface Revision Failures",
                "Insufficient Analysis Patterns"
            ],
            recommended_approaches=[
                "Use component reorganization for architectural issues",
                "Perform thorough dependency analysis before intervention",
                "Consider complexity metrics in strategy selection"
            ],
            cautionary_notes=[
                "Avoid quick fixes for interface issues",
                "Ensure sufficient analysis before major changes",
                "Monitor effectiveness of interventions"
            ],
            confidence_level=PatternConfidence.HIGH,
            lookback_period=timedelta(days=30),
            events_analyzed=15,
            patterns_identified=8
        )
    
    @staticmethod
    @pytest.fixture
    def sample_cross_phase_pattern():
        """Sample cross-phase pattern for testing."""
        return CrossPhasePattern(
            pattern_id="complexity_escalation",
            pattern_name="Complexity Escalation Pattern",
            phases_involved=["phase_one", "phase_three"],
            pattern_type="escalation",
            description="Unresolved Phase 1 complexity leads to increased Phase 3 optimization needs",
            trigger_conditions=[
                "High Phase 1 complexity scores",
                "Multiple Phase 1 refinement cycles",
                "Incomplete architectural resolution"
            ],
            propagation_path=[
                "phase_one: complex_architecture",
                "phase_two: component_implementation_issues", 
                "phase_three: feature_optimization_difficulties"
            ],
            system_impact="negative",
            mitigation_strategies=[
                "Increase Phase 1 complexity monitoring",
                "Apply Fire Agent decomposition earlier",
                "Enhance architectural validation"
            ],
            early_warning_signs=[
                "Phase 1 complexity scores above 80",
                "Multiple refinement iterations",
                "Dependency cycle warnings"
            ],
            supporting_cases=["case_001", "case_003", "case_007"],
            confidence=PatternConfidence.MEDIUM
        )


class SharedMockObjects:
    """Shared mock objects for testing."""
    
    @staticmethod
    @pytest.fixture
    def mock_state_manager():
        """Mock state manager with common functionality."""
        mock = AsyncMock()
        mock.set_state = AsyncMock()
        mock.get_state = AsyncMock(return_value=None)
        mock.list_keys = AsyncMock(return_value=[])
        mock.delete_state = AsyncMock()
        return mock
    
    @staticmethod
    @pytest.fixture
    def mock_health_tracker():
        """Mock health tracker for testing."""
        mock = MagicMock()
        mock.track_metric = MagicMock()
        return mock
    
    @staticmethod
    @pytest.fixture
    def mock_event_queue():
        """Mock event queue for testing."""
        mock = AsyncMock()
        mock.emit = AsyncMock()
        mock.subscribe = AsyncMock()
        return mock
    
    @staticmethod
    @pytest.fixture
    def mock_state_manager_with_decision_history(sample_decision_events):
        """Mock state manager populated with decision history."""
        mock = AsyncMock()
        
        # Create mock storage for decision events
        decision_storage = {}
        for i, event in enumerate(sample_decision_events):
            key = f"air_agent:decision_event:decision_{i+1}"
            decision_storage[key] = event.__dict__
        
        # Mock list_keys to return decision event keys
        mock.list_keys.return_value = list(decision_storage.keys())
        
        # Mock get_state to return stored events
        mock.get_state.side_effect = lambda key, *args: decision_storage.get(key)
        
        mock.set_state = AsyncMock()
        mock.delete_state = AsyncMock()
        
        return mock
    
    @staticmethod
    @pytest.fixture
    def mock_state_manager_with_fire_history(sample_fire_interventions):
        """Mock state manager populated with Fire intervention history."""
        mock = AsyncMock()
        
        # Create mock storage for Fire interventions
        fire_storage = {}
        for i, intervention in enumerate(sample_fire_interventions):
            key = f"air_agent:fire_intervention:fire_{i+1}"
            fire_storage[key] = intervention.__dict__
        
        # Mock list_keys to return Fire intervention keys
        mock.list_keys.return_value = list(fire_storage.keys())
        
        # Mock get_state to return stored interventions
        mock.get_state.side_effect = lambda key, *args: fire_storage.get(key)
        
        mock.set_state = AsyncMock()
        mock.delete_state = AsyncMock()
        
        return mock


class TestDataGenerators:
    """Generators for test data scenarios."""
    
    @staticmethod
    def generate_feature_performance_data(num_features: int = 5, complexity_distribution: str = "mixed") -> List[Dict[str, Any]]:
        """Generate feature performance data for testing."""
        features = []
        
        for i in range(num_features):
            if complexity_distribution == "mixed":
                # Mix of simple, moderate, and complex features
                if i % 3 == 0:
                    complexity = "simple"
                    responsibilities = [f"responsibility_{i}"]
                    dependencies = [f"dep_{i}"]
                    performance = 0.8 + (i % 3) * 0.05
                elif i % 3 == 1:
                    complexity = "moderate"
                    responsibilities = [f"responsibility_{i}_{j}" for j in range(3)]
                    dependencies = [f"dep_{i}_{j}" for j in range(4)]
                    performance = 0.65 + (i % 3) * 0.05
                else:
                    complexity = "complex"
                    responsibilities = [f"responsibility_{i}_{j}" for j in range(6)]
                    dependencies = [f"dep_{i}_{j}" for j in range(8)]
                    performance = 0.5 + (i % 3) * 0.05
            else:
                # All features have same complexity
                complexity = complexity_distribution
                responsibilities = [f"responsibility_{i}_{j}" for j in range(2 if complexity == "simple" else 5)]
                dependencies = [f"dep_{i}_{j}" for j in range(2 if complexity == "simple" else 6)]
                performance = 0.7
            
            feature = {
                "feature_id": f"feature_{i}",
                "performance_score": performance,
                "feature_specification": {
                    "responsibilities": responsibilities,
                    "dependencies": dependencies,
                    "scope": {"complexity": complexity},
                    "implementation": {"type": complexity}
                }
            }
            
            if complexity == "complex":
                feature["feature_specification"]["cross_cutting_concerns"] = ["logging", "security"]
                feature["feature_specification"]["scope"]["broad"] = True
            
            features.append(feature)
        
        return features
    
    @staticmethod
    def generate_decision_history(
        num_decisions: int = 10,
        success_rate: float = 0.7,
        agents: List[str] = None,
        time_span_days: int = 30
    ) -> List[DecisionEvent]:
        """Generate decision history for testing."""
        if agents is None:
            agents = ["garden_foundation_refinement", "natural_selection", "evolution"]
        
        decisions = []
        base_time = datetime.now()
        
        for i in range(num_decisions):
            # Determine success based on success rate
            is_success = i < int(num_decisions * success_rate)
            
            # Rotate through agents
            agent = agents[i % len(agents)]
            
            # Assign decision types based on agent
            if agent == "garden_foundation_refinement":
                decision_type = DecisionType.REFINEMENT_NECESSITY if i % 2 == 0 else DecisionType.REFINEMENT_STRATEGY
            elif agent == "natural_selection":
                decision_type = DecisionType.NATURAL_SELECTION
            else:
                decision_type = DecisionType.FEATURE_EVOLUTION
            
            decision = DecisionEvent(
                event_id=f"test_decision_{i}",
                decision_agent=agent,
                decision_type=decision_type,
                timestamp=base_time - timedelta(days=i * time_span_days // num_decisions),
                input_context={"test": f"context_{i}"},
                decision_rationale=f"Test rationale {i}",
                decision_details={"test": f"details_{i}"},
                decision_outcome=DecisionOutcome.SUCCESS if is_success else DecisionOutcome.FAILURE,
                effectiveness_score=0.8 if is_success else 0.3,
                phase_context="phase_one" if agent == "garden_foundation_refinement" else "phase_three",
                operation_id=f"test_operation_{i}"
            )
            
            decisions.append(decision)
        
        return decisions


# Export all fixtures and generators for use in tests
__all__ = [
    'FireAgentFixtures',
    'AirAgentFixtures', 
    'SharedMockObjects',
    'TestDataGenerators'
]