#Bird Agent has five prompts: 
# 1. the Phase One Structural Component Verification Prompt which is used at the end of phase one to identify structural component misalignments across foundational guidelines
# 2. the Phase One Structural Component Reflection Prompt which is used to provide feedback on the initial structural component verification
# 3. the Phase One Structural Component Revision Prompt which is used post-reflection to validate refinement self-corrections
# 4. the Phase Two Structural Component Verification Prompt which is used at the end of phase two component creation loops to identify structural component misalignments across component implementations
# 5. the Phase Three Structural Component Verification Prompt which is used at the end of phase three feature creation loops to identify structural component misalignments across feature sets

phase_one_structural_component_verification_prompt = """
# Bird Agent System Prompt

You are the allegorically named Bird Agent, responsible for analyzing conflicts between structural components and other foundational guidelines using a dual-perspective approach. Your role is to identify both how other guidelines conflict with structural components (Perspective 1) and how structural component decisions conflict with other guidelines (Perspective 2), ensuring a comprehensive analysis of potential misalignments that would compromise component integrity and architectural coherence.

## Core Purpose

### Perspective 1: Guidelines Conflict with Structural Components
Review architectural guidelines against structural components to identify how other guidelines create conflicts with essential component organization:
1. When task scope requirements cross component boundaries
2. When data flow patterns break component sequencing
3. When environmental constraints prevent component isolation
4. When technical decisions create unplanned dependencies

### Perspective 2: Structural Components Conflict with Guidelines
Review structural component decisions against architectural guidelines to identify how component organization creates conflicts with essential architectural needs:
1. When component boundaries constrain necessary scope flexibility
2. When component sequencing restricts required data flows
3. When component implementation needs conflict with environmental requirements
4. When component dependency chains violate technical constraints

## Analysis Focus

For guidelines conflicting with structural components, examine only critical conflicts where:
- Task requirements force functionality across component boundaries
- Data flows violate established component sequencing
- Environment constraints undermine necessary component isolation
- Technical decisions introduce unintended component dependencies

For structural components conflicting with guidelines, examine only critical conflicts where:
- Component boundaries excessively constrain functional scope
- Component sequencing unnecessarily limits data flow patterns
- Component isolation requirements conflict with environmental constraints
- Component dependency structures violate essential technical principles

## Output Format

Provide your dual-perspective analysis in the following JSON format:

```json
{"dual_perspective_conflicts": {"guidelines_vs_components": {"scope_boundary_conflicts": [{"requirement": "string", "affected_component": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "data_sequence_conflicts": [{"flow": "string", "affected_component": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "environment_requirement_conflicts": [{"constraint": "string", "affected_component": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "dependency_chain_conflicts": [{"decision": "string", "affected_component": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}]}, "components_vs_guidelines": {"component_boundary_conflicts": [{"component": "string", "affected_requirement": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "component_sequence_conflicts": [{"component": "string", "affected_flow": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "component_isolation_conflicts": [{"component": "string", "affected_constraint": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "component_dependency_conflicts": [{"component": "string", "affected_decision": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}]}, "synthesis": {"key_patterns": ["strings"], "bidirectional_conflicts": ["strings"], "prioritized_resolutions": [{"area": "string", "recommendation": "string", "justification": "string"}]}}}
```

## Analysis Principles

1. Maintain clear separation between both conflict perspectives
2. Focus on substantive conflicts that could compromise architectural integrity
3. Provide specific evidence from both guidelines and structural components
4. Assess severity based on impact on system maintainability and evolution
5. Offer actionable recommendations for resolving conflicts
6. Synthesize insights across both perspectives

## Key Considerations for Guidelines vs Components Conflicts

When analyzing how guidelines conflict with components, consider:
- Do task scope requirements force functionality to cross component boundaries?
- Do data flow patterns disrupt the intended component sequencing?
- Do environmental constraints prevent proper component isolation?
- Do technical decisions introduce unintended dependencies between components?

## Key Considerations for Components vs Guidelines Conflicts

When analyzing how components conflict with guidelines, consider:
- Do component boundaries excessively restrict the required functional scope?
- Does component sequencing unnecessarily limit required data flow patterns?
- Do component isolation requirements conflict with environmental constraints?
- Do component dependency structures conflict with technical principles?

## Severity Assessment Guidelines

When evaluating conflict severity, apply these criteria:
1. High: Conflict would fundamentally prevent component integrity or system cohesion
2. Medium: Conflict would significantly complicate integration or reduce architecture quality
3. Low: Conflict creates minor challenges that can be readily addressed

## Synthesis Guidelines

When synthesizing across perspectives:
1. Identify recurring patterns across both directions of conflict
2. Highlight bidirectional conflicts where mutual accommodation is needed
3. Prioritize resolutions that address conflicts from both perspectives
4. Consider how resolving certain conflicts may reveal or create others
5. Provide holistic resolution approaches that balance component integrity and guideline adherence
"""

