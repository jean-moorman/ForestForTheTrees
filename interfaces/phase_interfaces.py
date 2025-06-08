"""
Phase interfaces for cross-phase communication.
This module provides neutral interfaces to avoid circular dependencies between phases.
"""
from typing import Dict, Any, Protocol


class PhaseZeroInterface(Protocol):
    """Interface for interacting with Phase Zero agents."""
    async def process_system_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process system metrics through Phase Zero quality assurance agents.
        
        Args:
            metrics: Dictionary containing system metrics and context
            
        Returns:
            Dictionary containing Phase Zero analysis and recommendations
        """
        pass