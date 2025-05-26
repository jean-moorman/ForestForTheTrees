import pytest
import pytest_asyncio
import asyncio
import time
import logging
import sys
import os
from datetime import datetime

# Adjust path to import from the FFTT package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from resources.events import EventQueue, ResourceEventTypes
from resources.errors import ResourceError, ResourceOperationError, ResourceTimeoutError, ErrorSeverity
from resources.base import BaseManager, ErrorHandler, ErrorClassification

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_error_recovery")

# Create a test manager with simulated error scenarios
class TestRecoveryManager(BaseManager):
    """Concrete implementation of BaseManager for testing recovery strategies"""
    def __init__(self, event_queue):
        super().__init__(event_queue=event_queue)
        self.recovery_attempts = {}
        self.cleanup_called = False
        self.forced_cleanup_called = False
        self.stop_called = False
        self.start_called = False
        
    async def simulate_error(self, error_type, recovery_strategy=None):
        """Simulate different types of errors with specified recovery strategy"""
        if error_type == "timeout":
            error = ResourceTimeoutError(
                resource_id="test_resource",
                operation="test_operation",
                timeout_seconds=1.0,
                details={"test": True}
            )
            if recovery_strategy:
                error.recovery_strategy = recovery_strategy
            else:
                error.recovery_strategy = "retry_with_backoff"
                
        elif error_type == "resource_exhaustion":
            error = ResourceOperationError(
                message="Resource exhausted",
                resource_id="test_resource",
                severity=ErrorSeverity.DEGRADED,
                operation="test_operation",
                recovery_strategy=recovery_strategy or "force_cleanup",
                details={"test": True}
            )
            
        elif error_type == "critical":
            error = ResourceOperationError(
                message="Critical error",
                resource_id="test_resource",
                severity=ErrorSeverity.FATAL,
                operation="test_operation",
                recovery_strategy=recovery_strategy or "emergency_cleanup",
                details={"test": True}
            )
            
        else:  # General error
            error = ResourceOperationError(
                message="General error",
                resource_id="test_resource",
                severity=ErrorSeverity.TRANSIENT,
                operation="test_operation",
                recovery_strategy=recovery_strategy or "retry_with_backoff",
                details={"test": True}
            )
            
        # Simulate error handling
        await self.handle_operation_error(error, "test_operation")
        return error
    
    async def cleanup(self, force=False):
        """Required implementation of abstract method"""
        logger.debug(f"Cleanup called with force={force}")
        self.cleanup_called = True
        if force:
            self.forced_cleanup_called = True
    
    async def stop(self):
        """Simulate component stop for restart strategy"""
        logger.debug("Stop called")
        self.stop_called = True
        await super().stop()
        
    async def start(self):
        """Simulate component start for restart strategy"""
        logger.debug("Start called")
        self.start_called = True
        await super().start()

@pytest_asyncio.fixture
async def event_queue():
    """Create a new event queue for each test."""
    queue = EventQueue(max_size=100)
    await queue.start()
    yield queue
    await queue.stop()

@pytest_asyncio.fixture
async def recovery_manager(event_queue):
    """Create a test recovery manager for testing."""
    manager = TestRecoveryManager(event_queue=event_queue)
    yield manager
    # No specific cleanup needed

