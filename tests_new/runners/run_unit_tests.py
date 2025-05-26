#!/usr/bin/env python3
"""
Unit test runner for FFTT.
Runs all unit tests with optimized configuration.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def main():
    """Run unit tests with standard pytest configuration."""
    test_path = project_root / "tests_new" / "unit"
    
    cmd = [
        sys.executable, "-m", "pytest",
        "-xvs",
        "--log-cli-level=INFO",
        "--log-file=unit_tests.log",
        "--color=yes",
        "--asyncio-mode=auto",
        str(test_path)
    ]
    
    print(f"Running unit tests: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=project_root)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()