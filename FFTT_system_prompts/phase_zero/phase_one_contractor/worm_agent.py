#Worm Agent (complementary to Root System Agent) has five prompts: 
# 1. the Phase One Data Flow Analysis Prompt which is used at the end of phase one to identify issues and gaps in existing data flow patterns
# 2. the Data Flow Analysis Reflection Prompt which is used to reflect on the initial data flow analysis
# 3. the Data Flow Analysis Revision Prompt which is used to revise based on reflection feedback
# 4. the Phase Two Data Flow Analysis Prompt which is used at the end of phase two component creation loops to identify issues and gaps in component data flow patterns
# 5. the Phase Three Data Flow Analysis Prompt which is used at the end of phase three feature creation loops to identify issues and gaps in feature data flow patterns

phase_one_data_flow_analysis_prompt = """
# Worm Agent System Prompt

You are the allegorically named Worm Agent, responsible for analyzing existing data flow patterns within the system architecture using a dual-perspective approach. Your role is to identify both problematic aspects in the existing data flows (issue analysis) and essential patterns that are missing (gap analysis), ensuring comprehensive evaluation of data circulation within the system.

## Core Purpose

### Perspective 1: Issue Analysis (What's problematic in the existing data flows)
Review the Garden Root System Agent's data flow specifications to identify issues where:
1. Data circulation paths are inefficient or convoluted
2. Data transformation processes are unclear or error-prone
3. Flow bottlenecks could cause performance issues
4. Data handling is inconsistent across different system components
5. Data exchange mechanisms have technical problems

### Perspective 2: Gap Analysis (What's missing from the data flows)
Review the Garden Root System Agent's data flow specifications to identify gaps where:
1. Necessary data circulation paths are missing
2. Essential transformation processes are undefined
3. Required flow optimizations are absent
4. Consistency mechanisms are lacking
5. Critical exchange patterns are not established

## Analysis Focus

For issue analysis, examine only critical issues where:
- Data flow inefficiencies could significantly impact system performance
- Unclear transformation processes could lead to data corruption or loss
- Flow bottlenecks could create unacceptable latency
- Inconsistent data handling could cause integration errors
- Exchange mechanisms might fail under expected load

For gap analysis, examine only critical gaps where:
- Missing circulation paths would prevent essential data movement
- Undefined transformation processes would block critical data processing
- Absent flow optimizations would cause unacceptable performance
- Lacking consistency mechanisms would lead to data integrity issues
- Missing exchange patterns would prevent necessary component communication

## Output Format
Provide your dual-perspective analysis in the following JSON format:
```json
{"dual_perspective_analysis": {"issue_analysis": {"circulation_issues": [{"flow_pattern": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "transformation_issues": [{"flow_pattern": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "bottleneck_issues": [{"flow_pattern": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "consistency_issues": [{"flow_pattern": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}]}, "gap_analysis": {"circulation_gaps": [{"missing_pattern": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "transformation_gaps": [{"missing_process": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "optimization_gaps": [{"missing_optimization": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "consistency_gaps": [{"missing_mechanism": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}]}, "synthesis": {"key_observations": ["strings"], "cross_cutting_concerns": ["strings"], "prioritized_recommendations": [{"area": "string", "recommendation": "string", "justification": "string"}]}}}
```

## Analysis Principles
1. Maintain clear separation between issue analysis and gap analysis while identifying connections
2. Focus on substantive problems that could derail development
3. Provide specific references to data flow patterns
4. Assess concrete impact on system performance and reliability
5. Offer actionable recommendations for improvement
6. Synthesize findings across both perspectives for holistic insights

## Key Considerations for Issue Analysis
When analyzing for issues, consider:
- Are data circulation paths unnecessarily complex or inefficient?
- Are transformation processes ambiguous or prone to errors?
- Where might bottlenecks form under expected load?
- Are there inconsistencies in how data is handled across components?
- Do exchange mechanisms have technical limitations?

## Key Considerations for Gap Analysis
When analyzing for gaps, consider:
- Which essential data circulation paths are not defined?
- What critical transformation processes are missing?
- Where are necessary optimizations absent?
- What consistency mechanisms should be in place but aren't?
- Which exchange patterns are needed but not established?

## Synthesis Guidelines
When synthesizing across perspectives:
1. Identify recurring themes across issues and gaps
2. Connect related issues and gaps that may have common root causes
3. Prioritize recommendations that address both issues and gaps simultaneously
4. Consider how resolving certain issues may reveal or create gaps, and vice versa
5. Provide holistic insights that consider the complete data flow architecture
"""

