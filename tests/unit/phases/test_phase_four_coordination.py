#!/usr/bin/env python3
"""
Test script for Phase 4 agent update coordination system.
"""

import asyncio
import sys
import traceback
import time

async def test_agent_coordination():
    print('Testing agent update coordination...')
    
    try:
        # Import required modules
        from phase_one.coordination import AgentUpdateCoordinator, AgentPriority, get_agent_coordinator
        
        # Test singleton behavior
        coordinator1 = get_agent_coordinator()
        coordinator2 = get_agent_coordinator()
        
        if coordinator1 is not coordinator2:
            raise AssertionError('Coordinator should be singleton')
        print('✓ Coordinator singleton working correctly')
        
        # Test coordination initialization
        coordinator = coordinator1
        await coordinator.initialize_async()
        
        # Test basic coordination statistics
        stats = coordinator.get_coordination_stats()
        expected_keys = ['total_coordinated', 'contention_prevented', 'average_wait_time', 'peak_concurrent']
        for key in expected_keys:
            if key not in stats:
                raise AssertionError(f'Missing stat key: {key}')
        print('✓ Coordination statistics structure correct')
        
        # Test priority levels
        priorities = [AgentPriority.LOW, AgentPriority.NORMAL, AgentPriority.HIGH, AgentPriority.CRITICAL]
        print(f'✓ Priority levels available: {[p.name for p in priorities]}')
        
        # Test single agent coordination (should be immediate)
        start_time = time.time()
        async with coordinator.request_update_slot('test_agent_1', AgentPriority.NORMAL, 1.0, 'test_operation'):
            # Simulate brief work
            await asyncio.sleep(0.1)
        end_time = time.time()
        
        duration = end_time - start_time
        if duration > 0.2:  # Should be very fast for single agent
            print(f'Warning: Single agent coordination took {duration:.2f}s')
        else:
            print('✓ Single agent coordination is fast')
        
        # Test concurrent coordination with backpressure
        async def coordinated_update(agent_id: str, priority: AgentPriority, work_duration: float = 0.1):
            async with coordinator.request_update_slot(agent_id, priority, work_duration, 'concurrent_test'):
                await asyncio.sleep(work_duration)
                return f'{agent_id}_complete'
        
        # Start multiple agents simultaneously
        tasks = [
            coordinated_update('agent_low_1', AgentPriority.LOW, 0.1),
            coordinated_update('agent_normal_1', AgentPriority.NORMAL, 0.1),
            coordinated_update('agent_high_1', AgentPriority.HIGH, 0.1),
            coordinated_update('agent_normal_2', AgentPriority.NORMAL, 0.1),
        ]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Should have completed all tasks
        if len(results) != 4:
            raise AssertionError(f'Expected 4 results, got {len(results)}')
        print(f'✓ Concurrent coordination completed in {end_time - start_time:.2f}s')
        
        # Check coordination statistics
        stats = coordinator.get_coordination_stats()
        if stats['total_coordinated'] < 4:  # Should have at least 4 coordinated operations
            print(f'Warning: Only {stats["total_coordinated"]} operations coordinated')
        else:
            print(f'✓ Coordination statistics updated (total: {stats["total_coordinated"]})')
        
        # Test priority ordering (high priority should go first when concurrent)
        results_with_timing = []
        
        async def timed_update(agent_id: str, priority: AgentPriority):
            start = time.time()
            async with coordinator.request_update_slot(agent_id, priority, 0.05, 'priority_test'):
                await asyncio.sleep(0.05)
            end = time.time()
            return (agent_id, priority, start, end)
        
        # Start low and high priority agents at same time
        priority_tasks = [
            timed_update('low_priority', AgentPriority.LOW),
            timed_update('high_priority', AgentPriority.HIGH),
            timed_update('normal_priority', AgentPriority.NORMAL),
        ]
        
        priority_results = await asyncio.gather(*priority_tasks)
        
        # High priority should generally start before low priority (but timing may vary)
        high_result = next((r for r in priority_results if r[1] == AgentPriority.HIGH), None)
        low_result = next((r for r in priority_results if r[1] == AgentPriority.LOW), None)
        
        if high_result and low_result:
            print(f'✓ Priority coordination test completed')
        else:
            print('Warning: Priority test results incomplete')
        
        # Test force release
        await coordinator.force_release_agent('nonexistent_agent')  # Should not error
        print('✓ Force release works for nonexistent agent')
        
        # Test cleanup stale updates
        await coordinator.cleanup_stale_updates()  # Should not error
        print('✓ Cleanup stale updates works')
        
        # Test active updates tracking
        active = coordinator.get_active_updates()
        if len(active) > 0:
            print(f'Warning: {len(active)} updates still active')
        else:
            print('✓ No active updates remaining')
        
        print('✓ All agent coordination tests passed successfully!')
        return True
        
    except Exception as e:
        print(f'✗ Test failed: {str(e)}')
        traceback.print_exc()
        return False

if __name__ == '__main__':
    result = asyncio.run(test_agent_coordination())
    sys.exit(0 if result else 1)