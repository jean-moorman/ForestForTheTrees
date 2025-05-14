"""
Delegation Status Aggregator for Phase Two
---------------------------------------
Implements collection of status from multiple delegated tasks,
consolidated status reports, real-time status querying, and
alerts on delegation failures.
"""

import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, Set, Union
from datetime import datetime, timedelta
import time

from resources import (
    EventQueue,
    StateManager,
    MetricsManager,
    ResourceEventTypes
)

logger = logging.getLogger(__name__)

class DelegationStatusAggregator:
    """
    Aggregates status from delegated tasks to provide consolidated reporting.
    
    This class provides:
    1. Collection of status from multiple delegated tasks
    2. Generation of consolidated status reports
    3. Real-time status querying
    4. Alerts on delegation failures
    """
    
    def __init__(self,
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 metrics_manager: MetricsManager,
                 status_update_interval_seconds: int = 15,
                 alert_threshold_percent: float = 25.0):
        """
        Initialize the DelegationStatusAggregator.
        
        Args:
            event_queue: EventQueue for emitting events
            state_manager: StateManager for state persistence
            metrics_manager: MetricsManager for metrics recording
            status_update_interval_seconds: Interval between status updates in seconds
            alert_threshold_percent: Failure percentage threshold for alerts
        """
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._metrics_manager = metrics_manager
        self._status_update_interval = status_update_interval_seconds
        self._alert_threshold = alert_threshold_percent
        
        # Store delegation status
        # {delegation_id: status_dict}
        self._delegations: Dict[str, Dict[str, Any]] = {}
        
        # Store component status
        # {component_id: status_dict}
        self._components: Dict[str, Dict[str, Any]] = {}
        
        # Store task status
        # {task_id: status_dict}
        self._tasks: Dict[str, Dict[str, Any]] = {}
        
        # Store status update timestamps
        # {entity_id: last_update_timestamp}
        self._last_updates: Dict[str, float] = {}
        
        # Store active alerts
        # {alert_id: alert_dict}
        self._active_alerts: Dict[str, Dict[str, Any]] = {}
        
        # Background task for status aggregation
        self._aggregation_task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info(f"DelegationStatusAggregator initialized with update_interval={status_update_interval_seconds}s")
    
    async def start(self) -> None:
        """Start the status aggregator."""
        if self._running:
            return
        
        self._running = True
        
        # Start aggregation task
        self._aggregation_task = asyncio.create_task(self._status_aggregation_loop())
        
        # Register for delegation events
        await self._event_queue.subscribe(
            ResourceEventTypes.PHASE_COORDINATION_EVENT.value,
            self._handle_coordination_event
        )
        
        logger.info("DelegationStatusAggregator started")
    
    async def stop(self) -> None:
        """Stop the status aggregator."""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel aggregation task
        if self._aggregation_task:
            self._aggregation_task.cancel()
            try:
                await self._aggregation_task
            except asyncio.CancelledError:
                pass
        
        # Unregister event handler
        await self._event_queue.unsubscribe(
            ResourceEventTypes.PHASE_COORDINATION_EVENT.value,
            self._handle_coordination_event
        )
        
        logger.info("DelegationStatusAggregator stopped")
    
    async def register_delegation(self,
                                delegation_id: str,
                                component_id: str,
                                tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Register a delegation for status tracking.
        
        Args:
            delegation_id: ID of the delegation
            component_id: ID of the component being delegated
            tasks: List of tasks in the delegation
            
        Returns:
            Dictionary with registration result
        """
        # Check if delegation already exists
        if delegation_id in self._delegations:
            return {
                "success": False,
                "message": f"Delegation {delegation_id} already registered"
            }
        
        # Create task entries
        task_ids = []
        for task in tasks:
            task_id = task.get("id", f"task_{len(self._tasks)}")
            task_ids.append(task_id)
            
            # Store task
            self._tasks[task_id] = {
                "task_id": task_id,
                "delegation_id": delegation_id,
                "component_id": component_id,
                "status": "pending",
                "progress": 0.0,
                "definition": task,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        
        # Create delegation entry
        self._delegations[delegation_id] = {
            "delegation_id": delegation_id,
            "component_id": component_id,
            "status": "initiated",
            "progress": 0.0,
            "task_count": len(tasks),
            "task_ids": task_ids,
            "pending_tasks": task_ids.copy(),
            "in_progress_tasks": [],
            "completed_tasks": [],
            "failed_tasks": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Update component entry
        if component_id not in self._components:
            self._components[component_id] = {
                "component_id": component_id,
                "status": "pending",
                "progress": 0.0,
                "delegation_ids": [delegation_id],
                "task_count": len(tasks),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        else:
            # Update existing component
            self._components[component_id]["delegation_ids"].append(delegation_id)
            self._components[component_id]["task_count"] += len(tasks)
            self._components[component_id]["updated_at"] = datetime.now().isoformat()
        
        # Update last update timestamp
        now = time.time()
        self._last_updates[delegation_id] = now
        self._last_updates[component_id] = now
        for task_id in task_ids:
            self._last_updates[task_id] = now
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:status:delegation_registered",
            1.0,
            metadata={
                "delegation_id": delegation_id,
                "component_id": component_id,
                "task_count": len(tasks)
            }
        )
        
        logger.info(f"Registered delegation {delegation_id} for component {component_id} with {len(tasks)} tasks")
        
        return {
            "success": True,
            "delegation_id": delegation_id,
            "task_count": len(tasks)
        }
    
    async def update_task_status(self,
                               task_id: str,
                               status: str,
                               progress: float,
                               metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update the status of a task.
        
        Args:
            task_id: ID of the task
            status: New status ("pending", "in_progress", "completed", "failed")
            progress: Progress percentage (0-100)
            metadata: Optional additional metadata
            
        Returns:
            Dictionary with update result
        """
        # Check if task exists
        if task_id not in self._tasks:
            return {
                "success": False,
                "message": f"Task {task_id} not found"
            }
        
        # Get task info
        task = self._tasks[task_id]
        old_status = task["status"]
        
        # Update task status
        task["status"] = status
        task["progress"] = progress
        task["updated_at"] = datetime.now().isoformat()
        
        # Add metadata if provided
        if metadata:
            if "metadata" not in task:
                task["metadata"] = {}
            task["metadata"].update(metadata)
        
        # Get delegation and component IDs
        delegation_id = task["delegation_id"]
        component_id = task["component_id"]
        
        # Get delegation
        delegation = self._delegations.get(delegation_id)
        if delegation:
            # Update delegation task lists based on status change
            if old_status != status:
                # Remove from previous status list
                if old_status == "pending" and task_id in delegation["pending_tasks"]:
                    delegation["pending_tasks"].remove(task_id)
                elif old_status == "in_progress" and task_id in delegation["in_progress_tasks"]:
                    delegation["in_progress_tasks"].remove(task_id)
                elif old_status == "completed" and task_id in delegation["completed_tasks"]:
                    delegation["completed_tasks"].remove(task_id)
                elif old_status == "failed" and task_id in delegation["failed_tasks"]:
                    delegation["failed_tasks"].remove(task_id)
                
                # Add to new status list
                if status == "pending" and task_id not in delegation["pending_tasks"]:
                    delegation["pending_tasks"].append(task_id)
                elif status == "in_progress" and task_id not in delegation["in_progress_tasks"]:
                    delegation["in_progress_tasks"].append(task_id)
                elif status == "completed" and task_id not in delegation["completed_tasks"]:
                    delegation["completed_tasks"].append(task_id)
                elif status == "failed" and task_id not in delegation["failed_tasks"]:
                    delegation["failed_tasks"].append(task_id)
            
            # Update delegation status and progress
            await self._update_delegation_status(delegation_id)
        
        # Update last update timestamp
        now = time.time()
        self._last_updates[task_id] = now
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:status:task_updated",
            progress / 100.0,  # Normalize to 0-1
            metadata={
                "task_id": task_id,
                "delegation_id": delegation_id,
                "component_id": component_id,
                "status": status,
                "progress": progress
            }
        )
        
        # Check for alert conditions
        if status == "failed":
            await self._check_alert_conditions(delegation_id)
        
        return {
            "success": True,
            "task_id": task_id,
            "delegation_id": delegation_id
        }
    
    async def update_delegation_status(self,
                                     delegation_id: str,
                                     status: str,
                                     progress: float,
                                     metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update the status of a delegation.
        
        Args:
            delegation_id: ID of the delegation
            status: New status ("initiated", "in_progress", "completed", "failed", "partial")
            progress: Progress percentage (0-100)
            metadata: Optional additional metadata
            
        Returns:
            Dictionary with update result
        """
        # Check if delegation exists
        if delegation_id not in self._delegations:
            return {
                "success": False,
                "message": f"Delegation {delegation_id} not found"
            }
        
        # Get delegation info
        delegation = self._delegations[delegation_id]
        component_id = delegation["component_id"]
        
        # Update delegation status
        delegation["status"] = status
        delegation["progress"] = progress
        delegation["updated_at"] = datetime.now().isoformat()
        
        # Add metadata if provided
        if metadata:
            if "metadata" not in delegation:
                delegation["metadata"] = {}
            delegation["metadata"].update(metadata)
        
        # Update component status
        await self._update_component_status(component_id)
        
        # Update last update timestamp
        now = time.time()
        self._last_updates[delegation_id] = now
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:status:delegation_updated",
            progress / 100.0,  # Normalize to 0-1
            metadata={
                "delegation_id": delegation_id,
                "component_id": component_id,
                "status": status,
                "progress": progress
            }
        )
        
        # Check for alert conditions
        if status == "failed":
            await self._check_alert_conditions(delegation_id)
        
        return {
            "success": True,
            "delegation_id": delegation_id
        }
    
    async def update_component_status(self,
                                    component_id: str,
                                    status: str,
                                    progress: float,
                                    metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update the status of a component.
        
        Args:
            component_id: ID of the component
            status: New status ("pending", "in_progress", "completed", "failed", "partial")
            progress: Progress percentage (0-100)
            metadata: Optional additional metadata
            
        Returns:
            Dictionary with update result
        """
        # Check if component exists
        if component_id not in self._components:
            return {
                "success": False,
                "message": f"Component {component_id} not found"
            }
        
        # Get component info
        component = self._components[component_id]
        
        # Update component status
        component["status"] = status
        component["progress"] = progress
        component["updated_at"] = datetime.now().isoformat()
        
        # Add metadata if provided
        if metadata:
            if "metadata" not in component:
                component["metadata"] = {}
            component["metadata"].update(metadata)
        
        # Update last update timestamp
        now = time.time()
        self._last_updates[component_id] = now
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:status:component_updated",
            progress / 100.0,  # Normalize to 0-1
            metadata={
                "component_id": component_id,
                "status": status,
                "progress": progress
            }
        )
        
        return {
            "success": True,
            "component_id": component_id
        }
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Dictionary with task status
        """
        # Check if task exists
        if task_id not in self._tasks:
            return {
                "success": False,
                "message": f"Task {task_id} not found"
            }
        
        # Get task info
        task = self._tasks[task_id]
        
        return {
            "success": True,
            "task": task
        }
    
    async def get_delegation_status(self, delegation_id: str) -> Dict[str, Any]:
        """
        Get the status of a delegation.
        
        Args:
            delegation_id: ID of the delegation
            
        Returns:
            Dictionary with delegation status
        """
        # Check if delegation exists
        if delegation_id not in self._delegations:
            return {
                "success": False,
                "message": f"Delegation {delegation_id} not found"
            }
        
        # Get delegation info
        delegation = self._delegations[delegation_id]
        component_id = delegation["component_id"]
        
        # Get task details
        tasks = {}
        for task_id in delegation["task_ids"]:
            if task_id in self._tasks:
                tasks[task_id] = self._tasks[task_id]
        
        # Get active alerts for this delegation
        delegation_alerts = {}
        for alert_id, alert in self._active_alerts.items():
            if alert.get("delegation_id") == delegation_id:
                delegation_alerts[alert_id] = alert
        
        return {
            "success": True,
            "delegation": delegation,
            "component_id": component_id,
            "tasks": tasks,
            "alerts": delegation_alerts
        }
    
    async def get_component_status(self, component_id: str) -> Dict[str, Any]:
        """
        Get the status of a component.
        
        Args:
            component_id: ID of the component
            
        Returns:
            Dictionary with component status
        """
        # Check if component exists
        if component_id not in self._components:
            return {
                "success": False,
                "message": f"Component {component_id} not found"
            }
        
        # Get component info
        component = self._components[component_id]
        
        # Get delegation details
        delegations = {}
        for delegation_id in component["delegation_ids"]:
            if delegation_id in self._delegations:
                delegations[delegation_id] = self._delegations[delegation_id]
        
        # Get active alerts for this component
        component_alerts = {}
        for alert_id, alert in self._active_alerts.items():
            if alert.get("component_id") == component_id:
                component_alerts[alert_id] = alert
        
        return {
            "success": True,
            "component": component,
            "delegations": delegations,
            "alerts": component_alerts
        }
    
    async def get_consolidated_status(self) -> Dict[str, Any]:
        """
        Get consolidated status for all delegations.
        
        Returns:
            Dictionary with consolidated status
        """
        # Count tasks by status
        task_counts = {
            "total": len(self._tasks),
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "failed": 0
        }
        
        for task in self._tasks.values():
            status = task["status"]
            if status in task_counts:
                task_counts[status] += 1
        
        # Count delegations by status
        delegation_counts = {
            "total": len(self._delegations),
            "initiated": 0,
            "in_progress": 0,
            "completed": 0,
            "failed": 0,
            "partial": 0
        }
        
        for delegation in self._delegations.values():
            status = delegation["status"]
            if status in delegation_counts:
                delegation_counts[status] += 1
        
        # Count components by status
        component_counts = {
            "total": len(self._components),
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "failed": 0,
            "partial": 0
        }
        
        for component in self._components.values():
            status = component["status"]
            if status in component_counts:
                component_counts[status] += 1
        
        # Calculate overall progress
        total_task_progress = sum(task["progress"] for task in self._tasks.values())
        overall_task_progress = total_task_progress / len(self._tasks) if self._tasks else 0
        
        # Get alert counts
        alert_count = len(self._active_alerts)
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "task_counts": task_counts,
            "delegation_counts": delegation_counts,
            "component_counts": component_counts,
            "overall_progress": overall_task_progress,
            "alert_count": alert_count,
            "active_alerts": self._active_alerts
        }
    
    async def get_active_alerts(self) -> Dict[str, Any]:
        """
        Get all active alerts.
        
        Returns:
            Dictionary with active alerts
        """
        return {
            "success": True,
            "count": len(self._active_alerts),
            "alerts": self._active_alerts,
            "timestamp": datetime.now().isoformat()
        }
    
    async def acknowledge_alert(self, alert_id: str) -> Dict[str, Any]:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: ID of the alert to acknowledge
            
        Returns:
            Dictionary with acknowledgement result
        """
        # Check if alert exists
        if alert_id not in self._active_alerts:
            return {
                "success": False,
                "message": f"Alert {alert_id} not found"
            }
        
        # Get alert info
        alert = self._active_alerts[alert_id]
        
        # Update alert
        alert["acknowledged"] = True
        alert["acknowledged_at"] = datetime.now().isoformat()
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:status:alert_acknowledged",
            1.0,
            metadata={
                "alert_id": alert_id,
                "alert_type": alert["type"]
            }
        )
        
        return {
            "success": True,
            "alert_id": alert_id
        }
    
    async def resolve_alert(self, alert_id: str, resolution: str) -> Dict[str, Any]:
        """
        Resolve an alert.
        
        Args:
            alert_id: ID of the alert to resolve
            resolution: Resolution description
            
        Returns:
            Dictionary with resolution result
        """
        # Check if alert exists
        if alert_id not in self._active_alerts:
            return {
                "success": False,
                "message": f"Alert {alert_id} not found"
            }
        
        # Get alert info
        alert = self._active_alerts[alert_id]
        
        # Update alert
        alert["resolved"] = True
        alert["resolved_at"] = datetime.now().isoformat()
        alert["resolution"] = resolution
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:status:alert_resolved",
            1.0,
            metadata={
                "alert_id": alert_id,
                "alert_type": alert["type"]
            }
        )
        
        # Emit alert resolved event
        await self._event_queue.emit(
            ResourceEventTypes.PHASE_COORDINATION_EVENT.value,
            {
                "event_type": "delegation_alert_resolved",
                "alert_id": alert_id,
                "alert_type": alert["type"],
                "resolution": resolution,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Remove from active alerts
        del self._active_alerts[alert_id]
        
        return {
            "success": True,
            "alert_id": alert_id
        }
    
    async def _status_aggregation_loop(self) -> None:
        """Background task to aggregate status and check for alerts."""
        while self._running:
            try:
                # Aggregate delegation status
                await self._aggregate_all_status()
                
                # Wait for next update interval
                await asyncio.sleep(self._status_update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in status aggregation loop: {str(e)}")
                await asyncio.sleep(5)  # Short delay before retry
    
    async def _aggregate_all_status(self) -> None:
        """Aggregate status for all delegations."""
        # Aggregate delegation status
        for delegation_id in self._delegations:
            await self._update_delegation_status(delegation_id)
        
        # Aggregate component status
        for component_id in self._components:
            await self._update_component_status(component_id)
        
        # Generate consolidated report
        consolidated = await self.get_consolidated_status()
        
        # Emit status report event
        await self._event_queue.emit(
            ResourceEventTypes.PHASE_COORDINATION_EVENT.value,
            {
                "event_type": "delegation_status_report",
                "task_counts": consolidated["task_counts"],
                "delegation_counts": consolidated["delegation_counts"],
                "component_counts": consolidated["component_counts"],
                "overall_progress": consolidated["overall_progress"],
                "alert_count": consolidated["alert_count"],
                "timestamp": datetime.now().isoformat()
            }
        )
    
    async def _update_delegation_status(self, delegation_id: str) -> None:
        """
        Update the status and progress of a delegation based on its tasks.
        
        Args:
            delegation_id: ID of the delegation to update
        """
        # Get delegation info
        delegation = self._delegations.get(delegation_id)
        if not delegation:
            return
        
        # Get task counts
        total_tasks = delegation["task_count"]
        pending_count = len(delegation["pending_tasks"])
        in_progress_count = len(delegation["in_progress_tasks"])
        completed_count = len(delegation["completed_tasks"])
        failed_count = len(delegation["failed_tasks"])
        
        # Determine delegation status
        if failed_count == total_tasks:
            status = "failed"
        elif completed_count == total_tasks:
            status = "completed"
        elif completed_count > 0 or in_progress_count > 0:
            if failed_count > 0:
                status = "partial"
            else:
                status = "in_progress"
        else:
            status = "initiated"
        
        # Calculate progress
        progress = 0.0
        for task_id in delegation["task_ids"]:
            if task_id in self._tasks:
                progress += self._tasks[task_id]["progress"]
        
        # Average progress
        if total_tasks > 0:
            progress /= total_tasks
        
        # Update delegation
        delegation["status"] = status
        delegation["progress"] = progress
        delegation["updated_at"] = datetime.now().isoformat()
        
        # Update last update timestamp
        self._last_updates[delegation_id] = time.time()
    
    async def _update_component_status(self, component_id: str) -> None:
        """
        Update the status and progress of a component based on its delegations.
        
        Args:
            component_id: ID of the component to update
        """
        # Get component info
        component = self._components.get(component_id)
        if not component:
            return
        
        # Get delegation IDs for this component
        delegation_ids = component["delegation_ids"]
        
        # Count delegations by status
        status_counts = {
            "initiated": 0,
            "in_progress": 0,
            "completed": 0,
            "failed": 0,
            "partial": 0
        }
        
        # Calculate total progress
        total_progress = 0.0
        delegation_count = 0
        
        for delegation_id in delegation_ids:
            if delegation_id in self._delegations:
                delegation = self._delegations[delegation_id]
                status = delegation["status"]
                
                if status in status_counts:
                    status_counts[status] += 1
                
                total_progress += delegation["progress"]
                delegation_count += 1
        
        # Determine component status
        if status_counts["failed"] == delegation_count:
            status = "failed"
        elif status_counts["completed"] == delegation_count:
            status = "completed"
        elif status_counts["completed"] > 0 or status_counts["in_progress"] > 0:
            if status_counts["failed"] > 0 or status_counts["partial"] > 0:
                status = "partial"
            else:
                status = "in_progress"
        else:
            status = "pending"
        
        # Average progress
        progress = total_progress / delegation_count if delegation_count > 0 else 0.0
        
        # Update component
        component["status"] = status
        component["progress"] = progress
        component["updated_at"] = datetime.now().isoformat()
        
        # Update last update timestamp
        self._last_updates[component_id] = time.time()
    
    async def _check_alert_conditions(self, delegation_id: str) -> None:
        """
        Check for alert conditions for a delegation.
        
        Args:
            delegation_id: ID of the delegation to check
        """
        # Get delegation info
        delegation = self._delegations.get(delegation_id)
        if not delegation:
            return
        
        # Get component info
        component_id = delegation["component_id"]
        component = self._components.get(component_id)
        if not component:
            return
        
        # Calculate failure rate
        total_tasks = delegation["task_count"]
        failed_count = len(delegation["failed_tasks"])
        failure_rate = (failed_count / total_tasks) * 100 if total_tasks > 0 else 0
        
        # Check if failure rate exceeds threshold
        if failure_rate >= self._alert_threshold:
            # Create alert
            alert_id = f"alert_{delegation_id}_{int(time.time())}"
            
            alert = {
                "alert_id": alert_id,
                "type": "high_failure_rate",
                "delegation_id": delegation_id,
                "component_id": component_id,
                "failure_rate": failure_rate,
                "threshold": self._alert_threshold,
                "failed_count": failed_count,
                "total_count": total_tasks,
                "created_at": datetime.now().isoformat(),
                "acknowledged": False,
                "resolved": False
            }
            
            # Add to active alerts if not already alerting
            existing_alert = False
            for existing in self._active_alerts.values():
                if (existing["delegation_id"] == delegation_id and
                        existing["type"] == "high_failure_rate" and
                        not existing["resolved"]):
                    existing_alert = True
                    break
            
            if not existing_alert:
                self._active_alerts[alert_id] = alert
                
                # Emit alert event
                await self._event_queue.emit(
                    ResourceEventTypes.PHASE_COORDINATION_EVENT.value,
                    {
                        "event_type": "delegation_alert",
                        "alert_id": alert_id,
                        "alert_type": "high_failure_rate",
                        "delegation_id": delegation_id,
                        "component_id": component_id,
                        "failure_rate": failure_rate,
                        "threshold": self._alert_threshold,
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                # Record metric
                await self._metrics_manager.record_metric(
                    "phase_two:status:alert_raised",
                    failure_rate / 100.0,  # Normalize to 0-1
                    metadata={
                        "alert_id": alert_id,
                        "alert_type": "high_failure_rate",
                        "delegation_id": delegation_id,
                        "component_id": component_id,
                        "failure_rate": failure_rate
                    }
                )
                
                logger.warning(f"Alert: High failure rate ({failure_rate}%) for delegation {delegation_id}")
    
    async def _handle_coordination_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """
        Handle phase coordination events.
        
        Args:
            event_type: Type of event
            payload: Event payload
        """
        # Extract event type
        coord_event_type = payload.get("event_type", "")
        
        # Handle feature development events
        if coord_event_type == "feature_development_started":
            # Extract info
            operation_id = payload.get("operation_id", "")
            feature_id = payload.get("feature_id", "")
            
            # If this is a task we're tracking, update its status
            if feature_id in self._tasks:
                await self.update_task_status(
                    feature_id,
                    "in_progress",
                    0.0,
                    {"operation_id": operation_id}
                )
        
        elif coord_event_type == "feature_development_completed":
            # Extract info
            operation_id = payload.get("operation_id", "")
            feature_id = payload.get("feature_id", "")
            
            # If this is a task we're tracking, update its status
            if feature_id in self._tasks:
                await self.update_task_status(
                    feature_id,
                    "completed",
                    100.0,
                    {"operation_id": operation_id}
                )
        
        elif coord_event_type == "feature_development_failed":
            # Extract info
            operation_id = payload.get("operation_id", "")
            feature_id = payload.get("feature_id", "")
            error = payload.get("error", "Unknown error")
            
            # If this is a task we're tracking, update its status
            if feature_id in self._tasks:
                await self.update_task_status(
                    feature_id,
                    "failed",
                    0.0,
                    {
                        "operation_id": operation_id,
                        "error": error
                    }
                )