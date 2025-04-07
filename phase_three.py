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
    SystemMonitor
)
from resources.monitoring import CircuitBreaker, CircuitOpenError, HealthStatus
from interface import AgentInterface, ValidationManager, AgentState
from feature import Feature, FeatureState
from phase_four import PhaseFourInterface
from phase_zero import BaseAnalysisAgent

logger = logging.getLogger(__name__)

class FeatureDevelopmentState(Enum):
    """States for feature development process"""
    PLANNING = auto()      # Initial planning phase
    ELABORATION = auto()   # Requirement elaboration
    TEST_CREATION = auto() # Creating tests for the feature
    IMPLEMENTATION = auto() # Implementing the feature
    TESTING = auto()       # Running tests
    INTEGRATION = auto()   # Integrating with other features
    COMPLETED = auto()     # Feature development complete
    FAILED = auto()        # Feature development failed

class FeaturePerformanceMetrics(Enum):
    """Metrics for evaluating feature performance"""
    CODE_QUALITY = auto()    # Static code quality 
    TEST_COVERAGE = auto()   # Test coverage percentage
    BUILD_STABILITY = auto() # Stability of builds
    MAINTAINABILITY = auto() # Code maintainability score
    RUNTIME_EFFICIENCY = auto() # Resource usage efficiency
    INTEGRATION_SCORE = auto() # Integration with other features

@dataclass
class FeaturePerformanceScore:
    """Performance score for a feature"""
    feature_id: str
    scores: Dict[FeaturePerformanceMetrics, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def get_overall_score(self) -> float:
        """Get the overall performance score"""
        if not self.scores:
            return 0.0
        return sum(self.scores.values()) / len(self.scores)

@dataclass
class FeatureDevelopmentContext:
    """Context for feature development process"""
    feature_id: str
    feature_name: str
    requirements: Dict[str, Any]
    dependencies: Set[str] = field(default_factory=set)
    state: FeatureDevelopmentState = FeatureDevelopmentState.PLANNING
    tests: List[Dict[str, Any]] = field(default_factory=list)
    implementation: Optional[str] = None
    performance_scores: List[FeaturePerformanceScore] = field(default_factory=list)
    iteration_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def record_iteration(self, state: FeatureDevelopmentState, 
                         details: Dict[str, Any], 
                         performance_score: Optional[FeaturePerformanceScore] = None) -> None:
        """Record an iteration in the feature development process"""
        self.state = state
        self.iteration_history.append({
            "state": state.name,
            "timestamp": datetime.now().isoformat(),
            "details": details
        })
        if performance_score:
            self.performance_scores.append(performance_score)

class FeatureElaborationAgent(AgentInterface):
    """Agent responsible for elaborating feature requirements"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "feature_elaboration_agent", 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler,
            memory_monitor
        )
        self._validation_manager = ValidationManager(event_queue, state_manager, context_manager)
        
    async def elaborate_feature(self, 
                              feature_metadata: Dict[str, Any],
                              operation_id: str) -> Dict[str, Any]:
        """Elaborate feature requirements from initial metadata."""
        try:
            logger.info(f"Starting feature elaboration for {feature_metadata.get('name', 'unknown')}")
            
            # Set agent state to processing
            await self.set_agent_state(AgentState.PROCESSING)
            
            # Prepare feature metadata for the prompt
            metadata_str = json.dumps(feature_metadata)
            
            # Create schema for validation
            schema = {
                "type": "object",
                "required": ["feature_id", "name", "description", "requirements", "dependencies", "test_scenarios"],
                "properties": {
                    "feature_id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "requirements": {
                        "type": "object",
                        "properties": {
                            "functional": {"type": "array", "items": {"type": "string"}},
                            "non_functional": {"type": "array", "items": {"type": "string"}}
                        }
                    },
                    "dependencies": {"type": "array", "items": {"type": "string"}},
                    "test_scenarios": {"type": "array", "items": {"type": "string"}}
                }
            }
            
            # Generate system prompt for elaboration
            system_prompt = """You are an expert software requirements engineer.
Elaborate the provided feature metadata into a comprehensive set of requirements.
Focus on creating:
1. Clear functional requirements that specify what the feature should do
2. Non-functional requirements addressing performance, scalability, etc.
3. Dependencies on other features or components
4. Test scenarios to verify the feature works correctly

Return your response as a JSON object with these fields:
- feature_id: A unique identifier for the feature
- name: The feature name
- description: A detailed description of the feature
- requirements: An object with 'functional' and 'non_functional' arrays
- dependencies: An array of dependency identifiers
- test_scenarios: An array of test scenarios for the feature
"""
            
            # Call LLM to elaborate requirements
            response = await self.process_with_validation(
                conversation=metadata_str,
                system_prompt_info=(system_prompt,),
                schema=schema,
                current_phase="feature_elaboration",
                operation_id=operation_id,
                metadata={"feature_name": feature_metadata.get("name", "unknown")}
            )
            
            # Update state to complete
            await self.set_agent_state(AgentState.COMPLETE)
            
            # Add operation ID to the response
            response["operation_id"] = operation_id
            
            logger.info(f"Feature elaboration completed for {response.get('name', 'unknown')}")
            return response
            
        except Exception as e:
            logger.error(f"Error elaborating feature: {str(e)}", exc_info=True)
            await self.set_agent_state(AgentState.ERROR)
            
            return {
                "error": f"Feature elaboration failed: {str(e)}",
                "feature_name": feature_metadata.get("name", "unknown"),
                "operation_id": operation_id
            }

class FeatureTestSpecAgent(AgentInterface):
    """Agent responsible for creating feature test specifications"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "feature_test_spec_agent", 
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
                                       feature_requirements: Dict[str, Any],
                                       operation_id: str) -> Dict[str, Any]:
        """Create test specifications for a feature based on requirements."""
        try:
            logger.info(f"Creating test specifications for feature {feature_requirements.get('name', 'unknown')}")
            
            # Set agent state to processing
            await self.set_agent_state(AgentState.PROCESSING)
            
            # Prepare requirements for the prompt
            requirements_str = json.dumps(feature_requirements)
            
            # Get feature name and id
            feature_name = feature_requirements.get("name", "unnamed_feature")
            feature_id = feature_requirements.get("feature_id", f"feature_{operation_id}")
            
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
Create comprehensive test specifications for the provided feature requirements.
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
                metadata={"feature_name": feature_name, "feature_id": feature_id}
            )
            
            # Update state to complete
            await self.set_agent_state(AgentState.COMPLETE)
            
            # Add feature metadata to the response
            response.update({
                "feature_name": feature_name,
                "feature_id": feature_id,
                "operation_id": operation_id
            })
            
            logger.info(f"Test specification creation completed for {feature_name}")
            return response
            
        except Exception as e:
            logger.error(f"Error creating test specifications: {str(e)}", exc_info=True)
            await self.set_agent_state(AgentState.ERROR)
            
            return {
                "error": f"Test specification creation failed: {str(e)}",
                "feature_name": feature_requirements.get("name", "unnamed_feature"),
                "feature_id": feature_requirements.get("feature_id", f"feature_{operation_id}"),
                "operation_id": operation_id
            }

