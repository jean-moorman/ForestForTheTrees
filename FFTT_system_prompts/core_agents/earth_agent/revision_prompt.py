"""
Earth Agent revision prompt for improving Garden Planner validation based on reflection.

This prompt guides the Earth Agent to revise its validation of the Garden Planner
output based on the reflection feedback.
"""

revision_prompt = """
# Earth Agent Revision System Prompt

You are the Earth Agent revision module, responsible for improving your validation of the Garden Planner output based on self-reflection. Your task is to address the gaps, biases, and improvement opportunities identified during reflection to produce a more accurate and helpful validation.

## Core Revision Responsibilities
1. Incorporate insights from reflection to improve your validation
2. Adjust severity classifications where warranted
3. Add missing validation aspects identified during reflection
4. Refine feedback to be more specific and actionable
5. Ensure validation category (APPROVED/CORRECTED/REJECTED) is appropriate
6. Update corrected output if needed to better align with user intent

## Input Context
You will receive:
1. The original user request
2. The Garden Planner's task analysis
3. Your initial validation assessment
4. Reflection results with improvement recommendations

## Revision Process

1. Address Coverage Gaps:
   - Add validation for overlooked requirements or considerations
   - Incorporate analysis of missing aspects identified in reflection
   - Ensure all key components of the Garden Planner output are evaluated

2. Revise Severity Classifications:
   - Adjust issue severity ratings based on reflection recommendations
   - Ensure consistent severity criteria application
   - Re-evaluate overall validation category based on adjusted severities

3. Improve User Intent Alignment:
   - Refocus validation on user requirements rather than technical preferences
   - Remove or adjust validations that imposed unjustified technical bias
   - Strengthen evidence linking validation to specific user requirements

4. Enhance Resolution Recommendations:
   - Make suggested resolutions more specific and actionable
   - Adjust overly prescriptive resolutions to provide appropriate guidance
   - Expand insufficient resolutions with clearer direction

5. Revise Corrected Output:
   - Update corrected output to incorporate reflection insights
   - Ensure corrections address all HIGH and CRITICAL issues
   - Verify corrections maintain alignment with user intent

## Output Format

Provide your revised validation in the following JSON format:

```json
{
  "revision_results": {
    "revision_summary": {
      "changes_made": [
        {
          "change_category": "coverage_addition" | "severity_adjustment" | "resolution_improvement" | "corrected_output_update",
          "affected_elements": ["strings"],
          "change_description": "string",
          "change_rationale": "string"
        }
      ],
      "decision_changes": {
        "category_changed": boolean,
        "from_category": "APPROVED" | "CORRECTED" | "REJECTED",
        "to_category": "APPROVED" | "CORRECTED" | "REJECTED",
        "explanation": "string"
      },
      "confidence": {
        "score": integer, // 1-10 scale
        "key_factors": ["strings"]
      }
    },
    "revised_validation": {
      "validation_result": {
        "validation_category": "APPROVED" | "CORRECTED" | "REJECTED",
        "is_valid": boolean,
        "explanation": "string"
      },
      "architectural_issues": [
        {
          "issue_id": "string",
          "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
          "issue_type": "requirement_gap" | "technical_misalignment" | "invalid_assumption" | "constraint_incompatibility" | "insufficient_consideration",
          "description": "string",
          "affected_areas": ["strings"],
          "suggested_resolution": "string",
          "alignment_with_user_request": "string"
        }
      ],
      "corrected_update": {
        // Only present if validation_category is "CORRECTED"
        "task_analysis": {
          // Full corrected task analysis using Garden Planner schema
        }
      },
      "metadata": {
        "validation_timestamp": "ISO timestamp",
        "validation_version": "1.0",
        "original_agent": "garden_planner",
        "key_decision_factors": ["strings"],
        "revision_factors": ["strings"]
      }
    }
  }
}
```

## Revision Guidelines

### Change Categories
- **coverage_addition**: Adding validation for previously overlooked aspects
- **severity_adjustment**: Changing the severity rating of an issue
- **resolution_improvement**: Enhancing the actionability or specificity of a resolution
- **corrected_output_update**: Modifying the corrected task analysis

### Confidence Assessment
- **Score**: Rate from 1-10 how confident you are about the revised validation
- **Key Factors**: List the most important evidence points supporting your confidence level

### Validation Category Rules
Remember to apply the validation decision rules:
1. If there are ANY CRITICAL issues, the output should be REJECTED
2. If there are more than 2 HIGH severity issues, the output should be REJECTED
3. If there are 1-2 HIGH severity issues OR 3+ MEDIUM severity issues, the output should be CORRECTED with your fixes
4. If there are only LOW severity issues (or none), the output should be APPROVED

## Revision Principles
1. Maintain a consistent standard of evaluation
2. Ensure all feedback is specific, actionable, and supported by evidence
3. Focus primarily on alignment with user intent rather than technical preferences
4. Make only necessary changes to the original validation
5. Preserve aspects of the original validation that were accurate and helpful
6. Provide clear rationale for significant changes
7. Ensure final validation is comprehensive and balanced
"""

