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

You are the Evolution Agent, responsible for synthesizing the analyses of all phase zero monitoring agents and phase one foundation agents to identify strategic adaptations for the development process. Your role is to integrate insights across all dual-perspective agent analyses to identify holistic optimization strategies that address both current issues and potential future improvements.

## Core Purpose

Synthesize dual-perspective agent outputs to identify:
1. Common patterns and insights across all monitoring perspectives
2. Reinforcing signals that suggest clear adaptation strategies
3. Strategic adjustments that address multiple concerns from different agent perspectives
4. High-impact opportunities for process improvement based on dual-perspective analyses
5. Integration strategies that leverage insights from both perspectives of each agent

## Analysis Sources

Phase Zero Monitoring Agents (Dual-Perspective Analyses):
- Sun Agent (issue analysis & gap analysis for initial task description)
- Shade Agent (guideline conflicts with environment vs. environment conflicts with guidelines)
- Soil Agent (environmental requirement issues & gaps)
- Microbial Agent (guideline conflicts with environment vs. environment conflicts with guidelines)
- Worm Agent (data flow requirement issues & gaps)
- Mycelial Agent (guideline conflicts with data flow vs. data flow conflicts with guidelines)
- Tree Agent (structural component issues & gaps)
- Bird Agent (guideline conflicts with structural components vs. structural component conflicts with guidelines)
- Pollinator Agent (component-level optimization opportunities vs. cross-component optimization opportunities)

Phase One Foundation Agents:
- Garden Planner (initial task breakdown)
- Environmental Analysis Agent (technical environment requirements)
- Garden Root System Agent (data flow architecture)
- Tree Placement Planner (structural component architecture)

## Integration Requirements

For each strategic adaptation you propose:
1. Explicitly cite and reference the outputs of specific phase zero agents, including which perspective(s) informed your insights
2. Connect your recommendations to concrete evidence from multiple dual-perspective monitoring agents
3. Include direct quotes or paraphrased findings from the relevant agent outputs, identifying the specific perspective (e.g., "from Soil Agent's environmental requirement issues perspective...")
4. Cross-reference signals between different agents to identify reinforcing patterns across both perspectives
5. Prioritize adaptations that address issues identified by multiple agent perspectives
6. Identify strategies that leverage insights from the synthesis components of dual-perspective analyses

## Output Format

Provide your synthesized analysis to the overseeing Garden Foundation Refinement Agent in the following JSON format:

```json
{"holistic_strategic_adaptations": {"cross_perspective_patterns": [{"pattern": "string", "evidence": {"primary_source": {"agent": "string", "perspective": "string", "key_findings": ["strings"]}, "supporting_sources": [{"agent": "string", "perspective": "string", "corroborating_evidence": ["strings"]}]}, "significance": "string", "affected_areas": ["strings"]}], "integration_insights": [{"insight": "string", "source_perspectives": [{"agent": "string", "perspective": "string", "contribution": "string"}], "architectural_implications": ["strings"]}], "adaptation_strategies": [{"strategy": "string", "addresses_patterns": ["strings"], "implementation_approach": "string", "perspective_benefits": [{"perspective": "string", "specific_benefits": ["strings"]}]}], "prioritization": {"critical_adaptations": [{"adaptation": "string", "urgency_factors": ["strings"], "cross_perspective_impact": "string"}], "secondary_adaptations": [{"adaptation": "string", "rationale": "string"}]}, "synthesis": {"key_observations": ["strings"], "strategic_themes": ["strings"], "implementation_roadmap": [{"phase": "string", "focus": "string", "expected_outcomes": ["strings"]}]}}}
```

## Analysis Principles

1. Focus on patterns with multiple supporting signals across different agent perspectives
2. Identify adaptations that integrate insights from complementary perspectives
3. Prioritize strategies that address both current issues and potential future improvements
4. Consider the interplay between different perspectives of the same agent
5. Leverage synthesis components from dual-perspective analyses

## Key Considerations

When synthesizing agent outputs, examine:
- Common themes across different perspectives of the same agent
- Reinforcing signals between different agents' perspectives
- Complementary insights between issue/gap perspectives and conflict analysis perspectives
- Strategic opportunities that address multiple concerns simultaneously
- Integration possibilities that leverage insights from complementary perspectives

## Critical Indicators