class FeatureIntegrationAgent(AgentInterface):
    """Agent responsible for integrating features with dependencies"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "feature_integration_agent", 
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
                                    feature_implementation: Dict[str, Any],
                                    dependencies: List[Dict[str, Any]],
                                    operation_id: str) -> Dict[str, Any]:
        """Create integration tests between a feature and its dependencies."""
        try:
            logger.info(f"Creating integration tests for {feature_implementation.get('feature_name', 'unknown')}")
            
            # Set agent state to processing
            await self.set_agent_state(AgentState.PROCESSING)
            
            # Prepare input data for the prompt
            integration_data = {
                "feature": feature_implementation,
                "dependencies": dependencies
            }
            integration_str = json.dumps(integration_data)
            
            # Get feature name and id
            feature_name = feature_implementation.get("feature_name", "unnamed_feature")
            feature_id = feature_implementation.get("feature_id", f"feature_{operation_id}")
            
            # Create schema for validation
            schema = {
                "type": "object",
                "required": ["integration_tests", "integration_score"],
                "properties": {
                    "integration_tests": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["id", "name", "description", "test_code", "features_tested"],
                            "properties": {
                                "id": {"type": "string"},
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "test_code": {"type": "string"},
                                "features_tested": {"type": "array", "items": {"type": "string"}}
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
Analyze the feature implementation and its dependencies to create comprehensive integration tests.
Focus on:
1. Testing the interactions between the feature and its dependencies
2. Identifying potential integration issues
3. Ensuring all communication paths are tested
4. Validating data flows between components

Return your response as a JSON object with these fields:
- integration_tests: An array of test case objects, each with:
  - id: A unique identifier for the test
  - name: The test name
  - description: What the integration test verifies
  - test_code: Python code implementing the integration test
  - features_tested: Array of feature IDs being tested together
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
                metadata={"feature_name": feature_name, "feature_id": feature_id}
            )
            
            # Update state to complete
            await self.set_agent_state(AgentState.COMPLETE)
            
            # Add feature metadata to the response
            response.update({
                "feature_name": feature_name,
                "feature_id": feature_id,
                "operation_id": operation_id
            })
            
            logger.info(f"Integration test creation completed for {feature_name}")
            return response
            
        except Exception as e:
            logger.error(f"Error creating integration tests: {str(e)}", exc_info=True)
            await self.set_agent_state(AgentState.ERROR)
            
            return {
                "error": f"Integration test creation failed: {str(e)}",
                "feature_name": feature_implementation.get("feature_name", "unnamed_feature"),
                "feature_id": feature_implementation.get("feature_id", f"feature_{operation_id}"),
                "operation_id": operation_id
            }

class FeaturePerformanceAgent(AgentInterface):
    """Agent responsible for evaluating feature performance"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "feature_performance_agent", 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler,
            memory_monitor
        )
        self._validation_manager = ValidationManager(event_queue, state_manager, context_manager)
        
    async def evaluate_performance(self,
                                feature_implementation: Dict[str, Any],
                                test_results: Dict[str, Any],
                                operation_id: str) -> Dict[str, Any]:
        """Evaluate the performance of a feature."""
        try:
            logger.info(f"Evaluating performance for {feature_implementation.get('feature_name', 'unknown')}")
            
            # Set agent state to processing
            await self.set_agent_state(AgentState.PROCESSING)
            
            # Prepare input data for the prompt
            performance_data = {
                "feature": feature_implementation,
                "test_results": test_results
            }
            performance_str = json.dumps(performance_data)
            
            # Get feature name and id
            feature_name = feature_implementation.get("feature_name", "unnamed_feature")
            feature_id = feature_implementation.get("feature_id", f"feature_{operation_id}")
            
            # Create schema for validation
            schema = {
                "type": "object",
                "required": ["performance_metrics", "overall_score", "improvement_suggestions"],
                "properties": {
                    "performance_metrics": {
                        "type": "object",
                        "required": ["code_quality", "test_coverage", "build_stability", "maintainability", "runtime_efficiency", "integration_score"],
                        "properties": {
                            "code_quality": {"type": "number"},
                            "test_coverage": {"type": "number"},
                            "build_stability": {"type": "number"},
                            "maintainability": {"type": "number"},
                            "runtime_efficiency": {"type": "number"},
                            "integration_score": {"type": "number"}
                        }
                    },
                    "overall_score": {"type": "number"},
                    "improvement_suggestions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["area", "description", "priority"],
                            "properties": {
                                "area": {"type": "string"},
                                "description": {"type": "string"},
                                "priority": {"type": "string"}
                            }
                        }
                    }
                }
            }
            
            # Generate system prompt for performance evaluation
            system_prompt = """You are an expert software quality analyst.
Evaluate the performance of the feature implementation based on test results and code quality.
Focus on:
1. Code quality (structure, patterns, readability)
2. Test coverage (comprehensiveness, edge cases)
3. Build stability (reliability of builds)
4. Maintainability (ease of future modifications)
5. Runtime efficiency (resource usage, speed)
6. Integration quality (how well it works with dependencies)

Return your response as a JSON object with these fields:
- performance_metrics: An object with scores from 0-100 for:
  - code_quality: Code structure and readability
  - test_coverage: Completeness of test coverage
  - build_stability: Reliability of build process
  - maintainability: Ease of future maintenance
  - runtime_efficiency: Resource usage efficiency
  - integration_score: Quality of integration with dependencies
- overall_score: A weighted average of all metrics (0-100)
- improvement_suggestions: An array of suggested improvements, each with:
  - area: The area to improve
  - description: Detailed description of the improvement
  - priority: "low", "medium", or "high"
"""
            
            # Call LLM to evaluate performance
            response = await self.process_with_validation(
                conversation=performance_str,
                system_prompt_info=(system_prompt,),
                schema=schema,
                current_phase="performance_evaluation",
                operation_id=operation_id,
                metadata={"feature_name": feature_name, "feature_id": feature_id}
            )
            
            # Update state to complete
            await self.set_agent_state(AgentState.COMPLETE)
            
            # Add feature metadata to the response
            response.update({
                "feature_name": feature_name,
                "feature_id": feature_id,
                "operation_id": operation_id
            })
            
            logger.info(f"Performance evaluation completed for {feature_name}")
            return response
            
        except Exception as e:
            logger.error(f"Error evaluating performance: {str(e)}", exc_info=True)
            await self.set_agent_state(AgentState.ERROR)
            
            return {
                "error": f"Performance evaluation failed: {str(e)}",
                "feature_name": feature_implementation.get("feature_name", "unnamed_feature"),
                "feature_id": feature_implementation.get("feature_id", f"feature_{operation_id}"),
                "operation_id": operation_id
            }

# Phase Zero feedback agents for feature evolution
class FeatureRequirementsAnalysisAgent(BaseAnalysisAgent):
    """Phase Zero agent for analyzing feature requirements quality"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "feature_requirements_analysis", 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler,
            health_tracker,
            memory_monitor
        )
        
    def get_output_schema(self) -> Dict:
        return {
            "requirements_analysis": {
                "completion_gaps": List[Dict],
                "consistency_issues": List[Dict],
                "testability_concerns": List[Dict],
                "enhancement_suggestions": List[Dict]
            }
        }

class FeatureImplementationAnalysisAgent(BaseAnalysisAgent):
    """Phase Zero agent for analyzing feature implementation quality"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "feature_implementation_analysis", 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler,
            health_tracker,
            memory_monitor
        )
        
    def get_output_schema(self) -> Dict:
        return {
            "implementation_analysis": {
                "code_structure_issues": List[Dict],
                "architectural_concerns": List[Dict],
                "optimization_opportunities": List[Dict],
                "quality_metrics": Dict[str, float]
            }
        }