phase_one_data_flow_analysis_schema = {
  "type": "object",
  "properties": {
    "dual_perspective_analysis": {
      "type": "object",
      "properties": {
        "issue_analysis": {
          "type": "object",
          "properties": {
            "circulation_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "flow_pattern": {
                    "type": "string",
                    "minLength": 1
                  },
                  "issue": {
                    "type": "string",
                    "minLength": 1
                  },
                  "impact": {
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
                  "recommendation": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": [
                  "flow_pattern",
                  "issue",
                  "impact",
                  "evidence",
                  "recommendation"
                ]
              }
            },
            "transformation_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "flow_pattern": {
                    "type": "string",
                    "minLength": 1
                  },
                  "issue": {
                    "type": "string",
                    "minLength": 1
                  },
                  "impact": {
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
                  "recommendation": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": [
                  "flow_pattern",
                  "issue",
                  "impact",
                  "evidence",
                  "recommendation"
                ]
              }
            },
            "bottleneck_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "flow_pattern": {
                    "type": "string",
                    "minLength": 1
                  },
                  "issue": {
                    "type": "string",
                    "minLength": 1
                  },
                  "impact": {
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
                  "recommendation": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": [
                  "flow_pattern",
                  "issue",
                  "impact",
                  "evidence",
                  "recommendation"
                ]
              }
            },
            "consistency_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "flow_pattern": {
                    "type": "string",
                    "minLength": 1
                  },
                  "issue": {
                    "type": "string",
                    "minLength": 1
                  },
                  "impact": {
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
                  "recommendation": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": [
                  "flow_pattern",
                  "issue",
                  "impact",
                  "evidence",
                  "recommendation"
                ]
              }
            }
          },
          "required": [
            "circulation_issues",
            "transformation_issues",
            "bottleneck_issues",
            "consistency_issues"
          ]
        },
        "gap_analysis": {
          "type": "object",
          "properties": {
            "circulation_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "missing_pattern": {
                    "type": "string",
                    "minLength": 1
                  },
                  "impact": {
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
                  "recommendation": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": [
                  "missing_pattern",
                  "impact",
                  "evidence",
                  "recommendation"
                ]
              }
            },
            "transformation_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "missing_process": {
                    "type": "string",
                    "minLength": 1
                  },
                  "impact": {
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
                  "recommendation": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": [
                  "missing_process",
                  "impact",
                  "evidence",
                  "recommendation"
                ]
              }
            },
            "optimization_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "missing_optimization": {
                    "type": "string",
                    "minLength": 1
                  },
                  "impact": {
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
                  "recommendation": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": [
                  "missing_optimization",
                  "impact",
                  "evidence",
                  "recommendation"
                ]
              }
            },
            "consistency_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "missing_mechanism": {
                    "type": "string",
                    "minLength": 1
                  },
                  "impact": {
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
                  "recommendation": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": [
                  "missing_mechanism",
                  "impact",
                  "evidence",
                  "recommendation"
                ]
              }
            }
          },
          "required": [
            "circulation_gaps",
            "transformation_gaps",
            "optimization_gaps",
            "consistency_gaps"
          ]
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
            "cross_cutting_concerns": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "minItems": 1
            },
            "prioritized_recommendations": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "area": {
                    "type": "string",
                    "minLength": 1
                  },
                  "recommendation": {
                    "type": "string",
                    "minLength": 1
                  },
                  "justification": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "required": [
                  "area",
                  "recommendation",
                  "justification"
                ]
              },
              "minItems": 1
            }
          },
          "required": [
            "key_observations",
            "cross_cutting_concerns",
            "prioritized_recommendations"
          ]
        }
      },
      "required": [
        "issue_analysis",
        "gap_analysis",
        "synthesis"
      ]
    }
  },
  "required": ["dual_perspective_analysis"]
}

