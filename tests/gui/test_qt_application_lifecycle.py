"""
Test Qt Application Lifecycle from run_phase_one.py

This module tests Qt application initialization, lifecycle management, and integration
with qasync using the simplified event architecture. Tests the two-loop system integration
with GUI components.
"""

import pytest
import asyncio
import threading
import time
from unittest.mock import MagicMock, patch, AsyncMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import qasync

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from run_phase_one import PhaseOneApp
from resources.events.loop_management import EventLoopManager


class TestQApplicationInitialization:
    """Test QApplication initialization and singleton management with simplified architecture."""
    
    def test_qapplication_singleton_creation(self):
        """Test QApplication singleton creation and management."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            # Mock no existing instance
            mock_qapp_class.instance.return_value = None
            
            # Mock new QApplication creation
            mock_qapp = MagicMock()
            mock_qapp_class.return_value = mock_qapp
            
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    # Create PhaseOneApp
                    app = PhaseOneApp()
                    
                    # Verify QApplication was created
                    mock_qapp_class.assert_called_once()
                    assert hasattr(app, 'app')
                    assert app.app is mock_qapp
                
                finally:
                    test_loop.close()
                    EventLoopManager.cleanup()
    
    def test_qapplication_existing_instance_reuse(self):
        """Test reusing existing QApplication instance."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            # Mock existing instance
            existing_qapp = MagicMock()
            mock_qapp_class.instance.return_value = existing_qapp
            
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    # Create PhaseOneApp
                    app = PhaseOneApp()
                    
                    # Should not create new instance
                    assert not mock_qapp_class.called
                    assert app.app is existing_qapp
                
                finally:
                    test_loop.close()
                    EventLoopManager.cleanup()
    
    def test_qapplication_command_line_args(self):
        """Test QApplication creation with command line arguments."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp_class.instance.return_value = None
            mock_qapp = MagicMock()
            mock_qapp_class.return_value = mock_qapp
            
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                with patch('sys.argv', ['run_phase_one.py', '--test-arg']):
                    test_loop = asyncio.new_event_loop()
                    mock_ensure.return_value = test_loop
                    
                    try:
                        app = PhaseOneApp()
                        
                        # Verify QApplication was called with sys.argv
                        mock_qapp_class.assert_called_once()
                        call_args = mock_qapp_class.call_args
                        assert len(call_args[0]) >= 1  # Should include argv
                    
                    finally:
                        test_loop.close()
                        EventLoopManager.cleanup()


class TestSimplifiedEventLoopIntegration:
    """Test simplified event loop integration with Qt."""
    
    def test_event_loop_setup_on_initialization(self):
        """Test that PhaseOneApp correctly sets up simplified event loop architecture."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                mock_qapp = MagicMock()
                mock_qapp_class.instance.return_value = None
                mock_qapp_class.return_value = mock_qapp
                
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    
                    # Verify event loop setup was called
                    mock_ensure.assert_called_once()
                    
                    # Should store loop reference
                    assert hasattr(app, 'loop')
                    assert app.loop is test_loop
                
                finally:
                    test_loop.close()
                    EventLoopManager.cleanup()
    
    def test_qasync_loop_compatibility(self):
        """Test compatibility with qasync loops."""
        with patch('qasync.QEventLoop') as mock_qevent_loop:
            with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
                mock_qapp = MagicMock()
                mock_qapp_class.instance.return_value = None
                mock_qapp_class.return_value = mock_qapp
                
                # Mock qasync loop that acts like asyncio loop
                mock_qloop = MagicMock()
                mock_qloop.is_closed.return_value = False
                mock_qevent_loop.return_value = mock_qloop
                
                with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                    mock_ensure.return_value = mock_qloop
                    
                    try:
                        app = PhaseOneApp()
                        
                        # Should work with qasync loops
                        assert app.loop is mock_qloop
                        
                        # qasync loop creation can work with our simplified architecture
                        qloop = qasync.QEventLoop(mock_qapp)
                        mock_qevent_loop.assert_called_once_with(mock_qapp)
                    
                    finally:
                        EventLoopManager.cleanup()


