"""
Water Agent system prompts for agent coordination.

This module provides the system prompts used by the Water Agent to detect and
resolve misunderstandings between sequential agents in the FFTT system.
"""
from .misunderstanding_detection_prompt import MISUNDERSTANDING_DETECTION_PROMPT
from .resolution_assessment_prompt import RESOLUTION_ASSESSMENT_PROMPT
from .context_refinement_prompt import CONTEXT_REFINEMENT_PROMPT
from .reflection_prompt import WATER_AGENT_REFLECTION_PROMPT
from .revision_prompt import WATER_AGENT_REVISION_PROMPT

__all__ = [
    'MISUNDERSTANDING_DETECTION_PROMPT',
    'RESOLUTION_ASSESSMENT_PROMPT', 
    'CONTEXT_REFINEMENT_PROMPT',
    'WATER_AGENT_REFLECTION_PROMPT',
    'WATER_AGENT_REVISION_PROMPT'
]