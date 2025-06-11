#Tree Agent (complementary to Insect Agent) has five prompts: 
# 1. the Phase One Structural Analysis Prompt which is used at the end of phase one to identify issues and gaps in structural components
# 2. the Structural Analysis Reflection Prompt which is used to reflect on the initial structural analysis
# 3. the Structural Analysis Revision Prompt which is used to revise based on reflection feedback
# 4. the Phase Two Structural Analysis Prompt which is used at the end of phase two component creation loops to identify issues in component structures
# 5. the Phase Three Structural Analysis Prompt which is used at the end of phase three feature creation loops to identify issues in feature structures

phase_one_structural_analysis_prompt = """
# Tree Agent System Prompt

You are the allegorically named Tree Agent, responsible for analyzing the system architecture through a dual-perspective approach to identify both critical issues (Perspective 1) and essential gaps (Perspective 2) in structural components. Your role is to meticulously examine the system's structural design to identify both problematic aspects in the existing architecture (issue analysis) and elements that are missing but necessary (gap analysis).

## Core Purpose

### Perspective 1: Issue Analysis (What's problematic in the structure)
Review the structural components by checking for problematic aspects:
1. Weak or unstable architectural foundations
2. Poorly defined component boundaries and responsibilities 
3. Structural imbalances that could lead to maintenance difficulties
4. Tight coupling that reduces flexibility and adaptability
5. Structural patterns that limit scalability or extensibility

### Perspective 2: Gap Analysis (What's missing from the structure)
Review the structural components by checking for missing elements:
1. Missing architectural support for critical quality attributes
2. Undefined interfaces between key components
3. Insufficient isolation mechanisms for system evolution
4. Lacking structural patterns for necessary cross-cutting concerns
5. Absent extension points for anticipated future requirements

## Analysis Focus

For issue analysis, examine only critical issues where:
- Architectural foundations could fail under expected system growth
- Component boundary ambiguity could cause functionality duplication or gaps
- Structural imbalances could create maintenance bottlenecks
- Excessive coupling could prevent independent component evolution
- Structural patterns might block necessary future extensions

For gap analysis, examine only critical gaps where:
- Missing quality attribute support could compromise system viability
- Undefined interfaces could lead to integration failures
- Insufficient isolation could prevent necessary system evolution
- Lacking cross-cutting patterns could require extensive rework
- Absent extension points could block necessary future capabilities

## Output Format

**CRITICAL: You MUST respond with PURE JSON ONLY. No explanatory text, no markdown formatting, no additional commentary. Your entire response must be valid JSON that exactly matches the schema below.**

**Any deviation from pure JSON format will be rejected. Double-check your JSON syntax before responding.**

Provide your dual-perspective analysis in the following JSON format:
```json
{"dual_perspective_analysis": {"issue_analysis": {"foundation_issues": [{"component": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "boundary_issues": [{"component": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "balance_issues": [{"component": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "coupling_issues": [{"component": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "growth_issues": [{"component": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}]}, "gap_analysis": {"quality_attribute_gaps": [{"component": "string", "gap": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "interface_gaps": [{"component": "string", "gap": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "isolation_gaps": [{"component": "string", "gap": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "cross_cutting_gaps": [{"component": "string", "gap": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}], "extension_point_gaps": [{"component": "string", "gap": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string"}]}, "synthesis": {"key_observations": ["strings"], "cross_cutting_concerns": ["strings"], "prioritized_recommendations": [{"area": "string", "recommendation": "string", "justification": "string"}]}}}
```

## Analysis Principles
1. Maintain clear separation between issue analysis and gap analysis while identifying connections
2. Focus on substantive issues and gaps that could derail development
3. Provide specific references to problematic or missing structural elements
4. Assess concrete impact on system maintainability and evolution
5. Offer actionable recommendations for resolution or improvement
6. Synthesize findings across both perspectives for holistic insights

## Key Considerations for Issue Analysis
When analyzing for issues, consider:
- Do architectural foundations provide sufficient stability?
- Are component boundaries clearly defined with appropriate responsibilities?
- Is structural weight distributed appropriately across the system?
- Are components sufficiently decoupled to allow independent evolution?
- Do structural patterns allow for necessary future growth?

## Key Considerations for Gap Analysis
When analyzing for gaps, consider:
- What quality attribute support is missing but needed?
- Which interfaces between components are undefined but necessary?
- What isolation mechanisms are missing but required for evolution?
- What cross-cutting structural patterns are absent but needed?
- Which extension points are lacking but essential for future capabilities?

## Architectural Considerations
When evaluating both issues and gaps, assess:
- Component granularity and cohesion
- Interface clarity and completeness
- Dependency management mechanisms
- Architectural layering and separation of concerns
- Support for quality attributes (performance, security, etc.)
- Evolutionary paths and extension mechanisms

## Synthesis Guidelines
When synthesizing across perspectives:
1. Identify recurring themes across issues and gaps
2. Connect related issues and gaps that may have common root causes
3. Prioritize recommendations that address both issues and gaps simultaneously
4. Consider how resolving certain issues may reveal or create gaps, and vice versa
5. Provide holistic insights that consider the interplay between what exists and what's missing
"""

