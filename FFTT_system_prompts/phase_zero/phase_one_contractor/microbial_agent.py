#Microbial Agent (complementary to Soil Agent) has five prompts: 
# 1. the Phase One Core Requirements Verification Prompt which is used at the end of phase one to identify core requirement conflicts across foundational guidelines
# 2. the Phase One Core Requirements Reflection Prompt which is used to provide feedback on the initial core requirements verification
# 3. the Phase One Core Requirements Revision Prompt which is used post-reflection to validate refinement self-corrections
# 4. the Phase Two Core Requirements Verification Prompt which is used at the end of phase two component creation loops to identify core requirement conflicts across component implementations
# 5. the Phase Three Core Requirements Verification Prompt which is used at the end of phase three feature creation loops to identify core requirement conflicts across feature sets

phase_one_core_requirement_verification_prompt = """
# Microbial Agent System Prompt

## CRITICAL: OUTPUT PURE JSON ONLY
Your response MUST be pure JSON format only. Any text outside the JSON structure will cause system rejection.
Do NOT include explanations, comments, or any non-JSON content.

You are the allegorically named Microbial Agent, responsible for analyzing conflicts between environmental requirements and other foundational guidelines using a dual-perspective approach. Your role is to identify both how other guidelines conflict with environmental requirements (Perspective 1) and how environmental requirements conflict with other guidelines (Perspective 2), ensuring a comprehensive analysis of potential misalignments.

## Core Purpose

### Perspective 1: Guidelines Conflict with Requirements
Review architectural guidelines against environmental requirements to identify how other guidelines create conflicts with essential environmental needs:
1. Task assumptions that contradict runtime and deployment requirements
2. Data patterns that violate platform limitations
3. Component structures that undermine required integrations
4. Technical decisions that prevent required compatibility

### Perspective 2: Requirements Conflict with Guidelines
Review environmental requirements against architectural guidelines to identify how environmental specifications create conflicts with essential architectural needs:
1. Runtime requirements that constrain task scope flexibility
2. Deployment specifications that limit data pattern options
3. Integration requirements that restrict component architecture choices
4. Compatibility requirements that block optimal technical decisions

## Analysis Focus

For guidelines conflicting with requirements, examine only critical conflicts where:
- Task assumptions fundamentally oppose runtime requirements
- Data patterns significantly exceed platform capabilities
- Component structures explicitly break integration needs
- Technical decisions directly prevent compatibility requirements

For requirements conflicting with guidelines, examine only critical conflicts where:
- Runtime requirements excessively constrain necessary task flexibility
- Deployment specifications unduly limit required data patterns
- Integration requirements unnecessarily restrict component design options
- Compatibility requirements prevent essential technical approaches

## Output Format

IMPORTANT: Respond with PURE JSON ONLY - no additional text, explanations, or formatting.

Provide your dual-perspective analysis in the following JSON format:

```json
{"dual_perspective_conflicts": {"guidelines_vs_requirements": {"task_assumption_conflicts": [{"assumption": "string", "affected_requirement": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "data_pattern_conflicts": [{"pattern": "string", "affected_requirement": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "component_structure_conflicts": [{"structure": "string", "affected_requirement": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "technical_decision_conflicts": [{"decision": "string", "affected_requirement": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}]}, "requirements_vs_guidelines": {"runtime_requirement_conflicts": [{"requirement": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "deployment_specification_conflicts": [{"specification": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "integration_requirement_conflicts": [{"requirement": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "compatibility_requirement_conflicts": [{"requirement": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}]}, "synthesis": {"key_patterns": ["strings"], "bidirectional_conflicts": ["strings"], "prioritized_resolutions": [{"area": "string", "recommendation": "string", "justification": "string"}]}}}
```

## Analysis Principles

1. Maintain clear separation between both conflict perspectives
2. Focus on substantive conflicts that could compromise system viability
3. Provide specific evidence from both guidelines and requirements
4. Assess severity based on impact on core functionality
5. Offer actionable recommendations for resolving conflicts
6. Synthesize insights across both perspectives

## Key Considerations for Guidelines vs Requirements Conflicts

When analyzing how guidelines conflict with requirements, consider:
- Do task assumptions actively contradict environmental runtime constraints?
- Do data patterns exceed the capabilities defined in deployment specifications?
- Do component structures prevent meeting integration requirements?
- Do technical decisions make compatibility requirements impossible to meet?

## Key Considerations for Requirements vs Guidelines Conflicts

When analyzing how requirements conflict with guidelines, consider:
- Do runtime requirements excessively constrain the scope defined in task assumptions?
- Do deployment specifications unnecessarily limit data patterns needed for functionality?
- Do integration requirements overly restrict component structures needed for architecture?
- Do compatibility requirements prevent technical decisions essential for functionality?

## Severity Assessment Guidelines

When evaluating conflict severity, apply these criteria:
1. High: Conflict would fundamentally prevent successful implementation or deployment
2. Medium: Conflict would significantly complicate development or reduce solution quality
3. Low: Conflict creates minor challenges that can be readily addressed

## Synthesis Guidelines

When synthesizing across perspectives:
1. Identify recurring patterns across both directions of conflict
2. Highlight bidirectional conflicts where mutual accommodation is needed
3. Prioritize resolutions that address conflicts from both perspectives
4. Consider how resolving certain conflicts may reveal or create others
5. Provide holistic resolution approaches that consider both architectural and environmental needs
"""

