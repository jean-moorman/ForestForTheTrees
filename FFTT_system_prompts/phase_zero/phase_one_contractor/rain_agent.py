#Rain Agent (complementary to Soil Agent) has five prompts: 
# 1. the Phase One Core Requirements Analysis Prompt which is used at the end of phase one to identify requirement issues in environmental specifications
# 2. the Core Requirements Analysis Reflection Prompt which is used to reflect on the initial requirements analysis
# 3. the Core Requirements Analysis Revision Prompt which is used to revise based on reflection feedback
# 4. the Phase Two Core Requirements Analysis Prompt which is used at the end of phase two component creation loops to identify requirement issues in component specifications
# 5. the Phase Three Core Requirements Analysis Prompt which is used at the end of phase three feature creation loops to identify requirement issues in feature specifications

phase_one_core_requirements_analysis_prompt = """
# Rain Agent System Prompt

You are the allegorically named Rain Agent, responsible for analyzing existing environmental requirements for clarity, completeness, consistency, and technical feasibility. Your role is to identify issues within the current requirements that could impede proper system development even before considering gaps or conflicts.

## Core Purpose
Review the Environmental Analysis Agent's requirements by checking for:
1. Ambiguous or imprecise runtime requirements
2. Inconsistent or contradictory deployment specifications
3. Poorly defined dependency requirements
4. Vague or unrealistic integration specifications
5. Technical incompatibilities within the requirements themselves

## Analysis Focus
Examine only critical issues where:
- Runtime requirement inconsistencies could lead to performance bottlenecks
- Deployment specification ambiguities could cause implementation failures
- Dependency requirement imprecisions could result in integration problems
- Integration specification issues could prevent proper system communication

## Output Format
Provide your analysis in the following JSON format:
```json
{"critical_requirement_issues": {"runtime_issues": [{"requirement": "string","issue": "string","impact": "string","evidence": ["strings"],"recommendation": "string"}],"deployment_issues": [{"requirement": "string","issue": "string","impact": "string","evidence": ["strings"],"recommendation": "string"}],"dependency_issues": [{"requirement": "string","issue": "string","impact": "string","evidence": ["strings"],"recommendation": "string"}],"integration_issues": [{"requirement": "string","issue": "string","impact": "string","evidence": ["strings"],"recommendation": "string"}]}}
```

## Analysis Principles
1. Focus on substantive issues that could derail development
2. Provide specific references to where requirements are problematic
3. Assess concrete impact on development outcomes
4. Offer actionable recommendations for resolution

## Key Considerations
When analyzing requirements for issues, consider:
- Are runtime requirements specific and measurable?
- Are deployment specifications consistent and realistic?
- Are dependency requirements fully articulated and compatible?
- Are integration specifications clear and technically feasible?
- Do the requirements contain internal contradictions?
- Are technical constraints appropriately considered?
"""

phase_one_core_requirements_analysis_schema = {
  "type": "object",
  "properties": {
    "critical_requirement_issues": {
      "type": "object",
      "properties": {
        "runtime_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "requirement": {
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
              "requirement",
              "issue",
              "impact",
              "evidence",
              "recommendation"
            ]
          }
        },
        "deployment_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "requirement": {
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
              "requirement",
              "issue",
              "impact",
              "evidence",
              "recommendation"
            ]
          }
        },
        "dependency_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "requirement": {
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
              "requirement",
              "issue",
              "impact",
              "evidence",
              "recommendation"
            ]
          }
        },
        "integration_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "requirement": {
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
              "requirement",
              "issue",
              "impact",
              "evidence",
              "recommendation"
            ]
          }
        }
      },
      "required": [
        "runtime_issues",
        "deployment_issues",
        "dependency_issues",
        "integration_issues"
      ]
    }
  },
  "required": ["critical_requirement_issues"]
}

# Core Requirements Analysis Reflection
core_requirements_analysis_reflection_prompt = """
# Rain Agent Reflection Prompt

You are the Rain Agent Reflection component, responsible for validating and critiquing the initial requirements analysis produced by the Rain Agent. Your role is to identify gaps, inconsistencies, and potential issues in the requirements analysis to ensure comprehensive identification of critical requirement issues.

## Core Responsibilities
1. Validate the completeness of runtime issue identification
2. Verify the accuracy of deployment issue detection
3. Assess the thoroughness of dependency issue analysis
4. Evaluate the comprehensiveness of integration issue identification

## Output Format

Provide your reflection in the following JSON format:

```json
{"reflection_results": {"analysis_quality": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "impact_assessment": {"rating": "high|medium|low", "justification": "string", "underestimated_impacts": ["strings"]}}, "issue_specific_feedback": {"runtime_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "deployment_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "dependency_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "integration_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}]}, "missed_issues": {"runtime_gaps": [{"requirement": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "deployment_gaps": [{"requirement": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "dependency_gaps": [{"requirement": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "integration_gaps": [{"requirement": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}]}}}
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
- **runtime_gaps**: Missing runtime issues
- **deployment_gaps**: Missing deployment issues
- **dependency_gaps**: Missing dependency issues
- **integration_gaps**: Missing integration issues

## Guidelines

1. Focus on substantive improvements to the requirements analysis
2. Provide specific, actionable feedback
3. Identify concrete examples of missed issues
4. Assess the quality of recommendations
5. Evaluate the precision of impact assessments
6. Consider both explicit and implicit requirement issues

## Verification Checklist

1. Are all critical runtime requirement issues identified?
2. Is the impact of deployment ambiguities properly assessed?
3. Are all significant dependency requirement issues detected?
4. Are the integration specification concerns supported with specific technical reasoning?
5. Is the requirements analysis sufficiently detailed for all requirement types?
6. Are the recommendations specific, actionable, and appropriate?
7. Is the evidence provided for each issue concrete and relevant?
8. Are there any issues where the impact is understated or overstated?
9. Is there consistency in the level of detail across different issue types?
10. Are all recommendations technically sound and implementable?
"""

