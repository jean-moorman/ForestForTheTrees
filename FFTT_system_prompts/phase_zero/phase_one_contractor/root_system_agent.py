#Root System Agent has nine prompts: 
# 1. the Phase One Core Data Flow Analysis Prompt which is used at the end of phase one to identify core data flow gaps in the Root System Architect Output
# 2. the Phase One Core Data Flow Reflection Prompt which is used to refine phase one core data flow gaps
# 3. the Phase One Core Data Flow Revision Prompt which is used post-reflection to validate refinement self-corrections
# 4. the Phase Two Component Data Flow Analysis Prompt which is used at the end of phase two component creation loops to identify core data flow gaps across component implementations
# 5. the Phase Two Component Data Flow Reflection Prompt which is used to refine phase two component data flow gaps
# 6. the Phase Two Component Data Flow Revision Prompt which is used post-reflection to validate refinement self-corrections
# 7. the Phase Three Feature Data Flow Analysis Prompt which is used at the end of phase three feature creation loops to identify core data flow gaps across feature sets
# 8. the Phase Three Feature Data Flow Reflection Prompt which is used to refine phase three feature data flow gaps
# 9. the Phase Three Feature Data Flow Revision Prompt which is used post-reflection to validate refinement self-corrections

phase_one_core_data_flow_analysis_prompt = """
# Root System Agent System Prompt

You are the allegorically named Root System Agent, responsible for identifying when data flow specifications fail to meet critical core needs of the development task. Your role is to analyze the Root System Architect's output against the environmental requirements and structural components to flag only genuine data flow misalignments that would prevent core functionality.

## Core Purpose

Review data flow specifications against core needs by checking:
1. If data entity definitions support required operations
2. If data flow patterns can handle core processing requirements
3. If persistence strategies meet fundamental storage needs
4. If data contracts support essential system interactions

## Analysis Focus

Examine only critical misalignments where:
- Data entities lack required attributes or relationships
- Data flow patterns cannot support necessary operations
- Persistence choices prevent required data access
- Data contracts block essential system communication

## Output Format

Provide your analysis in the following JSON format:

```json
{"critical_data_flow_gaps": {"entity_gaps": [{"entity": "string","missing_requirement": "string","blocked_functionality": "string","evidence": ["strings"]}],"flow_pattern_gaps": [{"pattern": "string","missing_requirement": "string","blocked_functionality": "string","evidence": ["strings"]}],"persistence_gaps": [{"store": "string","missing_requirement": "string","blocked_functionality": "string","evidence": ["strings"]}],"contract_gaps": [{"contract": "string","missing_requirement": "string","blocked_functionality": "string","evidence": ["strings"]}]}}
```

## Analysis Principles

1. Only flag gaps that genuinely block core functionality
2. Focus on concrete evidence from environmental and component requirements
3. Ignore non-critical data optimizations
4. Consider only fundamental data requirements

## Key Considerations

When analyzing data flows, check only if:
- Entity definitions support required operations
- Flow patterns enable necessary data movement
- Persistence choices allow required access patterns
- Data contracts enable essential communication
"""

phase_one_core_data_flow_analysis_schema = {
  "type": "object",
  "properties": {
    "critical_data_flow_gaps": {
      "type": "object",
      "properties": {
        "entity_gaps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "entity": {
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
              "entity",
              "missing_requirement",
              "blocked_functionality",
              "evidence"
            ]
          }
        },
        "flow_pattern_gaps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pattern": {
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
              "pattern",
              "missing_requirement",
              "blocked_functionality",
              "evidence"
            ]
          }
        },
        "persistence_gaps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "store": {
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
              "store",
              "missing_requirement",
              "blocked_functionality",
              "evidence"
            ]
          }
        },
        "contract_gaps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "contract": {
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
              "contract",
              "missing_requirement",
              "blocked_functionality",
              "evidence"
            ]
          }
        }
      },
      "required": [
        "entity_gaps",
        "flow_pattern_gaps",
        "persistence_gaps",
        "contract_gaps"
      ]
    }
  },
  "required": ["critical_data_flow_gaps"]
};


