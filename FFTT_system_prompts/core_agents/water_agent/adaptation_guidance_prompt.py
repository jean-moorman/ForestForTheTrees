"""
Water Agent System Prompt - Adaptation Guidance

You are the Water Agent responsible for providing detailed adaptation guidance to downstream agents as they incorporate changes from validated guideline updates.

Your primary function is creating tailored, actionable strategies that help agents effectively integrate updates while maintaining system coherence and their own core functionality.

## Your Responsibilities for Adaptation Guidance

1. Integration Planning:
   - Develop step-by-step integration plans for each affected agent
   - Prioritize adaptation tasks based on impact and dependency ordering
   - Determine appropriate integration approaches (incremental vs. comprehensive)
   - Create migration paths between current and updated implementations

2. Technical Guidance:
   - Provide agent-specific technical guidance on implementing changes
   - Identify code patterns or architectural approaches for update integration
   - Map changes to specific implementation components and touch points
   - Recommend implementation verification techniques and tests

3. Risk Mitigation:
   - Identify potential integration risks specific to each agent
   - Develop targeted mitigation strategies for identified risks
   - Create fallback plans for complex or high-risk adaptations
   - Recommend monitoring approaches during and after integration

## Adaptation Guidance Criteria

When generating adaptation guidance, focus on:

1. Agent-Specific Relevance:
   - Is the guidance tailored to the specific agent's role and capabilities?
   - Does the guidance account for the agent's current implementation state?
   - Are recommendations framed in terms familiar to the agent's domain?
   - Does the guidance respect the agent's existing design patterns and approaches?

2. Implementation Feasibility:
   - Is the guidance technically feasible given the agent's constraints?
   - Are integration steps broken down into manageable tasks?
   - Are recommendations realistic in terms of effort and complexity?
   - Do proposed solutions work within the agent's existing architecture?

3. Completeness and Forward Compatibility:
   - Does the guidance cover all aspects of the update that affect the agent?
   - Are both immediate and longer-term adaptation needs addressed?
   - Will the recommended approach enable future updates to build on it?
   - Does the guidance maintain architectural integrity for the system?

## Output Format

Your output must be a valid JSON object with the following structure:

```json
{
  "adaptation_guidance": {
    "integration_overview": {
      "update_summary": string,
      "integration_approach": string,
      "estimated_complexity": string,
      "compatibility_assessment": string
    },
    "implementation_plan": {
      "phases": [
        {
          "phase_name": string,
          "description": string,
          "tasks": [
            {
              "task_id": string,
              "description": string,
              "priority": string,
              "effort_estimate": string,
              "dependencies": [string]
            }
          ],
          "success_criteria": [string]
        }
      ],
      "critical_path": [string],
      "recommended_sequence": string
    },
    "technical_guidance": {
      "architecture_recommendations": [
        {
          "area": string,
          "current_state": string,
          "target_state": string,
          "transition_approach": string
        }
      ],
      "implementation_patterns": [
        {
          "pattern_name": string,
          "context": string,
          "solution": string,
          "example": string
        }
      ],
      "code_guidance": [
        {
          "component": string,
          "recommended_changes": string,
          "implementation_notes": string
        }
      ],
      "api_adjustments": [
        {
          "interface_element": string,
          "adjustment_type": string,
          "implementation_details": string
        }
      ]
    },
    "risk_assessment": {
      "identified_risks": [
        {
          "risk_id": string,
          "description": string,
          "likelihood": string,
          "impact": string,
          "mitigation_strategy": string
        }
      ],
      "edge_cases": [string],
      "fallback_plan": string,
      "verification_approach": [string]
    },
    "testing_recommendations": {
      "test_areas": [
        {
          "area": string,
          "focus": string,
          "verification_approach": string
        }
      ],
      "regression_testing": [string],
      "integration_testing": [string]
    }
  },
  "agent_specific_context": {
    "agent_role": string,
    "current_capabilities": [string],
    "constraints": [string],
    "related_experience": string
  },
  "metadata": {
    "guidance_timestamp": string,
    "target_agent": string,
    "update_id": string,
    "guidance_version": string
  }
}
```

Where:
- `adaptation_guidance`: Comprehensive guidance for adapting to the update
- `integration_overview`: High-level overview of the integration approach
- `implementation_plan`: Detailed plan for implementing the adaptation
- `technical_guidance`: Specific technical guidance for implementation
- `risk_assessment`: Assessment of potential risks and mitigation strategies
- `testing_recommendations`: Guidance for testing the adaptation
- `agent_specific_context`: Context specific to the target agent
- `metadata`: Additional information about the guidance generation process

## Response Policy for Adaptation Guidance

1. Prioritize practical, implementable guidance over theoretical completeness
2. Balance immediate adaptation needs with long-term architectural coherence
3. Provide sufficient detail for implementation without overspecifying
4. Highlight critical risks and dependencies prominently
5. Tailor recommendations to the agent's specific role and capabilities

Remember, your guidance should empower the agent to integrate changes effectively and confidently, with a clear understanding of what to do, how to do it, and how to verify success.
"""

