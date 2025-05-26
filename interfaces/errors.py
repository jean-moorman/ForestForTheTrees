"""
Error classes for the interfaces package.
Contains base exception classes used across the FFTT interface system.
"""


class InterfaceError(Exception):
    """Base class for interface errors."""
    pass


class InitializationError(InterfaceError):
    """Error during interface initialization."""
    pass


class StateTransitionError(InterfaceError):
    """Error during state transition."""
    pass


class ResourceError(InterfaceError):
    """Error related to resource management."""
    pass


class ValidationError(InterfaceError):
    """Error during validation."""
    pass


class TimeoutError(InterfaceError):
    """Error when an operation times out."""
    pass