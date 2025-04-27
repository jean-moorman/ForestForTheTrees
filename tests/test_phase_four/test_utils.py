"""Tests for phase_four utils module."""

import unittest
from phase_four.models import CompilerType
from phase_four.utils import parse_compiler_output, create_improvement_prompt


class TestParseCompilerOutput(unittest.TestCase):
    """Test cases for parse_compiler_output function."""
    
    def test_parse_format_output_no_issues(self):
        """Test parsing black formatter output with no issues."""
        stdout = "All files are correctly formatted."
        stderr = ""
        
        issues = parse_compiler_output(CompilerType.FORMAT, stdout, stderr)
        
        self.assertEqual(issues, [])
        
    def test_parse_format_output_with_issues(self):
        """Test parsing black formatter output with formatting issues."""
        stdout = "would be reformatted test.py"
        stderr = ""
        
        issues = parse_compiler_output(CompilerType.FORMAT, stdout, stderr)
        
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["type"], "formatting")
        self.assertEqual(issues[0]["message"], "Code requires reformatting")
        self.assertEqual(issues[0]["severity"], "low")
        
    def test_parse_style_output(self):
        """Test parsing flake8 style output."""
        stdout = "test.py:10:5: E303 too many blank lines (3)"
        stderr = ""
        
        issues = parse_compiler_output(CompilerType.STYLE, stdout, stderr)
        
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["type"], "style")
        self.assertEqual(issues[0]["line"], 10)
        self.assertEqual(issues[0]["column"], 5)
        self.assertEqual(issues[0]["message"], "E303 too many blank lines (3)")
        self.assertEqual(issues[0]["severity"], "medium")
        
    def test_parse_lint_output(self):
        """Test parsing pylint output."""
        stdout = "test.py:15: error: Missing docstring [missing-docstring]"
        stderr = ""
        
        issues = parse_compiler_output(CompilerType.LINT, stdout, stderr)
        
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["type"], "lint")
        self.assertEqual(issues[0]["message"], "error: Missing docstring [missing-docstring]")
        self.assertEqual(issues[0]["severity"], "high")
        
    def test_parse_type_output(self):
        """Test parsing mypy type checking output."""
        stdout = "test.py:20: error: Incompatible types in assignment"
        stderr = ""
        
        issues = parse_compiler_output(CompilerType.TYPE, stdout, stderr)
        
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["type"], "type")
        self.assertEqual(issues[0]["line"], 20)
        self.assertEqual(issues[0]["message"], "error: Incompatible types in assignment")
        self.assertEqual(issues[0]["severity"], "high")
        
    def test_parse_security_output(self):
        """Test parsing bandit security output."""
        stdout = "Issue: Function call with shell=True identified.\nSeverity: High"
        stderr = ""
        
        issues = parse_compiler_output(CompilerType.SECURITY, stdout, stderr)
        
        self.assertEqual(len(issues), 2)
        self.assertEqual(issues[0]["type"], "security")
        self.assertEqual(issues[0]["message"], "Issue: Function call with shell=True identified.")
        self.assertEqual(issues[0]["severity"], "high")
        self.assertEqual(issues[1]["type"], "security")
        self.assertEqual(issues[1]["message"], "Severity: High")
        self.assertEqual(issues[1]["severity"], "high")


class TestCreateImprovementPrompt(unittest.TestCase):
    """Test cases for create_improvement_prompt function."""
    
    def test_create_improvement_prompt(self):
        """Test creating an improvement prompt with sample inputs."""
        original_code = "def add(a, b):\n    return a + b"
        improvements = ["Add type hints", "Add docstring"]
        rationale = "Improve code quality"
        
        prompt = create_improvement_prompt(original_code, improvements, rationale)
        
        # Check that the prompt contains all expected elements
        self.assertIn("def add(a, b):", prompt)
        self.assertIn("- Add type hints", prompt)
        self.assertIn("- Add docstring", prompt)
        self.assertIn("Improve code quality", prompt)
        
        # Check that the prompt structure is as expected
        self.assertIn("ORIGINAL CODE:", prompt)
        self.assertIn("IMPROVEMENT SUGGESTIONS:", prompt)
        self.assertIn("IMPROVEMENT RATIONALE:", prompt)
        self.assertIn("```python", prompt)
        self.assertIn("```", prompt)
        
        # Check that the response format instructions are included
        self.assertIn("Return your response as JSON", prompt)
        self.assertIn("improved_code", prompt)
        self.assertIn("explanation", prompt)
        self.assertIn("improvements_applied", prompt)


if __name__ == "__main__":
    unittest.main()