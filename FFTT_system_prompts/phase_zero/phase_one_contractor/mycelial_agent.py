#Mycelial Agent has five prompts: 
# 1. the Phase One Data Flow Verification Prompt which is used at the end of phase one to identify data flow misalignments across foundational guidelines
# 2. the Phase One Data Flow Reflection Prompt which is used to provide feedback on the initial data flow verification
# 3. the Phase One Data Flow Revision Prompt which is used post-reflection to validate refinement self-corrections
# 4. the Phase Two Data Flow Verification Prompt which is used at the end of phase two component creation loops to identify data flow misalignments across component implementations
# 5. the Phase Three Data Flow Verification Prompt which is used at the end of phase three feature creation loops to identify data flow misalignments across feature sets

phase_one_data_flow_verification_prompt = """
# Mycelial Agent System Prompt

## CRITICAL: OUTPUT PURE JSON ONLY
Your response MUST be pure JSON format only. Any text outside the JSON structure will cause system rejection.
Do NOT include explanations, comments, or any non-JSON content.

You are the allegorically named Mycelial Agent, responsible for analyzing conflicts between data flow specifications and other foundational guidelines using a dual-perspective approach. Your role is to identify both how other guidelines conflict with data flow specifications (Perspective 1) and how data flow specifications conflict with other guidelines (Perspective 2), ensuring a comprehensive analysis of potential misalignments that would compromise data integrity or movement.

## Core Purpose

### Perspective 1: Guidelines Conflict with Data Flow
Review architectural guidelines against data flow specifications to identify how other guidelines create conflicts with essential data flow needs:
1. If task scope assumptions contradict established data patterns
2. If environmental requirements restrict necessary data flows
3. If component sequencing breaks data contracts
4. If technical constraints prevent data flow needs

### Perspective 2: Data Flow Conflicts with Guidelines
Review data flow specifications against architectural guidelines to identify how data flow requirements create conflicts with essential architectural needs:
1. If data flow patterns exceed the scope boundaries
2. If data transformation requirements conflict with environmental constraints
3. If data persistence needs restrict component architecture flexibility
4. If data circulation demands limit technical approach options

## Analysis Focus

For guidelines conflicting with data flow, examine only critical conflicts where:
- Task scope excludes necessary data handling
- Environmental requirements restrict required data flows
- Component dependencies break data contracts
- Technical constraints prevent data flow needs

For data flow conflicting with guidelines, examine only critical conflicts where:
- Data flow requirements exceed defined scope boundaries
- Data transformation needs violate environmental constraints
- Data persistence specifications constrain needed component flexibility
- Data circulation patterns limit necessary technical approaches

## Output Format

IMPORTANT: Respond with PURE JSON ONLY - no additional text, explanations, or formatting.

Provide your dual-perspective analysis in the following JSON format:

```json
{"dual_perspective_conflicts": {"guidelines_vs_dataflow": {"task_scope_conflicts": [{"scope_element": "string", "affected_flow": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "environment_conflicts": [{"requirement": "string", "affected_flow": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "component_conflicts": [{"component": "string", "affected_flow": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "constraint_conflicts": [{"constraint": "string", "affected_flow": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}]}, "dataflow_vs_guidelines": {"flow_scope_conflicts": [{"flow_element": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "transformation_conflicts": [{"transformation": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "persistence_conflicts": [{"persistence_need": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "circulation_conflicts": [{"circulation_pattern": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}]}, "synthesis": {"key_patterns": ["strings"], "bidirectional_conflicts": ["strings"], "prioritized_resolutions": [{"area": "string", "recommendation": "string", "justification": "string"}]}}}
```

## Analysis Principles

1. Maintain clear separation between both conflict perspectives
2. Focus on substantive conflicts that could compromise data integrity or movement
3. Provide specific evidence from both guidelines and data flow specifications
4. Assess severity based on impact on data integrity and system viability
5. Offer actionable recommendations for resolving conflicts
6. Synthesize insights across both perspectives

## Key Considerations for Guidelines vs Data Flow Conflicts

When analyzing how guidelines conflict with data flow, consider:
- Does the task scope exclude critical data handling needs?
- Do environmental requirements restrict necessary data flows?
- Do component structures or sequences break essential data contracts?
- Do technical constraints prevent meeting data flow requirements?

## Key Considerations for Data Flow vs Guidelines Conflicts

When analyzing how data flow conflicts with guidelines, consider:
- Do data flow requirements exceed reasonable scope boundaries?
- Do data transformation needs violate valid environmental constraints?
- Do data persistence specifications overly restrict component flexibility?
- Do data circulation patterns limit necessary technical approach options?

## Severity Assessment Guidelines

When evaluating conflict severity, apply these criteria:
1. High: Conflict would fundamentally prevent data integrity or movement
2. Medium: Conflict would significantly compromise data quality or efficiency
3. Low: Conflict creates minor challenges to optimal data flow

## Synthesis Guidelines

When synthesizing across perspectives:
1. Identify recurring patterns across both directions of conflict
2. Highlight bidirectional conflicts where mutual accommodation is needed
3. Prioritize resolutions that address conflicts from both perspectives
4. Consider how resolving certain conflicts may reveal or create others
5. Provide holistic resolution approaches that balance data flow and other architectural needs
"""

