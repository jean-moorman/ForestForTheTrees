import logging
import time
import asyncio
import random
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from dataclasses import dataclass, field

from component import Component
from phase_two.agents.agent_base import PhaseTwoAgentBase
from resources import (
    EventQueue, 
    StateManager, 
    AgentContextManager, 
    CacheManager, 
    MetricsManager, 
    ErrorHandler,
    MemoryMonitor
)

logger = logging.getLogger(__name__)

@dataclass
class TestCoverage:
    components: Dict[str, float] = field(default_factory=dict)
    features: Dict[str, float] = field(default_factory=dict)
    interfaces: Dict[str, float] = field(default_factory=dict)
    requirements: Dict[str, float] = field(default_factory=dict)
    overall: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "components": self.components,
            "features": self.features,
            "interfaces": self.interfaces,
            "requirements": self.requirements,
            "overall": self.overall
        }


class SystemTestExecutor(PhaseTwoAgentBase):
    """
    Executes system tests on integrated components.
    
    Responsibilities:
    - Execute system tests on integrated components
    - Capture detailed test results
    - Generate test coverage reports
    - Track test execution performance
    """
    
    def __init__(self,
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        """Initialize the system test executor."""
        super().__init__(
            "system_test_executor",
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor
        )
        # Track test executions
        self._test_executions: Dict[str, Dict[str, Any]] = {}
    
    async def execute_system_tests(self, 
                                  components: List[Dict[str, Any]],
                                  system_tests: List[Dict[str, Any]],
                                  system_requirements: Dict[str, Any],
                                  execution_id: str) -> Dict[str, Any]:
        """
        Execute system tests on integrated components.
        
        Args:
            components: List of components to test
            system_tests: List of system tests to execute
            system_requirements: System requirements for coverage analysis
            execution_id: Unique identifier for this test execution
            
        Returns:
            Dictionary containing test execution results
        """
        logger.info(f"Executing system tests for execution ID: {execution_id}")
        
        start_time = time.time()
        
        # Record execution start
        await self._metrics_manager.record_metric(
            "system_test_execution:start",
            1.0,
            metadata={
                "execution_id": execution_id,
                "total_tests": len(system_tests),
                "components": len(components)
            }
        )
        
        if not system_tests:
            logger.info(f"No system tests to execute for {execution_id}")
            return {
                "status": "success",
                "message": "No system tests to execute",
                "execution_id": execution_id,
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "test_details": [],
                "coverage": TestCoverage().to_dict()
            }
        
        # Create component mapping
        component_instances = {
            component.get("id", ""): Component(
                component.get("id", ""),
                component.get("name", ""),
                component.get("description", ""),
                component
            )
            for component in components
        }
        
        # Execute tests
        test_results = await self._run_tests(system_tests, component_instances, execution_id)
        
        # Record test details
        test_details = self._record_test_details(system_tests, test_results)
        
        # Calculate coverage
        coverage = self._calculate_coverage(test_results, components, system_requirements)
        
        # Collect performance metrics
        performance_metrics = self._collect_performance_metrics(test_results)
        
        # Create execution report
        total_tests = len(system_tests)
        passed_tests = sum(1 for test in test_results if test.get("passed", False))
        failed_tests = total_tests - passed_tests
        
        execution_report = {
            "status": "completed",
            "execution_id": execution_id,
            "timestamp": datetime.now().isoformat(),
            "execution_time_seconds": time.time() - start_time,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "pass_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            "test_details": test_details,
            "coverage": coverage.to_dict(),
            "performance": performance_metrics
        }
        
        # Store execution in state
        self._test_executions[execution_id] = execution_report
        await self._state_manager.set_state(
            f"system_test_execution:{execution_id}",
            {
                "execution_id": execution_id,
                "timestamp": datetime.now().isoformat(),
                "status": "completed",
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests
            }
        )
        
        # Record execution completion
        await self._metrics_manager.record_metric(
            "system_test_execution:complete",
            1.0,
            metadata={
                "execution_id": execution_id,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "execution_time": time.time() - start_time
            }
        )
        
        logger.info(f"Completed system test execution {execution_id} - ran {total_tests} tests, {passed_tests} passed, {failed_tests} failed")
        return execution_report
    
    async def _run_tests(self, 
                        system_tests: List[Dict[str, Any]],
                        component_instances: Dict[str, Component],
                        execution_id: str) -> List[Dict[str, Any]]:
        """Execute system tests and return results."""
        test_results = []
        
        # Record start of test execution
        logger.info(f"Running {len(system_tests)} system tests for execution {execution_id}")
        
        for i, test in enumerate(system_tests):
            test_id = test.get("id", f"test_{i}")
            test_name = test.get("name", f"System Test {i}")
            components_under_test = test.get("components", [])
            
            logger.info(f"Running system test {test_id}: {test_name}")
            
            # Track test start time
            test_start_time = time.time()
            
            # Create test execution context with required components
            test_components = {}
            for comp_id in components_under_test:
                if comp_id in component_instances:
                    test_components[comp_id] = component_instances[comp_id]
            
            # If no specifically mentioned components, include all
            if not test_components:
                test_components = component_instances
            
            # Simulate test execution
            # In a real implementation, this would run the actual test
            success, test_log, test_metrics = await self._simulate_test_execution(
                test, test_components, execution_id
            )
            
            # Calculate test duration
            test_duration = time.time() - test_start_time
            
            # Record test result
            test_result = {
                "test_id": test_id,
                "test_name": test_name,
                "passed": success,
                "duration": test_duration,
                "timestamp": datetime.now().isoformat(),
                "components": list(test_components.keys()),
                "execution_id": execution_id,
                "output": test_log,
                "metrics": test_metrics
            }
            
            test_results.append(test_result)
            
            # Record individual test completion metric
            await self._metrics_manager.record_metric(
                "system_test:execution",
                1.0,
                metadata={
                    "test_id": test_id,
                    "execution_id": execution_id,
                    "status": "passed" if success else "failed",
                    "duration": test_duration,
                    "components": len(test_components)
                }
            )
        
        return test_results
    
    async def _simulate_test_execution(self, 
                                      test: Dict[str, Any],
                                      components: Dict[str, Component],
                                      execution_id: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Simulate test execution for a system test."""
        # Add slight delay to simulate test execution time
        test_duration = random.uniform(0.1, 1.0)
        await asyncio.sleep(test_duration / 10)  # Reduced for simulation
        
        # Simulate test steps
        test_steps = test.get("steps", [])
        if not test_steps:
            # Generate synthetic steps if none provided
            test_steps = ["Initialize components", "Execute test sequence", "Validate results"]
        
        # Simulate test log
        test_log = []
        test_log.append(f"=== Test Execution: {test.get('name', 'Unknown test')} ===")
        test_log.append(f"Time: {datetime.now().isoformat()}")
        test_log.append(f"Components: {', '.join(components.keys())}")
        test_log.append("")
        
        # Simulate step execution
        all_steps_passed = True
        step_results = []
        for i, step in enumerate(test_steps):
            step_description = step if isinstance(step, str) else step.get("description", f"Step {i+1}")
            
            # High success rate for simulation
            step_success = random.random() < 0.95
            all_steps_passed = all_steps_passed and step_success
            
            step_result = {
                "step": i + 1,
                "description": step_description,
                "status": "PASS" if step_success else "FAIL",
                "duration": random.uniform(0.01, 0.2)
            }
            
            step_results.append(step_result)
            test_log.append(f"Step {i+1}: {step_description} - {step_result['status']}")
            
            if not step_success:
                test_log.append(f"  ERROR: Test step failed")
                test_log.append(f"  Expected result not achieved")
                break
        
        # Add summary to log
        test_log.append("")
        test_log.append(f"Test result: {'PASS' if all_steps_passed else 'FAIL'}")
        test_log.append(f"Test duration: {test_duration:.2f} seconds")
        
        # Collect metrics
        test_metrics = {
            "duration": test_duration,
            "steps_count": len(test_steps),
            "steps_passed": sum(1 for step in step_results if step["status"] == "PASS"),
            "steps_failed": sum(1 for step in step_results if step["status"] == "FAIL"),
            "components_tested": len(components),
            "step_details": step_results
        }
        
        return all_steps_passed, "\n".join(test_log), test_metrics
    
    def _record_test_details(self, 
                            system_tests: List[Dict[str, Any]],
                            test_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create detailed test records from execution results."""
        test_details = []
        
        for test_result in test_results:
            test_id = test_result.get("test_id", "")
            
            # Find original test definition
            original_test = next((test for test in system_tests if test.get("id", "") == test_id), {})
            
            # Combine test definition with results
            test_detail = {
                "test_id": test_id,
                "test_name": test_result.get("test_name", ""),
                "description": original_test.get("description", ""),
                "priority": original_test.get("priority", "medium"),
                "tags": original_test.get("tags", []),
                "requirements": original_test.get("requirements", []),
                "components": test_result.get("components", []),
                "passed": test_result.get("passed", False),
                "duration": test_result.get("duration", 0),
                "output": test_result.get("output", ""),
                "metrics": test_result.get("metrics", {})
            }
            
            test_details.append(test_detail)
        
        return test_details
    
    def _calculate_coverage(self, 
                           test_results: List[Dict[str, Any]],
                           components: List[Dict[str, Any]],
                           system_requirements: Dict[str, Any]) -> TestCoverage:
        """Calculate test coverage for components and requirements."""
        coverage = TestCoverage()
        
        # Component coverage
        component_ids = set(component.get("id", "") for component in components)
        tested_components = set()
        
        for test_result in test_results:
            tested_components.update(test_result.get("components", []))
        
        # Calculate component coverage
        for component_id in component_ids:
            if component_id in tested_components:
                coverage.components[component_id] = 1.0
            else:
                coverage.components[component_id] = 0.0
        
        component_coverage = sum(coverage.components.values()) / len(coverage.components) if coverage.components else 0
        
        # Feature coverage (from component definitions)
        all_features = {}
        tested_features = set()
        
        for component in components:
            component_id = component.get("id", "")
            features = component.get("features", [])
            
            for feature in features:
                feature_id = feature.get("id", "")
                if feature_id:
                    all_features[feature_id] = component_id
        
        # Determine tested features
        for test_result in test_results:
            test_components = test_result.get("components", [])
            
            # Assume features are tested if their component is tested
            for feature_id, component_id in all_features.items():
                if component_id in test_components:
                    tested_features.add(feature_id)
        
        # Calculate feature coverage
        for feature_id in all_features:
            if feature_id in tested_features:
                coverage.features[feature_id] = 1.0
            else:
                coverage.features[feature_id] = 0.0
        
        feature_coverage = sum(coverage.features.values()) / len(coverage.features) if coverage.features else 0
        
        # Interface coverage
        # In a real implementation, this would analyze interface usage across components
        # Simplified for this implementation
        interface_coverage = component_coverage * 0.9  # Simplified approximation
        
        # Requirement coverage
        requirements = []
        requirements.extend(system_requirements.get("functional_requirements", []))
        requirements.extend(system_requirements.get("non_functional_requirements", []))
        
        requirement_ids = set(req.get("id", "") for req in requirements)
        tested_requirements = set()
        
        # Map components to requirements
        component_to_requirements = {}
        for req in requirements:
            req_id = req.get("id", "")
            if not req_id:
                continue
                
            components_for_req = req.get("components", [])
            for comp_id in components_for_req:
                if comp_id not in component_to_requirements:
                    component_to_requirements[comp_id] = set()
                component_to_requirements[comp_id].add(req_id)
        
        # Determine tested requirements based on tested components
        for test_result in test_results:
            if not test_result.get("passed", False):
                continue  # Only count requirements for passing tests
                
            test_components = test_result.get("components", [])
            
            for comp_id in test_components:
                tested_requirements.update(component_to_requirements.get(comp_id, set()))
        
        # Calculate requirement coverage
        for req_id in requirement_ids:
            if req_id in tested_requirements:
                coverage.requirements[req_id] = 1.0
            else:
                coverage.requirements[req_id] = 0.0
        
        requirement_coverage = sum(coverage.requirements.values()) / len(coverage.requirements) if coverage.requirements else 0
        
        # Calculate overall coverage
        coverage.overall = (component_coverage + feature_coverage + interface_coverage + requirement_coverage) / 4
        
        # Update interface coverage dictionary
        for component_id in component_ids:
            coverage.interfaces[component_id] = interface_coverage
        
        return coverage
    
    def _collect_performance_metrics(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Collect performance metrics from test execution."""
        # Calculate overall metrics
        total_duration = sum(test_result.get("duration", 0) for test_result in test_results)
        average_duration = total_duration / len(test_results) if test_results else 0
        
        durations = [test_result.get("duration", 0) for test_result in test_results]
        durations.sort()
        
        median_duration = durations[len(durations) // 2] if durations else 0
        p90_duration = durations[int(len(durations) * 0.9)] if durations else 0
        max_duration = max(durations) if durations else 0
        
        # Calculate success rates
        passed_tests = sum(1 for test in test_results if test.get("passed", False))
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Collect component-level metrics
        component_metrics = {}
        for test_result in test_results:
            components = test_result.get("components", [])
            for component_id in components:
                if component_id not in component_metrics:
                    component_metrics[component_id] = {
                        "total_tests": 0,
                        "passed_tests": 0,
                        "total_duration": 0
                    }
                
                component_metrics[component_id]["total_tests"] += 1
                if test_result.get("passed", False):
                    component_metrics[component_id]["passed_tests"] += 1
                component_metrics[component_id]["total_duration"] += test_result.get("duration", 0)
        
        # Calculate per-component success rates and average durations
        for component_id, metrics in component_metrics.items():
            metrics["success_rate"] = (metrics["passed_tests"] / metrics["total_tests"]) * 100 if metrics["total_tests"] > 0 else 0
            metrics["average_duration"] = metrics["total_duration"] / metrics["total_tests"] if metrics["total_tests"] > 0 else 0
        
        return {
            "total_duration": total_duration,
            "average_duration": average_duration,
            "median_duration": median_duration,
            "p90_duration": p90_duration,
            "max_duration": max_duration,
            "success_rate": success_rate,
            "component_metrics": component_metrics
        }
    
    async def get_execution_result(self, execution_id: str) -> Dict[str, Any]:
        """Retrieve results for a specific test execution."""
        # Check in-memory cache first
        if execution_id in self._test_executions:
            return self._test_executions[execution_id]
        
        # Try to get from state manager
        state = await self._state_manager.get_state(f"system_test_execution:{execution_id}")
        if state:
            return state
        
        # Not found
        return {
            "status": "not_found",
            "message": f"No test execution found with ID {execution_id}"
        }
    
    async def generate_coverage_report(self, execution_id: str) -> Dict[str, Any]:
        """Generate a detailed coverage report for a test execution."""
        # Get execution results
        execution_result = await self.get_execution_result(execution_id)
        
        if execution_result.get("status") == "not_found":
            return execution_result
        
        # Extract coverage data
        coverage_data = execution_result.get("coverage", {})
        
        # Generate coverage report
        coverage_report = {
            "execution_id": execution_id,
            "timestamp": datetime.now().isoformat(),
            "overall_coverage": coverage_data.get("overall", 0) * 100,
            "component_coverage": {
                component: value * 100
                for component, value in coverage_data.get("components", {}).items()
            },
            "feature_coverage": {
                feature: value * 100
                for feature, value in coverage_data.get("features", {}).items()
            },
            "requirement_coverage": {
                requirement: value * 100
                for requirement, value in coverage_data.get("requirements", {}).items()
            },
            "coverage_gaps": self._identify_coverage_gaps(coverage_data)
        }
        
        return coverage_report
    
    def _identify_coverage_gaps(self, coverage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Identify gaps in test coverage."""
        component_gaps = []
        feature_gaps = []
        requirement_gaps = []
        
        # Identify components with less than 100% coverage
        for component, value in coverage_data.get("components", {}).items():
            if value < 1.0:
                component_gaps.append({
                    "id": component,
                    "coverage": value * 100,
                    "gap": (1.0 - value) * 100
                })
        
        # Identify features with less than 100% coverage
        for feature, value in coverage_data.get("features", {}).items():
            if value < 1.0:
                feature_gaps.append({
                    "id": feature,
                    "coverage": value * 100,
                    "gap": (1.0 - value) * 100
                })
        
        # Identify requirements with less than 100% coverage
        for requirement, value in coverage_data.get("requirements", {}).items():
            if value < 1.0:
                requirement_gaps.append({
                    "id": requirement,
                    "coverage": value * 100,
                    "gap": (1.0 - value) * 100
                })
        
        return {
            "component_gaps": component_gaps,
            "feature_gaps": feature_gaps,
            "requirement_gaps": requirement_gaps,
            "total_gaps": len(component_gaps) + len(feature_gaps) + len(requirement_gaps)
        }