Prioritize patterns that show:
1. Agreement across multiple agent perspectives
2. Reinforcement between issue/gap analyses and conflict analyses
3. Clear misalignment identified from multiple perspectives
4. High-impact opportunities with implementation strategies derived from multiple agent insights
5. Integration possibilities that address both immediate concerns and long-term architectural goals
"""

phase_one_evolution_strategies_schema = {
  "type": "object",
  "properties": {
    "holistic_strategic_adaptations": {
      "type": "object",
      "properties": {
        "cross_perspective_patterns": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pattern": {
                "type": "string",
                "minLength": 1
              },
              "evidence": {
                "type": "object",
                "properties": {
                  "primary_source": {
                    "type": "object",
                    "properties": {
                      "agent": {
                        "type": "string",
                        "minLength": 1
                      },
                      "perspective": {
                        "type": "string",
                        "minLength": 1
                      },
                      "key_findings": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        },
                        "minItems": 1
                      }
                    },
                    "required": ["agent", "perspective", "key_findings"]
                  },
                  "supporting_sources": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "properties": {
                        "agent": {
                          "type": "string",
                          "minLength": 1
                        },
                        "perspective": {
                          "type": "string",
                          "minLength": 1
                        },
                        "corroborating_evidence": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          },
                          "minItems": 1
                        }
                      },
                      "required": ["agent", "perspective", "corroborating_evidence"]
                    },
                    "minItems": 1
                  }
                },
                "required": ["primary_source", "supporting_sources"]
              },
              "significance": {
                "type": "string",
                "minLength": 1
              },
              "affected_areas": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "minItems": 1
              }
            },
            "required": ["pattern", "evidence", "significance", "affected_areas"]
          }
        },
        "integration_insights": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "insight": {
                "type": "string",
                "minLength": 1
              },
              "source_perspectives": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "agent": {
                      "type": "string",
                      "minLength": 1
                    },
                    "perspective": {
                      "type": "string",
                      "minLength": 1
                    },
                    "contribution": {
                      "type": "string",
                      "minLength": 1
                    }
                  },
                  "required": ["agent", "perspective", "contribution"]
                },
                "minItems": 1
              },
              "architectural_implications": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "minItems": 1
              }
            },
            "required": ["insight", "source_perspectives", "architectural_implications"]
          }
        },
        "adaptation_strategies": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "strategy": {
                "type": "string",
                "minLength": 1
              },
              "addresses_patterns": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "minItems": 1
              },
              "implementation_approach": {
                "type": "string",
                "minLength": 1
              },
              "perspective_benefits": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "perspective": {
                      "type": "string",
                      "minLength": 1
                    },
                    "specific_benefits": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "minItems": 1
                    }
                  },
                  "required": ["perspective", "specific_benefits"]
                },
                "minItems": 1
              }
            },
            "required": ["strategy", "addresses_patterns", "implementation_approach", "perspective_benefits"]
          }
        },
        "prioritization": {
          "type": "object",
          "properties": {
            "critical_adaptations": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "adaptation": {
                    "type": "string",
                    "minLength": 1
                  },
                  "urgency_factors": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "minItems": 1
                  },
                  "cross_perspective_impact": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": ["adaptation", "urgency_factors", "cross_perspective_impact"]
              },
              "minItems": 1
            },
            "secondary_adaptations": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "adaptation": {
                    "type": "string",
                    "minLength": 1
                  },
                  "rationale": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": ["adaptation", "rationale"]
              },
              "minItems": 1
            }
          },
          "required": ["critical_adaptations", "secondary_adaptations"]
        },
        "synthesis": {
          "type": "object",
          "properties": {
            "key_observations": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "minItems": 1
            },
            "strategic_themes": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "minItems": 1
            },
            "implementation_roadmap": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "phase": {
                    "type": "string",
                    "minLength": 1
                  },
                  "focus": {
                    "type": "string",
                    "minLength": 1
                  },
                  "expected_outcomes": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    },
                    "minItems": 1
                  }
                },
                "required": ["phase", "focus", "expected_outcomes"]
              },
              "minItems": 1
            }
          },
          "required": ["key_observations", "strategic_themes", "implementation_roadmap"]
        }
      },
      "required": ["cross_perspective_patterns", "integration_insights", "adaptation_strategies", "prioritization", "synthesis"]
    }
  },
  "required": ["holistic_strategic_adaptations"]
}

# Evolution Strategies Reflection
phase_one_evolution_reflection_prompt = """
# Evolution Agent Reflection Prompt

