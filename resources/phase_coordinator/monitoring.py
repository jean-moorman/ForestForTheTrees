"""
Forest For The Trees (FFTT) Phase Coordination System - Monitoring
---------------------------------------------------
Handles phase monitoring, health checks, and metrics collection.
"""
import asyncio
import logging
from typing import Dict, Any, List, Set, Optional
from datetime import datetime

from resources.events import EventQueue, ResourceEventTypes
from resources.managers import MetricsManager
from resources.phase_coordinator.constants import PhaseState, PhaseType
from resources.phase_coordinator.models import PhaseContext, NestedPhaseExecution

logger = logging.getLogger(__name__)

class PhaseMonitor:
    """Monitors phases and collects metrics"""
    
    def __init__(self, 
                event_queue: EventQueue,
                metrics_manager: MetricsManager):
        """
        Initialize the phase monitor
        
        Args:
            event_queue: Event queue for sending events
            metrics_manager: Metrics manager for recording metrics
        """
        self._event_queue = event_queue
        self._metrics_manager = metrics_manager
        self._monitoring_task = None
        self._running = False
    
    async def start_monitoring(self, 
                              phase_states: Dict[str, PhaseContext], 
                              active_phases: Set[str],
                              nested_executions: Dict[str, NestedPhaseExecution]):
        """
        Start monitoring phases
        
        Args:
            phase_states: Dictionary of phase contexts
            active_phases: Set of active phase IDs
            nested_executions: Dictionary of nested executions
        """
        if self._running:
            return
            
        self._running = True
        
        # Start monitoring task
        loop = asyncio.get_event_loop()
        self._monitoring_task = loop.create_task(
            self._monitor_phases(phase_states, active_phases, nested_executions)
        )
        
        logger.info("Phase monitoring started")
    
    async def stop_monitoring(self):
        """Stop monitoring phases"""
        if not self._running:
            return
            
        self._running = False
        
        # Stop monitoring task if it exists
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass
                
        logger.info("Phase monitoring stopped")
    
    async def _monitor_phases(self, 
                             phase_states: Dict[str, PhaseContext], 
                             active_phases: Set[str],
                             nested_executions: Dict[str, NestedPhaseExecution]):
        """
        Monitor active phases and handle timeouts or stalls
        
        Args:
            phase_states: Dictionary of phase contexts
            active_phases: Set of active phase IDs
            nested_executions: Dictionary of nested executions
        """
        while self._running:
            try:
                # Check for stalled phases
                stalled_phases = self._check_for_stalled_phases(phase_states, active_phases)
                
                if stalled_phases:
                    for phase_id in stalled_phases:
                        logger.warning(f"Phase {phase_id} appears to be stalled")
                        
                        # Get phase type value safely
                        phase_type_value = "unknown"
                        if phase_id in phase_states:
                            context = phase_states[phase_id]
                            phase_type_value = (context.phase_type.value 
                                               if isinstance(context.phase_type, PhaseType) 
                                               else context.phase_type)
                        
                        # Record metric for stalled phase
                        await self._metrics_manager.record_metric(
                            "phase_coordinator:stalled_phase",
                            1.0,
                            metadata={
                                "phase_id": phase_id,
                                "stalled_since": datetime.now().isoformat(),
                                "phase_type": phase_type_value
                            }
                        )
                        
                        # Emit event for monitoring
                        await self._event_queue.emit(
                            ResourceEventTypes.RESOURCE_STATE_CHANGED.value,
                            {
                                "resource_id": f"phase:{phase_id}",
                                "state": "stalled",
                                "timestamp": datetime.now().isoformat()
                            }
                        )
                
                # Record metrics on current phase statistics
                await self._record_phase_metrics(phase_states, active_phases)
                
                # Check for orphaned nested executions
                await self._check_orphaned_executions(nested_executions)
                
                # Sleep before next check
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in phase monitoring: {str(e)}")
                await asyncio.sleep(10)  # Shorter sleep on error
    
    def _check_for_stalled_phases(self, 
                                 phase_states: Dict[str, PhaseContext], 
                                 active_phases: Set[str]) -> List[str]:
        """
        Check for phases that appear to be stalled.
        
        Args:
            phase_states: Dictionary of phase contexts
            active_phases: Set of active phase IDs
            
        Returns:
            List[str]: List of stalled phase IDs
        """
        stalled_phases = []
        now = datetime.now()
        
        for phase_id in active_phases:
            context = phase_states.get(phase_id)
            if not context or not context.start_time:
                continue
                
            # If phase has been running for more than 1 hour, consider it stalled
            running_time = (now - context.start_time).total_seconds()
            if running_time > 3600:  # 1 hour
                stalled_phases.append(phase_id)
                
        return stalled_phases
    
    async def _record_phase_metrics(self, 
                                  phase_states: Dict[str, PhaseContext], 
                                  active_phases: Set[str]):
        """
        Record metrics about current phase status for monitoring
        
        Args:
            phase_states: Dictionary of phase contexts
            active_phases: Set of active phase IDs
        """
        try:
            # Count phases by state
            state_counts = {}
            for state in PhaseState:
                state_counts[state.name] = 0
                
            for context in phase_states.values():
                state_counts[context.state.name] += 1
                
            # Count phases by type
            type_counts = {}
            for phase_type in PhaseType:
                type_counts[phase_type.value] = 0
                
            for context in phase_states.values():
                if isinstance(context.phase_type, PhaseType):
                    type_counts[context.phase_type.value] += 1
                
            # Record metrics for state counts
            for state, count in state_counts.items():
                await self._metrics_manager.record_metric(
                    f"phase_coordinator:phases_by_state:{state}",
                    count,
                    metadata={
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
            # Record metrics for type counts
            for phase_type, count in type_counts.items():
                await self._metrics_manager.record_metric(
                    f"phase_coordinator:phases_by_type:{phase_type}",
                    count,
                    metadata={
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
            # Record active phases count
            await self._metrics_manager.record_metric(
                "phase_coordinator:active_phases",
                len(active_phases),
                metadata={
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error recording phase metrics: {e}")
            # Log but don't re-raise to maintain stability
    
    async def _check_orphaned_executions(self, nested_executions: Dict[str, NestedPhaseExecution]):
        """
        Check for and clean up orphaned nested executions with progressive monitoring
        
        Args:
            nested_executions: Dictionary of nested executions
        """
        now = datetime.now()
        orphaned_executions = []
        warning_executions = []
        
        for exec_id, execution in nested_executions.items():
            if execution.status != "pending":
                continue
                
            # Record this health check
            execution.health_checks.append(now)
            
            # Calculate the execution time
            execution_time = (now - execution.start_time).total_seconds()
            
            # Get the effective timeout (use default if not set)
            timeout = execution.timeout_seconds if hasattr(execution, 'timeout_seconds') else 7200
            
            # Check if we need to time out this execution
            if execution_time > timeout:
                orphaned_executions.append(exec_id)
                continue
            
            # Progressive monitoring - increase frequency based on elapsed time percentage
            elapsed_percent = (execution_time / timeout) * 100
            
            # Define warning thresholds based on percentage of timeout
            if elapsed_percent > 75:  # >75% of timeout - critical warning
                # Check if there's been activity in the last 15 minutes
                if (not execution.last_activity or 
                    (now - execution.last_activity).total_seconds() > 900):  # 15 minutes
                    warning_executions.append((exec_id, "critical", elapsed_percent))
            elif elapsed_percent > 50:  # >50% of timeout - warning
                # Check if there's been activity in the last 30 minutes
                if (not execution.last_activity or 
                    (now - execution.last_activity).total_seconds() > 1800):  # 30 minutes
                    warning_executions.append((exec_id, "warning", elapsed_percent))
        
        # Handle warnings first
        for exec_id, level, percent in warning_executions:
            execution = nested_executions[exec_id]
            
            # Log warning
            if level == "critical":
                logger.warning(f"Execution nearing timeout ({percent:.1f}%): {exec_id} (parent: {execution.parent_id}, child: {execution.child_id})")
            else:
                logger.info(f"Long-running execution ({percent:.1f}%): {exec_id} (parent: {execution.parent_id}, child: {execution.child_id})")
            
            # Emit warning event
            await self._event_queue.emit(
                ResourceEventTypes.RESOURCE_ALERT_CREATED.value,
                {
                    "resource_id": f"nested_execution:{exec_id}",
                    "alert_type": "execution_warning",
                    "severity": level.upper(),
                    "message": f"Execution has been running for {percent:.1f}% of timeout",
                    "parent_phase": execution.parent_id,
                    "child_phase": execution.child_id,
                    "execution_time_seconds": (now - execution.start_time).total_seconds(),
                    "timeout_seconds": execution.timeout_seconds,
                    "timestamp": now.isoformat()
                }
            )
        
        # Clean up orphaned executions
        for exec_id in orphaned_executions:
            execution = nested_executions[exec_id]
            logger.warning(f"Cleaning up orphaned nested execution: {exec_id} (parent: {execution.parent_id}, child: {execution.child_id})")
            
            # Generate detailed timeout message with execution history
            timeout_message = (
                f"Execution orphaned - timed out after {execution.timeout_seconds//60} minutes. "
                f"Health checks: {len(execution.health_checks)}, "
                f"Progress updates: {len(execution.progress_updates)}"
            )
            
            # Mark as failed
            execution.status = "failed"
            execution.end_time = now
            execution.error = timeout_message
            
            # Emit detailed error event
            await self._event_queue.emit(
                ResourceEventTypes.RESOURCE_ERROR_OCCURRED.value,
                {
                    "resource_id": f"nested_execution:{exec_id}",
                    "error": timeout_message,
                    "error_type": "orphaned_execution",
                    "parent_phase": execution.parent_id,
                    "child_phase": execution.child_id,
                    "execution_details": {
                        "start_time": execution.start_time.isoformat(),
                        "end_time": now.isoformat(),
                        "duration_seconds": (now - execution.start_time).total_seconds(),
                        "health_checks": len(execution.health_checks),
                        "progress_updates": execution.progress_updates
                    },
                    "timestamp": now.isoformat()
                },
                priority="high"  # Use high priority for timeout errors
            )
    
    async def get_phase_health(self, 
                              phase_states: Dict[str, PhaseContext],
                              active_phases: Set[str],
                              circuit_breakers: Dict[str, Any],
                              transition_circuit_breaker: Any) -> Dict[str, Any]:
        """
        Get health status of all phases.
        
        Args:
            phase_states: Dictionary of phase contexts
            active_phases: Set of active phase IDs
            circuit_breakers: Dictionary of circuit breakers
            transition_circuit_breaker: Transition circuit breaker
            
        Returns:
            Dict[str, Any]: Health status information
        """
        # Count phases by state
        state_counts = {}
        for state in PhaseState:
            state_counts[state.name] = 0
            
        for context in phase_states.values():
            state_counts[context.state.name] += 1
            
        # Count phases by type
        type_counts = {}
        for phase_type in PhaseType:
            type_counts[phase_type.value] = 0
            
        for context in phase_states.values():
            if isinstance(context.phase_type, PhaseType):
                type_counts[context.phase_type.value] += 1
            
        # Calculate health status
        health_status = "HEALTHY"
        health_details = []
        
        # Check for failed phases
        if state_counts[PhaseState.FAILED.name] > 0:
            health_status = "CRITICAL"
            health_details.append(f"{state_counts[PhaseState.FAILED.name]} phases in FAILED state")
            
        # Check for aborted phases
        if state_counts[PhaseState.ABORTED.name] > 0:
            if health_status != "CRITICAL":
                health_status = "DEGRADED"
            health_details.append(f"{state_counts[PhaseState.ABORTED.name]} phases in ABORTED state")
            
        # Check for stalled phases
        stalled_phases = self._check_for_stalled_phases(phase_states, active_phases)
        if stalled_phases:
            if health_status == "HEALTHY":
                health_status = "WARNING"
            health_details.append(f"{len(stalled_phases)} phases appear to be stalled")
        
        # Check circuit breakers
        open_circuits = []
        for phase_type, circuit in circuit_breakers.items():
            if circuit.is_open():
                open_circuits.append(phase_type)
                
        if open_circuits:
            if health_status == "HEALTHY":
                health_status = "WARNING"
            health_details.append(f"Circuit breakers open for phases: {', '.join(open_circuits)}")
            
        # Check transition circuit breaker
        if transition_circuit_breaker.is_open():
            if health_status == "HEALTHY":
                health_status = "WARNING"
            health_details.append("Transition circuit breaker is open")
            
        return {
            "status": health_status,
            "description": "; ".join(health_details) if health_details else "All phases healthy",
            "state_counts": state_counts,
            "type_counts": type_counts,
            "active_phases": len(active_phases),
            "stalled_phases": len(stalled_phases),
            "open_circuits": open_circuits,
            "transition_circuit_open": transition_circuit_breaker.is_open(),
            "timestamp": datetime.now().isoformat()
        }