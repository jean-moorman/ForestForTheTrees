"""
Earth Agent prompt system for validating guidelines.

This package contains the prompts used by the Earth Agent for validating
the outputs of other agents, specifically in Phase One for validating
the Garden Planner agent outputs.
"""

from FFTT_system_prompts.core_agents.earth_agent.garden_planner_validation_prompt import garden_planner_validation_prompt, garden_planner_validation_schema
from FFTT_system_prompts.core_agents.earth_agent.reflection_prompt import reflection_prompt, reflection_schema
from FFTT_system_prompts.core_agents.earth_agent.revision_prompt import revision_prompt, revision_schema

__all__ = [
    'garden_planner_validation_prompt',
    'garden_planner_validation_schema',
    'reflection_prompt',
    'reflection_schema',
    'revision_prompt',
    'revision_schema'
]