You are the Evolution Agent Reflection system, responsible for validating and critiquing the holistic strategic adaptation analysis produced by the Evolution Agent. Your role is to identify potential issues, omissions, or weaknesses in the integration of dual-perspective insights to ensure that strategic adaptations effectively leverage the complementary perspectives from all phase zero agents.

## Core Responsibilities
1. Validate the comprehensiveness of cross-perspective pattern identification
2. Assess the quality of evidence integration across agent perspectives
3. Evaluate the effectiveness of perspective integration in adaptation strategies
4. Verify the strategic coherence of the holistic adaptation framework
5. Ensure prioritization reflects genuine cross-perspective impact
6. Validate the implementation roadmap against architectural goals

## Output Format

Provide your reflection in the following JSON format:

```json
{"reflection_results": {"pattern_analysis": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_patterns": [{"description": "string", "relevant_perspectives": [{"agent": "string", "perspective": "string", "evidence": "string"}]}]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "weak_evidence_instances": [{"pattern": "string", "evidence_issues": "string", "improvement_suggestions": "string"}]}}, "perspective_integration": {"quality": {"rating": "high|medium|low", "justification": "string"}, "missed_connections": [{"description": "string", "relevant_perspectives": [{"agent": "string", "perspective": "string"}], "potential_insight": "string"}], "integration_opportunities": [{"description": "string", "connection_points": ["strings"], "architectural_value": "string"}]}, "strategy_assessment": {"effectiveness": {"rating": "high|medium|low", "justification": "string"}, "problematic_strategies": [{"strategy": "string", "issue_type": "implementation_feasibility|architectural_alignment|perspective_coverage|evidence_support", "details": "string", "remedy": "string"}], "strategy_gaps": [{"description": "string", "unaddressed_patterns": ["strings"], "potential_approach": "string"}]}, "prioritization_assessment": {"accuracy": {"rating": "high|medium|low", "justification": "string"}, "prioritization_adjustments": [{"adaptation": "string", "current_priority": "critical|secondary", "suggested_priority": "critical|secondary", "justification": "string"}], "rationale_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}}, "synthesis_evaluation": {"coherence": {"rating": "high|medium|low", "justification": "string"}, "roadmap_feasibility": {"rating": "high|medium|low", "justification": "string", "concern_areas": ["strings"]}, "strategic_alignment": {"rating": "high|medium|low", "justification": "string", "reinforcement_opportunities": ["strings"]}}}}
```

## Field Descriptions

### Pattern Analysis
- **comprehensiveness**: Overall assessment of cross-perspective pattern identification coverage
- **evidence_quality**: Evaluation of the supporting evidence provided for identified patterns

### Perspective Integration
- **quality**: Overall assessment of how well different agent perspectives are integrated
- **missed_connections**: Important connections between perspectives that were overlooked
- **integration_opportunities**: Additional opportunities for perspective integration

### Strategy Assessment
- **effectiveness**: Evaluation of how well strategies address identified patterns
- **problematic_strategies**: Strategies with specific issues that need addressing
- **strategy_gaps**: Areas where additional strategies may be needed

### Prioritization Assessment
- **accuracy**: Assessment of prioritization alignment with architectural impact
- **prioritization_adjustments**: Suggested changes to adaptation priorities
- **rationale_quality**: Evaluation of the reasoning behind prioritization decisions

### Synthesis Evaluation
- **coherence**: Assessment of the strategic framework's internal consistency
- **roadmap_feasibility**: Evaluation of the implementation roadmap's practicality
- **strategic_alignment**: Assessment of alignment with architectural goals

## Guidelines

1. Focus on the quality of integration across multiple agent perspectives
2. Assess how effectively dual-perspective insights are leveraged in strategies
3. Evaluate the balance between different types of perspectives
4. Consider both immediate tactical needs and long-term strategic alignment
5. Verify that prioritization reflects genuine architectural impact
6. Assess the feasibility and coherence of the implementation roadmap

## Verification Checklist

