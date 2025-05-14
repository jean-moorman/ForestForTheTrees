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
class DeploymentRecommendation:
    recommendation_id: str
    priority: str  # high, medium, low
    title: str
    description: str
    action_items: List[str] = field(default_factory=list)
    affected_environments: List[str] = field(default_factory=list)
    affected_components: List[str] = field(default_factory=list)
    related_patterns: List[str] = field(default_factory=list)
    estimated_effort: str = "medium"  # high, medium, low
    deployment_impact: str = "medium"  # high, medium, low
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "recommendation_id": self.recommendation_id,
            "priority": self.priority,
            "title": self.title,
            "description": self.description,
            "action_items": self.action_items,
            "affected_environments": self.affected_environments,
            "affected_components": self.affected_components,
            "related_patterns": self.related_patterns,
            "estimated_effort": self.estimated_effort,
            "deployment_impact": self.deployment_impact
        }


class DeploymentTestReviewAgent(PhaseTwoAgentBase):
    """
    Reviews deployment analysis reports and generates recommendations.
    
    Responsibilities:
    - Review deployment analysis reports
    - Generate deployment environment recommendations
    - Prioritize deployment issues
    - Create deployment fix strategies
    """
    
    def __init__(self,
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        """Initialize the deployment test review agent."""
        super().__init__(
            "deployment_test_review_agent",
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor
        )
    
    async def review_deployment_analysis(self, 
                                        analysis_report: Dict[str, Any],
                                        environments: List[Dict[str, Any]],
                                        components: List[Dict[str, Any]],
                                        deployment_requirements: Dict[str, Any],
                                        review_id: str) -> Dict[str, Any]:
        """
        Review a deployment test analysis report and generate prioritized recommendations.
        
        Args:
            analysis_report: The deployment analysis report to review
            environments: List of deployment environments
            components: List of deployed components
            deployment_requirements: Deployment requirements and constraints
            review_id: Unique identifier for this review
            
        Returns:
            Dictionary containing review results and recommendations
        """
        logger.info(f"Reviewing deployment test analysis report for review ID: {review_id}")
        
        start_time = time.time()
        
        # Record review start
        await self._metrics_manager.record_metric(
            "deployment_test_review:start",
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
        
        # Create mappings for quick lookup
        environment_mapping = {env.get("id", ""): env for env in environments}
        component_mapping = {comp.get("id", ""): comp for comp in components}
        
        # Prioritize issues based on deployment impact
        prioritized_issues = self._prioritize_issues(
            patterns, environment_mapping, component_mapping, deployment_requirements)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            prioritized_issues, environment_mapping, component_mapping, deployment_requirements)
        
        # Create fix strategies
        fix_strategies = self._create_fix_strategies(
            recommendations, environment_mapping, deployment_requirements)
        
        # Create summary statistics
        summary = self._create_summary(recommendations, analysis_report)
        
        # Create review report
        review_report = {
            "status": "success",
            "review_id": review_id,
            "analysis_id": analysis_report.get("analysis_id", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "execution_time_seconds": time.time() - start_time,
            "recommendations": [rec.to_dict() for rec in recommendations],
            "fix_strategies": fix_strategies,
            "summary": summary,
            "critical_issues": self._extract_critical_issues(recommendations),
            "environment_assessments": self._assess_environments(
                recommendations, environment_mapping)
        }
        
        # Cache the review results
        await self._cache_manager.set(
            f"deployment_test_review:{review_id}",
            review_report,
            ttl=3600  # Cache for 1 hour
        )
        
        # Record review completion
        await self._metrics_manager.record_metric(
            "deployment_test_review:complete",
            1.0,
            metadata={
                "review_id": review_id,
                "recommendations_count": len(recommendations),
                "critical_issues": summary.get("critical_issues", 0),
                "execution_time": time.time() - start_time
            }
        )
        
        logger.info(f"Completed deployment test review {review_id} - generated {len(recommendations)} recommendations")
        return review_report
    
    def _prioritize_issues(self, 
                          patterns: List[Dict[str, Any]],
                          environment_mapping: Dict[str, Dict[str, Any]],
                          component_mapping: Dict[str, Dict[str, Any]],
                          deployment_requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Prioritize issues based on deployment impact and requirements.
        
        Args:
            patterns: List of failure patterns from analysis
            environment_mapping: Mapping of environment IDs to details
            component_mapping: Mapping of component IDs to details
            deployment_requirements: Deployment requirements to consider
            
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
            
            # 1. Check if pattern affects critical environments
            affected_environments = set(pattern.get("affected_environments", []))
            critical_environments = self._identify_critical_environments(deployment_requirements)
            critical_env_impact = affected_environments.intersection(critical_environments)
            
            if critical_env_impact:
                impact_factors.append({
                    "factor": "critical_environment_impact",
                    "description": f"Affects {len(critical_env_impact)} critical environments",
                    "severity": "high"
                })
                priority = "high"  # Upgrade priority if critical environments affected
            
            # 2. Check if pattern affects critical components
            affected_components = set(pattern.get("affected_components", []))
            critical_components = self._identify_critical_components(deployment_requirements)
            critical_component_impact = affected_components.intersection(critical_components)
            
            if critical_component_impact:
                impact_factors.append({
                    "factor": "critical_component_impact",
                    "description": f"Affects {len(critical_component_impact)} critical components",
                    "severity": "high"
                })
                priority = "high"  # Upgrade priority if critical components affected
            
            # 3. Check if pattern affects deployment requirements
            requirement_impact = self._assess_requirement_impact(pattern, deployment_requirements)
            if requirement_impact.get("high_priority_requirements", 0) > 0:
                impact_factors.append({
                    "factor": "requirement_impact",
                    "description": "Affects high-priority deployment requirements",
                    "severity": "high",
                    "details": requirement_impact
                })
                priority = "high"  # Upgrade priority if high-priority requirements affected
            
            # 4. Assess production impact
            production_impact = self._assess_production_impact(pattern, environment_mapping)
            if production_impact:
                impact_factors.append(production_impact)
                if production_impact.get("severity") == "high":
                    priority = "high"  # Upgrade priority for high production impact
            
            # Add impact assessment to pattern
            enhanced_pattern["deployment_impact"] = {
                "priority": priority,
                "impact_factors": impact_factors,
                "overall_assessment": self._summarize_impact(impact_factors, priority)
            }
            
            prioritized.append(enhanced_pattern)
        
        # Sort by priority (high, medium, low)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        return sorted(prioritized, key=lambda p: priority_order.get(p["deployment_impact"]["priority"], 1))
    
    def _identify_critical_environments(self, deployment_requirements: Dict[str, Any]) -> Set[str]:
        """Identify critical environments from deployment requirements."""
        critical_environments = set()
        
        # Check for explicitly marked critical environments
        environments = deployment_requirements.get("environments", [])
        for env in environments:
            if env.get("critical", False) or env.get("tier") == "production":
                critical_environments.add(env.get("id", ""))
        
        # Also consider environments that fulfill critical requirements
        critical_reqs = deployment_requirements.get("critical_requirements", [])
        for req in critical_reqs:
            if "environments" in req:
                critical_environments.update(req.get("environments", []))
        
        return critical_environments
    
    def _identify_critical_components(self, deployment_requirements: Dict[str, Any]) -> Set[str]:
        """Identify critical components from deployment requirements."""
        critical_components = set()
        
        # Check for explicitly marked critical components
        components = deployment_requirements.get("components", [])
        for component in components:
            if component.get("critical", False) or component.get("priority") == "high":
                critical_components.add(component.get("id", ""))
        
        return critical_components
    
    def _assess_requirement_impact(self, 
                                  pattern: Dict[str, Any],
                                  deployment_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Assess how the pattern impacts deployment requirements."""
        # Map components and environments to requirements
        requirement_mapping = {}
        reqs_by_priority = {"high": 0, "medium": 0, "low": 0}
        
        requirements = deployment_requirements.get("requirements", [])
        
        for req in requirements:
            req_id = req.get("id", "")
            req_priority = req.get("priority", "medium")
            req_components = req.get("components", [])
            req_environments = req.get("environments", [])
            
            # Add components to mapping
            for comp_id in req_components:
                if comp_id not in requirement_mapping:
                    requirement_mapping[comp_id] = []
                requirement_mapping[comp_id].append((req_id, req_priority, "component"))
            
            # Add environments to mapping
            for env_id in req_environments:
                if env_id not in requirement_mapping:
                    requirement_mapping[env_id] = []
                requirement_mapping[env_id].append((req_id, req_priority, "environment"))
        
        # Check affected components and environments against requirements
        affected_components = set(pattern.get("affected_components", []))
        affected_environments = set(pattern.get("affected_environments", []))
        affected_requirements = set()
        
        # Check components
        for comp_id in affected_components:
            for req_id, req_priority, req_type in requirement_mapping.get(comp_id, []):
                affected_requirements.add(req_id)
                reqs_by_priority[req_priority] += 1
        
        # Check environments
        for env_id in affected_environments:
            for req_id, req_priority, req_type in requirement_mapping.get(env_id, []):
                affected_requirements.add(req_id)
                reqs_by_priority[req_priority] += 1
        
        return {
            "affected_requirements": list(affected_requirements),
            "high_priority_requirements": reqs_by_priority["high"],
            "medium_priority_requirements": reqs_by_priority["medium"],
            "low_priority_requirements": reqs_by_priority["low"]
        }
    
    def _assess_production_impact(self, 
                                pattern: Dict[str, Any],
                                environment_mapping: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Assess how the pattern impacts production environments."""
        # Check if any affected environments are production
        production_environments = []
        for env_id in pattern.get("affected_environments", []):
            env = environment_mapping.get(env_id, {})
            env_type = env.get("type", "").lower()
            env_tier = env.get("tier", "").lower()
            
            if env_type == "production" or env_tier == "production":
                production_environments.append({
                    "id": env_id,
                    "name": env.get("name", ""),
                    "type": env_type
                })
        
        if production_environments:
            return {
                "factor": "production_impact",
                "description": f"Affects {len(production_environments)} production environments",
                "severity": "high",
                "environments": production_environments
            }
        
        # Check if issues could potentially affect production later
        staging_environments = []
        for env_id in pattern.get("affected_environments", []):
            env = environment_mapping.get(env_id, {})
            env_type = env.get("type", "").lower()
            env_tier = env.get("tier", "").lower()
            
            if env_type == "staging" or env_tier == "staging":
                staging_environments.append({
                    "id": env_id,
                    "name": env.get("name", ""),
                    "type": env_type
                })
        
        if staging_environments and pattern.get("frequency", 0) > 2:
            return {
                "factor": "production_risk",
                "description": f"Issues in staging may affect production deployment",
                "severity": "medium",
                "environments": staging_environments
            }
        
        return None
    
    def _summarize_impact(self, impact_factors: List[Dict[str, Any]], priority: str) -> str:
        """Create a concise summary of the overall impact."""
        high_factors = [f for f in impact_factors if f.get("severity") == "high"]
        
        if high_factors:
            factor_descriptions = [f.get("description", "") for f in high_factors]
            return f"High deployment impact: {'; '.join(factor_descriptions)}"
        elif priority == "medium":
            return "Moderate deployment impact requiring attention"
        else:
            return "Low deployment impact, routine resolution recommended"
    
    def _generate_recommendations(self, 
                                prioritized_issues: List[Dict[str, Any]],
                                environment_mapping: Dict[str, Dict[str, Any]],
                                component_mapping: Dict[str, Dict[str, Any]],
                                deployment_requirements: Dict[str, Any]) -> List[DeploymentRecommendation]:
        """
        Generate actionable recommendations based on prioritized issues.
        
        Args:
            prioritized_issues: List of prioritized issues
            environment_mapping: Mapping of environment IDs to details
            component_mapping: Mapping of component IDs to details
            deployment_requirements: Deployment requirements for context
            
        Returns:
            List of recommendations
        """
        recommendations = []
        recommendation_id_base = f"rec_{int(time.time())}"
        
        # Process high priority issues first
        high_priority_issues = [issue for issue in prioritized_issues 
                              if issue.get("deployment_impact", {}).get("priority") == "high"]
        
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
            
            if cause_type == "environment_configuration":
                recommendation = self._create_configuration_recommendation(
                    rec_id, issue, primary_cause, environment_mapping)
                
            elif cause_type == "deployment_dependency":
                recommendation = self._create_dependency_recommendation(
                    rec_id, issue, primary_cause, component_mapping)
                
            elif cause_type == "compatibility":
                recommendation = self._create_compatibility_recommendation(
                    rec_id, issue, primary_cause, environment_mapping, component_mapping)
                
            elif cause_type == "resource":
                recommendation = self._create_resource_recommendation(
                    rec_id, issue, primary_cause, environment_mapping)
                
            else:
                # Generic recommendation for other types
                recommendation = DeploymentRecommendation(
                    recommendation_id=rec_id,
                    priority="high",
                    title=f"Address critical deployment issues in {pattern_name}",
                    description=f"Resolve deployment failures related to: {cause_type}",
                    action_items=[
                        "Investigate root cause in affected environments",
                        "Fix identified issues with appropriate measures",
                        "Create deployment verification tests"
                    ],
                    affected_environments=issue.get("affected_environments", []),
                    affected_components=issue.get("affected_components", []),
                    related_patterns=[pattern_id],
                    estimated_effort="medium",
                    deployment_impact="high"
                )
            
            recommendations.append(recommendation)
        
        # Process medium priority issues
        medium_priority_issues = [issue for issue in prioritized_issues 
                                if issue.get("deployment_impact", {}).get("priority") == "medium"]
        
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
            
            recommendation = DeploymentRecommendation(
                recommendation_id=rec_id,
                priority="medium",
                title=f"Improve {cause_type} in {pattern_name}",
                description=f"Address {cause_type} issues to enhance deployment reliability",
                action_items=[
                    f"Review and fix {cause_type} in affected environments",
                    "Add appropriate tests to verify resolution",
                    "Update deployment documentation if needed"
                ],
                affected_environments=issue.get("affected_environments", []),
                affected_components=issue.get("affected_components", []),
                related_patterns=[pattern_id],
                estimated_effort="medium",
                deployment_impact="medium"
            )
            
            recommendations.append(recommendation)
        
        # Add cross-environment recommendations if needed
        if len(recommendations) > 3:
            recommendations.append(self._create_cross_environment_recommendation(
                f"{recommendation_id_base}_cross_env",
                prioritized_issues,
                environment_mapping,
                deployment_requirements
            ))
        
        return recommendations
    
    def _create_configuration_recommendation(self, 
                                           rec_id: str,
                                           issue: Dict[str, Any],
                                           cause: Dict[str, Any],
                                           environment_mapping: Dict[str, Dict[str, Any]]) -> DeploymentRecommendation:
        """Create a recommendation for environment configuration issues."""
        pattern_id = issue.get("pattern_id", "")
        pattern_name = issue.get("pattern_name", "Unknown pattern")
        affected_environments = issue.get("affected_environments", [])
        
        # Environment-specific actions
        env_actions = []
        for env_id in affected_environments:
            env = environment_mapping.get(env_id, {})
            env_name = env.get("name", f"Environment {env_id}")
            env_type = env.get("type", "unknown")
            
            env_actions.append(f"Verify configuration in {env_name} ({env_type})")
        
        return DeploymentRecommendation(
            recommendation_id=rec_id,
            priority="high",
            title=f"Fix environment configuration issues in {pattern_name}",
            description="Resolve environment configuration issues causing deployment failures",
            action_items=[
                *env_actions,
                "Validate environment variables and configuration files",
                "Check for missing or incorrect configuration entries",
                "Create environment configuration validation tests"
            ],
            affected_environments=affected_environments,
            affected_components=issue.get("affected_components", []),
            related_patterns=[pattern_id],
            estimated_effort="medium",
            deployment_impact="high"
        )
    
    def _create_dependency_recommendation(self, 
                                        rec_id: str,
                                        issue: Dict[str, Any],
                                        cause: Dict[str, Any],
                                        component_mapping: Dict[str, Dict[str, Any]]) -> DeploymentRecommendation:
        """Create a recommendation for deployment dependency issues."""
        pattern_id = issue.get("pattern_id", "")
        pattern_name = issue.get("pattern_name", "Unknown pattern")
        affected_components = issue.get("affected_components", [])
        
        # Component-specific actions
        component_actions = []
        for comp_id in affected_components:
            component = component_mapping.get(comp_id, {})
            comp_name = component.get("name", f"Component {comp_id}")
            
            component_actions.append(f"Verify dependencies for {comp_name}")
        
        return DeploymentRecommendation(
            recommendation_id=rec_id,
            priority="high",
            title=f"Resolve deployment dependency issues in {pattern_name}",
            description="Fix dependency conflicts and missing dependencies during deployment",
            action_items=[
                *component_actions,
                "Check for version conflicts between component dependencies",
                "Ensure all required dependencies are included in deployment packages",
                "Verify dependency resolution order during deployment",
                "Implement dependency validation during deployment process"
            ],
            affected_environments=issue.get("affected_environments", []),
            affected_components=affected_components,
            related_patterns=[pattern_id],
            estimated_effort="medium",
            deployment_impact="high"
        )
    
    def _create_compatibility_recommendation(self, 
                                          rec_id: str,
                                          issue: Dict[str, Any],
                                          cause: Dict[str, Any],
                                          environment_mapping: Dict[str, Dict[str, Any]],
                                          component_mapping: Dict[str, Dict[str, Any]]) -> DeploymentRecommendation:
        """Create a recommendation for component-environment compatibility issues."""
        pattern_id = issue.get("pattern_id", "")
        pattern_name = issue.get("pattern_name", "Unknown pattern")
        affected_environments = issue.get("affected_environments", [])
        affected_components = issue.get("affected_components", [])
        
        # Generate specific actions based on affected environments and components
        env_names = []
        for env_id in affected_environments:
            env = environment_mapping.get(env_id, {})
            env_names.append(env.get("name", f"Environment {env_id}"))
        
        comp_names = []
        for comp_id in affected_components:
            component = component_mapping.get(comp_id, {})
            comp_names.append(component.get("name", f"Component {comp_id}"))
        
        return DeploymentRecommendation(
            recommendation_id=rec_id,
            priority="high",
            title=f"Address component-environment compatibility issues in {pattern_name}",
            description=f"Resolve compatibility issues between components ({', '.join(comp_names)}) and environments ({', '.join(env_names)})",
            action_items=[
                "Verify component requirements match environment capabilities",
                "Update components to support all target environments",
                "Consider containerization to reduce environment dependencies",
                "Create environment compatibility test matrix",
                "Implement pre-deployment environment compatibility checks"
            ],
            affected_environments=affected_environments,
            affected_components=affected_components,
            related_patterns=[pattern_id],
            estimated_effort="high",
            deployment_impact="high"
        )
    
    def _create_resource_recommendation(self, 
                                      rec_id: str,
                                      issue: Dict[str, Any],
                                      cause: Dict[str, Any],
                                      environment_mapping: Dict[str, Dict[str, Any]]) -> DeploymentRecommendation:
        """Create a recommendation for resource allocation issues."""
        pattern_id = issue.get("pattern_id", "")
        pattern_name = issue.get("pattern_name", "Unknown pattern")
        affected_environments = issue.get("affected_environments", [])
        
        # Environment-specific actions
        env_actions = []
        for env_id in affected_environments:
            env = environment_mapping.get(env_id, {})
            env_name = env.get("name", f"Environment {env_id}")
            env_type = env.get("type", "unknown")
            
            env_actions.append(f"Review resource allocation for {env_name} ({env_type})")
        
        return DeploymentRecommendation(
            recommendation_id=rec_id,
            priority="high",
            title=f"Resolve resource allocation issues in {pattern_name}",
            description="Address resource constraints causing deployment failures",
            action_items=[
                *env_actions,
                "Increase resource allocation for affected environments",
                "Optimize component resource usage",
                "Implement resource monitoring and scaling",
                "Establish resource baselines for all components",
                "Add resource validation to pre-deployment checks"
            ],
            affected_environments=affected_environments,
            affected_components=issue.get("affected_components", []),
            related_patterns=[pattern_id],
            estimated_effort="medium",
            deployment_impact="high"
        )
    
    def _create_cross_environment_recommendation(self, 
                                              rec_id: str,
                                              issues: List[Dict[str, Any]],
                                              environment_mapping: Dict[str, Dict[str, Any]],
                                              deployment_requirements: Dict[str, Any]) -> DeploymentRecommendation:
        """Create a recommendation for cross-environment consistency issues."""
        # Collect all affected environments
        all_environments = set()
        for issue in issues:
            all_environments.update(issue.get("affected_environments", []))
        
        # Identify environment types 
        env_types = {}
        for env_id in all_environments:
            env = environment_mapping.get(env_id, {})
            env_type = env.get("type", "unknown")
            
            if env_type not in env_types:
                env_types[env_type] = []
            env_types[env_type].append(env_id)
        
        return DeploymentRecommendation(
            recommendation_id=rec_id,
            priority="high",
            title="Establish consistent deployment environment configuration",
            description="Create standardized deployment processes across all environments",
            action_items=[
                "Implement Infrastructure as Code to ensure environment consistency",
                "Create deployment environment templates for each environment type",
                "Establish configuration validation across environments",
                "Create cross-environment deployment testing process",
                "Implement continuous deployment verification"
            ],
            affected_environments=list(all_environments),
            affected_components=[],
            related_patterns=[issue.get("pattern_id", "") for issue in issues],
            estimated_effort="high",
            deployment_impact="high"
        )
    
    def _create_fix_strategies(self, 
                             recommendations: List[DeploymentRecommendation],
                             environment_mapping: Dict[str, Dict[str, Any]],
                             deployment_requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create deployment fix strategies based on recommendations.
        
        This method generates higher-level fix strategies that address multiple
        recommendations in a coordinated way, focusing on deployment process improvements.
        """
        strategies = []
        
        # Group recommendations by environment type
        env_type_recommendations = {}
        for rec in recommendations:
            for env_id in rec.affected_environments:
                env = environment_mapping.get(env_id, {})
                env_type = env.get("type", "unknown")
                
                if env_type not in env_type_recommendations:
                    env_type_recommendations[env_type] = []
                env_type_recommendations[env_type].append(rec)
        
        # Create strategies for each environment type
        for env_type, env_recs in env_type_recommendations.items():
            if len(env_recs) < 2:
                continue
                
            # Count high priority recommendations
            high_priority_count = sum(1 for r in env_recs if r.priority == "high")
            
            # Get affected environments of this type
            affected_environments = set()
            for rec in env_recs:
                for env_id in rec.affected_environments:
                    env = environment_mapping.get(env_id, {})
                    if env.get("type", "") == env_type:
                        affected_environments.add(env_id)
            
            # Create strategy for this environment type
            strategy = {
                "strategy_id": f"strategy_{env_type}_{int(time.time())}",
                "name": f"{env_type.capitalize()} Environment Deployment Strategy",
                "description": f"Comprehensive strategy to address deployment issues in {env_type} environments",
                "priority": "high" if high_priority_count > 0 else "medium",
                "affected_environments": list(affected_environments),
                "environment_type": env_type,
                "related_recommendations": [r.recommendation_id for r in env_recs],
                "implementation_phases": self._generate_implementation_phases(env_type, env_recs),
                "success_criteria": self._generate_success_criteria(env_type, affected_environments, deployment_requirements)
            }
            
            strategies.append(strategy)
        
        # Add a cross-environment strategy if needed
        if len(recommendations) > 5:
            strategies.append(self._create_cross_environment_strategy(recommendations, environment_mapping, deployment_requirements))
        
        return strategies
    
    def _generate_implementation_phases(self, 
                                      env_type: str, 
                                      recommendations: List[DeploymentRecommendation]) -> List[Dict[str, Any]]:
        """Generate implementation phases for a fix strategy."""
        phases = []
        
        # Phase 1: Immediate fixes for high priority issues
        high_priority_recs = [r for r in recommendations if r.priority == "high"]
        if high_priority_recs:
            phases.append({
                "phase": 1,
                "name": "Critical Issue Resolution",
                "description": f"Address high-priority deployment issues in {env_type} environments",
                "tasks": [
                    f"Implement recommendation: {r.title}" for r in high_priority_recs
                ],
                "timeline": "Immediate",
                "related_recommendations": [r.recommendation_id for r in high_priority_recs]
            })
        
        # Phase 2: Standardization and process improvements
        phases.append({
            "phase": 2,
            "name": f"{env_type.capitalize()} Environment Standardization",
            "description": f"Establish standardized deployment process for {env_type} environments",
            "tasks": [
                f"Create standardized {env_type} environment templates",
                f"Implement automated configuration validation for {env_type} environments",
                f"Establish deployment validation tests for {env_type} environments",
                f"Document {env_type} deployment requirements and procedures"
            ],
            "timeline": "Short-term",
            "related_recommendations": [r.recommendation_id for r in recommendations if r.priority == "medium"]
        })
        
        # Phase 3: Continuous improvement
        phases.append({
            "phase": 3,
            "name": "Continuous Deployment Improvement",
            "description": f"Implement long-term deployment improvements for {env_type} environments",
            "tasks": [
                f"Integrate {env_type} deployment verification into CI/CD pipeline",
                f"Establish automated deployment monitoring for {env_type} environments",
                f"Implement deployment metrics collection and analysis",
                f"Create deployment rollback and recovery procedures"
            ],
            "timeline": "Medium-term",
            "related_recommendations": []
        })
        
        return phases
    
    def _generate_success_criteria(self, 
                                 env_type: str,
                                 affected_environments: Set[str],
                                 deployment_requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate success criteria for a fix strategy."""
        criteria = [
            {
                "name": "Deployment Success Rate",
                "description": f"Successful deployments to {env_type} environments",
                "target": "100% success rate for all deployments",
                "measurement": "Track deployment success/failure rates"
            },
            {
                "name": "Environment Consistency",
                "description": f"Configuration consistency across {env_type} environments",
                "target": "100% of environment configurations match templates",
                "measurement": "Automated configuration validation"
            },
            {
                "name": "Deployment Time",
                "description": f"Time required to deploy to {env_type} environments",
                "target": "Deployment time reduced by 20%",
                "measurement": "Track deployment duration metrics"
            }
        ]
        
        # Add specific criteria for production environments
        if env_type == "production":
            criteria.append({
                "name": "Zero-Downtime Deployment",
                "description": "Deploy to production without service interruption",
                "target": "Zero downtime during deployments",
                "measurement": "Monitor service availability during deployments"
            })
        
        return criteria
    
    def _create_cross_environment_strategy(self, 
                                         recommendations: List[DeploymentRecommendation],
                                         environment_mapping: Dict[str, Dict[str, Any]],
                                         deployment_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create a cross-environment deployment strategy."""
        # Collect all affected environments
        all_environments = set()
        for rec in recommendations:
            all_environments.update(rec.affected_environments)
        
        # Create cross-environment strategy
        return {
            "strategy_id": f"strategy_cross_env_{int(time.time())}",
            "name": "Cross-Environment Deployment Strategy",
            "description": "Comprehensive strategy to address deployment issues across all environment types",
            "priority": "high",
            "affected_environments": list(all_environments),
            "environment_type": "all",
            "related_recommendations": [r.recommendation_id for r in recommendations],
            "implementation_phases": [
                {
                    "phase": 1,
                    "name": "Deployment Process Standardization",
                    "description": "Establish standardized deployment process across all environments",
                    "tasks": [
                        "Implement Infrastructure as Code for all environments",
                        "Create environment templates for each environment type",
                        "Establish configuration validation across environments",
                        "Implement automated deployment validation"
                    ],
                    "timeline": "Short-term",
                    "related_recommendations": []
                },
                {
                    "phase": 2,
                    "name": "Continuous Deployment Pipeline",
                    "description": "Implement continuous deployment with automated progression",
                    "tasks": [
                        "Create automated deployment pipeline across environments",
                        "Implement progressive deployment with validation gates",
                        "Establish deployment metrics and monitoring",
                        "Create comprehensive deployment testing framework"
                    ],
                    "timeline": "Medium-term",
                    "related_recommendations": []
                },
                {
                    "phase": 3,
                    "name": "Advanced Deployment Practices",
                    "description": "Implement advanced deployment practices for reliability",
                    "tasks": [
                        "Implement canary deployments",
                        "Create automated rollback mechanisms",
                        "Establish deployment feature flags",
                        "Implement deployment impact analysis"
                    ],
                    "timeline": "Long-term",
                    "related_recommendations": []
                }
            ],
            "success_criteria": [
                {
                    "name": "Environment Consistency",
                    "description": "Configuration consistency across all environments",
                    "target": "100% of environment configurations managed as code",
                    "measurement": "Automated configuration validation"
                },
                {
                    "name": "Deployment Success Rate",
                    "description": "Successful deployments across all environments",
                    "target": "99.9% success rate for all deployments",
                    "measurement": "Track deployment success/failure rates"
                },
                {
                    "name": "Cross-Environment Promotion",
                    "description": "Successful promotion of releases across environments",
                    "target": "Zero promotion failures between environments",
                    "measurement": "Track promotion metrics in deployment pipeline"
                }
            ]
        }
    
    def _create_summary(self, 
                       recommendations: List[DeploymentRecommendation],
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
        
        # Count affected environments by type
        environment_issues = {}
        for rec in recommendations:
            for env_id in rec.affected_environments:
                if env_id not in environment_issues:
                    environment_issues[env_id] = 0
                environment_issues[env_id] += 1
        
        return {
            "total_patterns": len(analysis_report.get("patterns", [])),
            "total_recommendations": len(recommendations),
            "high_priority_recommendations": priority_counts["high"],
            "medium_priority_recommendations": priority_counts["medium"],
            "low_priority_recommendations": priority_counts["low"],
            "critical_issues": priority_counts["high"],
            "affected_environment_count": len(environment_issues),
            "failure_rate": statistics.get("failure_rate", 0),
            "timestamp": datetime.now().isoformat()
        }
    
    def _extract_critical_issues(self, recommendations: List[DeploymentRecommendation]) -> List[Dict[str, Any]]:
        """Extract critical issues for executive summary."""
        critical_issues = []
        
        for rec in recommendations:
            if rec.priority == "high":
                critical_issues.append({
                    "title": rec.title,
                    "description": rec.description,
                    "recommendation_id": rec.recommendation_id,
                    "affected_environments": len(rec.affected_environments),
                    "affected_components": len(rec.affected_components),
                    "deployment_impact": rec.deployment_impact
                })
        
        return critical_issues
    
    def _assess_environments(self, 
                           recommendations: List[DeploymentRecommendation],
                           environment_mapping: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Create environment-specific assessments."""
        environment_assessments = {}
        
        # Group recommendations by environment
        recs_by_environment = {}
        for rec in recommendations:
            for env_id in rec.affected_environments:
                if env_id not in recs_by_environment:
                    recs_by_environment[env_id] = []
                recs_by_environment[env_id].append(rec)
        
        # Create assessment for each environment
        for env_id, env_recs in recs_by_environment.items():
            env = environment_mapping.get(env_id, {})
            env_name = env.get("name", f"Environment {env_id}")
            env_type = env.get("type", "unknown")
            
            # Count high priority recommendations
            high_priority_count = sum(1 for r in env_recs if r.priority == "high")
            
            # Determine health status
            if high_priority_count > 2:
                health_status = "critical"
            elif high_priority_count > 0:
                health_status = "unhealthy"
            elif len(env_recs) > 2:
                health_status = "needs_attention"
            elif len(env_recs) > 0:
                health_status = "fair"
            else:
                health_status = "healthy"
            
            environment_assessments[env_id] = {
                "environment_id": env_id,
                "environment_name": env_name,
                "environment_type": env_type,
                "health_status": health_status,
                "recommendation_count": len(env_recs),
                "high_priority_count": high_priority_count,
                "recommendation_ids": [r.recommendation_id for r in env_recs]
            }
        
        return environment_assessments