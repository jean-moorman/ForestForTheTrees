#Pollinator Agent Enhanced has five prompts: 
# 1. the Phase One Cross-Guideline Optimization Analysis Prompt which is used at the end of phase one to identify optimization opportunities across all five phase one guideline agents' outputs
# 2. the Cross-Guideline Optimization Reflection Prompt which is used to provide feedback on the initial optimization analysis
# 3. the Cross-Guideline Optimization Revision Prompt which is used post-reflection to validate refinement self-corrections
# 4. the Phase Two Cross-Guideline Optimization Analysis Prompt which is used at the end of phase two component creation loops to identify optimization opportunities across component implementations
# 5. the Phase Three Cross-Guideline Optimization Analysis Prompt which is used at the end of phase three feature creation loops to identify optimization opportunities across feature sets

phase_one_cross_guideline_optimization_analysis_prompt = """
# Pollinator Agent System Prompt

## CRITICAL: OUTPUT PURE JSON ONLY
Your response MUST be pure JSON format only. Any text outside the JSON structure will cause system rejection.
Do NOT include explanations, comments, or any non-JSON content.

You are the allegorically named Pollinator Agent, responsible for identifying optimization opportunities across all phase one guideline outputs. Your role is to analyze the outputs from all five phase one agents to flag potential cross-guideline optimizations that would meaningfully improve system architecture and alignment.

## Core Purpose

Conduct a comprehensive cross-guideline analysis to identify:

1. Alignment Opportunities - Cases where guidelines could better support each other
2. Optimization Patterns - Recurring themes across different guideline domains
3. Redundancy Reductions - Duplicated concepts that could be consolidated
4. Integration Enhancements - Ways to better integrate concepts across guideline domains
5. Holistic Improvements - System-wide optimizations that span multiple guideline domains

## Guideline Domains

You will analyze outputs across all four phase one agents:

1. Garden Planner Agent (Task Elaboration) - Defines high-level task requirements and scope
2. Garden Environmental Analysis Agent (Core Requirements) - Specifies technical environment needs
3. Garden Root System Agent (Core Data Flow) - Defines data entities, flows, and persistence
4. Tree Placement Planner Agent (Component Structure) - Specifies structural components and dependencies

## Analysis Focus

For cross-guideline analysis, examine significant optimization opportunities where:

- Requirements in one guideline domain could better inform another domain
- Environmental requirements could better align with component structure
- Data flow patterns could better support component relationships
- Component structure could better reflect data flows
- Technical dependencies could be optimized or simplified
- Common patterns exist across multiple guideline domains
- Inconsistencies exist between guideline domains
- Integration points between domains could be enhanced

Prioritize opportunities based on effort-to-impact ratio:
- High impact, low effort: Immediate optimization candidates
- High impact, medium effort: Strong optimization candidates
- Medium impact, low effort: Worthwhile optimization candidates
- Low impact, high effort: Defer these optimizations

## Output Format

IMPORTANT: Respond with PURE JSON ONLY - no additional text, explanations, or formatting.

Provide your analysis in the following JSON format:

```json
{"cross_guideline_optimization_opportunities": {"task_environment_alignments": [{"pattern": "string", "affected_domains": ["strings"], "optimization_target": "string", "optimization_approach": "string", "evidence": ["strings"], "effort_impact_ratio": {"effort": "high|medium|low", "impact": "high|medium|low", "priority": "string"}}], "environment_data_alignments": [{"pattern": "string", "affected_domains": ["strings"], "optimization_target": "string", "optimization_approach": "string", "evidence": ["strings"], "effort_impact_ratio": {"effort": "high|medium|low", "impact": "high|medium|low", "priority": "string"}}], "data_component_alignments": [{"pattern": "string", "affected_domains": ["strings"], "optimization_target": "string", "optimization_approach": "string", "evidence": ["strings"], "effort_impact_ratio": {"effort": "high|medium|low", "impact": "high|medium|low", "priority": "string"}}], "component_dependency_alignments": [{"pattern": "string", "affected_domains": ["strings"], "optimization_target": "string", "optimization_approach": "string", "evidence": ["strings"], "effort_impact_ratio": {"effort": "high|medium|low", "impact": "high|medium|low", "priority": "string"}}], "cross_cutting_optimizations": [{"pattern": "string", "affected_domains": ["strings"], "optimization_target": "string", "optimization_approach": "string", "evidence": ["strings"], "effort_impact_ratio": {"effort": "high|medium|low", "impact": "high|medium|low", "priority": "string"}}], "redundancy_reductions": [{"pattern": "string", "affected_domains": ["strings"], "redundant_elements": ["strings"], "consolidation_approach": "string", "evidence": ["strings"], "effort_impact_ratio": {"effort": "high|medium|low", "impact": "high|medium|low", "priority": "string"}}], "synthesis": {"key_cross_guideline_patterns": ["strings"], "prioritized_optimization_strategy": [{"domain_intersection": "string", "strategy": "string", "affected_guidelines": ["strings"], "justification": "string"}], "holistic_recommendations": ["strings"]}}}
```

## Field Descriptions

### Task-Environment Alignments
- **pattern**: Specific optimization pattern between task elaboration and environment requirements
- **affected_domains**: Guideline domains affected by this optimization
- **optimization_target**: Specific target for optimization
- **optimization_approach**: Proposed approach to optimize alignment
- **evidence**: Specific evidence from guidelines supporting this opportunity
- **effort_impact_ratio**: Assessment of implementation effort vs. architectural impact

### Environment-Data Alignments
- **pattern**: Specific optimization pattern between environment requirements and data flow
- **affected_domains**: Guideline domains affected by this optimization
- **optimization_target**: Specific target for optimization
- **optimization_approach**: Proposed approach to optimize alignment
- **evidence**: Specific evidence from guidelines supporting this opportunity
- **effort_impact_ratio**: Assessment of implementation effort vs. architectural impact

### Data-Component Alignments
- **pattern**: Specific optimization pattern between data flow and component structure
- **affected_domains**: Guideline domains affected by this optimization
- **optimization_target**: Specific target for optimization
- **optimization_approach**: Proposed approach to optimize alignment
- **evidence**: Specific evidence from guidelines supporting this opportunity
- **effort_impact_ratio**: Assessment of implementation effort vs. architectural impact

### Component-Dependency Alignments
- **pattern**: Specific optimization pattern between component structure and dependencies
- **affected_domains**: Guideline domains affected by this optimization
- **optimization_target**: Specific target for optimization
- **optimization_approach**: Proposed approach to optimize alignment
- **evidence**: Specific evidence from guidelines supporting this opportunity
- **effort_impact_ratio**: Assessment of implementation effort vs. architectural impact

### Cross-Cutting Optimizations
- **pattern**: Optimization pattern that spans three or more guideline domains
- **affected_domains**: Guideline domains affected by this optimization
- **optimization_target**: Specific target for optimization
- **optimization_approach**: Proposed approach to optimize alignment
- **evidence**: Specific evidence from guidelines supporting this opportunity
- **effort_impact_ratio**: Assessment of implementation effort vs. architectural impact

### Redundancy Reductions
- **pattern**: Pattern of redundant concepts across guideline domains
- **affected_domains**: Guideline domains containing redundancies
- **redundant_elements**: Specific redundant elements identified
- **consolidation_approach**: Approach to consolidate redundancies
- **evidence**: Specific evidence of redundancy from guidelines
- **effort_impact_ratio**: Assessment of implementation effort vs. architectural impact

### Synthesis
- **key_cross_guideline_patterns**: Key patterns identified across multiple guideline domains
- **prioritized_optimization_strategy**: Prioritized approach to implementing optimizations
- **holistic_recommendations**: System-wide recommendations spanning all guideline domains

## Analysis Principles

1. Only flag optimizations that provide clear value across guideline domains
2. Focus on patterns with concrete evidence from guideline outputs
3. Identify optimizations that increase guideline alignment
4. Consider impact on overall system architecture
5. Balance optimization benefits with implementation complexity
6. Prioritize high-impact, low-effort opportunities
7. Identify recurring patterns across guideline domains

## Key Considerations

When analyzing guidelines, check for:
- Misalignments between task requirements and environment specifications
- Inconsistencies between data flow patterns and environmental requirements
- Disconnects between data entities and component interfaces
- Gaps between component structures and data flows
- Dependency issues between components and their implementation needs
- Redundant concepts defined across multiple guideline domains
- Opportunities to enhance integration between guideline domains
- System-wide patterns that could be optimized holistically
"""

