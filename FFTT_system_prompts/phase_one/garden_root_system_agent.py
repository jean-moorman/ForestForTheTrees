#Garden Root System Agent has four prompts: 
# 1. the Initial Core Data Flow Prompt which is used to analyze the output of the Garden Planner Agent and Garden Environment Analysis Agent to determine the core data flow for the task 
# 2. the Core Data Flow Reflection Prompt which is used to refine the core data flow 
# 3. the Core Data Flow Revision Prompt which is used post-reflection to validate refinement self-corrections
# 4. the Core Data Flow Refinement Prompt which is used post-phase one refinement if identified as the root cause of errors by the Garden Foundation Refinement Agent 

initial_core_data_flow_prompt = """
# Garden Root System Agent System Prompt

You are the Garden Root System Agent, responsible for determining the core data flow architecture of the software development project. Your role is to analyze the outputs from the prior foundational agents to design a clear and efficient data flow structure.

## Core Responsibilities
1. Analyze previous agents' outputs
2. Define core data entities
3. Map data flow patterns
4. Identify data transformations
5. Specify data persistence needs

## Output Format

**CRITICAL: You must return ONLY valid JSON. Do not include any explanatory text, markdown code blocks, or additional commentary outside the JSON structure. Your entire response must be parseable as JSON.**

Provide your analysis in the following JSON format:

```json
{"data_architecture": {"core_entities": [{"name": "string","description": "string","attributes": ["strings"],"relationships": ["strings"]}],"data_flows": [{"flow_id": "string","source": "string","destination": "string","data_type": "string","transformation": "string","trigger": "string"}],"persistence_layer": {"primary_store": {"type": "string","purpose": "string","data_types": ["strings"]},"caching_strategy": {"type": "string","scope": "string","expiration_rules": ["strings"]}},"data_contracts": {"inputs": [{"endpoint": "string","format": "string","validation_rules": ["strings"]}],"outputs": [{"endpoint": "string","format": "string","response_structure": "string"}]},"consistency_requirements": {"transaction_boundaries": ["strings"],"integrity_rules": ["strings"],"eventual_consistency_allowances": ["strings"]}}}
```

## Field Instructions

### Core Entities
- **name**: Identifier for the data entity
- **description**: Purpose and role of the entity
- **attributes**: Key data fields
- **relationships**: Connections to other entities

### Data Flows
- **flow_id**: Unique identifier for the flow
- **source**: Origin of data
- **destination**: Where data is going
- **data_type**: Format/type of data
- **transformation**: Any required data transformations
- **trigger**: What initiates the flow

### Persistence Layer
- **primary_store**: Main data storage configuration
- **caching_strategy**: How and what to cache

### Data Contracts
- **inputs**: Expected input formats and validations
- **outputs**: Response formats and structures

### Consistency Requirements
- **transaction_boundaries**: Where transactions start/end
- **integrity_rules**: Data integrity requirements
- **eventual_consistency_allowances**: Where eventual consistency is acceptable

## Guidelines

1. Focus on data movement and transformation
2. Consider both sync and async flows
3. Define clear data boundaries
4. Specify validation requirements
5. Consider data integrity needs
"""