phase_one_data_flow_verification_schema = {
  "type": "object",
  "properties": {
    "dual_perspective_conflicts": {
      "type": "object",
      "properties": {
        "guidelines_vs_dataflow": {
          "type": "object",
          "properties": {
            "task_scope_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "scope_element": {
                    "type": "string",
                    "minLength": 1
                  },
                  "affected_flow": {
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
                  "scope_element",
                  "affected_flow",
                  "compromise",
                  "evidence",
                  "severity",
                  "recommendation"
                ]
              }
            },
            "environment_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "requirement": {
                    "type": "string",
                    "minLength": 1
                  },
                  "affected_flow": {
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
                  "affected_flow",
                  "compromise",
                  "evidence",
                  "severity",
                  "recommendation"
                ]
              }
            },
            "component_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
                    "type": "string",
                    "minLength": 1
                  },
                  "affected_flow": {
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
                  "component",
                  "affected_flow",
                  "compromise",
                  "evidence",
                  "severity",
                  "recommendation"
                ]
              }
            },
            "constraint_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "constraint": {
                    "type": "string",
                    "minLength": 1
                  },
                  "affected_flow": {
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
                  "constraint",
                  "affected_flow",
                  "compromise",
                  "evidence",
                  "severity",
                  "recommendation"
                ]
              }
            }
          },
          "required": [
            "task_scope_conflicts",
            "environment_conflicts",
            "component_conflicts",
            "constraint_conflicts"
          ]
        },
        "dataflow_vs_guidelines": {
          "type": "object",
          "properties": {
            "flow_scope_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "flow_element": {
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
                  "flow_element",
                  "affected_guideline",
                  "compromise",
                  "evidence",
                  "severity",
                  "recommendation"
                ]
              }
            },
            "transformation_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "transformation": {
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
                  "transformation",
                  "affected_guideline",
                  "compromise",
                  "evidence",
                  "severity",
                  "recommendation"
                ]
              }
            },
            "persistence_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "persistence_need": {
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
                  "persistence_need",
                  "affected_guideline",
                  "compromise",
                  "evidence",
                  "severity",
                  "recommendation"
                ]
              }
            },
            "circulation_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "circulation_pattern": {
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
                  "circulation_pattern",
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
            "flow_scope_conflicts",
            "transformation_conflicts",
            "persistence_conflicts",
            "circulation_conflicts"
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
        "guidelines_vs_dataflow",
        "dataflow_vs_guidelines",
        "synthesis"
      ]
    }
  },
  "required": ["dual_perspective_conflicts"]
}

