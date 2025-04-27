"""Utility functions used by multiple Phase Four components.

This module provides shared utility functions that are used across different
components of the Phase Four package. These functions handle common tasks like
parsing compiler output and generating prompts for code improvement.
"""

import logging
from typing import Dict, List, Any

from phase_four.models import CompilerType

logger = logging.getLogger(__name__)


def parse_compiler_output(compiler_type: CompilerType, 
                         stdout: str, stderr: str) -> List[Dict[str, Any]]:
    """Parse compiler output into structured issues.
    
    This function processes the raw stdout and stderr output from various
    static analysis tools and converts it into a standardized list of
    structured issue objects. Each issue contains information about the
    type, location, message, and severity of the problem.
    
    Args:
        compiler_type: The type of compiler whose output is being parsed
        stdout: The standard output from the compiler process
        stderr: The standard error output from the compiler process
        
    Returns:
        A list of dictionaries, where each dictionary represents a single
        issue with keys like "type", "message", "severity", and optional
        location information like "line" and "column".
    """
    issues = []
    
    if compiler_type == CompilerType.FORMAT:
        # Parse black output
        if "would be reformatted" in stdout:
            issues.append({
                "type": "formatting",
                "message": "Code requires reformatting",
                "severity": "low"
            })
            
    elif compiler_type == CompilerType.STYLE:
        # Parse flake8 output
        for line in stdout.split('\n'):
            if ':' in line:
                parts = line.strip().split(':')
                if len(parts) >= 4:
                    file_path, line_num, col, message = parts[0:4]
                    issues.append({
                        "type": "style",
                        "line": int(line_num),
                        "column": int(col),
                        "message": message.strip(),
                        "severity": "medium"
                    })
                    
    elif compiler_type == CompilerType.LINT:
        # Parse pylint output
        for line in stdout.split('\n'):
            if ':' in line and ('error' in line.lower() or 'warning' in line.lower()):
                parts = line.split(':')
                if len(parts) >= 2:
                    message = parts[-1].strip()
                    severity = "high" if "error" in line.lower() else "medium"
                    issues.append({
                        "type": "lint",
                        "message": message,
                        "severity": severity
                    })
                    
    elif compiler_type == CompilerType.TYPE:
        # Parse mypy output
        for line in stdout.split('\n'):
            if ':' in line and 'error' in line:
                parts = line.split(':')
                if len(parts) >= 3:
                    file_path, line_num = parts[0:2]
                    message = ':'.join(parts[2:]).strip()
                    issues.append({
                        "type": "type",
                        "line": int(line_num) if line_num.isdigit() else 0,
                        "message": message,
                        "severity": "high"
                    })
                    
    elif compiler_type == CompilerType.SECURITY:
        # Parse bandit output
        for line in stdout.split('\n'):
            if 'Issue:' in line or 'Severity:' in line:
                message = line.strip()
                severity = "high" if "High" in line else "medium" if "Medium" in line else "low"
                issues.append({
                    "type": "security",
                    "message": message,
                    "severity": severity
                })
    
    return issues


def create_improvement_prompt(original_code: str, improvements: List[str], rationale: str) -> str:
    """Create a prompt for code improvement.
    
    This function generates a system prompt for the LLM to improve code based on
    specified improvement suggestions. The prompt includes the original code,
    a list of desired improvements, and the rationale for making these improvements.
    
    Args:
        original_code: The source code to be improved
        improvements: A list of improvement suggestions
        rationale: The reason for making these improvements
        
    Returns:
        A formatted string containing the complete prompt for the LLM
    """
    improvements_formatted = "\n".join([f"- {improvement}" for improvement in improvements])
    
    return f"""You are an expert software developer focusing on code improvement and refactoring.
Improve the provided code based on the specified improvement suggestions.
Focus on making precise, targeted changes that address each suggestion while preserving the code's functionality.

ORIGINAL CODE:
```python
{original_code}
```

IMPROVEMENT SUGGESTIONS:
{improvements_formatted}

IMPROVEMENT RATIONALE:
{rationale}

When improving the code, follow these guidelines:
1. Preserve the overall functionality and behavior of the code
2. Apply improvements that address each suggestion precisely
3. Follow best practices for Python development (PEP 8, type annotations, etc.)
4. Add or improve comments where needed for clarity
5. Ensure the code is robust with proper error handling
6. Document your changes clearly in the explanation

Return your response as JSON with these fields:
- improved_code: The improved version of the code
- explanation: An explanation of the changes made and their benefits
- improvements_applied: An array of objects, each with:
  - description: Description of a specific improvement applied
  - changes: Details of what was changed and why
"""