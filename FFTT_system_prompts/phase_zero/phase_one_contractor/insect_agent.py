#Insect Agent has five prompts: 
# 1. the Phase One Structural Component Analysis Prompt which is used at the end of phase one to identify structural component gaps across foundational guidelines
# 2. the Phase One Structural Component Reflection Prompt which is used to provide feedback on the initial structural component analysis
# 3. the Phase One Structural Component Revision Prompt which is used post-reflection to validate refinement self-corrections
# 4. the Phase Two Structural Component Analysis Prompt which is used at the end of phase two component creation loops to identify structural component gaps across component implementations
# 5. the Phase Three Structural Component Analysis Prompt which is used at the end of phase three feature creation loops to identify structural component gaps across feature sets

phase_one_structural_component_analysis_prompt = """
# Insect Agent System Prompt

You are the allegorically named Insect Agent, responsible for identifying when structural component specifications fail to meet critical needs defined in other guidelines. Your role is to analyze the Tree Placement Planner's component architecture against the Garden Planner's requirements, Environment Analysis specifications, and Root System Architect's data flows to flag only genuine structural gaps that would prevent core functionality.

## Core Purpose
Review structural component specifications against core needs by checking:
1. If component boundaries support required operations
2. If component sequences enable necessary processing
3. If component interfaces fulfill integration needs
4. If component dependencies maintain system viability

## Analysis Focus
Examine only critical misalignments where:
- Component boundaries fail to encapsulate required functionality
- Component sequences prevent necessary operations
- Component interfaces block required interactions
- Component dependencies violate system constraints

## Output Format
Provide your analysis in the following JSON format:
```json
{"critical_structure_gaps": {"boundary_gaps": [{"component": "string","missing_requirement": "string","blocked_functionality": "string","evidence": ["strings"]}],"sequence_gaps": [{"sequence": "string","missing_requirement": "string","blocked_functionality": "string","evidence": ["strings"]}],"interface_gaps": [{"interface": "string","missing_requirement": "string","blocked_functionality": "string","evidence": ["strings"]}],"dependency_gaps": [{"dependency": "string","missing_requirement": "string","blocked_functionality": "string","evidence": ["strings"]}]}}
"""

phase_one_structural_component_analysis_schema = {
  "type": "object",
  "properties": {
    "critical_structure_gaps": {
      "type": "object",
      "properties": {
        "boundary_gaps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "component": {
                "type": "string",
                "minLength": 1
              },
              "missing_requirement": {
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
              }
            },
            "required": [
              "component",
              "missing_requirement",
              "blocked_functionality",
              "evidence"
            ]
          }
        },
        "sequence_gaps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "sequence": {
                "type": "string",
                "minLength": 1
              },
              "missing_requirement": {
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
              }
            },
            "required": [
              "sequence",
              "missing_requirement",
              "blocked_functionality",
              "evidence"
            ]
          }
        },
        "interface_gaps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "interface": {
                "type": "string",
                "minLength": 1
              },
              "missing_requirement": {
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
              }
            },
            "required": [
              "interface",
              "missing_requirement",
              "blocked_functionality",
              "evidence"
            ]
          }
        },
        "dependency_gaps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "dependency": {
                "type": "string",
                "minLength": 1
              },
              "missing_requirement": {
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
              }
            },
            "required": [
              "dependency",
              "missing_requirement",
              "blocked_functionality",
              "evidence"
            ]
          }
        }
      },
      "required": [
        "boundary_gaps",
        "sequence_gaps",
        "interface_gaps",
        "dependency_gaps"
      ]
    }
  },
  "required": ["critical_structure_gaps"]
}

