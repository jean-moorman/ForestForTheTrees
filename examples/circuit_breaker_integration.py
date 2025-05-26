"""
Example showing how to integrate the simplified circuit breaker implementation.

This example demonstrates how to use the CircuitBreakerSimple and 
CircuitBreakerRegistrySimple classes without creating circular dependencies.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Import from simplified module to avoid circular imports
from resources.circuit_breakers_simple import (
    CircuitBreakerSimple,
    CircuitBreakerRegistrySimple,
    CircuitOpenError,
    CircuitState
)
from resources.common import CircuitBreakerConfig, HealthStatus

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockEventQueue:
    """Simple mock event queue for demonstrations"""
    
    async def emit(self, event_type: str, data: Dict[str, Any], 
                  correlation_id: Optional[str] = None, 
                  priority: str = "normal") -> bool:
        """Emit an event with the given data"""
        logger.info(f"EVENT EMITTED: {event_type} - {data}")
        return True

class MockHealthTracker:
    """Simple mock health tracker for demonstrations"""
    
    async def update_health(self, component_id: str, health_status: HealthStatus) -> None:
        """Update health status for a component"""
        logger.info(f"HEALTH UPDATED: {component_id} - {health_status.status} - {health_status.description}")

class MockStateManager:
    """Simple mock state manager for demonstrations"""
    
    async def save_state(self, resource_id: str, state: Dict[str, Any]) -> None:
        """Save state for a resource"""
        logger.info(f"STATE SAVED: {resource_id} - {state}")

async def example_circuit_breaker_usage():
    """Demonstrate circuit breaker usage without circular dependencies"""
    logger.info("Starting circuit breaker example")
    
    # Create mock components
    event_queue = MockEventQueue()
    health_tracker = MockHealthTracker()
    state_manager = MockStateManager()
    
    # Initialize the circuit breaker registry
    registry = CircuitBreakerRegistrySimple()
    
    # Configure optional callbacks for integration - this avoids circular dependencies
    # by allowing late binding of dependencies
    registry.set_event_emitter(event_queue.emit)
    registry.set_health_tracker(health_tracker.update_health)
    registry.set_state_manager(lambda name, state: state_manager.save_state(f"circuit_breaker_{name}", state))
    
    # Create a circuit breaker configuration
    config = CircuitBreakerConfig(
        failure_threshold=3,  # Lower for demonstration
        recovery_timeout=5,   # Shorter for demonstration
        half_open_max_tries=1,
        failure_window=60
    )
    
    # Register the default configuration
    registry.set_default_config(config)
    
    # Create a circuit breaker
    api_circuit = await registry.get_or_create_circuit_breaker("api_service")
    
    # Create a component-specific configuration
    db_config = CircuitBreakerConfig(
        failure_threshold=2,   # Even lower for DB
        recovery_timeout=10,   # Longer for DB
        half_open_max_tries=1,
        failure_window=60
    )
    
    # Create another circuit breaker with component-specific config
    db_circuit = await registry.get_or_create_circuit_breaker(
        "database", 
        component="database", 
        config=db_config
    )
    
    # Register a dependency between circuits
    await registry.register_dependency("api_service", "database")
    
    # Simulate successful operations
    for i in range(3):
        try:
            # Execute an operation with the circuit breaker
            result = await registry.circuit_execute(
                "api_service",
                lambda: api_success_operation(i)
            )
            logger.info(f"Operation {i} succeeded: {result}")
        except CircuitOpenError as e:
            logger.error(f"Circuit is open: {e}")
        except Exception as e:
            logger.error(f"Operation failed: {e}")
    
    # Simulate failures to trip the circuit
    for i in range(5):
        try:
            # Execute an operation with the circuit breaker
            result = await registry.circuit_execute(
                "api_service",
                lambda: api_failure_operation(i)
            )
            logger.info(f"Operation {i} succeeded: {result}")
        except CircuitOpenError as e:
            logger.error(f"Circuit is open: {e}")
        except Exception as e:
            logger.error(f"Operation failed: {e}")
    
    # Check circuit status
    status = registry.get_circuit_status_summary()
    logger.info(f"Circuit status: {status}")
    
    # Wait for recovery timeout to elapse
    logger.info(f"Waiting for recovery timeout ({config.recovery_timeout} seconds)")
    await asyncio.sleep(config.recovery_timeout + 1)
    
    # Try again after recovery
    try:
        # Execute an operation with the circuit breaker
        result = await registry.circuit_execute(
            "api_service",
            lambda: api_success_operation(0)  # This should work now
        )
        logger.info(f"Recovery operation succeeded: {result}")
        
        # Check circuit status again
        status = registry.get_circuit_status_summary()
        logger.info(f"Circuit status after recovery: {status}")
    except CircuitOpenError as e:
        logger.error(f"Circuit is still open: {e}")
    except Exception as e:
        logger.error(f"Operation failed: {e}")
    
    # Manually trip the database circuit to show cascading trips
    logger.info("Manually tripping database circuit")
    await registry.trip_circuit("database", reason="Manual trip for demonstration")
    
    # Check circuit status after manual trip
    status = registry.get_circuit_status_summary()
    logger.info(f"Circuit status after manual trip: {status}")
    
    # Reset all circuits
    reset_count = await registry.reset_all_circuits()
    logger.info(f"Reset {reset_count} circuits")
    
    # Final status
    status = registry.get_circuit_status_summary()
    logger.info(f"Final circuit status: {status}")

async def api_success_operation(i: int) -> str:
    """Simulate a successful API operation"""
    await asyncio.sleep(0.1)  # Simulate network call
    return f"API call {i} completed successfully at {datetime.now().isoformat()}"

async def api_failure_operation(i: int) -> str:
    """Simulate a failing API operation"""
    await asyncio.sleep(0.1)  # Simulate network call
    raise ValueError(f"API call {i} failed at {datetime.now().isoformat()}")

async def main():
    """Run the circuit breaker example"""
    await example_circuit_breaker_usage()

if __name__ == "__main__":
    asyncio.run(main())