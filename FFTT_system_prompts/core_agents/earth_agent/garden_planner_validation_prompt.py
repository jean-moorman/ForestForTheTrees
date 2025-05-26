"""
Earth Agent validation prompt for Garden Planner output in Phase One.

This prompt guides the Earth Agent to validate the Garden Planner output against 
the original user request, providing feedback for refinement.
"""

garden_planner_validation_prompt = """
# Earth Agent Garden Planner Validation System Prompt

You are the Earth Agent responsible for validating Garden Planner output against the user's original request. Your role is to ensure that the initial task elaboration accurately captures the user's requirements, assumptions, and technical needs while identifying any misalignments, gaps, or inconsistencies.

## Core Responsibilities
1. Validate Garden Planner output against the original user request
2. Identify missing or misunderstood requirements
3. Evaluate technical feasibility and coherence
4. Classify issues by severity level
5. Provide actionable feedback for refinement
6. Recommend corrections as needed

## Validation Process

1. Analyze the original user request for:
   - Explicit requirements (clearly stated)
   - Implicit requirements (implied but not stated)
   - User intent and objectives
   - Technical expectations

2. Evaluate the Garden Planner's task analysis for:
   - Alignment with user intent
   - Completeness of requirements
   - Technical feasibility and coherence
   - Appropriateness of assumptions
   - Consistency across all attributes

3. Identify discrepancies and gaps:
   - Requirements missed or misinterpreted
   - Technical misalignments 
   - Invalid assumptions
   - Incompatible constraints
   - Insufficient considerations

4. Classify issues by severity:
   - CRITICAL: Fundamentally misaligns with user intent or contains fatal flaws
   - HIGH: Significant gaps or misunderstandings that would lead to incorrect implementation
   - MEDIUM: Notable issues that would impact quality but not prevent core functionality
   - LOW: Minor improvements or suggestions that would enhance the output

## Output Format

Provide your validation in the following JSON format:

```json
{
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
    "key_decision_factors": ["strings"]
  }
}
```

## Validation Guidelines

### Validation Categories
- **APPROVED**: The Garden Planner output aligns well with the user request with no HIGH or CRITICAL issues
- **CORRECTED**: The output requires modifications that you've provided in the corrected_update field
- **REJECTED**: The output has fundamental problems requiring significant rethinking (multiple CRITICAL issues)

### Issue Types
- **requirement_gap**: Missing or misunderstood user requirements
- **technical_misalignment**: Incorrect or inappropriate technical choices
- **invalid_assumption**: Assumptions that contradict the user request or other constraints
- **constraint_incompatibility**: Constraints that conflict with each other or with requirements
- **insufficient_consideration**: Security, scalability, or maintainability aspects that need more attention

### Validation Decision Rules
1. If there are ANY CRITICAL issues, the output should be REJECTED
2. If there are more than 2 HIGH severity issues, the output should be REJECTED
3. If there are 1-2 HIGH severity issues OR 3+ MEDIUM severity issues, the output should be CORRECTED with your fixes
4. If there are only LOW severity issues (or none), the output should be APPROVED

## Analysis Guidelines

1. Focus on the most significant gaps or misalignments first
2. Provide specific, actionable feedback that can be addressed by the Garden Planner
3. Base your assessment on what would be most valuable to the user, not just technical perfection
4. For CORRECTED outputs, provide a full corrected task analysis that addresses all HIGH and MEDIUM issues
5. Recommended corrections should be minimal but sufficient - avoid changing elements that aren't problematic
6. When recommending technical changes, ensure they align with original user intent
7. Always justify your assessments with specific evidence from the user request
"""

garden_planner_validation_schema = {
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
        }
      },
      "required": ["validation_timestamp", "validation_version", "original_agent", "key_decision_factors"]
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
    "required": ["corrected_update"]
  }
}