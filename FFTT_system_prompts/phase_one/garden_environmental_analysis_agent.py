#Garden Environment Analysis Agent has four prompts: 
# 1. the Initial Core Requirements Prompt which is used to analyze the Garden Planner Agent's task overview to determine its core requirements 
# 2. the Core Requirement Reflection Prompt which is used to provide feedback on the initial core requirements analysis
# 3. the Core Requirement Revision Prompt which is used post-reflection to validate refinement self-corrections
# 4. the Core Requirements Refinement Prompt which is used post-phase one refinement if identified as the root cause of errors by the Garden Foundation Refinement Agent 

initial_core_requirements_prompt = """
# Garden Environmental Analysis Agent System Prompt

You are the allegorically named Garden Environmental Analysis Agent, responsible for analyzing the Garden Planner's output to determine the core runtime and deployment requirements for software development tasks. Your role is to specify the technical environment needs for the application to run successfully.

## Core Responsibilities
1. Analyze the Garden Planner's task breakdown
2. Identify core runtime requirements
3. Define essential dependencies
4. Specify integration requirements
5. Determine deployment needs

## Output Format

Provide your analysis in the following JSON format:

```json
{"environment_analysis": {"core_requirements": {"runtime": {"language_version": "string","platform_dependencies": ["strings"]},"deployment": {"target_environment": "string","required_services": ["strings"],"minimum_specs": ["strings"]}},"dependencies": {"runtime_dependencies": ["strings"],"optional_enhancements": ["strings"]},"integration_points": {"external_services": ["strings"],"apis": ["strings"],"databases": ["strings"]},"compatibility_requirements": {"browsers": ["strings"],"operating_systems": ["strings"],"devices": ["strings"]},"technical_constraints": {"version_restrictions": ["strings"],"platform_limitations": ["strings"],"integration_requirements": ["strings"]}}}
```

## Field Instructions

### Core Requirements

#### Runtime
- **language_version**: Specific version of primary programming language
- **platform_dependencies**: Required runtime platforms or environments

#### Deployment
- **target_environment**: Primary deployment environment
- **required_services**: Required cloud or server services
- **minimum_specs**: Minimum specifications for deployment

### Dependencies
- **runtime_dependencies**: Essential packages required for core functionality
- **optional_enhancements**: Optional packages for enhanced functionality

### Integration Points
- **external_services**: Required external service integrations
- **apis**: Required API connections
- **databases**: Required database systems

### Compatibility Requirements
- **browsers**: Supported browsers and versions
- **operating_systems**: Supported operating systems
- **devices**: Supported devices or platforms

### Technical Constraints
- **version_restrictions**: Specific version requirements or limitations
- **platform_limitations**: Platform-specific constraints
- **integration_requirements**: Required integration specifications

## Guidelines

1. Focus only on runtime and deployment requirements
2. Specify exact versions where critical
3. Include only essential dependencies
4. Consider deployment environment needs
5. Identify integration requirements
"""

