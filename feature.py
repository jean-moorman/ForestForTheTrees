"""
Core Classes:
Feature: Inherits from FeatureInterface for feature management
FeatureTest: Manages feature-level test execution
FeatureBuild: Handles feature build process
FeatureToggle: Manages feature toggle state

Key Features:
Feature toggle management
Test execution tracking
Build process monitoring
Health metrics tracking
Event propagation

Design Decisions:
Inherited from FeatureInterface for consistency
Implemented comprehensive toggle management
Added extensive test tracking
Included build monitoring
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
from datetime import datetime

from interface import FeatureInterface
from resources import ResourceState, StateManager
from component import TestState, BuildState, TestExecution, BuildProcess

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeatureState(Enum):
    INITIALIZED = auto()
    IMPLEMENTING = auto()
    TESTING = auto()
    ACTIVE = auto()
    DISABLED = auto()
    ERROR = auto()

class ToggleState(Enum):
    ON = auto()
    OFF = auto()
    TRANSITIONING = auto()

@dataclass
class FeatureToggle:
    enabled: bool = True
    state: ToggleState = ToggleState.ON
    last_changed: datetime = field(default_factory=datetime.now)
    transition_history: List[Tuple[ToggleState, datetime]] = field(default_factory=list)

@dataclass
class FeatureMetadata:
    description: str
    functionalities: Set[str] = field(default_factory=set)
    requirements: Dict[str, Any] = field(default_factory=dict)
    dependencies: Set[str] = field(default_factory=set)

class Feature(FeatureInterface):
    """Feature class managing feature implementation and toggle state."""
    
    def __init__(self, feature_id: str, description: str):
        super().__init__(feature_id)
        self.state = FeatureState.INITIALIZED
        self._metadata = FeatureMetadata(description=description)
        self._toggle = FeatureToggle()
        self._test_executions: Dict[str, TestExecution] = {}
        self._build_processes: Dict[str, BuildProcess] = {}
        self._health_metrics: Dict[str, float] = {}
        
        # Initialize resource states
        self._resource_manager.set_state(
            f"feature:{self.interface_id}:state",
            self.state
        )
        self._resource_manager.set_state(
            f"feature:{self.interface_id}:metadata",
            {
                "description": description,
                "functionalities": list(self._metadata.functionalities),
                "requirements": self._metadata.requirements
            }
        )

    def add_functionality(self, functionality: str, requirements: Dict[str, Any]) -> None:
        """Add a functionality to the feature."""
        self._metadata.functionalities.add(functionality)
        self._metadata.requirements.update({functionality: requirements})
        
        # Update state in resource manager
        self._resource_manager.set_state(
            f"feature:{self.interface_id}:metadata",
            {
                "description": self._metadata.description,
                "functionalities": list(self._metadata.functionalities),
                "requirements": self._metadata.requirements
            }
        )
        
        # Emit functionality added event
        self._resource_manager.emit_event(
            "feature_functionality_added",
            {
                "feature_id": self.interface_id,
                "functionality": functionality,
                "requirements": requirements
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
        if not self._metadata.functionalities:
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
                
        return True

def register_feature_metrics(feature: Feature) -> None:
    """Register monitoring metrics for feature."""
    resource_manager = StateManager()
    
    # Register functionality metrics
    resource_manager.record_metric(
        f"feature:{feature.interface_id}:functionality_count",
        len(feature._metadata.functionalities)
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
            "feature_toggled"
        ]:
            logger.info(f"Feature change event: {data}")
            register_feature_metrics(feature)
    
    resource_manager = StateManager()
    resource_manager.subscribe_to_events("feature_functionality_added", 
                                       feature_change_callback)
    resource_manager.subscribe_to_events("feature_dependency_added", 
                                       feature_change_callback)
    resource_manager.subscribe_to_events("feature_toggled", 
                                       feature_change_callback)