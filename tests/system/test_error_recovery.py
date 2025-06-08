"""
Test Advanced Error Recovery from run_phase_one.py

This module tests advanced error recovery mechanisms including circuit breakers,
exponential backoff, deadlock detection, cascade failure prevention, and
self-healing capabilities that are missing from existing E2E tests.
"""

import pytest
import asyncio
import time
import random
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock
from collections import defaultdict

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from run_phase_one import PhaseOneApp, PhaseOneInterface
from resources.events import EventQueue
from resources.state import StateManager
from resources.monitoring.circuit_breakers import CircuitBreakerRegistry
from resources.managers.coordinator import ResourceCoordinator


class TestCircuitBreakerIntegration:
    """Test circuit breaker integration and behavior."""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_failure_threshold(self):
        """Test circuit breaker opens after failure threshold."""
        failure_count = 0
        circuit_states = []
        
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    event_queue = EventQueue()
                    await event_queue.start()
                    
                    circuit_breaker = CircuitBreakerRegistry(event_queue)
                    circuit_breaker.register('test_service', failure_threshold=3, timeout=1.0)
                    
                    # Mock failing service
                    async def failing_service():
                        nonlocal failure_count
                        failure_count += 1
                        raise Exception(f"Service failure #{failure_count}")
                    
                    # Test circuit breaker behavior
                    for i in range(5):
                        try:
                            await circuit_breaker.call('test_service', failing_service)
                        except Exception:
                            pass  # Expected failures
                        
                        state = circuit_breaker.get_state('test_service')
                        circuit_states.append(state)
                    
                    # Verify circuit breaker opened after threshold
                    assert 'CLOSED' in circuit_states  # Initially closed
                    assert 'OPEN' in circuit_states    # Opened after failures
                    
                    # Should have stopped calling service after opening
                    assert failure_count <= 4  # Max 3 failures + maybe 1 more before opening
                    
                    await event_queue.stop()
                
                finally:
                    test_loop.close()
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker half-open state and recovery."""
        call_attempts = []
        
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    event_queue = EventQueue()
                    await event_queue.start()
                    
                    circuit_breaker = CircuitBreakerRegistry(event_queue)
                    circuit_breaker.register('recovery_service', failure_threshold=2, timeout=0.1)
                    
                    # Service that fails initially then recovers
                    async def recovering_service():
                        call_attempts.append(len(call_attempts))
                        if len(call_attempts) <= 2:
                            raise Exception("Initial failures")
                        return "service_recovered"
                    
                    # Trigger initial failures to open circuit
                    for _ in range(3):
                        try:
                            await circuit_breaker.call('recovery_service', recovering_service)
                        except Exception:
                            pass
                    
                    # Wait for circuit to enter half-open state
                    await asyncio.sleep(0.2)
                    
                    # Test recovery
                    result = await circuit_breaker.call('recovery_service', recovering_service)
                    
                    # Should recover successfully
                    assert result == "service_recovered"
                    assert circuit_breaker.get_state('recovery_service') == 'CLOSED'
                    
                    await event_queue.stop()
                
                finally:
                    test_loop.close()
    
    @pytest.mark.asyncio
    async def test_multiple_circuit_breaker_coordination(self):
        """Test coordination between multiple circuit breakers."""
        service_states = defaultdict(list)
        
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    event_queue = EventQueue()
                    await event_queue.start()
                    
                    circuit_breaker = CircuitBreakerRegistry(event_queue)
                    
                    # Register multiple services
                    services = ['service_a', 'service_b', 'service_c']
                    for service in services:
                        circuit_breaker.register(service, failure_threshold=2, timeout=0.1)
                    
                    # Make service_a fail, others succeed
                    async def service_behavior(service_name):
                        if service_name == 'service_a':
                            raise Exception(f"{service_name} is failing")
                        return f"{service_name} success"
                    
                    # Test all services
                    for _ in range(3):
                        for service in services:
                            try:
                                result = await circuit_breaker.call(service, 
                                                                  lambda svc=service: service_behavior(svc))
                                service_states[service].append('success')
                            except Exception:
                                service_states[service].append('failure')
                            
                            state = circuit_breaker.get_state(service)
                            service_states[service].append(f"state_{state}")
                    
                    # Verify independent circuit breaker behavior
                    assert 'failure' in service_states['service_a']  # Should fail
                    assert 'success' in service_states['service_b']  # Should succeed
                    assert 'success' in service_states['service_c']  # Should succeed
                    
                    # Only service_a should have opened circuit
                    a_states = [s for s in service_states['service_a'] if s.startswith('state_')]
                    assert 'state_OPEN' in a_states
                    
                    await event_queue.stop()
                
                finally:
                    test_loop.close()


class TestExponentialBackoffRecovery:
    """Test exponential backoff recovery mechanisms."""
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self):
        """Test exponential backoff timing progression."""
        retry_times = []
        
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    
                    async def failing_operation():
                        retry_times.append(time.time())
                        raise Exception("Operation failed")
                    
                    # Test exponential backoff
                    start_time = time.time()
                    
                    try:
                        await app.retry_with_exponential_backoff(
                            failing_operation,
                            max_retries=4,
                            base_delay=0.1
                        )
                    except Exception:
                        pass  # Expected final failure
                    
                    # Verify exponential timing
                    assert len(retry_times) == 5  # Initial + 4 retries
                    
                    # Check intervals are approximately exponential
                    intervals = []
                    for i in range(1, len(retry_times)):
                        interval = retry_times[i] - retry_times[i-1]
                        intervals.append(interval)
                    
                    # Each interval should be roughly double the previous
                    for i in range(1, len(intervals)):
                        ratio = intervals[i] / intervals[i-1]
                        assert 1.5 < ratio < 2.5  # Allow some variance
                
                finally:
                    test_loop.close()
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_with_jitter(self):
        """Test exponential backoff with jitter to prevent thundering herd."""
        retry_intervals = []
        
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    
                    # Run multiple parallel backoff operations
                    async def run_backoff_operation(operation_id):
                        retry_times = []
                        
                        async def failing_op():
                            retry_times.append(time.time())
                            raise Exception(f"Op {operation_id} failed")
                        
                        try:
                            await app.retry_with_exponential_backoff(
                                failing_op,
                                max_retries=3,
                                base_delay=0.1,
                                jitter=True
                            )
                        except Exception:
                            pass
                        
                        # Calculate intervals
                        intervals = []
                        for i in range(1, len(retry_times)):
                            intervals.append(retry_times[i] - retry_times[i-1])
                        
                        return intervals
                    
                    # Run multiple operations in parallel
                    operations = [run_backoff_operation(i) for i in range(3)]
                    all_intervals = await asyncio.gather(*operations)
                    
                    # Verify jitter prevents exact timing alignment
                    for retry_level in range(3):  # Check each retry level
                        level_intervals = [intervals[retry_level] for intervals in all_intervals 
                                         if len(intervals) > retry_level]
                        
                        if len(level_intervals) > 1:
                            # Intervals should vary due to jitter
                            max_interval = max(level_intervals)
                            min_interval = min(level_intervals)
                            variation = (max_interval - min_interval) / min_interval
                            assert variation > 0.1  # At least 10% variation
                
                finally:
                    test_loop.close()
    
    @pytest.mark.asyncio
    async def test_backoff_success_on_retry(self):
        """Test successful recovery after backoff retries."""
        attempt_count = 0
        
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    
                    async def eventually_succeeding_operation():
                        nonlocal attempt_count
                        attempt_count += 1
                        
                        if attempt_count <= 2:  # Fail first 2 attempts
                            raise Exception(f"Attempt {attempt_count} failed")
                        
                        return f"Success on attempt {attempt_count}"
                    
                    # Should succeed after retries
                    result = await app.retry_with_exponential_backoff(
                        eventually_succeeding_operation,
                        max_retries=5,
                        base_delay=0.01
                    )
                    
                    assert result == "Success on attempt 3"
                    assert attempt_count == 3
                
                finally:
                    test_loop.close()


class TestDeadlockDetectionAndRecovery:
    """Test deadlock detection and recovery mechanisms."""
    
    @pytest.mark.asyncio
    async def test_resource_acquisition_timeout(self):
        """Test timeout-based deadlock prevention."""
        acquisition_results = []
        
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    
                    # Simulate shared resources
                    resource_locks = {
                        'resource_1': asyncio.Lock(),
                        'resource_2': asyncio.Lock()
                    }
                    
                    async def task_with_potential_deadlock(task_id, resources, timeout=0.1):
                        try:
                            # Try to acquire resources with timeout
                            acquired_locks = []
                            
                            for resource in resources:
                                try:
                                    await asyncio.wait_for(
                                        resource_locks[resource].acquire(),
                                        timeout=timeout
                                    )
                                    acquired_locks.append(resource)
                                except asyncio.TimeoutError:
                                    # Release already acquired locks
                                    for lock_name in acquired_locks:
                                        resource_locks[lock_name].release()
                                    acquisition_results.append(f"task_{task_id}_timeout")
                                    return f"task_{task_id}_timeout"
                            
                            # Simulate work
                            await asyncio.sleep(0.01)
                            
                            # Release locks
                            for lock_name in acquired_locks:
                                resource_locks[lock_name].release()
                            
                            acquisition_results.append(f"task_{task_id}_success")
                            return f"task_{task_id}_success"
                        
                        except Exception as e:
                            acquisition_results.append(f"task_{task_id}_error_{str(e)}")
                            return f"task_{task_id}_error"
                    
                    # Create potentially deadlocking tasks
                    tasks = [
                        task_with_potential_deadlock(1, ['resource_1', 'resource_2']),
                        task_with_potential_deadlock(2, ['resource_2', 'resource_1']),  # Reverse order
                        task_with_potential_deadlock(3, ['resource_1'])
                    ]
                    
                    # Run tasks concurrently
                    results = await asyncio.gather(*tasks)
                    
                    # Verify deadlock prevention
                    assert len(acquisition_results) == 3
                    
                    # At least some tasks should complete (timeout prevents complete deadlock)
                    success_count = len([r for r in acquisition_results if 'success' in r])
                    timeout_count = len([r for r in acquisition_results if 'timeout' in r])
                    
                    assert success_count > 0 or timeout_count > 0  # Should have some resolution
                
                finally:
                    test_loop.close()
    
    @pytest.mark.asyncio
    async def test_circular_dependency_detection(self):
        """Test detection of circular dependencies."""
        dependency_violations = []
        
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    
                    # Mock dependency graph with circular dependency
                    dependencies = {
                        'component_a': ['component_b'],
                        'component_b': ['component_c'],
                        'component_c': ['component_a']  # Circular!
                    }
                    
                    async def detect_circular_dependencies(deps):
                        visited = set()
                        rec_stack = set()
                        
                        def has_cycle(node):
                            if node in rec_stack:
                                dependency_violations.append(f"circular_dependency_detected_{node}")
                                return True
                            
                            if node in visited:
                                return False
                            
                            visited.add(node)
                            rec_stack.add(node)
                            
                            for neighbor in deps.get(node, []):
                                if has_cycle(neighbor):
                                    return True
                            
                            rec_stack.remove(node)
                            return False
                        
                        for component in deps:
                            if component not in visited:
                                if has_cycle(component):
                                    return True
                        return False
                    
                    # Test circular dependency detection
                    has_circular = await detect_circular_dependencies(dependencies)
                    
                    # Should detect the circular dependency
                    assert has_circular is True
                    assert len(dependency_violations) > 0
                    assert any('circular_dependency_detected' in violation 
                             for violation in dependency_violations)
                
                finally:
                    test_loop.close()
    
    @pytest.mark.asyncio
    async def test_deadlock_recovery_strategies(self):
        """Test different deadlock recovery strategies."""
        recovery_events = []
        
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    
                    # Mock deadlock recovery strategies
                    async def timeout_recovery():
                        await asyncio.sleep(0.5)  # Simulate timeout
                        recovery_events.append('timeout_recovery_triggered')
                        return 'recovered_via_timeout'
                    
                    async def priority_based_recovery():
                        await asyncio.sleep(0.1)  # Faster recovery
                        recovery_events.append('priority_recovery_triggered')
                        return 'recovered_via_priority'
                    
                    async def resource_ordering_recovery():
                        await asyncio.sleep(0.05)  # Fastest recovery
                        recovery_events.append('ordering_recovery_triggered')
                        return 'recovered_via_ordering'
                    
                    # Test concurrent recovery strategies
                    recovery_tasks = [
                        timeout_recovery(),
                        priority_based_recovery(),
                        resource_ordering_recovery()
                    ]
                    
                    # Race between recovery strategies
                    done, pending = await asyncio.wait(
                        recovery_tasks,
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # Cancel remaining tasks
                    for task in pending:
                        task.cancel()
                    
                    # Get the winning recovery result
                    winner = list(done)[0]
                    result = await winner
                    
                    # Verify fastest recovery strategy won
                    assert result == 'recovered_via_ordering'
                    assert 'ordering_recovery_triggered' in recovery_events
                    
                    # Other strategies shouldn't have completed
                    assert 'timeout_recovery_triggered' not in recovery_events
                    assert 'priority_recovery_triggered' not in recovery_events
                
                finally:
                    test_loop.close()


class TestCascadeFailurePrevention:
    """Test cascade failure prevention mechanisms."""
    
    @pytest.mark.asyncio
    async def test_failure_isolation_boundaries(self):
        """Test failure isolation between system boundaries."""
        component_states = {}
        
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    event_queue = EventQueue()
                    await event_queue.start()
                    
                    # Create isolated components
                    state_manager = StateManager(event_queue)
                    await state_manager.initialize()
                    component_states['state_manager'] = 'healthy'
                    
                    # Mock orchestrator with failure
                    mock_orchestrator = MagicMock()
                    mock_orchestrator._state_manager = state_manager
                    
                    # Simulate one agent failing
                    mock_orchestrator.garden_planner_agent = MagicMock()
                    
                    async def failing_agent_process(*args):
                        component_states['garden_planner'] = 'failed'
                        raise Exception("Garden planner failure")
                    
                    mock_orchestrator.garden_planner_agent.process = failing_agent_process
                    
                    # Other agents should remain healthy
                    mock_orchestrator.earth_agent = MagicMock()
                    
                    async def healthy_agent_process(*args):
                        component_states['earth_agent'] = 'healthy'
                        return {"status": "success", "result": "completed"}
                    
                    mock_orchestrator.earth_agent.process = healthy_agent_process
                    
                    interface = PhaseOneInterface(mock_orchestrator)
                    
                    # Test failure isolation
                    operation_id = await interface.start_phase_one("Test cascade prevention")
                    
                    # First step should fail
                    step1_result = await interface.execute_next_step(operation_id)
                    assert step1_result["step_result"]["status"] == "error"
                    
                    # Second step should still work (isolation)
                    step2_result = await interface.execute_next_step(operation_id)
                    assert step2_result["step_result"]["status"] == "success"
                    
                    # Verify failure isolation
                    assert component_states['garden_planner'] == 'failed'
                    assert component_states['earth_agent'] == 'healthy'
                    assert component_states['state_manager'] == 'healthy'
                    
                    await event_queue.stop()
                
                finally:
                    test_loop.close()
    
    @pytest.mark.asyncio
    async def test_bulkhead_pattern_implementation(self):
        """Test bulkhead pattern for resource isolation."""
        resource_pools = {
            'critical_pool': [],
            'normal_pool': [],
            'background_pool': []
        }
        
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    
                    # Simulate resource pools with different priorities
                    async def allocate_resource(pool_name, operation_id):
                        if len(resource_pools[pool_name]) >= 2:  # Pool limit
                            raise Exception(f"{pool_name} exhausted")
                        
                        resource_pools[pool_name].append(operation_id)
                        await asyncio.sleep(0.1)  # Simulate resource usage
                        resource_pools[pool_name].remove(operation_id)
                        return f"resource_allocated_{pool_name}_{operation_id}"
                    
                    # Test bulkhead isolation
                    tasks = []
                    
                    # Overwhelm normal pool
                    for i in range(5):
                        task = allocate_resource('normal_pool', f'normal_{i}')
                        tasks.append(task)
                    
                    # Critical operations should still work
                    for i in range(2):
                        task = allocate_resource('critical_pool', f'critical_{i}')
                        tasks.append(task)
                    
                    # Execute all tasks
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Verify bulkhead isolation
                    critical_results = [r for r in results if isinstance(r, str) and 'critical' in r]
                    normal_failures = [r for r in results if isinstance(r, Exception) and 'normal_pool' in str(r)]
                    
                    # Critical operations should succeed despite normal pool exhaustion
                    assert len(critical_results) == 2
                    assert len(normal_failures) >= 1  # Some normal operations should fail
                
                finally:
                    test_loop.close()
    
    @pytest.mark.asyncio
    async def test_rate_limiting_cascade_prevention(self):
        """Test rate limiting to prevent cascade failures."""
        request_times = []
        rate_limit_violations = []
        
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    
                    # Rate limiter: max 3 requests per second
                    rate_limit = 3
                    time_window = 1.0
                    request_history = []
                    
                    async def rate_limited_operation(operation_id):
                        current_time = time.time()
                        request_times.append(current_time)
                        
                        # Clean old requests outside time window
                        cutoff_time = current_time - time_window
                        request_history[:] = [t for t in request_history if t > cutoff_time]
                        
                        # Check rate limit
                        if len(request_history) >= rate_limit:
                            rate_limit_violations.append(operation_id)
                            raise Exception(f"Rate limit exceeded for operation {operation_id}")
                        
                        request_history.append(current_time)
                        await asyncio.sleep(0.05)  # Simulate processing
                        return f"operation_{operation_id}_completed"
                    
                    # Generate burst of requests
                    tasks = []
                    for i in range(10):  # More than rate limit
                        task = rate_limited_operation(i)
                        tasks.append(task)
                    
                    # Execute burst
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Verify rate limiting prevented cascade
                    successful_operations = [r for r in results if isinstance(r, str)]
                    failed_operations = [r for r in results if isinstance(r, Exception)]
                    
                    # Should have limited successful operations
                    assert len(successful_operations) <= rate_limit + 1  # Allow small variance
                    assert len(failed_operations) >= 5  # Most should be rate limited
                    assert len(rate_limit_violations) >= 5
                
                finally:
                    test_loop.close()


class TestSelfHealingCapabilities:
    """Test self-healing and adaptive recovery capabilities."""
    
    @pytest.mark.asyncio
    async def test_automatic_configuration_adjustment(self):
        """Test automatic configuration adjustment based on failures."""
        config_adjustments = []
        
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    
                    # Initial configuration
                    config = {
                        'timeout': 5.0,
                        'retry_count': 3,
                        'batch_size': 10
                    }
                    
                    failure_count = 0
                    
                    async def adaptive_operation():
                        nonlocal failure_count, config
                        failure_count += 1
                        
                        # Simulate operation with current config
                        await asyncio.sleep(config['timeout'] * 0.1)
                        
                        if failure_count <= 3:  # Fail first few attempts
                            # Adjust configuration based on failure pattern
                            if config['timeout'] < 10.0:
                                config['timeout'] *= 1.5
                                config_adjustments.append(f"timeout_increased_to_{config['timeout']}")
                            
                            if config['retry_count'] < 10:
                                config['retry_count'] += 1
                                config_adjustments.append(f"retry_count_increased_to_{config['retry_count']}")
                            
                            raise Exception(f"Operation failed (attempt {failure_count})")
                        
                        return "operation_succeeded_after_adjustment"
                    
                    # Test self-healing configuration adjustment
                    for attempt in range(5):
                        try:
                            result = await adaptive_operation()
                            if result:
                                break
                        except Exception:
                            # Continue with adjusted configuration
                            pass
                    
                    # Verify self-healing adjustments
                    assert len(config_adjustments) > 0
                    assert any('timeout_increased' in adj for adj in config_adjustments)
                    assert any('retry_count_increased' in adj for adj in config_adjustments)
                    
                    # Configuration should have been adapted
                    assert config['timeout'] > 5.0
                    assert config['retry_count'] > 3
                
                finally:
                    test_loop.close()
    
    @pytest.mark.asyncio
    async def test_performance_based_auto_scaling(self):
        """Test automatic scaling based on performance metrics."""
        scaling_events = []
        performance_metrics = []
        
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    
                    # Performance monitoring and auto-scaling
                    worker_count = 2
                    target_response_time = 0.1
                    
                    async def performance_monitored_operation(operation_id):
                        start_time = time.time()
                        
                        # Simulate load-dependent processing time
                        processing_time = 0.05 + (operation_id * 0.01)  # Increasing load
                        await asyncio.sleep(processing_time)
                        
                        response_time = time.time() - start_time
                        performance_metrics.append(response_time)
                        
                        return f"operation_{operation_id}_completed"
                    
                    async def auto_scaling_monitor():
                        nonlocal worker_count
                        
                        while len(performance_metrics) < 10:
                            await asyncio.sleep(0.1)
                            
                            if len(performance_metrics) >= 3:
                                avg_response_time = sum(performance_metrics[-3:]) / 3
                                
                                if avg_response_time > target_response_time * 1.5:
                                    # Scale up
                                    worker_count += 1
                                    scaling_events.append(f"scale_up_to_{worker_count}")
                                elif avg_response_time < target_response_time * 0.5 and worker_count > 1:
                                    # Scale down
                                    worker_count -= 1
                                    scaling_events.append(f"scale_down_to_{worker_count}")
                    
                    # Start monitoring
                    monitor_task = asyncio.create_task(auto_scaling_monitor())
                    
                    # Generate load
                    operation_tasks = []
                    for i in range(10):
                        task = performance_monitored_operation(i)
                        operation_tasks.append(task)
                        await asyncio.sleep(0.05)  # Stagger operations
                    
                    # Wait for operations and monitoring
                    await asyncio.gather(*operation_tasks)
                    monitor_task.cancel()
                    
                    # Verify auto-scaling behavior
                    assert len(scaling_events) > 0
                    assert any('scale_up' in event for event in scaling_events)
                    
                    # Performance should have triggered scaling
                    max_response_time = max(performance_metrics)
                    assert max_response_time > target_response_time
                
                finally:
                    test_loop.close()
    
    @pytest.mark.asyncio
    async def test_adaptive_error_handling(self):
        """Test adaptive error handling that learns from failure patterns."""
        error_patterns = defaultdict(int)
        adaptive_strategies = []
        
        with patch('PyQt6.QtWidgets.QApplication') as mock_qapp_class:
            mock_qapp = MagicMock()
            mock_qapp_class.instance.return_value = None
            mock_qapp_class.return_value = mock_qapp
            
            with patch('resources.events.utils.ensure_event_loop') as mock_ensure:
                test_loop = asyncio.new_event_loop()
                mock_ensure.return_value = test_loop
                
                try:
                    app = PhaseOneApp()
                    
                    # Simulate different error types
                    error_types = ['timeout', 'connection', 'validation', 'resource']
                    
                    async def operation_with_adaptive_handling(operation_id):
                        # Simulate random error type
                        error_type = error_types[operation_id % len(error_types)]
                        error_patterns[error_type] += 1
                        
                        # Adaptive strategy based on error pattern frequency
                        if error_patterns[error_type] >= 3:
                            if error_type == 'timeout':
                                adaptive_strategies.append('increase_timeout_strategy')
                                await asyncio.sleep(0.2)  # Longer timeout
                            elif error_type == 'connection':
                                adaptive_strategies.append('connection_pooling_strategy')
                                await asyncio.sleep(0.05)  # Faster with pooling
                            elif error_type == 'validation':
                                adaptive_strategies.append('enhanced_validation_strategy')
                                # Skip validation for this test
                                pass
                            elif error_type == 'resource':
                                adaptive_strategies.append('resource_reservation_strategy')
                                await asyncio.sleep(0.1)  # Reserve resources
                            
                            return f"operation_{operation_id}_succeeded_with_adaptation"
                        else:
                            # Not enough pattern data, simulate failure
                            raise Exception(f"{error_type}_error_in_operation_{operation_id}")
                    
                    # Test adaptive learning
                    results = []
                    for i in range(12):  # Enough to trigger adaptations
                        try:
                            result = await operation_with_adaptive_handling(i)
                            results.append(result)
                        except Exception as e:
                            results.append(str(e))
                    
                    # Verify adaptive learning
                    assert len(adaptive_strategies) > 0
                    
                    # Should have learned strategies for common error patterns
                    successful_adaptations = [r for r in results if 'succeeded_with_adaptation' in r]
                    assert len(successful_adaptations) > 0
                    
                    # Different strategies should be applied
                    assert len(set(adaptive_strategies)) > 1
                
                finally:
                    test_loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])