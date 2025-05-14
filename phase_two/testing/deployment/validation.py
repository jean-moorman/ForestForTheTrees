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
class DeploymentValidationResult:
    criterion_id: str
    name: str
    description: str
    validation_status: str  # "passed", "failed", "partial", "not_validated"
    validation_method: str  # "test", "analysis", "manual"
    validation_details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "criterion_id": self.criterion_id,
            "name": self.name,
            "description": self.description,
            "validation_status": self.validation_status,
            "validation_method": self.validation_method,
            "validation_details": self.validation_details
        }


class DeploymentValidationAgent(PhaseTwoAgentBase):
    """
    Validates deployment environments against criteria.
    
    Responsibilities:
    - Validate deployment environment configuration
    - Verify component compatibility in deployment
    - Check resource utilization and constraints
    - Validate deployment against operational requirements
    """
    
    def __init__(self,
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        """Initialize the deployment validation agent."""
        super().__init__(
            "deployment_validation_agent",
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
    
    async def validate_deployment(self, 
                                environment: Dict[str, Any],
                                components: List[Dict[str, Any]],
                                test_results: Dict[str, Any],
                                validation_id: str) -> Dict[str, Any]:
        """
        Validate a deployment environment against requirements.
        
        Args:
            environment: Deployment environment details
            components: List of deployed components
            test_results: Results from deployment testing
            validation_id: Unique identifier for this validation session
            
        Returns:
            Dictionary containing validation results
        """
        logger.info(f"Validating deployment environment {environment.get('name', 'unknown')} for validation ID: {validation_id}")
        
        start_time = time.time()
        
        # Record validation start
        await self._metrics_manager.record_metric(
            "deployment_validation:start",
            1.0,
            metadata={
                "validation_id": validation_id,
                "environment_id": environment.get("id", "unknown"),
                "component_count": len(components)
            }
        )
        
        # Define validation criteria
        validation_criteria = self._define_validation_criteria(environment, components)
        
        if not validation_criteria:
            logger.info(f"No validation criteria defined for {validation_id}")
            return {
                "status": "error",
                "message": "No validation criteria defined",
                "validation_id": validation_id,
                "validation_results": [],
                "coverage": {
                    "total_criteria": 0,
                    "validated_criteria": 0,
                    "validation_coverage": 0
                }
            }
        
        # Validate each criterion
        validation_results = []
        for criterion in validation_criteria:
            criterion_result = await self._validate_criterion(
                criterion, 
                environment,
                components,
                test_results,
                validation_id
            )
            validation_results.append(criterion_result)
        
        # Calculate coverage
        total_criteria = len(validation_criteria)
        validated_criteria = sum(1 for result in validation_results 
                              if result.validation_status in ["passed", "partial"])
        validation_coverage = (validated_criteria / total_criteria) * 100 if total_criteria > 0 else 0
        
        # Determine overall status
        if all(result.validation_status == "passed" for result in validation_results):
            status = "passed"
        elif any(result.validation_status == "failed" for result in validation_results):
            status = "failed"
        else:
            status = "partial"
        
        # Create validation report
        validation_report = {
            "status": status,
            "validation_id": validation_id,
            "timestamp": datetime.now().isoformat(),
            "environment_id": environment.get("id", "unknown"),
            "environment_name": environment.get("name", "unknown"),
            "environment_type": environment.get("type", "unknown"),
            "execution_time_seconds": time.time() - start_time,
            "validation_results": [result.to_dict() for result in validation_results],
            "coverage": {
                "total_criteria": total_criteria,
                "validated_criteria": validated_criteria,
                "validation_coverage": validation_coverage
            },
            "recommendations": self._generate_recommendations(validation_results)
        }
        
        # Store validation in state and memory
        self._validation_sessions[validation_id] = validation_report
        await self._state_manager.set_state(
            f"deployment_validation:{validation_id}",
            {
                "validation_id": validation_id,
                "environment_id": environment.get("id", "unknown"),
                "timestamp": datetime.now().isoformat(),
                "status": status,
                "total_criteria": total_criteria,
                "validated_criteria": validated_criteria,
                "validation_coverage": validation_coverage
            }
        )
        
        # Record validation completion
        await self._metrics_manager.record_metric(
            "deployment_validation:complete",
            1.0,
            metadata={
                "validation_id": validation_id,
                "status": status,
                "total_criteria": total_criteria,
                "validated_criteria": validated_criteria,
                "validation_coverage": validation_coverage,
                "execution_time": time.time() - start_time
            }
        )
        
        logger.info(f"Completed deployment validation {validation_id} with status: {status}")
        return validation_report
    
    def _define_validation_criteria(self, 
                                  environment: Dict[str, Any],
                                  components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Define validation criteria for the deployment environment."""
        env_type = environment.get("type", "").lower()
        
        # Common criteria for all environment types
        criteria = [
            {
                "id": "configuration",
                "name": "Configuration Validation",
                "description": "Validates that the environment is correctly configured",
                "validation_method": "analysis"
            },
            {
                "id": "compatibility",
                "name": "Component Compatibility",
                "description": "Validates that components work correctly together in the environment",
                "validation_method": "test"
            },
            {
                "id": "resources",
                "name": "Resource Utilization",
                "description": "Validates that environment resources are utilized efficiently",
                "validation_method": "analysis"
            }
        ]
        
        # Add environment-specific criteria
        if env_type == "production":
            criteria.extend([
                {
                    "id": "scalability",
                    "name": "Scalability",
                    "description": "Validates that the deployment can handle expected load",
                    "validation_method": "analysis"
                },
                {
                    "id": "availability",
                    "name": "High Availability",
                    "description": "Validates that the deployment meets availability requirements",
                    "validation_method": "analysis"
                },
                {
                    "id": "security",
                    "name": "Security",
                    "description": "Validates that security measures are properly implemented",
                    "validation_method": "analysis"
                }
            ])
        elif env_type == "staging":
            criteria.extend([
                {
                    "id": "monitoring",
                    "name": "Monitoring",
                    "description": "Validates that monitoring systems are properly configured",
                    "validation_method": "analysis"
                },
                {
                    "id": "data",
                    "name": "Data Integrity",
                    "description": "Validates that test data is properly configured",
                    "validation_method": "test"
                }
            ])
        elif env_type == "development":
            criteria.extend([
                {
                    "id": "debugging",
                    "name": "Debugging Tools",
                    "description": "Validates that debugging tools are properly configured",
                    "validation_method": "analysis"
                }
            ])
        
        return criteria
    
    async def _validate_criterion(self, 
                                criterion: Dict[str, Any],
                                environment: Dict[str, Any],
                                components: List[Dict[str, Any]],
                                test_results: Dict[str, Any],
                                validation_id: str) -> DeploymentValidationResult:
        """Validate a single criterion against the deployment environment."""
        criterion_id = criterion.get("id", "")
        name = criterion.get("name", "")
        description = criterion.get("description", "")
        validation_method = criterion.get("validation_method", "analysis")
        
        logger.info(f"Validating deployment criterion {name} ({criterion_id})")
        
        # Record validation attempt
        await self._metrics_manager.record_metric(
            "deployment_criterion_validation:attempt",
            1.0,
            metadata={
                "validation_id": validation_id,
                "criterion_id": criterion_id,
                "criterion_name": name,
                "validation_method": validation_method
            }
        )
        
        # Select validation method based on criterion type
        if criterion_id == "configuration":
            validation_result = self._validate_configuration(environment, components)
        elif criterion_id == "compatibility":
            validation_result = self._validate_compatibility(environment, components, test_results)
        elif criterion_id == "resources":
            validation_result = self._validate_resources(environment, components)
        elif criterion_id == "scalability":
            validation_result = self._validate_scalability(environment, components)
        elif criterion_id == "availability":
            validation_result = self._validate_availability(environment, components)
        elif criterion_id == "security":
            validation_result = self._validate_security(environment, components)
        elif criterion_id == "monitoring":
            validation_result = self._validate_monitoring(environment, components)
        elif criterion_id == "data":
            validation_result = self._validate_data(environment, components, test_results)
        elif criterion_id == "debugging":
            validation_result = self._validate_debugging(environment, components)
        else:
            # Default to not validated for unknown criteria
            validation_result = {
                "status": "not_validated",
                "details": f"Unknown validation criterion: {criterion_id}",
                "validation_items": []
            }
        
        # Create validation result
        result = DeploymentValidationResult(
            criterion_id=criterion_id,
            name=name,
            description=description,
            validation_status=validation_result.get("status", "not_validated"),
            validation_method=validation_method,
            validation_details=validation_result
        )
        
        # Record validation result
        await self._metrics_manager.record_metric(
            "deployment_criterion_validation:complete",
            1.0,
            metadata={
                "validation_id": validation_id,
                "criterion_id": criterion_id,
                "criterion_name": name,
                "status": result.validation_status
            }
        )
        
        return result
    
    def _validate_configuration(self, environment: Dict[str, Any], components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate environment configuration."""
        # In a real implementation, this would perform actual configuration validation
        # Simulated for this implementation
        
        # Check for required configuration fields
        required_fields = ["id", "name", "type", "resources", "configuration"]
        missing_fields = [field for field in required_fields if field not in environment]
        
        if missing_fields:
            return {
                "status": "failed",
                "details": f"Missing required configuration fields: {', '.join(missing_fields)}",
                "validation_items": []
            }
        
        # Verify resource configuration
        resources = environment.get("resources", {})
        if not resources:
            return {
                "status": "failed",
                "details": "No resources defined in environment configuration",
                "validation_items": []
            }
        
        # Check component configuration in environment
        component_ids = set(component.get("id", "") for component in components)
        environment_components = set(environment.get("components", []))
        
        missing_components = component_ids - environment_components
        if missing_components:
            return {
                "status": "partial",
                "details": f"Some components not registered in environment: {', '.join(missing_components)}",
                "validation_items": [
                    {
                        "item": "Components Registration",
                        "status": "partial",
                        "details": f"{len(environment_components)}/{len(component_ids)} components registered"
                    },
                    {
                        "item": "Resource Configuration",
                        "status": "passed",
                        "details": "Resources properly configured"
                    }
                ]
            }
        
        # All checks passed
        return {
            "status": "passed",
            "details": "Environment configuration is valid",
            "validation_items": [
                {
                    "item": "Configuration Fields",
                    "status": "passed",
                    "details": "All required fields present"
                },
                {
                    "item": "Resource Configuration",
                    "status": "passed",
                    "details": "Resources properly configured"
                },
                {
                    "item": "Components Registration",
                    "status": "passed",
                    "details": "All components registered in environment"
                }
            ]
        }
    
    def _validate_compatibility(self, environment: Dict[str, Any], components: List[Dict[str, Any]], test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate component compatibility based on test results."""
        # Use test results to determine compatibility
        total_tests = test_results.get("total_tests", 0)
        passed_tests = test_results.get("passed_tests", 0)
        failed_tests = test_results.get("failed_tests", 0)
        
        if total_tests == 0:
            return {
                "status": "not_validated",
                "details": "No compatibility tests were run",
                "validation_items": []
            }
        
        pass_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        if pass_rate == 100:
            status = "passed"
            details = "All compatibility tests passed"
        elif pass_rate >= 80:
            status = "partial"
            details = f"{passed_tests}/{total_tests} compatibility tests passed ({pass_rate:.1f}%)"
        else:
            status = "failed"
            details = f"Too many compatibility tests failed: {failed_tests}/{total_tests} failed ({100 - pass_rate:.1f}%)"
        
        return {
            "status": status,
            "details": details,
            "validation_items": [
                {
                    "item": "Component Integration Tests",
                    "status": status,
                    "details": f"{passed_tests}/{total_tests} tests passed"
                }
            ]
        }
    
    def _validate_resources(self, environment: Dict[str, Any], components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate resource utilization efficiency."""
        # In a real implementation, this would analyze resource metrics
        # Simulated for this implementation
        
        resources = environment.get("resources", {})
        metrics = environment.get("metrics", {})
        
        # Without real metrics, we'll simulate resource validation
        resource_metrics = metrics.get("resource_usage", {})
        
        validation_items = []
        for resource_name in ["cpu", "memory", "disk", "network"]:
            usage = resource_metrics.get(resource_name, 0)
            
            if resource_name in resources:
                threshold = resources.get(resource_name, {}).get("usage_threshold", 80)
                
                if usage > threshold:
                    status = "failed"
                    details = f"{resource_name.upper()} usage exceeds threshold: {usage}% > {threshold}%"
                elif usage > threshold * 0.8:
                    status = "partial"
                    details = f"{resource_name.upper()} usage approaching threshold: {usage}% nearing {threshold}%"
                else:
                    status = "passed"
                    details = f"{resource_name.upper()} usage within limits: {usage}% < {threshold}%"
                
                validation_items.append({
                    "item": f"{resource_name.upper()} Usage",
                    "status": status,
                    "details": details
                })
        
        # Determine overall status
        if all(item["status"] == "passed" for item in validation_items):
            status = "passed"
            details = "All resource utilization within expected limits"
        elif any(item["status"] == "failed" for item in validation_items):
            status = "failed"
            details = "Some resources exceeding utilization thresholds"
        else:
            status = "partial"
            details = "Some resources approaching utilization thresholds"
        
        return {
            "status": status,
            "details": details,
            "validation_items": validation_items
        }
    
    def _validate_scalability(self, environment: Dict[str, Any], components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate scalability of the deployment."""
        # In a real implementation, this would analyze load test results
        # Simulated for this implementation
        
        scaling = environment.get("configuration", {}).get("scaling", {})
        if not scaling:
            return {
                "status": "not_validated",
                "details": "Scaling configuration not found",
                "validation_items": []
            }
        
        auto_scaling = scaling.get("auto_scaling") == "enabled"
        min_instances = scaling.get("min_instances", 1)
        max_instances = scaling.get("max_instances", 1)
        
        validation_items = [
            {
                "item": "Auto-scaling",
                "status": "passed" if auto_scaling else "failed",
                "details": "Auto-scaling is enabled" if auto_scaling else "Auto-scaling is disabled"
            },
            {
                "item": "Instance Capacity",
                "status": "passed" if max_instances >= 2 else "failed",
                "details": f"Maximum instances: {max_instances}"
            }
        ]
        
        # Determine overall status
        if all(item["status"] == "passed" for item in validation_items):
            status = "passed"
            details = "Scalability configuration meets requirements"
        else:
            status = "failed"
            details = "Scalability configuration does not meet requirements"
        
        return {
            "status": status,
            "details": details,
            "validation_items": validation_items
        }
    
    def _validate_availability(self, environment: Dict[str, Any], components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate high availability configuration."""
        # In a real implementation, this would analyze HA configuration
        # Simulated for this implementation
        
        # Check replication settings
        database = environment.get("configuration", {}).get("database", {})
        replication = database.get("replication") == "enabled"
        
        # Check backup settings
        backup_interval = database.get("backup_interval", "")
        has_backups = backup_interval != ""
        
        validation_items = [
            {
                "item": "Data Replication",
                "status": "passed" if replication else "failed",
                "details": "Replication is enabled" if replication else "Replication is disabled"
            },
            {
                "item": "Backup Configuration",
                "status": "passed" if has_backups else "failed",
                "details": f"Backup interval: {backup_interval}" if has_backups else "No backup configuration"
            }
        ]
        
        # Determine overall status
        if all(item["status"] == "passed" for item in validation_items):
            status = "passed"
            details = "High availability configuration meets requirements"
        else:
            status = "failed"
            details = "High availability configuration does not meet requirements"
        
        return {
            "status": status,
            "details": details,
            "validation_items": validation_items
        }
    
    def _validate_security(self, environment: Dict[str, Any], components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate security configuration."""
        # In a real implementation, this would analyze security settings
        # Simulated for this implementation
        
        security = environment.get("configuration", {}).get("security", {})
        if not security:
            return {
                "status": "not_validated",
                "details": "Security configuration not found",
                "validation_items": []
            }
        
        encryption = security.get("encryption") == "enabled"
        authentication = security.get("authentication", "")
        firewall = security.get("firewall") == "enabled"
        
        validation_items = [
            {
                "item": "Encryption",
                "status": "passed" if encryption else "failed",
                "details": "Encryption is enabled" if encryption else "Encryption is disabled"
            },
            {
                "item": "Authentication",
                "status": "passed" if authentication in ["strict", "standard"] else "failed",
                "details": f"Authentication mode: {authentication}"
            },
            {
                "item": "Firewall",
                "status": "passed" if firewall else "failed",
                "details": "Firewall is enabled" if firewall else "Firewall is disabled"
            }
        ]
        
        # Determine overall status
        if all(item["status"] == "passed" for item in validation_items):
            status = "passed"
            details = "Security configuration meets requirements"
        elif sum(1 for item in validation_items if item["status"] == "passed") >= 2:
            status = "partial"
            details = "Some security requirements not met"
        else:
            status = "failed"
            details = "Security configuration does not meet requirements"
        
        return {
            "status": status,
            "details": details,
            "validation_items": validation_items
        }
    
    def _validate_monitoring(self, environment: Dict[str, Any], components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate monitoring configuration."""
        # In a real implementation, this would analyze monitoring settings
        # Simulated for this implementation
        
        logging = environment.get("configuration", {}).get("logging", {})
        if not logging:
            return {
                "status": "not_validated",
                "details": "Logging configuration not found",
                "validation_items": []
            }
        
        log_level = logging.get("level", "")
        retention = logging.get("retention_days", 0)
        detailed_errors = logging.get("detailed_errors", False)
        
        validation_items = [
            {
                "item": "Log Level",
                "status": "passed" if log_level in ["DEBUG", "INFO"] else "failed",
                "details": f"Log level: {log_level}"
            },
            {
                "item": "Log Retention",
                "status": "passed" if retention >= 7 else "failed",
                "details": f"Retention period: {retention} days"
            },
            {
                "item": "Error Logging",
                "status": "passed" if detailed_errors else "failed",
                "details": "Detailed error logging is enabled" if detailed_errors else "Detailed error logging is disabled"
            }
        ]
        
        # Determine overall status
        if all(item["status"] == "passed" for item in validation_items):
            status = "passed"
            details = "Monitoring configuration meets requirements"
        elif sum(1 for item in validation_items if item["status"] == "passed") >= 2:
            status = "partial"
            details = "Some monitoring requirements not met"
        else:
            status = "failed"
            details = "Monitoring configuration does not meet requirements"
        
        return {
            "status": status,
            "details": details,
            "validation_items": validation_items
        }
    
    def _validate_data(self, environment: Dict[str, Any], components: List[Dict[str, Any]], test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data integrity in test environment."""
        # In a real implementation, this would analyze test data configuration
        # Simulated for this implementation
        
        # Use test results to infer data validation
        total_tests = test_results.get("total_tests", 0)
        passed_tests = test_results.get("passed_tests", 0)
        
        if total_tests == 0:
            return {
                "status": "not_validated",
                "details": "No data tests were run",
                "validation_items": []
            }
        
        pass_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        if pass_rate >= 90:
            status = "passed"
            details = "Test data configuration appears valid"
        elif pass_rate >= 70:
            status = "partial"
            details = "Some test data issues detected"
        else:
            status = "failed"
            details = "Significant test data issues detected"
        
        return {
            "status": status,
            "details": details,
            "validation_items": [
                {
                    "item": "Data Integrity Tests",
                    "status": status,
                    "details": f"{passed_tests}/{total_tests} tests passed ({pass_rate:.1f}%)"
                }
            ]
        }
    
    def _validate_debugging(self, environment: Dict[str, Any], components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate debugging configuration in development environment."""
        # In a real implementation, this would analyze debugging configuration
        # Simulated for this implementation
        
        logging = environment.get("configuration", {}).get("logging", {})
        if not logging:
            return {
                "status": "not_validated",
                "details": "Logging configuration not found",
                "validation_items": []
            }
        
        log_level = logging.get("level", "")
        detailed_errors = logging.get("detailed_errors", False)
        
        validation_items = [
            {
                "item": "Debug Log Level",
                "status": "passed" if log_level == "DEBUG" else "failed",
                "details": f"Log level: {log_level}"
            },
            {
                "item": "Detailed Error Logging",
                "status": "passed" if detailed_errors else "failed",
                "details": "Detailed error logging is enabled" if detailed_errors else "Detailed error logging is disabled"
            }
        ]
        
        # Determine overall status
        if all(item["status"] == "passed" for item in validation_items):
            status = "passed"
            details = "Debugging configuration meets requirements"
        else:
            status = "failed"
            details = "Debugging configuration does not meet requirements"
        
        return {
            "status": status,
            "details": details,
            "validation_items": validation_items
        }
    
    def _generate_recommendations(self, validation_results: List[DeploymentValidationResult]) -> List[Dict[str, Any]]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        # Check for configuration issues
        config_result = next((r for r in validation_results if r.criterion_id == "configuration"), None)
        if config_result and config_result.validation_status != "passed":
            recommendations.append({
                "priority": "high",
                "type": "configuration",
                "title": "Fix Environment Configuration",
                "description": "Address configuration issues in the deployment environment",
                "action_items": [
                    "Verify all required configuration fields are present",
                    "Ensure all components are properly registered",
                    "Validate resource configurations"
                ]
            })
        
        # Check for compatibility issues
        compat_result = next((r for r in validation_results if r.criterion_id == "compatibility"), None)
        if compat_result and compat_result.validation_status in ["failed", "partial"]:
            recommendations.append({
                "priority": "high",
                "type": "compatibility",
                "title": "Address Component Compatibility Issues",
                "description": "Fix compatibility issues between components in the deployment",
                "action_items": [
                    "Review failed compatibility tests",
                    "Verify component interface definitions",
                    "Update component configurations for better integration"
                ]
            })
        
        # Check for resource issues
        resource_result = next((r for r in validation_results if r.criterion_id == "resources"), None)
        if resource_result and resource_result.validation_status in ["failed", "partial"]:
            recommendations.append({
                "priority": "medium",
                "type": "resources",
                "title": "Optimize Resource Utilization",
                "description": "Improve resource usage efficiency in the deployment",
                "action_items": [
                    "Adjust resource allocations for overutilized components",
                    "Review resource thresholds for appropriate limits",
                    "Implement resource monitoring and scaling"
                ]
            })
        
        # Check for scalability issues
        scalability_result = next((r for r in validation_results if r.criterion_id == "scalability"), None)
        if scalability_result and scalability_result.validation_status != "passed":
            recommendations.append({
                "priority": "medium",
                "type": "scalability",
                "title": "Improve Scalability Configuration",
                "description": "Enhance deployment scalability to handle load",
                "action_items": [
                    "Enable auto-scaling in environment configuration",
                    "Increase maximum instance capacity",
                    "Implement load testing to verify scalability"
                ]
            })
        
        # Check for security issues
        security_result = next((r for r in validation_results if r.criterion_id == "security"), None)
        if security_result and security_result.validation_status != "passed":
            recommendations.append({
                "priority": "high",
                "type": "security",
                "title": "Address Security Configuration Issues",
                "description": "Fix security vulnerabilities in deployment configuration",
                "action_items": [
                    "Enable encryption for sensitive data",
                    "Implement strict authentication mechanisms",
                    "Enable firewall protection for deployment environment"
                ]
            })
        
        # General recommendation if multiple issues exist
        if len([r for r in validation_results if r.validation_status != "passed"]) > 2:
            recommendations.append({
                "priority": "medium",
                "type": "process",
                "title": "Implement Deployment Validation Process",
                "description": "Create standard validation process for deployments",
                "action_items": [
                    "Develop pre-deployment validation checklist",
                    "Implement automated validation testing",
                    "Establish deployment approval workflow"
                ]
            })
        
        return recommendations
    
    async def get_validation_result(self, validation_id: str) -> Dict[str, Any]:
        """Retrieve results for a specific validation session."""
        # Check in-memory cache first
        if validation_id in self._validation_sessions:
            return self._validation_sessions[validation_id]
        
        # Try to get from state manager
        state = await self._state_manager.get_state(f"deployment_validation:{validation_id}")
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
        
        # Generate validation report
        validation_report = {
            "validation_id": validation_id,
            "timestamp": datetime.now().isoformat(),
            "title": "Deployment Validation Report",
            "summary": {
                "environment_id": validation_result.get("environment_id", ""),
                "environment_name": validation_result.get("environment_name", ""),
                "total_criteria": coverage.get("total_criteria", 0),
                "validated_criteria": coverage.get("validated_criteria", 0),
                "validation_coverage": coverage.get("validation_coverage", 0),
                "validation_status": self._determine_overall_status(coverage)
            },
            "validation_results": validation_results,
            "recommendations": validation_result.get("recommendations", []),
            "action_plan": self._generate_action_plan(validation_result.get("recommendations", []))
        }
        
        return validation_report
    
    def _determine_overall_status(self, coverage: Dict[str, Any]) -> str:
        """Determine overall validation status."""
        validated_percentage = coverage.get("validation_coverage", 0)
        
        if validated_percentage >= 95:
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
            "title": "Deployment Validation Action Plan",
            "description": "Prioritized actions to improve deployment validation",
            "action_items": action_items,
            "high_priority_count": len(priority_groups["high"]),
            "medium_priority_count": len(priority_groups["medium"]),
            "low_priority_count": len(priority_groups["low"])
        }