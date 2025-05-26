"""
Metrics tracking for agent interfaces in the FFTT system.
"""

import asyncio
from collections import Counter, defaultdict
from datetime import datetime
import logging
from typing import Dict, List, Any

from resources import (
    EventQueue,
    StateManager,
    MetricsManager,
    ResourceState
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InterfaceMetrics:
    """
    Handles interface metrics with enhanced error handling and comprehensive metrics collection.
    """
    def __init__(self, event_queue: EventQueue, state_manager: StateManager, interface_id: str):
        """
        Initialize interface metrics.
        
        Args:
            event_queue: Queue for event handling
            state_manager: Manager for state persistence
            interface_id: ID of the interface
        """
        self._metrics_manager = MetricsManager(event_queue)
        self._state_manager = state_manager
        self._interface_id = interface_id
        self._event_queue = event_queue
        
        # Initialize metrics collection in background
        asyncio.create_task(self._initialize_metrics())
        
    async def _initialize_metrics(self) -> None:
        """Initialize basic metrics for the interface."""
        try:
            # Register basic interface existence metric
            await self._metrics_manager.record_metric(
                f"interface:{self._interface_id}:initialized",
                1.0,
                metadata={"timestamp": datetime.now().isoformat()}
            )
        except Exception as e:
            logger.warning(f"Failed to initialize metrics for {self._interface_id}: {str(e)}")
        
    async def register_core_metrics(self, interface_state: ResourceState) -> None:
        """
        Register core interface metrics with improved error handling.
        
        Args:
            interface_state: Current state of the interface
        """
        try:
            # Record health metric
            await self._metrics_manager.record_metric(
                f"interface:{self._interface_id}:health",
                1.0 if interface_state == ResourceState.ACTIVE else 0.0,
                metadata={"state": interface_state.name, "timestamp": datetime.now().isoformat()}
            )
            
            # Record state transition count
            try:
                state_history = await self._state_manager.get_state_history(
                    f"interface:{self._interface_id}:state"
                )
                
                await self._metrics_manager.record_metric(
                    f"interface:{self._interface_id}:state_changes",
                    len(state_history),
                    metadata={"last_state": interface_state.name}
                )
                
                # Record state duration if applicable
                if state_history and len(state_history) >= 2:
                    # Calculate time in current state
                    current_state_start = state_history[-1].get("timestamp")
                    if current_state_start:
                        try:
                            start_time = datetime.fromisoformat(current_state_start)
                            duration = (datetime.now() - start_time).total_seconds()
                            
                            await self._metrics_manager.record_metric(
                                f"interface:{self._interface_id}:state_duration",
                                duration,
                                metadata={"state": interface_state.name}
                            )
                        except Exception as e:
                            logger.warning(f"Failed to calculate state duration: {str(e)}")
                
            except Exception as e:
                logger.warning(f"Failed to record state history metrics: {str(e)}")
                
        except Exception as e:
            logger.error(f"Failed to register core metrics for {self._interface_id}: {str(e)}")
            
            # Try to emit an error event
            try:
                from resources.events import ResourceEventTypes
                await self._event_queue.emit(
                    ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
                    {
                        "interface_id": self._interface_id,
                        "error": str(e),
                        "error_type": "metrics_failure",
                        "component": "core_metrics"
                    }
                )
            except Exception:
                pass  # Ignore event emission failures
            
    async def register_validation_metrics(self, validation_history: List[Dict[str, Any]]) -> None:
        """
        Register validation-related metrics with improved error handling and more detailed metrics.
        
        Args:
            validation_history: History of validation operations
        """
        if not validation_history:
            return
            
        try:
            # Calculate success rate
            success_count = sum(1 for v in validation_history if v.get("success", False))
            total_count = len(validation_history)
            success_rate = success_count / total_count if total_count > 0 else 0
            
            # Record success rate
            await self._metrics_manager.record_metric(
                f"interface:{self._interface_id}:validation:success_rate",
                success_rate,
                metadata={
                    "success_count": success_count,
                    "total_count": total_count,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Record attempts count
            await self._metrics_manager.record_metric(
                f"interface:{self._interface_id}:validation:attempts",
                total_count
            )
            
            # Record average attempts needed for success if applicable
            if success_count > 0:
                # Group validation history by operation
                validation_by_operation = defaultdict(list)
                for validation in validation_history:
                    operation = validation.get("operation_id", "unknown")
                    validation_by_operation[operation].append(validation)
                
                # Calculate attempts needed for successful operations
                attempts_until_success = []
                for operation, validations in validation_by_operation.items():
                    # Sort by timestamp if available
                    if all("timestamp" in v for v in validations):
                        validations.sort(key=lambda v: v.get("timestamp", ""))
                    
                    # Count attempts until first success
                    for i, validation in enumerate(validations, 1):
                        if validation.get("success", False):
                            attempts_until_success.append(i)
                            break
                
                if attempts_until_success:
                    avg_attempts = sum(attempts_until_success) / len(attempts_until_success)
                    await self._metrics_manager.record_metric(
                        f"interface:{self._interface_id}:validation:avg_attempts_to_success",
                        avg_attempts
                    )
            
            # Record common error types if failures exist
            if success_count < total_count:
                error_counts = Counter()
                for validation in validation_history:
                    if not validation.get("success", False) and "error_analysis" in validation:
                        error_analysis = validation["error_analysis"]
                        error_type = error_analysis.get("error_type", "unknown")
                        error_counts[error_type] += 1
                
                # Record top errors
                for error_type, count in error_counts.most_common(5):
                    await self._metrics_manager.record_metric(
                        f"interface:{self._interface_id}:validation:error:{error_type}",
                        count,
                        metadata={"error_type": error_type}
                    )
                
        except Exception as e:
            logger.error(f"Failed to register validation metrics for {self._interface_id}: {str(e)}")
            
            # Try to emit an error event
            try:
                from resources.events import ResourceEventTypes
                await self._event_queue.emit(
                    ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
                    {
                        "interface_id": self._interface_id,
                        "error": str(e),
                        "error_type": "metrics_failure",
                        "component": "validation_metrics"
                    }
                )
            except Exception:
                pass  # Ignore event emission failures
    
    async def register_performance_metrics(self, 
                                        response_time: float,
                                        processing_result: Dict[str, Any]) -> None:
        """
        Register performance metrics for the interface.
        
        Args:
            response_time: Time taken to process the request
            processing_result: Result of the processing operation
        """
        try:
            # Record response time
            await self._metrics_manager.record_metric(
                f"interface:{self._interface_id}:response_time",
                response_time,
                metadata={"timestamp": datetime.now().isoformat()}
            )
            
            # Record success/failure
            is_success = "error" not in processing_result
            await self._metrics_manager.record_metric(
                f"interface:{self._interface_id}:success",
                1.0 if is_success else 0.0
            )
            
            # Record specific metrics based on result
            if not is_success:
                error_type = "unknown"
                if isinstance(processing_result.get("error"), str):
                    # Extract general error category
                    error_text = processing_result["error"].lower()
                    if "timeout" in error_text:
                        error_type = "timeout"
                    elif "validation" in error_text:
                        error_type = "validation"
                    elif "memory" in error_text:
                        error_type = "memory"
                    elif "permission" in error_text:
                        error_type = "permission"
                    
                await self._metrics_manager.record_metric(
                    f"interface:{self._interface_id}:error:{error_type}",
                    1.0,
                    metadata={"error_message": str(processing_result.get("error", ""))}
                )
                
        except Exception as e:
            logger.warning(f"Failed to register performance metrics: {str(e)}")
            # Continue execution - metrics failures shouldn't block the main process