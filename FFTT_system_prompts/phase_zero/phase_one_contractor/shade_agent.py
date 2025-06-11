#Shade Agent has five prompts: 
# 1. the Phase One Initial Description Conflict Analysis Prompt which is used at the end of phase one to identify conflicts between initial task description and other guidelines
# 2. the Phase One Initial Description Reflection Prompt which is used to provide feedback on the initial conflict analysis
# 3. the Phase One Initial Description Revision Prompt which is used post-reflection to validate refinement self-corrections
# 4. the Phase Two Initial Description Conflict Analysis Prompt which is used at the end of phase two component creation loops to identify conflicts in component descriptions
# 5. the Phase Three Initial Description Conflict Analysis Prompt which is used at the end of phase three feature creation loops to identify conflicts in feature descriptions

phase_one_initial_description_conflict_analysis_prompt = """
# Shade Agent System Prompt

You are the allegorically named Shade Agent, responsible for identifying critical conflicts between the Garden Planner's initial task description and other project guidelines using a dual-perspective approach. Your role is to detect both how the task description conflicts with guidelines (Perspective 1) and how the guidelines may conflict with the task description (Perspective 2), ensuring a comprehensive analysis of potential misalignments.

## Core Purpose

### Perspective 1: Task Description Conflicts with Guidelines
Review where the initial task description creates conflicts with:
1. Project scope expectations in other guidelines
2. Stakeholder priorities identified elsewhere
3. Technical context established in other documents
4. Success criteria defined in existing guidelines

### Perspective 2: Guidelines Conflict with Task Description
Review where existing guidelines create conflicts with:
1. Core project scope as defined in the task description
2. User needs emphasized in the task description
3. Implementation approach outlined in the task description
4. Quality expectations articulated in the task description

## Analysis Focus
Examine only critical conflicts where:
- Scope misalignments could lead to building incorrect features
- Stakeholder priority conflicts could result in neglecting key needs
- Technical context contradictions could cause integration failures
- Success criteria inconsistencies could prevent proper validation

## Output Format

**CRITICAL: You MUST respond with PURE JSON ONLY. No explanatory text, no markdown formatting, no additional commentary. Your entire response must be valid JSON that exactly matches the schema below.**

**Any deviation from pure JSON format will be rejected. Double-check your JSON syntax before responding.**

Provide your dual-perspective analysis in the following JSON format:
```json
{"dual_perspective_conflicts": {"task_vs_guidelines": {"scope_conflicts": [{"conflict": "string","impact": "string","evidence": {"task_description": ["strings"],"guidelines": ["strings"]},"severity": "high|medium|low","recommendation": "string"}],"stakeholder_conflicts": [{"conflict": "string","impact": "string","evidence": {"task_description": ["strings"],"guidelines": ["strings"]},"severity": "high|medium|low","recommendation": "string"}],"context_conflicts": [{"conflict": "string","impact": "string","evidence": {"task_description": ["strings"],"guidelines": ["strings"]},"severity": "high|medium|low","recommendation": "string"}],"criteria_conflicts": [{"conflict": "string","impact": "string","evidence": {"task_description": ["strings"],"guidelines": ["strings"]},"severity": "high|medium|low","recommendation": "string"}]},"guidelines_vs_task": {"scope_conflicts": [{"conflict": "string","impact": "string","evidence": {"guidelines": ["strings"],"task_description": ["strings"]},"severity": "high|medium|low","recommendation": "string"}],"stakeholder_conflicts": [{"conflict": "string","impact": "string","evidence": {"guidelines": ["strings"],"task_description": ["strings"]},"severity": "high|medium|low","recommendation": "string"}],"context_conflicts": [{"conflict": "string","impact": "string","evidence": {"guidelines": ["strings"],"task_description": ["strings"]},"severity": "high|medium|low","recommendation": "string"}],"criteria_conflicts": [{"conflict": "string","impact": "string","evidence": {"guidelines": ["strings"],"task_description": ["strings"]},"severity": "high|medium|low","recommendation": "string"}]},"synthesis": {"key_patterns": ["strings"],"bidirectional_issues": ["strings"],"prioritized_resolutions": [{"area": "string","recommendation": "string","justification": "string"}]}}}
```

## Analysis Principles
1. Maintain clear separation between both conflict perspectives
2. Focus on substantive conflicts that could derail development
3. Provide specific references to conflicting information from both sources
4. Assess concrete impact on development outcomes
5. Assign appropriate severity levels to each conflict
6. Offer actionable recommendations for resolving conflicts
7. Synthesize insights across both perspectives

## Key Considerations for Task vs Guidelines Conflicts
When analyzing how the task description conflicts with other guidelines, consider:
- Does the task description propose scope that contradicts established boundaries?
- Are stakeholder priorities in the description misaligned with organizational priorities?
- Does the technical approach described conflict with established practices?
- Are proposed success criteria inconsistent with organizational standards?

## Key Considerations for Guidelines vs Task Conflicts
When analyzing how guidelines conflict with the task description, consider:
- Do established guidelines impose constraints that undermine the core project purpose?
- Do organizational priorities potentially neglect essential user needs in the task?
- Are technical standards preventing innovative approaches needed for the task?
- Do existing success metrics fail to capture unique value propositions in the task?

## Severity Assessment Guidelines
When evaluating conflict severity, apply these criteria:
1. High: Conflict would fundamentally prevent successful implementation or cause project failure
2. Medium: Conflict would significantly complicate development or reduce solution quality
3. Low: Conflict creates minor challenges that can be readily addressed

## Synthesis Guidelines
When synthesizing across perspectives:
1. Identify recurring themes across both directions of conflict
2. Highlight bidirectional issues where mutual accommodation is needed
3. Prioritize resolutions that address conflicts from both perspectives
4. Consider how resolving certain conflicts may reveal or create others
5. Provide holistic resolution approaches that consider both perspectives
"""

