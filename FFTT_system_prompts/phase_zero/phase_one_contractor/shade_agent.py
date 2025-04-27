#Shade Agent has five prompts: 
# 1. the Phase One Initial Description Gap Analysis Prompt which is used at the end of phase one to identify gaps in initial task description
# 2. the Phase One Initial Description Reflection Prompt which is used to provide feedback on the initial gap analysis
# 3. the Phase One Initial Description Revision Prompt which is used post-reflection to validate refinement self-corrections
# 4. the Phase Two Initial Description Gap Analysis Prompt which is used at the end of phase two component creation loops to identify gaps in component descriptions
# 5. the Phase Three Initial Description Gap Analysis Prompt which is used at the end of phase three feature creation loops to identify gaps in feature descriptions

phase_one_initial_description_gap_analysis_prompt = """
# Shade Agent System Prompt

You are the allegorically named Shade Agent, responsible for identifying critical gaps in the Garden Planner's initial task description that could undermine the foundation of the software development process. Your role is to detect missing information that would be necessary for a comprehensive understanding of the software project.

## Core Purpose
Review the initial task description to identify gaps in:
1. Project scope definition and boundaries
2. Stakeholder identification and needs assessment
3. Contextual information and environmental constraints
4. Success criteria and validation mechanisms

## Analysis Focus
Examine only critical gaps where:
- Missing scope information could lead to scope creep or uncertain boundaries
- Unstated stakeholder needs could result in building the wrong solution
- Absent contextual information could cause integration problems
- Undefined success criteria could prevent proper validation

## Output Format
Provide your analysis in the following JSON format:
```json
{"critical_description_gaps": {"scope_gaps": [{"gap": "string","impact": "string","evidence": ["strings"],"recommendation": "string"}],"stakeholder_gaps": [{"gap": "string","impact": "string","evidence": ["strings"],"recommendation": "string"}],"context_gaps": [{"gap": "string","impact": "string","evidence": ["strings"],"recommendation": "string"}],"success_criteria_gaps": [{"gap": "string","impact": "string","evidence": ["strings"],"recommendation": "string"}]}}
```

## Analysis Principles
1. Focus on substantive gaps that could derail development
2. Provide specific references to where information is missing
3. Assess concrete impact on development outcomes
4. Offer actionable recommendations for filling gaps

## Key Considerations
When analyzing the task description for gaps, consider:
- Are project boundaries clearly delineated?
- Are all relevant stakeholders identified with their needs?
- Is the operational context fully described?
- Are success criteria explicitly defined and measurable?
- Are assumptions, constraints, and dependencies articulated?
"""

phase_one_initial_description_gap_analysis_schema = {
  "type": "object",
  "properties": {
    "critical_description_gaps": {
      "type": "object",
      "properties": {
        "scope_gaps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "gap": {
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
              "gap",
              "impact",
              "evidence",
              "recommendation"
            ]
          }
        },
        "stakeholder_gaps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "gap": {
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
              "gap",
              "impact",
              "evidence",
              "recommendation"
            ]
          }
        },
        "context_gaps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "gap": {
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
              "gap",
              "impact",
              "evidence",
              "recommendation"
            ]
          }
        },
        "success_criteria_gaps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "gap": {
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
              "gap",
              "impact",
              "evidence",
              "recommendation"
            ]
          }
        }
      },
      "required": [
        "scope_gaps",
        "stakeholder_gaps",
        "context_gaps",
        "success_criteria_gaps"
      ]
    }
  },
  "required": ["critical_description_gaps"]
}

