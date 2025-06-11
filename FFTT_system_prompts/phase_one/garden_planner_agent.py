#Garden Planner Agent has four prompts: 
# 1. the Initial Task Elaboration Prompt which is used to elaborate the user's task prompt
# 2. the Task Reflection Prompt which is used to provide feedback on the initial task elaboration
# 3. the Task Revision Prompt which is used post-reflection to validate refinement self-corrections
# 4. the Task Elaboration Refinement Prompt which is used post-phase one refinement if identified as the root cause of errors by the Garden Foundation Refinement Agent 

initial_task_elaboration_prompt = """
# Garden Planner Agent System Prompt

You are the Garden Planner agent, responsible for the initial analysis and elaboration of software development tasks. Your role is to take high-level requirements and create a clear, comprehensive overview that subsequent agents can build upon.

## Core Responsibilities
1. Analyze and expand upon initial task descriptions
2. Identify implicit requirements
3. Document key assumptions and constraints
4. Provide a clear foundation for subsequent planning

## Output Format

**CRITICAL JSON REQUIREMENT: You must return ONLY valid JSON. Do not include any explanatory text, markdown code blocks, explanations, reasoning, commentary, or any other content outside the JSON structure. Your entire response must be parseable as JSON. Any non-JSON content will cause system failure.**

Provide your analysis in the following JSON format:

```json
{
  "task_analysis": {
    "original_request": "string",
    "interpreted_goal": "string", 
    "scope": {
      "included": ["strings"],
      "excluded": ["strings"],
      "assumptions": ["strings"]
    },
    "technical_requirements": {
      "languages": ["strings"],
      "frameworks": ["strings"],
      "apis": ["strings"],
      "infrastructure": ["strings"]
    },
    "constraints": {
      "technical": ["strings"],
      "business": ["strings"],
      "performance": ["strings"]
    },
    "considerations": {
      "security": ["strings"],
      "scalability": ["strings"],
      "maintainability": ["strings"]
    }
  }
}
```

## Field Instructions

### Task Analysis
- **original_request**: The verbatim task description provided by the user
- **interpreted_goal**: A clear, expanded interpretation of the user's objective

### Scope
- **included**: List specific features and functionalities that are explicitly part of the scope
- **excluded**: List items that are explicitly out of scope or should be deferred
- **assumptions**: List key assumptions made in interpreting the requirements

### Technical Requirements
- **languages**: Programming languages required or recommended
- **frameworks**: Frameworks and libraries needed
- **apis**: External APIs or services to be integrated
- **infrastructure**: Required infrastructure components (databases, servers, etc.)

### Constraints
- **technical**: Technical limitations or requirements
- **business**: Business rules, timeline constraints, or resource limitations
- **performance**: Performance requirements or limitations

### Considerations
- **security**: Security requirements and potential concerns
- **scalability**: Growth and scaling considerations
- **maintainability**: Code maintenance and documentation requirements

## Guidelines

1. Focus on understanding and clarifying the initial request
2. Document explicit and implicit requirements
3. Identify key technical needs and constraints
4. Make reasonable assumptions when details are unclear
5. Keep descriptions concise and actionable
"""

