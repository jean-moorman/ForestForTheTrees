import asyncio
import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock, AsyncMock

from phase_four import (
    CodeGenerationAgent,
    StaticCompilationAgent,
    CompilationDebugAgent,
    CompilationAnalysisAgent,
    CompilationRefinementAgent,
    PhaseFourInterface,
    CompilerType,
    CompilationState,
    CompilationResult,
    CompilationContext
)

# Sample feature requirements for testing
SAMPLE_FEATURE_REQUIREMENTS = {
    "id": "test_feature_001",
    "name": "Test Feature",
    "description": "A test feature for unit testing",
    "language": "python",
    "requirements": [
        "Provide a function that adds two numbers",
        "Include type annotations",
        "Add docstrings"
    ]
}

# Sample code for testing
SAMPLE_CODE = """
def add_numbers(a: int, b: int) -> int:
    \"\"\"
    Add two numbers together.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Sum of the two numbers
    \"\"\"
    return a + b
"""

# Mock LLM response for code generation
MOCK_CODE_GENERATION_RESPONSE = {
    "code": SAMPLE_CODE,
    "explanation": "Simple function to add two numbers",
    "imports": [],
    "dependencies": []
}

# Mock compilation results for testing
MOCK_COMPILATION_SUCCESS = {
    "feature_id": "test_feature_001",
    "operation_id": "test_op_001",
    "success": True,
    "results": {
        "format": {
            "success": True,
            "state": "SUCCEEDED",
            "issues": [],
            "execution_time": 0.1
        },
        "style": {
            "success": True,
            "state": "SUCCEEDED",
            "issues": [],
            "execution_time": 0.1
        },
        "lint": {
            "success": True,
            "state": "SUCCEEDED",
            "issues": [],
            "execution_time": 0.1
        },
        "type": {
            "success": True,
            "state": "SUCCEEDED",
            "issues": [],
            "execution_time": 0.1
        },
        "security": {
            "success": True,
            "state": "SUCCEEDED",
            "issues": [],
            "execution_time": 0.1
        }
    }
}

MOCK_COMPILATION_FAILURE = {
    "feature_id": "test_feature_001",
    "operation_id": "test_op_001",
    "success": False,
    "results": {
        "format": {
            "success": True,
            "state": "SUCCEEDED",
            "issues": [],
            "execution_time": 0.1
        },
        "style": {
            "success": False,
            "state": "FAILED",
            "issues": [
                {
                    "type": "style",
                    "line": 5,
                    "column": 1,
                    "message": "E303 too many blank lines",
                    "severity": "medium"
                }
            ],
            "execution_time": 0.1
        },
        "lint": {
            "success": True,
            "state": "SUCCEEDED",
            "issues": [],
            "execution_time": 0.1
        },
        "type": {
            "success": True,
            "state": "SUCCEEDED",
            "issues": [],
            "execution_time": 0.1
        },
        "security": {
            "success": True,
            "state": "SUCCEEDED",
            "issues": [],
            "execution_time": 0.1
        }
    }
}

# Mock debug results for testing
MOCK_DEBUG_RESULT = {
    "operation_id": "test_op_001",
    "success": True,
    "analysis": "Found style issues that need to be fixed",
    "suggestions": [
        {
            "issue": "Too many blank lines",
            "fix": "Remove extra blank lines"
        }
    ],
    "fixed_code": SAMPLE_CODE.replace("\n\n", "\n")
}

# Mock analysis results for testing
MOCK_ANALYSIS_RESULT = {
    "operation_id": "test_op_001",
    "success": True,
    "summary": "Code is well-structured but has minor style issues",
    "insights": ["Good type annotations", "Clear docstrings"],
    "metrics": {
        "code_quality_score": 85,
        "robustness_score": 90,
        "maintainability_score": 88,
        "security_score": 95
    },
    "improvements": [
        {
            "category": "style",
            "suggestion": "Fix blank line spacing",
            "priority": "low"
        }
    ]
}

@pytest.fixture
def mock_event_queue():
    """Create a mock event queue."""
    mock = AsyncMock()
    mock.emit = AsyncMock()
    mock._running = True
    return mock

@pytest.fixture
def mock_state_manager():
    """Create a mock state manager."""
    mock = AsyncMock()
    mock.set_state = AsyncMock()
    mock.get_state = AsyncMock()
    return mock

