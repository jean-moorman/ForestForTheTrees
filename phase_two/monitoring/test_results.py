"""
Forest For The Trees (FFTT) System and Deployment Test Results Monitoring
-------------------------------------------------------------------------
This module integrates system and deployment test results with the component monitoring system.
It provides a unified view of test results and component health, allowing for comprehensive
monitoring of components throughout their lifecycle.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict

from phase_two.agents.agent_base import PhaseTwoAgentBase
from resources import (
    EventQueue, 
    StateManager, 
    AgentContextManager, 
    CacheManager, 
    MetricsManager, 
    ErrorHandler,
    MemoryMonitor,
    SystemMonitor,
    ResourceEventTypes
)

logger = logging.getLogger(__name__)

@dataclass
class ComponentTestStatus:
    """Component test status tracking."""
    component_id: str
    name: str
    latest_system_test: Optional[Dict[str, Any]] = None
    latest_deployment_test: Optional[Dict[str, Any]] = None
    system_test_history: List[Dict[str, Any]] = field(default_factory=list)
    deployment_test_history: List[Dict[str, Any]] = field(default_factory=list)
    last_system_test_time: Optional[datetime] = None
    last_deployment_test_time: Optional[datetime] = None
    test_success_rate: float = 1.0  # Default to 100% success
    
    def update_system_test(self, test_result: Dict[str, Any]) -> None:
        """Update with new system test result."""
        # Store timestamp
        test_time = datetime.now()
        self.last_system_test_time = test_time
        
        # Prepare test entry
        test_entry = {
            "timestamp": test_time.isoformat(),
            "status": "passed" if not test_result.get("failed_tests", 0) else "failed",
            "total_tests": test_result.get("total_tests", 0),
            "passed_tests": test_result.get("passed_tests", 0),
            "failed_tests": test_result.get("failed_tests", 0),
            "session_id": test_result.get("session_id", "")
        }
        
        # Update latest result
        self.latest_system_test = test_entry
        
        # Add to history (limited to last 10 entries)
        self.system_test_history.append(test_entry)
        if len(self.system_test_history) > 10:
            self.system_test_history = self.system_test_history[-10:]
            
        # Update success rate
        self._update_success_rate()
    
    def update_deployment_test(self, test_result: Dict[str, Any]) -> None:
        """Update with new deployment test result."""
        # Store timestamp
        test_time = datetime.now()
        self.last_deployment_test_time = test_time
        
        # Prepare test entry
        test_entry = {
            "timestamp": test_time.isoformat(),
            "status": "passed" if not test_result.get("failed_tests", 0) else "failed",
            "total_tests": test_result.get("total_tests", 0),
            "passed_tests": test_result.get("passed_tests", 0),
            "failed_tests": test_result.get("failed_tests", 0),
            "environment": test_result.get("environment_details", {}).get("name", "unknown"),
            "session_id": test_result.get("session_id", "")
        }
        
        # Update latest result
        self.latest_deployment_test = test_entry
        
        # Add to history (limited to last 10 entries)
        self.deployment_test_history.append(test_entry)
        if len(self.deployment_test_history) > 10:
            self.deployment_test_history = self.deployment_test_history[-10:]
            
        # Update success rate
        self._update_success_rate()
    
    def _update_success_rate(self) -> None:
        """Calculate overall test success rate."""
        total_tests = 0
        total_passed = 0
        
        # Count system tests
        for test in self.system_test_history:
            total_tests += test.get("total_tests", 0)
            total_passed += test.get("passed_tests", 0)
            
        # Count deployment tests
        for test in self.deployment_test_history:
            total_tests += test.get("total_tests", 0)
            total_passed += test.get("passed_tests", 0)
            
        # Calculate success rate (avoid division by zero)
        if total_tests > 0:
            self.test_success_rate = total_passed / total_tests
        else:
            self.test_success_rate = 1.0  # Default to 100% if no tests
    
    def get_health_status(self) -> str:
        """Determine component health status based on test results."""
        # If no tests have been run, consider it UNKNOWN
        if not self.last_system_test_time and not self.last_deployment_test_time:
            return "UNKNOWN"
            
        # If success rate is 100%, it's HEALTHY
        if self.test_success_rate >= 0.99:
            return "HEALTHY"
            
        # If success rate is 90-99%, it's WARNING
        if self.test_success_rate >= 0.9:
            return "WARNING"
            
        # If success rate is 70-90%, it's DEGRADED
        if self.test_success_rate >= 0.7:
            return "DEGRADED"
            
        # Below 70%, it's CRITICAL
        return "CRITICAL"


class TestResultsMonitor(PhaseTwoAgentBase):
    """
    Monitors system and deployment test results and integrates them
    with the component monitoring system.
    
    Responsibilities:
    - Listens for test completion events
    - Tracks test results for each component
    - Updates component health status based on test results
    - Provides APIs for querying component test status
    - Generates test result reports for components
    """
    
    def __init__(self,
                event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                memory_monitor: Optional[MemoryMonitor] = None,
                system_monitor: Optional[SystemMonitor] = None):
        """Initialize the test results monitor."""
        super().__init__(
            "test_results_monitor",
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor
        )
        
        # Component test status tracking
        self._component_test_status: Dict[str, ComponentTestStatus] = {}
        
        # For health integration
        self._system_monitor = system_monitor
        
        # Event subscription tasks
        self._event_tasks: List[asyncio.Task] = []
        self._running = False
        
        # Register event handlers
        self._event_handlers = {
            ResourceEventTypes.SYSTEM_TESTING_COMPLETED.value: self._handle_system_testing_completed,
            ResourceEventTypes.PHASE_TWO_DEPLOYMENT_COMPLETED.value: self._handle_deployment_testing_completed
        }
    
    async def start_monitoring(self) -> None:
        """Start monitoring test results."""
        if self._running:
            return
            
        self._running = True
        
        # Register with system monitor if available
        if self._system_monitor:
            await self._system_monitor.register_component("test_results_monitor", {
                "type": "monitor",
                "description": "Monitors component test results"
            })
        
        # Subscribe to relevant events
        for event_type in self._event_handlers.keys():
            self._event_tasks.append(
                asyncio.create_task(
                    self._event_queue.subscribe(
                        event_type, 
                        self._handle_event,
                        subscription_id=f"test_results_monitor_{event_type}"
                    )
                )
            )
        
        logger.info("Test results monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop monitoring test results."""
        if not self._running:
            return
            
        self._running = False
        
        # Cancel event subscription tasks
        for task in self._event_tasks:
            if not task.done():
                task.cancel()
                
        # Wait for tasks to complete
        if self._event_tasks:
            await asyncio.gather(*self._event_tasks, return_exceptions=True)
            
        self._event_tasks = []
        
        logger.info("Test results monitoring stopped")
    
    async def _handle_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Handle test result events."""
        try:
            # Get the appropriate handler for this event type
            handler = self._event_handlers.get(event_type)
            if handler:
                await handler(event_data)
            else:
                logger.warning(f"No handler for event type {event_type}")
        except Exception as e:
            logger.error(f"Error handling event {event_type}: {e}", exc_info=True)
    
    async def _handle_system_testing_completed(self, event_data: Dict[str, Any]) -> None:
        """Handle system testing completed event."""
        try:
            session_id = event_data.get("session_id")
            if not session_id:
                logger.warning("System testing completed event missing session_id")
                return
                
            # Get the testing session details
            session_state = await self._state_manager.get_state(f"system_testing:{session_id}")
            if not session_state:
                logger.warning(f"System testing session {session_id} not found")
                return
                
            # Get detailed test results
            from phase_two.testing.system.integration import SystemTestingOrchestrator
            orchestrator = SystemTestingOrchestrator(
                self._event_queue,
                self._state_manager,
                self._context_manager,
                self._cache_manager,
                self._metrics_manager,
                self._error_handler,
                self._memory_monitor,
                self._system_monitor
            )
            
            test_result = await orchestrator.get_testing_session(session_id)
            
            # Get the components involved
            components = test_result.get("components", [])
            if not components:
                # Try to get components from execution results
                execution_results = test_result.get("execution_results", {})
                components = execution_results.get("components", [])
                
            # Update each component's test status
            for component in components:
                component_id = component.get("id", "")
                component_name = component.get("name", "")
                
                if not component_id:
                    continue
                    
                # Get or create component test status
                if component_id not in self._component_test_status:
                    self._component_test_status[component_id] = ComponentTestStatus(
                        component_id=component_id,
                        name=component_name
                    )
                
                # Update with test results
                self._component_test_status[component_id].update_system_test(test_result)
                
                # Store in state manager
                await self._state_manager.set_state(
                    f"component_test_status:{component_id}",
                    asdict(self._component_test_status[component_id])
                )
                
                # Update component health
                await self._update_component_health(component_id)
                
            # Record metric
            await self._metrics_manager.record_metric(
                "component_testing:system_test_processed",
                1.0,
                metadata={
                    "session_id": session_id,
                    "component_count": len(components),
                    "timestamp": datetime.now().isoformat()
                }
            )
                
        except Exception as e:
            logger.error(f"Error processing system testing completed: {e}", exc_info=True)
    
    async def _handle_deployment_testing_completed(self, event_data: Dict[str, Any]) -> None:
        """Handle deployment testing completed event."""
        try:
            session_id = event_data.get("session_id")
            if not session_id:
                logger.warning("Deployment testing completed event missing session_id")
                return
                
            # Get the testing session details
            session_state = await self._state_manager.get_state(f"deployment_testing:{session_id}")
            if not session_state:
                logger.warning(f"Deployment testing session {session_id} not found")
                return
                
            # Get detailed test results
            from phase_two.testing.deployment.integration import DeploymentTestingOrchestrator
            orchestrator = DeploymentTestingOrchestrator(
                self._event_queue,
                self._state_manager,
                self._context_manager,
                self._cache_manager,
                self._metrics_manager,
                self._error_handler,
                self._memory_monitor,
                self._system_monitor
            )
            
            test_result = await orchestrator.get_testing_session(session_id)
            
            # Get the components involved
            components = test_result.get("components", [])
            if not components:
                # Try to get components from execution results
                execution_results = test_result.get("execution_results", {})
                components = execution_results.get("components", [])
                
            # Update each component's test status
            for component in components:
                component_id = component.get("id", "")
                component_name = component.get("name", "")
                
                if not component_id:
                    continue
                    
                # Get or create component test status
                if component_id not in self._component_test_status:
                    self._component_test_status[component_id] = ComponentTestStatus(
                        component_id=component_id,
                        name=component_name
                    )
                
                # Update with test results
                self._component_test_status[component_id].update_deployment_test(test_result)
                
                # Store in state manager
                await self._state_manager.set_state(
                    f"component_test_status:{component_id}",
                    asdict(self._component_test_status[component_id])
                )
                
                # Update component health
                await self._update_component_health(component_id)
                
            # Record metric
            await self._metrics_manager.record_metric(
                "component_testing:deployment_test_processed",
                1.0,
                metadata={
                    "session_id": session_id,
                    "component_count": len(components),
                    "timestamp": datetime.now().isoformat()
                }
            )
                
        except Exception as e:
            logger.error(f"Error processing deployment testing completed: {e}", exc_info=True)
    
    async def _update_component_health(self, component_id: str) -> None:
        """Update component health based on test results."""
        component_status = self._component_test_status.get(component_id)
        if not component_status:
            return
            
        # Get health status
        health_status = component_status.get_health_status()
        
        # Update health in system monitor if available
        if self._system_monitor and hasattr(self._system_monitor, "health_tracker"):
            component_name = component_status.name
            
            # Generate description based on status
            description = f"Component '{component_name}' test health: {health_status}"
            
            # Prepare metadata
            metadata = {
                "component_id": component_id,
                "component_name": component_name,
                "success_rate": component_status.test_success_rate,
                "last_system_test": component_status.last_system_test_time.isoformat() if component_status.last_system_test_time else None,
                "last_deployment_test": component_status.last_deployment_test_time.isoformat() if component_status.last_deployment_test_time else None,
                "system_test_status": component_status.latest_system_test.get("status") if component_status.latest_system_test else None,
                "deployment_test_status": component_status.latest_deployment_test.get("status") if component_status.latest_deployment_test else None
            }
            
            # Update component health
            await self._system_monitor.health_tracker.update_health(
                f"component_test_status_{component_id}",
                {
                    "status": health_status,
                    "source": "test_results_monitor",
                    "description": description,
                    "metadata": metadata
                }
            )
        
        # Emit component test status event
        await self._event_queue.emit(
            ResourceEventTypes.RESOURCE_HEALTH_CHANGED.value,
            {
                "resource_id": f"component:{component_id}",
                "health_source": "test_results",
                "status": health_status,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "success_rate": component_status.test_success_rate,
                    "system_test_status": component_status.latest_system_test.get("status") if component_status.latest_system_test else None,
                    "deployment_test_status": component_status.latest_deployment_test.get("status") if component_status.latest_deployment_test else None
                }
            }
        )
    
    async def get_component_test_status(self, component_id: str) -> Dict[str, Any]:
        """Get testing status for a component."""
        # Check in-memory cache first
        if component_id in self._component_test_status:
            return asdict(self._component_test_status[component_id])
        
        # Try to fetch from state manager
        state = await self._state_manager.get_state(f"component_test_status:{component_id}")
        if state:
            return state
        
        # Not found
        return {
            "component_id": component_id,
            "status": "not_found",
            "message": f"No test status found for component ID {component_id}"
        }
    
    async def get_all_component_test_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get testing status for all components."""
        result = {}
        
        # Include in-memory data
        for component_id, status in self._component_test_status.items():
            result[component_id] = asdict(status)
        
        # Check for any stored states not in memory
        state_prefix = "component_test_status:"
        all_states = await self._state_manager.list_states(state_prefix)
        
        for state_key in all_states:
            component_id = state_key.replace(state_prefix, "")
            if component_id not in result:
                state = await self._state_manager.get_state(state_key)
                if state:
                    result[component_id] = state
        
        return result
    
    async def generate_test_summary_report(self) -> Dict[str, Any]:
        """Generate a summary report of all component test statuses."""
        # Get all component statuses
        all_statuses = await self.get_all_component_test_statuses()
        
        # Aggregate test statistics
        total_components = len(all_statuses)
        status_counts = {"HEALTHY": 0, "WARNING": 0, "DEGRADED": 0, "CRITICAL": 0, "UNKNOWN": 0}
        total_system_tests = 0
        total_deployment_tests = 0
        total_passed_tests = 0
        total_failed_tests = 0
        
        # Calculate status for each component
        component_statuses = []
        for component_id, status_data in all_statuses.items():
            # Skip if not a proper status object
            if "name" not in status_data:
                continue
                
            # Calculate health status
            component_status = ComponentTestStatus(**status_data)
            health_status = component_status.get_health_status()
            status_counts[health_status] += 1
            
            # Count tests
            system_test_count = len(component_status.system_test_history)
            deployment_test_count = len(component_status.deployment_test_history)
            total_system_tests += system_test_count
            total_deployment_tests += deployment_test_count
            
            # Count results
            for test in component_status.system_test_history:
                total_passed_tests += test.get("passed_tests", 0)
                total_failed_tests += test.get("failed_tests", 0)
                
            for test in component_status.deployment_test_history:
                total_passed_tests += test.get("passed_tests", 0)
                total_failed_tests += test.get("failed_tests", 0)
            
            # Add to component statuses
            component_statuses.append({
                "component_id": component_id,
                "name": component_status.name,
                "health_status": health_status,
                "success_rate": component_status.test_success_rate,
                "system_tests": system_test_count,
                "deployment_tests": deployment_test_count,
                "last_test": (
                    max(
                        component_status.last_system_test_time or datetime.min,
                        component_status.last_deployment_test_time or datetime.min
                    ).isoformat() if (component_status.last_system_test_time or component_status.last_deployment_test_time) else None
                )
            })
        
        # Sort by health status (critical first, then by name)
        status_order = {"CRITICAL": 0, "DEGRADED": 1, "WARNING": 2, "HEALTHY": 3, "UNKNOWN": 4}
        component_statuses.sort(key=lambda x: (status_order.get(x["health_status"], 5), x["name"]))
        
        # Calculate overall health
        overall_health = "HEALTHY"
        if status_counts["CRITICAL"] > 0:
            overall_health = "CRITICAL"
        elif status_counts["DEGRADED"] > 0:
            overall_health = "DEGRADED"
        elif status_counts["WARNING"] > 0:
            overall_health = "WARNING"
        elif status_counts["UNKNOWN"] == total_components:
            overall_health = "UNKNOWN"
        
        # Generate report
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_health": overall_health,
            "total_components": total_components,
            "status_summary": status_counts,
            "test_summary": {
                "total_system_tests": total_system_tests,
                "total_deployment_tests": total_deployment_tests,
                "total_passed_tests": total_passed_tests,
                "total_failed_tests": total_failed_tests,
                "success_rate": total_passed_tests / (total_passed_tests + total_failed_tests) if (total_passed_tests + total_failed_tests) > 0 else 1.0
            },
            "components": component_statuses
        }
        
    async def get_component_test_details(self, component_id: str) -> Dict[str, Any]:
        """Get detailed test results for a component."""
        # Get component status
        component_status = await self.get_component_test_status(component_id)
        if component_status.get("status") == "not_found":
            return component_status
            
        # Get the most recent system and deployment test session IDs
        system_test_session_id = component_status.get("latest_system_test", {}).get("session_id")
        deployment_test_session_id = component_status.get("latest_deployment_test", {}).get("session_id")
        
        system_test_details = None
        deployment_test_details = None
        
        # Get system test details if available
        if system_test_session_id:
            from phase_two.testing.system.integration import SystemTestingOrchestrator
            orchestrator = SystemTestingOrchestrator(
                self._event_queue,
                self._state_manager,
                self._context_manager,
                self._cache_manager,
                self._metrics_manager,
                self._error_handler,
                self._memory_monitor,
                self._system_monitor
            )
            
            system_test_details = await orchestrator.generate_comprehensive_report(system_test_session_id)
            
        # Get deployment test details if available
        if deployment_test_session_id:
            from phase_two.testing.deployment.integration import DeploymentTestingOrchestrator
            orchestrator = DeploymentTestingOrchestrator(
                self._event_queue,
                self._state_manager,
                self._context_manager,
                self._cache_manager,
                self._metrics_manager,
                self._error_handler,
                self._memory_monitor,
                self._system_monitor
            )
            
            deployment_test_details = await orchestrator.generate_deployment_report(deployment_test_session_id)
        
        # Build detailed report
        return {
            "component_id": component_id,
            "name": component_status.get("name", ""),
            "health_status": ComponentTestStatus(**component_status).get_health_status(),
            "test_history": {
                "system_tests": component_status.get("system_test_history", []),
                "deployment_tests": component_status.get("deployment_test_history", [])
            },
            "latest_test_results": {
                "system_test": system_test_details,
                "deployment_test": deployment_test_details
            },
            "success_rate": component_status.get("test_success_rate", 1.0),
            "last_system_test_time": component_status.get("last_system_test_time"),
            "last_deployment_test_time": component_status.get("last_deployment_test_time")
        }