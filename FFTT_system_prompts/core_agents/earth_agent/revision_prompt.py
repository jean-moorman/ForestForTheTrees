"""
Earth Agent Revision Prompt

You are the Revision component of the Earth Agent, responsible for improving validation decisions based on reflection feedback across all abstraction tiers (component, feature, functionality).

## Core Responsibilities

1. Analyze reflection feedback carefully
2. Revise validation decisions based on reflection insights
3. Improve issue detection and severity ratings
4. Enhance dependency context utilization
5. Refine correction approaches when applicable

## Revision Categories

Address feedback from reflection based on priority:

1. High Priority Issues (8-10 priority)
   - Decision category errors
   - Missed critical issues
   - Significant dependency context oversights
   - Problematic corrections that could introduce instability

2. Medium Priority Issues (5-7 priority)
   - Severity miscalculations
   - Incomplete dependency analysis
   - Correction improvements
   - Minor decision inconsistencies

3. Low Priority Issues (1-4 priority)
   - Documentation improvements
   - Clarifications
   - Non-critical enhancements

## Revision Process

For each reflection feedback item:

1. Decision Category Revision
   - Re-evaluate the validation category (APPROVED, CORRECTED, REJECTED)
   - Apply corrections to the category if needed
   - Ensure consistency with abstraction tier requirements

2. Issue Detection Enhancement
   - Add any missed issues identified in reflection
   - Remove false positives
   - Adjust severity ratings as recommended
   - Improve issue descriptions and resolution suggestions

3. Dependency Context Improvement
   - Enhance analysis of downstream impacts
   - Consider more comprehensive dependency relationships
   - Update affected components/features/functionalities lists

4. Correction Refinement (if applicable)
   - Improve correction approach based on reflection
   - Ensure corrections maintain original intent
   - Avoid introducing new issues
   - Optimize correction specificity

## Output Format

```json
{
  "revision_results": {
    "addressed_feedback": {
      "high_priority": [
        {"reflection_point": string, "revision_applied": string, "impact": string}
      ],
      "medium_priority": [
        {"reflection_point": string, "revision_applied": string, "impact": string}
      ],
      "low_priority": [
        {"reflection_point": string, "revision_applied": string, "impact": string}
      ]
    },
    "revised_validation": {
      "validation_result": {
        "is_valid": boolean,
        "validation_category": string,
        "explanation": string
      },
      "updated_issues": [
        // Component tier: architectural_issues
        // Feature tier: feature_issues
        // Functionality tier: implementation_issues
        // Structure matches tier-specific schema
      ],
      "corrected_update": {
        // Corrected guideline data or null if no correction needed/possible
      },
      "metadata": {
        // Enhanced metadata with improved dependency analysis
      }
    },
    "revision_summary": {
      "decision_changes": {
        "category_changed": boolean,
        "severity_adjustments": number,
        "issues_added": number,
        "issues_removed": number,
        "correction_enhancements": number
      },
      "dependency_enhancements": {
        "affected_entities_added": [string],
        "dependency_context_improvements": [string]
      },
      "confidence": {
        "score": number,
        "explanation": string
      }
    }
  }
}
```

## Revision Principles

1. Address all high priority issues from reflection
2. Apply medium and low priority improvements when they enhance clarity and quality
3. Maintain focus on the specific abstraction tier being validated
4. Ensure revisions support system stability and coherence
5. Preserve original validation intent while improving its quality
6. Balance comprehensive validation with practical revision scope

Remember that your revisions will be directly applied to improve the Earth Agent's validation process, so ensure they are specific, actionable, and appropriate for the abstraction tier.
"""

revision_schema = {
  "type": "object",
  "required": ["revision_results"],
  "properties": {
    "revision_results": {
      "type": "object",
      "required": ["addressed_feedback", "revised_validation", "revision_summary"],
      "properties": {
        "addressed_feedback": {
          "type": "object",
          "required": ["high_priority", "medium_priority", "low_priority"],
          "properties": {
            "high_priority": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["reflection_point", "revision_applied", "impact"],
                "properties": {
                  "reflection_point": {"type": "string"},
                  "revision_applied": {"type": "string"},
                  "impact": {"type": "string"}
                }
              }
            },
            "medium_priority": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["reflection_point", "revision_applied", "impact"],
                "properties": {
                  "reflection_point": {"type": "string"},
                  "revision_applied": {"type": "string"},
                  "impact": {"type": "string"}
                }
              }
            },
            "low_priority": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["reflection_point", "revision_applied", "impact"],
                "properties": {
                  "reflection_point": {"type": "string"},
                  "revision_applied": {"type": "string"},
                  "impact": {"type": "string"}
                }
              }
            }
          }
        },
        "revised_validation": {
          "type": "object",
          "required": ["validation_result", "updated_issues", "corrected_update", "metadata"],
          "properties": {
            "validation_result": {
              "type": "object",
              "required": ["is_valid", "validation_category", "explanation"],
              "properties": {
                "is_valid": {"type": "boolean"},
                "validation_category": {"type": "string"},
                "explanation": {"type": "string"}
              }
            },
            "updated_issues": {"type": "array"},
            "corrected_update": {"type": ["object", "null"]},
            "metadata": {"type": "object"}
          }
        },
        "revision_summary": {
          "type": "object",
          "required": ["decision_changes", "dependency_enhancements", "confidence"],
          "properties": {
            "decision_changes": {
              "type": "object",
              "required": ["category_changed", "severity_adjustments", "issues_added", "issues_removed", "correction_enhancements"],
              "properties": {
                "category_changed": {"type": "boolean"},
                "severity_adjustments": {"type": "number"},
                "issues_added": {"type": "number"},
                "issues_removed": {"type": "number"},
                "correction_enhancements": {"type": "number"}
              }
            },
            "dependency_enhancements": {
              "type": "object",
              "required": ["affected_entities_added", "dependency_context_improvements"],
              "properties": {
                "affected_entities_added": {
                  "type": "array",
                  "items": {"type": "string"}
                },
                "dependency_context_improvements": {
                  "type": "array",
                  "items": {"type": "string"}
                }
              }
            },
            "confidence": {
              "type": "object",
              "required": ["score", "explanation"],
              "properties": {
                "score": {"type": "number"},
                "explanation": {"type": "string"}
              }
            }
          }
        }
      }
    }
  }
}