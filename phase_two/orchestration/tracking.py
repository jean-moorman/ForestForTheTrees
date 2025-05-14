"""
Component Build Tracker
====================

This module provides functionality for tracking component build progress,
generating reports, and calculating metrics.
"""

import logging
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
from enum import Enum, auto
from dataclasses import dataclass, field

from resources import (
    StateManager,
    MetricsManager,
    EventQueue,
    ResourceType
)

logger = logging.getLogger(__name__)

class BuildStage(Enum):
    """Build stages for component development."""
    NOT_STARTED = auto()
    VALIDATION = auto()
    PREPARATION = auto()
    FEATURE_EXTRACTION = auto()
    DELEGATION = auto()
    RESULT_COLLECTION = auto()
    INTEGRATION = auto()
    TESTING = auto()
    COMPLETION = auto()
    FAILED = auto()

@dataclass
class BuildStatus:
    """Status information for a component build."""
    component_id: str
    component_name: str
    stage: BuildStage = BuildStage.NOT_STARTED
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    dependencies: Set[str] = field(default_factory=set)
    is_critical_path: bool = False
    stage_history: List[Tuple[BuildStage, float]] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    
    def add_stage_transition(self, stage: BuildStage) -> None:
        """Add a stage transition to history."""
        self.stage_history.append((stage, time.time()))
        self.stage = stage
    
    def add_error(self, error: Dict[str, Any]) -> None:
        """Add an error."""
        self.errors.append({
            **error,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_duration(self) -> float:
        """Get the total duration of the build in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "component_id": self.component_id,
            "component_name": self.component_name,
            "stage": self.stage.name,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            "duration": self.get_duration(),
            "dependencies": list(self.dependencies),
            "is_critical_path": self.is_critical_path,
            "stage_history": [
                {
                    "stage": stage.name,
                    "timestamp": datetime.fromtimestamp(ts).isoformat()
                }
                for stage, ts in self.stage_history
            ],
            "error_count": len(self.errors),
            "has_errors": len(self.errors) > 0,
            "metrics": self.metrics,
            "has_results": bool(self.results)
        }

class ComponentBuildTracker:
    """
    Tracks component build progress and generates reports.
    
    Key responsibilities:
    1. Track component development progress
    2. Calculate overall phase progress metrics
    3. Generate progress reports
    4. Determine critical path for complex component relationships
    """
    
    def __init__(self, state_manager: StateManager, metrics_manager: MetricsManager, event_queue: EventQueue):
        """
        Initialize the ComponentBuildTracker.
        
        Args:
            state_manager: StateManager for state persistence
            metrics_manager: MetricsManager for metrics recording
            event_queue: EventQueue for event emission
        """
        self._state_manager = state_manager
        self._metrics_manager = metrics_manager
        self._event_queue = event_queue
        
        # Build status tracking
        self._build_statuses: Dict[str, BuildStatus] = {}
        
        # Critical path tracking
        self._critical_path: List[str] = []
        
        # Overall progress
        self._total_components = 0
        self._completed_components = 0
        self._failed_components = 0
        
        # Reporting task
        self._reporting_task: Optional[asyncio.Task] = None
        self._report_interval = 60  # seconds
        self._is_running = False
    
    async def initialize(self) -> None:
        """Initialize the build tracker."""
        self._is_running = True
        
        # Start reporting task
        self._reporting_task = asyncio.create_task(self._periodic_reporting())
        
        logger.info("ComponentBuildTracker initialized")
    
    async def start_component_processing(self, 
                                      component_id: str,
                                      component_name: str,
                                      dependencies: Optional[Set[str]] = None) -> None:
        """
        Start tracking component processing.
        
        Args:
            component_id: ID of the component
            component_name: Name of the component
            dependencies: Optional set of dependency component IDs
        """
        # Create build status
        status = BuildStatus(
            component_id=component_id,
            component_name=component_name,
            dependencies=dependencies or set(),
            stage=BuildStage.NOT_STARTED,
            start_time=time.time()
        )
        
        # Add initial stage transition
        status.add_stage_transition(BuildStage.NOT_STARTED)
        
        # Store in state
        self._build_statuses[component_id] = status
        
        # Increment total components
        self._total_components += 1
        
        # Recalculate critical path
        await self._calculate_critical_path()
        
        # Store in state manager
        await self._state_manager.set_state(
            f"component:build:{component_id}",
            status.to_dict(),
            ResourceType.STATE
        )
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:build:component_started",
            1.0,
            metadata={
                "component_id": component_id,
                "component_name": component_name,
                "dependency_count": len(dependencies or set())
            }
        )
        
        logger.info(f"Started build tracking for component {component_name} ({component_id})")
    
    async def update_component_stage(self, component_id: str, stage: str) -> None:
        """
        Update component build stage.
        
        Args:
            component_id: ID of the component
            stage: Name of the build stage
        """
        if component_id not in self._build_statuses:
            logger.warning(f"Cannot update stage for unknown component: {component_id}")
            return
        
        # Get status
        status = self._build_statuses[component_id]
        
        # Parse stage string to enum
        try:
            build_stage = BuildStage[stage]
        except (ValueError, KeyError):
            logger.warning(f"Invalid build stage: {stage}")
            return
        
        # Update stage
        status.add_stage_transition(build_stage)
        
        # Store in state manager
        await self._state_manager.set_state(
            f"component:build:{component_id}",
            status.to_dict(),
            ResourceType.STATE
        )
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:build:component_stage_change",
            1.0,
            metadata={
                "component_id": component_id,
                "component_name": status.component_name,
                "stage": stage
            }
        )
        
        logger.debug(f"Updated build stage for component {component_id} to {stage}")
    
    async def complete_component_processing(self, 
                                         component_id: str,
                                         success: bool,
                                         results: Optional[Dict[str, Any]] = None,
                                         errors: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        Complete component processing tracking.
        
        Args:
            component_id: ID of the component
            success: Whether the build was successful
            results: Optional build results
            errors: Optional errors that occurred
        """
        if component_id not in self._build_statuses:
            logger.warning(f"Cannot complete build for unknown component: {component_id}")
            return
        
        # Get status
        status = self._build_statuses[component_id]
        
        # Update end time
        status.end_time = time.time()
        
        # Update stage
        if success:
            status.add_stage_transition(BuildStage.COMPLETION)
            self._completed_components += 1
        else:
            status.add_stage_transition(BuildStage.FAILED)
            self._failed_components += 1
        
        # Store results if provided
        if results:
            status.results = results
        
        # Store errors if provided
        if errors:
            for error in errors:
                status.add_error(error)
        
        # Calculate metrics
        metrics = self._calculate_component_metrics(status)
        status.metrics = metrics
        
        # Store in state manager
        await self._state_manager.set_state(
            f"component:build:{component_id}",
            status.to_dict(),
            ResourceType.STATE
        )
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:build:component_completed",
            1.0,
            metadata={
                "component_id": component_id,
                "component_name": status.component_name,
                "success": success,
                "duration": status.get_duration(),
                "has_errors": bool(errors)
            }
        )
        
        # Update overall progress metrics
        await self._update_overall_progress()
        
        # Recalculate critical path
        await self._calculate_critical_path()
        
        logger.info(f"Completed build tracking for component {component_id} with success={success}")
    
    async def add_component_error(self, component_id: str, error: Dict[str, Any]) -> None:
        """
        Add an error to a component build.
        
        Args:
            component_id: ID of the component
            error: Error information
        """
        if component_id not in self._build_statuses:
            logger.warning(f"Cannot add error for unknown component: {component_id}")
            return
        
        # Get status
        status = self._build_statuses[component_id]
        
        # Add error
        status.add_error(error)
        
        # Store in state manager
        await self._state_manager.set_state(
            f"component:build:{component_id}",
            status.to_dict(),
            ResourceType.STATE
        )
        
        # Record metric
        await self._metrics_manager.record_metric(
            "phase_two:build:component_error",
            1.0,
            metadata={
                "component_id": component_id,
                "component_name": status.component_name,
                "error_type": error.get("error_type", "unknown"),
                "error_count": len(status.errors)
            }
        )
        
        logger.warning(f"Added error to component {component_id}: {error.get('message', 'Unknown error')}")
    
    async def _calculate_critical_path(self) -> None:
        """Calculate critical path through component dependencies."""
        # Only update if we have components
        if not self._build_statuses:
            return
        
        # Build dependency graph
        graph = {}
        for component_id, status in self._build_statuses.items():
            graph[component_id] = {
                "dependencies": status.dependencies,
                "duration": status.get_duration(),
                "is_completed": status.stage == BuildStage.COMPLETION,
                "is_failed": status.stage == BuildStage.FAILED
            }
        
        # Calculate earliest completion times
        earliest_completion = {}
        
        def get_earliest_completion(node):
            if node in earliest_completion:
                return earliest_completion[node]
            
            # If no dependencies, earliest completion is just the node duration
            dependencies = graph[node]["dependencies"]
            if not dependencies:
                completion_time = graph[node]["duration"]
            else:
                # Otherwise, it's the node duration plus the max of the dependencies
                dep_times = []
                for dep in dependencies:
                    if dep in graph:
                        dep_times.append(get_earliest_completion(dep))
                
                if dep_times:
                    completion_time = graph[node]["duration"] + max(dep_times)
                else:
                    completion_time = graph[node]["duration"]
            
            earliest_completion[node] = completion_time
            return completion_time
        
        # Calculate earliest completion for all nodes
        for node in graph:
            if graph[node]["is_completed"] or graph[node]["is_failed"]:
                continue
            get_earliest_completion(node)
        
        # Find the node with the latest completion time
        if not earliest_completion:
            return
            
        latest_node = max(earliest_completion, key=earliest_completion.get)
        
        # Trace back to find the critical path
        critical_path = [latest_node]
        current = latest_node
        
        while graph[current]["dependencies"]:
            # Find the dependency with the latest completion time
            deps = [d for d in graph[current]["dependencies"] if d in graph]
            if not deps:
                break
                
            next_node = max(deps, key=lambda d: earliest_completion.get(d, 0))
            critical_path.append(next_node)
            current = next_node
        
        # Reverse to get the path from start to end
        critical_path.reverse()
        
        # Update critical path status
        self._critical_path = critical_path
        
        # Update is_critical_path flag in build statuses
        for component_id in self._build_statuses:
            is_critical = component_id in critical_path
            self._build_statuses[component_id].is_critical_path = is_critical
        
        # Store critical path in state manager
        await self._state_manager.set_state(
            "phase_two:build:critical_path",
            {
                "path": critical_path,
                "estimated_completion_time": earliest_completion.get(latest_node, 0),
                "timestamp": datetime.now().isoformat()
            },
            ResourceType.STATE
        )
        
        logger.info(f"Calculated critical path: {' -> '.join(critical_path)}")
    
    def _calculate_component_metrics(self, status: BuildStatus) -> Dict[str, Any]:
        """
        Calculate metrics for a component build.
        
        Args:
            status: Build status
            
        Returns:
            Dictionary with metrics
        """
        # Calculate stage durations
        stage_durations = {}
        for i in range(1, len(status.stage_history)):
            prev_stage, prev_time = status.stage_history[i-1]
            curr_stage, curr_time = status.stage_history[i]
            
            duration = curr_time - prev_time
            stage_durations[prev_stage.name] = duration
        
        # Calculate other metrics
        return {
            "total_duration": status.get_duration(),
            "stage_durations": stage_durations,
            "stage_count": len(status.stage_history),
            "error_count": len(status.errors),
            "average_stage_duration": sum(stage_durations.values()) / len(stage_durations) if stage_durations else 0,
            "is_critical_path": status.is_critical_path
        }
    
    async def _update_overall_progress(self) -> None:
        """Update overall build progress metrics."""
        # Calculate completion percentage
        if self._total_components > 0:
            completion_percentage = (self._completed_components / self._total_components) * 100
        else:
            completion_percentage = 0
        
        # Count components in each stage
        stage_counts = {stage.name: 0 for stage in BuildStage}
        for status in self._build_statuses.values():
            stage_counts[status.stage.name] += 1
        
        # Calculate average build duration
        durations = [status.get_duration() for status in self._build_statuses.values() 
                    if status.end_time is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Store overall progress in state manager
        await self._state_manager.set_state(
            "phase_two:build:overall_progress",
            {
                "total_components": self._total_components,
                "completed_components": self._completed_components,
                "failed_components": self._failed_components,
                "completion_percentage": completion_percentage,
                "stage_counts": stage_counts,
                "average_build_duration": avg_duration,
                "critical_path": self._critical_path,
                "timestamp": datetime.now().isoformat()
            },
            ResourceType.STATE
        )
        
        # Record metrics
        await self._metrics_manager.record_metric(
            "phase_two:build:overall_progress",
            completion_percentage,
            metadata={
                "total_components": self._total_components,
                "completed_components": self._completed_components,
                "failed_components": self._failed_components
            }
        )
        
        logger.info(f"Updated overall build progress: {completion_percentage:.2f}% complete")
    
    async def _periodic_reporting(self) -> None:
        """Periodically generate and emit build reports."""
        while self._is_running:
            try:
                # Generate report
                report = await self.generate_build_report()
                
                # Emit report event
                await self._event_queue.emit(
                    "phase_two:build:report",
                    report
                )
                
                # Update overall progress metrics
                await self._update_overall_progress()
                
            except Exception as e:
                logger.error(f"Error in periodic reporting: {str(e)}")
            
            # Wait for next report interval
            await asyncio.sleep(self._report_interval)
    
    async def generate_build_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive build report.
        
        Returns:
            Dictionary with build report data
        """
        # Prepare component status reports
        component_reports = {}
        for component_id, status in self._build_statuses.items():
            component_reports[component_id] = status.to_dict()
        
        # Calculate overall metrics
        active_count = sum(1 for s in self._build_statuses.values() 
                          if s.stage != BuildStage.COMPLETION and s.stage != BuildStage.FAILED)
        pending_count = sum(1 for s in self._build_statuses.values() if s.stage == BuildStage.NOT_STARTED)
        
        # Calculate completion percentage
        if self._total_components > 0:
            completion_percentage = (self._completed_components / self._total_components) * 100
        else:
            completion_percentage = 0
        
        # Calculate estimated remaining time
        est_remaining_time = 0
        if active_count > 0 and self._completed_components > 0:
            # Use average completion time of finished components to estimate
            completed_durations = [s.get_duration() for s in self._build_statuses.values() 
                                 if s.stage == BuildStage.COMPLETION]
            if completed_durations:
                avg_duration = sum(completed_durations) / len(completed_durations)
                est_remaining_time = avg_duration * (self._total_components - self._completed_components - self._failed_components)
        
        # Calculate critical path components
        critical_path_components = []
        for component_id in self._critical_path:
            if component_id in self._build_statuses:
                critical_path_components.append({
                    "component_id": component_id,
                    "component_name": self._build_statuses[component_id].component_name,
                    "stage": self._build_statuses[component_id].stage.name,
                    "is_completed": self._build_statuses[component_id].stage == BuildStage.COMPLETION,
                    "is_failed": self._build_statuses[component_id].stage == BuildStage.FAILED
                })
        
        # Create report
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_components": self._total_components,
            "completed_components": self._completed_components,
            "failed_components": self._failed_components,
            "active_components": active_count,
            "pending_components": pending_count,
            "completion_percentage": completion_percentage,
            "estimated_remaining_time": est_remaining_time,
            "critical_path": critical_path_components,
            "component_details": component_reports
        }
        
        return report
    
    async def get_component_build_status(self, component_id: str) -> Optional[Dict[str, Any]]:
        """
        Get build status for a component.
        
        Args:
            component_id: ID of the component
            
        Returns:
            Dictionary with build status or None if not found
        """
        if component_id not in self._build_statuses:
            return None
            
        return self._build_statuses[component_id].to_dict()
    
    async def get_overall_progress(self) -> Dict[str, Any]:
        """
        Get overall build progress.
        
        Returns:
            Dictionary with overall progress
        """
        # Count components in each stage
        stage_counts = {stage.name: 0 for stage in BuildStage}
        for status in self._build_statuses.values():
            stage_counts[status.stage.name] += 1
        
        # Calculate completion percentage
        if self._total_components > 0:
            completion_percentage = (self._completed_components / self._total_components) * 100
        else:
            completion_percentage = 0
        
        # Get critical path
        critical_path_components = []
        for component_id in self._critical_path:
            if component_id in self._build_statuses:
                critical_path_components.append({
                    "component_id": component_id,
                    "component_name": self._build_statuses[component_id].component_name,
                    "stage": self._build_statuses[component_id].stage.name
                })
        
        return {
            "total_components": self._total_components,
            "completed_components": self._completed_components,
            "failed_components": self._failed_components,
            "completion_percentage": completion_percentage,
            "stage_counts": stage_counts,
            "critical_path": critical_path_components,
            "timestamp": datetime.now().isoformat()
        }
    
    async def shutdown(self) -> None:
        """Shutdown the build tracker."""
        self._is_running = False
        
        # Cancel reporting task
        if self._reporting_task and not self._reporting_task.done():
            self._reporting_task.cancel()
            try:
                await self._reporting_task
            except asyncio.CancelledError:
                pass
        
        logger.info("ComponentBuildTracker shutdown complete")