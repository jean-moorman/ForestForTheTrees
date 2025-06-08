"""
Real Event Loop Architecture Integration Tests

This module tests the actual two-loop architecture WITHOUT mocks to verify:
- Real qasync + background loop coordination
- Thread boundary enforcement  
- Loop ownership violations detection
- Actual coordination between main and background loops

These tests use REAL components to expose actual system behavior,
unlike the existing mocked tests that hide integration issues.
"""

import pytest
import asyncio
import threading
import time
from typing import Dict, Any
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import qasync

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from resources.events.loop_management import EventLoopManager, SimpleEventLoopRegistry
from resources.managers.registry import CircuitBreakerRegistry
from resources.events import EventQueue
from run_phase_one import PhaseOneApp


class TestRealTwoLoopArchitecture:
    """Test REAL two-loop architecture without mocks."""
    
    def test_main_thread_uses_real_qasync_loop(self):
        """Verify main thread operations use REAL qasync loop."""
        # Clean slate
        EventLoopManager.cleanup()
        
        # Create REAL QApplication (not mocked)
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        try:
            # Create REAL qasync loop (not mocked)
            qasync_loop = qasync.QEventLoop(app)
            
            # Register as primary
            result = EventLoopManager.set_primary_loop(qasync_loop)
            assert result is True
            
            # Verify main thread gets qasync loop
            main_loop = EventLoopManager.get_loop_for_thread()
            assert main_loop is qasync_loop
            assert id(main_loop) == id(qasync_loop)
            
            # Verify this is actually a qasync loop
            assert isinstance(main_loop, qasync.QEventLoop)
            
        finally:
            if not qasync_loop.is_closed():
                qasync_loop.close()
            EventLoopManager.cleanup()
    
    def test_background_thread_uses_dedicated_loop(self):
        """Verify background thread gets its own dedicated loop."""
        EventLoopManager.cleanup()
        
        main_loop_id = None
        background_loop_id = None
        thread_error = None
        
        def background_worker():
            """Worker that gets its own loop using REAL EventLoopManager."""
            nonlocal background_loop_id, thread_error
            try:
                # This should create/get a dedicated background loop
                loop = EventLoopManager.get_loop_for_thread()
                background_loop_id = id(loop)
                
                # Verify it's a real asyncio loop
                assert isinstance(loop, asyncio.AbstractEventLoop)
                assert not loop.is_closed()
                
                # Register as background loop
                EventLoopManager.set_background_loop(loop)
                
                # Verify registration worked
                bg_loop = EventLoopManager.get_background_loop()
                assert bg_loop is loop
                
            except Exception as e:
                thread_error = e
                
        try:
            # Get main loop ID
            main_loop = EventLoopManager.get_loop_for_thread()
            main_loop_id = id(main_loop)
            
            # Start background thread
            thread = threading.Thread(target=background_worker)
            thread.start()
            thread.join(timeout=5.0)
            
            # Verify no errors in background thread
            if thread_error:
                raise thread_error
            
            # Verify different loops
            assert background_loop_id is not None
            assert main_loop_id != background_loop_id
            
        finally:
            EventLoopManager.cleanup()
    
    def test_no_cross_thread_loop_usage_real_scenario(self):
        """Test NO cross-thread loop usage in REAL scenario."""
        EventLoopManager.cleanup()
        
        violations = []
        completed_operations = []
        
        def background_monitoring():
            """Real background monitoring that should stay in background loop."""
            try:
                # Create dedicated background loop
                background_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(background_loop)
                EventLoopManager.set_background_loop(background_loop)
                
                async def monitoring_task():
                    # This should run in background loop
                    current_loop = asyncio.get_running_loop()
                    expected_loop = EventLoopManager.get_background_loop()
                    
                    if current_loop != expected_loop:
                        violations.append(f"Background monitoring in wrong loop: {id(current_loop)} vs {id(expected_loop)}")
                    
                    completed_operations.append("background_monitoring")
                
                # Run monitoring in background loop
                background_loop.run_until_complete(monitoring_task())
                background_loop.close()
                
            except Exception as e:
                violations.append(f"Background thread error: {e}")
        
        try:
            # Setup main loop
            main_loop = EventLoopManager.get_loop_for_thread()
            EventLoopManager.set_primary_loop(main_loop)
            
            # Start background thread
            thread = threading.Thread(target=background_monitoring)
            thread.start()
            thread.join(timeout=5.0)
            
            # Verify no violations and operations completed
            assert len(violations) == 0, f"Loop context violations: {violations}"
            assert "background_monitoring" in completed_operations
            
        finally:
            EventLoopManager.cleanup()
    
    def test_real_circuit_breaker_start_monitoring(self):
        """Test REAL CircuitBreakerRegistry.start_monitoring() without mocks."""
        EventLoopManager.cleanup()
        
        monitoring_started = False
        monitoring_error = None
        
        def background_worker():
            """Background thread that runs circuit breaker monitoring."""
            nonlocal monitoring_started, monitoring_error
            try:
                # Create background loop
                background_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(background_loop)
                EventLoopManager.set_background_loop(background_loop)
                
                async def run_monitoring():
                    nonlocal monitoring_started
                    
                    # Create REAL EventQueue and CircuitBreakerRegistry
                    event_queue = EventQueue(queue_id="test_circuit_monitoring")
                    await event_queue.start()
                    
                    try:
                        # Create REAL CircuitBreakerRegistry
                        registry = CircuitBreakerRegistry(event_queue)
                        
                        # This should work now (was missing before)
                        await registry.start_monitoring()
                        monitoring_started = True
                        
                        # Let it run briefly
                        await asyncio.sleep(0.1)
                        
                        # Stop monitoring
                        await registry.stop_monitoring()
                        
                    finally:
                        await event_queue.stop()
                
                background_loop.run_until_complete(run_monitoring())
                background_loop.close()
                
            except Exception as e:
                monitoring_error = e
        
        try:
            # Start background monitoring
            thread = threading.Thread(target=background_worker)
            thread.start()
            thread.join(timeout=10.0)
            
            # Verify monitoring started successfully
            if monitoring_error:
                raise monitoring_error
            
            assert monitoring_started, "Circuit breaker monitoring failed to start"
            
        finally:
            EventLoopManager.cleanup()