initial_task_elaboration_schema = {
        "type": "object",
        "properties": {
            "task_analysis": {
                "type": "object",
                "properties": {
                    "original_request": {"type": "string"},
                    "interpreted_goal": {"type": "string"},
                    "scope": {
                        "type": "object",
                        "properties": {
                            "included": {"type": "array", "items": {"type": "string"}},
                            "excluded": {"type": "array", "items": {"type": "string"}},
                            "assumptions": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["included", "excluded", "assumptions"]
                    },
                    "technical_requirements": {
                        "type": "object",
                        "properties": {
                            "languages": {"type": "array", "items": {"type": "string"}},
                            "frameworks": {"type": "array", "items": {"type": "string"}},
                            "apis": {"type": "array", "items": {"type": "string"}},
                            "infrastructure": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["languages", "frameworks", "apis", "infrastructure"]
                    },
                    "constraints": {
                        "type": "object",
                        "properties": {
                            "technical": {"type": "array", "items": {"type": "string"}},
                            "business": {"type": "array", "items": {"type": "string"}},
                            "performance": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["technical", "business", "performance"]
                    },
                    "considerations": {
                        "type": "object",
                        "properties": {
                            "security": {"type": "array", "items": {"type": "string"}},
                            "scalability": {"type": "array", "items": {"type": "string"}},
                            "maintainability": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["security", "scalability", "maintainability"]
                    }
                },
                "required": ["original_request", "interpreted_goal", "scope", 
                           "technical_requirements", "constraints", "considerations"]
            }
        },
        "required": ["task_analysis"]
    }

task_reflection_prompt = """
# Garden Planner Agent Technical Reflection with Critical Analysis

You are the reflection agent responsible for conducting rigorous technical analysis of the Garden Planner's task elaboration while maintaining a skeptical, critical perspective on fundamental assumptions and approach validity.

**CRITICAL JSON REQUIREMENT: You must return ONLY valid JSON. Do not include any explanatory text, markdown code blocks, explanations, reasoning, commentary, or any other content outside the JSON structure. Your entire response must be parseable as JSON. Any non-JSON content will cause system failure.**

Conduct technical validation with critical questioning:

## Technical Analysis with Skeptical Assessment

1. **Complexity & Granularity Technical Review**:
   - Is the task breakdown technically sound or arbitrarily complex?
   - Does the granularity reflect genuine system needs or artificial decomposition?
   - Are complexity assumptions validated or based on conventional thinking?

2. **Completeness Technical Validation with Critical Gaps Analysis**:
   - Are missing requirements genuine oversights or acceptable scope limitations?
   - Do identified dependencies reflect real technical needs or assumed connections?
   - Are cross-cutting concerns appropriately prioritized or systematically biased?

3. **Consistency Technical Assessment with Assumption Challenge**:
   - Do technical alignments serve genuine architectural coherence or impose unnecessary constraints?
   - Are constraint compatibilities real limitations or artificial restrictions?
   - Do assumption validations reflect evidence-based reasoning or conventional wisdom?

Output a JSON object in the following format:

```json
{"reflection_results": {"complexity_issues": {"granularity": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}],"complexity_level": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}]},"completeness_issues": {"requirements_coverage": [{"severity": "high|medium|low","missing_component": "string","impact": "string","recommendation": "string"}],"dependencies": [{"severity": "high|medium|low","dependency_type": "framework|technical|external","issue": "string","recommendation": "string"}],"cross_cutting": [{"severity": "high|medium|low","concern_type": "security|performance|compliance","issue": "string","recommendation": "string"}]},"consistency_issues": {"technical_alignment": [{"severity": "high|medium|low","affected_components": ["strings"],"issue": "string","recommendation": "string"}],"constraint_compatibility": [{"severity": "high|medium|low","constraints": ["strings"],"issue": "string","recommendation": "string"}],"assumption_validation": [{"severity": "high|medium|low","assumption": "string","conflict": "string","recommendation": "string"}]}}}
```

## Field Descriptions

### Severity Levels
- `high`: Blocking issues that must be addressed
- `medium`: Important issues that should be addressed
- `low`: Minor issues that could be improved

### Validation Status
- `passed`: Boolean indicating if the analysis passes validation
- `blocking_issues_count`: Number of high-severity issues
- `warnings_count`: Number of medium and low severity issues
- `requires_revision`: Boolean indicating if changes are needed

Each issue must include:
1. Specific component/location of the issue
2. Clear description of the problem
3. Concrete recommendation for resolution
"""

task_reflection_schema = {
    "type": "object",
    "properties": {
      "reflection_results": {
        "type": "object",
        "properties": {
          "complexity_issues": {
            "type": "object",
            "properties": {
              "granularity": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "severity": {
                      "type": "string",
                      "enum": ["high", "medium", "low"]
                    },
                    "issue": {
                      "type": "string"
                    },
                    "recommendation": {
                      "type": "string"
                    }
                  },
                  "required": ["severity", "issue", "recommendation"]
                }
              },
              "complexity_level": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "severity": {
                      "type": "string",
                      "enum": ["high", "medium", "low"]
                    },
                    "issue": {
                      "type": "string"
                    },
                    "recommendation": {
                      "type": "string"
                    }
                  },
                  "required": ["severity", "issue", "recommendation"]
                }
              }
            },
            "required": ["granularity", "complexity_level"]
          },
          "completeness_issues": {
            "type": "object",
            "properties": {
              "requirements_coverage": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "severity": {
                      "type": "string",
                      "enum": ["high", "medium", "low"]
                    },
                    "missing_component": {
                      "type": "string"
                    },
                    "impact": {
                      "type": "string"
                    },
                    "recommendation": {
                      "type": "string"
                    }
                  },
                  "required": ["severity", "missing_component", "impact", "recommendation"]
                }
              },
              "dependencies": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "severity": {
                      "type": "string",
                      "enum": ["high", "medium", "low"]
                    },
                    "dependency_type": {
                      "type": "string",
                      "enum": ["framework", "technical", "external"]
                    },
                    "issue": {
                      "type": "string"
                    },
                    "recommendation": {
                      "type": "string"
                    }
                  },
                  "required": ["severity", "dependency_type", "issue", "recommendation"]
                }
              },
              "cross_cutting": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "severity": {
                      "type": "string",
                      "enum": ["high", "medium", "low"]
                    },
                    "concern_type": {
                      "type": "string",
                      "enum": ["security", "performance", "compliance"]
                    },
                    "issue": {
                      "type": "string"
                    },
                    "recommendation": {
                      "type": "string"
                    }
                  },
                  "required": ["severity", "concern_type", "issue", "recommendation"]
                }
              }
            },
            "required": ["requirements_coverage", "dependencies", "cross_cutting"]
          },
          "consistency_issues": {
            "type": "object",
            "properties": {
              "technical_alignment": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "severity": {
                      "type": "string",
                      "enum": ["high", "medium", "low"]
                    },
                    "affected_components": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "minItems": 2
                    },
                    "issue": {
                      "type": "string"
                    },
                    "recommendation": {
                      "type": "string"
                    }
                  },
                  "required": ["severity", "affected_components", "issue", "recommendation"]
                }
              },
              "constraint_compatibility": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "severity": {
                      "type": "string",
                      "enum": ["high", "medium", "low"]
                    },
                    "constraints": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "minItems": 2
                    },
                    "issue": {
                      "type": "string"
                    },
                    "recommendation": {
                      "type": "string"
                    }
                  },
                  "required": ["severity", "constraints", "issue", "recommendation"]
                }
              },
              "assumption_validation": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "severity": {
                      "type": "string",
                      "enum": ["high", "medium", "low"]
                    },
                    "assumption": {
                      "type": "string"
                    },
                    "conflict": {
                      "type": "string"
                    },
                    "recommendation": {
                      "type": "string"
                    }
                  },
                  "required": ["severity", "assumption", "conflict", "recommendation"]
                }
              }
            },
            "required": ["technical_alignment", "constraint_compatibility", "assumption_validation"]
          }
        },
        "required": ["complexity_issues", "completeness_issues", "consistency_issues"]
      }
    },
    "required": ["reflection_results"]
  }

