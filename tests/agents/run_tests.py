#!/usr/bin/env python
"""
Run the Agent tests.

This script runs the comprehensive agent test suite including Water, Fire, and Air agents
with the appropriate pytest parameters.
"""

import sys
import os
import subprocess
import argparse


def run_agent_tests(verbose=True, specific_test=None, with_coverage=False, agent_type=None):
    """
    Run the agent tests.
    
    Args:
        verbose: Whether to run tests in verbose mode
        specific_test: Run only a specific test file or function
        with_coverage: Whether to generate coverage report
        agent_type: Specific agent type to test ('fire', 'air', 'water', 'integration', or None for all)
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
        coverage_modules = [
            "--cov=resources.fire_agent",
            "--cov=resources.air_agent", 
            "--cov=resources.water_agent",
            "--cov=interfaces.agent.coordination",
            "--cov=phase_one.validation.coordination",
            "--cov=phase_one.workflow",
            "--cov=phase_three.evolution.natural_selection"
        ]
        command.extend(coverage_modules)
        command.extend([
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
    elif agent_type:
        # Run tests for specific agent type
        if agent_type == "fire":
            command.append(os.path.join(current_dir, "test_fire_agent.py"))
        elif agent_type == "air":
            command.append(os.path.join(current_dir, "test_air_agent.py"))
        elif agent_type == "water":
            command.extend([
                os.path.join(current_dir, "test_water_agent_coordinator.py"),
                os.path.join(current_dir, "test_coordination_interface.py"),
                os.path.join(current_dir, "test_sequential_agent_coordinator.py")
            ])
        elif agent_type == "integration":
            command.append(os.path.join(current_dir, "test_fire_air_integration.py"))
        else:
            print(f"Unknown agent type: {agent_type}")
            print("Available types: fire, air, water, integration")
            return 1
    else:
        # Run all tests in this directory
        command.append(current_dir)
    
    # Run the tests
    print(f"Running command: {' '.join(command)}")
    result = subprocess.run(command)
    
    return result.returncode


def list_available_tests():
    """List all available test files in the directory."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_files = [f for f in os.listdir(current_dir) if f.startswith('test_') and f.endswith('.py')]
    
    print("Available test files:")
    for test_file in sorted(test_files):
        print(f"  - {test_file}")
    
    print("\nAgent types:")
    print("  - fire: Fire Agent complexity detection and decomposition tests")
    print("  - air: Air Agent historical context and decision tracking tests") 
    print("  - water: Water Agent coordination and integration tests")
    print("  - integration: Fire/Air agent workflow integration tests")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Agent tests")
    parser.add_argument("--quiet", action="store_true", help="Run tests in quiet mode")
    parser.add_argument("--test", help="Run a specific test file or function")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--agent", choices=["fire", "air", "water", "integration"], 
                       help="Run tests for specific agent type")
    parser.add_argument("--list", action="store_true", help="List available tests")
    
    args = parser.parse_args()
    
    if args.list:
        list_available_tests()
        sys.exit(0)
    
    exit_code = run_agent_tests(
        verbose=not args.quiet,
        specific_test=args.test,
        with_coverage=args.coverage,
        agent_type=args.agent
    )
    
    sys.exit(exit_code)