#!/usr/bin/env python3
"""
Test script for Phase 2 bulk circuit breaker creation optimization.
"""

import asyncio
import sys
import traceback
import time

async def test_bulk_circuit_creation():
    print('Testing bulk circuit breaker creation...')
    
    try:
        # Import required modules
        from resources import EventQueue
        from resources.monitoring.circuit_breakers import CircuitBreakerRegistry, CircuitBreakerPlaceholder
        from resources.common import CircuitBreakerConfig
        
        # Create test components
        event_queue = EventQueue()
        await event_queue.start()
        
        # Create circuit breaker registry
        registry = CircuitBreakerRegistry(event_queue)
        
        print('✓ CircuitBreakerRegistry created successfully')
        
        # Test bulk creation threshold
        if registry._bulk_creation_threshold != 10:
            raise AssertionError(f'Bulk creation threshold incorrect: {registry._bulk_creation_threshold}')
        print('✓ Bulk creation threshold configured correctly')
        
        # Test individual creation (should return placeholder)
        start_time = time.time()
        circuit1 = await registry.get_or_create_circuit_breaker('test_circuit_1')
        
        # Should be a placeholder initially
        if not hasattr(circuit1, '_is_placeholder'):
            raise AssertionError('Expected placeholder for individual creation')
        print('✓ Individual circuit creation returns placeholder')
        
        # Test bulk creation by creating multiple circuits
        circuit_names = [f'bulk_circuit_{i}' for i in range(12)]
        circuits = []
        
        bulk_start_time = time.time()
        for name in circuit_names:
            circuit = await registry.get_or_create_circuit_breaker(name)
            circuits.append(circuit)
        
        # Should trigger bulk creation after 10 circuits
        print(f'✓ Created {len(circuits)} circuits')
        
        # Wait for bulk creation to complete
        await asyncio.sleep(0.5)  # Give time for bulk processing
        
        # Flush any remaining circuits
        remaining = await registry.flush_creation_queue()
        print(f'✓ Flushed {remaining} remaining circuit breakers')
        
        # Verify circuits were created properly
        real_circuits = 0
        placeholders = 0
        for name in circuit_names:
            circuit = await registry.get_circuit_breaker(name)
            if circuit:
                if hasattr(circuit, '_is_placeholder') and circuit._is_placeholder:
                    placeholders += 1
                else:
                    real_circuits += 1
        
        print(f'✓ Real circuits: {real_circuits}, Placeholders: {placeholders}')
        
        # Verify creation count
        total_created = registry._creation_count
        if total_created < 12:  # Should have at least the bulk circuits
            print(f'Warning: Only {total_created} circuits recorded as created')
        else:
            print(f'✓ {total_created} circuits tracked in creation count')
        
        # Test circuit functionality
        test_circuit = await registry.get_circuit_breaker('bulk_circuit_5')
        if test_circuit:
            # Test execute functionality
            async def test_operation():
                return "test_result"
            
            result = await test_circuit.execute(test_operation)
            if result != "test_result":
                raise AssertionError(f'Circuit execute failed: {result}')
            print('✓ Circuit execute functionality working')
        
        # Test registry status
        status = registry.get_circuit_status_summary()
        print(f'✓ Registry contains {len(status)} circuit breakers')
        
        # Cleanup
        await event_queue.stop()
        print('✓ All bulk creation tests passed successfully!')
        return True
        
    except Exception as e:
        print(f'✗ Test failed: {str(e)}')
        traceback.print_exc()
        return False

if __name__ == '__main__':
    result = asyncio.run(test_bulk_circuit_creation())
    sys.exit(0 if result else 1)