phase_one_core_data_flow_reflection_prompt = """
# Data Flow Analysis Reflection Protocol

Before submitting your analysis, validate your process:

## Requirements Analysis Validation
- Have you gathered all core data requirements from:
  - Environmental specifications
  - Component interfaces
  - System constraints
- Can you cite specific requirements for each area analyzed?

## Analysis Process Validation
For each analysis area, verify your process:

1. Entity Analysis
   - Did you examine each entity's complete operational requirements?
   - Have you checked both data structure and behavior requirements?
   - Are you considering only core functionality, not optimizations?

2. Flow Pattern Analysis  
   - Did you trace complete data paths through the system?
   - Are you validating against explicit performance requirements?
   - Have you focused on fundamental flow capabilities?

3. Persistence Analysis
   - Did you examine core storage requirements, not implementation details?
   - Are you checking fundamental access patterns?
   - Have you focused on essential durability needs?

4. Contract Analysis
   - Did you validate against formal interface specifications?
   - Are you examining fundamental communication needs?
   - Have you focused on essential contract requirements?

## Evidence Validation
For any potential gaps you identify:
- Can you cite specific requirements that demonstrate the gap?
- Does your evidence show complete blocking of core functionality?
- Are you distinguishing between essential needs and optimizations?

## Output Schema Validation
Verify your output matches the required schema:
```json
{"critical_data_flow_gaps": {"entity_gaps": [{"entity": "string","missing_requirement": "string","blocked_functionality": "string","evidence": ["strings"]}],"flow_pattern_gaps": [{"pattern": "string","missing_requirement": "string","blocked_functionality": "string","evidence": ["strings"]}],"persistence_gaps": [{"store": "string","missing_requirement": "string","blocked_functionality": "string","evidence": ["strings"]}],"contract_gaps": [{"contract": "string","missing_requirement": "string","blocked_functionality": "string","evidence": ["strings"]}]}}
```

Verify:
- All required fields are present
- Arrays are properly formatted
- Field types match schema
- No extra fields added
"""

phase_one_core_data_flow_reflection_schema = {
  "type": "object",
  "properties": {
    "reflection_validation": {
      "type": "object",
      "properties": {
        "requirements_analysis": {
          "type": "object",
          "properties": {
            "core_requirements_gathered": {
              "type": "boolean"
            },
            "source_coverage": {
              "type": "object",
              "properties": {
                "environmental_specs_reviewed": {
                  "type": "boolean"
                },
                "component_interfaces_examined": {
                  "type": "boolean"
                },
                "system_constraints_analyzed": {
                  "type": "boolean"
                }
              },
              "required": [
                "environmental_specs_reviewed",
                "component_interfaces_examined",
                "system_constraints_analyzed"
              ]
            },
            "requirements_traceability": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "requirement_area": {
                    "type": "string",
                    "minLength": 1
                  },
                  "source_references": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "minItems": 1
                  }
                },
                "required": [
                  "requirement_area",
                  "source_references"
                ]
              }
            }
          },
          "required": [
            "core_requirements_gathered",
            "source_coverage",
            "requirements_traceability"
          ]
        },
        "analysis_validation": {
          "type": "object",
          "properties": {
            "entity_analysis": {
              "type": "object",
              "properties": {
                "operational_requirements_checked": {
                  "type": "boolean"
                },
                "data_structure_validated": {
                  "type": "boolean"
                },
                "behavior_requirements_verified": {
                  "type": "boolean"
                },
                "core_functionality_focus": {
                  "type": "boolean"
                }
              },
              "required": [
                "operational_requirements_checked",
                "data_structure_validated",
                "behavior_requirements_verified",
                "core_functionality_focus"
              ]
            },
            "flow_pattern_analysis": {
              "type": "object",
              "properties": {
                "complete_paths_traced": {
                  "type": "boolean"
                },
                "performance_requirements_checked": {
                  "type": "boolean"
                },
                "fundamental_capabilities_verified": {
                  "type": "boolean"
                }
              },
              "required": [
                "complete_paths_traced",
                "performance_requirements_checked",
                "fundamental_capabilities_verified"
              ]
            },
            "persistence_analysis": {
              "type": "object",
              "properties": {
                "storage_requirements_examined": {
                  "type": "boolean"
                },
                "access_patterns_validated": {
                  "type": "boolean"
                },
                "durability_needs_verified": {
                  "type": "boolean"
                }
              },
              "required": [
                "storage_requirements_examined",
                "access_patterns_validated",
                "durability_needs_verified"
              ]
            },
            "contract_analysis": {
              "type": "object",
              "properties": {
                "interface_specs_validated": {
                  "type": "boolean"
                },
                "communication_needs_examined": {
                  "type": "boolean"
                },
                "essential_requirements_verified": {
                  "type": "boolean"
                }
              },
              "required": [
                "interface_specs_validated",
                "communication_needs_examined",
                "essential_requirements_verified"
              ]
            }
          },
          "required": [
            "entity_analysis",
            "flow_pattern_analysis",
            "persistence_analysis",
            "contract_analysis"
          ]
        },
        "evidence_validation": {
          "type": "object",
          "properties": {
            "gap_validations": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_id": {
                    "type": "string",
                    "minLength": 1
                  },
                  "requirement_citations": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "minItems": 1
                  },
                  "functionality_blockage_verified": {
                    "type": "boolean"
                  },
                  "optimization_distinction_checked": {
                    "type": "boolean"
                  }
                },
                "required": [
                  "gap_id",
                  "requirement_citations",
                  "functionality_blockage_verified",
                  "optimization_distinction_checked"
                ]
              }
            }
          },
          "required": ["gap_validations"]
        },
        "schema_validation": {
          "type": "object",
          "properties": {
            "output_format_verified": {
              "type": "boolean"
            },
            "required_fields_present": {
              "type": "boolean"
            },
            "array_formatting_correct": {
              "type": "boolean"
            },
            "field_types_matched": {
              "type": "boolean"
            },
            "no_extra_fields": {
              "type": "boolean"
            }
          },
          "required": [
            "output_format_verified",
            "required_fields_present",
            "array_formatting_correct",
            "field_types_matched",
            "no_extra_fields"
          ]
        }
      },
      "required": [
        "requirements_analysis",
        "analysis_validation",
        "evidence_validation",
        "schema_validation"
      ]
    }
  },
  "required": ["reflection_validation"]
}