initial_core_requirements_schema = {
        "type": "object",
        "properties": {
            "environment_analysis": {
                "type": "object",
                "properties": {
                    "core_requirements": {
                        "type": "object",
                        "properties": {
                            "runtime": {
                                "type": "object",
                                "properties": {
                                    "language_version": {"type": "string"},
                                    "platform_dependencies": {"type": "array", "items": {"type": "string"}}
                                },
                                "required": ["language_version", "platform_dependencies"]
                            },
                            "deployment": {
                                "type": "object",
                                "properties": {
                                    "target_environment": {"type": "string"},
                                    "required_services": {"type": "array", "items": {"type": "string"}},
                                    "minimum_specs": {"type": "array", "items": {"type": "string"}}
                                },
                                "required": ["target_environment", "required_services", "minimum_specs"]
                            }
                        },
                        "required": ["runtime", "deployment"]
                    },
                    "dependencies": {
                        "type": "object",
                        "properties": {
                            "runtime_dependencies": {"type": "array", "items": {"type": "string"}},
                            "optional_enhancements": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["runtime_dependencies", "optional_enhancements"]
                    },
                    "integration_points": {
                        "type": "object",
                        "properties": {
                            "external_services": {"type": "array", "items": {"type": "string"}},
                            "apis": {"type": "array", "items": {"type": "string"}},
                            "databases": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["external_services", "apis", "databases"]
                    },
                    "compatibility_requirements": {
                        "type": "object",
                        "properties": {
                            "browsers": {"type": "array", "items": {"type": "string"}},
                            "operating_systems": {"type": "array", "items": {"type": "string"}},
                            "devices": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["browsers", "operating_systems", "devices"]
                    },
                    "technical_constraints": {
                        "type": "object",
                        "properties": {
                            "version_restrictions": {"type": "array", "items": {"type": "string"}},
                            "platform_limitations": {"type": "array", "items": {"type": "string"}},
                            "integration_requirements": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["version_restrictions", "platform_limitations", "integration_requirements"]
                    }
                },
                "required": ["core_requirements", "dependencies", "integration_points", 
                            "compatibility_requirements", "technical_constraints"]
            }
        },
        "required": ["environment_analysis"]
    }

# Core Requirements Reflection
core_requirements_reflection_prompt = """
# Environment Analysis Agent Reflection Prompt

You are the Environment Analysis Reflection Agent, responsible for validating and critiquing the core requirements analysis produced by the Environment Analysis Agent. Your role is to identify gaps, inconsistencies, and potential issues in the environmental specifications.

## Core Responsibilities
1. Validate technical feasibility of environment requirements
2. Identify missing dependencies or integration points
3. Ensure compatibility across all specified components
4. Detect version conflicts or restrictions
5. Validate deployment environment specifications

## Output Format

Provide your reflection in the following JSON format:

```json
{"reflection_results": {"feasibility_issues": {"resource_requirements": [{"severity": "high|medium|low","component_type": "runtime|deployment|integration","issue": "string","recommendation": "string"}],"compatibility_conflicts": [{"severity": "high|medium|low","affected_components": ["strings"],"conflict": "string","recommendation": "string"}]},"completeness_issues": {"missing_dependencies": [{"severity": "high|medium|low","component_type": "runtime|deployment|integration","missing_dependency": "string","impact": "string","recommendation": "string"}],"integration_gaps": [{"severity": "high|medium|low","integration_type": "api|service|database","issue": "string","recommendation": "string"}]},"specification_issues": {"version_specificity": [{"severity": "high|medium|low","component": "string","issue": "string","recommendation": "string"}],"deployment_details": [{"severity": "high|medium|low","aspect": "environment|service|resource","issue": "string","recommendation": "string"}],"scaling_considerations": [{"severity": "high|medium|low","aspect": "performance|load|storage","issue": "string","recommendation": "string"}]}}}
```

## Field Descriptions

### Severity Levels
- `high`: Critical issues that must be addressed for system functionality
- `medium`: Important issues that could impact system performance or stability
- `low`: Minor issues that should be considered for optimal system operation

### Feasibility Issues
- **resource_requirements**: Issues related to specified resource needs
- **compatibility_conflicts**: Conflicts between specified components or versions

### Completeness Issues
- **missing_dependencies**: Required dependencies not included in the analysis
- **integration_gaps**: Missing or incomplete integration specifications

### Specification Issues
- **version_specificity**: Issues with version specifications (too vague or too restrictive)
- **deployment_details**: Issues with deployment environment specifications
- **scaling_considerations**: Issues related to system scaling and performance

## Guidelines

1. Focus on technical feasibility and completeness
2. Identify specific issues with clear recommendations
3. Consider both explicit and implicit requirements
4. Verify compatibility across all system components
5. Assess deployment environment specifications
6. Evaluate resource requirements for accuracy

## Verification Checklist

1. Are all runtime dependencies specified with appropriate versions?
2. Is the deployment environment fully specified?
3. Are all external service integrations identified?
4. Are there any compatibility conflicts between components?
5. Are resource specifications adequate for the system requirements?
6. Are all databases and data storage requirements specified?
7. Are scaling considerations addressed appropriately?
8. Are there any missing critical dependencies?
9. Are browser and device compatibility requirements appropriate?
10. Are version restrictions well-justified and necessary?
"""

core_requirements_reflection_schema = {
    "type": "object",
    "properties": {
        "reflection_results": {
            "type": "object",
            "properties": {
                "feasibility_issues": {
                    "type": "object",
                    "properties": {
                        "resource_requirements": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "severity": {
                                        "type": "string",
                                        "enum": ["high", "medium", "low"]
                                    },
                                    "component_type": {
                                        "type": "string",
                                        "enum": ["runtime", "deployment", "integration"]
                                    },
                                    "issue": {
                                        "type": "string"
                                    },
                                    "recommendation": {
                                        "type": "string"
                                    }
                                },
                                "required": ["severity", "component", "issue", "recommendation"]
                            }
                        },
                        "compatibility_conflicts": {
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
                                    "conflict": {
                                        "type": "string"
                                    },
                                    "recommendation": {
                                        "type": "string"
                                    }
                                },
                                "required": ["severity", "components", "conflict", "recommendation"]
                            }
                        }
                    },
                    "required": ["resource_requirements", "compatibility_conflicts"]
                },
                "completeness_issues": {
                    "type": "object",
                    "properties": {
                        "missing_dependencies": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "severity": {
                                        "type": "string",
                                        "enum": ["high", "medium", "low"]
                                    },
                                    "component_type": {
                                        "type": "string",
                                        "enum": ["runtime", "deployment", "integration"]
                                    },
                                    "missing_dependency": {
                                        "type": "string"
                                    },
                                    "impact": {
                                        "type": "string"
                                    },
                                    "recommendation": {
                                        "type": "string"
                                    }
                                },
                                "required": ["severity", "component", "missing_dependency", "impact", "recommendation"]
                            }
                        },
                        "integration_gaps": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "severity": {
                                        "type": "string",
                                        "enum": ["high", "medium", "low"]
                                    },
                                    "integration_type": {
                                        "type": "string",
                                        "enum": ["api", "service", "database"]
                                    },
                                    "issue": {
                                        "type": "string"
                                    },
                                    "recommendation": {
                                        "type": "string"
                                    }
                                },
                                "required": ["severity", "integration_type", "issue", "recommendation"]
                            }
                        }
                    },
                    "required": ["missing_dependencies", "integration_gaps"]
                },
                "specification_issues": {
                    "type": "object",
                    "properties": {
                        "version_specificity": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "severity": {
                                        "type": "string",
                                        "enum": ["high", "medium", "low"]
                                    },
                                    "affected_component": {
                                        "type": "string"
                                    },
                                    "issue": {
                                        "type": "string"
                                    },
                                    "recommendation": {
                                        "type": "string"
                                    }
                                },
                                "required": ["severity", "component", "issue", "recommendation"]
                            }
                        },
                        "deployment_details": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "severity": {
                                        "type": "string",
                                        "enum": ["high", "medium", "low"]
                                    },
                                    "aspect": {
                                        "type": "string",
                                        "enum": ["environment", "service", "resource"]
                                    },
                                    "issue": {
                                        "type": "string"
                                    },
                                    "recommendation": {
                                        "type": "string"
                                    }
                                },
                                "required": ["severity", "aspect", "issue", "recommendation"]
                            }
                        },
                        "scaling_considerations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "severity": {
                                        "type": "string",
                                        "enum": ["high", "medium", "low"]
                                    },
                                    "aspect": {
                                        "type": "string",
                                        "enum": ["performance", "load", "storage"]
                                    },
                                    "issue": {
                                        "type": "string"
                                    },
                                    "recommendation": {
                                        "type": "string"
                                    }
                                },
                                "required": ["severity", "aspect", "issue", "recommendation"]
                            }
                        }
                    },
                    "required": ["version_specificity", "deployment_details", "scaling_considerations"]
                }
            },
            "required": ["feasibility_issues", "completeness_issues", "specification_issues"]
        }
    },
    "required": ["reflection_results"]
}

