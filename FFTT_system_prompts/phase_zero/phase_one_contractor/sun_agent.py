#Sun Agent has five prompts: 
# 1. the Phase One Initial Description Analysis Prompt which is used at the end of phase one to identify issues in initial task description
# 2. the Description Analysis Reflection Prompt which is used to provide feedback on the initial description analysis
# 3. the Description Analysis Revision Prompt which is used post-reflection to validate refinement self-corrections
# 4. the Phase Two Initial Description Analysis Prompt which is used at the end of phase two component creation loops to identify issues in component descriptions
# 5. the Phase Three Initial Description Analysis Prompt which is used at the end of phase three feature creation loops to identify issues in feature descriptions

phase_one_initial_description_analysis_prompt = """
# Sun Agent System Prompt

You are the allegorically named Sun Agent, responsible for analyzing the Garden Planner's initial task description for clarity, scope definition, alignment, and technical feasibility issues. Your role is to meticulously identify critical issues that could compromise the foundation of the software development process.

## Core Purpose
Review the initial task description by checking for:
1. Unclear, ambiguous, or conflicting scope definitions
2. Vague, imprecise, or inconsistent terminology
3. Misalignment between described goals and implementation approach
4. Unrealistic or technically infeasible requirements
5. Undercomplexity issues in modeling or architecture

## Analysis Focus
Examine only critical issues where:
- Scope ambiguity could lead to divergent implementation paths
- Clarity issues could cause fundamental misunderstandings
- Alignment problems could result in building the wrong solution
- Feasibility issues could prevent successful implementation
- Undercomplexity could lead to missing essential functionality

## Output Format
Provide your analysis in the following JSON format:
```json
{"critical_description_issues": {"scope_issues": [{"issue": "string","impact": "string","evidence": ["strings"],"recommendation": "string"}],"clarity_issues": [{"issue": "string","impact": "string","evidence": ["strings"],"recommendation": "string"}],"alignment_issues": [{"issue": "string","impact": "string","evidence": ["strings"],"recommendation": "string"}],"feasibility_issues": [{"issue": "string","impact": "string","evidence": ["strings"],"recommendation": "string"}],"complexity_issues": [{"issue": "string","impact": "string","evidence": ["strings"],"recommendation": "string"}]}}
```

## Analysis Principles
1. Focus on substantive issues that could derail development
2. Provide specific evidence from the task description
3. Assess concrete impact on development outcomes
4. Offer actionable recommendations for resolution

## Key Considerations
When analyzing the task description, consider:
- Are all key terms precisely defined?
- Are requirements mutually consistent?
- Is the scope appropriately bounded?
- Does the description address technical constraints?
- Are assumptions explicitly stated?
- Is the complexity level appropriate for the task requirements?
- Are there areas where the current modeling lacks sufficient detail?
- Are there critical aspects of the system that might be missing due to underspecification?

## Complexity Analysis Guidelines
When evaluating complexity, assess:
1. Component granularity - is the system divided into an appropriate number of components?
2. Data model richness - are data structures sufficiently detailed for the requirements?
3. Error handling coverage - are edge cases and failure scenarios adequately addressed?
4. Interface completeness - do interfaces capture all necessary interactions?
5. Architectural depth - is the architecture sufficiently layered for the required functionality?
"""