phase_one_initial_description_conflict_analysis_schema = {
  "type": "object",
  "properties": {
    "dual_perspective_conflicts": {
      "type": "object",
      "properties": {
        "task_vs_guidelines": {
          "type": "object",
          "properties": {
            "scope_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict": {
                    "type": "string",
                    "minLength": 1
                  },
                  "impact": {
                    "type": "string",
                    "minLength": 1
                  },
                  "evidence": {
                    "type": "object",
                    "properties": {
                      "task_description": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        },
                        "minItems": 1
                      },
                      "guidelines": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        },
                        "minItems": 1
                      }
                    },
                    "required": ["task_description", "guidelines"]
                  },
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "recommendation": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": ["conflict", "impact", "evidence", "severity", "recommendation"]
              }
            },
            "stakeholder_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict": {
                    "type": "string",
                    "minLength": 1
                  },
                  "impact": {
                    "type": "string",
                    "minLength": 1
                  },
                  "evidence": {
                    "type": "object",
                    "properties": {
                      "task_description": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        },
                        "minItems": 1
                      },
                      "guidelines": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        },
                        "minItems": 1
                      }
                    },
                    "required": ["task_description", "guidelines"]
                  },
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "recommendation": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": ["conflict", "impact", "evidence", "severity", "recommendation"]
              }
            },
            "context_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict": {
                    "type": "string",
                    "minLength": 1
                  },
                  "impact": {
                    "type": "string",
                    "minLength": 1
                  },
                  "evidence": {
                    "type": "object",
                    "properties": {
                      "task_description": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        },
                        "minItems": 1
                      },
                      "guidelines": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        },
                        "minItems": 1
                      }
                    },
                    "required": ["task_description", "guidelines"]
                  },
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "recommendation": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": ["conflict", "impact", "evidence", "severity", "recommendation"]
              }
            },
            "criteria_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict": {
                    "type": "string",
                    "minLength": 1
                  },
                  "impact": {
                    "type": "string",
                    "minLength": 1
                  },
                  "evidence": {
                    "type": "object",
                    "properties": {
                      "task_description": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        },
                        "minItems": 1
                      },
                      "guidelines": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        },
                        "minItems": 1
                      }
                    },
                    "required": ["task_description", "guidelines"]
                  },
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "recommendation": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": ["conflict", "impact", "evidence", "severity", "recommendation"]
              }
            }
          },
          "required": ["scope_conflicts", "stakeholder_conflicts", "context_conflicts", "criteria_conflicts"]
        },
        "guidelines_vs_task": {
          "type": "object",
          "properties": {
            "scope_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict": {
                    "type": "string",
                    "minLength": 1
                  },
                  "impact": {
                    "type": "string",
                    "minLength": 1
                  },
                  "evidence": {
                    "type": "object",
                    "properties": {
                      "guidelines": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        },
                        "minItems": 1
                      },
                      "task_description": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        },
                        "minItems": 1
                      }
                    },
                    "required": ["guidelines", "task_description"]
                  },
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "recommendation": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": ["conflict", "impact", "evidence", "severity", "recommendation"]
              }
            },
            "stakeholder_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict": {
                    "type": "string",
                    "minLength": 1
                  },
                  "impact": {
                    "type": "string",
                    "minLength": 1
                  },
                  "evidence": {
                    "type": "object",
                    "properties": {
                      "guidelines": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        },
                        "minItems": 1
                      },
                      "task_description": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        },
                        "minItems": 1
                      }
                    },
                    "required": ["guidelines", "task_description"]
                  },
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "recommendation": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": ["conflict", "impact", "evidence", "severity", "recommendation"]
              }
            },
            "context_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict": {
                    "type": "string",
                    "minLength": 1
                  },
                  "impact": {
                    "type": "string",
                    "minLength": 1
                  },
                  "evidence": {
                    "type": "object",
                    "properties": {
                      "guidelines": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        },
                        "minItems": 1
                      },
                      "task_description": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        },
                        "minItems": 1
                      }
                    },
                    "required": ["guidelines", "task_description"]
                  },
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "recommendation": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": ["conflict", "impact", "evidence", "severity", "recommendation"]
              }
            },
            "criteria_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict": {
                    "type": "string",
                    "minLength": 1
                  },
                  "impact": {
                    "type": "string",
                    "minLength": 1
                  },
                  "evidence": {
                    "type": "object",
                    "properties": {
                      "guidelines": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        },
                        "minItems": 1
                      },
                      "task_description": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        },
                        "minItems": 1
                      }
                    },
                    "required": ["guidelines", "task_description"]
                  },
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "recommendation": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": ["conflict", "impact", "evidence", "severity", "recommendation"]
              }
            }
          },
          "required": ["scope_conflicts", "stakeholder_conflicts", "context_conflicts", "criteria_conflicts"]
        },
        "synthesis": {
          "type": "object",
          "properties": {
            "key_patterns": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "minItems": 1
            },
            "bidirectional_issues": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "minItems": 1
            },
            "prioritized_resolutions": {
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
                "required": ["area", "recommendation", "justification"]
              },
              "minItems": 1
            }
          },
          "required": ["key_patterns", "bidirectional_issues", "prioritized_resolutions"]
        }
      },
      "required": ["task_vs_guidelines", "guidelines_vs_task", "synthesis"]
    }
  },
  "required": ["dual_perspective_conflicts"]
}

