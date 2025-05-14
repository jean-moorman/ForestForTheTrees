"""
Forest For The Trees (FFTT) Component Test Monitoring Dashboard
-------------------------------------------------------------
Provides a dashboard view of component test results and health status.
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

from .test_results import TestResultsMonitor

logger = logging.getLogger(__name__)


class ComponentTestingDashboard(PhaseTwoAgentBase):
    """
    Provides a dashboard view of component test results and health status.
    
    Responsibilities:
    - Aggregates test result data for visualization
    - Generates summary views of component health
    - Provides APIs for querying component test status
    - Identifies potential issues in component testing
    """
    
    def __init__(self,
                event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                test_results_monitor: TestResultsMonitor,
                memory_monitor: Optional[MemoryMonitor] = None,
                system_monitor: Optional[SystemMonitor] = None):
        """Initialize the component testing dashboard."""
        super().__init__(
            "component_testing_dashboard",
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor
        )
        
        # Store test results monitor
        self._test_results_monitor = test_results_monitor
        
        # For health integration
        self._system_monitor = system_monitor
        
        # Dashboard data
        self._last_refresh_time = None
        self._dashboard_data = {}
        self._refresh_interval = 300  # 5 minutes
        
        # Register with system monitor if available
        if self._system_monitor:
            asyncio.create_task(
                self._system_monitor.register_component("component_testing_dashboard", {
                    "type": "dashboard",
                    "description": "Dashboard for component test results"
                })
            )
    
    async def get_dashboard_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get the dashboard data, refreshing if needed.
        
        Args:
            force_refresh: Whether to force a refresh of the data
            
        Returns:
            Dict containing dashboard data
        """
        # Check if refresh is needed
        now = datetime.now()
        if (force_refresh or 
            self._last_refresh_time is None or 
            (now - self._last_refresh_time).total_seconds() > self._refresh_interval):
            await self._refresh_dashboard_data()
        
        return self._dashboard_data
    
    async def _refresh_dashboard_data(self) -> None:
        """Refresh the dashboard data."""
        try:
            # Start tracking refresh time
            start_time = datetime.now()
            
            # Get test summary report
            test_summary = await self._test_results_monitor.generate_test_summary_report()
            
            # Identify top components by health status
            critical_components = []
            degraded_components = []
            healthy_components = []
            
            for component in test_summary.get("components", []):
                if component.get("health_status") == "CRITICAL":
                    critical_components.append(component)
                elif component.get("health_status") in ["DEGRADED", "WARNING"]:
                    degraded_components.append(component)
                elif component.get("health_status") == "HEALTHY":
                    healthy_components.append(component)
            
            # Get recent test sessions
            recent_test_sessions = await self._get_recent_test_sessions()
            
            # Identify trends
            trends = await self._identify_trends(test_summary, recent_test_sessions)
            
            # Build dashboard data
            self._dashboard_data = {
                "timestamp": datetime.now().isoformat(),
                "summary": test_summary,
                "critical_components": critical_components[:5],  # Top 5
                "degraded_components": degraded_components[:5],  # Top 5
                "healthy_components": healthy_components[:5],    # Top 5
                "recent_test_sessions": recent_test_sessions,
                "trends": trends,
                "last_refresh": datetime.now().isoformat(),
                "refresh_duration_seconds": (datetime.now() - start_time).total_seconds()
            }
            
            # Update last refresh time
            self._last_refresh_time = datetime.now()
            
            # Record metric for dashboard refresh
            await self._metrics_manager.record_metric(
                "component_testing:dashboard_refresh",
                1.0,
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "refresh_duration": (datetime.now() - start_time).total_seconds(),
                    "component_count": test_summary.get("total_components", 0)
                }
            )
            
        except Exception as e:
            logger.error(f"Error refreshing dashboard data: {e}", exc_info=True)
            
            # Record error metric
            await self._metrics_manager.record_metric(
                "component_testing:dashboard_refresh_error",
                1.0,
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e)
                }
            )
    
    async def _get_recent_test_sessions(self) -> List[Dict[str, Any]]:
        """Get recent test sessions."""
        # Use state manager to find recent test sessions
        system_test_states = await self._state_manager.list_states("system_testing:")
        deployment_test_states = await self._state_manager.list_states("deployment_testing:")
        
        # Get the actual state data for each session
        system_tests = []
        for state_key in system_test_states[:10]:  # Limit to 10 most recent
            state = await self._state_manager.get_state(state_key)
            if state:
                state["type"] = "system"
                system_tests.append(state)
        
        deployment_tests = []
        for state_key in deployment_test_states[:10]:  # Limit to 10 most recent
            state = await self._state_manager.get_state(state_key)
            if state:
                state["type"] = "deployment"
                deployment_tests.append(state)
        
        # Combine and sort by timestamp
        all_tests = system_tests + deployment_tests
        all_tests.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return all_tests[:10]  # Return 10 most recent
    
    async def _identify_trends(self, 
                             test_summary: Dict[str, Any], 
                             recent_sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify trends in test results."""
        # Get component statuses
        component_statuses = await self._test_results_monitor.get_all_component_test_statuses()
        
        # Count components with increasing or decreasing success rates
        improving_components = []
        degrading_components = []
        
        for component_id, status in component_statuses.items():
            # Skip if not enough history
            if (not status.get("system_test_history") or 
                len(status.get("system_test_history", [])) < 2):
                continue
            
            # Get success rates from history
            history = status.get("system_test_history", [])
            history.sort(key=lambda x: x.get("timestamp", ""))
            
            # Calculate success rates at beginning and end of history
            if len(history) >= 2:
                first = history[0]
                last = history[-1]
                
                first_success_rate = first.get("passed_tests", 0) / first.get("total_tests", 1)
                last_success_rate = last.get("passed_tests", 0) / last.get("total_tests", 1)
                
                if last_success_rate > first_success_rate + 0.1:  # 10% improvement
                    improving_components.append({
                        "component_id": component_id,
                        "name": status.get("name", ""),
                        "first_success_rate": first_success_rate,
                        "last_success_rate": last_success_rate,
                        "improvement": last_success_rate - first_success_rate
                    })
                elif last_success_rate < first_success_rate - 0.1:  # 10% degradation
                    degrading_components.append({
                        "component_id": component_id,
                        "name": status.get("name", ""),
                        "first_success_rate": first_success_rate,
                        "last_success_rate": last_success_rate,
                        "degradation": first_success_rate - last_success_rate
                    })
        
        # Sort by improvement/degradation amount
        improving_components.sort(key=lambda x: x.get("improvement", 0), reverse=True)
        degrading_components.sort(key=lambda x: x.get("degradation", 0), reverse=True)
        
        # Count test sessions by day for the last 7 days
        now = datetime.now()
        daily_counts = {(now - timedelta(days=i)).strftime("%Y-%m-%d"): 0 for i in range(7)}
        
        for session in recent_sessions:
            timestamp = session.get("timestamp", "")
            if timestamp:
                try:
                    date = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d")
                    if date in daily_counts:
                        daily_counts[date] += 1
                except (ValueError, TypeError):
                    continue
        
        # Format the trend data
        return {
            "improving_components": improving_components[:5],  # Top 5
            "degrading_components": degrading_components[:5],  # Top 5
            "daily_test_counts": [
                {"date": date, "count": count}
                for date, count in sorted(daily_counts.items())
            ],
            "overall_health_trend": self._calculate_health_trend(test_summary)
        }
    
    def _calculate_health_trend(self, test_summary: Dict[str, Any]) -> str:
        """Calculate overall health trend."""
        status_counts = test_summary.get("status_summary", {})
        total = test_summary.get("total_components", 0)
        
        if total == 0:
            return "stable"
        
        # Calculate percentages
        healthy_percent = status_counts.get("HEALTHY", 0) / total if total > 0 else 0
        critical_percent = status_counts.get("CRITICAL", 0) / total if total > 0 else 0
        degraded_percent = status_counts.get("DEGRADED", 0) / total if total > 0 else 0
        warning_percent = status_counts.get("WARNING", 0) / total if total > 0 else 0
        
        # Determine trend
        if healthy_percent > 0.8:
            return "strongly_positive"
        elif healthy_percent > 0.6:
            return "positive"
        elif critical_percent > 0.3:
            return "strongly_negative"
        elif critical_percent > 0.1 or degraded_percent > 0.3:
            return "negative"
        else:
            return "stable"
    
    async def get_component_health_overview(self) -> Dict[str, Any]:
        """
        Get a summary of component health for executive overview.
        
        Returns:
            Dict containing component health summary
        """
        # Get test summary
        test_summary = await self._test_results_monitor.generate_test_summary_report()
        
        # Extract key metrics
        status_counts = test_summary.get("status_summary", {})
        test_summary_data = test_summary.get("test_summary", {})
        
        # Calculate percentages
        total = test_summary.get("total_components", 0)
        healthy_percent = status_counts.get("HEALTHY", 0) / total * 100 if total > 0 else 0
        critical_percent = status_counts.get("CRITICAL", 0) / total * 100 if total > 0 else 0
        
        # Get pass rate
        pass_rate = test_summary_data.get("success_rate", 0) * 100
        
        # Create summary
        return {
            "timestamp": datetime.now().isoformat(),
            "total_components": total,
            "health_distribution": status_counts,
            "healthy_percentage": healthy_percent,
            "critical_percentage": critical_percent,
            "test_pass_rate": pass_rate,
            "total_tests_executed": test_summary_data.get("total_system_tests", 0) + test_summary_data.get("total_deployment_tests", 0),
            "overall_health": test_summary.get("overall_health", "UNKNOWN"),
            "health_trend": self._calculate_health_trend(test_summary),
            "recommendation": self._generate_recommendation(test_summary)
        }
    
    def _generate_recommendation(self, test_summary: Dict[str, Any]) -> str:
        """Generate a recommendation based on test summary."""
        overall_health = test_summary.get("overall_health", "UNKNOWN")
        status_counts = test_summary.get("status_summary", {})
        
        if overall_health == "HEALTHY":
            return "All components are healthy. Continue monitoring and regular testing."
        elif overall_health == "CRITICAL":
            return f"Critical issues detected in {status_counts.get('CRITICAL', 0)} components. Immediate investigation required."
        elif overall_health == "DEGRADED":
            return f"Performance degradation in {status_counts.get('DEGRADED', 0)} components. Prioritize investigation and fixes."
        elif overall_health == "WARNING":
            return f"Potential issues detected in {status_counts.get('WARNING', 0)} components. Schedule investigation."
        else:
            return "Insufficient test data. Increase test coverage across components."
    
    async def get_component_details_report(self, component_id: str) -> Dict[str, Any]:
        """
        Get a detailed report for a specific component.
        
        Args:
            component_id: The ID of the component to report on
            
        Returns:
            Dict containing detailed component report
        """
        # Get component test details
        test_details = await self._test_results_monitor.get_component_test_details(component_id)
        if "error" in test_details:
            return test_details
        
        # Extract key information
        latest_system_test = test_details.get("latest_test_results", {}).get("system_test", {})
        latest_deployment_test = test_details.get("latest_test_results", {}).get("deployment_test", {})
        
        # Generate recommendations based on test results
        recommendations = self._generate_component_recommendations(test_details)
        
        # Create report
        return {
            "component_id": component_id,
            "name": test_details.get("name", ""),
            "health_status": test_details.get("health_status", "UNKNOWN"),
            "success_rate": test_details.get("success_rate", 0) * 100,
            "last_system_test_time": test_details.get("last_system_test_time"),
            "last_deployment_test_time": test_details.get("last_deployment_test_time"),
            "test_history": {
                "system_tests": len(test_details.get("test_history", {}).get("system_tests", [])),
                "deployment_tests": len(test_details.get("test_history", {}).get("deployment_tests", []))
            },
            "latest_system_test_summary": self._extract_test_summary(latest_system_test),
            "latest_deployment_test_summary": self._extract_test_summary(latest_deployment_test),
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }
    
    def _extract_test_summary(self, test_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract a summary from a test result."""
        if not test_result:
            return {"status": "not_available"}
        
        # Different formats depending on test type
        if "execution_results" in test_result:
            execution = test_result.get("execution_results", {})
            return {
                "status": execution.get("status", "unknown"),
                "total_tests": execution.get("total_tests", 0),
                "passed_tests": execution.get("passed_tests", 0),
                "failed_tests": execution.get("failed_tests", 0),
                "timestamp": test_result.get("timestamp", "")
            }
        
        # Check for summary field common in deployment tests
        if "summary" in test_result:
            summary = test_result.get("summary", {})
            return {
                "status": summary.get("overall_status", "unknown"),
                "environment": summary.get("environment", "unknown"),
                "test_summary": summary.get("test_summary", ""),
                "timestamp": test_result.get("timestamp", "")
            }
        
        # Generic handling for other formats
        return {
            "status": test_result.get("status", "unknown"),
            "timestamp": test_result.get("timestamp", "")
        }
    
    def _generate_component_recommendations(self, test_details: Dict[str, Any]) -> List[str]:
        """Generate recommendations for a component based on test details."""
        recommendations = []
        health_status = test_details.get("health_status", "UNKNOWN")
        success_rate = test_details.get("success_rate", 0)
        
        # Check if tests are recent
        last_system_test = test_details.get("last_system_test_time")
        last_deployment_test = test_details.get("last_deployment_test_time")
        
        now = datetime.now()
        system_test_age = None
        deployment_test_age = None
        
        if last_system_test:
            try:
                last_system_test_dt = datetime.fromisoformat(last_system_test)
                system_test_age = (now - last_system_test_dt).days
            except (ValueError, TypeError):
                pass
                
        if last_deployment_test:
            try:
                last_deployment_test_dt = datetime.fromisoformat(last_deployment_test)
                deployment_test_age = (now - last_deployment_test_dt).days
            except (ValueError, TypeError):
                pass
        
        # Add recommendations based on health status
        if health_status == "CRITICAL":
            recommendations.append("Immediate investigation required due to critical test failures.")
            recommendations.append("Prioritize fixing test failures before any new feature development.")
        elif health_status == "DEGRADED":
            recommendations.append("Address test failures to improve component reliability.")
            recommendations.append("Review recent changes that may have caused degradation.")
        elif health_status == "WARNING":
            recommendations.append("Monitor this component closely for further degradation.")
            recommendations.append("Schedule time to address minor test failures.")
        
        # Add recommendations based on test age
        if system_test_age is None or system_test_age > 30:
            recommendations.append("Run system tests as none have been run recently or ever.")
        
        if deployment_test_age is None or deployment_test_age > 60:
            recommendations.append("Schedule deployment tests as none have been run recently or ever.")
        
        # Add recommendations based on success rate trend
        history = test_details.get("test_history", {}).get("system_tests", [])
        if len(history) >= 2:
            history.sort(key=lambda x: x.get("timestamp", ""))
            first = history[0]
            last = history[-1]
            
            first_success_rate = first.get("passed_tests", 0) / first.get("total_tests", 1)
            last_success_rate = last.get("passed_tests", 0) / last.get("total_tests", 1)
            
            if last_success_rate < first_success_rate - 0.1:
                recommendations.append("Investigate recent regression in test success rate.")
        
        # If no specific recommendations, add generic ones
        if not recommendations:
            if success_rate >= 0.95:
                recommendations.append("Maintain current testing practices. Component is stable.")
            else:
                recommendations.append("Consider increasing test coverage to improve reliability.")
        
        return recommendations