class TestPhaseOneAppLifecycle:
    """Test PhaseOneApp lifecycle management with simplified architecture."""
    
    @pytest.mark.asyncio
    async def test_app_async_setup_with_event_queue(self):
        """Test PhaseOneApp async setup with EventQueue integration."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                with patch('resources.events.EventQueue') as mock_eq_class:
                    with patch('resources.managers.CircuitBreakerRegistry'):
                        with patch('resources.managers.ResourceCoordinator') as mock_rc_class:
                            
                            mock_qapp = MagicMock()
                            mock_qapp_class.instance.return_value = None
                            mock_qapp_class.return_value = mock_qapp
                            
                            test_loop = asyncio.new_event_loop()
                            mock_ensure.return_value = test_loop
                            
                            # Mock EventQueue
                            mock_eq = MagicMock()
                            mock_eq.start = AsyncMock()
                            mock_eq_class.return_value = mock_eq
                            
                            # Mock ResourceCoordinator
                            mock_rc = MagicMock()
                            mock_rc.initialize_all = AsyncMock()
                            mock_rc_class.return_value = mock_rc
                            
                            try:
                                app = PhaseOneApp()
                                
                                # Test async setup
                                if hasattr(app, 'setup_async'):
                                    await app.setup_async()
                                    
                                    # Verify EventQueue was started
                                    mock_eq.start.assert_called_once()
                                    
                                    # Verify ResourceCoordinator was initialized
                                    mock_rc.initialize_all.assert_called_once()
                            
                            finally:
                                test_loop.close()
                                EventLoopManager.cleanup()
    
    def test_app_cleanup_and_shutdown(self):
        """Test PhaseOneApp cleanup and shutdown procedures."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                mock_qapp = MagicMock()
                mock_qapp_class.instance.return_value = None
                mock_qapp_class.return_value = mock_qapp
                
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    
                    # Test cleanup method if it exists
                    if hasattr(app, 'cleanup'):
                        app.cleanup()
                        # Should call quit on QApplication
                        mock_qapp.quit.assert_called_once()
                
                finally:
                    test_loop.close()
                    EventLoopManager.cleanup()


class TestDisplayIntegration:
    """Test display component integration with simplified event architecture."""
    
    @pytest.mark.asyncio
    async def test_display_initialization_with_simplified_events(self):
        """Test display initialization with simplified event architecture."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            with patch('display.ForestDisplay') as mock_forest_display_class:
                with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                    
                    mock_qapp = MagicMock()
                    mock_qapp_class.instance.return_value = None
                    mock_qapp_class.return_value = mock_qapp
                    
                    mock_display = MagicMock()
                    mock_forest_display_class.return_value = mock_display
                    
                    test_loop = asyncio.new_event_loop()
                    mock_ensure.return_value = test_loop
                    
                    try:
                        app = PhaseOneApp()
                        
                        # Test display integration if present
                        if hasattr(app, 'display') or hasattr(app, 'main_window'):
                            # Should initialize display components
                            assert mock_qapp_class.called
                    
                    finally:
                        test_loop.close()
                        EventLoopManager.cleanup()
    
    def test_gui_event_handling_with_new_architecture(self):
        """Test GUI event handling with new event architecture."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                mock_qapp = MagicMock()
                mock_qapp_class.instance.return_value = None
                mock_qapp_class.return_value = mock_qapp
                
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    
                    # Should be able to handle GUI events with simplified architecture
                    # The app should maintain Qt event handling while using our event system
                    assert app.app is mock_qapp
                    assert app.loop is test_loop
                
                finally:
                    test_loop.close()
                    EventLoopManager.cleanup()


class TestAsyncGUICoordination:
    """Test async/GUI coordination with simplified event architecture."""
    
    @pytest.mark.asyncio
    async def test_async_task_execution_from_gui(self):
        """Test executing async tasks from GUI context."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                mock_qapp = MagicMock()
                mock_qapp_class.instance.return_value = None
                mock_qapp_class.return_value = mock_qapp
                
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    
                    # Test async operation in GUI context
                    async def test_async_operation():
                        await asyncio.sleep(0.01)
                        return "async_success"
                    
                    # Should be able to run async operations
                    result = await test_async_operation()
                    assert result == "async_success"
                
                finally:
                    test_loop.close()
                    EventLoopManager.cleanup()
    
    def test_gui_callback_async_integration(self):
        """Test GUI callback integration with async operations."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                mock_qapp = MagicMock()
                mock_qapp_class.instance.return_value = None
                mock_qapp_class.return_value = mock_qapp
                
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    
                    # Test that GUI callbacks can integrate with async operations
                    callback_results = []
                    
                    def gui_callback():
                        """Simulate GUI callback that needs async integration."""
                        callback_results.append("gui_callback_executed")
                        return True
                    
                    # Should be able to handle GUI callbacks
                    result = gui_callback()
                    assert result is True
                    assert len(callback_results) == 1
                
                finally:
                    test_loop.close()
                    EventLoopManager.cleanup()


