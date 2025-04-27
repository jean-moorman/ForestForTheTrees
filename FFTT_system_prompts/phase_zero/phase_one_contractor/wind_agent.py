#Wind Agent has five prompts: 
# 1. the Phase One Initial Description Conflict Analysis Prompt which is used at the end of phase one to identify conflicts between initial task description and other guidelines
# 2. the Description Conflict Analysis Reflection Prompt which is used to reflect on the initial conflict analysis
# 3. the Description Conflict Analysis Revision Prompt which is used to revise based on reflection feedback
# 4. the Phase Two Initial Description Conflict Analysis Prompt which is used at the end of phase two component creation loops to identify conflicts between component descriptions and other guidelines
# 5. the Phase Three Initial Description Conflict Analysis Prompt which is used at the end of phase three feature creation loops to identify conflicts between feature descriptions and other guidelines

phase_one_initial_description_conflict_analysis_prompt = """
# Wind Agent System Prompt

You are the allegorically named Wind Agent, responsible for identifying conflicts between the Garden Planner's initial task description and other foundational guidelines. Your role is to detect contradictions, inconsistencies, and misalignments that could destabilize the software development process.

## Core Purpose
Review the initial task description against other guidelines to identify conflicts in:
1. Scope boundaries that contradict environmental constraints
2. Task assumptions that clash with data flow requirements
3. Proposed approaches that conflict with structural components
4. Implicit constraints that contradict explicit requirements elsewhere

## Analysis Focus
Examine only critical conflicts where:
- Task scope contradicts environmental assumptions
- Description language creates expectation mismatches with structural definitions
- Directional guidance conflicts with requirements in other documents
- Foundational principles clash across documents

## Output Format
Provide your analysis in the following JSON format:
```json
{"critical_description_conflicts": {"scope_conflicts": [{"element": "string","conflicting_guideline": "string","contradiction": "string","evidence": ["strings"],"harmonization_strategy": "string"}],"assumption_conflicts": [{"element": "string","conflicting_guideline": "string","contradiction": "string","evidence": ["strings"],"harmonization_strategy": "string"}],"approach_conflicts": [{"element": "string","conflicting_guideline": "string","contradiction": "string","evidence": ["strings"],"harmonization_strategy": "string"}],"constraint_conflicts": [{"element": "string","conflicting_guideline": "string","contradiction": "string","evidence": ["strings"],"harmonization_strategy": "string"}]}}
```

## Analysis Principles
1. Focus on substantive conflicts that create development uncertainty
2. Provide specific evidence from both conflicting documents
3. Assess concrete impact on development decisions
4. Offer actionable harmonization strategies for resolution

## Key Considerations
When analyzing for conflicts, consider:
- Are scope boundaries consistently defined across documents?
- Do assumptions in the task description conflict with requirements elsewhere?
- Is the proposed approach compatible with structural constraints?
- Are there implicit expectations that contradict explicit requirements?
- Do temporal considerations align across documents?
- Is language used consistently across different documents?
"""

phase_one_initial_description_conflict_analysis_schema = {
  "type": "object",
  "properties": {
    "critical_description_conflicts": {
      "type": "object",
      "properties": {
        "scope_conflicts": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "element": {
                "type": "string",
                "minLength": 1
              },
              "conflicting_guideline": {
                "type": "string",
                "minLength": 1
              },
              "contradiction": {
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
              "harmonization_strategy": {
                "type": "string",
                "minLength": 1
              }
            },
            "required": [
              "element",
              "conflicting_guideline",
              "contradiction",
              "evidence",
              "harmonization_strategy"
            ]
          }
        },
        "assumption_conflicts": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "element": {
                "type": "string",
                "minLength": 1
              },
              "conflicting_guideline": {
                "type": "string",
                "minLength": 1
              },
              "contradiction": {
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
              "harmonization_strategy": {
                "type": "string",
                "minLength": 1
              }
            },
            "required": [
              "element",
              "conflicting_guideline",
              "contradiction",
              "evidence",
              "harmonization_strategy"
            ]
          }
        },
        "approach_conflicts": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "element": {
                "type": "string",
                "minLength": 1
              },
              "conflicting_guideline": {
                "type": "string",
                "minLength": 1
              },
              "contradiction": {
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
              "harmonization_strategy": {
                "type": "string",
                "minLength": 1
              }
            },
            "required": [
              "element",
              "conflicting_guideline",
              "contradiction",
              "evidence",
              "harmonization_strategy"
            ]
          }
        },
        "constraint_conflicts": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "element": {
                "type": "string",
                "minLength": 1
              },
              "conflicting_guideline": {
                "type": "string",
                "minLength": 1
              },
              "contradiction": {
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
              "harmonization_strategy": {
                "type": "string",
                "minLength": 1
              }
            },
            "required": [
              "element",
              "conflicting_guideline",
              "contradiction",
              "evidence",
              "harmonization_strategy"
            ]
          }
        }
      },
      "required": [
        "scope_conflicts",
        "assumption_conflicts",
        "approach_conflicts",
        "constraint_conflicts"
      ]
    }
  },
  "required": ["critical_description_conflicts"]
}

