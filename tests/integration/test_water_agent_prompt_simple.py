"""
Simplified prompt validation tests for Water Agent system prompts.
"""

import pytest
import json
import re
from tests.fixtures.water_agent_test_data import WaterAgentTestDataProvider
from FFTT_system_prompts.core_agents.water_agent import (
    MISUNDERSTANDING_DETECTION_PROMPT,
    misunderstanding_detection_schema
)


class TestSimplePromptValidation:
    """Test Water Agent prompt structure and basic functionality."""
    
    def test_prompt_structure(self):
        """Test that prompts have correct basic structure."""
        # Verify prompt contains required placeholders
        assert "{first_agent_output}" in MISUNDERSTANDING_DETECTION_PROMPT
        assert "{second_agent_output}" in MISUNDERSTANDING_DETECTION_PROMPT
        
        # Verify prompt contains guidance sections
        assert "Misunderstanding Detection System" in MISUNDERSTANDING_DETECTION_PROMPT
        assert "Output Format" in MISUNDERSTANDING_DETECTION_PROMPT
        assert "```json" in MISUNDERSTANDING_DETECTION_PROMPT
    
    def test_schema_completeness(self):
        """Test that schema covers required fields."""
        schema = misunderstanding_detection_schema
        
        # Verify top-level structure
        assert "properties" in schema
        assert "misunderstandings" in schema["properties"]
        assert "first_agent_questions" in schema["properties"]
        assert "second_agent_questions" in schema["properties"]
        
        # Verify misunderstanding schema
        misunderstanding_items = schema["properties"]["misunderstandings"]["items"]
        required_fields = ["id", "description", "severity", "context"]
        for field in required_fields:
            assert field in misunderstanding_items["properties"]
        
        # Verify severity enum
        severity_enum = misunderstanding_items["properties"]["severity"]["enum"]
        expected_severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        for severity in expected_severities:
            assert severity in severity_enum
    
    def test_mock_response_parsing(self):
        """Test parsing of mock LLM responses."""
        # Test valid response
        valid_response = '''```json
{
  "misunderstandings": [
    {
      "id": "M1",
      "description": "Test misunderstanding",
      "severity": "MEDIUM",
      "context": "Test context"
    }
  ],
  "first_agent_questions": [
    {
      "misunderstanding_id": "M1", 
      "question": "Test question"
    }
  ],
  "second_agent_questions": [
    {
      "misunderstanding_id": "M1",
      "question": "Test question"
    }
  ]
}
```'''
        
        # Extract JSON
        json_match = re.search(r'```json\s*(.*?)\s*```', valid_response, re.DOTALL)
        assert json_match
        
        json_str = json_match.group(1)
        response_data = json.loads(json_str)
        
        # Validate structure
        assert "misunderstandings" in response_data
        assert "first_agent_questions" in response_data
        assert "second_agent_questions" in response_data
        
        # Validate misunderstanding
        misunderstanding = response_data["misunderstandings"][0]
        assert misunderstanding["id"] == "M1"
        assert misunderstanding["severity"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        assert re.match(r"^M\d+$", misunderstanding["id"])
    
    def test_prompt_with_realistic_data(self):
        """Test prompt formatting with realistic test data."""
        scenarios = WaterAgentTestDataProvider.get_basic_scenarios()
        scenario = scenarios[0]
        
        # Manually replace placeholders to avoid format string issues
        test_prompt = MISUNDERSTANDING_DETECTION_PROMPT.replace(
            "{first_agent_output}", "TEST_FIRST_OUTPUT"
        ).replace(
            "{second_agent_output}", "TEST_SECOND_OUTPUT"
        )
        
        # Verify replacement worked
        assert "TEST_FIRST_OUTPUT" in test_prompt
        assert "TEST_SECOND_OUTPUT" in test_prompt
        assert "{first_agent_output}" not in test_prompt
        assert "{second_agent_output}" not in test_prompt
        
        # Verify prompt is still complete
        assert "Misunderstanding Detection System" in test_prompt
        assert "Output Format" in test_prompt
    
    def test_test_data_quality(self):
        """Test that test data scenarios are well-formed."""
        scenarios = WaterAgentTestDataProvider.get_all_scenarios()
        
        assert len(scenarios) > 0
        
        for scenario in scenarios:
            # Verify scenario structure
            assert hasattr(scenario, 'name')
            assert hasattr(scenario, 'first_agent_output')
            assert hasattr(scenario, 'second_agent_output')
            assert hasattr(scenario, 'expected_misunderstanding_types')
            assert hasattr(scenario, 'expected_severity')
            
            # Verify content quality (except for intentionally minimal scenarios)
            if "empty_output" not in scenario.name and "minimal" not in scenario.name:
                assert len(scenario.first_agent_output) > 100
                assert len(scenario.second_agent_output) > 100
            else:
                # Minimal output scenarios should still have some content
                assert len(scenario.first_agent_output) > 10
                assert len(scenario.second_agent_output) > 10
            assert len(scenario.expected_misunderstanding_types) > 0
            assert scenario.expected_severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    
    def test_expected_misunderstanding_generation(self):
        """Test generation of expected misunderstandings from scenarios."""
        scenarios = WaterAgentTestDataProvider.get_basic_scenarios()
        scenario = scenarios[0]
        
        expected = WaterAgentTestDataProvider.get_expected_misunderstanding_for_scenario(scenario)
        
        # Verify structure
        assert "misunderstandings" in expected
        assert "first_agent_questions" in expected
        assert "second_agent_questions" in expected
        
        # Verify content
        misunderstandings = expected["misunderstandings"]
        assert len(misunderstandings) > 0
        
        for misunderstanding in misunderstandings:
            assert "id" in misunderstanding
            assert "description" in misunderstanding
            assert "severity" in misunderstanding
            assert "context" in misunderstanding
            assert re.match(r"^M\d+$", misunderstanding["id"])
        
        # Verify questions reference misunderstandings
        first_questions = expected["first_agent_questions"]
        second_questions = expected["second_agent_questions"]
        
        for question in first_questions:
            assert "misunderstanding_id" in question
            assert "question" in question
            assert any(m["id"] == question["misunderstanding_id"] for m in misunderstandings)
        
        for question in second_questions:
            assert "misunderstanding_id" in question
            assert "question" in question
            assert any(m["id"] == question["misunderstanding_id"] for m in misunderstandings)
    
    def test_edge_case_scenarios(self):
        """Test edge case scenarios for robustness."""
        edge_cases = WaterAgentTestDataProvider.get_edge_case_scenarios()
        
        assert len(edge_cases) > 0
        
        for scenario in edge_cases:
            # Test that even edge cases produce valid expected results
            expected = WaterAgentTestDataProvider.get_expected_misunderstanding_for_scenario(scenario)
            
            assert isinstance(expected["misunderstandings"], list)
            assert isinstance(expected["first_agent_questions"], list)
            assert isinstance(expected["second_agent_questions"], list)
            
            # Edge cases should still have some expected misunderstandings
            if scenario.name != "empty_output_scenario":
                assert len(expected["misunderstandings"]) > 0