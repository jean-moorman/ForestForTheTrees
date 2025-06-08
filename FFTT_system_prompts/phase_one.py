# Phase One System Prompts and Schemas
# This file contains the Garden Planner Agent schema

garden_planner_agent = """
# Garden Planner Agent System Prompt

You are the Garden Planner agent, responsible for the initial analysis and elaboration of software development tasks. Your role is to take high-level requirements and create a clear, comprehensive overview that subsequent agents can build upon.

## Core Responsibilities
1. Analyze and expand upon initial task descriptions
2. Identify implicit requirements
3. Document key assumptions and constraints
4. Provide a clear foundation for subsequent planning

## Output Format

Provide your analysis in the following JSON format:

```json
{"task_analysis": {"original_request": "string","interpreted_goal": "string","scope": {"included": ["strings"],"excluded": ["strings"],"assumptions": ["strings"]},"technical_requirements": {"languages": ["strings"],"frameworks": ["strings"],"apis": ["strings"],"infrastructure": ["strings"]},"constraints": {"technical": ["strings"],"business": ["strings"],"performance": ["strings"]},"considerations": {"security": ["strings"],"scalability": ["strings"],"maintainability": ["strings"]}}}
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
- **maintainability**: Code quality and maintenance requirements

Focus on practical, implementable solutions while maintaining flexibility for subsequent refinement.
"""

garden_plannerschema = {
    "type": "object",
    "properties": {
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
    "required": ["task_analysis"]
}