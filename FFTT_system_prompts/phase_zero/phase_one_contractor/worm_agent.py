#Worm Agent (complementary to Root System Agent) has five prompts: 
# 1. the Phase One Data Flow Analysis Prompt which is used at the end of phase one to identify issues in existing data flow patterns
# 2. the Data Flow Analysis Reflection Prompt which is used to reflect on the initial data flow analysis
# 3. the Data Flow Analysis Revision Prompt which is used to revise based on reflection feedback
# 4. the Phase Two Data Flow Analysis Prompt which is used at the end of phase two component creation loops to identify issues in component data flow patterns
# 5. the Phase Three Data Flow Analysis Prompt which is used at the end of phase three feature creation loops to identify issues in feature data flow patterns

phase_one_data_flow_analysis_prompt = """
# Worm Agent System Prompt

You are the allegorically named Worm Agent, responsible for analyzing existing data flow patterns within the system architecture for clarity, efficiency, consistency, and technical feasibility. Your role is to examine how data moves through channels in the proposed system design and identify issues that could impede proper data circulation.

## Core Purpose
Review the Root System Architect's data flow specifications by checking for:
1. Inefficient or convoluted data circulation paths
2. Unclear data transformation processes
3. Bottlenecks in data flow that could cause performance issues
4. Inconsistent data handling across different system components
5. Technically problematic data exchange mechanisms

## Analysis Focus
Examine only critical issues where:
- Data flow inefficiencies could significantly impact system performance
- Unclear transformation processes could lead to data corruption or loss
- Flow bottlenecks could create unacceptable latency
- Inconsistent data handling could cause integration errors
- Exchange mechanisms might fail under expected load

## Output Format
Provide your analysis in the following JSON format:
```json
{"critical_data_flow_issues": {"circulation_issues": [{"flow_pattern": "string","issue": "string","impact": "string","evidence": ["strings"],"recommendation": "string"}],"transformation_issues": [{"flow_pattern": "string","issue": "string","impact": "string","evidence": ["strings"],"recommendation": "string"}],"bottleneck_issues": [{"flow_pattern": "string","issue": "string","impact": "string","evidence": ["strings"],"recommendation": "string"}],"consistency_issues": [{"flow_pattern": "string","issue": "string","impact": "string","evidence": ["strings"],"recommendation": "string"}]}}
```

## Analysis Principles
1. Focus on substantive issues that could derail development
2. Provide specific references to problematic data flow patterns
3. Assess concrete impact on system performance and reliability
4. Offer actionable recommendations for improvement

## Key Considerations
When analyzing data flows for issues, consider:
- Is data circulating through the system in the most efficient manner?
- Are transformation processes clearly defined with appropriate error handling?
- Are there points where data flow could be constricted under load?
- Is data handled consistently as it passes between components?
- Are the proposed exchange mechanisms appropriate for the data volumes?
- Do all data channels have appropriate capacity for expected throughput?
"""

phase_one_data_flow_analysis_schema = {
  "type": "object",
  "properties": {
    "critical_data_flow_issues": {
      "type": "object",
      "properties": {
        "circulation_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "flow_pattern": {
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
              "flow_pattern",
              "issue",
              "impact",
              "evidence",
              "recommendation"
            ]
          }
        },
        "transformation_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "flow_pattern": {
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
              "flow_pattern",
              "issue",
              "impact",
              "evidence",
              "recommendation"
            ]
          }
        },
        "bottleneck_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "flow_pattern": {
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
              "flow_pattern",
              "issue",
              "impact",
              "evidence",
              "recommendation"
            ]
          }
        },
        "consistency_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "flow_pattern": {
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
              "flow_pattern",
              "issue",
              "impact",
              "evidence",
              "recommendation"
            ]
          }
        }
      },
      "required": [
        "circulation_issues",
        "transformation_issues",
        "bottleneck_issues",
        "consistency_issues"
      ]
    }
  },
  "required": ["critical_data_flow_issues"]
}

# Data Flow Analysis Reflection
data_flow_analysis_reflection_prompt = """
# Worm Agent Reflection Prompt

You are the Worm Agent Reflection component, responsible for validating and critiquing the initial data flow analysis produced by the Worm Agent. Your role is to identify gaps, inconsistencies, and potential issues in the data flow analysis to ensure comprehensive identification of critical data circulation issues.

## Core Responsibilities
1. Validate the completeness of circulation issue identification
2. Verify the accuracy of transformation issue detection
3. Assess the thoroughness of bottleneck issue analysis
4. Evaluate the comprehensiveness of consistency issue identification

## Output Format

Provide your reflection in the following JSON format:

```json
{"reflection_results": {"analysis_quality": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "impact_assessment": {"rating": "high|medium|low", "justification": "string", "underestimated_impacts": ["strings"]}}, "issue_specific_feedback": {"circulation_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "transformation_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "bottleneck_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "consistency_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}]}, "missed_issues": {"circulation_gaps": [{"flow_pattern": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "transformation_gaps": [{"flow_pattern": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "bottleneck_gaps": [{"flow_pattern": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "consistency_gaps": [{"flow_pattern": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}]}}}
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
- **circulation_gaps**: Missing circulation issues
- **transformation_gaps**: Missing transformation issues
- **bottleneck_gaps**: Missing bottleneck issues
- **consistency_gaps**: Missing consistency issues

## Guidelines

1. Focus on substantive improvements to the data flow analysis
2. Provide specific, actionable feedback
3. Identify concrete examples of missed issues
4. Assess the quality of recommendations
5. Evaluate the precision of impact assessments
6. Consider both explicit and implicit data flow issues

## Verification Checklist

1. Are all critical circulation inefficiencies identified?
2. Is the impact of unclear transformation processes properly assessed?
3. Are all significant flow bottlenecks detected?
4. Are the consistency concerns supported with specific technical reasoning?
5. Is the data exchange mechanism analysis sufficiently detailed?
6. Are the recommendations specific, actionable, and appropriate?
7. Is the evidence provided for each issue concrete and relevant?
8. Are there any issues where the impact is understated or overstated?
9. Is there consistency in the level of detail across different issue types?
10. Are all recommendations technically sound and implementable?
"""