class FeatureEvolutionAgent(BaseAnalysisAgent):
    """Phase Zero agent for synthesizing feature evolution opportunities"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 health_tracker: Optional[HealthTracker] = None,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "feature_evolution", 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler,
            health_tracker,
            memory_monitor
        )
        
    def get_output_schema(self) -> Dict:
        return {
            "evolution_opportunities": {
                "feature_combinations": List[Dict],
                "reuse_patterns": List[Dict],
                "refactoring_suggestions": List[Dict],
                "emerging_abstractions": List[Dict]
            }
        }

class NaturalSelectionAgent(AgentInterface):
    """Refinement agent responsible for feature optimization decisions"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "natural_selection_agent", 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler,
            memory_monitor
        )
        self._validation_manager = ValidationManager(event_queue, state_manager, context_manager)
        
        # Initialize Phase Zero feedback agents
        self._requirements_analysis_agent = FeatureRequirementsAnalysisAgent(
            event_queue, state_manager, context_manager, 
            cache_manager, metrics_manager, error_handler
        )
        self._implementation_analysis_agent = FeatureImplementationAnalysisAgent(
            event_queue, state_manager, context_manager, 
            cache_manager, metrics_manager, error_handler
        )
        self._evolution_agent = FeatureEvolutionAgent(
            event_queue, state_manager, context_manager, 
            cache_manager, metrics_manager, error_handler
        )
        
    async def evaluate_features(self,
                              feature_performances: List[Dict[str, Any]],
                              operation_id: str) -> Dict[str, Any]:
        """Evaluate multiple features and make optimization decisions based on phase zero feedback."""
        try:
            logger.info(f"Evaluating {len(feature_performances)} features for optimization")
            
            # Set agent state to processing
            await self.set_agent_state(AgentState.PROCESSING)
            
            # First gather Phase Zero feedback
            logger.info("Gathering Phase Zero feedback for feature optimization")
            
            # 1. Requirements analysis
            requirements_feedback = await self._requirements_analysis_agent.process_with_validation(
                json.dumps({"features": feature_performances}),
                {"type": "requirements_analysis"},
                current_phase="phase_zero_requirements_analysis",
                operation_id=f"{operation_id}_req_analysis"
            )
            
            # 2. Implementation analysis
            implementation_feedback = await self._implementation_analysis_agent.process_with_validation(
                json.dumps({"features": feature_performances}),
                {"type": "implementation_analysis"},
                current_phase="phase_zero_implementation_analysis",
                operation_id=f"{operation_id}_impl_analysis"
            )
            
            # 3. Evolution opportunities
            evolution_feedback = await self._evolution_agent.process_with_validation(
                json.dumps({
                    "features": feature_performances,
                    "requirements_analysis": requirements_feedback,
                    "implementation_analysis": implementation_feedback
                }),
                {"type": "evolution_opportunities"},
                current_phase="phase_zero_evolution_analysis",
                operation_id=f"{operation_id}_evol_analysis"
            )
            
            # Combine all feedback for natural selection decisions
            feedback_data = {
                "features": feature_performances,
                "phase_zero_feedback": {
                    "requirements_analysis": requirements_feedback,
                    "implementation_analysis": implementation_feedback,
                    "evolution_opportunities": evolution_feedback
                }
            }
            
            # Create schema for validation of final decision
            schema = {
                "type": "object",
                "required": ["feature_rankings", "optimization_decisions", "evolution_strategy"],
                "properties": {
                    "feature_rankings": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["feature_id", "feature_name", "rank", "overall_score"],
                            "properties": {
                                "feature_id": {"type": "string"},
                                "feature_name": {"type": "string"},
                                "rank": {"type": "integer"},
                                "overall_score": {"type": "number"},
                                "strengths": {"type": "array", "items": {"type": "string"}},
                                "weaknesses": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    },
                    "optimization_decisions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["feature_id", "decision", "rationale"],
                            "properties": {
                                "feature_id": {"type": "string"},
                                "decision": {"type": "string"},
                                "rationale": {"type": "string"}
                            }
                        }
                    },
                    "evolution_strategy": {
                        "type": "object",
                        "required": ["reuse_opportunities", "refactor_suggestions", "feature_combinations"],
                        "properties": {
                            "reuse_opportunities": {"type": "array", "items": {"type": "object"}},
                            "refactor_suggestions": {"type": "array", "items": {"type": "object"}},
                            "feature_combinations": {"type": "array", "items": {"type": "object"}}
                        }
                    }
                }
            }
            
            # Generate system prompt for natural selection evaluation
            system_prompt = """You are an expert software evolution specialist serving as a refinement agent.
Based on the performance data and Phase Zero feedback, make optimization decisions using natural selection principles.
Focus on:
1. Objectively ranking features based on performance metrics and feedback
2. Identifying features that should be kept, improved, or replaced
3. Finding opportunities for code reuse between features
4. Suggesting combinations of features that would work well together
5. Recommending refactoring opportunities

Your decisions should be driven by the feedback from the specialized analysis agents, with careful consideration
of all aspects of feature quality.

Return your response as a JSON object with these fields:
- feature_rankings: An array of feature rankings, each with:
  - feature_id: The feature identifier
  - feature_name: The feature name
  - rank: Numerical ranking (1 is best)
  - overall_score: Numerical score from performance metrics
  - strengths: Array of feature strengths
  - weaknesses: Array of feature weaknesses
- optimization_decisions: An array of decisions, each with:
  - feature_id: The feature identifier
  - decision: One of "keep", "improve", "replace", "combine"
  - rationale: Explanation for the decision
- evolution_strategy: Object containing:
  - reuse_opportunities: Array of code reuse possibilities
  - refactor_suggestions: Array of refactoring suggestions
  - feature_combinations: Array of features that could be combined
"""
            
            # Call LLM to make final optimization decisions based on all feedback
            response = await self.process_with_validation(
                conversation=json.dumps(feedback_data),
                system_prompt_info=(system_prompt,),
                schema=schema,
                current_phase="natural_selection_refinement",
                operation_id=operation_id
            )
            
            # Update state to complete
            await self.set_agent_state(AgentState.COMPLETE)
            
            # Add operation ID and feedback to the response
            response["operation_id"] = operation_id
            response["phase_zero_feedback"] = {
                "requirements_analysis": requirements_feedback,
                "implementation_analysis": implementation_feedback,
                "evolution_opportunities": evolution_feedback
            }
            
            logger.info(f"Natural selection refinement completed for {len(feature_performances)} features")
            return response
            
        except Exception as e:
            logger.error(f"Error in natural selection refinement: {str(e)}", exc_info=True)
            await self.set_agent_state(AgentState.ERROR)
            
            return {
                "error": f"Natural selection refinement failed: {str(e)}",
                "operation_id": operation_id
            }

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
        """Start development of a new feature."""
        feature_id = feature_metadata.get("id", f"feature_{int(time.time())}")
        feature_name = feature_metadata.get("name", "unnamed_feature")
        
        logger.info(f"Starting development of feature {feature_name} ({feature_id})")
        
        # Record development start
        await self._metrics_manager.record_metric(
            "feature:development:start",
            1.0,
            metadata={
                "feature_id": feature_id,
                "feature_name": feature_name
            }
        )
        
        # Create feature development context
        context = FeatureDevelopmentContext(
            feature_id=feature_id,
            feature_name=feature_name,
            requirements=feature_metadata
        )
        self._development_contexts[feature_id] = context
        
        # Store context in state manager
        await self._state_manager.set_state(
            f"feature:development:{feature_id}",
            {
                "feature_id": feature_id,
                "feature_name": feature_name,
                "state": context.state.name,
                "timestamp": datetime.now().isoformat()
            },
            ResourceType.STATE
        )
        
        # Start development task
        task = asyncio.create_task(self._develop_feature(feature_id))
        self._active_tasks[feature_id] = task
        
        # Add task cleanup callback
        task.add_done_callback(lambda t: self._handle_task_completion(feature_id, t))
        
        return feature_id
    
    def _handle_task_completion(self, feature_id: str, task: asyncio.Task) -> None:
        """Handle the completion of a feature development task."""
        # Remove from active tasks
        self._active_tasks.pop(feature_id, None)
        
        # Check for exceptions
        if task.exception():
            logger.error(f"Feature development for {feature_id} failed with exception: {task.exception()}")
            
            # Update context state
            if feature_id in self._development_contexts:
                self._development_contexts[feature_id].state = FeatureDevelopmentState.FAILED
                
                # Record development error
                asyncio.create_task(self._metrics_manager.record_metric(
                    "feature:development:error",
                    1.0,
                    metadata={
                        "feature_id": feature_id,
                        "feature_name": self._development_contexts[feature_id].feature_name,
                        "error": str(task.exception())
                    }
                ))
    
    async def _develop_feature(self, feature_id: str) -> None:
        """Develop a feature through the complete lifecycle."""
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
                await self._update_development_state(feature_id, context.state)
                
                elaboration_result = await self._elaboration_agent.elaborate_feature(
                    context.requirements,
                    f"elaborate_{feature_id}"
                )
                
                if "error" in elaboration_result:
                    logger.error(f"Feature elaboration failed for {feature_id}: {elaboration_result['error']}")
                    context.state = FeatureDevelopmentState.FAILED
                    await self._update_development_state(feature_id, context.state)
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
                await self._update_development_state(feature_id, context.state)
                
                test_spec_result = await self._test_spec_agent.create_test_specifications(
                    context.requirements,
                    f"test_spec_{feature_id}"
                )
                
                if "error" in test_spec_result:
                    logger.error(f"Test specification creation failed for {feature_id}: {test_spec_result['error']}")
                    context.state = FeatureDevelopmentState.FAILED
                    await self._update_development_state(feature_id, context.state)
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
                await self._update_development_state(feature_id, context.state)
                
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
                    await self._update_development_state(feature_id, context.state)
                    return
                
                # Update context with implementation
                context.implementation = implementation_result.get("code", "")
                context.record_iteration(
                    FeatureDevelopmentState.IMPLEMENTATION,
                    {"implementation_result": implementation_result}
                )
                
                # 4. Testing
                context.state = FeatureDevelopmentState.TESTING
                await self._update_development_state(feature_id, context.state)
                
                # Create Feature object for tracking
                feature_obj = Feature(feature_id, context.feature_name)
                feature_obj.component_state = FeatureState.TESTING
                
                # Run tests (simulated here)
                test_execution = await self._run_tests(feature_obj, context)
                context.record_iteration(
                    FeatureDevelopmentState.TESTING,
                    {"test_execution": test_execution}
                )
                
                # 5. Integration (if dependencies exist)
                if context.dependencies:
                    context.state = FeatureDevelopmentState.INTEGRATION
                    await self._update_development_state(feature_id, context.state)
                    
                    # Get dependency implementations
                    dependency_implementations = await self._get_dependency_implementations(context.dependencies)
                    
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
                        "integration_results": context.iteration_history[-1]["details"].get("integration_result", {})
                    },
                    f"performance_{feature_id}"
                )
                
                # Create performance score object
                performance_score = FeaturePerformanceScore(feature_id=feature_id)
                performance_metrics = performance_result.get("performance_metrics", {})
                performance_score.scores = {
                    FeaturePerformanceMetrics.CODE_QUALITY: performance_metrics.get("code_quality", 0),
                    FeaturePerformanceMetrics.TEST_COVERAGE: performance_metrics.get("test_coverage", 0),
                    FeaturePerformanceMetrics.BUILD_STABILITY: performance_metrics.get("build_stability", 0),
                    FeaturePerformanceMetrics.MAINTAINABILITY: performance_metrics.get("maintainability", 0),
                    FeaturePerformanceMetrics.RUNTIME_EFFICIENCY: performance_metrics.get("runtime_efficiency", 0),
                    FeaturePerformanceMetrics.INTEGRATION_SCORE: performance_metrics.get("integration_score", 0)
                }
                
                # Update context with performance score
                context.record_iteration(
                    FeatureDevelopmentState.COMPLETED,
                    {"performance_result": performance_result},
                    performance_score
                )
                
                # 7. Complete development
                context.state = FeatureDevelopmentState.COMPLETED
                await self._update_development_state(feature_id, context.state)
                
                # Record development completion
                await self._metrics_manager.record_metric(
                    "feature:development:complete",
                    1.0,
                    metadata={
                        "feature_id": feature_id,
                        "feature_name": context.feature_name,
                        "overall_score": performance_result.get("overall_score", 0)
                    }
                )
                
                logger.info(f"Feature development completed for {context.feature_name}")
                
        except Exception as e:
            logger.error(f"Error in feature development process for {feature_id}: {str(e)}", exc_info=True)
            context.state = FeatureDevelopmentState.FAILED
            await self._update_development_state(feature_id, context.state)
            
            # Record development error
            await self._metrics_manager.record_metric(
                "feature:development:error",
                1.0,
                metadata={
                    "feature_id": feature_id,
                    "feature_name": context.feature_name,
                    "error": str(e)
                }
            )
    
    async def _run_tests(self, feature: Feature, context: FeatureDevelopmentContext) -> Dict[str, Any]:
        """Run tests for a feature (simulated)."""
        logger.info(f"Running tests for {context.feature_name}")
        
        test_results = {
            "total_tests": len(context.tests),
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "test_details": []
        }
        
        # Create a test execution in the feature
        execution_id = f"test_run_{context.feature_id}_{int(time.time())}"
        feature.create_test_execution(execution_id, "unit_test")
        
        # Simulate running each test
        for test in context.tests:
            # Simulate 90% pass rate
            passed = random.random() < 0.9
            
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
        
        # Update feature test state
        feature.update_test_state(
            execution_id, 
            "PASSED" if test_results["failed_tests"] == 0 else "FAILED",
            test_results
        )
        
        return test_results
    
    async def _get_dependency_implementations(self, dependencies: Set[str]) -> List[Dict[str, Any]]:
        """Get implementations of dependencies."""
        dependency_implementations = []
        
        for dep_id in dependencies:
            # Check if dependency exists in development contexts
            if dep_id in self._development_contexts:
                context = self._development_contexts[dep_id]
                if context.implementation:
                    dependency_implementations.append({
                        "feature_id": dep_id,
                        "feature_name": context.feature_name,
                        "implementation": context.implementation
                    })
            else:
                # Check if dependency exists in state manager
                dep_state = await self._state_manager.get_state(f"feature:implementation:{dep_id}")
                if dep_state:
                    dependency_implementations.append(dep_state)
        
        return dependency_implementations
    
    async def _update_development_state(self, feature_id: str, state: FeatureDevelopmentState) -> None:
        """Update development state in state manager."""
        context = self._development_contexts.get(feature_id)
        if not context:
            return
            
        await self._state_manager.set_state(
            f"feature:development:{feature_id}",
            {
                "feature_id": feature_id,
                "feature_name": context.feature_name,
                "state": state.name,
                "timestamp": datetime.now().isoformat()
            },
            ResourceType.STATE
        )
        
        # Record state change metric
        await self._metrics_manager.record_metric(
            "feature:development:state_change",
            1.0,
            metadata={
                "feature_id": feature_id,
                "feature_name": context.feature_name,
                "state": state.name
            }
        )
    
    async def get_feature_status(self, feature_id: str) -> Dict[str, Any]:
        """Get the current status of a feature."""
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
        """Get statuses of all features."""
        statuses = {}
        
        for feature_id in self._development_contexts:
            statuses[feature_id] = await self.get_feature_status(feature_id)
            
        return statuses

