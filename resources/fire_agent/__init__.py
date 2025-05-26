"""
Fire Agent: System-Wide Complexity Detection and Reduction

The Fire Agent serves as a system resource agent that detects complexity accumulation
across all phases and provides decomposition strategies for overly complex guidelines,
features, and components.

Core responsibilities:
1. Complexity detection across phases (guidelines, features, components)
2. Decomposition recommendations and execution
3. System-wide complexity monitoring
4. Integration with key decision points in workflows

Usage:
    from resources.fire_agent import (
        analyze_guideline_complexity,
        analyze_feature_complexity,
        decompose_complex_feature,
        decompose_complex_guideline
    )
"""

from .complexity_detector import (
    analyze_guideline_complexity,
    analyze_feature_complexity,
    analyze_component_complexity,
    detect_system_complexity_hotspots
)

from .decomposer import (
    decompose_complex_guideline,
    decompose_complex_feature,
    simplify_component_architecture
)

from .metrics import (
    calculate_complexity_score,
    identify_complexity_causes,
    assess_decomposition_impact
)

from .models import (
    ComplexityAnalysis,
    DecompositionResult,
    ComplexityCause,
    ComplexityThreshold
)

__all__ = [
    # Main analysis functions
    'analyze_guideline_complexity',
    'analyze_feature_complexity', 
    'analyze_component_complexity',
    'detect_system_complexity_hotspots',
    
    # Decomposition functions
    'decompose_complex_guideline',
    'decompose_complex_feature',
    'simplify_component_architecture',
    
    # Metrics and assessment
    'calculate_complexity_score',
    'identify_complexity_causes',
    'assess_decomposition_impact',
    
    # Data models
    'ComplexityAnalysis',
    'DecompositionResult',
    'ComplexityCause',
    'ComplexityThreshold'
]