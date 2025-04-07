#!/usr/bin/env python3
"""
Runner script for system error recovery tests.
"""
import os
import sys
import subprocess
import asyncio


def run_tests():
    """Run all system error recovery tests."""
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(current_dir))
    
    # Run the tests
    cmd = [
        "python", "-m", "pytest", "-xvs",
        "--asyncio-mode=auto",
        "--log-cli-level=INFO",
        "--color=yes",
        current_dir
    ]
    
    print(f"Running tests in {current_dir}")
    print(f"Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode


if __name__ == "__main__":
    sys.exit(run_tests())