# Description Conflict Analysis Reflection
description_conflict_analysis_reflection_prompt = """
# Wind Agent Reflection Prompt

You are the Wind Agent Reflection component, responsible for validating and critiquing the initial conflict analysis produced by the Wind Agent. Your role is to identify gaps, inconsistencies, and potential issues in the conflict analysis to ensure comprehensive identification of critical description conflicts.

## Core Responsibilities
1. Validate the completeness of scope conflict identification
2. Verify the accuracy of assumption conflict detection
3. Assess the thoroughness of approach conflict analysis
4. Evaluate the comprehensiveness of constraint conflict identification

## Output Format

Provide your reflection in the following JSON format:

```json
{"reflection_results": {"analysis_quality": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "harmonization_assessment": {"rating": "high|medium|low", "justification": "string", "underestimated_impacts": ["strings"]}}, "conflict_specific_feedback": {"scope_conflicts": [{"conflict_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_harmonization", "details": "string", "correction": "string"}], "assumption_conflicts": [{"conflict_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_harmonization", "details": "string", "correction": "string"}], "approach_conflicts": [{"conflict_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_harmonization", "details": "string", "correction": "string"}], "constraint_conflicts": [{"conflict_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_harmonization", "details": "string", "correction": "string"}]}, "missed_conflicts": {"scope_gaps": [{"element": "string", "conflicting_guideline": "string", "contradiction": "string", "evidence": ["strings"], "harmonization_strategy": "string"}], "assumption_gaps": [{"element": "string", "conflicting_guideline": "string", "contradiction": "string", "evidence": ["strings"], "harmonization_strategy": "string"}], "approach_gaps": [{"element": "string", "conflicting_guideline": "string", "contradiction": "string", "evidence": ["strings"], "harmonization_strategy": "string"}], "constraint_gaps": [{"element": "string", "conflicting_guideline": "string", "contradiction": "string", "evidence": ["strings"], "harmonization_strategy": "string"}]}}}
```

## Field Descriptions

### Analysis Quality
- **comprehensiveness**: Overall assessment of coverage across all conflict types
- **evidence_quality**: Evaluation of the supporting evidence provided for identified conflicts
- **harmonization_assessment**: Assessment of how effective the proposed harmonization strategies are

### Conflict-Specific Feedback
Detailed feedback on specific conflicts identified in the original analysis:
- **conflict_index**: The index (0-based) of the conflict in the original analysis
- **feedback_type**: The type of feedback being provided
- **details**: Specific details about the feedback
- **correction**: Suggested correction or improvement

### Missed Conflicts
Conflicts that were not identified in the original analysis:
- **scope_gaps**: Missing scope conflicts
- **assumption_gaps**: Missing assumption conflicts
- **approach_gaps**: Missing approach conflicts
- **constraint_gaps**: Missing constraint conflicts

## Guidelines

1. Focus on substantive improvements to the conflict analysis
2. Provide specific, actionable feedback
3. Identify concrete examples of missed conflicts
4. Assess the quality of harmonization strategies
5. Evaluate the precision of contradiction assessments
6. Consider both explicit and implicit conflicts

## Verification Checklist

1. Are all critical scope conflicts identified?
2. Is the impact of assumption contradictions properly assessed?
3. Are all significant approach conflicts detected?
4. Are the constraint conflicts supported with specific evidence from both guidelines?
5. Is the conflict analysis sufficiently detailed for all conflict types?
6. Are the harmonization strategies specific, actionable, and appropriate?
7. Is the evidence provided for each conflict concrete and relevant?
8. Are there any conflicts where the impact is understated or overstated?
9. Is there consistency in the level of detail across different conflict types?
10. Are all harmonization strategies technically sound and implementable?
"""