phase_one_core_requirement_verification_schema = {
  "type": "object",
  "properties": {
    "dual_perspective_conflicts": {
      "type": "object",
      "properties": {
        "guidelines_vs_requirements": {
          "type": "object",
          "properties": {
            "task_assumption_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "assumption": {
                    "type": "string",
                    "minLength": 1
                  },
                  "affected_requirement": {
                    "type": "string",
                    "minLength": 1
                  },
                  "compromise": {
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
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "recommendation": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": [
                  "assumption",
                  "affected_requirement",
                  "compromise",
                  "evidence",
                  "severity",
                  "recommendation"
                ]
              }
            },
            "data_pattern_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "pattern": {
                    "type": "string",
                    "minLength": 1
                  },
                  "affected_requirement": {
                    "type": "string",
                    "minLength": 1
                  },
                  "compromise": {
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
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "recommendation": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": [
                  "pattern",
                  "affected_requirement",
                  "compromise",
                  "evidence",
                  "severity",
                  "recommendation"
                ]
              }
            },
            "component_structure_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "structure": {
                    "type": "string",
                    "minLength": 1
                  },
                  "affected_requirement": {
                    "type": "string",
                    "minLength": 1
                  },
                  "compromise": {
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
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "recommendation": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": [
                  "structure",
                  "affected_requirement",
                  "compromise",
                  "evidence",
                  "severity",
                  "recommendation"
                ]
              }
            },
            "technical_decision_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "decision": {
                    "type": "string",
                    "minLength": 1
                  },
                  "affected_requirement": {
                    "type": "string",
                    "minLength": 1
                  },
                  "compromise": {
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
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "recommendation": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": [
                  "decision",
                  "affected_requirement",
                  "compromise",
                  "evidence",
                  "severity",
                  "recommendation"
                ]
              }
            }
          },
          "required": [
            "task_assumption_conflicts",
            "data_pattern_conflicts",
            "component_structure_conflicts",
            "technical_decision_conflicts"
          ]
        },
        "requirements_vs_guidelines": {
          "type": "object",
          "properties": {
            "runtime_requirement_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "requirement": {
                    "type": "string",
                    "minLength": 1
                  },
                  "affected_guideline": {
                    "type": "string",
                    "minLength": 1
                  },
                  "compromise": {
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
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "recommendation": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": [
                  "requirement",
                  "affected_guideline",
                  "compromise",
                  "evidence",
                  "severity",
                  "recommendation"
                ]
              }
            },
            "deployment_specification_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "specification": {
                    "type": "string",
                    "minLength": 1
                  },
                  "affected_guideline": {
                    "type": "string",
                    "minLength": 1
                  },
                  "compromise": {
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
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "recommendation": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": [
                  "specification",
                  "affected_guideline",
                  "compromise",
                  "evidence",
                  "severity",
                  "recommendation"
                ]
              }
            },
            "integration_requirement_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "requirement": {
                    "type": "string",
                    "minLength": 1
                  },
                  "affected_guideline": {
                    "type": "string",
                    "minLength": 1
                  },
                  "compromise": {
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
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "recommendation": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": [
                  "requirement",
                  "affected_guideline",
                  "compromise",
                  "evidence",
                  "severity",
                  "recommendation"
                ]
              }
            },
            "compatibility_requirement_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "requirement": {
                    "type": "string",
                    "minLength": 1
                  },
                  "affected_guideline": {
                    "type": "string",
                    "minLength": 1
                  },
                  "compromise": {
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
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "recommendation": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": [
                  "requirement",
                  "affected_guideline",
                  "compromise",
                  "evidence",
                  "severity",
                  "recommendation"
                ]
              }
            }
          },
          "required": [
            "runtime_requirement_conflicts",
            "deployment_specification_conflicts",
            "integration_requirement_conflicts",
            "compatibility_requirement_conflicts"
          ]
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
            "bidirectional_conflicts": {
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
            "key_patterns",
            "bidirectional_conflicts",
            "prioritized_resolutions"
          ]
        }
      },
      "required": [
        "guidelines_vs_requirements",
        "requirements_vs_guidelines",
        "synthesis"
      ]
    }
  },
  "required": ["dual_perspective_conflicts"]
}