class TestRealApplicationLifecycle:
    """Test complete REAL application lifecycle without mocks."""
    
    def test_real_phase_one_app_initialization(self):
        """Test REAL PhaseOneApp initialization with two-loop architecture."""
        EventLoopManager.cleanup()
        
        # Store original QApplication instance
        original_app = QApplication.instance()
        
        try:
            # Create REAL PhaseOneApp (no mocks)
            phase_app = PhaseOneApp()
            
            # Verify QApplication was created or reused
            assert phase_app.app is not None
            assert isinstance(phase_app.app, QApplication)
            
            # Verify event loop was set up
            assert hasattr(phase_app, 'loop')
            assert phase_app.loop is not None
            assert isinstance(phase_app.loop, asyncio.AbstractEventLoop)
            
            # Verify primary loop registration
            primary_loop = EventLoopManager.get_primary_loop()
            assert primary_loop is phase_app.loop
            
        finally:
            # Cleanup
            EventLoopManager.cleanup()
            
            # Only quit if we created a new QApplication
            if original_app is None and QApplication.instance():
                QApplication.instance().quit()
    
    @pytest.mark.asyncio
    async def test_real_async_setup_with_background_thread(self):
        """Test REAL async setup including background thread creation."""
        EventLoopManager.cleanup()
        
        original_app = QApplication.instance()
        phase_app = None
        
        try:
            # Create REAL PhaseOneApp
            phase_app = PhaseOneApp()
            
            # Run REAL async setup
            await phase_app.setup_async()
            
            # Verify main loop is registered
            primary_loop = EventLoopManager.get_primary_loop()
            assert primary_loop is not None
            
            # Verify background thread was created
            assert hasattr(phase_app, '_background_thread')
            assert phase_app._background_thread is not None
            assert phase_app._background_thread.is_alive()
            
            # Give background thread time to register its loop
            await asyncio.sleep(0.2)
            
            # Verify background loop is registered
            background_loop = EventLoopManager.get_background_loop()
            assert background_loop is not None
            
            # Verify different loops
            assert id(primary_loop) != id(background_loop)
            
            # Verify circuit registry exists and monitoring can start
            assert hasattr(phase_app, 'circuit_registry')
            assert phase_app.circuit_registry is not None
            
        finally:
            # Cleanup
            if phase_app:
                # Stop background thread
                phase_app._shutdown_background = True
                if hasattr(phase_app, '_background_thread') and phase_app._background_thread.is_alive():
                    phase_app._background_thread.join(timeout=2.0)
                
                # Stop other resources
                if hasattr(phase_app, 'event_queue'):
                    await phase_app.event_queue.stop()
            
            EventLoopManager.cleanup()
            
            if original_app is None and QApplication.instance():
                QApplication.instance().quit()


