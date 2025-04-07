import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime

from resources import (
    ResourceType, 
    ResourceState, 
    CircuitBreakerConfig, 
    ErrorHandler, 
    EventQueue, 
    ResourceEventTypes, 
    StateManager, 
    CacheManager, 
    AgentContextManager, 
    MetricsManager, 
    HealthTracker, 
    MemoryMonitor, 
    SystemMonitor,
    PhaseCoordinationIntegration,
    PhaseType,
    PhaseState as CoordinationPhaseState
)
from resources.monitoring import CircuitBreaker, CircuitOpenError, HealthStatus
from interface import AgentInterface, ValidationManager, AgentState
from component import Component, ComponentState
from phase_three import PhaseThreeInterface
from phase_zero import PhaseZeroOrchestrator

logger = logging.getLogger(__name__)

class ComponentDevelopmentState(Enum):
    """States for component development process"""
    PLANNING = auto()      # Initial planning phase
    TEST_CREATION = auto() # Creating tests for the component
    IMPLEMENTATION = auto() # Implementing the component
    TESTING = auto()       # Running tests
    INTEGRATION = auto()   # Integrating with other components
    SYSTEM_TESTING = auto() # Testing the full system
    DEPLOYMENT = auto()    # Deploying the component
    COMPLETED = auto()     # Component development complete
    FAILED = auto()        # Component development failed

@dataclass
class ComponentDevelopmentContext:
    """Context for component development process"""
    component_id: str
    component_name: str
    description: str
    requirements: Dict[str, Any]
    dependencies: Set[str] = field(default_factory=set)
    features: List[Dict[str, Any]] = field(default_factory=list)
    state: ComponentDevelopmentState = ComponentDevelopmentState.PLANNING
    tests: List[Dict[str, Any]] = field(default_factory=list)
    implementation: Optional[str] = None
    iteration_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def record_iteration(self, state: ComponentDevelopmentState, 
                         details: Dict[str, Any]) -> None:
        """Record an iteration in the component development process"""
        self.state = state
        self.iteration_history.append({
            "state": state.name,
            "timestamp": datetime.now().isoformat(),
            "details": details
        })

class ComponentTestCreationAgent(AgentInterface):
    """Agent responsible for creating component test specifications"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "component_test_creation_agent", 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler,
            memory_monitor
        )
        self._validation_manager = ValidationManager(event_queue, state_manager, context_manager)
        
    async def create_test_specifications(self, 
                                       component_requirements: Dict[str, Any],
                                       operation_id: str) -> Dict[str, Any]:
        """Create test specifications for a component based on requirements."""
        try:
            logger.info(f"Creating test specifications for component {component_requirements.get('name', 'unknown')}")
            
            # Set agent state to processing
            await self.set_agent_state(AgentState.PROCESSING)
            
            # Prepare requirements for the prompt
            requirements_str = json.dumps(component_requirements)
            
            # Get component name and id
            component_name = component_requirements.get("name", "unnamed_component")
            component_id = component_requirements.get("component_id", f"component_{operation_id}")
            
            # Create schema for validation
            schema = {
                "type": "object",
                "required": ["test_specifications", "test_coverage"],
                "properties": {
                    "test_specifications": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["id", "name", "description", "test_type", "expected_result"],
                            "properties": {
                                "id": {"type": "string"},
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "test_type": {"type": "string"},
                                "expected_result": {"type": "string"},
                                "dependencies": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    },
                    "test_coverage": {
                        "type": "object",
                        "properties": {
                            "requirements_covered": {"type": "array", "items": {"type": "string"}},
                            "coverage_percentage": {"type": "number"}
                        }
                    }
                }
            }
            
            # Generate system prompt for test specification creation
            system_prompt = """You are an expert test engineer specializing in test-driven development.
Create comprehensive test specifications for the provided component requirements.
Focus on creating:
1. Unit test specifications that verify individual functionalities
2. Integration test specifications for dependencies
3. Edge case test specifications for robustness
4. Performance test specifications for non-functional requirements

Return your response as a JSON object with these fields:
- test_specifications: An array of test specification objects, each with:
  - id: A unique identifier for the test
  - name: The test name
  - description: What the test verifies
  - test_type: The type of test (unit, integration, edge_case, performance)
  - expected_result: The expected outcome of the test
  - dependencies: Any dependencies needed to run the test
