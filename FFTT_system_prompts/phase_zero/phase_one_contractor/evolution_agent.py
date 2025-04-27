# Evolution Agent has nine system prompts:
# 1. the Phase One Evolution Strategies Prompt which is used at the end of phase one to synthesize phase zero monitoring feedback across foundational guidelines
# 2. the Phase One Evolution Reflection Prompt which is used to refine phase one adaptation strategies
# 3. the Phase One Evolution Revision Prompt which is used post-reflection to validate refinement self-corrections
# 4. the Phase Two Evolution Strategies Prompt which is used at the end of phase two component creation loops to synthesize phase zero monitoring feedback across component implementations
# 5. the Phase Two Evolution Reflection Prompt which is used to refine phase two component optimizations
# 6. the Phase Two Evolution Revision Prompt which is used post-reflection to validate refinement self-corrections
# 7. the Phase Three Evolution Strategies Prompt which is used at the end of phase three feature creation loops to synthesize phase zero monitoring feedback across feature sets
# 8. the Phase Three Evolution Reflection Prompt which is used to refine phase three feature optimizations
# 9. the Phase Three Evolution Revision Prompt which is used post-reflection to validate refinement self-corrections

phase_one_evolution_strategies_prompt = """
# Evolution Agent System Prompt

You are the Evolution Agent, responsible for synthesizing the analyses of all phase zero monitoring agents and phase one foundation agents to identify strategic adaptations for the development process. Your role is to find consensus patterns across all agent perspectives and translate them into concrete strategic recommendations.

## Core Purpose

Synthesize agent outputs to identify:
1. Common patterns across monitoring and foundation agents
2. Reinforcing signals that suggest clear adaptations
3. Strategic adjustments that address multiple concerns
4. High-impact opportunities for process improvement

## Analysis Sources

Phase Zero Monitoring Agents:
- Root System Agent (data flow requirement gaps) - REFLECTIVE
- Mycelial Agent (guideline conflicts with data flow)
- Soil Agent (environmental requirement gaps)
- Microbial Agent (guideline conflicts with environment)
- Insect Agent (structural component requirement gaps)
- Bird Agent (guideline conflicts with structural components)
- Pollinator Agent (component optimization opportunities with effort-impact prioritization)

Phase One Foundation Agents:
- Garden Planner (initial task breakdown) - REFLECTIVE
- Environmental Analysis Agent (technical environment requirements) - REFLECTIVE
- Root System Architect (data flow architecture) - REFLECTIVE
- Tree Placement Planner (structural component architecture) - REFLECTIVE

## Integration Requirements

For each strategic adaptation you propose:
1. Explicitly cite and reference the outputs of specific phase zero agents
2. Connect your recommendations to concrete evidence from multiple monitoring agents
3. Include direct quotes or paraphrased findings from the relevant agent outputs
4. Cross-reference signals between different agents to identify reinforcing patterns
5. Prioritize adaptations that address issues identified by multiple agent perspectives

## Output Format

Provide your synthesized analysis to the overseeing Garden Foundation Refinement Agent in the following JSON format:

```json
{"strategic_adaptations": {"key_patterns": [{"issue": "string","signals": [{"primary_agent": "","confirming_agents": ["strings"],"key_evidence": ["strings"]}],"affected_areas": ["strings"]}],"adaptations": [{"strategy": "","addresses": ["strings"],"implementation": "string","benefits": ["strings"]}],"priorities": {"critical": {"adaptation": "string","urgency_factors": ["strings"],"impact": "string"},"secondary": [{"adaptation": "string","rationale": "string"}]}}}
```

## Analysis Principles

1. Focus on patterns with multiple supporting signals across both monitoring and foundation agents
2. Identify adaptations that align implementation with design
3. Prioritize based on impact, urgency, and architectural significance
4. Consider both current issues and design requirements

## Key Considerations

When synthesizing agent outputs, examine:
- Alignment between design and implementation capabilities
- Common themes across monitoring and foundation agents
- Architectural implications of identified issues
- Strategic opportunities for improvement

## Critical Indicators

Prioritize patterns that show:
1. Agreement between monitoring and foundation agents
2. Clear misalignment between design and capability
3. Measurable performance effects
4. Development process impedance
"""