class TestRealLoopCoordination:
    """Test REAL loop coordination and context management."""
    
    def test_submit_to_correct_loop_real_routing(self):
        """Test REAL submit_to_correct_loop routing functionality."""
        EventLoopManager.cleanup()
        
        results = {}
        errors = []
        
        def background_thread():
            """Background thread with dedicated loop."""
            try:
                # Create background loop
                bg_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(bg_loop)
                EventLoopManager.set_background_loop(bg_loop)
                
                async def background_operation():
                    # This should run in background context
                    current_loop = asyncio.get_running_loop()
                    results['background_loop_id'] = id(current_loop)
                    results['background_thread_id'] = threading.get_ident()
                    return "background_result"
                
                # Use REAL submit_to_correct_loop
                try:
                    coro = background_operation()
                    future = EventLoopManager.submit_to_correct_loop(coro, "current")
                    result = bg_loop.run_until_complete(asyncio.wrap_future(future) if hasattr(future, 'result') else future)
                    results['background_result'] = result
                except Exception as e:
                    errors.append(f"Background submission error: {e}")
                
                bg_loop.close()
                
            except Exception as e:
                errors.append(f"Background thread error: {e}")
        
        try:
            # Setup main loop
            main_loop = EventLoopManager.get_loop_for_thread()
            EventLoopManager.set_primary_loop(main_loop)
            results['main_loop_id'] = id(main_loop)
            results['main_thread_id'] = threading.get_ident()
            
            # Start background thread
            thread = threading.Thread(target=background_thread)
            thread.start()
            thread.join(timeout=5.0)
            
            # Verify no errors
            assert len(errors) == 0, f"Coordination errors: {errors}"
            
            # Verify operations ran in correct contexts
            assert 'background_loop_id' in results
            assert 'main_loop_id' in results
            assert results['background_loop_id'] != results['main_loop_id']
            
            assert 'background_thread_id' in results
            assert 'main_thread_id' in results
            assert results['background_thread_id'] != results['main_thread_id']
            
            assert results.get('background_result') == "background_result"
            
        finally:
            EventLoopManager.cleanup()
    
    def test_prevent_registration_spam_real_scenario(self):
        """Test REAL prevention of loop registration spam."""
        EventLoopManager.cleanup()
        
        # Create a loop
        test_loop = asyncio.new_event_loop()
        
        try:
            # First registration should succeed and log
            result1 = EventLoopManager.set_primary_loop(test_loop)
            assert result1 is True
            
            # Subsequent registrations should be deduplicated
            result2 = EventLoopManager.set_primary_loop(test_loop)
            assert result2 is True
            
            result3 = EventLoopManager.set_primary_loop(test_loop)
            assert result3 is True
            
            # Verify loop is still registered correctly
            primary_loop = EventLoopManager.get_primary_loop()
            assert primary_loop is test_loop
            
            # Verify registration history tracking worked
            registry = EventLoopManager._registry if hasattr(EventLoopManager, '_registry') else None
            if registry:
                # Should have only one registration entry
                registrations = [key for key in registry._registration_history if key[2] == "main"]
                assert len(registrations) == 1
            
        finally:
            test_loop.close()
            EventLoopManager.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])