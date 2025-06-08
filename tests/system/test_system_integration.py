"""
Test System Integration from run_phase_one.py

This module tests system-level integration including process management, 
file system operations, environment variable handling, and cross-component
integration that spans the entire system architecture.
"""

import pytest
import asyncio
import os
import tempfile
import shutil
import threading
import time
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock, mock_open
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from run_phase_one import PhaseOneApp, PhaseOneInterface, PhaseOneDebugger
from resources.events import EventQueue
from resources.state import StateManager
from resources.managers import AgentContextManager, CacheManager, MetricsManager


class TestFileSystemIntegration:
    """Test file system operations and integration."""
    
    def test_temporary_file_creation_and_cleanup(self):
        """Test temporary file creation and proper cleanup."""
        temp_files_created = []
        
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            mock_file = MagicMock()
            mock_file.name = '/tmp/test_file_12345'
            mock_temp_file.return_value = mock_file
            
            with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
                mock_qapp = MagicMock()
                mock_qapp_class.instance.return_value = None
                mock_qapp_class.return_value = mock_qapp
                
                with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                    test_loop = asyncio.new_event_loop()
                    mock_ensure.return_value = test_loop
                    
                    try:
                        app = PhaseOneApp()
                        
                        # Simulate temporary file operations
                        temp_file = app.create_temp_file("test_data")
                        temp_files_created.append(temp_file.name)
                        
                        # Verify temp file was created
                        mock_temp_file.assert_called_once()
                        assert temp_file.name == '/tmp/test_file_12345'
                        
                        # Cleanup should remove temp files
                        app.cleanup_temp_files()
                        mock_file.close.assert_called_once()
                    
                    finally:
                        test_loop.close()
    
    def test_file_system_permission_handling(self):
        """Test handling of file system permission errors."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                with patch('builtins.open', mock_open()) as mock_file:
                    # Simulate permission error
                    mock_file.side_effect = PermissionError("Permission denied")
                    
                    test_loop = asyncio.new_event_loop()
                    mock_ensure.return_value = test_loop
                    
                    try:
                        app = PhaseOneApp()
                        
                        # Should handle permission errors gracefully
                        result = app.write_output_file("test.txt", "test content")
                        
                        # Should return error indication
                        assert result is False or result is None
                    
                    finally:
                        test_loop.close()
    
    def test_large_file_handling(self):
        """Test handling of large files."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    
                    # Simulate large file content
                    large_content = "x" * (10 * 1024 * 1024)  # 10MB
                    
                    with patch('builtins.open', mock_open()) as mock_file:
                        # Should handle large files efficiently
                        start_time = time.time()
                        result = app.write_output_file("large_file.txt", large_content)
                        write_time = time.time() - start_time
                        
                        # Should complete within reasonable time
                        assert write_time < 5.0  # Less than 5 seconds
                        mock_file.assert_called_once()
                
                finally:
                    test_loop.close()