phase_one_cross_guideline_optimization_analysis_schema = {
  "type": "object",
  "properties": {
    "cross_guideline_optimization_opportunities": {
      "type": "object",
      "properties": {
        "task_environment_alignments": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pattern": {
                "type": "string",
                "minLength": 1
              },
              "affected_domains": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "minItems": 1
              },
              "optimization_target": {
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
            "required": ["pattern", "affected_domains", "optimization_target", "optimization_approach", "evidence", "effort_impact_ratio"]
          }
        },
        "environment_data_alignments": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pattern": {
                "type": "string",
                "minLength": 1
              },
              "affected_domains": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "minItems": 1
              },
              "optimization_target": {
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
            "required": ["pattern", "affected_domains", "optimization_target", "optimization_approach", "evidence", "effort_impact_ratio"]
          }
        },
        "data_component_alignments": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pattern": {
                "type": "string",
                "minLength": 1
              },
              "affected_domains": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "minItems": 1
              },
              "optimization_target": {
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
            "required": ["pattern", "affected_domains", "optimization_target", "optimization_approach", "evidence", "effort_impact_ratio"]
          }
        },
        "component_dependency_alignments": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pattern": {
                "type": "string",
                "minLength": 1
              },
              "affected_domains": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "minItems": 1
              },
              "optimization_target": {
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
            "required": ["pattern", "affected_domains", "optimization_target", "optimization_approach", "evidence", "effort_impact_ratio"]
          }
        },
        "cross_cutting_optimizations": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pattern": {
                "type": "string",
                "minLength": 1
              },
              "affected_domains": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "minItems": 1
              },
              "optimization_target": {
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
            "required": ["pattern", "affected_domains", "optimization_target", "optimization_approach", "evidence", "effort_impact_ratio"]
          }
        },
        "redundancy_reductions": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pattern": {
                "type": "string",
                "minLength": 1
              },
              "affected_domains": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "minItems": 1
              },
              "redundant_elements": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "minItems": 1
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
            "required": ["pattern", "affected_domains", "redundant_elements", "consolidation_approach", "evidence", "effort_impact_ratio"]
          }
        },
        "synthesis": {
          "type": "object",
          "properties": {
            "key_cross_guideline_patterns": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "minItems": 1
            },
            "prioritized_optimization_strategy": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "domain_intersection": {
                    "type": "string",
                    "minLength": 1
                  },
                  "strategy": {
                    "type": "string",
                    "minLength": 1
                  },
                  "affected_guidelines": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "minItems": 1
                  },
                  "justification": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": ["domain_intersection", "strategy", "affected_guidelines", "justification"]
              },
              "minItems": 1
            },
            "holistic_recommendations": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "minItems": 1
            }
          },
          "required": ["key_cross_guideline_patterns", "prioritized_optimization_strategy", "holistic_recommendations"]
        }
      },
      "required": ["task_environment_alignments", "environment_data_alignments", "data_component_alignments", "component_dependency_alignments", "cross_cutting_optimizations", "redundancy_reductions", "synthesis"]
    }
  },
  "required": ["cross_guideline_optimization_opportunities"]
}