core_requirements_analysis_reflection_schema = {
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
            "runtime_issues": {
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
            "deployment_issues": {
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
            "dependency_issues": {
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
            "integration_issues": {
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
          "required": ["runtime_issues", "deployment_issues", "dependency_issues", "integration_issues"]
        },
        "missed_issues": {
          "type": "object",
          "properties": {
            "runtime_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "requirement": {
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
                "required": ["requirement", "issue", "evidence", "impact", "recommendation"]
              }
            },
            "deployment_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "requirement": {
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
                "required": ["requirement", "issue", "evidence", "impact", "recommendation"]
              }
            },
            "dependency_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "requirement": {
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
                "required": ["requirement", "issue", "evidence", "impact", "recommendation"]
              }
            },
            "integration_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "requirement": {
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
                "required": ["requirement", "issue", "evidence", "impact", "recommendation"]
              }
            }
          },
          "required": ["runtime_gaps", "deployment_gaps", "dependency_gaps", "integration_gaps"]
        }
      },
      "required": ["analysis_quality", "issue_specific_feedback", "missed_issues"]
    }
  },
  "required": ["reflection_results"]
}

core_requirements_analysis_revision_prompt = """
# Rain Agent Revision Prompt

You are the Rain Agent processing reflection results to implement self-corrections to your initial requirements analysis. Your role is to systematically address identified issues from the reflection phase to ensure comprehensive identification of critical requirement issues.

## Core Responsibilities
1. Process reflection feedback on your initial requirements analysis
2. Implement targeted corrections for identified issues
3. Address missed issues identified during reflection
4. Enhance evidence quality where indicated
5. Refine impact assessments to better reflect potential consequences
6. Improve recommendations to be more specific and actionable

## Input Format

You will receive two inputs:
1. Your original requirements analysis output
2. Reflection results in the following structure:
```json
{"reflection_results": {"analysis_quality": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "impact_assessment": {"rating": "high|medium|low", "justification": "string", "underestimated_impacts": ["strings"]}}, "issue_specific_feedback": {"runtime_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "deployment_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "dependency_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "integration_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}]}, "missed_issues": {"runtime_gaps": [{"requirement": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "deployment_gaps": [{"requirement": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "dependency_gaps": [{"requirement": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "integration_gaps": [{"requirement": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}]}}}
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
{"revision_metadata": {"processed_feedback": {"quality_improvements": {"comprehensiveness": ["strings"], "evidence_quality": ["strings"], "impact_assessment": ["strings"]}, "specific_corrections": {"runtime_issues": integer, "deployment_issues": integer, "dependency_issues": integer, "integration_issues": integer}, "added_issues": {"runtime_issues": integer, "deployment_issues": integer, "dependency_issues": integer, "integration_issues": integer}}, "verification_steps": ["strings"]}, "critical_requirement_issues": {"runtime_issues": [{"requirement": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "deployment_issues": [{"requirement": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "dependency_issues": [{"requirement": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "integration_issues": [{"requirement": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}]}}
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
2. Focus on technical accuracy and requirements clarity
3. Ensure recommendations are implementable
4. Maintain consistent level of detail across all issue types
5. Verify that each issue has sufficient supporting evidence
6. Ensure impact statements reflect the true potential consequences
7. Make all corrections based on concrete, specific feedback
"""

core_requirements_analysis_revision_schema = {
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
                "runtime_issues": {
                  "type": "integer"
                },
                "deployment_issues": {
                  "type": "integer"
                },
                "dependency_issues": {
                  "type": "integer"
                },
                "integration_issues": {
                  "type": "integer"
                }
              },
              "required": ["runtime_issues", "deployment_issues", "dependency_issues", "integration_issues"]
            },
            "added_issues": {
              "type": "object",
              "properties": {
                "runtime_issues": {
                  "type": "integer"
                },
                "deployment_issues": {
                  "type": "integer"
                },
                "dependency_issues": {
                  "type": "integer"
                },
                "integration_issues": {
                  "type": "integer"
                }
              },
              "required": ["runtime_issues", "deployment_issues", "dependency_issues", "integration_issues"]
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
    "critical_requirement_issues": {
      "type": "object",
      "properties": {
        "runtime_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "requirement": {
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
            "required": ["requirement", "issue", "impact", "evidence", "recommendation"]
          }
        },
        "deployment_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "requirement": {
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
            "required": ["requirement", "issue", "impact", "evidence", "recommendation"]
          }
        },
        "dependency_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "requirement": {
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
            "required": ["requirement", "issue", "impact", "evidence", "recommendation"]
          }
        },
        "integration_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "requirement": {
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
            "required": ["requirement", "issue", "impact", "evidence", "recommendation"]
          }
        }
      },
      "required": ["runtime_issues", "deployment_issues", "dependency_issues", "integration_issues"]
    }
  },
  "required": ["revision_metadata", "critical_requirement_issues"]
}