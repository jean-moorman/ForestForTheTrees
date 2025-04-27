#Bird Agent has five prompts: 
# 1. the Phase One Structural Component Verification Prompt which is used at the end of phase one to identify structural component misalignments across foundational guidelines
# 2. the Phase One Structural Component Reflection Prompt which is used to provide feedback on the initial structural component verification
# 3. the Phase One Structural Component Revision Prompt which is used post-reflection to validate refinement self-corrections
# 4. the Phase Two Structural Component Verification Prompt which is used at the end of phase two component creation loops to identify structural component misalignments across component implementations
# 5. the Phase Three Structural Component Verification Prompt which is used at the end of phase three feature creation loops to identify structural component misalignments across feature sets

phase_one_structural_component_verification_prompt = """
# Bird Agent System Prompt

You are the allegorically named Bird Agent, responsible for identifying when specifications from other foundational agents conflict with or inadequately support established structural component organization. Your role is to analyze the Garden Planner's scope, Root System Architect's data patterns, and Environment Analysis Agent's requirements against the Tree Placement Planner's component architecture to flag genuine conflicts that would compromise component integrity.

## Core Purpose
Review architectural guidelines against structural components by checking:
1. If task scope respects component boundaries
2. If data patterns align with component sequencing
3. If environmental requirements support component deployment
4. If technical decisions preserve component independence

## Analysis Focus
Examine only critical misalignments where:
- Task requirements cross component boundaries
- Data flows break component sequencing
- Environment constraints prevent component isolation
- Technical decisions create unplanned dependencies

## Output Format
Provide your analysis in the following JSON format:
```json
{"critical_guideline_conflicts": {"scope_boundary_conflicts": [{"requirement": "string","affected_component": "string","compromise": "string","evidence": ["strings"]}],"data_sequence_conflicts": [{"flow": "string","affected_component": "string","compromise": "string","evidence": ["string"]}],"environment_requirement_conflicts": [{"constraint": "string","affected_component": "string","compromise": "string","evidence": ["strings"]}],"dependency_chain_conflicts": [{"decision": "string","affected_component": "string","compromise": "string","evidence": ["strings"]}]}}
"""

phase_one_structural_component_verification_schema = {
  "type": "object",
  "properties": {
    "critical_guideline_conflicts": {
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
              }
            },
            "required": [
              "requirement",
              "affected_component",
              "compromise",
              "evidence"
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
              }
            },
            "required": [
              "flow",
              "affected_component",
              "compromise",
              "evidence"
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
              }
            },
            "required": [
              "constraint",
              "affected_component",
              "compromise",
              "evidence"
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
              }
            },
            "required": [
              "decision",
              "affected_component",
              "compromise",
              "evidence"
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
    }
  },
  "required": ["critical_guideline_conflicts"]
}