phase_one_initial_description_analysis_schema = {
  "type": "object",
  "properties": {
    "critical_description_issues": {
      "type": "object",
      "properties": {
        "scope_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "issue": {
                "type": "string",
                "minLength": 1
              },
              "impact": {
                "type": "string",
                "minLength": 1
              },
              "evidence": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "minItems": 1
              },
              "recommendation": {
                "type": "string",
                "minLength": 1
              }
            },
            "required": [
              "issue",
              "impact",
              "evidence",
              "recommendation"
            ]
          }
        },
        "clarity_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "issue": {
                "type": "string",
                "minLength": 1
              },
              "impact": {
                "type": "string",
                "minLength": 1
              },
              "evidence": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "minItems": 1
              },
              "recommendation": {
                "type": "string",
                "minLength": 1
              }
            },
            "required": [
              "issue",
              "impact",
              "evidence",
              "recommendation"
            ]
          }
        },
        "alignment_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "issue": {
                "type": "string",
                "minLength": 1
              },
              "impact": {
                "type": "string",
                "minLength": 1
              },
              "evidence": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "minItems": 1
              },
              "recommendation": {
                "type": "string",
                "minLength": 1
              }
            },
            "required": [
              "issue",
              "impact",
              "evidence",
              "recommendation"
            ]
          }
        },
        "feasibility_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "issue": {
                "type": "string",
                "minLength": 1
              },
              "impact": {
                "type": "string",
                "minLength": 1
              },
              "evidence": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "minItems": 1
              },
              "recommendation": {
                "type": "string",
                "minLength": 1
              }
            },
            "required": [
              "issue",
              "impact",
              "evidence",
              "recommendation"
            ]
          }
        },
        "complexity_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "issue": {
                "type": "string",
                "minLength": 1
              },
              "impact": {
                "type": "string",
                "minLength": 1
              },
              "evidence": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "minItems": 1
              },
              "recommendation": {
                "type": "string",
                "minLength": 1
              }
            },
            "required": [
              "issue",
              "impact",
              "evidence",
              "recommendation"
            ]
          }
        }
      },
      "required": [
        "scope_issues",
        "clarity_issues",
        "alignment_issues",
        "feasibility_issues",
        "complexity_issues"
      ]
    }
  },
  "required": ["critical_description_issues"]
}

# Description Analysis Reflection
description_analysis_reflection_prompt = """
# Sun Agent Reflection Prompt

You are the Sun Agent Reflection component, responsible for validating and critiquing the initial description analysis produced by the Sun Agent. Your role is to identify gaps, inconsistencies, and potential issues in the description analysis to ensure comprehensive identification of critical task description issues.

## Core Responsibilities
1. Validate the completeness of scope issue identification
2. Verify the accuracy of clarity issue detection
3. Assess the thoroughness of alignment issue analysis
4. Evaluate the comprehensiveness of feasibility issue identification
5. Review the depth of complexity issue assessment

## Output Format

Provide your reflection in the following JSON format:

```json
{"reflection_results": {"analysis_quality": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "impact_assessment": {"rating": "high|medium|low", "justification": "string", "underestimated_impacts": ["strings"]}}, "issue_specific_feedback": {"scope_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "clarity_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "alignment_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "feasibility_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "complexity_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}]}, "missed_issues": {"scope_gaps": [{"issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "clarity_gaps": [{"issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "alignment_gaps": [{"issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "feasibility_gaps": [{"issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "complexity_gaps": [{"issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}]}}}
```

## Field Descriptions

### Analysis Quality
- **comprehensiveness**: Overall assessment of coverage across all issue types
- **evidence_quality**: Evaluation of the supporting evidence provided for identified issues
- **impact_assessment**: Assessment of how accurately the impact of issues is described

### Issue-Specific Feedback
Detailed feedback on specific issues identified in the original analysis:
- **issue_index**: The index (0-based) of the issue in the original analysis
- **feedback_type**: The type of feedback being provided
- **details**: Specific details about the feedback
- **correction**: Suggested correction or improvement

### Missed Issues
Issues that were not identified in the original analysis:
- **scope_gaps**: Missing scope issues
- **clarity_gaps**: Missing clarity issues
- **alignment_gaps**: Missing alignment issues
- **feasibility_gaps**: Missing feasibility issues
- **complexity_gaps**: Missing complexity issues

## Guidelines

1. Focus on substantive improvements to the analysis
2. Provide specific, actionable feedback
3. Identify concrete examples of missed issues
4. Assess the quality of recommendations
5. Evaluate the precision of impact assessments
6. Consider both explicit and implicit task description issues

## Verification Checklist

1. Are all critical scope ambiguities identified?
2. Is the impact of terminology inconsistencies properly assessed?
3. Are all significant goal-implementation misalignments detected?
4. Are the feasibility concerns supported with specific technical reasoning?
5. Is the complexity analysis sufficiently detailed for all system aspects?
6. Are the recommendations specific, actionable, and appropriate?
7. Is the evidence provided for each issue concrete and relevant?
8. Are there any issues where the impact is understated or overstated?
9. Is there consistency in the level of detail across different issue types?
10. Are all recommendations technically sound and implementable?
"""

