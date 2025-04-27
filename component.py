"""
Core Classes:
ComponentManager: Manages component lifecycle and relationships
SystemComponent: Stores system-level guidelines and requirements
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
Phase one alignment and integration
Foundational guidelines storage

Design Decisions:
Inherited from ComponentInterface for consistency
Implemented comprehensive feature tracking
Added extensive integration validation
Included pipeline monitoring
Added system components for foundational guidelines
"""

from typing import Dict, List, Any, Optional, Set, Tuple, Union, Type
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
from datetime import datetime
import json

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

class ComponentType(Enum):
    FOUNDATION = "foundation"
    CORE = "core"
    FEATURE = "feature"
    UTILITY = "utility"
    SYSTEM = "system"  # Special type for system-level components

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

@dataclass
class ComponentGuideline:
    """Stores component-level guidelines from phase two outputs"""
    purpose: str
    requirements: Dict[str, Any] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)
    integration_points: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "purpose": self.purpose,
            "requirements": self.requirements,
            "constraints": self.constraints,
            "integration_points": self.integration_points,
            "success_criteria": self.success_criteria
        }

@dataclass
class ComponentDataFlow:
    """Manages data flow within a component and between features"""
    inputs: Dict[str, str] = field(default_factory=dict)  # name -> data type
    outputs: Dict[str, str] = field(default_factory=dict)  # name -> data type
    internal_flows: List[Dict[str, str]] = field(default_factory=list)  # flows between features
    data_transformations: Dict[str, str] = field(default_factory=dict)  # transformation name -> description
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "inputs": self.inputs,
            "outputs": self.outputs,
            "internal_flows": self.internal_flows,
            "data_transformations": self.data_transformations
        }

@dataclass
class ComponentMetadata:
    """Metadata extracted from the Tree Placement Planner Agent output."""
    component_type: ComponentType
    purpose: str
    sequence_number: int = 0
    data_types_handled: List[str] = field(default_factory=list)
    completion_criteria: List[str] = field(default_factory=list)
    public_interface: Dict[str, List[str]] = field(default_factory=lambda: {
        "inputs": [], "outputs": [], "events": []
    })
    features: Set[str] = field(default_factory=set)
    guidelines: Optional[ComponentGuideline] = None
    data_flow: Optional[ComponentDataFlow] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        result = {
            "type": self.component_type.value,
            "purpose": self.purpose,
            "sequence_number": self.sequence_number,
            "data_types_handled": self.data_types_handled,
            "completion_criteria": self.completion_criteria,
            "public_interface": self.public_interface,
            "features": list(self.features)
        }
        
        if self.guidelines:
            result["guidelines"] = self.guidelines.to_dict()
            
        if self.data_flow:
            result["data_flow"] = self.data_flow.to_dict()
            
        return result

