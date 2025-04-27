import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Set

from component import Component, ComponentState
from resources import ResourceType, PhaseType
from phase_two.models import ComponentDevelopmentContext, ComponentDevelopmentState
from phase_two.test_execution import TestExecutor
from phase_two.utils import use_internal_implementation

logger = logging.getLogger(__name__)

class ComponentDeveloper:
    """Handles component development logic"""
    
    def __init__(self, 
                 state_manager,
                 metrics_manager, 
                 test_agent, 
                 implementation_agent, 
                 integration_agent,
                 test_executor,
                 phase_three_interface,
                 phase_coordination=None,
                 phase_id=None):
        self._state_manager = state_manager
        self._metrics_manager = metrics_manager
        self._test_agent = test_agent
        self._implementation_agent = implementation_agent
        self._integration_agent = integration_agent
        self._test_executor = test_executor
        self._phase_three = phase_three_interface
        self._phase_coordination = phase_coordination
        self._phase_id = phase_id
    
    async def develop_component(self, 
                               component_id: str, 
                               context: ComponentDevelopmentContext,
                               development_contexts: Dict[str, ComponentDevelopmentContext]) -> Dict[str, Any]:
        """Develop a component through the complete lifecycle."""
        try:
            # 1. Test Creation
            context.state = ComponentDevelopmentState.TEST_CREATION
            await self._update_development_state(component_id, context.state)
            
            test_spec_result = await self._test_agent.create_test_specifications(
                context.requirements,
                f"test_spec_{component_id}"
            )
            
            if "error" in test_spec_result:
                logger.error(f"Test specification creation failed for {component_id}: {test_spec_result['error']}")
                context.state = ComponentDevelopmentState.FAILED
                await self._update_development_state(component_id, context.state)
                return {"error": test_spec_result["error"]}
            
            # Update context with test specifications
            context.tests = test_spec_result.get("test_specifications", [])
            context.record_iteration(
                ComponentDevelopmentState.TEST_CREATION,
                {"test_spec_result": test_spec_result}
            )
            
            # 2. Implementation using Phase Three
            context.state = ComponentDevelopmentState.IMPLEMENTATION
            await self._update_development_state(component_id, context.state)
            
            # Extract features from component requirements
            features = context.requirements.get("features", [])
            if not features:
                # If no features are explicitly defined, create a default one
                features = [{
                    "id": f"feature_{component_id}_main",
                    "name": f"{context.component_name} Main Feature",
                    "description": context.description,
                    "dependencies": []
                }]
            
            # Store features in context
            context.features = features
            
            # Process features through Phase Three using coordinated nested execution
            try:
                # Check if we should use coordination
                should_use_internal = await use_internal_implementation(
                    self._phase_coordination, 
                    {"feature_count": len(features)}
                )
                
                if not should_use_internal and self._phase_coordination and self._phase_id:
                    # Use coordinator for nested phase execution
                    logger.info(f"Using coordinator for nested phase three execution from component {component_id}")
                    
                    # Prepare configuration for phase three
                    phase_three_config = {
                        "component_id": component_id,
                        "operation_id": f"phase_three_{component_id}_{int(time.time())}",
                        "handlers": ["phase_two_to_three", "phase_three_to_four"]
                    }
                    
                    # Prepare input data for phase three
                    phase_three_input = {
                        "features": features,
                        "component_id": component_id,
                        "parent_component": context.component_name
                    }
                    
                    # Coordinate nested execution from phase two to phase three
                    feature_result = await self._phase_coordination.coordinate_nested_execution(
                        self._phase_id,  # Parent phase ID (phase two)
                        PhaseType.THREE,  # Target phase type
                        phase_three_input,  # Input data
                        phase_three_config  # Configuration
                    )
                else:
                    # Use legacy approach for feature cultivation
                    feature_result = await self._phase_three.start_feature_cultivation(features)
            except Exception as e:
                logger.error(f"Error in nested phase three execution: {str(e)}")
                feature_result = {
                    "error": f"Nested phase execution failed: {str(e)}",
                    "status": "error"
                }
            
            if "error" in feature_result:
                logger.error(f"Feature cultivation failed for {component_id}: {feature_result['error']}")
                context.state = ComponentDevelopmentState.FAILED
                await self._update_development_state(component_id, context.state)
                return {"error": feature_result["error"]}
            
            # Wait for feature cultivation to complete
            if "operation_id" in feature_result:
                if hasattr(self._phase_three, "get_cultivation_status"):
                    # Using direct phase three interface
                    feature_status = await self._phase_three.get_cultivation_status(feature_result["operation_id"])
                else:
                    # Using coordinator - result already contains the status
                    feature_status = feature_result
            else:
                # No operation ID available
                feature_status = {
                    "status": "unknown",
                    "features": features
                }
            
            # Update context with implementation
            # Combine all feature implementations into a single component implementation
            feature_implementations = []
            for feature_id in feature_result.get("started_features", []):
                feature_status = await self._phase_three.get_feature_status(feature_id)
                if feature_status.get("has_implementation", False):
                    feature_implementations.append(feature_status)
            
            # Create a Component object to track the component
            component_obj = Component(component_id, is_primary=context.requirements.get("is_primary", False))
            component_obj.component_state = ComponentState.DEVELOPMENT
            
            # Simulate implementation creation by combining features
            implementation_result = {
                "component_id": component_id,
                "component_name": context.component_name,
                "features": feature_implementations,
                "implementation": f"# Generated Component: {context.component_name}\n\n" + 
                                "\n\n".join([f"# Feature: {f.get('feature_name', 'Unknown')}\n{f.get('implementation', '')}" 
                                           for f in feature_implementations])
            }
            
            context.implementation = implementation_result.get("implementation", "")
            context.record_iteration(
                ComponentDevelopmentState.IMPLEMENTATION,
                {"implementation_result": implementation_result}
            )
            
            # 3. Testing
            context.state = ComponentDevelopmentState.TESTING
            await self._update_development_state(component_id, context.state)
            
            # Run component tests (simulated)
            test_execution = await self._test_executor.run_component_tests(component_obj, context)
            context.record_iteration(
                ComponentDevelopmentState.TESTING,
                {"test_execution": test_execution}
            )
            
            if test_execution.get("status") == "failed":
                logger.error(f"Component tests failed for {component_id}")
                context.state = ComponentDevelopmentState.FAILED
                await self._update_development_state(component_id, context.state)
                return {"error": "Component tests failed"}
            
            # 4. Integration (if dependencies exist)
            if context.dependencies:
                context.state = ComponentDevelopmentState.INTEGRATION
                await self._update_development_state(component_id, context.state)
                
                # Get dependency implementations
                dependency_implementations = []
                for dep_id in context.dependencies:
                    dep_context = development_contexts.get(dep_id)
                    if dep_context and dep_context.implementation:
                        dependency_implementations.append({
                            "component_id": dep_id,
                            "component_name": dep_context.component_name,
                            "implementation": dep_context.implementation
                        })
                
                # Create integration tests
                integration_result = await self._integration_agent.create_integration_tests(
                    {
                        "component_id": component_id,
                        "component_name": context.component_name,
                        "implementation": context.implementation
                    },
                    dependency_implementations,
                    f"integrate_{component_id}"
                )
                
                # Run integration tests (simulated)
                integration_execution = await self._test_executor.run_integration_tests(
                    component_obj, 
                    integration_result.get("integration_tests", [])
                )
                
                context.record_iteration(
                    ComponentDevelopmentState.INTEGRATION,
                    {
                        "integration_result": integration_result,
                        "integration_execution": integration_execution
                    }
                )
                
                if integration_execution.get("status") == "failed":
                    logger.error(f"Integration tests failed for {component_id}")
                    context.state = ComponentDevelopmentState.FAILED
                    await self._update_development_state(component_id, context.state)
                    return {"error": "Integration tests failed"}
            
            # 5. Mark as completed
            context.state = ComponentDevelopmentState.COMPLETED
            await self._update_development_state(component_id, context.state)
            
            # Create final result object
            final_result = {
                "component_id": component_id,
                "component_name": context.component_name,
                "description": context.description,
                "dependencies": list(context.dependencies),
                "features": context.features,
                "implementation": context.implementation,
                "tests": context.tests,
                "status": "completed"
            }
            
            # Record component completion metric
            await self._metrics_manager.record_metric(
                "component:development:complete",
                1.0,
                metadata={
                    "component_id": component_id,
                    "component_name": context.component_name
                }
            )
            
            logger.info(f"Component development completed for {context.component_name}")
            return final_result
            
        except Exception as e:
            logger.error(f"Error in component development process for {component_id}: {str(e)}", exc_info=True)
            context.state = ComponentDevelopmentState.FAILED
            await self._update_development_state(component_id, context.state)
            
            # Record development error
            await self._metrics_manager.record_metric(
                "component:development:error",
                1.0,
                metadata={
                    "component_id": component_id,
                    "component_name": context.component_name,
                    "error": str(e)
                }
            )
            
            return {
                "error": f"Component development failed: {str(e)}",
                "component_id": component_id,
                "component_name": context.component_name
            }
    
    async def _update_development_state(self, component_id: str, state: ComponentDevelopmentState) -> None:
        """Update development state in state manager."""
        try:
            # Get context from development contexts
            context_dict = await self._state_manager.get_state(f"component:development:{component_id}")
            if not context_dict:
                logger.warning(f"No context found for component {component_id}")
                return
                
            await self._state_manager.set_state(
                f"component:development:{component_id}",
                {
                    "component_id": component_id,
                    "component_name": context_dict.get("component_name", "unknown"),
                    "state": state.name,
                    "timestamp": datetime.now().isoformat()
                },
                ResourceType.STATE
            )
            
            # Record state change metric
            await self._metrics_manager.record_metric(
                "component:development:state_change",
                1.0,
                metadata={
                    "component_id": component_id,
                    "component_name": context_dict.get("component_name", "unknown"),
                    "state": state.name
                }
            )
        except Exception as e:
            logger.error(f"Error updating development state for {component_id}: {str(e)}")
            # Continue execution even if state update fails