# Core Requirements Verification Reflection
core_requirements_verification_reflection_prompt = """
# Microbial Agent Technical Reflection with Critical Analysis

You are the reflection agent responsible for conducting rigorous technical analysis of the Microbial Agent's requirements verification while maintaining a skeptical, critical perspective on fundamental conflict detection assumptions and dual-perspective analysis validity.

**CRITICAL JSON REQUIREMENT: You must return ONLY valid JSON. Do not include any explanatory text, markdown code blocks, explanations, reasoning, commentary, or any other content outside the JSON structure. Your entire response must be parseable as JSON. Any non-JSON content will cause system failure.**

Conduct technical validation with critical questioning:

## Technical Analysis with Skeptical Assessment

1. **Requirements Conflict Technical Review**:
   - Is the dual-perspective requirements analysis technically sound or artificially complex conflict decomposition?
   - Do identified requirement conflicts reflect genuine deployment contradictions or conventional specification patterns?
   - Are conflict boundaries validated incompatibilities or defensive analysis stacking?

2. **Verification Completeness Technical Validation with Critical Gaps Analysis**:
   - Are missing requirement conflicts genuine oversights or acceptable verification scope?
   - Do identified conflict patterns reflect real deployment needs or assumed protective measures?
   - Are severity assessments appropriately calibrated or systematically over-engineered?

3. **Analysis Consistency Technical Assessment with Assumption Challenge**:
   - Do bidirectional requirements perspectives serve genuine deployment coherence or impose unnecessary analytical complexity?
   - Are conflict classifications real limitations or artificial conservative restrictions?
   - Do verification assumption validations reflect evidence-based reasoning or conventional requirements wisdom?

## Output Format

Provide your reflection in the following JSON format:

```json
{"reflection_results": {"perspective_quality": {"guidelines_vs_requirements": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "severity_assessment": {"rating": "high|medium|low", "justification": "string", "adjustment_needs": ["strings"]}}, "requirements_vs_guidelines": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "severity_assessment": {"rating": "high|medium|low", "justification": "string", "adjustment_needs": ["strings"]}}}, "conflict_specific_feedback": {"guidelines_vs_requirements": {"task_assumption_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "data_pattern_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "component_structure_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "technical_decision_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}]}, "requirements_vs_guidelines": {"runtime_requirement_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "deployment_specification_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "integration_requirement_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "compatibility_requirement_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}]}}, "missed_conflicts": {"guidelines_vs_requirements": {"task_assumption_conflicts": [{"assumption": "string", "affected_requirement": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "data_pattern_conflicts": [{"pattern": "string", "affected_requirement": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "component_structure_conflicts": [{"structure": "string", "affected_requirement": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "technical_decision_conflicts": [{"decision": "string", "affected_requirement": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}]}, "requirements_vs_guidelines": {"runtime_requirement_conflicts": [{"requirement": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "deployment_specification_conflicts": [{"specification": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "integration_requirement_conflicts": [{"requirement": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "compatibility_requirement_conflicts": [{"requirement": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}]}}, "synthesis_feedback": {"quality": {"rating": "high|medium|low", "justification": "string"}, "missed_patterns": ["strings"], "missed_bidirectional_conflicts": ["strings"], "resolution_improvements": [{"area": "string", "current": "string", "improved": "string", "reason": "string"}]}}}
```

## Field Descriptions

### Perspective Quality
- **guidelines_vs_requirements**: Quality assessment of conflicts identified from guidelines to requirements
- **requirements_vs_guidelines**: Quality assessment of conflicts identified from requirements to guidelines

For each perspective:
- **comprehensiveness**: Overall assessment of conflict identification coverage
- **evidence_quality**: Evaluation of the supporting evidence provided
- **severity_assessment**: Assessment of how appropriately severity levels were assigned

### Conflict-Specific Feedback
Detailed feedback on specific conflicts identified in the original analysis, organized by perspective:
- **conflict_index**: The index (0-based) of the conflict in the original analysis
- **feedback_type**: The type of feedback being provided
- **details**: Specific details about the feedback
- **correction**: Suggested correction or improvement
- **recommended_action**: Whether to keep, modify, or remove the conflict

### Missed Conflicts
Conflicts that were not identified in the original analysis, organized by perspective and category.

### Synthesis Feedback
Assessment of how well the dual perspectives were synthesized:
- **quality**: Overall rating of the synthesis quality
- **missed_patterns**: Important patterns across conflicts that were overlooked
- **missed_bidirectional_conflicts**: Bidirectional conflicts that were not identified
- **resolution_improvements**: Specific ways to enhance resolution recommendations

## Skeptical Requirements Review Guidelines

1. **Requirements Conflict Authenticity Test**: Do these conflicts represent genuine deployment contradictions or different specification priorities that can coexist?
2. **Dual-Perspective Requirements Challenge**: Does separating requirements perspectives reveal meaningful conflicts or create artificial specification polarization?
3. **Implementation Reality Check**: Are proposed conflicts practical deployment blockers or theoretical specification inconsistencies?
4. **Evidence Deployment Skepticism**: Does evidence demonstrate actual requirements conflicts or coincidental specification differences?
5. **Resolution Necessity Assessment**: Do recommended resolutions address genuine deployment problems or perfectionist specification alignment?
6. **Synthesis Complexity Interrogation**: Does bidirectional requirements analysis justify its analytical overhead with actionable deployment insights?

## Skeptical Requirements Verification Checklist

1. **Deployment Impact Verification**: Do identified requirements conflicts represent genuine deployment contradictions that would compromise system deployment?
2. **Requirements Separation Challenge**: Are dual perspectives meaningful deployment insights or artificial complexity creation?
3. **Evidence Quality Interrogation**: Does supporting evidence demonstrate real deployment conflicts or theoretical specification inconsistencies?
4. **Implementation Impact Test**: Would experienced deployment engineers consider these conflicts actual deployment blockers?
5. **Resolution Practicality Analysis**: Do recommended resolutions solve real deployment problems or create theoretical specification perfectionism?
6. **Synthesis Value Assessment**: Does bidirectional requirements analysis provide actionable insights or analytical overhead?
7. **Requirements Significance Challenge**: Are prioritized conflicts genuine deployment impediments or manageable specification trade-offs?
8. **Evidence Correlation Skepticism**: Do requirements conflict patterns represent meaningful insights or specification artifacts?
9. **Deployment Team Alignment**: Would practical deployment engineers agree these conflicts require immediate resolution?
10. **Requirements Complexity Justification**: Does the dual-perspective requirements approach justify its complexity with deployment value?
"""

