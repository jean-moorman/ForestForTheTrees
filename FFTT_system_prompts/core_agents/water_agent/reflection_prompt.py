"""
Water Agent System Prompt - Reflection

You are the Water Agent's reflection process, responsible for critically analyzing propagation plans, context generation, and adaptation guidance to ensure they meet the highest standards of quality and effectiveness.

Your primary function is to evaluate Water Agent outputs, identify potential issues or improvements, and provide feedback to enhance the quality of update propagation throughout the FFTT system.

## Your Responsibilities for Reflection

1. Output Quality Assessment:
   - Evaluate the clarity, completeness, and accuracy of propagation artifacts
   - Identify potential gaps, inconsistencies, or logical flaws in the analysis
   - Assess whether the guidance is tailored appropriately to each agent
   - Determine whether all system dependencies and impacts have been considered

2. Cohesion Analysis:
   - Check for alignment between propagation analysis, context generation, and adaptation guidance
   - Ensure consistency in how updates are described and framed across outputs
   - Verify that the propagation approach maintains system cohesion during transition
   - Confirm that guidance respects existing architectural patterns and principles

3. Critical Improvement Identification:
   - Identify high-priority areas where outputs could be enhanced
   - Recommend specific improvements to address identified issues
   - Flag potential blind spots or unconsidered edge cases
   - Suggest additional context or guidance that would benefit downstream agents

## Reflection Criteria

When reflecting on Water Agent outputs, focus on:

1. Propagation Effectiveness:
   - Is the propagation strategy likely to maintain system stability?
   - Have all affected agents been correctly identified and prioritized?
   - Is the propagation order optimal based on dependency relationships?
   - Are there potential propagation paths or failure points not considered?

2. Contextual Richness:
   - Does the context generation provide sufficient "why" behind changes?
   - Is the technical detail balanced with conceptual explanation?
   - Are explanations tailored to each agent's perspective and domain?
   - Would an agent understand both what to do and why to do it?

3. Implementation Practicality:
   - Is the adaptation guidance specific and actionable?
   - Are integration steps realistic and appropriately scoped?
   - Have practical challenges and risks been adequately addressed?
   - Would an agent be confident in implementing the changes as described?

## Output Format

Your output must be a valid JSON object with the following structure:

```json
{
  "reflection_results": {
    "output_assessment": {
      "propagation_analysis": {
        "strengths": [string],
        "weaknesses": [string],
        "completeness_score": number,
        "detailed_feedback": string
      },
      "context_generation": {
        "strengths": [string],
        "weaknesses": [string],
        "completeness_score": number,
        "detailed_feedback": string
      },
      "adaptation_guidance": {
        "strengths": [string],
        "weaknesses": [string],
        "completeness_score": number,
        "detailed_feedback": string
      }
    },
    "cohesion_assessment": {
      "alignment_issues": [
        {
          "area": string,
          "description": string,
          "severity": string,
          "recommendation": string
        }
      ],
      "consistency_score": number,
      "cohesion_strengths": [string],
      "cohesion_gaps": [string]
    },
    "critical_improvements": [
      {
        "priority": number,
        "target_area": string,
        "issue_description": string,
        "improvement_recommendation": string,
        "expected_impact": string
      }
    ],
    "blind_spots": [
      {
        "area": string,
        "potential_issue": string,
        "consideration_recommendation": string
      }
    ],
    "overall_assessment": {
      "decision_quality_score": number,
      "propagation_quality_score": number,
      "context_quality_score": number,
      "guidance_quality_score": number,
      "summary_assessment": string,
      "critical_improvements_needed": boolean
    }
  },
  "metadata": {
    "reflection_timestamp": string,
    "original_operation_id": string,
    "iteration_number": number
  }
}
```

Where:
- `reflection_results`: Comprehensive reflection on the Water Agent outputs
- `output_assessment`: Assessment of each major output type
- `cohesion_assessment`: Analysis of alignment and consistency across outputs
- `critical_improvements`: Prioritized list of recommended improvements
- `blind_spots`: Identification of potential overlooked considerations
- `overall_assessment`: Summary evaluation of output quality
- `metadata`: Additional information about the reflection process

## Response Policy for Reflection

1. Be thorough and critical, but constructive in your feedback
2. Prioritize issues that would impact system stability or agent understanding
3. Be specific in identifying problems and proposing solutions
4. Consider both technical correctness and conceptual clarity
5. Focus on substantive improvements over stylistic preferences

Remember, your reflection serves to strengthen the Water Agent's ability to facilitate smooth system evolution through well-coordinated update propagation.
"""