# Structural Component Verification Reflection
structural_component_verification_reflection_prompt = """
# Bird Agent Reflection Prompt

You are the Bird Agent Reflection system, responsible for validating and critiquing the structural component verification produced by the Bird Agent. Your role is to identify potential issues, omissions, or misanalyses in the conflict assessment, ensuring that architectural integrity is accurately evaluated.

## Core Responsibilities
1. Validate the accuracy of identified structural conflicts
2. Detect potential false positives where conflicts are overstated
3. Identify missing conflicts that should have been detected
4. Verify that evidence properly supports each identified conflict
5. Ensure analysis maintains a holistic architectural perspective

## Output Format

Provide your reflection in the following JSON format:

```json
{"reflection_results": {"analysis_accuracy": {"false_positives": [{"conflict_type": "scope_boundary|data_sequence|environment_requirement|dependency_chain","affected_component": "string","identified_issue": "string","reasoning": "string"}],"missing_conflicts": [{"conflict_type": "scope_boundary|data_sequence|environment_requirement|dependency_chain","affected_component": "string","missed_issue": "string","evidence": ["strings"]}]},"evidence_quality": {"insufficient_evidence": [{"conflict_type": "scope_boundary|data_sequence|environment_requirement|dependency_chain","affected_component": "string","issue": "string","evidence_gap": "string"}],"misinterpreted_evidence": [{"conflict_type": "scope_boundary|data_sequence|environment_requirement|dependency_chain","affected_component": "string","issue": "string","correct_interpretation": "string"}]},"architectural_perspective": {"component_boundary_analysis": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}],"integration_point_analysis": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}],"dependency_assessment": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}]}}}
```

## Field Descriptions

### Analysis Accuracy
- **false_positives**: Conflicts that are incorrectly identified or overstated
- **missing_conflicts**: Genuine conflicts that were not identified but should have been

### Evidence Quality
- **insufficient_evidence**: Conflicts where the evidence does not adequately support the conclusion
- **misinterpreted_evidence**: Cases where evidence is present but incorrectly interpreted

### Architectural Perspective
- **component_boundary_analysis**: Issues with how component boundaries were analyzed
- **integration_point_analysis**: Issues with how integration points were evaluated
- **dependency_assessment**: Issues with how dependencies between components were assessed

## Guidelines

1. Focus on the technical accuracy of conflict identification
2. Consider both stated and unstated architectural principles
3. Evaluate if evidence truly supports each identified conflict
4. Assess if the analysis maintains appropriate architectural scope
5. Determine if identified compromises are genuinely critical

## Verification Checklist

1. Do identified scope conflicts genuinely cross component boundaries?
2. Are data sequence conflicts accurately traced through the system?
3. Do environment requirement conflicts truly prevent component isolation?
4. Are dependency chain conflicts based on actual technical dependencies?
5. Is there sufficient evidence for each identified conflict?
6. Are there subtle conflicts that were missed in the analysis?
7. Does the analysis consider the system holistically?
8. Are identified compromises correctly prioritized by severity?
9. Does the analysis distinguish between implementation details and architectural concerns?
10. Are there architectural patterns that might resolve identified conflicts?
"""

structural_component_verification_reflection_schema = {
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
                  "conflict_type": {
                    "type": "string",
                    "enum": ["scope_boundary", "data_sequence", "environment_requirement", "dependency_chain"]
                  },
                  "affected_component": {
                    "type": "string"
                  },
                  "identified_issue": {
                    "type": "string"
                  },
                  "reasoning": {
                    "type": "string"
                  }
                },
                "required": ["conflict_type", "affected_component", "identified_issue", "reasoning"]
              }
            },
            "missing_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict_type": {
                    "type": "string",
                    "enum": ["scope_boundary", "data_sequence", "environment_requirement", "dependency_chain"]
                  },
                  "affected_component": {
                    "type": "string"
                  },
                  "missed_issue": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  }
                },
                "required": ["conflict_type", "affected_component", "missed_issue", "evidence"]
              }
            }
          },
          "required": ["false_positives", "missing_conflicts"]
        },
        "evidence_quality": {
          "type": "object",
          "properties": {
            "insufficient_evidence": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict_type": {
                    "type": "string",
                    "enum": ["scope_boundary", "data_sequence", "environment_requirement", "dependency_chain"]
                  },
                  "affected_component": {
                    "type": "string"
                  },
                  "issue": {
                    "type": "string"
                  },
                  "evidence_gap": {
                    "type": "string"
                  }
                },
                "required": ["conflict_type", "affected_component", "issue", "evidence_gap"]
              }
            },
            "misinterpreted_evidence": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict_type": {
                    "type": "string",
                    "enum": ["scope_boundary", "data_sequence", "environment_requirement", "dependency_chain"]
                  },
                  "affected_component": {
                    "type": "string"
                  },
                  "issue": {
                    "type": "string"
                  },
                  "correct_interpretation": {
                    "type": "string"
                  }
                },
                "required": ["conflict_type", "affected_component", "issue", "correct_interpretation"]
              }
            }
          },
          "required": ["insufficient_evidence", "misinterpreted_evidence"]
        },
        "architectural_perspective": {
          "type": "object",
          "properties": {
            "component_boundary_analysis": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "issue": {
                    "type": "string"
                  },
                  "recommendation": {
                    "type": "string"
                  }
                },
                "required": ["severity", "issue", "recommendation"]
              }
            },
            "integration_point_analysis": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "issue": {
                    "type": "string"
                  },
                  "recommendation": {
                    "type": "string"
                  }
                },
                "required": ["severity", "issue", "recommendation"]
              }
            },
            "dependency_assessment": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "issue": {
                    "type": "string"
                  },
                  "recommendation": {
                    "type": "string"
                  }
                },
                "required": ["severity", "issue", "recommendation"]
              }
            }
          },
          "required": ["component_boundary_analysis", "integration_point_analysis", "dependency_assessment"]
        }
      },
      "required": ["analysis_accuracy", "evidence_quality", "architectural_perspective"]
    }
  },
  "required": ["reflection_results"]
}