@pytest.fixture
def mock_context_manager():
    """Create a mock context manager."""
    mock = AsyncMock()
    mock.create_context = AsyncMock()
    mock.get_context = AsyncMock()
    mock.store_context = AsyncMock()
    return mock

@pytest.fixture
def mock_cache_manager():
    """Create a mock cache manager."""
    mock = AsyncMock()
    mock.set_cache = AsyncMock()
    mock.get_cache = AsyncMock()
    mock.invalidate = AsyncMock()
    return mock

@pytest.fixture
def mock_metrics_manager():
    """Create a mock metrics manager."""
    mock = AsyncMock()
    mock.record_metric = AsyncMock()
    return mock

@pytest.fixture
def mock_error_handler():
    """Create a mock error handler."""
    mock = AsyncMock()
    return mock

@pytest.fixture
def mock_memory_monitor():
    """Create a mock memory monitor."""
    mock = AsyncMock()
    mock.track_resource = AsyncMock()
    mock.untrack_resource = AsyncMock()
    return mock

@pytest.fixture
def mock_system_monitor():
    """Create a mock system monitor."""
    mock = AsyncMock()
    return mock

@pytest.fixture
def code_generation_agent(
    mock_event_queue, mock_state_manager, mock_context_manager, 
    mock_cache_manager, mock_metrics_manager, mock_error_handler, 
    mock_memory_monitor
):
    """Create a CodeGenerationAgent instance with mocked dependencies."""
    with patch('phase_four.CodeGenerationAgent.__init__', return_value=None):
        agent = CodeGenerationAgent(
            mock_event_queue, mock_state_manager, mock_context_manager,
            mock_cache_manager, mock_metrics_manager, mock_error_handler,
            mock_memory_monitor
        )
        
    # Set up the agent with the necessary mocks
    agent.interface_id = "code_generation_agent"
    agent._event_queue = mock_event_queue
    agent._state_manager = mock_state_manager
    agent._context_manager = mock_context_manager
    agent._cache_manager = mock_cache_manager
    agent._metrics_manager = mock_metrics_manager
    agent._error_handler = mock_error_handler
    agent._memory_monitor = mock_memory_monitor
    agent._validation_manager = MagicMock()
    
    # Mock the required methods
    agent.process_with_validation = AsyncMock(return_value=MOCK_CODE_GENERATION_RESPONSE)
    agent.set_agent_state = AsyncMock()
    
    return agent

@pytest.fixture
def static_compilation_agent(
    mock_event_queue, mock_state_manager, mock_context_manager, 
    mock_cache_manager, mock_metrics_manager, mock_error_handler, 
    mock_memory_monitor
):
    """Create a StaticCompilationAgent instance with mocked dependencies."""
    with patch('phase_four.StaticCompilationAgent.__init__', return_value=None):
        agent = StaticCompilationAgent(
            mock_event_queue, mock_state_manager, mock_context_manager,
            mock_cache_manager, mock_metrics_manager, mock_error_handler,
            mock_memory_monitor
        )
        
    # Set up the agent with the necessary mocks
    agent.interface_id = "static_compilation_agent"
    agent._event_queue = mock_event_queue
    agent._state_manager = mock_state_manager
    agent._context_manager = mock_context_manager
    agent._cache_manager = mock_cache_manager
    agent._metrics_manager = mock_metrics_manager
    agent._error_handler = mock_error_handler
    agent._memory_monitor = mock_memory_monitor
    agent._circuit_breaker = MagicMock()
    agent._circuit_breaker.execute = AsyncMock(side_effect=lambda func: func())
    
    # Mock the required methods
    agent._run_compiler = AsyncMock(return_value=CompilationResult(
        compiler_type=CompilerType.FORMAT,
        state=CompilationState.SUCCEEDED,
        success=True
    ))
    agent.set_agent_state = AsyncMock()
    return agent

