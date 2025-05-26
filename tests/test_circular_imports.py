"""
Test for circular imports in the resources package.

This test validates that the interface-based refactoring has resolved
the circular dependencies in the resource package.
"""

import unittest


class TestCircularImports(unittest.TestCase):
    """Test that there are no circular imports in the resources package."""

    def test_base_and_base_resource_imports(self):
        """Test that base.py and base_resource.py can be imported without circular dependencies."""
        try:
            from resources import base
            from resources import base_resource
            # If we get here, no circular imports were detected
            self.assertTrue(True)
        except ImportError as e:
            if "cannot import name" in str(e) and "circular import" in str(e):
                self.fail(f"Circular import detected: {e}")
            else:
                raise

    def test_state_imports(self):
        """Test that state related modules can be imported without circular dependencies."""
        try:
            from resources.state import models
            from resources.state import manager
            from resources.state import validators
            # If we get here, no circular imports were detected
            self.assertTrue(True)
        except ImportError as e:
            if "cannot import name" in str(e) and "circular import" in str(e):
                self.fail(f"Circular import detected: {e}")
            else:
                raise

    def test_interface_imports(self):
        """Test that interface modules can be imported without circular dependencies."""
        try:
            from resources.interfaces import base
            from resources.interfaces import state
            # If we get here, no circular imports were detected
            self.assertTrue(True)
        except ImportError as e:
            if "cannot import name" in str(e) and "circular import" in str(e):
                self.fail(f"Circular import detected: {e}")
            else:
                raise

    def test_full_resource_imports(self):
        """Test that all resource modules can be imported in a single program."""
        try:
            # Import interfaces first
            from resources.interfaces import base as ibase
            from resources.interfaces import state as istate
            
            # Import implementations
            from resources import base
            from resources import base_resource
            from resources.state import models
            from resources.state import manager
            
            # Verify we can access concrete classes
            self.assertIsNotNone(base.BaseManager)
            self.assertIsNotNone(base_resource.BaseResource)
            self.assertIsNotNone(manager.StateManager)
            
            # Verify interface classes
            self.assertIsNotNone(ibase.IBaseResource)
            self.assertIsNotNone(istate.IStateManager)
            
            # If we get here, no circular imports were detected
            self.assertTrue(True)
        except ImportError as e:
            if "cannot import name" in str(e) and "circular import" in str(e):
                self.fail(f"Circular import detected: {e}")
            else:
                raise


if __name__ == "__main__":
    unittest.main()