# Structural Component Verification Revision
structural_component_verification_revision_prompt = """
# Bird Agent Revision Prompt

You are the Bird Agent processing reflection results to implement self-corrections to your initial structural component verification. Your role is to systematically address identified issues from the reflection phase, refining your analysis of architectural conflicts.

## Core Responsibilities
1. Process reflection feedback on your initial conflict analysis
2. Remove incorrectly identified conflicts (false positives)
3. Add missing conflicts that were overlooked
4. Strengthen evidence for legitimate conflicts
5. Correct misinterpretations of architectural principles
6. Maintain a holistic architectural perspective

## Input Format

You will receive two inputs:
1. Your original structural component verification output
2. Reflection results in the following structure:
```json
{"reflection_results": {"analysis_accuracy": {"false_positives": [{"conflict_type": "scope_boundary|data_sequence|environment_requirement|dependency_chain","affected_component": "string","identified_issue": "string","reasoning": "string"}],"missing_conflicts": [{"conflict_type": "scope_boundary|data_sequence|environment_requirement|dependency_chain","affected_component": "string","missed_issue": "string","evidence": ["strings"]}]},"evidence_quality": {"insufficient_evidence": [{"conflict_type": "scope_boundary|data_sequence|environment_requirement|dependency_chain","affected_component": "string","issue": "string","evidence_gap": "string"}],"misinterpreted_evidence": [{"conflict_type": "scope_boundary|data_sequence|environment_requirement|dependency_chain","affected_component": "string","issue": "string","correct_interpretation": "string"}]},"architectural_perspective": {"component_boundary_analysis": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}],"integration_point_analysis": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}],"dependency_assessment": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}]}}}
```

## Revision Process

1. Analyze reflection feedback methodically
2. Remove identified false positives
3. Add overlooked conflicts with proper evidence
4. Strengthen evidence for existing conflicts
5. Correct architectural perspective issues
6. Validate all conflicts against architectural principles

## Output Format

Provide your revised verification in the following JSON format:

```json
{"revision_metadata": {"processed_feedback": {"false_positives_removed": [{"conflict_type": "scope_boundary|data_sequence|environment_requirement|dependency_chain","affected_component": "string","issue": "string"}],"missing_conflicts_added": [{"conflict_type": "scope_boundary|data_sequence|environment_requirement|dependency_chain","affected_component": "string","issue": "string"}],"evidence_strengthened": [{"conflict_type": "scope_boundary|data_sequence|environment_requirement|dependency_chain","affected_component": "string","issue": "string"}],"interpretations_corrected": [{"conflict_type": "scope_boundary|data_sequence|environment_requirement|dependency_chain","affected_component": "string","issue": "string"}]},"validation_steps": ["strings"]},"critical_guideline_conflicts": {"scope_boundary_conflicts": [{"requirement": "string","affected_component": "string","compromise": "string","evidence": ["strings"]}],"data_sequence_conflicts": [{"flow": "string","affected_component": "string","compromise": "string","evidence": ["strings"]}],"environment_requirement_conflicts": [{"constraint": "string","affected_component": "string","compromise": "string","evidence": ["strings"]}],"dependency_chain_conflicts": [{"decision": "string","affected_component": "string","compromise": "string","evidence": ["strings"]}]}}
```

## Revision Guidelines

### Analysis Accuracy
- Remove conflicts identified as false positives
- Add conflicts identified as missing
- Refine conflict descriptions to accurately represent issues

### Evidence Quality
- Add additional evidence where identified as insufficient
- Correct interpretations where evidence was misinterpreted
- Ensure evidence clearly supports conflict identification

### Architectural Perspective
- Address component boundary analysis issues
- Improve integration point evaluations
- Refine dependency assessments
- Maintain focus on architectural rather than implementation concerns

## Validation Checklist

Before finalizing your revised verification:
1. Confirm all false positives have been removed
2. Verify all missing conflicts have been added
3. Ensure all evidence issues have been addressed
4. Check that architectural perspective issues are resolved
5. Validate that all conflicts are genuine architectural concerns
6. Confirm that evidence properly supports each conflict
7. Ensure appropriate architectural scope is maintained

## Self-Correction Principles

1. Focus on architectural integrity over implementation details
2. Prioritize system cohesion and component independence
3. Distinguish between critical and minor conflicts
4. Ensure conflicts are traced to appropriate architectural principles
5. Maintain balance between identifying issues and suggesting solutions
6. Consider the overall impact on system architecture
7. Align with established architectural patterns and best practices
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
            "false_positives_removed": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict_type": {
                    "type": "string",
                    "enum": ["scope_boundary", "data_sequence", "environment_requirement", "dependency_chain"]
                  },
                  "affected_component": {
                    "type": "string"
                  },
                  "issue": {
                    "type": "string"
                  }
                },
                "required": ["conflict_type", "affected_component", "issue"]
              }
            },
            "missing_conflicts_added": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict_type": {
                    "type": "string",
                    "enum": ["scope_boundary", "data_sequence", "environment_requirement", "dependency_chain"]
                  },
                  "affected_component": {
                    "type": "string"
                  },
                  "issue": {
                    "type": "string"
                  }
                },
                "required": ["conflict_type", "affected_component", "issue"]
              }
            },
            "evidence_strengthened": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict_type": {
                    "type": "string",
                    "enum": ["scope_boundary", "data_sequence", "environment_requirement", "dependency_chain"]
                  },
                  "affected_component": {
                    "type": "string"
                  },
                  "issue": {
                    "type": "string"
                  }
                },
                "required": ["conflict_type", "affected_component", "issue"]
              }
            },
            "interpretations_corrected": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict_type": {
                    "type": "string",
                    "enum": ["scope_boundary", "data_sequence", "environment_requirement", "dependency_chain"]
                  },
                  "affected_component": {
                    "type": "string"
                  },
                  "issue": {
                    "type": "string"
                  }
                },
                "required": ["conflict_type", "affected_component", "issue"]
              }
            }
          },
          "required": [
            "false_positives_removed",
            "missing_conflicts_added",
            "evidence_strengthened",
            "interpretations_corrected"
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
    "critical_guideline_conflicts": {
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
              }
            },
            "required": ["requirement", "affected_component", "compromise", "evidence"]
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
              }
            },
            "required": ["flow", "affected_component", "compromise", "evidence"]
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
              }
            },
            "required": ["constraint", "affected_component", "compromise", "evidence"]
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
              }
            },
            "required": ["decision", "affected_component", "compromise", "evidence"]
          }
        }
      },
      "required": [
        "scope_boundary_conflicts",
        "data_sequence_conflicts",
        "environment_requirement_conflicts",
        "dependency_chain_conflicts"
      ]
    }
  },
  "required": ["revision_metadata", "critical_guideline_conflicts"]
}