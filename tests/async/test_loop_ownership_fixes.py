#!/usr/bin/env python3
"""
Test script to verify our loop ownership violation fixes
"""

import sys, os
sys.path.append('/home/atlas/FFTT_dir/FFTT')
from resources.events.loop_management import EventLoopManager
import threading
import asyncio
import qasync
from PyQt6.QtWidgets import QApplication

def main():
    # Test 1: Main thread loop registration
    print('=== Test 1: Main thread loop registration ===')
    app = QApplication([])
    qasync_loop = qasync.QEventLoop(app)
    result = EventLoopManager.set_primary_loop(qasync_loop)
    print(f'Main loop registration: {result}')
    print(f'Main loop ID: {id(qasync_loop)}')

    # Test 2: Background thread loop registration
    print('\n=== Test 2: Background thread loop registration ===')
    
    def test_background():
        bg_loop = asyncio.new_event_loop()
        result = EventLoopManager.set_background_loop(bg_loop)
        print(f'Background loop registration: {result}')
        print(f'Background loop ID: {id(bg_loop)}')
        
        # Test for ownership violation
        violation_result = EventLoopManager.set_background_loop(qasync_loop)
        print(f'Ownership violation test (should be False): {violation_result}')

    bg_thread = threading.Thread(target=test_background)
    bg_thread.start()
    bg_thread.join()

    print('\n=== Test Results ===')
    main_loop = EventLoopManager.get_primary_loop()
    bg_loop = EventLoopManager.get_background_loop()
    print(f'Retrieved main loop: {id(main_loop) if main_loop else None}')
    print(f'Retrieved background loop: {id(bg_loop) if bg_loop else None}')
    
    different = main_loop != bg_loop if main_loop and bg_loop else 'N/A'
    print(f'Loops are different: {different}')
    
    # Test 3: ThreadLocalEventLoopStorage fix
    print('\n=== Test 3: ThreadLocalEventLoopStorage behavior ===')
    from resources.events.loop_management import ThreadLocalEventLoopStorage
    storage = ThreadLocalEventLoopStorage.get_instance()
    
    # Main thread should register as main loop
    main_result = storage.set_loop(qasync_loop)
    print(f'ThreadLocalEventLoopStorage main thread registration: {main_result}')
    
    def test_thread_storage():
        thread_loop = asyncio.new_event_loop()
        thread_result = storage.set_loop(thread_loop)
        print(f'ThreadLocalEventLoopStorage background thread registration: {thread_result}')
    
    thread_test = threading.Thread(target=test_thread_storage)
    thread_test.start()
    thread_test.join()
    
    print('\n=== All Tests Complete ===')

if __name__ == '__main__':
    main()