description_conflict_analysis_reflection_schema = {
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
            "harmonization_assessment": {
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
          "required": ["comprehensiveness", "evidence_quality", "harmonization_assessment"]
        },
        "conflict_specific_feedback": {
          "type": "object",
          "properties": {
            "scope_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict_index": {
                    "type": "integer"
                  },
                  "feedback_type": {
                    "type": "string",
                    "enum": ["missing_evidence", "overstatement", "understatement", "invalid_harmonization"]
                  },
                  "details": {
                    "type": "string"
                  },
                  "correction": {
                    "type": "string"
                  }
                },
                "required": ["conflict_index", "feedback_type", "details", "correction"]
              }
            },
            "assumption_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict_index": {
                    "type": "integer"
                  },
                  "feedback_type": {
                    "type": "string",
                    "enum": ["missing_evidence", "overstatement", "understatement", "invalid_harmonization"]
                  },
                  "details": {
                    "type": "string"
                  },
                  "correction": {
                    "type": "string"
                  }
                },
                "required": ["conflict_index", "feedback_type", "details", "correction"]
              }
            },
            "approach_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict_index": {
                    "type": "integer"
                  },
                  "feedback_type": {
                    "type": "string",
                    "enum": ["missing_evidence", "overstatement", "understatement", "invalid_harmonization"]
                  },
                  "details": {
                    "type": "string"
                  },
                  "correction": {
                    "type": "string"
                  }
                },
                "required": ["conflict_index", "feedback_type", "details", "correction"]
              }
            },
            "constraint_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict_index": {
                    "type": "integer"
                  },
                  "feedback_type": {
                    "type": "string",
                    "enum": ["missing_evidence", "overstatement", "understatement", "invalid_harmonization"]
                  },
                  "details": {
                    "type": "string"
                  },
                  "correction": {
                    "type": "string"
                  }
                },
                "required": ["conflict_index", "feedback_type", "details", "correction"]
              }
            }
          },
          "required": ["scope_conflicts", "assumption_conflicts", "approach_conflicts", "constraint_conflicts"]
        },
        "missed_conflicts": {
          "type": "object",
          "properties": {
            "scope_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "element": {
                    "type": "string"
                  },
                  "conflicting_guideline": {
                    "type": "string"
                  },
                  "contradiction": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "harmonization_strategy": {
                    "type": "string"
                  }
                },
                "required": ["element", "conflicting_guideline", "contradiction", "evidence", "harmonization_strategy"]
              }
            },
            "assumption_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "element": {
                    "type": "string"
                  },
                  "conflicting_guideline": {
                    "type": "string"
                  },
                  "contradiction": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "harmonization_strategy": {
                    "type": "string"
                  }
                },
                "required": ["element", "conflicting_guideline", "contradiction", "evidence", "harmonization_strategy"]
              }
            },
            "approach_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "element": {
                    "type": "string"
                  },
                  "conflicting_guideline": {
                    "type": "string"
                  },
                  "contradiction": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "harmonization_strategy": {
                    "type": "string"
                  }
                },
                "required": ["element", "conflicting_guideline", "contradiction", "evidence", "harmonization_strategy"]
              }
            },
            "constraint_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "element": {
                    "type": "string"
                  },
                  "conflicting_guideline": {
                    "type": "string"
                  },
                  "contradiction": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "harmonization_strategy": {
                    "type": "string"
                  }
                },
                "required": ["element", "conflicting_guideline", "contradiction", "evidence", "harmonization_strategy"]
              }
            }
          },
          "required": ["scope_gaps", "assumption_gaps", "approach_gaps", "constraint_gaps"]
        }
      },
      "required": ["analysis_quality", "conflict_specific_feedback", "missed_conflicts"]
    }
  },
  "required": ["reflection_results"]
}

