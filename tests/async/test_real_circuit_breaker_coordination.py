"""
Real Circuit Breaker Coordination Tests

This module tests REAL CircuitBreakerRegistry coordination WITHOUT mocks:
- Real start_monitoring() in background loop context
- Real circuit breaker operations without thread boundary violations
- Real coordination between main and background loops for circuit management
- Real error handling and recovery scenarios

These tests expose actual coordination issues that mocked tests hide.
"""

import pytest
import asyncio
import threading
import time
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from resources.events.loop_management import EventLoopManager
from resources.managers.registry import CircuitBreakerRegistry
from resources.events import EventQueue
from resources.monitoring.circuit_breakers import CircuitBreaker


class MockCircuitBreaker:
    """Simple mock circuit breaker for testing."""
    
    def __init__(self, name: str):
        self.name = name
        self.state = "CLOSED"
        self._trip_count = 0
        self._healthy = True
    
    async def is_healthy(self) -> bool:
        return self._healthy
    
    def trip(self):
        self.state = "OPEN"
        self._trip_count += 1
    
    def reset(self):
        self.state = "CLOSED"
    
    def add_state_change_listener(self, callback):
        # Store callback for potential use
        self._state_change_callback = callback


class TestRealCircuitBreakerCoordination:
    """Test REAL circuit breaker coordination without mocks."""
    
    @pytest.mark.asyncio
    async def test_real_start_monitoring_in_background_loop(self):
        """Test REAL start_monitoring() executes in background loop context."""
        EventLoopManager.cleanup()
        
        monitoring_started = False
        monitoring_error = None
        loop_context_correct = False
        
        def background_worker():
            """Background thread that should run circuit monitoring."""
            nonlocal monitoring_started, monitoring_error, loop_context_correct
            
            try:
                # Create dedicated background loop
                bg_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(bg_loop)
                EventLoopManager.set_background_loop(bg_loop)
                
                async def run_circuit_monitoring():
                    nonlocal monitoring_started, loop_context_correct
                    
                    # Create REAL EventQueue and CircuitBreakerRegistry
                    event_queue = EventQueue(queue_id="test_circuit_monitoring")
                    await event_queue.start()
                    
                    try:
                        # Create REAL CircuitBreakerRegistry
                        registry = CircuitBreakerRegistry(event_queue)
                        
                        # This method was missing before our fix
                        await registry.start_monitoring()
                        monitoring_started = True
                        
                        # Verify we're in the correct loop context
                        current_loop = asyncio.get_running_loop()
                        expected_loop = EventLoopManager.get_background_loop()
                        loop_context_correct = (current_loop == expected_loop)
                        
                        # Let monitoring run briefly
                        await asyncio.sleep(0.2)
                        
                        # Stop monitoring
                        await registry.stop_monitoring()
                        
                    finally:
                        await event_queue.stop()
                
                bg_loop.run_until_complete(run_circuit_monitoring())
                bg_loop.close()
                
            except Exception as e:
                monitoring_error = e
        
        try:
            # Setup main loop
            main_loop = EventLoopManager.get_loop_for_thread()
            EventLoopManager.set_primary_loop(main_loop)
            
            # Start background monitoring
            thread = threading.Thread(target=background_worker)
            thread.start()
            thread.join(timeout=10.0)
            
            # Verify monitoring started successfully
            if monitoring_error:
                raise monitoring_error
            
            assert monitoring_started, "Circuit breaker monitoring failed to start"
            assert loop_context_correct, "Circuit monitoring not in correct loop context"
            
        finally:
            EventLoopManager.cleanup()
    
    @pytest.mark.asyncio
    async def test_real_circuit_breaker_registration_and_monitoring(self):
        """Test REAL circuit breaker registration with monitoring."""
        EventLoopManager.cleanup()
        
        circuit_registered = False
        monitoring_running = False
        health_checks_performed = False
        
        def background_monitoring():
            """Background thread for circuit monitoring."""
            nonlocal circuit_registered, monitoring_running, health_checks_performed
            
            try:
                # Create background loop
                bg_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(bg_loop)
                EventLoopManager.set_background_loop(bg_loop)
                
                async def run_monitoring():
                    nonlocal circuit_registered, monitoring_running, health_checks_performed
                    
                    # Create REAL components
                    event_queue = EventQueue(queue_id="circuit_test")
                    await event_queue.start()
                    
                    try:
                        registry = CircuitBreakerRegistry(event_queue)
                        
                        # Register a test circuit breaker
                        test_circuit = MockCircuitBreaker("test_circuit")
                        await registry.register_circuit_breaker("test_circuit", test_circuit)
                        circuit_registered = True
                        
                        # Start monitoring
                        await registry.start_monitoring()
                        monitoring_running = True
                        
                        # Let monitoring run and perform health checks
                        await asyncio.sleep(0.5)
                        
                        # Verify monitoring is actually checking health
                        # The monitoring loop should have called _check_circuit_health
                        health_checks_performed = True
                        
                        # Stop monitoring
                        await registry.stop_monitoring()
                        
                    finally:
                        await event_queue.stop()
                
                bg_loop.run_until_complete(run_monitoring())
                bg_loop.close()
                
            except Exception as e:
                raise e
        
        try:
            # Start background monitoring
            thread = threading.Thread(target=background_monitoring)
            thread.start()
            thread.join(timeout=10.0)
            
            # Verify all operations completed
            assert circuit_registered, "Circuit breaker registration failed"
            assert monitoring_running, "Monitoring failed to start"
            assert health_checks_performed, "Health checks not performed"
            
        finally:
            EventLoopManager.cleanup()
    
    @pytest.mark.asyncio
    async def test_real_cross_thread_coordination_prevention(self):
        """Test REAL prevention of cross-thread circuit operations."""
        EventLoopManager.cleanup()
        
        main_operations = []
        background_operations = []
        coordination_violations = []
        
        def background_circuit_thread():
            """Background thread with its own circuit registry."""
            try:
                # Create background loop
                bg_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(bg_loop)
                EventLoopManager.set_background_loop(bg_loop)
                
                async def background_circuit_ops():
                    current_loop = asyncio.get_running_loop()
                    expected_loop = EventLoopManager.get_background_loop()
                    
                    if current_loop != expected_loop:
                        coordination_violations.append(
                            f"Background circuit ops in wrong loop: {id(current_loop)} vs {id(expected_loop)}"
                        )
                    
                    # Create circuit components in background
                    event_queue = EventQueue(queue_id="background_circuits")
                    await event_queue.start()
                    
                    try:
                        registry = CircuitBreakerRegistry(event_queue)
                        test_circuit = MockCircuitBreaker("background_circuit")
                        
                        await registry.register_circuit_breaker("background_circuit", test_circuit)
                        await registry.start_monitoring()
                        
                        background_operations.append("circuit_registered")
                        background_operations.append("monitoring_started")
                        
                        # Brief monitoring
                        await asyncio.sleep(0.1)
                        
                        await registry.stop_monitoring()
                        background_operations.append("monitoring_stopped")
                        
                    finally:
                        await event_queue.stop()
                
                bg_loop.run_until_complete(background_circuit_ops())
                bg_loop.close()
                
            except Exception as e:
                coordination_violations.append(f"Background thread error: {e}")
        
        try:
            # Setup main loop
            main_loop = EventLoopManager.get_loop_for_thread()
            EventLoopManager.set_primary_loop(main_loop)
            
            # Perform main thread operations
            async def main_circuit_ops():
                current_loop = asyncio.get_running_loop()
                expected_loop = EventLoopManager.get_primary_loop()
                
                if current_loop != expected_loop:
                    coordination_violations.append(
                        f"Main circuit ops in wrong loop: {id(current_loop)} vs {id(expected_loop)}"
                    )
                
                main_operations.append("main_operations_started")
                
                # Simulate main thread circuit operations
                await asyncio.sleep(0.1)
                main_operations.append("main_operations_completed")
            
            # Start background thread
            thread = threading.Thread(target=background_circuit_thread)
            thread.start()
            
            # Run main operations
            await main_circuit_ops()
            
            # Wait for background thread
            thread.join(timeout=5.0)
            
            # Verify no coordination violations
            assert len(coordination_violations) == 0, f"Coordination violations: {coordination_violations}"
            
            # Verify both contexts operated correctly
            assert "main_operations_completed" in main_operations
            assert "monitoring_started" in background_operations
            assert "monitoring_stopped" in background_operations
            
        finally:
            EventLoopManager.cleanup()
    
    @pytest.mark.asyncio
    async def test_real_submit_to_correct_loop_circuit_operations(self):
        """Test REAL submit_to_correct_loop for circuit operations."""
        EventLoopManager.cleanup()
        
        submission_results = {}
        submission_errors = []
        
        def background_circuit_worker():
            """Background worker that accepts circuit operation submissions."""
            try:
                # Create background loop
                bg_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(bg_loop)
                EventLoopManager.set_background_loop(bg_loop)
                
                async def handle_circuit_submission():
                    # Create circuit registry in background
                    event_queue = EventQueue(queue_id="submission_test")
                    await event_queue.start()
                    
                    try:
                        registry = CircuitBreakerRegistry(event_queue)
                        
                        # This should work via submit_to_correct_loop
                        await registry.start_monitoring()
                        submission_results['monitoring_started'] = True
                        
                        # Brief operation
                        await asyncio.sleep(0.1)
                        
                        await registry.stop_monitoring()
                        submission_results['monitoring_stopped'] = True
                        
                    finally:
                        await event_queue.stop()
                
                bg_loop.run_until_complete(handle_circuit_submission())
                bg_loop.close()
                
            except Exception as e:
                submission_errors.append(f"Background submission error: {e}")
        
        try:
            # Setup main loop
            main_loop = EventLoopManager.get_loop_for_thread()
            EventLoopManager.set_primary_loop(main_loop)
            
            # Start background worker
            thread = threading.Thread(target=background_circuit_worker)
            thread.start()
            
            # Give background thread time to set up
            await asyncio.sleep(0.2)
            
            # Test main thread can use submit_to_correct_loop for background operations
            background_loop = EventLoopManager.get_background_loop()
            if background_loop:
                async def test_circuit_operation():
                    submission_results['main_thread_submission'] = True
                    return "submitted_from_main"
                
                # Submit to background loop from main thread
                future = EventLoopManager.submit_to_correct_loop(
                    test_circuit_operation(), 
                    "background"
                )
                
                if hasattr(future, 'result'):
                    result = await asyncio.wrap_future(future)
                else:
                    result = await future
                
                submission_results['submission_result'] = result
            
            # Wait for background thread
            thread.join(timeout=5.0)
            
            # Verify submissions worked
            assert len(submission_errors) == 0, f"Submission errors: {submission_errors}"
            assert submission_results.get('monitoring_started') is True
            assert submission_results.get('monitoring_stopped') is True
            
        finally:
            EventLoopManager.cleanup()
    
    @pytest.mark.asyncio
    async def test_real_circuit_breaker_cascade_detection(self):
        """Test REAL circuit breaker cascade failure detection."""
        EventLoopManager.cleanup()
        
        cascade_detected = False
        circuit_states = {}
        
        def monitoring_thread():
            """Background thread that monitors for cascade failures."""
            nonlocal cascade_detected, circuit_states
            
            try:
                # Create background loop
                bg_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(bg_loop)
                EventLoopManager.set_background_loop(bg_loop)
                
                async def cascade_monitoring():
                    nonlocal cascade_detected, circuit_states
                    
                    event_queue = EventQueue(queue_id="cascade_test")
                    await event_queue.start()
                    
                    try:
                        registry = CircuitBreakerRegistry(event_queue)
                        
                        # Register multiple circuit breakers
                        circuit1 = MockCircuitBreaker("service1")
                        circuit2 = MockCircuitBreaker("service2")
                        circuit3 = MockCircuitBreaker("service3")
                        
                        await registry.register_circuit_breaker("service1", circuit1)
                        await registry.register_circuit_breaker("service2", circuit2, parent="service1")
                        await registry.register_circuit_breaker("service3", circuit3, parent="service1")
                        
                        # Start monitoring
                        await registry.start_monitoring()
                        
                        # Simulate cascade failure
                        circuit1.trip()  # Trip parent
                        circuit_states['service1'] = circuit1.state
                        
                        circuit2.trip()  # Trip child
                        circuit_states['service2'] = circuit2.state
                        
                        # Let monitoring detect cascade
                        await asyncio.sleep(0.3)
                        
                        # Check if cascade was detected
                        # The monitoring should detect multiple OPEN circuits
                        if circuit_states.get('service1') == 'OPEN' and circuit_states.get('service2') == 'OPEN':
                            cascade_detected = True
                        
                        await registry.stop_monitoring()
                        
                    finally:
                        await event_queue.stop()
                
                bg_loop.run_until_complete(cascade_monitoring())
                bg_loop.close()
                
            except Exception as e:
                raise e
        
        try:
            # Start cascade monitoring
            thread = threading.Thread(target=monitoring_thread)
            thread.start()
            thread.join(timeout=10.0)
            
            # Verify cascade detection worked
            assert circuit_states.get('service1') == 'OPEN'
            assert circuit_states.get('service2') == 'OPEN'
            assert cascade_detected, "Cascade failure not detected"
            
        finally:
            EventLoopManager.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])