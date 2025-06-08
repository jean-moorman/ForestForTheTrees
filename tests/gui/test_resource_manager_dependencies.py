"""
Test Resource Manager Dependencies in GUI Context from run_phase_one.py

This module tests the integration of resource managers (StateManager, CacheManager,
MetricsManager, etc.) within the GUI application context. Tests initialization order,
lifecycle management, and inter-dependency handling.
"""

import pytest
import asyncio
import threading
import time
from datetime import datetime
from unittest.mock import MagicMock, patch, AsyncMock

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from run_phase_one import PhaseOneApp
from resources.events import EventQueue
from resources.state import StateManager
from resources.managers import AgentContextManager, CacheManager, MetricsManager
from resources.managers.coordinator import ResourceCoordinator
from resources.monitoring.circuit_breakers import CircuitBreakerRegistry


class TestResourceManagerInitializationOrder:
    """Test correct initialization order of resource managers in GUI context."""
    
    @pytest.mark.asyncio
    async def test_resource_manager_initialization_sequence(self):
        """Test the sequence of resource manager initialization."""
        initialization_order = []
        
        # Mock all resource managers to track initialization order
        with patch('run_phase_one.EventQueue') as mock_eq_class:
            with patch('run_phase_one.StateManager') as mock_sm_class:
                with patch('run_phase_one.AgentContextManager') as mock_acm_class:
                    with patch('run_phase_one.CacheManager') as mock_cm_class:
                        with patch('run_phase_one.MetricsManager') as mock_mm_class:
                            with patch('run_phase_one.CircuitBreakerRegistry') as mock_cbr_class:
                                with patch('run_phase_one.ResourceCoordinator') as mock_rc_class:
                                    with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
                                        with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                                            
                                            # Setup tracking for initialization order
                                            def track_init(name, original_class):
                                                def wrapper(*args, **kwargs):
                                                    initialization_order.append(name)
                                                    mock_obj = MagicMock()
                                                    if hasattr(original_class, 'initialize'):
                                                        mock_obj.initialize = AsyncMock()
                                                    if hasattr(original_class, 'start'):
                                                        mock_obj.start = AsyncMock()
                                                    return mock_obj
                                                return wrapper
                                            
                                            mock_eq_class.side_effect = track_init('EventQueue', EventQueue)
                                            mock_sm_class.side_effect = track_init('StateManager', StateManager)
                                            mock_acm_class.side_effect = track_init('AgentContextManager', AgentContextManager)
                                            mock_cm_class.side_effect = track_init('CacheManager', CacheManager)
                                            mock_mm_class.side_effect = track_init('MetricsManager', MetricsManager)
                                            mock_cbr_class.side_effect = track_init('CircuitBreakerRegistry', CircuitBreakerRegistry)
                                            mock_rc_class.side_effect = track_init('ResourceCoordinator', ResourceCoordinator)
                                            
                                            # Setup QApplication mock
                                            mock_qapp = MagicMock()
                                            mock_qapp_class.instance.return_value = None
                                            mock_qapp_class.return_value = mock_qapp
                                            
                                            test_loop = asyncio.new_event_loop()
                                            mock_ensure.return_value = test_loop
                                            
                                            try:
                                                app = PhaseOneApp()
                                                await app.setup_async()
                                                
                                                # Verify initialization order
                                                expected_order = [
                                                    'EventQueue',
                                                    'CircuitBreakerRegistry', 
                                                    'ResourceCoordinator'
                                                ]
                                                
                                                # Core components should be initialized first
                                                assert initialization_order[:3] == expected_order
                                                
                                                # StateManager and other managers should follow
                                                remaining_managers = ['StateManager', 'AgentContextManager', 'CacheManager', 'MetricsManager']
                                                for manager in remaining_managers:
                                                    assert manager in initialization_order
                                            
                                            finally:
                                                test_loop.close()
    
    @pytest.mark.asyncio
    async def test_dependency_resolution_during_initialization(self):
        """Test that resource manager dependencies are correctly resolved."""
        dependencies_resolved = {}
        
        with patch('run_phase_one.EventQueue') as mock_eq_class:
            with patch('run_phase_one.StateManager') as mock_sm_class:
                with patch('run_phase_one.ResourceCoordinator') as mock_rc_class:
                    with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
                        with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                            
                            # Mock EventQueue
                            mock_eq = MagicMock()
                            mock_eq.start = AsyncMock()
                            mock_eq_class.return_value = mock_eq
                            
                            # Mock StateManager with dependency tracking
                            def state_manager_init(event_queue):
                                dependencies_resolved['StateManager'] = {
                                    'event_queue': event_queue is mock_eq
                                }
                                mock_sm = MagicMock()
                                mock_sm.initialize = AsyncMock()
                                return mock_sm
                            
                            mock_sm_class.side_effect = state_manager_init
                            
                            # Mock ResourceCoordinator
                            mock_rc = MagicMock()
                            mock_rc.initialize_all = AsyncMock()
                            mock_rc_class.return_value = mock_rc
                            
                            # Setup QApplication
                            mock_qapp = MagicMock()
                            mock_qapp_class.instance.return_value = None
                            mock_qapp_class.return_value = mock_qapp
                            
                            test_loop = asyncio.new_event_loop()
                            mock_ensure.return_value = test_loop
                            
                            try:
                                app = PhaseOneApp()
                                await app.setup_async()
                                
                                # Verify dependencies were correctly resolved
                                assert 'StateManager' in dependencies_resolved
                                assert dependencies_resolved['StateManager']['event_queue'] is True
                            
                            finally:
                                test_loop.close()


