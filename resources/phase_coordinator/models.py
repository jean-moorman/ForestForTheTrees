"""
Forest For The Trees (FFTT) Phase Coordination System - Models
---------------------------------------------------
Contains data models used by the phase coordination system.
"""
import logging
from typing import Dict, Any, Optional, List, Set, Union
from dataclasses import dataclass, field
from datetime import datetime

from resources.phase_coordinator.constants import PhaseState, PhaseType, _CUSTOM_PHASE_TYPES

logger = logging.getLogger(__name__)

@dataclass
class PhaseContext:
    """Context information for a phase"""
    phase_id: str
    phase_type: Union[PhaseType, str]  # Can be built-in enum or custom string type
    state: PhaseState = PhaseState.INITIALIZING
    parent_phase_id: Optional[str] = None
    child_phases: Set[str] = field(default_factory=set)
    dependencies: Set[str] = field(default_factory=set)
    config: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    checkpoint_ids: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_info: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_custom_type: bool = False  # Flag to indicate if using a custom phase type
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for storage"""
        # For phase_type, handle both enum and string cases
        phase_type_value = self.phase_type.value if isinstance(self.phase_type, PhaseType) else self.phase_type
        
        return {
            "phase_id": self.phase_id,
            "phase_type": phase_type_value,
            "is_custom_type": self.is_custom_type,
            "state": self.state.name,
            "parent_phase_id": self.parent_phase_id,
            "child_phases": list(self.child_phases),
            "dependencies": list(self.dependencies),
            "config": self.config,
            "metrics": self.metrics,
            "checkpoint_ids": self.checkpoint_ids,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "error_info": self.error_info,
            "result": self.result,
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PhaseContext':
        """Create context from dictionary"""
        # Handle both custom and built-in phase types
        is_custom_type = data.get("is_custom_type", False)
        phase_type_value = data["phase_type"]
        
        if is_custom_type:
            # Custom phase type is stored as a string
            phase_type = phase_type_value
        else:
            # Built-in phase type
            try:
                phase_type = PhaseType(phase_type_value)
            except ValueError:
                # Fallback: if value doesn't match built-in but exists as custom
                if phase_type_value in _CUSTOM_PHASE_TYPES:
                    phase_type = phase_type_value
                    is_custom_type = True
                else:
                    # Default to phase one for backward compatibility
                    logger.warning(f"Unknown phase type: {phase_type_value}, defaulting to phase_one")
                    phase_type = PhaseType.ONE
        
        context = cls(
            phase_id=data["phase_id"],
            phase_type=phase_type,
            is_custom_type=is_custom_type
        )
        context.state = PhaseState[data["state"]]
        context.parent_phase_id = data.get("parent_phase_id")
        context.child_phases = set(data.get("child_phases", []))
        context.dependencies = set(data.get("dependencies", []))
        context.config = data.get("config", {})
        context.metrics = data.get("metrics", {})
        context.checkpoint_ids = data.get("checkpoint_ids", [])
        context.metadata = data.get("metadata", {})
        
        if data.get("start_time"):
            context.start_time = datetime.fromisoformat(data["start_time"])
        if data.get("end_time"):
            context.end_time = datetime.fromisoformat(data["end_time"])
            
        context.error_info = data.get("error_info")
        context.result = data.get("result")
        
        return context

@dataclass
class NestedPhaseExecution:
    """Tracks a nested phase execution"""
    parent_id: str
    child_id: str
    execution_id: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    status: str = "pending"
    result: Any = None
    error: Optional[str] = None
    timeout_seconds: int = 7200  # Default timeout of 2 hours
    priority: str = "normal"  # Priority: high, normal, low
    health_checks: List[datetime] = field(default_factory=list)  # Timestamps of health checks
    progress_updates: Dict[str, Any] = field(default_factory=dict)  # Progress information
    last_activity: Optional[datetime] = None  # Last recorded activity timestamp