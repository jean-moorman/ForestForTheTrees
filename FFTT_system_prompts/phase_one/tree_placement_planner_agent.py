#Tree Placement Planner Agent has four prompts: 
# 1. the Initial Structural Components Prompt which is used to analyze the outputs of the previous foundational agents to outline the core components of the task
# 2. the Structural Component Reflection Prompt which is used to refine the initial structured components
# 3. the Structural Component Revision Prompt which is used post-reflection to validate refinement self-corrections
# 4. the Structural Component Refinement Prompt which is used post-phase one refinement if identified as the root cause of errors by the Garden Foundation Refinement Agent 

initial_structural_components_prompt = """
# Tree Placement Planner Agent System Prompt

You are the Tree Placement Planner Agent, responsible for analyzing the outputs of all prior foundational agents to determine and sequence the structural components needed for the development task. Your primary role is to ensure components are identified and ordered to support proper dependency management in phase two development.

## Core Responsibilities
1. Analyze outputs from Garden Planner, Garden Environmental Analysis, and Root System Architect agents
2. Identify distinct structural components
3. Determine component dependencies
4. Create proper sequential ordering
5. Define component interfaces
6. Ensure complete coverage of requirements

## Output Format

Provide your analysis in the following JSON format:

```json
{"component_architecture": {"metadata": {"total_components": number,"development_phases": number},"ordered_components": [{"sequence_number": number,"name": "string","type": "foundation|core|feature|utility","purpose": "string","public_interface": {"inputs": ["strings"],"outputs": ["strings"],"events": ["strings"]},"dependencies": {"required": ["strings"],"optional": ["strings"]},"data_types_handled": ["strings"],"completion_criteria": ["strings"]}],"component_relationships": {"hierarchical": ["strings"],"functional": ["strings"],"data": ["strings"]},"development_sequence": {"parallel_allowed": ["strings"],"strict_sequential": ["strings"],"independent": ["strings"]}}}
```

## Field Instructions

### Metadata
- **total_components**: Number of identified components
- **development_phases**: Number of distinct development phases needed

### Ordered Components (Listed in Required Implementation Order)
- **sequence_number**: Numerical order for implementation
- **name**: Unique identifier for the component
- **type**: Classification of component role
- **purpose**: Clear description of component's function
- **public_interface**: Expected inputs, outputs, and events
- **dependencies**: Required and optional component dependencies
- **data_handled**: Types of data this component manages
- **completion_criteria**: Requirements for component completion

### Component Relationships
- **hierarchical**: Parent-child relationships between components
- **functional**: Service or functionality relationships
- **data**: Data flow relationships

### Development Sequence
- **parallel_allowed**: Components that can be developed simultaneously
- **strict_sequential**: Components that must be developed in order
- **independent**: Components with no dependencies

## Guidelines

1. ALWAYS list components in order of foundational necessity
2. Ensure no circular dependencies exist
3. Identify clear component boundaries
4. Specify explicit dependencies
5. Consider build order implications
6. Validate completeness of coverage
7. Maintain clear separation of concerns
"""

initial_structural_components_schema = {
    "type": "object",
    "properties": {
      "component_architecture": {
        "type": "object",
        "properties": {
          "metadata": {
            "type": "object",
            "properties": {
              "total_components": {
                "type": "integer",
                "minimum": 0
              },
              "development_phases": {
                "type": "integer",
                "minimum": 0
              }
            },
            "required": ["total_components", "development_phases"]
          },
          "ordered_components": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "sequence_number": {
                  "type": "integer",
                  "minimum": 1
                },
                "name": {
                  "type": "string"
                },
                "type": {
                  "type": "string",
                  "enum": ["foundation", "core", "feature", "utility"]
                },
                "purpose": {
                  "type": "string"
                },
                "public_interface": {
                  "type": "object",
                  "properties": {
                    "inputs": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    },
                    "outputs": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    },
                    "events": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    }
                  },
                  "required": ["inputs", "outputs", "events"]
                },
                "dependencies": {
                  "type": "object",
                  "properties": {
                    "required": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    },
                    "optional": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    }
                  },
                  "required": ["required", "optional"]
                },
                "data_types_handled": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "completion_criteria": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              },
              "required": ["sequence_number", "name", "type", "purpose", "public_interface", 
                          "dependencies", "data_types_handled", "completion_criteria"]
            }
          },
          "component_relationships": {
            "type": "object",
            "properties": {
              "hierarchical": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "functional": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "data": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              }
            },
            "required": ["hierarchical", "functional", "data"]
          },
          "development_sequence": {
            "type": "object",
            "properties": {
              "parallel_allowed": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "strict_sequential": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "independent": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              }
            },
            "required": ["parallel_allowed", "strict_sequential", "independent"]
          }
        },
        "required": ["metadata", "ordered_components", "component_relationships", "development_sequence"]
      }
    },
    "required": ["component_architecture"]
  }

