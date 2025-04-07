import asyncio
import json
import logging
import subprocess
import os
import time
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum, auto
from concurrent.futures import ThreadPoolExecutor

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
from resources.monitoring import CircuitBreaker, CircuitOpenError
from interface import AgentInterface, ValidationManager, AgentState

logger = logging.getLogger(__name__)

class CompilerType(Enum):
    """Types of static compilation checks"""
    FORMAT = auto()  # Black code formatter
    STYLE = auto()   # Flake8 style checks
    LINT = auto()    # Pylint deep logical analysis
    TYPE = auto()    # MyPy type checking
    SECURITY = auto() # Bandit security checks

class CompilationState(Enum):
    """States for compilation process"""
    PENDING = auto()
    RUNNING = auto()
    FAILED = auto()
    SUCCEEDED = auto()
    ERROR = auto()

@dataclass
class CompilationResult:
    """Result of a compilation step"""
    compiler_type: CompilerType
    state: CompilationState = CompilationState.PENDING
    success: bool = False
    output: str = ""
    error_message: str = ""
    execution_time: float = 0.0
    issues: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class CompilationContext:
    """Context for a compilation process"""
    feature_code: str
    feature_id: str
    source_file_path: str
    results: Dict[CompilerType, CompilationResult] = field(default_factory=dict)
    current_stage: CompilerType = CompilerType.FORMAT
    max_iterations: int = 5
    current_iteration: int = 0
    start_time: float = field(default_factory=time.time)

class CodeGenerationAgent(AgentInterface):
    """Agent responsible for generating feature code from requirements"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "code_generation_agent", 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler,
            memory_monitor
        )
        self._validation_manager = ValidationManager(event_queue, state_manager, context_manager)
        
    async def generate_code(self, 
                          feature_requirements: Dict[str, Any],
                          operation_id: str) -> Dict[str, Any]:
        """Generate code based on feature requirements."""
        try:
            logger.info(f"Starting code generation for operation {operation_id}")
            
            # Set agent state to processing
            await self.set_agent_state(AgentState.PROCESSING)
            
            # Prepare feature requirements for the prompt
            requirements_str = json.dumps(feature_requirements)
            
            # Get feature name and id
            feature_name = feature_requirements.get("name", "unnamed_feature")
            feature_id = feature_requirements.get("id", f"feature_{operation_id}")
            
            # Create schema for validation
            schema = {
                "type": "object",
                "required": ["code", "explanation"],
                "properties": {
                    "code": {"type": "string"},
                    "explanation": {"type": "string"},
                    "imports": {"type": "array", "items": {"type": "string"}},
                    "dependencies": {"type": "array", "items": {"type": "string"}}
                }
            }
            
            # Determine language, default to Python
            language = feature_requirements.get("language", "python")
            
            # Generate system prompt for code generation
            system_prompt = f"""You are an expert {language} developer. 
Generate clean, well-structured, type-annotated code for a feature based on the requirements.
Focus on creating code that is:
1. Correct - implements all requirements accurately
2. Well-structured - follows good design patterns
3. Maintainable - clear, commented, and easy to understand
4. Type-annotated - uses proper type hints
5. Robust - includes appropriate error handling

