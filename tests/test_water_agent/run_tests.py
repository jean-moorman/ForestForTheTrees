#!/usr/bin/env python
"""
Run the Water Agent tests.

This script runs the Water Agent test suite with the appropriate pytest parameters.
"""

import sys
import os
import subprocess
import argparse


def run_water_agent_tests(verbose=True, specific_test=None, with_coverage=False):
    """
    Run the Water Agent tests.
    
    Args:
        verbose: Whether to run tests in verbose mode
        specific_test: Run only a specific test file or function
        with_coverage: Whether to generate coverage report
    """
    # Get the directory of this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Build pytest command
    command = ["python", "-m", "pytest"]
    
    # Add options
    if verbose:
        command.append("-v")
        
    # Add asyncio mode flag for async tests
    command.extend(["--asyncio-mode=auto"])
    
    # Add coverage if requested
    if with_coverage:
        command.extend([
            "--cov=resources.water_agent",
            "--cov=interfaces.agent.coordination",
            "--cov=phase_one.validation.coordination",
            "--cov-report=term",
            "--cov-report=html"
        ])
    
    # Add specific test if provided
    if specific_test:
        # Check if it's a path or just a name
        if os.path.exists(specific_test):
            command.append(specific_test)
        else:
            # Assume it's a test name pattern
            command.append(os.path.join(current_dir, specific_test))
    else:
        # Run all tests in this directory
        command.append(current_dir)
    
    # Run the tests
    print(f"Running command: {' '.join(command)}")
    result = subprocess.run(command)
    
    return result.returncode


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Water Agent tests")
    parser.add_argument("--quiet", action="store_true", help="Run tests in quiet mode")
    parser.add_argument("--test", help="Run a specific test file or function")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    
    args = parser.parse_args()
    
    exit_code = run_water_agent_tests(
        verbose=not args.quiet,
        specific_test=args.test,
        with_coverage=args.coverage
    )
    
    sys.exit(exit_code)