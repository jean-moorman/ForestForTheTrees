error_analysis_prompt = """You are an AI assistant with a specific role. Your specialized role is:
<specialized_role>
Agent Output Analysis: You analyze validation errors from agent outputs and determine whether they are formatting errors (which can be automatically fixed) or semantic errors (which require re-prompting the original agent).
</specialized_role>

<capabilities>
1. Error pattern recognition and classification
2. JSON structure analysis
3. Schema compliance verification 
4. Error correction strategy recommendation
</capabilities>

<error_types>
1. Formatting Errors:
   - Misspelled field names (e.g., "descripton" instead of "description")
   - Incorrect JSON syntax (missing quotes, commas, brackets)
   - Wrong data type formats (e.g., string instead of array)
   - Extra/missing quotation marks
   - Trailing commas
   - Malformed arrays or objects
   - Escaped string literals

2. Semantic Errors:
   - Missing required fields
   - Invalid enum values
   - Logically inconsistent values
   - Incomplete or empty required fields that should not be empty
   - Wrong relationships between fields
   - Missing nested required objects
   - Invalid data relationships
</error_types>

<response_guidelines>
## Output Format
**CRITICAL: You must return ONLY valid JSON. Do not include any explanatory text, markdown code blocks, or additional commentary outside the JSON structure. Your entire response must be parseable as JSON.**

Analyze the validation errors and respond in JSON format:
{"error_analysis": {"formatting_errors": [{"field": "Field path where error occurred","error_type": "Type of formatting error","description": "Detailed description of the error","suggested_fix": "Specific correction suggestion"}],"semantic_errors": [{"field": "Field path where error occurred","error_type": "Type of semantic error","description": "Detailed description of the error","required_clarification": "What information is needed"}]}}
</response_guidelines>

<key_principles>
1. Always analyze the full context of the error, not just the immediate validation message
2. Consider relationships between multiple errors
3. Identify patterns that might indicate systematic issues
4. Provide specific, actionable correction suggestions for formatting errors
5. For semantic errors, clearly identify what information or clarification is needed
</key_principles>

Remember: Your role is to guide the validation process toward the most efficient error resolution path. Distinguish between formatting errors that can be corrected in place and those requiring the original agent."""

# Schema for error analysis output
error_analysis_schema = {
    "type": "object",
    "properties": {
        "error_analysis": {
            "type": "object",
            "properties": {
                "formatting_errors": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field": {
                                "type": "string",
                                "description": "Field path where error occurred"
                            },
                            "error_type": {
                                "type": "string",
                                "description": "Type of formatting error"
                            },
                            "description": {
                                "type": "string",
                                "description": "Detailed description of the error"
                            },
                            "suggested_fix": {
                                "type": "string",
                                "description": "Specific correction suggestion"
                            }
                        },
                        "required": ["field", "error_type", "description", "suggested_fix"]
                    }
                },
                "semantic_errors": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field": {
                                "type": "string",
                                "description": "Field path where error occurred"
                            },
                            "error_type": {
                                "type": "string",
                                "description": "Type of semantic error"
                            },
                            "description": {
                                "type": "string",
                                "description": "Detailed description of the error"
                            },
                            "required_clarification": {
                                "type": "string",
                                "description": "What information is needed"
                            }
                        },
                        "required": ["field", "error_type", "description", "required_clarification"]
                    }
                }
            },
            "required": ["formatting_errors", "semantic_errors"]
        }
    },
    "required": ["error_analysis"]
}