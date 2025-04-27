from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict

from phase_three.models.enums import FeaturePerformanceMetrics

@dataclass
class FeaturePerformanceScore:
    """Performance score for a feature"""
    feature_id: str
    scores: Dict[FeaturePerformanceMetrics, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def get_overall_score(self) -> float:
        """Get the overall performance score"""
        if not self.scores:
            return 0.0
        return sum(self.scores.values()) / len(self.scores)