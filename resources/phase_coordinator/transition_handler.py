"""
Forest For The Trees (FFTT) Phase Coordination System - Transition Handler
---------------------------------------------------
Contains the protocol and utilities for transition handling between phases.
"""
import logging
from typing import Dict, Any, List, Optional, Protocol, Callable, Awaitable
from importlib import import_module

logger = logging.getLogger(__name__)

class PhaseTransitionHandler(Protocol):
    """Protocol for handlers that manage transitions between phases"""
    
    async def before_start(self, phase_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Called before a phase starts, can modify input data"""
        ...
        
    async def after_completion(self, phase_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Called after a phase completes, can modify result data"""
        ...
        
    async def on_failure(self, phase_id: str, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Called when a phase fails, can implement recovery or clean-up"""
        ...
        
    async def on_pause(self, phase_id: str, reason: str, context: Dict[str, Any]) -> None:
        """Called when a phase is paused"""
        ...
        
    async def on_resume(self, phase_id: str, context: Dict[str, Any]) -> None:
        """Called when a phase is resumed"""
        ...

def register_transition_handlers(handler_names: List[str]) -> List[PhaseTransitionHandler]:
    """
    Register transition handlers from a list of handler names
    
    Args:
        handler_names: List of handler names to register (format: "module_path.ClassName")
        
    Returns:
        List of instantiated handlers
    """
    if not handler_names:
        return []
    
    handlers = []
    
    for handler_name in handler_names:
        try:
            # Parse module and class name (expected format: module_path.ClassName)
            if '.' in handler_name:
                module_path, class_name = handler_name.rsplit('.', 1)
                # Import the module
                module = import_module(module_path)
                # Get the handler class
                handler_class = getattr(module, class_name)
                # Check if it's a valid transition handler
                if hasattr(handler_class, '__mro__') and PhaseTransitionHandler in handler_class.__mro__:
                    # Create instance and register
                    handler_instance = handler_class()
                    handlers.append(handler_instance)
                    logger.info(f"Registered handler {handler_name}")
                else:
                    logger.warning(f"Handler {handler_name} is not a valid PhaseTransitionHandler")
            else:
                logger.warning(f"Invalid handler format: {handler_name}, expected module.ClassName")
        except (ImportError, AttributeError, ValueError) as e:
            logger.error(f"Failed to register handler {handler_name}: {str(e)}")
    
    return handlers

def get_transition_handlers(handlers_map: Dict[str, List[PhaseTransitionHandler]],
                           source_phase: str, 
                           target_phase: str) -> List[PhaseTransitionHandler]:
    """
    Get transition handlers for a phase transition
    
    Args:
        handlers_map: Map of phase IDs to handlers
        source_phase: Source phase ID
        target_phase: Target phase ID
        
    Returns:
        List of transition handlers
    """
    # Combine source and target phase handlers
    handlers = []
    
    # First source phase handlers
    if source_phase in handlers_map:
        handlers.extend(handlers_map[source_phase])
        
    # Then target phase handlers
    if target_phase in handlers_map and target_phase != source_phase:
        handlers.extend(handlers_map[target_phase])
        
    return handlers