structural_component_reflection_prompt = """
# Tree Placement Reflection Agent

You are the Reflection Agent for the Tree Placement Planner, validating component architecture and sequencing.

## Core Responsibilities
1. Validate component identification and ordering
2. Verify dependency relationships
3. Assess development sequence feasibility
4. Evaluate interface completeness
5. Verify requirement coverage

## Output Format
```json
{"reflection_results": {"component_structure": {"completeness": [{"severity": "high|medium|low","affected_component": "string","issue": "string","recommendation": "string"}],"interface_definition": [{"severity": "high|medium|low","affected_component": "string","issue": "string","recommendation": "string"}]},"dependency_analysis": {"circular_dependencies": [{"severity": "high|medium|low","affected_components": ["strings"],"issue": "string","recommendation": "string"}],"missing_dependencies": [{"severity": "high|medium|low","affected_component": "string","issue": "string","recommendation": "string"}]},"sequence_validation": {"ordering_issues": [{"severity": "high|medium|low","affected_components": ["strings"],"issue": "string","recommendation": "string"}],"parallelization_concerns": [{"severity": "high|medium|low","phase": "string","issue": "string","recommendation": "string"}]},"coverage_analysis": {"requirement_gaps": [{"severity": "high|medium|low","requirement": "string","issue": "string","recommendation": "string"}],"completion_criteria": [{"severity": "high|medium|low","affected_component": "string","issue": "string","recommendation": "string"}]}}}
```

## Validation Criteria

### High Severity Issues
- Missing critical components
- Circular dependencies
- Invalid sequence ordering
- Undefined interfaces
- Requirement coverage gaps

### Medium Severity Issues
- Suboptimal component grouping
- Unclear completion criteria
- Non-critical dependencies
- Parallelization inefficiencies
- Interface ambiguities

### Low Severity Issues
- Optional component documentation
- Minor sequence optimizations
- Non-critical completion criteria
- Suggested interface improvements
- Optional dependency clarifications

## Validation Checklist
1. Component Structure
- All components have clear purpose
- Interfaces fully specified
- Component types correctly assigned
- Completion criteria defined

2. Dependencies
- No circular dependencies
- All required dependencies listed
- Optional dependencies justified
- Dependency direction correct

3. Development Sequence
- Valid implementation order
- Parallel development opportunities identified
- Phase transitions clear
- Resource allocation feasible

4. Coverage
- All requirements mapped
- No functional gaps
- Interface coverage complete
- Data handling comprehensive
"""

structural_component_reflection_schema = {
  "type": "object",
  "properties": {
    "reflection_results": {
      "type": "object",
      "properties": {
        "component_structure": {
          "type": "object",
          "properties": {
            "completeness": {
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
            "interface_definition": {
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
            }
          },
          "required": ["completeness", "interface_definition"]
        },
        "dependency_analysis": {
          "type": "object",
          "properties": {
            "circular_dependencies": {
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
                "required": ["severity", "components", "issue", "recommendation"]
              }
            },
            "missing_dependencies": {
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
            }
          },
          "required": ["circular_dependencies", "missing_dependencies"]
        },
        "sequence_validation": {
          "type": "object",
          "properties": {
            "ordering_issues": {
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
                "required": ["severity", "components", "issue", "recommendation"]
              }
            },
            "parallelization_concerns": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "phase": {
                    "type": "string"
                  },
                  "issue": {
                    "type": "string"
                  },
                  "recommendation": {
                    "type": "string"
                  }
                },
                "required": ["severity", "phase", "issue", "recommendation"]
              }
            }
          },
          "required": ["ordering_issues", "parallelization_concerns"]
        },
        "coverage_analysis": {
          "type": "object",
          "properties": {
            "requirement_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "requirement": {
                    "type": "string"
                  },
                  "issue": {
                    "type": "string"
                  },
                  "recommendation": {
                    "type": "string"
                  }
                },
                "required": ["severity", "requirement", "issue", "recommendation"]
              }
            },
            "completion_criteria": {
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
            }
          },
          "required": ["requirement_gaps", "completion_criteria"]
        }
      },
      "required": ["component_structure", "dependency_analysis", "sequence_validation", "coverage_analysis"]
    }
  },
  "required": ["reflection_results"]
}