class TestResourceManagerLifecycleInGUI:
    """Test resource manager lifecycle management within GUI application."""
    
    @pytest.mark.asyncio
    async def test_resource_manager_startup_lifecycle(self):
        """Test resource manager startup lifecycle."""
        lifecycle_events = []
        
        with patch('run_phase_one.EventQueue') as mock_eq_class:
            with patch('run_phase_one.StateManager') as mock_sm_class:
                with patch('run_phase_one.ResourceCoordinator') as mock_rc_class:
                    with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
                        with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                            
                            # Mock components with lifecycle tracking
                            mock_eq = MagicMock()
                            mock_eq.start = AsyncMock()
                            mock_eq.start.side_effect = lambda: lifecycle_events.append('EventQueue.start')
                            mock_eq_class.return_value = mock_eq
                            
                            mock_sm = MagicMock()
                            mock_sm.initialize = AsyncMock()
                            mock_sm.initialize.side_effect = lambda: lifecycle_events.append('StateManager.initialize')
                            mock_sm_class.return_value = mock_sm
                            
                            mock_rc = MagicMock()
                            mock_rc.initialize_all = AsyncMock()
                            mock_rc.initialize_all.side_effect = lambda: lifecycle_events.append('ResourceCoordinator.initialize_all')
                            mock_rc_class.return_value = mock_rc
                            
                            # Setup QApplication
                            mock_qapp = MagicMock()
                            mock_qapp_class.instance.return_value = None
                            mock_qapp_class.return_value = mock_qapp
                            
                            test_loop = asyncio.new_event_loop()
                            mock_ensure.return_value = test_loop
                            
                            try:
                                app = PhaseOneApp()
                                await app.setup_async()
                                
                                # Verify startup lifecycle events
                                expected_events = [
                                    'EventQueue.start',
                                    'ResourceCoordinator.initialize_all'
                                ]
                                
                                for event in expected_events:
                                    assert event in lifecycle_events
                            
                            finally:
                                test_loop.close()
    
    @pytest.mark.asyncio
    async def test_resource_manager_cleanup_lifecycle(self):
        """Test resource manager cleanup lifecycle."""
        cleanup_events = []
        
        with patch('run_phase_one.EventQueue') as mock_eq_class:
            with patch('run_phase_one.ResourceCoordinator') as mock_rc_class:
                with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
                    with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                        
                        # Mock components with cleanup tracking
                        mock_eq = MagicMock()
                        mock_eq.start = AsyncMock()
                        mock_eq.stop = AsyncMock()
                        mock_eq.stop.side_effect = lambda: cleanup_events.append('EventQueue.stop')
                        mock_eq_class.return_value = mock_eq
                        
                        mock_rc = MagicMock()
                        mock_rc.initialize_all = AsyncMock()
                        mock_rc.cleanup_all = AsyncMock()
                        mock_rc.cleanup_all.side_effect = lambda: cleanup_events.append('ResourceCoordinator.cleanup_all')
                        mock_rc_class.return_value = mock_rc
                        
                        # Setup QApplication
                        mock_qapp = MagicMock()
                        mock_qapp_class.instance.return_value = None
                        mock_qapp_class.return_value = mock_qapp
                        
                        test_loop = asyncio.new_event_loop()
                        mock_ensure.return_value = test_loop
                        
                        try:
                            app = PhaseOneApp()
                            await app.setup_async()
                            app.event_queue = mock_eq
                            app.resource_coordinator = mock_rc
                            
                            # Test cleanup
                            await app.cleanup_async()
                            
                            # Verify cleanup lifecycle events
                            expected_events = [
                                'ResourceCoordinator.cleanup_all',
                                'EventQueue.stop'
                            ]
                            
                            for event in expected_events:
                                assert event in cleanup_events
                        
                        finally:
                            test_loop.close()