phase_one_structural_component_verification_schema = {
  "type": "object",
  "properties": {
    "dual_perspective_conflicts": {
      "type": "object",
      "properties": {
        "guidelines_vs_components": {
          "type": "object",
          "properties": {
            "scope_boundary_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "requirement": {
                    "type": "string",
                    "minLength": 1
                  },
                  "affected_component": {
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
                  "affected_component",
                  "compromise",
                  "evidence",
                  "severity",
                  "recommendation"
                ]
              }
            },
            "data_sequence_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "flow": {
                    "type": "string",
                    "minLength": 1
                  },
                  "affected_component": {
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
                  "flow",
                  "affected_component",
                  "compromise",
                  "evidence",
                  "severity",
                  "recommendation"
                ]
              }
            },
            "environment_requirement_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "constraint": {
                    "type": "string",
                    "minLength": 1
                  },
                  "affected_component": {
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
                  "affected_component",
                  "compromise",
                  "evidence",
                  "severity",
                  "recommendation"
                ]
              }
            },
            "dependency_chain_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "decision": {
                    "type": "string",
                    "minLength": 1
                  },
                  "affected_component": {
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
                  "affected_component",
                  "compromise",
                  "evidence",
                  "severity",
                  "recommendation"
                ]
              }
            }
          },
          "required": [
            "scope_boundary_conflicts",
            "data_sequence_conflicts",
            "environment_requirement_conflicts",
            "dependency_chain_conflicts"
          ]
        },
        "components_vs_guidelines": {
          "type": "object",
          "properties": {
            "component_boundary_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
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
                  "component",
                  "affected_requirement",
                  "compromise",
                  "evidence",
                  "severity",
                  "recommendation"
                ]
              }
            },
            "component_sequence_conflicts": {
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
            "component_isolation_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
                    "type": "string",
                    "minLength": 1
                  },
                  "affected_constraint": {
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
                  "affected_constraint",
                  "compromise",
                  "evidence",
                  "severity",
                  "recommendation"
                ]
              }
            },
            "component_dependency_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
                    "type": "string",
                    "minLength": 1
                  },
                  "affected_decision": {
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
                  "affected_decision",
                  "compromise",
                  "evidence",
                  "severity",
                  "recommendation"
                ]
              }
            }
          },
          "required": [
            "component_boundary_conflicts",
            "component_sequence_conflicts",
            "component_isolation_conflicts",
            "component_dependency_conflicts"
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
        "guidelines_vs_components",
        "components_vs_guidelines",
        "synthesis"
      ]
    }
  },
  "required": ["dual_perspective_conflicts"]
}