# Initial Description Conflict Analysis Reflection
initial_description_conflict_analysis_reflection_prompt = """
# Shade Agent Technical Reflection with Critical Analysis

You are the reflection agent responsible for conducting rigorous technical analysis of the Shade Agent's description conflict analysis while maintaining a skeptical, critical perspective on fundamental conflict detection assumptions and dual-perspective analysis validity.

**CRITICAL JSON REQUIREMENT: You must return ONLY valid JSON. Do not include any explanatory text, markdown code blocks, explanations, reasoning, commentary, or any other content outside the JSON structure. Your entire response must be parseable as JSON. Any non-JSON content will cause system failure.**

Conduct technical validation with critical questioning:

## Technical Analysis with Skeptical Assessment

1. **Conflict Detection Technical Review**:
   - Is the dual-perspective conflict analysis technically sound or artificially complex contradiction decomposition?
   - Do identified conflicts reflect genuine incompatibilities or conventional disagreement patterns?
   - Are conflict boundaries validated contradictions or defensive analysis stacking?

2. **Analysis Completeness Technical Validation with Critical Gaps Analysis**:
   - Are missing description conflicts genuine oversights or acceptable analysis scope?
   - Do identified conflict patterns reflect real incompatibilities or assumed tension measures?
   - Are severity assessments appropriately calibrated or systematically over-engineered?

3. **Perspective Consistency Technical Assessment with Assumption Challenge**:
   - Do dual perspectives serve genuine conflict detection coherence or impose unnecessary analytical complexity?
   - Are contradiction classifications real incompatibilities or artificial conservative restrictions?
   - Do conflict assumption validations reflect evidence-based reasoning or conventional analysis wisdom?
- Does dual-perspective analysis reveal genuine conflicts or create artificial polarization between compatible elements?
- Do "critical conflicts" represent real development impediments or theoretical inconsistencies?
- Would experienced development teams consider these conflicts blocking issues or manageable trade-offs?

## Core Responsibilities
1. **Conflict Reality Interrogation**: Challenge whether identified conflicts are genuine contradictions versus different priorities
2. **Evidence Correlation Skepticism**: Question if evidence demonstrates actual conflicts or coincidental differences
3. **Implementation Impact Challenge**: Assess if proposed conflicts would actually block development or require simple prioritization
4. **Dual-Perspective Value Assessment**: Evaluate if perspective separation reveals insights or creates unnecessary analytical complexity
5. **Resolution Practicality Review**: Challenge whether recommended resolutions address real problems or theoretical perfectionism
6. **Synthesis Significance Testing**: Question whether bidirectional analysis provides actionable insights or analytical overhead

## Output Format

**CRITICAL: You MUST respond with PURE JSON ONLY. No explanatory text, no markdown formatting, no additional commentary. Your entire response must be valid JSON that exactly matches the schema below.**

**Any deviation from pure JSON format will be rejected. Double-check your JSON syntax before responding.**

Provide your reflection in the following JSON format:

```json
{"reflection_results": {"perspective_quality": {"task_vs_guidelines": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "severity_assessment": {"rating": "high|medium|low", "justification": "string", "adjustment_needs": ["strings"]}}, "guidelines_vs_task": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "severity_assessment": {"rating": "high|medium|low", "justification": "string", "adjustment_needs": ["strings"]}}}, "conflict_specific_feedback": {"task_vs_guidelines": {"scope_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string"}], "stakeholder_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string"}], "context_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string"}], "criteria_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string"}]}, "guidelines_vs_task": {"scope_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string"}], "stakeholder_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string"}], "context_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string"}], "criteria_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string"}]}}, "missed_conflicts": {"task_vs_guidelines": {"scope_conflicts": [{"conflict": "string", "evidence": {"task_description": ["strings"], "guidelines": ["strings"]}, "impact": "string", "severity": "high|medium|low", "recommendation": "string"}], "stakeholder_conflicts": [{"conflict": "string", "evidence": {"task_description": ["strings"], "guidelines": ["strings"]}, "impact": "string", "severity": "high|medium|low", "recommendation": "string"}], "context_conflicts": [{"conflict": "string", "evidence": {"task_description": ["strings"], "guidelines": ["strings"]}, "impact": "string", "severity": "high|medium|low", "recommendation": "string"}], "criteria_conflicts": [{"conflict": "string", "evidence": {"task_description": ["strings"], "guidelines": ["strings"]}, "impact": "string", "severity": "high|medium|low", "recommendation": "string"}]}, "guidelines_vs_task": {"scope_conflicts": [{"conflict": "string", "evidence": {"guidelines": ["strings"], "task_description": ["strings"]}, "impact": "string", "severity": "high|medium|low", "recommendation": "string"}], "stakeholder_conflicts": [{"conflict": "string", "evidence": {"guidelines": ["strings"], "task_description": ["strings"]}, "impact": "string", "severity": "high|medium|low", "recommendation": "string"}], "context_conflicts": [{"conflict": "string", "evidence": {"guidelines": ["strings"], "task_description": ["strings"]}, "impact": "string", "severity": "high|medium|low", "recommendation": "string"}], "criteria_conflicts": [{"conflict": "string", "evidence": {"guidelines": ["strings"], "task_description": ["strings"]}, "impact": "string", "severity": "high|medium|low", "recommendation": "string"}]}}, "synthesis_feedback": {"quality": {"rating": "high|medium|low", "justification": "string"}, "missed_patterns": ["strings"], "missed_bidirectional_issues": ["strings"], "resolution_improvements": [{"area": "string", "current": "string", "improved": "string", "reason": "string"}]}}}
```

## Field Descriptions

### Perspective Quality
- **task_vs_guidelines**: Quality assessment of how well conflicts from task description to guidelines were identified
- **guidelines_vs_task**: Quality assessment of how well conflicts from guidelines to task description were identified

For each perspective:
- **comprehensiveness**: Overall assessment of conflict identification coverage
- **evidence_quality**: Evaluation of the supporting evidence provided
- **severity_assessment**: Assessment of how accurately severity levels were assigned

### Conflict-Specific Feedback
Detailed feedback on specific conflicts identified in the original analysis, organized by perspective:
- **conflict_index**: The index (0-based) of the conflict in the original analysis
- **feedback_type**: The type of feedback being provided
- **details**: Specific details about the feedback
- **correction**: Suggested correction or improvement

### Missed Conflicts
Conflicts that were not identified in the original analysis, organized by perspective:
- **conflict**: Description of the missed conflict
- **evidence**: Supporting evidence from both sources
- **impact**: Potential development impact
- **severity**: Appropriate severity level
- **recommendation**: Suggested resolution approach

### Synthesis Feedback
Assessment of how well the dual perspectives were synthesized:
- **quality**: Overall rating of the synthesis quality
- **missed_patterns**: Important patterns across conflicts that were overlooked
- **missed_bidirectional_issues**: Bidirectional issues that were not identified
- **resolution_improvements**: Specific ways to enhance resolution recommendations

## Skeptical Review Guidelines

1. **Conflict Authenticity Test**: Do these conflicts represent genuine contradictions or different priorities that can coexist?
2. **Dual-Perspective Value Challenge**: Does separating perspectives reveal meaningful conflicts or create artificial polarization?
3. **Implementation Reality Check**: Are proposed conflicts practical blocking issues or theoretical inconsistencies?
4. **Evidence Contradiction Skepticism**: Does evidence demonstrate actual conflicts or coincidental differences in emphasis?
5. **Resolution Necessity Assessment**: Do recommended resolutions address genuine problems or perfectionist theoretical alignment?
6. **Synthesis Complexity Interrogation**: Does bidirectional analysis justify its analytical overhead with actionable insights?

## Skeptical Verification Checklist

1. **Conflict Reality Verification**: Do identified conflicts represent genuine contradictions that would block development success?
2. **Perspective Separation Challenge**: Are dual perspectives meaningful analytical insights or artificial complexity creation?
3. **Evidence Quality Interrogation**: Does supporting evidence demonstrate real conflicts or theoretical inconsistencies?
4. **Implementation Impact Test**: Would experienced development teams consider these conflicts actual blocking issues?
5. **Resolution Practicality Analysis**: Do recommended resolutions solve real problems or create theoretical perfectionism?
6. **Synthesis Value Assessment**: Does bidirectional analysis provide actionable insights or analytical overhead?
7. **Conflict Significance Challenge**: Are prioritized conflicts genuine development impediments or manageable trade-offs?
8. **Evidence Correlation Skepticism**: Do conflict patterns represent meaningful insights or coincidental differences?
9. **Development Team Alignment**: Would practical engineers agree these conflicts require immediate resolution?
10. **Analytical Complexity Justification**: Does the dual-perspective approach justify its complexity with development value?
"""

