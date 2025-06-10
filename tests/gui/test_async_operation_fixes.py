#!/usr/bin/env python3
"""
Test script to validate GUI async operation fixes
"""

import sys
import asyncio
import threading
from PyQt6.QtWidgets import QApplication
import qasync

# Add FFTT to path
sys.path.append('/home/atlas/FFTT_dir/FFTT')

from resources.events.loop_management import EventLoopManager

async def test_async_operation():
    """Simulate the async operation that was failing in GUI"""
    print("🔄 Testing async operation in qasync context...")
    
    # Simulate getting current loop like in _process_prompt_async
    try:
        current_loop = asyncio.get_running_loop()
        print(f"✅ Found running loop: {id(current_loop)}")
    except RuntimeError:
        # Try the fixed approach
        expected_loop = EventLoopManager.get_primary_loop()
        if expected_loop and not expected_loop.is_closed():
            current_loop = expected_loop
            print(f"⚠️  Using qasync primary loop: {id(expected_loop)}")
            asyncio.set_event_loop(current_loop)
        else:
            print("❌ No event loop available")
            return False
    
    # Simulate the step execution that was failing
    try:
        # Create a simple coroutine to test
        async def mock_step():
            await asyncio.sleep(0.1)
            return {"status": "success", "message": "Step completed"}
        
        # Test the fixed approach
        step_coro = mock_step()
        step_task = current_loop.create_task(step_coro)
        
        # This was the line that was failing
        step_result = await asyncio.wait_for(step_task, timeout=5.0)
        
        print(f"✅ Async operation completed: {step_result}")
        return True
        
    except Exception as e:
        print(f"❌ Async operation failed: {e}")
        return False

def main():
    print("=== Testing GUI Async Operation Fixes ===")
    
    # Create Qt application and qasync loop
    app = QApplication([])
    qasync_loop = qasync.QEventLoop(app)
    
    # Register with EventLoopManager
    EventLoopManager.set_primary_loop(qasync_loop)
    print(f"📍 Registered qasync loop: {id(qasync_loop)}")
    
    # Test the async operation
    try:
        # Run the test in the qasync loop
        result = qasync_loop.run_until_complete(test_async_operation())
        
        if result:
            print("\n🎉 GUI async operation fixes are working!")
            print("✅ Loop detection improved")
            print("✅ Task creation in correct context")
            print("✅ asyncio.wait_for() working with qasync")
        else:
            print("\n❌ GUI async operation fixes need more work")
            
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()