# Cross-Guideline Optimization Analysis Reflection
cross_guideline_optimization_reflection_prompt = """
# Pollinator Agent Technical Reflection with Critical Analysis

You are the reflection agent responsible for conducting rigorous technical analysis of the Pollinator Agent's cross-guideline optimization while maintaining a skeptical, critical perspective on fundamental optimization assumptions and dual-perspective analysis validity.

**CRITICAL JSON REQUIREMENT: You must return ONLY valid JSON. Do not include any explanatory text, markdown code blocks, explanations, reasoning, commentary, or any other content outside the JSON structure. Your entire response must be parseable as JSON. Any non-JSON content will cause system failure.**

Conduct technical validation with critical questioning:

## Technical Analysis with Skeptical Assessment

1. **Optimization Detection Technical Review**:
   - Is the cross-guideline optimization analysis technically sound or artificially complex improvement decomposition?
   - Do identified optimization opportunities reflect genuine system improvements or conventional enhancement patterns?
   - Are optimization boundaries validated benefits or defensive analysis stacking?

2. **Enhancement Completeness Technical Validation with Critical Gaps Analysis**:
   - Are missing optimization opportunities genuine oversights or acceptable enhancement scope?
   - Do identified improvement patterns reflect real system needs or assumed optimization measures?
   - Are impact assessments appropriately calibrated or systematically over-engineered?

3. **Optimization Consistency Technical Assessment with Assumption Challenge**:
   - Do cross-guideline perspectives serve genuine system coherence or impose unnecessary analytical complexity?
   - Are optimization priorities real improvements or artificial enhancement restrictions?
   - Do optimization assumption validations reflect evidence-based reasoning or conventional optimization wisdom?

## Core Responsibilities
1. **Optimization Reality Interrogation**: Challenge whether identified opportunities are genuine system improvements versus theoretical refinement preferences
2. **Evidence Optimization Skepticism**: Question if evidence demonstrates actual performance benefits or coincidental optimization correlations
3. **Implementation Impact Challenge**: Assess if proposed optimizations would actually improve system performance or require effort without real benefit
4. **Dual-Perspective Optimization Assessment**: Evaluate if perspective separation reveals optimization insights or creates unnecessary analytical complexity
5. **Resolution Optimization Review**: Challenge whether recommended optimizations address real performance problems or theoretical system perfectionism
6. **Synthesis Optimization Testing**: Question whether cross-guideline optimization analysis provides actionable performance insights or analytical overhead

## Output Format

Provide your reflection in the following JSON format:

```json
{"reflection_results": {"analysis_accuracy": {"false_positives": [{"domain_alignment": "task_environment|environment_data|data_component|component_dependency|cross_cutting|redundancy_reduction","pattern": "string","reasoning": "string"}],"missing_opportunities": [{"domain_alignment": "task_environment|environment_data|data_component|component_dependency|cross_cutting|redundancy_reduction","pattern": "string","affected_domains": ["strings"],"evidence": ["strings"]}]},"evidence_quality": {"insufficient_evidence": [{"domain_alignment": "task_environment|environment_data|data_component|component_dependency|cross_cutting|redundancy_reduction","pattern": "string","evidence_gap": "string"}],"misinterpreted_evidence": [{"domain_alignment": "task_environment|environment_data|data_component|component_dependency|cross_cutting|redundancy_reduction","pattern": "string","correct_interpretation": "string"}]},"effort_impact_assessment": {"effort_reassessment": [{"domain_alignment": "task_environment|environment_data|data_component|component_dependency|cross_cutting|redundancy_reduction","pattern": "string","current_rating": "high|medium|low","suggested_rating": "high|medium|low","justification": "string"}],"impact_reassessment": [{"domain_alignment": "task_environment|environment_data|data_component|component_dependency|cross_cutting|redundancy_reduction","pattern": "string","current_rating": "high|medium|low","suggested_rating": "high|medium|low","justification": "string"}],"priority_reassessment": [{"domain_alignment": "task_environment|environment_data|data_component|component_dependency|cross_cutting|redundancy_reduction","pattern": "string","current_priority": "string","suggested_priority": "string","justification": "string"}]},"optimization_approach": {"approach_issues": [{"domain_alignment": "task_environment|environment_data|data_component|component_dependency|cross_cutting|redundancy_reduction","pattern": "string","issue": "string","recommendation": "string"}],"alignment_concerns": [{"domain_alignment": "task_environment|environment_data|data_component|component_dependency|cross_cutting|redundancy_reduction","pattern": "string","concern": "string","recommendation": "string"}],"implementation_risks": [{"domain_alignment": "task_environment|environment_data|data_component|component_dependency|cross_cutting|redundancy_reduction","pattern": "string","risk": "string","recommendation": "string"}]},"synthesis_assessment": {"comprehensiveness": {"rating": "high|medium|low","justification": "string","improvement_areas": ["strings"]},"strategic_alignment": {"rating": "high|medium|low","justification": "string","improvement_areas": ["strings"]},"prioritization_effectiveness": {"rating": "high|medium|low","justification": "string","improvement_areas": ["strings"]}}}}
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
- **alignment_concerns**: Concerns about alignment between guidelines
- **implementation_risks**: Risks that may impact implementation success

### Synthesis Assessment
- **comprehensiveness**: Assessment of synthesis coverage across all optimization domains
- **strategic_alignment**: Evaluation of how well the strategy aligns with overall architecture
- **prioritization_effectiveness**: Assessment of optimization prioritization effectiveness

## Skeptical Optimization Review Guidelines

1. **Optimization Opportunity Authenticity Test**: Do these opportunities represent genuine system improvements or different implementation preferences that don't provide real value?
2. **Dual-Perspective Optimization Challenge**: Does separating optimization perspectives reveal meaningful improvements or create artificial optimization complexity?
3. **Implementation Reality Check**: Are proposed optimizations practical performance improvements or theoretical system perfectionism?
4. **Evidence Optimization Skepticism**: Does evidence demonstrate actual performance benefits or coincidental optimization correlations?
5. **Resolution Necessity Assessment**: Do recommended optimizations address real performance problems or theoretical system perfectionism?
6. **Synthesis Complexity Interrogation**: Does cross-guideline optimization analysis justify its analytical overhead with actionable performance insights?

## Skeptical Optimization Verification Checklist

1. **Performance Impact Verification**: Do identified optimization opportunities represent genuine performance improvements that would benefit system operation?
2. **Optimization Separation Challenge**: Are dual perspectives meaningful performance insights or artificial complexity creation?
3. **Evidence Quality Interrogation**: Does supporting evidence demonstrate real performance benefits or theoretical optimization inconsistencies?
4. **Implementation Impact Test**: Would experienced system engineers consider these optimizations valuable performance improvements?
5. **Resolution Practicality Analysis**: Do recommended optimizations solve real performance problems or create theoretical system perfectionism?
6. **Synthesis Value Assessment**: Does cross-guideline optimization analysis provide actionable insights or analytical overhead?
7. **Optimization Significance Challenge**: Are prioritized optimizations genuine performance improvements or manageable system trade-offs?
8. **Evidence Correlation Skepticism**: Do optimization patterns represent meaningful insights or optimization artifacts?
9. **Engineering Team Alignment**: Would practical system engineers agree these optimizations require immediate implementation?
10. **Optimization Complexity Justification**: Does the cross-guideline optimization approach justify its complexity with system performance value?
"""

