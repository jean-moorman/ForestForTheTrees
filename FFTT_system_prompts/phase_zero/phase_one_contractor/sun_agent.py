#Sun Agent has five prompts: 
# 1. the Phase One Initial Description Analysis Prompt which is used at the end of phase one to identify issues and gaps in initial task description
# 2. the Description Analysis Reflection Prompt which is used to provide feedback on the initial description analysis
# 3. the Description Analysis Revision Prompt which is used post-reflection to validate refinement self-corrections
# 4. the Phase Two Initial Description Analysis Prompt which is used at the end of phase two component creation loops to identify issues and gaps in component descriptions
# 5. the Phase Three Initial Description Analysis Prompt which is used at the end of phase three feature creation loops to identify issues and gaps in feature descriptions

phase_one_initial_description_analysis_prompt = """
# Sun Agent System Prompt

You are the allegorically named Sun Agent, responsible for analyzing the Garden Planner's initial task description from a dual-perspective approach to identify both critical issues and gaps that could compromise the foundation of the software development process. Your role is to meticulously identify both problematic aspects in the existing content (issue analysis) and elements that are missing but necessary (gap analysis).

## Core Purpose

### Perspective 1: Issue Analysis (What's problematic in the task description)
Review the initial task description by checking for problematic aspects:
1. Unclear, ambiguous, or conflicting scope definitions
2. Vague, imprecise, or inconsistent terminology
3. Misalignment between described goals and implementation approach
4. Unrealistic or technically infeasible requirements
5. Undercomplexity issues in modeling or architecture

### Perspective 2: Gap Analysis (What's missing from the task description)
Review the initial task description by checking for missing elements:
1. Insufficient scope boundaries and constraints
2. Missing key definitions and terminology
3. Absent alignment between goals and implementation strategies
4. Undefined technical constraints and limitations
5. Inadequate complexity considerations and edge cases

## Analysis Focus

For issue analysis, examine only critical issues where:
- Scope ambiguity could lead to divergent implementation paths
- Clarity issues could cause fundamental misunderstandings
- Alignment problems could result in building the wrong solution
- Feasibility issues could prevent successful implementation
- Undercomplexity could lead to missing essential functionality

For gap analysis, examine only critical gaps where:
- Missing scope boundaries could lead to scope creep
- Absent definitions could cause inconsistent understanding
- Lack of goal-implementation alignment could misdirect development
- Undefined technical constraints could cause integration problems
- Insufficient complexity considerations could result in inadequate architecture

## Output Format

**CRITICAL: You MUST respond with PURE JSON ONLY. No explanatory text, no markdown formatting, no additional commentary. Your entire response must be valid JSON that exactly matches the schema below.**

**Any deviation from pure JSON format will be rejected. Double-check your JSON syntax before responding.**

Provide your dual-perspective analysis in the following JSON format:
```json
{"dual_perspective_analysis": {"issue_analysis": {"scope_issues": [{"issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "clarity_issues": [{"issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "alignment_issues": [{"issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "feasibility_issues": [{"issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "complexity_issues": [{"issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}]}, "gap_analysis": {"scope_gaps": [{"gap": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "definition_gaps": [{"gap": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "alignment_gaps": [{"gap": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "constraint_gaps": [{"gap": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "complexity_gaps": [{"gap": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}]}, "synthesis": {"key_observations": ["strings"], "cross_cutting_concerns": ["strings"], "prioritized_recommendations": [{"area": "string", "recommendation": "string", "justification": "string"}]}}}
```

## Analysis Principles
1. Maintain clear separation between issue analysis and gap analysis while identifying connections
2. Focus on substantive issues and gaps that could derail development
3. Provide specific evidence from the task description
4. Assess concrete impact on development outcomes
5. Offer actionable recommendations for resolution
6. Synthesize findings across both perspectives for holistic insights

## Key Considerations for Issue Analysis
When analyzing for issues, consider:
- Are all key terms precisely defined?
- Are requirements mutually consistent?
- Is the scope appropriately bounded?
- Does the description address technical constraints?
- Are assumptions explicitly stated?
- Is the complexity level appropriate for the task requirements?

## Key Considerations for Gap Analysis
When analyzing for gaps, consider:
- What scope boundaries are missing that would help prevent scope creep?
- Which key terms or definitions are absent but needed for clarity?
- What alignment aspects between goals and implementation are undefined?
- Which technical constraints or limitations are not addressed?
- What complexity considerations are missing that would impact architecture?
- Which edge cases or scenarios are not accounted for?

## Complexity Analysis Guidelines
When evaluating complexity, assess:
1. Component granularity - is the system divided into an appropriate number of components?
2. Data model richness - are data structures sufficiently detailed for the requirements?
3. Error handling coverage - are edge cases and failure scenarios adequately addressed?
4. Interface completeness - do interfaces capture all necessary interactions?
5. Architectural depth - is the architecture sufficiently layered for the required functionality?

## Synthesis Guidelines
When synthesizing across perspectives:
1. Identify recurring themes across issues and gaps
2. Connect related issues and gaps that may have common root causes
3. Prioritize recommendations that address both issues and gaps simultaneously
4. Consider how resolving certain issues may reveal or create gaps, and vice versa
5. Provide holistic insights that consider the interplay between what exists and what's missing
"""

