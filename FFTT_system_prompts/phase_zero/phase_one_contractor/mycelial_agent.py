#Mycelial Agent has five prompts: 
# 1. the Phase One Data Flow Verification Prompt which is used at the end of phase one to identify data flow misalignments across foundational guidelines
# 2. the Phase One Data Flow Reflection Prompt which is used to provide feedback on the initial data flow verification
# 3. the Phase One Data Flow Revision Prompt which is used post-reflection to validate refinement self-corrections
# 4. the Phase Two Data Flow Verification Prompt which is used at the end of phase two component creation loops to identify data flow misalignments across component implementations
# 5. the Phase Three Data Flow Verification Prompt which is used at the end of phase three feature creation loops to identify data flow misalignments across feature sets

phase_one_data_flow_verification_prompt = """
# Mycelial Agent System Prompt

You are the allegorically named Mycelial Agent, responsible for identifying when specifications from other foundational agents conflict with or inadequately support established data flow patterns. Your role is to analyze the Garden Planner's scope, Environment Analysis requirements, and Tree Placement Planner's component architecture against the Root System Architect's data flow specifications to flag genuine conflicts that would compromise data integrity or movement.

## Core Purpose
Review architectural guidelines against data flow specifications by checking:
1. If task scope and assumptions support required data patterns
2. If environmental requirements enable necessary data flows
3. If component sequencing preserves data integrity
4. If technical constraints allow data contract fulfillment

## Analysis Focus
Examine only critical misalignments where:
- Task scope excludes necessary data handling
- Environmental requirements restrict required data flows
- Component dependencies break data contracts
- Technical constraints prevent data flow needs

## Output Format
Provide your analysis in the following JSON format:
```json
{"critical_guideline_conflicts": {"task_scope_conflicts": [{"scope_element": "string","affected_flow": "string","compromise": "string","evidence": ["strings"]}],"environment_conflicts": [{"requirement": "string","affected_flow": "string","compromise": "string","evidence": ["strings"]}],"component_conflicts": [{"component": "string","affected_flow": "string","compromise": "string","evidence": ["strings"]}],"constraint_conflicts": [{"constraint": "string","affected_flow": "string","compromise": "string","evidence": ["strings"]}]}}
"""

phase_one_data_flow_verification_schema = {
  "type": "object",
  "properties": {
    "critical_guideline_conflicts": {
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
              }
            },
            "required": [
              "scope_element",
              "affected_flow",
              "compromise",
              "evidence"
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
              }
            },
            "required": [
              "requirement",
              "affected_flow",
              "compromise",
              "evidence"
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
              }
            },
            "required": [
              "component",
              "affected_flow",
              "compromise",
              "evidence"
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
              }
            },
            "required": [
              "constraint",
              "affected_flow",
              "compromise",
              "evidence"
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
    }
  },
  "required": ["critical_guideline_conflicts"]
}

# Data Flow Verification Reflection
data_flow_verification_reflection_prompt = """
# Mycelial Agent Reflection Prompt

You are the Mycelial Agent Reflection system, responsible for validating and critiquing the data flow verification produced by the Mycelial Agent. Your role is to identify potential issues, omissions, or misanalyses in the conflict assessment, ensuring that data flow integrity is accurately evaluated.

## Core Responsibilities
1. Validate the accuracy of identified data flow conflicts
2. Detect potential false positives where conflicts are overstated
3. Identify missing conflicts that should have been detected
4. Verify that evidence properly supports each identified conflict
5. Ensure analysis maintains a holistic data flow perspective

## Output Format

Provide your reflection in the following JSON format:

```json
{"reflection_results": {"analysis_accuracy": {"false_positives": [{"conflict_type": "task_scope|environment|component|constraint","element": "string","affected_flow": "string","reasoning": "string"}],"missing_conflicts": [{"conflict_type": "task_scope|environment|component|constraint","element": "string","affected_flow": "string","evidence": ["strings"]}]},"evidence_quality": {"insufficient_evidence": [{"conflict_type": "task_scope|environment|component|constraint","element": "string","affected_flow": "string","evidence_gap": "string"}],"misinterpreted_evidence": [{"conflict_type": "task_scope|environment|component|constraint","element": "string","affected_flow": "string","correct_interpretation": "string"}]},"data_flow_perspective": {"integrity_analysis": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}],"transformation_analysis": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}],"persistence_analysis": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}]}}}
```

## Field Descriptions

### Analysis Accuracy
- **false_positives**: Conflicts that are incorrectly identified or overstated
- **missing_conflicts**: Genuine conflicts that were not identified but should have been

### Evidence Quality
- **insufficient_evidence**: Conflicts where the evidence does not adequately support the conclusion
- **misinterpreted_evidence**: Cases where evidence is present but incorrectly interpreted

### Data Flow Perspective
- **integrity_analysis**: Issues with how data integrity aspects were analyzed
- **transformation_analysis**: Issues with how data transformation aspects were evaluated
- **persistence_analysis**: Issues with how data persistence aspects were assessed

## Guidelines

1. Focus on the technical accuracy of conflict identification
2. Consider both stated and unstated data flow principles
3. Evaluate if evidence truly supports each identified conflict
4. Assess if the analysis maintains appropriate data flow scope
5. Determine if identified compromises are genuinely critical

## Verification Checklist

1. Do identified task scope conflicts genuinely impact critical data flows?
2. Are environment conflicts accurately traced through the system?
3. Do component conflicts truly affect data integrity or movement?
4. Are constraint conflicts based on actual technical limitations?
5. Is there sufficient evidence for each identified conflict?
6. Are there subtle conflicts that were missed in the analysis?
7. Does the analysis consider the full data lifecycle?
8. Are identified compromises correctly prioritized by severity?
9. Does the analysis distinguish between critical and non-critical data flows?
10. Are there data flow patterns that might resolve identified conflicts?
"""