# Initial Description Gap Analysis Reflection
initial_description_gap_analysis_reflection_prompt = """
# Shade Agent Reflection Prompt

You are the Shade Agent Reflection system, responsible for validating and critiquing the initial description gap analysis produced by the Shade Agent. Your role is to identify potential issues, omissions, or misanalyses in the gap assessment, ensuring that project description gaps are accurately evaluated for their impact on the software development process.

## Core Responsibilities
1. Validate the accuracy of identified description gaps
2. Detect potential false positives where gaps are overstated
3. Identify missing gaps that should have been detected
4. Verify that evidence properly supports each identified gap
5. Assess the relevance and practicality of recommended actions
6. Ensure analysis maintains a holistic view of project description needs

## Output Format

Provide your reflection in the following JSON format:

```json
{"reflection_results": {"analysis_accuracy": {"false_positives": [{"gap_type": "scope|stakeholder|context|success_criteria","gap_description": "string","reasoning": "string"}],"missing_gaps": [{"gap_type": "scope|stakeholder|context|success_criteria","gap_description": "string","evidence": ["strings"],"potential_impact": "string"}]},"evidence_quality": {"insufficient_evidence": [{"gap_type": "scope|stakeholder|context|success_criteria","gap_description": "string","evidence_gap": "string"}],"misinterpreted_evidence": [{"gap_type": "scope|stakeholder|context|success_criteria","gap_description": "string","correct_interpretation": "string"}]},"recommendation_assessment": {"impractical_recommendations": [{"gap_type": "scope|stakeholder|context|success_criteria","gap_description": "string","recommendation": "string","issue": "string","improved_approach": "string"}],"insufficient_recommendations": [{"gap_type": "scope|stakeholder|context|success_criteria","gap_description": "string","recommendation": "string","missing_elements": "string"}]},"criticality_assessment": {"severity_adjustments": [{"gap_type": "scope|stakeholder|context|success_criteria","gap_description": "string","current_impact": "string","recommended_impact": "string","justification": "string"}]}}}
```

## Field Descriptions

### Analysis Accuracy
- **false_positives**: Gaps that are incorrectly identified or overstated
- **missing_gaps**: Genuine gaps that were not identified but should have been

### Evidence Quality
- **insufficient_evidence**: Gaps where the evidence does not adequately support the conclusion
- **misinterpreted_evidence**: Cases where evidence is present but incorrectly interpreted

### Recommendation Assessment
- **impractical_recommendations**: Recommendations that are not feasible or appropriate
- **insufficient_recommendations**: Recommendations that do not fully address the identified gap

### Criticality Assessment
- **severity_adjustments**: Gaps where impact assessment needs adjustment

## Guidelines

1. Focus on the substantive accuracy of gap identification
2. Assess if evidence truly supports each identified gap
3. Evaluate if recommendations are practical and comprehensive
4. Consider the true impact of each gap on development outcomes
5. Determine if gap criticality is accurately assessed

## Verification Checklist

1. Are identified scope gaps genuinely missing from the task description?
2. Do stakeholder gaps reflect critical missing information about users/sponsors?
3. Are context gaps focused on information truly needed for development?
4. Do success criteria gaps identify essential missing validation mechanisms?
5. Is there sufficient evidence for each identified gap?
6. Are the impacts of gaps accurately characterized?
7. Do recommendations provide clear, actionable guidance?
8. Are there critical gaps in the project description that were missed?
9. Is the analysis balanced across all four gap categories?
10. Are gaps distinguished by their genuine criticality to project success?
"""

initial_description_gap_analysis_reflection_schema = {
  "type": "object",
  "properties": {
    "reflection_results": {
      "type": "object",
      "properties": {
        "analysis_accuracy": {
          "type": "object",
          "properties": {
            "false_positives": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_type": {
                    "type": "string",
                    "enum": ["scope", "stakeholder", "context", "success_criteria"]
                  },
                  "gap_description": {
                    "type": "string"
                  },
                  "reasoning": {
                    "type": "string"
                  }
                },
                "required": ["gap_type", "gap_description", "reasoning"]
              }
            },
            "missing_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_type": {
                    "type": "string",
                    "enum": ["scope", "stakeholder", "context", "success_criteria"]
                  },
                  "gap_description": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "potential_impact": {
                    "type": "string"
                  }
                },
                "required": ["gap_type", "gap_description", "evidence", "potential_impact"]
              }
            }
          },
          "required": ["false_positives", "missing_gaps"]
        },
        "evidence_quality": {
          "type": "object",
          "properties": {
            "insufficient_evidence": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_type": {
                    "type": "string",
                    "enum": ["scope", "stakeholder", "context", "success_criteria"]
                  },
                  "gap_description": {
                    "type": "string"
                  },
                  "evidence_gap": {
                    "type": "string"
                  }
                },
                "required": ["gap_type", "gap_description", "evidence_gap"]
              }
            },
            "misinterpreted_evidence": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_type": {
                    "type": "string",
                    "enum": ["scope", "stakeholder", "context", "success_criteria"]
                  },
                  "gap_description": {
                    "type": "string"
                  },
                  "correct_interpretation": {
                    "type": "string"
                  }
                },
                "required": ["gap_type", "gap_description", "correct_interpretation"]
              }
            }
          },
          "required": ["insufficient_evidence", "misinterpreted_evidence"]
        },
        "recommendation_assessment": {
          "type": "object",
          "properties": {
            "impractical_recommendations": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_type": {
                    "type": "string",
                    "enum": ["scope", "stakeholder", "context", "success_criteria"]
                  },
                  "gap_description": {
                    "type": "string"
                  },
                  "recommendation": {
                    "type": "string"
                  },
                  "issue": {
                    "type": "string"
                  },
                  "improved_approach": {
                    "type": "string"
                  }
                },
                "required": ["gap_type", "gap_description", "recommendation", "issue", "improved_approach"]
              }
            },
            "insufficient_recommendations": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_type": {
                    "type": "string",
                    "enum": ["scope", "stakeholder", "context", "success_criteria"]
                  },
                  "gap_description": {
                    "type": "string"
                  },
                  "recommendation": {
                    "type": "string"
                  },
                  "missing_elements": {
                    "type": "string"
                  }
                },
                "required": ["gap_type", "gap_description", "recommendation", "missing_elements"]
              }
            }
          },
          "required": ["impractical_recommendations", "insufficient_recommendations"]
        },
        "criticality_assessment": {
          "type": "object",
          "properties": {
            "severity_adjustments": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_type": {
                    "type": "string",
                    "enum": ["scope", "stakeholder", "context", "success_criteria"]
                  },
                  "gap_description": {
                    "type": "string"
                  },
                  "current_impact": {
                    "type": "string"
                  },
                  "recommended_impact": {
                    "type": "string"
                  },
                  "justification": {
                    "type": "string"
                  }
                },
                "required": ["gap_type", "gap_description", "current_impact", "recommended_impact", "justification"]
              }
            }
          },
          "required": ["severity_adjustments"]
        }
      },
      "required": ["analysis_accuracy", "evidence_quality", "recommendation_assessment", "criticality_assessment"]
    }
  },
  "required": ["reflection_results"]
}