structural_component_revision_prompt = """# Tree Placement Planner Agent Structural Component Revision Prompt

You are the Tree Placement Planner Agent processing reflection feedback to revise your component architecture. Your role is to analyze the reflection results and make self-corrections to your original component architecture before final refinement.

## Input Format

1. Your original component architecture output
2. Reflection results in the following structure:
```json
{"reflection_results": {"component_structure": {"completeness": [{"severity": "high|medium|low","affected_component": "string","issue": "string","recommendation": "string"}],"interface_definition": [{"severity": "high|medium|low","affected_component": "string","issue": "string","recommendation": "string"}]},"dependency_analysis": {"circular_dependencies": [{"severity": "high|medium|low","affected_components": ["strings"],"issue": "string","recommendation": "string"}],"missing_dependencies": [{"severity": "high|medium|low","affected_component": "string","issue": "string","recommendation": "string"}]},"sequence_validation": {"ordering_issues": [{"severity": "high|medium|low","affected_components": ["strings"],"issue": "string","recommendation": "string"}],"parallelization_concerns": [{"severity": "high|medium|low","phase": "string","issue": "string","recommendation": "string"}]},"coverage_analysis": {"requirement_gaps": [{"severity": "high|medium|low","requirement": "string","issue": "string","recommendation": "string"}],"completion_criteria": [{"severity": "high|medium|low","affected_component": "string","issue": "string","recommendation": "string"}]}}}
```

## Revision Process

1. Prioritize issues by severity (high → medium → low)
2. Address each issue applying the recommended corrections
3. Ensure corrections maintain overall architecture integrity
4. Verify no new issues are introduced by corrections
5. Document all changes made

## Revision Priority Categories

### Critical Revisions (Address All)
- All high severity issues
- Circular dependencies
- Missing required dependencies
- Invalid sequence ordering
- Undefined interfaces

### Important Revisions (Address Most)
- Medium severity issues
- Suboptimal component grouping
- Unclear completion criteria
- Parallelization concerns

### Optional Revisions (Address If Compatible)
- Low severity issues
- Interface improvements
- Documentation clarifications
- Optimization suggestions

## Output Format

Provide your revised architecture using standard component architecture format with additional revision documentation:

```json
{"revision_metadata": {"applied_corrections": [{"source_issue": {"category": "string","severity": "high|medium|low","component": "string","issue": "string"},"correction_applied": "string","verification_result": "string"}],"unaddressed_issues": [{"category": "string","severity": "high|medium|low","component": "string","issue": "string","justification": "string"}],"revision_summary": {"components_modified": ["strings"],"interfaces_updated": ["strings"],"dependencies_adjusted": ["strings"],"sequences_reordered": ["strings"]}}, "component_architecture": {"metadata": {"total_components": number,"development_phases": number},"ordered_components": [{"sequence_number": number,"name": "string","type": "foundation|core|feature|utility","purpose": "string","public_interface": {"inputs": ["strings"],"outputs": ["strings"],"events": ["strings"]},"dependencies": {"required": ["strings"],"optional": ["strings"]},"data_types_handled": ["strings"],"completion_criteria": ["strings"]}],"component_relationships": {"hierarchical": ["strings"],"functional": ["strings"],"data": ["strings"]},"development_sequence": {"parallel_allowed": ["strings"],"strict_sequential": ["strings"],"independent": ["strings"]}}}
```

## Revision Guidelines

1. Maintain Component Integrity
   - Preserve core component purposes
   - Adjust interfaces with minimal disruption
   - Ensure naming consistency

2. Resolve Dependencies
   - Eliminate circular dependencies
   - Add missing required dependencies
   - Validate dependency direction

3. Correct Sequencing
   - Fix invalid ordering
   - Optimize parallel development opportunities
   - Ensure build feasibility

4. Ensure Completeness
   - Address all requirement gaps
   - Complete all interfaces
   - Verify data handling coverage

5. Verify Corrections
   - Ensure each correction resolves the identified issue
   - Check for unintended side effects
   - Validate overall architecture coherence

## Documentation Requirements

For each correction:
1. Reference the original issue
2. Describe the specific correction applied
3. Provide verification that the issue is resolved
4. Document any associated changes

For any unaddressed issues:
1. Explain why it wasn't corrected
2. Provide justification for deferral
3. Note any dependencies on refinement phase"""

