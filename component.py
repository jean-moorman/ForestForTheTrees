"""
Core Classes:
ComponentManager: Manages component lifecycle and relationships
TestExecutionTracker: Tracks TDD cycle progress
BuildMonitor: Monitors build process status
ComponentHealth: Tracks component health metrics

Key Features:
Feature set management
Component integration validation
Development pipeline tracking
Test execution monitoring
Build process tracking
Health monitoring
State persistence

Design Decisions:
Inherited from ComponentInterface for consistency
Implemented comprehensive feature tracking
Added extensive integration validation
Included pipeline monitoring
"""

from typing import Dict, List, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
from datetime import datetime

from interface import ComponentInterface, FeatureInterface
from resources import StateManager, ResourceState
from dependency import DependencyInterface, BranchState
from integration import IntegrationInterface, IntegrationState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComponentState(Enum):
    INITIALIZED = auto()
    PLANNING = auto()
    DEVELOPMENT = auto()
    TESTING = auto()
    INTEGRATING = auto()
    COMPLETED = auto()
    ERROR = auto()

class TestState(Enum):
    NOT_STARTED = auto()
    IN_PROGRESS = auto()
    FAILED = auto()
    PASSED = auto()

class BuildState(Enum):
    PENDING = auto()
    BUILDING = auto()
    FAILED = auto()
    SUCCEEDED = auto()

@dataclass
class TestExecution:
    test_id: str
    test_type: str
    state: TestState = TestState.NOT_STARTED
    results: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class BuildProcess:
    build_id: str
    state: BuildState = BuildState.PENDING
    artifacts: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class Component(ComponentInterface):
    def __init__(self, component_id: str, is_primary: bool = False):
        super().__init__(component_id)
        self.is_primary = is_primary
        self._component_state = ComponentState.INITIALIZED
        self._dependency_manager = DependencyInterface()
        self._features: Set[str] = set()
        self._integrated_components: Set[str] = set()
        self._test_executions: Dict[str, TestExecution] = {}
        self._build_processes: Dict[str, BuildProcess] = {}
        self._health_metrics: Dict[str, float] = {}
        
        self._state_mapping = {
            ComponentState.ERROR: ResourceState.ERROR,
            ComponentState.INTEGRATING: ResourceState.PROPAGATING,
            ComponentState.TESTING: ResourceState.VALIDATING,
            ComponentState.DEVELOPMENT: ResourceState.ACTIVE,
            ComponentState.PLANNING: ResourceState.ACTIVE,
            ComponentState.COMPLETED: ResourceState.ACTIVE,
            ComponentState.INITIALIZED: ResourceState.INITIALIZED
        }
        
        self._resource_manager.set_state(
            f"component:{self.interface_id}:is_primary",
            is_primary
        )
        self.update_component_state(ComponentState.INITIALIZED)

    @property
    def component_state(self) -> ComponentState:
        return self._component_state

    @component_state.setter
    def component_state(self, new_state: ComponentState) -> None:
        self.update_component_state(new_state)

    def add_integrated_component(self, component_id: str) -> None:
        """Add a component integration with dependency management."""
        if not self._validate_component_integration(component_id):
            raise ValueError(f"Invalid component integration: {component_id}")
            
        self._integrated_components.add(component_id)
        self._dependency_manager.add_dependency(self.interface_id, component_id)
        
        # Create development path
        path_id = f"integration_path_{self.interface_id}_{component_id}"
        self._dependency_manager.create_development_path(
            path_id,
            [self.interface_id, component_id],
            priority=1 if self.is_primary else 0
        )
        
        # Update resource manager state
        self._resource_manager.set_state(
            f"component:{self.interface_id}:integrated_components",
            list(self._integrated_components)
        )
        
        # Create integration point
        integration_interface = IntegrationInterface(self.interface_id)
        integration_interface.create_integration_point(
            f"{self.interface_id}_{component_id}",
            "COMPONENT",
            {self.interface_id, component_id}
        )

    def update_component_state(self, new_state: ComponentState, 
                             metadata: Optional[Dict[str, Any]] = None) -> None:
        if metadata is None:
            metadata = {}
            
        old_state = self._component_state
        self._component_state = new_state
        
        # Update dependency manager
        self._dependency_manager.handle_state_change(
            self._state_mapping[new_state],
            {**metadata, "component_state": new_state.name}
        )

        metadata.update({
            "old_component_state": old_state.name,
            "new_component_state": new_state.name,
            "test_status": {tid: te.state.name for tid, te in self._test_executions.items()},
            "build_status": {bid: bp.state.name for bid, bp in self._build_processes.items()}
        })
        
        interface_state = self._state_mapping[new_state]
        self.propagate_state_change(interface_state, metadata)

    def create_component_snapshot(self) -> str:
        snapshot_id = f"component:{self.interface_id}:snapshot_{datetime.now().isoformat()}"
        
        snapshot = {
            "component_state": self._component_state,
            "features": self._features.copy(),
            "integrated_components": self._integrated_components.copy(),
            "test_executions": {k: v.__dict__ for k, v in self._test_executions.items()},
            "build_processes": {k: v.__dict__ for k, v in self._build_processes.items()},
            "health_metrics": self._health_metrics.copy()
        }
        
        self._resource_manager.set_state(snapshot_id, snapshot)
        return snapshot_id

    def restore_component_snapshot(self, snapshot_id: str) -> None:
        snapshot = self._resource_manager.get_state(snapshot_id)
        if not snapshot:
            raise ValueError(f"Component snapshot not found: {snapshot_id}")
            
        self._component_state = snapshot["component_state"]
        self._features = set(snapshot["features"])
        self._integrated_components = set(snapshot["integrated_components"])
        self._test_executions = {
            k: TestExecution(**v) for k, v in snapshot["test_executions"].items()
        }
        self._build_processes = {
            k: BuildProcess(**v) for k, v in snapshot["build_processes"].items()
        }
        self._health_metrics = snapshot["health_metrics"]
        
        self.update_component_state(self._component_state)

    def rollback_component(self, steps: int = 1) -> None:
        snapshot_id = self.create_component_snapshot()
        try:
            super().rollback(steps)
            component_state = self._resource_manager.get_state(
                f"component:{self.interface_id}:state"
            )
            self.restore_component_snapshot(snapshot_id)
            self.update_component_state(component_state)
        except Exception as e:
            self.restore_component_snapshot(snapshot_id)
            raise
    
    def set_development_holding_point(self) -> None:
        """Set a holding point for all development paths containing this component."""
        paths = [path_id for path_id, path in self._dependency_manager._development_paths.items()
                if self.interface_id in path.components]
                
        for path_id in paths:
            self._dependency_manager.add_holding_point(path_id, self.interface_id)
            self.update_component_state(ComponentState.TESTING)

    def resume_development(self) -> None:
        """Resume development from holding point."""
        paths = [path_id for path_id, path in self._dependency_manager._development_paths.items()
                if self.interface_id in path.holding_points]
                
        for path_id in paths:
            self._dependency_manager.resume_development(path_id, self.interface_id)
            self.update_component_state(ComponentState.DEVELOPMENT)

    def validate(self) -> bool:
        """Extended validation including dependency validation."""
        if not super().validate():
            return False
            
        return self._dependency_manager.validate()

