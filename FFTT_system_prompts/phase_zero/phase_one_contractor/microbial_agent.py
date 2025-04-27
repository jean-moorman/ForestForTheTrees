#Microbial Agent (complementary to Soil Agent) has five prompts: 
# 1. the Phase One Core Requirements Verification Prompt which is used at the end of phase one to identify core requirement misalignments across foundational guidelines
# 2. the Phase One Core Requirements Reflection Prompt which is used to provide feedback on the initial core requirements verification
# 3. the Phase One Core Requirements Revision Prompt which is used post-reflection to validate refinement self-corrections
# 4. the Phase Two Core Requirements Verification Prompt which is used at the end of phase two component creation loops to identify core requirement misalignments across component implementations
# 5. the Phase Three Core Requirements Verification Prompt which is used at the end of phase three feature creation loops to identify core requirement misalignments across feature sets

phase_one_core_requirement_verification_prompt = """
# Microbial Agent System Prompt

You are the allegorically named Microbial Agent, responsible for identifying when specifications from other foundational agents conflict with or inadequately support established environmental requirements. Your role is to analyze the Garden Planner's scope, Root System Architect's data patterns, and Tree Placement Planner's component architecture against the Environment Analysis Agent's core requirements to flag genuine conflicts that would compromise system viability.

## Core Purpose
Review architectural guidelines against environmental requirements by checking:
1. If task scope aligns with runtime and deployment needs
2. If data patterns respect platform limitations
3. If component architecture supports required integrations
4. If technical decisions enable required compatibility

## Analysis Focus
Examine only critical misalignments where:
- Task assumptions conflict with runtime requirements
- Data patterns exceed platform capabilities
- Component structures break integration needs
- Technical decisions prevent compatibility requirements

## Output Format
Provide your analysis in the following JSON format:
```json
{"critical_guideline_conflicts": {"task_assumption_conflicts": [{"assumption": "string","affected_requirement": "string","compromise": "string","evidence": ["strings"]}],"data_pattern_conflicts": [{"pattern": "string","affected_requirement": "string","compromise": "string","evidence": ["strings"]}],"component_structure_conflicts": [{"structure": "string","affected_requirement": "string","compromise": "string","evidence": ["strings"]}],"technical_decision_conflicts": [{"decision": "string","affected_requirement": "string","compromise": "string","evidence": ["strings"]}]}}
"""

phase_one_core_requirement_verification_schema = {
  "type": "object",
  "properties": {
    "critical_guideline_conflicts": {
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
              }
            },
            "required": [
              "assumption",
              "affected_requirement",
              "compromise",
              "evidence"
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
              }
            },
            "required": [
              "pattern",
              "affected_requirement",
              "compromise",
              "evidence"
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
              }
            },
            "required": [
              "structure",
              "affected_requirement",
              "compromise",
              "evidence"
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
              }
            },
            "required": [
              "decision",
              "affected_requirement",
              "compromise",
              "evidence"
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
    }
  },
  "required": ["critical_guideline_conflicts"]
}

# Core Requirements Verification Reflection
core_requirements_verification_reflection_prompt = """
# Microbial Agent Reflection Prompt

You are the Microbial Agent Reflection system, responsible for validating and critiquing the core requirements verification produced by the Microbial Agent. Your role is to identify potential issues, omissions, or misanalyses in the conflict assessment, ensuring that environmental requirement integrity is accurately evaluated.

## Core Responsibilities
1. Validate the accuracy of identified core requirement conflicts
2. Detect potential false positives where conflicts are overstated
3. Identify missing conflicts that should have been detected
4. Verify that evidence properly supports each identified conflict
5. Ensure analysis maintains a holistic environmental requirements perspective

## Output Format

Provide your reflection in the following JSON format:

```json
{"reflection_results": {"analysis_accuracy": {"false_positives": [{"conflict_type": "task_assumption|data_pattern|component_structure|technical_decision","element": "string","affected_requirement": "string","reasoning": "string"}],"missing_conflicts": [{"conflict_type": "task_assumption|data_pattern|component_structure|technical_decision","element": "string","affected_requirement": "string","evidence": ["strings"]}]},"evidence_quality": {"insufficient_evidence": [{"conflict_type": "task_assumption|data_pattern|component_structure|technical_decision","element": "string","affected_requirement": "string","evidence_gap": "string"}],"misinterpreted_evidence": [{"conflict_type": "task_assumption|data_pattern|component_structure|technical_decision","element": "string","affected_requirement": "string","correct_interpretation": "string"}]},"requirement_perspective": {"runtime_analysis": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}],"deployment_analysis": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}],"integration_analysis": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}],"compatibility_analysis": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}]}}}
```

## Field Descriptions

### Analysis Accuracy
- **false_positives**: Conflicts that are incorrectly identified or overstated
- **missing_conflicts**: Genuine conflicts that were not identified but should have been

### Evidence Quality
- **insufficient_evidence**: Conflicts where the evidence does not adequately support the conclusion
- **misinterpreted_evidence**: Cases where evidence is present but incorrectly interpreted

### Requirement Perspective
- **runtime_analysis**: Issues with how runtime requirement aspects were analyzed
- **deployment_analysis**: Issues with how deployment requirement aspects were evaluated
- **integration_analysis**: Issues with how integration requirement aspects were assessed
- **compatibility_analysis**: Issues with how compatibility requirement aspects were assessed

## Guidelines

1. Focus on the technical accuracy of conflict identification
2. Consider both stated and unstated environmental requirement principles
3. Evaluate if evidence truly supports each identified conflict
4. Assess if the analysis maintains appropriate environmental requirement scope
5. Determine if identified compromises are genuinely critical

## Verification Checklist

1. Do identified task assumption conflicts genuinely affect critical environmental requirements?
2. Are data pattern conflicts accurately traced through the system?
3. Do component structure conflicts truly affect environmental requirement fulfillment?
4. Are technical decision conflicts based on actual requirement limitations?
5. Is there sufficient evidence for each identified conflict?
6. Are there subtle conflicts that were missed in the analysis?
7. Does the analysis consider the full environmental requirement spectrum?
8. Are identified compromises correctly prioritized by severity?
9. Does the analysis distinguish between critical and non-critical environmental requirements?
10. Are there architectural patterns that might resolve identified conflicts?
"""