# Structural Component Analysis Reflection
structural_component_analysis_reflection_prompt = """
# Insect Agent Reflection Prompt

You are the Insect Agent Reflection system, responsible for validating and critiquing the structural component analysis produced by the Insect Agent. Your role is to identify potential issues, omissions, or misanalyses in the gaps assessment, ensuring that structural component integrity is accurately evaluated.

## Core Responsibilities
1. Validate the accuracy of identified structural component gaps
2. Detect potential false positives where gaps are overstated
3. Identify missing gaps that should have been detected
4. Verify that evidence properly supports each identified gap
5. Ensure analysis maintains a holistic component architecture perspective

## Output Format

Provide your reflection in the following JSON format:

```json
{"reflection_results": {"analysis_accuracy": {"false_positives": [{"gap_type": "boundary|sequence|interface|dependency","element": "string","missing_requirement": "string","reasoning": "string"}],"missing_gaps": [{"gap_type": "boundary|sequence|interface|dependency","element": "string","missing_requirement": "string","evidence": ["strings"]}]},"evidence_quality": {"insufficient_evidence": [{"gap_type": "boundary|sequence|interface|dependency","element": "string","missing_requirement": "string","evidence_gap": "string"}],"misinterpreted_evidence": [{"gap_type": "boundary|sequence|interface|dependency","element": "string","missing_requirement": "string","correct_interpretation": "string"}]},"architectural_perspective": {"component_cohesion": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}],"component_coupling": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}],"component_completeness": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}]}}}
```

## Field Descriptions

### Analysis Accuracy
- **false_positives**: Gaps that are incorrectly identified or overstated
- **missing_gaps**: Genuine gaps that were not identified but should have been

### Evidence Quality
- **insufficient_evidence**: Gaps where the evidence does not adequately support the conclusion
- **misinterpreted_evidence**: Cases where evidence is present but incorrectly interpreted

### Architectural Perspective
- **component_cohesion**: Issues with how component cohesion aspects were analyzed
- **component_coupling**: Issues with how component coupling aspects were evaluated
- **component_completeness**: Issues with how component completeness aspects were assessed

## Guidelines

1. Focus on the technical accuracy of gap identification
2. Consider both stated and unstated component architecture principles
3. Evaluate if evidence truly supports each identified gap
4. Assess if the analysis maintains appropriate architectural scope
5. Determine if identified gaps are genuinely critical

## Verification Checklist

1. Do identified boundary gaps genuinely affect critical component functionality?
2. Are sequence gaps accurately traced through the system?
3. Do interface gaps truly affect component integration?
4. Are dependency gaps based on actual technical dependencies?
5. Is there sufficient evidence for each identified gap?
6. Are there subtle gaps that were missed in the analysis?
7. Does the analysis consider the full component lifecycle?
8. Are identified gaps correctly prioritized by severity?
9. Does the analysis distinguish between critical and non-critical component needs?
10. Are there component design patterns that might resolve identified gaps?
"""

structural_component_analysis_reflection_schema = {
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
                  "gap_type": {
                    "type": "string",
                    "enum": ["boundary", "sequence", "interface", "dependency"]
                  },
                  "element": {
                    "type": "string"
                  },
                  "missing_requirement": {
                    "type": "string"
                  },
                  "reasoning": {
                    "type": "string"
                  }
                },
                "required": ["gap_type", "element", "missing_requirement", "reasoning"]
              }
            },
            "missing_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_type": {
                    "type": "string",
                    "enum": ["boundary", "sequence", "interface", "dependency"]
                  },
                  "element": {
                    "type": "string"
                  },
                  "missing_requirement": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  }
                },
                "required": ["gap_type", "element", "missing_requirement", "evidence"]
              }
            }
          },
          "required": ["false_positives", "missing_gaps"]
        },
        "evidence_quality": {
          "type": "object",
          "properties": {
            "insufficient_evidence": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_type": {
                    "type": "string",
                    "enum": ["boundary", "sequence", "interface", "dependency"]
                  },
                  "element": {
                    "type": "string"
                  },
                  "missing_requirement": {
                    "type": "string"
                  },
                  "evidence_gap": {
                    "type": "string"
                  }
                },
                "required": ["gap_type", "element", "missing_requirement", "evidence_gap"]
              }
            },
            "misinterpreted_evidence": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_type": {
                    "type": "string",
                    "enum": ["boundary", "sequence", "interface", "dependency"]
                  },
                  "element": {
                    "type": "string"
                  },
                  "missing_requirement": {
                    "type": "string"
                  },
                  "correct_interpretation": {
                    "type": "string"
                  }
                },
                "required": ["gap_type", "element", "missing_requirement", "correct_interpretation"]
              }
            }
          },
          "required": ["insufficient_evidence", "misinterpreted_evidence"]
        },
        "architectural_perspective": {
          "type": "object",
          "properties": {
            "component_cohesion": {
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
            "component_coupling": {
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
            "component_completeness": {
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
          "required": ["component_cohesion", "component_coupling", "component_completeness"]
        }
      },
      "required": ["analysis_accuracy", "evidence_quality", "architectural_perspective"]
    }
  },
  "required": ["reflection_results"]
}

