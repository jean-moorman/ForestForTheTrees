"""
Isolated test for CircuitBreakerRegistry to verify threading.Lock vs asyncio.Lock behavior.
"""
import asyncio
import pytest
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

@pytest.mark.asyncio
class TestCircuitBreakerIsolated:
    """Test the isolated CircuitBreakerRegistry implementation."""
    
    async def test_registry_thread_safety(self):
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
        
    async def test_registry_concurrent_access(self):
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
        
    async def test_registry_threaded_access(self):
        """Test access from actual separate threads."""
        # Create event queue and registry
        event_queue = MockEventQueue()
        registry = CircuitBreakerRegistry(event_queue)
        
        # Register initial circuit
        await registry.register_circuit_breaker("main_circuit")
        
        # Store results from threads
        results = []
        result_lock = threading.Lock()
        
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
                
            finally:
                # Clean up
                loop.close()
        
        # Start threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=thread_function, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
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