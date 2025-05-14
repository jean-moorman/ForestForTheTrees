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
class DeploymentFailurePattern:
    pattern_id: str
    pattern_name: str
    description: str
    frequency: int = 0
    affected_components: Set[str] = field(default_factory=set)
    affected_environments: Set[str] = field(default_factory=set)
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
            "affected_environments": list(self.affected_environments),
            "root_causes": self.root_causes,
            "priority": self.priority
        }


class DeploymentTestAnalysisAgent(PhaseTwoAgentBase):
    """
    Analyzes deployment test failures.
    
    Responsibilities:
    - Analyze deployment test failures
    - Identify deployment environment issues
    - Classify deployment failures
    - Generate deployment analysis reports
    """
    
    def __init__(self,
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        """Initialize the deployment test analysis agent."""
        super().__init__(
            "deployment_test_analysis_agent",
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor
        )
        self._failure_patterns: Dict[str, DeploymentFailurePattern] = {}
        
    async def analyze_deployment_failures(self, 
                                         test_results: Dict[str, Any],
                                         components: List[Dict[str, Any]],
                                         environments: List[Dict[str, Any]],
                                         analysis_id: str) -> Dict[str, Any]:
        """
        Analyze deployment test failures to identify patterns and root causes.
        
        Args:
            test_results: Results from deployment test execution
            components: List of components that were deployed
            environments: List of deployment environments tested
            analysis_id: Unique identifier for this analysis
            
        Returns:
            Dictionary containing analysis results
        """
        logger.info(f"Analyzing deployment test failures for analysis ID: {analysis_id}")
        
        start_time = time.time()
        
        # Record analysis start
        await self._metrics_manager.record_metric(
            "deployment_test_analysis:start",
            1.0,
            metadata={
                "analysis_id": analysis_id,
                "total_tests": test_results.get("total_tests", 0),
                "failed_tests": test_results.get("failed_tests", 0),
                "environments": len(environments)
            }
        )
        
        # Extract failed tests
        failed_tests = [test for test in test_results.get("test_details", []) 
                        if not test.get("passed", False)]
        
        if not failed_tests:
            logger.info(f"No failed deployment tests to analyze for {analysis_id}")
            return {
                "status": "success",
                "message": "No failed deployment tests to analyze",
                "analysis_id": analysis_id,
                "patterns": [],
                "statistics": {
                    "total_tests": test_results.get("total_tests", 0),
                    "failed_tests": 0
                }
            }
        
        # Create component and environment mappings
        component_mapping = {component.get("id", ""): component for component in components}
        environment_mapping = {env.get("id", ""): env for env in environments}
        
        # Identify components and environments involved in failures
        affected_components = self._identify_affected_components(failed_tests, component_mapping)
        affected_environments = self._identify_affected_environments(failed_tests, environment_mapping)
        
        # Extract patterns from test failures
        patterns = self._extract_failure_patterns(
            failed_tests, affected_components, affected_environments)
        
        # Classify failures by root cause
        classified_patterns = self._classify_by_root_cause(
            patterns, component_mapping, environment_mapping)
        
        # Calculate statistics
        statistics = self._calculate_statistics(
            test_results, failed_tests, classified_patterns, environments)
        
        # Generate analysis report
        analysis_report = {
            "status": "success",
            "analysis_id": analysis_id,
            "timestamp": datetime.now().isoformat(),
            "execution_time_seconds": time.time() - start_time,
            "patterns": [pattern.to_dict() for pattern in classified_patterns],
            "statistics": statistics,
            "affected_components": [comp_id for comp_id, _ in affected_components],
            "affected_environments": [env_id for env_id, _ in affected_environments],
            "environment_specific_issues": self._identify_environment_specific_issues(
                classified_patterns, environment_mapping),
            "recommendations": self._generate_recommendations(
                classified_patterns, environment_mapping)
        }
        
        # Cache the analysis results
        await self._cache_manager.set(
            f"deployment_test_analysis:{analysis_id}",
            analysis_report,
            ttl=3600  # Cache for 1 hour
        )
        
        # Record analysis completion
        await self._metrics_manager.record_metric(
            "deployment_test_analysis:complete",
            1.0,
            metadata={
                "analysis_id": analysis_id,
                "patterns_found": len(classified_patterns),
                "execution_time": time.time() - start_time
            }
        )
        
        logger.info(f"Completed deployment test failure analysis {analysis_id} - found {len(classified_patterns)} patterns")
        return analysis_report
    
    def _identify_affected_components(self, 
                                     failed_tests: List[Dict[str, Any]],
                                     component_mapping: Dict[str, Dict[str, Any]]) -> List[Tuple[str, int]]:
        """Identify components affected by deployment failures."""
        component_failures = Counter()
        
        for test in failed_tests:
            # Extract component IDs from test metadata
            test_components = test.get("components", [])
            
            for comp_id in test_components:
                component_failures[comp_id] += 1
        
        # Return sorted list of (component_id, failure_count) tuples
        return sorted(component_failures.items(), key=lambda x: x[1], reverse=True)
    
    def _identify_affected_environments(self, 
                                       failed_tests: List[Dict[str, Any]],
                                       environment_mapping: Dict[str, Dict[str, Any]]) -> List[Tuple[str, int]]:
        """Identify environments affected by deployment failures."""
        environment_failures = Counter()
        
        for test in failed_tests:
            # Extract environment ID from test metadata
            environment_id = test.get("environment", "")
            
            if environment_id:
                environment_failures[environment_id] += 1
        
        # Return sorted list of (environment_id, failure_count) tuples
        return sorted(environment_failures.items(), key=lambda x: x[1], reverse=True)
    
    def _extract_failure_patterns(self, 
                                 failed_tests: List[Dict[str, Any]], 
                                 affected_components: List[Tuple[str, int]],
                                 affected_environments: List[Tuple[str, int]]) -> List[DeploymentFailurePattern]:
        """
        Extract patterns from deployment test failures.
        
        This method identifies common patterns in deployment failures, categorizing them
        by failure type, affected environments, and components.
        """
        patterns = []
        
        # Group by failure type and message
        failure_messages = Counter()
        for test in failed_tests:
            failure_type = test.get("failure_type", "unknown")
            output = test.get("output", "").strip()
            message = f"{failure_type}: {output[:100]}"  # Truncate long messages
            failure_messages[message] += 1
        
        # Create patterns for common failure messages
        for i, (message, count) in enumerate(failure_messages.most_common()):
            # Basic pattern detection based on error message
            pattern_name = f"Pattern #{i+1}: {message[:50]}..." if len(message) > 50 else f"Pattern #{i+1}: {message}"
            
            # Determine affected components and environments for this pattern
            affected_pattern_components = set()
            affected_pattern_environments = set()
            
            for test in failed_tests:
                failure_type = test.get("failure_type", "unknown")
                output = test.get("output", "").strip()
                test_message = f"{failure_type}: {output[:100]}"
                
                if test_message == message:
                    # Add components from this test
                    affected_pattern_components.update(test.get("components", []))
                    
                    # Add environment from this test
                    environment_id = test.get("environment", "")
                    if environment_id:
                        affected_pattern_environments.add(environment_id)
            
            # Create pattern
            pattern = DeploymentFailurePattern(
                pattern_id=f"pattern_{int(time.time())}_{i}",
                pattern_name=pattern_name,
                description=f"Deployment failure pattern: {message}",
                frequency=count,
                affected_components=affected_pattern_components,
                affected_environments=affected_pattern_environments
            )
            
            patterns.append(pattern)
        
        return patterns
    
    def _classify_by_root_cause(self, 
                               patterns: List[DeploymentFailurePattern],
                               component_mapping: Dict[str, Dict[str, Any]],
                               environment_mapping: Dict[str, Dict[str, Any]]) -> List[DeploymentFailurePattern]:
        """
        Classify deployment failure patterns by probable root cause.
        
        This method analyzes patterns to determine likely root causes of deployment failures,
        taking into account both component characteristics and deployment environment factors.
        """
        classified_patterns = []
        
        for pattern in patterns:
            # Create a copy to modify
            updated_pattern = DeploymentFailurePattern(
                pattern_id=pattern.pattern_id,
                pattern_name=pattern.pattern_name,
                description=pattern.description,
                frequency=pattern.frequency,
                affected_components=pattern.affected_components.copy(),
                affected_environments=pattern.affected_environments.copy()
            )
            
            # Analyze root causes based on pattern characteristics
            root_causes = []
            
            # Check for environment configuration issues
            env_config_issues = self._check_for_environment_configuration_issues(
                pattern, environment_mapping)
            if env_config_issues:
                root_causes.append(env_config_issues)
            
            # Check for dependency issues
            dependency_issues = self._check_for_deployment_dependency_issues(
                pattern, component_mapping)
            if dependency_issues:
                root_causes.append(dependency_issues)
            
            # Check for compatibility issues
            compatibility_issues = self._check_for_compatibility_issues(
                pattern, component_mapping, environment_mapping)
            if compatibility_issues:
                root_causes.append(compatibility_issues)
            
            # Check for resource issues
            resource_issues = self._check_for_resource_issues(pattern, environment_mapping)
            if resource_issues:
                root_causes.append(resource_issues)
            
            # Add root causes to the pattern
            updated_pattern.root_causes = root_causes
            
            # Set priority based on frequency and impact
            if len(updated_pattern.affected_environments) > 2 or updated_pattern.frequency > 5:
                updated_pattern.priority = "high"
            elif len(updated_pattern.affected_environments) <= 1 and updated_pattern.frequency <= 2:
                updated_pattern.priority = "low"
            else:
                updated_pattern.priority = "medium"
                
            classified_patterns.append(updated_pattern)
            
        return classified_patterns
    
    def _check_for_environment_configuration_issues(self, 
                                                  pattern: DeploymentFailurePattern,
                                                  environment_mapping: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Check if the pattern indicates environment configuration issues."""
        if not pattern.affected_environments:
            return None
            
        # Look for configuration-related keywords in the pattern description
        config_keywords = ["config", "configuration", "setting", "parameter", "environment variable", 
                          "env var", ".env", "yaml", "property"]
        
        if any(keyword in pattern.description.lower() for keyword in config_keywords):
            affected_envs = []
            for env_id in pattern.affected_environments:
                env = environment_mapping.get(env_id, {})
                affected_envs.append({
                    "id": env_id,
                    "name": env.get("name", ""),
                    "type": env.get("type", "unknown")
                })
                
            return {
                "type": "environment_configuration",
                "description": "Environment configuration issue",
                "affected_environments": affected_envs,
                "confidence": "high"
            }
        
        # If the pattern affects only specific environments, it might be a configuration issue
        if 1 <= len(pattern.affected_environments) <= 2:
            affected_envs = []
            for env_id in pattern.affected_environments:
                env = environment_mapping.get(env_id, {})
                affected_envs.append({
                    "id": env_id,
                    "name": env.get("name", ""),
                    "type": env.get("type", "unknown")
                })
                
            return {
                "type": "environment_configuration",
                "description": "Possible environment-specific configuration issue",
                "affected_environments": affected_envs,
                "confidence": "medium"
            }
            
        return None
    
    def _check_for_deployment_dependency_issues(self, 
                                              pattern: DeploymentFailurePattern,
                                              component_mapping: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Check if the pattern indicates deployment dependency issues."""
        # Look for dependency-related keywords
        dependency_keywords = ["dependency", "missing", "not found", "required", "depends on", 
                              "version", "incompatible", "package", "library", "module"]
        
        if any(keyword in pattern.description.lower() for keyword in dependency_keywords):
            affected_comps = []
            for comp_id in pattern.affected_components:
                component = component_mapping.get(comp_id, {})
                dependencies = component.get("dependencies", [])
                affected_comps.append({
                    "id": comp_id,
                    "name": component.get("name", ""),
                    "dependencies": dependencies
                })
                
            return {
                "type": "deployment_dependency",
                "description": "Dependency issue during deployment",
                "affected_components": affected_comps,
                "confidence": "high"
            }
        
        # If multiple components with dependencies are affected, it might be a dependency issue
        components_with_dependencies = []
        for comp_id in pattern.affected_components:
            component = component_mapping.get(comp_id, {})
            dependencies = component.get("dependencies", [])
            if dependencies:
                components_with_dependencies.append({
                    "id": comp_id,
                    "name": component.get("name", ""),
                    "dependencies": dependencies
                })
        
        if len(components_with_dependencies) >= 2:
            return {
                "type": "deployment_dependency",
                "description": "Possible dependency conflicts between components",
                "affected_components": components_with_dependencies,
                "confidence": "medium"
            }
            
        return None
    
    def _check_for_compatibility_issues(self, 
                                       pattern: DeploymentFailurePattern,
                                       component_mapping: Dict[str, Dict[str, Any]],
                                       environment_mapping: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Check if the pattern indicates compatibility issues between components and environments."""
        # Look for compatibility-related keywords
        compatibility_keywords = ["compatibility", "not compatible", "unsupported", "requires", 
                                 "platform", "architecture", "version mismatch", "runtime"]
        
        if any(keyword in pattern.description.lower() for keyword in compatibility_keywords):
            affected_envs = []
            for env_id in pattern.affected_environments:
                env = environment_mapping.get(env_id, {})
                affected_envs.append({
                    "id": env_id,
                    "name": env.get("name", ""),
                    "type": env.get("type", ""),
                    "platform": env.get("platform", ""),
                    "version": env.get("version", "")
                })
                
            affected_comps = []
            for comp_id in pattern.affected_components:
                component = component_mapping.get(comp_id, {})
                affected_comps.append({
                    "id": comp_id,
                    "name": component.get("name", ""),
                    "requirements": component.get("requirements", {})
                })
                
            return {
                "type": "compatibility",
                "description": "Component-environment compatibility issue",
                "affected_environments": affected_envs,
                "affected_components": affected_comps,
                "confidence": "high"
            }
        
        # If pattern affects components across multiple environment types, it might be compatibility
        if len(pattern.affected_environments) >= 2:
            env_types = set()
            for env_id in pattern.affected_environments:
                env = environment_mapping.get(env_id, {})
                env_type = env.get("type", "")
                if env_type:
                    env_types.add(env_type)
            
            if len(env_types) >= 2:
                return {
                    "type": "compatibility",
                    "description": "Possible cross-environment compatibility issue",
                    "environment_types": list(env_types),
                    "confidence": "medium"
                }
                
        return None
    
    def _check_for_resource_issues(self, 
                                  pattern: DeploymentFailurePattern,
                                  environment_mapping: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Check if the pattern indicates resource allocation or availability issues."""
        # Look for resource-related keywords
        resource_keywords = ["resource", "memory", "cpu", "disk", "storage", "quota", "limit", 
                            "exceeded", "insufficient", "capacity", "out of", "allocation"]
        
        if any(keyword in pattern.description.lower() for keyword in resource_keywords):
            affected_envs = []
            for env_id in pattern.affected_environments:
                env = environment_mapping.get(env_id, {})
                affected_envs.append({
                    "id": env_id,
                    "name": env.get("name", ""),
                    "resources": env.get("resources", {})
                })
                
            return {
                "type": "resource",
                "description": "Resource allocation or availability issue",
                "affected_environments": affected_envs,
                "confidence": "high"
            }
        
        return None
    
    def _calculate_statistics(self, 
                             test_results: Dict[str, Any],
                             failed_tests: List[Dict[str, Any]],
                             patterns: List[DeploymentFailurePattern],
                             environments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics about the deployment test failures and patterns."""
        total_tests = test_results.get("total_tests", 0)
        total_failed = len(failed_tests)
        
        # Calculate failure rate
        failure_rate = (total_failed / total_tests) * 100 if total_tests > 0 else 0
        
        # Count patterns by priority
        priorities = Counter()
        for pattern in patterns:
            priorities[pattern.priority] += 1
        
        # Collect affected components and environments
        all_affected_components = set()
        all_affected_environments = set()
        
        for pattern in patterns:
            all_affected_components.update(pattern.affected_components)
            all_affected_environments.update(pattern.affected_environments)
        
        # Calculate failure rates by environment
        env_failure_rates = {}
        for env in environments:
            env_id = env.get("id", "")
            env_name = env.get("name", "")
            
            # Count tests and failures for this environment
            env_tests = [test for test in test_results.get("test_details", []) 
                        if test.get("environment") == env_id]
            env_failures = [test for test in env_tests if not test.get("passed", False)]
            
            total_env_tests = len(env_tests)
            total_env_failures = len(env_failures)
            
            env_failure_rate = 0
            if total_env_tests > 0:
                env_failure_rate = (total_env_failures / total_env_tests) * 100
                
            env_failure_rates[env_id] = {
                "environment_id": env_id,
                "environment_name": env_name,
                "total_tests": total_env_tests,
                "failed_tests": total_env_failures,
                "failure_rate": env_failure_rate
            }
        
        return {
            "total_tests": total_tests,
            "failed_tests": total_failed,
            "failure_rate": round(failure_rate, 2),
            "unique_failure_patterns": len(patterns),
            "affected_component_count": len(all_affected_components),
            "affected_environment_count": len(all_affected_environments),
            "patterns_by_priority": {
                "high": priorities["high"],
                "medium": priorities["medium"],
                "low": priorities["low"]
            },
            "environment_failure_rates": env_failure_rates
        }
    
    def _identify_environment_specific_issues(self, 
                                            patterns: List[DeploymentFailurePattern],
                                            environment_mapping: Dict[str, Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Identify issues that are specific to certain environments."""
        environment_issues = {}
        
        # Create a mapping of patterns by environment
        for pattern in patterns:
            for env_id in pattern.affected_environments:
                if env_id not in environment_issues:
                    environment_issues[env_id] = []
                
                # Determine if this issue is specific to this environment
                is_env_specific = len(pattern.affected_environments) == 1
                
                issue = {
                    "pattern_id": pattern.pattern_id,
                    "pattern_name": pattern.pattern_name,
                    "description": pattern.description,
                    "priority": pattern.priority,
                    "environment_specific": is_env_specific,
                    "root_causes": pattern.root_causes
                }
                
                environment_issues[env_id].append(issue)
        
        # Add environment metadata
        result = {}
        for env_id, issues in environment_issues.items():
            env = environment_mapping.get(env_id, {})
            env_name = env.get("name", f"Environment {env_id}")
            env_type = env.get("type", "unknown")
            
            result[env_id] = {
                "environment_id": env_id,
                "environment_name": env_name,
                "environment_type": env_type,
                "issues": issues,
                "issue_count": len(issues),
                "high_priority_issues": sum(1 for issue in issues if issue["priority"] == "high")
            }
            
        return result
    
    def _generate_recommendations(self, 
                                patterns: List[DeploymentFailurePattern],
                                environment_mapping: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate recommendations for addressing deployment failures."""
        recommendations = []
        
        # Generate recommendations for high priority patterns first
        high_priority_patterns = [p for p in patterns if p.priority == "high"]
        for pattern in high_priority_patterns:
            for root_cause in pattern.root_causes:
                cause_type = root_cause.get("type", "")
                
                if cause_type == "environment_configuration":
                    recommendations.append({
                        "priority": "high",
                        "type": "configuration",
                        "title": "Fix environment configuration issues",
                        "description": "Resolve environment configuration issues causing deployment failures",
                        "action_items": [
                            f"Verify configuration in environment {env_id}" 
                            for env_id in pattern.affected_environments
                        ],
                        "affected_environments": list(pattern.affected_environments),
                        "related_pattern": pattern.pattern_id
                    })
                    
                elif cause_type == "deployment_dependency":
                    recommendations.append({
                        "priority": "high",
                        "type": "dependency",
                        "title": "Resolve deployment dependency issues",
                        "description": "Fix dependency conflicts and missing dependencies",
                        "action_items": [
                            "Verify all required dependencies are properly installed",
                            "Check for version conflicts between components",
                            "Ensure dependency resolution order is correct during deployment"
                        ],
                        "affected_components": list(pattern.affected_components),
                        "related_pattern": pattern.pattern_id
                    })
                    
                elif cause_type == "compatibility":
                    recommendations.append({
                        "priority": "high",
                        "type": "compatibility",
                        "title": "Address component-environment compatibility issues",
                        "description": "Resolve compatibility issues between components and deployment environments",
                        "action_items": [
                            "Verify component requirements match environment capabilities",
                            "Update components to support target environments",
                            "Consider containerization to reduce environment dependencies"
                        ],
                        "affected_components": list(pattern.affected_components),
                        "affected_environments": list(pattern.affected_environments),
                        "related_pattern": pattern.pattern_id
                    })
                    
                elif cause_type == "resource":
                    recommendations.append({
                        "priority": "high",
                        "type": "resource",
                        "title": "Resolve resource allocation issues",
                        "description": "Address resource constraints causing deployment failures",
                        "action_items": [
                            "Increase resource allocation for affected environments",
                            "Optimize component resource usage",
                            "Implement resource monitoring and scaling"
                        ],
                        "affected_environments": list(pattern.affected_environments),
                        "related_pattern": pattern.pattern_id
                    })
        
        # Add environment-specific recommendations
        env_specific_recommendations = self._generate_environment_specific_recommendations(
            patterns, environment_mapping)
        recommendations.extend(env_specific_recommendations)
        
        # Add general recommendations if needed
        if len(patterns) > 3:
            recommendations.append({
                "priority": "medium",
                "type": "process",
                "title": "Improve deployment testing process",
                "description": "Enhance deployment testing to catch issues earlier",
                "action_items": [
                    "Implement pre-deployment validation checks",
                    "Add smoke tests for each deployment environment",
                    "Create standardized deployment environment configurations",
                    "Implement continuous deployment testing"
                ],
                "related_pattern": None
            })
        
        return recommendations
    
    def _generate_environment_specific_recommendations(self, 
                                                     patterns: List[DeploymentFailurePattern],
                                                     environment_mapping: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate recommendations for specific deployment environments."""
        env_recommendations = []
        
        # Group patterns by environment
        patterns_by_env = {}
        for pattern in patterns:
            for env_id in pattern.affected_environments:
                if env_id not in patterns_by_env:
                    patterns_by_env[env_id] = []
                patterns_by_env[env_id].append(pattern)
        
        # Generate recommendations for environments with multiple issues
        for env_id, env_patterns in patterns_by_env.items():
            if len(env_patterns) < 2:
                continue
                
            env = environment_mapping.get(env_id, {})
            env_name = env.get("name", f"Environment {env_id}")
            env_type = env.get("type", "unknown")
            
            # Count high priority patterns for this environment
            high_priority_count = sum(1 for p in env_patterns if p.priority == "high")
            priority = "high" if high_priority_count > 0 else "medium"
            
            # Create environment-specific recommendation
            recommendation = {
                "priority": priority,
                "type": "environment",
                "title": f"Resolve multiple issues in {env_name}",
                "description": f"Address {len(env_patterns)} deployment issues specific to the {env_type} environment",
                "action_items": [
                    f"Fix {p.pattern_name}" for p in env_patterns if p.priority == "high"
                ],
                "affected_environment": env_id,
                "environment_type": env_type,
                "related_patterns": [p.pattern_id for p in env_patterns]
            }
            
            # Add environment-specific action items based on environment type
            if env_type == "production":
                recommendation["action_items"].extend([
                    "Implement canary deployments to catch issues earlier",
                    "Add production-specific validation checks",
                    "Update rollback procedures for quicker recovery"
                ])
            elif env_type == "staging":
                recommendation["action_items"].extend([
                    "Ensure staging mirrors production configuration",
                    "Implement comprehensive pre-production validation"
                ])
            elif env_type == "development":
                recommendation["action_items"].extend([
                    "Standardize development environment setup",
                    "Create development environment validation checks"
                ])
            
            env_recommendations.append(recommendation)
        
        return env_recommendations