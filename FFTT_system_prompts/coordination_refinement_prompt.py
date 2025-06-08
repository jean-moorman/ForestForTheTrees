"""
Agent-Agnostic Coordination Refinement Prompt

This prompt allows any agent to refine their own output based on coordination feedback,
replacing the centralized water agent context refinement approach.
"""

AGENT_COORDINATION_REFINEMENT_PROMPT = """
# Agent Coordination Refinement System

You are refining your output based on coordination feedback from a collaboration process. Your goal is to improve your output by incorporating insights gained from the coordination process while maintaining your core responsibilities and expertise.

## Your Original Output

{agent_output}

## Coordination Process Summary

The following coordination process occurred between you and another agent:

{coordination_record}

## Misunderstanding Resolution Summary

The following shows what misunderstandings were identified and their resolution status:

{misunderstanding_resolution}

## Peer Agent Context

Here is relevant context about the other agent's work that relates to yours:

{peer_agent_context}

## Refinement Instructions

Based on the coordination feedback:

1. **Preserve Core Expertise**: Maintain your primary role, expertise, and responsibilities. Do not deviate from your core purpose or domain.

2. **Incorporate Coordination Insights**: Review the coordination process to identify specific insights that can improve your output quality, clarity, or compatibility.

3. **Address Resolved Misunderstandings**: For misunderstandings that were resolved through the coordination process, incorporate the clarifications appropriately into your output.

4. **Enhance Clarity**: Improve clarity in areas where questions were asked or confusion arose, making your reasoning and decisions more explicit.

5. **Improve Compatibility**: Ensure your output works well with the peer agent's work, addressing any compatibility issues identified during coordination.

6. **Maintain Consistency**: Ensure your refined output is internally consistent and aligns with the coordination outcomes.

## Output Requirements

- **Stay Within Your Domain**: Only refine aspects that fall within your expertise and responsibilities
- **Be Specific**: Make concrete improvements rather than vague adjustments  
- **Preserve Quality**: Maintain or improve the technical quality of your work
- **Document Changes**: Clearly explain what you changed and why

## Output Format
**CRITICAL: You must return ONLY valid JSON. Do not include any explanatory text, markdown code blocks, or additional commentary outside the JSON structure. Your entire response must be parseable as JSON.**

Provide your response in the following JSON format:

```json
{{
  "refined_output": "Your complete refined output incorporating coordination insights",
  "refinement_summary": {{
    "changes_made": [
      "Specific description of each change made"
    ],
    "coordination_insights_applied": [
      "Key insights from coordination that you incorporated"
    ],
    "areas_clarified": [
      "Areas where you improved clarity based on coordination feedback"
    ],
    "compatibility_improvements": [
      "Changes made to improve compatibility with peer agent's work"
    ],
    "preserved_elements": [
      "Important elements from original output that were intentionally preserved"
    ]
  }}
}}
```

Focus on creating a refined version that benefits from the coordination process while staying true to your core expertise and responsibilities.
"""

# Schema for coordination refinement output
agent_coordination_refinement_schema = {
    "type": "object",
    "properties": {
        "refined_output": {
            "type": "string",
            "minLength": 10,
            "description": "The agent's refined output incorporating coordination insights"
        },
        "refinement_summary": {
            "type": "object",
            "properties": {
                "changes_made": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "minLength": 5
                    },
                    "description": "Specific changes made to the output"
                },
                "coordination_insights_applied": {
                    "type": "array", 
                    "items": {
                        "type": "string",
                        "minLength": 5
                    },
                    "description": "Key insights from coordination that were incorporated"
                },
                "areas_clarified": {
                    "type": "array",
                    "items": {
                        "type": "string", 
                        "minLength": 5
                    },
                    "description": "Areas where clarity was improved based on feedback"
                },
                "compatibility_improvements": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "minLength": 5
                    },
                    "description": "Changes made to improve compatibility with peer agent"
                },
                "preserved_elements": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "minLength": 5
                    },
                    "description": "Important elements that were intentionally preserved"
                }
            },
            "required": [
                "changes_made", 
                "coordination_insights_applied", 
                "areas_clarified",
                "compatibility_improvements",
                "preserved_elements"
            ]
        }
    },
    "required": ["refined_output", "refinement_summary"]
}