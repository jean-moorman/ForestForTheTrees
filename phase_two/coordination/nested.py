"""
Nested Phase Coordinator for Phase Two
-------------------------------------
Provides API for initiating nested phase calls, checkpoint management,
result aggregation, and context propagation to nested phases.
"""

import logging
import asyncio
import uuid
from typing import Dict, Any, List, Optional, Tuple, Set, Union
from datetime import datetime

from resources import (
    PhaseCoordinationIntegration,
    EventQueue,
    StateManager,
    AgentContextManager,
    CacheManager,
    MetricsManager,
    MemoryMonitor,
    SystemMonitor,
    PhaseType,
    ResourceEventTypes
)
from resources.phase_coordinator import PhaseContext, PhaseState

from phase_two.coordination.checkpoints import CoordinationCheckpointManager

logger = logging.getLogger(__name__)

class NestedPhaseCoordinator:
    """
    Manages nested phase executions from Phase Two to other phases.
    
    This class provides:
    1. API for initiating nested phase calls to Phase Three and Four
    2. Checkpoint creation before and after nested execution
    3. Result aggregation from nested phases
    4. Context propagation to nested phases
    """
    
    def __init__(self,
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 phase_coordination: PhaseCoordinationIntegration,
                 checkpoint_manager: Optional[CoordinationCheckpointManager] = None,
                 memory_monitor: Optional[MemoryMonitor] = None,
                 system_monitor: Optional[SystemMonitor] = None):
        """
        Initialize the NestedPhaseCoordinator.
        
        Args:
            event_queue: EventQueue for emitting events
            state_manager: StateManager for state persistence
            context_manager: AgentContextManager for managing agent contexts
            cache_manager: CacheManager for caching
            metrics_manager: MetricsManager for metrics recording
            phase_coordination: PhaseCoordinationIntegration for coordination with other phases
            checkpoint_manager: Optional CoordinationCheckpointManager
            memory_monitor: Optional MemoryMonitor for monitoring memory
            system_monitor: Optional SystemMonitor for system monitoring
        """
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._context_manager = context_manager
        self._cache_manager = cache_manager
        self._metrics_manager = metrics_manager
        self._phase_coordination = phase_coordination
        self._memory_monitor = memory_monitor
        self._system_monitor = system_monitor
        
        # Create checkpoint manager if not provided
        self._checkpoint_manager = checkpoint_manager or CoordinationCheckpointManager(
            event_queue,
            state_manager,
            metrics_manager
        )
        
        # Store active nested executions
        self._active_executions: Dict[str, Dict[str, Any]] = {}
        
        # Execution history for result aggregation
        self._execution_history: Dict[str, List[Dict[str, Any]]] = {}
        
        logger.info("NestedPhaseCoordinator initialized")
    
    async def initiate_nested_phase(self,
                                  parent_phase_id: str,
                                  target_phase_type: PhaseType,
                                  input_data: Dict[str, Any],
                                  config: Dict[str, Any],
                                  execution_id: Optional[str] = None,
                                  checkpoint_before: bool = True,
                                  checkpoint_after: bool = True,
                                  timeout_seconds: Optional[int] = None,
                                  context_extensions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Initiate a nested phase execution with comprehensive configuration.
        
        Args:
            parent_phase_id: ID of the parent phase
            target_phase_type: Target phase type to execute
            input_data: Input data for the target phase
            config: Configuration for the target phase
            execution_id: Optional execution ID (generated if not provided)
            checkpoint_before: Whether to create checkpoint before execution
            checkpoint_after: Whether to create checkpoint after execution
            timeout_seconds: Optional timeout in seconds
            context_extensions: Optional context extensions to propagate
            
        Returns:
            Dictionary with execution result and metadata
        """
        # Generate execution ID if not provided
        if not execution_id:
            execution_id = f"nested_exec_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"
        
        # Record execution start
        await self._metrics_manager.record_metric(
            "phase_two:nested_execution:initiated",
            1.0,
            metadata={
                "parent_phase_id": parent_phase_id,
                "target_phase_type": target_phase_type.value,
                "execution_id": execution_id,
                "checkpoint_before": checkpoint_before,
                "checkpoint_after": checkpoint_after
            }
        )
        
        # Store execution info
        self._active_executions[execution_id] = {
            "parent_phase_id": parent_phase_id,
            "target_phase_type": target_phase_type.value,
            "start_time": datetime.now().isoformat(),
            "status": "initiated",
            "checkpoints": {}
        }
        
        # Initialize execution history for this execution
        self._execution_history[execution_id] = []
        
        # Create checkpoint before execution if requested
        checkpoint_id_before = None
        if checkpoint_before:
            try:
                checkpoint_id_before = await self._checkpoint_manager.create_checkpoint(
                    parent_phase_id,
                    "pre_nested_execution",
                    {
                        "execution_id": execution_id,
                        "input_data": input_data,
                        "config": config,
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                self._active_executions[execution_id]["checkpoints"]["before"] = checkpoint_id_before
                logger.info(f"Created pre-execution checkpoint {checkpoint_id_before} for {execution_id}")
            except Exception as e:
                logger.error(f"Failed to create pre-execution checkpoint for {execution_id}: {str(e)}")
        
        # Extend input data with context if provided
        enhanced_input = input_data.copy()
        if context_extensions:
            enhanced_input["context_extensions"] = context_extensions
        
        # Add execution metadata
        enhanced_input["execution_metadata"] = {
            "execution_id": execution_id,
            "parent_phase_id": parent_phase_id,
            "initiated_at": datetime.now().isoformat(),
            "checkpoint_id_before": checkpoint_id_before
        }
        
        # Execute the nested phase
        try:
            # Record execution attempt
            self._record_execution_event(execution_id, "execution_started", {
                "parent_phase_id": parent_phase_id,
                "target_phase_type": target_phase_type.value,
                "timestamp": datetime.now().isoformat()
            })
            
            # Update status
            self._active_executions[execution_id]["status"] = "executing"
            
            # Call the coordination method
            result = await self._phase_coordination.coordinate_nested_execution(
                parent_phase_id,
                target_phase_type,
                enhanced_input,
                config,
                timeout_seconds=timeout_seconds
            )
            
            # Record execution completion
            self._record_execution_event(execution_id, "execution_completed", {
                "timestamp": datetime.now().isoformat(),
                "status": "success" if "error" not in result else "error"
            })
            
            # Update execution info
            self._active_executions[execution_id].update({
                "status": "completed" if "error" not in result else "error",
                "end_time": datetime.now().isoformat(),
                "result_summary": {
                    "success": "error" not in result,
                    "error": result.get("error", None)
                }
            })
            
            # Create checkpoint after execution if requested
            checkpoint_id_after = None
            if checkpoint_after and "error" not in result:
                try:
                    # Create checkpoint after successful execution
                    checkpoint_id_after = await self._checkpoint_manager.create_checkpoint(
                        parent_phase_id,
                        "post_nested_execution",
                        {
                            "execution_id": execution_id,
                            "result": result,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                    
                    self._active_executions[execution_id]["checkpoints"]["after"] = checkpoint_id_after
                    logger.info(f"Created post-execution checkpoint {checkpoint_id_after} for {execution_id}")
                except Exception as e:
                    logger.error(f"Failed to create post-execution checkpoint for {execution_id}: {str(e)}")
            
            # Add checkpoint info to result
            result["execution_metadata"] = {
                "execution_id": execution_id,
                "checkpoints": {
                    "before": checkpoint_id_before,
                    "after": checkpoint_id_after
                }
            }
            
            # Record execution metric
            await self._metrics_manager.record_metric(
                "phase_two:nested_execution:completed",
                1.0,
                metadata={
                    "parent_phase_id": parent_phase_id,
                    "target_phase_type": target_phase_type.value,
                    "execution_id": execution_id,
                    "success": "error" not in result,
                    "duration_ms": (datetime.now() - datetime.fromisoformat(
                        self._active_executions[execution_id]["start_time"])).total_seconds() * 1000
                }
            )
            
            # Emit execution completed event
            await self._event_queue.emit(
                ResourceEventTypes.PHASE_COORDINATION_EVENT.value,
                {
                    "event_type": "nested_execution_completed",
                    "parent_phase_id": parent_phase_id,
                    "target_phase_type": target_phase_type.value,
                    "execution_id": execution_id,
                    "success": "error" not in result,
                    "checkpoints": {
                        "before": checkpoint_id_before,
                        "after": checkpoint_id_after
                    }
                }
            )
            
            return result
            
        except Exception as e:
            # Record execution failure
            self._record_execution_event(execution_id, "execution_failed", {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "error_type": str(type(e).__name__)
            })
            
            # Update execution info
            self._active_executions[execution_id].update({
                "status": "failed",
                "end_time": datetime.now().isoformat(),
                "error": str(e),
                "error_type": str(type(e).__name__)
            })
            
            # Record execution metric
            await self._metrics_manager.record_metric(
                "phase_two:nested_execution:failed",
                1.0,
                metadata={
                    "parent_phase_id": parent_phase_id,
                    "target_phase_type": target_phase_type.value,
                    "execution_id": execution_id,
                    "error": str(e),
                    "duration_ms": (datetime.now() - datetime.fromisoformat(
                        self._active_executions[execution_id]["start_time"])).total_seconds() * 1000
                }
            )
            
            # Emit execution failed event
            await self._event_queue.emit(
                ResourceEventTypes.PHASE_COORDINATION_EVENT.value,
                {
                    "event_type": "nested_execution_failed",
                    "parent_phase_id": parent_phase_id,
                    "target_phase_type": target_phase_type.value,
                    "execution_id": execution_id,
                    "error": str(e),
                    "error_type": str(type(e).__name__),
                    "checkpoint_before": checkpoint_id_before
                }
            )
            
            # Return error result
            return {
                "error": f"Nested execution failed: {str(e)}",
                "execution_metadata": {
                    "execution_id": execution_id,
                    "checkpoints": {
                        "before": checkpoint_id_before
                    }
                }
            }
    
    async def restore_from_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """
        Restore state from a previously created checkpoint.
        
        Args:
            checkpoint_id: ID of the checkpoint to restore
            
        Returns:
            Dictionary with restoration result
        """
        try:
            # Restore the checkpoint
            checkpoint_data = await self._checkpoint_manager.restore_checkpoint(checkpoint_id)
            
            if not checkpoint_data:
                return {
                    "success": False,
                    "error": f"Checkpoint {checkpoint_id} not found"
                }
            
            # Record metric
            await self._metrics_manager.record_metric(
                "phase_two:nested_execution:checkpoint_restored",
                1.0,
                metadata={
                    "checkpoint_id": checkpoint_id,
                    "checkpoint_type": checkpoint_data.get("type", "unknown"),
                    "execution_id": checkpoint_data.get("metadata", {}).get("execution_id", "unknown")
                }
            )
            
            # Return success with checkpoint data
            return {
                "success": True,
                "checkpoint_id": checkpoint_id,
                "checkpoint_data": checkpoint_data,
                "restored_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to restore checkpoint {checkpoint_id}: {str(e)}")
            
            # Record metric
            await self._metrics_manager.record_metric(
                "phase_two:nested_execution:checkpoint_restore_failed",
                1.0,
                metadata={
                    "checkpoint_id": checkpoint_id,
                    "error": str(e)
                }
            )
            
            return {
                "success": False,
                "error": f"Failed to restore checkpoint: {str(e)}",
                "checkpoint_id": checkpoint_id
            }
    
    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """
        Get the status of a nested execution.
        
        Args:
            execution_id: ID of the execution
            
        Returns:
            Dictionary with execution status
        """
        # Check if execution exists
        if execution_id not in self._active_executions:
            return {
                "found": False,
                "execution_id": execution_id,
                "message": f"Execution {execution_id} not found"
            }
        
        # Get execution info
        execution_info = self._active_executions[execution_id]
        
        # Get execution history
        execution_history = self._execution_history.get(execution_id, [])
        
        # Calculate duration if execution has ended
        duration_ms = None
        if "end_time" in execution_info:
            duration_ms = (datetime.fromisoformat(execution_info["end_time"]) - 
                          datetime.fromisoformat(execution_info["start_time"])).total_seconds() * 1000
        
        # Construct status response
        status = {
            "found": True,
            "execution_id": execution_id,
            "parent_phase_id": execution_info["parent_phase_id"],
            "target_phase_type": execution_info["target_phase_type"],
            "status": execution_info["status"],
            "start_time": execution_info["start_time"],
            "checkpoints": execution_info.get("checkpoints", {}),
            "history": execution_history
        }
        
        # Add end time and duration if available
        if "end_time" in execution_info:
            status["end_time"] = execution_info["end_time"]
            status["duration_ms"] = duration_ms
        
        # Add result summary if available
        if "result_summary" in execution_info:
            status["result_summary"] = execution_info["result_summary"]
        
        # Add error info if execution failed
        if "error" in execution_info:
            status["error"] = execution_info["error"]
            status["error_type"] = execution_info.get("error_type")
        
        return status
    
    async def aggregate_execution_results(self, execution_ids: List[str]) -> Dict[str, Any]:
        """
        Aggregate results from multiple nested executions.
        
        Args:
            execution_ids: List of execution IDs to aggregate
            
        Returns:
            Dictionary with aggregated results
        """
        results = []
        successful = []
        failed = []
        
        # Collect results for each execution
        for execution_id in execution_ids:
            status = await self.get_execution_status(execution_id)
            
            if status["found"]:
                if status["status"] == "completed":
                    successful.append(execution_id)
                elif status["status"] in ["failed", "error"]:
                    failed.append(execution_id)
                
                results.append(status)
        
        # Calculate success rate
        total = len(execution_ids)
        success_rate = len(successful) / total if total > 0 else 0
        
        # Construct aggregated result
        aggregated = {
            "total_executions": total,
            "successful_executions": len(successful),
            "failed_executions": len(failed),
            "success_rate": success_rate,
            "executions": results,
            "aggregated_at": datetime.now().isoformat()
        }
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:nested_execution:aggregated",
            success_rate,
            metadata={
                "total_executions": total,
                "successful_executions": len(successful),
                "failed_executions": len(failed)
            }
        )
        
        return aggregated
    
    async def get_active_executions(self) -> Dict[str, Any]:
        """
        Get information about all active executions.
        
        Returns:
            Dictionary with active executions information
        """
        # Collect active executions (those without end_time)
        active = {
            execution_id: info
            for execution_id, info in self._active_executions.items()
            if "end_time" not in info
        }
        
        # Collect all completed executions (those with end_time)
        completed = {
            execution_id: info
            for execution_id, info in self._active_executions.items()
            if "end_time" in info
        }
        
        return {
            "active_count": len(active),
            "completed_count": len(completed),
            "active_executions": active,
            "timestamp": datetime.now().isoformat()
        }
    
    def _record_execution_event(self, execution_id: str, event_type: str, data: Dict[str, Any]):
        """
        Record an event in the execution history.
        
        Args:
            execution_id: ID of the execution
            event_type: Type of event
            data: Event data
        """
        if execution_id not in self._execution_history:
            self._execution_history[execution_id] = []
        
        # Add event to history
        self._execution_history[execution_id].append({
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            **data
        })