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

from interface import BaseInterface
from resources import ResourceState, ResourceState, StateManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DependencyType(Enum):
    PRIMARY = auto()
    SECONDARY = auto()
    AUXILIARY = auto()

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
    
    def __init__(self, component_id: str):
        super().__init__(f"dependency:{component_id}")
        self._dependency_type = DependencyType.SECONDARY
        self._development_paths: Dict[str, DevelopmentPath] = {}
        self._dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self._reverse_graph: Dict[str, Set[str]] = defaultdict(set)
        self._holding_points: Dict[str, Set[str]] = defaultdict(set)
        
        # Register with resource manager
        self._resource_manager.set_state(
            f"dependency:{self.interface_id}:type",
            self._dependency_type
        )

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

    def add_dependency(self, dependent: str, dependency: str) -> None:
        """Add a dependency relationship to the DAG."""
        # Check for cycles before adding
        if self._would_create_cycle(dependent, dependency):
            raise ValueError(f"Adding dependency {dependency} would create a cycle")
            
        self._dependency_graph[dependent].add(dependency)
        self._reverse_graph[dependency].add(dependent)
        
        # Update state in resource manager
        self._resource_manager.set_state(
            f"dependency:{self.interface_id}:graph:{dependent}",
            list(self._dependency_graph[dependent])
        )
        
        # Emit dependency added event
        self._resource_manager.emit_event(
            "dependency_added",
            {
                "interface_id": self.interface_id,
                "dependent": dependent,
                "dependency": dependency
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
            
        # Validate dependency graph
        for dependent, dependencies in self._dependency_graph.items():
            for dependency in dependencies:
                # Check for cycles
                if self._would_create_cycle(dependent, dependency):
                    logger.error(f"Cycle detected in dependency graph: {dependent} -> {dependency}")
                    return False
                    
                # Validate dependency states
                dep_state = self._resource_manager.get_state(f"interface:{dependency}:state")
                if dep_state not in (ResourceState.ACTIVE, ResourceState.PROPAGATING):
                    logger.error(f"Invalid dependency state: {dependency} -> {dep_state}")
                    return False
                    
        # Validate development paths
        for path_id, path in self._development_paths.items():
            # Check component existence
            for component in path.components:
                if not self._resource_manager.verify_resource_health(f"interface:{component}"):
                    logger.error(f"Unhealthy component in path {path_id}: {component}")
                    return False
                    
            # Validate holding points
            for holding_point in path.holding_points:
                if holding_point not in path.components:
                    logger.error(f"Invalid holding point in path {path_id}: {holding_point}")
                    return False
                    
        return True

def register_dependency_metrics(dependency_interface: DependencyInterface) -> None:
    """Register monitoring metrics for dependency interface."""
    resource_manager = StateManager("main_interface")
    
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
    
    resource_manager = StateManager("main_interface")
    resource_manager.subscribe_to_events("dependency_added", dependency_change_callback)
    resource_manager.subscribe_to_events("dependency_removed", dependency_change_callback)
    resource_manager.subscribe_to_events("dependency_type_changed", dependency_change_callback)