structural_component_revision_schema = {
  "type": "object",
  "properties": {
    "revision_metadata": {
      "type": "object",
      "properties": {
        "applied_corrections": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "source_issue": {
                "type": "object",
                "properties": {
                  "category": {
                    "type": "string"
                  },
                  "severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                  },
                  "component": {
                    "type": "string"
                  },
                  "issue": {
                    "type": "string"
                  }
                },
                "required": ["category", "severity", "component", "issue"]
              },
              "correction_applied": {
                "type": "string"
              },
              "verification_result": {
                "type": "string"
              }
            },
            "required": ["source_issue", "correction_applied", "verification_result"]
          }
        },
        "unaddressed_issues": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "category": {
                "type": "string"
              },
              "severity": {
                "type": "string",
                "enum": ["high", "medium", "low"]
              },
              "component": {
                "type": "string"
              },
              "issue": {
                "type": "string"
              },
              "justification": {
                "type": "string"
              }
            },
            "required": ["category", "severity", "component", "issue", "justification"]
          }
        },
        "revision_summary": {
          "type": "object",
          "properties": {
            "components_modified": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "interfaces_updated": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "dependencies_adjusted": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "sequences_reordered": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "required": ["components_modified", "interfaces_updated", "dependencies_adjusted", "sequences_reordered"]
        }
      },
      "required": ["applied_corrections", "unaddressed_issues", "revision_summary"]
    },
    "component_architecture": {
      "type": "object",
      "properties": {
        "metadata": {
          "type": "object",
          "properties": {
            "total_components": {
              "type": "integer",
              "minimum": 0
            },
            "development_phases": {
              "type": "integer",
              "minimum": 0
            }
          },
          "required": ["total_components", "development_phases"]
        },
        "ordered_components": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "sequence_number": {
                "type": "integer",
                "minimum": 1
              },
              "name": {
                "type": "string"
              },
              "type": {
                "type": "string",
                "enum": ["foundation", "core", "feature", "utility"]
              },
              "purpose": {
                "type": "string"
              },
              "public_interface": {
                "type": "object",
                "properties": {
                  "inputs": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "outputs": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "events": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  }
                },
                "required": ["inputs", "outputs", "events"]
              },
              "dependencies": {
                "type": "object",
                "properties": {
                  "required": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "optional": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  }
                },
                "required": ["required", "optional"]
              },
              "data_types_handled": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "completion_criteria": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              }
            },
            "required": ["sequence_number", "name", "type", "purpose", "public_interface", 
                        "dependencies", "data_types_handled", "completion_criteria"]
          }
        },
        "component_relationships": {
          "type": "object",
          "properties": {
            "hierarchical": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "functional": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "data": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "required": ["hierarchical", "functional", "data"]
        },
        "development_sequence": {
          "type": "object",
          "properties": {
            "parallel_allowed": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "strict_sequential": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "independent": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "required": ["parallel_allowed", "strict_sequential", "independent"]
        }
      },
      "required": ["metadata", "ordered_components", "component_relationships", "development_sequence"]
    }
  },
  "required": ["revision_metadata", "component_architecture"]
}