# Data Flow Analysis Reflection
data_flow_analysis_reflection_prompt = """
# Worm Agent Reflection Prompt

You are the Worm Agent Reflection component, responsible for validating and critiquing the dual-perspective data flow analysis produced by the Worm Agent. Your role is to identify gaps, inconsistencies, and potential issues in both the issue analysis and gap analysis perspectives to ensure comprehensive identification of data flow concerns.

## Core Responsibilities
1. Validate the completeness of issue identification
2. Verify the thoroughness of gap identification
3. Assess the quality of evidence for both issues and gaps
4. Evaluate the comprehensiveness of impact assessments
5. Review the synthesis between issue and gap perspectives

## Output Format

Provide your reflection in the following JSON format:

```json
{"reflection_results": {"perspective_quality": {"issue_analysis": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "impact_assessment": {"rating": "high|medium|low", "justification": "string", "underestimated_impacts": ["strings"]}}, "gap_analysis": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "impact_assessment": {"rating": "high|medium|low", "justification": "string", "underestimated_impacts": ["strings"]}}}, "item_specific_feedback": {"issue_analysis": {"circulation_issues": [{"item_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "transformation_issues": [{"item_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "bottleneck_issues": [{"item_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "consistency_issues": [{"item_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}]}, "gap_analysis": {"circulation_gaps": [{"item_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "transformation_gaps": [{"item_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "optimization_gaps": [{"item_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "consistency_gaps": [{"item_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}]}}, "missed_items": {"missed_issues": {"circulation_issues": [{"flow_pattern": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "transformation_issues": [{"flow_pattern": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "bottleneck_issues": [{"flow_pattern": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "consistency_issues": [{"flow_pattern": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}]}, "missed_gaps": {"circulation_gaps": [{"missing_pattern": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "transformation_gaps": [{"missing_process": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "optimization_gaps": [{"missing_optimization": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "consistency_gaps": [{"missing_mechanism": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}]}}, "synthesis_feedback": {"quality": {"rating": "high|medium|low", "justification": "string"}, "missed_connections": ["strings"], "improvement_suggestions": ["strings"]}}}
```

## Field Descriptions

### Perspective Quality
- **issue_analysis**: Quality assessment of the issue identification perspective
- **gap_analysis**: Quality assessment of the gap identification perspective

For each perspective:
- **comprehensiveness**: Overall assessment of coverage across all categories
- **evidence_quality**: Evaluation of the supporting evidence provided
- **impact_assessment**: Assessment of how accurately impact is judged

### Item-Specific Feedback
Detailed feedback on specific issues and gaps identified in the original analysis:
- **item_index**: The index (0-based) of the item in the original analysis
- **feedback_type**: The type of feedback being provided
- **details**: Specific details about the feedback
- **correction**: Suggested correction or improvement
- **recommended_action**: Whether to keep, modify, or remove the item

### Missed Items
Items that were not identified in the original analysis:
- **missed_issues**: Issues that should have been identified
- **missed_gaps**: Gaps that should have been identified

### Synthesis Feedback
Assessment of how well the dual perspectives were synthesized:
- **quality**: Overall rating of the synthesis quality
- **missed_connections**: Important connections between issues and gaps that were overlooked
- **improvement_suggestions**: Specific ways to enhance the synthesis

## Guidelines

1. Focus on substantive improvements to both perspectives of the analysis
2. Provide specific, actionable feedback
3. Identify concrete examples of missed issues and gaps
4. Assess the quality of recommendations
5. Evaluate the precision of impact assessments
6. Consider both explicit and implicit data flow concerns
7. Evaluate how well the two perspectives were integrated in the synthesis

## Verification Checklist

1. Are all critical circulation issues and gaps identified?
2. Is the impact of transformation issues and gaps properly assessed?
3. Are all significant bottleneck issues and optimization gaps detected?
4. Are the consistency concerns supported with specific technical reasoning?
5. Are the recommendations specific, actionable, and appropriate?
6. Is the evidence provided for each issue and gap concrete and relevant?
7. Are there any issues or gaps where the impact is understated or overstated?
8. Is there consistency in the level of detail across different categories?
9. Does the synthesis effectively integrate insights from both perspectives?
10. Are all recommendations technically sound and implementable?
"""

