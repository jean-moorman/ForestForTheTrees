"""
Dependency Resolver
================

This module provides enhanced dependency resolution for components,
including cycle detection, validation, and parallel processing capabilities.
"""

import logging
import asyncio
import time
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict, deque

from resources import (
    StateManager,
    MetricsManager,
    ResourceType
)

from dependency import DependencyValidator

logger = logging.getLogger(__name__)

class DependencyResolver:
    """
    Enhanced dependency resolver for component orchestration.
    
    Key responsibilities:
    1. Enhanced component sorting based on dependency graph
    2. Cycle detection and resolution
    3. Parallel processing of independent components
    4. Dependency validation against core system requirements
    """
    
    def __init__(self, state_manager: StateManager, metrics_manager: MetricsManager):
        """
        Initialize the DependencyResolver.
        
        Args:
            state_manager: StateManager for state persistence
            metrics_manager: MetricsManager for metrics recording
        """
        self._state_manager = state_manager
        self._metrics_manager = metrics_manager
        
        # Initialize dependency validator for structural validation
        self._dependency_validator = DependencyValidator(state_manager)
        
        # Component dependency graph
        self._dependency_graph: Dict[str, Set[str]] = {}
        self._reverse_graph: Dict[str, Set[str]] = {}
        
        # Cache for already sorted components
        self._sorted_components_cache: Dict[str, List[Dict[str, Any]]] = {}
        
        # Cache for components that have been validated
        self._validated_components: Set[str] = set()
    
    async def sort_components(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort components based on dependencies, from most fundamental to least.
        
        This method uses a topological sort to ensure components are processed
        in the correct order based on their dependencies.
        
        Args:
            components: List of component definitions
            
        Returns:
            Sorted list of component definitions
        """
        # Check cache first
        cache_key = self._generate_cache_key(components)
        if cache_key in self._sorted_components_cache:
            logger.debug(f"Using cached component sort for {len(components)} components")
            return self._sorted_components_cache[cache_key]
        
        # Build dependency graph
        self._build_dependency_graph(components)
        
        # Perform topological sort
        sorted_components = await self._topological_sort(components)
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:dependency:components_sorted",
            len(components),
            metadata={
                "component_count": len(components),
                "sorted_count": len(sorted_components)
            }
        )
        
        # Cache the result
        self._sorted_components_cache[cache_key] = sorted_components
        
        logger.info(f"Sorted {len(components)} components based on dependencies")
        return sorted_components
    
    def _build_dependency_graph(self, components: List[Dict[str, Any]]) -> None:
        """
        Build dependency graphs from component definitions.
        
        Args:
            components: List of component definitions
        """
        # Clear existing graphs
        self._dependency_graph.clear()
        self._reverse_graph.clear()
        
        # Build component ID map for quick lookups
        component_map = {c.get("id", f"comp_{int(time.time())}"): c for c in components}
        
        # Build dependency graph
        for component in components:
            component_id = component.get("id", f"comp_{int(time.time())}")
            
            # Initialize dependency sets
            if component_id not in self._dependency_graph:
                self._dependency_graph[component_id] = set()
            
            # Get dependencies
            dependencies = component.get("dependencies", [])
            
            # Add edges to dependency graph
            for dep_id in dependencies:
                # Skip if dependency doesn't exist
                if dep_id not in component_map:
                    logger.warning(f"Component {component_id} depends on unknown component {dep_id}")
                    continue
                
                # Initialize if not already present
                if dep_id not in self._dependency_graph:
                    self._dependency_graph[dep_id] = set()
                
                # Add to dependency graph
                self._dependency_graph[component_id].add(dep_id)
                
                # Add to reverse graph
                if dep_id not in self._reverse_graph:
                    self._reverse_graph[dep_id] = set()
                self._reverse_graph[dep_id].add(component_id)
    
    async def _topological_sort(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Perform topological sort on components based on dependency graph.
        
        Args:
            components: List of component definitions
            
        Returns:
            Sorted list of component definitions
        """
        # Create a copy of the graph
        graph = {node: set(edges) for node, edges in self._dependency_graph.items()}
        
        # Create component map for quick lookup
        component_map = {c.get("id", f"comp_{int(time.time())}"): c for c in components}
        
        # Find nodes with no incoming edges (no dependencies)
        in_degree = {node: 0 for node in graph}
        for node in graph:
            for dep in graph[node]:
                in_degree[dep] = in_degree.get(dep, 0) + 1
        
        # Queue of nodes with no dependencies
        queue = deque([node for node in graph if in_degree.get(node, 0) == 0])
        
        # Result list
        sorted_ids = []
        
        # Process queue
        while queue:
            # Get node with no dependencies
            node = queue.popleft()
            sorted_ids.append(node)
            
            # Remove edges from the graph
            for dep in graph.get(node, set()).copy():
                in_degree[dep] -= 1
                
                # If dependent now has no dependencies, add to queue
                if in_degree[dep] == 0:
                    queue.append(dep)
        
        # Check if all nodes were sorted
        if len(sorted_ids) != len(graph):
            logger.warning(f"Not all components sorted. Remaining: {set(graph.keys()) - set(sorted_ids)}")
            
            # Fall back to simpler method - sort by dependency count
            remaining = list(set(graph.keys()) - set(sorted_ids))
            dependency_count = {node: len(graph.get(node, set())) for node in remaining}
            remaining_sorted = sorted(remaining, key=lambda x: dependency_count[x])
            
            # Append remaining nodes
            sorted_ids.extend(remaining_sorted)
        
        # Map back to component definitions
        sorted_components = [component_map[component_id] for component_id in sorted_ids if component_id in component_map]
        
        return sorted_components
    
    async def detect_cycles(self, components: List[Dict[str, Any]]) -> List[List[str]]:
        """
        Detect cycles in component dependencies.
        
        Args:
            components: List of component definitions
            
        Returns:
            List of cycles found (as lists of component IDs)
        """
        # Build dependency graph if not already built
        if not self._dependency_graph:
            self._build_dependency_graph(components)
        
        # Use Tarjan's algorithm to find strongly connected components
        # These represent cycles in the graph
        index_counter = [0]
        indices = {}
        lowlink = {}
        onstack = set()
        stack = []
        cycles = []
        
        def strongconnect(node):
            # Set the depth index for node
            indices[node] = index_counter[0]
            lowlink[node] = index_counter[0]
            index_counter[0] += 1
            stack.append(node)
            onstack.add(node)
            
            # Consider successors of node
            for successor in self._dependency_graph.get(node, []):
                if successor not in indices:
                    # Successor has not yet been visited; recurse on it
                    strongconnect(successor)
                    lowlink[node] = min(lowlink[node], lowlink[successor])
                elif successor in onstack:
                    # Successor is on the stack and hence in the current SCC
                    lowlink[node] = min(lowlink[node], indices[successor])
            
            # If node is a root node, pop the stack and generate an SCC
            if lowlink[node] == indices[node]:
                # Start a new strongly connected component
                scc = []
                while True:
                    successor = stack.pop()
                    onstack.remove(successor)
                    scc.append(successor)
                    if successor == node:
                        break
                
                # Only report SCCs of size > 1
                if len(scc) > 1:
                    cycles.append(scc)
        
        # Start DFS from each node
        for node in self._dependency_graph:
            if node not in indices:
                strongconnect(node)
        
        # Record cycle detection metric
        if cycles:
            await self._metrics_manager.record_metric(
                "phase_two:dependency:cycles_detected",
                len(cycles),
                metadata={
                    "component_count": len(components),
                    "cycle_count": len(cycles)
                }
            )
            
            logger.warning(f"Detected {len(cycles)} cycles in component dependencies")
        
        return cycles
    
    async def detect_and_resolve_cycles(self, components: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Detect and attempt to resolve cycles in dependencies.
        
        Args:
            components: List of component definitions
            
        Returns:
            Tuple of (resolved_components, unresolvable_cycles)
        """
        # Build dependency graph if not already built
        if not self._dependency_graph:
            self._build_dependency_graph(components)
        
        # Detect cycles
        cycles = await self.detect_cycles(components)
        
        if not cycles:
            # No cycles to resolve
            return components, []
        
        # Create component map for quick lookup
        component_map = {c.get("id", f"comp_{int(time.time())}"): c for c in components}
        
        # Attempt to resolve cycles
        resolvable_cycles = []
        unresolvable_cycles = []
        
        for cycle in cycles:
            # Try to resolve by finding the most fundamental component in the cycle
            # (the one with the fewest dependencies outside the cycle)
            if await self._try_resolve_cycle(cycle, component_map):
                resolvable_cycles.append(cycle)
            else:
                unresolvable_cycles.append({
                    "cycle": cycle,
                    "components": [component_map.get(c, {"id": c}) for c in cycle]
                })
        
        # Rebuild dependency graph with resolved cycles
        self._build_dependency_graph([component_map[c] for c in component_map])
        
        # Get sorted components
        resolved_components = await self._topological_sort(components)
        
        # Record resolution metric
        await self._metrics_manager.record_metric(
            "phase_two:dependency:cycles_resolved",
            len(resolvable_cycles),
            metadata={
                "component_count": len(components),
                "cycle_count": len(cycles),
                "resolved_count": len(resolvable_cycles),
                "unresolvable_count": len(unresolvable_cycles)
            }
        )
        
        return resolved_components, unresolvable_cycles
    
    async def _try_resolve_cycle(self, cycle: List[str], component_map: Dict[str, Dict[str, Any]]) -> bool:
        """
        Try to resolve a cycle by breaking the least important dependency.
        
        Args:
            cycle: List of component IDs forming a cycle
            component_map: Map of component ID to component definition
            
        Returns:
            True if cycle could be resolved, False otherwise
        """
        # Calculate external dependencies for each component in the cycle
        external_dependencies = {}
        for component_id in cycle:
            # Get all dependencies
            dependencies = set(component_map.get(component_id, {}).get("dependencies", []))
            # Filter to only those outside the cycle
            external = dependencies - set(cycle)
            external_dependencies[component_id] = external
        
        # Candidates for breaking the cycle are components with fewest external dependencies
        # This preserves the most important dependency relationships
        candidates = sorted(cycle, key=lambda c: len(external_dependencies[c]))
        
        if not candidates:
            return False
        
        # Select the component with fewest external dependencies
        to_break = candidates[0]
        
        # Find which dependencies to remove
        deps_to_remove = set(component_map.get(to_break, {}).get("dependencies", [])) & set(cycle)
        
        # Break the cycle by removing dependencies
        if to_break in component_map and deps_to_remove:
            # Get current dependencies
            current_deps = set(component_map[to_break].get("dependencies", []))
            
            # Remove cyclic dependencies
            new_deps = current_deps - deps_to_remove
            
            # Update component
            component_map[to_break]["dependencies"] = list(new_deps)
            
            # Add comment about broken cycle
            if "metadata" not in component_map[to_break]:
                component_map[to_break]["metadata"] = {}
            
            if "broken_cycles" not in component_map[to_break]["metadata"]:
                component_map[to_break]["metadata"]["broken_cycles"] = []
                
            component_map[to_break]["metadata"]["broken_cycles"].append({
                "cycle": cycle,
                "removed_dependencies": list(deps_to_remove),
                "timestamp": time.time()
            })
            
            logger.info(f"Resolved cycle {cycle} by removing dependencies {deps_to_remove} from component {to_break}")
            return True
        
        return False
    
    def find_independent_components(self, components: List[Dict[str, Any]]) -> List[Set[str]]:
        """
        Find sets of components that can be processed independently.
        
        This method identifies components with no dependencies on each other,
        allowing for parallel processing.
        
        Args:
            components: List of component definitions
            
        Returns:
            List of sets of component IDs that can be processed independently
        """
        # Build dependency graph if not already built
        if not self._dependency_graph:
            self._build_dependency_graph(components)
        
        # Create component map for quick lookup
        component_map = {c.get("id", f"comp_{int(time.time())}"): c for c in components}
        
        # Get independent sets by analyzing DAG levels
        independent_sets = []
        processed = set()
        
        while len(processed) < len(component_map):
            # Find components with all dependencies satisfied
            current_set = set()
            for component_id in component_map:
                if component_id in processed:
                    continue
                    
                dependencies = self._dependency_graph.get(component_id, set())
                if dependencies.issubset(processed):
                    current_set.add(component_id)
            
            # If no components found, there may be a cycle
            if not current_set:
                logger.warning("No independent components found, possible cycle")
                # Add all remaining components to the set
                current_set = set(component_map.keys()) - processed
            
            # Add the set
            independent_sets.append(current_set)
            
            # Mark as processed
            processed.update(current_set)
        
        logger.info(f"Found {len(independent_sets)} independent component sets for parallel processing")
        return independent_sets
    
    async def validate_component(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a component definition.
        
        Args:
            component: Component definition to validate
            
        Returns:
            Dictionary with validation result
        """
        component_id = component.get("id", f"comp_{int(time.time())}")
        
        # Check if already validated
        if component_id in self._validated_components:
            logger.debug(f"Component {component_id} already validated")
            return {"is_valid": True, "component_id": component_id}
        
        errors = []
        
        # Check required fields
        required_fields = ["id", "name", "description"]
        for field in required_fields:
            if field not in component:
                errors.append({
                    "field": field,
                    "error_type": "missing_field",
                    "message": f"Required field '{field}' is missing"
                })
        
        # Check dependencies
        if "dependencies" in component:
            deps = component["dependencies"]
            if not isinstance(deps, list):
                errors.append({
                    "field": "dependencies",
                    "error_type": "invalid_type",
                    "message": f"Dependencies must be a list, got {type(deps)}"
                })
            else:
                # Check for self-reference
                if component_id in deps:
                    errors.append({
                        "field": "dependencies",
                        "error_type": "self_reference",
                        "message": f"Component {component_id} cannot depend on itself"
                    })
        
        # Check features if present
        if "features" in component:
            features = component["features"]
            if not isinstance(features, list):
                errors.append({
                    "field": "features",
                    "error_type": "invalid_type",
                    "message": f"Features must be a list, got {type(features)}"
                })
            else:
                # Check each feature
                for i, feature in enumerate(features):
                    # Check required feature fields
                    for field in ["id", "name", "description"]:
                        if field not in feature:
                            errors.append({
                                "field": f"features[{i}].{field}",
                                "error_type": "missing_field",
                                "message": f"Required field '{field}' is missing in feature #{i}"
                            })
        
        # Use dependency validator for more detailed validation if available
        try:
            structural_result = await self._validate_structural_requirements(component)
            if not structural_result["is_valid"]:
                errors.extend(structural_result["errors"])
        except Exception as e:
            logger.error(f"Error in structural validation: {str(e)}")
            errors.append({
                "field": "structure",
                "error_type": "validation_error",
                "message": f"Structural validation error: {str(e)}"
            })
        
        # Determine validation result
        is_valid = len(errors) == 0
        
        # Mark as validated if valid
        if is_valid:
            self._validated_components.add(component_id)
        
        # Record validation metric
        await self._metrics_manager.record_metric(
            "phase_two:dependency:component_validation",
            1.0,
            metadata={
                "component_id": component_id,
                "is_valid": is_valid,
                "error_count": len(errors)
            }
        )
        
        return {
            "is_valid": is_valid,
            "component_id": component_id,
            "errors": errors
        }
    
    async def _validate_structural_requirements(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate component against structural requirements.
        
        Args:
            component: Component definition to validate
            
        Returns:
            Dictionary with validation result
        """
        # Get system requirements
        system_requirements = await self._state_manager.get_state("system:requirements")
        if not system_requirements:
            logger.warning("No system requirements found for validation")
            return {"is_valid": True, "errors": []}
        
        # Validate against system structural breakdown if available
        structural_breakdown = system_requirements.get("structural_breakdown", {})
        
        if not structural_breakdown:
            logger.warning("No structural breakdown found for validation")
            return {"is_valid": True, "errors": []}
        
        # Create test structure with only this component
        test_structure = {
            "ordered_components": [component]
        }
        
        # Use dependency validator
        is_valid, errors = await self._dependency_validator.validate_structural_breakdown(test_structure)
        
        return {
            "is_valid": is_valid,
            "errors": errors
        }
    
    async def validate_against_core_requirements(self, 
                                              component: Dict[str, Any],
                                              system_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate component against core system requirements.
        
        Args:
            component: Component definition to validate
            system_requirements: System requirements
            
        Returns:
            Dictionary with validation result
        """
        errors = []
        
        # Extract relevant requirements
        component_id = component.get("id", "")
        component_name = component.get("name", "")
        component_type = component.get("type", "")
        
        # Check against core requirements if available
        if "components" in system_requirements:
            for req_component in system_requirements["components"]:
                # If ID or name matches, validate against requirements
                if (req_component.get("id") == component_id or 
                    req_component.get("name") == component_name):
                    
                    # Check type
                    if "type" in req_component and component_type != req_component["type"]:
                        errors.append({
                            "field": "type",
                            "error_type": "type_mismatch",
                            "message": f"Component type should be '{req_component['type']}', got '{component_type}'",
                            "expected": req_component["type"],
                            "actual": component_type
                        })
                    
                    # Check required dependencies
                    if "required_dependencies" in req_component:
                        component_deps = set(component.get("dependencies", []))
                        required_deps = set(req_component["required_dependencies"])
                        missing_deps = required_deps - component_deps
                        
                        if missing_deps:
                            errors.append({
                                "field": "dependencies",
                                "error_type": "missing_dependencies",
                                "message": f"Missing required dependencies: {missing_deps}",
                                "missing": list(missing_deps)
                            })
                    
                    # Check required features
                    if "required_features" in req_component:
                        component_features = set(f["id"] for f in component.get("features", []))
                        required_features = set(req_component["required_features"])
                        missing_features = required_features - component_features
                        
                        if missing_features:
                            errors.append({
                                "field": "features",
                                "error_type": "missing_features",
                                "message": f"Missing required features: {missing_features}",
                                "missing": list(missing_features)
                            })
        
        # Determine validation result
        is_valid = len(errors) == 0
        
        # Record validation metric
        await self._metrics_manager.record_metric(
            "phase_two:dependency:core_requirements_validation",
            1.0,
            metadata={
                "component_id": component_id,
                "is_valid": is_valid,
                "error_count": len(errors)
            }
        )
        
        return {
            "is_valid": is_valid,
            "component_id": component_id,
            "errors": errors
        }
    
    def _generate_cache_key(self, components: List[Dict[str, Any]]) -> str:
        """
        Generate a cache key for the components list.
        
        Args:
            components: List of component definitions
            
        Returns:
            Cache key string
        """
        # Use component IDs and dependencies to create a unique key
        component_deps = []
        for comp in components:
            comp_id = comp.get("id", "")
            deps = sorted(comp.get("dependencies", []))
            component_deps.append(f"{comp_id}:{','.join(deps)}")
            
        return "|".join(sorted(component_deps))
    
    async def clear_cache(self) -> None:
        """Clear the cache."""
        self._sorted_components_cache.clear()
        self._validated_components.clear()
        self._dependency_graph.clear()
        self._reverse_graph.clear()
        
        logger.info("Dependency resolver cache cleared")