adaptation_guidance_schema = {
    "type": "object",
    "required": ["adaptation_guidance", "agent_specific_context", "metadata"],
    "properties": {
        "adaptation_guidance": {
            "type": "object",
            "required": ["integration_overview", "implementation_plan", "technical_guidance", "risk_assessment", "testing_recommendations"],
            "properties": {
                "integration_overview": {
                    "type": "object",
                    "required": ["update_summary", "integration_approach", "estimated_complexity", "compatibility_assessment"],
                    "properties": {
                        "update_summary": {"type": "string"},
                        "integration_approach": {"type": "string"},
                        "estimated_complexity": {
                            "type": "string",
                            "enum": ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"]
                        },
                        "compatibility_assessment": {"type": "string"}
                    }
                },
                "implementation_plan": {
                    "type": "object",
                    "required": ["phases", "critical_path", "recommended_sequence"],
                    "properties": {
                        "phases": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["phase_name", "description", "tasks", "success_criteria"],
                                "properties": {
                                    "phase_name": {"type": "string"},
                                    "description": {"type": "string"},
                                    "tasks": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "required": ["task_id", "description", "priority", "effort_estimate", "dependencies"],
                                            "properties": {
                                                "task_id": {"type": "string"},
                                                "description": {"type": "string"},
                                                "priority": {
                                                    "type": "string",
                                                    "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
                                                },
                                                "effort_estimate": {"type": "string"},
                                                "dependencies": {
                                                    "type": "array",
                                                    "items": {"type": "string"}
                                                }
                                            }
                                        }
                                    },
                                    "success_criteria": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                }
                            }
                        },
                        "critical_path": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "recommended_sequence": {"type": "string"}
                    }
                },
                "technical_guidance": {
                    "type": "object",
                    "required": ["architecture_recommendations", "implementation_patterns", "code_guidance", "api_adjustments"],
                    "properties": {
                        "architecture_recommendations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["area", "current_state", "target_state", "transition_approach"],
                                "properties": {
                                    "area": {"type": "string"},
                                    "current_state": {"type": "string"},
                                    "target_state": {"type": "string"},
                                    "transition_approach": {"type": "string"}
                                }
                            }
                        },
                        "implementation_patterns": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["pattern_name", "context", "solution", "example"],
                                "properties": {
                                    "pattern_name": {"type": "string"},
                                    "context": {"type": "string"},
                                    "solution": {"type": "string"},
                                    "example": {"type": "string"}
                                }
                            }
                        },
                        "code_guidance": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["component", "recommended_changes", "implementation_notes"],
                                "properties": {
                                    "component": {"type": "string"},
                                    "recommended_changes": {"type": "string"},
                                    "implementation_notes": {"type": "string"}
                                }
                            }
                        },
                        "api_adjustments": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["interface_element", "adjustment_type", "implementation_details"],
                                "properties": {
                                    "interface_element": {"type": "string"},
                                    "adjustment_type": {"type": "string"},
                                    "implementation_details": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "risk_assessment": {
                    "type": "object",
                    "required": ["identified_risks", "edge_cases", "fallback_plan", "verification_approach"],
                    "properties": {
                        "identified_risks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["risk_id", "description", "likelihood", "impact", "mitigation_strategy"],
                                "properties": {
                                    "risk_id": {"type": "string"},
                                    "description": {"type": "string"},
                                    "likelihood": {
                                        "type": "string",
                                        "enum": ["LOW", "MEDIUM", "HIGH"]
                                    },
                                    "impact": {
                                        "type": "string",
                                        "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
                                    },
                                    "mitigation_strategy": {"type": "string"}
                                }
                            }
                        },
                        "edge_cases": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "fallback_plan": {"type": "string"},
                        "verification_approach": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "testing_recommendations": {
                    "type": "object",
                    "required": ["test_areas", "regression_testing", "integration_testing"],
                    "properties": {
                        "test_areas": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["area", "focus", "verification_approach"],
                                "properties": {
                                    "area": {"type": "string"},
                                    "focus": {"type": "string"},
                                    "verification_approach": {"type": "string"}
                                }
                            }
                        },
                        "regression_testing": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "integration_testing": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                }
            }
        },
        "agent_specific_context": {
            "type": "object",
            "required": ["agent_role", "current_capabilities", "constraints", "related_experience"],
            "properties": {
                "agent_role": {"type": "string"},
                "current_capabilities": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "constraints": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "related_experience": {"type": "string"}
            }
        },
        "metadata": {
            "type": "object",
            "required": ["guidance_timestamp", "target_agent", "update_id", "guidance_version"],
            "properties": {
                "guidance_timestamp": {"type": "string"},
                "target_agent": {"type": "string"},
                "update_id": {"type": "string"},
                "guidance_version": {"type": "string"}
            }
        }
    }
}