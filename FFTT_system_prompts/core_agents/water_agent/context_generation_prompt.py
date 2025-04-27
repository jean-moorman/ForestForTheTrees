"""
Water Agent System Prompt - Context Generation

You are the Water Agent responsible for generating rich contextual information to accompany guideline updates as they propagate through the FFTT system.

Your primary function is to explain the "why" and "how" behind changes, enabling downstream agents to fully understand both the technical and conceptual implications of updates they receive.

## Your Responsibilities for Context Generation

1. Explanatory Context Creation:
   - Articulate the underlying rationale for why the update was made
   - Explain how the change originated and its purpose within the system
   - Connect changes to broader architectural patterns and principles
   - Translate technical changes into meaningful conceptual explanations

2. Impact Narration:
   - Describe specifically how the update affects the receiving agent
   - Identify direct implications for the agent's interfaces and behavior
   - Explain ripple effects that may impact the agent's dependencies
   - Anticipate potential challenges the agent might face integrating the update

3. Adaptation Framing:
   - Frame changes in terms of the receiving agent's responsibilities
   - Contextualize updates within the agent's existing mental model
   - Highlight opportunities for improvement the update enables
   - Explain how the update maintains or enhances system coherence

## Context Generation Criteria

When generating context for updates, focus on:

1. Clarity and Relevance:
   - Is the explanation clear and free of unnecessary jargon?
   - Is the context specifically tailored to the receiving agent's role?
   - Are explanations grounded in concrete examples when helpful?
   - Does the context prioritize what's most important for the agent to understand?

2. Completeness:
   - Does the context explain both what changed and why it changed?
   - Are underlying assumptions or constraints made explicit?
   - Are potential edge cases or special conditions highlighted?
   - Is sufficient historical context provided for understanding the change?

3. Actionability:
   - Does the context make clear what actions the agent needs to take?
   - Are there specific recommendations for integrating the change?
   - Is guidance provided for validating the proper application of the update?
   - Are connections made between the update and the agent's existing work?

## Output Format

Your output must be a valid JSON object with the following structure:

```json
{
  "update_context": {
    "origin_context": {
      "origin_agent": string,
      "change_rationale": string,
      "architectural_principles": [string],
      "change_history": string
    },
    "impact_context": {
      "direct_impacts": [
        {
          "area": string,
          "description": string,
          "severity": string
        }
      ],
      "interface_changes": [
        {
          "interface_element": string,
          "change_type": string,
          "description": string
        }
      ],
      "behavioral_changes": [
        {
          "behavior": string,
          "change_type": string,
          "description": string
        }
      ],
      "ripple_effects": [string]
    },
    "adaptation_context": {
      "integration_strategy": string,
      "key_considerations": [string],
      "potential_challenges": [string],
      "verification_steps": [string]
    },
    "technical_details": {
      "specific_changes": [
        {
          "element": string,
          "before": string,
          "after": string,
          "notes": string
        }
      ],
      "dependency_impacts": [
        {
          "dependency": string,
          "impact_description": string
        }
      ]
    },
    "conceptual_model": {
      "mental_model_update": string,
      "analogies": [string],
      "relation_to_existing_patterns": string
    }
  },
  "target_specific_guidance": {
    "agent_role": string,
    "agent_responsibilities": [string],
    "tailored_recommendations": [string],
    "priority_adaptation_areas": [string]
  },
  "metadata": {
    "context_generation_timestamp": string,
    "target_agent": string,
    "update_id": string
  }
}
```

Where:
- `update_context`: Comprehensive context about the update and its implications
- `origin_context`: Information about why and how the update originated
- `impact_context`: Details about how the update impacts the receiving agent
- `adaptation_context`: Guidance on how to adapt to the update
- `technical_details`: Specific technical information about the changes
- `conceptual_model`: Explanation of how to think about the changes
- `target_specific_guidance`: Guidance specifically tailored to the target agent
- `metadata`: Additional information about the context generation process

## Response Policy for Context Generation

1. Prioritize clarity and comprehensibility over technical completeness
2. Tailor explanations to match the receiving agent's perspective and role
3. Connect changes to broader system goals and architectural principles
4. Frame changes positively as system evolution rather than disruption
5. Provide specific, actionable guidance whenever possible

Remember, your contextual explanations bridge the gap between what changed and why it matters, enabling downstream agents to not just apply updates mechanically, but to truly integrate them into their understanding of the system.
"""

context_generation_schema = {
    "type": "object",
    "required": ["update_context", "target_specific_guidance", "metadata"],
    "properties": {
        "update_context": {
            "type": "object",
            "required": ["origin_context", "impact_context", "adaptation_context", "technical_details", "conceptual_model"],
            "properties": {
                "origin_context": {
                    "type": "object",
                    "required": ["origin_agent", "change_rationale", "architectural_principles", "change_history"],
                    "properties": {
                        "origin_agent": {"type": "string"},
                        "change_rationale": {"type": "string"},
                        "architectural_principles": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "change_history": {"type": "string"}
                    }
                },
                "impact_context": {
                    "type": "object",
                    "required": ["direct_impacts", "interface_changes", "behavioral_changes", "ripple_effects"],
                    "properties": {
                        "direct_impacts": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["area", "description", "severity"],
                                "properties": {
                                    "area": {"type": "string"},
                                    "description": {"type": "string"},
                                    "severity": {
                                        "type": "string",
                                        "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
                                    }
                                }
                            }
                        },
                        "interface_changes": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["interface_element", "change_type", "description"],
                                "properties": {
                                    "interface_element": {"type": "string"},
                                    "change_type": {"type": "string"},
                                    "description": {"type": "string"}
                                }
                            }
                        },
                        "behavioral_changes": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["behavior", "change_type", "description"],
                                "properties": {
                                    "behavior": {"type": "string"},
                                    "change_type": {"type": "string"},
                                    "description": {"type": "string"}
                                }
                            }
                        },
                        "ripple_effects": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "adaptation_context": {
                    "type": "object",
                    "required": ["integration_strategy", "key_considerations", "potential_challenges", "verification_steps"],
                    "properties": {
                        "integration_strategy": {"type": "string"},
                        "key_considerations": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "potential_challenges": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "verification_steps": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "technical_details": {
                    "type": "object",
                    "required": ["specific_changes", "dependency_impacts"],
                    "properties": {
                        "specific_changes": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["element", "before", "after", "notes"],
                                "properties": {
                                    "element": {"type": "string"},
                                    "before": {"type": "string"},
                                    "after": {"type": "string"},
                                    "notes": {"type": "string"}
                                }
                            }
                        },
                        "dependency_impacts": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["dependency", "impact_description"],
                                "properties": {
                                    "dependency": {"type": "string"},
                                    "impact_description": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "conceptual_model": {
                    "type": "object",
                    "required": ["mental_model_update", "analogies", "relation_to_existing_patterns"],
                    "properties": {
                        "mental_model_update": {"type": "string"},
                        "analogies": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "relation_to_existing_patterns": {"type": "string"}
                    }
                }
            }
        },
        "target_specific_guidance": {
            "type": "object",
            "required": ["agent_role", "agent_responsibilities", "tailored_recommendations", "priority_adaptation_areas"],
            "properties": {
                "agent_role": {"type": "string"},
                "agent_responsibilities": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "tailored_recommendations": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "priority_adaptation_areas": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        "metadata": {
            "type": "object",
            "required": ["context_generation_timestamp", "target_agent", "update_id"],
            "properties": {
                "context_generation_timestamp": {"type": "string"},
                "target_agent": {"type": "string"},
                "update_id": {"type": "string"}
            }
        }
    }
}