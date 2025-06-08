"""Phase Four Package - Code implementation with static compilation.

Phase Four is responsible for generating, refining, and improving feature code
within the FFTT system. It handles the transformation of feature requirements into
high-quality, production-ready code through a multi-step process:

1. Code Generation: Feature requirements are transformed into initial code
2. Static Compilation: The code is checked using multiple static analysis tools
3. Code Refinement: Issues are identified and fixed through iterative improvement
4. Code Analysis: Final code is analyzed for quality metrics and improvement suggestions

The static compilation process involves multiple layers of checks:
- Formatting (Black): Ensures consistent code formatting
- Style (Flake8): Checks adherence to style guidelines
- Linting (Pylint): Performs deep logical analysis and code quality checks
- Type Checking (MyPy): Verifies type annotations and type safety
- Security (Bandit): Scans for security vulnerabilities

This package provides a clean, modular structure with separate components for
each aspect of the code generation and refinement process.
"""

from .models import (
    CompilerType, 
    CompilationState, 
    CompilationResult, 
    CompilationContext
)
from .agents import (
    CodeGenerationAgent,
    StaticCompilationAgent,
    CompilationDebugAgent,
    CompilationAnalysisAgent,
    CompilationRefinementAgent
)
from .interface import PhaseFourInterface

__all__ = [
    # Models
    'CompilerType',
    'CompilationState',
    'CompilationResult',
    'CompilationContext',
    
    # Agents
    'CodeGenerationAgent',
    'StaticCompilationAgent',
    'CompilationDebugAgent',
    'CompilationAnalysisAgent',
    'CompilationRefinementAgent',
    
    # Interface
    'PhaseFourInterface'
]