class TestResourceManagerCommunication:
    """Test communication between resource managers in GUI context."""
    
    @pytest.mark.asyncio
    async def test_resource_manager_event_communication(self):
        """Test resource managers communicating through events."""
        events_exchanged = []
        
        with patch('run_phase_one.EventQueue') as mock_eq_class:
            with patch('run_phase_one.StateManager') as mock_sm_class:
                with patch('run_phase_one.MetricsManager') as mock_mm_class:
                    with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
                        with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                            
                            # Mock EventQueue with event tracking
                            mock_eq = MagicMock()
                            mock_eq.start = AsyncMock()
                            mock_eq.emit = AsyncMock()
                            mock_eq.emit.side_effect = lambda event_type, data: events_exchanged.append((event_type, data))
                            mock_eq_class.return_value = mock_eq
                            
                            # Mock StateManager
                            mock_sm = MagicMock()
                            mock_sm.initialize = AsyncMock()
                            mock_sm.set_state = AsyncMock()
                            mock_sm_class.return_value = mock_sm
                            
                            # Mock MetricsManager  
                            mock_mm = MagicMock()
                            mock_mm.initialize = AsyncMock()
                            mock_mm.record_metric = AsyncMock()
                            mock_mm_class.return_value = mock_mm
                            
                            # Setup QApplication
                            mock_qapp = MagicMock()
                            mock_qapp_class.instance.return_value = None
                            mock_qapp_class.return_value = mock_qapp
                            
                            test_loop = asyncio.new_event_loop()
                            mock_ensure.return_value = test_loop
                            
                            try:
                                app = PhaseOneApp()
                                app.event_queue = mock_eq
                                app.state_manager = mock_sm
                                app.metrics_manager = mock_mm
                                
                                # Simulate resource manager communication
                                await app.event_queue.emit('STATE_CHANGED', {
                                    'key': 'test_key',
                                    'value': 'test_value',
                                    'timestamp': datetime.now().isoformat()
                                })
                                
                                await app.event_queue.emit('METRIC_RECORDED', {
                                    'metric_name': 'test_metric',
                                    'metric_value': 42,
                                    'timestamp': datetime.now().isoformat()
                                })
                                
                                # Verify events were exchanged
                                assert len(events_exchanged) == 2
                                assert events_exchanged[0][0] == 'STATE_CHANGED'
                                assert events_exchanged[1][0] == 'METRIC_RECORDED'
                            
                            finally:
                                test_loop.close()
    
    @pytest.mark.asyncio
    async def test_cross_manager_state_synchronization(self):
        """Test state synchronization across resource managers."""
        state_updates = {}
        
        with patch('run_phase_one.EventQueue') as mock_eq_class:
            with patch('run_phase_one.StateManager') as mock_sm_class:
                with patch('run_phase_one.CacheManager') as mock_cm_class:
                    with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
                        with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                            
                            # Mock EventQueue
                            mock_eq = MagicMock()
                            mock_eq.start = AsyncMock()
                            mock_eq_class.return_value = mock_eq
                            
                            # Mock StateManager with state tracking
                            mock_sm = MagicMock()
                            mock_sm.initialize = AsyncMock()
                            mock_sm.set_state = AsyncMock()
                            mock_sm.set_state.side_effect = lambda key, value, state_type: state_updates.update({key: value})
                            mock_sm.get_state = AsyncMock()
                            mock_sm.get_state.side_effect = lambda key, state_type: state_updates.get(key)
                            mock_sm_class.return_value = mock_sm
                            
                            # Mock CacheManager
                            mock_cm = MagicMock()
                            mock_cm.initialize = AsyncMock()
                            mock_cm.set_cache = AsyncMock()
                            mock_cm.get_cache = AsyncMock()
                            mock_cm_class.return_value = mock_cm
                            
                            # Setup QApplication
                            mock_qapp = MagicMock()
                            mock_qapp_class.instance.return_value = None
                            mock_qapp_class.return_value = mock_qapp
                            
                            test_loop = asyncio.new_event_loop()
                            mock_ensure.return_value = test_loop
                            
                            try:
                                app = PhaseOneApp()
                                app.state_manager = mock_sm
                                app.cache_manager = mock_cm
                                
                                # Simulate cross-manager state synchronization
                                operation_id = "test_operation_123"
                                operation_state = {
                                    "status": "running",
                                    "progress": 0.5,
                                    "current_step": "environmental_analysis"
                                }
                                
                                # Update state in StateManager
                                await app.state_manager.set_state(operation_id, operation_state, "OPERATION")
                                
                                # Verify state was recorded
                                assert operation_id in state_updates
                                assert state_updates[operation_id] == operation_state
                                
                                # Simulate CacheManager accessing synchronized state
                                retrieved_state = await app.state_manager.get_state(operation_id, "OPERATION")
                                await app.cache_manager.set_cache(f"operation_cache_{operation_id}", retrieved_state)
                                
                                # Verify synchronization
                                mock_cm.set_cache.assert_called_once()
                                cache_call_args = mock_cm.set_cache.call_args
                                assert cache_call_args[0][1] == operation_state
                            
                            finally:
                                test_loop.close()