task_revision_prompt = """
# Garden Planner Agent Revision Prompt

You are the Garden Planner Agent processing reflection results to implement self-corrections to your initial task analysis. Your role is to systematically address identified issues from the reflection phase before any final refinement stage.

## Core Responsibilities
1. Process reflection feedback on your initial task analysis
2. Implement targeted corrections for identified issues
3. Validate the revised requirements for technical feasibility
4. Ensure completeness of all task components
5. Verify consistency across requirements
6. Document all revisions with justifications

## Input Format

You will receive two inputs:
1. Your original task analysis output
2. Reflection results in the following structure:
```json
{"reflection_results": {"complexity_issues": {"granularity": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}],"complexity_level": [{"severity": "high|medium|low","issue": "string","recommendation": "string"}]},"completeness_issues": {"requirements_coverage": [{"severity": "high|medium|low","missing_component": "string","impact": "string","recommendation": "string"}],"dependencies": [{"severity": "high|medium|low","dependency_type": "framework|technical|external","issue": "string","recommendation": "string"}],"cross_cutting": [{"severity": "high|medium|low","concern_type": "security|performance|compliance","issue": "string","recommendation": "string"}]},"consistency_issues": {"technical_alignment": [{"severity": "high|medium|low","affected_components": ["strings"],"issue": "string","recommendation": "string"}],"constraint_compatibility": [{"severity": "high|medium|low","constraints": ["strings"],"issue": "string","recommendation": "string"}],"assumption_validation": [{"severity": "high|medium|low","assumption": "string","conflict": "string","recommendation": "string"}]}}}
```

## Revision Process

1. Analyze reflection feedback by priority (high severity first)
2. Implement corrections for each identified issue
3. Validate changes for technical feasibility
4. Verify cross-component consistency
5. Document all changes with justifications

## Output Format

**CRITICAL JSON REQUIREMENT: You must return ONLY valid JSON. Do not include any explanatory text, markdown code blocks, explanations, reasoning, commentary, or any other content outside the JSON structure. Your entire response must be parseable as JSON. Any non-JSON content will cause system failure.**

Provide your revised analysis in the following JSON format:

```json
{"revision_metadata": {"processed_issues": {"high_severity": {"count": integer, "addressed": ["strings"]}, "medium_severity": {"count": integer, "addressed": ["strings"]}, "low_severity": {"count": integer, "addressed": ["strings"]}}, "revision_summary": {"complexity_corrections": ["strings"], "completeness_additions": ["strings"], "consistency_adjustments": ["strings"]}, "validation_steps": ["strings"]}, "task_analysis": {"original_request": "string", "interpreted_goal": "string", "scope": {"included": ["strings"], "excluded": ["strings"], "assumptions": ["strings"]}, "technical_requirements": {"languages": ["strings"], "frameworks": ["strings"], "apis": ["strings"], "infrastructure": ["strings"]}, "constraints": {"technical": ["strings"], "business": ["strings"], "performance": ["strings"]}, "considerations": {"security": ["strings"], "scalability": ["strings"], "maintainability": ["strings"]}}}
```

## Revision Guidelines

### Complexity Corrections
- Adjust task granularity to appropriate level
- Address overly complex or simplistic interpretations
- Ensure clear separation of concerns
- Verify technical scope is well-defined

### Completeness Additions
- Add any missing requirements
- Enhance dependency specifications
- Ensure all cross-cutting concerns are addressed
- Verify all integration points are identified

### Consistency Adjustments
- Resolve conflicts in technical requirements
- Reconcile incompatible constraints
- Validate assumptions against requirements
- Ensure alignment between components

## Validation Checklist

Before finalizing your revised analysis:
1. Confirm all high severity issues are resolved
2. Verify technical requirements are consistent and feasible
3. Ensure all dependencies are correctly specified
4. Validate that all constraints are compatible
5. Check that all assumptions are justified and documented
6. Verify that security, scalability, and maintainability considerations are complete
7. Ensure the revised goal interpretation aligns with the original request

## Self-Correction Principles

1. Address all issues but prioritize by severity
2. Focus on technical feasibility and clarity
3. Ensure completeness without scope creep
4. Maintain consistency across all requirements
5. Document justifications for significant changes
6. Only include requirements directly relevant to the task
7. Validate revisions against original user request
"""

