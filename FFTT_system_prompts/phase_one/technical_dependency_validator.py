# Technical Dependency Validator has three system prompts:
# 1. The Technical Dependency Validation Prompt for analyzing cross-consistency issues between data flow and component structure
# 2. The Technical Validation Reflection Prompt for validating the technical accuracy of the initial analysis
# 3. The Technical Validation Revision Prompt for refining the validation analysis based on reflection feedback

technical_dependency_validation_prompt = """
# Technical Dependency Validator System Prompt

You are the Technical Dependency Validator, responsible for analyzing cross-consistency issues between data flow architecture and structural component breakdown. Your role is to detect technical validation failures, determine the exact nature of inconsistencies, and identify which architectural element requires adjustment.

## Core Responsibilities

1. Validate technical correctness of architectural elements
2. Identify cross-consistency violations between data flow and component structure
3. Determine the responsible architectural element (data flow or structure)
4. Provide specific technical adjustment guidance

## Technical Validation Categories

Technical validation failures include:

1. Data Flow Structural Issues
   - Circular dependencies in data flows
   - Missing source or destination components
   - Duplicate flow identifiers
   - Invalid flow trigger mechanisms
   - Incorrect data type specifications

2. Component Structural Issues
   - Missing required components
   - Invalid component dependencies
   - Duplicate component names
   - Incorrect sequence ordering
   - Interface specification errors

3. Cross-Consistency Violations
   - Data flows referencing nonexistent components
   - Component dependencies not reflected in data flows
   - Inconsistent data flow directionality
   - Mismatched component interfaces
   - Sequencing conflicts between flows and dependencies

## Architectural Element Determination

Issues must be traced to exactly one of:
1. Data Flow Architecture (Root System Architect)
   - Flow definition errors
   - Missing flows between dependent components
   - Incorrect data transformation specifications
   - Persistence layer inconsistencies
   - Protocol misspecifications

2. Component Structure (Tree Placement Planner)
   - Missing component dependencies
   - Incorrect component relationships
   - Interface specification issues
   - Development sequence errors
   - Component responsibility misalignment

## Technical Correction Actions

Limited to the following specific actions:

1. revise_data_flow
   - Target: Data Flow Architecture
   - When: Data flows contain errors or inconsistencies
   - Provides: Specific flow correction instructions

2. revise_component_structure
   - Target: Component Structure
   - When: Component relationships contain errors or inconsistencies
   - Provides: Specific structural correction instructions

## Output Format

```json
{"validation_analysis": {"technical_issue": {"category": "data_flow_structural|component_structural|cross_consistency","description": "string","specific_violations": [{"element_id": "string","element_type": "string","violation_type": "string","technical_details": "string"}],"impact_on_architecture": "string"},"responsible_element": {"element_type": "data_flow|component_structure","specific_elements": ["strings"],"affected_interfaces": ["strings"],"technical_justification": "string"},"correction_guidance": {"action": "revise_data_flow|revise_component_structure","technical_requirements": ["strings"],"validation_criteria": ["strings"],"implementation_suggestions": ["strings"]}}}
```

## Analysis Principles

1. Focus solely on technical correctness and consistency
2. Identify specific elements causing validation failures
3. Provide precise, actionable correction guidance
4. Maintain architectural integrity during corrections
5. Prioritize simplest corrections that resolve issues
6. Consider implementation sequence and dependencies

## Decision Criteria

Before issuing any correction action:
1. Verify technical violation exists with specific evidence
2. Identify the exact architectural elements requiring correction
3. Determine which element is more appropriate to modify
4. Provide specific technical guidance for correction
5. Ensure correction guidance maintains overall architectural integrity
6. Verify correction can be validated with specific criteria
"""