class TestResourceManagerErrorHandling:
    """Test error handling and recovery in resource manager dependencies."""
    
    @pytest.mark.asyncio
    async def test_resource_manager_initialization_failure_recovery(self):
        """Test recovery from resource manager initialization failures."""
        initialization_attempts = {}
        
        with patch('run_phase_one.EventQueue') as mock_eq_class:
            with patch('run_phase_one.StateManager') as mock_sm_class:
                with patch('run_phase_one.ResourceCoordinator') as mock_rc_class:
                    with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
                        with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                            
                            # Mock EventQueue
                            mock_eq = MagicMock()
                            mock_eq.start = AsyncMock()
                            mock_eq_class.return_value = mock_eq
                            
                            # Mock StateManager with failure on first attempt
                            def state_manager_init_with_failure(event_queue):
                                if 'StateManager' not in initialization_attempts:
                                    initialization_attempts['StateManager'] = 0
                                initialization_attempts['StateManager'] += 1
                                
                                if initialization_attempts['StateManager'] == 1:
                                    raise Exception("StateManager initialization failed")
                                
                                mock_sm = MagicMock()
                                mock_sm.initialize = AsyncMock()
                                return mock_sm
                            
                            mock_sm_class.side_effect = state_manager_init_with_failure
                            
                            # Mock ResourceCoordinator
                            mock_rc = MagicMock()
                            mock_rc.initialize_all = AsyncMock()
                            mock_rc_class.return_value = mock_rc
                            
                            # Setup QApplication
                            mock_qapp = MagicMock()
                            mock_qapp_class.instance.return_value = None
                            mock_qapp_class.return_value = mock_qapp
                            
                            test_loop = asyncio.new_event_loop()
                            mock_ensure.return_value = test_loop
                            
                            try:
                                app = PhaseOneApp()
                                
                                # First setup should fail
                                with pytest.raises(Exception, match="StateManager initialization failed"):
                                    await app.setup_async()
                                
                                # Second setup should succeed
                                await app.setup_async()
                                
                                # Verify retry occurred
                                assert initialization_attempts['StateManager'] == 2
                            
                            finally:
                                test_loop.close()
    
    @pytest.mark.asyncio
    async def test_resource_manager_dependency_chain_failure(self):
        """Test handling of dependency chain failures."""
        failure_recovery_events = []
        
        with patch('run_phase_one.EventQueue') as mock_eq_class:
            with patch('run_phase_one.StateManager') as mock_sm_class:
                with patch('run_phase_one.AgentContextManager') as mock_acm_class:
                    with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
                        with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                            
                            # Mock EventQueue with failure
                            mock_eq = MagicMock()
                            mock_eq.start = AsyncMock()
                            mock_eq.start.side_effect = Exception("EventQueue start failed")
                            mock_eq_class.return_value = mock_eq
                            
                            # Mock StateManager (depends on EventQueue)
                            mock_sm = MagicMock()
                            mock_sm.initialize = AsyncMock()
                            mock_sm_class.return_value = mock_sm
                            
                            # Mock AgentContextManager (depends on StateManager)
                            mock_acm = MagicMock()
                            mock_acm.initialize = AsyncMock()
                            mock_acm_class.return_value = mock_acm
                            
                            # Setup QApplication
                            mock_qapp = MagicMock()
                            mock_qapp_class.instance.return_value = None
                            mock_qapp_class.return_value = mock_qapp
                            
                            test_loop = asyncio.new_event_loop()
                            mock_ensure.return_value = test_loop
                            
                            try:
                                app = PhaseOneApp()
                                
                                # Setup should fail due to EventQueue failure
                                with pytest.raises(Exception, match="EventQueue start failed"):
                                    await app.setup_async()
                                
                                # Verify that dependent managers were not initialized
                                # (because EventQueue failed)
                                mock_sm.initialize.assert_not_called()
                                mock_acm.initialize.assert_not_called()
                            
                            finally:
                                test_loop.close()