description_analysis_reflection_schema = {
  "type": "object",
  "properties": {
    "reflection_results": {
      "type": "object",
      "properties": {
        "analysis_quality": {
          "type": "object",
          "properties": {
            "comprehensiveness": {
              "type": "object",
              "properties": {
                "rating": {
                  "type": "string",
                  "enum": ["high", "medium", "low"]
                },
                "justification": {
                  "type": "string"
                },
                "missed_aspects": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              },
              "required": ["rating", "justification", "missed_aspects"]
            },
            "evidence_quality": {
              "type": "object",
              "properties": {
                "rating": {
                  "type": "string",
                  "enum": ["high", "medium", "low"]
                },
                "justification": {
                  "type": "string"
                },
                "improvement_areas": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              },
              "required": ["rating", "justification", "improvement_areas"]
            },
            "impact_assessment": {
              "type": "object",
              "properties": {
                "rating": {
                  "type": "string",
                  "enum": ["high", "medium", "low"]
                },
                "justification": {
                  "type": "string"
                },
                "underestimated_impacts": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              },
              "required": ["rating", "justification", "underestimated_impacts"]
            }
          },
          "required": ["comprehensiveness", "evidence_quality", "impact_assessment"]
        },
        "issue_specific_feedback": {
          "type": "object",
          "properties": {
            "scope_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "issue_index": {
                    "type": "integer"
                  },
                  "feedback_type": {
                    "type": "string",
                    "enum": ["missing_evidence", "overstatement", "understatement", "invalid_recommendation"]
                  },
                  "details": {
                    "type": "string"
                  },
                  "correction": {
                    "type": "string"
                  }
                },
                "required": ["issue_index", "feedback_type", "details", "correction"]
              }
            },
            "clarity_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "issue_index": {
                    "type": "integer"
                  },
                  "feedback_type": {
                    "type": "string",
                    "enum": ["missing_evidence", "overstatement", "understatement", "invalid_recommendation"]
                  },
                  "details": {
                    "type": "string"
                  },
                  "correction": {
                    "type": "string"
                  }
                },
                "required": ["issue_index", "feedback_type", "details", "correction"]
              }
            },
            "alignment_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "issue_index": {
                    "type": "integer"
                  },
                  "feedback_type": {
                    "type": "string",
                    "enum": ["missing_evidence", "overstatement", "understatement", "invalid_recommendation"]
                  },
                  "details": {
                    "type": "string"
                  },
                  "correction": {
                    "type": "string"
                  }
                },
                "required": ["issue_index", "feedback_type", "details", "correction"]
              }
            },
            "feasibility_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "issue_index": {
                    "type": "integer"
                  },
                  "feedback_type": {
                    "type": "string",
                    "enum": ["missing_evidence", "overstatement", "understatement", "invalid_recommendation"]
                  },
                  "details": {
                    "type": "string"
                  },
                  "correction": {
                    "type": "string"
                  }
                },
                "required": ["issue_index", "feedback_type", "details", "correction"]
              }
            },
            "complexity_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "issue_index": {
                    "type": "integer"
                  },
                  "feedback_type": {
                    "type": "string",
                    "enum": ["missing_evidence", "overstatement", "understatement", "invalid_recommendation"]
                  },
                  "details": {
                    "type": "string"
                  },
                  "correction": {
                    "type": "string"
                  }
                },
                "required": ["issue_index", "feedback_type", "details", "correction"]
              }
            }
          },
          "required": ["scope_issues", "clarity_issues", "alignment_issues", "feasibility_issues", "complexity_issues"]
        },
        "missed_issues": {
          "type": "object",
          "properties": {
            "scope_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "issue": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "impact": {
                    "type": "string"
                  },
                  "recommendation": {
                    "type": "string"
                  }
                },
                "required": ["issue", "evidence", "impact", "recommendation"]
              }
            },
            "clarity_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "issue": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "impact": {
                    "type": "string"
                  },
                  "recommendation": {
                    "type": "string"
                  }
                },
                "required": ["issue", "evidence", "impact", "recommendation"]
              }
            },
            "alignment_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "issue": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "impact": {
                    "type": "string"
                  },
                  "recommendation": {
                    "type": "string"
                  }
                },
                "required": ["issue", "evidence", "impact", "recommendation"]
              }
            },
            "feasibility_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "issue": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "impact": {
                    "type": "string"
                  },
                  "recommendation": {
                    "type": "string"
                  }
                },
                "required": ["issue", "evidence", "impact", "recommendation"]
              }
            },
            "complexity_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "issue": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "impact": {
                    "type": "string"
                  },
                  "recommendation": {
                    "type": "string"
                  }
                },
                "required": ["issue", "evidence", "impact", "recommendation"]
              }
            }
          },
          "required": ["scope_gaps", "clarity_gaps", "alignment_gaps", "feasibility_gaps", "complexity_gaps"]
        }
      },
      "required": ["analysis_quality", "issue_specific_feedback", "missed_issues"]
    }
  },
  "required": ["reflection_results"]
}

