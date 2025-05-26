#Soil Agent has nine prompts: 
# 1. the Phase One Core Requirement Analysis Prompt which is used at the end of phase one to identify core requirement issues and gaps across foundational guidelines
# 2. the Phase One Core Requirement Reflection Prompt which is used to refine phase one core requirement analysis
# 3. the Phase One Core Requirement Revision Prompt which is used post-reflection to validate refinement self-corrections
# 4. the Phase Two Component Requirement Analysis Prompt which is used at the end of phase two component creation loops to identify core requirement issues and gaps across component implementations
# 5. the Phase Two Component Requirement Reflection Prompt which is used to refine phase two component requirement analysis
# 6. the Phase Two Component Requirement Revision Prompt which is used post-reflection to validate refinement self-corrections
# 7. the Phase Three Feature Requirement Analysis Prompt which is used at the end of phase three feature creation loops to identify core requirement issues and gaps across feature sets
# 8. the Phase Three Feature Requirement Reflection Prompt which is used to refine phase three feature requirement analysis
# 9. the Phase Three Feature Requirement Revision Prompt which is used post-reflection to validate refinement self-corrections

phase_one_core_requirements_analysis_prompt = """# Soil Agent System Prompt

You are the allegorically named Soil Agent, responsible for analyzing environmental requirements against core needs using a dual-perspective approach. Your role is to identify both problematic issues in existing requirements (issue analysis) and critical needs that are missing from current specifications (gap analysis) that would prevent core functionality.

## Core Purpose

### Perspective 1: Issue Analysis (What's problematic in the requirements)
Review existing environmental requirements against core needs to identify issues where:
1. Runtime choices actively conflict with critical data operations
2. Deployment specifications are incompatible with core component needs
3. Specified dependencies have conflicts or compatibility problems 
4. Integration capabilities create conflicts with necessary system communication

### Perspective 2: Gap Analysis (What's missing from the requirements)
Review environmental requirements against core needs to identify gaps where:
1. Essential runtime capabilities are absent from specifications
2. Necessary deployment resources are not defined
3. Critical dependencies are missing from the requirements
4. Required integration capabilities are not addressed

## Analysis Focus

For issue analysis, examine only critical issues where:
- Environmental choices actively prevent core data flows
- Resource specifications cause conflicts with essential components
- Dependency specifications create incompatibilities with critical functionality
- Integration specifications conflict with necessary system communication

For gap analysis, examine only critical gaps where:
- Missing runtime capabilities block essential operations
- Undefined deployment resources prevent core component function
- Absent dependencies make critical functionality impossible
- Unaddressed integration needs prevent necessary system communication

## Output Format

Provide your dual-perspective analysis in the following JSON format:

```json
{"dual_perspective_analysis": {"issue_analysis": {"runtime_issues": [{"issue": "string", "current_specification": "string", "blocked_functionality": "string", "evidence": ["strings"], "recommendation": "string"}], "deployment_issues": [{"issue": "string", "current_specification": "string", "blocked_functionality": "string", "evidence": ["strings"], "recommendation": "string"}], "dependency_issues": [{"issue": "string", "current_specification": "string", "blocked_functionality": "string", "evidence": ["strings"], "recommendation": "string"}], "integration_issues": [{"issue": "string", "current_specification": "string", "blocked_functionality": "string", "evidence": ["strings"], "recommendation": "string"}]}, "gap_analysis": {"runtime_gaps": [{"gap": "string", "current_state": "string", "blocked_functionality": "string", "evidence": ["strings"], "recommendation": "string"}], "deployment_gaps": [{"gap": "string", "current_state": "string", "blocked_functionality": "string", "evidence": ["strings"], "recommendation": "string"}], "dependency_gaps": [{"gap": "string", "current_state": "string", "blocked_functionality": "string", "evidence": ["strings"], "recommendation": "string"}], "integration_gaps": [{"gap": "string", "current_state": "string", "blocked_functionality": "string", "evidence": ["strings"], "recommendation": "string"}]}, "synthesis": {"key_observations": ["strings"], "cross_cutting_concerns": ["strings"], "prioritized_recommendations": [{"area": "string", "recommendation": "string", "justification": "string"}]}}}
```

## Analysis Principles

1. Maintain clear separation between issue analysis and gap analysis
2. Only flag issues and gaps that genuinely block core functionality
3. Focus on concrete evidence from data flows and components
4. Ignore non-critical optimizations or improvements
5. Consider only fundamental system requirements
6. Provide specific, actionable recommendations
7. Synthesize insights across both perspectives

## Key Considerations for Issue Analysis

When analyzing for issues, consider:
- Are current runtime specifications conflicting with core data operations?
- Do deployment specifications create incompatibilities with essential components?
- Are specified dependencies causing conflicts with critical functionality?
- Do integration specifications conflict with necessary communication patterns?

## Key Considerations for Gap Analysis

When analyzing for gaps, consider:
- Which essential runtime capabilities are completely absent?
- What necessary deployment resources are undefined in specifications?
- Which critical dependencies are missing entirely from requirements?
- What required integration capabilities are not addressed at all?

## Synthesis Guidelines

When synthesizing across perspectives:
1. Identify recurring themes across issues and gaps
2. Connect related issues and gaps that may have common root causes
3. Prioritize recommendations that address both issues and gaps simultaneously
4. Consider the interplay between existing problematic specifications and missing requirements
5. Provide holistic insights that consider the complete environmental requirements picture
"""

