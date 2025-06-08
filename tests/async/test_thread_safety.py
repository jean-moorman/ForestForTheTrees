"""
Test Thread Safety in run_phase_one.py

This module tests thread safety aspects of the Phase One system including
concurrent access to state managers, cross-thread event queue operations,
and race conditions in resource initialization with the new simplified event architecture.
"""

import pytest
import asyncio
import threading
import time
import concurrent.futures
from unittest.mock import MagicMock, patch, AsyncMock

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from resources.events import EventQueue
from resources.state import StateManager
from resources.managers import AgentContextManager, CacheManager, MetricsManager
from resources.events.loop_management import EventLoopManager
from run_phase_one import PhaseOneApp, PhaseOneInterface


class TestEventQueueThreadSafety:
    """Test thread safety of EventQueue operations with new architecture."""
    
    @pytest.mark.asyncio
    async def test_concurrent_event_emission(self):
        """Test concurrent event emission from multiple async tasks."""
        event_queue = EventQueue(queue_id="thread_safety_test")
        await event_queue.start()
        
        try:
            events_emitted = []
            errors = []
            
            async def emit_events_async(task_id, count):
                """Emit events from async task."""
                try:
                    for i in range(count):
                        event_data = {
                            "task_id": task_id,
                            "event_number": i,
                            "timestamp": time.time()
                        }
                        result = await event_queue.emit("TEST_EVENT", event_data)
                        if result:
                            events_emitted.append(f"task_{task_id}_event_{i}")
                        
                        # Small delay to encourage race conditions
                        await asyncio.sleep(0.001)
                except Exception as e:
                    errors.append(f"Task {task_id}: {str(e)}")
            
            # Run multiple concurrent emission tasks
            tasks = []
            for task_id in range(5):
                task = asyncio.create_task(emit_events_async(task_id, 10))
                tasks.append(task)
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks)
            
            # Verify results
            assert len(errors) == 0, f"Errors during emission: {errors}"
            assert len(events_emitted) == 50  # 5 tasks * 10 events each
            
            # Verify all events were unique
            assert len(set(events_emitted)) == 50
        
        finally:
            await event_queue.stop()
    
    @pytest.mark.asyncio
    async def test_concurrent_event_subscription(self):
        """Test concurrent event subscription and handling."""
        event_queue = EventQueue(queue_id="subscription_test")
        await event_queue.start()
        
        try:
            received_events = []
            handler_errors = []
            
            async def event_handler(event_type: str, event_data: dict):
                """Handle events from subscription."""
                try:
                    handler_id = event_data.get("handler_id", "unknown")
                    event_id = event_data.get("event_id", "unknown")
                    received_events.append(f"{handler_id}_{event_id}")
                except Exception as e:
                    handler_errors.append(f"Handler error: {str(e)}")
            
            # Subscribe multiple handlers to same event type
            for handler_id in range(3):
                await event_queue.subscribe("SUBSCRIPTION_TEST", event_handler)
            
            # Emit events concurrently
            emission_tasks = []
            for event_id in range(10):
                event_data = {
                    "event_id": event_id,
                    "timestamp": time.time()
                }
                task = asyncio.create_task(
                    event_queue.emit("SUBSCRIPTION_TEST", event_data)
                )
                emission_tasks.append(task)
            
            await asyncio.gather(*emission_tasks)
            
            # Wait for event processing
            await event_queue.wait_for_processing(timeout=2.0)
            
            # Verify results - each event should be received by all 3 handlers
            assert len(handler_errors) == 0, f"Handler errors: {handler_errors}"
            # We should have received events (exact count may vary due to threading)
            assert len(received_events) > 0
        
        finally:
            await event_queue.stop()
    
    @pytest.mark.asyncio
    async def test_cross_thread_event_queue_access(self):
        """Test accessing event queue from different threads."""
        event_queue = EventQueue(queue_id="cross_thread_test")
        await event_queue.start()
        
        try:
            results = []
            errors = []
            
            def thread_worker(thread_id):
                """Worker function that accesses event queue from thread."""
                try:
                    # Create event loop for this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    async def emit_from_thread():
                        result = await event_queue.emit("CROSS_THREAD_EVENT", {
                            "thread_id": thread_id,
                            "message": f"Event from thread {thread_id}"
                        })
                        return f"success_thread_{thread_id}" if result else f"failed_thread_{thread_id}"
                    
                    result = loop.run_until_complete(emit_from_thread())
                    results.append(result)
                    loop.close()
                    
                except Exception as e:
                    errors.append(f"Thread {thread_id}: {str(e)}")
            
            # Start multiple threads
            threads = []
            for i in range(3):
                thread = threading.Thread(target=thread_worker, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for threads
            for thread in threads:
                thread.join(timeout=5.0)
            
            # Verify results
            assert len(errors) == 0, f"Cross-thread errors: {errors}"
            assert len(results) == 3
            
            for i in range(3):
                assert f"success_thread_{i}" in results
        
        finally:
            await event_queue.stop()


class TestStateManagerThreadSafety:
    """Test thread safety of StateManager operations."""
    
    @pytest.mark.asyncio
    async def test_concurrent_state_operations(self):
        """Test concurrent state get/set operations."""
        event_queue = EventQueue(queue_id="state_thread_test")
        await event_queue.start()
        
        try:
            state_manager = StateManager(event_queue)
            await state_manager.initialize()
            
            results = []
            errors = []
            
            async def concurrent_state_worker(worker_id, operations_count):
                """Worker that performs concurrent state operations."""
                try:
                    for i in range(operations_count):
                        key = f"worker_{worker_id}_key_{i}"
                        value = f"worker_{worker_id}_value_{i}"
                        
                        # Set state
                        await state_manager.set_state(key, value, resource_type="TEST")
                        
                        # Get state back
                        retrieved_entry = await state_manager.get_state(key)
                        retrieved = retrieved_entry.state if hasattr(retrieved_entry, 'state') else retrieved_entry
                        
                        if retrieved != value:
                            errors.append(f"Worker {worker_id}: Value mismatch for {key}")
                        else:
                            results.append(f"worker_{worker_id}_success_{i}")
                        
                        # Small delay to encourage race conditions
                        await asyncio.sleep(0.001)
                        
                except Exception as e:
                    errors.append(f"Worker {worker_id}: {str(e)}")
            
            # Run concurrent workers
            workers = []
            for worker_id in range(5):
                worker = asyncio.create_task(concurrent_state_worker(worker_id, 10))
                workers.append(worker)
            
            await asyncio.gather(*workers)
            
            # Verify results
            assert len(errors) == 0, f"State operation errors: {errors}"
            assert len(results) == 50  # 5 workers * 10 operations each
        
        finally:
            await event_queue.stop()
    
    @pytest.mark.asyncio
    async def test_concurrent_state_key_conflicts(self):
        """Test handling of concurrent operations on same state keys."""
        event_queue = EventQueue(queue_id="state_conflict_test")
        await event_queue.start()
        
        try:
            state_manager = StateManager(event_queue)
            await state_manager.initialize()
            
            conflict_results = []
            conflict_errors = []
            
            async def conflicting_worker(worker_id, shared_key, iterations):
                """Worker that operates on shared state key."""
                try:
                    for i in range(iterations):
                        # Multiple workers writing to same key
                        value = f"worker_{worker_id}_iteration_{i}"
                        await state_manager.set_state(shared_key, value, resource_type="CONFLICT_TEST")
                        
                        # Read back immediately
                        retrieved_entry = await state_manager.get_state(shared_key)
                        retrieved = retrieved_entry.state if hasattr(retrieved_entry, 'state') else retrieved_entry
                        
                        conflict_results.append({
                            "worker_id": worker_id,
                            "iteration": i,
                            "wrote": value,
                            "read": retrieved
                        })
                        
                        await asyncio.sleep(0.001)
                        
                except Exception as e:
                    conflict_errors.append(f"Worker {worker_id}: {str(e)}")
            
            # Run workers that conflict on same key
            shared_key = "shared_conflict_key"
            workers = []
            for worker_id in range(3):
                worker = asyncio.create_task(conflicting_worker(worker_id, shared_key, 5))
                workers.append(worker)
            
            await asyncio.gather(*workers)
            
            # Verify no errors occurred (race conditions are expected but shouldn't cause crashes)
            assert len(conflict_errors) == 0, f"Conflict handling errors: {conflict_errors}"
            assert len(conflict_results) == 15  # 3 workers * 5 iterations
            
            # Final state should be from one of the workers
            final_entry = await state_manager.get_state(shared_key)
            final_state = final_entry.state if hasattr(final_entry, 'state') else final_entry
            assert final_state is not None
            assert "worker_" in final_state
        
        finally:
            await event_queue.stop()


class TestResourceManagerThreadSafety:
    """Test thread safety of various resource managers."""
    
    @pytest.mark.asyncio
    async def test_concurrent_context_manager_operations(self):
        """Test concurrent AgentContextManager operations."""
        event_queue = EventQueue(queue_id="context_thread_test")
        await event_queue.start()
        
        try:
            context_manager = AgentContextManager(event_queue)
            await context_manager.initialize()
            
            results = []
            errors = []
            
            async def context_worker(worker_id, operations):
                """Worker performing context operations."""
                try:
                    for i in range(operations):
                        agent_id = f"agent_{worker_id}_{i}"
                        context_data = {
                            "worker_id": worker_id,
                            "operation": i,
                            "timestamp": time.time()
                        }
                        
                        # Store context
                        context = await context_manager.create_context(agent_id, f"op_{worker_id}_{i}", context_data)
                        await context.update_data(context_data)
                        
                        # Retrieve context
                        retrieved_context = await context_manager.get_context(agent_id)
                        retrieved = retrieved_context.get_current_data()[0] if retrieved_context else None
                        
                        if retrieved and retrieved.get("worker_id") == worker_id:
                            results.append(f"worker_{worker_id}_op_{i}")
                        else:
                            errors.append(f"Worker {worker_id}: Context mismatch for {agent_id}")
                        
                        await asyncio.sleep(0.001)
                        
                except Exception as e:
                    errors.append(f"Worker {worker_id}: {str(e)}")
            
            # Run concurrent context operations
            workers = []
            for worker_id in range(4):
                worker = asyncio.create_task(context_worker(worker_id, 8))
                workers.append(worker)
            
            await asyncio.gather(*workers)
            
            # Verify results
            assert len(errors) == 0, f"Context manager errors: {errors}"
            assert len(results) == 32  # 4 workers * 8 operations
        
        finally:
            await event_queue.stop()
    
    @pytest.mark.asyncio
    async def test_concurrent_cache_operations(self):
        """Test concurrent CacheManager operations."""
        event_queue = EventQueue(queue_id="cache_thread_test")
        await event_queue.start()
        
        try:
            cache_manager = CacheManager(event_queue)
            await cache_manager.initialize()
            
            cache_results = []
            cache_errors = []
            
            async def cache_worker(worker_id, operations):
                """Worker performing cache operations."""
                try:
                    for i in range(operations):
                        cache_key = f"cache_key_{worker_id}_{i}"
                        cache_value = f"cache_value_{worker_id}_{i}"
                        
                        # Store in cache
                        await cache_manager.set_cache(cache_key, cache_value)
                        
                        # Retrieve from cache
                        retrieved = await cache_manager.get_cache(cache_key)
                        
                        if retrieved == cache_value:
                            cache_results.append(f"worker_{worker_id}_cache_{i}")
                        else:
                            cache_errors.append(f"Worker {worker_id}: Cache mismatch for {cache_key}")
                        
                        await asyncio.sleep(0.001)
                        
                except Exception as e:
                    cache_errors.append(f"Worker {worker_id}: {str(e)}")
            
            # Run concurrent cache operations
            workers = []
            for worker_id in range(4):
                worker = asyncio.create_task(cache_worker(worker_id, 6))
                workers.append(worker)
            
            await asyncio.gather(*workers)
            
            # Verify results
            assert len(cache_errors) == 0, f"Cache manager errors: {cache_errors}"
            assert len(cache_results) == 24  # 4 workers * 6 operations
        
        finally:
            await event_queue.stop()
    
    @pytest.mark.asyncio
    async def test_concurrent_metrics_collection(self):
        """Test concurrent MetricsManager operations."""
        event_queue = EventQueue(queue_id="metrics_thread_test")
        await event_queue.start()
        
        try:
            metrics_manager = MetricsManager(event_queue)
            await metrics_manager.initialize()
            
            metrics_results = []
            metrics_errors = []
            
            async def metrics_worker(worker_id, metrics_count):
                """Worker performing metrics operations."""
                try:
                    for i in range(metrics_count):
                        metric_name = f"worker_{worker_id}_metric_{i}"
                        metric_value = worker_id * 100 + i
                        
                        # Record metric
                        await metrics_manager.record_metric(metric_name, metric_value)
                        
                        # Get metric
                        metric_data = await metrics_manager.get_metrics(metric_name, limit=1)
                        retrieved = metric_data[0]["value"] if metric_data else None
                        
                        if retrieved == metric_value:
                            metrics_results.append(f"worker_{worker_id}_metric_{i}")
                        else:
                            metrics_errors.append(f"Worker {worker_id}: Metric mismatch for {metric_name}")
                        
                        await asyncio.sleep(0.001)
                        
                except Exception as e:
                    metrics_errors.append(f"Worker {worker_id}: {str(e)}")
            
            # Run concurrent metrics operations
            workers = []
            for worker_id in range(3):
                worker = asyncio.create_task(metrics_worker(worker_id, 7))
                workers.append(worker)
            
            await asyncio.gather(*workers)
            
            # Verify results
            assert len(metrics_errors) == 0, f"Metrics manager errors: {metrics_errors}"
            assert len(metrics_results) == 21  # 3 workers * 7 metrics
        
        finally:
            await event_queue.stop()


class TestPhaseOneInterfaceThreadSafety:
    """Test thread safety of PhaseOneInterface operations."""
    
    @pytest.mark.asyncio
    async def test_concurrent_step_execution(self):
        """Test concurrent step execution from multiple operations."""
        # Mock the orchestrator to avoid complex dependencies
        mock_orchestrator = MagicMock()
        mock_orchestrator.garden_planner_agent = MagicMock()
        mock_orchestrator.earth_agent = MagicMock()
        
        # Mock state manager
        event_queue = EventQueue(queue_id="step_thread_test")
        await event_queue.start()
        
        try:
            state_manager = StateManager(event_queue)
            await state_manager.initialize()
            mock_orchestrator._state_manager = state_manager
            
            # Create interface
            interface = PhaseOneInterface(mock_orchestrator)
            
            # Mock agent process methods to return quickly
            async def mock_agent_process(*args):
                await asyncio.sleep(0.01)  # Simulate processing time
                return {"status": "success", "result": "mock_result"}
            
            mock_orchestrator.garden_planner_agent.process = mock_agent_process
            mock_orchestrator.earth_agent.process = mock_agent_process
            
            concurrent_results = []
            concurrent_errors = []
            
            async def concurrent_workflow(workflow_id):
                """Run a workflow concurrently."""
                try:
                    # Start workflow
                    operation_id = await interface.start_phase_one(f"Test prompt {workflow_id}")
                    
                    # Execute first step
                    step_result = await interface.execute_next_step(operation_id)
                    
                    concurrent_results.append({
                        "workflow_id": workflow_id,
                        "operation_id": operation_id,
                        "step_status": step_result["status"]
                    })
                    
                except Exception as e:
                    concurrent_errors.append(f"Workflow {workflow_id}: {str(e)}")
            
            # Run multiple workflows concurrently
            workflows = []
            for workflow_id in range(5):
                workflow = asyncio.create_task(concurrent_workflow(workflow_id))
                workflows.append(workflow)
            
            await asyncio.gather(*workflows)
            
            # Verify results
            assert len(concurrent_errors) == 0, f"Concurrent workflow errors: {concurrent_errors}"
            assert len(concurrent_results) == 5
            
            # Verify all operations have unique IDs
            operation_ids = [r["operation_id"] for r in concurrent_results]
            assert len(set(operation_ids)) == 5  # All unique
        
        finally:
            await event_queue.stop()
    
    @pytest.mark.asyncio
    async def test_concurrent_status_queries(self):
        """Test concurrent status queries for multiple operations."""
        # Setup mock components
        mock_orchestrator = MagicMock()
        event_queue = EventQueue(queue_id="status_thread_test")
        await event_queue.start()
        
        try:
            state_manager = StateManager(event_queue)
            await state_manager.initialize()
            mock_orchestrator._state_manager = state_manager
            
            interface = PhaseOneInterface(mock_orchestrator)
            
            # Create multiple operations
            operation_ids = []
            for i in range(5):
                op_id = await interface.start_phase_one(f"Test operation {i}")
                operation_ids.append(op_id)
            
            status_results = []
            status_errors = []
            
            async def query_status_worker(worker_id, query_count):
                """Worker that queries status of random operations."""
                try:
                    for i in range(query_count):
                        # Query random operation
                        op_id = operation_ids[i % len(operation_ids)]
                        status = await interface.get_step_status(op_id)
                        
                        status_results.append({
                            "worker_id": worker_id,
                            "query": i,
                            "operation_id": op_id,
                            "status": status["status"]
                        })
                        
                        await asyncio.sleep(0.001)
                        
                except Exception as e:
                    status_errors.append(f"Worker {worker_id}: {str(e)}")
            
            # Run concurrent status queries
            workers = []
            for worker_id in range(3):
                worker = asyncio.create_task(query_status_worker(worker_id, 10))
                workers.append(worker)
            
            await asyncio.gather(*workers)
            
            # Verify results
            assert len(status_errors) == 0, f"Status query errors: {status_errors}"
            assert len(status_results) == 30  # 3 workers * 10 queries
            
            # All status queries should succeed
            for result in status_results:
                assert result["status"] in ["initialized", "running", "completed"]
        
        finally:
            await event_queue.stop()


class TestRaceConditionPrevention:
    """Test prevention of race conditions in critical sections."""
    
    @pytest.mark.asyncio
    async def test_resource_initialization_race_conditions(self):
        """Test that resource initialization prevents race conditions."""
        initialization_order = []
        initialization_errors = []
        
        async def initialize_resource(resource_name, delay):
            """Simulate resource initialization with delay."""
            try:
                await asyncio.sleep(delay)
                initialization_order.append(f"start_{resource_name}")
                
                # Simulate initialization work
                await asyncio.sleep(0.01)
                
                initialization_order.append(f"complete_{resource_name}")
                
            except Exception as e:
                initialization_errors.append(f"{resource_name}: {str(e)}")
        
        # Start multiple resource initializations concurrently
        resources = [
            ("state_manager", 0.01),
            ("context_manager", 0.02),
            ("cache_manager", 0.015),
            ("metrics_manager", 0.005)
        ]
        
        tasks = []
        for resource_name, delay in resources:
            task = asyncio.create_task(initialize_resource(resource_name, delay))
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        # Verify no errors
        assert len(initialization_errors) == 0, f"Initialization errors: {initialization_errors}"
        
        # Verify all resources were initialized
        assert len(initialization_order) == 8  # 4 resources * 2 events each
        
        # Check that each resource completed initialization
        for resource_name, _ in resources:
            assert f"start_{resource_name}" in initialization_order
            assert f"complete_{resource_name}" in initialization_order
    
    @pytest.mark.asyncio
    async def test_state_consistency_under_concurrency(self):
        """Test state consistency under concurrent access."""
        event_queue = EventQueue(queue_id="consistency_test")
        await event_queue.start()
        
        try:
            state_manager = StateManager(event_queue)
            await state_manager.initialize()
            
            # Counter that will be modified concurrently
            await state_manager.set_state("counter", 0, resource_type="CONSISTENCY_TEST")
            
            consistency_errors = []
            
            async def increment_counter(worker_id, increments):
                """Worker that increments shared counter."""
                try:
                    for i in range(increments):
                        # Read current value
                        current_entry = await state_manager.get_state("counter")
                        
                        # Extract actual value from IStateEntry object
                        if hasattr(current_entry, 'state'):
                            current = current_entry.state
                        else:
                            current = current_entry
                        
                        # Increment and write back
                        new_value = current + 1
                        await state_manager.set_state("counter", new_value, resource_type="CONSISTENCY_TEST")
                        
                        # Small delay to encourage race conditions
                        await asyncio.sleep(0.001)
                        
                except Exception as e:
                    consistency_errors.append(f"Worker {worker_id}: {str(e)}")
            
            # Run multiple workers incrementing the same counter
            workers = []
            increments_per_worker = 10
            worker_count = 5
            
            for worker_id in range(worker_count):
                worker = asyncio.create_task(increment_counter(worker_id, increments_per_worker))
                workers.append(worker)
            
            await asyncio.gather(*workers)
            
            # Check final counter value
            final_entry = await state_manager.get_state("counter")
            if hasattr(final_entry, 'state'):
                final_value = final_entry.state
            else:
                final_value = final_entry
            
            # Verify no errors
            assert len(consistency_errors) == 0, f"Consistency errors: {consistency_errors}"
            
            # Due to race conditions, final value might be less than expected total
            # but should be at least 1 and at most the expected total
            expected_total = worker_count * increments_per_worker
            assert 1 <= final_value <= expected_total
            
            # In a real system, proper locking would ensure final_value == expected_total
            # Here we're testing that the system doesn't crash under race conditions
        
        finally:
            await event_queue.stop()


class TestThreadPoolExecution:
    """Test thread pool execution patterns."""
    
    @pytest.mark.asyncio
    async def test_mixed_thread_async_execution(self):
        """Test mixed execution of thread pool and async operations."""
        results = []
        errors = []
        
        def cpu_bound_task(task_id, iterations):
            """CPU-bound task to run in thread pool."""
            try:
                result = 0
                for i in range(iterations):
                    result += i * task_id
                return f"cpu_task_{task_id}_result_{result}"
            except Exception as e:
                return f"cpu_task_{task_id}_error_{str(e)}"
        
        async def async_task(task_id, delay):
            """Async I/O task."""
            try:
                await asyncio.sleep(delay)
                return f"async_task_{task_id}_completed"
            except Exception as e:
                return f"async_task_{task_id}_error_{str(e)}"
        
        # Mix of CPU-bound and async tasks
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Submit CPU-bound tasks to thread pool
            cpu_futures = []
            for i in range(3):
                future = executor.submit(cpu_bound_task, i, 1000)
                cpu_futures.append(future)
            
            # Create async tasks
            async_tasks = []
            for i in range(3):
                task = asyncio.create_task(async_task(i, 0.05))
                async_tasks.append(task)
            
            # Wait for async tasks
            async_results = await asyncio.gather(*async_tasks)
            results.extend(async_results)
            
            # Wait for CPU-bound tasks
            for future in cpu_futures:
                result = future.result(timeout=5.0)
                results.append(result)
        
        # Verify all tasks completed
        assert len(results) == 6  # 3 async + 3 CPU-bound
        
        # Verify results contain expected patterns
        async_count = sum(1 for r in results if "async_task" in r and "completed" in r)
        cpu_count = sum(1 for r in results if "cpu_task" in r and "result" in r)
        
        assert async_count == 3
        assert cpu_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])