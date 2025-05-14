"""
Component to Feature Mapper
==========================

This module provides functionality to map component definitions to feature
definitions for delegation to Phase Three.
"""

import logging
import uuid
from typing import Dict, List, Any, Set, Tuple, Optional

from resources import (
    StateManager,
    MetricsManager,
    EventQueue,
    ResourceType
)

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Exception raised for validation errors in component to feature mapping."""
    pass

class ComponentToFeatureMapper:
    """
    Maps component definitions to feature definitions for delegation to Phase Three.
    
    This class is responsible for:
    1. Extracting features from component definitions
    2. Establishing feature dependency hierarchy based on component dependencies
    3. Adding component-specific metadata to feature definitions
    4. Validating completeness and correctness of feature definitions
    """
    
    def __init__(self, state_manager: StateManager, metrics_manager: MetricsManager, event_queue: EventQueue):
        """
        Initialize the ComponentToFeatureMapper.
        
        Args:
            state_manager: StateManager instance for state persistence
            metrics_manager: MetricsManager instance for metrics recording
            event_queue: EventQueue instance for event emission
        """
        self._state_manager = state_manager
        self._metrics_manager = metrics_manager
        self._event_queue = event_queue
        
        # Track component to feature mappings
        self._component_to_features: Dict[str, List[str]] = {}
        # Track feature dependencies
        self._feature_dependencies: Dict[str, Set[str]] = {}
        
    async def extract_features(self, component_definition: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract feature definitions from a component definition.
        
        This method analyzes the component definition and extracts a list of
        feature definitions that can be passed to Phase Three.
        
        Args:
            component_definition: Dictionary containing component definition
            
        Returns:
            List of feature definition dictionaries
            
        Raises:
            ValidationError: If the component definition is invalid or incomplete
        """
        # Validate component definition
        self._validate_component_definition(component_definition)
        
        component_id = component_definition.get("id", "")
        component_name = component_definition.get("name", "")
        
        # Extract explicit features if present
        explicit_features = component_definition.get("features", [])
        
        # If no explicit features, create a default feature
        if not explicit_features:
            default_feature = self._create_default_feature(component_definition)
            features = [default_feature]
        else:
            features = explicit_features.copy()
            
        # Add component metadata to each feature
        for feature in features:
            self._add_component_metadata(feature, component_definition)
            
        # Generate unique IDs for features if not present
        for feature in features:
            if "id" not in feature:
                feature["id"] = f"feature_{component_id}_{uuid.uuid4().hex[:8]}"
                
        # Store mapping for later reference
        self._component_to_features[component_id] = [f["id"] for f in features]
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:delegation:features_extracted",
            len(features),
            metadata={
                "component_id": component_id,
                "component_name": component_name,
                "feature_count": len(features)
            }
        )
        
        logger.info(f"Extracted {len(features)} features from component {component_name} ({component_id})")
        return features
    
    async def establish_feature_dependencies(self, component_id: str, component_dependencies: List[str]) -> Dict[str, List[str]]:
        """
        Establish feature dependencies based on component dependencies.
        
        Args:
            component_id: ID of the component
            component_dependencies: List of component IDs that this component depends on
            
        Returns:
            Dictionary mapping feature IDs to lists of feature dependencies
        """
        # Get features for this component
        component_features = self._component_to_features.get(component_id, [])
        
        # Initialize result dictionary
        feature_dependencies: Dict[str, List[str]] = {f_id: [] for f_id in component_features}
        
        # For each component dependency, add feature dependencies
        for dep_component_id in component_dependencies:
            # Get features of dependency component
            dep_features = self._component_to_features.get(dep_component_id, [])
            
            # If no features found, log warning and continue
            if not dep_features:
                logger.warning(f"No features found for dependency component {dep_component_id}")
                continue
                
            # Add dependency for each feature
            for feature_id in component_features:
                for dep_feature_id in dep_features:
                    feature_dependencies.setdefault(feature_id, []).append(dep_feature_id)
                    
                    # Store in internal tracking
                    self._feature_dependencies.setdefault(feature_id, set()).add(dep_feature_id)
        
        # Record metrics
        total_dependencies = sum(len(deps) for deps in feature_dependencies.values())
        await self._metrics_manager.record_metric(
            "phase_two:delegation:feature_dependencies_established",
            total_dependencies,
            metadata={
                "component_id": component_id,
                "total_dependencies": total_dependencies
            }
        )
        
        logger.info(f"Established {total_dependencies} feature dependencies for component {component_id}")
        return feature_dependencies
    
    async def add_component_metadata(self, features: List[Dict[str, Any]], component_definition: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Add component-specific metadata to feature definitions.
        
        Args:
            features: List of feature definitions
            component_definition: Component definition dictionary
            
        Returns:
            Updated feature definitions with component metadata
        """
        component_id = component_definition.get("id", "")
        component_name = component_definition.get("name", "")
        
        for feature in features:
            feature["component_id"] = component_id
            feature["component_name"] = component_name
            
            # Add component guidelines if available
            if "guidelines" in component_definition:
                feature.setdefault("guidelines", {}).update({
                    "component_guidelines": component_definition["guidelines"]
                })
                
            # Add component data flow if available
            if "data_flow" in component_definition:
                feature.setdefault("data_flow", {}).update({
                    "component_data_flow": component_definition["data_flow"]
                })
                
            # Add public interface if available
            if "public_interface" in component_definition:
                feature["public_interface"] = component_definition["public_interface"]
        
        # Store updated features in state manager
        component_features_key = f"component:{component_id}:features"
        await self._state_manager.set_state(
            component_features_key, 
            [f["id"] for f in features],
            ResourceType.STATE
        )
        
        logger.info(f"Added component metadata to {len(features)} features for component {component_name}")
        return features
    
    async def validate_features(self, features: List[Dict[str, Any]]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate the completeness and correctness of feature definitions.
        
        Args:
            features: List of feature definitions to validate
            
        Returns:
            Tuple of (is_valid, validation_errors)
        """
        validation_errors = []
        
        # Check each feature for required fields
        for i, feature in enumerate(features):
            # Check required fields
            required_fields = ["id", "name", "description"]
            for field in required_fields:
                if field not in feature:
                    validation_errors.append({
                        "error_type": "missing_field",
                        "feature_index": i,
                        "field": field,
                        "message": f"Feature missing required field: {field}"
                    })
            
            # Check for duplicate IDs
            feature_id = feature.get("id", "")
            duplicate_count = sum(1 for f in features if f.get("id") == feature_id)
            if duplicate_count > 1:
                validation_errors.append({
                    "error_type": "duplicate_id",
                    "feature_index": i,
                    "feature_id": feature_id,
                    "message": f"Duplicate feature ID: {feature_id}"
                })
                
            # Validate dependencies
            if "dependencies" in feature:
                for dep_id in feature["dependencies"]:
                    # Check if dependency exists
                    dep_exists = any(f.get("id") == dep_id for f in features)
                    if not dep_exists and dep_id not in self._feature_dependencies.get(feature_id, set()):
                        validation_errors.append({
                            "error_type": "invalid_dependency",
                            "feature_index": i,
                            "feature_id": feature_id,
                            "dependency_id": dep_id,
                            "message": f"Feature {feature_id} depends on non-existent feature: {dep_id}"
                        })
        
        # Check for cycles in dependencies
        cycle_errors = self._check_dependency_cycles(features)
        validation_errors.extend(cycle_errors)
        
        is_valid = len(validation_errors) == 0
        
        # Record validation metric
        await self._metrics_manager.record_metric(
            "phase_two:delegation:features_validation",
            1,
            metadata={
                "is_valid": is_valid,
                "error_count": len(validation_errors),
                "feature_count": len(features)
            }
        )
        
        if not is_valid:
            logger.warning(f"Feature validation failed with {len(validation_errors)} errors")
        else:
            logger.info(f"Successfully validated {len(features)} features")
            
        return is_valid, validation_errors
    
    def _validate_component_definition(self, component_definition: Dict[str, Any]) -> None:
        """
        Validate the component definition for required fields.
        
        Args:
            component_definition: Component definition to validate
            
        Raises:
            ValidationError: If validation fails
        """
        # Check for required fields
        required_fields = ["id", "name", "description"]
        for field in required_fields:
            if field not in component_definition:
                raise ValidationError(f"Component definition missing required field: {field}")
    
    def _create_default_feature(self, component_definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a default feature from component definition if no features are defined.
        
        Args:
            component_definition: Component definition dictionary
            
        Returns:
            Default feature definition dictionary
        """
        component_id = component_definition.get("id", "")
        component_name = component_definition.get("name", "")
        
        return {
            "id": f"feature_{component_id}_main",
            "name": f"{component_name} Main Feature",
            "description": component_definition.get("description", ""),
            "dependencies": [],
            "is_default": True,
            "requirements": component_definition.get("requirements", {})
        }
    
    def _add_component_metadata(self, feature: Dict[str, Any], component_definition: Dict[str, Any]) -> None:
        """
        Add component metadata to a feature definition.
        
        Args:
            feature: Feature definition to update
            component_definition: Component definition dictionary
        """
        feature["component_id"] = component_definition.get("id", "")
        feature["component_name"] = component_definition.get("name", "")
        
        # Set component requirements as feature requirements if not already set
        if "requirements" not in feature:
            feature["requirements"] = component_definition.get("requirements", {})
            
        # Set component priority if available
        if "priority" in component_definition:
            feature["priority"] = component_definition["priority"]
    
    def _check_dependency_cycles(self, features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check for cycles in feature dependencies.
        
        Args:
            features: List of feature definitions
            
        Returns:
            List of validation errors for dependency cycles
        """
        validation_errors = []
        
        # Build dependency graph
        graph = {}
        for feature in features:
            feature_id = feature.get("id", "")
            dependencies = feature.get("dependencies", [])
            graph[feature_id] = set(dependencies)
            
        # Add tracked dependencies
        for feature_id, deps in self._feature_dependencies.items():
            if feature_id in graph:
                graph[feature_id].update(deps)
            else:
                graph[feature_id] = deps.copy()
        
        # Use DFS to detect cycles
        visited = set()
        rec_stack = set()
        
        def dfs_detect_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    if dfs_detect_cycle(neighbor):
                        return [node, neighbor]
                elif neighbor in rec_stack:
                    return [node, neighbor]
                    
            rec_stack.remove(node)
            return None
        
        # Check each node for cycles
        for node in graph:
            if node not in visited:
                cycle = dfs_detect_cycle(node)
                if cycle:
                    validation_errors.append({
                        "error_type": "dependency_cycle",
                        "cycle_nodes": cycle,
                        "message": f"Dependency cycle detected: {' -> '.join(cycle)}"
                    })
        
        return validation_errors
    
    async def get_component_feature_mapping(self, component_id: str) -> List[str]:
        """
        Get features mapped to a component.
        
        Args:
            component_id: ID of the component
            
        Returns:
            List of feature IDs for the component
        """
        return self._component_to_features.get(component_id, [])