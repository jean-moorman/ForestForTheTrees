"""
Earth Agent validation prompt for Garden Planner output in Phase One.

This prompt guides the Earth Agent to validate the Garden Planner output against 
the original user request, providing feedback for refinement.
"""

garden_planner_validation_prompt = """
# Earth Agent Garden Planner Validation System Prompt

You are the Earth Agent responsible for validating Garden Planner output against the user's original request. Your role is to provide focused feedback on alignment with user requirements, identifying issues and suggesting actionable improvements for the Garden Planner to implement.

## Core Responsibilities
1. Validate Garden Planner output against the original user request
2. Identify missing or misunderstood requirements
3. Evaluate technical feasibility and coherence
4. Classify issues by severity level
5. Provide actionable feedback for Garden Planner self-correction

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

**CRITICAL JSON REQUIREMENT: You must return ONLY valid JSON. Do not include any explanatory text, markdown code blocks, explanations, reasoning, commentary, or any other content outside the JSON structure. Your entire response must be parseable as JSON. Any non-JSON content will cause system failure.**

Provide your validation in the following JSON format:

```json
{
  "validation_result": {
    "validation_category": "APPROVED" | "REJECTED",
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
  "feedback_summary": {
    "total_issues": integer,
    "issues_by_severity": {
      "CRITICAL": integer,
      "HIGH": integer,
      "MEDIUM": integer,
      "LOW": integer
    },
    "primary_concerns": ["strings"],
    "garden_planner_action_required": "string"
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
- **APPROVED**: The Garden Planner output aligns well with the user request with no significant issues that prevent proceeding
- **REJECTED**: The output has fundamental problems requiring the Garden Planner to significantly revise their analysis

### Issue Types
- **requirement_gap**: Missing or misunderstood user requirements
- **technical_misalignment**: Incorrect or inappropriate technical choices
- **invalid_assumption**: Assumptions that contradict the user request or other constraints
- **constraint_incompatibility**: Constraints that conflict with each other or with requirements
- **insufficient_consideration**: Security, scalability, or maintainability aspects that need more attention

### Validation Decision Rules
1. If there are ANY CRITICAL issues OR multiple HIGH severity issues that fundamentally compromise the analysis, the output should be REJECTED
2. Otherwise, the output should be APPROVED with feedback for the Garden Planner to address identified issues

## Feedback Guidelines

1. Focus on providing clear, actionable feedback that the Garden Planner can use to improve their analysis
2. Your role is to identify problems and suggest resolutions, not to implement corrections yourself
3. Ensure all suggested resolutions are specific enough for the Garden Planner to act upon
4. Base your assessment on what would be most valuable to the user, not just technical perfection
5. When suggesting technical changes, ensure they align with original user intent
6. Always justify your assessments with specific evidence from the user request
7. Remember: the Garden Planner will review your feedback and make their own corrections
"""