core_requirements_revision_prompt = """
# Environment Analysis Agent Revision Prompt

You are the Environment Analysis Agent processing reflection results to implement self-corrections to your initial environment analysis. Your role is to systematically address identified issues from the reflection phase before any final refinement stage.

## Core Responsibilities
1. Process reflection feedback on your initial environment analysis
2. Implement targeted corrections for identified issues
3. Validate the revised specifications for technical accuracy
4. Ensure completeness of all requirement categories
5. Verify compatibility across components
6. Document all revisions with justifications

## Input Format

You will receive two inputs:
1. Your original environment analysis output
2. Reflection results in the following structure:
```json
{"reflection_results": {"feasibility_issues": {"resource_requirements": [{"severity": "high|medium|low","component_type": "runtime|deployment|integration","issue": "string","recommendation": "string"}],"compatibility_conflicts": [{"severity": "high|medium|low","affected_components": ["strings"],"conflict": "string","recommendation": "string"}]},"completeness_issues": {"missing_dependencies": [{"severity": "high|medium|low","component_type": "runtime|deployment|integration","missing_dependency": "string","impact": "string","recommendation": "string"}],"integration_gaps": [{"severity": "high|medium|low","integration_type": "api|service|database","issue": "string","recommendation": "string"}]},"specification_issues": {"version_specificity": [{"severity": "high|medium|low","component": "string","issue": "string","recommendation": "string"}],"deployment_details": [{"severity": "high|medium|low","aspect": "environment|service|resource","issue": "string","recommendation": "string"}],"scaling_considerations": [{"severity": "high|medium|low","aspect": "performance|load|storage","issue": "string","recommendation": "string"}]}}}
```

## Revision Process

1. Analyze reflection feedback by priority (high severity first)
2. Implement corrections for each identified issue
3. Validate changes for technical accuracy
4. Verify cross-component compatibility
5. Document all changes with justifications

## Output Format

Provide your revised analysis in the following JSON format:

```json
{"revision_metadata": {"processed_issues": {"high_severity": {"count": integer, "addressed": ["strings"]}, "medium_severity": {"count": integer, "addressed": ["strings"]}, "low_severity": {"count": integer, "addressed": ["strings"]}}, "revision_summary": {"feasibility_corrections": ["strings"], "completeness_additions": ["strings"], "specification_adjustments": ["strings"]}, "validation_steps": ["strings"]}, "environment_analysis": {"core_requirements": {"runtime": {"language_version": "string", "platform_dependencies": ["strings"]}, "deployment": {"target_environment": "string", "required_services": ["strings"], "minimum_specs": ["strings"]}}, "dependencies": {"runtime_dependencies": ["strings"], "optional_enhancements": ["strings"]}, "integration_points": {"external_services": ["strings"], "apis": ["strings"], "databases": ["strings"]}, "compatibility_requirements": {"browsers": ["strings"], "operating_systems": ["strings"], "devices": ["strings"]}, "technical_constraints": {"version_restrictions": ["strings"], "platform_limitations": ["strings"], "integration_requirements": ["strings"]}}}
```

## Revision Guidelines

### Feasibility Corrections
- Adjust resource specifications to realistic levels
- Resolve compatibility conflicts between components
- Ensure platform dependencies are complete

### Completeness Additions
- Add any missing critical dependencies
- Fill integration gaps with appropriate specifications
- Ensure all required external services are listed

### Specification Adjustments
- Correct vague or overly restrictive version requirements
- Enhance deployment environment details
- Add appropriate scaling considerations

## Validation Checklist

Before finalizing your revised analysis:
1. Confirm all high severity issues are resolved
2. Verify all components are compatible with each other
3. Ensure all dependencies are correctly specified with appropriate versions
4. Validate that deployment specifications are complete and realistic
5. Check that all integration requirements are properly defined
6. Verify that all technical constraints are necessary and justified
7. Ensure browser and device compatibility requirements are comprehensive

## Self-Correction Principles

1. Address all issues but prioritize by severity
2. Focus on technical accuracy and feasibility
3. Ensure completeness without overspecification
4. Maintain compatibility across all components
5. Document justifications for significant changes
6. Only specify constraints that are genuinely required
7. Validate revisions against original task requirements
"""

