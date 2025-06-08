#!/usr/bin/env python3
"""
Test runner for comprehensive Earth Agent test suite.

This script runs all Earth Agent tests with proper configuration and reporting.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def run_test_suite():
    """Run the complete Earth Agent test suite."""
    print("🌍 Earth Agent Comprehensive Test Suite")
    print("=" * 50)
    
    # Define test modules in order of execution (with full paths from project root)
    test_modules = [
        "tests_new/unit/agents/test_earth_agent_validation_core.py",
        "tests_new/unit/agents/test_earth_agent_validation_accuracy.py", 
        "tests_new/unit/agents/test_earth_agent_reflection_revision.py",
        "tests_new/unit/agents/test_earth_agent_error_handling.py"
    ]
    
    integration_tests = [
        "tests_new/integration/test_earth_agent_full_validation_workflow.py"
    ]
    
    all_passed = True
    start_time = time.time()
    
    print("\n📝 Running Unit Tests...")
    print("-" * 30)
    
    for test_module in test_modules:
        print(f"\n🧪 Running {test_module}...")
        
        cmd = [
            sys.executable, "-m", "pytest", 
            test_module,
            "-v",
            "--tb=short",
            "--color=yes",
            "--asyncio-mode=auto"
        ]
        
        try:
            # Run from project root to ensure correct schema paths
            project_root = Path(__file__).parent.parent.parent.parent
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
            
            if result.returncode == 0:
                print(f"✅ {test_module} - PASSED")
            else:
                print(f"❌ {test_module} - FAILED")
                print("STDOUT:", result.stdout[-500:])  # Last 500 chars
                print("STDERR:", result.stderr[-500:])  # Last 500 chars
                all_passed = False
                
        except Exception as e:
            print(f"❌ {test_module} - ERROR: {e}")
            all_passed = False
    
    print("\n🔗 Running Integration Tests...")
    print("-" * 35)
    
    for test_module in integration_tests:
        print(f"\n🧪 Running {test_module}...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            test_module,
            "-v", 
            "--tb=short",
            "--color=yes",
            "--asyncio-mode=auto"
        ]
        
        try:
            # Run from project root to ensure correct schema paths
            project_root = Path(__file__).parent.parent.parent.parent
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
            
            if result.returncode == 0:
                print(f"✅ {test_module} - PASSED")
            else:
                print(f"❌ {test_module} - FAILED")
                print("STDOUT:", result.stdout[-500:])
                print("STDERR:", result.stderr[-500:])
                all_passed = False
                
        except Exception as e:
            print(f"❌ {test_module} - ERROR: {e}")
            all_passed = False
    
    # Summary
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 50)
    print("📊 TEST SUITE SUMMARY")
    print("=" * 50)
    
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print(f"⏱️  Total time: {duration:.2f} seconds")
        print("\n✨ Earth Agent validation logic is working correctly!")
        return 0
    else:
        print("💥 SOME TESTS FAILED!")
        print(f"⏱️  Total time: {duration:.2f} seconds")
        print("\n🔍 Check the test output above for details.")
        return 1

def run_specific_test_category(category):
    """Run a specific category of tests."""
    categories = {
        "core": ["tests_new/unit/agents/test_earth_agent_validation_core.py"],
        "accuracy": ["tests_new/unit/agents/test_earth_agent_validation_accuracy.py"],
        "reflection": ["tests_new/unit/agents/test_earth_agent_reflection_revision.py"],
        "errors": ["tests_new/unit/agents/test_earth_agent_error_handling.py"],
        "integration": ["tests_new/integration/test_earth_agent_full_validation_workflow.py"]
    }
    
    if category not in categories:
        print(f"❌ Unknown category: {category}")
        print(f"Available categories: {', '.join(categories.keys())}")
        return 1
    
    print(f"🧪 Running {category} tests...")
    
    for test_module in categories[category]:
        cmd = [
            sys.executable, "-m", "pytest",
            test_module,
            "-v",
            "--tb=long",
            "--color=yes", 
            "--asyncio-mode=auto"
        ]
        
        # Run from project root to ensure correct schema paths
        project_root = Path(__file__).parent.parent.parent.parent
        result = subprocess.run(cmd, cwd=project_root)
        if result.returncode != 0:
            return 1
    
    return 0

if __name__ == "__main__":
    if len(sys.argv) > 1:
        category = sys.argv[1]
        exit_code = run_specific_test_category(category)
    else:
        exit_code = run_test_suite()
    
    sys.exit(exit_code)