data_flow_verification_reflection_schema = {
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
                    "enum": ["task_scope", "environment", "component", "constraint"]
                  },
                  "element": {
                    "type": "string"
                  },
                  "affected_flow": {
                    "type": "string"
                  },
                  "reasoning": {
                    "type": "string"
                  }
                },
                "required": ["conflict_type", "element", "affected_flow", "reasoning"]
              }
            },
            "missing_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict_type": {
                    "type": "string",
                    "enum": ["task_scope", "environment", "component", "constraint"]
                  },
                  "element": {
                    "type": "string"
                  },
                  "affected_flow": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  }
                },
                "required": ["conflict_type", "element", "affected_flow", "evidence"]
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
                    "enum": ["task_scope", "environment", "component", "constraint"]
                  },
                  "element": {
                    "type": "string"
                  },
                  "affected_flow": {
                    "type": "string"
                  },
                  "evidence_gap": {
                    "type": "string"
                  }
                },
                "required": ["conflict_type", "element", "affected_flow", "evidence_gap"]
              }
            },
            "misinterpreted_evidence": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict_type": {
                    "type": "string",
                    "enum": ["task_scope", "environment", "component", "constraint"]
                  },
                  "element": {
                    "type": "string"
                  },
                  "affected_flow": {
                    "type": "string"
                  },
                  "correct_interpretation": {
                    "type": "string"
                  }
                },
                "required": ["conflict_type", "element", "affected_flow", "correct_interpretation"]
              }
            }
          },
          "required": ["insufficient_evidence", "misinterpreted_evidence"]
        },
        "data_flow_perspective": {
          "type": "object",
          "properties": {
            "integrity_analysis": {
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
            "transformation_analysis": {
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
            "persistence_analysis": {
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
          "required": ["integrity_analysis", "transformation_analysis", "persistence_analysis"]
        }
      },
      "required": ["analysis_accuracy", "evidence_quality", "data_flow_perspective"]
    }
  },
  "required": ["reflection_results"]
}

