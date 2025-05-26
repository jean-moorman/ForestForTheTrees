"""
Fire Agent decomposition algorithms.

This module provides sophisticated decomposition strategies for reducing complexity
in guidelines, features, and components when they exceed acceptable thresholds.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from .models import (
    DecompositionResult,
    DecompositionStrategy,
    ComplexityCause,
    ComplexityThreshold
)

logger = logging.getLogger(__name__)


async def decompose_complex_guideline(
    complex_guideline: Dict[str, Any],
    guideline_context: str,
    state_manager=None,
    health_tracker=None,
    strategy: Optional[DecompositionStrategy] = None
) -> DecompositionResult:
    """
    Phase 1 guideline decomposition when Tree Placement Planner
    output becomes too complex.
    
    This is the primary decomposition function for Phase 1 integration
    with the Tree Placement Planner workflow.
    
    Args:
        complex_guideline: The complex guideline to decompose
        guideline_context: Context (e.g., "phase_one_component_architecture")
        state_manager: Optional state manager for persistence
        health_tracker: Optional health tracker for monitoring
        strategy: Optional specific decomposition strategy
        
    Returns:
        DecompositionResult with simplified architecture and metadata
    """
    try:
        logger.info(f"Decomposing complex guideline in context: {guideline_context}")
        
        # Determine strategy if not provided
        if strategy is None:
            strategy = await _determine_guideline_strategy(complex_guideline, guideline_context)
        
        # Calculate original complexity score for comparison
        from .complexity_detector import analyze_guideline_complexity
        original_analysis = await analyze_guideline_complexity(
            complex_guideline, guideline_context, state_manager, health_tracker
        )
        original_score = original_analysis.complexity_score
        
        # Execute decomposition based on strategy
        decomposition_success = False
        simplified_architecture = None
        decomposed_elements = []
        lessons_learned = []
        warnings = []
        
        if strategy == DecompositionStrategy.RESPONSIBILITY_EXTRACTION:
            simplified_architecture, decomposed_elements = await _extract_responsibilities_from_guideline(
                complex_guideline, guideline_context
            )
            decomposition_success = simplified_architecture is not None
            lessons_learned.append("Extracted single responsibilities into focused components")
            
        elif strategy == DecompositionStrategy.DEPENDENCY_REDUCTION:
            simplified_architecture, decomposed_elements = await _reduce_guideline_dependencies(
                complex_guideline, guideline_context
            )
            decomposition_success = simplified_architecture is not None
            lessons_learned.append("Reduced inter-component dependencies through abstraction")
            
        elif strategy == DecompositionStrategy.SCOPE_NARROWING:
            simplified_architecture, decomposed_elements = await _narrow_guideline_scope(
                complex_guideline, guideline_context
            )
            decomposition_success = simplified_architecture is not None
            lessons_learned.append("Narrowed component scope to core functionality")
            
        elif strategy == DecompositionStrategy.LAYER_SEPARATION:
            simplified_architecture, decomposed_elements = await _separate_guideline_layers(
                complex_guideline, guideline_context
            )
            decomposition_success = simplified_architecture is not None
            lessons_learned.append("Separated architectural layers for better organization")
            
        else:
            # Fallback to functional separation
            simplified_architecture, decomposed_elements = await _functionally_separate_guideline(
                complex_guideline, guideline_context
            )
            decomposition_success = simplified_architecture is not None
            lessons_learned.append("Applied functional separation to reduce complexity")
        
        # Calculate new complexity score if decomposition succeeded
        new_score = None
        complexity_reduction = None
        
        if decomposition_success and simplified_architecture:
            new_analysis = await analyze_guideline_complexity(
                simplified_architecture, guideline_context, state_manager, health_tracker
            )
            new_score = new_analysis.complexity_score
            complexity_reduction = original_score - new_score
            
            # Validate that complexity was actually reduced
            if complexity_reduction <= 0:
                warnings.append("Decomposition did not significantly reduce complexity")
                decomposition_success = False
        
        # Generate follow-up recommendations
        follow_up_recommendations = _generate_guideline_followup_recommendations(
            complex_guideline, simplified_architecture, strategy, decomposition_success
        )
        
        # Create decomposition result
        result = DecompositionResult(
            success=decomposition_success,
            original_complexity_score=original_score,
            new_complexity_score=new_score,
            complexity_reduction=complexity_reduction,
            strategy_used=strategy,
            decomposed_elements=decomposed_elements,
            simplified_architecture=simplified_architecture,
            lessons_learned=lessons_learned,
            warnings=warnings,
            follow_up_recommendations=follow_up_recommendations,
            success_metrics={
                "complexity_reduction_percentage": (complexity_reduction / original_score * 100) if complexity_reduction and original_score > 0 else 0,
                "elements_decomposed": len(decomposed_elements),
                "strategy_effectiveness": "high" if complexity_reduction and complexity_reduction > 20 else "low"
            }
        )
        
        # Store decomposition result if state manager available
        if state_manager:
            await _store_decomposition_result(state_manager, result, guideline_context)
        
        # Track decomposition metrics if health tracker available
        if health_tracker:
            await _track_decomposition_health(health_tracker, result)
        
        logger.info(f"Guideline decomposition complete: success={decomposition_success}, reduction={complexity_reduction:.2f if complexity_reduction else 0}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error decomposing complex guideline: {str(e)}")
        
        # Return failure result
        return DecompositionResult(
            success=False,
            original_complexity_score=0.0,
            warnings=[f"Decomposition failed: {str(e)}"],
            follow_up_recommendations=["Manual complexity review recommended"]
        )


async def decompose_complex_feature(
    complex_feature: Dict[str, Any],
    decomposition_strategy: str,
    state_manager=None,
    health_tracker=None
) -> DecompositionResult:
    """
    Phase 3 feature decomposition - the original Fire agent role.
    
    Supports Natural Selection by decomposing overly complex features
    into manageable sub-features.
    
    Args:
        complex_feature: The complex feature to decompose
        decomposition_strategy: Strategy name as string
        state_manager: Optional state manager for persistence
        health_tracker: Optional health tracker for monitoring
        
    Returns:
        DecompositionResult with decomposed features and metadata
    """
    try:
        logger.info(f"Decomposing complex feature using strategy: {decomposition_strategy}")
        
        # Convert string strategy to enum
        strategy_map = {
            "functional_separation": DecompositionStrategy.FUNCTIONAL_SEPARATION,
            "responsibility_extraction": DecompositionStrategy.RESPONSIBILITY_EXTRACTION,
            "dependency_reduction": DecompositionStrategy.DEPENDENCY_REDUCTION,
            "concern_isolation": DecompositionStrategy.CONCERN_ISOLATION,
            "scope_narrowing": DecompositionStrategy.SCOPE_NARROWING
        }
        
        strategy = strategy_map.get(decomposition_strategy, DecompositionStrategy.FUNCTIONAL_SEPARATION)
        
        # Calculate original complexity
        from .complexity_detector import analyze_feature_complexity
        original_analysis = await analyze_feature_complexity(
            complex_feature, {}, state_manager, health_tracker
        )
        original_score = original_analysis.complexity_score
        
        # Execute feature decomposition
        decomposition_success = False
        decomposed_features = []
        lessons_learned = []
        warnings = []
        
        if strategy == DecompositionStrategy.FUNCTIONAL_SEPARATION:
            decomposed_features = await _functionally_separate_feature(complex_feature)
            decomposition_success = len(decomposed_features) > 1
            lessons_learned.append("Separated feature by distinct functions")
            
        elif strategy == DecompositionStrategy.RESPONSIBILITY_EXTRACTION:
            decomposed_features = await _extract_feature_responsibilities(complex_feature)
            decomposition_success = len(decomposed_features) > 1
            lessons_learned.append("Extracted single responsibilities into sub-features")
            
        elif strategy == DecompositionStrategy.DEPENDENCY_REDUCTION:
            decomposed_features = await _reduce_feature_dependencies(complex_feature)
            decomposition_success = len(decomposed_features) > 1
            lessons_learned.append("Reduced inter-feature dependencies")
            
        elif strategy == DecompositionStrategy.CONCERN_ISOLATION:
            decomposed_features = await _isolate_feature_concerns(complex_feature)
            decomposition_success = len(decomposed_features) > 1
            lessons_learned.append("Isolated cross-cutting concerns")
            
        else:  # SCOPE_NARROWING
            decomposed_features = await _narrow_feature_scope(complex_feature)
            decomposition_success = len(decomposed_features) > 1
            lessons_learned.append("Narrowed feature scope to core functionality")
        
        # Calculate average new complexity score
        new_score = None
        complexity_reduction = None
        
        if decomposition_success and decomposed_features:
            total_new_score = 0.0
            for feature in decomposed_features:
                feature_analysis = await analyze_feature_complexity(
                    feature, {}, state_manager, health_tracker
                )
                total_new_score += feature_analysis.complexity_score
            
            new_score = total_new_score / len(decomposed_features)
            complexity_reduction = original_score - new_score
            
            if complexity_reduction <= 0:
                warnings.append("Feature decomposition did not reduce average complexity")
        
        # Generate follow-up recommendations
        follow_up_recommendations = _generate_feature_followup_recommendations(
            complex_feature, decomposed_features, strategy, decomposition_success
        )
        
        result = DecompositionResult(
            success=decomposition_success,
            original_complexity_score=original_score,
            new_complexity_score=new_score,
            complexity_reduction=complexity_reduction,
            strategy_used=strategy,
            decomposed_features=decomposed_features,
            lessons_learned=lessons_learned,
            warnings=warnings,
            follow_up_recommendations=follow_up_recommendations,
            success_metrics={
                "features_created": len(decomposed_features),
                "average_complexity_reduction": complexity_reduction if complexity_reduction else 0,
                "decomposition_effectiveness": "high" if len(decomposed_features) > 2 else "medium"
            }
        )
        
        # Store and track results
        if state_manager:
            await _store_decomposition_result(state_manager, result, "phase_three_feature")
        if health_tracker:
            await _track_decomposition_health(health_tracker, result)
        
        logger.info(f"Feature decomposition complete: success={decomposition_success}, features_created={len(decomposed_features)}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error decomposing complex feature: {str(e)}")
        return DecompositionResult(
            success=False,
            original_complexity_score=0.0,
            warnings=[f"Feature decomposition failed: {str(e)}"]
        )


async def simplify_component_architecture(
    complex_component: Dict[str, Any],
    component_context: Dict[str, Any],
    state_manager=None,
    health_tracker=None,
    strategy: Optional[DecompositionStrategy] = None
) -> DecompositionResult:
    """
    Phase 2 component architecture simplification.
    
    Args:
        complex_component: The complex component to simplify
        component_context: Additional context about the component
        state_manager: Optional state manager for persistence
        health_tracker: Optional health tracker for monitoring
        strategy: Optional specific decomposition strategy
        
    Returns:
        DecompositionResult with simplified components and metadata
    """
    try:
        logger.info("Simplifying complex component architecture")
        
        # Determine strategy if not provided
        if strategy is None:
            strategy = await _determine_component_strategy(complex_component, component_context)
        
        # Calculate original complexity
        from .complexity_detector import analyze_component_complexity
        original_analysis = await analyze_component_complexity(
            complex_component, component_context, state_manager, health_tracker
        )
        original_score = original_analysis.complexity_score
        
        # Execute component simplification
        decomposition_success = False
        simplified_components = []
        lessons_learned = []
        
        if strategy == DecompositionStrategy.LAYER_SEPARATION:
            simplified_components = await _separate_component_layers(complex_component)
            decomposition_success = len(simplified_components) > 1
            lessons_learned.append("Separated component into architectural layers")
            
        elif strategy == DecompositionStrategy.FUNCTIONAL_SEPARATION:
            simplified_components = await _functionally_separate_component(complex_component)
            decomposition_success = len(simplified_components) > 1
            lessons_learned.append("Separated component by functional concerns")
            
        else:
            # Default to functional separation
            simplified_components = await _functionally_separate_component(complex_component)
            decomposition_success = len(simplified_components) > 1
            lessons_learned.append("Applied functional separation to component")
        
        # Calculate new complexity metrics
        new_score = None
        complexity_reduction = None
        
        if decomposition_success and simplified_components:
            total_new_score = 0.0
            for component in simplified_components:
                component_analysis = await analyze_component_complexity(
                    component, component_context, state_manager, health_tracker
                )
                total_new_score += component_analysis.complexity_score
            
            new_score = total_new_score / len(simplified_components)
            complexity_reduction = original_score - new_score
        
        result = DecompositionResult(
            success=decomposition_success,
            original_complexity_score=original_score,
            new_complexity_score=new_score,
            complexity_reduction=complexity_reduction,
            strategy_used=strategy,
            simplified_components=simplified_components,
            lessons_learned=lessons_learned,
            success_metrics={
                "components_created": len(simplified_components),
                "simplification_effectiveness": "high" if complexity_reduction and complexity_reduction > 15 else "medium"
            }
        )
        
        # Store and track results
        if state_manager:
            await _store_decomposition_result(state_manager, result, "phase_two_component")
        if health_tracker:
            await _track_decomposition_health(health_tracker, result)
        
        return result
        
    except Exception as e:
        logger.error(f"Error simplifying component architecture: {str(e)}")
        return DecompositionResult(
            success=False,
            original_complexity_score=0.0,
            warnings=[f"Component simplification failed: {str(e)}"]
        )


# Strategy determination helpers

async def _determine_guideline_strategy(
    guideline: Dict[str, Any],
    context: str
) -> DecompositionStrategy:
    """Determine the best decomposition strategy for a guideline."""
    # Analyze the guideline to determine optimal strategy
    
    # Check for multiple responsibilities
    if _has_multiple_responsibilities(guideline):
        return DecompositionStrategy.RESPONSIBILITY_EXTRACTION
    
    # Check for high dependency count
    if _has_high_dependencies(guideline):
        return DecompositionStrategy.DEPENDENCY_REDUCTION
    
    # Check for broad scope
    if _has_broad_scope(guideline):
        return DecompositionStrategy.SCOPE_NARROWING
    
    # Check for layering opportunities
    if _has_layering_opportunities(guideline):
        return DecompositionStrategy.LAYER_SEPARATION
    
    # Default to functional separation
    return DecompositionStrategy.FUNCTIONAL_SEPARATION


async def _determine_component_strategy(
    component: Dict[str, Any],
    context: Dict[str, Any]
) -> DecompositionStrategy:
    """Determine the best decomposition strategy for a component."""
    # Component-specific strategy logic
    if _component_has_layers(component):
        return DecompositionStrategy.LAYER_SEPARATION
    else:
        return DecompositionStrategy.FUNCTIONAL_SEPARATION


# Guideline decomposition implementations

async def _extract_responsibilities_from_guideline(
    guideline: Dict[str, Any],
    context: str
) -> tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """Extract single responsibilities from a complex guideline."""
    try:
        # Identify responsibility clusters
        responsibilities = _identify_responsibility_clusters(guideline)
        
        if len(responsibilities) <= 1:
            return None, []
        
        # Create simplified architecture with core responsibility
        core_responsibility = responsibilities[0]
        simplified_architecture = {
            "core_component": core_responsibility,
            "supporting_components": responsibilities[1:],
            "dependencies": _extract_core_dependencies(guideline, core_responsibility),
            "interfaces": _extract_core_interfaces(guideline, core_responsibility)
        }
        
        # Create decomposed elements
        decomposed_elements = []
        for i, responsibility in enumerate(responsibilities):
            decomposed_elements.append({
                "element_id": f"responsibility_{i}",
                "type": "responsibility",
                "description": responsibility.get("description", f"Responsibility {i}"),
                "scope": responsibility.get("scope", []),
                "dependencies": responsibility.get("dependencies", [])
            })
        
        return simplified_architecture, decomposed_elements
        
    except Exception as e:
        logger.error(f"Error extracting responsibilities: {e}")
        return None, []


async def _reduce_guideline_dependencies(
    guideline: Dict[str, Any],
    context: str
) -> tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """Reduce dependencies in a complex guideline."""
    try:
        # Analyze dependency patterns
        dependencies = guideline.get("dependencies", [])
        if not dependencies:
            return None, []
        
        # Group dependencies by type/category
        dependency_groups = _group_dependencies(dependencies)
        
        # Create abstraction layers for major dependency groups
        simplified_architecture = {
            "core_functionality": _extract_core_functionality(guideline),
            "dependency_abstractions": [],
            "reduced_dependencies": []
        }
        
        decomposed_elements = []
        
        for group_name, group_deps in dependency_groups.items():
            if len(group_deps) > 1:  # Only abstract if multiple dependencies
                abstraction = {
                    "abstraction_name": f"{group_name}_abstraction",
                    "encapsulated_dependencies": group_deps,
                    "interface": f"I{group_name.title()}Service"
                }
                simplified_architecture["dependency_abstractions"].append(abstraction)
                
                decomposed_elements.append({
                    "element_id": f"abstraction_{group_name}",
                    "type": "dependency_abstraction",
                    "description": f"Abstraction for {group_name} dependencies",
                    "dependencies_encapsulated": len(group_deps)
                })
            else:
                # Keep single dependencies as-is
                simplified_architecture["reduced_dependencies"].extend(group_deps)
        
        return simplified_architecture, decomposed_elements
        
    except Exception as e:
        logger.error(f"Error reducing dependencies: {e}")
        return None, []


async def _narrow_guideline_scope(
    guideline: Dict[str, Any],
    context: str
) -> tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """Narrow the scope of a complex guideline."""
    try:
        # Identify core vs. peripheral functionality
        core_functionality = _identify_core_functionality(guideline)
        peripheral_functionality = _identify_peripheral_functionality(guideline)
        
        if not peripheral_functionality:
            return None, []
        
        # Create narrowed architecture focusing on core
        simplified_architecture = {
            "core_scope": core_functionality,
            "deferred_scope": peripheral_functionality,
            "phase_implementation": {
                "phase_1": core_functionality,
                "phase_2": peripheral_functionality[:len(peripheral_functionality)//2],
                "phase_3": peripheral_functionality[len(peripheral_functionality)//2:]
            }
        }
        
        decomposed_elements = []
        decomposed_elements.append({
            "element_id": "core_scope",
            "type": "scope_reduction",
            "description": "Core functionality scope",
            "priority": "high"
        })
        
        for i, peripheral in enumerate(peripheral_functionality):
            decomposed_elements.append({
                "element_id": f"deferred_scope_{i}",
                "type": "deferred_functionality",
                "description": f"Deferred: {peripheral.get('name', f'Peripheral {i}')}",
                "priority": "low"
            })
        
        return simplified_architecture, decomposed_elements
        
    except Exception as e:
        logger.error(f"Error narrowing scope: {e}")
        return None, []


async def _separate_guideline_layers(
    guideline: Dict[str, Any],
    context: str
) -> tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """Separate a guideline into architectural layers."""
    try:
        # Identify layer opportunities
        layers = _identify_architectural_layers(guideline)
        
        if len(layers) <= 1:
            return None, []
        
        # Create layered architecture
        simplified_architecture = {
            "architectural_layers": layers,
            "layer_dependencies": _map_layer_dependencies(layers),
            "layer_interfaces": _define_layer_interfaces(layers)
        }
        
        decomposed_elements = []
        for i, layer in enumerate(layers):
            decomposed_elements.append({
                "element_id": f"layer_{i}",
                "type": "architectural_layer",
                "name": layer.get("name", f"Layer {i}"),
                "responsibilities": layer.get("responsibilities", []),
                "level": i
            })
        
        return simplified_architecture, decomposed_elements
        
    except Exception as e:
        logger.error(f"Error separating layers: {e}")
        return None, []


async def _functionally_separate_guideline(
    guideline: Dict[str, Any],
    context: str
) -> tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """Functionally separate a complex guideline."""
    try:
        # Identify functional areas
        functional_areas = _identify_functional_areas(guideline)
        
        if len(functional_areas) <= 1:
            return None, []
        
        # Create functionally separated architecture
        simplified_architecture = {
            "functional_components": functional_areas,
            "component_interfaces": _define_component_interfaces(functional_areas),
            "integration_patterns": _define_integration_patterns(functional_areas)
        }
        
        decomposed_elements = []
        for i, area in enumerate(functional_areas):
            decomposed_elements.append({
                "element_id": f"functional_area_{i}",
                "type": "functional_component",
                "name": area.get("name", f"Function {i}"),
                "capabilities": area.get("capabilities", [])
            })
        
        return simplified_architecture, decomposed_elements
        
    except Exception as e:
        logger.error(f"Error functional separation: {e}")
        return None, []


# Feature decomposition implementations

async def _functionally_separate_feature(feature: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Separate a feature by distinct functions."""
    try:
        # Identify distinct functions within the feature
        functions = _identify_feature_functions(feature)
        
        decomposed_features = []
        for i, function in enumerate(functions):
            decomposed_features.append({
                "feature_id": f"{feature.get('id', 'feature')}_{function['name']}",
                "name": f"{feature.get('name', 'Feature')} - {function['name']}",
                "type": "functional_component",
                "scope": function.get("scope", {}),
                "dependencies": function.get("dependencies", []),
                "implementation": function.get("implementation", {}),
                "parent_feature": feature.get('id', 'unknown')
            })
        
        return decomposed_features
        
    except Exception as e:
        logger.error(f"Error in functional feature separation: {e}")
        return []