cross_guideline_optimization_reflection_schema = {
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
                  "domain_alignment": {
                    "type": "string",
                    "enum": [
                      "task_environment",
                      "environment_data",
                      "data_component",
                      "component_dependency",
                      "cross_cutting",
                      "redundancy_reduction"
                    ]
                  },
                  "pattern": {
                    "type": "string"
                  },
                  "reasoning": {
                    "type": "string"
                  }
                },
                "required": ["domain_alignment", "pattern", "reasoning"]
              }
            },
            "missing_opportunities": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "domain_alignment": {
                    "type": "string",
                    "enum": [
                      "task_environment",
                      "environment_data",
                      "data_component",
                      "component_dependency",
                      "cross_cutting",
                      "redundancy_reduction"
                    ]
                  },
                  "pattern": {
                    "type": "string"
                  },
                  "affected_domains": {
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
                "required": ["domain_alignment", "pattern", "affected_domains", "evidence"]
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
                  "domain_alignment": {
                    "type": "string",
                    "enum": [
                      "task_environment",
                      "environment_data",
                      "data_component",
                      "component_dependency",
                      "cross_cutting",
                      "redundancy_reduction"
                    ]
                  },
                  "pattern": {
                    "type": "string"
                  },
                  "evidence_gap": {
                    "type": "string"
                  }
                },
                "required": ["domain_alignment", "pattern", "evidence_gap"]
              }
            },
            "misinterpreted_evidence": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "domain_alignment": {
                    "type": "string",
                    "enum": [
                      "task_environment",
                      "environment_data",
                      "data_component",
                      "component_dependency",
                      "cross_cutting",
                      "redundancy_reduction"
                    ]
                  },
                  "pattern": {
                    "type": "string"
                  },
                  "correct_interpretation": {
                    "type": "string"
                  }
                },
                "required": ["domain_alignment", "pattern", "correct_interpretation"]
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
                  "domain_alignment": {
                    "type": "string",
                    "enum": [
                      "task_environment",
                      "environment_data",
                      "data_component",
                      "component_dependency",
                      "cross_cutting",
                      "redundancy_reduction"
                    ]
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
                "required": ["domain_alignment", "pattern", "current_rating", "suggested_rating", "justification"]
              }
            },
            "impact_reassessment": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "domain_alignment": {
                    "type": "string",
                    "enum": [
                      "task_environment",
                      "environment_data",
                      "data_component",
                      "component_dependency",
                      "cross_cutting",
                      "redundancy_reduction"
                    ]
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
                "required": ["domain_alignment", "pattern", "current_rating", "suggested_rating", "justification"]
              }
            },
            "priority_reassessment": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "domain_alignment": {
                    "type": "string",
                    "enum": [
                      "task_environment",
                      "environment_data",
                      "data_component",
                      "component_dependency",
                      "cross_cutting",
                      "redundancy_reduction"
                    ]
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
                "required": ["domain_alignment", "pattern", "current_priority", "suggested_priority", "justification"]
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
                  "domain_alignment": {
                    "type": "string",
                    "enum": [
                      "task_environment",
                      "environment_data",
                      "data_component",
                      "component_dependency",
                      "cross_cutting",
                      "redundancy_reduction"
                    ]
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
                "required": ["domain_alignment", "pattern", "issue", "recommendation"]
              }
            },
            "alignment_concerns": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "domain_alignment": {
                    "type": "string",
                    "enum": [
                      "task_environment",
                      "environment_data",
                      "data_component",
                      "component_dependency",
                      "cross_cutting",
                      "redundancy_reduction"
                    ]
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
                "required": ["domain_alignment", "pattern", "concern", "recommendation"]
              }
            },
            "implementation_risks": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "domain_alignment": {
                    "type": "string",
                    "enum": [
                      "task_environment",
                      "environment_data",
                      "data_component",
                      "component_dependency",
                      "cross_cutting",
                      "redundancy_reduction"
                    ]
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
                "required": ["domain_alignment", "pattern", "risk", "recommendation"]
              }
            }
          },
          "required": ["approach_issues", "alignment_concerns", "implementation_risks"]
        },
        "synthesis_assessment": {
          "type": "object",
          "properties": {
            "comprehensiveness": {
              "type": "object",
              "properties": {
                "rating": {
                  "type": "string",
                  "enum": ["high", "medium", "low"]
                },
                "justification": {
                  "type": "string"
                },
                "improvement_areas": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              },
              "required": ["rating", "justification", "improvement_areas"]
            },
            "strategic_alignment": {
              "type": "object",
              "properties": {
                "rating": {
                  "type": "string",
                  "enum": ["high", "medium", "low"]
                },
                "justification": {
                  "type": "string"
                },
                "improvement_areas": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              },
              "required": ["rating", "justification", "improvement_areas"]
            },
            "prioritization_effectiveness": {
              "type": "object",
              "properties": {
                "rating": {
                  "type": "string",
                  "enum": ["high", "medium", "low"]
                },
                "justification": {
                  "type": "string"
                },
                "improvement_areas": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              },
              "required": ["rating", "justification", "improvement_areas"]
            }
          },
          "required": ["comprehensiveness", "strategic_alignment", "prioritization_effectiveness"]
        }
      },
      "required": ["analysis_accuracy", "evidence_quality", "effort_impact_assessment", "optimization_approach", "synthesis_assessment"]
    }
  },
  "required": ["reflection_results"]
}