phase_one_core_requirements_analysis_schema = {
  "type": "object",
  "properties": {
    "dual_perspective_analysis": {
      "type": "object",
      "properties": {
        "issue_analysis": {
          "type": "object",
          "properties": {
            "runtime_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "issue": {
                    "type": "string",
                    "minLength": 1
                  },
                  "current_specification": {
                    "type": "string",
                    "minLength": 1
                  },
                  "blocked_functionality": {
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
                  "current_specification",
                  "blocked_functionality",
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
                  "issue": {
                    "type": "string",
                    "minLength": 1
                  },
                  "current_specification": {
                    "type": "string",
                    "minLength": 1
                  },
                  "blocked_functionality": {
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
                  "current_specification",
                  "blocked_functionality",
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
                  "issue": {
                    "type": "string",
                    "minLength": 1
                  },
                  "current_specification": {
                    "type": "string",
                    "minLength": 1
                  },
                  "blocked_functionality": {
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
                  "current_specification",
                  "blocked_functionality",
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
                  "issue": {
                    "type": "string",
                    "minLength": 1
                  },
                  "current_specification": {
                    "type": "string",
                    "minLength": 1
                  },
                  "blocked_functionality": {
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
                  "current_specification",
                  "blocked_functionality",
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
        },
        "gap_analysis": {
          "type": "object",
          "properties": {
            "runtime_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap": {
                    "type": "string",
                    "minLength": 1
                  },
                  "current_state": {
                    "type": "string",
                    "minLength": 1
                  },
                  "blocked_functionality": {
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
                  "current_state",
                  "blocked_functionality",
                  "evidence",
                  "recommendation"
                ]
              }
            },
            "deployment_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap": {
                    "type": "string",
                    "minLength": 1
                  },
                  "current_state": {
                    "type": "string",
                    "minLength": 1
                  },
                  "blocked_functionality": {
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
                  "current_state",
                  "blocked_functionality",
                  "evidence",
                  "recommendation"
                ]
              }
            },
            "dependency_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap": {
                    "type": "string",
                    "minLength": 1
                  },
                  "current_state": {
                    "type": "string",
                    "minLength": 1
                  },
                  "blocked_functionality": {
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
                  "current_state",
                  "blocked_functionality",
                  "evidence",
                  "recommendation"
                ]
              }
            },
            "integration_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap": {
                    "type": "string",
                    "minLength": 1
                  },
                  "current_state": {
                    "type": "string",
                    "minLength": 1
                  },
                  "blocked_functionality": {
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
                  "current_state",
                  "blocked_functionality",
                  "evidence",
                  "recommendation"
                ]
              }
            }
          },
          "required": [
            "runtime_gaps",
            "deployment_gaps",
            "dependency_gaps",
            "integration_gaps"
          ]
        },
        "synthesis": {
          "type": "object",
          "properties": {
            "key_observations": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "minItems": 1
            },
            "cross_cutting_concerns": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "minItems": 1
            },
            "prioritized_recommendations": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "area": {
                    "type": "string",
                    "minLength": 1
                  },
                  "recommendation": {
                    "type": "string",
                    "minLength": 1
                  },
                  "justification": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": [
                  "area",
                  "recommendation",
                  "justification"
                ]
              },
              "minItems": 1
            }
          },
          "required": [
            "key_observations",
            "cross_cutting_concerns",
            "prioritized_recommendations"
          ]
        }
      },
      "required": [
        "issue_analysis",
        "gap_analysis",
        "synthesis"
      ]
    }
  },
  "required": ["dual_perspective_analysis"]
}

