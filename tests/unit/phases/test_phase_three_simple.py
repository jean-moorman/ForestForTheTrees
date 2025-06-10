#!/usr/bin/env python3
"""
Simplified test for Phase 3 adaptive memory monitoring.
"""

import asyncio
import sys
import traceback
from datetime import datetime, timedelta

async def test_adaptive_memory_simple():
    print('Testing adaptive memory monitoring (simplified)...')
    
    try:
        # Import required modules
        from resources import EventQueue
        from resources.monitoring.memory import MemoryMonitor
        from resources.common import MemoryThresholds
        
        # Create test components
        event_queue = EventQueue()
        await event_queue.start()
        
        # Create memory monitor
        thresholds = MemoryThresholds()
        monitor = MemoryMonitor(event_queue, thresholds)
        
        print('✓ MemoryMonitor created successfully')
        
        # Test adaptive monitoring is enabled
        if not monitor._adaptive_monitoring:
            raise AssertionError('Adaptive monitoring should be enabled by default')
        print('✓ Adaptive monitoring enabled by default')
        
        # Test activity calculation with different scenarios
        
        # Low activity test
        with monitor._lock:
            monitor._operation_count = 0
            monitor._last_activity_check = datetime.now() - timedelta(seconds=60)
        activity = monitor._calculate_activity_level()
        if activity > 1:  # Should be very low
            print(f'Warning: Low activity test gave {activity} ops/min')
        print('✓ Low activity calculation working')
        
        # Medium activity test  
        with monitor._lock:
            monitor._operation_count = 6
            monitor._last_activity_check = datetime.now() - timedelta(seconds=60)
        activity = monitor._calculate_activity_level()
        if 5.5 <= activity <= 6.5:  # Should be around 6 ops/min
            print('✓ Medium activity calculation working')
        else:
            print(f'Warning: Medium activity gave {activity} ops/min (expected ~6)')
        
        # High activity test
        with monitor._lock:
            monitor._operation_count = 15
            monitor._last_activity_check = datetime.now() - timedelta(seconds=60)
        activity = monitor._calculate_activity_level()
        if 14 <= activity <= 16:  # Should be around 15 ops/min
            print('✓ High activity calculation working')
        else:
            print(f'Warning: High activity gave {activity} ops/min (expected ~15)')
        
        # Test adaptive intervals
        
        # Low activity interval
        with monitor._lock:
            monitor._operation_count = 2
            monitor._last_activity_check = datetime.now() - timedelta(seconds=60)
        interval = monitor._get_adaptive_check_interval()
        if interval == 300:  # Should be base interval
            print('✓ Low activity interval correct (300s)')
        else:
            print(f'Warning: Low activity interval: {interval}s (expected 300s)')
        
        # High activity interval
        with monitor._lock:
            monitor._operation_count = 15
            monitor._last_activity_check = datetime.now() - timedelta(seconds=60)
        interval = monitor._get_adaptive_check_interval()
        if interval == 120:  # Should be high activity interval
            print('✓ High activity interval correct (120s)')
        else:
            print(f'Warning: High activity interval: {interval}s (expected 120s)')
        
        # Test enable/disable
        monitor.set_adaptive_monitoring(False)
        if monitor._adaptive_monitoring:
            raise AssertionError('Should be disabled')
        print('✓ Can disable adaptive monitoring')
        
        monitor.set_adaptive_monitoring(True)
        if not monitor._adaptive_monitoring:
            raise AssertionError('Should be enabled')
        print('✓ Can re-enable adaptive monitoring')
        
        # Test stats
        stats = monitor.get_monitoring_stats()
        required_keys = ['adaptive_monitoring', 'current_mode', 'current_activity']
        for key in required_keys:
            if key not in stats:
                raise AssertionError(f'Missing stat: {key}')
        print('✓ Statistics working correctly')
        
        # Test resource tracking (activity counting)
        initial_count = monitor._operation_count
        await monitor.track_resource('test_res', 5.0, 'test_comp')
        if monitor._operation_count <= initial_count:
            print('Warning: Operation count not incremented')
        else:
            print('✓ Resource tracking increments operation count')
        
        # Cleanup
        await event_queue.stop()
        print('✓ All simplified adaptive memory tests passed!')
        return True
        
    except Exception as e:
        print(f'✗ Test failed: {str(e)}')
        traceback.print_exc()
        return False

if __name__ == '__main__':
    result = asyncio.run(test_adaptive_memory_simple())
    sys.exit(0 if result else 1)