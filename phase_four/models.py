"""Data models for Phase Four compilation and code generation processes.

This module contains the core data structures used throughout the Phase Four 
package, including enums for compiler types and states, as well as data classes
for compilation results and context tracking.
"""

import time
from typing import Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum, auto


class CompilerType(Enum):
    """Types of static compilation checks.
    
    This enum defines the different types of static analysis tools used in the
    compilation process. Each type represents a specific aspect of code quality
    that is checked during the compilation pipeline.
    
    Attributes:
        FORMAT: Code formatting checks using Black formatter
        STYLE: Style guide compliance checks using Flake8
        LINT: Deep logical analysis and code quality checks using Pylint
        TYPE: Type checking using MyPy
        SECURITY: Security vulnerability scanning using Bandit
    """
    FORMAT = auto()  # Black code formatter
    STYLE = auto()   # Flake8 style checks
    LINT = auto()    # Pylint deep logical analysis
    TYPE = auto()    # MyPy type checking
    SECURITY = auto() # Bandit security checks


class CompilationState(Enum):
    """States for the compilation process.
    
    This enum defines the possible states of a compilation step, tracking
    its progress through the compilation pipeline.
    
    Attributes:
        PENDING: The compilation step is waiting to be executed
        RUNNING: The compilation step is currently executing
        FAILED: The compilation step has failed due to code issues
        SUCCEEDED: The compilation step has completed successfully
        ERROR: The compilation step encountered an error during execution
    """
    PENDING = auto()
    RUNNING = auto()
    FAILED = auto()
    SUCCEEDED = auto()
    ERROR = auto()


@dataclass
class CompilationResult:
    """Result of a compilation step.
    
    This class stores the results of a specific compilation step, including
    success/failure status, output messages, and structured issues for analysis.
    
    Attributes:
        compiler_type: The type of compiler that produced this result
        state: The current state of the compilation step
        success: Whether the compilation step was successful
        output: The standard output of the compilation tool
        error_message: The standard error output of the compilation tool
        execution_time: The time taken to execute the compilation step (in seconds)
        issues: A list of structured issues found during compilation
    """
    compiler_type: CompilerType
    state: CompilationState = CompilationState.PENDING
    success: bool = False
    output: str = ""
    error_message: str = ""
    execution_time: float = 0.0
    issues: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CompilationContext:
    """Context for a compilation process.
    
    This class maintains the state and context for a complete compilation
    process across multiple steps and iterations. It tracks the code being
    compiled, the results of each step, and the current progress.
    
    Attributes:
        feature_code: The source code being compiled
        feature_id: A unique identifier for the feature being compiled
        source_file_path: The path to the temporary file containing the code
        results: A dictionary mapping compiler types to their results
        current_stage: The current compilation stage being executed
        max_iterations: The maximum number of refinement iterations allowed
        current_iteration: The current refinement iteration
        start_time: The time when the compilation process started
    """
    feature_code: str
    feature_id: str
    source_file_path: str
    results: Dict[CompilerType, CompilationResult] = field(default_factory=dict)
    current_stage: CompilerType = CompilerType.FORMAT
    max_iterations: int = 5
    current_iteration: int = 0
    start_time: float = field(default_factory=time.time)