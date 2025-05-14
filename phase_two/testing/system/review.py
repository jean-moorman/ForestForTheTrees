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
class ReviewRecommendation:
    recommendation_id: str
    priority: str  # high, medium, low
    title: str
    description: str
    action_items: List[str] = field(default_factory=list)
    affected_components: List[str] = field(default_factory=list)
    related_patterns: List[str] = field(default_factory=list)
    estimated_effort: str = "medium"  # high, medium, low
    system_impact: str = "medium"  # high, medium, low
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "recommendation_id": self.recommendation_id,
            "priority": self.priority,
            "title": self.title,
            "description": self.description,
            "action_items": self.action_items,
            "affected_components": self.affected_components,
            "related_patterns": self.related_patterns,
            "estimated_effort": self.estimated_effort,
            "system_impact": self.system_impact
        }


class SystemTestReviewAgent(PhaseTwoAgentBase):
    """
    Reviews analysis reports and prioritizes issues.
    
    Responsibilities:
    - Review analysis reports
    - Prioritize issues based on system impact
    - Generate actionable recommendations
    - Validate proposed solutions against system requirements
    """
    
    def __init__(self,
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        """Initialize the system test review agent."""
        super().__init__(
            "system_test_review_agent",
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor
        )
    
    async def review_analysis(self, 
                            analysis_report: Dict[str, Any],
                            system_requirements: Dict[str, Any],
                            review_id: str) -> Dict[str, Any]:
        """
        Review a system test analysis report and generate prioritized recommendations.
        
        Args:
            analysis_report: The analysis report to review
            system_requirements: System requirements to validate against
            review_id: Unique identifier for this review
            
        Returns:
            Dictionary containing review results and recommendations
        """
        logger.info(f"Reviewing system test analysis report for review ID: {review_id}")
        
        start_time = time.time()
        
        # Record review start
        await self._metrics_manager.record_metric(
            "system_test_review:start",
            1.0,
            metadata={
                "review_id": review_id,
                "analysis_id": analysis_report.get("analysis_id", "unknown")
            }
        )
        
        # Extract patterns from analysis report
        patterns = analysis_report.get("patterns", [])
        
        if not patterns:
            logger.info(f"No patterns to review for {review_id}")
            return {
                "status": "success",
                "message": "No patterns to review",
                "review_id": review_id,
                "recommendations": [],
                "summary": {
                    "total_patterns": 0,
                    "critical_issues": 0,
                    "high_priority_recommendations": 0
                }
            }
        
        # Prioritize issues based on system impact
        prioritized_issues = self._prioritize_issues(patterns, system_requirements)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(prioritized_issues, system_requirements)
        
        # Validate recommendations against system requirements
        validated_recommendations = self._validate_recommendations(recommendations, system_requirements)
        
        # Create summary statistics
        summary = self._create_summary(validated_recommendations, analysis_report)
        
        # Create review report
        review_report = {
            "status": "success",
            "review_id": review_id,
            "analysis_id": analysis_report.get("analysis_id", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "execution_time_seconds": time.time() - start_time,
            "recommendations": [rec.to_dict() for rec in validated_recommendations],
            "summary": summary,
            "critical_issues": self._extract_critical_issues(validated_recommendations),
            "system_impact_assessment": self._assess_system_impact(validated_recommendations, system_requirements)
        }
        
        # Cache the review results
        await self._cache_manager.set(
            f"system_test_review:{review_id}",
            review_report,
            ttl=3600  # Cache for 1 hour
        )
        
        # Record review completion
        await self._metrics_manager.record_metric(
            "system_test_review:complete",
            1.0,
            metadata={
                "review_id": review_id,
                "recommendations_count": len(validated_recommendations),
                "critical_issues": summary.get("critical_issues", 0),
                "execution_time": time.time() - start_time
            }
        )
        
        logger.info(f"Completed system test review {review_id} - generated {len(validated_recommendations)} recommendations")
        return review_report
    
    def _prioritize_issues(self, 
                          patterns: List[Dict[str, Any]],
                          system_requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Prioritize issues based on system impact and requirements.
        
        Args:
            patterns: List of failure patterns from analysis
            system_requirements: System requirements to consider for prioritization
            
        Returns:
            List of prioritized issues with additional impact metadata
        """
        prioritized = []
        
        for pattern in patterns:
            # Start with the pattern priority from analysis
            priority = pattern.get("priority", "medium")
            
            # Copy pattern and add impact assessments
            enhanced_pattern = pattern.copy()
            
            # Additional impact factors
            impact_factors = []
            
            # 1. Check if pattern affects critical components
            affected_components = set(pattern.get("affected_components", []))
            critical_components = self._identify_critical_components(system_requirements)
            critical_component_impact = affected_components.intersection(critical_components)
            
            if critical_component_impact:
                impact_factors.append({
                    "factor": "critical_component_impact",
                    "description": f"Affects {len(critical_component_impact)} critical components",
                    "severity": "high"
                })
                priority = "high"  # Upgrade priority if critical components affected
            
            # 2. Check if pattern affects high-priority requirements
            requirement_impact = self._assess_requirement_impact(pattern, system_requirements)
            if requirement_impact.get("high_priority_requirements", 0) > 0:
                impact_factors.append({
                    "factor": "requirement_impact",
                    "description": "Affects high-priority system requirements",
                    "severity": "high",
                    "details": requirement_impact
                })
                priority = "high"  # Upgrade priority if high-priority requirements affected
            
            # 3. Assess stabilization impact
            stability_impact = self._assess_stability_impact(pattern)
            if stability_impact:
                impact_factors.append(stability_impact)
                if stability_impact.get("severity") == "high":
                    priority = "high"  # Upgrade priority for high stability impact
            
            # Add impact assessment to pattern
            enhanced_pattern["system_impact"] = {
                "priority": priority,
                "impact_factors": impact_factors,
                "overall_assessment": self._summarize_impact(impact_factors, priority)
            }
            
            prioritized.append(enhanced_pattern)
        
        # Sort by priority (high, medium, low)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        return sorted(prioritized, key=lambda p: priority_order.get(p["system_impact"]["priority"], 1))
    
    def _identify_critical_components(self, system_requirements: Dict[str, Any]) -> Set[str]:
        """Identify critical components from system requirements."""
        critical_components = set()
        
        # Check for explicitly marked critical components
        components = system_requirements.get("components", [])
        for component in components:
            if component.get("critical", False) or component.get("priority") == "high":
                critical_components.add(component.get("id", ""))
        
        # Also consider components that fulfill critical requirements
        critical_reqs = system_requirements.get("critical_requirements", [])
        for req in critical_reqs:
            if "fulfilled_by" in req:
                critical_components.update(req.get("fulfilled_by", []))
        
        return critical_components
    
    def _assess_requirement_impact(self, 
                                  pattern: Dict[str, Any],
                                  system_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Assess how the pattern impacts system requirements."""
        # Map components to requirements
        component_to_reqs = {}
        reqs_by_priority = {"high": 0, "medium": 0, "low": 0}
        
        requirements = system_requirements.get("functional_requirements", [])
        requirements.extend(system_requirements.get("non_functional_requirements", []))
        
        for req in requirements:
            req_id = req.get("id", "")
            req_priority = req.get("priority", "medium")
            components = req.get("components", [])
            
            for comp_id in components:
                if comp_id not in component_to_reqs:
                    component_to_reqs[comp_id] = []
                component_to_reqs[comp_id].append((req_id, req_priority))
        
        # Check affected components against requirements
        affected_components = set(pattern.get("affected_components", []))
        affected_requirements = set()
        
        for comp_id in affected_components:
            for req_id, req_priority in component_to_reqs.get(comp_id, []):
                affected_requirements.add(req_id)
                reqs_by_priority[req_priority] += 1
        
        return {
            "affected_requirements": list(affected_requirements),
            "high_priority_requirements": reqs_by_priority["high"],
            "medium_priority_requirements": reqs_by_priority["medium"],
            "low_priority_requirements": reqs_by_priority["low"]
        }
    
    def _assess_stability_impact(self, pattern: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Assess how the pattern impacts system stability."""
        # Look for indicators of stability issues
        frequency = pattern.get("frequency", 0)
        root_causes = pattern.get("root_causes", [])
        
        # Check for systemic issues
        systemic_indicators = [
            cause for cause in root_causes 
            if cause.get("type") in ["dependency_issue", "interface_mismatch"]
        ]
        
        if systemic_indicators and frequency > 3:
            return {
                "factor": "stability_impact",
                "description": "Pattern indicates systemic stability issues",
                "severity": "high",
                "details": {
                    "systemic_indicators": len(systemic_indicators),
                    "frequency": frequency
                }
            }
        elif systemic_indicators:
            return {
                "factor": "stability_impact",
                "description": "Pattern may indicate stability concerns",
                "severity": "medium",
                "details": {
                    "systemic_indicators": len(systemic_indicators),
                    "frequency": frequency
                }
            }
        
        return None
    
    def _summarize_impact(self, impact_factors: List[Dict[str, Any]], priority: str) -> str:
        """Create a concise summary of the overall impact."""
        high_factors = [f for f in impact_factors if f.get("severity") == "high"]
        
        if high_factors:
            factor_descriptions = [f.get("description", "") for f in high_factors]
            return f"High system impact: {'; '.join(factor_descriptions)}"
        elif priority == "medium":
            return "Moderate system impact requiring attention"
        else:
            return "Low system impact, routine resolution recommended"
    
    def _generate_recommendations(self, 
                                prioritized_issues: List[Dict[str, Any]],
                                system_requirements: Dict[str, Any]) -> List[ReviewRecommendation]:
        """
        Generate actionable recommendations based on prioritized issues.
        
        Args:
            prioritized_issues: List of prioritized issues
            system_requirements: System requirements for context
            
        Returns:
            List of recommendations
        """
        recommendations = []
        recommendation_id_base = f"rec_{int(time.time())}"
        
        # Process high priority issues first
        high_priority_issues = [issue for issue in prioritized_issues 
                              if issue.get("system_impact", {}).get("priority") == "high"]
        
        for i, issue in enumerate(high_priority_issues):
            rec_id = f"{recommendation_id_base}_high_{i}"
            pattern_id = issue.get("pattern_id", "")
            pattern_name = issue.get("pattern_name", "Unknown pattern")
            
            # Create recommendation based on issue type
            root_causes = issue.get("root_causes", [])
            
            if not root_causes:
                continue
                
            primary_cause = root_causes[0]
            cause_type = primary_cause.get("type", "")
            
            if cause_type == "dependency_issue":
                recommendation = ReviewRecommendation(
                    recommendation_id=rec_id,
                    priority="high",
                    title=f"Resolve dependency issues in {pattern_name}",
                    description="Fix critical component dependency issues that are causing system failures",
                    action_items=[
                        "Audit component dependencies and ensure correct versions",
                        "Verify interface compatibility between dependent components",
                        "Update dependency documentation and validation tests"
                    ],
                    affected_components=issue.get("affected_components", []),
                    related_patterns=[pattern_id],
                    estimated_effort="medium",
                    system_impact="high"
                )
            elif cause_type == "interface_mismatch":
                recommendation = ReviewRecommendation(
                    recommendation_id=rec_id,
                    priority="high",
                    title=f"Fix interface incompatibilities in {pattern_name}",
                    description="Resolve component interface mismatches causing system integration failures",
                    action_items=[
                        "Review interface contracts between affected components",
                        "Update interface implementation to ensure compatibility",
                        "Add strong typing and validation at component boundaries",
                        "Create integration tests for interface compliance"
                    ],
                    affected_components=issue.get("affected_components", []),
                    related_patterns=[pattern_id],
                    estimated_effort="high",
                    system_impact="high"
                )
            elif cause_type == "implementation_error":
                recommendation = ReviewRecommendation(
                    recommendation_id=rec_id,
                    priority="high",
                    title=f"Fix implementation errors in {pattern_name}",
                    description="Address critical implementation bugs causing system failures",
                    action_items=[
                        "Debug and identify exact error locations in affected components",
                        "Fix implementation bugs in the components",
                        "Add comprehensive error handling and recovery",
                        "Create regression tests to prevent future occurrences"
                    ],
                    affected_components=issue.get("affected_components", []),
                    related_patterns=[pattern_id],
                    estimated_effort="medium",
                    system_impact="high"
                )
            else:
                # Generic recommendation for other types
                recommendation = ReviewRecommendation(
                    recommendation_id=rec_id,
                    priority="high",
                    title=f"Address critical issues in {pattern_name}",
                    description=f"Resolve issues causing system failures: {cause_type}",
                    action_items=[
                        "Investigate root cause in affected components",
                        "Fix identified issues with appropriate measures",
                        "Add tests to verify resolution"
                    ],
                    affected_components=issue.get("affected_components", []),
                    related_patterns=[pattern_id],
                    estimated_effort="medium",
                    system_impact="high"
                )
            
            recommendations.append(recommendation)
        
        # Process medium priority issues
        medium_priority_issues = [issue for issue in prioritized_issues 
                                if issue.get("system_impact", {}).get("priority") == "medium"]
        
        for i, issue in enumerate(medium_priority_issues):
            rec_id = f"{recommendation_id_base}_medium_{i}"
            pattern_id = issue.get("pattern_id", "")
            pattern_name = issue.get("pattern_name", "Unknown pattern")
            
            # Create more general recommendations for medium priority
            root_causes = issue.get("root_causes", [])
            
            if not root_causes:
                continue
                
            primary_cause = root_causes[0]
            cause_type = primary_cause.get("type", "")
            
            recommendation = ReviewRecommendation(
                recommendation_id=rec_id,
                priority="medium",
                title=f"Improve {cause_type} in {pattern_name}",
                description=f"Address {cause_type} issues to enhance system reliability",
                action_items=[
                    f"Review and fix {cause_type} in affected components",
                    "Add appropriate tests to verify resolution",
                    "Update documentation if needed"
                ],
                affected_components=issue.get("affected_components", []),
                related_patterns=[pattern_id],
                estimated_effort="medium",
                system_impact="medium"
            )
            
            recommendations.append(recommendation)
        
        # Add systemic recommendations if needed
        if len(recommendations) > 3:
            recommendations.append(self._create_systemic_recommendation(
                f"{recommendation_id_base}_systemic",
                prioritized_issues,
                system_requirements
            ))
        
        return recommendations
    
    def _create_systemic_recommendation(self, 
                                      rec_id: str,
                                      issues: List[Dict[str, Any]],
                                      system_requirements: Dict[str, Any]) -> ReviewRecommendation:
        """Create a recommendation addressing systemic issues."""
        # Identify common patterns across multiple issues
        cause_types = {}
        affected_components = set()
        
        for issue in issues:
            for cause in issue.get("root_causes", []):
                cause_type = cause.get("type", "")
                if cause_type not in cause_types:
                    cause_types[cause_type] = 0
                cause_types[cause_type] += 1
            
            affected_components.update(issue.get("affected_components", []))
        
        # Determine the most common cause type
        common_cause = max(cause_types.items(), key=lambda x: x[1])[0] if cause_types else "unknown"
        
        # Create appropriate systemic recommendation
        if common_cause == "dependency_issue":
            recommendation = ReviewRecommendation(
                recommendation_id=rec_id,
                priority="high",
                title="Establish improved dependency management practices",
                description="Address systemic dependency management issues across components",
                action_items=[
                    "Create centralized dependency management system",
                    "Implement automated dependency validation",
                    "Document component dependencies more clearly",
                    "Add dependency health checks to the CI pipeline"
                ],
                affected_components=list(affected_components),
                related_patterns=[],
                estimated_effort="high",
                system_impact="high"
            )
        elif common_cause == "interface_mismatch":
            recommendation = ReviewRecommendation(
                recommendation_id=rec_id,
                priority="high",
                title="Implement robust interface contract system",
                description="Establish strict interface contracts across component boundaries",
                action_items=[
                    "Define formal interface contracts for all components",
                    "Implement contract verification at runtime",
                    "Create comprehensive interface test suite",
                    "Generate interface documentation automatically"
                ],
                affected_components=list(affected_components),
                related_patterns=[],
                estimated_effort="high",
                system_impact="high"
            )
        elif common_cause == "implementation_error":
            recommendation = ReviewRecommendation(
                recommendation_id=rec_id,
                priority="high",
                title="Improve implementation quality and error handling",
                description="Enhance implementation practices to reduce errors systemwide",
                action_items=[
                    "Establish code review guidelines focused on error handling",
                    "Implement more comprehensive logging and monitoring",
                    "Add automated error detection to the CI pipeline",
                    "Create a test suite focused on edge cases and error conditions"
                ],
                affected_components=list(affected_components),
                related_patterns=[],
                estimated_effort="high",
                system_impact="high"
            )
        else:
            recommendation = ReviewRecommendation(
                recommendation_id=rec_id,
                priority="high",
                title="Address systemic quality issues",
                description="Implement improvements to overall system quality and testing",
                action_items=[
                    "Enhance test coverage across all components",
                    "Implement more robust integration testing",
                    "Improve error reporting and monitoring",
                    "Establish quality metrics and monitoring"
                ],
                affected_components=list(affected_components),
                related_patterns=[],
                estimated_effort="high",
                system_impact="high"
            )
        
        return recommendation
    
    def _validate_recommendations(self, 
                                recommendations: List[ReviewRecommendation],
                                system_requirements: Dict[str, Any]) -> List[ReviewRecommendation]:
        """
        Validate recommendations against system requirements.
        
        Args:
            recommendations: List of recommendations to validate
            system_requirements: System requirements to validate against
            
        Returns:
            Validated recommendations, potentially with adjustments
        """
        validated_recommendations = []
        
        for recommendation in recommendations:
            # Check recommendation against system constraints
            constraints = system_requirements.get("constraints", [])
            constraint_violations = []
            
            for constraint in constraints:
                constraint_type = constraint.get("type", "")
                
                if constraint_type == "performance" and "performance" in recommendation.description.lower():
                    # Ensure performance recommendations align with performance requirements
                    constraint_violations.append(f"Performance constraint: {constraint.get('description', '')}")
                
                elif constraint_type == "security" and "security" in recommendation.description.lower():
                    # Ensure security recommendations align with security requirements
                    constraint_violations.append(f"Security constraint: {constraint.get('description', '')}")
            
            # Create a copy of the recommendation
            validated_rec = ReviewRecommendation(
                recommendation_id=recommendation.recommendation_id,
                priority=recommendation.priority,
                title=recommendation.title,
                description=recommendation.description,
                action_items=recommendation.action_items.copy(),
                affected_components=recommendation.affected_components.copy(),
                related_patterns=recommendation.related_patterns.copy(),
                estimated_effort=recommendation.estimated_effort,
                system_impact=recommendation.system_impact
            )
            
            # Add constraint compliance notes if needed
            if constraint_violations:
                constraint_note = f"Note: Must comply with system constraints: {', '.join(constraint_violations)}"
                validated_rec.action_items.append(constraint_note)
            
            validated_recommendations.append(validated_rec)
        
        return validated_recommendations
    
    def _create_summary(self, 
                       recommendations: List[ReviewRecommendation],
                       analysis_report: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of the review results."""
        # Count recommendations by priority
        priority_counts = {"high": 0, "medium": 0, "low": 0}
        for rec in recommendations:
            priority_counts[rec.priority] += 1
        
        # Determine if there are critical issues
        critical_issues = priority_counts["high"] > 0
        
        # Extract statistics from analysis report
        statistics = analysis_report.get("statistics", {})
        
        return {
            "total_patterns": len(analysis_report.get("patterns", [])),
            "total_recommendations": len(recommendations),
            "high_priority_recommendations": priority_counts["high"],
            "medium_priority_recommendations": priority_counts["medium"],
            "low_priority_recommendations": priority_counts["low"],
            "critical_issues": priority_counts["high"],
            "failure_rate": statistics.get("failure_rate", 0),
            "affected_component_count": statistics.get("affected_component_count", 0)
        }
    
    def _extract_critical_issues(self, recommendations: List[ReviewRecommendation]) -> List[Dict[str, Any]]:
        """Extract critical issues for executive summary."""
        critical_issues = []
        
        for rec in recommendations:
            if rec.priority == "high":
                critical_issues.append({
                    "title": rec.title,
                    "description": rec.description,
                    "recommendation_id": rec.recommendation_id,
                    "affected_components": len(rec.affected_components),
                    "system_impact": rec.system_impact
                })
        
        return critical_issues
    
    def _assess_system_impact(self, 
                            recommendations: List[ReviewRecommendation],
                            system_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall system impact of identified issues."""
        if not recommendations:
            return {
                "overall_impact": "none",
                "description": "No system issues identified"
            }
        
        high_priority_count = sum(1 for rec in recommendations if rec.priority == "high")
        total_affected_components = set()
        
        for rec in recommendations:
            total_affected_components.update(rec.affected_components)
        
        # Check against critical requirements
        critical_reqs = system_requirements.get("critical_requirements", [])
        critical_components = self._identify_critical_components(system_requirements)
        critical_component_impact = total_affected_components.intersection(critical_components)
        
        # Determine overall impact
        if high_priority_count > 3 or len(critical_component_impact) > 1:
            impact = "severe"
            description = "Critical system functionality compromised, immediate action required"
        elif high_priority_count > 0 or critical_component_impact:
            impact = "significant"
            description = "Important system functionality affected, prompt action recommended"
        elif recommendations:
            impact = "moderate"
            description = "System functionality partially affected, scheduled action advised"
        else:
            impact = "minimal"
            description = "Minor issues with limited system impact"
        
        return {
            "overall_impact": impact,
            "description": description,
            "affected_components_count": len(total_affected_components),
            "critical_components_affected": len(critical_component_impact),
            "high_priority_issues": high_priority_count
        }