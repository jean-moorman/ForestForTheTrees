import logging
import time
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from collections import Counter
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
class FailurePattern:
    pattern_id: str
    pattern_name: str
    description: str
    frequency: int = 0
    affected_components: Set[str] = field(default_factory=set)
    affected_tests: Set[str] = field(default_factory=set)
    root_causes: List[Dict[str, Any]] = field(default_factory=list)
    priority: str = "medium"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "pattern_id": self.pattern_id,
            "pattern_name": self.pattern_name,
            "description": self.description,
            "frequency": self.frequency,
            "affected_components": list(self.affected_components),
            "affected_tests": list(self.affected_tests),
            "root_causes": self.root_causes,
            "priority": self.priority
        }


class SystemTestAnalysisAgent(PhaseTwoAgentBase):
    """
    Analyzes system test failures from integrated components.
    
    Responsibilities:
    - Identify patterns in failure reports
    - Classify failures by root cause
    - Generate detailed analysis reports
    """
    
    def __init__(self,
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        """Initialize the system test analysis agent."""
        super().__init__(
            "system_test_analysis_agent",
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor
        )
        self._failure_patterns: Dict[str, FailurePattern] = {}
        
    async def analyze_test_failures(self, 
                                   test_results: Dict[str, Any],
                                   components: List[Dict[str, Any]],
                                   analysis_id: str) -> Dict[str, Any]:
        """
        Analyze system test failures to identify patterns and root causes.
        
        Args:
            test_results: Results from system test execution
            components: List of implemented components
            analysis_id: Unique identifier for this analysis
            
        Returns:
            Dictionary containing analysis results
        """
        logger.info(f"Analyzing system test failures for analysis ID: {analysis_id}")
        
        start_time = time.time()
        
        # Record analysis start
        await self._metrics_manager.record_metric(
            "system_test_analysis:start",
            1.0,
            metadata={
                "analysis_id": analysis_id,
                "total_tests": test_results.get("total_tests", 0),
                "failed_tests": test_results.get("failed_tests", 0)
            }
        )
        
        # Extract failed tests
        failed_tests = [test for test in test_results.get("test_details", []) 
                        if not test.get("passed", False)]
        
        if not failed_tests:
            logger.info(f"No failed tests to analyze for {analysis_id}")
            return {
                "status": "success",
                "message": "No failed tests to analyze",
                "analysis_id": analysis_id,
                "patterns": [],
                "statistics": {
                    "total_tests": test_results.get("total_tests", 0),
                    "failed_tests": 0
                }
            }
        
        # Analyze component dependencies for test correlation
        component_mapping = {component.get("id", ""): component for component in components}
        
        # Identify components involved in test failures
        affected_components = self._identify_affected_components(failed_tests, component_mapping)
        
        # Extract error patterns
        patterns = self._extract_failure_patterns(failed_tests, affected_components)
        
        # Classify failures by root cause
        classified_patterns = self._classify_by_root_cause(patterns, component_mapping)
        
        # Calculate statistics
        statistics = self._calculate_statistics(test_results, failed_tests, classified_patterns)
        
        # Create analysis report
        analysis_report = {
            "status": "success",
            "analysis_id": analysis_id,
            "timestamp": datetime.now().isoformat(),
            "execution_time_seconds": time.time() - start_time,
            "patterns": [pattern.to_dict() for pattern in classified_patterns],
            "statistics": statistics,
            "affected_components": [comp_id for comp_id, _ in affected_components],
            "recommendations": self._generate_recommendations(classified_patterns, component_mapping)
        }
        
        # Cache the analysis results
        await self._cache_manager.set(
            f"system_test_analysis:{analysis_id}",
            analysis_report,
            ttl=3600  # Cache for 1 hour
        )
        
        # Record analysis completion
        await self._metrics_manager.record_metric(
            "system_test_analysis:complete",
            1.0,
            metadata={
                "analysis_id": analysis_id,
                "patterns_found": len(classified_patterns),
                "execution_time": time.time() - start_time
            }
        )
        
        logger.info(f"Completed system test failure analysis {analysis_id} - found {len(classified_patterns)} patterns")
        return analysis_report
    
    def _identify_affected_components(self, 
                                     failed_tests: List[Dict[str, Any]],
                                     component_mapping: Dict[str, Dict[str, Any]]) -> List[Tuple[str, int]]:
        """
        Identify components affected by test failures and their frequency.
        
        Args:
            failed_tests: List of failed test details
            component_mapping: Mapping of component IDs to component data
            
        Returns:
            List of tuples with component ID and failure count, sorted by count
        """
        component_failures = Counter()
        
        for test in failed_tests:
            # Extract component IDs from test metadata if available
            test_components = test.get("components", [])
            if test_components:
                for comp_id in test_components:
                    component_failures[comp_id] += 1
            else:
                # Attempt to infer from test name/id if components not explicitly listed
                test_name = test.get("test_name", "").lower()
                for comp_id, component in component_mapping.items():
                    comp_name = component.get("name", "").lower()
                    if comp_name and comp_name in test_name:
                        component_failures[comp_id] += 1
        
        # Return sorted list of (component_id, failure_count) tuples
        return sorted(component_failures.items(), key=lambda x: x[1], reverse=True)
    
    def _extract_failure_patterns(self, 
                                 failed_tests: List[Dict[str, Any]], 
                                 affected_components: List[Tuple[str, int]]) -> List[FailurePattern]:
        """
        Extract patterns from test failures.
        
        Args:
            failed_tests: List of failed test details
            affected_components: List of components affected by failures
            
        Returns:
            List of identified failure patterns
        """
        patterns = []
        
        # Group by failure output/message
        failure_messages = Counter()
        for test in failed_tests:
            output = test.get("output", "").strip()
            if output:
                failure_messages[output] += 1
        
        # Create patterns for common failure messages
        for i, (message, count) in enumerate(failure_messages.most_common()):
            # Basic pattern detection based on error message
            pattern_name = f"Pattern #{i+1}: {message[:30]}..." if len(message) > 30 else f"Pattern #{i+1}: {message}"
            
            # Determine affected components and tests for this pattern
            affected_pattern_components = set()
            affected_pattern_tests = set()
            
            for test in failed_tests:
                if test.get("output", "").strip() == message:
                    test_id = test.get("test_id", "")
                    affected_pattern_tests.add(test_id)
                    
                    # Add components related to this test
                    test_components = test.get("components", [])
                    if test_components:
                        affected_pattern_components.update(test_components)
            
            # Create pattern
            pattern = FailurePattern(
                pattern_id=f"pattern_{int(time.time())}_{i}",
                pattern_name=pattern_name,
                description=f"Failure pattern with message: {message}",
                frequency=count,
                affected_components=affected_pattern_components,
                affected_tests=affected_pattern_tests
            )
            
            patterns.append(pattern)
        
        return patterns
    
    def _classify_by_root_cause(self, 
                               patterns: List[FailurePattern],
                               component_mapping: Dict[str, Dict[str, Any]]) -> List[FailurePattern]:
        """
        Classify failure patterns by probable root cause.
        
        Args:
            patterns: List of identified failure patterns
            component_mapping: Mapping of component IDs to component data
            
        Returns:
            List of patterns with root cause classification added
        """
        classified_patterns = []
        
        for pattern in patterns:
            # Create a copy to modify
            updated_pattern = FailurePattern(
                pattern_id=pattern.pattern_id,
                pattern_name=pattern.pattern_name,
                description=pattern.description,
                frequency=pattern.frequency,
                affected_components=pattern.affected_components.copy(),
                affected_tests=pattern.affected_tests.copy()
            )
            
            # Analyze root causes based on pattern characteristics
            root_causes = []
            
            # 1. Check for dependency issues
            dependency_issues = self._check_for_dependency_issues(pattern, component_mapping)
            if dependency_issues:
                root_causes.append(dependency_issues)
            
            # 2. Check for interface mismatches
            interface_issues = self._check_for_interface_mismatches(pattern, component_mapping)
            if interface_issues:
                root_causes.append(interface_issues)
            
            # 3. Check for implementation errors
            implementation_issues = self._check_for_implementation_errors(pattern)
            if implementation_issues:
                root_causes.append(implementation_issues)
            
            # Add root causes to the pattern
            updated_pattern.root_causes = root_causes
            
            # Set priority based on frequency and impact
            if len(updated_pattern.affected_components) > 3 or updated_pattern.frequency > 5:
                updated_pattern.priority = "high"
            elif len(updated_pattern.affected_components) <= 1 and updated_pattern.frequency <= 2:
                updated_pattern.priority = "low"
            else:
                updated_pattern.priority = "medium"
                
            classified_patterns.append(updated_pattern)
            
        return classified_patterns
    
    def _check_for_dependency_issues(self, 
                                    pattern: FailurePattern,
                                    component_mapping: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Check if the pattern indicates dependency issues between components."""
        # Simulated dependency analysis
        for comp_id in pattern.affected_components:
            component = component_mapping.get(comp_id, {})
            dependencies = component.get("dependencies", [])
            
            if dependencies:
                # This is a simplified analysis - in a real system, 
                # we would analyze the actual error messages and component interactions
                return {
                    "type": "dependency_issue",
                    "description": "Potential dependency conflict or unfulfilled dependency",
                    "impacted_component": comp_id,
                    "dependencies": dependencies,
                    "confidence": "medium"
                }
        
        return None
    
    def _check_for_interface_mismatches(self, 
                                      pattern: FailurePattern,
                                      component_mapping: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Check if the pattern indicates interface mismatches between components."""
        # Simulated interface analysis
        if len(pattern.affected_components) >= 2:
            # In a real system, we would analyze specific interface contract violations
            return {
                "type": "interface_mismatch",
                "description": "Components may have incompatible interfaces",
                "impacted_components": list(pattern.affected_components),
                "confidence": "medium"
            }
        
        return None
    
    def _check_for_implementation_errors(self, pattern: FailurePattern) -> Optional[Dict[str, Any]]:
        """Check if the pattern indicates implementation errors within components."""
        # Basic implementation error detection
        error_keywords = ["null", "undefined", "exception", "error", "failed"]
        
        # Check if any error keywords appear in the pattern description
        if any(keyword in pattern.description.lower() for keyword in error_keywords):
            return {
                "type": "implementation_error",
                "description": "Likely implementation error in component code",
                "confidence": "high"
            }
        
        return None
    
    def _calculate_statistics(self, 
                             test_results: Dict[str, Any],
                             failed_tests: List[Dict[str, Any]],
                             patterns: List[FailurePattern]) -> Dict[str, Any]:
        """Calculate statistics about the test failures and patterns."""
        total_tests = test_results.get("total_tests", 0)
        total_failed = len(failed_tests)
        
        # Calculate failure rate
        failure_rate = (total_failed / total_tests) * 100 if total_tests > 0 else 0
        
        # Count patterns by priority
        priorities = Counter()
        for pattern in patterns:
            priorities[pattern.priority] += 1
        
        # Collect affected components
        all_affected_components = set()
        for pattern in patterns:
            all_affected_components.update(pattern.affected_components)
        
        return {
            "total_tests": total_tests,
            "failed_tests": total_failed,
            "failure_rate": round(failure_rate, 2),
            "unique_failure_patterns": len(patterns),
            "affected_component_count": len(all_affected_components),
            "patterns_by_priority": {
                "high": priorities["high"],
                "medium": priorities["medium"],
                "low": priorities["low"]
            }
        }
    
    def _generate_recommendations(self, 
                                patterns: List[FailurePattern],
                                component_mapping: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate recommendations based on identified patterns."""
        recommendations = []
        
        # Generate recommendations for high priority patterns first
        high_priority_patterns = [p for p in patterns if p.priority == "high"]
        for pattern in high_priority_patterns:
            for root_cause in pattern.root_causes:
                cause_type = root_cause.get("type", "")
                
                if cause_type == "dependency_issue":
                    recommendations.append({
                        "priority": "high",
                        "description": "Review and fix component dependencies",
                        "action_items": [
                            f"Verify that dependencies for component {comp_id} are correctly implemented"
                            for comp_id in pattern.affected_components
                        ],
                        "related_pattern": pattern.pattern_id
                    })
                elif cause_type == "interface_mismatch":
                    recommendations.append({
                        "priority": "high",
                        "description": "Resolve interface compatibility issues",
                        "action_items": [
                            "Review interface contracts between components",
                            "Ensure consistent data formats across component boundaries",
                            "Update interface documentation"
                        ],
                        "related_pattern": pattern.pattern_id
                    })
                elif cause_type == "implementation_error":
                    recommendations.append({
                        "priority": "high",
                        "description": "Fix implementation errors in components",
                        "action_items": [
                            "Debug components to identify exact error locations",
                            "Update implementation to fix identified issues",
                            "Add additional error handling"
                        ],
                        "related_pattern": pattern.pattern_id
                    })
        
        # Add general recommendations based on statistics
        if len(patterns) > 3:
            recommendations.append({
                "priority": "medium",
                "description": "Improve overall test coverage",
                "action_items": [
                    "Add more specific test cases for component interactions",
                    "Enhance error reporting in tests",
                    "Add integration tests focused on component boundaries"
                ],
                "related_pattern": None
            })
        
        return recommendations