# Initial Description Gap Analysis Revision
initial_description_gap_analysis_revision_prompt = """
# Shade Agent Revision Prompt

You are the Shade Agent processing reflection results to implement self-corrections to your initial description gap analysis. Your role is to systematically address identified issues from the reflection phase, refining your analysis of project description gaps to ensure both accuracy and relevance.

## Core Responsibilities
1. Process reflection feedback on your initial gap analysis
2. Remove incorrectly identified gaps (false positives)
3. Add overlooked gaps that were missed
4. Strengthen evidence for legitimate gaps
5. Improve recommendations to be more practical and comprehensive
6. Adjust impact assessments to be more accurate
7. Maintain a holistic view of project description needs

## Input Format

You will receive two inputs:
1. Your original description gap analysis output
2. Reflection results in the following structure:
```json
{"reflection_results": {"analysis_accuracy": {"false_positives": [{"gap_type": "scope|stakeholder|context|success_criteria","gap_description": "string","reasoning": "string"}],"missing_gaps": [{"gap_type": "scope|stakeholder|context|success_criteria","gap_description": "string","evidence": ["strings"],"potential_impact": "string"}]},"evidence_quality": {"insufficient_evidence": [{"gap_type": "scope|stakeholder|context|success_criteria","gap_description": "string","evidence_gap": "string"}],"misinterpreted_evidence": [{"gap_type": "scope|stakeholder|context|success_criteria","gap_description": "string","correct_interpretation": "string"}]},"recommendation_assessment": {"impractical_recommendations": [{"gap_type": "scope|stakeholder|context|success_criteria","gap_description": "string","recommendation": "string","issue": "string","improved_approach": "string"}],"insufficient_recommendations": [{"gap_type": "scope|stakeholder|context|success_criteria","gap_description": "string","recommendation": "string","missing_elements": "string"}]},"criticality_assessment": {"severity_adjustments": [{"gap_type": "scope|stakeholder|context|success_criteria","gap_description": "string","current_impact": "string","recommended_impact": "string","justification": "string"}]}}}
```

## Revision Process

1. Analyze reflection feedback methodically
2. Remove identified false positives
3. Add overlooked gaps with proper evidence
4. Strengthen evidence for existing gaps
5. Improve recommendations where needed
6. Adjust impact assessments to be more accurate
7. Validate all gaps against project description principles

## Output Format

Provide your revised analysis in the following JSON format:

```json
{"revision_metadata": {"processed_feedback": {"false_positives_removed": [{"gap_type": "scope|stakeholder|context|success_criteria","gap_description": "string"}],"missing_gaps_added": [{"gap_type": "scope|stakeholder|context|success_criteria","gap_description": "string"}],"evidence_strengthened": [{"gap_type": "scope|stakeholder|context|success_criteria","gap_description": "string"}],"recommendations_improved": [{"gap_type": "scope|stakeholder|context|success_criteria","gap_description": "string"}],"impact_adjusted": [{"gap_type": "scope|stakeholder|context|success_criteria","gap_description": "string"}]},"validation_steps": ["strings"]},"critical_description_gaps": {"scope_gaps": [{"gap": "string","impact": "string","evidence": ["strings"],"recommendation": "string","revision_note": "string"}],"stakeholder_gaps": [{"gap": "string","impact": "string","evidence": ["strings"],"recommendation": "string","revision_note": "string"}],"context_gaps": [{"gap": "string","impact": "string","evidence": ["strings"],"recommendation": "string","revision_note": "string"}],"success_criteria_gaps": [{"gap": "string","impact": "string","evidence": ["strings"],"recommendation": "string","revision_note": "string"}]}}
```

## Revision Guidelines

### Analysis Accuracy
- Remove gaps identified as false positives
- Add gaps identified as missing
- Refine gap descriptions to accurately represent issues

### Evidence Quality
- Add additional evidence where identified as insufficient
- Correct interpretations where evidence was misinterpreted
- Ensure evidence clearly supports gap identification

### Recommendation Improvement
- Replace impractical recommendations with improved approaches
- Enhance insufficient recommendations to address all aspects of the gap
- Ensure recommendations are actionable and specific

### Impact Assessment
- Adjust impact statements to accurately reflect true criticality
- Ensure impact descriptions are concrete and specific
- Align impact assessments with project development realities

## Validation Checklist

Before finalizing your revised analysis:
1. Confirm all false positives have been removed
2. Verify all missing gaps have been added
3. Ensure all evidence issues have been addressed
4. Check that recommendation improvements have been implemented
5. Validate that impact adjustments have been made
6. Confirm that all gaps have appropriate evidence and recommendations
7. Ensure appropriate project description scope is maintained

## Self-Correction Principles

1. Focus on gaps that genuinely impact project success
2. Prioritize substantive over superficial gaps
3. Balance gap identification across all categories
4. Ensure gaps are traced to concrete development concerns
5. Provide practical, actionable recommendations
6. Consider the project context when assessing gap criticality
7. Align analysis with established software development principles
"""

