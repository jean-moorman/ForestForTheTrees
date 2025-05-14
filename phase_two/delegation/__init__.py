"""
Phase Two Delegation Package
===========================

This package provides the delegation mechanism for Phase Two to hand off
component implementation and testing to Phase Three. The delegation framework
includes:

1. Component to Feature mapping
2. Event handling for delegation lifecycle
3. State tracking for delegated tasks
4. Interface for Phase Three interaction
5. Recovery mechanisms for failed delegations

The delegation framework is designed to ensure that Phase Two can orchestrate
the systematic development process while delegating the actual implementation
to Phase Three's feature cultivation process.
"""

from phase_two.delegation.mapper import ComponentToFeatureMapper
from phase_two.delegation.events import DelegationEventHandler, DelegationEventType
from phase_two.delegation.state import DelegationStateTracker, DelegationState
from phase_two.delegation.interface import PhaseThreeDelegationInterface
from phase_two.delegation.recovery import DelegationRecoveryHandler, RecoveryStrategy

__all__ = [
    'ComponentToFeatureMapper',
    'DelegationEventHandler',
    'DelegationEventType',
    'DelegationStateTracker',
    'DelegationState',
    'PhaseThreeDelegationInterface',
    'DelegationRecoveryHandler',
    'RecoveryStrategy'
]