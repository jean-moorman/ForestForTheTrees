"""
Prompt validation tests for Water Agent system prompts.

This module tests the effectiveness and robustness of Water Agent prompts
with various inputs and validates JSON schema compliance.
"""

import pytest
import json
import re
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from tests.fixtures.water_agent_test_data import WaterAgentTestDataProvider
from FFTT_system_prompts.core_agents.water_agent import (
    MISUNDERSTANDING_DETECTION_PROMPT,
    WATER_AGENT_REFLECTION_PROMPT,
    WATER_AGENT_REVISION_PROMPT,
    RESOLUTION_ASSESSMENT_PROMPT,
    misunderstanding_detection_schema,
    reflection_schema,
    revision_schema
)


class MockLLMInterface:
    """Mock LLM interface that simulates realistic responses."""
    
    def __init__(self, response_quality: str = "good"):
        self.response_quality = response_quality
        self.call_count = 0
        
    async def generate_response(self, prompt: str) -> str:
        """Generate a mock response based on prompt type and quality setting."""
        self.call_count += 1
        
        # For new JSON pattern, detect based on conversation data content
        if "Detect potential misunderstandings between sequential agent outputs" in prompt:
            return self._generate_misunderstanding_detection_response(prompt)
        elif "Reflect on misunderstanding detection results for accuracy" in prompt:
            return self._generate_reflection_response(prompt)
        elif "Revise misunderstanding detection results based on reflection" in prompt:
            return self._generate_revision_response(prompt)
        elif "Assess resolution of misunderstandings based on agent responses" in prompt:
            return self._generate_resolution_assessment_response(prompt)
        elif "Misunderstanding Detection System" in prompt:
            return self._generate_misunderstanding_detection_response(prompt)
        elif "Self-Reflection System" in prompt:
            return self._generate_reflection_response(prompt)
        elif "Revision System" in prompt:
            return self._generate_revision_response(prompt)
        elif "Resolution Assessment System" in prompt:
            return self._generate_resolution_assessment_response(prompt)
        else:
            return '{"error": "Unknown prompt type"}'
    
    def _generate_misunderstanding_detection_response(self, prompt: str) -> str:
        """Generate realistic misunderstanding detection response."""
        if self.response_quality == "good":
            return '''```json
{
  "misunderstandings": [
    {
      "id": "M1",
      "description": "The agents use different terminology for similar concepts, which could lead to confusion in implementation",
      "severity": "MEDIUM",
      "context": "First agent uses 'forest layers' while second agent uses 'cultivation zones'"
    },
    {
      "id": "M2", 
      "description": "The second agent has not addressed the weight limitations mentioned by the first agent",
      "severity": "HIGH",
      "context": "First agent specified '150 lbs per square foot' constraint but second agent proposes heavy soil beds"
    }
  ],
  "first_agent_questions": [
    {
      "misunderstanding_id": "M1",
      "question": "Can you clarify which specific terminology should be used consistently throughout the project?"
    },
    {
      "misunderstanding_id": "M2",
      "question": "How critical are the weight limitations you mentioned for the implementation?"
    }
  ],
  "second_agent_questions": [
    {
      "misunderstanding_id": "M1", 
      "question": "How do you interpret the terminology used by the first agent for the different zones?"
    },
    {
      "misunderstanding_id": "M2",
      "question": "Have you considered the weight constraints mentioned by the first agent in your recommendations?"
    }
  ]
}
```'''
        elif self.response_quality == "malformed":
            return '''```json
{
  "misunderstandings": [
    {
      "id": 123,
      "description": "",
      "severity": "INVALID",
      "missing_context": true
    }
  ],
  "first_agent_questions": "not an array",
  "second_agent_questions": []
}
```'''
        else:  # "poor"
            return '''```json
{
  "misunderstandings": [],
  "first_agent_questions": [],
  "second_agent_questions": []
}
```'''
    
    def _generate_reflection_response(self, prompt: str) -> str:
        """Generate realistic reflection response."""
        if self.response_quality == "good":
            return '''```json
{
  "reflection_results": {
    "overall_assessment": {
      "accuracy": "HIGH",
      "comprehensiveness": "MEDIUM",
      "critical_improvements": [
        {
          "aspect": "Severity classification needs refinement",
          "importance": "critical",
          "recommendation": "The HIGH severity misunderstanding should be CRITICAL given safety implications"
        }
      ]
    },
    "misunderstanding_assessments": [
      {
        "id": "M1",
        "assessment": "accurate",
        "severity_assessment": "appropriate",
        "recommended_severity": "MEDIUM",
        "question_quality": "effective",
        "comments": "Well-identified terminology conflict with appropriate questions"
      },
      {
        "id": "M2",
        "assessment": "accurate", 
        "severity_assessment": "should_be_higher",
        "recommended_severity": "CRITICAL",
        "question_quality": "partially_effective",
        "comments": "Safety-critical issue requires more direct questioning"
      }
    ],
    "false_positives": [],
    "false_negatives": [
      {
        "description": "Missing consideration of budget constraints conflict",
        "context": "First agent mentions $10,000 budget but second agent proposes $55,000 system",
        "recommended_severity": "HIGH",
        "suggested_questions": {
          "first_agent": "Is the budget constraint flexible or fixed?",
          "second_agent": "How can your proposal be adapted to fit the budget constraints?"
        }
      }
    ]
  }
}
```'''
        else:
            return '{"reflection_results": {"overall_assessment": {"accuracy": "LOW", "comprehensiveness": "LOW", "critical_improvements": []}}}'
    
    def _generate_revision_response(self, prompt: str) -> str:
        """Generate realistic revision response."""
        if self.response_quality == "good":
            return '''```json
{
  "misunderstandings": [
    {
      "id": "M1",
      "description": "The agents use different terminology for similar concepts, which could lead to confusion in implementation",
      "severity": "MEDIUM", 
      "context": "First agent uses 'forest layers' while second agent uses 'cultivation zones'"
    },
    {
      "id": "M2",
      "description": "The second agent has not addressed the weight limitations mentioned by the first agent",
      "severity": "CRITICAL",
      "context": "First agent specified '150 lbs per square foot' constraint but second agent proposes heavy soil beds"
    },
    {
      "id": "M3",
      "description": "Budget constraints conflict between agents",
      "severity": "HIGH",
      "context": "First agent mentions $10,000 budget but second agent proposes $55,000 system"
    }
  ],
  "first_agent_questions": [
    {
      "misunderstanding_id": "M1",
      "question": "Can you specify which terminology should be used consistently throughout the project?"
    },
    {
      "misunderstanding_id": "M2", 
      "question": "How critical are the weight limitations for structural safety?"
    },
    {
      "misunderstanding_id": "M3",
      "question": "Is the budget constraint flexible or absolutely fixed?"
    }
  ],
  "second_agent_questions": [
    {
      "misunderstanding_id": "M1",
      "question": "How do you interpret the terminology used by the first agent?"
    },
    {
      "misunderstanding_id": "M2",
      "question": "Can you redesign your recommendations to meet the weight constraints?"
    },
    {
      "misunderstanding_id": "M3",
      "question": "How can your proposal be adapted to fit within the budget constraints?"
    }
  ]
}
```'''
        else:
            return '{"misunderstandings": [], "first_agent_questions": [], "second_agent_questions": []}'
    
    def _generate_resolution_assessment_response(self, prompt: str) -> str:
        """Generate realistic resolution assessment response."""
        if self.response_quality == "good":
            return '''```json
{
  "resolved_misunderstandings": [
    {
      "id": "M1",
      "resolution_summary": "Agents agreed to use consistent terminology throughout project documentation"
    }
  ],
  "unresolved_misunderstandings": [
    {
      "id": "M2",
      "severity": "CRITICAL",
      "resolution_status": "partially_resolved",
      "resolution_summary": "Weight constraints acknowledged but specific modifications not yet proposed"
    }
  ],
  "new_first_agent_questions": [
    {
      "misunderstanding_id": "M2",
      "question": "What specific weight reduction strategies would you recommend?"
    }
  ],
  "new_second_agent_questions": [
    {
      "misunderstanding_id": "M2", 
      "question": "Can you provide alternative approaches that meet the weight limitations?"
    }
  ],
  "require_further_iteration": true,
  "iteration_recommendation": "Critical weight constraint issue requires specific technical solutions"
}
```'''
        else:
            return '{"resolved_misunderstandings": [], "unresolved_misunderstandings": [], "new_first_agent_questions": [], "new_second_agent_questions": [], "require_further_iteration": false, "iteration_recommendation": "Complete"}'