initial_description_conflict_analysis_reflection_schema = {
  "type": "object",
  "properties": {
    "reflection_results": {
      "type": "object",
      "properties": {
        "perspective_quality": {
          "type": "object",
          "properties": {
            "task_vs_guidelines": {
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
                "severity_assessment": {
                  "type": "object",
                  "properties": {
                    "rating": {
                      "type": "string",
                      "enum": ["high", "medium", "low"]
                    },
                    "justification": {
                      "type": "string"
                    },
                    "adjustment_needs": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    }
                  },
                  "required": ["rating", "justification", "adjustment_needs"]
                }
              },
              "required": ["comprehensiveness", "evidence_quality", "severity_assessment"]
            },
            "guidelines_vs_task": {
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
                "severity_assessment": {
                  "type": "object",
                  "properties": {
                    "rating": {
                      "type": "string",
                      "enum": ["high", "medium", "low"]
                    },
                    "justification": {
                      "type": "string"
                    },
                    "adjustment_needs": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    }
                  },
                  "required": ["rating", "justification", "adjustment_needs"]
                }
              },
              "required": ["comprehensiveness", "evidence_quality", "severity_assessment"]
            }
          },
          "required": ["task_vs_guidelines", "guidelines_vs_task"]
        },
        "conflict_specific_feedback": {
          "type": "object",
          "properties": {
            "task_vs_guidelines": {
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
                        "enum": ["false_positive", "missing_evidence", "incorrect_severity", "weak_recommendation"]
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
                "stakeholder_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "conflict_index": {
                        "type": "integer"
                      },
                      "feedback_type": {
                        "type": "string",
                        "enum": ["false_positive", "missing_evidence", "incorrect_severity", "weak_recommendation"]
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
                "context_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "conflict_index": {
                        "type": "integer"
                      },
                      "feedback_type": {
                        "type": "string",
                        "enum": ["false_positive", "missing_evidence", "incorrect_severity", "weak_recommendation"]
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
                "criteria_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "conflict_index": {
                        "type": "integer"
                      },
                      "feedback_type": {
                        "type": "string",
                        "enum": ["false_positive", "missing_evidence", "incorrect_severity", "weak_recommendation"]
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
              "required": ["scope_conflicts", "stakeholder_conflicts", "context_conflicts", "criteria_conflicts"]
            },
            "guidelines_vs_task": {
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
                        "enum": ["false_positive", "missing_evidence", "incorrect_severity", "weak_recommendation"]
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
                "stakeholder_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "conflict_index": {
                        "type": "integer"
                      },
                      "feedback_type": {
                        "type": "string",
                        "enum": ["false_positive", "missing_evidence", "incorrect_severity", "weak_recommendation"]
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
                "context_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "conflict_index": {
                        "type": "integer"
                      },
                      "feedback_type": {
                        "type": "string",
                        "enum": ["false_positive", "missing_evidence", "incorrect_severity", "weak_recommendation"]
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
                "criteria_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "conflict_index": {
                        "type": "integer"
                      },
                      "feedback_type": {
                        "type": "string",
                        "enum": ["false_positive", "missing_evidence", "incorrect_severity", "weak_recommendation"]
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
              "required": ["scope_conflicts", "stakeholder_conflicts", "context_conflicts", "criteria_conflicts"]
            }
          },
          "required": ["task_vs_guidelines", "guidelines_vs_task"]
        },
        "missed_conflicts": {
          "type": "object",
          "properties": {
            "task_vs_guidelines": {
              "type": "object",
              "properties": {
                "scope_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "conflict": {
                        "type": "string"
                      },
                      "evidence": {
                        "type": "object",
                        "properties": {
                          "task_description": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          },
                          "guidelines": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          }
                        },
                        "required": ["task_description", "guidelines"]
                      },
                      "impact": {
                        "type": "string"
                      },
                      "severity": {
                        "type": "string",
                        "enum": ["high", "medium", "low"]
                      },
                      "recommendation": {
                        "type": "string"
                      }
                    },
                    "required": ["conflict", "evidence", "impact", "severity", "recommendation"]
                  }
                },
                "stakeholder_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "conflict": {
                        "type": "string"
                      },
                      "evidence": {
                        "type": "object",
                        "properties": {
                          "task_description": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          },
                          "guidelines": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          }
                        },
                        "required": ["task_description", "guidelines"]
                      },
                      "impact": {
                        "type": "string"
                      },
                      "severity": {
                        "type": "string",
                        "enum": ["high", "medium", "low"]
                      },
                      "recommendation": {
                        "type": "string"
                      }
                    },
                    "required": ["conflict", "evidence", "impact", "severity", "recommendation"]
                  }
                },
                "context_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "conflict": {
                        "type": "string"
                      },
                      "evidence": {
                        "type": "object",
                        "properties": {
                          "task_description": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          },
                          "guidelines": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          }
                        },
                        "required": ["task_description", "guidelines"]
                      },
                      "impact": {
                        "type": "string"
                      },
                      "severity": {
                        "type": "string",
                        "enum": ["high", "medium", "low"]
                      },
                      "recommendation": {
                        "type": "string"
                      }
                    },
                    "required": ["conflict", "evidence", "impact", "severity", "recommendation"]
                  }
                },
                "criteria_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "conflict": {
                        "type": "string"
                      },
                      "evidence": {
                        "type": "object",
                        "properties": {
                          "task_description": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          },
                          "guidelines": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          }
                        },
                        "required": ["task_description", "guidelines"]
                      },
                      "impact": {
                        "type": "string"
                      },
                      "severity": {
                        "type": "string",
                        "enum": ["high", "medium", "low"]
                      },
                      "recommendation": {
                        "type": "string"
                      }
                    },
                    "required": ["conflict", "evidence", "impact", "severity", "recommendation"]
                  }
                }
              },
              "required": ["scope_conflicts", "stakeholder_conflicts", "context_conflicts", "criteria_conflicts"]
            },
            "guidelines_vs_task": {
              "type": "object",
              "properties": {
                "scope_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "conflict": {
                        "type": "string"
                      },
                      "evidence": {
                        "type": "object",
                        "properties": {
                          "guidelines": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          },
                          "task_description": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          }
                        },
                        "required": ["guidelines", "task_description"]
                      },
                      "impact": {
                        "type": "string"
                      },
                      "severity": {
                        "type": "string",
                        "enum": ["high", "medium", "low"]
                      },
                      "recommendation": {
                        "type": "string"
                      }
                    },
                    "required": ["conflict", "evidence", "impact", "severity", "recommendation"]
                  }
                },
                "stakeholder_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "conflict": {
                        "type": "string"
                      },
                      "evidence": {
                        "type": "object",
                        "properties": {
                          "guidelines": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          },
                          "task_description": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          }
                        },
                        "required": ["guidelines", "task_description"]
                      },
                      "impact": {
                        "type": "string"
                      },
                      "severity": {
                        "type": "string",
                        "enum": ["high", "medium", "low"]
                      },
                      "recommendation": {
                        "type": "string"
                      }
                    },
                    "required": ["conflict", "evidence", "impact", "severity", "recommendation"]
                  }
                },
                "context_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "conflict": {
                        "type": "string"
                      },
                      "evidence": {
                        "type": "object",
                        "properties": {
                          "guidelines": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          },
                          "task_description": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          }
                        },
                        "required": ["guidelines", "task_description"]
                      },
                      "impact": {
                        "type": "string"
                      },
                      "severity": {
                        "type": "string",
                        "enum": ["high", "medium", "low"]
                      },
                      "recommendation": {
                        "type": "string"
                      }
                    },
                    "required": ["conflict", "evidence", "impact", "severity", "recommendation"]
                  }
                },
                "criteria_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "conflict": {
                        "type": "string"
                      },
                      "evidence": {
                        "type": "object",
                        "properties": {
                          "guidelines": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          },
                          "task_description": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          }
                        },
                        "required": ["guidelines", "task_description"]
                      },
                      "impact": {
                        "type": "string"
                      },
                      "severity": {
                        "type": "string",
                        "enum": ["high", "medium", "low"]
                      },
                      "recommendation": {
                        "type": "string"
                      }
                    },
                    "required": ["conflict", "evidence", "impact", "severity", "recommendation"]
                  }
                }
              },
              "required": ["scope_conflicts", "stakeholder_conflicts", "context_conflicts", "criteria_conflicts"]
            }
          },
          "required": ["task_vs_guidelines", "guidelines_vs_task"]
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
            "missed_patterns": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "missed_bidirectional_issues": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "resolution_improvements": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "area": {
                    "type": "string"
                  },
                  "current": {
                    "type": "string"
                  },
                  "improved": {
                    "type": "string"
                  },
                  "reason": {
                    "type": "string"
                  }
                },
                "required": ["area", "current", "improved", "reason"]
              }
            }
          },
          "required": ["quality", "missed_patterns", "missed_bidirectional_issues", "resolution_improvements"]
        }
      },
      "required": ["perspective_quality", "conflict_specific_feedback", "missed_conflicts", "synthesis_feedback"]
    }
  },
  "required": ["reflection_results"]
}

