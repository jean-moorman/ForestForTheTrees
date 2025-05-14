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
    MemoryMonitor,
    SystemMonitor,
    ResourceEventTypes
)

from phase_two.testing.deployment.simulator import DeploymentSimulator
from phase_two.testing.deployment.analysis import DeploymentTestAnalysisAgent
from phase_two.testing.deployment.validation import DeploymentValidationAgent
from phase_two.testing.deployment.integration import DeploymentIntegrationValidator

logger = logging.getLogger(__name__)

@dataclass
class DeploymentTestingResult:
    """Container for complete deployment testing process results."""
    session_id: str
    environment_id: str
    analysis_id: str
    integration_id: str
    validation_id: str
    status: str
    component_count: int
    test_count: int
    environment_details: Dict[str, Any] = field(default_factory=dict)
    execution_results: Dict[str, Any] = field(default_factory=dict)
    analysis_results: Dict[str, Any] = field(default_factory=dict)
    integration_results: Dict[str, Any] = field(default_factory=dict)
    validation_results: Dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "session_id": self.session_id,
            "environment_id": self.environment_id,
            "analysis_id": self.analysis_id,
            "integration_id": self.integration_id,
            "validation_id": self.validation_id,
            "status": self.status,
            "component_count": self.component_count,
            "test_count": self.test_count,
            "environment_details": self.environment_details,
            "execution_results": self.execution_results,
            "analysis_results": self.analysis_results,
            "integration_results": self.integration_results,
            "validation_results": self.validation_results,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_duration": (self.end_time - self.start_time) if self.end_time else None
        }