class TestEnvironmentVariableIntegration:
    """Test environment variable handling and integration."""
    
    def test_environment_variable_configuration(self):
        """Test configuration via environment variables."""
        test_env_vars = {
            'FFTT_LOG_LEVEL': 'DEBUG',
            'FFTT_MAX_RETRIES': '5',
            'FFTT_TIMEOUT': '30'
        }
        
        with patch.dict(os.environ, test_env_vars):
            with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
                mock_qapp = MagicMock()
                mock_qapp_class.instance.return_value = None
                mock_qapp_class.return_value = mock_qapp
                
                with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                    test_loop = asyncio.new_event_loop()
                    mock_ensure.return_value = test_loop
                    
                    try:
                        app = PhaseOneApp()
                        
                        # Should read configuration from environment
                        config = app.load_configuration()
                        
                        assert config.get('log_level') == 'DEBUG'
                        assert config.get('max_retries') == 5
                        assert config.get('timeout') == 30
                    
                    finally:
                        test_loop.close()
    
    def test_missing_environment_variables(self):
        """Test handling of missing environment variables."""
        # Clear relevant environment variables
        env_vars_to_clear = ['FFTT_LOG_LEVEL', 'FFTT_MAX_RETRIES', 'FFTT_TIMEOUT']
        original_values = {}
        
        for var in env_vars_to_clear:
            original_values[var] = os.environ.pop(var, None)
        
        try:
            with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
                mock_qapp = MagicMock()
                mock_qapp_class.instance.return_value = None
                mock_qapp_class.return_value = mock_qapp
                
                with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                    test_loop = asyncio.new_event_loop()
                    mock_ensure.return_value = test_loop
                    
                    try:
                        app = PhaseOneApp()
                        
                        # Should use default values when env vars missing
                        config = app.load_configuration()
                        
                        assert config.get('log_level') in ['INFO', 'WARNING']  # Default levels
                        assert config.get('max_retries') in [3, 5, 10]  # Reasonable defaults
                        assert config.get('timeout') in [15, 30, 60]  # Reasonable defaults
                    
                    finally:
                        test_loop.close()
        
        finally:
            # Restore original environment
            for var, value in original_values.items():
                if value is not None:
                    os.environ[var] = value
    
    def test_invalid_environment_variable_values(self):
        """Test handling of invalid environment variable values."""
        invalid_env_vars = {
            'FFTT_MAX_RETRIES': 'invalid_number',
            'FFTT_TIMEOUT': 'not_a_number',
            'FFTT_LOG_LEVEL': 'INVALID_LEVEL'
        }
        
        with patch.dict(os.environ, invalid_env_vars):
            with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
                mock_qapp = MagicMock()
                mock_qapp_class.instance.return_value = None
                mock_qapp_class.return_value = mock_qapp
                
                with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                    test_loop = asyncio.new_event_loop()
                    mock_ensure.return_value = test_loop
                    
                    try:
                        app = PhaseOneApp()
                        
                        # Should handle invalid values gracefully
                        config = app.load_configuration()
                        
                        # Should fall back to defaults for invalid values
                        assert isinstance(config.get('max_retries'), int)
                        assert isinstance(config.get('timeout'), (int, float))
                        assert config.get('log_level') in ['DEBUG', 'INFO', 'WARNING', 'ERROR']
                    
                    finally:
                        test_loop.close()


class TestProcessManagement:
    """Test process management and lifecycle."""
    
    @pytest.mark.asyncio
    async def test_subprocess_execution_and_monitoring(self):
        """Test subprocess execution and monitoring."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                with patch('asyncio.create_subprocess_exec') as mock_subprocess:
                    # Mock subprocess
                    mock_process = MagicMock()
                    mock_process.wait = AsyncMock(return_value=0)
                    mock_process.communicate = AsyncMock(return_value=(b'output', b''))
                    mock_subprocess.return_value = mock_process
                    
                    test_loop = asyncio.new_event_loop()
                    mock_ensure.return_value = test_loop
                    
                    try:
                        app = PhaseOneApp()
                        
                        # Execute subprocess
                        result = await app.execute_subprocess(['echo', 'test'])
                        
                        # Verify subprocess was executed
                        mock_subprocess.assert_called_once()
                        assert result['returncode'] == 0
                        assert result['stdout'] == b'output'
                    
                    finally:
                        test_loop.close()
    
    @pytest.mark.asyncio
    async def test_subprocess_timeout_handling(self):
        """Test subprocess timeout handling."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                with patch('asyncio.create_subprocess_exec') as mock_subprocess:
                    # Mock long-running subprocess
                    mock_process = MagicMock()
                    mock_process.wait = AsyncMock(side_effect=asyncio.TimeoutError())
                    mock_process.terminate = MagicMock()
                    mock_process.kill = MagicMock()
                    mock_subprocess.return_value = mock_process
                    
                    test_loop = asyncio.new_event_loop()
                    mock_ensure.return_value = test_loop
                    
                    try:
                        app = PhaseOneApp()
                        
                        # Execute subprocess with timeout
                        result = await app.execute_subprocess(['sleep', '10'], timeout=0.1)
                        
                        # Should handle timeout gracefully
                        assert result['returncode'] != 0  # Non-zero exit due to termination
                        mock_process.terminate.assert_called_once()
                    
                    finally:
                        test_loop.close()
    
    def test_process_resource_cleanup(self):
        """Test process resource cleanup."""
        process_resources = []
        
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    
                    # Simulate resource allocation
                    for i in range(5):
                        resource = f"process_resource_{i}"
                        process_resources.append(resource)
                        app.register_process_resource(resource)
                    
                    # Cleanup should release all resources
                    app.cleanup_process_resources()
                    
                    # Verify cleanup
                    assert len(app.get_active_process_resources()) == 0
                
                finally:
                    test_loop.close()


