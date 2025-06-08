"""
Real Integration Test Fixtures

This module provides REAL integration test fixtures without mocks:
- Real QApplication and qasync loop setup
- Real background thread with dedicated loop
- Real EventQueue and component initialization
- Real cleanup and teardown

These fixtures support testing actual system behavior rather than mocked interfaces.
"""

import pytest
import asyncio
import threading
import time
from typing import Dict, Any, Optional, Tuple
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import qasync

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from resources.events.loop_management import EventLoopManager
from resources.events import EventQueue
from resources.managers.registry import CircuitBreakerRegistry
from run_phase_one import PhaseOneApp
from tests.utils.loop_validation import LoopContextValidator, LoopContextMonitor


@pytest.fixture
async def real_two_loop_environment():
    """
    Provide REAL two-loop environment for testing.
    
    Creates:
    - Real QApplication and qasync loop (main thread)
    - Real background thread with dedicated loop
    - Proper loop registration and coordination
    - Real cleanup on teardown
    
    Returns:
        Dict with main_loop, background_loop, app, and background_thread
    """
    # Store original state
    original_app = QApplication.instance()
    
    # Clean slate
    EventLoopManager.cleanup()
    
    # Create REAL QApplication if needed
    if original_app is None:
        app = QApplication([])
        created_new_app = True
    else:
        app = original_app
        created_new_app = False
    
    # Create REAL qasync loop
    qasync_loop = qasync.QEventLoop(app)
    EventLoopManager.set_primary_loop(qasync_loop)
    
    # Background thread setup
    background_loop = None
    background_thread = None
    background_ready = threading.Event()
    background_error = None
    
    def background_worker():
        """Background thread worker with dedicated loop."""
        nonlocal background_loop, background_error
        try:
            # Create dedicated background loop
            background_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(background_loop)
            EventLoopManager.set_background_loop(background_loop)
            
            # Signal that background is ready
            background_ready.set()
            
            # Keep background loop running
            async def keep_alive():
                while not getattr(threading.current_thread(), '_shutdown', False):
                    await asyncio.sleep(0.1)
            
            background_loop.run_until_complete(keep_alive())
            
        except Exception as e:
            background_error = e
        finally:
            if background_loop and not background_loop.is_closed():
                background_loop.close()
    
    # Start background thread
    background_thread = threading.Thread(target=background_worker, daemon=True)
    background_thread.start()
    
    # Wait for background thread to be ready
    if not background_ready.wait(timeout=5.0):
        raise RuntimeError("Background thread failed to start")
    
    if background_error:
        raise background_error
    
    # Verify we have two different loops
    main_loop = EventLoopManager.get_primary_loop()
    bg_loop = EventLoopManager.get_background_loop()
    
    assert main_loop is not None
    assert bg_loop is not None
    assert id(main_loop) != id(bg_loop)
    
    try:
        yield {
            "main_loop": main_loop,
            "background_loop": bg_loop,
            "app": app,
            "background_thread": background_thread,
            "qasync_loop": qasync_loop
        }
    
    finally:
        # Cleanup
        try:
            # Stop background thread
            if background_thread and background_thread.is_alive():
                background_thread._shutdown = True
                background_thread.join(timeout=3.0)
            
            # Close qasync loop
            if not qasync_loop.is_closed():
                qasync_loop.close()
            
            # Quit application if we created it
            if created_new_app and QApplication.instance():
                QApplication.instance().quit()
            
        except Exception as e:
            # Don't let cleanup errors break other tests
            pass
        finally:
            EventLoopManager.cleanup()


@pytest.fixture
async def real_phase_one_app():
    """
    Provide REAL PhaseOneApp with full initialization.
    
    Creates:
    - Real PhaseOneApp instance
    - Full async setup including all managers
    - Background thread monitoring
    - Real event queue and circuit registry
    
    Returns:
        Fully initialized PhaseOneApp instance
    """
    # Store original state
    original_app = QApplication.instance()
    
    # Clean slate
    EventLoopManager.cleanup()
    
    try:
        # Create REAL PhaseOneApp
        phase_app = PhaseOneApp()
        
        # Run REAL async setup
        await phase_app.setup_async()
        
        # Wait for background thread to be fully ready
        await asyncio.sleep(0.5)
        
        # Verify setup completed successfully
        assert hasattr(phase_app, 'event_queue')
        assert hasattr(phase_app, 'circuit_registry')
        assert hasattr(phase_app, '_background_thread')
        assert phase_app._background_thread.is_alive()
        
        yield phase_app
    
    finally:
        # Cleanup
        try:
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
            
        except Exception as e:
            # Don't let cleanup errors break other tests
            pass
        finally:
            EventLoopManager.cleanup()
            
            # Only quit if we created a new application
            if original_app is None and QApplication.instance():
                QApplication.instance().quit()


@pytest.fixture
def loop_context_validator():
    """
    Provide a LoopContextValidator for tracking context violations.
    
    Returns:
        Fresh LoopContextValidator instance
    """
    validator = LoopContextValidator()
    
    yield validator
    
    # Assert no violations at end of test
    try:
        validator.assert_no_violations()
    except AssertionError:
        # Print violation details before re-raising
        print(f"\nLoop Context Violations Detected:")
        print(validator._format_violations())
        raise