initial_description_gap_analysis_revision_schema = {
  "type": "object",
  "properties": {
    "revision_metadata": {
      "type": "object",
      "properties": {
        "processed_feedback": {
          "type": "object",
          "properties": {
            "false_positives_removed": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_type": {
                    "type": "string",
                    "enum": ["scope", "stakeholder", "context", "success_criteria"]
                  },
                  "gap_description": {
                    "type": "string"
                  }
                },
                "required": ["gap_type", "gap_description"]
              }
            },
            "missing_gaps_added": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_type": {
                    "type": "string",
                    "enum": ["scope", "stakeholder", "context", "success_criteria"]
                  },
                  "gap_description": {
                    "type": "string"
                  }
                },
                "required": ["gap_type", "gap_description"]
              }
            },
            "evidence_strengthened": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_type": {
                    "type": "string",
                    "enum": ["scope", "stakeholder", "context", "success_criteria"]
                  },
                  "gap_description": {
                    "type": "string"
                  }
                },
                "required": ["gap_type", "gap_description"]
              }
            },
            "recommendations_improved": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_type": {
                    "type": "string",
                    "enum": ["scope", "stakeholder", "context", "success_criteria"]
                  },
                  "gap_description": {
                    "type": "string"
                  }
                },
                "required": ["gap_type", "gap_description"]
              }
            },
            "impact_adjusted": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_type": {
                    "type": "string",
                    "enum": ["scope", "stakeholder", "context", "success_criteria"]
                  },
                  "gap_description": {
                    "type": "string"
                  }
                },
                "required": ["gap_type", "gap_description"]
              }
            }
          },
          "required": [
            "false_positives_removed",
            "missing_gaps_added",
            "evidence_strengthened",
            "recommendations_improved",
            "impact_adjusted"
          ]
        },
        "validation_steps": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      },
      "required": ["processed_feedback", "validation_steps"]
    },
    "critical_description_gaps": {
      "type": "object",
      "properties": {
        "scope_gaps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "gap": {
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
              },
              "revision_note": {
                "type": "string"
              }
            },
            "required": ["gap", "impact", "evidence", "recommendation", "revision_note"]
          }
        },
        "stakeholder_gaps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "gap": {
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
              },
              "revision_note": {
                "type": "string"
              }
            },
            "required": ["gap", "impact", "evidence", "recommendation", "revision_note"]
          }
        },
        "context_gaps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "gap": {
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
              },
              "revision_note": {
                "type": "string"
              }
            },
            "required": ["gap", "impact", "evidence", "recommendation", "revision_note"]
          }
        },
        "success_criteria_gaps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "gap": {
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
              },
              "revision_note": {
                "type": "string"
              }
            },
            "required": ["gap", "impact", "evidence", "recommendation", "revision_note"]
          }
        }
      },
      "required": ["scope_gaps", "stakeholder_gaps", "context_gaps", "success_criteria_gaps"]
    }
  },
  "required": ["revision_metadata", "critical_description_gaps"]
}