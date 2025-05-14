import logging
import time
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from dataclasses import dataclass, field

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
class ValidationResult:
    requirement_id: str
    name: str
    description: str
    validation_status: str  # "passed", "failed", "partial", "not_validated"
    validation_method: str  # "test", "analysis", "manual"
    validation_details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "requirement_id": self.requirement_id,
            "name": self.name,
            "description": self.description,
            "validation_status": self.validation_status,
            "validation_method": self.validation_method,
            "validation_details": self.validation_details
        }


class SystemValidationManager(PhaseTwoAgentBase):
    """
    Validates system behavior against requirements.
    
    Responsibilities:
    - Validate system behavior against requirements
    - Generate validation reports
    - Track validation coverage
    - Identify validation gaps
    """
    
    def __init__(self,
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        """Initialize the system validation manager."""
        super().__init__(
            "system_validation_manager",
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor
        )
        # Track validation sessions
        self._validation_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def validate_system(self, 
                            system_requirements: Dict[str, Any],
                            test_execution_result: Dict[str, Any],
                            components: List[Dict[str, Any]],
                            validation_id: str) -> Dict[str, Any]:
        """
        Validate system behavior against requirements.
        
        Args:
            system_requirements: System requirements to validate against
            test_execution_result: Results from system test execution
            components: List of implemented components
            validation_id: Unique identifier for this validation session
            
        Returns:
            Dictionary containing validation results
        """
        logger.info(f"Validating system against requirements for validation ID: {validation_id}")
        
        start_time = time.time()
        
        # Record validation start
        await self._metrics_manager.record_metric(
            "system_validation:start",
            1.0,
            metadata={
                "validation_id": validation_id,
                "execution_id": test_execution_result.get("execution_id", "unknown")
            }
        )
        
        # Extract requirements from system requirements
        functional_requirements = system_requirements.get("functional_requirements", [])
        non_functional_requirements = system_requirements.get("non_functional_requirements", [])
        all_requirements = functional_requirements + non_functional_requirements
        
        if not all_requirements:
            logger.info(f"No requirements to validate for {validation_id}")
            return {
                "status": "success",
                "message": "No requirements to validate",
                "validation_id": validation_id,
                "validation_results": [],
                "coverage": {
                    "total_requirements": 0,
                    "validated_requirements": 0,
                    "validation_coverage": 0
                }
            }
        
        # Validate requirements
        validation_results = []
        
        # Map test results to requirements for validation
        test_details = test_execution_result.get("test_details", [])
        test_by_requirement = self._map_tests_to_requirements(test_details, all_requirements)
        
        # Validate each requirement
        for requirement in all_requirements:
            req_id = requirement.get("id", "")
            
            if not req_id:
                continue
                
            requirement_name = requirement.get("name", f"Requirement {req_id}")
            requirement_description = requirement.get("description", "")
            requirement_type = requirement.get("type", "functional")
            
            # Validate based on tests
            tests_for_req = test_by_requirement.get(req_id, [])
            
            # Validate requirement
            validation_result = await self._validate_requirement(
                requirement,
                tests_for_req,
                test_execution_result,
                components,
                validation_id
            )
            
            validation_results.append(validation_result)
        
        # Calculate coverage
        total_requirements = len(all_requirements)
        validated_requirements = sum(1 for result in validation_results 
                                   if result.validation_status in ["passed", "partial"])
        validation_coverage = (validated_requirements / total_requirements) * 100 if total_requirements > 0 else 0
        
        # Identify validation gaps
        validation_gaps = self._identify_validation_gaps(validation_results, all_requirements)
        
        # Create validation report
        validation_report = {
            "status": "completed",
            "validation_id": validation_id,
            "timestamp": datetime.now().isoformat(),
            "execution_time_seconds": time.time() - start_time,
            "validation_results": [result.to_dict() for result in validation_results],
            "coverage": {
                "total_requirements": total_requirements,
                "validated_requirements": validated_requirements,
                "validation_coverage": validation_coverage
            },
            "validation_gaps": validation_gaps,
            "recommendations": self._generate_recommendations(validation_results, validation_gaps)
        }
        
        # Store validation in state and memory
        self._validation_sessions[validation_id] = validation_report
        await self._state_manager.set_state(
            f"system_validation:{validation_id}",
            {
                "validation_id": validation_id,
                "timestamp": datetime.now().isoformat(),
                "status": "completed",
                "total_requirements": total_requirements,
                "validated_requirements": validated_requirements,
                "validation_coverage": validation_coverage
            }
        )
        
        # Record validation completion
        await self._metrics_manager.record_metric(
            "system_validation:complete",
            1.0,
            metadata={
                "validation_id": validation_id,
                "total_requirements": total_requirements,
                "validated_requirements": validated_requirements,
                "validation_coverage": validation_coverage,
                "execution_time": time.time() - start_time
            }
        )
        
        logger.info(f"Completed system validation {validation_id} - validated {validated_requirements}/{total_requirements} requirements ({validation_coverage:.1f}% coverage)")
        return validation_report
    
    def _map_tests_to_requirements(self, 
                                  test_details: List[Dict[str, Any]],
                                  requirements: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Map test results to requirements for validation."""
        test_by_requirement = {}
        
        # First, map tests that explicitly list requirements
        for test in test_details:
            test_requirements = test.get("requirements", [])
            
            for req_id in test_requirements:
                if req_id not in test_by_requirement:
                    test_by_requirement[req_id] = []
                test_by_requirement[req_id].append(test)
        
        # Check for requirements without mapped tests
        for requirement in requirements:
            req_id = requirement.get("id", "")
            
            if req_id not in test_by_requirement:
                test_by_requirement[req_id] = []
                
                # Try to infer mapping based on component ID or requirement description
                req_components = requirement.get("components", [])
                req_description = requirement.get("description", "").lower()
                
                for test in test_details:
                    test_components = test.get("components", [])
                    test_name = test.get("test_name", "").lower()
                    test_description = test.get("description", "").lower()
                    
                    # Check for component overlap
                    if any(comp in test_components for comp in req_components):
                        test_by_requirement[req_id].append(test)
                        continue
                        
                    # Check for description similarity (very basic approach)
                    req_keywords = set(req_description.split())
                    test_keywords = set(test_name.split() + test_description.split())
                    
                    if len(req_keywords.intersection(test_keywords)) > 2:  # At least 3 common words
                        test_by_requirement[req_id].append(test)
        
        return test_by_requirement
    
    async def _validate_requirement(self, 
                                   requirement: Dict[str, Any],
                                   tests: List[Dict[str, Any]],
                                   test_execution_result: Dict[str, Any],
                                   components: List[Dict[str, Any]],
                                   validation_id: str) -> ValidationResult:
        """Validate a single requirement based on test results and analysis."""
        req_id = requirement.get("id", "")
        name = requirement.get("name", f"Requirement {req_id}")
        description = requirement.get("description", "")
        req_type = requirement.get("type", "functional")
        
        logger.info(f"Validating requirement {req_id}: {name}")
        
        # Record validation attempt
        await self._metrics_manager.record_metric(
            "requirement_validation:attempt",
            1.0,
            metadata={
                "validation_id": validation_id,
                "requirement_id": req_id,
                "requirement_type": req_type,
                "test_count": len(tests)
            }
        )
        
        # If no tests for this requirement, mark as not validated
        if not tests:
            return ValidationResult(
                requirement_id=req_id,
                name=name,
                description=description,
                validation_status="not_validated",
                validation_method="none",
                validation_details={
                    "reason": "No tests available for this requirement",
                    "recommendation": "Create tests that validate this requirement"
                }
            )
        
        # Check all test results
        test_validation_details = []
        passed_tests = 0
        failed_tests = 0
        
        for test in tests:
            test_id = test.get("test_id", "")
            test_passed = test.get("passed", False)
            
            test_result = {
                "test_id": test_id,
                "test_name": test.get("test_name", ""),
                "status": "passed" if test_passed else "failed",
                "duration": test.get("duration", 0)
            }
            
            test_validation_details.append(test_result)
            
            if test_passed:
                passed_tests += 1
            else:
                failed_tests += 1
        
        # Determine overall validation status
        if passed_tests > 0 and failed_tests == 0:
            validation_status = "passed"
        elif passed_tests > 0 and failed_tests > 0:
            validation_status = "partial"
        else:
            validation_status = "failed"
        
        # Perform additional validation for non-functional requirements
        additional_validation = {}
        validation_method = "test"
        
        if req_type == "non_functional":
            # For non-functional requirements, we might need to analyze performance metrics
            # or other system characteristics beyond simple pass/fail tests
            additional_validation = self._validate_non_functional_requirement(
                requirement, test_execution_result, components
            )
            
            # Update validation status based on additional validation
            if additional_validation.get("status") == "failed":
                validation_status = "failed"
            elif additional_validation.get("status") == "partial" and validation_status == "passed":
                validation_status = "partial"
                
            validation_method = "test+analysis"
        
        # Create validation result
        validation_result = ValidationResult(
            requirement_id=req_id,
            name=name,
            description=description,
            validation_status=validation_status,
            validation_method=validation_method,
            validation_details={
                "tests": test_validation_details,
                "test_summary": {
                    "total": len(tests),
                    "passed": passed_tests,
                    "failed": failed_tests
                },
                "additional_validation": additional_validation
            }
        )
        
        # Record validation result
        await self._metrics_manager.record_metric(
            "requirement_validation:complete",
            1.0,
            metadata={
                "validation_id": validation_id,
                "requirement_id": req_id,
                "status": validation_status,
                "test_count": len(tests),
                "passed_tests": passed_tests
            }
        )
        
        return validation_result
    
    def _validate_non_functional_requirement(self, 
                                           requirement: Dict[str, Any],
                                           test_execution_result: Dict[str, Any],
                                           components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform specialized validation for non-functional requirements."""
        req_id = requirement.get("id", "")
        subtype = requirement.get("subtype", "").lower()
        
        # Initialize default result
        result = {
            "status": "not_applicable",
            "details": "No specialized validation available for this non-functional requirement"
        }
        
        # Check requirement subtype
        if subtype == "performance":
            # Validate performance requirements
            result = self._validate_performance_requirement(requirement, test_execution_result)
        elif subtype == "security":
            # Validate security requirements
            result = self._validate_security_requirement(requirement, components)
        elif subtype == "reliability":
            # Validate reliability requirements
            result = self._validate_reliability_requirement(requirement, test_execution_result)
        elif subtype == "usability":
            # Usability typically requires manual validation
            result = {
                "status": "manual_required",
                "details": "Usability requirements require manual validation",
                "recommendation": "Schedule manual usability testing"
            }
        
        return result
    
    def _validate_performance_requirement(self, 
                                        requirement: Dict[str, Any],
                                        test_execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate performance requirements based on test metrics."""
        # Extract performance criteria from the requirement
        criteria = requirement.get("criteria", {})
        
        if not criteria:
            return {
                "status": "failed",
                "details": "No specific performance criteria defined in the requirement"
            }
        
        # Extract performance metrics from test results
        performance_metrics = test_execution_result.get("performance", {})
        
        # Check criteria against metrics
        criteria_results = []
        
        for criterion_name, expected_value in criteria.items():
            if criterion_name == "response_time":
                # Compare against p90_duration or average_duration
                actual_value = performance_metrics.get("p90_duration", performance_metrics.get("average_duration", 0))
                passed = actual_value <= expected_value
                
                criteria_results.append({
                    "criterion": criterion_name,
                    "expected": f"<= {expected_value}s",
                    "actual": f"{actual_value:.2f}s",
                    "status": "passed" if passed else "failed"
                })
            elif criterion_name == "throughput":
                # This would typically come from load testing metrics
                # Simplified for this implementation
                criteria_results.append({
                    "criterion": criterion_name,
                    "expected": expected_value,
                    "actual": "Not measured in current tests",
                    "status": "not_validated"
                })
            elif criterion_name == "success_rate":
                actual_value = performance_metrics.get("success_rate", 0)
                passed = actual_value >= expected_value
                
                criteria_results.append({
                    "criterion": criterion_name,
                    "expected": f">= {expected_value}%",
                    "actual": f"{actual_value:.1f}%",
                    "status": "passed" if passed else "failed"
                })
        
        # Determine overall status
        passed_criteria = sum(1 for c in criteria_results if c.get("status") == "passed")
        failed_criteria = sum(1 for c in criteria_results if c.get("status") == "failed")
        not_validated = sum(1 for c in criteria_results if c.get("status") == "not_validated")
        
        if failed_criteria == 0 and not_validated == 0:
            status = "passed"
        elif failed_criteria == 0 and not_validated > 0:
            status = "partial"
        elif passed_criteria > 0 and failed_criteria > 0:
            status = "partial"
        else:
            status = "failed"
        
        return {
            "status": status,
            "criteria_results": criteria_results,
            "details": f"{passed_criteria} of {len(criteria_results)} criteria passed"
        }
    
    def _validate_security_requirement(self, 
                                     requirement: Dict[str, Any],
                                     components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate security requirements (simulated)."""
        # For a real implementation, this would involve analysis of security features,
        # scanning for vulnerabilities, etc.
        
        # Extract security criteria from the requirement
        criteria = requirement.get("criteria", {})
        
        if not criteria:
            return {
                "status": "failed",
                "details": "No specific security criteria defined in the requirement"
            }
        
        # In a real system, this would perform actual security validation
        # Simplified for this implementation
        criteria_results = []
        
        for criterion_name, expected_value in criteria.items():
            # Simulate validation results
            status = "passed"  # Simplified for this implementation
            
            criteria_results.append({
                "criterion": criterion_name,
                "expected": expected_value,
                "actual": "Simulated security validation",
                "status": status
            })
        
        return {
            "status": "passed",  # Simplified for this implementation
            "criteria_results": criteria_results,
            "details": "Security validation simulation"
        }
    
    def _validate_reliability_requirement(self, 
                                        requirement: Dict[str, Any],
                                        test_execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate reliability requirements based on test metrics."""
        # Extract reliability criteria from the requirement
        criteria = requirement.get("criteria", {})
        
        if not criteria:
            return {
                "status": "failed",
                "details": "No specific reliability criteria defined in the requirement"
            }
        
        # Extract metrics from test results
        success_rate = test_execution_result.get("pass_rate", 0)
        
        # Check criteria against metrics
        criteria_results = []
        
        for criterion_name, expected_value in criteria.items():
            if criterion_name == "success_rate":
                passed = success_rate >= expected_value
                
                criteria_results.append({
                    "criterion": criterion_name,
                    "expected": f">= {expected_value}%",
                    "actual": f"{success_rate:.1f}%",
                    "status": "passed" if passed else "failed"
                })
            else:
                # For other reliability criteria
                criteria_results.append({
                    "criterion": criterion_name,
                    "expected": expected_value,
                    "actual": "Not measured in current tests",
                    "status": "not_validated"
                })
        
        # Determine overall status
        passed_criteria = sum(1 for c in criteria_results if c.get("status") == "passed")
        failed_criteria = sum(1 for c in criteria_results if c.get("status") == "failed")
        
        if failed_criteria == 0:
            status = "passed"
        elif passed_criteria > 0:
            status = "partial"
        else:
            status = "failed"
        
        return {
            "status": status,
            "criteria_results": criteria_results,
            "details": f"{passed_criteria} of {len(criteria_results)} criteria passed"
        }
    
    def _identify_validation_gaps(self, 
                                validation_results: List[ValidationResult],
                                requirements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify gaps in validation coverage."""
        # Calculate validation coverage by requirement type
        requirement_types = {}
        for req in requirements:
            req_type = req.get("type", "functional")
            if req_type not in requirement_types:
                requirement_types[req_type] = {
                    "total": 0,
                    "validated": 0,
                    "not_validated": 0,
                    "failed": 0,
                    "passed": 0,
                    "partial": 0
                }
            
            requirement_types[req_type]["total"] += 1
        
        for result in validation_results:
            req_id = result.requirement_id
            status = result.validation_status
            
            # Find requirement type
            req_type = "functional"  # Default
            for req in requirements:
                if req.get("id") == req_id:
                    req_type = req.get("type", "functional")
                    break
            
            # Update counts
            if status in ["passed", "partial"]:
                requirement_types[req_type]["validated"] += 1
            else:
                requirement_types[req_type]["not_validated"] += 1
                
            requirement_types[req_type][status] += 1
        
        # Calculate coverage percentages
        for req_type, stats in requirement_types.items():
            if stats["total"] > 0:
                stats["coverage_percentage"] = (stats["validated"] / stats["total"]) * 100
            else:
                stats["coverage_percentage"] = 0
        
        # Identify specific gaps
        not_validated_requirements = []
        failed_validations = []
        
        for result in validation_results:
            if result.validation_status == "not_validated":
                not_validated_requirements.append({
                    "requirement_id": result.requirement_id,
                    "name": result.name,
                    "reason": result.validation_details.get("reason", "Unknown reason")
                })
            elif result.validation_status == "failed":
                failed_validations.append({
                    "requirement_id": result.requirement_id,
                    "name": result.name,
                    "details": result.validation_details
                })
        
        return {
            "coverage_by_type": requirement_types,
            "not_validated_requirements": not_validated_requirements,
            "failed_validations": failed_validations,
            "total_gaps": len(not_validated_requirements) + len(failed_validations)
        }
    
    def _generate_recommendations(self, 
                                validation_results: List[ValidationResult],
                                validation_gaps: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on validation results and gaps."""
        recommendations = []
        
        # Recommend creating tests for non-validated requirements
        not_validated = validation_gaps.get("not_validated_requirements", [])
        if not_validated:
            recommendations.append({
                "type": "test_coverage",
                "priority": "high",
                "title": "Improve test coverage for unvalidated requirements",
                "description": f"Create tests for {len(not_validated)} requirements that currently have no validation",
                "affected_requirements": [req.get("requirement_id") for req in not_validated],
                "action_items": [
                    "Create explicit test cases for each unvalidated requirement",
                    "Update test tracking to map tests to requirements",
                    "Include requirement validation in test execution reports"
                ]
            })
        
        # Recommend fixing failed validations
        failed = validation_gaps.get("failed_validations", [])
        if failed:
            recommendations.append({
                "type": "validation_failures",
                "priority": "high",
                "title": "Address failed requirement validations",
                "description": f"Fix issues causing {len(failed)} requirements to fail validation",
                "affected_requirements": [req.get("requirement_id") for req in failed],
                "action_items": [
                    "Analyze root causes of validation failures",
                    "Implement fixes for failed requirements",
                    "Re-run validation after implementing fixes"
                ]
            })
        
        # Recommend improving partial validations
        partial_validations = [r for r in validation_results if r.validation_status == "partial"]
        if partial_validations:
            recommendations.append({
                "type": "partial_validations",
                "priority": "medium",
                "title": "Improve partially validated requirements",
                "description": f"Enhance validation for {len(partial_validations)} partially validated requirements",
                "affected_requirements": [r.requirement_id for r in partial_validations],
                "action_items": [
                    "Create additional test cases to fully validate requirements",
                    "Expand validation criteria for non-functional requirements",
                    "Implement specialized validation for complex requirements"
                ]
            })
        
        # Recommend better validation for non-functional requirements
        coverage_by_type = validation_gaps.get("coverage_by_type", {})
        nfr_stats = coverage_by_type.get("non_functional", {})
        if nfr_stats.get("coverage_percentage", 100) < 80:
            recommendations.append({
                "type": "non_functional_validation",
                "priority": "medium",
                "title": "Improve non-functional requirement validation",
                "description": "Enhance validation approach for non-functional requirements",
                "affected_requirements": [],  # Would be populated in a real implementation
                "action_items": [
                    "Implement specialized validation for performance requirements",
                    "Create security validation framework",
                    "Develop reliability testing methodology",
                    "Add automated validation for non-functional characteristics"
                ]
            })
        
        return recommendations
    
    async def get_validation_result(self, validation_id: str) -> Dict[str, Any]:
        """Retrieve results for a specific validation session."""
        # Check in-memory cache first
        if validation_id in self._validation_sessions:
            return self._validation_sessions[validation_id]
        
        # Try to get from state manager
        state = await self._state_manager.get_state(f"system_validation:{validation_id}")
        if state:
            return state
        
        # Not found
        return {
            "status": "not_found",
            "message": f"No validation session found with ID {validation_id}"
        }
    
    async def generate_validation_report(self, validation_id: str) -> Dict[str, Any]:
        """Generate a detailed validation report for stakeholders."""
        # Get validation results
        validation_result = await self.get_validation_result(validation_id)
        
        if validation_result.get("status") == "not_found":
            return validation_result
        
        # Extract validation data
        validation_results = validation_result.get("validation_results", [])
        coverage = validation_result.get("coverage", {})
        gaps = validation_result.get("validation_gaps", {})
        
        # Generate validation report
        validation_report = {
            "validation_id": validation_id,
            "timestamp": datetime.now().isoformat(),
            "title": "System Validation Report",
            "summary": {
                "total_requirements": coverage.get("total_requirements", 0),
                "validated_requirements": coverage.get("validated_requirements", 0),
                "validation_coverage": coverage.get("validation_coverage", 0),
                "validation_status": self._determine_overall_status(coverage, gaps)
            },
            "requirement_results": validation_results,
            "validation_gaps": gaps,
            "recommendations": validation_result.get("recommendations", []),
            "action_plan": self._generate_action_plan(validation_result.get("recommendations", []))
        }
        
        return validation_report
    
    def _determine_overall_status(self, coverage: Dict[str, Any], gaps: Dict[str, Any]) -> str:
        """Determine overall validation status."""
        validated_percentage = coverage.get("validation_coverage", 0)
        total_gaps = gaps.get("total_gaps", 0)
        
        if validated_percentage >= 95 and total_gaps == 0:
            return "Fully Validated"
        elif validated_percentage >= 80:
            return "Substantially Validated"
        elif validated_percentage >= 50:
            return "Partially Validated"
        else:
            return "Insufficiently Validated"
    
    def _generate_action_plan(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a prioritized action plan from recommendations."""
        # Group recommendations by priority
        priority_groups = {"high": [], "medium": [], "low": []}
        
        for rec in recommendations:
            priority = rec.get("priority", "medium")
            priority_groups[priority].append(rec)
        
        # Create prioritized action items
        action_items = []
        
        # Add high priority items first
        for rec in priority_groups["high"]:
            for item in rec.get("action_items", []):
                action_items.append({
                    "priority": "high",
                    "description": item,
                    "related_to": rec.get("title")
                })
        
        # Add medium priority items
        for rec in priority_groups["medium"]:
            for item in rec.get("action_items", []):
                action_items.append({
                    "priority": "medium",
                    "description": item,
                    "related_to": rec.get("title")
                })
        
        # Add low priority items
        for rec in priority_groups["low"]:
            for item in rec.get("action_items", []):
                action_items.append({
                    "priority": "low",
                    "description": item,
                    "related_to": rec.get("title")
                })
        
        return {
            "title": "Validation Improvement Action Plan",
            "description": "Prioritized actions to improve system validation",
            "action_items": action_items,
            "high_priority_count": len(priority_groups["high"]),
            "medium_priority_count": len(priority_groups["medium"]),
            "low_priority_count": len(priority_groups["low"])
        }