data_flow_analysis_reflection_schema = {
  "type": "object",
  "properties": {
    "reflection_results": {
      "type": "object",
      "properties": {
        "perspective_quality": {
          "type": "object",
          "properties": {
            "issue_analysis": {
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
                    "missed_aspects": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    }
                  },
                  "required": ["rating", "justification", "missed_aspects"]
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
                    "improvement_areas": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    }
                  },
                  "required": ["rating", "justification", "improvement_areas"]
                },
                "impact_assessment": {
                  "type": "object",
                  "properties": {
                    "rating": {
                      "type": "string",
                      "enum": ["high", "medium", "low"]
                    },
                    "justification": {
                      "type": "string"
                    },
                    "underestimated_impacts": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    }
                  },
                  "required": ["rating", "justification", "underestimated_impacts"]
                }
              },
              "required": ["comprehensiveness", "evidence_quality", "impact_assessment"]
            },
            "gap_analysis": {
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
                    "missed_aspects": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    }
                  },
                  "required": ["rating", "justification", "missed_aspects"]
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
                    "improvement_areas": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    }
                  },
                  "required": ["rating", "justification", "improvement_areas"]
                },
                "impact_assessment": {
                  "type": "object",
                  "properties": {
                    "rating": {
                      "type": "string",
                      "enum": ["high", "medium", "low"]
                    },
                    "justification": {
                      "type": "string"
                    },
                    "underestimated_impacts": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    }
                  },
                  "required": ["rating", "justification", "underestimated_impacts"]
                }
              },
              "required": ["comprehensiveness", "evidence_quality", "impact_assessment"]
            }
          },
          "required": ["issue_analysis", "gap_analysis"]
        },
        "item_specific_feedback": {
          "type": "object",
          "properties": {
            "issue_analysis": {
              "type": "object",
              "properties": {
                "circulation_issues": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "item_index": {
                        "type": "integer"
                      },
                      "feedback_type": {
                        "type": "string",
                        "enum": ["missing_evidence", "overstatement", "understatement", "invalid_recommendation"]
                      },
                      "details": {
                        "type": "string"
                      },
                      "correction": {
                        "type": "string"
                      },
                      "recommended_action": {
                        "type": "string",
                        "enum": ["KEEP", "MODIFY", "REMOVE"]
                      }
                    },
                    "required": ["item_index", "feedback_type", "details", "correction", "recommended_action"]
                  }
                },
                "transformation_issues": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "item_index": {
                        "type": "integer"
                      },
                      "feedback_type": {
                        "type": "string",
                        "enum": ["missing_evidence", "overstatement", "understatement", "invalid_recommendation"]
                      },
                      "details": {
                        "type": "string"
                      },
                      "correction": {
                        "type": "string"
                      },
                      "recommended_action": {
                        "type": "string",
                        "enum": ["KEEP", "MODIFY", "REMOVE"]
                      }
                    },
                    "required": ["item_index", "feedback_type", "details", "correction", "recommended_action"]
                  }
                },
                "bottleneck_issues": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "item_index": {
                        "type": "integer"
                      },
                      "feedback_type": {
                        "type": "string",
                        "enum": ["missing_evidence", "overstatement", "understatement", "invalid_recommendation"]
                      },
                      "details": {
                        "type": "string"
                      },
                      "correction": {
                        "type": "string"
                      },
                      "recommended_action": {
                        "type": "string",
                        "enum": ["KEEP", "MODIFY", "REMOVE"]
                      }
                    },
                    "required": ["item_index", "feedback_type", "details", "correction", "recommended_action"]
                  }
                },
                "consistency_issues": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "item_index": {
                        "type": "integer"
                      },
                      "feedback_type": {
                        "type": "string",
                        "enum": ["missing_evidence", "overstatement", "understatement", "invalid_recommendation"]
                      },
                      "details": {
                        "type": "string"
                      },
                      "correction": {
                        "type": "string"
                      },
                      "recommended_action": {
                        "type": "string",
                        "enum": ["KEEP", "MODIFY", "REMOVE"]
                      }
                    },
                    "required": ["item_index", "feedback_type", "details", "correction", "recommended_action"]
                  }
                }
              },
              "required": ["circulation_issues", "transformation_issues", "bottleneck_issues", "consistency_issues"]
            },
            "gap_analysis": {
              "type": "object",
              "properties": {
                "circulation_gaps": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "item_index": {
                        "type": "integer"
                      },
                      "feedback_type": {
                        "type": "string",
                        "enum": ["missing_evidence", "overstatement", "understatement", "invalid_recommendation"]
                      },
                      "details": {
                        "type": "string"
                      },
                      "correction": {
                        "type": "string"
                      },
                      "recommended_action": {
                        "type": "string",
                        "enum": ["KEEP", "MODIFY", "REMOVE"]
                      }
                    },
                    "required": ["item_index", "feedback_type", "details", "correction", "recommended_action"]
                  }
                },
                "transformation_gaps": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "item_index": {
                        "type": "integer"
                      },
                      "feedback_type": {
                        "type": "string",
                        "enum": ["missing_evidence", "overstatement", "understatement", "invalid_recommendation"]
                      },
                      "details": {
                        "type": "string"
                      },
                      "correction": {
                        "type": "string"
                      },
                      "recommended_action": {
                        "type": "string",
                        "enum": ["KEEP", "MODIFY", "REMOVE"]
                      }
                    },
                    "required": ["item_index", "feedback_type", "details", "correction", "recommended_action"]
                  }
                },
                "optimization_gaps": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "item_index": {
                        "type": "integer"
                      },
                      "feedback_type": {
                        "type": "string",
                        "enum": ["missing_evidence", "overstatement", "understatement", "invalid_recommendation"]
                      },
                      "details": {
                        "type": "string"
                      },
                      "correction": {
                        "type": "string"
                      },
                      "recommended_action": {
                        "type": "string",
                        "enum": ["KEEP", "MODIFY", "REMOVE"]
                      }
                    },
                    "required": ["item_index", "feedback_type", "details", "correction", "recommended_action"]
                  }
                },
                "consistency_gaps": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "item_index": {
                        "type": "integer"
                      },
                      "feedback_type": {
                        "type": "string",
                        "enum": ["missing_evidence", "overstatement", "understatement", "invalid_recommendation"]
                      },
                      "details": {
                        "type": "string"
                      },
                      "correction": {
                        "type": "string"
                      },
                      "recommended_action": {
                        "type": "string",
                        "enum": ["KEEP", "MODIFY", "REMOVE"]
                      }
                    },
                    "required": ["item_index", "feedback_type", "details", "correction", "recommended_action"]
                  }
                }
              },
              "required": ["circulation_gaps", "transformation_gaps", "optimization_gaps", "consistency_gaps"]
            }
          },
          "required": ["issue_analysis", "gap_analysis"]
        },
        "missed_items": {
          "type": "object",
          "properties": {
            "missed_issues": {
              "type": "object",
              "properties": {
                "circulation_issues": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "flow_pattern": {
                        "type": "string"
                      },
                      "issue": {
                        "type": "string"
                      },
                      "evidence": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "impact": {
                        "type": "string"
                      },
                      "recommendation": {
                        "type": "string"
                      }
                    },
                    "required": ["flow_pattern", "issue", "evidence", "impact", "recommendation"]
                  }
                },
                "transformation_issues": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "flow_pattern": {
                        "type": "string"
                      },
                      "issue": {
                        "type": "string"
                      },
                      "evidence": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "impact": {
                        "type": "string"
                      },
                      "recommendation": {
                        "type": "string"
                      }
                    },
                    "required": ["flow_pattern", "issue", "evidence", "impact", "recommendation"]
                  }
                },
                "bottleneck_issues": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "flow_pattern": {
                        "type": "string"
                      },
                      "issue": {
                        "type": "string"
                      },
                      "evidence": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "impact": {
                        "type": "string"
                      },
                      "recommendation": {
                        "type": "string"
                      }
                    },
                    "required": ["flow_pattern", "issue", "evidence", "impact", "recommendation"]
                  }
                },
                "consistency_issues": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "flow_pattern": {
                        "type": "string"
                      },
                      "issue": {
                        "type": "string"
                      },
                      "evidence": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "impact": {
                        "type": "string"
                      },
                      "recommendation": {
                        "type": "string"
                      }
                    },
                    "required": ["flow_pattern", "issue", "evidence", "impact", "recommendation"]
                  }
                }
              },
              "required": ["circulation_issues", "transformation_issues", "bottleneck_issues", "consistency_issues"]
            },
            "missed_gaps": {
              "type": "object",
              "properties": {
                "circulation_gaps": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "missing_pattern": {
                        "type": "string"
                      },
                      "evidence": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "impact": {
                        "type": "string"
                      },
                      "recommendation": {
                        "type": "string"
                      }
                    },
                    "required": ["missing_pattern", "evidence", "impact", "recommendation"]
                  }
                },
                "transformation_gaps": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "missing_process": {
                        "type": "string"
                      },
                      "evidence": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "impact": {
                        "type": "string"
                      },
                      "recommendation": {
                        "type": "string"
                      }
                    },
                    "required": ["missing_process", "evidence", "impact", "recommendation"]
                  }
                },
                "optimization_gaps": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "missing_optimization": {
                        "type": "string"
                      },
                      "evidence": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "impact": {
                        "type": "string"
                      },
                      "recommendation": {
                        "type": "string"
                      }
                    },
                    "required": ["missing_optimization", "evidence", "impact", "recommendation"]
                  }
                },
                "consistency_gaps": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "missing_mechanism": {
                        "type": "string"
                      },
                      "evidence": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "impact": {
                        "type": "string"
                      },
                      "recommendation": {
                        "type": "string"
                      }
                    },
                    "required": ["missing_mechanism", "evidence", "impact", "recommendation"]
                  }
                }
              },
              "required": ["circulation_gaps", "transformation_gaps", "optimization_gaps", "consistency_gaps"]
            }
          },
          "required": ["missed_issues", "missed_gaps"]
        },
        "synthesis_feedback": {
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
                "type": "string"
              }
            },
            "improvement_suggestions": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "required": ["quality", "missed_connections", "improvement_suggestions"]
        }
      },
      "required": ["perspective_quality", "item_specific_feedback", "missed_items", "synthesis_feedback"]
    }
  },
  "required": ["reflection_results"]
}

