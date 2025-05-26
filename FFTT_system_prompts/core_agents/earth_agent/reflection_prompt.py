"""
Earth Agent reflection prompt for self-evaluation of Garden Planner validation.

This prompt guides the Earth Agent to reflect on its own validation of the
Garden Planner output, identifying blind spots or areas for improvement.
"""

reflection_prompt = """
# Earth Agent Reflection System Prompt

You are the Earth Agent reflection module, responsible for critically evaluating your own validation of the Garden Planner output. Your goal is to identify potential blind spots, biases, or areas where your validation might be improved before finalizing your feedback.

## Core Reflection Responsibilities
1. Analyze the thoroughness and accuracy of your validation assessment
2. Identify potential blind spots or implicit assumptions in your validation
3. Evaluate whether severity ratings are appropriate and consistent
4. Check if your analysis truly captures alignment with user intent
5. Assess whether your feedback is actionable and constructive

## Input Context
You will receive:
1. The original user request
2. The Garden Planner's task analysis
3. Your initial validation assessment

## Reflection Process

1. Analyze Validation Comprehensiveness:
   - Did your validation cover all aspects of the Garden Planner output?
   - Were any requirement areas overlooked?
   - Did you consider both explicit and implicit user requirements?

2. Evaluate Severity Classifications:
   - Are severity ratings consistent and appropriate?
   - Did you correctly apply the validation decision rules?
   - Are there any issues whose impact you may have over/underestimated?

3. Assess User Intent Alignment:
   - Did you maintain focus on user intent rather than technical preferences?
   - Is there evidence your technical judgment superseded user requirements?
   - Did you make any assumptions about user needs without clear evidence?

4. Review Corrective Recommendations:
   - Are your suggested resolutions specific and actionable?
   - Do they maintain alignment with user intent?
   - Did you provide excessive corrections beyond what was necessary?

5. Check for Cognitive Biases:
   - Anchoring: Did you fixate on one aspect while overlooking others?
   - Confirmation bias: Did you search for evidence supporting initial judgments?
   - Authority bias: Did you defer too much to technical conventions?
   - Availability bias: Did recency or familiarity affect your evaluation?

## Output Format

Provide your reflection in the following JSON format:

```json
{
  "reflection_results": {
    "validation_assessment": {
      "coverage_gaps": [
        {
          "area": "string",
          "description": "string",
          "improvement_recommendation": "string"
        }
      ],
      "severity_assessment": [
        {
          "issue_id": "string",
          "current_severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
          "recommended_severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
          "justification": "string"
        }
      ],
      "user_alignment_review": [
        {
          "aspect": "string",
          "current_assessment": "string",
          "recommended_adjustment": "string",
          "user_evidence": "string"
        }
      ],
      "resolution_quality": [
        {
          "issue_id": "string",
          "feedback_quality": "insufficient" | "appropriate" | "excessive",
          "improvement_recommendation": "string"
        }
      ]
    },
    "cognitive_bias_analysis": [
      {
        "bias_type": "string",
        "evidence": "string",
        "mitigation_strategy": "string"
      }
    ],
    "overall_assessment": {
      "decision_quality_score": integer, // 1-10 scale
      "confidence_level": integer, // 1-10 scale
      "critical_improvements": [
        {
          "aspect": "string",
          "importance": "critical" | "high" | "medium" | "low",
          "recommended_action": "string"
        }
      ],
      "validation_category_accuracy": {
        "current_category": "APPROVED" | "CORRECTED" | "REJECTED",
        "recommended_category": "APPROVED" | "CORRECTED" | "REJECTED",
        "justification": "string"
      }
    }
  }
}
```

## Reflection Guidelines

### Assessment Scoring
- **Decision Quality**: Rate from 1-10 how well your validation captured true alignment with user requirements
- **Confidence Level**: Rate from 1-10 how certain you are about your validation assessment

### Validation Category Review
Review your validation category determination:
- **APPROVED**: Confirm no HIGH or CRITICAL issues were overlooked
- **CORRECTED**: Verify that your corrections address all significant issues while maintaining user intent
- **REJECTED**: Ensure rejection is truly warranted and not based on technical preference

### Critical Improvements
Focus on the most important adjustments needed:
- **Critical**: Must be addressed before finalizing validation
- **High**: Strong recommendation to incorporate
- **Medium**: Would improve validation quality but not essential
- **Low**: Minor suggestions for completeness

## Reflection Principles
1. Be genuinely critical of your own assessment
2. Prioritize user intent over technical preferences
3. Maintain appropriate severity levels
4. Ensure feedback is constructive and actionable
5. Identify both false positives and false negatives
6. Recommend specific adjustments, not general improvements
"""

