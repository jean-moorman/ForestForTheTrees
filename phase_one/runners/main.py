"""
Main Launcher for Phase One Runners

Simplified main entry point that coordinates CLI and GUI modes,
handles argument parsing, and manages application lifecycle.
"""

import asyncio
import logging
import sys
import traceback

import qasync
from PyQt6.QtWidgets import QApplication, QMessageBox

from .config.argument_parser import parse_arguments, determine_mode
from .config.logging_config import setup_logging
from .cli.interface import run_cli_mode
from .gui.app import PhaseOneApp

# Global reference to main application event loop
APPLICATION_MAIN_LOOP = None

logger = logging.getLogger(__name__)


async def main():
    """Main function to initialize and run the application."""
    # Use the global variable without declaring it again
    phase_one_app = None
    try:
        # The event loop should already be set up by qasync
        loop = asyncio.get_event_loop()
        logger.info(f"Main function running in event loop {id(loop)}")
        
        # Ensure loop is available globally and through EventLoopManager
        global APPLICATION_MAIN_LOOP
        if APPLICATION_MAIN_LOOP is None:
            APPLICATION_MAIN_LOOP = loop
            
        # Register with EventLoopManager for consistent access
        from resources.events.loop_management import EventLoopManager
        result = EventLoopManager.set_primary_loop(loop)
        logger.info(f"Registered event loop with EventLoopManager in main(): {result}")
        
        # Create the application instance with deferred initialization
        phase_one_app = PhaseOneApp()
        
        # Store loop reference in the app
        phase_one_app.loop = loop
        phase_one_app.main_loop = loop
        
        # Now perform async initialization
        logger.info("Running setup_async")
        await phase_one_app.setup_async()
        
        # Configure the main window's async components
        logger.info("Setting up main window async components")
        if hasattr(phase_one_app, 'main_window') and hasattr(phase_one_app.main_window, 'setup_async'):
            await phase_one_app.main_window.setup_async()
            
        return phase_one_app
    except Exception as e:
        logger.critical("Application failed to start", exc_info=True)
        QMessageBox.critical(None, "Startup Error", 
            f"The application failed to start:\n\n{str(e)}")
        if phase_one_app:
            phase_one_app.close()
        return None


def run_gui_mode():
    """Run the application in GUI mode."""
    try:
        # Create the Qt application
        app = QApplication.instance() or QApplication(sys.argv)
        app._is_running = False  # Add flag to track event loop state
        
        # Configure qasync
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        logger.info(f"Created qasync event loop: {id(loop)}")
        
        # Store the loop in the global variable for consistent access
        global APPLICATION_MAIN_LOOP
        APPLICATION_MAIN_LOOP = loop
        
        # Register with EventLoopManager for consistent access
        from resources.events.loop_management import EventLoopManager
        result = EventLoopManager.set_primary_loop(loop)
        logger.info(f"Registered main event loop with EventLoopManager: {result}")
        
        # Initialize the phase_one_app variable
        phase_one_app = None
        
        # Run the application with proper cleanup
        with loop:
            try:
                # Initialize the application
                logger.info("Running main() to initialize application")
                phase_one_app = loop.run_until_complete(main())
                
                if phase_one_app:
                    # Replace the exception hook with the application's version
                    sys.excepthook = phase_one_app._global_exception_handler
                    
                    # Start the application
                    logger.info("Starting application main loop")
                    exit_code = phase_one_app.run()
                else:
                    logger.error("Application initialization failed")
                    exit_code = 1
            finally:
                # Clean up properly
                if phase_one_app:
                    try:
                        logger.info("Closing application")
                        phase_one_app.close()
                    except Exception as e:
                        logger.error(f"Error during application cleanup: {e}", exc_info=True)
                        
        # Final cleanup
        logger.info("Processing final events")
        app.processEvents()
        
        # Quit only if the app isn't already being quit
        if not app._is_running:
            logger.info("Quitting application")
            app.quit()
            
        logger.info(f"Exiting with code {exit_code}")
        return exit_code
        
    except Exception as e:
        logger.critical("Failed to initialize GUI application", exc_info=True)
        # Show error dialog for truly catastrophic failures
        try:
            QMessageBox.critical(None, "Fatal Error", 
                f"The application failed catastrophically:\n\n{str(e)}")
        except:
            print(f"FATAL ERROR: {e}")
            traceback.print_exc()
        return 1


def run_application():
    """
    Main entry point for the Phase One application.
    Handles argument parsing and mode determination.
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Configure logging based on arguments
    setup_logging(args.log_level, args.log_file)
    
    # Determine mode - CLI takes precedence over GUI
    cli_mode, mode_desc = determine_mode(args)
    logger.info(f"Starting Phase One application in {mode_desc}")
    
    if cli_mode:
        # Run in CLI mode
        try:
            asyncio.run(run_cli_mode(args))
            return 0
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user")
            return 0
        except Exception as e:
            logger.critical(f"CLI mode failed: {e}", exc_info=True)
            print(f"❌ Fatal error: {str(e)}")
            return 1
    else:
        # Run in GUI mode (default)
        return run_gui_mode()


if __name__ == "__main__":
    sys.exit(run_application())