class Component(ComponentInterface):
    def __init__(self, component_id: str, is_primary: bool = False, 
                metadata: Optional[ComponentMetadata] = None):
        super().__init__(component_id)
        self.is_primary = is_primary
        self._component_state = ComponentState.INITIALIZED
        self._dependency_manager = DependencyInterface(component_id)
        self._features: Dict[str, 'Feature'] = {}  # Will store Feature instances
        self._integrated_components: Set[str] = set()
        self._test_executions: Dict[str, TestExecution] = {}
        self._build_processes: Dict[str, BuildProcess] = {}
        self._health_metrics: Dict[str, float] = {}
        self._metadata = metadata or ComponentMetadata(
            component_type=ComponentType.FEATURE,
            purpose="Generic component implementation"
        )
        
        self._state_mapping = {
            ComponentState.ERROR: ResourceState.ERROR,
            ComponentState.INTEGRATING: ResourceState.PROPAGATING,
            ComponentState.TESTING: ResourceState.VALIDATING,
            ComponentState.DEVELOPMENT: ResourceState.ACTIVE,
            ComponentState.PLANNING: ResourceState.ACTIVE,
            ComponentState.COMPLETED: ResourceState.ACTIVE,
            ComponentState.INITIALIZED: ResourceState.INITIALIZED
        }
        
        # Store component information in resource manager
        self._resource_manager.set_state(
            f"component:{self.interface_id}:is_primary",
            is_primary
        )
        self._resource_manager.set_state(
            f"component:{self.interface_id}:metadata",
            self._metadata.to_dict()
        )
        self.update_component_state(ComponentState.INITIALIZED)

    @property
    def component_state(self) -> ComponentState:
        return self._component_state

    @component_state.setter
    def component_state(self, new_state: ComponentState) -> None:
        self.update_component_state(new_state)
    
    @property
    def metadata(self) -> ComponentMetadata:
        """Get component metadata."""
        return self._metadata
    
    def set_metadata(self, metadata: ComponentMetadata) -> None:
        """Update component metadata."""
        self._metadata = metadata
        self._resource_manager.set_state(
            f"component:{self.interface_id}:metadata",
            {
                "type": self._metadata.component_type.value,
                "purpose": self._metadata.purpose,
                "sequence_number": self._metadata.sequence_number,
                "data_types_handled": self._metadata.data_types_handled,
                "completion_criteria": self._metadata.completion_criteria,
                "public_interface": self._metadata.public_interface
            }
        )
    
    def add_required_dependency(self, dependency_id: str) -> None:
        """Add a required dependency to this component."""
        self._dependency_manager.add_dependency(self.interface_id, dependency_id)
        self._resource_manager.set_state(
            f"component:{self.interface_id}:dependencies:required", 
            self._dependency_manager.get_dependencies(self.interface_id)
        )
        logger.info(f"Added required dependency {dependency_id} to component {self.interface_id}")

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
        
        feature_keys = list(self._features.keys())
        
        snapshot = {
            "component_state": self._component_state,
            "feature_keys": feature_keys,
            "integrated_components": self._integrated_components.copy(),
            "test_executions": {k: v.__dict__ for k, v in self._test_executions.items()},
            "build_processes": {k: v.__dict__ for k, v in self._build_processes.items()},
            "health_metrics": self._health_metrics.copy(),
            "metadata": self._metadata.to_dict()
        }
        
        # Also separately snapshot each feature
        for feature_id, feature in self._features.items():
            feature_snapshot_id = f"component:{self.interface_id}:feature:{feature_id}:snapshot_{datetime.now().isoformat()}"
            feature_snapshot = {
                "feature_id": feature_id,
                "state": feature.state.name if hasattr(feature, 'state') else "UNKNOWN",
                "metadata": feature._metadata.to_dict() if hasattr(feature, '_metadata') else {},
                "functionalities": list(feature.get_all_functionalities().keys()) if hasattr(feature, 'get_all_functionalities') else []
            }
            self._resource_manager.set_state(feature_snapshot_id, feature_snapshot)
            # Add reference to the feature snapshot in the component snapshot
            snapshot[f"feature_snapshot:{feature_id}"] = feature_snapshot_id
        
        self._resource_manager.set_state(snapshot_id, snapshot)
        return snapshot_id

    def restore_component_snapshot(self, snapshot_id: str) -> None:
        snapshot = self._resource_manager.get_state(snapshot_id)
        if not snapshot:
            raise ValueError(f"Component snapshot not found: {snapshot_id}")
            
        self._component_state = snapshot["component_state"]
        self._integrated_components = set(snapshot["integrated_components"])
        self._test_executions = {
            k: TestExecution(**v) for k, v in snapshot["test_executions"].items()
        }
        self._build_processes = {
            k: BuildProcess(**v) for k, v in snapshot["build_processes"].items()
        }
        self._health_metrics = snapshot["health_metrics"]
        
        # Clear current features
        self._features.clear()
        
        # Restore metadata if available
        if "metadata" in snapshot:
            metadata_dict = snapshot["metadata"]
            
            # Reconstruct the Component Metadata including guidelines and data flow
            guidelines = None
            if "guidelines" in metadata_dict:
                guidelines = ComponentGuideline(**metadata_dict["guidelines"])
                
            data_flow = None
            if "data_flow" in metadata_dict:
                data_flow = ComponentDataFlow(**metadata_dict["data_flow"])
                
            self._metadata = ComponentMetadata(
                component_type=ComponentType(metadata_dict["type"]),
                purpose=metadata_dict["purpose"],
                sequence_number=metadata_dict["sequence_number"],
                data_types_handled=metadata_dict["data_types_handled"],
                completion_criteria=metadata_dict["completion_criteria"],
                public_interface=metadata_dict["public_interface"],
                features=set(metadata_dict.get("features", [])),
                guidelines=guidelines,
                data_flow=data_flow
            )
        
        # For each feature, check if there's a feature snapshot and restore it
        from feature import Feature
        for feature_id in snapshot.get("feature_keys", []):
            feature_snapshot_id = snapshot.get(f"feature_snapshot:{feature_id}")
            if feature_snapshot_id:
                feature_snapshot = self._resource_manager.get_state(feature_snapshot_id)
                if feature_snapshot:
                    # Create a new feature instance
                    metadata_dict = feature_snapshot.get("metadata", {})
                    description = metadata_dict.get("description", "Restored feature")
                    
                    # Create the feature
                    feature = Feature(feature_id, description)
                    
                    # Restore feature metadata if available
                    if metadata_dict:
                        # Restore guidelines if available
                        if "guidelines" in metadata_dict:
                            feature.set_guidelines(metadata_dict["guidelines"])
                            
                        # Restore data flow if available
                        if "data_flow" in metadata_dict:
                            feature.set_data_flow(metadata_dict["data_flow"])
                            
                        # Restore dependencies
                        for dep_id in metadata_dict.get("dependencies", []):
                            feature.add_dependency(dep_id)
                    
                    # Add restored feature
                    self._features[feature_id] = feature
                    
                    # Import functionalities later if needed
        
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
    
    def add_feature(self, feature_id: str, description: str) -> 'Feature':
        """Add a feature to this component."""
        # Import Feature class from feature module to avoid circular import
        from feature import Feature
        from dependency import DependencyType
        
        # Create new feature with this component as parent
        feature = Feature(feature_id, description, component_id=self.interface_id)
        
        # Store in features dictionary
        self._features[feature_id] = feature
        
        # Add to metadata set
        self._metadata.features.add(feature_id)
        
        # Create hierarchical dependency relationship
        full_feature_id = f"feature:{feature_id}"
        full_component_id = f"component:{self.interface_id}"
        self._dependency_manager.add_hierarchical_dependency(
            full_component_id, 
            full_feature_id, 
            DependencyType.COMPONENT_TO_FEATURE
        )
        
        # Update state in resource manager
        self._resource_manager.set_state(
            f"component:{self.interface_id}:metadata",
            self._metadata.to_dict()
        )
        
        # Emit feature added event
        self._resource_manager.emit_event(
            "component_feature_added",
            {
                "component_id": self.interface_id,
                "feature_id": feature_id,
                "description": description
            }
        )
        
        return feature
    
    def get_feature(self, feature_id: str) -> 'Feature':
        """Get a feature by ID."""
        if feature_id not in self._features:
            raise ValueError(f"Feature not found: {feature_id}")
        return self._features[feature_id]
    
    def get_all_features(self) -> Dict[str, 'Feature']:
        """Get all features for this component."""
        return self._features.copy()
    
    def add_feature_dependency(self, from_id: str, to_id: str) -> None:
        """Add a dependency between two features."""
        # Verify features exist
        if from_id not in self._features:
            raise ValueError(f"Feature not found: {from_id}")
        if to_id not in self._features:
            raise ValueError(f"Feature not found: {to_id}")
        
        # Add dependency in feature object
        self._features[from_id].add_dependency(to_id)
        
        # Emit dependency added event
        self._resource_manager.emit_event(
            "component_feature_dependency_added",
            {
                "component_id": self.interface_id,
                "source_feature": from_id,
                "target_feature": to_id
            }
        )
    
    def get_feature_development_order(self) -> List[Set[str]]:
        """Get ordered development layers for features based on dependencies."""
        feature_dependency_manager = DependencyInterface(f"{self.interface_id}_features")
        
        # Build dependency graph
        for feature_id in self._features:
            feature_dependency_manager.add_node(feature_id)
            
        for feature_id, feature in self._features.items():
            for dependency_id in feature._metadata.dependencies:
                if dependency_id in self._features:
                    feature_dependency_manager.add_dependency(feature_id, dependency_id)
        
        # Get development order
        return feature_dependency_manager.get_development_order()
    
    def set_guidelines(self, guidelines: Union[Dict[str, Any], ComponentGuideline]) -> None:
        """Set component-level guidelines."""
        if isinstance(guidelines, dict):
            self._metadata.guidelines = ComponentGuideline(
                purpose=guidelines.get("purpose", ""),
                requirements=guidelines.get("requirements", {}),
                constraints=guidelines.get("constraints", []),
                integration_points=guidelines.get("integration_points", []),
                success_criteria=guidelines.get("success_criteria", [])
            )
        else:
            self._metadata.guidelines = guidelines
        
        # Update state in resource manager
        self._resource_manager.set_state(
            f"component:{self.interface_id}:metadata",
            self._metadata.to_dict()
        )
        
        # Emit guidelines set event
        self._resource_manager.emit_event(
            "component_guidelines_set",
            {
                "component_id": self.interface_id,
                "guidelines": self._metadata.guidelines.to_dict()
            }
        )
    
    def set_data_flow(self, data_flow: Union[Dict[str, Any], ComponentDataFlow]) -> None:
        """Set component-level data flow."""
        if isinstance(data_flow, dict):
            self._metadata.data_flow = ComponentDataFlow(
                inputs=data_flow.get("inputs", {}),
                outputs=data_flow.get("outputs", {}),
                internal_flows=data_flow.get("internal_flows", []),
                data_transformations=data_flow.get("data_transformations", {})
            )
        else:
            self._metadata.data_flow = data_flow
        
        # Update state in resource manager
        self._resource_manager.set_state(
            f"component:{self.interface_id}:metadata",
            self._metadata.to_dict()
        )
        
        # Emit data flow set event
        self._resource_manager.emit_event(
            "component_data_flow_set",
            {
                "component_id": self.interface_id,
                "data_flow": self._metadata.data_flow.to_dict()
            }
        )
    
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

