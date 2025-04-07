# Garden Foundation Refinement Agent has three system prompts:
# 1. the Task Foundation Refinement Prompt is used to analyze phase one outputs and the corresponding phase zero feedback to mediate targeted system refinement actions
# 2. the Task Foundation Reflection Prompt is used to refine the task foundation refinement
# 3. the Task Foundation Revision Prompt which is used post-reflection to validate refinement self-corrections

task_foundation_refinement_prompt = """
# Garden Foundation Refinement Agent System Prompt

You are the Garden Foundation Refinement Agent, serving as the critical refinement control point for phase one of the development process. Your role is to detect and respond to only genuinely critical phase one failures, trace them to their root cause, and provide focused refinement guidance to specific phase one agents.

## Core Responsibilities

1. Critical Failure Detection
2. Root Cause Analysis
3. Refinement Action Selection

## Critical Failure Categories

Only the following conditions qualify as critical failures:

1. Architectural Impossibility
   - Fundamentally contradictory requirements
   - Technically infeasible specifications
   - Irreconcilable component dependencies

2. Core Capability Blockers
   - Missing essential functionality
   - Unimplementable core features
   - Critical path blockages

3. Resource Invalidation
   - Insufficient resource allocation
   - Incompatible resource requirements
   - Unresolvable resource conflicts

4. Integration Impossibility
   - Incompatible interface specifications
   - Unresolvable protocol conflicts
   - Breaking dependency chains

## Root Cause Mapping

Failures must be traced to exactly one of:
1. Garden Planner Agent (Task Elaboration)
   - Task interpretation errors
   - Feature scope misunderstanding
   - User intent misalignment

2. Environmental Analysis Agent (Core Requirements)
   - Missing core requirements
   - Requirement misspecification
   - Critical requirement conflicts

3. Root System Architect (Data Flow)
   - Data flow impossibilities
   - Persistence strategy issues
   - Transformation requirement gaps

4. Tree Placement Planner (Component Structure)
   - Component relationship errors
   - Dependency cycle issues
   - Interface specification problems

## Refinement Actions

Limited to the following specific actions:

1. reanalyze_task
   - Target: Garden Planner Agent
   - When: Task scope or intent misunderstood
   - Provides: Specific task clarification

2. revise_environment
   - Target: Environmental Analysis Agent
   - When: Technical environment insufficient
   - Provides: Specific capability requirements

3. restructure_data_flow
   - Target: Root System Architect
   - When: Data flow patterns invalid
   - Provides: Specific flow corrections

4. reorganize_components
   - Target: Tree Placement Planner
   - When: Component structure impossible
   - Provides: Specific structural adjustments

## Output Format

```json
{"refinement_analysis": {"critical_failure": {"category": "architectural_impossibility|core_capability_blockers|resource_invalidation|integration_impossibility","description": "string","evidence": [{"source": "string","observation": "string","impact": "string"}],"phase_zero_signals": [{"agent": "string","supporting_evidence": ["strings"]}]},"root_cause": {"responsible_agent": "garden_planner|environmental_analysis|root_system_architect|tree_placement_planner","failure_point": "string","causal_chain": ["strings"],"verification_steps": ["strings"]},"refinement_action": {"action": "reanalyze_task|revise_environment|restructure_data_flow|reorganize_components","justification": "string","specific_guidance": {"current_state": "string","required_state": "string","adaptation_path": ["strings"]}}}}
```

## Analysis Principles

1. Default to no action unless critical failure is clearly evidenced
2. Require multiple, concrete evidence points for critical failure designation
3. Trace root cause thoroughly before assigning responsibility
4. Provide specific, actionable refinement guidance
5. Consider only phase one architectural issues
6. Ignore non-critical optimization or improvement opportunities

## Decision Criteria

Before issuing any refinement action:
1. Verify true architectural impossibility
2. Confirm multiple evidence sources
3. Validate phase zero signal support
4. Ensure clear responsibility assignment
5. Develop specific correction guidance
6. Verify action necessity
"""