# Cross-Guideline Optimization Analysis Revision
cross_guideline_optimization_revision_prompt = """
# Pollinator Agent Revision Prompt

You are the Pollinator Agent processing reflection results to implement self-corrections to your cross-guideline optimization analysis. Your role is to systematically address identified issues from the reflection phase, refining your analysis of optimization opportunities across phase one guidelines to ensure both accuracy and feasibility.

## Core Responsibilities
1. Process reflection feedback on your cross-guideline optimization analysis
2. Remove incorrectly identified opportunities (false positives)
3. Add overlooked opportunities that were missed
4. Strengthen evidence for legitimate opportunities
5. Adjust effort-impact assessments to be more realistic
6. Refine optimization approaches to address identified concerns
7. Improve the synthesis and prioritization of optimization recommendations
8. Maintain a holistic architectural perspective

## Input Format

You will receive two inputs:
1. Your original cross-guideline optimization analysis output
2. Reflection results in the following structure:
```json
{"reflection_results": {"analysis_accuracy": {"false_positives": [{"domain_alignment": "task_environment|environment_data|data_component|component_dependency|cross_cutting|redundancy_reduction","pattern": "string","reasoning": "string"}],"missing_opportunities": [{"domain_alignment": "task_environment|environment_data|data_component|component_dependency|cross_cutting|redundancy_reduction","pattern": "string","affected_domains": ["strings"],"evidence": ["strings"]}]},"evidence_quality": {"insufficient_evidence": [{"domain_alignment": "task_environment|environment_data|data_component|component_dependency|cross_cutting|redundancy_reduction","pattern": "string","evidence_gap": "string"}],"misinterpreted_evidence": [{"domain_alignment": "task_environment|environment_data|data_component|component_dependency|cross_cutting|redundancy_reduction","pattern": "string","correct_interpretation": "string"}]},"effort_impact_assessment": {"effort_reassessment": [{"domain_alignment": "task_environment|environment_data|data_component|component_dependency|cross_cutting|redundancy_reduction","pattern": "string","current_rating": "high|medium|low","suggested_rating": "high|medium|low","justification": "string"}],"impact_reassessment": [{"domain_alignment": "task_environment|environment_data|data_component|component_dependency|cross_cutting|redundancy_reduction","pattern": "string","current_rating": "high|medium|low","suggested_rating": "high|medium|low","justification": "string"}],"priority_reassessment": [{"domain_alignment": "task_environment|environment_data|data_component|component_dependency|cross_cutting|redundancy_reduction","pattern": "string","current_priority": "string","suggested_priority": "string","justification": "string"}]},"optimization_approach": {"approach_issues": [{"domain_alignment": "task_environment|environment_data|data_component|component_dependency|cross_cutting|redundancy_reduction","pattern": "string","issue": "string","recommendation": "string"}],"alignment_concerns": [{"domain_alignment": "task_environment|environment_data|data_component|component_dependency|cross_cutting|redundancy_reduction","pattern": "string","concern": "string","recommendation": "string"}],"implementation_risks": [{"domain_alignment": "task_environment|environment_data|data_component|component_dependency|cross_cutting|redundancy_reduction","pattern": "string","risk": "string","recommendation": "string"}]},"synthesis_assessment": {"comprehensiveness": {"rating": "high|medium|low","justification": "string","improvement_areas": ["strings"]},"strategic_alignment": {"rating": "high|medium|low","justification": "string","improvement_areas": ["strings"]},"prioritization_effectiveness": {"rating": "high|medium|low","justification": "string","improvement_areas": ["strings"]}}}}
```

## Revision Process

1. Analyze reflection feedback methodically for all optimization domains
2. Remove identified false positives
3. Add overlooked opportunities with proper evidence
4. Strengthen evidence for existing opportunities
5. Adjust effort and impact ratings where needed
6. Revise optimization approaches to address concerns
7. Enhance synthesis to better integrate optimization recommendations
8. Validate all opportunities against architectural principles

## Output Format

Provide your revised analysis in the following JSON format:

```json
{"revision_metadata": {"processed_feedback": {"false_positives_removed": [{"domain_alignment": "task_environment|environment_data|data_component|component_dependency|cross_cutting|redundancy_reduction","pattern": "string","removal_reason": "string"}],"opportunities_added": [{"domain_alignment": "task_environment|environment_data|data_component|component_dependency|cross_cutting|redundancy_reduction","pattern": "string","addition_justification": "string"}],"evidence_enhancements": [{"domain_alignment": "task_environment|environment_data|data_component|component_dependency|cross_cutting|redundancy_reduction","pattern": "string","enhancement_description": "string"}],"rating_adjustments": [{"domain_alignment": "task_environment|environment_data|data_component|component_dependency|cross_cutting|redundancy_reduction","pattern": "string","adjustment_type": "effort|impact|priority","adjustment_description": "string"}],"approach_refinements": [{"domain_alignment": "task_environment|environment_data|data_component|component_dependency|cross_cutting|redundancy_reduction","pattern": "string","refinement_description": "string"}],"synthesis_improvements": ["strings"]},"validation_steps": ["strings"]},"cross_guideline_optimization_opportunities": {"task_environment_alignments": [{"pattern": "string","affected_domains": ["strings"],"optimization_target": "string","optimization_approach": "string","evidence": ["strings"],"effort_impact_ratio": {"effort": "high|medium|low","impact": "high|medium|low","priority": "string"},"revision_note": "string"}],"environment_data_alignments": [{"pattern": "string","affected_domains": ["strings"],"optimization_target": "string","optimization_approach": "string","evidence": ["strings"],"effort_impact_ratio": {"effort": "high|medium|low","impact": "high|medium|low","priority": "string"},"revision_note": "string"}],"data_component_alignments": [{"pattern": "string","affected_domains": ["strings"],"optimization_target": "string","optimization_approach": "string","evidence": ["strings"],"effort_impact_ratio": {"effort": "high|medium|low","impact": "high|medium|low","priority": "string"},"revision_note": "string"}],"component_dependency_alignments": [{"pattern": "string","affected_domains": ["strings"],"optimization_target": "string","optimization_approach": "string","evidence": ["strings"],"effort_impact_ratio": {"effort": "high|medium|low","impact": "high|medium|low","priority": "string"},"revision_note": "string"}],"cross_cutting_optimizations": [{"pattern": "string","affected_domains": ["strings"],"optimization_target": "string","optimization_approach": "string","evidence": ["strings"],"effort_impact_ratio": {"effort": "high|medium|low","impact": "high|medium|low","priority": "string"},"revision_note": "string"}],"redundancy_reductions": [{"pattern": "string","affected_domains": ["strings"],"redundant_elements": ["strings"],"consolidation_approach": "string","evidence": ["strings"],"effort_impact_ratio": {"effort": "high|medium|low","impact": "high|medium|low","priority": "string"},"revision_note": "string"}],"synthesis": {"key_cross_guideline_patterns": ["strings"],"prioritized_optimization_strategy": [{"domain_intersection": "string","strategy": "string","affected_guidelines": ["strings"],"justification": "string","revision_note": "string"}],"holistic_recommendations": ["strings"]}}}
```

## Revision Guidelines

### Removing False Positives
- Remove optimization opportunities flagged as false positives
- Document reasoning for removal to maintain transparency
- Ensure removal doesn't create gaps in overall optimization strategy

### Adding Overlooked Opportunities
- Add all missing opportunities identified in reflection
- Provide comprehensive evidence for each new opportunity
- Ensure new additions maintain architectural coherence

### Evidence Enhancements
- Strengthen evidence for opportunities with insufficient support
- Correct misinterpreted evidence with accurate interpretations
- Ensure evidence is technical, specific, and directly supports the opportunity

### Rating Adjustments
- Adjust effort ratings to reflect technical complexity
- Revise impact ratings to accurately reflect architectural benefits
- Update priority designations to align with adjusted ratings

### Approach Refinements
- Address identified issues in optimization approaches
- Mitigate alignment concerns between guideline domains
- Reduce implementation risks through improved approaches

### Synthesis Improvements
- Strengthen key cross-guideline patterns
- Improve prioritization strategy
- Enhance holistic recommendations

## Validation Checklist

Before finalizing your revised analysis:
1. Confirm all false positives have been removed
2. Verify all missing opportunities have been added
3. Ensure all evidence issues have been addressed
4. Check that rating adjustments have been implemented
5. Validate that approach refinements address identified concerns
6. Confirm that synthesis improvements enhance overall strategy
7. Ensure comprehensive coverage of all cross-guideline domains
8. Verify strategic alignment of optimization recommendations

## Self-Correction Principles

1. Focus on architectural improvement over implementation details
2. Prioritize high-value, low-effort optimizations
3. Ensure optimizations genuinely improve cross-guideline alignment
4. Consider dependencies and potential ripple effects
5. Maintain balance between guideline domains
6. Ensure synthesis provides a coherent overall optimization strategy
7. Align optimizations with established architectural patterns and best practices
"""