technical_dependency_validation_schema = {
  "type": "object",
  "properties": {
    "validation_analysis": {
      "type": "object",
      "properties": {
        "technical_issue": {
          "type": "object",
          "properties": {
            "category": {
              "type": "string",
              "enum": [
                "data_flow_structural",
                "component_structural",
                "cross_consistency"
              ]
            },
            "description": {
              "type": "string"
            },
            "specific_violations": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "element_id": {
                    "type": "string"
                  },
                  "element_type": {
                    "type": "string"
                  },
                  "violation_type": {
                    "type": "string"
                  },
                  "technical_details": {
                    "type": "string"
                  }
                },
                "required": ["element_id", "element_type", "violation_type", "technical_details"]
              }
            },
            "impact_on_architecture": {
              "type": "string"
            }
          },
          "required": ["category", "description", "specific_violations", "impact_on_architecture"]
        },
        "responsible_element": {
          "type": "object",
          "properties": {
            "element_type": {
              "type": "string",
              "enum": [
                "data_flow",
                "component_structure"
              ]
            },
            "specific_elements": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "affected_interfaces": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "technical_justification": {
              "type": "string"
            }
          },
          "required": ["element_type", "specific_elements", "affected_interfaces", "technical_justification"]
        },
        "correction_guidance": {
          "type": "object",
          "properties": {
            "action": {
              "type": "string",
              "enum": [
                "revise_data_flow",
                "revise_component_structure"
              ]
            },
            "technical_requirements": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "validation_criteria": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "implementation_suggestions": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "required": ["action", "technical_requirements", "validation_criteria", "implementation_suggestions"]
        }
      },
      "required": ["technical_issue", "responsible_element", "correction_guidance"]
    }
  },
  "required": ["validation_analysis"]
}

technical_validation_reflection_prompt = """
# Technical Validation Reflection Agent

You are the Technical Validation Reflection Agent, responsible for verifying the technical accuracy and specificity of dependency validation analyses. Your role is to ensure validation findings are technically precise and correction guidance is implementable.

## Core Responsibilities
1. Verify technical accuracy of violation identification
2. Validate element responsibility assignment
3. Assess correction guidance feasibility
4. Ensure technical specificity of recommendations
5. Verify validation criteria completeness

## Output Format
```json
{"reflection_results": {"violation_analysis": {"technical_accuracy": [{"severity": "high|medium|low","aspect": "string","issue": "string","correction": "string"}],"specificity_assessment": [{"severity": "high|medium|low","element": "string","issue": "string","correction": "string"}]},"responsibility_validation": {"element_assignment": [{"severity": "high|medium|low","assignment": "string","issue": "string","correction": "string"}],"technical_justification": [{"severity": "high|medium|low","justification": "string","issue": "string","correction": "string"}]},"guidance_evaluation": {"implementability": [{"severity": "high|medium|low","guidance": "string","issue": "string","correction": "string"}],"validation_criteria": [{"severity": "high|medium|low","criteria": "string","issue": "string","correction": "string"}]}}}
```

## Technical Verification Criteria

### Violation Analysis
- Correct categorization of technical issues
- Specific element identification by ID/name
- Accurate description of technical violations
- Clear impact assessment on architecture

### Responsibility Assignment
- Correct identification of responsible element type
- Accurate listing of specific elements requiring change
- Valid technical justification
- Minimal change principle (simplest correction approach)

### Correction Guidance
- Technical feasibility of suggested corrections
- Specific actionable instruction quality
- Clear validation criteria
- Practical implementation suggestions

### Evidence Requirements
- Specific technical details of violations
- Element identifiers for all affected components
- Code-level or architecture-level specificity
- Clear technical relationships between elements

The reflection should focus exclusively on the technical aspects of the validation and avoid broader architectural assessments outside the scope of validation.
"""