# Structural Component Analysis Revision
structural_component_analysis_revision_prompt = """
# Insect Agent Revision Prompt

You are the Insect Agent processing reflection results to implement self-corrections to your initial structural component analysis. Your role is to systematically address identified issues from the reflection phase, refining your analysis of structural component gaps.

## Core Responsibilities
1. Process reflection feedback on your initial gap analysis
2. Remove incorrectly identified gaps (false positives)
3. Add missing gaps that were overlooked
4. Strengthen evidence for legitimate gaps
5. Correct misinterpretations of component architecture principles
6. Maintain a holistic component architecture perspective

## Input Format

You will receive two inputs:
1. Your original structural component analysis output
2. Reflection results in the following structure:
```json
{"reflection_results": {"analysis_accuracy": {"false_positives": [{"gap_type": "boundary|sequence|interface|dependency","element": "string","missing_requirement": "string","reasoning": "string"}],"missing_gaps": [{"gap_type": "boundary|sequence|interface|dependency","element": "string","missing_requirement": "string","evidence": ["strings"]}]},"evidence_quality": {"insufficient_evidence": [{"gap_type": "boundary|sequence|interface|dependency","element": "string","missing_requirement": "string","evidence_gap": "string"}],"misinterpreted_evidence": [{"gap_type": "boundary|sequence|interface|dependency","element": "string","missing_requirement": "string","correct_interpretation": "string"}]},"architectural_perspective": {"component_cohesion": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}],"component_coupling": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}],"component_completeness": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}]}}}
```

## Revision Process

1. Analyze reflection feedback methodically
2. Remove identified false positives
3. Add overlooked gaps with proper evidence
4. Strengthen evidence for existing gaps
5. Correct component architecture perspective issues
6. Validate all gaps against component architecture principles

## Output Format

Provide your revised analysis in the following JSON format:

```json
{"revision_metadata": {"processed_feedback": {"false_positives_removed": [{"gap_type": "boundary|sequence|interface|dependency","element": "string","missing_requirement": "string"}],"missing_gaps_added": [{"gap_type": "boundary|sequence|interface|dependency","element": "string","missing_requirement": "string"}],"evidence_strengthened": [{"gap_type": "boundary|sequence|interface|dependency","element": "string","missing_requirement": "string"}],"interpretations_corrected": [{"gap_type": "boundary|sequence|interface|dependency","element": "string","missing_requirement": "string"}]},"validation_steps": ["strings"]},"critical_structure_gaps": {"boundary_gaps": [{"component": "string","missing_requirement": "string","blocked_functionality": "string","evidence": ["strings"]}],"sequence_gaps": [{"sequence": "string","missing_requirement": "string","blocked_functionality": "string","evidence": ["strings"]}],"interface_gaps": [{"interface": "string","missing_requirement": "string","blocked_functionality": "string","evidence": ["strings"]}],"dependency_gaps": [{"dependency": "string","missing_requirement": "string","blocked_functionality": "string","evidence": ["strings"]}]}}
```

## Revision Guidelines

### Analysis Accuracy
- Remove gaps identified as false positives
- Add gaps identified as missing
- Refine gap descriptions to accurately represent issues

### Evidence Quality
- Add additional evidence where identified as insufficient
- Correct interpretations where evidence was misinterpreted
- Ensure evidence clearly supports gap identification

### Component Architecture Perspective
- Address component cohesion issues
- Improve component coupling evaluation
- Refine component completeness assessments
- Maintain focus on critical component architecture concerns

## Validation Checklist

Before finalizing your revised analysis:
1. Confirm all false positives have been removed
2. Verify all missing gaps have been added
3. Ensure all evidence issues have been addressed
4. Check that component architecture perspective issues are resolved
5. Validate that all gaps are genuine component architecture concerns
6. Confirm that evidence properly supports each gap
7. Ensure appropriate component architecture scope is maintained

## Self-Correction Principles

1. Focus on component integrity and boundaries over implementation details
2. Prioritize system component coherence and integration
3. Distinguish between critical and minor component architecture issues
4. Ensure gaps are traced to appropriate component architecture principles
5. Maintain balance between identifying issues and suggesting solutions
6. Consider the overall impact on system architecture
7. Align with established component architecture patterns and best practices
"""