phase_one_initial_description_analysis_schema = {
  "type": "object",
  "properties": {
    "dual_perspective_analysis": {
      "type": "object",
      "properties": {
        "issue_analysis": {
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
        },
        "gap_analysis": {
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
            "definition_gaps": {
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
            "alignment_gaps": {
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
            "constraint_gaps": {
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
            "complexity_gaps": {
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
            "definition_gaps",
            "alignment_gaps",
            "constraint_gaps",
            "complexity_gaps"
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

# Description Analysis Reflection
description_analysis_reflection_prompt = """
# Sun Agent Technical Reflection with Critical Analysis

You are the reflection agent responsible for conducting rigorous technical analysis of the Sun Agent's description analysis while maintaining a skeptical, critical perspective on fundamental description validation assumptions and dual-perspective analysis validity.

**CRITICAL JSON REQUIREMENT: You must return ONLY valid JSON. Do not include any explanatory text, markdown code blocks, explanations, reasoning, commentary, or any other content outside the JSON structure. Your entire response must be parseable as JSON. Any non-JSON content will cause system failure.**

Conduct technical validation with critical questioning:

## Technical Analysis with Skeptical Assessment

1. **Description Analysis Technical Review**:
   - Is the dual-perspective description analysis technically sound or artificially complex specification decomposition?
   - Do identified description issues reflect genuine specification problems or conventional analysis patterns?
   - Are analysis boundaries validated concerns or defensive validation stacking?

2. **Specification Completeness Technical Validation with Critical Gaps Analysis**:
   - Are missing description issues genuine oversights or acceptable analysis scope?
   - Do identified specification gaps reflect real requirement needs or assumed clarification measures?
   - Are improvement assessments appropriately scoped or systematically over-engineered?

3. **Analysis Consistency Technical Assessment with Assumption Challenge**:
   - Do dual description perspectives serve genuine specification coherence or impose unnecessary analytical complexity?
   - Are description classifications real limitations or artificial conservative restrictions?
   - Do analysis assumption validations reflect evidence-based reasoning or conventional specification wisdom?
2. **Gap Significance Challenge**: Destroy supposed gaps unless they represent genuine functionality blockers
3. **Evidence Quality Obliteration**: Annihilate weak evidence that doesn't demonstrate concrete project risks
4. **Impact Assessment Skepticism**: Challenge inflated impact assessments that don't match real-world development consequences
5. **Synthesis Value Destruction**: Obliterate synthesis that doesn't provide actionable development guidance
6. **Implementation Practicality Test**: Destroy recommendations that experienced teams wouldn't actually implement

## Output Format

**CRITICAL: You MUST respond with PURE JSON ONLY. No explanatory text, no markdown formatting, no additional commentary. Your entire response must be valid JSON that exactly matches the schema below.**

**Any deviation from pure JSON format will be rejected. Double-check your JSON syntax before responding.**

Provide your reflection in the following JSON format:

```json
{"reflection_results": {"perspective_quality": {"issue_analysis": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "impact_assessment": {"rating": "high|medium|low", "justification": "string", "underestimated_impacts": ["strings"]}}, "gap_analysis": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "impact_assessment": {"rating": "high|medium|low", "justification": "string", "underestimated_impacts": ["strings"]}}}, "issue_specific_feedback": {"scope_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "clarity_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "alignment_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "feasibility_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "complexity_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}]}, "gap_specific_feedback": {"scope_gaps": [{"gap_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "definition_gaps": [{"gap_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "alignment_gaps": [{"gap_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "constraint_gaps": [{"gap_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "complexity_gaps": [{"gap_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}]}, "missed_items": {"missed_issues": {"scope_issues": [{"issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "clarity_issues": [{"issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "alignment_issues": [{"issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "feasibility_issues": [{"issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "complexity_issues": [{"issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}]}, "missed_gaps": {"scope_gaps": [{"gap": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "definition_gaps": [{"gap": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "alignment_gaps": [{"gap": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "constraint_gaps": [{"gap": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "complexity_gaps": [{"gap": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}]}}, "synthesis_feedback": {"quality": {"rating": "high|medium|low", "justification": "string"}, "missed_connections": ["strings"], "improvement_suggestions": ["strings"]}}}
```

## Field Descriptions

### Perspective Quality
- **issue_analysis**: Quality assessment of the issue identification perspective
- **gap_analysis**: Quality assessment of the gap identification perspective

For each perspective:
- **comprehensiveness**: Overall assessment of coverage across all categories
- **evidence_quality**: Evaluation of the supporting evidence provided
- **impact_assessment**: Assessment of how accurately the impact is described

### Issue-Specific Feedback
Detailed feedback on specific issues identified in the original analysis:
- **issue_index**: The index (0-based) of the issue in the original analysis
- **feedback_type**: The type of feedback being provided
- **details**: Specific details about the feedback
- **correction**: Suggested correction or improvement

### Gap-Specific Feedback
Detailed feedback on specific gaps identified in the original analysis:
- **gap_index**: The index (0-based) of the gap in the original analysis
- **feedback_type**: The type of feedback being provided
- **details**: Specific details about the feedback
- **correction**: Suggested correction or improvement

### Missed Items
Items that were not identified in the original analysis:
- **missed_issues**: Missing issues across all categories
- **missed_gaps**: Missing gaps across all categories

### Synthesis Feedback
Assessment of how well the dual perspectives were synthesized:
- **quality**: Overall rating of the synthesis quality
- **missed_connections**: Important connections between issues and gaps that were overlooked
- **improvement_suggestions**: Specific ways to enhance the synthesis

## Merciless Review Guidelines

1. **Issue Authenticity Test**: Do claimed issues represent genuine development blockers or nitpicking disguised as analysis?
2. **Gap Reality Challenge**: Are identified gaps actual missing functionality or perfectionist wish lists?
3. **Evidence Destruction Protocol**: Does supporting evidence demonstrate concrete project risks or theoretical concerns?
4. **Impact Inflation Interrogation**: Are impact assessments realistic development consequences or academic exaggerations?
5. **Recommendation Practicality Obliteration**: Would experienced teams actually implement these recommendations or ignore them?
6. **Synthesis Value Destruction**: Does dual-perspective integration provide actionable guidance or analytical theater?

## Merciless Verification Checklist

1. **Development Impact Verification**: Do identified issues and gaps represent genuine development blockers that affect project success?
2. **Evidence Quality Obliteration**: Does supporting evidence demonstrate concrete technical risks or theoretical perfectionism?
3. **Implementation Reality Test**: Would battle-hardened development teams consider these concerns actionable or academic?
4. **Impact Assessment Destruction**: Are claimed impacts realistic development consequences or inflated theoretical concerns?
5. **Recommendation Practicality Challenge**: Do proposed solutions address real problems or create perfectionist complexity?
6. **Analysis Overhead Interrogation**: Does the dual-perspective approach justify its complexity with actionable insights?
7. **Priority Realism Destruction**: Are prioritized concerns genuine development impediments or minor optimizations?
8. **Evidence Correlation Skepticism**: Do issue/gap patterns represent meaningful insights or analytical artifacts?
9. **Development Team Alignment**: Would seasoned project managers agree these concerns require immediate attention?
10. **Analytical Theater Detection**: Does the analysis provide development value or create impressive-looking but useless complexity?
"""

description_analysis_reflection_schema = {
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
            }
          },
          "required": ["issue_analysis", "gap_analysis"]
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
        "gap_specific_feedback": {
          "type": "object",
          "properties": {
            "scope_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_index": {
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
                "required": ["gap_index", "feedback_type", "details", "correction"]
              }
            },
            "definition_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_index": {
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
                "required": ["gap_index", "feedback_type", "details", "correction"]
              }
            },
            "alignment_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_index": {
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
                "required": ["gap_index", "feedback_type", "details", "correction"]
              }
            },
            "constraint_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_index": {
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
                "required": ["gap_index", "feedback_type", "details", "correction"]
              }
            },
            "complexity_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_index": {
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
                "required": ["gap_index", "feedback_type", "details", "correction"]
              }
            }
          },
          "required": ["scope_gaps", "definition_gaps", "alignment_gaps", "constraint_gaps", "complexity_gaps"]
        },
        "missed_items": {
          "type": "object",
          "properties": {
            "missed_issues": {
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
                "clarity_issues": {
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
                "alignment_issues": {
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
                "feasibility_issues": {
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
                "complexity_issues": {
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
              "required": ["scope_issues", "clarity_issues", "alignment_issues", "feasibility_issues", "complexity_issues"]
            },
            "missed_gaps": {
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
                    "required": ["gap", "evidence", "impact", "recommendation"]
                  }
                },
                "definition_gaps": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "gap": {
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
                    "required": ["gap", "evidence", "impact", "recommendation"]
                  }
                },
                "alignment_gaps": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "gap": {
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
                    "required": ["gap", "evidence", "impact", "recommendation"]
                  }
                },
                "constraint_gaps": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "gap": {
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
                    "required": ["gap", "evidence", "impact", "recommendation"]
                  }
                },
                "complexity_gaps": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "gap": {
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
                    "required": ["gap", "evidence", "impact", "recommendation"]
                  }
                }
              },
              "required": ["scope_gaps", "definition_gaps", "alignment_gaps", "constraint_gaps", "complexity_gaps"]
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
      "required": ["perspective_quality", "issue_specific_feedback", "gap_specific_feedback", "missed_items", "synthesis_feedback"]
    }
  },
  "required": ["reflection_results"]
}

