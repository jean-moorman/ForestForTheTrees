"""
Fire Agent complexity detection algorithms.

This module provides sophisticated complexity analysis across different contexts:
- Phase 1: Guideline complexity (Tree Placement Planner output)
- Phase 2: Component complexity 
- Phase 3: Feature complexity (Natural Selection support)
- System-wide: Cross-phase complexity hotspot detection
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from .models import (
    ComplexityAnalysis,
    ComplexityLevel,
    ComplexityCause,
    DecompositionStrategy,
    ComplexityThreshold,
    SystemComplexitySnapshot
)

logger = logging.getLogger(__name__)


async def analyze_guideline_complexity(
    guideline: Dict[str, Any],
    context: str,  # "phase_one", "phase_two_component", "phase_three_feature"
    state_manager=None,
    health_tracker=None,
    thresholds: Optional[ComplexityThreshold] = None
) -> ComplexityAnalysis:
    """
    Unified complexity analysis across different guideline types.
    
    This is the primary entry point for Phase 1 Tree Placement Planner
    complexity checking.
    
    Args:
        guideline: The guideline data structure to analyze
        context: Context indicating which phase/type of guideline
        state_manager: Optional state manager for persistence
        health_tracker: Optional health tracker for monitoring
        thresholds: Optional custom complexity thresholds
        
    Returns:
        ComplexityAnalysis with score, causes, and recommendations
    """
    try:
        if thresholds is None:
            thresholds = ComplexityThreshold()
            
        logger.info(f"Analyzing guideline complexity in context: {context}")
        
        # Initialize complexity factors
        complexity_factors = []
        complexity_causes = []
        
        # Basic structure complexity
        structure_score = _analyze_structure_complexity(guideline)
        complexity_factors.append(("structure", structure_score))
        
        # Dependency complexity
        dependency_score = _analyze_dependency_complexity(guideline)
        complexity_factors.append(("dependencies", dependency_score))
        if dependency_score > 60:
            complexity_causes.append(ComplexityCause.HIGH_DEPENDENCY_COUNT)
        
        # Scope complexity
        scope_score = _analyze_scope_complexity(guideline, context)
        complexity_factors.append(("scope", scope_score))
        if scope_score > 70:
            complexity_causes.append(ComplexityCause.BROAD_IMPLEMENTATION_SCOPE)
        
        # Responsibility complexity
        responsibility_score = _analyze_responsibility_complexity(guideline)
        complexity_factors.append(("responsibilities", responsibility_score))
        if responsibility_score > 65:
            complexity_causes.append(ComplexityCause.MULTIPLE_RESPONSIBILITIES)
        
        # Integration complexity
        integration_score = _analyze_integration_complexity(guideline, context)
        complexity_factors.append(("integration", integration_score))
        if integration_score > 75:
            complexity_causes.append(ComplexityCause.INTEGRATION_COMPLEXITY)
        
        # Calculate weighted complexity score
        total_score = _calculate_weighted_complexity_score(complexity_factors)
        
        # Determine complexity level and threshold breach
        complexity_level = thresholds.get_level(total_score)
        exceeds_threshold = complexity_level in [ComplexityLevel.HIGH, ComplexityLevel.CRITICAL]
        
        # Determine recommended strategy
        recommended_strategy = _determine_decomposition_strategy(
            complexity_causes, total_score, context
        )
        
        # Generate decomposition opportunities
        decomposition_opportunities = _identify_decomposition_opportunities(
            guideline, complexity_causes, context
        )
        
        # Assess intervention urgency
        intervention_urgency = _assess_intervention_urgency(
            complexity_level, complexity_causes, context
        )
        
        # Create complexity analysis result
        analysis = ComplexityAnalysis(
            complexity_score=total_score,
            complexity_level=complexity_level,
            exceeds_threshold=exceeds_threshold,
            complexity_causes=complexity_causes,
            analysis_context=context,
            recommended_strategy=recommended_strategy,
            decomposition_opportunities=decomposition_opportunities,
            confidence_level=_calculate_confidence_level(guideline, complexity_factors),
            intervention_urgency=intervention_urgency,
            risk_assessment=_generate_risk_assessment(complexity_level, complexity_causes)
        )
        
        # Store analysis if state manager available
        if state_manager:
            await _store_complexity_analysis(state_manager, analysis, context)
        
        # Track health metrics if tracker available
        if health_tracker:
            await _track_complexity_health(health_tracker, analysis)
        
        logger.info(f"Guideline complexity analysis complete: score={total_score:.2f}, level={complexity_level.value}")
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing guideline complexity: {str(e)}")
        
        # Return safe fallback analysis
        return ComplexityAnalysis(
            complexity_score=50.0,
            complexity_level=ComplexityLevel.MEDIUM,
            exceeds_threshold=False,
            complexity_causes=[],
            analysis_context=context,
            confidence_level=0.1,
            risk_assessment=f"Analysis failed: {str(e)}"
        )


async def analyze_feature_complexity(
    feature_spec: Dict[str, Any],
    feature_context: Dict[str, Any],
    state_manager=None,
    health_tracker=None,
    thresholds: Optional[ComplexityThreshold] = None
) -> ComplexityAnalysis:
    """
    Phase 3 feature complexity analysis for Natural Selection support.
    
    Args:
        feature_spec: Feature specification to analyze
        feature_context: Additional context about the feature
        state_manager: Optional state manager for persistence
        health_tracker: Optional health tracker for monitoring
        thresholds: Optional custom complexity thresholds
        
    Returns:
        ComplexityAnalysis focused on feature-specific complexity indicators
    """
    try:
        if thresholds is None:
            thresholds = ComplexityThreshold()
            
        logger.info("Analyzing feature complexity for Natural Selection support")
        
        complexity_factors = []
        complexity_causes = []
        
        # Feature scope complexity
        scope_score = _analyze_feature_scope_complexity(feature_spec)
        complexity_factors.append(("feature_scope", scope_score))
        
        # Feature responsibility complexity
        responsibility_score = _analyze_feature_responsibility_complexity(feature_spec)
        complexity_factors.append(("feature_responsibilities", responsibility_score))
        if responsibility_score > 70:
            complexity_causes.append(ComplexityCause.MULTIPLE_RESPONSIBILITIES)
        
        # Feature dependency complexity
        dependency_score = _analyze_feature_dependency_complexity(feature_spec, feature_context)
        complexity_factors.append(("feature_dependencies", dependency_score))
        if dependency_score > 65:
            complexity_causes.append(ComplexityCause.HIGH_DEPENDENCY_COUNT)
        
        # Cross-cutting concerns
        cross_cutting_score = _analyze_cross_cutting_concerns(feature_spec)
        complexity_factors.append(("cross_cutting", cross_cutting_score))
        if cross_cutting_score > 60:
            complexity_causes.append(ComplexityCause.CROSS_CUTTING_CONCERNS)
        
        # Implementation breadth
        implementation_score = _analyze_implementation_breadth(feature_spec)
        complexity_factors.append(("implementation", implementation_score))
        if implementation_score > 75:
            complexity_causes.append(ComplexityCause.BROAD_IMPLEMENTATION_SCOPE)
        
        # Calculate total complexity score
        total_score = _calculate_weighted_complexity_score(complexity_factors)
        
        # Determine complexity level and recommendations with feature-specific thresholds
        complexity_level = thresholds.get_level(total_score, "phase_three_feature")
        # For features, trigger decomposition at MEDIUM level and above
        exceeds_threshold = complexity_level in [ComplexityLevel.MEDIUM, ComplexityLevel.HIGH, ComplexityLevel.CRITICAL]
        
        recommended_strategy = _determine_feature_decomposition_strategy(complexity_causes, total_score)
        decomposition_opportunities = _identify_feature_decomposition_opportunities(feature_spec, complexity_causes)
        
        analysis = ComplexityAnalysis(
            complexity_score=total_score,
            complexity_level=complexity_level,
            exceeds_threshold=exceeds_threshold,
            complexity_causes=complexity_causes,
            analysis_context="phase_three_feature",
            recommended_strategy=recommended_strategy,
            decomposition_opportunities=decomposition_opportunities,
            confidence_level=_calculate_feature_confidence_level(feature_spec, complexity_factors),
            intervention_urgency=_assess_feature_intervention_urgency(complexity_level, complexity_causes),
            risk_assessment=_generate_feature_risk_assessment(complexity_level, complexity_causes)
        )
        
        # Store and track as before
        if state_manager:
            await _store_complexity_analysis(state_manager, analysis, "phase_three_feature")
        if health_tracker:
            await _track_complexity_health(health_tracker, analysis)
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing feature complexity: {str(e)}")
        return ComplexityAnalysis(
            complexity_score=50.0,
            complexity_level=ComplexityLevel.MEDIUM,
            exceeds_threshold=False,
            complexity_causes=[],
            analysis_context="phase_three_feature",
            confidence_level=0.1
        )


async def analyze_component_complexity(
    component_spec: Dict[str, Any],
    component_context: Dict[str, Any],
    state_manager=None,
    health_tracker=None,
    thresholds: Optional[ComplexityThreshold] = None
) -> ComplexityAnalysis:
    """
    Phase 2 component complexity analysis.
    
    Args:
        component_spec: Component specification to analyze
        component_context: Additional context about the component
        state_manager: Optional state manager for persistence
        health_tracker: Optional health tracker for monitoring
        thresholds: Optional custom complexity thresholds
        
    Returns:
        ComplexityAnalysis focused on component-specific complexity indicators
    """
    try:
        if thresholds is None:
            thresholds = ComplexityThreshold()
            
        logger.info("Analyzing component complexity for Phase 2 support")
        
        # Similar structure to feature analysis but focused on component concerns
        complexity_factors = []
        complexity_causes = []
        
        # Component architecture complexity
        arch_score = _analyze_component_architecture_complexity(component_spec)
        complexity_factors.append(("architecture", arch_score))
        
        # Interface complexity
        interface_score = _analyze_component_interface_complexity(component_spec)
        complexity_factors.append(("interfaces", interface_score))
        
        # State management complexity
        state_score = _analyze_component_state_complexity(component_spec)
        complexity_factors.append(("state_management", state_score))
        
        # Calculate and return analysis similar to feature analysis
        total_score = _calculate_weighted_complexity_score(complexity_factors)
        complexity_level = thresholds.get_level(total_score)
        exceeds_threshold = complexity_level in [ComplexityLevel.HIGH, ComplexityLevel.CRITICAL]
        
        return ComplexityAnalysis(
            complexity_score=total_score,
            complexity_level=complexity_level,
            exceeds_threshold=exceeds_threshold,
            complexity_causes=complexity_causes,
            analysis_context="phase_two_component",
            confidence_level=_calculate_component_confidence_level(component_spec, complexity_factors)
        )
        
    except Exception as e:
        logger.error(f"Error analyzing component complexity: {str(e)}")
        return ComplexityAnalysis(
            complexity_score=50.0,
            complexity_level=ComplexityLevel.MEDIUM,
            exceeds_threshold=False,
            complexity_causes=[],
            analysis_context="phase_two_component",
            confidence_level=0.1
        )


async def detect_system_complexity_hotspots(
    system_state: Dict[str, Any],
    state_manager=None,
    health_tracker=None
) -> SystemComplexitySnapshot:
    """
    System-wide complexity analysis across all phases.
    Identifies areas where complexity is accumulating.
    
    Args:
        system_state: Current system state across phases
        state_manager: Optional state manager for persistence
        health_tracker: Optional health tracker for monitoring
        
    Returns:
        SystemComplexitySnapshot with hotspots and recommendations
    """
    try:
        logger.info("Detecting system-wide complexity hotspots")
        
        # Analyze complexity across different phases
        phase_scores = {}
        complexity_hotspots = []
        
        # Phase 1 complexity (guidelines)
        if "phase_one" in system_state:
            phase_one_score = await _analyze_phase_one_complexity(system_state["phase_one"])
            phase_scores["phase_one"] = phase_one_score
            if phase_one_score > 70:
                complexity_hotspots.append({
                    "phase": "phase_one",
                    "score": phase_one_score,
                    "type": "guideline_complexity",
                    "description": "High complexity in foundational guidelines"
                })
        
        # Phase 2 complexity (components)
        if "phase_two" in system_state:
            phase_two_score = await _analyze_phase_two_complexity(system_state["phase_two"])
            phase_scores["phase_two"] = phase_two_score
            if phase_two_score > 70:
                complexity_hotspots.append({
                    "phase": "phase_two",
                    "score": phase_two_score,
                    "type": "component_complexity",
                    "description": "High complexity in component architecture"
                })
        
        # Phase 3 complexity (features)
        if "phase_three" in system_state:
            phase_three_score = await _analyze_phase_three_complexity(system_state["phase_three"])
            phase_scores["phase_three"] = phase_three_score
            if phase_three_score > 70:
                complexity_hotspots.append({
                    "phase": "phase_three",
                    "score": phase_three_score,
                    "type": "feature_complexity",
                    "description": "High complexity in feature implementations"
                })
        
        # Calculate total system complexity
        total_score = sum(phase_scores.values()) / len(phase_scores) if phase_scores else 0
        
        # Determine complexity trend
        trending_complexity = await _determine_complexity_trend(state_manager, total_score)
        
        # Generate recommendations
        recommended_interventions = _generate_system_interventions(complexity_hotspots, phase_scores)
        priority_areas = _identify_priority_areas(complexity_hotspots)
        
        snapshot = SystemComplexitySnapshot(
            total_complexity_score=total_score,
            phase_complexity_scores=phase_scores,
            complexity_hotspots=complexity_hotspots,
            trending_complexity=trending_complexity,
            recommended_interventions=recommended_interventions,
            priority_areas=priority_areas
        )
        
        # Store snapshot if state manager available
        if state_manager:
            await _store_complexity_snapshot(state_manager, snapshot)
        
        return snapshot
        
    except Exception as e:
        logger.error(f"Error detecting system complexity hotspots: {str(e)}")
        return SystemComplexitySnapshot(
            total_complexity_score=0.0,
            phase_complexity_scores={},
            complexity_hotspots=[],
            trending_complexity="unknown"
        )


# Helper functions for complexity analysis

def _analyze_structure_complexity(guideline: Dict[str, Any]) -> float:
    """Analyze structural complexity of a guideline."""
    score = 0.0
    
    # Count nested levels
    def count_depth(obj, depth=0):
        if isinstance(obj, dict):
            return max([count_depth(v, depth + 1) for v in obj.values()], default=depth)
        elif isinstance(obj, list):
            return max([count_depth(item, depth + 1) for item in obj], default=depth)
        return depth
    
    depth = count_depth(guideline)
    score += min(depth * 10, 50)  # Cap at 50 points for depth
    
    # Count total keys/fields
    def count_keys(obj):
        if isinstance(obj, dict):
            return len(obj) + sum(count_keys(v) for v in obj.values())
        elif isinstance(obj, list):
            return sum(count_keys(item) for item in obj)
        return 0
    
    key_count = count_keys(guideline)
    score += min(key_count * 2, 40)  # Cap at 40 points for key count
    
    return min(score, 100)


def _analyze_dependency_complexity(guideline: Dict[str, Any]) -> float:
    """Analyze dependency complexity."""
    dependencies = guideline.get("dependencies", [])
    if isinstance(dependencies, dict):
        dependencies = list(dependencies.values())
    elif not isinstance(dependencies, list):
        dependencies = []
    
    # Base score on dependency count
    dep_count = len(dependencies)
    score = min(dep_count * 15, 80)
    
    # Add complexity for circular or complex dependencies
    if dep_count > 5:
        score += 20
    
    return min(score, 100)


def _analyze_scope_complexity(guideline: Dict[str, Any], context: str) -> float:
    """Analyze scope complexity based on context."""
    score = 0.0
    
    # Check for multiple scope indicators
    scope_indicators = [
        "components", "features", "responsibilities", "requirements",
        "interfaces", "subsystems", "modules", "services"
    ]
    
    scope_count = 0
    for indicator in scope_indicators:
        if indicator in guideline:
            item = guideline[indicator]
            if isinstance(item, (list, dict)):
                if isinstance(item, list):
                    scope_count += len(item)
                else:
                    scope_count += len(item.keys())
    
    score = min(scope_count * 8, 80)
    
    # Context-specific adjustments
    if context == "phase_one" and scope_count > 8:
        score += 20  # Phase 1 should be more focused
    
    return min(score, 100)


def _analyze_responsibility_complexity(guideline: Dict[str, Any]) -> float:
    """Analyze responsibility complexity."""
    score = 0.0
    
    # Look for responsibility indicators
    responsibility_fields = [
        "responsibilities", "functions", "capabilities", "operations",
        "tasks", "duties", "concerns", "roles"
    ]
    
    total_responsibilities = 0
    for field in responsibility_fields:
        if field in guideline:
            item = guideline[field]
            if isinstance(item, list):
                total_responsibilities += len(item)
            elif isinstance(item, dict):
                total_responsibilities += len(item.keys())
            elif isinstance(item, str):
                # Count sentences or major concepts
                total_responsibilities += len(item.split('.'))
    
    score = min(total_responsibilities * 12, 100)
    return score


def _analyze_integration_complexity(guideline: Dict[str, Any], context: str) -> float:
    """Analyze integration complexity."""
    score = 0.0
    
    # Check for integration indicators
    integration_fields = [
        "integrations", "connections", "interactions", "communications",
        "apis", "interfaces", "protocols", "channels"
    ]
    
    integration_count = 0
    for field in integration_fields:
        if field in guideline:
            item = guideline[field]
            if isinstance(item, (list, dict)):
                if isinstance(item, list):
                    integration_count += len(item)
                else:
                    integration_count += len(item.keys())
    
    score = min(integration_count * 20, 100)
    return score


def _calculate_weighted_complexity_score(complexity_factors: List[tuple]) -> float:
    """Calculate weighted complexity score from factors."""
    if not complexity_factors:
        return 0.0
    
    # Weights for different factors
    weights = {
        "structure": 0.2,
        "dependencies": 0.25,
        "scope": 0.25,
        "responsibilities": 0.2,
        "integration": 0.1,
        "feature_scope": 0.3,
        "feature_responsibilities": 0.25,
        "feature_dependencies": 0.2,
        "cross_cutting": 0.15,
        "implementation": 0.1,
        "architecture": 0.4,
        "interfaces": 0.3,
        "state_management": 0.3
    }
    
    total_weighted_score = 0.0
    total_weight = 0.0
    
    for factor_name, score in complexity_factors:
        weight = weights.get(factor_name, 0.1)  # Default weight
        total_weighted_score += score * weight
        total_weight += weight
    
    return min(total_weighted_score / total_weight if total_weight > 0 else 0, 100)


def _determine_decomposition_strategy(
    complexity_causes: List[ComplexityCause],
    total_score: float,
    context: str
) -> Optional[DecompositionStrategy]:
    """Determine the best decomposition strategy based on complexity causes."""
    if not complexity_causes or total_score < 70:
        return None
    
    # Priority-based strategy selection
    if ComplexityCause.MULTIPLE_RESPONSIBILITIES in complexity_causes:
        return DecompositionStrategy.RESPONSIBILITY_EXTRACTION
    elif ComplexityCause.HIGH_DEPENDENCY_COUNT in complexity_causes:
        return DecompositionStrategy.DEPENDENCY_REDUCTION
    elif ComplexityCause.CROSS_CUTTING_CONCERNS in complexity_causes:
        return DecompositionStrategy.CONCERN_ISOLATION
    elif ComplexityCause.BROAD_IMPLEMENTATION_SCOPE in complexity_causes:
        return DecompositionStrategy.SCOPE_NARROWING
    else:
        return DecompositionStrategy.FUNCTIONAL_SEPARATION


def _identify_decomposition_opportunities(
    guideline: Dict[str, Any],
    complexity_causes: List[ComplexityCause],
    context: str
) -> List[str]:
    """Identify specific decomposition opportunities."""
    opportunities = []
    
    if ComplexityCause.MULTIPLE_RESPONSIBILITIES in complexity_causes:
        opportunities.append("Split into single-responsibility components")
    
    if ComplexityCause.HIGH_DEPENDENCY_COUNT in complexity_causes:
        opportunities.append("Reduce external dependencies through abstraction")
    
    if ComplexityCause.BROAD_IMPLEMENTATION_SCOPE in complexity_causes:
        opportunities.append("Narrow implementation scope to core functionality")
    
    if ComplexityCause.INTEGRATION_COMPLEXITY in complexity_causes:
        opportunities.append("Simplify integration patterns and interfaces")
    
    return opportunities


def _assess_intervention_urgency(
    complexity_level: ComplexityLevel,
    complexity_causes: List[ComplexityCause],
    context: str
) -> str:
    """Assess the urgency of intervention needed."""
    if complexity_level == ComplexityLevel.CRITICAL:
        return "critical"
    elif complexity_level == ComplexityLevel.HIGH:
        if context == "phase_one":
            return "high"  # Phase 1 complexity is more critical
        return "high"
    elif complexity_level == ComplexityLevel.MEDIUM and len(complexity_causes) > 2:
        return "normal"
    else:
        return "low"


def _generate_risk_assessment(
    complexity_level: ComplexityLevel,
    complexity_causes: List[ComplexityCause]
) -> str:
    """Generate a risk assessment for the complexity level."""
    if complexity_level == ComplexityLevel.CRITICAL:
        return "Critical complexity level poses significant risks to development success and maintainability"
    elif complexity_level == ComplexityLevel.HIGH:
        return "High complexity level may lead to development delays and maintenance issues"
    elif complexity_level == ComplexityLevel.MEDIUM:
        return "Medium complexity level is manageable but should be monitored"
    else:
        return "Low complexity level poses minimal risk"


def _calculate_confidence_level(guideline: Dict[str, Any], complexity_factors: List[tuple]) -> float:
    """Calculate confidence level in the analysis."""
    # Base confidence on data completeness and factor coverage
    base_confidence = 0.7
    
    # Increase confidence with more factors analyzed
    factor_bonus = min(len(complexity_factors) * 0.05, 0.2)
    
    # Increase confidence with richer data
    data_richness = min(len(str(guideline)) / 1000, 0.1)
    
    return min(base_confidence + factor_bonus + data_richness, 1.0)


# Feature-specific analysis helpers

def _analyze_feature_scope_complexity(feature_spec: Dict[str, Any]) -> float:
    """Analyze feature scope complexity."""
    scope_indicators = feature_spec.get("scope", {})
    if isinstance(scope_indicators, str):
        return min(len(scope_indicators.split()) * 3, 100)
    elif isinstance(scope_indicators, (list, dict)):
        return min(len(scope_indicators) * 20, 100)
    elif isinstance(scope_indicators, dict):
        # Count nested scope elements
        total_scope_items = 0
        for key, value in scope_indicators.items():
            if isinstance(value, list):
                total_scope_items += len(value)
            elif isinstance(value, bool) and value:
                total_scope_items += 1
            elif isinstance(value, dict):
                total_scope_items += len(value)
        return min(total_scope_items * 8, 100)
    return 35  # Default moderate score


def _analyze_feature_responsibility_complexity(feature_spec: Dict[str, Any]) -> float:
    """Analyze feature responsibility complexity."""
    responsibilities = feature_spec.get("responsibilities", [])
    if isinstance(responsibilities, list):
        return min(len(responsibilities) * 25, 100)  # Increased multiplier
    elif isinstance(responsibilities, str):
        return min(len(responsibilities.split('.')) * 20, 100)  # Increased multiplier
    return 30


def _analyze_feature_dependency_complexity(feature_spec: Dict[str, Any], feature_context: Dict[str, Any]) -> float:
    """Analyze feature dependency complexity."""
    dependencies = feature_spec.get("dependencies", [])
    context_deps = feature_context.get("related_features", [])
    
    total_deps = len(dependencies) + len(context_deps)
    return min(total_deps * 22, 100)  # Increased multiplier


def _analyze_cross_cutting_concerns(feature_spec: Dict[str, Any]) -> float:
    """Analyze cross-cutting concerns in feature."""
    cross_cutting_indicators = [
        "logging", "security", "caching", "monitoring", "validation",
        "error_handling", "performance", "scalability", "authentication",
        "authorization", "auditing"
    ]
    
    found_concerns = 0
    spec_text = str(feature_spec).lower()
    
    # Check for explicit cross-cutting concerns in scope
    scope = feature_spec.get("scope", {})
    if isinstance(scope, dict):
        cross_cutting_list = scope.get("cross_cutting_concerns", [])
        if isinstance(cross_cutting_list, list):
            found_concerns += len(cross_cutting_list)
    
    # Check for keywords in text
    for concern in cross_cutting_indicators:
        if concern in spec_text:
            found_concerns += 1
    
    return min(found_concerns * 18, 100)  # Increased multiplier


def _analyze_implementation_breadth(feature_spec: Dict[str, Any]) -> float:
    """Analyze implementation breadth of feature."""
    implementation_areas = [
        "frontend", "backend", "database", "api", "ui", "service",
        "integration", "testing", "deployment", "configuration"
    ]
    
    areas_covered = 0
    spec_text = str(feature_spec).lower()
    
    # Check for explicit implementation areas
    implementation = feature_spec.get("implementation", {})
    if isinstance(implementation, dict):
        for area in implementation_areas:
            if implementation.get(area, False):
                areas_covered += 1
    
    # Also check in text
    for area in implementation_areas:
        if area in spec_text:
            areas_covered += 1
    
    return min(areas_covered * 15, 100)  # Increased multiplier


def _determine_feature_decomposition_strategy(
    complexity_causes: List[ComplexityCause],
    total_score: float
) -> Optional[DecompositionStrategy]:
    """Determine decomposition strategy for features."""
    if total_score < 45:  # Aligned with feature medium threshold
        return None
    
    # Feature-specific strategy logic
    if ComplexityCause.CROSS_CUTTING_CONCERNS in complexity_causes:
        return DecompositionStrategy.CONCERN_ISOLATION
    elif ComplexityCause.MULTIPLE_RESPONSIBILITIES in complexity_causes:
        return DecompositionStrategy.FUNCTIONAL_SEPARATION
    else:
        return DecompositionStrategy.SCOPE_NARROWING


def _identify_feature_decomposition_opportunities(
    feature_spec: Dict[str, Any],
    complexity_causes: List[ComplexityCause]
) -> List[str]:
    """Identify feature-specific decomposition opportunities."""
    opportunities = []
    
    if ComplexityCause.CROSS_CUTTING_CONCERNS in complexity_causes:
        opportunities.append("Extract cross-cutting concerns into separate utilities")
    
    if ComplexityCause.MULTIPLE_RESPONSIBILITIES in complexity_causes:
        opportunities.append("Split feature into focused sub-features")
    
    return opportunities


def _calculate_feature_confidence_level(feature_spec: Dict[str, Any], complexity_factors: List[tuple]) -> float:
    """Calculate confidence in feature analysis."""
    return min(0.8 + len(complexity_factors) * 0.03, 1.0)


def _assess_feature_intervention_urgency(
    complexity_level: ComplexityLevel,
    complexity_causes: List[ComplexityCause]
) -> str:
    """Assess intervention urgency for features."""
    if complexity_level == ComplexityLevel.CRITICAL:
        return "critical"
    elif complexity_level == ComplexityLevel.HIGH:
        return "high"
    else:
        return "normal"


def _generate_feature_risk_assessment(
    complexity_level: ComplexityLevel,
    complexity_causes: List[ComplexityCause]
) -> str:
    """Generate risk assessment for features."""
    if complexity_level == ComplexityLevel.CRITICAL:
        return "Feature complexity too high for effective Natural Selection optimization"
    elif complexity_level == ComplexityLevel.HIGH:
        return "Feature complexity may reduce Natural Selection effectiveness"
    else:
        return "Feature complexity manageable for Natural Selection"


# Component-specific analysis helpers

def _analyze_component_architecture_complexity(component_spec: Dict[str, Any]) -> float:
    """Analyze component architecture complexity."""
    # Simplified for now - can be expanded based on actual component structure
    return 40.0


def _analyze_component_interface_complexity(component_spec: Dict[str, Any]) -> float:
    """Analyze component interface complexity."""
    return 35.0


def _analyze_component_state_complexity(component_spec: Dict[str, Any]) -> float:
    """Analyze component state management complexity."""
    return 30.0


def _calculate_component_confidence_level(component_spec: Dict[str, Any], complexity_factors: List[tuple]) -> float:
    """Calculate confidence in component analysis."""
    return 0.75


# System-wide analysis helpers

async def _analyze_phase_one_complexity(phase_one_state: Dict[str, Any]) -> float:
    """Analyze overall Phase 1 complexity."""
    # Aggregate complexity from all Phase 1 components
    return 45.0  # Placeholder


async def _analyze_phase_two_complexity(phase_two_state: Dict[str, Any]) -> float:
    """Analyze overall Phase 2 complexity."""
    return 50.0  # Placeholder


async def _analyze_phase_three_complexity(phase_three_state: Dict[str, Any]) -> float:
    """Analyze overall Phase 3 complexity."""
    return 55.0  # Placeholder


async def _determine_complexity_trend(state_manager, current_score: float) -> str:
    """Determine if complexity is trending up, down, or stable."""
    if not state_manager:
        return "unknown"
    
    # Get historical scores and compare
    # Simplified for now
    return "stable"


def _generate_system_interventions(complexity_hotspots: List[Dict[str, Any]], phase_scores: Dict[str, float]) -> List[Dict[str, Any]]:
    """Generate system-wide intervention recommendations."""
    interventions = []
    
    for hotspot in complexity_hotspots:
        if hotspot["score"] > 80:
            interventions.append({
                "type": "urgent_decomposition",
                "target": hotspot["phase"],
                "description": f"Urgent complexity reduction needed in {hotspot['phase']}"
            })
    
    return interventions


def _identify_priority_areas(complexity_hotspots: List[Dict[str, Any]]) -> List[str]:
    """Identify priority areas for intervention."""
    return [hotspot["phase"] for hotspot in complexity_hotspots if hotspot["score"] > 75]


# Storage and tracking helpers

async def _store_complexity_analysis(state_manager, analysis: ComplexityAnalysis, context: str):
    """Store complexity analysis in state manager."""
    try:
        key = f"fire_agent:complexity_analysis:{context}:{datetime.now().isoformat()}"
        await state_manager.set_state(key, analysis.__dict__, "STATE")
    except Exception as e:
        logger.warning(f"Failed to store complexity analysis: {e}")


async def _track_complexity_health(health_tracker, analysis: ComplexityAnalysis):
    """Track complexity metrics in health tracker."""
    try:
        # Track basic metrics
        health_tracker.track_metric("fire_agent_complexity_score", analysis.complexity_score)
        health_tracker.track_metric("fire_agent_analysis_count", 1)
    except Exception as e:
        logger.warning(f"Failed to track complexity health: {e}")


async def _store_complexity_snapshot(state_manager, snapshot: SystemComplexitySnapshot):
    """Store system complexity snapshot."""
    try:
        key = f"fire_agent:system_snapshot:{datetime.now().isoformat()}"
        await state_manager.set_state(key, snapshot.__dict__, "STATE")
    except Exception as e:
        logger.warning(f"Failed to store complexity snapshot: {e}")