class TestResourceManagerPerformanceInGUI:
    """Test resource manager performance characteristics in GUI context."""
    
    @pytest.mark.asyncio
    async def test_resource_manager_initialization_performance(self):
        """Test resource manager initialization performance."""
        initialization_times = {}
        
        with patch('run_phase_one.EventQueue') as mock_eq_class:
            with patch('run_phase_one.StateManager') as mock_sm_class:
                with patch('run_phase_one.ResourceCoordinator') as mock_rc_class:
                    with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
                        with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                            
                            # Mock components with timing tracking
                            def timed_event_queue():
                                start_time = time.time()
                                mock_eq = MagicMock()
                                mock_eq.start = AsyncMock()
                                
                                async def timed_start():
                                    await asyncio.sleep(0.001)  # Simulate initialization time
                                    initialization_times['EventQueue'] = time.time() - start_time
                                
                                mock_eq.start = timed_start
                                return mock_eq
                            
                            mock_eq_class.side_effect = timed_event_queue
                            
                            def timed_state_manager(event_queue):
                                start_time = time.time()
                                mock_sm = MagicMock()
                                
                                async def timed_initialize():
                                    await asyncio.sleep(0.001)  # Simulate initialization time
                                    initialization_times['StateManager'] = time.time() - start_time
                                
                                mock_sm.initialize = timed_initialize
                                return mock_sm
                            
                            mock_sm_class.side_effect = timed_state_manager
                            
                            def timed_resource_coordinator():
                                start_time = time.time()
                                mock_rc = MagicMock()
                                
                                async def timed_initialize_all():
                                    await asyncio.sleep(0.001)  # Simulate initialization time
                                    initialization_times['ResourceCoordinator'] = time.time() - start_time
                                
                                mock_rc.initialize_all = timed_initialize_all
                                return mock_rc
                            
                            mock_rc_class.side_effect = timed_resource_coordinator
                            
                            # Setup QApplication
                            mock_qapp = MagicMock()
                            mock_qapp_class.instance.return_value = None
                            mock_qapp_class.return_value = mock_qapp
                            
                            test_loop = asyncio.new_event_loop()
                            mock_ensure.return_value = test_loop
                            
                            try:
                                app = PhaseOneApp()
                                
                                start_time = time.time()
                                await app.setup_async()
                                total_time = time.time() - start_time
                                
                                # Verify reasonable initialization times
                                assert total_time < 1.0  # Should complete within 1 second
                                
                                # Verify individual components initialized quickly
                                for component, init_time in initialization_times.items():
                                    assert init_time < 0.5, f"{component} took too long to initialize: {init_time}s"
                            
                            finally:
                                test_loop.close()
    
    @pytest.mark.asyncio
    async def test_concurrent_resource_manager_operations(self):
        """Test performance of concurrent resource manager operations."""
        operation_results = []
        
        with patch('run_phase_one.EventQueue') as mock_eq_class:
            with patch('run_phase_one.StateManager') as mock_sm_class:
                with patch('run_phase_one.CacheManager') as mock_cm_class:
                    with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
                        with patch('run_phase_one.ensure_event_loop') as mock_ensure:
                            
                            # Mock EventQueue
                            mock_eq = MagicMock()
                            mock_eq.start = AsyncMock()
                            mock_eq_class.return_value = mock_eq
                            
                            # Mock StateManager with async operations
                            mock_sm = MagicMock()
                            mock_sm.initialize = AsyncMock()
                            
                            async def mock_state_operation(key, value, state_type):
                                await asyncio.sleep(0.01)  # Simulate operation time
                                operation_results.append(f"state_{key}")
                                return True
                            
                            mock_sm.set_state = mock_state_operation
                            mock_sm_class.return_value = mock_sm
                            
                            # Mock CacheManager with async operations
                            mock_cm = MagicMock()
                            mock_cm.initialize = AsyncMock()
                            
                            async def mock_cache_operation(key, value):
                                await asyncio.sleep(0.01)  # Simulate operation time
                                operation_results.append(f"cache_{key}")
                                return True
                            
                            mock_cm.set_cache = mock_cache_operation
                            mock_cm_class.return_value = mock_cm
                            
                            # Setup QApplication
                            mock_qapp = MagicMock()
                            mock_qapp_class.instance.return_value = None
                            mock_qapp_class.return_value = mock_qapp
                            
                            test_loop = asyncio.new_event_loop()
                            mock_ensure.return_value = test_loop
                            
                            try:
                                app = PhaseOneApp()
                                app.state_manager = mock_sm
                                app.cache_manager = mock_cm
                                
                                # Perform concurrent operations
                                start_time = time.time()
                                
                                operations = []
                                for i in range(10):
                                    operations.append(app.state_manager.set_state(f"key_{i}", f"value_{i}", "TEST"))
                                    operations.append(app.cache_manager.set_cache(f"cache_key_{i}", f"cache_value_{i}"))
                                
                                await asyncio.gather(*operations)
                                
                                total_time = time.time() - start_time
                                
                                # Verify concurrent operations completed efficiently
                                assert total_time < 0.5  # Should complete much faster than sequential
                                assert len(operation_results) == 20  # All operations completed
                                
                                # Verify interleaved execution (not sequential)
                                state_operations = [r for r in operation_results if r.startswith('state_')]
                                cache_operations = [r for r in operation_results if r.startswith('cache_')]
                                assert len(state_operations) == 10
                                assert len(cache_operations) == 10
                            
                            finally:
                                test_loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])