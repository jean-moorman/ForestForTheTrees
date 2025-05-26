#!/usr/bin/env python3
"""
Runner script for Phase One tests.

This script provides a convenient way to run all Phase One tests including:
- Earth Agent validation tests
- Water Agent coordination tests
- Full Phase One workflow integration
- Dependency verification tests
- Unit tests for Phase One components
"""

import asyncio
import logging
import sys
import argparse
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"phase_one_test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

# Define test module paths
TEST_MODULES = {
    "earth_integration": "test_earth_agent_integration.py",
    "full_integration": "test_phase_one_full_integration.py",
    "workflow": "test_phase_one_workflow.py",
    "water_integration": "test_phase_one_water_agent_integration.py",
    "earth_unit": "test_earth_agent.py",
    "dependency": "test_phase_one_full.py"
}

async def run_earth_agent_tests():
    """Run Earth Agent validation tests."""
    from test_earth_agent_integration import run_earth_agent_tests as run_tests
    logger.info("Running Earth Agent validation tests...")
    result = await run_tests()
    logger.info("Earth Agent validation tests completed")
    return result

async def run_full_phase_one_test():
    """Run full Phase One workflow test."""
    from test_phase_one_full_integration import test_full_phase_one_integration
    logger.info("Running full Phase One workflow test...")
    result = await test_full_phase_one_integration()
    logger.info("Full Phase One workflow test completed")
    return result

async def run_all_integration_tests():
    """Run all Phase One integration tests."""
    try:
        logger.info("Starting Phase One integration tests")
        
        # Run Earth Agent tests first (they're faster)
        earth_result = await run_earth_agent_tests()
        
        # Run full Phase One test
        full_result = await run_full_phase_one_test()
        
        logger.info("Phase One integration tests completed successfully!")
        
        return {
            "earth_agent_tests": earth_result,
            "full_phase_one_test": full_result
        }
        
    except Exception as e:
        logger.error(f"Error running Phase One integration tests: {str(e)}", exc_info=True)
        raise

def run_pytest_tests(test_paths, verbose=True):
    """Run tests using pytest.
    
    Args:
        test_paths: List of test module paths to run
        verbose: Whether to use verbose output
        
    Returns:
        int: Return code from pytest
    """
    # Build command
    cmd = ["python", "-m", "pytest"]
    
    # Add verbosity flags
    if verbose:
        cmd.extend(["-xvs"])
    
    # Add test paths
    cmd.extend(test_paths)
    
    # Log command
    logger.info(f"Running pytest command: {' '.join(cmd)}")
    
    # Run the tests
    process = subprocess.run(cmd, capture_output=False)
    return process.returncode

def main():
    """Parse arguments and run selected tests."""
    parser = argparse.ArgumentParser(description="Run Phase One tests")
    
    # Test selection arguments
    parser.add_argument('--earth-only', action='store_true', help='Run only Earth Agent integration tests')
    parser.add_argument('--full-only', action='store_true', help='Run only full Phase One integration test')
    parser.add_argument('--all-integration', action='store_true', help='Run all integration tests using asyncio')
    parser.add_argument('--workflow', action='store_true', help='Run Phase One workflow tests')
    parser.add_argument('--water', action='store_true', help='Run Water Agent integration tests')
    parser.add_argument('--earth-unit', action='store_true', help='Run Earth Agent unit tests')
    parser.add_argument('--dependency', action='store_true', help='Run dependency verification tests')
    parser.add_argument('--all-pytest', action='store_true', help='Run all tests using pytest')
    
    # Test output arguments
    parser.add_argument('--quiet', action='store_true', help='Run tests with minimal output')
    
    args = parser.parse_args()
    
    # Run tests based on arguments
    if args.earth_only:
        # Run only Earth Agent integration tests
        asyncio.run(run_earth_agent_tests())
    elif args.full_only:
        # Run only full Phase One integration test
        asyncio.run(run_full_phase_one_test())
    elif args.all_integration:
        # Run all integration tests using asyncio
        asyncio.run(run_all_integration_tests())
    else:
        # Determine which tests to run with pytest
        test_paths = []
        
        if args.workflow:
            test_paths.append(TEST_MODULES["workflow"])
        if args.water:
            test_paths.append(TEST_MODULES["water_integration"])
        if args.earth_unit:
            test_paths.append(TEST_MODULES["earth_unit"])
        if args.dependency:
            test_paths.append(TEST_MODULES["dependency"])
            
        # If no specific tests were selected, or all-pytest was specified, run all
        if not test_paths or args.all_pytest:
            test_paths = list(TEST_MODULES.values())
            
        # Run the tests with pytest
        return run_pytest_tests(test_paths, not args.quiet)

if __name__ == "__main__":
    sys.exit(main())