async def _extract_feature_responsibilities(feature: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract single responsibilities from a feature."""
    try:
        responsibilities = _identify_feature_responsibilities(feature)
        
        decomposed_features = []
        for i, responsibility in enumerate(responsibilities):
            decomposed_features.append({
                "feature_id": f"{feature.get('id', 'feature')}_resp_{i}",
                "name": f"{responsibility['name']}",
                "type": "responsibility_component",
                "responsibility": responsibility,
                "scope": {"single_responsibility": responsibility['description']},
                "parent_feature": feature.get('id', 'unknown')
            })
        
        return decomposed_features
        
    except Exception as e:
        logger.error(f"Error extracting feature responsibilities: {e}")
        return []


async def _reduce_feature_dependencies(feature: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Reduce dependencies in a feature through decomposition."""
    try:
        # Group dependencies and create sub-features with reduced dependency sets
        dependencies = feature.get("dependencies", [])
        dependency_groups = _group_feature_dependencies(dependencies)
        
        decomposed_features = []
        for group_name, group_deps in dependency_groups.items():
            decomposed_features.append({
                "feature_id": f"{feature.get('id', 'feature')}_{group_name}",
                "name": f"{feature.get('name', 'Feature')} - {group_name}",
                "type": "dependency_reduced_component",
                "dependencies": group_deps,
                "scope": _create_scope_for_dependencies(group_deps),
                "parent_feature": feature.get('id', 'unknown')
            })
        
        return decomposed_features
        
    except Exception as e:
        logger.error(f"Error reducing feature dependencies: {e}")
        return []


async def _isolate_feature_concerns(feature: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Isolate cross-cutting concerns from a feature."""
    try:
        # Identify cross-cutting concerns
        concerns = _identify_crosscutting_concerns(feature)
        
        decomposed_features = []
        
        # Create core feature without cross-cutting concerns
        core_feature = {
            "feature_id": f"{feature.get('id', 'feature')}_core",
            "name": f"{feature.get('name', 'Feature')} - Core",
            "type": "core_functionality",
            "scope": _extract_core_feature_scope(feature, concerns),
            "parent_feature": feature.get('id', 'unknown')
        }
        decomposed_features.append(core_feature)
        
        # Create separate features for each cross-cutting concern
        for concern in concerns:
            concern_feature = {
                "feature_id": f"{feature.get('id', 'feature')}_{concern['name']}",
                "name": f"{concern['name']} Service",
                "type": "cross_cutting_service",
                "concern": concern,
                "scope": concern.get("scope", {}),
                "parent_feature": feature.get('id', 'unknown')
            }
            decomposed_features.append(concern_feature)
        
        return decomposed_features
        
    except Exception as e:
        logger.error(f"Error isolating feature concerns: {e}")
        return []


async def _narrow_feature_scope(feature: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Narrow feature scope to core functionality."""
    try:
        # Identify MVP vs. extended functionality
        mvp_scope = _identify_mvp_scope(feature)
        extended_scope = _identify_extended_scope(feature)
        
        decomposed_features = []
        
        # Core MVP feature
        mvp_feature = {
            "feature_id": f"{feature.get('id', 'feature')}_mvp",
            "name": f"{feature.get('name', 'Feature')} - MVP",
            "type": "mvp_component",
            "scope": mvp_scope,
            "priority": "high",
            "parent_feature": feature.get('id', 'unknown')
        }
        decomposed_features.append(mvp_feature)
        
        # Extended features
        for i, extension in enumerate(extended_scope):
            ext_feature = {
                "feature_id": f"{feature.get('id', 'feature')}_ext_{i}",
                "name": f"{feature.get('name', 'Feature')} - {extension['name']}",
                "type": "extension_component",
                "scope": extension,
                "priority": "low",
                "parent_feature": feature.get('id', 'unknown')
            }
            decomposed_features.append(ext_feature)
        
        return decomposed_features
        
    except Exception as e:
        logger.error(f"Error narrowing feature scope: {e}")
        return []


# Component decomposition implementations

async def _separate_component_layers(component: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Separate a component into architectural layers."""
    try:
        layers = [
            {"name": "presentation", "responsibilities": ["UI", "user interaction"]},
            {"name": "business", "responsibilities": ["business logic", "validation"]},
            {"name": "data", "responsibilities": ["data access", "persistence"]}
        ]
        
        decomposed_components = []
        for layer in layers:
            decomposed_components.append({
                "component_id": f"{component.get('id', 'component')}_{layer['name']}",
                "name": f"{component.get('name', 'Component')} - {layer['name'].title()} Layer",
                "type": "architectural_layer",
                "layer": layer,
                "parent_component": component.get('id', 'unknown')
            })
        
        return decomposed_components
        
    except Exception as e:
        logger.error(f"Error separating component layers: {e}")
        return []


async def _functionally_separate_component(component: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Functionally separate a component."""
    try:
        # Create basic functional separation
        functions = [
            {"name": "core", "description": "Core functionality"},
            {"name": "support", "description": "Supporting functionality"}
        ]
        
        decomposed_components = []
        for function in functions:
            decomposed_components.append({
                "component_id": f"{component.get('id', 'component')}_{function['name']}",
                "name": f"{component.get('name', 'Component')} - {function['name'].title()}",
                "type": "functional_component",
                "function": function,
                "parent_component": component.get('id', 'unknown')
            })
        
        return decomposed_components
        
    except Exception as e:
        logger.error(f"Error in functional component separation: {e}")
        return []


# Analysis helper functions

def _has_multiple_responsibilities(guideline: Dict[str, Any]) -> bool:
    """Check if guideline has multiple responsibilities."""
    responsibility_indicators = ["responsibilities", "functions", "capabilities", "tasks"]
    for indicator in responsibility_indicators:
        if indicator in guideline:
            item = guideline[indicator]
            if isinstance(item, list) and len(item) > 3:
                return True
            elif isinstance(item, dict) and len(item) > 3:
                return True
    return False


def _has_high_dependencies(guideline: Dict[str, Any]) -> bool:
    """Check if guideline has high dependency count."""
    dependencies = guideline.get("dependencies", [])
    if isinstance(dependencies, list):
        return len(dependencies) > 5
    elif isinstance(dependencies, dict):
        return len(dependencies) > 5
    return False


def _has_broad_scope(guideline: Dict[str, Any]) -> bool:
    """Check if guideline has broad scope."""
    scope_indicators = ["scope", "components", "modules", "services"]
    for indicator in scope_indicators:
        if indicator in guideline:
            item = guideline[indicator]
            if isinstance(item, (list, dict)) and len(item) > 6:
                return True
    return False


def _has_layering_opportunities(guideline: Dict[str, Any]) -> bool:
    """Check if guideline has layering opportunities."""
    layer_indicators = ["presentation", "business", "data", "service", "ui", "api"]
    content = str(guideline).lower()
    found_layers = sum(1 for indicator in layer_indicators if indicator in content)
    return found_layers >= 2


def _component_has_layers(component: Dict[str, Any]) -> bool:
    """Check if component has layer separation opportunities."""
    return _has_layering_opportunities(component)


# Content analysis helpers

def _identify_responsibility_clusters(guideline: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Identify clusters of related responsibilities."""
    # Simplified implementation
    responsibilities = guideline.get("responsibilities", [])
    if not isinstance(responsibilities, list):
        responsibilities = [responsibilities] if responsibilities else []
    
    clusters = []
    for i, resp in enumerate(responsibilities):
        clusters.append({
            "id": f"cluster_{i}",
            "description": str(resp),
            "scope": [str(resp)],
            "dependencies": []
        })
    
    return clusters[:4]  # Limit to 4 clusters


def _extract_core_dependencies(guideline: Dict[str, Any], core_responsibility: Dict[str, Any]) -> List[str]:
    """Extract core dependencies for a responsibility."""
    return guideline.get("dependencies", [])[:3]  # Simplified


def _extract_core_interfaces(guideline: Dict[str, Any], core_responsibility: Dict[str, Any]) -> List[str]:
    """Extract core interfaces for a responsibility."""
    return guideline.get("interfaces", [])[:2]  # Simplified


def _group_dependencies(dependencies: List[Any]) -> Dict[str, List[Any]]:
    """Group dependencies by type or category."""
    groups = {"core": [], "external": [], "internal": []}
    
    for dep in dependencies:
        dep_str = str(dep).lower()
        if "external" in dep_str or "third_party" in dep_str:
            groups["external"].append(dep)
        elif "internal" in dep_str or "system" in dep_str:
            groups["internal"].append(dep)
        else:
            groups["core"].append(dep)
    
    return {k: v for k, v in groups.items() if v}  # Only return non-empty groups


def _extract_core_functionality(guideline: Dict[str, Any]) -> Dict[str, Any]:
    """Extract core functionality from guideline."""
    return {
        "primary_purpose": guideline.get("purpose", "Core functionality"),
        "essential_features": guideline.get("features", [])[:3],
        "key_interfaces": guideline.get("interfaces", [])[:2]
    }


def _identify_core_functionality(guideline: Dict[str, Any]) -> Dict[str, Any]:
    """Identify core vs peripheral functionality."""
    return {
        "name": "Core",
        "features": guideline.get("features", [])[:2],
        "priority": "high"
    }


def _identify_peripheral_functionality(guideline: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Identify peripheral functionality that can be deferred."""
    features = guideline.get("features", [])
    peripheral = []
    
    for i, feature in enumerate(features[2:], 2):  # Skip first 2 core features
        peripheral.append({
            "name": f"Feature {i}",
            "description": str(feature),
            "priority": "low"
        })
    
    return peripheral


def _identify_architectural_layers(guideline: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Identify architectural layers in guideline."""
    content = str(guideline).lower()
    
    layers = []
    layer_types = [
        {"name": "presentation", "keywords": ["ui", "interface", "view", "display"]},
        {"name": "business", "keywords": ["logic", "rules", "process", "workflow"]},
        {"name": "data", "keywords": ["data", "storage", "persistence", "database"]}
    ]
    
    for layer_type in layer_types:
        if any(keyword in content for keyword in layer_type["keywords"]):
            layers.append({
                "name": layer_type["name"],
                "responsibilities": layer_type["keywords"],
                "identified": True
            })
    
    return layers


def _map_layer_dependencies(layers: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Map dependencies between layers."""
    deps = {}
    layer_names = [layer["name"] for layer in layers]
    
    # Standard layer dependency pattern
    if "presentation" in layer_names:
        deps["presentation"] = ["business"] if "business" in layer_names else []
    if "business" in layer_names:
        deps["business"] = ["data"] if "data" in layer_names else []
    if "data" in layer_names:
        deps["data"] = []
    
    return deps


def _define_layer_interfaces(layers: List[Dict[str, Any]]) -> Dict[str, str]:
    """Define interfaces between layers."""
    interfaces = {}
    for layer in layers:
        interfaces[layer["name"]] = f"I{layer['name'].title()}Service"
    return interfaces


def _identify_functional_areas(guideline: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Identify functional areas in guideline."""
    # Simplified implementation
    return [
        {"name": "Core", "capabilities": ["primary_function"]},
        {"name": "Support", "capabilities": ["helper_functions"]}
    ]


def _define_component_interfaces(functional_areas: List[Dict[str, Any]]) -> Dict[str, str]:
    """Define interfaces for functional components."""
    interfaces = {}
    for area in functional_areas:
        interfaces[area["name"]] = f"I{area['name']}Component"
    return interfaces


def _define_integration_patterns(functional_areas: List[Dict[str, Any]]) -> List[str]:
    """Define integration patterns between functional areas."""
    return ["event_driven", "direct_call", "message_passing"]


# Feature analysis helpers

def _identify_feature_functions(feature: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Identify distinct functions within a feature."""
    return [
        {"name": "core", "scope": {}, "dependencies": [], "implementation": {}},
        {"name": "validation", "scope": {}, "dependencies": [], "implementation": {}}
    ]


def _identify_feature_responsibilities(feature: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Identify feature responsibilities."""
    return [
        {"name": "Primary", "description": "Main feature responsibility"},
        {"name": "Secondary", "description": "Supporting responsibility"}
    ]


def _group_feature_dependencies(dependencies: List[Any]) -> Dict[str, List[Any]]:
    """Group feature dependencies."""
    return {"core": dependencies[:len(dependencies)//2], "support": dependencies[len(dependencies)//2:]}


def _create_scope_for_dependencies(dependencies: List[Any]) -> Dict[str, Any]:
    """Create scope definition for a set of dependencies."""
    return {"dependency_scope": [str(dep) for dep in dependencies]}


def _identify_crosscutting_concerns(feature: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Identify cross-cutting concerns in feature."""
    return [
        {"name": "logging", "scope": {"type": "cross_cutting"}},
        {"name": "validation", "scope": {"type": "cross_cutting"}}
    ]


def _extract_core_feature_scope(feature: Dict[str, Any], concerns: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract core feature scope without cross-cutting concerns."""
    return {"core_functionality": "main_feature_logic"}


def _identify_mvp_scope(feature: Dict[str, Any]) -> Dict[str, Any]:
    """Identify MVP scope for feature."""
    return {"mvp_features": ["essential_function_1", "essential_function_2"]}


def _identify_extended_scope(feature: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Identify extended scope beyond MVP."""
    return [
        {"name": "Advanced", "features": ["advanced_function_1"]},
        {"name": "Optional", "features": ["optional_function_1"]}
    ]


# Follow-up recommendation generators

def _generate_guideline_followup_recommendations(
    original_guideline: Dict[str, Any],
    simplified_architecture: Optional[Dict[str, Any]],
    strategy: DecompositionStrategy,
    success: bool
) -> List[str]:
    """Generate follow-up recommendations for guideline decomposition."""
    recommendations = []
    
    if success:
        recommendations.append("Validate decomposed architecture with stakeholders")
        recommendations.append("Update phase coordination to handle new structure")
        if strategy == DecompositionStrategy.DEPENDENCY_REDUCTION:
            recommendations.append("Implement dependency abstractions gradually")
    else:
        recommendations.append("Consider manual architectural review")
        recommendations.append("Evaluate if complexity is inherent to requirements")
    
    return recommendations


def _generate_feature_followup_recommendations(
    original_feature: Dict[str, Any],
    decomposed_features: List[Dict[str, Any]],
    strategy: DecompositionStrategy,
    success: bool
) -> List[str]:
    """Generate follow-up recommendations for feature decomposition."""
    recommendations = []
    
    if success:
        recommendations.append("Test decomposed features independently")
        recommendations.append("Update Natural Selection evaluation criteria")
        if len(decomposed_features) > 3:
            recommendations.append("Consider further decomposition if performance issues persist")
    else:
        recommendations.append("Re-evaluate feature requirements for simplification opportunities")
    
    return recommendations


# Storage and tracking helpers

async def _store_decomposition_result(
    state_manager,
    result: DecompositionResult,
    context: str
):
    """Store decomposition result in state manager."""
    try:
        key = f"fire_agent:decomposition:{context}:{datetime.now().isoformat()}"
        await state_manager.set_state(key, result.__dict__, "STATE")
    except Exception as e:
        logger.warning(f"Failed to store decomposition result: {e}")


async def _track_decomposition_health(
    health_tracker,
    result: DecompositionResult
):
    """Track decomposition metrics in health tracker."""
    try:
        health_tracker.track_metric("fire_agent_decomposition_success", 1 if result.success else 0)
        if result.complexity_reduction:
            health_tracker.track_metric("fire_agent_complexity_reduction", result.complexity_reduction)
    except Exception as e:
        logger.warning(f"Failed to track decomposition health: {e}")