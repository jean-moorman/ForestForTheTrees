#!/usr/bin/env python3
import os
import pytest
import sys

def run_tests():
    """Run all test files for resources/managers.py."""
    print("Running unit tests for resources/managers.py...\n")
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Test files to run
    test_files = [
        os.path.join(script_dir, "test_context_manager.py"),
        os.path.join(script_dir, "test_cache_manager.py"),
        os.path.join(script_dir, "test_metrics_manager.py"),
        os.path.join(script_dir, "test_manager_integration.py"),
        os.path.join(script_dir, "test_circuit_breaker_registry.py"),
        os.path.join(script_dir, "test_resource_coordinator.py")
    ]
    
    # Verify all test files exist
    for file in test_files:
        if not os.path.exists(file):
            print(f"Error: Test file not found: {file}")
            return 1
    
    # Run tests with pytest
    pytest_args = [
        "-xvs",            # x: stop on first failure, v: verbose, s: don't capture output
        "--asyncio-mode=auto",  # Use auto mode for asyncio
    ] + test_files
    
    return pytest.main(pytest_args)

if __name__ == "__main__":
    sys.exit(run_tests())