"""Interface for Phase Four operations.

This module provides the main entry point for integrating Phase Four functionality
into the wider FFTT system. It coordinates the code generation, compilation,
and improvement processes through a clean, high-level interface.

Phase Four is responsible for taking feature requirements and generating
high-quality code that passes multiple layers of static compilation checks,
including formatting, style, linting, type checking, and security analysis.
"""

import json
import logging
import time
from typing import Dict, List, Any, Optional

from resources import (
    ResourceType, 
    EventQueue, 
    StateManager, 
    AgentContextManager, 
    CacheManager, 
    MetricsManager, 
    ErrorHandler, 
    MemoryMonitor,
    SystemMonitor
)

from phase_four.agents.refinement import CompilationRefinementAgent
from phase_four.utils import create_improvement_prompt

logger = logging.getLogger(__name__)


class PhaseFourInterface:
    """Interface for Phase Four operations.
    
    This class provides the primary interface for other components to interact
    with Phase Four functionality. It coordinates the code generation, static
    compilation, and code improvement processes, providing a simplified API
    that abstracts away the complexity of the underlying agent interactions.
    
    The interface supports two main operations:
    1. process_feature_code: Generate and refine code for a new feature
    2. process_feature_improvement: Improve existing feature code
    
    Both operations ensure that the resulting code passes all static compilation
    checks and meets quality standards.
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
        """Initialize the Phase Four interface.
        
        Args:
            event_queue: Queue for publishing and subscribing to events
            state_manager: Manager for accessing and updating system state
            context_manager: Manager for agent context information
            cache_manager: Manager for caching results
            metrics_manager: Manager for recording metrics
            error_handler: Handler for processing errors
            memory_monitor: Optional monitor for tracking memory usage
            system_monitor: Optional monitor for tracking system health
        """
        self._event_queue = event_queue
        self._state_manager = state_manager
        self._context_manager = context_manager
        self._cache_manager = cache_manager
        self._metrics_manager = metrics_manager
        self._error_handler = error_handler
        self._memory_monitor = memory_monitor
        self._system_monitor = system_monitor
        
        # Initialize the code refinement agent
        self.refinement_agent = CompilationRefinementAgent(
            event_queue, state_manager, context_manager, 
            cache_manager, metrics_manager, error_handler, memory_monitor
        )
        
        logger.info("Phase Four interface initialized")
    
    async def process_feature_code(self, 
                               feature_requirements: Dict[str, Any],
                               initial_code: Optional[str] = None,
                               max_iterations: int = 5) -> Dict[str, Any]:
        """Process feature code generation and compilation.
        
        This method takes feature requirements and generates code that implements
        those requirements. The generated code is then passed through a series of
        static compilation checks, and refined iteratively until it passes all checks
        or reaches the maximum number of iterations.
        
        Args:
            feature_requirements: Dictionary containing feature specifications,
                including id, name, description, and other requirements
            initial_code: Optional starting code. If not provided, code will be
                generated from scratch based on the requirements
            max_iterations: Maximum number of refinement iterations to attempt
                
        Returns:
            A dictionary containing the results of the process, including:
                - feature_id: The ID of the feature
                - feature_name: The name of the feature
                - operation_id: A unique identifier for this operation
                - success: Whether the process completed successfully
                - code: The final generated and refined code
                - iterations: Number of refinement iterations performed
                - refinement_history: Details of each refinement iteration
                - analysis: Code quality analysis metrics
                - improvement_suggestions: Suggestions for further improvements
        """
        operation_id = f"phase_four_{int(time.time())}"
        
        try:
            logger.info(f"Starting Phase Four processing for operation {operation_id}")
            
            # Record process start
            await self._metrics_manager.record_metric(
                "phase_four:process:start",
                1.0,
                metadata={
                    "feature_id": feature_requirements.get("id", "unknown"),
                    "feature_name": feature_requirements.get("name", "unknown"),
                    "operation_id": operation_id
                }
            )
            
            # Run the code refinement process
            result = await self.refinement_agent.refine_code(
                feature_requirements,
                initial_code,
                max_iterations,
                operation_id
            )
            
            # Record process end
            await self._metrics_manager.record_metric(
                "phase_four:process:end",
                1.0,
                metadata={
                    "feature_id": feature_requirements.get("id", "unknown"),
                    "feature_name": feature_requirements.get("name", "unknown"),
                    "success": result.get("success", False),
                    "operation_id": operation_id
                }
            )
            
            # Store the result in state manager
            await self._state_manager.set_state(
                f"phase_four:result:{operation_id}",
                result,
                ResourceType.STATE
            )
            
            logger.info(f"Phase Four processing completed for operation {operation_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error in Phase Four processing: {str(e)}", exc_info=True)
            
            # Record error
            await self._metrics_manager.record_metric(
                "phase_four:process:error",
                1.0,
                metadata={
                    "feature_id": feature_requirements.get("id", "unknown"),
                    "feature_name": feature_requirements.get("name", "unknown"),
                    "error": str(e),
                    "operation_id": operation_id
                }
            )
            
            return {
                "feature_id": feature_requirements.get("id", "unknown"),
                "feature_name": feature_requirements.get("name", "unknown"),
                "operation_id": operation_id,
                "success": False,
                "error": f"Phase Four processing failed: {str(e)}"
            }
    
    async def process_feature_improvement(self, improvement_request: Dict[str, Any]) -> Dict[str, Any]:
        """Improve existing feature code based on improvement suggestions.
        
        This method takes existing feature code and a list of improvement suggestions,
        then uses an LLM to improve the code according to those suggestions. The
        improved code is then passed through static compilation checks to ensure it
        remains valid.
        
        Args:
            improvement_request: Dictionary containing:
                - id: Feature ID
                - name: Feature name
                - original_implementation: Original code to improve
                - improvements: List of improvement suggestions
                - rationale: Reason for improvement
                
        Returns:
            A dictionary containing the results of the improvement process, including:
                - feature_id: The ID of the feature
                - feature_name: The name of the feature
                - operation_id: A unique identifier for this operation
                - success: Whether the process completed successfully
                - improved_code: The improved version of the code
                - improvements_applied: Details of the improvements that were applied
                - explanation: Explanation of the changes made
                - compilation_results: Results of the static compilation checks
        """
        operation_id = f"improve_{int(time.time())}"
        feature_id = improvement_request.get("id", "unknown")
        feature_name = improvement_request.get("name", "unknown")
        
        try:
            logger.info(f"Starting feature improvement for {feature_name} (ID: {feature_id})")
            
            # Record improvement start
            await self._metrics_manager.record_metric(
                "phase_four:improvement:start",
                1.0,
                metadata={
                    "feature_id": feature_id,
                    "feature_name": feature_name,
                    "operation_id": operation_id
                }
            )
            
            # Extract improvement suggestions and original code
            original_code = improvement_request.get("original_implementation", "")
            improvements = improvement_request.get("improvements", [])
            rationale = improvement_request.get("rationale", "Unknown reason")
            
            if not original_code:
                raise ValueError("Original implementation is required for improvement")
                
            if not improvements:
                logger.warning("No improvement suggestions provided")
                return {
                    "feature_id": feature_id,
                    "feature_name": feature_name,
                    "operation_id": operation_id,
                    "success": False,
                    "error": "No improvement suggestions provided"
                }
            
            # Create prompt for code improvement
            improvement_prompt = create_improvement_prompt(
                original_code, improvements, rationale
            )
            
            # Create improvements schema
            schema = {
                "type": "object",
                "required": ["improved_code", "explanation", "improvements_applied"],
                "properties": {
                    "improved_code": {"type": "string"},
                    "explanation": {"type": "string"},
                    "improvements_applied": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["description", "changes"],
                            "properties": {
                                "description": {"type": "string"},
                                "changes": {"type": "string"}
                            }
                        }
                    }
                }
            }
            
            # Call LLM to improve code
            conversation = {
                "original_code": original_code,
                "improvements": improvements,
                "rationale": rationale
            }
            
            # Use validation manager from refinement agent
            improve_response = await self.refinement_agent._validation_manager.validate_llm_response(
                conversation=json.dumps(conversation),
                system_prompt_info=(improvement_prompt,),
                schema=schema,
                current_phase="feature_improvement",
                operation_id=operation_id,
                metadata={
                    "feature_id": feature_id,
                    "feature_name": feature_name
                }
            )
            
            # Get the improved code
            improved_code = improve_response.get("improved_code", "")
            
            # Now run the code through compilation checks
            compilation_result = await self.refinement_agent.static_compilation_agent.run_compilation(
                improved_code, feature_id, operation_id
            )
            
            # If compilation failed, try to fix it
            if not compilation_result.get("success", False):
                logger.info(f"Compilation failed after improvement, attempting to fix issues")
                
                # Debug compilation failures
                debug_result = await self.refinement_agent.compilation_debug_agent.analyze_failures(
                    improved_code, compilation_result, operation_id
                )
                
                # Use fixed code if available
                if debug_result.get("success", False) and "fixed_code" in debug_result:
                    improved_code = debug_result["fixed_code"]
                    
                    # Run compilation again
                    compilation_result = await self.refinement_agent.static_compilation_agent.run_compilation(
                        improved_code, feature_id, operation_id
                    )
            
            # Prepare final result
            success = compilation_result.get("success", False)
            result = {
                "feature_id": feature_id,
                "feature_name": feature_name,
                "operation_id": operation_id,
                "success": success,
                "improved_code": improved_code,
                "improvements_applied": improve_response.get("improvements_applied", []),
                "explanation": improve_response.get("explanation", ""),
                "compilation_results": compilation_result.get("results", {})
            }
            
            # Record improvement completion
            await self._metrics_manager.record_metric(
                "phase_four:improvement:complete",
                1.0,
                metadata={
                    "feature_id": feature_id,
                    "feature_name": feature_name,
                    "success": success,
                    "operation_id": operation_id
                }
            )
            
            # Store the result in state manager
            await self._state_manager.set_state(
                f"phase_four:improvement:{operation_id}",
                result,
                ResourceType.STATE
            )
            
            logger.info(f"Feature improvement completed for {feature_name}: success={success}")
            return result
            
        except Exception as e:
            logger.error(f"Error in feature improvement: {str(e)}", exc_info=True)
            
            # Record error
            await self._metrics_manager.record_metric(
                "phase_four:improvement:error",
                1.0,
                metadata={
                    "feature_id": feature_id,
                    "feature_name": feature_name,
                    "error": str(e),
                    "operation_id": operation_id
                }
            )
            
            return {
                "feature_id": feature_id,
                "feature_name": feature_name,
                "operation_id": operation_id,
                "success": False,
                "error": f"Feature improvement failed: {str(e)}"
            }