@pytest.fixture
async def loop_context_monitor(loop_context_validator):
    """
    Provide a LoopContextMonitor for continuous validation during tests.
    
    Returns:
        LoopContextMonitor that automatically starts and stops
    """
    monitor = LoopContextMonitor(loop_context_validator)
    
    # Start monitoring
    await monitor.start_monitoring(check_interval=0.05)  # Check every 50ms
    
    try:
        yield monitor
    finally:
        # Stop monitoring
        await monitor.stop_monitoring()


@pytest.fixture
async def real_event_queue_with_circuit_registry():
    """
    Provide REAL EventQueue and CircuitBreakerRegistry for testing.
    
    Returns:
        Tuple of (EventQueue, CircuitBreakerRegistry)
    """
    # Create REAL components
    event_queue = EventQueue(queue_id="fixture_test_queue")
    await event_queue.start()
    
    circuit_registry = CircuitBreakerRegistry(event_queue)
    
    try:
        yield (event_queue, circuit_registry)
    finally:
        # Cleanup
        try:
            await circuit_registry.stop_monitoring()
        except:
            pass
        
        try:
            await event_queue.stop()
        except:
            pass


@pytest.fixture
def real_background_thread_context():
    """
    Provide a REAL background thread context for testing background operations.
    
    Returns:
        Dict with background_loop and thread information
    """
    EventLoopManager.cleanup()
    
    background_info = {}
    background_ready = threading.Event()
    background_error = None
    
    def background_worker():
        """Real background worker thread."""
        nonlocal background_info, background_error
        try:
            # Create background loop
            bg_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(bg_loop)
            EventLoopManager.set_background_loop(bg_loop)
            
            background_info = {
                "loop": bg_loop,
                "loop_id": id(bg_loop),
                "thread_id": threading.get_ident(),
                "thread_name": threading.current_thread().name
            }
            
            background_ready.set()
            
            # Keep running until shutdown
            async def keep_alive():
                while not getattr(threading.current_thread(), '_shutdown', False):
                    await asyncio.sleep(0.1)
            
            bg_loop.run_until_complete(keep_alive())
            
        except Exception as e:
            background_error = e
        finally:
            if 'loop' in background_info and not background_info['loop'].is_closed():
                background_info['loop'].close()
    
    # Start background thread
    thread = threading.Thread(target=background_worker, daemon=True)
    thread.start()
    
    # Wait for ready
    if not background_ready.wait(timeout=5.0):
        raise RuntimeError("Background thread failed to start")
    
    if background_error:
        raise background_error
    
    background_info['thread'] = thread
    
    try:
        yield background_info
    finally:
        # Cleanup
        try:
            thread._shutdown = True
            thread.join(timeout=3.0)
        except:
            pass
        
        EventLoopManager.cleanup()


@pytest.fixture
async def coordinated_loop_operations():
    """
    Provide coordinated loop operations testing environment.
    
    This fixture sets up both main and background loops and provides
    utilities for testing cross-loop coordination.
    
    Returns:
        Dict with coordination utilities and loop references
    """
    # Use the two-loop environment
    async with real_two_loop_environment() as env:
        
        coordination_results = {
            "main_operations": [],
            "background_operations": [],
            "coordination_errors": []
        }
        
        async def run_in_main(operation_name: str, operation_func):
            """Run operation in main loop context."""
            try:
                current_loop = asyncio.get_running_loop()
                main_loop = env["main_loop"]
                
                if current_loop != main_loop:
                    coordination_results["coordination_errors"].append(
                        f"Main operation {operation_name} in wrong loop: {id(current_loop)} vs {id(main_loop)}"
                    )
                    return None
                
                result = await operation_func()
                coordination_results["main_operations"].append({
                    "operation": operation_name,
                    "result": result,
                    "loop_id": id(current_loop)
                })
                return result
                
            except Exception as e:
                coordination_results["coordination_errors"].append(
                    f"Main operation {operation_name} error: {e}"
                )
                return None
        
        def run_in_background(operation_name: str, operation_func):
            """Submit operation to background loop."""
            try:
                background_loop = env["background_loop"]
                
                async def background_wrapper():
                    current_loop = asyncio.get_running_loop()
                    if current_loop != background_loop:
                        coordination_results["coordination_errors"].append(
                            f"Background operation {operation_name} in wrong loop: {id(current_loop)} vs {id(background_loop)}"
                        )
                        return None
                    
                    result = await operation_func()
                    coordination_results["background_operations"].append({
                        "operation": operation_name,
                        "result": result,
                        "loop_id": id(current_loop)
                    })
                    return result
                
                # Submit to background loop
                future = asyncio.run_coroutine_threadsafe(background_wrapper(), background_loop)
                return future
                
            except Exception as e:
                coordination_results["coordination_errors"].append(
                    f"Background operation {operation_name} submission error: {e}"
                )
                return None
        
        coordination_utils = {
            "env": env,
            "results": coordination_results,
            "run_in_main": run_in_main,
            "run_in_background": run_in_background
        }
        
        yield coordination_utils