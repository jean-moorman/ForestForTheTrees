#!/usr/bin/env python3
"""
Run Phase One Standalone Script

This script runs just the Phase One of the FFTT system, similar to main.py but without
the Phase Two dependencies. It includes the Earth agent for validation and the Water agent
for coordination between sequential agents.

It provides both a complete GUI using display.py and a command-line interface for testing
Phase One functionality with interactive debugging capabilities.

This is now a simplified wrapper that delegates to the modular structure in
phase_one/runners/ while maintaining backward compatibility.
"""

import sys

# Import the modular main function
from phase_one.runners.main import run_application

# Re-export classes for backward compatibility
from phase_one.runners.cli.debugger import PhaseOneDebugger
from phase_one.runners.cli.interface import PhaseOneCLI, run_cli_mode
from phase_one.runners.gui.app import PhaseOneApp
from phase_one.runners.gui.interface import PhaseOneInterface
from phase_one.runners.main import main, APPLICATION_MAIN_LOOP

# Re-export configuration functions
from phase_one.runners.config.argument_parser import parse_arguments
from phase_one.runners.config.logging_config import setup_logging

# For any code that imports these directly from run_phase_one
__all__ = [
    'PhaseOneDebugger',
    'PhaseOneCLI', 
    'PhaseOneApp',
    'PhaseOneInterface',
    'main',
    'run_cli_mode',
    'parse_arguments',
    'APPLICATION_MAIN_LOOP'
]

if __name__ == "__main__":
    # Delegate to the modular main function
    sys.exit(run_application())