class TestErrorRecoveryStrategies:
    """Tests for the enhanced error recovery strategies."""
    
    @pytest.mark.asyncio
    async def test_force_cleanup_strategy(self, recovery_manager):
        """Test the force_cleanup recovery strategy."""
        # Simulate an error with force_cleanup strategy
        error = await recovery_manager.simulate_error("resource_exhaustion", "force_cleanup")
        
        # Verify strategy was implemented
        assert recovery_manager.cleanup_called is True
        assert recovery_manager.forced_cleanup_called is True
        
        # Verify the error was properly classified
        assert error.recovery_strategy == "force_cleanup"
    
    @pytest.mark.asyncio
    async def test_reduce_load_strategy(self, recovery_manager):
        """Test the reduce_load recovery strategy."""
        # Simulate an error with reduce_load strategy
        error = await recovery_manager.simulate_error("resource_exhaustion", "reduce_load")
        
        # Verify strategy was implemented (standard cleanup)
        assert recovery_manager.cleanup_called is True
        assert recovery_manager.forced_cleanup_called is False
        
        # Verify the error was properly classified
        assert error.recovery_strategy == "reduce_load"
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff_strategy(self, recovery_manager):
        """Test the retry_with_backoff recovery strategy."""
        # Simulate a timeout error which defaults to retry_with_backoff
        error = await recovery_manager.simulate_error("timeout")
        
        # This strategy doesn't do much in the manager, just acknowledges the retry
        # will happen elsewhere (in the event system's retry logic)
        assert error.recovery_strategy == "retry_with_backoff"
    
    @pytest.mark.asyncio
    async def test_restart_component_strategy(self, recovery_manager):
        """Test the restart_component recovery strategy."""
        # Simulate an error with restart_component strategy
        error = await recovery_manager.simulate_error("critical", "restart_component")
        
        # Verify strategy was implemented
        assert recovery_manager.cleanup_called is True
        assert recovery_manager.forced_cleanup_called is True
        assert recovery_manager.stop_called is True
        assert recovery_manager.start_called is True
        
        # Verify the error was properly classified
        assert error.recovery_strategy == "restart_component"
    
    @pytest.mark.asyncio
    async def test_emergency_cleanup_strategy(self, recovery_manager):
        """Test the emergency_cleanup recovery strategy."""
        # Track alert events
        alert_events = []
        
        async def alert_listener(event_type, data):
            if event_type == ResourceEventTypes.RESOURCE_ALERT_CREATED.value:
                alert_events.append(data)
        
        # Subscribe to alert events
        await recovery_manager._event_queue.subscribe(
            ResourceEventTypes.RESOURCE_ALERT_CREATED.value, 
            alert_listener
        )
        
        try:
            # Simulate a critical error with emergency_cleanup strategy
            error = await recovery_manager.simulate_error("critical", "emergency_cleanup")
            
            # Verify strategy was implemented
            assert recovery_manager.cleanup_called is True
            assert recovery_manager.forced_cleanup_called is True
            
            # Allow time for event processing
            await asyncio.sleep(0.2)
            
            # Verify alert was emitted
            assert len(alert_events) >= 1
            alert = alert_events[0]
            assert alert["alert_type"] == "emergency_cleanup_performed"
            assert alert["severity"] == "CRITICAL"
            
            # Verify the error was properly classified
            assert error.recovery_strategy == "emergency_cleanup"
        finally:
            # Unsubscribe from alerts
            await recovery_manager._event_queue.unsubscribe(
                ResourceEventTypes.RESOURCE_ALERT_CREATED.value, 
                alert_listener
            )
    
    @pytest.mark.asyncio
    async def test_manual_intervention_required_strategy(self, recovery_manager):
        """Test the manual_intervention_required recovery strategy."""
        # Track alert events
        alert_events = []
        
        async def alert_listener(event_type, data):
            if event_type == ResourceEventTypes.RESOURCE_ALERT_CREATED.value:
                alert_events.append(data)
        
        # Subscribe to alert events
        await recovery_manager._event_queue.subscribe(
            ResourceEventTypes.RESOURCE_ALERT_CREATED.value, 
            alert_listener
        )
        
        try:
            # Simulate a critical error with manual_intervention strategy
            error = await recovery_manager.simulate_error("critical", "manual_intervention_required")
            
            # Verify strategy was implemented (no automatic recovery)
            assert recovery_manager.cleanup_called is False
            assert recovery_manager.forced_cleanup_called is False
            
            # Allow time for event processing
            await asyncio.sleep(0.2)
            
            # Verify alert was emitted
            assert len(alert_events) >= 1
            alert = alert_events[0]
            assert alert["alert_type"] == "manual_intervention_required"
            assert alert["severity"] == "CRITICAL"
            
            # Verify the error was properly classified
            assert error.recovery_strategy == "manual_intervention_required"
        finally:
            # Unsubscribe from alerts
            await recovery_manager._event_queue.unsubscribe(
                ResourceEventTypes.RESOURCE_ALERT_CREATED.value, 
                alert_listener
            )
    
    @pytest.mark.asyncio
    async def test_recovery_tracking(self, recovery_manager, event_queue):
        """Test that recovery attempts are properly tracked and events emitted."""
        # Track recovery events
        recovery_events = []
        
        async def recovery_listener(event_type, data):
            if event_type in [
                ResourceEventTypes.RESOURCE_ERROR_RECOVERY_STARTED.value,
                ResourceEventTypes.RESOURCE_ERROR_RECOVERY_COMPLETED.value,
                ResourceEventTypes.RESOURCE_ERROR_RESOLVED.value
            ]:
                recovery_events.append((event_type, data))
        
        # Subscribe to recovery events
        await event_queue.subscribe(
            ResourceEventTypes.RESOURCE_ERROR_RECOVERY_STARTED.value,
            recovery_listener
        )
        await event_queue.subscribe(
            ResourceEventTypes.RESOURCE_ERROR_RECOVERY_COMPLETED.value,
            recovery_listener
        )
        await event_queue.subscribe(
            ResourceEventTypes.RESOURCE_ERROR_RESOLVED.value,
            recovery_listener
        )
        
        try:
            # Simulate error and recovery
            error = await recovery_manager.simulate_error("resource_exhaustion", "force_cleanup")
            
            # Allow time for event processing
            await asyncio.sleep(0.2)
            
            # Verify recovery events were emitted
            assert len(recovery_events) > 0
            
            # We should have either a recovery_started or recovery_completed event
            event_types = [e[0] for e in recovery_events]
            assert ResourceEventTypes.RESOURCE_ERROR_RECOVERY_STARTED.value in event_types or \
                   ResourceEventTypes.RESOURCE_ERROR_RECOVERY_COMPLETED.value in event_types
                   
        finally:
            # Unsubscribe from recovery events
            await event_queue.unsubscribe(
                ResourceEventTypes.RESOURCE_ERROR_RECOVERY_STARTED.value,
                recovery_listener
            )
            await event_queue.unsubscribe(
                ResourceEventTypes.RESOURCE_ERROR_RECOVERY_COMPLETED.value,
                recovery_listener
            )
            await event_queue.unsubscribe(
                ResourceEventTypes.RESOURCE_ERROR_RESOLVED.value,
                recovery_listener
            )

# Run the tests if file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])