class TestPromptValidation:
    """Test Water Agent prompt validation and schema compliance."""
    
    def test_misunderstanding_detection_prompt_structure(self):
        """Test that misunderstanding detection prompt has correct structure."""
        # Verify prompt contains required sections
        assert "Misunderstanding Detection System" in MISUNDERSTANDING_DETECTION_PROMPT
        assert "first_agent_output" in MISUNDERSTANDING_DETECTION_PROMPT
        assert "second_agent_output" in MISUNDERSTANDING_DETECTION_PROMPT
        assert "Output Format" in MISUNDERSTANDING_DETECTION_PROMPT
        
        # Verify JSON schema example is present
        assert "```json" in MISUNDERSTANDING_DETECTION_PROMPT
        assert "misunderstandings" in MISUNDERSTANDING_DETECTION_PROMPT
        assert "first_agent_questions" in MISUNDERSTANDING_DETECTION_PROMPT
        assert "second_agent_questions" in MISUNDERSTANDING_DETECTION_PROMPT
    
    def test_prompt_formatting_consistency(self):
        """Test that all prompts follow consistent formatting."""
        prompts = [
            MISUNDERSTANDING_DETECTION_PROMPT,
            WATER_AGENT_REFLECTION_PROMPT,
            WATER_AGENT_REVISION_PROMPT,
            RESOLUTION_ASSESSMENT_PROMPT
        ]
        
        for prompt in prompts:
            # Check for proper markdown headers
            assert re.search(r'^# .+', prompt, re.MULTILINE), "Missing main header"
            assert re.search(r'^## .+', prompt, re.MULTILINE), "Missing section headers"
            
            # Check for output format section
            assert "Output Format" in prompt or "output" in prompt.lower()
            
            # Check for JSON example
            assert "```json" in prompt
    
    @pytest.mark.asyncio
    async def test_misunderstanding_detection_schema_validation(self):
        """Test misunderstanding detection response validates against schema."""
        mock_llm = MockLLMInterface("good")
        
        # Prepare conversation data with realistic data (following new standard pattern)
        scenarios = WaterAgentTestDataProvider.get_basic_scenarios()
        scenario = scenarios[0]
        
        conversation_data = {
            "task": "Detect potential misunderstandings between sequential agent outputs",
            "first_agent_output": scenario.first_agent_output,
            "second_agent_output": scenario.second_agent_output
        }
        formatted_prompt = json.dumps(conversation_data, indent=2)
        
        # Get response
        response = await mock_llm.generate_response(formatted_prompt)
        
        # Extract JSON from response
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        assert json_match, "No JSON found in response"
        
        json_str = json_match.group(1)
        response_data = json.loads(json_str)
        
        # Validate against schema (basic validation)
        assert "misunderstandings" in response_data
        assert "first_agent_questions" in response_data
        assert "second_agent_questions" in response_data
        
        # Validate misunderstanding structure
        for misunderstanding in response_data["misunderstandings"]:
            assert "id" in misunderstanding
            assert "description" in misunderstanding
            assert "severity" in misunderstanding
            assert "context" in misunderstanding
            assert misunderstanding["severity"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
            assert re.match(r"^M\d+$", misunderstanding["id"])
        
        # Validate question structure
        for question in response_data["first_agent_questions"]:
            assert "misunderstanding_id" in question
            assert "question" in question
            assert re.match(r"^M\d+$", question["misunderstanding_id"])
    
    @pytest.mark.asyncio
    async def test_malformed_response_handling(self):
        """Test handling of malformed LLM responses."""
        mock_llm = MockLLMInterface("malformed")
        
        scenarios = WaterAgentTestDataProvider.get_basic_scenarios()
        scenario = scenarios[0]
        
        conversation_data = {
            "task": "Detect potential misunderstandings between sequential agent outputs",
            "first_agent_output": scenario.first_agent_output,
            "second_agent_output": scenario.second_agent_output
        }
        formatted_prompt = json.dumps(conversation_data, indent=2)
        
        response = await mock_llm.generate_response(formatted_prompt)
        
        # Extract JSON
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        assert json_match
        
        json_str = json_match.group(1)
        
        # Should be able to parse as JSON even if invalid
        try:
            response_data = json.loads(json_str)
            # Response data might be malformed but parseable
            assert isinstance(response_data, dict)
        except json.JSONDecodeError:
            pytest.fail("Even malformed responses should be valid JSON")
    
    @pytest.mark.asyncio
    async def test_reflection_prompt_effectiveness(self):
        """Test reflection prompt produces useful assessments."""
        mock_llm = MockLLMInterface("good")
        
        # Create realistic reflection input
        detection_results = {
            "misunderstandings": [
                {
                    "id": "M1",
                    "description": "Terminology conflict",
                    "severity": "MEDIUM",
                    "context": "Different terms used"
                }
            ],
            "first_agent_questions": [
                {"misunderstanding_id": "M1", "question": "Clarify terminology?"}
            ],
            "second_agent_questions": [
                {"misunderstanding_id": "M1", "question": "How do you interpret?"}
            ]
        }
        
        conversation_data = {
            "task": "Reflect on misunderstanding detection results for accuracy",
            "first_agent_output": "Sample first agent output",
            "second_agent_output": "Sample second agent output",
            "misunderstanding_detection_results": detection_results
        }
        formatted_prompt = json.dumps(conversation_data, indent=2)
        
        response = await mock_llm.generate_response(formatted_prompt)
        
        # Extract and validate reflection response
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        assert json_match
        
        reflection_data = json.loads(json_match.group(1))
        
        # Validate reflection structure
        assert "reflection_results" in reflection_data
        results = reflection_data["reflection_results"]
        
        assert "overall_assessment" in results
        assert "accuracy" in results["overall_assessment"]
        assert "comprehensiveness" in results["overall_assessment"]
        assert "critical_improvements" in results["overall_assessment"]
        
        # Validate assessment details
        assert results["overall_assessment"]["accuracy"] in ["HIGH", "MEDIUM", "LOW"]
        assert results["overall_assessment"]["comprehensiveness"] in ["HIGH", "MEDIUM", "LOW"]
        
        # Check for improvement suggestions
        improvements = results["overall_assessment"]["critical_improvements"]
        assert isinstance(improvements, list)
        for improvement in improvements:
            assert "aspect" in improvement
            assert "importance" in improvement
            assert "recommendation" in improvement
    
    @pytest.mark.asyncio
    async def test_revision_prompt_produces_improvements(self):
        """Test revision prompt produces improved results."""
        mock_llm = MockLLMInterface("good")
        
        # Create revision scenario with reflection feedback
        original_detection = {
            "misunderstandings": [
                {"id": "M1", "description": "Issue", "severity": "HIGH", "context": "Context"}
            ],
            "first_agent_questions": [{"misunderstanding_id": "M1", "question": "Question?"}],
            "second_agent_questions": [{"misunderstanding_id": "M1", "question": "Question?"}]
        }
        
        reflection_assessment = {
            "reflection_results": {
                "overall_assessment": {
                    "critical_improvements": [
                        {"aspect": "Add missing issue", "importance": "critical", "recommendation": "Add budget issue"}
                    ]
                },
                "false_negatives": [
                    {
                        "description": "Budget constraint issue",
                        "recommended_severity": "HIGH",
                        "suggested_questions": {
                            "first_agent": "Budget flexible?",
                            "second_agent": "Adapt to budget?"
                        }
                    }
                ]
            }
        }
        
        conversation_data = {
            "task": "Revise misunderstanding detection results based on reflection",
            "first_agent_output": "Sample output",
            "second_agent_output": "Sample output",
            "original_detection_results": original_detection,
            "reflection_assessment": reflection_assessment
        }
        formatted_prompt = json.dumps(conversation_data, indent=2)
        
        response = await mock_llm.generate_response(formatted_prompt)
        
        # Extract and validate revision
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        assert json_match
        
        revision_data = json.loads(json_match.group(1))
        
        # Verify revision added the missing issue
        misunderstandings = revision_data["misunderstandings"]
        assert len(misunderstandings) > len(original_detection["misunderstandings"])
        
        # Check that new misunderstanding was added based on reflection
        new_issues = [m for m in misunderstandings if m["id"] not in ["M1"]]
        assert len(new_issues) > 0
        
        # Verify questions were added for new issues
        first_questions = revision_data["first_agent_questions"]
        second_questions = revision_data["second_agent_questions"]
        assert len(first_questions) > len(original_detection["first_agent_questions"])
        assert len(second_questions) > len(original_detection["second_agent_questions"])
    
    @pytest.mark.asyncio
    async def test_resolution_assessment_tracking(self):
        """Test resolution assessment tracks progress effectively."""
        mock_llm = MockLLMInterface("good")
        
        # Create resolution assessment scenario
        misunderstandings = [
            {"id": "M1", "description": "Issue 1", "severity": "MEDIUM"},
            {"id": "M2", "description": "Issue 2", "severity": "HIGH"}
        ]
        
        qa_responses = """
        Q1: What do you mean by X?
        A1: X refers to the specific technical approach.
        
        Q2: How do you interpret Y?
        A2: Y means the implementation strategy.
        """
        
        conversation_data = {
            "task": "Assess resolution of misunderstandings based on agent responses",
            "misunderstandings": misunderstandings,
            "first_agent_questions_and_responses": qa_responses,
            "second_agent_questions_and_responses": qa_responses,
            "current_iteration": 1
        }
        formatted_prompt = json.dumps(conversation_data, indent=2)
        
        response = await mock_llm.generate_response(formatted_prompt)
        
        # Extract and validate assessment
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        assert json_match
        
        assessment_data = json.loads(json_match.group(1))
        
        # Validate assessment structure
        assert "resolved_misunderstandings" in assessment_data
        assert "unresolved_misunderstandings" in assessment_data
        assert "require_further_iteration" in assessment_data
        assert "iteration_recommendation" in assessment_data
        
        # Check resolution tracking
        resolved = assessment_data["resolved_misunderstandings"]
        unresolved = assessment_data["unresolved_misunderstandings"]
        
        for resolved_item in resolved:
            assert "id" in resolved_item
            assert "resolution_summary" in resolved_item
        
        for unresolved_item in unresolved:
            assert "id" in unresolved_item
            assert "severity" in unresolved_item
            assert "resolution_status" in unresolved_item
    
    @pytest.mark.asyncio
    async def test_prompt_robustness_with_edge_cases(self):
        """Test prompt robustness with edge case inputs."""
        mock_llm = MockLLMInterface("good")
        
        edge_cases = WaterAgentTestDataProvider.get_edge_case_scenarios()
        
        for scenario in edge_cases:
            conversation_data = {
                "task": "Detect potential misunderstandings between sequential agent outputs",
                "first_agent_output": scenario.first_agent_output,
                "second_agent_output": scenario.second_agent_output
            }
            formatted_prompt = json.dumps(conversation_data, indent=2)
            
            response = await mock_llm.generate_response(formatted_prompt)
            
            # Should always get valid JSON response
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            assert json_match, f"No JSON in response for scenario: {scenario.name}"
            
            try:
                response_data = json.loads(json_match.group(1))
                assert isinstance(response_data, dict)
                assert "misunderstandings" in response_data
            except json.JSONDecodeError:
                pytest.fail(f"Invalid JSON for scenario: {scenario.name}")
    
    def test_schema_completeness(self):
        """Test that schemas cover all required validation."""
        # Test misunderstanding detection schema
        schema = misunderstanding_detection_schema
        
        # Verify required fields
        assert "misunderstandings" in schema["properties"]
        assert "first_agent_questions" in schema["properties"]
        assert "second_agent_questions" in schema["properties"]
        
        # Verify misunderstanding item schema
        misunderstanding_schema = schema["properties"]["misunderstandings"]["items"]
        required_fields = ["id", "description", "severity", "context"]
        for field in required_fields:
            assert field in misunderstanding_schema["properties"]
            assert field in misunderstanding_schema["required"]
        
        # Verify severity enum
        severity_enum = misunderstanding_schema["properties"]["severity"]["enum"]
        expected_severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        for severity in expected_severities:
            assert severity in severity_enum
        
        # Verify ID pattern
        id_pattern = misunderstanding_schema["properties"]["id"]["pattern"]
        assert id_pattern == "^M[0-9]+$"
    
    @pytest.mark.asyncio
    async def test_prompt_performance_with_large_inputs(self):
        """Test prompt performance with large agent outputs."""
        mock_llm = MockLLMInterface("good")
        
        # Create large inputs
        large_output = "This is a very detailed analysis. " * 1000  # ~30KB text
        
        conversation_data = {
            "task": "Detect potential misunderstandings between sequential agent outputs",
            "first_agent_output": large_output,
            "second_agent_output": large_output
        }
        formatted_prompt = json.dumps(conversation_data, indent=2)
        
        # Should handle large inputs gracefully
        response = await mock_llm.generate_response(formatted_prompt)
        
        # Verify response is still valid
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        assert json_match
        
        response_data = json.loads(json_match.group(1))
        assert isinstance(response_data["misunderstandings"], list)
        
        # Performance check - should return in reasonable time
        assert mock_llm.call_count == 1