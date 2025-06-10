"""
Phase One Qt Application

Main Qt application class for Phase One, handling application setup, signal handling,
exception management, and coordinating the GUI components.
"""

import logging
import signal
import sys
import threading
import traceback

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer

from resources.events import EventQueue
from .event_management import EventManager
from .lifecycle import LifecycleManager

logger = logging.getLogger(__name__)


class PhaseOneApp:
    """Application for running Phase One functionality."""
    
    def __init__(self):
        # Get existing QApplication or create one
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)
            
        # Initialize event management
        self.event_manager = EventManager(self)
        self.event_manager.setup_event_loop()
        
        # Initialize the event queue with proper event loop
        self.event_queue = EventQueue(queue_id="phase_one_queue")
        
        # Store the event loop ID that created the queue for diagnostics
        logger.info(f"EventQueue created on thread {self.event_queue._creation_thread_id}")
        
        # Initialize lifecycle management
        self.lifecycle_manager = LifecycleManager(self)
        
        # Track initialization state
        self._initialized = False
        
    async def setup_async(self):
        """Initialize components that require the event loop."""
        await self.lifecycle_manager.setup_async()
        self._initialized = True
        
    def run(self):
        """Run the application main loop."""
        try:
            # Show the main window
            if hasattr(self, 'main_window') and not self.main_window.isVisible():
                self.main_window.show()
                
            # Setup signal handlers
            self._setup_signal_handlers()
            
            # Set up exception hook
            sys.excepthook = self._global_exception_handler
            
            # Run the Qt event loop
            logger.info("Starting application main loop")
            self.app._is_running = True
            try:
                return self.app.exec()
            finally:
                self.app._is_running = False
        except Exception as e:
            logger.error(f"Runtime error: {e}", exc_info=True)
            self._handle_fatal_error("Runtime error", e)
            return 1
    
    def _setup_signal_handlers(self):
        """Set up signal handlers for clean shutdown."""
        if hasattr(signal, 'SIGINT') and sys.platform != 'win32':
            try:
                loop = self.event_manager.loop
                for signame in ('SIGINT', 'SIGTERM'):
                    if hasattr(signal, signame):
                        try:
                            loop.add_signal_handler(
                                getattr(signal, signame),
                                lambda signame=signame: self._handle_signal(signame)
                            )
                            logger.debug(f"Added signal handler for {signame}")
                        except NotImplementedError:
                            # Fallback to traditional signal handler
                            signal.signal(
                                getattr(signal, signame),
                                lambda signum, frame, signame=signame: self._handle_signal(signame)
                            )
                            logger.debug(f"Added fallback signal handler for {signame}")
            except Exception as e:
                logger.warning(f"Could not set up signal handlers: {e}")
                        
    def _handle_signal(self, signame):
        """Handle a signal in the main thread safely."""
        logger.info(f"Received signal {signame}, initiating shutdown")
        # Schedule the app to quit safely from the main thread
        QTimer.singleShot(0, self.app.quit)
        
    def _global_exception_handler(self, exc_type, exc_value, exc_traceback):
        """Global exception handler for unhandled exceptions."""
        # Skip for KeyboardInterrupt
        if issubclass(exc_type, KeyboardInterrupt):
            logger.info("Keyboard interrupt received")
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        # Log the exception
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.critical(f"Unhandled exception: {error_msg}")
        
        # Show error dialog
        self._show_error_dialog("Unhandled Exception", error_msg)
        
    def _show_error_dialog(self, title, message):
        """Show an error dialog safely from the main thread."""
        if hasattr(self, 'main_window') and self.main_window is not None:
            QMessageBox.critical(self.main_window, title, message)
        else:
            QMessageBox.critical(None, title, message)
            
    def _handle_fatal_error(self, context: str, error: Exception):
        """Handle fatal errors with improved diagnostics and cleanup."""
        # Format traceback
        tb = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        error_msg = f"{context}:\n\n{tb}"
        
        # Log the error
        logger.critical(error_msg)
        
        # Show message box
        QMessageBox.critical(
            None,
            "Fatal Error",
            f"A fatal error has occurred:\n\n{error}\n\nThe application will now exit."
        )
        
        # Force exit on fatal errors
        sys.exit(1)
        
    def close(self):
        """Clean up resources in the correct sequence."""
        logger.info("Application shutdown initiated")
        
        # Delegate to lifecycle manager for proper shutdown
        self.lifecycle_manager.shutdown()
        
        # Clean up event management
        self.event_manager.cleanup()
        
        logger.info("Application shutdown complete")
        
    # Delegation methods for backward compatibility
    def register_task(self, coro):
        """Register and track an asyncio task."""
        return self.event_manager.register_task(coro)