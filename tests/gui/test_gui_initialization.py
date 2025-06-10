#!/usr/bin/env python3
"""
Test GUI initialization step by step to find exact hanging point.
"""

import asyncio
import sys
import logging
import signal
import time
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer
import qasync

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

# Import components 
from resources.events.loop_management import EventLoopManager
from phase_one.runners.gui.app import PhaseOneApp


async def test_gui_initialization():
    """Test each step of GUI initialization."""
    logger.info("=== Testing GUI initialization step by step ===")
    
    try:
        logger.info("Step 1: Creating PhaseOneApp...")
        app = PhaseOneApp()
        logger.info("✅ Step 1 completed: PhaseOneApp created")
        
        logger.info("Step 2: Running setup_async...")
        await app.setup_async() 
        logger.info("✅ Step 2 completed: setup_async done")
        
        logger.info("Step 3: Checking if main_window exists...")
        if hasattr(app, 'main_window') and app.main_window:
            logger.info("✅ Step 3 completed: main_window exists")
            
            logger.info("Step 4: Showing main window...")
            app.main_window.show()
            logger.info("✅ Step 4 completed: main_window shown")
        else:
            logger.warning("⚠️ Step 3: main_window not found")
        
        logger.info("=== GUI initialization test completed successfully ===")
        return True
        
    except Exception as e:
        logger.error(f"❌ GUI initialization failed: {e}", exc_info=True)
        return False


class TestMainWindow(QMainWindow):
    """Simple test window for timeout."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GUI Initialization Test")
        self.setGeometry(100, 100, 400, 200)
        
        # Create simple UI
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        label = QPushButton("Test completed - close window")
        label.clicked.connect(self.close)
        layout.addWidget(label)
        
        # Auto-close timer 
        self.close_timer = QTimer()
        self.close_timer.timeout.connect(self.close)
        self.close_timer.setSingleShot(True)
        self.close_timer.start(3000)  # Close after 3 seconds


def main():
    """Main function."""
    # Set up signal handler for clean exit
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, exiting...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Create Qt application
        app = QApplication.instance() or QApplication(sys.argv)
        logger.info("QApplication created")
        
        # Create qasync loop
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        logger.info(f"Created qasync event loop: {id(loop)}")
        
        # Register with EventLoopManager
        result = EventLoopManager.set_primary_loop(loop)
        logger.info(f"Registered main event loop with EventLoopManager: {result}")
        
        # Start the test with a timeout mechanism
        logger.info("Starting GUI initialization test...")
        
        start_time = time.time()
        test_completed = False
        test_result = False
        
        async def run_test_with_timeout():
            nonlocal test_completed, test_result
            try:
                test_result = await asyncio.wait_for(test_gui_initialization(), timeout=10.0)
                test_completed = True
                logger.info("Test completed within timeout")
            except asyncio.TimeoutError:
                logger.error("❌ Test timed out after 10 seconds - GUI initialization is hanging")
                test_completed = True
                test_result = False
            except Exception as e:
                logger.error(f"❌ Test failed with exception: {e}")
                test_completed = True
                test_result = False
        
        with loop:
            try:
                # Show a simple window to indicate test is running
                test_window = TestMainWindow()
                test_window.show()
                
                # Run the test directly in the event loop
                test_result = loop.run_until_complete(
                    asyncio.wait_for(test_gui_initialization(), timeout=10.0)
                )
                
                test_window.close()
                
                if test_result:
                    logger.info("🎉 GUI initialization test passed!")
                    return 0
                else:
                    logger.error("💥 GUI initialization test failed!")
                    return 1
                    
            except Exception as e:
                logger.error(f"💥 Test execution failed: {e}", exc_info=True)
                return 1
        
    except Exception as e:
        logger.error(f"Setup error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    logger.info(f"Test completed with exit code: {exit_code}")
    sys.exit(exit_code)