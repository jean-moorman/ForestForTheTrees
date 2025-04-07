"""
Recovery Integration Module for FFTT

Integrates error recovery with phase coordination and system monitoring to provide
comprehensive error management across the system.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple, Callable, Awaitable

from resources.error_traceback import ErrorTracebackManager
from resources.error_recovery import ErrorRecoverySystem
from resources.errors import ErrorClassification, ResourceError, ErrorSeverity
# PhaseCoordinator will be imported dynamically to avoid circular imports

logger = logging.getLogger(__name__)

class SystemRecoveryManager:
    """
    Integrates phase coordination with error recovery.
    
    This manager serves as the central coordination point for error handling
    and system recovery, connecting phase management, error traceback, and
    the recovery system.
    """
    def __init__(self, event_queue, state_manager=None, system_monitor=None):
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._system_monitor = system_monitor
        
        # Initialize core components
        self._traceback_manager = ErrorTracebackManager(event_queue)
        
        # Import managers as needed
        from resources.managers import AgentContextManager, CacheManager, MetricsManager
        from system_error_recovery import ErrorHandler
        
        # Create required managers if not provided
        context_manager = AgentContextManager(event_queue, state_manager) if state_manager else None
        cache_manager = CacheManager(event_queue) if event_queue else None
        metrics_manager = MetricsManager(event_queue) if event_queue else None
        error_handler = ErrorHandler(event_queue) if event_queue else None
        
        # Dynamically import PhaseCoordinator to avoid circular imports
        try:
            # Postpone the import until needed
            from resources.phase_coordinator import PhaseCoordinator
            
            # Initialize phase coordinator with all required parameters
            self._phase_coordinator = PhaseCoordinator(
                event_queue=event_queue,
                state_manager=state_manager,
                context_manager=context_manager,
                cache_manager=cache_manager,
                metrics_manager=metrics_manager,
                error_handler=error_handler
            )
        except ImportError as e:
            logger.warning(f"Could not import PhaseCoordinator: {e}")
            self._phase_coordinator = None
        
        self._recovery_system = ErrorRecoverySystem(
            event_queue, 
            self._traceback_manager, 
            system_monitor, 
            self._phase_coordinator
        )
        
        # Status tracking
        self._running = False
        self._system_health_task = None
        self._health_check_interval = 300  # 5 minutes
        
        # Recovery metrics
        self._recovery_metrics = {
            "total_errors": 0,
            "recovered_errors": 0,
            "failed_recoveries": 0,
            "manual_interventions": 0,
            "phase_rollbacks": 0,
            "circuit_breaker_trips": 0
        }
        
        # List of active error ids being handled
        self._active_errors: Set[str] = set()
        
        # Integration hooks for application
        self._pre_recovery_hooks: List[Callable[[], Awaitable[None]]] = []
        self._post_recovery_hooks: List[Callable[[], Awaitable[None]]] = []
    
    async def start(self):
        """Start the recovery manager and all subsystems"""
        if self._running:
            return
            
        self._running = True
        
        # Start the subsystems
        await self._traceback_manager.start()
        if self._phase_coordinator:
            await self._phase_coordinator.start()
        await self._recovery_system.start()
        
        # Subscribe to events
        if self._event_queue:
            await self._event_queue.subscribe("error_occurred", self._handle_error)
            await self._event_queue.subscribe("recovery_plan_completed", self._handle_recovery_completed)
            await self._event_queue.subscribe("manual_intervention_required", self._handle_manual_intervention)
            await self._event_queue.subscribe("circuit_breaker_triggered", self._handle_circuit_breaker)
            await self._event_queue.subscribe("phase_transition", self._handle_phase_transition)
        
        # Start health check task
        loop = asyncio.get_event_loop()
        self._system_health_task = loop.create_task(self._system_health_check())
        
        logger.info("System recovery manager started")
    
    async def stop(self):
        """Stop the recovery manager and all subsystems"""
        if not self._running:
            return
            
        self._running = False
        
        # Unsubscribe from events
        if self._event_queue:
            await self._event_queue.unsubscribe("error_occurred", self._handle_error)
            await self._event_queue.unsubscribe("recovery_plan_completed", self._handle_recovery_completed)
            await self._event_queue.unsubscribe("manual_intervention_required", self._handle_manual_intervention)
            await self._event_queue.unsubscribe("circuit_breaker_triggered", self._handle_circuit_breaker)
            await self._event_queue.unsubscribe("phase_transition", self._handle_phase_transition)
        
        # Stop health check task
        if self._system_health_task and not self._system_health_task.done():
            self._system_health_task.cancel()
            try:
                await self._system_health_task
            except asyncio.CancelledError:
                pass
        
        # Stop the subsystems
        await self._recovery_system.stop()
        if self._phase_coordinator:
            await self._phase_coordinator.stop()
        await self._traceback_manager.stop()
        
        logger.info("System recovery manager stopped")
    
    async def handle_operation_error(self, 
                                  error: Exception, 
                                  operation: str, 
                                  component_id: str,
                                  cleanup_callback: Optional[Callable[[bool], Awaitable[None]]] = None) -> ErrorClassification:
        """
        Primary interface for handling errors, with integrated recovery.
        
        Args:
            error: The error that occurred
            operation: The operation that was being performed
            component_id: The ID of the component that encountered the error
            cleanup_callback: Optional callback function for resource cleanup
            
        Returns:
            ErrorClassification: The classification of the error
        """
        # Track total errors
        self._recovery_metrics["total_errors"] += 1
        
        # Run pre-recovery hooks if any
        for hook in self._pre_recovery_hooks:
            try:
                await hook()
            except Exception as e:
                logger.error(f"Error in pre-recovery hook: {e}", exc_info=True)
        
        # Let the recovery system handle the error
        classification = await self._recovery_system.handle_operation_error(
            error, operation, component_id, cleanup_callback
        )
        
        # Track error ID if it has one
        if hasattr(classification, 'context') and classification.context.get('error_id'):
            self._active_errors.add(classification.context['error_id'])
        
        # Run post-recovery hooks if any
        for hook in self._post_recovery_hooks:
            try:
                await hook()
            except Exception as e:
                logger.error(f"Error in post-recovery hook: {e}", exc_info=True)
        
        return classification
    
    async def register_pre_recovery_hook(self, hook: Callable[[], Awaitable[None]]):
        """Register a hook to run before recovery"""
        self._pre_recovery_hooks.append(hook)
    
    async def register_post_recovery_hook(self, hook: Callable[[], Awaitable[None]]):
        """Register a hook to run after recovery"""
        self._post_recovery_hooks.append(hook)
    
    async def _handle_error(self, event_data: Dict[str, Any]):
        """Process error events"""
        error_id = event_data.get("error_id")
        if error_id:
            self._active_errors.add(error_id)
    
    async def _handle_recovery_completed(self, event_data: Dict[str, Any]):
        """Process recovery completion events"""
        # Track recovered errors
        self._recovery_metrics["recovered_errors"] += 1
        
        # Remove from active errors
        for error_id in event_data.get("error_ids", []):
            if error_id in self._active_errors:
                self._active_errors.remove(error_id)
    
    async def _handle_manual_intervention(self, event_data: Dict[str, Any]):
        """Track manual intervention events"""
        self._recovery_metrics["manual_interventions"] += 1
    
    async def _handle_circuit_breaker(self, event_data: Dict[str, Any]):
        """Track circuit breaker events"""
        self._recovery_metrics["circuit_breaker_trips"] += 1
    
    async def _handle_phase_transition(self, event_data: Dict[str, Any]):
        """Track phase transition events"""
        # Check if this was a rollback (phase going backwards)
        if "rollback" in event_data.get("transition_type", "").lower():
            self._recovery_metrics["phase_rollbacks"] += 1
    
    async def _system_health_check(self):
        """Periodic health check to ensure recovery is working properly"""
        while self._running:
            try:
                # Perform health check
                await self._check_system_health()
                
                # Wait for next interval
                await asyncio.sleep(self._health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in system health check: {e}", exc_info=True)
                await asyncio.sleep(60)  # Shorter interval on error
    
    async def _check_system_health(self):
        """Check overall system health"""
        try:
            # Compile health metrics
            health_metrics = {
                "timestamp": datetime.now().isoformat(),
                "active_errors": len(self._active_errors),
                "recovery_metrics": self._recovery_metrics,
                "subsystems": {
                    "traceback_manager": "active" if self._traceback_manager._running else "inactive",
                    "phase_coordinator": "active" if self._phase_coordinator and hasattr(self._phase_coordinator, '_running') and self._phase_coordinator._running else "inactive",
                    "recovery_system": "active" if self._recovery_system._running else "inactive"
                }
            }
            
            # Add phase information if available
            if self._phase_coordinator and hasattr(self._phase_coordinator, 'get_current_phase_info'):
                health_metrics["current_phase"] = await self._phase_coordinator.get_current_phase_info()
            
            # If too many active errors for too long, alert
            if len(self._active_errors) > 10:
                await self._event_queue.emit(
                    "system_health_alert",
                    {
                        "alert_type": "high_error_count",
                        "message": f"High number of active errors: {len(self._active_errors)}",
                        "severity": "WARNING",
                        "timestamp": datetime.now().isoformat(),
                        "metrics": health_metrics
                    }
                )
            
            # If recovery rate is concerning, alert
            if self._recovery_metrics["total_errors"] > 0:
                recovery_rate = self._recovery_metrics["recovered_errors"] / self._recovery_metrics["total_errors"]
                if recovery_rate < 0.5 and self._recovery_metrics["total_errors"] > 5:
                    await self._event_queue.emit(
                        "system_health_alert",
                        {
                            "alert_type": "low_recovery_rate",
                            "message": f"Low error recovery rate: {recovery_rate:.2f}",
                            "severity": "WARNING",
                            "timestamp": datetime.now().isoformat(),
                            "metrics": health_metrics
                        }
                    )
            
            # Emit health status for monitoring
            await self._event_queue.emit(
                "recovery_system_status",
                health_metrics
            )
            
        except Exception as e:
            logger.error(f"Error checking system health: {e}", exc_info=True)
    
    async def get_error_trace(self, error_id: str) -> Dict[str, Any]:
        """Get the full error trace for an error"""
        if self._traceback_manager:
            return await self._traceback_manager.get_error_trace(error_id)
        return {"error": "Traceback manager not available"}
    
    async def get_recovery_metrics(self) -> Dict[str, Any]:
        """Get current recovery metrics"""
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": self._recovery_metrics,
            "active_errors": len(self._active_errors),
            "status": "healthy" if self._running else "stopped"
        }
    
    async def retry_failed_recovery(self, error_id: str) -> bool:
        """
        Retry recovery for a specific error that previously failed.
        Returns success status.
        """
        if not self._recovery_system:
            return False
            
        if error_id not in self._active_errors:
            logger.warning(f"Attempted to retry recovery for unknown error: {error_id}")
            return False
        
        # Emit retry event
        await self._event_queue.emit(
            "retry_recovery_requested",
            {
                "error_id": error_id,
                "timestamp": datetime.now().isoformat(),
                "manual": True
            }
        )
        
        return True
    
    async def rollback_to_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Roll back the system to a specific checkpoint.
        Returns success status.
        """
        if not self._phase_coordinator or not hasattr(self._phase_coordinator, 'rollback_to_checkpoint'):
            return False
            
        try:
            return await self._phase_coordinator.rollback_to_checkpoint(checkpoint_id)
        except Exception as e:
            logger.error(f"Error rolling back to checkpoint {checkpoint_id}: {e}", exc_info=True)
            return False
    
    async def create_system_checkpoint(self, checkpoint_id: Optional[str] = None) -> str:
        """
        Create a new system checkpoint for potential rollback.
        Returns the checkpoint ID.
        """
        if not self._phase_coordinator or not hasattr(self._phase_coordinator, 'create_checkpoint'):
            return "checkpoint_creation_failed"
            
        try:
            if checkpoint_id:
                return await self._phase_coordinator.create_checkpoint(checkpoint_id)
            else:
                return await self._phase_coordinator.create_checkpoint(f"sys_checkpoint_{int(time.time())}")
        except Exception as e:
            logger.error(f"Error creating checkpoint: {e}", exc_info=True)
            return "checkpoint_creation_failed"
    
    async def apply_recovery_recommendation(self, error_id: str) -> Dict[str, Any]:
        """
        Get a recovery recommendation and apply it immediately.
        Returns the outcome of the recovery attempt.
        """
        try:
            # Get the error trace
            if not self._traceback_manager:
                return {"success": False, "reason": "Traceback manager not available"}
                
            error_trace = await self._traceback_manager.get_error_trace(error_id)
            if not error_trace or "error_info" not in error_trace:
                return {"success": False, "reason": "Error trace not available"}
            
            # Extract context info
            metadata = error_trace["error_info"].get("metadata", {})
            component_id = metadata.get("component_id", "unknown")
            error_type = metadata.get("error_type", "unknown")
            
            # Create context for recommendation
            error_context = {
                "error_id": error_id,
                "component_id": component_id,
                "error_type": error_type,
                "severity": metadata.get("severity", "UNKNOWN"),
                "timestamp": datetime.now().isoformat()
            }
            
            # Get recommendation
            recommendation = await self._recovery_system.get_recovery_recommendation(error_context)
            
            # Apply the recommendation
            recommended_action = recommendation.get("recommended_action")
            if not recommended_action:
                return {"success": False, "reason": "No recommendation available"}
            
            # Emit recovery event
            await self._event_queue.emit(
                "manual_recovery_requested",
                {
                    "error_id": error_id,
                    "component_id": component_id,
                    "strategy": recommended_action,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            return {
                "success": True,
                "recommended_action": recommended_action,
                "components": recommendation.get("required_components", []),
                "fallback": recommendation.get("fallback_action"),
                "context": recommendation.get("decision_context", {})
            }
            
        except Exception as e:
            logger.error(f"Error applying recovery recommendation: {e}", exc_info=True)
            return {"success": False, "reason": str(e)}
    
    async def analyze_error_patterns(self) -> Dict[str, Any]:
        """
        Analyze error patterns to identify system issues.
        Returns pattern analysis.
        """
        if not self._traceback_manager:
            return {"error": "Traceback manager not available"}
            
        try:
            return await self._traceback_manager.analyze_error_patterns()
        except Exception as e:
            logger.error(f"Error analyzing error patterns: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def visualize_error_network(self, error_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate visualization data for the error network.
        Optionally focused on a specific error.
        """
        if not self._traceback_manager:
            return {"error": "Traceback manager not available"}
            
        try:
            return await self._traceback_manager.visualize_error_graph(error_id)
        except Exception as e:
            logger.error(f"Error visualizing error network: {e}", exc_info=True)
            return {"error": str(e)}