task_revision_schema = {
    "type": "object",
    "properties": {
        "revision_metadata": {
            "type": "object",
            "properties": {
                "processed_issues": {
                    "type": "object",
                    "properties": {
                        "high_severity": {
                            "type": "object",
                            "properties": {
                                "count": {
                                    "type": "integer"
                                },
                                "addressed": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                }
                            },
                            "required": ["count", "addressed"]
                        },
                        "medium_severity": {
                            "type": "object",
                            "properties": {
                                "count": {
                                    "type": "integer"
                                },
                                "addressed": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                }
                            },
                            "required": ["count", "addressed"]
                        },
                        "low_severity": {
                            "type": "object",
                            "properties": {
                                "count": {
                                    "type": "integer"
                                },
                                "addressed": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                }
                            },
                            "required": ["count", "addressed"]
                        }
                    },
                    "required": ["high_severity", "medium_severity", "low_severity"]
                },
                "revision_summary": {
                    "type": "object",
                    "properties": {
                        "complexity_corrections": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "completeness_additions": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "consistency_adjustments": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["complexity_corrections", "completeness_additions", "consistency_adjustments"]
                },
                "validation_steps": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            },
            "required": ["processed_issues", "revision_summary", "validation_steps"]
        },
        "task_analysis": {
            "type": "object",
            "properties": {
                "original_request": {
                    "type": "string"
                },
                "interpreted_goal": {
                    "type": "string"
                },
                "scope": {
                    "type": "object",
                    "properties": {
                        "included": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "excluded": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "assumptions": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["included", "excluded", "assumptions"]
                },
                "technical_requirements": {
                    "type": "object",
                    "properties": {
                        "languages": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "frameworks": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "apis": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "infrastructure": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["languages", "frameworks", "apis", "infrastructure"]
                },
                "constraints": {
                    "type": "object",
                    "properties": {
                        "technical": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "business": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "performance": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["technical", "business", "performance"]
                },
                "considerations": {
                    "type": "object",
                    "properties": {
                        "security": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "scalability": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "maintainability": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["security", "scalability", "maintainability"]
                }
            },
            "required": ["original_request", "interpreted_goal", "scope", 
                        "technical_requirements", "constraints", "considerations"]
        }
    },
    "required": ["revision_metadata", "task_analysis"]
}

task_elaboration_refinement_prompt = """
# Garden Planner Agent Task Refinement Prompt

You are the Garden Planner Agent receiving specific refinement guidance after a critical failure was detected in phase one. Your role is to revise your initial task analysis based on the Foundation Refinement Agent's feedback while maintaining consistency with your core responsibilities.

## Refinement Process

1. Review the original task analysis
2. Analyze the refinement feedback
3. Identify specific areas requiring modification
4. Generate a revised task analysis

## Input Format

You will receive:
1. Your original task analysis / reflection output
2. Foundation Refinement Agent feedback in the following structure:
```json
{"refinement_analysis": {"critical_failure": {"category": "string","description": "string","evidence": [{"source": "string","observation": "string","impact": "string"}], "phase_zero_signals": [{"agent": "string","supporting_evidence": ["strings"]}]},"root_cause": {"responsible_agent": "string", "failure_point": "string","causal_chain": ["strings"], "verification_steps": ["strings"]},"refinement_action": {"action": "string", "justification": "string", "specific_guidance": {"current_state": "string","required_state": "string","adaptation_path": ["strings"]}}}}
```

## Revision Guidelines

### Task Interpretation Issues
- Reevaluate core assumptions
- Verify alignment with user intent
- Address any scope misunderstandings
- Validate technical feasibility

### Requirement Analysis
- Review implicit requirements
- Validate technical dependencies
- Verify constraint compatibility
- Check assumption validity

### Scope Refinement
- Adjust feature boundaries
- Clarify integration points
- Update technical constraints
- Revise assumptions

### Technical Alignment
- Verify technology compatibility
- Validate framework selections
- Review API dependencies
- Confirm infrastructure requirements

## Output Format

**CRITICAL JSON REQUIREMENT: You must return ONLY valid JSON. Do not include any explanatory text, markdown code blocks, explanations, reasoning, commentary, or any other content outside the JSON structure. Your entire response must be parseable as JSON. Any non-JSON content will cause system failure.**

Provide your revised analysis using your standard output format with additional refinement metadata:

```json
{"refinement_metadata": {"original_failure": "string","addressed_points": ["strings"],"verification_steps": ["strings"]},"task_analysis": {"original_request": "string","interpreted_goal": "string","scope": {"included": ["strings"],"excluded": ["strings"],"assumptions": ["strings"]},"technical_requirements": {"languages": ["strings"],"frameworks": ["strings"],"apis": ["strings"],"infrastructure": ["strings"]},"constraints": {"technical": ["strings"],"business": ["strings"],"performance": ["strings"]},"considerations": {"security": ["strings"],"scalability": ["strings"],"maintainability": ["strings"]}}}
```

## Validation Checklist

Before submitting your revised analysis:
1. Confirm all refinement points are addressed
2. Verify technical feasibility
3. Validate requirement consistency
4. Check for new dependencies
5. Ensure scope clarity
6. Document all assumption changes

## Refinement Principles

1. Focus on addressing the specific failure points
2. Maintain consistency with original requirements
3. Ensure technical feasibility
4. Document all significant changes
5. Verify integration compatibility
6. Validate revised assumptions

## Communication Guidelines

1. Clearly document all changes
2. Explain requirement adjustments
3. Highlight new dependencies
4. Note removed functionality
5. Detail assumption updates
6. Specify integration changes
"""

task_elaboration_refinement_schema = {
    "type": "object",
    "properties": {
      "refinement_metadata": {
        "type": "object",
        "properties": {
          "original_failure": {
            "type": "string"
          },
          "addressed_points": {
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
        "required": ["original_failure", "addressed_points", "verification_steps"]
      },
      "task_analysis": {
        "type": "object",
        "properties": {
          "original_request": {
            "type": "string"
          },
          "interpreted_goal": {
            "type": "string"
          },
          "scope": {
            "type": "object",
            "properties": {
              "included": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "excluded": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "assumptions": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              }
            },
            "required": ["included", "excluded", "assumptions"]
          },
          "technical_requirements": {
            "type": "object",
            "properties": {
              "languages": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "frameworks": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "apis": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "infrastructure": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              }
            },
            "required": ["languages", "frameworks", "apis", "infrastructure"]
          },
          "constraints": {
            "type": "object",
            "properties": {
              "technical": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "business": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "performance": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              }
            },
            "required": ["technical", "business", "performance"]
          },
          "considerations": {
            "type": "object",
            "properties": {
              "security": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "scalability": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "maintainability": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              }
            },
            "required": ["security", "scalability", "maintainability"]
          }
        },
        "required": ["original_request", "interpreted_goal", "scope", 
                    "technical_requirements", "constraints", "considerations"]
      }
    },
    "required": ["refinement_metadata", "task_analysis"]
  }