class DeploymentTestingOrchestrator(PhaseTwoAgentBase):
    """
    Orchestrates the complete deployment testing workflow.
    
    Responsibilities:
    - Coordinates deployment environment setup, test execution, analysis, review, and debugging
    - Manages the flow of information between deployment testing agents
    - Provides a unified interface for the deployment testing process
    - Tracks and reports on deployment testing progress
    """
    
    def __init__(self,
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None,
                 system_monitor: Optional[SystemMonitor] = None):
        """Initialize the deployment testing orchestrator."""
        super().__init__(
            "deployment_testing_orchestrator",
            event_queue,
            state_manager,
            context_manager,
            cache_manager,
            metrics_manager,
            error_handler,
            memory_monitor
        )
        
        # Initialize specialized deployment testing agents
        self._simulator = DeploymentSimulator(
            event_queue, state_manager, context_manager, cache_manager, 
            metrics_manager, error_handler, memory_monitor
        )
        
        self._analyzer = DeploymentTestAnalysisAgent(
            event_queue, state_manager, context_manager, cache_manager, 
            metrics_manager, error_handler, memory_monitor
        )
        
        self._validator = DeploymentValidationAgent(
            event_queue, state_manager, context_manager, cache_manager, 
            metrics_manager, error_handler, memory_monitor
        )
        
        self._integration_validator = DeploymentIntegrationValidator(
            event_queue, state_manager, context_manager, cache_manager, 
            metrics_manager, error_handler, memory_monitor
        )
        
        # Keep track of deployment testing sessions
        self._testing_sessions: Dict[str, DeploymentTestingResult] = {}
        
        # Register with system monitor if available
        self._system_monitor = system_monitor
        if self._system_monitor:
            asyncio.create_task(
                self._system_monitor.register_component("deployment_testing_orchestrator", {
                    "type": "orchestrator",
                    "description": "Orchestrates deployment testing workflow",
                })
            )
    
    async def execute_deployment_testing(self, 
                                       components: List[Dict[str, Any]],
                                       environment_spec: Dict[str, Any],
                                       deployment_tests: List[Dict[str, Any]],
                                       session_id: str,
                                       execution_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the complete deployment testing workflow.
        
        Args:
            components: List of components to deploy and test
            environment_spec: Specification for the deployment environment
            deployment_tests: List of deployment tests to execute
            session_id: Unique identifier for this testing session
            execution_config: Optional configuration for deployment and test execution
            
        Returns:
            Dictionary containing the results of the deployment testing process
        """
        logger.info(f"Starting deployment testing workflow for session {session_id} with {len(components)} components in environment {environment_spec.get('name', 'unknown')}")
        
        # Record workflow start
        start_time = time.time()
        await self._metrics_manager.record_metric(
            "deployment_testing:start",
            1.0,
            metadata={
                "session_id": session_id,
                "component_count": len(components),
                "test_count": len(deployment_tests),
                "environment": environment_spec.get("name", "unknown")
            }
        )
        
        # Emit event for workflow start
        await self._event_queue.emit(
            ResourceEventTypes.PHASE_TWO_DEPLOYMENT_STARTED.value,
            {
                "session_id": session_id,
                "component_count": len(components),
                "test_count": len(deployment_tests),
                "environment": environment_spec.get("name", "unknown"),
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Create unique IDs for each phase
        analysis_id = f"analysis_{session_id}"
        integration_id = f"integration_{session_id}"
        validation_id = f"validation_{session_id}"
        
        try:
            # Step 1: Create deployment environment
            logger.info(f"[{session_id}] Step 1/5: Creating deployment environment")
            environment_result = await self._simulator.create_environment(
                environment_spec=environment_spec,
                initialize=True
            )
            
            environment_id = environment_result.get("id")
            
            # Initialize testing session
            testing_session = DeploymentTestingResult(
                session_id=session_id,
                environment_id=environment_id,
                analysis_id=analysis_id,
                integration_id=integration_id,
                validation_id=validation_id,
                status="running",
                component_count=len(components),
                test_count=len(deployment_tests),
                environment_details=environment_result,
                start_time=start_time
            )
            
            self._testing_sessions[session_id] = testing_session
            
            # Step 2: Deploy components to environment
            logger.info(f"[{session_id}] Step 2/5: Deploying components to environment")
            deployment_config = execution_config.get("deployment_config", {})
            deployment_result = await self._simulator.deploy_components(
                environment_id=environment_id,
                components=components,
                deployment_config=deployment_config
            )
            
            # Step 3: Run deployment tests
            logger.info(f"[{session_id}] Step 3/5: Running deployment tests")
            test_config = execution_config.get("test_config", {})
            test_result = await self._simulator.run_deployment_tests(
                environment_id=environment_id,
                tests=deployment_tests,
                test_config=test_config
            )
            
            testing_session.execution_results = test_result
            
            # Step 4: Analyze test results if there are failures
            failed_tests = test_result.get("failed_tests", 0)
            if failed_tests > 0:
                logger.info(f"[{session_id}] Analyzing {failed_tests} test failures")
                environments = [environment_result]
                analysis_result = await self._analyzer.analyze_deployment_failures(
                    test_results=test_result,
                    components=components,
                    environments=environments,
                    analysis_id=analysis_id
                )
                
                testing_session.analysis_results = analysis_result
            else:
                logger.info(f"[{session_id}] All tests passed, skipping analysis phase")
                testing_session.analysis_results = {
                    "status": "skipped",
                    "message": "All tests passed, analysis not needed"
                }
                
            # Step 4: Validate component integration
            logger.info(f"[{session_id}] Step 4/5: Validating component integration")
            validation_config = {
                "environment_type": environment_result.get("type", "development")
            }
            
            integration_result = await self._integration_validator.validate_integration(
                environment_id=environment_id,
                components=components,
                validation_config=validation_config
            )
            
            testing_session.integration_results = integration_result
            
            # Step 5: Validate deployment
            logger.info(f"[{session_id}] Step 5/5: Validating deployment")
            validation_result = await self._validator.validate_deployment(
                environment=environment_result,
                components=components,
                test_results=test_result,
                validation_id=validation_id
            )
            
            testing_session.validation_results = validation_result
            
            # Update session status and end time
            testing_session.status = "completed"
            testing_session.end_time = time.time()
            
            # Create final result
            final_result = testing_session.to_dict()
            
            # Store session result
            await self._state_manager.set_state(
                f"deployment_testing:{session_id}",
                {
                    "session_id": session_id,
                    "status": "completed",
                    "component_count": len(components),
                    "test_count": len(deployment_tests),
                    "environment_id": environment_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Record workflow completion
            await self._metrics_manager.record_metric(
                "deployment_testing:complete",
                1.0,
                metadata={
                    "session_id": session_id,
                    "status": "completed",
                    "execution_time": time.time() - start_time,
                    "component_count": len(components),
                    "test_count": len(deployment_tests),
                    "passed_tests": test_result.get("passed_tests", 0),
                    "failed_tests": test_result.get("failed_tests", 0)
                }
            )
            
            # Emit event for workflow completion
            await self._event_queue.emit(
                ResourceEventTypes.PHASE_TWO_DEPLOYMENT_COMPLETED.value,
                {
                    "session_id": session_id,
                    "status": "completed",
                    "component_count": len(components),
                    "test_count": len(deployment_tests),
                    "execution_time": time.time() - start_time,
                    "environment": environment_spec.get("name", "unknown"),
                    "components": components,  # Include components for monitoring
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            logger.info(f"Completed deployment testing workflow for session {session_id} in {time.time() - start_time:.2f} seconds")
            return final_result
            
        except Exception as e:
            # Handle workflow errors
            logger.error(f"Error in deployment testing workflow for session {session_id}: {str(e)}", exc_info=True)
            
            # Update session status if we have a session
            if session_id in self._testing_sessions:
                testing_session = self._testing_sessions[session_id]
                testing_session.status = "error"
                testing_session.end_time = time.time()
            
            # Record error
            await self._metrics_manager.record_metric(
                "deployment_testing:error",
                1.0,
                metadata={
                    "session_id": session_id,
                    "error": str(e),
                    "execution_time": time.time() - start_time
                }
            )
            
            # Emit error event
            await self._event_queue.emit(
                ResourceEventTypes.PHASE_TWO_DEPLOYMENT_FAILED.value,
                {
                    "session_id": session_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            return {
                "status": "error",
                "session_id": session_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_testing_session(self, session_id: str) -> Dict[str, Any]:
        """Get the status and results of a testing session."""
        # Check in-memory cache first
        if session_id in self._testing_sessions:
            return self._testing_sessions[session_id].to_dict()
        
        # Try to retrieve from state manager
        state = await self._state_manager.get_state(f"deployment_testing:{session_id}")
        if state:
            return state
        
        # Not found
        return {
            "status": "not_found",
            "message": f"No deployment testing session found with ID {session_id}"
        }
    
    async def get_environment_metrics(self, environment_id: str, time_period: str = "24h") -> Dict[str, Any]:
        """Get metrics for a specific deployment environment."""
        try:
            return await self._simulator.get_deployment_metrics(environment_id, time_period)
        except Exception as e:
            logger.error(f"Error retrieving environment metrics: {str(e)}")
            return {
                "status": "error",
                "message": f"Error retrieving environment metrics: {str(e)}"
            }
    
    async def generate_deployment_report(self, session_id: str) -> Dict[str, Any]:
        """Generate a comprehensive deployment report."""
        # Get testing session
        testing_session = await self.get_testing_session(session_id)
        
        if testing_session.get("status") == "not_found":
            return testing_session
        
        # Create report
        report = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "title": "Deployment Testing Report",
            "summary": self._generate_summary(testing_session),
            "environment": testing_session.get("environment_details", {}),
            "test_results": {
                "total_tests": testing_session.get("test_count", 0),
                "passed_tests": testing_session.get("execution_results", {}).get("passed_tests", 0),
                "failed_tests": testing_session.get("execution_results", {}).get("failed_tests", 0)
            },
            "issues": self._generate_issue_summary(testing_session),
            "integration_status": testing_session.get("integration_results", {}).get("status", "unknown"),
            "validation_status": testing_session.get("validation_results", {}).get("status", "unknown"),
            "recommendations": self._consolidate_recommendations(testing_session),
            "metrics": await self.get_environment_metrics(testing_session.get("environment_id", ""))
        }
        
        return report
    
    def _generate_summary(self, testing_session: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the deployment testing session."""
        execution_results = testing_session.get("execution_results", {})
        
        total_tests = execution_results.get("total_tests", 0)
        passed_tests = execution_results.get("passed_tests", 0)
        failed_tests = execution_results.get("failed_tests", 0)
        
        environment = testing_session.get("environment_details", {})
        environment_name = environment.get("name", "Unknown")
        environment_type = environment.get("type", "Unknown")
        
        integration_status = testing_session.get("integration_results", {}).get("status", "unknown")
        validation_status = testing_session.get("validation_results", {}).get("status", "unknown")
        
        # Determine overall status
        if (failed_tests == 0 and 
            integration_status == "passed" and 
            validation_status == "passed"):
            overall_status = "Ready for Deployment"
        elif (failed_tests <= 1 and 
             integration_status in ["passed", "partial"] and 
             validation_status in ["passed", "partial"]):
            overall_status = "Minor Issues"
        elif (failed_tests > 0 and failed_tests <= 3) or integration_status == "failed":
            overall_status = "Needs Attention"
        else:
            overall_status = "Significant Issues"
        
        return {
            "overall_status": overall_status,
            "environment": f"{environment_name} ({environment_type})",
            "test_summary": f"{passed_tests}/{total_tests} tests passed ({(passed_tests/total_tests*100) if total_tests > 0 else 0:.1f}%)",
            "integration_status": integration_status,
            "validation_status": validation_status,
            "component_count": testing_session.get("component_count", 0),
            "execution_time": testing_session.get("total_duration"),
            "completed_at": datetime.fromtimestamp(testing_session.get("end_time", time.time())).isoformat()
        }
    
    def _generate_issue_summary(self, testing_session: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of issues found during deployment testing."""
        # Extract issues from different phases
        test_failures = testing_session.get("execution_results", {}).get("failed_tests", 0)
        
        # If no test failures and integration passed, return empty summary
        if (test_failures == 0 and 
            testing_session.get("integration_results", {}).get("status", "") == "passed"):
            return {
                "total_issues": 0,
                "message": "No issues found during deployment testing"
            }
        
        # Count integration issues
        integration_issues = 0
        if testing_session.get("integration_results", {}).get("status", "") != "passed":
            integration_aspects = testing_session.get("integration_results", {}).get("summary", {})
            integration_issues = integration_aspects.get("failed_aspects", 0)
        
        # Count validation issues
        validation_issues = 0
        validation_criteria = testing_session.get("validation_results", {}).get("validation_results", [])
        for criteria in validation_criteria:
            if criteria.get("validation_status", "") != "passed":
                validation_issues += 1
        
        # Extract patterns from analysis if there were test failures
        patterns = []
        if test_failures > 0:
            patterns = testing_session.get("analysis_results", {}).get("patterns", [])
        
        return {
            "total_issues": test_failures + integration_issues + validation_issues,
            "test_failures": test_failures,
            "integration_issues": integration_issues,
            "validation_issues": validation_issues,
            "identified_patterns": len(patterns),
            "high_priority_patterns": sum(1 for p in patterns if p.get("priority") == "high")
        }
    
    def _consolidate_recommendations(self, testing_session: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Consolidate recommendations from all testing phases."""
        all_recommendations = []
        
        # Add recommendations from analysis if there were test failures
        test_failures = testing_session.get("execution_results", {}).get("failed_tests", 0)
        if test_failures > 0:
            analysis_recommendations = testing_session.get("analysis_results", {}).get("recommendations", [])
            for rec in analysis_recommendations:
                all_recommendations.append({
                    "source": "analysis",
                    "priority": rec.get("priority", "medium"),
                    "title": rec.get("title", ""),
                    "description": rec.get("description", ""),
                    "action_items": rec.get("action_items", [])
                })
        
        # Add recommendations from integration validation
        integration_recommendations = testing_session.get("integration_results", {}).get("recommendations", [])
        for rec in integration_recommendations:
            all_recommendations.append({
                "source": "integration",
                "priority": rec.get("priority", "medium"),
                "title": rec.get("title", ""),
                "description": rec.get("description", ""),
                "action_items": rec.get("actions", [])
            })
        
        # Add recommendations from deployment validation
        validation_recommendations = testing_session.get("validation_results", {}).get("recommendations", [])
        for rec in validation_recommendations:
            all_recommendations.append({
                "source": "validation",
                "priority": rec.get("priority", "medium"),
                "title": rec.get("title", ""),
                "description": rec.get("description", ""),
                "action_items": rec.get("action_items", [])
            })
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        return sorted(all_recommendations, key=lambda r: priority_order.get(r.get("priority", "medium"), 1))
    
    async def get_integration_readiness_report(self, environment_id: str) -> Dict[str, Any]:
        """Generate an integration readiness report for an environment."""
        return await self._integration_validator.generate_readiness_report(environment_id)