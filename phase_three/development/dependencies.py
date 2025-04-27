import logging
from typing import Dict, Any, List, Set

from resources import StateManager

logger = logging.getLogger(__name__)

class DependencyResolver:
    """Responsible for resolving dependencies between features"""
    
    def __init__(self, state_manager: StateManager):
        """Initialize the dependency resolver.
        
        Args:
            state_manager: Manager for application state
        """
        self._state_manager = state_manager
    
    async def get_dependency_implementations(self, 
                                           dependencies: Set[str], 
                                           development_contexts: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get implementations of dependencies.
        
        Args:
            dependencies: Set of dependency IDs
            development_contexts: Dictionary of feature development contexts
            
        Returns:
            List of dependency implementations
        """
        dependency_implementations = []
        
        for dep_id in dependencies:
            # Check if dependency exists in development contexts
            if dep_id in development_contexts:
                context = development_contexts[dep_id]
                if context.implementation:
                    dependency_implementations.append({
                        "feature_id": dep_id,
                        "feature_name": context.feature_name,
                        "implementation": context.implementation
                    })
            else:
                # Check if dependency exists in state manager
                dep_state = await self._state_manager.get_state(f"feature:implementation:{dep_id}")
                if dep_state:
                    dependency_implementations.append(dep_state)
        
        return dependency_implementations
    
    async def get_dependent_features(self, feature_id: str) -> List[str]:
        """Find features that depend on the given feature.
        
        Args:
            feature_id: ID of the feature to find dependents for
            
        Returns:
            List of dependent feature IDs
        """
        # In a real implementation, this would query the dependency graph
        # Here we'll just search state for features with this dependency
        dependent_features = []
        
        # Placeholder for dependency resolution logic
        # In a real implementation, this would search all features for dependencies
        # including the specified feature_id
        
        return dependent_features