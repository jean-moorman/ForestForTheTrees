"""Agent responsible for running static compilation checks."""

import asyncio
import logging
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional

from resources import (
    EventQueue, 
    StateManager, 
    AgentContextManager, 
    CacheManager, 
    MetricsManager, 
    ErrorHandler, 
    MemoryMonitor,
    CircuitBreakerConfig
)
from resources.monitoring import CircuitBreaker, CircuitOpenError
from interface import AgentInterface, AgentState

from phase_four.models import CompilerType, CompilationState, CompilationResult, CompilationContext
from phase_four.utils import parse_compiler_output

logger = logging.getLogger(__name__)


class StaticCompilationAgent(AgentInterface):
    """Agent responsible for running static compilation checks"""
    
    def __init__(self, 
                event_queue: EventQueue,
                state_manager: StateManager,
                context_manager: AgentContextManager,
                cache_manager: CacheManager,
                metrics_manager: MetricsManager,
                error_handler: ErrorHandler,
                memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "static_compilation_agent", 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            error_handler, 
            metrics_manager,
            memory_monitor
        )
        self._circuit_breaker = CircuitBreaker(
            "static_compilation", 
            event_queue, 
            CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=60,
                failure_window=600
            )
        )
    
    async def _run_compiler(self, ctx: CompilationContext, 
                         compiler_type: CompilerType) -> CompilationResult:
        """Run a specific compiler on the code."""
        result = CompilationResult(compiler_type=compiler_type)
        result.state = CompilationState.RUNNING
        
        start_time = time.time()
        
        try:
            # Write the code to a temporary file
            with open(ctx.source_file_path, 'w') as file:
                file.write(ctx.feature_code)
            
            # Define compiler commands based on compiler type
            commands = {
                CompilerType.FORMAT: ["black", "--check", ctx.source_file_path],
                CompilerType.STYLE: ["flake8", ctx.source_file_path],
                CompilerType.LINT: ["pylint", ctx.source_file_path],
                CompilerType.TYPE: ["mypy", ctx.source_file_path],
                CompilerType.SECURITY: ["bandit", "-r", ctx.source_file_path]
            }
            
            command = commands[compiler_type]
            
            # Run command in a separate thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                process = await loop.run_in_executor(
                    executor,
                    lambda: subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        check=False
                    )
                )
            
            # Process results
            result.output = process.stdout
            result.error_message = process.stderr
            result.success = process.returncode == 0
            
            # Format-specific success if black finds no formatting issues
            if compiler_type == CompilerType.FORMAT and "would be reformatted" not in result.output:
                result.success = True
            
            # Parse issues into structured format
            if not result.success:
                result.state = CompilationState.FAILED
                result.issues = parse_compiler_output(
                    compiler_type, result.output, result.error_message
                )
            else:
                result.state = CompilationState.SUCCEEDED
                
        except Exception as e:
            logger.error(f"Error running {compiler_type.name} compiler: {str(e)}", exc_info=True)
            result.state = CompilationState.ERROR
            result.success = False
            result.error_message = str(e)
            
        finally:
            result.execution_time = time.time() - start_time
            return result
    
    async def run_compilation(self, 
                           code: str, 
                           feature_id: str,
                           operation_id: str) -> Dict[str, Any]:
        """Run all compilation steps on the given code."""
        try:
            logger.info(f"Starting compilation process for feature {feature_id}")
            
            # Set agent state to processing
            await self.set_agent_state(AgentState.PROCESSING)
            
            # Create temporary source file
            temp_dir = "/tmp/fftt_phase_four"
            os.makedirs(temp_dir, exist_ok=True)
            source_file_path = f"{temp_dir}/{feature_id}.py"
            
            # Create compilation context
            ctx = CompilationContext(
                feature_code=code,
                feature_id=feature_id,
                source_file_path=source_file_path
            )
            
            # Run all compilers in sequence
            for compiler_type in CompilerType:
                try:
                    # Use circuit breaker to prevent excessive failures
                    result = await self._circuit_breaker.execute(
                        lambda: self._run_compiler(ctx, compiler_type)
                    )
                    ctx.results[compiler_type] = result
                    
                    # Record metrics
                    await self._metrics_manager.record_metric(
                        f"compiler:{compiler_type.name.lower()}:execution_time",
                        result.execution_time,
                        metadata={
                            "feature_id": feature_id,
                            "success": result.success
                        }
                    )
                    
                    # If compilation failed, break the sequence
                    if not result.success:
                        break
                        
                except CircuitOpenError:
                    logger.error(f"Circuit breaker open for {compiler_type.name} compilation")
                    ctx.results[compiler_type] = CompilationResult(
                        compiler_type=compiler_type,
                        state=CompilationState.ERROR,
                        success=False,
                        error_message="Circuit breaker open due to excessive failures"
                    )
                    break
                    
                except Exception as e:
                    logger.error(f"Error in {compiler_type.name} compilation: {str(e)}", exc_info=True)
                    ctx.results[compiler_type] = CompilationResult(
                        compiler_type=compiler_type,
                        state=CompilationState.ERROR,
                        success=False,
                        error_message=str(e)
                    )
                    break
            
            # Check if all compilers passed
            all_passed = all(result.success for result in ctx.results.values())
            
            # Update state based on results
            if all_passed:
                await self.set_agent_state(AgentState.COMPLETE)
            else:
                await self.set_agent_state(AgentState.FAILED_VALIDATION)
            
            # Prepare response
            response = {
                "feature_id": feature_id,
                "operation_id": operation_id,
                "success": all_passed,
                "results": {
                    compiler_type.name.lower(): {
                        "success": result.success,
                        "state": result.state.name,
                        "issues": result.issues,
                        "execution_time": result.execution_time,
                    }
                    for compiler_type, result in ctx.results.items()
                }
            }
            
            logger.info(f"Compilation completed for {feature_id}: {all_passed}")
            return response
            
        except Exception as e:
            logger.error(f"Error in compilation process: {str(e)}", exc_info=True)
            await self.set_agent_state(AgentState.ERROR)
            
            return {
                "feature_id": feature_id,
                "operation_id": operation_id,
                "success": False,
                "error": str(e)
            }