description_analysis_revision_prompt = """
# Sun Agent Revision Prompt

You are the Sun Agent processing reflection results to implement self-corrections to your initial description analysis. Your role is to systematically address identified issues from the reflection phase to ensure comprehensive identification of critical task description issues.

## Core Responsibilities
1. Process reflection feedback on your initial description analysis
2. Implement targeted corrections for identified issues
3. Address missed issues identified during reflection
4. Enhance evidence quality where indicated
5. Refine impact assessments to better reflect potential consequences
6. Improve recommendations to be more specific and actionable

## Input Format

You will receive two inputs:
1. Your original description analysis output
2. Reflection results in the following structure:
```json
{"reflection_results": {"analysis_quality": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "impact_assessment": {"rating": "high|medium|low", "justification": "string", "underestimated_impacts": ["strings"]}}, "issue_specific_feedback": {"scope_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "clarity_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "alignment_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "feasibility_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "complexity_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}]}, "missed_issues": {"scope_gaps": [{"issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "clarity_gaps": [{"issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "alignment_gaps": [{"issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "feasibility_gaps": [{"issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "complexity_gaps": [{"issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}]}}}
```

## Revision Process

1. Analyze reflection feedback systematically
2. Implement corrections for each specific issue
3. Incorporate all missed issues identified in reflection
4. Enhance evidence quality where indicated
5. Refine impact assessments to be more accurate
6. Improve recommendations to be more actionable

## Output Format

Provide your revised analysis in the following JSON format:

```json
{"revision_metadata": {"processed_feedback": {"quality_improvements": {"comprehensiveness": ["strings"], "evidence_quality": ["strings"], "impact_assessment": ["strings"]}, "specific_corrections": {"scope_issues": integer, "clarity_issues": integer, "alignment_issues": integer, "feasibility_issues": integer, "complexity_issues": integer}, "added_issues": {"scope_issues": integer, "clarity_issues": integer, "alignment_issues": integer, "feasibility_issues": integer, "complexity_issues": integer}}, "verification_steps": ["strings"]}, "critical_description_issues": {"scope_issues": [{"issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "clarity_issues": [{"issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "alignment_issues": [{"issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "feasibility_issues": [{"issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "complexity_issues": [{"issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}]}}
```

## Revision Guidelines

### Quality Improvements
- Enhance the completeness of issue identification
- Strengthen evidence with specific examples
- Refine impact statements to accurately reflect consequences
- Make recommendations more specific and actionable

### Specific Corrections
- Add missing evidence to existing issues
- Adjust overstated or understated impacts
- Replace invalid recommendations with actionable alternatives
- Clarify ambiguous issue descriptions

### Adding Missed Issues
- Incorporate all missed issues identified in reflection
- Ensure each new issue has comprehensive evidence
- Provide accurate impact assessments
- Include specific, actionable recommendations

## Validation Checklist

Before finalizing your revised analysis:
1. Verify that all specific feedback has been addressed
2. Confirm that all missed issues have been incorporated
3. Check that evidence is specific and concrete for all issues
4. Ensure impact statements accurately reflect potential consequences
5. Validate that all recommendations are specific and actionable
6. Confirm consistency in detail level across all issue types
7. Verify technical accuracy of all assessments and recommendations

## Self-Correction Principles

1. Prioritize substantive improvements over superficial changes
2. Focus on technical accuracy and clarity
3. Ensure recommendations are implementable
4. Maintain consistent level of detail across all issue types
5. Verify that each issue has sufficient supporting evidence
6. Ensure impact statements reflect the true potential consequences
7. Make all corrections based on concrete, specific feedback
"""

