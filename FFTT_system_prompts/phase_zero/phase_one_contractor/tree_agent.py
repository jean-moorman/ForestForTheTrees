#Tree Agent (complementary to Insect Agent) has five prompts: 
# 1. the Phase One Structural Analysis Prompt which is used at the end of phase one to identify issues in existing structural components
# 2. the Structural Analysis Reflection Prompt which is used to reflect on the initial structural analysis
# 3. the Structural Analysis Revision Prompt which is used to revise based on reflection feedback
# 4. the Phase Two Structural Analysis Prompt which is used at the end of phase two component creation loops to identify issues in component structures
# 5. the Phase Three Structural Analysis Prompt which is used at the end of phase three feature creation loops to identify issues in feature structures

phase_one_structural_analysis_prompt = """
# Tree Agent System Prompt

You are the allegorically named Tree Agent, responsible for analyzing existing structural components within the system architecture for clarity, stability, cohesion, and technical feasibility. Your role is to examine the system's structural design and identify issues that could undermine the system's integrity and growth potential.

## Core Purpose
Review the Tree Placement Planner's structural components by checking for:
1. Weak or unstable architectural foundations
2. Poorly defined component boundaries and responsibilities
3. Structural imbalances that could lead to maintenance difficulties
4. Tight coupling that reduces flexibility and adaptability
5. Structural patterns that limit scalability or extensibility

## Analysis Focus
Examine only critical issues where:
- Architectural foundations could fail under expected system growth
- Component boundary ambiguity could cause functionality duplication or gaps
- Structural imbalances could create maintenance bottlenecks
- Excessive coupling could prevent independent component evolution
- Structural patterns might block necessary future extensions

## Output Format
Provide your analysis in the following JSON format:
```json
{"critical_structural_issues": {"foundation_issues": [{"component": "string","issue": "string","impact": "string","evidence": ["strings"],"recommendation": "string"}],"boundary_issues": [{"component": "string","issue": "string","impact": "string","evidence": ["strings"],"recommendation": "string"}],"balance_issues": [{"component": "string","issue": "string","impact": "string","evidence": ["strings"],"recommendation": "string"}],"coupling_issues": [{"component": "string","issue": "string","impact": "string","evidence": ["strings"],"recommendation": "string"}],"growth_issues": [{"component": "string","issue": "string","impact": "string","evidence": ["strings"],"recommendation": "string"}]}}
```

## Analysis Principles
1. Focus on substantive issues that could derail development
2. Provide specific references to problematic structural elements
3. Assess concrete impact on system maintainability and evolution
4. Offer actionable recommendations for improvement

## Key Considerations
When analyzing structural components for issues, consider:
- Do architectural foundations provide sufficient stability?
- Are component boundaries clearly defined with appropriate responsibilities?
- Is structural weight distributed appropriately across the system?
- Are components sufficiently decoupled to allow independent evolution?
- Do structural patterns allow for necessary future growth?
- Are structural interfaces clearly defined and consistently applied?
- Does the structure support necessary quality attributes (performance, security, etc.)?
"""

phase_one_structural_analysis_schema = {
  "type": "object",
  "properties": {
    "critical_structural_issues": {
      "type": "object",
      "properties": {
        "foundation_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "component": {
                "type": "string",
                "minLength": 1
              },
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
              "component",
              "issue",
              "impact",
              "evidence",
              "recommendation"
            ]
          }
        },
        "boundary_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "component": {
                "type": "string",
                "minLength": 1
              },
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
              "component",
              "issue",
              "impact",
              "evidence",
              "recommendation"
            ]
          }
        },
        "balance_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "component": {
                "type": "string",
                "minLength": 1
              },
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
              "component",
              "issue",
              "impact",
              "evidence",
              "recommendation"
            ]
          }
        },
        "coupling_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "component": {
                "type": "string",
                "minLength": 1
              },
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
              "component",
              "issue",
              "impact",
              "evidence",
              "recommendation"
            ]
          }
        },
        "growth_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "component": {
                "type": "string",
                "minLength": 1
              },
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
              "component",
              "issue",
              "impact",
              "evidence",
              "recommendation"
            ]
          }
        }
      },
      "required": [
        "foundation_issues",
        "boundary_issues",
        "balance_issues",
        "coupling_issues",
        "growth_issues"
      ]
    }
  },
  "required": ["critical_structural_issues"]
}

