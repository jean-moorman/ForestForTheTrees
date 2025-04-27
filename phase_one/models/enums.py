"""
Enums for phase one development and validation states.
"""
from enum import Enum

class DevelopmentState(Enum):
    INITIALIZING = "initializing" 
    ANALYZING = "analyzing"
    DESIGNING = "designing"
    VALIDATING = "validating"
    REFINING = "refining"
    ERROR = "error"
    COMPLETE = "complete"
    
class PhaseValidationState(Enum):
    NOT_STARTED = "not_started"
    DATA_FLOW_VALIDATING = "data_flow_validating"
    DATA_FLOW_REVISING = "data_flow_revising"
    STRUCTURAL_VALIDATING = "structural_validating"
    STRUCTURAL_REVISING = "structural_revising"
    CROSS_VALIDATING = "cross_validating"
    ARBITRATION = "arbitration"
    COMPLETED = "completed"