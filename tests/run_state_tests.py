import unittest
import sys
import os
from unittest.mock import MagicMock

# Set up path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock problematic imports
sys.modules['resources.phase_coordination_integration'] = MagicMock()

# Import test classes
try:
    # Core tests
    from test_state_core import (
        TestStateEntryBasic, 
        TestStateSnapshotBasic,
        TestStateTransitionValidatorBasic
    )
    
    # Backend concurrency tests
    from test_state_backends_concurrency import (
        TestFileBackendConcurrency,
        TestSQLiteBackendConcurrency
    )
    
    # Manager tests
    from test_state_manager import (
        TestStateManager,
        TestStateManagerErrorRecovery,
        TestCustomStateTypes
    )
    
    # Repair tests
    from test_state_repair import (
        TestFileBackendRepair,
        TestSQLiteBackendRepair
    )
    
    # Original backend tests
    from test_state_backends import (
        TestMemoryStateBackend,
        TestFileStateBackend
    )
    
    if __name__ == '__main__':
        # Create test suite
        suite = unittest.TestSuite()
        
        # Add core tests
        print("Adding core state tests...")
        suite.addTest(unittest.makeSuite(TestStateEntryBasic))
        suite.addTest(unittest.makeSuite(TestStateSnapshotBasic))
        suite.addTest(unittest.makeSuite(TestStateTransitionValidatorBasic))
        
        # Add original backend tests
        print("Adding original backend tests...")
        suite.addTest(unittest.makeSuite(TestMemoryStateBackend))
        suite.addTest(unittest.makeSuite(TestFileStateBackend))
        
        # Add backend concurrency tests
        print("Adding backend concurrency tests...")
        suite.addTest(unittest.makeSuite(TestFileBackendConcurrency))
        suite.addTest(unittest.makeSuite(TestSQLiteBackendConcurrency))
        
        # Add manager tests
        print("Adding state manager tests...")
        suite.addTest(unittest.makeSuite(TestStateManager))
        suite.addTest(unittest.makeSuite(TestStateManagerErrorRecovery))
        suite.addTest(unittest.makeSuite(TestCustomStateTypes))
        
        # Add repair tests
        print("Adding repair tests...")
        suite.addTest(unittest.makeSuite(TestFileBackendRepair))
        suite.addTest(unittest.makeSuite(TestSQLiteBackendRepair))
        
        # Run tests
        print("Running all state module tests...")
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Return proper exit code
        sys.exit(not result.wasSuccessful())

except ImportError as e:
    print(f"Error importing test modules: {e}")
    print("Running limited test set...")
    
    # Import only existing test classes for backward compatibility
    if os.path.exists("test_state.py"):
        from test_state import unittest
        unittest.main()
    else:
        print("No test modules found.")
        sys.exit(1)