task_foundation_refinement_schema = {
  "type": "object",
  "properties": {
    "refinement_analysis": {
      "type": "object",
      "properties": {
        "critical_failure": {
          "type": "object",
          "properties": {
            "category": {
              "type": "string",
              "enum": [
                "architectural_impossibility",
                "core_capability_blockers",
                "resource_invalidation",
                "integration_impossibility"
              ]
            },
            "description": {
              "type": "string"
            },
            "evidence": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "source": {
                    "type": "string"
                  },
                  "observation": {
                    "type": "string"
                  },
                  "impact": {
                    "type": "string"
                  }
                },
                "required": ["source", "observation", "impact"]
              }
            },
            "phase_zero_signals": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "agent": {
                    "type": "string"
                  },
                  "supporting_evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  }
                },
                "required": ["agent", "supporting_evidence"]
              }
            }
          },
          "required": ["category", "description", "evidence", "phase_zero_signals"]
        },
        "root_cause": {
          "type": "object",
          "properties": {
            "responsible_agent": {
              "type": "string",
              "enum": [
                "garden_planner",
                "environmental_analysis",
                "root_system_architect",
                "tree_placement_planner"
              ]
            },
            "failure_point": {
              "type": "string"
            },
            "causal_chain": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "verification_steps": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "required": ["responsible_agent", "failure_point", "causal_chain", "verification_steps"]
        },
        "refinement_action": {
          "type": "object",
          "properties": {
            "action": {
              "type": "string",
              "enum": [
                "reanalyze_task",
                "revise_environment",
                "restructure_data_flow",
                "reorganize_components"
              ]
            },
            "justification": {
              "type": "string"
            },
            "specific_guidance": {
              "type": "object",
              "properties": {
                "current_state": {
                  "type": "string"
                },
                "required_state": {
                  "type": "string"
                },
                "adaptation_path": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              },
              "required": ["current_state", "required_state", "adaptation_path"]
            }
          },
          "required": ["action", "justification", "specific_guidance"]
        }
      },
      "required": ["critical_failure", "root_cause", "refinement_action"]
    }
  },
  "required": ["refinement_analysis"]
}

task_foundation_reflection_prompt = """
# Foundation Refinement Reflection Agent
You are the Reflection Agent for the Garden Foundation Refinement process, validating critical failure detection and refinement actions.

## Core Responsibilities
1. Validate critical failure identification
2. Verify root cause analysis
3. Assess refinement action appropriateness
4. Ensure evidence completeness
5. Validate causal chains

## Output Format
```json
{"reflection_results": {"failure_analysis": {"critical_qualification": [{"severity": "high|medium|low","category": "string","issue": "string","recommendation": "string"}],"evidence_validation": [{"severity": "high|medium|low","evidence_point": "string","issue": "string","recommendation": "string"}]},"causality_validation": {"root_cause_verification": [{"severity": "high|medium|low","assigned_cause": "string","issue": "string","recommendation": "string"}],"causal_chain_integrity": [{"severity": "high|medium|low","chain_component": "string","issue": "string","recommendation": "string"}]},"action_assessment": {"refinement_appropriateness": [{"severity": "high|medium|low","action": "string","issue": "string","recommendation": "string"}],"guidance_specificity": [{"severity": "high|medium|low","guidance_aspect": "string","issue": "string","recommendation": "string"}]}}}
```

## Validation Criteria

### Critical Failures
- Verify architectural impossibility
- Confirm core capability blockers
- Validate resource invalidation
- Assess integration impossibility

### Root Cause Analysis
- Clear responsibility assignment
- Complete causal chain
- Verifiable evidence trail
- Phase zero signal support

### Action Verification
- Action necessity confirmed
- Target agent appropriate
- Specific guidance provided
- Clear adaptation path

### Evidence Requirements
- Multiple concrete points
- Clear impact demonstration
- Traceable observations
- Verifiable sources
"""

task_foundation_reflection_schema = {
  "type": "object",
  "properties": {
    "reflection_results": {
      "type": "object",
      "properties": {
        "failure_analysis": {
          "type": "object",
          "properties": {
            "critical_qualification": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "category": {
                    "type": "string"
                  },
                  "issue": {
                    "type": "string"
                  },
                  "recommendation": {
                    "type": "string"
                  }
                },
                "required": ["severity", "category", "issue", "recommendation"]
              }
            },
            "evidence_validation": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "evidence_point": {
                    "type": "string"
                  },
                  "issue": {
                    "type": "string"
                  },
                  "recommendation": {
                    "type": "string"
                  }
                },
                "required": ["severity", "evidence_point", "issue", "recommendation"]
              }
            }
          },
          "required": ["critical_qualification", "evidence_validation"]
        },
        "causality_validation": {
          "type": "object",
          "properties": {
            "root_cause_verification": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "assigned_cause": {
                    "type": "string"
                  },
                  "issue": {
                    "type": "string"
                  },
                  "recommendation": {
                    "type": "string"
                  }
                },
                "required": ["severity", "assigned_cause", "issue", "recommendation"]
              }
            },
            "causal_chain_integrity": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "chain_component": {
                    "type": "string"
                  },
                  "issue": {
                    "type": "string"
                  },
                  "recommendation": {
                    "type": "string"
                  }
                },
                "required": ["severity", "chain_component", "issue", "recommendation"]
              }
            }
          },
          "required": ["root_cause_verification", "causal_chain_integrity"]
        },
        "action_assessment": {
          "type": "object",
          "properties": {
            "refinement_appropriateness": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "action": {
                    "type": "string"
                  },
                  "issue": {
                    "type": "string"
                  },
                  "recommendation": {
                    "type": "string"
                  }
                },
                "required": ["severity", "action", "issue", "recommendation"]
              }
            },
            "guidance_specificity": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "guidance_aspect": {
                    "type": "string"
                  },
                  "issue": {
                    "type": "string"
                  },
                  "recommendation": {
                    "type": "string"
                  }
                },
                "required": ["severity", "guidance_aspect", "issue", "recommendation"]
              }
            }
          },
          "required": ["refinement_appropriateness", "guidance_specificity"]
        }
      },
      "required": ["failure_analysis", "causality_validation", "action_assessment"]
    }
  },
  "required": ["reflection_results"]
}

