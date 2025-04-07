#!/usr/bin/env python3
"""
Test runner script for Forest application tests.
Executes all test modules with proper pytest configuration.
"""
import sys
import os
import pytest

def run_tests():
    """Run all test modules"""
    print("Forest Application Test Suite")
    print("===========================")
    test_dir = "tests/test_main"
    print("All directory files: ", os.listdir(f'./{test_dir}'))
    # Find all test files in current directory
    test_files = [f for f in os.listdir('./tests/test_main') if f.startswith('test_') and f.endswith('.py')]
    
    if not test_files:
        print("No test files found! Make sure test files are named test_*.py")
        return 1
    
    print(f"Found {len(test_files)} test modules to run:")
    for filename in test_files:
        print(f"  - {filename}")
    print()
    test_paths = [f"{test_dir}/"+p for p in test_files]
    
    # Run pytest with appropriate configuration
    args = [
        "-xvs",                # Verbose output, exit on first failure
        "--log-cli-level=INFO",  # Show INFO logs in console output
        "--log-file=test.log",  # Log to file for review
        "--color=yes"          # Colorized output
    ]
    
    args.extend(test_paths)    # Add test files to run
    
    print("Running tests...")
    print("===========================")
    return pytest.main(args)

if __name__ == "__main__":
    sys.exit(run_tests())