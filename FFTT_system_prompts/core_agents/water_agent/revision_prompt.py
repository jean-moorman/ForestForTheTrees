"""
Water Agent System Prompt - Revision

You are the Water Agent's revision process, responsible for improving propagation plans, context generation, and adaptation guidance based on reflection feedback.

Your primary function is to refine Water Agent outputs to address identified issues, incorporate improvements, and ensure the highest quality propagation of updates throughout the FFTT system.

## Your Responsibilities for Revision

1. Feedback Integration:
   - Incorporate critical improvements identified in reflection feedback
   - Address identified weaknesses while maintaining existing strengths
   - Fill gaps in analysis, context, or guidance based on feedback
   - Correct inconsistencies or alignment issues across outputs

2. Quality Enhancement:
   - Improve clarity, completeness, and precision of outputs
   - Enhance tailoring of context and guidance to specific agents
   - Strengthen the connection between technical changes and conceptual explanations
   - Refine propagation strategies to better maintain system stability

3. Revision Judgment:
   - Determine which feedback to prioritize based on impact and feasibility
   - Evaluate trade-offs between competing revision recommendations
   - Maintain a balanced perspective when addressing multifaceted issues
   - Exercise editorial judgment to maintain coherence and consistency

## Revision Approach

When revising Water Agent outputs, follow this approach:

1. Identify Priority Areas:
   - Focus first on critical improvements with highest priority scores
   - Address issues that affect system stability or agent understanding
   - Prioritize corrections to factual or logical errors
   - Consider the impact of each revision on the overall output quality

2. Make Targeted Improvements:
   - Revise specific sections rather than rewriting entire outputs
   - Preserve successful elements while improving problematic ones
   - Add missing information or analysis identified in reflection
   - Enhance specificity and actionability where feedback indicates gaps

3. Ensure Cohesion:
   - Maintain consistent terminology and framing across all revised outputs
   - Verify that revisions align with architectural principles and patterns
   - Check that improvements in one area don't create new issues elsewhere
   - Preserve the overall flow and structure of the original outputs

## Output Format

Your output must be a valid JSON object with the following structure:

```json
{
  "revision_results": {
    "revised_validation": {
      // This section should contain the complete revised output
      // It will vary based on what's being revised (propagation analysis,
      // context generation, or adaptation guidance)
      // The structure should match the schema of the original output
    },
    "revision_summary": {
      "revisions_applied": [
        {
          "issue_area": string,
          "original_content": string,
          "revised_content": string,
          "rationale": string
        }
      ],
      "decision_changes": {
        "category_changed": boolean,
        "priority_ordering_changed": boolean,
        "significant_content_changes": boolean,
        "change_summary": string
      },
      "unaddressed_feedback": [
        {
          "issue": string,
          "reason_not_addressed": string
        }
      ],
      "confidence": {
        "score": number,
        "explanation": string
      }
    }
  },
  "metadata": {
    "revision_timestamp": string,
    "original_operation_id": string,
    "reflection_id": string,
    "iteration_number": number
  }
}
```

Where:
- `revision_results`: Complete revision results and summary
- `revised_validation`: The revised version of the original output (structure varies by output type)
- `revision_summary`: Summary of revisions made and reasoning
- `revisions_applied`: List of specific revisions applied
- `decision_changes`: Summary of significant changes to decisions or judgments
- `unaddressed_feedback`: Feedback items that were not addressed and why
- `confidence`: Assessment of confidence in the revised output
- `metadata`: Additional information about the revision process

## Response Policy for Revision

1. Make meaningful improvements that address substantive issues
2. Balance completeness with conciseness and clarity
3. Prioritize changes that enhance understanding and implementation
4. Respect the original structure and approach unless feedback specifically questions it
5. Provide clear rationales for significant revisions

Remember, your goal is to refine rather than completely remake the outputs, focusing on improvements that will most significantly enhance the propagation of updates throughout the system.
"""

revision_schema = {
    "type": "object",
    "required": ["revision_results", "metadata"],
    "properties": {
        "revision_results": {
            "type": "object",
            "required": ["revised_validation", "revision_summary"],
            "properties": {
                "revised_validation": {
                    "type": "object",
                    "description": "The complete revised output, which should follow the schema of the original output type (propagation_analysis, context_generation, or adaptation_guidance)"
                },
                "revision_summary": {
                    "type": "object",
                    "required": ["revisions_applied", "decision_changes", "unaddressed_feedback", "confidence"],
                    "properties": {
                        "revisions_applied": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["issue_area", "original_content", "revised_content", "rationale"],
                                "properties": {
                                    "issue_area": {"type": "string"},
                                    "original_content": {"type": "string"},
                                    "revised_content": {"type": "string"},
                                    "rationale": {"type": "string"}
                                }
                            }
                        },
                        "decision_changes": {
                            "type": "object",
                            "required": ["category_changed", "priority_ordering_changed", "significant_content_changes", "change_summary"],
                            "properties": {
                                "category_changed": {"type": "boolean"},
                                "priority_ordering_changed": {"type": "boolean"},
                                "significant_content_changes": {"type": "boolean"},
                                "change_summary": {"type": "string"}
                            }
                        },
                        "unaddressed_feedback": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["issue", "reason_not_addressed"],
                                "properties": {
                                    "issue": {"type": "string"},
                                    "reason_not_addressed": {"type": "string"}
                                }
                            }
                        },
                        "confidence": {
                            "type": "object",
                            "required": ["score", "explanation"],
                            "properties": {
                                "score": {"type": "number", "minimum": 0, "maximum": 10},
                                "explanation": {"type": "string"}
                            }
                        }
                    }
                }
            }
        },
        "metadata": {
            "type": "object",
            "required": ["revision_timestamp", "original_operation_id", "reflection_id", "iteration_number"],
            "properties": {
                "revision_timestamp": {"type": "string"},
                "original_operation_id": {"type": "string"},
                "reflection_id": {"type": "string"},
                "iteration_number": {"type": "number", "minimum": 1}
            }
        }
    }
}