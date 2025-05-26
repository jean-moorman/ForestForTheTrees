#!/usr/bin/env python3
"""
Performance test runner for FFTT.
Runs performance and stress tests with extended timeouts.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def main():
    """Run performance tests with extended configuration."""
    test_path = project_root / "tests_new" / "performance"
    
    cmd = [
        sys.executable, "-m", "pytest",
        "-xvs",
        "--log-cli-level=WARNING",  # Reduce log noise for perf tests
        "--log-file=performance_tests.log",
        "--color=yes",
        "--asyncio-mode=auto",
        "--timeout=300",  # 5 minute timeout for performance tests
        str(test_path)
    ]
    
    print(f"Running performance tests: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=project_root)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()