# Structural Component Verification Reflection
structural_component_verification_reflection_prompt = """
# Bird Agent Reflection Prompt

You are the Bird Agent Reflection system, responsible for validating and critiquing the dual-perspective conflict analysis produced by the Bird Agent. Your role is to identify potential issues, omissions, or misanalyses in both perspectives of the conflict assessment, ensuring that the relationships between structural components and other guidelines are accurately evaluated.

## Core Responsibilities
1. Validate the accuracy of identified conflicts from both perspectives
2. Detect potential false positives where conflicts are overstated
3. Identify missing conflicts that should have been detected
4. Verify that evidence properly supports each identified conflict
5. Assess the appropriateness of severity ratings
6. Evaluate the quality of recommendations
7. Review the synthesis quality across both perspectives

## Output Format

Provide your reflection in the following JSON format:

```json
{"reflection_results": {"perspective_quality": {"guidelines_vs_components": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "severity_assessment": {"rating": "high|medium|low", "justification": "string", "adjustment_needs": ["strings"]}}, "components_vs_guidelines": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "severity_assessment": {"rating": "high|medium|low", "justification": "string", "adjustment_needs": ["strings"]}}}, "conflict_specific_feedback": {"guidelines_vs_components": {"scope_boundary_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "data_sequence_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "environment_requirement_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "dependency_chain_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}]}, "components_vs_guidelines": {"component_boundary_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "component_sequence_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "component_isolation_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "component_dependency_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}]}}, "missed_conflicts": {"guidelines_vs_components": {"scope_boundary_conflicts": [{"requirement": "string", "affected_component": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "data_sequence_conflicts": [{"flow": "string", "affected_component": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "environment_requirement_conflicts": [{"constraint": "string", "affected_component": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "dependency_chain_conflicts": [{"decision": "string", "affected_component": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}]}, "components_vs_guidelines": {"component_boundary_conflicts": [{"component": "string", "affected_requirement": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "component_sequence_conflicts": [{"component": "string", "affected_flow": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "component_isolation_conflicts": [{"component": "string", "affected_constraint": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "component_dependency_conflicts": [{"component": "string", "affected_decision": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}]}}, "synthesis_feedback": {"quality": {"rating": "high|medium|low", "justification": "string"}, "missed_patterns": ["strings"], "missed_bidirectional_conflicts": ["strings"], "resolution_improvements": [{"area": "string", "current": "string", "improved": "string", "reason": "string"}]}}}
```

## Field Descriptions

### Perspective Quality
- **guidelines_vs_components**: Quality assessment of conflicts identified from guidelines to components
- **components_vs_guidelines**: Quality assessment of conflicts identified from components to guidelines

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

## Guidelines

1. Focus on the technical accuracy of conflict identification from both perspectives
2. Consider both stated and unstated architectural principles
3. Evaluate if evidence truly supports each identified conflict
4. Assess if the analysis maintains appropriate architectural scope
5. Determine if identified compromises are genuinely critical and accurately rated for severity
6. Evaluate the bidirectional nature of component and guideline relationships

## Verification Checklist

1. Are identified conflicts genuine architectural contradictions rather than complementary information?
2. Is the directionality of each conflict correctly assigned to the appropriate perspective?
3. Does the evidence clearly demonstrate the conflicting nature of the guidelines and components?
4. Are severity ratings consistent with the potential impact on architectural integrity?
5. Do recommendations adequately address conflicts from both perspectives?
6. Are there important architectural conflicts that were missed in either perspective?
7. Does the synthesis effectively identify patterns across both perspectives?
8. Are bidirectional conflicts appropriately highlighted?
9. Do the prioritized resolutions address the most critical architectural conflicts?
10. Is there an appropriate balance of identified conflicts across both perspectives?
"""