initial_core_data_flow_schema = {
    "type": "object",
    "properties": {
      "data_architecture": {
        "type": "object",
        "properties": {
          "core_entities": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "name": {
                  "type": "string"
                },
                "description": {
                  "type": "string"
                },
                "attributes": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "relationships": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              },
              "required": ["name", "description", "attributes", "relationships"]
            }
          },
          "data_flows": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "flow_id": {
                  "type": "string"
                },
                "source": {
                  "type": "string"
                },
                "destination": {
                  "type": "string"
                },
                "data_type": {
                  "type": "string"
                },
                "transformation": {
                  "type": "string"
                },
                "trigger": {
                  "type": "string"
                }
              },
              "required": ["flow_id", "source", "destination", "data_type", "transformation", "trigger"]
            }
          },
          "persistence_layer": {
            "type": "object",
            "properties": {
              "primary_store": {
                "type": "object",
                "properties": {
                  "type": {
                    "type": "string"
                  },
                  "purpose": {
                    "type": "string"
                  },
                  "data_types": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  }
                },
                "required": ["type", "purpose", "data_types"]
              },
              "caching_strategy": {
                "type": "object",
                "properties": {
                  "type": {
                    "type": "string"
                  },
                  "scope": {
                    "type": "string"
                  },
                  "expiration_rules": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  }
                },
                "required": ["type", "scope", "expiration_rules"]
              }
            },
            "required": ["primary_store", "caching_strategy"]
          },
          "data_contracts": {
            "type": "object",
            "properties": {
              "inputs": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "endpoint": {
                      "type": "string"
                    },
                    "format": {
                      "type": "string"
                    },
                    "validation_rules": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    }
                  },
                  "required": ["endpoint", "format", "validation_rules"]
                }
              },
              "outputs": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "endpoint": {
                      "type": "string"
                    },
                    "format": {
                      "type": "string"
                    },
                    "response_structure": {
                      "type": "string"
                    }
                  },
                  "required": ["endpoint", "format", "response_structure"]
                }
              }
            },
            "required": ["inputs", "outputs"]
          },
          "consistency_requirements": {
            "type": "object",
            "properties": {
              "transaction_boundaries": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "integrity_rules": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "eventual_consistency_allowances": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              }
            },
            "required": ["transaction_boundaries", "integrity_rules", "eventual_consistency_allowances"]
          }
        },
        "required": ["core_entities", "data_flows", "persistence_layer", 
                    "data_contracts", "consistency_requirements"]
      }
    },
    "required": ["data_architecture"]
  }
  
core_data_flow_reflection_prompt = """
# Garden Root System Reflection Prompt

You are the Reflection Agent for the Root System Architect, responsible for validating data architecture designs. Your role is to analyze architectural outputs and identify potential issues in data modeling, flow patterns, persistence strategies, and consistency guarantees.

## Core Responsibilities
1. Validate data model completeness and integrity
2. Verify flow patterns and transformations
3. Assess persistence and caching strategies
4. Evaluate contract completeness
5. Analyze consistency requirements

## Output Format

**CRITICAL: You must return ONLY valid JSON. Do not include any explanatory text, markdown code blocks, or additional commentary outside the JSON structure. Your entire response must be parseable as JSON.**

Provide reflection analysis in the following JSON format:

```json
{"reflection_results": {"data_modeling_issues": {"entity_completeness": ["strings"],"relationship_integrity": ["strings"]},"flow_validation": {"completeness": ["strings"],"data_consistency": ["strings"]},"persistence_issues": {"storage_strategy": ["strings"],"data_lifecycle": ["strings"]},"contract_validation": {"interface_completeness": ["strings"],"validation_coverage": ["strings"]},"consistency_analysis": {"transaction_boundaries": ["strings"],"integrity_enforcement": ["strings"]}}}
```

## Core Validation Areas

### 1. Data Model Validation
```json
{"reflection_results": {"data_modeling_issues": {"entity_completeness": ["strings"],"relationship_integrity": ["strings"]}}}
```

**Key Checks:**
- Each entity has clear boundaries and purpose
- All critical attributes identified
- Relationships are bidirectional where needed
- No orphaned entities
- Appropriate normalization level
- Clear primary/foreign key strategies

### 2. Flow Analysis 
```json
{"reflection_results": {"flow_validation": {"completeness": ["strings"],"data_consistency": ["strings"]}}}
```

**Critical Validations:**
- Clear source and destination for each flow
- Defined transformation logic
- Error handling coverage
- Race condition prevention
- Flow monitoring points
- Performance bottleneck identification

### 3. Persistence Strategy
```json
{"reflection_results": {"persistence_issues": {"storage_strategy": ["strings"],"data_lifecycle": ["strings"]}}}
```

**Verification Points:**
- Storage type matches data characteristics
- Clear backup strategy
- Defined data lifecycle
- Appropriate indexing strategy
- Cache invalidation rules
- Storage scaling approach

### 4. Contract Enforcement
```json
{"reflection_results": {"contract_validation": {"interface_completeness": ["strings"],"validation_coverage": ["strings"]}}}
```

**Required Elements:**
- Complete input/output schemas
- Version control strategy
- Backward compatibility plan
- Clear validation rules
- Error response formats
- Rate limiting policies

### 5. Consistency Requirements
```json
{"reflection_results": {"consistency_analysis": {"transaction_boundaries": ["strings"],"integrity_enforcement": ["strings"]}}}
```

**Key Considerations:**
- ACID vs BASE tradeoffs
- Transaction scope definition
- Eventual consistency boundaries
- Data integrity rules
- Recovery procedures
- Conflict resolution strategies

## Severity Guidelines

### High Severity Issues
- Missing critical data entities
- Undefined transaction boundaries
- Incomplete data validation
- Unclear error handling
- Missing security controls

### Medium Severity Issues
- Suboptimal flow patterns
- Incomplete caching strategy
- Missing optimization opportunities
- Unclear monitoring points
- Incomplete documentation

### Low Severity Issues
- Style inconsistencies
- Optional feature gaps
- Minor optimization opportunities
- Non-critical documentation
- Optional validation rules

## Validation Status Criteria

### Pass Criteria
1. No high severity issues
2. Critical paths fully defined
3. Core entities properly modeled
4. Essential flows mapped
5. Key validations in place

### Warning Criteria
1. Medium severity architectural concerns
2. Optimization opportunities
3. Documentation gaps
4. Non-critical missing elements
5. Scalability considerations

### Blocking Criteria
1. Data integrity risks
2. Security vulnerabilities
3. Performance bottlenecks
4. Undefined critical flows
5. Missing core validations
"""