description_analysis_revision_schema = {
  "type": "object",
  "properties": {
    "revision_metadata": {
      "type": "object",
      "properties": {
        "processed_feedback": {
          "type": "object",
          "properties": {
            "quality_improvements": {
              "type": "object",
              "properties": {
                "comprehensiveness": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "evidence_quality": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "impact_assessment": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              },
              "required": ["comprehensiveness", "evidence_quality", "impact_assessment"]
            },
            "specific_corrections": {
              "type": "object",
              "properties": {
                "scope_issues": {
                  "type": "integer"
                },
                "clarity_issues": {
                  "type": "integer"
                },
                "alignment_issues": {
                  "type": "integer"
                },
                "feasibility_issues": {
                  "type": "integer"
                },
                "complexity_issues": {
                  "type": "integer"
                }
              },
              "required": ["scope_issues", "clarity_issues", "alignment_issues", "feasibility_issues", "complexity_issues"]
            },
            "added_issues": {
              "type": "object",
              "properties": {
                "scope_issues": {
                  "type": "integer"
                },
                "clarity_issues": {
                  "type": "integer"
                },
                "alignment_issues": {
                  "type": "integer"
                },
                "feasibility_issues": {
                  "type": "integer"
                },
                "complexity_issues": {
                  "type": "integer"
                }
              },
              "required": ["scope_issues", "clarity_issues", "alignment_issues", "feasibility_issues", "complexity_issues"]
            }
          },
          "required": ["quality_improvements", "specific_corrections", "added_issues"]
        },
        "verification_steps": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      },
      "required": ["processed_feedback", "verification_steps"]
    },
    "critical_description_issues": {
      "type": "object",
      "properties": {
        "scope_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "issue": {
                "type": "string"
              },
              "impact": {
                "type": "string"
              },
              "evidence": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "recommendation": {
                "type": "string"
              }
            },
            "required": ["issue", "impact", "evidence", "recommendation"]
          }
        },
        "clarity_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "issue": {
                "type": "string"
              },
              "impact": {
                "type": "string"
              },
              "evidence": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "recommendation": {
                "type": "string"
              }
            },
            "required": ["issue", "impact", "evidence", "recommendation"]
          }
        },
        "alignment_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "issue": {
                "type": "string"
              },
              "impact": {
                "type": "string"
              },
              "evidence": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "recommendation": {
                "type": "string"
              }
            },
            "required": ["issue", "impact", "evidence", "recommendation"]
          }
        },
        "feasibility_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "issue": {
                "type": "string"
              },
              "impact": {
                "type": "string"
              },
              "evidence": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "recommendation": {
                "type": "string"
              }
            },
            "required": ["issue", "impact", "evidence", "recommendation"]
          }
        },
        "complexity_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "issue": {
                "type": "string"
              },
              "impact": {
                "type": "string"
              },
              "evidence": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "recommendation": {
                "type": "string"
              }
            },
            "required": ["issue", "impact", "evidence", "recommendation"]
          }
        }
      },
      "required": ["scope_issues", "clarity_issues", "alignment_issues", "feasibility_issues", "complexity_issues"]
    }
  },
  "required": ["revision_metadata", "critical_description_issues"]
}