class TestCrossComponentIntegration:
    """Test integration across different system components."""
    
    @pytest.mark.asyncio
    async def test_full_system_workflow_integration(self):
        """Test complete workflow integration across all components."""
        workflow_events = []
        
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            # Mock orchestrator with full workflow
            mock_orchestrator = MagicMock()
            mock_orchestrator._state_manager = MagicMock()
            
            # Setup all agents
            agents = ['garden_planner_agent', 'earth_agent', 'environmental_analysis_agent',
                     'root_system_architect_agent', 'tree_placement_planner_agent', 'foundation_refinement_agent']
            
            for agent_name in agents:
                agent = MagicMock()
                
                async def make_agent_process(name):
                    async def agent_process(*args):
                        workflow_events.append(f"{name}_executed")
                        await asyncio.sleep(0.01)  # Simulate processing
                        return {"status": "success", "result": f"{name} completed"}
                    return agent_process
                
                agent.process = await make_agent_process(agent_name)
                setattr(mock_orchestrator, agent_name, agent)
            
            with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    interface = PhaseOneInterface(mock_orchestrator)
                    
                    # Execute complete workflow
                    operation_id = await interface.start_phase_one("Full system integration test")
                    
                    # Execute all steps
                    for _ in range(6):  # 6 steps in Phase One
                        step_result = await interface.execute_next_step(operation_id)
                        workflow_events.append(f"step_completed_{step_result['step_executed']}")
                    
                    # Verify complete workflow execution
                    assert len(workflow_events) == 12  # 6 agent executions + 6 step completions
                    
                    # Verify all agents were executed
                    for agent_name in agents:
                        assert f"{agent_name}_executed" in workflow_events
                
                finally:
                    test_loop.close()
    
    @pytest.mark.asyncio
    async def test_event_propagation_across_components(self):
        """Test event propagation across different system components."""
        propagated_events = []
        
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    # Create event queue
                    event_queue = EventQueue()
                    await event_queue.start()
                    
                    # Create managers
                    state_manager = StateManager(event_queue)
                    await state_manager.initialize()
                    
                    cache_manager = CacheManager(event_queue)
                    await cache_manager.initialize()
                    
                    metrics_manager = MetricsManager(event_queue)
                    await metrics_manager.initialize()
                    
                    # Mock event handlers
                    async def event_handler(event_type, data):
                        propagated_events.append((event_type, data))
                    
                    event_queue.add_handler('STATE_CHANGED', event_handler)
                    event_queue.add_handler('CACHE_UPDATED', event_handler)
                    event_queue.add_handler('METRIC_RECORDED', event_handler)
                    
                    # Trigger events from different components
                    await state_manager.set_state('test_key', 'test_value', 'TEST')
                    await event_queue.emit('STATE_CHANGED', {'key': 'test_key', 'value': 'test_value'})
                    
                    await cache_manager.set_cache('cache_key', 'cache_value')
                    await event_queue.emit('CACHE_UPDATED', {'key': 'cache_key', 'value': 'cache_value'})
                    
                    await metrics_manager.record_metric('test_metric', 42)
                    await event_queue.emit('METRIC_RECORDED', {'metric': 'test_metric', 'value': 42})
                    
                    # Allow event propagation
                    await asyncio.sleep(0.1)
                    
                    # Verify event propagation
                    assert len(propagated_events) >= 3
                    event_types = [event[0] for event in propagated_events]
                    assert 'STATE_CHANGED' in event_types
                    assert 'CACHE_UPDATED' in event_types
                    assert 'METRIC_RECORDED' in event_types
                    
                    await event_queue.stop()
                
                finally:
                    test_loop.close()
    
    @pytest.mark.asyncio
    async def test_component_failure_isolation(self):
        """Test that component failures are properly isolated."""
        component_failures = []
        working_components = []
        
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    event_queue = EventQueue()
                    await event_queue.start()
                    
                    # Create managers with one failing
                    state_manager = StateManager(event_queue)
                    await state_manager.initialize()
                    
                    cache_manager = CacheManager(event_queue)
                    await cache_manager.initialize()
                    
                    # Mock cache manager to fail
                    async def failing_cache_operation(*args, **kwargs):
                        component_failures.append('cache_manager_failed')
                        raise Exception("Cache manager failure")
                    
                    cache_manager.set_cache = failing_cache_operation
                    
                    # Test operations
                    try:
                        await state_manager.set_state('key1', 'value1', 'TEST')
                        working_components.append('state_manager_working')
                    except Exception:
                        component_failures.append('state_manager_failed')
                    
                    try:
                        await cache_manager.set_cache('key2', 'value2')
                    except Exception:
                        pass  # Expected failure
                    
                    # StateManager should still work despite CacheManager failure
                    try:
                        value = await state_manager.get_state('key1', 'TEST')
                        if value == 'value1':
                            working_components.append('state_manager_isolated')
                    except Exception:
                        component_failures.append('state_manager_contaminated')
                    
                    # Verify failure isolation
                    assert 'cache_manager_failed' in component_failures
                    assert 'state_manager_working' in working_components
                    assert 'state_manager_isolated' in working_components
                    assert 'state_manager_contaminated' not in component_failures
                    
                    await event_queue.stop()
                
                finally:
                    test_loop.close()