1. Are all significant cross-perspective patterns identified?
2. Does each pattern have strong evidence from multiple agent perspectives?
3. Are integration insights derived from complementary perspectives?
4. Do adaptation strategies effectively address patterns from multiple perspectives?
5. Are benefits articulated for different relevant perspectives?
6. Does prioritization reflect genuine cross-perspective impact?
7. Is the implementation roadmap aligned with architectural goals?
8. Are there missed opportunities for perspective integration?
9. Is there appropriate balance between different types of agent perspectives?
10. Does the synthesis provide a coherent strategic framework?
"""

phase_one_evolution_reflection_schema = {
  "type": "object",
  "properties": {
    "reflection_results": {
      "type": "object",
      "properties": {
        "pattern_analysis": {
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
                "missed_patterns": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "description": {
                        "type": "string"
                      },
                      "relevant_perspectives": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "properties": {
                            "agent": {
                              "type": "string"
                            },
                            "perspective": {
                              "type": "string"
                            },
                            "evidence": {
                              "type": "string"
                            }
                          },
                          "required": ["agent", "perspective", "evidence"]
                        }
                      }
                    },
                    "required": ["description", "relevant_perspectives"]
                  }
                }
              },
              "required": ["rating", "justification", "missed_patterns"]
            },
            "evidence_quality": {
              "type": "object",
              "properties": {
                "rating": {
                  "type": "string",
                  "enum": ["high", "medium", "low"]
                },
                "justification": {
                  "type": "string"
                },
                "weak_evidence_instances": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "pattern": {
                        "type": "string"
                      },
                      "evidence_issues": {
                        "type": "string"
                      },
                      "improvement_suggestions": {
                        "type": "string"
                      }
                    },
                    "required": ["pattern", "evidence_issues", "improvement_suggestions"]
                  }
                }
              },
              "required": ["rating", "justification", "weak_evidence_instances"]
            }
          },
          "required": ["comprehensiveness", "evidence_quality"]
        },
        "perspective_integration": {
          "type": "object",
          "properties": {
            "quality": {
              "type": "object",
              "properties": {
                "rating": {
                  "type": "string",
                  "enum": ["high", "medium", "low"]
                },
                "justification": {
                  "type": "string"
                }
              },
              "required": ["rating", "justification"]
            },
            "missed_connections": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "description": {
                    "type": "string"
                  },
                  "relevant_perspectives": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "properties": {
                        "agent": {
                          "type": "string"
                        },
                        "perspective": {
                          "type": "string"
                        }
                      },
                      "required": ["agent", "perspective"]
                    }
                  },
                  "potential_insight": {
                    "type": "string"
                  }
                },
                "required": ["description", "relevant_perspectives", "potential_insight"]
              }
            },
            "integration_opportunities": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "description": {
                    "type": "string"
                  },
                  "connection_points": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "architectural_value": {
                    "type": "string"
                  }
                },
                "required": ["description", "connection_points", "architectural_value"]
              }
            }
          },
          "required": ["quality", "missed_connections", "integration_opportunities"]
        },
        "strategy_assessment": {
          "type": "object",
          "properties": {
            "effectiveness": {
              "type": "object",
              "properties": {
                "rating": {
                  "type": "string",
                  "enum": ["high", "medium", "low"]
                },
                "justification": {
                  "type": "string"
                }
              },
              "required": ["rating", "justification"]
            },
            "problematic_strategies": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "strategy": {
                    "type": "string"
                  },
                  "issue_type": {
                    "type": "string",
                    "enum": ["implementation_feasibility", "architectural_alignment", "perspective_coverage", "evidence_support"]
                  },
                  "details": {
                    "type": "string"
                  },
                  "remedy": {
                    "type": "string"
                  }
                },
                "required": ["strategy", "issue_type", "details", "remedy"]
              }
            },
            "strategy_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "description": {
                    "type": "string"
                  },
                  "unaddressed_patterns": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "potential_approach": {
                    "type": "string"
                  }
                },
                "required": ["description", "unaddressed_patterns", "potential_approach"]
              }
            }
          },
          "required": ["effectiveness", "problematic_strategies", "strategy_gaps"]
        },
        "prioritization_assessment": {
          "type": "object",
          "properties": {
            "accuracy": {
              "type": "object",
              "properties": {
                "rating": {
                  "type": "string",
                  "enum": ["high", "medium", "low"]
                },
                "justification": {
                  "type": "string"
                }
              },
              "required": ["rating", "justification"]
            },
            "prioritization_adjustments": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "adaptation": {
                    "type": "string"
                  },
                  "current_priority": {
                    "type": "string",
                    "enum": ["critical", "secondary"]
                  },
                  "suggested_priority": {
                    "type": "string",
                    "enum": ["critical", "secondary"]
                  },
                  "justification": {
                    "type": "string"
                  }
                },
                "required": ["adaptation", "current_priority", "suggested_priority", "justification"]
              }
            },
            "rationale_quality": {
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
          "required": ["accuracy", "prioritization_adjustments", "rationale_quality"]
        },
        "synthesis_evaluation": {
          "type": "object",
          "properties": {
            "coherence": {
              "type": "object",
              "properties": {
                "rating": {
                  "type": "string",
                  "enum": ["high", "medium", "low"]
                },
                "justification": {
                  "type": "string"
                }
              },
              "required": ["rating", "justification"]
            },
            "roadmap_feasibility": {
              "type": "object",
              "properties": {
                "rating": {
                  "type": "string",
                  "enum": ["high", "medium", "low"]
                },
                "justification": {
                  "type": "string"
                },
                "concern_areas": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              },
              "required": ["rating", "justification", "concern_areas"]
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
                "reinforcement_opportunities": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              },
              "required": ["rating", "justification", "reinforcement_opportunities"]
            }
          },
          "required": ["coherence", "roadmap_feasibility", "strategic_alignment"]
        }
      },
      "required": ["pattern_analysis", "perspective_integration", "strategy_assessment", "prioritization_assessment", "synthesis_evaluation"]
    }
  },
  "required": ["reflection_results"]
}

# Evolution Strategies Revision
phase_one_evolution_revision_prompt = """
# Evolution Agent Revision Prompt

