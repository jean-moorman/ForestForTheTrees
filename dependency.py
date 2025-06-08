"""
Core Classes:
DependencyManager: Manages dependency relationships and DAG
DependencyInterface: Inherits from BaseInterface for dependency management
DevelopmentPath: Handles development path ordering and holding points
BranchState: Manages branch states during development

Key Features:
DAG-based dependency tracking
Development path management
Holding point coordination
Branch state management
Resource reservation
Event propagation
Monitoring integration

Design Decisions:
Used inheritance from BaseInterface for consistency
Implemented DAG for dependency relationships
Integrated with resource management for state persistence
Added comprehensive validation mechanisms
Included monitoring hooks
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
from datetime import datetime
from collections import defaultdict

from interfaces.base import BaseInterface
from resources import ResourceState, ResourceState, StateManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DependencyType(Enum):
    PRIMARY = auto()
    SECONDARY = auto()
    AUXILIARY = auto()
    COMPONENT_TO_FEATURE = auto()
    FEATURE_TO_FUNCTIONALITY = auto()
    HIERARCHICAL = auto()  # Special type for hierarchical dependencies

class BranchState(Enum):
    ACTIVE = auto()
    HOLDING = auto()
    PENDING = auto()
    RESUMED = auto()
    COMPLETED = auto()

@dataclass
class DevelopmentPath:
    path_id: str
    components: List[str]
    priority: int = 0
    holding_points: Set[str] = field(default_factory=set)
    branch_state: BranchState = BranchState.PENDING
    resources_reserved: Dict[str, Any] = field(default_factory=dict)

class DependencyInterface(BaseInterface):
    """Dependency management interface inheriting from BaseInterface."""
    
    def __init__(self, component_id: str, 
                 event_queue=None, state_manager=None, context_manager=None, 
                 cache_manager=None, metrics_manager=None, error_handler=None, 
                 memory_monitor=None):
        # Create mock managers if not provided (for testing)
        if event_queue is None:
            from unittest.mock import MagicMock
            event_queue = MagicMock()
            state_manager = MagicMock()
            context_manager = MagicMock()
            cache_manager = MagicMock()
            metrics_manager = MagicMock()
            error_handler = MagicMock()
            memory_monitor = MagicMock()
            
        super().__init__(
            f"dependency:{component_id}",
            event_queue, state_manager, context_manager,
            cache_manager, metrics_manager, error_handler, memory_monitor
        )
        
        self._dependency_type = DependencyType.SECONDARY
        self._development_paths: Dict[str, DevelopmentPath] = {}
        self._dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self._reverse_graph: Dict[str, Set[str]] = defaultdict(set)
        self._holding_points: Dict[str, Set[str]] = defaultdict(set)
        self._validation_errors: List[Dict[str, Any]] = []
        
        # Register with resource manager if available
        if hasattr(self, '_state_manager') and self._state_manager and hasattr(self._state_manager, 'set_state'):
            try:
                self._state_manager.set_state(
                    f"dependency:{self.interface_id}:type",
                    self._dependency_type
                )
            except Exception:
                # Ignore errors during testing
                pass

    def set_dependency_type(self, dep_type: DependencyType) -> None:
        """Set the dependency type."""
        old_type = self._dependency_type
        self._dependency_type = dep_type
        
        # Update state in resource manager
        self._resource_manager.set_state(
            f"dependency:{self.interface_id}:type",
            dep_type,
            metadata={"old_type": old_type}
        )
        
        # Emit type change event
        self._resource_manager.emit_event(
            "dependency_type_changed",
            {
                "interface_id": self.interface_id,
                "old_type": old_type,
                "new_type": dep_type
            }
        )

    def add_node(self, node_id: str) -> None:
        """Add a node to the dependency graph without any dependencies."""
        if node_id not in self._dependency_graph:
            self._dependency_graph[node_id] = set()
            self._reverse_graph[node_id] = set()
            
            # Update state in resource manager
            self._resource_manager.set_state(
                f"dependency:{self.interface_id}:graph:{node_id}",
                []
            )
            
            # Emit node added event
            self._resource_manager.emit_event(
                "dependency_node_added",
                {
                    "interface_id": self.interface_id,
                    "node_id": node_id
                }
            )
        
    def add_dependency(self, dependent: str, dependency: str, dep_type: DependencyType = DependencyType.SECONDARY) -> None:
        """Add a dependency relationship to the DAG."""
        # Ensure both nodes exist
        self.add_node(dependent)
        self.add_node(dependency)
        
        # Check for cycles before adding unless it's a hierarchical dependency
        if dep_type != DependencyType.HIERARCHICAL and self._would_create_cycle(dependent, dependency):
            raise ValueError(f"Adding dependency {dependency} would create a cycle")
            
        self._dependency_graph[dependent].add(dependency)
        self._reverse_graph[dependency].add(dependent)
        
        # Update state in resource manager
        self._resource_manager.set_state(
            f"dependency:{self.interface_id}:graph:{dependent}",
            list(self._dependency_graph[dependent])
        )
        
        # Store the dependency type
        self._resource_manager.set_state(
            f"dependency:{self.interface_id}:type:{dependent}:{dependency}",
            dep_type.name
        )
        
        # Emit dependency added event
        self._resource_manager.emit_event(
            "dependency_added",
            {
                "interface_id": self.interface_id,
                "dependent": dependent,
                "dependency": dependency,
                "dependency_type": dep_type.name
            }
        )
        
    def get_dependencies(self, component_id: str) -> List[str]:
        """Get all dependencies for a component."""
        return list(self._dependency_graph.get(component_id, set()))
        
    def add_hierarchical_dependency(self, parent: str, child: str, hierarchy_type: DependencyType) -> None:
        """Add a hierarchical dependency (component->feature or feature->functionality)."""
        # This is a special type of dependency that might appear to create cycles
        # in the normal dependency graph but is actually a hierarchical relationship
        if hierarchy_type not in (DependencyType.COMPONENT_TO_FEATURE, DependencyType.FEATURE_TO_FUNCTIONALITY):
            raise ValueError(f"Invalid hierarchy type: {hierarchy_type}. Must be COMPONENT_TO_FEATURE or FEATURE_TO_FUNCTIONALITY")
            
        # Add with hierarchical flag to bypass cycle detection
        self.add_dependency(parent, child, dep_type=DependencyType.HIERARCHICAL)
        
        # Also store the specific hierarchy type
        self._resource_manager.set_state(
            f"dependency:{self.interface_id}:hierarchy:{parent}:{child}",
            hierarchy_type.name
        )
        
        # Emit a specific hierarchical dependency event
        self._resource_manager.emit_event(
            "hierarchical_dependency_added",
            {
                "interface_id": self.interface_id,
                "parent": parent,
                "child": child,
                "hierarchy_type": hierarchy_type.name
            }
        )

    def remove_dependency(self, dependent: str, dependency: str) -> None:
        """Remove a dependency relationship from the DAG."""
        self._dependency_graph[dependent].discard(dependency)
        self._reverse_graph[dependency].discard(dependent)
        
        # Update state in resource manager
        self._resource_manager.set_state(
            f"dependency:{self.interface_id}:graph:{dependent}",
            list(self._dependency_graph[dependent])
        )
        
        # Emit dependency removed event
        self._resource_manager.emit_event(
            "dependency_removed",
            {
                "interface_id": self.interface_id,
                "dependent": dependent,
                "dependency": dependency
            }
        )

    def _would_create_cycle(self, dependent: str, dependency: str) -> bool:
        """Check if adding a dependency would create a cycle."""
        visited = set()
        
        def dfs(node: str) -> bool:
            if node == dependent:
                return True
            visited.add(node)
            for next_node in self._dependency_graph[node]:
                if next_node not in visited and dfs(next_node):
                    return True
            return False
            
        return dfs(dependency)

    def get_development_order(self) -> List[Set[str]]:
        """Get ordered development layers based on dependencies."""
        in_degree = defaultdict(int)
        for node in self._dependency_graph:
            for dep in self._dependency_graph[node]:
                in_degree[dep] += 1
                
        # Start with nodes that have no dependencies
        ready = {node for node in self._dependency_graph 
                if in_degree.get(node, 0) == 0}
        result = []
        
        while ready:
            result.append(ready)
            next_ready = set()
            
            for node in ready:
                for dependent in self._reverse_graph[node]:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        next_ready.add(dependent)
                        
            ready = next_ready
            
        return result

    def create_development_path(self, path_id: str, components: List[str], 
                              priority: int = 0) -> DevelopmentPath:
        """Create a new development path."""
        path = DevelopmentPath(
            path_id=path_id,
            components=components,
            priority=priority
        )
        self._development_paths[path_id] = path
        
        # Register with resource manager
        self._resource_manager.set_state(
            f"dependency:{self.interface_id}:path:{path_id}",
            {
                "components": components,
                "priority": priority,
                "state": path.branch_state
            }
        )
        
        return path

    def add_holding_point(self, path_id: str, component_id: str) -> None:
        """Add a holding point to a development path."""
        if path_id not in self._development_paths:
            raise ValueError(f"Development path not found: {path_id}")
            
        path = self._development_paths[path_id]
        if component_id not in path.components:
            raise ValueError(f"Component not in path: {component_id}")
            
        path.holding_points.add(component_id)
        path.branch_state = BranchState.HOLDING
        
        # Update state in resource manager
        self._resource_manager.set_state(
            f"dependency:{self.interface_id}:path:{path_id}:holding_points",
            list(path.holding_points)
        )
        self._resource_manager.set_state(
            f"dependency:{self.interface_id}:path:{path_id}:state",
            path.branch_state
        )
        
        # Reserve resources for holding branch
        self._reserve_branch_resources(path_id)

    def resume_development(self, path_id: str, component_id: str) -> None:
        """Resume development after a holding point."""
        if path_id not in self._development_paths:
            raise ValueError(f"Development path not found: {path_id}")
            
        path = self._development_paths[path_id]
        if component_id not in path.holding_points:
            raise ValueError(f"No holding point found: {component_id}")
            
        path.holding_points.remove(component_id)
        if not path.holding_points:
            path.branch_state = BranchState.RESUMED
            
        # Update state in resource manager
        self._resource_manager.set_state(
            f"dependency:{self.interface_id}:path:{path_id}:holding_points",
            list(path.holding_points)
        )
        self._resource_manager.set_state(
            f"dependency:{self.interface_id}:path:{path_id}:state",
            path.branch_state
        )
        
        # Release reserved resources
        self._release_branch_resources(path_id)

    def _reserve_branch_resources(self, path_id: str) -> None:
        """Reserve resources for a holding branch."""
        path = self._development_paths[path_id]
        
        # Basic resource reservation - can be extended
        resources = {
            "memory": "standard",
            "state": "preserved",
            "context": "maintained"
        }
        
        path.resources_reserved = resources
        self._resource_manager.set_state(
            f"dependency:{self.interface_id}:path:{path_id}:resources",
            resources
        )

    def _release_branch_resources(self, path_id: str) -> None:
        """Release reserved resources for a branch."""
        path = self._development_paths[path_id]
        path.resources_reserved.clear()
        
        self._resource_manager.set_state(
            f"dependency:{self.interface_id}:path:{path_id}:resources",
            {}
        )

    def validate(self) -> bool:
        """Validate dependency interface state."""
        # First validate base interface
        if not super().validate_dependencies():
            return False
            
        # Clear previous validation errors
        self._validation_errors = []
        
        # Validate dependency graph
        for dependent, dependencies in self._dependency_graph.items():
            for dependency in dependencies:
                # Check for cycles
                if self._would_create_cycle(dependent, dependency):
                    error = {
                        "error_type": "cycle_detected",
                        "dependent": dependent,
                        "dependency": dependency,
                        "message": f"Cycle detected in dependency graph: {dependent} -> {dependency}"
                    }
                    self._validation_errors.append(error)
                    logger.error(error["message"])
                    return False
                    
                # Validate dependency states
                dep_state = self._resource_manager.get_state(f"interface:{dependency}:state")
                if dep_state not in (ResourceState.ACTIVE, ResourceState.PROPAGATING):
                    error = {
                        "error_type": "invalid_dependency_state",
                        "dependent": dependent,
                        "dependency": dependency,
                        "state": dep_state,
                        "message": f"Invalid dependency state: {dependency} -> {dep_state}"
                    }
                    self._validation_errors.append(error)
                    logger.error(error["message"])
                    return False
                    
        # Validate development paths
        for path_id, path in self._development_paths.items():
            # Check component existence
            for component in path.components:
                if not self._resource_manager.verify_resource_health(f"interface:{component}"):
                    error = {
                        "error_type": "unhealthy_component",
                        "path_id": path_id,
                        "component": component,
                        "message": f"Unhealthy component in path {path_id}: {component}"
                    }
                    self._validation_errors.append(error)
                    logger.error(error["message"])
                    return False
                    
            # Validate holding points
            for holding_point in path.holding_points:
                if holding_point not in path.components:
                    error = {
                        "error_type": "invalid_holding_point",
                        "path_id": path_id,
                        "holding_point": holding_point,
                        "message": f"Invalid holding point in path {path_id}: {holding_point}"
                    }
                    self._validation_errors.append(error)
                    logger.error(error["message"])
                    return False
                    
        return True
                    
    def get_validation_errors(self) -> List[Dict[str, Any]]:
        """Get all validation errors from the last validation run."""
        return self._validation_errors.copy()
        
    def validate_data_flow(self, data_flow: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate data flow structure in real-time.
        
        Args:
            data_flow: The data flow structure to validate
            
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        # Verify data flow basic structure
        if not isinstance(data_flow, dict):
            errors.append({
                "error_type": "invalid_data_flow_structure",
                "message": "Data flow must be a dictionary"
            })
            return False, errors
            
        # Verify data flows
        if "data_flows" not in data_flow:
            errors.append({
                "error_type": "missing_data_flows",
                "message": "Data flow must contain 'data_flows' key"
            })
            return False, errors
            
        flows = data_flow.get("data_flows", [])
        
        # Track source-destination pairs to detect duplicates
        flow_pairs = set()
        
        # Check each flow
        for i, flow in enumerate(flows):
            # Check required fields
            required_fields = ["source", "destination", "data_type"]
            for field in required_fields:
                if field not in flow:
                    errors.append({
                        "error_type": "missing_field",
                        "flow_index": i,
                        "field": field,
                        "message": f"Flow missing required field: {field}"
                    })
            
            # Skip further validation if required fields are missing
            if any(field not in flow for field in required_fields):
                continue
                
            # Check for self-reference
            if flow["source"] == flow["destination"]:
                errors.append({
                    "error_type": "self_reference",
                    "flow_index": i,
                    "source": flow["source"],
                    "message": f"Flow cannot have same source and destination: {flow['source']}"
                })
                
            # Check for duplicate flows
            flow_pair = (flow["source"], flow["destination"])
            if flow_pair in flow_pairs:
                errors.append({
                    "error_type": "duplicate_flow",
                    "flow_index": i,
                    "source": flow["source"],
                    "destination": flow["destination"],
                    "message": f"Duplicate flow from {flow['source']} to {flow['destination']}"
                })
            flow_pairs.add(flow_pair)
            
        # Check for cycles in the data flow graph
        graph = defaultdict(set)
        for flow in flows:
            if "source" in flow and "destination" in flow:
                graph[flow["source"]].add(flow["destination"])
                
        # Detect cycles using DFS
        visited = set()
        recursion_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            recursion_stack.add(node)
            
            for neighbor in graph[node]:
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in recursion_stack:
                    errors.append({
                        "error_type": "data_flow_cycle",
                        "cycle_node": node,
                        "cycle_next": neighbor,
                        "message": f"Cycle detected in data flow: {node} -> {neighbor}"
                    })
                    return True
                    
            recursion_stack.remove(node)
            return False
            
        for node in list(graph.keys()):
            if node not in visited:
                if has_cycle(node):
                    break
                    
        # Return validation result
        return len(errors) == 0, errors
        
    def validate_structural_breakdown(self, structure: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate structural breakdown in real-time.
        
        Args:
            structure: The structural breakdown to validate
            
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        # Verify structure basic format
        if not isinstance(structure, dict):
            errors.append({
                "error_type": "invalid_structure_format",
                "message": "Structure must be a dictionary"
            })
            return False, errors
            
        # Verify components are present
        if "ordered_components" not in structure:
            errors.append({
                "error_type": "missing_components",
                "message": "Structure must contain 'ordered_components' key"
            })
            return False, errors
            
        components = structure.get("ordered_components", [])
        
        # Track component names to detect duplicates
        component_names = set()
        component_sequence_numbers = set()
        
        # Check each component
        for i, component in enumerate(components):
            # Check required fields
            required_fields = ["name", "sequence_number", "dependencies"]
            for field in required_fields:
                if field not in component:
                    errors.append({
                        "error_type": "missing_field",
                        "component_index": i,
                        "field": field,
                        "message": f"Component missing required field: {field}"
                    })
            
            # Skip further validation if required fields are missing
            if any(field not in component for field in required_fields):
                continue
                
            # Check for duplicate names
            if component["name"] in component_names:
                errors.append({
                    "error_type": "duplicate_component_name",
                    "component_index": i,
                    "name": component["name"],
                    "message": f"Duplicate component name: {component['name']}"
                })
            component_names.add(component["name"])
            
            # Check for duplicate sequence numbers
            if component["sequence_number"] in component_sequence_numbers:
                errors.append({
                    "error_type": "duplicate_sequence_number",
                    "component_index": i,
                    "sequence_number": component["sequence_number"],
                    "message": f"Duplicate sequence number: {component['sequence_number']}"
                })
            component_sequence_numbers.add(component["sequence_number"])
            
            # Check dependencies exist
            if "dependencies" in component and "required" in component["dependencies"]:
                for dep in component["dependencies"]["required"]:
                    if dep not in component_names and i > 0:  # Allow forward references for first component
                        errors.append({
                            "error_type": "undefined_dependency",
                            "component_index": i,
                            "component_name": component["name"],
                            "dependency": dep,
                            "message": f"Component {component['name']} depends on undefined component: {dep}"
                        })
        
        # Check for cycles in dependency graph
        graph = defaultdict(set)
        for component in components:
            if "name" in component and "dependencies" in component and "required" in component["dependencies"]:
                name = component["name"]
                for dep in component["dependencies"]["required"]:
                    graph[name].add(dep)
                    
        # Detect cycles using DFS
        visited = set()
        recursion_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            recursion_stack.add(node)
            
            for neighbor in graph[node]:
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in recursion_stack:
                    errors.append({
                        "error_type": "dependency_cycle",
                        "cycle_node": node,
                        "cycle_next": neighbor,
                        "message": f"Cycle detected in component dependencies: {node} -> {neighbor}"
                    })
                    return True
                    
            recursion_stack.remove(node)
            return False
            
        for node in list(graph.keys()):
            if node not in visited:
                if has_cycle(node):
                    break
                    
        # Return validation result
        return len(errors) == 0, errors
        
    def validate_cross_consistency(self, data_flow: Dict[str, Any], structure: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate cross-consistency between data flow and structural breakdown.
        
        Args:
            data_flow: The data flow structure to validate
            structure: The structural breakdown to validate
            
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        # Extract components from structure
        components = []
        if isinstance(structure, dict) and "ordered_components" in structure:
            for comp in structure.get("ordered_components", []):
                if "name" in comp:
                    components.append(comp["name"])
        
        component_set = set(components)
        
        # Extract flows from data flow
        flows = []
        if isinstance(data_flow, dict) and "data_flows" in data_flow:
            flows = data_flow.get("data_flows", [])
            
        # Check each flow references valid components
        for i, flow in enumerate(flows):
            if "source" in flow and flow["source"] != "external" and flow["source"] not in component_set:
                errors.append({
                    "error_type": "flow_invalid_source",
                    "flow_index": i,
                    "source": flow["source"],
                    "message": f"Flow references non-existent source component: {flow['source']}"
                })
                
            if "destination" in flow and flow["destination"] != "external" and flow["destination"] not in component_set:
                errors.append({
                    "error_type": "flow_invalid_destination",
                    "flow_index": i,
                    "destination": flow["destination"],
                    "message": f"Flow references non-existent destination component: {flow['destination']}"
                })
                
        # Verify component dependencies align with data flows
        flow_dependencies = defaultdict(set)
        for flow in flows:
            if "source" in flow and "destination" in flow:
                if flow["source"] != "external" and flow["destination"] != "external":
                    flow_dependencies[flow["destination"]].add(flow["source"])
                    
        for i, comp in enumerate(structure.get("ordered_components", [])):
            if "name" not in comp or "dependencies" not in comp or "required" not in comp["dependencies"]:
                continue
                
            comp_name = comp["name"]
            comp_deps = set(comp["dependencies"]["required"])
            flow_deps = flow_dependencies.get(comp_name, set())
            
            # Check if data flow dependencies are reflected in structural dependencies
            for flow_dep in flow_deps:
                if flow_dep not in comp_deps:
                    errors.append({
                        "error_type": "missing_structural_dependency",
                        "component_name": comp_name,
                        "data_flow_dependency": flow_dep,
                        "message": f"Component {comp_name} has data flow from {flow_dep} but missing structural dependency"
                    })
                    
            # Check if structural dependencies have corresponding data flows
            for struct_dep in comp_deps:
                if struct_dep not in flow_deps and struct_dep in component_set:
                    errors.append({
                        "error_type": "missing_data_flow",
                        "component_name": comp_name,
                        "structural_dependency": struct_dep,
                        "message": f"Component {comp_name} depends on {struct_dep} but no data flow exists"
                    })
        
        return len(errors) == 0, errors

def register_dependency_metrics(dependency_interface: DependencyInterface) -> None:
    """Register monitoring metrics for dependency interface."""
    from resources.events import EventQueue
    event_queue = EventQueue()
    resource_manager = StateManager(event_queue)
    
    # Register dependency graph metrics
    for dependent, dependencies in dependency_interface._dependency_graph.items():
        resource_manager.record_metric(
            f"dependency:{dependency_interface.interface_id}:node:{dependent}:outdegree",
            len(dependencies)
        )
        resource_manager.record_metric(
            f"dependency:{dependency_interface.interface_id}:node:{dependent}:indegree",
            len(dependency_interface._reverse_graph[dependent])
        )
    
    # Register development path metrics
    for path_id, path in dependency_interface._development_paths.items():
        resource_manager.record_metric(
            f"dependency:{dependency_interface.interface_id}:path:{path_id}:holding_points",
            len(path.holding_points)
        )
        resource_manager.record_metric(
            f"dependency:{dependency_interface.interface_id}:path:{path_id}:state",
            path.branch_state.value
        )

def monitor_dependency_changes(dependency_interface: DependencyInterface) -> None:
    """Monitor dependency changes."""
    def dependency_change_callback(event_type: str, data: Dict[str, Any]) -> None:
        if event_type in ["dependency_added", "dependency_removed", "dependency_type_changed"]:
            logger.info(f"Dependency change event: {data}")
            register_dependency_metrics(dependency_interface)
    
    from resources.events import EventQueue
    event_queue = EventQueue()
    resource_manager = StateManager(event_queue)
    resource_manager.subscribe_to_events("dependency_added", dependency_change_callback)
    resource_manager.subscribe_to_events("dependency_removed", dependency_change_callback)
    resource_manager.subscribe_to_events("dependency_type_changed", dependency_change_callback)
    
class DependencyValidator:
    """
    Orchestrates the validation process for data flow and structural breakdown.
    
    Handles the sequential validation workflow where:
    1. Data flow is validated first
    2. Structural breakdown is validated next
    3. Cross-consistency is validated last
    
    Provides feedback to phase-specific agents for corrective action.
    """
    
    def __init__(self, resource_manager: StateManager):
        self.resource_manager = resource_manager
        self.dependency_interface = DependencyInterface("validator")
        self._validation_history = []
        self._data_flow = None
        self._structural_breakdown = None
        
    def record_validation_event(self, event_type: str, target: str, status: str, errors: List[Dict[str, Any]] = None) -> None:
        """Record a validation event for history and metrics tracking."""
        event = {
            "event_type": event_type,
            "target": target,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "errors": errors or []
        }
        
        self._validation_history.append(event)
        
        # Emit validation event (if supported)
        if hasattr(self.resource_manager, 'emit_event'):
            self.resource_manager.emit_event(
                f"dependency_validation_{event_type}",
                {
                    "target": target,
                    "status": status,
                    "timestamp": datetime.now().isoformat(),
                    "error_count": len(errors or [])
                }
            )
        
    async def validate_data_flow(self, data_flow: Dict[str, Any], phase: str = "one") -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate data flow and record the result.
        
        Args:
            data_flow: The data flow structure to validate
            phase: The phase of validation (one, two, three)
            
        Returns:
            Tuple of (is_valid, errors)
        """
        # Store data flow for cross-validation
        self._data_flow = data_flow
        
        # Validate data flow
        is_valid, errors = self.dependency_interface.validate_data_flow(data_flow)
        
        # Record validation event
        self.record_validation_event(
            "data_flow",
            f"phase_{phase}",
            "success" if is_valid else "failure",
            errors
        )
        
        return is_valid, errors
        
    async def validate_structural_breakdown(self, structure: Dict[str, Any], phase: str = "one") -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate structural breakdown and record the result.
        
        Args:
            structure: The structural breakdown to validate
            phase: The phase of validation (one, two, three)
            
        Returns:
            Tuple of (is_valid, errors)
        """
        # Store structural breakdown for cross-validation
        self._structural_breakdown = structure
        
        # Validate structural breakdown
        is_valid, errors = self.dependency_interface.validate_structural_breakdown(structure)
        
        # Record validation event
        self.record_validation_event(
            "structural_breakdown",
            f"phase_{phase}",
            "success" if is_valid else "failure",
            errors
        )
        
        return is_valid, errors
        
    async def validate_cross_consistency(self, phase: str = "one") -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate cross-consistency between data flow and structural breakdown.
        
        Args:
            phase: The phase of validation (one, two, three)
            
        Returns:
            Tuple of (is_valid, errors)
        """
        # Ensure both data flow and structural breakdown are available
        if self._data_flow is None or self._structural_breakdown is None:
            return False, [{
                "error_type": "missing_validation_data",
                "message": "Both data flow and structural breakdown must be validated first"
            }]
            
        # Validate cross-consistency
        is_valid, errors = self.dependency_interface.validate_cross_consistency(
            self._data_flow,
            self._structural_breakdown
        )
        
        # Record validation event
        self.record_validation_event(
            "cross_consistency",
            f"phase_{phase}",
            "success" if is_valid else "failure",
            errors
        )
        
        return is_valid, errors
        
    async def get_validation_summary(self) -> Dict[str, Any]:
        """Get a summary of validation results."""
        return {
            "data_flow_validated": self._data_flow is not None,
            "structural_breakdown_validated": self._structural_breakdown is not None,
            "cross_consistency_validated": any(event["event_type"] == "cross_consistency" for event in self._validation_history),
            "validation_history": self._validation_history,
            "latest_validation_time": self._validation_history[-1]["timestamp"] if self._validation_history else None,
            "overall_status": "success" if all(event["status"] == "success" for event in self._validation_history) else "failure"
        }
        
    async def determine_responsible_agent(self, errors: List[Dict[str, Any]]) -> Optional[str]:
        """
        Analyze validation errors to determine which agent is responsible for correction.
        
        Returns "data_flow_agent" or "structural_agent" based on error analysis.
        """
        # Count error types to make a decision
        data_flow_errors = 0
        structural_errors = 0
        
        for error in errors:
            error_type = error.get("error_type", "")
            
            # Data flow error types
            if error_type in [
                "invalid_data_flow_structure", "missing_data_flows", "self_reference",
                "duplicate_flow", "data_flow_cycle", "flow_invalid_source", 
                "flow_invalid_destination", "missing_data_flow"
            ]:
                data_flow_errors += 1
                
            # Structural error types
            elif error_type in [
                "invalid_structure_format", "missing_components", "duplicate_component_name",
                "duplicate_sequence_number", "undefined_dependency", "dependency_cycle",
                "missing_structural_dependency"
            ]:
                structural_errors += 1
        
        # Make a decision
        if data_flow_errors > structural_errors:
            return "data_flow_agent"
        elif structural_errors > data_flow_errors:
            return "structural_agent"
        elif data_flow_errors > 0:  # If tied but errors exist, fix data flow first
            return "data_flow_agent"
        else:
            return None  # No errors or cannot determine
            
    async def prepare_agent_feedback(self, agent_type: str, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Prepare feedback for the agent to correct errors.
        
        Args:
            agent_type: Either "data_flow_agent" or "structural_agent"
            errors: List of validation errors
            
        Returns:
            Dictionary with feedback information for the agent
        """
        # Filter errors relevant to this agent
        relevant_errors = []
        
        if agent_type == "data_flow_agent":
            error_types = [
                "invalid_data_flow_structure", "missing_data_flows", "self_reference",
                "duplicate_flow", "data_flow_cycle", "flow_invalid_source", 
                "flow_invalid_destination", "missing_data_flow"
            ]
        else:  # structural_agent
            error_types = [
                "invalid_structure_format", "missing_components", "duplicate_component_name",
                "duplicate_sequence_number", "undefined_dependency", "dependency_cycle",
                "missing_structural_dependency"
            ]
            
        for error in errors:
            if error.get("error_type", "") in error_types:
                relevant_errors.append(error)
                
        # Prepare feedback for the agent
        return {
            "agent_type": agent_type,
            "error_count": len(relevant_errors),
            "errors": relevant_errors,
            "timestamp": datetime.now().isoformat(),
            "correction_required": len(relevant_errors) > 0
        }