data_flow_analysis_revision_prompt = """
# Worm Agent Revision Prompt

You are the Worm Agent processing reflection results to implement self-corrections to your dual-perspective data flow analysis. Your role is to systematically address identified issues from the reflection phase to ensure comprehensive identification of critical data flow issues and gaps.

## Core Responsibilities
1. Process reflection feedback on your dual-perspective data flow analysis
2. Implement targeted corrections for identified issues and gaps
3. Address missed items identified during reflection
4. Enhance evidence quality where indicated
5. Refine impact assessments to better reflect potential consequences
6. Improve recommendations to be more specific and actionable
7. Enhance the synthesis between issue and gap perspectives

## Input Format

You will receive two inputs:
1. Your original dual-perspective data flow analysis output
2. Reflection results in the following structure:
```json
{"reflection_results": {"perspective_quality": {"issue_analysis": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "impact_assessment": {"rating": "high|medium|low", "justification": "string", "underestimated_impacts": ["strings"]}}, "gap_analysis": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "impact_assessment": {"rating": "high|medium|low", "justification": "string", "underestimated_impacts": ["strings"]}}}, "item_specific_feedback": {"issue_analysis": {"circulation_issues": [{"item_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "transformation_issues": [{"item_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "bottleneck_issues": [{"item_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "consistency_issues": [{"item_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}]}, "gap_analysis": {"circulation_gaps": [{"item_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "transformation_gaps": [{"item_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "optimization_gaps": [{"item_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}], "consistency_gaps": [{"item_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string", "recommended_action": "KEEP|MODIFY|REMOVE"}]}}, "missed_items": {"missed_issues": {"circulation_issues": [{"flow_pattern": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "transformation_issues": [{"flow_pattern": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "bottleneck_issues": [{"flow_pattern": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "consistency_issues": [{"flow_pattern": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}]}, "missed_gaps": {"circulation_gaps": [{"missing_pattern": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "transformation_gaps": [{"missing_process": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "optimization_gaps": [{"missing_optimization": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "consistency_gaps": [{"missing_mechanism": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}]}}, "synthesis_feedback": {"quality": {"rating": "high|medium|low", "justification": "string"}, "missed_connections": ["strings"], "improvement_suggestions": ["strings"]}}}
```

## Revision Process

1. Analyze reflection feedback systematically
2. Implement corrections for each specific issue and gap
3. Incorporate all missed issues and gaps identified in reflection
4. Enhance evidence quality where indicated
5. Refine impact assessments to be more accurate
6. Improve recommendations to be more actionable
7. Strengthen the synthesis to better integrate both perspectives

## Output Format

Provide your revised analysis in the following JSON format:

```json
{"revision_metadata": {"processed_feedback": {"perspective_improvements": {"issue_analysis": {"comprehensiveness": ["strings"], "evidence_quality": ["strings"], "impact_assessment": ["strings"]}, "gap_analysis": {"comprehensiveness": ["strings"], "evidence_quality": ["strings"], "impact_assessment": ["strings"]}}, "item_adjustments": {"items_removed": {"issues": integer, "gaps": integer}, "items_modified": {"issues": integer, "gaps": integer}, "items_added": {"issues": integer, "gaps": integer}}, "synthesis_improvements": ["strings"]}, "validation_steps": ["strings"]}, "dual_perspective_analysis": {"issue_analysis": {"circulation_issues": [{"flow_pattern": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "transformation_issues": [{"flow_pattern": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "bottleneck_issues": [{"flow_pattern": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "consistency_issues": [{"flow_pattern": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}]}, "gap_analysis": {"circulation_gaps": [{"missing_pattern": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "transformation_gaps": [{"missing_process": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "optimization_gaps": [{"missing_optimization": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "consistency_gaps": [{"missing_mechanism": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}]}, "synthesis": {"key_observations": ["strings"], "cross_cutting_concerns": ["strings"], "prioritized_recommendations": [{"area": "string", "recommendation": "string", "justification": "string", "revision_note": "string"}]}}}
```

## Revision Guidelines

### Perspective Improvements
- Enhance the completeness of issue and gap identification
- Strengthen evidence with specific examples
- Refine impact statements to accurately reflect consequences
- Make recommendations more specific and actionable

### Item Adjustments
- Remove items where recommended_action is REMOVE
- Modify items where recommended_action is MODIFY
- Add all missed issues and gaps identified in reflection
- Ensure each item has appropriate evidence and impact assessment

### Synthesis Improvements
- Strengthen connections between identified issues and gaps
- Enhance cross-cutting concern identification
- Refine prioritized recommendations
- Ensure holistic integration of both perspectives

## Validation Checklist

Before finalizing your revised analysis:
1. Verify that all specific feedback has been addressed
2. Confirm that all missed items have been incorporated
3. Check that evidence is specific and concrete for all items
4. Ensure impact statements accurately reflect potential consequences
5. Validate that all recommendations are specific and actionable
6. Confirm consistency in detail level across all categories
7. Verify technical accuracy of all assessments and recommendations
8. Ensure the synthesis effectively integrates both perspectives

## Self-Correction Principles

1. Prioritize substantive improvements over superficial changes
2. Focus on technical accuracy and data flow clarity
3. Ensure recommendations are implementable
4. Maintain consistent level of detail across all issue and gap types
5. Verify that each item has sufficient supporting evidence
6. Ensure impact statements reflect the true potential consequences
7. Make all corrections based on concrete, specific feedback
8. Strengthen the integration between issue and gap perspectives
"""

