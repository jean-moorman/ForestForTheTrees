"""
Feedback data structures for processing monitoring, analysis and evolution results.
"""
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

@dataclass
class MonitoringFeedback:
    """Structure to process monitoring feedback from Phase Zero"""
    flag_raised: bool = False
    flag_type: Optional[str] = None
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MonitoringFeedback':
        """Create from monitoring result dictionary"""
        return cls(
            flag_raised=data.get('flag_raised', False),
            flag_type=data.get('flag_type'),
            recommendations=data.get('recommendations', []),
            timestamp=datetime.now()
        )

@dataclass
class AnalysisFeedback:
    """Structure to process deep analysis feedback from Phase Zero"""
    sun_analysis: Dict[str, Any] = field(default_factory=dict)  # Initial description issues
    shade_analysis: Dict[str, Any] = field(default_factory=dict)  # Initial description gaps
    soil_analysis: Dict[str, Any] = field(default_factory=dict)  # Requirement issues
    microbial_analysis: Dict[str, Any] = field(default_factory=dict)  # Requirement conflicts
    root_system_analysis: Dict[str, Any] = field(default_factory=dict)  # Data flow issues
    mycelial_analysis: Dict[str, Any] = field(default_factory=dict)  # Data flow conflicts
    insect_analysis: Dict[str, Any] = field(default_factory=dict)  # Structural component issues
    bird_analysis: Dict[str, Any] = field(default_factory=dict)  # Structural component conflicts
    pollinator_analysis: Dict[str, Any] = field(default_factory=dict)  # Optimization opportunities
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisFeedback':
        """Create from deep analysis dictionary"""
        return cls(
            sun_analysis=data.get('sun', {}),  # Initial description issues
            shade_analysis=data.get('shade', {}),  # Initial description gaps
            soil_analysis=data.get('soil', {}),  # Requirement issues
            microbial_analysis=data.get('microbial', {}),  # Requirement conflicts
            root_system_analysis=data.get('root_system', {}),  # Data flow issues
            mycelial_analysis=data.get('mycelial', {}),  # Data flow conflicts
            insect_analysis=data.get('insect', {}),  # Structural component issues
            bird_analysis=data.get('bird', {}),  # Structural component conflicts
            pollinator_analysis=data.get('pollinator', {})  # Optimization opportunities
        )
    
    def get_critical_gaps(self) -> List[Dict[str, Any]]:
        """Extract all critical gaps from analysis feedback"""
        gaps = []
        
        # Extract issues from sun analysis (initial description)
        if 'critical_description_issues' in self.sun_analysis:
            for category, items in self.sun_analysis['critical_description_issues'].items():
                for item in items:
                    gaps.append({
                        'source': 'sun',
                        'category': category,
                        'details': item
                    })
        
        # Extract gaps from shade analysis (initial description)
        if 'critical_description_gaps' in self.shade_analysis:
            for category, items in self.shade_analysis['critical_description_gaps'].items():
                for item in items:
                    gaps.append({
                        'source': 'shade',
                        'category': category,
                        'details': item
                    })
        
        # Extract gaps from soil analysis (requirements)
        if 'critical_requirement_gaps' in self.soil_analysis:
            for category, items in self.soil_analysis['critical_requirement_gaps'].items():
                for item in items:
                    gaps.append({
                        'source': 'soil',
                        'category': category,
                        'details': item
                    })
        
        # Extract gaps from root system analysis (data flow)
        if 'critical_data_flow_gaps' in self.root_system_analysis:
            for category, items in self.root_system_analysis['critical_data_flow_gaps'].items():
                for item in items:
                    gaps.append({
                        'source': 'root_system',
                        'category': category,
                        'details': item
                    })
                    
        # Extract gaps from insect analysis (structural components)
        if 'critical_structure_gaps' in self.insect_analysis:
            for category, items in self.insect_analysis['critical_structure_gaps'].items():
                for item in items:
                    gaps.append({
                        'source': 'insect',
                        'category': category,
                        'details': item
                    })
        
        return gaps
    
    def get_critical_conflicts(self) -> List[Dict[str, Any]]:
        """Extract all critical conflicts from analysis feedback"""
        conflicts = []
        
        # Process for each relevant agent
        # Note: Sun and Shade analyses are handling description issues/gaps in get_critical_gaps method
        for source, data in [
            ('microbial', self.microbial_analysis),  # Requirement conflicts
            ('mycelial', self.mycelial_analysis),    # Data flow conflicts
            ('bird', self.bird_analysis)             # Structural component conflicts
        ]:
            if 'critical_guideline_conflicts' in data:
                for category, items in data['critical_guideline_conflicts'].items():
                    for item in items:
                        conflicts.append({
                            'source': source,
                            'category': category,
                            'details': item
                        })
        
        return conflicts
    
    def get_optimization_opportunities(self) -> List[Dict[str, Any]]:
        """Extract optimization opportunities from pollinator analysis"""
        opportunities = []
        
        if 'component_optimization_opportunities' in self.pollinator_analysis:
            for category, items in self.pollinator_analysis['component_optimization_opportunities'].items():
                for item in items:
                    opportunities.append({
                        'source': 'pollinator',
                        'category': category,
                        'details': item
                    })
        
        return opportunities

@dataclass
class EvolutionFeedback:
    """Structure to process evolution synthesis feedback from Phase Zero"""
    key_patterns: List[Dict[str, Any]] = field(default_factory=list)
    adaptations: List[Dict[str, Any]] = field(default_factory=list)
    priorities: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvolutionFeedback':
        """Create from evolution synthesis dictionary"""
        strategic_adaptations = data.get('strategic_adaptations', {})
        return cls(
            key_patterns=strategic_adaptations.get('key_patterns', []),
            adaptations=strategic_adaptations.get('adaptations', []),
            priorities=strategic_adaptations.get('priorities', {})
        )