- test_coverage: An object showing what requirements are covered and the coverage percentage
"""
            
            # Call LLM to create test specifications
            response = await self.process_with_validation(
                conversation=requirements_str,
                system_prompt_info=(system_prompt,),
                schema=schema,
                current_phase="test_specification",
                operation_id=operation_id,
                metadata={"component_name": component_name, "component_id": component_id}
            )
            
            # Update state to complete
            await self.set_agent_state(AgentState.COMPLETE)
            
            # Add component metadata to the response
            response.update({
                "component_name": component_name,
                "component_id": component_id,
                "operation_id": operation_id
            })
            
            logger.info(f"Test specification creation completed for {component_name}")
            return response
            
        except Exception as e:
            logger.error(f"Error creating test specifications: {str(e)}", exc_info=True)
            await self.set_agent_state(AgentState.ERROR)
            
            return {
                "error": f"Test specification creation failed: {str(e)}",
                "component_name": component_requirements.get("name", "unnamed_component"),
                "component_id": component_requirements.get("component_id", f"component_{operation_id}"),
                "operation_id": operation_id
            }

class ComponentImplementationAgent(AgentInterface):
    """Agent responsible for implementing components"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "component_implementation_agent", 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler,
            memory_monitor
        )
        self._validation_manager = ValidationManager(event_queue, state_manager, context_manager)
        
    async def implement_component(self, 
                                component_requirements: Dict[str, Any],
                                test_specifications: Dict[str, Any],
                                operation_id: str) -> Dict[str, Any]:
        """Implement a component based on requirements and test specifications."""
        try:
            logger.info(f"Implementing component {component_requirements.get('name', 'unknown')}")
            
            # Set agent state to processing
            await self.set_agent_state(AgentState.PROCESSING)
            
            # Prepare input data for the prompt
            implementation_data = {
                "requirements": component_requirements,
                "test_specifications": test_specifications
            }
            implementation_str = json.dumps(implementation_data)
            
            # Get component name and id
            component_name = component_requirements.get("name", "unnamed_component")
            component_id = component_requirements.get("component_id", f"component_{operation_id}")
            
            # Create schema for validation
            schema = {
                "type": "object",
                "required": ["implementation", "implementation_metadata"],
                "properties": {
                    "implementation": {"type": "string"},
                    "implementation_metadata": {
                        "type": "object",
                        "required": ["features", "dependencies", "interfaces"],
                        "properties": {
                            "features": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["id", "name", "description"],
                                    "properties": {
                                        "id": {"type": "string"},
                                        "name": {"type": "string"},
                                        "description": {"type": "string"}
                                    }
                                }
                            },
                            "dependencies": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "interfaces": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["name", "description", "methods"],
                                    "properties": {
                                        "name": {"type": "string"},
                                        "description": {"type": "string"},
                                        "methods": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            # Generate system prompt for implementation
            system_prompt = """You are an expert software developer specializing in test-driven development.
Implement the provided component based on the requirements and test specifications.
Focus on creating:
1. Clean, modular code that satisfies all requirements
2. Code that will pass the provided test specifications
3. Well-defined interfaces for other components to interact with
4. Proper handling of dependencies

Return your response as a JSON object with these fields:
- implementation: A string containing the Python code for the component
- implementation_metadata: An object with:
  - features: An array of feature objects, each with:
    - id: A unique identifier for the feature
    - name: The feature name
    - description: A description of the feature
  - dependencies: An array of component dependencies
  - interfaces: An array of interface objects, each with:
    - name: The interface name
    - description: A description of the interface
    - methods: An array of method signatures
"""
            
            # Call LLM to implement component
            response = await self.process_with_validation(
                conversation=implementation_str,
                system_prompt_info=(system_prompt,),
                schema=schema,
                current_phase="component_implementation",
                operation_id=operation_id,
                metadata={"component_name": component_name, "component_id": component_id}
            )
            
            # Update state to complete
            await self.set_agent_state(AgentState.COMPLETE)
            
            # Add component metadata to the response
            response.update({
                "component_name": component_name,
                "component_id": component_id,
                "operation_id": operation_id
            })
            
            logger.info(f"Component implementation completed for {component_name}")
            return response
            
        except Exception as e:
            logger.error(f"Error implementing component: {str(e)}", exc_info=True)
            await self.set_agent_state(AgentState.ERROR)
            
            return {
                "error": f"Component implementation failed: {str(e)}",
                "component_name": component_requirements.get("name", "unnamed_component"),
                "component_id": component_requirements.get("component_id", f"component_{operation_id}"),
                "operation_id": operation_id
            }

class IntegrationTestAgent(AgentInterface):
    """Agent responsible for creating integration tests between components"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "integration_test_agent", 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler,
            memory_monitor
        )
        self._validation_manager = ValidationManager(event_queue, state_manager, context_manager)
        
    async def create_integration_tests(self,
                                    component_implementation: Dict[str, Any],
                                    dependencies: List[Dict[str, Any]],
                                    operation_id: str) -> Dict[str, Any]:
        """Create integration tests between a component and its dependencies."""
        try:
            logger.info(f"Creating integration tests for {component_implementation.get('component_name', 'unknown')}")
            
            # Set agent state to processing
            await self.set_agent_state(AgentState.PROCESSING)
            
            # Prepare input data for the prompt
            integration_data = {
                "component": component_implementation,
                "dependencies": dependencies
            }
            integration_str = json.dumps(integration_data)
            
            # Get component name and id
            component_name = component_implementation.get("component_name", "unnamed_component")
            component_id = component_implementation.get("component_id", f"component_{operation_id}")
            
            # Create schema for validation
            schema = {
                "type": "object",
                "required": ["integration_tests", "integration_score"],
                "properties": {
                    "integration_tests": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["id", "name", "description", "test_code", "components_tested"],
                            "properties": {
                                "id": {"type": "string"},
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "test_code": {"type": "string"},
                                "components_tested": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    },
                    "integration_score": {"type": "number"},
                    "integration_issues": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["issue_type", "description", "severity"],
                            "properties": {
                                "issue_type": {"type": "string"},
                                "description": {"type": "string"},
                                "severity": {"type": "string"},
                                "fix_suggestion": {"type": "string"}
                            }
                        }
                    }
                }
            }
            
            # Generate system prompt for integration test creation
            system_prompt = """You are an expert integration test engineer.
Analyze the component implementation and its dependencies to create comprehensive integration tests.
Focus on:
1. Testing the interactions between the component and its dependencies
2. Identifying potential integration issues
3. Ensuring all communication paths are tested
4. Validating data flows between components

Return your response as a JSON object with these fields:
- integration_tests: An array of test case objects, each with:
  - id: A unique identifier for the test
  - name: The test name
  - description: What the integration test verifies
  - test_code: Python code implementing the integration test
  - components_tested: Array of component IDs being tested together
- integration_score: A score from 0-100 indicating integration quality
- integration_issues: An array of potential issues found, each with:
  - issue_type: Type of integration issue
  - description: Detailed description of the issue
  - severity: "low", "medium", or "high"
  - fix_suggestion: Suggested fix for the issue
"""
            
            # Call LLM to create integration tests
            response = await self.process_with_validation(
                conversation=integration_str,
                system_prompt_info=(system_prompt,),
                schema=schema,
                current_phase="integration_test_creation",
                operation_id=operation_id,
                metadata={"component_name": component_name, "component_id": component_id}
            )
            
            # Update state to complete
            await self.set_agent_state(AgentState.COMPLETE)
            
            # Add component metadata to the response
            response.update({
                "component_name": component_name,
                "component_id": component_id,
                "operation_id": operation_id
            })
            
            logger.info(f"Integration test creation completed for {component_name}")
            return response
            
        except Exception as e:
            logger.error(f"Error creating integration tests: {str(e)}", exc_info=True)
            await self.set_agent_state(AgentState.ERROR)
            
            return {
                "error": f"Integration test creation failed: {str(e)}",
                "component_name": component_implementation.get("component_name", "unnamed_component"),
                "component_id": component_implementation.get("component_id", f"component_{operation_id}"),
                "operation_id": operation_id
            }

class SystemTestAgent(AgentInterface):
    """Agent responsible for creating system tests"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "system_test_agent", 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler,
            memory_monitor
        )
        self._validation_manager = ValidationManager(event_queue, state_manager, context_manager)
        
    async def create_system_tests(self,
                               components: List[Dict[str, Any]],
                               system_requirements: Dict[str, Any],
                               operation_id: str) -> Dict[str, Any]:
        """Create system-level tests for the complete application."""
        try:
            logger.info(f"Creating system tests for {len(components)} components")
            
            # Set agent state to processing
            await self.set_agent_state(AgentState.PROCESSING)
            
            # Prepare input data for the prompt
            system_data = {
                "components": components,
                "requirements": system_requirements
            }
            system_str = json.dumps(system_data)
            
            # Create schema for validation
            schema = {
                "type": "object",
                "required": ["system_tests", "coverage_analysis"],
                "properties": {
                    "system_tests": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["id", "name", "description", "test_code", "components_involved"],
                            "properties": {
                                "id": {"type": "string"},
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "test_code": {"type": "string"},
                                "components_involved": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    },
                    "coverage_analysis": {
                        "type": "object",
                        "required": ["requirements_covered", "components_covered", "coverage_percentage"],
                        "properties": {
                            "requirements_covered": {"type": "array", "items": {"type": "string"}},
                            "components_covered": {"type": "array", "items": {"type": "string"}},
                            "coverage_percentage": {"type": "number"}
                        }
                    }
                }
            }
            
            # Generate system prompt for system test creation
            system_prompt = """You are an expert system test engineer.
Create comprehensive system tests for the complete application based on the components and requirements.
Focus on:
1. End-to-end functionality testing
2. System-level integration testing
3. Performance and reliability testing at the system level
4. Comprehensive coverage of system requirements

Return your response as a JSON object with these fields:
- system_tests: An array of test case objects, each with:
  - id: A unique identifier for the test
  - name: The test name
  - description: What the system test verifies
  - test_code: Python code implementing the system test
  - components_involved: Array of component IDs involved in the test
- coverage_analysis: An object with:
  - requirements_covered: Array of requirement IDs covered by the tests
  - components_covered: Array of component IDs covered by the tests
  - coverage_percentage: Percentage of system requirements covered
"""
            
            # Call LLM to create system tests
            response = await self.process_with_validation(
                conversation=system_str,
                system_prompt_info=(system_prompt,),
                schema=schema,
                current_phase="system_test_creation",
                operation_id=operation_id
            )
            
            # Update state to complete
            await self.set_agent_state(AgentState.COMPLETE)
            
            # Add operation ID to the response
            response["operation_id"] = operation_id
            
            logger.info(f"System test creation completed for {len(components)} components")
            return response
            
        except Exception as e:
            logger.error(f"Error creating system tests: {str(e)}", exc_info=True)
            await self.set_agent_state(AgentState.ERROR)
            
            return {
                "error": f"System test creation failed: {str(e)}",
                "operation_id": operation_id
            }

class DeploymentTestAgent(AgentInterface):
    """Agent responsible for creating deployment tests"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "deployment_test_agent", 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler,
            memory_monitor
        )
        self._validation_manager = ValidationManager(event_queue, state_manager, context_manager)
        
    async def create_deployment_tests(self,
                                   components: List[Dict[str, Any]],
                                   system_requirements: Dict[str, Any],
                                   operation_id: str) -> Dict[str, Any]:
        """Create deployment tests for the application."""
        try:
            logger.info(f"Creating deployment tests for {len(components)} components")
            
            # Set agent state to processing
            await self.set_agent_state(AgentState.PROCESSING)
            
            # Prepare input data for the prompt
            deployment_data = {
                "components": components,
                "requirements": system_requirements
            }
            deployment_str = json.dumps(deployment_data)
            
            # Create schema for validation
            schema = {
                "type": "object",
                "required": ["deployment_tests", "deployment_checks"],
                "properties": {
                    "deployment_tests": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["id", "name", "description", "test_code"],
                            "properties": {
                                "id": {"type": "string"},
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "test_code": {"type": "string"}
                            }
                        }
                    },
                    "deployment_checks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["check_type", "description", "verification_method"],
                            "properties": {
                                "check_type": {"type": "string"},
                                "description": {"type": "string"},
                                "verification_method": {"type": "string"}
                            }
                        }
                    }
                }
            }
            
            # Generate system prompt for deployment test creation
            system_prompt = """You are an expert deployment engineer.
Create comprehensive deployment tests for the application based on the components and requirements.
Focus on:
1. Environment validation tests
2. Dependency availability checks
3. Installation verification tests
4. Post-deployment health checks

Return your response as a JSON object with these fields:
- deployment_tests: An array of test case objects, each with:
  - id: A unique identifier for the test
  - name: The test name
  - description: What the deployment test verifies
  - test_code: Python code implementing the deployment test
- deployment_checks: An array of manual check objects, each with:
  - check_type: Type of deployment check
  - description: Detailed description of the check
  - verification_method: Method to verify the check
"""
            
            # Call LLM to create deployment tests
            response = await self.process_with_validation(
                conversation=deployment_str,
                system_prompt_info=(system_prompt,),
                schema=schema,
                current_phase="deployment_test_creation",
                operation_id=operation_id
            )
            
            # Update state to complete
            await self.set_agent_state(AgentState.COMPLETE)
            
            # Add operation ID to the response
            response["operation_id"] = operation_id
            
            logger.info(f"Deployment test creation completed for {len(components)} components")
            return response
            
        except Exception as e:
            logger.error(f"Error creating deployment tests: {str(e)}", exc_info=True)
            await self.set_agent_state(AgentState.ERROR)
            
            return {
                "error": f"Deployment test creation failed: {str(e)}",
                "operation_id": operation_id
            }

class PhaseTwo:
    """Manages the systematic development process from components to deployment"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 phase_zero: PhaseZeroOrchestrator,
                 phase_three: PhaseThreeInterface,
                 memory_monitor: Optional[MemoryMonitor] = None,
                 system_monitor: Optional[SystemMonitor] = None,
                 phase_coordination: Optional[PhaseCoordinationIntegration] = None):
        # Initialize resource managers
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._context_manager = context_manager
        self._cache_manager = cache_manager
        self._metrics_manager = metrics_manager
        self._error_handler = error_handler
        
        # References to other phases
        self._phase_zero = phase_zero
        self._phase_three = phase_three
        
        # Monitoring components
        self._memory_monitor = memory_monitor
        self._system_monitor = system_monitor
        
        # Phase coordination
        self._phase_coordination = phase_coordination
        if not self._phase_coordination:
            # Create phase coordination if not provided
            self._phase_coordination = PhaseCoordinationIntegration(
                event_queue,
                state_manager,
                context_manager,
                cache_manager,
                metrics_manager,
                error_handler,
                memory_monitor,
                system_monitor
            )
            # Initialize the coordination
            asyncio.create_task(self._phase_coordination.initialize())
        
        # Initialize agents
        self._test_agent = ComponentTestCreationAgent(
            event_queue, state_manager, context_manager, 
            cache_manager, metrics_manager, error_handler, memory_monitor
        )
        self._implementation_agent = ComponentImplementationAgent(
            event_queue, state_manager, context_manager, 
            cache_manager, metrics_manager, error_handler, memory_monitor
        )
        self._integration_agent = IntegrationTestAgent(
            event_queue, state_manager, context_manager, 
            cache_manager, metrics_manager, error_handler, memory_monitor
        )
        self._system_test_agent = SystemTestAgent(
            event_queue, state_manager, context_manager, 
            cache_manager, metrics_manager, error_handler, memory_monitor
        )
        self._deployment_agent = DeploymentTestAgent(
            event_queue, state_manager, context_manager, 
            cache_manager, metrics_manager, error_handler, memory_monitor
        )
        
        # Track development contexts
        self._development_contexts: Dict[str, ComponentDevelopmentContext] = {}
        self._completed_components: List[Dict[str, Any]] = []
        
        # Track processing state
        self._is_processing = False
        self._start_time = None
        self._phase_id = None
        
        # Register with system monitor if available
        if self._system_monitor:
            asyncio.create_task(
                self._system_monitor.register_component("phase_two", {
                    "type": "phase",
                    "description": "Phase Two - Systematic Development",
                    "depends_on": ["phase_one", "phase_three"]
                })
            )
            
        logger.info("Phase Two initialized")
        
    async def process_structural_components(self, 
                                         structural_components: List[Dict[str, Any]],
                                         system_requirements: Dict[str, Any],
                                         operation_id: str,
                                         parent_phase_id: Optional[str] = None) -> Dict[str, Any]:
        """Process the structural components from Phase One and develop the system."""
        if self._is_processing:
            logger.warning("Phase Two is already processing components")
            return {
                "status": "already_processing",
                "message": "Phase Two is already processing components",
                "operation_id": operation_id
            }
            
        self._is_processing = True
        self._start_time = time.time()
        
        try:
            # Initialize phase with the coordinator if we don't have a phase ID yet
            if not self._phase_id:
                config = {
                    "operation_id": operation_id,
                    "component_count": len(structural_components),
                    "handlers": ["phase_one_to_two", "phase_two_to_three"]
                }
                self._phase_id = await self._phase_coordination.initialize_phase_two(config, parent_phase_id)
                logger.info(f"Phase Two initialized with coordination ID: {self._phase_id}")
            
            # Record start of phase two
            await self._metrics_manager.record_metric(
                "phase_two:start",
                1.0,
                metadata={
                    "operation_id": operation_id,
                    "component_count": len(structural_components),
                    "phase_id": self._phase_id
                }
            )
            
            # Sort components by dependencies to determine processing order
            sorted_components = self._sort_components_by_dependencies(structural_components)
            
            logger.info(f"Starting component development process for {len(sorted_components)} components")
            
            # Process components in series, from most fundamental to least
            for component_data in sorted_components:
                component_id = component_data.get("id", f"component_{int(time.time())}")
                component_name = component_data.get("name", "unnamed_component")
                
                logger.info(f"Starting development for component {component_name} ({component_id})")
                
                # Create development context
                context = ComponentDevelopmentContext(
                    component_id=component_id,
                    component_name=component_name,
                    description=component_data.get("description", ""),
                    requirements=component_data,
                    dependencies=set(component_data.get("dependencies", []))
                )
                self._development_contexts[component_id] = context
                
                # Store context in state manager
                await self._state_manager.set_state(
                    f"component:development:{component_id}",
                    {
                        "component_id": component_id,
                        "component_name": component_name,
                        "state": context.state.name,
                        "timestamp": datetime.now().isoformat()
                    },
                    ResourceType.STATE
                )
                
                # Develop the component
                component_result = await self._develop_component(component_id)
                
                # Handle development result
                if "error" in component_result:
                    logger.error(f"Component development failed for {component_id}: {component_result['error']}")
                else:
                    logger.info(f"Component development completed for {component_name}")
                    self._completed_components.append(component_result)
            
            # Create system tests once all components are implemented
            if self._completed_components:
                system_test_result = await self._system_test_agent.create_system_tests(
                    self._completed_components,
                    system_requirements,
                    f"system_tests_{operation_id}"
                )
                
                # Run system tests (simulated)
                system_test_execution = await self._run_system_tests(system_test_result)
                
                # Create deployment tests
                deployment_test_result = await self._deployment_agent.create_deployment_tests(
                    self._completed_components,
                    system_requirements,
                    f"deployment_tests_{operation_id}"
                )
                
                # Run deployment tests (simulated)
                deployment_execution = await self._run_deployment_tests(deployment_test_result)
            else:
                system_test_execution = {"status": "skipped", "reason": "No components completed"}
                deployment_execution = {"status": "skipped", "reason": "No components completed"}
            
            # Prepare final result
            execution_time = time.time() - self._start_time
            result = {
                "status": "completed",
                "operation_id": operation_id,
                "components_processed": len(structural_components),
                "components_completed": len(self._completed_components),
                "execution_time_seconds": execution_time,
                "system_test_results": system_test_execution,
                "deployment_results": deployment_execution,
                "timestamp": datetime.now().isoformat()
            }
            
            # Record completion metric
            await self._metrics_manager.record_metric(
                "phase_two:complete",
                1.0,
                metadata={
                    "operation_id": operation_id,
                    "components_completed": len(self._completed_components),
                    "execution_time": execution_time
                }
            )
            
            logger.info(f"Phase Two completed processing {len(structural_components)} components in {execution_time:.2f} seconds")
            
            # If we have a phase ID and the coordinator is available, update phase state
            if self._phase_id:
                try:
                    # Create checkpoint for completion state
                    checkpoint_id = await self._phase_coordination.create_checkpoint(self._phase_id)
                    logger.info(f"Created completion checkpoint {checkpoint_id} for phase {self._phase_id}")
                except Exception as coord_error:
                    logger.warning(f"Failed to create checkpoint: {str(coord_error)}")
            
            self._is_processing = False
            return result
            
        except Exception as e:
            # Record error metric
            await self._metrics_manager.record_metric(
                "phase_two:error",
                1.0,
                metadata={
                    "operation_id": operation_id,
                    "error": str(e),
                    "phase_id": self._phase_id if hasattr(self, '_phase_id') else None
                }
            )
            
            # Try to report error to coordinator if we have a phase ID
            if hasattr(self, '_phase_id') and self._phase_id:
                try:
                    # Attempt to abort the phase with the coordinator
                    await self._phase_coordination.abort_phase(
                        self._phase_id, 
                        f"Error in Phase Two: {str(e)}"
                    )
                except Exception as coord_error:
                    logger.error(f"Failed to report error to coordinator: {str(coord_error)}")
            
            logger.error(f"Error in Phase Two: {str(e)}", exc_info=True)
            self._is_processing = False
            return {
                "status": "error",
                "error": str(e),
                "operation_id": operation_id
            }
            
    async def _use_internal_implementation(self, input_data: Dict[str, Any]) -> bool:
        """Determine whether to use internal implementation or coordinator."""
        # Check coordinator health
        try:
            health = await self._phase_coordination.get_phase_health()
            if health.get("status") != "HEALTHY":
                logger.warning(f"Phase coordinator not healthy: {health.get('description')}")
                return True
        except Exception as e:
            logger.warning(f"Error checking coordination health: {str(e)}")
            return True
            
        # Check if this is a compatibility mode request
        if input_data.get("use_legacy_implementation", False):
            return True
            
        # Otherwise, use coordinator by default for now
        # In a full implementation, we would gradually migrate to the coordinator
        # For now, still use the internal implementation for compatibility
        return True
    
    def _sort_components_by_dependencies(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort components from most fundamental (least dependencies) to least fundamental."""
        # Create a mapping of component IDs to components and dependency counts
        component_map = {}
        dependency_count = {}
        
        for comp in components:
            comp_id = comp.get("id", f"comp_{int(time.time())}")
            dependencies = comp.get("dependencies", [])
            component_map[comp_id] = comp
            dependency_count[comp_id] = len(dependencies)
        
        # Sort components by dependency count (ascending)
        sorted_ids = sorted(dependency_count.keys(), key=lambda x: dependency_count[x])
        sorted_components = [component_map[comp_id] for comp_id in sorted_ids]
        
        return sorted_components
            
    async def _develop_component(self, component_id: str) -> Dict[str, Any]:
        """Develop a component through the complete lifecycle."""
        # Get development context
        context = self._development_contexts.get(component_id)
        if not context:
            logger.error(f"Development context not found for component {component_id}")
            return {"error": f"Development context not found for component {component_id}"}
        
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
                if not self._use_internal_implementation({"feature_count": len(features)}):
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
                if hasattr(feature_result, "get_cultivation_status"):
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
            test_execution = await self._run_component_tests(component_obj, context)
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
                    dep_context = self._development_contexts.get(dep_id)
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
                integration_execution = await self._run_integration_tests(
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
        context = self._development_contexts.get(component_id)
        if not context:
            return
            
        await self._state_manager.set_state(
            f"component:development:{component_id}",
            {
                "component_id": component_id,
                "component_name": context.component_name,
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
                "component_name": context.component_name,
                "state": state.name
            }
        )
    
    async def _run_component_tests(self, component: Component, context: ComponentDevelopmentContext) -> Dict[str, Any]:
        """Run tests for a component (simulated)."""
        logger.info(f"Running tests for {context.component_name}")
        
        test_results = {
            "total_tests": len(context.tests),
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "test_details": []
        }
        
        # Create a test execution in the component
        execution_id = f"test_run_{context.component_id}_{int(time.time())}"
        component.create_test_execution(execution_id, "component_test")
        
        # Simulate running each test
        import random
        for test in context.tests:
            # High pass rate for simplicity
            passed = random.random() < 0.95
            
            result = {
                "test_id": test.get("id"),
                "test_name": test.get("name"),
                "passed": passed,
                "duration": random.uniform(0.01, 0.5),
                "output": "Test passed" if passed else "Test failed"
            }
            
            if passed:
                test_results["passed_tests"] += 1
            else:
                test_results["failed_tests"] += 1
                
            test_results["test_details"].append(result)
        
        # Update component test state
        component.update_test_state(
            execution_id, 
            "PASSED" if test_results["failed_tests"] == 0 else "FAILED",
            test_results
        )
        
        test_results["status"] = "passed" if test_results["failed_tests"] == 0 else "failed"
        return test_results
    
    async def _run_integration_tests(self, component: Component, integration_tests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run integration tests (simulated)."""
        logger.info(f"Running integration tests for {component.interface_id}")
        
        test_results = {
            "total_tests": len(integration_tests),
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": []
        }
        
        # Create a test execution in the component
        execution_id = f"integration_test_run_{component.interface_id}_{int(time.time())}"
        component.create_test_execution(execution_id, "integration_test")
        
        # Simulate running each test
        import random
        for test in integration_tests:
            # High pass rate for simplicity
            passed = random.random() < 0.95
            
            result = {
                "test_id": test.get("id"),
                "test_name": test.get("name"),
                "passed": passed,
                "duration": random.uniform(0.05, 1.0),
                "output": "Test passed" if passed else "Test failed"
            }
            
            if passed:
                test_results["passed_tests"] += 1
            else:
                test_results["failed_tests"] += 1
                
            test_results["test_details"].append(result)
        
        # Update component test state
        component.update_test_state(
            execution_id, 
            "PASSED" if test_results["failed_tests"] == 0 else "FAILED",
            test_results
        )
        
        test_results["status"] = "passed" if test_results["failed_tests"] == 0 else "failed"
        return test_results
    
    async def _run_system_tests(self, system_test_result: Dict[str, Any]) -> Dict[str, Any]:
        """Run system tests (simulated)."""
        logger.info("Running system tests")
        
        system_tests = system_test_result.get("system_tests", [])
        test_results = {
            "total_tests": len(system_tests),
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": []
        }
        
        # Simulate running each test
        import random
        for test in system_tests:
            # High pass rate for simplicity
            passed = random.random() < 0.95
            
            result = {
                "test_id": test.get("id"),
                "test_name": test.get("name"),
                "passed": passed,
                "duration": random.uniform(0.1, 2.0),
                "output": "Test passed" if passed else "Test failed"
            }
            
            if passed:
                test_results["passed_tests"] += 1
            else:
                test_results["failed_tests"] += 1
                
            test_results["test_details"].append(result)
        
        test_results["status"] = "passed" if test_results["failed_tests"] == 0 else "failed"
        test_results["coverage"] = system_test_result.get("coverage_analysis", {})
        
        # Record metric
        await self._metrics_manager.record_metric(
            "system_tests:execution",
            1.0,
            metadata={
                "total_tests": test_results["total_tests"],
                "passed_tests": test_results["passed_tests"],
                "failed_tests": test_results["failed_tests"],
                "status": test_results["status"]
            }
        )
        
        return test_results
    
    async def _run_deployment_tests(self, deployment_test_result: Dict[str, Any]) -> Dict[str, Any]:
        """Run deployment tests (simulated)."""
        logger.info("Running deployment tests")
        
        deployment_tests = deployment_test_result.get("deployment_tests", [])
        test_results = {
            "total_tests": len(deployment_tests),
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": []
        }
        
        # Simulate running each test
        import random
        for test in deployment_tests:
            # High pass rate for simplicity
            passed = random.random() < 0.95
            
            result = {
                "test_id": test.get("id"),
                "test_name": test.get("name"),
                "passed": passed,
                "duration": random.uniform(0.1, 1.5),
                "output": "Test passed" if passed else "Test failed"
            }
            
            if passed:
                test_results["passed_tests"] += 1
            else:
                test_results["failed_tests"] += 1
                
            test_results["test_details"].append(result)
        
        test_results["status"] = "passed" if test_results["failed_tests"] == 0 else "failed"
        test_results["deployment_checks"] = deployment_test_result.get("deployment_checks", [])
        
        # Record metric
        await self._metrics_manager.record_metric(
            "deployment_tests:execution",
            1.0,
            metadata={
                "total_tests": test_results["total_tests"],
                "passed_tests": test_results["passed_tests"],
                "failed_tests": test_results["failed_tests"],
                "status": test_results["status"]
            }
        )
        
        return test_results
    
    async def get_component_status(self, component_id: str) -> Dict[str, Any]:
        """Get the status of a component."""
        context = self._development_contexts.get(component_id)
        if not context:
            # Try to get from state manager
            state = await self._state_manager.get_state(f"component:development:{component_id}")
            if not state:
                return {"error": f"Component {component_id} not found"}
            return state
        
        # Build status from context
        return {
            "component_id": component_id,
            "component_name": context.component_name,
            "description": context.description,
            "state": context.state.name,
            "dependencies": list(context.dependencies),
            "features": context.features,
            "has_tests": len(context.tests) > 0,
            "has_implementation": bool(context.implementation),
            "iterations": len(context.iteration_history),
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_development_progress(self) -> Dict[str, Any]:
        """Get overall progress of the development process."""
        total_components = len(self._development_contexts)
        if total_components == 0:
            return {
                "status": "no_components",
                "message": "No components are being developed"
            }
        
        # Count components in each state
        state_counts = {state.name: 0 for state in ComponentDevelopmentState}
        for context in self._development_contexts.values():
            state_counts[context.state.name] += 1
        
        # Calculate completion percentage
        completed = state_counts[ComponentDevelopmentState.COMPLETED.name]
        completion_percentage = (completed / total_components) * 100 if total_components > 0 else 0
        
        return {
            "total_components": total_components,
            "completed_components": completed,
            "completion_percentage": completion_percentage,
            "state_counts": state_counts,
            "is_processing": self._is_processing,
            "timestamp": datetime.now().isoformat()
        }