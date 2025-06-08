# FFTT_system_prompts/phase_one/__init__.py

# Import the technical dependency validator prompts
from FFTT_system_prompts.phase_one.technical_dependency_validator import (
    technical_dependency_validation_prompt,
    technical_dependency_validation_schema,
    technical_validation_reflection_prompt,
    technical_validation_reflection_schema,
    technical_validation_revision_prompt,
    technical_validation_revision_schema
)

# Import the garden planner agent prompts
from FFTT_system_prompts.phase_one.garden_planner_agent import (
    initial_task_elaboration_prompt,
    task_reflection_prompt,
    task_revision_prompt,
    task_elaboration_refinement_prompt
)

# Make garden_planner_agent available as an alias for initial_task_elaboration_prompt
garden_planner_agent = initial_task_elaboration_prompt

# Import the garden foundation refinement agent prompts (original end-of-phase prompts)
from FFTT_system_prompts.phase_one.garden_foundation_refinement_agent import (
    task_foundation_refinement_prompt,
    task_foundation_refinement_schema,
    task_foundation_reflection_prompt,
    task_foundation_reflection_schema,
    task_foundation_revision_prompt,
    task_foundation_revision_schema
)

# Make all prompts available at the package level
__all__ = [
    # Garden planner agent prompts
    'garden_planner_agent',
    'initial_task_elaboration_prompt',
    'task_reflection_prompt',
    'task_revision_prompt',
    'task_elaboration_refinement_prompt',
    
    # Technical dependency validation prompts
    'technical_dependency_validation_prompt',
    'technical_dependency_validation_schema',
    'technical_validation_reflection_prompt',
    'technical_validation_reflection_schema',
    'technical_validation_revision_prompt',
    'technical_validation_revision_schema',
    
    # Garden foundation refinement prompts
    'task_foundation_refinement_prompt',
    'task_foundation_refinement_schema',
    'task_foundation_reflection_prompt',
    'task_foundation_reflection_schema',
    'task_foundation_revision_prompt',
    'task_foundation_revision_schema'
]