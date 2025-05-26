#!/usr/bin/env python3
"""
Run basic state module tests that don't require complex initialization.
"""
import os
import sys
import unittest

# Add parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import test cases
from basic_state_test import TestBasicStateElements

if __name__ == "__main__":
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTest(unittest.makeSuite(TestBasicStateElements))
    
    # Run tests
    print("Running basic state tests...")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return proper exit code
    sys.exit(not result.wasSuccessful())