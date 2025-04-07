"""
Core Classes:
Version: Implements semantic versioning with parsing and comparison
VersionInterface: Inherits from BaseInterface for version management
VersionConstraint: Handles version constraint validation
VersionState: Enum for version lifecycle states

Integration Points:
Uses resource.py for state management and event propagation
Inherits from interface.py's BaseInterface
Integrates with monitoring through metrics registration
Uses resource.py's event system for version changes

Key Features:
Semantic versioning implementation
Version state tracking and propagation
Version constraint validation
Version history management
Monitoring integration
Event propagation for version changes

Design Decisions:
Used inheritance from BaseInterface for consistency
Implemented comprehensive version parsing and validation
Integrated closely with resource management
Added monitoring hooks for version metrics
Included version constraint validation"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
import re
import logging
from datetime import datetime

from interface import BaseInterface

from resources import StateManager, ResourceState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VersionType(Enum):
    MAJOR = auto()
    MINOR = auto()
    PATCH = auto()

class VersionState(Enum):
    DRAFT = auto()
    STABLE = auto()
    DEPRECATED = auto()
    ARCHIVED = auto()

@dataclass
class Version:
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None

    def __str__(self) -> str:
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version

    @classmethod
    def parse(cls, version_str: str) -> 'Version':
        """Parse a version string into a Version object."""
        pattern = r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z-]+))?(?:\+([0-9A-Za-z-]+))?$"
        match = re.match(pattern, version_str)
        if not match:
            raise ValueError(f"Invalid version string: {version_str}")
            
        major, minor, patch, prerelease, build = match.groups()
        return cls(
            major=int(major),
            minor=int(minor),
            patch=int(patch),
            prerelease=prerelease,
            build=build
        )

    def increment(self, version_type: VersionType) -> 'Version':
        """Create a new Version with incremented version numbers."""
        if version_type == VersionType.MAJOR:
            return Version(self.major + 1, 0, 0)
        elif version_type == VersionType.MINOR:
            return Version(self.major, self.minor + 1, 0)
        else:  # PATCH
            return Version(self.major, self.minor, self.patch + 1)

class VersionInterface(BaseInterface):
    """Version management interface inheriting from BaseInterface."""
    
    def __init__(self, component_id: str):
        super().__init__(f"version:{component_id}")
        self._current_version: Optional[Version] = None
        self._version_history: List[Tuple[Version, datetime]] = []
        self._version_state = VersionState.DRAFT
        self._resource_manager = StateManager()
        
        # Register with resource manager
        self._resource_manager.set_state(
            f"version:{self.interface_id}:current",
            str(self._current_version) if self._current_version else None
        )
        self._resource_manager.set_state(
            f"version:{self.interface_id}:state",
            self._version_state
        )

    def set_version(self, version: Version) -> None:
        """Set the current version."""
        old_version = self._current_version
        self._current_version = version
        self._version_history.append((version, datetime.now()))
        
        # Update state in resource manager
        self._resource_manager.set_state(
            f"version:{self.interface_id}:current",
            str(version),
            metadata={"old_version": str(old_version) if old_version else None}
        )
        
        # Emit version change event
        self._resource_manager.emit_event(
            "version_changed",
            {
                "interface_id": self.interface_id,
                "old_version": str(old_version) if old_version else None,
                "new_version": str(version)
            }
        )

    def increment_version(self, version_type: VersionType) -> None:
        """Increment the current version."""
        if not self._current_version:
            self.set_version(Version(1, 0, 0))
        else:
            self.set_version(self._current_version.increment(version_type))

    def set_version_state(self, state: VersionState) -> None:
        """Set the version state."""
        old_state = self._version_state
        self._version_state = state
        
        # Update state in resource manager
        self._resource_manager.set_state(
            f"version:{self.interface_id}:state",
            state,
            metadata={"old_state": old_state}
        )
        
        # Emit state change event
        self._resource_manager.emit_event(
            "version_state_changed",
            {
                "interface_id": self.interface_id,
                "old_state": old_state,
                "new_state": state
            }
        )

    def get_version_history(self) -> List[Tuple[Version, datetime]]:
        """Get the version history."""
        return self._version_history.copy()

    def validate(self) -> bool:
        """Validate version interface state."""
        # First validate base interface
        if not super().validate_dependencies():
            return False
            
        # Validate version-specific rules
        if not self._current_version:
            logger.error("No current version set")
            return False
            
        if self._version_state == VersionState.STABLE:
            # Additional validation for stable versions
            if self._current_version.prerelease:
                logger.error("Stable version cannot have prerelease tag")
                return False
                
        return True

class VersionConstraint:
    """Class for version constraint validation."""
    
    def __init__(self, constraint_str: str):
        self.constraint_str = constraint_str
        self.parse_constraint()

    def parse_constraint(self) -> None:
        """Parse version constraint string."""
        # Simple constraint parsing - can be extended for more complex constraints
        self.operator = None
        self.version = None
        
        operators = ['>=', '<=', '>', '<', '=', '^', '~']
        for op in operators:
            if self.constraint_str.startswith(op):
                self.operator = op
                version_str = self.constraint_str[len(op):].strip()
                self.version = Version.parse(version_str)
                break
                
        if not self.operator:
            self.version = Version.parse(self.constraint_str)
            self.operator = '='

    def validate(self, version: Version) -> bool:
        """Validate if a version meets the constraint."""
        if self.operator == '=':
            return str(version) == str(self.version)
        elif self.operator == '>':
            return version.major > self.version.major or \
                   (version.major == self.version.major and version.minor > self.version.minor) or \
                   (version.major == self.version.major and version.minor == self.version.minor and \
                    version.patch > self.version.patch)
        elif self.operator == '>=':
            return version.major > self.version.major or \
                   (version.major == self.version.major and version.minor > self.version.minor) or \
                   (version.major == self.version.major and version.minor == self.version.minor and \
                    version.patch >= self.version.patch)
        # Add other operators as needed
        return False

def register_version_metrics(version_interface: VersionInterface) -> None:
    """Register monitoring metrics for version interface."""
    resource_manager = StateManager()
    
    # Register basic version metric
    if version_interface._current_version:
        resource_manager.record_metric(
            f"version:{version_interface.interface_id}:major",
            version_interface._current_version.major
        )
        resource_manager.record_metric(
            f"version:{version_interface.interface_id}:minor",
            version_interface._current_version.minor
        )
        resource_manager.record_metric(
            f"version:{version_interface.interface_id}:patch",
            version_interface._current_version.patch
        )
    
    # Register version state metric
    resource_manager.record_metric(
        f"version:{version_interface.interface_id}:state",
        version_interface._version_state.value
    )

def monitor_version_changes(version_interface: VersionInterface) -> None:
    """Monitor version changes."""
    def version_change_callback(event_type: str, data: Dict[str, Any]) -> None:
        if event_type in ["version_changed", "version_state_changed"]:
            logger.info(f"Version change event: {data}")
            register_version_metrics(version_interface)
    
    resource_manager = StateManager()
    resource_manager.subscribe_to_events("version_changed", version_change_callback)
    resource_manager.subscribe_to_events("version_state_changed", version_change_callback)