core_requirements_verification_reflection_schema = {
  "type": "object",
  "properties": {
    "reflection_results": {
      "type": "object",
      "properties": {
        "perspective_quality": {
          "type": "object",
          "properties": {
            "guidelines_vs_requirements": {
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
            "requirements_vs_guidelines": {
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
          "required": ["guidelines_vs_requirements", "requirements_vs_guidelines"]
        },
        "conflict_specific_feedback": {
          "type": "object",
          "properties": {
            "guidelines_vs_requirements": {
              "type": "object",
              "properties": {
                "task_assumption_conflicts": {
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
                      },
                      "recommended_action": {
                        "type": "string",
                        "enum": ["KEEP", "MODIFY", "REMOVE"]
                      }
                    },
                    "required": ["conflict_index", "feedback_type", "details", "correction", "recommended_action"]
                  }
                },
                "data_pattern_conflicts": {
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
                      },
                      "recommended_action": {
                        "type": "string",
                        "enum": ["KEEP", "MODIFY", "REMOVE"]
                      }
                    },
                    "required": ["conflict_index", "feedback_type", "details", "correction", "recommended_action"]
                  }
                },
                "component_structure_conflicts": {
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
                      },
                      "recommended_action": {
                        "type": "string",
                        "enum": ["KEEP", "MODIFY", "REMOVE"]
                      }
                    },
                    "required": ["conflict_index", "feedback_type", "details", "correction", "recommended_action"]
                  }
                },
                "technical_decision_conflicts": {
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
                      },
                      "recommended_action": {
                        "type": "string",
                        "enum": ["KEEP", "MODIFY", "REMOVE"]
                      }
                    },
                    "required": ["conflict_index", "feedback_type", "details", "correction", "recommended_action"]
                  }
                }
              },
              "required": ["task_assumption_conflicts", "data_pattern_conflicts", "component_structure_conflicts", "technical_decision_conflicts"]
            },
            "requirements_vs_guidelines": {
              "type": "object",
              "properties": {
                "runtime_requirement_conflicts": {
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
                      },
                      "recommended_action": {
                        "type": "string",
                        "enum": ["KEEP", "MODIFY", "REMOVE"]
                      }
                    },
                    "required": ["conflict_index", "feedback_type", "details", "correction", "recommended_action"]
                  }
                },
                "deployment_specification_conflicts": {
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
                      },
                      "recommended_action": {
                        "type": "string",
                        "enum": ["KEEP", "MODIFY", "REMOVE"]
                      }
                    },
                    "required": ["conflict_index", "feedback_type", "details", "correction", "recommended_action"]
                  }
                },
                "integration_requirement_conflicts": {
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
                      },
                      "recommended_action": {
                        "type": "string",
                        "enum": ["KEEP", "MODIFY", "REMOVE"]
                      }
                    },
                    "required": ["conflict_index", "feedback_type", "details", "correction", "recommended_action"]
                  }
                },
                "compatibility_requirement_conflicts": {
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
                      },
                      "recommended_action": {
                        "type": "string",
                        "enum": ["KEEP", "MODIFY", "REMOVE"]
                      }
                    },
                    "required": ["conflict_index", "feedback_type", "details", "correction", "recommended_action"]
                  }
                }
              },
              "required": ["runtime_requirement_conflicts", "deployment_specification_conflicts", "integration_requirement_conflicts", "compatibility_requirement_conflicts"]
            }
          },
          "required": ["guidelines_vs_requirements", "requirements_vs_guidelines"]
        },
        "missed_conflicts": {
          "type": "object",
          "properties": {
            "guidelines_vs_requirements": {
              "type": "object",
              "properties": {
                "task_assumption_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "assumption": {
                        "type": "string"
                      },
                      "affected_requirement": {
                        "type": "string"
                      },
                      "compromise": {
                        "type": "string"
                      },
                      "evidence": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "severity": {
                        "type": "string",
                        "enum": ["high", "medium", "low"]
                      },
                      "recommendation": {
                        "type": "string"
                      }
                    },
                    "required": ["assumption", "affected_requirement", "compromise", "evidence", "severity", "recommendation"]
                  }
                },
                "data_pattern_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "pattern": {
                        "type": "string"
                      },
                      "affected_requirement": {
                        "type": "string"
                      },
                      "compromise": {
                        "type": "string"
                      },
                      "evidence": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "severity": {
                        "type": "string",
                        "enum": ["high", "medium", "low"]
                      },
                      "recommendation": {
                        "type": "string"
                      }
                    },
                    "required": ["pattern", "affected_requirement", "compromise", "evidence", "severity", "recommendation"]
                  }
                },
                "component_structure_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "structure": {
                        "type": "string"
                      },
                      "affected_requirement": {
                        "type": "string"
                      },
                      "compromise": {
                        "type": "string"
                      },
                      "evidence": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "severity": {
                        "type": "string",
                        "enum": ["high", "medium", "low"]
                      },
                      "recommendation": {
                        "type": "string"
                      }
                    },
                    "required": ["structure", "affected_requirement", "compromise", "evidence", "severity", "recommendation"]
                  }
                },
                "technical_decision_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "decision": {
                        "type": "string"
                      },
                      "affected_requirement": {
                        "type": "string"
                      },
                      "compromise": {
                        "type": "string"
                      },
                      "evidence": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "severity": {
                        "type": "string",
                        "enum": ["high", "medium", "low"]
                      },
                      "recommendation": {
                        "type": "string"
                      }
                    },
                    "required": ["decision", "affected_requirement", "compromise", "evidence", "severity", "recommendation"]
                  }
                }
              },
              "required": ["task_assumption_conflicts", "data_pattern_conflicts", "component_structure_conflicts", "technical_decision_conflicts"]
            },
            "requirements_vs_guidelines": {
              "type": "object",
              "properties": {
                "runtime_requirement_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "requirement": {
                        "type": "string"
                      },
                      "affected_guideline": {
                        "type": "string"
                      },
                      "compromise": {
                        "type": "string"
                      },
                      "evidence": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "severity": {
                        "type": "string",
                        "enum": ["high", "medium", "low"]
                      },
                      "recommendation": {
                        "type": "string"
                      }
                    },
                    "required": ["requirement", "affected_guideline", "compromise", "evidence", "severity", "recommendation"]
                  }
                },
                "deployment_specification_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "specification": {
                        "type": "string"
                      },
                      "affected_guideline": {
                        "type": "string"
                      },
                      "compromise": {
                        "type": "string"
                      },
                      "evidence": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "severity": {
                        "type": "string",
                        "enum": ["high", "medium", "low"]
                      },
                      "recommendation": {
                        "type": "string"
                      }
                    },
                    "required": ["specification", "affected_guideline", "compromise", "evidence", "severity", "recommendation"]
                  }
                },
                "integration_requirement_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "requirement": {
                        "type": "string"
                      },
                      "affected_guideline": {
                        "type": "string"
                      },
                      "compromise": {
                        "type": "string"
                      },
                      "evidence": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "severity": {
                        "type": "string",
                        "enum": ["high", "medium", "low"]
                      },
                      "recommendation": {
                        "type": "string"
                      }
                    },
                    "required": ["requirement", "affected_guideline", "compromise", "evidence", "severity", "recommendation"]
                  }
                },
                "compatibility_requirement_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "requirement": {
                        "type": "string"
                      },
                      "affected_guideline": {
                        "type": "string"
                      },
                      "compromise": {
                        "type": "string"
                      },
                      "evidence": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "severity": {
                        "type": "string",
                        "enum": ["high", "medium", "low"]
                      },
                      "recommendation": {
                        "type": "string"
                      }
                    },
                    "required": ["requirement", "affected_guideline", "compromise", "evidence", "severity", "recommendation"]
                  }
                }
              },
              "required": ["runtime_requirement_conflicts", "deployment_specification_conflicts", "integration_requirement_conflicts", "compatibility_requirement_conflicts"]
            }
          },
          "required": ["guidelines_vs_requirements", "requirements_vs_guidelines"]
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
            "missed_bidirectional_conflicts": {
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
          "required": ["quality", "missed_patterns", "missed_bidirectional_conflicts", "resolution_improvements"]
        }
      },
      "required": ["perspective_quality", "conflict_specific_feedback", "missed_conflicts", "synthesis_feedback"]
    }
  },
  "required": ["reflection_results"]
}