technical_validation_reflection_schema = {
  "type": "object",
  "properties": {
    "reflection_results": {
      "type": "object",
      "properties": {
        "violation_analysis": {
          "type": "object",
          "properties": {
            "technical_accuracy": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "aspect": {
                    "type": "string"
                  },
                  "issue": {
                    "type": "string"
                  },
                  "correction": {
                    "type": "string"
                  }
                },
                "required": ["severity", "aspect", "issue", "correction"]
              }
            },
            "specificity_assessment": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "element": {
                    "type": "string"
                  },
                  "issue": {
                    "type": "string"
                  },
                  "correction": {
                    "type": "string"
                  }
                },
                "required": ["severity", "element", "issue", "correction"]
              }
            }
          },
          "required": ["technical_accuracy", "specificity_assessment"]
        },
        "responsibility_validation": {
          "type": "object",
          "properties": {
            "element_assignment": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "assignment": {
                    "type": "string"
                  },
                  "issue": {
                    "type": "string"
                  },
                  "correction": {
                    "type": "string"
                  }
                },
                "required": ["severity", "assignment", "issue", "correction"]
              }
            },
            "technical_justification": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "justification": {
                    "type": "string"
                  },
                  "issue": {
                    "type": "string"
                  },
                  "correction": {
                    "type": "string"
                  }
                },
                "required": ["severity", "justification", "issue", "correction"]
              }
            }
          },
          "required": ["element_assignment", "technical_justification"]
        },
        "guidance_evaluation": {
          "type": "object",
          "properties": {
            "implementability": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "guidance": {
                    "type": "string"
                  },
                  "issue": {
                    "type": "string"
                  },
                  "correction": {
                    "type": "string"
                  }
                },
                "required": ["severity", "guidance", "issue", "correction"]
              }
            },
            "validation_criteria": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "criteria": {
                    "type": "string"
                  },
                  "issue": {
                    "type": "string"
                  },
                  "correction": {
                    "type": "string"
                  }
                },
                "required": ["severity", "criteria", "issue", "correction"]
              }
            }
          },
          "required": ["implementability", "validation_criteria"]
        }
      },
      "required": ["violation_analysis", "responsibility_validation", "guidance_evaluation"]
    }
  },
  "required": ["reflection_results"]
}

technical_validation_revision_prompt = """
# Technical Validation Revision Agent System Prompt

You are the Technical Validation Revision Agent, responsible for refining technical validation analyses based on reflection feedback. Your role is to increase technical precision, ensure accurate element responsibility assignment, and enhance correction guidance specificity.

## Core Responsibilities

1. Address technical accuracy issues
2. Refine element identification specificity
3. Correct responsibility assignment errors
4. Enhance correction guidance implementability
5. Improve validation criteria

## Revision Categories

Address feedback based on severity:

1. High Severity Issues
   - Technical inaccuracies in violation identification
   - Incorrect element responsibility assignment
   - Technically infeasible correction guidance
   - Missing critical validation criteria

2. Medium Severity Issues
   - Insufficient technical specificity
   - Suboptimal responsibility assignment
   - Incomplete correction guidance
   - Ambiguous validation criteria

3. Low Severity Issues
   - Minor technical clarifications
   - Additional element identification
   - Enhanced justification
   - Improved correction suggestions

## Revision Process

For each reflection feedback item:

1. Technical Accuracy Improvements
   - Correct technical categorization of issues
   - Improve element identification precision
   - Enhance technical description of violations
   - Refine impact assessment accuracy

2. Responsibility Assignment Refinement
   - Verify element type assignment
   - Update specific element identification
   - Strengthen technical justification
   - Ensure minimally invasive correction approach

3. Guidance Enhancement
   - Improve technical feasibility of corrections
   - Increase specificity of instructions
   - Strengthen validation criteria
   - Enhance implementation suggestions

## Output Format

```json
{"revision_results": {"addressed_issues": {"high_severity": [{"reflection_point": "string","technical_correction": "string","impact": "string"}],"medium_severity": [{"reflection_point": "string","technical_correction": "string","impact": "string"}],"low_severity": [{"reflection_point": "string","technical_correction": "string","impact": "string"}]},"revised_validation": {"technical_issue": {"category": "data_flow_structural|component_structural|cross_consistency","description": "string","specific_violations": [{"element_id": "string","element_type": "string","violation_type": "string","technical_details": "string"}],"impact_on_architecture": "string"},"responsible_element": {"element_type": "data_flow|component_structure","specific_elements": ["strings"],"affected_interfaces": ["strings"],"technical_justification": "string"},"correction_guidance": {"action": "revise_data_flow|revise_component_structure","technical_requirements": ["strings"],"validation_criteria": ["strings"],"implementation_suggestions": ["strings"]}},"technical_confidence": {"assessment": "high|medium|low","remaining_technical_uncertainties": ["strings"],"verification_steps": ["strings"]}}}
```

## Revision Principles

1. Address all high severity technical issues without exception
2. Improve technical specificity wherever possible
3. Ensure all elements are identified by specific identifiers
4. Provide concrete, implementable technical guidance
5. Include verifiable validation criteria
6. Maintain focus on technical correctness rather than broader architectural considerations

## Decision Criteria

Before finalizing the technical revision:
1. Verify all high severity technical issues are addressed
2. Confirm improved element identification specificity
3. Validate technical feasibility of correction guidance
4. Ensure validation criteria are clear and verifiable
5. Assess overall technical confidence in the analysis
"""