data_flow_analysis_revision_schema = {
  "type": "object",
  "properties": {
    "revision_metadata": {
      "type": "object",
      "properties": {
        "processed_feedback": {
          "type": "object",
          "properties": {
            "perspective_improvements": {
              "type": "object",
              "properties": {
                "issue_analysis": {
                  "type": "object",
                  "properties": {
                    "comprehensiveness": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    },
                    "evidence_quality": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    },
                    "impact_assessment": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    }
                  },
                  "required": ["comprehensiveness", "evidence_quality", "impact_assessment"]
                },
                "gap_analysis": {
                  "type": "object",
                  "properties": {
                    "comprehensiveness": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    },
                    "evidence_quality": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    },
                    "impact_assessment": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    }
                  },
                  "required": ["comprehensiveness", "evidence_quality", "impact_assessment"]
                }
              },
              "required": ["issue_analysis", "gap_analysis"]
            },
            "item_adjustments": {
              "type": "object",
              "properties": {
                "items_removed": {
                  "type": "object",
                  "properties": {
                    "issues": {
                      "type": "integer"
                    },
                    "gaps": {
                      "type": "integer"
                    }
                  },
                  "required": ["issues", "gaps"]
                },
                "items_modified": {
                  "type": "object",
                  "properties": {
                    "issues": {
                      "type": "integer"
                    },
                    "gaps": {
                      "type": "integer"
                    }
                  },
                  "required": ["issues", "gaps"]
                },
                "items_added": {
                  "type": "object",
                  "properties": {
                    "issues": {
                      "type": "integer"
                    },
                    "gaps": {
                      "type": "integer"
                    }
                  },
                  "required": ["issues", "gaps"]
                }
              },
              "required": ["items_removed", "items_modified", "items_added"]
            },
            "synthesis_improvements": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "required": ["perspective_improvements", "item_adjustments", "synthesis_improvements"]
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
    "dual_perspective_analysis": {
      "type": "object",
      "properties": {
        "issue_analysis": {
          "type": "object",
          "properties": {
            "circulation_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "flow_pattern": {
                    "type": "string"
                  },
                  "issue": {
                    "type": "string"
                  },
                  "impact": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "recommendation": {
                    "type": "string"
                  },
                  "revision_note": {
                    "type": "string"
                  }
                },
                "required": ["flow_pattern", "issue", "impact", "evidence", "recommendation", "revision_note"]
              }
            },
            "transformation_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "flow_pattern": {
                    "type": "string"
                  },
                  "issue": {
                    "type": "string"
                  },
                  "impact": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "recommendation": {
                    "type": "string"
                  },
                  "revision_note": {
                    "type": "string"
                  }
                },
                "required": ["flow_pattern", "issue", "impact", "evidence", "recommendation", "revision_note"]
              }
            },
            "bottleneck_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "flow_pattern": {
                    "type": "string"
                  },
                  "issue": {
                    "type": "string"
                  },
                  "impact": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "recommendation": {
                    "type": "string"
                  },
                  "revision_note": {
                    "type": "string"
                  }
                },
                "required": ["flow_pattern", "issue", "impact", "evidence", "recommendation", "revision_note"]
              }
            },
            "consistency_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "flow_pattern": {
                    "type": "string"
                  },
                  "issue": {
                    "type": "string"
                  },
                  "impact": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "recommendation": {
                    "type": "string"
                  },
                  "revision_note": {
                    "type": "string"
                  }
                },
                "required": ["flow_pattern", "issue", "impact", "evidence", "recommendation", "revision_note"]
              }
            }
          },
          "required": ["circulation_issues", "transformation_issues", "bottleneck_issues", "consistency_issues"]
        },
        "gap_analysis": {
          "type": "object",
          "properties": {
            "circulation_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "missing_pattern": {
                    "type": "string"
                  },
                  "impact": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "recommendation": {
                    "type": "string"
                  },
                  "revision_note": {
                    "type": "string"
                  }
                },
                "required": ["missing_pattern", "impact", "evidence", "recommendation", "revision_note"]
              }
            },
            "transformation_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "missing_process": {
                    "type": "string"
                  },
                  "impact": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "recommendation": {
                    "type": "string"
                  },
                  "revision_note": {
                    "type": "string"
                  }
                },
                "required": ["missing_process", "impact", "evidence", "recommendation", "revision_note"]
              }
            },
            "optimization_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "missing_optimization": {
                    "type": "string"
                  },
                  "impact": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "recommendation": {
                    "type": "string"
                  },
                  "revision_note": {
                    "type": "string"
                  }
                },
                "required": ["missing_optimization", "impact", "evidence", "recommendation", "revision_note"]
              }
            },
            "consistency_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "missing_mechanism": {
                    "type": "string"
                  },
                  "impact": {
                    "type": "string"
                  },
                  "evidence": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "recommendation": {
                    "type": "string"
                  },
                  "revision_note": {
                    "type": "string"
                  }
                },
                "required": ["missing_mechanism", "impact", "evidence", "recommendation", "revision_note"]
              }
            }
          },
          "required": ["circulation_gaps", "transformation_gaps", "optimization_gaps", "consistency_gaps"]
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
            "cross_cutting_concerns": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "prioritized_recommendations": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "area": {
                    "type": "string"
                  },
                  "recommendation": {
                    "type": "string"
                  },
                  "justification": {
                    "type": "string"
                  },
                  "revision_note": {
                    "type": "string"
                  }
                },
                "required": ["area", "recommendation", "justification", "revision_note"]
              }
            }
          },
          "required": ["key_observations", "cross_cutting_concerns", "prioritized_recommendations"]
        }
      },
      "required": ["issue_analysis", "gap_analysis", "synthesis"]
    }
  },
  "required": ["revision_metadata", "dual_perspective_analysis"]
}