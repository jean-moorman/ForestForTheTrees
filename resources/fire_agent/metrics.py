"""
Fire Agent metrics and assessment utilities.

This module provides utility functions for calculating complexity scores,
identifying complexity causes, and assessing the impact of decomposition operations.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from .models import (
    ComplexityAnalysis,
    DecompositionResult,
    ComplexityCause,
    ComplexityLevel,
    ComplexityThreshold
)

logger = logging.getLogger(__name__)


def calculate_complexity_score(
    data_structure: Dict[str, Any],
    context: str = "general",
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Calculate complexity score for any data structure.
    
    This is a utility function that can be used independently of the
    main complexity analysis workflow.
    
    Args:
        data_structure: The data structure to analyze
        context: Context for scoring (affects weight distribution)
        weights: Optional custom weights for different factors
        
    Returns:
        Complexity score from 0-100
    """
    try:
        if not data_structure:
            return 0.0
        
        # Default weights based on context
        if weights is None:
            weights = _get_default_weights(context)
        
        # Calculate individual complexity factors
        structure_score = _calculate_structure_score(data_structure)
        depth_score = _calculate_depth_score(data_structure)
        dependency_score = _calculate_dependency_score(data_structure)
        scope_score = _calculate_scope_score(data_structure)
        interface_score = _calculate_interface_score(data_structure)
        
        # Apply weights and calculate total
        weighted_score = (
            structure_score * weights.get("structure", 0.2) +
            depth_score * weights.get("depth", 0.2) +
            dependency_score * weights.get("dependencies", 0.25) +
            scope_score * weights.get("scope", 0.2) +
            interface_score * weights.get("interfaces", 0.15)
        )
        
        return min(weighted_score, 100.0)
        
    except Exception as e:
        logger.error(f"Error calculating complexity score: {e}")
        return 50.0  # Return moderate score on error


def identify_complexity_causes(
    data_structure: Dict[str, Any],
    complexity_score: float,
    context: str = "general",
    thresholds: Optional[Dict[str, float]] = None
) -> List[ComplexityCause]:
    """
    Identify specific causes of complexity in a data structure.
    
    Args:
        data_structure: The data structure to analyze
        complexity_score: Overall complexity score
        context: Context for analysis
        thresholds: Optional custom thresholds for cause detection
        
    Returns:
        List of identified complexity causes
    """
    try:
        if not data_structure:
            return []
        
        # Default thresholds for cause detection
        if thresholds is None:
            thresholds = _get_default_cause_thresholds(context)
        
        causes = []
        
        # Check for multiple responsibilities
        if _has_multiple_responsibilities_metric(data_structure, thresholds.get("responsibilities", 60)):
            causes.append(ComplexityCause.MULTIPLE_RESPONSIBILITIES)
        
        # Check for high dependency count
        if _has_high_dependency_count_metric(data_structure, thresholds.get("dependencies", 65)):
            causes.append(ComplexityCause.HIGH_DEPENDENCY_COUNT)
        
        # Check for cross-cutting concerns
        if _has_cross_cutting_concerns_metric(data_structure, thresholds.get("cross_cutting", 55)):
            causes.append(ComplexityCause.CROSS_CUTTING_CONCERNS)
        
        # Check for broad implementation scope
        if _has_broad_scope_metric(data_structure, thresholds.get("scope", 70)):
            causes.append(ComplexityCause.BROAD_IMPLEMENTATION_SCOPE)
        
        # Check for conflicting requirements
        if _has_conflicting_requirements_metric(data_structure, thresholds.get("conflicts", 50)):
            causes.append(ComplexityCause.CONFLICTING_REQUIREMENTS)
        
        # Check for unclear boundaries
        if _has_unclear_boundaries_metric(data_structure, thresholds.get("boundaries", 45)):
            causes.append(ComplexityCause.UNCLEAR_BOUNDARIES)
        
        # Check for nested complexity
        if _has_nested_complexity_metric(data_structure, thresholds.get("nested", 60)):
            causes.append(ComplexityCause.NESTED_COMPLEXITY)
        
        # Check for integration complexity
        if _has_integration_complexity_metric(data_structure, thresholds.get("integration", 65)):
            causes.append(ComplexityCause.INTEGRATION_COMPLEXITY)
        
        return causes
        
    except Exception as e:
        logger.error(f"Error identifying complexity causes: {e}")
        return []


