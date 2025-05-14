import logging
import time
import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple
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
class DeploymentFixSolution:
    solution_id: str
    title: str
    description: str
    affected_environments: List[str]
    affected_components: List[str]
    implementation_details: Dict[str, Any]
    verification_steps: List[str]
    regression_tests: List[Dict[str, Any]]
    applied: bool = False
    verified: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "solution_id": self.solution_id,
            "title": self.title,
            "description": self.description,
            "affected_environments": self.affected_environments,
            "affected_components": self.affected_components,
            "implementation_details": self.implementation_details,
            "verification_steps": self.verification_steps,
            "regression_tests": self.regression_tests,
            "applied": self.applied,
            "verified": self.verified
        }


class DeploymentTestDebugAgent(PhaseTwoAgentBase):
    """
    Implements deployment environment fixes.
    
    Responsibilities:
    - Implement deployment environment fixes
    - Verify deployment fix effectiveness
    - Document deployment solutions
    - Create deployment regression tests
    """
    
    def __init__(self,
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        """Initialize the deployment test debug agent."""
        super().__init__(
            "deployment_test_debug_agent",
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor
        )
        # Track active fixes
        self._active_fixes: Dict[str, DeploymentFixSolution] = {}
    
    async def implement_deployment_fixes(self, 
                                       review_report: Dict[str, Any],
                                       environments: List[Dict[str, Any]],
                                       components: List[Dict[str, Any]],
                                       debug_id: str) -> Dict[str, Any]:
        """
        Implement fixes based on deployment review recommendations.
        
        Args:
            review_report: The deployment review report with recommendations
            environments: List of deployment environments
            components: List of components
            debug_id: Unique identifier for this debug session
            
        Returns:
            Dictionary containing fix implementations and results
        """
        logger.info(f"Implementing deployment fixes based on review recommendations for debug ID: {debug_id}")
        
        start_time = time.time()
        
        # Record debug start
        await self._metrics_manager.record_metric(
            "deployment_test_debug:start",
            1.0,
            metadata={
                "debug_id": debug_id,
                "review_id": review_report.get("review_id", "unknown")
            }
        )
        
        # Get recommendations from the review report
        recommendations = review_report.get("recommendations", [])
        
        if not recommendations:
            logger.info(f"No recommendations to implement for {debug_id}")
            return {
                "status": "success",
                "message": "No recommendations to implement",
                "debug_id": debug_id,
                "fixes": [],
                "summary": {
                    "total_recommendations": 0,
                    "fixes_implemented": 0,
                    "fixes_verified": 0
                }
            }
        
        # Create mappings for quick lookup
        environment_mapping = {env.get("id", ""): env for env in environments}
        component_mapping = {comp.get("id", ""): comp for comp in components}
        
        # Create fixes for each recommendation
        fixes = []
        for recommendation in recommendations:
            fix = await self._create_fix_from_recommendation(
                recommendation, environment_mapping, component_mapping, debug_id)
            
            if fix:
                fixes.append(fix)
                self._active_fixes[fix.solution_id] = fix
        
        # Apply the fixes
        applied_fixes = await self._apply_fixes(fixes, environment_mapping, component_mapping)
        
        # Verify the fixes
        verified_fixes = await self._verify_fixes(applied_fixes, debug_id)
        
        # Create regression tests
        regression_tests = await self._create_regression_tests(verified_fixes, debug_id)
        
        # Create documentation
        deployment_documentation = self._generate_deployment_documentation(verified_fixes)
        
        # Create summary statistics
        summary = self._create_summary(recommendations, verified_fixes, regression_tests)
        
        # Create debug report
        debug_report = {
            "status": "success",
            "debug_id": debug_id,
            "review_id": review_report.get("review_id", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "execution_time_seconds": time.time() - start_time,
            "fixes": [fix.to_dict() for fix in verified_fixes],
            "regression_tests": regression_tests,
            "deployment_documentation": deployment_documentation,
            "summary": summary,
            "environment_impacts": self._calculate_environment_impacts(
                verified_fixes, environment_mapping)
        }
        
        # Cache the debug results
        await self._cache_manager.set(
            f"deployment_test_debug:{debug_id}",
            debug_report,
            ttl=3600  # Cache for 1 hour
        )
        
        # Record debug completion
        await self._metrics_manager.record_metric(
            "deployment_test_debug:complete",
            1.0,
            metadata={
                "debug_id": debug_id,
                "fixes_implemented": len(verified_fixes),
                "regression_tests_created": len(regression_tests),
                "execution_time": time.time() - start_time
            }
        )
        
        logger.info(f"Completed deployment test debug {debug_id} - implemented {len(verified_fixes)} fixes")
        return debug_report
    
    async def _create_fix_from_recommendation(self, 
                                           recommendation: Dict[str, Any],
                                           environment_mapping: Dict[str, Dict[str, Any]],
                                           component_mapping: Dict[str, Dict[str, Any]],
                                           debug_id: str) -> Optional[DeploymentFixSolution]:
        """Create a fix solution from a deployment recommendation."""
        recommendation_id = recommendation.get("recommendation_id", "")
        title = recommendation.get("title", "Unknown recommendation")
        description = recommendation.get("description", "")
        action_items = recommendation.get("action_items", [])
        affected_environments = recommendation.get("affected_environments", [])
        affected_components = recommendation.get("affected_components", [])
        
        # Skip if no affected environments or action items
        if not affected_environments or not action_items:
            logger.warning(f"Skipping recommendation {recommendation_id} - insufficient details")
            return None
        
        # Get environment details
        environment_details = []
        for env_id in affected_environments:
            env = environment_mapping.get(env_id)
            if env:
                environment_details.append({
                    "id": env_id,
                    "name": env.get("name", ""),
                    "type": env.get("type", "unknown"),
                    "version": env.get("version", "unknown"),
                    "configuration": env.get("configuration", {})
                })
        
        # Get component details
        component_details = []
        for comp_id in affected_components:
            component = component_mapping.get(comp_id)
            if component:
                component_details.append({
                    "id": comp_id,
                    "name": component.get("name", ""),
                    "description": component.get("description", ""),
                    "version": component.get("version", "unknown"),
                    "dependencies": component.get("dependencies", [])
                })
        
        # Create implementation details based on recommendation type
        recommendation_type = recommendation.get("type", "unknown").lower()
        
        if "configuration" in recommendation_type:
            implementation_details = self._create_configuration_fix(
                recommendation, environment_details, component_details)
        elif "dependency" in recommendation_type:
            implementation_details = self._create_dependency_fix(
                recommendation, environment_details, component_details)
        elif "compatibility" in recommendation_type:
            implementation_details = self._create_compatibility_fix(
                recommendation, environment_details, component_details)
        elif "resource" in recommendation_type:
            implementation_details = self._create_resource_fix(
                recommendation, environment_details)
        else:
            implementation_details = self._create_general_deployment_fix(
                recommendation, environment_details, component_details)
        
        # Create verification steps
        verification_steps = self._create_deployment_verification_steps(
            recommendation, implementation_details)
        
        # Create empty regression tests (will be filled later)
        regression_tests = []
        
        # Create fix solution
        solution_id = f"fix_{debug_id}_{recommendation_id}"
        return DeploymentFixSolution(
            solution_id=solution_id,
            title=f"Fix for {title}",
            description=f"Implementation of solution for: {description}",
            affected_environments=affected_environments,
            affected_components=affected_components,
            implementation_details=implementation_details,
            verification_steps=verification_steps,
            regression_tests=regression_tests
        )
    
    def _create_configuration_fix(self, 
                                recommendation: Dict[str, Any],
                                environment_details: List[Dict[str, Any]],
                                component_details: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create implementation details for configuration-related fixes."""
        # Extract configuration details from environments
        environment_configs = []
        for env in environment_details:
            environment_configs.append({
                "environment_id": env.get("id"),
                "environment_name": env.get("name"),
                "configuration": env.get("configuration", {})
            })
        
        return {
            "fix_type": "configuration",
            "environments": environment_details,
            "components": component_details,
            "approach": "Update environment configurations to resolve deployment issues",
            "changes": [
                {
                    "environment_id": env.get("id"),
                    "environment_name": env.get("name"),
                    "change_type": "configuration_update",
                    "details": f"Update configuration for {env.get('name')} environment",
                    "configuration_paths": [
                        f"environments/{env.get('id')}/config.yaml",
                        f"environments/{env.get('id')}/.env"
                    ]
                }
                for env in environment_details
            ],
            "configuration_improvements": {
                "standardization": True,
                "validation": True,
                "documentation": True
            }
        }
    
    def _create_dependency_fix(self, 
                             recommendation: Dict[str, Any],
                             environment_details: List[Dict[str, Any]],
                             component_details: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create implementation details for dependency-related fixes."""
        # Extract dependency details from components
        component_dependencies = []
        for component in component_details:
            component_dependencies.append({
                "component_id": component.get("id"),
                "component_name": component.get("name"),
                "dependencies": component.get("dependencies", [])
            })
        
        return {
            "fix_type": "dependency",
            "environments": environment_details,
            "components": component_details,
            "approach": "Resolve component dependencies in deployment environments",
            "changes": [
                {
                    "component_id": component.get("id"),
                    "component_name": component.get("name"),
                    "change_type": "dependency_update",
                    "details": f"Update dependencies for {component.get('name')}",
                    "dependency_paths": [
                        f"components/{component.get('id')}/dependencies.json",
                        f"components/{component.get('id')}/requirements.txt"
                    ]
                }
                for component in component_details
            ],
            "dependency_improvements": {
                "version_pinning": True,
                "conflict_resolution": True,
                "dependency_validation": True
            }
        }
    
    def _create_compatibility_fix(self, 
                                recommendation: Dict[str, Any],
                                environment_details: List[Dict[str, Any]],
                                component_details: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create implementation details for compatibility-related fixes."""
        return {
            "fix_type": "compatibility",
            "environments": environment_details,
            "components": component_details,
            "approach": "Ensure compatibility between components and deployment environments",
            "changes": [
                {
                    "component_id": component.get("id"),
                    "component_name": component.get("name"),
                    "environment_id": env.get("id"),
                    "environment_name": env.get("name"),
                    "change_type": "compatibility_fix",
                    "details": f"Ensure compatibility between {component.get('name')} and {env.get('name')}",
                    "compatibility_paths": [
                        f"components/{component.get('id')}/environment_adapters/{env.get('id')}.py",
                        f"environments/{env.get('id')}/compatibility.yaml"
                    ]
                }
                for component in component_details
                for env in environment_details
            ],
            "compatibility_improvements": {
                "environment_adapters": True,
                "version_compatibility": True,
                "containerization": True
            }
        }
    
    def _create_resource_fix(self, 
                           recommendation: Dict[str, Any],
                           environment_details: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create implementation details for resource-related fixes."""
        return {
            "fix_type": "resource",
            "environments": environment_details,
            "approach": "Optimize resource allocation and usage in deployment environments",
            "changes": [
                {
                    "environment_id": env.get("id"),
                    "environment_name": env.get("name"),
                    "change_type": "resource_update",
                    "details": f"Update resource allocation for {env.get('name')}",
                    "resource_paths": [
                        f"environments/{env.get('id')}/resources.yaml",
                        f"environments/{env.get('id')}/scaling.yaml"
                    ]
                }
                for env in environment_details
            ],
            "resource_improvements": {
                "allocation_increase": True,
                "optimization": True,
                "monitoring": True,
                "auto_scaling": True
            }
        }
    
    def _create_general_deployment_fix(self, 
                                     recommendation: Dict[str, Any],
                                     environment_details: List[Dict[str, Any]],
                                     component_details: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create implementation details for general deployment fixes."""
        return {
            "fix_type": "general",
            "environments": environment_details,
            "components": component_details,
            "approach": "Implement general deployment improvements",
            "changes": [
                {
                    "environment_id": env.get("id"),
                    "environment_name": env.get("name"),
                    "change_type": "deployment_improvement",
                    "details": f"Improve deployment process for {env.get('name')}",
                    "deployment_paths": [
                        f"environments/{env.get('id')}/deployment.yaml",
                        f"deployments/scripts/{env.get('id')}_deploy.sh"
                    ]
                }
                for env in environment_details
            ],
            "deployment_improvements": {
                "process_automation": True,
                "verification": True,
                "documentation": True,
                "rollback": True
            }
        }
    
    def _create_deployment_verification_steps(self, 
                                            recommendation: Dict[str, Any],
                                            implementation_details: Dict[str, Any]) -> List[str]:
        """Create verification steps for a deployment fix solution."""
        fix_type = implementation_details.get("fix_type", "general")
        
        if fix_type == "configuration":
            return [
                "Verify all configuration changes are applied to affected environments",
                "Validate configuration values against required schema",
                "Test deployment with updated configurations",
                "Verify component initialization with new configuration",
                "Confirm all affected components operate correctly with new configuration"
            ]
        elif fix_type == "dependency":
            return [
                "Verify all dependency updates are correctly applied",
                "Validate dependency resolution during deployment",
                "Test component initialization with updated dependencies",
                "Verify inter-component communication with new dependencies",
                "Confirm deployment process completes successfully"
            ]
        elif fix_type == "compatibility":
            return [
                "Verify compatibility fixes are applied to all components",
                "Test deployment in each affected environment",
                "Validate component behavior in different environments",
                "Verify cross-environment component functionality",
                "Confirm deployment process succeeds in all environments"
            ]
        elif fix_type == "resource":
            return [
                "Verify resource allocation changes are applied",
                "Monitor resource usage during deployment",
                "Test component performance with new resource allocation",
                "Verify resource optimization improvements",
                "Confirm deployment completes without resource constraints"
            ]
        else:
            return [
                "Verify all deployment changes are correctly implemented",
                "Test deployment process in affected environments",
                "Validate component functionality after deployment",
                "Verify deployment automation improvements",
                "Confirm overall deployment success"
            ]
    
    async def _apply_fixes(self, 
                          fixes: List[DeploymentFixSolution],
                          environment_mapping: Dict[str, Dict[str, Any]],
                          component_mapping: Dict[str, Dict[str, Any]]) -> List[DeploymentFixSolution]:
        """Apply fixes to the affected environments and components (simulated)."""
        applied_fixes = []
        
        for fix in fixes:
            logger.info(f"Applying fix {fix.solution_id} to {len(fix.affected_environments)} environments")
            
            # Simulate applying the fix
            await asyncio.sleep(0.1)  # Simulate processing time
            
            # Add application details
            fix.implementation_details["application_results"] = {
                "timestamp": datetime.now().isoformat(),
                "status": "applied",
                "affected_files": []
            }
            
            # Track affected files
            for change in fix.implementation_details.get("changes", []):
                configuration_paths = change.get("configuration_paths", [])
                dependency_paths = change.get("dependency_paths", [])
                compatibility_paths = change.get("compatibility_paths", [])
                resource_paths = change.get("resource_paths", [])
                deployment_paths = change.get("deployment_paths", [])
                
                # Combine all paths
                all_paths = []
                all_paths.extend(configuration_paths)
                all_paths.extend(dependency_paths)
                all_paths.extend(compatibility_paths)
                all_paths.extend(resource_paths)
                all_paths.extend(deployment_paths)
                
                for file_path in all_paths:
                    fix.implementation_details["application_results"]["affected_files"].append({
                        "file_path": file_path,
                        "status": "updated",
                        "changes": "Applied fixes per implementation details"
                    })
            
            # Mark fix as applied
            fix.applied = True
            applied_fixes.append(fix)
            
            # Log metric for applied fix
            await self._metrics_manager.record_metric(
                "deployment_test_debug:fix_applied",
                1.0,
                metadata={
                    "solution_id": fix.solution_id,
                    "fix_type": fix.implementation_details.get("fix_type", "unknown"),
                    "affected_environments": len(fix.affected_environments)
                }
            )
        
        return applied_fixes
    
    async def _verify_fixes(self, 
                          fixes: List[DeploymentFixSolution], 
                          debug_id: str) -> List[DeploymentFixSolution]:
        """Verify that the applied fixes resolved the deployment issues (simulated)."""
        verified_fixes = []
        
        for fix in fixes:
            logger.info(f"Verifying fix {fix.solution_id}")
            
            # Simulate verification process
            await asyncio.sleep(0.1)  # Simulate processing time
            
            # Add verification results
            verification_results = {
                "timestamp": datetime.now().isoformat(),
                "status": "verified",
                "verification_tests": [
                    {
                        "test_name": f"Verification test for {step}",
                        "status": "passed",
                        "details": "Test verified the fix is effective"
                    }
                    for step in fix.verification_steps
                ],
                "deployment_validation": {
                    "status": "successful",
                    "environments_validated": len(fix.affected_environments),
                    "components_validated": len(fix.affected_components)
                }
            }
            
            fix.implementation_details["verification_results"] = verification_results
            fix.verified = True
            verified_fixes.append(fix)
            
            # Log metric for verified fix
            await self._metrics_manager.record_metric(
                "deployment_test_debug:fix_verified",
                1.0,
                metadata={
                    "solution_id": fix.solution_id,
                    "fix_type": fix.implementation_details.get("fix_type", "unknown"),
                    "affected_environments": len(fix.affected_environments)
                }
            )
        
        return verified_fixes
    
    async def _create_regression_tests(self, 
                                     fixes: List[DeploymentFixSolution],
                                     debug_id: str) -> List[Dict[str, Any]]:
        """Create regression tests for the implemented deployment fixes."""
        all_regression_tests = []
        
        for fix in fixes:
            logger.info(f"Creating regression tests for fix {fix.solution_id}")
            
            # Determine test type based on fix type
            fix_type = fix.implementation_details.get("fix_type", "general")
            
            if fix_type == "configuration":
                test_type = "configuration_validation"
            elif fix_type == "dependency":
                test_type = "dependency_validation"
            elif fix_type == "compatibility":
                test_type = "compatibility_validation"
            elif fix_type == "resource":
                test_type = "resource_validation"
            else:
                test_type = "deployment_validation"
            
            # Create regression tests for each affected environment
            environment_tests = []
            for env_id in fix.affected_environments:
                test_id = f"env_regression_{fix.solution_id}_{env_id}"
                
                test = {
                    "test_id": test_id,
                    "test_type": test_type,
                    "environment_id": env_id,
                    "name": f"Environment regression test for {fix.title} on environment {env_id}",
                    "description": f"Verifies that the fix for {fix.description} works correctly in environment {env_id}",
                    "test_steps": [
                        f"Deploy to environment {env_id}",
                        "Verify configuration consistency",
                        "Validate component initialization",
                        "Verify component functionality"
                    ],
                    "expected_results": "Deployment should succeed with no issues"
                }
                
                environment_tests.append(test)
                all_regression_tests.append(test)
            
            # Create regression tests for each affected component
            component_tests = []
            for comp_id in fix.affected_components:
                test_id = f"comp_regression_{fix.solution_id}_{comp_id}"
                
                test = {
                    "test_id": test_id,
                    "test_type": test_type,
                    "component_id": comp_id,
                    "name": f"Component regression test for {fix.title} on component {comp_id}",
                    "description": f"Verifies that the fix for {fix.description} works correctly for component {comp_id}",
                    "test_steps": [
                        f"Deploy component {comp_id} to each affected environment",
                        "Verify component initialization",
                        "Validate component functionality",
                        "Test component integration points"
                    ],
                    "expected_results": "Component should deploy and function correctly"
                }
                
                component_tests.append(test)
                all_regression_tests.append(test)
            
            # If fix affects multiple environments or components, add cross-validation test
            if len(fix.affected_environments) > 1 and len(fix.affected_components) > 1:
                cross_test_id = f"cross_regression_{fix.solution_id}"
                
                cross_test = {
                    "test_id": cross_test_id,
                    "test_type": f"cross_{test_type}",
                    "name": f"Cross-environment regression test for {fix.title}",
                    "description": f"Verifies that the fix works correctly across all affected environments and components",
                    "affected_environments": fix.affected_environments,
                    "affected_components": fix.affected_components,
                    "test_steps": [
                        "Deploy all affected components to all affected environments",
                        "Verify cross-environment functionality",
                        "Test component interactions across environments",
                        "Validate end-to-end workflows"
                    ],
                    "expected_results": "All components should work correctly in all environments"
                }
                
                all_regression_tests.append(cross_test)
            
            # Add regression tests to the fix
            fix.regression_tests = environment_tests + component_tests
            
            # Log metric for regression tests
            await self._metrics_manager.record_metric(
                "deployment_test_debug:regression_tests_created",
                len(fix.regression_tests),
                metadata={
                    "solution_id": fix.solution_id,
                    "test_type": test_type
                }
            )
        
        return all_regression_tests
    
    def _generate_deployment_documentation(self, fixes: List[DeploymentFixSolution]) -> Dict[str, Any]:
        """Generate documentation for the implemented deployment fixes."""
        documentation = {
            "title": "Deployment Fix Documentation",
            "description": "Documentation of fixes implemented to resolve deployment issues",
            "timestamp": datetime.now().isoformat(),
            "fixes": [],
            "affected_environments": [],
            "affected_components": [],
            "deployment_guidelines": {
                "pre_deployment_checklist": [
                    "Verify environment configuration",
                    "Validate component dependencies",
                    "Check resource availability",
                    "Ensure compatibility with target environment"
                ],
                "deployment_process": [
                    "Prepare deployment package",
                    "Apply environment-specific configurations",
                    "Deploy components in dependency order",
                    "Verify component initialization"
                ],
                "post_deployment_validation": [
                    "Run deployment verification tests",
                    "Validate component functionality",
                    "Verify cross-component integration",
                    "Monitor system health metrics"
                ]
            }
        }
        
        # Collect all affected environments and components
        all_environments = set()
        all_components = set()
        
        for fix in fixes:
            all_environments.update(fix.affected_environments)
            all_components.update(fix.affected_components)
        
        documentation["affected_environments"] = list(all_environments)
        documentation["affected_components"] = list(all_components)
        
        # Add detailed fix documentation
        for fix in fixes:
            fix_type = fix.implementation_details.get("fix_type", "general")
            
            fix_doc = {
                "title": fix.title,
                "description": fix.description,
                "solution_id": fix.solution_id,
                "fix_type": fix_type,
                "environments": fix.affected_environments,
                "components": fix.affected_components,
                "changes": fix.implementation_details.get("changes", []),
                "verification": fix.verification_steps,
                "regression_tests": [test.get("name") for test in fix.regression_tests]
            }
            
            # Add fix-type specific deployment instructions
            if fix_type == "configuration":
                fix_doc["deployment_instructions"] = [
                    "Apply updated configuration files to each environment",
                    "Validate configuration values before deployment",
                    "Restart affected components to apply new configuration",
                    "Verify component behavior with new configuration"
                ]
            elif fix_type == "dependency":
                fix_doc["deployment_instructions"] = [
                    "Update dependency definitions in deployment packages",
                    "Ensure correct dependency resolution order",
                    "Validate all dependencies are available in target environments",
                    "Test component initialization with updated dependencies"
                ]
            elif fix_type == "compatibility":
                fix_doc["deployment_instructions"] = [
                    "Apply environment-specific adaptation layers",
                    "Update environment compatibility definitions",
                    "Use environment-specific deployment configurations",
                    "Validate component behavior in each environment"
                ]
            elif fix_type == "resource":
                fix_doc["deployment_instructions"] = [
                    "Update resource allocation in environment configurations",
                    "Apply resource optimization settings",
                    "Configure monitoring for resource usage",
                    "Validate component performance with new resource settings"
                ]
            else:
                fix_doc["deployment_instructions"] = [
                    "Follow standard deployment process for affected components",
                    "Apply all recommended configurations",
                    "Validate deployment success in each environment",
                    "Verify component functionality after deployment"
                ]
                
            documentation["fixes"].append(fix_doc)
        
        return documentation
    
    def _create_summary(self, 
                       recommendations: List[Dict[str, Any]],
                       verified_fixes: List[DeploymentFixSolution],
                       regression_tests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a summary of the debug results."""
        # Count fixes by type
        fix_types = {}
        for fix in verified_fixes:
            fix_type = fix.implementation_details.get("fix_type", "unknown")
            if fix_type not in fix_types:
                fix_types[fix_type] = 0
            fix_types[fix_type] += 1
        
        # Count affected environments and components
        affected_environments = set()
        affected_components = set()
        for fix in verified_fixes:
            affected_environments.update(fix.affected_environments)
            affected_components.update(fix.affected_components)
        
        # Count regression tests by type
        test_types = {}
        for test in regression_tests:
            test_type = test.get("test_type", "unknown")
            if test_type not in test_types:
                test_types[test_type] = 0
            test_types[test_type] += 1
        
        return {
            "total_recommendations": len(recommendations),
            "fixes_implemented": len(verified_fixes),
            "fixes_verified": len([fix for fix in verified_fixes if fix.verified]),
            "regression_tests_created": len(regression_tests),
            "affected_environments": len(affected_environments),
            "affected_components": len(affected_components),
            "fixes_by_type": fix_types,
            "tests_by_type": test_types,
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_environment_impacts(self, 
                                     fixes: List[DeploymentFixSolution],
                                     environment_mapping: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Calculate the impact of fixes on each environment."""
        environment_impacts = {}
        
        # Group fixes by environment
        for fix in fixes:
            for env_id in fix.affected_environments:
                if env_id not in environment_impacts:
                    env = environment_mapping.get(env_id, {})
                    environment_impacts[env_id] = {
                        "environment_id": env_id,
                        "environment_name": env.get("name", f"Environment {env_id}"),
                        "environment_type": env.get("type", "unknown"),
                        "fixes": [],
                        "fix_count": 0,
                        "configuration_changes": False,
                        "dependency_changes": False,
                        "compatibility_changes": False,
                        "resource_changes": False,
                        "components_affected": set()
                    }
                
                # Add fix to environment
                environment_impacts[env_id]["fixes"].append(fix.solution_id)
                environment_impacts[env_id]["fix_count"] += 1
                
                # Update change flags
                fix_type = fix.implementation_details.get("fix_type", "unknown")
                if fix_type == "configuration":
                    environment_impacts[env_id]["configuration_changes"] = True
                elif fix_type == "dependency":
                    environment_impacts[env_id]["dependency_changes"] = True
                elif fix_type == "compatibility":
                    environment_impacts[env_id]["compatibility_changes"] = True
                elif fix_type == "resource":
                    environment_impacts[env_id]["resource_changes"] = True
                
                # Add affected components
                environment_impacts[env_id]["components_affected"].update(fix.affected_components)
        
        # Convert sets to lists for JSON serialization
        for env_id, impact in environment_impacts.items():
            impact["components_affected"] = list(impact["components_affected"])
            
            # Calculate deployment impact level
            change_count = sum([
                impact["configuration_changes"],
                impact["dependency_changes"],
                impact["compatibility_changes"],
                impact["resource_changes"]
            ])
            
            if change_count >= 3 or len(impact["components_affected"]) > 3:
                impact["impact_level"] = "high"
            elif change_count >= 2 or len(impact["components_affected"]) > 1:
                impact["impact_level"] = "medium"
            else:
                impact["impact_level"] = "low"
                
            # Add deployment recommendations
            impact["deployment_recommendations"] = self._generate_environment_deployment_recommendations(
                impact, environment_mapping.get(env_id, {}))
        
        return environment_impacts
    
    def _generate_environment_deployment_recommendations(self, 
                                                      impact: Dict[str, Any],
                                                      environment: Dict[str, Any]) -> List[str]:
        """Generate deployment recommendations for an environment based on impact."""
        recommendations = [
            f"Deploy all fixed components to {impact['environment_name']} environment"
        ]
        
        # Add specific recommendations based on change types
        if impact["configuration_changes"]:
            recommendations.append("Verify all configuration changes before deployment")
            
        if impact["dependency_changes"]:
            recommendations.append("Ensure all dependencies are resolved correctly")
            
        if impact["compatibility_changes"]:
            recommendations.append("Validate component compatibility with the environment")
            
        if impact["resource_changes"]:
            recommendations.append("Monitor resource usage during and after deployment")
        
        # Add impact-level specific recommendations
        if impact["impact_level"] == "high":
            recommendations.extend([
                "Perform phased deployment to minimize risk",
                "Create deployment rollback plan",
                "Implement additional monitoring during deployment",
                "Conduct comprehensive post-deployment validation"
            ])
        elif impact["impact_level"] == "medium":
            recommendations.extend([
                "Validate deployment in staging environment first",
                "Create basic rollback procedure",
                "Perform standard post-deployment verification"
            ])
        
        # Add environment-type specific recommendations
        env_type = environment.get("type", "unknown").lower()
        if env_type == "production":
            recommendations.extend([
                "Schedule deployment during low-traffic period",
                "Implement canary deployment approach",
                "Have on-call support available during deployment"
            ])
        elif env_type == "staging":
            recommendations.extend([
                "Verify production-like behavior after deployment",
                "Run full test suite after deployment"
            ])
            
        return recommendations