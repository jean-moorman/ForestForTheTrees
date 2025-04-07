#Bird Agent has three prompts: 
# 1. the Phase One Structural Component Verification Prompt which is used at the end of phase one to identify structural component misalignments across foundational guidelines
# 2. the Phase Two Structural Component Verification Prompt which is used at the end of phase two component creation loops to identify structural component misalignments across component implementations
# 3. the Phase Three Structural Component Verification Prompt which is used at the end of phase three feature creation loops to identify structural component misalignments across feature sets

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