Return your response as JSON with these fields:
- code: The implementation code as a string
- explanation: Brief explanation of the code structure
- imports: List of imports needed
- dependencies: List of other features or components this depends on
"""
            
            # Call LLM to generate code
            response = await self.process_with_validation(
                conversation=requirements_str,
                system_prompt_info=(system_prompt,),
                schema=schema,
                current_phase="code_generation",
                operation_id=operation_id,
                metadata={
                    "feature_name": feature_name,
                    "feature_id": feature_id
                }
            )
            
            # Update state to complete
            await self.set_agent_state(AgentState.COMPLETE)
            
            # Add feature metadata to the response
            response.update({
                "feature_name": feature_name,
                "feature_id": feature_id,
                "operation_id": operation_id
            })
            
            logger.info(f"Code generation completed for {feature_name}")
            return response
            
        except Exception as e:
            logger.error(f"Error generating code: {str(e)}", exc_info=True)
            await self.set_agent_state(AgentState.ERROR)
            
            return {
                "error": f"Code generation failed: {str(e)}",
                "feature_name": feature_requirements.get("name", "unnamed_feature"),
                "feature_id": feature_requirements.get("id", f"feature_{operation_id}"),
                "operation_id": operation_id
            }

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
                result.issues = self._parse_compiler_output(
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
    
    def _parse_compiler_output(self, compiler_type: CompilerType, 
                              stdout: str, stderr: str) -> List[Dict[str, Any]]:
        """Parse compiler output into structured issues."""
        issues = []
        
        if compiler_type == CompilerType.FORMAT:
            # Parse black output
            if "would be reformatted" in stdout:
                issues.append({
                    "type": "formatting",
                    "message": "Code requires reformatting",
                    "severity": "low"
                })
                
        elif compiler_type == CompilerType.STYLE:
            # Parse flake8 output
            for line in stdout.split('\n'):
                if ':' in line:
                    parts = line.strip().split(':')
                    if len(parts) >= 4:
                        file_path, line_num, col, message = parts[0:4]
                        issues.append({
                            "type": "style",
                            "line": int(line_num),
                            "column": int(col),
                            "message": message.strip(),
                            "severity": "medium"
                        })
                        
        elif compiler_type == CompilerType.LINT:
            # Parse pylint output
            for line in stdout.split('\n'):
                if ':' in line and 'error' in line.lower() or 'warning' in line.lower():
                    parts = line.split(':')
                    if len(parts) >= 2:
                        message = parts[-1].strip()
                        severity = "high" if "error" in line.lower() else "medium"
                        issues.append({
                            "type": "lint",
                            "message": message,
                            "severity": severity
                        })
                        
        elif compiler_type == CompilerType.TYPE:
            # Parse mypy output
            for line in stdout.split('\n'):
                if ':' in line and 'error' in line:
                    parts = line.split(':')
                    if len(parts) >= 3:
                        file_path, line_num = parts[0:2]
                        message = ':'.join(parts[2:]).strip()
                        issues.append({
                            "type": "type",
                            "line": int(line_num) if line_num.isdigit() else 0,
                            "message": message,
                            "severity": "high"
                        })
                        
        elif compiler_type == CompilerType.SECURITY:
            # Parse bandit output
            for line in stdout.split('\n'):
                if 'Issue:' in line or 'Severity:' in line:
                    message = line.strip()
                    severity = "high" if "High" in line else "medium" if "Medium" in line else "low"
                    issues.append({
                        "type": "security",
                        "message": message,
                        "severity": severity
                    })
        
        return issues
    
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

class CompilationDebugAgent(AgentInterface):
    """Agent that analyzes compiler failures and suggests fixes"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "compilation_debug_agent", 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler,
            memory_monitor
        )
    
    async def analyze_failures(self, 
                             code: str,
                             compilation_results: Dict[str, Any],
                             operation_id: str) -> Dict[str, Any]:
        """Analyze compilation failures and suggest fixes."""
        try:
            logger.info(f"Analyzing compilation failures for operation {operation_id}")
            
            # Set agent state to processing
            await self.set_agent_state(AgentState.PROCESSING)
            
            # Identify failed compiler steps
            failed_steps = []
            results = compilation_results.get("results", {})
            
            for compiler, result in results.items():
                if not result.get("success", False):
                    failed_steps.append({
                        "compiler": compiler,
                        "issues": result.get("issues", []),
                        "state": result.get("state", "UNKNOWN")
                    })
            
            # Skip if no failures found
            if not failed_steps:
                logger.info("No compilation failures to analyze")
                await self.set_agent_state(AgentState.COMPLETE)
                return {
                    "operation_id": operation_id,
                    "success": True,
                    "analysis": "No compilation failures to analyze",
                    "suggestions": []
                }
            
            # Format the issues for the prompt
            issues_str = json.dumps(failed_steps, indent=2)
            
            # Create schema for validation
            schema = {
                "type": "object",
                "required": ["analysis", "suggestions", "fixed_code"],
                "properties": {
                    "analysis": {"type": "string"},
                    "suggestions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["issue", "fix"],
                            "properties": {
                                "issue": {"type": "string"},
                                "fix": {"type": "string"},
                                "line_numbers": {"type": "array", "items": {"type": "integer"}}
                            }
                        }
                    },
                    "fixed_code": {"type": "string"}
                }
            }
            
            # Generate system prompt for analysis
            system_prompt = """You are an expert programming compiler specialist who diagnoses and fixes code issues.
Analyze the provided code and compilation issues, then suggest specific fixes to resolve each issue.
Focus on being precise and practical:
1. Identify the root cause of each compilation failure
2. Suggest specific code changes to fix each issue
3. Provide a fully corrected version of the code
4. Prioritize fixes for the most critical issues first

Return your response as JSON with these fields:
- analysis: A detailed analysis of the compilation failures
- suggestions: An array of objects, each with 'issue' (description of the problem) and 'fix' (how to fix it) fields
- fixed_code: The complete fixed version of the code
"""
            
            # Call LLM to analyze failures
            conversation = {
                "code": code,
                "compilation_failures": issues_str
            }
            
            response = await self.process_with_validation(
                conversation=json.dumps(conversation),
                system_prompt_info=(system_prompt,),
                schema=schema,
                current_phase="compilation_debug",
                operation_id=operation_id
            )
            
            # Update state to complete
            await self.set_agent_state(AgentState.COMPLETE)
            
            # Add operation id to the response
            response["operation_id"] = operation_id
            response["success"] = True
            
            logger.info(f"Compilation failure analysis completed for {operation_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error analyzing compilation failures: {str(e)}", exc_info=True)
            await self.set_agent_state(AgentState.ERROR)
            
            return {
                "operation_id": operation_id,
                "success": False,
                "error": f"Compilation failure analysis failed: {str(e)}"
            }