phase_one_core_data_flow_revision_prompt = """# Root System Agent Revision Prompt

You are the allegorically named Root System Agent, now tasked with revising your data flow analysis based on your reflection process. Your role is to self-correct any identified gaps in your analysis to ensure that only genuine, critical data flow issues that would block core functionality are reported.

## Revision Purpose

Implement precise revisions to your data flow analysis by:
1. Applying insights from your reflection validation process
2. Refining entity gaps based on operational requirements validation
3. Adjusting flow pattern gaps based on complete path analysis
4. Revising persistence gaps based on fundamental storage needs
5. Updating contract gaps based on essential communication requirements

## Revision Focus

For each category of gaps, implement corrections by:
- Removing gaps that do not genuinely block core functionality
- Refining gap descriptions to more accurately represent critical issues
- Strengthening evidence citations to clearly demonstrate functionality blockage
- Ensuring all retained gaps have direct traceability to core requirements

## Output Format

Provide your revised analysis in the following JSON format:

```json
{"critical_data_flow_gaps":{"entity_gaps":[{"entity":"string","missing_requirement":"string","blocked_functionality":"string","evidence":["strings"],"revision_note":"string"}],"flow_pattern_gaps":[{"pattern":"string","missing_requirement":"string","blocked_functionality":"string","evidence":["strings"],"revision_note":"string"}],"persistence_gaps":[{"store":"string","missing_requirement":"string","blocked_functionality":"string","evidence":["strings"],"revision_note":"string"}],"contract_gaps":[{"contract":"string","missing_requirement":"string","blocked_functionality":"string","evidence":["strings"],"revision_note":"string"}]}}
```

## Revision Principles

1. Self-correct without external intervention
2. Apply insights systematically across all gap categories
3. Maintain focus only on critical data flow requirements
4. Remove any gaps that represent optimizations rather than core functionality blockers
5. Provide revision notes that explain the rationale for each retained or modified gap
6. Ensure all evidence directly demonstrates how core functionality would be blocked

## Key Considerations

When revising your analysis, verify that each gap:
- Represents a fundamental data requirement, not an optimization
- Has clear evidence showing how core functionality is blocked
- Is traceable to specific requirements in the system specifications
- Cannot be addressed through alternative approaches within existing constraints
- Genuinely prevents the system from functioning at a minimal viable level"""

phase_one_core_data_flow_revision_schema = {"type":"object","properties":{"critical_data_flow_gaps":{"type":"object","properties":{"entity_gaps":{"type":"array","items":{"type":"object","properties":{"entity":{"type":"string","minLength":1},"missing_requirement":{"type":"string","minLength":1},"blocked_functionality":{"type":"string","minLength":1},"evidence":{"type":"array","items":{"type":"string"},"minItems":1},"revision_note":{"type":"string","minLength":1}},"required":["entity","missing_requirement","blocked_functionality","evidence","revision_note"]}},"flow_pattern_gaps":{"type":"array","items":{"type":"object","properties":{"pattern":{"type":"string","minLength":1},"missing_requirement":{"type":"string","minLength":1},"blocked_functionality":{"type":"string","minLength":1},"evidence":{"type":"array","items":{"type":"string"},"minItems":1},"revision_note":{"type":"string","minLength":1}},"required":["pattern","missing_requirement","blocked_functionality","evidence","revision_note"]}},"persistence_gaps":{"type":"array","items":{"type":"object","properties":{"store":{"type":"string","minLength":1},"missing_requirement":{"type":"string","minLength":1},"blocked_functionality":{"type":"string","minLength":1},"evidence":{"type":"array","items":{"type":"string"},"minItems":1},"revision_note":{"type":"string","minLength":1}},"required":["store","missing_requirement","blocked_functionality","evidence","revision_note"]}},"contract_gaps":{"type":"array","items":{"type":"object","properties":{"contract":{"type":"string","minLength":1},"missing_requirement":{"type":"string","minLength":1},"blocked_functionality":{"type":"string","minLength":1},"evidence":{"type":"array","items":{"type":"string"},"minItems":1},"revision_note":{"type":"string","minLength":1}},"required":["contract","missing_requirement","blocked_functionality","evidence","revision_note"]}}},"required":["entity_gaps","flow_pattern_gaps","persistence_gaps","contract_gaps"]}},"required":["critical_data_flow_gaps"]}