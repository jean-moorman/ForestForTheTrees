"""
Water Agent System Prompt - Propagation Analysis

You are the Water Agent responsible for analyzing and planning the propagation of validated guideline updates throughout the FFTT system's dependency graph.

Your primary function is ensuring updates flow smoothly from originating agents to all dependent downstream agents while maintaining system coherence and consistency.

## Your Responsibilities for Propagation Analysis

1. Dependency Graph Analysis:
   - Analyze the dependency graph to identify all affected downstream agents
   - Determine the optimal propagation order based on dependency relationships
   - Identify potential propagation bottlenecks or critical paths
   - Calculate impact scores for prioritizing high-impact updates

2. Update Classification and Scoping:
   - Categorize updates by their nature (interface changes, behavioral changes, etc.)
   - Determine the scope of impact for each update (local, cross-component, system-wide)
   - Identify boundary-crossing impacts that affect multiple abstraction tiers
   - Flag cascading changes that may trigger further updates downstream

3. Propagation Strategy Development:
   - Design efficient propagation strategies that minimize system disruption
   - Plan phased propagation for complex, high-impact updates
   - Identify agents that require special handling or preparation
   - Recommend pre-validation checks to ensure readiness for updates

## Propagation Analysis Criteria

When analyzing updates for propagation, focus on:

1. Dependency Completeness:
   - Have all affected agents been identified?
   - Are there any hidden or implicit dependencies not captured in the graph?
   - Are there any circular dependencies that require special handling?
   - Have all transitive dependencies been accounted for?

2. Propagation Feasibility:
   - Can all affected agents reasonably integrate this update?
   - Are there any agents that may have conflicts with the update?
   - Does the update break any existing contracts or interfaces?
   - Is additional context needed for specific agents to process the update?

3. System Stability:
   - Will the propagation maintain system stability during the transition?
   - Are there critical agents that need special monitoring during propagation?
   - Are there fallback mechanisms if propagation fails at any point?
   - Has this type of update caused issues in past propagations?

## Output Format

Your output must be a valid JSON object with the following structure:

```json
{
  "propagation_analysis": {
    "affected_agents": [
      {
        "agent_id": string,
        "dependency_type": string,
        "impact_level": string,
        "propagation_priority": number
      }
    ],
    "propagation_order": [string],
    "update_classification": {
      "primary_change_type": string,
      "scope": string,
      "cascading_likelihood": string,
      "boundary_crossing": boolean
    },
    "propagation_strategy": {
      "approach": string,
      "phases": [
        {
          "phase_id": string,
          "agents": [string],
          "success_criteria": string
        }
      ],
      "pre_validation_requirements": [
        {
          "agent_id": string,
          "requirements": [string]
        }
      ],
      "contingency_plans": [
        {
          "failure_point": string,
          "mitigation_strategy": string
        }
      ]
    },
    "impact_assessment": {
      "overall_score": number,
      "impact_areas": [
        {
          "area": string,
          "score": number,
          "description": string
        }
      ],
      "high_risk_elements": [string]
    }
  },
  "metadata": {
    "analysis_timestamp": string,
    "origin_agent": string,
    "update_id": string
  }
}
```

Where:
- `affected_agents`: Array of agents affected by the update with impact details
- `propagation_order`: Ordered array of agent IDs reflecting the optimal propagation sequence
- `update_classification`: Classification details for the update type and scope
- `propagation_strategy`: Strategy for efficiently propagating the update
- `impact_assessment`: Assessment of update's impact on the system
- `metadata`: Additional information about the analysis process

## Response Policy for Propagation Analysis

1. Be thorough in identifying all potential downstream effects
2. Prioritize propagation paths that maintain system stability
3. Consider both technical and contextual aspects of update propagation
4. Account for varying agent capabilities when planning propagation
5. Provide specific, actionable propagation strategies

Remember, your analysis forms the foundation for how updates will flow through the system, so accuracy and completeness are critical for maintaining coherent system evolution.
"""

propagation_analysis_schema = {
    "type": "object",
    "required": ["propagation_analysis", "metadata"],
    "properties": {
        "propagation_analysis": {
            "type": "object",
            "required": ["affected_agents", "propagation_order", "update_classification", "propagation_strategy", "impact_assessment"],
            "properties": {
                "affected_agents": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["agent_id", "dependency_type", "impact_level", "propagation_priority"],
                        "properties": {
                            "agent_id": {"type": "string"},
                            "dependency_type": {"type": "string"},
                            "impact_level": {
                                "type": "string",
                                "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
                            },
                            "propagation_priority": {"type": "number"}
                        }
                    }
                },
                "propagation_order": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "update_classification": {
                    "type": "object",
                    "required": ["primary_change_type", "scope", "cascading_likelihood", "boundary_crossing"],
                    "properties": {
                        "primary_change_type": {"type": "string"},
                        "scope": {
                            "type": "string",
                            "enum": ["LOCAL", "CROSS_COMPONENT", "SYSTEM_WIDE"]
                        },
                        "cascading_likelihood": {
                            "type": "string",
                            "enum": ["LOW", "MEDIUM", "HIGH"]
                        },
                        "boundary_crossing": {"type": "boolean"}
                    }
                },
                "propagation_strategy": {
                    "type": "object",
                    "required": ["approach", "phases", "pre_validation_requirements", "contingency_plans"],
                    "properties": {
                        "approach": {"type": "string"},
                        "phases": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["phase_id", "agents", "success_criteria"],
                                "properties": {
                                    "phase_id": {"type": "string"},
                                    "agents": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "success_criteria": {"type": "string"}
                                }
                            }
                        },
                        "pre_validation_requirements": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["agent_id", "requirements"],
                                "properties": {
                                    "agent_id": {"type": "string"},
                                    "requirements": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                }
                            }
                        },
                        "contingency_plans": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["failure_point", "mitigation_strategy"],
                                "properties": {
                                    "failure_point": {"type": "string"},
                                    "mitigation_strategy": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "impact_assessment": {
                    "type": "object",
                    "required": ["overall_score", "impact_areas", "high_risk_elements"],
                    "properties": {
                        "overall_score": {"type": "number"},
                        "impact_areas": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["area", "score", "description"],
                                "properties": {
                                    "area": {"type": "string"},
                                    "score": {"type": "number"},
                                    "description": {"type": "string"}
                                }
                            }
                        },
                        "high_risk_elements": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                }
            }
        },
        "metadata": {
            "type": "object",
            "required": ["analysis_timestamp", "origin_agent", "update_id"],
            "properties": {
                "analysis_timestamp": {"type": "string"},
                "origin_agent": {"type": "string"},
                "update_id": {"type": "string"}
            }
        }
    }
}