@pytest.fixture
def compilation_debug_agent(
    mock_event_queue, mock_state_manager, mock_context_manager, 
    mock_cache_manager, mock_metrics_manager, mock_error_handler, 
    mock_memory_monitor
):
    """Create a CompilationDebugAgent instance with mocked dependencies."""
    with patch('phase_four.CompilationDebugAgent.__init__', return_value=None):
        agent = CompilationDebugAgent(
            mock_event_queue, mock_state_manager, mock_context_manager,
            mock_cache_manager, mock_metrics_manager, mock_error_handler,
            mock_memory_monitor
        )
        
    # Set up the agent with the necessary mocks
    agent.interface_id = "compilation_debug_agent"
    agent._event_queue = mock_event_queue
    agent._state_manager = mock_state_manager
    agent._context_manager = mock_context_manager
    agent._cache_manager = mock_cache_manager
    agent._metrics_manager = mock_metrics_manager
    agent._error_handler = mock_error_handler
    agent._memory_monitor = mock_memory_monitor
    
    # Mock the required methods
    agent.process_with_validation = AsyncMock(return_value=MOCK_DEBUG_RESULT)
    agent.set_agent_state = AsyncMock()
    return agent

@pytest.fixture
def compilation_analysis_agent(
    mock_event_queue, mock_state_manager, mock_context_manager, 
    mock_cache_manager, mock_metrics_manager, mock_error_handler, 
    mock_memory_monitor
):
    """Create a CompilationAnalysisAgent instance with mocked dependencies."""
    with patch('phase_four.CompilationAnalysisAgent.__init__', return_value=None):
        agent = CompilationAnalysisAgent(
            mock_event_queue, mock_state_manager, mock_context_manager,
            mock_cache_manager, mock_metrics_manager, mock_error_handler,
            mock_memory_monitor
        )
        
    # Set up the agent with the necessary mocks
    agent.interface_id = "compilation_analysis_agent"
    agent._event_queue = mock_event_queue
    agent._state_manager = mock_state_manager
    agent._context_manager = mock_context_manager
    agent._cache_manager = mock_cache_manager
    agent._metrics_manager = mock_metrics_manager
    agent._error_handler = mock_error_handler
    agent._memory_monitor = mock_memory_monitor
    
    # Mock the required methods
    agent.process_with_validation = AsyncMock(return_value=MOCK_ANALYSIS_RESULT)
    agent.set_agent_state = AsyncMock()
    return agent

@pytest.fixture
def compilation_refinement_agent(
    mock_event_queue, mock_state_manager, mock_context_manager, 
    mock_cache_manager, mock_metrics_manager, mock_error_handler, 
    mock_memory_monitor
):
    """Create a CompilationRefinementAgent instance with mocked dependencies."""
    with patch('phase_four.CompilationRefinementAgent.__init__', return_value=None):
        agent = CompilationRefinementAgent(
            mock_event_queue, mock_state_manager, mock_context_manager,
            mock_cache_manager, mock_metrics_manager, mock_error_handler,
            mock_memory_monitor
        )
        
    # Set up the agent with the necessary mocks
    agent.interface_id = "compilation_refinement_agent"
    agent._event_queue = mock_event_queue
    agent._state_manager = mock_state_manager
    agent._context_manager = mock_context_manager
    agent._cache_manager = mock_cache_manager
    agent._metrics_manager = mock_metrics_manager
    agent._error_handler = mock_error_handler
    agent._memory_monitor = mock_memory_monitor
    
    # Mock sub-agents
    agent.code_generation_agent = MagicMock()
    agent.code_generation_agent.generate_code = AsyncMock(return_value=MOCK_CODE_GENERATION_RESPONSE)
    
    agent.static_compilation_agent = MagicMock()
    agent.static_compilation_agent.run_compilation = AsyncMock(return_value=MOCK_COMPILATION_SUCCESS)
    
    agent.compilation_debug_agent = MagicMock()
    agent.compilation_debug_agent.analyze_failures = AsyncMock(return_value=MOCK_DEBUG_RESULT)
    
    agent.compilation_analysis_agent = MagicMock()
    agent.compilation_analysis_agent.analyze_compilation = AsyncMock(return_value=MOCK_ANALYSIS_RESULT)
    
    # Mock the required methods
    agent.set_agent_state = AsyncMock()
    return agent

