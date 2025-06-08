"""
Comprehensive test suite for Fire Agent functionality.

Tests complexity detection, decomposition strategies, and integration points
across all phases of the FFTT system.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from resources.fire_agent import (
    analyze_guideline_complexity,
    analyze_feature_complexity,
    analyze_component_complexity,
    decompose_complex_guideline,
    decompose_complex_feature,
    simplify_component_architecture,
    calculate_complexity_score,
    identify_complexity_causes,
    assess_decomposition_impact
)

from resources.fire_agent.models import (
    ComplexityAnalysis,
    DecompositionResult,
    ComplexityCause,
    ComplexityLevel,
    ComplexityThreshold,
    DecompositionStrategy
)


class TestFireAgentComplexityDetection:
    """Test Fire Agent complexity detection algorithms."""
    
    @pytest.fixture
    def mock_state_manager(self):
        """Mock state manager for testing."""
        mock = AsyncMock()
        mock.set_state = AsyncMock()
        mock.get_state = AsyncMock()
        mock.list_keys = AsyncMock(return_value=[])
        return mock
    
    @pytest.fixture
    def mock_health_tracker(self):
        """Mock health tracker for testing."""
        mock = MagicMock()
        mock.track_metric = MagicMock()
        return mock
    
    @pytest.fixture
    def simple_guideline(self):
        """Simple guideline for testing."""
        return {
            "components": ["component1", "component2"],
            "dependencies": ["dep1"],
            "interfaces": ["interface1"],
            "scope": "limited"
        }
    
    @pytest.fixture
    def complex_guideline(self):
        """Complex guideline that should trigger decomposition."""
        return {
            "components": [f"component_{i}" for i in range(15)],
            "dependencies": [f"dep_{i}" for i in range(10)],
            "interfaces": [f"interface_{i}" for i in range(8)],
            "responsibilities": [f"responsibility_{i}" for i in range(12)],
            "scope": {
                "features": [f"feature_{i}" for i in range(20)],
                "modules": [f"module_{i}" for i in range(15)],
                "services": [f"service_{i}" for i in range(10)]
            },
            "integration": {
                "apis": [f"api_{i}" for i in range(12)],
                "protocols": [f"protocol_{i}" for i in range(8)]
            }
        }
    
    @pytest.fixture
    def simple_feature(self):
        """Simple feature specification."""
        return {
            "feature_id": "simple_feature",
            "name": "Simple Feature",
            "responsibilities": ["core_function"],
            "dependencies": ["dep1"],
            "scope": {"limited": True}
        }
    
    @pytest.fixture
    def complex_feature(self):
        """Complex feature that should trigger decomposition."""
        return {
            "feature_id": "complex_feature", 
            "name": "Complex Feature",
            "responsibilities": [f"responsibility_{i}" for i in range(8)],
            "dependencies": [f"dep_{i}" for i in range(12)],
            "scope": {
                "features": [f"sub_feature_{i}" for i in range(15)],
                "cross_cutting_concerns": ["logging", "security", "caching", "monitoring"]
            },
            "implementation": {
                "frontend": True,
                "backend": True,
                "database": True,
                "api": True,
                "testing": True
            }
        }
    
    @pytest.mark.asyncio
    async def test_analyze_simple_guideline_complexity(self, simple_guideline, mock_state_manager, mock_health_tracker):
        """Test complexity analysis of a simple guideline."""
        result = await analyze_guideline_complexity(
            guideline=simple_guideline,
            context="phase_one",
            state_manager=mock_state_manager,
            health_tracker=mock_health_tracker
        )
        
        assert isinstance(result, ComplexityAnalysis)
        assert result.complexity_score < 70  # Should be low complexity
        assert result.complexity_level in [ComplexityLevel.LOW, ComplexityLevel.MEDIUM]
        assert not result.exceeds_threshold
        assert result.analysis_context == "phase_one"
        assert result.confidence_level > 0.5
        
        # Verify state manager and health tracker were called
        mock_state_manager.set_state.assert_called()
        mock_health_tracker.track_metric.assert_called()
    
    @pytest.mark.asyncio
    async def test_analyze_complex_guideline_complexity(self, complex_guideline, mock_state_manager, mock_health_tracker):
        """Test complexity analysis of a complex guideline."""
        result = await analyze_guideline_complexity(
            guideline=complex_guideline,
            context="phase_one",
            state_manager=mock_state_manager,
            health_tracker=mock_health_tracker
        )
        
        assert isinstance(result, ComplexityAnalysis)
        assert result.complexity_score > 70  # Should be high complexity
        assert result.complexity_level in [ComplexityLevel.HIGH, ComplexityLevel.CRITICAL]
        assert result.exceeds_threshold
        assert len(result.complexity_causes) > 0
        assert result.recommended_strategy is not None
        assert len(result.decomposition_opportunities) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_feature_complexity_simple(self, simple_feature, mock_state_manager):
        """Test feature complexity analysis for simple feature."""
        result = await analyze_feature_complexity(
            feature_spec=simple_feature,
            feature_context={},
            state_manager=mock_state_manager
        )
        
        assert isinstance(result, ComplexityAnalysis)
        assert result.complexity_score < 60
        assert result.analysis_context == "phase_three_feature"
        assert not result.exceeds_threshold
    
    @pytest.mark.asyncio
    async def test_analyze_feature_complexity_complex(self, complex_feature, mock_state_manager):
        """Test feature complexity analysis for complex feature."""
        result = await analyze_feature_complexity(
            feature_spec=complex_feature,
            feature_context={"related_features": ["feature1", "feature2", "feature3"]},
            state_manager=mock_state_manager
        )
        
        assert isinstance(result, ComplexityAnalysis)
        assert result.complexity_score > 60
        assert result.exceeds_threshold
        assert ComplexityCause.MULTIPLE_RESPONSIBILITIES in result.complexity_causes or \
               ComplexityCause.CROSS_CUTTING_CONCERNS in result.complexity_causes
    
    @pytest.mark.asyncio
    async def test_analyze_component_complexity(self, mock_state_manager):
        """Test component complexity analysis."""
        component_spec = {
            "architecture": {"layers": ["presentation", "business", "data"]},
            "interfaces": [f"interface_{i}" for i in range(5)],
            "state_management": {"complex": True}
        }
        
        result = await analyze_component_complexity(
            component_spec=component_spec,
            component_context={},
            state_manager=mock_state_manager
        )
        
        assert isinstance(result, ComplexityAnalysis)
        assert result.analysis_context == "phase_two_component"
        assert result.complexity_score >= 0
    
    def test_calculate_complexity_score_simple(self):
        """Test complexity score calculation for simple structures."""
        simple_data = {"key1": "value1", "key2": ["item1", "item2"]}
        
        score = calculate_complexity_score(simple_data, context="general")
        
        assert 0 <= score <= 100
        assert score < 50  # Should be relatively low
    
    def test_calculate_complexity_score_complex(self):
        """Test complexity score calculation for complex structures."""
        complex_data = {
            "level1": {
                "level2": {
                    "level3": {
                        "items": [f"item_{i}" for i in range(20)]
                    }
                }
            },
            "dependencies": [f"dep_{i}" for i in range(15)],
            "interfaces": [f"interface_{i}" for i in range(10)]
        }
        
        score = calculate_complexity_score(complex_data, context="phase_one")
        
        assert score > 50  # Should be relatively high
    
    def test_identify_complexity_causes(self):
        """Test complexity cause identification."""
        complex_structure = {
            "responsibilities": [f"resp_{i}" for i in range(8)],
            "dependencies": [f"dep_{i}" for i in range(12)],
            "logging": True,
            "security": True,
            "caching": True
        }
        
        causes = identify_complexity_causes(
            data_structure=complex_structure,
            complexity_score=85,
            context="phase_three_feature"
        )
        
        assert len(causes) > 0
        assert any(cause in [
            ComplexityCause.MULTIPLE_RESPONSIBILITIES,
            ComplexityCause.HIGH_DEPENDENCY_COUNT,
            ComplexityCause.CROSS_CUTTING_CONCERNS
        ] for cause in causes)
    
    @pytest.mark.asyncio
    async def test_complexity_analysis_error_handling(self, mock_state_manager):
        """Test error handling in complexity analysis."""
        # Test with None input
        result = await analyze_guideline_complexity(
            guideline=None,
            context="phase_one",
            state_manager=mock_state_manager
        )
        
        assert isinstance(result, ComplexityAnalysis)
        assert result.complexity_score >= 0
        assert result.confidence_level < 1.0
    
    @pytest.mark.asyncio
    async def test_complexity_analysis_without_state_manager(self, simple_guideline):
        """Test complexity analysis without state manager."""
        result = await analyze_guideline_complexity(
            guideline=simple_guideline,
            context="phase_one",
            state_manager=None,
            health_tracker=None
        )
        
        assert isinstance(result, ComplexityAnalysis)
        assert result.complexity_score >= 0


class TestFireAgentDecomposition:
    """Test Fire Agent decomposition functionality."""
    
    @pytest.fixture
    def mock_state_manager(self):
        """Mock state manager for testing."""
        mock = AsyncMock()
        mock.set_state = AsyncMock()
        return mock
    
    @pytest.fixture
    def complex_guideline_for_decomposition(self):
        """Complex guideline suitable for decomposition testing."""
        return {
            "component_architecture": {
                "components": [f"component_{i}" for i in range(15)],
                "responsibilities": [f"responsibility_{i}" for i in range(10)],
                "dependencies": [f"dep_{i}" for i in range(12)]
            },
            "features": [f"feature_{i}" for i in range(20)],
            "scope": "very_broad"
        }
    
    @pytest.fixture
    def complex_feature_for_decomposition(self):
        """Complex feature suitable for decomposition testing."""
        return {
            "feature_id": "complex_feature",
            "responsibilities": [f"responsibility_{i}" for i in range(8)],
            "scope": {
                "frontend": True,
                "backend": True,
                "database": True,
                "api": True
            },
            "cross_cutting": ["logging", "security", "validation"]
        }
    
    @pytest.mark.asyncio
    async def test_decompose_complex_guideline_success(self, complex_guideline_for_decomposition, mock_state_manager):
        """Test successful guideline decomposition."""
        result = await decompose_complex_guideline(
            complex_guideline=complex_guideline_for_decomposition,
            guideline_context="phase_one_component_architecture",
            state_manager=mock_state_manager,
            strategy=DecompositionStrategy.RESPONSIBILITY_EXTRACTION
        )
        
        assert isinstance(result, DecompositionResult)
        assert result.success
        assert result.original_complexity_score > 0
        assert result.simplified_architecture is not None
        assert len(result.decomposed_elements) > 0
        assert result.strategy_used == DecompositionStrategy.RESPONSIBILITY_EXTRACTION
        assert len(result.lessons_learned) > 0
    
    @pytest.mark.asyncio
    async def test_decompose_complex_feature_functional_separation(self, complex_feature_for_decomposition, mock_state_manager):
        """Test feature decomposition with functional separation."""
        result = await decompose_complex_feature(
            complex_feature=complex_feature_for_decomposition,
            decomposition_strategy="functional_separation",
            state_manager=mock_state_manager
        )
        
        assert isinstance(result, DecompositionResult)
        assert result.success
        assert len(result.decomposed_features) > 0
        assert result.strategy_used == DecompositionStrategy.FUNCTIONAL_SEPARATION
        
        # Check that decomposed features have proper structure
        for feature in result.decomposed_features:
            assert "feature_id" in feature
            assert "name" in feature
            assert "type" in feature
    
    @pytest.mark.asyncio
    async def test_decompose_complex_feature_responsibility_extraction(self, complex_feature_for_decomposition, mock_state_manager):
        """Test feature decomposition with responsibility extraction."""
        result = await decompose_complex_feature(
            complex_feature=complex_feature_for_decomposition,
            decomposition_strategy="responsibility_extraction",
            state_manager=mock_state_manager
        )
        
        assert isinstance(result, DecompositionResult)
        assert result.success
        assert len(result.decomposed_features) > 0
        assert result.strategy_used == DecompositionStrategy.RESPONSIBILITY_EXTRACTION
    
    @pytest.mark.asyncio
    async def test_decompose_complex_feature_concern_isolation(self, complex_feature_for_decomposition, mock_state_manager):
        """Test feature decomposition with concern isolation."""
        result = await decompose_complex_feature(
            complex_feature=complex_feature_for_decomposition,
            decomposition_strategy="concern_isolation",
            state_manager=mock_state_manager
        )
        
        assert isinstance(result, DecompositionResult)
        assert result.success
        assert len(result.decomposed_features) > 0
        assert result.strategy_used == DecompositionStrategy.CONCERN_ISOLATION
    
    @pytest.mark.asyncio
    async def test_simplify_component_architecture(self, mock_state_manager):
        """Test component architecture simplification."""
        complex_component = {
            "architecture": {
                "presentation": {"ui": True, "forms": True},
                "business": {"logic": True, "rules": True},
                "data": {"persistence": True, "queries": True}
            }
        }
        
        result = await simplify_component_architecture(
            complex_component=complex_component,
            component_context={},
            state_manager=mock_state_manager,
            strategy=DecompositionStrategy.LAYER_SEPARATION
        )
        
        assert isinstance(result, DecompositionResult)
        assert result.success
        assert len(result.simplified_components) > 0
        assert result.strategy_used == DecompositionStrategy.LAYER_SEPARATION
    
    @pytest.mark.asyncio
    async def test_decomposition_with_empty_input(self, mock_state_manager):
        """Test decomposition behavior with empty input."""
        result = await decompose_complex_guideline(
            complex_guideline={},
            guideline_context="test_context",
            state_manager=mock_state_manager
        )
        
        assert isinstance(result, DecompositionResult)
        # Should handle empty input gracefully
    
    @pytest.mark.asyncio
    async def test_decomposition_error_handling(self, mock_state_manager):
        """Test error handling in decomposition."""
        # Test with invalid input
        result = await decompose_complex_feature(
            complex_feature=None,
            decomposition_strategy="invalid_strategy",
            state_manager=mock_state_manager
        )
        
        assert isinstance(result, DecompositionResult)
        assert not result.success
        assert "error" in str(result.warnings) or len(result.warnings) > 0


class TestFireAgentMetrics:
    """Test Fire Agent metrics and assessment functionality."""
    
    @pytest.fixture
    def sample_complexity_analysis(self):
        """Sample complexity analysis for testing."""
        return ComplexityAnalysis(
            complexity_score=85.0,
            complexity_level=ComplexityLevel.HIGH,
            exceeds_threshold=True,
            complexity_causes=[ComplexityCause.MULTIPLE_RESPONSIBILITIES, ComplexityCause.HIGH_DEPENDENCY_COUNT],
            analysis_context="phase_one",
            recommended_strategy=DecompositionStrategy.RESPONSIBILITY_EXTRACTION,
            decomposition_opportunities=["Split responsibilities", "Reduce dependencies"],
            confidence_level=0.8
        )
    
    @pytest.fixture
    def sample_decomposition_result(self):
        """Sample decomposition result for testing."""
        return DecompositionResult(
            success=True,
            original_complexity_score=85.0,
            new_complexity_score=45.0,
            complexity_reduction=40.0,
            strategy_used=DecompositionStrategy.RESPONSIBILITY_EXTRACTION,
            decomposed_elements=[
                {"element_id": "element_1", "type": "responsibility"},
                {"element_id": "element_2", "type": "responsibility"}
            ],
            lessons_learned=["Responsibility extraction effective for this case"],
            success_metrics={"complexity_reduction_percentage": 47.1}
        )
    
    def test_assess_decomposition_impact_success(self, sample_complexity_analysis, sample_decomposition_result):
        """Test decomposition impact assessment for successful decomposition."""
        assessment = assess_decomposition_impact(
            original_analysis=sample_complexity_analysis,
            decomposition_result=sample_decomposition_result
        )
        
        assert assessment["overall_effectiveness"] == "high"  # 47% reduction (≥30% = high)
        assert assessment["complexity_reduction"]["absolute"] == 40.0
        assert assessment["complexity_reduction"]["percentage"] > 40
        assert assessment["complexity_reduction"]["meets_target"] == True  # >15 point reduction
        assert assessment["decomposition_quality"]["elements_created"] == 2
        assert len(assessment["recommendations"]) > 0
        assert len(assessment["lessons_learned"]) > 0
    
    def test_assess_decomposition_impact_high_effectiveness(self, sample_complexity_analysis):
        """Test assessment of highly effective decomposition."""
        high_impact_result = DecompositionResult(
            success=True,
            original_complexity_score=90.0,
            new_complexity_score=25.0,
            complexity_reduction=65.0,
            strategy_used=DecompositionStrategy.FUNCTIONAL_SEPARATION,
            success_metrics={"complexity_reduction_percentage": 72.2}
        )
        
        assessment = assess_decomposition_impact(
            original_analysis=sample_complexity_analysis,
            decomposition_result=high_impact_result
        )
        
        assert assessment["overall_effectiveness"] == "high"  # >30% reduction
        assert assessment["complexity_reduction"]["percentage"] > 70
    
    def test_assess_decomposition_impact_failure(self, sample_complexity_analysis):
        """Test assessment of failed decomposition."""
        failed_result = DecompositionResult(
            success=False,
            original_complexity_score=85.0,
            warnings=["Decomposition strategy failed"]
        )
        
        assessment = assess_decomposition_impact(
            original_analysis=sample_complexity_analysis,
            decomposition_result=failed_result
        )
        
        assert assessment["overall_effectiveness"] == "unknown"
        assert "Manual review recommended" in assessment["recommendations"]
    
    def test_calculate_complexity_score_with_custom_weights(self):
        """Test complexity score calculation with custom weights."""
        test_data = {
            "structure": {"nested": {"deep": "value"}},
            "dependencies": ["dep1", "dep2", "dep3"],
            "scope": ["item1", "item2", "item3", "item4"]
        }
        
        custom_weights = {
            "structure": 0.5,
            "dependencies": 0.3,
            "scope": 0.2
        }
        
        score = calculate_complexity_score(
            data_structure=test_data,
            context="custom",
            weights=custom_weights
        )
        
        assert 0 <= score <= 100
    
    def test_identify_complexity_causes_comprehensive(self):
        """Test comprehensive complexity cause identification."""
        complex_data = {
            "responsibilities": [f"resp_{i}" for i in range(10)],  # Multiple responsibilities
            "dependencies": [f"dep_{i}" for i in range(15)],       # High dependency count
            "logging": True, "security": True, "monitoring": True,  # Cross-cutting concerns
            "scope": {
                "features": [f"feature_{i}" for i in range(25)]    # Broad scope
            },
            "unclear": "tbd", "ambiguous": "flexible",             # Unclear boundaries
            "conflict": "either_or", "contradiction": True         # Conflicting requirements
        }
        
        causes = identify_complexity_causes(
            data_structure=complex_data,
            complexity_score=95,
            context="phase_three_feature"
        )
        
        # Should identify multiple causes
        assert len(causes) >= 3
        assert ComplexityCause.MULTIPLE_RESPONSIBILITIES in causes
        assert ComplexityCause.HIGH_DEPENDENCY_COUNT in causes
        assert ComplexityCause.CROSS_CUTTING_CONCERNS in causes


class TestFireAgentIntegration:
    """Test Fire Agent integration with FFTT workflows."""
    
    @pytest.mark.asyncio
    async def test_phase_one_integration_simulation(self):
        """Test Fire Agent integration with Phase 1 Tree Placement Planner."""
        # Simulate complex component architecture from Tree Placement Planner
        complex_architecture = {
            "components": [f"component_{i}" for i in range(20)],
            "dependencies": [f"dep_{i}" for i in range(15)],
            "interfaces": [f"interface_{i}" for i in range(12)],
            "integration_points": [f"integration_{i}" for i in range(8)]
        }
        
        # Mock state manager
        mock_state_manager = AsyncMock()
        mock_state_manager.set_state = AsyncMock()
        
        # Analyze complexity
        complexity_analysis = await analyze_guideline_complexity(
            guideline=complex_architecture,
            context="phase_one",
            state_manager=mock_state_manager
        )
        
        # Should detect high complexity
        assert complexity_analysis.exceeds_threshold
        
        # If complex, decompose
        if complexity_analysis.exceeds_threshold:
            decomposition_result = await decompose_complex_guideline(
                complex_guideline=complex_architecture,
                guideline_context="phase_one_component_architecture",
                state_manager=mock_state_manager
            )
            
            assert decomposition_result.success
            assert decomposition_result.simplified_architecture is not None
    
    @pytest.mark.asyncio
    async def test_phase_three_integration_simulation(self):
        """Test Fire Agent integration with Phase 3 Natural Selection."""
        # Simulate feature performance data for Natural Selection
        feature_performances = [
            {
                "feature_id": "feature_1",
                "feature_specification": {
                    "responsibilities": [f"resp_{i}" for i in range(6)],
                    "dependencies": [f"dep_{i}" for i in range(8)],
                    "scope": {"broad": True}
                },
                "performance_score": 0.6
            },
            {
                "feature_id": "feature_2", 
                "feature_specification": {
                    "responsibilities": ["single_responsibility"],
                    "dependencies": ["dep1"],
                    "scope": {"focused": True}
                },
                "performance_score": 0.9
            }
        ]
        
        mock_state_manager = AsyncMock()
        fire_interventions = []
        
        # Simulate Fire Agent analysis for each feature
        for i, feature_performance in enumerate(feature_performances):
            feature_spec = feature_performance["feature_specification"]
            
            complexity_analysis = await analyze_feature_complexity(
                feature_spec=feature_spec,
                feature_context=feature_performance,
                state_manager=mock_state_manager
            )
            
            if complexity_analysis.exceeds_threshold:
                strategy = complexity_analysis.recommended_strategy.value if complexity_analysis.recommended_strategy else "functional_separation"
                
                decomposition_result = await decompose_complex_feature(
                    complex_feature=feature_spec,
                    decomposition_strategy=strategy,
                    state_manager=mock_state_manager
                )
                
                if decomposition_result.success:
                    fire_interventions.append({
                        "original_feature_id": feature_performance["feature_id"],
                        "decomposed_features": decomposition_result.decomposed_features,
                        "complexity_reduction": decomposition_result.complexity_reduction
                    })
        
        # Should have at least one intervention for the complex feature
        assert len(fire_interventions) > 0
        assert fire_interventions[0]["original_feature_id"] == "feature_1"
    
    @pytest.mark.asyncio
    async def test_fire_agent_error_resilience(self):
        """Test Fire Agent resilience to errors and edge cases."""
        mock_state_manager = AsyncMock()
        mock_state_manager.set_state.side_effect = Exception("State manager error")
        
        # Should handle state manager errors gracefully
        result = await analyze_guideline_complexity(
            guideline={"test": "data"},
            context="phase_one",
            state_manager=mock_state_manager
        )
        
        assert isinstance(result, ComplexityAnalysis)
        assert result.complexity_score >= 0
    
    def test_fire_agent_configuration_flexibility(self):
        """Test Fire Agent with different configuration options."""
        # Test custom complexity thresholds
        custom_thresholds = ComplexityThreshold(
            low_threshold=20.0,
            medium_threshold=50.0,
            high_threshold=75.0,
            critical_threshold=90.0
        )
        
        # Test with different threshold - 30.0 should be LOW (below medium_threshold of 50.0)
        assert custom_thresholds.get_level(30.0) == ComplexityLevel.LOW
        # Test medium threshold
        assert custom_thresholds.get_level(60.0) == ComplexityLevel.MEDIUM
        assert custom_thresholds.get_level(80.0) == ComplexityLevel.HIGH
        assert custom_thresholds.get_level(95.0) == ComplexityLevel.CRITICAL


if __name__ == "__main__":
    pytest.main([__file__, "-v"])