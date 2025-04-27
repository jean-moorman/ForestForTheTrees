"""
Refinement data structures for agent reflection and refinement.
"""
from dataclasses import dataclass
from typing import Dict, Any
from datetime import datetime

@dataclass
class RefinementContext:
    """Context for agent refinement iterations"""
    iteration: int
    agent_id: str
    original_output: Dict[str, Any]
    refined_output: Dict[str, Any]
    refinement_guidance: Dict[str, Any]
    timestamp: datetime = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "iteration": self.iteration,
            "agent_id": self.agent_id,
            "original_output": self.original_output,
            "refined_output": self.refined_output,
            "refinement_guidance": self.refinement_guidance,
            "timestamp": self.timestamp.isoformat()
        }

@dataclass
class AgentPromptConfig:
    """Configuration for agent prompt paths."""
    system_prompt_base_path: str
    reflection_prompt_name: str
    refinement_prompt_name: str
    initial_prompt_name: str