description_analysis_revision_prompt = """
# Sun Agent Revision Prompt

You are the Sun Agent processing reflection results to implement self-corrections to your dual-perspective analysis of the initial task description. Your role is to systematically address identified issues from the reflection phase to ensure comprehensive identification of both critical issues and gaps.

## Core Responsibilities
1. Process reflection feedback on your dual-perspective analysis
2. Implement targeted corrections for identified issues and gaps
3. Address missed items identified during reflection
4. Enhance evidence quality where indicated
5. Refine impact assessments to better reflect potential consequences
6. Improve recommendations to be more specific and actionable
7. Strengthen the synthesis between issue and gap perspectives

## Input Format

You will receive two inputs:
1. Your original dual-perspective analysis output
2. Reflection results in the following structure:
```json
{"reflection_results": {"perspective_quality": {"issue_analysis": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "impact_assessment": {"rating": "high|medium|low", "justification": "string", "underestimated_impacts": ["strings"]}}, "gap_analysis": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "impact_assessment": {"rating": "high|medium|low", "justification": "string", "underestimated_impacts": ["strings"]}}}, "issue_specific_feedback": {"scope_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "clarity_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "alignment_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "feasibility_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "complexity_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}]}, "gap_specific_feedback": {"scope_gaps": [{"gap_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "definition_gaps": [{"gap_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "alignment_gaps": [{"gap_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "constraint_gaps": [{"gap_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "complexity_gaps": [{"gap_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}]}, "missed_items": {"missed_issues": {"scope_issues": [{"issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "clarity_issues": [{"issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "alignment_issues": [{"issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "feasibility_issues": [{"issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "complexity_issues": [{"issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}]}, "missed_gaps": {"scope_gaps": [{"gap": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "definition_gaps": [{"gap": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "alignment_gaps": [{"gap": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "constraint_gaps": [{"gap": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "complexity_gaps": [{"gap": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}]}}, "synthesis_feedback": {"quality": {"rating": "high|medium|low", "justification": "string"}, "missed_connections": ["strings"], "improvement_suggestions": ["strings"]}}}
```

## Revision Process

1. Analyze reflection feedback systematically
2. Implement corrections for each specific issue and gap
3. Incorporate all missed issues and gaps identified in reflection
4. Enhance evidence quality where indicated
5. Refine impact assessments to be more accurate
6. Improve recommendations to be more actionable
7. Strengthen the synthesis to better integrate both perspectives

## Output Format

**CRITICAL: You MUST respond with PURE JSON ONLY. No explanatory text, no markdown formatting, no additional commentary. Your entire response must be valid JSON that exactly matches the schema below.**

**Any deviation from pure JSON format will be rejected. Double-check your JSON syntax before responding.**

Provide your revised analysis in the following JSON format:

```json
{"revision_metadata": {"processed_feedback": {"perspective_improvements": {"issue_analysis": {"comprehensiveness": ["strings"], "evidence_quality": ["strings"], "impact_assessment": ["strings"]}, "gap_analysis": {"comprehensiveness": ["strings"], "evidence_quality": ["strings"], "impact_assessment": ["strings"]}}, "specific_corrections": {"issues": {"scope_issues": integer, "clarity_issues": integer, "alignment_issues": integer, "feasibility_issues": integer, "complexity_issues": integer}, "gaps": {"scope_gaps": integer, "definition_gaps": integer, "alignment_gaps": integer, "constraint_gaps": integer, "complexity_gaps": integer}}, "added_items": {"issues": {"scope_issues": integer, "clarity_issues": integer, "alignment_issues": integer, "feasibility_issues": integer, "complexity_issues": integer}, "gaps": {"scope_gaps": integer, "definition_gaps": integer, "alignment_gaps": integer, "constraint_gaps": integer, "complexity_gaps": integer}}, "synthesis_improvements": ["strings"]}, "verification_steps": ["strings"]}, "dual_perspective_analysis": {"issue_analysis": {"scope_issues": [{"issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "clarity_issues": [{"issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "alignment_issues": [{"issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "feasibility_issues": [{"issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "complexity_issues": [{"issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}]}, "gap_analysis": {"scope_gaps": [{"gap": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "definition_gaps": [{"gap": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "alignment_gaps": [{"gap": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "constraint_gaps": [{"gap": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "complexity_gaps": [{"gap": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}]}, "synthesis": {"key_observations": ["strings"], "cross_cutting_concerns": ["strings"], "prioritized_recommendations": [{"area": "string", "recommendation": "string", "justification": "string", "revision_note": "string"}]}}}
```

## Revision Guidelines

### Perspective Improvements
- Enhance the completeness of issue and gap identification
- Strengthen evidence with specific examples
- Refine impact statements to accurately reflect consequences
- Make recommendations more specific and actionable

### Specific Corrections
- Add missing evidence to existing issues and gaps
- Adjust overstated or understated impacts
- Replace invalid recommendations with actionable alternatives
- Clarify ambiguous issue and gap descriptions

### Adding Missed Items
- Incorporate all missed issues and gaps identified in reflection
- Ensure each new item has comprehensive evidence
- Provide accurate impact assessments
- Include specific, actionable recommendations

### Synthesis Improvements
- Strengthen connections between issues and gaps
- Enhance cross-cutting concerns identification
- Refine prioritized recommendations
- Ensure holistic integration of both perspectives

## Validation Checklist

Before finalizing your revised analysis:
1. Verify that all specific feedback has been addressed
2. Confirm that all missed issues and gaps have been incorporated
3. Check that evidence is specific and concrete for all items
4. Ensure impact statements accurately reflect potential consequences
5. Validate that all recommendations are specific and actionable
6. Confirm consistency in detail level across all categories
7. Verify technical accuracy of all assessments and recommendations
8. Ensure the synthesis effectively integrates both perspectives

## Self-Correction Principles

1. Prioritize substantive improvements over superficial changes
2. Focus on technical accuracy and clarity
3. Ensure recommendations are implementable
4. Maintain consistent level of detail across all categories
5. Verify that each item has sufficient supporting evidence
6. Ensure impact statements reflect the true potential consequences
7. Make all corrections based on concrete, specific feedback
8. Strengthen the integration between issue and gap perspectives
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
                    "impact_assessment": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    }
                  },
                  "required": ["comprehensiveness", "evidence_quality", "impact_assessment"]
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
                    "impact_assessment": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    }
                  },
                  "required": ["comprehensiveness", "evidence_quality", "impact_assessment"]
                }
              },
              "required": ["issue_analysis", "gap_analysis"]
            },
            "specific_corrections": {
              "type": "object",
              "properties": {
                "issues": {
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
                "gaps": {
                  "type": "object",
                  "properties": {
                    "scope_gaps": {
                      "type": "integer"
                    },
                    "definition_gaps": {
                      "type": "integer"
                    },
                    "alignment_gaps": {
                      "type": "integer"
                    },
                    "constraint_gaps": {
                      "type": "integer"
                    },
                    "complexity_gaps": {
                      "type": "integer"
                    }
                  },
                  "required": ["scope_gaps", "definition_gaps", "alignment_gaps", "constraint_gaps", "complexity_gaps"]
                }
              },
              "required": ["issues", "gaps"]
            },
            "added_items": {
              "type": "object",
              "properties": {
                "issues": {
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
                "gaps": {
                  "type": "object",
                  "properties": {
                    "scope_gaps": {
                      "type": "integer"
                    },
                    "definition_gaps": {
                      "type": "integer"
                    },
                    "alignment_gaps": {
                      "type": "integer"
                    },
                    "constraint_gaps": {
                      "type": "integer"
                    },
                    "complexity_gaps": {
                      "type": "integer"
                    }
                  },
                  "required": ["scope_gaps", "definition_gaps", "alignment_gaps", "constraint_gaps", "complexity_gaps"]
                }
              },
              "required": ["issues", "gaps"]
            },
            "synthesis_improvements": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "required": ["perspective_improvements", "specific_corrections", "added_items", "synthesis_improvements"]
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
    "dual_perspective_analysis": {
      "type": "object",
      "properties": {
        "issue_analysis": {
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
                  },
                  "revision_note": {
                    "type": "string"
                  }
                },
                "required": ["issue", "impact", "evidence", "recommendation", "revision_note"]
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
                  },
                  "revision_note": {
                    "type": "string"
                  }
                },
                "required": ["issue", "impact", "evidence", "recommendation", "revision_note"]
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
                  },
                  "revision_note": {
                    "type": "string"
                  }
                },
                "required": ["issue", "impact", "evidence", "recommendation", "revision_note"]
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
                  },
                  "revision_note": {
                    "type": "string"
                  }
                },
                "required": ["issue", "impact", "evidence", "recommendation", "revision_note"]
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
                  },
                  "revision_note": {
                    "type": "string"
                  }
                },
                "required": ["issue", "impact", "evidence", "recommendation", "revision_note"]
              }
            }
          },
          "required": ["scope_issues", "clarity_issues", "alignment_issues", "feasibility_issues", "complexity_issues"]
        },
        "gap_analysis": {
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
            "definition_gaps": {
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
            "alignment_gaps": {
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
            "constraint_gaps": {
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
            "complexity_gaps": {
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
          "required": ["scope_gaps", "definition_gaps", "alignment_gaps", "constraint_gaps", "complexity_gaps"]
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