# Earth Agent system prompts for different abstraction tiers
# Used for validating potential updates to foundational guidelines

# Import schema definitions for all tiers
from .component_tier_prompt import component_tier_schema
from .feature_tier_prompt import feature_tier_schema
from .functionality_tier_prompt import functionality_tier_schema

# Export the schemas for use by the Earth agent
__all__ = [
    'component_tier_schema',
    'feature_tier_schema',
    'functionality_tier_schema'
]