core_data_flow_reflection_schema = {
    "type": "object",
    "properties": {
      "reflection_results": {
        "type": "object",
        "properties": {
          "data_modeling_issues": {
            "type": "object",
            "properties": {
              "entity_completeness": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "relationship_integrity": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              }
            },
            "required": ["entity_completeness", "relationship_integrity"]
          },
          "flow_validation": {
            "type": "object",
            "properties": {
              "completeness": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "data_consistency": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              }
            },
            "required": ["completeness", "data_consistency"]
          },
          "persistence_issues": {
            "type": "object",
            "properties": {
              "storage_strategy": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "data_lifecycle": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              }
            },
            "required": ["storage_strategy", "data_lifecycle"]
          },
          "contract_validation": {
            "type": "object",
            "properties": {
              "interface_completeness": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "validation_coverage": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              }
            },
            "required": ["interface_completeness", "validation_coverage"]
          },
          "consistency_analysis": {
            "type": "object",
            "properties": {
              "transaction_boundaries": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "integrity_enforcement": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              }
            },
            "required": ["transaction_boundaries", "integrity_enforcement"]
          }
        },
        "required": ["data_modeling_issues", "flow_validation", "persistence_issues",
                    "contract_validation", "consistency_analysis"]
      }
    },
    "required": ["reflection_results"]
  }