class SystemComponent(Component):
    """Special component for storing system-level guidelines and requirements 
    from phase one outputs."""
    
    def __init__(self, component_id: str = "system_foundation"):
        metadata = ComponentMetadata(
            component_type=ComponentType.SYSTEM,
            purpose="Store system-level guidelines and requirements",
            sequence_number=0,
            data_types_handled=["project_guidelines", "core_requirements", 
                               "data_architecture", "component_architecture"],
            completion_criteria=["All foundational guidelines stored and validated"]
        )
        super().__init__(component_id, is_primary=True, metadata=metadata)
        
        self._project_guidelines = {}
        self._core_requirements = {}
        self._data_architecture = {}
        self._component_architecture = {}
        
        self._resource_manager.set_state(
            f"component:{self.interface_id}:type",
            "system"
        )
    
    def store_project_guidelines(self, guidelines: Dict[str, Any]) -> None:
        """Store project guidelines from Garden Planner Agent."""
        self._project_guidelines = guidelines
        self._resource_manager.set_state(
            f"component:{self.interface_id}:project_guidelines",
            guidelines
        )
        logger.info(f"Stored project guidelines in system component")
    
    def store_core_requirements(self, requirements: Dict[str, Any]) -> None:
        """Store core requirements from Environment Analysis Agent."""
        self._core_requirements = requirements
        self._resource_manager.set_state(
            f"component:{self.interface_id}:core_requirements",
            requirements
        )
        logger.info(f"Stored core requirements in system component")
    
    def store_data_architecture(self, architecture: Dict[str, Any]) -> None:
        """Store data architecture from Root System Architect Agent."""
        self._data_architecture = architecture
        self._resource_manager.set_state(
            f"component:{self.interface_id}:data_architecture",
            architecture
        )
        logger.info(f"Stored data architecture in system component")
    
    def store_component_architecture(self, architecture: Dict[str, Any]) -> None:
        """Store component architecture from Tree Placement Planner Agent."""
        self._component_architecture = architecture
        self._resource_manager.set_state(
            f"component:{self.interface_id}:component_architecture",
            architecture
        )
        logger.info(f"Stored component architecture in system component")
    
    def get_project_guidelines(self) -> Dict[str, Any]:
        """Get stored project guidelines."""
        return self._project_guidelines
    
    def get_core_requirements(self) -> Dict[str, Any]:
        """Get stored core requirements."""
        return self._core_requirements
    
    def get_data_architecture(self) -> Dict[str, Any]:
        """Get stored data architecture."""
        return self._data_architecture
    
    def get_component_architecture(self) -> Dict[str, Any]:
        """Get stored component architecture."""
        return self._component_architecture