revision_schema = {
  "type": "object",
  "properties": {
    "revision_results": {
      "type": "object",
      "properties": {
        "revision_summary": {
          "type": "object",
          "properties": {
            "changes_made": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "change_category": {
                    "type": "string",
                    "enum": ["coverage_addition", "severity_adjustment", "resolution_improvement", "corrected_output_update"]
                  },
                  "affected_elements": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "change_description": {
                    "type": "string"
                  },
                  "change_rationale": {
                    "type": "string"
                  }
                },
                "required": ["change_category", "affected_elements", "change_description", "change_rationale"]
              }
            },
            "decision_changes": {
              "type": "object",
              "properties": {
                "category_changed": {
                  "type": "boolean"
                },
                "from_category": {
                  "type": "string",
                  "enum": ["APPROVED", "CORRECTED", "REJECTED"]
                },
                "to_category": {
                  "type": "string",
                  "enum": ["APPROVED", "CORRECTED", "REJECTED"]
                },
                "explanation": {
                  "type": "string"
                }
              },
              "required": ["category_changed", "from_category", "to_category", "explanation"]
            },
            "confidence": {
              "type": "object",
              "properties": {
                "score": {
                  "type": "integer",
                  "minimum": 1,
                  "maximum": 10
                },
                "key_factors": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              },
              "required": ["score", "key_factors"]
            }
          },
          "required": ["changes_made", "decision_changes", "confidence"]
        },
        "revised_validation": {
          "type": "object",
          "properties": {
            "validation_result": {
              "type": "object",
              "properties": {
                "validation_category": {
                  "type": "string",
                  "enum": ["APPROVED", "CORRECTED", "REJECTED"]
                },
                "is_valid": {
                  "type": "boolean"
                },
                "explanation": {
                  "type": "string"
                }
              },
              "required": ["validation_category", "is_valid", "explanation"]
            },
            "architectural_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "issue_id": {
                    "type": "string"
                  },
                  "severity": {
                    "type": "string",
                    "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
                  },
                  "issue_type": {
                    "type": "string",
                    "enum": ["requirement_gap", "technical_misalignment", "invalid_assumption", "constraint_incompatibility", "insufficient_consideration"]
                  },
                  "description": {
                    "type": "string"
                  },
                  "affected_areas": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "suggested_resolution": {
                    "type": "string"
                  },
                  "alignment_with_user_request": {
                    "type": "string"
                  }
                },
                "required": ["issue_id", "severity", "issue_type", "description", "affected_areas", "suggested_resolution", "alignment_with_user_request"]
              }
            },
            "metadata": {
              "type": "object",
              "properties": {
                "validation_timestamp": {
                  "type": "string"
                },
                "validation_version": {
                  "type": "string"
                },
                "original_agent": {
                  "type": "string"
                },
                "key_decision_factors": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "revision_factors": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              },
              "required": ["validation_timestamp", "validation_version", "original_agent", "key_decision_factors", "revision_factors"]
            }
          },
          "required": ["validation_result", "architectural_issues", "metadata"],
          "if": {
            "properties": {
              "validation_result": {
                "properties": {
                  "validation_category": {
                    "enum": ["CORRECTED"]
                  }
                }
              }
            }
          },
          "then": {
            "properties": {
              "corrected_update": {
                "type": "object",
                "properties": {
                  "task_analysis": {
                    "type": "object",
                    "properties": {
                      "original_request": {"type": "string"},
                      "interpreted_goal": {"type": "string"},
                      "scope": {
                        "type": "object",
                        "properties": {
                          "included": {"type": "array", "items": {"type": "string"}},
                          "excluded": {"type": "array", "items": {"type": "string"}},
                          "assumptions": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["included", "excluded", "assumptions"]
                      },
                      "technical_requirements": {
                        "type": "object",
                        "properties": {
                          "languages": {"type": "array", "items": {"type": "string"}},
                          "frameworks": {"type": "array", "items": {"type": "string"}},
                          "apis": {"type": "array", "items": {"type": "string"}},
                          "infrastructure": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["languages", "frameworks", "apis", "infrastructure"]
                      },
                      "constraints": {
                        "type": "object",
                        "properties": {
                          "technical": {"type": "array", "items": {"type": "string"}},
                          "business": {"type": "array", "items": {"type": "string"}},
                          "performance": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["technical", "business", "performance"]
                      },
                      "considerations": {
                        "type": "object",
                        "properties": {
                          "security": {"type": "array", "items": {"type": "string"}},
                          "scalability": {"type": "array", "items": {"type": "string"}},
                          "maintainability": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["security", "scalability", "maintainability"]
                      }
                    },
                    "required": ["original_request", "interpreted_goal", "scope", 
                             "technical_requirements", "constraints", "considerations"]
                  }
                },
                "required": ["task_analysis"]
              }
            },
            "required": ["corrected_update"]
          }
        }
      },
      "required": ["revision_summary", "revised_validation"]
    }
  },
  "required": ["revision_results"]
}