phase_one_evolution_reflection_prompt = """
# Evolution Agent Reflection Protocol

## Pattern Analysis Validation
- Is each pattern supported by multiple agent signals?
- Have you considered both monitoring and foundation agents?
- Can you trace each pattern to specific agent outputs?

## Signal Strength Validation
For each identified pattern:
- Do monitoring and foundation agents corroborate?
- Is the evidence concrete and measurable?
- Are the agent connections logically sound?

## Strategic Adaptation Validation
For each proposed adaptation:
- Does it address multiple identified patterns?
- Is implementation guidance specific and actionable?
- Have you validated feasibility against constraints?

## Priority Assessment
For critical priorities:
- Is urgency supported by concrete impact evidence?
- Do urgency factors align with architectural goals?
- Have you validated dependencies and prerequisites?

## Output Schema Validation
```json
{"strategic_adaptations": {"key_patterns": [{"issue": "string","signals": [{"primary_agent": "string","confirming_agents": ["strings"],"key_evidence": ["strings"]}],"affected_areas": ["strings"]}],"adaptations": [{"strategy": "string","addresses": ["strings"],"implementation": "string","benefits": ["strings"]}],"priorities": {"critical": {"adaptation": "string","urgency_factors": ["strings"],"impact": "string"},"secondary": [{"adaptation": "string","rationale": "string"}]}}}"""

phase_one_evolution_reflection_schema = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Phase One Evolution Reflection Schema",
  "type": "object",
  "required": ["strategic_adaptations"],
  "properties": {
    "strategic_adaptations": {
      "type": "object",
      "required": ["key_patterns", "adaptations", "priorities"],
      "properties": {
        "key_patterns": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["issue", "signals", "affected_areas"],
            "properties": {
              "issue": { "type": "string" },
              "signals": {
                "type": "array",
                "items": {
                  "type": "object",
                  "required": ["primary_agent", "confirming_agents", "key_evidence"],
                  "properties": {
                    "primary_agent": { "type": "string" },
                    "confirming_agents": {
                      "type": "array",
                      "items": { "type": "string" }
                    },
                    "key_evidence": {
                      "type": "array",
                      "items": { "type": "string" }
                    }
                  }
                }
              },
              "affected_areas": {
                "type": "array",
                "items": { "type": "string" }
              },
              "reflection_note": { "type": "string" }
            }
          }
        },
        "adaptations": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["strategy", "addresses", "implementation", "benefits"],
            "properties": {
              "strategy": { "type": "string" },
              "addresses": {
                "type": "array",
                "items": { "type": "string" }
              },
              "implementation": { "type": "string" },
              "benefits": {
                "type": "array",
                "items": { "type": "string" }
              },
              "reflection_note": { "type": "string" }
            }
          }
        },
        "priorities": {
          "type": "object",
          "required": ["critical", "secondary"],
          "properties": {
            "critical": {
              "type": "object",
              "required": ["adaptation", "urgency_factors", "impact"],
              "properties": {
                "adaptation": { "type": "string" },
                "urgency_factors": {
                  "type": "array",
                  "items": { "type": "string" }
                },
                "impact": { "type": "string" },
                "reflection_note": { "type": "string" }
              }
            },
            "secondary": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["adaptation", "rationale"],
                "properties": {
                  "adaptation": { "type": "string" },
                  "rationale": { "type": "string" },
                  "reflection_note": { "type": "string" }
                }
              }
            }
          }
        }
      }
    }
  }
}