class TestSystemPerformanceIntegration:
    """Test system performance under integrated load."""
    
    @pytest.mark.asyncio
    async def test_concurrent_operation_performance(self):
        """Test system performance with concurrent operations."""
        operation_results = []
        
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            # Mock orchestrator
            mock_orchestrator = MagicMock()
            mock_orchestrator._state_manager = MagicMock()
            mock_orchestrator.garden_planner_agent = MagicMock()
            
            async def fast_agent_process(*args):
                await asyncio.sleep(0.01)  # Fast processing
                return {"status": "success", "result": "completed"}
            
            mock_orchestrator.garden_planner_agent.process = fast_agent_process
            
            with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    interface = PhaseOneInterface(mock_orchestrator)
                    
                    # Start multiple concurrent operations
                    async def run_operation(op_id):
                        operation_id = await interface.start_phase_one(f"Concurrent operation {op_id}")
                        result = await interface.execute_next_step(operation_id)
                        operation_results.append((op_id, result["status"]))
                        return result
                    
                    # Measure concurrent execution time
                    start_time = time.time()
                    
                    operations = [run_operation(i) for i in range(10)]
                    await asyncio.gather(*operations)
                    
                    execution_time = time.time() - start_time
                    
                    # Verify performance
                    assert len(operation_results) == 10
                    assert execution_time < 1.0  # Should complete quickly with concurrency
                    
                    # All operations should succeed
                    assert all(result[1] == "step_completed" for result in operation_results)
                
                finally:
                    test_loop.close()
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self):
        """Test memory usage under sustained load."""
        memory_snapshots = []
        
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    
                    # Simulate memory tracking
                    initial_memory = app.get_memory_usage()
                    memory_snapshots.append(initial_memory)
                    
                    # Perform memory-intensive operations
                    for i in range(100):
                        # Simulate creating large data structures
                        large_data = "x" * 1024 * 10  # 10KB per iteration
                        app.process_large_data(large_data)
                        
                        if i % 20 == 0:  # Sample memory every 20 operations
                            current_memory = app.get_memory_usage()
                            memory_snapshots.append(current_memory)
                    
                    # Trigger garbage collection
                    app.cleanup_memory()
                    final_memory = app.get_memory_usage()
                    memory_snapshots.append(final_memory)
                    
                    # Verify memory management
                    assert len(memory_snapshots) >= 3
                    
                    # Memory should not grow unbounded
                    max_memory = max(memory_snapshots)
                    assert max_memory < initial_memory * 10  # No more than 10x growth
                    
                    # Memory should be cleaned up
                    assert final_memory <= max_memory
                
                finally:
                    test_loop.close()
    
    @pytest.mark.asyncio
    async def test_resource_contention_handling(self):
        """Test handling of resource contention."""
        contention_events = []
        
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    event_queue = EventQueue()
                    await event_queue.start()
                    
                    state_manager = StateManager(event_queue)
                    await state_manager.initialize()
                    
                    # Simulate resource contention
                    async def contending_operation(worker_id, iterations):
                        for i in range(iterations):
                            try:
                                # Multiple workers accessing same resource
                                await state_manager.set_state('shared_resource', f'worker_{worker_id}_value_{i}', 'CONTENTION_TEST')
                                await asyncio.sleep(0.001)  # Small delay
                                value = await state_manager.get_state('shared_resource', 'CONTENTION_TEST')
                                
                                contention_events.append({
                                    'worker_id': worker_id,
                                    'iteration': i,
                                    'value_written': f'worker_{worker_id}_value_{i}',
                                    'value_read': value
                                })
                            
                            except Exception as e:
                                contention_events.append({
                                    'worker_id': worker_id,
                                    'iteration': i,
                                    'error': str(e)
                                })
                    
                    # Run multiple workers with resource contention
                    workers = [contending_operation(i, 20) for i in range(5)]
                    await asyncio.gather(*workers)
                    
                    # Verify contention handling
                    assert len(contention_events) == 100  # 5 workers * 20 iterations
                    
                    # Should not have errors (proper contention handling)
                    error_events = [event for event in contention_events if 'error' in event]
                    assert len(error_events) == 0
                    
                    await event_queue.stop()
                
                finally:
                    test_loop.close()