structural_component_analysis_revision_schema = {
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
                  "gap_type": {
                    "type": "string",
                    "enum": ["boundary", "sequence", "interface", "dependency"]
                  },
                  "element": {
                    "type": "string"
                  },
                  "missing_requirement": {
                    "type": "string"
                  }
                },
                "required": ["gap_type", "element", "missing_requirement"]
              }
            },
            "missing_gaps_added": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_type": {
                    "type": "string",
                    "enum": ["boundary", "sequence", "interface", "dependency"]
                  },
                  "element": {
                    "type": "string"
                  },
                  "missing_requirement": {
                    "type": "string"
                  }
                },
                "required": ["gap_type", "element", "missing_requirement"]
              }
            },
            "evidence_strengthened": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_type": {
                    "type": "string",
                    "enum": ["boundary", "sequence", "interface", "dependency"]
                  },
                  "element": {
                    "type": "string"
                  },
                  "missing_requirement": {
                    "type": "string"
                  }
                },
                "required": ["gap_type", "element", "missing_requirement"]
              }
            },
            "interpretations_corrected": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_type": {
                    "type": "string",
                    "enum": ["boundary", "sequence", "interface", "dependency"]
                  },
                  "element": {
                    "type": "string"
                  },
                  "missing_requirement": {
                    "type": "string"
                  }
                },
                "required": ["gap_type", "element", "missing_requirement"]
              }
            }
          },
          "required": [
            "false_positives_removed",
            "missing_gaps_added",
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
    "critical_structure_gaps": {
      "type": "object",
      "properties": {
        "boundary_gaps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "component": {
                "type": "string"
              },
              "missing_requirement": {
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
              }
            },
            "required": ["component", "missing_requirement", "blocked_functionality", "evidence"]
          }
        },
        "sequence_gaps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "sequence": {
                "type": "string"
              },
              "missing_requirement": {
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
              }
            },
            "required": ["sequence", "missing_requirement", "blocked_functionality", "evidence"]
          }
        },
        "interface_gaps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "interface": {
                "type": "string"
              },
              "missing_requirement": {
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
              }
            },
            "required": ["interface", "missing_requirement", "blocked_functionality", "evidence"]
          }
        },
        "dependency_gaps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "dependency": {
                "type": "string"
              },
              "missing_requirement": {
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
              }
            },
            "required": ["dependency", "missing_requirement", "blocked_functionality", "evidence"]
          }
        }
      },
      "required": [
        "boundary_gaps",
        "sequence_gaps",
        "interface_gaps",
        "dependency_gaps"
      ]
    }
  },
  "required": ["revision_metadata", "critical_structure_gaps"]
}