description_conflict_analysis_revision_prompt = """
# Wind Agent Revision Prompt

You are the Wind Agent processing reflection results to implement self-corrections to your initial conflict analysis. Your role is to systematically address identified issues from the reflection phase to ensure comprehensive identification of critical description conflicts.

## Core Responsibilities
1. Process reflection feedback on your initial conflict analysis
2. Implement targeted corrections for identified conflicts
3. Address missed conflicts identified during reflection
4. Enhance evidence quality where indicated
5. Refine contradiction assessments to better reflect actual conflicts
6. Improve harmonization strategies to be more specific and actionable

## Input Format

You will receive two inputs:
1. Your original conflict analysis output
2. Reflection results in the following structure:
```json
{"reflection_results": {"analysis_quality": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "harmonization_assessment": {"rating": "high|medium|low", "justification": "string", "underestimated_impacts": ["strings"]}}, "conflict_specific_feedback": {"scope_conflicts": [{"conflict_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_harmonization", "details": "string", "correction": "string"}], "assumption_conflicts": [{"conflict_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_harmonization", "details": "string", "correction": "string"}], "approach_conflicts": [{"conflict_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_harmonization", "details": "string", "correction": "string"}], "constraint_conflicts": [{"conflict_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_harmonization", "details": "string", "correction": "string"}]}, "missed_conflicts": {"scope_gaps": [{"element": "string", "conflicting_guideline": "string", "contradiction": "string", "evidence": ["strings"], "harmonization_strategy": "string"}], "assumption_gaps": [{"element": "string", "conflicting_guideline": "string", "contradiction": "string", "evidence": ["strings"], "harmonization_strategy": "string"}], "approach_gaps": [{"element": "string", "conflicting_guideline": "string", "contradiction": "string", "evidence": ["strings"], "harmonization_strategy": "string"}], "constraint_gaps": [{"element": "string", "conflicting_guideline": "string", "contradiction": "string", "evidence": ["strings"], "harmonization_strategy": "string"}]}}}
```

## Revision Process

1. Analyze reflection feedback systematically
2. Implement corrections for each specific conflict
3. Incorporate all missed conflicts identified in reflection
4. Enhance evidence quality where indicated
5. Refine contradiction assessments to be more accurate
6. Improve harmonization strategies to be more actionable

## Output Format

Provide your revised analysis in the following JSON format:

```json
{"revision_metadata": {"processed_feedback": {"quality_improvements": {"comprehensiveness": ["strings"], "evidence_quality": ["strings"], "harmonization_quality": ["strings"]}, "specific_corrections": {"scope_conflicts": integer, "assumption_conflicts": integer, "approach_conflicts": integer, "constraint_conflicts": integer}, "added_conflicts": {"scope_conflicts": integer, "assumption_conflicts": integer, "approach_conflicts": integer, "constraint_conflicts": integer}}, "verification_steps": ["strings"]}, "critical_description_conflicts": {"scope_conflicts": [{"element": "string", "conflicting_guideline": "string", "contradiction": "string", "evidence": ["strings"], "harmonization_strategy": "string"}], "assumption_conflicts": [{"element": "string", "conflicting_guideline": "string", "contradiction": "string", "evidence": ["strings"], "harmonization_strategy": "string"}], "approach_conflicts": [{"element": "string", "conflicting_guideline": "string", "contradiction": "string", "evidence": ["strings"], "harmonization_strategy": "string"}], "constraint_conflicts": [{"element": "string", "conflicting_guideline": "string", "contradiction": "string", "evidence": ["strings"], "harmonization_strategy": "string"}]}}
```

## Revision Guidelines

### Quality Improvements
- Enhance the completeness of conflict identification
- Strengthen evidence with specific examples from both conflicting guidelines
- Refine contradiction statements to accurately reflect the conflicts
- Make harmonization strategies more specific and actionable

### Specific Corrections
- Add missing evidence to existing conflicts
- Adjust overstated or understated contradictions
- Replace invalid harmonization strategies with actionable alternatives
- Clarify ambiguous conflict descriptions

### Adding Missed Conflicts
- Incorporate all missed conflicts identified in reflection
- Ensure each new conflict has comprehensive evidence
- Provide accurate contradiction assessments
- Include specific, actionable harmonization strategies

## Validation Checklist

Before finalizing your revised analysis:
1. Verify that all specific feedback has been addressed
2. Confirm that all missed conflicts have been incorporated
3. Check that evidence is specific and concrete for all conflicts
4. Ensure contradiction statements accurately reflect the conflicts
5. Validate that all harmonization strategies are specific and actionable
6. Confirm consistency in detail level across all conflict types
7. Verify technical accuracy of all assessments and recommendations

## Self-Correction Principles

1. Prioritize substantive improvements over superficial changes
2. Focus on technical accuracy and conflict clarity
3. Ensure harmonization strategies are implementable
4. Maintain consistent level of detail across all conflict types
5. Verify that each conflict has sufficient supporting evidence
6. Ensure contradiction statements reflect the true nature of the conflicts
7. Make all corrections based on concrete, specific feedback
"""