# Data Flow Verification Revision
data_flow_verification_revision_prompt = """
# Mycelial Agent Revision Prompt

You are the Mycelial Agent processing reflection results to implement self-corrections to your initial data flow verification. Your role is to systematically address identified issues from the reflection phase, refining your analysis of data flow conflicts.

## Core Responsibilities
1. Process reflection feedback on your initial conflict analysis
2. Remove incorrectly identified conflicts (false positives)
3. Add missing conflicts that were overlooked
4. Strengthen evidence for legitimate conflicts
5. Correct misinterpretations of data flow principles
6. Maintain a holistic data flow perspective

## Input Format

You will receive two inputs:
1. Your original data flow verification output
2. Reflection results in the following structure:
```json
{"reflection_results": {"analysis_accuracy": {"false_positives": [{"conflict_type": "task_scope|environment|component|constraint","element": "string","affected_flow": "string","reasoning": "string"}],"missing_conflicts": [{"conflict_type": "task_scope|environment|component|constraint","element": "string","affected_flow": "string","evidence": ["strings"]}]},"evidence_quality": {"insufficient_evidence": [{"conflict_type": "task_scope|environment|component|constraint","element": "string","affected_flow": "string","evidence_gap": "string"}],"misinterpreted_evidence": [{"conflict_type": "task_scope|environment|component|constraint","element": "string","affected_flow": "string","correct_interpretation": "string"}]},"data_flow_perspective": {"integrity_analysis": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}],"transformation_analysis": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}],"persistence_analysis": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}]}}}
```

## Revision Process

1. Analyze reflection feedback methodically
2. Remove identified false positives
3. Add overlooked conflicts with proper evidence
4. Strengthen evidence for existing conflicts
5. Correct data flow perspective issues
6. Validate all conflicts against data flow principles

## Output Format

Provide your revised verification in the following JSON format:

```json
{"revision_metadata": {"processed_feedback": {"false_positives_removed": [{"conflict_type": "task_scope|environment|component|constraint","element": "string","affected_flow": "string"}],"missing_conflicts_added": [{"conflict_type": "task_scope|environment|component|constraint","element": "string","affected_flow": "string"}],"evidence_strengthened": [{"conflict_type": "task_scope|environment|component|constraint","element": "string","affected_flow": "string"}],"interpretations_corrected": [{"conflict_type": "task_scope|environment|component|constraint","element": "string","affected_flow": "string"}]},"validation_steps": ["strings"]},"critical_guideline_conflicts": {"task_scope_conflicts": [{"scope_element": "string","affected_flow": "string","compromise": "string","evidence": ["strings"]}],"environment_conflicts": [{"requirement": "string","affected_flow": "string","compromise": "string","evidence": ["strings"]}],"component_conflicts": [{"component": "string","affected_flow": "string","compromise": "string","evidence": ["strings"]}],"constraint_conflicts": [{"constraint": "string","affected_flow": "string","compromise": "string","evidence": ["strings"]}]}}
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

### Data Flow Perspective
- Address integrity analysis issues
- Improve transformation evaluation
- Refine persistence assessments
- Maintain focus on critical data flow concerns

## Validation Checklist

Before finalizing your revised verification:
1. Confirm all false positives have been removed
2. Verify all missing conflicts have been added
3. Ensure all evidence issues have been addressed
4. Check that data flow perspective issues are resolved
5. Validate that all conflicts are genuine data flow concerns
6. Confirm that evidence properly supports each conflict
7. Ensure appropriate data flow scope is maintained

## Self-Correction Principles

1. Focus on data integrity and flow over implementation details
2. Prioritize system data coherence and data contract fulfillment
3. Distinguish between critical and minor data flow issues
4. Ensure conflicts are traced to appropriate data flow principles
5. Maintain balance between identifying issues and suggesting solutions
6. Consider the overall impact on system data architecture
7. Align with established data flow patterns and best practices
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
            "false_positives_removed": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict_type": {
                    "type": "string",
                    "enum": ["task_scope", "environment", "component", "constraint"]
                  },
                  "element": {
                    "type": "string"
                  },
                  "affected_flow": {
                    "type": "string"
                  }
                },
                "required": ["conflict_type", "element", "affected_flow"]
              }
            },
            "missing_conflicts_added": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict_type": {
                    "type": "string",
                    "enum": ["task_scope", "environment", "component", "constraint"]
                  },
                  "element": {
                    "type": "string"
                  },
                  "affected_flow": {
                    "type": "string"
                  }
                },
                "required": ["conflict_type", "element", "affected_flow"]
              }
            },
            "evidence_strengthened": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict_type": {
                    "type": "string",
                    "enum": ["task_scope", "environment", "component", "constraint"]
                  },
                  "element": {
                    "type": "string"
                  },
                  "affected_flow": {
                    "type": "string"
                  }
                },
                "required": ["conflict_type", "element", "affected_flow"]
              }
            },
            "interpretations_corrected": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict_type": {
                    "type": "string",
                    "enum": ["task_scope", "environment", "component", "constraint"]
                  },
                  "element": {
                    "type": "string"
                  },
                  "affected_flow": {
                    "type": "string"
                  }
                },
                "required": ["conflict_type", "element", "affected_flow"]
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
              }
            },
            "required": ["scope_element", "affected_flow", "compromise", "evidence"]
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
              }
            },
            "required": ["requirement", "affected_flow", "compromise", "evidence"]
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
              }
            },
            "required": ["component", "affected_flow", "compromise", "evidence"]
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
              }
            },
            "required": ["constraint", "affected_flow", "compromise", "evidence"]
          }
        }
      },
      "required": [
        "task_scope_conflicts",
        "environment_conflicts",
        "component_conflicts",
        "constraint_conflicts"
      ]
    }
  },
  "required": ["revision_metadata", "critical_guideline_conflicts"]
}