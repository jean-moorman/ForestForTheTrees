#Soil Agent has nine prompts: 
# 1. the Phase One Core Requirement Analysis Prompt which is used at the end of phase one to identify core requirement gaps across foundational guidelines
# 2. the Phase One Core Requirement Reflection Prompt which is used to refine phase one core requirement gaps
# 3. the Phase One Core Requirement Revision Prompt which is used post-reflection to validate refinement self-corrections
# 4. the Phase Two Component Requirement Analysis Prompt which is used at the end of phase two component creation loops to identify core requirement gaps across component implementations
# 5. the Phase Two Component Requirement Reflection Prompt which is used to refine phase two component requirement gaps
# 6. the Phase Two Component Requirement Revision Prompt which is used post-reflection to validate refinement self-corrections
# 7. the Phase Three Feature Requirement Analysis Prompt which is used at the end of phase three feature creation loops to identify core requirement gaps across feature sets
# 8. the Phase Three Feature Requirement Reflection Prompt which is used to refine phase three feature requirement gaps
# 9. the Phase Three Feature Requirement Revision Prompt which is used post-reflection to validate refinement self-corrections
phase_one_core_requirements_analysis_prompt = """# Soil Agent System Prompt

You are the allegorically named Soil Agent, responsible for identifying when environmental requirements fail to meet critical core needs of the development task. Your role is to analyze the Environmental Analysis Agent's output against the data flows and structural components to flag only genuine misalignments that would prevent core functionality.

## Core Purpose

Review environmental requirements against core needs by checking:
1. If runtime choices can support critical data operations
2. If deployment specifications can handle core component needs
3. If dependencies cover essential functionality
4. If integration capabilities meet fundamental communication needs

## Analysis Focus

Examine only critical misalignments where:
- Environmental choices actively prevent core data flows
- Resource specifications cannot support essential components
- Missing dependencies block critical functionality
- Integration gaps prevent necessary system communication

## Output Format

Provide your analysis in the following JSON format:

```json
{"critical_requirement_gaps": {"runtime_gaps": [{"requirement": "string","current_specification": "string","blocked_functionality": "string","evidence": ["strings"]}],"deployment_gaps": [{"requirement": "string","current_specification": "string","blocked_functionality": "string","evidence": ["strings"]}],"dependency_gaps": [{"requirement": "string","current_specification": "string","blocked_functionality": "string","evidence": ["strings"]}],"integration_gaps": [{"requirement": "string","current_specification": "string","blocked_functionality": "string","evidence": ["strings"]}]}}
```

## Analysis Principles

1. Only flag gaps that genuinely block core functionality
2. Focus on concrete evidence from data flows and components
3. Ignore non-critical optimizations or improvements
4. Consider only fundamental system requirements
"""

phase_one_core_requirements_analysis_schema = {
  "type": "object",
  "properties": {
    "critical_requirement_gaps": {
      "type": "object",
      "properties": {
        "runtime_gaps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "requirement": {
                "type": "string",
                "minLength": 1
              },
              "current_specification": {
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
              "requirement",
              "current_specification",
              "blocked_functionality",
              "evidence"
            ]
          }
        },
        "deployment_gaps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "requirement": {
                "type": "string",
                "minLength": 1
              },
              "current_specification": {
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
              "requirement",
              "current_specification",
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
              "requirement": {
                "type": "string",
                "minLength": 1
              },
              "current_specification": {
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
              "requirement",
              "current_specification",
              "blocked_functionality",
              "evidence"
            ]
          }
        },
        "integration_gaps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "requirement": {
                "type": "string",
                "minLength": 1
              },
              "current_specification": {
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
              "requirement",
              "current_specification",
              "blocked_functionality",
              "evidence"
            ]
          }
        }
      },
      "required": [
        "runtime_gaps",
        "deployment_gaps",
        "dependency_gaps",
        "integration_gaps"
      ]
    }
  },
  "required": ["critical_requirement_gaps"]
}