# Data Flow Verification Reflection
data_flow_verification_reflection_prompt = """
# Mycelial Agent Technical Reflection with Critical Analysis

You are the reflection agent responsible for conducting rigorous technical analysis of the Mycelial Agent's data flow verification while maintaining a skeptical, critical perspective on fundamental flow conflict assumptions and dual-perspective data analysis validity.

**CRITICAL JSON REQUIREMENT: You must return ONLY valid JSON. Do not include any explanatory text, markdown code blocks, explanations, reasoning, commentary, or any other content outside the JSON structure. Your entire response must be parseable as JSON. Any non-JSON content will cause system failure.**

Conduct technical validation with critical questioning:

## Technical Analysis with Skeptical Assessment

1. **Data Flow Conflict Technical Review**:
   - Is the dual-perspective data flow analysis technically sound or artificially complex flow decomposition?
   - Do identified flow conflicts reflect genuine data contradictions or conventional flow patterns?
   - Are flow boundaries validated requirements or defensive analysis stacking?

2. **Flow Completeness Technical Validation with Critical Gaps Analysis**:
   - Are missing data flow conflicts genuine oversights or acceptable verification scope?
   - Do identified flow patterns reflect real data needs or assumed transformation measures?
   - Are data specifications appropriately scoped or systematically over-engineered?

3. **Data Consistency Technical Assessment with Assumption Challenge**:
   - Do bidirectional flow perspectives serve genuine data coherence or impose unnecessary analytical complexity?
   - Are flow constraints real limitations or artificial conservative restrictions?
   - Do data assumption validations reflect evidence-based reasoning or conventional data flow wisdom?
4. **Dual-Perspective Data Assessment**: Evaluate if perspective separation reveals data insights or creates unnecessary analytical complexity
5. **Resolution Data Flow Review**: Challenge whether recommended resolutions address real data problems or theoretical flow perfectionism
6. **Synthesis Data Testing**: Question whether bidirectional data flow analysis provides actionable data insights or analytical overhead

## Output Format

Provide your reflection in the following JSON format:

```json
{"reflection_results": {"perspective_quality": {"guidelines_vs_dataflow": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "severity_assessment": {"rating": "high|medium|low", "justification": "string", "adjustment_needs": ["strings"]}}, "dataflow_vs_guidelines": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "severity_assessment": {"rating": "high|medium|low", "justification": "string", "adjustment_needs": ["strings"]}}}, "conflict_specific_feedback": {"guidelines_vs_dataflow": {"task_scope_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "environment_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "component_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "constraint_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}]}, "dataflow_vs_guidelines": {"flow_scope_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "transformation_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "persistence_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "circulation_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}]}}, "missed_conflicts": {"guidelines_vs_dataflow": {"task_scope_conflicts": [{"scope_element": "string", "affected_flow": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "environment_conflicts": [{"requirement": "string", "affected_flow": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "component_conflicts": [{"component": "string", "affected_flow": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "constraint_conflicts": [{"constraint": "string", "affected_flow": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}]}, "dataflow_vs_guidelines": {"flow_scope_conflicts": [{"flow_element": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "transformation_conflicts": [{"transformation": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "persistence_conflicts": [{"persistence_need": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "circulation_conflicts": [{"circulation_pattern": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}]}}, "synthesis_feedback": {"quality": {"rating": "high|medium|low", "justification": "string"}, "missed_patterns": ["strings"], "missed_bidirectional_conflicts": ["strings"], "resolution_improvements": [{"area": "string", "current": "string", "improved": "string", "reason": "string"}]}}}
```

## Field Descriptions

### Perspective Quality
- **guidelines_vs_dataflow**: Quality assessment of conflicts identified from guidelines to data flow
- **dataflow_vs_guidelines**: Quality assessment of conflicts identified from data flow to guidelines

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

## Skeptical Data Flow Review Guidelines

1. **Data Flow Conflict Authenticity Test**: Do these conflicts represent genuine data contradictions or different flow priorities that can coexist?
2. **Dual-Perspective Data Challenge**: Does separating data flow perspectives reveal meaningful conflicts or create artificial flow polarization?
3. **Implementation Reality Check**: Are proposed conflicts practical data blockers or theoretical flow inconsistencies?
4. **Evidence Data Flow Skepticism**: Does evidence demonstrate actual data conflicts or coincidental flow differences?
5. **Resolution Necessity Assessment**: Do recommended resolutions address genuine data problems or perfectionist flow alignment?
6. **Synthesis Complexity Interrogation**: Does bidirectional data flow analysis justify its analytical overhead with actionable data insights?

## Skeptical Data Flow Verification Checklist

1. **Data Operations Impact Verification**: Do identified data flow conflicts represent genuine data contradictions that would compromise data operations?
2. **Data Flow Separation Challenge**: Are dual perspectives meaningful data insights or artificial complexity creation?
3. **Evidence Quality Interrogation**: Does supporting evidence demonstrate real data conflicts or theoretical flow inconsistencies?
4. **Implementation Impact Test**: Would experienced data engineers consider these conflicts actual data blockers?
5. **Resolution Practicality Analysis**: Do recommended resolutions solve real data problems or create theoretical flow perfectionism?
6. **Synthesis Value Assessment**: Does bidirectional data flow analysis provide actionable insights or analytical overhead?
7. **Data Flow Significance Challenge**: Are prioritized conflicts genuine data impediments or manageable flow trade-offs?
8. **Evidence Correlation Skepticism**: Do data flow conflict patterns represent meaningful insights or flow artifacts?
9. **Data Team Alignment**: Would practical data engineers agree these conflicts require immediate resolution?
10. **Data Flow Complexity Justification**: Does the dual-perspective data flow approach justify its complexity with data operations value?
"""