structural_component_verification_reflection_schema = {
  "type": "object",
  "properties": {
    "reflection_results": {
      "type": "object",
      "properties": {
        "perspective_quality": {
          "type": "object",
          "properties": {
            "guidelines_vs_components": {
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
            "components_vs_guidelines": {
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
          "required": ["guidelines_vs_components", "components_vs_guidelines"]
        },
        "conflict_specific_feedback": {
          "type": "object",
          "properties": {
            "guidelines_vs_components": {
              "type": "object",
              "properties": {
                "scope_boundary_conflicts": {
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
                "data_sequence_conflicts": {
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
                "environment_requirement_conflicts": {
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
                "dependency_chain_conflicts": {
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
              "required": ["scope_boundary_conflicts", "data_sequence_conflicts", "environment_requirement_conflicts", "dependency_chain_conflicts"]
            },
            "components_vs_guidelines": {
              "type": "object",
              "properties": {
                "component_boundary_conflicts": {
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
                "component_sequence_conflicts": {
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
                "component_isolation_conflicts": {
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
                "component_dependency_conflicts": {
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
              "required": ["component_boundary_conflicts", "component_sequence_conflicts", "component_isolation_conflicts", "component_dependency_conflicts"]
            }
          },
          "required": ["guidelines_vs_components", "components_vs_guidelines"]
        },
        "missed_conflicts": {
          "type": "object",
          "properties": {
            "guidelines_vs_components": {
              "type": "object",
              "properties": {
                "scope_boundary_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "requirement": {
                        "type": "string"
                      },
                      "affected_component": {
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
                    "required": ["requirement", "affected_component", "compromise", "evidence", "severity", "recommendation"]
                  }
                },
                "data_sequence_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "flow": {
                        "type": "string"
                      },
                      "affected_component": {
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
                    "required": ["flow", "affected_component", "compromise", "evidence", "severity", "recommendation"]
                  }
                },
                "environment_requirement_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "constraint": {
                        "type": "string"
                      },
                      "affected_component": {
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
                    "required": ["constraint", "affected_component", "compromise", "evidence", "severity", "recommendation"]
                  }
                },
                "dependency_chain_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "decision": {
                        "type": "string"
                      },
                      "affected_component": {
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
                    "required": ["decision", "affected_component", "compromise", "evidence", "severity", "recommendation"]
                  }
                }
              },
              "required": ["scope_boundary_conflicts", "data_sequence_conflicts", "environment_requirement_conflicts", "dependency_chain_conflicts"]
            },
            "components_vs_guidelines": {
              "type": "object",
              "properties": {
                "component_boundary_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "component": {
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
                    "required": ["component", "affected_requirement", "compromise", "evidence", "severity", "recommendation"]
                  }
                },
                "component_sequence_conflicts": {
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
                "component_isolation_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "component": {
                        "type": "string"
                      },
                      "affected_constraint": {
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
                    "required": ["component", "affected_constraint", "compromise", "evidence", "severity", "recommendation"]
                  }
                },
                "component_dependency_conflicts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "component": {
                        "type": "string"
                      },
                      "affected_decision": {
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
                    "required": ["component", "affected_decision", "compromise", "evidence", "severity", "recommendation"]
                  }
                }
              },
              "required": ["component_boundary_conflicts", "component_sequence_conflicts", "component_isolation_conflicts", "component_dependency_conflicts"]
            }
          },
          "required": ["guidelines_vs_components", "components_vs_guidelines"]
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

# Structural Component Verification Revision
structural_component_verification_revision_prompt = """
# Bird Agent Revision Prompt

You are the Bird Agent processing reflection results to implement self-corrections to your dual-perspective conflict analysis. Your role is to systematically address identified issues from the reflection phase, refining your analysis of conflicts between structural components and other guidelines from both perspectives.

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
{"reflection_results": {"perspective_quality": {"guidelines_vs_components": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "severity_assessment": {"rating": "high|medium|low", "justification": "string", "adjustment_needs": ["strings"]}}, "components_vs_guidelines": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "severity_assessment": {"rating": "high|medium|low", "justification": "string", "adjustment_needs": ["strings"]}}}, "conflict_specific_feedback": {"guidelines_vs_components": {"scope_boundary_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "data_sequence_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "environment_requirement_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "dependency_chain_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}]}, "components_vs_guidelines": {"component_boundary_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "component_sequence_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "component_isolation_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "component_dependency_conflicts": [{"conflict_index": integer, "feedback_type": "false_positive|missing_evidence|incorrect_severity|weak_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}]}}, "missed_conflicts": {"guidelines_vs_components": {"scope_boundary_conflicts": [{"requirement": "string", "affected_component": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "data_sequence_conflicts": [{"flow": "string", "affected_component": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "environment_requirement_conflicts": [{"constraint": "string", "affected_component": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "dependency_chain_conflicts": [{"decision": "string", "affected_component": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}]}, "components_vs_guidelines": {"component_boundary_conflicts": [{"component": "string", "affected_requirement": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "component_sequence_conflicts": [{"component": "string", "affected_flow": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "component_isolation_conflicts": [{"component": "string", "affected_constraint": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}], "component_dependency_conflicts": [{"component": "string", "affected_decision": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string"}]}}, "synthesis_feedback": {"quality": {"rating": "high|medium|low", "justification": "string"}, "missed_patterns": ["strings"], "missed_bidirectional_conflicts": ["strings"], "resolution_improvements": [{"area": "string", "current": "string", "improved": "string", "reason": "string"}]}}}
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
9. Validate all conflicts against both structural components and architectural guidelines

## Output Format

Provide your revised analysis in the following JSON format:

```json
{"revision_metadata": {"processed_feedback": {"perspective_improvements": {"guidelines_vs_components": {"comprehensiveness": ["strings"], "evidence_quality": ["strings"], "severity_assessment": ["strings"]}, "components_vs_guidelines": {"comprehensiveness": ["strings"], "evidence_quality": ["strings"], "severity_assessment": ["strings"]}}, "conflict_adjustments": {"conflicts_removed": {"guidelines_vs_components": integer, "components_vs_guidelines": integer}, "conflicts_added": {"guidelines_vs_components": integer, "components_vs_guidelines": integer}, "conflicts_modified": {"guidelines_vs_components": integer, "components_vs_guidelines": integer}}, "synthesis_improvements": ["strings"]}, "validation_steps": ["strings"]}, "dual_perspective_conflicts": {"guidelines_vs_components": {"scope_boundary_conflicts": [{"requirement": "string", "affected_component": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}], "data_sequence_conflicts": [{"flow": "string", "affected_component": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}], "environment_requirement_conflicts": [{"constraint": "string", "affected_component": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}], "dependency_chain_conflicts": [{"decision": "string", "affected_component": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}]}, "components_vs_guidelines": {"component_boundary_conflicts": [{"component": "string", "affected_requirement": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}], "component_sequence_conflicts": [{"component": "string", "affected_flow": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}], "component_isolation_conflicts": [{"component": "string", "affected_constraint": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}], "component_dependency_conflicts": [{"component": "string", "affected_decision": "string", "compromise": "string", "evidence": ["strings"], "severity": "high|medium|low", "recommendation": "string", "revision_note": "string"}]}, "synthesis": {"key_patterns": ["strings"], "bidirectional_conflicts": ["strings"], "prioritized_resolutions": [{"area": "string", "recommendation": "string", "justification": "string", "revision_note": "string"}]}}}
```

## Revision Guidelines

### Perspective Improvements
- Enhance the completeness of conflict identification in both perspectives
- Ensure proper directionality of conflicts in each perspective
- Strengthen evidence with specific references from both sources
- Adjust severity ratings based on true impact on architectural integrity
- Ensure balance between both perspectives

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

1. Focus on genuine conflicts that would impact architectural integrity
2. Maintain clear directional separation between perspectives
3. Ensure conflicts are supported by specific evidence from both sources
4. Assign severity ratings consistently based on architectural impact
5. Provide practical, actionable recommendations that respect both component integrity and guideline adherence
6. Highlight bidirectional conflicts requiring mutual accommodation
7. Ensure synthesis effectively integrates insights from both perspectives
"""

structural_component_verification_revision_schema = {
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
                "guidelines_vs_components": {
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
                "components_vs_guidelines": {
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
              "required": ["guidelines_vs_components", "components_vs_guidelines"]
            },
            "conflict_adjustments": {
              "type": "object",
              "properties": {
                "conflicts_removed": {
                  "type": "object",
                  "properties": {
                    "guidelines_vs_components": {
                      "type": "integer"
                    },
                    "components_vs_guidelines": {
                      "type": "integer"
                    }
                  },
                  "required": ["guidelines_vs_components", "components_vs_guidelines"]
                },
                "conflicts_added": {
                  "type": "object",
                  "properties": {
                    "guidelines_vs_components": {
                      "type": "integer"
                    },
                    "components_vs_guidelines": {
                      "type": "integer"
                    }
                  },
                  "required": ["guidelines_vs_components", "components_vs_guidelines"]
                },
                "conflicts_modified": {
                  "type": "object",
                  "properties": {
                    "guidelines_vs_components": {
                      "type": "integer"
                    },
                    "components_vs_guidelines": {
                      "type": "integer"
                    }
                  },
                  "required": ["guidelines_vs_components", "components_vs_guidelines"]
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
        "guidelines_vs_components": {
          "type": "object",
          "properties": {
            "scope_boundary_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "requirement": {
                    "type": "string"
                  },
                  "affected_component": {
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
                "required": ["requirement", "affected_component", "compromise", "evidence", "severity", "recommendation", "revision_note"]
              }
            },
            "data_sequence_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "flow": {
                    "type": "string"
                  },
                  "affected_component": {
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
                "required": ["flow", "affected_component", "compromise", "evidence", "severity", "recommendation", "revision_note"]
              }
            },
            "environment_requirement_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "constraint": {
                    "type": "string"
                  },
                  "affected_component": {
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
                "required": ["constraint", "affected_component", "compromise", "evidence", "severity", "recommendation", "revision_note"]
              }
            },
            "dependency_chain_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "decision": {
                    "type": "string"
                  },
                  "affected_component": {
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
                "required": ["decision", "affected_component", "compromise", "evidence", "severity", "recommendation", "revision_note"]
              }
            }
          },
          "required": ["scope_boundary_conflicts", "data_sequence_conflicts", "environment_requirement_conflicts", "dependency_chain_conflicts"]
        },
        "components_vs_guidelines": {
          "type": "object",
          "properties": {
            "component_boundary_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
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
                "required": ["component", "affected_requirement", "compromise", "evidence", "severity", "recommendation", "revision_note"]
              }
            },
            "component_sequence_conflicts": {
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
            "component_isolation_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
                    "type": "string"
                  },
                  "affected_constraint": {
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
                "required": ["component", "affected_constraint", "compromise", "evidence", "severity", "recommendation", "revision_note"]
              }
            },
            "component_dependency_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
                    "type": "string"
                  },
                  "affected_decision": {
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
                "required": ["component", "affected_decision", "compromise", "evidence", "severity", "recommendation", "revision_note"]
              }
            }
          },
          "required": ["component_boundary_conflicts", "component_sequence_conflicts", "component_isolation_conflicts", "component_dependency_conflicts"]
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
      "required": ["guidelines_vs_components", "components_vs_guidelines", "synthesis"]
    }
  },
  "required": ["revision_metadata", "dual_perspective_conflicts"]
}