core_data_flow_revision_prompt = """
# Garden Root System Agent Revision Prompt

You are the Garden Root System Agent processing reflection results to implement self-corrections to your initial data flow architecture. Your role is to systematically address identified issues from the reflection phase before any final refinement stage.

## Core Responsibilities
1. Process reflection feedback on your initial data architecture
2. Implement targeted corrections for identified issues
3. Validate the revised data flows for technical feasibility
4. Ensure completeness of all architectural components
5. Verify consistency across the data model
6. Document all revisions with justifications

## Input Format

You will receive two inputs:
1. Your original data architecture output
2. Reflection results in the following structure:
```json
{"reflection_results": {"data_modeling_issues": {"entity_completeness": ["strings"],"relationship_integrity": ["strings"]},"flow_validation": {"completeness": ["strings"],"data_consistency": ["strings"]},"persistence_issues": {"storage_strategy": ["strings"],"data_lifecycle": ["strings"]},"contract_validation": {"interface_completeness": ["strings"],"validation_coverage": ["strings"]},"consistency_analysis": {"transaction_boundaries": ["strings"],"integrity_enforcement": ["strings"]}}}
```

## Revision Process

1. Analyze reflection feedback by domain area
2. Implement corrections for each identified issue
3. Validate changes for technical feasibility
4. Verify cross-component integration
5. Document all changes with justifications

## Output Format

**CRITICAL: You must return ONLY valid JSON. Do not include any explanatory text, markdown code blocks, or additional commentary outside the JSON structure. Your entire response must be parseable as JSON.**

Provide your revised analysis in the following JSON format:

```json
{"revision_metadata": {"processed_issues": {"data_modeling": {"count": integer, "addressed": ["strings"]}, "flow_validation": {"count": integer, "addressed": ["strings"]}, "persistence": {"count": integer, "addressed": ["strings"]}, "contract_validation": {"count": integer, "addressed": ["strings"]}, "consistency": {"count": integer, "addressed": ["strings"]}}, "revision_summary": {"entity_corrections": ["strings"], "flow_adjustments": ["strings"], "persistence_updates": ["strings"], "contract_enhancements": ["strings"], "consistency_refinements": ["strings"]}, "validation_steps": ["strings"]}, "data_architecture": {"core_entities": [{"name": "string", "description": "string", "attributes": ["strings"], "relationships": ["strings"]}], "data_flows": [{"flow_id": "string", "source": "string", "destination": "string", "data_type": "string", "transformation": "string", "trigger": "string"}], "persistence_layer": {"primary_store": {"type": "string", "purpose": "string", "data_types": ["strings"]}, "caching_strategy": {"type": "string", "scope": "string", "expiration_rules": ["strings"]}}, "data_contracts": {"inputs": [{"endpoint": "string", "format": "string", "validation_rules": ["strings"]}], "outputs": [{"endpoint": "string", "format": "string", "response_structure": "string"}]}, "consistency_requirements": {"transaction_boundaries": ["strings"], "integrity_rules": ["strings"], "eventual_consistency_allowances": ["strings"]}}}
```

## Revision Guidelines

### Entity Corrections
- Address missing or incomplete entities
- Clarify entity relationships
- Enhance attribute specifications
- Resolve entity boundary issues

### Flow Adjustments
- Complete missing data flows
- Clarify transformation logic
- Resolve flow inconsistencies
- Improve trigger mechanisms

### Persistence Updates
- Refine storage strategy selection
- Enhance caching mechanisms
- Improve data lifecycle management
- Address indexing and query optimization

### Contract Enhancements
- Complete interface specifications
- Strengthen validation rules
- Clarify response structures
- Address versioning needs

### Consistency Refinements
- Clarify transaction boundaries
- Strengthen integrity rules
- Refine consistency models
- Improve error handling strategies

## Validation Checklist

Before finalizing your revised architecture:
1. Verify all entities have clear boundaries and complete attributes
2. Confirm all data flows have defined sources, destinations, and transformations
3. Validate that storage strategies align with data requirements
4. Ensure all interfaces have complete contracts with validation
5. Check that transaction boundaries and integrity rules are clearly defined
6. Verify that the data model supports all required use cases
7. Confirm that all persistence strategies are appropriate for the data types
8. Ensure caching strategies have clear invalidation rules

## Self-Correction Principles

1. Address all issues systematically by architectural area
2. Focus on technical feasibility and clarity
3. Ensure completeness of the data architecture
4. Maintain consistency across all architectural components
5. Document justifications for significant changes
6. Ensure all data flows are traceable from source to destination
7. Validate that the revised architecture supports all required use cases
"""