def create_component_from_structural_definition(component_def: Dict[str, Any]) -> Component:
    """Create a Component instance from Tree Placement Planner output."""
    component_type = ComponentType(component_def["type"])
    
    metadata = ComponentMetadata(
        component_type=component_type,
        purpose=component_def["purpose"],
        sequence_number=component_def["sequence_number"],
        data_types_handled=component_def["data_types_handled"],
        completion_criteria=component_def["completion_criteria"],
        public_interface=component_def["public_interface"]
    )
    
    component = Component(
        component_id=component_def["name"],
        is_primary=component_type in [ComponentType.FOUNDATION, ComponentType.CORE],
        metadata=metadata
    )
    
    # Add dependencies
    for dep in component_def["dependencies"]["required"]:
        component.add_required_dependency(dep)
    
    return component

def build_system_components_from_phase_one(
    project_guidelines: Dict[str, Any],
    core_requirements: Dict[str, Any],
    data_architecture: Dict[str, Any],
    component_architecture: Dict[str, Any]
) -> Dict[str, Component]:
    """Create system components based on phase one outputs."""
    # Create foundation system component
    system_component = SystemComponent()
    system_component.store_project_guidelines(project_guidelines)
    system_component.store_core_requirements(core_requirements)
    system_component.store_data_architecture(data_architecture)
    system_component.store_component_architecture(component_architecture)
    
    components = {"system_foundation": system_component}
    
    # Create ordered components from component architecture
    ordered_components = component_architecture.get("component_architecture", {}).get("ordered_components", [])
    
    for comp_def in ordered_components:
        component = create_component_from_structural_definition(comp_def)
        components[comp_def["name"]] = component
    
    # Validate dependency structure
    for comp_name, component in components.items():
        if not component.validate():
            logger.warning(f"Component {comp_name} failed validation")
    
    return components