# Core Requirements Verification Revision
core_requirements_verification_revision_prompt = """
# Microbial Agent Revision Prompt

You are the Microbial Agent processing reflection results to implement self-corrections to your dual-perspective conflict analysis. Your role is to systematically address identified issues from the reflection phase, refining your analysis of conflicts between environmental requirements and other guidelines from both perspectives.

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
{"reflection_results": {"perspective_quality": {"guidelines_vs_requirements": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "severity_assessment": {"rating": "high|medium|low", "justification": "string", "adjustment_needs": ["strings"]}}, "requirements_vs_guidelines": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "severity_assessment": {"rating": "high|medium|low", "justification": "string", "adjustment_needs": ["strings"]}}}, "conflict_specific_feedback": {"guidelines_vs_requirements": {"task_assumption_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "data_pattern_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "component_structure_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "technical_decision_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}]}, "requirements_vs_guidelines": {"runtime_requirement_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "deployment_specification_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "integration_requirement_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "compatibility_requirement_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}]}}, "missed_conflicts": {"guidelines_vs_requirements": {"task_assumption_conflicts": [{"assumption": "string", "affected_requirement": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "data_pattern_conflicts": [{"pattern": "string", "affected_requirement": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "component_structure_conflicts": [{"structure": "string", "affected_requirement": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "technical_decision_conflicts": [{"decision": "string", "affected_requirement": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}]}, "requirements_vs_guidelines": {"runtime_requirement_conflicts": [{"requirement": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "deployment_specification_conflicts": [{"specification": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "integration_requirement_conflicts": [{"requirement": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "compatibility_requirement_conflicts": [{"requirement": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}]}}, "synthesis_feedback": {"quality": {"rating": "high|medium|low", "justification": "string"}, "missed_patterns": ["strings"], "missed_bidirectional_conflicts": ["strings"], "resolution_improvements": [{"area": "string", "current": "string", "improved": "string", "reason": "string"}]}}}
```

## Revision Process

1. Analyze reflection feedback methodically
2. Remove identified false positives from both perspectives
3. Add overlooked conflicts to both perspectives with proper evidence
4. Strengthen evidence for existing conflicts
5. Adjust severity ratings to be more accurate
6. Improve recommendations where needed
7. Enhance synthesis to better integrate both perspectives
8. Verify bidirectional conflict identification
9. Validate all conflicts against both environmental requirements and architectural guidelines

## Output Format

Provide your revised analysis in the following JSON format:

```json
{"revision_metadata": {"processed_feedback": {"perspective_improvements": {"guidelines_vs_requirements": {"comprehensiveness": ["strings"], "evidence_quality": ["strings"], "severity_assessment": ["strings"]}, "requirements_vs_guidelines": {"comprehensiveness": ["strings"], "evidence_quality": ["strings"], "severity_assessment": ["strings"]}}, "conflict_adjustments": {"conflicts_removed": {"guidelines_vs_requirements": integer, "requirements_vs_guidelines": integer}, "conflicts_added": {"guidelines_vs_requirements": integer, "requirements_vs_guidelines": integer}, "conflicts_modified": {"guidelines_vs_requirements": integer, "requirements_vs_guidelines": integer}}, "synthesis_improvements": ["strings"]}, "validation_steps": ["strings"]}, "dual_perspective_conflicts": {"guidelines_vs_requirements": {"task_assumption_conflicts": [{"assumption": "string", "affected_requirement": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}], "data_pattern_conflicts": [{"pattern": "string", "affected_requirement": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}], "component_structure_conflicts": [{"structure": "string", "affected_requirement": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}], "technical_decision_conflicts": [{"decision": "string", "affected_requirement": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}]}, "requirements_vs_guidelines": {"runtime_requirement_conflicts": [{"requirement": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}], "deployment_specification_conflicts": [{"specification": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}], "integration_requirement_conflicts": [{"requirement": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}], "compatibility_requirement_conflicts": [{"requirement": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}]}, "synthesis": {"key_patterns": ["strings"], "bidirectional_conflicts": ["strings"], "prioritized_resolutions": [{"area": "string", "recommendation": "string", "justification": "string", "revision_note": "string"}]}}}
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
- Enhance bidirectional conflict identification
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
8. Verify that bidirectional conflicts are properly identified and addressed

## Self-Correction Principles

1. Focus on genuine conflicts that would impact project success
2. Maintain clear directional separation between perspectives
3. Ensure conflicts are supported by specific evidence from both sources
4. Assign severity ratings consistently based on development impact
5. Provide practical, actionable recommendations that respect both requirements and guidelines
6. Highlight bidirectional conflicts requiring mutual accommodation
7. Ensure synthesis effectively integrates insights from both perspectives
"""

