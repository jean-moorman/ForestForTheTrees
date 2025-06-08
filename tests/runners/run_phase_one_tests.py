#!/usr/bin/env python3
"""
Comprehensive Phase One Test Runner

This script runs all phase one tests with proper configuration and reporting.
Designed for both development and CI/CD environments.
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class PhaseOneTestRunner:
    """Comprehensive test runner for Phase One functionality."""
    
    def __init__(self, verbose: bool = True, timeout: int = 300):
        self.verbose = verbose
        self.timeout = timeout
        self.project_root = project_root
        self.test_results = {}
        
    def run_pytest(self, test_path: str, extra_args: List[str] = None, timeout: int = None) -> Dict[str, Any]:
        """Run pytest with standard configuration."""
        cmd = [
            sys.executable, "-m", "pytest",
            str(test_path),
            "-v" if self.verbose else "-q",
            "--tb=short",
            "--asyncio-mode=auto",
            "--disable-warnings"
        ]
        
        if extra_args:
            cmd.extend(extra_args)
        
        test_timeout = timeout or self.timeout
        
        print(f"Running: {' '.join(cmd)}")
        print(f"Timeout: {test_timeout} seconds")
        
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd, 
                cwd=self.project_root,
                timeout=test_timeout,
                capture_output=True,
                text=True
            )
            execution_time = time.time() - start_time
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time": execution_time,
                "timed_out": False
            }
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": f"Test timed out after {test_timeout} seconds",
                "execution_time": execution_time,
                "timed_out": True
            }
    
    def run_garden_planner_tests(self) -> bool:
        """Run Garden Planner agent tests."""
        print("\n=== Running Garden Planner Tests ===")
        
        test_files = [
            "tests/unit/agents/test_garden_planner_real_llm.py",
            "tests/unit/agents/test_garden_planner_agent.py"
        ]
        
        success = True
        for test_file in test_files:
            if (self.project_root / test_file).exists():
                result = self.run_pytest(test_file, timeout=180)
                self.test_results[f"garden_planner_{Path(test_file).stem}"] = result
                
                if result["returncode"] != 0:
                    success = False
                    print(f"❌ {test_file} failed")
                    if self.verbose:
                        print("STDERR:", result["stderr"])
                else:
                    print(f"✅ {test_file} passed ({result['execution_time']:.1f}s)")
        
        return success
    
    def run_earth_agent_tests(self) -> bool:
        """Run Earth Agent tests."""
        print("\n=== Running Earth Agent Tests ===")
        
        test_files = [
            "tests/unit/agents/test_earth_agent_validation_prompts_real_llm.py",
            "tests/unit/agents/test_earth_agent_validation_core.py",
            "tests/unit/agents/test_earth_agent_validation_accuracy.py"
        ]
        
        success = True
        for test_file in test_files:
            if (self.project_root / test_file).exists():
                result = self.run_pytest(test_file, timeout=240)
                self.test_results[f"earth_agent_{Path(test_file).stem}"] = result
                
                if result["returncode"] != 0:
                    success = False
                    print(f"❌ {test_file} failed")
                    if self.verbose:
                        print("STDERR:", result["stderr"])
                else:
                    print(f"✅ {test_file} passed ({result['execution_time']:.1f}s)")
        
        return success
    
    def run_environmental_analysis_tests(self) -> bool:
        """Run Environmental Analysis agent tests."""
        print("\n=== Running Environmental Analysis Tests ===")
        
        test_files = [
            "tests/unit/agents/test_environmental_analysis_real_llm.py",
            "tests/unit/agents/test_environmental_analysis_agent.py"
        ]
        
        success = True
        for test_file in test_files:
            if (self.project_root / test_file).exists():
                result = self.run_pytest(test_file, timeout=180)
                self.test_results[f"environmental_analysis_{Path(test_file).stem}"] = result
                
                if result["returncode"] != 0:
                    success = False
                    print(f"❌ {test_file} failed")
                    if self.verbose:
                        print("STDERR:", result["stderr"])
                else:
                    print(f"✅ {test_file} passed ({result['execution_time']:.1f}s)")
        
        return success
    
    def run_root_system_architect_tests(self) -> bool:
        """Run Root System Architect agent tests."""
        print("\n=== Running Root System Architect Tests ===")
        
        test_files = [
            "tests/unit/agents/test_root_system_architect_real_llm.py",
            "tests/unit/agents/test_root_system_architect_agent.py"
        ]
        
        success = True
        for test_file in test_files:
            if (self.project_root / test_file).exists():
                result = self.run_pytest(test_file, timeout=180)
                self.test_results[f"root_system_architect_{Path(test_file).stem}"] = result
                
                if result["returncode"] != 0:
                    success = False
                    print(f"❌ {test_file} failed")
                    if self.verbose:
                        print("STDERR:", result["stderr"])
                else:
                    print(f"✅ {test_file} passed ({result['execution_time']:.1f}s)")
        
        return success
    
    def run_tree_placement_planner_tests(self) -> bool:
        """Run Tree Placement Planner agent tests."""
        print("\n=== Running Tree Placement Planner Tests ===")
        
        test_files = [
            "tests/unit/agents/test_tree_placement_planner_real_llm.py",
            "tests/unit/phases/test_tree_placement_planner_agent.py"
        ]
        
        success = True
        for test_file in test_files:
            if (self.project_root / test_file).exists():
                result = self.run_pytest(test_file, timeout=180)
                self.test_results[f"tree_placement_planner_{Path(test_file).stem}"] = result
                
                if result["returncode"] != 0:
                    success = False
                    print(f"❌ {test_file} failed")
                    if self.verbose:
                        print("STDERR:", result["stderr"])
                else:
                    print(f"✅ {test_file} passed ({result['execution_time']:.1f}s)")
        
        return success
    
    def run_foundation_refinement_tests(self) -> bool:
        """Run Foundation Refinement agent tests."""
        print("\n=== Running Foundation Refinement Tests ===")
        
        test_files = [
            "tests/unit/agents/test_foundation_refinement_real_llm.py",
            "tests/unit/phases/test_foundation_refinement_agent.py"
        ]
        
        success = True
        for test_file in test_files:
            if (self.project_root / test_file).exists():
                result = self.run_pytest(test_file, timeout=180)
                self.test_results[f"foundation_refinement_{Path(test_file).stem}"] = result
                
                if result["returncode"] != 0:
                    success = False
                    print(f"❌ {test_file} failed")
                    if self.verbose:
                        print("STDERR:", result["stderr"])
                else:
                    print(f"✅ {test_file} passed ({result['execution_time']:.1f}s)")
        
        return success
    
    def run_prompt_validation_tests(self) -> bool:
        """Run comprehensive prompt validation tests."""
        print("\n=== Running Prompt Validation Tests ===")
        
        test_files = [
            "tests/unit/validation/test_prompt_validation_comprehensive.py"
        ]
        
        success = True
        for test_file in test_files:
            if (self.project_root / test_file).exists():
                result = self.run_pytest(test_file, timeout=600)  # Extended timeout for comprehensive tests
                self.test_results[f"prompt_validation_{Path(test_file).stem}"] = result
                
                if result["returncode"] != 0:
                    success = False
                    print(f"❌ {test_file} failed")
                    if self.verbose:
                        print("STDERR:", result["stderr"])
                else:
                    print(f"✅ {test_file} passed ({result['execution_time']:.1f}s)")
        
        return success
    
    def run_integration_tests(self) -> bool:
        """Run integration tests."""
        print("\n=== Running Integration Tests ===")
        
        test_files = [
            "tests/integration/test_phase_one_workflow_optimized.py",
            "tests/integration/test_phase_one_orchestrator.py"
        ]
        
        success = True
        for test_file in test_files:
            if (self.project_root / test_file).exists():
                result = self.run_pytest(test_file, timeout=300)
                self.test_results[f"integration_{Path(test_file).stem}"] = result
                
                if result["returncode"] != 0:
                    success = False
                    print(f"❌ {test_file} failed")
                    if self.verbose:
                        print("STDERR:", result["stderr"])
                else:
                    print(f"✅ {test_file} passed ({result['execution_time']:.1f}s)")
        
        return success
    
    def run_workflow_tests(self) -> bool:
        """Run workflow-specific tests."""
        print("\n=== Running Workflow Tests ===")
        
        test_files = [
            "tests/integration/test_phase_one_workflow.py",
            "tests/integration/test_phase_one_full.py"
        ]
        
        success = True
        for test_file in test_files:
            if (self.project_root / test_file).exists():
                result = self.run_pytest(test_file, timeout=400)
                self.test_results[f"workflow_{Path(test_file).stem}"] = result
                
                if result["returncode"] != 0:
                    success = False
                    print(f"❌ {test_file} failed")
                    if self.verbose and not result["timed_out"]:
                        print("STDERR:", result["stderr"])
                else:
                    print(f"✅ {test_file} passed ({result['execution_time']:.1f}s)")
        
        return success
    
    def run_smoke_tests(self) -> bool:
        """Run quick smoke tests for CI/CD."""
        print("\n=== Running Smoke Tests ===")
        
        # Run a subset of fast tests
        result = self.run_pytest(
            "tests/integration/test_phase_one_workflow_optimized.py::TestPhaseOneWorkflowCI",
            timeout=120
        )
        
        self.test_results["smoke_tests"] = result
        
        if result["returncode"] != 0:
            print("❌ Smoke tests failed")
            if self.verbose:
                print("STDERR:", result["stderr"])
            return False
        else:
            print(f"✅ Smoke tests passed ({result['execution_time']:.1f}s)")
            return True
    
    def print_summary(self):
        """Print test execution summary."""
        print("\n" + "="*60)
        print("PHASE ONE TEST EXECUTION SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["returncode"] == 0)
        failed_tests = total_tests - passed_tests
        total_time = sum(result["execution_time"] for result in self.test_results.values())
        
        print(f"Total test suites: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Total execution time: {total_time:.1f} seconds")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TEST SUITES:")
            for test_name, result in self.test_results.items():
                if result["returncode"] != 0:
                    status = "TIMEOUT" if result["timed_out"] else "FAILED"
                    print(f"  - {test_name}: {status} ({result['execution_time']:.1f}s)")
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        print(f"\nSuccess rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 Phase One tests are in good shape!")
        elif success_rate >= 60:
            print("⚠️  Phase One tests need some attention")
        else:
            print("🚨 Phase One tests require immediate attention")
    
    def run_all_tests(self) -> bool:
        """Run all phase one tests."""
        print("Starting comprehensive Phase One test execution...")
        print(f"Project root: {self.project_root}")
        
        overall_success = True
        
        # Check for API key
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("⚠️  ANTHROPIC_API_KEY not set - some tests may be skipped")
        
        # Run test suites
        test_suites = [
            ("Garden Planner", self.run_garden_planner_tests),
            ("Earth Agent", self.run_earth_agent_tests),
            ("Environmental Analysis", self.run_environmental_analysis_tests),
            ("Root System Architect", self.run_root_system_architect_tests),
            ("Tree Placement Planner", self.run_tree_placement_planner_tests),
            ("Foundation Refinement", self.run_foundation_refinement_tests),
            ("Integration", self.run_integration_tests),
        ]
        
        for suite_name, suite_func in test_suites:
            print(f"\n📋 Running {suite_name} test suite...")
            success = suite_func()
            if not success:
                overall_success = False
                print(f"❌ {suite_name} test suite failed")
            else:
                print(f"✅ {suite_name} test suite passed")
        
        return overall_success

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Phase One Test Runner")
    parser.add_argument("--suite", choices=[
        "all", "agents", "integration", "workflow", "smoke", "prompt-validation"
    ], default="all", help="Test suite to run")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--timeout", type=int, default=300, help="Default timeout per test file")
    parser.add_argument("--api-key-required", action="store_true", help="Require API key for real LLM tests")
    
    args = parser.parse_args()
    
    # Check API key requirement
    if args.api_key_required and not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY is required but not set")
        sys.exit(1)
    
    runner = PhaseOneTestRunner(verbose=args.verbose, timeout=args.timeout)
    
    success = True
    
    if args.suite == "all":
        success = runner.run_all_tests()
        # Also run prompt validation if API key is available
        if os.getenv("ANTHROPIC_API_KEY"):
            print("\n📋 Running Prompt Validation suite...")
            prompt_success = runner.run_prompt_validation_tests()
            success = success and prompt_success
    elif args.suite == "agents":
        test_suites = [
            runner.run_garden_planner_tests,
            runner.run_earth_agent_tests,
            runner.run_environmental_analysis_tests,
            runner.run_root_system_architect_tests,
            runner.run_tree_placement_planner_tests,
            runner.run_foundation_refinement_tests,
        ]
        for suite_func in test_suites:
            success = suite_func() and success
    elif args.suite == "integration":
        success = runner.run_integration_tests()
    elif args.suite == "workflow":
        success = runner.run_workflow_tests()
    elif args.suite == "smoke":
        success = runner.run_smoke_tests()
    elif args.suite == "prompt-validation":
        success = runner.run_prompt_validation_tests()
    
    # Print summary
    runner.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()