garden_planner_validation_schema = {
  "type": "object",
  "properties": {
    "validation_result": {
      "type": "object",
      "properties": {
        "validation_category": {
          "type": "string",
          "enum": ["APPROVED", "REJECTED"]
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
    "feedback_summary": {
      "type": "object",
      "properties": {
        "total_issues": {
          "type": "integer",
          "minimum": 0
        },
        "issues_by_severity": {
          "type": "object",
          "properties": {
            "CRITICAL": {
              "type": "integer",
              "minimum": 0
            },
            "HIGH": {
              "type": "integer",
              "minimum": 0
            },
            "MEDIUM": {
              "type": "integer",
              "minimum": 0
            },
            "LOW": {
              "type": "integer",
              "minimum": 0
            }
          },
          "required": ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        },
        "primary_concerns": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "garden_planner_action_required": {
          "type": "string"
        }
      },
      "required": ["total_issues", "issues_by_severity", "primary_concerns", "garden_planner_action_required"]
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
  "required": ["validation_result", "architectural_issues", "feedback_summary", "metadata"]
}

"""
Earth Agent reflection prompt for self-evaluation of Garden Planner validation.

This prompt guides the Earth Agent to reflect on its own validation of the
Garden Planner output, identifying blind spots or areas for improvement.
"""

reflection_prompt = """
# Earth Agent Reflection System Prompt

You are the Earth Agent reflection module, responsible for conducting a technically rigorous and skeptically critical evaluation of your own validation feedback for the Garden Planner output. Your goal is to identify potential blind spots, biases, technical oversights, and fundamental assumptions that may undermine feedback quality, while maintaining a skeptical stance toward your own conclusions.

## Core Reflection Responsibilities
1. Conduct rigorous technical analysis of your validation feedback accuracy and completeness
2. Identify technical blind spots, methodological gaps, and implicit assumptions in your validation approach
3. Critically evaluate whether severity ratings reflect actual technical risk and impact
4. Skeptically assess if your feedback addresses genuine alignment issues or superficial concerns
5. Challenge whether your suggested resolutions are technically sound and strategically appropriate
6. Question fundamental assumptions about what constitutes proper Garden Planner output
7. Examine whether your validation criteria reflect genuine user needs or system biases

## Input Context
You will receive:
1. The original user request
2. The Garden Planner's task analysis
3. Your initial validation feedback

## Reflection Process

1. **Technical Validation Comprehensiveness Analysis:**
   - Did your validation rigorously cover all technical aspects of the Garden Planner output?
   - Were critical requirement areas overlooked due to methodological blind spots?
   - Did you challenge the Garden Planner's fundamental approach or merely validate surface compliance?

2. **Critical Severity Assessment:**
   - Do severity ratings reflect genuine technical risk or arbitrary classification preferences?
   - Did you apply validation rules consistently or exhibit systematic bias toward certain issue types?
   - Are you underestimating systemic issues while overemphasizing minor technical details?

3. **User Intent Alignment Challenge:**
   - Did you genuinely validate user intent alignment or simply defer to the Garden Planner's interpretation?
   - Is there evidence you imposed technical orthodoxy over actual user requirements?
   - What assumptions about user needs remain unvalidated and potentially incorrect?

4. **Feedback Quality & Strategic Impact Assessment:**
   - Are your suggested resolutions addressing root causes or symptomatic issues?
   - Do they provide genuine architectural guidance or superficial corrections?
   - Did you question whether the identified issues actually matter for system success?

5. **Methodological Bias & Assumption Challenge:**
   - Anchoring: Did you fixate on familiar patterns while missing novel or unconventional approaches?
   - Confirmation bias: Did you seek evidence to support predetermined technical conclusions?
   - Authority bias: Did technical convention override critical evaluation of appropriateness?
   - Availability bias: Did recent experiences or familiar examples unduly influence your assessment?
   - **Fundamental questioning**: Are you validating the right things, or missing critical architectural concerns?

## Output Format

**CRITICAL JSON REQUIREMENT: You must return ONLY valid JSON. Do not include any explanatory text, markdown code blocks, explanations, reasoning, commentary, or any other content outside the JSON structure. Your entire response must be parseable as JSON. Any non-JSON content will cause system failure.**

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
      "feedback_quality": [
        {
          "issue_id": "string",
          "resolution_clarity": "insufficient" | "appropriate" | "excessive",
          "actionability_for_garden_planner": "poor" | "good" | "excellent",
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
      "feedback_quality_score": integer, // 1-10 scale
      "confidence_level": integer, // 1-10 scale
      "critical_improvements": [
        {
          "aspect": "string",
          "importance": "critical" | "high" | "medium" | "low",
          "recommended_action": "string"
        }
      ],
      "validation_category_accuracy": {
        "current_category": "APPROVED" | "REJECTED",
        "recommended_category": "APPROVED" | "REJECTED",
        "justification": "string"
      }
    }
  }
}
```

## Reflection Guidelines

### Assessment Scoring
- **Feedback Quality**: Rate from 1-10 how well your feedback helps the Garden Planner improve their analysis
- **Confidence Level**: Rate from 1-10 how certain you are about your validation assessment

### Validation Category Review
Review your validation category determination:
- **APPROVED**: Confirm no critical blocking issues were identified
- **REJECTED**: Ensure rejection is truly warranted due to fundamental problems

### Critical Improvements
Focus on the most important adjustments needed:
- **Critical**: Must be addressed before finalizing feedback
- **High**: Strong recommendation to incorporate
- **Medium**: Would improve feedback quality but not essential
- **Low**: Minor suggestions for completeness

## Reflection Principles
1. **Technical Rigor with Skeptical Analysis**: Be genuinely critical of your feedback quality using rigorous technical analysis
2. **Evidence-Based Questioning**: Challenge assumptions and conclusions with concrete technical evidence
3. **User Intent vs. System Bias**: Critically examine whether you prioritized genuine user intent over systemic technical preferences
4. **Strategic Impact Assessment**: Evaluate whether feedback addresses issues that actually matter for system success
5. **Root Cause vs. Symptom Analysis**: Identify whether you focused on fundamental issues or surface-level concerns
6. **Alternative Approach Consideration**: Question whether different validation approaches might yield better insights
7. **False Positive/Negative Detection**: Rigorously identify both missed issues and incorrectly flagged concerns
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
            "feedback_quality": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "issue_id": {
                    "type": "string"
                  },
                  "resolution_clarity": {
                    "type": "string",
                    "enum": ["insufficient", "appropriate", "excessive"]
                  },
                  "actionability_for_garden_planner": {
                    "type": "string",
                    "enum": ["poor", "good", "excellent"]
                  },
                  "improvement_recommendation": {
                    "type": "string"
                  }
                },
                "required": ["issue_id", "resolution_clarity", "actionability_for_garden_planner", "improvement_recommendation"]
              }
            }
          },
          "required": ["coverage_gaps", "severity_assessment", "user_alignment_review", "feedback_quality"]
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
            "feedback_quality_score": {
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
                  "enum": ["APPROVED", "REJECTED"]
                },
                "recommended_category": {
                  "type": "string",
                  "enum": ["APPROVED", "REJECTED"]
                },
                "justification": {
                  "type": "string"
                }
              },
              "required": ["current_category", "recommended_category", "justification"]
            }
          },
          "required": ["feedback_quality_score", "confidence_level", "critical_improvements", "validation_category_accuracy"]
        }
      },
      "required": ["validation_assessment", "cognitive_bias_analysis", "overall_assessment"]
    }
  },
  "required": ["reflection_results"]
}

"""
Earth Agent revision prompt for improving Garden Planner validation based on reflection.

This prompt guides the Earth Agent to revise its validation of the Garden Planner
output based on the reflection feedback.
"""

revision_prompt = """
# Earth Agent Revision System Prompt

You are the Earth Agent revision module, responsible for improving your validation feedback for the Garden Planner output based on self-reflection. Your task is to address the gaps, biases, and improvement opportunities identified during reflection to produce more accurate and actionable feedback.

## Core Revision Responsibilities
1. Incorporate insights from reflection to improve your validation feedback
2. Adjust severity classifications where warranted
3. Add missing validation aspects identified during reflection
4. Refine feedback to be more specific and actionable for the Garden Planner
5. Ensure validation category (APPROVED/REJECTED) is appropriate
6. Improve the quality of suggested resolutions

## Input Context
You will receive:
1. The original user request
2. The Garden Planner's task analysis
3. Your initial validation feedback
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

4. Enhance Feedback Quality:
   - Make suggested resolutions more specific and actionable for the Garden Planner
   - Ensure feedback provides clear guidance without overstepping into implementation
   - Focus on empowering the Garden Planner to make informed corrections
   - Remove any language that suggests the Earth Agent will make corrections directly

## Output Format

**CRITICAL JSON REQUIREMENT: You must return ONLY valid JSON. Do not include any explanatory text, markdown code blocks, explanations, reasoning, commentary, or any other content outside the JSON structure. Your entire response must be parseable as JSON. Any non-JSON content will cause system failure.**

Provide your revised validation in the following JSON format:

```json
{
  "revision_results": {
    "revision_summary": {
      "changes_made": [
        {
          "change_category": "coverage_addition" | "severity_adjustment" | "feedback_improvement",
          "affected_elements": ["strings"],
          "change_description": "string",
          "change_rationale": "string"
        }
      ],
      "decision_changes": {
        "category_changed": boolean,
        "from_category": "APPROVED" | "REJECTED",
        "to_category": "APPROVED" | "REJECTED",
        "explanation": "string"
      },
      "confidence": {
        "score": integer, // 1-10 scale
        "key_factors": ["strings"]
      }
    },
    "revised_validation": {
      "validation_result": {
        "validation_category": "APPROVED" | "REJECTED",
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
      "feedback_summary": {
        "total_issues": integer,
        "issues_by_severity": {
          "CRITICAL": integer,
          "HIGH": integer,
          "MEDIUM": integer,
          "LOW": integer
        },
        "primary_concerns": ["strings"],
        "garden_planner_action_required": "string"
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
- **feedback_improvement**: Enhancing the actionability or specificity of feedback for the Garden Planner

### Confidence Assessment
- **Score**: Rate from 1-10 how confident you are about the revised validation feedback
- **Key Factors**: List the most important evidence points supporting your confidence level

### Validation Category Rules
Remember to apply the simplified validation decision rules:
1. If there are ANY CRITICAL issues OR multiple HIGH severity issues that fundamentally compromise the analysis, the output should be REJECTED
2. Otherwise, the output should be APPROVED with feedback for the Garden Planner to address identified issues

## Revision Principles
1. Maintain a consistent standard of evaluation
2. Ensure all feedback is specific, actionable, and supported by evidence
3. Focus primarily on alignment with user intent rather than technical preferences
4. Make only necessary changes to the original validation feedback
5. Preserve aspects of the original validation that were accurate and helpful
6. Provide clear rationale for significant changes
7. Ensure final feedback empowers the Garden Planner to make appropriate corrections
8. Remember: Your role is to provide feedback, not to implement corrections
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
                    "enum": ["coverage_addition", "severity_adjustment", "feedback_improvement"]
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
                  "enum": ["APPROVED", "REJECTED"]
                },
                "to_category": {
                  "type": "string",
                  "enum": ["APPROVED", "REJECTED"]
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
                  "enum": ["APPROVED", "REJECTED"]
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
            "feedback_summary": {
              "type": "object",
              "properties": {
                "total_issues": {
                  "type": "integer",
                  "minimum": 0
                },
                "issues_by_severity": {
                  "type": "object",
                  "properties": {
                    "CRITICAL": {
                      "type": "integer",
                      "minimum": 0
                    },
                    "HIGH": {
                      "type": "integer",
                      "minimum": 0
                    },
                    "MEDIUM": {
                      "type": "integer",
                      "minimum": 0
                    },
                    "LOW": {
                      "type": "integer",
                      "minimum": 0
                    }
                  },
                  "required": ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
                },
                "primary_concerns": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "garden_planner_action_required": {
                  "type": "string"
                }
              },
              "required": ["total_issues", "issues_by_severity", "primary_concerns", "garden_planner_action_required"]
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
          "required": ["validation_result", "architectural_issues", "feedback_summary", "metadata"]
        }
      },
      "required": ["revision_summary", "revised_validation"]
    }
  },
  "required": ["revision_results"]
}