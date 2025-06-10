#!/usr/bin/env python3
"""
Test to isolate the specific GUI hanging issue.
"""

import asyncio
import sys
import logging
import signal
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer
import qasync

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

# Import our fixes
from resources.events.loop_management import EventLoopManager


class SimpleTestWindow(QMainWindow):
    """Simple test window to isolate the hanging issue."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Test Window")
        self.setGeometry(100, 100, 300, 100)
        
        # Create UI
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        self.button = QPushButton("Test Button")
        self.button.clicked.connect(self.on_button_click)
        layout.addWidget(self.button)
        
        # Auto-close timer to prevent hanging
        self.close_timer = QTimer()
        self.close_timer.timeout.connect(self.close_with_result)
        self.close_timer.setSingleShot(True)
        self.close_timer.start(5000)  # Close after 5 seconds
        
        logger.info("SimpleTestWindow initialized")
    
    def on_button_click(self):
        """Handle button click."""
        logger.info("Button clicked - test passed!")
        self.close_with_result()
    
    def close_with_result(self):
        """Close window with success result."""
        logger.info("Window closing normally")
        self.close()


def main():
    """Main function that mimics run_phase_one.py setup."""
    try:
        # Create the Qt application
        app = QApplication.instance() or QApplication(sys.argv)
        logger.info("QApplication created")
        
        # Create qasync loop (same as run_phase_one.py)
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        logger.info(f"Created qasync event loop: {id(loop)}")
        
        # Register with EventLoopManager (same as run_phase_one.py)
        result = EventLoopManager.set_primary_loop(loop)
        logger.info(f"Registered main event loop with EventLoopManager: {result}")
        
        # Create and show window
        window = SimpleTestWindow()
        window.show()
        logger.info("Window shown")
        
        # Set up signal handler for clean exit
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, closing...")
            app.quit()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Run the event loop
        logger.info("Starting application event loop...")
        
        with loop:
            try:
                exit_code = app.exec()
                logger.info(f"Application exited with code: {exit_code}")
                return exit_code
            except Exception as e:
                logger.error(f"Application error: {e}")
                return 1
        
    except Exception as e:
        logger.error(f"Setup error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    logger.info(f"Test completed with exit code: {exit_code}")
    sys.exit(exit_code)