def assess_decomposition_impact(
    original_analysis: ComplexityAnalysis,
    decomposition_result: DecompositionResult,
    target_elements: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Assess the impact and effectiveness of a decomposition operation.
    
    Args:
        original_analysis: Original complexity analysis before decomposition
        decomposition_result: Result of decomposition operation
        target_elements: Optional target elements for detailed assessment
        
    Returns:
        Assessment report with metrics and recommendations
    """
    try:
        assessment = {
            "overall_effectiveness": "unknown",
            "complexity_reduction": {
                "absolute": 0.0,
                "percentage": 0.0,
                "meets_target": False
            },
            "decomposition_quality": {
                "elements_created": 0,
                "average_element_complexity": 0.0,
                "cohesion_score": 0.0,
                "coupling_score": 0.0
            },
            "success_metrics": {},
            "recommendations": [],
            "lessons_learned": []
        }
        
        # Calculate complexity reduction
        if decomposition_result.success and decomposition_result.complexity_reduction:
            abs_reduction = decomposition_result.complexity_reduction
            pct_reduction = (abs_reduction / original_analysis.complexity_score * 100) if original_analysis.complexity_score > 0 else 0
            
            assessment["complexity_reduction"]["absolute"] = abs_reduction
            assessment["complexity_reduction"]["percentage"] = pct_reduction
            assessment["complexity_reduction"]["meets_target"] = abs_reduction >= 15.0  # 15-point reduction target
            
            # Determine overall effectiveness
            if pct_reduction >= 30:
                assessment["overall_effectiveness"] = "high"
            elif pct_reduction >= 15:
                assessment["overall_effectiveness"] = "medium"
            elif pct_reduction > 0:
                assessment["overall_effectiveness"] = "low"
            else:
                assessment["overall_effectiveness"] = "ineffective"
        
        # Assess decomposition quality
        elements_created = 0
        if decomposition_result.decomposed_features:
            elements_created = len(decomposition_result.decomposed_features)
        elif decomposition_result.simplified_components:
            elements_created = len(decomposition_result.simplified_components)
        elif decomposition_result.decomposed_elements:
            elements_created = len(decomposition_result.decomposed_elements)
        
        assessment["decomposition_quality"]["elements_created"] = elements_created
        
        # Calculate average element complexity if new score available
        if decomposition_result.new_complexity_score:
            assessment["decomposition_quality"]["average_element_complexity"] = decomposition_result.new_complexity_score
        
        # Assess cohesion and coupling (simplified metrics)
        cohesion_score = _assess_cohesion(decomposition_result)
        coupling_score = _assess_coupling(decomposition_result)
        
        assessment["decomposition_quality"]["cohesion_score"] = cohesion_score
        assessment["decomposition_quality"]["coupling_score"] = coupling_score
        
        # Include success metrics from decomposition result
        assessment["success_metrics"] = decomposition_result.success_metrics
        
        # Generate recommendations based on assessment
        recommendations = _generate_impact_recommendations(
            assessment, original_analysis, decomposition_result
        )
        assessment["recommendations"] = recommendations
        
        # Include lessons learned from decomposition
        assessment["lessons_learned"] = decomposition_result.lessons_learned
        
        return assessment
        
    except Exception as e:
        logger.error(f"Error assessing decomposition impact: {e}")
        return {
            "overall_effectiveness": "error",
            "error": str(e),
            "recommendations": ["Manual review recommended due to assessment error"]
        }


def calculate_system_complexity_trend(
    historical_scores: List[Tuple[datetime, float]],
    time_window: timedelta = timedelta(days=7)
) -> Dict[str, Any]:
    """
    Calculate system complexity trend over time.
    
    Args:
        historical_scores: List of (timestamp, complexity_score) tuples
        time_window: Time window for trend calculation
        
    Returns:
        Trend analysis with direction, rate, and projections
    """
    try:
        if len(historical_scores) < 2:
            return {
                "trend_direction": "unknown",
                "trend_rate": 0.0,
                "confidence": 0.0,
                "projection": None
            }
        
        # Filter scores within time window
        cutoff_time = datetime.now() - time_window
        recent_scores = [(ts, score) for ts, score in historical_scores if ts >= cutoff_time]
        
        if len(recent_scores) < 2:
            return {
                "trend_direction": "insufficient_data",
                "trend_rate": 0.0,
                "confidence": 0.0,
                "projection": None
            }
        
        # Calculate trend using simple linear regression
        timestamps = [(ts - recent_scores[0][0]).total_seconds() for ts, _ in recent_scores]
        scores = [score for _, score in recent_scores]
        
        # Calculate slope (trend rate)
        n = len(timestamps)
        sum_x = sum(timestamps)
        sum_y = sum(scores)
        sum_xy = sum(x * y for x, y in zip(timestamps, scores))
        sum_x2 = sum(x * x for x in timestamps)
        
        if n * sum_x2 - sum_x * sum_x == 0:
            trend_rate = 0.0
        else:
            trend_rate = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # Determine trend direction
        if abs(trend_rate) < 0.01:  # Very small change
            trend_direction = "stable"
        elif trend_rate > 0:
            trend_direction = "increasing"
        else:
            trend_direction = "decreasing"
        
        # Calculate confidence based on data consistency
        confidence = _calculate_trend_confidence(recent_scores, trend_rate)
        
        # Project future complexity
        projection = _project_future_complexity(recent_scores, trend_rate)
        
        return {
            "trend_direction": trend_direction,
            "trend_rate": trend_rate,
            "confidence": confidence,
            "projection": projection,
            "data_points": len(recent_scores),
            "time_span_hours": (recent_scores[-1][0] - recent_scores[0][0]).total_seconds() / 3600
        }
        
    except Exception as e:
        logger.error(f"Error calculating complexity trend: {e}")
        return {
            "trend_direction": "error",
            "trend_rate": 0.0,
            "confidence": 0.0,
            "error": str(e)
        }


def generate_complexity_recommendations(
    analysis: ComplexityAnalysis,
    decomposition_result: Optional[DecompositionResult] = None,
    system_context: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Generate actionable recommendations based on complexity analysis.
    
    Args:
        analysis: Complexity analysis results
        decomposition_result: Optional decomposition result for context
        system_context: Optional system context for targeted recommendations
        
    Returns:
        List of recommendation dictionaries with priority and actions
    """
    try:
        recommendations = []
        
        # High-level recommendations based on complexity level
        if analysis.complexity_level == ComplexityLevel.CRITICAL:
            recommendations.append({
                "priority": "critical",
                "category": "immediate_action",
                "title": "Critical Complexity Intervention Required",
                "description": "Complexity level poses immediate risk to development success",
                "actions": [
                    "Pause current development activities",
                    "Conduct emergency architectural review",
                    "Implement mandatory decomposition before proceeding"
                ],
                "timeline": "immediate"
            })
        
        elif analysis.complexity_level == ComplexityLevel.HIGH:
            recommendations.append({
                "priority": "high",
                "category": "architectural_review",
                "title": "High Complexity Requires Attention",
                "description": "Consider decomposition to prevent development issues",
                "actions": [
                    "Schedule architectural review session",
                    "Evaluate decomposition opportunities",
                    "Consider gradual refactoring approach"
                ],
                "timeline": "within_week"
            })
        
        # Specific recommendations based on complexity causes
        for cause in analysis.complexity_causes:
            if cause == ComplexityCause.MULTIPLE_RESPONSIBILITIES:
                recommendations.append({
                    "priority": "medium",
                    "category": "responsibility_separation",
                    "title": "Separate Multiple Responsibilities",
                    "description": "Extract single responsibilities into focused components",
                    "actions": [
                        "Identify distinct responsibility clusters",
                        "Create focused components for each responsibility",
                        "Implement clear interfaces between components"
                    ],
                    "timeline": "within_sprint"
                })
            
            elif cause == ComplexityCause.HIGH_DEPENDENCY_COUNT:
                recommendations.append({
                    "priority": "medium",
                    "category": "dependency_management",
                    "title": "Reduce Dependency Complexity",
                    "description": "Simplify dependency structure through abstraction",
                    "actions": [
                        "Group related dependencies",
                        "Create abstraction layers for dependency clusters",
                        "Implement dependency injection patterns"
                    ],
                    "timeline": "within_sprint"
                })
            
            elif cause == ComplexityCause.CROSS_CUTTING_CONCERNS:
                recommendations.append({
                    "priority": "medium",
                    "category": "concern_separation",
                    "title": "Isolate Cross-Cutting Concerns",
                    "description": "Extract cross-cutting concerns into separate services",
                    "actions": [
                        "Identify cross-cutting concerns",
                        "Create dedicated service components",
                        "Implement aspect-oriented patterns"
                    ],
                    "timeline": "within_iteration"
                })
            
            elif cause == ComplexityCause.BROAD_IMPLEMENTATION_SCOPE:
                recommendations.append({
                    "priority": "high",
                    "category": "scope_management",
                    "title": "Narrow Implementation Scope",
                    "description": "Focus on core functionality and defer peripheral features",
                    "actions": [
                        "Define MVP scope clearly",
                        "Move peripheral features to future iterations",
                        "Prioritize essential functionality"
                    ],
                    "timeline": "within_sprint"
                })
        
        # Recommendations based on decomposition results
        if decomposition_result:
            if decomposition_result.success:
                recommendations.append({
                    "priority": "low",
                    "category": "validation",
                    "title": "Validate Decomposition Results",
                    "description": "Ensure decomposed elements work effectively together",
                    "actions": [
                        "Test decomposed components independently",
                        "Validate integration points",
                        "Monitor complexity metrics post-decomposition"
                    ],
                    "timeline": "within_sprint"
                })
            else:
                recommendations.append({
                    "priority": "medium",
                    "category": "alternative_approach",
                    "title": "Explore Alternative Complexity Reduction",
                    "description": "Automated decomposition failed, consider manual approaches",
                    "actions": [
                        "Conduct manual architectural review",
                        "Consider different decomposition strategies",
                        "Evaluate if complexity is inherent to requirements"
                    ],
                    "timeline": "within_week"
                })
        
        # Context-specific recommendations
        if system_context:
            context_recommendations = _generate_context_specific_recommendations(
                analysis, system_context
            )
            recommendations.extend(context_recommendations)
        
        # Sort recommendations by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 4))
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating complexity recommendations: {e}")
        return [{
            "priority": "high",
            "category": "error_handling",
            "title": "Manual Review Required",
            "description": f"Automated recommendation generation failed: {str(e)}",
            "actions": ["Conduct manual complexity assessment"],
            "timeline": "immediate"
        }]


# Helper functions for complexity scoring

def _get_default_weights(context: str) -> Dict[str, float]:
    """Get default complexity scoring weights based on context."""
    weights_map = {
        "phase_one": {
            "structure": 0.25,
            "depth": 0.15,
            "dependencies": 0.3,
            "scope": 0.2,
            "interfaces": 0.1
        },
        "phase_two_component": {
            "structure": 0.2,
            "depth": 0.2,
            "dependencies": 0.25,
            "scope": 0.15,
            "interfaces": 0.2
        },
        "phase_three_feature": {
            "structure": 0.15,
            "depth": 0.15,
            "dependencies": 0.2,
            "scope": 0.3,
            "interfaces": 0.2
        },
        "general": {
            "structure": 0.2,
            "depth": 0.2,
            "dependencies": 0.25,
            "scope": 0.2,
            "interfaces": 0.15
        }
    }
    
    return weights_map.get(context, weights_map["general"])


def _calculate_structure_score(data_structure: Dict[str, Any]) -> float:
    """Calculate structural complexity score."""
    if not data_structure:
        return 0.0
    
    # Count total keys recursively
    def count_keys(obj):
        if isinstance(obj, dict):
            return len(obj) + sum(count_keys(v) for v in obj.values())
        elif isinstance(obj, list):
            return sum(count_keys(item) for item in obj)
        return 0
    
    key_count = count_keys(data_structure)
    return min(key_count * 3, 100)


def _calculate_depth_score(data_structure: Dict[str, Any]) -> float:
    """Calculate nesting depth complexity score."""
    def max_depth(obj, current_depth=0):
        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(max_depth(v, current_depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            if not obj:
                return current_depth
            return max(max_depth(item, current_depth + 1) for item in obj)
        return current_depth
    
    depth = max_depth(data_structure)
    return min(depth * 15, 100)


def _calculate_dependency_score(data_structure: Dict[str, Any]) -> float:
    """Calculate dependency complexity score."""
    dependencies = data_structure.get("dependencies", [])
    if isinstance(dependencies, dict):
        dep_count = len(dependencies)
    elif isinstance(dependencies, list):
        dep_count = len(dependencies)
    else:
        dep_count = 1 if dependencies else 0
    
    return min(dep_count * 12, 100)


def _calculate_scope_score(data_structure: Dict[str, Any]) -> float:
    """Calculate scope complexity score."""
    scope_indicators = [
        "scope", "features", "components", "responsibilities",
        "functions", "capabilities", "modules", "services"
    ]
    
    total_scope_items = 0
    for indicator in scope_indicators:
        if indicator in data_structure:
            item = data_structure[indicator]
            if isinstance(item, list):
                total_scope_items += len(item)
            elif isinstance(item, dict):
                total_scope_items += len(item)
            elif isinstance(item, str):
                total_scope_items += len(item.split())
    
    return min(total_scope_items * 5, 100)


def _calculate_interface_score(data_structure: Dict[str, Any]) -> float:
    """Calculate interface complexity score."""
    interface_indicators = [
        "interfaces", "apis", "endpoints", "methods",
        "operations", "protocols", "communications"
    ]
    
    interface_count = 0
    for indicator in interface_indicators:
        if indicator in data_structure:
            item = data_structure[indicator]
            if isinstance(item, (list, dict)):
                interface_count += len(item)
    
    return min(interface_count * 8, 100)


def _get_default_cause_thresholds(context: str) -> Dict[str, float]:
    """Get default thresholds for complexity cause detection."""
    thresholds_map = {
        "phase_one": {
            "responsibilities": 50,
            "dependencies": 60,
            "cross_cutting": 45,
            "scope": 65,
            "conflicts": 40,
            "boundaries": 35,
            "nested": 55,
            "integration": 60
        },
        "phase_three_feature": {
            "responsibilities": 60,
            "dependencies": 65,
            "cross_cutting": 55,
            "scope": 70,
            "conflicts": 50,
            "boundaries": 45,
            "nested": 60,
            "integration": 65
        },
        "general": {
            "responsibilities": 55,
            "dependencies": 60,
            "cross_cutting": 50,
            "scope": 65,
            "conflicts": 45,
            "boundaries": 40,
            "nested": 55,
            "integration": 60
        }
    }
    
    return thresholds_map.get(context, thresholds_map["general"])


# Complexity cause detection helpers

def _has_multiple_responsibilities_metric(data_structure: Dict[str, Any], threshold: float) -> bool:
    """Check if structure has multiple responsibilities using metrics."""
    responsibility_score = _calculate_responsibility_complexity(data_structure)
    return responsibility_score >= threshold


def _has_high_dependency_count_metric(data_structure: Dict[str, Any], threshold: float) -> bool:
    """Check if structure has high dependency count using metrics."""
    dependency_score = _calculate_dependency_score(data_structure)
    return dependency_score >= threshold


def _has_cross_cutting_concerns_metric(data_structure: Dict[str, Any], threshold: float) -> bool:
    """Check if structure has cross-cutting concerns using metrics."""
    cross_cutting_score = _calculate_cross_cutting_score(data_structure)
    return cross_cutting_score >= threshold


def _has_broad_scope_metric(data_structure: Dict[str, Any], threshold: float) -> bool:
    """Check if structure has broad scope using metrics."""
    scope_score = _calculate_scope_score(data_structure)
    return scope_score >= threshold


def _has_conflicting_requirements_metric(data_structure: Dict[str, Any], threshold: float) -> bool:
    """Check if structure has conflicting requirements using metrics."""
    conflict_score = _calculate_conflict_score(data_structure)
    return conflict_score >= threshold


def _has_unclear_boundaries_metric(data_structure: Dict[str, Any], threshold: float) -> bool:
    """Check if structure has unclear boundaries using metrics."""
    boundary_score = _calculate_boundary_clarity_score(data_structure)
    return boundary_score >= threshold


def _has_nested_complexity_metric(data_structure: Dict[str, Any], threshold: float) -> bool:
    """Check if structure has nested complexity using metrics."""
    nesting_score = _calculate_depth_score(data_structure)
    return nesting_score >= threshold


def _has_integration_complexity_metric(data_structure: Dict[str, Any], threshold: float) -> bool:
    """Check if structure has integration complexity using metrics."""
    integration_score = _calculate_integration_score(data_structure)
    return integration_score >= threshold


def _calculate_responsibility_complexity(data_structure: Dict[str, Any]) -> float:
    """Calculate responsibility complexity score."""
    responsibility_indicators = [
        "responsibilities", "functions", "duties", "roles",
        "capabilities", "operations", "tasks"
    ]
    
    total_responsibilities = 0
    for indicator in responsibility_indicators:
        if indicator in data_structure:
            item = data_structure[indicator]
            if isinstance(item, list):
                total_responsibilities += len(item)
            elif isinstance(item, dict):
                total_responsibilities += len(item)
    
    return min(total_responsibilities * 15, 100)


def _calculate_cross_cutting_score(data_structure: Dict[str, Any]) -> float:
    """Calculate cross-cutting concerns score."""
    cross_cutting_keywords = [
        "logging", "security", "caching", "monitoring",
        "validation", "error_handling", "performance",
        "authentication", "authorization", "auditing"
    ]
    
    content = str(data_structure).lower()
    found_concerns = sum(1 for keyword in cross_cutting_keywords if keyword in content)
    
    return min(found_concerns * 12, 100)


def _calculate_conflict_score(data_structure: Dict[str, Any]) -> float:
    """Calculate conflicting requirements score."""
    conflict_indicators = [
        "conflict", "contradiction", "incompatible",
        "mutually_exclusive", "either_or", "alternative"
    ]
    
    content = str(data_structure).lower()
    conflict_count = sum(1 for indicator in conflict_indicators if indicator in content)
    
    return min(conflict_count * 20, 100)


def _calculate_boundary_clarity_score(data_structure: Dict[str, Any]) -> float:
    """Calculate boundary clarity score (higher = less clear)."""
    clarity_indicators = [
        "unclear", "ambiguous", "undefined", "tbd",
        "to_be_determined", "flexible", "variable"
    ]
    
    content = str(data_structure).lower()
    unclear_count = sum(1 for indicator in clarity_indicators if indicator in content)
    
    return min(unclear_count * 25, 100)


def _calculate_integration_score(data_structure: Dict[str, Any]) -> float:
    """Calculate integration complexity score."""
    integration_indicators = [
        "integration", "interface", "api", "connection",
        "communication", "protocol", "endpoint", "service"
    ]
    
    integration_count = 0
    for indicator in integration_indicators:
        if indicator in data_structure:
            item = data_structure[indicator]
            if isinstance(item, (list, dict)):
                integration_count += len(item)
    
    return min(integration_count * 10, 100)


# Assessment helpers

def _assess_cohesion(decomposition_result: DecompositionResult) -> float:
    """Assess cohesion of decomposed elements (simplified)."""
    if not decomposition_result.success:
        return 0.0
    
    # Simplified cohesion assessment based on decomposition strategy
    if decomposition_result.strategy_used == DecompositionStrategy.RESPONSIBILITY_EXTRACTION:
        return 0.8  # High cohesion expected
    elif decomposition_result.strategy_used == DecompositionStrategy.FUNCTIONAL_SEPARATION:
        return 0.7  # Good cohesion expected
    else:
        return 0.6  # Moderate cohesion


def _assess_coupling(decomposition_result: DecompositionResult) -> float:
    """Assess coupling between decomposed elements (simplified)."""
    if not decomposition_result.success:
        return 1.0  # High coupling (bad)
    
    # Simplified coupling assessment
    if decomposition_result.strategy_used == DecompositionStrategy.DEPENDENCY_REDUCTION:
        return 0.3  # Low coupling expected
    elif decomposition_result.strategy_used == DecompositionStrategy.CONCERN_ISOLATION:
        return 0.4  # Low-moderate coupling
    else:
        return 0.5  # Moderate coupling


def _generate_impact_recommendations(
    assessment: Dict[str, Any],
    original_analysis: ComplexityAnalysis,
    decomposition_result: DecompositionResult
) -> List[str]:
    """Generate recommendations based on impact assessment."""
    recommendations = []
    
    effectiveness = assessment["overall_effectiveness"]
    
    if effectiveness == "high":
        recommendations.append("Decomposition highly effective - proceed with implementation")
        recommendations.append("Monitor complexity metrics to ensure sustained improvement")
    elif effectiveness == "medium":
        recommendations.append("Decomposition moderately effective - consider additional refinements")
        recommendations.append("Test decomposed elements thoroughly")
    elif effectiveness == "low":
        recommendations.append("Decomposition minimally effective - consider alternative strategies")
        recommendations.append("Review original requirements for inherent complexity")
    else:
        recommendations.append("Decomposition ineffective - manual architectural review required")
        recommendations.append("Consider if complexity is essential to the problem domain")
    
    # Quality-based recommendations
    elements_created = assessment["decomposition_quality"]["elements_created"]
    if elements_created > 5:
        recommendations.append("Many elements created - ensure clear integration strategy")
    elif elements_created < 2:
        recommendations.append("Few elements created - consider more aggressive decomposition")
    
    return recommendations


def _calculate_trend_confidence(scores: List[Tuple[datetime, float]], trend_rate: float) -> float:
    """Calculate confidence in trend calculation."""
    if len(scores) < 3:
        return 0.3  # Low confidence with few data points
    
    # Calculate R-squared for trend line fit
    timestamps = [(ts - scores[0][0]).total_seconds() for ts, _ in scores]
    actual_scores = [score for _, score in scores]
    
    # Predicted scores based on trend
    predicted_scores = [scores[0][1] + trend_rate * t for t in timestamps]
    
    # Calculate R-squared
    mean_actual = sum(actual_scores) / len(actual_scores)
    ss_tot = sum((actual - mean_actual) ** 2 for actual in actual_scores)
    ss_res = sum((actual - predicted) ** 2 for actual, predicted in zip(actual_scores, predicted_scores))
    
    if ss_tot == 0:
        return 0.5  # Moderate confidence if no variation
    
    r_squared = 1 - (ss_res / ss_tot)
    return max(0.0, min(1.0, r_squared))


def _project_future_complexity(scores: List[Tuple[datetime, float]], trend_rate: float) -> Dict[str, float]:
    """Project future complexity based on trend."""
    if not scores:
        return {}
    
    latest_time, latest_score = scores[-1]
    
    # Project 1 day, 1 week, and 1 month ahead
    projections = {}
    
    for period, hours in [("1_day", 24), ("1_week", 168), ("1_month", 720)]:
        projected_score = latest_score + (trend_rate * hours * 3600)  # trend_rate is per second
        projections[period] = max(0.0, min(100.0, projected_score))
    
    return projections


def _generate_context_specific_recommendations(
    analysis: ComplexityAnalysis,
    system_context: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Generate recommendations specific to system context."""
    recommendations = []
    
    # Context-based recommendations
    if analysis.analysis_context == "phase_one":
        recommendations.append({
            "priority": "high",
            "category": "phase_coordination",
            "title": "Update Phase Coordination",
            "description": "Ensure phase transitions account for architectural changes",
            "actions": [
                "Update phase handoff mechanisms",
                "Verify component interfaces remain compatible",
                "Test phase transition workflows"
            ],
            "timeline": "before_phase_two"
        })
    
    elif analysis.analysis_context == "phase_three_feature":
        recommendations.append({
            "priority": "medium",
            "category": "natural_selection",
            "title": "Update Natural Selection Criteria",
            "description": "Adjust evaluation criteria for decomposed features",
            "actions": [
                "Modify feature performance metrics",
                "Update selection algorithms",
                "Validate evolution strategies"
            ],
            "timeline": "within_iteration"
        })
    
    return recommendations