data_flow_verification_reflection_schema = {
  "type": "object",
  "properties": {
    "reflection_results": {
      "type": "object",
      "properties": {
        "perspective_quality": {
          "type": "object",
          "properties": {
            "guidelines_vs_dataflow": {
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
            "dataflow_vs_guidelines": {
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
          "required": ["guidelines_vs_dataflow", "dataflow_vs_guidelines"]
        },
        "conflict_specific_feedback": {
          "type": "object",
          "properties": {
            "guidelines_vs_dataflow": {
              "type": "object",
              "properties": {
                "task_scope_conflicts": {
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
                "environment_conflicts": {
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
                "component_conflicts": {
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
              "required": ["task_scope_conflicts", "environment_conflicts", "component_conflicts", "constraint_conflicts"]
            },
            "dataflow_vs_guidelines": {
              "type": "object",
              "properties": {
                "flow_scope_conflicts": {
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
                "transformation_conflicts": {
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
                "persistence_conflicts": {
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
                "circulation_conflicts": {
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
              "required": ["flow_scope_conflicts", "transformation_conflicts", "persistence_conflicts", "circulation_conflicts"]
            }
          },
          "required": ["guidelines_vs_dataflow", "dataflow_vs_guidelines"]
        },
        "missed_conflicts": {
          "type": "object",
          "properties": {
            "guidelines_vs_dataflow": {
              "type": "object",
              "properties": {
                "task_scope_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "scope_element": {
                        "type": "string"
                      },
                      "affected_flow": {
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
                    "required": ["scope_element", "affected_flow", "compromise", "evidence", "severity", "recommendation"]
                  }
                },
                "environment_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "requirement": {
                        "type": "string"
                      },
                      "affected_flow": {
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
                    "required": ["requirement", "affected_flow", "compromise", "evidence", "severity", "recommendation"]
                  }
                },
                "component_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "component": {
                        "type": "string"
                      },
                      "affected_flow": {
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
                    "required": ["component", "affected_flow", "compromise", "evidence", "severity", "recommendation"]
                  }
                },
                "constraint_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "constraint": {
                        "type": "string"
                      },
                      "affected_flow": {
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
                    "required": ["constraint", "affected_flow", "compromise", "evidence", "severity", "recommendation"]
                  }
                }
              },
              "required": ["task_scope_conflicts", "environment_conflicts", "component_conflicts", "constraint_conflicts"]
            },
            "dataflow_vs_guidelines": {
              "type": "object",
              "properties": {
                "flow_scope_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "flow_element": {
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
                    "required": ["flow_element", "affected_guideline", "compromise", "evidence", "severity", "recommendation"]
                  }
                },
                "transformation_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "transformation": {
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
                    "required": ["transformation", "affected_guideline", "compromise", "evidence", "severity", "recommendation"]
                  }
                },
                "persistence_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "persistence_need": {
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
                    "required": ["persistence_need", "affected_guideline", "compromise", "evidence", "severity", "recommendation"]
                  }
                },
                "circulation_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "circulation_pattern": {
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
                    "required": ["circulation_pattern", "affected_guideline", "compromise", "evidence", "severity", "recommendation"]
                  }
                }
              },
              "required": ["flow_scope_conflicts", "transformation_conflicts", "persistence_conflicts", "circulation_conflicts"]
            }
          },
          "required": ["guidelines_vs_dataflow", "dataflow_vs_guidelines"]
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

# Data Flow Verification Revision
data_flow_verification_revision_prompt = """
# Mycelial Agent Revision Prompt

You are the Mycelial Agent processing reflection results to implement self-corrections to your dual-perspective conflict analysis. Your role is to systematically address identified issues from the reflection phase, refining your analysis of conflicts between data flow specifications and other guidelines from both perspectives.

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
{"reflection_results": {"perspective_quality": {"guidelines_vs_dataflow": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "severity_assessment": {"rating": "high|medium|low", "justification": "string", "adjustment_needs": ["strings"]}}, "dataflow_vs_guidelines": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "severity_assessment": {"rating": "high|medium|low", "justification": "string", "adjustment_needs": ["strings"]}}}, "conflict_specific_feedback": {"guidelines_vs_dataflow": {"task_scope_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "environment_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "component_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "constraint_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}]}, "dataflow_vs_guidelines": {"flow_scope_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "transformation_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "persistence_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "circulation_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}]}}, "missed_conflicts": {"guidelines_vs_dataflow": {"task_scope_conflicts": [{"scope_element": "string", "affected_flow": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "environment_conflicts": [{"requirement": "string", "affected_flow": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "component_conflicts": [{"component": "string", "affected_flow": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "constraint_conflicts": [{"constraint": "string", "affected_flow": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}]}, "dataflow_vs_guidelines": {"flow_scope_conflicts": [{"flow_element": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "transformation_conflicts": [{"transformation": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "persistence_conflicts": [{"persistence_need": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "circulation_conflicts": [{"circulation_pattern": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}]}}, "synthesis_feedback": {"quality": {"rating": "high|medium|low", "justification": "string"}, "missed_patterns": ["strings"], "missed_bidirectional_conflicts": ["strings"], "resolution_improvements": [{"area": "string", "current": "string", "improved": "string", "reason": "string"}]}}}
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
9. Validate all conflicts against both data flow specifications and architectural guidelines

## Output Format

Provide your revised analysis in the following JSON format:

```json
{"revision_metadata": {"processed_feedback": {"perspective_improvements": {"guidelines_vs_dataflow": {"comprehensiveness": ["strings"], "evidence_quality": ["strings"], "severity_assessment": ["strings"]}, "dataflow_vs_guidelines": {"comprehensiveness": ["strings"], "evidence_quality": ["strings"], "severity_assessment": ["strings"]}}, "conflict_adjustments": {"conflicts_removed": {"guidelines_vs_dataflow": integer, "dataflow_vs_guidelines": integer}, "conflicts_added": {"guidelines_vs_dataflow": integer, "dataflow_vs_guidelines": integer}, "conflicts_modified": {"guidelines_vs_dataflow": integer, "dataflow_vs_guidelines": integer}}, "synthesis_improvements": ["strings"]}, "validation_steps": ["strings"]}, "dual_perspective_conflicts": {"guidelines_vs_dataflow": {"task_scope_conflicts": [{"scope_element": "string", "affected_flow": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}], "environment_conflicts": [{"requirement": "string", "affected_flow": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}], "component_conflicts": [{"component": "string", "affected_flow": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}], "constraint_conflicts": [{"constraint": "string", "affected_flow": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}]}, "dataflow_vs_guidelines": {"flow_scope_conflicts": [{"flow_element": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}], "transformation_conflicts": [{"transformation": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}], "persistence_conflicts": [{"persistence_need": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}], "circulation_conflicts": [{"circulation_pattern": "string", "affected_guideline": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}]}, "synthesis": {"key_patterns": ["strings"], "bidirectional_conflicts": ["strings"], "prioritized_resolutions": [{"area": "string", "recommendation": "string", "justification": "string", "revision_note": "string"}]}}}
```

## Revision Guidelines

### Perspective Improvements
- Enhance the completeness of conflict identification in both perspectives
- Ensure proper directionality of conflicts in each perspective
- Strengthen evidence with specific references from both sources
- Adjust severity ratings based on true impact on data integrity

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
7. Ensure appropriate balance across data flow aspects (scope, transformation, persistence, circulation)
8. Verify that bidirectional conflicts are properly identified and addressed

## Self-Correction Principles

1. Focus on genuine conflicts that would impact data integrity and system viability
2. Maintain clear directional separation between perspectives
3. Ensure conflicts are supported by specific evidence from both sources
4. Assign severity ratings consistently based on data integrity impact
5. Provide practical, actionable recommendations that respect both data flow and other guidelines
6. Highlight bidirectional conflicts requiring mutual accommodation
7. Ensure synthesis effectively integrates insights from both perspectives
8. Balance attention across all four data flow aspects: scope, transformation, persistence, and circulation
"""

data_flow_verification_revision_schema = {
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
                "guidelines_vs_dataflow": {
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
                "dataflow_vs_guidelines": {
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
              "required": ["guidelines_vs_dataflow", "dataflow_vs_guidelines"]
            },
            "conflict_adjustments": {
              "type": "object",
              "properties": {
                "conflicts_removed": {
                  "type": "object",
                  "properties": {
                    "guidelines_vs_dataflow": {
                      "type": "integer"
                    },
                    "dataflow_vs_guidelines": {
                      "type": "integer"
                    }
                  },
                  "required": ["guidelines_vs_dataflow", "dataflow_vs_guidelines"]
                },
                "conflicts_added": {
                  "type": "object",
                  "properties": {
                    "guidelines_vs_dataflow": {
                      "type": "integer"
                    },
                    "dataflow_vs_guidelines": {
                      "type": "integer"
                    }
                  },
                  "required": ["guidelines_vs_dataflow", "dataflow_vs_guidelines"]
                },
                "conflicts_modified": {
                  "type": "object",
                  "properties": {
                    "guidelines_vs_dataflow": {
                      "type": "integer"
                    },
                    "dataflow_vs_guidelines": {
                      "type": "integer"
                    }
                  },
                  "required": ["guidelines_vs_dataflow", "dataflow_vs_guidelines"]
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
        "guidelines_vs_dataflow": {
          "type": "object",
          "properties": {
            "task_scope_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "scope_element": {
                    "type": "string"
                  },
                  "affected_flow": {
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
                "required": ["scope_element", "affected_flow", "compromise", "evidence", "severity", "recommendation", "revision_note"]
              }
            },
            "environment_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "requirement": {
                    "type": "string"
                  },
                  "affected_flow": {
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
                "required": ["requirement", "affected_flow", "compromise", "evidence", "severity", "recommendation", "revision_note"]
              }
            },
            "component_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
                    "type": "string"
                  },
                  "affected_flow": {
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
                "required": ["component", "affected_flow", "compromise", "evidence", "severity", "recommendation", "revision_note"]
              }
            },
            "constraint_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "constraint": {
                    "type": "string"
                  },
                  "affected_flow": {
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
                "required": ["constraint", "affected_flow", "compromise", "evidence", "severity", "recommendation", "revision_note"]
              }
            }
          },
          "required": ["task_scope_conflicts", "environment_conflicts", "component_conflicts", "constraint_conflicts"]
        },
        "dataflow_vs_guidelines": {
          "type": "object",
          "properties": {
            "flow_scope_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "flow_element": {
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
                "required": ["flow_element", "affected_guideline", "compromise", "evidence", "severity", "recommendation", "revision_note"]
              }
            },
            "transformation_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "transformation": {
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
                "required": ["transformation", "affected_guideline", "compromise", "evidence", "severity", "recommendation", "revision_note"]
              }
            },
            "persistence_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "persistence_need": {
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
                "required": ["persistence_need", "affected_guideline", "compromise", "evidence", "severity", "recommendation", "revision_note"]
              }
            },
            "circulation_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "circulation_pattern": {
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
                "required": ["circulation_pattern", "affected_guideline", "compromise", "evidence", "severity", "recommendation", "revision_note"]
              }
            }
          },
          "required": ["flow_scope_conflicts", "transformation_conflicts", "persistence_conflicts", "circulation_conflicts"]
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
      "required": ["guidelines_vs_dataflow", "dataflow_vs_guidelines", "synthesis"]
    }
  },
  "required": ["revision_metadata", "dual_perspective_conflicts"]
}