#!/usr/bin/env python
"""
Run all thread safety tests for the event system.

This script runs all thread safety tests with proper pytest configuration.
"""

import os
import sys
import pytest
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('thread_safety_tests.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Run all thread safety tests."""
    # Get the directory of this script
    script_dir = Path(__file__).parent.absolute()
    
    # Collect test files
    test_files = [
        str(script_dir / "test_thread_safety.py"),
        str(script_dir / "test_thread_safety_extended.py")
    ]
    
    logger.info(f"Running thread safety tests from: {script_dir}")
    logger.info(f"Test files: {test_files}")
    
    # Configure pytest arguments
    pytest_args = [
        "-xvs",                   # Verbose output, no capture
        "--log-cli-level=INFO",   # Show INFO-level logs
        "--asyncio-mode=auto",    # Auto-detect asyncio mode
        "--color=yes"             # Colored output
    ] + test_files
    
    # Run tests
    logger.info("Starting test execution...")
    exit_code = pytest.main(pytest_args)
    
    # Report results
    if exit_code == 0:
        logger.info("All thread safety tests passed successfully!")
    else:
        logger.error(f"Thread safety tests failed with exit code: {exit_code}")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())