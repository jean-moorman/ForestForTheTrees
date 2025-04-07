#Pollinator Agent has three prompts: 
# 1. the Phase One Structural Component Analysis Prompt which is used at the end of phase one to identify structural component optimizations on the Tree Placement Planner Agent's guidelines
# 2. the Phase Two Component Implementation Analysis Prompt which is used at the end of phase two component creation loops to identify optimizations across component implementations
# 3. the Phase Three Feature Analysis Prompt which is used at the end of phase three feature creation loops to identify optimizations across feature sets

phase_one_structural_component_analysis_prompt = """
# Pollinator Agent System Prompt

You are the allegorically named Pollinator Agent, responsible for identifying opportunities to optimize component structure through reuse and reduction of redundancy. Your role is to analyze the Tree Placement Planner's output to flag potential component optimizations that would meaningfully improve system architecture.

## Core Purpose

Review structural components to identify:
1. Components with overlapping functionality
2. Opportunities for component reuse
3. Patterns that suggest potential shared services
4. Redundant implementations of common functionality

## Analysis Focus

Examine only significant optimization opportunities where:
- Multiple components implement similar functionality
- Common patterns suggest reusable components
- Separate components could be unified into shared services
- Standard functionality could be abstracted into utilities

## Output Format

Provide your analysis in the following JSON format:

```json
{"component_optimization_opportunities": {"redundant_implementations": [{"pattern": "string","affected_components": ["strings"],"common_functionality": "string","optimization_approach": "string","evidence": ["strings"]}],"reuse_opportunities": [{"pattern": "string","applicable_components": ["strings"],"shared_functionality": "string","reuse_approach": "string","evidence": ["strings"]}],"service_consolidation": [{"pattern": "string","mergeable_components": ["strings"],"unified_service": "string","consolidation_approach": "string","evidence": ["strings"]}],"abstraction_opportunities": [{"pattern": "string","current_implementations": ["strings"],"proposed_utility": "string","abstraction_approach": "string","evidence": ["strings"]}]}}
```

## Analysis Principles

1. Only flag optimizations that provide clear value
2. Focus on patterns with concrete evidence
3. Identify reuse that simplifies architecture
4. Consider impact on component relationships

## Key Considerations

When analyzing components, check for:
- Similar functionality across components
- Repeated implementation patterns
- Common service requirements
- Standard utility functions
"""

phase_one_structural_component_analysis_schema = {
  "type": "object",
  "properties": {
    "component_optimization_opportunities": {
      "type": "object",
      "properties": {
        "redundant_implementations": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pattern": {
                "type": "string",
                "minLength": 1
              },
              "affected_components": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "minItems": 1
              },
              "common_functionality": {
                "type": "string",
                "minLength": 1
              },
              "optimization_approach": {
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
              "affected_components",
              "common_functionality",
              "optimization_approach",
              "evidence"
            ]
          }
        },
        "reuse_opportunities": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pattern": {
                "type": "string",
                "minLength": 1
              },
              "applicable_components": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "minItems": 1
              },
              "shared_functionality": {
                "type": "string",
                "minLength": 1
              },
              "reuse_approach": {
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
              "applicable_components",
              "shared_functionality",
              "reuse_approach",
              "evidence"
            ]
          }
        },
        "service_consolidation": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pattern": {
                "type": "string",
                "minLength": 1
              },
              "mergeable_components": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "minItems": 1
              },
              "unified_service": {
                "type": "string",
                "minLength": 1
              },
              "consolidation_approach": {
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
              "mergeable_components",
              "unified_service",
              "consolidation_approach",
              "evidence"
            ]
          }
        },
        "abstraction_opportunities": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pattern": {
                "type": "string",
                "minLength": 1
              },
              "current_implementations": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "minItems": 1
              },
              "proposed_utility": {
                "type": "string",
                "minLength": 1
              },
              "abstraction_approach": {
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
              "current_implementations",
              "proposed_utility",
              "abstraction_approach",
              "evidence"
            ]
          }
        }
      },
      "required": [
        "redundant_implementations",
        "reuse_opportunities",
        "service_consolidation",
        "abstraction_opportunities"
      ]
    }
  },
  "required": ["component_optimization_opportunities"]
}