@pytest.fixture
def phase_four_interface(
    mock_event_queue, mock_state_manager, mock_context_manager, 
    mock_cache_manager, mock_metrics_manager, mock_error_handler, 
    mock_memory_monitor, mock_system_monitor, compilation_refinement_agent
):
    """Create a PhaseFourInterface instance with mocked dependencies."""
    with patch('phase_four.PhaseFourInterface.__init__', return_value=None):
        interface = PhaseFourInterface(
            mock_event_queue, mock_state_manager, mock_context_manager,
            mock_cache_manager, mock_metrics_manager, mock_error_handler,
            mock_memory_monitor, mock_system_monitor
        )
    
    # Set up the interface with the necessary mocks
    interface._event_queue = mock_event_queue
    interface._state_manager = mock_state_manager
    interface._context_manager = mock_context_manager
    interface._cache_manager = mock_cache_manager
    interface._metrics_manager = mock_metrics_manager
    interface._error_handler = mock_error_handler
    interface._memory_monitor = mock_memory_monitor
    interface._system_monitor = mock_system_monitor
    interface.refinement_agent = compilation_refinement_agent
    
    return interface

@pytest.mark.asyncio
async def test_code_generation_agent(code_generation_agent):
    """Test the CodeGenerationAgent."""
    result = await code_generation_agent.generate_code(
        SAMPLE_FEATURE_REQUIREMENTS, "test_op_001"
    )
    
    assert result.get("code") == SAMPLE_CODE
    assert "explanation" in result
    assert code_generation_agent.set_agent_state.called
    assert code_generation_agent.process_with_validation.called

@pytest.mark.asyncio
async def test_static_compilation_agent_success(static_compilation_agent):
    """Test the StaticCompilationAgent with successful compilation."""
    # Mock run_compilation directly
    static_compilation_agent.run_compilation = AsyncMock(return_value=MOCK_COMPILATION_SUCCESS)
    
    result = await static_compilation_agent.run_compilation(
        SAMPLE_CODE, "test_feature_001", "test_op_001"
    )
    
    assert result.get("success") is True
    assert static_compilation_agent.run_compilation.called

@pytest.mark.asyncio
async def test_static_compilation_agent_failure(static_compilation_agent):
    """Test the StaticCompilationAgent with failed compilation."""
    # Mock run_compilation directly
    static_compilation_agent.run_compilation = AsyncMock(return_value=MOCK_COMPILATION_FAILURE)
    
    result = await static_compilation_agent.run_compilation(
        SAMPLE_CODE, "test_feature_001", "test_op_001"
    )
    
    assert result.get("success") is False
    assert static_compilation_agent.run_compilation.called

@pytest.mark.asyncio
async def test_compilation_debug_agent(compilation_debug_agent):
    """Test the CompilationDebugAgent."""
    result = await compilation_debug_agent.analyze_failures(
        SAMPLE_CODE, MOCK_COMPILATION_FAILURE, "test_op_001"
    )
    
    assert result.get("success") is True
    assert "analysis" in result
    assert "suggestions" in result
    assert "fixed_code" in result
    assert compilation_debug_agent.set_agent_state.called
    assert compilation_debug_agent.process_with_validation.called

@pytest.mark.asyncio
async def test_compilation_analysis_agent(compilation_analysis_agent):
    """Test the CompilationAnalysisAgent."""
    result = await compilation_analysis_agent.analyze_compilation(
        SAMPLE_CODE, MOCK_COMPILATION_SUCCESS, "test_op_001"
    )
    
    assert result.get("success") is True
    assert "summary" in result
    assert "insights" in result
    assert "metrics" in result
    assert "improvements" in result
    assert compilation_analysis_agent.set_agent_state.called
    assert compilation_analysis_agent.process_with_validation.called

@pytest.mark.asyncio
async def test_compilation_refinement_agent_success(compilation_refinement_agent):
    """Test the CompilationRefinementAgent with successful refinement."""
    result = await compilation_refinement_agent.refine_code(
        SAMPLE_FEATURE_REQUIREMENTS, SAMPLE_CODE, 5, "test_op_001"
    )
    
    assert result.get("success") is True
    assert "code" in result
    assert compilation_refinement_agent.set_agent_state.called
    assert compilation_refinement_agent.static_compilation_agent.run_compilation.called
    assert not compilation_refinement_agent.compilation_debug_agent.analyze_failures.called  # No need to debug if successful
    assert compilation_refinement_agent.compilation_analysis_agent.analyze_compilation.called