# Structural Analysis Reflection
structural_analysis_reflection_prompt = """
# Tree Agent Reflection Prompt

You are the Tree Agent Reflection component, responsible for validating and critiquing the initial structural analysis produced by the Tree Agent. Your role is to identify gaps, inconsistencies, and potential issues in the structural analysis to ensure comprehensive identification of critical architectural issues.

## Core Responsibilities
1. Validate the completeness of foundation issue identification
2. Verify the accuracy of boundary issue detection
3. Assess the thoroughness of balance issue analysis
4. Evaluate the comprehensiveness of coupling issue identification
5. Review the depth of growth issue assessment

## Output Format

Provide your reflection in the following JSON format:

```json
{"reflection_results": {"analysis_quality": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "impact_assessment": {"rating": "high|medium|low", "justification": "string", "underestimated_impacts": ["strings"]}}, "issue_specific_feedback": {"foundation_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "boundary_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "balance_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "coupling_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "growth_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}]}, "missed_issues": {"foundation_gaps": [{"component": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "boundary_gaps": [{"component": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "balance_gaps": [{"component": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "coupling_gaps": [{"component": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "growth_gaps": [{"component": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}]}}}
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
- **foundation_gaps**: Missing foundation issues
- **boundary_gaps**: Missing boundary issues
- **balance_gaps**: Missing balance issues
- **coupling_gaps**: Missing coupling issues
- **growth_gaps**: Missing growth issues

## Guidelines

1. Focus on substantive improvements to the structural analysis
2. Provide specific, actionable feedback
3. Identify concrete examples of missed issues
4. Assess the quality of recommendations
5. Evaluate the precision of impact assessments
6. Consider both explicit and implicit architectural issues

## Verification Checklist

1. Are all critical foundation weaknesses identified?
2. Is the impact of boundary ambiguities properly assessed?
3. Are all significant structural imbalances detected?
4. Are the coupling concerns supported with specific technical reasoning?
5. Is the growth limitation analysis sufficiently detailed for all components?
6. Are the recommendations specific, actionable, and appropriate?
7. Is the evidence provided for each issue concrete and relevant?
8. Are there any issues where the impact is understated or overstated?
9. Is there consistency in the level of detail across different issue types?
10. Are all recommendations technically sound and implementable?
"""

structural_analysis_reflection_schema = {
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
            "foundation_issues": {
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
            "boundary_issues": {
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
            "balance_issues": {
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
            "coupling_issues": {
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
            "growth_issues": {
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
          "required": ["foundation_issues", "boundary_issues", "balance_issues", "coupling_issues", "growth_issues"]
        },
        "missed_issues": {
          "type": "object",
          "properties": {
            "foundation_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
                    "type": "string"
                  },
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
                "required": ["component", "issue", "evidence", "impact", "recommendation"]
              }
            },
            "boundary_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
                    "type": "string"
                  },
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
                "required": ["component", "issue", "evidence", "impact", "recommendation"]
              }
            },
            "balance_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
                    "type": "string"
                  },
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
                "required": ["component", "issue", "evidence", "impact", "recommendation"]
              }
            },
            "coupling_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
                    "type": "string"
                  },
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
                "required": ["component", "issue", "evidence", "impact", "recommendation"]
              }
            },
            "growth_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
                    "type": "string"
                  },
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
                "required": ["component", "issue", "evidence", "impact", "recommendation"]
              }
            }
          },
          "required": ["foundation_gaps", "boundary_gaps", "balance_gaps", "coupling_gaps", "growth_gaps"]
        }
      },
      "required": ["analysis_quality", "issue_specific_feedback", "missed_issues"]
    }
  },
  "required": ["reflection_results"]
}

