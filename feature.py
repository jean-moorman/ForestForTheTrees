"""
Core Classes:
Feature: Inherits from FeatureInterface for feature management
FeatureTest: Manages feature-level test execution
FeatureBuild: Handles feature build process
FeatureToggle: Manages feature toggle state
Functionality: Manages feature functionality implementation
FeatureGuideline: Stores feature-level guidelines and requirements
FeatureDataFlow: Manages data flow within and between features
FeatureStructure: Handles functionality structure breakdown

Key Features:
Feature toggle management
Test execution tracking
Build process monitoring
Health metrics tracking
Event propagation
Guidelines storage
Phase three integration
Functionality management
Feature evolution

Design Decisions:
Inherited from FeatureInterface for consistency
Implemented comprehensive toggle management
Added extensive test tracking
Included build monitoring
Added hierarchical feature functionality breakdown
Integrated phase three guideline management
"""

from typing import Dict, List, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
from datetime import datetime

from interface import FeatureInterface, FunctionalityInterface
from resources import ResourceState, StateManager
from component import TestState, BuildState, TestExecution, BuildProcess
from dependency import DependencyInterface, DevelopmentPath

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeatureState(Enum):
    INITIALIZED = auto()
    PLANNING = auto()
    IMPLEMENTING = auto()
    TESTING = auto()
    INTEGRATING = auto()
    ACTIVE = auto()
    DISABLED = auto()
    ERROR = auto()
    COMPLETED = auto()

class ToggleState(Enum):
    ON = auto()
    OFF = auto()
    TRANSITIONING = auto()

class FunctionalityState(Enum):
    INITIALIZED = auto()
    IMPLEMENTING = auto()
    TESTING = auto()
    REVIEWING = auto()
    ACTIVE = auto()
    DEPRECATED = auto()
    ERROR = auto()
    COMPLETED = auto()

class EvolutionState(Enum):
    """Tracks the evolutionary state of a feature within phase 3's natural selection"""
    STABLE = auto()    # Feature is performing well and stable
    ADAPTING = auto()  # Feature is currently being improved
    CANDIDATE = auto() # Feature is a candidate for replacement
    REPLACING = auto() # Feature is scheduled for replacement
    DEPRECATED = auto() # Feature has been replaced but is kept for reference

@dataclass
class FeatureToggle:
    enabled: bool = True
    state: ToggleState = ToggleState.ON
    last_changed: datetime = field(default_factory=datetime.now)
    transition_history: List[Tuple[ToggleState, datetime]] = field(default_factory=list)

@dataclass
class FeatureGuideline:
    """Stores feature-level guidelines from phase three outputs"""
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
class FeatureDataFlow:
    """Manages data flow within a feature and between functionalities"""
    inputs: Dict[str, str] = field(default_factory=dict)  # name -> data type
    outputs: Dict[str, str] = field(default_factory=dict)  # name -> data type
    internal_flows: List[Dict[str, str]] = field(default_factory=list)  # flows between functionalities
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
class FeatureMetadata:
    description: str
    functionalities: Set[str] = field(default_factory=set)
    requirements: Dict[str, Any] = field(default_factory=dict)
    dependencies: Set[str] = field(default_factory=set)
    guidelines: Optional[FeatureGuideline] = None
    data_flow: Optional[FeatureDataFlow] = None
    evolution_state: EvolutionState = EvolutionState.STABLE
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        result = {
            "description": self.description,
            "functionalities": list(self.functionalities),
            "requirements": self.requirements,
            "dependencies": list(self.dependencies),
            "evolution_state": self.evolution_state.name
        }
        
        if self.guidelines:
            result["guidelines"] = self.guidelines.to_dict()
            
        if self.data_flow:
            result["data_flow"] = self.data_flow.to_dict()
            
        return result

@dataclass
class FunctionalityMetadata:
    """Metadata for a functionality within a feature"""
    description: str
    inputs: Dict[str, str] = field(default_factory=dict)  # name -> data type
    outputs: Dict[str, str] = field(default_factory=dict)  # name -> data type
    requirements: Dict[str, Any] = field(default_factory=dict)
    dependencies: Set[str] = field(default_factory=set)  # Dependencies on other functionalities
    implementation_status: Dict[str, Any] = field(default_factory=dict)  # Implementation status details
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "description": self.description,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "requirements": self.requirements,
            "dependencies": list(self.dependencies),
            "implementation_status": self.implementation_status
        }