reflection_schema = {
    "type": "object",
    "required": ["reflection_results", "metadata"],
    "properties": {
        "reflection_results": {
            "type": "object",
            "required": ["output_assessment", "cohesion_assessment", "critical_improvements", "blind_spots", "overall_assessment"],
            "properties": {
                "output_assessment": {
                    "type": "object",
                    "required": ["propagation_analysis", "context_generation", "adaptation_guidance"],
                    "properties": {
                        "propagation_analysis": {
                            "type": "object",
                            "required": ["strengths", "weaknesses", "completeness_score", "detailed_feedback"],
                            "properties": {
                                "strengths": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "weaknesses": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "completeness_score": {"type": "number", "minimum": 0, "maximum": 10},
                                "detailed_feedback": {"type": "string"}
                            }
                        },
                        "context_generation": {
                            "type": "object",
                            "required": ["strengths", "weaknesses", "completeness_score", "detailed_feedback"],
                            "properties": {
                                "strengths": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "weaknesses": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "completeness_score": {"type": "number", "minimum": 0, "maximum": 10},
                                "detailed_feedback": {"type": "string"}
                            }
                        },
                        "adaptation_guidance": {
                            "type": "object",
                            "required": ["strengths", "weaknesses", "completeness_score", "detailed_feedback"],
                            "properties": {
                                "strengths": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "weaknesses": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "completeness_score": {"type": "number", "minimum": 0, "maximum": 10},
                                "detailed_feedback": {"type": "string"}
                            }
                        }
                    }
                },
                "cohesion_assessment": {
                    "type": "object",
                    "required": ["alignment_issues", "consistency_score", "cohesion_strengths", "cohesion_gaps"],
                    "properties": {
                        "alignment_issues": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["area", "description", "severity", "recommendation"],
                                "properties": {
                                    "area": {"type": "string"},
                                    "description": {"type": "string"},
                                    "severity": {
                                        "type": "string",
                                        "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
                                    },
                                    "recommendation": {"type": "string"}
                                }
                            }
                        },
                        "consistency_score": {"type": "number", "minimum": 0, "maximum": 10},
                        "cohesion_strengths": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "cohesion_gaps": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "critical_improvements": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["priority", "target_area", "issue_description", "improvement_recommendation", "expected_impact"],
                        "properties": {
                            "priority": {"type": "number", "minimum": 1, "maximum": 10},
                            "target_area": {"type": "string"},
                            "issue_description": {"type": "string"},
                            "improvement_recommendation": {"type": "string"},
                            "expected_impact": {"type": "string"}
                        }
                    }
                },
                "blind_spots": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["area", "potential_issue", "consideration_recommendation"],
                        "properties": {
                            "area": {"type": "string"},
                            "potential_issue": {"type": "string"},
                            "consideration_recommendation": {"type": "string"}
                        }
                    }
                },
                "overall_assessment": {
                    "type": "object",
                    "required": ["decision_quality_score", "propagation_quality_score", "context_quality_score", "guidance_quality_score", "summary_assessment", "critical_improvements_needed"],
                    "properties": {
                        "decision_quality_score": {"type": "number", "minimum": 0, "maximum": 10},
                        "propagation_quality_score": {"type": "number", "minimum": 0, "maximum": 10},
                        "context_quality_score": {"type": "number", "minimum": 0, "maximum": 10},
                        "guidance_quality_score": {"type": "number", "minimum": 0, "maximum": 10},
                        "summary_assessment": {"type": "string"},
                        "critical_improvements_needed": {"type": "boolean"}
                    }
                }
            }
        },
        "metadata": {
            "type": "object",
            "required": ["reflection_timestamp", "original_operation_id", "iteration_number"],
            "properties": {
                "reflection_timestamp": {"type": "string"},
                "original_operation_id": {"type": "string"},
                "iteration_number": {"type": "number", "minimum": 1}
            }
        }
    }
}