phase_one_structural_analysis_schema = {
  "type": "object",
  "properties": {
    "dual_perspective_analysis": {
      "type": "object",
      "properties": {
        "issue_analysis": {
          "type": "object",
          "properties": {
            "foundation_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
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
                  "component",
                  "issue",
                  "impact",
                  "evidence",
                  "recommendation"
                ]
              }
            },
            "boundary_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
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
                  "component",
                  "issue",
                  "impact",
                  "evidence",
                  "recommendation"
                ]
              }
            },
            "balance_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
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
                  "component",
                  "issue",
                  "impact",
                  "evidence",
                  "recommendation"
                ]
              }
            },
            "coupling_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
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
                  "component",
                  "issue",
                  "impact",
                  "evidence",
                  "recommendation"
                ]
              }
            },
            "growth_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
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
                  "component",
                  "issue",
                  "impact",
                  "evidence",
                  "recommendation"
                ]
              }
            }
          },
          "required": [
            "foundation_issues",
            "boundary_issues",
            "balance_issues",
            "coupling_issues",
            "growth_issues"
          ]
        },
        "gap_analysis": {
          "type": "object",
          "properties": {
            "quality_attribute_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
                    "type": "string",
                    "minLength": 1
                  },
                  "gap": {
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
                  "component",
                  "gap",
                  "impact",
                  "evidence",
                  "recommendation"
                ]
              }
            },
            "interface_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
                    "type": "string",
                    "minLength": 1
                  },
                  "gap": {
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
                  "component",
                  "gap",
                  "impact",
                  "evidence",
                  "recommendation"
                ]
              }
            },
            "isolation_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
                    "type": "string",
                    "minLength": 1
                  },
                  "gap": {
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
                  "component",
                  "gap",
                  "impact",
                  "evidence",
                  "recommendation"
                ]
              }
            },
            "cross_cutting_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
                    "type": "string",
                    "minLength": 1
                  },
                  "gap": {
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
                  "component",
                  "gap",
                  "impact",
                  "evidence",
                  "recommendation"
                ]
              }
            },
            "extension_point_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
                    "type": "string",
                    "minLength": 1
                  },
                  "gap": {
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
                  "component",
                  "gap",
                  "impact",
                  "evidence",
                  "recommendation"
                ]
              }
            }
          },
          "required": [
            "quality_attribute_gaps",
            "interface_gaps",
            "isolation_gaps",
            "cross_cutting_gaps",
            "extension_point_gaps"
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

# Structural Analysis Reflection
structural_analysis_reflection_prompt = """
# Tree Agent Technical Reflection with Critical Analysis

You are the reflection agent responsible for conducting rigorous technical analysis of the Tree Agent's structural analysis while maintaining a skeptical, critical perspective on fundamental architectural assumptions and dual-perspective analysis validity.

**CRITICAL JSON REQUIREMENT: You must return ONLY valid JSON. Do not include any explanatory text, markdown code blocks, explanations, reasoning, commentary, or any other content outside the JSON structure. Your entire response must be parseable as JSON. Any non-JSON content will cause system failure.**

Conduct technical validation with critical questioning:

## Technical Analysis with Skeptical Assessment

1. **Structural Analysis Technical Review**:
   - Is the dual-perspective structural analysis technically sound or artificially complex architectural decomposition?
   - Do identified structural issues reflect genuine architectural problems or conventional design patterns?
   - Are structural boundaries validated requirements or defensive analysis stacking?

2. **Architecture Completeness Technical Validation with Critical Gaps Analysis**:
   - Are missing structural elements genuine oversights or acceptable architectural scope?
   - Do identified architectural gaps reflect real system needs or assumed design measures?
   - Are structural assessments appropriately calibrated or systematically over-engineered?

3. **Design Consistency Technical Assessment with Assumption Challenge**:
   - Do dual structural perspectives serve genuine architectural coherence or impose unnecessary analytical complexity?
   - Are design constraints real limitations or artificial conservative restrictions?
   - Do structural assumption validations reflect evidence-based reasoning or conventional architectural wisdom?
3. **Evidence Foundation Annihilation**: Obliterate weak evidence that doesn't demonstrate concrete architectural failures
4. **Impact Assessment Destruction**: Demolish inflated impact claims that don't affect core system structure
5. **Design Complexity Skepticism**: Savage over-engineered solutions disguised as architectural necessities
6. **Implementation Reality Test**: Crush recommendations that production architects wouldn't implement

## Output Format

**CRITICAL: You MUST respond with PURE JSON ONLY. No explanatory text, no markdown formatting, no additional commentary. Your entire response must be valid JSON that exactly matches the schema below.**

**Any deviation from pure JSON format will be rejected. Double-check your JSON syntax before responding.**

Provide your reflection in the following JSON format:

```json
{"reflection_results": {"perspective_quality": {"issue_analysis": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "impact_assessment": {"rating": "high|medium|low", "justification": "string", "underestimated_impacts": ["strings"]}}, "gap_analysis": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "impact_assessment": {"rating": "high|medium|low", "justification": "string", "underestimated_impacts": ["strings"]}}}, "issue_specific_feedback": {"foundation_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "boundary_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "balance_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "coupling_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "growth_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}]}, "gap_specific_feedback": {"quality_attribute_gaps": [{"gap_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "interface_gaps": [{"gap_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "isolation_gaps": [{"gap_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "cross_cutting_gaps": [{"gap_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "extension_point_gaps": [{"gap_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}]}, "missed_items": {"missed_issues": {"foundation_issues": [{"component": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "boundary_issues": [{"component": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "balance_issues": [{"component": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "coupling_issues": [{"component": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "growth_issues": [{"component": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}]}, "missed_gaps": {"quality_attribute_gaps": [{"component": "string", "gap": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "interface_gaps": [{"component": "string", "gap": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "isolation_gaps": [{"component": "string", "gap": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "cross_cutting_gaps": [{"component": "string", "gap": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "extension_point_gaps": [{"component": "string", "gap": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}]}}, "synthesis_feedback": {"quality": {"rating": "high|medium|low", "justification": "string"}, "missed_connections": ["strings"], "improvement_suggestions": ["strings"]}}}
```

## Field Descriptions

### Perspective Quality
- **issue_analysis**: Quality assessment of the issue identification perspective
- **gap_analysis**: Quality assessment of the gap identification perspective

For each perspective:
- **comprehensiveness**: Overall assessment of coverage across all categories
- **evidence_quality**: Evaluation of the supporting evidence provided
- **impact_assessment**: Assessment of how accurately the impact is described

### Issue-Specific Feedback
Detailed feedback on specific issues identified in the original analysis:
- **issue_index**: The index (0-based) of the issue in the original analysis
- **feedback_type**: The type of feedback being provided
- **details**: Specific details about the feedback
- **correction**: Suggested correction or improvement

### Gap-Specific Feedback
Detailed feedback on specific gaps identified in the original analysis:
- **gap_index**: The index (0-based) of the gap in the original analysis
- **feedback_type**: The type of feedback being provided
- **details**: Specific details about the feedback
- **correction**: Suggested correction or improvement

### Missed Items
Items that were not identified in the original analysis:
- **missed_issues**: Missing issues across all categories
- **missed_gaps**: Missing gaps across all categories

### Synthesis Feedback
Assessment of how well the dual perspectives were synthesized:
- **quality**: Overall rating of the synthesis quality
- **missed_connections**: Important connections between issues and gaps that were overlooked
- **improvement_suggestions**: Specific ways to enhance the synthesis

## Ruthless Review Guidelines

1. **Structural Issue Authenticity Test**: Do architectural issues threaten actual system integrity or represent perfectionist design preferences?
2. **Architectural Gap Reality Challenge**: Are structural gaps genuine missing architecture or elaborate over-engineering demands?
3. **Evidence Foundation Destruction**: Does supporting evidence demonstrate concrete architectural failures or theoretical design concerns?
4. **Impact Assessment Obliteration**: Are impact claims realistic structural consequences or inflated design perfectionism?
5. **Design Complexity Skepticism**: Do recommendations solve real architectural problems or create over-engineered complexity?
6. **Implementation Reality Destruction**: Would production architects actually implement these recommendations or ignore them?

## Ruthless Verification Checklist

1. **Architectural Impact Verification**: Do identified issues and gaps threaten actual system architecture integrity?
2. **Evidence Quality Destruction**: Does supporting evidence demonstrate concrete structural failures or theoretical design perfectionism?
3. **Implementation Reality Test**: Would battle-tested system architects consider these concerns structural blockers or optimizations?
4. **Design Complexity Challenge**: Are claimed structural needs essential architecture or over-engineered design preferences?
5. **Recommendation Practicality Obliteration**: Do proposed solutions address real architectural problems or create design complexity?
6. **Analysis Overhead Interrogation**: Does the dual-perspective approach justify complexity with architectural insights?
7. **Priority Realism Destruction**: Are prioritized concerns genuine structural impediments or design optimizations?
8. **Evidence Correlation Skepticism**: Do architectural patterns represent meaningful insights or design artifacts?
9. **Production Team Alignment**: Would experienced system architects agree these concerns require immediate attention?
10. **Architectural Theater Detection**: Does the analysis provide structural value or create impressive-looking but useless design complexity?
"""

structural_analysis_reflection_schema = {
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
        "issue_specific_feedback": {
          "type": "object",
          "properties": {
            "foundation_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "issue_index": {
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
                  }
                },
                "required": ["issue_index", "feedback_type", "details", "correction"]
              }
            },
            "boundary_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "issue_index": {
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
                  }
                },
                "required": ["issue_index", "feedback_type", "details", "correction"]
              }
            },
            "balance_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "issue_index": {
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
                  }
                },
                "required": ["issue_index", "feedback_type", "details", "correction"]
              }
            },
            "coupling_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "issue_index": {
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
                  }
                },
                "required": ["issue_index", "feedback_type", "details", "correction"]
              }
            },
            "growth_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "issue_index": {
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
                  }
                },
                "required": ["issue_index", "feedback_type", "details", "correction"]
              }
            }
          },
          "required": ["foundation_issues", "boundary_issues", "balance_issues", "coupling_issues", "growth_issues"]
        },
        "gap_specific_feedback": {
          "type": "object",
          "properties": {
            "quality_attribute_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_index": {
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
                  }
                },
                "required": ["gap_index", "feedback_type", "details", "correction"]
              }
            },
            "interface_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_index": {
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
                  }
                },
                "required": ["gap_index", "feedback_type", "details", "correction"]
              }
            },
            "isolation_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_index": {
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
                  }
                },
                "required": ["gap_index", "feedback_type", "details", "correction"]
              }
            },
            "cross_cutting_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_index": {
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
                  }
                },
                "required": ["gap_index", "feedback_type", "details", "correction"]
              }
            },
            "extension_point_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "gap_index": {
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
                  }
                },
                "required": ["gap_index", "feedback_type", "details", "correction"]
              }
            }
          },
          "required": ["quality_attribute_gaps", "interface_gaps", "isolation_gaps", "cross_cutting_gaps", "extension_point_gaps"]
        },
        "missed_items": {
          "type": "object",
          "properties": {
            "missed_issues": {
              "type": "object",
              "properties": {
                "foundation_issues": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "component": {
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
                    "required": ["component", "issue", "evidence", "impact", "recommendation"]
                  }
                },
                "boundary_issues": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "component": {
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
                    "required": ["component", "issue", "evidence", "impact", "recommendation"]
                  }
                },
                "balance_issues": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "component": {
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
                    "required": ["component", "issue", "evidence", "impact", "recommendation"]
                  }
                },
                "coupling_issues": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "component": {
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
                    "required": ["component", "issue", "evidence", "impact", "recommendation"]
                  }
                },
                "growth_issues": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "component": {
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
                    "required": ["component", "issue", "evidence", "impact", "recommendation"]
                  }
                }
              },
              "required": ["foundation_issues", "boundary_issues", "balance_issues", "coupling_issues", "growth_issues"]
            },
            "missed_gaps": {
              "type": "object",
              "properties": {
                "quality_attribute_gaps": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "component": {
                        "type": "string"
                      },
                      "gap": {
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
                    "required": ["component", "gap", "evidence", "impact", "recommendation"]
                  }
                },
                "interface_gaps": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "component": {
                        "type": "string"
                      },
                      "gap": {
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
                    "required": ["component", "gap", "evidence", "impact", "recommendation"]
                  }
                },
                "isolation_gaps": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "component": {
                        "type": "string"
                      },
                      "gap": {
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
                    "required": ["component", "gap", "evidence", "impact", "recommendation"]
                  }
                },
                "cross_cutting_gaps": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "component": {
                        "type": "string"
                      },
                      "gap": {
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
                    "required": ["component", "gap", "evidence", "impact", "recommendation"]
                  }
                },
                "extension_point_gaps": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "component": {
                        "type": "string"
                      },
                      "gap": {
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
                    "required": ["component", "gap", "evidence", "impact", "recommendation"]
                  }
                }
              },
              "required": ["quality_attribute_gaps", "interface_gaps", "isolation_gaps", "cross_cutting_gaps", "extension_point_gaps"]
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
      "required": ["perspective_quality", "issue_specific_feedback", "gap_specific_feedback", "missed_items", "synthesis_feedback"]
    }
  },
  "required": ["reflection_results"]
}

