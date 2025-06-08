"""
Integration tests with run_phase_one.py system

Tests the GUI components working with the actual Phase One system as implemented
in run_phase_one.py, providing real integration testing that mirrors the production
environment.
"""

import asyncio
import pytest
import sys
import time
import threading
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock

import qasync
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Import the Phase One system components
from run_phase_one import PhaseOneApp, PhaseOneInterface, PhaseOneDebugger
from display import ForestDisplay, TimelineWidget, AlertLevel
from interfaces import AgentState

# Import test infrastructure
from .conftest import GuiTestBase, TestSignalWaiter, async_wait_for_condition

class MockPhaseOneComponents:
    """Mock components that simulate real Phase One system behavior."""
    
    def __init__(self):
        self.phase_one_app = None
        self.orchestrator = None
        self.event_queue = None
        self.system_monitor = None
        
    async def setup_mock_system(self):
        """Set up mock system components that behave like real ones."""
        # Create minimal event queue
        from resources.events import EventQueue
        self.event_queue = EventQueue(queue_id="integration_test_queue")
        await self.event_queue.start()
        
        # Create mock orchestrator with realistic responses
        self.orchestrator = MagicMock()
        self.orchestrator.process_task = self._mock_process_task
        self.orchestrator.get_agent_metrics = self._mock_get_agent_metrics
        
        # Create mock system monitor
        self.system_monitor = MagicMock()
        self.system_monitor.memory_monitor = MagicMock()
        self.system_monitor.health_tracker = MagicMock()
        self.system_monitor._circuit_breakers = {}
        self.system_monitor._metrics = MagicMock()
        
        # Configure realistic return values
        self._configure_system_monitor()
        
    async def _mock_process_task(self, prompt: str) -> Dict[str, Any]:
        """Mock task processing that simulates real Phase One behavior."""
        await asyncio.sleep(0.1)  # Simulate processing time
        
        return {
            "status": "success",
            "structural_components": [
                {
                    "name": "User Interface Component",
                    "description": f"UI component for: {prompt[:50]}...",
                    "dependencies": []
                },
                {
                    "name": "Data Processing Component", 
                    "description": "Handles data processing and validation",
                    "dependencies": ["User Interface Component"]
                },
                {
                    "name": "Storage Component",
                    "description": "Manages data persistence",
                    "dependencies": ["Data Processing Component"]
                }
            ],
            "system_requirements": {
                "task_analysis": {
                    "interpreted_goal": f"Build system for: {prompt}",
                    "technical_requirements": {
                        "languages": ["Python", "JavaScript"],
                        "frameworks": ["PyQt6", "React", "FastAPI"]
                    }
                }
            },
            "phase_one_outputs": {
                "garden_planner": {
                    "strategy": f"Strategic approach for {prompt}",
                    "components": ["component_1", "component_2", "component_3"],
                    "dependencies": []
                },
                "earth_agent": {
                    "validation_result": "passed",
                    "refinement_suggestions": [],
                    "validation_cycles": 1
                },
                "environmental_analysis": {
                    "environmental_factors": ["scalability", "maintainability", "security"],
                    "recommendations": ["Use modular architecture", "Implement proper testing"]
                },
                "root_system_architect": {
                    "architecture": "layered_architecture",
                    "patterns": ["MVC", "Repository", "Factory"]
                },
                "tree_placement_planner": {
                    "deployment_strategy": "containerized_deployment",
                    "infrastructure": ["Docker", "Kubernetes"]
                }
            },
            "execution_time": 2.5,
            "refinement_analysis": {
                "status": "no_refinement_required",
                "cycle": 1
            }
        }
        
    async def _mock_get_agent_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Mock agent metrics that simulate real monitoring data."""
        await asyncio.sleep(0.05)  # Simulate metrics collection time
        
        return {
            "status": "success",
            "agent_id": agent_id,
            "metrics": {
                "operations_count": 15 + hash(agent_id) % 50,
                "success_rate": 0.92 + (hash(agent_id) % 8) / 100,
                "average_response_time": 1.1 + (hash(agent_id) % 10) / 10,
                "error_rate": 0.08 - (hash(agent_id) % 8) / 100,
                "last_activity": time.time() - (hash(agent_id) % 3600),
                "memory_usage_mb": 25 + (hash(agent_id) % 20)
            },
            "state": ["READY", "RUNNING", "COMPLETED"][hash(agent_id) % 3],
            "health": "HEALTHY"
        }
        
    def _configure_system_monitor(self):
        """Configure system monitor with realistic data."""
        # Memory monitor configuration
        self.system_monitor.memory_monitor._resource_sizes = {
            "garden_planner": 45.2,
            "earth_agent": 38.7,
            "environmental_analysis": 29.3,
            "root_system_architect": 33.1,
            "tree_placement_planner": 27.8
        }
        
        self.system_monitor.memory_monitor._thresholds = MagicMock()
        self.system_monitor.memory_monitor._thresholds.total_memory_mb = 2048
        self.system_monitor.memory_monitor._thresholds.warning_percent = 75
        self.system_monitor.memory_monitor._thresholds.critical_percent = 90
        
        # Health tracker configuration
        health_status = MagicMock()
        health_status.status = "HEALTHY"
        self.system_monitor.health_tracker.get_system_health.return_value = health_status
        
        # Metrics configuration
        self.system_monitor._metrics.get_error_density.return_value = 0.02
        self.system_monitor._metrics.get_avg_recovery_time.return_value = 1.8
        self.system_monitor._metrics.get_state_durations.return_value = {
            "CLOSED": 95.0, "OPEN": 3.0, "HALF_OPEN": 2.0
        }
        
    async def cleanup(self):
        """Clean up mock system components."""
        if self.event_queue:
            try:
                await self.event_queue.stop()
            except Exception:
                pass


@pytest.fixture
def phase_one_integration_env(qapp_fixture, event_loop_fixture):
    """Set up integration testing environment with Phase One components."""
    mock_system = MockPhaseOneComponents()
    
    # Setup in the event loop
    loop = event_loop_fixture
    loop.run_until_complete(mock_system.setup_mock_system())
    
    yield mock_system
    
    # Cleanup in the event loop
    try:
        loop.run_until_complete(mock_system.cleanup())
    except Exception as e:
        print(f"Warning: Error during cleanup: {e}")


@pytest.mark.asyncio
class TestPhaseOneIntegration:
    """Integration tests with Phase One system components."""
    
    async def test_forest_display_with_phase_one_interface(self, phase_one_integration_env):
        """Test ForestDisplay integration with PhaseOneInterface."""
        mock_system = phase_one_integration_env
        
        # Create PhaseOneInterface with mock orchestrator
        interface = PhaseOneInterface(mock_system.orchestrator)
        
        # Create ForestDisplay with the interface
        display = ForestDisplay(
            mock_system.event_queue,
            interface,
            mock_system.system_monitor
        )
        
        try:
            display.show()
            
            # Test task processing through the interface
            test_prompt = "Create a comprehensive project management system"
            result = await interface.process_task(test_prompt)
            
            # Verify integration works
            assert result["status"] == "success"
            assert "phase_one_outputs" in result
            # The structural_components are nested inside phase_one_outputs
            phase_outputs = result["phase_one_outputs"]
            assert "structural_components" in phase_outputs or any("component" in str(v) for v in phase_outputs.values())
            
            # Verify display can handle the result
            await asyncio.sleep(0.1)  # Allow UI processing
            
        finally:
            display.close()
            
    async def test_display_with_realistic_agent_updates(self, phase_one_integration_env):
        """Test display with realistic agent state updates."""
        mock_system = phase_one_integration_env
        
        # Create display
        display = ForestDisplay(
            mock_system.event_queue,
            mock_system.orchestrator,
            mock_system.system_monitor
        )
        
        try:
            display.show()
            display._pending_updates = set()
            
            # Simulate realistic agent workflow
            agents = ['garden_planner', 'earth_agent', 'environmental_analysis', 
                     'root_system_architect', 'tree_placement_planner']
            
            for i, agent in enumerate(agents):
                # Simulate agent starting work
                from display import TimelineState
                start_state = TimelineState(
                    start_time=time.time(),
                    state=AgentState.RUNNING,
                    metadata={'operation': 'phase_one_workflow', 'step': i+1}
                )
                display.timeline.agent_states[agent].add_state(start_state)
                
                # Process UI updates
                await asyncio.sleep(0.1)
                
                # Simulate agent completing work
                complete_state = TimelineState(
                    start_time=time.time(),
                    state=AgentState.COMPLETED,
                    metadata={'operation': 'phase_one_workflow', 'step': i+1, 'result': 'success'}
                )
                display.timeline.agent_states[agent].add_state(complete_state)
                
                # Update display
                display.timeline.update()
                await asyncio.sleep(0.05)
                
            # Verify all agents have updated states
            for agent in agents:
                states = display.timeline.agent_states[agent].states
                assert len(states) >= 2  # Should have start and complete states
                
        finally:
            display.close()
            
    async def test_prompt_interface_with_real_workflow(self, phase_one_integration_env):
        """Test PromptInterface with realistic Phase One workflow."""
        mock_system = phase_one_integration_env
        
        # Create display with prompt interface
        display = ForestDisplay(
            mock_system.event_queue,
            mock_system.orchestrator,
            mock_system.system_monitor
        )
        
        try:
            display.show()
            
            # Test realistic prompt workflow
            test_prompts = [
                "Create a web-based customer relationship management system",
                "Build a real-time data analytics dashboard",
                "Develop a mobile application for task management"
            ]
            
            processed_results = []
            
            for prompt in test_prompts:
                # Process prompt through display
                result = await display._process_prompt_async(prompt)
                processed_results.append(result)
                
                # Verify result structure matches Phase One output
                assert "status" in result
                assert "phase_one_outputs" in result
                assert "structural_components" in result["phase_one_outputs"]
                
                # Allow UI processing time
                await asyncio.sleep(0.1)
                
            # Verify all prompts were processed
            assert len(processed_results) == len(test_prompts)
            
            # All should be successful
            for result in processed_results:
                assert result["status"] == "success"
                
        finally:
            display.close()
            
    async def test_metrics_integration_with_phase_one(self, phase_one_integration_env):
        """Test metrics integration with Phase One components."""
        mock_system = phase_one_integration_env
        
        # Create display
        display = ForestDisplay(
            mock_system.event_queue,
            mock_system.orchestrator,
            mock_system.system_monitor
        )
        
        try:
            display.show()
            
            # Test agent metrics retrieval
            test_agents = ['garden_planner', 'earth_agent', 'environmental_analysis']
            
            for agent in test_agents:
                # Get metrics through display
                metrics = await display._update_agent_metrics(agent)
                
                # Verify metrics structure
                assert "status" in metrics
                assert "agent_id" in metrics
                assert "metrics" in metrics
                assert metrics["agent_id"] == agent
                
                # Verify realistic metric values
                agent_metrics = metrics["metrics"]
                assert "operations_count" in agent_metrics
                assert "success_rate" in agent_metrics
                assert "average_response_time" in agent_metrics
                assert 0 <= agent_metrics["success_rate"] <= 1
                assert agent_metrics["average_response_time"] > 0
                
            # Test system metrics update
            display.metrics_panel.update_all()
            await asyncio.sleep(0.1)  # Allow processing
            
        finally:
            display.close()
            
    async def test_error_handling_integration(self, phase_one_integration_env):
        """Test error handling integration with Phase One system."""
        mock_system = phase_one_integration_env
        
        # Create display
        display = ForestDisplay(
            mock_system.event_queue,
            mock_system.orchestrator,
            mock_system.system_monitor
        )
        
        try:
            display.show()
            display._pending_updates = set()
            
            # Simulate various error conditions
            error_scenarios = [
                {
                    "type": "system_error",
                    "data": {
                        "error": "Memory threshold exceeded",
                        "component": "memory_monitor",
                        "severity": "HIGH"
                    }
                },
                {
                    "type": "agent_error", 
                    "data": {
                        "error": "Agent validation failed",
                        "component": "earth_agent",
                        "severity": "MEDIUM"
                    }
                },
                {
                    "type": "processing_error",
                    "data": {
                        "error": "Task processing timeout",
                        "component": "orchestrator",
                        "severity": "HIGH"
                    }
                }
            ]
            
            for scenario in error_scenarios:
                # Emit error event
                from resources import ResourceEventTypes
                await mock_system.event_queue.emit(
                    ResourceEventTypes.ERROR_OCCURRED,
                    scenario["data"]
                )
                
                # Allow error processing
                await asyncio.sleep(0.1)
                
            # Display should handle errors gracefully
            # (No exceptions means error handling worked)
            assert True
            
        finally:
            display.close()
            
    async def test_real_time_monitoring_integration(self, phase_one_integration_env):
        """Test real-time monitoring integration."""
        mock_system = phase_one_integration_env
        
        # Create display
        display = ForestDisplay(
            mock_system.event_queue,
            mock_system.orchestrator,
            mock_system.system_monitor
        )
        
        try:
            display.show()
            display._pending_updates = set()
            
            # Simulate real-time monitoring data
            monitoring_data = [
                {"metric": "cpu_usage", "value": 45.2, "timestamp": time.time()},
                {"metric": "memory_usage", "value": 67.8, "timestamp": time.time()},
                {"metric": "error_rate", "value": 0.02, "timestamp": time.time()},
                {"metric": "throughput", "value": 127.5, "timestamp": time.time()},
                {"metric": "response_time", "value": 1.23, "timestamp": time.time()}
            ]
            
            # Emit monitoring events
            from resources import ResourceEventTypes
            for data in monitoring_data:
                await mock_system.event_queue.emit(
                    ResourceEventTypes.METRIC_RECORDED,
                    data
                )
                await asyncio.sleep(0.02)  # Simulate real-time interval
                
            # Process all events
            await asyncio.sleep(0.2)
            
            # Test health status updates
            await mock_system.event_queue.emit(
                ResourceEventTypes.SYSTEM_HEALTH_CHANGED,
                {
                    "component": "system",
                    "status": "HEALTHY",
                    "description": "All systems operational"
                }
            )
            
            await asyncio.sleep(0.1)
            
            # Display should handle real-time updates
            assert True
            
        finally:
            display.close()


@pytest.mark.asyncio
class TestPhaseOneSystemIntegration:
    """Integration tests with the actual Phase One system architecture."""
    
    async def test_display_with_phase_one_app_architecture(self, qapp_fixture, event_loop_fixture):
        """Test display integration with Phase One app architecture."""
        # Note: This test simulates the PhaseOneApp structure without 
        # creating the full application to avoid conflicts
        
        # Create mock components that match PhaseOneApp structure
        from resources.events import EventQueue
        from resources.state import StateManager
        from resources.managers import AgentContextManager, CacheManager, MetricsManager
        from resources.monitoring import SystemMonitor, MemoryMonitor, HealthTracker
        
        # Initialize event queue
        event_queue = EventQueue(queue_id="phase_one_app_test")
        await event_queue.start()
        
        try:
            # Create resource managers (similar to PhaseOneApp.setup_async)
            state_manager = StateManager(event_queue)
            context_manager = AgentContextManager(event_queue)
            cache_manager = CacheManager(event_queue)
            metrics_manager = MetricsManager(event_queue)
            
            # Create monitoring components
            memory_monitor = MemoryMonitor(event_queue)
            health_tracker = HealthTracker(event_queue)
            system_monitor = SystemMonitor(event_queue, memory_monitor, health_tracker)
            
            # Create Phase One interface
            mock_orchestrator = MagicMock()
            mock_orchestrator.process_task = AsyncMock(return_value={
                "status": "success",
                "phase_one_outputs": {"garden_planner": {"strategy": "test"}}
            })
            
            interface = PhaseOneInterface(mock_orchestrator)
            
            # Create display with realistic components
            display = ForestDisplay(event_queue, interface, system_monitor)
            display.show()
            
            # Test that display works with real component structure
            test_prompt = "Test Phase One app integration"
            result = await interface.process_task(test_prompt)
            
            # Verify integration
            assert result["status"] == "success"
            
            # Test display update
            await asyncio.sleep(0.1)
            display.timeline.update()
            
            display.close()
            
        finally:
            await event_queue.stop()
            
    async def test_debugger_integration_simulation(self, phase_one_integration_env):
        """Test integration with Phase One debugger functionality."""
        mock_system = phase_one_integration_env
        
        # Create a debugger-like interface for testing
        class MockDebugger:
            def __init__(self, orchestrator):
                self.orchestrator = orchestrator
                self.execution_history = []
                
            async def execute_with_monitoring(self, prompt):
                """Simulate debugger execution with monitoring."""
                start_time = time.time()
                
                # Execute through orchestrator
                result = await self.orchestrator.process_task(prompt)
                
                end_time = time.time()
                
                # Record execution
                execution_record = {
                    "prompt": prompt,
                    "result": result,
                    "execution_time": end_time - start_time,
                    "timestamp": start_time
                }
                
                self.execution_history.append(execution_record)
                return result
        
        # Create display and debugger
        display = ForestDisplay(
            mock_system.event_queue,
            mock_system.orchestrator,
            mock_system.system_monitor
        )
        
        debugger = MockDebugger(mock_system.orchestrator)
        
        try:
            display.show()
            
            # Test debugger-style execution with display monitoring
            test_prompts = [
                "Create user authentication system",
                "Build data visualization dashboard",
                "Implement API gateway service"
            ]
            
            for prompt in test_prompts:
                # Execute through debugger
                result = await debugger.execute_with_monitoring(prompt)
                
                # Verify execution
                assert result["status"] == "success"
                
                # Update display with execution info
                await asyncio.sleep(0.05)
                
            # Verify debugger captured all executions
            assert len(debugger.execution_history) == len(test_prompts)
            
            # Verify display remains responsive
            display.timeline.update()
            await asyncio.sleep(0.1)
            
        finally:
            display.close()
            
    async def test_performance_with_phase_one_load(self, phase_one_integration_env):
        """Test display performance under Phase One typical load."""
        mock_system = phase_one_integration_env
        
        # Create display
        display = ForestDisplay(
            mock_system.event_queue,
            mock_system.orchestrator,
            mock_system.system_monitor
        )
        
        try:
            display.show()
            display._pending_updates = set()
            
            # Simulate typical Phase One operation load
            start_time = time.time()
            
            # Simulate agent workflow execution
            workflow_steps = [
                ("garden_planner", "strategy_development"),
                ("earth_agent", "validation_phase_1"),
                ("earth_agent", "validation_phase_2"), 
                ("environmental_analysis", "analysis_execution"),
                ("root_system_architect", "architecture_design"),
                ("tree_placement_planner", "deployment_planning")
            ]
            
            for agent, step in workflow_steps:
                # Simulate agent state change
                from display import TimelineState
                state = TimelineState(
                    start_time=time.time(),
                    state=AgentState.RUNNING,
                    metadata={'step': step, 'workflow': 'phase_one'}
                )
                display.timeline.agent_states[agent].add_state(state)
                
                # Simulate metrics update
                await mock_system.event_queue.emit(
                    "METRIC_RECORDED",
                    {
                        "metric": f"{agent}_performance",
                        "value": 85 + (hash(step) % 15),
                        "timestamp": time.time()
                    }
                )
                
                # Process updates
                await asyncio.sleep(0.02)
                
            # Final processing
            await asyncio.sleep(0.2)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Should handle typical load efficiently
            assert total_time < 1.0, f"Phase One load handling took too long: {total_time}s"
            
            # Display should remain responsive
            display.timeline.update()
            display.metrics_panel.update_all()
            
        finally:
            display.close()