class Functionality(FunctionalityInterface):
    """Functionality class representing a discrete functional unit within a feature."""
    
    def __init__(self, functionality_id: str, description: str, feature_id: str):
        super().__init__(functionality_id)
        self.feature_id = feature_id
        self.state = FunctionalityState.INITIALIZED
        self._metadata = FunctionalityMetadata(description=description)
        self._test_executions: Dict[str, TestExecution] = {}
        self._build_processes: Dict[str, BuildProcess] = {}
        self._health_metrics: Dict[str, float] = {}
        self._implementation_code: str = ""
        
        # Initialize resource states
        self._resource_manager.set_state(
            f"functionality:{self.interface_id}:state",
            self.state
        )
        self._resource_manager.set_state(
            f"functionality:{self.interface_id}:metadata",
            self._metadata.to_dict()
        )
        self._resource_manager.set_state(
            f"functionality:{self.interface_id}:feature_id",
            feature_id
        )
    
    def set_implementation_code(self, code: str) -> None:
        """Set the implementation code for this functionality."""
        self._implementation_code = code
        self._metadata.implementation_status["has_implementation"] = True
        self._metadata.implementation_status["last_updated"] = datetime.now().isoformat()
        
        # Update state in resource manager
        self._resource_manager.set_state(
            f"functionality:{self.interface_id}:implementation_code",
            code
        )
        self._resource_manager.set_state(
            f"functionality:{self.interface_id}:metadata",
            self._metadata.to_dict()
        )
        
        # Emit implementation event
        self._resource_manager.emit_event(
            "functionality_implemented",
            {
                "functionality_id": self.interface_id,
                "feature_id": self.feature_id,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def get_implementation_code(self) -> str:
        """Get the implementation code for this functionality."""
        return self._implementation_code
    
    def update_state(self, state: FunctionalityState) -> None:
        """Update the functionality state."""
        old_state = self.state
        self.state = state
        
        # Update state in resource manager
        self._resource_manager.set_state(
            f"functionality:{self.interface_id}:state",
            state
        )
        
        # Emit state change event
        self._resource_manager.emit_event(
            "functionality_state_changed",
            {
                "functionality_id": self.interface_id,
                "feature_id": self.feature_id,
                "old_state": old_state,
                "new_state": state,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def add_requirement(self, key: str, value: Any) -> None:
        """Add a requirement for this functionality."""
        self._metadata.requirements[key] = value
        
        # Update state in resource manager
        self._resource_manager.set_state(
            f"functionality:{self.interface_id}:metadata",
            self._metadata.to_dict()
        )
        
    def add_dependency(self, functionality_id: str) -> None:
        """Add a dependency on another functionality."""
        self._metadata.dependencies.add(functionality_id)
        
        # Update state in resource manager
        self._resource_manager.set_state(
            f"functionality:{self.interface_id}:metadata",
            self._metadata.to_dict()
        )
        
        # Emit dependency added event
        self._resource_manager.emit_event(
            "functionality_dependency_added",
            {
                "functionality_id": self.interface_id,
                "dependency_id": functionality_id,
                "feature_id": self.feature_id,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def add_input(self, name: str, data_type: str) -> None:
        """Define an input for this functionality."""
        self._metadata.inputs[name] = data_type
        
        # Update state in resource manager
        self._resource_manager.set_state(
            f"functionality:{self.interface_id}:metadata",
            self._metadata.to_dict()
        )
    
    def add_output(self, name: str, data_type: str) -> None:
        """Define an output for this functionality."""
        self._metadata.outputs[name] = data_type
        
        # Update state in resource manager
        self._resource_manager.set_state(
            f"functionality:{self.interface_id}:metadata",
            self._metadata.to_dict()
        )
    
    def create_test_execution(self, test_id: str, test_type: str) -> TestExecution:
        """Create a new test execution."""
        execution = TestExecution(
            test_id=test_id,
            test_type=test_type,
            started_at=datetime.now()
        )
        self._test_executions[test_id] = execution
        
        # Update state in resource manager
        self._resource_manager.set_state(
            f"functionality:{self.interface_id}:test:{test_id}",
            {
                "type": test_type,
                "state": execution.state,
                "started_at": execution.started_at
            }
        )
        
        return execution
    
    def update_test_state(self, test_id: str, state: TestState,
                        results: Optional[Dict[str, Any]] = None) -> None:
        """Update test execution state and results."""
        if test_id not in self._test_executions:
            raise ValueError(f"Test execution not found: {test_id}")
            
        execution = self._test_executions[test_id]
        execution.state = state
        if results:
            execution.results.update(results)
            
        if state in (TestState.FAILED, TestState.PASSED):
            execution.completed_at = datetime.now()
            
        # Update state in resource manager
        self._resource_manager.set_state(
            f"functionality:{self.interface_id}:test:{test_id}",
            {
                "state": state,
                "results": results,
                "completed_at": execution.completed_at
            }
        )
    
    def create_build_process(self, build_id: str) -> BuildProcess:
        """Create a new build process."""
        build = BuildProcess(
            build_id=build_id,
            started_at=datetime.now()
        )
        self._build_processes[build_id] = build
        
        # Update state in resource manager
        self._resource_manager.set_state(
            f"functionality:{self.interface_id}:build:{build_id}",
            {
                "state": build.state,
                "started_at": build.started_at
            }
        )
        
        return build
    
    def update_build_state(self, build_id: str, state: BuildState,
                         artifacts: Optional[Dict[str, Any]] = None,
                         errors: Optional[List[str]] = None) -> None:
        """Update build process state and results."""
        if build_id not in self._build_processes:
            raise ValueError(f"Build process not found: {build_id}")
            
        build = self._build_processes[build_id]
        build.state = state
        if artifacts:
            build.artifacts.update(artifacts)
        if errors:
            build.errors.extend(errors)
            
        if state in (BuildState.FAILED, BuildState.SUCCEEDED):
            build.completed_at = datetime.now()
            
        # Update state in resource manager
        self._resource_manager.set_state(
            f"functionality:{self.interface_id}:build:{build_id}",
            {
                "state": state,
                "artifacts": artifacts,
                "errors": errors,
                "completed_at": build.completed_at
            }
        )
    
    def update_health_metric(self, metric_name: str, value: float) -> None:
        """Update a functionality health metric."""
        self._health_metrics[metric_name] = value
        
        # Update metric in resource manager
        self._resource_manager.record_metric(
            f"functionality:{self.interface_id}:health:{metric_name}",
            value
        )
    
    def get_health_status(self) -> Dict[str, float]:
        """Get current functionality health status."""
        return self._health_metrics.copy()
    
    def validate(self) -> bool:
        """Validate functionality state and relationships."""
        # First validate functionality interface
        if not super().validate():
            return False
            
        # Validate requirements
        if not self._metadata.requirements:
            logger.error(f"No requirements defined for functionality: {self.interface_id}")
            return False
            
        # Validate I/O
        if not self._metadata.inputs and not self._metadata.outputs:
            logger.error(f"No inputs or outputs defined for functionality: {self.interface_id}")
            return False
            
        # Validate implementation
        if not self._implementation_code and self.state in (FunctionalityState.TESTING, FunctionalityState.ACTIVE, FunctionalityState.COMPLETED):
            logger.error(f"No implementation code for functionality in state {self.state}: {self.interface_id}")
            return False
            
        # Validate test executions
        for test_id, execution in self._test_executions.items():
            if execution.state == TestState.FAILED:
                logger.error(f"Failed test execution: {test_id}")
                return False
                
        # Validate build processes
        for build_id, build in self._build_processes.items():
            if build.state == BuildState.FAILED:
                logger.error(f"Failed build process: {build_id}")
                return False
                
        return True

class Feature(FeatureInterface):
    """Feature class managing feature implementation and toggle state."""
    
    def __init__(self, feature_id: str, description: str, component_id: Optional[str] = None):
        super().__init__(feature_id)
        self.state = FeatureState.INITIALIZED
        self._metadata = FeatureMetadata(description=description)
        self._toggle = FeatureToggle()
        self._test_executions: Dict[str, TestExecution] = {}
        self._build_processes: Dict[str, BuildProcess] = {}
        self._health_metrics: Dict[str, float] = {}
        self._functionalities: Dict[str, Functionality] = {}
        self._dependency_manager = DependencyInterface(feature_id)
        self._component_id = component_id  # The parent component this feature belongs to
        
        # Initialize resource states
        self._resource_manager.set_state(
            f"feature:{self.interface_id}:state",
            self.state
        )
        self._resource_manager.set_state(
            f"feature:{self.interface_id}:metadata",
            self._metadata.to_dict()
        )
        
        if component_id:
            self._resource_manager.set_state(
                f"feature:{self.interface_id}:component_id",
                component_id
            )

    def add_functionality(self, functionality_id: str, description: str, requirements: Dict[str, Any] = None) -> Functionality:
        """Add a functionality to the feature and return the created instance."""
        # Import dependency type
        from dependency import DependencyType
        
        # Create new functionality
        functionality = Functionality(functionality_id, description, self.interface_id)
        
        # Add requirements if provided
        if requirements:
            for key, value in requirements.items():
                functionality.add_requirement(key, value)
        
        # Store in functionalities dictionary
        self._functionalities[functionality_id] = functionality
        
        # Add to metadata set
        self._metadata.functionalities.add(functionality_id)
        if requirements:
            self._metadata.requirements.update({functionality_id: requirements})
        
        # Update state in resource manager
        self._resource_manager.set_state(
            f"feature:{self.interface_id}:metadata",
            self._metadata.to_dict()
        )
        
        # Set up dependency tracking
        self._dependency_manager.add_node(functionality_id)
        
        # Create hierarchical dependency relationship
        full_feature_id = f"feature:{self.interface_id}"
        full_functionality_id = f"functionality:{functionality_id}"
        self._dependency_manager.add_hierarchical_dependency(
            full_feature_id, 
            full_functionality_id, 
            DependencyType.FEATURE_TO_FUNCTIONALITY
        )
        
        # Emit functionality added event
        self._resource_manager.emit_event(
            "feature_functionality_added",
            {
                "feature_id": self.interface_id,
                "functionality_id": functionality_id,
                "description": description,
                "requirements": requirements or {}
            }
        )
        
        return functionality

    def get_functionality(self, functionality_id: str) -> Functionality:
        """Get a functionality by ID."""
        if functionality_id not in self._functionalities:
            raise ValueError(f"Functionality not found: {functionality_id}")
        return self._functionalities[functionality_id]

    def get_all_functionalities(self) -> Dict[str, Functionality]:
        """Get all functionalities for this feature."""
        return self._functionalities.copy()
    
    def add_functionality_dependency(self, from_id: str, to_id: str) -> None:
        """Add a dependency between two functionalities."""
        # Verify functionalities exist
        if from_id not in self._functionalities:
            raise ValueError(f"Functionality not found: {from_id}")
        if to_id not in self._functionalities:
            raise ValueError(f"Functionality not found: {to_id}")
        
        # Add dependency in functionality object
        self._functionalities[from_id].add_dependency(to_id)
        
        # Add dependency in dependency manager
        self._dependency_manager.add_dependency(from_id, to_id)
        
        # Emit dependency added event
        self._resource_manager.emit_event(
            "feature_functionality_dependency_added",
            {
                "feature_id": self.interface_id,
                "source_functionality": from_id,
                "target_functionality": to_id
            }
        )

    def get_functionality_development_order(self) -> List[Set[str]]:
        """Get ordered development layers for functionalities based on dependencies."""
        return self._dependency_manager.get_development_order()

    def set_guidelines(self, guidelines: Union[Dict[str, Any], FeatureGuideline]) -> None:
        """Set feature-level guidelines."""
        if isinstance(guidelines, dict):
            self._metadata.guidelines = FeatureGuideline(
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
            f"feature:{self.interface_id}:metadata",
            self._metadata.to_dict()
        )
        
        # Emit guidelines set event
        self._resource_manager.emit_event(
            "feature_guidelines_set",
            {
                "feature_id": self.interface_id,
                "guidelines": self._metadata.guidelines.to_dict()
            }
        )

    def set_data_flow(self, data_flow: Union[Dict[str, Any], FeatureDataFlow]) -> None:
        """Set feature-level data flow."""
        if isinstance(data_flow, dict):
            self._metadata.data_flow = FeatureDataFlow(
                inputs=data_flow.get("inputs", {}),
                outputs=data_flow.get("outputs", {}),
                internal_flows=data_flow.get("internal_flows", []),
                data_transformations=data_flow.get("data_transformations", {})
            )
        else:
            self._metadata.data_flow = data_flow
        
        # Update state in resource manager
        self._resource_manager.set_state(
            f"feature:{self.interface_id}:metadata",
            self._metadata.to_dict()
        )
        
        # Emit data flow set event
        self._resource_manager.emit_event(
            "feature_data_flow_set",
            {
                "feature_id": self.interface_id,
                "data_flow": self._metadata.data_flow.to_dict()
            }
        )

    def set_evolution_state(self, state: EvolutionState) -> None:
        """Update the evolutionary state of this feature."""
        old_state = self._metadata.evolution_state
        self._metadata.evolution_state = state
        
        # Update state in resource manager
        self._resource_manager.set_state(
            f"feature:{self.interface_id}:metadata",
            self._metadata.to_dict()
        )
        
        # Emit evolution state change event
        self._resource_manager.emit_event(
            "feature_evolution_state_changed",
            {
                "feature_id": self.interface_id,
                "old_state": old_state.name,
                "new_state": state.name,
                "timestamp": datetime.now().isoformat()
            }
        )

    def add_dependency(self, feature_id: str) -> None:
        """Add a feature dependency."""
        self._metadata.dependencies.add(feature_id)
        super().add_dependency(FeatureInterface(feature_id))
        
        # Update state in resource manager
        self._resource_manager.set_state(
            f"feature:{self.interface_id}:dependencies",
            list(self._metadata.dependencies)
        )
        
        # Emit dependency added event
        self._resource_manager.emit_event(
            "feature_dependency_added",
            {
                "feature_id": self.interface_id,
                "dependency_id": feature_id
            }
        )

    def toggle(self, enabled: bool) -> None:
        """Toggle the feature on or off."""
        old_state = self._toggle.state
        self._toggle.enabled = enabled
        self._toggle.state = ToggleState.ON if enabled else ToggleState.OFF
        self._toggle.last_changed = datetime.now()
        self._toggle.transition_history.append((self._toggle.state, datetime.now()))
        
        # Update state in resource manager
        self._resource_manager.set_state(
            f"feature:{self.interface_id}:toggle",
            {
                "enabled": enabled,
                "state": self._toggle.state,
                "last_changed": self._toggle.last_changed
            }
        )
        
        # Emit toggle event
        self._resource_manager.emit_event(
            "feature_toggled",
            {
                "feature_id": self.interface_id,
                "enabled": enabled,
                "old_state": old_state,
                "new_state": self._toggle.state
            }
        )

    def is_enabled(self) -> bool:
        """Check if feature is enabled."""
        return self._toggle.enabled and self._toggle.state == ToggleState.ON

    def create_test_execution(self, test_id: str, test_type: str) -> TestExecution:
        """Create a new test execution."""
        execution = TestExecution(
            test_id=test_id,
            test_type=test_type,
            started_at=datetime.now()
        )
        self._test_executions[test_id] = execution
        
        # Update state in resource manager
        self._resource_manager.set_state(
            f"feature:{self.interface_id}:test:{test_id}",
            {
                "type": test_type,
                "state": execution.state,
                "started_at": execution.started_at
            }
        )
        
        return execution

    def update_test_state(self, test_id: str, state: TestState,
                         results: Optional[Dict[str, Any]] = None) -> None:
        """Update test execution state and results."""
        if test_id not in self._test_executions:
            raise ValueError(f"Test execution not found: {test_id}")
            
        execution = self._test_executions[test_id]
        execution.state = state
        if results:
            execution.results.update(results)
            
        if state in (TestState.FAILED, TestState.PASSED):
            execution.completed_at = datetime.now()
            
        # Update state in resource manager
        self._resource_manager.set_state(
            f"feature:{self.interface_id}:test:{test_id}",
            {
                "state": state,
                "results": results,
                "completed_at": execution.completed_at
            }
        )

    def create_build_process(self, build_id: str) -> BuildProcess:
        """Create a new build process."""
        build = BuildProcess(
            build_id=build_id,
            started_at=datetime.now()
        )
        self._build_processes[build_id] = build
        
        # Update state in resource manager
        self._resource_manager.set_state(
            f"feature:{self.interface_id}:build:{build_id}",
            {
                "state": build.state,
                "started_at": build.started_at
            }
        )
        
        return build

    def update_build_state(self, build_id: str, state: BuildState,
                          artifacts: Optional[Dict[str, Any]] = None,
                          errors: Optional[List[str]] = None) -> None:
        """Update build process state and results."""
        if build_id not in self._build_processes:
            raise ValueError(f"Build process not found: {build_id}")
            
        build = self._build_processes[build_id]
        build.state = state
        if artifacts:
            build.artifacts.update(artifacts)
        if errors:
            build.errors.extend(errors)
            
        if state in (BuildState.FAILED, BuildState.SUCCEEDED):
            build.completed_at = datetime.now()
            
        # Update state in resource manager
        self._resource_manager.set_state(
            f"feature:{self.interface_id}:build:{build_id}",
            {
                "state": state,
                "artifacts": artifacts,
                "errors": errors,
                "completed_at": build.completed_at
            }
        )

    def update_health_metric(self, metric_name: str, value: float) -> None:
        """Update a feature health metric."""
        self._health_metrics[metric_name] = value
        
        # Update metric in resource manager
        self._resource_manager.record_metric(
            f"feature:{self.interface_id}:health:{metric_name}",
            value
        )

    def get_health_status(self) -> Dict[str, float]:
        """Get current feature health status."""
        return self._health_metrics.copy()

    def validate(self) -> bool:
        """Validate feature state and relationships."""
        # First validate feature interface
        if not super().validate():
            return False
            
        # Validate functionalities
        if not self._functionalities:
            logger.error(f"No functionalities defined for feature: {self.interface_id}")
            return False
            
        # Validate dependencies
        for dependency_id in self._metadata.dependencies:
            dependency = FeatureInterface(dependency_id)
            if not dependency.validate():
                logger.error(f"Invalid dependency: {dependency_id}")
                return False
                
        # Validate test executions
        for test_id, execution in self._test_executions.items():
            if execution.state == TestState.FAILED:
                logger.error(f"Failed test execution: {test_id}")
                return False
                
        # Validate build processes
        for build_id, build in self._build_processes.items():
            if build.state == BuildState.FAILED:
                logger.error(f"Failed build process: {build_id}")
                return False
                
        # Validate functionalities
        for functionality_id, functionality in self._functionalities.items():
            if not functionality.validate():
                logger.error(f"Invalid functionality: {functionality_id}")
                return False
                
        return True
    
    def update_state(self, state: FeatureState) -> None:
        """Update the feature state."""
        old_state = self.state
        self.state = state
        
        # Update state in resource manager
        self._resource_manager.set_state(
            f"feature:{self.interface_id}:state",
            state
        )
        
        # Emit state change event
        self._resource_manager.emit_event(
            "feature_state_changed",
            {
                "feature_id": self.interface_id,
                "old_state": old_state,
                "new_state": state,
                "timestamp": datetime.now().isoformat()
            }
        )

def create_feature_from_definition(feature_def: Dict[str, Any]) -> Feature:
    """Create a Feature instance from a definition dictionary."""
    feature = Feature(
        feature_id=feature_def["id"],
        description=feature_def["description"]
    )
    
    # Add dependencies if specified
    if "dependencies" in feature_def:
        for dep_id in feature_def["dependencies"]:
            feature.add_dependency(dep_id)
    
    # Set guidelines if specified
    if "guidelines" in feature_def:
        feature.set_guidelines(feature_def["guidelines"])
    
    # Set data flow if specified
    if "data_flow" in feature_def:
        feature.set_data_flow(feature_def["data_flow"])
    
    # Add functionalities if specified
    if "functionalities" in feature_def:
        for func_def in feature_def["functionalities"]:
            feature.add_functionality(
                functionality_id=func_def["id"],
                description=func_def["description"],
                requirements=func_def.get("requirements")
            )
    
    # Set evolution state if specified
    if "evolution_state" in feature_def:
        feature.set_evolution_state(EvolutionState[feature_def["evolution_state"]])
    
    return feature

def register_feature_metrics(feature: Feature) -> None:
    """Register monitoring metrics for feature."""
    from resources.events import EventQueue
    event_queue = EventQueue()
    resource_manager = StateManager(event_queue)
    
    # Register functionality metrics
    resource_manager.record_metric(
        f"feature:{feature.interface_id}:functionality_count",
        len(feature._functionalities)
    )
    
    # Register dependency metrics
    resource_manager.record_metric(
        f"feature:{feature.interface_id}:dependency_count",
        len(feature._metadata.dependencies)
    )
    
    # Register toggle metrics
    resource_manager.record_metric(
        f"feature:{feature.interface_id}:toggle_enabled",
        1 if feature.is_enabled() else 0
    )
    
    # Register evolution metrics
    resource_manager.record_metric(
        f"feature:{feature.interface_id}:evolution_state",
        feature._metadata.evolution_state.value
    )
    
    # Register test metrics
    test_states = {state: 0 for state in TestState}
    for execution in feature._test_executions.values():
        test_states[execution.state] += 1
    for state, count in test_states.items():
        resource_manager.record_metric(
            f"feature:{feature.interface_id}:tests:{state.name.lower()}",
            count
        )
    
    # Register build metrics
    build_states = {state: 0 for state in BuildState}
    for build in feature._build_processes.values():
        build_states[build.state] += 1
    for state, count in build_states.items():
        resource_manager.record_metric(
            f"feature:{feature.interface_id}:builds:{state.name.lower()}",
            count
        )

def monitor_feature_changes(feature: Feature) -> None:
    """Monitor feature changes."""
    def feature_change_callback(event_type: str, data: Dict[str, Any]) -> None:
        if event_type in [
            "feature_functionality_added",
            "feature_dependency_added",
            "feature_toggled",
            "feature_guidelines_set",
            "feature_data_flow_set",
            "feature_evolution_state_changed",
            "feature_state_changed"
        ]:
            logger.info(f"Feature change event: {data}")
            register_feature_metrics(feature)
    
    from resources.events import EventQueue
    event_queue = EventQueue()
    resource_manager = StateManager(event_queue)
    resource_manager.subscribe_to_events("feature_functionality_added", 
                                       feature_change_callback)
    resource_manager.subscribe_to_events("feature_dependency_added", 
                                       feature_change_callback)
    resource_manager.subscribe_to_events("feature_toggled", 
                                       feature_change_callback)
    resource_manager.subscribe_to_events("feature_guidelines_set", 
                                       feature_change_callback)
    resource_manager.subscribe_to_events("feature_data_flow_set", 
                                       feature_change_callback)
    resource_manager.subscribe_to_events("feature_evolution_state_changed", 
                                       feature_change_callback)
    resource_manager.subscribe_to_events("feature_state_changed", 
                                       feature_change_callback)

def register_functionality_metrics(functionality: Functionality) -> None:
    """Register monitoring metrics for functionality."""
    from resources.events import EventQueue
    event_queue = EventQueue()
    resource_manager = StateManager(event_queue)
    
    # Register dependency metrics
    resource_manager.record_metric(
        f"functionality:{functionality.interface_id}:dependency_count",
        len(functionality._metadata.dependencies)
    )
    
    # Register implementation metrics
    resource_manager.record_metric(
        f"functionality:{functionality.interface_id}:has_implementation",
        1 if functionality._implementation_code else 0
    )
    
    # Register test metrics
    test_states = {state: 0 for state in TestState}
    for execution in functionality._test_executions.values():
        test_states[execution.state] += 1
    for state, count in test_states.items():
        resource_manager.record_metric(
            f"functionality:{functionality.interface_id}:tests:{state.name.lower()}",
            count
        )
    
    # Register build metrics
    build_states = {state: 0 for state in BuildState}
    for build in functionality._build_processes.values():
        build_states[build.state] += 1
    for state, count in build_states.items():
        resource_manager.record_metric(
            f"functionality:{functionality.interface_id}:builds:{state.name.lower()}",
            count
        )

def monitor_functionality_changes(functionality: Functionality) -> None:
    """Monitor functionality changes."""
    def functionality_change_callback(event_type: str, data: Dict[str, Any]) -> None:
        if event_type in [
            "functionality_implemented",
            "functionality_dependency_added",
            "functionality_state_changed"
        ]:
            logger.info(f"Functionality change event: {data}")
            register_functionality_metrics(functionality)
    
    from resources.events import EventQueue
    event_queue = EventQueue()
    resource_manager = StateManager(event_queue)
    resource_manager.subscribe_to_events("functionality_implemented", 
                                       functionality_change_callback)
    resource_manager.subscribe_to_events("functionality_dependency_added", 
                                       functionality_change_callback)
    resource_manager.subscribe_to_events("functionality_state_changed", 
                                       functionality_change_callback)