"""
Feature Definition Generator
=========================

This module provides functionality for extracting feature definitions from
component requirements and establishing feature relationships.
"""

import logging
import time
import uuid
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass

from resources import (
    StateManager,
    MetricsManager,
    ResourceType
)

logger = logging.getLogger(__name__)

@dataclass
class FeatureTemplate:
    """Template for generating features based on component type."""
    name: str
    description: str
    properties: Dict[str, Any]
    is_required: bool = False

class FeatureDefinitionGenerator:
    """
    Generates feature definitions from component requirements.
    
    Key responsibilities:
    1. Extract feature definitions from component requirements
    2. Establish feature-level validations
    3. Apply feature templates based on component types
    4. Establish cross-component feature relationships
    """
    
    def __init__(self, state_manager: StateManager, metrics_manager: MetricsManager):
        """
        Initialize the FeatureDefinitionGenerator.
        
        Args:
            state_manager: StateManager for state persistence
            metrics_manager: MetricsManager for metrics recording
        """
        self._state_manager = state_manager
        self._metrics_manager = metrics_manager
        
        # Map of component type to feature templates
        self._feature_templates: Dict[str, List[FeatureTemplate]] = {}
        
        # Feature validation rules
        self._validation_rules: List[Dict[str, Any]] = []
        
        # Feature relationships between components
        self._cross_component_relationships: Dict[str, Dict[str, List[str]]] = {}
        
        # Initialize templates
        self._initialize_templates()
    
    def _initialize_templates(self) -> None:
        """Initialize default feature templates for component types."""
        # Core component templates
        self._feature_templates["core"] = [
            FeatureTemplate(
                name="Core API",
                description="Core API functionality for the component",
                properties={
                    "api_type": "internal",
                    "interface_type": "synchronous"
                },
                is_required=True
            ),
            FeatureTemplate(
                name="Data Storage",
                description="Data storage and management for the component",
                properties={
                    "storage_type": "in-memory",
                    "persistence": False
                },
                is_required=False
            )
        ]
        
        # Utility component templates
        self._feature_templates["utility"] = [
            FeatureTemplate(
                name="Utility Functions",
                description="Utility functions provided by the component",
                properties={
                    "scope": "internal",
                    "reusable": True
                },
                is_required=True
            )
        ]
        
        # Service component templates
        self._feature_templates["service"] = [
            FeatureTemplate(
                name="Service Interface",
                description="External service interface",
                properties={
                    "interface_type": "async",
                    "scope": "external"
                },
                is_required=True
            ),
            FeatureTemplate(
                name="Service Implementation",
                description="Implementation of service functionality",
                properties={
                    "scope": "internal"
                },
                is_required=True
            )
        ]
        
        # Feature component templates
        self._feature_templates["feature"] = [
            FeatureTemplate(
                name="User Interface",
                description="User interface for the feature",
                properties={
                    "interface_type": "ui",
                    "scope": "user"
                },
                is_required=False
            ),
            FeatureTemplate(
                name="Feature Logic",
                description="Core logic for the feature",
                properties={
                    "scope": "internal"
                },
                is_required=True
            )
        ]
        
        # Default templates
        self._feature_templates["default"] = [
            FeatureTemplate(
                name="Main Feature",
                description="Main functionality for the component",
                properties={},
                is_required=True
            )
        ]
        
        # Initialize validation rules
        self._validation_rules = [
            {
                "rule_id": "required_fields",
                "description": "Check for required fields in feature definition",
                "required_fields": ["id", "name", "description"]
            },
            {
                "rule_id": "unique_id",
                "description": "Ensure feature IDs are unique within component"
            },
            {
                "rule_id": "dependency_exists",
                "description": "Ensure all dependencies exist either as features or components"
            }
        ]
    
    async def extract_features(self, 
                             component: Dict[str, Any], 
                             dependencies: Optional[Set[str]] = None) -> Dict[str, Any]:
        """
        Extract feature definitions from a component.
        
        This method extracts features from the component definition,
        applies templates based on component type, and establishes
        cross-component relationships.
        
        Args:
            component: Component definition
            dependencies: Optional set of dependency component IDs
            
        Returns:
            Dictionary with extracted features and metadata
        """
        component_id = component.get("id", f"comp_{int(time.time())}")
        component_name = component.get("name", "Unnamed Component")
        component_type = component.get("type", "default").lower()
        
        logger.info(f"Extracting features for component {component_name} ({component_id})")
        
        # Start with explicit features if present
        explicit_features = component.get("features", [])
        features = explicit_features.copy() if explicit_features else []
        
        # Apply templates if needed
        if not features or component.get("apply_templates", False):
            # Get templates for this component type
            templates = self._feature_templates.get(component_type, self._feature_templates["default"])
            
            # Apply templates
            template_features = self._apply_templates(templates, component)
            
            # Only add template features that don't conflict with explicit ones
            existing_ids = {f.get("id", "") for f in features}
            existing_names = {f.get("name", "").lower() for f in features}
            
            for feature in template_features:
                feature_id = feature.get("id", "")
                feature_name = feature.get("name", "").lower()
                
                if feature_id not in existing_ids and feature_name not in existing_names:
                    features.append(feature)
        
        # Ensure all features have IDs
        for i, feature in enumerate(features):
            if "id" not in feature:
                feature["id"] = f"feature_{component_id}_{uuid.uuid4().hex[:8]}"
            
            # Ensure parent component reference
            feature["component_id"] = component_id
            feature["component_name"] = component_name
            
            # Ensure description exists
            if "description" not in feature:
                feature["description"] = f"{feature.get('name', 'Feature')} for {component_name}"
        
        # Establish cross-component relationships
        if dependencies:
            await self._establish_cross_component_relationships(component_id, features, dependencies)
        
        # Validate features
        validation_result = await self._validate_features(features, component_id)
        
        # Record metrics
        await self._metrics_manager.record_metric(
            "phase_two:features:extracted",
            len(features),
            metadata={
                "component_id": component_id,
                "feature_count": len(features),
                "explicit_count": len(explicit_features),
                "template_count": len(features) - len(explicit_features)
            }
        )
        
        if not validation_result["is_valid"]:
            # Record validation errors
            await self._metrics_manager.record_metric(
                "phase_two:features:validation_errors",
                len(validation_result["errors"]),
                metadata={
                    "component_id": component_id,
                    "error_count": len(validation_result["errors"])
                }
            )
            
            logger.error(f"Feature validation errors for {component_id}: {validation_result['errors']}")
            
            return {
                "error": "Feature validation failed",
                "validation_errors": validation_result["errors"],
                "component_id": component_id
            }
        
        # Store features in state manager
        for feature in features:
            feature_id = feature["id"]
            await self._state_manager.set_state(
                f"feature:{feature_id}:definition",
                feature,
                ResourceType.STATE
            )
            
            # Store component-feature relationship
            await self._state_manager.set_state(
                f"component:{component_id}:feature:{feature_id}",
                {
                    "component_id": component_id,
                    "feature_id": feature_id,
                    "timestamp": time.time()
                },
                ResourceType.STATE
            )
        
        # Store feature list in component
        await self._state_manager.set_state(
            f"component:{component_id}:features",
            [f["id"] for f in features],
            ResourceType.STATE
        )
        
        logger.info(f"Extracted {len(features)} features for component {component_id}")
        
        return {
            "features": features,
            "component_id": component_id,
            "template_applied": component_type
        }
    
    def _apply_templates(self, templates: List[FeatureTemplate], component: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply feature templates to generate features.
        
        Args:
            templates: List of feature templates
            component: Component definition
            
        Returns:
            List of generated feature definitions
        """
        component_id = component.get("id", f"comp_{int(time.time())}")
        features = []
        
        for template in templates:
            # Only include required templates or if templates should be fully applied
            if template.is_required or component.get("apply_all_templates", False):
                # Generate feature ID
                feature_id = f"feature_{component_id}_{template.name.lower().replace(' ', '_')}"
                
                # Create feature from template
                feature = {
                    "id": feature_id,
                    "name": f"{template.name}",
                    "description": template.description,
                    "template_generated": True,
                    "properties": template.properties.copy(),
                    "dependencies": []
                }
                
                # Add custom properties from component if they exist
                if "feature_properties" in component:
                    feature_props = component["feature_properties"].get(template.name, {})
                    if feature_props:
                        feature["properties"].update(feature_props)
                
                features.append(feature)
        
        logger.debug(f"Applied {len(features)} feature templates for component {component_id}")
        return features
    
    async def _establish_cross_component_relationships(self, 
                                                   component_id: str, 
                                                   features: List[Dict[str, Any]], 
                                                   dependencies: Set[str]) -> None:
        """
        Establish relationships between features across components.
        
        Args:
            component_id: ID of the component
            features: List of features
            dependencies: Set of dependency component IDs
        """
        # For each dependency, find potential relationships
        for dep_id in dependencies:
            # Get dependency features
            dep_features = await self._state_manager.get_state(f"component:{dep_id}:features")
            if not dep_features:
                logger.warning(f"No features found for dependency {dep_id}")
                continue
            
            # Get feature details
            dep_feature_details = []
            for feature_id in dep_features:
                feature_def = await self._state_manager.get_state(f"feature:{feature_id}:definition")
                if feature_def:
                    dep_feature_details.append(feature_def)
            
            # Look for potential relationships
            for feature in features:
                # Initialize dependencies list if not present
                if "dependencies" not in feature:
                    feature["dependencies"] = []
                
                # Look for matching features in dependency by name or purpose
                feature_name = feature.get("name", "").lower()
                feature_desc = feature.get("description", "").lower()
                
                for dep_feature in dep_feature_details:
                    dep_name = dep_feature.get("name", "").lower()
                    dep_desc = dep_feature.get("description", "").lower()
                    
                    # Check for potential relationships
                    if (
                        # Name contains similar terms
                        self._has_common_terms(feature_name, dep_name) or
                        # Or descriptions share common elements
                        self._has_common_terms(feature_desc, dep_desc)
                    ):
                        # Add as dependency if not already present
                        if dep_feature["id"] not in feature["dependencies"]:
                            feature["dependencies"].append(dep_feature["id"])
                            
                            # Store relationship in both directions
                            if component_id not in self._cross_component_relationships:
                                self._cross_component_relationships[component_id] = {}
                            if dep_id not in self._cross_component_relationships[component_id]:
                                self._cross_component_relationships[component_id][dep_id] = []
                                
                            relationship = {
                                "from_feature": feature["id"],
                                "to_feature": dep_feature["id"],
                                "from_component": component_id,
                                "to_component": dep_id,
                                "type": "depends_on"
                            }
                            
                            self._cross_component_relationships[component_id][dep_id].append(relationship)
                            
                            logger.debug(f"Established relationship: {feature['id']} depends on {dep_feature['id']}")
                            
                            # Store relationship in state manager
                            await self._state_manager.set_state(
                                f"feature:{feature['id']}:dependency:{dep_feature['id']}",
                                relationship,
                                ResourceType.STATE
                            )
    
    def _has_common_terms(self, text1: str, text2: str) -> bool:
        """
        Check if two text strings have common terms.
        
        Args:
            text1: First text string
            text2: Second text string
            
        Returns:
            True if texts have common terms, False otherwise
        """
        # Normalize and split into terms
        terms1 = set(text1.lower().split())
        terms2 = set(text2.lower().split())
        
        # Remove common stop words
        stop_words = {"a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "with", "of", "by"}
        terms1 = terms1 - stop_words
        terms2 = terms2 - stop_words
        
        # Find common terms
        common = terms1.intersection(terms2)
        
        # Require at least 2 common terms or 30% overlap
        min_terms = min(len(terms1), len(terms2))
        return len(common) >= 2 or (min_terms > 0 and len(common) / min_terms >= 0.3)
    
    async def _validate_features(self, features: List[Dict[str, Any]], component_id: str) -> Dict[str, Any]:
        """
        Validate feature definitions.
        
        Args:
            features: List of feature definitions
            component_id: Component ID
            
        Returns:
            Dictionary with validation result
        """
        errors = []
        
        # Check for required fields
        for i, feature in enumerate(features):
            # Check required fields
            required_fields = ["id", "name", "description"]
            for field in required_fields:
                if field not in feature:
                    errors.append({
                        "feature_index": i,
                        "error_type": "missing_field",
                        "field": field,
                        "message": f"Feature #{i} is missing required field '{field}'"
                    })
        
        # Check for duplicate IDs
        feature_ids = [f.get("id", "") for f in features]
        duplicate_ids = {fid for fid in feature_ids if feature_ids.count(fid) > 1}
        
        for dup_id in duplicate_ids:
            errors.append({
                "error_type": "duplicate_id",
                "id": dup_id,
                "message": f"Duplicate feature ID: {dup_id}"
            })
        
        # Check dependencies if present
        feature_id_set = set(feature_ids)
        
        for i, feature in enumerate(features):
            if "dependencies" in feature:
                deps = feature["dependencies"]
                
                for dep_id in deps:
                    # Skip if dependency is in the current feature set
                    if dep_id in feature_id_set:
                        continue
                        
                    # Otherwise, check if it exists in state manager
                    dep_exists = await self._state_manager.get_state(f"feature:{dep_id}:definition")
                    if not dep_exists:
                        errors.append({
                            "feature_index": i,
                            "error_type": "invalid_dependency",
                            "dependency_id": dep_id,
                            "message": f"Feature #{i} depends on non-existent feature: {dep_id}"
                        })
        
        # Check for cycles in dependencies
        cycles = self._detect_dependency_cycles(features)
        if cycles:
            for cycle in cycles:
                errors.append({
                    "error_type": "dependency_cycle",
                    "cycle": cycle,
                    "message": f"Dependency cycle detected: {' -> '.join(cycle)}"
                })
        
        # Determine validation result
        is_valid = len(errors) == 0
        
        return {
            "is_valid": is_valid,
            "component_id": component_id,
            "errors": errors
        }
    
    def _detect_dependency_cycles(self, features: List[Dict[str, Any]]) -> List[List[str]]:
        """
        Detect cycles in feature dependencies.
        
        Args:
            features: List of feature definitions
            
        Returns:
            List of cycles found (as lists of feature IDs)
        """
        # Build dependency graph
        graph = {}
        for feature in features:
            feature_id = feature.get("id", "")
            dependencies = feature.get("dependencies", [])
            
            if feature_id not in graph:
                graph[feature_id] = set()
                
            for dep_id in dependencies:
                graph[feature_id].add(dep_id)
                
                # Ensure node exists in graph
                if dep_id not in graph:
                    graph[dep_id] = set()
        
        # Detect cycles using DFS
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    cycle = dfs(neighbor, path.copy())
                    if cycle:
                        cycles.append(cycle)
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]
            
            rec_stack.remove(node)
            return None
        
        # Check each node
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    async def create_feature_templates(self, component_type: str, templates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create feature templates for a component type.
        
        Args:
            component_type: Component type
            templates: List of template definitions
            
        Returns:
            Dictionary with template creation result
        """
        # Convert template dictionaries to FeatureTemplate objects
        feature_templates = []
        for template in templates:
            feature_templates.append(FeatureTemplate(
                name=template.get("name", "Unnamed Template"),
                description=template.get("description", ""),
                properties=template.get("properties", {}),
                is_required=template.get("is_required", False)
            ))
        
        # Store templates
        self._feature_templates[component_type.lower()] = feature_templates
        
        logger.info(f"Created {len(feature_templates)} feature templates for component type {component_type}")
        
        return {
            "status": "success",
            "component_type": component_type,
            "template_count": len(feature_templates)
        }
    
    async def get_feature_templates(self, component_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get feature templates.
        
        Args:
            component_type: Optional component type to filter by
            
        Returns:
            Dictionary with templates
        """
        if component_type:
            # Get templates for specific component type
            component_type = component_type.lower()
            templates = self._feature_templates.get(component_type, [])
            
            return {
                "component_type": component_type,
                "templates": [
                    {
                        "name": t.name,
                        "description": t.description,
                        "properties": t.properties,
                        "is_required": t.is_required
                    }
                    for t in templates
                ]
            }
        else:
            # Get all templates
            templates = {}
            for comp_type, temp_list in self._feature_templates.items():
                templates[comp_type] = [
                    {
                        "name": t.name,
                        "description": t.description,
                        "properties": t.properties,
                        "is_required": t.is_required
                    }
                    for t in temp_list
                ]
            
            return {
                "templates": templates
            }
    
    async def get_cross_component_relationships(self, component_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get cross-component feature relationships.
        
        Args:
            component_id: Optional component ID to filter by
            
        Returns:
            Dictionary with relationships
        """
        if component_id:
            # Get relationships for specific component
            if component_id not in self._cross_component_relationships:
                return {
                    "component_id": component_id,
                    "relationships": {}
                }
                
            return {
                "component_id": component_id,
                "relationships": self._cross_component_relationships[component_id]
            }
        else:
            # Get all relationships
            return {
                "relationships": self._cross_component_relationships
            }