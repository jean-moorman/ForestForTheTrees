"""Agent that coordinates the refinement process for compilation failures."""

import logging
import time
from typing import Dict, Any, Optional

from resources import (
    EventQueue, 
    StateManager, 
    AgentContextManager, 
    CacheManager, 
    MetricsManager, 
    ErrorHandler, 
    MemoryMonitor
)
from interface import AgentInterface, AgentState, ValidationManager

from phase_four.agents.code_generation import CodeGenerationAgent
from phase_four.agents.static_compilation import StaticCompilationAgent
from phase_four.agents.debug import CompilationDebugAgent
from phase_four.agents.analysis import CompilationAnalysisAgent

logger = logging.getLogger(__name__)


class CompilationRefinementAgent(AgentInterface):
    """Agent that coordinates the refinement process for compilation failures"""
    
    def __init__(self, 
                event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "compilation_refinement_agent", 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler,
            memory_monitor
        )
        
        # Initialize validation manager
        self._validation_manager = ValidationManager(event_queue, state_manager, context_manager)
        
        # Initialize code generation, static compilation, and debug agents
        self.code_generation_agent = CodeGenerationAgent(
            event_queue, state_manager, context_manager, 
            cache_manager, metrics_manager, error_handler, memory_monitor
        )
        
        self.static_compilation_agent = StaticCompilationAgent(
            event_queue, state_manager, context_manager, 
            cache_manager, metrics_manager, error_handler, memory_monitor
        )
        
        self.compilation_debug_agent = CompilationDebugAgent(
            event_queue, state_manager, context_manager, 
            cache_manager, metrics_manager, error_handler, memory_monitor
        )
        
        self.compilation_analysis_agent = CompilationAnalysisAgent(
            event_queue, state_manager, context_manager, 
            cache_manager, metrics_manager, error_handler, memory_monitor
        )
    
    async def refine_code(self, 
                       feature_requirements: Dict[str, Any],
                       initial_code: Optional[str] = None,
                       max_iterations: int = 5,
                       operation_id: str = None) -> Dict[str, Any]:
        """Coordinate the code refinement process."""
        if not operation_id:
            operation_id = f"refine_{int(time.time())}"
            
        try:
            logger.info(f"Starting code refinement process for operation {operation_id}")
            
            # Set agent state to processing
            await self.set_agent_state(AgentState.PROCESSING)
            
            feature_id = feature_requirements.get("id", f"feature_{operation_id}")
            feature_name = feature_requirements.get("name", "unnamed_feature")
            
            # Record refinement process start
            await self._metrics_manager.record_metric(
                "refinement_process:start",
                1.0,
                metadata={
                    "feature_id": feature_id,
                    "feature_name": feature_name,
                    "operation_id": operation_id
                }
            )
            
            # Generate initial code if not provided
            current_code = initial_code
            if not current_code:
                logger.info(f"Generating initial code for {feature_name}")
                code_result = await self.code_generation_agent.generate_code(
                    feature_requirements, operation_id
                )
                
                if "error" in code_result:
                    logger.error(f"Initial code generation failed: {code_result['error']}")
                    await self.set_agent_state(AgentState.ERROR)
                    return {
                        "feature_id": feature_id,
                        "feature_name": feature_name,
                        "operation_id": operation_id,
                        "success": False,
                        "error": code_result["error"],
                        "stage": "code_generation"
                    }
                    
                current_code = code_result.get("code", "")
            
            # Track refinement history
            refinement_history = []
            iteration = 0
            success = False
            
            # Iterate until success or max iterations reached
            while iteration < max_iterations and not success:
                iteration += 1
                logger.info(f"Refinement iteration {iteration}/{max_iterations} for {feature_name}")
                
                # Run static compilation checks
                compilation_result = await self.static_compilation_agent.run_compilation(
                    current_code, feature_id, operation_id
                )
                
                # Check if compilation succeeded
                if compilation_result.get("success", False):
                    logger.info(f"Compilation succeeded on iteration {iteration}")
                    success = True
                    break
                
                # Debug compilation failures
                debug_result = await self.compilation_debug_agent.analyze_failures(
                    current_code, compilation_result, operation_id
                )
                
                # Update code with fixed version
                if debug_result.get("success", False) and "fixed_code" in debug_result:
                    current_code = debug_result["fixed_code"]
                    
                    # Record iteration details
                    refinement_history.append({
                        "iteration": iteration,
                        "compilation_result": compilation_result,
                        "debug_result": {
                            "analysis": debug_result.get("analysis", ""),
                            "suggestions": debug_result.get("suggestions", [])
                        }
                    })
                else:
                    logger.error(f"Debug analysis failed on iteration {iteration}")
                    break
            
            # Run final analysis even if we hit max iterations
            final_analysis = await self.compilation_analysis_agent.analyze_compilation(
                current_code, compilation_result, operation_id
            )
            
            # Update state based on results
            if success:
                await self.set_agent_state(AgentState.COMPLETE)
            else:
                await self.set_agent_state(AgentState.FAILED_VALIDATION)
            
            # Record refinement process end
            await self._metrics_manager.record_metric(
                "refinement_process:end",
                1.0,
                metadata={
                    "feature_id": feature_id,
                    "feature_name": feature_name,
                    "success": success,
                    "iterations": iteration,
                    "operation_id": operation_id
                }
            )
            
            # Prepare final response
            response = {
                "feature_id": feature_id,
                "feature_name": feature_name,
                "operation_id": operation_id,
                "success": success,
                "iterations": iteration,
                "code": current_code,
                "refinement_history": refinement_history,
                "analysis": final_analysis.get("metrics", {}),
                "improvement_suggestions": final_analysis.get("improvements", [])
            }
            
            logger.info(f"Code refinement completed for {feature_name}: success={success}, iterations={iteration}")
            return response
            
        except Exception as e:
            logger.error(f"Error in code refinement process: {str(e)}", exc_info=True)
            await self.set_agent_state(AgentState.ERROR)
            
            return {
                "feature_id": feature_requirements.get("id", f"feature_{operation_id}"),
                "feature_name": feature_requirements.get("name", "unnamed_feature"),
                "operation_id": operation_id,
                "success": False,
                "error": f"Code refinement failed: {str(e)}"
            }