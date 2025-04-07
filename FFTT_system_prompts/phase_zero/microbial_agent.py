#Microbial Agent (complementary to Soil Agent) has three prompts: 
# 1. the Phase One Core Requirements Verification Prompt which is used at the end of phase one to identify core requirement misalignments across foundational guidelines
# 2. the Phase Two Core Requirements Verification Prompt which is used at the end of phase two component creation loops to identify core requirement misalignments across component implementations
# 3. the Phase Three Core Requirements Verification Prompt which is used at the end of phase three feature creation loops to identify core requirement misalignments across feature sets

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