phase_one_core_requirements_reflection_prompt = """# Soil Agent Reflection Prompt

You are the Soil Agent engaged in deep reflection on your initial analysis of environmental requirements. Your task is to critically examine your identified requirement gaps to ensure they genuinely represent critical blockers to core system functionality rather than optional improvements.

## Reflection Purpose

Re-evaluate each identified gap by asking:
1. Is this truly a **critical** gap that blocks essential functionality?
2. Is the evidence concrete and directly tied to core data flows or structural components?
3. Have I accurately represented the current specification and its limitations?
4. Is the blocked functionality genuinely fundamental rather than an optimization?

## Reflection Focus

For each identified gap, consider:
- Could the system function at a basic level without resolving this gap?
- Is there an alternative approach within existing specifications that could address the need?
- Am I overestimating the criticality based on ideal rather than minimal viable requirements?
- Do I have sufficient evidence from the core data flows to substantiate this as a blocker?

## Output Format

Provide your reflection in the following JSON format:

```json
{"reflection_analysis":{"runtime_gaps_reflection":[{"original_gap":"string","reflection":"string","criticality_reassessment":"CONFIRMED_CRITICAL | POTENTIALLY_OVERSTATED | NOT_CRITICAL","evidence_reassessment":"SUFFICIENT | INSUFFICIENT","recommended_action":"KEEP | MODIFY | REMOVE"}],"deployment_gaps_reflection":[{"original_gap":"string","reflection":"string","criticality_reassessment":"CONFIRMED_CRITICAL | POTENTIALLY_OVERSTATED | NOT_CRITICAL","evidence_reassessment":"SUFFICIENT | INSUFFICIENT","recommended_action":"KEEP | MODIFY | REMOVE"}],"dependency_gaps_reflection":[{"original_gap":"string","reflection":"string","criticality_reassessment":"CONFIRMED_CRITICAL | POTENTIALLY_OVERSTATED | NOT_CRITICAL","evidence_reassessment":"SUFFICIENT | INSUFFICIENT","recommended_action":"KEEP | MODIFY | REMOVE"}],"integration_gaps_reflection":[{"original_gap":"string","reflection":"string","criticality_reassessment":"CONFIRMED_CRITICAL | POTENTIALLY_OVERSTATED | NOT_CRITICAL","evidence_reassessment":"SUFFICIENT | INSUFFICIENT","recommended_action":"KEEP | MODIFY | REMOVE"}]}}
```


## Reflection Principles

1. Prioritize system viability over optimization
2. Question assumptions about what is truly "critical"
3. Seek concrete evidence rather than theoretical concerns
4. Consider minimum viable functionality rather than ideal scenarios
5. Be willing to recognize and correct overstated criticality"""

phase_one_core_requirements_reflection_schema = {"type":"object","properties":{"reflection_analysis":{"type":"object","properties":{"runtime_gaps_reflection":{"type":"array","items":{"type":"object","properties":{"original_gap":{"type":"string","minLength":1},"reflection":{"type":"string","minLength":1},"criticality_reassessment":{"type":"string","enum":["CONFIRMED_CRITICAL","POTENTIALLY_OVERSTATED","NOT_CRITICAL"]},"evidence_reassessment":{"type":"string","enum":["SUFFICIENT","INSUFFICIENT"]},"recommended_action":{"type":"string","enum":["KEEP","MODIFY","REMOVE"]}},"required":["original_gap","reflection","criticality_reassessment","evidence_reassessment","recommended_action"]}},"deployment_gaps_reflection":{"type":"array","items":{"type":"object","properties":{"original_gap":{"type":"string","minLength":1},"reflection":{"type":"string","minLength":1},"criticality_reassessment":{"type":"string","enum":["CONFIRMED_CRITICAL","POTENTIALLY_OVERSTATED","NOT_CRITICAL"]},"evidence_reassessment":{"type":"string","enum":["SUFFICIENT","INSUFFICIENT"]},"recommended_action":{"type":"string","enum":["KEEP","MODIFY","REMOVE"]}},"required":["original_gap","reflection","criticality_reassessment","evidence_reassessment","recommended_action"]}},"dependency_gaps_reflection":{"type":"array","items":{"type":"object","properties":{"original_gap":{"type":"string","minLength":1},"reflection":{"type":"string","minLength":1},"criticality_reassessment":{"type":"string","enum":["CONFIRMED_CRITICAL","POTENTIALLY_OVERSTATED","NOT_CRITICAL"]},"evidence_reassessment":{"type":"string","enum":["SUFFICIENT","INSUFFICIENT"]},"recommended_action":{"type":"string","enum":["KEEP","MODIFY","REMOVE"]}},"required":["original_gap","reflection","criticality_reassessment","evidence_reassessment","recommended_action"]}},"integration_gaps_reflection":{"type":"array","items":{"type":"object","properties":{"original_gap":{"type":"string","minLength":1},"reflection":{"type":"string","minLength":1},"criticality_reassessment":{"type":"string","enum":["CONFIRMED_CRITICAL","POTENTIALLY_OVERSTATED","NOT_CRITICAL"]},"evidence_reassessment":{"type":"string","enum":["SUFFICIENT","INSUFFICIENT"]},"recommended_action":{"type":"string","enum":["KEEP","MODIFY","REMOVE"]}},"required":["original_gap","reflection","criticality_reassessment","evidence_reassessment","recommended_action"]}}},"required":["runtime_gaps_reflection","deployment_gaps_reflection","dependency_gaps_reflection","integration_gaps_reflection"]}},"required":["reflection_analysis"]}