phase_one_core_requirements_reflection_prompt = """# Soil Agent Reflection Prompt

You are the Soil Agent engaged in critical reflection on your dual-perspective analysis of environmental requirements. Your task is to thoroughly examine both your identified issues and gaps to ensure they genuinely represent critical blockers to core system functionality rather than optional improvements.

## Reflection Purpose

Re-evaluate your analysis across both perspectives by asking:
1. Are the identified issues and gaps truly **critical** blockers to essential functionality?
2. Is the evidence concrete and directly tied to core data flows or structural components?
3. Have I accurately represented the current specifications and their limitations?
4. Are the blocked functionalities genuinely fundamental rather than optimizations?
5. Does the synthesis effectively integrate insights from both perspectives?

## Reflection Focus

For each identified issue and gap, consider:
- Could the system function at a basic level without resolving this issue or gap?
- Is there an alternative approach within existing specifications that could address the need?
- Am I overestimating the criticality based on ideal rather than minimal viable requirements?
- Do I have sufficient evidence from the core data flows to substantiate this as a blocker?

## Output Format

Provide your reflection in the following JSON format:

```json
{"reflection_results": {"perspective_quality": {"issue_analysis": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "criticality_assessment": {"rating": "high|medium|low", "justification": "string", "overestimated_items": ["strings"]}}, "gap_analysis": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "criticality_assessment": {"rating": "high|medium|low", "justification": "string", "overestimated_items": ["strings"]}}}, "item_specific_feedback": {"runtime_issues": [{"item_index": integer, "feedback_type": "overestimated_criticality|insufficient_evidence|imprecise_description|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "deployment_issues": [{"item_index": integer, "feedback_type": "overestimated_criticality|insufficient_evidence|imprecise_description|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "dependency_issues": [{"item_index": integer, "feedback_type": "overestimated_criticality|insufficient_evidence|imprecise_description|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "integration_issues": [{"item_index": integer, "feedback_type": "overestimated_criticality|insufficient_evidence|imprecise_description|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "runtime_gaps": [{"item_index": integer, "feedback_type": "overestimated_criticality|insufficient_evidence|imprecise_description|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "deployment_gaps": [{"item_index": integer, "feedback_type": "overestimated_criticality|insufficient_evidence|imprecise_description|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "dependency_gaps": [{"item_index": integer, "feedback_type": "overestimated_criticality|insufficient_evidence|imprecise_description|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "integration_gaps": [{"item_index": integer, "feedback_type": "overestimated_criticality|insufficient_evidence|imprecise_description|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}]}, "missed_items": {"missed_issues": {"runtime_issues": [{"issue": "string", "current_specification": "string", "blocked_functionality": "string", "evidence": ["strings"], "recommendation": "string"}], "deployment_issues": [{"issue": "string", "current_specification": "string", "blocked_functionality": "string", "evidence": ["strings"], "recommendation": "string"}], "dependency_issues": [{"issue": "string", "current_specification": "string", "blocked_functionality": "string", "evidence": ["strings"], "recommendation": "string"}], "integration_issues": [{"issue": "string", "current_specification": "string", "blocked_functionality": "string", "evidence": ["strings"], "recommendation": "string"}]}, "missed_gaps": {"runtime_gaps": [{"gap": "string", "current_state": "string", "blocked_functionality": "string", "evidence": ["strings"], "recommendation": "string"}], "deployment_gaps": [{"gap": "string", "current_state": "string", "blocked_functionality": "string", "evidence": ["strings"], "recommendation": "string"}], "dependency_gaps": [{"gap": "string", "current_state": "string", "blocked_functionality": "string", "evidence": ["strings"], "recommendation": "string"}], "integration_gaps": [{"gap": "string", "current_state": "string", "blocked_functionality": "string", "evidence": ["strings"], "recommendation": "string"}]}}, "synthesis_feedback": {"quality": {"rating": "high|medium|low", "justification": "string"}, "missed_connections": ["strings"], "improvement_suggestions": ["strings"]}}}
```

## Field Descriptions

### Perspective Quality
- **issue_analysis**: Quality assessment of the problematic aspects identification
- **gap_analysis**: Quality assessment of the missing elements identification

For each perspective:
- **comprehensiveness**: Overall assessment of coverage across all categories
- **evidence_quality**: Evaluation of the supporting evidence provided
- **criticality_assessment**: Assessment of how accurately criticality is judged

### Item-Specific Feedback
Detailed feedback on specific issues and gaps identified in the original analysis:
- **item_index**: The index (0-based) of the item in the original analysis
- **feedback_type**: The type of feedback being provided
- **details**: Specific details about the feedback
- **correction**: Suggested correction or improvement
- **recommended_action**: Whether to keep, modify, or remove the item

### Missed Items
Items that were not identified in the original analysis:
- **missed_issues**: Issues that should have been identified
- **missed_gaps**: Gaps that should have been identified

### Synthesis Feedback
Assessment of how well the two perspectives were synthesized:
- **quality**: Overall rating of the synthesis quality
- **missed_connections**: Important connections between issues and gaps that were overlooked
- **improvement_suggestions**: Specific ways to enhance the synthesis

## Reflection Principles

1. Prioritize system viability over optimization
2. Question assumptions about what is truly "critical"
3. Seek concrete evidence rather than theoretical concerns
4. Consider minimum viable functionality rather than ideal scenarios
5. Be willing to recognize and correct overstated criticality
6. Assess how well the two perspectives complement each other
7. Evaluate the effectiveness of the synthesis in integrating insights
"""