def register_component_metrics(component: Component) -> None:
    """Register monitoring metrics for component."""
    resource_manager = StateManager("main_interface")
    
    # Register feature metrics
    resource_manager.record_metric(
        f"component:{component.interface_id}:feature_count",
        len(component._features)
    )
    
    # Register integration metrics
    resource_manager.record_metric(
        f"component:{component.interface_id}:integration_count",
        len(component._integrated_components)
    )
    
    # Register test metrics
    test_states = {state: 0 for state in TestState}
    for execution in component._test_executions.values():
        test_states[execution.state] += 1
    for state, count in test_states.items():
        resource_manager.record_metric(
            f"component:{component.interface_id}:tests:{state.name.lower()}",
            count
        )
    
    # Register build metrics
    build_states = {state: 0 for state in BuildState}
    for build in component._build_processes.values():
        build_states[build.state] += 1
    for state, count in build_states.items():
        resource_manager.record_metric(
            f"component:{component.interface_id}:builds:{state.name.lower()}",
            count
        )

def monitor_component_changes(component: Component) -> None:
    """Monitor component changes."""
    def component_change_callback(event_type: str, data: Dict[str, Any]) -> None:
        if event_type in [
            "component_feature_added",
            "component_integration_added"
        ]:
            logger.info(f"Component change event: {data}")
            register_component_metrics(component)
    
    resource_manager = StateManager("main_interface")
    resource_manager.subscribe_to_events("component_feature_added", 
                                       component_change_callback)
    resource_manager.subscribe_to_events("component_integration_added", 
                                       component_change_callback)