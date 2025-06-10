#!/usr/bin/env python3
"""
Simple test to reproduce the qasync loop detection issue.
"""

import asyncio
import sys
import logging
from PyQt6.QtWidgets import QApplication
import qasync

from resources.events.loop_management import EventLoopManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_loop_detection():
    """Test loop detection methods in qasync context."""
    print("=== Testing Loop Detection in qasync Context ===")
    
    # Test 1: asyncio.get_running_loop()
    try:
        current_loop = asyncio.get_running_loop()
        print(f"✅ asyncio.get_running_loop() works: {id(current_loop)}")
    except RuntimeError as e:
        print(f"❌ asyncio.get_running_loop() failed: {e}")
    
    # Test 2: EventLoopManager.get_primary_loop()
    primary_loop = EventLoopManager.get_primary_loop()
    print(f"EventLoopManager.get_primary_loop(): {id(primary_loop) if primary_loop else None}")
    
    # Test 3: asyncio.get_event_loop()
    try:
        thread_loop = asyncio.get_event_loop()
        print(f"asyncio.get_event_loop(): {id(thread_loop)}")
    except RuntimeError as e:
        print(f"asyncio.get_event_loop() failed: {e}")
    
    # Test 4: Compare loops
    if primary_loop:
        try:
            current_loop = asyncio.get_running_loop()
            if current_loop == primary_loop:
                print("✅ Loops match - detection working correctly")
            else:
                print("❌ Loop mismatch detected")
        except RuntimeError:
            print("❌ Cannot get running loop for comparison")


def main():
    """Main function."""
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create qasync loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    print(f"Created qasync loop: {id(loop)}")
    
    # Register with EventLoopManager
    result = EventLoopManager.set_primary_loop(loop)
    print(f"Registered with EventLoopManager: {result}")
    
    # Run the test
    with loop:
        try:
            loop.run_until_complete(test_loop_detection())
        except Exception as e:
            print(f"Test failed: {e}")


if __name__ == "__main__":
    main()