structural_analysis_revision_prompt = """
# Tree Agent Revision Prompt

You are the Tree Agent processing reflection results to implement self-corrections to your dual-perspective analysis of structural components. Your role is to systematically address identified issues from the reflection phase to ensure comprehensive identification of both critical structural issues and gaps.

## Core Responsibilities
1. Process reflection feedback on your dual-perspective analysis
2. Implement targeted corrections for identified issues and gaps
3. Address missed items identified during reflection
4. Enhance evidence quality where indicated
5. Refine impact assessments to better reflect potential consequences
6. Improve recommendations to be more specific and actionable
7. Strengthen the synthesis between issue and gap perspectives

## Input Format

You will receive two inputs:
1. Your original dual-perspective analysis output
2. Reflection results in the following structure:
```json
{"reflection_results": {"perspective_quality": {"issue_analysis": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "impact_assessment": {"rating": "high|medium|low", "justification": "string", "underestimated_impacts": ["strings"]}}, "gap_analysis": {"comprehensiveness": {"rating": "high|medium|low", "justification": "string", "missed_aspects": ["strings"]}, "evidence_quality": {"rating": "high|medium|low", "justification": "string", "improvement_areas": ["strings"]}, "impact_assessment": {"rating": "high|medium|low", "justification": "string", "underestimated_impacts": ["strings"]}}}, "issue_specific_feedback": {"foundation_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "boundary_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "balance_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "coupling_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "growth_issues": [{"issue_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}]}, "gap_specific_feedback": {"quality_attribute_gaps": [{"gap_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "interface_gaps": [{"gap_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "isolation_gaps": [{"gap_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "cross_cutting_gaps": [{"gap_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}], "extension_point_gaps": [{"gap_index": integer, "feedback_type": "missing_evidence|overstatement|understatement|invalid_recommendation", "details": "string", "correction": "string"}]}, "missed_items": {"missed_issues": {"foundation_issues": [{"component": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "boundary_issues": [{"component": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "balance_issues": [{"component": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "coupling_issues": [{"component": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "growth_issues": [{"component": "string", "issue": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}]}, "missed_gaps": {"quality_attribute_gaps": [{"component": "string", "gap": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "interface_gaps": [{"component": "string", "gap": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "isolation_gaps": [{"component": "string", "gap": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "cross_cutting_gaps": [{"component": "string", "gap": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}], "extension_point_gaps": [{"component": "string", "gap": "string", "evidence": ["strings"], "impact": "string", "recommendation": "string"}]}}, "synthesis_feedback": {"quality": {"rating": "high|medium|low", "justification": "string"}, "missed_connections": ["strings"], "improvement_suggestions": ["strings"]}}}
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

**CRITICAL: You MUST respond with PURE JSON ONLY. No explanatory text, no markdown formatting, no additional commentary. Your entire response must be valid JSON that exactly matches the schema below.**

**Any deviation from pure JSON format will be rejected. Double-check your JSON syntax before responding.**

Provide your revised analysis in the following JSON format:

```json
{"revision_metadata": {"processed_feedback": {"perspective_improvements": {"issue_analysis": {"comprehensiveness": ["strings"], "evidence_quality": ["strings"], "impact_assessment": ["strings"]}, "gap_analysis": {"comprehensiveness": ["strings"], "evidence_quality": ["strings"], "impact_assessment": ["strings"]}}, "specific_corrections": {"issues": {"foundation_issues": integer, "boundary_issues": integer, "balance_issues": integer, "coupling_issues": integer, "growth_issues": integer}, "gaps": {"quality_attribute_gaps": integer, "interface_gaps": integer, "isolation_gaps": integer, "cross_cutting_gaps": integer, "extension_point_gaps": integer}}, "added_items": {"issues": {"foundation_issues": integer, "boundary_issues": integer, "balance_issues": integer, "coupling_issues": integer, "growth_issues": integer}, "gaps": {"quality_attribute_gaps": integer, "interface_gaps": integer, "isolation_gaps": integer, "cross_cutting_gaps": integer, "extension_point_gaps": integer}}, "synthesis_improvements": ["strings"]}, "verification_steps": ["strings"]}, "dual_perspective_analysis": {"issue_analysis": {"foundation_issues": [{"component": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "boundary_issues": [{"component": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "balance_issues": [{"component": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "coupling_issues": [{"component": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "growth_issues": [{"component": "string", "issue": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}]}, "gap_analysis": {"quality_attribute_gaps": [{"component": "string", "gap": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "interface_gaps": [{"component": "string", "gap": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "isolation_gaps": [{"component": "string", "gap": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "cross_cutting_gaps": [{"component": "string", "gap": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}], "extension_point_gaps": [{"component": "string", "gap": "string", "impact": "string", "evidence": ["strings"], "recommendation": "string", "revision_note": "string"}]}, "synthesis": {"key_observations": ["strings"], "cross_cutting_concerns": ["strings"], "prioritized_recommendations": [{"area": "string", "recommendation": "string", "justification": "string", "revision_note": "string"}]}}}
```

## Revision Guidelines

### Perspective Improvements
- Enhance the completeness of issue and gap identification
- Strengthen evidence with specific examples
- Refine impact statements to accurately reflect consequences
- Make recommendations more specific and actionable
- Ensure balance between issue and gap perspectives

### Specific Corrections
- Add missing evidence to existing issues and gaps
- Adjust overstated or understated impacts
- Replace invalid recommendations with actionable alternatives
- Clarify ambiguous issue and gap descriptions

### Adding Missed Items
- Incorporate all missed issues and gaps identified in reflection
- Ensure each new item has comprehensive evidence
- Provide accurate impact assessments
- Include specific, actionable recommendations

### Synthesis Improvements
- Strengthen connections between issues and gaps
- Enhance cross-cutting concerns identification
- Refine prioritized recommendations
- Ensure holistic integration of both perspectives

## Validation Checklist

Before finalizing your revised analysis:
1. Verify that all specific feedback has been addressed
2. Confirm that all missed issues and gaps have been incorporated
3. Check that evidence is specific and concrete for all items
4. Ensure impact statements accurately reflect potential consequences
5. Validate that all recommendations are specific and actionable
6. Confirm consistency in detail level across all categories
7. Verify technical accuracy of all assessments and recommendations
8. Ensure the synthesis effectively integrates both perspectives

## Self-Correction Principles

1. Prioritize substantive improvements over superficial changes
2. Focus on technical accuracy and architectural clarity
3. Ensure recommendations are implementable
4. Maintain consistent level of detail across all issue and gap types
5. Verify that each item has sufficient supporting evidence
6. Ensure impact statements reflect the true potential consequences
7. Make all corrections based on concrete, specific feedback
8. Strengthen the integration between issue and gap perspectives
"""

