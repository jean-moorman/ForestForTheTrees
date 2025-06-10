#!/usr/bin/env python3
"""
Test the fixed qasync_wait_for implementation with timeouts.
"""

import asyncio
import sys
import logging
import time
from PyQt6.QtWidgets import QApplication
import qasync

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

# Import our fix
from resources.events.loop_management import EventLoopManager
from resources.events.qasync_utils import get_qasync_compatible_loop, qasync_wait_for


async def test_qasync_wait_for_scenarios():
    """Test various qasync_wait_for scenarios including timeouts."""
    logger.info("=== Testing qasync_wait_for scenarios ===")
    
    # Test 1: Normal operation without timeout
    logger.info("Test 1: Normal operation without timeout")
    try:
        async def quick_operation():
            await asyncio.sleep(0.1)
            return "quick_result"
        
        result = await qasync_wait_for(quick_operation(), timeout=None)
        logger.info(f"✅ Test 1 passed: {result}")
    except Exception as e:
        logger.error(f"❌ Test 1 failed: {e}")
        return False
    
    # Test 2: Normal operation with timeout (no timeout triggered)
    logger.info("Test 2: Normal operation with timeout (no timeout triggered)")
    try:
        async def quick_operation():
            await asyncio.sleep(0.1)
            return "quick_with_timeout"
        
        result = await qasync_wait_for(quick_operation(), timeout=5.0)
        logger.info(f"✅ Test 2 passed: {result}")
    except Exception as e:
        logger.error(f"❌ Test 2 failed: {e}")
        return False
    
    # Test 3: Timeout scenario (THIS IS THE CRITICAL TEST)
    logger.info("Test 3: Timeout scenario - testing the fix")
    try:
        async def slow_operation():
            await asyncio.sleep(2.0)  # This will timeout
            return "should_not_reach_here"
        
        # This should raise TimeoutError after 0.5 seconds
        start_time = time.time()
        await qasync_wait_for(slow_operation(), timeout=0.5)
        logger.error("❌ Test 3 failed: Should have timed out")
        return False
    except asyncio.TimeoutError as e:
        elapsed = time.time() - start_time
        logger.info(f"✅ Test 3 passed: Correctly timed out after {elapsed:.2f}s - {e}")
    except Exception as e:
        logger.error(f"❌ Test 3 failed with wrong exception: {e}")
        return False
    
    # Test 4: Exception handling in task
    logger.info("Test 4: Exception handling in task")
    try:
        async def failing_operation():
            await asyncio.sleep(0.1)
            raise ValueError("Test exception")
        
        await qasync_wait_for(failing_operation(), timeout=5.0)
        logger.error("❌ Test 4 failed: Should have raised ValueError")
        return False
    except ValueError as e:
        logger.info(f"✅ Test 4 passed: Correctly caught exception - {e}")
    except Exception as e:
        logger.error(f"❌ Test 4 failed with wrong exception: {e}")
        return False
    
    # Test 5: Task cancellation
    logger.info("Test 5: Task cancellation during timeout")
    try:
        task_was_cancelled = False
        
        async def cancellable_operation():
            nonlocal task_was_cancelled
            try:
                await asyncio.sleep(2.0)
                return "should_not_complete"
            except asyncio.CancelledError:
                task_was_cancelled = True
                raise
        
        try:
            await qasync_wait_for(cancellable_operation(), timeout=0.3)
        except asyncio.TimeoutError:
            pass  # Expected
        
        # Give a moment for cancellation to propagate
        await asyncio.sleep(0.1)
        
        if task_was_cancelled:
            logger.info("✅ Test 5 passed: Task was properly cancelled on timeout")
        else:
            logger.error("❌ Test 5 failed: Task was not cancelled")
            return False
    except Exception as e:
        logger.error(f"❌ Test 5 failed: {e}")
        return False
    
    # Test 6: qasync event loop context preservation
    logger.info("Test 6: Event loop context preservation")
    try:
        loop_before = get_qasync_compatible_loop()
        
        async def loop_checking_operation():
            current_loop = get_qasync_compatible_loop()
            if id(current_loop) != id(loop_before):
                raise RuntimeError(f"Loop context changed: {id(loop_before)} -> {id(current_loop)}")
            return "loop_context_preserved"
        
        result = await qasync_wait_for(loop_checking_operation(), timeout=5.0)
        logger.info(f"✅ Test 6 passed: {result}")
    except Exception as e:
        logger.error(f"❌ Test 6 failed: {e}")
        return False
    
    logger.info("🎉 All qasync_wait_for tests passed!")
    return True


def main():
    """Main function that sets up qasync environment and runs tests."""
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create qasync loop (same as run_phase_one.py)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    logger.info(f"Created qasync event loop: {id(loop)}")
    
    # Register with EventLoopManager (same as run_phase_one.py)
    result = EventLoopManager.set_primary_loop(loop)
    logger.info(f"Registered main event loop with EventLoopManager: {result}")
    
    # Run the tests
    with loop:
        try:
            test_result = loop.run_until_complete(
                asyncio.wait_for(test_qasync_wait_for_scenarios(), timeout=30.0)
            )
            if test_result:
                logger.info("🎉 All tests passed! The qasync_wait_for fix is working correctly.")
                return 0
            else:
                logger.error("💥 Tests failed! The qasync_wait_for fix needs more work.")
                return 1
        except Exception as e:
            logger.error(f"💥 Test execution failed: {e}")
            return 1


if __name__ == "__main__":
    sys.exit(main())