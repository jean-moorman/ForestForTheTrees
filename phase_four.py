"""Phase Four - Code implementation with static compilation."""

# This file now serves as a compatibility layer for existing code
# It re-exports all components from the phase_four package

from phase_four import (
    # Models
    CompilerType,
    CompilationState,
    CompilationResult,
    CompilationContext,
    
    # Agents
    CodeGenerationAgent,
    StaticCompilationAgent,
    CompilationDebugAgent,
    CompilationAnalysisAgent,
    CompilationRefinementAgent,
    
    # Interface
    PhaseFourInterface
)

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