phase_one_core_requirements_reflection_schema = {
  "type": "object",
  "properties": {
    "reflection_results": {
      "type": "object",
      "properties": {
        "perspective_quality": {
          "type": "object",
          "properties": {
            "issue_analysis": {
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
                "criticality_assessment": {
                  "type": "object",
                  "properties": {
                    "rating": {
                      "type": "string",
                      "enum": ["high", "medium", "low"]
                    },
                    "justification": {
                      "type": "string"
                    },
                    "overestimated_items": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    }
                  },
                  "required": ["rating", "justification", "overestimated_items"]
                }
              },
              "required": ["comprehensiveness", "evidence_quality", "criticality_assessment"]
            },
            "gap_analysis": {
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
                "criticality_assessment": {
                  "type": "object",
                  "properties": {
                    "rating": {
                      "type": "string",
                      "enum": ["high", "medium", "low"]
                    },
                    "justification": {
                      "type": "string"
                    },
                    "overestimated_items": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    }
                  },
                  "required": ["rating", "justification", "overestimated_items"]
                }
              },
              "required": ["comprehensiveness", "evidence_quality", "criticality_assessment"]
            }
          },
          "required": ["issue_analysis", "gap_analysis"]
        },
        "item_specific_feedback": {
          "type": "object",
          "properties": {
            "runtime_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "item_index": {
                    "type": "integer"
                  },
                  "feedback_type": {
                    "type": "string",
                    "enum": ["overestimated_criticality", "insufficient_evidence", "imprecise_description", "weak_recommendation"]
                  },
                  "details": {
                    "type": "string"
                  },
                  "correction": {
                    "type": "string"
                  },
                  "recommended_action": {
                    "type": "string",
                    "enum": ["KEEP", "MODIFY", "REMOVE"]
                  }
                },
                "required": ["item_index", "feedback_type", "details", "correction", "recommended_action"]
              }
            },
            "deployment_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "item_index": {
                    "type": "integer"
                  },
                  "feedback_type": {
                    "type": "string",
                    "enum": ["overestimated_criticality", "insufficient_evidence", "imprecise_description", "weak_recommendation"]
                  },
                  "details": {
                    "type": "string"
                  },
                  "correction": {
                    "type": "string"
                  },
                  "recommended_action": {
                    "type": "string",
                    "enum": ["KEEP", "MODIFY", "REMOVE"]
                  }
                },
                "required": ["item_index", "feedback_type", "details", "correction", "recommended_action"]
              }
            },
            "dependency_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "item_index": {
                    "type": "integer"
                  },
                  "feedback_type": {
                    "type": "string",
                    "enum": ["overestimated_criticality", "insufficient_evidence", "imprecise_description", "weak_recommendation"]
                  },
                  "details": {
                    "type": "string"
                  },
                  "correction": {
                    "type": "string"
                  },
                  "recommended_action": {
                    "type": "string",
                    "enum": ["KEEP", "MODIFY", "REMOVE"]
                  }
                },
                "required": ["item_index", "feedback_type", "details", "correction", "recommended_action"]
              }
            },
            "integration_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "item_index": {
                    "type": "integer"
                  },
                  "feedback_type": {
                    "type": "string",
                    "enum": ["overestimated_criticality", "insufficient_evidence", "imprecise_description", "weak_recommendation"]
                  },
                  "details": {
                    "type": "string"
                  },
                  "correction": {
                    "type": "string"
                  },
                  "recommended_action": {
                    "type": "string",
                    "enum": ["KEEP", "MODIFY", "REMOVE"]
                  }
                },
                "required": ["item_index", "feedback_type", "details", "correction", "recommended_action"]
              }
            },
            "runtime_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "item_index": {
                    "type": "integer"
                  },
                  "feedback_type": {
                    "type": "string",
                    "enum": ["overestimated_criticality", "insufficient_evidence", "imprecise_description", "weak_recommendation"]
                  },
                  "details": {
                    "type": "string"
                  },
                  "correction": {
                    "type": "string"
                  },
                  "recommended_action": {
                    "type": "string",
                    "enum": ["KEEP", "MODIFY", "REMOVE"]
                  }
                },
                "required": ["item_index", "feedback_type", "details", "correction", "recommended_action"]
              }
            },
            "deployment_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "item_index": {
                    "type": "integer"
                  },
                  "feedback_type": {
                    "type": "string",
                    "enum": ["overestimated_criticality", "insufficient_evidence", "imprecise_description", "weak_recommendation"]
                  },
                  "details": {
                    "type": "string"
                  },
                  "correction": {
                    "type": "string"
                  },
                  "recommended_action": {
                    "type": "string",
                    "enum": ["KEEP", "MODIFY", "REMOVE"]
                  }
                },
                "required": ["item_index", "feedback_type", "details", "correction", "recommended_action"]
              }
            },
            "dependency_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "item_index": {
                    "type": "integer"
                  },
                  "feedback_type": {
                    "type": "string",
                    "enum": ["overestimated_criticality", "insufficient_evidence", "imprecise_description", "weak_recommendation"]
                  },
                  "details": {
                    "type": "string"
                  },
                  "correction": {
                    "type": "string"
                  },
                  "recommended_action": {
                    "type": "string",
                    "enum": ["KEEP", "MODIFY", "REMOVE"]
                  }
                },
                "required": ["item_index", "feedback_type", "details", "correction", "recommended_action"]
              }
            },
            "integration_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "item_index": {
                    "type": "integer"
                  },
                  "feedback_type": {
                    "type": "string",
                    "enum": ["overestimated_criticality", "insufficient_evidence", "imprecise_description", "weak_recommendation"]
                  },
                  "details": {
                    "type": "string"
                  },
                  "correction": {
                    "type": "string"
                  },
                  "recommended_action": {
                    "type": "string",
                    "enum": ["KEEP", "MODIFY", "REMOVE"]
                  }
                },
                "required": ["item_index", "feedback_type", "details", "correction", "recommended_action"]
              }
            }
          },
          "required": ["runtime_issues", "deployment_issues", "dependency_issues", "integration_issues", "runtime_gaps", "deployment_gaps", "dependency_gaps", "integration_gaps"]
        },
        "missed_items": {
          "type": "object",
          "properties": {
            "missed_issues": {
              "type": "object",
              "properties": {
                "runtime_issues": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "issue": {
                        "type": "string"
                      },
                      "current_specification": {
                        "type": "string"
                      },
                      "blocked_functionality": {
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
                    "required": ["issue", "current_specification", "blocked_functionality", "evidence", "recommendation"]
                  }
                },
                "deployment_issues": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "issue": {
                        "type": "string"
                      },
                      "current_specification": {
                        "type": "string"
                      },
                      "blocked_functionality": {
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
                    "required": ["issue", "current_specification", "blocked_functionality", "evidence", "recommendation"]
                  }
                },
                "dependency_issues": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "issue": {
                        "type": "string"
                      },
                      "current_specification": {
                        "type": "string"
                      },
                      "blocked_functionality": {
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
                    "required": ["issue", "current_specification", "blocked_functionality", "evidence", "recommendation"]
                  }
                },
                "integration_issues": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "issue": {
                        "type": "string"
                      },
                      "current_specification": {
                        "type": "string"
                      },
                      "blocked_functionality": {
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
                    "required": ["issue", "current_specification", "blocked_functionality", "evidence", "recommendation"]
                  }
                }
              },
              "required": ["runtime_issues", "deployment_issues", "dependency_issues", "integration_issues"]
            },
            "missed_gaps": {
              "type": "object",
              "properties": {
                "runtime_gaps": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "gap": {
                        "type": "string"
                      },
                      "current_state": {
                        "type": "string"
                      },
                      "blocked_functionality": {
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
                    "required": ["gap", "current_state", "blocked_functionality", "evidence", "recommendation"]
                  }
                },
                "deployment_gaps": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "gap": {
                        "type": "string"
                      },
                      "current_state": {
                        "type": "string"
                      },
                      "blocked_functionality": {
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
                    "required": ["gap", "current_state", "blocked_functionality", "evidence", "recommendation"]
                  }
                },
                "dependency_gaps": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "gap": {
                        "type": "string"
                      },
                      "current_state": {
                        "type": "string"
                      },
                      "blocked_functionality": {
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
                    "required": ["gap", "current_state", "blocked_functionality", "evidence", "recommendation"]
                  }
                },
                "integration_gaps": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "gap": {
                        "type": "string"
                      },
                      "current_state": {
                        "type": "string"
                      },
                      "blocked_functionality": {
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
                    "required": ["gap", "current_state", "blocked_functionality", "evidence", "recommendation"]
                  }
                }
              },
              "required": ["runtime_gaps", "deployment_gaps", "dependency_gaps", "integration_gaps"]
            }
          },
          "required": ["missed_issues", "missed_gaps"]
        },
        "synthesis_feedback": {
          "type": "object",
          "properties": {
            "quality": {
              "type": "object",
              "properties": {
                "rating": {
                  "type": "string",
                  "enum": ["high", "medium", "low"]
                },
                "justification": {
                  "type": "string"
                }
              },
              "required": ["rating", "justification"]
            },
            "missed_connections": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "improvement_suggestions": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "required": ["quality", "missed_connections", "improvement_suggestions"]
        }
      },
      "required": ["perspective_quality", "item_specific_feedback", "missed_items", "synthesis_feedback"]
    }
  },
  "required": ["reflection_results"]
}