task_foundation_revision_prompt = """# Garden Foundation Revision Agent System Prompt

You are the Garden Foundation Revision Agent, responsible for self-correcting the refinement analysis based on reflection feedback. Your role is to integrate reflection insights into a revised refinement action that addresses identified issues while maintaining focus on genuine critical failures.

## Core Responsibilities

1. Process Reflection Feedback
2. Validate Critical Failure Classification
3. Correct Root Cause Analysis
4. Refine Action Guidance
5. Ensure Evidence Completeness

## Revision Categories

Address feedback based on severity:

1. High Severity Issues
   - Require immediate and comprehensive correction
   - May invalidate entire refinement sections
   - Must be resolved before proceeding

2. Medium Severity Issues
   - Require significant modification
   - May impact refinement effectiveness
   - Should be addressed if possible

3. Low Severity Issues
   - Represent opportunities for improvement
   - May clarify but not fundamentally change analysis
   - Should be addressed when they improve outcome clarity

## Revision Process

For each reflection feedback item:

1. Critical Failure Validation
   - Confirm or revise critical failure category
   - Strengthen evidence citations
   - Clarify impact descriptions
   - Verify phase zero signals alignment

2. Root Cause Reassessment
   - Validate or reassign agent responsibility
   - Strengthen causal chain logic
   - Enhance verification steps
   - Ensure clear failure point identification

3. Action Guidance Enhancement
   - Verify action appropriateness
   - Increase guidance specificity
   - Develop concrete adaptation steps
   - Ensure clear path from current to required state

## Output Format

```json
{"revision_results": {"acceptance_analysis": {"high_severity_issues": {"addressed": [{"reflection_point": "string","correction_applied": "string","impact_on_analysis": "string"}],"unaddressed": [{"reflection_point": "string","reason": "string"}]},"medium_severity_issues": {"addressed": [{"reflection_point": "string","correction_applied": "string","impact_on_analysis": "string"}],"unaddressed": [{"reflection_point": "string","reason": "string"}]},"low_severity_issues": {"addressed": [{"reflection_point": "string","correction_applied": "string","impact_on_analysis": "string"}],"unaddressed": [{"reflection_point": "string","reason": "string"}]}},"revised_refinement": {"critical_failure": {"category": "architectural_impossibility|core_capability_blockers|resource_invalidation|integration_impossibility","description": "string","evidence": [{"source": "string","observation": "string","impact": "string"}],"phase_zero_signals": [{"agent": "string","supporting_evidence": ["strings"]}]},"root_cause": {"responsible_agent": "garden_planner|environmental_analysis|root_system_architect|tree_placement_planner","failure_point": "string","causal_chain": ["strings"],"verification_steps": ["strings"]},"refinement_action": {"action": "reanalyze_task|revise_environment|restructure_data_flow|reorganize_components","justification": "string","specific_guidance": {"current_state": "string","required_state": "string","adaptation_path": ["strings"]}}},"revision_summary": {"confidence_assessment": "high|medium|low","remaining_uncertainties": ["strings"],"key_improvements": ["strings"]}}}
```

## Revision Principles

1. Address all high severity issues without exception
2. Integrate medium severity corrections that strengthen analysis
3. Incorporate low severity improvements that enhance clarity
4. Maintain focus on genuine critical failures only
5. Preserve original analysis aspects validated by reflection
6. Strengthen causal logic and evidence connections
7. Enhance specificity of guidance and adaptation paths

## Decision Criteria

Before finalizing revision:
1. Verify all high severity issues addressed or justified
2. Confirm critical failure still meets threshold after corrections
3. Validate root cause assignment with strengthened evidence
4. Ensure refinement action is specific and implementable
5. Verify all evidence chains are complete and logical
6. Assess overall confidence in revised analysis"""

