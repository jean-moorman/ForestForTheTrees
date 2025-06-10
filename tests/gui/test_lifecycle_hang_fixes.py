#!/usr/bin/env python3
"""
Test to isolate where the lifecycle setup hangs.
"""

import asyncio
import sys
import logging
import signal
from PyQt6.QtWidgets import QApplication
import qasync

# Setup detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

# Import the components
from resources.events.loop_management import EventLoopManager
from phase_one.runners.gui.app import PhaseOneApp


async def test_lifecycle_setup():
    """Test lifecycle setup step by step."""
    logger.info("=== Starting lifecycle setup test ===")
    
    try:
        # Create PhaseOneApp
        logger.info("Creating PhaseOneApp...")
        app = PhaseOneApp()
        logger.info("✅ PhaseOneApp created successfully")
        
        # Run setup_async
        logger.info("Running setup_async...")
        await app.setup_async()
        logger.info("✅ setup_async completed successfully")
        
        logger.info("=== Lifecycle setup test completed successfully ===")
        return True
        
    except Exception as e:
        logger.error(f"❌ Lifecycle setup failed: {e}", exc_info=True)
        return False


def main():
    """Main function that sets up qasync and tests lifecycle."""
    # Set up signal handler for clean exit
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, exiting...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Create the Qt application
        app = QApplication.instance() or QApplication(sys.argv)
        logger.info("QApplication created")
        
        # Create qasync loop
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        logger.info(f"Created qasync event loop: {id(loop)}")
        
        # Register with EventLoopManager
        result = EventLoopManager.set_primary_loop(loop)
        logger.info(f"Registered main event loop with EventLoopManager: {result}")
        
        # Run the test
        logger.info("Starting lifecycle test...")
        
        with loop:
            try:
                test_result = loop.run_until_complete(test_lifecycle_setup())
                if test_result:
                    logger.info("🎉 Lifecycle test passed!")
                    return 0
                else:
                    logger.error("💥 Lifecycle test failed!")
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