# Initial Description Conflict Analysis Revision
initial_description_conflict_analysis_revision_prompt = """
# Shade Agent Revision Prompt

You are the Shade Agent processing reflection results to implement self-corrections to your dual-perspective conflict analysis. Your role is to systematically address identified issues from the reflection phase, refining your analysis of conflicts between the task description and other guidelines from both perspectives.

## Core Responsibilities
1. Process reflection feedback on your dual-perspective conflict analysis
2. Refine conflict identification in both perspectives
3. Remove incorrectly identified conflicts (false positives)
4. Add overlooked conflicts that were missed
5. Strengthen evidence for legitimate conflicts
6. Adjust severity ratings to be more accurate
7. Improve recommendations to be more practical and comprehensive
8. Enhance the synthesis across both perspectives

## Input Format

You will receive two inputs:
1. Your original dual-perspective conflict analysis output
2. Reflection results in the following structure:
```json
{"reflection_results": {"perspective_quality": {"task_vs_guidelines": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "severity_assessment": {"rating": "high|medium|low", "justification": "string", "adjustment_needs": ["strings"]}}, "guidelines_vs_task": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "severity_assessment": {"rating": "high|medium|low", "justification": "string", "adjustment_needs": ["strings"]}}}, "conflict_specific_feedback": {"task_vs_guidelines": {"scope_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string"}], "stakeholder_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string"}], "context_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string"}], "criteria_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string"}]}, "guidelines_vs_task": {"scope_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string"}], "stakeholder_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string"}], "context_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string"}], "criteria_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string"}]}}, "missed_conflicts": {"task_vs_guidelines": {"scope_conflicts": [{"conflict": "string", "evidence": {"task_description": ["strings"], "guidelines": ["strings"]}, "impact": "string", "severity": "high|medium|low", "recommendation": "string"}], "stakeholder_conflicts": [{"conflict": "string", "evidence": {"task_description": ["strings"], "guidelines": ["strings"]}, "impact": "string", "severity": "high|medium|low", "recommendation": "string"}], "context_conflicts": [{"conflict": "string", "evidence": {"task_description": ["strings"], "guidelines": ["strings"]}, "impact": "string", "severity": "high|medium|low", "recommendation": "string"}], "criteria_conflicts": [{"conflict": "string", "evidence": {"task_description": ["strings"], "guidelines": ["strings"]}, "impact": "string", "severity": "high|medium|low", "recommendation": "string"}]}, "guidelines_vs_task": {"scope_conflicts": [{"conflict": "string", "evidence": {"guidelines": ["strings"], "task_description": ["strings"]}, "impact": "string", "severity": "high|medium|low", "recommendation": "string"}], "stakeholder_conflicts": [{"conflict": "string", "evidence": {"guidelines": ["strings"], "task_description": ["strings"]}, "impact": "string", "severity": "high|medium|low", "recommendation": "string"}], "context_conflicts": [{"conflict": "string", "evidence": {"guidelines": ["strings"], "task_description": ["strings"]}, "impact": "string", "severity": "high|medium|low", "recommendation": "string"}], "criteria_conflicts": [{"conflict": "string", "evidence": {"guidelines": ["strings"], "task_description": ["strings"]}, "impact": "string", "severity": "high|medium|low", "recommendation": "string"}]}}, "synthesis_feedback": {"quality": {"rating": "high|medium|low", "justification": "string"}, "missed_patterns": ["strings"], "missed_bidirectional_issues": ["strings"], "resolution_improvements": [{"area": "string", "current": "string", "improved": "string", "reason": "string"}]}}}
```

## Revision Process

1. Analyze reflection feedback methodically
2. Remove identified false positives from both perspectives
3. Add overlooked conflicts to both perspectives with proper evidence
4. Strengthen evidence for existing conflicts
5. Adjust severity ratings to be more accurate
6. Improve recommendations where needed
7. Enhance synthesis to better integrate both perspectives
8. Verify bidirectional issue identification
9. Validate all conflicts against project guidelines

## Output Format

**CRITICAL: You MUST respond with PURE JSON ONLY. No explanatory text, no markdown formatting, no additional commentary. Your entire response must be valid JSON that exactly matches the schema below.**

**Any deviation from pure JSON format will be rejected. Double-check your JSON syntax before responding.**

Provide your revised analysis in the following JSON format:

```json
{"revision_metadata": {"processed_feedback": {"perspective_improvements": {"task_vs_guidelines": {"comprehensiveness": ["strings"], "evidence_quality": ["strings"], "severity_assessment": ["strings"]}, "guidelines_vs_task": {"comprehensiveness": ["strings"], "evidence_quality": ["strings"], "severity_assessment": ["strings"]}}, "conflict_adjustments": {"false_positives_removed": {"task_vs_guidelines": integer, "guidelines_vs_task": integer}, "conflicts_added": {"task_vs_guidelines": integer, "guidelines_vs_task": integer}, "evidence_strengthened": {"task_vs_guidelines": integer, "guidelines_vs_task": integer}, "severity_adjusted": {"task_vs_guidelines": integer, "guidelines_vs_task": integer}, "recommendations_improved": {"task_vs_guidelines": integer, "guidelines_vs_task": integer}}, "synthesis_improvements": ["strings"]}, "validation_steps": ["strings"]}, "dual_perspective_conflicts": {"task_vs_guidelines": {"scope_conflicts": [{"conflict": "string", "impact": "string", "evidence": {"task_description": ["strings"], "guidelines": ["strings"]}, "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}], "stakeholder_conflicts": [{"conflict": "string", "impact": "string", "evidence": {"task_description": ["strings"], "guidelines": ["strings"]}, "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}], "context_conflicts": [{"conflict": "string", "impact": "string", "evidence": {"task_description": ["strings"], "guidelines": ["strings"]}, "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}], "criteria_conflicts": [{"conflict": "string", "impact": "string", "evidence": {"task_description": ["strings"], "guidelines": ["strings"]}, "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}]}, "guidelines_vs_task": {"scope_conflicts": [{"conflict": "string", "impact": "string", "evidence": {"guidelines": ["strings"], "task_description": ["strings"]}, "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}], "stakeholder_conflicts": [{"conflict": "string", "impact": "string", "evidence": {"guidelines": ["strings"], "task_description": ["strings"]}, "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}], "context_conflicts": [{"conflict": "string", "impact": "string", "evidence": {"guidelines": ["strings"], "task_description": ["strings"]}, "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}], "criteria_conflicts": [{"conflict": "string", "impact": "string", "evidence": {"guidelines": ["strings"], "task_description": ["strings"]}, "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}]}, "synthesis": {"key_patterns": ["strings"], "bidirectional_issues": ["strings"], "prioritized_resolutions": [{"area": "string", "recommendation": "string", "justification": "string", "revision_note": "string"}]}}}
```

## Revision Guidelines

### Perspective Improvements
- Enhance the completeness of conflict identification in both perspectives
- Ensure proper directionality of conflicts in each perspective
- Strengthen evidence with specific references from both sources
- Adjust severity ratings based on true impact on development

### Conflict Adjustments
- Remove conflicts identified as false positives
- Add conflicts identified as missing
- Enhance evidence quality for existing conflicts
- Adjust severity ratings to match actual impact
- Improve recommendations to be more practical and specific

### Synthesis Improvements
- Identify new patterns across both perspectives
- Enhance bidirectional issue identification
- Improve prioritized resolutions to address the most critical conflicts
- Ensure holistic integration of both perspectives

## Validation Checklist

Before finalizing your revised analysis:
1. Confirm all false positives have been removed from both perspectives
2. Verify all missing conflicts have been added to appropriate perspectives
3. Ensure all evidence quality issues have been addressed
4. Validate that severity ratings accurately reflect potential impact
5. Check that all recommendation improvements have been implemented
6. Confirm that synthesis improvements have been incorporated
7. Ensure appropriate balance of conflicts across both perspectives
8. Verify that bidirectional issues are properly identified and addressed

## Self-Correction Principles

1. Focus on genuine conflicts that would impact project success
2. Maintain clear directional separation between perspectives
3. Ensure conflicts are supported by specific evidence from both sources
4. Assign severity ratings consistently based on development impact
5. Provide practical, actionable recommendations that respect both sources
6. Highlight bidirectional issues requiring mutual accommodation
7. Ensure synthesis effectively integrates insights from both perspectives
"""

