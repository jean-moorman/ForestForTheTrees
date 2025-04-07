#Insect Agent has three prompts: 
# 1. the Phase One Structural Component Verification Prompt which is used at the end of phase one to identify structural component misalignments across foundational guidelines
# 2. the Phase Two Structural Component Verification Prompt which is used at the end of phase two component creation loops to identify structural component misalignments across component implementations
# 3. the Phase Three Structural Component Verification Prompt which is used at the end of phase three feature creation loops to identify structural component misalignments across feature sets

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