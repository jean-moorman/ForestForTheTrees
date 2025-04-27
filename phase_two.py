"""
Phase Two - Systematic Development Process
========================================

This module serves as a compatibility layer for the refactored phase_two package.
It re-exports the PhaseTwo class from the package to maintain backward compatibility.
"""

from phase_two import PhaseTwo

# Re-export for backward compatibility
__all__ = ['PhaseTwo']