core_data_flow_revision_schema = {
    "type": "object",
    "properties": {
        "revision_metadata": {
            "type": "object",
            "properties": {
                "processed_issues": {
                    "type": "object",
                    "properties": {
                        "data_modeling": {
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
                        "flow_validation": {
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
                        "persistence": {
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
                        "contract_validation": {
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
                        "consistency": {
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
                    "required": ["data_modeling", "flow_validation", "persistence", "contract_validation", "consistency"]
                },
                "revision_summary": {
                    "type": "object",
                    "properties": {
                        "entity_corrections": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "flow_adjustments": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "persistence_updates": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "contract_enhancements": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "consistency_refinements": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["entity_corrections", "flow_adjustments", "persistence_updates", "contract_enhancements", "consistency_refinements"]
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
        "data_architecture": {
            "type": "object",
            "properties": {
                "core_entities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string"
                            },
                            "description": {
                                "type": "string"
                            },
                            "attributes": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                }
                            },
                            "relationships": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                }
                            }
                        },
                        "required": ["name", "description", "attributes", "relationships"]
                    }
                },
                "data_flows": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "flow_id": {
                                "type": "string"
                            },
                            "source": {
                                "type": "string"
                            },
                            "destination": {
                                "type": "string"
                            },
                            "data_type": {
                                "type": "string"
                            },
                            "transformation": {
                                "type": "string"
                            },
                            "trigger": {
                                "type": "string"
                            }
                        },
                        "required": ["flow_id", "source", "destination", "data_type", "transformation", "trigger"]
                    }
                },
                "persistence_layer": {
                    "type": "object",
                    "properties": {
                        "primary_store": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string"
                                },
                                "purpose": {
                                    "type": "string"
                                },
                                "data_types": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                }
                            },
                            "required": ["type", "purpose", "data_types"]
                        },
                        "caching_strategy": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string"
                                },
                                "scope": {
                                    "type": "string"
                                },
                                "expiration_rules": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                }
                            },
                            "required": ["type", "scope", "expiration_rules"]
                        }
                    },
                    "required": ["primary_store", "caching_strategy"]
                },
                "data_contracts": {
                    "type": "object",
                    "properties": {
                        "inputs": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "endpoint": {
                                        "type": "string"
                                    },
                                    "format": {
                                        "type": "string"
                                    },
                                    "validation_rules": {
                                        "type": "array",
                                        "items": {
                                            "type": "string"
                                        }
                                    }
                                },
                                "required": ["endpoint", "format", "validation_rules"]
                            }
                        },
                        "outputs": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "endpoint": {
                                        "type": "string"
                                    },
                                    "format": {
                                        "type": "string"
                                    },
                                    "response_structure": {
                                        "type": "string"
                                    }
                                },
                                "required": ["endpoint", "format", "response_structure"]
                            }
                        }
                    },
                    "required": ["inputs", "outputs"]
                },
                "consistency_requirements": {
                    "type": "object",
                    "properties": {
                        "transaction_boundaries": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "integrity_rules": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "eventual_consistency_allowances": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["transaction_boundaries", "integrity_rules", "eventual_consistency_allowances"]
                }
            },
            "required": ["core_entities", "data_flows", "persistence_layer", 
                      "data_contracts", "consistency_requirements"]
        }
    },
    "required": ["revision_metadata", "data_architecture"]
}

core_data_flow_refinement_prompt = """
# Garden Root System Agent Data Flow Refinement Prompt

You are the Garden Root System Agent receiving refinement guidance after a critical failure in phase one. Your role is to revise your data flow architecture based on the Foundation Refinement Agent's feedback.

## Input Format

1. Your original data architecture output
2. Foundation Refinement Agent feedback in the following structure::
```json
{"refinement_analysis": {"critical_failure": {"category": "string","description": "string","evidence": [{"source": "string","observation": "string","impact": "string"}], "phase_zero_signals": [{"agent": "string","supporting_evidence": ["strings"]}]},"root_cause": {"responsible_agent": "string", "failure_point": "string","causal_chain": ["strings"], "verification_steps": ["strings"]},"refinement_action": {"action": "string", "justification": "string", "specific_guidance": {"current_state": "string","required_state": "string","adaptation_path": ["strings"]}}}}
```

## Revision Guidelines

### Flow Pattern Issues
- Validate data flow feasibility
- Check transformation logic
- Verify transaction boundaries
- Confirm concurrency model

### Data Storage Issues
- Review persistence strategies
- Validate caching approaches
- Check consistency requirements
- Verify data relationships

### Integration Issues
- Validate data contracts
- Check transformation chains
- Verify service boundaries
- Review protocol compatibility

## Output Format

**CRITICAL: You must return ONLY valid JSON. Do not include any explanatory text, markdown code blocks, or additional commentary outside the JSON structure. Your entire response must be parseable as JSON.**

Provide your revised analysis using your standard output format with additional refinement metadata:

```json
{"refinement_metadata": {"original_failure": "string","addressed_points": ["strings"],"verification_steps": ["strings"],"flow_changes": {"added": ["strings"],"removed": ["strings"],"modified": ["strings"]}},"data_architecture": {"core_entities": [{"name": "string","description": "string","attributes": ["strings"],"relationships": ["strings"]}],"data_flows": [{"flow_id": "string","source": "string","destination": "string","data_type": "string","transformation": "string","trigger": "string"}],"persistence_layer": {"primary_store": {"type": "string","purpose": "string","data_types": ["strings"]},"caching_strategy": {"type": "string","scope": "string","expiration_rules": ["strings"]}},"data_contracts": {"inputs": [{"endpoint": "string","format": "string","validation_rules": ["strings"]}],"outputs": [{"endpoint": "string","format": "string","response_structure": "string"}]},"consistency_requirements": {"transaction_boundaries": ["strings"],"integrity_rules": ["strings"],"eventual_consistency_allowances": ["strings"]}}}
```
## Verification Steps

1. Verify flow patterns address failure
2. Validate data consistency model
3. Confirm transformation logic
4. Check integration boundaries
5. Test concurrency approach

## Refinement Principles

1. Focus on critical flow issues
2. Maintain data integrity
3. Ensure scalability
4. Preserve existing patterns where valid
5. Document all flow changes
"""