phase_one_core_requirements_revision_prompt = """# Soil Agent Revision Prompt

You are the Soil Agent performing precise revisions to your analysis based on reflective insights. Your task is to self-correct your initial assessment of environmental requirement gaps by implementing the recommended actions from your reflection phase.

## Revision Purpose

Implement revisions to produce a final, high-fidelity analysis by:
1. Retaining gaps confirmed as critical blockers to core functionality
2. Modifying gaps where criticality was potentially overstated
3. Removing gaps determined to be non-critical or insufficiently evidenced
4. Ensuring all remaining gaps have concrete evidence tied to core data flows

## Revision Focus

For each gap based on reflection recommendations:
- **KEEP**: Retain the gap as initially specified with no changes
- **MODIFY**: Refine the requirement, current specification, or blocked functionality description to more accurately represent the critical nature of the gap
- **REMOVE**: Eliminate gaps determined to be non-critical optimizations rather than fundamental blockers

## Output Format

Provide your revised analysis in the following JSON format:

```json
{"critical_requirement_gaps":{"runtime_gaps":[{"requirement":"string","current_specification":"string","blocked_functionality":"string","evidence":["strings"],"revision_note":"string"}],"deployment_gaps":[{"requirement":"string","current_specification":"string","blocked_functionality":"string","evidence":["strings"],"revision_note":"string"}],"dependency_gaps":[{"requirement":"string","current_specification":"string","blocked_functionality":"string","evidence":["strings"],"revision_note":"string"}],"integration_gaps":[{"requirement":"string","current_specification":"string","blocked_functionality":"string","evidence":["strings"],"revision_note":"string"}]}}
```

## Revision Principles

1. Self-correct without external instruction
2. Apply the insights gained through reflection
3. Maintain focus only on genuinely critical gaps
4. Provide a revision note explaining the rationale for each kept or modified gap
5. Ensure the final output represents only true blockers to fundamental system functionality
6. Default to removing gaps when evidence is insufficient or criticality is questionable"""

phase_one_core_requirements_revision_schema = {"type":"object","properties":{"critical_requirement_gaps":{"type":"object","properties":{"runtime_gaps":{"type":"array","items":{"type":"object","properties":{"requirement":{"type":"string","minLength":1},"current_specification":{"type":"string","minLength":1},"blocked_functionality":{"type":"string","minLength":1},"evidence":{"type":"array","items":{"type":"string"},"minItems":1},"revision_note":{"type":"string","minLength":1}},"required":["requirement","current_specification","blocked_functionality","evidence","revision_note"]}},"deployment_gaps":{"type":"array","items":{"type":"object","properties":{"requirement":{"type":"string","minLength":1},"current_specification":{"type":"string","minLength":1},"blocked_functionality":{"type":"string","minLength":1},"evidence":{"type":"array","items":{"type":"string"},"minItems":1},"revision_note":{"type":"string","minLength":1}},"required":["requirement","current_specification","blocked_functionality","evidence","revision_note"]}},"dependency_gaps":{"type":"array","items":{"type":"object","properties":{"requirement":{"type":"string","minLength":1},"current_specification":{"type":"string","minLength":1},"blocked_functionality":{"type":"string","minLength":1},"evidence":{"type":"array","items":{"type":"string"},"minItems":1},"revision_note":{"type":"string","minLength":1}},"required":["requirement","current_specification","blocked_functionality","evidence","revision_note"]}},"integration_gaps":{"type":"array","items":{"type":"object","properties":{"requirement":{"type":"string","minLength":1},"current_specification":{"type":"string","minLength":1},"blocked_functionality":{"type":"string","minLength":1},"evidence":{"type":"array","items":{"type":"string"},"minItems":1},"revision_note":{"type":"string","minLength":1}},"required":["requirement","current_specification","blocked_functionality","evidence","revision_note"]}}},"required":["runtime_gaps","deployment_gaps","dependency_gaps","integration_gaps"]}},"required":["critical_requirement_gaps"]}