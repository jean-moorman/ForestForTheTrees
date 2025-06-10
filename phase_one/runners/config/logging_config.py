"""
Logging Configuration for Phase One Runners

Provides centralized logging setup and configuration for both
GUI and CLI modes of the Phase One application.
"""

import logging


def setup_logging(log_level: str = 'INFO', log_file: str = 'run_phase_one.log'):
    """
    Set up logging configuration for the Phase One application.
    
    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to the log file
    """
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Get logger for this module
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: level={log_level}, file={log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: The logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)