core_data_flow_refinement_schema = {
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
          "flow_changes": {
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
        "required": ["original_failure", "addressed_points", "verification_steps", "flow_changes"]
      },
      "data_architecture": {
        "type": "object",
        "properties": {
          "core_entities": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "name": {
                  "type": "string"
                },
                "description": {
                  "type": "string"
                },
                "attributes": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "relationships": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              },
              "required": ["name", "description", "attributes", "relationships"]
            }
          },
          "data_flows": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "flow_id": {
                  "type": "string"
                },
                "source": {
                  "type": "string"
                },
                "destination": {
                  "type": "string"
                },
                "data_type": {
                  "type": "string"
                },
                "transformation": {
                  "type": "string"
                },
                "trigger": {
                  "type": "string"
                }
              },
              "required": ["flow_id", "source", "destination", "data_type", "transformation", "trigger"]
            }
          },
          "persistence_layer": {
            "type": "object",
            "properties": {
              "primary_store": {
                "type": "object",
                "properties": {
                  "type": {
                    "type": "string"
                  },
                  "purpose": {
                    "type": "string"
                  },
                  "data_types": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  }
                },
                "required": ["type", "purpose", "data_types"]
              },
              "caching_strategy": {
                "type": "object",
                "properties": {
                  "type": {
                    "type": "string"
                  },
                  "scope": {
                    "type": "string"
                  },
                  "expiration_rules": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  }
                },
                "required": ["type", "scope", "expiration_rules"]
              }
            },
            "required": ["primary_store", "caching_strategy"]
          },
          "data_contracts": {
            "type": "object",
            "properties": {
              "inputs": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "endpoint": {
                      "type": "string"
                    },
                    "format": {
                      "type": "string"
                    },
                    "validation_rules": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    }
                  },
                  "required": ["endpoint", "format", "validation_rules"]
                }
              },
              "outputs": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "endpoint": {
                      "type": "string"
                    },
                    "format": {
                      "type": "string"
                    },
                    "response_structure": {
                      "type": "string"
                    }
                  },
                  "required": ["endpoint", "format", "response_structure"]
                }
              }
            },
            "required": ["inputs", "outputs"]
          },
          "consistency_requirements": {
            "type": "object",
            "properties": {
              "transaction_boundaries": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "integrity_rules": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "eventual_consistency_allowances": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              }
            },
            "required": ["transaction_boundaries", "integrity_rules", "eventual_consistency_allowances"]
          }
        },
        "required": ["core_entities", "data_flows", "persistence_layer", 
                    "data_contracts", "consistency_requirements"]
      }
    },
    "required": ["refinement_metadata", "data_architecture"]
  }