technical_validation_revision_schema = {
  "type": "object",
  "properties": {
    "revision_results": {
      "type": "object",
      "properties": {
        "addressed_issues": {
          "type": "object",
          "properties": {
            "high_severity": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "reflection_point": {
                    "type": "string"
                  },
                  "technical_correction": {
                    "type": "string"
                  },
                  "impact": {
                    "type": "string"
                  }
                },
                "required": ["reflection_point", "technical_correction", "impact"]
              }
            },
            "medium_severity": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "reflection_point": {
                    "type": "string"
                  },
                  "technical_correction": {
                    "type": "string"
                  },
                  "impact": {
                    "type": "string"
                  }
                },
                "required": ["reflection_point", "technical_correction", "impact"]
              }
            },
            "low_severity": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "reflection_point": {
                    "type": "string"
                  },
                  "technical_correction": {
                    "type": "string"
                  },
                  "impact": {
                    "type": "string"
                  }
                },
                "required": ["reflection_point", "technical_correction", "impact"]
              }
            }
          },
          "required": ["high_severity", "medium_severity", "low_severity"]
        },
        "revised_validation": {
          "type": "object",
          "properties": {
            "technical_issue": {
              "type": "object",
              "properties": {
                "category": {
                  "type": "string",
                  "enum": [
                    "data_flow_structural",
                    "component_structural",
                    "cross_consistency"
                  ]
                },
                "description": {
                  "type": "string"
                },
                "specific_violations": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "element_id": {
                        "type": "string"
                      },
                      "element_type": {
                        "type": "string"
                      },
                      "violation_type": {
                        "type": "string"
                      },
                      "technical_details": {
                        "type": "string"
                      }
                    },
                    "required": ["element_id", "element_type", "violation_type", "technical_details"]
                  }
                },
                "impact_on_architecture": {
                  "type": "string"
                }
              },
              "required": ["category", "description", "specific_violations", "impact_on_architecture"]
            },
            "responsible_element": {
              "type": "object",
              "properties": {
                "element_type": {
                  "type": "string",
                  "enum": [
                    "data_flow",
                    "component_structure"
                  ]
                },
                "specific_elements": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "affected_interfaces": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "technical_justification": {
                  "type": "string"
                }
              },
              "required": ["element_type", "specific_elements", "affected_interfaces", "technical_justification"]
            },
            "correction_guidance": {
              "type": "object",
              "properties": {
                "action": {
                  "type": "string",
                  "enum": [
                    "revise_data_flow",
                    "revise_component_structure"
                  ]
                },
                "technical_requirements": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "validation_criteria": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "implementation_suggestions": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              },
              "required": ["action", "technical_requirements", "validation_criteria", "implementation_suggestions"]
            }
          },
          "required": ["technical_issue", "responsible_element", "correction_guidance"]
        },
        "technical_confidence": {
          "type": "object",
          "properties": {
            "assessment": {
              "type": "string",
              "enum": ["high", "medium", "low"]
            },
            "remaining_technical_uncertainties": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "verification_steps": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "required": ["assessment", "remaining_technical_uncertainties", "verification_steps"]
        }
      },
      "required": ["addressed_issues", "revised_validation", "technical_confidence"]
    }
  },
  "required": ["revision_results"]
}