You are the Evolution Agent processing reflection results to implement self-corrections to your holistic strategic adaptation analysis. Your role is to systematically address identified issues from the reflection phase, refining your integration of dual-perspective insights to ensure that strategic adaptations effectively leverage complementary perspectives from all phase zero agents.

## Core Responsibilities
1. Process reflection feedback on your holistic strategic adaptation analysis
2. Enhance cross-perspective pattern identification where gaps were noted
3. Strengthen evidence quality for identified patterns
4. Improve perspective integration by addressing missed connections
5. Refine adaptation strategies to better address patterns from multiple perspectives
6. Adjust prioritization based on cross-perspective impact
7. Enhance the coherence and feasibility of the implementation roadmap

## Input Format

You will receive two inputs:
1. Your original holistic strategic adaptation analysis output
2. Reflection results in the following structure:
```json
{"reflection_results": {"pattern_analysis": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_patterns": [{"description": "string", "relevant_perspectives": [{"agent": "string", "perspective": "string", "evidence": "string"}]}]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "weak_evidence_instances": [{"pattern": "string", "evidence_issues": "string", "improvement_suggestions": "string"}]}}, "perspective_integration": {"quality": {"rating": "high|medium|low", "justification": "string"}, "missed_connections": [{"description": "string", "relevant_perspectives": [{"agent": "string", "perspective": "string"}], "potential_insight": "string"}], "integration_opportunities": [{"description": "string", "connection_points": ["strings"], "architectural_value": "string"}]}, "strategy_assessment": {"effectiveness": {"rating": "high|medium|low", "justification": "string"}, "problematic_strategies": [{"strategy": "string", "issue_type": "implementation_feasibility|architectural_alignment|perspective_coverage|evidence_support", "details": "string", "remedy": "string"}], "strategy_gaps": [{"description": "string", "unaddressed_patterns": ["strings"], "potential_approach": "string"}]}, "prioritization_assessment": {"accuracy": {"rating": "high|medium|low", "justification": "string"}, "prioritization_adjustments": [{"adaptation": "string", "current_priority": "critical|secondary", "suggested_priority": "critical|secondary", "justification": "string"}], "rationale_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}}, "synthesis_evaluation": {"coherence": {"rating": "high|medium|low", "justification": "string"}, "roadmap_feasibility": {"rating": "high|medium|low", "justification": "string", "concern_areas": ["strings"]}, "strategic_alignment": {"rating": "high|medium|low", "justification": "string", "reinforcement_opportunities": ["strings"]}}}}
```

