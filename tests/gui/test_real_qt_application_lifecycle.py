"""
Real Qt Application Lifecycle Tests

This module tests REAL Qt application lifecycle management WITHOUT mocks:
- Real QApplication initialization and singleton management
- Real qasync event loop integration with background loops
- Real GUI component initialization and coordination
- Real application shutdown sequences

These tests expose actual Qt/qasync integration issues that mocked tests hide.
"""

import pytest
import asyncio
import threading
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import qasync

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from run_phase_one import PhaseOneApp
from resources.events.loop_management import EventLoopManager


class TestRealQApplicationLifecycle:
    """Test REAL QApplication lifecycle without mocks."""
    
    def test_real_qapplication_singleton_creation(self):
        """Test REAL QApplication singleton creation and management."""
        # Clean slate
        EventLoopManager.cleanup()
        
        # Store original state
        original_app = QApplication.instance()
        
        try:
            # If no QApplication exists, PhaseOneApp should create one
            if original_app is None:
                app = PhaseOneApp()
                
                # Verify REAL QApplication was created
                assert app.app is not None
                assert isinstance(app.app, QApplication)
                assert QApplication.instance() is app.app
                
                # Verify event loop setup
                assert hasattr(app, 'loop')
                assert app.loop is not None
                assert isinstance(app.loop, asyncio.AbstractEventLoop)
                
            else:
                # If QApplication already exists, PhaseOneApp should reuse it
                app = PhaseOneApp()
                
                # Should reuse existing instance
                assert app.app is original_app
                assert QApplication.instance() is original_app
                
        finally:
            EventLoopManager.cleanup()
            
            # Only quit if we created a new application
            if original_app is None and QApplication.instance():
                QApplication.instance().quit()
    
    def test_real_qasync_integration(self):
        """Test REAL qasync integration with PhaseOneApp."""
        EventLoopManager.cleanup()
        
        original_app = QApplication.instance()
        phase_app = None
        
        try:
            # Create REAL PhaseOneApp
            phase_app = PhaseOneApp()
            
            # Create REAL qasync loop
            qasync_loop = qasync.QEventLoop(phase_app.app)
            
            # Register as primary loop
            result = EventLoopManager.set_primary_loop(qasync_loop)
            assert result is True
            
            # Verify the loop is properly registered
            primary_loop = EventLoopManager.get_primary_loop()
            assert primary_loop is qasync_loop
            
            # Verify it's actually a qasync loop
            assert isinstance(primary_loop, qasync.QEventLoop)
            
            # Test that get_loop_for_thread returns qasync loop in main thread
            thread_loop = EventLoopManager.get_loop_for_thread()
            assert thread_loop is qasync_loop
            
        finally:
            if phase_app and hasattr(phase_app, 'loop'):
                if not phase_app.loop.is_closed():
                    phase_app.loop.close()
            
            EventLoopManager.cleanup()
            
            if original_app is None and QApplication.instance():
                QApplication.instance().quit()
    
    @pytest.mark.asyncio
    async def test_real_async_setup_lifecycle(self):
        """Test REAL async setup lifecycle with all components."""
        EventLoopManager.cleanup()
        
        original_app = QApplication.instance()
        phase_app = None
        
        try:
            # Create REAL PhaseOneApp
            phase_app = PhaseOneApp()
            
            # Run REAL async setup - this should:
            # 1. Initialize all resource managers
            # 2. Start background thread
            # 3. Set up monitoring systems
            await phase_app.setup_async()
            
            # Verify primary loop registration
            primary_loop = EventLoopManager.get_primary_loop()
            assert primary_loop is not None
            assert primary_loop is phase_app.loop
            
            # Verify background thread was created and is running
            assert hasattr(phase_app, '_background_thread')
            assert phase_app._background_thread is not None
            assert phase_app._background_thread.is_alive()
            
            # Give background thread time to register its loop
            await asyncio.sleep(0.3)
            
            # Verify background loop is registered and different from main
            background_loop = EventLoopManager.get_background_loop()
            assert background_loop is not None
            assert id(background_loop) != id(primary_loop)
            
            # Verify event queue was started
            assert hasattr(phase_app, 'event_queue')
            assert phase_app.event_queue._running
            
            # Verify resource managers were initialized
            assert hasattr(phase_app, 'state_manager')
            assert hasattr(phase_app, 'context_manager')
            assert hasattr(phase_app, 'cache_manager')
            assert hasattr(phase_app, 'metrics_manager')
            assert hasattr(phase_app, 'circuit_registry')
            
            # Verify circuit registry can start monitoring (this was failing before)
            await phase_app.circuit_registry.start_monitoring()
            
            # Let monitoring run briefly
            await asyncio.sleep(0.1)
            
            # Stop monitoring
            await phase_app.circuit_registry.stop_monitoring()
            
        finally:
            # Proper cleanup
            if phase_app:
                # Stop background monitoring
                phase_app._shutdown_background = True
                
                # Stop background thread
                if hasattr(phase_app, '_background_thread') and phase_app._background_thread.is_alive():
                    phase_app._background_thread.join(timeout=3.0)
                
                # Stop event queue
                if hasattr(phase_app, 'event_queue') and phase_app.event_queue._running:
                    await phase_app.event_queue.stop()
                
                # Stop circuit monitoring
                if hasattr(phase_app, 'circuit_registry'):
                    try:
                        await phase_app.circuit_registry.stop_monitoring()
                    except:
                        pass
            
            EventLoopManager.cleanup()
            
            if original_app is None and QApplication.instance():
                QApplication.instance().quit()