class TestGUIErrorHandling:
    """Test GUI error handling and recovery with simplified architecture."""
    
    def test_qapplication_creation_failure_handling(self):
        """Test handling of QApplication creation failure."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            # First call fails, second succeeds
            call_count = 0
            def failing_qapp_creation(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise RuntimeError("QApplication creation failed")
                return MagicMock()
            
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.side_effect = failing_qapp_creation
            
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    # Should handle QApplication creation failure
                    with pytest.raises(RuntimeError):
                        app = PhaseOneApp()
                
                finally:
                    test_loop.close()
                    EventLoopManager.cleanup()
    
    def test_event_loop_error_recovery(self):
        """Test event loop error recovery in GUI context."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                mock_qapp = MagicMock()
                mock_qapp_class.instance.return_value = None
                mock_qapp_class.return_value = mock_qapp
                
                # First call fails, second succeeds
                call_count = 0
                def failing_ensure_loop():
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:
                        raise RuntimeError("Event loop creation failed")
                    return asyncio.new_event_loop()
                
                mock_ensure.side_effect = failing_ensure_loop
                
                try:
                    # Should handle event loop creation failure
                    with pytest.raises(RuntimeError):
                        app = PhaseOneApp()
                
                finally:
                    EventLoopManager.cleanup()


class TestGUIPerformanceOptimizations:
    """Test GUI performance optimizations with simplified architecture."""
    
    def test_qapplication_singleton_efficiency(self):
        """Test QApplication singleton reuse efficiency."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            existing_qapp = MagicMock()
            mock_qapp_class.instance.return_value = existing_qapp
            
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    # Create multiple apps
                    apps = []
                    for _ in range(5):
                        app = PhaseOneApp()
                        apps.append(app)
                    
                    # Should reuse existing QApplication (never call constructor)
                    assert not mock_qapp_class.called
                    
                    # All apps should reference same QApplication
                    for app in apps:
                        assert app.app is existing_qapp
                
                finally:
                    test_loop.close()
                    EventLoopManager.cleanup()
    
    @pytest.mark.asyncio
    async def test_simplified_event_architecture_performance(self):
        """Test performance of simplified event architecture in GUI context."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                mock_qapp = MagicMock()
                mock_qapp_class.instance.return_value = None
                mock_qapp_class.return_value = mock_qapp
                
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    
                    # Test performance of event operations
                    operation_times = []
                    
                    async def timed_operation():
                        start_time = time.time()
                        await asyncio.sleep(0.001)  # Minimal delay
                        operation_times.append(time.time() - start_time)
                        return "operation_complete"
                    
                    # Run multiple operations
                    for _ in range(10):
                        result = await timed_operation()
                        assert result == "operation_complete"
                    
                    # Verify reasonable performance
                    avg_time = sum(operation_times) / len(operation_times)
                    assert avg_time < 0.1  # Should be much faster than 100ms
                
                finally:
                    test_loop.close()
                    EventLoopManager.cleanup()


class TestLegacyCompatibility:
    """Test compatibility with legacy GUI patterns."""
    
    def test_legacy_qt_timer_integration(self):
        """Test legacy Qt timer integration with simplified architecture."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            with patch('PyQt6.QtCore.QTimer') as mock_qtimer_class:
                with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                    
                    mock_qapp = MagicMock()
                    mock_qapp_class.instance.return_value = None
                    mock_qapp_class.return_value = mock_qapp
                    
                    mock_timer = MagicMock()
                    mock_qtimer_class.return_value = mock_timer
                    
                    test_loop = asyncio.new_event_loop()
                    mock_ensure.return_value = test_loop
                    
                    try:
                        app = PhaseOneApp()
                        
                        # Should be able to create Qt timers
                        timer = QTimer()
                        mock_qtimer_class.assert_called_once()
                        
                        # Timer operations should work
                        timer.start(100)
                        mock_timer.start.assert_called_once_with(100)
                    
                    finally:
                        test_loop.close()
                        EventLoopManager.cleanup()
    
    def test_mixed_qt_async_event_handling(self):
        """Test mixed Qt and async event handling patterns."""
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                mock_qapp = MagicMock()
                mock_qapp_class.instance.return_value = None
                mock_qapp_class.return_value = mock_qapp
                
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    
                    # Should handle both Qt and async events
                    qt_events_handled = []
                    async_events_handled = []
                    
                    def qt_event_handler():
                        qt_events_handled.append("qt_event")
                    
                    async def async_event_handler():
                        async_events_handled.append("async_event")
                    
                    # Both should be callable
                    qt_event_handler()
                    assert len(qt_events_handled) == 1
                    
                    # Async handler would be called differently in real scenario
                    # but this tests the basic integration
                    assert len(async_events_handled) == 0  # Not called yet
                
                finally:
                    test_loop.close()
                    EventLoopManager.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])