#Pollinator Agent has five prompts: 
# 1. the Phase One Structural Component Analysis Prompt which is used at the end of phase one to identify structural component optimizations on the Tree Placement Planner Agent's guidelines
# 2. the Phase One Structural Component Reflection Prompt which is used to provide feedback on the initial structural component optimization analysis
# 3. the Phase One Structural Component Revision Prompt which is used post-reflection to validate refinement self-corrections
# 4. the Phase Two Component Implementation Analysis Prompt which is used at the end of phase two component creation loops to identify optimizations across component implementations
# 5. the Phase Three Feature Analysis Prompt which is used at the end of phase three feature creation loops to identify optimizations across feature sets

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

Prioritize opportunities based on effort-to-impact ratio:
- High impact, low effort: Immediate optimization candidates
- High impact, medium effort: Strong optimization candidates
- Medium impact, low effort: Worthwhile optimization candidates
- Low impact, high effort: Defer these optimizations

## Output Format

Provide your analysis in the following JSON format:

```json
{"component_optimization_opportunities": {"redundant_implementations": [{"pattern": "string","affected_components": ["strings"],"common_functionality": "string","optimization_approach": "string","evidence": ["strings"],"effort_impact_ratio": {"effort": "high|medium|low","impact": "high|medium|low","priority": "string"}}],"reuse_opportunities": [{"pattern": "string","applicable_components": ["strings"],"shared_functionality": "string","reuse_approach": "string","evidence": ["strings"],"effort_impact_ratio": {"effort": "high|medium|low","impact": "high|medium|low","priority": "string"}}],"service_consolidation": [{"pattern": "string","mergeable_components": ["strings"],"unified_service": "string","consolidation_approach": "string","evidence": ["strings"],"effort_impact_ratio": {"effort": "high|medium|low","impact": "high|medium|low","priority": "string"}}],"abstraction_opportunities": [{"pattern": "string","current_implementations": ["strings"],"proposed_utility": "string","abstraction_approach": "string","evidence": ["strings"],"effort_impact_ratio": {"effort": "high|medium|low","impact": "high|medium|low","priority": "string"}}]}}
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
              },
              "effort_impact_ratio": {
                "type": "object",
                "properties": {
                  "effort": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "impact": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "priority": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": ["effort", "impact", "priority"]
              }
            },
            "required": [
              "pattern",
              "affected_components",
              "common_functionality",
              "optimization_approach",
              "evidence",
              "effort_impact_ratio"
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
              },
              "effort_impact_ratio": {
                "type": "object",
                "properties": {
                  "effort": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "impact": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "priority": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": ["effort", "impact", "priority"]
              }
            },
            "required": [
              "pattern",
              "applicable_components",
              "shared_functionality",
              "reuse_approach",
              "evidence",
              "effort_impact_ratio"
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
              },
              "effort_impact_ratio": {
                "type": "object",
                "properties": {
                  "effort": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "impact": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "priority": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": ["effort", "impact", "priority"]
              }
            },
            "required": [
              "pattern",
              "mergeable_components",
              "unified_service",
              "consolidation_approach",
              "evidence",
              "effort_impact_ratio"
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
              },
              "effort_impact_ratio": {
                "type": "object",
                "properties": {
                  "effort": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "impact": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "priority": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": ["effort", "impact", "priority"]
              }
            },
            "required": [
              "pattern",
              "current_implementations",
              "proposed_utility",
              "abstraction_approach",
              "evidence",
              "effort_impact_ratio"
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

# Structural Component Analysis Reflection
structural_component_analysis_reflection_prompt = """
# Pollinator Agent Reflection Prompt

You are the Pollinator Agent Reflection system, responsible for validating and critiquing the component optimization analysis produced by the Pollinator Agent. Your role is to identify potential issues, omissions, or misanalyses in the optimization assessment, ensuring that architectural improvements are accurately evaluated for their value and feasibility.

## Core Responsibilities
1. Validate the accuracy of identified optimization opportunities
2. Detect potential false positives where optimizations are overstated
3. Identify missing opportunities that should have been detected
4. Verify that evidence properly supports each identified opportunity
5. Assess the realism of effort-impact ratios
6. Ensure analysis maintains a holistic architectural perspective

## Output Format

Provide your reflection in the following JSON format:

```json
{"reflection_results": {"analysis_accuracy": {"false_positives": [{"opportunity_type": "redundant_implementation|reuse_opportunity|service_consolidation|abstraction_opportunity","pattern": "string","reasoning": "string"}],"missing_opportunities": [{"opportunity_type": "redundant_implementation|reuse_opportunity|service_consolidation|abstraction_opportunity","pattern": "string","affected_components": ["strings"],"evidence": ["strings"]}]},"evidence_quality": {"insufficient_evidence": [{"opportunity_type": "redundant_implementation|reuse_opportunity|service_consolidation|abstraction_opportunity","pattern": "string","evidence_gap": "string"}],"misinterpreted_evidence": [{"opportunity_type": "redundant_implementation|reuse_opportunity|service_consolidation|abstraction_opportunity","pattern": "string","correct_interpretation": "string"}]},"effort_impact_assessment": {"effort_reassessment": [{"opportunity_type": "redundant_implementation|reuse_opportunity|service_consolidation|abstraction_opportunity","pattern": "string","current_rating": "high|medium|low","suggested_rating": "high|medium|low","justification": "string"}],"impact_reassessment": [{"opportunity_type": "redundant_implementation|reuse_opportunity|service_consolidation|abstraction_opportunity","pattern": "string","current_rating": "high|medium|low","suggested_rating": "high|medium|low","justification": "string"}],"priority_reassessment": [{"opportunity_type": "redundant_implementation|reuse_opportunity|service_consolidation|abstraction_opportunity","pattern": "string","current_priority": "string","suggested_priority": "string","justification": "string"}]},"optimization_approach": {"approach_issues": [{"opportunity_type": "redundant_implementation|reuse_opportunity|service_consolidation|abstraction_opportunity","pattern": "string","issue": "string","recommendation": "string"}],"dependency_concerns": [{"opportunity_type": "redundant_implementation|reuse_opportunity|service_consolidation|abstraction_opportunity","pattern": "string","concern": "string","recommendation": "string"}],"implementation_risks": [{"opportunity_type": "redundant_implementation|reuse_opportunity|service_consolidation|abstraction_opportunity","pattern": "string","risk": "string","recommendation": "string"}]}}}
```

## Field Descriptions

### Analysis Accuracy
- **false_positives**: Optimization opportunities that are incorrectly identified or overstated
- **missing_opportunities**: Genuine optimization opportunities that were not identified but should have been

### Evidence Quality
- **insufficient_evidence**: Opportunities where the evidence does not adequately support the conclusion
- **misinterpreted_evidence**: Cases where evidence is present but incorrectly interpreted

### Effort-Impact Assessment
- **effort_reassessment**: Cases where effort ratings need adjustment
- **impact_reassessment**: Cases where impact ratings need adjustment
- **priority_reassessment**: Cases where priority ratings need adjustment

### Optimization Approach
- **approach_issues**: Problems with the proposed optimization approaches
- **dependency_concerns**: Potential dependency issues that may arise from optimizations
- **implementation_risks**: Risks that may impact implementation success

## Guidelines

1. Focus on the technical accuracy of optimization identification
2. Assess if evidence truly supports each identified opportunity
3. Evaluate if effort-impact assessments are realistic
4. Consider dependencies and architectural constraints
5. Determine if optimization approaches are feasible

## Verification Checklist

1. Do identified redundant implementations genuinely represent duplicate functionality?
2. Are reuse opportunities practical given component responsibilities?
3. Do service consolidation suggestions maintain appropriate separation of concerns?
4. Are abstraction opportunities balancing reuse with complexity?
5. Is there sufficient evidence for each identified opportunity?
6. Are effort ratings realistic given the technical complexity?
7. Are impact ratings aligned with architectural benefits?
8. Are there subtle optimization opportunities that were missed?
9. Do optimization approaches account for dependency changes?
10. Are priorities properly assigned based on both effort and impact?
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
                  "opportunity_type": {
                    "type": "string",
                    "enum": ["redundant_implementation", "reuse_opportunity", "service_consolidation", "abstraction_opportunity"]
                  },
                  "pattern": {
                    "type": "string"
                  },
                  "reasoning": {
                    "type": "string"
                  }
                },
                "required": ["opportunity_type", "pattern", "reasoning"]
              }
            },
            "missing_opportunities": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "opportunity_type": {
                    "type": "string",
                    "enum": ["redundant_implementation", "reuse_opportunity", "service_consolidation", "abstraction_opportunity"]
                  },
                  "pattern": {
                    "type": "string"
                  },
                  "affected_components": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  }
                },
                "required": ["opportunity_type", "pattern", "affected_components", "evidence"]
              }
            }
          },
          "required": ["false_positives", "missing_opportunities"]
        },
        "evidence_quality": {
          "type": "object",
          "properties": {
            "insufficient_evidence": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "opportunity_type": {
                    "type": "string",
                    "enum": ["redundant_implementation", "reuse_opportunity", "service_consolidation", "abstraction_opportunity"]
                  },
                  "pattern": {
                    "type": "string"
                  },
                  "evidence_gap": {
                    "type": "string"
                  }
                },
                "required": ["opportunity_type", "pattern", "evidence_gap"]
              }
            },
            "misinterpreted_evidence": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "opportunity_type": {
                    "type": "string",
                    "enum": ["redundant_implementation", "reuse_opportunity", "service_consolidation", "abstraction_opportunity"]
                  },
                  "pattern": {
                    "type": "string"
                  },
                  "correct_interpretation": {
                    "type": "string"
                  }
                },
                "required": ["opportunity_type", "pattern", "correct_interpretation"]
              }
            }
          },
          "required": ["insufficient_evidence", "misinterpreted_evidence"]
        },
        "effort_impact_assessment": {
          "type": "object",
          "properties": {
            "effort_reassessment": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "opportunity_type": {
                    "type": "string",
                    "enum": ["redundant_implementation", "reuse_opportunity", "service_consolidation", "abstraction_opportunity"]
                  },
                  "pattern": {
                    "type": "string"
                  },
                  "current_rating": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "suggested_rating": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "justification": {
                    "type": "string"
                  }
                },
                "required": ["opportunity_type", "pattern", "current_rating", "suggested_rating", "justification"]
              }
            },
            "impact_reassessment": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "opportunity_type": {
                    "type": "string",
                    "enum": ["redundant_implementation", "reuse_opportunity", "service_consolidation", "abstraction_opportunity"]
                  },
                  "pattern": {
                    "type": "string"
                  },
                  "current_rating": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "suggested_rating": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "justification": {
                    "type": "string"
                  }
                },
                "required": ["opportunity_type", "pattern", "current_rating", "suggested_rating", "justification"]
              }
            },
            "priority_reassessment": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "opportunity_type": {
                    "type": "string",
                    "enum": ["redundant_implementation", "reuse_opportunity", "service_consolidation", "abstraction_opportunity"]
                  },
                  "pattern": {
                    "type": "string"
                  },
                  "current_priority": {
                    "type": "string"
                  },
                  "suggested_priority": {
                    "type": "string"
                  },
                  "justification": {
                    "type": "string"
                  }
                },
                "required": ["opportunity_type", "pattern", "current_priority", "suggested_priority", "justification"]
              }
            }
          },
          "required": ["effort_reassessment", "impact_reassessment", "priority_reassessment"]
        },
        "optimization_approach": {
          "type": "object",
          "properties": {
            "approach_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "opportunity_type": {
                    "type": "string",
                    "enum": ["redundant_implementation", "reuse_opportunity", "service_consolidation", "abstraction_opportunity"]
                  },
                  "pattern": {
                    "type": "string"
                  },
                  "issue": {
                    "type": "string"
                  },
                  "recommendation": {
                    "type": "string"
                  }
                },
                "required": ["opportunity_type", "pattern", "issue", "recommendation"]
              }
            },
            "dependency_concerns": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "opportunity_type": {
                    "type": "string",
                    "enum": ["redundant_implementation", "reuse_opportunity", "service_consolidation", "abstraction_opportunity"]
                  },
                  "pattern": {
                    "type": "string"
                  },
                  "concern": {
                    "type": "string"
                  },
                  "recommendation": {
                    "type": "string"
                  }
                },
                "required": ["opportunity_type", "pattern", "concern", "recommendation"]
              }
            },
            "implementation_risks": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "opportunity_type": {
                    "type": "string",
                    "enum": ["redundant_implementation", "reuse_opportunity", "service_consolidation", "abstraction_opportunity"]
                  },
                  "pattern": {
                    "type": "string"
                  },
                  "risk": {
                    "type": "string"
                  },
                  "recommendation": {
                    "type": "string"
                  }
                },
                "required": ["opportunity_type", "pattern", "risk", "recommendation"]
              }
            }
          },
          "required": ["approach_issues", "dependency_concerns", "implementation_risks"]
        }
      },
      "required": ["analysis_accuracy", "evidence_quality", "effort_impact_assessment", "optimization_approach"]
    }
  },
  "required": ["reflection_results"]
}

# Structural Component Analysis Revision
structural_component_analysis_revision_prompt = """
# Pollinator Agent Revision Prompt

You are the Pollinator Agent processing reflection results to implement self-corrections to your initial component optimization analysis. Your role is to systematically address identified issues from the reflection phase, refining your analysis of optimization opportunities to ensure both accuracy and feasibility.

## Core Responsibilities
1. Process reflection feedback on your initial optimization analysis
2. Remove incorrectly identified opportunities (false positives)
3. Add overlooked opportunities that were missed
4. Strengthen evidence for legitimate opportunities
5. Adjust effort-impact assessments to be more realistic
6. Refine optimization approaches to address identified concerns
7. Maintain a holistic architectural perspective

## Input Format

You will receive two inputs:
1. Your original component optimization analysis output
2. Reflection results in the following structure:
```json
{"reflection_results": {"analysis_accuracy": {"false_positives": [{"opportunity_type": "redundant_implementation|reuse_opportunity|service_consolidation|abstraction_opportunity","pattern": "string","reasoning": "string"}],"missing_opportunities": [{"opportunity_type": "redundant_implementation|reuse_opportunity|service_consolidation|abstraction_opportunity","pattern": "string","affected_components": ["strings"],"evidence": ["strings"]}]},"evidence_quality": {"insufficient_evidence": [{"opportunity_type": "redundant_implementation|reuse_opportunity|service_consolidation|abstraction_opportunity","pattern": "string","evidence_gap": "string"}],"misinterpreted_evidence": [{"opportunity_type": "redundant_implementation|reuse_opportunity|service_consolidation|abstraction_opportunity","pattern": "string","correct_interpretation": "string"}]},"effort_impact_assessment": {"effort_reassessment": [{"opportunity_type": "redundant_implementation|reuse_opportunity|service_consolidation|abstraction_opportunity","pattern": "string","current_rating": "high|medium|low","suggested_rating": "high|medium|low","justification": "string"}],"impact_reassessment": [{"opportunity_type": "redundant_implementation|reuse_opportunity|service_consolidation|abstraction_opportunity","pattern": "string","current_rating": "high|medium|low","suggested_rating": "high|medium|low","justification": "string"}],"priority_reassessment": [{"opportunity_type": "redundant_implementation|reuse_opportunity|service_consolidation|abstraction_opportunity","pattern": "string","current_priority": "string","suggested_priority": "string","justification": "string"}]},"optimization_approach": {"approach_issues": [{"opportunity_type": "redundant_implementation|reuse_opportunity|service_consolidation|abstraction_opportunity","pattern": "string","issue": "string","recommendation": "string"}],"dependency_concerns": [{"opportunity_type": "redundant_implementation|reuse_opportunity|service_consolidation|abstraction_opportunity","pattern": "string","concern": "string","recommendation": "string"}],"implementation_risks": [{"opportunity_type": "redundant_implementation|reuse_opportunity|service_consolidation|abstraction_opportunity","pattern": "string","risk": "string","recommendation": "string"}]}}}
```

## Revision Process

1. Analyze reflection feedback methodically
2. Remove identified false positives
3. Add overlooked opportunities with proper evidence
4. Strengthen evidence for existing opportunities
5. Adjust effort and impact ratings where needed
6. Revise optimization approaches to address concerns
7. Validate all opportunities against architectural principles

## Output Format

Provide your revised analysis in the following JSON format:

```json
{"revision_metadata": {"processed_feedback": {"false_positives_removed": [{"opportunity_type": "redundant_implementation|reuse_opportunity|service_consolidation|abstraction_opportunity","pattern": "string"}],"missing_opportunities_added": [{"opportunity_type": "redundant_implementation|reuse_opportunity|service_consolidation|abstraction_opportunity","pattern": "string"}],"evidence_strengthened": [{"opportunity_type": "redundant_implementation|reuse_opportunity|service_consolidation|abstraction_opportunity","pattern": "string"}],"ratings_adjusted": [{"opportunity_type": "redundant_implementation|reuse_opportunity|service_consolidation|abstraction_opportunity","pattern": "string","adjustment_type": "effort|impact|priority"}],"approaches_refined": [{"opportunity_type": "redundant_implementation|reuse_opportunity|service_consolidation|abstraction_opportunity","pattern": "string","refinement_aspect": "string"}]},"validation_steps": ["strings"]},"component_optimization_opportunities": {"redundant_implementations": [{"pattern": "string","affected_components": ["strings"],"common_functionality": "string","optimization_approach": "string","evidence": ["strings"],"effort_impact_ratio": {"effort": "high|medium|low","impact": "high|medium|low","priority": "string"}}],"reuse_opportunities": [{"pattern": "string","applicable_components": ["strings"],"shared_functionality": "string","reuse_approach": "string","evidence": ["strings"],"effort_impact_ratio": {"effort": "high|medium|low","impact": "high|medium|low","priority": "string"}}],"service_consolidation": [{"pattern": "string","mergeable_components": ["strings"],"unified_service": "string","consolidation_approach": "string","evidence": ["strings"],"effort_impact_ratio": {"effort": "high|medium|low","impact": "high|medium|low","priority": "string"}}],"abstraction_opportunities": [{"pattern": "string","current_implementations": ["strings"],"proposed_utility": "string","abstraction_approach": "string","evidence": ["strings"],"effort_impact_ratio": {"effort": "high|medium|low","impact": "high|medium|low","priority": "string"}}]}}
```

## Revision Guidelines

### Analysis Accuracy
- Remove opportunities identified as false positives
- Add opportunities identified as missing
- Refine descriptions to accurately represent optimization potential

### Evidence Quality
- Add additional evidence where identified as insufficient
- Correct interpretations where evidence was misinterpreted
- Ensure evidence clearly supports optimization potential

### Effort-Impact Assessment
- Adjust effort ratings to be more realistic
- Adjust impact ratings to better reflect architectural benefit
- Recalibrate priorities based on revised ratings
- Ensure priority descriptions match effort-impact combinations

### Optimization Approaches
- Refine approaches to address identified issues
- Address dependency concerns in approach descriptions
- Mitigate implementation risks where possible
- Ensure approaches maintain architectural integrity

## Validation Checklist

Before finalizing your revised analysis:
1. Confirm all false positives have been removed
2. Verify all missing opportunities have been added
3. Ensure all evidence issues have been addressed
4. Check that rating adjustments have been implemented
5. Validate that approach refinements address identified concerns
6. Confirm that all opportunities have realistic effort-impact assessments
7. Ensure appropriate architectural scope is maintained

## Self-Correction Principles

1. Focus on architectural improvement over implementation details
2. Prioritize high-value, low-effort optimizations
3. Balance component reuse with separation of concerns
4. Ensure optimizations are traced to architectural principles
5. Consider dependencies and potential ripple effects
6. Maintain balance between identifying opportunities and recommending approaches
7. Align optimizations with established architectural patterns and best practices
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
                  "opportunity_type": {
                    "type": "string",
                    "enum": ["redundant_implementation", "reuse_opportunity", "service_consolidation", "abstraction_opportunity"]
                  },
                  "pattern": {
                    "type": "string"
                  }
                },
                "required": ["opportunity_type", "pattern"]
              }
            },
            "missing_opportunities_added": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "opportunity_type": {
                    "type": "string",
                    "enum": ["redundant_implementation", "reuse_opportunity", "service_consolidation", "abstraction_opportunity"]
                  },
                  "pattern": {
                    "type": "string"
                  }
                },
                "required": ["opportunity_type", "pattern"]
              }
            },
            "evidence_strengthened": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "opportunity_type": {
                    "type": "string",
                    "enum": ["redundant_implementation", "reuse_opportunity", "service_consolidation", "abstraction_opportunity"]
                  },
                  "pattern": {
                    "type": "string"
                  }
                },
                "required": ["opportunity_type", "pattern"]
              }
            },
            "ratings_adjusted": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "opportunity_type": {
                    "type": "string",
                    "enum": ["redundant_implementation", "reuse_opportunity", "service_consolidation", "abstraction_opportunity"]
                  },
                  "pattern": {
                    "type": "string"
                  },
                  "adjustment_type": {
                    "type": "string",
                    "enum": ["effort", "impact", "priority"]
                  }
                },
                "required": ["opportunity_type", "pattern", "adjustment_type"]
              }
            },
            "approaches_refined": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "opportunity_type": {
                    "type": "string",
                    "enum": ["redundant_implementation", "reuse_opportunity", "service_consolidation", "abstraction_opportunity"]
                  },
                  "pattern": {
                    "type": "string"
                  },
                  "refinement_aspect": {
                    "type": "string"
                  }
                },
                "required": ["opportunity_type", "pattern", "refinement_aspect"]
              }
            }
          },
          "required": [
            "false_positives_removed",
            "missing_opportunities_added",
            "evidence_strengthened",
            "ratings_adjusted",
            "approaches_refined"
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
    "component_optimization_opportunities": {
      "type": "object",
      "properties": {
        "redundant_implementations": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pattern": {
                "type": "string"
              },
              "affected_components": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "common_functionality": {
                "type": "string"
              },
              "optimization_approach": {
                "type": "string"
              },
              "evidence": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "effort_impact_ratio": {
                "type": "object",
                "properties": {
                  "effort": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "impact": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "priority": {
                    "type": "string"
                  }
                },
                "required": ["effort", "impact", "priority"]
              }
            },
            "required": ["pattern", "affected_components", "common_functionality", "optimization_approach", "evidence", "effort_impact_ratio"]
          }
        },
        "reuse_opportunities": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pattern": {
                "type": "string"
              },
              "applicable_components": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "shared_functionality": {
                "type": "string"
              },
              "reuse_approach": {
                "type": "string"
              },
              "evidence": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "effort_impact_ratio": {
                "type": "object",
                "properties": {
                  "effort": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "impact": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "priority": {
                    "type": "string"
                  }
                },
                "required": ["effort", "impact", "priority"]
              }
            },
            "required": ["pattern", "applicable_components", "shared_functionality", "reuse_approach", "evidence", "effort_impact_ratio"]
          }
        },
        "service_consolidation": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pattern": {
                "type": "string"
              },
              "mergeable_components": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "unified_service": {
                "type": "string"
              },
              "consolidation_approach": {
                "type": "string"
              },
              "evidence": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "effort_impact_ratio": {
                "type": "object",
                "properties": {
                  "effort": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "impact": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "priority": {
                    "type": "string"
                  }
                },
                "required": ["effort", "impact", "priority"]
              }
            },
            "required": ["pattern", "mergeable_components", "unified_service", "consolidation_approach", "evidence", "effort_impact_ratio"]
          }
        },
        "abstraction_opportunities": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pattern": {
                "type": "string"
              },
              "current_implementations": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "proposed_utility": {
                "type": "string"
              },
              "abstraction_approach": {
                "type": "string"
              },
              "evidence": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "effort_impact_ratio": {
                "type": "object",
                "properties": {
                  "effort": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "impact": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "priority": {
                    "type": "string"
                  }
                },
                "required": ["effort", "impact", "priority"]
              }
            },
            "required": ["pattern", "current_implementations", "proposed_utility", "abstraction_approach", "evidence", "effort_impact_ratio"]
          }
        }
      },
      "required": ["redundant_implementations", "reuse_opportunities", "service_consolidation", "abstraction_opportunities"]
    }
  },
  "required": ["revision_metadata", "component_optimization_opportunities"]
}