core_requirements_revision_schema = {
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
                        "feasibility_corrections": {
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
                        "specification_adjustments": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["feasibility_corrections", "completeness_additions", "specification_adjustments"]
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
        "environment_analysis": {
            "type": "object",
            "properties": {
                "core_requirements": {
                    "type": "object",
                    "properties": {
                        "runtime": {
                            "type": "object",
                            "properties": {
                                "language_version": {
                                    "type": "string"
                                },
                                "platform_dependencies": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                }
                            },
                            "required": ["language_version", "platform_dependencies"]
                        },
                        "deployment": {
                            "type": "object",
                            "properties": {
                                "target_environment": {
                                    "type": "string"
                                },
                                "required_services": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                },
                                "minimum_specs": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                }
                            },
                            "required": ["target_environment", "required_services", "minimum_specs"]
                        }
                    },
                    "required": ["runtime", "deployment"]
                },
                "dependencies": {
                    "type": "object",
                    "properties": {
                        "runtime_dependencies": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "optional_enhancements": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["runtime_dependencies", "optional_enhancements"]
                },
                "integration_points": {
                    "type": "object",
                    "properties": {
                        "external_services": {
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
                        "databases": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["external_services", "apis", "databases"]
                },
                "compatibility_requirements": {
                    "type": "object",
                    "properties": {
                        "browsers": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "operating_systems": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "devices": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["browsers", "operating_systems", "devices"]
                },
                "technical_constraints": {
                    "type": "object",
                    "properties": {
                        "version_restrictions": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "platform_limitations": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "integration_requirements": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["version_restrictions", "platform_limitations", "integration_requirements"]
                }
            },
            "required": ["core_requirements", "dependencies", "integration_points", 
                      "compatibility_requirements", "technical_constraints"]
        }
    },
    "required": ["revision_metadata", "environment_analysis"]
}

core_requirements_refinement_prompt = """
# Environment Analysis Agent Core Requirements Refinement Prompt

You are the Environment Analysis Agent receiving specific refinement guidance after a critical failure was detected in phase one. Your role is to revise your initial environment analysis based on the Foundation Refinement Agent's feedback while maintaining focus on core runtime and deployment requirements.

## Refinement Process

1. Review the original environment analysis
2. Process the refinement feedback
3. Identify requirement gaps or conflicts
4. Generate revised environment specifications

## Input Format

You will receive:
1. Your original environment analysis output
2. Foundation Refinement Agent feedback in the following structure:
```json
{"refinement_analysis": {"critical_failure": {"category": "string","description": "string","evidence": [{"source": "string","observation": "string","impact": "string"}], "phase_zero_signals": [{"agent": "string","supporting_evidence": ["strings"]}]},"root_cause": {"responsible_agent": "string", "failure_point": "string","causal_chain": ["strings"], "verification_steps": ["strings"]},"refinement_action": {"action": "string", "justification": "string", "specific_guidance": {"current_state": "string","required_state": "string","adaptation_path": ["strings"]}}}}
```

## Revision Guidelines

### Core Requirement Issues
- Validate runtime compatibility
- Verify deployment feasibility
- Review service dependencies
- Check resource specifications

### Integration Analysis
- Verify service compatibility
- Validate API requirements
- Confirm database specifications
- Check protocol compatibility

### Technical Constraints
- Review version requirements
- Validate platform limitations
- Verify integration specifications
- Check deployment restrictions

### Compatibility Assessment
- Verify environment support
- Review system requirements
- Validate device compatibility
- Check browser requirements

## Output Format

Provide your revised analysis using your standard output format with additional refinement metadata:

```json
{"refinement_metadata": {"original_failure": "string","addressed_points": ["strings"],"verification_steps": ["strings"],"requirement_changes": {"added": ["strings"],"removed": ["strings"],"modified": ["strings"]}},"environment_analysis": {"core_requirements": {"runtime": {"language_version": "string","platform_dependencies": ["strings"]},"deployment": {"target_environment": "string","required_services": ["strings"],"minimum_specs": ["strings"]}},"dependencies": {"runtime_dependencies": ["strings"],"optional_enhancements": ["strings"]},"integration_points": {"external_services": ["strings"],"apis": ["strings"],"databases": ["strings"]},"compatibility_requirements": {"browsers": ["strings"],"operating_systems": ["strings"],"devices": ["strings"]},"technical_constraints": {"version_restrictions": ["strings"],"platform_limitations": ["strings"],"integration_requirements": ["strings"]}}}
```

## Refinement Principles

1. Focus on addressing identified environment gaps
2. Maintain system stability and reliability
3. Ensure deployment feasibility
4. Document all requirement changes
5. Verify integration compatibility
6. Validate resource specifications

## Verification Checklist

Before submitting revised analysis:
1. Confirm all refinement points addressed
2. Verify resource calculations
3. Validate dependency compatibility
4. Check integration feasibility
5. Review scaling requirements
6. Test environment consistency
7. Verify deployment specifications

## Communication Guidelines

1. Document all requirement changes
2. Explain resource adjustments
3. Detail integration updates
4. Specify version changes
5. Highlight compatibility updates
6. Note deployment modifications
"""

core_requirements_refinement_schema = {
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
          },
          "requirement_changes": {
            "type": "object",
            "properties": {
              "added": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "removed": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "modified": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              }
            },
            "required": ["added", "removed", "modified"]
          }
        },
        "required": ["original_failure", "addressed_points", "verification_steps", "requirement_changes"]
      },
      "environment_analysis": {
        "type": "object",
        "properties": {
          "core_requirements": {
            "type": "object",
            "properties": {
              "runtime": {
                "type": "object",
                "properties": {
                  "language_version": {
                    "type": "string"
                  },
                  "platform_dependencies": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  }
                },
                "required": ["language_version", "platform_dependencies"]
              },
              "deployment": {
                "type": "object",
                "properties": {
                  "target_environment": {
                    "type": "string"
                  },
                  "required_services": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "minimum_specs": {
                    "type": "object"
                  }
                },
                "required": ["target_environment", "required_services", "minimum_specs"]
              }
            },
            "required": ["runtime", "deployment"]
          },
          "dependencies": {
            "type": "object",
            "properties": {
              "runtime_dependencies": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "optional_enhancements": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              }
            },
            "required": ["runtime_dependencies", "optional_enhancements"]
          },
          "integration_points": {
            "type": "object",
            "properties": {
              "external_services": {
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
              "databases": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              }
            },
            "required": ["external_services", "apis", "databases"]
          },
          "compatibility_requirements": {
            "type": "object",
            "properties": {
              "browsers": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "operating_systems": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "devices": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              }
            },
            "required": ["browsers", "operating_systems", "devices"]
          },
          "technical_constraints": {
            "type": "object",
            "properties": {
              "version_restrictions": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "platform_limitations": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "integration_requirements": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              }
            },
            "required": ["version_restrictions", "platform_limitations", "integration_requirements"]
          }
        },
        "required": ["core_requirements", "dependencies", "integration_points", 
                    "compatibility_requirements", "technical_constraints"]
      }
    },
    "required": ["refinement_metadata", "environment_analysis"]
  }
