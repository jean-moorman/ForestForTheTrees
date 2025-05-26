"""
Simple script to test if we've fixed the circular imports.
"""
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Attempt to import the modules
try:
    print("Importing interfaces...")
    from resources.interfaces import base as ibase
    from resources.interfaces import state as istate
    print("✅ Successfully imported interfaces")
    
    print("\nImporting base modules...")
    from resources import base
    from resources import base_resource
    print("✅ Successfully imported base modules")
    
    print("\nImporting state modules...")
    from resources.state import models
    from resources.state import manager
    print("✅ Successfully imported state modules")
    
    print("\nAccessing concrete classes...")
    print(f"BaseManager: {base.BaseManager}")
    print(f"BaseResource: {base_resource.BaseResource}")
    print(f"StateManager: {manager.StateManager}")
    print("✅ Successfully accessed concrete classes")
    
    print("\nAccessing interface classes...")
    print(f"IBaseResource: {ibase.IBaseResource}")
    print(f"IStateManager: {istate.IStateManager}")
    print("✅ Successfully accessed interface classes")
    
    print("\n✅ All imports successful, circular dependencies resolved!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    if "circular import" in str(e):
        print("  ↳ This is a circular dependency issue that needs to be fixed.")
    else:
        print("  ↳ This could be a module not found error or another import issue.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)