class CompilationAnalysisAgent(AgentInterface):
    """Agent that performs deep analysis of compilation results"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None):
        super().__init__(
            "compilation_analysis_agent", 
            event_queue, 
            state_manager, 
            context_manager, 
            cache_manager, 
            metrics_manager, 
            error_handler,
            memory_monitor
        )
    
    async def analyze_compilation(self, 
                               code: str,
                               compilation_results: Dict[str, Any],
                               operation_id: str) -> Dict[str, Any]:
        """Analyze compilation results and provide insights."""
        try:
            logger.info(f"Performing compilation analysis for operation {operation_id}")
            
            # Set agent state to processing
            await self.set_agent_state(AgentState.PROCESSING)
            
            # Format the results for the prompt
            results_str = json.dumps(compilation_results, indent=2)
            
            # Create schema for validation
            schema = {
                "type": "object",
                "required": ["summary", "insights", "metrics", "improvements"],
                "properties": {
                    "summary": {"type": "string"},
                    "insights": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "metrics": {
                        "type": "object",
                        "properties": {
                            "code_quality_score": {"type": "number"},
                            "robustness_score": {"type": "number"},
                            "maintainability_score": {"type": "number"},
                            "security_score": {"type": "number"}
                        }
                    },
                    "improvements": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["category", "suggestion"],
                            "properties": {
                                "category": {"type": "string"},
                                "suggestion": {"type": "string"},
                                "priority": {"type": "string"}
                            }
                        }
                    }
                }
            }
            
            # Generate system prompt for analysis
            system_prompt = """You are an expert code quality analyst who evaluates compilation results.
Analyze the provided code and compilation results to offer insights into code quality.
Focus on providing value through:
1. Objective analysis of compilation metrics
2. Specific insights about code structure and quality
3. Numerical scores for different aspects of the code
4. Actionable suggestions for improvements
5. Identification of patterns that might cause future issues

Return your response as JSON with these fields:
- summary: A concise summary of the overall code quality
- insights: An array of specific insights drawn from the compilation results
- metrics: An object with numerical scores (0-100) for code_quality_score, robustness_score, maintainability_score, and security_score
- improvements: An array of objects with 'category', 'suggestion', and 'priority' fields
"""
            
            # Call LLM to analyze compilation results
            conversation = {
                "code": code,
                "compilation_results": results_str
            }
            
            response = await self.process_with_validation(
                conversation=json.dumps(conversation),
                system_prompt_info=(system_prompt,),
                schema=schema,
                current_phase="compilation_analysis",
                operation_id=operation_id
            )
            
            # Update state to complete
            await self.set_agent_state(AgentState.COMPLETE)
            
            # Add operation id to the response
            response["operation_id"] = operation_id
            response["success"] = True
            
            logger.info(f"Compilation analysis completed for {operation_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error in compilation analysis: {str(e)}", exc_info=True)
            await self.set_agent_state(AgentState.ERROR)
            
            return {
                "operation_id": operation_id,
                "success": False,
                "error": f"Compilation analysis failed: {str(e)}"
            }

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

class PhaseFourInterface:
    """Interface for Phase Four operations"""
    
    def __init__(self, 
                 event_queue: EventQueue,
                 state_manager: StateManager,
                 context_manager: AgentContextManager,
                 cache_manager: CacheManager,
                 metrics_manager: MetricsManager,
                 error_handler: ErrorHandler,
                 memory_monitor: Optional[MemoryMonitor] = None,
                 system_monitor: Optional[SystemMonitor] = None):
        """Initialize the Phase Four interface."""
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
        """Process feature code generation and compilation."""
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
        
        Args:
            improvement_request: Dictionary containing:
                - id: Feature ID
                - name: Feature name
                - original_implementation: Original code to improve
                - improvements: List of improvement suggestions
                - rationale: Reason for improvement
                
        Returns:
            Dictionary with improvement results
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
            improvement_prompt = self._create_improvement_prompt(
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
    
    def _create_improvement_prompt(self, 
                                original_code: str, 
                                improvements: List[str], 
                                rationale: str) -> str:
        """Create a prompt for code improvement."""
        improvements_formatted = "\n".join([f"- {improvement}" for improvement in improvements])
        
        return f"""You are an expert software developer focusing on code improvement and refactoring.
Improve the provided code based on the specified improvement suggestions.
Focus on making precise, targeted changes that address each suggestion while preserving the code's functionality.

ORIGINAL CODE:
```python
{original_code}
```

IMPROVEMENT SUGGESTIONS:
{improvements_formatted}

IMPROVEMENT RATIONALE:
{rationale}

When improving the code, follow these guidelines:
1. Preserve the overall functionality and behavior of the code
2. Apply improvements that address each suggestion precisely
3. Follow best practices for Python development (PEP 8, type annotations, etc.)
4. Add or improve comments where needed for clarity
5. Ensure the code is robust with proper error handling
6. Document your changes clearly in the explanation

Return your response as JSON with these fields:
- improved_code: The improved version of the code
- explanation: An explanation of the changes made and their benefits
- improvements_applied: An array of objects, each with:
  - description: Description of a specific improvement applied
  - changes: Details of what was changed and why
"""