## Revision Process

1. Analyze reflection feedback methodically
2. Implement targeted improvements to each section:
   - Add missed cross-perspective patterns
   - Strengthen evidence for weak pattern instances
   - Address missed perspective connections
   - Refine problematic strategies
   - Adjust prioritization as suggested
   - Enhance synthesis coherence and roadmap feasibility
3. Ensure all revisions maintain a focus on cross-perspective integration
4. Validate strategic alignment with architectural goals

## Output Format

Provide your revised analysis in the following JSON format:

```json
{"revision_metadata": {"processed_feedback": {"pattern_improvements": ["strings"], "evidence_enhancements": ["strings"], "integration_enhancements": ["strings"], "strategy_refinements": ["strings"], "prioritization_adjustments": ["strings"], "synthesis_improvements": ["strings"]}, "validation_steps": ["strings"]}, "holistic_strategic_adaptations": {"cross_perspective_patterns": [{"pattern": "string", "evidence": {"primary_source": {"agent": "string", "perspective": "string", "key_findings": ["strings"]}, "supporting_sources": [{"agent": "string", "perspective": "string", "corroborating_evidence": ["strings"]}]}, "significance": "string", "affected_areas": ["strings"], "revision_note": "string"}], "integration_insights": [{"insight": "string", "source_perspectives": [{"agent": "string", "perspective": "string", "contribution": "string"}], "architectural_implications": ["strings"], "revision_note": "string"}], "adaptation_strategies": [{"strategy": "string", "addresses_patterns": ["strings"], "implementation_approach": "string", "perspective_benefits": [{"perspective": "string", "specific_benefits": ["strings"]}], "revision_note": "string"}], "prioritization": {"critical_adaptations": [{"adaptation": "string", "urgency_factors": ["strings"], "cross_perspective_impact": "string", "revision_note": "string"}], "secondary_adaptations": [{"adaptation": "string", "rationale": "string", "revision_note": "string"}]}, "synthesis": {"key_observations": ["strings"], "strategic_themes": ["strings"], "implementation_roadmap": [{"phase": "string", "focus": "string", "expected_outcomes": ["strings"]}], "revision_note": "string"}}}
```

## Revision Guidelines

### Pattern Improvements
- Add missing cross-perspective patterns identified in reflection
- Enhance pattern descriptions to better capture cross-perspective insights
- Ensure each pattern clearly identifies its multi-perspective origins

### Evidence Enhancements
- Strengthen weak evidence instances as indicated in reflection
- Ensure evidence includes concrete citations from agent outputs
- Balance evidence across different agent perspectives

### Integration Enhancements
- Address missed connections between agent perspectives
- Incorporate suggested integration opportunities
- Ensure balanced representation across different types of agent perspectives

### Strategy Refinements
- Address identified issues with problematic strategies
- Fill identified strategy gaps
- Ensure strategies leverage insights from multiple perspectives

### Prioritization Adjustments
- Implement suggested priority changes
- Strengthen rationale for prioritization decisions
- Ensure priorities reflect genuine cross-perspective impact

### Synthesis Improvements
- Enhance coherence of the overall strategic framework
- Address roadmap feasibility concerns
- Strengthen alignment with architectural goals

## Validation Checklist

Before finalizing your revised analysis:
1. Verify that all missed patterns have been incorporated
2. Confirm that weak evidence instances have been strengthened
3. Check that missed perspective connections have been addressed
4. Ensure problematic strategies have been refined
5. Verify that prioritization adjustments have been implemented
6. Confirm that synthesis improvements enhance coherence and feasibility
7. Validate that all revisions maintain cross-perspective integration focus
8. Ensure strategic alignment with architectural goals

## Self-Correction Principles

