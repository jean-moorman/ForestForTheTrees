#Mycelial Agent has three prompts: 
# 1. the Phase One Data Flow Verification Prompt which is used at the end of phase one to identify data flow misalignments across foundational guidelines
# 2. the Phase Two Data Flow Verification Prompt which is used at the end of phase two component creation loops to identify data flow misalignments across component implementations
# 3. the Phase Three Data Flow Verification Prompt which is used at the end of phase three feature creation loops to identify data flow misalignments across feature sets

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

# phase_two_data_flow_verification_schema = {
#   "type": "object",
#   "properties": {
#     "component_flow_conflicts": {
#       "type": "object",
#       "properties": {
#         "interface_conflicts": {
#           "type": "array",
#           "items": {
#             "type": "object",
#             "properties": {
#               "component": {
#                 "type": "string",
#                 "minLength": 1
#               },
#               "interface": {
#                 "type": "string",
#                 "minLength": 1
#               },
#               "affected_flow": {
#                 "type": "string",
#                 "minLength": 1
#               },
#               "compromise": {
#                 "type": "string",
#                 "minLength": 1
#               },
#               "evidence": {
#                 "type": "array",
#                 "items": {
#                   "type": "string"
#                 },
#                 "minItems": 1
#               }
#             },
#             "required": [
#               "component",
#               "interface",
#               "affected_flow",
#               "compromise",
#               "evidence"
#             ]
#           }
#         },
#         "dependency_conflicts": {
#           "type": "array",
#           "items": {
#             "type": "object",
#             "properties": {
#               "source_component": {
#                 "type": "string",
#                 "minLength": 1
#               },
#               "target_component": {
#                 "type": "string",
#                 "minLength": 1
#               },
#               "affected_flow": {
#                 "type": "string",
#                 "minLength": 1
#               },
#               "compromise": {
#                 "type": "string",
#                 "minLength": 1
#               },
#               "evidence": {
#                 "type": "array",
#                 "items": {
#                   "type": "string"
#                 },
#                 "minItems": 1
#               }
#             },
#             "required": [
#               "source_component",
#               "target_component",
#               "affected_flow",
#               "compromise",
#               "evidence"
#             ]
#           }
#         },
#         "implementation_conflicts": {
#           "type": "array",
#           "items": {
#             "type": "object",
#             "properties": {
#               "component": {
#                 "type": "string",
#                 "minLength": 1
#               },
#               "implementation_detail": {
#                 "type": "string",
#                 "minLength": 1
#               },
#               "affected_flow": {
#                 "type": "string",
#                 "minLength": 1
#               },
#               "compromise": {
#                 "type": "string",
#                 "minLength": 1
#               },
#               "evidence": {
#                 "type": "array",
#                 "items": {
#                   "type": "string"
#                 },
#                 "minItems": 1
#               }
#             },
#             "required": [
#               "component",
#               "implementation_detail",
#               "affected_flow",
#               "compromise",
#               "evidence"
#             ]
#           }
#         }
#       },
#       "required": [
#         "interface_conflicts",
#         "dependency_conflicts",
#         "implementation_conflicts"
#       ]
#     }
#   },
#   "required": ["component_flow_conflicts"]
# }

# phase_three_data_flow_verification_schema = {
#   "type": "object",
#   "properties": {
#     "feature_flow_conflicts": {
#       "type": "object",
#       "properties": {
#         "feature_interface_conflicts": {
#           "type": "array",
#           "items": {
#             "type": "object",
#             "properties": {
#               "feature": {
#                 "type": "string",
#                 "minLength": 1
#               },
#               "interface": {
#                 "type": "string",
#                 "minLength": 1
#               },
#               "affected_flow": {
#                 "type": "string",
#                 "minLength": 1
#               },
#               "user_impact": {
#                 "type": "string",
#                 "minLength": 1
#               },
#               "evidence": {
#                 "type": "array",
#                 "items": {
#                   "type": "string"
#                 },
#                 "minItems": 1
#               }
#             },
#             "required": [
#               "feature",
#               "interface",
#               "affected_flow",
#               "user_impact",
#               "evidence"
#             ]
#           }
#         },
#         "feature_interaction_conflicts": {
#           "type": "array",
#           "items": {
#             "type": "object",
#             "properties": {
#               "source_feature": {
#                 "type": "string",
#                 "minLength": 1
#               },
#               "target_feature": {
#                 "type": "string",
#                 "minLength": 1
#               },
#               "affected_flow": {
#                 "type": "string",
#                 "minLength": 1
#               },
#               "user_impact": {
#                 "type": "string",
#                 "minLength": 1
#               },
#               "evidence": {
#                 "type": "array",
#                 "items": {
#                   "type": "string"
#                 },
#                 "minItems": 1
#               }
#             },
#             "required": [
#               "source_feature",
#               "target_feature",
#               "affected_flow",
#               "user_impact",
#               "evidence"
#             ]
#           }
#         },
#         "data_integrity_conflicts": {
#           "type": "array",
#           "items": {
#             "type": "object",
#             "properties": {
#               "feature_set": {
#                 "type": "string",
#                 "minLength": 1
#               },
#               "data_flow": {
#                 "type": "string",
#                 "minLength": 1
#               },
#               "integrity_issue": {
#                 "type": "string",
#                 "minLength": 1
#               },
#               "user_impact": {
#                 "type": "string",
#                 "minLength": 1
#               },
#               "evidence": {
#                 "type": "array",
#                 "items": {
#                   "type": "string"
#                 },
#                 "minItems": 1
#               }
#             },
#             "required": [
#               "feature_set",
#               "data_flow",
#               "integrity_issue",
#               "user_impact",
#               "evidence"
#             ]
#           }
#         }
#       },
#       "required": [
#         "feature_interface_conflicts",
#         "feature_interaction_conflicts",
#         "data_integrity_conflicts"
#       ]
#     }
#   },
#   "required": ["feature_flow_conflicts"]
# }