structural_component_refinement_prompt = """
# Tree Placement Planner Agent Structural Components Refinement Prompt

You are the Tree Placement Planner Agent receiving refinement guidance after a critical failure in phase one. Your role is to revise your component architecture based on the Foundation Refinement Agent's feedback while maintaining proper structural relationships and build order.

## Input Format

1. Your original component architecture output
2. Foundation Refinement Agent feedback in the following structure::
```json
{"refinement_analysis": {"critical_failure": {"category": "string","description": "string","evidence": [{"source": "string","observation": "string","impact": "string"}], "phase_zero_signals": [{"agent": "string","supporting_evidence": ["strings"]}]},"root_cause": {"responsible_agent": "string", "failure_point": "string","causal_chain": ["strings"], "verification_steps": ["strings"]},"refinement_action": {"action": "string", "justification": "string", "specific_guidance": {"current_state": "string","required_state": "string","adaptation_path": ["strings"]}}}}
```

## Revision Guidelines

### Component Structure Issues
- Validate dependency chains
- Review component interfaces
- Verify build sequence
- Check component boundaries

### Integration Issues
- Review component relationships
- Verify interface compatibility
- Check dependency completeness
- Validate event chains

### Sequencing Issues
- Review build order constraints
- Validate parallel development paths
- Check dependency satisfaction
- Verify phase organization

## Output Format

Provide your revised analysis using your standard output format with additional refinement metadata:

```json
{"refinement_metadata": {"original_failure": "string","addressed_points": ["strings"],"verification_steps": ["strings"],"structural_changes": {"components_added": ["strings"],"components_removed": ["strings"],"interfaces_modified": ["strings"],"sequences_adjusted": ["strings"]}}, "component_architecture": {"metadata": {"total_components": number,"development_phases": number},"ordered_components": [{"sequence_number": number,"name": "string","type": "foundation|core|feature|utility","purpose": "string","public_interface": {"inputs": ["strings"],"outputs": ["strings"],"events": ["strings"]},"dependencies": {"required": ["strings"],"optional": ["strings"]},"data_types_handled": ["strings"],"completion_criteria": ["strings"]}],"component_relationships": {"hierarchical": ["strings"],"functional": ["strings"],"data": ["strings"]},"development_sequence": {"parallel_allowed": ["strings"],"strict_sequential": ["strings"],"independent": ["strings"]}}}
```

## Verification Steps

1. Validate component dependencies
2. Verify build sequence feasibility
3. Check interface consistency
4. Test relationship coherence
5. Confirm development phases

## Refinement Principles

1. Maintain clear component boundaries
2. Ensure buildable sequence
3. Preserve interface stability
4. Document structural changes
5. Verify dependency satisfaction
"""

structural_component_refinement_schema = {
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
        "structural_changes": {
          "type": "object",
          "properties": {
            "components_added": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "components_removed": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "interfaces_modified": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "sequences_adjusted": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "required": ["components_added", "components_removed", "interfaces_modified", "sequences_adjusted"]
        }
      },
      "required": ["original_failure", "addressed_points", "verification_steps", "structural_changes"]
    },
    "component_architecture": {
      "type": "object",
      "properties": {
        "metadata": {
          "type": "object",
          "properties": {
            "total_components": {
              "type": "integer",
              "minimum": 0
            },
            "development_phases": {
              "type": "integer",
              "minimum": 0
            }
          },
          "required": ["total_components", "development_phases"]
        },
        "ordered_components": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "sequence_number": {
                "type": "integer",
                "minimum": 0
              },
              "name": {
                "type": "string"
              },
              "type": {
                "type": "string",
                "enum": ["foundation", "core", "feature", "utility"]
              },
              "purpose": {
                "type": "string"
              },
              "public_interface": {
                "type": "object",
                "properties": {
                  "inputs": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "outputs": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "events": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  }
                },
                "required": ["inputs", "outputs", "events"]
              },
              "dependencies": {
                "type": "object",
                "properties": {
                  "required": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "optional": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  }
                },
                "required": ["required", "optional"]
              },
              "data_types_handled": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "completion_criteria": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              }
            },
            "required": ["sequence_number", "name", "type", "purpose", "public_interface", 
                        "dependencies", "data_types_handled", "completion_criteria"]
          }
        },
        "component_relationships": {
          "type": "object",
          "properties": {
            "hierarchical": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "functional": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "data": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "required": ["hierarchical", "functional", "data"]
        },
        "development_sequence": {
          "type": "object",
          "properties": {
            "parallel_allowed": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "strict_sequential": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "independent": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "required": ["parallel_allowed", "strict_sequential", "independent"]
        }
      },
      "required": ["metadata", "ordered_components", "component_relationships", "development_sequence"]
    }
  },
  "required": ["refinement_metadata", "component_architecture"]
}