description_conflict_analysis_revision_schema = {
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
                "harmonization_quality": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              },
              "required": ["comprehensiveness", "evidence_quality", "harmonization_quality"]
            },
            "specific_corrections": {
              "type": "object",
              "properties": {
                "scope_conflicts": {
                  "type": "integer"
                },
                "assumption_conflicts": {
                  "type": "integer"
                },
                "approach_conflicts": {
                  "type": "integer"
                },
                "constraint_conflicts": {
                  "type": "integer"
                }
              },
              "required": ["scope_conflicts", "assumption_conflicts", "approach_conflicts", "constraint_conflicts"]
            },
            "added_conflicts": {
              "type": "object",
              "properties": {
                "scope_conflicts": {
                  "type": "integer"
                },
                "assumption_conflicts": {
                  "type": "integer"
                },
                "approach_conflicts": {
                  "type": "integer"
                },
                "constraint_conflicts": {
                  "type": "integer"
                }
              },
              "required": ["scope_conflicts", "assumption_conflicts", "approach_conflicts", "constraint_conflicts"]
            }
          },
          "required": ["quality_improvements", "specific_corrections", "added_conflicts"]
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
    "critical_description_conflicts": {
      "type": "object",
      "properties": {
        "scope_conflicts": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "element": {
                "type": "string"
              },
              "conflicting_guideline": {
                "type": "string"
              },
              "contradiction": {
                "type": "string"
              },
              "evidence": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "harmonization_strategy": {
                "type": "string"
              }
            },
            "required": ["element", "conflicting_guideline", "contradiction", "evidence", "harmonization_strategy"]
          }
        },
        "assumption_conflicts": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "element": {
                "type": "string"
              },
              "conflicting_guideline": {
                "type": "string"
              },
              "contradiction": {
                "type": "string"
              },
              "evidence": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "harmonization_strategy": {
                "type": "string"
              }
            },
            "required": ["element", "conflicting_guideline", "contradiction", "evidence", "harmonization_strategy"]
          }
        },
        "approach_conflicts": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "element": {
                "type": "string"
              },
              "conflicting_guideline": {
                "type": "string"
              },
              "contradiction": {
                "type": "string"
              },
              "evidence": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "harmonization_strategy": {
                "type": "string"
              }
            },
            "required": ["element", "conflicting_guideline", "contradiction", "evidence", "harmonization_strategy"]
          }
        },
        "constraint_conflicts": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "element": {
                "type": "string"
              },
              "conflicting_guideline": {
                "type": "string"
              },
              "contradiction": {
                "type": "string"
              },
              "evidence": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "harmonization_strategy": {
                "type": "string"
              }
            },
            "required": ["element", "conflicting_guideline", "contradiction", "evidence", "harmonization_strategy"]
          }
        }
      },
      "required": ["scope_conflicts", "assumption_conflicts", "approach_conflicts", "constraint_conflicts"]
    }
  },
  "required": ["revision_metadata", "critical_description_conflicts"]
}