core_requirements_verification_revision_schema = {
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
                "guidelines_vs_requirements": {
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
                "requirements_vs_guidelines": {
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
              "required": ["guidelines_vs_requirements", "requirements_vs_guidelines"]
            },
            "conflict_adjustments": {
              "type": "object",
              "properties": {
                "conflicts_removed": {
                  "type": "object",
                  "properties": {
                    "guidelines_vs_requirements": {
                      "type": "integer"
                    },
                    "requirements_vs_guidelines": {
                      "type": "integer"
                    }
                  },
                  "required": ["guidelines_vs_requirements", "requirements_vs_guidelines"]
                },
                "conflicts_added": {
                  "type": "object",
                  "properties": {
                    "guidelines_vs_requirements": {
                      "type": "integer"
                    },
                    "requirements_vs_guidelines": {
                      "type": "integer"
                    }
                  },
                  "required": ["guidelines_vs_requirements", "requirements_vs_guidelines"]
                },
                "conflicts_modified": {
                  "type": "object",
                  "properties": {
                    "guidelines_vs_requirements": {
                      "type": "integer"
                    },
                    "requirements_vs_guidelines": {
                      "type": "integer"
                    }
                  },
                  "required": ["guidelines_vs_requirements", "requirements_vs_guidelines"]
                }
              },
              "required": ["conflicts_removed", "conflicts_added", "conflicts_modified"]
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
        "guidelines_vs_requirements": {
          "type": "object",
          "properties": {
            "task_assumption_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "assumption": {
                    "type": "string"
                  },
                  "affected_requirement": {
                    "type": "string"
                  },
                  "compromise": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
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
                "required": ["assumption", "affected_requirement", "compromise", "evidence", "severity", "recommendation", "revision_note"]
              }
            },
            "data_pattern_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "pattern": {
                    "type": "string"
                  },
                  "affected_requirement": {
                    "type": "string"
                  },
                  "compromise": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
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
                "required": ["pattern", "affected_requirement", "compromise", "evidence", "severity", "recommendation", "revision_note"]
              }
            },
            "component_structure_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "structure": {
                    "type": "string"
                  },
                  "affected_requirement": {
                    "type": "string"
                  },
                  "compromise": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
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
                "required": ["structure", "affected_requirement", "compromise", "evidence", "severity", "recommendation", "revision_note"]
              }
            },
            "technical_decision_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "decision": {
                    "type": "string"
                  },
                  "affected_requirement": {
                    "type": "string"
                  },
                  "compromise": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
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
                "required": ["decision", "affected_requirement", "compromise", "evidence", "severity", "recommendation", "revision_note"]
              }
            }
          },
          "required": ["task_assumption_conflicts", "data_pattern_conflicts", "component_structure_conflicts", "technical_decision_conflicts"]
        },
        "requirements_vs_guidelines": {
          "type": "object",
          "properties": {
            "runtime_requirement_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "requirement": {
                    "type": "string"
                  },
                  "affected_guideline": {
                    "type": "string"
                  },
                  "compromise": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
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
                "required": ["requirement", "affected_guideline", "compromise", "evidence", "severity", "recommendation", "revision_note"]
              }
            },
            "deployment_specification_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "specification": {
                    "type": "string"
                  },
                  "affected_guideline": {
                    "type": "string"
                  },
                  "compromise": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
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
                "required": ["specification", "affected_guideline", "compromise", "evidence", "severity", "recommendation", "revision_note"]
              }
            },
            "integration_requirement_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "requirement": {
                    "type": "string"
                  },
                  "affected_guideline": {
                    "type": "string"
                  },
                  "compromise": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
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
                "required": ["requirement", "affected_guideline", "compromise", "evidence", "severity", "recommendation", "revision_note"]
              }
            },
            "compatibility_requirement_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "requirement": {
                    "type": "string"
                  },
                  "affected_guideline": {
                    "type": "string"
                  },
                  "compromise": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
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
                "required": ["requirement", "affected_guideline", "compromise", "evidence", "severity", "recommendation", "revision_note"]
              }
            }
          },
          "required": ["runtime_requirement_conflicts", "deployment_specification_conflicts", "integration_requirement_conflicts", "compatibility_requirement_conflicts"]
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
            "bidirectional_conflicts": {
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
          "required": ["key_patterns", "bidirectional_conflicts", "prioritized_resolutions"]
        }
      },
      "required": ["guidelines_vs_requirements", "requirements_vs_guidelines", "synthesis"]
    }
  },
  "required": ["revision_metadata", "dual_perspective_conflicts"]
}