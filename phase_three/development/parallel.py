import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime

from resources import (
    ResourceType, 
    EventQueue, 
    StateManager, 
    CacheManager, 
    AgentContextManager, 
    MetricsManager, 
    ErrorHandler, 
    MemoryMonitor
)
from feature import Feature, FeatureState
from phase_four import PhaseFourInterface

from phase_three.models.enums import FeatureDevelopmentState
from phase_three.models.scores import FeaturePerformanceScore
from phase_three.models.context import FeatureDevelopmentContext
from phase_three.agents import (
    FeatureElaborationAgent,
    FeatureTestSpecAgent,
    FeatureIntegrationAgent,
    FeaturePerformanceAgent
)
from phase_three.development.testing import TestExecutor
from phase_three.development.dependencies import DependencyResolver
from phase_three.development.lifecycle import FeatureLifecycleManager

logger = logging.getLogger(__name__)

class ParallelFeatureDevelopment:
    """Manages parallel development of non-dependent features"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 phase_four_interface: PhaseFourInterface,
                 memory_monitor: Optional[MemoryMonitor] = None,
                 max_parallel: int = 3):
        """Initialize parallel feature development manager.
        
        Args:
            event_queue: Queue for system events
            state_manager: Manager for application state
            context_manager: Manager for agent context
            cache_manager: Manager for caching results
            metrics_manager: Manager for metrics collection
            error_handler: Handler for error processing
            phase_four_interface: Interface to Phase Four
            memory_monitor: Optional monitor for memory usage
            max_parallel: Maximum features to develop in parallel
        """
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._context_manager = context_manager
        self._cache_manager = cache_manager
        self._metrics_manager = metrics_manager
        self._error_handler = error_handler
        self._memory_monitor = memory_monitor
        self._phase_four_interface = phase_four_interface
        self._max_parallel = max_parallel
        
        # Create development contexts
        self._development_contexts: Dict[str, FeatureDevelopmentContext] = {}
        self._active_tasks: Dict[str, asyncio.Task] = {}
        
        # Semaphore to limit parallel development
        self._semaphore = asyncio.Semaphore(max_parallel)
        
        # Initialize helper components
        self._test_executor = TestExecutor()
        self._dependency_resolver = DependencyResolver(state_manager)
        self._lifecycle_manager = FeatureLifecycleManager(state_manager, metrics_manager)
        
        # Development agents
        self._elaboration_agent = FeatureElaborationAgent(
            event_queue, state_manager, context_manager, 
            cache_manager, metrics_manager, error_handler, memory_monitor
        )
        self._test_spec_agent = FeatureTestSpecAgent(
            event_queue, state_manager, context_manager, 
            cache_manager, metrics_manager, error_handler, memory_monitor
        )
        self._integration_agent = FeatureIntegrationAgent(
            event_queue, state_manager, context_manager, 
            cache_manager, metrics_manager, error_handler, memory_monitor
        )
        self._performance_agent = FeaturePerformanceAgent(
            event_queue, state_manager, context_manager, 
            cache_manager, metrics_manager, error_handler, memory_monitor
        )
        
        logger.info(f"Parallel feature development initialized with {max_parallel} max parallel tasks")
    
    async def start_feature_development(self, feature_metadata: Dict[str, Any]) -> str:
        """Start development of a new feature.
        
        Args:
            feature_metadata: Metadata for the feature to develop
            
        Returns:
            String feature ID
        """
        feature_id = feature_metadata.get("id", f"feature_{int(time.time())}")
        feature_name = feature_metadata.get("name", "unnamed_feature")
        
        logger.info(f"Starting development of feature {feature_name} ({feature_id})")
        
        # Record development start
        await self._lifecycle_manager.record_development_start(feature_id, feature_name)
        
        # Create feature development context
        context = FeatureDevelopmentContext(
            feature_id=feature_id,
            feature_name=feature_name,
            requirements=feature_metadata
        )
        self._development_contexts[feature_id] = context
        
        # Store context in state manager
        await self._lifecycle_manager.update_development_state(
            feature_id, 
            feature_name, 
            FeatureDevelopmentState.PLANNING
        )
        
        # Start development task
        task = asyncio.create_task(self._develop_feature(feature_id))
        self._active_tasks[feature_id] = task
        
        # Add task cleanup callback
        task.add_done_callback(lambda t: self._handle_task_completion(feature_id, t))
        
        return feature_id
    
    def _handle_task_completion(self, feature_id: str, task: asyncio.Task) -> None:
        """Handle the completion of a feature development task.
        
        Args:
            feature_id: ID of the feature
            task: Completed asyncio task
        """
        # Remove from active tasks
        self._active_tasks.pop(feature_id, None)
        
        # Check for exceptions
        if task.exception():
            logger.error(f"Feature development for {feature_id} failed with exception: {task.exception()}")
            
            # Update context state
            if feature_id in self._development_contexts:
                self._development_contexts[feature_id].state = FeatureDevelopmentState.FAILED
                
                # Record development error
                asyncio.create_task(self._lifecycle_manager.record_development_error(
                    feature_id,
                    self._development_contexts[feature_id].feature_name,
                    str(task.exception())
                ))
    
    async def _develop_feature(self, feature_id: str) -> None:
        """Develop a feature through the complete lifecycle.
        
        Args:
            feature_id: ID of the feature to develop
        """
        # Get development context
        context = self._development_contexts.get(feature_id)
        if not context:
            logger.error(f"Development context not found for feature {feature_id}")
            return
        
        try:
            # Acquire semaphore to limit parallel development
            async with self._semaphore:
                logger.info(f"Starting development process for {context.feature_name}")
                
                # 1. Feature Elaboration
                context.state = FeatureDevelopmentState.ELABORATION
                await self._lifecycle_manager.update_development_state(
                    feature_id, context.feature_name, context.state
                )
                
                elaboration_result = await self._elaboration_agent.elaborate_feature(
                    context.requirements,
                    f"elaborate_{feature_id}"
                )
                
                if "error" in elaboration_result:
                    logger.error(f"Feature elaboration failed for {feature_id}: {elaboration_result['error']}")
                    context.state = FeatureDevelopmentState.FAILED
                    await self._lifecycle_manager.update_development_state(
                        feature_id, context.feature_name, context.state
                    )
                    return
                
                # Update context with elaborated requirements
                context.requirements = elaboration_result
                context.dependencies = set(elaboration_result.get("dependencies", []))
                context.record_iteration(
                    FeatureDevelopmentState.ELABORATION,
                    {"elaboration_result": elaboration_result}
                )
                
                # 2. Test Specification Creation
                context.state = FeatureDevelopmentState.TEST_CREATION
                await self._lifecycle_manager.update_development_state(
                    feature_id, context.feature_name, context.state
                )
                
                test_spec_result = await self._test_spec_agent.create_test_specifications(
                    context.requirements,
                    f"test_spec_{feature_id}"
                )
                
                if "error" in test_spec_result:
                    logger.error(f"Test specification creation failed for {feature_id}: {test_spec_result['error']}")
                    context.state = FeatureDevelopmentState.FAILED
                    await self._lifecycle_manager.update_development_state(
                        feature_id, context.feature_name, context.state
                    )
                    return
                
                # Update context with test specifications
                context.tests = test_spec_result.get("test_specifications", [])
                context.record_iteration(
                    FeatureDevelopmentState.TEST_CREATION,
                    {"test_spec_result": test_spec_result}
                )
                
                # Use Phase Four to generate actual test code based on specifications
                test_implementation_requirements = {
                    "id": f"tests_{feature_id}",
                    "name": f"Tests for {context.feature_name}",
                    "requirements": {
                        "test_specifications": context.tests,
                        "feature_requirements": context.requirements
                    },
                    "language": "python"
                }
                
                test_implementation_result = await self._phase_four_interface.process_feature_code(
                    test_implementation_requirements
                )
                
                if not test_implementation_result.get("success", False):
                    logger.error(f"Test implementation failed for {feature_id}: {test_implementation_result.get('error', 'Unknown error')}")
                    # We continue anyway as test implementation failure shouldn't stop development
                    # But we record the failure in the context
                    context.record_iteration(
                        FeatureDevelopmentState.TEST_CREATION,
                        {"test_implementation_result": test_implementation_result, "status": "failed"}
                    )
                else:
                    # Update tests with actual code
                    for i, test in enumerate(context.tests):
                        test["test_code"] = test_implementation_result.get("code", "# Test implementation not available")
                        
                    context.record_iteration(
                        FeatureDevelopmentState.TEST_CREATION,
                        {"test_implementation_result": test_implementation_result, "status": "success"}
                    )
                
                # 3. Implementation using Phase Four
                context.state = FeatureDevelopmentState.IMPLEMENTATION
                await self._lifecycle_manager.update_development_state(
                    feature_id, context.feature_name, context.state
                )
                
                # Prepare feature requirements for Phase Four
                implementation_requirements = {
                    "id": feature_id,
                    "name": context.feature_name,
                    "requirements": context.requirements,
                    "test_cases": context.tests,
                    "language": "python"
                }
                
                # Call Phase Four for implementation
                implementation_result = await self._phase_four_interface.process_feature_code(
                    implementation_requirements
                )
                
                if not implementation_result.get("success", False):
                    logger.error(f"Implementation failed for {feature_id}: {implementation_result.get('error', 'Unknown error')}")
                    context.state = FeatureDevelopmentState.FAILED
                    await self._lifecycle_manager.update_development_state(
                        feature_id, context.feature_name, context.state
                    )
                    return
                
                # Update context with implementation
                context.implementation = implementation_result.get("code", "")
                context.record_iteration(
                    FeatureDevelopmentState.IMPLEMENTATION,
                    {"implementation_result": implementation_result}
                )
                
                # 4. Testing
                context.state = FeatureDevelopmentState.TESTING
                await self._lifecycle_manager.update_development_state(
                    feature_id, context.feature_name, context.state
                )
                
                # Create Feature object for tracking
                feature_obj = Feature(feature_id, context.feature_name)
                feature_obj.component_state = FeatureState.TESTING
                
                # Run tests (simulated here)
                test_execution = await self._test_executor.run_tests(feature_obj, context)
                context.record_iteration(
                    FeatureDevelopmentState.TESTING,
                    {"test_execution": test_execution}
                )
                
                # 5. Integration (if dependencies exist)
                if context.dependencies:
                    context.state = FeatureDevelopmentState.INTEGRATION
                    await self._lifecycle_manager.update_development_state(
                        feature_id, context.feature_name, context.state
                    )
                    
                    # Get dependency implementations
                    dependency_implementations = await self._dependency_resolver.get_dependency_implementations(
                        context.dependencies, 
                        self._development_contexts
                    )
                    
                    # Create integration tests
                    integration_result = await self._integration_agent.create_integration_tests(
                        {
                            "feature_id": feature_id,
                            "feature_name": context.feature_name,
                            "implementation": context.implementation
                        },
                        dependency_implementations,
                        f"integrate_{feature_id}"
                    )
                    
                    context.record_iteration(
                        FeatureDevelopmentState.INTEGRATION,
                        {"integration_result": integration_result}
                    )
                
                # 6. Performance Evaluation
                performance_result = await self._performance_agent.evaluate_performance(
                    {
                        "feature_id": feature_id,
                        "feature_name": context.feature_name,
                        "implementation": context.implementation
                    },
                    {
                        "test_results": test_execution,
                        "integration_results": context.iteration_history[-1]["details"].get("integration_result", {}) if context.dependencies else {}
                    },
                    f"performance_{feature_id}"
                )
                
                # Create performance score object
                performance_score = FeaturePerformanceScore(feature_id=feature_id)
                performance_metrics = performance_result.get("performance_metrics", {})
                performance_score.scores = {
                    key: value for key, value in (
                        (FeaturePerformanceMetrics.CODE_QUALITY, performance_metrics.get("code_quality", 0)),
                        (FeaturePerformanceMetrics.TEST_COVERAGE, performance_metrics.get("test_coverage", 0)),
                        (FeaturePerformanceMetrics.BUILD_STABILITY, performance_metrics.get("build_stability", 0)),
                        (FeaturePerformanceMetrics.MAINTAINABILITY, performance_metrics.get("maintainability", 0)),
                        (FeaturePerformanceMetrics.RUNTIME_EFFICIENCY, performance_metrics.get("runtime_efficiency", 0)),
                        (FeaturePerformanceMetrics.INTEGRATION_SCORE, performance_metrics.get("integration_score", 0))
                    )
                }
                
                # Store implementation in state manager
                await self._state_manager.set_state(
                    f"feature:implementation:{feature_id}",
                    {
                        "feature_id": feature_id,
                        "feature_name": context.feature_name,
                        "implementation": context.implementation,
                        "timestamp": datetime.now().isoformat()
                    },
                    ResourceType.STATE
                )
                
                # Update context with performance score
                context.record_iteration(
                    FeatureDevelopmentState.COMPLETED,
                    {"performance_result": performance_result},
                    performance_score
                )
                
                # 7. Complete development
                context.state = FeatureDevelopmentState.COMPLETED
                await self._lifecycle_manager.update_development_state(
                    feature_id, context.feature_name, context.state
                )
                
                # Record development completion
                await self._lifecycle_manager.record_development_completion(
                    feature_id,
                    context.feature_name,
                    performance_result.get("overall_score", 0)
                )
                
                logger.info(f"Feature development completed for {context.feature_name}")
                
        except Exception as e:
            logger.error(f"Error in feature development process for {feature_id}: {str(e)}", exc_info=True)
            context.state = FeatureDevelopmentState.FAILED
            await self._lifecycle_manager.update_development_state(
                feature_id, context.feature_name, context.state
            )
            
            # Record development error
            await self._lifecycle_manager.record_development_error(
                feature_id,
                context.feature_name,
                str(e)
            )
    
    async def get_feature_status(self, feature_id: str) -> Dict[str, Any]:
        """Get the current status of a feature.
        
        Args:
            feature_id: ID of the feature to get status for
            
        Returns:
            Dict containing feature status
        """
        context = self._development_contexts.get(feature_id)
        if not context:
            # Try to get from state manager
            state = await self._state_manager.get_state(f"feature:development:{feature_id}")
            if not state:
                return {"error": f"Feature {feature_id} not found"}
            return state
            
        # Get status from context
        feature_status = {
            "feature_id": feature_id,
            "feature_name": context.feature_name,
            "state": context.state.name,
            "dependencies": list(context.dependencies),
            "has_tests": len(context.tests) > 0,
            "has_implementation": bool(context.implementation),
            "iterations": len(context.iteration_history),
            "performance": None
        }
        
        # Add performance information if available
        if context.performance_scores:
            latest_score = context.performance_scores[-1]
            feature_status["performance"] = {
                "overall_score": latest_score.get_overall_score(),
                "metrics": {k.name.lower(): v for k, v in latest_score.scores.items()},
                "timestamp": latest_score.timestamp.isoformat()
            }
            
        return feature_status
    
    async def get_all_feature_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get statuses of all features.
        
        Returns:
            Dict mapping feature IDs to status dicts
        """
        statuses = {}
        
        for feature_id in self._development_contexts:
            statuses[feature_id] = await self.get_feature_status(feature_id)
            
        return statuses