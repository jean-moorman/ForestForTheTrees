import logging
import asyncio
from typing import Dict, Any, Optional

from resources import (
    PhaseCoordinationIntegration,
    EventQueue,
    StateManager,
    AgentContextManager,
    CacheManager,
    MetricsManager,
    MemoryMonitor,
    SystemMonitor,
    PhaseType
)
# Import ErrorHandler directly
from resources import ErrorHandler
# Import CoordinationPhaseState correctly (it's PhaseState in the imports)
from resources import PhaseState as CoordinationPhaseState

logger = logging.getLogger(__name__)

class PhaseTwoCoordinator:
    """Handles coordination with other phases"""
    
    def __init__(self,
                event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                memory_monitor: Optional[MemoryMonitor] = None,
                system_monitor: Optional[SystemMonitor] = None):
        # Create phase coordination if not provided
        self._phase_coordination = PhaseCoordinationIntegration(
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor,
            system_monitor
        )
        # Initialize the coordination
        asyncio.create_task(self._phase_coordination.initialize())
    
    async def initialize_phase(self, config: Dict[str, Any], parent_phase_id: Optional[str] = None) -> str:
        """Initialize phase with the coordinator"""
        phase_id = await self._phase_coordination.initialize_phase_two(config, parent_phase_id)
        logger.info(f"Phase Two initialized with coordination ID: {phase_id}")
        return phase_id
    
    async def create_checkpoint(self, phase_id: str) -> str:
        """Create a checkpoint for the current phase"""
        try:
            # Create checkpoint for completion state
            checkpoint_id = await self._phase_coordination.create_checkpoint(phase_id)
            logger.info(f"Created completion checkpoint {checkpoint_id} for phase {phase_id}")
            return checkpoint_id
        except Exception as coord_error:
            logger.warning(f"Failed to create checkpoint: {str(coord_error)}")
            return ""
    
    async def abort_phase(self, phase_id: str, reason: str) -> None:
        """Abort the current phase with a specific reason"""
        try:
            # Attempt to abort the phase with the coordinator
            await self._phase_coordination.abort_phase(
                phase_id, 
                reason
            )
        except Exception as coord_error:
            logger.error(f"Failed to report error to coordinator: {str(coord_error)}")
    
    async def coordinate_nested_execution(self, 
                                        parent_phase_id: str, 
                                        target_phase_type: PhaseType,
                                        input_data: Dict[str, Any],
                                        config: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate nested execution with another phase"""
        return await self._phase_coordination.coordinate_nested_execution(
            parent_phase_id,
            target_phase_type,
            input_data,
            config
        )
    
    def get_coordinator(self) -> PhaseCoordinationIntegration:
        """Get the underlying coordinator instance"""
        return self._phase_coordination