class TestRealGUIEventLoopIntegration:
    """Test REAL GUI event loop integration scenarios."""
    
    def test_real_gui_async_operation_context(self):
        """Test REAL GUI async operations stay in correct qasync context."""
        EventLoopManager.cleanup()
        
        original_app = QApplication.instance()
        context_violations = []
        operation_results = []
        
        try:
            # Create REAL QApplication and qasync loop
            if original_app is None:
                app = QApplication([])
            else:
                app = original_app
            
            qasync_loop = qasync.QEventLoop(app)
            EventLoopManager.set_primary_loop(qasync_loop)
            
            async def gui_async_operation():
                """Simulated GUI async operation that should stay in qasync loop."""
                current_loop = asyncio.get_running_loop()
                expected_loop = EventLoopManager.get_primary_loop()
                
                if current_loop != expected_loop:
                    context_violations.append(
                        f"GUI operation in wrong context: {id(current_loop)} vs {id(expected_loop)}"
                    )
                
                # Verify we're in qasync loop
                if not isinstance(current_loop, qasync.QEventLoop):
                    context_violations.append(
                        f"GUI operation not in qasync loop: {type(current_loop)}"
                    )
                
                operation_results.append("gui_operation_completed")
                return "gui_result"
            
            # Run the operation in qasync loop
            try:
                asyncio.set_event_loop(qasync_loop)
                result = qasync_loop.run_until_complete(gui_async_operation())
                
                # Verify operation completed successfully
                assert result == "gui_result"
                assert "gui_operation_completed" in operation_results
                assert len(context_violations) == 0, f"Context violations: {context_violations}"
                
            finally:
                qasync_loop.close()
            
        finally:
            EventLoopManager.cleanup()
            
            if original_app is None and QApplication.instance():
                QApplication.instance().quit()
    
    def test_real_background_monitoring_isolation(self):
        """Test REAL background monitoring stays isolated from GUI loop."""
        EventLoopManager.cleanup()
        
        original_app = QApplication.instance()
        gui_operations = []
        background_operations = []
        context_violations = []
        
        def background_monitoring_thread():
            """REAL background thread that should stay isolated."""
            try:
                # Create dedicated background loop
                bg_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(bg_loop)
                EventLoopManager.set_background_loop(bg_loop)
                
                async def background_monitoring():
                    current_loop = asyncio.get_running_loop()
                    expected_loop = EventLoopManager.get_background_loop()
                    
                    if current_loop != expected_loop:
                        context_violations.append(
                            f"Background monitoring in wrong context: {id(current_loop)} vs {id(expected_loop)}"
                        )
                    
                    # Verify we're NOT in qasync loop
                    if isinstance(current_loop, qasync.QEventLoop):
                        context_violations.append("Background monitoring incorrectly in qasync loop")
                    
                    background_operations.append("background_monitoring_completed")
                    return "background_result"
                
                result = bg_loop.run_until_complete(background_monitoring())
                bg_loop.close()
                
                background_operations.append(f"background_result: {result}")
                
            except Exception as e:
                context_violations.append(f"Background thread error: {e}")
        
        try:
            # Setup REAL GUI loop
            if original_app is None:
                app = QApplication([])
            else:
                app = original_app
                
            qasync_loop = qasync.QEventLoop(app)
            EventLoopManager.set_primary_loop(qasync_loop)
            
            # Start background thread
            thread = threading.Thread(target=background_monitoring_thread)
            thread.start()
            
            # Simulate GUI operation in qasync loop
            async def gui_operation():
                current_loop = asyncio.get_running_loop()
                expected_loop = EventLoopManager.get_primary_loop()
                
                if current_loop != expected_loop:
                    context_violations.append(
                        f"GUI operation in wrong context: {id(current_loop)} vs {id(expected_loop)}"
                    )
                
                gui_operations.append("gui_operation_completed")
                return "gui_result"
            
            # Run GUI operation
            asyncio.set_event_loop(qasync_loop)
            gui_result = qasync_loop.run_until_complete(gui_operation())
            
            # Wait for background thread
            thread.join(timeout=5.0)
            
            # Verify both operations completed in correct contexts
            assert len(context_violations) == 0, f"Context violations: {context_violations}"
            assert "gui_operation_completed" in gui_operations
            assert "background_monitoring_completed" in background_operations
            assert gui_result == "gui_result"
            
            qasync_loop.close()
            
        finally:
            EventLoopManager.cleanup()
            
            if original_app is None and QApplication.instance():
                QApplication.instance().quit()
    
    async def test_real_phase_one_app_shutdown_sequence(self):
        """Test REAL PhaseOneApp shutdown sequence."""
        EventLoopManager.cleanup()
        
        original_app = QApplication.instance()
        phase_app = None
        shutdown_events = []
        
        try:
            # Create and setup REAL PhaseOneApp
            phase_app = PhaseOneApp()
            
            # Partial async setup for testing
            await phase_app.setup_async()
            
            # Verify everything is running
            assert phase_app.event_queue._running
            assert phase_app._background_thread.is_alive()
            
            # Record initial state
            shutdown_events.append("app_fully_initialized")
            
            # Simulate shutdown sequence
            phase_app._shutdown_background = True
            shutdown_events.append("background_shutdown_signaled")
            
            # Stop event queue
            await phase_app.event_queue.stop()
            shutdown_events.append("event_queue_stopped")
            
            # Stop circuit monitoring
            if hasattr(phase_app, 'circuit_registry'):
                await phase_app.circuit_registry.stop_monitoring()
                shutdown_events.append("circuit_monitoring_stopped")
            
            # Wait for background thread to stop
            if phase_app._background_thread.is_alive():
                phase_app._background_thread.join(timeout=3.0)
            
            shutdown_events.append("background_thread_stopped")
            
            # Verify clean shutdown
            assert not phase_app.event_queue._running
            assert not phase_app._background_thread.is_alive() or not phase_app._background_thread.is_alive()
            
            shutdown_events.append("shutdown_complete")
            
            # Verify shutdown sequence was correct
            expected_sequence = [
                "app_fully_initialized",
                "background_shutdown_signaled", 
                "event_queue_stopped",
                "circuit_monitoring_stopped",
                "background_thread_stopped",
                "shutdown_complete"
            ]
            
            assert shutdown_events == expected_sequence
            
        finally:
            # Ensure cleanup even if test fails
            if phase_app:
                try:
                    phase_app._shutdown_background = True
                    if hasattr(phase_app, 'event_queue') and phase_app.event_queue._running:
                        await phase_app.event_queue.stop()
                    if hasattr(phase_app, '_background_thread') and phase_app._background_thread.is_alive():
                        phase_app._background_thread.join(timeout=2.0)
                except:
                    pass
            
            EventLoopManager.cleanup()
            
            if original_app is None and QApplication.instance():
                QApplication.instance().quit()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])