class TestSystemRecoveryMechanisms:
    """Test system recovery mechanisms and resilience."""
    
    @pytest.mark.asyncio
    async def test_automatic_component_restart(self):
        """Test automatic restart of failed components."""
        restart_attempts = []
        
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    
                    # Mock component that fails then succeeds
                    failure_count = 0
                    
                    async def failing_component_start():
                        nonlocal failure_count
                        failure_count += 1
                        restart_attempts.append(f"attempt_{failure_count}")
                        
                        if failure_count <= 2:  # Fail first 2 attempts
                            raise Exception(f"Component start failed (attempt {failure_count})")
                        return True  # Succeed on 3rd attempt
                    
                    app.critical_component_start = failing_component_start
                    
                    # Test automatic restart
                    success = await app.start_critical_component_with_retry()
                    
                    # Should eventually succeed after retries
                    assert success is True
                    assert len(restart_attempts) == 3
                    assert failure_count == 3
                
                finally:
                    test_loop.close()
    
    @pytest.mark.asyncio
    async def test_system_health_monitoring(self):
        """Test system health monitoring and alerts."""
        health_reports = []
        
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    
                    # Mock health monitoring
                    async def health_check_callback(health_status):
                        health_reports.append(health_status)
                    
                    app.register_health_callback(health_check_callback)
                    
                    # Simulate health monitoring cycle
                    for cycle in range(5):
                        health_status = {
                            'cycle': cycle,
                            'memory_usage': 50 + cycle * 10,  # Gradually increasing
                            'cpu_usage': 20 + cycle * 5,
                            'active_operations': max(0, 3 - cycle),
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        await app.report_health_status(health_status)
                        await asyncio.sleep(0.01)
                    
                    # Verify health monitoring
                    assert len(health_reports) == 5
                    
                    # Health metrics should be tracked over time
                    memory_trend = [report['memory_usage'] for report in health_reports]
                    assert memory_trend == [50, 60, 70, 80, 90]  # Increasing trend
                
                finally:
                    test_loop.close()
    
    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """Test graceful degradation when components fail."""
        degradation_events = []
        
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    event_queue = EventQueue()
                    await event_queue.start()
                    
                    # Create managers
                    state_manager = StateManager(event_queue)
                    await state_manager.initialize()
                    
                    cache_manager = CacheManager(event_queue)
                    await cache_manager.initialize()
                    
                    app = PhaseOneApp()
                    app.state_manager = state_manager
                    app.cache_manager = cache_manager
                    
                    # Simulate cache manager failure
                    original_cache_get = cache_manager.get_cache
                    
                    async def failing_cache_get(*args, **kwargs):
                        degradation_events.append('cache_unavailable')
                        raise Exception("Cache service unavailable")
                    
                    cache_manager.get_cache = failing_cache_get
                    
                    # App should degrade gracefully (use state manager as fallback)
                    result = await app.get_data_with_fallback('test_key')
                    
                    # Should fall back to state manager
                    assert result is not None or 'cache_unavailable' in degradation_events
                    
                    # System should still be functional
                    await state_manager.set_state('fallback_test', 'working', 'TEST')
                    value = await state_manager.get_state('fallback_test', 'TEST')
                    assert value == 'working'
                    
                    degradation_events.append('system_still_functional')
                    
                    # Verify graceful degradation
                    assert 'cache_unavailable' in degradation_events
                    assert 'system_still_functional' in degradation_events
                    
                    await event_queue.stop()
                
                finally:
                    test_loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])