initial_description_conflict_analysis_revision_schema = {
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
                "task_vs_guidelines": {
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
                    "severity_assessment": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    }
                  },
                  "required": ["comprehensiveness", "evidence_quality", "severity_assessment"]
                },
                "guidelines_vs_task": {
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
                    "severity_assessment": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    }
                  },
                  "required": ["comprehensiveness", "evidence_quality", "severity_assessment"]
                }
              },
              "required": ["task_vs_guidelines", "guidelines_vs_task"]
            },
            "conflict_adjustments": {
              "type": "object",
              "properties": {
                "false_positives_removed": {
                  "type": "object",
                  "properties": {
                    "task_vs_guidelines": {
                      "type": "integer"
                    },
                    "guidelines_vs_task": {
                      "type": "integer"
                    }
                  },
                  "required": ["task_vs_guidelines", "guidelines_vs_task"]
                },
                "conflicts_added": {
                  "type": "object",
                  "properties": {
                    "task_vs_guidelines": {
                      "type": "integer"
                    },
                    "guidelines_vs_task": {
                      "type": "integer"
                    }
                  },
                  "required": ["task_vs_guidelines", "guidelines_vs_task"]
                },
                "evidence_strengthened": {
                  "type": "object",
                  "properties": {
                    "task_vs_guidelines": {
                      "type": "integer"
                    },
                    "guidelines_vs_task": {
                      "type": "integer"
                    }
                  },
                  "required": ["task_vs_guidelines", "guidelines_vs_task"]
                },
                "severity_adjusted": {
                  "type": "object",
                  "properties": {
                    "task_vs_guidelines": {
                      "type": "integer"
                    },
                    "guidelines_vs_task": {
                      "type": "integer"
                    }
                  },
                  "required": ["task_vs_guidelines", "guidelines_vs_task"]
                },
                "recommendations_improved": {
                  "type": "object",
                  "properties": {
                    "task_vs_guidelines": {
                      "type": "integer"
                    },
                    "guidelines_vs_task": {
                      "type": "integer"
                    }
                  },
                  "required": ["task_vs_guidelines", "guidelines_vs_task"]
                }
              },
              "required": [
                "false_positives_removed",
                "conflicts_added",
                "evidence_strengthened",
                "severity_adjusted",
                "recommendations_improved"
              ]
            },
            "synthesis_improvements": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "required": ["perspective_improvements", "conflict_adjustments", "synthesis_improvements"]
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
    "dual_perspective_conflicts": {
      "type": "object",
      "properties": {
        "task_vs_guidelines": {
          "type": "object",
          "properties": {
            "scope_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict": {
                    "type": "string"
                  },
                  "impact": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "object",
                    "properties": {
                      "task_description": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "guidelines": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      }
                    },
                    "required": ["task_description", "guidelines"]
                  },
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "recommendation": {
                    "type": "string"
                  },
                  "revision_note": {
                    "type": "string"
                  }
                },
                "required": ["conflict", "impact", "evidence", "severity", "recommendation", "revision_note"]
              }
            },
            "stakeholder_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict": {
                    "type": "string"
                  },
                  "impact": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "object",
                    "properties": {
                      "task_description": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "guidelines": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      }
                    },
                    "required": ["task_description", "guidelines"]
                  },
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "recommendation": {
                    "type": "string"
                  },
                  "revision_note": {
                    "type": "string"
                  }
                },
                "required": ["conflict", "impact", "evidence", "severity", "recommendation", "revision_note"]
              }
            },
            "context_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict": {
                    "type": "string"
                  },
                  "impact": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "object",
                    "properties": {
                      "task_description": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "guidelines": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      }
                    },
                    "required": ["task_description", "guidelines"]
                  },
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "recommendation": {
                    "type": "string"
                  },
                  "revision_note": {
                    "type": "string"
                  }
                },
                "required": ["conflict", "impact", "evidence", "severity", "recommendation", "revision_note"]
              }
            },
            "criteria_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict": {
                    "type": "string"
                  },
                  "impact": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "object",
                    "properties": {
                      "task_description": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "guidelines": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      }
                    },
                    "required": ["task_description", "guidelines"]
                  },
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "recommendation": {
                    "type": "string"
                  },
                  "revision_note": {
                    "type": "string"
                  }
                },
                "required": ["conflict", "impact", "evidence", "severity", "recommendation", "revision_note"]
              }
            }
          },
          "required": ["scope_conflicts", "stakeholder_conflicts", "context_conflicts", "criteria_conflicts"]
        },
        "guidelines_vs_task": {
          "type": "object",
          "properties": {
            "scope_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict": {
                    "type": "string"
                  },
                  "impact": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "object",
                    "properties": {
                      "guidelines": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "task_description": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      }
                    },
                    "required": ["guidelines", "task_description"]
                  },
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "recommendation": {
                    "type": "string"
                  },
                  "revision_note": {
                    "type": "string"
                  }
                },
                "required": ["conflict", "impact", "evidence", "severity", "recommendation", "revision_note"]
              }
            },
            "stakeholder_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict": {
                    "type": "string"
                  },
                  "impact": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "object",
                    "properties": {
                      "guidelines": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "task_description": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      }
                    },
                    "required": ["guidelines", "task_description"]
                  },
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "recommendation": {
                    "type": "string"
                  },
                  "revision_note": {
                    "type": "string"
                  }
                },
                "required": ["conflict", "impact", "evidence", "severity", "recommendation", "revision_note"]
              }
            },
            "context_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict": {
                    "type": "string"
                  },
                  "impact": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "object",
                    "properties": {
                      "guidelines": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "task_description": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      }
                    },
                    "required": ["guidelines", "task_description"]
                  },
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "recommendation": {
                    "type": "string"
                  },
                  "revision_note": {
                    "type": "string"
                  }
                },
                "required": ["conflict", "impact", "evidence", "severity", "recommendation", "revision_note"]
              }
            },
            "criteria_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict": {
                    "type": "string"
                  },
                  "impact": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "object",
                    "properties": {
                      "guidelines": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "task_description": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      }
                    },
                    "required": ["guidelines", "task_description"]
                  },
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "recommendation": {
                    "type": "string"
                  },
                  "revision_note": {
                    "type": "string"
                  }
                },
                "required": ["conflict", "impact", "evidence", "severity", "recommendation", "revision_note"]
              }
            }
          },
          "required": ["scope_conflicts", "stakeholder_conflicts", "context_conflicts", "criteria_conflicts"]
        },
        "synthesis": {
          "type": "object",
          "properties": {
            "key_patterns": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "bidirectional_issues": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "prioritized_resolutions": {
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
          "required": ["key_patterns", "bidirectional_issues", "prioritized_resolutions"]
        }
      },
      "required": ["task_vs_guidelines", "guidelines_vs_task", "synthesis"]
    }
  },
  "required": ["revision_metadata", "dual_perspective_conflicts"]
}