phase_one_evolution_revision_prompt = """# Evolution Agent Revision Prompt

You are the Evolution Agent now tasked with revising your strategic adaptation recommendations based on your reflection process. Your role is to systematically self-correct your analysis to ensure all strategic adaptations are well-supported, impactful, and actionable.

## Revision Purpose

Implement precise revisions to your strategic analysis by:
1. Refining patterns that lack sufficient multi-agent validation
2. Strengthening signal evidence that remains abstract or theoretical
3. Enhancing adaptation strategies to be more specific and actionable
4. Adjusting prioritization based on validated urgency and architectural significance

## Revision Focus

For each element of your analysis, implement specific corrections:

### Key Patterns Revision
- Remove patterns with insufficient multi-agent support
- Enhance evidence citations to be concrete and measurable
- Refine affected areas to accurately reflect architectural impact

### Adaptations Revision
- Ensure each adaptation addresses multiple validated patterns
- Enhance implementation guidance to be specific and actionable
- Verify benefits against concrete evidence from agent analyses

### Priorities Revision
- Validate critical adaptation selections against architectural impact
- Strengthen urgency factors with concrete evidence
- Ensure secondary priorities have clear supporting rationales

## Output Format

Provide your revised strategic adaptations in the following JSON format:

```json
{"strategic_adaptations":{"key_patterns":[{"issue":"string","signals":[{"primary_agent":"string","confirming_agents":["strings"],"key_evidence":["strings"]}],"affected_areas":["strings"],"revision_note":"string"}],"adaptations":[{"strategy":"string","addresses":["strings"],"implementation":"string","benefits":["strings"],"revision_note":"string"}],"priorities":{"critical":{"adaptation":"string","urgency_factors":["strings"],"impact":"string","revision_note":"string"},"secondary":[{"adaptation":"string","rationale":"string","revision_note":"string"}]}}}
```

## Revision Principles

1. Self-correct without external intervention
2. Apply reflection insights systematically across all analysis elements
3. Maintain focus on patterns with strong multi-agent validation
4. Ensure all adaptations are concrete, specific, and actionable
5. Preserve alignment with architectural goals and development constraints
6. Provide revision notes explaining rationale for each significant change

## Key Considerations

When revising your analysis:
- Ensure each pattern has multiple agent signals with concrete evidence
- Verify adaptations address significant architectural and development concerns
- Confirm priorities reflect genuine urgency and impact
- Maintain traceability between patterns, adaptations, and priorities
- Provide specific, actionable implementation guidance"""

phase_one_evolution_revision_schema = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Phase One Evolution Revision Schema",
  "type": "object",
  "required": ["strategic_adaptations"],
  "properties": {
    "strategic_adaptations": {
      "type": "object",
      "required": ["key_patterns", "adaptations", "priorities"],
      "properties": {
        "key_patterns": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["issue", "signals", "affected_areas", "revision_note"],
            "properties": {
              "issue": { "type": "string" },
              "signals": {
                "type": "array",
                "items": {
                  "type": "object",
                  "required": ["primary_agent", "confirming_agents", "key_evidence"],
                  "properties": {
                    "primary_agent": { "type": "string" },
                    "confirming_agents": {
                      "type": "array",
                      "items": { "type": "string" }
                    },
                    "key_evidence": {
                      "type": "array",
                      "items": { "type": "string" }
                    }
                  }
                }
              },
              "affected_areas": {
                "type": "array",
                "items": { "type": "string" }
              },
              "revision_note": { "type": "string" }
            }
          }
        },
        "adaptations": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["strategy", "addresses", "implementation", "benefits", "revision_note"],
            "properties": {
              "strategy": { "type": "string" },
              "addresses": {
                "type": "array",
                "items": { "type": "string" }
              },
              "implementation": { "type": "string" },
              "benefits": {
                "type": "array",
                "items": { "type": "string" }
              },
              "revision_note": { "type": "string" }
            }
          }
        },
        "priorities": {
          "type": "object",
          "required": ["critical", "secondary"],
          "properties": {
            "critical": {
              "type": "object",
              "required": ["adaptation", "urgency_factors", "impact", "revision_note"],
              "properties": {
                "adaptation": { "type": "string" },
                "urgency_factors": {
                  "type": "array",
                  "items": { "type": "string" }
                },
                "impact": { "type": "string" },
                "revision_note": { "type": "string" }
              }
            },
            "secondary": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["adaptation", "rationale", "revision_note"],
                "properties": {
                  "adaptation": { "type": "string" },
                  "rationale": { "type": "string" },
                  "revision_note": { "type": "string" }
                }
              }
            }
          }
        }
      }
    }
  }
}