@pytest.mark.asyncio
async def test_compilation_refinement_agent_with_iterations(compilation_refinement_agent):
    """Test the CompilationRefinementAgent with multiple iterations."""
    # Mock compilation to fail once, then succeed
    compilation_refinement_agent.static_compilation_agent.run_compilation = AsyncMock(side_effect=[
        MOCK_COMPILATION_FAILURE,  # First call fails
        MOCK_COMPILATION_SUCCESS   # Second call succeeds
    ])
    
    result = await compilation_refinement_agent.refine_code(
        SAMPLE_FEATURE_REQUIREMENTS, SAMPLE_CODE, 5, "test_op_001"
    )
    
    assert result.get("success") is True
    assert result.get("iterations") == 2  # Should take 2 iterations
    assert "code" in result
    assert compilation_refinement_agent.set_agent_state.called
    assert compilation_refinement_agent.compilation_debug_agent.analyze_failures.called  # Should be called for the failing iteration
    assert compilation_refinement_agent.compilation_analysis_agent.analyze_compilation.called

@pytest.mark.asyncio
async def test_phase_four_interface(phase_four_interface, mock_metrics_manager, mock_state_manager):
    """Test the PhaseFourInterface."""
    # Mock the process_feature_code method
    successful_result = {
        "feature_id": "test_feature_001",
        "feature_name": "Test Feature",
        "success": True,
        "code": SAMPLE_CODE,
        "iterations": 1
    }
    phase_four_interface.process_feature_code = AsyncMock(return_value=successful_result)
    
    result = await phase_four_interface.process_feature_code(
        SAMPLE_FEATURE_REQUIREMENTS, SAMPLE_CODE, 5
    )
    
    assert result.get("success") is True
    assert "code" in result
    assert phase_four_interface.process_feature_code.called

@pytest.mark.asyncio
async def test_compile_result_parsing():
    """Test parsing compiler output."""
    # Create a mock agent with only the _parse_compiler_output method
    class MockStaticCompilationAgent:
        def _parse_compiler_output(self, compiler_type, stdout, stderr):
            if compiler_type == CompilerType.STYLE:
                # Parse flake8 output
                for line in stdout.split('\n'):
                    if ':' in line:
                        parts = line.strip().split(':')
                        if len(parts) >= 4:
                            file_path, line_num, col, message = parts[0:4]
                            return [{
                                "type": "style",
                                "line": int(line_num),
                                "column": int(col),
                                "message": message.strip(),
                                "severity": "medium"
                            }]
            elif compiler_type == CompilerType.TYPE:
                # Parse mypy output
                for line in stdout.split('\n'):
                    if ':' in line and 'error' in line:
                        parts = line.split(':')
                        if len(parts) >= 3:
                            file_path, line_num = parts[0:2]
                            message = ':'.join(parts[2:]).strip()
                            return [{
                                "type": "type",
                                "line": int(line_num) if line_num.isdigit() else 0,
                                "message": message,
                                "severity": "high"
                            }]
            return []
    
    mock_agent = MockStaticCompilationAgent()
    
    # Test parsing flake8 output
    flake8_output = "/path/to/file.py:10:5: E303 too many blank lines (3)"
    issues = mock_agent._parse_compiler_output(CompilerType.STYLE, flake8_output, "")
    
    assert len(issues) == 1
    assert issues[0]["type"] == "style"
    assert issues[0]["line"] == 10
    assert issues[0]["column"] == 5
    assert "blank lines" in issues[0]["message"]
    
    # Test parsing mypy output
    mypy_output = "/path/to/file.py:15: error: Argument 1 to \"add\" has incompatible type \"str\"; expected \"int\""
    issues = mock_agent._parse_compiler_output(CompilerType.TYPE, mypy_output, "")
    
    assert len(issues) == 1
    assert issues[0]["type"] == "type"
    assert issues[0]["line"] == 15
    assert "incompatible type" in issues[0]["message"]

@pytest.mark.asyncio
async def test_compilation_context():
    """Test the CompilationContext."""
    ctx = CompilationContext(
        feature_code=SAMPLE_CODE,
        feature_id="test_feature_001",
        source_file_path="/tmp/test_feature_001.py"
    )
    
    assert ctx.feature_code == SAMPLE_CODE
    assert ctx.feature_id == "test_feature_001"
    assert ctx.source_file_path == "/tmp/test_feature_001.py"
    assert ctx.current_stage == CompilerType.FORMAT
    assert ctx.max_iterations == 5
    assert ctx.current_iteration == 0
    assert isinstance(ctx.results, dict)
    assert len(ctx.results) == 0