1. Focus on enhancing multi-perspective integration
2. Maintain balance across different agent perspectives
3. Ensure all strategic adaptations have strong cross-perspective evidence
4. Prioritize based on genuine architectural impact
5. Ensure implementation roadmap is feasible and coherent
6. Maintain alignment with architectural goals
7. Provide revision notes explaining rationale for significant changes
"""

phase_one_evolution_revision_schema = {
  "type": "object",
  "properties": {
    "revision_metadata": {
      "type": "object",
      "properties": {
        "processed_feedback": {
          "type": "object",
          "properties": {
            "pattern_improvements": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "minItems": 1
            },
            "evidence_enhancements": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "minItems": 1
            },
            "integration_enhancements": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "minItems": 1
            },
            "strategy_refinements": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "minItems": 1
            },
            "prioritization_adjustments": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "minItems": 1
            },
            "synthesis_improvements": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "minItems": 1
            }
          },
          "required": ["pattern_improvements", "evidence_enhancements", "integration_enhancements", "strategy_refinements", "prioritization_adjustments", "synthesis_improvements"]
        },
        "validation_steps": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "minItems": 1
        }
      },
      "required": ["processed_feedback", "validation_steps"]
    },
    "holistic_strategic_adaptations": {
      "type": "object",
      "properties": {
        "cross_perspective_patterns": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pattern": {
                "type": "string"
              },
              "evidence": {
                "type": "object",
                "properties": {
                  "primary_source": {
                    "type": "object",
                    "properties": {
                      "agent": {
                        "type": "string"
                      },
                      "perspective": {
                        "type": "string"
                      },
                      "key_findings": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      }
                    },
                    "required": ["agent", "perspective", "key_findings"]
                  },
                  "supporting_sources": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "properties": {
                        "agent": {
                          "type": "string"
                        },
                        "perspective": {
                          "type": "string"
                        },
                        "corroborating_evidence": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          }
                        }
                      },
                      "required": ["agent", "perspective", "corroborating_evidence"]
                    }
                  }
                },
                "required": ["primary_source", "supporting_sources"]
              },
              "significance": {
                "type": "string"
              },
              "affected_areas": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "revision_note": {
                "type": "string"
              }
            },
            "required": ["pattern", "evidence", "significance", "affected_areas", "revision_note"]
          }
        },
        "integration_insights": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "insight": {
                "type": "string"
              },
              "source_perspectives": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "agent": {
                      "type": "string"
                    },
                    "perspective": {
                      "type": "string"
                    },
                    "contribution": {
                      "type": "string"
                    }
                  },
                  "required": ["agent", "perspective", "contribution"]
                }
              },
              "architectural_implications": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "revision_note": {
                "type": "string"
              }
            },
            "required": ["insight", "source_perspectives", "architectural_implications", "revision_note"]
          }
        },
        "adaptation_strategies": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "strategy": {
                "type": "string"
              },
              "addresses_patterns": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "implementation_approach": {
                "type": "string"
              },
              "perspective_benefits": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "perspective": {
                      "type": "string"
                    },
                    "specific_benefits": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    }
                  },
                  "required": ["perspective", "specific_benefits"]
                }
              },
              "revision_note": {
                "type": "string"
              }
            },
            "required": ["strategy", "addresses_patterns", "implementation_approach", "perspective_benefits", "revision_note"]
          }
        },
        "prioritization": {
          "type": "object",
          "properties": {
            "critical_adaptations": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "adaptation": {
                    "type": "string"
                  },
                  "urgency_factors": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "cross_perspective_impact": {
                    "type": "string"
                  },
                  "revision_note": {
                    "type": "string"
                  }
                },
                "required": ["adaptation", "urgency_factors", "cross_perspective_impact", "revision_note"]
              }
            },
            "secondary_adaptations": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "adaptation": {
                    "type": "string"
                  },
                  "rationale": {
                    "type": "string"
                  },
                  "revision_note": {
                    "type": "string"
                  }
                },
                "required": ["adaptation", "rationale", "revision_note"]
              }
            }
          },
          "required": ["critical_adaptations", "secondary_adaptations"]
        },
        "synthesis": {
          "type": "object",
          "properties": {
            "key_observations": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "strategic_themes": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "implementation_roadmap": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "phase": {
                    "type": "string"
                  },
                  "focus": {
                    "type": "string"
                  },
                  "expected_outcomes": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  }
                },
                "required": ["phase", "focus", "expected_outcomes"]
              }
            },
            "revision_note": {
              "type": "string"
            }
          },
          "required": ["key_observations", "strategic_themes", "implementation_roadmap", "revision_note"]
        }
      },
      "required": ["cross_perspective_patterns", "integration_insights", "adaptation_strategies", "prioritization", "synthesis"]
    }
  },
  "required": ["revision_metadata", "holistic_strategic_adaptations"]
}