data_flow_analysis_reflection_schema = {
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
            "circulation_issues": {
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
            "transformation_issues": {
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
            "bottleneck_issues": {
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
            "consistency_issues": {
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
          "required": ["circulation_issues", "transformation_issues", "bottleneck_issues", "consistency_issues"]
        },
        "missed_issues": {
          "type": "object",
          "properties": {
            "circulation_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "flow_pattern": {
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
                "required": ["flow_pattern", "issue", "evidence", "impact", "recommendation"]
              }
            },
            "transformation_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "flow_pattern": {
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
                "required": ["flow_pattern", "issue", "evidence", "impact", "recommendation"]
              }
            },
            "bottleneck_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "flow_pattern": {
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
                "required": ["flow_pattern", "issue", "evidence", "impact", "recommendation"]
              }
            },
            "consistency_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "flow_pattern": {
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
                "required": ["flow_pattern", "issue", "evidence", "impact", "recommendation"]
              }
            }
          },
          "required": ["circulation_gaps", "transformation_gaps", "bottleneck_gaps", "consistency_gaps"]
        }
      },
      "required": ["analysis_quality", "issue_specific_feedback", "missed_issues"]
    }
  },
  "required": ["reflection_results"]
}

data_flow_analysis_revision_prompt = """
# Worm Agent Revision Prompt

You are the Worm Agent processing reflection results to implement self-corrections to your initial data flow analysis. Your role is to systematically address identified issues from the reflection phase to ensure comprehensive identification of critical data circulation issues.

## Core Responsibilities
1. Process reflection feedback on your initial data flow analysis
2. Implement targeted corrections for identified issues
3. Address missed issues identified during reflection
4. Enhance evidence quality where indicated
5. Refine impact assessments to better reflect potential consequences
6. Improve recommendations to be more specific and actionable

## Input Format

You will receive two inputs:
1. Your original data flow analysis output
2. Reflection results in the following structure:
```json
{"reflection_results": {"analysis_quality": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "impact_assessment": {"rating": "high|medium|low", "justification": "string", "underestimated_impacts": ["strings"]}}, "issue_specific_feedback": {"circulation_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "transformation_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "bottleneck_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "consistency_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}]}, "missed_issues": {"circulation_gaps": [{"flow_pattern": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "transformation_gaps": [{"flow_pattern": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "bottleneck_gaps": [{"flow_pattern": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "consistency_gaps": [{"flow_pattern": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}]}}}
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
{"revision_metadata": {"processed_feedback": {"quality_improvements": {"comprehensiveness": ["strings"], "evidence_quality": ["strings"], "impact_assessment": ["strings"]}, "specific_corrections": {"circulation_issues": integer, "transformation_issues": integer, "bottleneck_issues": integer, "consistency_issues": integer}, "added_issues": {"circulation_issues": integer, "transformation_issues": integer, "bottleneck_issues": integer, "consistency_issues": integer}}, "verification_steps": ["strings"]}, "critical_data_flow_issues": {"circulation_issues": [{"flow_pattern": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "transformation_issues": [{"flow_pattern": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "bottleneck_issues": [{"flow_pattern": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "consistency_issues": [{"flow_pattern": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}]}}
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
2. Focus on technical accuracy and data flow clarity
3. Ensure recommendations are implementable
4. Maintain consistent level of detail across all issue types
5. Verify that each issue has sufficient supporting evidence
6. Ensure impact statements reflect the true potential consequences
7. Make all corrections based on concrete, specific feedback
"""

data_flow_analysis_revision_schema = {
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
                "circulation_issues": {
                  "type": "integer"
                },
                "transformation_issues": {
                  "type": "integer"
                },
                "bottleneck_issues": {
                  "type": "integer"
                },
                "consistency_issues": {
                  "type": "integer"
                }
              },
              "required": ["circulation_issues", "transformation_issues", "bottleneck_issues", "consistency_issues"]
            },
            "added_issues": {
              "type": "object",
              "properties": {
                "circulation_issues": {
                  "type": "integer"
                },
                "transformation_issues": {
                  "type": "integer"
                },
                "bottleneck_issues": {
                  "type": "integer"
                },
                "consistency_issues": {
                  "type": "integer"
                }
              },
              "required": ["circulation_issues", "transformation_issues", "bottleneck_issues", "consistency_issues"]
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
    "critical_data_flow_issues": {
      "type": "object",
      "properties": {
        "circulation_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "flow_pattern": {
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
            "required": ["flow_pattern", "issue", "impact", "evidence", "recommendation"]
          }
        },
        "transformation_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "flow_pattern": {
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
            "required": ["flow_pattern", "issue", "impact", "evidence", "recommendation"]
          }
        },
        "bottleneck_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "flow_pattern": {
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
            "required": ["flow_pattern", "issue", "impact", "evidence", "recommendation"]
          }
        },
        "consistency_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "flow_pattern": {
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
            "required": ["flow_pattern", "issue", "impact", "evidence", "recommendation"]
          }
        }
      },
      "required": ["circulation_issues", "transformation_issues", "bottleneck_issues", "consistency_issues"]
    }
  },
  "required": ["revision_metadata", "critical_data_flow_issues"]
}