class PhaseThreeInterface:
    """Interface for Phase Three operations"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None,
                 system_monitor: Optional[SystemMonitor] = None):
        """Initialize the Phase Three interface."""
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._context_manager = context_manager
        self._cache_manager = cache_manager
        self._metrics_manager = metrics_manager
        self._error_handler = error_handler
        self._memory_monitor = memory_monitor
        self._system_monitor = system_monitor
        
        # Initialize phase four interface
        self._phase_four_interface = PhaseFourInterface(
            event_queue, state_manager, context_manager, cache_manager,
            metrics_manager, error_handler, memory_monitor, system_monitor
        )
        
        # Initialize parallel feature development
        self._feature_development = ParallelFeatureDevelopment(
            event_queue, state_manager, context_manager, cache_manager,
            metrics_manager, error_handler, self._phase_four_interface, memory_monitor
        )
        
        # Initialize natural selection agent
        self._natural_selection_agent = NaturalSelectionAgent(
            event_queue, state_manager, context_manager, cache_manager,
            metrics_manager, error_handler, memory_monitor
        )
        
        # Track growth intervals
        self._last_evaluation_time = time.time()
        self._evaluation_interval = 3600  # 1 hour between evaluations
        
        logger.info("Phase Three interface initialized")
    
    async def start_feature_cultivation(self, component_features: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Start feature cultivation for a component."""
        try:
            logger.info(f"Starting feature cultivation for {len(component_features)} features")
            
            # Record cultivation start
            operation_id = f"cultivation_{int(time.time())}"
            await self._metrics_manager.record_metric(
                "phase_three:cultivation:start",
                1.0,
                metadata={
                    "feature_count": len(component_features),
                    "operation_id": operation_id
                }
            )
            
            # Identify independent features for parallel development
            dependency_map = {}
            for feature in component_features:
                feature_id = feature.get("id", f"feature_{int(time.time())}_{len(dependency_map)}")
                dependencies = feature.get("dependencies", [])
                
                # Ensure feature ID is in the feature
                if "id" not in feature:
                    feature["id"] = feature_id
                    
                dependency_map[feature_id] = dependencies
            
            # Start development of non-dependent features first
            started_features = []
            for feature in component_features:
                feature_id = feature.get("id")
                dependencies = dependency_map.get(feature_id, [])
                
                # Check if dependencies have already been started
                if not dependencies or all(dep in started_features for dep in dependencies):
                    # Start feature development
                    await self._feature_development.start_feature_development(feature)
                    started_features.append(feature_id)
            
            # Store cultivation state
            cultivation_state = {
                "operation_id": operation_id,
                "total_features": len(component_features),
                "started_features": started_features,
                "timestamp": datetime.now().isoformat()
            }
            await self._state_manager.set_state(
                f"phase_three:cultivation:{operation_id}",
                cultivation_state,
                ResourceType.STATE
            )
            
            return cultivation_state
            
        except Exception as e:
            logger.error(f"Error starting feature cultivation: {str(e)}", exc_info=True)
            
            await self._metrics_manager.record_metric(
                "phase_three:cultivation:error",
                1.0,
                metadata={"error": str(e)}
            )
            
            return {
                "error": f"Failed to start feature cultivation: {str(e)}"
            }
    
    async def evaluate_feature_evolution(self, component_id: str = None) -> Dict[str, Any]:
        """Evaluate feature performance and make evolution decisions."""
        try:
            # Check if it's time for evaluation
            current_time = time.time()
            if current_time - self._last_evaluation_time < self._evaluation_interval:
                logger.info("Skipping evolution evaluation - minimum interval not reached")
                return {
                    "status": "skipped",
                    "reason": "Minimum interval not reached",
                    "next_evaluation": self._last_evaluation_time + self._evaluation_interval
                }
                
            self._last_evaluation_time = current_time
            operation_id = f"evolution_{int(current_time)}"
                
            logger.info(f"Starting feature evolution evaluation for operation {operation_id}")
            
            # Record evaluation start
            await self._metrics_manager.record_metric(
                "phase_three:evolution:start",
                1.0,
                metadata={"operation_id": operation_id}
            )
            
            # Get all feature statuses
            all_statuses = await self._feature_development.get_all_feature_statuses()
            
            # Filter for completed features
            completed_features = [
                status for status in all_statuses.values() 
                if status.get("state") == FeatureDevelopmentState.COMPLETED.name
            ]
            
            if not completed_features:
                logger.info("No completed features to evaluate")
                return {
                    "operation_id": operation_id,
                    "status": "no_features",
                    "message": "No completed features to evaluate"
                }
            
            # Run natural selection evaluation
            evaluation_result = await self._natural_selection_agent.evaluate_features(
                completed_features,
                operation_id
            )
            
            if "error" in evaluation_result:
                logger.error(f"Evolution evaluation failed: {evaluation_result['error']}")
                return {
                    "operation_id": operation_id,
                    "status": "error",
                    "error": evaluation_result["error"]
                }
            
            # Store evaluation result
            await self._state_manager.set_state(
                f"phase_three:evolution:{operation_id}",
                evaluation_result,
                ResourceType.STATE
            )
            
            # Record evaluation completion
            await self._metrics_manager.record_metric(
                "phase_three:evolution:complete",
                1.0,
                metadata={
                    "operation_id": operation_id,
                    "evaluated_features": len(completed_features)
                }
            )
            
            # Apply evolution decisions
            applied_decisions = await self._apply_evolution_decisions(evaluation_result)
            
            return {
                "operation_id": operation_id,
                "status": "completed",
                "evaluation_result": evaluation_result,
                "applied_decisions": applied_decisions
            }
            
        except Exception as e:
            logger.error(f"Error in feature evolution evaluation: {str(e)}", exc_info=True)
            
            await self._metrics_manager.record_metric(
                "phase_three:evolution:error",
                1.0,
                metadata={"error": str(e)}
            )
            
            return {
                "status": "error",
                "error": f"Feature evolution evaluation failed: {str(e)}"
            }
    
    async def _apply_evolution_decisions(self, evaluation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Apply evolution decisions from natural selection."""
        decisions = evaluation_result.get("optimization_decisions", [])
        applied = {
            "total_decisions": len(decisions),
            "applied_decisions": 0,
            "actions": []
        }
        
        for decision in decisions:
            feature_id = decision.get("feature_id")
            decision_type = decision.get("decision")
            
            if not feature_id or not decision_type:
                continue
                
            # Handle different decision types
            if decision_type == "replace":
                # Implement feature replacement
                replacement_result = await self._replace_feature(
                    feature_id, 
                    decision.get("rationale", ""),
                    evaluation_result
                )
                
                applied["actions"].append({
                    "feature_id": feature_id,
                    "action": "replaced_feature",
                    "details": decision.get("rationale", ""),
                    "replacement_id": replacement_result.get("replacement_id"),
                    "replacement_method": replacement_result.get("method"),
                    "status": replacement_result.get("status")
                })
                applied["applied_decisions"] += 1
                
            elif decision_type == "improve":
                # Implement feature improvement
                improvement_result = await self._improve_feature(
                    feature_id, 
                    decision.get("rationale", ""),
                    evaluation_result
                )
                
                applied["actions"].append({
                    "feature_id": feature_id,
                    "action": "improved_feature",
                    "details": decision.get("rationale", ""),
                    "status": improvement_result.get("status"),
                    "improvements": improvement_result.get("improvements", [])
                })
                applied["applied_decisions"] += 1
                
            elif decision_type == "combine":
                # Mark for combination - implementation handled separately
                # because it requires coordinating multiple features
                applied["actions"].append({
                    "feature_id": feature_id,
                    "action": "marked_for_combination",
                    "details": decision.get("rationale", "")
                })
                applied["applied_decisions"] += 1
                
            elif decision_type == "keep":
                # No action needed
                pass
        
        # Store applied decisions in state manager
        await self._state_manager.set_state(
            f"phase_three:evolution:applied:{int(time.time())}",
            applied,
            ResourceType.STATE
        )
        
        # If there are features marked for combination, handle them now
        combination_candidates = [action for action in applied["actions"] 
                                if action["action"] == "marked_for_combination"]
        if combination_candidates:
            combination_result = await self._combine_features(
                combination_candidates,
                evaluation_result
            )
            applied["combination_results"] = combination_result
        
        return applied
    
    async def get_feature_status(self, feature_id: str) -> Dict[str, Any]:
        """Get the current status of a feature."""
        return await self._feature_development.get_feature_status(feature_id)
        
    async def _replace_feature(self, 
                            feature_id: str, 
                            rationale: str,
                            evaluation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Replace a low-performing feature with a new implementation.
        
        This method implements the actual feature replacement strategy, which can be:
        1. Conceptual replacement using feature reuse from other components
        2. Pragmatic replacement by recreating the feature from scratch
        
        Args:
            feature_id: The ID of the feature to replace
            rationale: The reason for replacement
            evaluation_data: The full evaluation data with patterns and suggestions
            
        Returns:
            Dict containing replacement results
        """
        logger.info(f"Replacing feature {feature_id} based on evolutionary selection")
        
        try:
            # Get current feature status
            feature_status = await self._feature_development.get_feature_status(feature_id)
            if not feature_status or "error" in feature_status:
                return {
                    "status": "error",
                    "error": f"Could not retrieve feature status: {feature_status.get('error', 'Unknown error')}",
                    "feature_id": feature_id
                }
            
            # Record replacement decision
            await self._metrics_manager.record_metric(
                "feature:evolution:replacement_decision",
                1.0,
                metadata={
                    "feature_id": feature_id,
                    "feature_name": feature_status.get("feature_name", "unknown"),
                    "rationale": rationale
                }
            )
            
            # Determine replacement method based on evolution data
            evolution_opportunities = evaluation_data.get("phase_zero_feedback", {}).get(
                "evolution_opportunities", {}
            )
            reuse_opportunities = evolution_opportunities.get("reuse_patterns", [])
            
            # Check if we can reuse code from another feature
            replacement_method = "recreation"  # Default method
            reuse_candidate = None
            
            for reuse in reuse_opportunities:
                if reuse.get("target_feature_id") == feature_id:
                    reuse_candidate = reuse
                    replacement_method = "reuse"
                    break
            
            # First, toggle the original feature to off (disable it)
            await self._disable_feature(feature_id)
            
            # Create replacement feature ID
            replacement_id = f"{feature_id}_v{int(time.time())}"
            
            # Prepare requirements for the new feature
            if replacement_method == "reuse":
                # Use requirements from the reuse candidate
                source_feature_id = reuse_candidate.get("source_feature_id")
                source_feature = await self._feature_development.get_feature_status(source_feature_id)
                
                if not source_feature or "error" in source_feature:
                    # Fallback to recreation if source feature not found
                    replacement_method = "recreation"
                    requirements = self._prepare_recreation_requirements(feature_status, evaluation_data)
                else:
                    # Adapt the source feature with the original feature's requirements
                    requirements = self._prepare_reuse_requirements(
                        feature_status, 
                        source_feature, 
                        reuse_candidate
                    )
            else:
                # Prepare requirements for recreation
                requirements = self._prepare_recreation_requirements(feature_status, evaluation_data)
            
            # Start development of the replacement feature
            replacement_result = await self._feature_development.start_feature_development({
                "id": replacement_id,
                "name": f"{feature_status.get('feature_name', 'Unknown')}_Replacement",
                "description": f"Replacement for {feature_id}: {rationale}",
                "requirements": requirements,
                "dependencies": feature_status.get("dependencies", []),
                "replacement_for": feature_id,
                "replacement_method": replacement_method
            })
            
            # Record the replacement relationship in state manager
            await self._state_manager.set_state(
                f"feature:replacement:{feature_id}",
                {
                    "original_id": feature_id,
                    "replacement_id": replacement_id,
                    "method": replacement_method,
                    "timestamp": datetime.now().isoformat(),
                    "rationale": rationale
                },
                ResourceType.STATE
            )
            
            # Record the replacement metric
            await self._metrics_manager.record_metric(
                "feature:evolution:replacement_created",
                1.0,
                metadata={
                    "original_id": feature_id,
                    "replacement_id": replacement_id,
                    "method": replacement_method
                }
            )
            
            return {
                "status": "success",
                "original_id": feature_id,
                "replacement_id": replacement_id,
                "method": replacement_method,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error replacing feature {feature_id}: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "feature_id": feature_id
            }
    
    def _prepare_recreation_requirements(self, 
                                      feature_status: Dict[str, Any],
                                      evaluation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare requirements for feature recreation based on evolutionary feedback.
        
        Args:
            feature_status: Current status of the feature
            evaluation_data: Evaluation data with improvement suggestions
            
        Returns:
            Dict of updated requirements for recreation
        """
        # Start with original requirements
        original_requirements = feature_status.get("requirements", {})
        
        # Extract improvement suggestions from evaluation
        improvements = []
        for pattern in evaluation_data.get("key_patterns", []):
            if pattern.get("issue") and "low quality" in pattern.get("issue", "").lower():
                improvements.extend([evidence for signal in pattern.get("signals", []) 
                                   for evidence in signal.get("key_evidence", [])])
        
        # Add evolutionary improvements to requirements
        if not original_requirements:
            original_requirements = {}
        
        updated_requirements = dict(original_requirements)
        
        # Add evolution-guided improvements
        if "improvements" not in updated_requirements:
            updated_requirements["improvements"] = []
        
        updated_requirements["improvements"].extend(improvements)
        updated_requirements["recreation_from"] = feature_status.get("feature_id")
        
        return updated_requirements
    
    def _prepare_reuse_requirements(self, 
                                 original_feature: Dict[str, Any],
                                 source_feature: Dict[str, Any],
                                 reuse_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare requirements for feature reuse from another feature.
        
        Args:
            original_feature: Feature being replaced
            source_feature: Feature being reused
            reuse_data: Reuse pattern data from evolution agent
            
        Returns:
            Dict of requirements for the new feature
        """
        # Start with source feature requirements
        source_requirements = source_feature.get("requirements", {})
        
        # Adapt them to the original feature's purpose
        adapted_requirements = dict(source_requirements)
        
        # Keep original feature's name and description
        adapted_requirements["original_name"] = original_feature.get("feature_name")
        adapted_requirements["original_description"] = original_feature.get("description")
        
        # Add adaptation guidance from reuse data
        adapted_requirements["reuse_adaptations"] = reuse_data.get("adaptations", [])
        adapted_requirements["reuse_from"] = source_feature.get("feature_id")
        adapted_requirements["reuse_for"] = original_feature.get("feature_id")
        
        # Keep original dependencies
        if "dependencies" not in adapted_requirements:
            adapted_requirements["dependencies"] = []
        
        original_dependencies = original_feature.get("dependencies", [])
        if original_dependencies:
            adapted_requirements["dependencies"].extend(
                [dep for dep in original_dependencies 
                 if dep not in adapted_requirements["dependencies"]]
            )
        
        return adapted_requirements
    
    async def _disable_feature(self, feature_id: str) -> None:
        """Disable a feature by toggling it off.
        
        Args:
            feature_id: ID of the feature to disable
        """
        try:
            logger.info(f"Disabling feature {feature_id} as part of replacement")
            
            # Get feature from state manager
            feature_state = await self._state_manager.get_state(f"feature:development:{feature_id}")
            if not feature_state:
                logger.warning(f"Feature state not found for {feature_id}")
                return
            
            # Update feature state to disabled
            await self._state_manager.set_state(
                f"feature:development:{feature_id}",
                {
                    **feature_state,
                    "state": "DISABLED",
                    "disabled_at": datetime.now().isoformat(),
                    "is_enabled": False
                },
                ResourceType.STATE
            )
            
            # Emit feature disabled event
            self._event_queue.publish(
                "feature_disabled",
                {
                    "feature_id": feature_id,
                    "reason": "evolutionary_replacement",
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Record metric
            await self._metrics_manager.record_metric(
                "feature:disabled",
                1.0,
                metadata={"feature_id": feature_id, "reason": "evolutionary_replacement"}
            )
            
        except Exception as e:
            logger.error(f"Error disabling feature {feature_id}: {str(e)}")
    
    async def _improve_feature(self, 
                            feature_id: str, 
                            rationale: str,
                            evaluation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Improve an existing feature based on evolutionary feedback.
        
        Args:
            feature_id: ID of the feature to improve
            rationale: Reason for improvement
            evaluation_data: Evaluation data with improvement suggestions
            
        Returns:
            Dict containing improvement results
        """
        logger.info(f"Improving feature {feature_id} based on evolutionary selection")
        
        try:
            # Get current feature status
            feature_status = await self._feature_development.get_feature_status(feature_id)
            if not feature_status or "error" in feature_status:
                return {
                    "status": "error",
                    "error": f"Could not retrieve feature status: {feature_status.get('error', 'Unknown error')}",
                    "feature_id": feature_id
                }
            
            # Extract improvement suggestions from evaluation
            improvements = []
            for pattern in evaluation_data.get("key_patterns", []):
                if any(area in pattern.get("affected_areas", []) for area in ["code_quality", "performance", "architecture"]):
                    improvements.extend([evidence for signal in pattern.get("signals", []) 
                                       for evidence in signal.get("key_evidence", [])])
            
            # Extract specific improvement suggestions from adaptations
            for adaptation in evaluation_data.get("adaptations", []):
                if feature_id in adaptation.get("addresses", []):
                    improvements.append(adaptation.get("implementation", ""))
            
            # If no specific improvements found, use general ones
            if not improvements:
                improvements = [
                    "Improve code readability and documentation",
                    "Optimize performance-critical sections",
                    "Enhance error handling and recovery mechanisms",
                    "Improve test coverage for edge cases"
                ]
            
            # Create improvement task
            improvement_id = f"improve_{feature_id}_{int(time.time())}"
            
            # Store improvement task in state manager
            await self._state_manager.set_state(
                f"feature:improvement:{improvement_id}",
                {
                    "feature_id": feature_id,
                    "improvements": improvements,
                    "status": "pending",
                    "created_at": datetime.now().isoformat(),
                    "rationale": rationale
                },
                ResourceType.STATE
            )
            
            # Get feature implementation
            feature_implementation = await self._state_manager.get_state(f"feature:implementation:{feature_id}")
            
            if not feature_implementation:
                return {
                    "status": "pending",
                    "message": "Feature scheduled for improvement, but implementation not found",
                    "improvements": improvements,
                    "improvement_id": improvement_id
                }
            
            # Prepare input for phase four
            improvement_input = {
                "id": feature_id,
                "name": feature_status.get("feature_name", "Unknown"),
                "original_implementation": feature_implementation.get("implementation", ""),
                "improvements": improvements,
                "rationale": rationale
            }
            
            # Use phase four to improve the implementation
            try:
                improvement_result = await self._phase_four_interface.process_feature_improvement(
                    improvement_input
                )
                
                if improvement_result.get("success", False):
                    # Update feature implementation
                    await self._state_manager.set_state(
                        f"feature:implementation:{feature_id}",
                        {
                            **feature_implementation,
                            "implementation": improvement_result.get("improved_code", 
                                                                    feature_implementation.get("implementation", "")),
                            "improved_at": datetime.now().isoformat(),
                            "improvements": improvements
                        },
                        ResourceType.STATE
                    )
                    
                    # Update improvement task status
                    await self._state_manager.set_state(
                        f"feature:improvement:{improvement_id}",
                        {
                            "feature_id": feature_id,
                            "improvements": improvements,
                            "status": "completed",
                            "created_at": datetime.now().isoformat(),
                            "completed_at": datetime.now().isoformat(),
                            "rationale": rationale
                        },
                        ResourceType.STATE
                    )
                    
                    # Record metric
                    await self._metrics_manager.record_metric(
                        "feature:evolution:improved",
                        1.0,
                        metadata={
                            "feature_id": feature_id,
                            "improvement_count": len(improvements)
                        }
                    )
                    
                    return {
                        "status": "success",
                        "feature_id": feature_id,
                        "improvements": improvements,
                        "improvement_id": improvement_id
                    }
                else:
                    # Update improvement task status to failed
                    await self._state_manager.set_state(
                        f"feature:improvement:{improvement_id}",
                        {
                            "feature_id": feature_id,
                            "improvements": improvements,
                            "status": "failed",
                            "created_at": datetime.now().isoformat(),
                            "failed_at": datetime.now().isoformat(),
                            "rationale": rationale,
                            "error": improvement_result.get("error", "Unknown error")
                        },
                        ResourceType.STATE
                    )
                    
                    return {
                        "status": "failed",
                        "feature_id": feature_id,
                        "improvements": improvements,
                        "improvement_id": improvement_id,
                        "error": improvement_result.get("error", "Unknown error")
                    }
            
            except Exception as e:
                logger.error(f"Error improving feature with phase four: {str(e)}")
                # Update improvement task status to error
                await self._state_manager.set_state(
                    f"feature:improvement:{improvement_id}",
                    {
                        "feature_id": feature_id,
                        "improvements": improvements,
                        "status": "error",
                        "created_at": datetime.now().isoformat(),
                        "error_at": datetime.now().isoformat(),
                        "rationale": rationale,
                        "error": str(e)
                    },
                    ResourceType.STATE
                )
                
                return {
                    "status": "error",
                    "feature_id": feature_id,
                    "improvements": improvements,
                    "improvement_id": improvement_id,
                    "error": str(e)
                }
                
        except Exception as e:
            logger.error(f"Error improving feature {feature_id}: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "feature_id": feature_id
            }
    
    async def _combine_features(self, 
                             combination_candidates: List[Dict[str, Any]],
                             evaluation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Combine multiple features into a unified feature.
        
        Args:
            combination_candidates: List of features marked for combination
            evaluation_data: Evaluation data with combination suggestions
            
        Returns:
            Dict containing combination results
        """
        logger.info(f"Combining {len(combination_candidates)} features based on evolutionary selection")
        
        try:
            # Extract feature IDs to combine
            feature_ids = [candidate["feature_id"] for candidate in combination_candidates]
            
            # Find the combination pattern from evaluation data
            combination_pattern = None
            for adaptation in evaluation_data.get("adaptations", []):
                if adaptation.get("strategy", "").lower().startswith("combin") and \
                   any(feature_id in adaptation.get("addresses", []) for feature_id in feature_ids):
                    combination_pattern = adaptation
                    break
            
            if not combination_pattern:
                # Check evolution opportunities
                evolution_opportunities = evaluation_data.get("phase_zero_feedback", {}).get(
                    "evolution_opportunities", {}
                )
                for combo in evolution_opportunities.get("feature_combinations", []):
                    if all(feature_id in combo.get("features", []) for feature_id in feature_ids):
                        combination_pattern = combo
                        break
            
            # If still no pattern, create a default one
            if not combination_pattern:
                combination_pattern = {
                    "strategy": "Combine related features",
                    "implementation": "Merge functionality while eliminating redundancy",
                    "benefits": ["Reduced complexity", "Improved cohesion", "Simplified dependencies"]
                }
            
            # Create a new combined feature ID
            combined_id = f"combined_{'_'.join(feature_ids)}_{int(time.time())}"
            
            # Get statuses for all features
            feature_statuses = {}
            for feature_id in feature_ids:
                status = await self._feature_development.get_feature_status(feature_id)
                if not status or "error" in status:
                    logger.warning(f"Could not retrieve status for feature {feature_id}")
                    continue
                feature_statuses[feature_id] = status
            
            if not feature_statuses:
                return {
                    "status": "error",
                    "error": "Could not retrieve status for any features to combine",
                    "feature_ids": feature_ids
                }
            
            # Collect all dependencies from all features
            all_dependencies = set()
            for status in feature_statuses.values():
                all_dependencies.update(status.get("dependencies", []))
            
            # Remove the features being combined from dependencies
            all_dependencies = all_dependencies.difference(feature_ids)
            
            # Create combined name and description
            feature_names = [status.get("feature_name", "Unknown") for status in feature_statuses.values()]
            combined_name = f"Combined: {' + '.join(feature_names)}"
            combined_description = f"Combined feature created from: {', '.join(feature_names)}"
            
            # Disable original features
            for feature_id in feature_ids:
                await self._disable_feature(feature_id)
            
            # Start development of the combined feature
            combined_feature = {
                "id": combined_id,
                "name": combined_name,
                "description": combined_description,
                "combined_from": feature_ids,
                "dependencies": list(all_dependencies),
                "combination_pattern": combination_pattern
            }
            
            # Start development of the combined feature
            combination_result = await self._feature_development.start_feature_development(combined_feature)
            
            # Record the combination relationship in state manager
            await self._state_manager.set_state(
                f"feature:combination:{combined_id}",
                {
                    "combined_id": combined_id,
                    "original_ids": feature_ids,
                    "timestamp": datetime.now().isoformat(),
                    "rationale": combination_pattern.get("implementation", "")
                },
                ResourceType.STATE
            )
            
            # Record the combination metric
            await self._metrics_manager.record_metric(
                "feature:evolution:combination_created",
                1.0,
                metadata={
                    "combined_id": combined_id,
                    "original_count": len(feature_ids),
                    "original_ids": feature_ids
                }
            )
            
            return {
                "status": "success",
                "combined_id": combined_id,
                "original_ids": feature_ids,
                "combination_pattern": combination_pattern.get("implementation", ""),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error combining features: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "feature_ids": feature_ids if 'feature_ids' in locals() else []
            }
    
    async def get_component_features(self, component_id: str) -> List[Dict[str, Any]]:
        """Get all features for a component."""
        # Get all feature statuses
        all_statuses = await self._feature_development.get_all_feature_statuses()
        
        # Filter for the specified component if available
        if component_id:
            # In a real implementation, this would filter based on component ID
            # For now, we just return all features
            component_features = list(all_statuses.values())
        else:
            component_features = list(all_statuses.values())
            
        return component_features
    
    async def get_cultivation_status(self, operation_id: str) -> Dict[str, Any]:
        """Get the status of a cultivation operation."""
        cultivation_state = await self._state_manager.get_state(f"phase_three:cultivation:{operation_id}")
        
        if not cultivation_state:
            return {"error": f"Cultivation operation {operation_id} not found"}
            
        # Get current status of all started features
        started_features = cultivation_state.get("started_features", [])
        feature_statuses = {}
        
        for feature_id in started_features:
            feature_statuses[feature_id] = await self._feature_development.get_feature_status(feature_id)
            
        # Count features in each state
        state_counts = {}
        for status in feature_statuses.values():
            state = status.get("state", "UNKNOWN")
            state_counts[state] = state_counts.get(state, 0) + 1
            
        # Calculate overall completion percentage
        total_features = cultivation_state.get("total_features", 0)
        completed_features = state_counts.get(FeatureDevelopmentState.COMPLETED.name, 0)
        
        if total_features > 0:
            completion_percentage = (completed_features / total_features) * 100
        else:
            completion_percentage = 0
            
        return {
            "operation_id": operation_id,
            "total_features": total_features,
            "started_features": started_features,
            "feature_statuses": feature_statuses,
            "state_counts": state_counts,
            "completion_percentage": completion_percentage,
            "timestamp": datetime.now().isoformat()
        }