phase_one_core_requirements_revision_prompt = """# Soil Agent Revision Prompt

You are the Soil Agent performing precise revisions to your dual-perspective analysis based on reflective insights. Your task is to self-correct your initial assessment of environmental requirement issues and gaps by implementing the recommended actions from your reflection phase.

## Revision Purpose

Implement revisions to produce a final, high-fidelity analysis by:
1. Retaining issues and gaps confirmed as critical blockers to core functionality
2. Modifying items where criticality was potentially overstated
3. Removing items determined to be non-critical or insufficiently evidenced
4. Adding missed issues and gaps identified during reflection
5. Strengthening evidence for all retained items
6. Enhancing the synthesis to better integrate insights from both perspectives

## Revision Focus

For each item based on reflection recommendations:
- **KEEP**: Retain the item as initially specified with no changes
- **MODIFY**: Refine the issue/gap description, current specification/state, blocked functionality, evidence, or recommendation to more accurately represent the critical nature of the item
- **REMOVE**: Eliminate items determined to be non-critical optimizations rather than fundamental blockers
- **ADD**: Include newly identified issues or gaps that were missed in the initial analysis

## Output Format

Provide your revised analysis in the following JSON format:

```json
{"revision_metadata": {"processed_feedback": {"perspective_improvements": {"issue_analysis": {"comprehensiveness": ["strings"], "evidence_quality": ["strings"], "criticality_assessment": ["strings"]}, "gap_analysis": {"comprehensiveness": ["strings"], "evidence_quality": ["strings"], "criticality_assessment": ["strings"]}}, "item_adjustments": {"items_removed": {"issues": integer, "gaps": integer}, "items_modified": {"issues": integer, "gaps": integer}, "items_added": {"issues": integer, "gaps": integer}}, "synthesis_improvements": ["strings"]}, "validation_steps": ["strings"]}, "dual_perspective_analysis": {"issue_analysis": {"runtime_issues": [{"issue": "string", "current_specification": "string", "blocked_functionality": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "deployment_issues": [{"issue": "string", "current_specification": "string", "blocked_functionality": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "dependency_issues": [{"issue": "string", "current_specification": "string", "blocked_functionality": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "integration_issues": [{"issue": "string", "current_specification": "string", "blocked_functionality": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}]}, "gap_analysis": {"runtime_gaps": [{"gap": "string", "current_state": "string", "blocked_functionality": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "deployment_gaps": [{"gap": "string", "current_state": "string", "blocked_functionality": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "dependency_gaps": [{"gap": "string", "current_state": "string", "blocked_functionality": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "integration_gaps": [{"gap": "string", "current_state": "string", "blocked_functionality": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}]}, "synthesis": {"key_observations": ["strings"], "cross_cutting_concerns": ["strings"], "prioritized_recommendations": [{"area": "string", "recommendation": "string", "justification": "string", "revision_note": "string"}]}}}
```

## Revision Guidelines

### Perspective Improvements
- Enhance the completeness of issue and gap identification
- Strengthen evidence with specific references to requirements
- Refine criticality assessments to focus only on genuine blockers

### Item Adjustments
- Remove non-critical items that wouldn't truly block core functionality
- Modify items where descriptions, evidence, or recommendations need improvement
- Add missed items that should have been identified in the initial analysis

### Synthesis Improvements
- Strengthen connections between identified issues and gaps
- Enhance cross-cutting concern identification
- Refine prioritized recommendations for comprehensive solutions
- Ensure holistic integration of both perspectives

## Validation Checklist

Before finalizing your revised analysis:
1. Confirm all recommended removals have been implemented
2. Verify all recommended modifications have been made
3. Ensure all missed items have been added
4. Check that evidence is specific and concrete for all items
5. Validate that all items genuinely block core functionality
6. Confirm that synthesis effectively integrates both perspectives
7. Ensure revision notes explain the rationale for each change

## Self-Correction Principles

1. Self-correct without external instruction
2. Apply the insights gained through reflection
3. Maintain focus only on genuinely critical issues and gaps
4. Provide a revision note explaining the rationale for each change
5. Ensure the final output represents only true blockers to fundamental system functionality
6. Default to removing items when evidence is insufficient or criticality is questionable
7. Strengthen the integration between issue and gap perspectives
"""

