# Forest For The Trees (FFTT) Package Initialization

"""
Forest For The Trees (FFTT) - Nature-inspired LLM agent workflow system.

This package provides a modular architecture for automated software development
through sophisticated agent workflows organized in phases:
- Phase 0: Quality assurance and refinement
- Phase 1: Foundation guidelines and validation  
- Phase 2: Systematic component development
- Phase 3: Feature elaboration and evolutionary selection
- Phase 4: Code generation and static compilation

For optimal performance and test isolation, import specific components directly:
- from phase_one.agents.earth_agent import EarthAgent
- from phase_four.interface import PhaseFourInterface
- etc.
"""

# Lazy imports to avoid circular dependencies and improve test isolation
def _get_phase_four_interface():
    """Lazy import for PhaseFourInterface."""
    try:
        from phase_four import PhaseFourInterface
        return PhaseFourInterface
    except ImportError as e:
        raise ImportError(f"Phase Four not available: {e}")

def _get_phase_four_agents():
    """Lazy import for Phase Four agents."""
    try:
        from phase_four import (
            CodeGenerationAgent, StaticCompilationAgent, 
            CompilationDebugAgent, CompilationAnalysisAgent, 
            CompilationRefinementAgent
        )
        return {
            'CodeGenerationAgent': CodeGenerationAgent,
            'StaticCompilationAgent': StaticCompilationAgent,
            'CompilationDebugAgent': CompilationDebugAgent,
            'CompilationAnalysisAgent': CompilationAnalysisAgent,
            'CompilationRefinementAgent': CompilationRefinementAgent
        }
    except ImportError as e:
        raise ImportError(f"Phase Four agents not available: {e}")

# Only expose what's actually needed at package level
__all__ = []

# Dynamic attribute access for backward compatibility
def __getattr__(name: str):
    """Dynamic import handler for package-level access."""
    if name == 'PhaseFourInterface':
        return _get_phase_four_interface()
    elif name in ['CodeGenerationAgent', 'StaticCompilationAgent', 
                  'CompilationDebugAgent', 'CompilationAnalysisAgent', 
                  'CompilationRefinementAgent']:
        agents = _get_phase_four_agents()
        return agents[name]
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")