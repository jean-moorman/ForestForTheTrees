"""
Dependency validation module for Phase Two component guidelines.

This module provides functionality for validating dependencies between features
within components, and between different components.
"""
import logging
from typing import Dict, Any, List, Tuple, Set, Optional
from datetime import datetime

from resources import StateManager

logger = logging.getLogger(__name__)

class ComponentDependencyValidator:
    """
    Validates dependencies for component guidelines.
    
    This class handles:
    1. Feature dependency validation within a component
    2. Feature-to-feature relationship validation
    3. Cross-component dependency validation
    4. Data flow validation within features
    """
    
    def __init__(self, state_manager: StateManager):
        """
        Initialize the dependency validator.
        
        Args:
            state_manager: State manager for retrieving stored data
        """
        self.state_manager = state_manager
        
    async def validate_feature_dependencies(
        self, 
        component_id: str, 
        features: List[Dict[str, Any]]
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate dependencies between features within a component.
        
        Args:
            component_id: ID of the component containing the features
            features: List of features with dependencies
            
        Returns:
            Tuple[bool, List[Dict]]: (is_valid, errors)
        """
        logger.info(f"Validating feature dependencies for component {component_id}")
        
        # Track validation errors
        errors = []
        
        # Build mapping of feature IDs
        feature_ids = {feature.get("id"): feature for feature in features if "id" in feature}
        
        # Check for duplicate feature IDs
        duplicate_ids = self._find_duplicate_feature_ids(features)
        if duplicate_ids:
            for dup_id in duplicate_ids:
                errors.append({
                    "error_type": "duplicate_feature_id",
                    "feature_id": dup_id,
                    "message": f"Duplicate feature ID: {dup_id}"
                })
                
        # Check for undefined dependencies
        undefined_deps = self._find_undefined_dependencies(features, feature_ids)
        if undefined_deps:
            for dep in undefined_deps:
                errors.append({
                    "error_type": "undefined_dependency",
                    "feature_id": dep["feature_id"],
                    "dependency": dep["dependency"],
                    "message": f"Feature {dep['feature_id']} depends on undefined feature {dep['dependency']}"
                })
                
        # Check for circular dependencies
        circular_deps = self._find_circular_dependencies(features)
        if circular_deps:
            for dep in circular_deps:
                errors.append({
                    "error_type": "circular_dependency",
                    "feature_id": dep["feature_id"],
                    "dependency_chain": dep["dependency_chain"],
                    "message": f"Circular dependency detected: {' -> '.join(dep['dependency_chain'])}"
                })
                
        # Validation passes if no errors
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info(f"Feature dependencies validation passed for component {component_id}")
        else:
            logger.warning(f"Feature dependencies validation failed with {len(errors)} errors for component {component_id}")
            
        return is_valid, errors
        
    async def validate_feature_relationships(
        self, 
        component_id: str, 
        features: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]]
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate feature relationships within a component.
        
        Args:
            component_id: ID of the component containing the features
            features: List of features
            relationships: List of feature relationships
            
        Returns:
            Tuple[bool, List[Dict]]: (is_valid, errors)
        """
        logger.info(f"Validating feature relationships for component {component_id}")
        
        # Track validation errors
        errors = []
        
        # Build mapping of feature IDs
        feature_ids = {feature.get("id") for feature in features if "id" in feature}
        
        # Check for relationships referencing undefined features
        for relationship in relationships:
            source_id = relationship.get("source_id")
            target_id = relationship.get("target_id")
            
            if source_id and source_id not in feature_ids:
                errors.append({
                    "error_type": "undefined_relationship_source",
                    "source_id": source_id,
                    "target_id": target_id,
                    "message": f"Relationship source feature {source_id} is not defined"
                })
                
            if target_id and target_id not in feature_ids:
                errors.append({
                    "error_type": "undefined_relationship_target",
                    "source_id": source_id,
                    "target_id": target_id,
                    "message": f"Relationship target feature {target_id} is not defined"
                })
                
        # Check for duplicate relationships
        duplicate_relationships = self._find_duplicate_relationships(relationships)
        if duplicate_relationships:
            for dup in duplicate_relationships:
                errors.append({
                    "error_type": "duplicate_relationship",
                    "source_id": dup["source_id"],
                    "target_id": dup["target_id"],
                    "message": f"Duplicate relationship between {dup['source_id']} and {dup['target_id']}"
                })
                
        # Check for conflicting relationship types
        conflicting_relationships = self._find_conflicting_relationships(relationships)
        if conflicting_relationships:
            for conflict in conflicting_relationships:
                errors.append({
                    "error_type": "conflicting_relationship_types",
                    "source_id": conflict["source_id"],
                    "target_id": conflict["target_id"],
                    "types": conflict["types"],
                    "message": f"Conflicting relationship types between {conflict['source_id']} and {conflict['target_id']}: {', '.join(conflict['types'])}"
                })
                
        # Validation passes if no errors
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info(f"Feature relationships validation passed for component {component_id}")
        else:
            logger.warning(f"Feature relationships validation failed with {len(errors)} errors for component {component_id}")
            
        return is_valid, errors
        
    async def validate_component_data_flow(
        self, 
        component_id: str, 
        data_flow: Dict[str, Any]
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate component data flow.
        
        Args:
            component_id: ID of the component
            data_flow: Component data flow definition
            
        Returns:
            Tuple[bool, List[Dict]]: (is_valid, errors)
        """
        logger.info(f"Validating data flow for component {component_id}")
        
        # Track validation errors
        errors = []
        
        # Check if data flow has required structure
        if not isinstance(data_flow, dict) or "component_data_flow" not in data_flow:
            errors.append({
                "error_type": "invalid_data_flow_structure",
                "message": "Data flow must be a dictionary with 'component_data_flow' field"
            })
            return False, errors
            
        component_data_flow = data_flow.get("component_data_flow", {})
        
        # Check for required fields
        required_fields = ["inputs", "outputs", "internal_transformations"]
        missing_fields = [field for field in required_fields if field not in component_data_flow]
        
        if missing_fields:
            errors.append({
                "error_type": "missing_data_flow_fields",
                "missing_fields": missing_fields,
                "message": f"Missing required data flow fields: {', '.join(missing_fields)}"
            })
            
        # Check inputs
        inputs = component_data_flow.get("inputs", [])
        if not isinstance(inputs, list):
            errors.append({
                "error_type": "invalid_inputs_format",
                "message": "Inputs must be a list"
            })
        else:
            # Check each input has required fields
            for i, input_item in enumerate(inputs):
                if not isinstance(input_item, dict):
                    errors.append({
                        "error_type": "invalid_input_format",
                        "index": i,
                        "message": f"Input item at index {i} must be a dictionary"
                    })
                    continue
                    
                # Check required fields
                required_input_fields = ["name", "type", "description"]
                missing_input_fields = [field for field in required_input_fields if field not in input_item]
                
                if missing_input_fields:
                    errors.append({
                        "error_type": "missing_input_fields",
                        "index": i,
                        "input_name": input_item.get("name", f"input_{i}"),
                        "missing_fields": missing_input_fields,
                        "message": f"Input {input_item.get('name', f'input_{i}')} is missing required fields: {', '.join(missing_input_fields)}"
                    })
        
        # Check outputs
        outputs = component_data_flow.get("outputs", [])
        if not isinstance(outputs, list):
            errors.append({
                "error_type": "invalid_outputs_format",
                "message": "Outputs must be a list"
            })
        else:
            # Check each output has required fields
            for i, output_item in enumerate(outputs):
                if not isinstance(output_item, dict):
                    errors.append({
                        "error_type": "invalid_output_format",
                        "index": i,
                        "message": f"Output item at index {i} must be a dictionary"
                    })
                    continue
                    
                # Check required fields
                required_output_fields = ["name", "type", "description"]
                missing_output_fields = [field for field in required_output_fields if field not in output_item]
                
                if missing_output_fields:
                    errors.append({
                        "error_type": "missing_output_fields",
                        "index": i,
                        "output_name": output_item.get("name", f"output_{i}"),
                        "missing_fields": missing_output_fields,
                        "message": f"Output {output_item.get('name', f'output_{i}')} is missing required fields: {', '.join(missing_output_fields)}"
                    })
        
        # Check transformations
        transformations = component_data_flow.get("internal_transformations", [])
        if not isinstance(transformations, list):
            errors.append({
                "error_type": "invalid_transformations_format",
                "message": "Internal transformations must be a list"
            })
        else:
            # Check each transformation has required fields
            for i, transformation in enumerate(transformations):
                if not isinstance(transformation, dict):
                    errors.append({
                        "error_type": "invalid_transformation_format",
                        "index": i,
                        "message": f"Transformation at index {i} must be a dictionary"
                    })
                    continue
                    
                # Check required fields
                required_transformation_fields = ["name", "inputs", "outputs", "description"]
                missing_transformation_fields = [field for field in required_transformation_fields if field not in transformation]
                
                if missing_transformation_fields:
                    errors.append({
                        "error_type": "missing_transformation_fields",
                        "index": i,
                        "transformation_name": transformation.get("name", f"transformation_{i}"),
                        "missing_fields": missing_transformation_fields,
                        "message": f"Transformation {transformation.get('name', f'transformation_{i}')} is missing required fields: {', '.join(missing_transformation_fields)}"
                    })
                    
        # Validation passes if no errors
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info(f"Data flow validation passed for component {component_id}")
        else:
            logger.warning(f"Data flow validation failed with {len(errors)} errors for component {component_id}")
            
        return is_valid, errors
        
    async def validate_cross_component_dependencies(
        self, 
        component_id: str, 
        component_dependencies: List[str]
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate dependencies between components.
        
        Args:
            component_id: ID of the component
            component_dependencies: List of component IDs that this component depends on
            
        Returns:
            Tuple[bool, List[Dict]]: (is_valid, errors)
        """
        logger.info(f"Validating cross-component dependencies for component {component_id}")
        
        # Track validation errors
        errors = []
        
        # Get all defined components
        all_components = await self._get_all_components()
        component_ids = {comp.get("id") for comp in all_components if "id" in comp}
        
        # Check for dependencies on undefined components
        undefined_components = [dep for dep in component_dependencies if dep not in component_ids]
        for undefined in undefined_components:
            errors.append({
                "error_type": "undefined_component_dependency",
                "component_id": component_id,
                "dependency": undefined,
                "message": f"Component {component_id} depends on undefined component {undefined}"
            })
            
        # Check for circular dependencies
        circular_deps = await self._find_circular_component_dependencies(component_id, component_dependencies)
        for circular in circular_deps:
            errors.append({
                "error_type": "circular_component_dependency",
                "component_id": component_id,
                "dependency_chain": circular["dependency_chain"],
                "message": f"Circular component dependency detected: {' -> '.join(circular['dependency_chain'])}"
            })
            
        # Validation passes if no errors
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info(f"Cross-component dependencies validation passed for component {component_id}")
        else:
            logger.warning(f"Cross-component dependencies validation failed with {len(errors)} errors for component {component_id}")
            
        return is_valid, errors
        
    async def prepare_agent_feedback(
        self, 
        agent_id: str, 
        validation_errors: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Prepare feedback for an agent based on validation errors.
        
        Args:
            agent_id: ID of the agent to prepare feedback for
            validation_errors: List of validation errors
            
        Returns:
            Dict with organized feedback
        """
        # Filter errors relevant to this agent
        agent_mapping = {
            "flower_bed_planner": ["invalid_data_flow_structure", "invalid_format"],
            "flower_bed_environment": ["missing_data_flow_fields", "invalid_inputs_format", "invalid_outputs_format"],
            "flower_root_system": ["invalid_transformations_format", "missing_transformation_fields", "invalid_input_format", "invalid_output_format"],
            "flower_placement": ["duplicate_feature_id", "undefined_dependency", "circular_dependency", "undefined_relationship_source", "undefined_relationship_target"]
        }
        
        # Get error types for this agent
        relevant_error_types = agent_mapping.get(agent_id, [])
        
        # Filter errors
        relevant_errors = [
            error for error in validation_errors 
            if error.get("error_type") in relevant_error_types
        ]
        
        # Group errors by type
        grouped_errors = {}
        for error in relevant_errors:
            error_type = error.get("error_type", "unknown")
            if error_type not in grouped_errors:
                grouped_errors[error_type] = []
            grouped_errors[error_type].append(error)
            
        # Build feedback
        feedback = {
            "agent_id": agent_id,
            "error_count": len(relevant_errors),
            "error_types": list(grouped_errors.keys()),
            "errors": grouped_errors,
            "timestamp": datetime.now().isoformat()
        }
        
        return feedback
        
    async def get_validation_summary(
        self, 
        component_id: str
    ) -> Dict[str, Any]:
        """
        Get a summary of validation results for a component.
        
        Args:
            component_id: ID of the component to get summary for
            
        Returns:
            Dict with validation summary
        """
        # Get validation states from state manager
        feature_dependencies_state = await self.state_manager.get_state(
            f"component:validation:{component_id}:feature_dependencies"
        )
        
        feature_relationships_state = await self.state_manager.get_state(
            f"component:validation:{component_id}:feature_relationships"
        )
        
        data_flow_state = await self.state_manager.get_state(
            f"component:validation:{component_id}:data_flow"
        )
        
        cross_component_state = await self.state_manager.get_state(
            f"component:validation:{component_id}:cross_component"
        )
        
        # Build summary
        summary = {
            "component_id": component_id,
            "feature_dependencies_validated": feature_dependencies_state == True if feature_dependencies_state else False,
            "feature_relationships_validated": feature_relationships_state == True if feature_relationships_state else False,
            "data_flow_validated": data_flow_state == True if data_flow_state else False,
            "cross_component_validated": cross_component_state == True if cross_component_state else False,
            "timestamp": datetime.now().isoformat()
        }
        
        return summary
        
    def _find_duplicate_feature_ids(
        self, 
        features: List[Dict[str, Any]]
    ) -> List[str]:
        """Find duplicate feature IDs in a list of features."""
        ids = {}
        duplicates = []
        
        for feature in features:
            feature_id = feature.get("id")
            if not feature_id:
                continue
                
            if feature_id in ids:
                duplicates.append(feature_id)
            else:
                ids[feature_id] = True
                
        return duplicates
        
    def _find_undefined_dependencies(
        self, 
        features: List[Dict[str, Any]], 
        feature_ids: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find dependencies on undefined features."""
        undefined_deps = []
        
        for feature in features:
            feature_id = feature.get("id")
            dependencies = feature.get("dependencies", [])
            
            if not feature_id or not dependencies:
                continue
                
            # Check each dependency
            for dep in dependencies:
                if dep not in feature_ids:
                    undefined_deps.append({
                        "feature_id": feature_id,
                        "dependency": dep
                    })
                    
        return undefined_deps
        
    def _find_circular_dependencies(
        self, 
        features: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find circular dependencies in feature relationships."""
        circular_deps = []
        
        # Build dependency graph
        graph = {}
        for feature in features:
            feature_id = feature.get("id")
            dependencies = feature.get("dependencies", [])
            
            if not feature_id:
                continue
                
            graph[feature_id] = dependencies
            
        # Check for cycles using DFS
        visited = set()
        path = set()
        
        def dfs(node: str, path_so_far: List[str]):
            nonlocal visited, path, circular_deps
            
            visited.add(node)
            path.add(node)
            path_so_far.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path_so_far[:])
                elif neighbor in path:
                    # Found a cycle
                    cycle_path = path_so_far + [neighbor]
                    
                    # Find the start of the cycle
                    start_idx = cycle_path.index(neighbor)
                    cycle = cycle_path[start_idx:]
                    
                    circular_deps.append({
                        "feature_id": node,
                        "dependency_chain": cycle
                    })
            
            path.remove(node)
            
        # Run DFS for each node
        for feature in features:
            feature_id = feature.get("id")
            
            if not feature_id or feature_id in visited:
                continue
                
            dfs(feature_id, [])
            
        return circular_deps
        
    def _find_duplicate_relationships(
        self, 
        relationships: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find duplicate relationships between features."""
        seen_relationships = {}
        duplicates = []
        
        for relationship in relationships:
            source_id = relationship.get("source_id")
            target_id = relationship.get("target_id")
            
            if not source_id or not target_id:
                continue
                
            relationship_key = f"{source_id}:{target_id}"
            
            if relationship_key in seen_relationships:
                duplicates.append({
                    "source_id": source_id,
                    "target_id": target_id
                })
            else:
                seen_relationships[relationship_key] = relationship
                
        return duplicates
        
    def _find_conflicting_relationships(
        self, 
        relationships: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find conflicting relationship types between features."""
        relationship_types = {}
        conflicts = []
        
        for relationship in relationships:
            source_id = relationship.get("source_id")
            target_id = relationship.get("target_id")
            relationship_type = relationship.get("type")
            
            if not source_id or not target_id or not relationship_type:
                continue
                
            relationship_key = f"{source_id}:{target_id}"
            
            if relationship_key in relationship_types:
                # Check if types conflict
                existing_type = relationship_types[relationship_key]
                
                if existing_type != relationship_type:
                    conflicts.append({
                        "source_id": source_id,
                        "target_id": target_id,
                        "types": [existing_type, relationship_type]
                    })
            else:
                relationship_types[relationship_key] = relationship_type
                
        return conflicts
        
    async def _get_all_components(self) -> List[Dict[str, Any]]:
        """Get all defined components from state manager."""
        components = []
        
        # Get all component states
        component_states = await self.state_manager.get_states_by_prefix("component:info:")
        
        for state_key, state in component_states.items():
            if hasattr(state, 'state') and isinstance(state.state, dict):
                components.append(state.state)
                
        return components
        
    async def _find_circular_component_dependencies(
        self, 
        component_id: str, 
        direct_dependencies: List[str]
    ) -> List[Dict[str, Any]]:
        """Find circular dependencies in component relationships."""
        circular_deps = []
        
        # Build dependency graph
        graph = {component_id: direct_dependencies}
        
        # Get all components and their dependencies
        all_components = await self._get_all_components()
        
        for component in all_components:
            comp_id = component.get("id")
            dependencies = component.get("dependencies", [])
            
            if not comp_id or comp_id == component_id:
                continue
                
            graph[comp_id] = dependencies
            
        # Check for cycles using DFS
        visited = set()
        path = set()
        
        def dfs(node: str, path_so_far: List[str]):
            nonlocal visited, path, circular_deps
            
            visited.add(node)
            path.add(node)
            path_so_far.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path_so_far[:])
                elif neighbor in path:
                    # Found a cycle
                    cycle_path = path_so_far + [neighbor]
                    
                    # Find the start of the cycle
                    start_idx = cycle_path.index(neighbor)
                    cycle = cycle_path[start_idx:]
                    
                    circular_deps.append({
                        "component_id": node,
                        "dependency_chain": cycle
                    })
            
            path.remove(node)
            
        # Run DFS starting from our component
        dfs(component_id, [])
            
        return circular_deps