phase_one_core_requirements_revision_schema = {
  "type": "object",
  "properties": {
    "revision_metadata": {
      "type": "object",
      "properties": {
        "processed_feedback": {
          "type": "object",
          "properties": {
            "perspective_improvements": {
              "type": "object",
              "properties": {
                "issue_analysis": {
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
                    "criticality_assessment": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    }
                  },
                  "required": ["comprehensiveness", "evidence_quality", "criticality_assessment"]
                },
                "gap_analysis": {
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
                    "criticality_assessment": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    }
                  },
                  "required": ["comprehensiveness", "evidence_quality", "criticality_assessment"]
                }
              },
              "required": ["issue_analysis", "gap_analysis"]
            },
            "item_adjustments": {
              "type": "object",
              "properties": {
                "items_removed": {
                  "type": "object",
                  "properties": {
                    "issues": {
                      "type": "integer"
                    },
                    "gaps": {
                      "type": "integer"
                    }
                  },
                  "required": ["issues", "gaps"]
                },
                "items_modified": {
                  "type": "object",
                  "properties": {
                    "issues": {
                      "type": "integer"
                    },
                    "gaps": {
                      "type": "integer"
                    }
                  },
                  "required": ["issues", "gaps"]
                },
                "items_added": {
                  "type": "object",
                  "properties": {
                    "issues": {
                      "type": "integer"
                    },
                    "gaps": {
                      "type": "integer"
                    }
                  },
                  "required": ["issues", "gaps"]
                }
              },
              "required": ["items_removed", "items_modified", "items_added"]
            },
            "synthesis_improvements": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "required": ["perspective_improvements", "item_adjustments", "synthesis_improvements"]
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
    "dual_perspective_analysis": {
      "type": "object",
      "properties": {
        "issue_analysis": {
          "type": "object",
          "properties": {
            "runtime_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "issue": {
                    "type": "string"
                  },
                  "current_specification": {
                    "type": "string"
                  },
                  "blocked_functionality": {
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
                "required": ["issue", "current_specification", "blocked_functionality", "evidence", "recommendation", "revision_note"]
              }
            },
            "deployment_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "issue": {
                    "type": "string"
                  },
                  "current_specification": {
                    "type": "string"
                  },
                  "blocked_functionality": {
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
                "required": ["issue", "current_specification", "blocked_functionality", "evidence", "recommendation", "revision_note"]
              }
            },
            "dependency_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "issue": {
                    "type": "string"
                  },
                  "current_specification": {
                    "type": "string"
                  },
                  "blocked_functionality": {
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
                "required": ["issue", "current_specification", "blocked_functionality", "evidence", "recommendation", "revision_note"]
              }
            },
            "integration_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "issue": {
                    "type": "string"
                  },
                  "current_specification": {
                    "type": "string"
                  },
                  "blocked_functionality": {
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
                "required": ["issue", "current_specification", "blocked_functionality", "evidence", "recommendation", "revision_note"]
              }
            }
          },
          "required": ["runtime_issues", "deployment_issues", "dependency_issues", "integration_issues"]
        },
        "gap_analysis": {
          "type": "object",
          "properties": {
            "runtime_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap": {
                    "type": "string"
                  },
                  "current_state": {
                    "type": "string"
                  },
                  "blocked_functionality": {
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
                "required": ["gap", "current_state", "blocked_functionality", "evidence", "recommendation", "revision_note"]
              }
            },
            "deployment_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap": {
                    "type": "string"
                  },
                  "current_state": {
                    "type": "string"
                  },
                  "blocked_functionality": {
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
                "required": ["gap", "current_state", "blocked_functionality", "evidence", "recommendation", "revision_note"]
              }
            },
            "dependency_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap": {
                    "type": "string"
                  },
                  "current_state": {
                    "type": "string"
                  },
                  "blocked_functionality": {
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
                "required": ["gap", "current_state", "blocked_functionality", "evidence", "recommendation", "revision_note"]
              }
            },
            "integration_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap": {
                    "type": "string"
                  },
                  "current_state": {
                    "type": "string"
                  },
                  "blocked_functionality": {
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
                "required": ["gap", "current_state", "blocked_functionality", "evidence", "recommendation", "revision_note"]
              }
            }
          },
          "required": ["runtime_gaps", "deployment_gaps", "dependency_gaps", "integration_gaps"]
        },
        "synthesis": {
          "type": "object",
          "properties": {
            "key_observations": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "cross_cutting_concerns": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "prioritized_recommendations": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "area": {
                    "type": "string"
                  },
                  "recommendation": {
                    "type": "string"
                  },
                  "justification": {
                    "type": "string"
                  },
                  "revision_note": {
                    "type": "string"
                  }
                },
                "required": ["area", "recommendation", "justification", "revision_note"]
              }
            }
          },
          "required": ["key_observations", "cross_cutting_concerns", "prioritized_recommendations"]
        }
      },
      "required": ["issue_analysis", "gap_analysis", "synthesis"]
    }
  },
  "required": ["revision_metadata", "dual_perspective_analysis"]
}