def validate_data_flow_against_components(
    data_architecture: Dict[str, Any],
    components: Dict[str, Component]
) -> bool:
    """Validate that the data flow architecture aligns with component structure."""
    data_flows = data_architecture.get("data_architecture", {}).get("data_flows", [])
    component_names = set(components.keys())
    
    # Check that all data flow sources and destinations are valid components
    for flow in data_flows:
        source = flow.get("source", "")
        destination = flow.get("destination", "")
        
        if source not in component_names and source != "external":
            logger.error(f"Data flow source '{source}' is not a valid component")
            return False
        
        if destination not in component_names and destination != "external":
            logger.error(f"Data flow destination '{destination}' is not a valid component")
            return False
    
    return True

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
    
    # Register feature-level metrics for each feature in the component
    for feature_id, feature in component._features.items():
        from feature import register_feature_metrics
        if hasattr(feature, 'register_metrics'):
            feature.register_metrics()
        elif 'register_feature_metrics' in globals():
            register_feature_metrics(feature)
        
    # Register metrics for component guidelines and data flow
    has_guidelines = component._metadata.guidelines is not None
    has_data_flow = component._metadata.data_flow is not None
    
    resource_manager.record_metric(
        f"component:{component.interface_id}:has_guidelines",
        1.0 if has_guidelines else 0.0
    )
    
    resource_manager.record_metric(
        f"component:{component.interface_id}:has_data_flow",
        1.0 if has_data_flow else 0.0
    )

def monitor_component_changes(component: Component) -> None:
    """Monitor component changes."""
    def component_change_callback(event_type: str, data: Dict[str, Any]) -> None:
        if event_type in [
            "component_feature_added",
            "component_integration_added",
            "component_feature_dependency_added",
            "component_guidelines_set",
            "component_data_flow_set"
        ]:
            logger.info(f"Component change event: {data}")
            register_component_metrics(component)
    
    resource_manager = StateManager("main_interface")
    resource_manager.subscribe_to_events("component_feature_added", 
                                       component_change_callback)
    resource_manager.subscribe_to_events("component_integration_added", 
                                       component_change_callback)
    resource_manager.subscribe_to_events("component_feature_dependency_added", 
                                       component_change_callback)
    resource_manager.subscribe_to_events("component_guidelines_set", 
                                       component_change_callback)
    resource_manager.subscribe_to_events("component_data_flow_set", 
                                       component_change_callback)