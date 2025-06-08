#!/usr/bin/env python3
"""
Direct test for CircuitBreakerRegistry to verify threading.Lock vs asyncio.Lock behavior.
This test runs directly without pytest to avoid circular import issues.
"""
import asyncio
import threading
import logging
import time
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class CircuitState:
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class MockEventQueue:
    """Mock event queue for testing"""
    async def emit(self, event_type, data, correlation_id=None, priority="normal"):
        logger.info(f"MockEventQueue: Emitted event {event_type}")
        return True

class MockCircuitBreaker:
    """Mock circuit breaker for testing"""
    def __init__(self, name, event_queue):
        self.name = name
        self._event_queue = event_queue
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.last_state_change = time.time()
        self._lock = threading.RLock()  # Using threading.RLock for testing

class CircuitBreakerRegistry:
    """Simplified version of the circuit breaker registry for testing"""
    def __init__(self, event_queue):
        self._event_queue = event_queue
        self._circuit_breakers: Dict[str, MockCircuitBreaker] = {}
        # This is the key line - use threading.RLock() instead of asyncio.Lock()
        self._registry_lock = threading.RLock()
        
    def get_circuit_status_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get a summary of all circuit breakers and their current status."""
        status = {}
        
        # Thread-safe access to circuit breakers
        with self._registry_lock:
            circuit_breakers_copy = dict(self._circuit_breakers)
            
        for name, breaker in circuit_breakers_copy.items():
            try:
                # Thread-safe access to circuit state
                with breaker._lock:
                    state_name = breaker.state
                    failure_count = breaker.failure_count
                
                status[name] = {
                    "state": state_name,
                    "failure_count": failure_count,
                }
            except Exception as e:
                status[name] = {"error": str(e)}
                
        return status
    
    async def _check_all_circuits(self) -> None:
        """Check status of all circuit breakers - simulating the problematic method."""
        # Create a thread-safe copy of the circuit breakers dictionary
        with self._registry_lock:  # This is what was using asyncio.Lock in the original
            circuit_breakers_copy = dict(self._circuit_breakers)
            
        for name, breaker in circuit_breakers_copy.items():
            # Various operations that use the lock
            with self._registry_lock:
                if name not in self._circuit_breakers:
                    continue
        
        return True
    
    async def register_circuit_breaker(self, name, parent=None):
        """Register a circuit breaker for testing."""
        # Create a new circuit breaker
        circuit = MockCircuitBreaker(name, self._event_queue)
        
        # Register it with the registry using the lock
        with self._registry_lock:
            self._circuit_breakers[name] = circuit
        
        return circuit

class RegistryWithAsyncioLock(CircuitBreakerRegistry):
    """Version of the registry using asyncio.Lock() to demonstrate issue"""
    def __init__(self, event_queue):
        self._event_queue = event_queue
        self._circuit_breakers: Dict[str, MockCircuitBreaker] = {}
        # Using asyncio.Lock() - this is the problematic version
        self._registry_lock = asyncio.Lock()
        
    async def get_circuit_status_summary_async(self) -> Dict[str, Dict[str, Any]]:
        """Get a summary of all circuit breakers using asyncio.Lock."""
        status = {}
        
        # Thread-safe access to circuit breakers
        async with self._registry_lock:
            circuit_breakers_copy = dict(self._circuit_breakers)
            
        for name, breaker in circuit_breakers_copy.items():
            try:
                # Thread-safe access to circuit state
                with breaker._lock:
                    state_name = breaker.state
                    failure_count = breaker.failure_count
                
                status[name] = {
                    "state": state_name,
                    "failure_count": failure_count,
                }
            except Exception as e:
                status[name] = {"error": str(e)}
                
        return status
    
    def get_circuit_status_summary(self) -> Dict[str, Dict[str, Any]]:
        """PROBLEMATIC METHOD: Using asyncio.Lock in synchronous context"""
        status = {}
        
        # Attempt to use asyncio.Lock in synchronous context - THIS WILL FAIL
        with self._registry_lock:  # This will fail because asyncio.Lock requires 'async with'
            circuit_breakers_copy = dict(self._circuit_breakers)
            
        # The rest of the method won't execute due to the error above
        for name, breaker in circuit_breakers_copy.items():
            try:
                with breaker._lock:
                    state_name = breaker.state
                    failure_count = breaker.failure_count
                
                status[name] = {
                    "state": state_name,
                    "failure_count": failure_count,
                }
            except Exception as e:
                status[name] = {"error": str(e)}
                
        return status
    
    async def _check_all_circuits(self) -> None:
        """Check status of all circuit breakers with asyncio.Lock."""
        # Create a thread-safe copy of the circuit breakers dictionary
        async with self._registry_lock:  # Using asyncio.Lock correctly in async context
            circuit_breakers_copy = dict(self._circuit_breakers)
            
        for name, breaker in circuit_breakers_copy.items():
            # Various operations that use the lock
            async with self._registry_lock:
                if name not in self._circuit_breakers:
                    continue
        
        return True
    
    async def register_circuit_breaker(self, name, parent=None):
        """Register a circuit breaker for testing."""
        # Create a new circuit breaker
        circuit = MockCircuitBreaker(name, self._event_queue)
        
        # Register it with the registry using the lock
        async with self._registry_lock:
            self._circuit_breakers[name] = circuit
        
        return circuit

async def test_registry_thread_safety():
    """Test that the registry works properly with threading.Lock."""
    # Create event queue and registry
    event_queue = MockEventQueue()
    registry = CircuitBreakerRegistry(event_queue)
    
    # Register some circuit breakers
    await registry.register_circuit_breaker("circuit1")
    await registry.register_circuit_breaker("circuit2")
    
    # Run the check_all_circuits method that would use the lock
    result = await registry._check_all_circuits()
    assert result is True
    
    # Get status summary - this should also use the lock
    status = registry.get_circuit_status_summary()
    assert "circuit1" in status
    assert "circuit2" in status
    
    # Verify circuit states
    assert status["circuit1"]["state"] == CircuitState.CLOSED
    assert status["circuit2"]["state"] == CircuitState.CLOSED
    
    logger.info("✅ Test registry_thread_safety passed")
    return True

async def test_registry_concurrent_access():
    """Test concurrent access to the registry from multiple threads."""
    # Create event queue and registry
    event_queue = MockEventQueue()
    registry = CircuitBreakerRegistry(event_queue)
    
    # Register initial circuit breakers
    await registry.register_circuit_breaker("main_circuit")
    
    # Function to run in threads
    async def register_and_check(thread_id):
        # Register a circuit breaker
        circuit_name = f"circuit_thread_{thread_id}"
        await registry.register_circuit_breaker(circuit_name)
        
        # Check all circuits
        await registry._check_all_circuits()
        
        # Get status summary
        status = registry.get_circuit_status_summary()
        assert circuit_name in status
        return True
    
    # Create tasks for concurrent access
    tasks = []
    for i in range(5):
        task = asyncio.create_task(register_and_check(i))
        tasks.append(task)
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks)
    
    # Verify all tasks succeeded
    assert all(results)
    
    # Verify final state
    status = registry.get_circuit_status_summary()
    assert len(status) == 6  # main_circuit + 5 thread circuits
    assert "main_circuit" in status
    for i in range(5):
        assert f"circuit_thread_{i}" in status
    
    logger.info("✅ Test registry_concurrent_access passed")
    return True

async def test_registry_threaded_access():
    """Test access from actual separate threads."""
    # Create event queue and registry
    event_queue = MockEventQueue()
    registry = CircuitBreakerRegistry(event_queue)
    
    # Register initial circuit
    await registry.register_circuit_breaker("main_circuit")
    
    # Store results from threads
    results = []
    result_lock = threading.Lock()
    completed_event = threading.Event()
    
    # Function to run in thread
    def thread_function(thread_id):
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run the async function
            circuit_name = f"thread_{thread_id}_circuit"
            
            # Register and check circuit breaker
            async def thread_task():
                await registry.register_circuit_breaker(circuit_name)
                await registry._check_all_circuits()
                status = registry.get_circuit_status_summary()
                return circuit_name in status
            
            # Run the async function in this thread's event loop
            success = loop.run_until_complete(thread_task())
            
            # Store result
            with result_lock:
                results.append((thread_id, success))
            
            # Signal completion if this is the last thread
            if len(results) == 5:
                completed_event.set()
                
        finally:
            # Clean up
            loop.close()
    
    # Start threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=thread_function, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete with timeout
    completed_event.wait(timeout=10.0)
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join(timeout=1.0)
    
    # Verify all threads succeeded
    assert len(results) == 5
    assert all(success for _, success in results)
    
    # Verify final state
    status = registry.get_circuit_status_summary()
    assert len(status) == 6  # main_circuit + 5 thread circuits
    
    # Check that all circuits are present
    assert "main_circuit" in status
    for i in range(5):
        assert f"thread_{i}_circuit" in status
    
    logger.info("✅ Test registry_threaded_access passed")
    return True

async def test_asyncio_lock_error():
    """Test demonstrating error when using asyncio.Lock in synchronous context."""
    # Create event queue and registry with asyncio.Lock
    event_queue = MockEventQueue()
    registry = RegistryWithAsyncioLock(event_queue)
    
    # Register circuit breaker - this uses asyncio.Lock correctly
    await registry.register_circuit_breaker("test_circuit")
    
    # This will work because it uses asyncio.Lock correctly in async context
    result = await registry._check_all_circuits()
    assert result is True
    
    # Get summary using async method - this should work
    status = await registry.get_circuit_status_summary_async()
    assert "test_circuit" in status
    
    # Try using the synchronous method that incorrectly uses asyncio.Lock
    try:
        registry.get_circuit_status_summary()
        # If we reach here, the test failed
        assert False, "Should have raised an exception when using asyncio.Lock in sync context"
    except (RuntimeError, TypeError):
        # Expected error - asyncio.Lock cannot be used in synchronous context
        logger.info("✅ Correctly caught error when using asyncio.Lock in synchronous context")
    
    return True

async def run_tests():
    """Run all tests."""
    logger.info("Running thread safety tests for CircuitBreakerRegistry")
    
    # Run the tests
    await test_registry_thread_safety()
    await test_registry_concurrent_access()
    await test_registry_threaded_access()
    await test_asyncio_lock_error()
    
    logger.info("All tests passed!")

if __name__ == "__main__":
    # Run the tests
    asyncio.run(run_tests())