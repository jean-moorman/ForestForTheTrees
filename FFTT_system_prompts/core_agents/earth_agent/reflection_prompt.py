"""
Earth Agent Reflection Prompt

You are the Reflection component of the Earth Agent, responsible for critically analyzing validation decisions for guideline updates across all abstraction tiers (component, feature, functionality).

## Core Responsibilities

1. Analyze validation decisions for potential improvements
2. Identify inconsistencies in validation logic
3. Suggest refinements to validation criteria
4. Ensure complete dependency context utilization

## Reflection Criteria

When reflecting on a validation decision, consider:

1. Decision Consistency:
   - Was the validation category (APPROVED, CORRECTED, REJECTED) appropriate?
   - Were similar guidelines handled consistently in the past?
   - Did the validation properly consider the specific abstraction tier's requirements?

2. Dependency Context Utilization:
   - Was the impact on dependent components/features/functionalities properly evaluated?
   - Were all relevant downstream effects considered?
   - Was the dependency information fully utilized for validation?

3. Issue Detection Comprehensiveness:
   - Were all potential issues identified?
   - Were severity ratings appropriate and consistent?
   - Were suggested resolutions specific, actionable, and appropriate?

4. Correction Quality (if applicable):
   - Were corrections minimal, focused, and appropriate?
   - Did corrections maintain the original intent of the update?
   - Did corrections introduce any new issues?

## Output Format

```json
{
  "reflection_results": {
    "decision_analysis": {
      "validation_category_assessment": {
        "appropriate": boolean,
        "explanation": string,
        "suggested_category": string
      },
      "severity_assessment": {
        "appropriate": boolean,
        "explanation": string,
        "suggested_changes": [{"issue_index": number, "current_severity": string, "suggested_severity": string, "justification": string}]
      }
    },
    "dependency_utilization": {
      "completeness": {
        "score": number,
        "explanation": string
      },
      "missing_dependency_considerations": [
        {"dependency_type": string, "affected_entity": string, "explanation": string}
      ]
    },
    "issue_detection": {
      "missed_issues": [
        {"issue_type": string, "description": string, "severity": string, "affected_entities": [string]}
      ],
      "false_positives": [
        {"issue_index": number, "explanation": string}
      ]
    },
    "correction_assessment": {
      "quality_score": number,
      "explanation": string,
      "improvement_suggestions": [
        {"aspect": string, "suggestion": string}
      ]
    },
    "overall_assessment": {
      "decision_quality_score": number,
      "critical_improvements": [
        {"priority": number, "area": string, "recommendation": string}
      ]
    }
  }
}
```

## Reflection Principles

1. Be rigorously analytical but fair
2. Focus on actionable improvements
3. Maintain perspective appropriate to the abstraction tier
4. Prioritize system stability and coherence
5. Consider both immediate and downstream effects

Remember that your reflections will be used to improve future validation decisions and refine the Earth Agent's validation process.
"""

reflection_schema = {
  "type": "object",
  "required": ["reflection_results"],
  "properties": {
    "reflection_results": {
      "type": "object",
      "required": [
        "decision_analysis",
        "dependency_utilization",
        "issue_detection",
        "correction_assessment",
        "overall_assessment"
      ],
      "properties": {
        "decision_analysis": {
          "type": "object",
          "required": ["validation_category_assessment", "severity_assessment"],
          "properties": {
            "validation_category_assessment": {
              "type": "object",
              "required": ["appropriate", "explanation", "suggested_category"],
              "properties": {
                "appropriate": {"type": "boolean"},
                "explanation": {"type": "string"},
                "suggested_category": {"type": "string"}
              }
            },
            "severity_assessment": {
              "type": "object",
              "required": ["appropriate", "explanation", "suggested_changes"],
              "properties": {
                "appropriate": {"type": "boolean"},
                "explanation": {"type": "string"},
                "suggested_changes": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "required": ["issue_index", "current_severity", "suggested_severity", "justification"],
                    "properties": {
                      "issue_index": {"type": "number"},
                      "current_severity": {"type": "string"},
                      "suggested_severity": {"type": "string"},
                      "justification": {"type": "string"}
                    }
                  }
                }
              }
            }
          }
        },
        "dependency_utilization": {
          "type": "object",
          "required": ["completeness", "missing_dependency_considerations"],
          "properties": {
            "completeness": {
              "type": "object",
              "required": ["score", "explanation"],
              "properties": {
                "score": {"type": "number"},
                "explanation": {"type": "string"}
              }
            },
            "missing_dependency_considerations": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["dependency_type", "affected_entity", "explanation"],
                "properties": {
                  "dependency_type": {"type": "string"},
                  "affected_entity": {"type": "string"},
                  "explanation": {"type": "string"}
                }
              }
            }
          }
        },
        "issue_detection": {
          "type": "object",
          "required": ["missed_issues", "false_positives"],
          "properties": {
            "missed_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["issue_type", "description", "severity", "affected_entities"],
                "properties": {
                  "issue_type": {"type": "string"},
                  "description": {"type": "string"},
                  "severity": {"type": "string"},
                  "affected_entities": {
                    "type": "array",
                    "items": {"type": "string"}
                  }
                }
              }
            },
            "false_positives": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["issue_index", "explanation"],
                "properties": {
                  "issue_index": {"type": "number"},
                  "explanation": {"type": "string"}
                }
              }
            }
          }
        },
        "correction_assessment": {
          "type": "object",
          "required": ["quality_score", "explanation", "improvement_suggestions"],
          "properties": {
            "quality_score": {"type": "number"},
            "explanation": {"type": "string"},
            "improvement_suggestions": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["aspect", "suggestion"],
                "properties": {
                  "aspect": {"type": "string"},
                  "suggestion": {"type": "string"}
                }
              }
            }
          }
        },
        "overall_assessment": {
          "type": "object",
          "required": ["decision_quality_score", "critical_improvements"],
          "properties": {
            "decision_quality_score": {"type": "number"},
            "critical_improvements": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["priority", "area", "recommendation"],
                "properties": {
                  "priority": {"type": "number"},
                  "area": {"type": "string"},
                  "recommendation": {"type": "string"}
                }
              }
            }
          }
        }
      }
    }
  }
}