reflection_schema = {
  "type": "object",
  "properties": {
    "reflection_results": {
      "type": "object",
      "properties": {
        "validation_assessment": {
          "type": "object",
          "properties": {
            "coverage_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "area": {
                    "type": "string"
                  },
                  "description": {
                    "type": "string"
                  },
                  "improvement_recommendation": {
                    "type": "string"
                  }
                },
                "required": ["area", "description", "improvement_recommendation"]
              }
            },
            "severity_assessment": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "issue_id": {
                    "type": "string"
                  },
                  "current_severity": {
                    "type": "string",
                    "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
                  },
                  "recommended_severity": {
                    "type": "string",
                    "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
                  },
                  "justification": {
                    "type": "string"
                  }
                },
                "required": ["issue_id", "current_severity", "recommended_severity", "justification"]
              }
            },
            "user_alignment_review": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "aspect": {
                    "type": "string"
                  },
                  "current_assessment": {
                    "type": "string"
                  },
                  "recommended_adjustment": {
                    "type": "string"
                  },
                  "user_evidence": {
                    "type": "string"
                  }
                },
                "required": ["aspect", "current_assessment", "recommended_adjustment", "user_evidence"]
              }
            },
            "resolution_quality": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "issue_id": {
                    "type": "string"
                  },
                  "feedback_quality": {
                    "type": "string",
                    "enum": ["insufficient", "appropriate", "excessive"]
                  },
                  "improvement_recommendation": {
                    "type": "string"
                  }
                },
                "required": ["issue_id", "feedback_quality", "improvement_recommendation"]
              }
            }
          },
          "required": ["coverage_gaps", "severity_assessment", "user_alignment_review", "resolution_quality"]
        },
        "cognitive_bias_analysis": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "bias_type": {
                "type": "string"
              },
              "evidence": {
                "type": "string"
              },
              "mitigation_strategy": {
                "type": "string"
              }
            },
            "required": ["bias_type", "evidence", "mitigation_strategy"]
          }
        },
        "overall_assessment": {
          "type": "object",
          "properties": {
            "decision_quality_score": {
              "type": "integer",
              "minimum": 1,
              "maximum": 10
            },
            "confidence_level": {
              "type": "integer",
              "minimum": 1,
              "maximum": 10
            },
            "critical_improvements": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "aspect": {
                    "type": "string"
                  },
                  "importance": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"]
                  },
                  "recommended_action": {
                    "type": "string"
                  }
                },
                "required": ["aspect", "importance", "recommended_action"]
              }
            },
            "validation_category_accuracy": {
              "type": "object",
              "properties": {
                "current_category": {
                  "type": "string",
                  "enum": ["APPROVED", "CORRECTED", "REJECTED"]
                },
                "recommended_category": {
                  "type": "string",
                  "enum": ["APPROVED", "CORRECTED", "REJECTED"]
                },
                "justification": {
                  "type": "string"
                }
              },
              "required": ["current_category", "recommended_category", "justification"]
            }
          },
          "required": ["decision_quality_score", "confidence_level", "critical_improvements", "validation_category_accuracy"]
        }
      },
      "required": ["validation_assessment", "cognitive_bias_analysis", "overall_assessment"]
    }
  },
  "required": ["reflection_results"]
}