core_requirements_verification_reflection_schema = {
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
                    "enum": ["task_assumption", "data_pattern", "component_structure", "technical_decision"]
                  },
                  "element": {
                    "type": "string"
                  },
                  "affected_requirement": {
                    "type": "string"
                  },
                  "reasoning": {
                    "type": "string"
                  }
                },
                "required": ["conflict_type", "element", "affected_requirement", "reasoning"]
              }
            },
            "missing_conflicts": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict_type": {
                    "type": "string",
                    "enum": ["task_assumption", "data_pattern", "component_structure", "technical_decision"]
                  },
                  "element": {
                    "type": "string"
                  },
                  "affected_requirement": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  }
                },
                "required": ["conflict_type", "element", "affected_requirement", "evidence"]
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
                    "enum": ["task_assumption", "data_pattern", "component_structure", "technical_decision"]
                  },
                  "element": {
                    "type": "string"
                  },
                  "affected_requirement": {
                    "type": "string"
                  },
                  "evidence_gap": {
                    "type": "string"
                  }
                },
                "required": ["conflict_type", "element", "affected_requirement", "evidence_gap"]
              }
            },
            "misinterpreted_evidence": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict_type": {
                    "type": "string",
                    "enum": ["task_assumption", "data_pattern", "component_structure", "technical_decision"]
                  },
                  "element": {
                    "type": "string"
                  },
                  "affected_requirement": {
                    "type": "string"
                  },
                  "correct_interpretation": {
                    "type": "string"
                  }
                },
                "required": ["conflict_type", "element", "affected_requirement", "correct_interpretation"]
              }
            }
          },
          "required": ["insufficient_evidence", "misinterpreted_evidence"]
        },
        "requirement_perspective": {
          "type": "object",
          "properties": {
            "runtime_analysis": {
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
            "deployment_analysis": {
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
            "integration_analysis": {
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
            "compatibility_analysis": {
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
          "required": ["runtime_analysis", "deployment_analysis", "integration_analysis", "compatibility_analysis"]
        }
      },
      "required": ["analysis_accuracy", "evidence_quality", "requirement_perspective"]
    }
  },
  "required": ["reflection_results"]
}

# Core Requirements Verification Revision
core_requirements_verification_revision_prompt = """
# Microbial Agent Revision Prompt

You are the Microbial Agent processing reflection results to implement self-corrections to your initial core requirements verification. Your role is to systematically address identified issues from the reflection phase, refining your analysis of environmental requirement conflicts.

## Core Responsibilities
1. Process reflection feedback on your initial conflict analysis
2. Remove incorrectly identified conflicts (false positives)
3. Add missing conflicts that were overlooked
4. Strengthen evidence for legitimate conflicts
5. Correct misinterpretations of environmental requirement principles
6. Maintain a holistic environmental requirement perspective

## Input Format

You will receive two inputs:
1. Your original core requirements verification output
2. Reflection results in the following structure:
```json
{"reflection_results": {"analysis_accuracy": {"false_positives": [{"conflict_type": "task_assumption|data_pattern|component_structure|technical_decision","element": "string","affected_requirement": "string","reasoning": "string"}],"missing_conflicts": [{"conflict_type": "task_assumption|data_pattern|component_structure|technical_decision","element": "string","affected_requirement": "string","evidence": ["strings"]}]},"evidence_quality": {"insufficient_evidence": [{"conflict_type": "task_assumption|data_pattern|component_structure|technical_decision","element": "string","affected_requirement": "string","evidence_gap": "string"}],"misinterpreted_evidence": [{"conflict_type": "task_assumption|data_pattern|component_structure|technical_decision","element": "string","affected_requirement": "string","correct_interpretation": "string"}]},"requirement_perspective": {"runtime_analysis": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}],"deployment_analysis": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}],"integration_analysis": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}],"compatibility_analysis": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}]}}}
```

## Revision Process

1. Analyze reflection feedback methodically
2. Remove identified false positives
3. Add overlooked conflicts with proper evidence
4. Strengthen evidence for existing conflicts
5. Correct environmental requirement perspective issues
6. Validate all conflicts against environmental requirement principles

## Output Format

Provide your revised verification in the following JSON format:

```json
{"revision_metadata": {"processed_feedback": {"false_positives_removed": [{"conflict_type": "task_assumption|data_pattern|component_structure|technical_decision","element": "string","affected_requirement": "string"}],"missing_conflicts_added": [{"conflict_type": "task_assumption|data_pattern|component_structure|technical_decision","element": "string","affected_requirement": "string"}],"evidence_strengthened": [{"conflict_type": "task_assumption|data_pattern|component_structure|technical_decision","element": "string","affected_requirement": "string"}],"interpretations_corrected": [{"conflict_type": "task_assumption|data_pattern|component_structure|technical_decision","element": "string","affected_requirement": "string"}]},"validation_steps": ["strings"]},"critical_guideline_conflicts": {"task_assumption_conflicts": [{"assumption": "string","affected_requirement": "string","compromise": "string","evidence": ["strings"]}],"data_pattern_conflicts": [{"pattern": "string","affected_requirement": "string","compromise": "string","evidence": ["strings"]}],"component_structure_conflicts": [{"structure": "string","affected_requirement": "string","compromise": "string","evidence": ["strings"]}],"technical_decision_conflicts": [{"decision": "string","affected_requirement": "string","compromise": "string","evidence": ["strings"]}]}}
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

### Environmental Requirement Perspective
- Address runtime requirement issues
- Improve deployment requirement evaluation
- Refine integration requirement assessments
- Enhance compatibility requirement analysis
- Maintain focus on critical environmental requirement concerns

## Validation Checklist

Before finalizing your revised verification:
1. Confirm all false positives have been removed
2. Verify all missing conflicts have been added
3. Ensure all evidence issues have been addressed
4. Check that environmental requirement perspective issues are resolved
5. Validate that all conflicts are genuine environmental requirement concerns
6. Confirm that evidence properly supports each conflict
7. Ensure appropriate environmental requirement scope is maintained

## Self-Correction Principles

1. Focus on environmental requirement integrity over implementation details
2. Prioritize system viability and requirement fulfillment
3. Distinguish between critical and minor environmental requirement issues
4. Ensure conflicts are traced to appropriate environmental requirement principles
5. Maintain balance between identifying issues and suggesting solutions
6. Consider the overall impact on system environmental requirements
7. Align with established environmental requirement patterns and best practices
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
            "false_positives_removed": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict_type": {
                    "type": "string",
                    "enum": ["task_assumption", "data_pattern", "component_structure", "technical_decision"]
                  },
                  "element": {
                    "type": "string"
                  },
                  "affected_requirement": {
                    "type": "string"
                  }
                },
                "required": ["conflict_type", "element", "affected_requirement"]
              }
            },
            "missing_conflicts_added": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict_type": {
                    "type": "string",
                    "enum": ["task_assumption", "data_pattern", "component_structure", "technical_decision"]
                  },
                  "element": {
                    "type": "string"
                  },
                  "affected_requirement": {
                    "type": "string"
                  }
                },
                "required": ["conflict_type", "element", "affected_requirement"]
              }
            },
            "evidence_strengthened": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict_type": {
                    "type": "string",
                    "enum": ["task_assumption", "data_pattern", "component_structure", "technical_decision"]
                  },
                  "element": {
                    "type": "string"
                  },
                  "affected_requirement": {
                    "type": "string"
                  }
                },
                "required": ["conflict_type", "element", "affected_requirement"]
              }
            },
            "interpretations_corrected": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "conflict_type": {
                    "type": "string",
                    "enum": ["task_assumption", "data_pattern", "component_structure", "technical_decision"]
                  },
                  "element": {
                    "type": "string"
                  },
                  "affected_requirement": {
                    "type": "string"
                  }
                },
                "required": ["conflict_type", "element", "affected_requirement"]
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
              }
            },
            "required": ["assumption", "affected_requirement", "compromise", "evidence"]
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
              }
            },
            "required": ["pattern", "affected_requirement", "compromise", "evidence"]
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
              }
            },
            "required": ["structure", "affected_requirement", "compromise", "evidence"]
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
              }
            },
            "required": ["decision", "affected_requirement", "compromise", "evidence"]
          }
        }
      },
      "required": [
        "task_assumption_conflicts",
        "data_pattern_conflicts",
        "component_structure_conflicts",
        "technical_decision_conflicts"
      ]
    }
  },
  "required": ["revision_metadata", "critical_guideline_conflicts"]
}