from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Set

from phase_three.models.enums import FeatureDevelopmentState
from phase_three.models.scores import FeaturePerformanceScore

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