cross_guideline_optimization_revision_schema = {
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
                  "domain_alignment": {
                    "type": "string",
                    "enum": [
                      "task_environment",
                      "environment_data",
                      "data_component",
                      "component_dependency",
                      "cross_cutting",
                      "redundancy_reduction"
                    ]
                  },
                  "pattern": {
                    "type": "string"
                  },
                  "removal_reason": {
                    "type": "string"
                  }
                },
                "required": ["domain_alignment", "pattern", "removal_reason"]
              }
            },
            "opportunities_added": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "domain_alignment": {
                    "type": "string",
                    "enum": [
                      "task_environment",
                      "environment_data",
                      "data_component",
                      "component_dependency",
                      "cross_cutting",
                      "redundancy_reduction"
                    ]
                  },
                  "pattern": {
                    "type": "string"
                  },
                  "addition_justification": {
                    "type": "string"
                  }
                },
                "required": ["domain_alignment", "pattern", "addition_justification"]
              }
            },
            "evidence_enhancements": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "domain_alignment": {
                    "type": "string",
                    "enum": [
                      "task_environment",
                      "environment_data",
                      "data_component",
                      "component_dependency",
                      "cross_cutting",
                      "redundancy_reduction"
                    ]
                  },
                  "pattern": {
                    "type": "string"
                  },
                  "enhancement_description": {
                    "type": "string"
                  }
                },
                "required": ["domain_alignment", "pattern", "enhancement_description"]
              }
            },
            "rating_adjustments": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "domain_alignment": {
                    "type": "string",
                    "enum": [
                      "task_environment",
                      "environment_data",
                      "data_component",
                      "component_dependency",
                      "cross_cutting",
                      "redundancy_reduction"
                    ]
                  },
                  "pattern": {
                    "type": "string"
                  },
                  "adjustment_type": {
                    "type": "string",
                    "enum": ["effort", "impact", "priority"]
                  },
                  "adjustment_description": {
                    "type": "string"
                  }
                },
                "required": ["domain_alignment", "pattern", "adjustment_type", "adjustment_description"]
              }
            },
            "approach_refinements": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "domain_alignment": {
                    "type": "string",
                    "enum": [
                      "task_environment",
                      "environment_data",
                      "data_component",
                      "component_dependency",
                      "cross_cutting",
                      "redundancy_reduction"
                    ]
                  },
                  "pattern": {
                    "type": "string"
                  },
                  "refinement_description": {
                    "type": "string"
                  }
                },
                "required": ["domain_alignment", "pattern", "refinement_description"]
              }
            },
            "synthesis_improvements": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "required": ["false_positives_removed", "opportunities_added", "evidence_enhancements", "rating_adjustments", "approach_refinements", "synthesis_improvements"]
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
    "cross_guideline_optimization_opportunities": {
      "type": "object",
      "properties": {
        "task_environment_alignments": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pattern": {
                "type": "string"
              },
              "affected_domains": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "optimization_target": {
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
              },
              "revision_note": {
                "type": "string"
              }
            },
            "required": ["pattern", "affected_domains", "optimization_target", "optimization_approach", "evidence", "effort_impact_ratio", "revision_note"]
          }
        },
        "environment_data_alignments": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pattern": {
                "type": "string"
              },
              "affected_domains": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "optimization_target": {
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
              },
              "revision_note": {
                "type": "string"
              }
            },
            "required": ["pattern", "affected_domains", "optimization_target", "optimization_approach", "evidence", "effort_impact_ratio", "revision_note"]
          }
        },
        "data_component_alignments": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pattern": {
                "type": "string"
              },
              "affected_domains": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "optimization_target": {
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
              },
              "revision_note": {
                "type": "string"
              }
            },
            "required": ["pattern", "affected_domains", "optimization_target", "optimization_approach", "evidence", "effort_impact_ratio", "revision_note"]
          }
        },
        "component_dependency_alignments": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pattern": {
                "type": "string"
              },
              "affected_domains": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "optimization_target": {
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
              },
              "revision_note": {
                "type": "string"
              }
            },
            "required": ["pattern", "affected_domains", "optimization_target", "optimization_approach", "evidence", "effort_impact_ratio", "revision_note"]
          }
        },
        "cross_cutting_optimizations": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pattern": {
                "type": "string"
              },
              "affected_domains": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "optimization_target": {
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
              },
              "revision_note": {
                "type": "string"
              }
            },
            "required": ["pattern", "affected_domains", "optimization_target", "optimization_approach", "evidence", "effort_impact_ratio", "revision_note"]
          }
        },
        "redundancy_reductions": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pattern": {
                "type": "string"
              },
              "affected_domains": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "redundant_elements": {
                "type": "array",
                "items": {
                  "type": "string"
                }
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
              },
              "revision_note": {
                "type": "string"
              }
            },
            "required": ["pattern", "affected_domains", "redundant_elements", "consolidation_approach", "evidence", "effort_impact_ratio", "revision_note"]
          }
        },
        "synthesis": {
          "type": "object",
          "properties": {
            "key_cross_guideline_patterns": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "prioritized_optimization_strategy": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "domain_intersection": {
                    "type": "string"
                  },
                  "strategy": {
                    "type": "string"
                  },
                  "affected_guidelines": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "justification": {
                    "type": "string"
                  },
                  "revision_note": {
                    "type": "string"
                  }
                },
                "required": ["domain_intersection", "strategy", "affected_guidelines", "justification", "revision_note"]
              }
            },
            "holistic_recommendations": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "required": ["key_cross_guideline_patterns", "prioritized_optimization_strategy", "holistic_recommendations"]
        }
      },
      "required": ["task_environment_alignments", "environment_data_alignments", "data_component_alignments", "component_dependency_alignments", "cross_cutting_optimizations", "redundancy_reductions", "synthesis"]
    }
  },
  "required": ["revision_metadata", "cross_guideline_optimization_opportunities"]
}