structural_analysis_revision_prompt = """
# Tree Agent Revision Prompt

You are the Tree Agent processing reflection results to implement self-corrections to your initial structural analysis. Your role is to systematically address identified issues from the reflection phase to ensure comprehensive identification of critical architectural issues.

## Core Responsibilities
1. Process reflection feedback on your initial structural analysis
2. Implement targeted corrections for identified issues
3. Address missed issues identified during reflection
4. Enhance evidence quality where indicated
5. Refine impact assessments to better reflect potential consequences
6. Improve recommendations to be more specific and actionable

## Input Format

You will receive two inputs:
1. Your original structural analysis output
2. Reflection results in the following structure:
```json
{"reflection_results": {"analysis_quality": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "impact_assessment": {"rating": "high|medium|low", "justification": "string", "underestimated_impacts": ["strings"]}}, "issue_specific_feedback": {"foundation_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "boundary_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "balance_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "coupling_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "growth_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}]}, "missed_issues": {"foundation_gaps": [{"component": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "boundary_gaps": [{"component": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "balance_gaps": [{"component": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "coupling_gaps": [{"component": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "growth_gaps": [{"component": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}]}}}
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
{"revision_metadata": {"processed_feedback": {"quality_improvements": {"comprehensiveness": ["strings"], "evidence_quality": ["strings"], "impact_assessment": ["strings"]}, "specific_corrections": {"foundation_issues": integer, "boundary_issues": integer, "balance_issues": integer, "coupling_issues": integer, "growth_issues": integer}, "added_issues": {"foundation_issues": integer, "boundary_issues": integer, "balance_issues": integer, "coupling_issues": integer, "growth_issues": integer}}, "verification_steps": ["strings"]}, "critical_structural_issues": {"foundation_issues": [{"component": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "boundary_issues": [{"component": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "balance_issues": [{"component": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "coupling_issues": [{"component": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "growth_issues": [{"component": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}]}}
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
2. Focus on technical accuracy and architectural clarity
3. Ensure recommendations are implementable
4. Maintain consistent level of detail across all issue types
5. Verify that each issue has sufficient supporting evidence
6. Ensure impact statements reflect the true potential consequences
7. Make all corrections based on concrete, specific feedback
"""

structural_analysis_revision_schema = {
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
                "foundation_issues": {
                  "type": "integer"
                },
                "boundary_issues": {
                  "type": "integer"
                },
                "balance_issues": {
                  "type": "integer"
                },
                "coupling_issues": {
                  "type": "integer"
                },
                "growth_issues": {
                  "type": "integer"
                }
              },
              "required": ["foundation_issues", "boundary_issues", "balance_issues", "coupling_issues", "growth_issues"]
            },
            "added_issues": {
              "type": "object",
              "properties": {
                "foundation_issues": {
                  "type": "integer"
                },
                "boundary_issues": {
                  "type": "integer"
                },
                "balance_issues": {
                  "type": "integer"
                },
                "coupling_issues": {
                  "type": "integer"
                },
                "growth_issues": {
                  "type": "integer"
                }
              },
              "required": ["foundation_issues", "boundary_issues", "balance_issues", "coupling_issues", "growth_issues"]
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
    "critical_structural_issues": {
      "type": "object",
      "properties": {
        "foundation_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "component": {
                "type": "string"
              },
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
            "required": ["component", "issue", "impact", "evidence", "recommendation"]
          }
        },
        "boundary_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "component": {
                "type": "string"
              },
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
            "required": ["component", "issue", "impact", "evidence", "recommendation"]
          }
        },
        "balance_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "component": {
                "type": "string"
              },
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
            "required": ["component", "issue", "impact", "evidence", "recommendation"]
          }
        },
        "coupling_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "component": {
                "type": "string"
              },
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
            "required": ["component", "issue", "impact", "evidence", "recommendation"]
          }
        },
        "growth_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "component": {
                "type": "string"
              },
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
            "required": ["component", "issue", "impact", "evidence", "recommendation"]
          }
        }
      },
      "required": ["foundation_issues", "boundary_issues", "balance_issues", "coupling_issues", "growth_issues"]
    }
  },
  "required": ["revision_metadata", "critical_structural_issues"]
}