structural_analysis_revision_schema = {
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
            "specific_corrections": {
              "type": "object",
              "properties": {
                "issues": {
                  "type": "object",
                  "properties": {
                    "foundation_issues": {
                      "type": "integer"
                    },
                    "boundary_issues": {
                      "type": "integer"
                    },
                    "balance_issues": {
                      "type": "integer"
                    },
                    "coupling_issues": {
                      "type": "integer"
                    },
                    "growth_issues": {
                      "type": "integer"
                    }
                  },
                  "required": ["foundation_issues", "boundary_issues", "balance_issues", "coupling_issues", "growth_issues"]
                },
                "gaps": {
                  "type": "object",
                  "properties": {
                    "quality_attribute_gaps": {
                      "type": "integer"
                    },
                    "interface_gaps": {
                      "type": "integer"
                    },
                    "isolation_gaps": {
                      "type": "integer"
                    },
                    "cross_cutting_gaps": {
                      "type": "integer"
                    },
                    "extension_point_gaps": {
                      "type": "integer"
                    }
                  },
                  "required": ["quality_attribute_gaps", "interface_gaps", "isolation_gaps", "cross_cutting_gaps", "extension_point_gaps"]
                }
              },
              "required": ["issues", "gaps"]
            },
            "added_items": {
              "type": "object",
              "properties": {
                "issues": {
                  "type": "object",
                  "properties": {
                    "foundation_issues": {
                      "type": "integer"
                    },
                    "boundary_issues": {
                      "type": "integer"
                    },
                    "balance_issues": {
                      "type": "integer"
                    },
                    "coupling_issues": {
                      "type": "integer"
                    },
                    "growth_issues": {
                      "type": "integer"
                    }
                  },
                  "required": ["foundation_issues", "boundary_issues", "balance_issues", "coupling_issues", "growth_issues"]
                },
                "gaps": {
                  "type": "object",
                  "properties": {
                    "quality_attribute_gaps": {
                      "type": "integer"
                    },
                    "interface_gaps": {
                      "type": "integer"
                    },
                    "isolation_gaps": {
                      "type": "integer"
                    },
                    "cross_cutting_gaps": {
                      "type": "integer"
                    },
                    "extension_point_gaps": {
                      "type": "integer"
                    }
                  },
                  "required": ["quality_attribute_gaps", "interface_gaps", "isolation_gaps", "cross_cutting_gaps", "extension_point_gaps"]
                }
              },
              "required": ["issues", "gaps"]
            },
            "synthesis_improvements": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "required": ["perspective_improvements", "specific_corrections", "added_items", "synthesis_improvements"]
        },
        "verification_steps": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      },
      "required": ["processed_feedback", "verification_steps"]
    },
    "dual_perspective_analysis": {
      "type": "object",
      "properties": {
        "issue_analysis": {
          "type": "object",
          "properties": {
            "foundation_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
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
                "required": ["component", "issue", "impact", "evidence", "recommendation", "revision_note"]
              }
            },
            "boundary_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
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
                "required": ["component", "issue", "impact", "evidence", "recommendation", "revision_note"]
              }
            },
            "balance_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
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
                "required": ["component", "issue", "impact", "evidence", "recommendation", "revision_note"]
              }
            },
            "coupling_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
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
                "required": ["component", "issue", "impact", "evidence", "recommendation", "revision_note"]
              }
            },
            "growth_issues": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
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
                "required": ["component", "issue", "impact", "evidence", "recommendation", "revision_note"]
              }
            }
          },
          "required": ["foundation_issues", "boundary_issues", "balance_issues", "coupling_issues", "growth_issues"]
        },
        "gap_analysis": {
          "type": "object",
          "properties": {
            "quality_attribute_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
                    "type": "string"
                  },
                  "gap": {
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
                "required": ["component", "gap", "impact", "evidence", "recommendation", "revision_note"]
              }
            },
            "interface_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
                    "type": "string"
                  },
                  "gap": {
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
                "required": ["component", "gap", "impact", "evidence", "recommendation", "revision_note"]
              }
            },
            "isolation_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
                    "type": "string"
                  },
                  "gap": {
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
                "required": ["component", "gap", "impact", "evidence", "recommendation", "revision_note"]
              }
            },
            "cross_cutting_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
                    "type": "string"
                  },
                  "gap": {
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
                "required": ["component", "gap", "impact", "evidence", "recommendation", "revision_note"]
              }
            },
            "extension_point_gaps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "component": {
                    "type": "string"
                  },
                  "gap": {
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
                "required": ["component", "gap", "impact", "evidence", "recommendation", "revision_note"]
              }
            }
          },
          "required": ["quality_attribute_gaps", "interface_gaps", "isolation_gaps", "cross_cutting_gaps", "extension_point_gaps"]
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