task_foundation_revision_schema = {
  "type": "object",
  "properties": {
    "revision_results": {
      "type": "object",
      "properties": {
        "acceptance_analysis": {
          "type": "object",
          "properties": {
            "high_severity_issues": {
              "type": "object",
              "properties": {
                "addressed": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "reflection_point": {
                        "type": "string"
                      },
                      "correction_applied": {
                        "type": "string"
                      },
                      "impact_on_analysis": {
                        "type": "string"
                      }
                    },
                    "required": ["reflection_point", "correction_applied", "impact_on_analysis"]
                  }
                },
                "unaddressed": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "reflection_point": {
                        "type": "string"
                      },
                      "reason": {
                        "type": "string"
                      }
                    },
                    "required": ["reflection_point", "reason"]
                  }
                }
              },
              "required": ["addressed", "unaddressed"]
            },
            "medium_severity_issues": {
              "type": "object",
              "properties": {
                "addressed": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "reflection_point": {
                        "type": "string"
                      },
                      "correction_applied": {
                        "type": "string"
                      },
                      "impact_on_analysis": {
                        "type": "string"
                      }
                    },
                    "required": ["reflection_point", "correction_applied", "impact_on_analysis"]
                  }
                },
                "unaddressed": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "reflection_point": {
                        "type": "string"
                      },
                      "reason": {
                        "type": "string"
                      }
                    },
                    "required": ["reflection_point", "reason"]
                  }
                }
              },
              "required": ["addressed", "unaddressed"]
            },
            "low_severity_issues": {
              "type": "object",
              "properties": {
                "addressed": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "reflection_point": {
                        "type": "string"
                      },
                      "correction_applied": {
                        "type": "string"
                      },
                      "impact_on_analysis": {
                        "type": "string"
                      }
                    },
                    "required": ["reflection_point", "correction_applied", "impact_on_analysis"]
                  }
                },
                "unaddressed": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "reflection_point": {
                        "type": "string"
                      },
                      "reason": {
                        "type": "string"
                      }
                    },
                    "required": ["reflection_point", "reason"]
                  }
                }
              },
              "required": ["addressed", "unaddressed"]
            }
          },
          "required": ["high_severity_issues", "medium_severity_issues", "low_severity_issues"]
        },
        "revised_refinement": {
          "type": "object",
          "properties": {
            "critical_failure": {
              "type": "object",
              "properties": {
                "category": {
                  "type": "string",
                  "enum": [
                    "architectural_impossibility",
                    "core_capability_blockers",
                    "resource_invalidation",
                    "integration_impossibility"
                  ]
                },
                "description": {
                  "type": "string"
                },
                "evidence": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "source": {
                        "type": "string"
                      },
                      "observation": {
                        "type": "string"
                      },
                      "impact": {
                        "type": "string"
                      }
                    },
                    "required": ["source", "observation", "impact"]
                  }
                },
                "phase_zero_signals": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "agent": {
                        "type": "string"
                      },
                      "supporting_evidence": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      }
                    },
                    "required": ["agent", "supporting_evidence"]
                  }
                }
              },
              "required": ["category", "description", "evidence", "phase_zero_signals"]
            },
            "root_cause": {
              "type": "object",
              "properties": {
                "responsible_agent": {
                  "type": "string",
                  "enum": [
                    "garden_planner",
                    "environmental_analysis",
                    "root_system_architect",
                    "tree_placement_planner"
                  ]
                },
                "failure_point": {
                  "type": "string"
                },
                "causal_chain": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "verification_steps": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              },
              "required": ["responsible_agent", "failure_point", "causal_chain", "verification_steps"]
            },
            "refinement_action": {
              "type": "object",
              "properties": {
                "action": {
                  "type": "string",
                  "enum": [
                    "reanalyze_task",
                    "revise_environment",
                    "restructure_data_flow",
                    "reorganize_components"
                  ]
                },
                "justification": {
                  "type": "string"
                },
                "specific_guidance": {
                  "type": "object",
                  "properties": {
                    "current_state": {
                      "type": "string"
                    },
                    "required_state": {
                      "type": "string"
                    },
                    "adaptation_path": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    }
                  },
                  "required": ["current_state", "required_state", "adaptation_path"]
                }
              },
              "required": ["action", "justification", "specific_guidance"]
            }
          },
          "required": ["critical_failure", "root_cause", "refinement_action"]
        },
        "revision_summary": {
          "type": "object",
          "properties": {
            "confidence_assessment": {
              "type": "string",
              "enum": ["high", "medium", "low"]
            },
            "remaining_uncertainties": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "key_improvements": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "required": ["confidence_assessment", "remaining_uncertainties", "key_improvements"]
        }
      },
      "required": ["acceptance_analysis", "revised_refinement", "revision_summary"]
    }
  },
  "required": ["revision_results"]
}