#!/usr/bin/env python3
"""
Consolidated test runner for all FFTT tests.
Runs the complete test suite with proper configuration.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def run_pytest(test_path, extra_args=None):
    """Run pytest with standard configuration."""
    cmd = [
        sys.executable, "-m", "pytest",
        "-xvs",
        "--log-cli-level=INFO",
        "--log-file=test.log",
        "--color=yes",
        "--asyncio-mode=auto",
        str(test_path)
    ]
    
    if extra_args:
        cmd.extend(extra_args)
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode

def main():
    parser = argparse.ArgumentParser(description="Run FFTT test suite")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--system", action="store_true", help="Run system tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--agents", action="store_true", help="Run agent tests only")
    parser.add_argument("--fast", action="store_true", help="Run tests with minimal output")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    
    args = parser.parse_args()
    
    test_root = project_root / "tests"
    extra_args = []
    
    if args.fast:
        extra_args.extend(["-q", "--tb=short"])
    
    if args.coverage:
        extra_args.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])
    
    exit_code = 0
    
    if args.unit:
        print("=== Running Unit Tests ===")
        exit_code |= run_pytest(test_root / "unit", extra_args)
    elif args.integration:
        print("=== Running Integration Tests ===")
        exit_code |= run_pytest(test_root / "integration", extra_args)
    elif args.system:
        print("=== Running System Tests ===")
        exit_code |= run_pytest(test_root / "system", extra_args)
    elif args.performance:
        print("=== Running Performance Tests ===")
        exit_code |= run_pytest(test_root / "performance", extra_args)
    elif args.agents:
        print("=== Running Agent Tests ===")
        exit_code |= run_pytest(test_root / "agents", extra_args)
    else:
        print("=== Running All Tests ===")
        print("Running Unit Tests...")
        exit_code |= run_pytest(test_root / "unit", extra_args)
        
        print("\nRunning Integration Tests...")
        exit_code |= run_pytest(test_root / "integration", extra_args)
        
        print("\nRunning Agent Tests...")
        exit_code |= run_pytest(test_root / "agents", extra_args)
        
        print("\nRunning Performance Tests...")
        exit_code |= run_pytest(test_root / "performance", extra_args)
        
        if (test_root / "system").exists():
            print("\nRunning System Tests...")
            exit_code |= run_pytest(test_root / "system", extra_args)
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()